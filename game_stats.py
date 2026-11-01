class GameStats:
    """Track game statistics and player-performance data."""

    def __init__(self, ai_game):
        self.settings = ai_game.settings
        self.high_score = 0
        self.reset_stats()

    def reset_stats(self):
        self.ships_left = self.settings.ship_limit
        self.score = 0
        self.level = 1
        self.shots_fired = 0
        self.shots_hit = 0
        self.start_ticks = 0
        self.lives_lost = 0

    @property
    def shooting_accuracy(self):
        if self.shots_fired == 0:
            return 0.0
        return self.shots_hit / self.shots_fired
