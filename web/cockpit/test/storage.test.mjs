import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readStored,publish} from '../lib/storage.mjs';
import {createHash} from 'node:crypto';
const env={KV_REST_API_URL:'https://example.upstash.io',KV_REST_API_TOKEN:'WRITE_SECRET',KV_REST_API_READ_ONLY_TOKEN:'READ_SECRET'};
const page='<!doctype html><title>Actual saved result</title>';
const state={version:1,mode:'paper_research',updated_at:1000,report_updated_at:1000,report_revision:createHash('sha256').update(page).digest('hex'),agent_state:'idle',activity:[],source_errors:[],completed_runs:1};
test('private fixed-key reader uses read-only token and no redirects',async()=>{
 let request;
 const result=await readStored('status.json',env,async(url,options)=>{
  request={url,options};return new Response(JSON.stringify({result:'saved'}));
 });
 assert.equal(result,'saved');assert.equal(request.options.headers.Authorization,'Bearer READ_SECRET');
 assert.equal(request.options.redirect,'error');assert.deepEqual(JSON.parse(request.options.body),['GET','neuraledge:cockpit:status']);
 await assert.rejects(()=>readStored('../../other',env),/key/);
 await assert.rejects(()=>readStored('status.json',{...env,KV_REST_API_URL:'http://attacker.test'}),/endpoint/);
});
test('report and metadata are published atomically; later heartbeat omits unchanged report',async()=>{
 const commands=[];const fetcher=async(url,options)=>{commands.push(JSON.parse(options.body));return new Response('{"result":"OK"}');};
 await publish(state,page,env,fetcher);
 assert.deepEqual(commands[0].slice(0,4),['MSET','neuraledge:cockpit:report',page,'neuraledge:cockpit:status']);
 assert.deepEqual(JSON.parse(commands[0][4]),state);
 await publish({...state,updated_at:1060},null,env,fetcher);
 assert.equal(commands[1][0],'SET');assert.equal(commands[1].length,3);
 await assert.rejects(()=>publish(state,'changed',env,fetcher),/mismatch/);
 assert.equal(commands.length,2);
});
test('upstream failures are sanitized and never become fabricated data',async()=>{
 await assert.rejects(()=>readStored('status.json',env,async()=>new Response('SECRET',{status:500})),/Storage unavailable/);
 await assert.rejects(()=>readStored('status.json',{...env,KV_REST_API_READ_ONLY_TOKEN:''}),/credential/);
});
