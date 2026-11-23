'use strict';
const $=s=>document.querySelector(s),c=$('canvas'),g=c.getContext('2d');c.width=960;c.height=468;g.imageSmoothingEnabled=false;
const W=12000,ground=410,regions=[['초록 마을',0,'#bee1e1','#86b77b'],['햇살 초원',1800,'#c8e5dd','#8fbb6b'],['버섯 언덕',4000,'#c6decd','#84aa72'],['깊은 숲',6500,'#a5c5c0','#52856d'],['달빛 유적',9200,'#b2b9d5','#7882a0']];
const STEP_MS = 1000 / 60;
const attackAnimation = PIXEL_DATA.meta.hero.animations.attack;
const swingDuration = attackAnimation.durations.reduce((total, duration) => total + duration, 0);
let swing = null;
let p={x:320,y:ground,vy:0,dir:1,hp:100,level:1,xp:0,gold:0,kills:0,pots:5,quest:0,claimed:0},keys={},mobs=[],fx=[],drops=[],camera=0,tick=0,skillCD=0,inv=0,paused=false,dialog=false,map=false,sound=false,audio,lastRegion=-1,acc=0,last=0,autosave=0;
// Each region has its own ledge layout. Spans are [offset, height above ground, width, ladder offset].
const ledgeLayouts = [
  [[42,116,180,54],[158,208,200,68],[381,82,176,56],[465,166,201,62],[617,250,186,43],[700,115,158,74]],
  [[65,82,180,67],[160,170,170,54],[284,257,190,36],[337,89,228,70],[482,174,192,48],[655,117,172,57]],
  [[24,113,163,60],[109,206,205,52],[285,132,232,57],[426,219,207,51],[534,76,171,80],[644,153,171,41]],
  [[46,151,183,59],[165,74,192,72],[233,239,185,42],[359,155,196,48],[527,211,210,67],[644,110,164,54]],
  [[34,83,230,74],[190,169,155,61],[304,249,200,41],[379,101,222,68],[549,183,202,55],[684,94,150,51]]
];

const platforms = [{x: 0, y: ground, w: W}];
for (const [index, [, startX]] of regions.entries()) {
  const endX = regions[index + 1]?.[1] ?? W;
  for (let start = startX, section = 0; start < endX; start += 850, section++) {
    for (const [offset, height, width, ladderOffset] of ledgeLayouts[index]) {
      const x = start + offset;
      if (x + width > endX - 12) continue;
      const y = ground - height + (section % 2 ? 12 : 0);
      platforms.push({x, y, w: width, ladderX: x + ladderOffset});
    }
  }
}
const ladders = platforms.filter(platform => platform.ladderX !== undefined).map(platform => {
  const x = platform.ladderX;
  let bottom = ground;
  for (const lower of platforms) {
    if (lower.y > platform.y && lower.y < bottom && x > lower.x + 10 && x < lower.x + lower.w - 10) {
      bottom = lower.y;
    }
  }
  return {x, top: platform.y, bottom};
});
let climbing = null;
let walking = false;
let walkDistance = 0;

const npcs=[{x:560,name:'리나',role:'숲의 의뢰',hair:'#a75f40',dress:'#bf7d75'},{x:870,name:'토비',role:'물약 상점',hair:'#695b43',dress:'#6a91a0'},{x:1130,name:'루카',role:'세계 안내',hair:'#a59c63',dress:'#788e59'},{x:9550,name:'별지기',role:'유적의 의뢰',hair:'#c3bfd7',dress:'#8779a1'}];
try{let s=JSON.parse(localStorage.getItem('maple-local-world-v1'));if(s&&Number.isFinite(s.x)&&Number.isFinite(s.level)){for(const k of Object.keys(p))if(Number.isFinite(s[k]))p[k]=s[k];p.x=Math.max(30,Math.min(W-30,p.x));p.y=ground;p.vy=0;p.hp=Math.max(1,Math.min(100,p.hp));p.level=Math.max(1,p.level)}}catch{}
function save(){try{localStorage.setItem('maple-local-world-v1',JSON.stringify(p));return true}catch{return false}}
function toast(t){$('#toast').textContent=t;$('#toast').style.opacity=1;clearTimeout(toast.timer);toast.timer=setTimeout(()=>$('#toast').style.opacity=0,4000)}
function beep(f){if(!sound)return;try{audio=audio||new AudioContext();let o=audio.createOscillator(),v=audio.createGain();o.type='triangle';o.frequency.value=f;v.gain.setValueAtTime(.04,audio.currentTime);v.gain.exponentialRampToValueAtTime(.001,audio.currentTime+.16);o.connect(v);v.connect(audio.destination);o.start();o.stop(audio.currentTime+.16)}catch{}}
function region(x){for(let i=regions.length-1;i>=0;i--)if(x>=regions[i][1])return i;return 0}
function ui(){let need=50+p.level*25;$('#lv').textContent='Lv. '+p.level;$('#hp').textContent=p.hp+' / 100';$('#hpbar').style.width=p.hp+'%';$('#xp').textContent=p.xp+' / '+need;$('#xpbar').style.width=Math.min(100,p.xp/need*100)+'%';$('#gold').textContent=p.gold+' 메소';$('#kills').textContent='처치 '+p.kills;$('#pots').textContent=p.pots;$('#quest').textContent=p.quest===0?'리나와 대화하기 · ↑':p.quest===1?'숲의 몬스터 '+Math.min(10,p.kills)+' / 10 · 리나에게 보고':p.quest===2?'유적에서 별지기 만나기 · 9,550m':p.quest===3?'추가 몬스터 '+Math.min(15,p.kills-p.claimed)+' / 15 · 별지기에게 보고':'모든 의뢰 완료! 자유롭게 탐험하세요';}
function spawn(x, index, ledge) {
  const area = region(x);
  const type = area >= 4 ? 2 : area >= 2 || ledge ? 1 : 0;
  const max = 4 + area * 3;
  mobs.push({
    x, y: ledge?.y ?? ground, home: x,
    left: ledge ? ledge.x + 16 : x - 130,
    right: ledge ? ledge.x + ledge.w - 16 : x + 130,
    dir: index % 2 ? 1 : -1, type, hp: max, max, dead: 0, phase: index * 1.7
  });
}
for (let i = 0, x = 1950; x < W - 200; x += 220, i++) spawn(x, i);
for (const [i, ledge] of platforms.slice(1).entries()) {
  if (i % 3 !== 0) spawn(Math.round(ledge.x + ledge.w * 0.6), i, ledge);
}
function textfx(text,x,y,col='#ffdc66'){fx.push({text,x,y,col,life:60})}
function reward(m){m.dead=400;const r=region(m.home);p.kills++;p.xp+=18+r*10;drops.push({x:m.x,y:m.y-15,gold:8+r*7,life:900});while(p.xp>=50+p.level*25){p.xp-=50+p.level*25;p.level++;p.hp=100;textfx('LEVEL UP!',p.x,p.y-100,'#fff5b0');beep(880);toast('레벨 '+p.level+'! 공격력이 오르고 체력이 회복되었어요.')}ui()}
function attack(skill = false) {
  if (!pixelReady || paused || dialog || map || swing || climbing || p.hurtUntil > tick) return;
  if (skill && skillCD > 0) return;
  if (skill) skillCD = 210;
  swing = {startTick: tick, direction: p.dir, skill, hasHit: false};
  beep(skill ? 420 : 370);
}

function advanceAttack() {
  if (!swing) return;
  const elapsed = (tick - swing.startTick) * STEP_MS;
  if (elapsed >= swingDuration) {
    swing = null;
    return;
  }
  if (swing.hasHit || elapsed < attackAnimation.durations[0]) return;
  swing.hasHit = true;

  const {skill, direction} = swing;
  beep(skill ? 760 : 510);
  for (const monster of mobs) {
    if (monster.dead) continue;
    const horizontal = monster.x - p.x;
    const vertical = Math.abs(monster.y - p.y);
    const inRange = skill
      ? Math.abs(horizontal) <= 175 && vertical <= 66
      : horizontal * direction >= -8 && horizontal * direction <= 54 && vertical <= 29;
    if (!inRange) continue;

    const impactDirection = skill ? Math.sign(horizontal) || direction : direction;
    const damage = skill ? 9 + p.level * 2 : 2 + p.level + Math.floor(Math.random() * 3);
    monster.hp -= damage;
    monster.x = Math.max(monster.left, Math.min(monster.right, monster.x + impactDirection * 9));
    monster.hitUntil = tick + 10;
    monster.hitDirection = impactDirection;
    textfx(String(damage), monster.x, monster.y - 46);
    if (monster.hp <= 0) {
      monster.deathAt = tick;
      reward(monster);
    }
  }
  if (skill) fx.push({ring: true, x: p.x, y: p.y - 23, col: '#bdf8ff', life: 30});
}

function jump() {
  if ((!p.grounded && !climbing) || paused || dialog || map) return;
  climbing = null;
  p.vy = -11.2;
  p.grounded = false;
  beep(300);
}

function travelTo(x) {
  swing = null;
  climbing = null;
  p.x = x;
  p.y = ground;
  p.vy = 0;
  p.grounded = true;
  walking = false;
  walkDistance = 0;
}
function close(){dialog=false;$('#dialog').hidden=true}function talk(n){dialog=true;$('#dialog').hidden=false;let text='',buttons=[];function btn(t,fn){buttons.push([t,fn])}
if(n.name==='리나'){if(p.quest===0){text='반가워요, 모험가님! 마을 밖 몬스터 10마리를 잡아주실래요? 보상은 150 메소와 물약 5개예요.';btn('의뢰 수락',()=>{p.quest=1;ui();save();close();toast('새 의뢰 · 마을 오른쪽 초원으로 출발하세요!')})}else if(p.quest===1&&p.kills>=10){text='덕분에 숲길이 안전해졌어요! 더 큰 모험을 원한다면 동쪽 달빛 유적에서 별지기를 만나보세요.';btn('보상 받기',()=>{p.gold+=150;p.pots+=5;p.quest=2;ui();save();close();toast('150 메소 + 물약 5개 획득!')})}else text='초원은 마을 오른쪽에 있어요. '+(p.quest===1?'몬스터 '+Math.min(p.kills,10)+' / 10마리 처치했네요.':'유적의 별지기가 당신을 기다려요.');}
if(n.name==='토비'){text='숲의 약초로 만든 물약이에요. 30 메소에 HP를 50 회복하는 물약 하나! 현재 '+p.gold+' 메소를 가지고 있군요.';btn('물약 구매 · 30 메소',()=>{if(p.gold>=30){p.gold-=30;p.pots++;ui();save();talk(n)}else toast('메소가 부족해요. 몬스터를 사냥해 보세요.')})}
if(n.name==='루카'){text='이곳은 초록 마을이에요. 동쪽으로 초원, 버섯 언덕, 깊은 숲, 달빛 유적이 이어져요. ↑ 키로 사다리를 오르고, X로 광역 스킬을 쓰세요. M은 지도, R은 마을 귀환이에요.';btn('유적까지 빠른 이동 · 80 메소',()=>{if(p.gold>=80){p.gold-=80;travelTo(9400);close();ui();save()}else toast('이동에는 80 메소가 필요해요.')})}
if(n.name==='별지기'){if(p.quest<2)text='유적에 오신 걸 환영해요. 초록 마을 리나의 의뢰부터 해결해 보세요.';else if(p.quest===2){text='이 오래된 숲에 평화를 되찾아주세요. 몬스터를 15마리 더 잡으면 400 메소와 물약 10개를 드릴게요.';btn('의뢰 수락',()=>{p.quest=3;p.claimed=p.kills;ui();save();close()})}else if(p.quest===3&&p.kills-p.claimed>=15){text='빛이 다시 돌아왔군요. 당신은 이 숲의 훌륭한 모험가예요.';btn('보상 받기',()=>{p.quest=4;p.gold+=400;p.pots+=10;ui();save();close();toast('유적 의뢰 완료! 400 메소 + 물약 10개')})}else text=p.quest===4?'언제든 이 숲을 자유롭게 여행하세요.':'몬스터를 '+(p.kills-p.claimed)+' / 15마리 처치했어요. 기다리고 있을게요.';}
$('#dialog').replaceChildren();let title=document.createElement('b');title.textContent=n.name+' · '+n.role;let para=document.createElement('p');para.textContent=text;$('#dialog').append(title,para);for(const [t,f]of buttons){let b=document.createElement('button');b.textContent=t;b.onclick=f;$('#dialog').append(b)}let b=document.createElement('button');b.textContent='닫기 · Esc';b.onclick=close;$('#dialog').append(b)}
function interact(){if(dialog){close();return}const n=npcs.find(n=>Math.abs(n.x-p.x)<75&&p.y>365);if(n)talk(n)}
function worldmap(){map=!map;$('#worldmap').hidden=!map;if(!map)return;$('#worldmap').innerHTML='<button id="mapclose">닫기 ×</button><b>WORLD MAP · 이어진 하나의 세계</b><p style="color:#7e8d74">현재 위치: '+regions[region(p.x)][0]+' / '+Math.floor(p.x)+'m</p><div class="mapline">'+regions.map((r,i)=>'<div style="'+(region(p.x)===i?'outline:3px solid #de9f65;':'')+'">'+['🏡','🌾','🍄','🌲','🌙'][i]+'<br>'+r[0]+'<br>'+r[1]+'m</div>').join('')+'</div><p>← 서쪽 마을 &nbsp; · &nbsp; 동쪽 유적 →</p><small>R 마을 귀환 · NPC 루카에게서 유적 빠른 이동 가능</small>';$('#mapclose').onclick=worldmap}
function potion(){if(p.pots&&p.hp<100){p.pots--;p.hp=Math.min(100,p.hp+50);textfx('HP +50',p.x,p.y-80,'#baf3a7');beep(660);ui();save()}else toast(p.pots?'체력이 가득 차 있어요.':'물약이 없어요. 마을의 토비에게 구매하세요.')}
function key(code){if(code==='Space')jump();if(code==='KeyZ')attack();if(code==='KeyX')attack(true);if(code==='ArrowUp')interact();if(code==='KeyM')worldmap();if(code==='Escape'){if(dialog)close();else if(map)worldmap()}if(code==='KeyK')toast(save()?'모험을 저장했어요.':'저장 공간을 사용할 수 없어요.');if(code==='KeyR'&&!dialog){travelTo(320);p.hp=100;ui();save();toast('초록 마을로 돌아왔어요.')}}
window.addEventListener('keydown',e=>{if(['ArrowLeft','ArrowRight','ArrowUp','ArrowDown','Space'].includes(e.code))e.preventDefault();keys[e.code]=true;if(!e.repeat)key(e.code)});window.addEventListener('keyup',e=>keys[e.code]=false);window.addEventListener('blur',()=>{keys={};save()});window.addEventListener('pagehide',save);
document.querySelectorAll('[data-key]').forEach(b=>{b.onpointerdown=e=>{e.preventDefault();b.setPointerCapture(e.pointerId);keys[b.dataset.key]=true;key(b.dataset.key)};b.onpointerup=b.onpointercancel=()=>keys[b.dataset.key]=false});$('#potion').onclick=potion;$('#pause').onclick=()=>{paused=!paused;$('#pause').textContent=paused?'▶ 계속하기':'Ⅱ 일시정지'};$('#sound').onclick=()=>{sound=!sound;$('#sound').textContent=sound?'♪ 소리 끄기':'♪ 소리 켜기';beep(600)};
function rect(x, y, width, height, color) {
  g.fillStyle = color;
  g.fillRect(Math.round(x), Math.round(y), Math.round(width), Math.round(height));
}

function movePlayer(dx) {
  const climbDirection = Number(Boolean(keys.ArrowDown)) - Number(Boolean(keys.ArrowUp));
  if (dx) climbing = null;
  if (!climbing && !dx && !swing && climbDirection && p.vy >= 0) {
    climbing = ladders.find(ladder => (
      Math.abs(p.x - ladder.x) <= 12 &&
      (climbDirection < 0 ? p.y > ladder.top && p.y <= ladder.bottom :
        p.y >= ladder.top && p.y < ladder.bottom)
    )) ?? null;
  }
  if (climbing) {
    p.x = climbing.x;
    p.y = Math.max(climbing.top, Math.min(climbing.bottom, p.y + climbDirection * 3.2));
    p.vy = 0;
    p.grounded = p.y === climbing.top || p.y === climbing.bottom;
    if (p.grounded) climbing = null;
    return;
  }

  p.x = Math.max(24, Math.min(W - 24, p.x + dx * (swing && p.grounded ? 2.4 : 4.2)));
  const oldY = p.y;
  p.vy += 0.5;
  p.y += p.vy;
  p.grounded = false;
  if (p.vy < 0) return;

  // Select the first surface crossed when several ledges overlap horizontally.
  let landing = Infinity;
  for (const {x, y, w} of platforms) {
    if (oldY <= y && p.y >= y && p.x >= x - 4 && p.x <= x + w + 4) {
      landing = Math.min(landing, y);
    }
  }
  if (landing !== Infinity) {
    p.y = landing;
    p.vy = 0;
    p.grounded = true;
  }
}

function moveMonsters() {
  for (const monster of mobs) {
    if (monster.dead) {
      if (--monster.dead === 0) {
        monster.hp = monster.max;
        monster.x = monster.home;
      }
      continue;
    }
    const speed = monster.type === 2 ? 0.8 : 0.5;
    monster.x += monster.dir * speed;
    if (monster.x <= monster.left || monster.x >= monster.right) {
      monster.x = Math.max(monster.left, Math.min(monster.right, monster.x));
      monster.dir *= -1;
    }
    if (inv || Math.abs(monster.x - p.x) >= 17 || Math.abs(monster.y - p.y) >= 23) continue;

    const damage = 5 + monster.type * 3;
    p.hp -= damage;
    inv = 70;
    p.hurtUntil = tick + 10;
    climbing = null;
    swing = null;
    p.vy = -4;
    p.grounded = false;
    textfx('-' + damage, p.x, p.y - 55, '#f2a6a0');
    beep(140);
    if (p.hp <= 0) {
      p.hp = 100;
      travelTo(320);
      toast('마을에서 회복했어요. 다시 출발해 볼까요?');
    }
    ui();
  }
}

function step() {
  if (!pixelReady) return;
  tick++;
  if (skillCD) skillCD--;
  if (inv) inv--;
  const dx = Number(Boolean(keys.ArrowRight)) - Number(Boolean(keys.ArrowLeft));
  if (dx && !swing) p.dir = dx;
  if (keys.KeyX) attack(true);
  if (keys.KeyZ) attack();
  const oldX = p.x;
  const oldY = p.y;
  movePlayer(dx);
  walking = p.grounded && Math.abs(p.x - oldX) > 0;
  if (walking || climbing) {
    walkDistance += Math.abs(p.x - oldX) + Math.abs(p.y - oldY);
  } else {
    walkDistance = 0;
  }
  advanceAttack();
  moveMonsters();

  for (const drop of drops) {
    drop.life--;
    if (Math.abs(drop.x - p.x) < 33 && Math.abs(drop.y - p.y) < 38) {
      p.gold += drop.gold;
      drop.life = 0;
      textfx('+' + drop.gold + ' 메소', p.x, p.y - 42, '#fff3a2');
      ui();
    }
  }
  drops = drops.filter(drop => drop.life > 0);
  fx = fx.filter(effect => --effect.life > 0);
  for (const effect of fx) if (!effect.ring) effect.y -= 0.55;
  camera = Math.max(0, Math.min(W - 960, p.x - 480));
  const area = region(p.x);
  if (area !== lastRegion) {
    lastRegion = area;
    $('#region').textContent = ['🏡 ', '🌾 ', '🍄 ', '🌲 ', '🌙 '][area] + regions[area][0];
    if (tick > 2) toast(regions[area][0] + '에 도착했어요.');
  }
  if (++autosave > 600) {
    autosave = 0;
    save();
  }
}

function draw(){background();mobs.forEach(drawMob);for(const d of drops)if(d.x>camera-30&&d.x<camera+990){rect(d.x-camera-5,d.y-8+Math.sin(tick*.09)*2,10,9,'#b68c3e');rect(d.x-camera-3,d.y-7+Math.sin(tick*.09)*2,6,6,'#f3d06a')}drawPlayer();for(const f of fx){g.globalAlpha=Math.min(1,f.life/15);if(f.ring){g.strokeStyle=f.col;g.lineWidth=4;g.beginPath();g.ellipse(f.x-camera,f.y,30+(30-f.life)*7,50,0,0,Math.PI*2);g.stroke()}else{g.font='bold 20px sans-serif';g.textAlign='center';g.strokeStyle='#805c42';g.lineWidth=3;g.strokeText(f.text,f.x-camera,f.y);g.fillStyle=f.col;g.fillText(f.text,f.x-camera,f.y)}}g.globalAlpha=1;g.textAlign='left';rect(755,87,185,42,'#f7f4dfcc');g.fillStyle='#647555';g.font='10px sans-serif';g.fillText(Math.floor(p.x)+' m / 12,000 m · '+(skillCD?'스킬 '+(skillCD/60).toFixed(1)+'초':'X 스킬 준비'),765,102);rect(766,113,162,4,'#c5ceae');rect(766+p.x/W*158,110,5,10,'#d49c63');if(paused){rect(0,0,960,468,'#253d4666');g.fillStyle='#fff5dc';g.textAlign='center';g.font='26px sans-serif';g.fillText('잠깐 쉬어가는 중',480,234);g.textAlign='left'}}
function loop(t){acc+=Math.min(80,t-last);last=t;while(acc>=STEP_MS){if(!paused&&!dialog&&!map)step();acc-=STEP_MS}draw();requestAnimationFrame(loop)}ui();camera=Math.max(0,Math.min(W-960,p.x-480));toast('↑ 리나와 대화해 첫 의뢰를 시작하세요 · M 지도');requestAnimationFrame(loop);
