import { test } from 'node:test';
import assert from 'node:assert/strict';
import { validate, freshness } from '../lib/protocol.mjs';
import { serve } from '../lib/serve.mjs';
import { createHash } from 'node:crypto';
const sample = {version:1,updated_at:1000,report_updated_at:990,report_revision:'a'.repeat(64),agent_state:'idle',completed_runs:38,source_errors:[],activity:[],mode:'paper_research'};
test('freshness tracks source timestamp, never response arrival',()=>{
 assert.equal(freshness(validate(sample),1010).state,'connected');
 assert.equal(freshness(sample,1181).state,'stale');
 assert.throws(()=>freshness({...sample,updated_at:2000},1000),/future/);
 assert.throws(()=>validate({...sample,report_revision:'javascript:bad'}));
 assert.throws(()=>validate({...sample,updated_at:NaN}));
 assert.throws(()=>validate({...sample,agent_state:'live_trading'}));
});
test('read endpoint bounds inputs, retains privacy, refuses mismatched report', async()=>{
 const html='<!doctype html><title>Actual report</title>';
 const revision=createHash('sha256').update(html).digest('hex');
 const read=async key=>key==='status.json'?JSON.stringify(sample):html;
 assert.equal((await serve('POST','http://localhost/api/live',read)).status,405);
 assert.equal((await serve('GET','http://localhost/api/live?part=../../secret',read)).status,400);
 const status=await serve('GET','http://localhost/api/live',read);
 assert.equal(status.status,200); assert.equal(status.headers['Cache-Control'],'private, no-store');
 assert.equal((await serve('GET','http://localhost/api/live?part=report&revision='+'a'.repeat(64),read)).status,409);
 assert.equal((await serve('GET','http://localhost/api/live?part=report&revision='+revision,read)).body,html);
});
test('storage absence/failure/oversize never returns a false connected state', async()=>{
 assert.equal((await serve('GET','http://localhost/api/live',async()=>null)).status,503);
 const fail=await serve('GET','http://localhost/api/live',async()=>{throw Error('SECRET TOKEN');});
 assert.equal(fail.status,503); assert.ok(!fail.body.includes('SECRET'));
 assert.equal((await serve('GET','http://localhost/api/live',async()=> 'x'.repeat(20001))).status,503);
});
