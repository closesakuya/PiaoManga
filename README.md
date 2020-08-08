# PiaoManga
a manga downloader, can witch source site, currently support site "manhuaju"

一个基于pyppeteer的漫画下载器，目前完成基本框架并支持一个漫画源"manhuaju.com"，后续会持续完善。
可增加/piaomanga/comicsource/MangaSource/下的代码来增加漫画源，按示例格式添加后会自动识别。

##安装 :
`>>python setup.py install`
(pyppeteer库需要安装cromium浏览器，若下载速度慢建议手动下载后通过如下函数：
`set_chromium(exepath:str = None, userdatapath:str = None)`配置浏览器路径及浏览器缓存文件路径)

##使用:

```python
from piaomanga import PiaoManga,set_chromium,get_source_list

# 创建漫画
manga = PiaoManga(u'漫画名',u'作者名(options)')
#打印可选漫画源
source_list = get_source_list()
# 依据漫画源的id添加该源
manga.addsource('manhuaju')
# 搜索章节并返回章节列表
chapter_list = manga.get_chapter_list()
print(chapter_list)
# 预加载第一章图片(此处会自动打开chromium浏览器，最小化让其后台自动运行即可)
manga.load_chapter(chapter_list[0])
# 下载第一章到指定目录，可选参数下载完成后的回调函数
# 返回一个下载任务ID,任务创建失败返回None
taskid = manga.download_chapter(chapter_list[0],save_path=r'D:/manga/')

# 可定时查看下载进度
taskstatus = manga.get_download_status(taskid)
print(taskstatus)
```

