import json
from dataclasses import dataclass
from functools import lru_cache
from itertools import combinations, permutations
from time import perf_counter


@lru_cache(maxsize=None)
def tuples_for(length, total):
    return tuple(p for combo in combinations(range(1,10),length)
                 if sum(combo)==total for p in permutations(combo))


@dataclass(frozen=True)
class Run:
    cells: tuple
    total: int


class Puzzle:
    def __init__(self, data):
        self.name, self.grid = data['name'], data['grid']
        if not self.grid or not self.grid[0] or any(len(row)!=len(self.grid[0]) for row in self.grid):
            raise ValueError('Grid must be a nonempty rectangle')
        self.cells = tuple((r,c) for r,row in enumerate(self.grid) for c,x in enumerate(row) if x is None)
        self.runs = []
        for r,row in enumerate(self.grid):
            for c,clue in enumerate(row):
                if clue is None:
                    continue
                if not isinstance(clue,dict) or set(clue)-{'down','right'}:
                    raise ValueError('Invalid clue')
                for direction,(dr,dc) in [('down',(1,0)),('right',(0,1))]:
                    if direction not in clue:
                        continue
                    cells=[]
                    rr,cc=r+dr,c+dc
                    while (rr,cc) in self.cells:
                        cells.append((rr,cc)); rr+=dr; cc+=dc
                    if not 2 <= len(cells) <= 9 or not isinstance(clue[direction],int) or not tuples_for(len(cells),clue[direction]):
                        raise ValueError('Invalid run length or sum')
                    self.runs.append(Run(tuple(cells),clue[direction]))
        self.members = {cell:[run for run in self.runs if cell in run.cells] for cell in self.cells}
        if not self.cells or any(len(runs)!=2 for runs in self.members.values()):
            raise ValueError('Each white cell needs one horizontal and one vertical run')
        self.neighbors = {cell:set().union(*(set(run.cells) for run in runs))-{cell}
                          for cell,runs in self.members.items()}

    @classmethod
    def load(cls,path):
        with open(path,encoding='utf-8') as f:
            return cls(json.load(f))

    def valid(self, values):
        return (set(values)==set(self.cells) and all(v in range(1,10) for v in values.values())
                and all(sum(values[c] for c in run.cells)==run.total and
                        len({values[c] for c in run.cells})==len(run.cells) for run in self.runs))


class KakuroSolver:
    def __init__(self,puzzle,heuristics=True):
        self.puzzle=puzzle
        self.heuristics=heuristics
        self.stats=dict(nodes=0,backtracks=0,pruned=0,seconds=0.0)
        self.solution=None

    def event(self,kind,domains,cell=None,depth=0):
        return dict(kind=kind,domains={c:set(d) for c,d in domains.items()},cell=cell,depth=depth)

    def supports(self,run,domains):
        return [t for t in tuples_for(len(run.cells),run.total)
                if all(v in domains[c] for c,v in zip(run.cells,t))]

    def propagate(self,domains,depth):
        changed=True
        while changed:
            changed=False
            for run in self.puzzle.runs:
                supported=self.supports(run,domains)
                if not supported:
                    yield self.event('contradiction',domains,run.cells[0],depth)
                    return False
                for i,cell in enumerate(run.cells):
                    reduced=domains[cell] & {t[i] for t in supported}
                    if reduced != domains[cell]:
                        self.stats['pruned']+=len(domains[cell])-len(reduced)
                        domains[cell]=reduced
                        changed=True
                        yield self.event('propagate',domains,cell,depth)
        return True

    def search(self,domains,depth):
        self.stats['nodes']+=1
        if not (yield from self.propagate(domains,depth)):
            return None
        pending=[c for c in domains if len(domains[c])>1]
        if not pending:
            values={c:next(iter(d)) for c,d in domains.items()}
            if not self.puzzle.valid(values):
                return None
            yield self.event('solution',domains,depth=depth)
            return values
        cell=(min(pending,key=lambda c:(len(domains[c]),-sum(len(domains[n])>1 for n in self.puzzle.neighbors[c]),c))
              if self.heuristics else pending[0])
        def flexibility(value):

            score=0
            trial={c:set(d) for c,d in domains.items()}
            trial[cell]={value}
            for run in self.puzzle.members[cell]:
                support=self.supports(run,trial)
                score+=sum(len({t[i] for t in support}) for i,c in enumerate(run.cells) if c!=cell)
            return -score,value
        values=sorted(domains[cell],key=flexibility) if self.heuristics else sorted(domains[cell])
        for value in values:
            branch={c:set(d) for c,d in domains.items()}
            branch[cell]={value}
            yield self.event('assign',branch,cell,depth)
            result=yield from self.search(branch,depth+1)
            if result is not None:
                return result
            self.stats['backtracks']+=1
            yield self.event('backtrack',domains,cell,depth)
        return None

    def events(self):
        self.stats=dict(nodes=0,backtracks=0,pruned=0,seconds=0.0)
        self.solution=None
        start=perf_counter()
        domains={c:set(range(1,10)) for c in self.puzzle.cells}
        yield self.event('start',domains)
        self.solution=yield from self.search(domains,0)
        self.stats['seconds']=perf_counter()-start
        yield self.event('done' if self.solution else 'unsatisfiable',
                         {c:{v} for c,v in self.solution.items()} if self.solution else domains)

    def solve(self):
        for _ in self.events():
            pass
        return self.solution
