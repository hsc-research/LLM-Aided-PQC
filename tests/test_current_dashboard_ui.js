// Offline DOM behavior checks. Does not claim a full browser accessibility audit.
const fs=require('fs'),vm=require('vm'),assert=require('assert');
class Node {
 constructor(tag='div'){this.tag=tag;this.textContent='';this.children=[];this.value='';this.checked=true;this.attrs={};this.listeners={};}
 appendChild(n){this.children.push(n);return n;}replaceChildren(){this.children=[];}addEventListener(type,fn){this.listeners[type]=fn;}setAttribute(k,v){this.attrs[k]=v;}contains(n){return this===n||this.children.some(x=>x.contains(n));}
}
const nodes={};for(const id of ['state','runs','refresh','run-select','auto-refresh','overview','errors'])nodes[id]=new Node();
let fail=false;const record={id:'<img src=x onerror=alert(1)>',status:'PROMPT_PREPARED_NO_API_CALL',notes:[],observations:{metrics:{worst_setup_slack_ns:.293,worst_hold_slack_ns:.201},warnings:{no_clock:198}},comparison:{status:'BLOCKED',reason:'No candidate'}};
let data={runs:[record],errors:[],notice:'Read-only'},tick;
const document={createElement:tag=>new Node(tag),getElementById:id=>nodes[id],activeElement:null};
const context={document,fetch:async()=>{if(fail)throw Error('offline');return{ok:true,json:async()=>data}},setInterval:fn=>{tick=fn;},Date,JSON,String,Error};
vm.createContext(context);vm.runInContext(fs.readFileSync('agent/dashboard_static/current.js','utf8'),context);
const text=n=>n.textContent+' '+n.children.map(text).join(' ');
const descendants=n=>[n,...n.children.flatMap(descendants)];
const settle=()=>new Promise(resolve=>setImmediate(resolve));
(async()=>{
 await settle();await context.refresh(true);
 assert.equal(nodes.runs.children.length,1);const original=nodes.runs.children[0];assert(text(original).includes('<img'));
 assert(text(original).includes('Baseline and candidate comparison'));assert(text(original).includes('Not run'));assert(text(original).includes('Hold slack (ns)'));assert(text(original).includes('0.293'));assert(text(original).includes('0.201'));
 const ds=descendants(original);assert(ds.some(n=>n.tag==='caption'));assert(ds.filter(n=>n.tag==='th').every(n=>['row','col'].includes(n.attrs.scope)));
 await context.refresh(false);assert.strictEqual(nodes.runs.children[0],original,'Unchanged polling must not replace focused/read content');
 document.activeElement=original.children[0];data={runs:[{...record,status:'RUNNING'}],errors:[]};await context.refresh(false);assert.strictEqual(nodes.runs.children[0],original);assert(nodes.state.textContent.includes('New records'));
 document.activeElement=null;await context.refresh(true);assert(text(nodes.runs).includes('Waiting for model'));
 nodes['auto-refresh'].checked=false;nodes['auto-refresh'].listeners.change();assert(nodes.state.textContent.includes('paused'));const before=nodes.runs.children[0];tick();await settle();assert.strictEqual(nodes.runs.children[0],before);
 fail=true;await context.refresh(true);assert(nodes.state.textContent.includes('may be stale'));assert.strictEqual(nodes.runs.children[0],before);
 fail=false;data={runs:[{...record,kind:'asic_measurement',target:'asic',measurement_role:'candidate',technology:'test-library',observations:{metrics:{area:123.5,area_unit:'um^2',total_power_w:null},critical_paths:[{startpoint:'a/Q',endpoint:'b/D',path_type:'Setup',slack_ns:-.1}]}}],errors:[]};await context.refresh(true);assert(text(nodes.runs).includes('ASIC design measurement'));assert(text(nodes.runs).includes('123.5'));assert(text(nodes.runs).includes('um^2'));assert(text(nodes.runs).includes('No matched record'));assert(text(nodes.runs).includes('a/Q'));assert(!text(nodes.runs).includes('FPGA part'));
 fail=false;data={runs:[],errors:['Run directory symlink refused']};await context.refresh(true);assert(text(nodes.errors).includes('symlink refused'));assert(text(nodes.runs).includes('No current run records'));
 console.log('Dashboard DOM tests passed: tables, safe text, stable polling, focus preservation, pause, failure, empty/error states');
})().catch(e=>{console.error(e);process.exitCode=1});
