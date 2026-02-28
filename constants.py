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
PARTICLE_COLORS_OBSTACLE_SEEKER = [(210, 55, 55), (235, 80, 60), (185, 35, 35)]         # Crimson red variations

# Circular Pulse Effect Constants
PULSE_MIN_RADIUS = 3
PULSE_MAX_RADIUS = 30
PULSE_GROWTH_RATE = 1.5  # How fast the pulse grows per frame
PULSE_LINE_WIDTH = 2  # Width of the pulse circle line
PULSE_LIFESPAN = 15  # How many frames the pulse lasts
PULSE_COUNT = 3  # Number of pulse circles per effect

# Level System Constants
LEVEL_2_APPLES = 10   # normal apples eaten to reach level 2
LEVEL_3_APPLES = 20   # normal apples eaten to reach level 3
LEVEL_4_APPLES = 35   # normal apples eaten to reach level 4 (seeker enemies)
LEVEL_5_APPLES = 55   # normal apples eaten to reach the end-level (all types spawn randomly)
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

MAGIC_APPLE_COLOR = (255, 215, 0)  # Gold
MAGIC_APPLE_SIZE = (GRID_SIZE, GRID_SIZE)
MAGIC_APPLE_TYPES = [
    "increase_tick_speed", "decrease_tick_speed", "ghost_mode", "no_grow",
    "double_score", "freeze_obstacles", "shrink", "shield", "manual_control",
    "color_invert", "spawn_enemies", "darkness",
]
MAGIC_APPLE_SPAWN_PROBABILITY = 0.1  # Probability of spawning a magic apple when eating a normal apple
MAGIC_APPLE_LIFESPAN = 50  # Lifespan in ticks

# Magic Apple Buff Durations (in ticks)
BUFF_DURATION_SPEED_UP = 120
BUFF_DURATION_SPEED_DOWN = 120
BUFF_DURATION_GHOST = 100
BUFF_DURATION_NO_GROW = 80
BUFF_DURATION_DOUBLE_SCORE = 300
BUFF_DURATION_FREEZE = 70
SHIELD_HITS = 3             # obstacle hits the shield absorbs before breaking
BUFF_MANUAL_MOVES = 20      # key-presses the manual control buff lasts
BUFF_DURATION_INVERT = 90   # ticks the color-invert buff lasts
BUFF_SPAWN_ENEMIES_COUNT = 5        # number of enemies the spawn_enemies buff creates
BUFF_SPAWN_ENEMIES_LIFESPAN = 100   # ticks before spawned enemies despawn

# Combo Multiplier
COMBO_WINDOW = 30       # ticks the player has to eat the next apple and keep the chain
COMBO_MAX_MULT = 4      # highest score multiplier tier (×1, ×2, ×3, ×4)

# Darkness Buff
BUFF_DURATION_DARKNESS = 80  # ticks the darkness buff lasts
DARKNESS_RADIUS = 90         # px radius of the visible circle around the snake head

# Buff HUD display info: buff_key -> (label, RGB color)
BUFF_DISPLAY_NAMES = {
    'increase_tick_speed': ('Speed+',  (220,  80,  80)),   # bad – red
    'decrease_tick_speed': ('Slow',    ( 80, 220,  80)),   # good – green
    'ghost_mode':          ('Ghost',   (120, 180, 255)),
    'no_grow':             ('No Grow', ( 80, 220,  80)),
    'double_score':        ('x2 Score',(255, 200,   0)),
    'freeze_obstacles':    ('Freeze',  (160, 230, 255)),
    'shield':              ('Shield',  (100, 180, 255)),
    'shrink':              ('Shrink!', (200, 100, 255)),
    'manual_control':      ('Manual',  (255, 165,   0)),   # orange
    'color_invert':        ('Invert',  (220,   0, 220)),   # magenta
    'spawn_enemies':       ('Swarm!',  (255,  80,  40)),   # orange-red
    'darkness':            ('Darkness',(60,   60, 180)),   # deep blue
}

# Obstacle Constants
OBSTACLE_COLOR = (100, 100, 100)  # Gray
OBSTACLE_SIZE = (GRID_SIZE, GRID_SIZE)
MIN_OBSTACLE_SPAWN_DISTANCE = 5  # Minimum distance from the snake head to spawn obstacles

# Moving Obstacle Constants
MOVING_OBSTACLE_USE_FLOAT_COLLISION = True # Set to True for smooth snake/moving_obstacle collision
MOVING_OBSTACLE_COLOR_DIAGONAL = (150, 110, 200)   # Brighter purple for diagonal obstacles
MOVING_OBSTACLE_COLOR_ORTHOGONAL = (220, 120, 60)  # Orange-amber for orthogonal obstacles
MOVING_OBSTACLE_COLOR_SEEKER = (210, 55, 55)       # Crimson red for homing seeker obstacles
MOVING_OBSTACLE_SIZE = (GRID_SIZE, GRID_SIZE)
MOVING_OBSTACLE_SPEED = 0.1   # Grid cells per frame
SEEKER_OBSTACLE_SPEED = 0.12  # Slightly faster than regular moving obstacles
SEEKER_TURN_RATE_SCALE = 0.60 # Turn rate = SCALE / dist; seeker is passive far away, aggressive up close
SEEKER_TURN_RATE_MAX  = 0.35  # Cap so the seeker never snap-turns at point-blank range

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
MAGIC_APPLE_EAT_SOUND_FILE = get_sound_file_path(SOUND_FOLDER, "magic-apple-eat.wav")
MAGIC_APPLE_EAT_SOUND_FILES = [
    get_sound_file_path(SOUND_FOLDER, "magic_1.mp3"),
    get_sound_file_path(SOUND_FOLDER, "magic_2.mp3"),
    get_sound_file_path(SOUND_FOLDER, "magic_3.mp3"),
    get_sound_file_path(SOUND_FOLDER, "magic_4.mp3"),
]
BITE_SELF_SOUND_FILE = get_sound_file_path(SOUND_FOLDER, "bite-self.wav")
BITE_OBSTACLE_SOUND_FILE = get_sound_file_path(SOUND_FOLDER, "bite-obstacle.wav")
REMOVE_OBSTACLE_SOUND_FILE = get_sound_file_path(SOUND_FOLDER, "remove-obstacle.wav")

# Death-screen wave animation
WAVE_SPAWN_INTERVAL = 70    # frames between new ripple waves
WAVE_SPEED = 7              # pixels the wave radius grows per frame
WAVE_MAX_RADIUS = 900       # radius at which a wave is discarded

# UI and Display Constants
BACKGROUND_COLOR = (0, 0, 0)
GRID_LINE_COLOR = (12, 12, 12)      # Barely-visible grid overlay
TEXT_COLOR = (255, 255, 255)
TEXT_DIM_COLOR = (180, 180, 180)    # Secondary / caption text
SCORE_POS = (10, 10)

# Death / Game-over screen colours
GAMEOVER_TITLE_COLOR = (220, 50, 50)       # Bold red "Game Over!" title
GAMEOVER_SCORE_COLOR = (255, 200, 80)      # Warm amber for the score
PANEL_BG_RGBA = (15, 15, 30, 210)          # Deep-dark blue panel background
PANEL_BORDER_COLOR = (70, 70, 120)         # Subtle blue panel border

# High-score rank medal colours
HS_RANK_GOLD   = (255, 215,   0)
HS_RANK_SILVER = (200, 200, 200)
HS_RANK_BRONZE = (205, 127,  50)
HS_HIGHLIGHT   = (255, 255, 120)           # Newly set score

# Prompt / restart colours
PROMPT_COLOR   = (160, 160, 160)           # Dimmed prompt text

# Snake Visual Constants
SNAKE_SEGMENT_INSET = 1             # px inset on each side of every segment rect
SNAKE_EYE_RADIUS = 2                # px radius of each eye dot
SNAKE_GHOST_ALPHA = 80              # alpha of snake during ghost mode (0-255)

# Apple Visual Constants
APPLE_HIGHLIGHT_COLOR = (255, 255, 200)  # Warm-white highlight dot
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
    "That was not bad, but then you lost.",
    "Listen... the sound of failure.",
    "This sound... it's the sound of defeat.",
    "Tragic...",
    "I know, certainly not your fault.",
    "Anyone home?",
    "Hello? Is anyone even there?",
    "Looks like it's just you and your thoughts now.",
    "Man, this is awkward...",
    "All you had to do was follow the damn train, CJ.",
    "All other three directions seemed safer...",
    "Well, that escalated quickly.",
    "Surprise! You died.",
    "Pack it up, you're done.",
    "Wow, so fast back to the start.",
    "Looks like you really know how to make an exit.",
    "And just like that, it's game over.",
    "If you don't put in the effort, you won't see results.",
    "I don't know how to sugarcoat this..."
]
