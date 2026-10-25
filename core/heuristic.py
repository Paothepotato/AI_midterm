from collections import deque
from typing import Dict, FrozenSet, List, Optional, Set, Tuple

try:
    from scipy.optimize import linear_sum_assignment
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

from core.board import Board
from core.state import Coord, State


INF = 10**8


def solve_min_cost_matching(cost_matrix: List[List[int]]) -> int:
    k = len(cost_matrix)
    if k == 0:
        return 0

    if HAS_SCIPY:
        row_ind, col_ind = linear_sum_assignment(cost_matrix)
        total_cost = int(sum(cost_matrix[r][c] for r, c in zip(row_ind, col_ind)))
        return total_cost

    best_cost = [INF]

    min_col = [min(cost_matrix[r][c] for r in range(k)) for c in range(k)]

    def bnb(box_idx: int, used_goals_mask: int, current_cost: int):
        if current_cost >= best_cost[0]:
            return
        if box_idx == k:
            best_cost[0] = current_cost
            return

        lb = current_cost + sum(min_col[c] for c in range(k) if not (used_goals_mask & (1 << c)))
        if lb >= best_cost[0]:
            return

        candidates = [(cost_matrix[box_idx][c], c) for c in range(k) if not (used_goals_mask & (1 << c))]
        candidates.sort(key=lambda x: x[0])

        for c_cost, c in candidates:
            if current_cost + c_cost < best_cost[0]:
                bnb(box_idx + 1, used_goals_mask | (1 << c), current_cost + c_cost)

    bnb(0, 0, 0)
    return best_cost[0]


class SokobanHeuristic:
    def __init__(self, board: Board):
        self.board = board
        self.goals_list: List[Coord] = sorted(list(board.goals))
        self.num_goals = len(self.goals_list)

        self.dist_matrix: List[Dict[Coord, int]] = []
        self._precompute_bfs_distances()

        self.h_cache: Dict[Tuple[Coord, ...], int] = {}

        self.dead_squares: Set[Coord] = self._compute_static_deadlocks()

    def _precompute_bfs_distances(self):
        for g in self.goals_list:
            dist: Dict[Coord, int] = {g: 0}
            queue = deque([g])
            while queue:
                curr = queue.popleft()
                d = dist[curr]
                cx, cy = curr
                for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                    nbr = (cx + dx, cy + dy)
                    if nbr in self.board.floors and nbr not in dist:
                        dist[nbr] = d + 1
                        queue.append(nbr)
            self.dist_matrix.append(dist)

    def _compute_static_deadlocks(self) -> Set[Coord]:
        dead_cells: Set[Coord] = set()

        for p in self.board.floors:
            if p in self.board.goals:
                continue
            px, py = p
            north_wall = (px, py - 1) in self.board.walls
            south_wall = (px, py + 1) in self.board.walls
            west_wall = (px - 1, py) in self.board.walls
            east_wall = (px + 1, py) in self.board.walls

            if (north_wall and west_wall) or (north_wall and east_wall) or \
               (south_wall and west_wall) or (south_wall and east_wall):
                dead_cells.add(p)

        for y in range(self.board.height):
            for x_start in range(self.board.width):
                if (x_start, y) in dead_cells:
                    for side in (-1, 1):
                        span = []
                        x = x_start + 1
                        has_goal = False
                        while (x, y) in self.board.floors:
                            if (x, y) in self.board.goals:
                                has_goal = True
                                break
                            if (x, y + side) not in self.board.walls:
                                break
                            span.append((x, y))
                            if (x, y) in dead_cells:
                                if not has_goal:
                                    dead_cells.update(span)
                                break
                            x += 1

        for x in range(self.board.width):
            for y_start in range(self.board.height):
                if (x_start := x, y_start) in dead_cells:
                    for side in (-1, 1):
                        span = []
                        y = y_start + 1
                        has_goal = False
                        while (x, y) in self.board.floors:
                            if (x, y) in self.board.goals:
                                has_goal = True
                                break
                            if (x + side, y) not in self.board.walls:
                                break
                            span.append((x, y))
                            if (x, y) in dead_cells:
                                if not has_goal:
                                    dead_cells.update(span)
                                break
                            y += 1

        return dead_cells

    def has_deadlock(self, boxes: Tuple[Coord, ...]) -> bool:
        for b in boxes:
            if b in self.dead_squares:
                return True
        return False

    def compute_h(self, state: State) -> int:
        boxes_key = state.boxes
        if boxes_key in self.h_cache:
            return self.h_cache[boxes_key]

        k = len(boxes_key)
        if k != self.num_goals:
            return 0

        cost_matrix: List[List[int]] = []
        for b in boxes_key:
            row: List[int] = []
            for g_idx in range(self.num_goals):
                d = self.dist_matrix[g_idx].get(b, INF)
                row.append(d)
            cost_matrix.append(row)

        h_val = solve_min_cost_matching(cost_matrix)
        if h_val >= INF:
            h_val = INF

        self.h_cache[boxes_key] = h_val
        return h_val
