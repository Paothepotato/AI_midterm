import os
import sys


if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8') # type: ignore
        sys.stderr.reconfigure(encoding='utf-8') # type: ignore
    except Exception:
        pass

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.board import Board
from core.competition import Competition
from task7.runner import DecisionRunner


def run_competitive_match(map_path: str = "maps/map_competition.txt", turns_limit: int = 25):
    print("=" * 85)
    print("TASK 7: MÔ PHỎNG TRẬN ĐẤU ĐỐI KHÁNG SOKOBAN HAI NGƯỜI (COMPETITIVE SOKOBAN)")
    print("=" * 85)

    board = Board.from_file(map_path)
    competition = Competition(board, limit=turns_limit)
    state = competition.create_initial_state()
    runner = DecisionRunner()

    print(f"Kích thước bản đồ : {board.width}x{board.height}")
    print(f"Player 0 (Agent A - A*) : Bắt đầu tại {state.players[0]}")
    print(f"Player 1 (Agent Z - BFS): Bắt đầu tại {state.players[1]}")
    print(f"Tổng số hộp       : {len(state.boxes)} | Tổng số đích: {len(board.goals)}")
    print(f"Giới hạn số lượt n: {turns_limit} lượt")
    print("-" * 85)

    step_timings_0 = []
    step_timings_1 = []

    while not competition.is_game_over(state):
        curr_turn = state.turn

        actions, timings, errors = runner.decide(board, state, limit_seconds=1.0)
        step_timings_0.append(timings[0])
        step_timings_1.append(timings[1])

        next_state = competition.step(state, actions)

        s0, s1 = next_state.get_score()

        print(
            f"Lượt {curr_turn+1:2d} | "
            f"P0({actions[0]:5s}, {timings[0]*1000:4.1f}ms) vs "
            f"P1({actions[1]:5s}, {timings[1]*1000:4.1f}ms) | "
            f"Tỷ số: P0={s0} - P1={s1} | "
            f"Vị trí: P0={next_state.players[0]}, P1={next_state.players[1]}"
        )

        state = next_state

    print("-" * 85)
    score0, score1 = state.get_score()
    winner = competition.get_winner(state)

    print("\nKẾT QUẢ CHUNG CUỘC TRẬN ĐẤU:")
    print(f" - Tổng số lượt đã đấu : {state.turn}")
    print(f" - Điểm số cuối cùng   : Player 0 (A*) = {score0} | Player 1 (BFS) = {score1}")

    if winner == 0:
        print(" - NGƯỜI CHIẾN THẮNG   : PLAYER 0 (Agent A* Planning)! [VICTORY]")
    elif winner == 1:
        print(" - NGƯỜI CHIẾN THẮNG   : PLAYER 1 (Agent BFS Planning)! [VICTORY]")
    else:
        print(" - KẾT QUẢ CHUNG CUỘC  : HÒA NHAU! [TIED MATCH]")

    print(f"\nKIỂM CHỨNG RÀNG BUỘC THỜI GIAN (< 1,000ms):")
    max_t0 = max(step_timings_0) * 1000
    avg_t0 = (sum(step_timings_0) / len(step_timings_0)) * 1000
    max_t1 = max(step_timings_1) * 1000
    avg_t1 = (sum(step_timings_1) / len(step_timings_1)) * 1000

    print(f" - Player 0 (A*) : Lớn nhất = {max_t0:.2f}ms, Trung bình = {avg_t0:.2f}ms -> {'ĐẠT CHUẨN ( < 1000ms )' if max_t0 < 1000 else 'VI PHẠM'}")
    print(f" - Player 1 (BFS): Lớn nhất = {max_t1:.2f}ms, Trung bình = {avg_t1:.2f}ms -> {'ĐẠT CHUẨN ( < 1000ms )' if max_t1 < 1000 else 'VI PHẠM'}")
    print("=" * 85)


if __name__ == "__main__":
    run_competitive_match()
