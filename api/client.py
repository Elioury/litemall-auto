# -*- coding: utf-8 -*-
"""
接口封装层（api 层）：把 litemall 买家端接口按业务模块封装成方法。
设计目的：
  1. 用例层只写“做什么业务”，不关心 URL、请求头怎么拼 —— 和 Postman 里“一个请求一个卡片”对应；
  2. 接口路径/参数一旦变化，只改这一个文件（和 PageObject 同一种“封装隔离变化”的思想）；
  3. 统一处理 Token 请求头（等价于 JMeter 的 HTTP 信息头管理器）。
"""
import base64
import json

import requests
from config import config


def parse_jwt_user_id(token):
    """
    从 litemall 登录 token（JWT）解析用户 id。
    背景：账号登录返回的 userInfo 只有 nickName/avatarUrl、不含 id；userId 编码在 JWT payload。
    JWT 结构 header.payload.signature，payload 是 base64url 编码的 JSON，字段名为 "userId"。
    """
    try:
        payload = token.split(".")[1]
        payload += "=" * (-len(payload) % 4)          # base64url 补齐到 4 的倍数再解码
        data = json.loads(base64.urlsafe_b64decode(payload))
        return data.get("userId") or data.get("user_id")
    except Exception:
        return None


class LitemallClient:
    """一个 LitemallClient 实例 = 一个“虚拟用户会话”。"""

    def __init__(self):
        self.base_url = config.BASE_URL.rstrip("/")
        # requests.Session 会自动维持 Cookie；litemall 主要靠 Token，我们手动放到请求头
        self.session = requests.Session()
        self.token = None
        self.user_id = None        # 登录后记录用户id，供数据库断言按 user_id 核对


    # ---------- 内部统一请求方法（所有接口都走这里，统一加 token、统一异常处理）----------
    def _request(self, method, path, **kwargs):
        url = self.base_url + path
        # 关键：登录拿到 token 后，后续每个请求都自动带 X-Litemall-Token 头
        headers = kwargs.pop("headers", {})
        if self.token:
            headers["X-Litemall-Token"] = self.token
        resp = self.session.request(method, url, headers=headers, timeout=10, **kwargs)
        resp.raise_for_status()      # HTTP 层异常（4xx/5xx）直接抛出
        return resp.json()           # litemall 统一返回 JSON：{errno, errmsg, data}

    # ==================== 1. 登录鉴权 ====================
    def login(self, username, password):
        """POST /wx/auth/login；成功后把 token 存到本会话，后续请求自动携带。"""
        body = self._request("POST", "/wx/auth/login",
                             json={"username": username, "password": password})
        if body.get("errno") == 0:
            self.token = body["data"]["token"]     # 等价 Postman 的 pm.environment.set('token',...)
            self.user_id = body["data"].get("userInfo", {}).get("id") or parse_jwt_user_id(self.token)
        return body

    # ==================== 2. 商品 ====================
    def goods_list(self, page=1, limit=10, keyword=None, sort="add_time", order="desc"):
        """GET /wx/goods/list：商品列表 + 关键字搜索（带 keyword 就是搜索）。"""
        params = {"page": page, "limit": limit, "sort": sort, "order": order}
        if keyword:
            params["keyword"] = keyword
        return self._request("GET", "/wx/goods/list", params=params)

    def goods_detail(self, goods_id):
        """GET /wx/goods/detail?id=：商品详情，返回 info(SPU) 与 productList(SKU)。"""
        return self._request("GET", "/wx/goods/detail", params={"id": goods_id})

    # ==================== 3. 购物车 ====================
    def cart_index(self):
        """GET /wx/cart/index：购物车列表，cartList 每项含 id(购物车行id)/goodsId/productId/number。"""
        return self._request("GET", "/wx/cart/index")

    def cart_add(self, goods_id, product_id, number):
        """POST /wx/cart/add，body={goodsId,productId,number}；已存在则数量累加，默认勾选。"""
        return self._request("POST", "/wx/cart/add",
                             json={"goodsId": goods_id, "productId": product_id, "number": number})

    def cart_update(self, cart_id, goods_id, product_id, number):
        """
        POST /wx/cart/update，body={id,goodsId,productId,number}。
        注意（实战踩坑点）：id 是购物车行主键，goodsId/productId 必须与该行一致（三值同源），
        否则后端返回 402。正确做法是先 cart_index 取出同一行的三个值。
        """
        return self._request("POST", "/wx/cart/update", json={
            "id": cart_id, "goodsId": goods_id, "productId": product_id, "number": number})

    def cart_checked(self, product_ids, is_checked=1):
        """POST /wx/cart/checked，body={productIds:[...], isChecked:1勾选/0取消}。"""
        return self._request("POST", "/wx/cart/checked",
                             json={"productIds": product_ids, "isChecked": is_checked})

    def cart_delete(self, product_ids):
        """POST /wx/cart/delete，body={productIds:[...]}。"""
        return self._request("POST", "/wx/cart/delete", json={"productIds": product_ids})

    # ==================== 4. 收货地址 ====================
    def address_save(self, addr=None):
        """
        POST /wx/address/save：新增地址。
        成功后 data 直接是“新地址的整数 id”（不是 data.id，这也是实战踩坑点）。
        """
        addr = addr or config.ADDRESS
        return self._request("POST", "/wx/address/save", json=addr)

    def address_list(self):
        """GET /wx/address/list：当前用户地址列表。"""
        return self._request("GET", "/wx/address/list")

    # ==================== 5. 订单 ====================
    def order_checkout(self, cart_id=0, address_id=0):
        """
        GET /wx/order/checkout：结算预览（算价格、运费、选中地址/商品）。
        cartId=0 表示结算“所有已勾选”购物车商品；addressId=0 表示用默认地址。
        """
        return self._request("GET", "/wx/cart/checkout", params={
            "cartId": cart_id, "addressId": address_id, "couponId": 0,
            "userCouponId": 0, "grouponRulesId": 0})

    def order_submit(self, address_id, cart_id=0):
        """
        POST /wx/order/submit：真正下单，成功 data.orderId 即订单号（接口关联的关键产出）。
        """
        return self._request("POST", "/wx/order/submit", json={
            "cartId": cart_id, "addressId": address_id, "couponId": 0,
            "userCouponId": 0, "grouponRulesId": 0, "message": "自动化测试订单"})

    def order_list(self, page=1, limit=10, showType=0):
        """GET /wx/order/list：订单列表。"""
        return self._request("GET", "/wx/order/list",
                             params={"page": page, "limit": limit, "showType": showType})

    def order_detail(self, order_id):
        """GET /wx/order/detail?orderId=：订单详情。"""
        return self._request("GET", "/wx/order/detail", params={"orderId": order_id})

    def order_cancel(self, order_id):
        """POST /wx/order/cancel，body={orderId}：取消订单并回补库存（保证脚本可重复执行）。"""
        return self._request("POST", "/wx/order/cancel", json={"orderId": order_id})

    # ---------- 工具方法：清空当前用户购物车（用例前后置/数据清理用）----------
    def clear_cart(self):
        """把当前用户购物车里的商品全部删掉，保证用例之间互不影响（用例独立性）。"""
        body = self.cart_index()
        product_ids = [item["productId"] for item in body["data"]["cartList"]]
        if product_ids:
            self.cart_delete(product_ids)
