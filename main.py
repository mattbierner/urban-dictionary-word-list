import argparse
import itertools
import string
import time
import urllib.request
from os.path import exists

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


def extract_letter_entries(letter):
    url = API.format(letter)
    attempt = 0
    while url:
        print(url)
        response = urllib.request.urlopen(url)
        code = response.getcode()
        if code == 200:
            content = response.read()
            yield list(extract_page_entries(content))
            url = get_next(content)
            attempt = 0
        else:
            print(f"Trying again, expected response code: 200, got {code}")
            attempt += 1
            if attempt > MAX_ATTEMPTS:
                break
            time.sleep(DELAY * attempt)


opener = urllib.request.build_opener(
    NoRedirection, urllib.request.HTTPCookieProcessor()
)
urllib.request.install_opener(opener)


letters = list(string.ascii_uppercase) + ["#"]


def download_letter_entries(letter, file, remove_dead):
    file = file.format(letter)
    entries = itertools.chain.from_iterable(list(extract_letter_entries(letter)))

    if remove_dead or not exists(file):
        all_data = entries
    else:
        with open(file, "r", encoding="utf-8") as f:
            old_data = [line.strip() for line in f.readlines()]
        all_data = sorted(set(old_data).union(set(entries)), key=str.casefold)

    with open(file, "w", encoding="utf-8") as f:
        f.write("\n".join(all_data) + "\n")


def download_entries(letters, file, remove_dead):
    for letter in letters:
        print(f"======={letter}=======")
        download_letter_entries(letter, file, remove_dead)


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
    "--remove-dead", action="store_true", help="Removes entries that no longer exist."
)

args = parser.parse_args()

letters = [letter.upper() for letter in args.letters]
if not letters:
    with open(args.ifile, "r") as ifile:
        for row in ifile:
            letters.append(row.strip())

download_entries(letters, args.out, args.remove_dead)
