import os
import sys
import pygame
from typing import List, Optional, Tuple

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

try:
    from core.board import Board
    from core.state import State
    from core.gui_theme import (
        COLOR_BG, COLOR_HUD_BG, COLOR_HUD_LINE, COLOR_TEXT, COLOR_TEXT_MUTED,
        COLOR_ACCENT, COLOR_BOX_NEUTRAL, COLOR_BOX_GOAL, COLOR_AGENT_SINGLE,
        get_system_font, draw_floor, draw_wall, draw_box, draw_agent
    )
    from task2.solver import SearchSolver, SearchResult
except ImportError:
    from board import Board
    from state import State
    from solver import SearchSolver, SearchResult
    from core.gui_theme import (
        COLOR_BG, COLOR_HUD_BG, COLOR_HUD_LINE, COLOR_TEXT, COLOR_TEXT_MUTED,
        COLOR_ACCENT, COLOR_BOX_NEUTRAL, COLOR_BOX_GOAL, COLOR_AGENT_SINGLE,
        get_system_font, draw_floor, draw_wall, draw_box, draw_agent
    )


def resolve_map_path(map_name_or_path: str) -> str:
    candidates = [
        map_name_or_path,
        os.path.join(PROJECT_ROOT, map_name_or_path),
        os.path.join(PROJECT_ROOT, 'maps', os.path.basename(map_name_or_path)),
        os.path.join(CURRENT_DIR, '..', 'maps', os.path.basename(map_name_or_path))
    ]
    for c in candidates:
        if os.path.isfile(c):
            return os.path.abspath(c)
    return map_name_or_path


class SinglePlayerGUI:

    def __init__(self, map_path: str = 'maps/example_map.txt', default_algo: str = 'astar'):
        pygame.init()
        pygame.display.set_caption('Sokoban AI - Single Player (UCS & A*)')

        self.available_maps: List[Tuple[str, str]] = [
            ('Small (2B)', resolve_map_path('maps/map_small_easy.txt')),
            ('Example (7B)', resolve_map_path('maps/example_map.txt')),
            ('Medium (8B)', resolve_map_path('maps/map_medium.txt')),
        ]

        self.map_file = resolve_map_path(map_path)
        if not os.path.isfile(self.map_file):
            self.map_file = self.available_maps[1][1]

        self.algorithm = default_algo.lower()
        if self.algorithm not in ('ucs', 'astar'):
            self.algorithm = 'astar'

        self.cell_size = 48
        self.hud_height = 146

        self.font_main = get_system_font(18, bold=True)
        self.font_sub = get_system_font(13)
        self.font_title = get_system_font(19, bold=True)
        self.font_btn = get_system_font(13, bold=True)

        self.solution_res: Optional[SearchResult] = None
        self.history_states: List[State] = []
        self.actions_list: List[str] = []
        self.current_idx = 0

        self.is_paused = True
        self.step_delay_ms = 400
        self.last_step_time = pygame.time.get_ticks()

        self._init_board_and_window()
        self._solve()

    def _init_board_and_window(self):
        self.board = Board.from_file(self.map_file)
        self.grid_width = self.board.width * self.cell_size
        self.grid_height = self.board.height * self.cell_size
        self.screen_width = max(self.grid_width, 820)
        self.screen_height = self.grid_height + self.hud_height

        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        self.clock = pygame.time.Clock()
        self._recalc_buttons()

    def _recalc_buttons(self):
        self.map_btn_rects = []
        start_x = 80
        for i, (name, _) in enumerate(self.available_maps):
            w = 100 if 'Small' in name else 105
            self.map_btn_rects.append((pygame.Rect(start_x, 42, w, 28), name))
            start_x += w + 8

        bx = self.screen_width - 240
        self.btn_ucs_rect = pygame.Rect(bx, 42, 105, 28)
        self.btn_astar_rect = pygame.Rect(bx + 112, 42, 108, 28)

        self.btn_prev_rect = pygame.Rect(bx, 78, 50, 28)
        self.btn_play_rect = pygame.Rect(bx + 56, 78, 66, 28)
        self.btn_next_rect = pygame.Rect(bx + 128, 78, 50, 28)
        self.btn_reset_rect = pygame.Rect(bx + 184, 78, 44, 28)

    def switch_map(self, map_path: str):
        target = resolve_map_path(map_path)
        if target == self.map_file:
            return
        self.map_file = target
        self._init_board_and_window()
        self._solve()

    def _cycle_map(self):
        current_idx = 0
        for idx, (_, path) in enumerate(self.available_maps):
            if path == self.map_file:
                current_idx = idx
                break
        next_idx = (current_idx + 1) % len(self.available_maps)
        self.switch_map(self.available_maps[next_idx][1])

    def _solve(self):
        solver = SearchSolver(self.board, algorithm=self.algorithm, prune_deadlocks=True)
        self.solution_res = solver.solve(timeout=30.0)

        if self.solution_res.status == 'solved':
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

    def _draw_button(self, rect: pygame.Rect, text: str, is_active: bool, is_accent: bool = False, active_color: Optional[Tuple[int, int, int]] = None):
        if is_active:
            if active_color:
                bg_color = active_color
                border_color = (255, 255, 255)
                text_color = (255, 255, 255)
            elif is_accent:
                bg_color = (225, 155, 15)
                border_color = (255, 215, 90)
                text_color = (20, 20, 20)
            else:
                bg_color = (35, 110, 230)
                border_color = (120, 180, 255)
                text_color = (255, 255, 255)
        else:
            bg_color = (32, 36, 46)
            border_color = (65, 72, 85)
            text_color = (185, 190, 200)

        pygame.draw.rect(self.screen, bg_color, rect, border_radius=5)
        pygame.draw.rect(self.screen, border_color, rect, 2 if is_active else 1, border_radius=5)
        txt_surf = self.font_btn.render(text, True, text_color)
        self.screen.blit(txt_surf, txt_surf.get_rect(center=rect.center))

    def _draw_hud(self):
        hud_rect = pygame.Rect(0, 0, self.screen_width, self.hud_height)
        pygame.draw.rect(self.screen, COLOR_HUD_BG, hud_rect)
        pygame.draw.line(self.screen, COLOR_HUD_LINE, (0, self.hud_height), (self.screen_width, self.hud_height), 2)

        algo_name = 'A* (Hungarian BFS)' if self.algorithm == 'astar' else 'UCS (Uniform Cost Search)'
        status_txt = 'PAUSED' if self.is_paused else 'PLAYING'

        cur_state = self.history_states[self.current_idx]
        is_at_goal = self.board.is_goal(cur_state)
        goal_status = 'HOAN THANH GOAL' if is_at_goal else 'DANG DI CHUYEN'

        title_surf = self.font_title.render(f'Thuat toan: {algo_name}', True, COLOR_ACCENT)
        self.screen.blit(title_surf, (20, 10))

        state_color = (100, 220, 100) if not self.is_paused else (240, 180, 80)
        mode_surf = self.font_main.render(f'[{status_txt}] - {goal_status}', True, state_color)
        self.screen.blit(mode_surf, (self.screen_width - 240, 12))

        map_label = self.font_sub.render('Ban do:', True, COLOR_TEXT_MUTED)
        self.screen.blit(map_label, (20, 48))

        for (rect, name), (_, path) in zip(self.map_btn_rects, self.available_maps):
            is_active = (path == self.map_file)
            self._draw_button(rect, name, is_active=is_active, active_color=(40, 140, 95) if is_active else None)

        self._draw_button(self.btn_ucs_rect, 'UCS [1/U]', is_active=(self.algorithm == 'ucs'), is_accent=False)
        self._draw_button(self.btn_astar_rect, 'A* [2/A]', is_active=(self.algorithm == 'astar'), is_accent=True)

        total_actions = len(self.actions_list)
        time_ms = self.solution_res.elapsed_seconds * 1000 if self.solution_res else 0.0
        expanded = self.solution_res.expanded if self.solution_res else 0

        info_1 = f'Hanh dong: Buoc {self.current_idx} / {total_actions} (Cost: {total_actions})'
        info_2 = f'Thoi gian giai: {time_ms:.1f}ms | So node mo rong: {expanded}'
        self.screen.blit(self.font_main.render(info_1, True, COLOR_TEXT), (20, 78))
        self.screen.blit(self.font_sub.render(info_2, True, COLOR_TEXT_MUTED), (20, 104))

        self._draw_button(self.btn_prev_rect, '< Lui', is_active=False)
        play_label = 'Pause' if not self.is_paused else 'Play'
        self._draw_button(self.btn_play_rect, play_label, is_active=(not self.is_paused))
        self._draw_button(self.btn_next_rect, 'Tien >', is_active=False)
        self._draw_button(self.btn_reset_rect, 'Reset', is_active=False)

        controls_text = 'Phim: [Space] Play/Pause | [->] Tien | [<-] Lui | [1]/[U] UCS | [2]/[A] A* | [M] Doi map | [R] Reset'
        self.screen.blit(self.font_sub.render(controls_text, True, (165, 170, 180)), (20, 126))

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
                        draw_agent(self.screen, center, radius, COLOR_AGENT_SINGLE, 'A', self.font_sub)

    def run(self):
        running = True
        while running:
            now = pygame.time.get_ticks()

            mpos = pygame.mouse.get_pos()
            is_hovering_btn = (
                self.btn_ucs_rect.collidepoint(mpos) or
                self.btn_astar_rect.collidepoint(mpos) or
                self.btn_play_rect.collidepoint(mpos) or
                self.btn_prev_rect.collidepoint(mpos) or
                self.btn_next_rect.collidepoint(mpos) or
                self.btn_reset_rect.collidepoint(mpos) or
                any(rect.collidepoint(mpos) for rect, _ in self.map_btn_rects)
            )
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND if is_hovering_btn else pygame.SYSTEM_CURSOR_ARROW)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    pos = event.pos
                    if self.btn_ucs_rect.collidepoint(pos):
                        self.switch_algorithm('ucs')
                    elif self.btn_astar_rect.collidepoint(pos):
                        self.switch_algorithm('astar')
                    elif self.btn_play_rect.collidepoint(pos):
                        self.is_paused = not self.is_paused
                    elif self.btn_prev_rect.collidepoint(pos):
                        self.is_paused = True
                        self._step_backward()
                    elif self.btn_next_rect.collidepoint(pos):
                        self.is_paused = True
                        self._step_forward()
                    elif self.btn_reset_rect.collidepoint(pos):
                        self.current_idx = 0
                        self.is_paused = True
                    else:
                        for (rect, _), (_, path) in zip(self.map_btn_rects, self.available_maps):
                            if rect.collidepoint(pos):
                                self.switch_map(path)
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
                        self.switch_algorithm('ucs')
                    elif event.key in (pygame.K_2, pygame.K_a):
                        self.switch_algorithm('astar')
                    elif event.key == pygame.K_m:
                        self._cycle_map()
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


if __name__ == '__main__':
    map_target = 'maps/example_map.txt'
    algo_target = 'astar'

    if len(sys.argv) > 1:
        map_target = sys.argv[1]
    if len(sys.argv) > 2:
        algo_target = sys.argv[2]

    print(f'Khoi dong Sokoban Single Player GUI:')
    print(f' - Ban do   : {map_target}')
    print(f' - Thuat toan: {algo_target.upper()}')
    app = SinglePlayerGUI(map_path=map_target, default_algo=algo_target)
    app.run()
