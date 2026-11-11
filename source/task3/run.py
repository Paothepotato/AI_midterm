import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description='Task 3: Kakuro')
    sub = parser.add_subparsers(dest='command', required=True)
    ui = sub.add_parser('ui')
    ui.add_argument('--board', choices=['small', 'large', 'backtrack_demo'], default='small')
    ui.add_argument('--screenshot', type=Path)
    bench = sub.add_parser('benchmark')
    bench.add_argument('--trials', type=int, default=10)
    solve = sub.add_parser('kakuro')
    solve.add_argument('--board', choices=['small', 'large'], default='small')
    args = parser.parse_args()
    if args.command == 'ui':
        from ui import KakuroApp
        KakuroApp(args.board).run(args.screenshot)
    elif args.command == 'benchmark':
        from experiments import run
        run(args.trials)
    else:
        from kakuro import Puzzle, KakuroSolver
        solver = KakuroSolver(Puzzle.load(ROOT / 'data' / f'{args.board}.json'))
        print(solver.solve())
        print(solver.stats)


if __name__ == '__main__':
    main()
