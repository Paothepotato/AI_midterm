import random
from typing import List, Optional, Tuple, Set

from core.board import Board
from core.constants import ACTIONS, WAIT_ACTION
from core.state import CompetitiveState, Coord


class Competition:
    def __init__(self, board: Board, limit: int = 50):
        if board.second_player is None:
            raise ValueError("Chế độ thi đấu bắt buộc bản đồ phải có Agent thứ hai ('Z').")
        self.board = board
        self.limit = int(limit)

    def create_initial_state(self) -> CompetitiveState:
        players = (self.board.initial.player, self.board.second_player)
        boxes_with_owners = tuple((b, -1) for b in self.board.initial.boxes)
        return CompetitiveState(players=players, boxes_with_owners=boxes_with_owners, turn=0)

    def is_game_over(self, state: CompetitiveState) -> bool:
        return state.turn >= self.limit

    def get_winner(self, state: CompetitiveState) -> Optional[int]:
        s0, s1 = state.get_score()
        if s0 > s1:
            return 0
        elif s1 > s0:
            return 1
        return None

    def step(self, state: CompetitiveState, actions: List[str]) -> CompetitiveState:
        if len(actions) != 2:
            raise ValueError(f"Competition.step yêu cầu chính xác 2 hành động, nhưng nhận được {len(actions)}")

        if state.turn >= self.limit:
            return state

        p0, p1 = state.players
        act0, act1 = actions[0], actions[1]

        intent0 = self._evaluate_single_intent(p0, act0, state, opponent_pos=p1)
        intent1 = self._evaluate_single_intent(p1, act1, state, opponent_pos=p0)

        if intent0['valid'] and intent1['valid']:
            same_pos = (intent0['new_p'] == intent1['new_p'])
            same_box = (intent0['push'] and intent1['push'] and intent0['box_from'] == intent1['box_from'])

            if same_pos or same_box:
                p = random.random()
                if p < 0.5:
                    intent1['valid'] = False
                else:
                    intent0['valid'] = False

            if intent0['valid'] and intent1['valid']:
                conflict = False
                if intent0['new_p'] == p1 and intent1['new_p'] == p0:
                    conflict = True
                if intent0['push'] and intent0['box_to'] == intent1['new_p']:
                    conflict = True
                if intent1['push'] and intent1['box_to'] == intent0['new_p']:
                    conflict = True
                if intent0['push'] and intent1['push'] and intent0['box_to'] == intent1['box_to']:
                    conflict = True
                if conflict:
                    intent0['valid'] = False
                    intent1['valid'] = False

        new_p0 = intent0['new_p'] if intent0['valid'] else p0
        new_p1 = intent1['new_p'] if intent1['valid'] else p1

        box_owner_map = {b: o for b, o in zip(state.boxes, state.owners)}

        if intent0['valid'] and intent0['push']:
            b_from, b_to = intent0['box_from'], intent0['box_to']
            del box_owner_map[b_from]

            new_owner = 0 if b_to in self.board.goals else -1
            box_owner_map[b_to] = new_owner

        if intent1['valid'] and intent1['push']:
            b_from, b_to = intent1['box_from'], intent1['box_to']
            del box_owner_map[b_from]
            new_owner = 1 if b_to in self.board.goals else -1
            box_owner_map[b_to] = new_owner

        new_boxes_with_owners = tuple(box_owner_map.items())

        return CompetitiveState(
            players=(new_p0, new_p1),
            boxes_with_owners=new_boxes_with_owners,
            turn=state.turn + 1
        )

    def _evaluate_single_intent(
        self,
        player_pos: Coord,
        action: str,
        state: CompetitiveState,
        opponent_pos: Coord
    ) -> dict:
        if action not in ACTIONS:
            return {'valid': False, 'new_p': player_pos, 'push': False}

        dx, dy = ACTIONS[action]
        target = (player_pos[0] + dx, player_pos[1] + dy)

        if target not in self.board.floors:
            return {'valid': False, 'new_p': player_pos, 'push': False}

        if target == opponent_pos:
            return {'valid': False, 'new_p': player_pos, 'push': False}

        if target in state.boxes:
            box_target = (target[0] + dx, target[1] + dy)

            if (box_target not in self.board.floors or
                box_target in state.boxes or
                box_target == opponent_pos):
                return {'valid': False, 'new_p': player_pos, 'push': False}

            return {
                'valid': True,
                'new_p': target,
                'push': True,
                'box_from': target,
                'box_to': box_target
            }

        return {'valid': True, 'new_p': target, 'push': False}
