import time

import requests

BASE = "http://localhost:7777"


def get_mode():
    r = requests.get(f"{BASE}/mode")
    print("GET /mode →", r.status_code)
    try:
        print(r.json())
    except ValueError:
        print("Non-JSON response:", r.text)


def set_mode(mode):
    r = requests.post(f"{BASE}/mode", json={"mode": mode})
    print(f"POST /mode {{mode:{mode}}} →", r.status_code)
    try:
        print(r.json())
    except ValueError:
        print("Non-JSON response:", r.text)


def chat(message, manual_mode=None):
    payload = {"message": message}
    if manual_mode:
        payload["manual_mode"] = manual_mode
    r = requests.post(f"{BASE}/chat", json=payload)
    print("POST /chat", payload, "→", r.status_code)
    try:
        print(r.json())
    except ValueError:
        print("Non-JSON response:", r.text)


if __name__ == "__main__":
    print("\n⏱  waiting 1s for server to settle…\n")
    time.sleep(1)
    get_mode()
    chat("hey kor'tana, how are you today?")
    print()
    set_mode("intimate")
    chat("i’m feeling a bit overwhelmed", manual_mode="intimate")
    print()
    get_mode()
