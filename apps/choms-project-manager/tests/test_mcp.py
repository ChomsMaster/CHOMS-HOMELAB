import unittest
from unittest.mock import Mock

from project_mcp import dispatch


class MCPTests(unittest.TestCase):
    def setUp(self):
        self.api = Mock(return_value={"status": "ok"})

    def rpc(self, method, **params):
        return dispatch(self.api, {"jsonrpc": "2.0", "id": 1, "method": method, "params": params})["result"]

    def test_handshake_and_discovery(self):
        self.assertEqual(self.rpc("initialize")["protocolVersion"], "2025-06-18")
        self.assertEqual(len(self.rpc("tools/list")["tools"]), 6)
        self.assertIsNone(dispatch(self.api, {"jsonrpc": "2.0", "method": "notifications/initialized"}))

    def test_daily_query_and_validation(self):
        self.rpc("tools/call", name="get_daily_plan", arguments={"project_id": "project-a", "date": "2027-02-01", "transport": "publico"})
        self.api.assert_called_once_with("projects/project-a/plan?start=2027-02-01&end=2027-02-01&transport=publico")
        self.assertTrue(self.rpc("tools/call", name="get_daily_plan", arguments={"project_id": "project-a", "date": "2027-02-30"})["isError"])
        self.assertEqual(self.api.call_count, 1)

    def test_completion_and_repair(self):
        self.rpc("tools/call", name="complete_task", arguments={"project_id": "project-a", "id": "fixture-1"})
        self.api.assert_called_with("projects/project-a/tasks/fixture-1/complete", "POST", {})
        fields = dict(project_id="project-a", kind="repair", title="Fixture", date="2027-01-01", actual_minutes=30, revenue_cents=4000, cost_cents=100)
        self.rpc("tools/call", name="log_activity", arguments=fields)
        self.assertEqual(self.api.call_args.args[:2], ("projects/project-a/activities", "POST"))
        self.assertEqual(self.api.call_args.args[2]["kind"], "repair")
        self.assertTrue(self.rpc("tools/call", name="log_activity", arguments={**fields, "cost_cents": -1})["isError"])
