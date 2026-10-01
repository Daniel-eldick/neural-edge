// Internal one-shot transport, called under the Python observer's advisory lock.
// Only sanitized snapshots are read; this never loads Jev credentials or journals.
import { readFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { publish } from './lib/storage.mjs';
import { validate, freshness } from './lib/protocol.mjs';
async function main(){
 if(!process.argv[2]) throw Error('Provide observer output directory');
 const directory=resolve(process.argv[2]);
 const confirmed=process.argv[3]||null;
 if(confirmed&&!/^[a-f0-9]{64}$/.test(confirmed)) throw Error('Invalid confirmed revision');
 const data=validate(JSON.parse(await readFile(resolve(directory,'status.json'),'utf8')));
 if(freshness(data).state==='stale') throw Error('Local observer is stale');
 const report=data.report_revision&&data.report_revision!==confirmed?
   await readFile(resolve(directory,'report.html'),'utf8'):null;
 await publish(data,report);
 console.log(JSON.stringify({published_at:data.updated_at,agent_state:data.agent_state,completed_runs:data.completed_runs}));
}
main().catch(()=>{console.error('Cockpit upload failed: verify local observer and private storage access. Last successful timestamp retained.');process.exitCode=1;});
