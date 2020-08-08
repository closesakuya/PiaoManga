__all__=['UrlsTool']
from .MyAsycioFrame import AsycioPool
from .DownLoader import *
from time import sleep, time
import os
from functools import partial
import asyncio
import threading
import logging
import aiohttp
from pyppeteer import launch
from pyppeteer.network_manager import Request, Response
import pyppeteer

import requests
from typing import List, Dict, Set, Callable
from .Header import get_user_agent_pc as Header
from .Header import get_user_agent_phone as HeaderMobile

# chromiun浏览器位置

#Chromium_exe_path = r"D:\MY_TOOL\chrome-win\chrome-win\chrome.exe"
Chromium_exe_path = None
#Chromium_user_Data_Dir = r"D:\MY_TOOL\chrome-win\chrome-win\browsertemp"
Chromium_user_Data_Dir = None
Chromium_args = {
    "headless": False,
    'handleSIGINT': False,
    'handleSIGTERM': False,
    # 'handleSIGHUP': False,
    #'executablePath': Chromium_exe_path,
    #'userDataDir': Chromium_user_Data_Dir,  # 用户缓存路径，不设置close时会报错?
    "args": [
        "--start-maximized",
        "--no-sandbox",
        "--disable-infobars",
        "--ignore-certificate-errors",
        "--log-level=3",
        "--enable-extensions",
        "--window-size=1920,1080",
        "--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.97 Safari/537.36",
    ],
}
# 将webdriver的属性值设为false
Chromium_js1 = """
    () =>{
        Object.defineProperties(navigator,{
            webdriver:{
            get: () => false
            }
        })
    }
"""
# 读取 webdriver属性值，输出为false
Chromium_js2 = '''() => {
    alert (
        window.navigator.webdriver
    )
}'''

REQ_FILTER_LIST = ['media', 'image', 'stylesheet', 'xhr', 'eventsource', 'websocket']
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - '
                                               '%(levelname)s - %(module)s -'
                                               ' %(funcName)s - %(threadName)s - %(message)s')
logger = logging.getLogger(__name__)


class UrlsTool(AsycioPool):
    def __init__(self):
        super().__init__()
        self._header = None
        self._cookies = {'cookies_are': 0}
        self._genheader()

        self.browser = None
        # 使用该锁会报错got Future <Future pending> attached to a different loop
        # self.browser_lock = asyncio.Lock()
        # 代替使用标志 有线程不同步隐患
        self.is_open_browser = False

        self.SeesionNum = 0

    @staticmethod
    def set_chromium_path( exe_path:str = None, temp_path:str = None)->bool:
        import os
        global Chromium_exe_path
        global Chromium_user_Data_Dir
        global Chromium_args
        if  not exe_path:
            exe_path = Chromium_exe_path
        if exe_path:
            if not os.path.exists( exe_path ):
                logger.error(" chrome.exe 路径错误,路径无效：" + exe_path + '\n')
            else:
                Chromium_exe_path = exe_path
                Chromium_args['executablePath'] = exe_path

        done = False
        if temp_path:
            if os.path.exists(temp_path):
                done = True
            else:
                try:
                    os.makedirs(temp_path)
                    logger.info(" 创建用户缓存目录：" + temp_path + '\n')
                    done = True
                except:
                    done = False

        if done:
            Chromium_user_Data_Dir = temp_path
            Chromium_args['userDataDir'] = temp_path
        else:
            try:
                temp_path = os.path.split(Chromium_exe_path)[0] + "user_temp"
                os.makedirs(temp_path)
                logger.info(u" 创建用户缓存目录在chrome.exe同一路径下" + temp_path + '\n')
                Chromium_user_Data_Dir = temp_path
                Chromium_args['userDataDir'] = temp_path
            except FileExistsError:
                Chromium_user_Data_Dir = temp_path
                Chromium_args['userDataDir'] = temp_path
            except:
                logger.error(u" 创建用户缓存目录在: {0} 失败！\n".format(temp_path))
                return False


        return True

    def _genheader(self, contenttype: str = "text/html; charset=utf-8", header: str = None, mobile: bool = False):

        if self._header:
            del self._header
        self._header = {'content-type': contenttype}
        if not header:
            if mobile:
                self._header['User-Agent'] = HeaderMobile()
            else:
                self._header['User-Agent'] = Header()
        else:
            self._header['User-Agent'] = header

    def asynurlget(self, url: str, maxwork: int = 4, prestart: int = 2, maxwaittime: float = 999999,
                   prewaittime: float = 0.5) -> str:
        assert (maxwork >= prestart)
        assert (maxwaittime >= prewaittime)
        ret = ""
        ok = False

        def callback(backtxt: str):
            nonlocal ret
            ret = backtxt
            nonlocal ok
            ok = True

        async def task():
            try:
                # async with aiohttp.ClientSession(cookies = self._cookies) as session:
                async with aiohttp.ClientSession() as session:  # cookies设置错误
                    self._genheader()
                    async with session.get(url, headers=self._header) as r:
                        return await r.text(encoding='utf-8')
            except asyncio.CancelledError:
                logger.warning('task cancel')
                raise

        tasks = []
        for i in range(prestart):
            tasks.append(self.addtask(task, callback=callback))
        maxwork -= prestart
        st = time()
        mstart = False
        while True:
            if ok:
                break
            if (time() - st > prewaittime) and not mstart:
                mstart = True
                for i in range(maxwork):
                    tasks.append(self.addtask(task, callback=callback))
            if time() - st > maxwaittime:
                logger.warning("请求超时")
                break
            sleep(0.02)
        if ok:
            for item in tasks:
                pass  # item.cancel()

        return ret

    def asynurlget_dynamic(self, urls: str or List[str],
                           maxworker: int = 1,
                           maxwaittime: float = 60,
                           retrytimes: int = 0,
                           filterpattern: str = None,
                           filterlst: List[str] = None
                           ) -> str or Dict[str:str]:
        if type(urls) is str:
            urls = [urls]
        if not filterlst:
            filterlst = REQ_FILTER_LIST
        rets = {item: str() for item in urls}
        oks = {item: False for item in urls}
        # browser = None
        is_open_browser = False
        loop = asyncio.get_event_loop()

        async def openbrowser(reset: bool = False):
            # nonlocal browser
            # nonlocal is_open_browser

            if (not self.browser) or (reset):
                # 锁机制,同一时间只有一个task能创建浏览器
                if reset and not self.is_open_browser:
                    self.browser = None
                while not self.browser:
                    if not self.is_open_browser:
                        self.is_open_browser = True
                        if not self.browser:
                            self.browser = await launch(Chromium_args)
                        self.is_open_browser = False
                    else:
                        await asyncio.sleep(0.1)

        def callback(backtxt: str, url: str):
            nonlocal rets
            # if not filterpattern:
            rets[url] = backtxt
            nonlocal oks
            if backtxt:
                oks[url] = True

        async def dynamictask(url):

            async def response_filter(response: Response):
                pass
                # txt = await response.text()
                # print(await response.text())

            cancel = False

            async def request_filter(request: Request):
                nonlocal cancel

                if filterpattern and (filterpattern in request.url):
                    logger.info("找到过滤请求 " + url + ":" + request.url)
                    cancel = True
                    await request.continue_()
                    # await request.continue_({"url": "http:www.baidu.com"})
                    # nonlocal rets
                    # rets[url] = request.url

                    # callback(txt, url = url)
                    # raise pyppeteer.errors.TimeoutError
                elif request.resourceType in filterlst:
                    await request.abort()
                else:
                    if cancel:
                        await request.abort()
                    else:
                        await request.continue_()

            # nonlocal browser
            try:
                await openbrowser()
                # browser = await launch(Chromium_args)
                cnt = 0
                page = None
                while cnt < 3:
                    try:
                        page = await self.browser.newPage()
                        break
                    except:  # page关闭,重开
                        await openbrowser(reset=True)
                        cnt += 1
                await page.setUserAgent(HeaderMobile())
                await page.evaluateOnNewDocument(Chromium_js1)
                page.setDefaultNavigationTimeout(maxwaittime * 1000)
                # if filterpattern:
                await page.setRequestInterception(True)
                page.on("request", request_filter)
                page.on("response", response_filter)
                try:
                    await page.goto(url, timeout=1000 * maxwaittime)
                    # await page.evaluate(Chromium_js1) #去除webdriver字段，有报错
                    txt = await page.content()
                    await page.close()
                    self.SeesionNum = len( await self.browser.pages())
                    return txt
                except pyppeteer.errors.TimeoutError:
                    logger.error("time out")
                    return None
                # await page.waitForXPath("//span[@id='k_total']/img/@src")
                # except pyppeteer.errors.TimeoutError:
            except asyncio.CancelledError:
                logger.warning('task cancel')
                raise

        tasks = {}
        for u in urls:
            tasks.update({u: []})
            for i in range(maxworker):
                tasks[u].append(self.addtask(dynamictask, u, callback=partial(callback, url=u)))
                # future = loop.create_task(dynamictask())
                # future.add_done_callback(lambda future: callback(future.result()))
                # loop.run_until_complete(future)
        st = time()
        while True:
            sets = set(oks.values())
            if True in sets and len(sets) == 1:
                logger.info("任务完成")
                break
            if time() - st > maxwaittime:
                logger.warning("请求超时")
                retrytimes -= 1
                if retrytimes < 0:
                    break
                st = time()
                for u, b in oks.items():
                    if not b:
                        tasks[u].append(self.addtask(dynamictask, u, callback=partial(callback, url=u)))
            sleep(0.1)

        # self.addtask(self.browser.close())
        # 只能在主线程中关闭
         #for item in self.browser.pages():


         #   loop.run_until_complete(item.close())

        if self.SeesionNum > 20:  #窗口过多才关闭
            loop.run_until_complete(self.browser.close())
            self.SeesionNum = 0
            self.browser = None

        return [rets.get(i, None) for i in urls]

    def urlget(self, url: str, maxwaittiem: int = 3) -> str:
        maxcnt = maxwaittiem
        while maxwaittiem > 0:
            try:
                ret = requests.get(url, headers=self._header, timeout=3)
                ret.encoding = 'utf-8'
                return ret.text
            except requests.exceptions.RequestException as e:
                logger.warning("请求超时 尝试第 " + str(maxcnt - maxwaittiem + 1) + " 次重连")
                self._genheader()

            maxwaittiem -= 1

        return ""
