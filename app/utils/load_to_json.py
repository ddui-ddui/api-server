
import json
import os
from typing import Dict


def load_json_data(filename: str, *path_parts) -> Dict:
    try:
        file_path = os.path.join(*path_parts, filename)
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")