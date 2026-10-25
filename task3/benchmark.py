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


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import matplotlib.pyplot as plt
import numpy as np

from core.board import Board
from task2.solver import SearchSolver


def run_single_experiment(map_path: str, algorithm: str, timeout: float = 30.0) -> Dict[str, Any]:
    board = Board.from_file(map_path)
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
        {"name": "Simple (1 Box)", "file": "maps/example_simple.txt", "boxes": 1},
        {"name": "Small 2 (2 Boxes)", "file": "maps/map_small_3.txt", "boxes": 2},
        {"name": "Small Easy (2 Boxes)", "file": "maps/map_easy.txt", "boxes": 2},
        {"name": "Medium 1 (3 Boxes)", "file": "maps/map_medium_1.txt", "boxes": 3},
        {"name": "Medium Obstacle (3 Boxes)", "file": "maps/map_medium_2.txt", "boxes": 3},
        {"name": "Large (4 Boxes)", "file": "maps/map_large_1.txt", "boxes": 4},
    ]

    print("=" * 90)
    print("BẮT ĐẦU CHẠY THỰC NGHIỆM ĐO LƯỜNG: UCS VS A* (HUNGARIAN HEURISTIC)")
    print("=" * 90)

    results = []

    for tc in test_cases:
        map_name = tc["name"]
        map_file = tc["file"]
        print(f"\n[+] Đang đo lường trên: {map_name} ({map_file})...")

        ucs_data = run_single_experiment(map_file, "ucs", timeout=20.0)
        astar_data = run_single_experiment(map_file, "astar", timeout=20.0)

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
    plots_dir = os.path.join(os.path.dirname(__file__), "plots")
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

    fig, ax = plt.subplots(figsize=(8, 6))
    rects1 = ax.bar(x - width/2, ucs_expanded, width, label='UCS', color='#4A90E2', edgecolor='black')
    rects2 = ax.bar(x + width/2, astar_expanded, width, label='A* (Hungarian Heuristic)', color='#E94E77', edgecolor='black')
    ax.set_yscale('log')
    ax.set_ylabel('Số Node Mở Rộng (Thang Logarithmic)')
    ax.set_title('Độ Phức Tạp Không Gian & Thời Gian: Số Node Mở Rộng (UCS vs A*)')
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=20, ha='right', fontsize=9)
    ax.legend()
    ax.grid(axis='y', linestyle='--', alpha=0.6)
    fig.tight_layout()
    plot_path1 = os.path.join(plots_dir, "nodes_comparison.png")
    fig.savefig(plot_path1, dpi=200)
    plt.close(fig)
    print(f"\n[+] Đã lưu biểu đồ: {plot_path1}")

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.bar(x - width/2, ucs_time, width, label='UCS', color='#4A90E2', edgecolor='black')
    ax.bar(x + width/2, astar_time, width, label='A* (Hungarian Heuristic)', color='#E94E77', edgecolor='black')
    ax.set_ylabel('Thời Gian Thực Thi (Giây)')
    ax.set_title('Độ Phức Tạp Thời Gian: Thời Gian CPU (UCS vs A*)')
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=20, ha='right', fontsize=9)
    ax.legend()
    ax.grid(axis='y', linestyle='--', alpha=0.6)
    fig.tight_layout()
    plot_path2 = os.path.join(plots_dir, "time_comparison.png")
    fig.savefig(plot_path2, dpi=200)
    plt.close(fig)
    print(f"[+] Đã lưu biểu đồ: {plot_path2}")

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.bar(x - width/2, ucs_mem, width, label='UCS', color='#4A90E2', edgecolor='black')
    ax.bar(x + width/2, astar_mem, width, label='A* (Hungarian Heuristic)', color='#E94E77', edgecolor='black')
    ax.set_ylabel('Bộ Nhớ RAM Đỉnh (KB)')
    ax.set_title('Độ Phức Tạp Không Gian: Bộ Nhớ RAM Đỉnh (UCS vs A*)')
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=20, ha='right', fontsize=9)
    ax.legend()
    ax.grid(axis='y', linestyle='--', alpha=0.6)
    fig.tight_layout()
    plot_path3 = os.path.join(plots_dir, "memory_comparison.png")
    fig.savefig(plot_path3, dpi=200)
    plt.close(fig)
    print(f"[+] Đã lưu biểu đồ: {plot_path3}")


if __name__ == "__main__":
    run_full_benchmark()
