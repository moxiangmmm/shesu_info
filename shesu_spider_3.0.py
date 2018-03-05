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
from read_company import read_company1, read_company2
from item_dumpkey import Item_dump
import concurrent.futures
from damatuWeb import DamatuApi


# 使用多线程打码准确率不高，不建议使用

proxyHost = "http-dyn.abuyun.com"
proxyPort = "9020"

proxyUser = "H65403216IJKN42D"
proxyPass = "55697F9CCB86225E"

proxyMeta = "http://%(user)s:%(pass)s@%(host)s:%(port)s" % {
    "host": proxyHost,
    "port": proxyPort,
    "user": proxyUser,
    "pass": proxyPass,
}

proxies = {
    "http": proxyMeta,
    "https": proxyMeta,
}



def get_detail(html, captcha, headers, company):
    # 判断是否有查询结果,并获取案号id
    ss_list = []
    tr_list = html.xpath("//tbody//tr")
    # print(tr_list)
    if len(tr_list) > 1:
        print("*" * 20)
        for tr in tr_list:
            id = tr.xpath(".//td[@align='center']/a/@id")
            if len(id) > 0:
                ss_one = []
                id = id[0]
                # print(id)
                # 拼接详情页的链接
                # http://zhixing.court.gov.cn/search/newdetail?id=16900266&j_captcha=pzt8&captchaId=fda97538121240b38b0c73eeac144dbe&_=1515212716230
                time_id = int(time.time()) * 1000
                detail_url = "http://zhixing.court.gov.cn/search/newdetail?id={}&j_captcha={}&captchaId=fda97538121240b38b0c73eeac144dbe&_={}".format(id, captcha, time_id)
                # 发送请求
                try:
                    ret = requests.get(detail_url, headers=headers, timeout=60)
                except Exception as e:
                    with open("log/shesu_log.log", 'a') as f:
                        now = str(datetime.datetime.now())
                        f.write(now + ',' + company + ',' + str(e) + '\n')
                        continue
                print("查看++++++++++", ret.status_code)
                ret_json = ret.content.decode()
                # 将json 格式转换成python类型
                ret_dic = json.loads(ret_json)
                # 获取所需的字段 如果字典没有这个建会报异常
                try:
                    pname = ret_dic["pname"]
                except:
                    pname = "未获取到"
                try:
                    caseCode = ret_dic["caseCode"]  # 案号
                except:
                    caseCode = "未获取到"
                try:
                    caseCreateTime = ret_dic["caseCreateTime"]  # 立案时间
                except:
                    caseCreateTime = "未获取到"
                try:
                    partyCardNum = ret_dic["partyCardNum"]  # 身份证号码
                except:
                    partyCardNum = "未获取到"
                try:
                    execCourtName = ret_dic["execCourtName"]  # 执行法院
                except:
                    execCourtName = "未获取到"
                try:
                    execMoney = ret_dic["execMoney"]  # 执行标的
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


# 请求验证码
@retry(stop_max_attempt_number=5, stop_max_delay=30000)
def _search_company(company, captcha_url):
    u = Rand_ua()
    ua = u.rand_chose()
    headers = {'User-Agent': ua}
    try:
        captcha_response = requests.get(captcha_url, headers=headers, timeout=60)
        # captcha = indetify(captcha_response.content)
        dmt = DamatuApi("469819183", "54188")
        captcha = dmt.decode(captcha_response.content, 42)

    except Exception as e:
        print(e)
        with open("log/shesu_log.log", 'a') as f:
            now = str(datetime.datetime.now())
            f.write(now + ',' + company + ',' + str(e) + '\n')
        return "验证码获取失败！"

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
    resp = requests.post('http://zhixing.court.gov.cn/search/newsearch', data=post_data, headers=headers,timeout=60)
    print("查询++++++++++", resp.status_code)
    content = resp.content.decode()
    html = etree.HTML(content)
    # 判断验证码是否错误
    text = html.xpath("//title/text()")[0]
    print("*" * 20, text)
    # 处理验证码，超过5次忽略，计入日志
    assert (text != "验证码出现错误，请重新输入！" and resp.status_code == 200)
    # 请求详情页
    ss_list = get_detail(html, captcha, headers,company)

    return ss_list

def search_company(company, captcha_url):
    try:
        ss_list = _search_company(company, captcha_url)

    except Exception as e:
        print(e)
        with open("log/shesu_log.log", 'a') as f:
            now = str(datetime.datetime.now())
            f.write(now + ',' + company + ',' + str(e) + '\n')
            ss_list = ["未获取到信息"]
        with open("log/except_company.csv", 'a') as f:
            f.write(company + '\n')

    return ss_list

def run(company):
    # 给验证码的url拼接16位随机数
    # i = Item_dump(company)
    # ret = i.item_dump()
    # if not ret:
    item = {}
    item["company"] = company
    item["type"] = None
    captcha_url = 'http://zhixing.court.gov.cn/search/captcha.do?captchaId=fda97538121240b38b0c73eeac144dbe&random={}'.format(random.randint(999999999999999, 9999999999999999) / 10000000000000000)
    ss_list = search_company(company, captcha_url)
    item["涉诉信息"] = ss_list
    print(item)

def run_text(path):
    # 给验证码的url拼接16位随机数
    futures = set()
    company_list = read_company2(path)
    with concurrent.futures.ProcessPoolExecutor(2) as executor:
        for company in company_list:
            future = executor.submit(run, company)
            futures.add(future)
    try:
        for future in concurrent.futures.as_completed(
                futures):  # 返回一个迭代器，yield那些完成的futures对象。fs里面有重复的也只可能返回一次。任何futures在调用as_completed()调用之前完成首先被yield。
            err = future.exception()
            if err is not None:
                raise err
    except KeyboardInterrupt:
        print("stopped by hand")

def text_dama():
    u = Rand_ua()
    ua = u.rand_chose()
    headers = {'User-Agent': ua}
    captcha_url = 'http://zhixing.court.gov.cn/search/captcha.do?captchaId=fda97538121240b38b0c73eeac144dbe&random={}'.format(random.randint(999999999999999, 9999999999999999) / 10000000000000000)
    response = requests.get(captcha_url,headers=headers)
    print(type(response.content))
    dmt = DamatuApi("469819183","54188")
    ret = dmt.decode(response.content,42)
    print(ret)


# 获取验证码之后对接打码平台

# 携带验证码搜索公司信息

# 处理返回信息



if __name__ == '__main__':
    # path = sys.argv[1]
    run_text('/home/python/Desktop/company/sz_total.csv')
    # text_dama()