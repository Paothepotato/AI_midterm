import csv
import platform
import sys
from pathlib import Path
from statistics import mean
from kakuro import Puzzle, KakuroSolver

ROOT=Path(__file__).resolve().parent


def write_csv(name,rows):
    path=ROOT/'results'/name
    path.parent.mkdir(exist_ok=True)
    with path.open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)


def run(trials=10):
    if trials < 1:
        raise ValueError('trials must be positive')
    (ROOT/'results').mkdir(exist_ok=True)
    kakuro=[]
    for name in ('small','large'):
        puzzle=Puzzle.load(ROOT/'data'/f'{name}.json')
        for heuristics in (False,True):
            for trial in range(trials):
                solver=KakuroSolver(puzzle,heuristics)
                values=solver.solve()
                assert values is not None and puzzle.valid(values)
                kakuro.append(dict(board=name,heuristics=heuristics,trial=trial,valid=True,**solver.stats))
                if heuristics and trial==0:
                    import json
                    (ROOT/'results'/f'{name}_solution.json').write_text(json.dumps(
                        {f'{r},{c}':v for (r,c),v in values.items()},indent=2),encoding='utf-8')
    write_csv('kakuro.csv',kakuro)
    (ROOT/'results'/'environment.txt').write_text(
        f'{platform.platform()}\nPython {sys.version}\nProcessor: {platform.processor()}\n'
        'Timing: perf_counter; sequential runs; Kakuro cache warm after first trial.\n',encoding='utf-8')
