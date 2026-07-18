/* PQC Agent Dashboard v5 */
let DATA=null, DESIGN=localStorage.getItem('design')||'mldsa';

/* ---------- matrix rain (proper 1s/0s) ---------- */
const cv=document.getElementById('rain'),cx=cv.getContext('2d');
let drops=[],FS=14;
function sizeRain(){cv.width=innerWidth;cv.height=innerHeight;
  const cols=Math.floor(cv.width/FS);drops=Array(cols).fill(0).map(()=>Math.random()*-50);}
sizeRain();addEventListener('resize',sizeRain);
setInterval(()=>{
  if(document.body.dataset.theme!=='matrix')return;
  cx.fillStyle='rgba(4,7,10,0.12)';cx.fillRect(0,0,cv.width,cv.height);
  cx.font=FS+'px monospace';
  for(let i=0;i<drops.length;i++){
    const y=drops[i]*FS;
    cx.fillStyle=Math.random()<0.08?'#b4ffd0':'#1e9e4a';
    cx.fillText(Math.random()<0.5?'0':'1',i*FS,y);
    if(y>cv.height&&Math.random()>0.975)drops[i]=0;else drops[i]++;
  }
},55);

/* ---------- theme ---------- */
document.querySelectorAll('.themes button').forEach(b=>b.onclick=()=>{
  document.body.dataset.theme=b.dataset.t;localStorage.setItem('theme',b.dataset.t);});
document.body.dataset.theme=localStorage.getItem('theme')||'matrix';

/* ---------- helpers ---------- */
const $=id=>document.getElementById(id);
const esc=s=>String(s??'').replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));
function svgLine(pts,w,h,color){
  if(pts.length<2)return '<div class="nobase">not enough points</div>';
  const xs=pts.map((_,i)=>i),ys=pts.map(p=>p[1]);
  const mn=Math.min(...ys),mx=Math.max(...ys),pad=(mx-mn)||1;
  const X=i=>10+(i/(pts.length-1))*(w-20),Y=v=>h-14-((v-mn)/pad)*(h-30);
  let d=pts.map((p,i)=>(i?'L':'M')+X(i).toFixed(1)+' '+Y(p[1]).toFixed(1)).join(' ');
  let dots=pts.map((p,i)=>`<circle cx="${X(i).toFixed(1)}" cy="${Y(p[1]).toFixed(1)}" r="3" fill="${color}"/>`).join('');
  return `<svg width="100%" viewBox="0 0 ${w} ${h}">
    <path d="${d}" stroke="${color}" fill="none" stroke-width="2"/>${dots}
    <text x="10" y="12">${mx.toFixed(3)}</text><text x="10" y="${h-4}">${mn.toFixed(3)}</text></svg>`;
}

/* ---------- drill-down modal ---------- */
function openModal(html){$('mbody').innerHTML=html;$('modal').classList.remove('hidden');}
$('mclose').onclick=()=>$('modal').classList.add('hidden');
$('modal').onclick=e=>{if(e.target.id==='modal')$('modal').classList.add('hidden');};
function editHtml(edits){
  if(!edits||!edits.length)return '<div class="nobase">edit text not recorded for this win</div>';
  return edits.map((e,i)=>`<div class="diff"><h3>EDIT ${i+1}${e.file?' — '+esc(e.file):''}</h3>
    ${e.old_str?`<pre class="old">- ${esc(e.old_str)}</pre>`:''}
    ${e.new_str?`<pre class="new">+ ${esc(e.new_str)}</pre>`:''}
    ${(!e.old_str&&!e.new_str)?`<pre>${esc(JSON.stringify(e,null,1))}</pre>`:''}</div>`).join('');
}
function showFix(card){
  const d=card.detail||{};
  openModal(`<h2>WIN — ${esc(card.block)}</h2>
    <div class="mrow">
      <span><span class="k">strategy</span> ${esc(card.strategy||'—')}</span>
      <span><span class="k">gain</span> +${card.gain}ns</span>
      <span><span class="k">cost</span> ${card.cost!=null?'$'+card.cost:'n/a (no API cost logged)'}</span>
      <span><span class="k">model</span> ${esc(card.model||'—')}</span>
      <span><span class="k">when</span> ${esc(card.ts||'—')}</span>
    </div>
    <div class="mrow"><span><span class="k">tier</span> ${esc(card.tier)}</span></div>
    ${editHtml(d.edits)}`);
}
function findWin(block){
  const wins=(DATA.cards||[]).filter(c=>c.verdict==='ACCEPTED'&&c.block===block);
  return wins[0]||null;
}

/* ---------- render ---------- */
function render(){
  const d=DATA;if(!d)return;
  $('clock').textContent=d.now;
  const hero=$('hero');hero.className='hero '+d.state;$('status').textContent=d.status;
  $('procs').innerHTML=Object.entries(d.procs).map(([k,v])=>
    `<span class="proc ${v?'on':''}">${k}${v?' ●':''}</span>`).join('');
  const t=d.totals;
  $('totals').innerHTML=[['attempts',t.attempts],['verified wins',t.accepted],
    ['total gain (ns)',t.gain_ns],['API spend ($)',t.cost_usd]]
    .map(([l,n])=>`<div class="tot"><div class="n">${n}</div><div class="l">${l}</div></div>`).join('');

  /* tabs + board */
  const dk=Object.keys(d.designs||{});
  if(!dk.includes(DESIGN))DESIGN=dk[0];
  $('tabs').innerHTML=dk.map(k=>`<button class="${k===DESIGN?'on':''}" data-k="${k}">${esc(d.designs[k].label||k)}</button>`).join('');
  document.querySelectorAll('#tabs button').forEach(b=>b.onclick=()=>{DESIGN=b.dataset.k;localStorage.setItem('design',DESIGN);render();});
  const des=d.designs[DESIGN]||{cores:[]};
  const vals=des.cores.flatMap(c=>[c.base,c.now]).filter(v=>typeof v==='number');
  const mn=Math.min(...vals,0)-0.2,mx=Math.max(...vals,0)+0.2;
  const px=v=>((v-mn)/(mx-mn))*100;
  $('board').innerHTML=des.cores.map(c=>{
    if(c.base==null)return `<div class="core"><div class="nm"><span>${esc(c.block)}</span><span class="nobase">no baseline measured</span></div></div>`;
    const win=findWin(c.block);
    return `<div class="core"><div class="nm"><span>${esc(c.block)}</span>
      <span>${c.base} → <b style="color:var(--win)">${c.now??c.base}</b> ns</span></div>
      <div class="dumb"><div class="track"></div>
        <div class="zero" style="left:${px(0)}%"></div>
        <div class="dot base" style="left:${px(c.base)}%" title="baseline ${c.base}"></div>
        <div class="dot now" style="left:${px(c.now??c.base)}%" title="click for the fix"
          onclick='showFixByBlock("${esc(c.block)}")'></div>
      </div></div>`;}).join('')
    +(des.chip?`<div class="chipline">chip closure: ${esc(JSON.stringify(des.chip))}</div>`:'');

  /* trend */
  $('trend').innerHTML=svgLine(d.series||[],860,150,'var(--win)');

  /* trajectories */
  const tr=d.traj||{};
  $('traj').innerHTML=Object.keys(tr).length?Object.entries(tr).map(([b,pts])=>
    `<div class="trajcard"><div class="nm">${esc(b)}</div>${svgLine(pts,300,110,'var(--acc)')}</div>`).join('')
    :'<div class="nobase">trajectories appear as blocks accumulate accepted wins</div>';

  /* legend + feed */
  $('legend').innerHTML=[['win','var(--win)'],['fail','var(--fail)'],['marginal','var(--marg)'],['neutral','var(--neu)']]
    .map(([l,c])=>`<span><span class="sw" style="background:${c}"></span>${l}</span>`).join('');
  drawFeed();
}
window.showFixByBlock=b=>{const w=findWin(b);if(w)showFix(w);else openModal(`<h2>${esc(b)}</h2><div class="nobase">no accepted win recorded in the logs for this block (baseline improvement may predate structured logging)</div>`);};

function drawFeed(){
  const q=($('q').value||'').toLowerCase();
  const cards=(DATA.cards||[]).filter(c=>!q||JSON.stringify(c).toLowerCase().includes(q));
  $('feed').innerHTML=cards.slice(0,80).map((c,i)=>
    `<div class="card ${c.kind}" data-i="${i}">
      <div class="top"><span>${esc(c.tier)}${c.block?' · '+esc(c.block):''}</span>
      <span><span class="badge">${esc(c.verdict)}</span> ${esc(c.ts||'')}</span></div>
      <div class="story">${esc(c.story)}</div></div>`).join('');
  document.querySelectorAll('#feed .card').forEach(el=>el.onclick=()=>{
    const c=cards[+el.dataset.i];
    if(c.verdict==='ACCEPTED')showFix(c);
    else openModal(`<h2>${esc(c.verdict)} — ${esc(c.block||c.tier)}</h2>
      <div class="mrow"><span><span class="k">when</span> ${esc(c.ts||'—')}</span>
      <span><span class="k">cost</span> ${c.cost!=null?'$'+c.cost:'—'}</span></div>
      <p style="margin:8px 0">${esc(c.story)}</p>
      <p style="color:var(--dim);font-size:12px">${esc((DATA.explain||{})[c.verdict]||'')}</p>
      ${c.detail?`<pre>${esc(JSON.stringify(c.detail,null,1))}</pre>`:''}`);
  });
}
$('q').oninput=drawFeed;

/* ---------- side panels ---------- */
async function loadSide(){
  try{
    const r=await(await fetch('/api/rules')).json();
    $('rcount').textContent=(r.rules||[]).length;
    $('rules').innerHTML=(r.rules||[]).slice().reverse().map(x=>
      `<div class="rule">${esc(x.rule)}<div class="m">[${esc(x.design)}] ${esc(x.ts)} · ${esc(x.source_model||'')}</div></div>`).join('')
      ||'<div class="nobase">rulebook empty — populates from ACCEPTED / REJECTED_MARGINAL verdicts</div>';
  }catch(e){}
  try{
    const m=await(await fetch('/api/minerva')).json();
    $('mrun').textContent=m.running?'RUNNING':'idle';
    $('minerva').innerHTML=(m.minerva||[]).map(e=>{
      const rs=(e.results||[]).map(r=>
        `<div class="mtile"><b>${esc(e.alg)}</b> — <b>${parseFloat(r.freq).toFixed(1)} MHz</b><br>
        LUT ${esc(r.LUT)} · FF ${esc(r.FF)} · Slice ${esc(r.Slice)}<br>
        <span style="color:var(--dim)">start ${esc(r.start_time)} · runtime ${esc(r.run_time)} · ${esc(r.device)}</span></div>`).join('');
      return rs||`<div class="mtile"><b>${esc(e.alg)}</b> — <span class="nobase">no result yet</span></div>`;
    }).join('')||'<div class="nobase">no Minerva status files found</div>';
  }catch(e){}
}

/* ---------- poll ---------- */
async function tick(){
  try{DATA=await(await fetch('/api/data')).json();render();}catch(e){}
  loadSide();
}
tick();setInterval(tick,5000);
