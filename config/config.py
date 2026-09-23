# -*- coding: utf-8 -*-
"""
全局配置：环境地址、账号、固定测试数据。
切换测试环境（测试/预发）时，只需要改这里的 BASE_URL，用例代码不用动 —— 这就是“环境隔离”。
"""

# ====== 被测环境 ======
# 改成你自己的腾讯云公网 IP（后端端口固定 8080）；本地部署就用 http://127.0.0.1:8080
BASE_URL = "http://106.55.27.7:8080"

# ====== 买家测试账号（你在 litemall 里注册的账号）======
USERNAME = "user123"
PASSWORD = "user123"

# ====== 固定测试商品（初始库真实存在：色织精梳AB纱格纹空调被）======
GOODS_ID = 1011004     # SPU，商品 id
PRODUCT_ID = 20        # SKU，具体规格货品 id（下单/加购用的是它）

# ====== 收货地址测试数据（手机号必须符合 11 位手机号正则，否则后端 401）======
ADDRESS = {
    "name": "测试收货人",
    "tel": "13800138000",
    "province": "福建省",
    "city": "厦门市",
    "county": "同安区",
    "areaCode": "350212",
    "addressDetail": "新民镇测试路1号",
    "isDefault": True,
}

# ====== 业务返回码约定（litemall 特点：HTTP 基本恒为 200，成败看 errno）======
class Errno:
    OK = 0          # 成功
    BAD_ARG = 401   # 缺少参数 / 参数不合法
    BAD_VALUE = 402 # 参数值不对（如购物车项不属于本人）
    UNLOGIN = 501   # 未登录 / token 缺失

# ====== 数据库（可选，仅用于“接口+数据库”双重校验）======
DB_CONFIG = {
    "host": "127.0.0.1",   # 云数据库默认只允许本机连接，远程连不上就保持默认、不用 db 用例
    "port": 13306,
    "user": "litemall",
    "password": "sqlmima",
    "database": "litemall",
    "charset": "utf8mb4",
}
'''
DB_CONFIG = {"host": "127.0.0.1", "port": 13306, "user": "litemall",
             "password": "sqlmima", "database": "litemall", "charset": "utf8mb4"}
'''

