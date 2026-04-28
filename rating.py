import json
import os
from config import ACHIEVEMENTS

RATING_FILE = "data/rating.json"

def load_rating() -> dict:
    if not os.path.exists("data"):
        os.makedirs("data")
    if os.path.exists(RATING_FILE):
        with open(RATING_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_rating(data: dict):
    with open(RATING_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_all_players() -> dict:
    return load_rating()

def update_player_stats(user_id: int, name: str, result: dict):
    """
    result может содержать:
    - game_type: "local"/"online"/"training"
    - won: True/False/None (если тренировка – None)
    - total_pushups: int
    - rounds: int
    - pushups_this_game: int (для ачивки "сотня")
    """
    data = load_rating()
    uid = str(user_id)
    if uid not in data:
        data[uid] = {
            "name": name,
            "games": 0,
            "wins": 0,
            "losses": 0,
            "total_pushups": 0,
            "max_pushups_one_game": 0,
            "trainings": 0,
            "training_pushups": 0,
            "achievements": [],
        }
    p = data[uid]
    p["name"] = name  # обновляем имя
    if result.get("game_type") == "training":
        p["trainings"] += 1
        p["training_pushups"] += result.get("total_pushups", 0)
        p["total_pushups"] += result.get("total_pushups", 0)
    else:
        p["games"] += 1
        p["total_pushups"] += result.get("total_pushups", 0)
        if result.get("won"):
            p["wins"] += 1
        elif result.get("won") is False:
            p["losses"] += 1
        if result.get("total_pushups", 0) > p["max_pushups_one_game"]:
            p["max_pushups_one_game"] = result["total_pushups"]

    # проверка ачивок
    new_ach = check_achievements(p)
    for ach in new_ach:
        if ach not in p["achievements"]:
            p["achievements"].append(ach)
    save_rating(data)
    return new_ach

def check_achievements(stats: dict) -> list:
    earned = []
    if stats["games"] + stats["trainings"] >= 1 and "first_game" not in stats["achievements"]:
        earned.append("first_game")
    if stats["wins"] >= 1 and "first_win" not in stats["achievements"]:
        earned.append("first_win")
    if stats["wins"] >= 5 and "five_wins" not in stats["achievements"]:
        earned.append("five_wins")
    if stats["max_pushups_one_game"] >= 100 and "hundred_pushups" not in stats["achievements"]:
        earned.append("hundred_pushups")
    # ten_rounds можно передавать через result, но для простоты пропустим
    return earned

def get_top(n=10) -> list:
    data = load_rating()
    players = []
    for uid, p in data.items():
        score = p["wins"] * 3 + (p["total_pushups"] // 10)
        players.append((int(uid), p["name"], score, p["wins"], p["games"], p["total_pushups"]))
    players.sort(key=lambda x: x[2], reverse=True)
    return players[:n]

def get_user_stats(user_id: int) -> dict:
    data = load_rating()
    return data.get(str(user_id))
