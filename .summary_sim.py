import json
from statistics import mean
from pathlib import Path
p=Path('data/simulations/siumlaciones_completas.json')
try:
    data=json.loads(p.read_text(encoding='utf-8'))
except Exception as e:
    print('ERROR reading json:', e)
    raise
by_trial={}
for s in data.get('simulations',[]):
    t=s.get('trial')
    by_trial.setdefault(t,[]).append(s)
print(f"{'trial':>5} {'count':>6} {'avg_dur':>10} {'avg_reward':>11} {'agent_cost':>12} {'user_cost':>10} {'terminations':>20}")
for t in sorted(by_trial, key=lambda x:(x is None, x)):
    items=by_trial[t]
    durations=[x['duration'] for x in items if x.get('duration') is not None]
    rewards=[(x.get('reward_info') or {}).get('reward') for x in items]
    rewards=[r for r in rewards if r is not None]
    agent=sum(float(x.get('agent_cost') or 0) for x in items)
    user=sum(float(x.get('user_cost') or 0) for x in items)
    term_counts={}
    for x in items:
        tr=x.get('termination_reason') or 'unknown'
        term_counts[tr]=term_counts.get(tr,0)+1
    term_str=','.join(f"{k}:{v}" for k,v in term_counts.items())
    avg_dur = f"{mean(durations):.2f}" if durations else "null"
    avg_reward = f"{mean(rewards):.3f}" if rewards else "null"
    print(f"{str(t):>5} {len(items):6} {avg_dur:10} {avg_reward:11} {agent:12.2f} {user:10.2f} {term_str:>20}")
