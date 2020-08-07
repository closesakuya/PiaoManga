__all__=['PiaoManga', 'set_chromium', 'get_source_list']
#from SourceFactory import ComicSourceFactory
from .comicsource import *
from typing import List, Dict, Set
import logging
#from AbsComic import *
from .m_types import *
from .utils import *

# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - '
                                               '%(levelname)s - %(module)s -'
                                               ' %(funcName)s - %(threadName)s - %(message)s')
logger = logging.getLogger(__name__)


def set_chromium(exepath:str = None, userdatapath:str = None):
    return UrlsTool.set_chromium_path(exepath, userdatapath)


def get_source_list():
    return ComicSourceFactory.get_source_list()


class PiaoManga:
    _sourceFactory = ComicSourceFactory()

    def __init__(self, name, author):

        self.name = name
        self.author = author

        self._comicStatus = {}
        self._source = {}
        self._chapter = []
        self._cursource = None

        self._curchapter = None
        self._curpage = 1

    @property
    def cursource(self):
        return self._source.get(self._cursource)

    @property
    def curstatus(self):
        return self._comicStatus.get(self._cursource)

    @property
    def curchapter(self):
        return self._curchapter

    @property
    def curpage(self):
        return self._curpage

    @property
    def chapterlist(self):
        if not self._chapter:
            self.get_chapter_list()
        return self._chapter

    def update(self) -> bool:
        if not self._cursource:
            logger.error("no source found\n")
            return False
        # 直接使用缓存的首页更新
        if self.cursource.is_comic_exist(self.name):
            self._comicStatus[self._cursource] = self.cursource.update_comic(self._comicStatus[self._cursource])
            # self.cursource.update_comic(self._comicStatus[self._cursource])
            self.name = self.curstatus.name
            self.author = self.curstatus.author
            return True

        # 重新搜索
        comiclst = self.cursource.get_comic_bytitle(self.name)
        if comiclst.__len__() == 1:
            self._comicStatus[self._cursource] = self.cursource.update_comic(comiclst[0])

        elif comiclst:
            r = self.choice_comic_handle(comiclst)
            if r:
                del self._comicStatus[self._cursource]
                self._comicStatus[self._cursource] = self.cursource.update_comic(r)

                # 更新名称作者
                self.name = self.curstatus.name
                self.author = self.curstatus.author

    def addsource(self, sourcename: str) -> bool:
        src = self._sourceFactory.get(sourcename)
        if src:
            self._source[sourcename] = self._sourceFactory.get(sourcename)
            self._comicStatus[sourcename] = None
            if not self._cursource:
                self.setsource(sourcename)
                self.update()

            return True
        else:
            return False

    # can be override
    @staticmethod
    def choice_comic_handle(choiceItem: List[comicStatus] or Dict[comicStatus]) -> comicStatus:
        if type(choiceItem) is list:
            for i, item in enumerate(choiceItem):
                print("{0}. {1}".format(i, item))
            idx = input(u"请选择序号:0--{0}".format(len(choiceItem) - 1))
            return choiceItem[int(idx)]
        elif type(choiceItem) is dict:
            pass

    # can be override
    @staticmethod
    def choice_chapter_handle(choiceItem: List[comicChapter], defaultchoice: int = 0) -> comicChapter:
        return choiceItem[defaultchoice]

    # can be override
    @staticmethod
    def choice_page_handle(pagetotal: int, defaultchoice: int = 0) -> int:
        return defaultchoice

    def search_source(self):
        for srcname, src in self._sourceFactory:
            comiclst = src().get_comic_bytitle(self.name)
            print(srcname, src, comiclst)

    def setsource(self, sourcename: str) -> bool:
        try:
            self._cursource = sourcename
            return True
        except KeyError:
            logger.error("comic source : " + sourcename + " not found!\n")
            return False

    def get_chapter_list(self) -> List[comicChapter]:
        if not self.cursource:
            return []
        # 缓存
        self._chapter = self.cursource.get_chapter_list(self.name)

        return self._chapter

    def read(self, chapterNo: int = None, pageNo: int = None):

        if not chapterNo:
            chap = self.choice_chapter_handle(self.chapterlist)
        else:
            assert len(self.chapterlist) >= chapterNo > 0
            chap = self.chapterlist[chapterNo - 1]

        if not pageNo:
            pageNo = self.choice_page_handle(chap.chapterPageNum)


import timeit


# if __name__ == "__main__":
