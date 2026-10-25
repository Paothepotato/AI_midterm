import os
import sys
import time
import tracemalloc
from typing import Dict, List, Any


if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass


CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import matplotlib.pyplot as plt
import numpy as np

from core.board import Board
from task2.solver import SearchSolver


def resolve_map_path(file_path: str) -> str:
    candidates = [
        file_path,
        os.path.join(PROJECT_ROOT, file_path),
        os.path.join(CURRENT_DIR, "..", file_path),
        os.path.join(PROJECT_ROOT, "maps", os.path.basename(file_path)),
    ]
    for c in candidates:
        if os.path.isfile(c):
            return os.path.abspath(c)
    return file_path


def run_single_experiment(map_path: str, algorithm: str, timeout: float = 30.0) -> Dict[str, Any]:
    actual_path = resolve_map_path(map_path)
    board = Board.from_file(actual_path)
    solver = SearchSolver(board, algorithm=algorithm, prune_deadlocks=True)

    tracemalloc.start()
    res = solver.solve(timeout=timeout)
    current_mem, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    peak_mem_kb = peak_mem / 1024.0

    return {
        "algorithm": algorithm.upper(),
        "status": res.status,
        "cost": res.cost,
        "expanded": res.expanded,
        "generated": res.generated,
        "peak_frontier": res.peak_frontier,
        "peak_mem_kb": peak_mem_kb,
        "time_s": res.elapsed_seconds,
    }


def run_full_benchmark():
    test_cases = [
        {"name": "Small Easy (2 Boxes)", "file": "maps/map_easy.txt", "boxes": 2},
        {"name": "Example (Medium)", "file": "maps/example_map.txt", "boxes": 7},
        {"name": "Medium Obstacle (8 Boxes)", "file": "maps/map_medium.txt", "boxes": 8},
    ]

    print("=" * 90)
    print("BẮT ĐẦU CHẠY THỰC NGHIỆM ĐO LƯỜNG: UCS VS A* (HUNGARIAN HEURISTIC)")
    print("=" * 90)

    results = []

    for tc in test_cases:
        map_name = tc["name"]
        map_file = tc["file"]
        print(f"\n[+] Đang đo lường trên: {map_name} ({map_file})...")

        ucs_data = run_single_experiment(map_file, "ucs", timeout=25.0)
        astar_data = run_single_experiment(map_file, "astar", timeout=25.0)

        node_reduction = 0.0
        if ucs_data["expanded"] > 0:
            node_reduction = (1.0 - astar_data["expanded"] / ucs_data["expanded"]) * 100.0

        speedup = 1.0
        if astar_data["time_s"] > 0:
            speedup = ucs_data["time_s"] / astar_data["time_s"]

        mem_reduction = 0.0
        if ucs_data["peak_mem_kb"] > 0:
            mem_reduction = (1.0 - astar_data["peak_mem_kb"] / ucs_data["peak_mem_kb"]) * 100.0

        item = {
            "name": map_name,
            "boxes": tc["boxes"],
            "ucs": ucs_data,
            "astar": astar_data,
            "node_reduction": node_reduction,
            "speedup": speedup,
            "mem_reduction": mem_reduction,
        }
        results.append(item)

        print(f"  UCS -> Chi phí: {ucs_data['cost']}, Nodes: {ucs_data['expanded']}, RAM: {ucs_data['peak_mem_kb']:.1f} KB, Thời gian: {ucs_data['time_s']:.4f}s")
        print(f"  A*  -> Chi phí: {astar_data['cost']}, Nodes: {astar_data['expanded']}, RAM: {astar_data['peak_mem_kb']:.1f} KB, Thời gian: {astar_data['time_s']:.4f}s")
        print(f"  --> A* giảm số node: {node_reduction:.1f}% | Tăng tốc: {speedup:.1f}x")

    generate_benchmark_plots(results)

    print_markdown_table(results)

    return results


def print_markdown_table(results: List[Dict[str, Any]]):
    print("\n" + "=" * 90)
    print("BẢNG TỔNG HỢP KẾT QUẢ THỰC NGHIỆM TASK 3 CHO SLIDE VÀ BÁO CÁO")
    print("=" * 90)
    header = (
        "| Bản đồ | Số Hộp | Chi phí ($g^*$) | UCS Expanded | A* Expanded | Giảm Node (%) | "
        "UCS Thời gian (s) | A* Thời gian (s) | Tăng tốc (Speedup) | UCS RAM (KB) | A* RAM (KB) |"
    )
    sep = (
        "| :--- | :---: | :---: | :---: | :---: | :---: | "
        ":---: | :---: | :---: | :---: | :---: |"
    )
    print(header)
    print(sep)
    for r in results:
        u = r["ucs"]
        a = r["astar"]
        row = (
            f"| {r['name']} | {r['boxes']} | {a['cost']} | "
            f"{u['expanded']:,} | {a['expanded']:,} | **{r['node_reduction']:.1f}%** | "
            f"{u['time_s']:.4f} | {a['time_s']:.4f} | **{r['speedup']:.1f}x** | "
            f"{u['peak_mem_kb']:.1f} | {a['peak_mem_kb']:.1f} |"
        )
        print(row)


def generate_benchmark_plots(results: List[Dict[str, Any]]):
    plots_dir = os.path.join(CURRENT_DIR, "plots")
    os.makedirs(plots_dir, exist_ok=True)

    labels = [r["name"] for r in results]
    ucs_expanded = [r["ucs"]["expanded"] for r in results]
    astar_expanded = [r["astar"]["expanded"] for r in results]

    ucs_time = [r["ucs"]["time_s"] for r in results]
    astar_time = [r["astar"]["time_s"] for r in results]

    ucs_mem = [r["ucs"]["peak_mem_kb"] for r in results]
    astar_mem = [r["astar"]["peak_mem_kb"] for r in results]

    x = np.arange(len(labels))
    width = 0.35

    # 1. Biểu đồ số lượng nút mở rộng (Nodes Expanded) - Thang Logarithmic
    fig, ax = plt.subplots(figsize=(8.5, 6))
    rects1 = ax.bar(x - width/2, ucs_expanded, width, label='UCS', color='#4A90E2', edgecolor='black')
    rects2 = ax.bar(x + width/2, astar_expanded, width, label='A* (Hungarian Heuristic)', color='#E94E77', edgecolor='black')
    ax.set_yscale('log')
    ax.set_ylabel('Số Node Mở Rộng (Thang Logarithmic)', fontsize=11)
    ax.set_title('Độ Phức Tạp Không Gian & Thời Gian: Số Node Mở Rộng (UCS vs A*)', fontsize=12, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=15, ha='right', fontsize=10)
    ax.legend(fontsize=10)
    ax.grid(axis='y', linestyle='--', alpha=0.6)

    for rect in rects1:
        h = rect.get_height()
        ax.annotate(f'{int(h):,}', xy=(rect.get_x() + rect.get_width() / 2, h),
                    xytext=(0, 4), textcoords="offset points", ha='center', va='bottom', fontsize=8, rotation=20)
    for rect in rects2:
        h = rect.get_height()
        ax.annotate(f'{int(h):,}', xy=(rect.get_x() + rect.get_width() / 2, h),
                    xytext=(0, 4), textcoords="offset points", ha='center', va='bottom', fontsize=8, rotation=20)

    fig.tight_layout()
    plot_path1 = os.path.join(plots_dir, "nodes_comparison.png")
    fig.savefig(plot_path1, dpi=200)
    plt.close(fig)
    print(f"\n[+] Đã lưu biểu đồ: {plot_path1}")

    # 2. Biểu đồ thời gian thực thi (Execution Time)
    fig, ax = plt.subplots(figsize=(8.5, 6))
    rects1 = ax.bar(x - width/2, ucs_time, width, label='UCS', color='#4A90E2', edgecolor='black')
    rects2 = ax.bar(x + width/2, astar_time, width, label='A* (Hungarian Heuristic)', color='#E94E77', edgecolor='black')
    ax.set_ylabel('Thời Gian Thực Thi (Giây)', fontsize=11)
    ax.set_title('Độ Phức Tạp Thời Gian: Thời Gian CPU (UCS vs A*)', fontsize=12, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=15, ha='right', fontsize=10)
    ax.legend(fontsize=10)
    ax.grid(axis='y', linestyle='--', alpha=0.6)

    for rect in rects1:
        h = rect.get_height()
        ax.annotate(f'{h:.3f}s', xy=(rect.get_x() + rect.get_width() / 2, h),
                    xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontsize=8)
    for rect in rects2:
        h = rect.get_height()
        ax.annotate(f'{h:.3f}s', xy=(rect.get_x() + rect.get_width() / 2, h),
                    xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontsize=8)

    fig.tight_layout()
    plot_path2 = os.path.join(plots_dir, "time_comparison.png")
    fig.savefig(plot_path2, dpi=200)
    plt.close(fig)
    print(f"[+] Đã lưu biểu đồ: {plot_path2}")

    # 3. Biểu đồ bộ nhớ RAM tiêu thụ (Peak RAM)
    fig, ax = plt.subplots(figsize=(8.5, 6))
    rects1 = ax.bar(x - width/2, ucs_mem, width, label='UCS', color='#4A90E2', edgecolor='black')
    rects2 = ax.bar(x + width/2, astar_mem, width, label='A* (Hungarian Heuristic)', color='#E94E77', edgecolor='black')
    ax.set_ylabel('Bộ Nhớ RAM Đỉnh (KB)', fontsize=11)
    ax.set_title('Độ Phức Tạp Không Gian: Bộ Nhớ RAM Đỉnh (UCS vs A*)', fontsize=12, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=15, ha='right', fontsize=10)
    ax.legend(fontsize=10)
    ax.grid(axis='y', linestyle='--', alpha=0.6)

    for rect in rects1:
        h = rect.get_height()
        txt = f'{h/1024:.1f}MB' if h >= 1024 else f'{h:.0f}KB'
        ax.annotate(txt, xy=(rect.get_x() + rect.get_width() / 2, h),
                    xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontsize=8)
    for rect in rects2:
        h = rect.get_height()
        txt = f'{h/1024:.1f}MB' if h >= 1024 else f'{h:.0f}KB'
        ax.annotate(txt, xy=(rect.get_x() + rect.get_width() / 2, h),
                    xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontsize=8)

    fig.tight_layout()
    plot_path3 = os.path.join(plots_dir, "memory_comparison.png")
    fig.savefig(plot_path3, dpi=200)
    plt.close(fig)
    print(f"[+] Đã lưu biểu đồ: {plot_path3}")


if __name__ == "__main__":
    run_full_benchmark()
