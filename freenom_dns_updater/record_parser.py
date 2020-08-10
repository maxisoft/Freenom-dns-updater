from bs4 import BeautifulSoup

from .record import Record


class RecordParser(object):
    @classmethod
    def parse(cls, raw_html):
        if "No records to display." in raw_html:
            return []
        soup = BeautifulSoup(raw_html, "html.parser")
        tag = soup.find("input", {'name': 'dnsaction', 'value': 'modify'})
        assert tag, "can't parse the given html"
        tag = tag.parent
        raw_records = tag.select("tbody > tr")
        ret = []
        for raw_record in raw_records:
            inputs = raw_record.find_all("input")
            record = Record()
            record.type = inputs[1]["value"]
            record.name = inputs[2]["value"]
            record.ttl = inputs[3]["value"]
            record.target = inputs[4]["value"]
            ret.append(record)
        return ret
