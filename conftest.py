# -*- coding: utf-8 -*-
"""
conftest.py：pytest 的“公共夹具(fixture)”文件，文件名固定，pytest 会自动加载，无需 import。
fixture 等价于 JMeter 的 setUp/tearDown、Postman 的集合级前置脚本，用来统一准备登录态、清理数据。
"""
import os
import sys

# 让 testcases 里能 import 到根目录下的 api / config 包
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pytest
from api.client import LitemallClient
from config import config


@pytest.fixture
def client():
    """未登录客户端：专门用于“未登录访问”等鉴权异常用例。"""
    c = LitemallClient()
    yield c


@pytest.fixture
def user_client():
    """
    已登录客户端（function 级：每个用例都是全新会话，互不影响）。
    前置：登录 + 清空购物车；后置：再清空购物车，保证用例可重复执行、数据隔离。
    """
    c = LitemallClient()
    login_body = c.login(config.USERNAME, config.PASSWORD)
    assert login_body["errno"] == 0, "测试账号登录失败，请检查 config.py 中的账号密码与服务是否启动"
    c.clear_cart()          # 前置清理
    yield c                 # yield 之前是前置，之后是后置
    c.clear_cart()          # 后置清理（测试数据准备与清理思想）
