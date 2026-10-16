// Local verification server. Loopback only; never exposes research files by URL.
import { createServer } from 'node:http';
import { readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { resolve } from 'node:path';
import { serve } from './lib/serve.mjs';
const root=fileURLToPath(new URL('.',import.meta.url));
const feed=resolve(process.argv[2]);
const assets={'/':'index.html','/live.mjs':'live.mjs','/live.css':'live.css','/lib/protocol.mjs':'lib/protocol.mjs'};
const csp="default-src 'none'; script-src 'self'; style-src 'self' 'unsafe-inline'; connect-src 'self'; frame-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'";
createServer(async(req,res)=>{
 res.setHeader('Cache-Control','private, no-store');res.setHeader('Content-Security-Policy',csp);
 const url=new URL(req.url,'http://127.0.0.1');
 if(url.pathname==='/api/live'){
  const result=await serve(req.method,url,async key=>readFile(resolve(feed,key),'utf8'));
  for(const [key,value] of Object.entries(result.headers)) res.setHeader(key,value);
  res.writeHead(result.status);return res.end(result.body);
 }
 if(req.method!=='GET'||!assets[url.pathname]){res.writeHead(404);return res.end();}
 try{
  const file=assets[url.pathname];const body=await readFile(resolve(root,file));
  res.setHeader('Content-Type',file.endsWith('.mjs')?'text/javascript':file.endsWith('.css')?'text/css':'text/html');res.end(body);
 }catch{res.writeHead(500);res.end('Asset unavailable');}
}).listen(8765,'127.0.0.1',()=>console.log('Cockpit verification at http://127.0.0.1:8765'));
