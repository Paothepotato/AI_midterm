# board.py
# Quan ly cau truc ban choi, doc va kiem tra tinh hop le cua map

from typing import Set, Tuple, Optional, FrozenSet

class Board:
    """Luu tru thong tin tinh cua ban do Sokoban (tuong, san, dich, vi tri khoi tao)."""
    
    def __init__(self, filename: str):
        self.filename = filename
        self.name = filename.replace("\\", "/").split("/")[-1]
        
        # Tap hop cac o co dinh
        self.walls: FrozenSet[Tuple[int, int]] = frozenset()
        self.floors: FrozenSet[Tuple[int, int]] = frozenset()
        self.goals: FrozenSet[Tuple[int, int]] = frozenset()
        
        # Vi tri khoi tao
        self.initial_agent: Tuple[int, int] = (0, 0)
        self.second_player: Optional[Tuple[int, int]] = None
        self.initial_boxes: Tuple[Tuple[int, int], ...] = ()
        
        self.width: int = 0
        self.height: int = 0
        
        self._load_and_parse(filename)

    def _load_and_parse(self, filename: str):
        """Doc noi dung map tu file va trich xuat toa do cac phan tu."""
        with open(filename, "r", encoding="utf-8") as f:
            lines = [line.rstrip("\r\n") for line in f.readlines()]
            
        if not lines:
            raise ValueError("File map rong.")
            
        self.height = len(lines)
        self.width = max(len(line) for line in lines)
        
        # Chuan hoa do dai cac dong bang cach them khoang trang dem o cuoi
        padded_lines = [line.ljust(self.width, " ") for line in lines]
        
        raw_walls: Set[Tuple[int, int]] = set()
        raw_goals: Set[Tuple[int, int]] = set()
        raw_boxes: Set[Tuple[int, int]] = set()
        agent_positions = []
        second_positions = []
        all_cells: Set[Tuple[int, int]] = set()
        
        for y, line in enumerate(padded_lines):
            for x, char in enumerate(line):
                all_cells.add((x, y))
                if char == "%":
                    raw_walls.add((x, y))
                elif char == "A":
                    agent_positions.append((x, y))
                elif char == "Z":
                    second_positions.append((x, y))
                elif char == "B":
                    raw_boxes.add((x, y))
                elif char == "D":
                    raw_goals.add((x, y))
                elif char == "C":
                    raw_boxes.add((x, y))
                    raw_goals.add((x, y))
                elif char == " ":
                    pass
                else:
                    raise ValueError(f"Ky tu khong hop le trong map: '{char}' tai ({x}, {y})")

        # Kiem tra so luong agent hop le
        if len(agent_positions) != 1:
            raise ValueError(f"Map phai co dung 1 agent A, hien co: {len(agent_positions)}")
        if len(second_positions) > 1:
            raise ValueError(f"Map co toi da 1 agent Z, hien co: {len(second_positions)}")
            
        self.initial_agent = agent_positions[0]
        self.second_player = second_positions[0] if second_positions else None
        
        # Kiem tra so luong hop va dich
        if len(raw_boxes) == 0:
            raise ValueError("Map phai co it nhat 1 hop.")
        if len(raw_boxes) != len(raw_goals):
            raise ValueError(f"So luong hop ({len(raw_boxes)}) khong bang so dich ({len(raw_goals)}).")

        # Xac dinh phan dem ngoai map bang BFS tu vien ngoai cung (chi di qua khoang trang)
        outside: Set[Tuple[int, int]] = set()
        queue = []
        for x in range(self.width):
            for y in (0, self.height - 1):
                if padded_lines[y][x] == " ":
                    outside.add((x, y))
                    queue.append((x, y))
        for y in range(self.height):
            for x in (0, self.width - 1):
                if padded_lines[y][x] == " " and (x, y) not in outside:
                    outside.add((x, y))
                    queue.append((x, y))
                    
        while queue:
            cx, cy = queue.pop(0)
            for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                nx, ny = cx + dx, cy + dy
                if 0 <= nx < self.width and 0 <= ny < self.height:
                    if (nx, ny) not in outside and padded_lines[ny][nx] == " ":
                        outside.add((nx, ny))
                        queue.append((nx, ny))

        # O san (floors) la cac o ben trong khung tuong (khong thuoc outside va khong phai tuong)
        raw_floors = (all_cells - outside) - raw_walls
        
        # Cac vi tri agent, box, goal phai nam trong vung san di chuyen duoc
        for box in raw_boxes:
            if box not in raw_floors:
                raise ValueError(f"Hop tai {box} nam ngoai vung choi.")
        for goal in raw_goals:
            if goal not in raw_floors:
                raise ValueError(f"Dich tai {goal} nam ngoai vung choi.")
        if self.initial_agent not in raw_floors:
            raise ValueError(f"Agent A tai {self.initial_agent} nam ngoai vung choi.")
        if self.second_player and self.second_player not in raw_floors:
            raise ValueError(f"Agent Z tai {self.second_player} nam ngoai vung choi.")

        self.walls = frozenset(raw_walls)
        self.floors = frozenset(raw_floors)
        self.goals = frozenset(raw_goals)
        self.initial_boxes = tuple(sorted(raw_boxes, key=lambda p: (p[0], p[1])))
