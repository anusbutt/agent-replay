"""Fixed-vector tests for canonical_json + sha256(name + canonical_json(args)) (research R3).

Exact digests pinned so any future change to serialization (key order,
separators, unicode handling) is caught immediately — the fork engine's
hash-fallback tier (constitution III) depends on this being stable and
reproducible across processes.
"""

from app.replay.interceptor import canonical_json, tool_call_hash


def test_canonical_json_sorts_keys():
    assert canonical_json({"b": 1, "a": 2}) == '{"a":2,"b":1}'


def test_canonical_json_compact_separators_no_whitespace():
    assert canonical_json({"a": 1, "b": 2}) == '{"a":1,"b":2}'
    assert " " not in canonical_json({"a": 1, "b": 2})


def test_canonical_json_preserves_unicode_unescaped():
    result = canonical_json({"name": "café", "emoji": "🎉"})
    assert result == '{"emoji":"🎉","name":"café"}'
    assert "\\u" not in result  # ensure_ascii=False — no \uXXXX escapes


def test_canonical_json_sorts_nested_keys_and_preserves_list_order():
    result = canonical_json({"outer": {"z": 1, "a": [3, 2, 1]}, "flag": True, "none": None})
    assert result == '{"flag":true,"none":null,"outer":{"a":[3,2,1],"z":1}}'


def test_tool_call_hash_fixed_vectors():
    assert (
        tool_call_hash("tool_a", {"b": 1, "a": 2})
        == "d040fe7646266f535b67472e03b32493262cb4e271dcccfe200a4c36110e4e1b"
    )
    assert (
        tool_call_hash("unicode_tool", {"name": "café", "emoji": "🎉"})
        == "5eaf3b088605fa83b81fd18b10a1ec3d9910d64ef8ed86eaa3063e87b129b8b4"
    )
    assert (
        tool_call_hash("nested_tool", {"outer": {"z": 1, "a": [3, 2, 1]}, "flag": True, "none": None})
        == "e813015f0a223d35c15c0df1aa57731a3fa6f09597a822c5927ccd867dff2fcd"
    )
    # data contract's illustrative book_appointment example
    assert (
        tool_call_hash("book_appointment", {"day": "saturday", "time": "14:00", "customer_id": "cust_991"})
        == "d3b248ae64f986ea0bd6fea3798904d9cd459140de899cd3f0b4465d9bb7445f"
    )


def test_tool_call_hash_is_order_independent_for_dict_keys():
    """Key insertion order must not affect the hash — only sorted content does."""
    h1 = tool_call_hash("book_appointment", {"day": "saturday", "time": "14:00", "customer_id": "cust_991"})
    h2 = tool_call_hash("book_appointment", {"customer_id": "cust_991", "time": "14:00", "day": "saturday"})
    assert h1 == h2


def test_tool_call_hash_differs_on_any_content_change():
    base = tool_call_hash("book_appointment", {"day": "saturday", "time": "14:00", "customer_id": "cust_991"})
    different_day = tool_call_hash("book_appointment", {"day": "friday", "time": "14:00", "customer_id": "cust_991"})
    different_name = tool_call_hash("cancel_appointment", {"day": "saturday", "time": "14:00", "customer_id": "cust_991"})
    assert base != different_day
    assert base != different_name
