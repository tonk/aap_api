#!/usr/bin/env python3
"""Convert Bruno .bru collections under bruno/ to Postman Collection v2.1 + environments."""

from __future__ import annotations

import json
import re
import uuid
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BRUNO = ROOT / "bruno"


def gen_id() -> str:
    return str(uuid.uuid4())


def extract_blocks(text: str) -> list[tuple[str, str]]:
    lines = text.splitlines()
    blocks: list[tuple[str, str]] = []
    i = 0
    n = len(lines)
    block_start = re.compile(r"^([a-zA-Z][a-zA-Z0-9_:-]*) \{$")
    while i < n:
        m = block_start.match(lines[i])
        if not m:
            i += 1
            continue
        block_type = m.group(1)
        i += 1
        depth = 1
        body_start = i
        while i < n and depth:
            for ch in lines[i]:
                if ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
            i += 1
        inner = "\n".join(lines[body_start : i - 1])
        blocks.append((block_type, inner))
    return blocks


def block_kv(body: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in body.splitlines():
        m = re.match(r"^\s*(\w+):\s*(.*)$", line)
        if not m:
            continue
        out[m.group(1)] = m.group(2).strip()
    return out


def meta_name_and_seq(blocks) -> tuple[str, int]:
    name = "request"
    seq = 9999
    for bt, inner in blocks:
        if bt != "meta":
            continue
        for line in inner.splitlines():
            if m := re.match(r"^\s*name:\s*(.+)$", line):
                name = m.group(1).strip()
            elif m := re.match(r"^\s*seq:\s*(\d+)\s*$", line):
                seq = int(m.group(1))
    return name, seq


def parse_headers(body: str) -> list[dict]:
    rows: list[dict] = []
    for line in body.splitlines():
        m = re.match(r"^\s*([^:]+):\s*(.+)$", line)
        if not m:
            continue
        key, val = m.group(1).strip(), m.group(2).strip()
        rows.append({"key": key, "value": val, "type": "text"})
    return rows


def extract_json_body(inner: str) -> str:
    s = inner.strip()
    i = s.find("{")
    if i < 0:
        return ""
    depth = 0
    for j in range(i, len(s)):
        if s[j] == "{":
            depth += 1
        elif s[j] == "}":
            depth -= 1
            if depth == 0:
                return s[i : j + 1]
    return s[i:]


def bruno_script_to_postman(inner: str, default_var: str) -> list[str]:
    """Map Bruno post-response script to Postman Tests tab (exec lines)."""
    var = "hubToken" if "hubToken" in inner else default_var
    return [
        "const body = pm.response.json();",
        "const t = body && (body.token || body.access_token);",
        "if (pm.response.code >= 200 && pm.response.code < 300 && t) {",
        f'    pm.environment.set("{var}", t);',
        "}",
    ]


def http_method_and_req(blocks) -> tuple[str | None, dict[str, str]]:
    for bt, inner in blocks:
        if bt in ("get", "post", "put", "patch", "delete", "head", "options"):
            return bt.upper(), block_kv(inner)
    return None, {}


def auth_from_blocks(blocks) -> tuple[dict | None, dict[str, str]]:
    basic_user = basic_pass = ""
    bearer_token = ""
    for bt, inner in blocks:
        if bt == "auth:basic":
            kv = block_kv(inner)
            basic_user = kv.get("username", "")
            basic_pass = kv.get("password", "")
        elif bt == "auth:bearer":
            kv = block_kv(inner)
            bearer_token = kv.get("token", "")
    if basic_user or basic_pass:
        return (
            {
                "type": "basic",
                "basic": [
                    {"key": "username", "value": basic_user, "type": "string"},
                    {"key": "password", "value": basic_pass, "type": "string"},
                ],
            },
            {"username": basic_user, "password": basic_pass},
        )
    if bearer_token:
        return (
            {
                "type": "bearer",
                "bearer": [
                    {"key": "token", "value": bearer_token, "type": "string"},
                ],
            },
            {"token": bearer_token},
        )
    return None, {}


def parse_env_bru(path: Path) -> tuple[list[dict], list[str]]:
    text = path.read_text(encoding="utf-8")
    secrets: list[str] = []
    sm = re.search(r"vars:secret \[\s*([\s\S]*?)\s*\]", text)
    if sm:
        secrets = re.findall(r"\b(\w+)\b", sm.group(1))
        text = text[: sm.start()] + text[sm.end() :]
    blocks = extract_blocks(text)
    vars_block = ""
    for bt, inner in blocks:
        if bt == "vars":
            vars_block = inner
    values: list[dict] = []
    secret_set = set(secrets)
    seen: set[str] = set()
    for line in vars_block.splitlines():
        m = re.match(r"^\s*(\w+):\s*(.*)$", line)
        if not m:
            continue
        key, raw = m.group(1), m.group(2).strip()
        if raw.startswith('"') and raw.endswith('"'):
            val = raw[1:-1]
        else:
            val = raw
        entry: dict = {
            "key": key,
            "value": val,
            "enabled": True,
        }
        if key in secret_set:
            entry["type"] = "secret"
        values.append(entry)
        seen.add(key)
    for key in secrets:
        if key not in seen:
            entry = {"key": key, "value": "", "enabled": True, "type": "secret"}
            values.append(entry)
    return values, secrets


def bru_to_request(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    blocks = extract_blocks(text)
    name, seq = meta_name_and_seq(blocks)
    method, req_kv = http_method_and_req(blocks)
    if not method:
        raise ValueError(f"No HTTP method in {path}")
    url_raw = req_kv.get("url", "")
    body_mode = req_kv.get("body", "none")
    req_auth_setting = req_kv.get("auth", "none")

    postman_auth, _hints = auth_from_blocks(blocks)
    headers: list[dict] = []
    for bt, inner in blocks:
        if bt == "headers":
            headers = parse_headers(inner)

    body_obj: dict | None = None
    if body_mode == "json":
        raw_json = ""
        for bt, inner in blocks:
            if bt == "body:json":
                raw_json = extract_json_body(inner)
                break
        body_obj = {
            "mode": "raw",
            "raw": raw_json if raw_json else "{}",
            "options": {"raw": {"language": "json"}},
        }

    events = []
    for bt, inner in blocks:
        if bt != "script:post-response":
            continue
        var = "token"
        if "hubToken" in inner:
            var = "hubToken"
        script_lines = bruno_script_to_postman(inner, var)
        events.append(
            {
                "listen": "test",
                "script": {
                    "exec": script_lines,
                    "type": "text/javascript",
                },
            }
        )

    description = ""
    for bt, inner in blocks:
        if bt == "docs":
            description = inner.strip()

    # Use a string URL (Collection v2.1 allows string | object). If we emit a URL object
    # with `path` but no `host`, Postman rebuilds the request and drops {{baseUrl}},
    # yielding invalid URIs like "http:///api/...".
    req: dict = {
        "name": name,
        "request": {
            "method": method,
            "header": headers,
            "url": url_raw,
        },
    }
    if description:
        req["request"]["description"] = description
    if body_obj is not None:
        req["request"]["body"] = body_obj
    # Bearer/basic on request unless hub-style (auth none + Authorization header)
    if req_auth_setting != "none" and postman_auth:
        req["request"]["auth"] = postman_auth
    elif req_auth_setting == "none" and postman_auth:
        # shouldn't happen
        pass
    if events:
        req["event"] = events
    req["_seq"] = seq
    return req


def build_collection(collection_dir: Path, bruno_meta_name: str) -> dict:
    """collection_dir is e.g. bruno/aap_2.5 (contains *.bru in subdirs, bruno.json)."""
    by_folder: dict[str, list[tuple[int, str, dict]]] = defaultdict(list)

    for bru in sorted(collection_dir.rglob("*.bru")):
        rel = bru.relative_to(collection_dir)
        if rel.parts and rel.parts[0] == "environments":
            continue
        folder = rel.parts[0] if len(rel.parts) > 1 else "root"
        data = bru_to_request(bru)
        seq = data.pop("_seq")
        by_folder[folder].append((seq, bru.name, data))

    folder_order = [
        "auth",
        "controller",
        "eda",
        "gateway",
        "hub",
        "legacy",
        "system",
        "workflow",
        "root",
    ]
    items = []
    for folder in folder_order:
        if folder not in by_folder:
            continue
        entries = sorted(by_folder[folder], key=lambda x: (x[0], x[1]))
        sub = [e[2] for e in entries]
        items.append({"name": folder, "item": sub})
    # Any extra folders
    for folder in sorted(by_folder.keys()):
        if folder in folder_order:
            continue
        entries = sorted(by_folder[folder], key=lambda x: (x[0], x[1]))
        items.append({"name": folder, "item": [e[2] for e in entries]})

    return {
        "info": {
            "_postman_id": gen_id(),
            "name": bruno_meta_name,
            "description": f"Imported from Bruno collection: {collection_dir.name}",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
        },
        "variable": [
            {
                "key": "baseUrl",
                "value": "https://your-aap-host.example.com",
                "type": "string",
            },
        ],
        "item": items,
    }


def write_env(name: str, values: list[dict], out_path: Path) -> None:
    env = {
        "id": gen_id(),
        "name": name,
        "values": values,
        "_postman_variable_scope": "environment",
    }
    out_path.write_text(json.dumps(env, indent=2), encoding="utf-8")


def main() -> None:
    out_root = ROOT / "postman"
    out_root.mkdir(exist_ok=True)

    for sub in ("aap_2.5", "aap_2.6"):
        col_dir = BRUNO / sub
        if not col_dir.is_dir():
            continue
        out_dir = out_root / sub
        out_dir.mkdir(parents=True, exist_ok=True)
        meta = json.loads((col_dir / "bruno.json").read_text(encoding="utf-8"))
        name = meta.get("name", sub)
        coll = build_collection(col_dir, name)
        coll_path = out_dir / "Platform_API.postman_collection.json"
        coll_path.write_text(json.dumps(coll, indent=2), encoding="utf-8")
        print("Wrote", coll_path)

        env_dir = col_dir / "environments"
        if env_dir.is_dir():
            for env_bru in sorted(env_dir.glob("*.bru")):
                stem = env_bru.stem
                vals, _ = parse_env_bru(env_bru)
                env_name = f"{name} ({stem})"
                out_e = out_dir / f"{stem}.postman_environment.json"
                write_env(env_name, vals, out_e)
                print("Wrote", out_e)


if __name__ == "__main__":
    main()
