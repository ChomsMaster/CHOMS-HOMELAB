"""Hermes stdio MCP for controlled Codex jobs and consent-gated checkpoints."""
from __future__ import annotations

import json
import os
from pathlib import Path
import select
import subprocess
import sys
import uuid
import re
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    from . import coordinator
except ImportError:  # direct stdio launch
    import coordinator


def registered_memory_target(config_path: Path | None = None) -> str:
    config_path = config_path or Path.home() / ".hermes/config.yaml"
    try:
        config = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        servers = config.get("mcp_servers", {})
        memory_name = next((name for name in ("choms_memory", "choms-memory") if name in servers), None)
        bridge_args = servers[memory_name].get("args", []) if memory_name else []
        target = bridge_args[bridge_args.index("--ssh-target") + 1]
    except (OSError, ValueError, KeyError, TypeError, IndexError):
        raise coordinator.CoordinationError("memory_bridge_not_configured") from None
    if not re.fullmatch(r"[a-z_][a-z0-9_-]*@[a-zA-Z0-9.-]+", target):
        raise coordinator.CoordinationError("memory_bridge_configuration_invalid")
    return target


def _tools(root: Path, state: Path, codex: str) -> dict:
    def call(name: str, args: dict) -> dict:
        _validate(name, args)
        if name == "delegate":
            return coordinator.submit(task=args["task"], workspace=args["workspace"],
                                      workspace_root=root, state_dir=state, codex=codex,
                                      profile=args.get("profile", "omniroute"))
        if name == "status":
            return coordinator.status(job_id=args["job_id"], state_dir=state)
        if name == "result":
            return coordinator.result(job_id=args["job_id"], state_dir=state)
        if name == "cleanup":
            return coordinator.remove(job_id=args["job_id"], state_dir=state,
                                      explicit=args.get("explicit") is True)
        if name == "checkpoint":
            if args.get("user_authorized") is not True:
                raise coordinator.CoordinationError("explicit_checkpoint_authorization_required")
            job = coordinator.status(job_id=args["job_id"], state_dir=state)
            if job["state"] != "succeeded":
                raise coordinator.CoordinationError("checkpoint_requires_successful_job")
            return _memory_checkpoint(args, job, root)
        raise coordinator.CoordinationError("unknown_tool")
    return {"delegate": call}


def _validate(name: str, args: dict) -> None:
    if not isinstance(args, dict):
        raise coordinator.CoordinationError("invalid_arguments")
    fields = {
        "delegate": ({"task", "workspace", "profile"}, {"task", "workspace"}),
        "status": ({"job_id"}, {"job_id"}), "result": ({"job_id"}, {"job_id"}),
        "cleanup": ({"job_id", "explicit"}, {"job_id", "explicit"}),
        "checkpoint": ({"job_id", "summary", "details", "project_id", "topic", "user_authorized"},
                       {"job_id", "summary", "project_id", "user_authorized"}),
    }
    if name not in fields:
        raise coordinator.CoordinationError("unknown_tool")
    allowed, required = fields[name]
    if set(args) - allowed or required - set(args):
        raise coordinator.CoordinationError("invalid_arguments")
    string_limits = {"task": 12_000, "workspace": 4096, "profile": 64, "job_id": 36,
                     "summary": 240, "details": 2000, "project_id": 100, "topic": 120}
    for key, max_length in string_limits.items():
        if key in args and (not isinstance(args[key], str) or not args[key] or len(args[key]) > max_length):
            raise coordinator.CoordinationError("invalid_arguments")
    for key in ("explicit", "user_authorized"):
        if key in args and not isinstance(args[key], bool):
            raise coordinator.CoordinationError("invalid_arguments")


def _memory_checkpoint(args: dict, job: dict, root: Path) -> dict:
    target = registered_memory_target()
    bridge = root / "scripts/memory/choms_memory_mcp.py"
    # The bridge validates the destination and fixes kubectl/SSH command words.
    proc = subprocess.Popen([sys.executable, "-I", str(bridge), "--ssh-target", target,
                             "--client", "hermes"], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.DEVNULL, cwd=root, env=coordinator.execution_env())
    def send(value: dict) -> None:
        assert proc.stdin is not None
        proc.stdin.write(json.dumps(value, separators=(",", ":")).encode() + b"\n")
        proc.stdin.flush()
    def receive(expected_id: int) -> dict:
        assert proc.stdout is not None
        while True:
            ready, _, _ = select.select([proc.stdout], [], [], 120)
            if not ready:
                raise coordinator.CoordinationError("memory_call_timeout")
            line = proc.stdout.readline(262145)
            if not line:
                raise coordinator.CoordinationError("memory_transport_closed")
            if len(line) >= 262145:
                raise coordinator.CoordinationError("memory_response_too_large")
            value = json.loads(line)
            if value.get("id") == expected_id:
                if "error" in value:
                    raise coordinator.CoordinationError("memory_rpc_error")
                return value["result"]
    try:
        send({"jsonrpc":"2.0","id":1,"method":"initialize","params":{
            "protocolVersion":"2025-06-18","capabilities":{},
            "clientInfo":{"name":"choms-coordinator","version":"1"}}})
        receive(1)
        send({"jsonrpc":"2.0","method":"notifications/initialized"})
        send({"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}})
        names = {x.get("name") for x in receive(2).get("tools",[])}
        if names != {"health","propose","remember","review","search","supersede","forget","checkpoint"}:
            raise coordinator.CoordinationError("memory_tool_contract_mismatch")
        send({"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"checkpoint","arguments":{
            "explicit":True,"request_id":str(uuid.uuid4()),"record":{
                "scope":"project","project_id":args["project_id"],
                "summary":args["summary"],"details":args.get("details", ""),
                "topic":args.get("topic", "codex-delegation"),"type":"checkpoint",
                "importance":"high","sensitivity":"internal",
                "source_kind":"user_explicit","source_reference":"user-explicit:hermes-codex:"+job["job_id"]}}}})
        result = receive(3)
        structured = result.get("structuredContent", result)
        if not isinstance(structured, dict) or "ok" not in structured:
            text_blocks = [x.get("text", "") for x in result.get("content", []) if x.get("type") == "text"]
            if len(text_blocks) == 1:
                try:
                    structured = json.loads(text_blocks[0])
                except json.JSONDecodeError:
                    structured = {}
        if structured.get("ok") is False:
            return {"status":"blocked","reason":structured.get("error",{}).get("code","memory_rejected")}
        if structured.get("ok") is not True:
            raise coordinator.CoordinationError("memory_response_invalid")
        return {"status":"recorded"}
    finally:
        if proc.stdin:
            proc.stdin.close()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.terminate()
            proc.wait(timeout=3)


def tool_rows() -> list[dict]:
    return [
        {"name":"delegate","description":"Start one isolated Codex CLI task in an authorized Git workspace. Does not commit or publish.","inputSchema":{"type":"object","properties":{"task":{"type":"string","minLength":1,"maxLength":12000},"workspace":{"type":"string"},"profile":{"type":"string","default":"omniroute"}},"required":["task","workspace"],"additionalProperties":False}},
        {"name":"status","description":"Read the current state of one coordinator job.","inputSchema":{"type":"object","properties":{"job_id":{"type":"string","format":"uuid"}},"required":["job_id"],"additionalProperties":False}},
        {"name":"result","description":"Recover the bounded result for a terminal coordinator job.","inputSchema":{"type":"object","properties":{"job_id":{"type":"string","format":"uuid"}},"required":["job_id"],"additionalProperties":False}},
        {"name":"checkpoint","description":"Record a successful Codex job in CHOMS Memory only after explicit user authorization; the server backup gate still applies.","inputSchema":{"type":"object","properties":{"job_id":{"type":"string","format":"uuid"},"summary":{"type":"string","minLength":1,"maxLength":240},"details":{"type":"string","maxLength":2000},"project_id":{"type":"string","minLength":1,"maxLength":100},"topic":{"type":"string","minLength":1,"maxLength":120},"user_authorized":{"type":"boolean"}},"required":["job_id","summary","project_id","user_authorized"],"additionalProperties":False}},
        {"name":"cleanup","description":"Remove only one terminal job's private task/result record. Requires explicit=true and does not touch its workspace.","inputSchema":{"type":"object","properties":{"job_id":{"type":"string","format":"uuid"},"explicit":{"type":"boolean","const":True}},"required":["job_id","explicit"],"additionalProperties":False}},
    ]


def serve(root: Path, state: Path, codex: str) -> None:
    for line in sys.stdin.buffer:
        try:
            message = json.loads(line)
            method = message.get("method")
            request_id = message.get("id")
            if method == "initialize":
                result = {"protocolVersion":message["params"].get("protocolVersion","2025-06-18"),
                          "capabilities":{"tools":{"listChanged":False}},
                          "serverInfo":{"name":"choms-coordinator","version":"1.0.0"},
                          "instructions":"Use a reviewed OmniRoute Codex profile. Preserve workspaces and sessions. Checkpoint only after explicit user authorization and CHOMS Memory acceptance."}
            elif method == "notifications/initialized":
                continue
            elif method == "tools/list":
                result = {"tools":tool_rows()}
            elif method == "tools/call":
                params = message.get("params",{})
                name, args = params.get("name"), params.get("arguments",{})
                fn = _tools(root, state, codex)["delegate"]
                try:
                    value = fn(name, args)
                    result = {"content":[{"type":"text","text":json.dumps(value,ensure_ascii=False)}],"structuredContent":value}
                except (coordinator.CoordinationError, KeyError, ValueError) as exc:
                    code = str(exc) if isinstance(exc, coordinator.CoordinationError) else "invalid_arguments"
                    result = {"content":[{"type":"text","text":json.dumps({"error":code})}],"isError":True}
            else:
                if request_id is None:
                    continue
                raise ValueError("method_not_found")
            if request_id is not None:
                response = {"jsonrpc":"2.0","id":request_id,"result":result}
                sys.stdout.write(json.dumps(response,separators=(",",":"))+"\n");sys.stdout.flush()
        except Exception:
            if 'request_id' in locals() and request_id is not None:
                sys.stdout.write(json.dumps({"jsonrpc":"2.0","id":request_id,"error":{"code":-32603,"message":"coordinator_error"}})+"\n");sys.stdout.flush()


def main() -> None:
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument("--workspace-root",type=Path,required=True)
    parser.add_argument("--state-dir",type=Path,required=True)
    parser.add_argument("--codex",default="codex")
    args=parser.parse_args()
    serve(args.workspace_root.resolve(strict=True),args.state_dir,args.codex)


if __name__ == "__main__":
    main()
