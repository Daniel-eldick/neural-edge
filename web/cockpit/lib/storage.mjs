import {createHash} from 'node:crypto';
import {validate} from './protocol.mjs';
const keys={'status.json':'neuraledge:cockpit:status','report.html':'neuraledge:cockpit:report'};
async function command(args,env,write,fetcher){
  const url=new URL(env.KV_REST_API_URL || 'https://missing.invalid');
  if(url.protocol!=='https:'||!url.hostname.endsWith('.upstash.io')||url.username||url.password||
      url.port||url.search||url.hash||url.pathname!=='/') throw Error('Invalid storage endpoint');
  const token=write?env.KV_REST_API_TOKEN:env.KV_REST_API_READ_ONLY_TOKEN;
  if(!token) throw Error('Storage credential missing');
  try{
    const result=await fetcher(url.origin,{method:'POST',redirect:'error',cache:'no-store',
      headers:{Authorization:`Bearer ${token}`,'Content-Type':'application/json'},
      body:JSON.stringify(args),signal:AbortSignal.timeout(10000)});
    if(!result.ok||!result.body) throw Error('Request failed');
    const reader=result.body.getReader();const chunks=[];let size=0;
    try{
      while(true){const {done,value}=await reader.read();if(done) break;
        size+=value.length;if(size>26*1024*1024) throw Error('Response too large');chunks.push(Buffer.from(value));}
    }finally{await reader.cancel();}
    const data=JSON.parse(Buffer.concat(chunks).toString('utf8'));
    if(!data||!Object.hasOwn(data,'result')||Object.hasOwn(data,'error')) throw Error('Bad response');
    return data.result;
  }catch{throw Error('Storage unavailable');}
}
export async function readStored(key,env=process.env,fetcher=fetch){
  if(!Object.hasOwn(keys,key)) throw Error('Invalid storage key');
  const result=await command(['GET',keys[key]],env,false,fetcher);
  if(result!==null&&typeof result!=='string') throw Error('Invalid stored value');
  return result;
}
export async function publish(state,report,env=process.env,fetcher=fetch){
  const valid=validate(state);let args=['SET',keys['status.json'],JSON.stringify(valid)];
  if(report!==null){
    if(typeof report!=='string'||Buffer.byteLength(report)>4194304||
        createHash('sha256').update(report).digest('hex')!==valid.report_revision) throw Error('Report mismatch');
    args=['MSET',keys['report.html'],report,keys['status.json'],JSON.stringify(valid)];
  }
  if(await command(args,env,true,fetcher)!=='OK') throw Error('Publication was not acknowledged');
}
