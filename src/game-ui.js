'use strict';

const panelElement = $('#panel');
let panelTab = 'buy';

function shownButton(text, onClick, disabled = false) {
  const button = document.createElement('button');
  button.textContent = text;
  button.disabled = disabled;
  button.onclick = onClick;
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
  if (item.slot) parts.push(SLOTS[item.slot], 'Lv. ' + item.level);
  if (item.job) parts.push(CLASSES[item.job].name);
  for (const [key, label] of Object.entries({attack: '공격', defense: '방어', hp: '최대 HP', mp: '최대 MP'})) {
    if (item[key]) parts.push(label + ' +' + item[key]);
  }
  return parts.join(' · ');
}
function panelRow(title, details, action, handler, blocked = false) {
  const row = document.createElement('div');
  row.className = 'panel-row';
  const label = document.createElement('div');
  addText('b', title, label);
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
  const limits = stats();
  addText('p', 'Lv. ' + p.level + ' ' + CLASSES[p.job].name + ' · 공격력 ' + limits.attack + ' · 방어력 ' + limits.defense);
  for (const [slot, label] of Object.entries(SLOTS)) {
    const id = p.equipment[slot];
    panelRow(label + ' · ' + (id ? ITEMS[id].name : '비어 있음'), id && itemDetails(ITEMS[id]));
  }
  addText('h3', '가방');
  panelRow('체력 물약 × ' + p.pots, 'HP 55 회복', '사용', () => healWith('potion'), !p.pots);
  panelRow('마력 물약 × ' + p.tonics, 'MP 35 회복', '사용', () => healWith('tonic'), !p.tonics);
  for (const [id, amount] of Object.entries(p.bag)) {
    if (!amount) continue;
    const item = ITEMS[id];
    const equipped = item.slot && p.equipment[item.slot] === id;
    panelRow(item.name + ' × ' + amount, itemDetails(item), item.slot ? (equipped ? '해제' : '장착') : null,
      () => toggleEquipment(id), !canEquip(id));
  }
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
      panelRow(item.name, itemDetails(item), item.price + ' 메소', () => buy(id, npc.stock), p.gold < item.price);
    }
  } else {
    for (const [id, quantity] of Object.entries(p.bag)) {
      const item = ITEMS[id];
      const locked = p.equipment[item.slot] === id && quantity === 1;
      panelRow(item.name + ' × ' + quantity, locked ? '장착 중' : itemDetails(item),
        Math.max(1, Math.floor(item.price / 2)) + ' 메소 받기', () => sell(id), locked);
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
  const detail = index ? '항구 끝에서 등대 수문장을 처치해 주세요.' : '숲길의 이슬방울과 호박 갓버섯을 8마리 처치해 주세요.';
  addText('p', detail);
  const rewardText = definition.xp + ' EXP · ' + definition.gold + ' 메소 · ' + ITEMS[definition.item].name;
  if (!progress.state) {
    panelRow(definition.name, rewardText, '의뢰 받기', () => {
      if (progress.state) return;
      progress.state = 1;
      updateAfterChange();
      closePanel();
      toast(definition.name + ' 의뢰를 받았어요.');
    });
  } else if (progress.state === 1) {
    panelRow(definition.name + ' · ' + progress.count + ' / ' + definition.target, rewardText, '보상 받기', () => {
      if (progress.state !== 1 || progress.count < definition.target) return;
      progress.state = 2;
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
function renderPanel() {
  panelElement.replaceChildren();
  panelElement.hidden = false;
  const {kind, data} = panel;
  const title = {inventory: '장비와 가방', map: '지역 지도', guide: '유란 · 숲길 안내'};
  const heading = document.createElement('div');
  heading.className = 'panel-heading';
  addText('h2', title[kind] ?? (data.name + ' · ' + data.role), heading);
  heading.append(shownButton('닫기', closePanel));
  panelElement.append(heading);

  if (kind === 'inventory') renderInventory();
  if (kind === 'shop') renderShop(data);
  if (kind === 'trainer') renderTrainer();
  if (kind === 'quest' || kind === 'harbor') renderQuest(kind === 'quest' ? 0 : 1);
  if (kind === 'guide') addText('p', '맵 가장자리의 출구에서 ↑를 누르면 다음 지역으로 이동해요. 숲길 깊은 곳과 항구 끝에서는 강한 몬스터가 나와요.');
  if (kind === 'map') {
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
  if (code === 'ArrowUp' && !panel) interact();
  if (code === 'KeyI') openPanel('inventory');
  if (code === 'KeyM') openPanel('map');
  if (code === 'KeyR') home();
  if (code === 'KeyK') toast(save() ? '모험을 저장했어요.' : '저장 공간을 사용할 수 없어요.');
}

window.addEventListener('keydown', event => {
  if (['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown', 'Space'].includes(event.code)) {
    if (event.code === 'Space' && event.target?.tagName === 'BUTTON') return;
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
$('#potion').onclick = () => healWith('potion');
$('#tonic').onclick = () => healWith('tonic');
$('#inventory').onclick = () => openPanel('inventory');
$('#mapbutton').onclick = () => openPanel('map');
$('#returnbutton').onclick = home;
$('#savebutton').onclick = () => handleKey('KeyK');
$('#pause').onclick = () => {
  if (panel) closePanel();
  paused = !paused;
  $('#pause').textContent = paused ? '계속하기' : '일시정지';
};
$('#sound').onclick = () => {
  sound = !sound;
  $('#sound').textContent = sound ? '소리 끄기' : '소리 켜기';
  beep(600);
};

loadGame();
populate();
camera = cameraTarget(p.x);
updateHUD();
