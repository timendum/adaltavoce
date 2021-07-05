import datetime
import re
import sys
from collections import namedtuple
from os import path as path
from urllib.parse import urljoin

import chevron
import requests
from bs4 import BeautifulSoup

from single import AltaVoce

BASE_URL = "https://www.raiplayradio.it/programmi/adaltavoce/archivio/audiolibri/tutte/"

Entry = namedtuple("Entry", ["title", "text", "file", "img"])


class AdAltaVoce:
    def __init__(self):
        self.page = 1
        self.entries = []
        self._base_path = path.join(path.dirname(path.abspath(__file__)), "dist")
        self._text_re = re.compile(r"((?:[A-Z][a-z]+) (?:(?:[A-Z][a-z]*\.?|de) )?(?:[A-Z][a-z]+))")

    def next_page(self):
        result = requests.get(BASE_URL + str(self.page))
        if result.status_code != 200:
            return None
        soup = BeautifulSoup(result.content, "html.parser")
        elements = soup.find_all(class_="programItemPlaylist")
        for element in elements:
            url = urljoin(result.url, element.parent["href"])
            img = urljoin(result.url, element.find("img")["src"])
            title = element.find("h3").text
            # author, reader = self._parse_text(element)
            text = element.find(class_="canale").text.strip()
            altavoce = AltaVoce(url)
            file = altavoce.process(self._base_path)
            if file:
                self.entries.append(Entry(title, text, file, img))
                print(self.entries[-1])
        self.page = self.page + 1
        return len(elements) > 0

    def all_pages(self):
        while self.next_page():
            pass

    def _parse_text(self, element):
        textes = [element.find(class_="canale").text, element.find(class_="description").text]
        for text in textes:
            matches = self._text_re.findall(text)
            if len(matches) == 2:
                return matches
        raise ValueError("Author not found in {}".format(element.find("h3").text))

    def write_index(self):
        # Build letter index
        index = {}
        for entry in self.entries:
            letter = entry.title[0].lower()
            if letter not in index:
                index[letter] = {"letter": letter, "upper": letter.upper, "entries": []}
            index[letter]["entries"].append(entry)
        # Sort entries
        for letter in index:
            index[letter]["entries"] = sorted(
                index[letter]["entries"], key=lambda entry: entry.title.lower()
            )
        index_data = [index[k] for k in sorted(index.keys())]
        # Render
        with open(path.join(path.dirname(path.abspath(__file__)), "index.mustache"), "r") as t:
            output = chevron.render(
                t,
                {"index": index_data, "lastUpdate": datetime.date.today().isoformat()},
            )
        with open(path.join(self._base_path, "index.html"), "w", encoding="utf8") as text_file:
            text_file.write(output)


if __name__ == "__main__":
    ALTAVOCE = AdAltaVoce()
    ALTAVOCE.all_pages()
    if len(sys.argv) > 1 and sys.argv[1] == "-nohtml":
        pass
    else:
        ALTAVOCE.write_index()
