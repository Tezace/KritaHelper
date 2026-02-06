import psutil
import time
import os
import json
import random
import colorsys
import rgbprint
from datetime import datetime

KRITA_PROCESS_NAME = "krita.exe"
DATA_DIR = os.path.dirname(os.path.abspath(__file__))
TIME_FILE_PATH = os.path.join(DATA_DIR, "krita_time.json")
LOG_FILE_PATH = os.path.join(DATA_DIR, "krita_log.json")

def ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)

def format_time(seconds: int) -> str: # formats time like "1222:32:02"
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def clear_console():
    os.system("cls" if os.name == "nt" else "clear") # well, because if the user uses windows, it's cls for some reason

class KritaTimeTracker:
    def __init__(self, process_name: str, time_file: str, log_file: str):
        self.process_name = process_name
        self.time_file = time_file
        self.log_file = log_file

        self.total_seconds = 0
        self.is_running = False
        self.start_time = None

        self.daily_log = {}
        self.load_time()
        self.load_log()

    def load_time(self):
        if os.path.exists(self.time_file):
            try:
                with open(self.time_file, "r") as f:
                    data = json.load(f)
                    self.total_seconds = data.get("total_seconds", 0)
            except (json.JSONDecodeError, IOError):
                self.total_seconds = 0

    def save_time(self):
        try:
            with open(self.time_file, "w") as f:
                json.dump({"total_seconds": self.total_seconds}, f, indent=2)
        except IOError:
            print("Could not save total time file")

    def load_log(self):
        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, "r") as f:
                    self.daily_log = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.daily_log = {}
        else:
            self.daily_log = {}

    def save_log(self):
        try:
            with open(self.log_file, "w") as f:
                json.dump(self.daily_log, f, indent=2)
        except IOError:
            print("Could not save log file")

    def is_krita_running(self) -> bool: # iterates through processes to check if kritas running
        for proc in psutil.process_iter(attrs=['name']):
            try:
                if proc.info['name'].lower() == self.process_name.lower():
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return False

    def update_daily_log(self):
        today = datetime.now().strftime("%Y-%m-%d")
        self.daily_log[today] = int(self.daily_log.get(today, 0) + 1)
        self.save_log()

    def get_today_seconds(self) -> int:
        today = datetime.now().strftime("%Y-%m-%d")
        return int(self.daily_log.get(today, 0))

    def track(self): 
        print("Starting Krita time tracking. Press Ctrl+C to stop.\n")

        try:
            while True:
                now = time.time()
                running = self.is_krita_running()

                if running and not self.is_running:
                    self.is_running = True
                    self.start_time = now - self.total_seconds # detects when you start krita
                    print("Krita detected, tracking started.")

                elif not running and self.is_running:
                    self.is_running = False
                    self.total_seconds = now - self.start_time # pauses hwen you close krita
                    print("Krita closed, tracking paused.")

                if self.is_running:
                    self.total_seconds = now - self.start_time
                    self.update_daily_log()

                clear_console()
                today_seconds = self.get_today_seconds()
                print(f"Total time in Krita: {format_time(int(self.total_seconds))}")
                print(f"Today's session: {format_time(today_seconds)}")
                if not self.is_running:
                    print("Waiting for Krita to start...")

                self.save_time()
                time.sleep(1)

        except KeyboardInterrupt:
            print("\nSaving and exiting...")
            self.save_time()
            self.save_log()
        except Exception as e:
            print(f"\nError: {e}")
            self.save_time()
            self.save_log()

class ColorPaletteGenerator:
    def __init__(self, count: int = 5):
        self.count = count

    @staticmethod
    def random_palette(n=5, hue_range=(0.0, 1.0), sat_range=(0.4, 0.8), light_range=(0.3, 0.7)): # uses ai, no not generative ai y'all hate, the other ai, to cook up a color palette
        colors = []
        for _ in range(n):
            h = random.uniform(*hue_range)
            s = random.uniform(*sat_range)
            l = random.uniform(*light_range)
            r, g, b = colorsys.hls_to_rgb(h, l, s)
            colors.append((r, g, b))
        return colors

    @staticmethod
    def rgb_to_hex(rgb): # converts rgb to hex for it to be compatible w/ rgbprint
        return "#{:02x}{:02x}{:02x}".format(
            int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255)
        )

    def display_palette(self):
        clear_console()
        palette = self.random_palette(self.count)
        hex_palette = [self.rgb_to_hex(c) for c in palette]

        print("\nHere's the color palette:")
        for rgb, hex_code in zip(palette, hex_palette):
            r, g, b = [int(x * 255) for x in rgb]
            rgbprint.rgbprint(f"{hex_code}", color=(r, g, b))
        while True:
            time.sleep(15)

class Statistics:
    def __init__(self, time_file: str, log_file: str):
        self.time_file = time_file
        self.log_file = log_file

        self.average = 0
        self.total_seconds = 0
        self.most_in_1_day = 0
        self.daily_log = {}

        self.load_log()
        self.load_time()

    def load_time(self): # basically loads the time file
        if os.path.exists(self.time_file):
            try:
                with open(self.time_file, "r") as f:
                    data = json.load(f)
                    self.total_seconds = data.get("total_seconds", 0)
                    self.total_seconds = int(self.total_seconds)
            except (json.JSONDecodeError, IOError):
                self.total_seconds = 0
    
    def load_log(self): # basically loads up the log file and finds the average
        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, "r") as f:
                    self.daily_log = json.load(f)
                    vals = list(self.daily_log.values())
                    length = len(vals)
                    total = 0
                    for i in vals:
                        total += i
                    self.average = total/length if length != 0 else 0 # handles division by zero
                    self.average = int(self.average)
                    self.most_in_1_day = max(vals) if length != 0 else 0 # also handles zero
            except (json.JSONDecodeError, IOError):
                self.daily_log = {}
        else:
            self.daily_log = {}
    
    def display_stats(self):
        while True:
            clear_console()
            self.load_log()
            self.load_time()
            if self.average <= 150:
                rgbprint.rgbprint(f"The average time spent per day: {format_time(self.average)} (Bronze I)", color="brown")
            elif self.average <= 225:
                rgbprint.rgbprint(f"The average time spent per day: {format_time(self.average)} (Bronze II)", color="brown")
            elif self.average <= 300:
                rgbprint.rgbprint(f"The average time spent per day: {format_time(self.average)} (Bronze III)", color="brown")
            elif self.average <= 450:
                rgbprint.gradient_print(f"The average time spent per day: {format_time(self.average)} (Silver I)", start_color="gray", end_color="white")
            elif self.average <= 600:
                rgbprint.gradient_print(f"The average time spent per day: {format_time(self.average)} (Silver II)", start_color="gray", end_color="white")
            elif self.average <= 800:
                rgbprint.gradient_print(f"The average time spent per day: {format_time(self.average)} (Silver III)", start_color="gray", end_color="white")
            elif self.average <= 1000:
                rgbprint.gradient_print(f"The average time spent per day: {format_time(self.average)} (Gold I)", start_color="yellow", end_color="white")
            elif self.average <= 1300:
                rgbprint.gradient_print(f"The average time spent per day: {format_time(self.average)} (Gold II)", start_color="yellow", end_color="white")
            elif self.average <= 1600:
                rgbprint.gradient_print(f"The average time spent per day: {format_time(self.average)} (Gold III)", start_color="yellow", end_color="white")
            elif self.average <= 2000:
                rgbprint.gradient_print(f"The average time spent per day: {format_time(self.average)} (Diamond I)", start_color="cyan", end_color="white")
            elif self.average <= 2800:
                rgbprint.gradient_print(f"The average time spent per day: {format_time(self.average)} (Diamond II)", start_color="cyan", end_color="white")
            elif self.average <= 3600:
                rgbprint.gradient_print(f"The average time spent per day: {format_time(self.average)} (Diamond III)", start_color="cyan", end_color="white")
            elif self.average <= 4800:
                rgbprint.gradient_print(f"The average time spent per day: {format_time(self.average)} (Azure I)", start_color="blue", end_color="white")
            elif self.average <= 6000:
                rgbprint.gradient_print(f"The average time spent per day: {format_time(self.average)} (Azure II)", start_color="blue", end_color="white")
            elif self.average <= 7200:
                rgbprint.gradient_print(f"The average time spent per day: {format_time(self.average)} (Azure III)", start_color="blue", end_color="white")
            elif self.average <= 9000:
                rgbprint.gradient_print(f"The average time spent per day: ", start_color=(255, 0, 0), end_color=(255, 255, 0), end="")
                rgbprint.gradient_print(f"{format_time(self.average)}", start_color=(255, 255, 0), end_color=(0, 255, 255), end="")
                rgbprint.gradient_print(f" (Prismatic I)", start_color=(0, 255, 255), end_color=(255, 0, 255))
            elif self.average <= 10800:
                rgbprint.gradient_print(f"The average time spent per day: ", start_color=(255, 75, 75), end_color=(255, 255, 75), end="")
                rgbprint.gradient_print(f"{format_time(self.average)}", start_color=(255, 255, 75), end_color=(75, 255, 255), end="")
                rgbprint.gradient_print(f" (Prismatic II)", start_color=(75, 255, 255), end_color=(255, 75, 255))
            elif self.average <= 13200:
                rgbprint.gradient_print(f"The average time spent per day: ", start_color=(255, 150, 150), end_color=(255, 255, 150), end="")
                rgbprint.gradient_print(f"{format_time(self.average)}", start_color=(255, 255, 150), end_color=(150, 255, 255), end="")
                rgbprint.gradient_print(f" (Prismatic III)", start_color=(150, 255, 255), end_color=(255, 150, 255))
            elif self.average <= 15600:
                rgbprint.gradient_print(f"The average time spent per day: {format_time(self.average)} (Astral I)", start_color=(100, 0, 255), end_color=(255, 0, 255))
            elif self.average <= 18000:
                rgbprint.gradient_print(f"The average time spent per day: {format_time(self.average)} (Astral II)", start_color=(175, 75, 255), end_color=(255, 75, 255))
            elif self.average <= 20400:
                rgbprint.gradient_print(f"The average time spent per day: {format_time(self.average)} (Astral III)", start_color=(250, 150, 255), end_color=(255, 150, 255))
            else:
                rgbprint.gradient_print(f"The average time spent per day: {format_time(self.average)} (Archon)", start_color="red", end_color="white") # oh boy that was a long one
            
            # basically the same but for total seconds
            if self.total_seconds <= 10000:
                rgbprint.rgbprint(f"Total time spent on Krita: {format_time(self.total_seconds)} (Bronze I)", color="brown")
            elif self.total_seconds <= 20000:
                rgbprint.rgbprint(f"Total time spent on Krita: {format_time(self.total_seconds)} (Bronze II)", color="brown")
            elif self.total_seconds <= 30000:
                rgbprint.rgbprint(f"Total time spent on Krita: {format_time(self.total_seconds)} (Bronze III)", color="brown")
            elif self.total_seconds <= 50000:
                rgbprint.gradient_print(f"Total time spent on Krita: {format_time(self.total_seconds)} (Silver I)", start_color="gray", end_color="white")
            elif self.total_seconds <= 75000:
                rgbprint.gradient_print(f"Total time spent on Krita: {format_time(self.total_seconds)} (Silver II)", start_color="gray", end_color="white")
            elif self.total_seconds <= 100000:
                rgbprint.gradient_print(f"Total time spent on Krita: {format_time(self.total_seconds)} (Silver III)", start_color="gray", end_color="white")
            elif self.total_seconds <= 130000:
                rgbprint.gradient_print(f"Total time spent on Krita: {format_time(self.total_seconds)} (Gold I)", start_color="yellow", end_color="white")
            elif self.total_seconds <= 170000:
                rgbprint.gradient_print(f"Total time spent on Krita: {format_time(self.total_seconds)} (Gold II)", start_color="yellow", end_color="white")
            elif self.total_seconds <= 200000:
                rgbprint.gradient_print(f"Total time spent on Krita: {format_time(self.total_seconds)} (Gold III)", start_color="yellow", end_color="white")
            elif self.total_seconds <= 275000:
                rgbprint.gradient_print(f"Total time spent on Krita: {format_time(self.total_seconds)} (Diamond I)", start_color="cyan", end_color="white")
            elif self.total_seconds <= 350000:
                rgbprint.gradient_print(f"Total time spent on Krita: {format_time(self.total_seconds)} (Diamond II)", start_color="cyan", end_color="white")
            elif self.total_seconds <= 410000:
                rgbprint.gradient_print(f"Total time spent on Krita: {format_time(self.total_seconds)} (Diamond III)", start_color="cyan", end_color="white")
            elif self.total_seconds <= 500000:
                rgbprint.gradient_print(f"Total time spent on Krita: {format_time(self.total_seconds)} (Azure I)", start_color="blue", end_color="white")
            elif self.total_seconds <= 710000:
                rgbprint.gradient_print(f"Total time spent on Krita: {format_time(self.total_seconds)} (Azure II)", start_color="blue", end_color="white")
            elif self.total_seconds <= 980000:
                rgbprint.gradient_print(f"Total time spent on Krita: {format_time(self.total_seconds)} (Azure III)", start_color="blue", end_color="white")
            elif self.total_seconds <= 1200000:
                rgbprint.gradient_print(f"Total time spent on Krita: ", start_color=(255, 0, 0), end_color=(255, 255, 0), end="")
                rgbprint.gradient_print(f"{format_time(self.total_seconds)}", start_color=(255, 255, 0), end_color=(0, 255, 255), end="")
                rgbprint.gradient_print(f" (Prismatic I)", start_color=(0, 255, 255), end_color=(255, 0, 255))
            elif self.total_seconds <= 1500000:
                rgbprint.gradient_print(f"Total time spent on Krita: ", start_color=(255, 75, 75), end_color=(255, 255, 75), end="")
                rgbprint.gradient_print(f"{format_time(self.total_seconds)}", start_color=(255, 255, 75), end_color=(75, 255, 255), end="")
                rgbprint.gradient_print(f" (Prismatic II)", start_color=(75, 255, 255), end_color=(255, 75, 255))
            elif self.total_seconds <= 1900000:
                rgbprint.gradient_print(f"Total time spent on Krita: ", start_color=(255, 150, 150), end_color=(255, 255, 150), end="")
                rgbprint.gradient_print(f"{format_time(self.total_seconds)}", start_color=(255, 255, 150), end_color=(150, 255, 255), end="")
                rgbprint.gradient_print(f" (Prismatic III)", start_color=(150, 255, 255), end_color=(255, 150, 255))
            elif self.total_seconds <= 2500000:
                rgbprint.gradient_print(f"Total time spent on Krita: {format_time(self.total_seconds)} (Astral I)", start_color=(100, 0, 255), end_color=(255, 0, 255))
            elif self.total_seconds <= 3750000:
                rgbprint.gradient_print(f"Total time spent on Krita: {format_time(self.total_seconds)} (Astral II)", start_color=(175, 75, 255), end_color=(255, 75, 255))
            elif self.total_seconds <= 5000000:
                rgbprint.gradient_print(f"Total time spent on Krita: {format_time(self.total_seconds)} (Astral III)", start_color=(250, 150, 255), end_color=(255, 150, 255))
            else:
                rgbprint.gradient_print(f"Total time spent on Krita: {format_time(self.total_seconds)} (Archon)", start_color="red", end_color="white")
            
            if self.most_in_1_day <= 300:
                rgbprint.rgbprint(f"Most amount of time spent in 1 day: {format_time(self.most_in_1_day)} (Bronze I)", color="brown")
            elif self.most_in_1_day <= 450:
                rgbprint.rgbprint(f"Most amount of time spent in 1 day: {format_time(self.most_in_1_day)} (Bronze II)", color="brown")
            elif self.most_in_1_day <= 600:
                rgbprint.rgbprint(f"Most amount of time spent in 1 day: {format_time(self.most_in_1_day)} (Bronze III)", color="brown")
            elif self.most_in_1_day <= 900:
                rgbprint.gradient_print(f"Most amount of time spent in 1 day: {format_time(self.most_in_1_day)} (Silver I)", start_color="gray", end_color="white")
            elif self.most_in_1_day <= 1200:
                rgbprint.gradient_print(f"Most amount of time spent in 1 day: {format_time(self.most_in_1_day)} (Silver II)", start_color="gray", end_color="white")
            elif self.most_in_1_day <= 1600:
                rgbprint.gradient_print(f"Most amount of time spent in 1 day: {format_time(self.most_in_1_day)} (Silver III)", start_color="gray", end_color="white")
            elif self.most_in_1_day <= 2000:
                rgbprint.gradient_print(f"Most amount of time spent in 1 day: {format_time(self.most_in_1_day)} (Gold I)", start_color="yellow", end_color="white")
            elif self.most_in_1_day <= 2600:
                rgbprint.gradient_print(f"Most amount of time spent in 1 day: {format_time(self.most_in_1_day)} (Gold II)", start_color="yellow", end_color="white")
            elif self.most_in_1_day <= 3200:
                rgbprint.gradient_print(f"Most amount of time spent in 1 day: {format_time(self.most_in_1_day)} (Gold III)", start_color="yellow", end_color="white")
            elif self.most_in_1_day <= 4000:
                rgbprint.gradient_print(f"Most amount of time spent in 1 day: {format_time(self.most_in_1_day)} (Diamond I)", start_color="cyan", end_color="white")
            elif self.most_in_1_day <= 5600:
                rgbprint.gradient_print(f"Most amount of time spent in 1 day: {format_time(self.most_in_1_day)} (Diamond II)", start_color="cyan", end_color="white")
            elif self.most_in_1_day <= 7200:
                rgbprint.gradient_print(f"Most amount of time spent in 1 day: {format_time(self.most_in_1_day)} (Diamond III)", start_color="cyan", end_color="white")
            elif self.most_in_1_day <= 9600:
                rgbprint.gradient_print(f"Most amount of time spent in 1 day: {format_time(self.most_in_1_day)} (Azure I)", start_color="blue", end_color="white")
            elif self.most_in_1_day <= 12000:
                rgbprint.gradient_print(f"Most amount of time spent in 1 day: {format_time(self.most_in_1_day)} (Azure II)", start_color="blue", end_color="white")
            elif self.most_in_1_day <= 14400:
                rgbprint.gradient_print(f"Most amount of time spent in 1 day: {format_time(self.most_in_1_day)} (Azure III)", start_color="blue", end_color="white")
            elif self.most_in_1_day <= 18000:
                rgbprint.gradient_print(f"Most amount of time spent in 1 day: ", start_color=(255, 0, 0), end_color=(255, 255, 0), end="")
                rgbprint.gradient_print(f"{format_time(self.most_in_1_day)}", start_color=(255, 255, 0), end_color=(0, 255, 255), end="")
                rgbprint.gradient_print(f" (Prismatic I)", start_color=(0, 255, 255), end_color=(255, 0, 255))
            elif self.most_in_1_day <= 21600:
                rgbprint.gradient_print(f"Most amount of time spent in 1 day: ", start_color=(255, 75, 75), end_color=(255, 255, 75), end="")
                rgbprint.gradient_print(f"{format_time(self.most_in_1_day)}", start_color=(255, 255, 75), end_color=(75, 255, 255), end="")
                rgbprint.gradient_print(f" (Prismatic II)", start_color=(75, 255, 255), end_color=(255, 75, 255))
            elif self.most_in_1_day <= 26400:
                rgbprint.gradient_print(f"Most amount of time spent in 1 day: ", start_color=(255, 150, 150), end_color=(255, 255, 150), end="")
                rgbprint.gradient_print(f"{format_time(self.most_in_1_day)}", start_color=(255, 255, 150), end_color=(150, 255, 255), end="")
                rgbprint.gradient_print(f" (Prismatic III)", start_color=(150, 255, 255), end_color=(255, 150, 255))
            elif self.most_in_1_day <= 31200:
                rgbprint.gradient_print(f"Most amount of time spent in 1 day: {format_time(self.most_in_1_day)} (Astral I)", start_color=(100, 0, 255), end_color=(255, 0, 255))
            elif self.most_in_1_day <= 36000:
                rgbprint.gradient_print(f"Most amount of time spent in 1 day: {format_time(self.most_in_1_day)} (Astral II)", start_color=(175, 75, 255), end_color=(255, 75, 255))
            elif self.most_in_1_day <= 40800:
                rgbprint.gradient_print(f"Most amount of time spent in 1 day: {format_time(self.most_in_1_day)} (Astral III)", start_color=(250, 150, 255), end_color=(255, 150, 255))
            else:
                rgbprint.gradient_print(f"Most amount of time spent in 1 day: {format_time(self.most_in_1_day)} (Archon)", start_color="red", end_color="white")
            
            # basically keeps it running forever unless you purposely close it
            time.sleep(1)
        



def main():
    ensure_data_dir()

    rgbprint.gradient_print("KritaHelper v0.9 | made by Tezace", start_color="cyan", end_color="light_green")
    rgbprint.gradient_print("1 - Krita Time Tracker", start_color="light_green", end_color="yellow")
    rgbprint.gradient_print("2 - Random Color Palette Generator", start_color="magenta", end_color="red")
    rgbprint.gradient_print("3 - Stats + Analytics (basically required to run both this and 1)", start_color="red", end_color="yellow")
    print("More coming soon!")
    print("Pro tip: you can run multiple instances of this at the same time, so you can both get a random color palette AND track your time\n")

    try:
        choice = int(input("Input your choice (1, 2 or 3): "))
    except ValueError:
        print("Invalid input, please enter a number.")
        return

    if choice == 1:
        tracker = KritaTimeTracker(KRITA_PROCESS_NAME, TIME_FILE_PATH, LOG_FILE_PATH)
        tracker.track()
    elif choice == 2:
        palette = ColorPaletteGenerator()
        palette.display_palette()
    elif choice == 3:
        stats = Statistics(TIME_FILE_PATH, LOG_FILE_PATH)
        stats.display_stats()
    else:
        print("Invalid choice, please select 1 or 2.")


if __name__ == "__main__":
    main()
