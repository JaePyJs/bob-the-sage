import socket
from pathlib import Path

from streamlit.testing.v1 import AppTest


APP_PATH = Path(__file__).resolve().parents[2] / "streamlit_app.py"


def test_worked_example_opens_without_credentials_or_network(monkeypatch):
    for env_var in ("GEMINI_API_KEY", "SEMANTIC_SCHOLAR_API_KEY", "DEEPL_API_KEY"):
        monkeypatch.delenv(env_var, raising=False)

    lookup_attempts = []

    def reject_lookup(host, *_args, **_kwargs):
        lookup_attempts.append(host)
        raise AssertionError("The worked example should not resolve remote hosts")

    monkeypatch.setattr(socket, "getaddrinfo", reject_lookup)
    app = AppTest.from_file(str(APP_PATH), default_timeout=15).run()

    assert not app.exception
    assert lookup_attempts == []
    assert app.radio[0].value == "Worked example"
    assert {metric.label: metric.value for metric in app.metric} == {
        "Papers": "4",
        "Checked citations": "4",
    }
    assert len(app.get("graphviz_chart")) == 1
    assert app.table[0].value.to_dict("records") == [
        {"Year": "2015", "Papers": 1, "Citations received": 1},
        {"Year": "2016", "Papers": 0, "Citations received": 0},
        {"Year": "2017", "Papers": 1, "Citations received": 2},
        {"Year": "2018", "Papers": 0, "Citations received": 0},
        {"Year": "2019", "Papers": 1, "Citations received": 1},
        {"Year": "2020", "Papers": 1, "Citations received": 0},
    ]


def test_live_search_can_still_be_selected():
    app = AppTest.from_file(str(APP_PATH), default_timeout=15).run()
    assert not app.exception

    app.radio[0].set_value("Live search").run()

    assert not app.exception
    assert app.text_input[0].label == "Research Topic"
    assert app.button[0].label == "Run Pipeline"
