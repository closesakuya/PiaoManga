__all__=['ComicSourceFactory']
import os
import sys
import re
from importlib import import_module
import importlib.util
_pattern = re.compile(r'^__SOURCE_CLASS__', re.I)
_source_dir_name = 'MangaSource'
def get_obj_from_file( filename:str,maxreadline:int=20):
    cnt = 0
    with open(filename, 'r',encoding='UTF-8') as f:
        for line in f:
            matchObj  = re.match(_pattern,line.strip())
            if matchObj:
                try:
                    clsname = line.split('=')[1].strip().strip(' ').strip('"').strip("'")
                    #print("class name " + clsname)
                except IndexError:
                    print(u"import source格式非法: " + line)
                    break

                try:
                    modname = filename.split(_source_dir_name)[1].strip(os.path.sep).strip('.py').replace(os.path.sep, '.')
                    #print("modname " + modname)
                except IndexError:
                    print(u"import modname格式非法: " + filename)
                    break
                try:
                    md = importlib.import_module(modname, package="MangaSource")
                    cls = eval( 'md.' + clsname)
                    return cls
                except ModuleNotFoundError:
                    print(u"import {0} 失败".format(modname + '.' + clsname))
                    return None
                except AttributeError:
                    print(u"文件:{0} 中写入的类名:'__SOURCE_CLASS__={1}' 不存在".format(filename, clsname))
                    return None
                except:
                    print(u"未知错误：当前在处理 file :{0} |import: {1} |class: {2} |line:{3}"
                          .format(filename, modname, clsname, line))
            cnt +=1
            if cnt >= maxreadline:
                break
    return None
def get_all_source( path , source_obj = {}, deep:int = 0):
    if deep >= 2: #只搜索二级目录
        return source_obj
    flst = os.listdir(path)
    for item in flst:
        item = os.path.join(path,item)
        if os.path.isfile(item) and item.endswith('.py'):
            cls = get_obj_from_file(item)
            if cls:
                source_obj.update({cls.sourceID:cls})
        elif os.path.isdir(item):
            get_all_source(item,source_obj,deep+1 )
    return source_obj

sys.path.append(os.path.split(os.path.realpath(__file__))[0]) #添加当前文件路径到import搜索路径
FILE_PATH = os.path.split(os.path.realpath(__file__))[0] + os.path.sep + _source_dir_name
sys.path.append(FILE_PATH) #添加当前文件路径到import搜索路径

SOURCESET = {}
get_all_source(FILE_PATH, SOURCESET)

#SOURCESET = {Manhuaju.sourceID: Manhuaju, Manhuaju.sourceName: Manhuaju}


class ComicSourceFactory:

    def __init__(self):
        self._iterItem = list(SOURCESET.keys())
        self._iterUni = []

    @staticmethod
    def get_source_list( ):
        return [[s.sourceID, s.sourceName, s.domain ] for s in set(SOURCESET.values())]

    def get(self, sourcename: str):
        try:
            return SOURCESET[sourcename]()
        except KeyError:
            return None

    def __iter__(self):
        return self

    def __next__(self):
        try:
            key = self._iterItem.pop(0)
            value = SOURCESET[key]
            if value not in self._iterUni:
                self._iterUni.append(value)
                return key,SOURCESET[key]
            else:
                return self.__next__()
        except IndexError:
            self._iterItem.clear()
            self._iterItem  = self._iterItem + list(SOURCESET.keys())
            self._iterUni.clear()
            raise StopIteration()

    def __call__(self, sourcename: str):
        return SOURCESET[sourcename]()


if __name__ == "__main__":
    a = ComicSourceFactory().get(u"漫画居")
    a.start()
    ret = a.get_comic_bytitle(u"恋爱")
    for item in ret:
        print(item)
    # a.addtask(add, 11,12,callback = print)
