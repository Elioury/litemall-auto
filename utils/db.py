# -*- coding: utf-8 -*-
"""
数据库校验工具（可选增强）。
作用：接口返回对不对，除了断言响应体，还可以连 MySQL 校验“库里的数据是否真的变了”，
      这就是“接口测试 + 数据库双重校验”，也是你手工阶段用 SQL 核对数据的代码化。

注意：腾讯云 MySQL 默认只监听 127.0.0.1、且安全组通常不放行 3306，本地一般连不上。
      想在本地跑数据库用例，需要：①安全组放行3306；②MySQL 授权远程用户。
      连不上完全不影响接口用例，本类默认不被引用。
"""


# -*- coding: utf-8 -*-
"""数据库校验工具（接口自动化的“数据层断言”，可选增强层）。"""
from config import config


class DB:
    def __init__(self, db_config=None):
        try:
            import pymysql
        except ImportError as e:
            raise ImportError("未安装 PyMySQL，请先执行 pip install PyMySQL") from e
        cfg = dict(db_config or config.DB_CONFIG)
        cfg.setdefault("charset", "utf8mb4")
        cfg["cursorclass"] = pymysql.cursors.DictCursor
        self.conn = pymysql.connect(autocommit=True, **cfg)

    def query_all(self, sql, args=None):
        with self.conn.cursor() as cur:
            cur.execute(sql, args)
            return cur.fetchall()

    def query_one(self, sql, args=None):
        with self.conn.cursor() as cur:
            cur.execute(sql, args)
            return cur.fetchone()

    def query_scalar(self, sql, args=None):
        row = self.query_one(sql, args)
        return None if not row else next(iter(row.values()))

    def get_order(self, order_id):
        return self.query_one(
            "SELECT id, user_id, order_status, actual_price "
            "FROM litemall_order WHERE id=%s", (order_id,))

    def get_product_stock(self, product_id):
        return self.query_scalar(
            "SELECT number FROM litemall_goods_product WHERE id=%s", (product_id,))

    def count_user_orders(self, user_id, order_status=None):
        if order_status is None:
            return self.query_scalar(
                "SELECT COUNT(*) FROM litemall_order WHERE user_id=%s", (user_id,))
        return self.query_scalar(
            "SELECT COUNT(*) FROM litemall_order WHERE user_id=%s AND order_status=%s",
            (user_id, order_status))

    def close(self):
        if self.conn:
            self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
        return False



# ===== 结合 litemall 的常用校验 SQL（面试可讲：接口断言 + DB 断言）=====
# 1) 下单后校验订单确实落库：
#    SELECT COUNT(*) FROM litemall_order WHERE user_id = %s
# 2) 校验某 SKU 库存（下单扣减、取消回补，对应 reduceStock/addStock）：
#    SELECT number FROM litemall_goods_product WHERE id = 20
# 3) 校验购物车记录：
#    SELECT * FROM litemall_cart WHERE user_id = %s AND product_id = 20
