# runner.py
# Bo dieu phoi thoi gian va quan ly quyet dinh dong thoi giua 2 agent

import time
from typing import Tuple, List, Optional
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from board import Board
from competitive import CompetitiveState, ACTIONS_DIR
import agent_0
import agent_1

class DecisionRunner:
    """Dieu phoi thuc thi 2 agent song song, kiem soat thoi gian cung limit_seconds=1.0s."""

    def __init__(self):
        # Su dung pool de goi 2 agent dong thoi
        self._executor = ThreadPoolExecutor(max_workers=2)

    def _call_agent(self, agent_func, board: Board, state: CompetitiveState, player: int, budget: float):
        """Goi ham choose_action cua agent va tra ve ket qua cung thoi gian thuc thi."""
        t_start = time.perf_counter()
        try:
            act = agent_func(board, state, player=player, budget_seconds=budget)
            elapsed = time.perf_counter() - t_start
            return act, elapsed, None
        except Exception as e:
            elapsed = time.perf_counter() - t_start
            return "Wait", elapsed, str(e)

    def decide(self, board: Board, state: CompetitiveState, limit_seconds: float = 1.0) -> Tuple[List[str], List[float], List[Optional[str]]]:
        """Thu thap hanh dong tu 2 agent voi thoi gian toi da limit_seconds."""
        budget = max(0.1, limit_seconds - 0.2)
        
        # Gui yeu cau den ca 2 agent dong thoi
        future_0 = self._executor.submit(self._call_agent, agent_0.choose_action, board, state, 0, budget)
        future_1 = self._executor.submit(self._call_agent, agent_1.choose_action, board, state, 1, budget)

        actions = ["Wait", "Wait"]
        timings = [0.0, 0.0]
        errors = [None, None]

        # Thu nhap ket qua Agent 0
        try:
            act0, t0, err0 = future_0.result(timeout=limit_seconds)
            timings[0] = round(t0, 4)
            if err0 is not None:
                errors[0] = f"Loi Agent 0: {err0}"
                actions[0] = "Wait"
            elif act0 not in ACTIONS_DIR:
                errors[0] = f"Hanh dong khong hop le tu Agent 0: '{act0}'"
                actions[0] = "Wait"
            else:
                actions[0] = act0
        except FuturesTimeoutError:
            timings[0] = limit_seconds
            errors[0] = "Agent 0 qua han thoi gian (Timeout > 1.0s)"
            actions[0] = "Wait"

        # Thu nhap ket qua Agent 1
        try:
            act1, t1, err1 = future_1.result(timeout=limit_seconds)
            timings[1] = round(t1, 4)
            if err1 is not None:
                errors[1] = f"Loi Agent 1: {err1}"
                actions[1] = "Wait"
            elif act1 not in ACTIONS_DIR:
                errors[1] = f"Hanh dong khong hop le tu Agent 1: '{act1}'"
                actions[1] = "Wait"
            else:
                actions[1] = act1
        except FuturesTimeoutError:
            timings[1] = limit_seconds
            errors[1] = "Agent 1 qua han thoi gian (Timeout > 1.0s)"
            actions[1] = "Wait"

        return actions, timings, errors

    def close(self):
        """Dong executor khi tran dau ket thuc."""
        self._executor.shutdown(wait=False)
