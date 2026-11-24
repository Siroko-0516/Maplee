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

test("independent accounts, four slots, and versioned saves",async () => {
  const SAVES = storage();
  const call = (path,method="GET",body,cookie="",source=origin) => worker.fetch(new Request(origin + path,{
    method,headers:{ "Content-Type":"application/json",Origin:source,Cookie:cookie },body:JSON.stringify(body)
  }),{ SAVES });
  const cookie = response => response.headers.get("Set-Cookie").split(";")[0];
  const credentials = { login:"account_1",password:"longer-than-ten-characters" };
  const signup = await call("/api/signup","POST",credentials);
  const first = cookie(signup);
  assert.equal(signup.status,200);
  assert.match(signup.headers.get("Set-Cookie"),/HttpOnly; SameSite=Lax; Secure/);
  assert.deepEqual((await signup.json()).slots,[null,null,null,null]);
  assert.equal((await call("/api/signup","POST",credentials)).status,409);
  assert.equal((await call("/api/login","POST",{ ...credentials,password:"not-the-password" })).status,401);
  assert.equal((await call("/api/session")).status,401);

  const profile = { name:"안개 모험가", job:"cleric", sex:1, skin:4, hair:6, style:"frost" };
  for (let i=0; i<4; i++) assert.equal((await call("/api/slot/"+i,"POST",{profile},first)).status,201);
  assert.equal((await call("/api/slot/4","POST",{profile},first)).status,404);
  assert.equal((await call("/api/slot/1","POST",{profile},first)).status,409);
  const state = { job:"cleric", level:9, gold:842, avatarStyle:"classic" };
  const race = await Promise.all([1,2].map(() => call("/api/slot/1","PUT",{revision:0,progress:state},first)));
  assert.deepEqual(race.map(r=>r.status).sort(),[200,409]);
  const changed = await call("/api/slot/1","GET",undefined,first);
  assert.deepEqual((await changed.json()).progress,state);
  const unchanged = await call("/api/slot/0","GET",undefined,first);
  assert.equal((await unchanged.json()).progress,null);
  const second = cookie(await call("/api/signup","POST",{ ...credentials, login:"account_2" }));
  assert.equal((await call("/api/slot/1","GET",undefined,second)).status,404);
  assert.equal((await call("/api/slot/1","PUT",{revision:1,progress:state},first,"https://bad.test")).status,403);
  assert.equal((await call("/api/logout","POST",{},first)).status,200);
  assert.equal((await call("/api/session","GET",undefined,first)).status,401);
  const signedIn = cookie(await call("/api/login","POST",credentials));
  const restored = await call("/api/slot/1","GET",undefined,signedIn);
  assert.deepEqual((await restored.json()).profile,profile);
  const listed = await call("/api/session","GET",undefined,signedIn);
  assert.deepEqual((await listed.json()).slots[1].profile,{...profile,style:"classic"});
});

test("shared world shows nearby characters and credits a coordinated kill once", async t => {
  const SAVES = storage();
  const WORLD = sqliteWorld(":memory:");
  const serialized = readFileSync(new URL("../dist/server/index.js", import.meta.url), "utf8");
  const layout = JSON.parse(/^const SHARED_WORLD = (.+);$/m.exec(serialized)[1]);
  const monster = layout.monsters[0];
  let now = 1_800_000_000_000;
  t.mock.method(Date, "now", () => now);
  const call = (cookie, path, body) => worker.fetch(new Request(origin + path, {
    method: "POST", headers: { "Content-Type": "application/json", Origin: origin, Cookie: cookie },
    body: JSON.stringify(body)
  }), { SAVES, WORLD });
  const pose = { x:monster.home, y:Math.round(monster.y), job:"beginner", level:1,
    facing:1, frame:0, equipment:{ weapon:"twig" } };
  assert.equal((await call("", "/api/world/join", { slot:0, layout:layout.layout, pose })).status, 401);

  async function join(login, name) {
    const password = "this-is-a-test-password";
    const signup = await call("", "/api/signup", { login, password });
    const cookie = signup.headers.get("Set-Cookie").split(";")[0];
    const creation = await call(cookie, "/api/slot/0", {
      profile: { name, job:"beginner", sex:0, hair:0, skin:0 }
    });
    assert.equal(creation.status, 201);
    const entry = await call(cookie, "/api/world/join", { slot:0, layout:layout.layout, pose });
    assert.equal(entry.status, 200);
    return { cookie, ...await entry.json() };
  }

  const first = await join("world_test_a", "바람 모험가");
  const second = await join("world_test_b", "풀잎 모험가");
  assert.deepEqual(first.players, []);
  assert.equal(second.players[0].name, "바람 모험가");
  assert.equal(second.players[0].equipment.weapon, "twig");
  assert.equal(second.players[0].id, first.actor);
  assert.equal("account" in second.players[0], false);

  const hit = power => ({ id:0, life:0, x:pose.x, y:pose.y, power });
  async function sync(member, seq, hits = [], ack = [], position = pose) {
    const result = await call(member.cookie, "/api/world/sync", {
      actor:member.actor, seq, layout:layout.layout, pose:position, hits, ack
    });
    const data = await result.json();
    assert.equal(result.status, 200, JSON.stringify(data));
    return data;
  }
  now += 350;
  const chipped = await sync(first, 1, [hit(4)]);
  assert.deepEqual(chipped.monsters[0].slice(0,3), [0, monster.hp-4, 0]);
  assert.equal(chipped.players[0].name, "풀잎 모험가");
  now += 350;
  assert.equal((await sync(first, 1, [hit(4)])).monsters[0][1], monster.hp-4);

  now += 350;
  await Promise.all([sync(first, 2, [hit(5)]), sync(second, 1, [hit(monster.hp-9)])]);
  now += 350;
  const a = await sync(first, 3);
  const b = await sync(second, 2);
  assert.deepEqual(a.monsters[0].slice(0,3), [0, 0, 0]);
  assert.ok(a.monsters[0][3] > now);
  assert.deepEqual(a.rewards.map(row => row.event), ["0:0"]);
  assert.deepEqual(b.rewards.map(row => row.event), ["0:0"]);

  now += 350;
  assert.deepEqual((await sync(first, 4, [], ["0:0"])).rewards, []);
  const nextRegion = { ...pose, x:layout.ends[0]+150 };
  const traveled = await sync(second, 3, [], ["0:0"], nextRegion);
  assert.equal(traveled.region, 1);
  assert.deepEqual(traveled.players, []);
  assert.deepEqual(traveled.rewards, []);

  now = a.monsters[0][3] + 350;
  const revived = await sync(first, 5, [hit(6)]);
  assert.deepEqual(revived.monsters[0], [0, monster.hp, 1, 0]);
  assert.equal((await call(first.cookie, "/api/world/leave", { actor:first.actor })).status, 200);
  now += 350;
  const back = await sync(second, 4);
  assert.deepEqual(back.players, []);
});
