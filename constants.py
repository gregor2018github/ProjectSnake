import pygame
import os

# General Game Constants
WALL_COLLISION = False
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 600
GRID_SIZE = 20
GRID_WIDTH = SCREEN_WIDTH // GRID_SIZE
GRID_HEIGHT = SCREEN_HEIGHT // GRID_SIZE

# Particle Effects Constants
PARTICLE_COUNT = 15  # Number of particles per effect
PARTICLE_MIN_SIZE = 1
PARTICLE_MAX_SIZE = 5
PARTICLE_MIN_SPEED = 0.4
PARTICLE_MAX_SPEED = 0.95
PARTICLE_LIFESPAN = 20  # Duration in ticks
PARTICLE_COLORS = [(255, 0, 0), (255, 50, 0), (255, 20, 20)]  # Variations of red

# Level System Constants
LEVEL_2_SCORE = 5
LEVEL_3_SCORE = 10
LEVEL_4_SCORE = 15
OBSTACLE_REMOVAL_INTERVAL = 4 # every x ticks one obstacle is removed

# Snake Constants
SNAKE_USE_FLOAT_MOVEMENT = False # Set to True for smooth snake movement
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

# Moving Obstacle Constants
MOVING_OBSTACLE_USE_FLOAT_COLLISION = True # Set to True for smooth snake/moving_obstacle collision
MOVING_OBSTACLE_COLOR = (120, 100, 140)  # Orange
MOVING_OBSTACLE_SIZE = (GRID_SIZE, GRID_SIZE)
MOVING_OBSTACLE_SPEED = 0.1  # Grid cells per frame

# Sound Constants
SOUND_FOLDER = os.path.join("Files", "Sound")

def get_sound_file_path(folder, filename):
    """Helper function to safely get sound file path."""
    file_path = os.path.join(folder, filename)
    if not os.path.exists(file_path):
        print(f"Warning: Sound file not found: {file_path}")
        return None
    return file_path

APPLE_EAT_SOUND_FILE = get_sound_file_path(SOUND_FOLDER, "apple-eat.wav")
BITE_SELF_SOUND_FILE = get_sound_file_path(SOUND_FOLDER, "bite-self.wav")
BITE_OBSTACLE_SOUND_FILE = get_sound_file_path(SOUND_FOLDER, "bite-obstacle.wav")
REMOVE_OBSTACLE_SOUND_FILE = get_sound_file_path(SOUND_FOLDER, "remove-obstacle.wav")

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
