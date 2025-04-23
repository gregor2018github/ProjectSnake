import pygame
import sys
import random
import os # Import os for path joining
from pygame.locals import *
from pygame import mixer # Import mixer

# Use absolute imports
import constants as C
import high_scores as hs
from game_objects import Snake, Apple, Obstacle, MovingObstacle, ParticleEffect, OrthogonalMovingObstacle
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
        self.remove_obstacle_sound = None

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
        
        try:
            self.remove_obstacle_sound = mixer.Sound(C.REMOVE_OBSTACLE_SOUND_FILE)
        except pygame.error as e:
            print(f"Warning: Could not load remove obstacle sound ({C.REMOVE_OBSTACLE_SOUND_FILE}): {e}")

        self.reset()

    def _get_occupied_positions(self):
        """ Returns a list of grid coordinates occupied by the snake and obstacles. """
        occupied = list(self.snake.positions) # Snake body positions
        occupied.extend([(ob.x, ob.y) for ob in self.obstacles]) # Obstacle positions
        occupied.extend([(mo.x, mo.y) for mo in self.moving_obstacles])  # Moving obstacle positions
        return occupied

    def _create_initial_apple(self):
        """ Creates the first apple, ensuring it doesn't spawn on snake/obstacles. """
        apple = Apple(0, 0) # Initial dummy position
        apple.respawn(self._get_occupied_positions())
        return apple

    def _add_obstacle(self):
        """ Adds a new obstacle in a random, unoccupied grid location. """
        # Only add static obstacles in level 1
        if self.level != 1:
            return
            
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

    def _add_moving_obstacle(self):
        """ Adds a new moving obstacle in a random, unoccupied grid location. """
        while True:
            x = random.randint(0, C.GRID_WIDTH - 1)
            y = random.randint(0, C.GRID_HEIGHT - 1)
            new_obstacle_pos = (x, y)

            # Check against snake, existing obstacles, and the apple
            occupied = self._get_occupied_positions()
            occupied.append((self.apple.x, self.apple.y)) # Include apple position

            if new_obstacle_pos not in occupied:
                self.moving_obstacles.append(MovingObstacle(x, y))
                break

    def _add_orthogonal_moving_obstacle(self):
        """ Adds a new orthogonal moving obstacle for level 2. """
        while True:
            x = random.randint(0, C.GRID_WIDTH - 1)
            y = random.randint(0, C.GRID_HEIGHT - 1)
            new_pos = (x, y)
            occupied = self._get_occupied_positions()
            occupied.append((self.apple.x, self.apple.y))
            if new_pos not in occupied:
                self.moving_obstacles.append(OrthogonalMovingObstacle(x, y))
                break

    def _check_level_update(self):
        """Checks if the player should advance to the next level"""
        if self.level == 1 and self.score >= C.LEVEL_2_SCORE:
            self.level = 2
        elif self.level == 2 and self.score >= C.LEVEL_3_SCORE:
            self.level = 3
        elif self.level == 3 and self.score >= C.LEVEL_4_SCORE:
            self.level = 4
            
    def _update_level_mechanics(self):
        """Updates level-specific mechanics"""
        if self.level == 2:
            # In level 2, remove an obstacle every OBSTACLE_REMOVAL_INTERVAL frames
            if len(self.obstacles) > 0 and self.frame_counter % C.OBSTACLE_REMOVAL_INTERVAL == 0:
                self.obstacles.pop(0)  # Remove the first obstacle
                if self.remove_obstacle_sound:
                    self.remove_obstacle_sound.play()
        elif self.level == 3:
            # In level 3, remove all orthogonal moving obstacles every OBSTACLE_REMOVAL_INTERVAL frames
            if len(self.moving_obstacles) > 0 and self.frame_counter % C.OBSTACLE_REMOVAL_INTERVAL == 0:
                self.moving_obstacles = [mo for mo in self.moving_obstacles if not isinstance(mo, OrthogonalMovingObstacle)]
                if self.remove_obstacle_sound:
                    self.remove_obstacle_sound.play()
                
        # Update moving obstacles
        for moving_obstacle in self.moving_obstacles:
            moving_obstacle.update(self.snake, self.obstacles)
                
        # Increment frame counter
        self.frame_counter += 1

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
            
        # Check if player advances to next level
        self._check_level_update()
        
        # Apply level-specific mechanics
        self._update_level_mechanics()
        
        # Update particle effects and remove finished ones
        self.particle_effects = [effect for effect in self.particle_effects if effect.update()]

    def check_collisions(self):
        """ Checks for collisions between game objects. """
        # Snake eating apple
        if self.snake.collides_with_rect(self.apple.rect):
            self.score += 1
            self.snake.grow()
            if self.apple_eat_sound: 
                self.apple_eat_sound.play()
                
            # Create particle effect at apple position
            self.particle_effects.append(ParticleEffect(self.apple.x, self.apple.y))
                
            # Level-specific behaviors when apple is eaten
            if self.level == 1:
                self._add_obstacle()
            elif self.level == 2:
                self._add_orthogonal_moving_obstacle()
            elif self.level == 3:
                self._add_moving_obstacle()
                
            # Respawn apple, ensuring it's not on the snake or obstacles
            self.apple.respawn(self._get_occupied_positions())

        # Snake hitting obstacles
        if self.snake.collides_with_obstacles(self.obstacles):
            if self.bite_obstacle_sound: 
                self.bite_obstacle_sound.play()
            self.game_over()
            
        # Snake head hitting moving obstacles
        for moving_obstacle in self.moving_obstacles:
            if moving_obstacle.collides_with_snake_head(self.snake):
                if self.bite_obstacle_sound:
                    self.bite_obstacle_sound.play()
                self.game_over()

    def draw(self):
        """ Draws all game elements onto the screen. """
        self.screen.clear()
        # Draw particle effects
        for effect in self.particle_effects:
            effect.draw(self.screen.surface)
        self.screen.draw_element(self.snake)
        self.screen.draw_element(self.apple)
        for obstacle in self.obstacles:
            self.screen.draw_element(obstacle)
        for moving_obstacle in self.moving_obstacles:
            self.screen.draw_element(moving_obstacle)
            
        self.screen.draw_score(self.score)
        self.screen.draw_level(self.level)
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
                    elif event.key == K_RETURN:
                    # Enter restarts the game
                        waiting_for_input = False # Exit loop to restart or quit

        # If the game is still running (i.e., didn't quit), reset for a new game
        if self.running:
            self.reset()


    def reset(self):
        """ Resets the game state for a new game. """
        self.snake = Snake()
        self.obstacles = [] # Start with no obstacles
        self.moving_obstacles = [] # Start with no moving obstacles
        self.particle_effects = [] # Initialize empty list for particle effects
        self.apple = self._create_initial_apple()
        self.score = 0
        self.level = 1
        self.frame_counter = 0
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
