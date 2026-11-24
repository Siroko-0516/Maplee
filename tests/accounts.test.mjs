import test from "node:test";
import { readFileSync } from "node:fs";
import { sqliteWorld } from "../server/sqlite-world.mjs";
import assert from "node:assert/strict";
import worker from "../dist/server/index.js";

const origin = "https://maplee.test";
function storage() {
  const documents = new Map();
  return {
    async get(key) {
      const row = documents.get(key);
      return row ? { etag: row.etag, json: async () => JSON.parse(row.text) } : null;
    },
    async put(key,text,{ onlyIf:match } = {}) {
      if (match?.etagDoesNotMatch === "*" && documents.has(key)) return null;
      if (match?.etagMatches && documents.get(key)?.etag !== match.etagMatches) return null;
      const etag = crypto.randomUUID();
      documents.set(key,{ etag,text });
      return { etag };
    },
    async delete(key) { documents.delete(key); },
  };
}

const packed = readFileSync(new URL("../dist/server/index.js", import.meta.url), "utf8");
const catalog = JSON.parse(/^const SHARED_WORLD = (.+);$/m.exec(packed)[1]);
const starter = { name:"안개 모험가", job:"beginner", sex:1, skin:4, hair:6, style:"frost" };
const password = "this-is-a-test-password";
const protocol = 1;

function fixture() {
  const SAVES = storage();
  const WORLD = sqliteWorld(":memory:");
  const call = (cookie, path, method="GET", data, source=origin) => worker.fetch(new Request(origin+path, {
    method, headers:{ "Content-Type":"application/json", Cookie:cookie, Origin:source }, body:JSON.stringify(data),
  }),{ SAVES,WORLD });
  async function signup(login) {
    const response = await call("", "/api/signup", "POST", { login,password });
    assert.equal(response.status,200);
    assert.match(response.headers.get("Set-Cookie"), /HttpOnly; SameSite=Lax; Secure/);
    assert.deepEqual((await response.json()).slots,[null,null,null,null]);
    return response.headers.get("Set-Cookie").split(";")[0];
  }
  async function legacy(login,slot,save) {
    const bytes = await crypto.subtle.digest("SHA-256",new TextEncoder().encode(login));
    const digest = Buffer.from(bytes).toString("hex");
    const account = await (await SAVES.get("users/"+digest)).json();
    const key = `slots/${account.id}/${slot}`;
    await SAVES.put(key,JSON.stringify(save));
    return key;
  }
  async function get(cookie,slot=0) {
    const response = await call(cookie,"/api/slot/"+slot);
    assert.equal(response.status,200);
    return response.json();
  }
  async function join(cookie,pose,slot=0,mode="shared") {
    const response = await call(cookie,"/api/world/join","POST",{ protocol,layout:catalog.layout,slot,mode,pose });
    assert.equal(response.status,200,JSON.stringify(await response.clone().json()));
    return { cookie,...await response.json() };
  }
  async function sync(member,seq,pose,{ ops=[], move=null, ...rest }={}) {
    const response = await call(member.cookie,"/api/world/sync","POST",
      { protocol,layout:catalog.layout,actor:member.actor,seq,pose,ops,move,...rest });
    const data = await response.json();
    assert.equal(response.status,200,JSON.stringify(data));
    return data;
  }
  return { SAVES,call,signup,legacy,get,join,sync };
}

test("accounts, four slots, durable legacy migration and settings-only autosaves",async () => {
  const { SAVES,call,signup,legacy,get } = fixture();
  const cookie = await signup("account_1");
  const other = await signup("account_2");
  for (let i=0; i<3; i++) assert.equal((await call(cookie,"/api/slot/"+i,"POST",{ profile:starter })).status,201);
  assert.equal((await call(cookie,"/api/slot/4","POST",{ profile:starter })).status,404);
  assert.equal((await call(cookie,"/api/slot/1","POST",{ profile:starter })).status,409);
  assert.equal((await call(other,"/api/slot/0")).status,404);
  assert.equal((await call("","/api/slot/0")).status,401);
  const old = { profile:{ ...starter,job:"cleric" }, revision:7,updated:1795400000,progress:{
    job:"cleric", level:9, gold:842, xp:22, avatarStyle:"classic",bag:{ chimewand:2, cap:1, jelly:5 },
    equipment:{ weapon:"chimewand", armor:"cap" }, x:catalog.start+10, worldLayout:catalog.layout,
    quests:[{ state:2,count:8 }], bestiary:{ 0:18 },
  } };
  const key = await legacy("account_1",3,old);
  const [one,two] = await Promise.all([get(cookie,3),get(cookie,3)]);
  assert.equal(one.characterId,two.characterId);
  assert.match(one.characterId,/^[0-9a-f]{32}$/);
  assert.equal(one.revision,7);
  assert.equal(one.progress.gold,842);
  assert.equal(one.progress.equipment.head,"cap");
  assert.equal(one.progress.bestiary[0],18);
  assert.deepEqual(one.progress.gear.chimewand.ranges,[[1,2]]);
  assert.equal(one.equipmentIds.weapon,one.characterId+":chimewand:1");
  assert.deepEqual(await (await SAVES.get(key)).json(),old);
  const first = await get(cookie);
  assert.equal(first.progress.job,"beginner");
  assert.notEqual(first.characterId,one.characterId);
  const payload = { protocol,revision:7,settings:{ hotbar:["mp"],gold:1_000_000,x:40000 },progress:{ level:200,job:"mage" } };
  const race = await Promise.all([1,2].map(() => call(cookie,"/api/slot/3","PUT",payload)));
  assert.deepEqual(race.map(r=>r.status).sort(),[200,409]);
  const changed = await get(cookie,3);
  assert.equal(changed.revision,8);
  assert.equal(changed.progress.hotbar[0],"mp");
  assert.equal(changed.progress.level,9);
  assert.equal(changed.progress.gold,842);
  assert.equal(changed.progress.x,old.progress.x);
  assert.equal((await call(cookie,"/api/slot/3","PUT",{ ...payload,revision:8 },"https://bad.test")).status,403);
  assert.equal((await call(cookie,"/api/slot/3","PUT",{ revision:8,progress:old.progress })).status,426);
  const listed = await (await call(cookie,"/api/session")).json();
  assert.equal(listed.slots[3].profile.style,"classic");
  assert.equal((await call(cookie,"/api/logout","POST",{})).status,200);
  assert.equal((await call(cookie,"/api/session")).status,401);
  const login = await call("","/api/login","POST",{ login:"account_1",password });
  assert.equal(login.status,200);
  const restored = await get(login.headers.get("Set-Cookie").split(";")[0],3);
  assert.equal(restored.characterId,one.characterId);
});

function patrol(spec, at) {
  const width = spec.right-spec.left;
  const origin = spec.direction > 0 ? spec.home-spec.left : 2*width-(spec.home-spec.left);
  const phase = (at*.06*spec.speed+origin) % (2*width);
  return spec.left+Math.min(phase,2*width-phase);
}

test("server damage, replay-safe cooperative rewards, mode isolation and portal validation",async t => {
  const { call,signup,legacy,get,join,sync } = fixture();
  const mob = catalog.monsters[0];
  let now = 1_800_000_000_000;
  t.mock.method(Date,"now",()=>now);
  const pose = () => ({ x:Math.round(patrol(mob,now))-20, y:Math.round(mob.y), facing:1 });
  const joinPose = pose();
  async function player(login, name) {
    const cookie = await signup(login);
    await legacy(login,0,{ profile:{ ...starter,name },revision:0,updated:now/1000,
      progress:{ level:1,x:joinPose.x,worldLayout:catalog.layout,job:"beginner",bag:{ twig:1 },
        equipment:{ weapon:"twig" }, quests:[{ state:1,count:0 }] } });
    return join(cookie,joinPose);
  }
  const a = await player("field_a","바람 모험가");
  const b = await player("field_b","풀잎 모험가");
  assert.deepEqual(a.players,[]);
  assert.equal(b.players[0].name,"바람 모험가");
  assert.equal(b.players[0].equipment.weapon,"twig");
  assert.equal("account" in b.players[0],false);
  now += 550;
  const attack = (intent="basic", from=pose()) => ["attack",intent,now,from.x,from.y,from.facing,999999];
  const struck = await sync(a,1,pose(),{ ops:[attack(),attack()] });
  assert.deepEqual(struck.hits,[[0,6,"impact"]]);
  assert.deepEqual(struck.monsters[0].slice(0,3),[0,mob.hp-6,0]);
  const replay = await sync(a,1,pose(),{ ops:[attack()] });
  assert.equal(replay.monsters[0][1],mob.hp-6);
  now += 550;
  const wrong = { ...pose(), y:pose().y-133 };
  const missed = await sync(a,2,pose(),{ ops:[attack("basic",wrong)], hits:[{ id:0,power:1800 }] });
  assert.equal(missed.monsters[0][1],mob.hp-6);
  now += 550;
  await Promise.all([sync(a,3,pose(),{ ops:[attack()] }),sync(b,1,pose(),{ ops:[attack("primary")] })]);
  const aDone = await get(a.cookie), bDone = await get(b.cookie);
  for (const done of [aDone,bDone]) {
    assert.equal(done.progress.kills,1);
    assert.equal(done.progress.gold,catalog.species[0].gold);
    assert.equal(done.progress.xp,catalog.species[0].xp);
    assert.equal(done.progress.bag[catalog.species[0].loot],1);
    assert.equal(done.progress.quests[0].count,1);
  }
  const privateField = await join(b.cookie,pose(),0,"solo");
  assert.deepEqual(privateField.monsters,[]);
  assert.deepEqual(privateField.players,[]);
  assert.equal(privateField.progress.kills,1);
  const fake = { ...pose(),x:catalog.ends[0]+200 };
  now += 500;
  assert.equal((await sync(privateField,1,fake)).region,0);
  const east = catalog.portals.find(([x,,target])=>x<catalog.ends[0] && target===1);
  await legacy("field_b",1,{ profile:starter,updated:now/1000,revision:0,
    progress:{ job:"beginner",level:1,x:east[0],worldLayout:catalog.layout } });
  const port = { x:east[0],y:355,facing:1 };
  const traveler = await join(b.cookie,port,1,"solo");
  now += 500;
  const travel = await sync(traveler,1,traveler.pose,{ move:east[0] });
  assert.equal(travel.warp,"portal");
  assert.equal(travel.pose.x,east[1]);
  assert.equal(travel.region,1);
  assert.equal((await get(b.cookie,1)).progress.x,east[1]);
  assert.equal((await call("", "/api/world/join","POST",{ protocol })).status,401);
});

test("shop charges, equipment identity and reconnect preserve server results",async t => {
  const { signup,legacy,get,join,sync } = fixture();
  let now = 1_800_000_100_000;
  t.mock.method(Date,"now",()=>now);
  const cookie = await signup("economy_test");
  const shop = catalog.npcs.find(npc=>npc.kind === "shop");
  const pos = { x:shop.x,y:338,facing:1 };
  const initialGold = 1000;
  await legacy("economy_test",0,{ profile:starter,revision:0,updated:now/1000,
    progress:{ job:"beginner",level:4,gold:initialGold,bag:{ twig:1 },equipment:{ weapon:"twig" },
      x:pos.x, worldLayout:catalog.layout } });
  const actor = await join(cookie,pos);
  now += 450;
  const input = { ops:[["buy","bronze"],["equip_item","bronze"],["sell","bronze"],["attribute","strength"]] };
  const purchased = await sync(actor,1,actor.pose,input);
  assert.deepEqual(purchased.results,[[0,true],[1,true],[2,false],[3,true]]);
  const replay = await sync(actor,1,actor.pose,input);
  assert.equal(replay.progress.gold,initialGold-catalog.items.bronze.price);
  assert.equal(replay.progress.bag.bronze,1);
  const reloaded = await get(cookie);
  assert.equal(reloaded.progress.attributes.strength,1);
  assert.equal(reloaded.progress.equipment.weapon,"bronze");
  assert.equal(reloaded.equipmentIds.weapon,reloaded.characterId+":bronze:1");
  const rejoined = await join(cookie,actor.pose);
  assert.equal(rejoined.progress.gold,reloaded.progress.gold);
});
