from collections import deque
from typing import Dict, FrozenSet, List, Optional, Set, Tuple

from core.board import Board
from core.constants import ACTIONS
from core.state import Coord

_safe_cells_cache: Dict[int, FrozenSet[Coord]] = {}
_goal_bfs_cache: Dict[int, Dict[Coord, Dict[Coord, int]]] = {}


def get_goal_bfs_distances(board: Board) -> Dict[Coord, Dict[Coord, int]]:
    bid = id(board)
    if bid in _goal_bfs_cache:
        return _goal_bfs_cache[bid]

    all_dists: Dict[Coord, Dict[Coord, int]] = {}
    for g in board.goals:
        dist: Dict[Coord, int] = {g: 0}
        q = deque([g])
        while q:
            cur = q.popleft()
            d = dist[cur]
            for dx, dy in ACTIONS.values():
                nbr = (cur[0] + dx, cur[1] + dy)
                if nbr in board.floors and nbr not in dist:
                    dist[nbr] = d + 1
                    q.append(nbr)
        all_dists[g] = dist

    _goal_bfs_cache[bid] = all_dists
    return all_dists


def get_safe_box_cells(board: Board) -> FrozenSet[Coord]:
    bid = id(board)
    if bid in _safe_cells_cache:
        return _safe_cells_cache[bid]

    safe: Set[Coord] = set(board.goals)
    q: deque = deque(list(board.goals))
    while q:
        cur = q.popleft()
        for dx, dy in ACTIONS.values():
            prev_box = (cur[0] - dx, cur[1] - dy)
            pusher = (cur[0] - 2 * dx, cur[1] - 2 * dy)
            if (prev_box in board.floors and
                    pusher in board.floors and
                    prev_box not in safe):
                safe.add(prev_box)
                q.append(prev_box)

    res = frozenset(safe)
    _safe_cells_cache[bid] = res
    return res


def is_block_2x2_deadlock(board: Board, boxes: Set[Coord], new_box_pos: Coord) -> bool:
    test_boxes = boxes | {new_box_pos}
    bx, by = new_box_pos

    offsets = [(-1, -1), (0, -1), (-1, 0), (0, 0)]

    for ox, oy in offsets:
        x0, y0 = bx + ox, by + oy
        square = [
            (x0, y0), (x0 + 1, y0),
            (x0, y0 + 1), (x0 + 1, y0 + 1)
        ]

        all_blocked = True
        has_non_goal_box = False

        for cell in square:
            is_wall = cell not in board.floors
            is_box = cell in test_boxes
            if not (is_wall or is_box):
                all_blocked = False
                break
            if is_box and cell not in board.goals:
                has_non_goal_box = True

        if all_blocked and has_non_goal_box:
            return True

    return False


def is_safe_push(board: Board, current_boxes: Set[Coord],
                 box_from: Coord, box_to: Coord) -> bool:
    safe_cells = get_safe_box_cells(board)
    if box_to not in safe_cells:
        return False

    other_boxes = current_boxes - {box_from}
    if is_block_2x2_deadlock(board, other_boxes, box_to):
        return False

    return True
