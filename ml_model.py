"""AI/ML engine for Alien Invasion.

Two models are used:
1. K-Means: unsupervised clustering of player-performance profiles.
2. Random Forest: supervised classification of performance levels.

The starter training profiles are simulated. Real completed sessions are
stored in gameplay_data.csv for later analysis and future retraining.
"""
import numpy as np
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler


class PlayerDifficultyModel:
    FEATURES = ["shooting_accuracy", "survival_seconds", "lives_lost"]
    LEVELS = {
        "Beginner": 0.85,
        "Intermediate": 1.00,
        "Advanced": 1.15,
    }

    def __init__(self):
        rng = np.random.default_rng(42)
        beginner = np.column_stack((
            rng.uniform(0.05, 0.38, 250),
            rng.uniform(5, 55, 250),
            rng.integers(1, 4, 250),
        ))
        intermediate = np.column_stack((
            rng.uniform(0.30, 0.72, 250),
            rng.uniform(35, 150, 250),
            rng.integers(0, 3, 250),
        ))
        advanced = np.column_stack((
            rng.uniform(0.65, 1.00, 250),
            rng.uniform(100, 300, 250),
            rng.integers(0, 2, 250),
        ))

        X = np.vstack((beginner, intermediate, advanced))
        y = np.array(
            ["Beginner"] * len(beginner)
            + ["Intermediate"] * len(intermediate)
            + ["Advanced"] * len(advanced)
        )

        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)

        self.classifier = RandomForestClassifier(
            n_estimators=150, max_depth=8, random_state=42,
            class_weight="balanced"
        )
        self.classifier.fit(X_scaled, y)

        self.cluster_model = KMeans(n_clusters=3, random_state=42, n_init=10)
        self.cluster_model.fit(X_scaled)
        self.cluster_names = self._name_clusters()
        self.training_accuracy = self.classifier.score(X_scaled, y)

    def _name_clusters(self):
        centers = self.scaler.inverse_transform(self.cluster_model.cluster_centers_)
        score = centers[:, 0] * 100 + centers[:, 1] * 0.25 - centers[:, 2] * 12
        order = np.argsort(score)
        return {
            int(order[0]): "Beginner",
            int(order[1]): "Intermediate",
            int(order[2]): "Advanced",
        }

    def predict(self, accuracy, survival_seconds, lives_lost):
        features = np.array([[
            float(np.clip(accuracy, 0.0, 1.0)),
            float(np.clip(survival_seconds, 0.0, 300.0)),
            float(np.clip(lives_lost, 0, 3)),
        ]])
        scaled = self.scaler.transform(features)

        # Random Forest is the main prediction model.
        predicted_level = str(self.classifier.predict(scaled)[0])
        probabilities = self.classifier.predict_proba(scaled)[0]
        confidence = float(np.max(probabilities))

        # K-Means independently finds the nearest performance cluster.
        cluster_id = int(self.cluster_model.predict(scaled)[0])
        cluster_level = self.cluster_names[cluster_id]

        return (
            predicted_level,
            self.LEVELS[predicted_level],
            confidence,
            cluster_level,
        )
