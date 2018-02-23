# coding=utf-8
import concurrent.futures
import time
import random
import multiprocessing

# multiprocessing.cpu_count() 返回系统当前有多少个cpu
def read(q):
    print('Get %s from queue.' % q)
    time.sleep(random.random())


def main():
    futures = set()
    with concurrent.futures.ThreadPoolExecutor(2) as executor:
        for q in (chr(ord('A') + i) for i in range(26)):
            future = executor.submit(read, q)
            futures.add(future)
    try:
        for future in concurrent.futures.as_completed(futures):# 返回一个迭代器，yield那些完成的futures对象。fs里面有重复的也只可能返回一次。任何futures在调用as_completed()调用之前完成首先被yield。
            err = future.exception()
            if err is not None:
                raise err
    except KeyboardInterrupt:
        print("stopped by hand")


if __name__ == '__main__':
    main()