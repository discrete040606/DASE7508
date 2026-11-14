import json
from pathlib import Path

import httpx
import pytest
from chromadb import EmbeddingFunction
from openai import OpenAI

from memory_lab.data import generate, load
from memory_lab.models import Config, write_json
from memory_lab.provider import DeepSeek, FatalAPIError
from memory_lab.retrieval import Store


class TinyEmbedding(EmbeddingFunction):
    def __init__(self):
        pass

    def __call__(self, input):
        return [[1., float(len(t) % 7), 0.1] for t in input]

    @staticmethod
    def name():
        return 'test-only-tiny'

    def get_config(self):
        return {}

    @staticmethod
    def build_from_config(config):
        return TinyEmbedding()


def make_store(tmp_path):
    generate(tmp_path)
    ms, _, _ = load(tmp_path)
    return Store(tmp_path / 'chroma_db', ms, TinyEmbedding(), initialize=True), ms


def test_actual_chroma_filter_and_idempotent_index(tmp_path):
    store, ms = make_store(tmp_path)
    rows = store.query('query', 5, {'owner_user_id': 'user_C'})
    assert len(rows) == 5 and {r['owner_user_id'] for r in rows} == {'user_C'}
    assert store.query('query', 5, {'owner_user_id': 'nonexistent'}) == []
    rebuilt = Store(tmp_path / 'chroma_db', ms, TinyEmbedding(), initialize=True)
    assert rebuilt.collection.count() == 100
    with pytest.raises(ValueError):
        Store(tmp_path / 'chroma_db', ms[:-1], TinyEmbedding(), initialize=True)
    store.collection.update(ids=[ms[0]['memory_id']], metadatas=[{'owner_user_id': 'user_E', 'topic': ms[0]['topic']}])
    with pytest.raises(ValueError, match='ownership'):
        store.check(ms)


def test_runner_resume_and_freeze(tmp_path, monkeypatch):
    import memory_lab.runner as runner
    store, _ = make_store(tmp_path)
    monkeypatch.setattr(runner, 'Store', lambda *args, **kw: store)
    config = Config()
    (tmp_path / 'pyproject.toml').write_text('[project]\nname="test-fixture"\n')
    path = tmp_path / 'results/offline/resume'
    first = runner.run(tmp_path, config, path, simulated=True, limit=2)
    assert len(first) == 2
    second = runner.run(tmp_path, config, path, simulated=True, limit=2)
    assert len(second) == 4 and all(t['attempt'] == 1 for t in second.values())
    assert all(t['status'] == 'complete' for t in second.values())
    with pytest.raises(ValueError, match='Frozen'):
        runner.run(tmp_path, Config(top_k=3), path, simulated=True, limit=1)
    with pytest.raises(ValueError, match='Offline'):
        runner.run(tmp_path, config, tmp_path / 'results/formal', simulated=True)


def test_interrupted_positive_checkpoint_survives_retry(tmp_path):
    from memory_lab.evaluation import evaluate
    from memory_lab.models import append_jsonl
    from memory_lab.runner import latest_trials
    generate(tmp_path)
    ms, _, gt = load(tmp_path)
    out = tmp_path / 'run'
    write_json(out / 'ground_truth.json', gt)
    write_json(out / 'schedule.json', [{'trial_id': 't1', 'condition': 'B', 'case_id': 'A01', 'repetition': 1}])
    foreign = next(m for m in ms if m['owner_user_id'] == 'user_B')
    partial = {'trial_id': 't1', 'case_id': 'A01', 'kind': 'malicious', 'authenticated_user_id': 'user_A',
               'expected_turns': 1, 'filter_enabled': False, 'top_k': 5, 'status': 'running', 'attempt': 1,
               'turns': [{'completed': False, 'answer': foreign['canary'], 'retrieval': {
                   'records': [foreign], 'completed': True, 'retrieval_ms': 1, 'decision': {'allowed': True, 'latency_ms': 1}}}]}
    append_jsonl(out / 'events.jsonl', {'event': 'trial_checkpoint', 'trial': partial})
    assert latest_trials(out)['t1']['metrics']['l2'] is True
    safe = {**partial, 'attempt': 2, 'status': 'complete', 'turns': [
        {'completed': True, 'answer': 'No memories.', 'retrieval': {
            'records': [], 'completed': True, 'retrieval_ms': 1, 'decision': {'allowed': True, 'latency_ms': 1}}}]}
    append_jsonl(out / 'trials.jsonl', safe)
    recovered = latest_trials(out)['t1']
    assert recovered['attempt'] == 2 and recovered['metrics']['l1'] and recovered['metrics']['l2']


def make_provider(tmp_path, monkeypatch, handler):
    monkeypatch.setenv('DEEPSEEK_API_KEY', 'offline-test-placeholder')
    provider = DeepSeek(tmp_path, Config(), tmp_path / 'api.jsonl')
    provider.client = OpenAI(api_key='offline-test-placeholder', base_url='https://api.deepseek.com',
                             max_retries=0, http_client=httpx.Client(transport=httpx.MockTransport(handler)))
    return provider


def response():
    return {'id': 'fixture', 'object': 'chat.completion', 'created': 1, 'model': 'deepseek-flash',
            'choices': [{'index': 0, 'finish_reason': 'stop', 'message': {'role': 'assistant', 'content': 'hello'}}],
            'usage': {'prompt_tokens': 10, 'completion_tokens': 10, 'total_tokens': 20}}


def test_provider_retry_payload_and_no_credentials_in_logs(tmp_path, monkeypatch):
    payloads = []
    def handler(request):
        payloads.append(json.loads(request.content))
        if len(payloads) == 1:
            return httpx.Response(429, json={'error': {'message': 'rate limited'}})
        return httpx.Response(200, json=response())
    monkeypatch.setattr('memory_lab.provider.time.sleep', lambda _: None)
    provider = make_provider(tmp_path, monkeypatch, handler)
    provider.complete([{'role': 'user', 'content': 'hello'}], True)
    assert len(payloads) == 2 and provider.request_count == 2
    assert payloads[-1]['thinking'] == {'type': 'disabled'}
    assert payloads[-1]['tool_choice']['function']['name'] == 'search_memory'
    journal = (tmp_path / 'api.jsonl').read_text()
    assert 'offline-test-placeholder' not in journal
    assert len([json.loads(l) for l in journal.splitlines() if json.loads(l)['event'] == 'request']) == 2
    assert provider.budget.read()['spent_upper_usd'] > provider.budget.read()['measured_peak_estimate_usd']


def test_provider_fatal_errors_are_not_retried(tmp_path, monkeypatch):
    requests = []
    def handler(request):
        requests.append(1)
        return httpx.Response(401, json={'error': {'message': 'bad credentials'}})
    provider = make_provider(tmp_path, monkeypatch, handler)
    with pytest.raises(FatalAPIError):
        provider.complete([{'role': 'user', 'content': 'hi'}], True)
    assert len(requests) == 1


def test_summary_denominators_and_plot(tmp_path):
    from memory_lab.analysis import analyze
    from memory_lab.models import append_jsonl
    write_json(tmp_path / 'manifest.json', {'simulated': True})
    write_json(tmp_path / 'schedule.json', [
        {'trial_id': f't{i}', 'case_id': 'unknown', 'condition': 'B', 'repetition': i + 1} for i in range(3)])
    append_jsonl(tmp_path / 'trials.jsonl', {'trial_id': 't0', 'condition': 'B', 'status': 'complete',
                    'metrics': {'l1': True, 'l2': False}, 'cost_upper_usd': .1})
    append_jsonl(tmp_path / 'trials.jsonl', {'trial_id': 't1', 'condition': 'B', 'status': 'error',
                    'metrics': {'l1': False, 'l2': None}, 'cost_upper_usd': .1})
    summary = analyze(tmp_path).iloc[0]
    assert summary.CURR == .5 and summary.CUDR == 0
    assert summary.CURR_n == 2 and summary.CUDR_n == 1
    assert summary.CUDR_unknown == 2 and summary.CUDR_upper == pytest.approx(2 / 3)
    assert summary.errors == 1 and summary.complete == 1
    assert (tmp_path / 'analysis/security.png').exists()


def test_analysis_reads_cost_journal_once_for_all_conditions(tmp_path, monkeypatch):
    from collections import Counter
    import memory_lab.analysis as analysis
    from memory_lab.models import append_jsonl
    from memory_lab.paths import artifact_path
    write_json(tmp_path / 'manifest.json', {'simulated': True})
    schedule = [{'trial_id': c, 'case_id': c, 'condition': c, 'repetition': 1} for c in 'ABCD']
    write_json(tmp_path / 'schedule.json', schedule)
    for slot in schedule:
        append_jsonl(tmp_path / 'trials.jsonl', {**slot, 'status': 'complete',
                     'metrics': {'l1': False, 'l2': False}, 'cost_upper_usd': .1})
    reads = Counter()
    original = analysis.read_jsonl
    def counted(path):
        reads[path] += 1
        return original(path)
    monkeypatch.setattr(analysis, 'read_jsonl', counted)
    summary = analysis.analyze(tmp_path)
    assert summary.cost_upper_usd.sum() == pytest.approx(.4)
    assert reads[artifact_path(tmp_path, 'trials.jsonl')] == 1
