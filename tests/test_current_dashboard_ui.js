// Offline DOM exercise: repeated refresh, hostile text, and failed reload.
const fs=require('fs'), vm=require('vm'), assert=require('assert');
class Node {constructor(){this.textContent='';this.children=[];}appendChild(n){this.children.push(n);}replaceChildren(){this.children=[];}addEventListener(){}}
const nodes={state:new Node(),runs:new Node(),refresh:new Node()};
let fail=false;
const record={id:'<img src=x onerror=alert(1)>',status:'PROMPT_PREPARED_NO_API_CALL',notes:[],observations:{},comparison:{status:'BLOCKED',reason:'No candidate'}};
const context={document:{createElement:()=>new Node(),getElementById:id=>nodes[id]},fetch:async()=>{if(fail)throw Error('offline');return{ok:true,json:async()=>({runs:[record],errors:[],notice:'Read-only'})}},setInterval:()=>{},Date,JSON,String,Error};
vm.createContext(context);vm.runInContext(fs.readFileSync('agent/dashboard_static/current.js','utf8'),context);
(async()=>{await context.refresh();await context.refresh();assert.equal(nodes.runs.children.length,1);assert(nodes.runs.children[0].children[0].textContent.includes('<img'));fail=true;await context.refresh();assert(nodes.state.textContent.includes('may be stale'));assert.equal(nodes.runs.children.length,1);console.log('Current dashboard UI repeated refresh, text-only rendering, and interruption tests passed');})().catch(e=>{console.error(e);process.exitCode=1});
