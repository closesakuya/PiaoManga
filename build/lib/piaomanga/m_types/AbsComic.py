__all__ = ['comicConst', 'comicChapter','comicStatus']
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - '
                                               '%(levelname)s - %(module)s -'
                                               ' %(funcName)s - %(threadName)s - %(message)s')
logger = logging.getLogger(__name__)


class comicConst:
    __slots__ = ("name", "author", "type")

    def __init__(self, name, author="anonymous", **kw):
        kw["name"] = name
        kw["author"] = author
        for k in self.__slots__:
            object.__setattr__(self, k, kw.get(k))

    def __setattr__(self, name, value):
        pass


class comicStatus(comicConst):
    _dict = ("status", "lastChapterName", "coverUrl", "doorUrl",
             "lastChapterUrl", "chapterNum", "abstract",
             "lastUpdateTime")

    def __init__(self, name, author="anonymous", **kw):
        super().__init__(name, author, **kw)

        for item in self._dict:
            object.__setattr__(self, item, kw.get(item))

    def __str__(self):
        res = self.__class__.__name__ + ":"
        detail = ["{0} : {1}".format(k, self.__getattribute__(k)) for k in super(comicStatus, self).__slots__]
        detail = ", ".join(detail) + ", " + ", ".join(
            k.__str__() + ': ' + v.__str__() for k, v in (self.__dict__.items()))
        res = res + '( ' + detail + ')'
        return res

    def __setattr__(self, name, value):
        return object.__setattr__(self, name, value)

    def set(self, attr: str, value: not None):
        if attr in self._dict or attr in super(comicStatus, self).__slots__:
            object.__setattr__(self, attr, value)


class comicChapter:
    _dct = (
    "comicName", "chapterName", "url", "coverUrl", "chapterNo", "chapterPageNum", "abstract", "pageUrls", "args")

    def __init__(self, chapterNo: int, comicName: str = None, chapterName: str = None, url: str = None,
                 chapterPageNum: int = None, **kw):
        for item in self._dct:
            self.__setattr__(item, None)
        self.comicName = comicName
        self.chapterNo = chapterNo
        self.chapterName = chapterName
        self.url = url
        self.chapterPageNum = chapterPageNum
        self.pageUrls = []
        self.args = {}
        if not self.chapterName:
            self.chapterName = "No.{0}".format(self.chapterNo)

        for k, v in kw.items():
            if k in self._dct:
                self.__setattr__(k, v)

    def __setattr__(self, key, value):
        if key not in self._dct:
            print("key not in dict ,can not set\n".format(key))
        else:
            return object.__setattr__(self, key, value)

    def __str__(self):
        ret = ",".join([k + ": " + str(self.__getattribute__(k)) for k in self._dct])
        return ret
