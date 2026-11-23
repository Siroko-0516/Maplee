const path = require('node:path');
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const {execFileSync} = require('node:child_process');
const {createCanvas, Image} = require('@napi-rs/canvas');

const root = path.resolve(__dirname, '..');

async function main() {
  execFileSync(process.execPath, [path.join(root, 'scripts/build.mjs')]);
  const html = fs.readFileSync(path.join(root, 'dist/maple-local.html'), 'utf8');
  assert(!html.includes('<script src=') && !html.includes('href="src/'), 'offline build embeds code and stylesheet');
  const canvas = createCanvas(960, 468);
  const mini = createCanvas(200, 46);
  function node(tag) {
    return {
      tag, children: [], style: {}, dataset: {},
      append(...children) { this.children.push(...children); },
      replaceChildren() { this.children = []; }, setAttribute() {}
    };
  }
  const elements = new Map([...html.matchAll(/id="([^"]+)"/g)].map(([, id]) => [id, node(id)]));
  elements.set('minimap', mini);
  const key = 'maple-local-world-v1';
  const storage = {[key]: JSON.stringify({x: 310, level: 2, xp: 12, hp: 62, gold: 17, kills: 4, pots: 3, quest: 1})};
  const sandbox = vm.createContext({
    document: {
      querySelector: selector => selector === 'canvas' ? canvas : elements.get(selector.slice(1)),
      querySelectorAll: () => [], createElement: node
    },
    localStorage: {getItem: key => storage[key] ?? null, setItem: (key, value) => storage[key] = value},
    window: {addEventListener() {}},
    setTimeout() {}, clearTimeout() {}, requestAnimationFrame() {}, Image
  });
  const run = code => vm.runInContext(code, sandbox);
  for (const [, script] of html.matchAll(/<script>([\s\S]*?)<\/script>/g)) run(script);
  for (let i = 0; i < 150 && !run('pixelReady'); i++) await new Promise(resolve => setTimeout(resolve, 20));
  assert(run('pixelReady'), 'embedded images load');

  run(`
    function check(value, message) { if (!value) throw new Error(message); }
    function advance(steps) { for (let i = 0; i < steps; i++) step(); }
    check(p.level === 2 && p.hp === 62 && p.quests[0].count === 4 && p.job === 'beginner', 'legacy save migration');
    check(remainingAP() === 3 && remainingSP() === 1, 'legacy saves receive points earned by level');
    handleKey('KeyC');
    check(panel?.kind === 'character', 'character shortcut opens the AP panel');
    const initialAttack = stats().attack;
    allocateAttribute('strength');
    allocateAttribute('vitality');
    allocateAttribute('agility');
    allocateAttribute('spirit');
    check(stats().attack === initialAttack + 2 && stats().hp === 118 && stats().speed > 4.2,
      'AP modifies combat stats and movement');
    check(remainingAP() === 0 && p.attributes.spirit === 0, 'AP cannot be overspent');
    closePanel();
    monsters = [];
    travelTo(390);
    keys.ArrowRight = true;
    let previousY = p.y;
    for (let i = 0; i < 90; i++) {
      step();
      check(p.grounded && Math.abs(p.y - previousY) < 2, 'continuous walk along ground slopes');
      previousY = p.y;
    }
    check(p.x > 700 && p.y === 338, 'slope reaches next terrace');
    travelTo(2400);
    advance(80);
    check(areaAt(p.x) === AREAS[0] && camera === AREAS[0].end - canvas.width, 'walking does not switch maps');
    keys.ArrowRight = false;
    travelTo(portals[0].x);
    interact();
    check(areaAt(p.x) === AREAS[1] && camera === AREAS[1].start, 'portal switches map and resets the camera');
    const east = portals.find(portal => portal.label === AREAS[2].name);
    travelTo(east.x);
    interact();
    check(areaAt(p.x) === AREAS[2], 'second exit enters the harbor');
    travelTo(ledges[0].ladderX);
    keys.ArrowUp = true;
    advance(70);
    check(p.y === ledges[0].y && p.grounded, 'climb onto ledge');
    keys.ArrowUp = false;
    keys.ArrowDown = true;
    jump();
    advance(60);
    check(p.surface === 'ground', 'drop through ledge');
    keys.ArrowDown = false;

    travelTo(2690);
    p.dir = 1;
    spawn(p.x + 37, 0, 0);
    const target = monsters[0];
    const hp = target.hp;
    attack();
    advance(4);
    check(target.hp === hp, 'no damage before strike frame');
    step();
    check(frameAt(attackAnimation, (tick - swing.start) * STEP_MS) === 9 && target.hp < hp, 'damage lands with strike');
    const after = target.hp;
    advance(16);
    check(target.hp === after, 'one hit per swing');

    travelTo(870);
    interact();
    check(panel?.kind === 'shop', 'interact opens shop panel');
    p.gold = 200;
    buy('bronze', panel.data.stock);
    check(p.bag.bronze === 1 && p.gold === 122, 'buy uses shop stock and gold');
    const originalAttack = stats().attack;
    toggleEquipment('bronze');
    check(stats().attack === originalAttack + 3 && p.equipment.weapon === 'bronze', 'equipment updates attack');
    sell('bronze');
    check(p.bag.bronze === 1 && p.gold === 122, 'equipped last copy cannot be sold');
    sell('twig');
    check(!p.bag.twig && p.gold === 134, 'sell grants gold');
    closePanel();
    p.hp = 30;
    healWith('potion');
    check(p.hp === 85 && p.pots === 2, 'HP potion');

    changeJob('ranger');
    check(p.job === 'beginner', 'level requirement blocks job change');
    p.xp = 0;
    gainXP(450);
    check(p.level >= 5 && p.hp === stats().hp, 'XP levels up and restores health');
    upgradeSkill('primary');
    check(p.skillRanks.primary === 2 && primarySkill().power > CLASSES.beginner.power, 'SP raises primary skill power');
    changeJob('ranger');
    check(p.skillRanks.primary === 2, 'primary skill rank follows the job change');
    check(p.job === 'ranger' && p.equipment.weapon === 'bow', 'job change grants and equips starter weapon');
    toggleEquipment('wand');
    check(p.equipment.weapon === 'bow', 'equipment class restriction');
    monsters = [];
    travelTo(2720);
    spawn(p.x + 130, 0, 0);
    const mana = p.mp;
    attack(true);
    check(p.mp === mana - CLASSES.ranger.cost, 'skill consumes MP');
    advance(18);
    check(monsters[0].deathAt !== null && drops.some(drop => drop.item === 'jelly'), 'ranged skill travels and creates loot');

    monsters = [];
    travelTo(11732);
    spawn(11780, 4, 1);
    p.quests[1].state = 1;
    reward(monsters[0]);
    check(p.quests[1].count === 1 && drops.at(-1).rare === 'prism', 'elite drop and quest');
    travelTo(11780);
    step();
    check(p.bag.prism >= 1, 'elite equipment can be picked up');
    p.quests[2].state = 1;
    handleKey('KeyQ');
    check(panel?.kind === 'journal', 'quest shortcut opens journal');
    p.trackedQuest = 2;
    updateHUD();
    check($('#quest').textContent.startsWith(QUESTS[2].name), 'quest tracker follows selected quest');
    closePanel();

    while (p.level < 7) gainXP(xpNeeded());
    upgradeSkill('support');
    check(p.skillRanks.support === 1, 'class support unlocks at level seven');
    openPanel('hotkeys');
    const selects = $('#panel').children.flatMap(node => node.children).filter(node => node.tag === 'select');
    check(selects.length === 4, 'settings expose four quickslot assignments');
    selects[0].value = 'support';
    selects[0].onchange();
    selects[3].value = '';
    selects[3].onchange();
    closePanel();
    p.mp = stats().mp;
    const beforeSupport = p.mp;
    handleKey('Digit1');
    check(p.mp === beforeSupport - SUPPORTS.ranger.cost && supportValue('speed') > 0, 'assigned quickslot activates class support');
    const spentMP = p.mp;
    handleKey('Digit1');
    check(p.mp === spentMP && $('#slot-count-0').textContent.endsWith('초'), 'cooldown locks use and appears on quickslot');
    supportUntil = tick;
    check(supportValue('speed') === 0, 'support buff expires');
    check($('#minimap-player').style.left.endsWith('%'), 'minimap marker follows the current map');
    const oldGold = p.gold;
    save();
    p.gold = 0;
    p.job = 'beginner';
    loadGame();
    check(p.job === 'ranger' && p.gold === oldGold && p.bag.prism >= 1 && !p.bag.twig, 'progression survives a save round trip without restoring sold items');
    check(p.attributes.strength === 1 && p.skillRanks.primary === 2 && p.skillRanks.support === 1 &&
      p.hotbar[0] === 'support' && p.hotbar[3] === null && p.trackedQuest === 2,
      'points, skill ranks, quickslots and tracked quest persist');
  `);

  for (const [index, x] of [650, 4720, 10470].entries()) {
    run('monsters = []; populate(); travelTo(' + x + '); effects = []; drops = []; draw();');
    if (process.env.MAPLEE_RENDER_DIR) {
      fs.writeFileSync(path.join(process.env.MAPLEE_RENDER_DIR, 'maplee-area-' + index + '.png'), canvas.toBuffer('image/png'));
    }
  }
  run(`
    // Sweep both edges and the middle of each map with a bright fill below the tile layer.
    for (const area of AREAS) {
      for (const left of [area.start, Math.floor((area.start + area.end - 960) / 2), area.end - 960]) {
        camera = left;
        rect(0, 0, 960, 468, '#ff00ff');
        g.save();
        g.translate(-left, 0);
        drawGround(area);
        g.restore();
        const pixels = g.getImageData(0, 0, 960, 468).data;
        for (let x = 0; x < 960; x++) {
          const offset = (Math.ceil(groundAt(left + x)) + 10) * 960 * 4 + x * 4;
          check(!(pixels[offset] === 255 && pixels[offset+1] === 0 && pixels[offset+2] === 255), 'ground seam at ' + (left + x));
        }
        g.drawImage(pixelImages.background, 0, 0, 1, 1, 0, 0, 960, 468);
        const original = g.drawImage;
        let sampled = false;
        g.drawImage = function(image, sx, sy, sw, sh, ...rest) {
          check(!sampled && sx >= 0 && sx + sw <= image.width, 'backdrop uses one in-bounds image window');
          sampled = true;
          return original.call(g, image, sx, sy, sw, sh, ...rest);
        };
        drawBackdrop(area);
        g.drawImage = original;
        check(sampled, 'backdrop was drawn');
      }
    }
  `);
  console.log('PASS: offline HTML, slopes, three separate maps, ground and backdrop continuity, ladder, combat, jobs, equipment, shop, quests, AP/SP, quickslots, minimap and saves');
}

main().catch(error => {
  console.error(error);
  process.exitCode = 1;
});
