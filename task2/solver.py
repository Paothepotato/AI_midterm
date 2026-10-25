from dataclasses import asdict, dataclass
import heapq
import time
from typing import Any, Dict, List, Optional

from core.board import Board
from core.heuristic import SokobanHeuristic, INF
from core.state import State


@dataclass
class SearchResult:
    algorithm: str
    status: str
    actions: List[str]
    cost: Optional[int]
    expanded: int
    generated: int
    peak_frontier: int
    discovered: int
    elapsed_seconds: float
    heuristic_cache_entries: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class SearchSolver:
    def __init__(self, board: Board, algorithm: str = 'astar', prune_deadlocks: bool = True):
        algo_lower = algorithm.lower().strip()
        if algo_lower not in ('ucs', 'astar'):
            raise ValueError(f"Thuật toán '{algorithm}' không hợp lệ. Chỉ chấp nhận 'ucs' hoặc 'astar'.")

        self.board = board
        self.algorithm = algo_lower
        self.prune_deadlocks = prune_deadlocks
        self.heuristic = SokobanHeuristic(board)

    def solve(
        self,
        timeout: float = 30.0,
        max_expanded: int = 500_000,
        cancel: Optional[Any] = None
    ) -> SearchResult:
        start_time = time.perf_counter()

        initial_state = self.board.initial

        if self.board.is_goal(initial_state):
            elapsed = time.perf_counter() - start_time
            return SearchResult(
                algorithm=self.algorithm,
                status='solved',
                actions=[],
                cost=0,
                expanded=0,
                generated=1,
                peak_frontier=1,
                discovered=1,
                elapsed_seconds=elapsed,
                heuristic_cache_entries=len(self.heuristic.h_cache),
            )

        if self.prune_deadlocks and self.heuristic.has_deadlock(initial_state.boxes):
            elapsed = time.perf_counter() - start_time
            return SearchResult(
                algorithm=self.algorithm,
                status='unsolvable',
                actions=[],
                cost=None,
                expanded=0,
                generated=1,
                peak_frontier=0,
                discovered=1,
                elapsed_seconds=elapsed,
                heuristic_cache_entries=len(self.heuristic.h_cache),
            )

        counter = 0
        h_init = 0 if self.algorithm == 'ucs' else self.heuristic.compute_h(initial_state)
        if h_init >= INF:
            elapsed = time.perf_counter() - start_time
            return SearchResult(
                algorithm=self.algorithm,
                status='unsolvable',
                actions=[],
                cost=None,
                expanded=0,
                generated=1,
                peak_frontier=0,
                discovered=1,
                elapsed_seconds=elapsed,
                heuristic_cache_entries=len(self.heuristic.h_cache),
            )

        init_pri = h_init if self.algorithm == 'astar' else 0
        frontier = [(init_pri, counter, 0, initial_state, [])]

        cost_so_far: Dict[State, int] = {initial_state: 0}

        expanded = 0
        generated = 1
        peak_frontier = 1
        status = 'unsolvable'
        solution_actions: List[str] = []
        solution_cost: Optional[int] = None

        while frontier:
            if cancel is not None and getattr(cancel, 'is_set', lambda: False)():
                status = 'cancelled'
                break

            elapsed_now = time.perf_counter() - start_time
            if elapsed_now >= timeout:
                status = 'timeout'
                break

            if expanded >= max_expanded:
                status = 'node_limit'
                break

            pri, _, g, curr_state, actions = heapq.heappop(frontier)

            if g > cost_so_far.get(curr_state, INF):
                continue

            expanded += 1

            if self.board.is_goal(curr_state):
                status = 'solved'
                solution_actions = actions
                solution_cost = len(actions)
                break

            for action_name, next_state in self.board.successors(curr_state):
                generated += 1

                if self.prune_deadlocks and self.heuristic.has_deadlock(next_state.boxes):
                    continue

                new_g = g + 1

                if next_state not in cost_so_far or new_g < cost_so_far[next_state]:
                    cost_so_far[next_state] = new_g

                    if self.algorithm == 'astar':
                        h_val = self.heuristic.compute_h(next_state)
                        if h_val >= INF:
                            continue
                        next_pri = new_g + h_val
                    else:
                        next_pri = new_g

                    counter += 1
                    heapq.heappush(
                        frontier,
                        (next_pri, counter, new_g, next_state, actions + [action_name])
                    )

            if len(frontier) > peak_frontier:
                peak_frontier = len(frontier)

        elapsed_total = time.perf_counter() - start_time
        return SearchResult(
            algorithm=self.algorithm,
            status=status,
            actions=solution_actions,
            cost=solution_cost,
            expanded=expanded,
            generated=generated,
            peak_frontier=peak_frontier,
            discovered=len(cost_so_far),
            elapsed_seconds=elapsed_total,
            heuristic_cache_entries=len(self.heuristic.h_cache),
        )
