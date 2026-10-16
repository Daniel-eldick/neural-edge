import { createHash } from 'node:crypto';
import { validate } from './protocol.mjs';
export const headers = {'Cache-Control':'private, no-store','X-Robots-Tag':'noindex, nofollow, noarchive',
  'X-Content-Type-Options':'nosniff','Referrer-Policy':'no-referrer'};
export async function serve(method, url, read) {
  const reply = (status, body, type='application/json') => ({status,body,headers:{...headers,'Content-Type':type}});
  if (method !== 'GET') return reply(405,JSON.stringify({error:'Read-only endpoint'}));
  const query = new URL(url).searchParams;
  const part = query.get('part') || 'status';
  const revision = query.get('revision');
  if (!['status','report'].includes(part) || (part==='report' && !/^[a-f0-9]{64}$/.test(revision || '')))
    return reply(400,JSON.stringify({error:'Invalid request'}));
  try {
    const body = await read(part==='report'?'report.html':'status.json',part==='report'?4194304:20000);
    if (typeof body !== 'string' || Buffer.byteLength(body)>(part==='report'?4194304:20000))
      throw Error('Missing or oversized feed');
    if (part==='status') return reply(200,JSON.stringify(validate(JSON.parse(body))));
    if (createHash('sha256').update(body).digest('hex')!==revision)
      return reply(409,JSON.stringify({error:'Publication changed; refresh status'}));
    return reply(200,body,'text/html; charset=utf-8');
  } catch {
    return reply(503,JSON.stringify({error:'Updates unavailable; last saved results retained'}));
  }
}
