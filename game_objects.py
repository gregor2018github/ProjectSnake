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

    def get_head_position(self):
        # Returns integer grid position (compatible with existing logic)
        return self.positions[0]

    def get_float_head_position(self):
        # Returns float grid position
        return self.float_x, self.float_y

    def move(self):
        dx, dy = self.direction
        cur_x, cur_y = self.get_head_position()
        if C.WALL_COLLISION:
            new_head_grid = (cur_x + dx, cur_y + dy)
            if not (0 <= new_head_grid[0] < C.GRID_WIDTH and 0 <= new_head_grid[1] < C.GRID_HEIGHT):
                return False # Wall collision
        else:
            new_head_grid = ((cur_x + dx) % C.GRID_WIDTH, (cur_y + dy) % C.GRID_HEIGHT)

        # Check for self-collision using integer grid positions
        # Only check if the grid position actually changed to avoid false positives with float movement
        if new_head_grid != self.positions[0] and new_head_grid in self.positions[1:]:
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
        # Draw head, use integer grid position for head rect
        head_x, head_y = self.positions[0]
        head_rect = pygame.Rect(head_x * C.GRID_SIZE, head_y * C.GRID_SIZE, self.size, self.size)

        pygame.draw.rect(surface, self.head_color, head_rect)

        # Draw body segments (always based on integer grid positions)
        for i, (x, y) in enumerate(self.positions[1:]):
            segment_rect = pygame.Rect(x * C.GRID_SIZE, y * C.GRID_SIZE, self.size, self.size)
            pygame.draw.rect(surface, self.color, segment_rect)

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

class Obstacle(GameObject):
    """ Represents an obstacle """
    def __init__(self, x, y):
        super().__init__(x, y, C.OBSTACLE_SIZE[0], C.OBSTACLE_SIZE[1], C.OBSTACLE_COLOR)

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

        # Update the integer grid position (rounded down) for other logic if needed
        new_x = int(self.float_x)
        new_y = int(self.float_y)

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
        # Calculate screen coordinates directly from float_x/y
        screen_x = self.float_x * C.GRID_SIZE
        screen_y = self.float_y * C.GRID_SIZE
        # Create a temporary rect for drawing at the precise location
        draw_rect = pygame.Rect(screen_x, screen_y, self.width, self.height)
        pygame.draw.rect(surface, self.color, draw_rect)

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

class ParticleEffect:
    """Manages a group of particles for an effect"""
    def __init__(self, x, y, effect_type="apple"):
        self.particles = []
        
        # Choose color palette based on effect type
        color_map = {
            "apple": C.PARTICLE_COLORS_APPLE,
            "obstacle_static": C.PARTICLE_COLORS_OBSTACLE_STATIC,
            "obstacle_orthogonal": C.PARTICLE_COLORS_OBSTACLE_ORTHOGONAL,
            "obstacle_diagonal": C.PARTICLE_COLORS_OBSTACLE_DIAGONAL
        }
        
        # Get color palette or default to apple colors
        colors = color_map.get(effect_type, C.PARTICLE_COLORS_APPLE)
            
        for _ in range(C.PARTICLE_COUNT):
            particle = Particle(x, y)
            particle.color = random.choice(colors)
            self.particles.append(particle)
        
    def update(self):
        """Update all particles and remove dead ones"""
        self.particles = [particle for particle in self.particles if particle.update()]
        return len(self.particles) > 0  # Effect is alive if any particles remain
        
    def draw(self, surface):
        """Draw all particles in the effect"""
        for particle in self.particles:
            particle.draw(surface)
