import pygame
import os

# General Game Constants
WALL_COLLISION = False
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 600
GRID_SIZE = 20
GRID_WIDTH = SCREEN_WIDTH // GRID_SIZE
GRID_HEIGHT = SCREEN_HEIGHT // GRID_SIZE

# Level System Constants
LEVEL_2_SCORE = 20
OBSTACLE_REMOVAL_INTERVAL = 4

# Snake Constants
SNAKE_START_LENGTH = 5
SNAKE_START_POS = (GRID_WIDTH // 2, GRID_HEIGHT // 2)  # Start in grid coordinates
SNAKE_START_DIR = (0, 1)  # (dx, dy) -> Down
SNAKE_SPEED_INITIAL = 10  # Ticks per second
SNAKE_COLOR = (0, 150, 0)  # Darker green
SNAKE_HEAD_COLOR = (0, 255, 0)  # Brighter green

# Apple Constants
APPLE_COLOR = (255, 0, 0)  # Red
APPLE_SIZE = (GRID_SIZE, GRID_SIZE)

# Obstacle Constants
OBSTACLE_COLOR = (100, 100, 100)  # Gray
OBSTACLE_SIZE = (GRID_SIZE, GRID_SIZE)

# Sound Constants
SOUND_FOLDER = os.path.join("Files", "Sound")
try:
    APPLE_EAT_SOUND_FILE = os.path.join(SOUND_FOLDER, "apple-eat.wav")
    BITE_SELF_SOUND_FILE = os.path.join(SOUND_FOLDER, "bite-self.wav")
    BITE_OBSTACLE_SOUND_FILE = os.path.join(SOUND_FOLDER, "bite-obstacle.wav")
    REMOVE_OBSTACLE_SOUND_FILE = os.path.join(SOUND_FOLDER, "remove-obstacle.wav")
except FileNotFoundError:
    print("Sound files not found. Ensure the 'Files/Sound' directory exists and contains the required sound files.")
    APPLE_EAT_SOUND_FILE = None
    BITE_SELF_SOUND_FILE = None
    BITE_OBSTACLE_SOUND_FILE = None
    REMOVE_OBSTACLE_SOUND_FILE = None

# UI and Display Constants
BACKGROUND_COLOR = (0, 0, 0)
TEXT_COLOR = (255, 255, 255)
SCORE_POS = (10, 10)
GAME_OVER_POS = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)

# High Score Constants
HIGH_SCORE_FILE = os.path.join("Files", "highscores.txt")  # Use os.path.join for compatibility
NUM_HIGH_SCORES = 5
DEFAULT_HIGH_SCORE_ENTRY = ("Empty Slot", 0)

# Text Input Constants
INPUT_BOX_RECT = pygame.Rect(SCREEN_WIDTH // 4, SCREEN_HEIGHT // 2 + 50, SCREEN_WIDTH // 2, 40)
INPUT_PROMPT_POS = (INPUT_BOX_RECT.centerx, INPUT_BOX_RECT.top - 20)
INPUT_TEXT_COLOR = (0, 0, 0)
INPUT_BOX_COLOR_ACTIVE = pygame.Color('lightskyblue3')
INPUT_BOX_COLOR_INACTIVE = pygame.Color('gray')  # Or use TEXT_COLOR
MAX_NAME_LENGTH = 15
RESTART_PROMPT_POS = (SCREEN_WIDTH // 2, SCREEN_HEIGHT - 40)
