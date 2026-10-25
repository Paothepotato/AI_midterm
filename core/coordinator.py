from collections import deque
from typing import Dict, List, Optional, Set, Tuple

from core.board import Board
from core.constants import ACTIONS, WAIT_ACTION
from core.state import CompetitiveState, Coord


class MultiAgentCoordinator:
    def __init__(self, history_len: int = 8):
        self.history_len = history_len
        self.state_history: List[Tuple[Coord, Coord, Tuple[Coord, ...], Tuple[int, int]]] = []
        self.action_history: Dict[int, List[str]] = {0: [], 1: []}

    def record_turn(self, state: CompetitiveState, actions: List[str]):
        snapshot = (state.players[0], state.players[1], state.boxes, state.get_score())
        self.state_history.append(snapshot)
        if len(self.state_history) > self.history_len:
            self.state_history.pop(0)

        for p_id in (0, 1):
            if p_id < len(actions):
                self.action_history[p_id].append(actions[p_id])
                if len(self.action_history[p_id]) > self.history_len:
                    self.action_history[p_id].pop(0)

    def is_in_cycle(self, player_id: int) -> bool:
        if len(self.state_history) < 4:
            return False

        scores = [snap[3] for snap in self.state_history[-4:]]
        if len(set(scores)) > 1:
            return False

        agent_positions = [snap[player_id] for snap in self.state_history[-4:]]
        if agent_positions[0] == agent_positions[2] and agent_positions[1] == agent_positions[3]:
            return True

        acts = self.action_history[player_id][-4:]
        if len(acts) == 4:
            opposites = {('North', 'South'), ('South', 'North'), ('East', 'West'), ('West', 'East')}
            if (acts[-1], acts[-2]) in opposites and (acts[-3], acts[-4]) in opposites:
                return True

        return False

    def is_chokepoint_corridor(self, board: Board, pos: Coord) -> bool:
        x, y = pos
        north_wall = (x, y - 1) not in board.floors
        south_wall = (x, y + 1) not in board.floors
        west_wall = (x - 1, y) not in board.floors
        east_wall = (x + 1, y) not in board.floors

        is_h_corridor = north_wall and south_wall and ((x - 1, y) in board.floors) and ((x + 1, y) in board.floors)
        is_v_corridor = west_wall and east_wall and ((x, y - 1) in board.floors) and ((x, y + 1) in board.floors)
        return is_h_corridor or is_v_corridor

    def resolve_head_on_conflict(
        self,
        board: Board,
        my_pos: Coord,
        opp_pos: Coord,
        desired_action: str,
        player_id: int
    ) -> Optional[str]:
        dx, dy = ACTIONS.get(desired_action, (0, 0))
        target_cell = (my_pos[0] + dx, my_pos[1] + dy)

        if target_cell == opp_pos:
            return None

        if self.is_chokepoint_corridor(board, my_pos) and self.is_chokepoint_corridor(board, opp_pos):
            if player_id == 1:
                for act_name, (adx, ady) in ACTIONS.items():
                    side_cell = (my_pos[0] + adx, my_pos[1] + ady)
                    if side_cell in board.floors and not self.is_chokepoint_corridor(board, side_cell):
                        return act_name

        return desired_action
