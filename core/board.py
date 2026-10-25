from collections import deque
from typing import Dict, FrozenSet, List, Optional, Set, Tuple

from core.constants import ACTIONS, SINGLE_PLAYER_ACTIONS, WAIT_ACTION
from core.state import Coord, State


class Board:
    def __init__(
        self,
        width: int,
        height: int,
        walls: FrozenSet[Coord],
        floors: FrozenSet[Coord],
        goals: FrozenSet[Coord],
        initial: State,
        second_player: Optional[Coord] = None,
        name: str = "Map",
    ):
        self.width = width
        self.height = height
        self.walls = walls
        self.floors = floors
        self.goals = goals
        self.initial = initial
        self.second_player = second_player
        self.name = name

    @classmethod
    def from_text(cls, text: str, name: str = "Map") -> "Board":
        raw_lines = text.splitlines()

        while raw_lines and raw_lines[-1].strip() == "":
            raw_lines.pop()

        if not raw_lines:
            raise ValueError("Nội dung bản đồ không được để trống.")

        height = len(raw_lines)
        width = max(len(line) for line in raw_lines)

        grid: List[str] = [line.ljust(width) for line in raw_lines]

        walls_set: Set[Coord] = set()
        goals_set: Set[Coord] = set()
        boxes_set: Set[Coord] = set()
        player_a: Optional[Coord] = None
        player_z: Optional[Coord] = None
        all_non_wall_positions: Set[Coord] = set()

        for y in range(height):
            for x in range(width):
                char = grid[y][x]
                pos = (x, y)

                if char == '%':
                    walls_set.add(pos)
                else:
                    all_non_wall_positions.add(pos)
                    if char == 'A':
                        if player_a is not None:
                            raise ValueError("Phát hiện nhiều hơn một vị trí Agent A trên bản đồ.")
                        player_a = pos
                    elif char == 'Z':
                        if player_z is not None:
                            raise ValueError("Phát hiện nhiều hơn một vị trí Agent Z trên bản đồ.")
                        player_z = pos
                    elif char == 'B':
                        boxes_set.add(pos)
                    elif char == 'D':
                        goals_set.add(pos)
                    elif char == 'C':
                        boxes_set.add(pos)
                        goals_set.add(pos)
                    elif char == ' ':
                        pass
                    else:
                        raise ValueError(f"Ký hiệu lạ không xác định '{char}' tại tọa độ ({x}, {y}).")

        if player_a is None:
            raise ValueError("Bản đồ bắt buộc phải có đúng một Agent 'A'.")

        exterior: Set[Coord] = set()
        queue: deque = deque()

        for x in range(width):
            if (x, 0) in all_non_wall_positions:
                queue.append((x, 0))
                exterior.add((x, 0))
            if (x, height - 1) in all_non_wall_positions:
                queue.append((x, height - 1))
                exterior.add((x, height - 1))

        for y in range(height):
            if (0, y) in all_non_wall_positions and (0, y) not in exterior:
                queue.append((0, y))
                exterior.add((0, y))
            if (width - 1, y) in all_non_wall_positions and (width - 1, y) not in exterior:
                queue.append((width - 1, y))
                exterior.add((width - 1, y))

        while queue:
            cx, cy = queue.popleft()
            for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                nx, ny = cx + dx, cy + dy
                npos = (nx, ny)
                if 0 <= nx < width and 0 <= ny < height:
                    if npos in all_non_wall_positions and npos not in exterior:
                        exterior.add(npos)
                        queue.append(npos)

        floors_set = all_non_wall_positions - exterior

        if player_a not in floors_set:
            raise ValueError("Agent A nằm ngoài tường bao hoặc bản đồ bị hở (không khép kín).")
        if player_z is not None and player_z not in floors_set:
            raise ValueError("Agent Z nằm ngoài tường bao hoặc bản đồ bị hở.")
        for b in boxes_set:
            if b not in floors_set:
                raise ValueError(f"Hộp tại tọa độ {b} nằm ngoài tường bao.")
        for g in goals_set:
            if g not in floors_set:
                raise ValueError(f"Vị trí đích tại tọa độ {g} nằm ngoài tường bao.")

        if len(boxes_set) == 0:
            raise ValueError("Bản đồ phải có ít nhất một hộp.")
        if len(boxes_set) != len(goals_set):
            raise ValueError(
                f"Số lượng hộp ({len(boxes_set)}) phải bằng số lượng đích ({len(goals_set)})."
            )

        initial_state = State(player=player_a, boxes=tuple(boxes_set))

        return cls(
            width=width,
            height=height,
            walls=frozenset(walls_set),
            floors=frozenset(floors_set),
            goals=frozenset(goals_set),
            initial=initial_state,
            second_player=player_z,
            name=name,
        )

    @classmethod
    def from_file(cls, file_path: str, name: Optional[str] = None) -> "Board":
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        map_name = name or file_path.replace("\\", "/").split("/")[-1]
        return cls.from_text(content, name=map_name)

    def is_goal(self, state: State) -> bool:
        return frozenset(state.boxes) == self.goals

    def move(self, state: State, action: str) -> Optional[State]:
        if action not in SINGLE_PLAYER_ACTIONS:
            return None

        dx, dy = ACTIONS[action]
        px, py = state.player
        target = (px + dx, py + dy)

        if target not in self.floors:
            return None

        if target in state.boxes:
            box_target = (target[0] + dx, target[1] + dy)

            if box_target not in self.floors or box_target in state.boxes:
                return None

            new_boxes = tuple(b if b != target else box_target for b in state.boxes)
            return State(player=target, boxes=new_boxes)

        return State(player=target, boxes=state.boxes)

    def successors(self, state: State) -> List[Tuple[str, State]]:
        result = []
        for action in SINGLE_PLAYER_ACTIONS:
            next_state = self.move(state, action)
            if next_state is not None:
                result.append((action, next_state))
        return result

    def replay(self, actions: List[str]) -> List[State]:
        states = [self.initial]
        curr = self.initial
        for i, action in enumerate(actions):
            next_state = self.move(curr, action)
            if next_state is None:
                raise ValueError(f"Hành động '{action}' tại bước {i} không hợp lệ từ trạng thái {curr}.")
            states.append(next_state)
            curr = next_state
        return states

    def render(self, state: Optional[State] = None) -> str:
        st = state if state is not None else self.initial
        box_set = set(st.boxes)
        lines = []

        for y in range(self.height):
            row = []
            for x in range(self.width):
                pos = (x, y)
                if pos in self.walls:
                    row.append('%')
                elif pos == st.player:
                    row.append('A')
                elif pos in box_set and pos in self.goals:
                    row.append('C')
                elif pos in box_set:
                    row.append('B')
                elif pos in self.goals:
                    row.append('D')
                elif pos in self.floors:
                    row.append(' ')
                else:
                    row.append(' ')
            lines.append("".join(row).rstrip())
        return "\n".join(lines)
