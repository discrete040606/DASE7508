"""中文演示入口。启动：streamlit run demo.py；后端逻辑都在 memory_lab 中。"""

import json
import sys
import uuid
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from memory_lab.cli import prepare_environment

prepare_environment(ROOT)
from memory_lab.agent import Agent
from memory_lab.data import load
from memory_lab.evaluation import evaluate
from memory_lab.paths import artifact_path
from memory_lab.models import Case, Config, USERS, append_jsonl
from memory_lab.provider import Budget, DeepSeek, MockProvider, exclusive
from memory_lab.retrieval import Retrieval, Sessions, Store

st.set_page_config(page_title="DASE7508 共享记忆实验", layout="wide")
st.title("共享记忆访问控制实验")
st.caption("模拟认证 · 仅本地课堂演示 · 英文实验数据 / 中文界面")
config = Config.load(ROOT / "configs/experiment.yaml")


@st.cache_resource
def resources():
    memories, cases, truth = load(ROOT)
    return Store(ROOT / ".local" / "chroma", memories), cases, truth


try:
    store, cases, truth = resources()
except Exception as exc:
    st.info("请先在项目目录运行 memory-lab prepare 和 memory-lab index。")
    st.caption(type(exc).__name__)
    st.stop()

user = st.sidebar.selectbox("模拟用户（实验操作员设置）", USERS)
defence = st.sidebar.toggle("开启身份过滤", value=True)
offline = st.sidebar.toggle("离线协议演示（不是真实模型结果）", value=True)
signature = (user, defence, offline)
# 用户、过滤模式或模型模式变化时清空历史，避免把旧身份的信息带入新会话。
if st.session_state.get("signature") != signature:
    st.session_state.signature = signature
    st.session_state.history = None
    st.session_state.messages = []
    st.session_state.observations = []
    st.session_state.sessions = Sessions()
    st.session_state.session = st.session_state.sessions.create(user)
if st.sidebar.button("清空当前对话"):
    st.session_state.history = None
    st.session_state.messages = []
    st.session_state.observations = []
    st.rerun()
st.sidebar.metric(
    "累计费用上界估算（美元）", f"{Budget(ROOT, config).read()['spent_upper_usd']:.6f}"
)
if offline:
    st.warning("当前是离线协议夹具：回答会直接展示检索记录，不能作为模型泄露实验结论。")

chat_tab, observe_tab, results_tab = st.tabs(
    ["交互演示", "实验观察（操作员专用）", "已保存的实验结果"]
)
with chat_tab:
    templates = {
        "自定义": None,
        **{f"{c.family} · {c.case_id}": c for c in cases if c.kind == "malicious"},
    }
    template = st.selectbox("攻击模板", list(templates))
    selected = templates[template]
    initial = (
        selected.turns[-1]
        if selected
        else "What is the confirmation reference for my project deadline?"
    )
    with st.form("query_form"):
        query = st.text_area("英文查询", initial, key=f"query_{template}", max_chars=2000)
        compare = st.checkbox("同一查询：关闭 / 开启防御对比（使用两个全新会话）")
        submitted = st.form_submit_button("提交查询")
    # Streamlit 每次交互都会重跑脚本；只有点击提交才允许调用模型。
    if submitted and query.strip():
        try:
            with exclusive(ROOT / ".local/runtime/active.lock"):
                demo_dir = ROOT / ("results/offline/demo" if offline else "results/demo")
                provider = (
                    MockProvider()
                    if offline
                    else DeepSeek(ROOT, config, artifact_path(demo_dir, "api.jsonl"))
                )
                case = Case(
                    case_id="DEMO",
                    kind="malicious",
                    attacker_user_id=user,
                    target_user_id=USERS[(USERS.index(user) + 1) % len(USERS)],
                    turns=[query],
                )
                trials = []
                for enabled in ([False, True] if compare else [defence]):
                    session = (
                        st.session_state.sessions.create(user)
                        if compare
                        else st.session_state.session
                    )
                    agent = Agent(
                        Retrieval(store, st.session_state.sessions, config.top_k),
                        provider,
                        artifact_path(demo_dir, "events.jsonl"),
                    )
                    trial, history = agent.run_case(
                        case,
                        session,
                        config,
                        enabled,
                        "demo-" + uuid.uuid4().hex,
                        None if compare else st.session_state.history,
                    )
                    trial["metrics"] = evaluate(trial, truth)
                    append_jsonl(artifact_path(demo_dir, "trials.jsonl"), trial)
                    trials.append(trial)
                    if not compare:
                        st.session_state.history = (
                            history if trial["status"] == "complete" else None
                        )
                st.session_state.observations = trials
                st.session_state.messages.append({"query": query, "trials": trials})
        except Exception as exc:
            st.error(f"请求未完成：{type(exc).__name__}。检查密钥、索引、预算或是否已有实验运行。")
    for exchange in st.session_state.messages:
        with st.chat_message("user"):
            st.write(exchange["query"])
        columns = st.columns(len(exchange["trials"]))
        for column, trial in zip(columns, exchange["trials"]):
            with column:
                st.caption("开启防御" if trial["filter_enabled"] else "关闭防御")
                with st.chat_message("assistant"):
                    st.write(trial["turns"][-1].get("answer") or "本轮未生成完整回答。")
                st.caption(f"状态：{trial['status']}")
with observe_tab:
    st.caption("此处为评估者证据；不提供给攻击脚本或模型。")
    for trial in st.session_state.observations:
        st.subheader("开启防御" if trial["filter_enabled"] else "关闭防御")
        st.json(
            {
                "身份": trial["authenticated_user_id"],
                "状态": trial["status"],
                "L1 跨用户检索": trial["metrics"]["l1"],
                "L2 回答泄露": trial["metrics"]["l2"],
            }
        )
        for turn in trial["turns"]:
            event = turn.get("retrieval", {})
            st.json(event.get("decision", {}))
            st.dataframe(event.get("records", []), use_container_width=True)
        st.json(trial["metrics"]["disclosure_evidence"])
with results_tab:
    summaries = sorted((ROOT / "results").glob("**/summary.json"))
    if not summaries:
        st.info("暂无汇总。运行 memory-lab analyze 后在此查看。")
    else:
        chosen = st.selectbox(
            "结果目录",
            summaries,
            format_func=lambda p: str(
                (p.parent.parent if p.parent.name == "analysis" else p.parent).relative_to(ROOT)
            ),
        )
        st.dataframe(json.loads(chosen.read_text()), use_container_width=True)
        for name in ("security", "utility", "latency"):
            image = chosen.parent / f"{name}.png"
            if image.exists():
                st.image(str(image))
