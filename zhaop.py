import requests
import sqlite3
import json
from  lxml import etree
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
def send_jobs_2_email(dic):

    import smtplib
    from email.mime.text import MIMEText
    # 设置服务器所需信息
    # 邮箱服务器地址
    mail_host = ''
    # 用户名
    mail_user = ''
    # 密码(部分邮箱为授权码)
    mail_pass = ''
    # 邮件发送方邮箱地址
    sender = ''
    # 邮件接受方邮箱地址，注意需要[]包裹，这意味着你可以写多个邮件地址群发
    receivers = ['']

    # 设置email信息
    # 邮件内容设置

    if dic:
        with open('zhaopin.html', 'rb') as f:
            html = f.read().decode('utf-8')
        str_dic = ''
        for k, v in dic.items():
            str_dic += '''<div>
                    <h2><a href="%s">%s</a></h2>
                               <ul>''' % (v[1][0], k)
            if v:
                for i in v[0]:
                    str_dic += '''<li>%s</li>''' % i
            str_dic+='</ul></div>'
        message = MIMEText(html%str_dic, 'html', 'utf-8')
    else:
        message = MIMEText('今天没有要更新的内容', 'html', 'utf-8')
    # 邮件主题
    message['Subject'] = '武汉事业单位招聘'
    # 发送方信息
    message['From'] = sender
    # 接受方信息
    message['To'] = receivers[0]

    # 登录并发送邮件
    try:
        smtpObj = smtplib.SMTP()
        # 连接到服务器
        smtpObj.connect(mail_host, 25)
        # 登录到服务器
        smtpObj.login(mail_user, mail_pass)
        # 发送
        smtpObj.sendmail(
            sender, receivers, message.as_string())
        # 退出
        smtpObj.quit()
        print('邮件发送成功')
    except smtplib.SMTPException as e:
        # 打印错误
        print('邮件发送失败', e)


def save_2_db(title,db):
    with db:
        cur = db.cursor()
        # 判断数据是否已存在
        cur.execute('SELECT * FROM title WHERE 标题 =?', title)
        title_rows = cur.fetchone()
        if title_rows:
            return False
        else:
            # 插入数据
            try:
                cur.execute("INSERT INTO title (标题) VALUES (?)", title)
                db.commit()
                return True
            except Exception as e:
                print(e)
                db.rollback()
def parse_html(html):
    dic = {}
    # 用xpath解析获取到的html内容
    xml = etree.HTML(html)
    html = xml.xpath('//*[@id="content"]/div/div[2]/ul[1]/li')
    db = sqlite3.connect('teacher_info')
    for i in html:
        # 获取招聘标题
        title = i.xpath('div[2]/div[1]/h2/a/text()')
        # 获取招聘职位
        job = i.xpath('div[2]/ul/li/a//text()')
        #获取招聘具体链接
        url = i.xpath('div[2]/div[1]/h2/a/@href')
        if save_2_db(title,db):
            jobs_list = []
            if job:
                job_len = int(len(job) / 3)
                for i in range(job_len):
                    jobs = job[i * 3] + job[i * 3 + 1] + job[i * 3 + 2]
                    jobs_list.append(jobs)
            print(title, jobs_list)
            dic[title[0]] = [jobs_list, url]
        else:
            print("已存在=======================", title)
    return dic

def get_teacher_info(url):
    # 抓取教师招聘网的信息
    url = "http://www.jiaoshizhaopin.net/hubei/wuhan"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36"
    }
    response = requests.get(url, headers)
    html = response.text
    return html
def main():
    url = "http://www.jiaoshizhaopin.net/hubei/wuhan"
    html = get_teacher_info(url)
    dic = parse_html(html)
    send_jobs_2_email(dic)

if __name__ == '__main__':
    from apscheduler.schedulers.blocking import BlockingScheduler
    # 实例化一个调度器
    scheduler = BlockingScheduler()
    # 添加任务并设置触发方式为每8点执行
    scheduler.add_job(main, 'cron',hour=8)
    # 开始运行调度器
    scheduler.start()