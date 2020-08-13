from typing import List
from urllib.parse import parse_qs, urlsplit

from bs4 import BeautifulSoup

from .domain import Domain


class DomainParser(object):
    @classmethod
    def parse(cls, raw_html) -> List[Domain]:
        soup = BeautifulSoup(raw_html, "html.parser")
        tag = soup.find("form", {'id': 'bulkactionform'})
        if not tag:
            raise ValueError("can't parse the given html")
        raw_domains = tag.select("tbody > tr")
        ret = []
        for raw_domain in raw_domains:
            props = raw_domain.find_all("td")
            domain = Domain()
            domain.name = props[0].text.strip().lower()
            domain.register_date = props[1].text
            domain.expire_date = props[2].text
            domain.state = props[3].text
            domain.type = props[4].text
            href = props[5].find('a')['href']
            query = urlsplit(href).query
            domain.id = parse_qs(query)['id'][0]
            ret.append(domain)
        return ret
