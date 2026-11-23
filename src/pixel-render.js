'use strict';

const pixelImages = {};
const pixelMeta = PIXEL_DATA.meta;
const ASSETS = ['hero', 'wildlife', 'background', 'terrain', 'stone', 'props', 'depths', 'icons'];
const heroScale = 0.72;
const walkCycle = pixelMeta.hero.animations.walk.durations.reduce((sum, duration) => sum + duration, 0);
let pixelLoaded = 0;
let pixelReady = false;
let loadingError = false;

for (const name of ASSETS) {
  const image = new Image();
  image.onload = () => {
    if (++pixelLoaded === ASSETS.length) {
      pixelReady = true;
      toast('↑ 대화·출구 · Z 공격 · X 스킬 · 1~4 퀵슬롯');
    }
  };
  image.onerror = () => { loadingError = true; };
  pixelImages[name] = image;
  image.src = PIXEL_DATA[name];
}

function frameAt(animation, elapsed) {
  const total = animation.durations.reduce((sum, duration) => sum + duration, 0);
  let position = animation.loop === false ? Math.min(elapsed, total - 1) : elapsed % total;
  for (const [index, duration] of animation.durations.entries()) {
    if (position < duration) return animation.frames[index];
    position -= duration;
  }
  return animation.frames.at(-1);
}

function atlas(name, frame, x, y, scale, direction = 1, opacity = 1, tint = 'none') {
  const {columns, frameWidth, frameHeight, anchor} = pixelMeta[name];
  g.save();
  g.globalAlpha = opacity;
  if (tint !== 'none') g.filter = tint;
  g.translate(Math.round(x), Math.round(y));
  if (direction < 0) g.scale(-1, 1);
  g.drawImage(
    pixelImages[name], frame % columns * frameWidth, Math.floor(frame / columns) * frameHeight, frameWidth, frameHeight,
    -Math.round(anchor[0] * scale), -Math.round(anchor[1] * scale),
    Math.round(frameWidth * scale), Math.round(frameHeight * scale)
  );
  g.restore();
}
function pixelText(text, x, y, color = '#fff7de', size = 11) {
  g.font = 'bold ' + size + 'px system-ui, sans-serif';
  g.textAlign = 'center';
  g.lineJoin = 'round';
  g.lineWidth = 3;
  g.strokeStyle = '#16382a';
  g.strokeText(text, Math.round(x), Math.round(y));
  g.fillStyle = color;
  g.fillText(text, Math.round(x), Math.round(y));
  g.textAlign = 'left';
}
function rect(x, y, width, height, color) {
  g.fillStyle = color;
  g.fillRect(Math.round(x), Math.round(y), Math.round(width), Math.round(height));
}
function drawBackdrop(area) {
  const image = pixelImages[area.image ?? 'background'];
  const [start, end] = area.backdrop;
  const progress = clamp((camera - area.start) / (area.end - area.start - canvas.width), 0, 1);
  const x = Math.round(image.width * (start + (end - start) * progress));
  // Sample a moving camera window inside the panorama. There is no wrap or tile edge.
  g.drawImage(image, x, area.image ? 0 : 123, Math.floor(image.width * 0.36), area.image ? image.height : 505,
    0, 0, canvas.width, canvas.height);
}

function textureBand(image, left, right, deep = false) {
  const first = Math.floor(left / image.width);
  for (let tile = first; tile * image.width < right; tile++) {
    g.save();
    g.translate((tile + (tile % 2)) * image.width, 0);
    if (tile % 2) g.scale(-1, 1);
    g.drawImage(image, 0, 0);
    if (deep) {
      const underside = 48;
      g.translate(0, image.height * 2);
      g.scale(1, -1);
      g.drawImage(image, 0, image.height - underside, image.width, underside,
        0, image.height - underside, image.width, underside);
    }
    g.restore();
  }
}

function drawGround(area) {
  const image = pixelImages[area.material];
  const visibleLeft = Math.floor(camera);
  const visibleRight = Math.min(area.end, visibleLeft + canvas.width);
  const segments = [];
  for (let i = 1; i < groundPoints.length; i++) {
    const [startX, startY] = groundPoints[i - 1];
    const [endX, endY] = groundPoints[i];
    const left = Math.max(startX, visibleLeft);
    const right = Math.min(endX, visibleRight);
    if (right <= left) continue;
    const slope = (endY - startY) / (endX - startX);
    segments.push({left, right, slope, offset: startY - slope * startX - 5});
  }
  if (!segments.length) return;
  const first = segments[0];
  g.save();
  g.beginPath();
  g.moveTo(first.left, first.slope * first.left + first.offset);
  for (const {right, slope, offset} of segments) g.lineTo(right, slope * right + offset);
  g.lineTo(visibleRight, canvas.height);
  g.lineTo(visibleLeft, canvas.height);
  g.closePath();
  g.clip();
  rect(visibleLeft, 290, visibleRight - visibleLeft, canvas.height, area.material === 'stone' ? '#887765' : '#564522');

  for (const {left, right, slope, offset} of segments) {
    g.save();
    g.beginPath();
    g.rect(left - 0.45, 0, right - left + 0.9, canvas.height);
    g.clip();
    g.transform(1, slope, 0, 1, 0, offset);
    textureBand(image, left - 0.45, right + 0.45, true);
    g.restore();
  }
  g.restore();
}

function drawLedge(ledge, image) {
  const {x, y, w} = ledge;
  g.save();
  g.beginPath();
  g.roundRect(x, y - 5, w, 32, [4, 4, 10, 10]);
  g.clip();
  g.translate(0, y - 5);
  textureBand(image, x, x + w);
  rect(x, 28, w, 4, '#21351886');
  g.restore();
}
function drawProp([x, id, width, y]) {
  const [sourceX, sourceY, sourceWidth, sourceHeight] = pixelMeta.props[id];
  const height = Math.round(width * sourceHeight / sourceWidth);
  g.drawImage(pixelImages.props, sourceX, sourceY, sourceWidth, sourceHeight,
    Math.round(x - width / 2), Math.round((y ?? groundAt(x)) - height + 2), width, height);
}
function drawLadder({x, top, bottom}) {
  rect(x - 10, top, 4, bottom - top, '#775837');
  rect(x + 6, top, 4, bottom - top, '#775837');
  rect(x - 10, top, 1, bottom - top, '#dcba80');
  rect(x + 6, top, 1, bottom - top, '#dcba80');
  for (let y = top + 8; y < bottom; y += 10) {
    rect(x - 7, y, 15, 3, '#bc995f');
    rect(x - 7, y, 15, 1, '#e3c486');
  }
}
function drawPortal(portal) {
  const x = portal.x;
  const y = groundAt(x);
  g.fillStyle = '#42e4ff32';
  g.beginPath();
  g.ellipse(x, y - 28, 16, 27, 0, 0, Math.PI * 2);
  g.fill();
  g.lineWidth = 2;
  g.strokeStyle = '#bbefff';
  g.stroke();
  for (let i = 0; i < 7; i++) {
    const height = (i * 7 + tick * 0.5) % 46;
    rect(x + (i % 3 - 1) * 7, y - height - 5, 2, 4, '#e6fcff');
  }
  pixelText('↑ ' + portal.label, x, y - 62, '#b9edff');
}
function drawScenery(area) {
  const left = Math.floor(camera);
  const right = left + canvas.width;
  const image = pixelImages[area.material];
  g.save();
  g.translate(-left, 0);
  for (const prop of sceneryProps) {
    if (prop[0] >= area.start && prop[0] < area.end && prop[0] > left - 160 && prop[0] < right + 160) drawProp(prop);
  }
  for (const ladder of ladders) {
    if (ladder.x >= area.start && ladder.x < area.end && ladder.x >= left - 12 && ladder.x <= right + 12) drawLadder(ladder);
  }
  drawGround(area);
  for (const ledge of ledges) {
    if (ledge.x >= area.start && ledge.x + ledge.w <= area.end && ledge.x + ledge.w > left && ledge.x < right) drawLedge(ledge, image);
  }
  for (const portal of portals) {
    if (portal.x >= area.start && portal.x < area.end && portal.x > left - 60 && portal.x < right + 60) drawPortal(portal);
  }
  for (const npc of NPCS) {
    if (npc.x < left - 50 || npc.x > right + 50) continue;
    const y = groundAt(npc.x);
    const frame = frameAt(pixelMeta.hero.animations.idle, tick * STEP_MS + npc.x * 3);
    const tint = npc.kind === 'shop' ? 'hue-rotate(42deg)' : npc.kind === 'trainer' ? 'hue-rotate(196deg)' : 'none';
    atlas('hero', frame, npc.x, y, heroScale, p.x > npc.x ? 1 : -1, 1, tint);
    pixelText(npc.name + ' · ' + npc.role, npc.x, y - 56, '#ffe3a6');
    const questId = npc.kind === 'harbor' ? 1 : npc.kind === 'quest' ? npc.quest ?? 0 : null;
    const progress = p.quests[questId];
    if (nearbyNPC() === npc) pixelText('↑ 대화', npc.x, y - 72, '#fffbd8', 12);
    else if (progress?.state === 0 || progress?.state === 1 && progress.count >= QUESTS[questId].target) {
      pixelText(progress.state === 0 ? '◆' : '✓', npc.x, y - 72, '#ffdc80', 15);
    }
  }
  g.restore();
}
function drawPlayer() {
  const animations = pixelMeta.hero.animations;
  let name = 'idle';
  let time = tick * STEP_MS;
  if (hurtUntil > tick) name = 'hurt';
  else if (swing) { name = 'attack'; time = (tick - swing.start) * STEP_MS; }
  else if (!p.grounded && !climbing) name = p.vy < 0 ? 'jumpUp' : 'jumpDown';
  else if (walking || (climbing && (keys.ArrowUp || keys.ArrowDown))) {
    name = 'walk';
    time = (walkDistance % 68) / 68 * walkCycle;
  }
  const direction = swing?.direction ?? p.dir;
  const opacity = invulnerableUntil > tick && hurtUntil <= tick && tick % 6 < 3 ? 0.55 : 1;
  if (supportUntil > tick) {
    rect(p.x - 12, p.y - 2, 24, 2, '#9de6bd77');
    for (let i = 0; i < 3; i++) {
      rect(p.x - 12 + i * 11, p.y - (tick + i * 11) % 36, 2, 2, '#a0f3ca');
    }
  }
  atlas('hero', frameAt(animations[name], time), p.x, p.y, heroScale, direction, opacity);
  pixelText('Lv.' + p.level + ' ' + CLASSES[p.job].name, p.x, p.y - 61);
}
function drawMonster(monster) {
  const death = monster.deathAt === null ? 0 : tick - monster.deathAt;
  if (death >= 20) return;
  const {species} = monster;
  const hurt = Math.max(0, monster.hitUntil - tick);
  const walking = Math.floor((tick + monster.phase) / (monster.state === 'pursuit' ? 6 : 10)) % 4;
  const attacking = monster.lastStrike !== undefined && tick - monster.lastStrike < 8;
  const pose = hurt || monster.deathAt !== null ? 3 :
    monster.strikeAt ? 2 : attacking ? 5 : [0, 1, 0, 4][walking];
  const hop = species.float ? Math.sin((tick + monster.phase) / 10) * 3 : 0;
  const scale = species.elite ? 1.6 : species.sprite === 4 ? 1.16 : 1.03;
  const x = monster.x + (monster.hitDirection ?? 0) * hurt * 0.35;
  if (monster.strikeAt) {
    const reach = monster.attackRange ?? 25;
    const left = monster.dir > 0 ? monster.x : monster.x - reach;
    rect(left, monster.y - 2, reach, 4, species.elite ? '#ffd379a8' : '#f1a57187');
  }
  atlas('wildlife', species.sprite * 6 + pose, x, monster.y - hop - death * 0.25,
    scale, monster.dir, 1 - death / 20, species.tint);
  if (monster.deathAt !== null) return;
  const tagY = monster.y - (species.elite ? 77 : 53);
  const visible = species.elite || Math.abs(monster.x - p.x) < 100;
  if (visible) pixelText('Lv.' + species.level + ' ' + species.name, monster.x, tagY, '#fff4bf', 10);
  if (monster.hp < species.hp || species.elite) {
    const width = species.elite ? 64 : 30;
    rect(monster.x - width / 2, tagY + 4, width, 5, '#241d32');
    rect(monster.x - width / 2 + 1, tagY + 5, (width - 2) * monster.hp / species.hp, 3, species.elite ? '#f39477' : '#d3ec82');
  }
  if (monster.strikeAt) pixelText('!', monster.x, tagY - 12, '#ffbc77', 17);
}
function drawIcon(index, x, y, size) {
  const tile = pixelImages.icons.width / 4;
  g.drawImage(pixelImages.icons, index % 4 * tile, Math.floor(index / 4) * tile,
    tile, tile, Math.round(x - size / 2), Math.round(y - size / 2), size, size);
}
function drawDrop(drop) {
  const progress = Math.min(1, (tick - drop.start) / 26);
  const height = Math.sin(progress * Math.PI) * 35;
  const bounce = progress === 1 ? Math.sin((tick - drop.start) / 8) * 3 : 0;
  const y = drop.y - 9 - height + bounce;
  drawIcon(7, drop.x - 12, y + 2, 18);
  drawIcon(itemIcon(drop.item), drop.x + 4, y, 23);
  if (drop.rare) {
    drawIcon(itemIcon(drop.rare), drop.x + 22, y - 4, 25);
    const sparkle = tick % 36;
    if (sparkle < 16) {
      rect(drop.x + 30, y - 17 - sparkle / 2, 2, 9, '#fff1ab');
      rect(drop.x + 27, y - 13 - sparkle / 2, 8, 2, '#fff1ab');
    }
  }
}
function drawEffect(effect) {
  const {shape, x, y, color, text, direction, duration, start} = effect;
  const progress = (tick - start) / duration;
  if (effect.expired) return;
  if (shape === 'pickup') {
    const eased = 1 - (1 - progress) ** 2;
    drawIcon(effect.icon, x + (effect.endX - x) * eased,
      y + (effect.endY - y) * eased - Math.sin(progress * Math.PI) * 12, 20);
    return;
  }
  if (shape === 'boss-wave') {
    const step = Math.round(progress * 8);
    for (let i = -3; i <= 3; i++) rect(x + i * effect.size / 4, y - (3 - Math.abs(i)) * step,
      8 + step, 4 + step / 2, step < 5 ? '#fff0a0' : '#f19b7b88');
    return;
  }
  if (shape === 'arrow') {
    rect(x - direction * 12, y - 1, 13, 2, '#b6f6df');
    rect(x, y - 2, 4, 4, '#fff4b0');
    return;
  }
  g.save();
  g.globalAlpha = Math.min(1, (1 - progress) * 2);
  if (shape === 'text') {
    pixelText(text, x, y - progress * 22, color, 17);
  } else if (shape === 'stars') {
    for (let i = -2; i <= 2; i++) {
      const px = x + i * 47 + (i * 13 % 17);
      const py = y - 65 + progress * 78 + Math.abs(i * 9);
      rect(px - 1, py - 7, 3, 15, '#fae0ff');
      rect(px - 6, py - 1, 13, 3, '#fae0ff');
    }
  } else {
    g.strokeStyle = shape === 'arc' ? '#ffe09a' : '#aef0ff';
    g.lineWidth = 3;
    g.beginPath();
    if (shape === 'arc') {
      g.ellipse(x + direction * 39, y, 27 + progress * 36, 28, 0,
        direction > 0 ? -1.3 : 1.8, direction > 0 ? 1.3 : 4.5);
    } else g.ellipse(x, y, 18 + progress * 104, 8 + progress * 28, 0, 0, Math.PI * 2);
    g.stroke();
  }
  g.restore();
}

function draw() {
  g.imageSmoothingEnabled = false;
  if (!pixelReady) {
    rect(0, 0, canvas.width, canvas.height, '#10303b');
    pixelText(loadingError ? '그래픽을 불러오지 못했어요. 게임 폴더 전체를 압축 해제해 주세요.' :
      '그래픽 불러오는 중 · ' + pixelLoaded + '/' + ASSETS.length, 480, 234, '#fff7de', 15);
    return;
  }
  const area = areaAt(p.x);
  drawBackdrop(area);
  drawScenery(area);
  if (area.tint) rect(0, 0, canvas.width, canvas.height, area.tint);
  const left = Math.floor(camera);
  g.save();
  g.translate(-left, 0);
  for (const monster of monsters) {
    if (areaAt(monster.x) === area && monster.x > left - 70 && monster.x < left + canvas.width + 70) drawMonster(monster);
  }
  for (const drop of drops) {
    if (areaAt(drop.x) !== area || drop.x < left || drop.x > left + canvas.width) continue;
    drawDrop(drop);
  }
  drawPlayer();
  for (const effect of effects) drawEffect(effect);
  g.restore();
  if (paused) {
    rect(0, 0, canvas.width, canvas.height, '#102c4270');
    pixelText('일시정지', 480, 234, '#fff7de', 23);
  }
}

let previousFrame;
let accumulator = 0;
function loop(now) {
  if (previousFrame !== undefined) accumulator += Math.min(80, now - previousFrame);
  previousFrame = now;
  while (accumulator >= STEP_MS) {
    step();
    accumulator -= STEP_MS;
  }
  draw();
  requestAnimationFrame(loop);
}
requestAnimationFrame(loop);
