# competitive.py
# Quan ly trang thai va quy tac thi dau doi khang hai agent

from typing import Tuple, List, Optional, Dict
from dataclasses import dataclass
from board import Board

# Cac vecto huong di chuyen tuong ung voi ten hanh dong chuan
ACTIONS_DIR: Dict[str, Tuple[int, int]] = {
    "North": (0, -1),
    "East": (1, 0),
    "West": (-1, 0),
    "South": (0, 1),
    "Wait": (0, 0),
}

@dataclass(frozen=True)
class CompetitiveState:
    """Trang thai bat bien cua tran thi dau giua 2 agent."""
    players: Tuple[Tuple[int, int], Tuple[int, int]]  # Vi tri (agent_0, agent_1)
    boxes: Tuple[Tuple[int, int], ...]                # Toa do hop da sap xep
    owners: Tuple[int, ...]                           # Chu so huu tuong ung cua tung hop (-1, 0, 1)
    turn: int                                         # So luot da qua (bat dau tu 0)

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
    """Quan ly luat thi dau va chuyen doi trang thai dong thoi giua 2 agent."""
    
    def __init__(self, board: Board, limit_steps: int):
        if board.second_player is None:
            raise ValueError("Map thi dau bat buoc phai co agent Z (player 1).")
        if limit_steps <= 0:
            raise ValueError("So luot thi dau n phai la so nguyen duong.")
            
        self.board = board
        self.limit_steps = limit_steps
        
        # Khoi tao trang thai ban dau
        initial_owners = tuple(-1 for _ in range(len(board.initial_boxes)))
        self.initial_state = CompetitiveState(
            players=(board.initial_agent, board.second_player),
            boxes=board.initial_boxes,
            owners=initial_owners,
            turn=0
        )

    def get_scores(self, state: CompetitiveState) -> Tuple[int, int]:
        """Tinh diem so hien tai: so hop tren dich thuoc so huu cua tung agent."""
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
        """Kiem tra tran dau da ket thuc chua (khi turn >= n)."""
        return state.turn >= self.limit_steps

    def get_winner(self, state: CompetitiveState) -> Optional[int]:
        """Xac dinh nguoi chien thang: tra ve 0, 1 hoac None neu hoa."""
        s0, s1 = self.get_scores(state)
        if s0 > s1:
            return 0
        if s1 > s0:
            return 1
        return None

    def step(self, state: CompetitiveState, actions: List[str]) -> CompetitiveState:
        """Thuc hien mot luot choi dong thoi cho ca 2 agent voi co che giai quyet xung dot."""
        if len(actions) != 2:
            raise ValueError(f"Yeu cau dung 2 actions cho 2 agent, nhan duoc: {len(actions)}")
            
        # Neu da het so luot thi giu nguyen trang thai
        if state.turn >= self.limit_steps:
            return state

        p0, p1 = state.players
        boxes_set = set(state.boxes)
        box_to_owner = dict(zip(state.boxes, state.owners))

        # Y dinh di chuyen doc lap cua tung ben: (is_valid, new_player_pos, pushed_box_from, pushed_box_to)
        intentions = []
        for i, act in enumerate(actions):
            if act not in ACTIONS_DIR or act == "Wait":
                intentions.append((True, state.players[i], None, None))
                continue
                
            dx, dy = ACTIONS_DIR[act]
            cur_p = state.players[i]
            target_p = (cur_p[0] + dx, cur_p[1] + dy)
            
            # O dich khong thuoc san di chuyen duoc
            if target_p not in self.board.floors:
                intentions.append((False, cur_p, None, None))
                continue
                
            # Truong hop day hop
            if target_p in boxes_set:
                target_box = (target_p[0] + dx, target_p[1] + dy)
                # Box khong the day ra ngoai san hoac de len hop khac
                if target_box not in self.board.floors or target_box in boxes_set:
                    intentions.append((False, cur_p, None, None))
                else:
                    intentions.append((True, target_p, target_p, target_box))
            else:
                # Di chuyen vao o trong
                intentions.append((True, target_p, None, None))

        v0, target_p0, push_from0, push_to0 = intentions[0]
        v1, target_p1, push_from1, push_to1 = intentions[1]

        # Kiem tra quy tac can tro voi vi tri hien tai cua doi thu
        if v0 and target_p0 == p1:
            v0 = False
        if v1 and target_p1 == p0:
            v1 = False
        if v0 and push_to0 == p1:
            v0 = False
        if v1 and push_to1 == p0:
            v1 = False

        # Kiem tra xung dot dong thoi giua 2 ben khi ca hai deu co y dinh di chuyen
        if v0 and v1:
            conflict = False
            # Hai agent cung di vao mot o
            if target_p0 == target_p1:
                conflict = True
            # Hai agent doi cho / di xuyen qua nhau
            elif target_p0 == p1 and target_p1 == p0:
                conflict = True
            # Hai agent cung day chung mot hop
            elif push_from0 is not None and push_from0 == push_from1:
                conflict = True
            # O den cua hop ben nay trung o den cua agent ben kia
            elif push_to0 is not None and push_to0 == target_p1:
                conflict = True
            elif push_to1 is not None and push_to1 == target_p0:
                conflict = True
            # Hai hop duoc day den cung mot o
            elif push_to0 is not None and push_to0 == push_to1:
                conflict = True

            if conflict:
                v0 = False
                v1 = False

        # Ap dung cac y dinh con hop le
        final_p0 = target_p0 if v0 else p0
        final_p1 = target_p1 if v1 else p1

        # Cap nhat vi tri hop va quyen so huu (owners)
        new_box_to_owner = dict(box_to_owner)
        
        if v0 and push_from0 is not None:
            old_owner = new_box_to_owner.pop(push_from0)
            # Day len dich thi tinh diem cho agent 0, ra khoi dich thi mat diem (-1)
            new_owner = 0 if push_to0 in self.board.goals else -1
            new_box_to_owner[push_to0] = new_owner

        if v1 and push_from1 is not None:
            old_owner = new_box_to_owner.pop(push_from1)
            # Day len dich thi tinh diem cho agent 1, ra khoi dich thi mat diem (-1)
            new_owner = 1 if push_to1 in self.board.goals else -1
            new_box_to_owner[push_to1] = new_owner

        # Chuan hoa sap xep toa do hop va owners tuong ung
        sorted_boxes_with_owner = sorted(new_box_to_owner.items(), key=lambda item: (item[0][0], item[0][1]))
        final_boxes = tuple(item[0] for item in sorted_boxes_with_owner)
        final_owners = tuple(item[1] for item in sorted_boxes_with_owner)

        return CompetitiveState(
            players=(final_p0, final_p1),
            boxes=final_boxes,
            owners=final_owners,
            turn=state.turn + 1
        )
