/* PQC Agent Dashboard v3 front end (vanilla JS, no deps) */
let DATA = null;
let tierFilter = null, verdictFilter = null, q = "";
const open = new Set();          // open card keys persist across refresh

const $ = id => document.getElementById(id);
const esc = s => String(s == null ? "" : s)
  .replace(/[&<>]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;"}[c]));

function fmtGain(g){
  if (typeof g !== "number") return "";
  const cls = g >= 0 ? "gain-pos" : "gain-neg";
  return `<span class="${cls}">${g > 0 ? "+" : ""}${g}ns</span>`;
}

function heroStats(t){
  const items = [
    [t.accepted, "wins"],
    [t.attempts, "attempts"],
    [t.gain_ns + "ns", "gained", t.gain_ns > 0],
    ["$" + t.cost_usd, "api spend"],
  ];
  return items.map(([v, l, pos]) =>
    `<div class="stat"><b class="${pos ? "pos" : ""}">${esc(v)}</b><span>${l}</span></div>`).join("");
}

function procPills(p){
  const names = {block_orch:"block orchestrator", chip_orch:"chip loop",
                 minerva:"minerva", vivado:"vivado", xsim:"simulation"};
  return Object.entries(p)
    .map(([k, on]) => `<span class="pill ${on ? "live" : ""}">${on ? "●" : "○"} ${names[k]}</span>`)
    .join("");
}

function trend(series){
  const svg = $("trend");
  if (!series || series.length < 2){
    svg.innerHTML = `<text x="300" y="75" fill="#5b6272" font-size="12" text-anchor="middle">not enough accepted edits yet</text>`;
    return;
  }
  const W = 600, H = 140, P = 12;
  const ys = series.map(s => s[1]);
  const max = Math.max(...ys), min = Math.min(0, ...ys);
  const x = i => P + i * (W - 2 * P) / (series.length - 1);
  const y = v => H - P - (v - min) * (H - 2 * P) / (max - min || 1);
  const pts = series.map((s, i) => `${x(i)},${y(s[1])}`).join(" ");
  const area = `M${x(0)},${y(min)} L` + pts.replace(/ /g, " L") + ` L${x(series.length-1)},${y(min)} Z`;
  svg.innerHTML = `
    <defs><linearGradient id="g" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#3fd68f" stop-opacity=".25"/>
      <stop offset="100%" stop-color="#3fd68f" stop-opacity="0"/>
    </linearGradient></defs>
    <path d="${area}" fill="url(#g)"/>
    <polyline points="${pts}" fill="none" stroke="#3fd68f" stroke-width="2"
      stroke-linejoin="round" stroke-linecap="round"/>
    <text x="${W-P}" y="${y(max)+4}" fill="#3fd68f" font-size="11" text-anchor="end">${max}ns</text>`;
}

function pillbar(el, items, active, onclick){
  el.innerHTML = items.map(([k, label, n]) =>
    `<span class="pill click ${active === k ? "active" : ""}" data-k="${esc(k)}">${esc(label)}<span class="n">${n}</span></span>`
  ).join("");
  el.querySelectorAll(".pill").forEach(p =>
    p.addEventListener("click", () => onclick(p.dataset.k === active ? null : p.dataset.k)));
}

function cardKey(c){ return c.src + ":" + c.idx; }

function renderCards(){
  const el = $("journey");
  if (!DATA) return;
  let cards = DATA.cards;
  if (tierFilter)    cards = cards.filter(c => c.src === tierFilter);
  if (verdictFilter) cards = cards.filter(c => c.verdict === verdictFilter);
  if (q){
    const s = q.toLowerCase();
    cards = cards.filter(c => JSON.stringify(c).toLowerCase().includes(s));
  }
  if (!cards.length){ el.innerHTML = `<div class="empty">no attempts match</div>`; return; }
  el.innerHTML = cards.map(c => {
    const k = cardKey(c);
    const title = [c.strategy, c.block].filter(Boolean).join(" · ") || c.tier;
    const meta = [
      c.gain != null ? fmtGain(c.gain) : "",
      c.cost != null ? "$" + c.cost : "",
      c.model ? esc(c.model) : "",
      c.ts ? esc(c.ts) : "",
    ].filter(Boolean).join(" · ");
    const hasDetail = c.detail && Object.keys(c.detail).length;
    return `<div class="attempt ${c.kind} ${open.has(k) ? "open" : ""}" data-k="${k}">
      <div class="a-head">
        <span class="badge ${c.kind}">${esc(c.verdict || "event")}</span>
        <span class="a-title">${esc(title)}</span>
        <span class="a-meta">${meta}</span>
      </div>
      <p class="a-story">${esc(c.story)}</p>
      <div class="a-sub">${esc(c.tier)}</div>
      ${hasDetail ? `<span class="a-expand">details</span>
        <div class="a-detail"><pre>${esc(JSON.stringify(c.detail, null, 2).slice(0, 4000))}</pre></div>` : ""}
    </div>`;
  }).join("");
  el.querySelectorAll(".a-expand").forEach(x =>
    x.addEventListener("click", e => {
      const card = e.target.closest(".attempt");
      const k = card.dataset.k;
      open.has(k) ? open.delete(k) : open.add(k);
      card.classList.toggle("open");
    }));
}

function renderFilters(){
  const counts = {};
  const vcounts = {};
  for (const c of DATA.cards){
    counts[c.src] = (counts[c.src] || 0) + 1;
    vcounts[c.verdict] = (vcounts[c.verdict] || 0) + 1;
  }
  pillbar($("tier-pills"),
    Object.entries(counts).map(([k, n]) => [k, DATA.cards.find(c => c.src === k).tier, n]),
    tierFilter, k => { tierFilter = k; renderFilters(); renderCards(); });
  pillbar($("verdict-pills"),
    Object.entries(vcounts).map(([k, n]) => [k, k, n]),
    verdictFilter, k => { verdictFilter = k; renderFilters(); renderCards(); });
}

function renderBoard(board, chip){
  const el = $("board");
  if (!board || !board.length){ el.innerHTML = ""; return; }
  const min = Math.min(...board.map(b => Math.min(b.base, b.now))) - 0.3;
  const max = 0.3;
  const pct = v => ((v - min) / (max - min) * 100).toFixed(2) + "%";
  el.innerHTML = board
    .slice().sort((a,b) => a.now - b.now)
    .map(b => {
      const left = Math.min(b.base, b.now), right = Math.max(b.base, b.now);
      const improved = b.now > b.base;
      return `<div class="row">
        <span class="lbl">${esc(b.block)}</span>
        <div class="track">
          <div class="seg" style="left:${pct(left)};width:calc(${pct(right)} - ${pct(left)})"></div>
          <span class="pt base" style="left:${pct(b.base)}" title="baseline ${b.base}ns"></span>
          <span class="pt now" style="left:${pct(b.now)}" title="current ${b.now}ns"></span>
          <span class="target" style="left:${pct(0)}" title="target (timing met)"></span>
        </div>
        <span class="vals">${b.base} → <b class="${improved ? "gain-pos" : ""}">${b.now}</b></span>
      </div>`;
    }).join("");
  if (chip){
    const d = (chip.now_mhz - chip.pristine_mhz) / chip.pristine_mhz * 100;
    $("chipline").innerHTML =
      `Chip: ${esc(chip.label)} — pristine ${chip.pristine_mhz} MHz → <b>${chip.now_mhz} MHz</b> (+${d.toFixed(1)}%)`;
  }
}

async function tick(){
  try{
    DATA = await (await fetch("/api/data")).json();
    $("clock").textContent = "updated " + DATA.now;
    $("statedot").className = "dot " + (DATA.state === "run" ? "run" : DATA.state);
    $("status-line").textContent = DATA.status;
    $("proc-pills").innerHTML = procPills(DATA.procs);
    $("hero-stats").innerHTML = heroStats(DATA.totals);
    trend(DATA.series);
    renderBoard(DATA.board, DATA.chip);
    $("live-tail").textContent = DATA.live.tail || "(no run log)";
    $("live-age").textContent = DATA.live.age_s != null ? `· ${DATA.live.age_s}s ago` : "";
    $("legendbody").innerHTML = Object.entries(DATA.explain).map(([k, v]) =>
      `<div><b class="v-${esc(k).replace(/[^\w]/g,"_")}">${esc(k)}</b> — ${esc(v)}</div>`).join("");
    renderFilters();
    renderCards();
  }catch(e){
    $("clock").textContent = "fetch error";
  }
}

$("q").addEventListener("input", e => { q = e.target.value; renderCards(); });
document.addEventListener("keydown", e => {
  if (e.key === "/" && document.activeElement !== $("q")){ e.preventDefault(); $("q").focus(); }
  if (e.key === "Escape"){ $("q").blur(); }
});

tick();
setInterval(tick, 5000);


