__all__ = ['AsycioPool']

import attr
import asyncio
from threading import Thread
import concurrent.futures as futures
from concurrent.futures import ThreadPoolExecutor


# 解决asyncio嵌套报错问题，但是开启后pyppeteer不能用
# import nest_asyncio
# nest_asyncio.apply()

@attr.s
class AsycioPool:
    __MAX_WORKER = 10

    loop_thread = attr.ib(type=Thread, default=None)
    loop = attr.ib(default=None)

    __is_start = attr.ib(default=False)
    taskpool = attr.ib(default={})
    executor = attr.ib(type=ThreadPoolExecutor, default=
    ThreadPoolExecutor(max_workers=__MAX_WORKER))

    def start(self):

        if self.__is_start:
            return
        if not self.loop:
            self.loop = asyncio.new_event_loop()

        if not self.loop_thread:
            def loop_run(loop):
                asyncio.set_event_loop(loop)
                loop.run_forever()

            self.loop_thread = Thread(target=loop_run, args=(self.loop,))

        self.__is_start = True
        self.loop_thread.setDaemon(True)
        self.loop_thread.start()

    def _addtask(self, task, *wd, **kw):

        return self.loop.run_in_executor(self.executor, task, *wd, **kw)

    def _addcoro(self, task, *wd, **kw):

        if r"callback" in kw:
            callback = kw.pop(r"callback")
        else:
            callback = None

        future = asyncio.run_coroutine_threadsafe(task(*wd, **kw), self.loop)

        if callback:
            future.add_done_callback(lambda future: callback(future.result()))

        return future

    def addtask(self, task, *wd, **kw):
        if asyncio.iscoroutinefunction(task):
            return self._addcoro(task, *wd, **kw)
        else:
            return self._addtask(task, *wd, **kw)
