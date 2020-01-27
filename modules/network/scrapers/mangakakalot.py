from typing import List

import requests
from bs4 import BeautifulSoup

from .frame import ScraperSource
from ..decorators import checked_connection
from ..models import Chapter, Page, Manga, MangaStatus
from ..exceptions import IdentificationError, NetworkError


class Mangakakalot(ScraperSource):

    @checked_connection
    def get_manga_info(self, url: str) -> Manga:

        r = requests.get(url)
        soup = BeautifulSoup(r.content, "html.parser")

        type = _Source.identify(url)

        instance = Manga()
        if type == _Source.Mangakakalot:
            titlebox = soup.find(class_="manga-info-text")
            if titlebox is None:
                raise IdentificationError('Unable to identify title box.')

            instance.url = url
            instance.title = titlebox.find("h1").text

            for box in titlebox.find_all('li'):
                if box.text.startswith('Status :'):
                    instance.status = MangaStatus.parse(box.text[9:])

            _descriptionbox = soup.find('div', {'id': 'noidungm'})
            instance.description = _descriptionbox.text[len(_descriptionbox.find('h2').text):].strip()
        elif type == _Source.Manganel:
            leftpanel = soup.find(class_='story-info-right')
            if leftpanel is None:
                raise IdentificationError('Unable to identify info panel.')

            instance.url = url
            instance.title = leftpanel.find('h1').text

            for box in leftpanel.find_all('tr'):
                content = box.find_all('td')
                if 'info-status' in content[0].find('i')['class']:
                    instance.status = MangaStatus.parse(content[1].text)

            _descriptionbox = soup.find('div', {'id': 'panel-story-info-description'})
            instance.description = _descriptionbox.text[len(_descriptionbox.find('h3').text) + 1:].strip()

        return instance

    @checked_connection
    def get_chapter_list(self, manga: Manga) -> List[Chapter]:
        r = requests.get(manga.url)
        soup = BeautifulSoup(r.content, "html.parser")

        type = _Source.identify(manga.url)

        chapter_list = []
        if type == _Source.Mangakakalot:
            chapterbox = soup.find_all(class_="chapter-list")
            rows = chapterbox[0].find_all(class_="row")

            for i in range(len(rows) - 1, -1, -1):
                chapter_list.append(
                    Chapter(rows[i].find("a", href=True).text, rows[i].find("a", href=True)['href']))
        elif type == _Source.Manganel:
            rows = soup.find_all('li', {'class': 'a-h'})

            for i in range(len(rows) - 1, -1, -1):
                title = rows[i].find("a", href=True).text
                url = rows[i].find("a", href=True)['href']

                chapter_list.append(Chapter(title, url))

        return chapter_list

    @checked_connection
    def get_page_list(self, chapter: Chapter) -> List[Page]:
        r = requests.get(chapter.url)
        soup = BeautifulSoup(r.content, "html.parser")

        type = _Source.identify(chapter.url)

        if type == _Source.Mangakakalot:
            pagebox = soup.find(id="vungdoc")
        elif type == _Source.Manganel:
            pagebox = soup.find(class_="container-chapter-reader")

        rows = pagebox.find_all('img')

        pages = []
        for row in rows:
            pages.append(Page(row['src']))
        return pages


class _Source:
    Mangakakalot = 'mangakakalot'
    Manganel = 'manganel'

    @staticmethod
    def identify(url):
        if 'mangakakalot' in url:
            return _Source.Mangakakalot
        elif 'manganel' in url:
            return _Source.Manganel
        else:
            raise IdentificationError('Unable to identify source.')