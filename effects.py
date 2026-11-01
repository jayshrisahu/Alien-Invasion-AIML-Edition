
import pygame
import random


class Explosion:
    """Create a particle explosion effect."""

    def __init__(self, x, y):
        self.particles = []

        for _ in range(25):
            particle = {
                "x": float(x),
                "y": float(y),
                "dx": random.uniform(-4, 4),
                "dy": random.uniform(-4, 4),
                "life": random.randint(15, 30),
                "radius": random.randint(2, 5),
                "color": random.choice([
                    (255, 80, 0),
                    (255, 180, 0),
                    (255, 255, 0),
                    (255, 255, 255)
                ])
            }

            self.particles.append(particle)

    def update(self):
        """Move particles and decrease their lifetime."""

        for particle in self.particles:
            particle["x"] += particle["dx"]
            particle["y"] += particle["dy"]
            particle["life"] -= 1

        self.particles = [
            p for p in self.particles if p["life"] > 0
        ]

    def draw(self, screen):
        """Draw explosion particles."""

        for particle in self.particles:
            pygame.draw.circle(
                screen,
                particle["color"],
                (int(particle["x"]), int(particle["y"])),
                particle["radius"]
            )

    def finished(self):
        return len(self.particles) == 0
