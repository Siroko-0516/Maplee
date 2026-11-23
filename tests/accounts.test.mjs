import test from "node:test";
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

  const profile = { name:"안개 모험가", job:"cleric", sex:1, skin:4, hair:6 };
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
