# -*- coding: utf-8 -*-
"""
商品模块：列表、搜索（命中/空结果）、详情与 SKU 提取。
覆盖：场景法、边界值（空结果）、参数化数据驱动、接口关联的“取数”环节。
"""
import pytest
from config import config
from data.test_data import SEARCH_KEYWORDS_HIT, SEARCH_KEYWORDS_EMPTY


def test_goods_list_default(client):
    """商品首页默认列表应能查到在售商品（初始库有 29 个家纺商品）。"""
    body = client.goods_list(page=1, limit=10)
    assert body["errno"] == 0
    assert len(body["data"]["list"]) > 0


@pytest.mark.parametrize("keyword", SEARCH_KEYWORDS_HIT)
def test_search_hit(client, keyword):
    """数据驱动：多个真实存在的关键词，都应搜到结果。"""
    body = client.goods_list(keyword=keyword)
    assert body["errno"] == 0
    assert body["data"]["total"] > 0
    assert len(body["data"]["list"]) > 0


@pytest.mark.parametrize("keyword", SEARCH_KEYWORDS_EMPTY)
def test_search_empty(client, keyword):
    """边界：搜索库里没有的词（手机/电脑），errno 仍为 0，但 total=0、list 为空——这不是 bug。"""
    body = client.goods_list(keyword=keyword)
    assert body["errno"] == 0
    assert body["data"]["total"] == 0
    assert body["data"]["list"] == []


def test_goods_detail_and_extract_sku(client):
    """
    详情 + 接口关联取数：从商品详情里动态取出 SKU(productId)，
    后续加购/下单都依赖它（等价 Postman 的 JSON 提取 $.data.productList[0].id）。
    """
    body = client.goods_detail(config.GOODS_ID)
    assert body["errno"] == 0
    assert body["data"]["info"]["id"] == config.GOODS_ID
    product_list = body["data"]["productList"]
    assert len(product_list) > 0
    product_id = product_list[0]["id"]      # ← 关联取值
    assert isinstance(product_id, int)
