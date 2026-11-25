// The client predicts movement and draws effects. The field resolves attacks and awards.
const FIELD_POLL = 320;
const FIELD_LINGER = 18_000;
const CREDIT_WINDOW = 25_000;
const POSE_INTERVAL_LIMIT = 6500;
const POSE_X_TOLERANCE = 45;
const POSE_Y_TOLERANCE = 65;
const POSE_X_SPEED = .64;
const POSE_RISE_SPEED = 1.08;
const POSE_FALL_SPEED = 1.85;

function fieldRegion(x) {
  return rules().ends.findIndex(end => x < end);
}

function fieldGround(x) {
  const points = rules().ground;
  let left = 0, right = points.length - 1;
  while (right - left > 1) {
    const middle = (right + left) >> 1;
    if (points[middle][0] <= x) left = middle;
    else right = middle;
  }
  const [a, y] = points[left], [b, z] = points[right];
  return y + (z - y) * Math.min(1, Math.max(0, (x - a) / (b - a)));
}

function fieldFloor(x) {
  return Math.round(fieldGround(x));
}

function shapePose(input) {
  if (!Number.isSafeInteger(input?.x) || !Number.isSafeInteger(input.y) ||
      input.x < 24 || input.x > rules().ends.at(-1) - 24 || input.y < -650 || input.y > 540) return null;
  return {
    x:input.x, y:input.y, facing:input.facing === -1 ? -1 : 1,
    frame:Number.isInteger(input.frame) && input.frame >= 0 && input.frame < 28 ? input.frame : 0,
    swing:Number.isInteger(input.swing) && input.swing >= 0 && input.swing < rules().basicTicks ? input.swing : null
  };
}

function fieldAppearance(pose, state) {
  return { ...pose, region:fieldRegion(pose.x), job:state.job, level:state.level, equipment:state.equipment };
}

function arenaKey(mode, character, region) {
  return (mode === "solo" ? character : "public") + "/" + rules().mapIds[region];
}

function patrolX(spec, time) {
  const width = spec.right - spec.left;
  if (!width) return spec.home;
  const origin = spec.direction > 0 ? spec.home - spec.left : 2 * width - (spec.home - spec.left);
  const traveled = (time * .06 * spec.speed + origin) % (2 * width);
  return spec.left + (traveled <= width ? traveled : 2 * width - traveled);
}

function fieldBody(spec, at) {
  const x = patrolX(spec, at);
  const y = (spec.ledge ? spec.y : fieldGround(x)) - spec.hover;
  const scale = spec.scale;
  const half = spec.body[0] * scale / 2;
  return { x, y, bounds:[x - half, y - spec.body[1] * scale, x + half, y] };
}

function intersects(a, b) {
  return a[0] <= b[2] && a[2] >= b[0] && a[1] <= b[3] && a[3] >= b[1];
}

function fieldBounds(input, previous, elapsed) {
  if (rules().walkGroups[fieldRegion(input.x)] !== rules().walkGroups[fieldRegion(previous.x)])
    return { ...previous, facing:input.facing };
  const interval = Math.min(POSE_INTERVAL_LIMIT, elapsed);
  const x = Math.abs(input.x - previous.x) <= POSE_X_TOLERANCE + interval * POSE_X_SPEED ? input.x : previous.x;
  const deltaY = input.y - previous.y;
  const vertical = POSE_Y_TOLERANCE + interval * (deltaY > 0 ? POSE_FALL_SPEED : POSE_RISE_SPEED);
  const y = Math.abs(deltaY) <= vertical && input.y <= fieldFloor(x) + 4
    ? input.y : Math.min(previous.y, fieldFloor(x));
  return { ...input, x, y };
}

function updatePosition(input, previous, elapsed, move, voyage, now) {
  if (voyage) {
    if (now < voyage.until) return { pose:previous, warp:null, voyage };
    const x = voyage.destination;
    return { pose:{ ...previous,x,y:fieldFloor(x) }, warp:voyage.mode, voyage:null };
  }
  const ordinary = fieldBounds(input, previous, elapsed);
  if (move === "home") return { pose:{ ...ordinary, x:rules().start, y:fieldFloor(rules().start) }, warp:"home", voyage:null };
  const portal = Number.isInteger(move) && rules().portals.find(([x]) =>
    move === x && Math.abs(ordinary.x - x) <= 48 && Math.abs(ordinary.y - fieldFloor(x)) <= 33);
  const mode = portal && rules().transports[move];
  if (mode) return { pose:ordinary, warp:null, voyage:{ mode, start:now, until:now + (mode === "boat" ? 3200 : 3800),
    destination:portal[1], region:portal[2] } };
  return portal
    ? { pose:{ ...ordinary, x:portal[1], y:fieldFloor(portal[1]) }, warp:"portal", voyage:null }
    : { pose:ordinary, warp:null, voyage:null };
}

const regionSpawns = rules().ends.map((_, region) => rules().monsters.flatMap((spec, index) =>
  spec.region === region ? [index] : []));
const spawnIndex = Object.fromEntries(rules().monsters.map((spec, index) => [spec.id, index]));

function monsterAlive(encounter, index, at) {
  const entry = encounter[rules().monsters[index].id];
  return !entry || !entry.until || entry.until <= at;
}

function fieldSnapshot(encounter, now) {
  return Object.entries(encounter).map(([id, monster]) => {
    const index = spawnIndex[id], spec = rules().monsters[index];
    const revived = monster.until && monster.until <= now;
    return [index, revived ? spec.hp : monster.hp, monster.life + Number(Boolean(revived)), revived ? 0 : monster.until];
  });
}

function damageMonster(context, index, power, at, effect) {
  const { encounter, area, owner, hits, rewards, now } = context;
  const spec = rules().monsters[index];
  let entry = encounter[spec.id] ?? { hp:spec.hp, life:0, until:0, credits:{} };
  if (entry.until && entry.until <= at) entry = { hp:spec.hp, life:entry.life + 1, until:0, credits:{} };
  if (entry.until) return;
  encounter[spec.id] = entry;
  context.combatChanged = true;
  entry.hp = Math.max(0, entry.hp - power);
  entry.credits[owner] = now;
  hits.push([index, power, effect]);
  if (entry.hp !== 0) return;
  entry.until = Math.ceil((now + spec.recovery) / spec.wave) * spec.wave;
  const source = area + "/" + spec.id + "/" + entry.life;
  for (const [character, at] of Object.entries(entry.credits))
    if (now - at <= CREDIT_WINDOW) rewards.push([character, source, JSON.stringify(rollReward(spec))]);
  entry.credits = {};
}

function attackTargets(context, shape, reach, facing, origin, at, primary) {
  const candidates = regionSpawns[fieldRegion(origin.x)].filter(index => monsterAlive(context.encounter, index, at));
  if (shape === "arrow" || shape === "bolt") {
    const y = origin.y - 24;
    let nearest = null;
    for (const index of candidates) {
      const body = fieldBody(rules().monsters[index], at);
      const flight = Math.max(0, Math.abs(body.x - origin.x) - 18) / .9;
      const moved = fieldBody(rules().monsters[index], at + flight);
      const from = origin.x + facing * 18, end = from + facing * reach;
      if (!intersects([Math.min(from,end)-3, y-4, Math.max(from,end)+3, y+4], moved.bounds)) continue;
      if (!nearest || flight < nearest.flight) nearest = { index, flight, x:moved.x };
    }
    if (!nearest) return [];
    const result = [nearest.index];
    if (primary && shape === "arrow") {
      const splash = [nearest.x-75, y-48, nearest.x+75, y+48];
      result.push(...candidates.filter(index => index !== nearest.index &&
        intersects(splash, fieldBody(rules().monsters[index], at+nearest.flight).bounds)).slice(0,5));
    }
    return result;
  }
  const back = ["slash", "arc", "punch", "stab"].includes(shape) ? 4 : reach;
  const ends = [origin.x - facing * back, origin.x + facing * reach];
  const box = [Math.min(...ends), origin.y - (shape === "stars" ? 92 : primary ? 64 : 53),
    Math.max(...ends), origin.y + 5];
  return candidates.map(index => [index, fieldBody(rules().monsters[index], at)])
    .filter(([index, body]) => (shape !== "heal" || rules().monsters[index].undead) && intersects(box, body.bounds))
    .sort((a,b) => Math.abs(a[1].x-origin.x) - Math.abs(b[1].x-origin.x))
    .slice(0, shape === "stab" ? 1 : 6).map(([index]) => index);
}

function resolveAttack(context, kind, at, facing, origin) {
  const { state, runtime } = context;
  const primary = kind === "primary";
  if (kind !== "basic" && !primary || at < runtime.stagger) return false;
  const job = rules().jobs[state.job], weapon = state.equipment.weapon;
  const attack = rules().weaponAttacks[weapon] ?? (weapon ? "slash" : "punch");
  const shape = primary ? job.shape : attack;
  const reach = primary ? job.reach : { arrow:222, bolt:158 }[shape] ?? 54;
  const melee = !primary && ["slash", "punch"].includes(shape);
  const impact = { stab:9, kick:13, heal:16 }[shape] ?? (melee ? rules().basicImpact : rules().swingImpact);
  const started = at - impact * 1000 / 60;
  if (started < runtime.attack || primary && (started < runtime.primary || state.mp < job.cost)) return false;
  const duration = { stab:25, kick:32, heal:35 }[shape] ??
    (primary || ["arrow","bolt"].includes(shape) ? rules().swingTicks : rules().basicTicks);
  runtime.attack = started + duration * 1000 / 60 - 18;
  let power = characterStats(state).attack;
  const support = rules().supports[state.job];
  if (runtime.buff > at && support?.stat === "bless") power += support.power * (1 + .35 * (state.skillRanks.support - 1));
  if (primary) {
    runtime.primary = started + job.cooldown * 1000 / 60 - 18;
    state.mp -= job.cost;
    power = Math.ceil(power * (job.power + .25 * (state.skillRanks.primary - 1)));
    if (shape === "heal") {
      const maximum = characterStats(state).hp;
      state.hp = Math.min(maximum, state.hp + Math.round(maximum * (.22 + .04 * state.skillRanks.primary)));
    }
  }
  if (support?.stat === "stealth") runtime.buff = 0;
  for (const target of attackTargets(context, shape, reach, facing, origin, at, primary)) {
    const effect = shape === "stab" ? "stab" : primary || ["arrow","bolt"].includes(shape) ? shape + "_hit" : "impact";
    damageMonster(context, target, Math.round(power), at, effect);
    if (shape === "stab" && monsterAlive(context.encounter, target, at))
      damageMonster(context, target, Math.round(power), at, "stab_hit");
  }
  return true;
}

function damageCharacter(context, index, origin, at) {
  const { state, runtime } = context;
  const monster = rules().monsters[index];
  if (!monster || at < runtime.inv || monster.region !== fieldRegion(origin.x) ||
      !monsterAlive(context.encounter, index, at)) return false;
  const { x, y } = fieldBody(monster, at);
  const entry = context.encounter[monster.id];
  const enraged = monster.elite && entry?.hp <= monster.hp / 2;
  if (Math.abs(x - origin.x) > (enraged ? 90 : monster.reach) + 12 || Math.abs(y - origin.y) > 42 + monster.hover)
    return false;
  const support = runtime.buff > at ? rules().supports[state.job] : null;
  if (support?.stat === "stealth") return false;
  const buff = (support?.power ?? 0) * (1 + .35 * (state.skillRanks.support - 1));
  const stats = characterStats(state);
  let lost = Math.max(1, Math.ceil(monster.attack * (enraged ? 1.2 : 1)) -
    Math.floor(stats.defense + (support?.stat === "bless" ? buff : 0)));
  if (support?.stat === "reflect") damageMonster(context, index, Math.max(1, Math.round(lost*buff)), at, "impact");
  if (support?.stat === "guard") {
    const absorbed = Math.min(state.mp, Math.round(lost * Math.min(.8, buff)));
    state.mp -= absorbed;
    lost -= absorbed;
  }
  state.hp -= lost;
  runtime.inv = at + 900;
  runtime.stagger = at + 150;
  if (state.hp <= 0) {
    Object.assign(state, { hp:stats.hp, mp:stats.mp });
    context.died = true;
  }
  return true;
}

function applyFieldOps(context, ops, pose, previous, elapsed) {
  const { state, runtime, now, results } = context;
  const regenerate = Math.floor((now - runtime.manaAt) / 1500);
  if (regenerate > 0) {
    const before = state.mp;
    state.mp = Math.min(characterStats(state).mp, state.mp + regenerate);
    runtime.manaAt += regenerate * 1500;
    context.changed ||= before !== state.mp;
  }
  for (const [i, op] of ops.entries()) {
    if (!Array.isArray(op) || typeof op[0] !== "string" ||
        !["string","number"].includes(typeof op[1])) continue;
    const [action, argument, clock, x, y, facing] = op;
    let accepted = false;
    if (["attack", "hurt", "support"].includes(action)) {
      if (!Number.isSafeInteger(clock) || clock < now - 1600 || clock > now + 100 || clock < runtime.lastOp) continue;
      const sample = shapePose({ x, y, facing });
      if (!sample || fieldRegion(x) !== fieldRegion(previous.x)) continue;
      const origin = fieldBounds(sample, previous, elapsed);
      if (sample.x !== origin.x || sample.y !== origin.y ||
          Math.abs(pose.x - origin.x) > 290 || Math.abs(pose.y - origin.y) > 260) continue;
      const at = Math.min(clock,now);
      if (action === "attack") accepted = resolveAttack(context, argument, at, origin.facing, origin);
      else if (action === "hurt") accepted = damageCharacter(context, argument, origin, at);
      else {
        const support = rules().supports[state.job], rank = state.skillRanks.support;
        if (support && rank && at >= runtime.support && at >= runtime.stagger && state.mp >= support.cost) {
          state.mp -= support.cost;
          runtime.support = at + 12_000;
          runtime.buff = at + (420 + 90*(rank-1)) * 1000 / 60;
          accepted = true;
        }
      }
      if (accepted) runtime.lastOp = at;
    } else {
      accepted = useCharacterAction(state, action, argument, pose);
      if (accepted && action === "job") runtime.buff = 0;
      results.push([i, accepted]);
    }
    context.changed ||= accepted && !(action === "attack" && argument === "basic");
    if (context.died) break;
  }
}

async function fieldActor(db, account, checksCombat = false) {
  const combat = checksCombat ? ", e.state AS encounter_state, e.revision AS encounter_revision" : "";
  const join = checksCombat ? "LEFT JOIN field_encounters e ON e.area = f.area" : "";
  return db.prepare(`SELECT f.*, c.state AS character_state, c.revision AS character_revision ${combat}
    FROM field_sessions f JOIN characters c ON f.character_id = c.id ${join} WHERE f.account = ?`)
    .bind(account).first();
}

async function syncMovement(db, account, data, input, now) {
  const { actor, seq } = data;
  const change = random(12);
  const response = { sample:[input.x,input.y] };
  // A within-bounds movement sample and its snapshot need one D1 round trip.
  // Rebases, mana ticks and gameplay commands use the full sync transaction.
  const update = db.prepare(`UPDATE field_sessions SET seen = ?, sequence = ?, response = ?, change_id = ?,
      pose = json_set(pose, '$.x', ?, '$.y', ?, '$.facing', ?, '$.frame', ?, '$.swing', ?)
    WHERE account = ? AND actor = ? AND sequence = ? AND seen > 0 AND ? - seen >= 90
      AND ? - json_extract(runtime, '$.manaAt') < 1500
      AND json_extract(runtime, '$.voyage') IS NULL
      AND area = (CASE mode WHEN 'solo' THEN character_id ELSE 'public' END) || '/' || ?
      AND abs(? - json_extract(pose, '$.x')) <= ? + MIN(?, ? - seen) * ?
      AND ? - json_extract(pose, '$.y') BETWEEN -(? + MIN(?, ? - seen) * ?) AND ? + MIN(?, ? - seen) * ?
    RETURNING actor, area, pose, character_id`).bind(now,seq,JSON.stringify(response),change,
      input.x,input.y,input.facing,input.frame,input.swing,account,actor,seq-1,now,now,rules().mapIds[fieldRegion(input.x)],
      input.x,POSE_X_TOLERANCE,POSE_INTERVAL_LIMIT,now,POSE_X_SPEED,input.y,
      POSE_Y_TOLERANCE,POSE_INTERVAL_LIMIT,now,POSE_RISE_SPEED,POSE_Y_TOLERANCE,POSE_INTERVAL_LIMIT,now,POSE_FALL_SPEED);
  const [moved, ...snapshot] = await db.batch([update, ...fieldViewQueries(db, actor, now, change)]);
  return moved.results[0] ? fieldView(db,moved.results[0],response,now,data.stateVersion,snapshot) : null;
}

async function syncField(db, session, data, input, now) {
  const { seq, ops, move } = data;
  if (!ops.length && move == null && input.y <= fieldFloor(input.x)+4) {
    const moved = await syncMovement(db,session.id,data,input,now);
    if (moved) return moved;
  }
  const checksCombat = ops.some(op => Array.isArray(op) && ["attack","hurt"].includes(op[0]));
  for (let attempt = 0; attempt < 5; attempt++) {
    const actor = await fieldActor(db,session.id,checksCombat);
    if (!actor) return fail(410, "월드에 다시 접속해야 해요.");
    if (actor.actor !== data.actor) return fail(409, "다른 창에서 이 계정이 월드에 접속했어요.");
    if (!actor.seen) return fail(410, "월드에 다시 접속해야 해요.");
    if (seq === actor.sequence)
      return fieldView(db, actor, JSON.parse(actor.response), now, data.stateVersion);
    if (seq !== actor.sequence + 1) return fail(409, "월드 동기화 순서를 확인할 수 없어요.");
    if (now - actor.seen < 90) return fail(429, "잠시 후 다시 연결해요.");

    const old = JSON.parse(actor.pose), elapsed = now - actor.seen;
    const state = JSON.parse(actor.character_state);
    const runtime = JSON.parse(actor.runtime);
    const onBoard = Boolean(runtime.voyage);
    let { pose, warp, voyage } = updatePosition(input,old,elapsed,move,runtime.voyage,now);
    runtime.voyage = voyage;
    const actionPose = fieldBounds(input, old, elapsed);
    const combatRevision = actor.encounter_revision ?? 0;
    const context = { encounter:JSON.parse(actor.encounter_state ?? "{}"), area:actor.area, state, runtime,
      owner:actor.character_id, hits:[], rewards:[], results:[], now, changed:false, combatChanged:false };
    applyFieldOps(context, onBoard ? [] : ops, actionPose, old, elapsed);
    if (context.died) {
      pose = { ...pose, x:rules().start, y:fieldFloor(rules().start) };
      warp = "respawn";
      runtime.voyage = voyage = null;
    }
    const appearance = fieldAppearance(pose, state);
    const area = arenaKey(actor.mode, actor.character_id, appearance.region);
    const response = { sample:[input.x,input.y], hits:context.hits, results:context.results, warp, voyage };
    const change = random(12);
    const commands = [db.prepare(`UPDATE field_sessions SET area = ?, pose = ?, seen = ?, sequence = ?,
      runtime = ?, response = ?, change_id = ?
      WHERE account = ? AND actor = ? AND sequence = ?
        AND EXISTS (SELECT 1 FROM characters WHERE id = ? AND revision = ?)
        AND (? = 0 OR COALESCE((SELECT revision FROM field_encounters WHERE area = ?), 0) = ?)`).bind(
      area, JSON.stringify(appearance), now, seq, JSON.stringify(runtime), JSON.stringify(response), change,
      session.id, actor.actor, actor.sequence, actor.character_id, actor.character_revision,
      Number(checksCombat), actor.area, combatRevision)];
    if (context.changed || warp) {
      state.x = pose.x;
      state.y = pose.y;
      commands.push(db.prepare(`UPDATE characters SET state = ?, revision = revision + 1, updated = ?, change_id = ?
        WHERE id = ? AND EXISTS (SELECT 1 FROM field_sessions WHERE actor = ? AND change_id = ?)`)
        .bind(JSON.stringify(state), Math.floor(now/1000), change, actor.character_id, actor.actor, change));
    }
    if (context.combatChanged) commands.push(db.prepare(`INSERT INTO field_encounters (area, state, revision)
      SELECT ?, ?, ? WHERE EXISTS (SELECT 1 FROM field_sessions WHERE actor = ? AND change_id = ?)
      ON CONFLICT(area) DO UPDATE SET state = excluded.state, revision = excluded.revision`)
      .bind(actor.area, JSON.stringify(context.encounter), combatRevision+1, actor.actor, change));
    if (context.rewards.length) commands.push(db.prepare(`INSERT OR IGNORE INTO character_rewards (character_id, source, reward)
      SELECT json_extract(value, '$[0]'), json_extract(value, '$[1]'), json_extract(value, '$[2]')
      FROM json_each(?) WHERE EXISTS (SELECT 1 FROM field_sessions WHERE actor = ? AND change_id = ?)`)
      .bind(JSON.stringify(context.rewards), actor.actor, change));
    const current = { ...actor, area, pose:JSON.stringify(appearance) };
    const [written, ...snapshot] = await db.batch([...commands, ...fieldViewQueries(db,actor.actor,now,change)]);
    if (written.meta.changes)
      return fieldView(db, current, response, now, data.stateVersion, snapshot.slice(commands.length-1));
  }
  return fail(503, "월드 동기화를 다시 시도해요.");
}

function fieldViewQueries(db, actor, now, change = null) {
  const focus = `WITH own AS (SELECT actor, area, character_id FROM field_sessions WHERE actor = ?
    ${change ? "AND change_id = ?" : ""}) `;
  const key = change ? [actor,change] : [actor];
  return [
    db.prepare(focus + `SELECT f.actor, f.pose, c.profile FROM own JOIN field_sessions f ON f.area = own.area
      JOIN characters c ON c.id = f.character_id WHERE f.seen >= ? AND f.actor <> own.actor LIMIT 40`)
      .bind(...key,now-FIELD_LINGER),
    db.prepare(focus + "SELECT e.state FROM own JOIN field_encounters e ON e.area = own.area").bind(...key),
    db.prepare(focus + "SELECT c.* FROM own JOIN characters c ON c.id = own.character_id").bind(...key),
    db.prepare(focus + `SELECT r.source, r.reward FROM own JOIN character_rewards r ON r.character_id = own.character_id
      WHERE r.applied = 0 LIMIT 60`).bind(...key),
  ];
}

async function fieldView(db, actor, response, now, clientVersion, snapshot) {
  const [nearby, monsters, characters, rewards] = snapshot ?? await db.batch(fieldViewQueries(db,actor.actor,now));
  if (!characters.results.length) return fail(409, "다른 창에서 이 계정이 월드에 접속했어요.");
  const { row, loot } = await settleRewards(db, characters.results[0], rewards.results);
  const pose = JSON.parse(actor.pose);
  const progress = clientVersion === row.revision ? null : JSON.parse(row.state);
  if (progress) delete progress.gear;
  const clock = Date.now();
  return reply({ actor:actor.actor, now:clock, poll:FIELD_POLL, region:pose.region, pose, ...response,
    progress, stateVersion:row.revision, loot,
    players:nearby.results.map(other => ({ id:other.actor, name:JSON.parse(other.profile).name, ...JSON.parse(other.pose) })),
    monsters:fieldSnapshot(JSON.parse(monsters.results[0]?.state ?? "{}"), clock) });
}

async function sharedWorld(request, store, db, session, action) {
  if (request.method !== "POST") return fail(405, "요청 방식을 확인해주세요.");
  if (!db) return fail(503, "공용 월드 저장소에 연결할 수 없어요.");
  const data = await body(request, 12_000);
  if (!data) return fail(400, "월드 요청을 읽을 수 없어요.");
  const now = Date.now();
  if (action === "leave") {
    if (typeof data.actor === "string")
      await db.prepare("UPDATE field_sessions SET seen = 0 WHERE account = ? AND actor = ?")
        .bind(session.id, data.actor).run();
    return reply({});
  }
  if (data.protocol !== FIELD_PROTOCOL || data.layout !== rules().layout)
    return fail(426, "새 버전을 불러오려면 새로고침해주세요.");
  const input = shapePose(data.pose);
  if (!input) return fail(400, "캐릭터 위치를 확인할 수 없어요.");
  if (action === "sync") {
    if (typeof data.actor !== "string" || !/^[a-f0-9]{28}$/.test(data.actor) ||
        !Number.isSafeInteger(data.seq) || data.seq < 1 || !Array.isArray(data.ops) || data.ops.length > 24)
      return fail(400, "월드 동기화 요청을 확인해주세요.");
    return syncField(db, session, data, input, now);
  }
  if (![0,1,2,3].includes(data.slot) || !["shared","solo"].includes(data.mode))
    return fail(400, "캐릭터 슬롯과 플레이 모드를 선택해주세요.");
  const character = await loadCharacter(db, store, session.id, data.slot);
  if (!character) return fail(404, "선택한 캐릭터를 찾을 수 없어요.");
  const state = JSON.parse(character.state);
  const existing = await fieldActor(db, session.id);
  const sameCharacter = existing?.character_id === character.id;
  const recent = sameCharacter ? JSON.parse(existing.pose) : null;
  const origin = recent ?? { ...input, x:state.x, y:fieldFloor(state.x) };
  const pose = fieldAppearance(fieldBounds(input, origin, 220), state);
  const actor = random(14);
  const area = arenaKey(data.mode, character.id, pose.region);
  // Keep attack cooldowns when reconnecting or switching field modes.
  const runtime = sameCharacter ? JSON.parse(existing.runtime) :
    { manaAt:now, attack:0, primary:0, support:0, buff:0, inv:0, stagger:0, lastOp:0 };
  await db.prepare(`INSERT INTO field_sessions (account, actor, character_id, mode, area, pose, seen, runtime)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(account) DO UPDATE SET actor = excluded.actor, character_id = excluded.character_id,
      mode = excluded.mode, area = excluded.area, pose = excluded.pose, seen = excluded.seen,
      runtime = excluded.runtime, sequence = 0, response = '{}', change_id = ''`)
    .bind(session.id, actor, character.id, data.mode, area, JSON.stringify(pose), now - FIELD_POLL, JSON.stringify(runtime)).run();
  return fieldView(db, { actor, area, pose:JSON.stringify(pose), character_id:character.id },
    { voyage:runtime.voyage ?? null }, now);
}
