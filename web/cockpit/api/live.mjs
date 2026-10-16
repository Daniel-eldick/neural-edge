import { serve } from '../lib/serve.mjs';
import { readStored } from '../lib/storage.mjs';
export default async function handler(req, res) {
  const response=await serve(req.method,new URL(req.url,'https://cockpit.invalid'),readStored);
  for(const [key,value] of Object.entries(response.headers)) res.setHeader(key,value);
  res.statusCode=response.status; res.end(response.body);
}
