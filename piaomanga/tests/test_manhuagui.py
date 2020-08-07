import sys
sys.path.append("..")
sys.path.append("../..")
sys.path.append("../../..")

from PiaoManga.piaomanga.comicsource.MangaSource.manhuagui import Manhuagui
from PiaoManga import *

set_chromium(r"D:\MY_TOOL\chrome-win\chrome-win\chrome.exe")
print(get_source_list())
a = Manhuagui()

lst = a.get_comic_bytitle("恋爱")
#for item in lst:
#    print(item)
manga = lst[0]
chap = a.get_chapter_list(manga.name)
for item in chap:
    print(item)

a.get_chap_page_url_list(chap[0])