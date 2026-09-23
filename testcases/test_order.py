# -*- coding: utf-8 -*-
"""
订单模块：完整下单交易主链路（场景法/业务流测试），是整套脚本的核心冒烟用例。
链路：登录 → 商品详情取SKU → 加购 → 准备收货地址 → 结算checkout → 下单submit取orderId
      → 订单详情/列表断言 → 取消订单（回补库存、清理，保证可重复执行）。
这条链路集中体现“接口关联”：上一个接口的返回值，是下一个接口的入参。
"""
import json
import pytest
from config import config


@pytest.mark.smoke
def test_full_order_flow(user_client):
    c = user_client

    # 1) 商品详情，动态取出 SKU（productId）——关联起点
    detail = c.goods_detail(config.GOODS_ID)
    assert detail["errno"] == 0
    product_id = detail["data"]["productList"][0]["id"]

    # 2) 加入购物车（add 默认勾选，结算时会被带上）
    assert c.cart_add(config.GOODS_ID, product_id, 1)["errno"] == 0

    # 3) 准备收货地址：已有就用第一个，没有就新增
    addr_list = c.address_list()["data"]["list"]
    if addr_list:
        address_id = addr_list[0]["id"]
    else:
        saved = c.address_save()
        assert saved["errno"] == 0
        address_id = saved["data"]      # 注意：地址保存成功 data 直接是整数 id（不是 data.id）
    assert address_id

    # 4) 结算预览：cartId=0 结算所有已勾选商品，带上 addressId
    checkout = c.order_checkout(cart_id=0, address_id=address_id)
    assert checkout["errno"] == 0

    # 5) 提交订单，取出 orderId —— 关键关联产出
    submit = c.order_submit(address_id=address_id, cart_id=0)
    assert submit["errno"] == 0, f"下单失败：{submit}"
    order_id = submit["data"]["orderId"]
    assert order_id

    # 6) 订单详情断言（用 json.dumps 宽松包含，避免耦合具体嵌套字段）
    detail_order = c.order_detail(order_id)
    assert detail_order["errno"] == 0
    assert str(order_id) in json.dumps(detail_order["data"], ensure_ascii=False)

    # 7) 订单列表里应能找到刚下的单
    order_list = c.order_list()
    assert order_list["errno"] == 0
    assert any(o.get("id") == order_id for o in order_list["data"]["list"])

    # 8) 取消订单：回补库存并清理，保证脚本可反复运行（数据清理）
    cancel = c.order_cancel(order_id)
    assert cancel["errno"] == 0
