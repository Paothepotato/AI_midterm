import time
from collections import deque
from typing import Dict, List, Optional, Set, Tuple

from core.board import Board
from core.constants import ACTIONS, WAIT_ACTION
from core.deadlock import get_goal_bfs_distances, is_safe_push
from core.state import CompetitiveState, Coord

_last_pos_p1: Optional[Coord] = None
_last_act_p1: Optional[str] = None
_pos_history_p1: List[Coord] = []


def _bfs_path_to_targets(
    board: Board,
    start: Coord,
    targets: Set[Coord],
    obstacles: Set[Coord],
    forbidden_first_act: Optional[str] = None,
    budget_s: float = 0.3
) -> Optional[str]:
    if not targets or start in targets:
        return None

    t0 = time.perf_counter()
    q = deque([(start, None)])
    visited = {start}

    while q:
        if time.perf_counter() - t0 > budget_s:
            break

        curr, first_act = q.popleft()
        if curr in targets:
            if first_act != forbidden_first_act:
                return first_act

        for act_name, (dx, dy) in ACTIONS.items():
            if curr == start and act_name == forbidden_first_act:
                continue

            nbr = (curr[0] + dx, curr[1] + dy)
            if nbr in board.floors and nbr not in obstacles and nbr not in visited:
                visited.add(nbr)
                fa = first_act if first_act is not None else act_name
                q.append((nbr, fa))

    return None


def choose_action(
    board: Board,
    state: CompetitiveState,
    player: int = 1,
    budget_seconds: float = 0.8
) -> str:
    global _last_pos_p1, _last_act_p1, _pos_history_p1
    t0 = time.perf_counter()

    my_pos = state.players[player]
    opp_pos = state.players[1 - player]
    boxes_set = set(state.boxes)
    box_owner_map = {b: o for b, o in zip(state.boxes, state.owners)}
    obstacles = boxes_set | {opp_pos}

    forbidden_act = None
    if _last_pos_p1 == my_pos and _last_act_p1 is not None and _last_act_p1 != WAIT_ACTION:
        forbidden_act = _last_act_p1

    _pos_history_p1.append(my_pos)
    if len(_pos_history_p1) > 8:
        _pos_history_p1.pop(0)

    in_cycle = False
    if len(_pos_history_p1) >= 4:
        if _pos_history_p1[-1] == _pos_history_p1[-3] and _pos_history_p1[-2] == _pos_history_p1[-4]:
            in_cycle = True
        elif len(_pos_history_p1) >= 6 and len(set(_pos_history_p1[-6:])) <= 2:
            in_cycle = True

    goal_dists = get_goal_bfs_distances(board)
    open_goals = [g for g in board.goals if box_owner_map.get(g) != player]

    if not open_goals:
        _last_pos_p1 = my_pos
        _last_act_p1 = WAIT_ACTION
        return WAIT_ACTION

    agent_dist: Dict[Coord, int] = {my_pos: 0}
    q_ag = deque([my_pos])
    while q_ag:
        c = q_ag.popleft()
        d = agent_dist[c]
        for dx, dy in ACTIONS.values():
            nbr = (c[0] + dx, c[1] + dy)
            if nbr in board.floors and nbr not in obstacles and nbr not in agent_dist:
                agent_dist[nbr] = d + 1
                q_ag.append(nbr)

    neutral_boxes = [b for b, o in box_owner_map.items() if o == -1]
    opp = 1 - player
    opp_scored_boxes = [b for b, o in box_owner_map.items() if o == opp and b in board.goals]

    categories = [
        (neutral_boxes, False),
        (opp_scored_boxes, True)
    ]

    candidates = []

    for b_list, is_steal in categories:
        for box in b_list:
            bx, by = box
            for push_act, (dx, dy) in ACTIONS.items():
                push_from = (bx - dx, by - dy)
                box_dest = (bx + dx, by + dy)

                if my_pos == push_from and push_act == forbidden_act:
                    continue

                if push_from not in board.floors or push_from in boxes_set or push_from == opp_pos:
                    continue
                if box_dest not in board.floors or box_dest in boxes_set or box_dest == opp_pos:
                    continue

                if not is_safe_push(board, boxes_set, box, box_dest):
                    continue

                d_agent = agent_dist.get(push_from, 10**6)
                if d_agent == 10**6:
                    continue

                best_box_to_goal = 10**6
                for g in open_goals:
                    if g in goal_dists and box_dest in goal_dists[g]:
                        d_bg = goal_dists[g][box_dest]
                        if d_bg < best_box_to_goal:
                            best_box_to_goal = d_bg

                if best_box_to_goal == 10**6:
                    continue

                if is_steal:
                    bonus = -50 if box_dest in board.goals else -20
                    score = d_agent * 2 + best_box_to_goal * 3 + bonus
                else:
                    bonus = -70 if box_dest in open_goals else 0
                    score = d_agent * 2 + best_box_to_goal * 3 + bonus

                candidates.append((score, push_from, push_act, box))

    if candidates:
        candidates.sort(key=lambda c: c[0])
        selected_idx = 1 if (in_cycle and len(candidates) > 1) else 0
        _, push_from, push_act, _ = candidates[selected_idx]

        if my_pos == push_from and push_act != forbidden_act:
            _last_pos_p1 = my_pos
            _last_act_p1 = push_act
            return push_act

        time_left = budget_seconds - (time.perf_counter() - t0)
        step_act = _bfs_path_to_targets(
            board, my_pos, {push_from}, obstacles,
            forbidden_first_act=forbidden_act, budget_s=max(0.05, time_left * 0.7)
        )

        if step_act is not None:
            dx, dy = ACTIONS.get(step_act, (0, 0))
            next_step_pos = (my_pos[0] + dx, my_pos[1] + dy)
            if next_step_pos != opp_pos:
                _last_pos_p1 = my_pos
                _last_act_p1 = step_act
                return step_act

    for act_name, (dx, dy) in ACTIONS.items():
        if act_name == forbidden_act:
            continue
        nbr = (my_pos[0] + dx, my_pos[1] + dy)
        if nbr in board.floors and nbr not in obstacles:
            _last_pos_p1 = my_pos
            _last_act_p1 = act_name
            return act_name

    _last_pos_p1 = my_pos
    _last_act_p1 = WAIT_ACTION
    return WAIT_ACTION
