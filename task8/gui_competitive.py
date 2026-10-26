import os
import sys
import pygame
from typing import List, Tuple, Optional

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

try:
    from core.board import Board
    from core.competition import Competition
    from core.state import CompetitiveState
    from core.gui_theme import (
        COLOR_BG, COLOR_HUD_BG, COLOR_HUD_LINE, COLOR_TEXT, COLOR_TEXT_MUTED,
        COLOR_BOX_NEUTRAL, COLOR_BOX_0, COLOR_BOX_1, COLOR_AGENT_0, COLOR_AGENT_1,
        get_system_font, draw_floor, draw_wall, draw_box, draw_agent
    )
    from task7.runner import DecisionRunner
except ImportError:
    from board import Board
    from competitive import Competition, CompetitiveState
    from runner import DecisionRunner
    from core.gui_theme import (
        COLOR_BG, COLOR_HUD_BG, COLOR_HUD_LINE, COLOR_TEXT, COLOR_TEXT_MUTED,
        COLOR_BOX_NEUTRAL, COLOR_BOX_0, COLOR_BOX_1, COLOR_AGENT_0, COLOR_AGENT_1,
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


class CompetitiveGUI:

    def __init__(self, map_path: str = 'maps/competitive_map.txt', default_n: int = 30):
        pygame.init()
        pygame.display.set_caption('Sokoban AI - Competitive 2 Agents')

        self.available_maps: List[Tuple[str, str]] = [
            ('Arena Standard', resolve_map_path('maps/competitive_map.txt')),
            ('Maze Obstacles', resolve_map_path('maps/map_competition.txt')),
        ]

        self.map_file = resolve_map_path(map_path)
        if not os.path.isfile(self.map_file):
            self.map_file = self.available_maps[0][1]

        self.default_n = int(default_n)
        self.runner = DecisionRunner()

        self.cell_size = 48
        self.hud_height = 146

        self.font_main = get_system_font(18, bold=True)
        self.font_sub = get_system_font(13)
        self.font_title = get_system_font(19, bold=True)
        self.font_btn = get_system_font(13, bold=True)

        self.history_states: List[CompetitiveState] = []
        self.history_actions: List[Tuple[str, str]] = []
        self.history_timings: List[Tuple[float, float]] = []
        self.current_idx = 0

        self.is_paused = True
        self.step_delay_ms = 400
        self.last_step_time = pygame.time.get_ticks()

        self._init_board_and_window()

    def _init_board_and_window(self):
        self.board = Board.from_file(self.map_file)
        self.limit_steps = self.default_n
        self.competition = Competition(self.board, limit=self.limit_steps)

        self.history_states = [self.competition.create_initial_state()]
        self.history_actions.clear()
        self.history_timings.clear()
        self.current_idx = 0
        self.is_paused = True

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
        for name, _ in self.available_maps:
            w = 130
            self.map_btn_rects.append((pygame.Rect(start_x, 42, w, 28), name))
            start_x += w + 8

        bx = self.screen_width - 240
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

    def _cycle_map(self):
        current_idx = 0
        for idx, (_, path) in enumerate(self.available_maps):
            if path == self.map_file:
                current_idx = idx
                break
        next_idx = (current_idx + 1) % len(self.available_maps)
        self.switch_map(self.available_maps[next_idx][1])

    def _step_forward(self):
        if self.current_idx < len(self.history_states) - 1:
            self.current_idx += 1
            return

        cur_state = self.history_states[-1]
        if self.competition.is_game_over(cur_state):
            self.is_paused = True
            return

        actions, timings, errors = self.runner.decide(self.board, cur_state, limit_seconds=1.0)
        next_state = self.competition.step(cur_state, actions)

        self.history_states.append(next_state)
        self.history_actions.append((actions[0], actions[1]))
        self.history_timings.append((timings[0], timings[1]))
        self.current_idx += 1

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

        cur_state = self.history_states[self.current_idx]
        score_0, score_1 = cur_state.get_score()

        status_txt = 'PAUSED' if self.is_paused else 'PLAYING'
        if self.competition.is_game_over(cur_state):
            winner = self.competition.get_winner(cur_state)
            status_txt = 'HOA NHAU!' if winner is None else f'AGENT {winner} CHIEN THANG!'

        turn_str = f'Luot: {cur_state.turn} / {self.limit_steps} | [{status_txt}]'
        self.screen.blit(self.font_title.render(turn_str, True, COLOR_TEXT), (20, 10))

        txt_p0 = self.font_main.render(f'Agent 0 (A): {score_0} diem', True, COLOR_AGENT_0)
        txt_p1 = self.font_main.render(f'Agent 1 (Z): {score_1} diem', True, COLOR_AGENT_1)
        self.screen.blit(txt_p0, (self.screen_width - 340, 12))
        self.screen.blit(txt_p1, (self.screen_width - 170, 12))

        map_label = self.font_sub.render('Ban do:', True, COLOR_TEXT_MUTED)
        self.screen.blit(map_label, (20, 48))

        for (rect, name), (_, path) in zip(self.map_btn_rects, self.available_maps):
            is_active = (path == self.map_file)
            self._draw_button(rect, name, is_active=is_active, active_color=(40, 140, 95) if is_active else None)

        if self.current_idx > 0 and self.current_idx - 1 < len(self.history_actions):
            a0, a1 = self.history_actions[self.current_idx - 1]
            t0, t1 = self.history_timings[self.current_idx - 1]
            detail_str = f'Nuoc di gan nhat: A0={a0} ({t0*1000:.1f}ms) | A1={a1} ({t1*1000:.1f}ms)'
        else:
            detail_str = 'Trang thai xuat phat tran dau'
        self.screen.blit(self.font_sub.render(detail_str, True, COLOR_TEXT_MUTED), (20, 82))

        self._draw_button(self.btn_prev_rect, '< Lui', is_active=False)
        play_label = 'Pause' if not self.is_paused else 'Play'
        self._draw_button(self.btn_play_rect, play_label, is_active=(not self.is_paused))
        self._draw_button(self.btn_next_rect, 'Tien >', is_active=False)
        self._draw_button(self.btn_reset_rect, 'Reset', is_active=False)

        guide_str = 'Phim: [Space] Pause/Play | [->] Tien | [<-] Lui | [M] Doi map | [R] Reset | [Esc] Thoat'
        self.screen.blit(self.font_sub.render(guide_str, True, (165, 170, 180)), (20, 114))

    def _draw_board(self):
        offset_x = (self.screen_width - self.grid_width) // 2
        offset_y = self.hud_height

        cur_state = self.history_states[self.current_idx]
        boxes_dict = dict(zip(cur_state.boxes, cur_state.owners))

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

                    if pos in boxes_dict:
                        owner = boxes_dict[pos]
                        if owner == 0:
                            box_color = COLOR_BOX_0
                        elif owner == 1:
                            box_color = COLOR_BOX_1
                        else:
                            box_color = COLOR_BOX_NEUTRAL
                        draw_box(self.screen, rect, box_color)

                    if pos == cur_state.players[0]:
                        center = rect.center
                        radius = self.cell_size // 3
                        draw_agent(self.screen, center, radius, COLOR_AGENT_0, '0', self.font_sub)

                    if pos == cur_state.players[1]:
                        center = rect.center
                        radius = self.cell_size // 3
                        draw_agent(self.screen, center, radius, COLOR_AGENT_1, '1', self.font_sub)

    def run(self):
        running = True
        while running:
            now = pygame.time.get_ticks()

            mpos = pygame.mouse.get_pos()
            is_hovering_btn = (
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
                    if self.btn_play_rect.collidepoint(pos):
                        self.is_paused = not self.is_paused
                    elif self.btn_prev_rect.collidepoint(pos):
                        self.is_paused = True
                        self._step_backward()
                    elif self.btn_next_rect.collidepoint(pos):
                        self.is_paused = True
                        self._step_forward()
                    elif self.btn_reset_rect.collidepoint(pos):
                        self.history_states = [self.competition.create_initial_state()]
                        self.history_actions.clear()
                        self.history_timings.clear()
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
                    elif event.key == pygame.K_m:
                        self._cycle_map()
                    elif event.key == pygame.K_r:
                        self.history_states = [self.competition.create_initial_state()]
                        self.history_actions.clear()
                        self.history_timings.clear()
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

        self.runner.close()
        pygame.quit()


if __name__ == '__main__':
    map_target = 'maps/competitive_map.txt'
    default_turns = 30

    if len(sys.argv) > 1:
        map_target = sys.argv[1]
    if len(sys.argv) > 2:
        try:
            default_turns = int(sys.argv[2])
        except ValueError:
            pass

    print(f'Khoi dong Sokoban Competitive GUI:')
    print(f' - Ban do: {map_target}')
    print(f' - So luot toi da: {default_turns}')
    app = CompetitiveGUI(map_path=map_target, default_n=default_turns)
    app.run()
