import json
import unittest
from unittest.mock import patch

import app as app_module


class TeachingAgentApiTestCase(unittest.TestCase):
    def setUp(self):
        self.temp_db = app_module.os.path.join(app_module.BASE_DIR, "instance", "test_teaching_agent.db")
        app_module.app.config["TESTING"] = True
        app_module.app.config["DATABASE_PATH"] = self.temp_db
        app_module.app.config["DEFAULT_API_KEYS"] = {
            "deepseek": "",
            "zhipu": "",
            "tyqw": "",
        }
        app_module.init_db(force=True)
        self.client = app_module.app.test_client()

    def tearDown(self):
        if app_module.os.path.exists(self.temp_db):
            app_module.os.remove(self.temp_db)

    def test_health_endpoint(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["status"], "ok")

    def test_index_uses_local_frontend_assets_only(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn('/static/app.js', html)
        self.assertNotIn('https://cdn.jsdelivr.net/npm/marked/marked.min.js', html)

    def test_default_key_status_endpoint_returns_boolean_map(self):
        app_module.app.config["DEFAULT_API_KEYS"] = {
            "deepseek": "sk-default-12345678",
            "zhipu": "",
            "tyqw": "sk-qwen-12345678",
        }
        response = self.client.get("/api/config/default-keys")
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertTrue(payload["items"]["deepseek"])
        self.assertFalse(payload["items"]["zhipu"])
        self.assertTrue(payload["items"]["tyqw"])

    @patch("app.call_model_api", return_value="这是测试回复")
    def test_chat_roundtrip_persists_to_sqlite(self, mock_call_model_api):
        response = self.client.post(
            "/api/chat",
            data=json.dumps(
                {
                    "model": "deepseek",
                    "api_key": "sk-test-12345678",
                    "messages": [{"role": "user", "content": "你好"}],
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["status"], "success")
        self.assertEqual(payload["chat"]["messages"][-1]["content"], "这是测试回复")
        mock_call_model_api.assert_called_once()

        chat_id = payload["chat"]["chat_id"]
        detail_response = self.client.get(f"/api/chats/{chat_id}")
        self.assertEqual(detail_response.status_code, 200)
        detail_payload = detail_response.get_json()
        self.assertEqual(len(detail_payload["messages"]), 2)

    @patch("app.call_model_api", return_value="这是流式测试回复")
    def test_chat_stream_mode_returns_ndjson_done_event(self, mock_call_model_api):
        response = self.client.post(
            "/api/chat",
            data=json.dumps(
                {
                    "model": "deepseek",
                    "api_key": "sk-test-12345678",
                    "stream": True,
                    "messages": [{"role": "user", "content": "你好"}],
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        body = response.data.decode("utf-8")
        self.assertIn('"type": "status"', body)
        self.assertIn('"type": "delta"', body)
        self.assertIn('"type": "done"', body)
        self.assertIn("这是流式测试回复", body)

    def test_rename_missing_chat_returns_404(self):
        response = self.client.patch(
            "/api/chats/not-found",
            data=json.dumps({"title": "新的标题"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 404)

    @patch("app.call_model_api", return_value="这是答辩模式回复")
    def test_chat_accepts_scene_mode_and_summary_contains_preview(self, mock_call_model_api):
        response = self.client.post(
            "/api/chat",
            data=json.dumps(
                {
                    "model": "deepseek",
                    "scene_mode": "defense",
                    "api_key": "sk-test-12345678",
                    "messages": [{"role": "user", "content": "这是我的课程项目，请帮我模拟答辩。"}],
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["chat"]["messages"][0]["role"], "user")

        list_response = self.client.get("/api/chats")
        self.assertEqual(list_response.status_code, 200)
        list_payload = list_response.get_json()
        self.assertTrue(list_payload["items"][0]["last_message_preview"])
        mock_call_model_api.assert_called_once()

    def test_invalid_scene_mode_returns_400(self):
        response = self.client.post(
            "/api/chat",
            data=json.dumps(
                {
                    "model": "deepseek",
                    "scene_mode": "unsupported-mode",
                    "api_key": "sk-test-12345678",
                    "messages": [{"role": "user", "content": "你好"}],
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_defense_analysis_returns_structured_payload(self):
        response = self.client.post(
            "/api/defense-analysis",
            data=json.dumps(
                {
                    "messages": [{"role": "user", "content": "我的课题是基于多模态的 AI 教学助手。"}]
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["status"], "success")
        self.assertTrue(payload["analysis"]["opening"])
        self.assertEqual(len(payload["analysis"]["questions"]), 5)
        self.assertTrue(payload["analysis"]["followups"])
        self.assertTrue(payload["analysis"]["outline"])
        self.assertTrue(payload["analysis"]["teaching_value"]["learning_goals"])
        self.assertTrue(payload["analysis"]["defense_strategy"]["high_frequency_focus"])
        self.assertTrue(payload["analysis"]["improvement_plan"])
        self.assertTrue(payload["analysis"]["demo_script"])
        self.assertTrue(payload["analysis"]["qa_checklist"])


if __name__ == "__main__":
    unittest.main()
