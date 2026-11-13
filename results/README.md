# 实验结果导航

| 运行 | 用途 | 记录 |
| --- | --- | --- |
| [formal/v1](formal/v1) | 最终真实实验：300/300，零错误 | [汇总表](formal/v1/analysis/summary.csv) · [图表](formal/v1/analysis/security.png) · [完整性核对](formal/v1/analysis/validation.json) |
| [pilot/v2](pilot/v2) | 修正后的真实试跑：24/24 | [汇总表](pilot/v2/analysis/summary.csv) |
| [pilot/v1](pilot/v1) | 初次试跑；保留协议错误供追溯 | [汇总表](pilot/v1/analysis/summary.csv) |
| offline/ | 本地协议测试，不属于研究结果，不上传 GitHub | 用 README 中的离线命令重新生成 |

每次运行均按以下结构归档：

```text
formal/v1/
├── manifest.json      原始冻结配置与代码版本
├── inputs/            memories、ground_truth、schedule 快照
├── raw/               api、events、trials 原始 JSONL
└── analysis/          CSV/JSON 汇总、完整性核对、PNG 图表
```

[正式结果解读](../docs/formal-results.md)解释检测口径与研究限制。原始日志、输入快照、冻结清单和已生成表格/图表的内容在目录整理中保持不变。

重新分析时仍传入整个运行目录，例如 `memory-lab analyze results/formal/v1`；新表格和图表写入 analysis/。请先复制归档再做探索性分析，避免覆盖已归档的派生图表。
