// Characters and progression are durable in D1. R2 slot objects are read once when migrated.
const FIELD_PROTOCOL = 1;
const objectValue = value => value && typeof value === "object" && !Array.isArray(value) ? value : {};
const countValue = (value, max = 1_000_000_000) =>
  Number.isFinite(value) ? Math.max(0, Math.min(max, Math.trunc(value))) : 0;
const rules = () => SHARED_WORLD;
const known = (table, id) => typeof id === "string" && Object.hasOwn(table, id);

function characterStats(state) {
  const level = state.level - 1;
  const job = rules().jobs[state.job];
  const stats = { hp:100 + 10 * level + job.hp, mp:35 + 4 * level + job.mp,
    attack:4 + 2 * level + job.attack, defense:Math.floor(level / 2) };
  for (const id of Object.values(state.equipment)) {
    const gear = rules().items[id];
    for (const key of Object.keys(stats)) stats[key] += gear?.[key] ?? 0;
  }
  for (const [id, count] of Object.entries(state.attributes)) {
    for (const key of Object.keys(stats)) stats[key] += (rules().attributes[id]?.[key] ?? 0) * count;
  }
  return stats;
}

function canWear(state, id) {
  const item = rules().items[id];
  return Boolean(known(rules().items, id) && item.slot && item.level <= state.level &&
    (!item.job || item.job === state.job || (state.job === "cleric" && ["wand", "tidewand"].includes(id))));
}

function issueItem(state, id, count = 1) {
  if (id === "potion" || id === "tonic") {
    state[id === "potion" ? "pots" : "tonics"] += count;
    return;
  }
  state.bag[id] = (state.bag[id] ?? 0) + count;
  if (!rules().items[id].slot) return;
  // Contiguous ranges encode individual serials even for very large old stacks.
  const stock = state.gear[id] ??= { next:1, ranges:[] };
  const tail = stock.ranges.at(-1);
  if (tail && tail[0] + tail[1] === stock.next) tail[1] += count;
  else stock.ranges.push([stock.next, count]);
  stock.next += count;
}

function spendItem(state, id, count) {
  state.bag[id] -= count;
  if (state.bag[id] === 0) delete state.bag[id];
  const stock = state.gear[id];
  while (stock?.ranges.length && count) {
    const tail = stock.ranges.at(-1);
    const used = Math.min(count, tail[1]);
    tail[1] -= used;
    count -= used;
    if (tail[1] === 0) stock.ranges.pop();
  }
}

function wornIds(character, state) {
  return Object.fromEntries(Object.entries(state.equipment).map(([slot, id]) => {
    const first = state.gear[id]?.ranges[0]?.[0];
    return [slot, first ? character + ":" + id + ":" + first : null];
  }));
}

function rankLevel(id, rank) {
  return id === "primary" ? 2 * rank - 1 : 5 + 2 * rank;
}

function clampVitals(state) {
  const stats = characterStats(state);
  state.hp = Math.max(1, Math.min(state.hp, stats.hp));
  state.mp = Math.min(state.mp, stats.mp);
}

function gainExperience(state, amount) {
  if (state.level >= 200) return;
  state.xp += amount;
  const previous = state.level;
  while (state.level < 200 && state.xp >= 45 + (state.level - 1) * 28) {
    state.xp -= 45 + (state.level - 1) * 28;
    state.level++;
  }
  if (state.level === 200) state.xp = 0;
  if (previous !== state.level) {
    const { hp, mp } = characterStats(state);
    Object.assign(state, { hp, mp });
  }
}

function settingsFrom(state, settings) {
  if (Array.isArray(settings.hotbar)) {
    for (const [i, item] of settings.hotbar.slice(0, 4).entries()) {
      if (item === null || rules().hotbar.includes(item)) state.hotbar[i] = item;
    }
  }
  if (settings.trackedQuest === null || Number.isInteger(settings.trackedQuest) &&
      state.quests[settings.trackedQuest]?.state === 1) state.trackedQuest = settings.trackedQuest;
  if (avatarStyles.has(settings.avatarStyle)) state.avatarStyle = settings.avatarStyle;
}

function migrateProgress(identity, saved) {
  const state = structuredClone(rules().defaults);
  state.gear = {};
  state.bag = {};
  const job = state.job = known(rules().jobs, saved?.job) ? saved.job : identity.job;
  if (!saved) {
    const starter = rules().starterWeapons[job];
    issueItem(state, starter);
    state.equipment.weapon = starter;
    const { hp, mp } = characterStats(state);
    Object.assign(state, { hp, mp });
    return state;
  }
  for (const field of ["level", "xp", "gold", "kills", "pots", "tonics", "hp", "mp"])
    if (Number.isFinite(saved[field])) state[field] = countValue(saved[field], field === "level" ? 200 : undefined);
  state.level = Math.max(1, state.level);
  if (Number.isFinite(saved.x) && saved.x >= 0) {
    let x = saved.x;
    if (!rules().preservedLayouts.includes(saved.worldLayout)) {
      if (saved.worldLayout === 2) x /= 1.25;
      x = Math.round((x - Math.max(0, Math.min(6650, x - 2450)) / 4) * 1.25);
    }
    state.x = Math.max(24, Math.min(rules().ends.at(-1) - 24, Math.round(x)));
    state.y = fieldGround(state.x);
  }
  for (const [id, count] of Object.entries(objectValue(saved.bag))) {
    if (known(rules().items, id) && countValue(count) && !["potion", "tonic"].includes(id))
      issueItem(state, id, countValue(count));
  }
  if (!saved.bag) issueItem(state, rules().starterWeapons[job]);
  state.equipment.weapon = null;
  for (const id of Object.values(objectValue(saved.equipment))) {
    if (state.bag[id] && canWear(state, id)) state.equipment[rules().items[id].slot] = id;
  }
  if (!saved.bag && !saved.equipment) state.equipment.weapon = rules().starterWeapons[job];
  let budget = 3 * (state.level - 1);
  for (const id of Object.keys(state.attributes)) {
    state.attributes[id] = countValue(saved.attributes?.[id], budget);
    budget -= state.attributes[id];
  }
  budget = state.level - 1;
  for (const [id, max] of [["primary", 5], ["support", job === "beginner" ? 0 : 3]]) {
    for (let rank = state.skillRanks[id] + 1; budget > 0 && rank <= max &&
         rank <= saved.skillRanks?.[id] && state.level >= rankLevel(id, rank); rank++) {
      state.skillRanks[id] = rank;
      budget--;
    }
  }
  if (Array.isArray(saved.quests)) {
    for (const [index, entry] of saved.quests.slice(0, rules().quests.length).entries()) {
      if (entry && [0, 1, 2].includes(entry.state))
        state.quests[index] = { state:entry.state, count:countValue(entry.count, rules().quests[index].target) };
    }
  } else if (Number.isInteger(saved.quest) && saved.quest > 0) {
    state.quests[0] = { state:saved.quest >= 2 ? 2 : 1, count:Math.min(state.kills, rules().quests[0].target) };
    if (saved.quest >= 4) state.quests[1] = { state:2, count:1 };
  }
  for (let i = 0; i < rules().species.length; i++) {
    const kills = countValue(saved.bestiary?.[i]);
    if (kills) state.bestiary[i] = kills;
  }
  settingsFrom(state, saved);
  clampVitals(state);
  return state;
}

function characterDocument(row) {
  const progress = JSON.parse(row.state);
  return { characterId:row.id, profile:JSON.parse(row.profile), progress, revision:row.save_revision,
    stateVersion:row.revision, updated:row.updated, equipmentIds:wornIds(row.id, progress) };
}

async function slotRow(db, account, slot) {
  return db.prepare("SELECT * FROM characters WHERE account = ? AND slot = ?").bind(account, slot).first();
}

async function insertCharacter(db, account, slot, identity, saved, revision, updated) {
  return db.prepare(`INSERT OR IGNORE INTO characters (id, account, slot, profile, state, save_revision, updated)
    VALUES (?, ?, ?, ?, ?, ?, ?)`).bind(random(16), account, slot, JSON.stringify(identity),
    JSON.stringify(migrateProgress(identity, saved)), revision, updated).run();
}

async function loadCharacter(db, store, account, slot) {
  const current = await slotRow(db, account, slot);
  if (current) return current;
  const legacy = (await record(store, "slots/" + account + "/" + slot))?.value;
  if (!legacy) return null;
  await insertCharacter(db, account, slot, legacy.profile, legacy.progress, legacy.revision ?? 0, legacy.updated);
  return slotRow(db, account, slot);
}

function rollReward(monster) {
  const spec = rules().species[monster.kind];
  const items = [spec.loot];
  if (spec.elite || Math.random() < .16) items.push(spec.rare);
  if (spec.equipmentDrops?.length && Math.random() < .10)
    items.push(spec.equipmentDrops[Math.floor(Math.random() * spec.equipmentDrops.length)]);
  if (Math.random() < .18) items.push(monster.kind % 2 ? "tonic" : "potion");
  return { kind:monster.kind, gold:spec.gold, xp:spec.xp, items };
}

function applyReward(state, reward) {
  state.kills++;
  state.bestiary[reward.kind] = (state.bestiary[reward.kind] ?? 0) + 1;
  gainExperience(state, reward.xp);
  state.gold += reward.gold;
  for (const item of reward.items) issueItem(state, item);
  for (const [index, entry] of state.quests.entries()) {
    const quest = rules().quests[index];
    if (entry.state === 1 && quest.matches.includes(reward.kind))
      entry.count = Math.min(quest.target, entry.count + 1);
  }
}

function pendingRewards(db, id) {
  return db.prepare(`SELECT source, reward FROM character_rewards
    WHERE character_id = ? AND applied = 0 LIMIT 60`).bind(id);
}

async function settleRewards(db, row, queued = null) {
  const id = row.id;
  for (let attempt = 0; attempt < 5; attempt++) {
    const pending = queued ?? (await pendingRewards(db, id).all()).results;
    if (!pending.length) return { row, loot:null };
    const state = JSON.parse(row.state);
    const rewards = pending.map(item => JSON.parse(item.reward));
    for (const reward of rewards) applyReward(state, reward);
    const change = random(12);
    const [write] = await db.batch([
      db.prepare(`UPDATE characters SET state = ?, revision = revision + 1, updated = ?, change_id = ?
        WHERE id = ? AND revision = ?`).bind(JSON.stringify(state), Math.floor(Date.now()/1000), change, id, row.revision),
      db.prepare(`UPDATE character_rewards SET applied = 1 WHERE character_id = ?
        AND source IN (SELECT value FROM json_each(?))
        AND EXISTS (SELECT 1 FROM characters WHERE id = ? AND change_id = ?)`)
        .bind(id, JSON.stringify(pending.map(item => item.source)), id, change),
    ]);
    row = await db.prepare("SELECT * FROM characters WHERE id = ?").bind(id).first();
    if (write.meta.changes) return { row, loot:{ gold:rewards.reduce((total, r) => total+r.gold, 0),
      items:rewards.flatMap(r => r.items).slice(0, 12) } };
    queued = null;
  }
  throw new Error("Character reward contention");
}

function useCharacterAction(state, name, argument, pose) {
  const { items, quests, recipes, npcs, jobs, starterWeapons, attributes } = rules();
  if (name === "equip_item" && state.bag[argument] && canWear(state, argument)) {
    const slot = items[argument].slot;
    state.equipment[slot] = state.equipment[slot] === argument ? null : argument;
  } else if (name === "attribute" && known(attributes, argument) &&
             Object.values(state.attributes).reduce((a,b) => a+b, 0) < 3*(state.level-1)) {
    state.attributes[argument]++;
    state.hp += attributes[argument].hp ?? 0;
    state.mp += attributes[argument].mp ?? 0;
  } else if (name === "skill_rank" && ["primary", "support"].includes(argument)) {
    const rank = state.skillRanks[argument] + 1;
    if (rank > (argument === "primary" ? 5 : 3) || argument === "support" && state.job === "beginner" ||
        state.level < rankLevel(argument, rank) || state.skillRanks.primary + state.skillRanks.support >= state.level)
      return false;
    state.skillRanks[argument] = rank;
  } else if (name === "potion" && ["hp", "mp"].includes(argument)) {
    const maximum = characterStats(state)[argument];
    const count = argument === "hp" ? "pots" : "tonics";
    if (state[count] < 1 || state[argument] >= maximum) return false;
    state[count]--;
    state[argument] = Math.min(maximum, state[argument] + (argument === "hp" ? 55 : 35));
  } else {
    const npc = npcs.find(npc => Math.abs(npc.x - pose.x) <= 65 && Math.abs(fieldGround(npc.x) - pose.y) <= 35);
    if (!npc) return false;
    if (name === "job" && npc.kind === "trainer" && known(jobs, argument) &&
        argument !== "beginner" && argument !== state.job && state.level >= 5) {
      state.job = argument;
      const starter = starterWeapons[argument];
      if (!state.bag[starter]) issueItem(state, starter);
      for (const [slot, id] of Object.entries(state.equipment))
        if (id && !canWear(state,id)) state.equipment[slot] = null;
      state.equipment.weapon = starter;
    } else if (name === "buy" && npc.kind === "shop" && npc.stock.includes(argument) && state.gold >= items[argument].price) {
      state.gold -= items[argument].price;
      issueItem(state, argument);
    } else if (name === "sell" && npc.kind === "shop" && known(items,argument) &&
               state.bag[argument] > (Object.values(state.equipment).includes(argument) ? 1 : 0)) {
      spendItem(state, argument, 1);
      state.gold += Math.floor(items[argument].price / 2);
    } else if (name === "craft" && npc.kind === "forge") {
      const recipe = recipes.find(recipe => recipe.item === argument);
      if (!recipe || state.gold < recipe.gold ||
          Object.entries(recipe.ingredients).some(([id, count]) => (state.bag[id] ?? 0) < count)) return false;
      for (const [id, count] of Object.entries(recipe.ingredients)) spendItem(state, id, count);
      state.gold -= recipe.gold;
      issueItem(state, argument);
    } else if (["accept_quest", "claim_quest"].includes(name) && Number.isInteger(argument) && quests[argument] &&
               questAtNPC(npc, argument)) {
      const quest = quests[argument], entry = state.quests[argument];
      if (name === "accept_quest") {
        if (entry.state !== 0) return false;
        entry.state = 1;
        state.trackedQuest = argument;
      } else {
        if (entry.state !== 1 || entry.count < quest.target) return false;
        entry.state = 2;
        if (state.trackedQuest === argument) state.trackedQuest = null;
        issueItem(state, quest.item);
        state.gold += quest.gold;
        gainExperience(state, quest.xp);
      }
    } else return false;
  }
  clampVitals(state);
  return true;
}

function questAtNPC(npc, index) {
  if (npc.kind === "quest") return index === (npc.quest ?? 0);
  return npc.kind === "harbor" && index === 1;
}
