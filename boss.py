
import pygame
from pygame.sprite import Sprite


class Boss(Sprite):
    """A different and stronger boss every five levels."""

    COLORS = [
        (255, 70, 70),    # Red Boss
        (160, 70, 255),   # Purple Boss
        (70, 220, 100),   # Green Boss
        (255, 190, 40),   # Golden Boss
        (40, 210, 255),   # Mega Boss
    ]

    def __init__(self, ai_game, tier):
        super().__init__()

        self.screen = ai_game.screen
        self.settings = ai_game.settings
        self.tier = tier

        original_image = pygame.image.load(
            "images/alien.png"
        ).convert_alpha()

        # Different size for every boss.
        scale = min(3 + tier, 7)

        width = original_image.get_width() * scale
        height = original_image.get_height() * scale

        self.image = pygame.transform.scale(
            original_image, (width, height)
        )

        # Different colour for every boss.
        color = self.COLORS[(tier - 1) % len(self.COLORS)]

        self.image.fill(
            color, special_flags=pygame.BLEND_RGBA_MULT
        )

        self.rect = self.image.get_rect()

        self.max_health = 25 * tier
        self.health = self.max_health

        self.horizontal_speed = 2 + tier * 0.5
        self.vertical_speed = 0.25 + tier * 0.08

        self.direction = 1

        self.reset_position()

    def reset_position(self):
        """Place boss back at the top after hitting the ship."""

        self.rect.midtop = (
            self.screen.get_rect().centerx, 65
        )

        self.x = float(self.rect.x)
        self.y = float(self.rect.y)

    def update(self):
        """Move boss sideways and gradually downward."""

        self.x += self.horizontal_speed * self.direction
        self.y += self.vertical_speed

        self.rect.x = int(self.x)
        self.rect.y = int(self.y)

        if self.rect.right >= self.screen.get_rect().right:
            self.direction = -1

        elif self.rect.left <= 0:
            self.direction = 1

    def draw_health_bar(self):
        """Display boss health."""

        bar_width = 300
        bar_height = 20

        x = self.screen.get_rect().centerx - bar_width // 2
        y = 20

        pygame.draw.rect(
            self.screen, (100, 0, 0),
            (x, y, bar_width, bar_height)
        )

        health_width = int(
            bar_width * max(0, self.health) / self.max_health
        )

        pygame.draw.rect(
            self.screen, (0, 230, 0),
            (x, y, health_width, bar_height)
        )

        pygame.draw.rect(
            self.screen, (255, 255, 255),
            (x, y, bar_width, bar_height), 2
        )
