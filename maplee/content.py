"""Static world layout, jobs, items, encounters and quests."""

from bisect import bisect_right
from .gear_data import EXPANSION_EQUIPMENT, EXPANSION_ICON_COLUMNS, LEGACY_WORN, MELEE_WEAPONS, WORN_ITEMS, WORN_ROWS
from .wildlife_data import MOB_BOOKS, MOB_FRAMES

WORLD_LAYOUT = 6
PRESERVED_LAYOUTS = (3, 4, 5, WORLD_LAYOUT)
PANORAMA_Y = 144
LEDGE_DEPTH = 32
BELLFLOWER_START, BELLFLOWER_END = 2450, 9100
WORLD_SCALE = 1.25


def map_x(value):
    """Convert coordinates authored against the original layout."""
    forest_distance = min(max(value - BELLFLOWER_START, 0), BELLFLOWER_END - BELLFLOWER_START)
    return round((value - forest_distance / 4) * WORLD_SCALE)


def saved_x(value, layout):
    if layout in PRESERVED_LAYOUTS:
        return int(value)
    if layout == 2:
        value /= WORLD_SCALE
    return map_x(value)


BASE_WORLD_WIDTH = 41000
MAP_IDS = ["pinecone", "bellflower", "blue-sail", "glass-mine", "moonwind", "ember-grove",
           "lantern-quay", "windroot", "sunset-eggs", "copper-terraces", "glassseed"]
MAIN_REGIONS = ((0,2,"솔방울 해안"),(3,6,"유리 산맥"),(7,10,"바람뿌리 군도"))
TRANSPORT_LABELS = {"boat":"배", "airship":"비행선"}

AREAS = [
    dict(name="솔방울 마을", start=0, end=BELLFLOWER_START, icon="🍄", material="stone", image="daylight", view=0),
    dict(name="종꽃 숲길", start=BELLFLOWER_START, end=BELLFLOWER_END, icon="🌿", material="terrain", image="bellflower", view=270),
    dict(name="푸른돛 항구", start=BELLFLOWER_END, end=12000, icon="⚓", material="stone", image="daylight", view=870),
    dict(name="유리빛 광산", start=12000, end=14900, icon="💎", material="quarry_ground", image="cavern", view=0),
    dict(name="달바람 고원", start=14900, end=18300, icon="🌙", material="terrain", image="highland", view=0),
    dict(name="잿등불 숲", start=18300, end=21400, icon="✧", material="terrain", image="ember_grove", view=0),
    dict(name="안개등 부두", start=21400, end=24700, icon="⚓", material="stone", image="lantern_quay", view=0),
    dict(name="바람뿌리 거목", start=24700, end=29300, icon="🌳", material="terrain", image="windroot", view=0),
    dict(name="노을알 분지", start=29300, end=34000, icon="🥚", material="stone", image="sunegg", view=170),
    dict(name="구리층 계단", start=34000, end=37100, icon="🔶", material="copper_ground", image="terrace_sky", view=90),
    dict(name="물빛 씨앗숲", start=37100, end=BASE_WORLD_WIDTH, icon="🌱", material="seed_ground", image="seed_sky",
         mid_image="seed_canopy", view=140),
]

# Main-map surfaces use the existing grass-topped cliff sheets. The tint is
# baked into each tile variant before the renderer repeats it over slopes.
MAIN_TERRAIN = (
    ("terrain", "#58462922"),        # 솔방울 마을
    ("seed_ground", "#30442a28"),    # 종꽃 숲길
    ("quarry_ground", "#59514426"),  # 푸른돛 항구
    ("quarry_ground", "#34334465"),  # 유리빛 광산
    ("copper_ground", "#57413b20"),  # 달바람 고원
    ("copper_ground", "#522e4154"),  # 잿등불 숲
    ("seed_ground", "#293b4c49"),    # 안개등 부두
    ("seed_ground", "#28391e33"),    # 바람뿌리 거목
    ("copper_ground", "#633a2424"),  # 노을알 분지
    ("quarry_ground", "#6b43282e"),  # 구리층 계단
    ("terrain", "#213d3c35"),        # 물빛 씨앗숲
)
for _area, (_material, _tint) in zip(AREAS, MAIN_TERRAIN):
    _area.update(material=_material, terrain_tint=_tint)

GROUND = [[0, 390],
 [400, 390],
 [660, 338],
 [1140, 338],
 [1380, 388],
 [1750, 388],
 [1990, 355],
 [2290, 355],
 [2550, 369],
 [2840, 369],
 [3090, 308],
 [3540, 308],
 [3790, 353],
 [4170, 353],
 [4460, 403],
 [4800, 403],
 [5050, 358],
 [5430, 358],
 [5710, 318],
 [6050, 318],
 [6350, 382],
 [6820, 382],
 [7110, 332],
 [7540, 332],
 [7820, 413],
 [8180, 413],
 [8460, 379],
 [8740, 379],
 [9090, 397],
 [9510, 397],
 [9800, 352],
 [10310, 352],
 [10640, 305],
 [11000, 305],
 [11310, 355],
 [12000, 355],
 [12450, 398],
 [12860, 398],
 [13220, 336],
 [13550, 336],
 [13910, 397],
 [14250, 397],
 [14600, 342],
 [14900, 342],
 [15250, 388],
 [15750, 388],
 [16120, 324],
 [16600, 324],
 [16900, 379],
 [17270, 379],
 [17600, 339],
 [18300, 339]]

GROUND.extend(((18540,358),(18920,390),(19360,390),(19740,332),(20200,332),
               (20520,378),(20860,378),(21400,355),(21740,355),(22140,402),
               (22500,402),(22980,327),(23340,327),(23740,371),(24060,371),(24700,356)))
GROUND.extend((
    (25010,356),(25440,390),(25800,390),(26150,344),(26800,344),
    (27200,399),(27800,399),(28200,359),(28700,359),(29300,383),
    (29640,383),(29980,345),(30500,345),(30820,398),(31250,398),
    (31700,342),(32140,342),(32600,387),(33000,387),(33510,346),(34000,346),
    (34300,346),(34800,388),(35150,388),(35630,334),(36240,334),(36700,384),(37100,384),
    (37480,384),(37920,334),(38250,334),(38580,395),(39110,395),(39600,352),
    (40280,352),(40780,382),(41000,382),
))

LEDGES = [{'x': 260, 'y': 248, 'w': 240, 'ladderX': 372},
 {'x': 533, 'y': 195, 'w': 240, 'ladderX': 711},
 {'x': 870, 'y': 237, 'w': 256, 'ladderX': 954},
 {'x': 1300, 'y': 274, 'w': 235, 'ladderX': 1409},
 {'x': 1490, 'y': 191, 'w': 267, 'ladderX': 1516},
 {'x': 1850, 'y': 236, 'w': 252, 'ladderX': 1984},
 {'x': 2100, 'y': 149, 'w': 161, 'ladderX': 2200},
 {'x': 2250, 'y': 253, 'w': 193, 'ladderX': 2356},
 {'x': 2480, 'y': 272, 'w': 240, 'ladderX': 2596},
 {'x': 2685, 'y': 184, 'w': 258, 'ladderX': 2705},
 {'x': 3060, 'y': 218, 'w': 284, 'ladderX': 3174},
 {'x': 3320, 'y': 133, 'w': 250, 'ladderX': 3338},
 {'x': 3640, 'y': 235, 'w': 290, 'ladderX': 3774},
 {'x': 3890, 'y': 157, 'w': 210, 'ladderX': 3913},
 {'x': 4160, 'y': 274, 'w': 329, 'ladderX': 4319},
 {'x': 4480, 'y': 190, 'w': 226, 'ladderX': 4496},
 {'x': 4810, 'y': 286, 'w': 244, 'ladderX': 4902},
 {'x': 5100, 'y': 228, 'w': 318, 'ladderX': 5241},
 {'x': 5380, 'y': 142, 'w': 230, 'ladderX': 5396},
 {'x': 5720, 'y': 200, 'w': 340, 'ladderX': 5896},
 {'x': 6050, 'y': 276, 'w': 242, 'ladderX': 6152},
 {'x': 6340, 'y': 216, 'w': 271, 'ladderX': 6480},
 {'x': 6580, 'y': 124, 'w': 209, 'ladderX': 6601},
 {'x': 6900, 'y': 252, 'w': 330, 'ladderX': 7072},
 {'x': 7200, 'y': 162, 'w': 252, 'ladderX': 7220},
 {'x': 7510, 'y': 223, 'w': 295, 'ladderX': 7632},
 {'x': 7820, 'y': 288, 'w': 224, 'ladderX': 7923},
 {'x': 8030, 'y': 198, 'w': 244, 'ladderX': 8046},
 {'x': 8320, 'y': 285, 'w': 275, 'ladderX': 8471},
 {'x': 8570, 'y': 214, 'w': 253, 'ladderX': 8588},
 {'x': 8860, 'y': 271, 'w': 223, 'ladderX': 8977},
 {'x': 9120, 'y': 224, 'w': 309, 'ladderX': 9265},
 {'x': 9410, 'y': 147, 'w': 215, 'ladderX': 9426},
 {'x': 9705, 'y': 246, 'w': 291, 'ladderX': 9827},
 {'x': 10040, 'y': 197, 'w': 263, 'ladderX': 10177},
 {'x': 10400, 'y': 221, 'w': 249, 'ladderX': 10535},
 {'x': 10640, 'y': 138, 'w': 230, 'ladderX': 10656},
 {'x': 10970, 'y': 212, 'w': 298, 'ladderX': 11125},
 {'x': 11240, 'y': 152, 'w': 184, 'ladderX': 11258},
 {'x': 11510, 'y': 237, 'w': 280, 'ladderX': 11605},
 {'x': 12100, 'y': 262, 'w': 260, 'ladderX': 12214},
 {'x': 12330, 'y': 169, 'w': 290, 'ladderX': 12352},
 {'x': 12630, 'y': 280, 'w': 260, 'ladderX': 12726},
 {'x': 12890, 'y': 224, 'w': 280, 'ladderX': 12995},
 {'x': 13140, 'y': 138, 'w': 230, 'ladderX': 13160},
 {'x': 13410, 'y': 237, 'w': 275, 'ladderX': 13518},
 {'x': 13710, 'y': 294, 'w': 240, 'ladderX': 13820},
 {'x': 13950, 'y': 195, 'w': 260, 'ladderX': 14075},
 {'x': 14200, 'y': 274, 'w': 280, 'ladderX': 14302},
 {'x': 14450, 'y': 179, 'w': 250, 'ladderX': 14476},
 {'x': 14710, 'y': 245, 'w': 175, 'ladderX': 14785},
 {'x': 15020, 'y': 246, 'w': 250, 'ladderX': 15119},
 {'x': 15250, 'y': 154, 'w': 260, 'ladderX': 15266},
 {'x': 15550, 'y': 268, 'w': 270, 'ladderX': 15685},
 {'x': 15850, 'y': 208, 'w': 282, 'ladderX': 15982},
 {'x': 16110, 'y': 123, 'w': 260, 'ladderX': 16127},
 {'x': 16400, 'y': 238, 'w': 255, 'ladderX': 16522},
 {'x': 16650, 'y': 182, 'w': 265, 'ladderX': 16669},
 {'x': 16950, 'y': 275, 'w': 312, 'ladderX': 17066},
 {'x': 17250, 'y': 186, 'w': 240, 'ladderX': 17275},
 {'x': 17500, 'y': 252, 'w': 254, 'ladderX': 17619},
 {'x': 17800, 'y': 209, 'w': 340, 'ladderX': 17920}]

PROPS = [[195, 0, 175],
 [413, 2, 126, 248],
 [615, 2, 137],
 [830, 1, 210],
 [1070, 0, 145, 237],
 [1350, 2, 160],
 [1530, 1, 140, 191],
 [1935, 0, 165],
 [2200, 2, 170],
 [2370, 3, 79],
 [2580, 3, 105, 272],
 [2750, 2, 175],
 [2825, 3, 92, 184],
 [3190, 2, 133, 218],
 [3460, 3, 112],
 [3680, 2, 156],
 [3780, 3, 116, 235],
 [4050, 3, 102],
 [4325, 2, 157, 274],
 [4560, 3, 107],
 [4920, 3, 108, 286],
 [5175, 2, 164],
 [5270, 3, 99, 228],
 [5705, 3, 116],
 [5910, 2, 158, 200],
 [6180, 3, 109, 276],
 [6370, 2, 179],
 [6760, 3, 102, 124],
 [7050, 3, 117, 252],
 [7445, 2, 181],
 [7680, 3, 100, 223],
 [7990, 2, 162],
 [8170, 3, 114, 198],
 [8430, 2, 170],
 [8765, 3, 121, 214],
 [9000, 2, 145],
 [9300, 4, 154, 224],
 [9470, 4, 217],
 [9850, 2, 120],
 [10150, 4, 182],
 [10355, 3, 76],
 [10730, 5, 196],
 [11155, 4, 205],
 [11670, 5, 185],
 [12200, 3, 105, 262],
 [12439, 3, 108],
 [13000, 3, 105, 224],
 [13555, 3, 130],
 [14020, 3, 119, 195],
 [14630, 3, 122],
 [15140, 2, 134, 246],
 [15500, 3, 115],
 [16020, 2, 143, 208],
 [16520, 3, 104, 238],
 [17010, 2, 170],
 [17660, 3, 114, 252],
 [18140, 2, 184]]

LEDGES.extend(
    dict(x=x,y=y,w=w,ladderX=x+w//2)
    for x,y,w in ((18450,236,280),(18820,262,300),(19180,201,275),(19740,224,326),
                  (20200,191,240),(20570,265,320),(21030,227,270),(21540,240,270),
                  (22120,289,310),(22500,219,280),(23000,210,290),(23400,254,280),
                  (23900,251,320),(24330,199,255))
)
PROPS.extend((
    (18540,4,135),(18890,3,151),(19160,4,165),(19790,4,177),(20270,3,155),
    (20670,4,165),(21150,4,142),(21670,3,149),(22130,1,118),(22550,5,160),
    (23080,3,148),(23560,5,130),(23960,1,123),(24440,3,167),
))
LEDGES.extend(
    dict(x=x,y=y,w=w,ladderX=ladder)
    for x,y,w,ladder in (
        (3275,26,440,3450),(3620,-94,560,3680),(4010,-216,680,4135),
        (5270,72,415,5356),(5510,6,470,5580),(5740,-103,470,5840),(5960,-215,465,6100),
        (6370,-87,450,6495),(6640,-194,535,6740),(7070,-99,460,7170),
        (25170,254,320,25312),(25570,248,400,25772),(25770,144,420,25850),
        (25980,247,610,26205),(26260,122,810,26520),(26510,-4,680,26700),(26720,-132,510,27000),
        (27210,286,390,27400),(27530,185,540,27562),(27950,86,510,28006),
        (28430,228,490,28640),(28740,138,380,28852),
        (29690,237,400,29800),(29980,134,545,30056),(30290,30,475,30358),
        (30880,277,695,31120),(31260,153,670,31430),(31670,30,650,31825),(32030,-83,485,32155),
        (32410,268,540,32610),(32740,168,550,32800),(33150,83,525,33200),(33580,243,275,33715),
        (34290,245,450,34477),(34350,160,210,34458),(34760,243,540,34954),
        (35000,138,830,35125),(35380,24,805,35510),(35950,-95,457,36110),
        (36455,164,420,36610),(36585,56,285,36680),
        (37420,249,380,37560),(37760,152,560,37788),(38060,43,480,38200),
        (38460,255,635,38690),(38910,143,710,39020),(39390,27,600,39550),(39800,-104,660,39885),
        (40320,220,485,40550),(40560,110,300,40700),
    )
)
PROPS.extend(
    (x,frame,width,floor,"terrace_props")
    for x,frame,width,floor in (
        (34415,0,117,245),(34676,1,134,None),(34900,0,170,243),(35180,1,140,138),
        (35460,0,198,None),(35731,0,175,24),(36070,1,190,-95),(36447,0,145,None),
        (36715,1,150,164),(36923,0,145,None),
        (37509,1,150,249),(37730,3,347,None),(38018,2,233,152),(38300,1,148,43),
        (38705,2,274,None),(38937,3,415,None),(39142,2,220,143),(39570,1,205,27),
        (39994,2,200,-104),(40163,3,382,None),(40596,2,231,220),(40734,1,136,110),
    )
)
PROPS.extend(
    (x,frame,width,floor,"canopy_props")
    for x,frame,width,floor in (
        (3490,0,430,None),(3650,3,170,26),(3910,2,217,-94),(4450,3,251,-216),
        (5600,0,452,None),(5510,3,185,72),(5715,2,194,6),(6210,3,221,-215),
        (6610,3,199,-87),(6855,2,190,-194),(7330,3,167,-99),
        (25235,2,179,254),(25512,0,380,None),(25806,3,196,248),(26430,0,420,None),
        (26375,3,245,122),(26885,2,210,-132),(27255,0,425,None),(27690,3,214,185),
        (28095,2,180,86),(28555,0,369,None),(28940,3,205,138),
        (29793,1,250,None),(30101,3,226,134),(30441,1,168,30),(30696,0,387,None),
        (31095,1,290,277),(31517,2,227,153),(31841,1,247,30),(32175,3,220,-83),
        (32270,0,378,None),(32590,1,264,268),(32950,2,187,168),(33240,1,310,None),
        (33395,3,236,83),(33722,2,191,243),
    )
)

CLASSES = {'beginner': {'name': '모험가',
              'skill': '별빛 파동',
              'attack': 0,
              'hp': 0,
              'mp': 0,
              'cost': 8,
              'cooldown': 170,
              'reach': 110,
              'power': 1.6,
              'shape': 'ring'},
 'guardian': {'name': '수호검사',
              'skill': '가르기',
              'attack': 3,
              'hp': 32,
              'mp': 0,
              'cost': 10,
              'cooldown': 125,
              'reach': 104,
              'power': 2.3,
              'shape': 'arc'},
 'ranger': {'name': '숲길잡이',
            'skill': '바람 화살',
            'attack': 2,
            'hp': 8,
            'mp': 10,
            'cost': 9,
            'cooldown': 105,
            'reach': 340,
            'power': 2.05,
            'shape': 'arrow'},
 'mage': {'name': '별빛술사',
          'skill': '별비',
          'attack': 1,
          'hp': 0,
          'mp': 32,
          'cost': 16,
          'cooldown': 155,
          'reach': 188,
          'power': 2.35,
          'shape': 'stars'}}

CLASSES.update({
    "thief": dict(name="그림자 척후병", skill="쌍섬", shape="stab", attack=3, hp=12, mp=8, cost=8, cooldown=65, reach=79, power=1.15),
    "pirate": dict(name="파도 격투가", skill="파도 돌려차기", shape="kick", attack=3, hp=24, mp=4, cost=12, cooldown=86, reach=85, power=2.1),
    "cleric": dict(name="새벽 치유사", skill="새벽의 종", shape="heal", attack=1, hp=6, mp=34, cost=14, cooldown=98, reach=168, power=1.9),
})
CLASSES["guardian"]["skill"] = "반달 베기"
CLASSES["mage"]["skill"] = "별벼락"
CLASSES["ranger"]["skill"] = "폭뢰 화살"

ATTRIBUTES = {'strength': {'name': '힘', 'detail': '공격력 +2', 'icon': '◆', 'attack': 2},
 'vitality': {'name': '체력', 'detail': '최대 HP +8 · 방어력 +1', 'icon': '♥', 'hp': 8, 'defense': 1},
 'spirit': {'name': '정신', 'detail': '최대 MP +5', 'icon': '✦', 'mp': 5},
 'agility': {'name': '민첩', 'detail': '이동 속도 +0.09', 'icon': '➟', 'speed': 0.09}}

SUPPORTS = {
    "guardian": dict(name="가시 방벽", summary="받은 접촉 피해 일부를 몬스터에게 돌려줘요.", stat="reflect", power=.35, cost=12),
    "ranger": dict(name="바람걸음", summary="이동 속도와 점프력이 증가해요.", stat="speed", power=1.25, cost=12),
    "mage": dict(name="마력 장막", summary="피해 일부를 MP로 대신 받아요.", stat="guard", power=.6, cost=15),
    "thief": dict(name="연막 잠행", summary="공격하기 전까지 몬스터 접촉을 피해요.", stat="stealth", power=1, cost=10),
    "pirate": dict(name="물결 질주", summary="이동 속도와 점프력이 증가해요.", stat="speed", power=1.7, cost=10),
    "cleric": dict(name="새벽의 축복", summary="공격력과 방어력이 증가해요.", stat="bless", power=6, cost=14),
}

HOTKEYS = ['Digit1', 'Digit2', 'Digit3', 'Digit4']

DEFAULT_HOTBAR = ['hp', 'mp', 'skill', 'support']

HOTBAR_ACTIONS = {'hp': {'name': '체력 물약', 'icon': '♥', 'color': 'rose'},
 'mp': {'name': '마력 물약', 'icon': '◆', 'color': 'sky'},
 'skill': {'name': '직업 스킬', 'icon': '✦', 'color': 'violet'},
 'support': {'name': '보조 스킬', 'icon': '⬡', 'color': 'mint'},
 'home': {'name': '마을 귀환', 'icon': '⌂', 'color': 'gold'}}

ITEMS = {'twig': {'name': '마른가지 검', 'slot': 'weapon', 'level': 1, 'attack': 2, 'price': 25, 'icon': 0},
 'bronze': {'name': '등대 청동검', 'slot': 'weapon', 'level': 2, 'attack': 5, 'price': 78, 'icon': 16},
 'coat': {'name': '갈색 하드래더', 'slot': 'armor', 'level': 2, 'defense': 2, 'hp': 12, 'price': 65, 'icon': 14},
 'cap': {'name': '갈색 삿갓', 'slot': 'head', 'level': 3, 'defense': 4, 'hp': 20, 'price': 110, 'icon': 28},
 'dew': {'name': '반짝이는 반지', 'slot': 'ring', 'level': 3, 'hp': 18, 'mp': 10, 'price': 96, 'icon': 24},
 'blade': {'name': '푸른결 곡검',
           'slot': 'weapon',
           'level': 5,
           'job': 'guardian',
           'attack': 12,
           'price': 245,
           'icon': 17},
 'bow': {'name': '솔가지 활', 'slot': 'weapon', 'level': 5, 'job': 'ranger', 'attack': 11, 'price': 245, 'icon': 1},
 'wand': {'name': '별나무 완드',
          'slot': 'weapon',
          'level': 5,
          'job': 'mage',
          'attack': 11,
          'mp': 12,
          'price': 245,
          'icon': 2},
 'shell': {'name': '스틸 코퍼럴', 'slot': 'armor', 'level': 7, 'defense': 8, 'hp': 36, 'price': 390, 'icon': 21},
 'prism': {'name': '혼테일의 목걸이',
           'slot': 'charm',
           'level': 8,
           'attack': 3,
           'hp': 24,
           'mp': 24,
           'price': 420,
           'icon': 26},
 'jelly': {'name': '풀빛 젤리', 'price': 15},
 'spores': {'name': '호박 버섯 포자', 'price': 24},
 'ash': {'name': '안개 가루', 'price': 39},
 'coral': {'name': '바람 산호', 'price': 56},
 'potion': {'name': '체력 물약', 'price': 28},
 'tonic': {'name': '마력 물약', 'price': 32},
 'quartz': {'name': '별철 원석', 'price': 68, 'icon': 12, 'rarity': 'uncommon'},
 'plume': {'name': '달바람 깃털', 'price': 85, 'icon': 15, 'rarity': 'uncommon'},
 'anchor': {'name': '수문장의 닻 파편', 'price': 120, 'icon': 13, 'rarity': 'rare'},
 'nightcore': {'name': '달철 심장', 'price': 220, 'icon': 13, 'rarity': 'epic'},
 'glasscoat': {'name': '블루 이너스 체인메일',
               'slot': 'armor',
               'level': 10,
               'defense': 12,
               'hp': 54,
               'price': 620,
               'icon': 22,
               'rarity': 'rare'},
 'moonseal': {'name': '성실한 모험가의 훈장',
              'slot': 'seal',
              'level': 12,
              'attack': 8,
              'hp': 36,
              'mp': 42,
              'price': 830,
              'icon': 25,
              'rarity': 'epic'},
 'sunblade': {'name': '노을 장검',
              'slot': 'weapon',
              'level': 11,
              'job': 'guardian',
              'attack': 29,
              'hp': 26,
              'price': 920,
              'icon': 18,
              'rarity': 'epic'},
 'nightbow': {'name': '초승달 활',
              'slot': 'weapon',
              'level': 11,
              'job': 'ranger',
              'attack': 27,
              'mp': 22,
              'price': 920,
              'icon': 19,
              'rarity': 'epic'},
 'tidewand': {'name': '얼음결 완드',
              'slot': 'weapon',
              'level': 11,
              'job': 'mage',
              'attack': 27,
              'mp': 34,
              'price': 920,
              'icon': 20,
              'rarity': 'epic'},
 'crabguard': {'name': '레드 이너스 체인메일',
               'slot': 'armor',
               'level': 8,
               'defense': 9,
               'hp': 43,
               'price': 515,
               'icon': 23,
               'rarity': 'rare'},
 'shimmer': {'name': '슈피겔만의 목걸이',
             'slot': 'charm',
             'level': 9,
             'hp': 27,
             'mp': 30,
             'price': 555,
             'icon': 27,
             'rarity': 'rare'}}

for icon, (key, name, slot, level, price, bonus, job) in enumerate(EXPANSION_EQUIPMENT, 32):
    item = {"name":name, "slot":slot, "level":level, "price":price, "icon":icon}
    item["attack" if slot=="weapon" else "defense"] = bonus
    if slot!="weapon":
        item["hp"] = 3*level
    if job:
        item["job"] = job
    ITEMS[key] = item

SLOTS = {'head': '모자', 'armor': '방어구', 'weapon': '무기', 'ring': '반지', 'charm': '목걸이', 'seal': '훈장'}

SPECIES = [{'name': '슬라임',
  'level': 1,
  'sprite': 0,
  'hp': 15,
  'attack': 8,
  'xp': 17,
  'gold': 14,
  'speed': 0.7,
  'loot': 'jelly',
  'rare': 'bronze'},
 {'name': '주황버섯',
  'level': 3,
  'sprite': 1,
  'hp': 34,
  'attack': 13,
  'xp': 32,
  'gold': 23,
  'speed': 0.8,
  'loot': 'spores',
  'rare': 'cap'},
 {'name': '빨간 달팽이',
  'level': 5,
  'sprite': 2,
  'hp': 57,
  'attack': 19,
  'xp': 52,
  'gold': 35,
  'speed': 1,
  'loot': 'ash',
  'rare': 'dew'},
 {'name': '리본 돼지',
  'level': 7,
  'sprite': 3,
  'hp': 84,
  'attack': 25,
  'xp': 75,
  'gold': 50,
  'speed': 1.05,
  'loot': 'coral',
  'rare': 'shell'},
 {'name': '킹크랑',
  'level': 9,
  'sprite': 4,
  'hp': 190,
  'attack': 34,
  'xp': 190,
  'gold': 140,
  'speed': 1.2,
  'loot': 'anchor',
  'rare': 'prism',
  'elite': True,
  'aggro': 105},
 {'name': '로랑',
  'level': 8,
  'sprite': 5,
  'hp': 95,
  'attack': 24,
  'xp': 83,
  'gold': 54,
  'speed': 1.25,
  'loot': 'coral',
  'rare': 'crabguard',
  'aggro': 110},
 {'name': '버블링',
  'level': 9,
  'sprite': 6,
  'hp': 119,
  'attack': 28,
  'xp': 103,
  'gold': 67,
  'speed': 1,
  'loot': 'quartz',
  'rare': 'glasscoat',
  'aggro': 90},
 {'name': '스톤골렘',
  'level': 11,
  'sprite': 7,
  'hp': 175,
  'attack': 35,
  'xp': 142,
  'gold': 81,
  'speed': 1.05,
  'loot': 'quartz',
  'rare': 'glasscoat',
  'aggro': 144},
 {'name': '스타픽시',
  'level': 12,
  'sprite': 8,
  'hp': 204,
  'attack': 39,
  'xp': 171,
  'gold': 93,
  'speed': 1.35,
  'float': True,
  'hover': 24,
  'loot': 'plume',
  'rare': 'shimmer',
  'aggro': 143},
 {'name': '클랑',
  'level': 13,
  'sprite': 9,
  'hp': 231,
  'attack': 43,
  'xp': 196,
  'gold': 104,
  'speed': 1.5,
  'loot': 'plume',
  'rare': 'moonseal',
  'aggro': 147},
 {'name': '머쉬맘',
  'level': 15,
  'sprite': 10,
  'hp': 655,
  'attack': 55,
  'xp': 680,
  'gold': 390,
  'speed': 1.28,
  'loot': 'nightcore',
  'rare': 'moonseal',
  'elite': True,
  'aggro': 193}]

for _species in SPECIES:
    _source, _species["body_size"], _species["framebooks"] = MOB_BOOKS[_species["sprite"]]


# Higher-level field variants share the existing classic animation books.
# Keep species indices stable for earlier quest and bestiary saves.
for base, name, level, hp, attack, xp, gold, rare, drops in (
    (6, "잿숲 버블링", 16, 396, 49, 144, 96, "shadowdagger", ("shadowdagger","hwarang")),
    (9, "안개등 클랑", 18, 428, 51, 162, 108, "stormknuckle", ("stormknuckle","dawnwand")),
    (7, "거목 스톤골렘", 18, 425, 55, 232, 115, "glasscoat", ("glasscoat","stormknuckle")),
    (8, "수관 스타픽시", 19, 460, 57, 250, 124, "nightbow", ("nightbow","dawnwand")),
    (6, "구리 버블링", 18, 388, 50, 217, 104, "prism", ("chimewand","glasscoat")),
    (7, "구리 스톤골렘", 20, 515, 59, 275, 133, "stormknuckle", ("stormknuckle","hwarang")),
    (8, "씨앗숲 스타픽시", 21, 620, 63, 322, 151, "shimmer", ("dawnwand","glasscoat")),
    (10, "씨앗숲 머쉬맘", 23, 1480, 77, 1080, 460, "moonseal", ("moonseal","hwarang","dawnwand")),
):
    SPECIES.append(dict(SPECIES[base], name=name, level=level, hp=hp, attack=attack, xp=xp, gold=gold,
                        rare=rare, equipmentDrops=drops))
SPECIES[11].update(undead=True, loot="spores")
SPECIES[12].update(undead=True, loot="ash")
for _species in SPECIES:
    _species["scale"] = 2 if _species["sprite"] == 7 else 1.5 if _species.get("elite") else 1


def monster_art(species, action, ticks=0, fraction=None):
    """Look up a packed frame at native timing, or at a combat phase."""
    first, ends = species["framebooks"][action]
    position = ticks % ends[-1] if fraction is None else max(0, min(ends[-1]-1, int(fraction*ends[-1])))
    frame = first + bisect_right(ends, position)
    return MOB_FRAMES[frame]


for species, pool in zip(SPECIES, (
    ("redcap","blazer"), ("bandana","baseball"), ("greenhood","apprenticehat"),
    ("blackthief","dagger"), ("archertop","knuckle"), ("sergeant","steelhelm"),
    ("wizardhat","orangethief"), ("steelhelm","stormknuckle"), ("vikinghelm","hwarang"),
    ("hwarang","shadowdagger"), ("shadowdagger","stormknuckle"),
)):
    species["equipmentDrops"] = pool

NPCS = [{'x': 475, 'name': '리나', 'role': '의뢰', 'kind': 'quest'},
 {'x': 870, 'name': '샘', 'role': '보급품', 'kind': 'shop', 'stock': ['potion', 'tonic', 'bronze', 'coat', 'dew', 'redcap', 'bandana', 'blazer', 'baseball', 'apprenticehat', 'greenhood', 'frostspear']},
 {'x': 1430, 'name': '헬레나', 'role': '전직', 'kind': 'trainer'},
 {'x': 2230, 'name': '쿤', 'role': '숲길 안내', 'kind': 'guide'},
 {'x': 5710, 'name': '마야', 'role': '숲길 의뢰', 'kind': 'quest', 'quest': 2},
 {'x': 9660,
  'name': '나타샤',
  'role': '항구 장비점',
  'kind': 'shop',
  'stock': ['potion', 'tonic', 'blade', 'bow', 'wand', 'shell', 'prism', 'dagger', 'knuckle', 'chimewand', 'archertop', 'sergeant', 'steelhelm', 'blackthief']},
 {'x': 10670, 'name': '리더 알', 'role': '의뢰', 'kind': 'harbor'},
 {'x': 12170, 'name': '스미스', 'role': '대장간', 'kind': 'forge'},
 {'x': 12425, 'name': '윈스턴', 'role': '광산 의뢰', 'kind': 'quest', 'quest': 3},
 {'x': 13370, 'name': '이얀', 'role': '광산 조사', 'kind': 'quest', 'quest': 4},
 {'x': 15095, 'name': '요정 아르웬', 'role': '고원 의뢰', 'kind': 'quest', 'quest': 5},
 {'x': 15320,
  'name': '해리',
  'role': '고원 보급품',
  'kind': 'shop',
  'stock': ['potion', 'tonic', 'crabguard', 'glasscoat', 'shimmer', 'shadowdagger', 'stormknuckle', 'dawnwand', 'wizardhat', 'vikinghelm', 'orangethief', 'hwarang']},
 {'x': 16645, 'name': '만지', 'role': '머쉬맘 의뢰', 'kind': 'quest', 'quest': 6}]

QUESTS = [{'name': '숲길 청소',
  'who': '리나',
  'area': 0,
  'target': 8,
  'matches': [0, 1],
  'xp': 85,
  'gold': 95,
  'item': 'coat',
  'detail': '숲길의 슬라임과 주황버섯을 처치하세요.'},
 {'name': '항구의 불빛',
  'who': '리더 알',
  'area': 2,
  'target': 1,
  'matches': [4],
  'xp': 220,
  'gold': 190,
  'item': 'prism',
  'detail': '항구 끝에 있는 킹크랑을 처치하세요.'},
 {'name': '종꽃길의 달팽이',
  'who': '마야',
  'area': 1,
  'target': 5,
  'matches': [2],
  'xp': 155,
  'gold': 120,
  'item': 'dew',
  'detail': '숲길 깊은 곳에서 빨간 달팽이를 처치하세요.'},
 {'name': '유리맥 안전 점검',
  'who': '윈스턴',
  'area': 3,
  'target': 8,
  'matches': [6, 7],
  'xp': 350,
  'gold': 240,
  'item': 'glasscoat',
  'detail': '광산의 버블링과 스톤골렘을 처치하세요.'},
 {'name': '광산의 푸른 집게',
  'who': '이얀',
  'area': 3,
  'target': 5,
  'matches': [5],
  'xp': 240,
  'gold': 165,
  'item': 'crabguard',
  'detail': '광산 입구와 항구에서 로랑을 처치하세요.'},
 {'name': '달바람 관측',
  'who': '요정 아르웬',
  'area': 4,
  'target': 9,
  'matches': [8, 9],
  'xp': 500,
  'gold': 330,
  'item': 'shimmer',
  'detail': '고원의 스타픽시와 클랑을 처치하세요.'},
 {'name': '고원의 거대 버섯',
  'who': '만지',
  'area': 4,
  'target': 1,
  'matches': [10],
  'xp': 720,
  'gold': 450,
  'item': 'moonseal',
  'detail': '고원 끝의 머쉬맘을 쓰러뜨리세요.'}]

RECIPES = [{'item': 'crabguard', 'ingredients': {'coral': 4}, 'gold': 105},
 {'item': 'glasscoat', 'ingredients': {'quartz': 5, 'coral': 2}, 'gold': 180},
 {'item': 'shimmer', 'ingredients': {'ash': 4, 'quartz': 2}, 'gold': 160},
 {'item': 'sunblade', 'ingredients': {'quartz': 8, 'anchor': 1}, 'gold': 325},
 {'item': 'nightbow', 'ingredients': {'quartz': 8, 'anchor': 1}, 'gold': 325},
 {'item': 'tidewand', 'ingredients': {'quartz': 8, 'anchor': 1}, 'gold': 325},
 {'item': 'moonseal', 'ingredients': {'plume': 6, 'nightcore': 1}, 'gold': 390}]

ITEM_ICONS = {'twig': 0,
 'bronze': 16,
 'blade': 17,
 'bow': 1,
 'wand': 2,
 'coat': 14,
 'cap': 28,
 'dew': 24,
 'shell': 21,
 'prism': 26,
 'jelly': 8,
 'spores': 9,
 'ash': 10,
 'coral': 11,
 'potion': 4,
 'tonic': 5,
 'sunblade': 18,
 'nightbow': 19,
 'tidewand': 20,
 'glasscoat': 22,
 'crabguard': 23,
 'moonseal': 25,
 'shimmer': 27}

SPRITES = {'hero': {'file': 'hero-adventurer.png',
          'columns': 4,
          'rows': 7,
          'frameWidth': 80,
          'frameHeight': 80,
          'anchor': [38, 75],
          'animations': {'idle': {'frames': [0, 1, 2, 1, 0, 1, 2, 1, 3, 1],
                                  'durations': [500, 500, 500, 500, 500, 500, 500, 390, 65, 45], 'loop': True},
                         'walk': {'frames': [4, 5, 6, 7], 'durations': [180, 180, 180, 180], 'loop': True},
                         'attack': {'frames': [8, 9, 10, 11], 'ticks': [4, 4, 6, 10], 'loop': False},
                         'bow': {'frames': [16, 17, 18, 19], 'loop': False},
                         'cast': {'frames': [20, 21, 22, 23], 'loop': False},
                         'climb': {'frames': [24, 25, 26, 27], 'loop': True},
                         'jumpUp': {'frames': [12], 'durations': [100], 'loop': True},
                         'jumpDown': {'frames': [13], 'durations': [100], 'loop': True},
                         'hurt': {'frames': [14], 'durations': [160], 'loop': False}}},
 'villager': {'columns': 12, 'rows': 13, 'frameWidth': 96, 'frameHeight': 96, 'anchor': [48, 92]},
 'props': [[0, 0, 126, 122],
           [128, 0, 126, 118],
           [256, 0, 126, 117],
           [0, 160, 126, 138],
           [128, 160, 126, 114],
           [256, 160, 108, 155]]}
SPRITES["canopy_props"] = [(0,0,224,352),(224,0,172,128),(396,0,172,224),(568,0,224,146)]
SPRITES["terrace_props"] = [(0,0,150,110),(150,0,148,151),(298,0,182,167),(480,0,214,255)]

# GMS v83 NPC display height and original idle frame durations in milliseconds.
NPC_IDLE = (
    (67, (150, 100, 1200) * 3), (61, (1200,)), (71, (1200,)),
    (85, (2000, 200, 200, 200, 500, 200)), (77, (1200,)), (76, (1200,)),
    (86, (180,) * 8), (69, (1200,)), (72, (1000, 700, 100, 100, 700, 100)),
    (74, (1000, 100, 100, 100, 100, 100, 800, 100, 100, 800, 100, 100)),
    (57, (1200,)), (79, (1200, 100, 150)), (79, (1200,)),
)
# One weapon cel per simulation tick. Body and damage use the same timeline.
MELEE_ANIMATION = SPRITES["hero"]["animations"]["attack"]
MELEE_POSES = tuple(pose for pose, ticks in zip(MELEE_ANIMATION["frames"], MELEE_ANIMATION["ticks"])
                    for _ in range(ticks))
MELEE_IMPACT = MELEE_POSES.index(10)
WEAPON_ATTACKS = {"bow": "arrow", "nightbow": "arrow", "wand": "bolt", "tidewand": "bolt", "chimewand": "bolt", "dawnwand": "bolt"}

IMAGES = {'classic_ui': 'classic-ui.png', 'damage': 'damage.png', 'swing_weapons': 'swing-weapons.png', 'worn': 'worn-equipment.png', 'combat': 'combat-fx.png', 'interface': 'interface.png', 'hero': SPRITES['hero']['file'], 'villager': 'townsfolk.png', 'wildlife': 'wildlife.png', 'terrain': 'terrain.png', 'stone': 'stone.png', 'props': 'scenery.png', 'icons': 'equipment.png', 'frame': 'pixel-frame.png'}
JOB_LOOKS = {job: "hero_" + job for job in ("guardian", "ranger", "mage")}
IMAGES.update({key: "hero-" + job + ".png" for job, key in JOB_LOOKS.items()})

IMAGES.update(expansion_worn="expansion-worn.png", expansion_swing="expansion-swing.png", expansion_icons="expansion-icons.png")
IMAGES["adventure_ui"] = "adventure-ui.png"
IMAGES.update(ember_grove="ember-grove-tall.png", lantern_quay="lantern-quay-tall.png",
              daylight="daylight-panorama-tall.png", cavern="cavern-panorama-tall.png",
              highland="highland-panorama-tall.png", ladder="ladder.png")
IMAGES["bellflower"] = "bellflower-forest.png"
IMAGES.update(windroot="windroot.png", sunegg="sunegg.png", canopy_props="canopy-scenery.png")
IMAGES.update(copper_ground="copper-ground.png", seed_ground="seed-ground.png", terrace_sky="terrace-sky.png",
              seed_sky="seed-sky.png", seed_canopy="seed-canopy.png", terrace_props="terrace-props.png",
              terrain="grass-cliff.png", quarry_ground="quarry-ground.png", quarry_props="quarry-scenery.png")
SPRITES["quarry_props"] = [(0,0,144,196),(144,0,164,192),(308,0,204,147)]
PROPS.extend((x, art, width, None, "quarry_props") for x, art, width in (
    (12680,0,154),(12840,1,194),(13175,2,179),(13670,0,169),(14130,1,191),(14595,2,189),
))

AVATAR_JOBS = ("beginner","guardian","ranger","mage","thief","pirate","cleric")
STARTER_WEAPONS = {"beginner":"twig","guardian":"blade","ranger":"bow","mage":"wand",
                   "thief":"dagger","pirate":"knuckle","cleric":"chimewand"}
for _starter in STARTER_WEAPONS.values():
    ITEMS[_starter]["level"] = 1


# Each row pairs one species with a portal in the nearby main route.
HUNT_FIELD_DATA = (
    ("slime-clearing", "슬라임 초지", 0, 700, 1520, "meadow"),
    ("orange-mushroom-rise", "주황버섯 비탈", 1, 3090, 1600, "meadow"),
    ("red-snail-path", "빨간 달팽이 고갯길", 1, 4320, 1530, "meadow"),
    ("ribbon-pig-pen", "리본 돼지 목책길", 2, 9430, 1540, "coast"),
    ("king-crab-cove", "킹크랑 암초굴", 2, 10480, 1660, "coast"),
    ("crab-shoal", "로랑 여울", 2, 9860, 1580, "coast"),
    ("bubbling-niche", "버블링 수정굴", 3, 12300, 1610, "mine"),
    ("stone-golem-works", "스톤골렘 채석장", 3, 13220, 1800, "mine"),
    ("star-pixie-terrace", "스타픽시 별마루", 4, 15460, 1620, "canopy"),
    ("clang-ridge", "클랑 바위능선", 4, 16180, 1590, "meadow"),
    ("mushmom-den", "머쉬맘 둥지", 4, 17500, 1690, "canopy"),
    ("ash-bubble-copse", "잿숲 버블링 수풀", 5, 18600, 1550, "meadow"),
    ("quay-clang-wharf", "안개등 클랑 갯길", 6, 21880, 1640, "coast"),
    ("root-golem-hollow", "거목 스톤골렘 뿌리굴", 7, 25030, 1770, "mine"),
    ("canopy-pixie-grove", "수관 스타픽시 나뭇길", 7, 26210, 1690, "canopy"),
    ("copper-bubble-drift", "구리 버블링 갱도", 9, 34350, 1630, "mine"),
    ("copper-golem-cut", "구리 스톤골렘 절벽", 9, 35440, 1810, "mine"),
    ("forest-pixie-stairs", "씨앗숲 스타픽시 계단", 10, 37390, 1680, "canopy"),
    ("forest-mushmom-nest", "씨앗숲 머쉬맘 둥지", 10, 39840, 1760, "canopy"),
)

# Fractions along each field reuse the current terrain, props and ladder art.
FIELD_LAYOUTS = {
    "meadow": (
        ((.1,381),(.23,353),(.43,353),(.6,393),(.73,393),(.86,354),(.94,354)),
        ((.19,.45,249,.31),(.37,.66,143,.42),(.7,.92,224,.81)), "props", (0,2,3)),
    "mine": (
        ((.11,386),(.3,388),(.47,347),(.62,347),(.76,392),(.91,371)),
        ((.18,.52,261,.31),(.39,.69,142,.46),(.61,.91,234,.75)), "quarry_props", (0,1,2)),
    "coast": (
        ((.13,370),(.28,380),(.49,380),(.63,343),(.8,343),(.93,383)),
        ((.21,.49,255,.33),(.55,.84,243,.7),(.7,.93,127,.77)), "props", (4,5,1)),
    "canopy": (
        ((.12,387),(.29,357),(.42,357),(.57,394),(.74,394),(.92,363)),
        ((.18,.52,254,.32),(.37,.74,145,.47),(.62,.91,39,.67)), "terrace_props", (3,1,2)),
}

HUNT_FIELDS = []
_field_start = BASE_WORLD_WIDTH
for _kind, (_map_id, _name, _parent, _gate, _width, _style) in enumerate(HUNT_FIELD_DATA):
    _end = _field_start + _width
    _area = dict(AREAS[_parent], name=_name, start=_field_start, end=_end, hunt_kind=_kind,
                 hunt_parent=_parent, view=(AREAS[_parent]["view"] + 270 + 153*(_kind % 3)))
    if _style == "mine":
        _area.update(material="quarry_ground", image="cavern", terrain_tint="#33405a60")
    MAP_IDS.append(_map_id)
    HUNT_FIELDS.append(dict(kind=_kind, region=len(AREAS), start=_field_start, width=_width, gate=_gate, parent=_parent,
                            ledges=[]))
    AREAS.append(_area)
    _ground, _ledges, _atlas, _objects = FIELD_LAYOUTS[_style]
    GROUND.extend((_field_start + round(_width*fraction), y) for fraction, y in _ground)
    GROUND.append((_end, 382))
    for _index, (_left, _right, _y, _ladder) in enumerate(_ledges):
        _x = _field_start + round(_width*_left)
        LEDGES.append(dict(x=_x, y=_y, w=_field_start + round(_width*_right) - _x,
                           ladderX=_field_start + round(_width*_ladder)))
        HUNT_FIELDS[-1]["ledges"].append(_x)
        _prop_x = _x + round(_width*(_right-_left)*.31)
        PROPS.append((_prop_x, _objects[_index], 124+_index*12, _y, _atlas))
    for _fraction, _slot in ((.16,0),(.55,1),(.94,2)):
        PROPS.append((_field_start + round(_width*_fraction), _objects[_slot], 152+_slot*16, None, _atlas))
    _field_start = _end

WORLD_WIDTH = map_x(_field_start)
for _area in AREAS:
    _area.update(start=map_x(_area["start"]),end=map_x(_area["end"]))
GROUND = [(map_x(x),y) for x,y in GROUND]
for _ledge in LEDGES:
    _start = map_x(_ledge["x"])
    _ledge.update(x=_start, w=map_x(_ledge["x"]+_ledge["w"])-_start, ladderX=map_x(_ledge["ladderX"]))
PROPS = [(map_x(prop[0]), *prop[1:]) for prop in PROPS]
for _npc in NPCS:
    _npc["x"] = map_x(_npc["x"])
