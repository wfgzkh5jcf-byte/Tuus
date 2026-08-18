const canvas = document.getElementById('clock');
const ctx = canvas.getContext('2d');
const timeEl = document.getElementById('digitalTime');
const dateEl = document.getElementById('digitalDate');
const agendaDateEl = document.getElementById('agendaDate');
const agendaList = document.getElementById('agendaList');
const agendaTomorrow = document.getElementById('agendaTomorrow');
const todoList = document.getElementById('todoList');
const todoCount = document.getElementById('todoCount');

const colors = { cream:'#f3ebdd', green:'#91a961', orange:'#f39a18', muted:'#7f8c88', edge:'#374247' };
const days = ['zondag','maandag','dinsdag','woensdag','donderdag','vrijdag','zaterdag'];
const months = ['januari','februari','maart','april','mei','juni','juli','augustus','september','oktober','november','december'];

function resizeCanvas(){
  const rect=canvas.getBoundingClientRect(), dpr=window.devicePixelRatio||1;
  const width=Math.max(1,Math.round(rect.width*dpr)), height=Math.max(1,Math.round(rect.height*dpr));
  if(canvas.width!==width||canvas.height!==height){canvas.width=width;canvas.height=height;}
}
function polar(cx,cy,angle,radius){return [cx+Math.cos(angle-Math.PI/2)*radius,cy+Math.sin(angle-Math.PI/2)*radius];}
function drawClock(now){
  resizeCanvas(); const dpr=window.devicePixelRatio||1,w=canvas.width,h=canvas.height,cx=w/2,cy=h/2,r=Math.min(w,h)*.46;
  ctx.clearRect(0,0,w,h); ctx.lineCap='round'; ctx.strokeStyle=colors.edge; ctx.lineWidth=2*dpr; ctx.beginPath();ctx.arc(cx,cy,r,0,Math.PI*2);ctx.stroke();
  for(let i=0;i<60;i++){const major=i%5===0,angle=i*Math.PI/30,[x1,y1]=polar(cx,cy,angle,r-(major?18:9)*dpr),[x2,y2]=polar(cx,cy,angle,r-3*dpr);ctx.strokeStyle=major?colors.cream:colors.muted;ctx.lineWidth=(major?3:1)*dpr;ctx.beginPath();ctx.moveTo(x1,y1);ctx.lineTo(x2,y2);ctx.stroke();}
  ctx.fillStyle=colors.cream;ctx.font=`700 ${Math.round(17*dpr)}px system-ui, sans-serif`;ctx.textAlign='center';ctx.textBaseline='middle';
  for(let hour=1;hour<=12;hour++){const [x,y]=polar(cx,cy,hour*Math.PI/6,r*.72);ctx.fillText(String(hour),x,y);}
  const sec=now.getSeconds()+now.getMilliseconds()/1000,min=now.getMinutes()+sec/60,hour=(now.getHours()%12)+min/60;
  function hand(angle,length,width,color,back=0){const [x2,y2]=polar(cx,cy,angle,r*length),[x1,y1]=polar(cx,cy,angle+Math.PI,r*back);ctx.strokeStyle=color;ctx.lineWidth=width*dpr;ctx.beginPath();ctx.moveTo(x1,y1);ctx.lineTo(x2,y2);ctx.stroke();}
  hand(hour*Math.PI/6,.48,7,colors.cream);hand(min*Math.PI/30,.69,5,colors.green);hand(sec*Math.PI/30,.80,2,colors.orange,.15);
  ctx.fillStyle=colors.orange;ctx.beginPath();ctx.arc(cx,cy,6*dpr,0,Math.PI*2);ctx.fill();
}
function nlDate(now,capitalize=false){const text=`${days[now.getDay()]} ${now.getDate()} ${months[now.getMonth()]} ${now.getFullYear()}`;return capitalize?text.charAt(0).toUpperCase()+text.slice(1):text;}
function updateDigital(now){const hh=String(now.getHours()).padStart(2,'0'),mm=String(now.getMinutes()).padStart(2,'0');timeEl.textContent=`${hh}:${mm}`;dateEl.textContent=nlDate(now,true);agendaDateEl.textContent=nlDate(now,true);}
function updateTodoCount(){const checks=[...todoList.querySelectorAll('input[type="checkbox"]')],done=checks.filter(b=>b.checked).length;todoCount.textContent=`✓ ${done} van ${checks.length} taken voltooid`;}
todoList.addEventListener('change',updateTodoCount);updateTodoCount();

function esc(text){const div=document.createElement('div');div.textContent=text;return div.innerHTML;}
function agendaRow(event){return `<div class="agenda-item"><div class="agenda-time">${event.all_day?'hele dag':esc(event.time)}</div><div><div class="agenda-title">${esc(event.title)}</div></div></div>`;}
async function loadAgenda(){
  try{
    const response=await fetch('/api/agenda',{cache:'no-store'}); if(!response.ok) throw new Error(`HTTP ${response.status}`);
    const data=await response.json();
    const today=data.events.filter(e=>e.date===data.today), tomorrow=data.events.filter(e=>e.date===data.tomorrow);
    agendaList.innerHTML=today.length?today.map(agendaRow).join(''):'<div class="agenda-item"><div class="agenda-time">—</div><div><div class="agenda-title">Geen afspraken vandaag</div></div></div>';
    if(tomorrow.length){const first=tomorrow[0];agendaTomorrow.innerHTML=`Morgen: &nbsp; <strong>${first.all_day?'hele dag':esc(first.time)}</strong> &nbsp; ${esc(first.title)}${tomorrow.length>1?` &nbsp; +${tomorrow.length-1}`:''}`;}
    else agendaTomorrow.textContent='Morgen: geen afspraken';
  }catch(err){agendaList.innerHTML='<div class="agenda-item"><div class="agenda-time">!</div><div><div class="agenda-title">Agenda niet bereikbaar</div></div></div>';agendaTomorrow.textContent='Controleer Tuus-server';console.error(err);}
}
loadAgenda(); setInterval(loadAgenda,5*60*1000);

let lastMinute=-1;
function frame(){const now=new Date();drawClock(now);if(now.getMinutes()!==lastMinute){updateDigital(now);lastMinute=now.getMinutes();}requestAnimationFrame(frame);}
window.addEventListener('resize',resizeCanvas);requestAnimationFrame(frame);
