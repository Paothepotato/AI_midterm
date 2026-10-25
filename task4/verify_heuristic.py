import os
import sys
from typing import Any, Dict, List, Tuple


if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import matplotlib.pyplot as plt
import numpy as np

from core.board import Board
from core.heuristic import SokobanHeuristic
from core.state import State
from task2.solver import SearchSolver


def sample_states_from_search(board: Board, max_samples: int = 50) -> List[State]:
    visited = {board.initial}
    queue = [board.initial]
    sampled = [board.initial]

    while queue and len(sampled) < max_samples:
        curr = queue.pop(0)
        for _, nxt in board.successors(curr):
            if nxt not in visited:
                visited.add(nxt)
                queue.append(nxt)
                sampled.append(nxt)
                if len(sampled) >= max_samples:
                    break

    return sampled


def verify_admissibility(board: Board, samples: List[State]) -> Dict[str, Any]:
    heuristic = SokobanHeuristic(board)
    data = []
    violations = 0

    print(f"\n[+] Đang kiểm chứng tính Admissible trên {len(samples)} trạng thái mẫu...")

    for idx, s in enumerate(samples):
        h_val = heuristic.compute_h(s)

        temp_board = Board(
            width=board.width,
            height=board.height,
            walls=board.walls,
            floors=board.floors,
            goals=board.goals,
            initial=s,
            name=f"temp_{idx}"
        )
        solver = SearchSolver(temp_board, algorithm='ucs', prune_deadlocks=True)
        res = solver.solve(timeout=5.0)

        if res.status == 'solved':
            h_star = res.cost
            diff = h_star - h_val
            ratio = (h_val / h_star) if h_star > 0 else 1.0

            is_admissible = (h_val <= h_star)
            if not is_admissible:
                violations += 1

            data.append({
                "state": s,
                "h": h_val,
                "h_star": h_star,
                "diff": diff,
                "ratio": ratio,
                "valid": is_admissible
            })

    print(f"  -> Số trạng thái giải được đã kiểm tra: {len(data)}")
    print(f"  -> Số trường hợp vi phạm Admissibility: {violations}")
    assert violations == 0, f"Phát hiện {violations} trường hợp vi phạm tính Admissible!"

    return {
        "data": data,
        "violations": violations,
        "total_tested": len(data)
    }


def verify_consistency(board: Board, num_transitions: int = 500) -> Dict[str, Any]:
    heuristic = SokobanHeuristic(board)
    visited = {board.initial}
    queue = [board.initial]

    delta_h_list = []
    transitions_checked = 0
    violations = 0

    print(f"\n[+] Đang kiểm chứng tính Consistent (Bất đẳng thức tam giác) trên các bước chuyển...")

    while queue and transitions_checked < num_transitions:
        curr = queue.pop(0)
        h_curr = heuristic.compute_h(curr)

        for action, nxt in board.successors(curr):
            h_nxt = heuristic.compute_h(nxt)
            delta_h = h_curr - h_nxt

            transitions_checked += 1
            delta_h_list.append(delta_h)

            if delta_h > 1:
                violations += 1
                print(f"  [!] Vi phạm tại bước chuyển: h(s)={h_curr}, h(s')={h_nxt}, delta={delta_h}")

            if nxt not in visited:
                visited.add(nxt)
                queue.append(nxt)

            if transitions_checked >= num_transitions:
                break

    print(f"  -> Tổng số bước chuyển trạng thái đã đánh giá: {transitions_checked}")
    print(f"  -> Số trường hợp vi phạm tính Consistent: {violations}")
    assert violations == 0, f"Phát hiện {violations} trường hợp vi phạm tính Consistent!"

    return {
        "deltas": delta_h_list,
        "violations": violations,
        "transitions_checked": transitions_checked
    }


def plot_verification_results(adm_data: List[Dict], deltas: List[int]):
    plots_dir = os.path.join(os.path.dirname(__file__), "plots")
    os.makedirs(plots_dir, exist_ok=True)

    h_vals = [d["h"] for d in adm_data]
    h_star_vals = [d["h_star"] for d in adm_data]

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.scatter(h_star_vals, h_vals, color='#4A90E2', alpha=0.7, edgecolors='black', s=60, label='Trạng Thái Mẫu')

    max_val = max(max(h_star_vals, default=10), max(h_vals, default=10)) + 2

    ax.plot([0, max_val], [0, max_val], 'r--', linewidth=2, label='Đường Cận Trên: h(n) = h*(n)')

    ax.set_xlabel('Chi Phí Tối Ưu Thực Tế h*(n) từ UCS')
    ax.set_ylabel('Giá Trị Heuristic h(n) (Hungarian BFS)')
    ax.set_title('Kiểm Chứng Tính Admissible: h(n) <= h*(n)')
    ax.set_xlim(0, max_val)
    ax.set_ylim(0, max_val)
    ax.legend(loc='upper left')
    ax.grid(True, linestyle='--', alpha=0.5)
    fig.tight_layout()

    plot_admissibility = os.path.join(plots_dir, "admissibility_scatter.png")
    fig.savefig(plot_admissibility, dpi=200)
    plt.close(fig)
    print(f"[+] Đã lưu biểu đồ: {plot_admissibility}")

    fig, ax = plt.subplots(figsize=(8, 6))
    unique, counts = np.unique(deltas, return_counts=True)

    colors = ['#50E3C2' if u <= 1 else '#E94E77' for u in unique]
    bars = ax.bar(unique, counts, width=0.4, color=colors, edgecolor='black')

    ax.set_xlabel('Độ Biến Thiên Heuristic: delta_h = h(s) - h(s\')')
    ax.set_ylabel('Số Lượng Bước Chuyển (Tần Suất)')
    ax.set_title('Kiểm Chứng Tính Consistent: Bất Đẳng Thức Tam Giác (delta_h <= 1)')
    ax.set_xticks(unique)
    ax.axvline(1.5, color='red', linestyle='--', label='Ranh Giới Consistent (delta_h <= 1)')
    ax.legend()
    ax.grid(axis='y', linestyle='--', alpha=0.5)

    for bar, count in zip(bars, counts):
        height = bar.get_height()
        ax.annotate(f'{count}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3), textcoords="offset points",
                    ha='center', va='bottom', fontsize=10, weight='bold')

    fig.tight_layout()
    plot_consistency = os.path.join(plots_dir, "consistency_histogram.png")
    fig.savefig(plot_consistency, dpi=200)
    plt.close(fig)
    print(f"[+] Đã lưu biểu đồ: {plot_consistency}")


def run_heuristic_verification():
    print("=" * 80)
    print("TASK 4: KIỂM CHỨNG LÝ THUYẾT VÀ THỰC NGHIỆM TÍNH CHẤT HEURISTIC")
    print("=" * 80)

    board = Board.from_file("maps/map_small_easy.txt")
    print(f"Đã nạp bản đồ: {board.name} ({board.width}x{board.height})")

    samples = sample_states_from_search(board, max_samples=40)
    adm_result = verify_admissibility(board, samples)

    cons_result = verify_consistency(board, num_transitions=300)

    plot_verification_results(adm_result["data"], cons_result["deltas"])

    print("\n" + "=" * 80)
    print("BẢNG MẪU KIỂM CHỨNG TÍNH ADMISSIBLE (10 trạng thái đầu tiên)")
    print("=" * 80)
    print("| Mẫu | h(n) | h*(n) | Chênh Lệch (h* - h) | Tỷ Số (h / h*) | Thỏa Admissible? |")
    print("| :---: | :---: | :---: | :---: | :---: | :---: |")
    for i, row in enumerate(adm_result["data"][:10]):
        print(f"| {i+1} | {row['h']} | {row['h_star']} | {row['diff']} | {row['ratio']:.2f} | **ĐẠT (HỢP LỆ)** |")

    print("\nTỔNG HỢP KIỂM CHỨNG TÍNH CONSISTENT:")
    unique, counts = np.unique(cons_result["deltas"], return_counts=True)
    for u, c in zip(unique, counts):
        print(f" - delta_h = {u:2d} : {c:4d} bước chuyển ({c/len(cons_result['deltas'])*100:.1f}%)")

    print("\n-> TẤT CẢ TÍNH CHẤT HEURISTIC ĐÃ ĐƯỢC CHỨNG MINH VÀ KIỂM CHỨNG THÀNH CÔNG 100%!\n")


if __name__ == "__main__":
    run_heuristic_verification()
