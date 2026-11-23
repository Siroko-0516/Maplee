'use strict';

const pixelImages = {};
const pixelMeta = PIXEL_DATA.meta;
const heroScale = 0.72;
const monsterScale = 0.74;
const walkCycle = pixelMeta.hero.animations.walk.durations.reduce((sum, duration) => sum + duration, 0);
let pixelLoaded = 0;
let pixelReady = false;
let loadingError = false;

for (const name of ['hero', 'monsters', 'background', 'terrain']) {
  const image = new Image();
  image.onload = () => {
    if (++pixelLoaded === 4) {
      pixelReady = true;
      toast('↑ 리나와 대화해 첫 의뢰를 시작하세요 · M 지도');
    }
  };
  image.onerror = () => {
    loadingError = true;
    toast('이미지를 불러오지 못했어요. 파일을 다시 열어주세요.');
  };
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

function atlas(name, frame, x, y, scale, direction = 1, opacity = 1) {
  const {columns, frameWidth, frameHeight, anchor} = pixelMeta[name];
  const sourceX = (frame % columns) * frameWidth;
  const sourceY = Math.floor(frame / columns) * frameHeight;
  g.save();
  g.globalAlpha = opacity;
  g.imageSmoothingEnabled = false;
  g.translate(Math.round(x), Math.round(y));
  if (direction < 0) g.scale(-1, 1);
  g.drawImage(
    pixelImages[name], sourceX, sourceY, frameWidth, frameHeight,
    -Math.round(anchor[0] * scale), -Math.round(anchor[1] * scale),
    Math.round(frameWidth * scale), Math.round(frameHeight * scale)
  );
  g.restore();
}

function pixelText(text, x, y, color = '#fff5d0', size = 11) {
  g.font = 'bold ' + size + 'px monospace';
  g.textAlign = 'center';
  g.lineWidth = 3;
  g.strokeStyle = '#263d29';
  g.strokeText(text, Math.round(x), Math.round(y));
  g.fillStyle = color;
  g.fillText(text, Math.round(x), Math.round(y));
  g.textAlign = 'left';
}

function terrainStrip(platform) {
  const {x, y, w} = platform;
  const isGround = y === ground;
  const height = isGround ? 70 : 27;
  const image = pixelImages.terrain;
  const lip = PIXEL_DATA.terrainLip;
  const firstTile = Math.floor(Math.max(x, camera) / image.width) * image.width;
  const right = Math.min(x + w, camera + c.width);

  g.save();
  g.beginPath();
  if (isGround) {
    g.rect(x, y - 9, w, height + 9);
  } else {
    g.roundRect(x, y - 9, w, height + 9, [3, 3, 7, 7]);
  }
  g.clip();
  for (let tileX = firstTile; tileX < right; tileX += image.width) {
    g.drawImage(image, 0, lip, image.width, height, tileX, y + 7, image.width, height);
    g.drawImage(image, 0, 0, image.width, lip + 8, tileX, y - 9, image.width, lip + 8);
  }
  if (!isGround) rect(x, y + height - 4, w, 4, '#28301980');
  g.restore();
}

function background() {
  g.imageSmoothingEnabled = false;
  if (!pixelReady) {
    rect(0, 0, c.width, c.height, '#183a42');
    pixelText(loadingError ? '이미지 로드 실패' : '도트 그래픽 불러오는 중 · ' + pixelLoaded + '/4', 480, 234);
    return;
  }

  // Mirror the next landscape tile so that neighboring edges share the same pixels.
  const offset = Math.floor(camera * 0.12);
  let tile = Math.floor(offset / c.width);
  for (let x = tile * c.width - offset; x < c.width; x += c.width, tile++) {
    g.save();
    g.translate(x + (tile % 2) * c.width, 0);
    if (tile % 2) g.scale(-1, 1);
    g.drawImage(pixelImages.background, 0, -172, c.width, 640);
    g.restore();
  }
  const area = region(p.x);
  if (area >= 3) rect(0, 0, c.width, c.height, area === 4 ? '#303e7930' : '#164b2624');

  g.save();
  g.translate(-Math.floor(camera), 0);
  for (const {x, top, bottom} of ladders) {
    if (x < camera - 12 || x > camera + c.width + 12) continue;
    rect(x - 10, top, 3, bottom - top, '#785d36');
    rect(x + 7, top, 3, bottom - top, '#785d36');
    for (let y = top + 10; y < bottom; y += 10) {
      rect(x - 8, y, 16, 3, '#b5a16c');
      rect(x - 8, y, 16, 1, '#ddc58b');
    }
  }
  for (const platform of platforms) {
    if (platform.x + platform.w > camera && platform.x < camera + c.width) {
      terrainStrip(platform);
    }
  }
  for (const npc of npcs) {
    if (npc.x < camera - 45 || npc.x > camera + c.width + 45) continue;
    const frame = frameAt(pixelMeta.hero.animations.idle, tick * STEP_MS + npc.x * 3);
    atlas('hero', frame, npc.x, ground, heroScale, p.x > npc.x ? 1 : -1);
    pixelText(npc.name, npc.x, ground - 56, '#ffe5a2');
    if (Math.abs(npc.x - p.x) < 75 && p.y > 365) {
      pixelText('↑ 대화', npc.x, ground - 70, '#fffbd8', 12);
    }
  }
  g.restore();
}

function drawPlayer() {
  if (!pixelReady) return;
  let name = 'idle';
  let time = tick * STEP_MS;
  if (p.hurtUntil > tick) {
    name = 'hurt';
  } else if (swing) {
    name = 'attack';
    time = (tick - swing.startTick) * STEP_MS;
  } else if (!p.grounded && !climbing) {
    name = p.vy < 0 ? 'jumpUp' : 'jumpDown';
  } else if (walking || (climbing && (keys.ArrowUp || keys.ArrowDown))) {
    name = 'walk';
    time = (walkDistance % 68) / 68 * walkCycle;
  }

  const x = p.x - Math.floor(camera);
  const alpha = inv && p.hurtUntil <= tick && tick % 6 < 3 ? 0.45 : 1;
  atlas('hero', frameAt(pixelMeta.hero.animations[name], time), x, p.y, heroScale, p.dir, alpha);
  pixelText('Lv.' + p.level + ' 모험가', x, p.y - 61);
}

function drawMob(monster) {
  if (!pixelReady || monster.x < camera - 50 || monster.x > camera + c.width + 50) return;
  const death = monster.dead ? tick - monster.deathAt : 0;
  if (death >= 20) return;
  const name = ['slime', 'mushroom', 'spirit'][monster.type];
  const animation = pixelMeta.monsters.animations[name];
  const hurtTicks = Math.max(0, (monster.hitUntil ?? 0) - tick);
  const elapsed = tick * STEP_MS + monster.phase * 80;
  const frame = hurtTicks || monster.dead ? animation.hurtFrame : frameAt(animation, elapsed);
  const float = monster.type === 2 ? Math.sin(tick * 0.055 + monster.phase) * 3 : 0;
  const x = monster.x - Math.floor(camera) + (monster.hitDirection ?? 0) * hurtTicks * 0.4;
  atlas('monsters', frame, x, monster.y - float - death * 0.35, monsterScale, monster.dir, 1 - death / 20);
  if (monster.hp < monster.max && !monster.dead) {
    rect(x - 13, monster.y - 46, 26, 4, '#32452b');
    rect(x - 12, monster.y - 45, 24 * Math.max(0, monster.hp / monster.max), 2, '#c9e47b');
  }
}
