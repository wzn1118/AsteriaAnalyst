from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable

from app.services.report_hooks_service import ReportHookRegistry, build_default_report_hooks


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


StageRunner = Callable[[], Any]
HookPayloadBuilder = Callable[[Any], dict[str, Any]]
StageListener = Callable[[dict[str, Any]], None]


def _dedupe_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        text = str(value or "").strip()
        if not text or text in seen:
            continue
        seen.add(text)
        ordered.append(text)
    return ordered


@dataclass(slots=True)
class ReportCoordinator:
    dataset_name: str
    sheet_name: str
    report_lens: str
    query_loop_id: str
    hooks: ReportHookRegistry = field(default_factory=build_default_report_hooks)
    stage_events: list[dict[str, Any]] = field(default_factory=list)
    hook_events: list[dict[str, Any]] = field(default_factory=list)
    hook_state: dict[str, Any] = field(default_factory=dict)
    query_state: dict[str, Any] = field(default_factory=lambda: {
        "current_stage": "",
        "loop_iterations": 0,
        "completed_stages": [],
        "failed_stages": [],
    })
    control_signals: list[dict[str, Any]] = field(default_factory=list)
    stage_listener: StageListener | None = None

    def record_stage(self, stage_id: str, title: str, detail: str, *, payload: dict[str, Any] | None = None) -> None:
        event = {
            "stage_id": stage_id,
            "title": title,
            "detail": detail,
            "timestamp": _now_iso(),
        }
        if payload:
            event["payload"] = payload
        self.stage_events.append(event)
        if self.stage_listener:
            try:
                self.stage_listener(dict(event))
            except Exception:
                pass

    def run_hook(self, event: str, payload: dict[str, Any]) -> None:
        hook_records = self.hooks.run(event, payload, self.hook_state)
        self.hook_events.extend(hook_records)
        for record in hook_records:
            output = record.get("output") or {}
            if not isinstance(output, dict):
                continue
            control = output.get("control")
            if isinstance(control, dict) and control:
                self.control_signals.append(
                    {
                        "event": event,
                        "name": record.get("name"),
                        "control": control,
                        "timestamp": record.get("timestamp"),
                    }
                )

    def attach_external_runtime_event(self, event: dict[str, Any]) -> None:
        stage_id = str(event.get("stage_id") or "external_runtime")
        title = str(event.get("title") or "External runtime")
        detail = str(event.get("detail") or "")
        payload = dict(event.get("payload")) if isinstance(event.get("payload"), dict) else {}
        payload.setdefault("source", "runtime_child_task")
        payload.setdefault("external_runtime", True)
        self.record_stage(stage_id, title, detail, payload=payload)

        status = str(payload.get("status") or "").strip().lower()
        if status == "completed":
            completed = list(self.query_state.get("completed_stages") or [])
            if stage_id not in completed:
                completed.append(stage_id)
            self.query_state["completed_stages"] = completed
        elif status in {"failed", "cancelled", "timed_out"}:
            failed = list(self.query_state.get("failed_stages") or [])
            if stage_id not in failed:
                failed.append(stage_id)
            self.query_state["failed_stages"] = failed

    def consume_controls(self, event: str | None = None) -> dict[str, Any]:
        matched: list[dict[str, Any]] = []
        remaining: list[dict[str, Any]] = []
        for signal in self.control_signals:
            if event and str(signal.get("event") or "") != event:
                remaining.append(signal)
                continue
            matched.append(signal)
        if event:
            self.control_signals = remaining

        rerun_targets: list[str] = []
        skip_targets: list[str] = []
        block_release = False
        reasons: list[str] = []

        for signal in matched:
            control = signal.get("control") or {}
            rerun_value = control.get("rerun_stage")
            if isinstance(rerun_value, list):
                rerun_targets.extend(str(item).strip() for item in rerun_value if str(item).strip())
            elif str(rerun_value or "").strip():
                rerun_targets.append(str(rerun_value).strip())

            skip_value = control.get("skip_stage")
            if isinstance(skip_value, list):
                skip_targets.extend(str(item).strip() for item in skip_value if str(item).strip())
            elif str(skip_value or "").strip():
                skip_targets.append(str(skip_value).strip())

            if bool(control.get("block_release")):
                block_release = True

            reason = str(control.get("reason") or "").strip()
            if reason:
                reasons.append(reason)

        return {
            "signals": matched,
            "rerun_stage": _dedupe_preserve_order(rerun_targets),
            "skip_stage": _dedupe_preserve_order(skip_targets),
            "block_release": block_release,
            "reasons": _dedupe_preserve_order(reasons),
        }

    def execute_stage(
        self,
        *,
        stage_id: str,
        title: str,
        detail: str,
        runner: StageRunner,
        hook_event: str | None = None,
        hook_payload_builder: HookPayloadBuilder | None = None,
        max_attempts: int = 1,
    ) -> Any:
        attempts = max(1, int(max_attempts))
        self.query_state["current_stage"] = stage_id
        for attempt in range(1, attempts + 1):
            self.query_state["loop_iterations"] = int(self.query_state.get("loop_iterations") or 0) + 1
            self.record_stage(
                stage_id,
                title,
                detail,
                payload={"attempt": attempt, "max_attempts": attempts, "status": "running"},
            )
            try:
                output = runner()
                if hook_event and hook_payload_builder:
                    self.run_hook(hook_event, hook_payload_builder(output))
                self.record_stage(
                    stage_id,
                    title,
                    detail,
                    payload={"attempt": attempt, "max_attempts": attempts, "status": "completed"},
                )
                completed = list(self.query_state.get("completed_stages") or [])
                if stage_id not in completed:
                    completed.append(stage_id)
                self.query_state["completed_stages"] = completed
                self.query_state["current_stage"] = ""
                return output
            except Exception as exc:
                self.record_stage(
                    stage_id,
                    title,
                    detail,
                    payload={"attempt": attempt, "max_attempts": attempts, "status": "failed", "error": str(exc)},
                )
                if attempt >= attempts:
                    failed = list(self.query_state.get("failed_stages") or [])
                    if stage_id not in failed:
                        failed.append(stage_id)
                    self.query_state["failed_stages"] = failed
                    self.query_state["current_stage"] = ""
                    raise
        self.query_state["current_stage"] = ""
        raise RuntimeError(f"Stage {stage_id} exhausted without output")

    def snapshot(self) -> dict[str, Any]:
        return {
            "query_loop_id": self.query_loop_id,
            "dataset_name": self.dataset_name,
            "sheet_name": self.sheet_name,
            "report_lens": self.report_lens,
            "stage_events": self.stage_events,
            "hook_events": self.hook_events,
            "hook_state": self.hook_state,
            "control_signals": self.control_signals,
            "query_state": self.query_state,
        }
