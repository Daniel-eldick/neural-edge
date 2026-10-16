const states = new Set(['idle', 'paused', 'running', 'unavailable']);
const finite = x => typeof x === 'number' && Number.isFinite(x) && x >= 0;
export function validate(value) {
  if (!value || typeof value !== 'object' || value.version !== 1 || value.mode !== 'paper_research' ||
      !finite(value.updated_at) || !states.has(value.agent_state) ||
      !Number.isInteger(value.completed_runs) || value.completed_runs < 0 || value.completed_runs > 1000 ||
      !Array.isArray(value.source_errors) || value.source_errors.length > 10 ||
      !value.source_errors.every(x => typeof x === 'string' && x.length <= 300) ||
      !Array.isArray(value.activity) || value.activity.length > 10) throw Error('Invalid feed');
  if (value.report_revision === null) {
    if (value.report_updated_at !== null) throw Error('Invalid report timestamp');
  } else if (typeof value.report_revision !== 'string' || !/^[a-f0-9]{64}$/.test(value.report_revision) ||
      !finite(value.report_updated_at) || value.report_updated_at > value.updated_at) throw Error('Invalid report');
  const activity = value.activity.map(item => {
    if (!item || typeof item.run !== 'string' || item.run.length > 200 ||
        !['starting','running','paused'].includes(item.state)) throw Error('Invalid activity');
    if (item.state === 'starting') return {run:item.run,state:item.state};
    if (!Number.isInteger(item.steps) || item.steps < 0 || !finite(item.equity) ||
        !(item.market_time === null || finite(item.market_time)) ||
        !Number.isInteger(item.policy_errors) || item.policy_errors < 0 ||
        !Number.isInteger(item.open_positions) || item.open_positions < 0) throw Error('Invalid progress');
    return {run:item.run,state:item.state,steps:item.steps,equity:item.equity,
      market_time:item.market_time,policy_errors:item.policy_errors,open_positions:item.open_positions};
  });
  return {version:1,mode:'paper_research',updated_at:value.updated_at,agent_state:value.agent_state,
    report_revision:value.report_revision,report_updated_at:value.report_updated_at,
    completed_runs:value.completed_runs,source_errors:value.source_errors,activity};
}
export function freshness(value, now = Date.now()/1000) {
  if (!finite(now) || value.updated_at > now+30) throw Error('Feed timestamp is in the future');
  const age = Math.max(0, now-value.updated_at);
  return {state:age>180?'stale':'connected',age};
}
