import pygame
import random
import constants as C # Use absolute import
import math  # For particle effects calculations

class GameObject:
    """ Base class for objects with position and size """
    def __init__(self, x, y, width, height, color):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.color = color
        # Convert grid coordinates to screen coordinates for the rect
        self.rect = pygame.Rect(self.x * C.GRID_SIZE, self.y * C.GRID_SIZE, self.width, self.height)

    def draw(self, surface):
        pygame.draw.rect(surface, self.color, self.rect)

    def update_rect(self):
        # Update rect based on grid coordinates
        self.rect.topleft = (self.x * C.GRID_SIZE, self.y * C.GRID_SIZE)

    def collides_with(self, other_rect):
        return self.rect.colliderect(other_rect)

class Snake:
    """ Represents the snake """
    def __init__(self):
        self.length = C.SNAKE_START_LENGTH
        # Initial grid positions
        start_x, start_y = C.SNAKE_START_POS
        self.positions = [(start_x, start_y - i) for i in range(self.length)]
        self.direction = C.SNAKE_START_DIR
        self.color = C.SNAKE_COLOR
        self.head_color = C.SNAKE_HEAD_COLOR
        self.size = C.GRID_SIZE
        # Initialize float coordinates for the head
        self.float_x = float(start_x)
        self.float_y = float(start_y)
        # Visual state – set by Game.draw() each frame
        self.ghost_alpha = 255

    def get_head_position(self):
        # Returns integer grid position (compatible with existing logic)
        return self.positions[0]

    def get_float_head_position(self):
        # Returns float grid position
        return self.float_x, self.float_y

    def move(self, ghost=False):
        dx, dy = self.direction
        cur_x, cur_y = self.get_head_position()
        if C.WALL_COLLISION:
            new_head_grid = (cur_x + dx, cur_y + dy)
            if not (0 <= new_head_grid[0] < C.GRID_WIDTH and 0 <= new_head_grid[1] < C.GRID_HEIGHT):
                return False # Wall collision
        else:
            new_head_grid = ((cur_x + dx) % C.GRID_WIDTH, (cur_y + dy) % C.GRID_HEIGHT)

        # Check for self-collision (bypassed in ghost mode)
        if not ghost and new_head_grid != self.positions[0] and new_head_grid in self.positions[1:]:
            return False # Self-collision

        # Insert new head position (always integer grid coordinates for body segments)
        self.positions.insert(0, new_head_grid)

        # Remove tail if snake hasn't grown
        if len(self.positions) > self.length:
            self.positions.pop()

        return True # Movement successful

    def change_direction(self, new_direction):
        # Prevent reversing direction
        if (new_direction[0] * -1, new_direction[1] * -1) != self.direction:
            self.direction = new_direction

    def grow(self):
        self.length += 1

    def draw(self, surface):
        inset = C.SNAKE_SEGMENT_INSET
        seg_size = C.GRID_SIZE - 2 * inset
        n = len(self.positions)
        use_alpha = self.ghost_alpha < 255

        # Helper: draw one inset rect (with optional alpha) onto `surface`
        def _draw_seg(sx, sy, color):
            rx = sx * C.GRID_SIZE + inset
            ry = sy * C.GRID_SIZE + inset
            if use_alpha:
                s = pygame.Surface((seg_size, seg_size), pygame.SRCALPHA)
                s.fill((*color, self.ghost_alpha))
                surface.blit(s, (rx, ry))
            else:
                pygame.draw.rect(surface, color, pygame.Rect(rx, ry, seg_size, seg_size))

        # Head
        head_x, head_y = self.positions[0]
        inv = getattr(self, 'invert_colors', False)
        _draw_seg(head_x, head_y, (200, 30, 30) if inv else self.head_color)

        # Body gradient: green normally, red when color-inverted
        for i, (x, y) in enumerate(self.positions[1:]):
            t = i / max(n - 2, 1)
            v = int(200 - t * 130)   # 200 → 70
            _draw_seg(x, y, (v, 0, 0) if inv else (0, v, 0))

        # Eyes on head (2 small white dots)
        dx, dy = self.direction
        cx = head_x * C.GRID_SIZE + C.GRID_SIZE // 2
        cy = head_y * C.GRID_SIZE + C.GRID_SIZE // 2
        r = C.SNAKE_EYE_RADIUS
        offset = C.GRID_SIZE // 2 - r - 2
        # Perpendicular axis to movement
        if dx == 0:   # moving up/down → eyes side by side horizontally
            eye1 = (cx - offset, cy + dy * offset)
            eye2 = (cx + offset, cy + dy * offset)
        else:         # moving left/right → eyes side by side vertically
            eye1 = (cx + dx * offset, cy - offset)
            eye2 = (cx + dx * offset, cy + offset)

        eye_color = (255, 255, 255) if not use_alpha else (255, 255, 255)
        eye_alpha = self.ghost_alpha
        if use_alpha:
            for ex, ey in (eye1, eye2):
                s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
                pygame.draw.circle(s, (255, 255, 255, eye_alpha), (r, r), r)
                surface.blit(s, (int(ex) - r, int(ey) - r))
        else:
            for ex, ey in (eye1, eye2):
                pygame.draw.circle(surface, eye_color, (int(ex), int(ey)), r)

    def collides_with_rect(self, rect):
        # Collision check based on the integer grid head position's rect
        # This keeps apple/obstacle collision grid-based for simplicity unless changed
        head_x, head_y = self.get_head_position()
        head_rect = pygame.Rect(head_x * C.GRID_SIZE, head_y * C.GRID_SIZE, self.size, self.size)
        return head_rect.colliderect(rect)

    def collides_with_obstacles(self, obstacles):
        for obstacle in obstacles:
            # Use the integer grid head position for collision with static obstacles
            if self.collides_with_rect(obstacle.rect):
                return True
        return False

    def get_body_positions(self):
        # Return grid coordinates of the body segments
        return self.positions[1:]

class Apple(GameObject):
    """ Represents the apple """
    def __init__(self, x, y):
        super().__init__(x, y, C.APPLE_SIZE[0], C.APPLE_SIZE[1], C.APPLE_COLOR)

    def draw(self, surface):
        """Draw a circle with a small warm-white highlight."""
        cx = self.x * C.GRID_SIZE + C.GRID_SIZE // 2
        cy = self.y * C.GRID_SIZE + C.GRID_SIZE // 2
        radius = C.GRID_SIZE // 2 - 1
        pygame.draw.circle(surface, self.color, (cx, cy), radius)
        # Small highlight in upper-right quadrant
        hx = cx + radius // 3
        hy = cy - radius // 3
        pygame.draw.circle(surface, C.APPLE_HIGHLIGHT_COLOR, (hx, hy), 2)

    def respawn(self, occupied_positions):
        """ Respawn apple in a free grid location """
        while True:
            self.x = random.randint(0, C.GRID_WIDTH - 1)
            self.y = random.randint(0, C.GRID_HEIGHT - 1)
            new_pos = (self.x, self.y)

            # Check if the new grid position is occupied by snake or obstacles
            is_occupied = False
            for pos in occupied_positions:
                if pos == new_pos:
                    is_occupied = True
                    break

            if not is_occupied:
                self.update_rect() # Update rect based on new grid position
                break # Found a free spot

class MagicApple(GameObject):
    """ Represents a magic apple """
    def __init__(self, x, y, force_type=None):
        super().__init__(x, y, C.MAGIC_APPLE_SIZE[0], C.MAGIC_APPLE_SIZE[1], C.MAGIC_APPLE_COLOR)
        self.type = force_type if force_type else random.choice(C.MAGIC_APPLE_TYPES)
        self.lifespan = C.MAGIC_APPLE_LIFESPAN + random.uniform(-0.5, 0.5) * C.MAGIC_APPLE_LIFESPAN
        self.initial_lifespan = self.lifespan

    def update(self):
        """Updates and returns the magic apple's lifetime"""
        self.lifespan -= 1
        return self.lifespan

    def draw(self, surface):
        """Draw a gold circle with a green→red outline indicating remaining lifespan."""
        cx = self.x * C.GRID_SIZE + C.GRID_SIZE // 2
        cy = self.y * C.GRID_SIZE + C.GRID_SIZE // 2
        radius = C.GRID_SIZE // 2 - 1
        pygame.draw.circle(surface, self.color, (cx, cy), radius)
        # Highlight
        hx = cx + radius // 3
        hy = cy - radius // 3
        pygame.draw.circle(surface, C.APPLE_HIGHLIGHT_COLOR, (hx, hy), 2)
        # Lifespan border: green → red circle outline
        ratio = max(0.0, self.lifespan / self.initial_lifespan)
        border_color = (int(255 * (1.0 - ratio)), int(255 * ratio), 0)
        pygame.draw.circle(surface, border_color, (cx, cy), radius, 2)

def _draw_beveled_rect(surface, color, rect):
    """Draw a filled rect with a lighter inner highlight for a 3-D bevel look."""
    pygame.draw.rect(surface, color, rect)
    r, g, b = color
    light = (min(r + 45, 255), min(g + 45, 255), min(b + 45, 255))
    inner = pygame.Rect(rect.x + 2, rect.y + 2, rect.w - 4, rect.h - 4)
    if inner.w > 0 and inner.h > 0:
        pygame.draw.rect(surface, light, inner)

class Obstacle(GameObject):
    """ Represents an obstacle """
    def __init__(self, x, y):
        super().__init__(x, y, C.OBSTACLE_SIZE[0], C.OBSTACLE_SIZE[1], C.OBSTACLE_COLOR)

    def draw(self, surface):
        _draw_beveled_rect(surface, self.color, self.rect)

class MovingObstacle(GameObject):
    """ Represents a moving obstacle """
    def __init__(self, x, y):
        super().__init__(x, y, C.MOVING_OBSTACLE_SIZE[0], C.MOVING_OBSTACLE_SIZE[1], C.MOVING_OBSTACLE_COLOR_DIAGONAL)
        # Randomly assign an initial direction
        self.dx = random.choice([-1, 1]) * C.MOVING_OBSTACLE_SPEED
        self.dy = random.choice([-1, 1]) * C.MOVING_OBSTACLE_SPEED
        # Store the actual position as floats for smoother movement
        # Initialize float_x/y based on the initial grid position x/y
        self.float_x = float(x)
        self.float_y = float(y)

    def update(self, snake, obstacles):
        # Update the floating position
        self.float_x += self.dx
        self.float_y += self.dy

        # Calculate current screen rectangle for collision detection
        current_screen_x = self.float_x * C.GRID_SIZE
        current_screen_y = self.float_y * C.GRID_SIZE
        obstacle_rect = pygame.Rect(current_screen_x, current_screen_y, self.width, self.height)

        # Handle wall collisions (wrap around or bounce)
        if C.WALL_COLLISION:
            # Bounce off walls
            if obstacle_rect.left < 0:
                self.float_x = 0
                self.dx = -self.dx
                obstacle_rect.left = 0 # Adjust rect after changing float_x
            elif obstacle_rect.right > C.SCREEN_WIDTH:
                self.float_x = (C.SCREEN_WIDTH - self.width) / C.GRID_SIZE
                self.dx = -self.dx
                obstacle_rect.right = C.SCREEN_WIDTH # Adjust rect

            if obstacle_rect.top < 0:
                self.float_y = 0
                self.dy = -self.dy
                obstacle_rect.top = 0 # Adjust rect
            elif obstacle_rect.bottom > C.SCREEN_HEIGHT:
                self.float_y = (C.SCREEN_HEIGHT - self.height) / C.GRID_SIZE
                self.dy = -self.dy
                obstacle_rect.bottom = C.SCREEN_HEIGHT # Adjust rect
        else:
            # Wrap around - adjust float position for smooth wrapping
            if self.float_x < 0:
                self.float_x += C.GRID_WIDTH
            elif self.float_x >= C.GRID_WIDTH:
                self.float_x -= C.GRID_WIDTH

            if self.float_y < 0:
                self.float_y += C.GRID_HEIGHT
            elif self.float_y >= C.GRID_HEIGHT:
                self.float_y -= C.GRID_HEIGHT
            # Update rect based on wrapped float position for subsequent checks
            current_screen_x = self.float_x * C.GRID_SIZE
            current_screen_y = self.float_y * C.GRID_SIZE
            obstacle_rect = pygame.Rect(current_screen_x, current_screen_y, self.width, self.height)

        # Update the grid coordinates used for collision detection with static obstacles
        self.x = int(self.float_x)
        self.y = int(self.float_y)

        # Check collision with snake body (not head) using rectangle collision
        collided_with_body = False
        for seg_x, seg_y in snake.get_body_positions():
            segment_rect = pygame.Rect(seg_x * C.GRID_SIZE, seg_y * C.GRID_SIZE, C.GRID_SIZE, C.GRID_SIZE)
            if obstacle_rect.colliderect(segment_rect):
                # Bounce off snake body
                self.dx = -self.dx
                self.dy = -self.dy
                # Optional: Move slightly away after bounce to prevent sticking
                self.float_x += self.dx * 0.1
                self.float_y += self.dy * 0.1
                collided_with_body = True
                break # Only bounce once per frame

        # Check collision with regular obstacles using grid coordinates (or rect collision if preferred)
        if not collided_with_body: # Avoid double collision checks if already bounced off snake
            static_obstacles = [ob for ob in obstacles if isinstance(ob, Obstacle)]
            for obstacle in static_obstacles:
                # Using rect collision for consistency, though grid check might suffice here
                if obstacle_rect.colliderect(obstacle.rect):
                    # Bounce off obstacle
                    self.dx = -self.dx
                    self.dy = -self.dy
                    # Optional: Move slightly away
                    self.float_x += self.dx * 0.1
                    self.float_y += self.dy * 0.1
                    break

    def draw(self, surface):
        # Draw based on the floating-point position for smooth movement
        screen_x = self.float_x * C.GRID_SIZE
        screen_y = self.float_y * C.GRID_SIZE
        draw_rect = pygame.Rect(screen_x, screen_y, self.width, self.height)
        _draw_beveled_rect(surface, self.color, draw_rect)

    def collides_with_snake_head(self, snake):
        # Use rectangle collision based on screen coordinates
        head_x, head_y = snake.get_head_position()
        head_rect = pygame.Rect(head_x * C.GRID_SIZE, head_y * C.GRID_SIZE, C.GRID_SIZE, C.GRID_SIZE)

        # Calculate obstacle's current screen rectangle
        obstacle_screen_x = self.float_x * C.GRID_SIZE
        obstacle_screen_y = self.float_y * C.GRID_SIZE
        obstacle_rect = pygame.Rect(obstacle_screen_x, obstacle_screen_y, self.width, self.height)

        return obstacle_rect.colliderect(head_rect)

class OrthogonalMovingObstacle(MovingObstacle):
    """Represents an orthogonally moving obstacle"""
    def __init__(self, x, y):
        # Initialize with base class but override color
        super().__init__(x, y)
        self.color = C.MOVING_OBSTACLE_COLOR_ORTHOGONAL
        # override direction to be orthogonal
        orientation = random.choice(['horizontal', 'vertical'])
        speed = C.MOVING_OBSTACLE_SPEED
        if orientation == 'horizontal':
            self.dx = random.choice([-1, 1]) * speed
            self.dy = 0
        else:
            self.dy = random.choice([-1, 1]) * speed
            self.dx = 0


class SeekerObstacle(MovingObstacle):
    """A homing obstacle that slowly steers toward the snake head each tick.

    Moves slightly faster than regular moving obstacles but corrects its
    heading gradually (SEEKER_TURN_RATE), so the player has time to react
    and outmaneuver it.  Drawn as a diamond to distinguish it visually.
    """

    def __init__(self, x, y):
        super().__init__(x, y)
        self.color = C.MOVING_OBSTACLE_COLOR_SEEKER
        # Start with a random direction at seeker speed
        angle = random.uniform(0, 2 * math.pi)
        spd = C.SEEKER_OBSTACLE_SPEED
        self.dx = math.cos(angle) * spd
        self.dy = math.sin(angle) * spd

    def update(self, snake, obstacles):
        # Nudge velocity toward the snake head before moving
        head_x, head_y = snake.get_head_position()
        tx = head_x - self.float_x
        ty = head_y - self.float_y
        dist = math.sqrt(tx * tx + ty * ty)
        if dist > 0:
            spd = C.SEEKER_OBSTACLE_SPEED
            target_dx = (tx / dist) * spd
            target_dy = (ty / dist) * spd
            # Turn rate scales with proximity: weak pull from afar, strong lock-on up close
            turn = min(C.SEEKER_TURN_RATE_MAX, C.SEEKER_TURN_RATE_SCALE / dist)
            self.dx += (target_dx - self.dx) * turn
            self.dy += (target_dy - self.dy) * turn
            # Re-normalise so speed stays constant despite blending
            cur_spd = math.sqrt(self.dx ** 2 + self.dy ** 2)
            if cur_spd > 0:
                self.dx = (self.dx / cur_spd) * spd
                self.dy = (self.dy / cur_spd) * spd
        # Delegate movement and collision physics to parent
        super().update(snake, obstacles)

    def draw(self, surface):
        """Draw as a crimson diamond to visually distinguish from square obstacles."""
        screen_x = self.float_x * C.GRID_SIZE
        screen_y = self.float_y * C.GRID_SIZE
        cx = int(screen_x + self.width / 2)
        cy = int(screen_y + self.height / 2)
        half = self.width // 2 - 1
        points = [
            (cx,        cy - half),  # top
            (cx + half, cy),          # right
            (cx,        cy + half),  # bottom
            (cx - half, cy),          # left
        ]
        pygame.draw.polygon(surface, self.color, points)
        light = tuple(min(c + 45, 255) for c in self.color)
        inner_half = half - 3
        if inner_half > 0:
            inner_points = [
                (cx,              cy - inner_half),
                (cx + inner_half, cy),
                (cx,              cy + inner_half),
                (cx - inner_half, cy),
            ]
            pygame.draw.polygon(surface, light, inner_points)

class ShockwaveEffect:
    """Expanding multi-ring shockwave drawn at the point of a lethal collision.

    Plays at the death screen's 15-fps tick rate.  Four rings erupt with
    staggered delays and shift from white → yellow → orange → red, giving
    a clear 'impact here' read without obscuring the frozen game frame.
    """

    _RINGS = [
        # (start_tick, color,                lifespan)
        (0,  (255, 255, 255), 22),   # white
        (5,  (255, 230,  80), 22),   # yellow
        (10, (255, 130,  30), 22),   # orange
        (15, (210,  40,  40), 22),   # red
    ]
    GROWTH_RATE  = 4.5   # px per tick
    FLASH_RADIUS = 10    # px — solid centre burst
    FLASH_LIFE   = 7     # ticks the centre burst lasts

    def __init__(self, cx, cy):
        self.cx   = cx
        self.cy   = cy
        self.tick = 0
        self._total = max(d + ls for d, _, ls in self._RINGS)

    @property
    def done(self):
        return self.tick >= self._total

    def update(self):
        self.tick += 1

    def draw(self, surface):
        # Solid centre flash
        if self.tick < self.FLASH_LIFE:
            alpha = int(220 * (1.0 - self.tick / self.FLASH_LIFE))
            r = self.FLASH_RADIUS
            s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (255, 255, 255, alpha), (r, r), r)
            surface.blit(s, (self.cx - r, self.cy - r))

        # Expanding rings
        for delay, color, lifespan in self._RINGS:
            ring_tick = self.tick - delay
            if ring_tick < 0 or ring_tick >= lifespan:
                continue
            progress = ring_tick / lifespan
            radius   = max(1, int(ring_tick * self.GROWTH_RATE + 5))
            alpha    = int(255 * (1.0 - progress))
            lw       = max(1, round(3 * (1.0 - progress * 0.6)))
            diam     = radius * 2 + lw * 2 + 4
            s = pygame.Surface((diam, diam), pygame.SRCALPHA)
            pygame.draw.circle(s, (*color, alpha), (diam // 2, diam // 2), radius, lw)
            surface.blit(s, (self.cx - diam // 2, self.cy - diam // 2))


class Particle:
    """Represents a single particle in a particle effect"""
    def __init__(self, x, y):
        # Convert grid coordinates to screen coordinates for particles
        self.x = x * C.GRID_SIZE + C.GRID_SIZE // 2  # Center of grid cell
        self.y = y * C.GRID_SIZE + C.GRID_SIZE // 2
        self.size = random.randint(C.PARTICLE_MIN_SIZE, C.PARTICLE_MAX_SIZE)
        self.color = random.choice(C.PARTICLE_COLORS_APPLE)
        # Random direction
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(C.PARTICLE_MIN_SPEED, C.PARTICLE_MAX_SPEED)
        self.dx = math.cos(angle) * speed
        self.dy = math.sin(angle) * speed
        self.lifespan = C.PARTICLE_LIFESPAN
        self.alpha = 255  # Transparency (255 = fully opaque)
        
    def update(self):
        """Update particle position and lifespan"""
        self.x += self.dx
        self.y += self.dy
        self.lifespan -= 1
        # Gradually reduce alpha/transparency as particle ages
        self.alpha = int(255 * (self.lifespan / C.PARTICLE_LIFESPAN))
        return self.lifespan > 0
        
    def draw(self, surface):
        """Draw particle with appropriate transparency"""
        if self.lifespan <= 0:
            return
            
        # Create temporary surface with per-pixel alpha
        particle_surf = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        # Apply transparency to the color
        color_with_alpha = (*self.color, self.alpha)
        pygame.draw.rect(particle_surf, color_with_alpha, (0, 0, self.size, self.size))
        surface.blit(particle_surf, (int(self.x - self.size/2), int(self.y - self.size/2)))

class CirclePulse:
    """Represents a single expanding circle in a pulse effect"""
    def __init__(self, x, y, color, delay=0):
        # Convert grid coordinates to screen coordinates for the circle center
        self.x = x * C.GRID_SIZE + C.GRID_SIZE // 2
        self.y = y * C.GRID_SIZE + C.GRID_SIZE // 2
        self.radius = C.PULSE_MIN_RADIUS
        self.color = color
        self.lifespan = C.PULSE_LIFESPAN
        self.delay = delay  # Delay before starting to pulse
        self.alpha = 255  # Start fully opaque
        
    def update(self):
        """Update pulse radius and transparency"""
        if self.delay > 0:
            self.delay -= 1
            return True
            
        self.radius += C.PULSE_GROWTH_RATE
        self.lifespan -= 1
        
        # Calculate alpha based on remaining lifespan
        self.alpha = int(255 * (self.lifespan / C.PULSE_LIFESPAN))
        
        return self.lifespan > 0
    
    def draw(self, surface):
        """Draw the pulse circle with appropriate transparency"""
        if self.delay > 0 or self.lifespan <= 0:
            return
            
        # Create a temporary surface with per-pixel alpha
        size = int(self.radius * 2 + C.PULSE_LINE_WIDTH * 2)
        circle_surf = pygame.Surface((size, size), pygame.SRCALPHA)
        
        # Draw circle on the temporary surface with alpha
        color_with_alpha = (*self.color, self.alpha)
        pygame.draw.circle(
            circle_surf, 
            color_with_alpha, 
            (size // 2, size // 2), 
            self.radius, 
            C.PULSE_LINE_WIDTH
        )
        
        # Blit the circle to the main surface
        surface.blit(
            circle_surf, 
            (int(self.x - size // 2), int(self.y - size // 2))
        )

class CirclePulseEffect:
    """Creates an expanding circular pulse effect from the epicentrum"""
    def __init__(self, x, y, effect_type="apple"):
        self.pulses = []

        # Choose color palette based on effect type
        color_map = {
            "apple": C.PARTICLE_COLORS_APPLE,
            "obstacle_static": C.PARTICLE_COLORS_OBSTACLE_STATIC,
            "obstacle_orthogonal": C.PARTICLE_COLORS_OBSTACLE_ORTHOGONAL,
            "obstacle_diagonal": C.PARTICLE_COLORS_OBSTACLE_DIAGONAL,
            "obstacle_seeker": C.PARTICLE_COLORS_OBSTACLE_SEEKER,
        }
        
        # Get color palette or default to apple colors
        colors = color_map.get(effect_type, C.PARTICLE_COLORS_APPLE)
        
        # Create multiple pulses with different delays
        for i in range(C.PULSE_COUNT):
            pulse = CirclePulse(
                x, y, 
                random.choice(colors), 
                delay=i * 3  # Staggered delay for wave effect
            )
            self.pulses.append(pulse)
    
    def update(self):
        """Update all pulses and remove expired ones"""
        self.pulses = [pulse for pulse in self.pulses if pulse.update()]
        return len(self.pulses) > 0  # Effect is alive if any pulses remain
        
    def draw(self, surface):
        """Draw all pulses in the effect"""
        for pulse in self.pulses:
            pulse.draw(surface)

class ParticleEffect:
    """Manages a group of particles for an effect"""
    def __init__(self, x, y, effect_type="apple", is_spawning=False):
        self.particles = []
        self.pulses = None
        self.effect_type = effect_type

        # Choose color palette based on effect type
        color_map = {
            "apple": C.PARTICLE_COLORS_APPLE,
            "obstacle_static": C.PARTICLE_COLORS_OBSTACLE_STATIC,
            "obstacle_orthogonal": C.PARTICLE_COLORS_OBSTACLE_ORTHOGONAL,
            "obstacle_diagonal": C.PARTICLE_COLORS_OBSTACLE_DIAGONAL,
            "obstacle_seeker": C.PARTICLE_COLORS_OBSTACLE_SEEKER,
        }
        
        # Get color palette or default to apple colors
        colors = color_map.get(effect_type, C.PARTICLE_COLORS_APPLE)
        
        # Create appropriate effect based on whether object is spawning or despawning
        if is_spawning:
            # Circular pulse for spawning objects
            self.pulses = CirclePulseEffect(x, y, effect_type)
        else:
            # Dust particles for despawning objects
            for _ in range(C.PARTICLE_COUNT):
                particle = Particle(x, y)
                particle.color = random.choice(colors)
                self.particles.append(particle)
        
    def update(self):
        """Update all particles and remove dead ones"""
        # Update and check pulse effect
        if self.pulses and not self.pulses.update():
            self.pulses = None
        
        # Update and check particles
        self.particles = [particle for particle in self.particles if particle.update()]
        
        # Return True if any effect is still active
        return self.pulses is not None or len(self.particles) > 0
        
    def draw(self, surface):
        """Draw all effects"""
        if self.pulses:
            self.pulses.draw(surface)
            
        for particle in self.particles:
            particle.draw(surface)


class BuffAnnouncement:
    """Animated text pop-up that appears when a magic apple buff activates.
    Scales up with a pop, then fades out while staying semi-transparent so the
    game field remains visible underneath."""

    LIFESPAN = 32   # ticks the announcement lives

    def __init__(self, label, color):
        self.tick    = 0
        self.angle   = -9          # slight counter-clockwise tilt (degrees)
        try:
            font = pygame.font.SysFont('Arial', 54, bold=True)
        except pygame.error:
            font = pygame.font.Font(None, 60)
        self.base_surf = font.render(label, True, color)

    def update(self):
        self.tick += 1
        return self.tick < self.LIFESPAN

    def draw(self, surface):
        t = self.tick / self.LIFESPAN          # 0.0 → 1.0

        # ---- scale: pop to 1.3×, then settle to 1.0 ----
        if t < 0.20:
            scale = (t / 0.20) * 1.3
        elif t < 0.38:
            scale = 1.3 - ((t - 0.20) / 0.18) * 0.3
        else:
            scale = 1.0

        # ---- alpha: quick fade-in, hold, then fade out at the end ----
        # Max alpha kept low (175) so the game field is still visible.
        if t < 0.08:
            alpha = int((t / 0.08) * 175)
        elif t < 0.62:
            alpha = 175
        else:
            alpha = int(((1.0 - t) / 0.38) * 175)
        alpha = max(0, min(255, alpha))

        # ---- scale + rotate ----
        w = max(1, int(self.base_surf.get_width()  * scale))
        h = max(1, int(self.base_surf.get_height() * scale))
        scaled  = pygame.transform.smoothscale(self.base_surf, (w, h))
        rotated = pygame.transform.rotate(scaled, self.angle)
        rotated.set_alpha(alpha)

        cx, cy = C.SCREEN_WIDTH // 2, C.SCREEN_HEIGHT // 2
        surface.blit(rotated, rotated.get_rect(center=(cx, cy)))
