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
            timings[0] = time.perf_counter() - t0_start
            actions[0] = act0 if timings[0] <= limit_seconds else WAIT_ACTION
            if timings[0] > limit_seconds:
                errors[0] = f"Timeout ({timings[0]:.3f}s)"
        except Exception as e:
            timings[0] = time.perf_counter() - t0_start
            actions[0] = WAIT_ACTION
            errors[0] = str(e)

        t1_start = time.perf_counter()
        try:
            act1 = self.agent1.choose_action(board, state, player=1, budget_seconds=0.8)
            timings[1] = time.perf_counter() - t1_start
            actions[1] = act1 if timings[1] <= limit_seconds else WAIT_ACTION
            if timings[1] > limit_seconds:
                errors[1] = f"Timeout ({timings[1]:.3f}s)"
        except Exception as e:
            timings[1] = time.perf_counter() - t1_start
            actions[1] = WAIT_ACTION
            errors[1] = str(e)

        return actions, timings, errors

    def close(self):
        """Dong runner, giai phong tai nguyen neu can."""
        pass
