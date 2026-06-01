#!/usr/bin/env python3
"""
generate_play.py — emit a self-contained, playable browser port of Ashen Vigil.

Fidelity: reads the same constants and level map out of the Swift source (via
neon_sim.spec) that the iOS game and the test harness use, AND embeds the real
generated PNG art (Art/out/*.png, base64) so the single play.html stays
self-contained while showing the actual gothic sprites + parallax backdrop.

    cd NeonCitadel/Art && python3 generate_art.py     # (re)build art first
    cd NeonCitadel/WebPlaytest && python3 generate_play.py
    # then open play.html in any browser (phone or desktop)

This is a faithful *reimplementation* of the deterministic gameplay (physics,
double-jump, ability gate, stomp/damage), NOT the literal SpriteKit build.
"""

from __future__ import annotations

import base64
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "TestHarness"))

from neon_sim import spec  # noqa: E402

ART_DIR = HERE.parent / "Art" / "out"


def build_config() -> dict:
    s = spec.load_spec()
    level = spec.load_level_map()
    return {
        "moveSpeed": s.move_speed,
        "jumpVelocity": s.jump_velocity,
        "gravity": s.gravity,
        "stompBounce": s.stomp_bounce,
        "tileSize": s.tile_size,
        "maxHealth": s.max_health,
        "apexTiles": round(s.jump_apex_tiles, 3),
        "level": level,
        "cols": len(level[0]),
        "rows": len(level),
    }


def build_art() -> dict:
    """base64 data-URIs for every generated PNG, keyed by stem."""
    art = {}
    if ART_DIR.is_dir():
        for png in sorted(ART_DIR.glob("*.png")):
            b64 = base64.b64encode(png.read_bytes()).decode()
            art[png.stem] = f"data:image/png;base64,{b64}"
    return art


def render_html(config: dict, art: dict) -> str:
    return (HTML_TEMPLATE
            .replace("/*__CONFIG__*/", json.dumps(config, indent=2))
            .replace("/*__ART__*/", json.dumps(art)))


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no, viewport-fit=cover">
<title>Ashen Vigil</title>
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="Ashen Vigil">
<meta name="theme-color" content="#080a16">
<link rel="apple-touch-icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='180' height='180'%3E%3Crect width='180' height='180' fill='%23080a16'/%3E%3Ccircle cx='90' cy='84' r='46' fill='%235a96e6'/%3E%3Ccircle cx='90' cy='84' r='16' fill='%23e04078'/%3E%3Crect x='30' y='150' width='120' height='10' fill='%232c2a4a'/%3E%3C/svg%3E">
<style>
  * { margin:0; padding:0; box-sizing:border-box; -webkit-tap-highlight-color:transparent; }
  html,body { height:100%; background:#080a16; overflow:hidden;
    font-family:ui-monospace,Menlo,Consolas,monospace; color:#e0b048;
    touch-action:none; -webkit-user-select:none; user-select:none; }
  #wrap { position:fixed; inset:0; display:flex; align-items:center; justify-content:center; }
  canvas { width:100%; height:100%; display:block; image-rendering:pixelated; }
  #hint { position:fixed; top:6px; left:50%; transform:translateX(-50%);
    font-size:11px; color:#e0b04899; letter-spacing:1px; pointer-events:none; z-index:5; }
  .pad { position:fixed; bottom:max(18px,env(safe-area-inset-bottom)); z-index:10; display:flex; gap:14px; }
  #padL { left:max(18px,env(safe-area-inset-left)); }
  #padR { right:max(18px,env(safe-area-inset-right)); }
  .btn { width:64px; height:64px; border-radius:50%;
    border:2px solid #e0b048cc; background:#ffffff10; color:#e0b048;
    font-size:26px; display:flex; align-items:center; justify-content:center; backdrop-filter:blur(2px); }
  .btn:active, .btn.on { background:#96182855; }
  #attack { border-color:#ce2c3ccc; color:#ff96c4; }
  @media (pointer:fine){ .pad{ opacity:0.5 } }
</style>
</head>
<body>
<div id="hint">◀ ▶ / A D move · ▲ / W / Space jump (×2 after the relic) · ✦ / J strike · R restart</div>
<div id="wrap"><canvas id="c"></canvas></div>
<div class="pad" id="padL">
  <div class="btn" data-k="left">◀</div>
  <div class="btn" data-k="right">▶</div>
</div>
<div class="pad" id="padR">
  <div class="btn" id="attack" data-k="attack">✦</div>
  <div class="btn" data-k="jump">▲</div>
</div>
<script>
"use strict";
const CFG = /*__CONFIG__*/;
const ART_SRC = /*__ART__*/;

const TILE = CFG.tileSize;
const GRAV = Math.abs(CFG.gravity);
const JUMP_V = CFG.jumpVelocity;
const MOVE = CFG.moveSpeed;
const BOUNCE = CFG.stompBounce;
const COLS = CFG.cols, ROWS = CFG.rows;
const WORLD_W = COLS * TILE, WORLD_H = ROWS * TILE;

// Gothic palette (mirrors Systems/Palette.swift after the retheme).
const COL = {
  void:"#080a16", night:"#1a1e42", stone:"#2c2a4a", stoneDark:"#1c1a30",
  crimson:"#96182 8".replace(" ",""), crimsonLite:"#ce2c3c",
  gold:"#e0b048", goldLite:"#ffe08a", candle:"#ffc46e",
  rose:"#e04078", health:"#ce2c3c", healthEmpty:"#2c2a4a",
};

// --- Load art (real generated PNGs, base64). Sprites render when ready;
//     until then a procedural fallback keeps the game visible. ---
const ART = {}; let artReady=0, artTotal=0;
for(const k in ART_SRC){ artTotal++; const im=new Image();
  im.onload=()=>{artReady++;}; im.src=ART_SRC[k]; ART[k]=im; }
function haveArt(){ return artTotal>0 && artReady>=artTotal; }

function cellCenter(col,row){ return { x:(col+0.5)*TILE, y:(ROWS-1-row+0.5)*TILE }; }

// --- Parse level ---
const solids=[]; const solidSet=new Set();
let spawn=null, pickup=null, door=null, goal=null; const enemies=[];
for(let r=0;r<ROWS;r++){ const line=CFG.level[r];
  for(let c=0;c<line.length;c++){ const ch=line[c];
    if(ch==='X'){ solids.push({col:c,row:r}); solidSet.add(c+','+r); }
    else if(ch==='P'){ spawn=cellCenter(c,r); }
    else if(ch==='C'){ pickup={...cellCenter(c,r), got:false}; }
    else if(ch==='D'){ door={...cellCenter(c,r), col:c, row:r, open:false}; }
    else if(ch==='G'){ goal=cellCenter(c,r); }
    else if(ch==='E'){ const p=cellCenter(c,r);
      enemies.push({x:p.x,y:p.y,dir:1,minX:p.x-TILE*2.5,maxX:p.x+TILE*2.5,w:TILE*0.9,h:TILE*0.7,alive:true}); }
  }
}
function isSolid(col,row){ return solidSet.has(col+','+row); }

// --- Player ---
const PW = TILE*0.6, PH = TILE*0.95;
const player = { x:spawn.x, y:spawn.y, vx:0, vy:0, onGround:false, hasDouble:false, jumps:0, face:1, hp:CFG.maxHealth, invuln:0, anim:0 };

// --- Input ---
const keys = { left:false, right:false, jump:false, attack:false };
const held = { jump:false, attack:false };
function bindKey(e,down){ const k=e.key.toLowerCase();
  if(k==='arrowleft'||k==='a'){ keys.left=down; }
  else if(k==='arrowright'||k==='d'){ keys.right=down; }
  else if(k==='arrowup'||k==='w'||k===' '){ keys.jump=down; e.preventDefault(); }
  else if(k==='j'||k==='f'){ keys.attack=down; }
  else if(k==='r'&&down){ reset(); }
}
addEventListener('keydown',e=>bindKey(e,true));
addEventListener('keyup',e=>bindKey(e,false));
document.querySelectorAll('.btn').forEach(b=>{ const k=b.dataset.k;
  const set=(v)=>{ keys[k]=v; b.classList.toggle('on',v); };
  b.addEventListener('touchstart',e=>{e.preventDefault();set(true);},{passive:false});
  b.addEventListener('touchend',  e=>{e.preventDefault();set(false);},{passive:false});
  b.addEventListener('touchcancel',e=>{set(false);});
  b.addEventListener('mousedown', e=>{e.preventDefault();set(true);});
  b.addEventListener('mouseup',   e=>set(false));
  b.addEventListener('mouseleave',e=>set(false));
});

// --- Effects ---
const fx=[]; function puff(x,y,color,r=14){ fx.push({x,y,r,life:0.3,max:0.3,color}); }
let banner=null; function showBanner(text,color){ banner={text,color,life:2.0}; }
let state="play"; let slash=null;

function reset(){
  player.x=spawn.x; player.y=spawn.y; player.vx=0; player.vy=0;
  player.onGround=false; player.hasDouble=false; player.jumps=0;
  player.hp=CFG.maxHealth; player.invuln=0; player.face=1;
  if(pickup) pickup.got=false; if(door) door.open=false;
  enemies.forEach(e=>{ e.alive=true; e.x=(e.minX+e.maxX)/2; e.dir=1; });
  fx.length=0; banner=null; slash=null; state="play";
}

function moveAndCollide(dt){
  const w=PW,h=PH, half_w=w/2, half_h=h/2;
  function blocked(col,row){ if(isSolid(col,row)) return true;
    if(door && !door.open){ if(col===door.col && (row===door.row || row===door.row-1)) return true; }
    return false; }
  player.x += player.vx*dt;
  { const c0=Math.floor((player.x-half_w)/TILE), c1=Math.floor((player.x+half_w)/TILE);
    const rTop=ROWS-1-Math.floor((player.y+half_h-1)/TILE);
    const rBot=ROWS-1-Math.floor((player.y-half_h+1)/TILE);
    for(let c=c0;c<=c1;c++) for(let r=rTop;r<=rBot;r++){ if(!blocked(c,r)) continue;
      const cx=(c+0.5)*TILE;
      if(player.vx>0){ player.x=Math.min(player.x, cx-TILE/2-half_w); }
      else if(player.vx<0){ player.x=Math.max(player.x, cx+TILE/2+half_w); } } }
  player.y += player.vy*dt; player.onGround=false;
  { const c0=Math.floor((player.x-half_w+1)/TILE), c1=Math.floor((player.x+half_w-1)/TILE);
    const rTop=ROWS-1-Math.floor((player.y+half_h)/TILE);
    const rBot=ROWS-1-Math.floor((player.y-half_h)/TILE);
    for(let c=c0;c<=c1;c++) for(let r=rTop;r<=rBot;r++){ if(!blocked(c,r)) continue;
      const cy=(ROWS-1-r+0.5)*TILE;
      if(player.vy<0){ player.y=Math.max(player.y, cy+TILE/2+half_h); player.vy=0; player.onGround=true; }
      else if(player.vy>0){ player.y=Math.min(player.y, cy-TILE/2-half_h); player.vy=0; } } }
}

function tryJump(){ if(player.onGround) player.jumps = player.hasDouble?2:1;
  if(player.jumps<=0) return; player.jumps--; player.onGround=false; player.vy=JUMP_V;
  if(player.jumps===0 && player.hasDouble) puff(player.x,player.y-PH/2,COL.gold,18); }

function doAttack(){ slash={ x:player.x+player.face*PW, y:player.y, life:0.12, face:player.face };
  const reach=TILE*0.9;
  for(const e of enemies){ if(!e.alive) continue;
    if(Math.abs(e.x-slash.x)<reach && Math.abs(e.y-slash.y)<PH*0.9){ e.alive=false; puff(e.x,e.y,COL.crimsonLite,18); } } }

function update(dt){
  if(state!=="play"){ if(keys.jump && !held.jump){ held.jump=true; if(state!=="play") reset(); }
    if(!keys.jump) held.jump=false; if(banner) banner.life-=dt; return; }
  const dir=(keys.right?1:0)-(keys.left?1:0);
  player.vx = dir*MOVE; if(dir>0) player.face=1; else if(dir<0) player.face=-1;
  player.anim += Math.abs(dir)*dt*10;
  if(keys.jump && !held.jump){ held.jump=true; tryJump(); }
  if(!keys.jump) held.jump=false;
  if(keys.attack && !held.attack){ held.attack=true; doAttack(); }
  if(!keys.attack) held.attack=false;
  player.vy -= GRAV*dt; moveAndCollide(dt);
  for(const e of enemies){ if(!e.alive) continue; e.x += e.dir*90*dt;
    if(e.x>=e.maxX){ e.dir=-1; } else if(e.x<=e.minX){ e.dir=1; } }
  if(pickup && !pickup.got){ if(Math.abs(player.x-pickup.x)<TILE*0.7 && Math.abs(player.y-pickup.y)<TILE*0.7){
      pickup.got=true; player.hasDouble=true; player.jumps=Math.max(player.jumps,1);
      puff(pickup.x,pickup.y,COL.gold,22); showBanner("RELIC OF THE TWICE-RISEN", COL.gold); } }
  if(door && !door.open){ if(Math.abs(player.x-door.x)<TILE*1.2 && Math.abs(player.y-door.y)<TILE*1.4){
      if(player.hasDouble){ door.open=true; puff(door.x,door.y,COL.rose,26); showBanner("GATE UNSEALED",COL.rose); }
      else { showBanner("SEALED — SEEK THE RELIC", COL.crimsonLite); } } }
  if(goal && Math.abs(player.x-goal.x)<TILE*0.7 && Math.abs(player.y-goal.y)<TILE*0.8){ state="win"; showBanner("VIGIL COMPLETE", COL.goldLite||COL.gold); }
  if(player.invuln>0) player.invuln-=dt;
  for(const e of enemies){ if(!e.alive) continue;
    if(Math.abs(player.x-e.x)<(PW/2+e.w/2) && Math.abs(player.y-e.y)<(PH/2+e.h/2)){
      const stomping = player.vy<0 && player.y > e.y + e.h*0.2;
      if(stomping){ e.alive=false; player.vy=BOUNCE; puff(e.x,e.y,COL.crimsonLite,18); }
      else if(player.invuln<=0){ player.hp--; player.invuln=1.0;
        player.vx = (player.x<e.x?-1:1)*320; player.vy=520;
        if(player.hp<=0){ state="dead"; showBanner("FALLEN", COL.crimsonLite); } } } }
  if(player.y < -TILE){ player.hp--; player.invuln=1.0;
    if(player.hp<=0){ state="dead"; showBanner("FALLEN", COL.crimsonLite); }
    else { player.x=spawn.x; player.y=spawn.y; player.vx=player.vy=0; } }
  for(let i=fx.length-1;i>=0;i--){ fx[i].life-=dt; if(fx[i].life<=0) fx.splice(i,1); }
  if(slash){ slash.life-=dt; if(slash.life<=0) slash=null; }
  if(banner){ banner.life-=dt; if(banner.life<=0) banner=null; }
}

// === Rendering ===
const canvas=document.getElementById('c'); const ctx=canvas.getContext('2d');
let VW=0, VH=0, DPR=1;
function resize(){ DPR=Math.min(devicePixelRatio||1, 2); VW=innerWidth; VH=innerHeight;
  canvas.width=Math.floor(VW*DPR); canvas.height=Math.floor(VH*DPR);
  ctx.setTransform(DPR,0,0,DPR,0,0); ctx.imageSmoothingEnabled=false; }
addEventListener('resize',resize); resize();

function camera(){ const scale = VH / (Math.min(WORLD_H, 12*TILE));
  const viewW = VW/scale, viewH=VH/scale; let cx=player.x, cy=player.y;
  cx=Math.max(viewW/2, Math.min(WORLD_W-viewW/2, cx));
  cy=Math.max(viewH/2, Math.min(WORLD_H-viewH/2, cy));
  if(WORLD_W<viewW) cx=WORLD_W/2; if(WORLD_H<viewH) cy=WORLD_H/2;
  return {scale,cx,cy,viewW,viewH}; }
function worldToScreen(wx,wy,cam){ const sx=(wx-(cam.cx-cam.viewW/2))*cam.scale;
  const sy=VH-(wy-(cam.cy-cam.viewH/2))*cam.scale; return [sx,sy]; }

// Parallax backdrop: layers scroll at fractions of the camera, cover-fit to screen.
function drawLayer(im, cam, factor){
  if(!im || !im.width){ return false; }
  const scale = Math.max(VW/im.width, VH/im.height);
  const dw=im.width*scale, dh=im.height*scale;
  const maxScroll = WORLD_W - cam.viewW;
  const t = maxScroll>0 ? (cam.cx-cam.viewW/2)/maxScroll : 0; // 0..1
  const ox = -(t*factor)*(dw-VW);
  ctx.drawImage(im, ox, VH-dh, dw, dh);
  return true;
}
function drawBackground(cam){
  if(haveArt()){
    ctx.fillStyle=COL.void; ctx.fillRect(0,0,VW,VH);
    drawLayer(ART.bg_sky,cam,0.10);
    drawLayer(ART.bg_spires,cam,0.30);
    drawLayer(ART.bg_window,cam,0.55);
    drawLayer(ART.bg_pillars,cam,0.85);
    // decorative boss sentinel standing at the far right of the hall
    if(ART.boss && ART.boss.width){ const [bx,by]=worldToScreen(WORLD_W-TILE*3, TILE*4, cam);
      const s=cam.scale*1.4; ctx.drawImage(ART.boss, bx-ART.boss.width*s/2, by-ART.boss.height*s, ART.boss.width*s, ART.boss.height*s); }
  } else {
    const g=ctx.createLinearGradient(0,0,0,VH); g.addColorStop(0,COL.void); g.addColorStop(1,COL.night);
    ctx.fillStyle=g; ctx.fillRect(0,0,VW,VH);
  }
}

// Blit a sub-rect of a sprite sheet at a world position (centered, +y up).
function blit(im, sx,sy,sw,sh, wx,wy, cam, flip){
  const [px,py]=worldToScreen(wx,wy,cam);
  const dw=sw*cam.scale, dh=sh*cam.scale;
  ctx.save(); ctx.translate(px,py); if(flip) ctx.scale(-1,1);
  ctx.drawImage(im, sx,sy,sw,sh, -dw/2,-dh/2, dw,dh); ctx.restore();
}

function draw(){
  const cam=camera(); drawBackground(cam);

  // Tiles (sprite if available, else colored block)
  const useArt=haveArt();
  for(const t of solids){ const ctr=cellCenter(t.col,t.row); const [sx,sy]=worldToScreen(ctr.x,ctr.y,cam); const s=TILE*cam.scale;
    if(useArt && ART.tiles && ART.tiles.width){ const top=!isSolid(t.col,t.row-1);
      const idx=top?1:0; ctx.drawImage(ART.tiles, idx*16,0,16,16, sx-s/2,sy-s/2, s,s); }
    else { ctx.fillStyle=COL.stone; ctx.fillRect(sx-s/2,sy-s/2,s,s); ctx.fillStyle=COL.stoneDark; ctx.fillRect(sx-s/2+2,sy-s/2+2,s-4,s-4); } }

  // Goal portal glow
  if(goal){ const [sx,sy]=worldToScreen(goal.x,goal.y,cam); const r=TILE*0.6*cam.scale;
    const g=ctx.createRadialGradient(sx,sy,0,sx,sy,r); g.addColorStop(0,COL.goldLite||"#ffe08a"); g.addColorStop(1,"#e0b04800");
    ctx.fillStyle=g; ctx.beginPath(); ctx.arc(sx,sy,r,0,7); ctx.fill();
    ctx.strokeStyle=COL.gold; ctx.lineWidth=2; ctx.beginPath(); ctx.arc(sx,sy,r*0.5,0,7); ctx.stroke(); }

  // Door (closed): sealed gate bars
  if(door && !door.open){ const [sx,sy]=worldToScreen(door.x,door.y,cam);
    const w=TILE*0.6*cam.scale, h=TILE*2.2*cam.scale;
    ctx.fillStyle=COL.stoneDark; ctx.fillRect(sx-w/2,sy-h/2,w,h);
    ctx.strokeStyle=COL.gold; ctx.lineWidth=2; ctx.strokeRect(sx-w/2,sy-h/2,w,h);
    ctx.fillStyle=COL.crimsonLite; for(let i=0;i<4;i++){ const yy=sy-h/2+8+i*(h-16)/3; ctx.fillRect(sx-w*0.35,yy,w*0.7,4); } }

  // Pickup relic
  if(pickup && !pickup.got){ const bob=Math.sin(performance.now()/300)*4;
    if(useArt && ART.pickup && ART.pickup.width){ blit(ART.pickup,0,0,12,12, pickup.x,pickup.y+bob, cam, false); }
    else { const [sx,sy]=worldToScreen(pickup.x,pickup.y+bob,cam); ctx.fillStyle=COL.gold; ctx.fillRect(sx-6,sy-6,12,12); } }

  // Enemies
  for(const e of enemies){ if(!e.alive) continue;
    if(useArt && ART.enemy && ART.enemy.width){ const fr=(Math.floor(performance.now()/250)%2);
      blit(ART.enemy, fr*16,0,16,18, e.x,e.y, cam, e.dir<0); }
    else { const [sx,sy]=worldToScreen(e.x,e.y,cam); ctx.fillStyle=COL.crimsonLite; ctx.fillRect(sx-e.w*cam.scale/2,sy-e.h*cam.scale/2,e.w*cam.scale,e.h*cam.scale); } }

  // Slash
  if(slash){ const [sx,sy]=worldToScreen(slash.x,slash.y,cam);
    ctx.strokeStyle=COL.goldLite||"#ffe08a"; ctx.lineWidth=3; ctx.globalAlpha=slash.life/0.12;
    ctx.beginPath(); ctx.arc(sx,sy,TILE*0.5*cam.scale,-0.6,0.9); ctx.stroke(); ctx.globalAlpha=1; }

  // Player (sprite frame from 6-frame sheet)
  if(!(player.invuln>0 && Math.floor(performance.now()/80)%2)){
    if(useArt && ART.player && ART.player.width){
      let frame=0; // idle
      if(!player.onGround) frame=5;            // jump
      else if(Math.abs(player.vx)>1) frame=2+(Math.floor(player.anim)%3); // run 2..4
      else frame=(Math.floor(performance.now()/500)%2); // idle 0..1
      blit(ART.player, frame*16,0,16,24, player.x,player.y, cam, player.face<0);
    } else { const [sx,sy]=worldToScreen(player.x,player.y,cam); const w=PW*cam.scale,h=PH*cam.scale;
      ctx.fillStyle=COL.crimson; ctx.fillRect(sx-w/2,sy-h/2,w,h); }
  }

  // FX
  for(const f of fx){ const [sx,sy]=worldToScreen(f.x,f.y,cam);
    ctx.globalAlpha=f.life/f.max; ctx.fillStyle=f.color;
    ctx.beginPath(); ctx.arc(sx,sy,f.r*cam.scale*(1.4-f.life/f.max),0,7); ctx.fill(); ctx.globalAlpha=1; }

  // HUD health
  for(let i=0;i<CFG.maxHealth;i++){ ctx.fillStyle = i<player.hp ? COL.health : COL.healthEmpty; ctx.fillRect(16+i*22, 16, 16, 16); }
  ctx.strokeStyle = player.hasDouble?COL.gold:COL.healthEmpty; ctx.lineWidth=2; ctx.strokeRect(16+CFG.maxHealth*22+8, 16, 16, 16);

  if(banner){ ctx.globalAlpha=Math.min(1, banner.life); ctx.fillStyle=banner.color;
    ctx.font="bold 30px ui-monospace,monospace"; ctx.textAlign="center";
    ctx.fillText(banner.text, VW/2, VH*0.30); ctx.globalAlpha=1;
    if(state!=="play"){ ctx.fillStyle=COL.gold; ctx.font="16px ui-monospace,monospace"; ctx.fillText("press ▲ / Space / R to begin again", VW/2, VH*0.30+34); }
    ctx.textAlign="left"; }
}

let last=performance.now();
function frame(now){ let dt=(now-last)/1000; last=now; dt=Math.min(dt, 1/30); update(dt); draw(); requestAnimationFrame(frame); }
requestAnimationFrame(frame);
</script>
</body>
</html>
"""


def main() -> int:
    config = build_config()
    art = build_art()
    html = render_html(config, art)
    out = HERE / "play.html"
    out.write_text(html, encoding="utf-8")
    print(f"Wrote {out} ({len(html):,} bytes)")
    print(f"Level {config['cols']}x{config['rows']}, jump apex {config['apexTiles']} tiles, "
          f"{config['maxHealth']} HP. Art images embedded: {len(art)}.")
    if not art:
        print("WARNING: no art found in Art/out — run Art/generate_art.py first "
              "(the game will use the procedural fallback).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
