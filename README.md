# 园区能耗采集与预测预警系统 · 第一周

负责人：任若菡。依照学生版任务书第七节第一周交付，源码原创，业务常量按任务书。

交付包含：分层后端、独立前端/算法进程、八张表、完整种子、参数化造数、全年 CSV 与 truth、需求/接口/数据库文档、自动验证、第一周周报。**统计、定时采集、模型训练及预警属于后续周次，第一周不提供虚构模型分数。**

## 运行要求

Python 3.10+；可选 Git。零第三方依赖、不需要 Node、Docker、MySQL 或服务器。macOS/Linux 用 python3，Windows 可把命令中的 python3 换成 py。浏览器建议现代 Chrome/Firefox/Edge。

技术栈调整及 Swagger 说明见 `docs/需求说明.md`。前端为原生 HTML/CSS/JS 空壳，不是 React 项目；这是任务书允许的第一周实现选择。

## 从干净目录启动

1. 下载解压到不含权限限制的目录，进入 `park-energy-week1`。压缩包同层附有 `park-energy-week1.bundle`，含按模块拆分的 Git 历史。可离线执行 `git clone park-energy-week1.bundle park-energy-clone` 后进入 `park-energy-clone`。交付时未创建外部远程仓库。
2. 执行：

```bash
python3 db/generate_data.py
python3 db/init_db.py --import-data
python3 scripts/verify.py
python3 scripts/run.py
```

3. 打开 `http://127.0.0.1:5173`，概览可看到六块器具、全年数据量与注入率；原始数据可按区域/器具/能源/日期预览。API 调试：`http://127.0.0.1:5173/api.html`。
4. 后端：`http://127.0.0.1:8000/api/health`；算法空壳：`http://127.0.0.1:8001/health`。
5. Ctrl+C 关闭全部服务。重新启动无需重复造数和建表。明确重建数据库时先停止服务，再运行 `python3 db/init_db.py --reset --import-data`，该操作会清空现有数据库。

交付附带已生成 CSV，可以跳过第一条造数命令直接导入；但验收建议现场重跑。

端口占用：`python3 scripts/run.py --backend-port 8100 --frontend-port 5174 --algo-port 8101`，随后使用打印出的前端地址。单独启动后端：`python3 -m backend.controller`；前端：`python3 frontend/server.py`；算法：`python3 algo-service/server.py`。命令均在项目根目录执行。

## 造数参数

```bash
python3 db/generate_data.py --days 365 --seed 42 --start 2026-01-01 --missing-ratio 0.01 --outlier-ratio 0.005 --drift-ratio 0.003 --output data
```

会覆盖指定输出目录中三个生成文件，默认覆盖 data 下交付数据。需要保留现有数据时使用 `--output data-experiment`。各比例 0…1，和不超过 0.25；days 1…3660。按完整网格计数，漂移取整为完整 12 小时事件。默认网格 52,560；删除缺失 526；写出 52,034 行；异常 truth 945 个点，其中突变 263、漂移 156（13 个事件）。实际总异常率约 1.798%，非检测 accuracy。

`raw_data.csv`：device_id/device_code/data_time/value/unit/data_quality/source。缺失不写行。时间升序，同时间器具 ID 升序。`anomaly_truth.csv`：每个异常一个点，漂移含 event_id 和 start_time/end_time，保留 original_value 与 injected_value。truth 只用于评估，不得训练或推理读取。

`generation_report.json`：种子、参数、目标/实际比例、计数、SHA-256。生成器标准库随机序列与任务书 NumPy 示例不同，但负荷公式一致；同 Python 版本重跑一致。

## 验证与验收

```bash
python3 scripts/verify.py
python3 scripts/smoke_test.py
```

verify 检查全年完整网格、缺行/真值一一对应、互斥异常、漂移窗口/倍率、突变倍率、SHA-256 与重跑一致性、数据库约束和区域下钻过滤、空结果与非法参数。smoke_test 在临时数据库与随机可用端口启动三个服务，测试 HTTP/代理/错误响应，结束后关闭进程。已从干净目录 `git clone` 离线 bundle，按 README 建库、重跑数据、启动三个服务，并验证 Ctrl+C 清理通过；证据在 `docs/clean-clone-validation.json`。其他验证见 `docs/validation.json` 和 `docs/weekly/week1.md`。

## 目录

| 路径 | 内容 |
|---|---|
| backend/ | Controller / Service / Mapper |
| frontend/ | 独立页面、样式、请求封装、同源代理、接口调试 |
| algo-service/ | 独立算法服务 health 空壳 |
| db/ | DDL、种子、造数、数据库初始化 |
| data/ | 全年原始 CSV、异常 truth、生成报告 |
| docs/ | 需求、契约、数据库设计、验收证据、周报 |
| scripts/ | 启停、数据与数据库验证、HTTP 冒烟 |
| runtime/ | 本地数据库（自动创建，Git 忽略） |

第一周完成清单见周报；第二周实现主数据 CRUD、每分钟增量采集、日志、手工填报、导出和能耗汇总下钻。

## 常见问题

- 页面提示后端不可用：查看运行终端，先初始化数据库，确认 8000 端口正常。
- 无原始数据：仅建表不会自动导入；停服务后显式 `--reset --import-data` 重建演示数据。
- 页面无数据：改变日期/区域；缺失时点本来没有行，不能当成消费量为零。
- DB already exists：为避免误删，脚本默认拒绝覆盖；只有确定要重建时使用 --reset。
- Windows：用 `py`，解压后在项目目录打开终端。测试已在当前 Linux 环境执行，macOS/Windows 按标准库兼容设计但未在实体设备验证。
- 项目无密码配置，无真实业务数据。仅本机开发使用，不向公网发布。
