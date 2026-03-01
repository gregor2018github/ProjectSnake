import pygame
import random
import math
from pygame.locals import *
from pygame import mixer # Import mixer
from time import sleep

# Use absolute imports
import constants as C
import high_scores as hs
import magic_apple_logic as mal
from game_objects import Snake, Apple, MagicApple, Obstacle, MovingObstacle, ParticleEffect, OrthogonalMovingObstacle, SeekerObstacle, BuffAnnouncement, ShockwaveEffect, LevelDoor
from screen import Screen

class Game:
    """ Manages the game state and main loop """
    def __init__(self, test_buff=None, start_level=1):
        pygame.init()
        mixer.init() # Initialize the mixer
        self.screen = Screen() # Uses constants defined in screen.py/constants.py
        self.clock = pygame.time.Clock()
        self.high_scores = hs.load_high_scores() # Uses function from high_scores.py
        self.test_buff = test_buff   # if set, force this magic apple type after the 1st apple
        self.start_level = max(1, min(start_level, 5))  # clamped to valid range
        self.gameover = False

        # Initialize sound attributes to None
        self.apple_eat_sound = None
        self.magic_apple_eat_sound = None
        self.magic_apple_eat_sounds = []   # list of 4 random magic sounds
        self.bite_self_sound = None
        self.bite_obstacle_sound = None
        self.remove_obstacle_sound = None
        self.whoosh_sound = None
        self.next_direction = None # Buffer for the next direction change

        # Load sound effects individually
        try:
            self.apple_eat_sound = mixer.Sound(C.APPLE_EAT_SOUND_FILE)
        except pygame.error as e:
            print(f"Warning: Could not load apple eat sound ({C.APPLE_EAT_SOUND_FILE}): {e}")

        try:
            self.magic_apple_eat_sound = mixer.Sound(C.MAGIC_APPLE_EAT_SOUND_FILE)
        except pygame.error as e:
            print(f"Warning: Could not load magic apple eat sound ({C.MAGIC_APPLE_EAT_SOUND_FILE}): {e}")

        for path in C.MAGIC_APPLE_EAT_SOUND_FILES:
            if path:
                try:
                    self.magic_apple_eat_sounds.append(mixer.Sound(path))
                except pygame.error as e:
                    print(f"Warning: Could not load magic sound ({path}): {e}")

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

        try:
            self.whoosh_sound = mixer.Sound(C.WHOOSH_SOUND_FILE)
            self.whoosh_sound.set_volume(0.7)
        except pygame.error as e:
            print(f"Warning: Could not load whoosh sound ({C.WHOOSH_SOUND_FILE}): {e}")

        self.reset()

    def _apply_start_level(self):
        """Pre-configure game state to match the requested start_level.
        Sets apples_eaten to the level threshold, updates level tracking,
        and spawns a small set of representative obstacles so the field
        immediately reflects that level's difficulty."""
        if self.start_level <= 1:
            return

        level_thresholds = {
            2: C.LEVEL_2_APPLES,
            3: C.LEVEL_3_APPLES,
            4: C.LEVEL_4_APPLES,
            5: C.LEVEL_5_APPLES,
        }
        self.level = self.start_level
        self.max_level_reached = self.start_level
        self.apples_eaten = level_thresholds.get(self.start_level, C.LEVEL_5_APPLES)

        # Spawn a small representative set of obstacles for immediate level feel
        if self.start_level == 2:
            for _ in range(4):
                self._add_obstacle("orthogonal")
        elif self.start_level == 3:
            for _ in range(3):
                self._add_obstacle("orthogonal")
            for _ in range(3):
                self._add_obstacle("diagonal")
        elif self.start_level == 4:
            for _ in range(4):
                self._add_obstacle("seeker")
        elif self.start_level == 5:
            for _ in range(2):
                self._add_obstacle("seeker")
            for _ in range(2):
                self._add_obstacle("diagonal")
            self._add_obstacle("orthogonal")

    def _get_occupied_positions(self):
        """ Returns a list of grid coordinates occupied by the snake and obstacles. """
        occupied = list(self.snake.positions)
        for ob in self.obstacles:
            occupied.extend(ob.cells)          # all cells of multi-cell static obstacles
        for mo in self.moving_obstacles:
            occupied.extend(mo.cells)          # all cells of multi-cell moving obstacles
        return occupied

    def _create_initial_apple(self):
        """ Creates the first apple, ensuring it doesn't spawn on snake/obstacles. Subsequent apple spawning is defined in the Apple class."""
        apple = Apple(0, 0) # Initial dummy position
        apple.respawn(self._get_occupied_positions())
        return apple
    
    def _add_magic_apple(self, force_type=None):
        """ Adds a magic apple to the game at a random unoccupied position.
        If force_type is given, that buff type is used instead of a random one. """
        while True:
            x = random.randint(0, C.GRID_WIDTH - 1)
            y = random.randint(0, C.GRID_HEIGHT - 1)
            new_pos = (x, y)
            
            # Check against snake, existing obstacles, and the regular apple
            occupied = self._get_occupied_positions()
            occupied.append((self.apple.x, self.apple.y))
            
            # Get snake head position for distance check
            head_x, head_y = self.snake.get_head_position()
            
            # Calculate Manhattan distance from snake head
            distance_from_head = abs(x - head_x) + abs(y - head_y)
            
            if new_pos not in occupied and distance_from_head >= C.MIN_OBSTACLE_SPAWN_DISTANCE:
                # Create the magic apple
                magic_apple = MagicApple(x, y, force_type=force_type)
                self.magic_apples.append(magic_apple)
                break

    def _add_obstacle(self, obstacle_type="static", lifespan=None):
        """
        Adds a new obstacle of the specified type in a random, unoccupied grid location.
        Static and orthogonal types pick a random multi-cell shape from OBSTACLE_SHAPES
        and validate every cell before placing. Diagonal and seeker remain single-cell.
        """
        obstacle_map = {
            "static":     {"class": Obstacle,                  "effect_type": "obstacle_static",     "list": self.obstacles},
            "orthogonal": {"class": OrthogonalMovingObstacle,  "effect_type": "obstacle_orthogonal", "list": self.moving_obstacles},
            "diagonal":   {"class": MovingObstacle,            "effect_type": "obstacle_diagonal",   "list": self.moving_obstacles},
            "seeker":     {"class": SeekerObstacle,            "effect_type": "obstacle_seeker",     "list": self.moving_obstacles},
        }

        obstacle_settings = obstacle_map.get(obstacle_type)
        if not obstacle_settings:
            print(f"Warning: Unknown obstacle type '{obstacle_type}'")
            return

        use_shapes = obstacle_type in ("static", "orthogonal")

        while True:
            x = random.randint(0, C.GRID_WIDTH - 1)
            y = random.randint(0, C.GRID_HEIGHT - 1)

            occupied = self._get_occupied_positions()
            occupied.append((self.apple.x, self.apple.y))
            occupied_set = set(occupied)
            head_x, head_y = self.snake.get_head_position()

            if use_shapes:
                shape = random.choice(C.OBSTACLE_SHAPES)
                all_cells = [(x + dx, y + dy) for (dx, dy) in shape]
                valid = all(
                    0 <= cx < C.GRID_WIDTH and 0 <= cy < C.GRID_HEIGHT
                    and (cx, cy) not in occupied_set
                    and abs(cx - head_x) + abs(cy - head_y) >= C.MIN_OBSTACLE_SPAWN_DISTANCE
                    for (cx, cy) in all_cells
                )
            else:
                shape = None
                valid = (
                    (x, y) not in occupied_set
                    and abs(x - head_x) + abs(y - head_y) >= C.MIN_OBSTACLE_SPAWN_DISTANCE
                )

            if valid:
                if obstacle_type == "static":
                    obstacle = Obstacle(x, y, shape=shape)
                elif obstacle_type == "orthogonal":
                    obstacle = OrthogonalMovingObstacle(x, y, shape=shape)
                else:
                    obstacle = obstacle_settings["class"](x, y)
                if lifespan is not None:
                    obstacle.lifespan = lifespan
                obstacle_settings["list"].append(obstacle)
                self.particle_effects.append(ParticleEffect(x, y, obstacle_settings["effect_type"], is_spawning=True))
                break

    def _check_for_level_up(self):
        """Checks if the player should start clearing the current level (based on apples eaten).
        Level actually increments only after the snake exits the door."""
        if self.level_clearing or self.level_door or self.level_exiting:
            return
        thresholds = {
            1: C.LEVEL_2_APPLES,
            2: C.LEVEL_3_APPLES,
            3: C.LEVEL_4_APPLES,
            4: C.LEVEL_5_APPLES,
        }
        if self.level not in thresholds or self.apples_eaten < thresholds[self.level]:
            return
        self.next_level     = self.level + 1
        self.level_clearing = True
        self.apple_visible  = False   # no apple visible during clear/door/exit sequence
        if self.level == 1:   self.removing_static_obstacles     = True
        elif self.level == 2: self.removing_orthogonal_obstacles  = True
        elif self.level == 3: self.removing_diagonal_obstacles    = True
        elif self.level == 4: self.removing_seeker_obstacles      = True
        self._spawn_level_door()  # portal appears immediately as enemies begin despawning

    def _spawn_level_door(self):
        """Spawn the exit portal on a random wall edge."""
        self.level_door = LevelDoor(random.choice(['top', 'bottom', 'left', 'right']))

    def _update_mechanics_and_objects(self):
        """Updates mechanics, basically a collection folder for everything that must be checked."""
        # Static obstacle removal (clearing phase 1 → 2)
        if self.removing_static_obstacles and self.frame_counter % C.OBSTACLE_REMOVAL_INTERVAL == 0:
            if self.obstacles:
                obstacle_to_remove = self.obstacles.pop(0)
                if self.remove_obstacle_sound:
                    self.remove_obstacle_sound.play()
                self.particle_effects.append(ParticleEffect(obstacle_to_remove.x, obstacle_to_remove.y, "obstacle_static", is_spawning=False))
            else:
                self.removing_static_obstacles = False

        # Handle orthogonal obstacle removal with dust particles
        if self.removing_orthogonal_obstacles and self.frame_counter % C.MOVING_OBSTACLE_REMOVAL_INTERVAL == 0:
            orthogonal_obstacles = [obstacle for obstacle in self.moving_obstacles
                                    if isinstance(obstacle, OrthogonalMovingObstacle)]
            if orthogonal_obstacles:
                obstacle_to_remove = orthogonal_obstacles[0]
                self.moving_obstacles.remove(obstacle_to_remove)
                if self.remove_obstacle_sound:
                    self.remove_obstacle_sound.play()
                self.particle_effects.append(ParticleEffect(obstacle_to_remove.x, obstacle_to_remove.y, "obstacle_orthogonal", is_spawning=False))
            else:
                self.removing_orthogonal_obstacles = False

        # Handle diagonal obstacle removal with dust particles
        if self.removing_diagonal_obstacles and self.frame_counter % C.MOVING_OBSTACLE_REMOVAL_INTERVAL == 0:
            diagonal_obstacles = [obstacle for obstacle in self.moving_obstacles
                                  if isinstance(obstacle, MovingObstacle)
                                  and not isinstance(obstacle, OrthogonalMovingObstacle)
                                  and not isinstance(obstacle, SeekerObstacle)]
            if diagonal_obstacles:
                obstacle_to_remove = diagonal_obstacles[0]
                self.moving_obstacles.remove(obstacle_to_remove)
                if self.remove_obstacle_sound:
                    self.remove_obstacle_sound.play()
                self.particle_effects.append(ParticleEffect(obstacle_to_remove.x, obstacle_to_remove.y, "obstacle_diagonal", is_spawning=False))
            else:
                self.removing_diagonal_obstacles = False

        # Handle seeker obstacle removal with dust particles (transition 4 → 5)
        if self.removing_seeker_obstacles and self.frame_counter % C.MOVING_OBSTACLE_REMOVAL_INTERVAL == 0:
            seeker_obstacles = [ob for ob in self.moving_obstacles if isinstance(ob, SeekerObstacle)]
            if seeker_obstacles:
                obstacle_to_remove = seeker_obstacles[0]
                self.moving_obstacles.remove(obstacle_to_remove)
                if self.remove_obstacle_sound:
                    self.remove_obstacle_sound.play()
                self.particle_effects.append(ParticleEffect(int(obstacle_to_remove.float_x), int(obstacle_to_remove.float_y), "obstacle_seeker", is_spawning=False))
            else:
                self.removing_seeker_obstacles = False

        # Tick door animations
        if self.level_door:
            self.level_door.update()
        if self.entry_door:
            self.entry_door.update()
            self.entry_door_ticks -= 1
            if self.entry_door_ticks <= 0:
                self.entry_door = None
                
        # Update moving obstacles (frozen during freeze_obstacles buff)
        if 'freeze_obstacles' not in self.active_buffs:
            for moving_obstacle in self.moving_obstacles:
                moving_obstacle.update(self.snake, self.obstacles)

            # Soft seeker-seeker bounce: resolve overlaps between seekers
            seekers = [ob for ob in self.moving_obstacles if isinstance(ob, SeekerObstacle)]
            for i in range(len(seekers)):
                for j in range(i + 1, len(seekers)):
                    s1, s2 = seekers[i], seekers[j]
                    # Centre positions in grid units
                    dx = (s1.float_x + 0.5) - (s2.float_x + 0.5)
                    dy = (s1.float_y + 0.5) - (s2.float_y + 0.5)
                    dist_sq = dx * dx + dy * dy
                    if dist_sq >= 1.0 or dist_sq == 0:
                        continue
                    dist = math.sqrt(dist_sq)
                    nx, ny = dx / dist, dy / dist
                    # Positional correction: push apart to eliminate overlap
                    push = (1.0 - dist) * 0.5
                    s1.float_x += nx * push
                    s1.float_y += ny * push
                    s2.float_x -= nx * push
                    s2.float_y -= ny * push
                    # Velocity impulse along collision normal (only if approaching)
                    rel_v_n = (s1.dx - s2.dx) * nx + (s1.dy - s2.dy) * ny
                    if rel_v_n < 0:
                        impulse = rel_v_n * -0.5   # restitution = 0.4 → soft bounce
                        s1.dx += impulse * nx
                        s1.dy += impulse * ny
                        s2.dx -= impulse * nx
                        s2.dy -= impulse * ny
                        # Re-normalise to keep constant seeker speed
                        for s in (s1, s2):
                            spd = math.sqrt(s.dx ** 2 + s.dy ** 2)
                            if spd > 0:
                                s.dx = (s.dx / spd) * C.SEEKER_OBSTACLE_SPEED
                                s.dy = (s.dy / spd) * C.SEEKER_OBSTACLE_SPEED

        # Update magical apples
        for magic_apple in list(self.magic_apples):
            life_span = magic_apple.update()
            if life_span <= 0:
                self.magic_apples.remove(magic_apple)

        # Tick and despawn temporary obstacles (those tagged with a lifespan)
        for ob in list(self.obstacles):
            if hasattr(ob, 'lifespan'):
                ob.lifespan -= 1
                if ob.lifespan <= 0:
                    self.obstacles.remove(ob)
                    self.particle_effects.append(ParticleEffect(ob.x, ob.y, "obstacle_static", is_spawning=False))
        for mob in list(self.moving_obstacles):
            if hasattr(mob, 'lifespan'):
                mob.lifespan -= 1
                if mob.lifespan <= 0:
                    self.moving_obstacles.remove(mob)
                    if isinstance(mob, SeekerObstacle):
                        effect_type = "obstacle_seeker"
                    elif isinstance(mob, OrthogonalMovingObstacle):
                        effect_type = "obstacle_orthogonal"
                    else:
                        effect_type = "obstacle_diagonal"
                    self.particle_effects.append(ParticleEffect(int(mob.float_x), int(mob.float_y), effect_type, is_spawning=False))

        # Tick per-obstacle hit cooldowns (prevents multi-charge drain on a single pass-through)
        self.obstacle_hit_cooldowns = {
            ob: v - 1 for ob, v in self.obstacle_hit_cooldowns.items() if v > 1
        }

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
                elif event.key == K_SPACE:
                    self.pause_game()
                elif event.key == K_ESCAPE:
                    self.confirm_quit()

                if new_dir:
                    # Store the intended direction instead of changing immediately
                    self.next_direction = new_dir
                    if 'manual_control' in self.active_buffs:
                        self.manual_step = True

    def _tick_active_buffs(self):
        """Decrement all active buff timers; restore speed when speed buffs expire.
        'shield' is charge-based, not time-based – it is never decremented here."""
        charge_based = ('shield', 'manual_control')
        expired = [k for k, v in self.active_buffs.items() if k not in charge_based and v <= 1]
        for key in expired:
            if key in ('increase_tick_speed', 'decrease_tick_speed'):
                self.game_speed = self.base_speed
        self.active_buffs = {
            k: (v if k in charge_based else v - 1)
            for k, v in self.active_buffs.items()
            if k in charge_based or v > 1
        }

    def _start_menu_music(self):
        """Start looping menu music if it isn't already playing."""
        if C.MENU_MUSIC_FILE and not mixer.music.get_busy():
            try:
                mixer.music.load(C.MENU_MUSIC_FILE)
                mixer.music.set_volume(C.MENU_MUSIC_VOLUME)
                mixer.music.play(-1)
            except pygame.error:
                pass

    def _stop_menu_music(self):
        """Fade the menu music out over MENU_MUSIC_FADEOUT_MS milliseconds."""
        mixer.music.fadeout(C.MENU_MUSIC_FADEOUT_MS)

    def _start_level_exit(self):
        """Begin the portal exit animation.
        The snake continues moving naturally (move() called each tick);
        segments that have passed through the portal are simply not rendered.
        Game speed is cranked up so the crawl-through feels snappy."""
        self.exit_original_length  = len(self.snake.positions)
        self.exit_consumed         = 0
        self.exit_segments_left    = self.exit_original_length
        self.level_exiting         = True
        self.snake.exit_mode       = True
        self.snake.exit_original_n = self.exit_original_length
        self.snake.exit_consumed   = 0
        self.game_speed            = C.EXIT_ANIMATION_SPEED
        if self.whoosh_sound:
            self.whoosh_sound.play()

    def _calc_level_clear_bonus(self, elapsed):
        overtime = max(0, elapsed - C.LEVEL_CLEAR_BONUS_DECAY)
        return max(0, C.LEVEL_CLEAR_BONUS_BASE - overtime // C.LEVEL_CLEAR_BONUS_RATE)

    def _show_level_clear_screen(self, elapsed_ticks, bonus):
        """Blocking animated screen shown between levels."""
        self._start_menu_music()
        self.screen.reset_waves()
        anim_tick = 0
        waiting   = True
        while waiting and self.running:
            self.clock.tick(20)
            anim_tick += 1
            self.screen.tick_waves()
            self.screen.draw_level_clear_screen(
                self.level, self.next_level, elapsed_ticks, bonus, self.score, anim_tick
            )
            self.screen.update()
            for event in pygame.event.get():
                if event.type == QUIT:
                    self.running = False
                elif event.type == KEYDOWN:
                    if event.key in (K_RETURN, K_SPACE):
                        waiting = False
                    elif event.key == K_ESCAPE:
                        self.running = False
        self._stop_menu_music()

    def _setup_next_level(self):
        """Advance to next_level, clear the field, and place the snake at a new entry portal."""
        self.level              = self.next_level
        self.max_level_reached  = max(self.max_level_reached, self.level)
        self.level_clearing     = False
        self.level_door         = None
        self.level_exiting      = False
        self.removing_static_obstacles     = False
        self.removing_orthogonal_obstacles = False
        self.removing_diagonal_obstacles   = False
        self.removing_seeker_obstacles     = False
        self.game_speed         = self.base_speed
        self.obstacle_hit_cooldowns.clear()
        self.active_buffs.clear()
        self.obstacles.clear()
        self.moving_obstacles.clear()
        self.magic_apples.clear()
        self.particle_effects.clear()

        # Entry portal on a random wall
        wall  = random.choice(['top', 'bottom', 'left', 'right'])
        entry = LevelDoor(wall, start_tick=C.DOOR_APPEAR_TICKS)  # fully visible immediately
        self.entry_door       = entry
        self.entry_door_ticks = C.DOOR_ENTRY_FADE_TICKS

        # exit_dir points INTO the wall; snake moves in the opposite direction (away from wall)
        ex, ey   = entry.exit_dir
        in_x, in_y = -ex, -ey

        if wall == 'top':    hx, hy = entry.x, 1
        elif wall == 'bottom': hx, hy = entry.x, C.GRID_HEIGHT - 2
        elif wall == 'left':   hx, hy = 1, entry.y
        else:                  hx, hy = C.GRID_WIDTH - 2, entry.y

        # Build positions: head at hx,hy; body segments trail toward the wall
        n = C.SNAKE_START_LENGTH
        positions = [
            (max(0, min(C.GRID_WIDTH  - 1, hx + ex * i)),
             max(0, min(C.GRID_HEIGHT - 1, hy + ey * i)))
            for i in range(n)
        ]
        self.snake            = Snake()
        self.snake.positions  = positions
        self.snake.length     = n
        self.snake.direction  = (in_x, in_y)

        self.apple_visible = True
        self.apple.respawn(self._get_occupied_positions())
        self.level_start_tick = self.time_alive

    def _complete_level_exit(self):
        """Called when the last snake segment has entered the door."""
        elapsed = self.time_alive - self.level_start_tick
        bonus   = self._calc_level_clear_bonus(elapsed)
        self.score += bonus
        self._show_level_clear_screen(elapsed, bonus)
        if self.running:
            self._setup_next_level()
        self.level_exiting = False

    def update_game_state(self):
        """ Updates the position of the snake. """

        # --- Level exit animation: snake moves naturally; portal clips rendering ---
        if self.level_exiting:
            if self.exit_segments_left > 0:
                self.snake.move(ghost=True)   # advance naturally; head wraps around
                self.exit_consumed      += 1
                self.exit_segments_left -= 1
                self.snake.exit_consumed = self.exit_consumed
            if self.exit_segments_left <= 0:
                self._complete_level_exit()
            self._tick_active_buffs()
            self.time_alive += 1
            self._update_mechanics_and_objects()
            self.particle_effects = [e for e in self.particle_effects if e.update()]
            return

        # Apply the buffered direction change before moving
        if self.next_direction:
            self.snake.change_direction(self.next_direction)
            self.next_direction = None

        # Manual control: snake only moves when a direction key was pressed
        manual = 'manual_control' in self.active_buffs
        do_move = not manual or self.manual_step
        if manual and self.manual_step:
            self.manual_step = False

        if do_move:
            if not self.snake.move(ghost='ghost_mode' in self.active_buffs):
                head = self.snake.get_head_position()
                self.death_pos = (
                    head[0] * C.GRID_SIZE + C.GRID_SIZE // 2,
                    head[1] * C.GRID_SIZE + C.GRID_SIZE // 2,
                )
                if head in self.snake.positions[1:]:
                    if self.bite_self_sound:
                        self.bite_self_sound.play()
                self.game_over()
                return

            # Decrement manual-control move counter
            if manual:
                self.active_buffs['manual_control'] -= 1
                if self.active_buffs['manual_control'] <= 0:
                    del self.active_buffs['manual_control']

            self.distance_traveled += 1
            current_len = len(self.snake.positions)
            if current_len > self.max_snake_length:
                self.max_snake_length = current_len

        # Tick time-based buff timers every tick regardless of snake movement
        self._tick_active_buffs()

        # Tick combo timer; break chain when it expires
        if self.combo_timer > 0:
            self.combo_timer -= 1
            if self.combo_timer == 0:
                self.combo_count = 0

        # Track time alive
        self.time_alive += 1

        # Check if player advances to next level
        self._check_for_level_up()

        # Apply level-specific mechanics
        self._update_mechanics_and_objects()

        # Update particle effects and remove finished ones
        self.particle_effects = [effect for effect in self.particle_effects if effect.update()]

    def _apply_obstacle_death(self):
        """Handle an obstacle collision: absorb one shield charge or die."""
        if 'shield' in self.active_buffs:
            self.active_buffs['shield'] -= 1
            if self.active_buffs['shield'] == 0:
                del self.active_buffs['shield']
            if self.bite_obstacle_sound:
                self.bite_obstacle_sound.play()
            return  # hit absorbed – snake survives
        if self.bite_obstacle_sound:
            self.bite_obstacle_sound.play()
        self.game_over()

    def check_collisions(self):
        """ Checks for collisions between game objects. """
        if self.level_exiting:
            return  # no collisions during door exit animation
        # Snake eating apple (hidden during level-clear sequence)
        if self.apple_visible and self.snake.collides_with_rect(self.apple.rect):
            self.combo_count += 1
            self.combo_timer = C.COMBO_WINDOW
            if self.combo_count > self.max_combo:
                self.max_combo = self.combo_count
            combo_mult = min(self.combo_count, C.COMBO_MAX_MULT)
            base_score = 2 if 'double_score' in self.active_buffs else 1
            self.score += base_score * combo_mult
            self.apples_eaten += 1
            if 'no_grow' not in self.active_buffs:
                self.snake.grow()
            if self.apple_eat_sound:
                self.apple_eat_sound.play()

            # Level-specific obstacle spawning (paused while clearing or door active)
            if not self.level_clearing and not self.level_door:
                if self.level == 1:
                    self._add_obstacle("static")
                elif self.level == 2:
                    self._add_obstacle("orthogonal")
                elif self.level == 3:
                    self._add_obstacle("diagonal")
                elif self.level == 4:
                    self._add_obstacle("seeker")
                elif self.level == 5:
                    self._add_obstacle(random.choice(["static", "orthogonal", "diagonal", "seeker"]))

            # Respawn apple, ensuring it's not on the snake or obstacles
            self.apple.respawn(self._get_occupied_positions())

            # In test mode, force the target buff after the very first apple
            if self.test_buff and self.apples_eaten == 1:
                self._add_magic_apple(force_type=self.test_buff)
            elif random.random() < C.MAGIC_APPLE_SPAWN_PROBABILITY:
                self._add_magic_apple()

            # Check immediately so apple_visible is set before draw() runs this frame
            self._check_for_level_up()

        # Snake eating magic apple
        for magic_apple in list(self.magic_apples):
            if self.snake.collides_with_rect(magic_apple.rect):
                self.score += 5
                self.snake.grow()
                if self.magic_apple_eat_sounds:
                    random.choice(self.magic_apple_eat_sounds).play()
                elif self.magic_apple_eat_sound:
                    self.magic_apple_eat_sound.play()
                # Dispatch buff effect
                fn = getattr(mal, magic_apple.type, None)
                if fn:
                    fn(self)
                self.magic_apples_eaten += 1
                self.magic_apples.remove(magic_apple)
                label, color = C.BUFF_DISPLAY_NAMES.get(
                    magic_apple.type, (magic_apple.type, C.TEXT_COLOR))
                self.buff_announcements.append(BuffAnnouncement(label, color))
                break

        # Snake hitting static obstacles (bypassed during ghost_mode)
        if 'ghost_mode' not in self.active_buffs:
            for ob in self.obstacles:
                if ob in self.obstacle_hit_cooldowns:
                    continue
                if any(self.snake.collides_with_rect(r) for r in ob.rects):
                    self.death_pos = (
                        ob.x * C.GRID_SIZE + C.GRID_SIZE // 2,
                        ob.y * C.GRID_SIZE + C.GRID_SIZE // 2,
                    )
                    self._apply_obstacle_death()
                    if self.running:  # hit absorbed – start cooldown
                        self.obstacle_hit_cooldowns[ob] = C.OBSTACLE_HIT_COOLDOWN
                    break

        # Snake head hitting moving obstacles (bypassed during ghost_mode)
        if 'ghost_mode' not in self.active_buffs and self.running:
            for moving_obstacle in self.moving_obstacles:
                if moving_obstacle in self.obstacle_hit_cooldowns:
                    continue
                if moving_obstacle.collides_with_snake_head(self.snake):
                    self.death_pos = (
                        int(moving_obstacle.float_x * C.GRID_SIZE + C.GRID_SIZE // 2),
                        int(moving_obstacle.float_y * C.GRID_SIZE + C.GRID_SIZE // 2),
                    )
                    self._apply_obstacle_death()
                    if self.running:  # hit absorbed – start cooldown
                        self.obstacle_hit_cooldowns[moving_obstacle] = C.OBSTACLE_HIT_COOLDOWN
                    break

        # Level door entry: snake head in door cell moving toward the wall
        if self.level_door and self.running and not self.level_exiting:
            if self.level_door.is_head_entering(self.snake):
                self._start_level_exit()

    def draw(self):
        """ Draws all game elements onto the screen. """
        invert = 'color_invert' in self.active_buffs
        self.screen.invert_mode = invert
        self.screen.clear()

        for effect in self.particle_effects:
            effect.draw(self.screen.surface)

        self.snake.ghost_alpha = C.SNAKE_GHOST_ALPHA if 'ghost_mode' in self.active_buffs else 255
        self.snake.invert_colors = invert
        self.screen.draw_element(self.snake)

        # Apple: hidden during level-clear sequence
        if self.apple_visible:
            orig_apple_color = self.apple.color
            if invert:
                self.apple.color = (0, 190, 0)
            self.screen.draw_element(self.apple)
            self.apple.color = orig_apple_color

        # Magic apples: swap fill to magenta when inverted; border (lifespan) unchanged
        for magic_apple in self.magic_apples:
            orig_ma_color = magic_apple.color
            if invert:
                magic_apple.color = (200, 0, 200)
            self.screen.draw_element(magic_apple)
            magic_apple.color = orig_ma_color

        for obstacle in self.obstacles:
            self.screen.draw_element(obstacle)
        for moving_obstacle in self.moving_obstacles:
            self.screen.draw_element(moving_obstacle)

        # Level door portals
        if self.level_door:
            self.level_door.draw(self.screen.surface)
        if self.entry_door:
            fade = max(0.0, self.entry_door_ticks / C.DOOR_ENTRY_FADE_TICKS)
            self.entry_door.draw(self.screen.surface, alpha_scale=fade)

        # Darkness buff: drape a fully-opaque vignette over the gameplay layer,
        # leaving only a soft-edged circle around the snake head visible.
        # Applied BEFORE buff announcements and HUD so they always stay readable.
        if 'darkness' in self.active_buffs:
            head_x, head_y = self.snake.get_head_position()
            px = head_x * C.GRID_SIZE + C.GRID_SIZE // 2
            py = head_y * C.GRID_SIZE + C.GRID_SIZE // 2
            self.screen.apply_darkness((px, py))

        # Buff announcements drawn after the darkness mask so they are never hidden
        active = []
        for ann in self.buff_announcements:
            if ann.update():
                ann.draw(self.screen.surface)
                active.append(ann)
        self.buff_announcements = active

        self.screen.draw_score_and_level(self.score, self.level,
                                          self.combo_count, self.combo_timer)
        self.screen.draw_buffs(self.active_buffs)
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

        while input_active and self.running:
            self.clock.tick(30)  # cap at 30 fps so the blinking cursor redraws smoothly
            self.screen.clear()
            self.screen.draw_overlay()
            self.screen.draw_game_over_message(self.score)
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

    def pause_game(self):
        """Pauses the game and waits for player input to continue."""
        self.wait_for_continue()

    def confirm_quit(self):
        """Show a quit-confirmation dialog; quit only if ESC is pressed again."""
        # Freeze the current frame; only the dialog animates on top
        snapshot = self.screen.surface.copy()
        tick = 0
        quit_rect = resume_rect = None
        while True:
            for event in pygame.event.get():
                if event.type == QUIT:
                    self.running = False
                    return
                if event.type == KEYDOWN:
                    if event.key == K_ESCAPE:
                        self.running = False
                        return
                    if event.key == K_SPACE:
                        return  # resume
                if event.type == MOUSEBUTTONDOWN and event.button == 1:
                    if quit_rect and quit_rect.collidepoint(event.pos):
                        self.running = False
                        return
                    if resume_rect and resume_rect.collidepoint(event.pos):
                        return
            self.screen.surface.blit(snapshot, (0, 0))
            quit_rect, resume_rect = self.screen.draw_quit_confirm(tick)
            self.screen.update()
            self.clock.tick(20)
            tick += 1

    def wait_for_continue(self):
        """Game pauses and awaits 'Space'. Other buttons cannot be pressed."""
        self.running = False # Pause the game loop
        # Print to the bottom of the screen "Press Space to continue..."
        self.screen.draw_bottom_message(message="Press SPACE to continue...", size=20)
        self.screen.update()
        waiting_for_input = True
        while waiting_for_input:
            self.clock.tick(15)  # Lower tick rate for game over screen
            for event in pygame.event.get():
                if event.type == QUIT:
                    self.running = False
                    waiting_for_input = False
                elif event.type == KEYDOWN:
                    if event.key == K_SPACE:
                        waiting_for_input = False  # Exit waiting loop
                        self.running = True  # Ensure game continues
    
    def wait_for_continue_after_death(self):
        """Game pauses and awaits 'Space'. Other buttons cannot be pressed. In the meantime a random joke sentence will pass over the screen."""
        self._start_menu_music()
        # chose random joke from the death message list
        joke_text = random.choice(C.Death_Messages)
        text_height_start = random.randint(50, C.SCREEN_HEIGHT-100)
        current_text_height = text_height_start
        # measure rendered text width and pick an X so the text stays fully on-screen
        font_size = 20
        font = pygame.font.Font(None, font_size)
        text_pixel_width, _ = font.size(joke_text)
        current_text_width = text_pixel_width / 1.5 + 20

        self.running = False # Pause the game loop
        self.screen.draw_bottom_message(message="Press SPACE to continue...", size=20)
        self.screen.update()
        waiting_for_input = True
        static_background = self.screen.surface.copy() # save the current visuals to rerender it
        shockwave = ShockwaveEffect(*self.death_pos) if self.death_pos else None
        while waiting_for_input:
            self.clock.tick(15)  # Lower tick rate for game over screen
            # reprint the last screen
            self.screen.surface.blit(static_background, (0, 0))
            # shockwave at the point of death
            if shockwave and not shockwave.done:
                shockwave.update()
                shockwave.draw(self.screen.surface)
            # display the joke text
            self.screen.draw_message_at_x_y(joke_text, current_text_width, current_text_height, 20)

            # change position for next frame
            if text_height_start < C.SCREEN_HEIGHT/2: # sometimes text goes up, sometimes down, depending on where it starts
                current_text_height += 1
            else:
                current_text_height -= 1
            current_text_width += 1 # text always goes towards the right
            self.screen.update()

            # check for the user to press enter
            for event in pygame.event.get():
                if event.type == QUIT:
                    self.running = False
                    waiting_for_input = False
                elif event.type == KEYDOWN:
                    if event.key == K_SPACE:
                        waiting_for_input = False  # Exit waiting loop
                        self.running = True  # Ensure game continues

    def game_over(self):
        """ Handles the game over sequence, including high score check and restart prompt. """
        self.gameover = True
        self.wait_for_continue_after_death()
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

        # Build stats dict for the death screen
        stats = {
            'apples':       self.apples_eaten,
            'time_ticks':   self.time_alive,
            'max_level':    self.max_level_reached,
            'max_length':   self.max_snake_length,
            'distance':     self.distance_traveled,
            'magic_apples': self.magic_apples_eaten,
            'max_combo':    self.max_combo,
        }

        # Animated game-over screen – redraws each tick so waves animate
        self.screen.reset_waves()
        waiting_for_input = True
        anim_tick = 0
        restart_rect = quit_rect = None
        while waiting_for_input and self.running:
            self.clock.tick(20)
            anim_tick += 1
            self.screen.tick_waves()
            restart_rect, quit_rect = self.screen.draw_death_screen(
                self.score, stats, self.high_scores,
                highlight_pos=insert_pos, tick=anim_tick
            )
            self.screen.update()
            for event in pygame.event.get():
                if event.type == QUIT:
                    self.running = False
                    waiting_for_input = False
                elif event.type == KEYDOWN:
                    if event.key == K_ESCAPE:
                        self.running = False
                    elif event.key == K_RETURN:
                        waiting_for_input = False
                elif event.type == MOUSEBUTTONDOWN and event.button == 1:
                    if restart_rect and restart_rect.collidepoint(event.pos):
                        waiting_for_input = False
                    elif quit_rect and quit_rect.collidepoint(event.pos):
                        self.running = False
                        waiting_for_input = False

        # If the game is still running (i.e., didn't quit), reset for a new game
        if self.running:
            self._stop_menu_music()
            self.reset()

    def reset(self):
        """ Resets the game state for a new game. """
        self.snake = Snake()
        self.obstacles = []
        self.moving_obstacles = []
        self.magic_apples = []
        self.particle_effects = []
        self.buff_announcements = []
        self.apple = self._create_initial_apple()
        self.score = 0
        self.apples_eaten = 0
        self.time_alive = 0
        self.max_snake_length = C.SNAKE_START_LENGTH
        self.distance_traveled = 0
        self.magic_apples_eaten = 0
        self.level = 1
        self.max_level_reached = 1
        self.frame_counter = 0
        self.base_speed = C.SNAKE_SPEED_INITIAL
        self.game_speed = C.SNAKE_SPEED_INITIAL
        self.active_buffs = {}
        self.next_direction = None
        self.manual_step = False   # True for one tick when a key is pressed during manual_control
        self.combo_count = 0       # consecutive apples eaten within the COMBO_WINDOW
        self.combo_timer = 0       # ticks remaining before the combo chain breaks
        self.max_combo = 0         # highest combo_count reached this run
        self.removing_static_obstacles = False
        self.removing_orthogonal_obstacles = False
        self.removing_diagonal_obstacles = False
        self.removing_seeker_obstacles = False
        self.level_clearing       = False   # threshold hit; old obstacles being removed
        self.next_level           = 1       # level that becomes active after the next door
        self.level_door           = None    # LevelDoor (exit portal), active until snake exits
        self.level_exiting        = False   # True during exit animation
        self.exit_segments_left   = 0
        self.exit_consumed        = 0       # segments consumed from front so far
        self.exit_original_length = 0
        self.level_start_tick     = 0       # time_alive when current level began
        self.entry_door           = None    # fading entry portal (visual only)
        self.entry_door_ticks     = 0       # countdown for entry portal fade
        self.apple_visible        = True    # False while clearing/door active (no new apples)
        self.death_pos = None   # screen-pixel (cx, cy) of the object that killed the snake
        self.obstacle_hit_cooldowns = {}  # obstacle -> ticks until same obstacle can hit again
        self.running = True
        self._apply_start_level()

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
