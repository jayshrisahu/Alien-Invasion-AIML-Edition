ALIEN INVASION - AI/ML EDITION
================================

PROJECT IDEA
An AI-powered arcade game that analyses player performance and adapts game
difficulty using Machine Learning. Pygame handles the game interface and
physics; the ML engine makes player-performance predictions.

MACHINE LEARNING USED
1. Random Forest Classifier (supervised learning): predicts Beginner,
   Intermediate, or Advanced using shooting accuracy, survival time, and
   lives lost. It also reports prediction confidence.
2. K-Means Clustering (unsupervised learning): independently groups similar
   player profiles into three clusters.
3. Adaptive system: Random Forest prediction changes alien speed.

DATA
The model's starter training profiles are simulated and reproducible. This
allows the project to work on its first run. Each completed game session is
saved in gameplay_data.csv. These real sessions can be analysed and used as
a basis for future retraining after enough labelled examples are collected.
Do not describe the starter data as real player history.

FEATURES
- shooting_accuracy: shots hit / shots fired
- survival_seconds: time survived in the session
- lives_lost: number of player lives lost
- score and level are also stored for analysis

INSTALLATION
Open a terminal in the folder containing alien_invasion.py and run:
python -m pip install -r requirements.txt

RUN THE GAME
python alien_invasion.py

VIEW THE GAMEPLAY ANALYTICS
Complete at least one game session so gameplay_data.csv is created, then run:
python ml_dashboard.py

CONTROLS
Arrow keys: move ship
Space: shoot
Mouse: click PLAY

IMPORTANT LIMITATION
This is an ML-integrated game, not a game whose every component is AI. The
interface, movement, collision detection, and rendering use normal Python
and Pygame. The player classification and adaptive difficulty are the
Machine Learning parts. Starter model training data is simulated; completed
player sessions are saved separately as real gameplay observations.
