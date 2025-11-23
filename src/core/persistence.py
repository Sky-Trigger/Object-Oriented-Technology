# 游戏存档持久化模块，负责JSON格式的保存和加载
import json
import os


def save_game(file_path, payload):
    # 保存游戏数据到JSON文件
    directory = os.path.dirname(file_path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
    try:
        with open(file_path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
    except OSError as error:
        raise ValueError(f"Failed to save file: {error}")


def load_game(file_path):
    # 从JSON文件加载游戏数据
    if not os.path.exists(file_path):
        raise ValueError("Save file does not exist")
    try:
        with open(file_path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"Failed to load save file: {error}")
