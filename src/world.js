'use strict';

const $ = selector => document.querySelector(selector);
const canvas = $('canvas');
const g = canvas.getContext('2d');
canvas.width = 960;
canvas.height = 468;
const STEP_MS = 1000 / 60;
const attackAnimation = PIXEL_DATA.meta.hero.animations.attack;
const swingDuration = attackAnimation.durations.reduce((sum, duration) => sum + duration, 0);
const SAVE_KEY = 'maple-local-world-v1';
const START_X = 310;
const keys = {};
const clamp = (value, low, high) => Math.max(low, Math.min(high, value));

function areaAt(x) {
  return AREAS.find(area => x < area.end) ?? AREAS.at(-1);
}

function cameraTarget(x) {
  const area = areaAt(x);
  return clamp(x - canvas.width / 2, area.start, area.end - canvas.width);
}

const portals = AREAS.flatMap((area, index) => [
  ...(index ? [{x: area.start + 65, target: AREAS[index - 1].end - 155, label: AREAS[index - 1].name}] : []),
  ...(index < AREAS.length - 1 ? [{x: area.end - 65, target: AREAS[index + 1].start + 155, label: AREAS[index + 1].name}] : [])
]);

function nearbyPortal() {
  return portals.find(portal => Math.abs(portal.x - p.x) <= 45 && Math.abs(groundAt(portal.x) - p.y) <= 30);
}

function groundAt(x) {
  for (let i = 1; i < groundPoints.length; i++) {
    const [right, nextY] = groundPoints[i];
    if (x > right) continue;
    const [left, previousY] = groundPoints[i - 1];
    return previousY + (nextY - previousY) * (clamp(x, left, right) - left) / (right - left);
  }
  return groundPoints.at(-1)[1];
}

const ladders = ledges.map(ledge => {
  const x = ledge.ladderX;
  let bottom = groundAt(x);
  for (const lower of ledges) {
    if (lower.y > ledge.y && lower.y < bottom && x > lower.x + 8 && x < lower.x + lower.w - 8) {
      bottom = lower.y;
    }
  }
  return {x, top: ledge.y, bottom};
});

const p = {
  x: START_X, y: groundAt(START_X), vy: 0, dir: 1, grounded: true, surface: 'ground',
  hp: 100, mp: 35, level: 1, xp: 0, gold: 0, kills: 0, pots: 5, tonics: 1,
  job: 'beginner', bag: {twig: 1}, equipment: {weapon: 'twig', armor: null, charm: null},
  quests: QUESTS.map(() => ({state: 0, count: 0})),
  attributes: Object.fromEntries(Object.keys(ATTRIBUTES).map(id => [id, 0])),
  skillRanks: {primary: 1, support: 0}, hotbar: DEFAULT_HOTBAR.slice(),
  trackedQuest: null, bestiary: {}
};
let camera = 0;
let tick = 0;
let panel = null;
let paused = false;
let swing = null;
let climbing = null;
let invulnerableUntil = 0;
let hurtUntil = 0;
let skillCooldown = 0;
let supportCooldown = 0;
let supportUntil = 0;
let walkDistance = 0;
let walking = false;
let lastArea = null;
let sound = false;
let audio;
let drops = [];
let effects = [];
let monsters = [];

function stats() {
  const job = CLASSES[p.job];
  const result = {
    hp: 100 + (p.level - 1) * 10 + job.hp, mp: 35 + (p.level - 1) * 4 + job.mp,
    attack: 4 + (p.level - 1) * 2 + job.attack, defense: Math.floor((p.level - 1) / 2), speed: 4.2
  };
  for (const id of Object.values(p.equipment)) {
    if (!id) continue;
    const item = ITEMS[id];
    for (const key of Object.keys(result)) result[key] += item[key] ?? 0;
  }
  for (const [id, amount] of Object.entries(p.attributes)) {
    for (const key of Object.keys(result)) result[key] += (ATTRIBUTES[id][key] ?? 0) * amount;
  }
  return result;
}

function allocatedAP() {
  return Object.values(p.attributes).reduce((total, points) => total + points, 0);
}
function remainingAP() { return Math.max(0, (p.level - 1) * 3 - allocatedAP()); }
function remainingSP() { return Math.max(0, p.level - p.skillRanks.primary - p.skillRanks.support); }
function rankRequirement(id, rank) { return id === 'primary' ? rank * 2 - 1 : 5 + rank * 2; }

function primarySkill() {
  const job = CLASSES[p.job];
  return {...job, power: job.power + (p.skillRanks.primary - 1) * 0.25};
}
function supportValue(stat) {
  const support = SUPPORTS[p.job];
  if (supportUntil <= tick || support?.stat !== stat) return 0;
  return support.power * (1 + (p.skillRanks.support - 1) * 0.35);
}
function useSupport() {
  if (!pixelReady || paused || panel || hurtUntil > tick || !p.skillRanks.support || supportCooldown > 0) return;
  const support = SUPPORTS[p.job];
  if (p.mp < support.cost) { toast('마력이 부족해요.'); return; }
  p.mp -= support.cost;
  supportUntil = tick + 420 + (p.skillRanks.support - 1) * 90;
  supportCooldown = 720;
  textEffect(support.name, p.x, p.y - 64, '#bcf8cf');
  beep(690);
  updateHUD();
}

function canEquip(id) {
  const item = ITEMS[id];
  return !!item?.slot && p.level >= item.level && (!item.job || item.job === p.job);
}

function loadGame() {
  let saved;
  try { saved = JSON.parse(localStorage.getItem(SAVE_KEY)); } catch { return; }
  if (!saved || !Number.isFinite(saved.level)) return;
  for (const key of ['x', 'level', 'xp', 'gold', 'kills', 'pots', 'tonics', 'hp', 'mp']) {
    if (Number.isFinite(saved[key])) p[key] = Math.max(0, Math.trunc(saved[key]));
  }
  p.x = clamp(p.x, 24, WORLD_WIDTH - 24);
  p.y = groundAt(p.x);
  p.level = Math.max(1, p.level);
  if (Object.hasOwn(CLASSES, saved.job)) p.job = saved.job;
  if (saved.bag && typeof saved.bag === 'object') {
    p.bag = {};
    p.equipment.weapon = null;
  }
  for (const id of Object.keys(ITEMS)) {
    if (id === 'potion' || id === 'tonic') continue;
    const amount = saved.bag?.[id];
    if (Number.isSafeInteger(amount) && amount > 0) p.bag[id] = amount;
  }
  for (const slot of Object.keys(SLOTS)) {
    const id = saved.equipment?.[slot];
    if (id === null || (ITEMS[id]?.slot === slot && p.bag[id] > 0 && canEquip(id))) p.equipment[slot] = id;
  }
  if (Array.isArray(saved.quests)) {
    for (const [i, quest] of QUESTS.entries()) {
      const entry = saved.quests[i];
      if (entry && [0, 1, 2].includes(entry.state) && Number.isFinite(entry.count)) {
        p.quests[i] = {state: entry.state, count: clamp(Math.trunc(entry.count), 0, quest.target)};
      }
    }
  } else if (saved.quest > 0) {
    p.quests[0] = {state: saved.quest >= 2 ? 2 : 1, count: Math.min(QUESTS[0].target, p.kills)};
    if (saved.quest >= 4) p.quests[1] = {state: 2, count: 1};
  }
  p.attributes = Object.fromEntries(Object.keys(ATTRIBUTES).map(id => [id, 0]));
  let ap = (p.level - 1) * 3;
  for (const id of Object.keys(ATTRIBUTES)) {
    const value = saved.attributes?.[id];
    if (!Number.isSafeInteger(value) || value < 0) continue;
    p.attributes[id] = Math.min(value, ap);
    ap -= p.attributes[id];
  }
  const primaryRank = saved.skillRanks?.primary;
  p.skillRanks.primary = Number.isSafeInteger(primaryRank) ? clamp(primaryRank, 1, Math.min(5, Math.ceil(p.level / 2))) : 1;
  const supportRank = saved.skillRanks?.support;
  p.skillRanks.support = SUPPORTS[p.job] && Number.isSafeInteger(supportRank)
    ? clamp(supportRank, 0, Math.min(3, Math.max(0, Math.floor((p.level - 5) / 2)), p.level - p.skillRanks.primary)) : 0;
  p.hotbar = DEFAULT_HOTBAR.map((fallback, i) => {
    const action = saved.hotbar?.[i];
    return action === null || Object.hasOwn(HOTBAR_ACTIONS, action) ? action : fallback;
  });
  p.bestiary = {};
  for (const [index] of SPECIES.entries()) {
    const count = saved.bestiary?.[index];
    if (Number.isSafeInteger(count) && count > 0) p.bestiary[index] = count;
  }
  p.trackedQuest = Number.isInteger(saved.trackedQuest) && p.quests[saved.trackedQuest]?.state === 1 ? saved.trackedQuest : null;
  const limits = stats();
  p.hp = clamp(p.hp, 1, limits.hp);
  p.mp = clamp(p.mp, 0, limits.mp);
}

function save() {
  try { localStorage.setItem(SAVE_KEY, JSON.stringify(p)); return true; } catch { return false; }
}

function toast(message) {
  const element = $('#toast');
  element.textContent = message;
  element.style.opacity = 1;
  clearTimeout(toast.timer);
  toast.timer = setTimeout(() => { element.style.opacity = 0; }, 3500);
}

function beep(frequency) {
  if (!sound) return;
  try {
    audio ??= new AudioContext();
    const oscillator = audio.createOscillator();
    const volume = audio.createGain();
    oscillator.type = 'triangle';
    oscillator.frequency.value = frequency;
    volume.gain.setValueAtTime(0.035, audio.currentTime);
    volume.gain.exponentialRampToValueAtTime(0.001, audio.currentTime + 0.16);
    oscillator.connect(volume).connect(audio.destination);
    oscillator.start();
    oscillator.stop(audio.currentTime + 0.16);
  } catch {}
}

const xpNeeded = () => 45 + (p.level - 1) * 28;

function updateHUD() {
  const limits = stats();
  const job = CLASSES[p.job];
  $('#lv').textContent = 'Lv. ' + p.level;
  $('#job').textContent = job.name;
  $('#hp').textContent = p.hp + ' / ' + limits.hp;
  $('#hpbar').style.width = p.hp / limits.hp * 100 + '%';
  $('#mp').textContent = p.mp + ' / ' + limits.mp;
  $('#mpbar').style.width = p.mp / limits.mp * 100 + '%';
  $('#xp').textContent = p.xp + ' / ' + xpNeeded();
  $('#xpbar').style.width = Math.min(100, p.xp / xpNeeded() * 100) + '%';
  $('#gold').textContent = p.gold + ' 메소';
  $('#point-badge').textContent = remainingAP() || '';
  $('#skill-point-badge').textContent = remainingSP() || '';
  $('#xp-percent').textContent = Math.floor(p.xp / xpNeeded() * 100) + '%';
  const questIndex = p.trackedQuest ?? p.quests.findIndex(quest => quest.state === 1);
  const active = QUESTS[questIndex];
  $('#quest').textContent = active
    ? (p.quests[questIndex].count >= active.target ? active.who + '에게 보고' :
      active.name + ' · ' + p.quests[questIndex].count + ' / ' + active.target)
    : p.quests[0].state === 0 ? '마을의 리나와 대화' : p.job === 'beginner'
      ? 'Lv. 5에 다온에게 전직' : p.quests[1].state === 0 ? '항구의 등대지기와 대화' : '모험 계속하기';
  updateHotbar();
}

function gainXP(amount) {
  p.xp += amount;
  const previous = p.level;
  while (p.xp >= xpNeeded()) {
    p.xp -= xpNeeded();
    p.level++;
  }
  if (p.level !== previous) {
    const limits = stats();
    p.hp = limits.hp;
    p.mp = limits.mp;
    textEffect('LEVEL UP!', p.x, p.y - 76, '#ffe69e');
    toast(previous < 5 && p.level >= 5 ? 'Lv. 5 달성! 다온에게 전직할 수 있어요.' : '레벨 ' + p.level + ' 달성 · C 능력치 · S 스킬');
    beep(840);
  }
}

function addItem(id) {
  if (id === 'potion') p.pots++;
  else if (id === 'tonic') p.tonics++;
  else p.bag[id] = (p.bag[id] ?? 0) + 1;
}

function spawn(x, kind, index, ledge = null) {
  const species = SPECIES[kind];
  const stride = species.elite ? 134 : 86;
  monsters.push({
    x, home: x, y: ledge?.y ?? groundAt(x), kind, ledge, species,
    left: ledge ? ledge.x + 16 : Math.max(areaAt(x).start + 24, x - stride),
    right: ledge ? ledge.x + ledge.w - 16 : Math.min(areaAt(x).end - 24, x + stride),
    dir: index % 2 ? 1 : -1, hp: species.hp, deathAt: null, hitUntil: 0,
    nextStrike: 0, strikeAt: 0, phase: index * 31, state: 'patrol'
  });
}

function populate() {
  const kindFor = (x, index) => {
    if (x < 3780) return 0;
    if (x < 6100) return 1;
    if (x < 9100) return 2;
    if (x < 12000) return index % 2 ? 3 : 5;
    if (x < 13040) return index % 2 ? 5 : 6;
    if (x < 14900) return index % 3 ? 6 : 7;
    return index % 2 ? 8 : 9;
  };
  for (let index = 0, x = 2580; x < 18070; x += 213, index++) {
    if (x >= 9290 && x <= 10810 || x > 11520 && x < 12500 ||
      x > 14900 && x < 15500) continue;
    spawn(x, kindFor(x, index), index);
  }
  for (const [index, ledge] of ledges.entries()) {
    if (ledge.x >= 2450 && index % 3 !== 0 && (ledge.x < 9100 || ledge.x > 10900)) {
      spawn(ledge.x + Math.round(ledge.w * 0.6), kindFor(ledge.x, index), index, ledge);
    }
  }
  spawn(11780, 4, 1);
  spawn(18120, 10, 1);
}

function textEffect(text, x, y, color = '#ffe381') {
  effects.push({shape: 'text', text, x, y, color, duration: 44, start: tick});
}

function reward(monster) {
  monster.deathAt = tick;
  monster.strikeAt = 0;
  p.kills++;
  p.bestiary[monster.kind] = (p.bestiary[monster.kind] ?? 0) + 1;
  gainXP(monster.species.xp);
  for (const [index, quest] of QUESTS.entries()) {
    const entry = p.quests[index];
    if (entry.state === 1 && quest.matches.includes(monster.kind)) {
      entry.count = Math.min(quest.target, entry.count + 1);
      if (entry.count === quest.target) toast(quest.who + '에게 의뢰를 보고하세요.');
    }
  }
  drops.push({
    x: monster.x, y: monster.y, gold: monster.species.gold, item: monster.species.loot, start: tick,
    rare: monster.species.elite || Math.random() < 0.16 ? monster.species.rare : null,
    bonus: Math.random() < 0.18 ? (monster.kind % 2 ? 'tonic' : 'potion') : null, until: tick + 1000
  });
  updateHUD();
}

function pickupDrops() {
  drops = drops.filter(drop => {
    if (tick >= drop.until) return false;
    if (Math.abs(drop.x - p.x) > 34 || Math.abs(drop.y - p.y) > 30) return true;
    p.gold += drop.gold;
    addItem(drop.item);
    if (drop.rare) addItem(drop.rare);
    if (drop.bonus) addItem(drop.bonus);
    reportLoot([drop.item, drop.rare, drop.bonus].filter(Boolean), drop.gold);
    effects.push({shape: 'pickup', icon: itemIcon(drop.rare ?? drop.item), x: drop.x, y: drop.y - 7,
      endX: p.x, endY: p.y - 35, duration: 19, start: tick});
    textEffect('+' + drop.gold + ' 메소', p.x, p.y - 54);
    updateHUD();
    return false;
  });
}

function attack(skill = false) {
  if (!pixelReady || paused || panel || swing || climbing || hurtUntil > tick) return;
  const job = primarySkill();
  if (skill) {
    if (skillCooldown) return;
    if (p.mp < job.cost) {
      if (tick - (attack.lastManaNotice ?? -60) >= 60) {
        attack.lastManaNotice = tick;
        toast('마력이 부족해요.');
      }
      return;
    }
    p.mp -= job.cost;
    skillCooldown = job.cooldown;
    updateHUD();
  }
  swing = {start: tick, direction: p.dir, skill, hit: false};
  beep(skill ? 420 : 370);
}

function damage(monster, amount, direction) {
  monster.hp -= amount;
  monster.hitUntil = tick + 10;
  monster.hitDirection = direction;
  if (!monster.species.elite) {
    monster.strikeAt = 0;
    monster.nextStrike = Math.max(monster.nextStrike, tick + 13);
  }
  if (monster.species.aggro && monster.state !== 'return') monster.state = 'pursuit';
  monster.x = clamp(monster.x + direction * 8, monster.left, monster.right);
  if (!monster.ledge) monster.y = groundAt(monster.x);
  textEffect(String(amount), monster.x, monster.y - 46);
  if (monster.hp <= 0) reward(monster);
}

function advanceAttack() {
  if (!swing) return;
  const elapsed = (tick - swing.start) * STEP_MS;
  if (elapsed >= swingDuration) { swing = null; return; }
  if (swing.hit || elapsed < attackAnimation.durations[0]) return;
  swing.hit = true;
  const {skill, direction} = swing;
  const job = primarySkill();
  const power = Math.round(stats().attack + supportValue('attack'));
  beep(skill ? 760 : 510);
  if (skill && job.shape === 'arrow') {
    effects.push({
      shape: 'arrow', x: p.x + 15 * direction, y: p.y - 20, direction,
      duration: Math.ceil(job.reach / 15), start: tick, power: Math.ceil(power * job.power)
    });
    return;
  }
  for (const monster of monsters) {
    if (monster.deathAt !== null || areaAt(monster.x) !== areaAt(p.x)) continue;
    const dx = monster.x - p.x;
    const dy = Math.abs(monster.y - p.y);
    const forward = dx * direction >= -8;
    const inRange = !skill ? forward && Math.abs(dx) <= 54 && dy <= 31 :
      Math.abs(dx) <= job.reach && dy <= (job.shape === 'stars' ? 92 : 53) &&
      (job.shape !== 'arc' || forward);
    if (inRange) damage(monster, skill ? Math.ceil(power * job.power) : power + Math.floor(Math.random() * 3),
      Math.sign(dx) || direction);
  }
  if (skill) effects.push({shape: job.shape, x: p.x, y: p.y - 21, direction, duration: 25, start: tick});
}

function advanceEffects() {
  effects = effects.filter(effect => tick - effect.start < effect.duration && !effect.expired);
  for (const effect of effects.slice()) {
    if (effect.shape !== 'arrow') continue;
    const nextX = effect.x + effect.direction * 15;
    const hit = monsters.find(monster => monster.deathAt === null &&
      Math.abs(nextX - monster.x) <= 18 && Math.abs(effect.y - (monster.y - 18)) <= 22);
    if (hit) {
      damage(hit, effect.power, effect.direction);
      effect.expired = true;
    } else {
      effect.x = nextX;
    }
  }
}

function moveMonsterToward(monster, destination, speed) {
  const difference = destination - monster.x;
  if (difference) monster.dir = Math.sign(difference);
  monster.x = clamp(monster.x + clamp(difference, -speed, speed), monster.left, monster.right);
  if (!monster.ledge) monster.y = groundAt(monster.x);
}

function receiveHit(monster, power) {
  if (tick < invulnerableUntil) return;
  const lost = Math.max(1, power - Math.floor(stats().defense + supportValue('defense')));
  p.hp = Math.max(0, p.hp - lost);
  invulnerableUntil = tick + 55;
  hurtUntil = tick + 10;
  climbing = swing = null;
  p.grounded = false;
  p.vy = -3.4;
  textEffect('-' + lost, p.x, p.y - 52, '#ffad9e');
  beep(monster.species.elite ? 108 : 150);
  if (!p.hp) {
    travelTo(START_X);
    p.hp = stats().hp;
    p.mp = stats().mp;
    toast('솔방울 마을에서 회복했어요.');
  }
  updateHUD();
}

function moveMonsters() {
  for (const monster of monsters) {
    const {species} = monster;
    if (monster.deathAt !== null) {
      if (tick - monster.deathAt >= (species.elite ? 900 : 340)) {
        monster.hp = species.hp;
        monster.x = monster.home;
        monster.y = monster.ledge?.y ?? groundAt(monster.x);
        monster.deathAt = null;
        monster.state = 'patrol';
        monster.strikeAt = 0;
        monster.nextStrike = tick + 40;
      }
      continue;
    }
    if (areaAt(monster.home) !== areaAt(p.x)) {
      if (monster.state !== 'patrol' || monster.strikeAt) {
        monster.x = monster.home;
        monster.y = monster.ledge?.y ?? groundAt(monster.x);
        monster.state = 'patrol';
        monster.strikeAt = 0;
      }
      continue;
    }
    const sameHeight = Math.abs(monster.y - p.y) < 37;
    const distance = Math.abs(monster.x - p.x);
    const enraged = species.elite && monster.hp <= species.hp * 0.5;
    const reach = species.elite ? (enraged ? 90 : 60) : 25;
    if (monster.strikeAt) {
      if (tick < monster.strikeAt) continue;
      monster.strikeAt = 0;
      monster.lastStrike = tick;
      monster.nextStrike = tick + (enraged ? 46 : 64);
      const attackRange = monster.attackRange ?? reach;
      if (species.elite) effects.push({
        shape: 'boss-wave', x: monster.x + monster.dir * attackRange / 2, y: monster.y - 10,
        size: attackRange / 2 + 6, duration: 20, start: tick
      });
      const offset = (p.x - monster.x) * monster.dir;
      if (sameHeight && offset >= -12 && offset <= attackRange) {
        receiveHit(monster, Math.ceil(species.attack * (enraged ? 1.2 : 1)));
      }
      continue;
    }
    if (monster.hitUntil > tick) continue;
    const nearHome = Math.abs(p.x - monster.home) <= (species.aggro ?? 55) + 70;
    if (monster.state === 'pursuit' && (!nearHome || !sameHeight || distance > (species.aggro ?? 45) + 80)) {
      monster.state = 'return';
    }
    if (monster.state === 'patrol' && species.aggro && sameHeight && nearHome && distance <= species.aggro) {
      monster.state = 'pursuit';
    }
    if (monster.state !== 'return' && sameHeight && distance <= reach && tick >= monster.nextStrike) {
      monster.dir = Math.sign(p.x - monster.x) || monster.dir;
      monster.attackRange = reach;
      monster.strikeAt = tick + (species.elite ? (enraged ? 24 : 34) : 17);
      continue;
    }
    if (monster.state === 'return') {
      moveMonsterToward(monster, monster.home, species.speed * 1.6);
      if (monster.x === monster.home) monster.state = 'patrol';
    } else if (monster.state === 'pursuit') {
      if (distance > reach - 2) moveMonsterToward(monster, p.x, species.speed * (enraged ? 2.35 : 1.9));
    } else {
      const target = monster.dir > 0 ? monster.right : monster.left;
      moveMonsterToward(monster, target, species.speed);
      if (monster.x === target) monster.dir *= -1;
    }
  }
}

function travelTo(x) {
  if (areaAt(p.x) !== areaAt(x)) effects = [];
  p.x = clamp(x, 24, WORLD_WIDTH - 24);
  p.y = groundAt(p.x);
  p.vy = 0;
  p.grounded = true;
  p.surface = 'ground';
  climbing = swing = null;
  walkDistance = 0;
  walking = false;
  camera = cameraTarget(p.x);
}

function jump() {
  if (paused || panel || (!p.grounded && !climbing)) return;
  if (keys.ArrowDown && typeof p.surface === 'object' && p.surface !== null) {
    p.y += 2;
    p.vy = 1;
  } else {
    p.vy = -11.2;
    beep(300);
  }
  p.grounded = false;
  p.surface = climbing = null;
}

function movePlayer(dx) {
  const vertical = Number(!!keys.ArrowDown) - Number(!!keys.ArrowUp);
  if (dx) climbing = null;
  if (!climbing && !dx && !swing && vertical && p.vy >= 0) {
    climbing = ladders.find(ladder => Math.abs(p.x - ladder.x) <= 11 &&
      (vertical < 0 ? p.y > ladder.top && p.y <= ladder.bottom + 2 :
        p.y >= ladder.top - 1 && p.y < ladder.bottom - 1)) ?? null;
  }
  if (climbing) {
    p.x = climbing.x;
    p.y = clamp(p.y + vertical * 3.2, climbing.top, climbing.bottom);
    p.vy = 0;
    p.grounded = p.y === climbing.top || p.y === climbing.bottom;
    p.surface = null;
    if (p.grounded) climbing = null;
    return;
  }

  const area = areaAt(p.x);
  const speed = stats().speed + supportValue('speed');
  p.x = clamp(p.x + dx * speed * (swing && p.grounded ? 2.4 / 4.2 : 1), area.start + 24, area.end - 24);
  const floor = groundAt(p.x);
  if (p.grounded && p.surface === 'ground') { p.y = floor; return; }
  const oldY = p.y;
  p.vy += 0.5;
  p.y += p.vy;
  p.grounded = false;
  p.surface = null;
  if (p.vy < 0) return;
  let landing = p.y >= floor ? floor : Infinity;
  let surface = 'ground';
  for (const ledge of ledges) {
    if (ledge.y < landing && oldY <= ledge.y && p.y >= ledge.y &&
        p.x >= ledge.x - 3 && p.x <= ledge.x + ledge.w + 3) {
      landing = ledge.y;
      surface = ledge;
    }
  }
  if (Number.isFinite(landing)) {
    p.y = landing;
    p.vy = 0;
    p.grounded = true;
    p.surface = surface;
  }
}

function step() {
  if (!pixelReady || paused || panel) return;
  tick++;
  if (skillCooldown) skillCooldown--;
  if (supportCooldown) supportCooldown--;
  const dx = Number(!!keys.ArrowRight) - Number(!!keys.ArrowLeft);
  if (dx && !swing) p.dir = dx;
  if (keys.KeyX) attack(true);
  if (keys.KeyZ) attack();
  const {x, y} = p;
  movePlayer(dx);
  walking = p.grounded && p.x !== x;
  if (walking || climbing) walkDistance += Math.abs(p.x - x) + Math.abs(p.y - y);
  else walkDistance = 0;
  advanceAttack();
  advanceEffects();
  moveMonsters();
  pickupDrops();

  const area = areaAt(p.x);
  if (area !== lastArea) {
    if (lastArea) toast(area.name);
    lastArea = area;
    $('#region').textContent = area.name;
  }
  if (tick % 90 === 0 && p.mp < stats().mp) { p.mp++; updateHUD(); }
  if (tick % 6 === 0) updateCombatHUD();
  if (tick % 600 === 0) save();
  const target = cameraTarget(p.x);
  camera += (target - camera) * 0.18;
  if (Math.abs(target - camera) < 0.1) camera = target;
}

function nearbyNPC() {
  return NPCS.find(npc => Math.abs(npc.x - p.x) <= 63 && Math.abs(groundAt(npc.x) - p.y) <= 30);
}
