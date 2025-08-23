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
PARTICLE_COLORS_APPLE = [(255, 0, 0), (255, 50, 0), (255, 20, 20)]  # Variations of red
PARTICLE_COLORS_OBSTACLE_STATIC = [(130, 130, 130), (160, 160, 160), (100, 100, 100)]  # Gray variations
PARTICLE_COLORS_OBSTACLE_ORTHOGONAL = [(220, 120, 60), (240, 140, 80), (200, 100, 40)]  # Orange variations
PARTICLE_COLORS_OBSTACLE_DIAGONAL = [(150, 110, 200), (170, 130, 220), (130, 90, 180)]  # Purple variations

# Circular Pulse Effect Constants
PULSE_MIN_RADIUS = 3
PULSE_MAX_RADIUS = 30
PULSE_GROWTH_RATE = 1.5  # How fast the pulse grows per frame
PULSE_LINE_WIDTH = 2  # Width of the pulse circle line
PULSE_LIFESPAN = 15  # How many frames the pulse lasts
PULSE_COUNT = 3  # Number of pulse circles per effect

# Level System Constants
LEVEL_2_SCORE = 25
LEVEL_3_SCORE = 45
LEVEL_4_SCORE = 65
OBSTACLE_REMOVAL_INTERVAL = 4 # every x ticks one obstacle is removed
MOVING_OBSTACLE_REMOVAL_INTERVAL = 4 # ticks between removing orthogonal obstacles

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
MIN_OBSTACLE_SPAWN_DISTANCE = 5  # Minimum distance from the snake head to spawn obstacles

# Moving Obstacle Constants
MOVING_OBSTACLE_USE_FLOAT_COLLISION = True # Set to True for smooth snake/moving_obstacle collision
MOVING_OBSTACLE_COLOR_DIAGONAL = (150, 110, 200)  # Brighter purple for diagonal obstacles
MOVING_OBSTACLE_COLOR_ORTHOGONAL = (220, 120, 60)  # Orange-amber for orthogonal obstacles
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

# Messages
Death_Messages = [
    "Oh no!",
    "You really should not do that.",
    "Well, that was unexpected!",
    "Try to be more careful next time.",
    "Angry yet?",
    "Just a little bit more effort next time.",
    "Hint: Hit the apple next time!",
    "The last move was a bit questionable.",
    "How often do you plan on making this mistake?",
    "Snake.exe has stopped working.",
    "Well, that's one way to end world hunger.",
    "Achievement unlocked: Creative ways to disappoint.",
    "Breaking news: Local snake forgets how to snake.",
    "Error 404: Survival instinct not found.",
    "Your snake has chosen violence... against itself.",
    "Roses are red, violets are blue, your snake is dead, and so are you.",
    "Have you considered a career in professional losing?",
    "Snake.exe has encountered an unexpected user.",
    "Did someone forget to tell you that you cannot eat everything?",
    "Your snake just rage-quit life.",
    "That's what we call a 'pro gamer move' (not really).",
    "Have you tried turning yourself off and on again?",
    "Your snake has left to find a more competent player.",
    "Smoking Ben Affleck meme? Yes, that is your snake right now.",
    "It's not even funny anymore.",
    "Hint: The goal is NOT to see this screen.",
    "You lost, again.",
    "Are you collecting these death messages?",
    "Try to avoid the obstacles for starters.",
    "Have you tried not running into things?",
    "Wow, you're really good at dying.",
    "Just a little bit more effort next time.",
    "Are you even trying?",
    "Maybe practice would help, just a suggestion.",
    "Reflexes fade in high age, it's ok.",
    "That was fast...",
    "At least you made it to the game over screen.",
    "Ouch!",
    "You did not see that coming, did you?",
    "There are other hobbies out there, you know?",
    "Crash test dummy reporting for duty.",
    "This is why we can't have nice things.",
    "Remember, it's just a game... sort of.",
    "Do you really try or is that trolling?",
    "That was not bad, but then you lost."
]
