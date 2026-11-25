"""Hand-placed hunting routes. Platform positions refer to the ledge's left edge."""

from .content import HUNT_FIELDS, SPECIES, map_x

SLIME, MUSHROOM, SNAIL, PIG, KING_CRAB, CRAB, BUBBLE, GOLEM, PIXIE, CLANG, MUSHMOM, ASH_BUBBLE, QUAY_CLANG = range(13)
ROOT_GOLEM, CANOPY_PIXIE = range(13, 15)
COPPER_BUBBLE, COPPER_GOLEM, FOREST_PIXIE, FOREST_MUSHMOM = range(15, 19)


def hunting_spot(label, ground=(), ledges=()):
    return {"label":label, "ground":tuple((map_x(x),kind) for x,kind in ground),
            "ledges":tuple((map_x(x),kind) for x,kind in ledges),
            "spawn_ids":(tuple(f"floor-{x}" for x, _ in ground), tuple(f"ledge-{x}" for x, _ in ledges))}


def hunting_zone(label, levels, wave, recovery, spots, boss_waves=0):
    # Timings are simulation ticks. Recovery prevents an immediate return when
    # a kill lands just before the next wave.
    species = sorted({kind for spot in spots for lane in ("ground", "ledges")
                      for _, kind in spot[lane]})
    return dict(label=label, levels=levels, wave=wave, recovery=recovery,
                boss_waves=boss_waves, species=tuple(species), spots=spots)


HUNT_ZONES = (
    hunting_zone("솔방울 연습터", (1, 1), 240, 120, (
        hunting_spot("마을 뒤뜰",
                     ground=((1765, SLIME), (1945, SLIME)),
                     ledges=((1850, SLIME),)),
    )),
    hunting_zone("세 갈래 꽃길", (1, 5), 250, 150, (
        hunting_spot("새싹 비탈",
                     ground=((2800, SLIME), (2920, SLIME), (3270, SLIME), (3450, MUSHROOM)),
                     ledges=((2685, SLIME), (3060, SLIME), (3320, MUSHROOM))),
        hunting_spot("버섯 공터",
                     ground=((3930, SLIME), (4130, MUSHROOM), (4510, MUSHROOM),
                             (4700, MUSHROOM), (5120, MUSHROOM), (5350, MUSHROOM)),
                     ledges=((3890, MUSHROOM), (4480, MUSHROOM), (4810, SLIME), (5380, MUSHROOM))),
        hunting_spot("종꽃 언덕",
                     ground=((6150, MUSHROOM), (6390, SNAIL), (6615, SNAIL), (7035, SNAIL),
                             (7360, MUSHROOM), (7825, SNAIL), (8040, SNAIL), (8510, SNAIL)),
                     ledges=((6050, MUSHROOM), (6580, SNAIL), (7200, MUSHROOM),
                             (7820, SNAIL), (8320, SNAIL), (8570, SNAIL))),
        hunting_spot("쌍가지 수관길",
                     ledges=((3275,SLIME),(3620,MUSHROOM),(4010,MUSHROOM),(5270,SLIME),
                             (5510,MUSHROOM),(5740,MUSHROOM),(5960,SNAIL),(6370,MUSHROOM),
                             (6640,SNAIL),(7070,MUSHROOM))),
    )),
    hunting_zone("방파제 암초밭", (7, 9), 290, 165, (
        hunting_spot("창고 뒤뜰",
                     ground=((10050, PIG), (10280, PIG)), ledges=((10040, PIG),)),
        hunting_spot("소금물 웅덩이",
                     ground=((10980, CRAB), (11200, PIG), (11410, CRAB)),
                     ledges=((10970, CRAB), (11240, PIG))),
        hunting_spot("등대 아래 암초", ground=((11590, KING_CRAB),)),
    ), boss_waves=4),
    hunting_zone("수정맥 갱도", (8, 11), 270, 180, (
        hunting_spot("배수로",
                     ground=((12670, CRAB), (12870, BUBBLE), (13090, CRAB)),
                     ledges=((12630, BUBBLE), (12890, CRAB))),
        hunting_spot("유리맥 채굴장",
                     ground=((13620, BUBBLE), (13835, GOLEM), (14040, BUBBLE),
                             (14270, BUBBLE), (14550, GOLEM)),
                     ledges=((13410, BUBBLE), (13710, GOLEM), (14200, GOLEM), (14450, BUBBLE))),
    )),
    hunting_zone("달바람 능선", (12, 15), 265, 190, (
        hunting_spot("별가루 바위",
                     ground=((15610, CLANG), (15820, PIXIE), (16040, CLANG), (16305, PIXIE)),
                     ledges=((15550, PIXIE), (15850, CLANG), (16110, PIXIE))),
        hunting_spot("바람마루",
                     ground=((16920, CLANG), (17150, CLANG), (17390, PIXIE), (17630, CLANG)),
                     ledges=((16950, PIXIE), (17250, PIXIE), (17500, CLANG))),
        hunting_spot("달그늘 둥지", ground=((17900, MUSHMOM),)),
    ), boss_waves=6),
    hunting_zone("잿불 뿌리터", (12, 16), 245, 195, (
        hunting_spot("그을린 나무길",
                     ground=((18710, ASH_BUBBLE), (18920, ASH_BUBBLE), (19180, PIXIE)),
                     ledges=((18820, PIXIE), (19180, ASH_BUBBLE))),
        hunting_spot("재 묻은 뿌리",
                     ground=((19580, ASH_BUBBLE), (19770, ASH_BUBBLE), (20000, PIXIE), (20230, ASH_BUBBLE)),
                     ledges=((19740, ASH_BUBBLE), (20200, PIXIE))),
        hunting_spot("꺼진 등불터",
                     ground=((20600, ASH_BUBBLE), (20775, ASH_BUBBLE), (20985, ASH_BUBBLE)), ledges=((20570, ASH_BUBBLE),)),
    )),
    hunting_zone("안개등 잔교", (13, 18), 225, 205, (
        hunting_spot("밀물 계단",
                     ground=((21760, CLANG), (22005, QUAY_CLANG), (22240, CLANG)),
                     ledges=((22120, QUAY_CLANG),)),
        hunting_spot("침수된 선착장",
                     ground=((22640, QUAY_CLANG), (22840, QUAY_CLANG), (23030, CLANG), (23250, QUAY_CLANG)),
                     ledges=((22500, QUAY_CLANG), (23000, QUAY_CLANG), (23400, CLANG))),
        hunting_spot("마지막 계류장",
                     ground=((23750, QUAY_CLANG), (23950, QUAY_CLANG), (24160, QUAY_CLANG), (24360, CLANG)),
                     ledges=((23900, QUAY_CLANG), (24330, QUAY_CLANG))),
    )),
    hunting_zone("거목의 뿌리와 수관", (18, 19), 260, 205, (
        hunting_spot("등불 뿌리밭",
                     ground=((25230,ROOT_GOLEM),(25472,ROOT_GOLEM),(25700,ROOT_GOLEM),(25921,CANOPY_PIXIE)),
                     ledges=((25170,ROOT_GOLEM),(25570,ROOT_GOLEM),(25770,CANOPY_PIXIE))),
        hunting_spot("구름까지 닿는 거목",
                     ground=((26340,ROOT_GOLEM),(26640,CANOPY_PIXIE),(26910,ROOT_GOLEM)),
                     ledges=((25980,ROOT_GOLEM),(26260,CANOPY_PIXIE),(26510,ROOT_GOLEM),(26720,CANOPY_PIXIE))),
        hunting_spot("덩굴 공중길",
                     ground=((27390,ROOT_GOLEM),(27720,CANOPY_PIXIE),(28100,ROOT_GOLEM),(28680,CANOPY_PIXIE)),
                     ledges=((27210,ROOT_GOLEM),(27530,CANOPY_PIXIE),(27950,CANOPY_PIXIE),(28430,ROOT_GOLEM),(28740,CANOPY_PIXIE))),
    )),
    hunting_zone("해질녘 둥지", (11, 19), 275, 215, (
        hunting_spot("첫 번째 알터",
                     ground=((29770,GOLEM),(29995,CANOPY_PIXIE),(30280,GOLEM),(30520,GOLEM)),
                     ledges=((29690,CANOPY_PIXIE),(29980,GOLEM),(30290,CANOPY_PIXIE))),
        hunting_spot("황금잎 계단",
                     ground=((30975,GOLEM),(31230,GOLEM),(31640,CANOPY_PIXIE),(32020,GOLEM)),
                     ledges=((30880,GOLEM),(31260,CANOPY_PIXIE),(31670,GOLEM),(32030,CANOPY_PIXIE))),
        hunting_spot("머쉬맘의 둥지",
                     ground=((32608,GOLEM),(32910,CANOPY_PIXIE),(33395,MUSHMOM),(33670,GOLEM)),
                     ledges=((32410,GOLEM),(32740,CANOPY_PIXIE),(33150,GOLEM),(33580,CANOPY_PIXIE))),
    ), boss_waves=5),
    hunting_zone("구리 절벽 사냥터", (18, 20), 255, 190, (
        hunting_spot("구리 바닥",
                     ground=((34540,COPPER_BUBBLE),(34880,COPPER_BUBBLE),(35200,COPPER_GOLEM)),
                     ledges=((34290,COPPER_BUBBLE),(34350,COPPER_BUBBLE),(34760,COPPER_GOLEM))),
        hunting_spot("세 칸 절벽",
                     ground=((35710,COPPER_BUBBLE),(36150,COPPER_GOLEM),(36640,COPPER_BUBBLE)),
                     ledges=((35000,COPPER_BUBBLE),(35380,COPPER_GOLEM),(35950,COPPER_GOLEM),
                             (36455,COPPER_BUBBLE),(36585,COPPER_GOLEM))),
    )),
    hunting_zone("푸른 수관 사냥터", (20, 23), 280, 220, (
        hunting_spot("물비늘 여울",
                     ground=((37510,FOREST_PIXIE),(37870,COPPER_GOLEM),(38230,FOREST_PIXIE)),
                     ledges=((37420,FOREST_PIXIE),(37760,COPPER_GOLEM),(38060,FOREST_PIXIE))),
        hunting_spot("유리씨 나무",
                     ground=((38560,COPPER_GOLEM),(38960,FOREST_PIXIE),(39330,FOREST_PIXIE),(39660,COPPER_GOLEM)),
                     ledges=((38460,FOREST_PIXIE),(38910,COPPER_GOLEM),(39390,FOREST_PIXIE),(39800,FOREST_MUSHMOM))),
        hunting_spot("별갓 전망대",
                     ground=((40060,FOREST_PIXIE),(40472,FOREST_MUSHMOM),(40745,COPPER_GOLEM)),
                     ledges=((40320,FOREST_PIXIE),(40560,COPPER_GOLEM))),
    ), boss_waves=6),
)


def dedicated_hunt(field):
    kind = field["kind"]
    creature = SPECIES[kind]
    elite = creature.get("elite", False)
    level = creature["level"]
    floor_positions = (.73,) if elite else (.29,.47,.64,.83)
    shelves = field["ledges"][1:2] if elite else field["ledges"]
    return hunting_zone(creature["name"] + " 전용 사냥터", (level,level), 260, 200, (
        hunting_spot("사냥터 바닥", ground=tuple((field["start"] + round(field["width"]*fraction),kind)
                                                for fraction in floor_positions)),
        hunting_spot("사냥터 발판", ledges=tuple((ledge,kind) for ledge in shelves)),
    ), boss_waves=5 if elite else 0)


HUNT_ZONES += tuple(dedicated_hunt(field) for field in HUNT_FIELDS)


def next_hunting_wave(zone, tick, elite=False):
    period = zone["wave"]
    minimum = zone["recovery"] + (zone["boss_waves"] * period if elite else 0)
    earliest = tick + minimum
    return ((earliest + period - 1) // period) * period
