import pygame
import random
import constants as C # Use absolute import

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
        # Ensure initial positions are within grid boundaries if needed, though wrap-around handles it
        self.positions = [(C.SNAKE_START_POS[0], C.SNAKE_START_POS[1] - i) for i in range(self.length)]
        self.direction = C.SNAKE_START_DIR
        self.color = C.SNAKE_COLOR
        self.head_color = C.SNAKE_HEAD_COLOR
        self.size = C.GRID_SIZE

    def get_head_position(self):
        return self.positions[0]

    def move(self):
        cur_x, cur_y = self.get_head_position()
        dx, dy = self.direction
        if C.WALL_COLLISION:
            new_head = (cur_x + dx, cur_y + dy)
            # Check for wall collision explicitly if WALL_COLLISION is True
            if not (0 <= new_head[0] < C.GRID_WIDTH and 0 <= new_head[1] < C.GRID_HEIGHT):
                return False # Indicate collision with wall
        else:
            # Wrap around logic
            new_head = ((cur_x + dx) % C.GRID_WIDTH, (cur_y + dy) % C.GRID_HEIGHT)

        # Check for self-collision
        if new_head in self.positions[1:]: # Check against the body, not the current head before moving
             # If the new head position is already in the body segments, it's a self-collision.
             # Note: This check should ideally happen *before* inserting the new head.
             # Let's adjust the logic slightly: calculate new_head, check collision, then update.
             return False # Indicate self-collision

        # Insert new head position
        self.positions.insert(0, new_head)

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
        # Draw head
        head_x, head_y = self.positions[0]
        head_rect = pygame.Rect(head_x * C.GRID_SIZE, head_y * C.GRID_SIZE, self.size, self.size)
        pygame.draw.rect(surface, self.head_color, head_rect)
        # Draw body segments
        for i, (x, y) in enumerate(self.positions[1:]):
            segment_rect = pygame.Rect(x * C.GRID_SIZE, y * C.GRID_SIZE, self.size, self.size)
            pygame.draw.rect(surface, self.color, segment_rect)

    def collides_with_rect(self, rect):
        head_x, head_y = self.get_head_position()
        head_rect = pygame.Rect(head_x * C.GRID_SIZE, head_y * C.GRID_SIZE, self.size, self.size)
        return head_rect.colliderect(rect)

    def collides_with_obstacles(self, obstacles):
        for obstacle in obstacles:
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
