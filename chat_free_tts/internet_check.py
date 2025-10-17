import requests
import threading
import time

internet_status = True

def check_internet():
    global internet_status
    while True:
        try:
            requests.get("https://www.google.com", timeout=5)
            internet_status = True
        except:
            internet_status = False
        time.sleep(5)

threading.Thread(target=check_internet, daemon=True).start()
