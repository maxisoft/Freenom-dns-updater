import time
from typing import Optional, Union
from urllib.parse import urlparse

import requests


class FreenomSession(requests.Session):
    last_request_time: float
    previous_url: Optional[str] = None
    request_cooldown = 3.0
    retry = 3

    def __init__(self):
        super().__init__()
        self.last_request_time = time.monotonic()

    def request(self, method, url, *args, **kwargs) -> requests.Response:
        if abs(self.last_request_time - time.monotonic()) < self.request_cooldown:
            time.sleep(self.request_cooldown)
        res: Optional[requests.Response] = None
        for i in range(self.retry):
            res = super().request(method, url, *args, **kwargs)
            self.last_request_time = time.monotonic()
            self.previous_url = url
            retry = False
            if res.status_code == 503:
                if "Back-end server is at capacity" in self._decode_reason(res.reason):
                    retry = True
            if res.status_code == 504:
                retry = True
            if retry:
                time.sleep(self.request_cooldown)
                continue
            return res
        assert res is not None
        return res

    def _decode_reason(self, reason: Union[str, bytes]) -> str:
        if isinstance(reason, bytes):
            try:
                reason = reason.decode('utf-8')
            except UnicodeDecodeError:
                if isinstance(reason, bytes):
                    reason = reason.decode('iso-8859-1')
        return reason

    def prepare_request(self, request: requests.Request):
        request = self._inject_headers(request)
        return super().prepare_request(request)

    def _inject_headers(self, request: requests.Request) -> requests.Request:
        if request.headers is None:
            request.headers = dict()

        if 'Host' not in request.headers:
            url = urlparse(request.url)
            request.headers['Host'] = url.hostname

        if 'Referer' not in request.headers:
            if self.previous_url is not None:
                request.headers['Referer'] = self.previous_url
            else:
                request.headers['Referer'] = request.url

        return request
