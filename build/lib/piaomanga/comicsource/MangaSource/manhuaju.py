__SOURCE_CLASS__ = "Manhuaju"
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
    domain = "http://www.manhuaju.com"
    mobile_domain = "http://m.manhuaju.com"

    search_uri = "/statics/search.aspx?key="


class Manhuaju(ComicSource):
    sourceID = "manhuaju"
    sourceName = u"漫画居"
    domain = _Res.domain

    def __init__(self):
        super().__init__()

        self.comicmap = {}

        self.chapter_pool = {}

        # 启动eventloop
        self.start()

    def get_comic_bytitle(self, comicTitle: str) -> List[comicStatus]:

        url = _Res.domain + _Res.search_uri + comicTitle
        logger.info(u"搜索标题: " + url)
        ret = self.asynurlget(url)
        if not ret:
            return []
        res = btfsoup(ret, "html.parser")
        res = res.find_all(class_="mh-list col7")
        done = False
        ret = []
        if res:
            # print(type(res), res)
            res = btfsoup(res.__str__(), "html.parser")
            res = res.find_all(class_="mh-item")
            if res:
                for item in res:
                    try:
                        dct = {"coverUrl": _Res.domain + item.p.get("style")}
                        try:

                            dct["coverUrl"] = re.findall(r"(?<=url\().*?(?=\))", dct["coverUrl"])[0]
                        except IndexError:
                            pass
                        dct["name"] = item.div.h2.a.get_text()
                        dct["doorUrl"] = _Res.domain + item.div.h2.a.get("href")
                        dct["lastChapterUrl"] = _Res.domain + item.div.find(class_="chapter").a.get("href")
                        dct["lastChapterName"] = item.div.find(class_="chapter").a.get("title")
                        try:
                            dct["chapterNum"] = int(re.findall(r'\d+', dct["lastChapterName"])[0])
                        except IndexError or ValueError:
                            dct["chapterNum"] = 1
                        ret.append(comicStatus(**dct))
                        self.comicmap[dct["name"]] = dct["doorUrl"]
                    except AttributeError:
                        logger.error(" parse error: item: " + item.__str__())

        else:
            logger.error(" can not find class_=mh-list col7")

        return ret

    def is_comic_exist(self, comicName: str):
        return self.comicmap.get(comicName) is not None

    # 用于搜索后查询漫画详细信息
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

        ret = self.asynurlget(url)
        if not ret:
            return None
        res = btfsoup(ret, "html.parser")
        res = res.find(class_=r"banner_detail_form")
        if res:
            print(res)
            res = btfsoup(res.__str__(), "html.parser")
            try:
                comic.author = res.find(class_=r"subtitle").a.get("title")
            except AttributeError:
                logger.error(u"漫画作者未找到，html未解析")
            try:
                comic.abstract = re.search(r"(?<=vertical;\">).*?(?=<a)"
                                    , res.find(class_=r"content").__str__()).group()
            except AttributeError:
                logger.error(u"漫画简介未找到，html未解析")
            try:
                comic.status = res.find(class_=r"tip").find_all(class_=r"block")[0].span.get_text()
            except AttributeError:
                logger.error(u"漫画状态未找到，html未解析")
            try:
                comic.type = res.find(class_=r"tip").find_all(class_=r"block")[1].a.span.get_text()
            except AttributeError:
                logger.error(u"漫画类型未找到，html未解析")

            logger.info(u"更新漫画状态 : " + comic.__str__())
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
        ret = self.asynurlget(url)
        if not ret:
            return []
        # ret.encoding = 'utf-8'
        res = btfsoup(ret, "html.parser")
        res = res.find(class_="view-win-list detail-list-select")
        if res:
            res = btfsoup(res.__str__(), "html.parser")
            res = res.find_all("li")
            if res:
                for i, item in enumerate(res):
                    title = item.a.get_text()
                    link = _Res.mobile_domain + item.a.get(r"href")
                    # 提取第几集
                    try:
                        number = int(re.search(r"\d{1,4}", title).group())
                    except AttributeError:
                        number = len(res) - i
                    chaplst.append(comicChapter(number, comicTitle, title, url=link))
        if needSort:
            chaplst.sort(key=lambda x: x.chapterNo)
        logger.info(u"{0}共[{1}]章节信息加载完毕 . ".format(comicTitle, len(chaplst)))
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
                # r = btfsoup(url, "html.parser")
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

        # 请求执行show 脚本后即可得到图片链接
        # pc版js r"manhuaju.com/template/skin5/css/d7s/js/show"
        ret = self.asynurlget_dynamic(chapter.url, filterpattern=r"m.manhuaju.com/template/wap1/css/d7s/js",
                                      maxworker=3, retrytimes=5, maxwaittime=50)
        # print(ret)
        if not ret:
            return list()
        retlst = list()
        totalpagenum = None
        # ret.encoding = 'utf-8'
        bts = btfsoup(ret[0], "html.parser")
        try:
            res = bts.body.find(class_="subHeader")
            res = re.search(r"(?<=id=\"k_total\">).*?(?=</span>)"
                            , res.__str__()).group()
            totalpagenum = res
        except AttributeError:
            logger.error(u"找不到目标元素 url:" + chapter.url)
            return retlst

        if not totalpagenum or not totalpagenum.isdigit():
            logger.info(u"未查到总页码  ")
            return retlst

        totalpagenum = int(totalpagenum)
        chapter.chapterPageNum = totalpagenum
        urls = [None] * totalpagenum
        # 第一页已经找到
        urls[0] = get_image_url(bts)

        togets = [chapter.url + "?p={0}".format(i) for i in range(1, totalpagenum + 1)]

        # 第二页开始
        i = 1
        while i < totalpagenum:
            if i + loadpertime >= totalpagenum:
                retlst = self.asynurlget_dynamic(togets[i:], filterpattern=r"m.manhuaju.com/template/wap1/css/d7s/js",
                                                 retrytimes=3, maxwaittime=30)

            else:
                retlst = self.asynurlget_dynamic(togets[i:i + loadpertime],
                                                 filterpattern=r"m.manhuaju.com/template/wap1/css/d7s/js",
                                                 retrytimes=3, maxwaittime=30)
            for j, item in enumerate(retlst):
                try:
                    bts = btfsoup(item, "html.parser")
                    urls[i + j] = get_image_url(bts)
                except:
                    #任务未完整
                    logger.error(u"第{0}页查询返回异常，返回当前已完成urls列表.异常html:{1}".format(i+j, bts))
                    return urls

            i += loadpertime

        #改写对象属性
        import copy
        chapter.pageUrls = urls
        mychapter = copy.deepcopy(chapter)

        try:
            self.chapter_pool[mychapter.comicName][mychapter.chapterName] = mychapter
        except KeyError:
            self.chapter_pool[mychapter.comicName] = {mychapter.chapterName: mychapter}
        logger.info(u"章节页url加载完毕 :" + urls.__str__() + "\n")
        return urls
