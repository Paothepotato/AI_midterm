from dataclasses import dataclass
from typing import Tuple

Coord = Tuple[int, int]


@dataclass(frozen=True)
class State:
    player: Coord
    boxes: Tuple[Coord, ...]

    def __init__(self, player: Coord, boxes: Tuple[Coord, ...]):
        object.__setattr__(self, 'player', (int(player[0]), int(player[1])))

        sorted_boxes = tuple(sorted((int(x), int(y)) for x, y in boxes))
        object.__setattr__(self, 'boxes', sorted_boxes)

    def __repr__(self) -> str:
        return f"State(player={self.player}, boxes={self.boxes})"


@dataclass(frozen=True)
class CompetitiveState:
    players: Tuple[Coord, Coord]
    boxes: Tuple[Coord, ...]
    owners: Tuple[int, ...]
    turn: int

    def __init__(
        self,
        players: Tuple[Coord, Coord],
        boxes_with_owners: Tuple[Tuple[Coord, int], ...],
        turn: int = 0
    ):
        p0 = (int(players[0][0]), int(players[0][1]))
        p1 = (int(players[1][0]), int(players[1][1]))
        object.__setattr__(self, 'players', (p0, p1))
        object.__setattr__(self, 'turn', int(turn))

        sorted_pairs = sorted(boxes_with_owners, key=lambda pair: (pair[0][0], pair[0][1]))
        sorted_boxes = tuple((pair[0][0], pair[0][1]) for pair in sorted_pairs)
        sorted_owners = tuple(pair[1] for pair in sorted_pairs)

        object.__setattr__(self, 'boxes', sorted_boxes)
        object.__setattr__(self, 'owners', sorted_owners)

    def get_score(self) -> Tuple[int, int]:
        s0 = sum(1 for o in self.owners if o == 0)
        s1 = sum(1 for o in self.owners if o == 1)
        return s0, s1

    def __repr__(self) -> str:
        return (
            f"CompetitiveState(players={self.players}, "
            f"boxes={self.boxes}, owners={self.owners}, turn={self.turn})"
        )
