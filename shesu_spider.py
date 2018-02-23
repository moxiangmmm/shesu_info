# coding=utf-8
# coding=utf-8
import requests
from lxml import etree
from dama import indetify
import time
import random
import datetime
import json
from retrying import retry
from rand_ua import Rand_ua
import pymongo
import sys
from read_company import read_company1,read_company2
from item_dumpkey import Item_dump
# 读取客户名单中的公司名称
# for循环遍历
# 判断验证码是否错误，如错重新请求
# 判断是查询结果是否有内容，如有请求详情页信息
# 获取案号id
# 拼接参数，发送GET请求
# 下载源代码保存到本地
# 用retry装饰函数，如果验证码错误就抛异常，最多尝试5次

# 根据传过来的参数发送请求检索是否有诉信息
# 如果没有则返回一个空列表
# 如果有则遍历每一行信息，并把字段添加到一个列表中
# 再把各个列表添加到一个列表中返回

proxyHost = "http-dyn.abuyun.com"
proxyPort = "9020"


proxyUser = "H65403216IJKN42D"
proxyPass = "55697F9CCB86225E"

proxyMeta = "http://%(user)s:%(pass)s@%(host)s:%(port)s" % {
  "host" : proxyHost,
  "port" : proxyPort,
  "user" : proxyUser,
  "pass" : proxyPass,
}

proxies = {
    "http"  : proxyMeta,
    "https" : proxyMeta,
}


class ZhixingSpider:

    def __init__(self, path, text_list=None, type=None,proxies=None):
        self.proxies = proxies
        self.u = Rand_ua()
        self.client = pymongo.MongoClient(host='127.0.0.1', port=27017)
        self.conn = self.client["qg_ss"]['shesu_info']
        self.type = type  # 公司类型
        self.text_list = text_list  # 测试列表
        self.path = path  # 公司名单路径
        self.captcha_url = 'http://zhixing.court.gov.cn/search/captcha.do?captchaId=fda97538121240b38b0c73eeac144dbe&random={}'


    @retry(stop_max_attempt_number=5,stop_max_delay=60000)
    def _search_company(self, company, captcha_url):
        ua = self.u.rand_chose()
        headers = {'User-Agent': ua}
        try:
            captcha_response = requests.get(captcha_url, headers=headers, timeout=60, proxies=self.proxies)
            captcha = indetify(captcha_response.content)
        except Exception as e:
            print(e)
            with open("log/shesu_log.log", 'a') as f:
                now = str(datetime.datetime.now())
                f.write(now+','+company+','+str(e)+'\n')
            return  "验证码获取失败！"

        post_data = {
            "searchCourtName": "全国法院（包含地方各级法院）",
            "selectCourtId": 1,
            "selectCourtArrange": 1,
            "pname": company,
            "cardNum": "",
            "j_captcha": captcha,
            "captchaId": "fda97538121240b38b0c73eeac144dbe"
        }
        # print(post_data)
        resp = requests.post('http://zhixing.court.gov.cn/search/newsearch', data=post_data, headers=headers, timeout=60,proxies=self.proxies)
        print("查询++++++++++", resp.status_code)
        content = resp.content.decode()
        html = etree.HTML(content)
        # 判断验证码是否错误
        text = html.xpath("//title/text()")[0]
        print("*"*20, text)
        # 处理验证码，超过5次忽略，计入日志
        assert (text != "验证码出现错误，请重新输入！" and resp.status_code == 200)
        # 请求详情页
        ss_list = self.get_detail(html, captcha, headers)

        return ss_list


    def search_company(self, company, captcha_url):
        try:
            ss_list = self._search_company(company, captcha_url)

        except Exception as e:
            print(e)
            with open("log/shesu_log.log", 'a') as f:
                now = str(datetime.datetime.now())
                f.write(now+','+company+','+str(e)+'\n')
                ss_list = ["未获取到信息"]
            with open("log/except_company.csv", 'a') as f:
                f.write(company+'\n')

        return ss_list



    def get_detail(self, html, captcha, headers):
        # 判断是否有查询结果,并获取案号id
        ss_list = []
        tr_list = html.xpath("//tbody//tr")
        # print(tr_list)
        if len(tr_list)>1:
            print("*" * 20)
            for tr in tr_list:
                id = tr.xpath(".//td[@align='center']/a/@id")
                if len(id)>0:
                    ss_one = []
                    id = id[0]
                    # print(id)
                    # 拼接详情页的链接
                    # http://zhixing.court.gov.cn/search/newdetail?id=16900266&j_captcha=pzt8&captchaId=fda97538121240b38b0c73eeac144dbe&_=1515212716230
                    time_id = int(time.time())*1000
                    detail_url = "http://zhixing.court.gov.cn/search/newdetail?id={}&j_captcha={}&captchaId=fda97538121240b38b0c73eeac144dbe&_={}".format(id, captcha, time_id)
                    # 发送请求
                    try:
                        ret = requests.get(detail_url, headers=headers, timeout=60,proxies=self.proxies)
                    except Exception as e:
                        with open("log/shesu_log.log", 'a') as f:
                            now = str(datetime.datetime.now())
                            f.write(now + ',' + company + ',' + str(e) + '\n')
                            continue
                    print("查看++++++++++",ret.status_code)
                    ret_json = ret.content.decode()
                    # 将json 格式转换成python类型
                    ret_dic = json.loads(ret_json)
                    # 获取所需的字段 如果字典没有这个建会报异常
                    try:
                        pname = ret_dic["pname"]
                    except:
                        pname = "未获取到"
                    try:
                        caseCode = ret_dic["caseCode"]# 案号
                    except:
                        caseCode = "未获取到"
                    try:
                        caseCreateTime = ret_dic["caseCreateTime"] # 立案时间
                    except:
                        caseCreateTime = "未获取到"
                    try:
                        partyCardNum = ret_dic["partyCardNum"]# 身份证号码
                    except:
                        partyCardNum = "未获取到"
                    try:
                        execCourtName = ret_dic["execCourtName"]# 执行法院
                    except:
                        execCourtName = "未获取到"
                    try:
                        execMoney = ret_dic["execMoney"]# 执行标的
                    except:
                        execMoney = "未获取到"
                    ss_one.append(pname)
                    ss_one.append(caseCode)
                    ss_one.append(caseCreateTime)
                    ss_one.append(partyCardNum)
                    ss_one.append(execCourtName)
                    ss_one.append(execMoney)
                    ss_list.append(ss_one)
                    time.sleep(2)

        return ss_list

    def save_mongodb(self, item):
        self.conn.insert_one(dict(item))
        print("保存成功！")

    def run(self):
        # 给验证码的url拼接16位随机数
        company_list = read_company2(self.path)

        for company in company_list:
            i = Item_dump(company)
            ret = i.item_dump()
            if not ret:
                item = {}
                item["company"] = company
                item["type"] = self.type
                captcha_url = self.captcha_url.format(random.randint(999999999999999,9999999999999999)/10000000000000000)
                ss_list = self.search_company(company, captcha_url)
                item["涉诉信息"] = ss_list
                self.save_mongodb(item)
                print(item)
    # 测试模式
    def run_text(self):
        # 给验证码的url拼接16位随机数
        company_list = read_company2(self.path)
        for company in company_list:
            item = {}
            item["company"] = company
            item["type"] = self.type
            captcha_url = self.captcha_url.format(
                random.randint(999999999999999, 9999999999999999) / 10000000000000000)
            ss_list = self.search_company(company, captcha_url)
            item["涉诉信息"] = ss_list
            print(item)





if __name__ == '__main__':
    path = sys.argv[1]
    company = "广西五鸿建设集团有限公司"
    # company = ZhixingSpider(path=path, proxies=proxies)
    company = ZhixingSpider(path=path)

    company.run_text()