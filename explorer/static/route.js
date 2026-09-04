const params = new URLSearchParams(location.search);
const currentJob = params.get('job');
let routeGeneration = 0, exportBase = null, selectedNode = null;
async function selectRoute(jobId,index) {
  error(); const generation=++routeGeneration; $('export-image').disabled=true;$('export-properties').disabled=true;
  $('tree').replaceChildren(element('div','Generating retrosynthetic route…','empty'));$('properties').replaceChildren();$('descriptor-detail').replaceChildren();
  const base=`/api/jobs/${jobId}/routes/${index}`; const data=await api(base);if(generation!==routeGeneration || currentJob!==jobId)return;
  $('route-title').textContent=`Route ${index+1} · Retrosynthetic route`;
  const image=element('img'); image.alt=`Route ${index+1}, with molecule node IDs`;
  image.onload=()=>{if(generation!==routeGeneration)return;$('tree').replaceChildren(image);};
  image.onerror=()=>{if(generation!==routeGeneration)return;$('tree').replaceChildren(element('div','Image generation failed. Result JSON and properties remain available.','empty'));};image.src=base+'/image';
  exportBase=base;$('export-image').disabled=false;$('export-properties').disabled=false;
  $('export-node').replaceChildren(...data.nodes.map(n=>new Option(`${n.node_id} · ${n.role}`,n.node_id)));
  const table=element('table'),head=element('tr');['Node','Role','Stock','Formula','MW (g/mol)','cLogP','TPSA (Å²)'].forEach(t=>head.append(element('th',t)));table.append(head);
  data.nodes.forEach(node=>{const props=data.descriptors[node.molecule_key],row=element('tr'),cell=element('td'),btn=element('button',node.node_id);
    btn.onclick=()=>{selectedNode=node.node_id;$('export-node').value=selectedNode;table.querySelectorAll('button').forEach(b=>b.setAttribute('aria-pressed',String(b===btn)));$('descriptor-detail').replaceChildren(element('p',`${node.node_id} · ${props.canonical_smiles}`,'hint'),descriptorTable(props));};cell.append(btn);row.append(cell);
    [node.role,node.in_stock?'In stock':'Not in stock'].forEach(t=>row.append(element('td',t)));props.values.slice(0,4).forEach(p=>row.append(propertyCell(p)));table.append(row);
  });$('properties').className='';$('properties').replaceChildren(table);
  const first=data.descriptors[data.nodes[0].molecule_key];$('method-note').textContent=`RDKit ${first.rdkit_version} · Computed descriptors, not experimental measurements. Node IDs match the tree. Select a node to see all properties and units.`;
  table.querySelector('button')?.click();
}

(async()=>{
  const routeParam=params.get('route');
  if(!currentJob || !/^[a-f0-9]{32}$/.test(currentJob) || !/^\d+$/.test(routeParam || '') || !Number.isSafeInteger(Number(routeParam))) {
    error('This route link is invalid. Return to the route list and select a route.');
    $('route-summary').textContent='Route unavailable';
    return;
  }
  $('back-to-routes').href=`/?job=${encodeURIComponent(currentJob)}`;
  const index=Number(routeParam);
  try {
    const job=await api(`/api/jobs/${currentJob}`);
    $('route-summary').textContent=`Route ${index+1} · ${job.request.smiles}`;
    document.title=`Route ${index+1} · Retrosynthesis Explorer`;
    await selectRoute(currentJob,index);
  } catch(e) {
    error(e.message);
    $('tree').replaceChildren(element('div','This route could not be loaded. Return to the route list and try again.','empty'));
  }
})();

function exportOptions(resetScope=false) {
  const images=$('export-kind').value==='image';
  if(resetScope) $('export-scope').replaceChildren(...(images ? [['route','Entire retrosynthetic route'],['node','One molecule'],['all','All molecules (separate files)']] : [['route','All molecules in this route'],['node','One molecule']]).map(([v,t])=>new Option(t,v)));
  const scope=$('export-scope').value, oldFormat=$('export-format').value;
  const formats=images ? (scope==='route'?['png']:['png','svg']) : ['csv','json'];
  $('export-format').replaceChildren(...formats.map(f=>new Option(f.toUpperCase(),f)));
  if(formats.includes(oldFormat)) $('export-format').value=oldFormat;
  $('node-selection').hidden=scope!=='node';
  $('export-note').textContent=images ? (scope==='all'?'Download a ZIP with a separate image for each node and a node-ID manifest. Repeated molecules keep their node IDs.':scope==='node'?'Export the selected molecule as a standalone structure image.':'Export the complete route with structures, connections and node IDs.') : 'Export calculated properties with units and node IDs. JSON also retains calculation provenance.';
}
function openExport(kind) {
  $('export-kind').value=kind;exportOptions(true);
  if(kind==='properties' && selectedNode) $('export-node').value=selectedNode;
  $('export-error').hidden=true;$('export-dialog').showModal();
}
$('export-image').onclick=()=>openExport('image');
$('export-properties').onclick=()=>openExport('properties');
$('close-export').onclick=()=>$('export-dialog').close();
$('export-kind').onchange=()=>exportOptions(true);
$('export-scope').onchange=()=>exportOptions();
$('export-form').onsubmit=async event=>{
  event.preventDefault();$('export-error').hidden=true;$('export-download').disabled=true;$('export-download').textContent='Preparing…';
  try {
    const query=new URLSearchParams({kind:$('export-kind').value,scope:$('export-scope').value,format:$('export-format').value});
    if($('export-scope').value==='node')query.set('node_id',$('export-node').value);
    const response=await fetch(`${exportBase}/export?${query}`);
    if(!response.ok){const failure=await response.json();throw new Error(typeof failure.detail==='string'?failure.detail:'Export failed. Please try again.');}
    const url=URL.createObjectURL(await response.blob()), link=element('a');link.href=url;
    link.download=response.headers.get('Content-Disposition')?.match(/filename="([^"]+)"/)?.[1] || 'export';
    document.body.append(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(url),60000);
    $('export-dialog').close();
  } catch(e){$('export-error').textContent=e.message;$('export-error').hidden=false;}
  finally{$('export-download').disabled=false;$('export-download').textContent='Download';}
};
