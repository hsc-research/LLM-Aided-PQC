'use strict';
function element(tag, text, parent) {const node=document.createElement(tag); node.textContent=text; parent.appendChild(node); return node;}
function shown(value) {return value === null || value === undefined ? 'Unknown / not measured' : String(value);}
async function refresh() {
 const state=document.getElementById('state');
 try {
  const response=await fetch('/api/current', {cache:'no-store'}); if(!response.ok) throw new Error('HTTP '+response.status);
  const data=await response.json(); const main=document.getElementById('runs'); main.replaceChildren();
  state.textContent='Updated '+new Date().toLocaleTimeString()+'. '+data.notice;
  if(!data.runs.length) element('p','No current proposal records. Prepare a proposal under .pqc_runs/fpga-proposals/<run> to start tracking.',main);
  for(const run of data.runs){
   const card=element('article','',main); element('h2',run.id+' — '+run.status,card);
   const list=element('dl','',card);
   for(const [title,value] of [['Source profile',run.profile_fingerprint],['Target',run.target+' / '+run.tool+' '+run.tool_version+' / '+run.part],['Period (ns)',run.period_ns],['Measurement stage',run.measurement_stage],['Functional verification',run.functional_verification],['Candidate measurement',run.candidate_measurement],['Automatic acceptance',run.automatic_acceptance],['Model',run.model],['Generation requests attempted',run.api_calls_attempted],['Input tokens',run.input_tokens],['Output tokens',run.output_tokens],['Reported cost (USD)',run.reported_cost_usd],['Estimated maximum request cost (USD)',run.estimated_max_cost_usd]]){element('dt',title,list);element('dd',shown(value),list);}
   element('h3','Baseline observations (preliminary imported reports)',card); element('pre',JSON.stringify(run.observations,null,2),card);
   element('p','Comparison: '+run.comparison.status+'. '+run.comparison.reason,card);
   for(const note of run.notes) element('p',note,card);
   if(run.cost_note) element('p',run.cost_note,card);
  }
  for(const error of data.errors) element('p',error.id+': '+error.status+' — '+error.reason,main).className='warning';
 } catch(error) {state.textContent='Refresh failed; displayed information may be stale. '+error.message;}
}
document.getElementById('refresh').addEventListener('click',refresh); refresh(); setInterval(refresh,5000);
