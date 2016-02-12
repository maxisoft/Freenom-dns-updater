import re

from bs4 import BeautifulSoup

from .domain import Domain


class DomainParser(object):
    regex_domain_id = "clientarea\.php\?action=domaindetails&id=(\d+)"

    @classmethod
    def parse(cls, raw_html):
        soup = BeautifulSoup(raw_html, "html.parser")
        tag = soup.find("form", {'id': 'bulkactionform'})
        assert tag, "can't parse the given html"
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
            domain.id = props[5].find('a')['href']
            domain.id = re.match(cls.regex_domain_id, domain.id).group(1)
            ret.append(domain)
        return ret
