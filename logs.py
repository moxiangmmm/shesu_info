# coding=utf-8
import datetime

def Log(path, e):
    with open(path, 'a') as f:
        now = str(datetime.datetime.now())
        f.write(now + ',' + str(e) + ',' + ',' + '\n')

if __name__ == '__main__':
    pass