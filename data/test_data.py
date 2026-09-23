# -*- coding: utf-8 -*-
"""
测试数据集中管理（数据驱动思想：用例逻辑不变，数据放这里）。
parametrize 直接引用下面的数据，新增场景只需加数据、不用改用例代码。
"""

# 商品搜索：初始库 29 个商品全是家纺/床品，这些关键词一定能搜到
SEARCH_KEYWORDS_HIT = ["四件套", "被", "毛巾", "枕", "棉"]

# 搜索：库里不存在的词，用于“空结果”边界用例（errno 仍为 0，但 list 为空）
SEARCH_KEYWORDS_EMPTY = ["手机", "电脑", "不存在的商品xyz"]

# 购物车购买数量的非法边界值（后端应返回 401）
INVALID_CART_NUMBER = [0, -1, -99]

# 错误登录凭据（用于鉴权/异常用例）
WRONG_LOGIN = [
    ("user123", "wrong_pwd"),
    ("not_exist_user", "123456"),
]
