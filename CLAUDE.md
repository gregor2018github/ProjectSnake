# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the Game

The project uses a local virtual environment at `snake_envi/`. Activate it before running:

```bash
# Windows
snake_envi/Scripts/activate
python main.py
```

No build step, no tests, no linter configured.

## Architecture

```
main.py           → Entry point: instantiates Game and calls game.run()
game.py           → Game class: main loop, state management, collision handling, high score flow
game_objects.py   → All game entities and visual effects
screen.py         → Screen class: all rendering and UI drawing
constants.py      → All tunable constants (speeds, colors, sizes, score thresholds, messages)
high_scores.py    → load/save high scores to Files/highscores.txt (CSV: "name,score")
magic_apple_logic.py → Stub file for future magic apple buff effects (currently empty)
```

### Game Loop

`Game.run()` calls per tick: `handle_events()` → `update_game_state()` → `check_collisions()` → `draw()`. Game speed is controlled by `self.game_speed` (ticks/sec, initially `SNAKE_SPEED_INITIAL`).

Direction changes are buffered via `self.next_direction` and applied at the start of each `update_game_state()` call, preventing the 180° reversal bug.

### Coordinate System

The game uses a **grid coordinate system** (30×30 cells). `GRID_SIZE = 20` px per cell on a 600×600 screen. Game objects store grid positions (`self.x`, `self.y`). `MovingObstacle` additionally tracks sub-grid float positions (`self.float_x`, `self.float_y`) for smooth movement.

### Level Progression (score-based)

| Level | Score threshold | Obstacle type spawned per apple |
|-------|----------------|--------------------------------|
| 1     | start          | Static (gray)                   |
| 2     | 25             | Orthogonal moving (orange)      |
| 3     | 45             | Diagonal moving (purple)        |
| 4     | 65             | No new obstacles                |

On level transition, the previous level's obstacles are **gradually removed** one-by-one via `removing_static_obstacles`, `removing_orthogonal_obstacles`, and `removing_diagonal_obstacles` flags, timed by `frame_counter`.

### Game Objects Hierarchy

- `GameObject` (base): grid position, rect, color, `draw()`
  - `Apple` – respawns randomly on a free grid cell
  - `MagicApple` – gold, 10% spawn chance when normal apple eaten; despawns after `MAGIC_APPLE_LIFESPAN` ticks (±50% random variation); worth 5 points; `type` field references a `MAGIC_APPLE_TYPES` string for future buff dispatch via `magic_apple_logic.py`
  - `Obstacle` – static gray block
  - `MovingObstacle` – diagonal float movement, bounces off walls/snake body/static obstacles
    - `OrthogonalMovingObstacle` – subclass; movement restricted to one axis only

Visual effects live entirely in `game_objects.py`:
- `ParticleEffect`: spawning objects → `CirclePulseEffect` (expanding rings); despawning → dust `Particle` spray
- Colors per effect type are defined in `constants.py` (`PARTICLE_COLORS_*`)

### Adding a New Magic Apple Buff

1. Add a new string to `MAGIC_APPLE_TYPES` in `constants.py`
2. Implement the corresponding function in `magic_apple_logic.py`
3. Dispatch it in `Game.check_collisions()` where magic apples are consumed (currently only score/grow is done there)

## Controls

| Key            | Action              |
|----------------|---------------------|
| Arrow keys / WASD | Move snake       |
| Space          | Pause / unpause     |
| ESC            | Quit                |
| Enter          | Restart after death |

## Key Constants to Know

- `WALL_COLLISION` (False) – walls wrap instead of killing
- `MAGIC_APPLE_SPAWN_PROBABILITY` (0.1) – 10% chance per normal apple eaten
- `LEVEL_2_SCORE`, `LEVEL_3_SCORE`, `LEVEL_4_SCORE` – score thresholds for level-ups
- `SNAKE_SPEED_INITIAL` – ticks per second (game speed)
- `MIN_OBSTACLE_SPAWN_DISTANCE` – Manhattan distance from snake head enforced for all spawns
