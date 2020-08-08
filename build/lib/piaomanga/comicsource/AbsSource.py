__all__=['ComicSource']
import sys
sys.path.append("..")
sys.path.append("../..")
from piaomanga.utils import UrlsTool
from piaomanga.m_types import *
from piaomanga.utils import DownLoader
from time import sleep, time
import os
from functools import partial
import asyncio
import threading
import logging

from typing import List, Dict, Set, Callable


# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - '
                                               '%(levelname)s - %(module)s -'
                                               ' %(funcName)s - %(threadName)s - %(message)s')
logger = logging.getLogger(__name__)


class ComicSource(UrlsTool):
    sourceID = "meta"
    sourceName = u"未实例化"
    domain = "None"
    def __init__(self):
        super().__init__()

        self.downloader = DownLoader.Downloader(self)


    def get_comic_bytitle(self, comicTitle: str) -> List[comicStatus]:
        raise NotImplementedError

    def get_chapter_list(self, comicTitle: str, needSort: bool = False, forceRefresh: bool = False) -> List[str]:
        raise NotImplementedError

    def get_chap_page_url_list(self, chapter: comicChapter, loadpertime: int = 20, forceRefresh: bool = False) -> List[
        str]:
        raise NotImplementedError

    # can be inherited
    def download_chapter(self, chapter: comicChapter, folder: str = None, picFormat: str = 'jpg',
                         successCallback: Callable = None,
                         failedCallback: Callable = None) -> str:

        if not chapter.pageUrls:
            pageUrls = self.get_chap_page_url_list(chapter)
        else:
            pageUrls = chapter.pageUrls
        # urls需大于总页数
        assert len(chapter.pageUrls) >= chapter.chapterPageNum

        if not folder:
            folder = os.getcwd()
        mangadir = folder.strip(os.path.sep) + os.path.sep + chapter.comicName + os.path.sep + chapter.chapterName

        try:
            os.makedirs(mangadir)
        except FileExistsError:
            pass

        ts = []
        for i, url in enumerate(pageUrls):
            path = mangadir + os.path.sep + "{0}.{1}".format(i + 1, picFormat)
            name = chapter.comicName + '_' + str(i+1) + '_' + chapter.chapterName
            if not os.path.exists(path):    #不覆盖
                ts.append(DownLoader.DownloadTaskStatus(url, name, path))
            else:
                logger.info(u"文件{0} 已存在，退出下载".format(path))
        # return taskid

        return self.downloader.download(ts, successCallback=successCallback, failedCallback=failedCallback)
