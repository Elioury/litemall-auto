import pytest
from config import config

try:
    import allure
except ImportError:                      # 没装 allure 也能跑，只是没有美化报告
    class _AllureShim:
        def __getattr__(self, name):
            def decorator(*a, **k):
                if a and callable(a[0]): return a[0]
                def wrap(f): return f
                return wrap
            return decorator
        def step(self, title):
            class _S:
                def __enter__(self): return self
                def __exit__(self, *e): return False
            return _S()
        def attach(self, *a, **k): return None
    allure = _AllureShim()

@pytest.fixture
def db():                               # 数据库夹具：连不上自动 skip
    pytest.importorskip("pymysql")
    from utils.db import DB
    try:
        conn = DB()
    except Exception as e:
        pytest.skip(f"数据库不可达，请先开 SSH 隧道并把端口改为 13306：{e}")
    yield conn
    conn.close()

@allure.feature("交易中心-订单")
@allure.story("买家完整下单-取消链路（含数据库校验）")
@allure.severity("critical")
@pytest.mark.smoke
def test_order_flow_with_db_check(user_client, db):
    c = user_client
    with allure.step("商品详情取 SKU，并记录下单前库存"):
        detail = c.goods_detail(config.GOODS_ID)
        assert detail["errno"] == 0
        product_id = detail["data"]["productList"][0]["id"]
        stock_before = db.get_product_stock(product_id)

    with allure.step("加购 1 件"):
        assert c.cart_add(config.GOODS_ID, product_id, 1)["errno"] == 0

    with allure.step("准备收货地址"):
        addr_list = c.address_list()["data"]["list"]
        address_id = addr_list[0]["id"] if addr_list else c.address_save()["data"]
        assert address_id

    with allure.step("结算预览"):
        assert c.order_checkout(cart_id=0, address_id=address_id)["errno"] == 0

    with allure.step("提交订单，取 orderId"):
        submit = c.order_submit(address_id=address_id, cart_id=0)
        assert submit["errno"] == 0, f"下单失败：{submit}"
        order_id = submit["data"]["orderId"]
        assert order_id

    with allure.step("接口断言：详情/列表可查到订单"):
        assert c.order_detail(order_id)["errno"] == 0
        assert any(o.get("id") == order_id for o in c.order_list()["data"]["list"])

    with allure.step("数据库断言①：订单落库、归属正确、状态=101"):
        order_row = db.get_order(order_id)
        assert order_row is not None, "订单未落库"
        assert order_row["user_id"] == c.user_id
        assert order_row["order_status"] == 101

    with allure.step("数据库断言②：库存扣减 1"):
        assert db.get_product_stock(product_id) == stock_before - 1

    with allure.step("取消订单"):
        assert c.order_cancel(order_id)["errno"] == 0

    with allure.step("数据库断言③：状态=102，库存回补"):
        assert db.get_order(order_id)["order_status"] == 102
        assert db.get_product_stock(product_id) == stock_before