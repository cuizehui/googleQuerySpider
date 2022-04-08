import datetime
import hashlib
import logging
import os
import random
import sys
import re
import Levenshtein

from urllib.parse import parse_qs, urlparse

import sqlite3

import pymysql
from pymysql.converters import escape_string
from bs4 import BeautifulSoup
from pandas import DataFrame
import pandas as pd
from magic_google import MagicGoogle
from request.search_page import SearchPager

sys.path.append(os.path.dirname(os.path.dirname(__file__)))


# ------------------------------

class DataBaseOperation:
    columns = ['SpiderFileName', 'url', 'shopName', "icon", 'keyWord', 'searchflag']
    database_name = "shopInfo.db"
    database_path = "./shopInfo.db"
    data_sources = 'sender.xlsx'
    shop_info_table_name = 'shopInfo'

    def __init__(self) -> None:
        super().__init__()

    def init(self):
        sqlite_conn = sqlite3.connect(self.database_path)
        df = pd.read_excel(self.data_sources)
        df.to_sql(self.shop_info_table_name, con=sqlite_conn, schema=self.shop_info_table_name, if_exists='append',
                  index=True)
        for index, columns_name in enumerate(self.columns):
            if index == 5:
                add_columns_sql = ('ALTER TABLE %s ADD  %s INT' % (self.shop_info_table_name, self.columns[index]))
            else:
                add_columns_sql = (
                        'ALTER TABLE %s ADD  %s VARCHAR(255)' % (self.shop_info_table_name, self.columns[index]))
            try:
                sqlite_conn.execute(add_columns_sql)
            except Exception:
                pass
                log_print("exception update sql")
        sqlite_conn.close()

    def query_all_need_spider_sender(self):
        sqlite_conn = sqlite3.connect(self.database_path)
        cursor = sqlite_conn.execute(
            # "SELECT sender , language FROM shopInfo  ORDER BY 'index' DESC")
            "SELECT sender , language , content FROM shopInfo  WHERE shopName  is  null  ORDER BY "
            # "SELECT sender , language , content FROM shopInfo  WHERE shopName  is null  AND icon is null ORDER BY "
            # "'index' DESC")
            "'send_count' DESC")
        result = cursor.fetchall()
        sqlite_conn.close()
        return result

    def update_sender_data_from_shop_info(self, shop_info):
        sqlite_conn = sqlite3.connect(self.database_path)
        requirement_list = []
        if shop_info.spider_file:
            requirement_list.append(self.columns[0] + " = " + "'" + shop_info.spider_file.replace("'", " ") + "'")
        if shop_info.url:
            requirement_list.append(self.columns[1] + " = " + "'" + shop_info.url.replace("'", " ") + "'")
        if shop_info.shop_name:
            requirement_list.append(self.columns[2] + " = " + "'" + shop_info.shop_name.replace("'", " ") + "'")
        if shop_info.icon:
            requirement_list.append(self.columns[3] + " = " + "'" + shop_info.icon.replace("'", " ") + "'")
        if shop_info.keyWord:
            requirement_list.append(self.columns[4] + " = " + "'" + shop_info.keyWord.replace("'", " ") + "'")
        requirement_list.append(self.columns[5] + " = " + '1')
        update_shop_info_sql = "UPDATE " + self.shop_info_table_name + " set " + ",".join(
            requirement_list) + " WHERE " + " sender = '%s'" % shop_info.number.replace("'", " ")
        log_print(update_shop_info_sql)
        sqlite_conn.execute(update_shop_info_sql)
        sqlite_conn.commit()
        sqlite_conn.close()


class FileOperation:

    def __init__(self) -> None:
        super().__init__()
        self.path = os.getcwd() + "/data"

    def sava_result_to_file(self, file_name, result):
        folder = os.path.exists(self.path)
        if not folder:
            os.makedirs(self.path)
        with open(self.path + "/%s" % file_name, "w", encoding="utf-8") as text_file:
            text_file.write(result)
        return text_file.name

    def read_file(self, xml_file_name):
        try:
            f = open(self.path + "/%s" % xml_file_name, "r", encoding="utf-8")
            contents = f.read()
        except FileNotFoundError:
            contents = ''
            pass
        return contents

    def check_file_exist(self, file_name):
        return os.path.exists(os.getcwd() + "/data/" + file_name)


class Spider:
    TAG = "Spider"

    def __init__(self) -> None:
        super().__init__()
        self.mg = MagicGoogle()
        self.do_config()
        self.sp = SearchPager()
        self.dbo = DataBaseOperation()
        self.fo = FileOperation()

    def do_config(self):
        pass

    def start(self):
        cursor = self.dbo.query_all_need_spider_sender()
        log_print("start spider %d" % cursor.__len__())
        for index, row in enumerate(cursor):
            log_print("start index : %d" %index)
            # if index == 1:
            #     break
            # shop_info = ShopInfo()
            # shop_info.number = "AD-650003"
            # shop_info.country = 'id'
            # shop_info.keyWord = '9319XXX201 par Airtel pack samapt hone wala hai!Abhi recharge karein aur anand lein 1.5GB/din,100SMS/din,UL call, 56 din, Rs479 mein. https://p.paytm.me/xCTH/airpld'
            # ----
            shop_info = ShopInfo()
            shop_info.number = row[0]
            shop_info.country = row[1]
            shop_info.keyWord = row[2]
            log_print(row)

            self.start_search_spider(shop_info)

    def start_search_spider(self, shop_info):
        sleep = random.randint(2, 15)
        sender = self.deal_sender_name(shop_info.number)
        xml_file_name = sender + ".html"

        search_keyword = SearchKeyWord()
        search_keyword.isSenderWord = self.judge_sender_is_word(sender)

        if search_keyword.isSenderWord:
            search_keyword.keyWord = sender
        else:
            log_print(" deal  number")
            search_keyword = self.extract_keywords(shop_info.keyWord)

        shop_info.keyWord = search_keyword.keyWord
        if search_keyword.isUrl or (not search_keyword.isSenderWord and search_keyword.isContent):
            deal_results = Extract()
            deal_results.topUri.append(search_keyword.keyWord)
        else:
            if not self.fo.check_file_exist(xml_file_name):
                log_print("start request------ %s" % search_keyword.keyWord)
                result = self.mg.search_page(query=search_keyword.keyWord, num=1, pause=sleep,
                                             country=shop_info.country)
                if result:
                    self.fo.sava_result_to_file(xml_file_name, result)
                    log_print("xml_file_name %s-------" % xml_file_name)
                else:
                    log_print("request error")
                    return
            shop_info.spider_file = xml_file_name
            deal_results = self.deal_google_xml_data(xml_file_name)

        for uri in deal_results.topUri:
            try:
                uri = urlparse(uri)
                if self.is_url_match_key(sender, uri.geturl()) or search_keyword.isSenderWord is not True:
                    log_print(uri.geturl())
                    shop_info.url = uri.geturl()
                    md5hash = hashlib.md5(uri.geturl().encode('utf-8'))
                    file_name = md5hash.hexdigest()
                    shop_info_file_name = sender + "_" + file_name + "_info.html"
                    if not self.fo.check_file_exist(shop_info_file_name):
                        log_print("search_page : %s" % uri.geturl())
                        shop_info_xml = self.sp.search_page(uri.geturl())
                        if shop_info_xml:
                            log_print("sava_result_to_file : %s" % shop_info_file_name)
                            self.fo.sava_result_to_file(shop_info_file_name, shop_info_xml)
                    if self.deal_company_xml_data(shop_info_file_name, shop_info):
                        break
            except FileNotFoundError:
                log_print("Unexpected : %s" % sys.exc_info()[0])
                print("Unexpected error:", sys.exc_info()[0])
        self.dbo.update_sender_data_from_shop_info(shop_info)

    def deal_sender_name(self, number):
        if number:
            senderlist = number.split('-')
        if len(senderlist) == 1:
            if len(number) > 6 and (
                    number.startswith("QP") or number.startswith("AD")
                    or number.startswith("JD") or number.startswith("CP")):
                sender = number[2:]
            else:
                sender = senderlist[0]
        else:
            sender = senderlist[len(senderlist) - 1]
        log_print(sender)
        return sender

    def deal_google_xml_data(self, xml_file_name):
        log_print("deal_google_xml_data------")
        contents = self.fo.read_file(xml_file_name)
        if not contents:
            return
        soup = BeautifulSoup(contents, 'lxml')
        results = Extract()
        for g in soup.find_all('div'):
            anchors = g.find_all('a')
            if anchors:
                temp_link = anchors[0]['href']
                link = Spider.filter_link(temp_link)
                if link:
                    results.topUri.append(link)
        list_temp = list(set(results.topUri))
        list_temp.sort(key=results.topUri.index)
        results.topUri = list_temp
        log_print(results.topUri)
        return results
        pass

    def is_url_match_key(self, key, url):
        match_key = "{1}.*".join(key.lower().replace("+", ""))
        match_obj = re.search(match_key, url, re.I)
        uri = urlparse(url)
        if uri.hostname:
            if uri.hostname.startswith("accounts.google") or uri.hostname.startswith(
                    "maps.google") or uri.hostname.startswith("support.google") or uri.hostname.startswith("www.google"):
                return None

        if match_obj:
            return match_obj
        else:
            sim = Levenshtein.jaro(key.lower(), uri.hostname)
            log_print("match jaro %f" % sim)
            if sim > 0.5:
                return sim


    def extract_keywords(self, content):
        """
        优先匹配url -> label eg: -face book
        """
        url_pattern = '(https?|ftp|file)://[-A-Za-z0-9+&@#/%?=~_|!:,.;]+[-A-Za-z0-9+&@#/%=~_|]'
        no_scheme_url_pattern = "([\w-]+\.)+[\w-]+(/[\w/?%&=]*)"
        label_pattern = ""
        search_keyword = SearchKeyWord()
        if re.search(url_pattern, content):
            keyword = re.search(url_pattern, content)
            search_keyword.isUrl = True
        elif re.search(no_scheme_url_pattern, content):
            keyword = re.search(no_scheme_url_pattern, content)

            search_keyword.isUrl = True
        else:
            keyword = re.search(label_pattern, content)

        if keyword and keyword.group(0):
            if search_keyword.isUrl:
                uri = urlparse(keyword.group(0))
                if not uri.hostname:
                    uri = urlparse("https://%s" % keyword.group(0))
                search_keyword.keyWord = uri.geturl()
            else:
                search_keyword.keyWord = keyword.group(0)
        else:
            search_keyword.isContent = True
            search_keyword.keyWord = content[50:]
        return search_keyword

    def judge_sender_is_word(self, keyword):
        number_pattern = '[a-z]'
        match_obj = re.search(number_pattern, keyword, re.I)
        return match_obj

    def deal_company_xml_data(self, xml_file_name, shop_info):
        log_print("deal_company_xml %s" % xml_file_name)
        contents = self.fo.read_file(xml_file_name)
        if not contents:
            log_print("not company contents")
            return False
            pass
        soup = BeautifulSoup(contents, 'lxml')

        # deal title
        if soup.head:
            title = ""
            if soup.title:
                title = soup.title.string

            title_property = soup.head.findAll(name="meta",
                                               attrs={"property": "title", "property": "og:title",
                                                      "property": "twitter:title"})
            for p in title_property:
                if p.attrs.get("content"):
                    title = p.attrs["content"]
            if title:
                log_print('title %s' + title)
                shop_info.shop_name = title

            # deal icon
            icon_link = ""
            icon = ""
            icon_property = soup.head.findAll(name="meta",
                                              attrs={"property": "og:image"})
            for p in icon_property:
                if p.attrs.get("content"):
                    icon = p.attrs["content"]
                if p.attrs.get("href"):
                    icon = p.attrs["href"]
            if icon:
                log_print('icon_property %s' + icon)
                shop_info.icon = icon
            icon_link = soup.head.findAll(name="link", attrs={"rel": "icon", "rel": "shortcut icon", "rel": "og:image"})
            for i in icon_link:
                log_print(i)
                if i.attrs["href"]:
                    icon_link = i.attrs["href"]
            if icon_link:
                shop_info.icon = icon_link
        return True

    def filter_link(templink):
        try:
            # Valid results are absolute URLs not pointing to a Google domain
            # like images.google.com or googleusercontent.com
            o = urlparse(templink, "http")
            if o.netloc:
                return templink
            # Decode hidden URLs.
            if templink.startswith("/url?"):
                link = parse_qs(o.query)["q"][0]
                # Valid results are absolute URLs not pointing to a Google domain
                # like images.google.com or googleusercontent.com
                o = urlparse(link, "http")
                if o.netloc:
                    return link
        # Otherwise, or on error, return None.
        except Exception as e:
            # self.logger.exception(e)
            return None


# --------------------------------

class SearchKeyWord:
    isUrl: bool
    keyWord: str
    isContent: bool
    isSenderWord: bool

    def __init__(self) -> None:
        super().__init__()
        self.isUrl = False
        self.isContent = False
        self.keyWord = ""
        self.isSenderWord = False
        pass


# ---------------------------------

class ShopInfo:
    number: str
    keyWord: str
    spider_file: str
    shop_name: str
    url: str
    country: str
    icon: str

    def __init__(self) -> None:
        super().__init__()
        self.number = ""
        self.keyWord = ""
        self.spider_file = ""
        self.shop_name = ""
        self.url = ""
        self.icon = ""
        pass


# -------------------------------

class Extract:

    def __init__(self) -> None:
        super().__init__()
        self.topUri = []
        self.shopName: str
        self.icon: str


def log_print(log):
    logging.info(log)
    print(log)
    pass


def main():
    spider = Spider()
    spider.start()
    pass


if __name__ == '__main__':
    main()
