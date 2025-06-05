import os
from typing import Any, Dict, Optional
import requests
from requests import Response
import base64
from hashlib import sha224

from configs import configs


def check_server_connection() -> bool:
    server_url = f"http://{configs.server_ip}:{configs.server_port}"
    try:
        response = requests.get(f"{server_url}/ollama_list_models")
        if response.status_code == 200:
            return True
        return False
    except ConnectionError:
        return False


def send_to_server(data: Optional[Dict[str, Any]], endpoint) -> Response:
    server_url = f"http://{configs.server_ip}:{configs.server_port}"
    if data:
        uid = sha224(configs.username.encode("utf-8")).hexdigest()
        payload = {"uid": uid, **data}
        response = requests.post(f"{server_url}/{endpoint}", json=payload)
    else:
        response = requests.get(f"{server_url}/{endpoint}")
    return response.json()


def convert_and_save(b64_img: str, fname: str, dirname: str) -> str:
    full_name = os.path.join(dirname, fname)
    with open(full_name, "wb") as f:
        f.write(base64.b64decode(b64_img))
    return os.path.basename(full_name)
