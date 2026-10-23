from collections import deque
import heapq
import time
from typing import Dict, List, Optional, Set, Tuple

from core.board import Board
from core.constants import ACTIONS, WAIT_ACTION
from core.state import CompetitiveState, Coord


def choose_action(
    board: Board,
    state: CompetitiveState,
    player: int,
    budget_seconds: float = 0.8
) -> str:
    start_time = time.perf_counter()

    my_pos = state.players[player]
    opp_pos = state.players[1 - player]
    boxes_set = set(state.boxes)
    px, py = my_pos

    box_owner_map = {b: o for b, o in zip(state.boxes, state.owners)}

    available_goals = [g for g in board.goals if box_owner_map.get(g) != player]
    if not available_goals:
        return WAIT_ACTION

    candidate_boxes = [b for b, o in box_owner_map.items() if o != player]
    if not candidate_boxes:
        return WAIT_ACTION

    best_candidate = None
    best_cost = 10**6

    for b in candidate_boxes:
        for g in available_goals:
            d_bg = abs(b[0] - g[0]) + abs(b[1] - g[1])

            d_pb = abs(px - b[0]) + abs(py - b[1])

            cost = d_bg * 3 + d_pb
            if cost < best_cost:
                best_cost = cost
                best_candidate = (b, g)

    if best_candidate is None:
        return WAIT_ACTION

    target_box, target_goal = best_candidate
    bx, by = target_box
    gx, gy = target_goal

    for act_name, (dx, dy) in ACTIONS.items():
        if (px + dx, py + dy) in boxes_set:
            adj_box = (px + dx, py + dy)
            box_dest = (adj_box[0] + dx, adj_box[1] + dy)

            if (box_dest in board.floors and
                box_dest not in boxes_set and
                box_dest != opp_pos):
                if box_dest in available_goals:
                    return act_name

    if (abs(px - bx) + abs(py - by)) == 1:
        push_dx = bx - px
        push_dy = by - py
        for act_name, (dx, dy) in ACTIONS.items():
            if (dx, dy) == (push_dx, push_dy):
                dest = (bx + dx, by + dy)
                if (dest in board.floors and
                    dest not in boxes_set and
                    dest != opp_pos):
                    curr_d = abs(bx - gx) + abs(by - gy)
                    nxt_d = abs(dest[0] - gx) + abs(dest[1] - gy)

                    if nxt_d <= curr_d or dest in available_goals:
                        return act_name

    ideal_push_positions = []
    for act_name, (dx, dy) in ACTIONS.items():
        behind_pos = (bx - dx, by - dy)
        dest_pos = (bx + dx, by + dy)
        if (behind_pos in board.floors and
            behind_pos not in boxes_set and
            behind_pos != opp_pos and
            dest_pos in board.floors and
            dest_pos not in boxes_set and
            dest_pos != opp_pos):
            curr_d = abs(bx - gx) + abs(by - gy)
            dest_d = abs(dest_pos[0] - gx) + abs(dest_pos[1] - gy)
            if dest_d <= curr_d or dest_pos in available_goals:
                ideal_push_positions.append(behind_pos)

    obstacles = boxes_set | {opp_pos}
    if ideal_push_positions:
        act = _astar_path(board, my_pos, set(ideal_push_positions), obstacles, timeout=0.3)
        if act is not None:
            return act

    adj_cells = set()
    for dx, dy in ACTIONS.values():
        c = (bx + dx, by + dy)
        if c in board.floors and c not in obstacles:
            adj_cells.add(c)

    if adj_cells:
        act = _astar_path(board, my_pos, adj_cells, obstacles, timeout=0.2)
        if act is not None:
            return act

    for act_name, (dx, dy) in ACTIONS.items():
        tgt = (px + dx, py + dy)
        if tgt in boxes_set:
            box_dest = (tgt[0] + dx, tgt[1] + dy)
            if (box_dest in board.floors and
                box_dest not in boxes_set and
                box_dest != opp_pos):
                return act_name

    for act_name, (dx, dy) in ACTIONS.items():
        nxt = (px + dx, py + dy)
        if nxt in board.floors and nxt not in boxes_set and nxt != opp_pos:
            return act_name

    return WAIT_ACTION


def _astar_path(
    board: Board,
    start: Coord,
    targets: Set[Coord],
    obstacles: Set[Coord],
    timeout: float = 0.3
) -> Optional[str]:
    if start in targets:
        return None

    start_time = time.perf_counter()
    frontier = []
    counter = 0

    def h_cost(c: Coord) -> int:
        return min(abs(c[0] - t[0]) + abs(c[1] - t[1]) for t in targets)

    heapq.heappush(frontier, (h_cost(start), counter, 0, start, None))
    cost_so_far = {start: 0}

    while frontier:
        if time.perf_counter() - start_time > timeout:
            break

        f, _, g, curr, first_act = heapq.heappop(frontier)

        if curr in targets:
            return first_act

        cx, cy = curr
        for act_name, (dx, dy) in ACTIONS.items():
            nbr = (cx + dx, cy + dy)

            if nbr in board.floors and nbr not in obstacles:
                new_g = g + 1
                if nbr not in cost_so_far or new_g < cost_so_far[nbr]:
                    cost_so_far[nbr] = new_g

                    act_to_pass = first_act if first_act is not None else act_name
                    counter += 1
                    pri = new_g + h_cost(nbr)
                    heapq.heappush(frontier, (pri, counter, new_g, nbr, act_to_pass))

    return None
