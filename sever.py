import werobot
import json
import pymysql
import re
import sys
import logging
import os
import threading
from logging import handlers
import smtplib
from email.mime.text import MIMEText
from email.utils import formataddr

def _logging(**kwargs):
    level = kwargs.pop('level', None)
    filename = kwargs.pop('filename', None)
    datefmt = kwargs.pop('datefmt', None)
    format = kwargs.pop('format', None)
    if level is None:
        level = logging.DEBUG
    if filename is None:
        filename = 'default.log'
    if datefmt is None:
        datefmt = '%Y-%m-%d %H:%M:%S'
    if format is None:
        format = '%(asctime)s [%(module)s] %(levelname)s [%(lineno)d] %(message)s'

    log = logging.getLogger(filename)
    format_str = logging.Formatter(format, datefmt)

    def namer(filename):
        return filename.split('default.')[1]

    os.makedirs("./debug/logs", exist_ok=True)
    th_debug = handlers.TimedRotatingFileHandler(filename="./debug/" + filename, when='D',
                                                 encoding='utf-8')
    # th_debug.namer = namer
    th_debug.suffix = "%Y-%m-%d.log"
    th_debug.setFormatter(format_str)
    th_debug.setLevel(logging.DEBUG)
    log.addHandler(th_debug)

    th = handlers.TimedRotatingFileHandler(filename=filename, when='D', encoding='utf-8')
    th.suffix = "%Y-%m-%d.log"
    th.setFormatter(format_str)
    th.setLevel(logging.INFO)
    log.addHandler(th)
    log.setLevel(level)
    return log
my_sender=""
my_pass=""
my_user=""
with open('config.json') as f:
    fileJson=json.load(f)
    robot = werobot.WeRoBot(token=fileJson['token'])
    robot.config['APP_ID']=fileJson['appID']
    robot.config['APP_SECRET']=fileJson['appsecret']
    robot.config['HOST'] = fileJson['host']
    robot.config['PORT'] = fileJson['port']
    my_sender=fileJson['mailsender']
    my_pass=fileJson['mailpass']
    my_user=fileJson['mailreceiver']
    dbuser,dbpass=fileJson['baseName'],fileJson['basePass']



def mail(text):
    print("Email sender called")
    ret = True
    try:
    # 邮件内容
        print(my_pass)
        msg = MIMEText(text, 'plain', 'utf-8')
    # 括号里的对应发件人邮箱昵称、发件人邮箱账号
        msg['From'] = formataddr(["微信公众号后台", my_sender])
    # 括号里的对应收件人邮箱昵称、收件人邮箱账号
        msg['To'] = formataddr(["管理员", my_user])
    # 邮件的主题
        msg['Subject'] = "物品兑换提醒"
        server = smtplib.SMTP_SSL("smtp.exmail.qq.com", 465)
        server.login(my_sender, my_pass)
        server.sendmail(my_sender, [my_user, ], msg.as_string())
        server.quit()
        print("here")
    except Exception:
        ret = False
        return ret
    return ret

os.makedirs('./logs', exist_ok=True)
logger = _logging(filename='./logs/default')


admin=[]
with open('admins.ini') as f:
    for line in f.readlines():  
        line=line.strip('\n')
        admin.append(line)
print(admin)
db=pymysql.connect(host = '127.0.0.1' ,user =dbuser , passwd=dbpass, port= 3306, db='rj93' , charset='utf8' )

def reg(wechat_id,name):
    se_result=_search(wechat_id)
    if(se_result[0]!=sys.maxsize):
        return '%s，您已经注册过了，修改信息执行"改名"指令。' % se_result[1]
    cursor = db.cursor()
    sql = 'INSERT INTO wechat(wechat_id, point, name) VALUES ("%s",%d,"%s")' % (wechat_id, 0, name)
    try:
        cursor.execute(sql)
        db.commit()
        cursor.close() 
        logger.info('%s registered with name %s successfully'%(wechat_id,name))
        return "注册成功！"
    except:
        # rollback when exception occurs
        db.rollback()
        cursor.close() 
        logger.info('%s failed to register with name %s'%(wechat_id,name))
        return "数据库出现错误，请稍候再试。如果连续出现此提示请联系管理员。"

def _search(wechat_id):
    # returns (point,name). If not registered, point=sys.maxsize
    cursor = db.cursor()
    sql = 'SELECT * FROM wechat WHERE wechat_id = "%s"' % (wechat_id)
    try:
        cursor.execute(sql)
        result = cursor.fetchall()
        cursor.close() 
        if(len(result)!=0):
            return result[0][1],result[0][2]
    except:
        cursor.close() 
        return sys.maxsize,''
    return sys.maxsize,''

def search(wechat_id):
    se_result=_search(wechat_id)
    if(se_result[0]==sys.maxsize):
        return "您尚未注册，不能执行此操作。请先注册。"
    else:
        return "%s，您的可用积分为：%d"%(se_result[1],se_result[0])

def update_point(wechat_id,delta):
    # 更改积分的方法 delta为积分增量
    se_result=_search(wechat_id)
    if(se_result[0]==sys.maxsize):
        return -1  #Not registered
    cursor = db.cursor()
    sql =  'UPDATE wechat SET point = point + %d WHERE wechat_id = "%s"' % (delta,wechat_id)
    try:
        cursor.execute(sql)
        db.commit()
        cursor.close() 
        logger.info('%s \'s point update with increment %d'%(wechat_id,delta))
        return 1 #success
    except:
        db.rollback()
        cursor.close() 
        return -2 #Failed

def update_name(wechat_id,new_name):
    # 更改用户名的方法
    se_result=_search(wechat_id)
    if(se_result[0]==sys.maxsize):
        return -1  #Not registered
    cursor = db.cursor()
    sql =  'UPDATE wechat SET name = "%s" WHERE wechat_id = "%s"' % (new_name,wechat_id)
    try:
        cursor.execute(sql)
        db.commit()
        cursor.close() 
        logger.info('%s update name to %s'%(wechat_id , new_name))
        return 1 #success
    except:
        db.rollback()
        cursor.close() 
        return -2 #Failed

def usecdk(wechat_id,cdk):
    # 使用激活码兑换积分的方法
    cursor = db.cursor()
    sql='SELECT * FROM cdkeys WHERE cdkey = "%s" AND usageLeft > 0 ' % (cdk)
    try:
        cursor.execute(sql)
        result = cursor.fetchall()
        if(len(result)!=0):
            if(result[0][4]==0): #0 stands for not-allowed-reuse
                if wechat_id in str(result[0][3]).split(','):
                    return -15 #already used
            sql= 'UPDATE cdkeys SET usageLeft = usageLeft - 1 WHERE cdkey = "%s"' % (result[0][0])
            cursor.execute(sql)
            sql= 'UPDATE cdkeys SET usedUsers = "%s" WHERE cdkey = "%s"' % (str(wechat_id)+","+str(result[0][3]),cdk)
            cursor.execute(sql)
            db.commit()
            cursor.close()
            return update_point(wechat_id,result[0][1]) 
        return -10 # No accessible cdk found
    except:
        db.rollback()
        cursor.close()
        return -20 # exception occured

def getreward(wechat_id,name):
    # 使用积分兑换奖品的方法
    cursor = db.cursor()
    sql='SELECT * FROM rewards WHERE Name = "%s" AND usageLeft > 0 ' % (name)
    try:
        cursor.execute(sql)
        result = cursor.fetchall()
        if(len(result)!=0):
            if(result[0][4]==0): #0 stands for not-allowed-reuse
                if wechat_id in str(result[0][3]).split(','):
                    return -15 #already used

            if(_search(wechat_id)[0]+result[0][1]<0):
                return -16 
            sql= 'UPDATE rewards SET usageLeft = usageLeft - 1 WHERE Name = "%s"' % (result[0][0])
            cursor.execute(sql)
            sql= 'UPDATE rewards SET usedUsers = "%s" WHERE Name = "%s"' % (str(wechat_id)+","+str(result[0][3]),name)
            cursor.execute(sql)
            db.commit()
            cursor.close()
            print("Starting searching info")
            if(mail(_search(wechat_id)[1]+"("+str(wechat_id)+")兑换了["+result[0][0]+"]，请尽快处理")):
                return update_point(wechat_id,result[0][1]) 
            return -30 # Failed to send email to the admin
        return -10 # No accessible cdk found
    except:
        db.rollback()
        cursor.close()
        return -20 # exception occured

@robot.filter(re.compile("注册([\t ]*)(.*)"))
def reply_reg(message, session, matchObj):
    if(len(matchObj.group(2).strip())!=0):
        return reg(message.source,matchObj.group(2))
    else:
        return '请按照"注册 用户名"（如：注册 王老板）的格式输入。'

@robot.filter("查询")
def reply_req(message):
    return search(message.source)

@robot.filter("标识码")
def reply_req(message, session, match):
    return (message.source)

@robot.filter("签到")
def reply_bonus(message, session, match):
    if(update_point(message.source,+100)==1):
        return "签到成功，积分+100！"
    return "您尚未注册，不能执行此操作。请先注册。"

@robot.filter(re.compile("激活([\t ]*)(.*)"))
def reply_change(message,session, matchObj):
    cdk=matchObj.group(2).strip()
    if(len(cdk)!=0):
        result=usecdk(message.source,cdk)
        if(result==1):
            return "激活成功！"
        else:
            return "您的代码无效或已被使用。"
    else:
        return '请按照"激活 代码"（如：激活 sample）的格式输入。'

@robot.filter(re.compile("改名([\t ]*)(.*)"))
def reply_change(message,session, matchObj):
    if(len(matchObj.group(2).strip())!=0):
        result=update_name(message.source,matchObj.group(2).strip())
        if(result==1):
            return "修改成功！"
        else:
            return "您尚未注册，不能执行此操作。请先注册。"
    else:
        return '请按照"改名 姓名"（如：改名 王老板）的格式输入。'

@robot.filter(re.compile("兑换([\t ]*)(.*)"))
def reply_reward(message,session, matchObj):
    cdk=matchObj.group(2).strip()
    if(len(cdk)!=0):
        result=getreward(message.source,cdk)
        if(result==1):
            return "兑换成功！请等待工作人员联系。"
        else:
            print(result)
            return "库存不足或已到最大兑换限度。"
    else:
        cursor = db.cursor()
        sql = "SELECT * FROM rewards"
        try:
            cursor.execute(sql)
            results = cursor.fetchall()
            resultstr=""
            for row in results:
                name_ = row[0]
                point_ = row[1]
                use_ = row[2]
                reuse_ = row[4]
                resultstr=resultstr+ "%s,所需积分%d,剩余个数%d,是否可以重复兑换%d\n" % (name_,-point_, use_, reuse_)
        except:
            return "数据库出现错误，请稍候再试。如果连续出现此提示请联系管理员。"
    return resultstr +'请按照"兑换 物品名"（如：兑换 sample）的格式输入。'

def reply_help():
    return '回复"注册 用户名"（如：注册 王老板）为当前微信号注册账号\n回复"查询"获取当前积分\n回复"签到"获取积分+1\
    \n回复"激活"激活积分代码\n回复"改名"修改用户名\n回复"兑换"使用积分换取奖励'
robot.add_filter(func=reply_help, rules=["？", "?","help"])

#======= admin methods =======

@robot.filter("后台")
def reply_add_cdk(message):
    # 考虑加密存储admin
    if (message.source in admin):
        return "success"
    return "权限不足"
@robot.handler
def reply_no_found():
    return "找不到您所输入的指令，请检查您的输入。"

# 让服务器监听在 0.0.0.0:2562
robot.run()