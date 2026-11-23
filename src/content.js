'use strict';

const WORLD_WIDTH = 12000;
const AREAS = [
  {name: '솔방울 마을', start: 0, end: 2450, icon: '🍄', material: 'stone', backdrop: [0.01, 0.14]},
  {name: '종꽃 숲길', start: 2450, end: 9100, icon: '🌿', material: 'terrain', backdrop: [0.19, 0.49]},
  {name: '푸른돛 항구', start: 9100, end: WORLD_WIDTH, icon: '⚓', material: 'stone', backdrop: [0.56, 0.63]}
];

const groundPoints = [
  [0, 390], [400, 390], [660, 338], [1140, 338], [1380, 388], [1750, 388], [1990, 355],
  [2290, 355], [2550, 369], [2840, 369], [3090, 308], [3540, 308], [3790, 353], [4170, 353],
  [4460, 403], [4800, 403], [5050, 358], [5430, 358], [5710, 318], [6050, 318],
  [6350, 382], [6820, 382], [7110, 332], [7540, 332], [7820, 413], [8180, 413],
  [8460, 379], [8740, 379], [9090, 397], [9510, 397], [9800, 352], [10310, 352],
  [10640, 305], [11000, 305], [11310, 355], [WORLD_WIDTH, 355]
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
  [10640, 138, 230, 16], [10970, 212, 298, 155], [11240, 152, 184, 18], [11510, 237, 280, 95]
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
  [10355,3,76], [10730,5,196], [11155,4,205], [11670,5,185]
];

const CLASSES = {
  beginner: {name: '모험가', skill: '별빛 파동', attack: 0, hp: 0, mp: 0, cost: 8, cooldown: 170, reach: 110, power: 1.6, shape: 'ring'},
  guardian: {name: '수호검사', skill: '가르기', attack: 3, hp: 32, mp: 0, cost: 10, cooldown: 125, reach: 104, power: 2.3, shape: 'arc'},
  ranger: {name: '숲길잡이', skill: '바람 화살', attack: 2, hp: 8, mp: 10, cost: 9, cooldown: 105, reach: 340, power: 2.05, shape: 'arrow'},
  mage: {name: '별빛술사', skill: '별비', attack: 1, hp: 0, mp: 32, cost: 16, cooldown: 155, reach: 188, power: 2.35, shape: 'stars'}
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
  tonic: {name: '마력 물약', price: 32}
};
const SLOTS = {weapon: '무기', armor: '방어구', charm: '장신구'};
const SPECIES = [
  {name: '이슬방울', level: 1, sprite: 0, hp: 15, attack: 8, xp: 17, gold: 14, speed: 0.7, loot: 'jelly', rare: 'bronze'},
  {name: '호박 갓버섯', level: 3, sprite: 1, hp: 34, attack: 13, xp: 32, gold: 23, speed: 0.8, loot: 'spores', rare: 'cap'},
  {name: '안개 정령', level: 5, sprite: 2, hp: 57, attack: 19, xp: 52, gold: 35, speed: 1.0, float: true, loot: 'ash', rare: 'dew'},
  {name: '소금 갓버섯', level: 7, sprite: 1, tint: 'hue-rotate(143deg)', hp: 84, attack: 25, xp: 75, gold: 50, speed: 1.05, loot: 'coral', rare: 'shell'},
  {name: '등대 수문장', level: 9, sprite: 2, tint: 'hue-rotate(42deg)', hp: 190, attack: 34, xp: 190, gold: 140, speed: 1.2, float: true, loot: 'coral', rare: 'prism', elite: true}
];
const NPCS = [
  {x: 475, name: '리나', role: '의뢰', kind: 'quest'},
  {x: 870, name: '토비', role: '보급품', kind: 'shop', stock: ['potion','tonic','bronze','coat','dew']},
  {x: 1430, name: '다온', role: '전직', kind: 'trainer'},
  {x: 2230, name: '유란', role: '숲길 안내', kind: 'guide'},
  {x: 9660, name: '마레', role: '항구 장비점', kind: 'shop', stock: ['potion','tonic','blade','bow','wand','shell','prism']},
  {x: 10670, name: '등대지기', role: '의뢰', kind: 'harbor'}
];
const QUESTS = [
  {name: '숲길 청소', who: '리나', target: 8, matches: [0,1], xp: 85, gold: 95, item: 'coat'},
  {name: '항구의 불빛', who: '등대지기', target: 1, matches: [4], xp: 220, gold: 190, item: 'prism'}
];
