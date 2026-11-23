"""Shop inventory and atlas indexing shared by the game and asset baker."""
# ID, display name, slot, level, price, primary bonus, job.
EXPANSION_EQUIPMENT = (
    ("dagger","갈대 단검","weapon",5,245,11,"thief"),
    ("shadowdagger","월식 단검","weapon",12,980,30,"thief"),
    ("knuckle","부두 건틀릿","weapon",5,245,12,"pirate"),
    ("stormknuckle","뇌운 건틀릿","weapon",12,980,30,"pirate"),
    ("redcap","산딸기 모자","head",2,70,2,None),
    ("apprenticehat","여행자 펠트 모자","head",4,115,4,None),
    ("wizardhat","약초꾼 모자","head",8,360,8,None),
    ("steelhelm","등대지기 투구","head",7,300,7,None),
    ("bandana","구름 두건","head",3,95,3,None),
    ("vikinghelm","황동 뿔투구","head",11,680,11,None),
    ("blazer","까마귀 재킷","armor",3,105,3,None),
    ("archertop","갈대 사냥복","armor",5,160,5,None),
    ("sergeant","항만 근무복","armor",7,350,8,None),
    ("blackthief","연막 조끼","armor",6,240,6,None),
    ("orangethief","여우불 외투","armor",8,430,9,None),
    ("greenhood","이끼 후드 조끼","armor",4,140,4,None),
    ("hwarang","노을 비늘갑옷","armor",12,790,15,None),
    ("baseball","단풍 바람막이","armor",3,105,3,None),
    ("chimewand","새벽종 완드","weapon",5,245,9,"cleric"),
    ("dawnwand","햇무리 완드","weapon",12,980,26,"cleric"),
)

WORN_ITEMS = ("twig", "bronze", "blade", "sunblade", "bow", "nightbow", "wand", "tidewand",
              "coat", "shell", "glasscoat", "crabguard", "cap")
WORN_ITEMS += tuple(entry[0] for entry in EXPANSION_EQUIPMENT)
MELEE_WEAPONS = WORN_ITEMS[:4] + ("dagger","shadowdagger","knuckle","stormknuckle")
WORN_ROWS = {item: row for row, item in enumerate(WORN_ITEMS)}
WORN_ROWS.update({item: len(WORN_ITEMS) + len(MELEE_WEAPONS) + row for row, item in enumerate(("dew","prism","shimmer","moonseal"))})

LEGACY_WORN = dict(zip(("coat","shell","glasscoat","crabguard","cap","dew","prism","shimmer","moonseal"),
                       (8,9,10,11,12,17,18,19,20)))
EXPANSION_ICON_COLUMNS = {item: index for index, item in enumerate((0,16,17,18,1,19,2,20))}
EXPANSION_ICON_COLUMNS.update({index: index-24 for index in range(32,32+len(EXPANSION_EQUIPMENT))})
