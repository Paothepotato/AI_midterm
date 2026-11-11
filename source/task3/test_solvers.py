import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent/'.vendor'))
from kakuro import Puzzle,KakuroSolver


class SolversTest(unittest.TestCase):
    def test_assignment_boards(self):
        for name in ('small','large'):
            puzzle=Puzzle.load(ROOT/'data'/f'{name}.json')
            for h in (False,True):
                solver=KakuroSolver(puzzle,h)
                self.assertTrue(puzzle.valid(solver.solve()))

    def test_unsatisfiable_and_backtrack_trace(self):
        data={'name':'contradictory','grid':[
            [{},{'down':3},{'down':4}],
            [{'right':3},None,None],
            [{'right':3},None,None]]}
        solver=KakuroSolver(Puzzle(data))
        events=list(solver.events())
        self.assertIsNone(solver.solution)
        self.assertEqual(events[-1]['kind'],'unsatisfiable')
        self.assertTrue(any(e['kind']=='contradiction' for e in events))

    def test_snapshot_isolation_and_invalid_input(self):
        puzzle=Puzzle.load(ROOT/'data'/'small.json')
        solver=KakuroSolver(puzzle)
        events=list(solver.events())
        self.assertTrue(all(len(d)==9 for d in events[0]['domains'].values()))
        with self.assertRaises(ValueError): Puzzle({'name':'bad','grid':[[None]]})

    def test_backtracking_restores_domains(self):
        solver=KakuroSolver(Puzzle.load(ROOT/'data'/'backtrack_demo.json'))
        events=list(solver.events())
        self.assertIsNone(solver.solution)
        self.assertGreater(solver.stats['backtracks'],0)
        self.assertTrue(any(e['kind']=='backtrack' and len(e['domains'][e['cell']])>1 for e in events))

if __name__=='__main__': unittest.main()
