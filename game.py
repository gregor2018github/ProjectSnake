import pygame
import sys
import random
import os # Import os for path joining
from pygame.locals import *
from pygame import mixer # Import mixer
from time import sleep

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
        self.next_direction = None # Buffer for the next direction change

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

    def _add_obstacle(self, obstacle_type="static"):
        """
        Adds a new obstacle of the specified type in a random, unoccupied grid location.
        
        Args:
            obstacle_type: String indicating the type of obstacle to create.
                "static" - Static obstacle for level 1
                "orthogonal" - Orthogonally moving obstacle for level 2
                "diagonal" - Diagonally moving obstacle for level 3
        """
        # Map obstacle types to their classes and effect types
        obstacle_map = {
            "static": {"class": Obstacle, "effect_type": "obstacle_static", "list": self.obstacles},
            "orthogonal": {"class": OrthogonalMovingObstacle, "effect_type": "obstacle_orthogonal", "list": self.moving_obstacles},
            "diagonal": {"class": MovingObstacle, "effect_type": "obstacle_diagonal", "list": self.moving_obstacles}
        }
        
        # Get the corresponding settings for this obstacle type
        obstacle_settings = obstacle_map.get(obstacle_type)
        if not obstacle_settings:
            print(f"Warning: Unknown obstacle type '{obstacle_type}'")
            return
        
        # Find a suitable location
        while True:
            x = random.randint(0, C.GRID_WIDTH - 1)
            y = random.randint(0, C.GRID_HEIGHT - 1)
            new_pos = (x, y)
            
            # Check against snake, existing obstacles, and the apple
            occupied = self._get_occupied_positions()
            occupied.append((self.apple.x, self.apple.y))
            
            # Get snake head position for distance check
            head_x, head_y = self.snake.get_head_position()
            
            # Calculate Manhattan distance from snake head
            distance_from_head = abs(x - head_x) + abs(y - head_y)
            
            if new_pos not in occupied and distance_from_head >= C.MIN_OBSTACLE_SPAWN_DISTANCE:
                # Create the obstacle
                obstacle = obstacle_settings["class"](x, y)
                # Add to the appropriate list
                obstacle_settings["list"].append(obstacle)
                # Create spawn effect
                self.particle_effects.append(ParticleEffect(x, y, obstacle_settings["effect_type"], is_spawning=True))
                break

    def _check_level_update(self):
        """Checks if the player should advance to the next level"""
        previous_level = self.level
        
        if self.level == 1 and self.score >= C.LEVEL_2_SCORE:
            self.level = 2
            # Flag to start removing static obstacles when transitioning to level 2
            self.removing_static_obstacles = True
        elif self.level == 2 and self.score >= C.LEVEL_3_SCORE:
            self.level = 3
            # Flag to start removing orthogonal obstacles when transitioning to level 3
            self.removing_orthogonal_obstacles = True
        elif self.level == 3 and self.score >= C.LEVEL_4_SCORE:
            self.level = 4
            # Flag to start removing diagonal obstacles when transitioning to level 4
            self.removing_diagonal_obstacles = True

    def _update_level_mechanics(self):
        """Updates level-specific mechanics"""
        if self.level == 2:
            # In level 2, remove static obstacles with dust particles
            if len(self.obstacles) > 0 and self.frame_counter % C.OBSTACLE_REMOVAL_INTERVAL == 0:
                obstacle_to_remove = self.obstacles.pop(0)  # Remove the first obstacle
                if self.remove_obstacle_sound:
                    self.remove_obstacle_sound.play()
                # Create dust particles for obstacle removal (is_spawning=False)
                self.particle_effects.append(ParticleEffect(obstacle_to_remove.x, obstacle_to_remove.y, "obstacle_static", is_spawning=False))
        
        # Handle orthogonal obstacle removal with dust particles
        if self.removing_orthogonal_obstacles and self.frame_counter % C.MOVING_OBSTACLE_REMOVAL_INTERVAL == 0:
            orthogonal_obstacles = [obstacle for obstacle in self.moving_obstacles 
                                    if isinstance(obstacle, OrthogonalMovingObstacle)]
            if orthogonal_obstacles:
                # Remove the first orthogonal obstacle
                obstacle_to_remove = orthogonal_obstacles[0]
                self.moving_obstacles.remove(obstacle_to_remove)
                # Play removal sound
                if self.remove_obstacle_sound:
                    self.remove_obstacle_sound.play()
                # Create dust particles for removal
                self.particle_effects.append(ParticleEffect(obstacle_to_remove.x, obstacle_to_remove.y, "obstacle_orthogonal", is_spawning=False))
            else:
                self.removing_orthogonal_obstacles = False
        
        # Handle diagonal obstacle removal with dust particles
        if hasattr(self, 'removing_diagonal_obstacles') and self.removing_diagonal_obstacles and self.frame_counter % C.MOVING_OBSTACLE_REMOVAL_INTERVAL == 0:
            diagonal_obstacles = [obstacle for obstacle in self.moving_obstacles 
                                if isinstance(obstacle, MovingObstacle) and not isinstance(obstacle, OrthogonalMovingObstacle)]
            if diagonal_obstacles:
                # Remove the first diagonal obstacle
                obstacle_to_remove = diagonal_obstacles[0]
                self.moving_obstacles.remove(obstacle_to_remove)
                # Play removal sound
                if self.remove_obstacle_sound:
                    self.remove_obstacle_sound.play()
                # Create dust particles for removal
                self.particle_effects.append(ParticleEffect(obstacle_to_remove.x, obstacle_to_remove.y, "obstacle_diagonal", is_spawning=False))
            else:
                self.removing_diagonal_obstacles = False
                
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
                new_dir = None
                if event.key == K_UP or event.key == K_w:
                    new_dir = (0, -1)
                elif event.key == K_DOWN or event.key == K_s:
                    new_dir = (0, 1)
                elif event.key == K_LEFT or event.key == K_a:
                    new_dir = (-1, 0)
                elif event.key == K_RIGHT or event.key == K_d:
                    new_dir = (1, 0)
                elif event.key == K_ESCAPE:
                    self.running = False # Allow quitting during gameplay

                if new_dir:
                    # Store the intended direction instead of changing immediately
                    self.next_direction = new_dir

    def update_game_state(self):
        """ Updates the position of the snake. """
        # Apply the buffered direction change before moving
        if self.next_direction:
            self.snake.change_direction(self.next_direction)
            self.next_direction = None # Clear the buffer

        if not self.snake.move(): # move() returns False on collision (self or wall if enabled)
            # Check if the collision was with self
            head = self.snake.get_head_position()
            if head in self.snake.positions[1:]: # Check against body segments
                if self.bite_self_sound:
                    self.bite_self_sound.play()
            self.game_over()
            return # Stop further updates if game over occurred

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
                
            # Level-specific behaviors when apple is eaten
            if self.level == 1:
                self._add_obstacle("static")
            elif self.level == 2:
                self._add_obstacle("orthogonal")
            elif self.level == 3:
                self._add_obstacle("diagonal")
                
            # Store old apple position to create dust effect
            old_x, old_y = self.apple.x, self.apple.y
                
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
    
    def wait_for_enter(self):
        """Game pauses and awaits 'Enter'. Other buttons cannot be pressed."""
        self.running = False # Pause the game loop
        # Print to the bottom of the screen "Press Enter to continue..."
        self.screen.draw_bottom_message(message="Press ENTER to continue...", size=20)
        self.screen.update()
        waiting_for_input = True
        while waiting_for_input:
            self.clock.tick(15)  # Lower tick rate for game over screen
            for event in pygame.event.get():
                if event.type == QUIT:
                    self.running = False
                    waiting_for_input = False
                elif event.type == KEYDOWN:
                    if event.key == K_RETURN:
                        waiting_for_input = False  # Exit waiting loop
                        self.running = True  # Ensure game continues

    def game_over(self):
        """ Handles the game over sequence, including high score check and restart prompt. """
        self.running = False # Stop the main game loop
        self.wait_for_enter()
        self.running = True # Allow the game to continue for restart or quit
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
        self.next_direction = None # Reset direction buffer
        # Flag to track if we need to remove orthogonal obstacles gradually
        self.removing_orthogonal_obstacles = False
        self.orthogonal_removal_counter = 0
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
