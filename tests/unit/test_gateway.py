"""Gateway API 单元测试。"""
from __future__ import annotations
import pytest
from httpx import ASGITransport, AsyncClient
from app.gateway.app import create_app
from app.gateway.config import CORSConfig, GatewayConfig
from app.gateway.path_utils import build_resource_path, generate_thread_id, is_valid_thread_id

VALID_TID = "12345678-1234-1234-1234-123456789abc"
INVALID_TID = "not-a-uuid"

@pytest.fixture
def app():
    return create_app()

@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

class TestGatewayConfig:
    def test_defaults(self):
        cfg = GatewayConfig()
        assert cfg.host == "0.0.0.0"
        assert cfg.port == 8001
        assert cfg.debug is False

    def test_cors_defaults(self):
        cors = CORSConfig()
        assert cors.allow_origins == ["*"]
        assert cors.allow_credentials is True

    def test_custom(self):
        cfg = GatewayConfig(port=9000, debug=True)
        assert cfg.port == 9000

class TestPathUtils:
    def test_valid_tid(self):
        assert is_valid_thread_id(VALID_TID) is True

    def test_invalid_tid(self):
        assert is_valid_thread_id("bad") is False

    def test_generate(self):
        assert is_valid_thread_id(generate_thread_id())

    def test_build_path(self):
        assert build_resource_path("x", "artifacts") == "/api/threads/x/artifacts"

class TestCreateApp:
    def test_app_created(self, app):
        assert app.title == "HN Agent Gateway"

    def test_routes_registered(self, app):
        paths = {r.path for r in app.routes}
        assert "/api/models" in paths
        assert "/api/threads" in paths
        assert "/api/agents" in paths
        assert "/api/channels" in paths

class TestModelsRoute:
    @pytest.mark.asyncio
    async def test_list_models(self, client):
        resp = await client.get("/api/models")
        assert resp.status_code == 200
        data = resp.json()
        assert "models" in data
        assert len(data["models"]) > 0

class TestMCPRoute:
    @pytest.mark.asyncio
    async def test_list_mcp(self, client):
        resp = await client.get("/api/mcp")
        assert resp.status_code == 200
        assert "servers" in resp.json()

class TestSkillsRoute:
    @pytest.mark.asyncio
    async def test_list_skills(self, client):
        resp = await client.get("/api/skills")
        assert resp.status_code == 200
        assert "skills" in resp.json()

class TestMemoryRoute:
    @pytest.mark.asyncio
    async def test_get_memory(self, client):
        resp = await client.get("/api/memory")
        assert resp.status_code == 200
        assert "entries" in resp.json()

    @pytest.mark.asyncio
    async def test_put_memory(self, client):
        resp = await client.put("/api/memory", json={"entries": [{"key": "k1", "content": "v1"}]})
        assert resp.status_code == 200
        assert resp.json()["updated"] == 1

    @pytest.mark.asyncio
    async def test_put_memory_invalid(self, client):
        resp = await client.put("/api/memory", json={"bad": "data"})
        assert resp.status_code == 422

class TestUploadsRoute:
    @pytest.mark.asyncio
    async def test_upload_file(self, client):
        resp = await client.post(
            f"/api/threads/{VALID_TID}/uploads",
            files={"file": ("test.txt", b"hello world", "text/plain")},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["filename"] == "test.txt"
        assert data["size"] == 11

    @pytest.mark.asyncio
    async def test_upload_invalid_tid(self, client):
        resp = await client.post(
            f"/api/threads/{INVALID_TID}/uploads",
            files={"file": ("f.txt", b"x", "text/plain")},
        )
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_upload_no_file(self, client):
        resp = await client.post(f"/api/threads/{VALID_TID}/uploads")
        assert resp.status_code == 422

class TestThreadsRoute:
    @pytest.mark.asyncio
    async def test_list_threads(self, client):
        resp = await client.get("/api/threads")
        assert resp.status_code == 200
        assert "threads" in resp.json()

    @pytest.mark.asyncio
    async def test_create_thread(self, client):
        resp = await client.post("/api/threads", json={"title": "Test"})
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "Test"
        assert is_valid_thread_id(data["id"])

    @pytest.mark.asyncio
    async def test_create_thread_default(self, client):
        resp = await client.post("/api/threads", json={})
        assert resp.status_code == 201
        assert resp.json()["title"] == "新对话"

    @pytest.mark.asyncio
    async def test_chat_invalid_tid(self, client):
        resp = await client.post(f"/api/threads/{INVALID_TID}/chat", json={"message": "hi"})
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_chat_empty_message(self, client):
        resp = await client.post(f"/api/threads/{VALID_TID}/chat", json={"message": "   "})
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_chat_missing_message(self, client):
        resp = await client.post(f"/api/threads/{VALID_TID}/chat", json={})
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_chat_sse(self, client):
        resp = await client.post(f"/api/threads/{VALID_TID}/chat", json={"message": "hello"})
        assert resp.status_code == 200
        assert "text/event-stream" in resp.headers.get("content-type", "")

class TestArtifactsRoute:
    @pytest.mark.asyncio
    async def test_list_artifacts(self, client):
        resp = await client.get(f"/api/threads/{VALID_TID}/artifacts")
        assert resp.status_code == 200
        assert "artifacts" in resp.json()

    @pytest.mark.asyncio
    async def test_invalid_tid(self, client):
        resp = await client.get(f"/api/threads/{INVALID_TID}/artifacts")
        assert resp.status_code == 400

class TestSuggestionsRoute:
    @pytest.mark.asyncio
    async def test_list_suggestions(self, client):
        resp = await client.get(f"/api/threads/{VALID_TID}/suggestions")
        assert resp.status_code == 200
        assert "suggestions" in resp.json()

    @pytest.mark.asyncio
    async def test_invalid_tid(self, client):
        resp = await client.get(f"/api/threads/{INVALID_TID}/suggestions")
        assert resp.status_code == 400

class TestAgentsRoute:
    @pytest.mark.asyncio
    async def test_list_agents(self, client):
        resp = await client.get("/api/agents")
        assert resp.status_code == 200
        assert "agents" in resp.json()

    @pytest.mark.asyncio
    async def test_create_agent(self, client):
        resp = await client.post("/api/agents", json={"name": "TestAgent", "model": "claude-3-sonnet"})
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "TestAgent"
        assert data["model"] == "claude-3-sonnet"

    @pytest.mark.asyncio
    async def test_create_agent_default_model(self, client):
        resp = await client.post("/api/agents", json={"name": "A1"})
        assert resp.status_code == 201
        assert resp.json()["model"] == "gpt-4o"

    @pytest.mark.asyncio
    async def test_create_agent_empty_name(self, client):
        resp = await client.post("/api/agents", json={"name": "  "})
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_create_agent_missing_name(self, client):
        resp = await client.post("/api/agents", json={})
        assert resp.status_code == 422

class TestChannelsRoute:
    @pytest.mark.asyncio
    async def test_list_channels(self, client):
        resp = await client.get("/api/channels")
        assert resp.status_code == 200
        assert "channels" in resp.json()

    @pytest.mark.asyncio
    async def test_create_channel(self, client):
        resp = await client.post("/api/channels", json={"name": "My Feishu", "type": "feishu"})
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "My Feishu"
        assert data["type"] == "feishu"

    @pytest.mark.asyncio
    async def test_create_channel_invalid_type(self, client):
        resp = await client.post("/api/channels", json={"name": "Bad", "type": "discord"})
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_create_channel_empty_name(self, client):
        resp = await client.post("/api/channels", json={"name": "  ", "type": "slack"})
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_create_channel_missing_fields(self, client):
        resp = await client.post("/api/channels", json={})
        assert resp.status_code == 422
