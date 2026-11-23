const path = require('node:path');
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const {execFileSync} = require('node:child_process');
const {createCanvas, Image} = require('@napi-rs/canvas');

const root = path.resolve(__dirname, '..');

async function main() {
  const canvas = createCanvas(960, 468);
  const elements = {};
  const storage = {};
  function element(id) {
    return elements[id] ??= {
      style: {}, hidden: false, append() {}, replaceChildren() {},
      getContext: () => canvas.getContext('2d')
    };
  }
  const context = vm.createContext({
    document: {
      querySelector: element, querySelectorAll: () => [],
      createElement: () => element(Symbol())
    },
    localStorage: {getItem: key => storage[key] ?? null, setItem: (key, value) => storage[key] = value},
    window: {addEventListener() {}},
    setTimeout() {}, clearTimeout() {}, requestAnimationFrame() {},
    Image
  });
  const run = code => vm.runInContext(code, context);
  run(execFileSync(process.execPath, [path.join(root, 'scripts/build.mjs'), '--asset-data'], {encoding: 'utf8'}));
  for (const file of ['world.js', 'pixel-render.js']) run(fs.readFileSync(path.join(root, 'src', file), 'utf8'));
  for (let i = 0; i < 150 && !run('pixelReady'); i++) {
    await new Promise(resolve => setTimeout(resolve, 20));
  }
  assert(run('pixelReady'), 'embedded PNGs load');

  run(`
    function check(value, message) { if (!value) throw new Error(message); }
    function advance(steps) { for (let i = 0; i < steps; i++) step(); }
    function testMonster(x, y = ground, hp = 999) {
      return {x, y, home: x, left: x - 10, right: x + 10, dir: 1, type: 1, hp, max: hp, dead: 0, phase: 0};
    }

    mobs = [];
    travelTo(2200);
    advance(1);
    check(p.grounded && p.y === ground, 'ground landing');
    jump();
    check(p.vy < 0, 'jump');
    keys.ArrowRight = true;
    advance(15);
    keys = {};
    check(p.x > 2250 && camera > 1700, 'world movement and camera');

    const stackedLadder = ladders.find(ladder => ladder.bottom < ground);
    check(stackedLadder && platforms.length > 65, 'multi-level field layout');
    p.x = stackedLadder.x;
    p.y = stackedLadder.bottom;
    p.vy = 0;
    p.grounded = true;
    keys.ArrowUp = true;
    advance(Math.ceil((stackedLadder.bottom - stackedLadder.top) / 3.2));
    check(p.y === stackedLadder.top && p.grounded, 'climb from a lower ledge');
    keys = {ArrowDown: true};
    advance(Math.ceil((stackedLadder.bottom - stackedLadder.top) / 3.2));
    check(p.y === stackedLadder.bottom && p.grounded, 'descend onto a lower ledge');
    keys = {};
    p.y = stackedLadder.top - 12;
    p.vy = stackedLadder.bottom - stackedLadder.top + 15;
    step();
    check(p.y === stackedLadder.top, 'land on the first crossed ledge');

    travelTo(2200);
    p.dir = 1;
    const target = testMonster(2234);
    const rear = testMonster(2165);
    const higher = testMonster(2234, ground - 58);
    mobs = [target, rear, higher];
    attack();
    advance(4);
    check(target.hp === target.max && !swing.hasHit, 'no damage in the windup');
    step();
    check(frameAt(attackAnimation, (tick - swing.startTick) * STEP_MS) === 9, 'visible strike frame');
    check(target.hp < target.max && target.hitUntil > tick, 'damage and hurt pose start on the strike');
    check(rear.hp === rear.max && higher.hp === higher.max, 'sword skips rear and upper-tier targets');
    const remaining = target.hp;
    advance(15);
    check(target.hp === remaining, 'each swing hits a target only once');

    travelTo(2200);
    p.dir = 1;
    const lethal = testMonster(2234, ground, 1);
    mobs = [lethal];
    const kills = p.kills;
    attack(true);
    advance(5);
    check(lethal.dead && p.kills === kills + 1 && drops.length && fx.some(effect => effect.ring),
      'skill lands on the strike and awards loot');
    p.x = drops[0].x;
    const gold = p.gold;
    step();
    check(p.gold > gold, 'loot pickup');
    travelTo(2200);
    const interrupted = testMonster(2205);
    mobs = [interrupted];
    attack();
    advance(5);
    check(!swing && interrupted.hp === interrupted.max, 'a contact hit interrupts the windup');

    p.hp = 25;
    const potions = p.pots;
    potion();
    check(p.hp === 75 && p.pots === potions - 1, 'potion');
    save();
    check(JSON.parse(localStorage.getItem('maple-local-world-v1')).hp === 75, 'save');
    talk(npcs[0]);
    check(dialog, 'NPC interaction');
    close();

    travelTo(2250);
    camera = 1770;
    inv = 0;
    p.hurtUntil = 0;
    fx = [];
    mobs = [];
    platforms.filter(platform => platform.x > camera && platform.x < camera + 880)
      .forEach((platform, index) => spawn(platform.x + 85, index, platform));
    spawn(2350, 0);
    draw();
  `);

  if (process.env.MAPLEE_RENDER_PATH) {
    fs.writeFileSync(process.env.MAPLEE_RENDER_PATH, canvas.toBuffer('image/png'));
  }
  const idle = canvas.toBuffer('image/png');
  run('keys.ArrowRight = true; advance(8); draw();');
  assert(!idle.equals(canvas.toBuffer('image/png')), 'movement changes the rendered frame');

  const html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
  for (const id of ['region','hp','hpbar','xp','xpbar','lv','gold','kills','pots','dialog','worldmap','toast','pause','sound']) {
    assert(html.includes('id="' + id + '"'), id + ' present');
  }
  console.log('PASS: pixel rendering, movement, stacked ledges and ladders, timed damage, loot, save and HUD');
}

main().catch(error => {
  console.error(error);
  process.exitCode = 1;
});
