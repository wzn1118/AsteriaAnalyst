from __future__ import annotations

from concurrent.futures import FIRST_COMPLETED, Future, ThreadPoolExecutor, wait
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass(slots=True)
class JobNode:
    job_id: str
    title: str
    detail: str
    runner: Callable[[dict[str, Any]], Any]
    dependencies: tuple[str, ...] = field(default_factory=tuple)
    category: str = "engineering"
    parallel_group: str = ""
    formatter: Callable[[Any], str] | None = None


def _default_output_summary(output: Any) -> str:
    if output is None:
        return ""
    if isinstance(output, dict):
        for key in ["summary", "title", "name", "mode", "detail", "why"]:
            value = output.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return f"dict({len(output)})"
    if isinstance(output, list):
        return f"list({len(output)})"
    return str(output)


def execute_job_graph(
    nodes: list[JobNode],
    *,
    initial_results: dict[str, Any] | None = None,
    max_workers: int = 4,
) -> dict[str, Any]:
    remaining = {node.job_id: node for node in nodes}
    results = dict(initial_results or {})
    steps: list[dict[str, Any]] = []
    running: dict[Future[Any], JobNode] = {}

    def _ready_nodes() -> list[JobNode]:
        return [
            node
            for node in remaining.values()
            if all(dependency in results for dependency in node.dependencies)
        ]

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        while remaining or running:
            for node in _ready_nodes():
                if any(existing.job_id == node.job_id for existing in running.values()):
                    continue
                steps.append(
                    {
                        "id": node.job_id,
                        "title": node.title,
                        "detail": node.detail,
                        "status": "running",
                        "category": node.category,
                        "parallel_group": node.parallel_group,
                        "timestamp": _now_iso(),
                    }
                )
                future = executor.submit(node.runner, dict(results))
                running[future] = node
                remaining.pop(node.job_id, None)

            if not running:
                if remaining:
                    unresolved = ", ".join(sorted(remaining))
                    raise RuntimeError(f"Job graph stalled. Unresolved jobs: {unresolved}")
                break

            completed, _ = wait(running.keys(), return_when=FIRST_COMPLETED)
            for future in completed:
                node = running.pop(future)
                output = future.result()
                results[node.job_id] = output
                formatter = node.formatter or _default_output_summary
                steps.append(
                    {
                        "id": node.job_id,
                        "title": node.title,
                        "detail": node.detail,
                        "status": "completed",
                        "category": node.category,
                        "parallel_group": node.parallel_group,
                        "output": formatter(output),
                        "timestamp": _now_iso(),
                    }
                )

    return {
        "results": results,
        "steps": steps,
    }
