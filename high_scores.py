import os
import constants as C # Use absolute import

def load_high_scores(filepath=C.HIGH_SCORE_FILE):
    """ Loads high scores from a file. Creates the file with defaults if it doesn't exist. """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    high_scores = [C.DEFAULT_HIGH_SCORE_ENTRY] * C.NUM_HIGH_SCORES
    try:
        with open(filepath, 'r') as f:
            lines = f.readlines()
            loaded_scores = []
            for line in lines:
                try:
                    name, score_str = line.strip().split(',')
                    score = int(score_str)
                    loaded_scores.append((name, score))
                except ValueError:
                    continue  # Skip malformed lines
            loaded_scores.sort(key=lambda item: item[1], reverse=True)
            for i in range(min(len(loaded_scores), C.NUM_HIGH_SCORES)):
                high_scores[i] = loaded_scores[i]
    except FileNotFoundError:
        save_high_scores(filepath, high_scores) # Save defaults if file not found
    except Exception as e:
        print(f"Error loading high scores: {e}. Using defaults.")
        high_scores = [C.DEFAULT_HIGH_SCORE_ENTRY] * C.NUM_HIGH_SCORES
        save_high_scores(filepath, high_scores) # Attempt to save defaults on other errors

    return high_scores

def save_high_scores(filepath, high_scores):
    """ Saves the high scores list to a file. """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    try:
        with open(filepath, 'w') as f:
            for name, score in high_scores:
                f.write(f"{name},{score}\n")
    except Exception as e:
        print(f"Error saving high scores: {e}")
