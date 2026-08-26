"""M0 setup tests. No networking or AI diagnosis coverage."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_python_environment() -> None:
    import sys

    assert sys.version_info.major >= 3


def test_package_imports() -> None:
    import ai
    import config
    import core
    import rules

    assert config.__name__ == "config"
    assert core.__name__ == "core"
    assert ai.__name__ == "ai"
    assert rules.__name__ == "rules"


def test_settings_module_imports() -> None:
    from config.settings import get_openai_api_key, is_openai_configured

    key = get_openai_api_key()
    assert key is None or isinstance(key, str)
    assert isinstance(is_openai_configured(), bool)


def test_no_hardcoded_api_key_in_source() -> None:
    settings_text = (ROOT / "config" / "settings.py").read_text(encoding="utf-8")
    app_text = (ROOT / "app.py").read_text(encoding="utf-8")
    env_example = (ROOT / ".env.example").read_text(encoding="utf-8")

    assert "sk-" not in settings_text
    assert "sk-" not in app_text
    assert env_example.strip() == "OPENAI_API_KEY="


def test_streamlit_application_starts() -> None:
    from streamlit.testing.v1 import AppTest

    app_test = AppTest.from_file(str(ROOT / "app.py"))
    app_test.run()
    assert not app_test.exception
    titles = [element.value for element in app_test.title]
    bodies = [element.value for element in app_test.markdown]
    assert "NetSage AI" in titles
    assert any("System initialized." in str(value) for value in bodies)
