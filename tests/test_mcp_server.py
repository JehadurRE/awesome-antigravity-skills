"""Tests for the Unified Canva Skills MCP server, auth manager, and remote rotation proxy."""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from mcp_server.auth import AccountManager
from mcp_server.remote_proxy import CanvaRemoteClient, parse_mcp_http_response
from mcp_server.server import UnifiedCanvaMCPServer

REPO_ROOT = Path(__file__).resolve().parent.parent


class TestUnifiedCanvaMCPServer(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = TemporaryDirectory()
        self.state_dir = Path(self.tmp.name)
        self.manager = AccountManager(state_dir=self.state_dir)
        self.server = UnifiedCanvaMCPServer(
            skills_root=REPO_ROOT / "skills",
            manager=self.manager,
        )

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_initialize_and_capabilities(self) -> None:
        resp = self.server.handle_request(
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05"}}
        )
        self.assertIsNotNone(resp)
        result = resp["result"]
        self.assertEqual(result["serverInfo"]["name"], "canva-skills-mcp")
        self.assertIn("tools", result["capabilities"])
        self.assertIn("resources", result["capabilities"])
        self.assertIn("prompts", result["capabilities"])

    def test_list_and_get_skills(self) -> None:
        tools_resp = self.server.handle_request({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
        tool_names = {t["name"] for t in tools_resp["result"]["tools"]}
        self.assertIn("canva_list_skills", tool_names)
        self.assertIn("canva_remote_call", tool_names)
        self.assertIn("canva_inspect_pdf", tool_names)

        list_res = self.server.call_tool("canva_list_skills")
        payload = json.loads(list_res["content"][0]["text"])
        skill_ids = {s["id"] for s in payload["skills"]}
        self.assertEqual(skill_ids, {"canva", "canva-studio", "pptx-presentation-designer"})

        skill_doc = self.server.call_tool("canva_get_skill", {"skill_id": "canva-studio"})
        self.assertIn("Canva Studio", skill_doc["content"][0]["text"])

        ref_doc = self.server.call_tool(
            "canva_get_skill",
            {"skill_id": "canva-studio", "reference": "design-formats-and-grids.md"},
        )
        self.assertIn("social-square", ref_doc["content"][0]["text"])

    def test_resources_and_prompts(self) -> None:
        res_list = self.server.handle_request({"jsonrpc": "2.0", "id": 3, "method": "resources/list"})
        uris = {r["uri"] for r in res_list["result"]["resources"]}
        self.assertIn("skill://canva-studio/SKILL.md", uris)
        self.assertIn("skill://canva-studio/references/canva-mcp-tools.md", uris)

        read_res = self.server.handle_request(
            {
                "jsonrpc": "2.0",
                "id": 4,
                "method": "resources/read",
                "params": {"uri": "skill://canva-studio/SKILL.md"},
            }
        )
        self.assertIn("create-design", read_res["result"]["contents"][0]["text"])

        prompts_resp = self.server.handle_request({"jsonrpc": "2.0", "id": 5, "method": "prompts/list"})
        prompt_names = {p["name"] for p in prompts_resp["result"]["prompts"]}
        self.assertIn("canva-create-design", prompt_names)
        self.assertIn("canva-social-campaign", prompt_names)

        prompt_get = self.server.handle_request(
            {
                "jsonrpc": "2.0",
                "id": 6,
                "method": "prompts/get",
                "params": {
                    "name": "canva-create-design",
                    "arguments": {"format": "instagram_post", "brief": "Product launch"},
                },
            }
        )
        self.assertIn("Product launch", prompt_get["result"]["messages"][0]["content"]["text"])

    def test_layout_spec_presets(self) -> None:
        all_res = self.server.call_tool("canva_get_layout_spec", {"list_all": True})
        presets = json.loads(all_res["content"][0]["text"])["presets"]
        preset_ids = {p["preset_id"] for p in presets}
        self.assertIn("social-square", preset_ids)
        self.assertIn("presentation-16x9", preset_ids)
        self.assertIn("us-letter-3col", preset_ids)

        res = self.server.call_tool("canva_get_layout_spec", {"preset": "us-letter-3col"})
        spec = json.loads(res["content"][0]["text"])["spec"]
        self.assertEqual(spec["dimensions"]["width"], 612.0)
        self.assertEqual(spec["live_area"]["width"], 540.0)
        self.assertEqual(len(spec["grid"]["columns"]), 3)

    def test_multi_account_rotation_on_quota_cooldown(self) -> None:
        self.manager.register_account(
            "account_1",
            "Primary",
            {"access_token": "tok_1", "refresh_token": "ref_1"},
            make_active=True,
        )
        self.manager.register_account(
            "account_2",
            "Secondary",
            {"access_token": "tok_2", "refresh_token": "ref_2"},
            make_active=False,
        )

        calls: list[str] = []

        class MockRemoteClient(CanvaRemoteClient):
            def _raw_rpc(self, method: str, params: dict, access_token: str) -> dict:
                calls.append(access_token)
                if access_token == "tok_1":
                    return {
                        "jsonrpc": "2.0",
                        "id": 1,
                        "result": {
                            "status": "failed",
                            "failure": {"code": "quota_cooldown", "message": "Limit reached"},
                            "_meta": {
                                "com.canva/aiCreditQuotaError": {
                                    "quota_usage": {"cooldown_ends_at": 9999999999}
                                }
                            },
                        },
                    }
                return {"jsonrpc": "2.0", "id": 2, "result": {"status": "completed", "design_id": "D123"}}

        client = MockRemoteClient(manager=self.manager)
        out = client.call_tool("create-design", {"query": "test"})
        self.assertEqual(calls, ["tok_1", "tok_2"])
        self.assertEqual(out["account_id"], "account_2")
        self.assertEqual(out["response"]["result"]["design_id"], "D123")

    def test_sse_parser(self) -> None:
        sse = (
            "event: message\n"
            'data: {"jsonrpc":"2.0","id":1,"result":{"tools":[{"name":"create-design"}]}}\n\n'
        )
        parsed = parse_mcp_http_response(sse, "text/event-stream")
        self.assertEqual(parsed["result"]["tools"][0]["name"], "create-design")


if __name__ == "__main__":
    unittest.main()
