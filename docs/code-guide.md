# 从哪里开始读代码

先把项目理解成一条流水线：**准备记忆 → 建立向量索引 → 用户提问 → 检索记忆 → 生成回答 → 判定泄露 → 汇总结果**。网页和命令行共用这条流水线。

## 第一遍：只看一次提问怎么完成

1. 打开 `data/cases.json`，找 `L01` 和 `A01`。它们分别是正常查询和攻击查询，先看输入是什么。
2. 打开 `memory_lab/models.py`，看 `Memory`、`Session`、`Case` 和 `SearchArgs`。它们约定各模块接收的数据；不需要先研究文件末尾的日志函数。
3. 打开 `memory_lab/agent.py`，从 `Agent.run_case()` 开始。它让模型调用一次工具，执行检索，再把实际结果交给模型回答。
4. 跟进 `memory_lab/retrieval.py` 的 `Retrieval.retrieve()`。最关键的是 `decision["where"]`：开启防御时，所有权来自已签发的会话，不来自查询或模型。
5. 再看同文件的 `Store.query()`：`where` 直接传入 Chroma，然后对授权范围内的记录排序并取前 k 条。
6. 最后看 `memory_lab/evaluation.py` 的 `evaluate()`：L1 看取回的记录属于谁，L2 看回答是否包含其他用户的 canary 或独有事实。

可以沿这一条调用链对照阅读：

```text
demo.py 或 cli.py
  → Agent.run_case()
    → provider.complete(planning=True)  模型提出检索词
    → Retrieval.retrieve()              校验可信身份、构造过滤条件
      → Store.query()                   Chroma 检索
    → provider.complete(planning=False) 模型根据实际记录回答
  → evaluate()                          检查整段对话是否泄露
```

评估答案 `data/ground_truth.json` 只用于最后一步。它没有传给模型。关闭防御和开启防御使用相同的提示词，区别在数据库查询条件。

## 第二遍：看实验怎样批量运行

| 文件 | 要回答的问题 | 建议先读的位置 |
| --- | --- | --- |
| `memory_lab/data.py` | 100 条记忆和 30 个用例从哪里来？ | `generate()`、`validate()` |
| `configs/experiment.yaml` | 模型、k、重复次数和预算是什么？ | 直接查看参数 |
| `memory_lab/runner.py` | 为什么有 300 次实验？如何续跑？ | `slots()`、`run()`，再读 `manifest()` 和 `latest_trials()` |
| `memory_lab/analysis.py` | 如何从日志得到论文表格？ | `analyze()` 中按 condition 分组的循环 |
| `memory_lab/provider.py` | 怎样调用 API、限制费用、处理重试？ | 先 `MockProvider`，再 `DeepSeek.complete()`，最后 `Budget` |
| `memory_lab/paths.py` | 日志和图表保存在哪里？ | 文件名到子目录的映射 |
| `memory_lab/cli.py` | 终端命令对应哪个函数？ | `main()` 的子命令分支 |
| `demo.py` | 中文页面怎么调用后端？ | 提交按钮后的代码，以及身份切换时的历史重置 |

`provider.py` 的离线夹具会直接回显检索内容，只用于检查程序流程。真实研究结论来自已保存的 DeepSeek 实验。

## 第三遍：用结果反查代码

先看 [正式结果](formal-results.md)，再打开 `results/formal/v1/analysis/summary.csv`。随后用一个 trial ID 在 `raw/trials.jsonl` 中找到完整记录：输入、检索条件、所属用户、回答和判定都在里面。`raw/events.jsonl` 是中途检查点，`raw/api.jsonl` 是逐次 API 请求与响应，不需要第一遍全部阅读。

多轮 M7 的三次提问属于一个 trial；任何一轮发生泄露都算阳性。失败或中断不自动算安全，也不删除已有证据。

## 先运行什么

在项目根目录打开终端：

```bash
source .venv/bin/activate
memory-lab validate
python -m pytest -q
./launch_demo.command
```

已有环境可以直接运行；新电脑先按 [README](../README.md) 安装并建索引。网页默认离线，适合先熟悉流程。阅读现有实验不需要重新计费运行，也不需要修改历史结果。

## 哪些目录暂时不用看

- `tests/`：需要理解某条约束时再找对应测试。
- `references/`：老师提供的 PDF 原件。
- `.venv/`、`.python/`：Python 环境，不是项目业务代码。
- `.local/`：下载模型、向量索引、缓存和费用账本。不要整体删除，尤其要保留 `runtime/budget.json`。

设计依据见 [架构](architecture.md) 和 [实验计划](experiment-plan.md)；[验证记录](verification.md)、[分工](team-plan.md)、[AI 使用说明](ai-usage.md)、[提交检查表](submission.md) 在需要准备课程材料时再读。
