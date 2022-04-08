import random
import sys
import time

import cchardet
import requests

from pyquery import PyQuery as pq

from magic_google import MagicGoogle
from magic_google.config import Config
from magic_google.utils import get_data, get_logger

if sys.version_info[0] > 2:
    from urllib.parse import parse_qs, quote_plus, urlparse
else:
    from urllib import quote_plus

    from urllib.parse import parse_qs, urlparse


requests.packages.urllib3.disable_warnings(
    requests.packages.urllib3.exceptions.InsecureRequestWarning
)


class SearchPager:

    def __init__(self) -> None:
        self.mg = MagicGoogle()
        proxies = [{
            'http': 'http://127.0.0.1:7890',
            'https': 'http://127.0.0.1:7890'
        }]
        self.proxies = random.choice(proxies) if proxies else None
        super().__init__()

    def search_page(self, url, language=None, num=None, start=0, pause=2, country=None):

        #
        # url = url.replace("hl=None&", "") if language is None else url
        # url = url.replace("&cr=None", "") if country is None else url
        # Add headers
        headers = {"user-agent": self.mg.get_random_user_agent()}
        try:
            self.mg.logger.info(url)
            r = requests.get(
                url=url,
                proxies=self.proxies,
                headers=headers,
                allow_redirects=True,
                verify=False,
                timeout=30,
            )
            content = r.content
            charset = cchardet.detect(content)
            text = content.decode(charset["encoding"])
            return text
        except Exception as e:
            self.mg.logger.exception(e)
            return None
