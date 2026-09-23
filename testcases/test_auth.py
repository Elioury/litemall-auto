# -*- coding: utf-8 -*-
"""
鉴权模块：登录正/反向用例 + 未登录访问拦截。
覆盖用例设计方法：等价类（正确/错误凭据）、安全鉴权。
"""
import pytest
from config import config
from data.test_data import WRONG_LOGIN


def test_login_success(client):
    """正向：正确账号密码登录，应返回 errno=0 且下发 token。"""
    body = client.login(config.USERNAME, config.PASSWORD)
    assert body["errno"] == 0
    assert body["data"]["token"]          # token 必须存在
    assert client.token == body["data"]["token"]   # client 已自动保存，后续请求自动带


@pytest.mark.parametrize("username,password", WRONG_LOGIN)
def test_login_wrong_credential(client, username, password):
    """反向（等价类）：错误密码/不存在用户，errno 必须非 0。"""
    body = client.login(username, password)
    assert body["errno"] != 0


def test_add_cart_without_token(client):
    """安全鉴权：未登录直接加购，后端应返回 501（未登录）。"""
    body = client.cart_add(config.GOODS_ID, config.PRODUCT_ID, 1)
    assert body["errno"] == config.Errno.UNLOGIN
