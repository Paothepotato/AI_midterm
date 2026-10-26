import os
import sys

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.board import Board
from task2.solver import SearchSolver


def test_map_solving(map_path: str, timeout: float = 30.0):
    print('=' * 75)
    print(f'KIEM THU THUAT TOAN TREN BAN DO: {map_path}')
    print('=' * 75)
    board = Board.from_file(map_path)
    print(f'Kich thuoc: {board.width}x{board.height}, So hop: {len(board.initial.boxes)}, So dich: {len(board.goals)}')

    print('\n--- [1] Dang chay UCS (Uniform Cost Search) ---')
    solver_ucs = SearchSolver(board, algorithm='ucs', prune_deadlocks=True)
    res_ucs = solver_ucs.solve(timeout=timeout)
    print(f'Trang thai         : {res_ucs.status}')
    print(f'Chi phi toi uu (g*): {res_ucs.cost}')
    print(f'So node mo rong    : {res_ucs.expanded} nodes')
    print(f'So node sinh ra    : {res_ucs.generated} nodes')
    print(f'Dinh hang doi      : {res_ucs.peak_frontier} nodes')
    print(f'Thoi gian chay     : {res_ucs.elapsed_seconds:.4f} giay')

    print('\n--- [2] Dang chay A* (BFS Grid + Hungarian Heuristic) ---')
    solver_astar = SearchSolver(board, algorithm='astar', prune_deadlocks=True)
    res_astar = solver_astar.solve(timeout=timeout)
    print(f'Trang thai         : {res_astar.status}')
    print(f'Chi phi toi uu (g*): {res_astar.cost}')
    print(f'So node mo rong    : {res_astar.expanded} nodes')
    print(f'So node sinh ra    : {res_astar.generated} nodes')
    print(f'Dinh hang doi      : {res_astar.peak_frontier} nodes')
    print(f'Thoi gian chay     : {res_astar.elapsed_seconds:.4f} giay')
    print(f'Muc trong Cache h  : {res_astar.heuristic_cache_entries} entries')

    if res_astar.status == 'solved':
        print(f'\nChuoi hanh dong cua A* ({len(res_astar.actions)} buoc):')
        print(' -> '.join(res_astar.actions))

        final_state = board.replay(res_astar.actions)[-1]
        assert board.is_goal(final_state), 'Trang thai cuoi cung sau khi phat lai loi giai A* phai dat muc tieu!'
        print('Kiem chung Replay: Thanh cong dua toan bo hop vao Goal State!')

    if res_ucs.status == 'solved' and res_astar.status == 'solved':
        assert res_ucs.cost == res_astar.cost, f'Loi tinh toi uu: Chi phi UCS ({res_ucs.cost}) != Chi phi A* ({res_astar.cost})'
        print(f'Kiem chung Tinh Toi uu: DAT CHUAN (Ca hai deu tim ra chi phi toi uu = {res_astar.cost})')
        reduction = (1 - res_astar.expanded / res_ucs.expanded) * 100 if res_ucs.expanded > 0 else 0
        print(f'Muc do cat giam khong gian tim kiem: A* mo rong it hon UCS {reduction:.1f}% so node!')


if __name__ == '__main__':
    test_map_solving('maps/example_map.txt')
    test_map_solving('maps/map_small_easy.txt')
