# -*- coding: utf-8 -*-
from config import config

# 登录+搜索+加购，验证骨架可用
def test_login_and_search(client):            # client 是未登录夹具
    body = client.login(config.USERNAME, config.PASSWORD)
    assert body["errno"] == 0                  # 登录成功
    assert body["data"]["token"]               # 且下发了 token
    g = client.goods_list(keyword="四件套")
    assert g["errno"] == 0
    assert len(g["data"]["list"]) > 0         # 搜索要有结果

def test_add_cart(user_client):                # user_client 是已登录、已清购物车的夹具
    r = user_client.cart_add(config.GOODS_ID, config.PRODUCT_ID, 1)
    assert r["errno"] == 0                     # 加购成功