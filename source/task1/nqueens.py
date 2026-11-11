from dataclasses import dataclass
from itertools import combinations
from random import Random
from time import perf_counter


def valid(rows):
    return all(rows[a] != rows[b] and abs(rows[a]-rows[b]) != b-a
               for a in range(len(rows)) for b in range(a+1, len(rows)))


class QueensCNF:
    def __init__(self, n):
        if n < 1:
            raise ValueError('N must be positive')
        self.n = n

    def var(self, r, c):
        return r*self.n+c+1

    def clauses(self):
        n = self.n
        clauses = []
        def at_most_one(group):
            clauses.extend([[-a, -b] for a, b in combinations(group, 2)])
        for r in range(n):
            group = [self.var(r,c) for c in range(n)]
            clauses.append(group)
            at_most_one(group)
        for c in range(n):
            group = [self.var(r,c) for r in range(n)]
            clauses.append(group)
            at_most_one(group)
        for direction in (-1, 1):
            for key in range(-(n-1), 2*n-1):
                at_most_one([self.var(r,c) for r in range(n) for c in range(n)
                             if r+direction*c == key])
        return clauses

    def solve(self):
        from pysat.solvers import Glucose3
        start = perf_counter()
        clauses = self.clauses()
        encoding_s = perf_counter()-start
        with Glucose3(bootstrap_with=clauses) as solver:
            start = perf_counter()
            sat = solver.solve()
            solve_s = perf_counter()-start
            model = solver.get_model() if sat else []
        rows = [-1]*self.n
        for literal in model:
            if literal > 0:
                r,c = divmod(literal-1,self.n)
                rows[c] = r
        if sat and (min(rows)<0 or not valid(rows)):
            raise AssertionError('Invalid SAT solution')
        return dict(solved=sat, rows=rows if sat else None,
                    clauses=len(clauses), encoding_s=encoding_s, seconds=solve_s)


@dataclass
class MinConflicts:
    n: int
    strategy: str = 'random'
    max_steps: int = 10000

    def solve(self, seed=0):
        if self.n < 1 or self.max_steps < 0 or self.strategy not in ('random','max_conflict'):
            raise ValueError('Invalid Min-Conflicts configuration')
        rng = Random(seed)
        rows = [rng.randrange(self.n) for _ in range(self.n)]
        start = perf_counter()
        def conflicts(c, r):
            return sum(c != j and (r == rows[j] or abs(r-rows[j]) == abs(c-j))
                       for j in range(self.n))
        for step in range(self.max_steps+1):
            scores = [conflicts(c,r) for c,r in enumerate(rows)]
            bad = [c for c,s in enumerate(scores) if s]
            if not bad:
                assert valid(rows)
                return dict(solved=True, rows=rows, steps=step, seconds=perf_counter()-start)
            if step == self.max_steps:
                break
            if self.strategy == 'max_conflict':
                peak = max(scores)
                bad = [c for c in bad if scores[c] == peak]
            c = rng.choice(bad)
            costs = [conflicts(c,r) for r in range(self.n)]
            best = min(costs)
            rows[c] = rng.choice([r for r,v in enumerate(costs) if v == best])
        return dict(solved=False, rows=None, steps=self.max_steps, seconds=perf_counter()-start)
