import pygame
import math
import random
import constants as C # Use absolute import

class Screen:
    """ Handles screen drawing and updates """
    def __init__(self, width=C.SCREEN_WIDTH, height=C.SCREEN_HEIGHT, caption='Snake Game'):
        self.width = width
        self.height = height
        self.surface = pygame.display.set_mode((width, height))
        pygame.display.set_caption(caption)
        try:
            self.font           = pygame.font.SysFont('Arial', 22, bold=True)
            self.font_regular   = pygame.font.SysFont('Arial', 22)
            self.title_font     = pygame.font.SysFont('Arial', 52, bold=True)
            self.score_font     = pygame.font.SysFont('Arial', 28, bold=True)
            self.hs_title_font  = pygame.font.SysFont('Arial', 22, bold=True)
            self.hs_entry_font  = pygame.font.SysFont('Arial', 19)
            self.input_font     = pygame.font.SysFont('Arial', 22)
            self.prompt_font    = pygame.font.SysFont('Arial', 18)
            self.buff_font      = pygame.font.SysFont('Arial', 17, bold=True)
            self.hud_font       = pygame.font.SysFont('Arial', 22, bold=True)
        except pygame.error:
            self.font           = pygame.font.Font(None, 28)
            self.font_regular   = pygame.font.Font(None, 28)
            self.title_font     = pygame.font.Font(None, 64)
            self.score_font     = pygame.font.Font(None, 34)
            self.hs_title_font  = pygame.font.Font(None, 28)
            self.hs_entry_font  = pygame.font.Font(None, 24)
            self.input_font     = pygame.font.Font(None, 28)
            self.prompt_font    = pygame.font.Font(None, 23)
            self.buff_font      = pygame.font.Font(None, 22)
            self.hud_font       = pygame.font.Font(None, 28)
        # Keep old names so legacy call sites (pause, death animation) still work
        self.game_over_font   = self.title_font
        self.high_score_font  = self.hs_entry_font
        # Ripple wave state for the death screen animation
        self._waves = []      # list of [cx, cy, radius]
        self._wave_tick = 0

    # ------------------------------------------------------------------ helpers
    def _alpha_surface(self, w, h, color_rgba):
        """Return a pre-filled SRCALPHA surface."""
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        s.fill(color_rgba)
        return s

    def _panel(self, rect, color_rgba=None, border_color=None):
        """Draw a rounded-corner-style panel (dark fill + optional 1 px border)."""
        if color_rgba is None:
            color_rgba = C.PANEL_BG_RGBA
        s = self._alpha_surface(rect.width, rect.height, color_rgba)
        self.surface.blit(s, rect)
        if border_color:
            pygame.draw.rect(self.surface, border_color, rect, 1)

    def _shadow_text(self, font, text, color, center, offset=2):
        """Render text with a drop shadow."""
        shadow = font.render(text, True, (0, 0, 0))
        surf   = font.render(text, True, color)
        sr = shadow.get_rect(center=(center[0] + offset, center[1] + offset))
        tr = surf.get_rect(center=center)
        self.surface.blit(shadow, sr)
        self.surface.blit(surf, tr)

    def _draw_hud_bar(self, rect):
        """Semi-transparent bar behind HUD text."""
        pad_x, pad_y = 8, 4
        s = self._alpha_surface(rect.width + pad_x * 2, rect.height + pad_y * 2, (0, 0, 0, 160))
        self.surface.blit(s, (rect.x - pad_x, rect.y - pad_y))

    # ------------------------------------------------------------------ gameplay HUD
    def clear(self):
        self.surface.fill(C.BACKGROUND_COLOR)
        for x in range(0, C.SCREEN_WIDTH, C.GRID_SIZE):
            pygame.draw.line(self.surface, C.GRID_LINE_COLOR, (x, 0), (x, C.SCREEN_HEIGHT))
        for y in range(0, C.SCREEN_HEIGHT, C.GRID_SIZE):
            pygame.draw.line(self.surface, C.GRID_LINE_COLOR, (0, y), (C.SCREEN_WIDTH, y))

    def draw_element(self, element):
        element.draw(self.surface)

    def draw_score_and_level(self, score, level):
        """Score + level on a single semi-transparent HUD bar."""
        score_surf = self.hud_font.render(f'Score: {score}', True, C.TEXT_COLOR)
        level_surf = self.hud_font.render(f'Level: {level}', True, C.TEXT_COLOR)
        score_rect = score_surf.get_rect(topleft=C.SCORE_POS)
        level_rect = level_surf.get_rect(topleft=(C.SCORE_POS[0] + 150, C.SCORE_POS[1]))
        self._draw_hud_bar(score_rect.union(level_rect))
        self.surface.blit(score_surf, score_rect)
        self.surface.blit(level_surf, level_rect)

    def draw_buffs(self, active_buffs):
        """Active buff pills in the top-right corner with a coloured background."""
        if not active_buffs:
            return
        x_right = self.width - 8
        y = 10
        for buff_key, ticks_left in active_buffs.items():
            label, color = C.BUFF_DISPLAY_NAMES.get(buff_key, (buff_key, C.TEXT_COLOR))
            text = self.buff_font.render(f'{label}  {ticks_left}', True, color)
            text_rect = text.get_rect(topright=(x_right, y))
            # Coloured pill background
            r, g, b = color
            pill = self._alpha_surface(text_rect.width + 14, text_rect.height + 6,
                                       (r // 5, g // 5, b // 5, 200))
            self.surface.blit(pill, (text_rect.x - 7, text_rect.y - 3))
            pygame.draw.rect(self.surface, (r // 2, g // 2, b // 2),
                             pygame.Rect(text_rect.x - 7, text_rect.y - 3,
                                         text_rect.width + 14, text_rect.height + 6), 1)
            self.surface.blit(text, text_rect)
            y += text_rect.height + 10

    # Legacy single-method call sites (pause screen etc.)
    def draw_score(self, score):
        self.surface.blit(self.hud_font.render(f'Score: {score}', True, C.TEXT_COLOR), C.SCORE_POS)

    def draw_level(self, level):
        self.surface.blit(self.hud_font.render(f'Level: {level}', True, C.TEXT_COLOR),
                          (C.SCORE_POS[0] + 150, C.SCORE_POS[1]))

    # ------------------------------------------------------------------ overlay
    def draw_overlay(self, alpha=175):
        """Dim the current frame with a dark transparent layer."""
        s = self._alpha_surface(self.width, self.height, (0, 0, 0, alpha))
        self.surface.blit(s, (0, 0))

    # ------------------------------------------------------------------ death / game-over screens
    def draw_game_over_message(self, score):
        """'Game Over!' (bold red) + 'Score: X' (amber) centred on screen."""
        cx = C.GAME_OVER_POS[0]
        self._shadow_text(self.title_font, 'Game Over!',
                          C.GAMEOVER_TITLE_COLOR, (cx, C.GAME_OVER_POS[1] - 152))
        self._shadow_text(self.score_font, f'Score:  {score}',
                          C.GAMEOVER_SCORE_COLOR, (cx, C.GAME_OVER_POS[1] - 108))

    def draw_run_stats(self, apples_eaten, time_ticks, max_level):
        """Per-run stats bar between the score and the high-score list."""
        seconds = time_ticks // 10
        parts = [
            (f'\u25b6  {apples_eaten} apples', C.TEXT_COLOR),
            ('|', C.PROMPT_COLOR),
            (f'\u23f1  {seconds}s', C.TEXT_COLOR),
            ('|', C.PROMPT_COLOR),
            (f'\u2605  level {max_level}', C.TEXT_COLOR),
        ]
        gap = 10
        surfaces = [self.prompt_font.render(t, True, c) for t, c in parts]
        total_w = sum(s.get_width() for s in surfaces) + gap * (len(surfaces) - 1)
        x = C.GAME_OVER_POS[0] - total_w // 2
        y_center = C.GAME_OVER_POS[1] - 75
        # background pill
        h = max(s.get_height() for s in surfaces)
        pill = self._alpha_surface(total_w + 20, h + 8, (30, 30, 30, 180))
        self.surface.blit(pill, (x - 10, y_center - h // 2 - 4))
        for surf in surfaces:
            r = surf.get_rect(midleft=(x, y_center))
            self.surface.blit(surf, r)
            x += surf.get_width() + gap

    def draw_high_score_list(self, high_scores, highlight_pos=-1):
        """High-score list with a panel, medal colours, and optional new-entry highlight."""
        cx = C.GAME_OVER_POS[0]
        title_y  = C.GAME_OVER_POS[1] - 44
        entry_y0 = C.GAME_OVER_POS[1] - 14
        row_h    = 26
        panel_pad = 12
        panel_rect = pygame.Rect(
            cx - 170,
            title_y - panel_pad - 6,
            340,
            panel_pad * 2 + 30 + len(high_scores) * row_h + 6
        )
        self._panel(panel_rect, border_color=C.PANEL_BORDER_COLOR)

        # Title
        self._shadow_text(self.hs_title_font, 'High Scores',
                          C.HS_RANK_GOLD, (cx, title_y))

        # Rank medal colours
        medal = [C.HS_RANK_GOLD, C.HS_RANK_SILVER, C.HS_RANK_BRONZE]

        for i, (name, hs_score) in enumerate(high_scores):
            if i == highlight_pos:
                color = C.HS_HIGHLIGHT
                # Highlight row background
                row_bg = self._alpha_surface(panel_rect.width - 4, row_h - 2, (80, 80, 0, 120))
                self.surface.blit(row_bg, (panel_rect.x + 2, entry_y0 + i * row_h - row_h // 2))
            elif i < 3:
                color = medal[i]
            else:
                color = C.TEXT_DIM_COLOR

            rank_surf  = self.hs_entry_font.render(f'{i + 1}.', True, color)
            name_surf  = self.hs_entry_font.render(name, True, color)
            score_surf = self.hs_entry_font.render(str(hs_score), True, color)

            row_y = entry_y0 + i * row_h
            self.surface.blit(rank_surf,  rank_surf.get_rect(midright=(cx - 110, row_y)))
            self.surface.blit(name_surf,  name_surf.get_rect(midleft=(cx - 100, row_y)))
            self.surface.blit(score_surf, score_surf.get_rect(midright=(cx + 155, row_y)))

    def show_restart_prompt(self):
        text = 'ENTER  restart     ESC  quit'
        surf = self.prompt_font.render(text, True, C.PROMPT_COLOR)
        rect = surf.get_rect(center=C.RESTART_PROMPT_POS)
        pill = self._alpha_surface(rect.width + 20, rect.height + 8, (0, 0, 0, 140))
        self.surface.blit(pill, (rect.x - 10, rect.y - 4))
        self.surface.blit(surf, rect)

    def draw_text_input(self, prompt, current_text, active):
        """Name-entry input box with a dark fill and accent border."""
        # Prompt label
        prompt_surf = self.prompt_font.render(prompt, True, C.TEXT_DIM_COLOR)
        self.surface.blit(prompt_surf, prompt_surf.get_rect(center=C.INPUT_PROMPT_POS))

        # Box background
        box_fill = self._alpha_surface(C.INPUT_BOX_RECT.width, C.INPUT_BOX_RECT.height,
                                       (20, 20, 20, 220))
        self.surface.blit(box_fill, C.INPUT_BOX_RECT)

        # Border – accent colour when active
        border_color = (100, 160, 255) if active else (80, 80, 80)
        pygame.draw.rect(self.surface, border_color, C.INPUT_BOX_RECT, 2)

        # Typed text
        text_surf = self.input_font.render(current_text, True, C.TEXT_COLOR)
        self.surface.blit(text_surf,
                          text_surf.get_rect(midleft=(C.INPUT_BOX_RECT.x + 8,
                                                       C.INPUT_BOX_RECT.centery)))

    # ------------------------------------------------------------------ misc text
    def draw_message_at_x_y(self, message, x, y, size):
        font = pygame.font.SysFont('Arial', size)
        surf = font.render(message, True, C.TEXT_COLOR)
        self.surface.blit(surf, surf.get_rect(center=(x, y)))

    def draw_bottom_message(self, message, size):
        font = pygame.font.SysFont('Arial', size)
        surf = font.render(message, True, C.PROMPT_COLOR)
        pill = self._alpha_surface(surf.get_width() + 20, surf.get_height() + 8, (0, 0, 0, 150))
        rect = surf.get_rect(center=(C.SCREEN_WIDTH // 2, C.SCREEN_HEIGHT - 40))
        self.surface.blit(pill, (rect.x - 10, rect.y - 4))
        self.surface.blit(surf, rect)

    # ------------------------------------------------------------------ wave animation
    def reset_waves(self):
        self._waves = []
        self._wave_tick = 0

    def tick_waves(self):
        """Spawn and advance ripple waves one frame."""
        self._wave_tick += 1
        if self._wave_tick % C.WAVE_SPAWN_INTERVAL == 0:
            self._waves.append([
                random.randint(0, C.SCREEN_WIDTH),
                random.randint(0, C.SCREEN_HEIGHT),
                1
            ])
        for w in self._waves:
            w[2] += C.WAVE_SPEED
        self._waves = [w for w in self._waves if w[2] < C.WAVE_MAX_RADIUS]

    def _draw_ripple_grid(self):
        """Dark grid background with expanding ripple circles."""
        self.surface.fill(C.BACKGROUND_COLOR)
        for x in range(0, C.SCREEN_WIDTH + 1, C.GRID_SIZE):
            pygame.draw.line(self.surface, C.GRID_LINE_COLOR, (x, 0), (x, C.SCREEN_HEIGHT))
        for y in range(0, C.SCREEN_HEIGHT + 1, C.GRID_SIZE):
            pygame.draw.line(self.surface, C.GRID_LINE_COLOR, (0, y), (C.SCREEN_WIDTH, y))
        if not self._waves:
            return
        overlay = pygame.Surface((C.SCREEN_WIDTH, C.SCREEN_HEIGHT), pygame.SRCALPHA)
        max_r = math.sqrt(C.SCREEN_WIDTH ** 2 + C.SCREEN_HEIGHT ** 2)
        for cx, cy, radius in self._waves:
            t = min(radius / max_r, 1.0)
            alpha = int(180 * (1 - t))
            b     = int(110 * (1 - t))
            pygame.draw.circle(overlay, (0, b // 2, b, alpha),
                                (int(cx), int(cy)), int(radius), 2)
        self.surface.blit(overlay, (0, 0))

    # ------------------------------------------------------------------ stat cards
    def _draw_stat_cards(self, stats, y_top):
        """2 rows x 3 columns of labelled stat cards."""
        cards = [
            ('Peak Size',  f"{stats['max_length']} seg"),
            ('Apples',     str(stats['apples'])),
            ('Distance',   f"{stats['distance']} cells"),
            ('Power-ups',  str(stats['magic_apples'])),
            ('Survived',   f"{stats['time_ticks'] // 10}s"),
            ('Max Level',  str(stats['max_level'])),
        ]
        cols           = 3
        card_w, card_h = 172, 36
        gap_x, gap_y   = 12, 8
        total_w = cols * card_w + (cols - 1) * gap_x
        start_x = (C.SCREEN_WIDTH - total_w) // 2

        for i, (label, value) in enumerate(cards):
            col = i % cols
            row = i // cols
            x = start_x + col * (card_w + gap_x)
            y = y_top   + row * (card_h + gap_y)
            rect = pygame.Rect(x, y, card_w, card_h)

            bg = self._alpha_surface(card_w, card_h, (18, 18, 48, 190))
            self.surface.blit(bg, rect)
            pygame.draw.rect(self.surface, C.PANEL_BORDER_COLOR, rect, 1)

            lsurf = self.prompt_font.render(label, True, C.TEXT_DIM_COLOR)
            self.surface.blit(lsurf, lsurf.get_rect(midleft=(rect.x + 10, rect.centery)))

            vsurf = self.hs_entry_font.render(value, True, C.TEXT_COLOR)
            self.surface.blit(vsurf, vsurf.get_rect(midright=(rect.right - 10, rect.centery)))

    # ------------------------------------------------------------------ HS section
    def _draw_hs_section(self, high_scores, highlight_pos, y_title):
        """High-score list with title, medal colours, new-entry highlight."""
        cx = C.SCREEN_WIDTH // 2
        self._shadow_text(self.hs_title_font, 'HIGH  SCORES', C.HS_RANK_GOLD, (cx, y_title))
        medal   = [C.HS_RANK_GOLD, C.HS_RANK_SILVER, C.HS_RANK_BRONZE]
        entry_y = y_title + 26
        row_h   = 28

        for i, (name, hs_score) in enumerate(high_scores):
            if i == highlight_pos:
                color   = C.HS_HIGHLIGHT
                row_bg  = self._alpha_surface(524, row_h - 2, (80, 80, 0, 100))
                self.surface.blit(row_bg, (38, entry_y + i * row_h - row_h // 2 + 1))
            elif i < 3:
                color = medal[i]
            else:
                color = C.TEXT_DIM_COLOR

            rank_s  = self.hs_entry_font.render(f'{i + 1}.', True, color)
            name_s  = self.hs_entry_font.render(name,         True, color)
            score_s = self.hs_entry_font.render(str(hs_score), True, color)
            row_y   = entry_y + i * row_h
            self.surface.blit(rank_s,  rank_s.get_rect(midright=(cx - 140, row_y)))
            self.surface.blit(name_s,  name_s.get_rect(midleft=(cx - 128, row_y)))
            self.surface.blit(score_s, score_s.get_rect(midright=(cx + 172, row_y)))

    # ------------------------------------------------------------------ restart buttons
    def _draw_restart_buttons(self, tick):
        """Two styled keyboard-hint buttons that pulse to signal interactivity."""
        pulse   = int(160 + 80 * math.sin(tick * 0.15))   # 80-240
        cy      = 492
        btn_h   = 36
        btn_w   = 170

        # ENTER – Restart
        er = pygame.Rect(C.SCREEN_WIDTH // 2 - btn_w - 16, cy - btn_h // 2, btn_w, btn_h)
        self._panel(er, (0, 30, 0, 200))
        pygame.draw.rect(self.surface, (0, pulse, 0), er, 2)
        es = self.prompt_font.render('ENTER   Restart', True, (80, pulse, 80))
        self.surface.blit(es, es.get_rect(center=er.center))

        # ESC – Quit
        qr = pygame.Rect(C.SCREEN_WIDTH // 2 + 16, cy - btn_h // 2, btn_w, btn_h)
        self._panel(qr, (30, 0, 0, 200))
        pygame.draw.rect(self.surface, (pulse // 2, 0, 0), qr, 2)
        qs = self.prompt_font.render('ESC   Quit', True, (pulse // 2 + 60, 60, 60))
        self.surface.blit(qs, qs.get_rect(center=qr.center))

    # ------------------------------------------------------------------ full death screen
    def draw_death_screen(self, score, stats, high_scores, highlight_pos=-1, tick=0):
        """Complete animated death screen: ripple grid + panel + stats + leaderboard."""
        cx = C.SCREEN_WIDTH // 2

        # 1. Animated grid background
        self._draw_ripple_grid()

        # 2. Main translucent panel
        panel = pygame.Rect(18, 14, 564, 454)
        self._panel(panel, (8, 8, 22, 235), C.PANEL_BORDER_COLOR)

        # 3. "GAME  OVER" title
        self._shadow_text(self.title_font, 'GAME  OVER', C.GAMEOVER_TITLE_COLOR, (cx, 60))

        # 4. Score
        self._shadow_text(self.score_font, f'Score   {score}', C.GAMEOVER_SCORE_COLOR, (cx, 108))

        # 5. Thin divider
        pygame.draw.line(self.surface, C.PANEL_BORDER_COLOR, (38, 130), (562, 130), 1)

        # 6. Stat cards (2 x 3)
        self._draw_stat_cards(stats, y_top=138)

        # 7. Thin divider
        pygame.draw.line(self.surface, C.PANEL_BORDER_COLOR, (38, 222), (562, 222), 1)

        # 8. High-score section
        self._draw_hs_section(high_scores, highlight_pos, y_title=242)

        # 9. Pulsing restart/quit buttons (below panel)
        self._draw_restart_buttons(tick)

    def update(self):
        pygame.display.update()
