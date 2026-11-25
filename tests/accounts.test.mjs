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
  return { SAVES,WORLD,call,signup,legacy,get,join,sync };
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
    equipment:{ weapon:"chimewand", armor:"cap" }, x:catalog.start+10, worldLayout:5,
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
  const east = catalog.portals.find(([, ,target])=>catalog.mapIds[target]==="slime-clearing");
  await legacy("field_b",1,{ profile:starter,updated:now/1000,revision:0,
    progress:{ job:"beginner",level:1,x:east[0],worldLayout:catalog.layout } });
  const port = { x:east[0],y:355,facing:1 };
  const traveler = await join(b.cookie,port,1,"solo");
  now += 500;
  const travel = await sync(traveler,1,traveler.pose,{ move:east[0] });
  assert.equal(travel.warp,"portal");
  assert.equal(travel.pose.x,east[1]);
  assert.equal(travel.region,east[2]);
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

test("movement uses one database batch and retries acknowledge the original position",async t => {
  const { WORLD,signup,legacy,join,sync } = fixture();
  let now = 1_800_000_100_000;
  t.mock.method(Date,"now",()=>now);
  const cookie = await signup("field_latency");
  const x = catalog.start;
  await legacy("field_latency",0,{ profile:starter,revision:0,updated:now/1000,
    progress:{ level:1,job:"beginner",x,worldLayout:catalog.layout } });
  const actor = await join(cookie,{ x,y:390,facing:1 });

  const batches = t.mock.method(WORLD,"batch",WORLD.batch);
  now += 320;
  const airborne = { x:x+95,y:130,facing:1 };
  const first = await sync(actor,1,airborne,{ stateVersion:actor.stateVersion });
  assert.equal(batches.mock.callCount(),1);
  assert.deepEqual(first.sample,[airborne.x,airborne.y]);
  assert.equal(first.pose.y,airborne.y);
  assert.equal(first.progress,null);

  now += 155;
  const descending = { x:x+131,y:365,facing:1 };
  const retry = await sync(actor,1,descending);
  assert.deepEqual(retry.sample,first.sample);
  assert.equal(retry.pose.y,airborne.y);
  const landed = await sync(actor,2,descending);
  assert.deepEqual(landed.sample,[descending.x,descending.y]);
  assert.equal(landed.pose.y,descending.y);

  now += 4500;
  const afterDelay = { x:x+1550,y:330,facing:1 };
  const resumed = await sync(actor,3,afterDelay);
  assert.equal(resumed.pose.x,afterDelay.x);
  assert.equal(resumed.pose.y,afterDelay.y);
  now += 120;
  const invalid = { ...afterDelay,y:500 };
  const constrained = await sync(actor,4,invalid);
  assert.deepEqual(constrained.sample,[invalid.x,invalid.y]);
  assert.equal(constrained.pose.x,afterDelay.x);
  assert.equal(constrained.pose.y,afterDelay.y);
});

test("connected maps allow walking and both transport routes persist until arrival",async t => {
  const { call,signup,legacy,get,join,sync } = fixture();
  let now = 1_800_000_200_000;
  t.mock.method(Date,"now",()=>now);
  const login = "region_traveler";
  const cookie = await signup(login);
  function poseAt(x) {
    const at = catalog.ground.findIndex(([point])=>point>x);
    const [left,y] = catalog.ground[at-1], [right,z] = catalog.ground[at];
    return { x,y:Math.round(y+(z-y)*(x-left)/(right-left)),facing:1 };
  }
  async function spawn(slot,x) {
    await legacy(login,slot,{ profile:starter,revision:0,updated:now/1000,
      progress:{ job:"beginner",level:1,x,worldLayout:catalog.layout } });
    return join(cookie,poseAt(x),slot);
  }

  const seam = catalog.ends[0];
  const walker = await spawn(0,seam-45);
  now += 320;
  const walked = await sync(walker,1,poseAt(seam+37));
  assert.equal(walked.region,1);
  assert.equal(walked.pose.x,seam+37);
  assert.equal(walked.warp,null);

  for (const [slot, mode] of [[1,"boat"],[2,"airship"]]) {
    const [gate, arrival, region] = catalog.portals.find(([x])=>catalog.transports[x]===mode);
    const rider = await spawn(slot,gate);
    now += 320;
    const attemptedWalk = await sync(rider,1,poseAt(catalog.ends[region-1]+24));
    assert.equal(attemptedWalk.region,rider.region);
    assert.equal(attemptedWalk.pose.x,gate);
    now += 320;
    const boarded = await sync(rider,2,poseAt(gate),{ move:gate });
    assert.equal(boarded.warp,null);
    assert.equal(boarded.voyage.mode,mode);
    assert.equal(boarded.region,rider.region);
    assert.equal((await call(cookie,"/api/world/leave","POST",{ actor:rider.actor })).status,200);
    now += 320;
    const reconnected = await join(cookie,poseAt(gate),slot);
    assert.deepEqual(reconnected.voyage,boarded.voyage);
    now += 320;
    const inTransit = await sync(reconnected,1,poseAt(gate),{ move:"home" });
    assert.equal(inTransit.pose.x,gate);
    assert.equal(inTransit.voyage.mode,mode);
    now = boarded.voyage.until+125;
    const docked = await sync(reconnected,2,poseAt(gate));
    assert.equal(docked.voyage,null);
    assert.equal(docked.warp,mode);
    assert.equal(docked.region,region);
    assert.equal(docked.pose.x,arrival);
    assert.equal((await get(cookie,slot)).progress.x,arrival);
  }
});
