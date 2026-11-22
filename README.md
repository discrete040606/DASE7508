# DASE7508：多用户 Agent 的跨用户记忆泄露实验

这个项目考察多用户 Agent 共用记忆库时的隔离问题：缺少所有权过滤的检索会不会将其他用户的记忆带入回答；加入过滤后，正常检索是否受影响。

## 当前状态

代码包括 Agent、身份过滤、批量实验和中文演示页面。

**真实正式实验已完成：300/300，零错误。** 结果与原始证据见 [正式实验摘要](results/README.md)。

实验只使用合成记忆，用户身份由本地程序模拟。

## 项目导航

```text
Agent project/
├── README.md             安装、运行与项目说明：从这里开始
├── demo.py               中文网页入口
├── launch_demo.command   Mac 双击启动网页
├── memory_lab/           核心代码：数据 → 检索 → Agent → 评估 → 实验
├── configs/              实验参数
├── data/                 记忆、查询和评估答案
├── tests/                自动测试
└── results/              正式实验的原始记录、表格和图表
```

读代码可从 [Agent 入口](memory_lab/agent.py) 开始，沿 [可信会话与检索](memory_lab/retrieval.py)、[评估](memory_lab/evaluation.py)、[批量运行](memory_lab/runner.py) 和 [汇总](memory_lab/analysis.py) 查看。

隐藏目录 `.venv/`、`.python/` 是运行环境；`.local/` 保存下载模型、向量索引和缓存，其中 `runtime/budget.json` 是累计费用账本，不要删除。密钥 `.env` 和这些本地文件都不会上传。

## 安装

开发及验证环境：macOS、Python 3.11；使用 POSIX 文件锁，因此 Windows 应通过 WSL 运行。所有依赖版本见 `requirements.lock.txt`。

```bash
git clone https://github.com/discrete040606/DASE7508.git
cd DASE7508
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.lock.txt
python -m pip install --no-deps -e .
memory-lab prepare
memory-lab validate
memory-lab index
```

`prepare` 生成 100 条记忆、30 个用例和评估答案，`validate` 检查这些文件。`index` 首次使用时下载约 80 MB 的向量模型，并建立共享 Chroma collection；模型和索引保存在 `.local/`。再次执行会检查现有索引，数据不匹配时会报错。

## 离线检查

```bash
python -m pytest -q
memory-lab run --offline --output results/offline/check
memory-lab analyze results/offline/check
```

离线运行使用回显检索记录的测试夹具，检查 300 个槽位和日志、统计、作图流程，每组 A/B/C/D 各 75 个。它不调用 DeepSeek，输出保存在 `results/offline/`，图中标有离线字样。没有本地索引时，核心单元测试仍可运行，网页集成测试会跳过。

## 中文网页

```bash
streamlit run demo.py --server.address 127.0.0.1 --server.headless true --browser.gatherUsageStats false
```

Mac 用户也可以双击 `launch_demo.command`，随后打开终端显示的 localhost 地址。页面默认离线演示；真实模式使用下节说明的本地密钥。

页面可以选择用户、输入英文查询、使用 M1–M8 模板，并对照查看开关防御后的回答与检索记录。提交按钮触发请求，刷新页面不会重复调用；切换身份或模式会清空对话。用户选择器属于实验操作员控制，聊天中的身份声明不能修改可信会话。观察面板仅供评估者查看。

## 真实实验

在环境变量或项目根目录的 `.env` 中填写 `DEEPSEEK_API_KEY`。环境变量优先，文件中的值按原样读取；密钥仅在本地使用。以下示例使用新的运行目录，已有的 `v1` 归档用于查看结果。

```bash
# 在本地 .env 填好密钥，或在终端 export DEEPSEEK_API_KEY 后运行。
memory-lab run --pilot --output results/pilot/reproduction
memory-lab analyze results/pilot/reproduction
# 检查试跑日志，冻结代码、依赖、数据和配置并提交 Git，再执行：
memory-lab run --output results/formal/reproduction
memory-lab analyze results/formal/reproduction
memory-lab budget
```

默认配置采用 DeepSeek 官方 Chat Completions：`deepseek-flash`、关闭思考、temperature=0.2、top_k=5，规划/回答输出上限为 256/512 tokens。完整参数在 `configs/experiment.yaml`。

重试仅限限流、超时和暂时服务错误，最多两次；认证错误、模型不可用等永久错误会停止运行。单次超时 60 秒。程序不自动换模型。模型服务别名可能由服务商更新；保存请求标识、返回模型和运行日期不能保证服务端权重永远不变，这是复现限制。

试跑共 24 个 trial（4 条合法＋8 类攻击，每条两个模式各一次）；正式运行共 300 个 trial。M7 含三轮，完整正式运行正常情况下需要约 680 次模型请求，重试另计。数据、系统提示和参数在条件之间一致；模型生成的检索改写可能不同，实际改写全部留痕。

### 续跑和预算

- 续跑需要相同的代码提交、数据、配置和依赖环境；再次执行同一命令会跳过已完成槽位。`--limit 2` 可用于分段检查。
- 重试使用新会话，旧尝试和中断检查点仍保留。已观察到的泄露不会因后来的安全回答而消失。
- 网页、试跑和正式实验共用 `.local/runtime/budget.json`。每次请求先预留费用，累计上限为 20 美元；缺少 usage 时保留预留金额。估算使用高峰价格，实际账单以服务商为准。
- 文件锁限制同一时间只有一个实验或网页请求运行。配置变化后使用新版本目录。

## 检索边界与核查

模型工具只接收查询文本。应用从已签发的模拟会话取得用户 ID，开启过滤时把所有权条件传给 Chroma。无效会话无法查询，数据库错误也不会触发无过滤查询。两种过滤模式共用同一记忆库、系统提示和检索参数。实验期间记忆只读，评估答案仅供评估程序使用。

[正式实验结果](results/README.md)说明了四组设置、指标口径、检测范围和原始证据。助教可以用保存的日志重新计算结果，无需 DeepSeek 密钥。冻结版本和输入都可从运行目录的清单与快照核对。

## 项目贡献与 AI 协助

杨凌峰负责项目协调和整合。Codex 协助搭建仓库、实现和检查代码、运行与分析试跑及正式实验，以及整理代码和文档。实际验证范围见关联 PR。课程提交中的成员个人贡献以组员核实后的记录为准。

参考：[DeepSeek 工具调用](https://api-docs.deepseek.com/guides/tool_calls/)、[DeepSeek 计价](https://api-docs.deepseek.com/quick_start/pricing/)、[Chroma 元数据过滤](https://docs.trychroma.com/docs/querying-collections/metadata-filtering)。
