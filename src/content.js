'use strict';

const WORLD_WIDTH = 18300;
const AREAS = [
  {name: '솔방울 마을', start: 0, end: 2450, icon: '🍄', material: 'stone', backdrop: [0.01, 0.14]},
  {name: '종꽃 숲길', start: 2450, end: 9100, icon: '🌿', material: 'terrain', backdrop: [0.19, 0.49]},
  {name: '푸른돛 항구', start: 9100, end: 12000, icon: '⚓', material: 'stone', backdrop: [0.56, 0.63]},
  {name: '유리빛 광산', start: 12000, end: 14900, icon: '💎', material: 'stone', image: 'depths', backdrop: [0.02, 0.13], tint: '#271d5455'},
  {name: '달바람 고원', start: 14900, end: WORLD_WIDTH, icon: '🌙', material: 'terrain', image: 'depths', backdrop: [0.51, 0.63], tint: '#44275933'}
];

const groundPoints = [
  [0, 390], [400, 390], [660, 338], [1140, 338], [1380, 388], [1750, 388], [1990, 355],
  [2290, 355], [2550, 369], [2840, 369], [3090, 308], [3540, 308], [3790, 353], [4170, 353],
  [4460, 403], [4800, 403], [5050, 358], [5430, 358], [5710, 318], [6050, 318],
  [6350, 382], [6820, 382], [7110, 332], [7540, 332], [7820, 413], [8180, 413],
  [8460, 379], [8740, 379], [9090, 397], [9510, 397], [9800, 352], [10310, 352],
  [10640, 305], [11000, 305], [11310, 355], [12000, 355], [12450, 398], [12860, 398], [13220, 336],
  [13550, 336], [13910, 397], [14250, 397], [14600, 342], [14900, 342], [15250, 388], [15750, 388],
  [16120, 324], [16600, 324], [16900, 379], [17270, 379], [17600, 339], [WORLD_WIDTH, 339]
];

const ledges = [
  [260, 248, 240, 112], [533, 195, 240, 178], [870, 237, 256, 84], [1300, 274, 235, 109],
  [1490, 191, 267, 26], [1850, 236, 252, 134], [2100, 149, 161, 100], [2250, 253, 193, 106],
  [2480, 272, 240, 116], [2685, 184, 258, 20], [3060, 218, 284, 114], [3320, 133, 250, 18],
  [3640, 235, 290, 134], [3890, 157, 210, 23], [4160, 274, 329, 159], [4480, 190, 226, 16],
  [4810, 286, 244, 92], [5100, 228, 318, 141], [5380, 142, 230, 16], [5720, 200, 340, 176],
  [6050, 276, 242, 102], [6340, 216, 271, 140], [6580, 124, 209, 21], [6900, 252, 330, 172],
  [7200, 162, 252, 20], [7510, 223, 295, 122], [7820, 288, 224, 103], [8030, 198, 244, 16],
  [8320, 285, 275, 151], [8570, 214, 253, 18], [8860, 271, 223, 117], [9120, 224, 309, 145],
  [9410, 147, 215, 16], [9705, 246, 291, 122], [10040, 197, 263, 137], [10400, 221, 249, 135],
  [10640, 138, 230, 16], [10970, 212, 298, 155], [11240, 152, 184, 18], [11510, 237, 280, 95],
  [12100,262,260,114], [12330,169,290,22], [12630,280,260,96], [12890,224,280,105],
  [13140,138,230,20], [13410,237,275,108], [13710,294,240,110], [13950,195,260,125],
  [14200,274,280,102], [14450,179,250,26], [14710,245,175,75], [15020,246,250,99],
  [15250,154,260,16], [15550,268,270,135], [15850,208,282,132], [16110,123,260,17],
  [16400,238,255,122], [16650,182,265,19], [16950,275,312,116], [17250,186,240,25],
  [17500,252,254,119], [17800,209,340,120]
].map(([x, y, w, ladderOffset]) => ({x, y, w, ladderX: x + ladderOffset}));

const sceneryProps = [
  [195,0,175], [413,2,126,248], [615,2,137], [830,1,210], [1070,0,145,237],
  [1350,2,160], [1530,1,140,191], [1935,0,165], [2200,2,170], [2370,3,79],
  [2580,3,105,272], [2750,2,175], [2825,3,92,184], [3190,2,133,218], [3460,3,112],
  [3680,2,156], [3780,3,116,235], [4050,3,102], [4325,2,157,274], [4560,3,107],
  [4920,3,108,286], [5175,2,164], [5270,3,99,228], [5705,3,116], [5910,2,158,200],
  [6180,3,109,276], [6370,2,179], [6760,3,102,124], [7050,3,117,252], [7445,2,181],
  [7680,3,100,223], [7990,2,162], [8170,3,114,198], [8430,2,170], [8765,3,121,214],
  [9000,2,145], [9300,4,154,224], [9470,4,217], [9850,2,120], [10150,4,182],
  [10355,3,76], [10730,5,196], [11155,4,205], [11670,5,185],
  [12200,3,105,262], [12439,3,108], [13000,3,105,224], [13555,3,130], [14020,3,119,195],
  [14630,3,122], [15140,2,134,246], [15500,3,115], [16020,2,143,208],
  [16520,3,104,238], [17010,2,170], [17660,3,114,252], [18140,2,184]
];

const CLASSES = {
  beginner: {name: '모험가', skill: '별빛 파동', attack: 0, hp: 0, mp: 0, cost: 8, cooldown: 170, reach: 110, power: 1.6, shape: 'ring'},
  guardian: {name: '수호검사', skill: '가르기', attack: 3, hp: 32, mp: 0, cost: 10, cooldown: 125, reach: 104, power: 2.3, shape: 'arc'},
  ranger: {name: '숲길잡이', skill: '바람 화살', attack: 2, hp: 8, mp: 10, cost: 9, cooldown: 105, reach: 340, power: 2.05, shape: 'arrow'},
  mage: {name: '별빛술사', skill: '별비', attack: 1, hp: 0, mp: 32, cost: 16, cooldown: 155, reach: 188, power: 2.35, shape: 'stars'}
};

const ATTRIBUTES = {
  strength: {name: '힘', detail: '공격력 +2', icon: '◆', attack: 2},
  vitality: {name: '체력', detail: '최대 HP +8 · 방어력 +1', icon: '♥', hp: 8, defense: 1},
  spirit: {name: '정신', detail: '최대 MP +5', icon: '✦', mp: 5},
  agility: {name: '민첩', detail: '이동 속도 +0.09', icon: '➟', speed: 0.09}
};
const SUPPORTS = {
  guardian: {name: '철벽 맹세', summary: '잠시 방어력을 높여요.', stat: 'defense', power: 7, cost: 12},
  ranger: {name: '순풍 걸음', summary: '잠시 이동 속도를 높여요.', stat: 'speed', power: 1.25, cost: 12},
  mage: {name: '별불 집중', summary: '잠시 공격력을 높여요.', stat: 'attack', power: 8, cost: 15}
};
const HOTKEYS = ['Digit1', 'Digit2', 'Digit3', 'Digit4'];
const DEFAULT_HOTBAR = ['hp', 'mp', 'skill', 'support'];
const HOTBAR_ACTIONS = {
  hp: {name: '체력 물약', icon: '♥', color: 'rose'},
  mp: {name: '마력 물약', icon: '◆', color: 'sky'},
  skill: {name: '직업 스킬', icon: '✦', color: 'violet'},
  support: {name: '보조 스킬', icon: '⬡', color: 'mint'},
  home: {name: '마을 귀환', icon: '⌂', color: 'gold'}
};

const ITEMS = {
  twig: {name: '여행자의 목검', slot: 'weapon', level: 1, attack: 2, price: 25},
  bronze: {name: '청동 검', slot: 'weapon', level: 2, attack: 5, price: 78},
  coat: {name: '여행자의 조끼', slot: 'armor', level: 2, defense: 2, hp: 12, price: 65},
  cap: {name: '버섯 가죽 모자', slot: 'armor', level: 3, defense: 4, hp: 20, price: 110},
  dew: {name: '이슬 장식', slot: 'charm', level: 3, hp: 18, mp: 10, price: 96},
  blade: {name: '수호자의 사브르', slot: 'weapon', level: 5, job: 'guardian', attack: 12, price: 245},
  bow: {name: '솔가지 활', slot: 'weapon', level: 5, job: 'ranger', attack: 11, price: 245},
  wand: {name: '별무리 지팡이', slot: 'weapon', level: 5, job: 'mage', attack: 11, mp: 12, price: 245},
  shell: {name: '진주빛 흉갑', slot: 'armor', level: 7, defense: 8, hp: 36, price: 390},
  prism: {name: '등대 수정', slot: 'charm', level: 8, attack: 3, hp: 24, mp: 24, price: 420},
  jelly: {name: '풀빛 젤리', price: 15},
  spores: {name: '호박 버섯 포자', price: 24},
  ash: {name: '안개 가루', price: 39},
  coral: {name: '바람 산호', price: 56},
  potion: {name: '체력 물약', price: 28},
  tonic: {name: '마력 물약', price: 32},
  quartz: {name: '별철 원석', price: 68, icon: 12, rarity: 'uncommon'},
  plume: {name: '달바람 깃털', price: 85, icon: 15, rarity: 'uncommon'},
  anchor: {name: '수문장의 닻 파편', price: 120, icon: 13, rarity: 'rare'},
  nightcore: {name: '달철 심장', price: 220, icon: 13, rarity: 'epic'},
  glasscoat: {name: '유리맥 갑옷', slot: 'armor', level: 10, defense: 12, hp: 54, price: 620, icon: 14, rarity: 'rare'},
  moonseal: {name: '달바람 인장', slot: 'charm', level: 12, attack: 8, hp: 36, mp: 42, price: 830, icon: 12, rarity: 'epic'},
  sunblade: {name: '황혼의 대검', slot: 'weapon', level: 11, job: 'guardian', attack: 29, hp: 26, price: 920, icon: 0, rarity: 'epic'},
  nightbow: {name: '월백의 순풍궁', slot: 'weapon', level: 11, job: 'ranger', attack: 27, mp: 22, price: 920, icon: 1, rarity: 'epic'},
  tidewand: {name: '유리별 홀', slot: 'weapon', level: 11, job: 'mage', attack: 27, mp: 34, price: 920, icon: 2, rarity: 'epic'},
  crabguard: {name: '산호 외투', slot: 'armor', level: 8, defense: 9, hp: 43, price: 515, icon: 3, rarity: 'rare'},
  shimmer: {name: '반딧불 목걸이', slot: 'charm', level: 9, hp: 27, mp: 30, price: 555, icon: 13, rarity: 'rare'}
};
const SLOTS = {weapon: '무기', armor: '방어구', charm: '장신구'};
const SPECIES = [
  {name: '이슬방울', level: 1, sprite: 0, hp: 15, attack: 8, xp: 17, gold: 14, speed: 0.7, loot: 'jelly', rare: 'bronze'},
  {name: '호박 갓버섯', level: 3, sprite: 1, hp: 34, attack: 13, xp: 32, gold: 23, speed: 0.8, loot: 'spores', rare: 'cap'},
  {name: '안개 정령', level: 5, sprite: 2, hp: 57, attack: 19, xp: 52, gold: 35, speed: 1.0, float: true, loot: 'ash', rare: 'dew'},
  {name: '소금 갓버섯', level: 7, sprite: 1, tint: 'hue-rotate(143deg)', hp: 84, attack: 25, xp: 75, gold: 50, speed: 1.05, loot: 'coral', rare: 'shell'},
  {name: '등대 수문장', level: 9, sprite: 2, tint: 'hue-rotate(42deg)', hp: 190, attack: 34, xp: 190, gold: 140, speed: 1.2, float: true, loot: 'anchor', rare: 'prism', elite: true, aggro: 105},
  {name: '유리집게', level: 8, sprite: 3, hp: 95, attack: 24, xp: 83, gold: 54, speed: 1.25, loot: 'coral', rare: 'crabguard', aggro: 110},
  {name: '수정방울', level: 9, sprite: 0, tint: 'hue-rotate(138deg)', hp: 119, attack: 28, xp: 103, gold: 67, speed: 1.00, loot: 'quartz', rare: 'glasscoat', aggro: 90},
  {name: '별철 파수꾼', level: 11, sprite: 4, hp: 175, attack: 35, xp: 142, gold: 81, speed: 1.05, loot: 'quartz', rare: 'glasscoat', aggro: 144},
  {name: '달바람 정령', level: 12, sprite: 2, tint: 'hue-rotate(277deg)', hp: 204, attack: 39, xp: 171, gold: 93, speed: 1.35, float: true, loot: 'plume', rare: 'shimmer', aggro: 143},
  {name: '월광 집게', level: 13, sprite: 3, tint: 'hue-rotate(65deg)', hp: 231, attack: 43, xp: 196, gold: 104, speed: 1.5, loot: 'plume', rare: 'moonseal', aggro: 147},
  {name: '달철 기사', level: 15, sprite: 4, tint: 'hue-rotate(215deg)', hp: 655, attack: 55, xp: 680, gold: 390, speed: 1.28, loot: 'nightcore', rare: 'moonseal', elite: true, aggro: 193}
];
const NPCS = [
  {x: 475, name: '리나', role: '의뢰', kind: 'quest'},
  {x: 870, name: '토비', role: '보급품', kind: 'shop', stock: ['potion','tonic','bronze','coat','dew']},
  {x: 1430, name: '다온', role: '전직', kind: 'trainer'},
  {x: 2230, name: '유란', role: '숲길 안내', kind: 'guide'},
  {x: 5710, name: '노을', role: '숲길 의뢰', kind: 'quest', quest: 2},
  {x: 9660, name: '마레', role: '항구 장비점', kind: 'shop', stock: ['potion','tonic','blade','bow','wand','shell','prism']},
  {x: 10670, name: '등대지기', role: '의뢰', kind: 'harbor'},
  {x: 12170, name: '리오', role: '대장간', kind: 'forge'},
  {x: 12425, name: '하람', role: '광산 의뢰', kind: 'quest', quest: 3},
  {x: 13370, name: '수아', role: '광산 조사', kind: 'quest', quest: 4},
  {x: 15095, name: '여울', role: '고원 의뢰', kind: 'quest', quest: 5},
  {x: 15320, name: '찬별', role: '고원 보급품', kind: 'shop', stock: ['potion','tonic','crabguard','glasscoat','shimmer']},
  {x: 16645, name: '자야', role: '달철 기사 의뢰', kind: 'quest', quest: 6}
];
const QUESTS = [
  {
    name: '숲길 청소', who: '리나', area: 0, target: 8, matches: [0, 1], xp: 85, gold: 95, item: 'coat',
    detail: '숲길의 이슬방울과 호박 갓버섯을 처치하세요.'
  },
  {
    name: '항구의 불빛', who: '등대지기', area: 2, target: 1, matches: [4], xp: 220, gold: 190, item: 'prism',
    detail: '항구 끝에 있는 등대 수문장을 처치하세요.'
  },
  {
    name: '종꽃에 남은 안개', who: '노을', area: 1, target: 5, matches: [2], xp: 155, gold: 120, item: 'dew',
    detail: '숲길 깊은 곳에서 안개 정령을 처치하세요.'
  },
  {name: '유리맥 안전 점검', who: '하람', area: 3, target: 8, matches: [6,7], xp: 350, gold: 240, item: 'glasscoat',
    detail: '광산의 수정방울과 별철 파수꾼을 처치하세요.'},
  {name: '광산의 푸른 집게', who: '수아', area: 3, target: 5, matches: [5], xp: 240, gold: 165, item: 'crabguard',
    detail: '광산 입구와 항구에서 유리집게를 처치하세요.'},
  {name: '달바람 관측', who: '여울', area: 4, target: 9, matches: [8,9], xp: 500, gold: 330, item: 'shimmer',
    detail: '고원의 달바람 정령과 월광 집게를 처치하세요.'},
  {name: '납빛 갑옷의 밤', who: '자야', area: 4, target: 1, matches: [10], xp: 720, gold: 450, item: 'moonseal',
    detail: '고원 끝의 달철 기사를 쓰러뜨리세요.'}
];

const RECIPES = [
  {item: 'crabguard', ingredients: {coral: 4}, gold: 105},
  {item: 'glasscoat', ingredients: {quartz: 5, coral: 2}, gold: 180},
  {item: 'shimmer', ingredients: {ash: 4, quartz: 2}, gold: 160},
  {item: 'sunblade', ingredients: {quartz: 8, anchor: 1}, gold: 325},
  {item: 'nightbow', ingredients: {quartz: 8, anchor: 1}, gold: 325},
  {item: 'tidewand', ingredients: {quartz: 8, anchor: 1}, gold: 325},
  {item: 'moonseal', ingredients: {plume: 6, nightcore: 1}, gold: 390}
];
const ITEM_ICONS = {twig: 0, bronze: 0, blade: 0, bow: 1, wand: 2, coat: 14, cap: 14,
  dew: 12, shell: 3, prism: 12, jelly: 8, spores: 9, ash: 10, coral: 11, potion: 4, tonic: 5};
const itemIcon = id => ITEMS[id]?.icon ?? ITEM_ICONS[id] ?? 6;
