## 公众号后台 For Ruanjian93

#### 简介：

```Python werobot框架+MySQL```

主要功能：

注册：将微信号与用户名绑定

改名：修改微信号对应的用户名

激活：使用积分码来兑换积分，积分码可以注册以下类型：

1. 只允许单次使用

2. 允许多次使用，但每人只允许一次

3. 允许多次使用，且不限制每人使用次数

兑换：使用积分来兑换奖品，兑换成功后会给配置文件中的管理员发送电子邮件提醒处理。实现逻辑与激活积分码相同，但增加了积分余额与所需积分的比较。

查询：查询当前微信用户的积分余额。

后台：可以将指定的微信号注册为管理员，并可根据此开发其他功能。

#### 配置文件说明：

在同级目录下放置两个文件：

```config.json```结构如下：

```json
{
    "appID": "",
    "appsecret": "",
    "token": """,
    "host": "mysql地址，默认0.0.0.0",
    "port": "mysql端口",
    "baseName": "mysql用户名",
    "basePass": "mysql密码",
    "mailsender":"发信邮箱，默认使用腾讯企业邮服务器",
    "mailpass":"发信邮箱密码",
    "mailreceiver":"收信邮箱地址"
}
```



```admins.ini```存储管理员WeChat_ID，每行一个。不要添加多余字符

#### TODOS

admins加密存储比对

完善功能（管理员操作）

优化代码结构/重构代码