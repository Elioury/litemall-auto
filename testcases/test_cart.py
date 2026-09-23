# -*- coding: utf-8 -*-
"""
购物车模块：加购、非法数量边界、改数量（三值同源）、勾选、删除。
全部使用已登录的 user_client（conftest 里每个用例前后自动清空购物车，保证独立可重复）。
"""
import pytest
from config import config
from data.test_data import INVALID_CART_NUMBER


def _find_cart_item(client, product_id):
    """辅助：从购物车列表里找到指定 SKU 的那一行（关联取 id/goodsId/productId）。"""
    body = client.cart_index()
    assert body["errno"] == 0
    for item in body["data"]["cartList"]:
        if item["productId"] == product_id:
            return item
    return None


def test_add_cart_success(user_client):
    """正向：加购 1 件，errno=0，且购物车列表里能查到该 SKU。"""
    body = user_client.cart_add(config.GOODS_ID, config.PRODUCT_ID, 1)
    assert body["errno"] == 0
    item = _find_cart_item(user_client, config.PRODUCT_ID)
    assert item is not None


@pytest.mark.parametrize("number", INVALID_CART_NUMBER)
def test_add_cart_invalid_number(user_client, number):
    """边界值：数量为 0/负数，后端应返回 401（参数不合法）。"""
    body = user_client.cart_add(config.GOODS_ID, config.PRODUCT_ID, number)
    assert body["errno"] == config.Errno.BAD_ARG


def test_update_cart_number(user_client):
    """
    修改数量（实战踩坑点）：update 需要 {id,goodsId,productId,number}，
    其中 id/goodsId/productId 必须来自购物车列表里“同一行”（三值同源），否则 402。
    """
    user_client.cart_add(config.GOODS_ID, config.PRODUCT_ID, 1)
    item = _find_cart_item(user_client, config.PRODUCT_ID)
    assert item is not None

    body = user_client.cart_update(
        cart_id=item["id"], goods_id=item["goodsId"],
        product_id=item["productId"], number=2)
    assert body["errno"] == 0

    # 二次查询，断言数量确实变成 2（接口返回成功 + 数据核对）
    again = _find_cart_item(user_client, config.PRODUCT_ID)
    assert again["number"] == 2


def test_cart_uncheck(user_client):
    """勾选状态：加购默认勾选，调用 checked 取消勾选后，该行 checked 应为 False。"""
    user_client.cart_add(config.GOODS_ID, config.PRODUCT_ID, 1)
    item = _find_cart_item(user_client, config.PRODUCT_ID)
    body = user_client.cart_checked([item["productId"]], is_checked=0)
    assert body["errno"] == 0
    assert _find_cart_item(user_client, config.PRODUCT_ID)["checked"] is False


def test_delete_cart_item(user_client):
    """删除：加购后删除该 SKU，购物车列表里应再查不到。"""
    user_client.cart_add(config.GOODS_ID, config.PRODUCT_ID, 1)
    body = user_client.cart_delete([config.PRODUCT_ID])
    assert body["errno"] == 0
    assert _find_cart_item(user_client, config.PRODUCT_ID) is None
