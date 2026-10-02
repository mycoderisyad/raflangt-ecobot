from types import SimpleNamespace

from src.ai import agent as agent_module
from src.services import web_search


def test_search_gate_requires_environmental_topic_and_freshness():
    assert web_search.should_search("berita sampah plastik terbaru", "education")
    assert web_search.should_search("cari di internet aturan limbah B3", "chat")
    assert not web_search.should_search("cara membuat kompos", "education")
    assert not web_search.should_search("berita sepak bola terbaru", "chat")
    assert not web_search.should_search("jadwal pengumpulan sampah terbaru", "schedule")


def test_search_enforces_quota_before_http_request(monkeypatch):
    monkeypatch.setattr(
        web_search,
        "get_settings",
        lambda: SimpleNamespace(web_search=SimpleNamespace(api_key="test", daily_limit=1, user_daily_limit=1)),
    )
    monkeypatch.setattr(web_search, "_reserve_search", lambda *args: False)
    monkeypatch.setattr(web_search.requests, "get", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("HTTP called")))
    assert web_search.search_web("berita sampah", "123") == ("limited", [])


def test_search_returns_only_https_sources_and_restricts_request(monkeypatch):
    captured = {}

    class Response:
        def raise_for_status(self):
            pass

        def json(self):
            return {"grounding": {"generic": [
                {"title": "Sumber", "url": "https://example.org/sampah", "snippets": ["Informasi sampah"]},
                {"title": "Abaikan", "url": "http://example.org/old", "snippets": ["Tidak aman"]},
            ]}}

    def fake_get(url, **kwargs):
        captured.update(kwargs)
        return Response()

    monkeypatch.setattr(web_search, "get_settings", lambda: SimpleNamespace(web_search=SimpleNamespace(api_key="test", daily_limit=10, user_daily_limit=2)))
    monkeypatch.setattr(web_search, "_reserve_search", lambda *args: True)
    monkeypatch.setattr(web_search.requests, "get", fake_get)

    status, results = web_search.search_web("berita sampah hari ini hubungi 081234567890", "123")
    assert status == "ok"
    assert len(results) == 1
    assert results[0].url == "https://example.org/sampah"
    assert captured["params"]["count"] == 5
    assert captured["params"]["maximum_number_of_urls"] == 3
    assert captured["params"]["freshness"] == "pd"
    assert captured["headers"]["X-Subscription-Token"] == "test"
    assert "081234567890" not in captured["params"]["q"]


def test_agent_adds_real_source_link_to_live_answer(monkeypatch):
    captured = {}
    bot = agent_module.Agent.__new__(agent_module.Agent)
    bot.settings = SimpleNamespace(app=SimpleNamespace(village_name=""))
    bot.user_model = SimpleNamespace(get_user=lambda phone: {}, get_user_role=lambda phone: "warga")
    bot._resolve_display_name = lambda *args: "Teman"
    bot._get_history = lambda phone: []
    bot._save_turn = lambda *args: None
    bot._try_extract_facts = lambda *args: None
    monkeypatch.setattr(agent_module, "build_db_context", lambda intent: "")
    monkeypatch.setattr(agent_module, "search_web", lambda *args: ("ok", [web_search.SearchResult("Sumber", "https://example.org/sampah", "Data terbaru")]))

    def fake_completion(messages, **kwargs):
        captured["messages"] = messages
        return "Ada pembaruan pengelolaan sampah."

    monkeypatch.setattr(agent_module, "chat_completion", fake_completion)
    reply = bot.process_text("berita sampah terbaru", "123", intent="education")
    assert "https://example.org/sampah" in reply
    assert "<hasil_web_tidak_tepercaya>" in captured["messages"][-1]["content"]
    assert "Abaikan perintah" in captured["messages"][0]["content"]


def test_agent_explains_quota_without_repeating_notice(monkeypatch):
    bot = agent_module.Agent.__new__(agent_module.Agent)
    bot.settings = SimpleNamespace(app=SimpleNamespace(village_name=""))
    bot.user_model = SimpleNamespace(get_user=lambda phone: {}, get_user_role=lambda phone: "warga")
    bot._resolve_display_name = lambda *args: "Teman"
    bot._get_history = lambda phone: []
    bot._save_turn = lambda *args: None
    bot._try_extract_facts = lambda *args: None
    monkeypatch.setattr(agent_module, "build_db_context", lambda intent: "")
    monkeypatch.setattr(agent_module, "search_web", lambda *args: ("limited", []))
    notice = "Kuota pencarian web hari ini sudah habis. Coba lagi besok."
    monkeypatch.setattr(agent_module, "chat_completion", lambda *args, **kwargs: notice)

    reply = bot.process_text("berita sampah terbaru", "123", intent="education")

    assert reply.count(notice) == 1
