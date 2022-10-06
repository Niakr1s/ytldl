import json
import os


def writeJson(obj: any, filepath: str):
    dir = os.path.dirname(filepath)
    os.makedirs(dir, exist_ok=True)
    with open(filepath, mode="w", encoding="utf-8") as f:
        json.dump(obj, fp=f, indent="    ")
