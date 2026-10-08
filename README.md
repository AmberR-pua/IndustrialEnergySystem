# 园区能耗采集与预测预警系统 · 第一周

负责人：任若菡。依照学生版任务书第七节第一周交付，源码原创，业务常量按任务书。

交付包含：分层后端、独立前端/算法进程、八张表、完整种子、参数化造数、全年 CSV 与 truth、需求/接口/数据库文档、自动验证、第一周周报。**统计、定时采集、模型训练及预警属于后续周次，第一周尚未实现模型训练、预测与预警，因此暂无模型评估结果。**

## 运行要求

Python 3.10+；可选 Git。零第三方依赖、不需要 Node、Docker、MySQL 或服务器。macOS/Linux 用 python3，Windows 可把命令中的 python3 换成 py。浏览器建议现代 Chrome/Firefox/Edge。

技术栈调整及 Swagger 说明见 `docs/需求说明.md`。前端使用原生 HTML、CSS 和 JavaScript，实现基础页面、原始数据查询和接口调试；后端使用 Python，数据库使用 SQLite。当前版本无需安装第三方 Python 依赖。

## 从干净目录启动

### 1. 下载项目

在终端执行：

```bash
git clone https://github.com/AmberR-pua/IndustrialEnergySystem.git
cd IndustrialEnergySystem
```

如果已经把项目下载到电脑，直接进入项目根目录即可，无需重复克隆。后面的命令都在项目根目录执行。

### 2. 生成模拟数据并初始化数据库

首次运行时执行：

```bash
python3 db/generate_data.py
python3 db/init_db.py --import-data
```

第一条命令生成模拟能耗数据、异常真值文件和生成报告；第二条命令创建数据库、写入基础信息并导入能耗数据。

如果已经初始化过数据库，可以跳过这一步。

### 3. 验证项目

```bash
python3 scripts/verify.py
python3 scripts/smoke_test.py
```

分别检查数据与数据库，以及三个服务的启动和 HTTP 接口。

### 4. 启动系统

```bash
python3 scripts/run.py
```

该命令同时启动前端、后端和算法服务。启动后，在浏览器中打开：

- 系统页面：http://127.0.0.1:5173
- 接口调试页面：http://127.0.0.1:5173/api.html
- 后端健康检查：http://127.0.0.1:8000/api/health
- 算法服务健康检查：http://127.0.0.1:8001/health

第一周的算法服务提供健康检查接口，模型训练和预测功能将在后续阶段实现。

### 5. 停止与再次启动

在运行服务的终端中按 `Ctrl+C`，即可停止三个服务。

之后再次运行项目，只需执行：

```bash
python3 scripts/run.py
```

无需重复生成数据或初始化数据库。

### 6. 重新建立数据库

如果需要清空现有数据库并重新导入数据，先停止服务，再执行：

```bash
python3 db/init_db.py --reset --import-data
```

注意：`--reset` 会删除现有数据库并重新创建，请确认现有数据不再需要后使用。

### 7. 端口被占用时

可以指定其他端口启动：

```bash
python3 scripts/run.py --backend-port 8100 --frontend-port 5174 --algo-port 8101
```

此时系统页面地址为：http://127.0.0.1:5174。

以上命令适用于 macOS 和 Linux。Windows 可以将命令中的 `python3` 替换为 `py`。

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

`verify.py` 检查模拟数据的完整性、缺失记录与异常真值的对应关系、异常互斥性、漂移窗口与倍率、文件哈希、数据库约束，以及区域及其下级区域的数据过滤、空结果和非法参数。

`smoke_test.py` 使用临时数据库和可用端口启动前端、后端及算法服务，测试 HTTP 接口、前端代理和错误响应，测试结束后关闭进程。

已有验证记录见 `docs/validation.json`、`docs/data-validation.json` 和 `docs/http-validation.json`。`docs/clean-clone-validation.json` 记录的是原始交付版本通过离线 Git bundle 克隆后的运行验证，不代表当前 GitHub 仓库的克隆验证。第一周完成情况见 `docs/weekly/week1.md`。

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
- 无原始数据：初始化时需要添加 `--import-data`。如果尚未创建数据库，执行 `python3 db/init_db.py --import-data`；如果数据库已经存在，且确认可以清空现有内容，再停止服务并执行 `python3 db/init_db.py --reset --import-data`。
- 页面无数据：改变日期/区域；缺失时点本来没有行，不能当成消费量为零。
- DB already exists：为避免误删，脚本默认拒绝覆盖；只有确定要重建时使用 --reset。
- Windows：用 `py`，下载或克隆项目后在项目目录打开终端。测试已在当前 Linux 环境执行，macOS/Windows 按标准库兼容设计但未在实体设备验证。
- 项目无密码配置，无真实业务数据。仅本机开发使用，不向公网发布。
