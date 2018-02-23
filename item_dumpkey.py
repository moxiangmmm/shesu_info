# coding=utf-8
import redis
import hashlib

class Item_dump():

    def __init__(self, company):
        self.r = redis.Redis(host='127.0.0.1', port=6379, db=5) # 连接数据库
        self.item_key = "shesu_dump"
        self.company = company

    def item_dump(self):
        f = hashlib.sha1()
        f.update(self.company.encode())
        fingerprint = f.hexdigest()
        added = self.r.sadd(self.item_key, fingerprint)
        # 保存成功返回false， 保存失败返回True
        return added == 0


if __name__ == '__main__':
    item = {"_id":2}
    i = Item_dump(item)
    ret = i.item_dump()
    print(ret)




