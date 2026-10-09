/* Shared page shell and assembly workspace; electrical endpoints come from wiring.yaml. */
(() => {
  'use strict';
  const root=document.getElementById('assembly-guide'), data=document.getElementById('guide-data');
  if(!root || !data) return;
  const D=JSON.parse(data.textContent);
  const ASSETS=new URL('.',document.currentScript.src), SITE=new URL('../',ASSETS);
  const esc=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const page=root.dataset.page || 'intro';
  const pages=[['intro','Introduction'],['bom','BOM'],['wiring','Wiring'],['tubing','Tubing']];
  const pageURL=(name,hash='')=>new URL((name==='intro'?'':name+'/')+hash,SITE).href;
  const storageKey='autolever-guide';
  let saved={}, persistent=true;
  try {saved=JSON.parse(localStorage.getItem(storageKey)||'{}')||{};} catch {persistent=false;}
  if(typeof saved!=='object'||Array.isArray(saved)) saved={};
  const checked=key=>saved[key]===true;
  const save=(key,value)=>{saved[key]=value;try{localStorage.setItem(storageKey,JSON.stringify(saved));}catch{persistent=false;}};
  // a tick belongs to one exact connection: change either end and it is unchecked again
  const wireKey=w=>`wire-${w.no}:${w.a}:${w.b}`, tubeKey=t=>`tube-${t.id}:${t.from}:${t.to}`, bomKey=p=>`bom-${p.id}:${p.part}`;
  const state={step:0,wire:0,tube:0,scope:page==='tubing'?'all':'step',zoom:1,expanded:false,search:''};
  const colors={WH:'#fff',BU:'#347bdc',BN:'#956238',BK:'#273039',GY:'#929ea9',DIODE:'#29363a'};
  const isDiagram=page==='wiring'||page==='tubing';
  const button=(text,action,extra='')=>`<button type="button" data-action="${action}" ${extra}>${text}</button>`;
  const count=(items,key)=>items.filter(x=>checked(key(x))).length;
  function navigate(view,index=0,wire=0) {
    const hash=view==='wiring'?`${D.steps[index].id}/${D.steps[index].wires[wire].no}`:view==='tubing'?String(index+1):'';
    if(view!==page) {location.href=pageURL(view,hash?'#'+hash:'');return;}
    if(location.hash.slice(1)===hash) {readHash();render();} else location.hash=hash;
  }
  function readHash() {
    const bits=location.hash.slice(1).split('/');
    if(page==='wiring') {
      if(bits[0]==='wiring') bits.shift();
      const i=D.steps.findIndex(s=>s.id===bits[0]);state.step=i>=0?i:0;
      const j=D.steps[state.step].wires.findIndex(w=>w.no===bits[1]);state.wire=j>=0?j:0;
    }
    if(page==='tubing') state.tube=Math.max(0,Math.min(D.tubes.length-1,(Number(bits[0])||1)-1));
  }
  let board, stopSizing;
  function render() {
    stopSizing?.();
    board?.destroy();board=null;
    root.classList.toggle('ag-diagram-page',isDiagram);
    root.classList.toggle('ag-expanded',state.expanded);
    root.innerHTML=`<header class="ag-top"><div class="ag-top-inner"><a class="ag-brand" href="${pageURL('intro')}"><img class="ag-mark" src="${new URL('autolever.svg',ASSETS)}" alt="" width="36" height="36"><span class="ag-wordmark">Auto<span>Lever</span></span><span class="ag-brand-label">BUILD GUIDE</span></a></div></header>
    <main class="ag-main"><nav class="ag-nav" aria-label="Guide pages">${pages.map(([id,title])=>`<a href="${pageURL(id)}" ${id===page?'aria-current="page"':''}>${title}</a>`).join('')}</nav><p class="ag-warning" role="note"><b>⚠ Safety</b> ${esc(D.intro.warning)}</p><div id="ag-content">${page==='intro'?renderIntro():page==='bom'?renderBOM():renderAssembly()}</div>
    <footer class="ag-footer"><span>${isDiagram?(persistent?'Progress saved in this browser':'Storage unavailable · progress lasts for this visit'):'AutoLever · pneumatic press drive'}${D.revision?' · revision '+esc(D.revision):''}</span>${button('Print','print')}</footer></main>`;
    bind();
    if(page==='wiring') {
      board=window.mountGuideBoard?.(root.querySelector('.ag-board-canvas'),D,{step:state.step,wire:state.wire,scope:state.scope,zoom:state.zoom,select(no){const i=D.steps.findIndex(s=>s.wires.some(w=>w.no===no));navigate('wiring',i,D.steps[i].wires.findIndex(w=>w.no===no));}});
      root.querySelectorAll('[data-wire]').forEach(row=>{
        const no=D.steps[state.step].wires[Number(row.dataset.wire)].no;
        row.onmouseenter=()=>board?.highlight(no,true);
        row.onmouseleave=()=>board?.highlight(no,no===D.steps[state.step].wires[state.wire].no);
      });
    } else if(page==='tubing') board=mountTubing();
    if(isDiagram) stopSizing=fitWorkspace();
    updateScreenButton();
    // phones: bring the current step into the strip without moving the page
    const strip=root.querySelector('.ag-steps'),current=strip?.querySelector('[aria-current]');
    if(current){const a=strip.getBoundingClientRect(),b=current.getBoundingClientRect();strip.scrollLeft+=b.left-a.left-(a.width-b.width)/2;}
  }
  const twoColumns=matchMedia('(min-width:900px)');
  function fitWorkspace() {
    const canvas=root.querySelector('.ag-board-canvas');
    let frame;
    const fit=()=>{
      cancelAnimationFrame(frame);
      frame=requestAnimationFrame(()=>{
        if(state.expanded)return;
        const below=root.querySelectorAll(twoColumns.matches?'.ag-board-legend':'.ag-board-legend, .ag-board-toolbar, .ag-connection-detail, .ag-wire-navigation');
        const reserved=[...below].reduce((sum,el)=>{
          const style=getComputedStyle(el);
          return sum+el.getBoundingClientRect().height+parseFloat(style.marginTop)+parseFloat(style.marginBottom);
        },14);
        const top=canvas.getBoundingClientRect().top+window.scrollY;
        // stacked layout: never smaller than half the screen or the diagram's own height at full width
        const floor=twoColumns.matches?120:Math.min(Math.round(window.innerHeight*.5),Math.round(canvas.clientWidth*(page==='tubing'?.4:.63)));
        canvas.style.setProperty('--ag-canvas-height',Math.max(floor,window.innerHeight-top-reserved)+'px');
      });
    };
    const observer=new ResizeObserver(fit);
    root.querySelectorAll('.ag-top, .ag-nav, .ag-warning, .ag-page-heading, .ag-steps, .ag-work-heading, .ag-board-toolbar, .ag-board-legend, .ag-connection-detail, .ag-wire-navigation').forEach(el=>observer.observe(el));
    window.addEventListener('resize',fit);fit();
    return ()=>{observer.disconnect();window.removeEventListener('resize',fit);cancelAnimationFrame(frame);};
  }
  // intro sections: a list item is text or [bold lead, text]; a section has list, steps or text
  const item=t=>Array.isArray(t)?`<b>${esc(t[0])}</b> ${esc(t[1])}`:esc(t);
  const paragraphs=(text,className)=>(Array.isArray(text)?text:[text]).map(t=>`<p class="${className}">${esc(t)}</p>`).join('');
  const block=s=>s.steps?`<ol class="ag-list">${s.steps.map(t=>`<li>${item(t)}</li>`).join('')}</ol>`
    :s.list?`<ul class="ag-list">${s.list.map(t=>`<li>${item(t)}</li>`).join('')}</ul>`:paragraphs(s.text,'ag-text');
  function renderIntro() {
    const I=D.intro;
    return `<section class="ag-intro"><div class="ag-intro-copy"><h1>${esc(I.title)}</h1>${paragraphs(I.lead,'ag-lead')}${I.sections.map(s=>`<h2>${esc(s.title)}</h2>${block(s)}`).join('')}</div>
      <aside class="ag-intro-media" aria-label="Video and image">
        <figure class="ag-media-placeholder ag-media-video">
          <svg viewBox="0 0 48 48" aria-hidden="true" focusable="false"><rect x="5" y="10" width="38" height="28" rx="5"/><path d="m20 17 11 7-11 7Z"/></svg>
          <figcaption>Video placeholder</figcaption>
        </figure>
        <figure class="ag-media-placeholder ag-media-image">
          <svg viewBox="0 0 48 48" aria-hidden="true" focusable="false"><rect x="5" y="5" width="38" height="38" rx="5"/><circle cx="16" cy="16" r="4"/><path d="m5 35 12-12 9 9 7-7 10 10"/></svg>
          <figcaption>Image placeholder</figcaption>
        </figure>
      </aside></section>`;
  }
  function stepNavigation(tubing) {
    const steps=tubing?D.tubes:D.steps;
    return `<nav class="ag-steps" aria-label="${tubing?'Tubing':'Wiring'} steps">${steps.map((s,i)=>{
      const total=tubing?1:s.wires.length, done=tubing?Number(checked(tubeKey(s))):count(s.wires,wireKey);
      return `<button type="button" ${tubing?'data-tube':'data-step'}="${i}" ${i===(tubing?state.tube:state.step)?'aria-current="step"':''}><span class="ag-step-id ${done===total?'complete':''}">${done===total?'✓':tubing?i+1:s.id}</span><span><b>${esc(s.title)}</b><small>${done} / ${total}</small></span></button>`;
    }).join('')}</nav>`;
  }
  function toolbar(tubing) {
    return `<div class="ag-board-toolbar"><label>Show <select id="ag-wire-scope" aria-label="Visible connections"><option value="step" ${state.scope==='step'?'selected':''}>This step</option>${!tubing?`<option value="single" ${state.scope==='single'?'selected':''}>Selected wire</option>`:''}<option value="all" ${state.scope==='all'?'selected':''}>All connections</option></select></label><div class="ag-board-controls">${button('−','zoom-out','aria-label="Zoom out"')}${button('Fit','zoom-fit')}${button('+','zoom-in','aria-label="Zoom in"')}${button('⛶ Fullscreen','fullscreen','class="ag-fullscreen-button"')}</div></div>`;
  }
  function connectionSummary(from,to,key,diode=false,cable='') {
    return `<div class="ag-connection-detail"><div><small>FROM${diode?' · RING END':''}</small><strong>${esc(from)}</strong></div><span class="ag-detail-arrow">→</span><div><small>TO${diode?' · PLAIN END':''}</small><strong>${esc(to)}</strong></div>${cable?`<div class="ag-cable"><small>CABLE</small><strong>${esc(cable)}</strong></div>`:''}<label class="ag-verify"><input type="checkbox" data-check="${key}" ${checked(key)?'checked':''}>${checked(key)?'Checked':'Mark checked'}</label></div>`;
  }
  function renderAssembly() {
    const tubing=page==='tubing', s=tubing?D.tubes[state.tube]:D.steps[state.step], w=tubing?null:s.wires[state.wire];
    const done=tubing?count(D.tubes,tubeKey):count(D.steps.flatMap(s=>s.wires),wireKey);
    const total=tubing?D.tubes.length:D.steps.flatMap(s=>s.wires).length;
    const first=tubing?state.tube===0:state.step===0&&state.wire===0;
    const last=tubing&&state.tube===D.tubes.length-1;
    const next=tubing?'Next connection →':state.wire===s.wires.length-1?(state.step===D.steps.length-1?'Open tubing →':'Next step →'):'Next connection →';
    return `<section class="ag-workspace"><div class="ag-page-heading"><h1>${tubing?'Tubing':'Wiring'}</h1><span class="ag-progress">${done} / ${total} checked</span></div>${stepNavigation(tubing)}<div class="ag-work"><div class="ag-work-heading"><h2>${esc(s.title)}</h2></div>
    <div class="ag-panel ag-full-board"><div class="ag-board-canvas" tabindex="0" role="region" aria-label="${tubing?'Pneumatic tubing diagram':'Wiring board'}">${tubing?`<div class="ag-air-paper">${airDiagram(state.tube)}</div>`:'<span class="ag-board-loading">Loading board…</span>'}</div><div class="ag-board-legend"><span>${tubing?'6 × 4 mm tube · schematic':'<i class="ag-diode-key"></i>Silver ring = cathode'}</span><span>Green = selected connection</span></div></div>
    ${toolbar(tubing)}
    ${connectionSummary(tubing?s.from:w.la,tubing?s.to:w.lb,tubing?tubeKey(s):wireKey(w),!tubing&&w.col==='DIODE',tubing||w.col==='DIODE'?'':[w.cable,w.size].filter(Boolean).join(' · '))}
    <div class="ag-wire-navigation">${button('← Previous',tubing?'prev-tube':'prev-wire',`class="ag-quiet" ${first?'disabled':''}`)}<span>${tubing?state.tube+1:state.wire+1} / ${tubing?D.tubes.length:s.wires.length}</span>${button(last?'Last connection':next,tubing?'next-tube':'next-wire',`class="ag-primary" ${last?'disabled':''}`)}</div>
    <div class="ag-list-heading"><h3>${tubing?'All tubing connections':'Connections in this step'}</h3></div><div class="ag-wire-list">${tubing?D.tubes.map((t,i)=>connectionRow(i+1,t.from,t.to,tubeKey(t),checked(tubeKey(t)),i===state.tube,'tube',i)).join(''):s.wires.map((v,i)=>connectionRow(v.no,v.a.replace(':',' · '),v.b.replace(':',' · '),wireKey(v),checked(wireKey(v)),i===state.wire,'wire',i,v.col)).join('')}</div>
    </div></section>`;
  }
  function connectionRow(no,from,to,key,done,selected,kind,index,color) {
    return `<div class="ag-wire-row ${selected?'selected':''} ${done?'is-done':''}"><input type="checkbox" data-check="${key}" aria-label="Connection ${esc(no)} checked" ${done?'checked':''}><button type="button" data-${kind}="${index}" ${selected?'aria-current="true"':''}><span class="ag-wire-number">${esc(no)}</span><span>${esc(from)}</span><span class="ag-row-arrow">→</span><span>${esc(to)}</span>${color?`<span class="ag-row-color"><i style="--wire:${colors[color]}"></i>${esc(color)}</span>`:''}</button></div>`;
  }
  const svgText=(x,y,t,cls='',extra='')=>`<text x="${x}" y="${y}" class="${cls}" ${extra}>${esc(t)}</text>`;
  const svgStart=(label,view)=>`<svg viewBox="${view}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="${esc(label)}"><rect width="100%" height="100%" fill="#fff"/>`;
  function airDiagram(active) {
    let svg=svgStart('Air supply through filter regulator, shut-off and pressure switch tee to P. A to cylinder cap end, B to rod end. R and S to silencers. Selected connection '+(active+1)+'.','0 0 1000 400');
    const paths=['M110 260H160','M270 260H305','M375 260H440','M440 260H535','M595 220V137H770V105','M690 220V167H880V105','M610 310V351 M700 310V351'];
    paths.forEach((d,i)=>{if(state.scope!=='all'&&i!==active)return;svg+=`<g data-air-route="${i}" role="button" tabindex="0" aria-label="${esc(D.tubes[i].title)}"><path d="${d}" stroke="transparent" stroke-width="18" fill="none"/><path d="${d}" stroke="${i===active?'#21634c':'#7694b2'}" stroke-width="${i===active?6:3}" fill="none" stroke-linejoin="round" stroke-linecap="round"/></g>`;});
    svg+=`<path d="M440 260V197" stroke="#b8c8ce" stroke-width="3"/><circle cx="440" cy="260" r="6" fill="${[2,3].includes(active)?'#21634c':'#879ca3'}"/>
      <rect x="15" y="232" width="95" height="56" rx="8" fill="#fff" stroke="#b7c6c4"/>${svgText(62,253,'AIR','svg-id','text-anchor="middle"')}${svgText(62,275,'7–10 bar','svg-sub','text-anchor="middle"')}
      <rect x="160" y="216" width="110" height="88" rx="8" fill="#fff" stroke="#b7c6c4"/><circle cx="215" cy="201" r="20" fill="#fff" stroke="#94aaa3"/><path d="M215 201L224 191" stroke="#346453" stroke-width="2"/>${svgText(215,247,'FRL','svg-id','text-anchor="middle"')}${svgText(215,271,'IN → OUT','svg-sub','text-anchor="middle"')}${svgText(215,330,'Filter-regulator','svg-sub','text-anchor="middle"')}
      <rect x="305" y="236" width="70" height="48" rx="7" fill="#fff" stroke="#b7c6c4"/><path d="M340 284V302M333 296L340 304L347 296" fill="none" stroke="#8ba4ab" stroke-width="2"/>${svgText(340,265,'3/2','svg-pin','text-anchor="middle"')}${svgText(340,322,'shut-off, vents','svg-sub','text-anchor="middle"')}
      <rect x="396" y="151" width="88" height="47" rx="7" fill="#fff" stroke="#b7c6c4"/>${svgText(440,178,'QPM11','svg-pin','text-anchor="middle"')}${svgText(440,293,'6 mm tee','svg-sub','text-anchor="middle"')}
      <rect x="535" y="220" width="215" height="90" rx="9" fill="#fff" stroke="#b7c6c4"/>${svgText(643,260,'5/3 VALVE','svg-id','text-anchor="middle"')}${svgText(643,282,'exhaust centre','svg-sub','text-anchor="middle"')}
      <rect x="748" y="53" width="162" height="52" rx="6" fill="#fff" stroke="#8ea6a0" stroke-width="2"/><rect x="818" y="56" width="10" height="46" fill="#9caeab"/><path d="M828 79H973" stroke="#93a5a2" stroke-width="9"/>${svgText(818,34,'DSNU CYLINDER','svg-id','text-anchor="middle"')}
      ${svgText(756,122,'cap end','svg-tiny','text-anchor="end"')}${svgText(917,125,'rod end','svg-tiny','text-anchor="middle"')}
      ${[[770,137],[880,167]].map(([x,y])=>`<rect x="${x-13}" y="${y-12}" width="26" height="24" rx="4" fill="#fff" stroke="#8aa3ad"/><path d="M${x-7} ${y+6}L${x+7} ${y-6}M${x+2} ${y-7}H${x+8}V${y-1}" fill="none" stroke="#476875" stroke-width="1.7"/>`).join('')}
      ${svgText(816,196,'2 × meter-out controls','svg-sub','text-anchor="middle"')}
      ${[[535,260,'P',502,236],[595,220,'A',580,204],[690,220,'B',680,204],[610,310,'R',583,332],[700,310,'S',712,332]].map(([x,y,label,tx,ty])=>`<circle cx="${x}" cy="${y}" r="5" fill="#fff" stroke="#66877e" stroke-width="2"/>${svgText(tx,ty,label,'svg-port')}`).join('')}
      ${[610,700].map(x=>`<rect x="${x-12}" y="350" width="24" height="20" rx="3" fill="#eff3f3" stroke="#8ba4ab"/><path d="M${x-8} 356H${x+8}M${x-8} 362H${x+8}" stroke="#8ba4ab"/>`).join('')}${svgText(654,390,'R + S → atmosphere','svg-sub','text-anchor="middle"')}`;
    return svg+'</svg>';
  }
  function mountTubing() {
    const canvas=root.querySelector('.ag-board-canvas'), paper=canvas.querySelector('.ag-air-paper');
    let zoom=state.zoom;
    function fit() {const scale=Math.min(canvas.clientWidth/1000,canvas.clientHeight/400)*zoom;paper.style.width=1000*scale+'px';paper.style.height=400*scale+'px';}
    const observer=new ResizeObserver(fit);observer.observe(canvas);fit();canvas.dataset.ready='true';
    canvas.querySelectorAll('[data-air-route]').forEach(link=>{
      const select=()=>navigate('tubing',Number(link.dataset.airRoute));
      link.onclick=select;
      link.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();select();}};
    });
    let drag;
    canvas.onpointerdown=e=>{if(e.pointerType==='touch'||e.target.closest('[data-air-route]'))return;drag={x:e.clientX,y:e.clientY,left:canvas.scrollLeft,top:canvas.scrollTop};canvas.setPointerCapture(e.pointerId);};
    canvas.onpointermove=e=>{if(drag){canvas.scrollLeft=drag.left+drag.x-e.clientX;canvas.scrollTop=drag.top+drag.y-e.clientY;}};
    canvas.onpointerup=canvas.onpointercancel=()=>{drag=null;};
    return {destroy(){observer.disconnect();},zoom(value){zoom=value;fit();},fit(){zoom=1;fit();canvas.scrollTo(0,0);}};
  }
  function filteredParts() {return D.bom.filter(p=>`${p.part} ${p.spec} ${p.group}`.toLowerCase().includes(state.search.toLowerCase()));}
  function renderBOM() {
    return `<section><div class="ag-page-heading"><div><h1>BOM</h1><p>Feel free to substitute as required for local availability and cost. Cable and tube lengths are estimates.</p></div><div class="ag-bom-actions"><span class="ag-progress">${count(D.bom,bomKey)} / ${D.bom.length} checked</span>${button('↓ Export CSV','export','class="ag-primary"')}</div></div><div class="ag-bom-tools"><label class="ag-search"><input type="search" id="ag-search" placeholder="Find a component…" aria-label="Search BOM" value="${esc(state.search)}"></label></div><div id="ag-bom-results">${bomRows()}</div></section>`;
  }
  function bomRows() {
    const parts=filteredParts();
    if(!parts.length)return '<div class="ag-empty">No matching components.</div>';
    let group='';
    const image=p=>p.image?new URL(p.image,ASSETS):p.photo?new URL('parts/'+p.photo+'.jpg',ASSETS):null;
    const row=p=>{
      const head=p.group!==group?`<tr class="ag-group"><th colspan="3" scope="rowgroup">${esc(group=p.group)}</th></tr>`:'';
      const link=p.makerworld?` <a class="ag-source-link" href="${esc(p.makerworld)}" target="_blank" rel="noopener">MakerWorld ↗</a>`:'';
      const done=checked(bomKey(p));
      return `${head}<tr class="${done?'is-done':''}"><td class="ag-qty"><label class="ag-have"><input type="checkbox" data-check="${esc(bomKey(p))}" aria-label="${esc(p.part)} checked" ${done?'checked':''}>${esc(p.qty)}</label></td><td><div class="ag-part-cell">${image(p)?`<img src="${image(p)}" alt="" loading="lazy">`:''}<div><strong>${esc(p.part)}</strong></div></div></td><td>${esc(p.spec)}${link}</td></tr>`;
    };
    return `<div class="ag-bom-table"><table><caption class="ag-sr">Bill of materials</caption><thead><tr><th scope="col">Qty</th><th scope="col">Component</th><th scope="col">Specification</th></tr></thead><tbody>${parts.map(row).join('')}</tbody></table></div><p class="ag-result-count">${parts.length} / ${D.bom.length} components</p>`;
  }
  function exportCSV() {
    const rows=[['Group','Component','Specification','Quantity','MakerWorld'],...filteredParts().map(p=>[p.group,p.part,p.spec,p.qty,p.makerworld||''])];
    const cell=v=>'"'+String(v).replace(/"/g,'""')+'"';
    const blob=new Blob(['\ufeff'+rows.map(r=>r.map(cell).join(',')).join('\r\n')],{type:'text/csv;charset=utf-8'});
    const url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='autolever-bom.csv';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
  }
  function moveWire(dir) {
    let i=state.step,j=state.wire+dir;
    if(j<0){i--;if(i<0)return;j=D.steps[i].wires.length-1;}
    if(j>=D.steps[i].wires.length){i++;j=0;}
    if(i>=D.steps.length)return navigate('tubing');
    navigate('wiring',i,j);
  }
  function updateScreenButton(){root.querySelectorAll('[data-action=fullscreen]').forEach(b=>{b.textContent=state.expanded?'⤢ Exit fullscreen':'⛶ Fullscreen';b.setAttribute('aria-pressed',String(state.expanded));});document.body.classList.toggle('ag-no-scroll',state.expanded);}
  async function toggleScreen(){
    if(state.expanded){if(document.fullscreenElement===root)await document.exitFullscreen();state.expanded=false;}
    else{state.expanded=true;root.classList.add('ag-expanded');try{await root.requestFullscreen();}catch{}}
    root.classList.toggle('ag-expanded',state.expanded);updateScreenButton();
  }
  document.addEventListener('fullscreenchange',()=>{if(!document.fullscreenElement){state.expanded=false;root.classList.remove('ag-expanded');updateScreenButton();}});
  document.addEventListener('keydown',e=>{if(e.key==='Escape'&&state.expanded&&!document.fullscreenElement)toggleScreen();});
  function bindChecks(scope){
    // a BOM row toggles its tick wherever you click it (the box, its label and links keep their own click)
    scope.querySelectorAll('.ag-bom-table [data-check]').forEach(box=>box.closest('tr').onclick=e=>{if(!e.target.closest('input,label,a'))box.click();});
    scope.querySelectorAll('[data-check]').forEach(box=>box.onchange=()=>{
      const key=box.dataset.check,sel=`[data-check="${CSS.escape(key)}"]`,index=[...root.querySelectorAll(sel)].indexOf(box);
      save(key,box.checked);render();
      root.querySelectorAll(sel)[index]?.focus({preventScroll:true});
    });
  }
  function bind(){
    const scope=root.querySelector('#ag-wire-scope');if(scope)scope.onchange=()=>{state.scope=scope.value;render();};
    root.querySelectorAll('[data-step]').forEach(b=>b.onclick=()=>navigate('wiring',Number(b.dataset.step)));
    root.querySelectorAll('[data-wire]').forEach(b=>b.onclick=()=>navigate('wiring',state.step,Number(b.dataset.wire)));
    root.querySelectorAll('[data-tube]').forEach(b=>b.onclick=()=>navigate('tubing',Number(b.dataset.tube)));
    bindChecks(root);
    const search=root.querySelector('#ag-search');if(search)search.oninput=()=>{state.search=search.value;const results=root.querySelector('#ag-bom-results');results.innerHTML=bomRows();bindChecks(results);};
    root.querySelectorAll('[data-action]').forEach(b=>b.onclick=()=>{
      switch(b.dataset.action){
        case 'fullscreen':toggleScreen();break;
        case 'zoom-in':state.zoom=Math.min(3,state.zoom+.25);board?.zoom(state.zoom);break;
        case 'zoom-out':state.zoom=Math.max(1,state.zoom-.25);board?.zoom(state.zoom);break;
        case 'zoom-fit':state.zoom=1;board?.fit();break;
        case 'next-wire':moveWire(1);break;
        case 'prev-wire':moveWire(-1);break;
        case 'next-tube':if(state.tube<D.tubes.length-1)navigate('tubing',state.tube+1);break;
        case 'prev-tube':if(state.tube>0)navigate('tubing',state.tube-1);break;
        case 'export':exportCSV();break;
        case 'print':window.print();break;
      }
    });
  }
  window.addEventListener('hashchange',()=>{readHash();render();});
  readHash();render();
})();
