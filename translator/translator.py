from abc import ABC, abstractmethod
import time
from translator.intermediate_language import IntermediateLanguage
from translator.return_enum import ResultEnum
from config import TIMEOUT
import multiprocessing

class _TimeoutError(Exception):
    pass

def run_with_timeout(func, args=(), kwargs={}, timeout=10):
    def target(queue, *args, **kwargs):
        result = func(*args, **kwargs)
        queue.put(result)

    queue = multiprocessing.Queue()
    process = multiprocessing.Process(
        target=target,
        args=(queue, *args),
        kwargs=kwargs
    )
    process.start()
    process.join(timeout)

    if process.is_alive():
        process.terminate()
        process.join()
        raise _TimeoutError()

    if not queue.empty():
        return queue.get()
    else:
        raise _TimeoutError()

class Translator(ABC):
    def __init__(self, intermediate_language: IntermediateLanguage) -> None:
        self.intermediate_language = intermediate_language

    @abstractmethod
    def to_file_string(self) -> str:
        pass

    def write_to_file(self, file_path: str):
        with open(file_path, "w") as file:
            file.write(self.to_file_string())

    def solve(self):
        start_time = time.time()
        try:
            res = run_with_timeout(self._solve, timeout=TIMEOUT)

        except _TimeoutError:
            end_time = time.time()
            execution_time = end_time - start_time
            return (ResultEnum.Timeout, None), execution_time
        except Exception as e:
            print(e)
            end_time = time.time()
            execution_time = end_time - start_time
            return (ResultEnum.Error, None), execution_time

        end_time = time.time()
        execution_time = end_time - start_time
        return res, execution_time

    def _solve(self):
        pass
