import datetime
import subprocess

def get_ny_time():
    # Get current time in New York timezone
    import pytz
    ny_tz = pytz.timezone("America/New_York")
    return datetime.datetime.now(ny_tz)

if __name__ == '__main__':
    now = get_ny_time()
    hour = now.hour
    minute = now.minute

    print(f"[INFO] Current NY time: {hour}:{minute:02}")

    # Example logic: before 9:00 AM = close_market, after 9:30 AM = open_market
    if hour < 9 or (hour == 9 and minute < 15):
        print("[INFO] Running close_market.py")
        subprocess.run(["python3", "closed_market.py"])
    elif hour == 9 and minute >= 30 or hour >= 10:
        print("[INFO] Running open_market.py")
        subprocess.run(["python3", "open_market.py"])
    else:
        print("[INFO] Not a valid window. Skipping.")
