'use strict';
const D = JSON.parse(document.getElementById('pointData').textContent);
const stage = document.querySelector('.stage');
const canvas = document.querySelector('canvas');
const ctx = canvas.getContext('2d');
const tooltip = document.querySelector('.tooltip');
const selection = document.querySelector('.selection');
const enabled = new Set(D.datasets.map((_, i) => i));
const poses = [...document.querySelectorAll('.pose')];
const homePositions = poses.map(button => [button.style.left, button.style.top]);
let cardDrag = null;
let yaw = .72, pitch = .42, zoom = 1, panX = 0, panY = 0, mode = 'rotate', drag = null, selected = null;
let width = 1, height = 1, fit = 1, projected = [], framePending = false;

function rotate(q, a = yaw, b = pitch) {
  const x = Math.cos(a)*q[0] + Math.sin(a)*q[2];
  const z = -Math.sin(a)*q[0] + Math.cos(a)*q[2];
  const y = Math.cos(b)*q[1] - Math.sin(b)*z;
  const depth = Math.sin(b)*q[1] + Math.cos(b)*z;
  const perspective = .72 / Math.max(.6, 2.7-depth*.4);
  return [x*perspective, y*perspective, depth];
}
const baseline = D.coords.map(q => rotate(q, .72, .42));
const xs = baseline.map(q => q[0]), ys = baseline.map(q => q[1]);
const bounds = [Math.min(...xs), Math.max(...xs), Math.min(...ys), Math.max(...ys)];
const center = [(bounds[0]+bounds[1])/2, (bounds[2]+bounds[3])/2];

function project(q) {
  const p = rotate(q);
  return [width*(.51+panX)+(p[0]-center[0])*fit*zoom, height*(.48+panY)-(p[1]-center[1])*fit*zoom, p[2]];
}
function schedule() {
  if (!framePending) {
    framePending = true;
    requestAnimationFrame(() => {framePending = false; draw();});
  }
}
function resize() {
  width = stage.clientWidth; height = stage.clientHeight;
  const ratio = Math.min(window.devicePixelRatio || 1, 2);
  canvas.width = Math.round(width*ratio); canvas.height = Math.round(height*ratio);
  ctx.setTransform(ratio,0,0,ratio,0,0);
  fit = Math.min(width*.57/(bounds[1]-bounds[0]), height*.74/(bounds[3]-bounds[2]));
  poses.forEach(button => movePose(button,parseFloat(button.style.left)/100,parseFloat(button.style.top)/100));
  schedule();
}
function movePose(button,x,y) {
  const halfW=Math.min(.5,button.offsetWidth/(2*width)),halfH=Math.min(.5,button.offsetHeight/(2*height));
  button.style.left=`${Math.max(halfW,Math.min(1-halfW,x))*100}%`;
  button.style.top=`${Math.max(halfH,Math.min(1-halfH,y))*100}%`;
}
function draw() {
  ctx.clearRect(0,0,width,height);
  projected = D.coords.map(project);
  const visible = projected.map((q,i) => [q,i]).filter(([,i]) => enabled.has(D.sourceIds[i]));
  visible.sort((a,b) => a[0][2]-b[0][2]);
  ctx.globalAlpha = .64;
  for (const [q,i] of visible) {
    ctx.fillStyle = D.colors[D.sourceIds[i]];
    ctx.beginPath(); ctx.arc(q[0],q[1],width<600?1.6:2,0,Math.PI*2); ctx.fill();
  }
  ctx.globalAlpha = 1;
  const origin = project([0,0,0]);
  for (const [q,label,color] of [[[1.7,0,0],'PC1','#ad7b53'],[[0,1.7,0],'PC2','#739569'],[[0,0,1.7],'PC3','#7a9bad']]) {
    const end = project(q);
    ctx.strokeStyle=color;ctx.lineWidth=.8;ctx.beginPath();ctx.moveTo(origin[0],origin[1]);ctx.lineTo(end[0],end[1]);ctx.stroke();
    ctx.fillStyle=color;ctx.font='10px system-ui';ctx.fillText(label,end[0]+4,end[1]-4);
  }
  const stageBox = stage.getBoundingClientRect();
  D.medoids.forEach((m,c) => {
    const on = enabled.has(D.sourceIds[m.index]); poses[c].classList.toggle('is-muted',!on);
    if (!on) return;
    const q = projected[m.index], card = poses[c].getBoundingClientRect();
    const cx=card.left-stageBox.left+card.width/2,cy=card.top-stageBox.top+card.height/2;
    const dx=q[0]-cx,dy=q[1]-cy;
    const edge=Math.min(1,(card.width/2+3)/Math.max(Math.abs(dx),.01),(card.height/2+3)/Math.max(Math.abs(dy),.01));
    ctx.strokeStyle=selected===c?'#7b6546':'#aaa08f';ctx.lineWidth=selected===c?1.4:.85;
    ctx.beginPath();ctx.moveTo(cx+dx*edge,cy+dy*edge);ctx.lineTo(q[0],q[1]);ctx.stroke();
    ctx.fillStyle='#fdfaf4';ctx.beginPath();ctx.arc(q[0],q[1],selected===c?8:6,0,Math.PI*2);ctx.fill();
    ctx.strokeStyle='#3e3a32';ctx.lineWidth=1.2;ctx.stroke();
    ctx.fillStyle=D.colors[D.sourceIds[m.index]];ctx.beginPath();ctx.arc(q[0],q[1],selected===c?5.5:4,0,Math.PI*2);ctx.fill();
  });
}
function select(c) {
  selected=c;
  poses.forEach((button,i) => button.setAttribute('aria-pressed',String(i===c)));
  const m=D.medoids[c];
  selection.replaceChildren();
  const title=document.createElement('strong');title.textContent=`C${c} / ${m.dataset}`;
  selection.append(title);
  schedule();
}
poses.forEach((button,c) => {
  let suppressClick=false;
  button.addEventListener('pointerdown',e=>{
    if(e.button!==0||cardDrag||drag)return;
    suppressClick=false;
    cardDrag={id:e.pointerId,button,x:e.clientX,y:e.clientY,left:parseFloat(button.style.left)/100,top:parseFloat(button.style.top)/100};
    button.setPointerCapture(e.pointerId);
    tooltip.style.display='none';
  });
  button.addEventListener('pointermove',e=>{
    if(!cardDrag||cardDrag.button!==button||cardDrag.id!==e.pointerId)return;
    const dx=e.clientX-cardDrag.x,dy=e.clientY-cardDrag.y;
    if(!suppressClick&&Math.hypot(dx,dy)<4)return;
    suppressClick=true;
    button.classList.add('is-dragging');
    movePose(button,cardDrag.left+dx/width,cardDrag.top+dy/height);
    schedule();
  });
  function stopCard(e){
    if(cardDrag&&cardDrag.button===button&&cardDrag.id===e.pointerId){cardDrag=null;button.classList.remove('is-dragging');}
  }
  button.addEventListener('pointerup',stopCard);
  button.addEventListener('pointercancel',stopCard);
  button.addEventListener('lostpointercapture',stopCard);
  button.addEventListener('click',e=>{
    if(suppressClick&&e.detail!==0){suppressClick=false;e.preventDefault();return;}
    select(c);
  });
  button.addEventListener('keydown',e=>{
    if(!['ArrowLeft','ArrowRight','ArrowUp','ArrowDown','Home'].includes(e.key))return;
    e.preventDefault();
    if(e.key==='Home'){movePose(button,parseFloat(homePositions[c][0])/100,parseFloat(homePositions[c][1])/100);}
    else{
      const step=e.shiftKey?30:10;
      movePose(button,parseFloat(button.style.left)/100+(e.key==='ArrowLeft'?-step:e.key==='ArrowRight'?step:0)/width,
        parseFloat(button.style.top)/100+(e.key==='ArrowUp'?-step:e.key==='ArrowDown'?step:0)/height);
    }
    schedule();
  });
});
document.querySelectorAll('[data-source]').forEach(button => button.addEventListener('click',()=>{
  const i=Number(button.dataset.source);
  if(enabled.has(i))enabled.delete(i);else enabled.add(i);
  button.setAttribute('aria-pressed',String(enabled.has(i)));schedule();
}));
function reset(){
  yaw=.72;pitch=.42;zoom=1;panX=0;panY=0;
  poses.forEach((button,c)=>movePose(button,parseFloat(homePositions[c][0])/100,parseFloat(homePositions[c][1])/100));
  tooltip.style.display='none';schedule();
}
document.querySelectorAll('[data-mode]').forEach(button => button.addEventListener('click',()=>{
  mode=button.dataset.mode;
  document.querySelectorAll('[data-mode]').forEach(item=>item.setAttribute('aria-pressed',String(item.dataset.mode===mode)));
  canvas.classList.toggle('move-mode',mode==='move');
}));
document.querySelector('[data-reset]').addEventListener('click',reset);
document.querySelector('[data-zoom-in]').addEventListener('click',()=>{zoom=Math.min(2,zoom*1.15);schedule();});
document.querySelector('[data-zoom-out]').addEventListener('click',()=>{zoom=Math.max(.55,zoom/1.15);schedule();});
canvas.addEventListener('pointerdown',e=>{
  if(drag||cardDrag||![0,2].includes(e.button))return;
  const moving=mode==='move'||e.shiftKey||e.button===2;
  drag={id:e.pointerId,x:e.clientX,y:e.clientY,yaw,pitch,panX,panY,moving};canvas.setPointerCapture(e.pointerId);canvas.classList.add('dragging');tooltip.style.display='none';
});
canvas.addEventListener('pointermove',e=>{
  if(drag){
    if(e.pointerId!==drag.id)return;
    if(drag.moving){panX=drag.panX+(e.clientX-drag.x)/width;panY=drag.panY+(e.clientY-drag.y)/height;}
    else{yaw=drag.yaw+(e.clientX-drag.x)*.008;pitch=Math.max(-1.4,Math.min(1.4,drag.pitch+(e.clientY-drag.y)*.008));}
    schedule();return;
  }
  const r=canvas.getBoundingClientRect(),x=e.clientX-r.left,y=e.clientY-r.top;
  let nearest=-1,distance=10;
  projected.forEach((q,i)=>{if(!enabled.has(D.sourceIds[i]))return;const d=Math.hypot(q[0]-x,q[1]-y);if(d<distance){distance=d;nearest=i;}});
  if(nearest<0){tooltip.style.display='none';return;}
  tooltip.textContent=`${D.datasets[D.sourceIds[nearest]]} / C${D.labels[nearest]}`;
  tooltip.style.left=`${Math.max(0,Math.min(width-190,x+12))}px`;tooltip.style.top=`${Math.max(0,y-32)}px`;tooltip.style.display='block';
});
function stop(e){if(drag&&e.pointerId===drag.id){drag=null;canvas.classList.remove('dragging');}}
canvas.addEventListener('pointerup',stop);canvas.addEventListener('pointercancel',stop);canvas.addEventListener('lostpointercapture',stop);
canvas.addEventListener('contextmenu',e=>e.preventDefault());
canvas.addEventListener('pointerleave',()=>{tooltip.style.display='none';});
canvas.addEventListener('wheel',e=>{e.preventDefault();zoom=Math.max(.55,Math.min(2,zoom*Math.exp(-e.deltaY*.001)));schedule();},{passive:false});
canvas.addEventListener('keydown',e=>{
  if(!['ArrowLeft','ArrowRight','ArrowUp','ArrowDown','+','=','-','0'].includes(e.key))return;
  e.preventDefault();
  if(e.shiftKey||mode==='move'){
    if(e.key==='ArrowLeft')panX-=20/width;if(e.key==='ArrowRight')panX+=20/width;
    if(e.key==='ArrowUp')panY-=20/height;if(e.key==='ArrowDown')panY+=20/height;
  }else{
    if(e.key==='ArrowLeft')yaw-=.12;if(e.key==='ArrowRight')yaw+=.12;
    if(e.key==='ArrowUp')pitch=Math.max(-1.4,pitch-.12);if(e.key==='ArrowDown')pitch=Math.min(1.4,pitch+.12);
  }
  if(e.key==='+'||e.key==='=')zoom=Math.min(2,zoom*1.1);if(e.key==='-')zoom=Math.max(.55,zoom/1.1);if(e.key==='0')reset();
  schedule();
});
new ResizeObserver(resize).observe(stage);
document.fonts.ready.then(schedule);
resize();
