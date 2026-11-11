import csv
import platform
import sys
from pathlib import Path
from statistics import mean
from nqueens import QueensCNF, MinConflicts

ROOT=Path(__file__).resolve().parent


def write_csv(name,rows):
    path=ROOT/'results'/name
    path.parent.mkdir(exist_ok=True)
    with path.open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)


def run(ns=(4,8,16,32),trials=10,max_steps=3000):
    if trials < 1:
        raise ValueError('trials must be positive')
    raw=[]; sat=[]
    for n in ns:
        for seed in range(trials):
            result=QueensCNF(n).solve(); result.pop('rows')
            sat.append(dict(n=n,trial=seed,**result))
            for strategy in ('random','max_conflict'):
                result=MinConflicts(n,strategy,max_steps).solve(seed); result.pop('rows')
                raw.append(dict(n=n,seed=seed,strategy=strategy,max_steps=max_steps,**result))
    write_csv('nqueens_sat.csv',sat)
    write_csv('nqueens_minconflicts.csv',raw)
    summary=[]
    for n in ns:
        for strategy in ('random','max_conflict'):
            group=[r for r in raw if r['n']==n and r['strategy']==strategy]
            successful=[r for r in group if r['solved']]
            summary.append(dict(n=n,strategy=strategy,trials=trials,
                success_rate=len(successful)/trials,
                mean_steps_all=mean(r['steps'] for r in group),
                mean_seconds_all=mean(r['seconds'] for r in group),
                mean_steps_success=mean(r['steps'] for r in successful) if successful else 'NA'))
    write_csv('nqueens_summary.csv',summary)
    (ROOT/'results'/'environment.txt').write_text(
        f'{platform.platform()}\nPython {sys.version}\nProcessor: {platform.processor()}\n'
        'Timing: perf_counter; sequential runs; Kakuro cache warm after first trial.\n',encoding='utf-8')
    for row in summary:
        print(row)
