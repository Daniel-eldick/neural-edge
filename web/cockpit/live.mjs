import { validate, freshness } from './lib/protocol.mjs';
const byId=id=>document.getElementById(id);
const frame=byId('report');
let last=null,shown=null,networkError=false,busy=false,timer=null,observer=null;
const time=value=>new Date(value*1000).toLocaleString(undefined,{year:'numeric',month:'short',day:'numeric',hour:'2-digit',minute:'2-digit',second:'2-digit',timeZoneName:'short'});
function status() {
  if(!last) return;
  let fresh;
  try{fresh=freshness(last);}catch{fresh={state:'invalid',age:0};}
  const invalidClock=fresh.state==='invalid';
  const offline=networkError||!navigator.onLine||invalidClock;
  byId('connection').dataset.state=offline?'offline':fresh.state;
  byId('connection').textContent=offline?'Updates unavailable':fresh.state==='stale'?'Publisher offline or delayed':'Updates connected';
  const labels={idle:'Agent idle',running:'Backtest running',paused:'Replay paused',unavailable:'Source needs attention'};
  byId('agent').textContent=fresh.state==='stale'||offline?'Agent status unknown':labels[last.agent_state];
  byId('updated').textContent=`Last source update ${time(last.updated_at)}${invalidClock?'':` · ${Math.floor(fresh.age)}s ago`}`;
  byId('result-time').textContent=last.report_updated_at===null?'No published result yet':`Results published ${time(last.report_updated_at)}`;
  byId('notice').textContent=invalidClock?'Source time could not be verified. Check the device clock; last saved result remains below.':offline?'Connection lost. Last saved result remains below; retrying automatically.':fresh.state==='stale'?
    'The source may be stopped or asleep. These results are not current.':last.source_errors.length?
    'A source could not be verified. The last good result is retained.':
    'Automatic updates are connected. This does not mean an agent is trading.';
  const items=last.activity.map(item=>{const li=document.createElement('li');
    li.textContent=`${item.run} · ${item.state}${item.steps!==undefined?` · ${item.steps} candle batches committed`:''}`;return li;});
  byId('activity').replaceChildren(...items);
}
function resize(){if(frame.contentDocument) frame.style.height=`${Math.ceil(frame.contentDocument.body.getBoundingClientRect().height)}px`;}
function replaceReport(html,revision){
  const previous=frame.contentDocument;
  const open=previous?[...previous.querySelectorAll('details[open]')].map(x=>x.id||x.querySelector('summary')?.textContent):[];
  const radio=previous?.querySelector('input[type=radio]:checked')?.id;
  frame.onload=()=>{
    const doc=frame.contentDocument;
    const style=doc.createElement('style');
    style.textContent='.rail,.topbar,footer{display:none}.workspace{margin-left:0}';
    doc.head.append(style);
    for(const item of doc.querySelectorAll('details')) if(open.includes(item.id||item.querySelector('summary')?.textContent)) item.open=true;
    if(radio && doc.getElementById(radio)) doc.getElementById(radio).checked=true;
    doc.addEventListener('toggle',resize,true);
    observer?.disconnect();observer=new ResizeObserver(resize);observer.observe(doc.body);resize();
  };
  frame.srcdoc=html;frame.hidden=false;byId('empty').hidden=true;shown=revision;
}
async function poll(){
  if(busy||document.hidden) return;
  busy=true;byId('refresh').disabled=true;
  const controller=new AbortController();const timeout=setTimeout(()=>controller.abort(),15000);
  try{
    const response=await fetch('/api/live',{cache:'no-store',signal:controller.signal});
    if(!response.ok||!response.headers.get('content-type')?.includes('application/json')) throw Error('Feed unavailable');
    const data=validate(await response.json());freshness(data);
    if(last && data.updated_at<last.updated_at) throw Error('Older publication');
    last=data;networkError=false;status();
    if(last.report_revision && shown!==last.report_revision){
      const page=await fetch(`/api/live?part=report&revision=${last.report_revision}`,{cache:'no-store',signal:controller.signal});
      if(!page.ok||!page.headers.get('content-type')?.includes('text/html')) throw Error('Report unavailable');
      replaceReport(await page.text(),last.report_revision);
    }
  }catch{
    networkError=true;
    if(last) status(); else {
      byId('connection').textContent='Updates unavailable';byId('agent').textContent='Waiting for the publisher';
      byId('notice').textContent='No live source is connected yet, or your session needs sign-in. Refresh to retry.';
    }
  }finally{clearTimeout(timeout);busy=false;byId('refresh').disabled=false;clearTimeout(timer);timer=setTimeout(poll,30000);}
}
byId('refresh').addEventListener('click',poll);
document.addEventListener('visibilitychange',()=>{if(!document.hidden) poll();else clearTimeout(timer);});
window.addEventListener('online',poll);window.addEventListener('offline',()=>{networkError=true;status();});
window.addEventListener('resize',resize);setInterval(()=>{if(last) status();},1000);poll();
