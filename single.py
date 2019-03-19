# -*- coding: utf-8 -*-
import re
import sys
import unicodedata
from email.utils import formatdate
from os import path as path
from urllib.parse import urljoin

import pystache
import requests
from bs4 import BeautifulSoup


class AltaVoce():
    def __init__(self, url):
        self.url = url

    def parse(self, contents):
        entries = []

        for content in contents:
            # url
            img = urljoin(self.url, content['data-image'])
            mp3 = url = urljoin(self.url, content['data-mediapolis'])
            url = urljoin(self.url, content['data-href']) or url
            # title
            title = content.find("h2").text.strip()
            entry = ({'url': url, 'mp3': mp3, 'title': title, 'image': img})
            duration = content.find(class_='timePlaylist')
            if duration:
                entry['duration'] = duration.text
            entries.append(entry)
        return entries

    def process(self, folder):
        out_data = {
            'url': self.url,
            'author': 'Ad Alta Voce - Rai Radio 3',
            'rss2update': formatdate(),
            'entries': []
        }
        result = requests.get(self.url)
        if result.status_code != 200:
            return None

        soup = BeautifulSoup(result.content, "html.parser")
        header = soup.find("div", class_="descriptionProgramma")
        out_data['title'] = header.find('h2').text
        out_data['description'] = header.find(class_='textDescriptionProgramma').text
        out_data['image'] = urljoin(self.url, soup.find(class_='imgHomeProgramma')['src'])
        contents = soup.find(class_='elencoPlaylist').find_all('li')

        out_data['entries'] = self.parse(contents)

        filename = out_data['title'].lower()
        filename = unicodedata.normalize('NFKD', filename)
        filename = re.sub(r'\W+', '-', filename)
        filename = filename.strip('-')
        filename = filename + '.xml'
        filepath = path.join(folder, filename)
        self.output(filepath, out_data)
        return filename

    @staticmethod
    def output(filename, data):
        renderer = pystache.Renderer()
        output = renderer.render_path(
            path.join(path.dirname(path.abspath(__file__)), 'podcast.mustache'), data)
        with open(filename, "w", encoding="utf8") as text_file:
            text_file.write(output)
        return True


def main():
    if len(sys.argv) < 2:
        print('Need a url')
        exit(2)
    altavoce = AltaVoce(sys.argv[1])
    print(altavoce.process('.'))


if __name__ == '__main__':
    main()
