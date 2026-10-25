import os
import sys
import pygame
from typing import List, Optional, Tuple

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


def discover_single_player_maps() -> List[Tuple[str, str]]:
    maps_dir = os.path.join(PROJECT_ROOT, "maps")
    if not os.path.isdir(maps_dir):
        maps_dir = os.path.join(CURRENT_DIR, "..", "maps")

    items = []
    if os.path.isdir(maps_dir):
        for fname in os.listdir(maps_dir):
            if fname.endswith(".txt") and "comp" not in fname.lower():
                full_path = os.path.abspath(os.path.join(maps_dir, fname))
                try:
                    b = Board.from_file(full_path)
                    if b.second_player is None and len(b.initial.boxes) > 0:
                        nb = len(b.initial.boxes)
                        if "small_easy" in fname:
                            label = f"Small Easy ({nb}B)"
                        elif "example" in fname:
                            label = f"Example ({nb}B)"
                        elif "medium" in fname:
                            label = f"Medium Obstacle ({nb}B)"
                        else:
                            base_name = fname[:-4].replace("map_", "").replace("_", " ").title()
                            label = f"{base_name} ({nb}B)"
                        items.append((full_path, label, nb))
                except Exception:
                    pass
    items.sort(key=lambda x: x[2])
    return [(p, l) for p, l, _ in items]


class SinglePlayerGUI:
    """Giao dien do hoa Pygame cho tro choi Sokoban che do mot nguoi."""

    def __init__(self, map_path: str = "maps/map_small_easy.txt", default_algo: str = "astar"):
        pygame.init()
        pygame.display.set_caption("Sokoban AI - Single Player (UCS & A*)")

        self.map_file = resolve_map_path(map_path)
        if not os.path.isfile(self.map_file):
            raise FileNotFoundError(f"Khong tim thay file ban do: {self.map_file}")

        self.available_maps = discover_single_player_maps()
        existing_paths = [os.path.abspath(p) for p, _ in self.available_maps]
        if os.path.abspath(self.map_file) not in existing_paths:
            fname = os.path.basename(self.map_file)
            self.available_maps.insert(0, (self.map_file, f"{fname} (Custom)"))

        self.board = Board.from_file(self.map_file)
        self.algorithm = default_algo.lower()
        if self.algorithm not in ("ucs", "astar"):
            self.algorithm = "astar"

        # Tinh toan kich thuoc cua so
        self.cell_size = 48
        self.hud_height = 160
        self.grid_width = self.board.width * self.cell_size
        self.grid_height = self.board.height * self.cell_size
        self.screen_width = max(self.grid_width, 760)
        self.screen_height = self.grid_height + self.hud_height

        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        self.clock = pygame.time.Clock()

        # Khoi tao phong chu da nen tang
        self.font_main = get_system_font(16, bold=True)
        self.font_sub = get_system_font(13)
        self.font_title = get_system_font(18, bold=True)
        self.font_btn = get_system_font(13, bold=True)

        # Trang thai giai va dieu khien
        self.solution_res: Optional[SearchResult] = None
        self.history_states: List[State] = [self.board.initial]
        self.actions_list: List[str] = []
        self.current_idx = 0

        self.is_paused = True
        self.step_delay_ms = 400
        self.last_step_time = pygame.time.get_ticks()

        self.map_buttons: List[Tuple[pygame.Rect, str]] = []

        # Giai tim duong ban dau
        self._solve()

    def _solve(self):
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

    def switch_map(self, new_map_path: str):
        actual_path = resolve_map_path(new_map_path)
        if not os.path.isfile(actual_path):
            return
        if os.path.abspath(actual_path) == os.path.abspath(self.map_file):
            self.current_idx = 0
            self.is_paused = True
            return

        self.map_file = actual_path
        self.board = Board.from_file(self.map_file)

        self.grid_width = self.board.width * self.cell_size
        self.grid_height = self.board.height * self.cell_size
        self.screen_width = max(self.grid_width, 760)
        self.screen_height = self.grid_height + self.hud_height

        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        self._solve()

    def cycle_next_map(self):
        if not self.available_maps:
            return
        curr_abs = os.path.abspath(self.map_file)
        curr_idx = 0
        for i, (p, _) in enumerate(self.available_maps):
            if os.path.abspath(p) == curr_abs:
                curr_idx = i
                break
        next_idx = (curr_idx + 1) % len(self.available_maps)
        self.switch_map(self.available_maps[next_idx][0])

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
        self.screen.blit(self.font_main.render(info_1, True, COLOR_TEXT), (20, 38))
        self.screen.blit(self.font_sub.render(info_2, True, COLOR_TEXT_MUTED), (20, 64))

        # Dong 3: Huong dan phim bam
        controls_text = "Phim: [Space] Chay/Dung | [->]/[<-] Buoc | [1]/[U] UCS | [2]/[A] A* | [M]/[Tab] Doi Map | [R] Reset"
        self.screen.blit(self.font_sub.render(controls_text, True, (180, 185, 195)), (20, 88))

        # Dong 4: Thanh chon Ban do (Map Selector Bar)
        map_label = self.font_main.render("Ban do:", True, COLOR_TEXT)
        self.screen.blit(map_label, (20, 118))

        mouse_pos = pygame.mouse.get_pos()
        self.map_buttons = []
        btn_x = 95
        btn_y = 113
        curr_abs = os.path.abspath(self.map_file)

        for path, label in self.available_maps:
            is_active = (os.path.abspath(path) == curr_abs)
            tw, th = self.font_btn.size(label)
            btn_w = tw + 20
            btn_h = 28
            btn_rect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)
            is_hover = btn_rect.collidepoint(mouse_pos)

            if is_active:
                pygame.draw.rect(self.screen, COLOR_ACCENT, btn_rect, border_radius=6)
                txt_surf = self.font_btn.render(label, True, (20, 24, 32))
            elif is_hover:
                pygame.draw.rect(self.screen, (55, 62, 75), btn_rect, border_radius=6)
                pygame.draw.rect(self.screen, (130, 140, 160), btn_rect, 1, border_radius=6)
                txt_surf = self.font_btn.render(label, True, (255, 255, 255))
            else:
                pygame.draw.rect(self.screen, (35, 40, 50), btn_rect, border_radius=6)
                pygame.draw.rect(self.screen, (65, 72, 85), btn_rect, 1, border_radius=6)
                txt_surf = self.font_btn.render(label, True, (190, 195, 205))

            txt_x = btn_rect.x + (btn_rect.width - tw) // 2
            txt_y = btn_rect.y + (btn_rect.height - th) // 2
            self.screen.blit(txt_surf, (txt_x, txt_y))

            self.map_buttons.append((btn_rect, path))
            btn_x += btn_w + 10

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

                if pos in self.board.walls:
                    draw_wall(self.screen, rect)
                    continue

                if pos in self.board.floors:
                    is_goal = pos in self.board.goals
                    draw_floor(self.screen, rect, is_goal=is_goal)

                    if pos in boxes_set:
                        box_color = COLOR_BOX_GOAL if is_goal else COLOR_BOX_NEUTRAL
                        draw_box(self.screen, rect, box_color)

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
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        for btn_rect, m_path in self.map_buttons:
                            if btn_rect.collidepoint(event.pos):
                                self.switch_map(m_path)
                                break
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
                    elif event.key in (pygame.K_m, pygame.K_TAB):
                        self.cycle_next_map()
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
    map_target = "maps/map_small_easy.txt"
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
