__all__ = ['DownloadTaskStatus','Downloader']
import os
from time import time, localtime, asctime
import asyncio
import aiohttp
import aiofiles
import random
from typing import Dict, List, Callable, Mapping
from .MyAsycioFrame import AsycioPool
from .Header import get_user_agent_pc as Hd
from .Header import get_user_agent_phone as mHd
import copy
from .Header import get_user_agent_phone as HeaderMobile
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - '
                                               '%(levelname)s - %(module)s -'
                                               ' %(funcName)s - %(threadName)s - %(message)s')
logger = logging.getLogger(__name__)


def generate_random_str(randomlength=16):
    """
  生成一个指定长度的随机字符串
  """
    random_str = ''
    base_str = 'ABCDEFGHIGKLMNOPQRSTUVWXYZabcdefghigklmnopqrstuvwxyz0123456789'
    length = len(base_str) - 1
    for i in range(randomlength):
        random_str += base_str[random.randint(0, length)]
    return random_str


# 外部引出用
class DownloadTaskStatus:
    def __init__(self, addr: str = "", name: str = "", path: str = "", args: Dict = None):
        self.addr = addr
        if not path:
            path = os.getcwd()
        self.path = path
        if not name:
            name = addr
        self.name = name

        self.args = args

        assert self.addr is not None and self.addr != ""

        self.retry_time = 0
        self.start_time = "0"
        self.end_time = "0"
        self.tasks_id = ""
        self.is_failed = False
        self.progress = 0.0

    def __str__(self):
        s = "[task cell] ( " + "name: " + self.name + " path: " + self.path + \
            " progress: " + str(self.progress) + " task_id: " + self.tasks_id + \
            " failed: " + str(self.is_failed) + " start: " + str(self.start_time) + \
            " finish: " + str(self.end_time) +  " url: " + str(self.addr) + ")\n"
        return s


class DownloadTask:
    MAX_PERMIT_RETRY_TIMES = 3

    def __init__(self, task: DownloadTaskStatus, args: Dict = None):
        self.addr = task.addr
        if not task.path:
            self.path = os.getcwd()
        else:
            self.path = task.path
        if not task.name:
            self.name = task.addr
        else:
            self.name = task.name

        if task.args:
            self.args = args
        else:
            self.args = task.args

        assert self.addr is not None and self.addr != ""

        self._retry_time = 0
        self.start_time = None
        self.end_time = None
        self._tasks_id = None
        self.is_failed = False
        self.progress = 0.0

    def get_status(self) -> DownloadTaskStatus:
        s = DownloadTaskStatus(self.addr, self.name, self.path)
        s.start_time = asctime(localtime(self.start_time))
        if not s.start_time:
            s.start_time = "0"
        s.end_time = asctime(localtime(self.end_time))
        if not s.end_time:
            s.end_time = "0"
        s.retry_time = self._retry_time
        s.tasks_id = self.tasks_id
        s.progress = self.progress
        s.is_failed = self.is_failed
        return s

    def belong_to(self, tasks_id: str):
        self._tasks_id = tasks_id

    @property
    def tasks_id(self):
        return self._tasks_id

    def retry(self) -> bool:
        self._retry_time += 1
        try:
            return self._retry_time < self.args["max_retry_times"]
        except KeyError:
            return self._retry_time < self.MAX_PERMIT_RETRY_TIMES

    @property
    def cur_retry_time(self):
        return self._retry_time


class Downloader:
    MAX_TASK_BUNDLE_NUM = 1

    def __init__(self, ev_pool: AsycioPool, name: str = "", args: Dict = None):

        self._ev_pool = ev_pool
        self.name = name
        self.args = args
        self._task_pool = {}  # task_cell
        self._bundle_pool = {}  # task_bundle
        self._bundle_queue = []

    @property
    def headers(self):
        try:
            return self.args["headers"]
        except:
            return Hd()

    async def _down_cell(self, task: DownloadTask, bytePerLoop: int = 1024, maxwaittime: int = 100,
                         successCallback: Callable = None) -> bool:
        task.start_time = time()
        print(task.get_status().__str__())
        header = {'User-Agent': self.headers}
        async with aiohttp.ClientSession() as session:
            async with session.get(task.addr, headers=header) as resp:
            #async with session.get(task.addr) as resp:
                try:
                    totallens = int(resp.headers['content-length'])
                except KeyError:
                    logger.error("not found content-length in headers ,url: " + resp.url.name)
                    totallens = float("inf")
                if resp.status == 200:
                    f = await aiofiles.open('{0}'.format(task.path), mode='wb')
                    curlens = 0
                    st_time = time()
                    while time() - st_time < maxwaittime:
                        chunk = await resp.content.read(bytePerLoop)
                        if not chunk:
                            await f.close()
                            task.progress = 1.0
                            break
                        await f.write(chunk)
                        curlens += bytePerLoop
                        if curlens <= totallens:
                            task.progress = float(curlens / totallens)

                    logger.info("子任务完成: " + task.get_status().__str__() + "\n")
        task.end_time = time()
        # 最后一个任务执行完成
        if self._get_tasks_is_done(task.tasks_id) and successCallback:
            try:
                logger.info("tasks fined call successCallback ")
                successCallback({"tasks": list(map(lambda x: x.get_status(), self._bundle_pool[task.tasks_id]))})
            except:
                logger.error("call successCallback failed!")

            #清除队列
            try:
                self._bundle_queue.remove(task.tasks_id)
            except ValueError:
                logger.error(u"taskID {0} 不在 bundle_queue队列中\n".format(task.tasks_id))

            try:
                todel = self._bundle_pool.pop(task.tasks_id)
                del todel
            except KeyError:
                logger.error(u"taskID {0} 不在 bundle_pool队列中\n".format(task.tasks_id))

        if task.progress >= 1.0:
            return True
        else:
            if task.retry():  # 重试
                logger.info("task cell :{0} is failed, retry times {1}".format(task, task.cur_retry_time))
                return await self._down_cell(task, bytePerLoop, maxwaittime, successCallback)

            task.is_failed = True
            return False

    def _clear_bundle(self):
        try:
            tasksid = self._bundle_queue.pop(0)
            try:
                tasklist = self._bundle_pool.pop(tasksid)
            except KeyError:
                logger.info("task :{0} has de queue".format(taskid))
                return
            for task in tasklist:
                try:
                    t = self._task_pool.pop(task.addr)
                    del t
                except KeyError:
                    pass
            del tasklist
        except IndexError:
            pass

    def _get_tasks_is_done(self, taskid: str, ) -> bool:
        tasks = self._bundle_pool.get(taskid)
        if not tasks:
            logger.error("task ID :" + taskid + " not found !")
            return True

        ret = True
        for task in tasks:
            if task.progress < 1 and not task.is_failed:
                ret = False
                break
        return ret

    def download(self, tasks: DownloadTaskStatus or List[DownloadTaskStatus], successCallback: Callable = None,
                 failedCallback: Callable = None ) -> str:
        if type(tasks) is not list:
            tasks = [tasks]

        # 启动eventloop
        self._ev_pool.start()

        # 以下载任务的url作为key
        taskid = generate_random_str()

        if len(self._bundle_queue) >= self.MAX_TASK_BUNDLE_NUM:
            self._clear_bundle()
        self._bundle_pool[taskid] = []
        self._bundle_queue.append(taskid)
        for task in tasks:
            if self._task_pool.get(task.addr):  # 任务已存在，删除
                rb = self._task_pool.pop(task.addr)
                del rb
            self._task_pool[task.addr] = DownloadTask(task)
            self._task_pool[task.addr].belong_to(taskid)
            self._ev_pool.addtask(self._down_cell, self._task_pool[task.addr], successCallback=successCallback)
            self._bundle_pool[taskid].append(self._task_pool[task.addr])

        async def tasks_monitor(tasks: List[DownloadTask], maxwaittime: int = 9999):
            if not tasks:
                return
            while True:
                await asyncio.sleep(0.5)

        return taskid

    def get_progress(self, taskId: str) -> List[DownloadTaskStatus] or None:
        try:
            return list(map(lambda x: x.get_status(), self._bundle_pool.get(taskId)))
        except KeyError:
            logger.error(u"任务ID: {0} 找不到，请确认是否正确\n", format(taskId))


if __name__ == "__main__":
    urls = ['https://res.xiaoqinre.com/images/comic/614/1227808/1581445473kobThvokJBIcXJrB.jpg',
            'https://res.xiaoqinre.com/images/comic/614/1227808/1581445472A9QOq7_OEK6alY6A.jpg',
            'https://res.xiaoqinre.com/images/comic/614/1227808/1581445471Z1h430QU0VrRJJDr.jpg',
            'https://res.xiaoqinre.com/images/comic/614/1227808/1581445470pc4YUTYCikSnMtSs.jpg',
            'https://res.xiaoqinre.com/images/comic/614/1227808/1581445469yz1flZNiHxG8p6iK.jpg',
            'https://res.xiaoqinre.com/images/comic/614/1227808/15814454685pGUsp92Y2HoMNdD.jpg',
            'https://res.xiaoqinre.com/images/comic/614/1227808/1581445467nvnyF8jWO_LGSefS.jpg',
            'https://res.xiaoqinre.com/images/comic/614/1227808/1581445466-FnmYpY5rihfqNgt.jpg',
            'https://res.xiaoqinre.com/images/comic/614/1227808/15814454654iilxzLXxE65UkK9.jpg',
            'https://res.xiaoqinre.com/images/comic/614/1227808/1581445464-dzOefWlLy-jy-_a.jpg',
            'https://res.xiaoqinre.com/images/comic/614/1227808/1581445463F1x-P8EZnatUicUu.jpg',
            'https://res.xiaoqinre.com/images/comic/614/1227808/1581445462TZIYIVUxH0p4_gbY.jpg',
            'https://res.xiaoqinre.com/images/comic/614/1227808/1581445461L7UtnV45b15CCy4C.jpg',
            'https://res.xiaoqinre.com/images/comic/614/1227808/1581445460H93eUnEJavrpyRvc.jpg',
            'https://res.xiaoqinre.com/images/comic/614/1227808/15814454591YtSrhm4v72wIPqh.jpg',
            'https://res.xiaoqinre.com/images/comic/614/1227808/1581445458nVr9fHCtmaduFLJ2.jpg',
            'https://res.xiaoqinre.com/images/comic/614/1227808/1581445457z4hqE6n76wYGl2sp.jpg',
            'https://res.xiaoqinre.com/images/comic/614/1227808/1581445456xW7RW1ZgYMHfrZYj.jpg',
            'https://res.xiaoqinre.com/images/comic/614/1227808/1581445455kLoVQXMC9YkWV5Pd.jpg',
            'https://res.xiaoqinre.com/images/comic/614/1227808/1581445454GM4tztlK-gaTfoJi.jpg']

    rootpath = r"D:\MY_Collects\manga\租借女友"
    ts = []
    for i, url in enumerate(urls):
        name = u"第 {0} 话".format(i + 1)
        path = rootpath + os.path.sep + str(i + 1) + '.jpg'

        ts.append(DownloadTaskStatus(url, name, path))

    ev = MyAsycioFrame.AsycioPool()

    d = Downloader(ev)
    taskid = d.download(ts)
    while True:
        status = d.get_progress(taskid)
        for item in status:
            print(item)
        from time import sleep

        sleep(1)
