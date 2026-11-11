import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent/'.vendor'))
from nqueens import QueensCNF,MinConflicts,valid


class SolversTest(unittest.TestCase):
    def test_sat_and_clause_count(self):
        for n in (1,2,3,4,8):
            solver=QueensCNF(n)
            expected=2*n + n*n*(n-1) + n*(n-1)*(2*n-1)//3
            self.assertEqual(len(solver.clauses()),expected)
            result=solver.solve()
            self.assertEqual(result['solved'],n not in (2,3))
            if result['solved']: self.assertTrue(valid(result['rows']))

    def test_minconflicts(self):
        for strategy in ('random','max_conflict'):
            result=MinConflicts(8,strategy).solve(0)
            self.assertTrue(result['solved']); self.assertTrue(valid(result['rows']))
            self.assertFalse(MinConflicts(3,strategy,50).solve(0)['solved'])

if __name__=='__main__': unittest.main()
