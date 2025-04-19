import pygame
import sys
import random
import os # Import os for path joining
from pygame.locals import *
from pygame import mixer # Import mixer

# Use absolute imports
import constants as C
import high_scores as hs
from game_objects import Snake, Apple, Obstacle
from screen import Screen

class Game:
    """ Manages the game state and main loop """
    def __init__(self):
        pygame.init()
        mixer.init() # Initialize the mixer
        self.screen = Screen() # Uses constants defined in screen.py/constants.py
        self.clock = pygame.time.Clock()
        self.high_scores = hs.load_high_scores() # Uses function from high_scores.py

        # Initialize sound attributes to None
        self.apple_eat_sound = None
        self.bite_self_sound = None
        self.bite_obstacle_sound = None

        # Load sound effects individually
        try:
            self.apple_eat_sound = mixer.Sound(C.APPLE_EAT_SOUND_FILE)
        except pygame.error as e:
            print(f"Warning: Could not load apple eat sound ({C.APPLE_EAT_SOUND_FILE}): {e}")

        try:
            self.bite_self_sound = mixer.Sound(C.BITE_SELF_SOUND_FILE)
        except pygame.error as e:
            print(f"Warning: Could not load bite self sound ({C.BITE_SELF_SOUND_FILE}): {e}")

        try:
            self.bite_obstacle_sound = mixer.Sound(C.BITE_OBSTACLE_SOUND_FILE)
        except pygame.error as e:
            print(f"Warning: Could not load bite obstacle sound ({C.BITE_OBSTACLE_SOUND_FILE}): {e}")

        self.reset()

    def _get_occupied_positions(self):
        """ Returns a list of grid coordinates occupied by the snake and obstacles. """
        occupied = list(self.snake.positions) # Snake body positions
        occupied.extend([(ob.x, ob.y) for ob in self.obstacles]) # Obstacle positions
        return occupied

    def _create_initial_apple(self):
        """ Creates the first apple, ensuring it doesn't spawn on snake/obstacles. """
        apple = Apple(0, 0) # Initial dummy position
        apple.respawn(self._get_occupied_positions())
        return apple

    def _add_obstacle(self):
        """ Adds a new obstacle in a random, unoccupied grid location. """
        while True:
            x = random.randint(0, C.GRID_WIDTH - 1)
            y = random.randint(0, C.GRID_HEIGHT - 1)
            new_obstacle_pos = (x, y)

            # Check against snake, existing obstacles, and the apple
            occupied = self._get_occupied_positions()
            occupied.append((self.apple.x, self.apple.y)) # Include apple position

            if new_obstacle_pos not in occupied:
                self.obstacles.append(Obstacle(x, y))
                break

    def handle_events(self):
        """ Processes player input and game events. """
        for event in pygame.event.get():
            if event.type == QUIT:
                self.running = False
            elif event.type == KEYDOWN:
                if event.key == K_UP or event.key == K_w:
                    self.snake.change_direction((0, -1))
                elif event.key == K_DOWN or event.key == K_s:
                    self.snake.change_direction((0, 1))
                elif event.key == K_LEFT or event.key == K_a:
                    self.snake.change_direction((-1, 0))
                elif event.key == K_RIGHT or event.key == K_d:
                    self.snake.change_direction((1, 0))
                elif event.key == K_ESCAPE:
                    self.running = False # Allow quitting during gameplay

    def update_game_state(self):
        """ Updates the position of the snake. """
        if not self.snake.move(): # move() returns False on collision (self or wall if enabled)
            if self.bite_self_sound: 
                self.bite_self_sound.play()
            self.game_over()

    def check_collisions(self):
        """ Checks for collisions between game objects. """
        # Snake eating apple
        if self.snake.collides_with_rect(self.apple.rect):
            self.score += 1
            self.snake.grow()
            if self.apple_eat_sound: 
                self.apple_eat_sound.play()
            self._add_obstacle() # Add obstacle when apple is eaten
            # Respawn apple, ensuring it's not on the new obstacle or snake
            self.apple.respawn(self._get_occupied_positions())

        # Snake hitting obstacles
        if self.snake.collides_with_obstacles(self.obstacles):
            if self.bite_obstacle_sound: 
                self.bite_obstacle_sound.play()
            self.game_over()

        # Wall collision check (only if WALL_COLLISION is True in constants)
        # Note: The wall collision logic is now primarily handled within snake.move()
        # This section might be redundant if snake.move() already returns False on wall hit.
        # if C.WALL_COLLISION:
        #     head_x, head_y = self.snake.get_head_position()
        #     if not (0 <= head_x < C.GRID_WIDTH and 0 <= head_y < C.GRID_HEIGHT):
        #         self.game_over()


    def draw(self):
        """ Draws all game elements onto the screen. """
        self.screen.clear()
        self.screen.draw_element(self.snake)
        self.screen.draw_element(self.apple)
        for obstacle in self.obstacles:
            self.screen.draw_element(obstacle)
        self.screen.draw_score(self.score)
        self.screen.update()

    def check_and_update_high_scores(self, current_score):
        """ Checks if the current score qualifies for the high score list. """
        insert_pos = -1
        # Find the position where the new score should be inserted
        for i in range(len(self.high_scores)):
            if current_score > self.high_scores[i][1]:
                insert_pos = i
                break
        # If score is lower than all existing scores, but there's space
        if insert_pos == -1 and len(self.high_scores) < C.NUM_HIGH_SCORES:
             insert_pos = len(self.high_scores)

        # If the score doesn't make it into the top N scores
        if insert_pos == -1 or insert_pos >= C.NUM_HIGH_SCORES:
             return -1 # Indicate no high score achieved or list is full

        return insert_pos # Return the index where the score should be inserted


    def get_player_name(self):
        """ Handles the text input screen for entering a high score name. """
        player_name = ""
        input_active = True
        prompt = f"High Score! Enter Name (max {C.MAX_NAME_LENGTH}):"

        while input_active and self.running: # Check self.running to allow quitting
            self.screen.clear() # Clear screen for input display
            # Draw only the game over message for context
            self.screen.draw_game_over_message(self.score)
            # Draw the input prompt and box
            self.screen.draw_text_input(prompt, player_name, True)
            self.screen.update()

            for event in pygame.event.get():
                if event.type == QUIT:
                    self.running = False # Signal game exit
                    return None # Indicate quit
                if event.type == KEYDOWN:
                    if event.key == K_RETURN:
                        input_active = False # Name submitted
                    elif event.key == K_BACKSPACE:
                        player_name = player_name[:-1]
                    elif event.key == K_ESCAPE:
                        return None # Allow escaping name entry without saving
                    else:
                        # Add character if it's printable and name length is within limit
                        if len(player_name) < C.MAX_NAME_LENGTH and event.unicode.isprintable():
                             # Check isprintable() for safety, though event.unicode usually handles it
                            player_name += event.unicode

        return player_name if player_name else "Anonymous" # Default name if empty


    def game_over(self):
        """ Handles the game over sequence, including high score check and restart prompt. """
        insert_pos = self.check_and_update_high_scores(self.score)

        player_name = None
        if insert_pos != -1: # Qualifies for high score
            player_name = self.get_player_name()
            if player_name is None: # Player quit during name entry
                self.running = False
                return # Exit game over sequence

            # Add new high score entry and save
            new_entry = (player_name, self.score)
            self.high_scores.insert(insert_pos, new_entry)
            # Keep only the top N scores
            if len(self.high_scores) > C.NUM_HIGH_SCORES:
                self.high_scores.pop()
            hs.save_high_scores(C.HIGH_SCORE_FILE, self.high_scores)
            # Reload high scores after saving to ensure the list displayed is current
            self.high_scores = hs.load_high_scores()

        # Display final game over screen with scores and restart prompt
        self.screen.clear()
        # Use the new separated drawing methods
        self.screen.draw_game_over_message(self.score)
        self.screen.draw_high_score_list(self.high_scores) # Draw the list now
        self.screen.show_restart_prompt()
        self.screen.update()

        # Wait for player input to restart or quit
        waiting_for_input = True
        while waiting_for_input and self.running:
            self.clock.tick(15) # Lower tick rate for game over screen
            for event in pygame.event.get():
                if event.type == QUIT:
                    self.running = False
                    waiting_for_input = False
                elif event.type == KEYDOWN:
                    if event.key == K_ESCAPE:
                        self.running = False # Quit on ESC
                    # Any other key press restarts the game
                    waiting_for_input = False # Exit loop to restart or quit

        # If the game is still running (i.e., didn't quit), reset for a new game
        if self.running:
            self.reset()


    def reset(self):
        """ Resets the game state for a new game. """
        self.snake = Snake()
        self.obstacles = [] # Start with no obstacles
        self.apple = self._create_initial_apple()
        self.score = 0
        self.game_speed = C.SNAKE_SPEED_INITIAL
        # self.running should already be True if reset is called from game_over
        # If called initially, set it here.
        self.running = True


    def run(self):
        """ Starts and runs the main game loop. """
        while self.running:
            self.clock.tick(self.game_speed) # Control game speed
            self.handle_events()
            # Only update and draw if the game is still running after event handling
            if self.running:
                self.update_game_state()
                # Check collisions only if game state update didn't end the game
                if self.running:
                    self.check_collisions()
                    # Draw only if collision checks didn't end the game
                    if self.running:
                        self.draw()

        # Clean up pygame resources when the loop ends
        mixer.quit() # Quit the mixer
        pygame.quit()
        # sys.exit() # Consider if this is needed, depends on application structure
