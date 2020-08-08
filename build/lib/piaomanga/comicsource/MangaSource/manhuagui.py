__SOURCE_CLASS__ = "Manhuagui"
from typing import List, Dict, Set
import os
import sys
sys.path.append("..")
sys.path.append("../..")
from piaomanga.m_types.AbsComic import *
from AbsSource import *
from time import sleep, time
import asyncio
import aiohttp
import asyncio
import re
from bs4 import BeautifulSoup as btfsoup
import logging

# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - '
                                               '%(levelname)s - %(module)s -'
                                               ' %(funcName)s - %(threadName)s - %(message)s')
logger = logging.getLogger(__name__)


class _Res():
    domain = "https://www.manhuagui.com"
    mobile_domain = "https://tw.manhuagui.com"

    search_uri = "/s/{0}.html"


class Manhuagui(ComicSource):
    sourceID = "manhuagui"
    sourceName = u"漫画柜"
    domain = _Res.domain

    def __init__(self):
        super().__init__()

        self.comicmap = {}
        self.chapter_pool = {}
        # 启动eventloop
        self.start()

    def get_comic_bytitle(self, comicTitle: str) -> List[comicStatus]:

        url = (_Res.domain + _Res.search_uri).format(comicTitle)
        logger.info(u"搜索标题: " + url)
        ret = self.asynurlget(url,maxwork= 3, prestart= 1)
        if not ret:
            return []
        res = btfsoup(ret, "html.parser")
        res = res.find(class_="book-result")
        done = False
        ret = []
        if res:
            if res:
                mangalst = res.find_all(class_="cf")
                for item in mangalst:
                    dct = {}
                    detail = item.find(class_="book-detail")
                    dct["name"] = detail.a.get("title")
                    dct["author"] = re.search(r"(?<=作者).*?(?=/a>)", detail.__str__()).group()
                    dct["author"] = re.search(r"(?<=title=\").*?(?=\")", dct["author"]).group()
                    dct["doorUrl"] = _Res.mobile_domain + item.find(class_="bcover").get("href")
                    dct["coverUrl"] = item.find(class_="bcover").img.get("src")
                    dct["abstract"] = detail.find(class_="intro").span.strong.get_text()
                    dct["type"] = re.search(r"(?<=类型).*?(?=/a>)", detail.__str__()).group()
                    dct["type"] = re.search(r"(?<=title=\").*?(?=\")", dct["type"]).group()
                    stt = detail.find(class_="tags status").find_all(class_="red")
                    dct["status"] = stt[0].get_text()
                    dct["lastUpdateTime"] = stt[1].get_text()
                    dct["lastChapterUrl"] = _Res.mobile_domain+detail.find(class_="tags status").span.a.get("href")
                    dct["lastChapterName"] = detail.find(class_="tags status").span.a.get_text()
                    try:
                        dct["chapterNum"] = int(re.findall(r'\d+', dct["lastChapterName"])[0])
                    except IndexError or ValueError:
                        dct["chapterNum"] = 1
                    ret.append(comicStatus(**dct))
                    self.comicmap[dct["name"]] = dct["doorUrl"]

        return ret

    def is_comic_exist(self, comicName: str):
        return self.comicmap.get(comicName) is not None

    def update_comic(self, comic: comicStatus) -> comicStatus or None:
        try:
            url = self.comicmap[comic.name]
        except KeyError:
            self.get_comic_bytitle(comic.name)
            try:
                url = self.comicmap[comic.name]
            except KeyError:
                logger.error(u"更新失败 ")
                return comic

        return comic


    def get_chapter_list(self, comicTitle: str, needSort: bool = True, forceRefresh: bool = False) -> List[comicChapter]:
        try:
            url = self.comicmap[comicTitle]
        except KeyError:
            self.get_comic_bytitle(comicTitle)
            try:
                url = self.comicmap[comicTitle]
            except KeyError:
                return []

        chaplst = []
        logger.info(u"搜索 {0} 章节:".format(comicTitle) + url)
        ret = self.asynurlget(url,maxwork= 4, prestart= 2)
        if not ret:
            return []
        # ret.encoding = 'utf-8'
        res = btfsoup(ret, "html.parser")
        res = res.find(class_="chapter-list cf mt10").find_all("li")
        for i,item in enumerate(res):
            pageurl = _Res.mobile_domain + item.a.get("href")
            title = item.a.get("title")
            try:
                number = int(re.search(r"\d{1,4}", title).group())
            except:
                number = len(res) - i
            chaplst.append(comicChapter(number, comicTitle, title, url=pageurl))
        return chaplst


    def get_chap_page_url_list(self, chapter: comicChapter, loadpertime: int = 10, forceRefresh: bool = False) -> List[str]:
        if self.chapter_pool and not forceRefresh:
            try:
                cpt = self.chapter_pool[chapter.comicName][chapter.chapterName]
                urls = cpt.pageUrls
                if len(urls) >= cpt.chapterPageNum:
                    logger.info("chapter page has been load, use cache."+ cpt.__str__())
                    return cpt.pageUrls
            except KeyError:
                pass
        def get_image_url(url) -> str or None:
            try:
                r = url.body.find(class_="UnderPage").div.div.div
                #print(r)
                r = re.search(r"(?<=src=\").*?(?=&amp;)"
                              , r.__str__()).group()
                r = r.split(r"https%3A//")[1]
                return "https://" + r
            except AttributeError or IndexError:
                logger.error(u"找不到图片缓存地址 url:" + url.__str__())
                return None

        if not chapter.url:
            logger.info(u"查找章节:{0}\n没有Url地址  ".format(chapter))
            return list()

        logger.info(u"搜索章节:{0} {1}".format(chapter.chapterName, chapter.chapterNo))

        ret = self.asynurlget_dynamic(chapter.url, filterpattern=r"i.hamreus.com/ps2/z/",
                                      maxworker=3, retrytimes=5, maxwaittime=50)
        print(ret)
        if not ret:
            return list()
        retlst = list()