import pygame
import constants as C # Use absolute import

class Screen:
    """ Handles screen drawing and updates """
    def __init__(self, width=C.SCREEN_WIDTH, height=C.SCREEN_HEIGHT, caption='Snake Game'):
        self.width = width
        self.height = height
        self.surface = pygame.display.set_mode((width, height))
        pygame.display.set_caption(caption)
        # Initialize fonts - consider error handling if font not found
        try:
            self.font = pygame.font.SysFont('Arial', 25)
            self.game_over_font = pygame.font.SysFont('Arial', 40)
            self.high_score_font = pygame.font.SysFont('Arial', 20)
            self.input_font = pygame.font.SysFont('Arial', 25)
            self.prompt_font = pygame.font.SysFont('Arial', 20)
        except pygame.error as e:
            print(f"Warning: Font loading error - {e}. Using default font.")
            # Fallback to default font
            self.font = pygame.font.Font(None, 30)
            self.game_over_font = pygame.font.Font(None, 50)
            self.high_score_font = pygame.font.Font(None, 25)
            self.input_font = pygame.font.Font(None, 30)
            self.prompt_font = pygame.font.Font(None, 25)

    def clear(self):
        self.surface.fill(C.BACKGROUND_COLOR)

    def draw_element(self, element):
        # Assumes element has a 'draw' method that takes the surface
        element.draw(self.surface)

    def draw_score(self, score):
        score_text = self.font.render(f'Score: {score}', True, C.TEXT_COLOR)
        self.surface.blit(score_text, C.SCORE_POS)

    def draw_game_over_message(self, score):
        """Draws only the 'Game Over! Score: X' message."""
        game_over_text = self.game_over_font.render(f'Game Over! Score: {score}', True, C.TEXT_COLOR)
        # Adjust vertical position slightly if needed, maybe higher to accommodate input box later
        text_rect = game_over_text.get_rect(center=(C.GAME_OVER_POS[0], C.GAME_OVER_POS[1] - 100)) # Raised position
        self.surface.blit(game_over_text, text_rect)

    def draw_high_score_list(self, high_scores):
        """Draws only the high score list."""
        # High Scores title
        hs_title_text = self.font.render('High Scores:', True, C.TEXT_COLOR)
        # Position relative to the center or the game over message position
        hs_title_rect = hs_title_text.get_rect(center=(C.GAME_OVER_POS[0], C.GAME_OVER_POS[1] - 50)) # Adjusted position
        self.surface.blit(hs_title_text, hs_title_rect)

        # Display high score entries
        start_y = hs_title_rect.bottom + 15 # Adjusted spacing
        for i, (name, hs_score) in enumerate(high_scores):
            entry_text = self.high_score_font.render(f"{i+1}. {name} - {hs_score}", True, C.TEXT_COLOR)
            entry_rect = entry_text.get_rect(center=(C.GAME_OVER_POS[0], start_y + i * 25))
            self.surface.blit(entry_text, entry_rect)

    def draw_text_input(self, prompt, current_text, active):
        # Draw prompt above the input box
        prompt_surf = self.prompt_font.render(prompt, True, C.TEXT_COLOR)
        # Adjust prompt position based on new game over message position if needed
        prompt_rect = prompt_surf.get_rect(center=C.INPUT_PROMPT_POS)
        self.surface.blit(prompt_surf, prompt_rect)

        # Draw the input box border
        box_color = C.INPUT_BOX_COLOR_ACTIVE if active else C.INPUT_BOX_COLOR_INACTIVE
        pygame.draw.rect(self.surface, box_color, C.INPUT_BOX_RECT, 2) # Draw border only

        # Draw the text entered by the user inside the box
        text_surface = self.input_font.render(current_text, True, C.TEXT_COLOR)
        # Position text slightly inside the box
        text_rect = text_surface.get_rect(midleft=(C.INPUT_BOX_RECT.x + 5, C.INPUT_BOX_RECT.centery))
        # Ensure text doesn't overflow the box visually (optional clipping)
        # pygame.draw.rect(self.surface, C.BACKGROUND_COLOR, C.INPUT_BOX_RECT) # Clear inside box first if needed
        self.surface.blit(text_surface, text_rect)

    def show_restart_prompt(self):
        prompt_text = self.prompt_font.render("Press any key to restart (ESC to quit)", True, C.TEXT_COLOR)
        prompt_rect = prompt_text.get_rect(center=C.RESTART_PROMPT_POS)
        self.surface.blit(prompt_text, prompt_rect)

    def update(self):
        pygame.display.update()
