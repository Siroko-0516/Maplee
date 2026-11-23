"""Hand-placed hunting routes. Platform positions refer to the ledge's left edge."""

SLIME, MUSHROOM, SNAIL, PIG, KING_CRAB, CRAB, BUBBLE, GOLEM, PIXIE, CLANG, MUSHMOM, MOSS, ANCHOR = range(13)


def hunting_spot(label, ground=(), ledges=()):
    return {"label": label, "ground": ground, "ledges": ledges}


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
                     ground=((2760, SLIME), (2920, SLIME), (3270, SLIME), (3450, MUSHROOM)),
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
                     ground=((18710, MOSS), (18920, MOSS), (19180, PIXIE)),
                     ledges=((18820, PIXIE), (19180, MOSS))),
        hunting_spot("재 묻은 뿌리",
                     ground=((19580, MOSS), (19770, MOSS), (20000, PIXIE), (20230, MOSS)),
                     ledges=((19740, MOSS), (20200, PIXIE))),
        hunting_spot("꺼진 등불터",
                     ground=((20600, MOSS), (20775, MOSS), (20985, MOSS)), ledges=((20570, MOSS),)),
    )),
    hunting_zone("안개등 잔교", (13, 18), 225, 205, (
        hunting_spot("밀물 계단",
                     ground=((21760, CLANG), (22005, ANCHOR), (22240, CLANG)),
                     ledges=((22120, ANCHOR),)),
        hunting_spot("침수된 선착장",
                     ground=((22640, ANCHOR), (22840, ANCHOR), (23030, CLANG), (23250, ANCHOR)),
                     ledges=((22500, ANCHOR), (23000, ANCHOR), (23400, CLANG))),
        hunting_spot("마지막 계류장",
                     ground=((23750, ANCHOR), (23950, ANCHOR), (24160, ANCHOR), (24360, CLANG)),
                     ledges=((23900, ANCHOR), (24330, ANCHOR))),
    )),
)


def next_hunting_wave(zone, tick, elite=False):
    period = zone["wave"]
    minimum = zone["recovery"] + (zone["boss_waves"] * period if elite else 0)
    earliest = tick + minimum
    return ((earliest + period - 1) // period) * period
