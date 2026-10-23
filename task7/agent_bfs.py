from collections import deque
import time
from typing import List, Optional, Set, Tuple

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

    box_owner_map = {b: o for b, o in zip(state.boxes, state.owners)}
    candidate_boxes = [b for b, o in box_owner_map.items() if o != player]

    if not candidate_boxes:
        return WAIT_ACTION

    px, py = my_pos
    closest_box = min(candidate_boxes, key=lambda b: abs(b[0] - px) + abs(b[1] - py))

    for act_name, (dx, dy) in ACTIONS.items():
        if (px + dx, py + dy) == closest_box:
            dest = (closest_box[0] + dx, closest_box[1] + dy)

            if dest in board.floors and dest not in boxes_set and dest != opp_pos:
                return act_name

    adj_cells = set()
    for dx, dy in ACTIONS.values():
        c = (closest_box[0] + dx, closest_box[1] + dy)
        if c in board.floors and c not in boxes_set and c != opp_pos:
            adj_cells.add(c)

    if adj_cells:
        queue = deque([(my_pos, None)])
        visited = {my_pos}
        obstacles = boxes_set | {opp_pos}

        while queue:
            if time.perf_counter() - start_time > budget_seconds - 0.05:
                break

            curr, first_act = queue.popleft()
            if curr in adj_cells:
                if first_act is not None:
                    return first_act

            cx, cy = curr
            for act_name, (dx, dy) in ACTIONS.items():
                nbr = (cx + dx, cy + dy)
                if nbr in board.floors and nbr not in obstacles and nbr not in visited:
                    visited.add(nbr)
                    act_to_pass = first_act if first_act is not None else act_name
                    queue.append((nbr, act_to_pass))

    for act_name, (dx, dy) in ACTIONS.items():
        nbr = (px + dx, py + dy)
        if nbr in board.floors and nbr not in boxes_set and nbr != opp_pos:
            return act_name

    return WAIT_ACTION
