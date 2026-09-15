import requests
import zipfile
import io
from datetime import datetime
import os
import time

date = datetime.today()
month_upper = date.strftime("%b").upper()

url = f"https://www.nseindia.com/content/historical/EQUITIES/{date:%Y}/{month_upper}/cm{date:%d}{month_upper}{date:%Y}bhav.csv.zip"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1"
}

def check_connectivity():
    try:
        requests.get("https://www.google.com", timeout=5)
        return True
    except requests.exceptions.RequestException:
        return False

if not check_connectivity():
    print("No internet connection detected. Please check your network.")
    exit(1)

session = requests.Session()

for attempt in range(3):
    try:
        print(f"Attempt {attempt + 1}: Initializing session...")
        session.get("https://www.nseindia.com", headers=headers, timeout=15)
        time.sleep(2)
        
        print("Downloading bhavcopy...")
        res = session.get(url, headers=headers, timeout=60)
        res.raise_for_status()
        
        if len(res.content) < 1000:
            print("Response too small, likely an error page:")
            print(res.content.decode('utf-8', errors='ignore')[:500])
            if attempt < 2:
                print("Retrying...")
                time.sleep(3)
                continue
            else:
                print("Failed: Server returned error page instead of zip file")
                break
        
        os.makedirs("data", exist_ok=True)
        z = zipfile.ZipFile(io.BytesIO(res.content))
        z.extractall("data")
        print("Downloaded successfully: " + url)
        break
    except requests.exceptions.Timeout:
        print(f"Timeout on attempt {attempt + 1}")
        if attempt < 2:
            print("Retrying...")
            time.sleep(3)
        else:
            print("Failed after 3 attempts due to timeout")
            print("URL attempted: " + url)
    except requests.exceptions.RequestException as e:
        print("Failed to download: " + str(e))
        print("URL attempted: " + url)
        break
    except zipfile.BadZipFile:
        print("Downloaded file is not a valid zip file")
        print("Response status: " + str(res.status_code))
        break