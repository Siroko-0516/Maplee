import { asset } from "./static.mjs";

const encoder = new TextEncoder();
const COOKIE = "maplee_session";
const SESSION_SECONDS = 14 * 86400;
const MAX_SAVE_BYTES = 48_000;
const avatarStyles = new Set(["classic","custom"]);
const JOBS = new Set(["beginner", "guardian", "ranger", "mage", "thief", "pirate", "cleric"]);
const reply = (body, status = 200, extra = {}) =>
  Response.json(body, { status, headers: { "Cache-Control": "no-store", ...extra } });
const fail = (status, error) => reply({ error }, status);
const hex = bytes => Array.from(bytes, byte => byte.toString(16).padStart(2, "0")).join("");
const random = length => hex(crypto.getRandomValues(new Uint8Array(length)));
const digest = async value => hex(new Uint8Array(await crypto.subtle.digest("SHA-256", encoder.encode(value))));
const saltBytes = text => Uint8Array.from(text.match(/../g), byte => parseInt(byte, 16));

async function passwordHash(password, salt) {
  const key = await crypto.subtle.importKey("raw", encoder.encode(password), "PBKDF2", false, ["deriveBits"]);
  const bits = await crypto.subtle.deriveBits({ name: "PBKDF2", hash: "SHA-256",
    iterations: 100000, salt: saltBytes(salt) }, key, 256);
  return hex(new Uint8Array(bits));
}

function equal(a, b) {
  let difference = 0;
  for (let i = 0; i < 64; i++) difference |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return difference === 0;
}

async function record(store, key) {
  const object = await store.get(key);
  return object ? { value: await object.json(), etag: object.etag } : null;
}

async function put(store, key, value, prior = null) {
  const condition = prior ? { etagMatches: prior.etag } : { etagDoesNotMatch: "*" };
  return await store.put(key, JSON.stringify(value), { onlyIf: condition });
}

async function throttle(store, ip, timestamp) {
  const key = "limits/" + await digest(ip);
  for (let attempt = 0; attempt < 4; attempt++) {
    const prior = await record(store, key);
    const limit = prior?.value;
    const state = limit && limit.until > timestamp ? limit : { until: timestamp + 600, count: 0 };
    if (state.count >= 18) return false;
    if (await put(store, key, { ...state, count: state.count + 1 }, prior)) return true;
  }
  return false;
}

function sessionCookie(token, request, seconds) {
  const secure = new URL(request.url).protocol === "https:" ? "; Secure" : "";
  return `${COOKIE}=${token}; Path=/; Max-Age=${seconds}; HttpOnly; SameSite=Lax${secure}`;
}

async function body(request, max = 2048) {
  const stream = request.body?.getReader();
  if (!stream || !request.headers.get("Content-Type")?.startsWith("application/json")) return null;
  const decoder = new TextDecoder();
  let bytes = 0;
  let text = "";
  try {
    while (true) {
      const { value, done } = await stream.read();
      if (done) break;
      bytes += value.byteLength;
      if (bytes > max) {
        await stream.cancel();
        return null;
      }
      text += decoder.decode(value, { stream: true });
    }
    const parsed = JSON.parse(text + decoder.decode());
    return parsed && typeof parsed === "object" && !Array.isArray(parsed) ? parsed : null;
  } catch {
    return null;
  }
}

function profile(data) {
  const name = typeof data?.name === "string" ? data.name.normalize("NFC").trim() : "";
  if (!/^[\p{L}\p{N} _-]{2,14}$/u.test(name) || !JOBS.has(data.job) ||
      ![0, 1].includes(data.sex) || !Number.isInteger(data.skin) || data.skin < 0 || data.skin > 4 ||
      !Number.isInteger(data.hair) || data.hair < 0 || data.hair > 6) return null;
  if (data.style !== undefined && !avatarStyles.has(data.style)) return null;
  return { name, job: data.job, sex: data.sex, skin: data.skin, hair: data.hair,
    ...(data.style !== undefined ? { style: data.style } : {}) };
}

function progress(data) {
  return data && !Array.isArray(data) && typeof data === "object" &&
    Number.isInteger(data.level) && data.level >= 1 && data.level <= 200 &&
    JOBS.has(data.job) ? data : null;
}

function brief(slot, document) {
  const chosen = document.progress?.avatarStyle;
  return { slot, profile: { ...document.profile, job: document.progress?.job || document.profile.job,
    ...(avatarStyles.has(chosen) ? { style: chosen } : {}) },
    level: document.progress?.level || 1, updated: document.updated };
}

async function accounts(request, store) {
  const { pathname, origin } = new URL(request.url);
  const method = request.method;
  if (!["GET", "HEAD"].includes(method) && request.headers.get("Origin") !== origin)
    return fail(403, "요청 출처가 올바르지 않아요.");
  const now = Math.floor(Date.now() / 1000);
  if (method === "POST" && ["/api/signup", "/api/login"].includes(pathname)) {
    const data = await body(request);
    const login = typeof data?.login === "string" ? data.login.trim().toLowerCase() : "";
    const password = data?.password;
    if (!/^[a-z0-9_]{3,24}$/.test(login) || typeof password !== "string" || password.length < 10 || password.length > 128)
      return fail(400, "아이디는 영문·숫자·밑줄 3~24자, 비밀번호는 10~128자예요.");
    const ip = request.headers.get("CF-Connecting-IP") || "local";
    if (!await throttle(store,ip,now)) return fail(429, "로그인 요청이 많아요. 잠시 후 다시 시도해주세요.");
    const key = "users/" + await digest(login);
    let account;
    if (pathname === "/api/signup") {
      const salt = random(16);
      account = { id: random(18), salt, hash: await passwordHash(password,salt) };
      const created = await put(store,key,account);
      if (!created) return fail(409, "이미 사용 중인 아이디예요.");
    } else {
      account = (await record(store,key))?.value;
      const candidate = await passwordHash(password,account?.salt || "00000000000000000000000000000000");
      if (!account || !equal(candidate,account.hash)) return fail(401,"아이디 또는 비밀번호를 확인해주세요.");
    }
    const token = random(32);
    const session = { id: account.id, login, expiry: now + SESSION_SECONDS };
    await store.put("sessions/" + await digest(token),JSON.stringify(session));
    return reply({ account: login, slots: await slots(store,account.id) },200,
      { "Set-Cookie": sessionCookie(token,request,SESSION_SECONDS) });
  }

  const raw = request.headers.get("Cookie")?.match(/(?:^|;\s*)maplee_session=([a-f0-9]{64})(?:;|$)/)?.[1];
  const key = raw ? "sessions/" + await digest(raw) : null;
  const session = key && (await record(store,key))?.value;
  if (!session || session.expiry <= now) return fail(401,"로그인이 필요해요.");
  if (pathname === "/api/logout" && method === "POST") {
    await store.delete(key);
    return reply({},200,{"Set-Cookie":sessionCookie("",request,0)});
  }
  if (pathname === "/api/session" && method === "GET")
    return reply({ account: session.login, slots: await slots(store,session.id) });

  const match = /^\/api\/slot\/([0-3])$/.exec(pathname);
  if (!match) return fail(404,"페이지를 찾을 수 없어요.");
  const slot = Number(match[1]);
  const saveKey = "slots/" + session.id + "/" + slot;
  const saved = await record(store,saveKey);
  if (method === "GET")
    return saved ? reply(saved.value) : fail(404,"빈 캐릭터 슬롯이에요.");
  if (method === "POST") {
    const data = await body(request,MAX_SAVE_BYTES);
    const identity = profile(data?.profile);
    if (!identity) return fail(400,"캐릭터 이름은 한글·영문·숫자 등 2~14자로 입력해주세요.");
    const imported = data.legacy == null ? null : progress(data.legacy);
    if (data.legacy != null && !imported) return fail(400,"이전 세이브를 가져올 수 없어요.");
    const entry = { profile: identity, progress: imported, revision: 0, updated: now };
    if (!await put(store,saveKey,entry)) return fail(409,"이미 캐릭터가 있는 슬롯이에요.");
    return reply(entry,201);
  }
  if (method === "PUT" && saved) {
    const data = await body(request,MAX_SAVE_BYTES);
    const current = progress(data?.progress);
    if (!current) return fail(400,"진행 기록을 저장할 수 없어요.");
    if (data.revision !== saved.value.revision) return fail(409,"다른 탭에 더 최신 저장이 있어요.");
    const next = { ...saved.value, progress: current, revision: saved.value.revision + 1, updated: now };
    if (!await put(store,saveKey,next,saved)) return fail(409,"다른 탭에 더 최신 저장이 있어요.");
    return reply({ revision: next.revision, updated: now });
  }
  return fail(404,"캐릭터 슬롯을 찾을 수 없어요.");
}

async function slots(store, id) {
  return await Promise.all(Array.from({ length:4 }, async (_,index) => {
    const saved = await record(store,"slots/"+id+"/"+index);
    return saved ? brief(index,saved.value) : null;
  }));
}

export default {
  async fetch(request, env) {
    if (!new URL(request.url).pathname.startsWith("/api/")) return asset(request);
    if (!env.SAVES) return fail(503,"계정 저장소가 아직 연결되지 않았어요.");
    try {
      return await accounts(request,env.SAVES);
    } catch (error) {
      console.error("Maplee storage operation failed", error?.name || "Error");
      return fail(503,"저장소에 연결할 수 없어요. 잠시 후 다시 시도해주세요.");
    }
  }
};
