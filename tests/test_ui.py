from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_web_refresh_and_identity_reset(monkeypatch, tmp_path):
    from memory_lab.provider import MockProvider
    from memory_lab.models import append_jsonl
    root = Path(__file__).resolve().parents[1]
    if not (root / '.local/chroma/dataset.json').exists():
        import pytest
        pytest.skip('Run memory-lab index for the UI integration test')
    calls = []
    original = MockProvider.complete
    def counted(self, *args, **kwargs):
        calls.append(1)
        return original(self, *args, **kwargs)
    monkeypatch.setattr(MockProvider, 'complete', counted)
    def test_log(path, value):
        append_jsonl(tmp_path / path.name, value)
    monkeypatch.setattr('memory_lab.models.append_jsonl', test_log)
    monkeypatch.setattr('memory_lab.agent.append_jsonl', test_log)
    app = AppTest.from_file(str(root / 'app/demo.py'), default_timeout=30).run()
    assert not app.exception
    submit = next(b for b in app.button if b.label == '提交查询')
    submit.click().run()
    assert not app.exception and len(calls) == 2
    app.run()
    assert len(calls) == 2
    assert len(app.session_state['messages']) == 1
    app.sidebar.selectbox[0].set_value('user_B').run()
    assert not app.exception and app.session_state['messages'] == []
    assert app.session_state['history'] is None
