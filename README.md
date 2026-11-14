# DASE7508：多用户 Agent 的跨用户记忆泄露实验

这个项目考察多用户 Agent 共用记忆库时的隔离问题：缺少所有权过滤的检索会不会将其他用户的记忆带入回答；加入过滤后，正常检索是否受影响。

## 当前状态

代码包括 Agent、身份过滤、批量实验和中文演示页面。

**真实正式实验已完成：300/300，零错误。** 结果与原始证据见 [正式实验摘要](docs/formal-results.md)；两轮试跑和离线验证均单独保存，不混入正式统计。

实验只使用合成记忆，用户身份由本地程序模拟。

## 项目导航

```text
Agent project/
├── src/memory_lab/       核心实验代码
├── app/                  中文演示网页
├── tests/                自动测试
├── configs/              实验参数
├── data/                 合成输入与评估答案
├── results/              正式实验与试跑证据
├── docs/                 设计、结果、验证、协作和提交说明
├── launch_demo.command   双击启动网页
└── .local/               本地索引、模型、缓存、费用账本和工具（不上传）
```

第一次看项目，可先读 [正式实验结果](docs/formal-results.md)，再沿 [文档导航](docs/README.md) 查看设计和验证过程。[结果文件导航](results/README.md)列出了原始日志、输入快照和图表的位置。

本地 Python 环境放在 `.venv/` 和 `.python/`，运行文件集中在 `.local/`。其中 `.local/runtime/budget.json` 保存累计费用，迁移项目时也要保留。密钥 `.env` 和 IDE 设置 `.idea/` 均已加入 Git 忽略规则。

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
streamlit run app/demo.py --server.address 127.0.0.1 --server.headless true --browser.gatherUsageStats false
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

## 指标与证据

L1 / CURR 记录工具是否返回其他用户的记忆，L2 / CUDR 记录这些内容是否出现在回答中。两者分别统计；错误或未完成记录不会自动当作安全结果。合法检索质量、延迟和费用的计算口径见 [实验计划](docs/design/experiment-plan.md)。

每次运行的 `manifest.json` 保存冻结配置和版本哈希；`inputs/` 保存输入快照；`raw/` 保存请求、逐轮检查点和每次尝试。`analysis/` 中的表格与图表由这些记录计算。

[架构图](docs/design/architecture.md)标出了数据流和信任边界，[验证记录](docs/validation/verification.md)列出已执行的检查。评估答案单独保存，程序只把实际检索结果交给模型。共享记忆在实验中保持只读。

## 代码结构与协作

读代码时，可从 `models.py` 的数据结构开始，再看 `retrieval.py` 的会话与过滤、`agent.py` 的调用流程，最后读 `runner.py` 和 `analysis.py`。网页直接复用这些模块。

协作流程见 [CONTRIBUTING.md](CONTRIBUTING.md)，实际贡献和 AI 使用情况单独记录。

项目由杨凌峰发起统一实现。准备课程材料时，请核对 [成员分工](docs/collaboration/team-plan.md)、[AI 使用说明](docs/collaboration/ai-usage.md) 和 [提交检查表](docs/submission/submission-checklist.md)。

参考：[DeepSeek 工具调用](https://api-docs.deepseek.com/guides/tool_calls/)、[DeepSeek 计价](https://api-docs.deepseek.com/quick_start/pricing/)、[Chroma 元数据过滤](https://docs.trychroma.com/docs/querying-collections/metadata-filtering)。
