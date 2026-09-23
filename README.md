# litemall 接口自动化测试工程（pytest + requests）

一套可直接运行、分层设计、带完整中文注释的电商接口自动化项目，覆盖 **登录鉴权、商品搜索、购物车、完整下单交易** 四类核心场景，是把你在 Postman 里手工做的接口测试“代码化”。

## 一、目录结构（分层思想）

```
litemall_auto/
├── config/config.py      # 环境配置：base_url、账号、固定商品、地址、返回码、数据库
├── data/test_data.py     # 测试数据：搜索词、非法数量、错误账号（数据驱动）
├── api/client.py         # 接口封装层：所有 litemall 接口收敛成 LitemallClient 的方法
├── utils/db.py           # （可选）MySQL 双重校验工具
├── testcases/            # 测试用例层：只写业务步骤与断言
│   ├── test_auth.py      #   鉴权：登录正反向、未登录拦截
│   ├── test_goods.py     #   商品：列表、搜索命中/空结果、详情取SKU
│   ├── test_cart.py      #   购物车：加购、边界数量、改数量、勾选、删除
│   └── test_order.py     #   订单：完整下单主链路（核心冒烟）
├── conftest.py           # 公共夹具：统一登录态(user_client)、前后置清数据
├── reports/              # 报告输出目录
├── pytest.ini            # pytest 配置
└── requirements.txt
```

分层好处：接口变了只改 `api/`，数据变了只改 `data/`，用例只关心业务。

## 二、环境准备（Windows）

```bash
# 1) 建议用 Python 3.9~3.12，进入项目目录后安装依赖
pip install -r requirements.txt

# 2) 打开 config/config.py，把 BASE_URL 改成你的公网IP，确认账号/商品id
#    BASE_URL = "http://你的公网IP:8080"
```

## 三、运行命令

```bash
# 跑全部用例（pytest.ini 已默认生成 reports/report.html）
pytest

# 只跑核心下单冒烟用例（按 mark）
pytest -m smoke

# 按文件名/关键字筛选
pytest testcases/test_cart.py
pytest -k search

# 生成 Allure 报告（需先安装 allure 命令行）
pytest --alluredir=reports/allure
allure serve reports/allure
```

## 四、场景与用例设计对照（面试可讲）

| 业务场景 | 用例 | 设计方法 | 断言点 |
|---|---|---|---|
| 登录 | 正确登录/错误密码/不存在用户 | 等价类 | errno、token |
| 鉴权 | 未登录加购 | 安全/异常流 | errno=501 |
| 商品搜索 | 命中词/空结果词 | 参数化、边界值 | total、list |
| 购物车 | 加购、数量0/负数、改数量、勾选、删除 | 边界值、等价类 | errno + 列表核对 |
| 下单 | 详情→加购→地址→结算→下单→查询→取消 | 场景法（业务流） | orderId、详情/列表包含 |

## 五、接口关联是怎么体现的

- **Token 关联**：`login` 拿到 token 存到 client，后续请求由 `_request` 自动加 `X-Litemall-Token` 头（等价 JMeter HTTP 信息头管理器）。
- **SKU 关联**：商品详情 `data.productList[0].id` → 作为加购入参 productId。
- **购物车行关联**：购物车列表同一行的 `id/goodsId/productId` 三值同源 → 作为 update 入参（否则 402）。
- **地址关联**：地址保存返回的 `data`（直接是整数 id）→ 作为下单 addressId。
- **订单关联**：下单返回 `data.orderId` → 作为订单详情/取消的入参。

## 六、实战踩坑点（已在代码中规避）

1. litemall 的 HTTP 状态码基本恒为 200，成败看响应体 `errno`（0成功/401缺参/402值不对/501未登录）。
2. 购物车 `update` 必须传同一行的 id/goodsId/productId，错配返回 402。
3. 地址 `save` 成功后 id 在 `data` 本身（整数），不是 `data.id`。
4. 搜索“手机/电脑”为空不是 bug，初始库 29 个商品全是家纺。
5. 下单用例最后主动 `cancel` 回补库存，保证可重复执行（测试数据清理）。

## 七、可选：接口 + 数据库双重校验

`utils/db.py` 给了 PyMySQL 示例（查订单是否落库、查 SKU 库存变化）。云数据库默认不开放远程，需放行 3306 并授权后才能在本地连，不连不影响接口用例。
