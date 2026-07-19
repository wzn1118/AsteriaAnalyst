from __future__ import annotations

import hashlib
import json
import mimetypes
import time
import urllib.error
import urllib.request
from datetime import date, datetime
from pathlib import Path
from typing import Any, Callable
import re
import requests

from app.services.path_service import RUNS_DIR
from app.services.settings_service import load_runtime_settings_raw


def _responses_endpoint(base_url: str) -> str:
    root = (base_url or "").strip() or "https://api.openai.com/v1"
    if not root.endswith("/v1"):
        root = f"{root.rstrip('/')}/v1"
    return f"{root.rstrip('/')}/responses"


def _files_endpoint(base_url: str) -> str:
    root = (base_url or "").strip() or "https://api.openai.com/v1"
    if not root.endswith("/v1"):
        root = f"{root.rstrip('/')}/v1"
    return f"{root.rstrip('/')}/files"


def _extract_text(payload: dict[str, Any]) -> str:
    if isinstance(payload.get("output_text"), str) and payload["output_text"].strip():
        return payload["output_text"]

    chunks: list[str] = []
    for output in payload.get("output", []):
        for content in output.get("content", []):
            text = content.get("text") or content.get("value")
            if isinstance(text, str):
                chunks.append(text)
    return "\n".join(chunks).strip()


def _extract_json_from_text(text: str) -> dict[str, Any]:
    stripped = str(text or "").strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?\s*", "", stripped)
        stripped = re.sub(r"\s*```$", "", stripped)
        stripped = stripped.strip()
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", stripped, flags=re.S)
        if match:
            return json.loads(match.group(0))
        raise


def _extract_output_items(payload: dict[str, Any]) -> list[dict[str, Any]]:
    return [item for item in payload.get("output", []) if isinstance(item, dict)]


def _extract_function_calls(payload: dict[str, Any]) -> list[dict[str, Any]]:
    calls: list[dict[str, Any]] = []
    for item in _extract_output_items(payload):
        if item.get("type") == "function_call" and item.get("name") and item.get("call_id"):
            calls.append(item)
    return calls


def _json_default(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, set):
        return list(value)
    item = getattr(value, "item", None)
    if callable(item):
        try:
            return item()
        except Exception:
            pass
    isoformat = getattr(value, "isoformat", None)
    if callable(isoformat):
        try:
            return isoformat()
        except Exception:
            pass
    raise TypeError(f"Object of type {value.__class__.__name__} is not JSON serializable")


CODEX_CACHE_DIR = RUNS_DIR / "codex_cache"
CODEX_CACHE_VERSION = "2026-04-28-v1"


def _cache_payload_signature(
    *,
    kind: str,
    model: str,
    provider_label: str,
    reasoning_effort: str,
    base_url: str,
    system_prompt: str,
    user_payload: dict[str, Any],
    tool_specs: list[dict[str, Any]] | None = None,
) -> str:
    normalized_tool_specs = [
        {
            "name": str(item.get("name") or ""),
            "description": str(item.get("description") or ""),
            "parameters": item.get("parameters") or {},
        }
        for item in (tool_specs or [])
    ]
    raw = json.dumps(
        {
            "cache_version": CODEX_CACHE_VERSION,
            "kind": kind,
            "model": model,
            "provider_label": provider_label,
            "reasoning_effort": reasoning_effort,
            "base_url": base_url.strip(),
            "system_prompt": system_prompt,
            "user_payload": user_payload,
            "tool_specs": normalized_tool_specs,
        },
        ensure_ascii=False,
        sort_keys=True,
        default=_json_default,
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _cache_path(cache_key: str) -> Path:
    CODEX_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return CODEX_CACHE_DIR / f"{cache_key}.json"


def _load_cached_codex_result(cache_key: str) -> dict[str, Any] | None:
    path = _cache_path(cache_key)
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    result = payload.get("result")
    return dict(result) if isinstance(result, dict) else None


def _save_cached_codex_result(cache_key: str, result: dict[str, Any]) -> None:
    path = _cache_path(cache_key)
    payload = {
        "cache_key": cache_key,
        "saved_at": datetime.utcnow().isoformat() + "Z",
        "result": result,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default), encoding="utf-8")


def _cached_result_payload(
    cached: dict[str, Any],
    *,
    model: str,
    provider_label: str,
    reasoning_effort: str,
    default_mode: str,
) -> dict[str, Any]:
    result = dict(cached)
    result["model"] = result.get("model") or model
    result["provider_label"] = result.get("provider_label") or provider_label
    result["reasoning_effort"] = result.get("reasoning_effort") or reasoning_effort
    result["mode"] = result.get("mode") or default_mode
    result["runtime_state"] = "cached"
    result["degradation_state"] = "none"
    result["live_available"] = True
    result["cache_hit"] = True
    return result


GENERIC_FALLBACK_PHRASES: tuple[str, ...] = (
    "这份报告当前最该回答的",
    "这份数据最适合支持什么判断",
    "背景层的职责",
    "这部分",
    "find the most decision-useful",
    "batch robustness evaluation",
    "这份数据更适合按管理会计复盘方式组织",
    "当前数据仍可支持专业初步判断",
    "这层结论只能",
    "若缺少成本",
    "后续所有优化建议都应围绕",
)
FALLBACK_ACTION_TOKENS: tuple[str, ...] = (
    "主推",
    "桥梁",
    "观察",
    "清理",
    "收缩",
    "放量",
    "排查",
    "补货",
    "搭售",
    "承接",
    "复核",
    "风险",
    "扩量",
)


def _is_generic_fallback_line(text: str) -> bool:
    stripped = str(text or "").strip()
    if not stripped:
        return True
    lowered = stripped.lower()
    return any(phrase in lowered for phrase in GENERIC_FALLBACK_PHRASES)


def _has_result_signal(text: str) -> bool:
    stripped = str(text or "").strip()
    if not stripped:
        return False
    if re.search(r"\d", stripped):
        return True
    return any(token in stripped for token in FALLBACK_ACTION_TOKENS)


def _clean_fallback_lines(items: list[Any], *, require_result_signal: bool = False, limit: int = 6) -> list[str]:
    cleaned: list[str] = []
    seen: set[str] = set()
    for item in items:
        text = str(item or "").strip()
        if not text or text in seen or _is_generic_fallback_line(text):
            continue
        if require_result_signal and not _has_result_signal(text):
            continue
        seen.add(text)
        cleaned.append(text)
        if len(cleaned) >= limit:
            break
    return cleaned


def _is_procurement_sales_management_fusion_payload(payload: dict[str, Any]) -> bool:
    fusion_context = payload.get("fusion_context") or {}
    if fusion_context.get("procurement_sales_management"):
        return True
    return str(payload.get("report_lens") or "") == "procurement_sales_review"


def _responses_request(
    body: dict[str, Any],
    settings: dict[str, Any],
    *,
    timeout_seconds: int = 120,
) -> dict[str, Any]:
    api_key = settings.get("api_key", "")
    base_url = settings.get("base_url", "")
    request = urllib.request.Request(
        _responses_endpoint(base_url),
        data=json.dumps(body, ensure_ascii=False, default=_json_default).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
        return json.loads(response.read().decode("utf-8"))


def _is_retryable_codex_error(exc: Exception) -> bool:
    if isinstance(exc, urllib.error.HTTPError):
        return int(getattr(exc, "code", 0) or 0) in {408, 409, 429, 500, 502, 503, 504, 524}
    if isinstance(exc, urllib.error.URLError):
        return True
    if isinstance(exc, TimeoutError):
        return True
    return False


def _upload_file_to_openai(path: Path, settings: dict[str, Any], *, purpose: str = "user_data") -> dict[str, Any]:
    api_key = settings.get("api_key", "")
    base_url = settings.get("base_url", "")
    if not api_key:
        raise RuntimeError("missing_api_key")
    if not path.exists():
        raise FileNotFoundError(f"artifact file not found: {path}")
    mime_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    last_exc: Exception | None = None
    for attempt in range(4):
        try:
            with path.open("rb") as handle:
                response = requests.post(
                    _files_endpoint(base_url),
                    headers={"Authorization": f"Bearer {api_key}"},
                    data={"purpose": purpose},
                    files={"file": (path.name, handle, mime_type)},
                    timeout=300,
                )
            response.raise_for_status()
            return response.json()
        except requests.HTTPError as exc:
            last_exc = exc
            status_code = int(getattr(exc.response, "status_code", 0) or 0)
            if status_code in {408, 409, 429, 500, 502, 503, 504, 524} and attempt < 3:
                time.sleep(min(20.0, 3.0 * (attempt + 1)))
                continue
            raise
        except requests.RequestException as exc:
            last_exc = exc
            if attempt < 3:
                time.sleep(min(20.0, 3.0 * (attempt + 1)))
                continue
            raise RuntimeError(f"file_upload_failed: {exc}") from exc
    raise RuntimeError(f"file_upload_failed: {last_exc}")


def _request_codex_json(
    *,
    system_prompt: str,
    user_payload: dict[str, Any],
    fallback_builder: Callable[[str, dict[str, Any]], dict[str, Any]],
    model_override: str | None = None,
    reasoning_effort_override: str | None = None,
    timeout_seconds: int = 120,
    store: bool = True,
) -> dict[str, Any]:
    settings = load_runtime_settings_raw()
    api_key = settings.get("api_key", "")
    model = model_override or settings.get("model", "gpt-5.4")
    base_url = settings.get("base_url", "")
    provider_label = settings.get("provider_label", "OpenAI Codex API")
    reasoning_effort = reasoning_effort_override or settings.get("reasoning_effort", "xhigh")
    cache_key = _cache_payload_signature(
        kind="request_codex_json",
        model=model,
        provider_label=provider_label,
        reasoning_effort=reasoning_effort,
        base_url=base_url,
        system_prompt=system_prompt,
        user_payload=user_payload,
    )
    cached = _load_cached_codex_result(cache_key)
    if cached:
        return _cached_result_payload(
            cached,
            model=model,
            provider_label=provider_label,
            reasoning_effort=reasoning_effort,
            default_mode="live_codex",
        )

    if not api_key:
        result = fallback_builder("missing_api_key", user_payload)
        result["model"] = model
        result["provider_label"] = provider_label
        result["reasoning_effort"] = reasoning_effort
        result["runtime_state"] = "fallback"
        result["degradation_state"] = "hard_fallback"
        result["fallback_reason"] = "missing_api_key"
        result["live_available"] = False
        return result

    body = {
        "model": model,
        "instructions": system_prompt,
        "input": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": json.dumps(user_payload, ensure_ascii=False, indent=2, default=_json_default),
                    }
                ],
            }
        ],
        "reasoning": {"effort": reasoning_effort},
        "store": store,
    }

    last_exc: Exception | None = None
    max_attempts = 6
    for attempt in range(max_attempts):
        try:
            payload = _responses_request(body, settings, timeout_seconds=timeout_seconds)
            text = _extract_text(payload)
            parsed = json.loads(text)
            parsed["mode"] = "live_codex"
            parsed["model"] = model
            parsed["provider_label"] = provider_label
            parsed["reasoning_effort"] = reasoning_effort
            parsed["runtime_state"] = "live"
            parsed["degradation_state"] = "none"
            parsed["live_available"] = True
            parsed["cache_hit"] = False
            _save_cached_codex_result(cache_key, parsed)
            return parsed
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, json.JSONDecodeError, KeyError) as exc:
            last_exc = exc
            if attempt < max_attempts - 1 and _is_retryable_codex_error(exc):
                time.sleep(min(20.0, 2.5 * (attempt + 1)))
                continue
            break
    if cached:
        return _cached_result_payload(
            cached,
            model=model,
            provider_label=provider_label,
            reasoning_effort=reasoning_effort,
            default_mode="live_codex",
        )
    result = fallback_builder(f"codex_request_failed: {last_exc}", user_payload)
    result["model"] = model
    result["provider_label"] = provider_label
    result["reasoning_effort"] = reasoning_effort
    result["runtime_state"] = "fallback"
    result["degradation_state"] = "hard_fallback"
    result["fallback_reason"] = f"codex_request_failed: {last_exc}"
    result["live_available"] = False
    return result


def _request_codex_agentic_json(
    *,
    system_prompt: str,
    user_payload: dict[str, Any],
    tool_specs: list[dict[str, Any]],
    fallback_builder: Callable[[str, dict[str, Any]], dict[str, Any]],
    max_turns: int = 6,
) -> dict[str, Any]:
    settings = load_runtime_settings_raw()
    api_key = settings.get("api_key", "")
    model = settings.get("model", "gpt-5.4")
    base_url = settings.get("base_url", "")
    provider_label = settings.get("provider_label", "OpenAI Codex API")
    reasoning_effort = settings.get("reasoning_effort", "xhigh")
    cache_key = _cache_payload_signature(
        kind="request_codex_agentic_json",
        model=model,
        provider_label=provider_label,
        reasoning_effort="low",
        base_url=base_url,
        system_prompt=system_prompt,
        user_payload=user_payload,
        tool_specs=tool_specs,
    )
    cached = _load_cached_codex_result(cache_key)
    if cached:
        return _cached_result_payload(
            cached,
            model=model,
            provider_label=provider_label,
            reasoning_effort="low",
            default_mode="live_codex_agentic",
        )

    if not api_key:
        result = fallback_builder("missing_api_key", user_payload)
        result["model"] = model
        result["provider_label"] = provider_label
        result["reasoning_effort"] = reasoning_effort
        result["runtime_state"] = "fallback"
        result["degradation_state"] = "hard_fallback"
        result["fallback_reason"] = "missing_api_key"
        result["live_available"] = False
        return result

    direct_body = {
        "model": model,
        "instructions": system_prompt,
        "input": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": json.dumps(
                            {
                                **user_payload,
                                "agentic_tool_context": {
                                    "tool_names_available_but_not_required": [str(item.get("name") or "") for item in tool_specs],
                                    "instruction": "Use the supplied payload directly and return the requested JSON schema without calling tools unless absolutely necessary.",
                                },
                            },
                            ensure_ascii=False,
                            indent=2,
                            default=_json_default,
                        ),
                    }
                ],
            }
        ],
        "reasoning": {"effort": "low"},
        "store": False,
    }
    try:
        direct_payload = _responses_request(direct_body, settings, timeout_seconds=30)
        direct_text = _extract_text(direct_payload)
        direct_result = json.loads(direct_text)
        direct_result["mode"] = "live_codex_agentic"
        direct_result["model"] = model
        direct_result["provider_label"] = provider_label
        direct_result["reasoning_effort"] = "low"
        direct_result["agentic_tools_used"] = []
        direct_result["runtime_state"] = "live"
        direct_result["degradation_state"] = "none"
        direct_result["live_available"] = True
        direct_result["cache_hit"] = False
        _save_cached_codex_result(cache_key, direct_result)
        return direct_result
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, json.JSONDecodeError, KeyError) as exc:
        result = fallback_builder(f"codex_agentic_direct_request_failed: {exc}", user_payload)
        result["model"] = model
        result["provider_label"] = provider_label
        result["reasoning_effort"] = "low"
        result["runtime_state"] = "local"
        result["degradation_state"] = "soft_local"
        result["fallback_reason"] = f"codex_agentic_direct_request_failed: {exc}"
        result["live_available"] = False
        result["mode"] = "local_deterministic_agentic_substitute"
        result["agentic_tools_used"] = []
        return result

    tool_registry = {item["name"]: item["handler"] for item in tool_specs}
    tools = [
        {
            "type": "function",
            "name": item["name"],
            "description": item["description"],
            "parameters": item["parameters"],
            "strict": True,
        }
        for item in tool_specs
    ]

    body: dict[str, Any] = {
        "model": model,
        "instructions": system_prompt,
        "input": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": json.dumps(user_payload, ensure_ascii=False, indent=2, default=_json_default),
                    }
                ],
            }
        ],
        "reasoning": {"effort": "low"},
        "parallel_tool_calls": True,
        "tool_choice": "auto",
        "tools": tools,
        "store": False,
    }

    try:
        payload = _responses_request(body, settings, timeout_seconds=60)
        turns = 0
        while turns < min(max_turns, 3):
            turns += 1
            function_calls = _extract_function_calls(payload)
            if not function_calls:
                text = _extract_text(payload)
                parsed = json.loads(text)
                parsed["mode"] = "live_codex_agentic"
                parsed["model"] = model
                parsed["provider_label"] = provider_label
                parsed["reasoning_effort"] = reasoning_effort
                parsed["agentic_tools_used"] = [item["name"] for item in tool_specs]
                parsed["runtime_state"] = "live"
                parsed["degradation_state"] = "none"
                parsed["live_available"] = True
                parsed["cache_hit"] = False
                _save_cached_codex_result(cache_key, parsed)
                return parsed

            tool_outputs = []
            for call in function_calls:
                handler = tool_registry.get(str(call.get("name")))
                arguments_raw = call.get("arguments") or "{}"
                try:
                    arguments = json.loads(arguments_raw) if isinstance(arguments_raw, str) else dict(arguments_raw)
                except Exception:
                    arguments = {}
                if handler is None:
                    output = {"error": f"Unknown tool {call.get('name')}"}
                else:
                    output = handler(arguments)
                tool_outputs.append(
                    {
                        "type": "function_call_output",
                        "call_id": call["call_id"],
                        "output": json.dumps(output, ensure_ascii=False, default=_json_default),
                    }
                )

            payload = _responses_request(
                {
                    "model": model,
                    "instructions": system_prompt,
                    "previous_response_id": payload.get("id"),
                    "input": tool_outputs,
                    "reasoning": {"effort": "low"},
                    "parallel_tool_calls": True,
                    "tool_choice": "auto",
                    "tools": tools,
                    "store": False,
                },
                settings,
                timeout_seconds=60,
            )

        raise TimeoutError("agentic_loop_exhausted")
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, json.JSONDecodeError, KeyError) as exc:
        if cached:
            return _cached_result_payload(
                cached,
                model=model,
                provider_label=provider_label,
                reasoning_effort=reasoning_effort,
                default_mode="live_codex_agentic",
            )
        result = fallback_builder(f"codex_agentic_request_failed: {exc}", user_payload)
        result["model"] = model
        result["provider_label"] = provider_label
        result["reasoning_effort"] = reasoning_effort
        result["runtime_state"] = "fallback"
        result["degradation_state"] = "hard_fallback"
        result["fallback_reason"] = f"codex_agentic_request_failed: {exc}"
        result["live_available"] = False
        return result


def _fallback_codex_layer(reason: str, report_context: dict[str, Any]) -> dict[str, Any]:
    executive_summary = report_context.get("executive_summary", [])
    first_summary = executive_summary[0] if executive_summary else "数据已完成自动分析。"
    return {
        "mode": "fallback",
        "reason": reason,
        "board_title": "Codex 高层摘要暂未在线返回，当前展示规则层中文摘要",
        "executive_summary_rewrite": [
            first_summary,
            "建议先围绕质量分、复杂度、关键市场维度和主要结果指标，确认这份数据最适合支持哪类业务判断。",
            "如果后续要形成正式管理汇报，优先把高价值细分、异常波动和下一步动作单独抽成一页。 ",
        ],
        "strategic_recommendations": [
            "优先把头部细分、长尾机会和高增长区域拆开看，不要只看整体平均。",
            "高缺失字段和高异常字段要进入数据治理清单，否则后续策略判断会不稳。",
            "如果报告里已经出现分群、实验机会或市场集中度，就把这些章节转成下一轮专项分析任务。",
        ],
        "risk_flags": [
            "当前是规则层兜底，不是完整的 live Codex 语言综合结果。",
            "若字段命名存在歧义或单位未统一，结论应先视为高质量假设而不是最终事实。",
        ],
        "next_questions": [
            "哪些细分最值得进入经营周报或市场看板？",
            "哪些字段需要补数、重命名或统一口径后再做更深判断？",
            "下一轮应该优先做市场深挖、A/B、因果还是预测？",
        ],
    }


def _fallback_semantic_layer(reason: str, semantic_context: dict[str, Any]) -> dict[str, Any]:
    text_columns = semantic_context.get("text_columns", [])
    numeric_columns = semantic_context.get("numeric_columns", [])
    core_outcomes = semantic_context.get("core_outcomes", [])
    efficiency_metrics = semantic_context.get("efficiency_metrics", [])
    profile_examples = semantic_context.get("profile_examples", {})
    profile_columns = [str(column).lower() for column in semantic_context.get("profile_columns", [])]
    primary_identity = None
    if profile_examples:
        first_key = next(iter(profile_examples))
        values = profile_examples.get(first_key) or []
        if values:
            primary_identity = values[0]

    joined_text = " ".join(
        str(text)
        for values in semantic_context.get("text_samples", {}).values()
        for text in (values or [])
        if text is not None
    )
    subject_type = "generic_subject"
    domain_guess = "综合内容主体"

    if any(token in profile_columns for token in ["screen_name", "username", "handle", "account", "author"]):
        subject_type = "social_account"
        domain_guess = "社交平台主体"
    elif any(token in profile_columns for token in ["customer", "client", "member", "buyer"]):
        subject_type = "customer_entity"
        domain_guess = "客户或用户主体"
    elif any(token in profile_columns for token in ["product", "sku", "item", "goods"]):
        subject_type = "product_entity"
        domain_guess = "产品或商品主体"
    elif any(token in profile_columns for token in ["order", "invoice", "payment", "transaction"]):
        subject_type = "transaction_entity"
        domain_guess = "交易或订单主体"
    elif any(token in profile_columns for token in ["doc", "document", "page", "section", "chapter"]):
        subject_type = "document_entity"
        domain_guess = "文档或内容载体"

    if any(token in joined_text for token in ["军委", "政治局", "中央", "部长", "免职", "调查", "人事"]):
        subject_type = "social_account"
        domain_guess = "中文时政与军政评论主体"
    elif any(token in joined_text.lower() for token in ["finance", "market", "stock", "earnings"]):
        domain_guess = "财经或市场评论主体"
    elif any(token in joined_text for token in ["产品", "增长", "运营", "用户"]):
        domain_guess = "产品与运营观察主体"

    creator_profile = (
        f"{primary_identity} 大概率对应一个{domain_guess}，当前样本显示它主要围绕特定议题持续输出内容。"
        if primary_identity
        else f"从当前样本推断，这组数据更像一个{domain_guess}，而不是纯随机记录。"
    )

    return {
        "mode": "fallback",
        "reason": reason,
        "title": "文本与数值语义层",
        "subject_type": subject_type,
        "creator_profile": creator_profile,
        "content_domains": [
            f"从文本关键词看，当前内容最接近{domain_guess}。",
            "建议结合更多历史样本确认长期定位，而不是只看当前导出窗口。",
            "如果后续要做市场或舆情分析，优先把主题、主体类型和受众先稳定下来。",
        ],
        "audience_profile": [
            "当前内容更像给关注该议题的专业用户、经营角色或高关注受众阅读。",
            "如果是社交内容，互动结构说明它更接近观点传播或讨论场，而不是纯记录流。",
        ],
        "evidence_points": [
            "优先依据字段名、主体字段、样本行和长文本内容共同推断主体角色。",
            "若文本中反复出现行业、人事、价格、地区或渠道词，通常说明它不是泛内容流而是主题型主体。",
            "数值字段的长尾、集中度和高峰样本会共同影响主体判断。",
        ],
        "text_findings": [
            f"优先文本字段包括：{', '.join(text_columns[:3]) or '暂无明显长文本字段'}。",
            "建议继续做主题聚类、高互动文本模式和风险表达识别。",
            "如存在乱码、缩写或平台格式残留，应先做标准化清洗。",
        ],
        "numeric_findings": [
            f"优先数值字段包括：{', '.join(numeric_columns[:4]) or '暂无明显数值字段'}。",
            "建议关注头部峰值、异常样本和波动集中区间。",
            "如果数值字段带业务单位，后续要补充口径映射表。",
        ],
        "metric_cards": [
            {
                "metric": column,
                "role": "核心结果指标" if column in core_outcomes else "过程/效率指标" if column in efficiency_metrics else "重点指标",
                "business_meaning": f"`{column}` 更适合作为当前业务判断里的重点指标之一，需要结合上下游字段一起读。",
                "management_impact": "它会直接影响管理层如何判断规模、效率、风险或资源优先级。",
                "caution": "在口径和单位没有完全确认前，应先把它当成高价值观察指标，而不是最终定论。",
            }
            for column in (core_outcomes + efficiency_metrics + numeric_columns)[:6]
        ],
        "important_columns": text_columns[:3] + numeric_columns[:3],
        "recommended_actions": [
            "先统一字段命名、时间口径和单位口径。",
            "把文本洞察和高波动指标联动分析，不要分开看。",
            "如果目标是经营或市场判断，优先围绕主体、细分和结果指标构建 dashboard 入口。",
        ],
    }


def codex_enhance_report(report_context: dict[str, Any]) -> dict[str, Any]:
    system_prompt = (
        "You are Codex acting as a principal analytics strategist. "
        "Read the structured analysis context and return JSON only. "
        "You must answer in Simplified Chinese. "
        "Turn statistical, structural, semantic, and market findings into a sharper executive layer. "
        "If writer_agent_candidates are provided, choose the most suitable writing stance and narrative cadence from them before drafting the executive layer. "
        "Return keys: board_title, executive_summary_rewrite, strategic_recommendations, risk_flags, next_questions. "
        "Each list should contain 3 to 5 concise Chinese strings. "
        "Do not invent unavailable facts; infer carefully from the provided evidence only."
    )
    tool_specs = [
        {
            "name": "lookup_context",
            "description": "Read a subset of top-level report context fields before making the final executive judgment.",
            "parameters": {
                "type": "object",
                "properties": {
                    "fields": {
                        "type": "array",
                        "items": {"type": "string"},
                    }
                },
                "required": ["fields"],
                "additionalProperties": False,
            },
            "handler": lambda args: {
                key: report_context.get(key)
                for key in [str(item) for item in args.get("fields", [])[:8]]
            },
        },
        {
            "name": "section_snapshot",
            "description": "Read specific section summaries and bullets from the current report draft.",
            "parameters": {
                "type": "object",
                "properties": {
                    "titles": {
                        "type": "array",
                        "items": {"type": "string"},
                    }
                },
                "required": ["titles"],
                "additionalProperties": False,
            },
            "handler": lambda args: {
                "sections": [
                    item
                    for item in report_context.get("section_summaries", [])
                    if item.get("title") in {str(title) for title in args.get("titles", [])}
                ][:6]
            },
        },
    ]
    return _request_codex_agentic_json(
        system_prompt=system_prompt,
        user_payload=report_context,
        tool_specs=tool_specs,
        fallback_builder=_fallback_codex_layer,
    )


def codex_semantic_analysis(semantic_context: dict[str, Any]) -> dict[str, Any]:
    system_prompt = (
        "You are Codex acting as a principal data analyst. "
        "Analyze the semantic meaning of text fields, the business meaning of numeric fields, and the likely profile of the primary subject behind the rows. "
        "You must answer in Simplified Chinese. "
        "Return JSON only with keys: title, subject_type, creator_profile, content_domains, audience_profile, evidence_points, text_findings, numeric_findings, metric_cards, important_columns, recommended_actions. "
        "subject_type should be one of: social_account, customer_entity, product_entity, transaction_entity, document_entity, generic_subject. "
        "creator_profile must be one concise Chinese sentence that directly answers what the primary subject is mainly doing or what kind of subject it is. "
        "The list fields should each contain 3 to 5 concise Chinese bullet strings. "
        "metric_cards must be a list of 3 to 6 concise JSON objects, each with keys: metric, role, business_meaning, management_impact, caution. "
        "For metric_cards, explain what the metric means in business terms, why management should care, and what caveat to keep in mind. "
        "Use the provided headers, profile columns, sample rows, text samples, and metric summaries only; do not invent unsupported facts. "
        "Do not assume the subject is an account unless the evidence supports it. "
        "If the profile is uncertain, explicitly say it is a likely role rather than a confirmed identity."
    )
    tool_specs = [
        {
            "name": "get_text_samples",
            "description": "Fetch sample texts for requested text columns.",
            "parameters": {
                "type": "object",
                "properties": {
                    "columns": {
                        "type": "array",
                        "items": {"type": "string"},
                    }
                },
                "required": ["columns"],
                "additionalProperties": False,
            },
            "handler": lambda args: {
                "text_samples": {
                    column: semantic_context.get("text_samples", {}).get(column, [])
                    for column in [str(item) for item in args.get("columns", [])[:6]]
                }
            },
        },
        {
            "name": "get_numeric_context",
            "description": "Fetch summaries for requested numeric columns.",
            "parameters": {
                "type": "object",
                "properties": {
                    "columns": {
                        "type": "array",
                        "items": {"type": "string"},
                    }
                },
                "required": ["columns"],
                "additionalProperties": False,
            },
            "handler": lambda args: {
                "numeric_summaries": [
                    item
                    for item in semantic_context.get("numeric_summaries", [])
                    if item.get("column") in {str(column) for column in args.get("columns", [])}
                ][:6]
            },
        },
        {
            "name": "get_profile_examples",
            "description": "Fetch profile columns and representative sample values.",
            "parameters": {
                "type": "object",
                "properties": {
                    "columns": {
                        "type": "array",
                        "items": {"type": "string"},
                    }
                },
                "required": ["columns"],
                "additionalProperties": False,
            },
            "handler": lambda args: {
                "profile_examples": {
                    column: semantic_context.get("profile_examples", {}).get(column, [])
                    for column in [str(item) for item in args.get("columns", [])[:6]]
                }
            },
        },
    ]
    return _request_codex_agentic_json(
        system_prompt=system_prompt,
        user_payload=semantic_context,
        tool_specs=tool_specs,
        fallback_builder=_fallback_semantic_layer,
    )


def _fallback_metric_interpretation(reason: str, payload: dict[str, Any]) -> dict[str, Any]:
    metric_candidates = payload.get("metric_candidates", [])[:6]
    numeric_summaries = payload.get("numeric_summaries", [])
    method_findings = payload.get("method_findings", [])
    summary_lookup = {str(item.get("metric")): item for item in numeric_summaries if item.get("metric")}
    method_lookup: dict[str, list[dict[str, Any]]] = {}
    for item in method_findings:
        for metric in item.get("metrics", []):
            method_lookup.setdefault(str(metric), []).append(item)

    cards: list[dict[str, Any]] = []
    for item in metric_candidates:
        metric = str(item.get("metric") or "")
        if not metric:
            continue
        summary = summary_lookup.get(metric, {})
        methods = method_lookup.get(metric, [])
        stat_sentence = ""
        if methods:
            first = methods[0]
            stat_sentence = f" 当前已实跑 `{first.get('method', '统计方法')}`，结论是：{first.get('result', '')}"
        distribution_sentence = ""
        if summary:
            distribution_sentence = (
                f"`{metric}` 当前样本量 {summary.get('n', 'n/a')}，均值 {summary.get('mean', 'n/a')}，"
                f"中位数 {summary.get('median', 'n/a')}，标准差 {summary.get('std', 'n/a')}，"
                f"P25 {summary.get('p25', 'n/a')}，P75 {summary.get('p75', 'n/a')}。"
            )
        cards.append(
            {
                "metric": metric,
                "role": item.get("role", "重点指标"),
                "business_meaning": distribution_sentence or f"`{metric}` 是当前业务判断中的重点指标。",
                "management_impact": (item.get("management_question") or f"它直接服务于 `{payload.get('core_purpose') or payload.get('problem_to_solve') or '当前判断'}`。") + stat_sentence,
                "caution": item.get("caution") or "若口径、单位或分母尚未完全确认，应先把它当作观察指标，不直接写成拍板结论。",
            }
        )
    return {
        "mode": "fallback",
        "reason": reason,
        "metric_cards": cards[:6],
    }


def codex_metric_interpretation(metric_context: dict[str, Any]) -> dict[str, Any]:
    system_prompt = (
        "You are Codex acting as a principal analytics explainer. "
        "You must answer in Simplified Chinese and JSON only. "
        "Your only job is to rewrite key metric explanation cards using the actual dataset summaries and executed statistical results. "
        "Return JSON only with key: metric_cards. "
        "metric_cards must be a list of 3 to 8 concise JSON objects, each with keys: metric, role, business_meaning, management_impact, caution. "
        "Every card must use actual numbers from the provided metric summary when available, such as total/sample size, mean, median, standard deviation, quartiles, ratio, or outlier share. "
        "When a real executed method is available for this metric, mention the actual result in Chinese, such as significance, correlation strength, uplift direction, or whether the evidence is weak. "
        "Do not write generic phrases like '需要结合上下游字段一起读' or '会影响规模效率风险'. "
        "Do not invent methods or conclusions that are not in the payload. "
        "If evidence is weak, say the conclusion should stay at observation level."
    )
    tool_specs = [
        {
            "name": "lookup_metric_summary",
            "description": "Read the numeric summary for selected metrics.",
            "parameters": {
                "type": "object",
                "properties": {
                    "metrics": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["metrics"],
                "additionalProperties": False,
            },
            "handler": lambda args: {
                "numeric_summaries": [
                    item for item in metric_context.get("numeric_summaries", [])
                    if item.get("metric") in {str(metric) for metric in args.get("metrics", [])}
                ][:8]
            },
        },
        {
            "name": "lookup_method_findings",
            "description": "Read executed statistical findings tied to selected metrics.",
            "parameters": {
                "type": "object",
                "properties": {
                    "metrics": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["metrics"],
                "additionalProperties": False,
            },
            "handler": lambda args: {
                "method_findings": [
                    item for item in metric_context.get("method_findings", [])
                    if set(item.get("metrics", [])) & {str(metric) for metric in args.get("metrics", [])}
                ][:8]
            },
        },
    ]
    return _request_codex_agentic_json(
        system_prompt=system_prompt,
        user_payload=metric_context,
        tool_specs=tool_specs,
        fallback_builder=_fallback_metric_interpretation,
    )


def _format_metric_number(value: Any, digits: int = 4) -> str:
    try:
        if value is None:
            return "n/a"
        return f"{float(value):.{digits}f}"
    except Exception:
        return str(value)


def _parse_numberish(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().replace(",", "")
    if not text or text.lower() == "n/a":
        return None
    if text.endswith("%"):
        try:
            return float(text[:-1]) / 100.0
        except Exception:
            return None
    try:
        return float(text)
    except Exception:
        return None


def _format_ratio_as_percent(value: Any) -> str:
    numeric = _parse_numberish(value)
    if numeric is None:
        return "n/a"
    return f"{numeric * 100:.1f}%"


def _method_reviews_are_low_signal(method_reviews: list[dict[str, Any]]) -> bool:
    if not method_reviews:
        return True
    generic_fragments = [
        "服务于当前业务判断",
        "服务于",
        "继续观察",
        "优先级筛选",
        "第一轮动作决策",
        "提供数据依据",
    ]
    concrete_hits = 0
    for review in method_reviews:
        text = " ".join(
            str(review.get(key) or "")
            for key in ["headline", "result_meaning", "business_takeaway", "caution"]
        )
        if any(token in text for token in ["渠道", "活动", "内容", "留存", "转化", "订单", "社群", "日期", "用户"]):
            concrete_hits += 1
        if not any(char.isdigit() for char in text):
            return True
        if sum(fragment in text for fragment in generic_fragments) >= 2:
            return True
    return concrete_hits < max(1, len(method_reviews) // 2)


def _fallback_method_review(reason: str, payload: dict[str, Any]) -> dict[str, Any]:
    report_lens = str(payload.get("report_lens") or "")
    core_purpose = str(payload.get("core_purpose") or payload.get("problem_to_solve") or "当前业务判断")
    background_text = str(payload.get("business_background_text") or "")
    method_reviews: list[dict[str, Any]] = []
    for run in payload.get("method_runs", []):
        method_id = str(run.get("method_id") or "")
        method = str(run.get("method") or method_id or "统计方法")
        target = str(run.get("target") or "当前指标")
        group = str(run.get("group_column") or "")
        metrics = run.get("metrics", {}) or {}
        result_meaning = str(run.get("result_sentence") or "").strip()
        business_takeaway = str(run.get("business_use") or "").strip()
        caution = "这层结论只能服务于当前样本内判断，不能越过口径边界直接写成绝对策略。"

        if method_id == "correlation":
            corr = metrics.get("strongest_correlation")
            p_value = metrics.get("strongest_p_value")
            left = metrics.get("strongest_left")
            right = metrics.get("strongest_right")
            if corr is not None:
                result_meaning = (
                    f"`{left}` 与 `{right}` 的相关系数约 {_format_metric_number(corr, 3)}"
                    + (f"，p值约 {_format_metric_number(p_value, 4)}" if p_value is not None else "")
                    + "。这表示它们在当前样本里是否会同步变化已经有了显式统计证据。"
                )
                if abs(float(corr)) < 0.2:
                    business_takeaway = f"对 `{core_purpose}` 来说，这两个指标不适合并成同一条运营监控链路，后续应分别复盘。"
                elif abs(float(corr)) < 0.5:
                    business_takeaway = f"对 `{core_purpose}` 来说，这两个指标存在中等联动，可以一起看趋势，但还不适合互相替代。"
                else:
                    business_takeaway = f"对 `{core_purpose}` 来说，这两个指标联动已经足够强，适合放进同一条监控链路并继续排查共同驱动因素。"
        elif method_id in {"random_forest", "neural_network", "deep_learning"} and metrics.get("rmse") is not None:
            r_squared = metrics.get("r_squared")
            rmse = float(metrics.get("rmse"))
            mean_actual = metrics.get("mean_actual")
            mae = metrics.get("mae")
            features = [str(item) for item in run.get("features", []) if item]
            relative_error = None
            if mean_actual not in {None, 0}:
                try:
                    relative_error = abs(rmse / float(mean_actual))
                except Exception:
                    relative_error = None
            result_meaning = (
                f"`{target}` 的测试集 R² 约 {_format_metric_number(r_squared, 3)}，RMSE 约 {_format_metric_number(rmse, 3)}"
                + (f"，MAE 约 {_format_metric_number(mae, 3)}" if mae is not None else "")
                + "。这意味着模型做单条预测时，通常会和真实值相差约 "
                + f"{_format_metric_number(rmse, 3)} 个 `{target}` 单位。"
            )
            if relative_error is not None:
                result_meaning += f" 这个误差大约相当于该指标典型水平的 {relative_error * 100:.1f}%。"
                if (
                    report_lens == "internet_ops_review"
                    and relative_error <= 0.02
                    and any(token in "".join(features) for token in ["活跃", "新增", "留存", "转化", "订单", "率"])
                ):
                    business_takeaway = f"对互联网运营复盘来说，这种几乎贴着真实值的预测更像是在复刻现有计数链，说明 `{target}` 与输入指标存在很强口径重叠；它更适合做异常预警、补数和名单排序，不足以直接证明哪个渠道或活动真正驱动了 `{target}`。"
                elif relative_error <= 0.1:
                    business_takeaway = f"对 `{core_purpose}` 来说，这个误差水平已经足够支持对象排序、优先级筛选和第一轮动作决策。"
                elif relative_error <= 0.2:
                    business_takeaway = f"对 `{core_purpose}` 来说，这个误差水平适合做方向判断和对象排序，但不适合把单点预测当成精确承诺。"
                else:
                    business_takeaway = f"对 `{core_purpose}` 来说，这个误差仍然偏大，更适合做风险预警和粗筛，不适合直接下精细动作。"
            else:
                business_takeaway = f"对 `{core_purpose}` 来说，应先结合 `{target}` 的业务单位理解这组误差，再决定是否用于动作优先级。"
            caution = "RMSE 是按目标原始单位计量的平均误差，不是百分比；如果输入变量与目标变量本来就共享同一条计数链，高R²更可能反映口径重叠，而不等于已经识别出真正的业务因果。"
        elif method_id in {"anova", "kruskal", "tukey_hsd", "ttest", "mann_whitney"}:
            p_value = metrics.get("p_value")
            result_meaning = (
                result_meaning
                or f"`{target}` 在 `{group}` 分组下的差异检验 p值约 {_format_metric_number(p_value, 4)}。"
            )
            if p_value is not None and float(p_value) < 0.05:
                if report_lens == "internet_ops_review" and group:
                    business_takeaway = f"对互联网运营复盘来说，`{group}` 已经可以作为一级拆盘维度，后续应继续比较不同 `{group}` 在留存率、转化率和订单承接上的差异，并把动作落到具体渠道、活动或内容主题名单。"
                else:
                    business_takeaway = f"对 `{core_purpose}` 来说，`{group}` 已经是值得单独拆分复盘的业务切片。"
            else:
                if report_lens == "internet_ops_review" and group:
                    business_takeaway = f"对互联网运营复盘来说，当前没有证据说明不同 `{group}` 整体表现已经稳定拉开，不能直接按 `{group}` 大类切预算或定动作，后续应回到 `{group}` × 活动 或 `{group}` × 内容主题 继续拆，并把重点放在订单承接和留存承接更高的对象。"
                else:
                    business_takeaway = f"对 `{core_purpose}` 来说，`{group}` 还不足以单独当成强切片，后续应更多回到对象级复盘。"
        elif method_id in {"chi_square", "fisher_exact"}:
            p_value = metrics.get("p_value")
            strength = metrics.get("cramers_v") or metrics.get("odds_ratio")
            result_meaning = (
                result_meaning
                or f"`{group}` 与 `{target}` 的结构关系 p值约 {_format_metric_number(p_value, 4)}，结构强度约 {_format_metric_number(strength, 4)}。"
            )
            if report_lens == "internet_ops_review" and p_value is not None and float(p_value) >= 0.05:
                business_takeaway = f"对互联网运营复盘来说，`{group}` 与 `{target}` 没有形成稳定绑定关系，说明当前不需要先按固定组合模板复盘，而应先看单个渠道、单个活动各自的承接质量，再决定要不要做组合策略。"
            else:
                business_takeaway = f"对 `{core_purpose}` 来说，这个结果回答的是结构是否真的绑定，而不是数值高低谁更强。"
        elif method_id == "normality":
            p_value = metrics.get("p_value")
            result_meaning = result_meaning or f"`{target}` 的正态性检验 p值约 {_format_metric_number(p_value, 4)}。"
            if report_lens == "internet_ops_review":
                business_takeaway = f"对互联网运营复盘来说，这意味着 `{target}` 的均值很容易被少数高峰日拉高，汇报时必须同时看中位数、P75 和异常窗口，不能只报平均水平。"
            else:
                business_takeaway = f"对 `{core_purpose}` 来说，这个结果决定汇报时更该看均值，还是更该看中位数、分位数和异常窗口。"
        elif method_id == "pca":
            variance = metrics.get("variance_pc1", 0) or 0
            variance += metrics.get("variance_pc2", 0) or 0
            result_meaning = result_meaning or f"前两个主成分累计解释方差约 {_format_metric_number(variance, 4)}。"
            business_takeaway = f"对 `{core_purpose}` 来说，这意味着当前指标体系里已经有一部分信息可以被压缩成少数几个管理维度。"

        if not result_meaning:
            result_meaning = f"{method} 已完成实跑，但当前回退链路没有拿到足够详细的解释字段。"
        if not business_takeaway:
            if report_lens == "internet_ops_review":
                business_takeaway = f"对互联网运营复盘来说，这个结果需要进一步翻译成渠道、活动、内容主题和留存/转化动作。"
            else:
                business_takeaway = f"对 `{core_purpose}` 来说，这个结果需要继续压成对象、指标和动作。"

        if report_lens == "internet_ops_review" and background_text:
            business_takeaway += " 当前建议必须同时服从业务背景里对运营目标、资源分配和策略优化的要求。"

        method_reviews.append(
            {
                "method_id": method_id,
                "method": method,
                "headline": f"{method}说明了什么",
                "result_meaning": result_meaning,
                "business_takeaway": business_takeaway,
                "caution": caution,
            }
        )
    return {
        "mode": "fallback",
        "reason": reason,
        "method_reviews": method_reviews,
    }


def codex_method_review(method_context: dict[str, Any]) -> dict[str, Any]:
    system_prompt = (
        "You are Codex acting as a principal analytics method reviewer. "
        "You must answer in Simplified Chinese and JSON only. "
        "You will receive already executed statistical or machine-learning method results. "
        "Your job is not to repeat the method name, but to explain what the specific numeric result means for the current dataset and business decision. "
        "Return JSON only with key method_reviews. "
        "method_reviews must be a list with one object per executed method, preserving input order. "
        "Each object must contain keys: method_id, method, headline, result_meaning, business_takeaway, caution. "
        "Rules: "
        "1) Use actual numbers from the payload. "
        "2) For p-values, explain whether evidence is strong enough to support a grouping or relationship claim. "
        "3) For correlation, mention coefficient and p-value, and explain whether the pair is strong enough to be monitored together. "
        "4) For R² and RMSE, explain RMSE as average prediction error in the target's own unit, and if mean_actual exists, explain the error share relative to the typical target level. "
        "5) Tie every explanation to the current business purpose and, when possible, to concrete dataset objects such as 渠道、活动、内容主题、媒体、责任中心、项目、客户或地区. "
        "6) Use business_background_text when available, so that business_takeaway explains how the finding should influence the stated business objective, not just analytics process. "
        "7) Avoid generic phrases like '支持渠道投放、活动设计和内容策略优化' unless you name the exact object and the specific decision implication. "
        "8) If evidence is weak, say the result stays at observation level and explain what it cannot yet support."
    )
    tool_specs = [
        {
            "name": "lookup_method_runs",
            "description": "Read selected executed method runs and their metrics before writing reviews.",
            "parameters": {
                "type": "object",
                "properties": {
                    "indexes": {"type": "array", "items": {"type": "integer"}}
                },
                "required": ["indexes"],
                "additionalProperties": False,
            },
            "handler": lambda args: {
                "method_runs": [
                    method_context.get("method_runs", [])[index]
                    for index in args.get("indexes", [])
                    if isinstance(index, int) and 0 <= index < len(method_context.get("method_runs", []))
                ]
            },
        },
        {
            "name": "lookup_business_context",
            "description": "Read selected business-context fields before writing method reviews.",
            "parameters": {
                "type": "object",
                "properties": {
                    "fields": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["fields"],
                "additionalProperties": False,
            },
            "handler": lambda args: {
                key: method_context.get(key)
                for key in [str(item) for item in args.get("fields", [])[:12]]
            },
        },
    ]
    result = _request_codex_agentic_json(
        system_prompt=system_prompt,
        user_payload=method_context,
        tool_specs=tool_specs,
        fallback_builder=_fallback_method_review,
    )
    if result.get("mode") == "fallback":
        return result
    method_reviews = result.get("method_reviews")
    if not isinstance(method_reviews, list) or _method_reviews_are_low_signal(method_reviews):
        return _fallback_method_review("low_signal_method_review", method_context)
    return result


def _fallback_semantic_expansion(reason: str, payload: dict[str, Any]) -> dict[str, Any]:
    semantic_layer = payload.get("semantic_layer", {})
    text_findings = semantic_layer.get("text_findings", [])[:3]
    numeric_findings = semantic_layer.get("numeric_findings", [])[:3]
    actions = semantic_layer.get("recommended_actions", [])[:3]
    rows_by_dimension = payload.get("rows_by_dimension", {}) or {}
    report_lens = str(payload.get("report_lens") or "")
    paragraphs = [
        "从文本层看，这份数据不只是商品或实体清单，而是在名字与标签中已经隐含了较强的业务语义。系统应优先把名称字段拆成品牌、功效、品类或主题，再去看结构和表现差异。",
        "从数值层看，均值与中位数差距明显时，通常意味着头部样本强烈拉高整体，因此不能只看平均水平，而要按头部、腰部、尾部分层去解释结构。",
        "从业务动作层看，真正值得复盘的不是所有对象，而是净增长高、增长快、流失异常或重合度异常的重点对象，先找头部和异常，再决定后续资源投放。",
    ]
    followup_prompts: list[dict[str, Any]] = []
    if report_lens in {"procurement_sales_review", "sales_review", "management_accounting_review"}:
        product_rows = rows_by_dimension.get("商品") or rows_by_dimension.get("SKU") or []
        category_rows = rows_by_dimension.get("品类") or []
        supplier_rows = rows_by_dimension.get("供应商") or []
        if product_rows:
            head_object = product_rows[0].get("对象", "头部对象")
            followup_prompts.append(
                {
                    "theme": "头部对象",
                    "prompt": f"语义层已经提示要看头部对象，下一步直接拆 `{head_object}`：比较它与次头部对象在销售额、订单覆盖、客户覆盖、复购、低分评价和逾期率上的差异，判断它到底是放心放量的主推头部，还是有量但要先修的修复型头部。",
                    "why": "避免把“头部”直接等同于“最该放量”。",
                }
            )
        if category_rows:
            head_category = category_rows[0].get("对象", "头部品类")
            followup_prompts.append(
                {
                    "theme": "品类头部",
                    "prompt": f"语义层已经提示要看结构头部，下一步继续拆 `{head_category}`：看这个品类的头部商品和高风险商品是不是同一批，判断这个盘子是在健康放量，还是在用售后与履约问题换规模。",
                    "why": "避免把品类盘子大误判成品类健康。",
                }
            )
        if supplier_rows:
            followup_prompts.append(
                {
                    "theme": "供应商分工",
                    "prompt": "语义层已经提示要看供给主体，下一步比较销售贡献头部与客户承接头部是否为同一个卖家，再看履约和低分评价是否在拖后腿，明确谁该保留合作、谁该先修、谁该降权。",
                    "why": "供应商层不能只有一张销售榜单。",
                }
            )
    if not followup_prompts:
        followup_prompts = [
            {
                "theme": "头部结构",
                "prompt": "语义层提示要看头部对象时，下一步要直接比较头部、次头部和高风险对象的差异，不要停在描述头部存在。",
                "why": "把语义结论变成后续分析动作。",
            },
            {
                "theme": "异常对象",
                "prompt": "语义层提示要看异常对象时，下一步要拆它是低基数异常、口径异常，还是业务风险异常，再决定是观察、修复还是止损。",
                "why": "避免把异常都写成同一种问题。",
            },
        ]
    return {
        "mode": "fallback",
        "reason": reason,
        "title": "语义洞察展开",
        "expanded_paragraphs": paragraphs,
        "market_angles": text_findings + numeric_findings,
        "action_expansion": actions,
        "followup_prompts": followup_prompts[:5],
    }


def codex_expand_semantic_narrative(expansion_context: dict[str, Any]) -> dict[str, Any]:
    system_prompt = (
        "You are Codex acting as a senior business analyst. "
        "You must answer in Simplified Chinese. "
        "Expand a semantic-layer bullet list into richer, decision-useful analytical commentary. "
        "Do not repeat bullets mechanically. Instead, write 3 to 5 concise but fully formed analytical paragraphs that explain what the findings mean, why they matter, and how they support market or business interpretation. "
        "Return JSON only with keys: title, expanded_paragraphs, market_angles, action_expansion, followup_prompts. "
        "expanded_paragraphs must contain 3 to 5 paragraph-like Chinese strings. "
        "market_angles and action_expansion must each contain 3 to 5 concise Chinese strings. "
        "followup_prompts must contain 3 to 6 objects with keys: theme, prompt, why. "
        "The prompt field must turn semantic findings into the next concrete analysis task, for example if the semantic layer says to inspect head objects, then the prompt must explicitly tell the next layer to compare head vs next-best vs high-risk objects using actual business fields."
    )
    tool_specs = [
        {
            "name": "lookup_semantic_context",
            "description": "Read selected semantic findings, market angles, and metric context before expanding the narrative.",
            "parameters": {
                "type": "object",
                "properties": {
                    "fields": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["fields"],
                "additionalProperties": False,
            },
            "handler": lambda args: {
                key: expansion_context.get(key)
                for key in [str(item) for item in args.get("fields", [])[:10]]
            },
        }
    ]
    return _request_codex_agentic_json(
        system_prompt=system_prompt,
        user_payload=expansion_context,
        tool_specs=tool_specs,
        fallback_builder=_fallback_semantic_expansion,
    )


def _fallback_historical_report_adaptation(reason: str, payload: dict[str, Any]) -> dict[str, Any]:
    source_name = payload.get("historical_report_name") or "历史报告"
    executive_summary = payload.get("executive_summary", [])
    section_summaries = payload.get("section_summaries", [])

    lines = [
        f"# {payload.get('dataset_name', '当前数据')} 仿历史报告版",
        "",
        f"> 参考样例：{source_name}",
        "",
        "## 管理层摘要",
        "",
    ]
    for bullet in executive_summary[:4]:
        lines.append(f"- {bullet}")

    for section in section_summaries[:6]:
        lines.extend(["", f"## {section.get('title', '章节')}", ""])
        summary = section.get("summary")
        if summary:
            lines.append(str(summary))
            lines.append("")
        for bullet in section.get("bullets", [])[:4]:
            lines.append(f"- {bullet}")

    return {
        "mode": "fallback",
        "reason": reason,
        "title": "历史报告仿写层",
        "source_name": source_name,
        "template_signals": [
            "系统已识别到用户希望复用历史报告的章节结构和表达口径。",
            "当前为兜底模式，会优先保留历史报告导向，但仍以新数据结论为准。",
            "若历史报告中包含当前数据无法支撑的章节，系统会自动弱化或省略。",
        ],
        "adaptation_notes": [
            "先复用旧报告的章节顺序和表达风格，再替换成新数据支持的结论。",
            "不会沿用旧报告里的旧数值或旧事实，所有数字都应来自当前数据。",
            "建议把这版作为‘只换数据’的初稿，再做一轮人工审阅。",
        ],
        "adapted_report_markdown": "\n".join(lines) + "\n",
    }


def _fallback_business_classification(reason: str, payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "mode": "fallback",
        "reason": reason,
        "task_family_candidates": [],
        "object_candidates": [],
        "column_role_hints": [],
        "notes": [
            "当前未取得 live Codex 分类结果，系统继续使用规则层的行业与对象识别。",
            "如果字段语义仍有不确定性，后续会保持结论保守，不把猜测写成事实。",
        ],
    }


def _fallback_requirement_model(reason: str, payload: dict[str, Any]) -> dict[str, Any]:
    user_requirement = str(payload.get("user_requirement") or "").strip()
    problem = str(payload.get("problem_to_solve") or "").strip() or user_requirement
    audience = str(payload.get("target_audience") or "").strip()
    purpose = str(payload.get("core_purpose") or "").strip()
    expected = str(payload.get("expected_result") or "").strip()
    constraints_raw = str(payload.get("key_constraints") or "").replace("；", "\n").replace(";", "\n")
    explicit_constraints = [item.strip() for item in constraints_raw.splitlines() if item.strip()][:5]
    ambiguity_flags: list[str] = []
    if not problem:
        ambiguity_flags.append("核心业务问题仍偏模糊")
    if not audience:
        ambiguity_flags.append("目标受众未明确")
    if not purpose and not expected:
        ambiguity_flags.append("输出目的与交付形式未明确")

    refined_problem = problem or f"围绕 `{payload.get('dataset_name', '当前数据')}` 形成一份可执行分析判断"
    refined_audience = audience or "业务负责人 / 分析协作者"
    refined_purpose = purpose or expected or "形成一份可直接用于汇报和后续执行的分析报告"
    refined_expected_result = expected or "主报告 + 支撑结论的分析附录"

    success_criteria = [
        "能明确回答用户当前最想解决的业务问题",
        "能区分强结论、弱结论和仍需验证的部分",
        "能给出面向当前受众的可执行动作或后续验证建议",
    ]
    must_answer_questions = [
        refined_problem,
        "这份数据最适合支持什么判断",
        "报告最后应该让当前受众拿走什么结论和动作",
    ]
    non_goals = [
        "不把数据里没有证据支持的判断写成事实",
        "不输出与当前问题无关的泛泛分析",
    ]
    output_preferences = [
        "优先给出结论、证据和动作，而不是方法堆砌",
        "优先写成可汇报、可执行、可继续追问的结构",
        "对缺失信息与边界保持明确标注",
    ]
    recommended_focus = [
        "先锁定必须回答的问题",
        "再围绕当前受众组织章节顺序",
        "最后把结论转成动作与验证清单",
    ]
    return {
        "mode": "fallback",
        "reason": reason,
        "refined_problem": refined_problem,
        "refined_audience": refined_audience,
        "refined_purpose": refined_purpose,
        "refined_expected_result": refined_expected_result,
        "explicit_constraints": explicit_constraints,
        "success_criteria": success_criteria,
        "must_answer_questions": must_answer_questions,
        "non_goals": non_goals,
        "output_preferences": output_preferences,
        "ambiguity_flags": ambiguity_flags,
        "recommended_focus": recommended_focus,
        "next_step": "若问题足够明确，则直接按当前问题组织分析；若仍模糊，则先补齐目标、受众和交付偏好。",
    }


def _family_defaults_from_context(payload: dict[str, Any]) -> dict[str, str]:
    joined = " ".join(
        [
            str(payload.get("dataset_name") or ""),
            str(payload.get("sheet_name") or ""),
            str(payload.get("user_requirement") or ""),
            str(payload.get("problem_to_solve") or ""),
            str(payload.get("business_background_text") or ""),
            " ".join(str(item) for item in payload.get("columns", [])[:20]),
        ]
    )
    if any(token in joined for token in ["基金会", "公益", "捐赠", "理事会", "服务领域"]):
        return {
            "business_background_name": "基金会年度复盘场景",
            "business_background_text": "这是一份基金会年度汇总与项目/支出相关数据，适合用于复盘基金会主体结构、公益支出、收入来源、治理活跃度和后续重点复盘对象。",
            "user_requirement": "请基于基金会年度汇总与项目结构生成一份专业复盘报告。",
            "problem_to_solve": "判断哪些基金会承担主要公益支出，收入与支出结构是否健康，公益支出占比是否足够，哪些基金会值得优先复盘与排查。",
            "target_audience": "基金会负责人 / 秘书处 / 项目管理负责人 / 资助管理团队",
            "core_purpose": "形成一份可直接用于内部复盘会和资源配置讨论的基金会分析报告",
            "expected_result": "主报告 + 重点基金会清单 + 结构风险与补数建议",
            "key_constraints": "只基于当前上传数据判断；明确结论边界；优先给可执行建议；中文输出",
        }
    if any(token in joined for token in ["投放", "媒体", "曝光", "点击", "点位", "终端"]):
        return {
            "business_background_name": "投放复盘场景",
            "business_background_text": "这是一份媒体投放或执行复盘数据，适合用于解释规模、效率、兑现、组合差异和后续资源调整方向。",
            "user_requirement": "请基于当前投放数据生成一份可用于管理层复盘的专业报告。",
            "problem_to_solve": "判断哪些媒体、终端和组合承担主要结果，效率与兑现是否健康，哪些对象值得加码、收缩或优先排查。",
            "target_audience": "市场负责人 / 媒介负责人 / 品牌负责人 / 分析团队",
            "core_purpose": "形成投放复盘、资源调整和下一轮验证的决策依据",
            "expected_result": "主报告 + 动作矩阵 + 复盘明细附件",
            "key_constraints": "只基于当前上传数据判断；区分规模、效率与兑现；中文输出",
        }
    if any(token in joined for token in ["销售", "订单", "sku", "spu", "收入", "门店"]):
        return {
            "business_background_name": "经营销售复盘场景",
            "business_background_text": "这是一份经营或销售数据，适合用于解释结构、趋势、增长动量、重点商品和渠道差异。",
            "user_requirement": "请基于经营销售数据生成一份专业复盘报告。",
            "problem_to_solve": "判断增长来源、结构健康度、重点商品/渠道与优先优化方向。",
            "target_audience": "经营负责人 / 销售负责人 / 品类负责人 / 分析团队",
            "core_purpose": "形成经营复盘、资源配置与增长优化建议",
            "expected_result": "主报告 + 重点对象清单 + 风险与机会附件",
            "key_constraints": "只基于当前上传数据判断；优先给结构和动作建议；中文输出",
        }
    if any(token in joined for token in ["问卷", "满意度", "消费者", "态度", "NPS"]):
        return {
            "business_background_name": "消费者研究场景",
            "business_background_text": "这是一份消费者或问卷研究数据，适合用于解释人群差异、需求场景、分群和策略输入。",
            "user_requirement": "请基于消费者研究数据生成一份专业洞察报告。",
            "problem_to_solve": "判断关键人群差异、需求场景、分群结果和最值得进入策略的洞察。",
            "target_audience": "品牌负责人 / 用户研究团队 / 策略团队",
            "core_purpose": "形成洞察总结、策略输入和后续验证方向",
            "expected_result": "主报告 + 分群洞察清单 + 研究附录",
            "key_constraints": "先分强弱结论；避免把态度直接写成行为；中文输出",
        }
    if any(token in joined for token in ["舆情", "评论", "帖子", "主题", "情绪", "小红书", "微博"]):
        return {
            "business_background_name": "品牌舆情复盘场景",
            "business_background_text": "这是一份品牌舆情或内容讨论数据，适合用于解释主题、情绪、事件冲击、风险与内容机会。",
            "user_requirement": "请基于品牌舆情数据生成一份风险与机会复盘报告。",
            "problem_to_solve": "判断当前主导话题、情绪走向、事件性风险和可放大的内容机会。",
            "target_audience": "品牌负责人 / 公关负责人 / 舆情团队 / 内容团队",
            "core_purpose": "形成舆情复盘、风险响应和内容优化依据",
            "expected_result": "主报告 + 风险池 + 内容机会池",
            "key_constraints": "区分常态讨论与事件冲击；不要把声量直接写成品牌资产变化；中文输出",
        }
    if any(token in joined for token in ["实验", "A/B", "ab", "uplift", "control", "treatment"]):
        return {
            "business_background_name": "实验复盘场景",
            "business_background_text": "这是一份实验或 AB 测试数据，适合用于判断显著性、样本量、推广边界与后续实验动作。",
            "user_requirement": "请基于实验数据生成一份可用于推广决策的复盘报告。",
            "problem_to_solve": "判断实验结果是否显著、是否满足推广条件，以及哪些风险需要先复验。",
            "target_audience": "增长负责人 / 实验负责人 / 产品负责人 / 分析团队",
            "core_purpose": "形成上线、复验或停止的判断依据",
            "expected_result": "主报告 + 实验结果卡 + 推广条件清单",
            "key_constraints": "必须标明显著性、样本量与边界；中文输出",
        }
    return {
        "business_background_name": "通用业务分析场景",
        "business_background_text": "这是一份待分析业务数据，系统将先识别对象、结果变量与关键切片，再组织分析与结论。",
        "user_requirement": "请基于当前数据生成一份专业分析报告。",
        "problem_to_solve": "判断当前数据最值得支持的业务问题、关键结构差异、风险与后续动作。",
        "target_audience": "业务负责人 / 分析协作者",
        "core_purpose": "形成可汇报、可执行、可继续验证的分析结论",
        "expected_result": "主报告 + 支撑结论的分析附件",
        "key_constraints": "只基于当前上传数据判断；中文输出；明确结论边界",
    }


def _fallback_input_completion(reason: str, payload: dict[str, Any]) -> dict[str, Any]:
    defaults = _family_defaults_from_context(payload)

    def pick(key: str) -> str:
        source = _coerce_requirement_text(payload.get(key), "")
        if source:
            return source
        return defaults.get(key, "")

    completed = {
        "completed_business_background_name": pick("business_background_name"),
        "completed_business_background_text": pick("business_background_text"),
        "completed_user_requirement": pick("user_requirement"),
        "completed_problem_to_solve": pick("problem_to_solve"),
        "completed_target_audience": pick("target_audience"),
        "completed_core_purpose": pick("core_purpose"),
        "completed_expected_result": pick("expected_result"),
        "completed_key_constraints": pick("key_constraints"),
        "autofilled_fields": [
            label
            for label, key in [
                ("业务背景名称", "business_background_name"),
                ("业务背景正文", "business_background_text"),
                ("需求描述", "user_requirement"),
                ("要解决的问题", "problem_to_solve"),
                ("目标受众", "target_audience"),
                ("核心目的", "core_purpose"),
                ("预期结果", "expected_result"),
                ("关键约束", "key_constraints"),
            ]
            if not _coerce_requirement_text(payload.get(key), "")
        ],
        "completion_notes": [
            "空白输入项会优先根据数据结构、字段、样本行和业务背景材料自动补齐。",
            "如果用户已明确填写某项内容，系统保留用户原始输入，不用自动补齐覆盖。",
            "补齐结果会继续进入需求建模与分析程序，而不只停留在说明页。",
        ],
    }
    completed["mode"] = "fallback"
    completed["reason"] = reason
    return completed


def codex_complete_input_fields(input_context: dict[str, Any]) -> dict[str, Any]:
    system_prompt = (
        "You are Codex acting as an analytics intake completion agent. "
        "You must answer in Simplified Chinese and return JSON only. "
        "Your job is to fill in missing user input fields for a reporting workflow, using dataset schema, sample rows, business background text, and historical report hints. "
        "If frontend_context_pack exists, treat it as the high-priority compressed interpretation of the frontend demand and background. "
        "If a field is already non-empty in the payload, preserve the user's original intent and only refine around it mentally; do not override it in the completed_* output. "
        "Return keys: completed_business_background_name, completed_business_background_text, completed_user_requirement, completed_problem_to_solve, completed_target_audience, completed_core_purpose, completed_expected_result, completed_key_constraints, autofilled_fields, completion_notes. "
        "All completed_* values must be concise Chinese strings suitable for direct use in the report workflow. "
        "autofilled_fields must be a Chinese list naming which input fields were filled automatically. "
        "completion_notes must explain the autofill logic in 2 to 5 concise Chinese strings. "
        "Do not invent unavailable factual details; infer only the kind of analysis task, audience, purpose, expected output, and constraints that best fit the dataset and provided context."
    )
    tool_specs = [
        {
            "name": "lookup_input_context",
            "description": "Read selected input, schema, and sample fields before completing missing intake items.",
            "parameters": {
                "type": "object",
                "properties": {
                    "fields": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["fields"],
                "additionalProperties": False,
            },
            "handler": lambda args: {
                key: input_context.get(key)
                for key in [str(item) for item in args.get("fields", [])[:12]]
            },
        }
    ]
    return _request_codex_agentic_json(
        system_prompt=system_prompt,
        user_payload=input_context,
        tool_specs=tool_specs,
        fallback_builder=_fallback_input_completion,
    )


def _coerce_requirement_text(value: Any, fallback: str = "") -> str:
    if isinstance(value, str):
        text = value.strip()
        if text.count("?") >= max(2, len(text) // 4) or "�" in text:
            return fallback
        return text or fallback
    if isinstance(value, list):
        parts = [str(item).strip() for item in value if str(item).strip()]
        text = "；".join(parts)
        if text.count("?") >= max(2, len(text) // 4) or "�" in text:
            return fallback
        return text or fallback
    text = str(value).strip()
    if text.count("?") >= max(2, len(text) // 4) or "�" in text:
        return fallback
    return text or fallback


def _coerce_requirement_list(value: Any) -> list[str]:
    if isinstance(value, list):
        items = [str(item).strip() for item in value if str(item).strip()]
        return [item for item in items if item.count("?") < max(2, len(item) // 4) and "�" not in item]
    if isinstance(value, str):
        text = value.strip()
        if not text or text.count("?") >= max(2, len(text) // 4) or "�" in text:
            return []
        return [text]
    text = str(value).strip()
    if not text or text.count("?") >= max(2, len(text) // 4) or "�" in text:
        return []
    return [text]


def _normalize_requirement_result(result: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(result)
    normalized["refined_problem"] = _coerce_requirement_text(result.get("refined_problem"), "")
    normalized["refined_audience"] = _coerce_requirement_text(result.get("refined_audience"), "")
    normalized["refined_purpose"] = _coerce_requirement_text(result.get("refined_purpose"), "")
    normalized["refined_expected_result"] = _coerce_requirement_text(result.get("refined_expected_result"), "")
    for key in [
        "explicit_constraints",
        "success_criteria",
        "must_answer_questions",
        "non_goals",
        "output_preferences",
        "ambiguity_flags",
        "recommended_focus",
    ]:
        normalized[key] = _coerce_requirement_list(result.get(key))
    normalized["next_step"] = _coerce_requirement_text(result.get("next_step"), "")
    return normalized


def _ground_requirement_result(result: dict[str, Any], requirement_context: dict[str, Any]) -> dict[str, Any]:
    grounded = dict(result)
    source_problem = _coerce_requirement_text(requirement_context.get("problem_to_solve") or requirement_context.get("user_requirement"), "")
    source_audience = _coerce_requirement_text(requirement_context.get("target_audience"), "")
    source_purpose = _coerce_requirement_text(requirement_context.get("core_purpose"), "")
    source_expected = _coerce_requirement_text(requirement_context.get("expected_result"), "")
    source_dataset = _coerce_requirement_text(requirement_context.get("dataset_name"), "")
    source_constraints = _coerce_requirement_list(requirement_context.get("key_constraints"))
    frontend_context_pack = requirement_context.get("frontend_context_pack") if isinstance(requirement_context.get("frontend_context_pack"), dict) else {}
    directives = frontend_context_pack.get("context_directives") if isinstance(frontend_context_pack.get("context_directives"), dict) else {}
    pack_questions = _coerce_requirement_list(directives.get("must_answer"))
    pack_preserve = _coerce_requirement_list(directives.get("must_preserve"))
    pack_tone = _coerce_requirement_list(directives.get("tone_preferences"))
    pack_dimensions = _coerce_requirement_list(directives.get("detail_dimension_hints"))
    pack_background = _coerce_requirement_list((frontend_context_pack.get("business_background") or {}).get("summary_bullets"))

    def _looks_missing(text: str) -> bool:
        tokens = ["为空", "未明确", "无法直接确定", "尚未明确", "待确认", "模糊", "未知", "占位", "缺失", "不可读", "无法判断"]
        return not text or any(token in text for token in tokens)

    if source_problem:
        grounded["refined_problem"] = source_problem
    if source_audience:
        grounded["refined_audience"] = source_audience
    if source_purpose:
        grounded["refined_purpose"] = source_purpose
    if source_expected:
        grounded["refined_expected_result"] = source_expected

    explicit_constraints = list(grounded.get("explicit_constraints", []))
    for item in source_constraints:
        if item not in explicit_constraints:
            explicit_constraints.append(item)
    grounded["explicit_constraints"] = explicit_constraints[:5]

    must_answer = list(grounded.get("must_answer_questions", []))
    for item in reversed(pack_questions):
        if item and item not in must_answer:
            must_answer.insert(0, item)
    if source_problem and source_problem not in must_answer:
        must_answer.insert(0, source_problem)
    grounded["must_answer_questions"] = must_answer[:5]

    output_preferences = list(grounded.get("output_preferences", []))
    for item in [*pack_tone[:3], *pack_preserve[:2]]:
        if item and item not in output_preferences:
            output_preferences.append(item)
    grounded["output_preferences"] = output_preferences[:5]

    recommended_focus = list(grounded.get("recommended_focus", []))
    for item in [*pack_dimensions[:3], *pack_background[:2]]:
        if item and item not in recommended_focus:
            recommended_focus.append(item)
    grounded["recommended_focus"] = recommended_focus[:5]

    ambiguity_flags = [
        item
        for item in grounded.get("ambiguity_flags", [])
        if not (
            (source_problem and any(token in item for token in ["核心业务问题", "原始需求", "问题", "user_requirement", "problem_to_solve"]))
            or (source_audience and any(token in item for token in ["目标受众", "target_audience"]))
            or ((source_purpose or source_expected) and any(token in item for token in ["输出目的", "交付形式", "core_purpose", "expected_result"]))
            or (source_dataset and any(token in item for token in ["dataset_name", "数据集名称"]))
        )
    ]
    grounded["ambiguity_flags"] = ambiguity_flags[:5]

    if source_problem and source_audience and (source_purpose or source_expected):
        grounded["next_step"] = "围绕当前已明确的问题、受众和目的直接组织分析与报告。"

    return grounded


def codex_synthesize_requirement(requirement_context: dict[str, Any]) -> dict[str, Any]:
    system_prompt = (
        "You are Codex acting as a principal analytics requirements architect. "
        "You must answer in Simplified Chinese and return JSON only. "
        "Your job is to transform the user's raw requirement into an executable analytics brief. "
        "Read the user requirement, problem to solve, target audience, purpose, expected result, constraints, business background, and historical report hints. "
        "If frontend_context_pack exists, prioritize its context_brief, must_answer, must_preserve, detail_dimension_hints, business_background summary, and historical reference cues over generic inference. "
        "Return keys: refined_problem, refined_audience, refined_purpose, refined_expected_result, explicit_constraints, success_criteria, must_answer_questions, non_goals, output_preferences, ambiguity_flags, recommended_focus, next_step. "
        "All list fields should contain 2 to 5 concise Chinese strings. "
        "The output must make the requirement more actionable, less generic, and clearly tied to what the final report must answer. "
        "Do not invent unsupported business facts. If something is unclear, put it into ambiguity_flags instead of pretending it is known."
    )
    tool_specs = [
        {
            "name": "lookup_requirement_fields",
            "description": "Read a subset of requirement and context fields before synthesizing the analytics brief.",
            "parameters": {
                "type": "object",
                "properties": {
                    "fields": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["fields"],
                "additionalProperties": False,
            },
            "handler": lambda args: {
                key: requirement_context.get(key)
                for key in [str(item) for item in args.get("fields", [])[:10]]
            },
        }
    ]
    result = _request_codex_agentic_json(
        system_prompt=system_prompt,
        user_payload=requirement_context,
        tool_specs=tool_specs,
        fallback_builder=_fallback_requirement_model,
    )
    normalized = _normalize_requirement_result(result)
    return _ground_requirement_result(normalized, requirement_context)


def _fallback_statistical_scope(reason: str, payload: dict[str, Any]) -> dict[str, Any]:
    numeric_columns = [str(item) for item in payload.get("numeric_columns", [])]
    temporal_columns = {str(item) for item in payload.get("temporal_columns", [])}
    profiles = {str(item.get("column")): item for item in payload.get("column_profiles", [])}
    metric_tokens = ["收入", "支出", "捐赠", "公益", "金额", "总额", "次数", "占比", "率", "income", "spend", "revenue", "cost", "donation", "roi"]
    time_tokens = ["年度", "年份", "日期", "时间", "month", "year", "date", "time"]
    keep: list[str] = []
    exclude: list[dict[str, str]] = []
    for column in numeric_columns:
        profile = profiles.get(column, {})
        lower = column.lower()
        is_time_like = any(token in column or token in lower for token in time_tokens) and not any(token in column or token in lower for token in metric_tokens)
        unique_count = int(profile.get("unique_count") or 0)
        std = profile.get("std")
        if column in temporal_columns or is_time_like:
            exclude.append({"column": column, "reason": "更适合作为时间口径或索引字段解读，不进入相关性和建模比较"})
        elif unique_count <= 1 or std in (0, 0.0):
            exclude.append({"column": column, "reason": "该字段几乎不波动，放进相关性或显著性比较没有业务意义"})
        else:
            keep.append(column)
    if not keep:
        keep = [column for column in numeric_columns if column not in temporal_columns][:4]
    return {
        "mode": "fallback",
        "reason": reason,
        "keep_numeric_columns": keep[:8],
        "exclude_numeric_columns": exclude[:8],
        "notes": [
            "统计比较守门器优先排除时间口径、主键/索引型字段和几乎不波动的字段。",
            "只有具备可比性和波动性的指标才进入相关性、显著性检验和自动建模。",
        ],
    }


def codex_statistical_scope(statistical_context: dict[str, Any]) -> dict[str, Any]:
    system_prompt = (
        "You are Codex acting as a statistical scope gatekeeper. "
        "You must answer in Simplified Chinese and return JSON only. "
        "Your job is to decide which numeric columns are valid for correlation analysis, statistical testing, clustering, and predictive modeling in the current dataset. "
        "Read numeric columns, temporal columns, column profiles, semantic mapping, object candidates, and user intent. "
        "Return keys: keep_numeric_columns, exclude_numeric_columns, notes. "
        "keep_numeric_columns must be an ordered Chinese/English column-name list for statistically comparable metrics. "
        "exclude_numeric_columns must be a list of objects with fields column and reason. "
        "Exclude fields that are mainly time indexes, IDs, administrative sequence values, or nearly constant fields, unless they are clearly business metrics. "
        "Prefer keeping actual business metrics such as income, spend, count, conversion, reach, or governance counts. "
        "Do not invent columns that are not in the payload."
    )
    tool_specs = [
        {
            "name": "lookup_statistical_context",
            "description": "Read selected numeric columns, temporal fields, and profiles before deciding statistical scope.",
            "parameters": {
                "type": "object",
                "properties": {
                    "fields": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["fields"],
                "additionalProperties": False,
            },
            "handler": lambda args: {
                key: statistical_context.get(key)
                for key in [str(item) for item in args.get("fields", [])[:12]]
            },
        }
    ]
    result = _request_codex_agentic_json(
        system_prompt=system_prompt,
        user_payload=statistical_context,
        tool_specs=tool_specs,
        fallback_builder=_fallback_statistical_scope,
    )
    numeric_columns = [str(item) for item in statistical_context.get("numeric_columns", [])]
    temporal_columns = {str(item) for item in statistical_context.get("temporal_columns", [])}
    metric_tokens = ["收入", "支出", "捐赠", "公益", "金额", "总额", "次数", "占比", "率", "income", "spend", "revenue", "cost", "donation", "roi"]
    keep = [str(item) for item in result.get("keep_numeric_columns", []) if str(item) in numeric_columns]
    exclude_rows = [dict(item) for item in result.get("exclude_numeric_columns", []) if str(item.get("column", "")) in numeric_columns]
    excluded_names = {str(item.get("column", "")) for item in exclude_rows}
    for column in numeric_columns:
        lower = column.lower()
        if any(token in column or token in lower for token in metric_tokens) and column not in keep:
            keep.append(column)
            excluded_names.discard(column)
    exclude_rows = [item for item in exclude_rows if str(item.get("column", "")) in excluded_names]
    if not keep:
        keep = [column for column in numeric_columns if column not in temporal_columns][:8]
    result["keep_numeric_columns"] = keep[:8]
    result["exclude_numeric_columns"] = exclude_rows[:8]
    return result


def _fallback_statistical_method_selection(reason: str, payload: dict[str, Any]) -> dict[str, Any]:
    candidates = payload.get("candidate_methods", []) or []
    numeric_columns = [str(item) for item in payload.get("numeric_columns", []) if str(item).strip()]
    categorical_columns = [str(item) for item in payload.get("categorical_columns", []) if str(item).strip()]
    temporal_columns = [str(item) for item in payload.get("temporal_columns", []) if str(item).strip()]
    lens = str(payload.get("report_lens") or "mixed_business_review")

    candidate_by_id = {str(item.get("id") or ""): item for item in candidates if str(item.get("id") or "").strip()}
    selected_ids: list[str] = []
    selected_methods: list[dict[str, Any]] = []

    def add(method_id: str, *, priority: int, why: str, business_question: str, expected_output: str) -> None:
        if method_id not in candidate_by_id or method_id in selected_ids:
            return
        row = candidate_by_id[method_id]
        selected_ids.append(method_id)
        selected_methods.append(
            {
                "priority": priority,
                "method_id": method_id,
                "method": row.get("method") or method_id,
                "why": why,
                "business_question": business_question,
                "expected_output": expected_output,
            }
        )

    if len(numeric_columns) >= 2:
        add(
            "correlation",
            priority=1,
            why="当前至少有两列可比较数值指标，适合先用相关矩阵找联动链。",
            business_question="哪些指标会一起变化，适合进入同一条监控链？",
            expected_output="最强相关指标对、相关强度和联动解释。",
        )
    if numeric_columns:
        add(
            "normality",
            priority=2,
            why="需要先知道核心数值指标能不能按均值口径读，还是要改看分位数和异常值。",
            business_question="当前主指标应按均值解释，还是按分位数和异常窗口解释？",
            expected_output="正态性结果与均值口径可用性判断。",
        )
    if categorical_columns and numeric_columns:
        add(
            "anova",
            priority=3,
            why="当前既有分组字段也有数值结果，适合先判断不同切片之间是否已形成稳定差异。",
            business_question="不同分组在核心指标上是否已经拉开可操作差异？",
            expected_output="组间差异显著性与头部切片优先级。",
        )
        add(
            "kruskal",
            priority=4,
            why="在分布偏态或异常值较多时，需要用更稳健的非参数方法复核组间差异。",
            business_question="如果不按均值口径看，组间差异是否依然成立？",
            expected_output="中位数/秩次口径下的组间差异判断。",
        )
        add(
            "tukey_hsd",
            priority=5,
            why="如果 ANOVA 可跑，就需要继续识别到底是哪几组真正拉开差距。",
            business_question="显著差异究竟来自哪一组与哪一组？",
            expected_output="具体组对之间的差异定位。",
        )
    if len(categorical_columns) >= 2:
        add(
            "chi_square",
            priority=6,
            why="多个分类维度并存时，适合先判断结构组合是不是随机分布。",
            business_question="两个分类切片之间是否存在稳定结构耦合？",
            expected_output="列联关系和结构联动判断。",
        )
    if len(numeric_columns) >= 3 and lens in {"sales_review", "procurement_sales_review", "mixed_business_review", "management_accounting_review"}:
        add(
            "pca",
            priority=7,
            why="当前数值维度较多，适合先压缩成少数主维度，减少正文堆指标。",
            business_question="复杂指标能否压成更少的管理维度？",
            expected_output="主成分与高载荷变量。",
        )

    if not selected_methods:
        for index, candidate in enumerate(candidates[:5], start=1):
            method_id = str(candidate.get("id") or "")
            add(
                method_id,
                priority=index,
                why="当前可运行候选方法有限，先按可运行性和解释性排序。",
                business_question="这类方法能否为当前数据提供一条清晰的结构或差异判断？",
                expected_output="可进入正文的初步统计结论。",
            )

    headline = "已从统计方法目录里筛出最值得实跑的一组方法，优先保证可解释性、业务相关性和当前数据可运行性。"
    return {
        "mode": "fallback",
        "reason": reason,
        "headline": headline,
        "selected_method_ids": selected_ids[:8],
        "selected_methods": selected_methods[:8],
    }


def codex_select_statistical_methods(selection_context: dict[str, Any]) -> dict[str, Any]:
    system_prompt = (
        "You are Codex acting as a statistical method selection agent. "
        "You must answer in Simplified Chinese and JSON only. "
        "You will receive a candidate method list, numeric/categorical/temporal fields, report lens, and business request. "
        "Your job is to pick the small set of methods most worth actually running now. "
        "Do not return a long catalog. Prioritize methods that are both runnable on this dataset and easy to explain in business language. "
        "Return keys: headline, selected_method_ids, selected_methods. "
        "selected_method_ids must be an ordered list of method ids. "
        "selected_methods must be a list of objects with keys: priority, method_id, method, why, business_question, expected_output."
    )
    tool_specs = [
        {
            "name": "lookup_statistical_method_selection_context",
            "description": "Read candidate methods, schema signals, and business request before choosing methods to run.",
            "parameters": {
                "type": "object",
                "properties": {
                    "fields": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["fields"],
                "additionalProperties": False,
            },
            "handler": lambda args: {
                key: selection_context.get(key)
                for key in [str(item) for item in args.get("fields", [])[:14]]
            },
        }
    ]
    return _request_codex_agentic_json(
        system_prompt=system_prompt,
        user_payload=selection_context,
        tool_specs=tool_specs,
        fallback_builder=_fallback_statistical_method_selection,
    )


def _fallback_r_workflow_author(reason: str, payload: dict[str, Any]) -> dict[str, Any]:
    temporal_columns = [str(item) for item in payload.get("temporal_columns", [])[:8] if str(item).strip()]
    temporal_vector = "c(" + ", ".join(json.dumps(column) for column in temporal_columns) + ")"
    clean_script = r'''
args <- commandArgs(trailingOnly = TRUE)
input_path <- args[1]
workflow_dir <- args[2]
dir.create(workflow_dir, recursive = TRUE, showWarnings = FALSE)

df <- read.csv(input_path, check.names = FALSE, stringsAsFactors = FALSE)

trim_value <- function(x) {
  if (is.character(x)) {
    return(trimws(x))
  }
  x
}

for (col in names(df)) {
  df[[col]] <- trim_value(df[[col]])
}

write.csv(df, file.path(workflow_dir, "cleaned_dataset.csv"), row.names = FALSE, na = "")
'''
    analysis_script = f'''
args <- commandArgs(trailingOnly = TRUE)
workflow_dir <- args[1]

df <- read.csv(file.path(workflow_dir, "cleaned_dataset.csv"), check.names = FALSE, stringsAsFactors = FALSE)
numeric_cols <- names(df)[sapply(df, is.numeric)]
char_cols <- names(df)[sapply(df, function(x) is.character(x) || is.factor(x))]
temporal_candidates <- {temporal_vector}
date_cols <- temporal_candidates[temporal_candidates %in% names(df)]
use_ggplot2 <- requireNamespace("ggplot2", quietly = TRUE)

safe_write_csv <- function(data, path) {{
  write.csv(data, path, row.names = FALSE, na = "")
}}

method_names <- c()
method_outputs <- c()
method_status <- c()
record_method <- function(name, output, status) {{
  method_names <<- c(method_names, name)
  method_outputs <<- c(method_outputs, output)
  method_status <<- c(method_status, status)
}}

if (length(numeric_cols) > 0) {{
  summary_rows <- do.call(rbind, lapply(numeric_cols, function(col) {{
    series <- suppressWarnings(as.numeric(df[[col]]))
    data.frame(
      column = col,
      n = sum(!is.na(series)),
      mean = mean(series, na.rm = TRUE),
      median = median(series, na.rm = TRUE),
      sd = sd(series, na.rm = TRUE),
      min = min(series, na.rm = TRUE),
      max = max(series, na.rm = TRUE)
    )
  }}))
  safe_write_csv(summary_rows, file.path(workflow_dir, "summary_stats.csv"))
  record_method("summary_stats", "summary_stats.csv", TRUE)

  quantile_rows <- do.call(rbind, lapply(numeric_cols, function(col) {{
    series <- suppressWarnings(as.numeric(df[[col]]))
    data.frame(
      column = col,
      p05 = quantile(series, 0.05, na.rm = TRUE, names = FALSE),
      p25 = quantile(series, 0.25, na.rm = TRUE, names = FALSE),
      p75 = quantile(series, 0.75, na.rm = TRUE, names = FALSE),
      p95 = quantile(series, 0.95, na.rm = TRUE, names = FALSE)
    )
  }}))
  safe_write_csv(quantile_rows, file.path(workflow_dir, "quantile_profile.csv"))
  record_method("quantile_profile", "quantile_profile.csv", TRUE)

  anomaly_rows <- do.call(rbind, lapply(numeric_cols, function(col) {{
    series <- suppressWarnings(as.numeric(df[[col]]))
    q1 <- quantile(series, 0.25, na.rm = TRUE, names = FALSE)
    q3 <- quantile(series, 0.75, na.rm = TRUE, names = FALSE)
    iqr <- q3 - q1
    lower <- q1 - 1.5 * iqr
    upper <- q3 + 1.5 * iqr
    outlier_ratio <- if (iqr == 0) 0 else mean(series < lower | series > upper, na.rm = TRUE)
    data.frame(
      column = col,
      q1 = q1,
      q3 = q3,
      iqr = iqr,
      lower_bound = lower,
      upper_bound = upper,
      outlier_ratio = outlier_ratio
    )
  }}))
  safe_write_csv(anomaly_rows, file.path(workflow_dir, "anomaly_summary.csv"))
  record_method("anomaly_summary", "anomaly_summary.csv", TRUE)

  png(file.path(workflow_dir, "numeric_distribution.png"), width = 1400, height = 900)
  if (use_ggplot2) {{
    plot_df <- data.frame(value = suppressWarnings(as.numeric(df[[numeric_cols[1]]])))
    p <- ggplot2::ggplot(plot_df, ggplot2::aes(x = value)) +
      ggplot2::geom_histogram(bins = 20, fill = "#4E79A7", color = "white") +
      ggplot2::theme_minimal(base_size = 14) +
      ggplot2::labs(title = paste("Distribution of", numeric_cols[1]), x = numeric_cols[1], y = "Count")
    print(p)
  }} else {{
    hist(df[[numeric_cols[1]]], main = paste("Distribution of", numeric_cols[1]), col = "#4E79A7", border = "white")
  }}
  dev.off()
  record_method("numeric_distribution_plot", "numeric_distribution.png", TRUE)

  boxplot_metric_cols <- head(numeric_cols, 6)
  boxplot_height <- max(900, 380 * ceiling(length(boxplot_metric_cols) / 2))
  png(file.path(workflow_dir, "numeric_boxplot.png"), width = 1600, height = boxplot_height)
  if (use_ggplot2) {{
    long_df <- do.call(rbind, lapply(boxplot_metric_cols, function(col) {{
      data.frame(metric = col, group = "数值分布", value = suppressWarnings(as.numeric(df[[col]])), stringsAsFactors = FALSE)
    }}))
    long_df <- long_df[!is.na(long_df$value), , drop = FALSE]
    box_stats <- do.call(rbind, lapply(boxplot_metric_cols, function(col) {{
      series <- suppressWarnings(as.numeric(df[[col]]))
      series <- series[!is.na(series)]
      if (length(series) == 0) return(NULL)
      bp <- boxplot.stats(series)
      q <- as.numeric(stats::quantile(series, probs = c(0.25, 0.5, 0.75), na.rm = TRUE, names = FALSE))
      data.frame(
        metric = col,
        group = "数值分布",
        stat_name = c("下须", "Q1", "中位", "Q3", "上须"),
        y_value = c(bp$stats[1], q[1], q[2], q[3], bp$stats[5]),
        label = c(
          paste0("下须 ", sprintf("%.1f", bp$stats[1])),
          paste0("Q1 ", sprintf("%.1f", q[1])),
          paste0("中位 ", sprintf("%.1f", q[2])),
          paste0("Q3 ", sprintf("%.1f", q[3])),
          paste0("上须 ", sprintf("%.1f", bp$stats[5]))
        ),
        stringsAsFactors = FALSE
      )
    }}))
    p <- ggplot2::ggplot(long_df, ggplot2::aes(x = group, y = value)) +
      ggplot2::geom_boxplot(fill = "#E9C46A", outlier.color = "#B22222", width = 0.36) +
      ggplot2::geom_text(
        data = box_stats,
        ggplot2::aes(x = group, y = y_value, label = label),
        inherit.aes = FALSE,
        nudge_x = 0.18,
        hjust = 0,
        size = 3.4,
        color = "#333333",
        fontface = "bold"
      ) +
      ggplot2::facet_wrap(~metric, scales = "free_y", ncol = 2) +
      ggplot2::theme_minimal(base_size = 14) +
      ggplot2::theme(
        axis.title.x = ggplot2::element_blank(),
        axis.text.x = ggplot2::element_blank(),
        axis.ticks.x = ggplot2::element_blank(),
        plot.margin = ggplot2::margin(12, 80, 12, 12)
      ) +
      ggplot2::labs(title = "Numeric Boxplot Overview", subtitle = "图内标注：下须 / Q1 / 中位 / Q3 / 上须", y = "字段值")
    print(p)
  }} else {{
    plot_count <- min(length(boxplot_metric_cols), 6)
    old_par <- par(no.readonly = TRUE)
    par(mfrow = c(ceiling(plot_count / 2), 2), mar = c(4, 6, 3, 4))
    for (metric_name in boxplot_metric_cols[seq_len(plot_count)]) {{
      series <- suppressWarnings(as.numeric(df[[metric_name]]))
      series <- series[!is.na(series)]
      boxplot(series, horizontal = TRUE, col = "#E9C46A", main = metric_name, xlab = "值")
      bp <- boxplot.stats(series)
      q <- as.numeric(stats::quantile(series, probs = c(0.25, 0.5, 0.75), na.rm = TRUE, names = FALSE))
      text(c(bp$stats[1], q[1], q[2], q[3], bp$stats[5]), rep(1.2, 5), labels = c(
        paste0("下须 ", sprintf("%.1f", bp$stats[1])),
        paste0("Q1 ", sprintf("%.1f", q[1])),
        paste0("中位 ", sprintf("%.1f", q[2])),
        paste0("Q3 ", sprintf("%.1f", q[3])),
        paste0("上须 ", sprintf("%.1f", bp$stats[5]))
      ), cex = 0.85, pos = 3)
    }}
    par(old_par)
  }}
  dev.off()
  record_method("numeric_boxplot", "numeric_boxplot.png", TRUE)
}}

if (length(numeric_cols) >= 2) {{
  corr <- suppressWarnings(cor(df[numeric_cols], use = "pairwise.complete.obs"))
  write.csv(corr, file.path(workflow_dir, "correlation_matrix.csv"), row.names = TRUE, na = "")
  record_method("correlation_matrix", "correlation_matrix.csv", TRUE)
}}

if (length(char_cols) > 0) {{
  counts <- sort(table(df[[char_cols[1]]]), decreasing = TRUE)
  top_counts <- head(counts, 12)
  top_df <- data.frame(category = names(top_counts), count = as.integer(top_counts))
  safe_write_csv(top_df, file.path(workflow_dir, "top_categories.csv"))
  record_method("category_mix", "top_categories.csv", TRUE)

  png(file.path(workflow_dir, "category_mix.png"), width = 1400, height = 900)
  if (use_ggplot2) {{
    plot_df <- data.frame(category = names(top_counts), count = as.integer(top_counts))
    p <- ggplot2::ggplot(plot_df, ggplot2::aes(x = reorder(category, count), y = count)) +
      ggplot2::geom_col(fill = "#F28E2B") +
      ggplot2::coord_flip() +
      ggplot2::theme_minimal(base_size = 14) +
      ggplot2::labs(title = paste("Top categories for", char_cols[1]), x = NULL, y = "Count")
    print(p)
  }} else {{
    barplot(top_counts, las = 2, col = "#F28E2B", main = paste("Top categories for", char_cols[1]))
  }}
  dev.off()
  record_method("category_mix_plot", "category_mix.png", TRUE)

  if (length(numeric_cols) > 0) {{
    grouped_metric <- aggregate(df[[numeric_cols[1]]], list(category = df[[char_cols[1]]]), mean, na.rm = TRUE)
    names(grouped_metric)[2] <- "mean_value"
    grouped_metric <- grouped_metric[order(grouped_metric$mean_value, decreasing = TRUE), ]
    grouped_metric <- head(grouped_metric, 20)
    safe_write_csv(grouped_metric, file.path(workflow_dir, "category_metric_summary.csv"))
    record_method("category_metric_summary", "category_metric_summary.csv", TRUE)
  }}
}}

if (length(date_cols) > 0 && length(numeric_cols) > 0) {{
  parsed <- safe_parse_datetime(df[[date_cols[1]]])
  valid <- !is.na(parsed)
  if (sum(valid) > 1) {{
    trend_df <- aggregate(df[[numeric_cols[1]]][valid], list(period = as.Date(parsed[valid])), mean, na.rm = TRUE)
    names(trend_df)[2] <- "value"
    safe_write_csv(trend_df, file.path(workflow_dir, "temporal_trend.csv"))
    record_method("temporal_trend", "temporal_trend.csv", TRUE)
    png(file.path(workflow_dir, "temporal_trend.png"), width = 1400, height = 900)
    if (use_ggplot2) {{
      p <- ggplot2::ggplot(trend_df, ggplot2::aes(x = period, y = value)) +
        ggplot2::geom_line(color = "#59A14F", linewidth = 1.2) +
        ggplot2::geom_point(color = "#59A14F", size = 2.2) +
        ggplot2::theme_minimal(base_size = 14) +
        ggplot2::labs(title = paste("Trend of", numeric_cols[1]), x = date_cols[1], y = numeric_cols[1])
      print(p)
    }} else {{
      plot(trend_df$period, trend_df$value, type = "l", lwd = 2, col = "#59A14F", main = paste("Trend of", numeric_cols[1]), xlab = date_cols[1], ylab = numeric_cols[1])
    }}
    dev.off()
    record_method("temporal_trend_plot", "temporal_trend.png", TRUE)
  }}
}}

missing_profile <- data.frame(
  column = names(df),
  missing_count = sapply(df, function(col) sum(is.na(col))),
  missing_ratio = sapply(df, function(col) mean(is.na(col)))
)
safe_write_csv(missing_profile, file.path(workflow_dir, "missing_profile.csv"))
record_method("missing_profile", "missing_profile.csv", TRUE)

duplicate_profile <- data.frame(
  metric = c("row_count", "duplicated_rows", "duplicate_ratio"),
  value = c(nrow(df), sum(duplicated(df)), ifelse(nrow(df) == 0, 0, sum(duplicated(df)) / nrow(df)))
)
safe_write_csv(duplicate_profile, file.path(workflow_dir, "duplicate_profile.csv"))
record_method("duplicate_profile", "duplicate_profile.csv", TRUE)

if (all(c("page_views", "cart_count", "fav_count", "buy_count") %in% names(df))) {{
  funnel_metrics <- data.frame(
    stage = c("page_views", "cart_count", "fav_count", "buy_count"),
    total = c(sum(df$page_views, na.rm = TRUE), sum(df$cart_count, na.rm = TRUE), sum(df$fav_count, na.rm = TRUE), sum(df$buy_count, na.rm = TRUE))
  )
  safe_write_csv(funnel_metrics, file.path(workflow_dir, "funnel_metrics.csv"))
  record_method("funnel_metrics", "funnel_metrics.csv", TRUE)

  png(file.path(workflow_dir, "funnel_overview.png"), width = 1400, height = 900)
  if (use_ggplot2) {{
    p <- ggplot2::ggplot(funnel_metrics, ggplot2::aes(x = stage, y = total, fill = stage)) +
      ggplot2::geom_col(show.legend = FALSE) +
      ggplot2::theme_minimal(base_size = 14) +
      ggplot2::labs(title = "Behavior Funnel Overview", x = NULL, y = "Total")
    print(p)
  }} else {{
    barplot(funnel_metrics$total, names.arg = funnel_metrics$stage, col = "#4E79A7", main = "Behavior Funnel Overview")
  }}
  dev.off()
  record_method("funnel_overview_plot", "funnel_overview.png", TRUE)
}}

if ("item_id" %in% names(df) && length(numeric_cols) > 0) {{
  item_metric <- aggregate(df[[numeric_cols[1]]], list(item_id = df$item_id), sum, na.rm = TRUE)
  names(item_metric)[2] <- "total_value"
  item_metric <- item_metric[order(item_metric$total_value, decreasing = TRUE), ]
  item_metric <- head(item_metric, 30)
  safe_write_csv(item_metric, file.path(workflow_dir, "top_items.csv"))
  record_method("top_items", "top_items.csv", TRUE)
}}

method_log <- data.frame(method = method_names, output = method_outputs, status = method_status)
safe_write_csv(method_log, file.path(workflow_dir, "method_log.csv"))
'''
    run_script = r'''
args <- commandArgs(trailingOnly = TRUE)
input_path <- args[1]
workflow_dir <- args[2]

source(file.path(workflow_dir, "01_clean_prepare.R"))
source(file.path(workflow_dir, "02_analysis_visualize.R"))
'''
    return {
        "mode": "fallback",
        "reason": reason,
        "overview": "已按当前数据结构生成一套可执行的 R 清洗、分析与可视化脚本骨架。",
        "clean_script": clean_script,
        "analysis_script": analysis_script,
        "run_script": run_script,
        "expected_outputs": [
            "cleaned_dataset.csv",
            "summary_stats.csv",
            "quantile_profile.csv",
            "missing_profile.csv",
            "duplicate_profile.csv",
            "anomaly_summary.csv",
            "correlation_matrix.csv",
            "top_categories.csv",
            "category_metric_summary.csv",
            "temporal_trend.csv",
            "top_items.csv",
            "funnel_metrics.csv",
            "numeric_distribution.png",
            "numeric_boxplot.png",
            "category_mix.png",
            "temporal_trend.png",
            "funnel_overview.png",
            "method_log.csv",
        ],
    }


def _fallback_r_workflow_author_v2(reason: str, payload: dict[str, Any]) -> dict[str, Any]:
    temporal_columns = [str(item) for item in payload.get("temporal_columns", [])[:8] if str(item).strip()]
    temporal_vector = "c(" + ", ".join(json.dumps(column) for column in temporal_columns) + ")"
    numeric_columns = [str(item) for item in payload.get("numeric_columns", [])[:24] if str(item).strip()]
    category_columns = [str(item) for item in payload.get("categorical_columns", [])[:24] if str(item).strip()]
    object_columns = [str(item) for item in payload.get("object_columns", [])[:24] if str(item).strip()]
    variance_pairs = payload.get("column_role_registry", {}).get("variance_pairs", []) or []
    numeric_vector = "c(" + ", ".join(json.dumps(column) for column in numeric_columns) + ")"
    category_vector = "c(" + ", ".join(json.dumps(column) for column in category_columns) + ")"
    object_vector = "c(" + ", ".join(json.dumps(column) for column in object_columns) + ")"
    variance_pair_vector = "list(" + ", ".join(
        f'list(baseline={json.dumps(str(item.get("baseline_column") or ""))}, actual={json.dumps(str(item.get("actual_column") or ""))}, family={json.dumps(str(item.get("family") or ""))})'
        for item in variance_pairs
        if str(item.get("baseline_column") or "").strip() and str(item.get("actual_column") or "").strip()
    ) + ")"
    clean_script = r'''
args <- commandArgs(trailingOnly = TRUE)
input_path <- args[1]
workflow_dir <- args[2]
dir.create(workflow_dir, recursive = TRUE, showWarnings = FALSE)

df <- read.csv(input_path, check.names = FALSE, stringsAsFactors = FALSE)

trim_value <- function(x) {
  if (is.character(x)) return(trimws(x))
  x
}

for (col in names(df)) {
  df[[col]] <- trim_value(df[[col]])
}

write.csv(df, file.path(workflow_dir, "cleaned_dataset.csv"), row.names = FALSE, na = "")
'''
    analysis_template = r'''
args <- commandArgs(trailingOnly = TRUE)
workflow_dir <- args[1]

df <- read.csv(file.path(workflow_dir, "cleaned_dataset.csv"), check.names = FALSE, stringsAsFactors = FALSE)
use_ggplot2 <- requireNamespace("ggplot2", quietly = TRUE)
temporal_candidates <- __TEMPORAL_VECTOR__
preferred_numeric_cols <- __NUMERIC_VECTOR__
preferred_category_cols <- __CATEGORY_VECTOR__
preferred_object_cols <- __OBJECT_VECTOR__
preferred_variance_pairs <- __VARIANCE_PAIR_VECTOR__

safe_write_csv <- function(data, path) {
  write.csv(data, path, row.names = FALSE, na = "")
}

safe_numeric <- function(x) suppressWarnings(as.numeric(x))
safe_ratio <- function(num, den) ifelse(is.na(den) || den == 0, NA_real_, num / den)
safe_parse_datetime <- function(x) {
  if (inherits(x, "POSIXct") || inherits(x, "POSIXt")) return(as.POSIXct(x, tz = "UTC"))
  if (inherits(x, "Date")) return(as.POSIXct(x, tz = "UTC"))
  if (is.numeric(x)) {
    parsed_num <- tryCatch(
      suppressWarnings(as.POSIXct(x, origin = "1970-01-01", tz = "UTC")),
      error = function(e) rep(as.POSIXct(NA), length(x))
    )
    if (mean(!is.na(parsed_num)) >= 0.6) return(parsed_num)
  }
  values <- as.character(x)
  try_formats <- c(
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d %H:%M",
    "%Y-%m-%d",
    "%Y/%m/%d %H:%M:%S",
    "%Y/%m/%d %H:%M",
    "%Y/%m/%d",
    "%d/%m/%Y %H:%M:%S",
    "%d/%m/%Y %H:%M",
    "%d/%m/%Y",
    "%m/%d/%Y %H:%M:%S",
    "%m/%d/%Y %H:%M",
    "%m/%d/%Y",
    "%Y-%m",
    "%Y/%m",
    "%Y%m%d"
  )
  parsed <- tryCatch(
    suppressWarnings(as.POSIXct(values, tz = "UTC", tryFormats = try_formats)),
    error = function(e) rep(as.POSIXct(NA), length(values))
  )
  if (mean(!is.na(parsed)) < 0.6) {
    parsed <- tryCatch(
      suppressWarnings(as.POSIXct(values, tz = "UTC")),
      error = function(e) rep(as.POSIXct(NA), length(values))
    )
  }
  parsed
}

calc_skewness <- function(x) {
  x <- x[!is.na(x)]
  if (length(x) < 3) return(NA_real_)
  s <- sd(x)
  if (is.na(s) || s == 0) return(0)
  mean(((x - mean(x)) / s)^3)
}

calc_kurtosis <- function(x) {
  x <- x[!is.na(x)]
  if (length(x) < 4) return(NA_real_)
  s <- sd(x)
  if (is.na(s) || s == 0) return(0)
  mean(((x - mean(x)) / s)^4)
}

method_names <- c()
method_outputs <- c()
method_status <- c()
method_notes <- c()
record_method <- function(name, output, status, note = "") {
  method_names <<- c(method_names, name)
  method_outputs <<- c(method_outputs, output)
  method_status <<- c(method_status, status)
  method_notes <<- c(method_notes, note)
}

id_like_pattern <- "(^|_)(id|code|no)$|invoice|customerid|userid|sellerid|orderid"
id_like_cols <- names(df)[grepl(id_like_pattern, tolower(names(df)))]

numeric_cols <- names(df)[sapply(df, is.numeric)]
coercible_cols <- c()
for (col in names(df)) {
  if (col %in% numeric_cols || col %in% id_like_cols) next
  sample_values <- head(df[[col]], 1000)
  parsed <- safe_numeric(sample_values)
  usable <- mean(!is.na(parsed))
  if (!is.na(usable) && usable >= 0.8) {
    coercible_cols <- c(coercible_cols, col)
    df[[col]] <- safe_numeric(df[[col]])
  }
}
numeric_cols <- unique(c(numeric_cols, coercible_cols))
numeric_cols <- numeric_cols[!numeric_cols %in% id_like_cols]
if (length(numeric_cols) > 0) {
  numeric_cols <- numeric_cols[vapply(numeric_cols, function(col) {
    series <- safe_numeric(df[[col]])
    sum(!is.na(series)) >= 3 && length(unique(na.omit(series))) > 1
  }, logical(1))]
} else {
  numeric_cols <- character(0)
}

char_cols <- names(df)[sapply(df, function(x) is.character(x) || is.factor(x))]
char_cols <- char_cols[!char_cols %in% id_like_cols]
if ("category_id" %in% names(df) && !("category_id" %in% char_cols)) char_cols <- c(char_cols, "category_id")
if ("item_id" %in% names(df) && !("item_id" %in% char_cols)) char_cols <- c(char_cols, "item_id")

date_cols <- temporal_candidates[temporal_candidates %in% names(df)]
if (length(date_cols) == 0) {
  date_cols <- names(df)[grepl("date|time|period|day|month|year", tolower(names(df)))]
}
if (length(date_cols) > 0) {
  date_cols <- date_cols[vapply(date_cols, function(col) {
    parsed <- safe_parse_datetime(df[[col]])
    mean(!is.na(parsed)) >= 0.6
  }, logical(1))]
} else {
  date_cols <- character(0)
}
if (length(preferred_numeric_cols) > 0) {
  numeric_cols <- unique(preferred_numeric_cols[preferred_numeric_cols %in% names(df)])
}
numeric_cols <- numeric_cols[!numeric_cols %in% date_cols]

if (length(numeric_cols) > 0) {
  summary_rows <- do.call(rbind, lapply(numeric_cols, function(col) {
    series <- safe_numeric(df[[col]])
    data.frame(column = col, n = sum(!is.na(series)), mean = mean(series, na.rm = TRUE), median = median(series, na.rm = TRUE), sd = sd(series, na.rm = TRUE), min = min(series, na.rm = TRUE), max = max(series, na.rm = TRUE))
  }))
  safe_write_csv(summary_rows, file.path(workflow_dir, "summary_stats.csv")); record_method("summary_stats", "summary_stats.csv", TRUE, "已生成字段级摘要。")

  quantile_rows <- do.call(rbind, lapply(numeric_cols, function(col) {
    series <- safe_numeric(df[[col]])
    data.frame(column = col, p05 = quantile(series, 0.05, na.rm = TRUE, names = FALSE), p25 = quantile(series, 0.25, na.rm = TRUE, names = FALSE), p50 = quantile(series, 0.50, na.rm = TRUE, names = FALSE), p75 = quantile(series, 0.75, na.rm = TRUE, names = FALSE), p95 = quantile(series, 0.95, na.rm = TRUE, names = FALSE))
  }))
  safe_write_csv(quantile_rows, file.path(workflow_dir, "quantile_profile.csv")); record_method("quantile_profile", "quantile_profile.csv", TRUE, "已生成分位数轮廓。")

  anomaly_rows <- do.call(rbind, lapply(numeric_cols, function(col) {
    series <- safe_numeric(df[[col]])
    q1 <- quantile(series, 0.25, na.rm = TRUE, names = FALSE); q3 <- quantile(series, 0.75, na.rm = TRUE, names = FALSE)
    iqr <- q3 - q1; lower <- q1 - 1.5 * iqr; upper <- q3 + 1.5 * iqr
    outlier_ratio <- if (iqr == 0) 0 else mean(series < lower | series > upper, na.rm = TRUE)
    data.frame(column = col, q1 = q1, q3 = q3, iqr = iqr, lower_bound = lower, upper_bound = upper, outlier_ratio = outlier_ratio)
  }))
  safe_write_csv(anomaly_rows, file.path(workflow_dir, "anomaly_summary.csv")); record_method("anomaly_summary", "anomaly_summary.csv", TRUE, "已生成异常值摘要。")

  zero_rows <- do.call(rbind, lapply(numeric_cols, function(col) {
    series <- safe_numeric(df[[col]])
    data.frame(column = col, zero_count = sum(series == 0, na.rm = TRUE), zero_ratio = mean(series == 0, na.rm = TRUE))
  }))
  safe_write_csv(zero_rows, file.path(workflow_dir, "zero_ratio_summary.csv")); record_method("zero_ratio_summary", "zero_ratio_summary.csv", TRUE, "已生成零值占比。")

  cv_rows <- do.call(rbind, lapply(numeric_cols, function(col) {
    series <- safe_numeric(df[[col]]); avg <- mean(series, na.rm = TRUE); sdv <- sd(series, na.rm = TRUE)
    data.frame(column = col, mean = avg, sd = sdv, cv = ifelse(is.na(avg) || avg == 0, NA_real_, sdv / abs(avg)))
  }))
  safe_write_csv(cv_rows, file.path(workflow_dir, "coefficient_variation.csv")); record_method("coefficient_variation", "coefficient_variation.csv", TRUE, "已生成波动系数。")

  skew_rows <- do.call(rbind, lapply(numeric_cols, function(col) {
    series <- safe_numeric(df[[col]])
    data.frame(column = col, skewness = calc_skewness(series), kurtosis = calc_kurtosis(series))
  }))
  safe_write_csv(skew_rows, file.path(workflow_dir, "skew_kurtosis_summary.csv")); record_method("skew_kurtosis_summary", "skew_kurtosis_summary.csv", TRUE, "已生成偏度峰度。")

  distribution_metric_cols <- head(numeric_cols, 6)
  distribution_plot_height <- max(900, 360 * ceiling(length(distribution_metric_cols) / 2))
  png(file.path(workflow_dir, "numeric_distribution.png"), width = 1600, height = distribution_plot_height)
  if (use_ggplot2) {
    hist_df <- do.call(rbind, lapply(distribution_metric_cols, function(col) {
      data.frame(metric = col, value = safe_numeric(df[[col]]), stringsAsFactors = FALSE)
    }))
    hist_df <- hist_df[!is.na(hist_df$value), , drop = FALSE]
    p <- ggplot2::ggplot(hist_df, ggplot2::aes(x = value)) +
      ggplot2::geom_histogram(bins = 24, fill = "#4E79A7", color = "white") +
      ggplot2::facet_wrap(~metric, scales = "free", ncol = 2) +
      ggplot2::theme_minimal(base_size = 14) +
      ggplot2::labs(title = "Numeric Distribution Overview", subtitle = "每个面板对应一个数值字段", x = "字段值", y = "样本数")
    print(p)
  } else {
    plot_count <- min(length(distribution_metric_cols), 6)
    old_par <- par(no.readonly = TRUE)
    par(mfrow = c(ceiling(plot_count / 2), 2), mar = c(4, 4, 3, 1))
    for (metric_name in distribution_metric_cols[seq_len(plot_count)]) {
      hist(safe_numeric(df[[metric_name]]), main = paste("Distribution of", metric_name), col = "#4E79A7", border = "white", xlab = metric_name)
    }
    par(old_par)
  }
  dev.off(); record_method("numeric_distribution_plot", "numeric_distribution.png", TRUE, "已生成多字段数值分布图。")

  boxplot_metric_cols <- distribution_metric_cols
  boxplot_height <- max(900, 380 * ceiling(length(boxplot_metric_cols) / 2))
  png(file.path(workflow_dir, "numeric_boxplot.png"), width = 1600, height = boxplot_height)
  if (use_ggplot2) {
    long_df <- do.call(rbind, lapply(boxplot_metric_cols, function(col) {
      data.frame(metric = col, group = "数值分布", value = safe_numeric(df[[col]]), stringsAsFactors = FALSE)
    }))
    long_df <- long_df[!is.na(long_df$value), , drop = FALSE]
    box_stats <- do.call(rbind, lapply(boxplot_metric_cols, function(col) {
      series <- safe_numeric(df[[col]])
      series <- series[!is.na(series)]
      if (length(series) == 0) return(NULL)
      bp <- boxplot.stats(series)
      q <- as.numeric(stats::quantile(series, probs = c(0.25, 0.5, 0.75), na.rm = TRUE, names = FALSE))
      data.frame(
        metric = col,
        group = "数值分布",
        stat_name = c("下须", "Q1", "中位", "Q3", "上须"),
        y_value = c(bp$stats[1], q[1], q[2], q[3], bp$stats[5]),
        label = c(
          paste0("下须 ", sprintf("%.1f", bp$stats[1])),
          paste0("Q1 ", sprintf("%.1f", q[1])),
          paste0("中位 ", sprintf("%.1f", q[2])),
          paste0("Q3 ", sprintf("%.1f", q[3])),
          paste0("上须 ", sprintf("%.1f", bp$stats[5]))
        ),
        stringsAsFactors = FALSE
      )
    }))
    p <- ggplot2::ggplot(long_df, ggplot2::aes(x = group, y = value)) +
      ggplot2::geom_boxplot(fill = "#E9C46A", outlier.color = "#B22222", width = 0.36) +
      ggplot2::geom_text(
        data = box_stats,
        ggplot2::aes(x = group, y = y_value, label = label),
        inherit.aes = FALSE,
        nudge_x = 0.18,
        hjust = 0,
        size = 3.4,
        color = "#333333",
        fontface = "bold"
      ) +
      ggplot2::facet_wrap(~metric, scales = "free_y", ncol = 2) +
      ggplot2::theme_minimal(base_size = 14) +
      ggplot2::theme(
        axis.title.x = ggplot2::element_blank(),
        axis.text.x = ggplot2::element_blank(),
        axis.ticks.x = ggplot2::element_blank(),
        plot.margin = ggplot2::margin(12, 80, 12, 12)
      ) +
      ggplot2::labs(title = "Numeric Boxplot Overview", subtitle = "图内标注：下须 / Q1 / 中位 / Q3 / 上须", y = "字段值")
    print(p)
  } else {
    plot_count <- min(length(boxplot_metric_cols), 6)
    old_par <- par(no.readonly = TRUE)
    par(mfrow = c(ceiling(plot_count / 2), 2), mar = c(4, 6, 3, 4))
    for (metric_name in boxplot_metric_cols[seq_len(plot_count)]) {
      series <- safe_numeric(df[[metric_name]])
      series <- series[!is.na(series)]
      boxplot(series, horizontal = TRUE, col = "#E9C46A", main = metric_name, xlab = "值")
      bp <- boxplot.stats(series)
      q <- as.numeric(stats::quantile(series, probs = c(0.25, 0.5, 0.75), na.rm = TRUE, names = FALSE))
      text(c(bp$stats[1], q[1], q[2], q[3], bp$stats[5]), rep(1.2, 5), labels = c(
        paste0("下须 ", sprintf("%.1f", bp$stats[1])),
        paste0("Q1 ", sprintf("%.1f", q[1])),
        paste0("中位 ", sprintf("%.1f", q[2])),
        paste0("Q3 ", sprintf("%.1f", q[3])),
        paste0("上须 ", sprintf("%.1f", bp$stats[5]))
      ), cex = 0.85, pos = 3)
    }
    par(old_par)
  }
  dev.off(); record_method("numeric_boxplot", "numeric_boxplot.png", TRUE, "已生成带统计标注的多字段箱线图。")

  png(file.path(workflow_dir, "numeric_density.png"), width = 1600, height = distribution_plot_height)
  try({
    density_metric_cols <- distribution_metric_cols[sapply(distribution_metric_cols, function(col) sum(!is.na(safe_numeric(df[[col]]))) >= 3)]
    if (length(density_metric_cols) > 0) {
      if (use_ggplot2) {
        density_df <- do.call(rbind, lapply(density_metric_cols, function(col) {
          data.frame(metric = col, value = safe_numeric(df[[col]]), stringsAsFactors = FALSE)
        }))
        density_df <- density_df[!is.na(density_df$value), , drop = FALSE]
        p <- ggplot2::ggplot(density_df, ggplot2::aes(x = value)) +
          ggplot2::geom_density(fill = "#CDB4DB", color = "#6A4C93", alpha = 0.85) +
          ggplot2::facet_wrap(~metric, scales = "free", ncol = 2) +
          ggplot2::theme_minimal(base_size = 14) +
          ggplot2::labs(title = "Numeric Density Overview", subtitle = "每个面板对应一个数值字段", x = "字段值", y = "密度")
        print(p)
      } else {
        plot_count <- min(length(density_metric_cols), 6)
        old_par <- par(no.readonly = TRUE)
        par(mfrow = c(ceiling(plot_count / 2), 2), mar = c(4, 4, 3, 1))
        for (metric_name in density_metric_cols[seq_len(plot_count)]) {
          dens <- density(safe_numeric(df[[metric_name]]), na.rm = TRUE)
          plot(dens, main = paste("Density of", metric_name), col = "#6A4C93", lwd = 2, xlab = metric_name)
          polygon(dens, col = "#CDB4DB", border = "#6A4C93")
        }
        par(old_par)
      }
      record_method("numeric_density_plot", "numeric_density.png", TRUE, "已生成多字段密度图。")
    } else {
      record_method("numeric_density_plot", "numeric_density.png", FALSE, "可用于密度估计的数值字段不足。")
    }
  }, silent = TRUE)
  dev.off()
} else {
  for (method in c("summary_stats","quantile_profile","anomaly_summary","zero_ratio_summary","coefficient_variation","skew_kurtosis_summary","numeric_distribution_plot","numeric_boxplot","numeric_density_plot")) {
    output <- switch(method, summary_stats = "summary_stats.csv", quantile_profile = "quantile_profile.csv", anomaly_summary = "anomaly_summary.csv", zero_ratio_summary = "zero_ratio_summary.csv", coefficient_variation = "coefficient_variation.csv", skew_kurtosis_summary = "skew_kurtosis_summary.csv", numeric_distribution_plot = "numeric_distribution.png", numeric_boxplot = "numeric_boxplot.png", numeric_density_plot = "numeric_density.png")
    record_method(method, output, FALSE, "缺少可用数值字段。")
  }
}

if (length(numeric_cols) >= 2) {
  corr <- suppressWarnings(cor(df[numeric_cols], use = "pairwise.complete.obs"))
  write.csv(corr, file.path(workflow_dir, "correlation_matrix.csv"), row.names = TRUE, na = ""); record_method("correlation_matrix", "correlation_matrix.csv", TRUE, "已生成相关矩阵。")
  corr_pairs <- data.frame(left = character(), right = character(), correlation = numeric(), abs_correlation = numeric())
  for (i in seq_along(numeric_cols)) for (j in seq_along(numeric_cols)) if (j > i) corr_pairs <- rbind(corr_pairs, data.frame(left = numeric_cols[i], right = numeric_cols[j], correlation = corr[i, j], abs_correlation = abs(corr[i, j])))
  corr_pairs <- head(corr_pairs[order(corr_pairs$abs_correlation, decreasing = TRUE), ], 30)
  safe_write_csv(corr_pairs, file.path(workflow_dir, "correlation_pairs.csv")); record_method("correlation_pairs", "correlation_pairs.csv", TRUE, "已生成高相关对。")
  cov_mat <- cov(df[numeric_cols], use = "pairwise.complete.obs")
  write.csv(cov_mat, file.path(workflow_dir, "covariance_matrix.csv"), row.names = TRUE, na = ""); record_method("covariance_matrix", "covariance_matrix.csv", TRUE, "已生成协方差矩阵。")

  png(file.path(workflow_dir, "correlation_heatmap.png"), width = 1400, height = 1000)
  if (use_ggplot2) { corr_df <- as.data.frame(as.table(corr)); p <- ggplot2::ggplot(corr_df, ggplot2::aes(x = Var1, y = Var2, fill = Freq)) + ggplot2::geom_tile() + ggplot2::scale_fill_gradient2(low = "#457B9D", mid = "#F7F7F7", high = "#D62828", midpoint = 0) + ggplot2::theme_minimal(base_size = 13) + ggplot2::theme(axis.text.x = ggplot2::element_text(angle = 35, hjust = 1)) + ggplot2::labs(title = "Correlation Heatmap", x = NULL, y = NULL, fill = "corr"); print(p) } else { image(1:ncol(corr), 1:nrow(corr), t(corr[nrow(corr):1, ]), axes = FALSE, col = heat.colors(20), main = "Correlation Heatmap") }
  dev.off(); record_method("correlation_heatmap", "correlation_heatmap.png", TRUE, "已生成相关热力图。")

  scatter_metric_cols <- head(numeric_cols, 6)
  scatter_pairs <- combn(scatter_metric_cols, 2, simplify = FALSE)
  scatter_plot_height <- max(900, 360 * ceiling(length(scatter_pairs) / 2))
  png(file.path(workflow_dir, "numeric_scatter_plot.png"), width = 1600, height = scatter_plot_height)
  if (use_ggplot2) {
    scatter_df <- do.call(rbind, lapply(scatter_pairs, function(pair) {
      data.frame(
        pair = paste(pair[1], "vs", pair[2]),
        x = safe_numeric(df[[pair[1]]]),
        y = safe_numeric(df[[pair[2]]]),
        x_metric = pair[1],
        y_metric = pair[2],
        stringsAsFactors = FALSE
      )
    }))
    scatter_df <- scatter_df[!is.na(scatter_df$x) & !is.na(scatter_df$y), , drop = FALSE]
    p <- ggplot2::ggplot(scatter_df, ggplot2::aes(x = x, y = y)) +
      ggplot2::geom_point(alpha = 0.42, color = "#264653", size = 1.9) +
      ggplot2::facet_wrap(~pair, scales = "free", ncol = 2) +
      ggplot2::theme_minimal(base_size = 14) +
      ggplot2::labs(title = "Numeric Scatter Overview", subtitle = "每个面板对应一组数值字段组合", x = "横轴字段值", y = "纵轴字段值")
    print(p)
  } else {
    plot_count <- min(length(scatter_pairs), 6)
    old_par <- par(no.readonly = TRUE)
    par(mfrow = c(ceiling(plot_count / 2), 2), mar = c(4, 4, 3, 1))
    for (pair in scatter_pairs[seq_len(plot_count)]) {
      plot(
        safe_numeric(df[[pair[1]]]),
        safe_numeric(df[[pair[2]]]),
        pch = 19,
        col = "#264653",
        main = paste(pair[1], "vs", pair[2]),
        xlab = pair[1],
        ylab = pair[2]
      )
    }
    par(old_par)
  }
  dev.off(); record_method("numeric_scatter_plot", "numeric_scatter_plot.png", TRUE, "已生成多字段数值散点图。")

  numeric_complete <- na.omit(df[numeric_cols])
  if (nrow(numeric_complete) >= 5) {
    pca_fit <- prcomp(numeric_complete, center = TRUE, scale. = TRUE)
    variance_df <- data.frame(component = paste0("PC", seq_along(pca_fit$sdev)), std_dev = pca_fit$sdev, variance_explained = (pca_fit$sdev ^ 2) / sum(pca_fit$sdev ^ 2), cumulative_variance = cumsum((pca_fit$sdev ^ 2) / sum(pca_fit$sdev ^ 2)))
    safe_write_csv(variance_df, file.path(workflow_dir, "pca_variance.csv")); record_method("pca_variance", "pca_variance.csv", TRUE, "已生成主成分方差解释。")
    loadings_df <- data.frame(variable = rownames(pca_fit$rotation), pca_fit$rotation, row.names = NULL)
    safe_write_csv(loadings_df, file.path(workflow_dir, "pca_loadings.csv")); record_method("pca_loadings", "pca_loadings.csv", TRUE, "已生成主成分载荷。")
    scores_df <- data.frame(index = seq_len(min(nrow(pca_fit$x), 500)), pca_fit$x[seq_len(min(nrow(pca_fit$x), 500)), , drop = FALSE], row.names = NULL)
    safe_write_csv(scores_df, file.path(workflow_dir, "pca_scores.csv")); record_method("pca_scores", "pca_scores.csv", TRUE, "已生成主成分得分。")
    centers <- min(3, nrow(numeric_complete))
    if (centers >= 2) {
      km <- kmeans(numeric_complete[, seq_len(min(ncol(numeric_complete), 4)), drop = FALSE], centers = centers)
      cluster_df <- data.frame(index = seq_len(nrow(numeric_complete)), cluster = km$cluster)
      safe_write_csv(cluster_df, file.path(workflow_dir, "kmeans_clusters.csv")); record_method("kmeans_clusters", "kmeans_clusters.csv", TRUE, "已生成聚类结果。")
      profile_df <- aggregate(numeric_complete, list(cluster = km$cluster), mean, na.rm = TRUE)
      safe_write_csv(profile_df, file.path(workflow_dir, "cluster_profile.csv")); record_method("cluster_profile", "cluster_profile.csv", TRUE, "已生成聚类画像。")
    } else {
      record_method("kmeans_clusters", "kmeans_clusters.csv", FALSE, "样本不足以进行聚类。")
      record_method("cluster_profile", "cluster_profile.csv", FALSE, "样本不足以生成聚类画像。")
    }
  } else {
    for (method in c("pca_variance","pca_loadings","pca_scores","kmeans_clusters","cluster_profile")) {
      output <- switch(method, pca_variance = "pca_variance.csv", pca_loadings = "pca_loadings.csv", pca_scores = "pca_scores.csv", kmeans_clusters = "kmeans_clusters.csv", cluster_profile = "cluster_profile.csv")
      record_method(method, output, FALSE, "完整数值样本不足。")
    }
  }
} else {
  for (method in c("correlation_matrix","correlation_pairs","covariance_matrix","correlation_heatmap","numeric_scatter_plot","pca_variance","pca_loadings","pca_scores","kmeans_clusters","cluster_profile")) {
    output <- switch(method, correlation_matrix = "correlation_matrix.csv", correlation_pairs = "correlation_pairs.csv", covariance_matrix = "covariance_matrix.csv", correlation_heatmap = "correlation_heatmap.png", numeric_scatter_plot = "numeric_scatter_plot.png", pca_variance = "pca_variance.csv", pca_loadings = "pca_loadings.csv", pca_scores = "pca_scores.csv", kmeans_clusters = "kmeans_clusters.csv", cluster_profile = "cluster_profile.csv")
    record_method(method, output, FALSE, "可用数值字段不足两个。")
  }
}

category_candidates <- char_cols[!char_cols %in% date_cols]
category_candidates <- category_candidates[!grepl("date|time|period|day|month|year", tolower(category_candidates))]
preferred_category_candidates <- category_candidates[
  grepl("category|类|品类|类目|supplier|vendor|seller|brand|channel|segment|group|department|center|responsibility|region|product|sku", tolower(category_candidates))
]
if (length(category_candidates) > 0) {
  bounded_category_candidates <- category_candidates[vapply(category_candidates, function(col) {
    unique_count <- length(unique(na.omit(df[[col]])))
    unique_count >= 2 && unique_count <= max(12, min(50, floor(nrow(df) * 0.6)))
  }, logical(1))]
} else {
  bounded_category_candidates <- character(0)
}
category_basis <- unique(c(intersect(c("category_id"), names(df)), preferred_category_candidates, bounded_category_candidates, category_candidates))
if (length(category_basis) > 0) {
  category_col <- category_basis[1]
  counts <- sort(table(df[[category_col]]), decreasing = TRUE)
  top_counts <- head(counts, 20)
  top_df <- data.frame(category = names(top_counts), count = as.integer(top_counts))
  safe_write_csv(top_df, file.path(workflow_dir, "top_categories.csv")); record_method("top_categories", "top_categories.csv", TRUE, "已生成头部类别摘要。")
  share_df <- data.frame(category = names(counts), count = as.integer(counts)); share_df$share <- share_df$count / sum(share_df$count); share_df$cumulative_share <- cumsum(share_df$share); share_df <- head(share_df, 30)
  safe_write_csv(share_df, file.path(workflow_dir, "category_share_summary.csv")); record_method("category_share_summary", "category_share_summary.csv", TRUE, "已生成类别占比与累计占比。")

  png(file.path(workflow_dir, "category_mix.png"), width = 1400, height = 900)
  if (use_ggplot2) { plot_df <- data.frame(category = names(top_counts), count = as.integer(top_counts)); p <- ggplot2::ggplot(plot_df, ggplot2::aes(x = reorder(category, count), y = count)) + ggplot2::geom_col(fill = "#F28E2B", width = 0.34) + ggplot2::coord_flip() + ggplot2::theme_minimal(base_size = 14) + ggplot2::labs(title = paste("Top categories for", category_col), x = NULL, y = "Count"); print(p) } else { barplot(top_counts, las = 2, col = "#F28E2B", main = paste("Top categories for", category_col), width = 0.55, space = 0.7) }
  dev.off(); record_method("category_mix_plot", "category_mix.png", TRUE, "已生成类别结构图。")

  png(file.path(workflow_dir, "category_pareto.png"), width = 1600, height = 1000)
  pareto_df <- head(share_df, 15)
  pareto_note <- ifelse(nrow(pareto_df) <= 2, "当前类别过少，主要看是否均衡分布，不硬套 20/80。", "柱=数量，柱顶=单类占比，折线=累计占比。")
  if (use_ggplot2) {
    pareto_df$category <- factor(pareto_df$category, levels = pareto_df$category)
    pareto_df$cumulative_pct <- pareto_df$cumulative_share * 100
    scale_factor <- max(pareto_df$count) / 100
    if (!is.finite(scale_factor) || scale_factor == 0) scale_factor <- 1
    p <- ggplot2::ggplot(pareto_df, ggplot2::aes(x = category)) +
      ggplot2::geom_col(ggplot2::aes(y = count), fill = "#E9C46A", color = "#8D6E00", width = 0.34) +
      ggplot2::geom_text(
        ggplot2::aes(y = count, label = paste0(count, " / ", sprintf("%.1f%%", share * 100))),
        vjust = -0.45,
        size = 3.7,
        color = "#333333",
        fontface = "bold"
      ) +
      ggplot2::geom_line(
        ggplot2::aes(y = cumulative_pct * scale_factor, group = 1),
        color = "#D62828",
        linewidth = 1.1
      ) +
      ggplot2::geom_point(
        ggplot2::aes(y = cumulative_pct * scale_factor),
        color = "#D62828",
        size = 2.4
      ) +
      ggplot2::geom_text(
        ggplot2::aes(y = cumulative_pct * scale_factor, label = paste0(sprintf("%.1f", cumulative_pct), "%")),
        color = "#D62828",
        nudge_y = max(pareto_df$count) * 0.06,
        size = 3.5,
        fontface = "bold"
      ) +
      ggplot2::scale_y_continuous(
        name = "类别数量",
        sec.axis = ggplot2::sec_axis(~ . / scale_factor, name = "累计占比", labels = function(x) paste0(round(x), "%"))
      ) +
      ggplot2::coord_cartesian(ylim = c(0, max(pareto_df$count) * 1.35)) +
      ggplot2::theme_minimal(base_size = 14) +
      ggplot2::theme(axis.text.x = ggplot2::element_text(angle = 30, hjust = 1)) +
      ggplot2::labs(title = "Category Pareto", subtitle = pareto_note, x = NULL)
    print(p)
  } else {
    par(mar = c(8, 5, 5, 5))
    bar_positions <- barplot(
      pareto_df$count,
      names.arg = pareto_df$category,
      las = 2,
      col = "#E9C46A",
      border = "#8D6E00",
      width = 0.55,
      space = 0.7,
      ylim = c(0, max(pareto_df$count) * 1.35),
      main = "Category Pareto",
      ylab = "类别数量"
    )
    text(bar_positions, pareto_df$count, labels = paste0(pareto_df$count, " / ", sprintf("%.1f%%", pareto_df$share * 100)), pos = 3, cex = 0.9)
    par(new = TRUE)
    plot(bar_positions, pareto_df$cumulative_share * 100, type = "b", axes = FALSE, xlab = "", ylab = "", col = "#D62828", pch = 19, ylim = c(0, 100))
    axis(side = 4, at = seq(0, 100, 20), labels = paste0(seq(0, 100, 20), "%"))
    mtext("累计占比", side = 4, line = 2.5)
    text(bar_positions, pareto_df$cumulative_share * 100, labels = paste0(sprintf("%.1f", pareto_df$cumulative_share * 100), "%"), pos = 3, cex = 0.85, col = "#D62828")
    mtext(pareto_note, side = 1, line = 6, cex = 0.9)
  }
  dev.off(); record_method("category_pareto", "category_pareto.png", TRUE, "已生成可解释的类别帕累托图。")

  if (length(numeric_cols) > 0) {
    grouped_metric <- aggregate(df[[numeric_cols[1]]], list(category = df[[category_col]]), mean, na.rm = TRUE)
    names(grouped_metric)[2] <- "mean_value"; grouped_metric <- head(grouped_metric[order(grouped_metric$mean_value, decreasing = TRUE), ], 20)
    safe_write_csv(grouped_metric, file.path(workflow_dir, "category_metric_summary.csv")); record_method("category_metric_summary", "category_metric_summary.csv", TRUE, "已生成类别指标摘要。")

    png(file.path(workflow_dir, "category_metric_plot.png"), width = 1400, height = 900)
    if (use_ggplot2) { p <- ggplot2::ggplot(grouped_metric, ggplot2::aes(x = reorder(category, mean_value), y = mean_value)) + ggplot2::geom_col(fill = "#2A9D8F", width = 0.34) + ggplot2::coord_flip() + ggplot2::theme_minimal(base_size = 14) + ggplot2::labs(title = paste("Average", numeric_cols[1], "by", category_col), x = NULL, y = numeric_cols[1]); print(p) } else { barplot(grouped_metric$mean_value, names.arg = grouped_metric$category, las = 2, col = "#2A9D8F", main = paste("Average", numeric_cols[1], "by", category_col), width = 0.55, space = 0.7) }
    dev.off(); record_method("category_metric_plot", "category_metric_plot.png", TRUE, "已生成类别指标图。")

    quantiles <- quantile(safe_numeric(df[[numeric_cols[1]]]), probs = seq(0, 1, 0.25), na.rm = TRUE, names = FALSE)
    if (length(unique(quantiles)) >= 2) {
      bands <- cut(safe_numeric(df[[numeric_cols[1]]]), breaks = unique(quantiles), include.lowest = TRUE)
      price_band_df <- as.data.frame(table(df[[category_col]], bands)); names(price_band_df) <- c("category", "band", "count")
      safe_write_csv(price_band_df, file.path(workflow_dir, "category_price_band_summary.csv")); record_method("category_price_band_summary", "category_price_band_summary.csv", TRUE, "已生成类别价格带摘要。")
    } else {
      record_method("category_price_band_summary", "category_price_band_summary.csv", FALSE, "价格带分位不足以形成有效分组。")
    }
  } else {
    for (method in c("category_metric_summary","category_metric_plot","category_price_band_summary")) {
      output <- switch(method, category_metric_summary = "category_metric_summary.csv", category_metric_plot = "category_metric_plot.png", category_price_band_summary = "category_price_band_summary.csv")
      record_method(method, output, FALSE, "缺少可用数值字段。")
    }
  }
} else {
  for (method in c("top_categories","category_share_summary","category_mix_plot","category_metric_summary","category_metric_plot","category_price_band_summary","category_pareto")) {
    output <- switch(method, top_categories = "top_categories.csv", category_share_summary = "category_share_summary.csv", category_mix_plot = "category_mix.png", category_metric_summary = "category_metric_summary.csv", category_metric_plot = "category_metric_plot.png", category_price_band_summary = "category_price_band_summary.csv", category_pareto = "category_pareto.png")
    record_method(method, output, FALSE, "缺少可用类别字段。")
  }
}

if (length(date_cols) > 0 && length(numeric_cols) > 0) {
  parsed <- safe_parse_datetime(df[[date_cols[1]]]); valid <- !is.na(parsed)
  if (sum(valid) > 1) {
    trend_df <- aggregate(df[[numeric_cols[1]]][valid], list(period = as.Date(parsed[valid])), mean, na.rm = TRUE); names(trend_df)[2] <- "value"
    safe_write_csv(trend_df, file.path(workflow_dir, "temporal_trend.csv")); record_method("temporal_trend", "temporal_trend.csv", TRUE, "已生成时间趋势。")
    growth_df <- trend_df; growth_df$delta <- c(NA, diff(growth_df$value)); growth_df$growth_rate <- c(NA, growth_df$delta[-1] / head(growth_df$value, -1))
    safe_write_csv(growth_df, file.path(workflow_dir, "temporal_growth.csv")); record_method("temporal_growth", "temporal_growth.csv", TRUE, "已生成时间增长率。")
    ma_df <- trend_df
    ma_df$moving_avg_3 <- if (nrow(ma_df) >= 3) stats::filter(ma_df$value, rep(1/3, 3), sides = 1) else rep(NA_real_, nrow(ma_df))
    safe_write_csv(ma_df, file.path(workflow_dir, "temporal_moving_average.csv")); record_method("temporal_moving_average", "temporal_moving_average.csv", TRUE, "已生成移动平均。")
    profile_df <- data.frame(period_bucket = weekdays(as.Date(parsed[valid])), value = df[[numeric_cols[1]]][valid]); profile_df <- aggregate(profile_df$value, list(period_bucket = profile_df$period_bucket), mean, na.rm = TRUE); names(profile_df)[2] <- "mean_value"
    safe_write_csv(profile_df, file.path(workflow_dir, "temporal_period_profile.csv")); record_method("temporal_period_profile", "temporal_period_profile.csv", TRUE, "已生成周期画像。")

    png(file.path(workflow_dir, "temporal_trend.png"), width = 1400, height = 900)
    if (use_ggplot2) { p <- ggplot2::ggplot(trend_df, ggplot2::aes(x = period, y = value)) + ggplot2::geom_line(color = "#59A14F", linewidth = 1.2) + ggplot2::geom_point(color = "#59A14F", size = 2.2) + ggplot2::theme_minimal(base_size = 14) + ggplot2::labs(title = paste("Trend of", numeric_cols[1]), x = date_cols[1], y = numeric_cols[1]); print(p) } else { plot(trend_df$period, trend_df$value, type = "l", lwd = 2, col = "#59A14F", main = paste("Trend of", numeric_cols[1]), xlab = date_cols[1], ylab = numeric_cols[1]) }
    dev.off(); record_method("temporal_trend_plot", "temporal_trend.png", TRUE, "已生成时间趋势图。")

    png(file.path(workflow_dir, "temporal_growth.png"), width = 1400, height = 900)
    if (use_ggplot2) { p <- ggplot2::ggplot(growth_df, ggplot2::aes(x = period, y = growth_rate)) + ggplot2::geom_col(fill = "#E76F51") + ggplot2::theme_minimal(base_size = 14) + ggplot2::labs(title = "Temporal Growth Rate", x = date_cols[1], y = "Growth Rate"); print(p) } else { barplot(growth_df$growth_rate, names.arg = growth_df$period, las = 2, col = "#E76F51", main = "Temporal Growth Rate") }
    dev.off(); record_method("temporal_growth_plot", "temporal_growth.png", TRUE, "已生成时间增长图。")

    png(file.path(workflow_dir, "temporal_period_plot.png"), width = 1400, height = 900)
    if (use_ggplot2) { p <- ggplot2::ggplot(profile_df, ggplot2::aes(x = reorder(period_bucket, mean_value), y = mean_value)) + ggplot2::geom_col(fill = "#8AB17D") + ggplot2::coord_flip() + ggplot2::theme_minimal(base_size = 14) + ggplot2::labs(title = "Period Profile", x = NULL, y = numeric_cols[1]); print(p) } else { barplot(profile_df$mean_value, names.arg = profile_df$period_bucket, las = 2, col = "#8AB17D", main = "Period Profile") }
    dev.off(); record_method("temporal_period_plot", "temporal_period_plot.png", TRUE, "已生成周期画像图。")
  } else {
    for (method in c("temporal_trend","temporal_growth","temporal_moving_average","temporal_period_profile","temporal_trend_plot","temporal_growth_plot","temporal_period_plot")) {
      output <- switch(method, temporal_trend = "temporal_trend.csv", temporal_growth = "temporal_growth.csv", temporal_moving_average = "temporal_moving_average.csv", temporal_period_profile = "temporal_period_profile.csv", temporal_trend_plot = "temporal_trend.png", temporal_growth_plot = "temporal_growth.png", temporal_period_plot = "temporal_period_plot.png")
      record_method(method, output, FALSE, "可解析时间样本不足。")
    }
  }
} else {
  for (method in c("temporal_trend","temporal_growth","temporal_moving_average","temporal_period_profile","temporal_trend_plot","temporal_growth_plot","temporal_period_plot")) {
    output <- switch(method, temporal_trend = "temporal_trend.csv", temporal_growth = "temporal_growth.csv", temporal_moving_average = "temporal_moving_average.csv", temporal_period_profile = "temporal_period_profile.csv", temporal_trend_plot = "temporal_trend.png", temporal_growth_plot = "temporal_growth.png", temporal_period_plot = "temporal_period_plot.png")
    record_method(method, output, FALSE, "缺少可用时间字段或数值字段。")
  }
}

missing_profile <- data.frame(column = names(df), missing_count = sapply(df, function(col) sum(is.na(col))), missing_ratio = sapply(df, function(col) mean(is.na(col))))
safe_write_csv(missing_profile, file.path(workflow_dir, "missing_profile.csv")); record_method("missing_profile", "missing_profile.csv", TRUE, "已生成缺失值画像。")

duplicate_profile <- data.frame(metric = c("row_count", "duplicated_rows", "duplicate_ratio"), value = c(nrow(df), sum(duplicated(df)), ifelse(nrow(df) == 0, 0, sum(duplicated(df)) / nrow(df))))
safe_write_csv(duplicate_profile, file.path(workflow_dir, "duplicate_profile.csv")); record_method("duplicate_profile", "duplicate_profile.csv", TRUE, "已生成重复值画像。")

if (all(c("page_views", "cart_count", "fav_count", "buy_count") %in% names(df))) {
  funnel_metrics <- data.frame(stage = c("page_views", "cart_count", "fav_count", "buy_count"), total = c(sum(df$page_views, na.rm = TRUE), sum(df$cart_count, na.rm = TRUE), sum(df$fav_count, na.rm = TRUE), sum(df$buy_count, na.rm = TRUE)))
  funnel_metrics$conversion_to_next <- c(safe_ratio(funnel_metrics$total[2], funnel_metrics$total[1]), safe_ratio(funnel_metrics$total[3], funnel_metrics$total[2]), safe_ratio(funnel_metrics$total[4], funnel_metrics$total[3]), NA_real_)
  safe_write_csv(funnel_metrics, file.path(workflow_dir, "funnel_metrics.csv")); record_method("funnel_metrics", "funnel_metrics.csv", TRUE, "已生成漏斗总量。")
  conversion_df <- data.frame(from_stage = funnel_metrics$stage[-length(funnel_metrics$stage)], to_stage = funnel_metrics$stage[-1], conversion_rate = funnel_metrics$conversion_to_next[-length(funnel_metrics$conversion_to_next)])
  safe_write_csv(conversion_df, file.path(workflow_dir, "funnel_conversion_summary.csv")); record_method("funnel_conversion_summary", "funnel_conversion_summary.csv", TRUE, "已生成漏斗转化摘要。")
  png(file.path(workflow_dir, "funnel_overview.png"), width = 1400, height = 900)
  if (use_ggplot2) { p <- ggplot2::ggplot(funnel_metrics, ggplot2::aes(x = stage, y = total, fill = stage)) + ggplot2::geom_col(show.legend = FALSE, width = 0.34) + ggplot2::theme_minimal(base_size = 14) + ggplot2::labs(title = "Behavior Funnel Overview", x = NULL, y = "Total"); print(p) } else { barplot(funnel_metrics$total, names.arg = funnel_metrics$stage, col = "#4E79A7", main = "Behavior Funnel Overview", width = 0.55, space = 0.7) }
  dev.off(); record_method("funnel_overview_plot", "funnel_overview.png", TRUE, "已生成漏斗图。")
} else {
  for (method in c("funnel_metrics","funnel_conversion_summary","funnel_overview_plot")) {
    output <- switch(method, funnel_metrics = "funnel_metrics.csv", funnel_conversion_summary = "funnel_conversion_summary.csv", funnel_overview_plot = "funnel_overview.png")
    record_method(method, output, FALSE, "缺少漏斗字段。")
  }
}

item_col <- NULL
for (candidate in c("item_id", "SKU", "sku", "Product", "product")) {
  if (candidate %in% names(df)) { item_col <- candidate; break }
}

if (!is.null(item_col) && length(numeric_cols) > 0) {
  selected_item_metric_cols <- numeric_cols
  item_metric_frames <- lapply(selected_item_metric_cols, function(metric_col) {
    item_metric <- aggregate(df[[metric_col]], list(item = df[[item_col]]), sum, na.rm = TRUE); names(item_metric)[2] <- "total_value"; item_metric <- head(item_metric[order(item_metric$total_value, decreasing = TRUE), ], 30)
    item_metric$metric <- metric_col
    item_metric
  })
  item_metric <- do.call(rbind, item_metric_frames)
  safe_write_csv(item_metric[, c("item", "metric", "total_value")], file.path(workflow_dir, "top_items.csv")); record_method("top_items", "top_items.csv", TRUE, "已生成头部对象多指标摘要。")
  item_summary_frames <- lapply(selected_item_metric_cols, function(metric_col) {
    item_summary <- aggregate(df[[metric_col]], list(item = df[[item_col]]), mean, na.rm = TRUE); names(item_summary)[2] <- "mean_value"; item_summary <- head(item_summary[order(item_summary$mean_value, decreasing = TRUE), ], 30)
    item_summary$metric <- metric_col
    item_summary
  })
  item_summary <- do.call(rbind, item_summary_frames)
  safe_write_csv(item_summary[, c("item", "metric", "mean_value")], file.path(workflow_dir, "item_metric_summary.csv")); record_method("item_metric_summary", "item_metric_summary.csv", TRUE, "已生成对象多指标摘要。")
  png(file.path(workflow_dir, "top_items_plot.png"), width = 1400, height = 900)
  if (use_ggplot2) { item_metric$item_key <- paste(item_metric$item, item_metric$metric, sep = " | "); item_metric$item_key <- factor(item_metric$item_key, levels = unique(item_metric$item_key)); p <- ggplot2::ggplot(item_metric, ggplot2::aes(x = item_key, y = total_value)) + ggplot2::geom_col(fill = "#577590", width = 0.34) + ggplot2::coord_flip() + ggplot2::facet_wrap(~metric, scales = "free_y", ncol = 2) + ggplot2::scale_x_discrete(labels = function(x) sub(" \\| .*?$", "", x)) + ggplot2::theme_minimal(base_size = 14) + ggplot2::labs(title = paste("Top", item_col, "Overview"), x = NULL, y = "Total value"); print(p) } else { plot_metrics <- unique(item_metric$metric); plot_count <- min(length(plot_metrics), 4); old_par <- par(no.readonly = TRUE); par(mfrow = c(plot_count, 1), mar = c(4, 8, 3, 1)); for (metric_name in plot_metrics[seq_len(plot_count)]) { subset_df <- item_metric[item_metric$metric == metric_name, , drop = FALSE]; barplot(subset_df$total_value, names.arg = subset_df$item, las = 2, horiz = TRUE, col = "#577590", main = metric_name, width = 0.55, space = 0.7) }; par(old_par) }
  dev.off(); record_method("top_items_plot", "top_items_plot.png", TRUE, "已生成头部对象图。")
  if (length(date_cols) > 0) {
    parsed <- safe_parse_datetime(df[[date_cols[1]]]); valid <- !is.na(parsed)
    if (sum(valid) > 1) {
      daily_frames <- lapply(selected_item_metric_cols, function(metric_col) { daily_item <- aggregate(df[[metric_col]][valid], list(period = as.Date(parsed[valid]), item = df[[item_col]][valid]), sum, na.rm = TRUE); names(daily_item)[3] <- "total_value"; daily_item$metric <- metric_col; head(daily_item[order(daily_item$total_value, decreasing = TRUE), ], 200) })
      daily_item <- do.call(rbind, daily_frames)
      safe_write_csv(daily_item[, c("period", "item", "metric", "total_value")], file.path(workflow_dir, "item_daily_summary.csv")); record_method("item_daily_summary", "item_daily_summary.csv", TRUE, "已生成对象多指标日级摘要。")
    } else {
      record_method("item_daily_summary", "item_daily_summary.csv", FALSE, "对象日级时间样本不足。")
    }
  } else {
    record_method("item_daily_summary", "item_daily_summary.csv", FALSE, "缺少时间字段。")
  }
} else {
  for (method in c("top_items","item_metric_summary","top_items_plot","item_daily_summary")) {
    output <- switch(method, top_items = "top_items.csv", item_metric_summary = "item_metric_summary.csv", top_items_plot = "top_items_plot.png", item_daily_summary = "item_daily_summary.csv")
    record_method(method, output, FALSE, "缺少对象字段或数值字段。")
  }
}

if (length(numeric_cols) > 0) {
  series <- safe_numeric(df[[numeric_cols[1]]]); q1 <- quantile(series, 0.25, na.rm = TRUE, names = FALSE); q3 <- quantile(series, 0.75, na.rm = TRUE, names = FALSE); iqr <- q3 - q1; lower <- q1 - 1.5 * iqr; upper <- q3 + 1.5 * iqr
  outlier_idx <- which(series < lower | series > upper)
  if (length(outlier_idx) > 0) { outlier_records <- head(df[outlier_idx, , drop = FALSE], 100); safe_write_csv(outlier_records, file.path(workflow_dir, "outlier_records.csv")); record_method("outlier_records", "outlier_records.csv", TRUE, "已生成异常样本明细。") } else { record_method("outlier_records", "outlier_records.csv", FALSE, "当前没有显著异常样本。") }
} else {
  record_method("outlier_records", "outlier_records.csv", FALSE, "缺少可用数值字段。")
}

method_log <- data.frame(method = method_names, output = method_outputs, status = method_status, note = method_notes)
safe_write_csv(method_log, file.path(workflow_dir, "method_log.csv"))
'''
    temporal_block_replacement = r'''if (length(date_cols) > 0 && length(numeric_cols) > 0) {
  temporal_metric_cols <- numeric_cols
  parsed <- safe_parse_datetime(df[[date_cols[1]]]); valid <- !is.na(parsed)
  if (sum(valid) > 1 && length(temporal_metric_cols) > 0) {
    period_dates <- as.Date(parsed[valid])
    long_temporal <- do.call(rbind, lapply(temporal_metric_cols, function(metric_col) {
      data.frame(period = period_dates, metric = metric_col, value = safe_numeric(df[[metric_col]][valid]), stringsAsFactors = FALSE)
    }))
    long_temporal <- long_temporal[!is.na(long_temporal$value), , drop = FALSE]
    if (nrow(long_temporal) > 0) {
      trend_df <- aggregate(value ~ period + metric, long_temporal, mean, na.rm = TRUE)
      trend_df <- trend_df[order(trend_df$metric, trend_df$period), , drop = FALSE]
      safe_write_csv(trend_df, file.path(workflow_dir, "temporal_trend.csv")); record_method("temporal_trend", "temporal_trend.csv", TRUE, "已按时间输出多指标趋势。")

      growth_parts <- lapply(split(trend_df, trend_df$metric), function(metric_df) {
        metric_df <- metric_df[order(metric_df$period), , drop = FALSE]
        if (nrow(metric_df) <= 1) {
          return(data.frame(
            metric = character(),
            period_from = as.Date(character()),
            period_to = as.Date(character()),
            period_pair = character(),
            value_from = numeric(),
            value_to = numeric(),
            delta = numeric(),
            growth_rate = numeric(),
            growth_pct_label = character(),
            direction = character(),
            stringsAsFactors = FALSE
          ))
        }
        prev_values <- head(metric_df$value, -1)
        next_values <- metric_df$value[-1]
        delta <- next_values - prev_values
        growth_rate <- ifelse(is.na(prev_values) | prev_values == 0, NA_real_, delta / prev_values)
        data.frame(
          metric = metric_df$metric[-1],
          period_from = metric_df$period[-nrow(metric_df)],
          period_to = metric_df$period[-1],
          period_pair = paste(format(metric_df$period[-nrow(metric_df)], "%Y-%m-%d"), "→", format(metric_df$period[-1], "%Y-%m-%d")),
          value_from = prev_values,
          value_to = next_values,
          delta = delta,
          growth_rate = growth_rate,
          growth_pct_label = ifelse(is.na(growth_rate), "n/a", paste0(sprintf("%.1f", growth_rate * 100), "%")),
          label_text = ifelse(
            is.na(growth_rate),
            paste0("Δ", sprintf("%+.1f", delta), "\n", sprintf("%.1f→%.1f", prev_values, next_values)),
            paste0(
              paste(format(metric_df$period[-nrow(metric_df)], "%Y-%m-%d"), "→", format(metric_df$period[-1], "%Y-%m-%d")),
              "\n",
              sprintf("%.1f%%", growth_rate * 100),
              " | Δ",
              sprintf("%+.1f", delta),
              "\n",
              sprintf("%.1f→%.1f", prev_values, next_values)
            )
          ),
          direction = ifelse(is.na(growth_rate), "unknown", ifelse(growth_rate >= 0, "增长", "下降")),
          stringsAsFactors = FALSE
        )
      })
      growth_df <- do.call(rbind, growth_parts); rownames(growth_df) <- NULL
      safe_write_csv(growth_df, file.path(workflow_dir, "temporal_growth.csv")); record_method("temporal_growth", "temporal_growth.csv", TRUE, "已按时间输出多指标增长率。")

      ma_parts <- lapply(split(trend_df, trend_df$metric), function(metric_df) {
        metric_df <- metric_df[order(metric_df$period), , drop = FALSE]
        metric_df$moving_avg_3 <- if (nrow(metric_df) >= 3) as.numeric(stats::filter(metric_df$value, rep(1/3, 3), sides = 1)) else rep(NA_real_, nrow(metric_df))
        metric_df
      })
      ma_df <- do.call(rbind, ma_parts); rownames(ma_df) <- NULL
      safe_write_csv(ma_df, file.path(workflow_dir, "temporal_moving_average.csv")); record_method("temporal_moving_average", "temporal_moving_average.csv", TRUE, "已按时间输出多指标移动平均。")

      profile_source <- long_temporal
      profile_source$period_bucket <- weekdays(profile_source$period)
      bucket_levels <- unique(profile_source$period_bucket)
      profile_df <- aggregate(value ~ period_bucket + metric, profile_source, mean, na.rm = TRUE)
      names(profile_df)[3] <- "mean_value"
      profile_df$period_bucket <- factor(profile_df$period_bucket, levels = bucket_levels)
      profile_df <- profile_df[order(profile_df$metric, profile_df$period_bucket), , drop = FALSE]
      safe_write_csv(profile_df, file.path(workflow_dir, "temporal_period_profile.csv")); record_method("temporal_period_profile", "temporal_period_profile.csv", TRUE, "已按时间输出多指标周期画像。")

      temporal_plot_height <- max(900, 360 * ceiling(length(unique(trend_df$metric)) / 2))

      png(file.path(workflow_dir, "temporal_trend.png"), width = 1600, height = temporal_plot_height)
      if (use_ggplot2) {
        p <- ggplot2::ggplot(trend_df, ggplot2::aes(x = period, y = value, group = metric, color = metric)) +
          ggplot2::geom_line(linewidth = 1.1) +
          ggplot2::geom_point(size = 1.8) +
          ggplot2::facet_wrap(~metric, scales = "free_y", ncol = 2) +
          ggplot2::theme_minimal(base_size = 14) +
          ggplot2::theme(legend.position = "none") +
          ggplot2::labs(title = paste("Temporal Trend by", date_cols[1]), x = date_cols[1], y = "Mean value")
        print(p)
      } else {
        plot_metrics <- unique(trend_df$metric)
        plot_count <- min(length(plot_metrics), 4)
        old_par <- par(no.readonly = TRUE)
        par(mfrow = c(plot_count, 1), mar = c(4, 4, 3, 1))
        for (metric_name in plot_metrics[seq_len(plot_count)]) {
          metric_df <- trend_df[trend_df$metric == metric_name, , drop = FALSE]
          plot(metric_df$period, metric_df$value, type = "l", lwd = 2, col = "#59A14F", main = paste("Trend of", metric_name), xlab = date_cols[1], ylab = "Mean value")
        }
        par(old_par)
      }
      dev.off(); record_method("temporal_trend_plot", "temporal_trend.png", TRUE, "已生成多指标时间趋势图。")

      png(file.path(workflow_dir, "temporal_growth.png"), width = 1600, height = temporal_plot_height)
      growth_plot_df <- growth_df[!is.na(growth_df$growth_rate), , drop = FALSE]
      if (nrow(growth_plot_df) > 0) {
        growth_plot_df$label_y <- ifelse(abs(growth_plot_df$growth_rate) < 0.02, ifelse(growth_plot_df$growth_rate >= 0, 0.015, -0.015), growth_plot_df$growth_rate / 2)
        growth_plot_df$label_color <- ifelse(abs(growth_plot_df$growth_rate) < 0.02, "#222222", "white")
        if (use_ggplot2) {
          growth_plot_df$period_pair <- factor(growth_plot_df$period_pair, levels = unique(growth_plot_df$period_pair))
          p <- ggplot2::ggplot(growth_plot_df, ggplot2::aes(x = period_pair, y = growth_rate, fill = direction)) +
            ggplot2::geom_hline(yintercept = 0, linewidth = 0.5, color = "#777777") +
            ggplot2::geom_col(show.legend = FALSE, width = 0.32) +
            ggplot2::geom_text(
              ggplot2::aes(
                label = label_text,
                y = label_y,
                color = label_color
              ),
              vjust = 0.5,
              lineheight = 0.95,
              size = 3.5,
              show.legend = FALSE,
              fontface = "bold"
            ) +
            ggplot2::facet_wrap(~metric, scales = "free_y", ncol = 2) +
            ggplot2::scale_fill_manual(values = c("增长" = "#2A9D8F", "下降" = "#E76F51", "unknown" = "#9AA0A6")) +
            ggplot2::scale_color_identity() +
            ggplot2::scale_y_continuous(expand = ggplot2::expansion(mult = c(0.18, 0.18))) +
            ggplot2::theme_minimal(base_size = 14) +
            ggplot2::theme(
              legend.position = "none",
              axis.text.x = ggplot2::element_text(angle = 20, hjust = 1),
              plot.margin = ggplot2::margin(12, 28, 12, 12)
            ) +
            ggplot2::labs(
              title = paste("Temporal Growth by", date_cols[1]),
              subtitle = "标签=时间区间 | 增长率 | Δ值 | 前值→后值",
              x = "期间对比",
              y = "增长率"
            )
        print(p)
      } else {
          plot_metrics <- unique(growth_plot_df$metric)
          plot_count <- min(length(plot_metrics), 4)
          old_par <- par(no.readonly = TRUE)
          par(mfrow = c(plot_count, 1), mar = c(4, 10, 3, 2))
          for (metric_name in plot_metrics[seq_len(plot_count)]) {
            metric_df <- growth_plot_df[growth_plot_df$metric == metric_name, , drop = FALSE]
            colors <- ifelse(metric_df$growth_rate >= 0, "#2A9D8F", "#E76F51")
            mids <- barplot(metric_df$growth_rate, names.arg = metric_df$period_pair, las = 2, horiz = TRUE, col = colors, main = paste("Growth of", metric_name), xlab = "增长率", width = 0.5, space = 0.75)
            text(metric_df$growth_rate, mids, labels = paste0(metric_df$growth_pct_label, " (", sprintf("%+.1f", metric_df$delta), ")"), pos = ifelse(metric_df$growth_rate >= 0, 4, 2), cex = 0.9)
          }
          par(old_par)
        }
        dev.off(); record_method("temporal_growth_plot", "temporal_growth.png", TRUE, "已生成可解释的多指标时间增长图。")
      } else {
        dev.off(); record_method("temporal_growth_plot", "temporal_growth.png", FALSE, "时间增长缺少可解释的有效变化样本。")
      }

      png(file.path(workflow_dir, "temporal_period_plot.png"), width = 1600, height = temporal_plot_height)
      if (use_ggplot2) {
        p <- ggplot2::ggplot(profile_df, ggplot2::aes(x = period_bucket, y = mean_value, fill = metric)) +
          ggplot2::geom_col(show.legend = FALSE, width = 0.34) +
          ggplot2::coord_flip() +
          ggplot2::facet_wrap(~metric, scales = "free_x", ncol = 2) +
          ggplot2::theme_minimal(base_size = 14) +
          ggplot2::labs(title = "Period Profile", x = NULL, y = "Mean value")
        print(p)
      } else {
        plot_metrics <- unique(profile_df$metric)
        plot_count <- min(length(plot_metrics), 4)
        old_par <- par(no.readonly = TRUE)
        par(mfrow = c(plot_count, 1), mar = c(4, 6, 3, 1))
        for (metric_name in plot_metrics[seq_len(plot_count)]) {
          metric_df <- profile_df[profile_df$metric == metric_name, , drop = FALSE]
          barplot(metric_df$mean_value, names.arg = metric_df$period_bucket, las = 2, horiz = TRUE, col = "#8AB17D", main = paste("Period Profile -", metric_name), width = 0.5, space = 0.75)
        }
        par(old_par)
      }
      dev.off(); record_method("temporal_period_plot", "temporal_period_plot.png", TRUE, "已生成多指标周期画像图。")
    } else {
      for (method in c("temporal_trend","temporal_growth","temporal_moving_average","temporal_period_profile","temporal_trend_plot","temporal_growth_plot","temporal_period_plot")) {
        output <- switch(method, temporal_trend = "temporal_trend.csv", temporal_growth = "temporal_growth.csv", temporal_moving_average = "temporal_moving_average.csv", temporal_period_profile = "temporal_period_profile.csv", temporal_trend_plot = "temporal_trend.png", temporal_growth_plot = "temporal_growth.png", temporal_period_plot = "temporal_period_plot.png")
        record_method(method, output, FALSE, "时间字段存在，但没有形成可用的多指标时间样本。")
      }
    }
  } else {
    for (method in c("temporal_trend","temporal_growth","temporal_moving_average","temporal_period_profile","temporal_trend_plot","temporal_growth_plot","temporal_period_plot")) {
      output <- switch(method, temporal_trend = "temporal_trend.csv", temporal_growth = "temporal_growth.csv", temporal_moving_average = "temporal_moving_average.csv", temporal_period_profile = "temporal_period_profile.csv", temporal_trend_plot = "temporal_trend.png", temporal_growth_plot = "temporal_growth.png", temporal_period_plot = "temporal_period_plot.png")
      record_method(method, output, FALSE, "可解析时间样本不足。")
    }
  }
} else {
  for (method in c("temporal_trend","temporal_growth","temporal_moving_average","temporal_period_profile","temporal_trend_plot","temporal_growth_plot","temporal_period_plot")) {
    output <- switch(method, temporal_trend = "temporal_trend.csv", temporal_growth = "temporal_growth.csv", temporal_moving_average = "temporal_moving_average.csv", temporal_period_profile = "temporal_period_profile.csv", temporal_trend_plot = "temporal_trend.png", temporal_growth_plot = "temporal_growth.png", temporal_period_plot = "temporal_period_plot.png")
    record_method(method, output, FALSE, "缺少可用时间字段或数值字段。")
  }
}

missing_profile <- data.frame('''
    category_block_replacement = r'''selected_category_cols <- preferred_category_cols[preferred_category_cols %in% names(df)]
if (length(selected_category_cols) == 0) {
category_candidates <- char_cols[!char_cols %in% date_cols]
category_candidates <- category_candidates[!grepl("date|time|period|day|month|year", tolower(category_candidates))]
preferred_category_candidates <- category_candidates[
  grepl("category|类|品类|类目|supplier|vendor|seller|brand|channel|segment|group|department|center|responsibility|region|product|sku", tolower(category_candidates))
]
bounded_category_candidates <- category_candidates[sapply(category_candidates, function(col) {
  unique_count <- length(unique(na.omit(df[[col]])))
  unique_count >= 2 && unique_count <= max(12, min(50, floor(nrow(df) * 0.6)))
})]
selected_category_cols <- unique(c(intersect(c("category_id"), names(df)), preferred_category_candidates, bounded_category_candidates, category_candidates))
selected_category_cols <- selected_category_cols[!selected_category_cols %in% preferred_object_cols]
}
if (length(selected_category_cols) > 0) {
  top_frames <- lapply(selected_category_cols, function(category_col) {
    counts <- sort(table(df[[category_col]]), decreasing = TRUE)
    top_counts <- head(counts, 15)
    data.frame(dimension = category_col, category = names(top_counts), count = as.integer(top_counts), stringsAsFactors = FALSE)
  })
  top_df <- do.call(rbind, top_frames)
  safe_write_csv(top_df, file.path(workflow_dir, "top_categories.csv")); record_method("top_categories", "top_categories.csv", TRUE, "已生成多分类维度头部类别摘要。")

  share_frames <- lapply(selected_category_cols, function(category_col) {
    counts <- sort(table(df[[category_col]]), decreasing = TRUE)
    top_counts <- head(counts, 15)
    frame <- data.frame(dimension = category_col, category = names(top_counts), count = as.integer(top_counts), stringsAsFactors = FALSE)
    frame$share <- frame$count / sum(counts)
    frame$cumulative_share <- cumsum(frame$share)
    frame$category_key <- paste(category_col, frame$category, sep = " | ")
    frame
  })
  share_df <- do.call(rbind, share_frames)
  safe_write_csv(share_df[, c("dimension", "category", "count", "share", "cumulative_share")], file.path(workflow_dir, "category_share_summary.csv")); record_method("category_share_summary", "category_share_summary.csv", TRUE, "已生成多分类维度占比与累计占比。")

  category_plot_height <- max(900, 360 * ceiling(length(selected_category_cols) / 2))
  png(file.path(workflow_dir, "category_mix.png"), width = 1600, height = category_plot_height)
  if (use_ggplot2) {
    top_df$category_key <- paste(top_df$dimension, top_df$category, sep = " | ")
    top_df$category_key <- factor(top_df$category_key, levels = unique(top_df$category_key))
    p <- ggplot2::ggplot(top_df, ggplot2::aes(x = category_key, y = count)) +
      ggplot2::geom_col(fill = "#F28E2B", width = 0.34) +
      ggplot2::coord_flip() +
      ggplot2::facet_wrap(~dimension, scales = "free_y", ncol = 2) +
      ggplot2::scale_x_discrete(labels = function(x) sub("^.* \\| ", "", x)) +
      ggplot2::theme_minimal(base_size = 14) +
      ggplot2::labs(title = "Category Mix Overview", subtitle = "按所有可用分类维度展开", x = NULL, y = "Count")
    print(p)
  } else {
    plot_count <- min(length(selected_category_cols), 6)
    old_par <- par(no.readonly = TRUE)
    par(mfrow = c(ceiling(plot_count / 2), 2), mar = c(5, 8, 3, 1))
    for (category_col in selected_category_cols[seq_len(plot_count)]) {
      subset_df <- top_df[top_df$dimension == category_col, , drop = FALSE]
      barplot(subset_df$count, names.arg = subset_df$category, las = 2, horiz = TRUE, col = "#F28E2B", main = category_col, width = 0.55, space = 0.7)
    }
    par(old_par)
  }
  dev.off(); record_method("category_mix_plot", "category_mix.png", TRUE, "已生成多分类维度结构图。")

  png(file.path(workflow_dir, "category_pareto.png"), width = 1600, height = category_plot_height)
  pareto_note <- "柱=单类占比，折线=累计占比；如果某个维度类别过少，主要看是否均衡分布。"
  if (use_ggplot2) {
    share_df$category_key <- factor(share_df$category_key, levels = unique(share_df$category_key))
    p <- ggplot2::ggplot(share_df, ggplot2::aes(x = category_key)) +
      ggplot2::geom_col(ggplot2::aes(y = share * 100), fill = "#E9C46A", color = "#8D6E00", width = 0.34) +
      ggplot2::geom_text(
        ggplot2::aes(y = share * 100, label = paste0(count, " / ", sprintf("%.1f%%", share * 100))),
        vjust = -0.35,
        size = 3.3,
        color = "#333333",
        fontface = "bold"
      ) +
      ggplot2::geom_line(
        ggplot2::aes(y = cumulative_share * 100, group = 1),
        color = "#D62828",
        linewidth = 1.0
      ) +
      ggplot2::geom_point(
        ggplot2::aes(y = cumulative_share * 100),
        color = "#D62828",
        size = 2.2
      ) +
      ggplot2::geom_text(
        ggplot2::aes(y = cumulative_share * 100, label = paste0(sprintf("%.1f", cumulative_share * 100), "%")),
        color = "#D62828",
        nudge_y = 4,
        size = 3.2,
        fontface = "bold"
      ) +
      ggplot2::facet_wrap(~dimension, scales = "free_x", ncol = 2) +
      ggplot2::scale_x_discrete(labels = function(x) sub("^.* \\| ", "", x)) +
      ggplot2::coord_cartesian(ylim = c(0, 110)) +
      ggplot2::theme_minimal(base_size = 14) +
      ggplot2::theme(axis.text.x = ggplot2::element_text(angle = 30, hjust = 1)) +
      ggplot2::labs(title = "Category Pareto Overview", subtitle = pareto_note, x = NULL, y = "占比")
    print(p)
  } else {
    plot_count <- min(length(selected_category_cols), 6)
    old_par <- par(no.readonly = TRUE)
    par(mfrow = c(ceiling(plot_count / 2), 2), mar = c(8, 5, 4, 4))
    for (category_col in selected_category_cols[seq_len(plot_count)]) {
      subset_df <- share_df[share_df$dimension == category_col, , drop = FALSE]
      mids <- barplot(subset_df$share * 100, names.arg = subset_df$category, las = 2, col = "#E9C46A", border = "#8D6E00", width = 0.55, space = 0.7, ylim = c(0, 110), main = category_col, ylab = "占比")
      lines(mids, subset_df$cumulative_share * 100, type = "b", col = "#D62828", pch = 19)
      text(mids, subset_df$share * 100, labels = paste0(subset_df$count, " / ", sprintf("%.1f%%", subset_df$share * 100)), pos = 3, cex = 0.85)
      text(mids, subset_df$cumulative_share * 100, labels = paste0(sprintf("%.1f", subset_df$cumulative_share * 100), "%"), pos = 3, cex = 0.8, col = "#D62828")
    }
    par(old_par)
  }
  dev.off(); record_method("category_pareto", "category_pareto.png", TRUE, "已生成多分类维度帕累托图。")

  if (length(numeric_cols) > 0) {
    selected_category_metric_cols <- numeric_cols
    category_metric_frames <- lapply(selected_category_cols, function(category_col) {
      do.call(rbind, lapply(selected_category_metric_cols, function(metric_col) {
        grouped_metric <- aggregate(df[[metric_col]], list(category = df[[category_col]]), mean, na.rm = TRUE)
        names(grouped_metric)[2] <- "mean_value"
        grouped_metric <- head(grouped_metric[order(grouped_metric$mean_value, decreasing = TRUE), ], 15)
        grouped_metric$dimension <- category_col
        grouped_metric$metric <- metric_col
        grouped_metric
      }))
    })
    category_metric_df <- do.call(rbind, category_metric_frames)
    safe_write_csv(category_metric_df[, c("dimension", "category", "metric", "mean_value")], file.path(workflow_dir, "category_metric_summary.csv")); record_method("category_metric_summary", "category_metric_summary.csv", TRUE, "已生成多分类维度与多指标均值摘要。")

    png(file.path(workflow_dir, "category_metric_plot.png"), width = 1600, height = category_plot_height)
    if (use_ggplot2) {
      category_metric_df$category_key <- paste(category_metric_df$dimension, category_metric_df$category, category_metric_df$metric, sep = " | ")
      category_metric_df$category_key <- factor(category_metric_df$category_key, levels = unique(category_metric_df$category_key))
      p <- ggplot2::ggplot(category_metric_df, ggplot2::aes(x = category_key, y = mean_value)) +
        ggplot2::geom_col(fill = "#2A9D8F", width = 0.34) +
        ggplot2::coord_flip() +
        ggplot2::facet_wrap(~dimension + metric, scales = "free_y", ncol = 2) +
        ggplot2::scale_x_discrete(labels = function(x) sub("^.* \\| .* \\| ", "", x)) +
        ggplot2::theme_minimal(base_size = 14) +
        ggplot2::labs(title = "Category Metric Overview", x = NULL, y = "Mean value")
      print(p)
    } else {
      plot_keys <- unique(paste(category_metric_df$dimension, category_metric_df$metric, sep = " | "))
      plot_count <- min(length(plot_keys), 6)
      old_par <- par(no.readonly = TRUE)
      par(mfrow = c(ceiling(plot_count / 2), 2), mar = c(5, 8, 3, 1))
      for (plot_key in plot_keys[seq_len(plot_count)]) {
        parts <- strsplit(plot_key, " \\| ")[[1]]
        subset_df <- category_metric_df[category_metric_df$dimension == parts[1] & category_metric_df$metric == parts[2], , drop = FALSE]
        barplot(subset_df$mean_value, names.arg = subset_df$category, las = 2, horiz = TRUE, col = "#2A9D8F", main = plot_key, width = 0.55, space = 0.7)
      }
      par(old_par)
    }
    dev.off(); record_method("category_metric_plot", "category_metric_plot.png", TRUE, "已生成多分类维度与多指标图。")

    quantile_source_col <- selected_category_metric_cols[1]
    quantiles <- quantile(safe_numeric(df[[quantile_source_col]]), probs = seq(0, 1, 0.25), na.rm = TRUE, names = FALSE)
    if (length(unique(quantiles)) >= 2) {
      band_frames <- lapply(selected_category_cols, function(category_col) {
        bands <- cut(safe_numeric(df[[quantile_source_col]]), breaks = unique(quantiles), include.lowest = TRUE)
        price_band_df <- as.data.frame(table(df[[category_col]], bands))
        names(price_band_df) <- c("category", "band", "count")
        price_band_df$dimension <- category_col
        price_band_df$metric <- quantile_source_col
        price_band_df
      })
      price_band_df <- do.call(rbind, band_frames)
      safe_write_csv(price_band_df[, c("dimension", "category", "metric", "band", "count")], file.path(workflow_dir, "category_price_band_summary.csv")); record_method("category_price_band_summary", "category_price_band_summary.csv", TRUE, "已生成多分类维度价格带摘要。")
    } else {
      record_method("category_price_band_summary", "category_price_band_summary.csv", FALSE, "价格带分位不足以形成有效分组。")
    }

    available_budget_pairs <- Filter(function(pair) pair$baseline %in% names(df) && pair$actual %in% names(df), preferred_variance_pairs)
    if (length(available_budget_pairs) > 0) {
      budget_frames <- lapply(selected_category_cols, function(category_col) {
        do.call(rbind, lapply(available_budget_pairs, function(pair) {
          budget_df <- aggregate(df[[pair$baseline]], list(category = df[[category_col]]), mean, na.rm = TRUE)
          names(budget_df)[2] <- "budget_mean"
          actual_df <- aggregate(df[[pair$actual]], list(category = df[[category_col]]), mean, na.rm = TRUE)
          names(actual_df)[2] <- "actual_mean"
          merged_df <- merge(budget_df, actual_df, by = "category", all = TRUE)
          merged_df$dimension <- category_col
          merged_df$metric_pair <- paste(pair$baseline, pair$actual, sep = " / ")
          merged_df$metric_family <- pair$family
          merged_df$gap <- merged_df$actual_mean - merged_df$budget_mean
          merged_df$gap_rate <- ifelse(is.na(merged_df$budget_mean) | merged_df$budget_mean == 0, NA_real_, merged_df$gap / abs(merged_df$budget_mean))
          merged_df <- head(merged_df[order(abs(merged_df$gap), decreasing = TRUE), ], 15)
          merged_df
        }))
      })
      budget_variance_df <- do.call(rbind, budget_frames)
      safe_write_csv(budget_variance_df[, c("dimension", "category", "metric_family", "metric_pair", "budget_mean", "actual_mean", "gap", "gap_rate")], file.path(workflow_dir, "budget_variance_summary.csv")); record_method("budget_variance_summary", "budget_variance_summary.csv", TRUE, "已生成预算 vs 实际偏差分层摘要。")
    } else {
      record_method("budget_variance_summary", "budget_variance_summary.csv", FALSE, "缺少预算/实际成对字段。")
    }
  } else {
    for (method in c("category_metric_summary","category_metric_plot","category_price_band_summary","budget_variance_summary")) {
      output <- switch(method, category_metric_summary = "category_metric_summary.csv", category_metric_plot = "category_metric_plot.png", category_price_band_summary = "category_price_band_summary.csv", budget_variance_summary = "budget_variance_summary.csv")
      record_method(method, output, FALSE, "缺少可用数值字段。")
    }
  }
} else {
  for (method in c("top_categories","category_share_summary","category_mix_plot","category_metric_summary","category_metric_plot","category_price_band_summary","category_pareto","budget_variance_summary")) {
    output <- switch(method, top_categories = "top_categories.csv", category_share_summary = "category_share_summary.csv", category_mix_plot = "category_mix.png", category_metric_summary = "category_metric_summary.csv", category_metric_plot = "category_metric_plot.png", category_price_band_summary = "category_price_band_summary.csv", category_pareto = "category_pareto.png", budget_variance_summary = "budget_variance_summary.csv")
    record_method(method, output, FALSE, "缺少可用类别字段。")
  }
}'''
    item_block_replacement = r'''item_col <- NULL
for (candidate in c(preferred_object_cols, "item_id", "SKU", "sku", "Product", "product")) {
  if (candidate %in% names(df)) { item_col <- candidate; break }
}

if (!is.null(item_col) && length(numeric_cols) > 0) {
  selected_item_metric_cols <- head(numeric_cols, 6)
  item_metric_frames <- lapply(selected_item_metric_cols, function(metric_col) {
    item_metric <- aggregate(df[[metric_col]], list(item = df[[item_col]]), sum, na.rm = TRUE); names(item_metric)[2] <- "total_value"; item_metric <- head(item_metric[order(item_metric$total_value, decreasing = TRUE), ], 30)
    item_metric$metric <- metric_col
    item_metric
  })
  item_metric <- do.call(rbind, item_metric_frames)
  safe_write_csv(item_metric[, c("item", "metric", "total_value")], file.path(workflow_dir, "top_items.csv")); record_method("top_items", "top_items.csv", TRUE, "已生成头部对象多指标摘要。")
  item_summary_frames <- lapply(selected_item_metric_cols, function(metric_col) {
    item_summary <- aggregate(df[[metric_col]], list(item = df[[item_col]]), mean, na.rm = TRUE); names(item_summary)[2] <- "mean_value"; item_summary <- head(item_summary[order(item_summary$mean_value, decreasing = TRUE), ], 30)
    item_summary$metric <- metric_col
    item_summary
  })
  item_summary <- do.call(rbind, item_summary_frames)
  safe_write_csv(item_summary[, c("item", "metric", "mean_value")], file.path(workflow_dir, "item_metric_summary.csv")); record_method("item_metric_summary", "item_metric_summary.csv", TRUE, "已生成对象多指标摘要。")
  png(file.path(workflow_dir, "top_items_plot.png"), width = 1400, height = 900)
  if (use_ggplot2) { item_metric$item_key <- paste(item_metric$item, item_metric$metric, sep = " | "); item_metric$item_key <- factor(item_metric$item_key, levels = unique(item_metric$item_key)); p <- ggplot2::ggplot(item_metric, ggplot2::aes(x = item_key, y = total_value)) + ggplot2::geom_col(fill = "#577590", width = 0.34) + ggplot2::coord_flip() + ggplot2::facet_wrap(~metric, scales = "free_y", ncol = 2) + ggplot2::scale_x_discrete(labels = function(x) sub(" \\| .*?$", "", x)) + ggplot2::theme_minimal(base_size = 14) + ggplot2::labs(title = paste("Top", item_col, "Overview"), x = NULL, y = "Total value"); print(p) } else { plot_metrics <- unique(item_metric$metric); plot_count <- min(length(plot_metrics), 4); old_par <- par(no.readonly = TRUE); par(mfrow = c(plot_count, 1), mar = c(4, 8, 3, 1)); for (metric_name in plot_metrics[seq_len(plot_count)]) { subset_df <- item_metric[item_metric$metric == metric_name, , drop = FALSE]; barplot(subset_df$total_value, names.arg = subset_df$item, las = 2, horiz = TRUE, col = "#577590", main = metric_name, width = 0.55, space = 0.7) }; par(old_par) }
  dev.off(); record_method("top_items_plot", "top_items_plot.png", TRUE, "已生成头部对象图。")
  if (length(date_cols) > 0) {
    parsed <- safe_parse_datetime(df[[date_cols[1]]]); valid <- !is.na(parsed)
    if (sum(valid) > 1) {
      daily_frames <- lapply(head(selected_item_metric_cols, 3), function(metric_col) { daily_item <- aggregate(df[[metric_col]][valid], list(period = as.Date(parsed[valid]), item = df[[item_col]][valid]), sum, na.rm = TRUE); names(daily_item)[3] <- "total_value"; daily_item$metric <- metric_col; head(daily_item[order(daily_item$total_value, decreasing = TRUE), ], 200) })
      daily_item <- do.call(rbind, daily_frames)
      safe_write_csv(daily_item[, c("period", "item", "metric", "total_value")], file.path(workflow_dir, "item_daily_summary.csv")); record_method("item_daily_summary", "item_daily_summary.csv", TRUE, "已生成对象多指标日级摘要。")
    } else {
      record_method("item_daily_summary", "item_daily_summary.csv", FALSE, "对象日级时间样本不足。")
    }
  } else {
    record_method("item_daily_summary", "item_daily_summary.csv", FALSE, "缺少时间字段。")
  }
} else {
  for (method in c("top_items","item_metric_summary","top_items_plot","item_daily_summary")) {
    output <- switch(method, top_items = "top_items.csv", item_metric_summary = "item_metric_summary.csv", top_items_plot = "top_items_plot.png", item_daily_summary = "item_daily_summary.csv")
    record_method(method, output, FALSE, "缺少对象字段或数值字段。")
  }
}'''
    pca_cluster_block_replacement = r'''if (length(numeric_cols) > 0) {
  pca_candidate_cols <- numeric_cols[vapply(numeric_cols, function(col) {
    series <- safe_numeric(df[[col]])
    series <- series[!is.na(series)]
    length(series) >= 5 && length(unique(series)) > 1 && !is.na(stats::sd(series)) && stats::sd(series) > 0
  }, logical(1))]
} else {
  pca_candidate_cols <- character(0)
}
excluded_pca_cols <- setdiff(numeric_cols, pca_candidate_cols)
excluded_note <- if (length(excluded_pca_cols) > 0) paste0(" 已自动排除常量/零方差字段：", paste(excluded_pca_cols, collapse = ", ")) else ""
numeric_complete <- na.omit(df[pca_candidate_cols])
complete_row_index <- suppressWarnings(as.integer(rownames(numeric_complete)))
if (length(complete_row_index) != nrow(numeric_complete) || any(is.na(complete_row_index))) {
  complete_row_index <- which(stats::complete.cases(df[pca_candidate_cols]))
}
if (length(pca_candidate_cols) >= 2 && nrow(numeric_complete) >= 5 && ncol(numeric_complete) >= 2) {
  pca_fit <- tryCatch(prcomp(numeric_complete, center = TRUE, scale. = TRUE), error = function(e) e)
  if (!inherits(pca_fit, "error")) {
    variance_df <- data.frame(component = paste0("PC", seq_along(pca_fit$sdev)), std_dev = pca_fit$sdev, variance_explained = (pca_fit$sdev ^ 2) / sum(pca_fit$sdev ^ 2), cumulative_variance = cumsum((pca_fit$sdev ^ 2) / sum(pca_fit$sdev ^ 2)))
    safe_write_csv(variance_df, file.path(workflow_dir, "pca_variance.csv")); record_method("pca_variance", "pca_variance.csv", TRUE, paste0("已生成主成分方差解释。", excluded_note))
    loadings_df <- data.frame(variable = rownames(pca_fit$rotation), pca_fit$rotation, row.names = NULL)
    safe_write_csv(loadings_df, file.path(workflow_dir, "pca_loadings.csv")); record_method("pca_loadings", "pca_loadings.csv", TRUE, paste0("已生成主成分载荷。", excluded_note))
    scores_df <- data.frame(row_index = complete_row_index[seq_len(min(nrow(pca_fit$x), 500))], pca_fit$x[seq_len(min(nrow(pca_fit$x), 500)), , drop = FALSE], row.names = NULL)
    safe_write_csv(scores_df, file.path(workflow_dir, "pca_scores.csv")); record_method("pca_scores", "pca_scores.csv", TRUE, paste0("已生成主成分得分。", excluded_note))

    axis_rows <- do.call(rbind, lapply(seq_len(min(3, nrow(variance_df))), function(idx) {
      component_name <- as.character(variance_df$component[idx])
      loading_slice <- data.frame(variable = loadings_df$variable, loading = loadings_df[[component_name]], stringsAsFactors = FALSE)
      loading_slice <- loading_slice[order(abs(loading_slice$loading), decreasing = TRUE), , drop = FALSE]
      positive_fields <- loading_slice$variable[loading_slice$loading > 0]
      negative_fields <- loading_slice$variable[loading_slice$loading < 0]
      positive_text <- paste(head(positive_fields, 3), collapse = " | ")
      negative_text <- paste(head(negative_fields, 3), collapse = " | ")
      axis_summary <- if (nzchar(positive_text) && nzchar(negative_text)) {
        paste0(positive_text, " vs ", negative_text)
      } else if (nzchar(positive_text)) {
        paste0(positive_text, " 同向变化")
      } else if (nzchar(negative_text)) {
        paste0(negative_text, " 反向变化")
      } else {
        "未识别主导指标"
      }
      data.frame(
        component = component_name,
        variance_explained = variance_df$variance_explained[idx],
        cumulative_variance = variance_df$cumulative_variance[idx],
        positive_drivers = positive_text,
        negative_drivers = negative_text,
        axis_summary = axis_summary,
        stringsAsFactors = FALSE
      )
    }))
    safe_write_csv(axis_rows, file.path(workflow_dir, "pca_axis_summary.csv")); record_method("pca_axis_summary", "pca_axis_summary.csv", TRUE, paste0("已生成主轴业务摘要。", excluded_note))
  } else {
    failure_note <- paste0("PCA 不适用：", conditionMessage(pca_fit), excluded_note)
    record_method("pca_variance", "pca_variance.csv", FALSE, failure_note)
    record_method("pca_loadings", "pca_loadings.csv", FALSE, failure_note)
    record_method("pca_scores", "pca_scores.csv", FALSE, failure_note)
    record_method("pca_axis_summary", "pca_axis_summary.csv", FALSE, failure_note)
  }

  cluster_feature_pool <- numeric_complete[, sapply(names(numeric_complete), function(col) {
    series <- safe_numeric(numeric_complete[[col]])
    series <- series[!is.na(series)]
    length(series) >= 5 && length(unique(series)) > 1 && !is.na(stats::sd(series)) && stats::sd(series) > 0
  }), drop = FALSE]
  cluster_input <- cluster_feature_pool[, seq_len(min(ncol(cluster_feature_pool), 4)), drop = FALSE]
  centers <- min(3, nrow(cluster_input))
  if (ncol(cluster_input) >= 2 && centers >= 2) {
    km <- tryCatch(kmeans(cluster_input, centers = centers), error = function(e) e)
    if (!inherits(km, "error")) {
      cluster_df <- data.frame(row_index = complete_row_index[seq_len(nrow(cluster_input))], cluster = km$cluster, row.names = NULL)
      safe_write_csv(cluster_df, file.path(workflow_dir, "kmeans_clusters.csv")); record_method("kmeans_clusters", "kmeans_clusters.csv", TRUE, paste0("已生成聚类结果。", excluded_note))
      profile_df <- aggregate(cluster_input, list(cluster = km$cluster), mean, na.rm = TRUE)
      safe_write_csv(profile_df, file.path(workflow_dir, "cluster_profile.csv")); record_method("cluster_profile", "cluster_profile.csv", TRUE, paste0("已生成聚类画像。", excluded_note))

      detail_id_cols <- unique(c(preferred_object_cols[preferred_object_cols %in% names(df)], id_like_cols[id_like_cols %in% names(df)]))
      detail_text_cols <- char_cols[char_cols %in% names(df) & !char_cols %in% detail_id_cols & !char_cols %in% date_cols]
      detail_cols <- unique(c(detail_id_cols, head(detail_text_cols, 2), names(cluster_input)))
      if (length(detail_cols) > 0) {
        detail_df <- df[cluster_df$row_index, detail_cols, drop = FALSE]
      } else {
        detail_df <- data.frame(stringsAsFactors = FALSE)
      }
      detail_df$row_index <- cluster_df$row_index
      detail_df$cluster <- cluster_df$cluster
      detail_df <- detail_df[, c("cluster", "row_index", setdiff(names(detail_df), c("cluster", "row_index"))), drop = FALSE]
      safe_write_csv(detail_df, file.path(workflow_dir, "cluster_member_detail.csv")); record_method("cluster_member_detail", "cluster_member_detail.csv", TRUE, paste0("已生成聚类成员明细。", excluded_note))
    } else {
      failure_note <- paste0("聚类不适用：", conditionMessage(km), excluded_note)
      record_method("kmeans_clusters", "kmeans_clusters.csv", FALSE, failure_note)
      record_method("cluster_profile", "cluster_profile.csv", FALSE, failure_note)
      record_method("cluster_member_detail", "cluster_member_detail.csv", FALSE, failure_note)
    }
  } else {
    failure_note <- paste0("可用聚类特征不足。", excluded_note)
    record_method("kmeans_clusters", "kmeans_clusters.csv", FALSE, failure_note)
    record_method("cluster_profile", "cluster_profile.csv", FALSE, failure_note)
    record_method("cluster_member_detail", "cluster_member_detail.csv", FALSE, failure_note)
  }
} else {
  insufficiency_note <- paste0("完整数值样本不足或可用变化字段不足。", excluded_note)
  for (method in c("pca_variance","pca_loadings","pca_scores","pca_axis_summary","kmeans_clusters","cluster_profile","cluster_member_detail")) {
    output <- switch(method, pca_variance = "pca_variance.csv", pca_loadings = "pca_loadings.csv", pca_scores = "pca_scores.csv", pca_axis_summary = "pca_axis_summary.csv", kmeans_clusters = "kmeans_clusters.csv", cluster_profile = "cluster_profile.csv", cluster_member_detail = "cluster_member_detail.csv")
    record_method(method, output, FALSE, insufficiency_note)
  }
}'''
    analysis_template = re.sub(
        r'if \(length\(date_cols\) > 0 && length\(numeric_cols\) > 0\) \{.*?\n\}\n\nmissing_profile <- data.frame\(',
        lambda _m: temporal_block_replacement,
        analysis_template,
        count=1,
        flags=re.S,
    )
    analysis_template = re.sub(
        r'numeric_complete <- na\.omit\(df\[numeric_cols\]\)\n  if \(nrow\(numeric_complete\) >= 5\) \{.*?\n  \}(?=\n} else \{)',
        lambda _m: pca_cluster_block_replacement,
        analysis_template,
        count=1,
        flags=re.S,
    )
    analysis_template = re.sub(
        r'category_candidates <- char_cols\[!char_cols %in% date_cols\].*?\nif \(length\(date_cols\) > 0 && length\(numeric_cols\) > 0\) \{',
        lambda _m: category_block_replacement + "\n\nif (length(date_cols) > 0 && length(numeric_cols) > 0) {",
        analysis_template,
        count=1,
        flags=re.S,
    )
    analysis_template = re.sub(
        r'item_col <- NULL\nfor \(candidate in c\("item_id", "SKU", "sku", "Product", "product"\)\) \{\n  if \(candidate %in% names\(df\)\) \{ item_col <- candidate; break \}\n\}\n\nif \(!is.null\(item_col\) && length\(numeric_cols\) > 0\) \{.*?\n\} else \{\n  for \(method in c\("top_items","item_metric_summary","top_items_plot","item_daily_summary"\)\) \{\n    output <- switch\(method, top_items = "top_items.csv", item_metric_summary = "item_metric_summary.csv", top_items_plot = "top_items_plot.png", item_daily_summary = "item_daily_summary.csv"\)\n    record_method\(method, output, FALSE, "缺少对象字段或数值字段。"\)\n  \}\n\}',
        lambda _m: item_block_replacement,
        analysis_template,
        count=1,
        flags=re.S,
    )
    analysis_script = (
        analysis_template
        .replace("__TEMPORAL_VECTOR__", temporal_vector)
        .replace("__NUMERIC_VECTOR__", numeric_vector)
        .replace("__CATEGORY_VECTOR__", category_vector)
        .replace("__OBJECT_VECTOR__", object_vector)
        .replace("__VARIANCE_PAIR_VECTOR__", variance_pair_vector)
    )
    run_script = r'''
args <- commandArgs(trailingOnly = TRUE)
input_path <- args[1]
workflow_dir <- args[2]

source(file.path(workflow_dir, "01_clean_prepare.R"))
source(file.path(workflow_dir, "02_analysis_visualize.R"))
'''
    return {
        "mode": "fallback",
        "reason": reason,
        "overview": "已按当前数据结构生成一套更完整的 R 清洗、统计、分群、趋势、漏斗与可视化工作流。",
        "clean_script": clean_script,
        "analysis_script": analysis_script,
        "run_script": run_script,
        "expected_outputs": [
            "cleaned_dataset.csv",
            "summary_stats.csv",
            "quantile_profile.csv",
            "anomaly_summary.csv",
            "zero_ratio_summary.csv",
            "coefficient_variation.csv",
            "skew_kurtosis_summary.csv",
            "missing_profile.csv",
            "duplicate_profile.csv",
            "correlation_matrix.csv",
            "correlation_pairs.csv",
            "covariance_matrix.csv",
            "pca_variance.csv",
            "pca_loadings.csv",
            "pca_scores.csv",
            "pca_axis_summary.csv",
            "kmeans_clusters.csv",
            "cluster_profile.csv",
            "cluster_member_detail.csv",
            "top_categories.csv",
            "category_share_summary.csv",
            "category_metric_summary.csv",
            "category_price_band_summary.csv",
            "temporal_trend.csv",
            "temporal_growth.csv",
            "temporal_moving_average.csv",
            "temporal_period_profile.csv",
            "funnel_metrics.csv",
            "funnel_conversion_summary.csv",
            "top_items.csv",
            "item_metric_summary.csv",
            "item_daily_summary.csv",
            "outlier_records.csv",
            "numeric_distribution.png",
            "numeric_boxplot.png",
            "numeric_density.png",
            "correlation_heatmap.png",
            "numeric_scatter_plot.png",
            "category_mix.png",
            "category_metric_plot.png",
            "category_pareto.png",
            "temporal_trend.png",
            "temporal_growth.png",
            "temporal_period_plot.png",
            "funnel_overview.png",
            "top_items_plot.png",
            "method_log.csv",
        ],
    }


def _analysis_script_has_rootfixed_pca_cluster_flow(script_text: str) -> bool:
    text = str(script_text or "")
    if not text.strip():
        return False
    lower = text.lower()
    if "prcomp(" not in lower and "kmeans(" not in lower:
        return True
    required_markers = [
        "pca_candidate_cols",
        "cluster_feature_pool",
        "pca_axis_summary.csv",
        "cluster_member_detail.csv",
        "row_index",
    ]
    return all(marker in text for marker in required_markers)


def _coerce_r_workflow_agent_layer_to_safe_template(
    layer: dict[str, Any],
    r_context: dict[str, Any],
) -> dict[str, Any]:
    if _analysis_script_has_rootfixed_pca_cluster_flow(layer.get("analysis_script") or ""):
        return layer

    safe_layer = _fallback_r_workflow_author_v2("validated_safe_fallback_after_r_workflow_review", r_context)
    safe_layer["mode"] = "validated_safe_fallback"
    safe_layer["runtime_state"] = "local"
    safe_layer["degradation_state"] = "validated_safe_fallback"
    safe_layer["fallback_reason"] = "unsafe_or_incomplete_pca_cluster_script"
    safe_layer["live_available"] = bool(layer.get("live_available"))
    for key in ("model", "provider_label", "reasoning_effort"):
        if key in layer:
            safe_layer[key] = layer[key]
    return safe_layer


def codex_generate_r_workflow(r_context: dict[str, Any]) -> dict[str, Any]:
    system_prompt = (
        "You are Codex acting as an R workflow authoring agent. "
        "You must answer in Simplified Chinese and JSON only. "
        "You will receive dataset schema, temporal columns, business request, report lens, and a column_role_registry that already separates suitable numeric fields, category dimensions, object fields, and excluded fields. "
        "Return keys: overview, clean_script, analysis_script, run_script, expected_outputs. "
        "Your job is to write runnable R code from cleaning to analysis and visualization. "
        "Prefer base R so the workflow stays portable. "
        "Do not leave placeholders like TODO. "
        "Do not stop at only 3 or 4 simple methods. "
        "By default, aim to cover multiple method families when the data supports them: summary statistics, quantiles, anomalies/outliers, correlation, category structure, grouped summaries, missingness, duplicates, time trend, and at least 2 charts. "
        "Before writing code, honor the provided column suitability judgment. "
        "Numeric methods such as mean, median, quantile, anomaly, CV, skewness, kurtosis, correlation, covariance, PCA, clustering, grouped mean, and temporal aggregation must cover all suitable numeric fields when the output format allows it, not only the first metric. "
        "Never compute mean, quantile, correlation, covariance, PCA, clustering, or numeric trend on identifier columns, name/title/text columns, or temporal columns themselves. "
        "Before PCA or clustering, always remove constant or zero-variance numeric columns first. "
        "For clustering, first filter all complete-case numeric columns for usable variance, then choose the first few survivors; do not truncate first and filter later. "
        "When you output clustering results, preserve the original row index and also emit a cluster_member_detail.csv table that includes cluster, row_index, member identifiers when available, and the clustering metrics used for grouping. "
        "When you output PCA results, also emit a pca_axis_summary.csv table that names each leading axis using its dominant positive and negative drivers. "
        "Category methods should cover multiple suitable category dimensions when the data supports them. "
        "Object-level summaries should cover multiple suitable numeric metrics when the data supports them. "
        "If the dataset looks like management accounting, finance, budgeting, or business review data, add management-accounting-specific outputs such as budget_vs_actual grouped summaries and profitability/cash-flow oriented grouped views. "
        "If funnel-style columns or item/category columns exist, add funnel or top-object methods too. "
        "The method_log should look materially richer than a minimal demo."
    )
    tool_specs = [
        {
            "name": "lookup_r_workflow_context",
            "description": "Read selected schema and request fields before writing the R workflow.",
            "parameters": {
                "type": "object",
                "properties": {"fields": {"type": "array", "items": {"type": "string"}}},
                "required": ["fields"],
                "additionalProperties": False,
            },
            "handler": lambda args: {
                key: r_context.get(key)
                for key in [str(item) for item in args.get("fields", [])[:14]]
            },
        }
    ]
    result = _request_codex_agentic_json(
        system_prompt=system_prompt,
        user_payload=r_context,
        tool_specs=tool_specs,
        fallback_builder=_fallback_r_workflow_author_v2,
    )
    return _coerce_r_workflow_agent_layer_to_safe_template(result, r_context)


def _fallback_r_results_interpretation(reason: str, payload: dict[str, Any]) -> dict[str, Any]:
    summary_rows = payload.get("summary_rows") or []
    category_rows = payload.get("category_rows") or []
    temporal_rows = payload.get("temporal_rows") or []
    method_rows = payload.get("method_rows") or []
    correlation_rows = payload.get("correlation_rows") or []
    pca_axis_rows = payload.get("pca_axis_rows") or []
    cluster_member_rows = payload.get("cluster_member_rows") or []
    bullets: list[str] = []
    key_metric_readings: list[str] = []
    structure_readings: list[str] = []
    trend_readings: list[str] = []
    relation_readings: list[str] = []
    action_recommendations: list[str] = []
    risk_alerts: list[str] = []
    if pca_axis_rows:
        first_axis = pca_axis_rows[0]
        axis_name = first_axis.get("component", "PC1")
        axis_summary = first_axis.get("axis_summary", "主轴")
        explained = first_axis.get("variance_explained", "n/a")
        bullets.append(f"PCA 已经把变化压成 `{axis_name}` 等主轴，可以把统计主轴直接接进业务解读。")
        relation_readings.append(f"`{axis_name}` 当前更像 `{axis_summary}`，解释 {explained} 的变化，说明这不只是数学结果，而是可以对应到业务结构的主观察轴。")
        action_recommendations.append("把 `pca_axis_summary` 接进主报告，用“主轴”而不是 PC1/PC2 数学代号去讲业务。")
    if cluster_member_rows:
        sample_member = cluster_member_rows[0]
        sample_cluster = sample_member.get("cluster", "n/a")
        sample_identifier = next(
            (
                sample_member.get(key)
                for key in ["Product", "product", "SKU", "sku", "OrderID", "item_id", "row_index"]
                if sample_member.get(key)
            ),
            "n/a",
        )
        structure_readings.append(f"聚类不再只是簇均值画像，现在已经能下钻到成员明细。例如 cluster `{sample_cluster}` 里的样本 `{sample_identifier}`，可直接用于业务复核。")
        action_recommendations.append("围绕 `cluster_member_detail` 把主流群、次级特征群和异常群各自抽样复核，否则聚类仍然只是统计结果。")
    if summary_rows:
        top_metric = summary_rows[0]
        metric_name = top_metric.get("column", "n/a")
        mean_value = top_metric.get("mean", "n/a")
        median_value = top_metric.get("median", "n/a")
        bullets.append(f"核心数值指标首先落在 `{metric_name}`，说明 R 工作流已经能稳定完成基础数值画像。")
        key_metric_readings.append(f"`{metric_name}` 当前均值 {mean_value}、中位数 {median_value}，后续要区分是常态贡献，还是被少数大值记录拉动。")
    if category_rows:
        top_category = category_rows[0]
        top_name = top_category.get("category", "n/a")
        top_count = top_category.get("count", "n/a")
        bullets.append(f"类别结构头部是 `{top_name}`，后续复盘应优先围绕这一头部切片继续拆解。")
        structure_readings.append(f"头部类别 `{top_name}` 当前数量 {top_count}，说明这部分对象承担了主要结构权重，后续要确认它带来的是健康增长还是单点挤压。")
    if temporal_rows:
        first_period = temporal_rows[0].get("period", "n/a")
        last_period = temporal_rows[-1].get("period", "n/a")
        bullets.append(f"时间趋势样本从 `{first_period}` 延续到 `{last_period}`，说明已经有节奏线索可读。")
        if len(temporal_rows) >= 2:
            trend_readings.append(
                f"最近时间窗 `{last_period}` 相比上一窗 `{temporal_rows[-2].get('period', 'n/a')}` 的变化，需要和活动节奏、供给变化或自然波动放在一起解释。"
            )
    if method_rows:
        completed = [row.get("method") for row in method_rows if str(row.get("status", "")).lower() in {"true", "1"}]
        if completed:
            bullets.append(f"当前 R 实跑已完成的方法包括：{'、'.join(str(item) for item in completed[:6])}。")
            action_recommendations.append(f"优先把 `{'、'.join(str(item) for item in completed[:3])}` 这几类结果接进业务判断，而不是只把它们当附录。")
    if correlation_rows:
        relation_readings.append("相关矩阵已经显示关键指标存在联动，后续要区分这些指标是在重复描述同一结果，还是分别代表流量、转化和成交。")
        risk_alerts.append("如果高相关指标被反复当成独立结论，报告会显得很满，但实质是在重复同一条业务事实。")
    if summary_rows:
        action_recommendations.append("把数值摘要里的头部指标拉进经营主线，明确它影响的是销量、客单、利润还是效率。")
    if category_rows:
        action_recommendations.append("围绕头部类别继续拆对象明细，确认结构头部是否真的带来经营质量提升。")
    if temporal_rows:
        action_recommendations.append("把趋势波动和业务节奏对齐，确认高点和低点到底来自活动、供给还是自然波动。")
    if not bullets:
        bullets.append("当前 R 工作流已经完成数据抽取，但还需要更完整的输出文件才能形成更强业务解读。")
    if not key_metric_readings:
        key_metric_readings.append("当前样本还缺少足够稳定的数值结果，先把核心指标口径补全，再展开经营解释。")
    if not structure_readings:
        structure_readings.append("当前结构切片还不够稳定，先确认主分类字段，再判断头部和长尾。")
    if not trend_readings:
        trend_readings.append("当前时间趋势信息还偏弱，后续应优先补时间窗和节奏解释。")
    if not relation_readings:
        relation_readings.append("当前指标关系仍需结合相关矩阵或交叉表继续确认，避免把并列表格误当成业务联动。")
    if not action_recommendations:
        action_recommendations.append("先把已有 R 输出压成业务结论，再决定哪些结果需要回写主报告。")
    if not risk_alerts:
        risk_alerts.append("当前 R 输出更适合做结构复核和趋势验证，不能脱离业务背景直接下因果结论。")
    return {
        "mode": "fallback",
        "reason": reason,
        "headline": "已结合 R 工作流输出形成一份业务解读，不把 R 结果直接塞回主大表。",
        "interpretation_summary": bullets[:6],
        "business_markdown": "\n".join(f"- {item}" for item in bullets[:6]),
        "key_metric_readings": key_metric_readings[:4],
        "structure_readings": structure_readings[:4],
        "trend_readings": trend_readings[:4],
        "relation_readings": relation_readings[:4],
        "action_recommendations": action_recommendations[:5],
        "risk_alerts": risk_alerts[:4],
    }


def codex_interpret_r_results(interpret_context: dict[str, Any]) -> dict[str, Any]:
    system_prompt = (
        "You are Codex acting as an R results interpretation agent. "
        "You must answer in Simplified Chinese and JSON only. "
        "You will receive structured outputs from an R workflow. "
        "Return keys: headline, interpretation_summary, business_markdown, key_metric_readings, structure_readings, trend_readings, relation_readings, action_recommendations, risk_alerts. "
        "Your job is to translate R outputs into business-readable conclusions without copying raw tables. "
        "Do not only summarize methods; explain what the output means for the business and what to do next. "
        "When pca_axis_rows are available, explicitly explain what the leading axes mean in business terms instead of repeating PC1/PC2 labels. "
        "When cluster_member_rows are available, explicitly mention that clustering can now be verified down to concrete members instead of only cluster averages."
    )
    tool_specs = [
        {
            "name": "lookup_r_results_context",
            "description": "Read selected R output rows before interpreting them.",
            "parameters": {
                "type": "object",
                "properties": {"fields": {"type": "array", "items": {"type": "string"}}},
                "required": ["fields"],
                "additionalProperties": False,
            },
            "handler": lambda args: {
                key: interpret_context.get(key)
                for key in [str(item) for item in args.get("fields", [])[:14]]
            },
        }
    ]
    return _request_codex_agentic_json(
        system_prompt=system_prompt,
        user_payload=interpret_context,
        tool_specs=tool_specs,
        fallback_builder=_fallback_r_results_interpretation,
    )


def build_r_artifact_intelligence_system_prompt() -> str:
    return (
        "You are Codex acting as a standalone R artifact intelligence agent. "
        "You must answer in Simplified Chinese and JSON only. "
        "This is a new flow bound to the R workflow only. "
        "You will receive two primary source files mounted into Code Interpreter: "
        "1) the R workflow Excel master workbook, "
        "2) the R workflow interpretation PDF. "
        "You must use the code interpreter tool to inspect those files directly instead of relying on pre-digested local summaries. "
        "Do not treat this as the main report flow, and do not borrow conclusions from any non-R workflow artifacts. "
        "Your primary job is not to explain statistics mechanically, but to convert the R artifact bundle into a business-facing management interpretation. "
        "Return keys: headline, executive_summary, artifact_usage, sheet_findings, cross_artifact_findings, evidence_boundaries, action_recommendations, markdown. "
        "sheet_findings must be a list of objects with keys: sheet_name, finding, why_it_matters, evidence. "
        "artifact_usage must explain which workbook sheets and which PDF passages were actually inspected inside Code Interpreter. "
        "cross_artifact_findings must synthesize across workbook and PDF instead of repeating sheet names. "
        "evidence_boundaries must clearly state where evidence is direct, grouped, proxy-like, sparse, or absent. "
        "action_recommendations must be operational and tied to the R evidence, not generic advice. "
        "Your detailed reasoning rules are: "
        "1) prioritize workbook sheet evidence over narrative wording when they conflict; "
        "2) never infer business meaning from a column name alone without support from sheet rows or PDF text; "
        "3) distinguish observed facts, grouped statistical patterns, and interpretation hypotheses; "
        "4) when the workbook shows layered metrics by dimension, explicitly say which dimension and which metric are driving the finding; "
        "5) if the PDF only summarizes a subset of workbook evidence, call that out instead of pretending the PDF is exhaustive; "
        "6) if some sheets are empty, sparse, or failed, explain what cannot be concluded; "
        "7) do not restate every method mechanically, focus on business interpretation grounded in the artifact bundle; "
        "8) write markdown that can be rendered as a standalone R-language intelligent interpretation note; "
        "9) if the PDF says something that the workbook does not support, call it out explicitly; "
        "10) do not skip file inspection; "
        "11) start from business object, management question, and decision impact before talking about methods; "
        "12) every executive_summary bullet should ideally contain a business object or dimension, a metric signal, and a management meaning; "
        "13) if the data looks like ecommerce, media, finance, operations, procurement, or project management, translate findings into that business language rather than generic statistical language; "
        "14) avoid long lectures about data quality unless those issues materially change business decisions; "
        "15) the markdown should use clear Chinese business headings such as '这是什么业务盘子', '最重要的经营发现', '哪些分层值得管', '哪些结论不能下', '下一步动作'."
    )


def build_r_artifact_summary_intelligence_system_prompt() -> str:
    return (
        "You are Codex acting as a standalone R artifact intelligence agent in summary-pack mode. "
        "You must answer in Simplified Chinese and JSON only. "
        "The upstream provider could not mount raw files directly, so you are given a business-oriented extraction pack built from the R workbook and R PDF. "
        "Your job is still to produce a business-facing management interpretation, not a method recap. "
        "Return keys: headline, executive_summary, artifact_usage, sheet_findings, cross_artifact_findings, evidence_boundaries, action_recommendations, markdown. "
        "Treat the provided workbook extractions and PDF excerpts as primary evidence. "
        "Prioritize business object, management question, and decision impact before statistical method naming. "
        "Every executive_summary bullet should ideally contain a business object or dimension, a metric signal, and a management meaning. "
        "When grouped sheets exist, explicitly name the dimension and the metric driving the finding. "
        "If evidence is only descriptive and does not support causal or strategic conclusions, say so clearly. "
        "Avoid generic statistical prose. Explain what the business should pay attention to, what cannot yet be concluded, and what action should follow."
    )


def _fallback_r_workflow_semantic_understanding(reason: str, payload: dict[str, Any]) -> dict[str, Any]:
    heuristic = payload.get("heuristic_registry") or {}
    return {
        "numeric_method_columns": list(heuristic.get("numeric_method_columns") or []),
        "category_dimension_columns": list(heuristic.get("category_dimension_columns") or []),
        "object_dimension_columns": list(heuristic.get("object_dimension_columns") or []),
        "temporal_columns": list(heuristic.get("temporal_columns") or []),
        "variance_pairs": list(heuristic.get("variance_pairs") or []),
        "why": f"fallback_semantic_understanding: {reason}",
    }


def codex_infer_r_workflow_semantics(semantic_context: dict[str, Any]) -> dict[str, Any]:
    system_prompt = (
        "You are Codex acting as an R workflow semantic understanding agent. "
        "You must answer in Simplified Chinese and JSON only. "
        "Your job is to decide which columns should be treated as numeric metrics, category dimensions, object dimensions, temporal dimensions, and which baseline-vs-actual pairs should be compared in management-style analysis. "
        "Do not rely on exact hardcoded field names. Use semantic understanding from headers, sample rows, file context, and business request. "
        "Return keys: numeric_method_columns, category_dimension_columns, object_dimension_columns, temporal_columns, variance_pairs, why. "
        "variance_pairs must be a list of objects with keys: baseline_column, actual_column, family, reason. "
        "Only return columns that exist in the provided schema. "
        "Only create variance_pairs when the semantic meaning is strong enough. "
        "If the sheet looks like management accounting, budgeting, finance, or business review data, actively look for budget/plan/target vs actual/realized pairs across revenue, cost, profit, cashflow, inventory, receivable, payable, asset, liability, or equity families. "
        "If the sheet is not that type of data, return an empty variance_pairs list."
    )
    return _request_codex_json(
        system_prompt=system_prompt,
        user_payload=semantic_context,
        fallback_builder=_fallback_r_workflow_semantic_understanding,
        reasoning_effort_override="medium",
        timeout_seconds=180,
        store=False,
    )


def _fallback_r_artifact_bundle_interpretation(reason: str, payload: dict[str, Any]) -> dict[str, Any]:
    workbook_name = str(payload.get("workbook_name") or "r-statistics-summary.xlsx")
    sheet_summaries = payload.get("workbook_sheet_summaries") or []
    pdf_excerpt = str(payload.get("pdf_excerpt") or "").strip()
    focus_question = str(payload.get("focus_question") or "").strip()

    executive_summary: list[str] = []
    artifact_usage: list[str] = []
    sheet_findings: list[dict[str, str]] = []
    cross_artifact_findings: list[str] = []
    evidence_boundaries: list[str] = []
    action_recommendations: list[str] = []

    if sheet_summaries:
        executive_summary.append(f"本次解读已读取 `{workbook_name}` 的 {len(sheet_summaries)} 张工作表，不只依赖单一摘要页。")
        artifact_usage.append(f"主证据来自 Excel 总表 `{workbook_name}`，已读取工作表索引和各 sheet 样例行。")
        for item in sheet_summaries[:6]:
            sheet_name = str(item.get("sheet_name") or "unknown")
            row_count = item.get("row_count", 0)
            columns = item.get("columns") or []
            sample_rows = item.get("sample_rows") or []
            first_row = sample_rows[0] if sample_rows else {}
            evidence = "；".join(f"{key}={value}" for key, value in list(first_row.items())[:4]) if first_row else "该表暂无样例行"
            sheet_findings.append(
                {
                    "sheet_name": sheet_name,
                    "finding": f"`{sheet_name}` 当前可见 {row_count} 行，说明这张表已进入 R 工作流统计产物。",
                    "why_it_matters": f"这张表覆盖字段 {', '.join(str(col) for col in columns[:6])}，可用于补充业务判断。",
                    "evidence": evidence,
                }
            )
        cross_artifact_findings.append("Excel 总表已经把分层统计结果按 sheet 归档，适合做二次业务归纳，而不是只看单页 PDF 摘要。")
        action_recommendations.append("优先从 summary_stats、category_metric_summary、temporal_trend 这几类 sheet 提炼经营主线，再回看 PDF 是否遗漏层次。")
    else:
        executive_summary.append("当前没有读取到有效的 Excel sheet 样例，因此无法形成充分的表级证据。")
        evidence_boundaries.append("Excel 总表缺少可读 sheet 样例，结论可信度受限。")

    if pdf_excerpt:
        artifact_usage.append("同时读取了 R 工作流 PDF 的文本摘录，用于核对 R 叙述层是否覆盖了 workbook 里的统计结果。")
        cross_artifact_findings.append("PDF 更适合作为叙述层校对，而 workbook 更适合作为统计证据主源。")
    else:
        evidence_boundaries.append("PDF 文本摘录为空或不足，无法确认叙述层是否完整覆盖统计表。")

    if focus_question:
        action_recommendations.insert(0, f"本次解读应优先围绕 `{focus_question}` 回答，而不是平均铺陈所有统计方法。")

    evidence_boundaries.append("本 fallback 结果只证明新流链路可用，不替代 live Codex 的深度归纳。")

    markdown_lines = [
        "# R 语言及智能解读",
        "",
        f"- fallback_reason: {reason}",
        *[f"- {item}" for item in executive_summary],
        "",
        "## Artifact Usage",
        "",
        *[f"- {item}" for item in artifact_usage],
        "",
        "## Sheet Findings",
        "",
    ]
    for finding in sheet_findings:
        markdown_lines.extend(
            [
                f"### {finding['sheet_name']}",
                "",
                f"- 发现：{finding['finding']}",
                f"- 业务意义：{finding['why_it_matters']}",
                f"- 证据：{finding['evidence']}",
                "",
            ]
        )
    markdown_lines.extend(
        [
            "## Cross Artifact Findings",
            "",
            *[f"- {item}" for item in cross_artifact_findings],
            "",
            "## Evidence Boundaries",
            "",
            *[f"- {item}" for item in evidence_boundaries],
            "",
            "## Action Recommendations",
            "",
            *[f"- {item}" for item in action_recommendations],
            "",
        ]
    )

    return {
        "headline": "已基于 R 工作流 Excel 总表与 PDF 形成独立智能解读草稿。",
        "executive_summary": executive_summary[:6],
        "artifact_usage": artifact_usage[:6],
        "sheet_findings": sheet_findings[:8],
        "cross_artifact_findings": cross_artifact_findings[:6],
        "evidence_boundaries": evidence_boundaries[:6],
        "action_recommendations": action_recommendations[:6],
        "markdown": "\n".join(markdown_lines),
    }


def codex_interpret_r_artifact_bundle(interpret_context: dict[str, Any]) -> dict[str, Any]:
    system_prompt = build_r_artifact_intelligence_system_prompt()
    return _request_codex_json(
        system_prompt=system_prompt,
        user_payload=interpret_context,
        fallback_builder=_fallback_r_artifact_bundle_interpretation,
        reasoning_effort_override="medium",
        timeout_seconds=240,
        store=False,
    )


def codex_interpret_r_artifact_bundle_from_files(
    interpret_context: dict[str, Any],
    *,
    workbook_path: Path,
    pdf_path: Path,
) -> dict[str, Any]:
    settings = load_runtime_settings_raw()
    api_key = settings.get("api_key", "")
    model = settings.get("model", "gpt-5.4")
    provider_label = settings.get("provider_label", "OpenAI Codex API")
    if not api_key:
        raise RuntimeError("R 智能解读新流要求 live Codex，但当前缺少 API Key。")

    uploaded_workbook = _upload_file_to_openai(workbook_path, settings, purpose="user_data")
    uploaded_pdf = _upload_file_to_openai(pdf_path, settings, purpose="user_data")
    file_ids = [str(uploaded_workbook.get("id") or ""), str(uploaded_pdf.get("id") or "")]
    system_prompt = build_r_artifact_intelligence_system_prompt()
    body = {
        "model": model,
        "instructions": system_prompt,
        "input": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": json.dumps(
                            {
                                **interpret_context,
                                "artifact_contract": {
                                    "workbook_file_name": workbook_path.name,
                                    "pdf_file_name": pdf_path.name,
                                    "instruction": "Use code interpreter to inspect both uploaded files directly, then return JSON only.",
                                },
                            },
                            ensure_ascii=False,
                            indent=2,
                            default=_json_default,
                        ),
                    }
                ],
            }
        ],
        "tools": [
            {
                "type": "code_interpreter",
                "container": {
                    "type": "auto",
                    "memory_limit": "4g",
                    "file_ids": file_ids,
                },
            }
        ],
        "tool_choice": "required",
        "reasoning": {"effort": "medium"},
        "store": False,
    }

    last_exc: Exception | None = None
    for attempt in range(4):
        try:
            payload = _responses_request(body, settings, timeout_seconds=600)
            text = _extract_text(payload)
            parsed = _extract_json_from_text(text)
            parsed["mode"] = "live_codex_code_interpreter"
            parsed["model"] = model
            parsed["provider_label"] = provider_label
            parsed["reasoning_effort"] = "medium"
            parsed["runtime_state"] = "live"
            parsed["degradation_state"] = "none"
            parsed["live_available"] = True
            parsed["uploaded_files"] = [
                {"name": workbook_path.name, "file_id": file_ids[0]},
                {"name": pdf_path.name, "file_id": file_ids[1]},
            ]
            return parsed
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, json.JSONDecodeError, KeyError, requests.RequestException) as exc:
            last_exc = exc
            if attempt < 3 and _is_retryable_codex_error(exc):
                time.sleep(min(20.0, 3.0 * (attempt + 1)))
                continue
            break
    raise RuntimeError(f"R 智能解读文件直送 Codex 失败：{last_exc}")


def codex_interpret_r_artifact_bundle_from_summary(
    interpret_context: dict[str, Any],
) -> dict[str, Any]:
    return _request_codex_json(
        system_prompt=build_r_artifact_summary_intelligence_system_prompt(),
        user_payload=interpret_context,
        fallback_builder=_fallback_r_artifact_bundle_interpretation,
        reasoning_effort_override="medium",
        timeout_seconds=240,
        store=False,
    )


def _fallback_management_accounting_review(reason: str, payload: dict[str, Any]) -> dict[str, Any]:
    cards = payload.get("knowledge_cards") or []
    totals = payload.get("totals_rows") or []
    margin_rows = payload.get("margin_rows") or []
    budget_rows = payload.get("budget_rows") or []
    working_capital_rows = payload.get("working_capital_rows") or []
    leverage_rows = payload.get("leverage_rows") or []
    slice_rows = payload.get("slice_rows") or []
    product_rows = payload.get("product_rows") or []
    sku_rows = payload.get("sku_rows") or []
    category_rows = payload.get("category_rows") or []
    fusion_enabled = _is_procurement_sales_management_fusion_payload(payload)

    metric_interpretations: list[str] = []
    if margin_rows:
        metric_interpretations.append(f"{margin_rows[0]['指标']} 是当前最适合先看的盈利质量口径，用来区分收入增长和利润质量。")
    if budget_rows:
        metric_interpretations.append(f"{budget_rows[0]['预算主题']} 的预算偏差最大，应优先拆解价格、销量、效率或投放节奏的影响。")
    if working_capital_rows:
        metric_interpretations.append("营运资本相关字段已经足以支撑现金占压复盘，经营结论需要同时看利润和资金占用。")
    if leverage_rows:
        metric_interpretations.append(f"{leverage_rows[0]['指标']} 可以直接进入偿债压力与财务韧性判断。")

    key_findings = [str(item) for item in payload.get("summary_bullets", [])[:4]]
    if not key_findings and totals:
        key_findings.append("当前样本已具备管理会计复盘条件，至少可以从规模、利润、预算偏差和资金占用四条线展开。")
    if slice_rows:
        key_findings.append(f"经营切片中 `{slice_rows[0]['经营切片']}` 当前承担了更大的经营盘子，应优先进入第一轮责任归属与支出集中度排查。")
    if fusion_enabled:
        top_business_row = (product_rows or sku_rows or category_rows or [None])[0]
        if top_business_row:
            key_findings.append(
                f"`{top_business_row.get('对象', '头部对象')}` 当前销售额 {top_business_row.get('销售额总量', 'n/a')}、订单覆盖 {top_business_row.get('订单覆盖', 'n/a')}、客户覆盖 {top_business_row.get('客户覆盖', 'n/a')}，说明采购/预算投入已经能和销售承接放到同一条链上复盘。"
            )
            return_rate = str(top_business_row.get("退货率", "n/a")).strip()
            if return_rate not in {"", "n/a", "0", "0.0", "0%", "0.0%"}:
                metric_interpretations.append(
                    f"`{top_business_row.get('对象', '头部对象')}` 当前退货率 {return_rate}，因此采销判断不能只看卖得多，还要看逆向交易和库存回压。"
                )

    risk_flags: list[str] = []
    if budget_rows:
        risk_flags.append("预算偏差需要先区分结构性偏差和执行性偏差，不能直接把偏差额写成团队优劣。")
    if working_capital_rows:
        risk_flags.append("当前数据已显示资金占用线索，不能只看利润表结论忽略现金转换。")
    if leverage_rows:
        risk_flags.append("杠杆指标只能说明压力水平，不能脱离债务结构和偿付节奏下结论。")
    if not risk_flags:
        risk_flags.append("当前为规则兜底的管理会计分析，强结论仍需结合完整财务口径复核。")

    managerial_actions = []
    if budget_rows:
        top_budget = budget_rows[0]
        managerial_actions.append(f"优先排查 `{top_budget['预算主题']}` 的预算偏差，并区分是预算编制问题还是执行偏差问题。")
    if slice_rows:
        managerial_actions.append(f"先围绕 `{slice_rows[0]['经营切片']}` 做支出集中度和责任归属复盘，再决定是否扩大到其他对象。")
    if fusion_enabled:
        top_business_row = (product_rows or sku_rows or category_rows or [None])[0]
        if top_business_row:
            managerial_actions.append(
                f"把 `{top_business_row.get('对象', '头部对象')}` 拉进采销联动清单，和责任主体、预算主题、库存/退货风险放在一张表里看，判断投入有没有真正转成订单与客户覆盖。"
            )
    if not managerial_actions:
        managerial_actions.extend(
            [
                "先按支出集中度、异常金额和时间波动三条线组织正文，而不是只堆财务字段。",
                "把金额最高、波动最大和责任归属不清的对象列为第一轮复盘清单。",
                "在缺乏完整现金流或资产负债细项时，只保留可执行的排查和复核动作。",
            ]
        )
    if cards:
        managerial_actions.append(f"当前知识库最匹配的管理会计镜头包括：{'、'.join(card['title'] for card in cards[:3])}。")

    management_summary = key_findings[0] if key_findings else "当前支出或预算对象里已经出现可优先排查的头部对象，应先落到责任归属和异常金额复盘。"
    management_summary = f"这份数据更适合按管理会计口径来读：{management_summary}"
    if fusion_enabled and (product_rows or sku_rows):
        top_business_row = (product_rows or sku_rows)[0]
        management_summary = (
            f"这份数据更适合按管理会计与采销一体融合口径来读：`{top_business_row.get('对象', '头部对象')}` 当前销售额 {top_business_row.get('销售额总量', 'n/a')}，需要和预算、责任主体、库存与退货风险一起判断。"
        )

    return {
        "mode": "fallback",
        "reason": reason,
        "management_summary": management_summary,
        "key_findings": key_findings[:5],
        "metric_interpretations": metric_interpretations[:5],
        "risk_flags": risk_flags[:5],
        "managerial_actions": managerial_actions[:5],
        "recommended_sections": [
            *(
                ["采销一体联动洞察", "商品/SKU经营承接复盘"]
                if fusion_enabled
                else []
            ),
            "经营结果与利润质量",
            "预算执行与偏差归因",
            "营运资本与现金压力",
            "责任中心与成本结构",
        ][:5],
    }


def codex_management_accounting_review(accounting_context: dict[str, Any]) -> dict[str, Any]:
    system_prompt = (
        "You are Codex acting as a senior management accounting review agent. "
        "You must answer in Simplified Chinese and return JSON only. "
        "You will receive detected financial columns, summary metrics, budget variance rows, working-capital rows, leverage rows, slice rows, optionally product/SKU/category rows, and matched knowledge cards from official accounting frameworks. "
        "Your job is to turn them into management-accounting guidance, not generic statistical commentary. "
        "Return keys: management_summary, key_findings, metric_interpretations, risk_flags, managerial_actions, recommended_sections. "
        "All list fields must contain 3 to 5 concise Chinese strings. "
        "Explain business meaning and management impact, especially around profit quality, budget variance, working capital, leverage, responsibility-center structure, and when commercial rows exist, whether procurement投入真正转成销售承接。 "
        "Do not invent unsupported facts. If a metric is missing, say what cannot yet be judged instead of pretending it exists."
    )
    tool_specs = [
        {
            "name": "lookup_accounting_context",
            "description": "Read selected totals, margins, budget rows, capital rows, leverage rows, and business context before writing the management accounting review.",
            "parameters": {
                "type": "object",
                "properties": {
                    "fields": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["fields"],
                "additionalProperties": False,
            },
            "handler": lambda args: {
                key: accounting_context.get(key)
                for key in [str(item) for item in args.get("fields", [])[:12]]
            },
        }
    ]
    return _request_codex_agentic_json(
        system_prompt=system_prompt,
        user_payload=accounting_context,
        tool_specs=tool_specs,
        fallback_builder=_fallback_management_accounting_review,
    )


def _legacy_fallback_internet_ops_review_stage1(reason: str, payload: dict[str, Any]) -> dict[str, Any]:
    topline_rows = payload.get("topline_rows") or []
    channel_rows = payload.get("channel_rows") or []
    activity_rows = payload.get("activity_rows") or []
    content_rows = payload.get("content_rows") or []
    method_findings = payload.get("method_findings") or []

    key_findings: list[str] = []
    if topline_rows:
        metrics = {str(row.get("核心指标") or row.get("metric") or ""): row for row in topline_rows}
        active_row = metrics.get("活跃用户总量") or next(iter(metrics.values()))
        if active_row:
            key_findings.append(
                f"当前运营盘子先看 `{active_row.get('核心指标', '核心指标')}`，总量 {active_row.get('总量', 'n/a')}，均值 {active_row.get('均值', 'n/a')}，说明当前先要判断规模，再判断效率。"
            )
    if channel_rows:
        top_channel = channel_rows[0]
        key_findings.append(
            f"渠道层当前最值得先看的对象是 `{top_channel.get('渠道', '头部渠道')}`，活跃占比 {top_channel.get('活跃占比', 'n/a')}，后续要继续看它的留存率和转化率是否同步领先。"
        )
    if activity_rows:
        top_activity = activity_rows[0]
        key_findings.append(
            f"活动层当前应优先复盘 `{top_activity.get('活动', '头部活动')}`，因为它同时承担了活跃规模和结果承接的第一层判断。"
        )
    if content_rows:
        top_content = content_rows[0]
        key_findings.append(
            f"内容层当前最值得继续观察的是 `{top_content.get('内容主题', '重点内容主题')}`，它更适合进入下一轮内容复盘和验证。"
        )

    metric_interpretations: list[str] = []
    if topline_rows:
        for row in topline_rows[:3]:
            metric_interpretations.append(
                f"{row.get('核心指标', '核心指标')} 当前要结合总量、均值和中位数一起看，判断它是稳定盘子还是被少数峰值拉动。"
            )
    if method_findings:
        metric_interpretations.append(
            f"当前已实跑的重点方法包括：{'、'.join(str(item.get('method')) for item in method_findings[:3])}，这些结果应直接进入运营动作解释，而不是停留在方法列表。"
        )

    risk_flags: list[str] = []
    if channel_rows:
        risk_flags.append("渠道份额高不等于值得加投，后续必须继续结合留存率、转化率和异常率一起判断。")
    if activity_rows:
        risk_flags.append("活动冲高不等于稳定增长，后续必须继续确认高表现是否由单次峰值或短窗拉动。")
    if not risk_flags:
        risk_flags.append("如果业务口径、时间窗口或分母不稳，运营结论只能先保留在观察层。")

    managerial_actions = [
        "先把渠道、活动、内容三层的头部对象拆成单独复盘清单，不要继续只看整体均值。",
        "把留存率、转化率、订单承接和异常率绑在一起看，再决定是扩量、维持还是修复。",
        "把当前最头部渠道和活动拉入下一轮验证议程，确认它们是稳定承接还是单次高峰。",
    ]
    if channel_rows:
        managerial_actions[0] = f"先围绕 `{channel_rows[0].get('渠道', '头部渠道')}` 做渠道深挖，再比较次头部渠道的留存与转化差。"
    if activity_rows:
        managerial_actions[1] = f"围绕 `{activity_rows[0].get('活动', '头部活动')}` 做活动承接复盘，验证它是否真的带来稳定订单与留存。"

    validation_agenda = [
        "下一轮验证应优先确认留存率和转化率的分母与周期定义。",
        "下一轮验证应把高表现活动拆到日期窗口，判断是否由单日峰值驱动。",
        "下一轮验证应把渠道、活动和内容做组合对比，识别真正稳定的增长组合。",
    ]

    return {
        "mode": "fallback",
        "reason": reason,
        "management_summary": "这份数据更适合按互联网运营复盘口径来组织：先看活跃与新增盘子，再看留存、转化、渠道承接和活动有效性。",
        "key_findings": key_findings[:5],
        "metric_interpretations": metric_interpretations[:5],
        "risk_flags": risk_flags[:5],
        "managerial_actions": managerial_actions[:5],
        "validation_agenda": validation_agenda[:5],
        "recommended_sections": [
            "运营总览",
            "渠道承接复盘",
            "活动结果复盘",
            "内容主题复盘",
            "下一轮验证议程",
        ],
    }


def _internet_ops_review_is_low_signal(result: dict[str, Any]) -> bool:
    management_summary = str(result.get("management_summary") or "")
    key_findings = [str(item) for item in result.get("key_findings", [])]
    managerial_actions = [str(item) for item in result.get("managerial_actions", [])]
    text = " ".join([management_summary, *key_findings, *managerial_actions])
    if sum(token in text for token in ["渠道", "活动", "内容", "留存", "转化", "订单", "日期"]) < 4:
        return True
    if not any(char.isdigit() for char in text):
        return True
    generic_fragments = ["继续观察", "提供依据", "支持优化", "服务于", "进一步分析"]
    if sum(fragment in text for fragment in generic_fragments) >= 3:
        return True
    if managerial_actions and not all("：" in item or ":" in item for item in managerial_actions[:3]):
        return True
    return False


def _fallback_business_background_analysis(reason: str, payload: dict[str, Any]) -> dict[str, Any]:
    background_name = str(payload.get("business_background_name") or "未命名业务背景")
    background_text = str(payload.get("business_background_text") or "").strip()
    report_lens = str(payload.get("report_lens") or "")
    fusion_enabled = _is_procurement_sales_management_fusion_payload(payload)
    core_purpose = str(payload.get("core_purpose") or payload.get("problem_to_solve") or "当前业务判断")
    top_channels = payload.get("channel_rows") or []
    top_activities = payload.get("activity_rows") or []
    top_contents = payload.get("content_rows") or []
    top_media = payload.get("media_rows") or []
    top_terminals = payload.get("terminal_rows") or []
    top_brands = payload.get("brand_rows") or []
    top_placements = payload.get("placement_rows") or []
    top_products = payload.get("product_rows") or []
    top_skus = payload.get("sku_rows") or []
    top_suppliers = payload.get("supplier_rows") or []
    top_slices = payload.get("slice_rows") or []
    summary = (
        f"业务背景 `{background_name}` 当前最像一份围绕 `{core_purpose}` 的任务说明。"
        if background_text
        else f"当前没有用户显式提供业务背景正文，系统按 `{report_lens}` 的典型业务背景来解释这份数据。"
    )
    if report_lens == "procurement_sales_review":
        summary = "当前这份数据更像一份电商采销经营复盘材料：重点不是重复讲背景，而是直接判断商品、SKU、卖家、履约和售后问题分别在拖动什么结果。"
    elif report_lens == "management_accounting_review" and fusion_enabled:
        summary = "当前这份数据更像一份采销经营与管理会计联动材料：既要看预算、责任主体和资金占用，也要看商品/SKU是否真正把采购投入转成销售结果。"
    key_points = []
    if background_text:
        key_points.append("背景材料里最重要的作用，是限定这份报告到底服务于汇报、优化还是验证，而不是让报告自由发挥。")
    if report_lens == "internet_ops_review":
        key_points.append("对互联网运营来说，业务背景真正决定的是：先看新增、先看留存，还是先看订单承接。")
        if top_channels:
            key_points.append(f"当前数据里头部渠道是 `{top_channels[0].get('渠道', '头部渠道')}`，背景解读必须回答这个渠道在当前目标里到底承担拉新、承接还是成交。")
        if top_activities:
            key_points.append(f"当前数据里头部活动是 `{top_activities[0].get('活动', '头部活动')}`，背景解读必须判断它更像短期冲量动作还是稳定经营动作。")
        if top_contents:
            key_points.append(f"当前数据里头部内容主题是 `{top_contents[0].get('内容主题', '头部内容主题')}`，背景解读必须回答它更适合做拉活、留存承接还是成交转化。")
    elif report_lens == "media_review":
        key_points.append("对投放复盘来说，这份数据最像执行与交付诊断材料，不应被误读成完整的市场份额研究或最终生意归因报告。")
        if top_media:
            key_points.append(f"当前头部媒体是 `{top_media[0].get('category', '头部媒体')}`，管理层真正要判断的是它该继续保留、修复执行，还是收缩资源。")
        if top_terminals:
            key_points.append(f"当前终端结构里 `{top_terminals[0].get('category', '头部终端')}` 占比更高，这意味着复盘要把触达场景和素材适配一起看，而不是只看总体均值。")
        if top_placements:
            key_points.append(f"当前点位层已出现 `{top_placements[0].get('category', '头部点位')}` 这类执行单元，因此业务背景必须把结论落到资源位纪律和排期执行，而不是停留在平台层。")
        if top_brands:
            key_points.append(f"当前品牌或产品线头部对象是 `{top_brands[0].get('category', '头部品牌')}`，但这更像阶段性投放承压主体，不直接等于真实市场领先。")
    elif report_lens == "sales_review":
        key_points.append("对商品经营来说，这份数据更适合支持样本内商品/SKU决策，而不是直接推导绝对市场份额或长期采购计划。")
        if top_products:
            key_points.append(f"当前头部商品是 `{top_products[0].get('对象', '头部商品')}`，背景解读必须回答它到底是主推款、承接款，还是只是样本内总量大。")
        if top_skus:
            key_points.append(f"当前头部SKU是 `{top_skus[0].get('对象', '头部SKU')}`，后续判断必须继续结合订单覆盖、客户覆盖和退货风险，而不是只看销量。")
        if top_suppliers:
            key_points.append(f"当前头部供应商是 `{top_suppliers[0].get('对象', '头部供应商')}`，背景解读必须继续判断它是稳定供给来源，还是履约/口碑风险来源。")
    elif report_lens == "procurement_sales_review":
        key_points.append("对采销专门复盘来说，这份数据最该回答的是哪些商品值得推、哪些卖家需要修、哪些履约和售后问题已经开始反噬经营结果。")
        if top_products:
            key_points.append(f"当前头部商品是 `{top_products[0].get('对象', '头部商品')}`，要先判断它是稳健主推，还是被售后或履约问题拖住。")
        if top_skus:
            key_points.append(f"当前头部SKU是 `{top_skus[0].get('对象', '头部SKU')}`，后续要继续看它的订单承接、客户覆盖、复购和低分评价。")
        if top_suppliers:
            key_points.append(f"当前头部卖家/供应商是 `{top_suppliers[0].get('对象', '头部卖家')}`，要判断它是稳定供给来源，还是履约和口碑风险来源。")
    elif report_lens == "management_accounting_review" and fusion_enabled:
        key_points.append("对采销一体来说，采购/预算控制和销售承接不是两份独立报告，而是一条经营闭环。")
        if top_slices:
            key_points.append(f"当前责任主体头部对象是 `{top_slices[0].get('经营切片', '头部主体')}`，背景解读必须回答它承担的预算或采购投入有没有真正转成销售结果。")
        if top_products:
            key_points.append(f"当前头部商品是 `{top_products[0].get('对象', '头部商品')}`，背景解读必须把它和责任主体、库存、退货风险一起看，而不是只给一张销售额榜单。")
        if top_skus:
            key_points.append(f"当前头部SKU是 `{top_skus[0].get('对象', '头部SKU')}`，后续结论必须继续落到采销动作，例如调采购、调结构、调库存，而不是停在观察层。")
        if top_suppliers:
            key_points.append(f"当前头部供应商是 `{top_suppliers[0].get('对象', '头部供应商')}`，后续结论必须继续比较它的履约时效、评价风险和销售承接，而不是只看供货规模。")
    decision_implications = [
        f"后续所有优化建议都应围绕 `{core_purpose}` 组织，不再把通用统计结论直接冒充业务动作。",
        "背景层的职责是限定判断边界：哪些能说成动作建议，哪些只能停留在观察层。",
    ]
    if report_lens == "internet_ops_review":
        decision_implications.append("互联网运营场景下，背景层必须把渠道、活动和内容分别映射到增长链条中的不同职责。")
    elif report_lens == "media_review":
        decision_implications.extend(
            [
                "投放场景下，优先级必须同时依赖规模、效率、兑现和稳定性，不能只按份额或总量给平台排座次。",
                "这类日报或阶段性执行数据更适合支持保留/修复/收缩判断，不足以单独支撑品牌份额或长期预算迁移结论。",
            ]
        )
    elif report_lens == "sales_review":
        decision_implications.extend(
            [
                "商品经营场景下，主推判断至少要同时看销售额、订单承接和客户覆盖，不能只看单列总量排名。",
                "如果缺少利润、库存或采购成本，这份报告就应停留在经营结构与样本内决策层，不上升成完整采销结论。",
            ]
        )
    elif report_lens == "procurement_sales_review":
        decision_implications.extend(
            [
                "采销专门场景下，结论必须落到商品、SKU、卖家、履约和售后动作，不再用预算控制语言复读。",
                "这类报告最核心的不是证明会分析，而是说明什么该主推、什么该修复、什么该清理，以及依据是什么。",
            ]
        )
    elif report_lens == "management_accounting_review" and fusion_enabled:
        decision_implications.extend(
            [
                "采销一体场景下，预算/采购判断必须同时解释钱花到哪里、货卖到哪里，以及库存和退货风险卡在哪里。",
                "这类数据不该被拆成一份财务控制报告加一份销售榜单，而应该直接压成责任主体、商品结构和资金效率的联动决策。",
            ]
        )
    return {
        "mode": "fallback",
        "reason": reason,
        "background_summary": summary,
        "key_points": key_points[:5],
        "decision_implications": decision_implications[:5],
    }


def codex_business_background_analysis(background_context: dict[str, Any]) -> dict[str, Any]:
    system_prompt = (
        "You are Codex acting as a senior business-background analyst. "
        "You must answer in Simplified Chinese and JSON only. "
        "You will receive user-provided business background, inferred business brief, and the top data slices already summarized from the dataset. "
        "Return keys: background_summary, key_points, decision_implications. "
        "All list fields must contain 3 to 5 concise Chinese strings. "
        "Your job is to explain what business role this dataset plays, what decision frame it should be read under, and how the business background should constrain the later recommendations. "
        "Do not summarize the background text mechanically. Tie it to concrete data objects such as 渠道、活动、内容主题、订单、留存、转化、商品、SKU or 责任中心 when available. "
        "If business background is blank, infer the most likely business context from the report lens and current top data slices instead of complaining."
    )
    tool_specs = [
        {
            "name": "lookup_background_context",
            "description": "Read selected background and top-slice fields before writing the business background analysis.",
            "parameters": {
                "type": "object",
                "properties": {
                    "fields": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["fields"],
                "additionalProperties": False,
            },
            "handler": lambda args: {
                key: background_context.get(key)
                for key in [str(item) for item in args.get("fields", [])[:16]]
            },
        }
    ]
    return _request_codex_agentic_json(
        system_prompt=system_prompt,
        user_payload=background_context,
        tool_specs=tool_specs,
        fallback_builder=_fallback_business_background_analysis,
    )


def _fallback_business_object_interpretation(reason: str, payload: dict[str, Any]) -> dict[str, Any]:
    object_meanings: list[dict[str, Any]] = []
    report_lens = str(payload.get("report_lens") or "")
    fusion_enabled = _is_procurement_sales_management_fusion_payload(payload)
    if report_lens == "internet_ops_review":
        for row in (payload.get("channel_rows") or [])[:4]:
            value = str(row.get("渠道") or row.get("对象") or "")
            if not value:
                continue
            inferred_role = {
                "社群": "私域承接渠道",
                "自然": "自然获取渠道",
                "广告": "付费获客渠道",
                "Push": "触达唤醒渠道",
                "联盟": "合作分发渠道",
                "搜索": "主动需求渠道",
            }.get(value, "运营渠道")
            object_meanings.append(
                {
                    "dimension": "渠道",
                    "value": value,
                    "inferred_role": inferred_role,
                    "business_meaning": f"`{value}` 在这份表里更像 `{inferred_role}`，当前应重点看它承担拉新、承接还是成交的哪一段职责。",
                    "action_hint": f"后续围绕 `{value}` 继续比较留存率、转化率和订单承接，决定它该扩量、维持还是只保留观察。",
                }
            )
        for row in (payload.get("activity_rows") or [])[:4]:
            value = str(row.get("活动") or row.get("对象") or "")
            if not value:
                continue
            inferred_role = {
                "拉新活动": "获客动作",
                "召回活动": "流失唤回动作",
                "内容上新": "内容供给动作",
                "会员促活": "存量激活动作",
                "搜索冲量": "短期冲量动作",
            }.get(value, "运营活动")
            object_meanings.append(
                {
                    "dimension": "活动",
                    "value": value,
                    "inferred_role": inferred_role,
                    "business_meaning": f"`{value}` 更像 `{inferred_role}`，当前要判断它带来的是短期流量峰值，还是能稳定转成留存与订单。",
                    "action_hint": f"把 `{value}` 拆到日期窗口和渠道来源，判断它适合继续放大，还是只适合短期使用。",
                }
            )
        for row in (payload.get("content_rows") or [])[:4]:
            value = str(row.get("内容主题") or row.get("对象") or "")
            if not value:
                continue
            inferred_role = {
                "品牌故事": "品牌认知内容",
                "产品卖点": "转化承接内容",
                "福利活动": "促销刺激内容",
                "策略教程": "教育承接内容",
            }.get(value, "内容主题")
            object_meanings.append(
                {
                    "dimension": "内容主题",
                    "value": value,
                    "inferred_role": inferred_role,
                    "business_meaning": f"`{value}` 更像 `{inferred_role}`，不能只按活跃高低判断，而要看它更适合拉活、留存承接还是成交转化。",
                    "action_hint": f"后续把 `{value}` 按拉活内容、承接内容、成交内容三类重新归位，再决定资源分配。",
                }
            )
    elif report_lens == "media_review":
        dimension_specs = [
            ("媒体", payload.get("media_rows") or [], {
                "抖音": "高频触达平台",
                "微博": "话题扩散平台",
                "小红书": "种草种智平台",
                "Bilibili": "年轻化内容平台",
            }, "平台角色不等于投放结论，还要结合兑现和稳定性判断保留还是收缩。"),
            ("终端", payload.get("terminal_rows") or [], {
                "PHONE端": "移动主触达场景",
                "OTT": "大屏触达场景",
                "PAD端": "跨屏补充场景",
            }, "终端更像触达场景，后续要和素材形态、点击效率、兑现偏差一起读。"),
            ("品牌", payload.get("brand_rows") or [], {}, "品牌在这里更像投放承压主体，不能直接把投放份额解释成市场份额。"),
            ("点位", payload.get("placement_rows") or [], {
                "开屏": "强打断高曝光资源位",
                "信息流": "连续浏览承接资源位",
                "前贴片": "视频前置曝光资源位",
            }, "点位是最接近执行动作的单元，后续应直接用来做保留、修复和排期调整。"),
        ]
        for dimension, rows, role_map, action_tail in dimension_specs:
            for row in rows[:4]:
                value = str(row.get("category") or row.get("对象") or "").strip()
                if not value:
                    continue
                inferred_role = role_map.get(value, f"{dimension}业务对象")
                object_meanings.append(
                    {
                        "dimension": dimension,
                        "value": value,
                        "inferred_role": inferred_role,
                        "business_meaning": f"`{value}` 在这份投放表里更像 `{inferred_role}`，应放进执行链路而不是只按总量排名。",
                        "action_hint": f"{action_tail} 因此 `{value}` 后续应继续比较规模、效率、兑现偏差和稳定性。",
                    }
                )
    elif report_lens == "sales_review":
        dimension_specs = [
            ("商品", payload.get("product_rows") or [], "商品经营单元", "后续先比较销售额、订单覆盖和客户覆盖，再决定它是主推款还是承接款。"),
            ("SKU", payload.get("sku_rows") or [], "最细颗粒经营单元", "后续继续看动销、订单承接和退货风险，再决定保留还是清退。"),
            ("品类", payload.get("category_rows") or [], "结构切片", "后续比较头部和长尾结构，再决定资源是否过度集中。"),
            ("供应商", payload.get("supplier_rows") or [], "供给与履约主体", "后续继续比较履约时效、低分评价占比和销售承接，再决定是重点合作还是先修复。"),
        ]
        for dimension, rows, inferred_role, action_hint in dimension_specs:
            for row in rows[:4]:
                value = str(row.get("对象") or "").strip()
                if not value:
                    continue
                sales = row.get("销售额总量", "n/a")
                customers = row.get("客户覆盖", "n/a")
                orders = row.get("订单覆盖", "n/a")
                object_meanings.append(
                    {
                        "dimension": dimension,
                        "value": value,
                        "inferred_role": inferred_role,
                        "business_meaning": f"`{value}` 在这份表里更像 `{inferred_role}`。当前销售额 `{sales}`、客户覆盖 `{customers}`、订单覆盖 `{orders}`。",
                        "action_hint": action_hint,
                    }
                )
    elif report_lens == "procurement_sales_review":
        for dimension, rows, inferred_role, action_hint in [
            ("商品", payload.get("product_rows") or [], "商品经营承接单元", "继续比较销售额、订单覆盖、客户覆盖、复购和低分评价，再决定是主推还是修复。"),
            ("SKU", payload.get("sku_rows") or [], "采销最细颗粒单元", "继续比较订单承接、复购、低分评价和履约时效，再决定补货、修复还是清理。"),
            ("品类", payload.get("category_rows") or [], "采销结构切片", "继续看品类头尾结构、卖家集中度和售后风险是否需要调结构。"),
            ("供应商", payload.get("supplier_rows") or [], "供给与履约主体", "继续比较销售贡献、履约时效、逾期率和低分评价占比，再决定重点合作还是优先修复。"),
        ]:
            for row in rows[:2]:
                value = str(row.get("对象") or "").strip()
                if not value:
                    continue
                details = []
                for label, key in [("销售额", "销售额总量"), ("订单覆盖", "订单覆盖"), ("客户覆盖", "客户覆盖"), ("低分评价占比", "低分评价占比"), ("逾期率", "逾期率")]:
                    value_text = str(row.get(key, "n/a"))
                    if value_text not in {"", "n/a"}:
                        details.append(f"{label} `{value_text}`")
                object_meanings.append(
                    {
                        "dimension": dimension,
                        "value": value,
                        "inferred_role": inferred_role,
                        "business_meaning": f"`{value}` 更像 `{inferred_role}`。当前{'、'.join(details) if details else '已形成可供判断的经营和履约信号'}。",
                        "action_hint": action_hint,
                    }
                )
    elif report_lens in {"management_accounting_review"} and fusion_enabled:
        for row in (payload.get("slice_rows") or [])[:4]:
            value = str(row.get("经营切片") or "").strip()
            if not value:
                continue
            object_meanings.append(
                {
                    "dimension": "责任主体",
                    "value": value,
                    "inferred_role": "采购/预算责任主体",
                    "business_meaning": f"`{value}` 在这份表里更像采购投入、预算执行或资源配置的责任承接主体，后续要和商品经营结果一起判断它花出去的钱有没有转成销售结果。",
                    "action_hint": f"围绕 `{value}` 继续对照头部商品、SKU、库存和退货风险，决定是继续投放资源、调结构还是收缩。",
                }
            )
        for dimension, rows, inferred_role, action_hint in [
            ("商品", payload.get("product_rows") or [], "商品经营承接单元", "把它和责任主体、预算与库存放到一张表里，判断采销动作是否要调整。"),
            ("SKU", payload.get("sku_rows") or [], "采销最细颗粒单元", "继续比较订单覆盖、客户覆盖、退货风险和库存占压，再决定调采购还是调经营动作。"),
            ("品类", payload.get("category_rows") or [], "采销结构切片", "继续看头部和长尾结构是否与预算、库存和责任主体匹配。"),
            ("供应商", payload.get("supplier_rows") or [], "供给与履约主体", "继续比较履约时效、口碑风险和销售承接，再决定保留、压价还是替换。"),
        ]:
            for row in rows[:4]:
                value = str(row.get("对象") or "").strip()
                if not value:
                    continue
                object_meanings.append(
                    {
                        "dimension": dimension,
                        "value": value,
                        "inferred_role": inferred_role,
                        "business_meaning": f"`{value}` 当前销售额 `{row.get('销售额总量', 'n/a')}`、订单覆盖 `{row.get('订单覆盖', 'n/a')}`、客户覆盖 `{row.get('客户覆盖', 'n/a')}`，因此它不只是销售对象，也是采销闭环里检验采购投入是否有效的结果单元。",
                        "action_hint": action_hint,
                    }
                )
    summary = "当前系统已根据表头、头部对象和值样本，对渠道、活动、内容主题在业务链条中的角色做初步判定。"
    key_points = [
        "对象意义层的职责，是先回答“它在业务链里是什么”，再回答“它该不该优先投入”。",
        "同样是头部对象，可能承担完全不同职责；渠道、活动、内容主题不能混成一个优先级名单。",
        "这层解释服务于业务背景中的资源分配与策略设计，而不是服务于方法展示。",
    ]
    if report_lens == "media_review":
        summary = "当前系统已根据表头、头部媒体/终端/品牌/点位对象和值样本，对投放链路里的对象职责做初步判定。"
        key_points = [
            "媒体、终端、品牌和点位属于不同层级的业务对象，不能被压成同一个优先级名单。",
            "对象意义层的作用，是先分清它是平台、场景、承压主体还是执行单元，再决定它该保留、修复还是收缩。",
            "这层解释服务于投放决策和执行复盘，而不是服务于表面上的资源排序。",
        ]
    elif report_lens == "sales_review":
        summary = "当前系统已根据表头、样本行以及商品/SKU聚合结果，对不同经营对象在商品经营链条中的角色做初步判定。"
        key_points = [
            "商品经营里最怕把高销售额直接写成最该主推，因此必须先分清谁贡献成交、谁覆盖客户、谁承担承接。",
            "商品、SKU、品类是不同层级的经营对象，不能压成同一份总量排名单。",
            "这层解释服务于主推、承接、观察和清退决策，而不是服务于方法展示。",
        ]
    elif report_lens == "procurement_sales_review":
        summary = "当前系统已把商品、SKU、品类和卖家放到同一条采销经营链上做角色判定，不再把所有对象压成同一套模板。"
        key_points = [
            "采销对象层最怕把商品、SKU、品类和卖家混成一张总量榜单，因此必须先分清谁回答销售承接、谁回答结构问题、谁回答供给与履约问题。",
            "同样是头部对象，商品回答的是卖什么，SKU回答的是怎么卖，卖家回答的是谁在供给并承担履约风险。",
            "这层解释服务于主推、修复、补货和卖家协同，而不是服务于泛化背景复读。",
        ]
    elif report_lens in {"management_accounting_review"} and fusion_enabled:
        summary = "当前系统已把责任主体、商品、SKU和品类放到同一条采销经营链上做初步角色判定，不再把预算控制和商品经营拆开解读。"
        key_points = [
            "采销一体里最怕把责任主体、商品和SKU压成同一种对象，因此必须先分清谁承担预算责任、谁承接销售结果、谁暴露库存和退货风险。",
            "同样是头部对象，责任主体回答的是钱花到哪里，商品/SKU回答的是货卖到哪里，二者必须联动解释。",
            "这层解释服务于采销结构调整、责任归属和资源配置，而不是服务于表面总量排序。",
        ]
    return {
        "mode": "fallback",
        "reason": reason,
        "background_summary": summary,
        "key_points": key_points,
        "decision_implications": ["后续建议必须先区分拉新、承接、成交三种职责，再决定资源去向。"],
        "object_meanings": object_meanings[:12],
    }


def codex_business_object_interpretation(object_context: dict[str, Any]) -> dict[str, Any]:
    system_prompt = (
        "You are Codex acting as a business-object interpretation agent. "
        "You must answer in Simplified Chinese and JSON only. "
        "You will receive table headers, semantic mapping, sample rows, top channels, top activities, top content themes, top categories/products/SKUs when available, and business background. "
        "Return keys: background_summary, key_points, decision_implications, object_meanings. "
        "object_meanings must be a list of 6 to 15 objects with keys: dimension, value, inferred_role, business_meaning, action_hint. "
        "Your job is to infer what each object means in the real business workflow. "
        "For example, determine whether a 渠道 is more like 私域承接 / 付费获客 / 自然需求, whether an 活动 is more like 拉新 / 召回 / 冲量 / 内容供给, whether a 内容主题 is more like 品牌认知 / 承接转化 / 教育 / 促销刺激, and whether a 商品/SKU is more like 引流款 / 承接款 / 主推款 / 长尾观察对象. "
        "Do not summarize mechanically. Tie every meaning to the current business background and explain how that role changes how the object should be evaluated. "
        "If the background is blank, infer the most likely business context from the table contents."
    )
    tool_specs = [
        {
            "name": "lookup_object_context",
            "description": "Read selected top objects, semantic roles, sample rows, and business background before interpreting business meaning.",
            "parameters": {
                "type": "object",
                "properties": {"fields": {"type": "array", "items": {"type": "string"}}},
                "required": ["fields"],
                "additionalProperties": False,
            },
            "handler": lambda args: {
                key: object_context.get(key)
                for key in [str(item) for item in args.get("fields", [])[:16]]
            },
        }
    ]
    return _request_codex_agentic_json(
        system_prompt=system_prompt,
        user_payload=object_context,
        tool_specs=tool_specs,
        fallback_builder=_fallback_business_object_interpretation,
    )


def _fallback_commercial_dimension_review(reason: str, payload: dict[str, Any]) -> dict[str, Any]:
    rows_by_dimension = payload.get("rows_by_dimension") or {}
    report_lens = str(payload.get("report_lens") or "")
    if not report_lens:
        dimension_keys = {str(key).strip() for key in rows_by_dimension.keys()}
        if dimension_keys & {"品类", "商品", "SKU", "SPU", "供应商", "卖家"}:
            report_lens = "procurement_sales_review"
    dimension_reviews: list[dict[str, Any]] = []
    for dimension, rows in rows_by_dimension.items():
        rows = rows or []
        if not rows:
            continue
        top = rows[0]
        customer_signal = top.get("客户覆盖")
        order_signal = top.get("订单覆盖")
        if report_lens == "procurement_sales_review":
            if dimension == "供应商":
                dimension_reviews.append(
                    {
                        "dimension": dimension,
                        "headline": f"供应商当前最该关注的是 `{top.get('对象', '头部供应商')}`",
                        "finding": f"它当前销售额 `{top.get('销售额总量', 'n/a')}`、逾期率 `{top.get('逾期率', 'n/a')}`、低分评价占比 `{top.get('低分评价占比', 'n/a')}`。这说明卖家判断不能只看卖了多少，还要看履约和口碑有没有在拖后腿。",
                        "business_action": f"后续围绕 `{top.get('对象', '头部供应商')}` 继续比较销售贡献、履约时效、逾期率和低分评价占比，再决定是重点合作、先修复还是收缩。",
                    }
                )
                continue
            if dimension == "品类":
                dimension_reviews.append(
                    {
                        "dimension": dimension,
                        "headline": f"品类结构当前头部是 `{top.get('对象', '头部品类')}`",
                        "finding": f"它当前销售额 `{top.get('销售额总量', 'n/a')}`、订单覆盖 `{order_signal or 'n/a'}`、客户覆盖 `{customer_signal or 'n/a'}`。这说明品类层更该回答结构集中度和资源倾斜，而不是简单给单品动作。",
                        "business_action": f"后续围绕 `{top.get('对象', '头部品类')}` 继续看头尾结构、卖家集中度和低分评价占比，决定该扩品类、调结构还是压风险。",
                    }
                )
                continue
        dimension_reviews.append(
            {
                "dimension": dimension,
                "headline": f"{dimension}当前头部对象是 `{top.get('对象', '头部对象')}`",
                "finding": f"它当前在销售额上领先，客户覆盖为 `{customer_signal or 'n/a'}`、订单覆盖为 `{order_signal or 'n/a'}`。这说明是否值得重点经营，必须继续区分它是主推款、承接款，还是只是样本内总量大。",
                "business_action": f"后续围绕 `{top.get('对象', '头部对象')}` 继续比较头部与次头部对象在动销、客户覆盖、订单承接和退货风险上的差异，再决定是主推、保留、观察还是清退。",
            }
        )
    return {
        "mode": "fallback",
        "reason": reason,
        "management_summary": (
            "这份数据更适合按京东采销经营决策口径来读：先看商品和SKU是否承接销售，再看卖家履约与售后是否在拖动结果。"
            if report_lens == "procurement_sales_review"
            else "这份数据更适合按商品经营决策口径来读：先看谁贡献销售额和订单，再看谁覆盖客户、谁承担承接、谁只是样本内总量大。"
        ),
        "dimension_reviews": dimension_reviews[:8],
        "priority_actions": (
            [
                "优先区分主推、修复、观察和清理对象，不再把商品、SKU和卖家压成一张总量榜单。",
                "把商品和 SKU 看成交与承接，把卖家看履约与口碑，再决定主推、补货和修复动作。",
                "对头部卖家继续比较销售贡献、逾期率和低分评价占比，避免把卖得多直接写成合作最优。",
            ]
            if report_lens == "procurement_sales_review"
            else [
                "优先区分主推候选、承接候选、观察对象和清退/退货排查对象，不再只看总销售额。",
                "把商品和 SKU 按客户覆盖、订单承接和销售额贡献三条线拆开管理。",
                "对头部 SKU 继续看动销、客户覆盖和退货风险，避免把高销量直接写成健康经营。",
            ]
        ),
    }


def codex_commercial_dimension_review(review_context: dict[str, Any]) -> dict[str, Any]:
    system_prompt = (
        "You are Codex acting as a commercial dimension review agent inspired by JD merchandising and category management workflows. "
        "You must answer in Simplified Chinese and JSON only. "
        "You will receive category/product/SKU/SPU rows, business background, and current analytical context. "
        "Return keys: management_summary, dimension_reviews, priority_actions. "
        "dimension_reviews must be a list of objects with keys: dimension, headline, finding, business_action. "
        "Your job is to explain what the category/product/SKU structure means for real merchandising decisions such as 主推、承接、利润、低效占用、动销、周转 or inventory pressure. "
        "Do not invent unavailable metrics; if profit or inventory is absent, say the decision should stay at order/revenue/structure level."
    )
    tool_specs = [
        {
            "name": "lookup_commercial_context",
            "description": "Read selected category/product/SKU rows and business background before writing the commercial review.",
            "parameters": {
                "type": "object",
                "properties": {"fields": {"type": "array", "items": {"type": "string"}}},
                "required": ["fields"],
                "additionalProperties": False,
            },
            "handler": lambda args: {
                key: review_context.get(key)
                for key in [str(item) for item in args.get("fields", [])[:16]]
            },
        }
    ]
    return _request_codex_agentic_json(
        system_prompt=system_prompt,
        user_payload=review_context,
        tool_specs=tool_specs,
        fallback_builder=_fallback_commercial_dimension_review,
    )


def _legacy_codex_internet_ops_review_stage1(ops_context: dict[str, Any]) -> dict[str, Any]:
    system_prompt = (
        "You are Codex acting as a senior internet operations review agent. "
        "You must answer in Simplified Chinese and return JSON only. "
        "You will receive an already analyzed internet operations dataset, including topline metrics, channel scorecards, activity scorecards, content/theme slices, statistical method results, and inferred business requirement context. "
        "If the user's business input was blank, treat the provided completed requirement fields as the governing business brief and read the dataset directly. "
        "Your job is to turn existing analysis into operator-grade conclusions, not to repeat generic growth advice. "
        "Return keys: management_summary, key_findings, metric_interpretations, risk_flags, managerial_actions, validation_agenda, recommended_sections. "
        "All list fields must contain 3 to 5 concise Chinese strings. "
        "Every conclusion must tie to actual objects such as 渠道, 活动, 内容主题, 留存率, 转化率, 订单数, or 日期窗口. "
        "Use the provided statistical findings where available, and mention what they mean for growth judgment in Chinese. "
        "Do not write generic statements like '需要继续观察' unless you say what to observe, on which object, and why. "
        "If business inputs were blank, do not complain; use the completed request fields and the dataset evidence to infer the most likely business objective."
    )
    tool_specs = [
        {
            "name": "lookup_ops_context",
            "description": "Read selected topline, channel, activity, content, and requirement fields before writing the internet operations review.",
            "parameters": {
                "type": "object",
                "properties": {
                    "fields": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["fields"],
                "additionalProperties": False,
            },
            "handler": lambda args: {
                key: ops_context.get(key)
                for key in [str(item) for item in args.get("fields", [])[:14]]
            },
        }
    ]
    result = _request_codex_agentic_json(
        system_prompt=system_prompt,
        user_payload=ops_context,
        tool_specs=tool_specs,
        fallback_builder=_fallback_internet_ops_review,
    )
    if result.get("mode") == "fallback":
        return result
    if _internet_ops_review_is_low_signal(result):
        return _fallback_internet_ops_review("low_signal_ops_review", ops_context)
    return result


def _fallback_internet_ops_review(reason: str, payload: dict[str, Any]) -> dict[str, Any]:
    topline_rows = payload.get("topline_rows") or []
    channel_rows = payload.get("channel_rows") or []
    activity_rows = payload.get("activity_rows") or []
    content_rows = payload.get("content_rows") or []
    channel_impact_rows = payload.get("channel_impact_rows") or []
    activity_impact_rows = payload.get("activity_impact_rows") or []
    content_impact_rows = payload.get("content_impact_rows") or []
    combo_rows = payload.get("combo_rows") or []
    combo_action_rows = payload.get("combo_action_rows") or []
    method_reviews = payload.get("method_reviews") or []
    method_findings = payload.get("method_findings") or []

    key_findings: list[str] = []
    metric_interpretations: list[str] = []
    risk_flags: list[str] = []
    managerial_actions: list[str] = []
    validation_agenda: list[str] = []

    topline_lookup = {str(row.get("核心指标") or row.get("metric") or ""): row for row in topline_rows}
    active_row = topline_lookup.get("活跃用户总量") or next(iter(topline_lookup.values()), None)
    new_row = topline_lookup.get("新增用户总量")
    retained_row = topline_lookup.get("留存用户总量")
    orders_row = topline_lookup.get("订单总量")

    if active_row:
        key_findings.append(
            f"当前运营盘子的基础量级是 `{active_row.get('核心指标', '活跃用户总量')}`={active_row.get('总量', 'n/a')}，均值 {active_row.get('均值', 'n/a')}、中位数 {active_row.get('中位数', 'n/a')}。这说明汇报不能只看平均水平，必须同时判断是不是被少数峰值日拉高。"
        )
    if new_row and retained_row:
        key_findings.append(
            f"新增总量 {new_row.get('总量', 'n/a')}、留存总量 {retained_row.get('总量', 'n/a')}，这份表更适合回答“哪里在起量、哪里在承接”，而不是只回答单次活动有没有冲高。"
        )
    if orders_row:
        key_findings.append(
            f"订单总量 {orders_row.get('总量', 'n/a')} 让这份数据可以继续往承接质量上走，后续每个渠道和活动都应该同时看规模、留存和订单，而不是只看活跃。"
        )

    if channel_impact_rows or channel_rows:
        top_channel = (channel_impact_rows or channel_rows)[0]
        second_channel = (channel_impact_rows or channel_rows)[1] if len((channel_impact_rows or channel_rows)) > 1 else None
        top_share = _parse_numberish(top_channel.get("活跃占比"))
        second_share = _parse_numberish(second_channel.get("活跃占比")) if second_channel else None
        top_channel_name = str(top_channel.get("对象") or top_channel.get("渠道") or "头部渠道")
        if top_share is not None and second_share is not None and abs(top_share - second_share) < 0.03:
            key_findings.append(
                f"`{top_channel_name}` 当前活跃占比 {top_channel.get('活跃占比', 'n/a')}、留存率 {top_channel.get('留存率', 'n/a')}、转化率 {top_channel.get('转化率', 'n/a')}，相对整体的订单均值为 {top_channel.get('订单均值相对整体', top_channel.get('订单均值', 'n/a'))}。但渠道份额差距并不大，头部渠道和次头部渠道之间没有拉出极端断层，现在不能直接把它写成“最优先渠道”。"
            )
        managerial_actions.append(
            (
                f"{top_channel_name}：先把它放进第一轮复盘名单，但不要直接定为唯一重点；继续下钻到 `{top_channel_name}` × 活动 × 内容主题，比较它和次头部渠道谁在留存、转化和订单承接上更稳。"
                if top_share is not None and second_share is not None and abs(top_share - second_share) < 0.03
                else f"{top_channel_name}：因为它同时承担当前最大的活跃盘子和较高的留存/转化承接，先把它作为一级复盘对象，继续下钻到 `{top_channel_name}` × 活动 × 内容主题，找能稳定复制的增长组合。"
            )
        )

    if activity_impact_rows or activity_rows:
        top_activity = (activity_impact_rows or activity_rows)[0]
        activity_name = str(top_activity.get("对象") or top_activity.get("活动") or "头部活动")
        key_findings.append(
            f"`{activity_name}` 当前活跃总量 {top_activity.get('活跃总量', top_activity.get('活跃用户', 'n/a'))}、活跃均值 {top_activity.get('活跃均值', 'n/a')}、订单均值 {top_activity.get('订单均值', 'n/a')}、留存率 {top_activity.get('留存率', 'n/a')}。这一步只能证明它是头部活动之一，还不能证明它是效率最优活动。"
        )
        managerial_actions.append(
            f"{activity_name}：围绕这类活动先拆日期窗口、内容主题和渠道来源，确认高表现是稳定机制还是少数峰值日造成的短冲。"
        )

    if content_impact_rows or content_rows:
        top_content = (content_impact_rows or content_rows)[0]
        content_name = str(top_content.get("对象") or top_content.get("内容主题") or "头部内容主题")
        key_findings.append(
            f"`{content_name}` 当前活跃总量 {top_content.get('活跃总量', 'n/a')}、活跃均值 {top_content.get('活跃均值', 'n/a')}、订单均值 {top_content.get('订单均值', 'n/a')}、转化率 {top_content.get('转化率', 'n/a')}。这一步只能说明它是头部主题之一，后续还要确认它到底承担拉活、承接还是成交。"
        )
        managerial_actions.append(
            f"{content_name}：如果它主要贡献活跃而没有同步带来更高订单，就把它当成拉活内容继续做分发，不要直接按成交内容的标准去扩量。"
        )

    if combo_rows:
        top_combo = combo_rows[0]
        top_combo_name = str(top_combo.get("组合") or "头部组合")
        key_findings.append(
            f"`{top_combo_name}` 当前是组合层的总量头部，活跃占比 {top_combo.get('活跃占比', 'n/a')}、订单均值 {top_combo.get('订单均值', 'n/a')}、留存率 {top_combo.get('留存率', 'n/a')}、稳定性 `{top_combo.get('稳定性', 'n/a')}`。这比只看单一渠道或活动更接近真实运营动作单元。"
        )
        managerial_actions.insert(
            0,
            f"{top_combo_name}：先按组合复盘它的新增、留存和订单承接是否同时成立；如果订单均值和留存率没有同步领先，就不要把它直接升格成长期增长方法。"
        )
    if combo_action_rows:
        first_combo_action = combo_action_rows[0]
        action_text = str(first_combo_action.get("动作") or "").strip()
        evidence_text = str(first_combo_action.get("依据") or "").strip()
        signal_text = str(first_combo_action.get("验证信号") or "").strip()
        if action_text:
            managerial_actions.insert(
                0,
                f"{action_text} 关键验证信号：{signal_text or '看组合层留存、转化和订单承接是否持续领先'}。依据：{evidence_text or '当前组合效果比较表'}"
            )

    if method_reviews:
        for review in method_reviews[:4]:
            result_meaning = str(review.get("result_meaning") or "").strip()
            business_takeaway = str(review.get("business_takeaway") or "").strip()
            caution = str(review.get("caution") or "").strip()
            if result_meaning:
                metric_interpretations.append(result_meaning[:220])
            if business_takeaway and business_takeaway not in key_findings:
                key_findings.append(business_takeaway[:220])
            if caution and caution not in risk_flags:
                risk_flags.append(caution[:200])
    elif method_findings:
        for finding in method_findings[:3]:
            result = str(finding.get("result") or "").strip()
            if result:
                metric_interpretations.append(result[:220])

    if not risk_flags:
        risk_flags.extend(
            [
                "当前方法结果主要用于排序和识别线索，不能把样本内联动直接写成渠道或活动的因果提升。",
                "如果留存率、转化率的分母和周期口径还没有锁定，当前结论只能停留在样本内观察层。",
            ]
        )

    validation_agenda.extend(
        [
            "下一轮验证优先确认留存率和转化率的分母、周期和统计口径，避免把口径问题误写成运营问题。",
            "下一轮验证要把头部渠道、头部活动和头部内容主题拆到日期窗口，看高表现是否由少数峰值日驱动。",
            "下一轮验证按渠道×活动×内容主题做组合对比，只保留那些在规模、留存和订单承接上同时站得住的增长组合。",
        ]
    )

    return {
        "mode": "fallback",
        "reason": reason,
        "management_summary": "这份数据更适合按互联网运营复盘口径来读：先看盘子大小，再看承接质量，最后才决定资源该往哪些渠道、活动和内容主题上移动。",
        "key_findings": key_findings[:5],
        "metric_interpretations": metric_interpretations[:5],
        "risk_flags": risk_flags[:5],
        "managerial_actions": managerial_actions[:5],
        "validation_agenda": validation_agenda[:5],
        "recommended_sections": [
            "渠道经营判断",
            "活动承接判断",
            "内容主题判断",
            "方法结果与动作翻译",
        ],
    }


def codex_internet_ops_review(ops_context: dict[str, Any]) -> dict[str, Any]:
    system_prompt = (
        "You are Codex acting as a senior internet operations review agent. "
        "You must answer in Simplified Chinese and return JSON only. "
        "You will receive an already analyzed internet operations dataset, including topline metrics, channel scorecards, activity scorecards, content/theme slices, channel/activity/content impact rows, combo impact rows, statistical method results, method reviews, and inferred business requirement context. "
        "If the user's business input was blank, treat the provided completed requirement fields as the governing business brief and read the dataset directly. "
        "Your job is to turn existing analysis into operator-grade conclusions, not to repeat generic growth advice. "
        "Return keys: management_summary, key_findings, metric_interpretations, risk_flags, managerial_actions, validation_agenda, recommended_sections. "
        "All list fields must contain 3 to 5 concise Chinese strings. "
        "Every conclusion must tie to actual objects such as 渠道、活动、内容主题、留存率、转化率、订单数或日期窗口。 "
        "If you mention p值、相关系数、R²、RMSE、准确率或F1, you must explain what the number means for the business in plain Chinese. "
        "Every managerial_actions item must follow the pattern '对象 + 依据 + 动作'. "
        "Do not write generic statements like '继续观察' or '提供依据' unless you say what object to observe, by which metric, and what decision depends on it. "
        "If combo_action_rows already exists, do not ask the reader to build another combo table or dashboard first; convert the existing combo comparison into direct actions. "
        "If business inputs were blank, do not complain; use the completed request fields and the dataset evidence to infer the most likely business objective."
    )
    tool_specs = [
        {
            "name": "lookup_ops_context",
            "description": "Read selected topline, channel, activity, content, impact rows, combo rows, method review, and requirement fields before writing the internet operations review.",
            "parameters": {
                "type": "object",
                "properties": {
                    "fields": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["fields"],
                "additionalProperties": False,
            },
            "handler": lambda args: {
                key: ops_context.get(key)
                for key in [str(item) for item in args.get("fields", [])[:16]]
            },
        }
    ]
    return _request_codex_agentic_json(
        system_prompt=system_prompt,
        user_payload=ops_context,
        tool_specs=tool_specs,
        fallback_builder=_fallback_internet_ops_review,
    )


def codex_classify_business_context(classification_context: dict[str, Any]) -> dict[str, Any]:
    system_prompt = (
        "You are Codex acting as a principal analytics architect. "
        "You must answer in Simplified Chinese and return JSON only. "
        "Your job is to classify what business family and data object this dataset most likely belongs to, "
        "using the provided headers, column profiles, sample rows, user intent, and existing heuristic candidates. "
        "Return keys: task_family_candidates, object_candidates, column_role_hints, notes. "
        "task_family_candidates: list of 1 to 4 items with fields family, score, confidence, why. "
        "object_candidates: list of 1 to 4 items with fields object_type, score, confidence, observation_unit, why. "
        "column_role_hints: list of up to 12 items with fields column, role, confidence, why. "
        "Use only these confidence labels: high, medium, low. "
        "Prefer precise business families such as media_review, sales_review, procurement_sales_review, foundation_review, management_accounting_review, consumer_research, "
        "brand_listening, experiment_review, channel_review, pricing_review, performance_benchmark, mixed_business_review. "
        "Prefer precise object types such as media_performance_log, sales_transaction_panel, nonprofit_project_portfolio, "
        "crm_funnel_event_log, survey_response_table, brand_social_listening, financial_budget_table, management_accounting_statement, experiment_result_table, "
        "regional_time_series_performance, performance_benchmark_table, generic_business_table. "
        "Do not invent unsupported facts. If uncertain, keep confidence low and explain why."
    )
    tool_specs = [
        {
            "name": "lookup_business_classification_context",
            "description": "Read selected headers, profiles, samples, semantic mapping, and heuristic candidates before classifying the business context.",
            "parameters": {
                "type": "object",
                "properties": {
                    "fields": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["fields"],
                "additionalProperties": False,
            },
            "handler": lambda args: {
                key: classification_context.get(key)
                for key in [str(item) for item in args.get("fields", [])[:14]]
            },
        }
    ]
    return _request_codex_agentic_json(
        system_prompt=system_prompt,
        user_payload=classification_context,
        tool_specs=tool_specs,
        fallback_builder=_fallback_business_classification,
    )


def codex_historical_report_adaptation(adaptation_context: dict[str, Any]) -> dict[str, Any]:
    system_prompt = (
        "You are Codex acting as a principal consulting writer. "
        "You must answer in Simplified Chinese. "
        "The user provided a historical report example and wants a new report that keeps the historical structure and tone but replaces all facts, numbers, and conclusions with the current dataset evidence. "
        "When the historical report resembles consulting output, prefer answer-first writing, SCQA framing, and pyramid-structured reasoning. "
        "This is not a template fill exercise: the rewritten report must still discover fresh insights, trends, drivers, risks, and next actions from the new data. "
        "Use the historical report as structural guidance only. Do not copy placeholder bullets or generic sentences from it. "
        "Every section in the rewritten report must contain concrete findings tied to the new data; otherwise omit or soften that section. "
        "Return JSON only with keys: title, source_name, template_signals, adaptation_notes, adapted_report_markdown. "
        "template_signals and adaptation_notes must be concise Chinese bullet strings, 3 to 5 each. "
        "adapted_report_markdown must be a complete Chinese markdown report. "
        "Reuse the historical report's sectioning logic, narrative cadence, and consulting-style framing when possible, but never copy unsupported facts. "
        "If the historical report includes sections not supported by the current data, omit or soften them explicitly."
    )
    tool_specs = [
        {
            "name": "lookup_historical_context",
            "description": "Read selected historical adaptation context fields and summaries.",
            "parameters": {
                "type": "object",
                "properties": {
                    "fields": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["fields"],
                "additionalProperties": False,
            },
            "handler": lambda args: {
                key: adaptation_context.get(key)
                for key in [str(item) for item in args.get("fields", [])[:10]]
            },
        }
    ]
    return _request_codex_agentic_json(
        system_prompt=system_prompt,
        user_payload=adaptation_context,
        tool_specs=tool_specs,
        fallback_builder=_fallback_historical_report_adaptation,
    )


def _fallback_evidence_digest(reason: str, payload: dict[str, Any]) -> dict[str, Any]:
    requirement = payload.get("requirement_layer", {}) or {}
    method_review = payload.get("method_review_layer", {}) or {}
    semantic_layer = payload.get("semantic_layer", {}) or {}
    metric_interpretation_layer = payload.get("metric_interpretation_layer", {}) or {}
    business_background_layer = payload.get("business_background_layer", {}) or {}
    business_object_layer = payload.get("business_object_layer", {}) or {}
    relation_context = payload.get("relation_context", {}) or {}
    gate_feedback_layer = payload.get("gate_feedback_layer") or {}
    gate_issue_codes = [str(item).strip() for item in (gate_feedback_layer.get("issue_codes") or []) if str(item).strip()]
    gate_revision_suggestions = [str(item).strip() for item in (gate_feedback_layer.get("revision_suggestions") or []) if str(item).strip()]
    context_compaction = payload.get("context_compaction", {}) or {}
    compact_pack = context_compaction.get("compact_evidence_pack", {}) or {}
    section_drafts = payload.get("section_drafts", []) or []

    priority_evidence: list[str] = _clean_fallback_lines(
        compact_pack.get("priority_evidence", []),
        require_result_signal=True,
        limit=6,
    )
    if len(priority_evidence) < 4:
        metric_evidence = []
        for card in metric_interpretation_layer.get("metric_cards", [])[:6]:
            metric = str(card.get("metric") or "").strip()
            meaning = str(card.get("business_meaning") or "").strip()
            impact = str(card.get("management_impact") or "").strip()
            if metric and meaning:
                metric_evidence.append(f"{metric}：{meaning}")
            elif metric:
                metric_evidence.append(metric)
            if impact:
                metric_evidence.append(f"{metric or '该指标'}=>{impact}")
        priority_evidence.extend(_clean_fallback_lines(metric_evidence, limit=4))
    for section in section_drafts[:18]:
        priority_evidence.extend(_clean_fallback_lines([section.get("summary"), *(section.get("bullets") or [])], require_result_signal=True, limit=2))
        if len(priority_evidence) >= 8:
            break
    if len(priority_evidence) < 4:
        priority_evidence.extend(
            _clean_fallback_lines(
                [item.get("business_meaning") for item in metric_interpretation_layer.get("metric_cards", [])[:6]],
                require_result_signal=True,
                limit=4,
            )
        )
    if len(priority_evidence) < 4:
        priority_evidence.extend(
            _clean_fallback_lines(
                [item.get("result_meaning") for item in method_review.get("method_reviews", [])[:6]],
                limit=4,
            )
        )
    if len(priority_evidence) < 4:
        priority_evidence.extend(
            _clean_fallback_lines(
                [
                    f"{item.get('method')}=>{item.get('headline') or item.get('result_meaning')}"
                    for item in method_review.get("method_reviews", [])[:6]
                    if item.get("method")
                ],
                limit=4,
            )
        )
    if len(priority_evidence) < 3:
        priority_evidence.extend(_clean_fallback_lines(requirement.get("must_answer_questions", [])[:3], limit=3))
    if len(priority_evidence) < 6:
        priority_evidence.extend(
            _clean_fallback_lines(relation_context.get("relation_findings", [])[:6], require_result_signal=True, limit=4)
        )

    key_metrics = [str(item) for item in compact_pack.get("key_metrics", [])[:6] if str(item).strip()]
    if not key_metrics:
        key_metrics = [str(item.get("metric") or "") for item in metric_interpretation_layer.get("metric_cards", [])[:5] if item.get("metric")]
    key_slices = [str(item) for item in compact_pack.get("key_objects", [])[:6] if str(item).strip()]
    key_slices.extend([
        f"{item.get('dimension')}:{item.get('value')}=>{item.get('inferred_role')}"
        for item in business_object_layer.get("object_meanings", [])[:6]
        if item.get("value")
    ])
    for item in relation_context.get("dimension_profiles", [])[:4]:
        dimension = str(item.get("dimension") or "")
        head = ((item.get("head") or {}).get("对象")) if isinstance(item.get("head"), dict) else None
        middle = ((item.get("middle") or {}).get("对象")) if isinstance(item.get("middle"), dict) else None
        tail = ((item.get("tail") or {}).get("对象")) if isinstance(item.get("tail"), dict) else None
        if dimension and head:
            key_slices.append(f"{dimension}:头部=>{head}")
        if dimension and middle:
            key_slices.append(f"{dimension}:中位=>{middle}")
        if dimension and tail:
            key_slices.append(f"{dimension}:底部=>{tail}")
    key_methods = [str(item) for item in compact_pack.get("key_methods", [])[:6] if str(item).strip()]
    key_methods.extend([
        f"{item.get('method')}=>{item.get('headline')}"
        for item in method_review.get("method_reviews", [])[:6]
        if item.get("method")
    ])
    key_anomalies = [str(item) for item in semantic_layer.get("numeric_findings", [])[:4] if str(item).strip()]
    key_boundaries = [str(item) for item in compact_pack.get("risk_signals", [])[:5] if str(item).strip()]
    key_boundaries.extend(str(item) for item in business_background_layer.get("decision_implications", [])[:3] if str(item).strip())
    key_boundaries.extend(str(item.get("caution") or "") for item in method_review.get("method_reviews", [])[:2] if item.get("caution"))
    return {
        "mode": "fallback",
        "reason": reason,
        "headline": "已将底层证据压成优先证据视图，供后续洞察和判断层使用。",
        "priority_evidence": priority_evidence[:8],
        "key_metrics": key_metrics[:6],
        "key_slices": key_slices[:6],
        "key_methods": key_methods[:6],
        "key_anomalies": key_anomalies[:5],
        "key_boundaries": key_boundaries[:5],
    }


def codex_evidence_digest(digest_context: dict[str, Any]) -> dict[str, Any]:
    system_prompt = (
        "You are Codex acting as an Evidence Digest Agent. "
        "You must answer in Simplified Chinese and JSON only. "
        "You will receive Layer 1 outputs such as requirement completion, semantic analysis, metric interpretation, method review, business background reading, object interpretation, and drafted sections. "
        "If context_compaction is present, treat compact_evidence_pack as the primary compressed evidence base and only use the raw layers to fill gaps. "
        "Do not make new judgments. Your only job is to compress and prioritize evidence. "
        "Return keys: headline, priority_evidence, key_metrics, key_slices, key_methods, key_anomalies, key_boundaries. "
        "All list fields must contain 3 to 8 concise Chinese strings. "
        "Prefer evidence that is most decision-relevant, most concrete, or most likely to constrain later judgment."
    )
    tool_specs = [
        {
            "name": "lookup_digest_context",
            "description": "Read selected evidence-layer fields before digesting them.",
            "parameters": {
                "type": "object",
                "properties": {"fields": {"type": "array", "items": {"type": "string"}}},
                "required": ["fields"],
                "additionalProperties": False,
            },
            "handler": lambda args: {
                key: digest_context.get(key)
                for key in [str(item) for item in args.get("fields", [])[:16]]
            },
        }
    ]
    return _request_codex_agentic_json(
        system_prompt=system_prompt,
        user_payload=digest_context,
        tool_specs=tool_specs,
        fallback_builder=_fallback_evidence_digest,
    )


def _fallback_insight_mining(reason: str, payload: dict[str, Any]) -> dict[str, Any]:
    evidence = payload.get("evidence_digest_layer", {}) or {}
    relation_context = payload.get("relation_context", {}) or {}
    context_compaction = payload.get("context_compaction", {}) or {}
    compact_relations = ((context_compaction.get("relation_matrix", {}) or {}).get("relation_findings", []) or [])[:6]
    priority_evidence = _clean_fallback_lines(evidence.get("priority_evidence", []), require_result_signal=True, limit=6)
    if not priority_evidence:
        priority_evidence = _clean_fallback_lines(evidence.get("priority_evidence", []), limit=6)
    relation_findings = _clean_fallback_lines(
        relation_context.get("relation_findings", [])[:6] or compact_relations,
        require_result_signal=True,
        limit=4,
    )
    if not relation_findings:
        relation_findings = _clean_fallback_lines(relation_context.get("relation_findings", [])[:6] or compact_relations, limit=4)
    important_findings = (relation_findings + priority_evidence)[:4]
    if not important_findings:
        important_findings = _clean_fallback_lines(
            [
                *(evidence.get("priority_evidence") or []),
                *(evidence.get("key_methods") or []),
                *(evidence.get("key_boundaries") or []),
            ],
            limit=4,
        )
    noise_findings = [str(item) for item in evidence.get("key_metrics", [])[4:6] if str(item).strip()]
    mechanism_hypotheses = relation_findings[:2] or [
        "真正值得写进正文的，不是所有指标，而是能同时影响规模、效率和承接的关键链路。",
        "如果头部对象只是总量领先而效率不领先，这更像样本覆盖差异，不像稳定机制差异。",
    ]
    priority_insights = [
        {
            "title": f"洞察{i+1}",
            "insight": item,
            "why_it_matters": "它直接影响主报告该围绕什么写，而不是继续堆指标。",
            "evidence_refs": " / ".join((evidence.get("key_methods") or [])[:2]) or "证据层摘要",
        }
        for i, item in enumerate(important_findings[:4])
    ]
    return {
        "mode": "fallback",
        "reason": reason,
        "headline": "已从证据层提炼出更值得进入正文的结构性发现。",
        "priority_insights": priority_insights,
        "important_findings": important_findings[:6],
        "noise_findings": noise_findings[:4],
        "mechanism_hypotheses": mechanism_hypotheses[:4],
    }


def codex_insight_mining(insight_context: dict[str, Any]) -> dict[str, Any]:
    system_prompt = (
        "You are Codex acting as an Insight Mining Agent. "
        "You must answer in Simplified Chinese and JSON only. "
        "You will receive an evidence digest plus business background and object interpretation. "
        "If context_compaction is present, use object_summaries and relation_matrix to avoid shallow or repetitive insight claims. "
        "Your job is to mine non-obvious insights worth entering the main report. "
        "Do not restate raw metrics. Distinguish important findings from noise. "
        "Return keys: headline, priority_insights, important_findings, noise_findings, mechanism_hypotheses. "
        "priority_insights must be a list of objects with keys: title, insight, why_it_matters, evidence_refs."
    )
    tool_specs = [
        {
            "name": "lookup_insight_context",
            "description": "Read selected digest and business-context fields before mining insights.",
            "parameters": {
                "type": "object",
                "properties": {"fields": {"type": "array", "items": {"type": "string"}}},
                "required": ["fields"],
                "additionalProperties": False,
            },
            "handler": lambda args: {
                key: insight_context.get(key)
                for key in [str(item) for item in args.get("fields", [])[:16]]
            },
        }
    ]
    return _request_codex_agentic_json(
        system_prompt=system_prompt,
        user_payload=insight_context,
        tool_specs=tool_specs,
        fallback_builder=_fallback_insight_mining,
    )


def _followup_row_score(row: dict[str, Any], *, weight_keys: list[str]) -> float:
    score = 0.0
    for key in weight_keys:
        value = _parse_numberish(row.get(key))
        if value is None:
            continue
        score += value
    return score


def _fallback_followup_mining(reason: str, payload: dict[str, Any]) -> dict[str, Any]:
    rows_by_dimension = payload.get("rows_by_dimension") or {}
    report_lens = str(payload.get("report_lens") or "")
    semantic_followup_prompts = payload.get("semantic_followup_prompts") or []
    gate_feedback_layer = payload.get("gate_feedback_layer") or {}
    gate_issue_codes = [str(item).strip() for item in (gate_feedback_layer.get("issue_codes") or []) if str(item).strip()]
    gate_revision_suggestions = [str(item).strip() for item in (gate_feedback_layer.get("revision_suggestions") or []) if str(item).strip()]
    context_compaction = payload.get("context_compaction", {}) or {}
    object_summaries = context_compaction.get("object_summaries", []) or []
    relation_matrix = context_compaction.get("relation_matrix", {}) or {}
    relation_findings = relation_matrix.get("relation_findings", []) or []
    product_rows = rows_by_dimension.get("商品") or rows_by_dimension.get("SKU") or []
    sku_rows = rows_by_dimension.get("SKU") or []
    category_rows = rows_by_dimension.get("品类") or []
    supplier_rows = rows_by_dimension.get("供应商") or []

    findings: list[dict[str, Any]] = []

    if "missing_object_split" in gate_issue_codes:
        findings.append(
            {
                "title": "对象层级拆分修复",
                "trigger_finding": "release gate 指出商品 / SKU / 卖家三层拆分不完整。",
                "deeper_read": "下一轮不能继续复写同一对象，而要把商品层写成经营主题，SKU 层写成规格差异，卖家层写成协同与履约质量。",
                "business_move": "正式报告里明确分成商品该推什么、SKU 该推哪一规格、卖家该保留还是修复三条动作线。",
                "evidence_refs": "release_gate / 商品经营影响评估 / SKU经营影响评估 / 供应商协同与履约评估",
            }
        )
    if "missing_supplier_relationship" in gate_issue_codes:
        findings.append(
            {
                "title": "供应商关系链修复",
                "trigger_finding": "release gate 指出供应商层缺少口碑与复购/单客产出的关系判断。",
                "deeper_read": "供应商层必须回答口碑和履约问题有没有开始压缩复购客户占比、客户覆盖和单客销售额，而不是停在评分和逾期率报表。",
                "business_move": "正式报告里把供应商动作改成保留、修复、降权、替换，并绑定到复购承接和单客产出变化。",
                "evidence_refs": "release_gate / 供应商协同与履约评估 / 履约与售后闭环",
            }
        )
    if "missing_sku_body" in gate_issue_codes:
        findings.append(
            {
                "title": "SKU 正文补齐",
                "trigger_finding": "release gate 指出 SKU 正文未形成独立经营动作。",
                "deeper_read": "SKU 层不该复写商品层总盘判断，而是要解释具体规格之间谁在放量、谁在拖累、谁在承接需求。",
                "business_move": "正式报告必须单列 SKU 头部、中位、尾部和对应动作，不再只把 SKU 当商品的附表。",
                "evidence_refs": "release_gate / SKU经营影响评估",
            }
        )

    if "missing_object_split" in gate_issue_codes:
        findings.append(
            {
                "title": "对象层级拆分修复",
                "trigger_finding": "release gate 指出商品 / SKU / 卖家三层拆分不完整。",
                "deeper_read": "下一轮不是重复头部对象，而是要把商品层写成经营主题，SKU 层写成规格差异，卖家层写成协同与履约质量。",
                "business_move": "正式报告里明确分成商品该推什么、SKU 该推哪一规格、卖家该保留还是修复三条动作线。",
                "evidence_refs": "release_gate / 商品经营影响评估 / SKU经营影响评估 / 供应商协同与履约评估",
            }
        )
    if "missing_supplier_relationship" in gate_issue_codes:
        findings.append(
            {
                "title": "供应商关系链修复",
                "trigger_finding": "release gate 指出供应商层缺少口碑与复购/单客产出的关系判断。",
                "deeper_read": "供应商层必须回答口碑和履约问题有没有开始压缩复购客户占比、客户覆盖和单客销售额，而不是停在评分和逾期率报表。",
                "business_move": "正式报告里把供应商动作改成保留、修复、降权、替换，并绑定到复购承接和单客产出变化。",
                "evidence_refs": "release_gate / 供应商协同与履约评估 / 履约与售后闭环",
            }
        )
    if "missing_sku_body" in gate_issue_codes:
        findings.append(
            {
                "title": "SKU 正文补齐",
                "trigger_finding": "release gate 指出 SKU 正文未形成独立经营动作。",
                "deeper_read": "SKU 层不该复写商品层总盘判断，而是要解释具体规格之间谁在放量、谁在拖累、谁在承接需求。",
                "business_move": "正式报告必须单列 SKU 头部、中位、尾部和对应动作，不再只把 SKU 当商品的附表。",
                "evidence_refs": "release_gate / SKU经营影响评估",
            }
        )

    head_row = next((row for row in product_rows if str(row.get("经营判断") or "") == "核心主推"), product_rows[0] if product_rows else None)
    if head_row:
        low_review = _parse_numberish(head_row.get("低分评价占比")) or 0.0
        late_rate = _parse_numberish(head_row.get("逾期率")) or 0.0
        repeat_rate = _parse_numberish(head_row.get("复购客户占比")) or 0.0
        if low_review >= 0.15 or late_rate >= 0.15:
            deeper_read = (
                f"`{head_row.get('对象')}` 虽然是销售头部，但低分评价占比 {head_row.get('低分评价占比', 'n/a')}、逾期率 {head_row.get('逾期率', 'n/a')}，"
                "说明它不是“放心放量”的主推款，而是“有量但要先修”的修复型头部。"
            )
            business_move = "主推预算和曝光不应直接放大，先拆差评词、逾期订单来源和卖家履约链路。"
        elif repeat_rate < 0.05:
            deeper_read = (
                f"`{head_row.get('对象')}` 当前总量领先，但复购客户占比仅 {head_row.get('复购客户占比', 'n/a')}，"
                "说明它更像一次性成交头部，而不是稳定复购头部。"
            )
            business_move = "继续拆新客成交和老客回流，不要把一次性放量误判成长期主推。"
        else:
            deeper_read = (
                f"`{head_row.get('对象')}` 同时拿住销售和复购承接，已经不是单纯样本内大单，而是更接近稳定经营头部。"
            )
            business_move = "优先复盘它与次头部对象的差异，沉淀成可复制的主推打法。"
        findings.append(
            {
                "title": "头部对象的二次拆解",
                "trigger_finding": f"`{head_row.get('对象')}` 当前经营判断为 `{head_row.get('经营判断', '待判断')}`。",
                "deeper_read": deeper_read,
                "business_move": business_move,
                "evidence_refs": "商品经营影响评估 / 履约与售后闭环",
            }
        )

    bridge_row = next(
        (
            row for row in product_rows
            if str(row.get("经营判断") or "") in {"桥梁候选", "主推兼承接"}
            and ((_parse_numberish(row.get("订单覆盖")) or 0) >= 30 or (_parse_numberish(row.get("客户覆盖")) or 0) >= 30)
        ),
        None,
    )
    if bridge_row:
        findings.append(
            {
                "title": "承接型对象与放量型对象分离",
                "trigger_finding": f"`{bridge_row.get('对象')}` 当前经营判断为 `{bridge_row.get('经营判断', '待判断')}`。",
                "deeper_read": (
                    f"`{bridge_row.get('对象')}` 的订单覆盖 {bridge_row.get('订单覆盖', 'n/a')}、客户覆盖 {bridge_row.get('客户覆盖', 'n/a')}，"
                    "说明它承担的是承接流量和接住需求的角色，不一定需要按头部销售额去管理。"
                ),
                "business_move": "把它从“要不要主推”改成“要不要做承接/搭售/连带成交”的经营问题。",
                "evidence_refs": "品类经营影响评估 / 商品经营影响评估",
            }
        )

    edge_risk_row = max(
        [
            row for row in product_rows
            if str(row.get("经营判断") or "") == "观察池"
        ],
        key=lambda row: _followup_row_score(row, weight_keys=["低分评价占比", "逾期率"]),
        default=None,
    )
    if edge_risk_row and _followup_row_score(edge_risk_row, weight_keys=["低分评价占比", "逾期率"]) > 0.25:
        findings.append(
            {
                "title": "边缘对象的止损线",
                "trigger_finding": f"`{edge_risk_row.get('对象')}` 当前仍在观察池。",
                "deeper_read": (
                    f"`{edge_risk_row.get('对象')}` 销售额占比仅 {edge_risk_row.get('销售额占比', 'n/a')}，"
                    f"但低分评价占比 {edge_risk_row.get('低分评价占比', 'n/a')}、逾期率 {edge_risk_row.get('逾期率', 'n/a')}。"
                    "这类对象不是“再观察一下”，而是已经接近止损或下架复核边界。"
                ),
                "business_move": "把它们从普通观察池单独拆成“高风险边缘池”，避免低基数风险对象继续扩散。 ",
                "evidence_refs": "商品经营影响评估 / SKU经营影响评估",
            }
        )

    if supplier_rows:
        sales_head = supplier_rows[0]
        customer_head = max(supplier_rows, key=lambda row: _parse_numberish(row.get("客户覆盖")) or float("-inf"))
        if customer_head.get("对象") != sales_head.get("对象"):
            findings.append(
                {
                    "title": "供应商层的双头部拆分",
                    "trigger_finding": f"销售贡献头部是 `{sales_head.get('对象')}`，客户承接头部是 `{customer_head.get('对象')}`。",
                    "deeper_read": (
                        f"`{sales_head.get('对象')}` 更像结果贡献头部，而 `{customer_head.get('对象')}` 客户覆盖 {customer_head.get('客户覆盖', 'n/a')}、"
                        f"订单覆盖 {customer_head.get('订单覆盖', 'n/a')}，更像平台承接头部。供应商层不该只有一张销售排行榜。"
                    ),
                    "business_move": "供应商考核要分成销售贡献、承接能力、履约稳定性三套口径，不再用单一销售额拍板。",
                    "evidence_refs": "供应商协同与履约评估",
                }
            )

    if category_rows:
        risky_category = max(
            category_rows,
            key=lambda row: _followup_row_score(row, weight_keys=["低分评价占比", "逾期率"]),
        )
        if risky_category and (_parse_numberish(risky_category.get("低分评价占比")) or 0) >= 0.1:
            findings.append(
                {
                    "title": "品类头部不等于可放量品类",
                    "trigger_finding": f"`{risky_category.get('对象')}` 当前是重点品类之一。",
                    "deeper_read": (
                        f"`{risky_category.get('对象')}` 当前销售额占比 {risky_category.get('销售额占比', 'n/a')}，"
                        f"但低分评价占比 {risky_category.get('低分评价占比', 'n/a')}、逾期率 {risky_category.get('逾期率', 'n/a')}。"
                        "说明品类扩张不能只看盘子，还要先看这个盘子是不是在用售后和履约问题换规模。"
                    ),
                    "business_move": "品类扩量前先拆品类内的高风险商品和卖家，不要把风险一并放大。",
                    "evidence_refs": "品类经营影响评估 / 供应商协同与履约评估",
                }
            )

    if len(findings) < 2 and object_summaries:
        for summary in object_summaries[:3]:
            dimension = str(summary.get("dimension") or "对象")
            head_summary = str(summary.get("head_summary") or "").strip()
            middle_summary = str(summary.get("middle_summary") or "").strip()
            tail_summary = str(summary.get("tail_summary") or "").strip()
            if not any([head_summary, middle_summary, tail_summary]):
                continue
            findings.append(
                {
                    "title": f"{dimension}层代表对象继续深挖",
                    "trigger_finding": head_summary or middle_summary or tail_summary,
                    "deeper_read": "这层不能只看头部，必须把头部、中位、底部一起放进同一张经营语境里，判断谁在贡献规模、谁在承接客户、谁在拖累效率。",
                    "business_move": "把同一维度的头中尾对象拉成对照组，优先确认中位承接层和底部风险层的动作边界。",
                    "evidence_refs": " / ".join(item for item in [head_summary, middle_summary, tail_summary] if item),
                }
            )
            if len(findings) >= 3:
                break

    if len(findings) < 3 and relation_findings:
        for item in relation_findings[:2]:
            text = str(item).strip()
            if not text:
                continue
            findings.append(
                {
                    "title": "关系矩阵继续深挖",
                    "trigger_finding": text,
                    "deeper_read": "这条关系不是描述性结论，而是下一轮对象级拆解入口，需要继续确认它影响的是复购、单客产出、客户承接还是履约风险。",
                    "business_move": "围绕这条关系继续追到具体对象和动作，不再停留在关系本身。",
                    "evidence_refs": "关系矩阵 / Context Compaction",
                }
            )
            if len(findings) >= 4:
                break

    if not findings:
        summary = payload.get("business_judgement_layer", {}) or {}
        findings.append(
            {
                "title": "继续深挖的默认入口",
                "trigger_finding": str(summary.get("management_summary") or "当前主报告已形成初步经营判断。"),
                "deeper_read": "下一轮不该再补一层摘要，而该围绕头部对象、承接对象和高风险边缘对象继续拆角色差异。",
                "business_move": "优先把主报告里已经点名的对象按头部/腰部/边缘和结果/承接/风险三条线继续深挖。",
                "evidence_refs": "业务判断层 / 管理层摘要",
            }
        )

    if semantic_followup_prompts:
        for item in semantic_followup_prompts[:3]:
            prompt = str(item.get("prompt") or "").strip()
            why = str(item.get("why") or "").strip()
            theme = str(item.get("theme") or "语义追问").strip()
            if not prompt:
                continue
            findings.append(
                {
                    "title": f"{theme}追问",
                    "trigger_finding": f"语义洞察已提示：{theme}",
                    "deeper_read": prompt,
                    "business_move": why or "把语义提示转成下一轮对象级复盘动作。",
                    "evidence_refs": "语义洞察展开",
                }
            )

    if gate_revision_suggestions:
        for suggestion in gate_revision_suggestions[:4]:
            if len(findings) >= 6:
                break
            findings.append(
                {
                    "title": "门禁回修任务",
                    "trigger_finding": "release gate 已给出明确修复要求。",
                    "deeper_read": suggestion,
                    "business_move": "把这条修复要求直接改写进正式正文，而不是继续留在门禁说明页。",
                    "evidence_refs": "release_gate",
                }
            )

    if gate_revision_suggestions:
        for suggestion in gate_revision_suggestions[:4]:
            if len(findings) >= 6:
                break
            findings.append(
                {
                    "title": "门禁回修任务",
                    "trigger_finding": "release gate 已给出明确修复要求。",
                    "deeper_read": suggestion,
                    "business_move": "把这条修复要求直接改写进正式正文，而不是继续留在门禁说明页。",
                    "evidence_refs": "release_gate",
                }
            )

    section_bullets = [str(item.get("deeper_read") or "").strip() for item in findings[:4] if str(item.get("deeper_read") or "").strip()]
    management_followups = [str(item.get("business_move") or "").strip() for item in findings[:4] if str(item.get("business_move") or "").strip()]
    return {
        "mode": "fallback",
        "reason": reason,
        "headline": "已在现有报告基础上继续往下挖一层，优先补足对象角色、结构矛盾和动作边界。",
        "section_bullets": section_bullets[:6],
        "drilldown_findings": findings[:6],
        "management_followups": management_followups[:6],
        "report_lens": report_lens,
    }


def codex_followup_mining(followup_context: dict[str, Any]) -> dict[str, Any]:
    system_prompt = (
        "You are Codex acting as a Follow-up Mining Agent. "
        "You must answer in Simplified Chinese and JSON only. "
        "You will receive the current report draft, business judgment, challenge output, semantic follow-up prompts, gate revision feedback, context_compaction, and structured rows for category/product/SKU/supplier when available. "
        "Your job is to continue digging based on already-written conclusions. "
        "Do not summarize the report again. Push one level deeper: identify the contradiction behind a head object, separate result leaders from承接 leaders, and mark stop-loss style edge objects. "
        "If semantic follow-up prompts are provided, treat them as mandatory drill-down tasks rather than optional notes. "
        "If gate revision feedback is provided, treat its revision suggestions as mandatory repair tasks for the next report draft. "
        "Return keys: headline, section_bullets, drilldown_findings, management_followups. "
        "drilldown_findings must be a list of 3 to 6 objects with keys: title, trigger_finding, deeper_read, business_move, evidence_refs. "
        "Each deeper_read must contain concrete business meaning, not generic advice."
    )
    tool_specs = [
        {
            "name": "lookup_followup_context",
            "description": "Read selected report, judgment, challenge, and structured-row fields before continuing the mining.",
            "parameters": {
                "type": "object",
                "properties": {"fields": {"type": "array", "items": {"type": "string"}}},
                "required": ["fields"],
                "additionalProperties": False,
            },
            "handler": lambda args: {
                key: followup_context.get(key)
                for key in [str(item) for item in args.get("fields", [])[:16]]
            },
        }
    ]
    return _request_codex_agentic_json(
        system_prompt=system_prompt,
        user_payload=followup_context,
        tool_specs=tool_specs,
        fallback_builder=_fallback_followup_mining,
    )


def _fallback_generic_deep_mining(reason: str, payload: dict[str, Any]) -> dict[str, Any]:
    context_compaction = payload.get("context_compaction", {}) or {}
    object_summaries = context_compaction.get("object_summaries", []) or []
    relation_findings = ((context_compaction.get("relation_matrix", {}) or {}).get("relation_findings", []) or [])[:8]
    category_rows = payload.get("category_rows", []) or []
    temporal_rows = payload.get("temporal_rows", []) or []
    correlation_rows = payload.get("correlation_rows", []) or []
    outlier_rows = payload.get("outlier_rows", []) or []

    findings: list[dict[str, Any]] = []

    if object_summaries:
        for summary in object_summaries[:3]:
            dimension = str(summary.get("dimension") or "对象")
            head_summary = str(summary.get("head_summary") or "").strip()
            middle_summary = str(summary.get("middle_summary") or "").strip()
            tail_summary = str(summary.get("tail_summary") or "").strip()
            evidence_refs = " / ".join(item for item in [head_summary, middle_summary, tail_summary] if item)
            if not evidence_refs:
                continue
            findings.append(
                {
                    "title": f"{dimension}层代表对象拆解",
                    "trigger_finding": head_summary or middle_summary or tail_summary,
                    "deeper_read": "这份数据即使暂时没有明确业务分类，也已经能从头部、中位、底部代表对象里看出结构分层，后续应围绕谁在拉动结果、谁在承接常态、谁在暴露边缘风险继续下钻。",
                    "business_move": "把这一维度的头中底对象拉成对照组，优先确认头部是否稳定、中位是否可复制、底部是否需要排除或单列。",
                    "evidence_refs": evidence_refs,
                }
            )

    if len(findings) < 4 and category_rows:
        head = category_rows[0]
        second = category_rows[1] if len(category_rows) > 1 else None
        trigger = f"`{head.get('category')}` 当前占比约 {_format_ratio_as_percent(head.get('share'))}。"
        if second:
            deeper_read = f"`{head.get('category')}` 不是简单的第一名，而是相对第二名 `{second.get('category')}` 已经拉开结构差距。这说明后续深挖不能平均铺开，而要先围绕结构头部与次头部的差异展开。"
        else:
            deeper_read = f"`{head.get('category')}` 当前已经是唯一显著切片，说明这份数据的结构入口很集中，后续应先从这条主切片继续往下挖。"
        findings.append(
            {
                "title": "结构切片深挖",
                "trigger_finding": trigger,
                "deeper_read": deeper_read,
                "business_move": "优先拆结构头部的组成、波动来源和异常值贡献，再决定是否扩展到其余切片。",
                "evidence_refs": "类别结构 / Context Compaction",
            }
        )

    if len(findings) < 5 and len(temporal_rows) >= 2:
        latest = temporal_rows[-1]
        previous = temporal_rows[-2]
        findings.append(
            {
                "title": "时间节奏深挖",
                "trigger_finding": f"`{latest.get('period')}` 相比 `{previous.get('period')}` 出现最新窗口变化。",
                "deeper_read": "无法分类的数据不代表没有节奏。当前应该先把最新窗口和上一窗口拆开，判断变化来自真实趋势、结构切换，还是异常记录集中出现。",
                "business_move": "先复核最新窗口的对象组成，再决定后续看趋势延续还是异常校正。",
                "evidence_refs": "时间趋势样本",
            }
        )

    if len(findings) < 6 and correlation_rows:
        top_corr = correlation_rows[0]
        findings.append(
            {
                "title": "指标联动深挖",
                "trigger_finding": f"`{top_corr.get('left')}` 与 `{top_corr.get('right')}` 当前相关系数 {float(top_corr.get('correlation') or 0.0):.3f}。",
                "deeper_read": "这说明至少有一条指标链是联动变化的。对于无法直接分类的数据，最稳妥的深挖入口不是先贴业务标签，而是先追这条联动链背后的共同驱动因子。",
                "business_move": "把这对指标放进同一条监控链，继续排查它们是口径重叠、共同驱动，还是异常共振。",
                "evidence_refs": "最高相关字段对",
            }
        )

    if len(findings) < 6 and outlier_rows:
        top_outlier = outlier_rows[0]
        findings.append(
            {
                "title": "异常字段深挖",
                "trigger_finding": f"`{top_outlier.get('column')}` 的异常占比约 {_format_ratio_as_percent(top_outlier.get('outlier_ratio'))}。",
                "deeper_read": "这意味着当前很多总量、均值和相关关系都有可能被少数异常记录带偏。对未知类别数据，先拆异常字段往往比先贴行业标签更有效。",
                "business_move": "先抽异常记录样本，确认是脏数据、极端事件还是确有业务异常，再决定是否保留进主叙事。",
                "evidence_refs": "数值异常概览",
            }
        )

    if len(findings) < 6 and relation_findings:
        for item in relation_findings[:2]:
            text = str(item).strip()
            if not text:
                continue
            findings.append(
                {
                    "title": "通用关系追问",
                    "trigger_finding": text,
                    "deeper_read": "这条关系已经足够成为下一轮深挖入口，不需要先完成业务归类才继续分析。",
                    "business_move": "围绕这条关系继续追到具体对象、具体窗口或具体异常字段。",
                    "evidence_refs": "通用关系矩阵",
                }
            )
            if len(findings) >= 6:
                break

    if not findings:
        findings.append(
            {
                "title": "通用深挖入口",
                "trigger_finding": "当前数据尚未形成稳定业务分类，但已经具备继续深挖的统计和结构线索。",
                "deeper_read": "下一轮应先从结构头部、时间变化、指标联动和异常字段四条线继续下钻，而不是停在分类命名上。",
                "business_move": "先按结构、时间、联动、异常四条线做对象级复盘，再决定是否需要更细业务建模。",
                "evidence_refs": "Context Compaction / 通用信号",
            }
        )

    section_bullets = [str(item.get("deeper_read") or "").strip() for item in findings[:4] if str(item.get("deeper_read") or "").strip()]
    management_followups = [str(item.get("business_move") or "").strip() for item in findings[:4] if str(item.get("business_move") or "").strip()]
    return {
        "mode": "fallback",
        "reason": reason,
        "headline": "已针对暂时无法清晰分类的数据直接启动通用深挖，不再等待业务标签先被识别出来。",
        "section_bullets": section_bullets[:6],
        "drilldown_findings": findings[:6],
        "management_followups": management_followups[:6],
    }


def codex_generic_deep_mining(generic_context: dict[str, Any]) -> dict[str, Any]:
    system_prompt = (
        "You are Codex acting as a Generic Deep Mining Agent. "
        "You must answer in Simplified Chinese and JSON only. "
        "You will receive a dataset report draft plus structural slices, temporal rows, correlation rows, outlier rows, relation findings, and context compaction. "
        "Do not try to classify the dataset into a named business domain first. "
        "Your job is to mine what can already be dug deeper directly from the data structure itself: head-vs-middle-vs-tail objects, time-window shifts, metric linkages, and anomaly-driven distortions. "
        "Return keys: headline, section_bullets, drilldown_findings, management_followups. "
        "drilldown_findings must be a list of 3 to 6 objects with keys: title, trigger_finding, deeper_read, business_move, evidence_refs. "
        "Each deeper_read must be concrete and must not depend on first naming the dataset category."
    )
    tool_specs = [
        {
            "name": "lookup_generic_mining_context",
            "description": "Read selected structural, temporal, correlation, anomaly, and report fields before generic deep mining.",
            "parameters": {
                "type": "object",
                "properties": {"fields": {"type": "array", "items": {"type": "string"}}},
                "required": ["fields"],
                "additionalProperties": False,
            },
            "handler": lambda args: {
                key: generic_context.get(key)
                for key in [str(item) for item in args.get("fields", [])[:16]]
            },
        }
    ]
    return _request_codex_agentic_json(
        system_prompt=system_prompt,
        user_payload=generic_context,
        tool_specs=tool_specs,
        fallback_builder=_fallback_generic_deep_mining,
    )


def _fallback_generic_structure_mining(reason: str, payload: dict[str, Any]) -> dict[str, Any]:
    context_compaction = payload.get("context_compaction", {}) or {}
    object_summaries = context_compaction.get("object_summaries", []) or []
    findings: list[str] = []
    head_objects: list[str] = []
    middle_objects: list[str] = []
    tail_objects: list[str] = []
    drilldown_prompts: list[str] = []

    for summary in object_summaries[:4]:
        dimension = str(summary.get("dimension") or "对象")
        head_summary = str(summary.get("head_summary") or "").strip()
        middle_summary = str(summary.get("middle_summary") or "").strip()
        tail_summary = str(summary.get("tail_summary") or "").strip()
        if head_summary:
            head_objects.append(head_summary)
            findings.append(f"{dimension}层头部对象已经出现，可直接作为第一优先切片继续拆。")
            drilldown_prompts.append(f"继续拆 `{dimension}` 层头部对象的组成、稳定性和是否只是少数样本拉动。")
        if middle_summary:
            middle_objects.append(middle_summary)
            findings.append(f"{dimension}层存在中位代表对象，说明这份数据不该只看头部。")
            drilldown_prompts.append(f"继续拆 `{dimension}` 层中位对象，判断它是承接常态、桥梁层还是普通噪音。")
        if tail_summary:
            tail_objects.append(tail_summary)
            findings.append(f"{dimension}层底部对象已经可识别，后续要单独判断是否属于风险边界。")
            drilldown_prompts.append(f"继续拆 `{dimension}` 层底部对象，确认是长尾自然现象还是需要单列清理的异常边缘。")
        if len(findings) >= 6:
            break

    return {
        "mode": "fallback",
        "reason": reason,
        "headline": "已先从对象分层结构里切出头部、中位、底部代表对象，不等待业务标签先被命名。",
        "structure_findings": _clean_fallback_lines(findings, limit=6),
        "head_objects": head_objects[:4],
        "middle_objects": middle_objects[:4],
        "tail_objects": tail_objects[:4],
        "drilldown_prompts": _clean_fallback_lines(drilldown_prompts, limit=6),
    }


def codex_generic_structure_mining(structure_context: dict[str, Any]) -> dict[str, Any]:
    system_prompt = (
        "You are Codex acting as a Generic Structure Mining Agent. "
        "You must answer in Simplified Chinese and JSON only. "
        "You will receive object summaries and compacted relation context for a dataset that may not fit any known business lens. "
        "Do not classify the business first. "
        "Your job is to identify head, middle, and tail objects worth further investigation. "
        "Return keys: headline, structure_findings, head_objects, middle_objects, tail_objects, drilldown_prompts."
    )
    tool_specs = [
        {
            "name": "lookup_generic_structure_context",
            "description": "Read selected object-summary and relation fields before mining structure.",
            "parameters": {
                "type": "object",
                "properties": {"fields": {"type": "array", "items": {"type": "string"}}},
                "required": ["fields"],
                "additionalProperties": False,
            },
            "handler": lambda args: {
                key: structure_context.get(key)
                for key in [str(item) for item in args.get("fields", [])[:14]]
            },
        }
    ]
    return _request_codex_agentic_json(
        system_prompt=system_prompt,
        user_payload=structure_context,
        tool_specs=tool_specs,
        fallback_builder=_fallback_generic_structure_mining,
    )


def _fallback_generic_pattern_mining(reason: str, payload: dict[str, Any]) -> dict[str, Any]:
    temporal_rows = payload.get("temporal_rows", []) or []
    correlation_rows = payload.get("correlation_rows", []) or []
    outlier_rows = payload.get("outlier_rows", []) or []
    findings: list[str] = []
    temporal_findings: list[str] = []
    linkage_findings: list[str] = []
    anomaly_findings: list[str] = []
    drilldown_prompts: list[str] = []

    if len(temporal_rows) >= 2:
        latest = temporal_rows[-1]
        previous = temporal_rows[-2]
        temporal_findings.append(f"最新窗口 `{latest.get('period')}` 相比 `{previous.get('period')}` 已有可解释变化。")
        drilldown_prompts.append("把最近两个时间窗口单独拆开，确认变化来自趋势延续、结构切换还是异常记录。")
    if correlation_rows:
        top_corr = correlation_rows[0]
        linkage_findings.append(
            f"`{top_corr.get('left')}` 与 `{top_corr.get('right')}` 当前相关系数 {float(top_corr.get('correlation') or 0.0):.3f}。"
        )
        drilldown_prompts.append("把最强相关指标放进同一条监控链，继续确认它们是共同驱动还是口径重叠。")
    if outlier_rows:
        top_outlier = outlier_rows[0]
        anomaly_findings.append(
            f"`{top_outlier.get('column')}` 的异常占比约 {_format_ratio_as_percent(top_outlier.get('outlier_ratio'))}。"
        )
        drilldown_prompts.append("先抽异常字段样本，确认是否会显著拉歪均值、总量和趋势判断。")

    findings.extend(temporal_findings[:2])
    findings.extend(linkage_findings[:2])
    findings.extend(anomaly_findings[:2])
    return {
        "mode": "fallback",
        "reason": reason,
        "headline": "已从时间、联动和异常三条线抽出可继续深挖的模式，不等待业务分类先完成。",
        "pattern_findings": _clean_fallback_lines(findings, limit=6),
        "temporal_findings": temporal_findings[:4],
        "linkage_findings": linkage_findings[:4],
        "anomaly_findings": anomaly_findings[:4],
        "drilldown_prompts": _clean_fallback_lines(drilldown_prompts, limit=6),
    }


def codex_generic_pattern_mining(pattern_context: dict[str, Any]) -> dict[str, Any]:
    system_prompt = (
        "You are Codex acting as a Generic Pattern Mining Agent. "
        "You must answer in Simplified Chinese and JSON only. "
        "You will receive temporal rows, correlation rows, outlier rows, and compact relation context. "
        "Do not classify the business first. "
        "Your job is to identify time shifts, metric linkages, and anomaly distortions worth deeper investigation. "
        "Return keys: headline, pattern_findings, temporal_findings, linkage_findings, anomaly_findings, drilldown_prompts."
    )
    tool_specs = [
        {
            "name": "lookup_generic_pattern_context",
            "description": "Read selected temporal, correlation, anomaly, and relation fields before mining patterns.",
            "parameters": {
                "type": "object",
                "properties": {"fields": {"type": "array", "items": {"type": "string"}}},
                "required": ["fields"],
                "additionalProperties": False,
            },
            "handler": lambda args: {
                key: pattern_context.get(key)
                for key in [str(item) for item in args.get("fields", [])[:14]]
            },
        }
    ]
    return _request_codex_agentic_json(
        system_prompt=system_prompt,
        user_payload=pattern_context,
        tool_specs=tool_specs,
        fallback_builder=_fallback_generic_pattern_mining,
    )


def _fallback_generic_chain_polish(reason: str, payload: dict[str, Any]) -> dict[str, Any]:
    mining_layer = payload.get("generic_deep_mining_layer", {}) or {}
    structure_layer = payload.get("structure_agent_layer", {}) or {}
    pattern_layer = payload.get("pattern_agent_layer", {}) or {}

    bullets = _clean_fallback_lines(
        [
            *(mining_layer.get("section_bullets") or [])[:4],
            *(structure_layer.get("structure_findings") or [])[:3],
            *(pattern_layer.get("pattern_findings") or [])[:3],
        ],
        limit=6,
    )
    findings = (mining_layer.get("drilldown_findings") or [])[:6]
    management_followups = _clean_fallback_lines(
        [
            *(mining_layer.get("management_followups") or [])[:4],
            *(structure_layer.get("drilldown_prompts") or [])[:3],
            *(pattern_layer.get("drilldown_prompts") or [])[:3],
        ],
        limit=6,
    )
    return {
        "mode": "fallback",
        "reason": reason,
        "headline": "已把通用深挖结果压成可直接进入正文的链条，不再停留在结构信号堆叠。",
        "section_bullets": bullets[:6],
        "drilldown_findings": findings,
        "management_followups": management_followups[:6],
    }


def codex_generic_chain_polish(polish_context: dict[str, Any]) -> dict[str, Any]:
    system_prompt = (
        "You are Codex acting as a Generic Deep-Mining Polish Agent. "
        "You must answer in Simplified Chinese and JSON only. "
        "You will receive outputs from a background-understanding agent, a structure-mining agent, a pattern-mining agent, and a generic deep-mining agent. "
        "Your job is to merge them into one sharp deep-mining section for the main report. "
        "Return keys: headline, section_bullets, drilldown_findings, management_followups."
    )
    tool_specs = [
        {
            "name": "lookup_generic_polish_context",
            "description": "Read selected generic-agent outputs before polishing them into one section.",
            "parameters": {
                "type": "object",
                "properties": {"fields": {"type": "array", "items": {"type": "string"}}},
                "required": ["fields"],
                "additionalProperties": False,
            },
            "handler": lambda args: {
                key: polish_context.get(key)
                for key in [str(item) for item in args.get("fields", [])[:16]]
            },
        }
    ]
    return _request_codex_agentic_json(
        system_prompt=system_prompt,
        user_payload=polish_context,
        tool_specs=tool_specs,
        fallback_builder=_fallback_generic_chain_polish,
    )


def _fallback_generic_chain_judge(reason: str, payload: dict[str, Any]) -> dict[str, Any]:
    background = payload.get("background_understanding_agent", {}) or {}
    structure = payload.get("structure_mining_agent", {}) or {}
    pattern = payload.get("pattern_mining_agent", {}) or {}
    mining = payload.get("generic_deep_mining_agent", {}) or {}
    polish = payload.get("polish_agent", {}) or {}

    score = 78
    strengths: list[str] = []
    weaknesses: list[str] = []
    improvements: list[str] = []
    route_to: list[str] = []

    autofilled = background.get("autofilled_fields") or []
    if background.get("completed_problem_to_solve") or background.get("completed_core_purpose"):
        strengths.append("背景理解 agent 已把问题、目的和约束补成可执行输入。")
        score += 4
    else:
        weaknesses.append("背景理解 agent 还没有把数据背景翻成可执行分析任务。")
        improvements.append("先补清 observation unit、核心问题和预期交付，再继续后续 agent。")
        route_to.append("background_understanding_agent")
        score -= 8

    if len(structure.get("structure_findings") or []) >= 3:
        strengths.append("结构 agent 已经拆出头部、中位、底部或其他代表对象。")
        score += 4
    else:
        weaknesses.append("结构 agent 还没有稳定拆出可继续深挖的代表对象。")
        improvements.append("继续强化对象分层，至少拉出头部、中位和边缘对象。")
        route_to.append("structure_mining_agent")
        score -= 8

    pattern_hits = sum(
        1
        for key in ["temporal_findings", "linkage_findings", "anomaly_findings"]
        if len(pattern.get(key) or []) > 0
    )
    if pattern_hits >= 2:
        strengths.append("模式 agent 已从时间、联动、异常里抽出可下钻线索。")
        score += 4
    else:
        weaknesses.append("模式 agent 还没有形成足够的时间/联动/异常深挖线索。")
        improvements.append("补足时间变化、指标联动和异常字段三条线里的至少两条。")
        route_to.append("pattern_mining_agent")
        score -= 8

    if len(mining.get("drilldown_findings") or []) >= 4:
        strengths.append("通用深挖 agent 已形成足够具体的 drilldown 结论。")
        score += 5
    else:
        weaknesses.append("通用深挖 agent 仍然偏薄，无法支撑深度分析正文。")
        improvements.append("继续把代表对象、时间窗口和异常字段串成对象级结论。")
        route_to.append("generic_deep_mining_agent")
        score -= 10

    if len(polish.get("section_bullets") or []) >= 3 and len(polish.get("drilldown_findings") or []) >= 3:
        strengths.append("润色 agent 已把多 agent 结果收束成可交付段落。")
        score += 4
    else:
        weaknesses.append("润色 agent 还没有把多 agent 输出压成清晰正文。")
        improvements.append("继续压缩和重排 deep-mining 结果，避免像并列素材堆叠。")
        route_to.append("polish_agent")
        score -= 8

    route_to = [item for item in route_to if item]
    verdict = "pass" if score >= 90 and not route_to else "block"
    if not improvements:
        improvements.append("继续扩大对象层、中位层和异常层的证据密度，把分数推到 90+。")
    return {
        "mode": "fallback",
        "reason": reason,
        "total_score": max(0, min(100, int(score))),
        "threshold": 90,
        "target_score": 90,
        "verdict": verdict,
        "strengths": strengths[:6],
        "weaknesses": weaknesses[:6],
        "improvement_actions": improvements[:6],
        "route_to": route_to[:5],
        "brief_rationale": f"通用 deep-mining agent 链以 90 分为放行线；当前得分 {max(0, min(100, int(score)))}。",
    }


def codex_generic_chain_judge(judge_context: dict[str, Any]) -> dict[str, Any]:
    system_prompt = (
        "You are CodexJudge acting as the final reviewer for a generic deep-mining agent chain. "
        "You must answer in Simplified Chinese and JSON only. "
        "You will receive outputs from: background_understanding_agent, structure_mining_agent, pattern_mining_agent, generic_deep_mining_agent, and polish_agent. "
        "Score the chain as a management-facing deep-mining workflow for data that cannot be cleanly classified yet. "
        "Return keys: total_score, threshold, target_score, verdict, strengths, weaknesses, improvement_actions, route_to, brief_rationale. "
        "threshold must be 90. target_score must be 90. verdict must be pass or block. "
        "If score is below 90, route_to must name which agent(s) should be rerun."
    )
    tool_specs = [
        {
            "name": "lookup_generic_chain_judge_context",
            "description": "Read selected generic-agent outputs before scoring the chain.",
            "parameters": {
                "type": "object",
                "properties": {"fields": {"type": "array", "items": {"type": "string"}}},
                "required": ["fields"],
                "additionalProperties": False,
            },
            "handler": lambda args: {
                key: judge_context.get(key)
                for key in [str(item) for item in args.get("fields", [])[:16]]
            },
        }
    ]
    return _request_codex_agentic_json(
        system_prompt=system_prompt,
        user_payload=judge_context,
        tool_specs=tool_specs,
        fallback_builder=_fallback_generic_chain_judge,
    )


def _fallback_challenge_review(reason: str, payload: dict[str, Any]) -> dict[str, Any]:
    insight_layer = payload.get("insight_mining_layer", {}) or {}
    challenge_points: list[dict[str, Any]] = []
    for item in (insight_layer.get("important_findings") or [])[:4]:
        text = str(item)
        issue_type = "overreach" if "优先" in text or "领先" in text else "boundary"
        challenge_points.append(
            {
                "claim": text,
                "challenge": "当前结论需要继续区分它是总量领先、效率领先，还是仅仅口径联动。",
                "issue_type": issue_type,
                "severity": "medium",
                "route_hint": "business_synthesis" if issue_type == "overreach" else "decision_design",
            }
        )
    return {
        "mode": "fallback",
        "reason": reason,
        "headline": "已对洞察层做反证审视，避免把样本内现象直接写成强结论。",
        "challenge_points": challenge_points,
        "counter_arguments": [item["challenge"] for item in challenge_points[:4]],
        "boundary_alerts": [str(item) for item in (payload.get("evidence_digest_layer", {}) or {}).get("key_boundaries", [])[:4]],
        "unresolved_gaps": ["若缺少成本、归因窗口、cohort 或因果设计，报告只能做样本内判断。"],
    }


def codex_challenge_review(challenge_context: dict[str, Any]) -> dict[str, Any]:
    system_prompt = (
        "You are Codex acting as a Challenge Agent. "
        "You must answer in Simplified Chinese and JSON only. "
        "You will receive evidence digest and mined insights. "
        "Your job is to challenge over-interpretation, surface counter-arguments, and mark causal or sample boundaries. "
        "Return keys: headline, challenge_points, counter_arguments, boundary_alerts, unresolved_gaps. "
        "challenge_points must contain objects with keys: claim, challenge, issue_type, severity, route_hint. "
        "This layer must actively disagree when needed; do not turn it into generic caution text."
    )
    tool_specs = [
        {
            "name": "lookup_challenge_context",
            "description": "Read selected digest and insight fields before challenging them.",
            "parameters": {
                "type": "object",
                "properties": {"fields": {"type": "array", "items": {"type": "string"}}},
                "required": ["fields"],
                "additionalProperties": False,
            },
            "handler": lambda args: {
                key: challenge_context.get(key)
                for key in [str(item) for item in args.get("fields", [])[:14]]
            },
        }
    ]
    return _request_codex_agentic_json(
        system_prompt=system_prompt,
        user_payload=challenge_context,
        tool_specs=tool_specs,
        fallback_builder=_fallback_challenge_review,
    )


def _fallback_business_synthesis(reason: str, payload: dict[str, Any]) -> dict[str, Any]:
    request = payload.get("request", {}) or {}
    background = payload.get("business_background_layer", {}) or {}
    insights = payload.get("insight_mining_layer", {}) or {}
    evidence = payload.get("evidence_digest_layer", {}) or {}
    challenge = payload.get("challenge_layer", {}) or {}
    relation_context = payload.get("relation_context", {}) or {}
    report_lens = str(payload.get("report_lens") or "")
    fusion_enabled = _is_procurement_sales_management_fusion_payload(payload)
    product_rows = payload.get("product_rows") or []
    sku_rows = payload.get("sku_rows") or []
    category_rows = payload.get("category_rows") or []
    supplier_rows = payload.get("supplier_rows") or []
    gate_feedback_layer = payload.get("gate_feedback_layer", {}) or {}
    gate_issue_codes = [str(item).strip() for item in (gate_feedback_layer.get("issue_codes") or []) if str(item).strip()]
    gate_revision_suggestions = [str(item).strip() for item in (gate_feedback_layer.get("revision_suggestions") or []) if str(item).strip()]
    core_purpose = str(request.get("core_purpose") or request.get("problem_to_solve") or "当前业务判断")
    judgement_points = _clean_fallback_lines(
        [*(relation_context.get("relation_findings") or []), *(insights.get("important_findings") or []), *(evidence.get("priority_evidence") or [])],
        require_result_signal=True,
        limit=5,
    )
    if report_lens in {"management_accounting_review", "procurement_sales_review"} and len(judgement_points) < 3:
        key_slices = [str(item) for item in (evidence.get("key_slices") or [])[:3] if str(item).strip()]
        key_anomalies = [str(item) for item in (evidence.get("key_anomalies") or [])[:3] if str(item).strip()]
        key_metrics = [str(item) for item in (evidence.get("key_metrics") or [])[:3] if str(item).strip()]
        for item in key_slices:
            text = f"优先围绕 `{item}` 做第一轮集中度与责任归属排查，确认是否存在单一对象或单一年度过度集中。"
            if text not in judgement_points:
                judgement_points.append(text)
            if len(judgement_points) >= 3:
                break
        if len(judgement_points) < 3:
            for item in key_anomalies:
                text = f"先复核 `{item}` 对应的异常记录，再决定是否进入预算控制、付款节奏修正或合同排查。"
                if text not in judgement_points:
                    judgement_points.append(text)
                if len(judgement_points) >= 3:
                    break
        if len(judgement_points) < 3:
            for item in key_metrics:
                text = f"围绕 `{item}` 先做大额支出与头部对象复核，避免管理结论停留在结构描述层。"
                if text not in judgement_points:
                    judgement_points.append(text)
                if len(judgement_points) >= 3:
                    break
    if report_lens == "procurement_sales_review":
        if "missing_object_split" in gate_issue_codes and "这轮正式正文必须把商品、SKU、卖家三层动作拆开写，不能继续把同一对象放在不同层复写。" not in judgement_points:
            judgement_points.append("这轮正式正文必须把商品、SKU、卖家三层动作拆开写，不能继续把同一对象放在不同层复写。")
        if "missing_supplier_relationship" in gate_issue_codes and "这轮供应商判断必须直接回答口碑和履约问题有没有开始压缩复购客户占比、客户覆盖和单客销售额。" not in judgement_points:
            judgement_points.append("这轮供应商判断必须直接回答口碑和履约问题有没有开始压缩复购客户占比、客户覆盖和单客销售额。")
        if "missing_sku_body" in gate_issue_codes and "这轮 SKU 层必须单列头部、中位、尾部规格对象和对应动作，不再把 SKU 当成商品层附表。" not in judgement_points:
            judgement_points.append("这轮 SKU 层必须单列头部、中位、尾部规格对象和对应动作，不再把 SKU 当成商品层附表。")
        for row in product_rows[:2]:
            text = f"`{row.get('对象', '头部商品')}` 当前销售额 {row.get('销售额总量', 'n/a')}、订单覆盖 {row.get('订单覆盖', 'n/a')}、客户覆盖 {row.get('客户覆盖', 'n/a')}，应先判断它是稳健主推，还是被售后与履约问题拖住。"
            if text not in judgement_points:
                judgement_points.append(text)
            if len(judgement_points) >= 3:
                break
        if len(judgement_points) < 4:
            for row in supplier_rows[:2]:
                text = f"`{row.get('对象', '头部卖家')}` 当前逾期率 {row.get('逾期率', 'n/a')}、低分评价占比 {row.get('低分评价占比', 'n/a')}，卖家判断必须同时看销售贡献、履约和口碑。"
                if text not in judgement_points:
                    judgement_points.append(text)
                if len(judgement_points) >= 4:
                    break
    if report_lens in {"management_accounting_review", "procurement_sales_review"} and fusion_enabled:
        for row in (product_rows or sku_rows or category_rows)[:3]:
            text = (
                f"`{row.get('对象', '头部对象')}` 当前销售额 {row.get('销售额总量', 'n/a')}、订单覆盖 {row.get('订单覆盖', 'n/a')}、客户覆盖 {row.get('客户覆盖', 'n/a')}，应和采购/预算投入一起判断有没有真正转成销售承接。"
            )
            if text not in judgement_points:
                judgement_points.append(text)
            if len(judgement_points) >= 4:
                break
    strategic_implications = _clean_fallback_lines(
        [*(challenge.get("boundary_alerts") or []), *(challenge.get("unresolved_gaps") or [])],
        limit=4,
    )
    if judgement_points:
        management_summary = judgement_points[0]
    elif strategic_implications:
        management_summary = strategic_implications[0]
    else:
        management_summary = f"当前更适合先围绕 `{core_purpose}` 收缩可执行结论，再决定哪些对象值得进入资源动作。"
    if core_purpose and core_purpose not in management_summary:
        management_summary = f"围绕{core_purpose}，{management_summary}"

    focus_decisions = {
        "sales_review": [
            "哪些对象值得优先进入主推或桥梁名单",
            "哪些对象当前只能继续观察而不能直接下资源动作",
            "哪些结论要等补字段或补验证后才能拍板",
        ],
        "management_accounting_review": [
            "哪些供应商、合同或支出对象值得优先排查",
            "哪些预算或采购信号已经足够支持控制动作",
            "哪些结论仍需补口径、补时间或补责任归属",
        ],
        "procurement_sales_review": [
            "哪些商品、SKU和卖家值得优先进入主推或修复名单",
            "哪些履约、售后或口碑信号已经足够支持调整采销动作",
            "哪些结论仍需补采购成本、库存或更长周期数据才能拍板",
        ],
        "media_review": [
            "哪些投放对象值得优先保留或修复",
            "哪些对象只能继续观察而不能直接放量",
            "哪些动作要等口径和时间边界稳定后再推进",
        ],
        "internet_ops_review": [
            "哪些渠道、活动或内容值得优先进入增长动作",
            "哪些对象当前只能继续观察而不能直接扩量",
            "哪些结论要等补验证后才能拍板",
        ],
    }.get(
        report_lens,
        [
            "哪些对象值得优先进入复盘名单",
            "哪些对象当前只能继续观察而不能直接下资源动作",
            "哪些结论要等补字段或补验证后才能拍板",
        ],
    )
    if report_lens == "procurement_sales_review":
        focus_decisions = [
            "哪些商品值得继续主推，哪些只是总量大但售后或履约已经在拖后腿",
            "哪些卖家需要优先修复履约和口碑，而不是继续只按销售贡献合作",
            "哪些品类该扩、该收、该调结构，依据分别是什么",
        ]
    elif report_lens in {"management_accounting_review", "procurement_sales_review"} and fusion_enabled:
        focus_decisions = [
            "哪些责任主体或采购投入已经真正转成商品/SKU销售承接",
            "哪些头部商品卖得动但正在吞噬库存、退货或资金占用",
            "哪些预算、采购或库存动作应该直接跟着商品经营结果一起调整",
        ]
    for item in gate_revision_suggestions[:3]:
        if item and item not in strategic_implications and item not in judgement_points:
            strategic_implications.append(item)
    return {
        "mode": "fallback",
        "reason": reason,
        "report_lens": report_lens,
        "management_summary": management_summary,
        "judgement_points": judgement_points[:5],
        "strategic_implications": strategic_implications[:5],
        "focus_decisions": focus_decisions[:5],
    }


def codex_business_synthesis(synthesis_context: dict[str, Any]) -> dict[str, Any]:
    system_prompt = (
        "You are Codex acting as a Business Synthesis Agent. "
        "You must answer in Simplified Chinese and JSON only. "
        "You will receive the evidence digest, insight mining layer, challenge layer, business background, user requirements, optionally historical template signals, and optionally release-gate revision feedback. "
        "Do not rerun analysis. Your job is to produce business judgment. "
        "Return keys: management_summary, judgement_points, strategic_implications, focus_decisions. "
        "All list fields must contain 3 to 5 concise Chinese strings. "
        "This layer answers what the analysis means for the actual business decision, after absorbing the challenge layer. "
        "If release-gate revision feedback is provided, treat its revision suggestions as mandatory repair goals for the next draft."
    )
    tool_specs = [
        {
            "name": "lookup_synthesis_context",
            "description": "Read selected prior-layer fields before writing business judgment.",
            "parameters": {
                "type": "object",
                "properties": {"fields": {"type": "array", "items": {"type": "string"}}},
                "required": ["fields"],
                "additionalProperties": False,
            },
            "handler": lambda args: {
                key: synthesis_context.get(key)
                for key in [str(item) for item in args.get("fields", [])[:16]]
            },
        }
    ]
    return _request_codex_agentic_json(
        system_prompt=system_prompt,
        user_payload=synthesis_context,
        tool_specs=tool_specs,
        fallback_builder=_fallback_business_synthesis,
    )


def _fallback_decision_design(reason: str, payload: dict[str, Any]) -> dict[str, Any]:
    business = payload.get("business_judgement_layer", {}) or {}
    challenge = payload.get("challenge_layer", {}) or {}
    judgement_points = [str(item) for item in (business.get("judgement_points") or [])[:3] if str(item).strip()]
    priority_actions = []
    for index, point in enumerate(judgement_points, start=1):
        priority_actions.append(
            {
                "priority": f"P{index}",
                "action": point,
                "rationale": "它当前同时影响业务判断和后续资源动作。",
                "sequence": index,
                "expected_signal": "下一轮验证里应出现更清晰的对象差异或边界收缩。",
            }
        )
    return {
        "mode": "fallback",
        "reason": reason,
        "decision_headline": "已把业务判断翻成带优先级的决策路线。",
        "priority_actions": priority_actions[:5],
        "scenario_options": [str(item) for item in (business.get("strategic_implications") or [])[:3] if str(item).strip()],
        "validation_agenda": [str(item) for item in (challenge.get("unresolved_gaps") or [])[:3] if str(item).strip()],
        "management_questions": [str(item) for item in (business.get("focus_decisions") or [])[:3] if str(item).strip()],
    }


def codex_decision_design(decision_context: dict[str, Any]) -> dict[str, Any]:
    system_prompt = (
        "You are Codex acting as a Decision Design Agent. "
        "You must answer in Simplified Chinese and JSON only. "
        "You will receive business judgment plus challenge output. "
        "Do not redo analysis. Your job is to turn judgments into priority, sequence, scenarios, and validation agenda. "
        "Return keys: decision_headline, priority_actions, scenario_options, validation_agenda, management_questions. "
        "priority_actions must be a list of objects with keys: priority, action, rationale, sequence, expected_signal. "
        "Do not output a generic bullet list; the layer must encode execution order and why each action is ahead of the next."
    )
    tool_specs = [
        {
            "name": "lookup_decision_context",
            "description": "Read selected business-judgment and challenge fields before designing decisions.",
            "parameters": {
                "type": "object",
                "properties": {"fields": {"type": "array", "items": {"type": "string"}}},
                "required": ["fields"],
                "additionalProperties": False,
            },
            "handler": lambda args: {
                key: decision_context.get(key)
                for key in [str(item) for item in args.get("fields", [])[:14]]
            },
        }
    ]
    return _request_codex_agentic_json(
        system_prompt=system_prompt,
        user_payload=decision_context,
        tool_specs=tool_specs,
        fallback_builder=_fallback_decision_design,
    )


def _fallback_final_polish(reason: str, payload: dict[str, Any]) -> dict[str, Any]:
    business = payload.get("business_judgement_layer", {}) or {}
    decision = payload.get("decision_design_layer", {}) or {}
    gate_feedback = payload.get("gate_feedback_layer", {}) or {}
    anti_generic = payload.get("anti_generic_layer", {}) or {}
    report_lens = str(payload.get("report_lens") or "")
    gate_suggestions = [str(item).strip() for item in (gate_feedback.get("revision_suggestions") or []) if str(item).strip()]
    anti_generic_rewrites = [str(item).strip() for item in (anti_generic.get("rewrite_instructions") or []) if str(item).strip()]
    internal_markers = (
        "analysis_program",
        "decision_summary",
        "action_roadmap",
        "quality",
        "必须删掉空话",
        "改成对象、指标、动作",
        "元叙述",
        "过程化表述",
        "section_id",
    )

    def _is_internal_instruction(text: str) -> bool:
        normalized = str(text or "").strip()
        return any(marker in normalized for marker in internal_markers)

    visible_gate_suggestions = [item for item in gate_suggestions if not _is_internal_instruction(item)]
    visible_rewrites = [item for item in anti_generic_rewrites if not _is_internal_instruction(item)]
    executive_summary = [str(business.get("management_summary") or "").strip()]
    executive_summary.extend(str(item).strip() for item in (business.get("judgement_points") or [])[:2] if str(item).strip())
    executive_summary.extend(str(item.get("action") or "").strip() for item in (decision.get("priority_actions") or [])[:2] if str(item.get("action") or "").strip())
    executive_summary.extend(visible_gate_suggestions[:2])
    executive_summary.extend(visible_rewrites[:2])
    section_overrides = []
    if report_lens != "procurement_sales_review":
        section_overrides.append(
            {
                "section_id": "decision_summary",
                "summary": str(business.get("management_summary") or ""),
                "bullets": [str(item) for item in (business.get("judgement_points") or [])[:4]] + visible_gate_suggestions[:2] + visible_rewrites[:2],
            }
        )
    section_overrides.append(
        {
            "section_id": "action_roadmap",
            "summary": str(decision.get("decision_headline") or ""),
            "bullets": [str(item.get("action") or "") for item in (decision.get("priority_actions") or [])[:4] if str(item.get("action") or "").strip()] + visible_gate_suggestions[:3] + visible_rewrites[:2],
        }
    )
    anti_generic_overrides = [item for item in (anti_generic.get("section_overrides") or []) if isinstance(item, dict)]
    if report_lens == "procurement_sales_review":
        anti_generic_overrides = [item for item in anti_generic_overrides if str(item.get("section_id") or "") != "decision_summary"]
    return {
        "mode": "fallback",
        "reason": reason,
        "polished_executive_summary": [item for item in executive_summary if item][:6],
        "narrative_upgrades": ([str(item) for item in (decision.get("scenario_options") or [])[:3] if str(item).strip()] + visible_gate_suggestions[:3] + visible_rewrites[:3])[:6],
        "section_overrides": section_overrides + anti_generic_overrides[:8],
    }


def _fallback_anti_generic_review(reason: str, payload: dict[str, Any]) -> dict[str, Any]:
    current_report = payload.get("current_report", {}) or {}
    executive_summary = [str(item).strip() for item in (current_report.get("executive_summary") or []) if str(item).strip()]
    sections = current_report.get("section_summaries") or []
    gate_feedback = payload.get("gate_feedback_layer", {}) or {}
    rewrite_instructions: list[str] = []
    generic_findings: list[str] = []
    section_overrides: list[dict[str, Any]] = []
    executive_summary_overrides: list[str] = []

    generic_markers = [
        "先做", "先看", "当前更适合", "报告越长", "不能只看", "应优先", "管理层要先", "后续要先",
        "更适合", "这一层", "这部分不只是", "当前任务", "越要先", "先把口径讲清", "观察一下",
        "建议先", "优先围绕", "先围绕", "这份报告当前最该", "更像一份", "当前要先",
    ]
    result_tokens = ["`", "%", "订单", "客户", "销售额", "复购", "逾期", "评价", "ROI", "预算", "库存", "毛利", "收入", "支出", "销量", "类目", "SKU", "卖家"]

    for item in executive_summary:
        has_concrete_signal = any(token in item for token in result_tokens)
        if any(marker in item for marker in generic_markers) and not has_concrete_signal:
            generic_findings.append("管理层摘要里仍有空话或过程化句子。")
            rewrite_instructions.append("管理层摘要必须只保留对象、指标、动作，不再出现过程话。")
        else:
            executive_summary_overrides.append(item)

    for section in sections[:24]:
        section_id = str(section.get("id") or "").strip()
        section_summary = str(section.get("summary") or "").strip()
        bullets = [str(item).strip() for item in (section.get("bullets") or []) if str(item).strip()]
        if not section_id or (not bullets and not section_summary):
            continue

        kept: list[str] = []
        removed: list[str] = []
        summary_override = section_summary
        has_concrete_summary = any(token in section_summary for token in result_tokens)
        if section_summary and any(marker in section_summary for marker in generic_markers) and not has_concrete_summary:
            generic_findings.append(f"`{section_id}` 的摘要仍偏泛化。")
            rewrite_instructions.append(f"`{section_id}` 的摘要必须改成对象级经营判断，不要写元叙述。")
            summary_override = ""
        for bullet in bullets:
            has_concrete_signal = any(token in bullet for token in result_tokens)
            if any(marker in bullet for marker in generic_markers) and not has_concrete_signal:
                removed.append(bullet)
            else:
                kept.append(bullet)

        if removed or (section_summary and not summary_override):
            generic_findings.append(f"`{section_id}` 存在 {len(removed)} 条泛化或过程化表述。")
            rewrite_instructions.append(f"`{section_id}` 必须删掉空话，改成对象、指标、动作三件事写法。")
            if kept or summary_override:
                section_overrides.append(
                    {
                        "section_id": section_id,
                        "summary": summary_override or (kept[0] if kept else str(section.get("summary") or "")),
                        "bullets": kept[:6],
                    }
                )

    for item in [str(x).strip() for x in (gate_feedback.get("revision_suggestions") or []) if str(x).strip()]:
        if item not in rewrite_instructions:
            rewrite_instructions.append(item)

    if not generic_findings:
        generic_findings.append("当前主报告未发现明显的大面空话，后续重点是继续压缩重复表述。")
    if not rewrite_instructions:
        rewrite_instructions.append("把没有对象、没有指标、没有动作的句子继续删掉或重写。")

    return {
        "mode": "fallback",
        "reason": reason,
        "headline": "已对主报告做反泛化巡检，目标是把空话、元叙述和重复句挡在正式版之外。",
        "generic_findings": generic_findings[:8],
        "rewrite_instructions": rewrite_instructions[:8],
        "executive_summary_overrides": executive_summary_overrides[:6],
        "section_overrides": section_overrides[:10],
    }


def codex_anti_generic_review(review_context: dict[str, Any]) -> dict[str, Any]:
    system_prompt = (
        "You are Codex acting as an Anti-Generic Review Agent for a management-facing analytical report. "
        "You must answer in Simplified Chinese and JSON only. "
        "Your job is to identify generic, meta, repetitive, or process-heavy statements in the main report draft, "
        "then produce concrete rewrite guidance and section-level overrides. "
        "Return keys: headline, generic_findings, rewrite_instructions, section_overrides. "
        "section_overrides must contain objects with keys: section_id, summary, bullets. "
        "Do not add new unsupported facts. Remove or rewrite generic language into object-level, metric-level, action-level expressions."
    )
    tool_specs = [
        {
            "name": "lookup_anti_generic_context",
            "description": "Read selected report, business judgment, decision design, and gate-feedback fields before anti-generic review.",
            "parameters": {
                "type": "object",
                "properties": {"fields": {"type": "array", "items": {"type": "string"}}},
                "required": ["fields"],
                "additionalProperties": False,
            },
            "handler": lambda args: {
                key: review_context.get(key)
                for key in [str(item) for item in args.get("fields", [])[:16]]
            },
        }
    ]
    return _request_codex_agentic_json(
        system_prompt=system_prompt,
        user_payload=review_context,
        tool_specs=tool_specs,
        fallback_builder=_fallback_anti_generic_review,
    )


def codex_final_polish(polish_context: dict[str, Any]) -> dict[str, Any]:
    system_prompt = (
        "You are Codex acting as a Final Polish Agent. "
        "You must answer in Simplified Chinese and JSON only. "
        "You will receive business judgment, decision design, challenge output, release-gate revision feedback, and the current report draft. "
        "You are only allowed to optimize structure, sharpness, readability, and executive rhythm. "
        "Do not change evidence meaning or invent new judgments. "
        "Return keys: polished_executive_summary, narrative_upgrades, section_overrides. "
        "If release-gate revision feedback is provided, you must actively repair the targeted weaknesses instead of only smoothing language. "
        "section_overrides must contain objects with keys: section_id, summary, bullets."
    )
    tool_specs = [
        {
            "name": "lookup_polish_context",
            "description": "Read selected business, decision, challenge, and report-draft fields before polishing.",
            "parameters": {
                "type": "object",
                "properties": {"fields": {"type": "array", "items": {"type": "string"}}},
                "required": ["fields"],
                "additionalProperties": False,
            },
            "handler": lambda args: {
                key: polish_context.get(key)
                for key in [str(item) for item in args.get("fields", [])[:16]]
            },
        }
    ]
    return _request_codex_agentic_json(
        system_prompt=system_prompt,
        user_payload=polish_context,
        tool_specs=tool_specs,
        fallback_builder=_fallback_final_polish,
    )


def _fallback_judge_feedback(reason: str, payload: dict[str, Any]) -> dict[str, Any]:
    business = payload.get("business_judgement_layer", {}) or {}
    decision = payload.get("decision_design_layer", {}) or {}
    polish = payload.get("final_polish_layer", {}) or {}
    issues: list[dict[str, Any]] = []
    if len(business.get("judgement_points") or []) < 2:
        issues.append({"issue_type": "business_depth", "route_to": "business_synthesis", "message": "业务判断层仍然偏薄。", "severity": "high"})
    if len(decision.get("priority_actions") or []) < 2:
        issues.append({"issue_type": "decision_strength", "route_to": "decision_design", "message": "决策设计层没有形成足够清晰的优先级和执行顺序。", "severity": "high"})
    if len(polish.get("polished_executive_summary") or []) < 2:
        issues.append({"issue_type": "polish_quality", "route_to": "final_polish", "message": "最终表达层没有形成足够锋利的管理层摘要。", "severity": "medium"})
    verdict = "revise" if issues else "pass"
    return {
        "mode": "fallback",
        "reason": reason,
        "verdict": verdict,
        "issues": issues,
        "strengths": ["长链结构已形成层级分工。"] if not issues else [],
        "revise_instructions": [item["message"] for item in issues][:4],
        "route_summary": [f"{item['issue_type']} -> {item['route_to']}" for item in issues][:4],
    }


def codex_judge_feedback(judge_context: dict[str, Any]) -> dict[str, Any]:
    system_prompt = (
        "You are Codex acting as the final Judge Agent for an analytics report. "
        "You must answer in Simplified Chinese and JSON only. "
        "You will receive the business judgment layer, decision design layer, final polish layer, and challenge layer. "
        "Return keys: verdict, issues, strengths, revise_instructions, route_summary. "
        "verdict must be pass or revise. "
        "issues must be a list of objects with keys: issue_type, route_to, message, severity. "
        "route_to must be one of: business_synthesis, decision_design, final_polish. "
        "If the problem is about business logic, route to business_synthesis. "
        "If the problem is about action strength, priority, scenario, or validation agenda, route to decision_design. "
        "If the problem is mainly about readability, structure, or wording softness, route to final_polish. "
        "Do not route every issue to polish."
    )
    tool_specs = [
        {
            "name": "lookup_judge_context",
            "description": "Read selected business, decision, challenge, and polish layers before judging.",
            "parameters": {
                "type": "object",
                "properties": {"fields": {"type": "array", "items": {"type": "string"}}},
                "required": ["fields"],
                "additionalProperties": False,
            },
            "handler": lambda args: {
                key: judge_context.get(key)
                for key in [str(item) for item in args.get("fields", [])[:16]]
            },
        }
    ]
    return _request_codex_agentic_json(
        system_prompt=system_prompt,
        user_payload=judge_context,
        tool_specs=tool_specs,
        fallback_builder=_fallback_judge_feedback,
    )


def _fallback_report_judgement(reason: str, payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "mode": "fallback",
        "reason": reason,
        "total_score": 55,
        "subscores": {
            "specificity": 10,
            "business_judgment": 10,
            "metric_explanation": 10,
            "method_interpretation": 10,
            "flow_readability": 10,
            "anti_genericity": 5,
        },
        "verdict": "fallback",
        "strengths": ["Codex judge unavailable"],
        "weaknesses": ["Judge request failed"],
        "improvement_actions": ["Retry with live Codex"],
        "brief_rationale": f"Fallback because {reason}",
    }


def codex_judge_report(report_context: dict[str, Any]) -> dict[str, Any]:
    system_prompt = (
        "You are CodexJudge, a very strict principal analytics reviewer. "
        "You must answer in Simplified Chinese and JSON only. "
        "Judge the report as a management-facing analytical report, not as a code artifact. "
        "Reward only concrete statements tied to actual dataset objects, indicators, risks, evidence chains, and actions. "
        "Penalize process talk, generic template language, repeated empty phrases, and conclusions without supporting metrics or tables. "
        "Return keys: total_score, subscores, verdict, strengths, weaknesses, improvement_actions, brief_rationale. "
        "subscores must include specificity (0-20), business_judgment (0-20), metric_explanation (0-15), method_interpretation (0-15), flow_readability (0-15), anti_genericity (0-15). "
        "total_score must be an integer 0-100. "
        "80+ means genuinely strong, 70-79 usable, 60-69 weak, below 60 poor. "
        "weaknesses and improvement_actions must be concrete Chinese strings."
    )
    tool_specs = [
        {
            "name": "lookup_report_slice",
            "description": "Read a compact slice of the report payload before judging it.",
            "parameters": {
                "type": "object",
                "properties": {
                    "fields": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["fields"],
                "additionalProperties": False,
            },
            "handler": lambda args: {
                key: report_context.get(key)
                for key in [str(item) for item in args.get("fields", [])[:14]]
            },
        }
    ]
    result = _request_codex_agentic_json(
        system_prompt=system_prompt,
        user_payload=report_context,
        tool_specs=tool_specs,
        fallback_builder=_fallback_report_judgement,
    )
    if result.get("mode") == "fallback":
        backup = _request_codex_json(
            system_prompt=system_prompt,
            user_payload=report_context,
            fallback_builder=_fallback_report_judgement,
        )
        if backup.get("mode") != "fallback":
            backup["mode"] = "live_codex_judge_backup"
            backup["judge_primary_path"] = "agentic_then_json_backup"
            return backup
    return result


def _fallback_procurement_sales_judge(reason: str, payload: dict[str, Any]) -> dict[str, Any]:
    runtime = payload.get("intelligence_runtime", {}) or {}
    critical_layers = runtime.get("critical_layers", []) or []
    fallback_layers = [item.get("layer") for item in critical_layers if item.get("runtime_state") == "fallback"]
    context_compaction = payload.get("context_compaction", {}) or {}
    judge_pack = context_compaction.get("judge_pack", {}) or {}
    sections = payload.get("sections", []) or judge_pack.get("section_summaries", []) or []
    section_lookup = {str(section.get("id") or ""): section for section in sections}
    section_titles = {str(section.get("title") or "") for section in sections}
    supplier_section = section_lookup.get("sales_supplier_impact") or section_lookup.get("followup_mining") or {}
    supplier_bullets = [str(item).strip() for item in supplier_section.get("bullets", []) if str(item).strip()]
    section_ids = {str(section.get("id") or "") for section in sections}
    object_summaries = judge_pack.get("object_summaries", []) or []
    object_dimensions = {str(item.get("dimension") or "") for item in object_summaries}
    relation_findings = [str(item).strip() for item in judge_pack.get("relation_findings", []) if str(item).strip()]

    score = 78
    strengths: list[str] = []
    weaknesses: list[str] = []
    improvements: list[str] = []
    route_to: list[str] = []

    has_core_dimensions = {"sales_product_impact", "sales_sku_impact", "sales_supplier_impact"} <= section_ids or {
        "商品经营影响评估",
        "SKU经营影响评估",
        "供应商协同与履约评估",
    } <= section_titles or {"商品", "SKU", "供应商"} <= object_dimensions
    if has_core_dimensions:
        strengths.append("商品、SKU、卖家三层对象已拆开，不再混成一张总量榜。")
        score += 4
    else:
        weaknesses.append("商品、SKU、卖家三层还没有完整拆开。")
        route_to.append("business_synthesis")
        score -= 8

    if "followup_mining" in section_ids or "继续深挖洞察" in section_titles:
        strengths.append("已有继续深挖洞察层，不再停在头部对象描述。")
        score += 3
    else:
        weaknesses.append("缺少继续深挖洞察层。")
        route_to.append("followup_mining")
        score -= 6

    supplier_rows = ((supplier_section.get("tables") or [{}])[0].get("rows", [])) if isinstance(supplier_section, dict) else []
    supplier_relationship_hit = any("复购客户占比" in bullet and "低分评价占比" in bullet for bullet in supplier_bullets) or any(
        ("复购客户占比" in str(row.get("判断依据") or "")) and ("低分评价占比" in str(row.get("判断依据") or ""))
        for row in supplier_rows[:8]
    ) or any("复购" in item and "低分" in item for item in relation_findings[:8]) or any(
        "复购" in str(summary.get("head_summary") or "") and "动作/判断" in str(summary.get("head_summary") or "")
        for summary in object_summaries
        if str(summary.get("dimension") or "") == "供应商"
    )
    if supplier_relationship_hit:
        strengths.append("供应商层已经把口碑与复购承接关系写成业务判断。")
        score += 4
    else:
        weaknesses.append("供应商层仍缺少口碑与复购/单客产出的关系判断。")
        route_to.extend(["business_synthesis", "followup_mining"])
        score -= 10

    if context_compaction and judge_pack.get("section_summaries") and object_summaries and relation_findings:
        strengths.append("Context Compaction 已形成原始行、对象摘要、关系矩阵和 judge pack。")
        score += 3
    else:
        weaknesses.append("Context Compaction 还不完整，judge 缺少稳定的压缩证据包。")
        route_to.append("business_synthesis")
        score -= 6

    if fallback_layers:
        weaknesses.append("关键智能层存在 fallback：" + "、".join(fallback_layers[:6]) + "。")
        improvements.append("补 live Codex 能力后再放行主报告，不能把 fallback 产物当最终版。")
        score -= min(18, 4 * len(fallback_layers))
    else:
        strengths.append("关键智能层均为 live 结果。")

    score = max(0, min(100, int(score)))
    verdict = "pass" if score >= 90 and not fallback_layers and not route_to else "block"
    if not improvements:
        improvements = [
            "继续压缩中位对象的低基数误判，确保中位层更像真实腰部代表。",
            "把关系挖掘层继续接进当前用途、业务含义和动作矩阵，不只停在对象判断。",
        ]
    route_to = [item for item in route_to if item]
    return {
        "mode": "fallback",
        "reason": reason,
        "judge_type": "procurement_sales",
        "total_score": score,
        "threshold": 80,
        "target_score": 90,
        "verdict": verdict,
        "strengths": strengths[:6],
        "weaknesses": weaknesses[:6],
        "improvement_actions": improvements[:6],
        "route_to": route_to[:5],
        "brief_rationale": f"采销专门 judge 以 80 分为放行线；当前得分 {score}。"
    }


def codex_procurement_sales_judge(report_context: dict[str, Any]) -> dict[str, Any]:
    system_prompt = (
        "You are CodexJudge acting as a procurement-sales specialist reviewer. "
        "You must answer in Simplified Chinese and JSON only. "
        "Judge this report only as a 采销经营决策报告. "
        "If context_compaction is present, use judge_pack as the primary compact review payload and raw sections only as support. "
        "A strong report must separate product, SKU, category, and supplier roles; must link reputation or fulfillment to repeat purchase, customer coverage, or revenue-per-customer; "
        "must include head, middle, and tail representative objects; and must avoid generic phrases without object-level evidence. "
        "If key intelligence layers are fallback rather than live, you must not pass the report. "
        "Return keys: total_score, threshold, target_score, verdict, strengths, weaknesses, improvement_actions, route_to, brief_rationale. "
        "threshold must be 80 as the base admissibility line. target_score must be 90 as the high-score release line. verdict must be pass or block. "
        "Below 80 or any critical fallback means block. Scores between 80 and 89 should still be treated as not yet high quality and should route to revision. "
        "If blocked, route_to must name which layer(s) should be rerun, chosen from: business_synthesis, decision_design, final_polish, followup_mining, sections_finalized."
    )
    tool_specs = [
        {
            "name": "lookup_procurement_sales_report",
            "description": "Read selected report and runtime fields before judging the procurement-sales report.",
            "parameters": {
                "type": "object",
                "properties": {
                    "fields": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["fields"],
                "additionalProperties": False,
            },
            "handler": lambda args: {
                key: report_context.get(key)
                for key in [str(item) for item in args.get("fields", [])[:12]]
            },
        }
    ]
    return _request_codex_agentic_json(
        system_prompt=system_prompt,
        user_payload=report_context,
        tool_specs=tool_specs,
        fallback_builder=_fallback_procurement_sales_judge,
    )


def _fallback_eval_feedback_summary(reason: str, payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "mode": "fallback",
        "reason": reason,
        "headline": "当前批量评测已完成，但 Codex 汇总器未在线返回；先按规则层汇总继续优化。",
        "common_failures": [
            "管理层摘要仍可能掺入过程性描述。",
            "强结论与证据链仍需要继续压实。",
            "正文与附录的边界仍需继续收紧。",
        ],
        "priority_repairs": [
            "优先压缩管理层摘要，只保留结论、风险、动作和证据。",
            "对所有优先级判断补足指标、时间和切片证据。",
            "把方法结果继续下沉，正文只保留能支持动作的解释。",
        ],
        "score_hypotheses": [
            "specificity 与 flow_readability 仍是最容易被过程话术拉低的分项。",
            "business_judgment 与 anti_genericity 取决于证据链是否闭合。",
        ],
        "brief_rationale": f"Fallback because {reason}",
    }


def codex_summarize_eval_feedback(eval_context: dict[str, Any]) -> dict[str, Any]:
    system_prompt = (
        "You are Codex acting as a score-improvement strategist for analytical reports. "
        "You must answer in Simplified Chinese and JSON only. "
        "You will receive multiple evaluation results from large-scale report tests. "
        "Your job is to summarize what is repeatedly hurting the score, what to fix first, and what score gains are most realistic next. "
        "Return keys: headline, common_failures, priority_repairs, score_hypotheses, brief_rationale. "
        "All list fields must contain 3 to 6 concrete Chinese strings. "
        "Avoid generic PM language. Focus on evidence chains, management readability, business judgment, and anti-genericity."
    )
    tool_specs = [
        {
            "name": "lookup_eval_summary",
            "description": "Read selected evaluation result slices before summarizing score improvement priorities.",
            "parameters": {
                "type": "object",
                "properties": {
                    "fields": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["fields"],
                "additionalProperties": False,
            },
            "handler": lambda args: {
                key: eval_context.get(key)
                for key in [str(item) for item in args.get("fields", [])[:12]]
            },
        }
    ]
    result = _request_codex_agentic_json(
        system_prompt=system_prompt,
        user_payload=eval_context,
        tool_specs=tool_specs,
        fallback_builder=_fallback_eval_feedback_summary,
    )
    if result.get("mode") == "fallback":
        backup = _request_codex_json(
            system_prompt=system_prompt,
            user_payload=eval_context,
            fallback_builder=_fallback_eval_feedback_summary,
        )
        if backup.get("mode") != "fallback":
            backup["mode"] = "live_codex_feedback_backup"
            backup["feedback_primary_path"] = "agentic_then_json_backup"
            return backup
    return result


def _fallback_generic_metric_derivation_plan(reason: str, payload: dict[str, Any]) -> dict[str, Any]:
    metrics = []
    for item in payload.get("metric_candidates", [])[:24]:
        metrics.append(
            {
                "metric_id": str(item.get("metric_id") or item.get("metric_name") or "metric").strip(),
                "metric_name": str(item.get("metric_name") or item.get("metric_id") or "指标").strip(),
                "formula": str(item.get("formula") or "按当前字段口径直接计算").strip(),
                "source_fields": [str(field) for field in item.get("source_fields", [])[:6]],
                "business_value": str(item.get("business_value") or "作为通用经营分析中的候选派生指标").strip(),
                "claim_strength": "weak",
                "caution": "当前为 fallback 生成的派生指标计划，strict_90_pdf 不得视为 live AI 解释结论。",
            }
        )
    return {
        "mode": "fallback",
        "reason": reason,
        "metrics": metrics,
        "notes": [
            "当前 metric_derivation_plan 由 fallback 生成，只能作为降级观察与补字段参考。",
            "strict_90_pdf 模式下，fallback 指标计划不得视为 AI 成功调用。",
        ],
    }


def codex_generic_metric_derivation_plan(plan_context: dict[str, Any]) -> dict[str, Any]:
    system_prompt = (
        "You are Codex acting as a Metric Derivation Planning Agent for a generic long business report. "
        "You must answer in Simplified Chinese and JSON only. "
        "Your job is to read field semantics, sample rows, and business context, then decide which derived metrics can be computed safely. "
        "Return JSON only with keys: metrics, notes. "
        "metrics must be a list of 8 to 24 objects with keys: metric_id, metric_name, formula, source_fields, business_value, claim_strength, caution. "
        "claim_strength must be one of: strong, medium, weak. "
        "Do not invent source fields that are not in the payload."
    )
    tool_specs = [
        {
            "name": "lookup_metric_derivation_context",
            "description": "Read selected field semantics, business context, and candidate metrics before planning derived metrics.",
            "parameters": {
                "type": "object",
                "properties": {"fields": {"type": "array", "items": {"type": "string"}}},
                "required": ["fields"],
                "additionalProperties": False,
            },
            "handler": lambda args: {
                key: plan_context.get(key)
                for key in [str(item) for item in args.get("fields", [])[:16]]
            },
        }
    ]
    return _request_codex_agentic_json(
        system_prompt=system_prompt,
        user_payload=plan_context,
        tool_specs=tool_specs,
        fallback_builder=_fallback_generic_metric_derivation_plan,
    )


def _fallback_generic_long_page_plan(reason: str, payload: dict[str, Any]) -> dict[str, Any]:
    seed_pages = payload.get("seed_page_plan", [])[:50]
    pages = []
    for index, item in enumerate(seed_pages, start=1):
        pages.append(
            {
                "page_number": int(item.get("page_number") or index),
                "page_title": str(item.get("page_title") or f"第{index}页").strip(),
                "management_question": str(item.get("management_question") or item.get("business_question") or "当前这一页要回答什么管理问题").strip(),
                "page_purpose": str(item.get("page_purpose") or "把这一页变成管理层可读的经营判断").strip(),
                "required_metrics": [str(metric) for metric in item.get("required_metrics", [])[:6]],
                "required_dimensions": [str(metric) for metric in item.get("required_dimensions", [])[:6]],
                "available_fields": [str(metric) for metric in item.get("available_fields", [])[:12]],
                "derived_metrics": item.get("derived_metrics", [])[:6],
                "evidence_query": str(item.get("evidence_query") or "围绕当前页主题抽取对象、结构、异常与字段边界证据").strip(),
                "objects_to_discuss": [str(obj) for obj in item.get("objects_to_discuss", [])[:8]],
                "allowed_claim_types": [str(t) for t in item.get("allowed_claim_types", [])[:6]],
                "forbidden_claim_types": [str(t) for t in item.get("forbidden_claim_types", [])[:6]],
                "required_table_or_chart": str(item.get("required_table_or_chart") or "table").strip(),
                "action_type": str(item.get("action_type") or "验证计划").strip(),
                "source_passes": [str(p) for p in item.get("source_passes", [])[:8]],
            }
        )
    return {
        "mode": "fallback",
        "reason": reason,
        "pages": pages,
        "notes": [
            "当前 long_report_page_plan 由 fallback 生成，只能作为降级版页面规划。",
            "strict_90_pdf 模式下，fallback 页面规划不得视为通过。"
        ],
    }


def codex_generic_long_page_plan(plan_context: dict[str, Any]) -> dict[str, Any]:
    system_prompt = (
        "You are Codex acting as a Long Report Page Planning Agent for a generic long business report. "
        "You must answer in Simplified Chinese and JSON only. "
        "Create a 35 to 50 page page-plan for a management-facing long report. "
        "Return JSON only with keys: pages, notes. "
        "pages must be a list of 35 to 50 objects. "
        "Each object must contain exactly these keys: page_number, page_title, management_question, page_purpose, required_metrics, required_dimensions, available_fields, derived_metrics, evidence_query, objects_to_discuss, allowed_claim_types, forbidden_claim_types, required_table_or_chart, action_type, source_passes. "
        "Do not output empty pages. Do not repeat generic titles."
    )
    tool_specs = [
        {
            "name": "lookup_generic_page_plan_context",
            "description": "Read selected business context, question bank, metric plan, object registry and seed plan before creating the AI page plan.",
            "parameters": {
                "type": "object",
                "properties": {"fields": {"type": "array", "items": {"type": "string"}}},
                "required": ["fields"],
                "additionalProperties": False,
            },
            "handler": lambda args: {
                key: plan_context.get(key)
                for key in [str(item) for item in args.get("fields", [])[:18]]
            },
        }
    ]
    return _request_codex_agentic_json(
        system_prompt=system_prompt,
        user_payload=plan_context,
        tool_specs=tool_specs,
        fallback_builder=_fallback_generic_long_page_plan,
    )


def _fallback_generic_page_generation_batch(reason: str, payload: dict[str, Any]) -> dict[str, Any]:
    pages = []
    for item in payload.get("pages", [])[:8]:
        page_number = int(item.get("page_number") or 0)
        title = str(item.get("page_title") or f"第{page_number}页").strip()
        metric_rows = item.get("derived_metrics") or []
        evidence = []
        for metric in metric_rows[:2]:
            evidence.append(
                {
                    "metric_id": str(metric.get("metric_id") or "").strip(),
                    "metric_name": str(metric.get("metric_name") or "").strip(),
                    "value": str(metric.get("value") or "待补数据").strip(),
                    "comparison": str(metric.get("comparison") or "当前无稳定比较口径").strip(),
                    "object_or_dimension": "当前页面主对象",
                    "evidence_strength": str(metric.get("evidence_strength") or "low").strip(),
                }
            )
        pages.append(
            {
                "page_number": page_number,
                "page_title": title,
                "management_question": str(item.get("management_question") or "").strip(),
                "diagnosis": f"{title} 当前仅获得 fallback 级 AI 草稿，因此本页只能作为观察级诊断，不得进入 strict_90_pdf 正式版。需要围绕对象结构、字段边界和已知异常继续复核，不能把模板性判断写成管理结论。",
                "evidence": evidence[:1] or [
                    {
                        "metric_id": "fallback_metric",
                        "metric_name": "fallback_metric",
                        "value": "待补数据",
                        "comparison": "当前无稳定比较",
                        "object_or_dimension": "当前页面主对象",
                        "evidence_strength": "low",
                    }
                ],
                "derived_metric_explanation": "当前页面的派生指标解释来自 fallback 生成，只能作为后续 live AI 重跑前的占位。",
                "business_interpretation": "当前页面暂时只能提示这一页仍缺少 live AI 的深度经营解释，因此不能把页面中的判断视为严格经营结论。必须在重跑后用 live AI 内容覆盖这段说明。",
                "recommended_action": {
                    "object": "当前页面主对象",
                    "trigger_metric": evidence[0]["metric_id"] if evidence else "fallback_metric",
                    "current_value": evidence[0]["value"] if evidence else "待补数据",
                    "threshold_or_comparison": "需待 live AI 复核后确定",
                    "owner_role": "业务负责人 + 数据分析",
                    "action": "重跑 live AI page_generation_batch 并覆写当前页面",
                    "deadline": "T+1",
                    "verification_metric": evidence[0]["metric_name"] if evidence else "fallback_metric",
                },
                "data_limitations": "当前页面为 fallback 级 AI 草稿，严格模式下不得释放。",
                "forbidden_misreadings": ["不能把 fallback 页面当成严格经营判断"],
                "ai_content_hash": f"fallback-{page_number}",
                "source_passes": [str(p) for p in item.get("source_passes", [])[:8]],
                "low_data_boundary_page": True,
            }
        )
    return {
        "mode": "fallback",
        "reason": reason,
        "pages": pages,
    }


def codex_generic_page_generation_batch(draft_context: dict[str, Any]) -> dict[str, Any]:
    system_prompt = (
        "You are Codex acting as a Page Generation Agent for a generic long business report. "
        "You must answer in Simplified Chinese and JSON only. "
        "Generate structured page drafts for the provided page specs. "
        "Return JSON only with key: pages. "
        "pages must be a list with one object per requested page, and each object must contain exactly these keys: "
        "page_number, page_title, management_question, diagnosis, evidence, derived_metric_explanation, business_interpretation, recommended_action, data_limitations, forbidden_misreadings, ai_content_hash, source_passes. "
        "diagnosis must be specific, not generic. business_interpretation must explain management meaning, not just restate the metric. "
        "evidence must be a list of 2 to 4 objects with keys: metric_id, metric_name, value, comparison, object_or_dimension, evidence_strength. "
        "recommended_action must be an object with keys: object, trigger_metric, current_value, threshold_or_comparison, owner_role, action, deadline, verification_metric. "
        "Do not output markdown."
    )
    tool_specs = [
        {
            "name": "lookup_generic_page_draft_context",
            "description": "Read selected page plan rows, derived metrics, object registry hints, and evidence context before drafting pages.",
            "parameters": {
                "type": "object",
                "properties": {"fields": {"type": "array", "items": {"type": "string"}}},
                "required": ["fields"],
                "additionalProperties": False,
            },
            "handler": lambda args: {
                key: draft_context.get(key)
                for key in [str(item) for item in args.get("fields", [])[:18]]
            },
        }
    ]
    return _request_codex_agentic_json(
        system_prompt=system_prompt,
        user_payload=draft_context,
        tool_specs=tool_specs,
        fallback_builder=_fallback_generic_page_generation_batch,
    )


def _fallback_generic_management_question_bank(reason: str, payload: dict[str, Any]) -> dict[str, Any]:
    seed = payload.get("seed_questions") or []
    questions = []
    for item in seed[:20]:
        questions.append(
            {
                "priority": int(item.get("priority") or len(questions) + 1),
                "business_question": str(item.get("business_question") or "").strip(),
                "why_it_matters": str(item.get("why_it_matters") or "这是管理层当前最想回答的问题").strip(),
                "can_answer_now": str(item.get("can_answer_now") or "部分可答").strip(),
                "required_fields": [str(field) for field in item.get("required_fields", [])[:6]],
                "report_section": str(item.get("report_section") or "管理问题诊断").strip(),
                "management_action": str(item.get("management_action") or "围绕问题组织动作").strip(),
            }
        )
    return {
        "mode": "fallback",
        "reason": reason,
        "questions": questions,
    }


def codex_generic_management_question_bank(question_context: dict[str, Any]) -> dict[str, Any]:
    system_prompt = (
        "You are Codex acting as a Management Question Bank Agent for a generic long business report. "
        "You must answer in Simplified Chinese and JSON only. "
        "Return JSON only with key: questions. "
        "questions must be a list of at least 20 objects. "
        "Each object must contain keys: priority, business_question, why_it_matters, can_answer_now, required_fields, report_section, management_action. "
        "Prioritize management-facing questions, not technical questions."
    )
    tool_specs = [
        {
            "name": "lookup_generic_question_context",
            "description": "Read selected requirement, field boundary, and seed-question context before producing the management question bank.",
            "parameters": {
                "type": "object",
                "properties": {"fields": {"type": "array", "items": {"type": "string"}}},
                "required": ["fields"],
                "additionalProperties": False,
            },
            "handler": lambda args: {
                key: question_context.get(key)
                for key in [str(item) for item in args.get("fields", [])[:18]]
            },
        }
    ]
    return _request_codex_agentic_json(
        system_prompt=system_prompt,
        user_payload=question_context,
        tool_specs=tool_specs,
        fallback_builder=_fallback_generic_management_question_bank,
    )


def _fallback_generic_exploratory_interpretation(reason: str, payload: dict[str, Any]) -> dict[str, Any]:
    metric_rows = payload.get("metric_execution", {}).get("metrics", []) or []
    findings = [f"{row.get('metric_name', '指标')} 当前值 {row.get('value', '待补数据')}，比较口径为 {row.get('comparison', '当前无稳定比较')}。" for row in metric_rows[:6]]
    return {
        "mode": "fallback",
        "reason": reason,
        "main_findings": findings,
        "anomalies": ["当前探索性解释处于 fallback 模式，不能直接升级为强诊断。"],
        "possible_reasons": ["需要 live AI 进一步拆解对象差异、时间变化和异常来源。"],
        "cannot_conclude": ["fallback 模式下不得把观察写成经营拍板结论。"],
        "next_validations": ["重跑 live AI exploratory_interpretation 并覆盖当前结果。"],
    }


def codex_generic_exploratory_interpretation(exploratory_context: dict[str, Any]) -> dict[str, Any]:
    system_prompt = (
        "You are Codex acting as an Exploratory Interpretation Agent for a generic long business report. "
        "You must answer in Simplified Chinese and JSON only. "
        "Return JSON only with keys: main_findings, anomalies, possible_reasons, cannot_conclude, next_validations. "
        "All fields must be concise Chinese lists. "
        "The goal is to turn descriptive statistics and object structure into management-facing exploratory interpretation."
    )
    tool_specs = [
        {
            "name": "lookup_generic_exploratory_context",
            "description": "Read selected field-boundary, metric, object, and sample-row context before writing exploratory interpretation.",
            "parameters": {
                "type": "object",
                "properties": {"fields": {"type": "array", "items": {"type": "string"}}},
                "required": ["fields"],
                "additionalProperties": False,
            },
            "handler": lambda args: {
                key: exploratory_context.get(key)
                for key in [str(item) for item in args.get("fields", [])[:18]]
            },
        }
    ]
    return _request_codex_agentic_json(
        system_prompt=system_prompt,
        user_payload=exploratory_context,
        tool_specs=tool_specs,
        fallback_builder=_fallback_generic_exploratory_interpretation,
    )


def _fallback_generic_business_rigor_review(reason: str, payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "mode": "fallback",
        "reason": reason,
        "total_score": 0,
        "verdict": "revise",
        "weaknesses": ["当前 business_rigor_review 处于 fallback 模式，不能作为 strict_90 交付依据。"],
        "improvement_actions": ["重跑 live AI 的 business_rigor_review。"],
    }


def codex_generic_business_rigor_review(rigor_context: dict[str, Any]) -> dict[str, Any]:
    system_prompt = (
        "You are Codex acting as a Business Rigor Review Agent for a generic long business report. "
        "You must answer in Simplified Chinese and JSON only. "
        "Return JSON only with keys: total_score, verdict, weaknesses, improvement_actions. "
        "total_score must be 0-100. verdict must be pass or revise. "
        "You must be strict about unsupported causal claims, field-boundary overreach, and low-sample overclaiming."
    )
    tool_specs = [
        {
            "name": "lookup_generic_rigor_context",
            "description": "Read selected context about field boundaries, page drafts, and object judgments before reviewing business rigor.",
            "parameters": {
                "type": "object",
                "properties": {"fields": {"type": "array", "items": {"type": "string"}}},
                "required": ["fields"],
                "additionalProperties": False,
            },
            "handler": lambda args: {
                key: rigor_context.get(key)
                for key in [str(item) for item in args.get("fields", [])[:18]]
            },
        }
    ]
    return _request_codex_agentic_json(
        system_prompt=system_prompt,
        user_payload=rigor_context,
        tool_specs=tool_specs,
        fallback_builder=_fallback_generic_business_rigor_review,
    )


def _fallback_generic_final_review(reason: str, payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "mode": "fallback",
        "reason": reason,
        "total_score": 0,
        "verdict": "revise",
        "weaknesses": ["当前 final_codex_interpretation_review 处于 fallback 模式，不能建议生成 strict_90 PDF。"],
        "improvement_actions": ["重跑 live AI 的 final_codex_interpretation_review。"],
    }


def codex_generic_final_review(review_context: dict[str, Any]) -> dict[str, Any]:
    system_prompt = (
        "You are Codex acting as the Final Delivery Review Agent for a generic long business report. "
        "You must answer in Simplified Chinese and JSON only. "
        "Return JSON only with keys: total_score, verdict, weaknesses, improvement_actions. "
        "total_score must be 0-100. verdict must be pass or revise. "
        "You must judge whether the report is truly deliverable to management."
    )
    tool_specs = [
        {
            "name": "lookup_generic_final_review_context",
            "description": "Read selected page-draft, gate, and review context before making the final delivery judgement.",
            "parameters": {
                "type": "object",
                "properties": {"fields": {"type": "array", "items": {"type": "string"}}},
                "required": ["fields"],
                "additionalProperties": False,
            },
            "handler": lambda args: {
                key: review_context.get(key)
                for key in [str(item) for item in args.get("fields", [])[:18]]
            },
        }
    ]
    return _request_codex_agentic_json(
        system_prompt=system_prompt,
        user_payload=review_context,
        tool_specs=tool_specs,
        fallback_builder=_fallback_generic_final_review,
    )
