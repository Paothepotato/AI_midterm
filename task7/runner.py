import time
from typing import List, Optional, Tuple

from core.board import Board
from core.constants import WAIT_ACTION
from core.state import CompetitiveState
from task7 import agent_astar, agent_bfs


class DecisionRunner:
    def __init__(self, agent0_module=agent_astar, agent1_module=agent_bfs):
        self.agent0 = agent0_module
        self.agent1 = agent1_module

    def decide(
        self,
        board: Board,
        state: CompetitiveState,
        limit_seconds: float = 1.0
    ) -> Tuple[List[str], List[float], List[Optional[str]]]:
        actions = [WAIT_ACTION, WAIT_ACTION]
        timings = [0.0, 0.0]
        errors = [None, None]

        t0_start = time.perf_counter()
        try:
            act0 = self.agent0.choose_action(board, state, player=0, budget_seconds=0.8)
            t0_end = time.perf_counter()
            timings[0] = t0_end - t0_start
            if timings[0] > limit_seconds:
                actions[0] = WAIT_ACTION
                errors[0] = f"Quá hạn thời gian ({timings[0]:.3f}s > {limit_seconds}s)"
            else:
                actions[0] = act0
        except Exception as e:
            timings[0] = time.perf_counter() - t0_start
            actions[0] = WAIT_ACTION
            errors[0] = str(e)

        t1_start = time.perf_counter()
        try:
            act1 = self.agent1.choose_action(board, state, player=1, budget_seconds=0.8)
            t1_end = time.perf_counter()
            timings[1] = t1_end - t1_start
            if timings[1] > limit_seconds:
                actions[1] = WAIT_ACTION
                errors[1] = f"Quá hạn thời gian ({timings[1]:.3f}s > {limit_seconds}s)"
            else:
                actions[1] = act1
        except Exception as e:
            timings[1] = time.perf_counter() - t1_start
            actions[1] = WAIT_ACTION
            errors[1] = str(e)

        return actions, timings, errors
