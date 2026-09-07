"""
Car Dodge Game
==============
A simple arcade-style car game built with Pygame.

Controls:
  - LEFT / RIGHT arrow keys (or A / D): move your car
  - UP / DOWN arrow keys (or W / S): speed up / slow down
  - P: pause / unpause
  - R: restart after game over
  - ESC: quit

Goal:
  Dodge the oncoming traffic for as long as you can. Your score increases
  over time and the game gets progressively harder (traffic speeds up and
  spawns more often).

Requirements:
  pip install pygame

Run:
  python car_game.py
"""

import pygame
import random
import sys

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
pygame.init()

WIDTH, HEIGHT = 480, 700
ROAD_WIDTH = 360
ROAD_X = (WIDTH - ROAD_WIDTH) // 2
LANE_COUNT = 3
LANE_WIDTH = ROAD_WIDTH // LANE_COUNT

FPS = 60

WHITE = (245, 245, 245)
BLACK = (20, 20, 20)
GRAY = (60, 60, 60)
LIGHT_GRAY = (110, 110, 110)
YELLOW = (240, 200, 40)
RED = (220, 60, 60)
BLUE = (60, 130, 220)
GREEN = (60, 200, 100)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Car Dodge")
clock = pygame.time.Clock()

font_big = pygame.font.SysFont("arial", 48, bold=True)
font_med = pygame.font.SysFont("arial", 28, bold=True)
font_small = pygame.font.SysFont("arial", 20)


# ---------------------------------------------------------------------------
# Helper classes
# ---------------------------------------------------------------------------
class Car:
    """The player's car."""

    def __init__(self):
        self.width = 46
        self.height = 80
        self.lane = LANE_COUNT // 2
        self.x = self.lane_x(self.lane)
        self.y = HEIGHT - self.height - 30
        self.speed_x = 8  # horizontal move speed

    def lane_x(self, lane):
        center = ROAD_X + lane * LANE_WIDTH + LANE_WIDTH // 2
        return center - self.width // 2

    def move(self, keys):
        target_x = self.lane_x(self.lane)
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.x -= self.speed_x
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.x += self.speed_x
        # keep on road
        self.x = max(ROAD_X + 4, min(self.x, ROAD_X + ROAD_WIDTH - self.width - 4))

    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.width, self.height)

    def draw(self, surface):
        r = self.rect()
        pygame.draw.rect(surface, BLUE, r, border_radius=10)
        # windows
        pygame.draw.rect(surface, WHITE, (r.x + 6, r.y + 10, r.width - 12, 18), border_radius=4)
        pygame.draw.rect(surface, WHITE, (r.x + 6, r.y + r.height - 28, r.width - 12, 18), border_radius=4)
        # wheels
        pygame.draw.rect(surface, BLACK, (r.x - 4, r.y + 8, 6, 18), border_radius=2)
        pygame.draw.rect(surface, BLACK, (r.x + r.width - 2, r.y + 8, 6, 18), border_radius=2)
        pygame.draw.rect(surface, BLACK, (r.x - 4, r.y + r.height - 26, 6, 18), border_radius=2)
        pygame.draw.rect(surface, BLACK, (r.x + r.width - 2, r.y + r.height - 26, 6, 18), border_radius=2)


class Obstacle:
    """An oncoming enemy car."""

    def __init__(self, speed):
        self.width = 46
        self.height = 80
        lane = random.randint(0, LANE_COUNT - 1)
        center = ROAD_X + lane * LANE_WIDTH + LANE_WIDTH // 2
        self.x = center - self.width // 2
        self.y = -self.height
        self.speed = speed
        self.color = random.choice([RED, GREEN, YELLOW, (200, 100, 220)])

    def update(self):
        self.y += self.speed

    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.width, self.height)

    def off_screen(self):
        return self.y > HEIGHT

    def draw(self, surface):
        r = self.rect()
        pygame.draw.rect(surface, self.color, r, border_radius=10)
        pygame.draw.rect(surface, WHITE, (r.x + 6, r.y + 10, r.width - 12, 18), border_radius=4)
        pygame.draw.rect(surface, WHITE, (r.x + 6, r.y + r.height - 28, r.width - 12, 18), border_radius=4)


# ---------------------------------------------------------------------------
# Game state
# ---------------------------------------------------------------------------
class Game:
    def __init__(self):
        self.reset()

    def reset(self):
        self.car = Car()
        self.obstacles = []
        self.score = 0.0
        self.base_speed = 6
        self.spawn_timer = 0
        self.spawn_interval = 55  # frames between spawns, decreases over time
        self.game_over = False
        self.paused = False
        self.road_scroll = 0

    def spawn_obstacle(self):
        speed = self.base_speed + random.uniform(0, 2)
        self.obstacles.append(Obstacle(speed))

    def update(self):
        if self.game_over or self.paused:
            return

        keys = pygame.key.get_pressed()
        self.car.move(keys)

        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.base_speed = min(self.base_speed + 0.05, 16)
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.base_speed = max(self.base_speed - 0.05, 3)

        self.spawn_timer += 1
        if self.spawn_timer >= self.spawn_interval:
            self.spawn_timer = 0
            self.spawn_obstacle()
            # difficulty ramps up
            self.spawn_interval = max(20, self.spawn_interval - 0.5)

        for obs in self.obstacles:
            obs.update()
        self.obstacles = [o for o in self.obstacles if not o.off_screen()]

        # collision check
        car_rect = self.car.rect()
        for obs in self.obstacles:
            if car_rect.colliderect(obs.rect()):
                self.game_over = True

        self.score += self.base_speed * 0.05
        self.road_scroll = (self.road_scroll + self.base_speed) % 40

    def draw_road(self, surface):
        surface.fill(GRAY)
        pygame.draw.rect(surface, LIGHT_GRAY, (ROAD_X, 0, ROAD_WIDTH, HEIGHT))
        # lane dividers
        for lane in range(1, LANE_COUNT):
            x = ROAD_X + lane * LANE_WIDTH
            y = -40 + self.road_scroll
            while y < HEIGHT:
                pygame.draw.rect(surface, YELLOW, (x - 3, y, 6, 24))
                y += 40
        # road edges
        pygame.draw.rect(surface, WHITE, (ROAD_X - 6, 0, 6, HEIGHT))
        pygame.draw.rect(surface, WHITE, (ROAD_X + ROAD_WIDTH, 0, 6, HEIGHT))

    def draw_hud(self, surface):
        score_text = font_small.render(f"Score: {int(self.score)}", True, WHITE)
        speed_text = font_small.render(f"Speed: {self.base_speed:.1f}", True, WHITE)
        surface.blit(score_text, (10, 10))
        surface.blit(speed_text, (10, 34))

        if self.paused:
            self._center_message(surface, "PAUSED", "Press P to resume")
        if self.game_over:
            self._center_message(surface, "GAME OVER", "Press R to restart")

    def _center_message(self, surface, title, subtitle):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        surface.blit(overlay, (0, 0))

        title_surf = font_big.render(title, True, WHITE)
        sub_surf = font_med.render(subtitle, True, WHITE)
        surface.blit(title_surf, title_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 20)))
        surface.blit(sub_surf, sub_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 30)))

    def draw(self, surface):
        self.draw_road(surface)
        self.car.draw(surface)
        for obs in self.obstacles:
            obs.draw(surface)
        self.draw_hud(surface)


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------
def main():
    game = Game()
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_p and not game.game_over:
                    game.paused = not game.paused
                elif event.key == pygame.K_r and game.game_over:
                    game.reset()

        game.update()
        game.draw(screen)
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
