"""Visualise completed Alien Invasion gameplay sessions."""
import os
import pandas as pd
import matplotlib.pyplot as plt

DATA_FILE = "gameplay_data.csv"


def main():
    if not os.path.exists(DATA_FILE):
        print("No gameplay_data.csv found. Play the game until Game Over first.")
        return

    data = pd.read_csv(DATA_FILE)
    if data.empty:
        print("The gameplay dataset is empty. Complete a game session first.")
        return

    print("\nAI/ML GAMEPLAY ANALYSIS")
    print("----------------------")
    print(f"Total recorded sessions: {len(data)}")
    print(f"Average score: {data['score'].mean():.1f}")
    print(f"Average shooting accuracy: {data['shooting_accuracy'].mean() * 100:.1f}%")
    print(f"Average survival time: {data['survival_seconds'].mean():.1f} seconds")
    print("\nPredicted player groups:")
    print(data["ml_player_group"].value_counts().to_string())

    data["session"] = range(1, len(data) + 1)
    data.plot(x="session", y="shooting_accuracy", marker="o", legend=False,
              title="Player Shooting Accuracy Across Sessions")
    plt.ylabel("Accuracy (0 to 1)")
    plt.tight_layout()
    plt.show()

    data.plot(x="session", y="survival_seconds", marker="o", legend=False,
              title="Player Survival Time Across Sessions")
    plt.ylabel("Seconds")
    plt.tight_layout()
    plt.show()

    data["ml_player_group"].value_counts().plot(kind="bar",
              title="ML Player Performance Classification")
    plt.xlabel("Predicted player group")
    plt.ylabel("Number of sessions")
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
