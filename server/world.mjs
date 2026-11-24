// Shared field state. Positions are transient and save slots remain independent.
const WORLD_POLL_MS = 320;
const WORLD_PRESENCE_MS = 18_000;
const WORLD_REWARD_MS = 120_000;

function worldRegion(x) {
  return SHARED_WORLD.ends.findIndex(end => x < end);
}

function worldPose(input) {
  if (!input || !Number.isFinite(input.x) || input.x < 24 || input.x > SHARED_WORLD.ends.at(-1) - 24 ||
      !Number.isFinite(input.y) || input.y < -650 || input.y > 540 || !JOBS.has(input.job)) return null;
  const equipment = Object.fromEntries(Object.entries(SHARED_WORLD.items).map(([slot, items]) =>
    [slot, items.includes(input.equipment?.[slot]) ? input.equipment[slot] : null]));
  return {
    x: Math.round(input.x), y: Math.round(input.y), region: worldRegion(input.x), job: input.job,
    level: Number.isInteger(input.level) ? Math.min(200, Math.max(1, input.level)) : 1,
    facing: input.facing === -1 ? -1 : 1,
    frame: Number.isInteger(input.frame) && input.frame >= 0 && input.frame < 28 ? input.frame : 0,
    swing: Number.isInteger(input.swing) && input.swing >= 0 && input.swing < 24 ? input.swing : null,
    equipment
  };
}

function patrolX(monster, time) {
  const width = monster.right - monster.left;
  const traveled = (time * .06 * monster.speed + (monster.direction > 0 ?
    monster.home - monster.left : 2 * width - (monster.home - monster.left))) % (2 * width);
  return monster.left + (traveled <= width ? traveled : 2 * width - traveled);
}

function worldSnapshot(combat, now) {
  return Object.entries(combat?.monsters || {}).map(([id, monster]) => {
    const respawned = monster.until && monster.until <= now;
    return [Number(id), respawned ? SHARED_WORLD.monsters[id].hp : monster.hp,
      monster.life + (respawned ? 1 : 0), respawned ? 0 : monster.until];
  });
}

function applyWorldHits(combat, actor, sequence, hits, now) {
  if (sequence <= (combat.cursors[actor]?.sequence ?? 0)) return null;
  combat.cursors[actor] = { sequence, at: now };
  for (const [key, row] of Object.entries(combat.cursors)) {
    if (row.at < now - WORLD_REWARD_MS) delete combat.cursors[key];
  }
  const awards = [];
  for (const { id, life, power, x } of hits) {
    const spec = SHARED_WORLD.monsters[id];
    let monster = combat.monsters[id] ?? { hp: spec.hp, life: 0, until: 0, by: {} };
    if (monster.until && monster.until <= now)
      monster = { hp: spec.hp, life: monster.life + 1, until: 0, by: {} };
    combat.monsters[id] = monster;
    if (monster.until || monster.life !== life) continue;
    // The local browser resolves its attack box; the server constrains the
    // hit to a nearby spawn, bounds the amount, and owns HP and respawns.
    const contact = patrolX(spec, now);
    if (Math.abs(x - contact) > 420) continue;
    monster.hp = Math.max(0, monster.hp - power);
    monster.by[actor] = now;
    for (const [key, at] of Object.entries(monster.by)) {
      if (at < now - WORLD_REWARD_MS) delete monster.by[key];
    }
    if (monster.hp !== 0) continue;
    monster.until = Math.ceil((now + spec.recovery) / spec.wave) * spec.wave;
    const event = id + ":" + monster.life;
    for (const credit of Object.keys(monster.by)) awards.push([credit, event, id, Math.round(contact)]);
    monster.by = {};
  }
  return awards;
}

async function updateWorldCombat(db, account, actor, region, sequence, hits, now) {
  for (let attempt = 0; attempt < 6; attempt++) {
    const row = await db.prepare("SELECT revision, state FROM world_combat WHERE region = ?").bind(region).first();
    const combat = row ? JSON.parse(row.state) : { monsters: {}, cursors: {} };
    const awards = applyWorldHits(combat, actor, sequence, hits, now);
    if (awards === null) return true;
    const version = row?.revision ?? 0;
    const change = random(12);
    const commands = [db.prepare(
      `INSERT INTO world_combat (region, revision, last_change, state)
       SELECT ?, ?, ?, ? WHERE EXISTS
         (SELECT 1 FROM world_presence WHERE account = ? AND actor = ?)
       ON CONFLICT(region) DO UPDATE SET revision = excluded.revision,
         last_change = excluded.last_change, state = excluded.state
       WHERE world_combat.revision = ?`
    ).bind(region, version + 1, change, JSON.stringify(combat), account, actor, version)];
    if (awards.length) commands.push(db.prepare(
      `INSERT OR IGNORE INTO world_rewards (actor, event, monster, x, issued)
       SELECT json_extract(value, '$[0]'), json_extract(value, '$[1]'),
              json_extract(value, '$[2]'), json_extract(value, '$[3]'), ?
       FROM json_each(?) WHERE EXISTS
         (SELECT 1 FROM world_combat WHERE region = ? AND last_change = ?)`
    ).bind(now, JSON.stringify(awards), region, change));
    const [result] = await db.batch(commands);
    if (result.meta.changes) return true;
  }
  return false;
}

function worldHits(input, pose) {
  const regions = new Map();
  for (const hit of input.slice(0, 30)) {
    if (!hit || !Number.isInteger(hit.id) || !Number.isInteger(hit.life) || hit.life < 0 ||
        !Number.isInteger(hit.power) || hit.power < 1 || hit.power > 1800 ||
        !Number.isInteger(hit.x) || !Number.isInteger(hit.y)) continue;
    const spec = SHARED_WORLD.monsters[hit.id];
    if (!spec || Math.abs(hit.y - spec.y) > (spec.ledge ? 136 : 190) ||
        worldRegion(hit.x) !== spec.region ||
        (spec.region === pose.region && Math.abs(hit.x - pose.x) > 300)) continue;
    if (!regions.has(spec.region)) regions.set(spec.region, []);
    regions.get(spec.region).push(hit);
  }
  return regions;
}

function worldViewQueries(db, pose, actor, now) {
  return [
    db.prepare("SELECT actor, name, pose FROM world_presence WHERE region = ? AND seen > ? AND actor != ? ORDER BY seen DESC LIMIT 40")
      .bind(pose.region, now - WORLD_PRESENCE_MS, actor),
    db.prepare("SELECT state FROM world_combat WHERE region = ?").bind(pose.region),
    db.prepare("SELECT event, monster, x FROM world_rewards WHERE actor = ? AND issued >= ? ORDER BY issued LIMIT 60")
      .bind(actor, now - WORLD_REWARD_MS)
  ];
}

async function sharedWorld(request, store, db, session, action) {
  if (request.method !== "POST") return fail(405, "요청 방식을 확인해주세요.");
  if (!db) return fail(503, "공용 월드 저장소에 연결할 수 없어요.");
  const data = await body(request, 8192);
  if (!data) return fail(400, "월드 요청을 읽을 수 없어요.");
  const now = Date.now();
  if (action === "leave") {
    if (typeof data.actor === "string")
      await db.prepare("DELETE FROM world_presence WHERE account = ? AND actor = ?")
        .bind(session.id, data.actor).run();
    return reply({});
  }
  if (data.layout !== SHARED_WORLD.layout) return fail(426, "새 버전을 불러오려면 새로고침해주세요.");
  const pose = worldPose(data.pose);
  if (!pose) return fail(400, "캐릭터 위치를 확인할 수 없어요.");
  let actor = data.actor;
  let view;
  if (action === "join") {
    if (![0, 1, 2, 3].includes(data.slot)) return fail(400, "캐릭터 슬롯을 선택해주세요.");
    const slot = await record(store, "slots/" + session.id + "/" + data.slot);
    if (!slot) return fail(404, "선택한 캐릭터를 찾을 수 없어요.");
    actor = random(14);
    const result = await db.batch([
      db.prepare(
        `INSERT INTO world_presence (account, actor, name, region, seen, pose) VALUES (?, ?, ?, ?, ?, ?)
         ON CONFLICT(account) DO UPDATE SET actor = excluded.actor, name = excluded.name,
           region = excluded.region, seen = excluded.seen, pose = excluded.pose`
      ).bind(session.id, actor, slot.value.profile.name, pose.region, now, JSON.stringify(pose)),
      db.prepare("DELETE FROM world_presence WHERE seen < ?").bind(now - WORLD_PRESENCE_MS * 4),
      db.prepare("DELETE FROM world_rewards WHERE issued < ?").bind(now - WORLD_REWARD_MS),
      ...worldViewQueries(db, pose, actor, now)
    ]);
    view = result.slice(3);
  } else if (action === "sync") {
    if (!/^[0-9a-f]{28}$/.test(actor) || !Number.isSafeInteger(data.seq) || data.seq < 1 ||
        !Array.isArray(data.hits) || !Array.isArray(data.ack)) return fail(400, "월드 동기화 요청을 확인해주세요.");
    const update = db.prepare(
      "UPDATE world_presence SET region = ?, seen = ?, pose = ? WHERE account = ? AND actor = ? AND seen <= ?"
    ).bind(pose.region, now, JSON.stringify(pose), session.id, actor, now - 100);
    const idle = !data.hits.length && !data.ack.length;
    // Movement-only updates can write the pose and read the field in one round trip.
    const [changed, ...snapshot] = idle
      ? await db.batch([update, ...worldViewQueries(db, pose, actor, now)])
      : [await update.run()];
    if (!changed.meta.changes) {
      const row = await db.prepare("SELECT actor FROM world_presence WHERE account = ?").bind(session.id).first();
      if (!row) return fail(410, "월드에 다시 접속해야 해요.");
      return row.actor === actor ? fail(429, "잠시 후 다시 연결해요.") : fail(409, "다른 창에서 이 계정이 월드에 접속했어요.");
    }
    if (idle) view = snapshot;
    for (const [region, hits] of worldHits(data.hits, pose)) {
      if (!await updateWorldCombat(db, session.id, actor, region, data.seq, hits, now))
        return fail(503, "월드 동기화를 다시 시도해요.");
    }
    const acknowledgments = data.ack.slice(0, 60).filter(event => typeof event === "string" && /^\d+:\d+$/.test(event));
    if (acknowledgments.length)
      await db.prepare("DELETE FROM world_rewards WHERE actor = ? AND event IN (SELECT value FROM json_each(?))")
        .bind(actor, JSON.stringify(acknowledgments)).run();
  } else {
    return fail(404, "월드 주소를 확인해주세요.");
  }

  const [nearby, hunting, rewards] = view ?? await db.batch(worldViewQueries(db, pose, actor, now));
  const players = nearby.results.map(row => ({ id: row.actor, name: row.name, ...JSON.parse(row.pose) }));
  const state = hunting.results[0]?.state;
  return reply({
    actor, now, poll: WORLD_POLL_MS, region: pose.region, players,
    monsters: worldSnapshot(state ? JSON.parse(state) : null, now), rewards: rewards.results
  });
}
