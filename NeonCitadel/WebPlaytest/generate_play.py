#!/usr/bin/env python3
"""
generate_play.py — emit a self-contained, playable browser port of Neon Citadel.

The point of this file is *fidelity*: it reads the same constants and level map
out of the Swift source (via neon_sim.spec) that the iOS game and the test
harness use, then bakes them into a single standalone play.html. Run it after
changing any tunable or the level, and the web playtest re-syncs automatically.

    cd NeonCitadel/WebPlaytest
    python3 generate_play.py          # writes play.html next to this script
    # then open play.html in any browser (phone or desktop)

This is a faithful *reimplementation* of the deterministic gameplay (physics,
double-jump, ability gate, stomp/damage), NOT the literal SpriteKit build — it's
for testing feel and design without a Mac. Rendering is canvas 2D with a
synthwave look approximating the SpriteKit visuals.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
# WebPlaytest/ -> NeonCitadel/ ; the harness package lives in TestHarness/
sys.path.insert(0, str(HERE.parent / "TestHarness"))

from neon_sim import spec  # noqa: E402


def build_config() -> dict:
    s = spec.load_spec()
    level = spec.load_level_map()
    return {
        "moveSpeed": s.move_speed,
        "jumpVelocity": s.jump_velocity,
        "gravity": s.gravity,          # negative = downward (we flip in JS world)
        "stompBounce": s.stomp_bounce,
        "tileSize": s.tile_size,
        "maxHealth": s.max_health,
        "apexTiles": round(s.jump_apex_tiles, 3),
        "level": level,
        "cols": len(level[0]),
        "rows": len(level),
    }


def render_html(config: dict) -> str:
    cfg_json = json.dumps(config, indent=2)
    return HTML_TEMPLATE.replace("/*__CONFIG__*/", cfg_json)


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no, viewport-fit=cover">
<title>Neon Citadel</title>
<!-- iOS "Add to Home Screen": launch full-screen like a native app. -->
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="Neon Citadel">
<meta name="theme-color" content="#0b0618">
<!-- Home-screen icon: a tiny inline SVG (neon citadel sun), no extra files. -->
<link rel="apple-touch-icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='180' height='180'%3E%3Crect width='180' height='180' fill='%230b0618'/%3E%3Ccircle cx='90' cy='96' r='52' fill='%23ff69b4'/%3E%3Crect x='38' y='96' width='104' height='6' fill='%230b0618'/%3E%3Crect x='38' y='110' width='104' height='8' fill='%230b0618'/%3E%3Crect x='38' y='126' width='104' height='10' fill='%230b0618'/%3E%3Crect x='20' y='150' width='140' height='8' fill='%232de3e3'/%3E%3C/svg%3E">
<style>
  :root { --cyan:#2de3e3; --pink:#ff69b4; }
  * { margin:0; padding:0; box-sizing:border-box; -webkit-tap-highlight-color:transparent; }
  html,body { height:100%; background:#0b0618; overflow:hidden;
    font-family:ui-monospace,Menlo,Consolas,monospace; color:var(--cyan);
    touch-action:none; -webkit-user-select:none; user-select:none; }
  #wrap { position:fixed; inset:0; display:flex; align-items:center; justify-content:center; }
  canvas { width:100%; height:100%; display:block; image-rendering:pixelated; }
  #hint { position:fixed; top:6px; left:50%; transform:translateX(-50%);
    font-size:11px; color:#2de3e3aa; letter-spacing:1px; pointer-events:none; z-index:5; }
  /* On-screen controls */
  .pad { position:fixed; bottom:max(18px,env(safe-area-inset-bottom)); z-index:10;
    display:flex; gap:14px; }
  #padL { left:max(18px,env(safe-area-inset-left)); }
  #padR { right:max(18px,env(safe-area-inset-right)); }
  .btn { width:64px; height:64px; border-radius:50%;
    border:2px solid #2de3e3d9; background:#ffffff12; color:var(--cyan);
    font-size:26px; display:flex; align-items:center; justify-content:center;
    backdrop-filter:blur(2px); }
  .btn:active, .btn.on { background:#2de3e359; }
  #attack { border-color:#ff69b4d9; color:var(--pink); }
  @media (pointer:fine){ .pad{ opacity:0.5 } }
</style>
</head>
<body>
<div id="hint">◀ ▶ / A D move · ▲ / W / Space jump (×2 after the core) · ✦ / J attack · R restart</div>
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
// === Config baked from the Swift source (do not edit by hand; see generate_play.py) ===
const CFG = /*__CONFIG__*/;

const TILE = CFG.tileSize;
const GRAV = Math.abs(CFG.gravity);     // downward magnitude, +y is up in world space
const JUMP_V = CFG.jumpVelocity;
const MOVE = CFG.moveSpeed;
const BOUNCE = CFG.stompBounce;
const COLS = CFG.cols, ROWS = CFG.rows;
const WORLD_W = COLS * TILE, WORLD_H = ROWS * TILE;

// Palette (mirrors Systems/Palette.swift)
const COL = {
  bg0:"#0b0618", bg1:"#260a2e", bgN:"#260a4a",
  sun:"#ff69b4", sunCore:"#ffc64c", grid:"#2de3e3",
  tile:"#1f1841", tileEdge:"#7339d4",
  player:"#49f2ca", playerDark:"#1c7e73", visor:"#ff4c8a",
  enemy:"#ff4557", enemyDark:"#8a1c2b", enemyEye:"#ffe566",
  pickup:"#ffc64c", door:"#7339d4", doorLock:"#ff69b4",
  health:"#ff4473", healthEmpty:"#3c1e4a",
};

// World coords: origin bottom-left, +y up (matches SpriteKit / Level.position()).
// Grid row 0 is the TOP, so worldY for a cell center = (ROWS-1-row+0.5)*TILE.
function cellCenter(col,row){ return { x:(col+0.5)*TILE, y:(ROWS-1-row+0.5)*TILE }; }

// --- Parse level into solids + entities ---
const solids = [];                 // {col,row} of 'X'
const solidSet = new Set();
let spawn=null, pickup=null, door=null, goal=null;
const enemies=[];
for(let r=0;r<ROWS;r++){
  const line=CFG.level[r];
  for(let c=0;c<line.length;c++){
    const ch=line[c];
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
const player = {
  x:spawn.x, y:spawn.y, vx:0, vy:0,
  onGround:false, hasDouble:false, jumps:0, face:1,
  hp:CFG.maxHealth, invuln:0,
};

// --- Input ---
const keys = { left:false, right:false, jump:false, attack:false };
const held = { jump:false, attack:false };   // edge-detect for jump/attack
function bindKey(e,down){
  const k=e.key.toLowerCase();
  if(k==='arrowleft'||k==='a'){ keys.left=down; }
  else if(k==='arrowright'||k==='d'){ keys.right=down; }
  else if(k==='arrowup'||k==='w'||k===' '){ keys.jump=down; e.preventDefault(); }
  else if(k==='j'||k==='f'){ keys.attack=down; }
  else if(k==='r'&&down){ reset(); }
}
addEventListener('keydown',e=>bindKey(e,true));
addEventListener('keyup',e=>bindKey(e,false));
document.querySelectorAll('.btn').forEach(b=>{
  const k=b.dataset.k;
  const set=(v)=>{ keys[k]=v; b.classList.toggle('on',v); };
  b.addEventListener('touchstart',e=>{e.preventDefault();set(true);},{passive:false});
  b.addEventListener('touchend',  e=>{e.preventDefault();set(false);},{passive:false});
  b.addEventListener('touchcancel',e=>{set(false);});
  b.addEventListener('mousedown', e=>{e.preventDefault();set(true);});
  b.addEventListener('mouseup',   e=>set(false));
  b.addEventListener('mouseleave',e=>set(false));
});

// --- Effects (transient) ---
const fx=[];        // {x,y,r,life,max,color,vy?}
function puff(x,y,color,r=14){ fx.push({x,y,r,life:0.3,max:0.3,color}); }
let banner=null;    // {text,color,life}
function showBanner(text,color){ banner={text,color,life:2.0}; }

let state="play";   // play | win | dead
let slash=null;     // {x,y,life,face}

function reset(){
  player.x=spawn.x; player.y=spawn.y; player.vx=0; player.vy=0;
  player.onGround=false; player.hasDouble=false; player.jumps=0;
  player.hp=CFG.maxHealth; player.invuln=0; player.face=1;
  if(pickup) pickup.got=false;
  if(door) door.open=false;
  enemies.forEach(e=>{ e.alive=true; e.x=(e.minX+e.maxX)/2; e.dir=1; });
  fx.length=0; banner=null; slash=null; state="play";
}

// --- Physics helpers: AABB vs tile grid, axis-separated ---
function aabbVsSolids(nx,ny,w,h){
  // returns {x,y,onGround} after resolving against solids + closed door
  let x=nx, y=ny, onGround=false;
  // Build candidate blocking cells around the player.
  const half_w=w/2, half_h=h/2;
  function blocked(col,row){
    if(isSolid(col,row)) return true;
    if(door && !door.open && col===door.col && row===door.row) return true; // closed door is solid
    if(door && !door.open && col===door.col && row===door.row-1) return true; // door spans ~2 tiles tall visually; block the upper cell too
    return false;
  }
  // Convert world->grid. world y up; row = ROWS-1 - floor(y/TILE).
  function cellsOverlapping(px,py){
    const c0=Math.floor((px-half_w)/TILE), c1=Math.floor((px+half_w)/TILE);
    const rTop=ROWS-1-Math.floor((py+half_h)/TILE);
    const rBot=ROWS-1-Math.floor((py-half_h)/TILE);
    const list=[];
    for(let c=c0;c<=c1;c++) for(let r=rTop;r<=rBot;r++) list.push({c,r});
    return list;
  }
  return {x,y,onGround,cellsOverlapping,blocked,half_w,half_h};
}

function moveAndCollide(dt){
  const w=PW,h=PH, half_w=w/2, half_h=h/2;
  function blocked(col,row){
    if(isSolid(col,row)) return true;
    if(door && !door.open){
      if(col===door.col && (row===door.row || row===door.row-1)) return true;
    }
    return false;
  }
  // Horizontal
  player.x += player.vx*dt;
  {
    const c0=Math.floor((player.x-half_w)/TILE), c1=Math.floor((player.x+half_w)/TILE);
    const rTop=ROWS-1-Math.floor((player.y+half_h-1)/TILE);
    const rBot=ROWS-1-Math.floor((player.y-half_h+1)/TILE);
    for(let c=c0;c<=c1;c++) for(let r=rTop;r<=rBot;r++){
      if(!blocked(c,r)) continue;
      const cx=(c+0.5)*TILE;
      if(player.vx>0){ player.x=Math.min(player.x, cx-TILE/2-half_w); }
      else if(player.vx<0){ player.x=Math.max(player.x, cx+TILE/2+half_w); }
    }
  }
  // Vertical
  player.y += player.vy*dt;
  player.onGround=false;
  {
    const c0=Math.floor((player.x-half_w+1)/TILE), c1=Math.floor((player.x+half_w-1)/TILE);
    const rTop=ROWS-1-Math.floor((player.y+half_h)/TILE);
    const rBot=ROWS-1-Math.floor((player.y-half_h)/TILE);
    for(let c=c0;c<=c1;c++) for(let r=rTop;r<=rBot;r++){
      if(!blocked(c,r)) continue;
      const cy=(ROWS-1-r+0.5)*TILE;
      if(player.vy<0){ // falling: land on top of tile
        player.y=Math.max(player.y, cy+TILE/2+half_h);
        player.vy=0; player.onGround=true;
      } else if(player.vy>0){ // rising: bonk head
        player.y=Math.min(player.y, cy-TILE/2-half_h);
        player.vy=0;
      }
    }
  }
}

function tryJump(){
  if(player.onGround) player.jumps = player.hasDouble?2:1;
  if(player.jumps<=0) return;
  player.jumps--;
  player.onGround=false;
  player.vy=JUMP_V;
  if(player.jumps===0 && player.hasDouble) puff(player.x,player.y-PH/2,COL.player,18);
}

function doAttack(){
  slash={ x:player.x+player.face*PW, y:player.y, life:0.12, face:player.face };
  const reach=TILE*0.9;
  for(const e of enemies){
    if(!e.alive) continue;
    if(Math.abs(e.x-slash.x)<reach && Math.abs(e.y-slash.y)<PH*0.9){
      e.alive=false; puff(e.x,e.y,COL.enemy,18);
    }
  }
}

function update(dt){
  if(state!=="play"){
    // allow restart edge
    if(keys.jump && !held.jump){ held.jump=true; if(state!=="play") reset(); }
    if(!keys.jump) held.jump=false;
    if(banner) banner.life-=dt;
    return;
  }

  // Horizontal intent
  const dir=(keys.right?1:0)-(keys.left?1:0);
  player.vx = dir*MOVE;
  if(dir>0) player.face=1; else if(dir<0) player.face=-1;

  // Jump (edge-triggered)
  if(keys.jump && !held.jump){ held.jump=true; tryJump(); }
  if(!keys.jump) held.jump=false;
  // Attack (edge-triggered)
  if(keys.attack && !held.attack){ held.attack=true; doAttack(); }
  if(!keys.attack) held.attack=false;

  // Gravity
  player.vy -= GRAV*dt;
  moveAndCollide(dt);

  // Enemies patrol
  for(const e of enemies){
    if(!e.alive) continue;
    e.x += e.dir*90*dt;
    if(e.x>=e.maxX){ e.dir=-1; } else if(e.x<=e.minX){ e.dir=1; }
  }

  // Pickup
  if(pickup && !pickup.got){
    if(Math.abs(player.x-pickup.x)<TILE*0.7 && Math.abs(player.y-pickup.y)<TILE*0.7){
      pickup.got=true; player.hasDouble=true; player.jumps=Math.max(player.jumps,1);
      puff(pickup.x,pickup.y,COL.pickup,22);
      showBanner("DOUBLE JUMP ACQUIRED", COL.pickup);
    }
  }
  // Door — trigger when the player is pressed up against it. The body halts at
  // the wall face (~one tile from the door center), so the x window must be a
  // little over one tile or the gate can never be reached.
  if(door && !door.open){
    if(Math.abs(player.x-door.x)<TILE*1.2 && Math.abs(player.y-door.y)<TILE*1.4){
      if(player.hasDouble){ door.open=true; puff(door.x,door.y,COL.door,26); showBanner("GATE UNLOCKED",COL.door); }
      else { showBanner("LOCKED — FIND THE CORE", COL.doorLock); }
    }
  }
  // Goal
  if(goal && Math.abs(player.x-goal.x)<TILE*0.7 && Math.abs(player.y-goal.y)<TILE*0.8){
    state="win"; showBanner("LEVEL CLEAR", COL.grid);
  }

  // Enemy contact
  if(player.invuln>0) player.invuln-=dt;
  for(const e of enemies){
    if(!e.alive) continue;
    if(Math.abs(player.x-e.x)<(PW/2+e.w/2) && Math.abs(player.y-e.y)<(PH/2+e.h/2)){
      const stomping = player.vy<0 && player.y > e.y + e.h*0.2;
      if(stomping){ e.alive=false; player.vy=BOUNCE; puff(e.x,e.y,COL.enemy,18); }
      else if(player.invuln<=0){
        player.hp--; player.invuln=1.0;
        player.vx = (player.x<e.x?-1:1)*320; player.vy=520;
        if(player.hp<=0){ state="dead"; showBanner("GAME OVER", COL.enemy); }
      }
    }
  }

  // Fell out of world
  if(player.y < -TILE){
    player.hp--; player.invuln=1.0;
    if(player.hp<=0){ state="dead"; showBanner("GAME OVER", COL.enemy); }
    else { player.x=spawn.x; player.y=spawn.y; player.vx=player.vy=0; }
  }

  // FX
  for(let i=fx.length-1;i>=0;i--){ fx[i].life-=dt; if(fx[i].life<=0) fx.splice(i,1); }
  if(slash){ slash.life-=dt; if(slash.life<=0) slash=null; }
  if(banner){ banner.life-=dt; if(banner.life<=0) banner=null; }
}

// === Rendering ===
const canvas=document.getElementById('c');
const ctx=canvas.getContext('2d');
let VW=0, VH=0, DPR=1;
function resize(){
  DPR=Math.min(devicePixelRatio||1, 2);
  VW=innerWidth; VH=innerHeight;
  canvas.width=Math.floor(VW*DPR); canvas.height=Math.floor(VH*DPR);
  ctx.setTransform(DPR,0,0,DPR,0,0);
}
addEventListener('resize',resize); resize();

// Camera: follow player, clamp to world; scale so the world height fits nicely.
function camera(){
  const scale = VH / (Math.min(WORLD_H, 12*TILE)); // show ~12 tiles tall
  const viewW = VW/scale, viewH=VH/scale;
  let cx=player.x, cy=player.y;
  cx=Math.max(viewW/2, Math.min(WORLD_W-viewW/2, cx));
  cy=Math.max(viewH/2, Math.min(WORLD_H-viewH/2, cy));
  if(WORLD_W<viewW) cx=WORLD_W/2;
  if(WORLD_H<viewH) cy=WORLD_H/2;
  return {scale,cx,cy,viewW,viewH};
}
// world (origin bottom-left, y up) -> screen (y down)
function worldToScreen(wx,wy,cam){
  const sx=(wx-(cam.cx-cam.viewW/2))*cam.scale;
  const sy=VH-(wy-(cam.cy-cam.viewH/2))*cam.scale;
  return [sx,sy];
}

function drawBackground(){
  // gradient sky
  const g=ctx.createLinearGradient(0,0,0,VH);
  g.addColorStop(0,COL.bg0); g.addColorStop(1,COL.bgN);
  ctx.fillStyle=g; ctx.fillRect(0,0,VW,VH);
  // sun
  const horizon=VH*0.52, R=Math.min(VW,VH)*0.22, sunX=VW*0.5, sunY=horizon-R*0.2;
  const sg=ctx.createLinearGradient(sunX,sunY-R,sunX,sunY+R);
  sg.addColorStop(0,COL.sunCore); sg.addColorStop(1,COL.sun);
  ctx.save(); ctx.beginPath(); ctx.arc(sunX,sunY,R,0,7); ctx.clip();
  ctx.fillStyle=sg; ctx.fillRect(sunX-R,sunY-R,R*2,R*2);
  // bands
  ctx.fillStyle=COL.bg0;
  let yy=sunY+R*0.05, th=3;
  while(yy<sunY+R){ ctx.fillRect(sunX-R,yy,R*2,th); yy+=th+7; th+=1.2; }
  ctx.restore();
  // horizon grid
  ctx.strokeStyle=COL.grid; ctx.globalAlpha=0.35; ctx.lineWidth=1;
  for(let i=0;i<=14;i++){ const t=i/14, x=t*VW;
    ctx.beginPath(); ctx.moveTo(x,horizon); ctx.lineTo((x-VW/2)*3+VW/2,VH); ctx.stroke(); }
  for(let i=1;i<=8;i++){ const t=i/8, y=horizon+(VH-horizon)*t*t;
    ctx.beginPath(); ctx.moveTo(0,y); ctx.lineTo(VW,y); ctx.stroke(); }
  ctx.globalAlpha=1;
}

function rect(cam,wx,wy,w,h,color,glow){
  const [sx,sy]=worldToScreen(wx,wy+h/2,cam); // wy is center? we pass center
  const sw=w*cam.scale, sh=h*cam.scale;
  if(glow){ ctx.shadowColor=color; ctx.shadowBlur=glow; } else ctx.shadowBlur=0;
  ctx.fillStyle=color;
  ctx.fillRect(sx-sw/2, sy-sh/2, sw, sh);
  ctx.shadowBlur=0;
}

function draw(){
  drawBackground();
  const cam=camera();

  // Tiles
  for(const t of solids){
    const ctr=cellCenter(t.col,t.row);
    const [sx,sy]=worldToScreen(ctr.x,ctr.y,cam);
    const s=TILE*cam.scale;
    ctx.fillStyle=COL.tileEdge; ctx.fillRect(sx-s/2,sy-s/2,s,s);
    ctx.fillStyle=COL.tile; ctx.fillRect(sx-s/2+2,sy-s/2+2,s-4,s-4);
  }

  // Goal portal
  if(goal){
    const [sx,sy]=worldToScreen(goal.x,goal.y,cam); const r=TILE*0.5*cam.scale;
    ctx.strokeStyle=COL.grid; ctx.lineWidth=3; ctx.shadowColor=COL.grid; ctx.shadowBlur=12;
    ctx.beginPath(); ctx.arc(sx,sy,r,0,7); ctx.stroke();
    ctx.strokeStyle=COL.sun; ctx.beginPath(); ctx.arc(sx,sy,r*0.55,0,7); ctx.stroke();
    ctx.shadowBlur=0;
  }

  // Door (if closed)
  if(door && !door.open){
    const [sx,sy]=worldToScreen(door.x,door.y,cam);
    const w=TILE*0.5*cam.scale, h=TILE*2.2*cam.scale;
    ctx.strokeStyle=COL.doorLock; ctx.lineWidth=3; ctx.shadowColor=COL.doorLock; ctx.shadowBlur=10;
    ctx.strokeRect(sx-w/2,sy-h/2,w,h);
    ctx.fillStyle=COL.doorLock;
    for(let i=0;i<4;i++){ const yy=sy-h/2+8+i*(h-16)/3; ctx.fillRect(sx-w*0.35,yy,w*0.7,4); }
    ctx.shadowBlur=0;
  }

  // Pickup
  if(pickup && !pickup.got){
    const bob=Math.sin(performance.now()/300)*4;
    const [sx,sy]=worldToScreen(pickup.x,pickup.y+bob,cam); const r=TILE*0.4*cam.scale;
    ctx.fillStyle=COL.pickup; ctx.shadowColor=COL.pickup; ctx.shadowBlur=16;
    ctx.beginPath(); for(let i=0;i<4;i++){ const a=i/4*Math.PI*2+performance.now()/600;
      const px=sx+Math.cos(a)*r, py=sy+Math.sin(a)*r; i?ctx.lineTo(px,py):ctx.moveTo(px,py);} ctx.closePath(); ctx.fill();
    ctx.shadowBlur=0;
  }

  // Enemies
  for(const e of enemies){ if(!e.alive) continue;
    const [sx,sy]=worldToScreen(e.x,e.y,cam); const w=e.w*cam.scale,h=e.h*cam.scale;
    ctx.fillStyle=COL.enemy; ctx.shadowColor=COL.enemy; ctx.shadowBlur=10;
    ctx.fillRect(sx-w/2,sy-h/2,w,h);
    ctx.shadowBlur=0; ctx.fillStyle=COL.enemyEye;
    ctx.fillRect(sx-w*0.25,sy-h*0.1,w*0.18,h*0.3); ctx.fillRect(sx+w*0.07,sy-h*0.1,w*0.18,h*0.3);
  }

  // Slash
  if(slash){ const [sx,sy]=worldToScreen(slash.x,slash.y,cam);
    ctx.strokeStyle=COL.player; ctx.lineWidth=3; ctx.globalAlpha=slash.life/0.12;
    ctx.shadowColor=COL.player; ctx.shadowBlur=10;
    ctx.beginPath(); ctx.arc(sx,sy,TILE*0.5*cam.scale,0,7); ctx.stroke();
    ctx.globalAlpha=1; ctx.shadowBlur=0;
  }

  // Player
  {
    const [sx,sy]=worldToScreen(player.x,player.y,cam);
    const w=PW*cam.scale, h=PH*cam.scale;
    if(!(player.invuln>0 && Math.floor(performance.now()/80)%2)){
      ctx.fillStyle=COL.player; ctx.shadowColor=COL.player; ctx.shadowBlur=12;
      ctx.fillRect(sx-w/2,sy-h/2,w,h);
      ctx.shadowBlur=0; ctx.fillStyle=COL.visor;
      const vx = player.face>0 ? sx-w*0.1 : sx-w*0.3;
      ctx.fillRect(vx, sy-h*0.3, w*0.4, h*0.18);
    }
  }

  // FX
  for(const f of fx){ const cam2=cam; const [sx,sy]=worldToScreen(f.x,f.y,cam2);
    ctx.globalAlpha=f.life/f.max; ctx.fillStyle=f.color; ctx.shadowColor=f.color; ctx.shadowBlur=12;
    ctx.beginPath(); ctx.arc(sx,sy,f.r*cam2.scale*(1.4-f.life/f.max),0,7); ctx.fill();
    ctx.globalAlpha=1; ctx.shadowBlur=0;
  }

  // HUD: health pips
  for(let i=0;i<CFG.maxHealth;i++){
    ctx.fillStyle = i<player.hp ? COL.health : COL.healthEmpty;
    ctx.shadowColor=COL.health; ctx.shadowBlur=i<player.hp?6:0;
    ctx.fillRect(16+i*22, 16, 16, 16);
  }
  ctx.shadowBlur=0;
  // ability indicator
  ctx.strokeStyle = player.hasDouble?COL.pickup:COL.healthEmpty; ctx.lineWidth=2;
  ctx.strokeRect(16+CFG.maxHealth*22+8, 16, 16, 16);

  // Banner
  if(banner){
    ctx.globalAlpha=Math.min(1, banner.life);
    ctx.fillStyle=banner.color; ctx.font="bold 32px ui-monospace,monospace";
    ctx.textAlign="center"; ctx.shadowColor=banner.color; ctx.shadowBlur=12;
    ctx.fillText(banner.text, VW/2, VH*0.32);
    ctx.shadowBlur=0; ctx.globalAlpha=1;
    if(state!=="play"){ ctx.fillStyle=COL.grid; ctx.font="16px ui-monospace,monospace";
      ctx.fillText("press ▲ / Space / R to restart", VW/2, VH*0.32+34); }
    ctx.textAlign="left";
  }
}

// === Loop ===
let last=performance.now();
function frame(now){
  let dt=(now-last)/1000; last=now;
  dt=Math.min(dt, 1/30);
  update(dt);
  draw();
  requestAnimationFrame(frame);
}
requestAnimationFrame(frame);
</script>
</body>
</html>
"""


def main() -> int:
    config = build_config()
    html = render_html(config)
    out = HERE / "play.html"
    out.write_text(html, encoding="utf-8")
    print(f"Wrote {out} ({len(html):,} bytes)")
    print(f"Level {config['cols']}x{config['rows']}, "
          f"jump apex {config['apexTiles']} tiles, {config['maxHealth']} HP.")
    print("Open it in any browser to play.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
