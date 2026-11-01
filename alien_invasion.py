import sys
import csv
import os
from time import sleep

import pygame

from settings import Settings
from game_stats import GameStats
from scoreboard import Scoreboard
from button import Button
from ship import Ship
from bullet import Bullet
from alien import Alien
from boss import Boss
from effects import Explosion
from ml_model import PlayerDifficultyModel


class AlienInvasion:

    def __init__(self):
        pygame.init()

        self.clock = pygame.time.Clock()
        self.settings = Settings()
        self.ml_model = PlayerDifficultyModel()
        self.ml_label = "Not classified yet"
        self.ml_confidence = 0.0
        self.ml_cluster = "Pending"
        self.ml_multiplier = 1.0
        self.ml_last_update = 0

        self.screen = pygame.display.set_mode(
            (self.settings.screen_width,
             self.settings.screen_height)
        )

        pygame.display.set_caption("Alien Invasion")

        # SOUND SYSTEM
        self.sounds = {}
        self._load_sounds()

        self.stats = GameStats(self)
        self.sb = Scoreboard(self)

        self.ship = Ship(self)
        self.bullets = pygame.sprite.Group()
        self.aliens = pygame.sprite.Group()

        self.boss = None
        self.explosions = []

        # Level transition system
        self.level_up_until = 0
        self.previous_level = 1
        self.pending_boss_tier = 0

        # Boss warning system
        self.boss_warning_until = 0
        self.boss_warning_tier = 0

        # Fonts
        self.warning_font = pygame.font.SysFont(None, 85)
        self.warning_small_font = pygame.font.SysFont(None, 40)
        self.level_font = pygame.font.SysFont(None, 100)
        self.level_small_font = pygame.font.SysFont(None, 45)

        self._create_fleet()

        self.game_active = False
        self.game_over = False

        self.play_button = Button(self, "PLAY")

        self.title_font = pygame.font.SysFont(None, 90)
        self.instruction_font = pygame.font.SysFont(None, 38)
        self.game_over_font = pygame.font.SysFont(None, 100)

    # -----------------------------------------
    # SOUND FUNCTIONS
    # -----------------------------------------

    def _load_sounds(self):

        sound_files = {
            "shoot": "sounds/shoot.wav",
            "alien_explosion": "sounds/alien_explosion.wav",
            "boss_warning": "sounds/boss_warning.wav",
            "boss_defeated": "sounds/boss_defeated.wav",
            "ship_hit": "sounds/ship_hit.wav",
            "level_up": "sounds/level_up.wav",
            "game_over": "sounds/game_over.wav",
        }

        for name, path in sound_files.items():

            try:
                self.sounds[name] = pygame.mixer.Sound(path)

            except (pygame.error, FileNotFoundError):
                self.sounds[name] = None
                print(f"Sound not found or could not load: {path}")

        # Sound effect volume
        for sound in self.sounds.values():

            if sound is not None:
                sound.set_volume(0.5)

        # Music volume
        try:
            pygame.mixer.music.set_volume(0.35)

        except pygame.error:
            pass

    def _play_sound(self, name):

        sound = self.sounds.get(name)

        if sound is not None:
            sound.play()

    def _start_boss_music(self):

        try:
            pygame.mixer.music.load("sounds/boss_music.mp3")
            pygame.mixer.music.play(-1)

        except (pygame.error, FileNotFoundError):
            print("Boss music could not be loaded.")

    def _stop_boss_music(self):

        try:
            pygame.mixer.music.stop()

        except pygame.error:
            pass

    # -----------------------------------------
    # MAIN GAME LOOP
    # -----------------------------------------

    def run_game(self):

        while True:

            self._check_events()

            if self.game_active:

                self._update_ml_difficulty()
                self._update_level_transition()
                self._update_boss_warning()

                if (
                    self.level_up_until == 0
                    and self.boss_warning_until == 0
                ):
                    self.ship.update()
                    self._update_bullets()
                    self._update_aliens()

                self._update_explosions()

            self._update_screen()
            self.clock.tick(60)

    # -----------------------------------------
    # EVENTS
    # -----------------------------------------

    def _check_events(self):

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            elif event.type == pygame.KEYDOWN:
                self._check_keydown_events(event)

            elif event.type == pygame.KEYUP:
                self._check_keyup_events(event)

            elif event.type == pygame.MOUSEBUTTONDOWN:

                mouse_pos = pygame.mouse.get_pos()
                self._check_play_button(mouse_pos)

    def _check_play_button(self, mouse_pos):

        button_clicked = self.play_button.rect.collidepoint(
            mouse_pos
        )

        if button_clicked and not self.game_active:

            self.settings.initialize_dynamic_settings()

            self.stats.reset_stats()
            self.stats.start_ticks = pygame.time.get_ticks()
            self.ml_label = "Not classified yet"
            self.ml_confidence = 0.0
            self.ml_cluster = "Pending"
            self.ml_multiplier = 1.0
            self.ml_last_update = pygame.time.get_ticks()
            self._apply_ml_difficulty(1.0)

            self.sb.prep_score()
            self.sb.prep_level()
            self.sb.prep_ships()

            self.game_active = True
            self.game_over = False

            self.bullets.empty()
            self.aliens.empty()

            self.boss = None
            self.explosions.clear()

            self._stop_boss_music()

            self.level_up_until = 0
            self.previous_level = 1
            self.pending_boss_tier = 0

            self.boss_warning_until = 0
            self.boss_warning_tier = 0

            self._create_fleet()
            self.ship.center_ship()

            self.ship.moving_right = False
            self.ship.moving_left = False

            pygame.mouse.set_visible(False)

    def _check_keydown_events(self, event):

        if event.key == pygame.K_RIGHT:
            self.ship.moving_right = True

        elif event.key == pygame.K_LEFT:
            self.ship.moving_left = True

        elif event.key == pygame.K_SPACE and self.game_active:
            self._fire_bullet()

        elif event.key == pygame.K_q:
            pygame.quit()
            sys.exit()

    def _check_keyup_events(self, event):

        if event.key == pygame.K_RIGHT:
            self.ship.moving_right = False

        elif event.key == pygame.K_LEFT:
            self.ship.moving_left = False

    # -----------------------------------------
    # BULLETS
    # -----------------------------------------

    def _fire_bullet(self):

        if (
            self.level_up_until > 0
            or self.boss_warning_until > 0
        ):
            return

        if len(self.bullets) < self.settings.bullets_allowed:

            new_bullet = Bullet(self)
            self.bullets.add(new_bullet)
            self.stats.shots_fired += 1

            self._play_sound("shoot")

    def _update_bullets(self):

        self.bullets.update()

        for bullet in self.bullets.copy():

            if bullet.rect.bottom <= 0:
                self.bullets.remove(bullet)

        self._check_bullet_alien_collisions()
        self._check_bullet_boss_collisions()

    def _check_bullet_alien_collisions(self):

        collisions = pygame.sprite.groupcollide(
            self.bullets, self.aliens, True, True
        )

        if collisions:

            self.stats.shots_hit += len(collisions)
            self._play_sound("alien_explosion")

            for alien_list in collisions.values():

                for alien in alien_list:

                    self.explosions.append(
                        Explosion(
                            alien.rect.centerx,
                            alien.rect.centery
                        )
                    )

                self.stats.score += (
                    self.settings.alien_points *
                    len(alien_list)
                )

            self.sb.prep_score()
            self.sb.check_high_score()

        if (
            not self.aliens
            and self.boss is None
            and self.boss_warning_until == 0
            and self.level_up_until == 0
        ):
            self._advance_level()

    def _check_bullet_boss_collisions(self):

        if self.boss is None:
            return

        hits = pygame.sprite.spritecollide(
            self.boss, self.bullets, True
        )

        if hits:

            self.stats.shots_hit += len(hits)
            self.boss.health -= len(hits)

            if self.boss.health <= 0:

                self.explosions.append(
                    Explosion(
                        self.boss.rect.centerx,
                        self.boss.rect.centery
                    )
                )

                self._play_sound("boss_defeated")
                self._stop_boss_music()

                self.stats.score += 1000

                self.sb.prep_score()
                self.sb.check_high_score()

                self.boss = None

                self._advance_level()

    # -----------------------------------------
    # MACHINE LEARNING DIFFICULTY ADAPTATION
    # -----------------------------------------

    def _apply_ml_difficulty(self, multiplier):
        """Apply the ML multiplier to the base alien speed."""
        self.ml_multiplier = multiplier
        self.settings.alien_speed = self.settings.alien_speed_base * multiplier

    def _update_ml_difficulty(self):
        """Classify player performance every 20 seconds."""
        now = pygame.time.get_ticks()
        if now - self.ml_last_update < 20000:
            return

        self.ml_last_update = now
        survival_seconds = (now - self.stats.start_ticks) / 1000
        label, multiplier, confidence, cluster_label = self.ml_model.predict(
            self.stats.shooting_accuracy,
            survival_seconds,
            self.stats.lives_lost
        )
        self.ml_label = label
        self.ml_confidence = confidence
        self.ml_cluster = cluster_label
        self._apply_ml_difficulty(multiplier)

    # -----------------------------------------
    # LEVEL SYSTEM
    # -----------------------------------------

    def _advance_level(self):

        self.bullets.empty()

        self.settings.increase_speed()
        self._apply_ml_difficulty(self.ml_multiplier)

        self.previous_level = self.stats.level

        self.stats.level += 1
        self.sb.prep_level()

        self.aliens.empty()
        self.boss = None

        self.level_up_until = pygame.time.get_ticks() + 2000

        self._play_sound("level_up")

        if self.stats.level % 5 == 0:

            self.pending_boss_tier = self.stats.level // 5

        else:

            self.pending_boss_tier = 0

    def _update_level_transition(self):

        if self.level_up_until == 0:
            return

        if pygame.time.get_ticks() >= self.level_up_until:

            self.level_up_until = 0

            if self.pending_boss_tier > 0:

                self.boss_warning_tier = self.pending_boss_tier

                self.boss_warning_until = (
                    pygame.time.get_ticks() + 3000
                )

                self._play_sound("boss_warning")

                self.pending_boss_tier = 0

            else:

                self._create_fleet()

    # -----------------------------------------
    # BOSS SYSTEM
    # -----------------------------------------

    def _update_boss_warning(self):

        if self.boss_warning_until == 0:
            return

        if pygame.time.get_ticks() >= self.boss_warning_until:

            self.boss = Boss(self, self.boss_warning_tier)

            self.boss_warning_until = 0

            self._start_boss_music()

    # -----------------------------------------
    # EXPLOSIONS
    # -----------------------------------------

    def _update_explosions(self):

        for explosion in self.explosions[:]:

            explosion.update()

            if explosion.finished():
                self.explosions.remove(explosion)

    # -----------------------------------------
    # SHIP HIT
    # -----------------------------------------

    def _ship_hit(self):

        self.stats.ships_left -= 1
        self.stats.lives_lost += 1
        self.sb.prep_ships()

        self._play_sound("ship_hit")

        if self.stats.ships_left > 0:

            self.bullets.empty()
            self.aliens.empty()

            if self.boss is not None:

                self.boss.reset_position()

            else:

                self._create_fleet()

            self.ship.center_ship()

            self.ship.moving_right = False
            self.ship.moving_left = False

            sleep(0.5)

        else:

            self._save_gameplay_data()
            self.game_active = False
            self.game_over = True

            self._stop_boss_music()
            self._play_sound("game_over")

            pygame.mouse.set_visible(True)

    def _save_gameplay_data(self):
        """Append the completed session's performance features to a CSV file."""
        file_exists = os.path.exists("gameplay_data.csv")
        survival_seconds = max(
            0, (pygame.time.get_ticks() - self.stats.start_ticks) / 1000
        )

        with open("gameplay_data.csv", "a", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            if not file_exists:
                writer.writerow([
                    "score", "level", "shooting_accuracy",
                    "survival_seconds", "lives_lost", "ml_player_group",
                    "rf_confidence", "kmeans_cluster"
                ])

            writer.writerow([
                self.stats.score,
                self.stats.level,
                round(self.stats.shooting_accuracy, 3),
                round(survival_seconds, 1),
                self.stats.lives_lost,
                self.ml_label,
                round(getattr(self, "ml_confidence", 0.0), 3),
                getattr(self, "ml_cluster", "Pending")
            ])

    # -----------------------------------------
    # ALIEN MOVEMENT
    # -----------------------------------------

    def _update_aliens(self):

        if self.boss is not None:

            self.boss.update()

            if (
                pygame.sprite.collide_rect(self.ship, self.boss)
                or self.boss.rect.bottom >=
                self.settings.screen_height
            ):
                self._ship_hit()

        else:

            self._check_fleet_edges()
            self.aliens.update()

            if pygame.sprite.spritecollideany(
                self.ship, self.aliens
            ):
                self._ship_hit()

            self._check_aliens_bottom()

    def _check_aliens_bottom(self):

        for alien in self.aliens.sprites():

            if alien.rect.bottom >= self.settings.screen_height:

                self._ship_hit()
                break

    # -----------------------------------------
    # CREATE ALIEN FLEET
    # -----------------------------------------

    def _create_fleet(self):

        alien = Alien(self)

        alien_width, alien_height = alien.rect.size

        current_x = alien_width
        current_y = alien_height

        while current_y < (
            self.settings.screen_height - 3 * alien_height
        ):

            while current_x < (
                self.settings.screen_width - 2 * alien_width
            ):

                self._create_alien(current_x, current_y)

                current_x += 2 * alien_width

            current_x = alien_width
            current_y += 2 * alien_height

    def _create_alien(self, x_position, y_position):

        new_alien = Alien(self)

        new_alien.x = x_position
        new_alien.rect.x = x_position
        new_alien.rect.y = y_position

        self.aliens.add(new_alien)

    def _check_fleet_edges(self):

        for alien in self.aliens.sprites():

            if alien.check_edges():

                self._change_fleet_direction()
                break

    def _change_fleet_direction(self):

        for alien in self.aliens.sprites():

            alien.rect.y += self.settings.fleet_drop_speed

        self.settings.fleet_direction *= -1

    # -----------------------------------------
    # SCREEN DISPLAY
    # -----------------------------------------

    def _update_screen(self):

        self.screen.fill(self.settings.bg_color)

        if self.game_active:

            # Draw bullets
            for bullet in self.bullets.sprites():
                bullet.draw_bullet()

            # Draw ship and aliens
            self.ship.blitme()
            self.aliens.draw(self.screen)

            # Draw boss
            if self.boss is not None:

                self.screen.blit(
                    self.boss.image,
                    self.boss.rect
                )

                self.boss.draw_health_bar()

            # Draw explosions
            for explosion in self.explosions:
                explosion.draw(self.screen)

            self.sb.show_score()

            ml_text = pygame.font.SysFont(None, 30).render(
                f"RF: {self.ml_label} ({self.ml_confidence:.0%}) | "
                f"K-Means: {self.ml_cluster} | Speed x{self.ml_multiplier:.2f}",
                True,
                (0, 80, 150)
            )
            self.screen.blit(ml_text, (20, 65))

            # LEVEL UP ANNOUNCEMENT
            if self.level_up_until > 0:

                level_title = self.level_font.render(
                    "LEVEL UP!",
                    True,
                    (255, 215, 0)
                )

                level_title_rect = level_title.get_rect(
                    center=(
                        self.settings.screen_width // 2,
                        self.settings.screen_height // 2 - 65
                    )
                )

                self.screen.blit(
                    level_title,
                    level_title_rect
                )

                level_text = self.level_small_font.render(
                    f"LEVEL {self.previous_level}  >>  LEVEL {self.stats.level}",
                    True,
                    (255, 255, 255)
                )

                level_text_rect = level_text.get_rect(
                    center=(
                        self.settings.screen_width // 2,
                        self.settings.screen_height // 2 + 10
                    )
                )

                self.screen.blit(
                    level_text,
                    level_text_rect
                )

                get_ready = self.level_small_font.render(
                    "GET READY!",
                    True,
                    (100, 255, 100)
                )

                ready_rect = get_ready.get_rect(
                    center=(
                        self.settings.screen_width // 2,
                        self.settings.screen_height // 2 + 70
                    )
                )

                self.screen.blit(get_ready, ready_rect)

            # BOSS INCOMING ANNOUNCEMENT
            elif self.boss_warning_until > 0:

                remaining = (
                    self.boss_warning_until -
                    pygame.time.get_ticks()
                )

                if (remaining // 300) % 2 == 0:

                    warning = self.warning_font.render(
                        "!!! BOSS INCOMING !!!",
                        True,
                        (255, 0, 0)
                    )

                    warning_rect = warning.get_rect(
                        center=(
                            self.settings.screen_width // 2,
                            self.settings.screen_height // 2
                        )
                    )

                    self.screen.blit(
                        warning,
                        warning_rect
                    )

                prepare_text = self.warning_small_font.render(
                    "PREPARE FOR BATTLE!",
                    True,
                    (255, 220, 0)
                )

                prepare_rect = prepare_text.get_rect(
                    center=(
                        self.settings.screen_width // 2,
                        self.settings.screen_height // 2 + 65
                    )
                )

                self.screen.blit(
                    prepare_text,
                    prepare_rect
                )

        else:

            if self.game_over:

                title = self.game_over_font.render(
                    "GAME OVER!",
                    True,
                    (220, 0, 0)
                )

            else:

                title = self.title_font.render(
                    "ALIEN INVASION",
                    True,
                    (0, 0, 120)
                )

            title_rect = title.get_rect()
            title_rect.centerx = (
                self.settings.screen_width // 2
            )
            title_rect.top = 100

            self.screen.blit(title, title_rect)

            if not self.game_over:

                instructions = [
                    "GAME RULES",
                    "",
                    "SPACE - Fire Bullets",
                    "LEFT ARROW - Move Left",
                    "RIGHT ARROW - Move Right",
                    "Q - Quit Game",
                    "",
                    "Defeat aliens and survive Boss Battles!"
                ]

                y_position = 260

                for line in instructions:

                    text = self.instruction_font.render(
                        line,
                        True,
                        (30, 30, 30)
                    )

                    text_rect = text.get_rect()
                    text_rect.centerx = (
                        self.settings.screen_width // 2
                    )
                    text_rect.top = y_position

                    self.screen.blit(text, text_rect)

                    y_position += 48

            else:

                message = self.instruction_font.render(
                    "Your 3 lives are over!",
                    True,
                    (30, 30, 30)
                )

                message_rect = message.get_rect()
                message_rect.centerx = (
                    self.settings.screen_width // 2
                )
                message_rect.top = 260

                self.screen.blit(message, message_rect)

            self.play_button.draw_button()

        pygame.display.flip()


if __name__ == '__main__':

    ai = AlienInvasion()
    ai.run_game()