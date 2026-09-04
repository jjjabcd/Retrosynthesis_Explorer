let currentJob = null, pollTimer = null, previewGeneration = 0;
const terminal = new Set(['completed', 'failed', 'cancelled', 'timed_out', 'interrupted']);
async function preview() {
  error(); const generation=++previewGeneration;
  $('preview-box').replaceChildren(element('span','Generating molecular preview…'));$('target-properties').replaceChildren();$('accessibility').replaceChildren();
  let data;
  try { data = await api('/api/molecule', {smiles:$('smiles').value}); }
  catch(e) { if(generation===previewGeneration)$('preview-box').replaceChildren(element('span','A valid SMILES is required for a preview.')); throw e; }
  if(generation!==previewGeneration)return;
  const image=element('img'); image.src=data.image; image.alt='Target molecule structure'; $('preview-box').replaceChildren(image);
  data.accessibility?.forEach(score=>{const card=element('div',undefined,'score-card');card.append(element('strong',`${score.name}: ${score.value===null?'Unavailable':value(score.value)}`),element('p',score.error || `Range ${score.range.join('–')}. ${score.note}`,'hint'));card.title=score.method;$('accessibility').append(card);});
  $('target-properties').replaceChildren(descriptorTable(data,true),element('p',`RDKit ${data.rdkit_version} · Computed descriptors`,'hint'));
}
function clearResults() {
  $('routes').replaceChildren(element('div','Routes will appear after the search.','empty'));
  $('export').hidden=true;
}
async function refreshHistory() {
  const jobs=await api('/api/jobs'); $('history').replaceChildren(new Option('Select a saved job',''));
  jobs.forEach(j=>$('history').add(new Option(`${new Date(j.started_at*1000).toLocaleString('en-US')} · ${j.status}`,j.id)));
  if(currentJob) $('history').value=currentJob;
  return jobs;
}
async function showRoutes(jobId) {
  const data=await api(`/api/jobs/${jobId}/routes`); if(currentJob!==jobId)return;
  $('routes').replaceChildren();$('export').href=`/api/jobs/${jobId}/export`;$('export').hidden=false;
  if(!data.summaries.length){$('routes').append(element('div','No routes were returned. Try a longer search or a different target.','empty'));return;}
  if(data.search_stats) $('routes').append(element('p',`${data.search_stats.solved_routes_found} distinct solved routes found · ${data.summaries.length} routes returned · Stopped: ${data.search_stats.stop_reason.replaceAll('_',' ')}`,'hint'));
  data.summaries.forEach(route=>{
    const button=element('a',undefined,'route');button.href=`/static/route.html?job=${encodeURIComponent(jobId)}&route=${route.id}`;const label=element('div',`Route ${route.id+1}`);
    label.append(element('small',`Total reaction steps: ${route.reaction_count} · Starting materials: ${route.starting_materials} · ${Object.entries(route.scores).map(([k,v])=>`${k==='state score'?'State score':k}: ${value(v)}`).join(' · ')}`));
    button.append(label,element('span',route.solved?'Solved':'Unsolved',route.solved?'solved':'unsolved'));
    $('routes').append(button);
  });
}
async function poll(jobId) {
  try {
    const job=await api(`/api/jobs/${jobId}`);if(currentJob!==jobId)return;
    $('status').textContent=job.status==='running'?job.phase:job.status.replaceAll('_',' ').replace(/^./,s=>s.toUpperCase());
    $('elapsed').textContent=`${job.elapsed_seconds}s elapsed · Search budget ${job.request.search_seconds}s · Total limit ${job.request.timeout_seconds}s`;
    $('cancel').disabled=terminal.has(job.status);$('run').disabled=!terminal.has(job.status);
    if(terminal.has(job.status)){if(job.error)error(job.error);if(job.status==='completed')await showRoutes(jobId);await refreshHistory();}
    else pollTimer=setTimeout(()=>poll(jobId),1000);
  } catch(e){error(e.message);if(currentJob===jobId)pollTimer=setTimeout(()=>poll(jobId),3000);}
}
async function openJob(jobId) {
  error();clearTimeout(pollTimer);currentJob=jobId;window.history.replaceState(null,'',`/?job=${encodeURIComponent(jobId)}`);clearResults();
  const job=await api(`/api/jobs/${jobId}`);if(currentJob!==jobId)return;
  $('smiles').value=job.request.smiles;
  [['seconds','search_seconds'],['timeout','timeout_seconds'],['iterations','iterations'],['steps','max_transforms']].forEach(([id,key])=>$(id).value=job.request[key]);
  $('candidate-target').value=job.request.solved_route_target ?? 0;$('return-routes').value=job.request.return_routes ?? 25;
  await preview();if(currentJob===jobId)poll(jobId);
}
$('preview').onclick=()=>preview().catch(e=>error(e.message));
$('smiles').addEventListener('input',()=>{previewGeneration++;$('preview-box').replaceChildren(element('span','Preview the updated SMILES to see its structure.'));$('target-properties').replaceChildren();$('accessibility').replaceChildren();});
$('run').onclick=async()=>{error();$('run').disabled=true;try{await preview();const job=await api('/api/jobs',{smiles:$('smiles').value,search_seconds:Number($('seconds').value),timeout_seconds:Number($('timeout').value),iterations:Number($('iterations').value),max_transforms:Number($('steps').value),solved_route_target:Number($('candidate-target').value),return_routes:Number($('return-routes').value)});clearTimeout(pollTimer);currentJob=job.id;window.history.replaceState(null,'',`/?job=${encodeURIComponent(job.id)}`);clearResults();poll(job.id);refreshHistory().catch(e=>error(e.message));}catch(e){error(e.message);$('run').disabled=false;}};
$('cancel').onclick=async()=>{try{await api(`/api/jobs/${currentJob}/cancel`,{});clearTimeout(pollTimer);poll(currentJob);}catch(e){error(e.message);}};
$('history').onchange=()=>{if($('history').value)openJob($('history').value).catch(e=>error(e.message));};
(async()=>{try{const h=await api('/api/health');$('connection').textContent=h.configured?'Local workspace · Ready':'Setup required';await preview();const jobs=await refreshHistory();const running=jobs.find(j=>!terminal.has(j.status));const saved=new URLSearchParams(location.search).get('job');if(saved)await openJob(saved);else if(running)await openJob(running.id);}catch(e){$('connection').textContent='Connection unavailable';error(e.message);}})();
