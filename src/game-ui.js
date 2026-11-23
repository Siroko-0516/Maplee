'use strict';

const panelElement = $('#panel');
let panelTab = 'buy';
let bagTab = 'gear';
let journalTab = 'active';
let lastMinimapArea;
const MAPLEE_SITE = 'https://maplee-pixel-world.jisung-20090725.chatgpt.site';
const onMapleeSite = typeof location !== 'undefined' && location.origin === MAPLEE_SITE;
const atlasStyle = document.documentElement.style;
atlasStyle.setProperty('--item-art', 'url("' + PIXEL_DATA.icons + '")');
atlasStyle.setProperty('--frame-art', 'url("' + PIXEL_DATA.frame + '")');

function applyIcon(element, icon) {
  element.classList.add('pixel-icon');
  element.style.backgroundPosition = ((icon % 4) * 100 / 3) + '% ' + (Math.floor(icon / 4) * 100 / 3) + '%';
}
function makeIcon(icon, className = '') {
  const element = document.createElement('span');
  element.className = className;
  element.setAttribute('aria-hidden', 'true');
  applyIcon(element, icon);
  return element;
}
const rarityLabels = {uncommon: '고급', rare: '희귀', epic: '영웅'};
let lootTimer;

function reportLoot(ids, gold) {
  const feed = $('#loot-feed');
  const line = document.createElement('div');
  line.className = 'loot-line';
  if (gold) {
    line.append(makeIcon(7));
    addText('b', '+' + gold + ' 메소', line);
  }
  for (const id of ids) {
    line.append(makeIcon(itemIcon(id)));
    const text = addText('span', ITEMS[id].name, line);
    if (ITEMS[id].rarity) text.dataset.rarity = ITEMS[id].rarity;
  }
  feed.replaceChildren(line);
  feed.hidden = false;
  clearTimeout(lootTimer);
  lootTimer = setTimeout(() => { feed.hidden = true; }, 3900);
}

function makeTabs(options, active, change) {
  const tabs = document.createElement('nav');
  tabs.className = 'panel-tabs';
  for (const [id, label] of options) {
    const button = shownButton(label, () => { change(id); renderPanel(); });
    button.setAttribute('aria-pressed', String(active === id));
    tabs.append(button);
  }
  panelElement.append(tabs);
}

const menuPanels = [
  ['character', '능력치', 'C'], ['skills', '스킬', 'S'], ['inventory', '장비·가방', 'I'],
  ['journal', '퀘스트', 'Q'], ['map', '지도', 'M'], ['bestiary', '도감', 'B'], ['account', '계정', null]
];

function runSlot(index) {
  const action = p.hotbar[index];
  if (!action || paused || panel) return;
  if (action === 'hp') healWith('potion');
  if (action === 'mp') healWith('tonic');
  if (action === 'skill') attack(true);
  if (action === 'support') useSupport();
  if (action === 'home') home();
}

function updateHotbar() {
  for (let i = 0; i < HOTKEYS.length; i++) {
    const action = p.hotbar[i];
    const entry = HOTBAR_ACTIONS[action];
    const name = action === 'skill' ? CLASSES[p.job].skill : action === 'support' ?
      (SUPPORTS[p.job]?.name ?? '보조 스킬') : entry?.name;
    const button = $('#slot-' + i);
    button.dataset.color = entry?.color ?? 'empty';
    button.title = name ?? '빈 슬롯';
    button.setAttribute('aria-label', (i + 1) + '번 · ' + (name ?? '빈 슬롯'));
    const icon = $('#slot-symbol-' + i);
    const icons = {hp: 4, mp: 5, skill: p.job === 'ranger' ? 1 : p.job === 'mage' ? 2 : 0, support: 13, home: 6};
    icon.classList.remove('pixel-icon');
    icon.textContent = entry ? '' : '–';
    if (entry) applyIcon(icon, icons[action]);
  }
  updateCombatHUD();
}

function updateCombatHUD() {
  for (let i = 0; i < HOTKEYS.length; i++) {
    const action = p.hotbar[i];
    const badge = action === 'hp' ? String(p.pots) : action === 'mp' ? String(p.tonics) :
      action === 'skill' && skillCooldown ? Math.ceil(skillCooldown / 60) + '초' :
      action === 'support' ? (!p.skillRanks.support ? '잠김' : supportCooldown ? Math.ceil(supportCooldown / 60) + '초' : '') : '';
    $('#slot-count-' + i).textContent = badge;
    const unavailable = !action || action === 'hp' && !p.pots || action === 'mp' && !p.tonics ||
      action === 'skill' && (skillCooldown > 0 || p.mp < CLASSES[p.job].cost) ||
      action === 'support' && (!p.skillRanks.support || supportCooldown > 0 || p.mp < SUPPORTS[p.job].cost);
    $('#slot-' + i).dataset.unavailable = String(unavailable);
  }
  const support = supportUntil > tick ? SUPPORTS[p.job] : null;
  $('#buff-status').textContent = support ? support.name + ' · ' + Math.ceil((supportUntil - tick) / 60) + '초' : '';
  updateMinimap();
}

function updateMinimap() {
  const area = areaAt(p.x);
  const width = 200;
  const scale = x => 6 + (x - area.start) * (width - 12) / (area.end - area.start);
  if (area !== lastMinimapArea) {
    lastMinimapArea = area;
    const mini = $('#minimap').getContext('2d');
    mini.clearRect(0, 0, width, 46);
    mini.fillStyle = '#25444b';
    mini.strokeStyle = '#8cbdb2';
    mini.lineWidth = 1.5;
    mini.beginPath();
    mini.moveTo(6, 39);
    mini.lineTo(6, groundAt(area.start) / 20 + 13);
    for (const [x, y] of groundPoints) {
      if (x > area.start && x < area.end) mini.lineTo(scale(x), y / 20 + 13);
    }
    mini.lineTo(width - 6, groundAt(area.end) / 20 + 13);
    mini.lineTo(width - 6, 39);
    mini.closePath();
    mini.fill();
    mini.stroke();
    mini.fillStyle = '#7da7a2';
    for (const ledge of ledges) {
      if (ledge.x < area.start || ledge.x >= area.end) continue;
      mini.fillRect(scale(ledge.x), ledge.y / 20 + 10, Math.max(3, scale(ledge.x + ledge.w) - scale(ledge.x)), 1.5);
    }
    for (const portal of portals) {
      if (portal.x < area.start || portal.x >= area.end) continue;
      mini.fillStyle = '#8be6fa';
      mini.fillRect(scale(portal.x) - 2, 27, 4, 7);
    }
    for (const npc of NPCS) {
      if (npc.x < area.start || npc.x >= area.end) continue;
      mini.fillStyle = '#f2bb78';
      mini.fillRect(scale(npc.x) - 1, groundAt(npc.x) / 20 + 9, 3, 3);
    }
  }
  $('#minimap-player').style.left = scale(p.x) / width * 100 + '%';
  $('#minimap-player').style.top = (p.y / 20 + 9) / 46 * 100 + '%';
}

function shownButton(text, onClick, disabled = false) {
  const button = document.createElement('button');
  button.textContent = text;
  button.disabled = disabled;
  button.onclick = onClick;
  button.type = 'button';
  return button;
}
function addText(tag, text, target = panelElement) {
  const element = document.createElement(tag);
  element.textContent = text;
  target.append(element);
  return element;
}
function closePanel() {
  panel = null;
  panelElement.hidden = true;
  for (const code of Object.keys(keys)) keys[code] = false;
}
function openPanel(kind, data = null) {
  if (panel?.kind === kind && !data) { closePanel(); return; }
  panel = {kind, data};
  paused = false;
  $('#pause').textContent = '일시정지';
  for (const code of Object.keys(keys)) keys[code] = false;
  renderPanel();
}
function itemDetails(item) {
  const parts = [];
  if (item.rarity) parts.push(rarityLabels[item.rarity]);
  if (item.slot) parts.push(SLOTS[item.slot], 'Lv. ' + item.level);
  if (item.job) parts.push(CLASSES[item.job].name);
  for (const [key, label] of Object.entries({attack: '공격', defense: '방어', hp: '최대 HP', mp: '최대 MP'})) {
    if (item[key]) parts.push(label + ' +' + item[key]);
  }
  return parts.join(' · ');
}
function panelRow(title, details, action, handler, blocked = false, itemId = null) {
  const row = document.createElement('div');
  row.className = 'panel-row';
  if (itemId) row.append(makeIcon(itemIcon(itemId), 'row-icon'));
  const label = document.createElement('div');
  label.className = 'row-label';
  const itemTitle = addText('b', title, label);
  if (itemId && ITEMS[itemId].rarity) itemTitle.dataset.rarity = ITEMS[itemId].rarity;
  if (details) addText('small', details, label);
  row.append(label);
  if (action) row.append(shownButton(action, handler, blocked));
  panelElement.append(row);
}
function updateAfterChange() {
  updateHUD();
  save();
  if (panel) renderPanel();
}
function healWith(kind) {
  const statsNow = stats();
  const mana = kind === 'tonic';
  const key = mana ? 'mp' : 'hp';
  const supply = mana ? 'tonics' : 'pots';
  if (!p[supply]) { toast('물약이 없어요. 상점에서 살 수 있어요.'); return; }
  if (p[key] === statsNow[key]) { toast(key.toUpperCase() + '가 가득 차 있어요.'); return; }
  p[supply]--;
  p[key] = Math.min(statsNow[key], p[key] + (mana ? 35 : 55));
  beep(620);
  updateAfterChange();
}
function toggleEquipment(id) {
  if (!p.bag[id] || !canEquip(id)) return;
  const slot = ITEMS[id].slot;
  p.equipment[slot] = p.equipment[slot] === id ? null : id;
  const limits = stats();
  p.hp = Math.min(p.hp, limits.hp);
  p.mp = Math.min(p.mp, limits.mp);
  updateAfterChange();
}
function renderInventory() {
  makeTabs([['gear', '장비'], ['supply', '소비'], ['loot', '전리품']], bagTab, id => { bagTab = id; });
  if (bagTab === 'gear') {
    const equipped = document.createElement('div');
    equipped.className = 'equipment-grid';
    for (const [slot, label] of Object.entries(SLOTS)) {
      const id = p.equipment[slot];
      const card = document.createElement('div');
      addText('small', label, card);
      card.append(makeIcon(id ? itemIcon(id) : 6, id ? 'equip-icon' : 'equip-icon empty-icon'));
      addText('b', id ? ITEMS[id].name : '비어 있음', card);
      equipped.append(card);
    }
    panelElement.append(equipped);
  } else if (bagTab === 'supply') {
    panelRow('체력 물약 × ' + p.pots, 'HP 55 회복', '사용', () => healWith('potion'), !p.pots, 'potion');
    panelRow('마력 물약 × ' + p.tonics, 'MP 35 회복', '사용', () => healWith('tonic'), !p.tonics, 'tonic');
    return;
  }
  const items = Object.entries(p.bag).filter(([id]) => bagTab === 'gear' ? ITEMS[id].slot : !ITEMS[id].slot);
  if (!items.length) addText('p', bagTab === 'gear' ? '가방에 장비가 없어요.' : '몬스터를 잡으면 전리품을 얻을 수 있어요.');
  for (const [id, amount] of items) {
    const item = ITEMS[id];
    const equipped = item.slot && p.equipment[item.slot] === id;
    const details = item.slot ? itemDetails(item) : '상점 판매가 ' + Math.floor(item.price / 2) + ' 메소';
    panelRow(item.name + ' × ' + amount, details, item.slot ? (equipped ? '해제' : '장착') : null,
      () => toggleEquipment(id), !canEquip(id), id);
  }
}

function allocateAttribute(id) {
  if (!Object.hasOwn(ATTRIBUTES, id) || !remainingAP()) return;
  p.attributes[id]++;
  p.hp += ATTRIBUTES[id].hp ?? 0;
  p.mp += ATTRIBUTES[id].mp ?? 0;
  updateAfterChange();
}
function renderCharacter() {
  const current = stats();
  addText('p', 'Lv. ' + p.level + ' ' + CLASSES[p.job].name + ' · 남은 AP ' + remainingAP() + ' · 처치 ' + p.kills);
  const summary = document.createElement('div');
  summary.className = 'equipment-grid';
  for (const [label, value] of [['공격력', current.attack], ['방어력', current.defense], ['최대 HP / MP', current.hp + ' / ' + current.mp]]) {
    const card = document.createElement('div');
    addText('small', label, card);
    addText('b', String(value), card);
    summary.append(card);
  }
  panelElement.append(summary);
  for (const [id, attr] of Object.entries(ATTRIBUTES)) {
    panelRow(attr.icon + '  ' + attr.name + ' · ' + p.attributes[id], attr.detail, '+1', () => allocateAttribute(id), !remainingAP());
  }
}
function upgradeSkill(id) {
  if (id !== 'primary' && id !== 'support') return;
  const maximum = id === 'primary' ? 5 : 3;
  if (!remainingSP() || p.skillRanks[id] >= maximum || p.level < rankRequirement(id, p.skillRanks[id] + 1)) return;
  if (id === 'support' && !SUPPORTS[p.job]) return;
  p.skillRanks[id]++;
  updateAfterChange();
}
function renderSkills() {
  const skill = primarySkill();
  const support = SUPPORTS[p.job];
  const rank = p.skillRanks.primary;
  addText('p', '남은 SP ' + remainingSP() + ' · 레벨업마다 1 SP');
  panelRow(skill.skill + ' · 랭크 ' + rank + '/5', 'X · MP ' + skill.cost + ' · 공격력의 ' + Math.round(skill.power * 100) + '%',
    rank === 5 ? '최대' : p.level < rankRequirement('primary', rank + 1) ? 'Lv. ' + rankRequirement('primary', rank + 1) : '강화',
    () => upgradeSkill('primary'), rank >= 5 || !remainingSP() || p.level < rankRequirement('primary', rank + 1));
  if (support) {
    const level = p.skillRanks.support;
    panelRow(support.name + ' · 랭크 ' + level + '/3', 'V · MP ' + support.cost + ' · ' + support.summary,
      level === 3 ? '최대' : p.level < rankRequirement('support', level + 1) ? 'Lv. ' + rankRequirement('support', level + 1) :
        level === 0 ? '배우기' : '강화', () => upgradeSkill('support'),
      level >= 3 || !remainingSP() || p.level < rankRequirement('support', level + 1));
  } else {
    addText('p', '전직 후 Lv. 7부터 보조 스킬을 배울 수 있어요. 주력 스킬 랭크는 전직할 때 이어집니다.');
  }
}
function renderJournal() {
  makeTabs([['active', '진행 중'], ['available', '받을 수 있음'], ['done', '완료']], journalTab, id => { journalTab = id; });
  const filter = {active: 1, available: 0, done: 2}[journalTab];
  const quests = QUESTS.map((quest, index) => [quest, p.quests[index], index]).filter(([, state]) => state.state === filter);
  if (!quests.length) addText('p', '이 목록에 표시할 퀘스트가 없어요.');
  const tracked = p.trackedQuest ?? p.quests.findIndex(quest => quest.state === 1);
  for (const [quest, progress, id] of quests) {
    const location = AREAS[quest.area].name + ' · ' + quest.who;
    const details = progress.state === 1 ? quest.detail + ' ' + progress.count + ' / ' + quest.target + ' · ' + location : location;
    panelRow(quest.name, details, progress.state === 1 ? (id === tracked ? '추적 중' : '추적') : null, () => {
      p.trackedQuest = id;
      updateAfterChange();
    }, id === tracked);
  }
}
function renderHotkeys() {
  addText('p', '숫자 1~4 단축키에 원하는 물약이나 스킬을 놓으세요.');
  p.hotbar.forEach((current, index) => {
    const row = document.createElement('label');
    row.className = 'panel-row';
    addText('b', (index + 1) + '번 슬롯', row);
    const select = document.createElement('select');
    select.setAttribute('aria-label', (index + 1) + '번 슬롯');
    for (const [id, action] of [['', {name: '비우기'}], ...Object.entries(HOTBAR_ACTIONS)]) {
      const option = document.createElement('option');
      option.value = id;
      option.textContent = action.name;
      select.append(option);
    }
    select.value = current ?? '';
    select.onchange = () => {
      p.hotbar[index] = Object.hasOwn(HOTBAR_ACTIONS, select.value) ? select.value : null;
      updateHUD();
      save();
    };
    row.append(select);
    panelElement.append(row);
  });
  panelRow('효과음', sound ? '켜짐' : '꺼짐', sound ? '끄기' : '켜기', () => {
    sound = !sound;
    if (sound) beep(600);
    renderPanel();
  });
  panelRow('진행 저장', '이 브라우저에 저장', '저장', () => handleKey('KeyK'));
}

function buy(id, stock) {
  const item = ITEMS[id];
  if (!stock.includes(id) || p.gold < item.price) return;
  p.gold -= item.price;
  addItem(id);
  updateAfterChange();
}
function sell(id) {
  const item = ITEMS[id];
  if (!item || !p.bag[id] || (p.equipment[item.slot] === id && p.bag[id] === 1)) return;
  if (--p.bag[id] === 0) delete p.bag[id];
  p.gold += Math.max(1, Math.floor(item.price / 2));
  updateAfterChange();
}
function renderShop(npc) {
  const tabs = document.createElement('div');
  tabs.className = 'panel-tabs';
  for (const [id, label] of [['buy', '구매'], ['sell', '판매']]) {
    const button = shownButton(label, () => { panelTab = id; renderPanel(); });
    button.setAttribute('aria-pressed', String(panelTab === id));
    tabs.append(button);
  }
  panelElement.append(tabs);
  addText('p', '보유 메소 ' + p.gold);
  if (panelTab === 'buy') {
    for (const id of npc.stock) {
      const item = ITEMS[id];
      panelRow(item.name, itemDetails(item), item.price + ' 메소', () => buy(id, npc.stock), p.gold < item.price, id);
    }
  } else {
    for (const [id, quantity] of Object.entries(p.bag)) {
      const item = ITEMS[id];
      const locked = p.equipment[item.slot] === id && quantity === 1;
      panelRow(item.name + ' × ' + quantity, locked ? '장착 중' : itemDetails(item),
        Math.max(1, Math.floor(item.price / 2)) + ' 메소 받기', () => sell(id), locked, id);
    }
  }
}
function changeJob(id) {
  if (p.level < 5 || p.job !== 'beginner' || id === 'beginner' || !Object.hasOwn(CLASSES, id)) return;
  p.job = id;
  const starter = {guardian: 'blade', ranger: 'bow', mage: 'wand'}[id];
  addItem(starter);
  p.equipment.weapon = starter;
  p.hp = stats().hp;
  p.mp = stats().mp;
  swing = null;
  updateAfterChange();
  toast(CLASSES[id].name + '로 전직했어요. X로 ' + CLASSES[id].skill + ' 사용');
}
function renderTrainer() {
  if (p.job !== 'beginner') {
    addText('p', CLASSES[p.job].name + '의 기술은 ' + CLASSES[p.job].skill + '예요. X로 사용하세요.');
    return;
  }
  addText('p', 'Lv. 5부터 한 직업을 고를 수 있어요. 전직하면 전용 무기를 지급하고 바로 장착해요.');
  const descriptions = {
    guardian: '높은 체력 · 전방에 넓게 베기', ranger: '긴 사거리 · 적 한 마리를 맞히는 화살',
    mage: '높은 마력 · 위아래까지 닿는 별비'
  };
  for (const id of ['guardian', 'ranger', 'mage']) {
    panelRow(CLASSES[id].name, descriptions[id], '전직', () => changeJob(id), p.level < 5);
  }
}
function renderQuest(index) {
  const definition = QUESTS[index];
  const progress = p.quests[index];
  addText('p', definition.detail);
  const rewardText = definition.xp + ' EXP · ' + definition.gold + ' 메소 · ' + ITEMS[definition.item].name;
  if (!progress.state) {
    panelRow(definition.name, rewardText, '의뢰 받기', () => {
      if (progress.state) return;
      progress.state = 1;
      if (p.trackedQuest === null) p.trackedQuest = index;
      updateAfterChange();
      closePanel();
      toast(definition.name + ' 의뢰를 받았어요.');
    });
  } else if (progress.state === 1) {
    panelRow(definition.name + ' · ' + progress.count + ' / ' + definition.target, rewardText, '보상 받기', () => {
      if (progress.state !== 1 || progress.count < definition.target) return;
      progress.state = 2;
      if (p.trackedQuest === index) p.trackedQuest = null;
      p.gold += definition.gold;
      gainXP(definition.xp);
      addItem(definition.item);
      updateAfterChange();
      toast('의뢰 완료 · ' + ITEMS[definition.item].name + ' 획득');
    }, progress.count < definition.target);
  } else {
    addText('p', '의뢰를 완료했어요.');
  }
}
function canCraft(recipe) {
  return p.gold >= recipe.gold && Object.entries(recipe.ingredients).every(([id, amount]) => (p.bag[id] ?? 0) >= amount);
}
function craft(id) {
  const recipe = RECIPES.find(entry => entry.item === id);
  if (panel?.kind !== 'forge' || !recipe || !canCraft(recipe)) return;
  for (const [material, amount] of Object.entries(recipe.ingredients)) {
    p.bag[material] -= amount;
    if (!p.bag[material]) delete p.bag[material];
  }
  p.gold -= recipe.gold;
  addItem(id);
  reportLoot([id], 0);
  updateAfterChange();
  toast(ITEMS[id].name + ' 제작 완료');
}
function renderForge() {
  addText('p', '보유 메소 ' + p.gold + ' · 재료는 몬스터에게서 얻을 수 있어요.');
  for (const recipe of RECIPES) {
    const item = ITEMS[recipe.item];
    const ingredients = Object.entries(recipe.ingredients).map(([id, amount]) => ITEMS[id].name + ' ' + (p.bag[id] ?? 0) + '/' + amount);
    panelRow(item.name, [itemDetails(item), ...ingredients, recipe.gold + ' 메소'].join(' · '),
      '제작', () => craft(recipe.item), !canCraft(recipe), recipe.item);
  }
}
function renderBestiary() {
  const found = SPECIES.filter((_, index) => p.bestiary[index]).length;
  addText('p', '발견한 몬스터 ' + found + '/' + SPECIES.length + ' · 몬스터를 처음 잡으면 드롭 정보가 열려요.');
  for (const [index, species] of SPECIES.entries()) {
    const count = p.bestiary[index] ?? 0;
    const title = 'Lv. ' + species.level + ' · ' + (count ? species.name : '미발견');
    const detail = count ? '처치 ' + count + ' · 드롭 ' + ITEMS[species.loot].name + ' · ' + ITEMS[species.rare].name : null;
    panelRow(title, detail, null, null, false, count ? species.loot : null);
  }
}
function renderAccount() {
  addText('p', onMapleeSite ? '이 사이트는 ChatGPT 계정으로 인증한 소유자만 입장할 수 있어요.' :
    '웹 버전은 ChatGPT 계정 인증으로 입장해요.');
  const link = document.createElement('a');
  link.className = 'account-link';
  link.href = onMapleeSite ? '/signout-with-chatgpt' : MAPLEE_SITE;
  link.target = '_top';
  link.textContent = onMapleeSite ? 'ChatGPT 로그아웃' : '웹에서 ChatGPT 로그인';
  if (onMapleeSite) link.onclick = () => save();
  panelElement.append(link);
  addText('p', '캐릭터와 진행 기록은 지금 브라우저에 저장돼요.');
  panelRow('진행 상황', 'Lv. ' + p.level + ' ' + CLASSES[p.job].name + ' · ' + areaAt(p.x).name,
    '저장', () => handleKey('KeyK'));
}
function renderPanel() {
  panelElement.replaceChildren();
  panelElement.hidden = false;
  const {kind, data} = panel;
  const title = {inventory: '장비와 가방', map: '지역 지도', guide: '유란 · 숲길 안내',
    character: '캐릭터 능력치', skills: '스킬', journal: '퀘스트 기록', hotkeys: '단축키와 설정',
    bestiary: '몬스터 도감', account: '계정과 저장'};
  const heading = document.createElement('div');
  heading.className = 'panel-heading';
  addText('h2', title[kind] ?? (data.name + ' · ' + data.role), heading);
  heading.append(shownButton('닫기', closePanel));
  panelElement.append(heading);

  if (menuPanels.some(([id]) => id === kind) || kind === 'hotkeys') {
    makeTabs([...menuPanels, ['hotkeys', '설정']], kind, id => { panel = {kind: id, data: null}; });
  }
  if (kind === 'inventory') renderInventory();
  if (kind === 'character') renderCharacter();
  if (kind === 'skills') renderSkills();
  if (kind === 'journal') renderJournal();
  if (kind === 'hotkeys') renderHotkeys();
  if (kind === 'shop') renderShop(data);
  if (kind === 'forge') renderForge();
  if (kind === 'bestiary') renderBestiary();
  if (kind === 'account') renderAccount();
  if (kind === 'trainer') renderTrainer();
  if (kind === 'quest' || kind === 'harbor') renderQuest(data.quest ?? (kind === 'quest' ? 0 : 1));
  if (kind === 'guide') addText('p', '맵 가장자리의 출구에서 ↑를 누르면 다음 지역으로 이동해요. 숲길 깊은 곳과 항구 끝에서는 강한 몬스터가 나와요.');
  if (kind === 'map') {
    addText('p', '하늘색 표시는 출구, 주황색은 NPC, 노란색은 내 위치예요.');
    const current = areaAt(p.x);
    addText('p', '현재 위치 · ' + current.name);
    for (const area of AREAS) panelRow(area.icon + ' ' + area.name, area === current ? '현재 위치' : '맵 끝의 출구에서 ↑');
  }
}
function interact() {
  if (paused) return;
  if (panel) { closePanel(); return; }
  const portal = nearbyPortal();
  if (portal) {
    travelTo(portal.target);
    save();
    return;
  }
  const npc = nearbyNPC();
  if (npc) {
    panelTab = 'buy';
    openPanel(npc.kind, npc);
  }
}
function home() {
  closePanel();
  travelTo(START_X);
  save();
  toast('솔방울 마을로 돌아왔어요.');
}
function handleKey(code) {
  if (code === 'Escape') closePanel();
  if (code === 'Space') jump();
  if (code === 'KeyZ') attack();
  if (code === 'KeyX') attack(true);
  if (code === 'KeyV') useSupport();
  if (code === 'ArrowUp' && !panel) interact();
  const menu = menuPanels.find(([, , shortcut]) => shortcut && code === 'Key' + shortcut);
  if (menu) openPanel(menu[0]);
  if (code === 'KeyR') home();
  if (code === 'KeyK') toast(save() ? '모험을 저장했어요.' : '저장 공간을 사용할 수 없어요.');
  const slot = HOTKEYS.indexOf(code);
  if (slot >= 0) runSlot(slot);
}

window.addEventListener('keydown', event => {
  if (['SELECT', 'INPUT', 'TEXTAREA'].includes(event.target?.tagName) && event.code !== 'Escape') return;
  if (['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown', 'Space'].includes(event.code)) {
    if (event.code === 'Space' && panel && event.target?.tagName === 'BUTTON') return;
    event.preventDefault();
  }
  keys[event.code] = true;
  if (!event.repeat) handleKey(event.code);
});
window.addEventListener('keyup', event => { keys[event.code] = false; });
window.addEventListener('blur', () => {
  for (const code of Object.keys(keys)) keys[code] = false;
  save();
});
window.addEventListener('pagehide', save);
for (const button of document.querySelectorAll('[data-key]')) {
  const code = button.dataset.key;
  button.onpointerdown = event => {
    event.preventDefault();
    button.setPointerCapture(event.pointerId);
    keys[code] = true;
    handleKey(code);
  };
  button.onpointerup = button.onpointercancel = () => { keys[code] = false; };
}
for (const [id] of menuPanels) $('#' + id).onclick = () => openPanel(id);
$('#minimap-button').onclick = () => openPanel('map');
$('#quest-button').onclick = () => openPanel('journal');
$('#hotkeys').onclick = () => openPanel('hotkeys');
HOTKEYS.forEach((_, i) => { $('#slot-' + i).onclick = () => runSlot(i); });
$('#pause').onclick = () => {
  if (panel) closePanel();
  paused = !paused;
  $('#pause').textContent = paused ? '계속하기' : '일시정지';
};
loadGame();
populate();
camera = cameraTarget(p.x);
$('#region').textContent = areaAt(p.x).name;
updateHUD();
