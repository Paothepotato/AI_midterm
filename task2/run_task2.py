import os
import sys


if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.board import Board
from task2.solver import SearchSolver


def test_map_solving(map_path: str, timeout: float = 30.0):
    print("=" * 75)
    print(f"KIỂM THỬ THUẬT TOÁN TRÊN BẢN ĐỒ: {map_path}")
    print("=" * 75)
    board = Board.from_file(map_path)
    print(f"Kích thước: {board.width}x{board.height}, Số hộp: {len(board.initial.boxes)}, Số đích: {len(board.goals)}")

    print("\n--- [1] Đang chạy UCS (Uniform Cost Search) ---")
    solver_ucs = SearchSolver(board, algorithm='ucs', prune_deadlocks=True)
    res_ucs = solver_ucs.solve(timeout=timeout)
    print(f"Trạng thái         : {res_ucs.status}")
    print(f"Chi phí tối ưu (g*): {res_ucs.cost}")
    print(f"Số node mở rộng    : {res_ucs.expanded} nodes")
    print(f"Số node sinh ra    : {res_ucs.generated} nodes")
    print(f"Đỉnh hàng đợi      : {res_ucs.peak_frontier} nodes")
    print(f"Thời gian chạy     : {res_ucs.elapsed_seconds:.4f} giây")

    print("\n--- [2] Đang chạy A* (BFS Grid + Hungarian Heuristic) ---")
    solver_astar = SearchSolver(board, algorithm='astar', prune_deadlocks=True)
    res_astar = solver_astar.solve(timeout=timeout)
    print(f"Trạng thái         : {res_astar.status}")
    print(f"Chi phí tối ưu (g*): {res_astar.cost}")
    print(f"Số node mở rộng    : {res_astar.expanded} nodes")
    print(f"Số node sinh ra    : {res_astar.generated} nodes")
    print(f"Đỉnh hàng đợi      : {res_astar.peak_frontier} nodes")
    print(f"Thời gian chạy     : {res_astar.elapsed_seconds:.4f} giây")
    print(f"Mục trong Cache h  : {res_astar.heuristic_cache_entries} entries")

    if res_astar.status == 'solved':
        print(f"\nChuỗi hành động của A* ({len(res_astar.actions)} bước):")
        print(" -> ".join(res_astar.actions))

        final_state = board.replay(res_astar.actions)[-1]
        assert board.is_goal(final_state), "Trạng thái cuối cùng sau khi phát lại lời giải A* phải đạt mục tiêu!"
        print("Kiểm chứng Replay: Thành công đưa toàn bộ hộp vào Goal State!")

    if res_ucs.status == 'solved' and res_astar.status == 'solved':
        assert res_ucs.cost == res_astar.cost, f"Lỗi tính tối ưu: Chi phí UCS ({res_ucs.cost}) != Chi phí A* ({res_astar.cost})"
        print(f"Kiểm chứng Tính Tối ưu: ĐẠT CHUẨN (Cả hai đều tìm ra chi phí tối ưu = {res_astar.cost})")
        reduction = (1 - res_astar.expanded / res_ucs.expanded) * 100 if res_ucs.expanded > 0 else 0
        print(f"Mức độ cắt giảm không gian tìm kiếm: A* mở rộng ít hơn UCS {reduction:.1f}% số node!")


if __name__ == "__main__":
    test_map_solving("maps/map_small_easy.txt")

    test_map_solving("maps/map_medium.txt")
