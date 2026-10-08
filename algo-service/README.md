# 算法服务第一周空壳

`python3 algo-service/server.py`，health 位于 8001/health。modelReady=false，未训练、未生成指标。

第三周：先最近 7 天均值/上周同期基线，再 LightGBM，按时间 walk-forward；用训练历史形成 lag/rolling 特征，不读取 anomaly_truth、不使用预测时点未来真实值。主力模型必须与相同回测窗口、相同 horizon 的基线比较，保留切分、版本、种子和 MAE/RMSE/MAPE/R²，未击败基线如实报告。

第四周：完整网格检测缺失，时段/星期条件化处理周期，再做异常阈值；用验证时段选阈值、最后时间段评估 P/R/F1，truth 单独做 join。按点评估全部三类并分别报告，漂移另报事件命中。缺失不能丢掉再评估。算法报告待真实运行后形成，第一周不编写虚构训练报告。
