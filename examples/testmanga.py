import sys
sys.path.append("..")
sys.path.append("../..")

from PiaoManga import *
from time import time,sleep
def test():
    set_chromium(r"D:\MY_TOOL\chrome-win\chrome-win\chrome.exe")
    print(get_source_list())
    a = PiaoManga("city", "a")
    a.addsource("manhuaju")

    a.update()
    # print(a.curstatus)
    lst = a.get_chapter_list()
    todown = [item for item in lst if item.chapterNo >= 119]
    for item in todown:
        urls = [""]
        while None in urls or "" in urls:
            urls = a.cursource.get_chap_page_url_list(item, loadpertime=10)
        done = False

        def callback(args, *wd, **kw):
            nonlocal done
            done = True

        taskid = a.cursource.download_chapter(item, r"D:\MY_Collects\manga", successCallback=callback)
        st = time()
        while time() - st <= 60:

            if done:
                break
            # if a.cursource.downloader._get_tasks_is_done(taskid):
            #    break
            status = a.cursource.downloader.get_progress(taskid)
            for tt in status:
                #print(tt)
                pass
            print("\n")
            sleep(3)

    # a.setsource("manhuaju")
    # a.update()
    # print(a._source)


# t = timeit.repeat(stmt="test()", setup="from __main__ import test", number=10, repeat=10)
# print(t)
test()
# test()
