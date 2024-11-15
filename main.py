import argparse
import itertools
import os
import string
import threading
import time
import tkinter as tk
from concurrent.futures import ThreadPoolExecutor, as_completed
from tkinter import ttk
import urllib.request

from bs4 import BeautifulSoup

API = "https://www.urbandictionary.com/browse.php?character={0}"

MAX_ATTEMPTS = 10
DELAY = 10

NUMBER_SIGN = "*"


# https://stackoverflow.com/a/554580/306149
class NoRedirection(urllib.request.HTTPErrorProcessor):
    def http_response(self, request, response):
        return response

    https_response = http_response


def extract_page_entries(html):
    soup = BeautifulSoup(html, "html.parser")
    # find word list element, this might change in the future
    ul = soup.find_all("ul", class_="mt-3 columns-2 md:columns-3")[0]
    for li in ul.find_all("li"):
        a = li.find("a").string
        if a:
            yield a


def get_next(html):
    soup = BeautifulSoup(html, "html.parser")
    next_link = soup.find("a", {"rel": "next"})
    if next_link:
        href = next_link["href"]
        return "https://www.urbandictionary.com" + href
    return None


def extract_letter_entries(letter, progress_callback):
    url = API.format(letter)
    attempt = 0
    while url:
        progress_callback(letter, url)  # Update UI with current URL
        response = urllib.request.urlopen(url)
        code = response.getcode()
        if code == 200:
            content = response.read()
            yield list(extract_page_entries(content))
            url = get_next(content)
            attempt = 0
        else:
            print(
                f"[{letter}] Trying again, expected response code: 200, got {code}"
            )
            attempt += 1
            if attempt > MAX_ATTEMPTS:
                break
            time.sleep(DELAY * attempt)


opener = urllib.request.build_opener(
    NoRedirection, urllib.request.HTTPCookieProcessor()
)
urllib.request.install_opener(opener)


letters = list(string.ascii_uppercase) + ["#"]


def download_letter_entries(letter, file, remove_dead, progress_callback):
    start_time = time.time()
    file = file.format(letter)
    entries = itertools.chain.from_iterable(
        list(extract_letter_entries(letter, progress_callback))
    )

    if remove_dead:
        all_data = entries
    else:
        try:
            with open(file, "r", encoding="utf-8") as f:
                old_data = [line.strip() for line in f.readlines()]
            all_data = sorted(set(old_data).union(set(entries)), key=str.casefold)
        except FileNotFoundError:
            all_data = entries

    with open(file, "w", encoding="utf-8") as f:
        f.write("\n".join(all_data) + "\n")

    end_time = time.time()
    progress_callback(letter, "Done")  # Update UI with "Done" status
    print(f"[{letter}] Finished in {end_time - start_time:.2f} seconds")


def download_entries(letters, file, remove_dead, max_workers, progress_callback):
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(
                download_letter_entries,
                letter,
                file,
                remove_dead,
                progress_callback,
            )
            for letter in letters
        ]
        for future in as_completed(futures):
            pass  # Detailed output is handled in download_letter_entries


class App(tk.Tk):
    def __init__(self, letters, file, remove_dead, max_workers):
        super().__init__()
        self.title("Urban Dictionary Scraper")
        self.geometry("500x650")  # Adjust window size as needed

        self.letters = letters
        self.file = file
        self.remove_dead = remove_dead
        self.max_workers = max_workers

        self.create_ui()

    def create_ui(self):
        # Create a frame for the progress bars
        progress_frame = ttk.Frame(self)
        progress_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # Create progress bars for each letter
        self.progress_vars = {}
        self.progress_labels = {}
        for i, letter in enumerate(self.letters):
            self.progress_vars[letter] = tk.StringVar(value="Pending")
            self.progress_labels[letter] = ttk.Label(
                progress_frame, textvariable=self.progress_vars[letter]
            )
            self.progress_labels[letter].grid(row=i, column=0, sticky=tk.W)

        # Create a button to start the scraping process
        start_button = ttk.Button(self, text="Start", command=self.start_scraping)
        start_button.pack(pady=10)

    def start_scraping(self):
        # Disable the start button
        start_button = ttk.Button(self, text="Start", command=self.start_scraping)
        start_button.pack(pady=10)
        start_button.config(state=tk.DISABLED)

        # Start the scraping process in a separate thread
        threading.Thread(
            target=download_entries,
            args=(
                self.letters,
                self.file,
                self.remove_dead,
                self.max_workers,
                self.update_progress,
            ),
        ).start()

    def update_progress(self, letter, message):
        # Update the progress bar for the given letter
        self.progress_vars[letter].set(message)
        self.update_idletasks()  # Update the UI immediately


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download urban dictionary words.")

    parser.add_argument(
        "letters", metavar="L", type=str, nargs="*", help="Letters to download."
    )

    parser.add_argument(
        "--ifile",
        dest="ifile",
        help="input file name. Contains a list of letters separated by a newline",
        default="input.list",
    )

    parser.add_argument(
        "--out",
        dest="out",
        help="output file name. May be a format string",
        default="data/{0}.data",
    )

    parser.add_argument(
        "--remove-dead",
        action="store_true",
        help="Removes entries that no longer exist.",
    )

    parser.add_argument(
        "--max-workers",
        type=int,
        default=20,
        help="Maximum number of threads to use for downloading",
    )

    args = parser.parse_args()

    letters = [letter.upper() for letter in args.letters]
    if not letters:
        with open(args.ifile, "r") as ifile:
            for row in ifile:
                letters.append(row.strip())

    # Create and run the UI
    app = App(letters, args.out, args.remove_dead, args.max_workers)
    app.mainloop()
