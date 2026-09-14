"""Zero-initialised label combinations: the first real event must be a visible counter step."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from prometheus_client import CollectorRegistry, generate_latest  # noqa: E402

import llm_proxy  # noqa: E402


def test_preinit_creates_zero_series():
    m = llm_proxy.Metrics(CollectorRegistry())
    m.preinit("s1", "m1", ["interactive"])
    text = generate_latest(m.registry).decode()
    base = 'endpoint="chat",model="m1",server="s1",stream="true",thinking="default"'
    assert f'llm_requests_total{{{base},finish_reason="abort",status_class="2xx"}} 0.0' in text \
        or 'finish_reason="abort"' in text
    assert "llm_time_to_first_answer_token_seconds_count{" in text
    assert 'error_type="client_disconnect"' in text
    assert 'slo="interactive"' in text
    for line in text.splitlines():
        if line.startswith(("llm_requests_total{", "llm_request_errors_total{",
                            "llm_time_to_first_answer_token_seconds_count{")):
            assert line.endswith(" 0.0"), line


def test_preinit_is_idempotent_and_cardinality_bounded():
    m = llm_proxy.Metrics(CollectorRegistry())
    m.preinit("s1", "m1", ["a", "b"])
    n1 = len(generate_latest(m.registry).splitlines())
    m.preinit("s1", "m1", ["a", "b"])
    assert len(generate_latest(m.registry).splitlines()) == n1
    assert n1 < 8000
