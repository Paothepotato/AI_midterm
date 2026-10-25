import pygame
from typing import Tuple

COLOR_BG = (30, 34, 42)
COLOR_HUD_BG = (20, 22, 28)
COLOR_HUD_LINE = (50, 55, 65)
COLOR_TEXT = (240, 240, 240)
COLOR_TEXT_MUTED = (160, 165, 175)
COLOR_ACCENT = (255, 195, 0)

COLOR_FLOOR = (235, 235, 230)
COLOR_FLOOR_BORDER = (215, 215, 210)
COLOR_WALL = (70, 75, 85)
COLOR_WALL_BORDER = (50, 55, 65)
COLOR_GOAL = (220, 60, 60)

COLOR_BOX_NEUTRAL = (190, 140, 80)
COLOR_BOX_GOAL = (50, 175, 110)
COLOR_BOX_0 = (65, 145, 255)
COLOR_BOX_1 = (255, 110, 65)

COLOR_AGENT_SINGLE = (45, 125, 245)
COLOR_AGENT_0 = (40, 120, 240)
COLOR_AGENT_1 = (235, 90, 40)


def get_system_font(size: int, bold: bool = False) -> pygame.font.Font:
    fonts = ["Arial", "Helvetica", "DejaVu Sans", "Segoe UI"]
    for f in fonts:
        try:
            return pygame.font.SysFont(f, size, bold=bold)
        except Exception:
            continue
    return pygame.font.Font(None, size)


def draw_floor(surface: pygame.Surface, rect: pygame.Rect, is_goal: bool = False):
    pygame.draw.rect(surface, COLOR_FLOOR, rect)
    pygame.draw.rect(surface, COLOR_FLOOR_BORDER, rect, 1)
    if is_goal:
        center = rect.center
        radius = max(3, rect.width // 5)
        pygame.draw.circle(surface, COLOR_GOAL, center, radius)


def draw_wall(surface: pygame.Surface, rect: pygame.Rect):
    pygame.draw.rect(surface, COLOR_WALL, rect)
    pygame.draw.rect(surface, COLOR_WALL_BORDER, rect, 1)


def draw_box(surface: pygame.Surface, rect: pygame.Rect, color: Tuple[int, int, int]):
    inner_rect = rect.inflate(-12, -12)
    pygame.draw.rect(surface, color, inner_rect, border_radius=4)
    pygame.draw.rect(surface, (30, 30, 30), inner_rect, 2, border_radius=4)

    p1 = (inner_rect.left + 5, inner_rect.top + 5)
    p2 = (inner_rect.right - 5, inner_rect.bottom - 5)
    p3 = (inner_rect.right - 5, inner_rect.top + 5)
    p4 = (inner_rect.left + 5, inner_rect.bottom - 5)
    pygame.draw.line(surface, (40, 40, 40), p1, p2, 2)
    pygame.draw.line(surface, (40, 40, 40), p3, p4, 2)


def draw_agent(surface: pygame.Surface, center: Tuple[int, int], radius: int,
               color: Tuple[int, int, int], label: str, font: pygame.font.Font):
    pygame.draw.circle(surface, color, center, radius)
    pygame.draw.circle(surface, (255, 255, 255), center, radius, 2)
    if label:
        txt = font.render(label, True, (255, 255, 255))
        surface.blit(txt, txt.get_rect(center=center))
