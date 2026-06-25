import httpx
from bs4 import BeautifulSoup
from typing import List
from ..utils.models import Programa

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )
}


class BaseScraper:
    nombre: str = "base"
    url_base: str = ""

    def __init__(self, timeout: int = 30):
        self.client = httpx.Client(
            headers=HEADERS,
            timeout=timeout,
            follow_redirects=True,
            verify=False,
        )

    def get(self, url: str) -> BeautifulSoup:
        r = self.client.get(url)
        r.raise_for_status()
        return BeautifulSoup(r.text, "lxml")

    def scrape(self) -> List[Programa]:
        raise NotImplementedError

    def close(self):
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()
