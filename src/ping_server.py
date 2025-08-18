import os
import time
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

SERVER_URL = os.getenv("SERVER_URL")

def send_ping():
    if not SERVER_URL:
        print("SERVER_URL environment variable not set. Cannot send ping.")
        return

    ping_url = f"{SERVER_URL}/api/ping"
    try:
        response = requests.post(ping_url)
        response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
        print(f"[{time.ctime()}] Ping successful: {response.json().get('message')}")
    except requests.exceptions.RequestException as e:
        print(f"[{time.ctime()}] Ping failed: {e}")

if __name__ == "__main__":
    print("Starting continuous ping to server...")
    while True:
        send_ping()
        time.sleep(60)  # Ping every 60 seconds (1 minute)
