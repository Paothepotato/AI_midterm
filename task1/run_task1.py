import sys
import os


if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.board import Board
from core.constants import ACTIONS, STEP_COST


def demonstrate_state_space(map_path: str):
    print("=" * 70)
    print(f"MINH HỌA MÔ HÌNH HÓA KHÔNG GIAN TRẠNG THÁI: {map_path}")
    print("=" * 70)

    board = Board.from_file(map_path)
    print(f"\n[1] Thông tin bản đồ tĩnh (Board):")
    print(f" - Kích thước lưới : {board.width} x {board.height}")
    print(f" - Số ô tường      : {len(board.walls)} ô")
    print(f" - Số ô sàn đi được: {len(board.floors)} ô")
    print(f" - Số ô đích       : {len(board.goals)} ô -> {sorted(list(board.goals))}")

    print(f"\n[2] Các thành phần của bài toán tìm kiếm (State-Space Formulation):")
    print(f" - Trạng thái ban đầu (s0):")
    print(f"     Vị trí người chơi : {board.initial.player}")
    print(f"     Vị trí các hộp    : {board.initial.boxes}")
    print(f" - Tập hành động A(s)  : {list(ACTIONS.keys())}")
    print(f" - Chi phí bước đi c   : {STEP_COST}")
    print(f" - Điều kiện đích      : frozenset(state.boxes) == board.goals")
    print(f" - s0 đã là đích chưa? : {board.is_goal(board.initial)}")

    print(f"\n[3] Bản đồ trực quan ban đầu:")
    print(board.render(board.initial))

    succs = board.successors(board.initial)
    print(f"\n[4] Các trạng thái kế tiếp hợp lệ từ s0 ({len(succs)} nước đi):")
    for act, next_st in succs:
        print(f" - Hành động '{act:5s}' -> Người chơi: {next_st.player}, Hộp: {next_st.boxes}")

    return board


def test_transitions_on_simple_map():
    print("\n" + "=" * 70)
    print("KIỂM CHỨNG QUY TẮC CHUYỂN TRẠNG THÁI TRÊN BẢN ĐỒ ĐƠN GIẢN")
    print("=" * 70)
    board = Board.from_file("maps/example_simple.txt")
    s0 = board.initial
    print(f"Trạng thái ban đầu: {s0}")

    s1 = board.move(s0, "North")
    print(f"\nBước đi North -> {s1}")
    assert s1 is not None and s1.player == (2, 1), "Bước đi North phải hợp lệ."

    s_wall = board.move(s1, "North")
    print(f"Bước đi North đâm vào tường -> {s_wall}")
    assert s_wall is None, "Đi vào tường bắt buộc phải trả về None."

    actions = ['North', 'East', 'East', 'South']
    print(f"\nPhát lại chuỗi hành động lời giải: {actions}")
    history = board.replay(actions)
    for step_idx, state in enumerate(history):
        print(f" Bước {step_idx}: Người={state.player}, Hộp={state.boxes}, Đạt đích={board.is_goal(state)}")

    assert board.is_goal(history[-1]), "Trạng thái cuối cùng bắt buộc phải đạt mục tiêu (Goal State)!"
    print("-> Luật chuyển trạng thái và tính năng replay kiểm chứng THÀNH CÔNG!\n")


if __name__ == "__main__":
    board_simple = demonstrate_state_space("maps/example_simple.txt")
    test_transitions_on_simple_map()

    board_official = demonstrate_state_space("maps/example_map.txt")
    print("Tất cả các thành phần của Task 1 đã vượt qua kiểm thử thành công!")
