from typing import Tuple, List, Optional, Dict
from dataclasses import dataclass
from board import Board

ACTIONS_DIR: Dict[str, Tuple[int, int]] = {
    "North": (0, -1),
    "East": (1, 0),
    "West": (-1, 0),
    "South": (0, 1),
    "Wait": (0, 0),
}

@dataclass(frozen=True)
class CompetitiveState:
    players: Tuple[Tuple[int, int], Tuple[int, int]]  
    boxes: Tuple[Tuple[int, int], ...]              
    owners: Tuple[int, ...]                           
    turn: int                                       

    def __hash__(self):
        return hash((self.players, self.boxes, self.owners, self.turn))

    def __eq__(self, other):
        if not isinstance(other, CompetitiveState):
            return False
        return (self.players == other.players and 
                self.boxes == other.boxes and 
                self.owners == other.owners and 
                self.turn == other.turn)


class Competition:
    
    def __init__(self, board: Board, limit_steps: int):
        if board.second_player is None:
            raise ValueError("Map thi dau bat buoc phai co agent Z (player 1).")
        if limit_steps <= 0:
            raise ValueError("So luot thi dau n phai la so nguyen duong.")
            
        self.board = board
        self.limit_steps = limit_steps
        
        initial_owners = tuple(-1 for _ in range(len(board.initial_boxes)))
        self.initial_state = CompetitiveState(
            players=(board.initial_agent, board.second_player),
            boxes=board.initial_boxes,
            owners=initial_owners,
            turn=0
        )

    def get_scores(self, state: CompetitiveState) -> Tuple[int, int]:
        score_0 = 0
        score_1 = 0
        for box, owner in zip(state.boxes, state.owners):
            if box in self.board.goals:
                if owner == 0:
                    score_0 += 1
                elif owner == 1:
                    score_1 += 1
        return score_0, score_1

    def is_terminal(self, state: CompetitiveState) -> bool:
        return state.turn >= self.limit_steps

    def get_winner(self, state: CompetitiveState) -> Optional[int]:
        s0, s1 = self.get_scores(state)
        if s0 > s1:
            return 0
        if s1 > s0:
            return 1
        return None

    def step(self, state: CompetitiveState, actions: List[str]) -> CompetitiveState:
        if len(actions) != 2:
            raise ValueError(f"Yeu cau dung 2 actions cho 2 agent, nhan duoc: {len(actions)}")
            
        if state.turn >= self.limit_steps:
            return state

        p0, p1 = state.players
        boxes_set = set(state.boxes)
        box_to_owner = dict(zip(state.boxes, state.owners))

        intentions = []
        for i, act in enumerate(actions):
            if act not in ACTIONS_DIR or act == "Wait":
                intentions.append((True, state.players[i], None, None))
                continue
                
            dx, dy = ACTIONS_DIR[act]
            cur_p = state.players[i]
            target_p = (cur_p[0] + dx, cur_p[1] + dy)
            
            if target_p not in self.board.floors:
                intentions.append((False, cur_p, None, None))
                continue
                
            if target_p in boxes_set:
                target_box = (target_p[0] + dx, target_p[1] + dy)
                if target_box not in self.board.floors or target_box in boxes_set:
                    intentions.append((False, cur_p, None, None))
                else:
                    intentions.append((True, target_p, target_p, target_box))
            else:
                intentions.append((True, target_p, None, None))

        v0, target_p0, push_from0, push_to0 = intentions[0]
        v1, target_p1, push_from1, push_to1 = intentions[1]

        if v0 and target_p0 == p1:
            v0 = False
        if v1 and target_p1 == p0:
            v1 = False
        if v0 and push_to0 == p1:
            v0 = False
        if v1 and push_to1 == p0:
            v1 = False

        if v0 and v1:
            conflict = False
            if target_p0 == target_p1:
                conflict = True
            elif target_p0 == p1 and target_p1 == p0:
                conflict = True
            elif push_from0 is not None and push_from0 == push_from1:
                conflict = True
            elif push_to0 is not None and push_to0 == target_p1:
                conflict = True
            elif push_to1 is not None and push_to1 == target_p0:
                conflict = True
            elif push_to0 is not None and push_to0 == push_to1:
                conflict = True

            if conflict:
                v0 = False
                v1 = False

        final_p0 = target_p0 if v0 else p0
        final_p1 = target_p1 if v1 else p1

        new_box_to_owner = dict(box_to_owner)
        
        if v0 and push_from0 is not None:
            old_owner = new_box_to_owner.pop(push_from0)
            new_owner = 0 if push_to0 in self.board.goals else -1
            new_box_to_owner[push_to0] = new_owner

        if v1 and push_from1 is not None:
            old_owner = new_box_to_owner.pop(push_from1)
            new_owner = 1 if push_to1 in self.board.goals else -1
            new_box_to_owner[push_to1] = new_owner

        sorted_boxes_with_owner = sorted(new_box_to_owner.items(), key=lambda item: (item[0][0], item[0][1]))
        final_boxes = tuple(item[0] for item in sorted_boxes_with_owner)
        final_owners = tuple(item[1] for item in sorted_boxes_with_owner)

        return CompetitiveState(
            players=(final_p0, final_p1),
            boxes=final_boxes,
            owners=final_owners,
            turn=state.turn + 1
        )
