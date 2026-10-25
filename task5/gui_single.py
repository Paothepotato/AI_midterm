import os
import sys
import pygame
from typing import List, Optional

# Dam bao import duoc core va task2 du chay tu thu muc goc hay tu task5/
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.board import Board
from core.state import State
from core.gui_theme import (
    COLOR_BG, COLOR_HUD_BG, COLOR_HUD_LINE, COLOR_TEXT, COLOR_TEXT_MUTED,
    COLOR_ACCENT, COLOR_BOX_NEUTRAL, COLOR_BOX_GOAL, COLOR_AGENT_SINGLE,
    get_system_font, draw_floor, draw_wall, draw_box, draw_agent
)
from task2.solver import SearchSolver, SearchResult


def resolve_map_path(map_name_or_path: str) -> str:
    # Tim file ban do theo ca duong dan tuong doi va thu muc maps/
    candidates = [
        map_name_or_path,
        os.path.join(PROJECT_ROOT, map_name_or_path),
        os.path.join(PROJECT_ROOT, "maps", os.path.basename(map_name_or_path)),
        os.path.join(CURRENT_DIR, "..", "maps", os.path.basename(map_name_or_path))
    ]
    for c in candidates:
        if os.path.isfile(c):
            return os.path.abspath(c)
    return map_name_or_path


class SinglePlayerGUI:
    """Giao dien do hoa Pygame cho tro choi Sokoban che do mot nguoi."""

    def __init__(self, map_path: str = "maps/example_simple.txt", default_algo: str = "astar"):
        pygame.init()
        pygame.display.set_caption("Sokoban AI - Single Player (UCS & A*)")

        self.map_file = resolve_map_path(map_path)
        if not os.path.isfile(self.map_file):
            raise FileNotFoundError(f"Khong tim thay file ban do: {self.map_file}")

        self.board = Board.from_file(self.map_file)
        self.algorithm = default_algo.lower()
        if self.algorithm not in ("ucs", "astar"):
            self.algorithm = "astar"

        # Tinh toan kich thuoc cua so
        self.cell_size = 48
        self.hud_height = 130
        self.grid_width = self.board.width * self.cell_size
        self.grid_height = self.board.height * self.cell_size
        self.screen_width = max(self.grid_width, 720)
        self.screen_height = self.grid_height + self.hud_height

        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        self.clock = pygame.time.Clock()

        # Khoi tao phong chu da nen tang
        self.font_main = get_system_font(18, bold=True)
        self.font_sub = get_system_font(14)
        self.font_title = get_system_font(20, bold=True)

        # Trang thai giai va dieu khien
        self.solution_res: Optional[SearchResult] = None
        self.history_states: List[State] = [self.board.initial]
        self.actions_list: List[str] = []
        self.current_idx = 0

        self.is_paused = True
        self.step_delay_ms = 400
        self.last_step_time = pygame.time.get_ticks()

        # Giai tim duong ban dau
        self._solve()

    def _solve(self):
        # Chay thuat toan duoc chon (UCS hoac A*)
        solver = SearchSolver(self.board, algorithm=self.algorithm, prune_deadlocks=True)
        self.solution_res = solver.solve(timeout=30.0)

        if self.solution_res.status == "solved":
            self.actions_list = self.solution_res.actions
            self.history_states = self.board.replay(self.actions_list)
        else:
            self.actions_list = []
            self.history_states = [self.board.initial]

        self.current_idx = 0
        self.is_paused = True

    def switch_algorithm(self, new_algo: str):
        if new_algo != self.algorithm:
            self.algorithm = new_algo
            self._solve()

    def _step_forward(self):
        if self.current_idx < len(self.history_states) - 1:
            self.current_idx += 1
        else:
            self.is_paused = True

    def _step_backward(self):
        if self.current_idx > 0:
            self.current_idx -= 1

    def _draw_hud(self):
        hud_rect = pygame.Rect(0, 0, self.screen_width, self.hud_height)
        pygame.draw.rect(self.screen, COLOR_HUD_BG, hud_rect)
        pygame.draw.line(self.screen, COLOR_HUD_LINE, (0, self.hud_height), (self.screen_width, self.hud_height), 2)

        algo_name = "A* (Hungarian BFS)" if self.algorithm == "astar" else "UCS (Uniform Cost Search)"
        status_txt = "PAUSED" if self.is_paused else "PLAYING"
        is_solved = self.solution_res and self.solution_res.status == "solved"

        cur_state = self.history_states[self.current_idx]
        is_at_goal = self.board.is_goal(cur_state)
        goal_status = "HOAN THANH GOAL" if is_at_goal else "DANG DI CHUYEN"

        # Dong 1: Thuat toan va trang thai chay
        title_surf = self.font_title.render(f"Thuat toan: {algo_name}", True, COLOR_ACCENT)
        self.screen.blit(title_surf, (20, 10))

        state_color = (100, 220, 100) if not self.is_paused else (240, 180, 80)
        mode_surf = self.font_main.render(f"[{status_txt}] - {goal_status}", True, state_color)
        self.screen.blit(mode_surf, (self.screen_width - 270, 12))

        # Dong 2: So hanh dong / cost va thong so tim kiem
        total_actions = len(self.actions_list)
        time_ms = self.solution_res.elapsed_seconds * 1000 if self.solution_res else 0.0
        expanded = self.solution_res.expanded if self.solution_res else 0

        info_1 = f"Hanh dong: Buoc {self.current_idx} / {total_actions} (Tong chi phi cost: {total_actions})"
        info_2 = f"Thoi gian giai: {time_ms:.1f}ms | So node mo rong: {expanded}"
        self.screen.blit(self.font_main.render(info_1, True, COLOR_TEXT), (20, 42))
        self.screen.blit(self.font_sub.render(info_2, True, COLOR_TEXT_MUTED), (20, 70))

        # Dong 3: Huong dan phim bam
        controls_text = "Phim: [Space] Pause/Play | [->] Tien | [<-] Lui | [1]/[U] UCS | [2]/[A] A* | [R] Reset"
        self.screen.blit(self.font_sub.render(controls_text, True, (180, 185, 195)), (20, 98))

    def _draw_board(self):
        offset_x = (self.screen_width - self.grid_width) // 2
        offset_y = self.hud_height

        cur_state = self.history_states[self.current_idx]
        boxes_set = set(cur_state.boxes)

        for y in range(self.board.height):
            for x in range(self.board.width):
                pos = (x, y)
                px = offset_x + x * self.cell_size
                py = offset_y + y * self.cell_size
                rect = pygame.Rect(px, py, self.cell_size, self.cell_size)

                # Ve tuong
                if pos in self.board.walls:
                    draw_wall(self.screen, rect)
                    continue

                # Ve san va diem dich
                if pos in self.board.floors:
                    is_goal = pos in self.board.goals
                    draw_floor(self.screen, rect, is_goal=is_goal)

                    # Ve hop: doi mau neu da vao diem dich
                    if pos in boxes_set:
                        box_color = COLOR_BOX_GOAL if is_goal else COLOR_BOX_NEUTRAL
                        draw_box(self.screen, rect, box_color)

                    # Ve Agent 1 nguoi
                    if pos == cur_state.player:
                        center = rect.center
                        radius = self.cell_size // 3
                        draw_agent(self.screen, center, radius, COLOR_AGENT_SINGLE, "A", self.font_sub)

    def run(self):
        running = True
        while running:
            now = pygame.time.get_ticks()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        self.is_paused = not self.is_paused
                    elif event.key == pygame.K_RIGHT:
                        self.is_paused = True
                        self._step_forward()
                    elif event.key == pygame.K_LEFT:
                        self.is_paused = True
                        self._step_backward()
                    elif event.key in (pygame.K_1, pygame.K_u):
                        self.switch_algorithm("ucs")
                    elif event.key in (pygame.K_2, pygame.K_a):
                        self.switch_algorithm("astar")
                    elif event.key == pygame.K_r:
                        self.current_idx = 0
                        self.is_paused = True
                    elif event.key == pygame.K_ESCAPE:
                        running = False

            if not self.is_paused and now - self.last_step_time >= self.step_delay_ms:
                self.last_step_time = now
                self._step_forward()

            self.screen.fill(COLOR_BG)
            self._draw_hud()
            self._draw_board()
            pygame.display.flip()
            self.clock.tick(30)

        pygame.quit()


if __name__ == "__main__":
    map_target = "maps/example_simple.txt"
    algo_target = "astar"

    if len(sys.argv) > 1:
        map_target = sys.argv[1]
    if len(sys.argv) > 2:
        algo_target = sys.argv[2]

    print(f"Khoi dong Sokoban Single Player GUI:")
    print(f" - Ban do   : {map_target}")
    print(f" - Thuat toan: {algo_target.upper()}")
    app = SinglePlayerGUI(map_path=map_target, default_algo=algo_target)
    app.run()
