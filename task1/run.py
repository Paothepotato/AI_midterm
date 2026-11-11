import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / '.vendor'))


def main():
    parser = argparse.ArgumentParser(description='Task 1: N-Queens')
    sub = parser.add_subparsers(dest='command', required=True)
    bench = sub.add_parser('benchmark')
    bench.add_argument('--trials', type=int, default=10)
    bench.add_argument('--ns', type=int, nargs='+', default=[4, 8, 16, 32])
    bench.add_argument('--max-steps', type=int, default=3000)
    queens = sub.add_parser('queens')
    queens.add_argument('n', type=int)
    queens.add_argument('--method', choices=['sat', 'random', 'max_conflict'], default='sat')
    queens.add_argument('--seed', type=int, default=0)
    args = parser.parse_args()
    if args.command == 'benchmark':
        from experiments import run
        run(args.ns, args.trials, args.max_steps)
    else:
        from nqueens import QueensCNF, MinConflicts
        result = (QueensCNF(args.n).solve() if args.method == 'sat'
                  else MinConflicts(args.n, args.method).solve(args.seed))
        print(result)


if __name__ == '__main__':
    main()
