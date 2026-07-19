from __future__ import annotations

import contextlib
import importlib
import io
import json
import shutil
import time
import traceback
import uuid
from pathlib import Path
from typing import Any

import duckdb
import numpy as np
import pandas as pd
from fastapi import HTTPException

from app.models import CodeExecutionRequest
from app.services.dataset_service import DATASETS_DIR, RUNS_DIR, load_dataset_frame
from app.services.path_service import bundled_rscript_candidates
from app.services.settings_service import load_runtime_settings_raw


def run_code(request: CodeExecutionRequest, python_executable: str) -> dict[str, Any]:
    frame, metadata, sheet = load_dataset_frame(request.dataset_id, request.active_sheet)
    if request.language == "sql":
        return _run_sql(frame, sheet["name"], request.code)
    if request.language == "r":
        return _run_r(
            request=request,
            dataset_name=metadata["name"],
            sheet_name=sheet["name"],
            frame=frame,
        )
    return _run_python(
        request=request,
        python_executable=python_executable,
        dataset_name=metadata["name"],
        sheet_name=sheet["name"],
        dataset_path=(DATASETS_DIR / request.dataset_id / sheet["storage_file"]).resolve(),
    )


def _run_sql(frame: pd.DataFrame, sheet_name: str, code: str) -> dict[str, Any]:
    connection = duckdb.connect()
    connection.register("dataset", frame)
    try:
        result = connection.execute(code).fetch_df().head(200)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"SQL execution failed: {exc}") from exc
    finally:
        connection.close()

    return {
        "language": "sql",
        "active_sheet": sheet_name,
        "stdout": "DuckDB query executed successfully.",
        "stderr": "",
        "result_kind": "table",
        "table": {
            "columns": result.columns.astype(str).tolist(),
            "rows": result.where(pd.notnull(result), None).to_dict(orient="records"),
        },
        "result": None,
        "images": [],
        "elapsed_ms": 0,
    }


def _run_python(
    *,
    request: CodeExecutionRequest,
    python_executable: str,
    dataset_name: str,
    sheet_name: str,
    dataset_path: Path,
) -> dict[str, Any]:
    run_id = uuid.uuid4().hex[:10]
    run_dir = RUNS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    frame = pd.read_pickle(dataset_path)
    start_time = time.time()
    artifacts: list[str] = []
    stdout_buffer = io.StringIO()
    stderr_buffer = io.StringIO()

    def _load_matplotlib():
        module = importlib.import_module("matplotlib")
        module.use("Agg")
        return module

    def _load_pyplot():
        _load_matplotlib()
        return importlib.import_module("matplotlib.pyplot")

    class LazyModule:
        def __init__(self, module_name: str, loader: Any = None) -> None:
            self._module_name = module_name
            self._loader = loader
            self._loaded: Any = None

        def _load(self) -> Any:
            if self._loaded is None:
                self._loaded = self._loader() if self._loader is not None else importlib.import_module(self._module_name)
            return self._loaded

        def __getattr__(self, item: str) -> Any:
            return getattr(self._load(), item)

        def __dir__(self) -> list[str]:
            return dir(self._load())

    lazy_duckdb = LazyModule("duckdb")
    lazy_pyplot = LazyModule("matplotlib.pyplot", loader=_load_pyplot)
    lazy_seaborn = LazyModule("seaborn")

    def save_chart(name: str | None = None) -> str:
        filename = name or f"chart-{len(artifacts) + 1}.png"
        if not filename.endswith(".png"):
            filename += ".png"
        target = run_dir / filename
        pyplot = lazy_pyplot._load()
        pyplot.tight_layout()
        pyplot.savefig(target, dpi=180, bbox_inches="tight")
        artifacts.append(filename)
        pyplot.close("all")
        return str(target)

    result_payload: dict[str, Any] = {"kind": "empty", "value": None}
    globals_dict = {
        "__name__": "__main__",
        "pd": pd,
        "np": np,
        "duckdb": lazy_duckdb,
        "sns": lazy_seaborn,
        "plt": lazy_pyplot,
        "df": frame,
        "save_chart": save_chart,
    }

    try:
        with contextlib.redirect_stdout(stdout_buffer), contextlib.redirect_stderr(stderr_buffer):
            exec(request.code, globals_dict, globals_dict)

        result = globals_dict.get("result")
        if isinstance(result, pd.DataFrame):
            preview = result.head(200).copy()
            preview = preview.where(pd.notnull(preview), None)
            result_payload = {
                "kind": "table",
                "value": {
                    "columns": preview.columns.astype(str).tolist(),
                    "rows": preview.to_dict(orient="records"),
                },
            }
        elif isinstance(result, (dict, list, str, int, float, bool)) or result is None:
            result_payload = {"kind": "json", "value": result}
        else:
            result_payload = {"kind": "text", "value": str(result)}
    except Exception:
        traceback.print_exc(file=stderr_buffer)
    finally:
        (run_dir / "stdout.txt").write_text(stdout_buffer.getvalue(), encoding="utf-8")
        (run_dir / "stderr.txt").write_text(stderr_buffer.getvalue(), encoding="utf-8")
        (run_dir / "result.json").write_text(
            json.dumps(result_payload, ensure_ascii=False, default=str),
            encoding="utf-8",
        )
        (run_dir / "artifacts.json").write_text(
            json.dumps(
                {"images": artifacts, "elapsed_ms": int((time.time() - start_time) * 1000)},
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

    return {
        "language": "python",
        "dataset_name": dataset_name,
        "active_sheet": sheet_name,
        "stdout": stdout_buffer.getvalue(),
        "stderr": stderr_buffer.getvalue(),
        "result_kind": result_payload.get("kind"),
        "table": result_payload.get("value") if result_payload.get("kind") == "table" else None,
        "result": result_payload.get("value") if result_payload.get("kind") != "table" else None,
        "images": [f"/storage/runs/{run_id}/{image}" for image in artifacts],
        "elapsed_ms": int((time.time() - start_time) * 1000),
    }


def _resolve_rscript_path() -> str | None:
    settings = load_runtime_settings_raw()
    configured = str(settings.get("rscript_path") or "").strip()
    if configured and Path(configured).exists():
        return configured
    for candidate in bundled_rscript_candidates():
        if candidate.exists():
            return str(candidate.resolve())
    discovered = shutil.which("Rscript")
    if discovered:
        return discovered
    return None


def _csv_ready_frame(frame: pd.DataFrame) -> pd.DataFrame:
    export_frame = frame.copy()
    for column in export_frame.columns:
        if pd.api.types.is_datetime64_any_dtype(export_frame[column]):
            export_frame[column] = export_frame[column].dt.strftime("%Y-%m-%d %H:%M:%S")
    return export_frame.where(pd.notnull(export_frame), None)


def _run_r(
    *,
    request: CodeExecutionRequest,
    dataset_name: str,
    sheet_name: str,
    frame: pd.DataFrame,
) -> dict[str, Any]:
    runtime_path = _resolve_rscript_path()
    if not runtime_path:
        raise HTTPException(
            status_code=400,
            detail="R execution is not available because Rscript Path is not configured.",
        )

    run_id = uuid.uuid4().hex[:10]
    run_dir = RUNS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    input_path = run_dir / "input-data.csv"
    _csv_ready_frame(frame).to_csv(input_path, index=False, encoding="utf-8-sig")

    runner = textwrap.dedent(
        f"""
        options(warn = 1)
        suppressPackageStartupMessages({{
          library(jsonlite)
          library(ggplot2)
        }})

        args <- commandArgs(trailingOnly = TRUE)
        dataset_path <- args[1]
        run_dir <- args[2]
        user_code <- {json.dumps(request.code, ensure_ascii=False)}
        start_time <- Sys.time()
        artifacts <- character()
        stdout_lines <- character()
        stderr_lines <- character()
        payload <- list(kind = "empty", value = NULL)

        append_stdout <- function(...) {{
          stdout_lines <<- c(stdout_lines, paste(..., collapse = ""))
        }}

        save_chart <- function(plot = ggplot2::last_plot(), name = NULL, width = 10, height = 6, dpi = 180) {{
          if (is.null(name) || !nzchar(name)) {{
            name <- sprintf("chart-%d.png", length(artifacts) + 1)
          }}
          if (!grepl("\\\\.png$", name, ignore.case = TRUE)) {{
            name <- paste0(name, ".png")
          }}
          target <- file.path(run_dir, name)
          ggplot2::ggsave(filename = target, plot = plot, width = width, height = height, dpi = dpi)
          artifacts <<- c(artifacts, name)
          target
        }}

        finalize_payload <- function(result) {{
          if (is.data.frame(result)) {{
            preview <- utils::head(result, 200)
            payload <<- list(
              kind = "table",
              value = list(
                columns = colnames(preview),
                rows = jsonlite::fromJSON(jsonlite::toJSON(preview, dataframe = "rows", na = "null", auto_unbox = TRUE))
              )
            )
          }} else if (
            is.null(result) ||
            is.atomic(result) ||
            is.list(result)
          ) {{
            payload <<- list(
              kind = "json",
              value = jsonlite::fromJSON(jsonlite::toJSON(result, auto_unbox = TRUE, null = "null", na = "null"))
            )
          }} else {{
            payload <<- list(kind = "text", value = paste(capture.output(print(result)), collapse = "\\n"))
          }}
        }}

        tryCatch({{
          df <- utils::read.csv(dataset_path, check.names = FALSE, stringsAsFactors = FALSE, encoding = "UTF-8")
          user_env <- new.env(parent = globalenv())
          user_env$df <- df
          user_env$save_chart <- save_chart
          user_env$append_stdout <- append_stdout
          user_env$result <- NULL

          evaluated <- NULL
          output <- capture.output(
            evaluated <- eval(parse(text = user_code), envir = user_env),
            type = "output"
          )
          if (length(output)) {{
            stdout_lines <<- c(stdout_lines, output)
          }}

          result <- get0("result", envir = user_env, ifnotfound = evaluated)
          finalize_payload(result)
        }}, error = function(exc) {{
          stderr_lines <<- c(stderr_lines, conditionMessage(exc))
        }}, finally = {{
          elapsed_ms <- as.integer(round(as.numeric(difftime(Sys.time(), start_time, units = "secs")) * 1000))
          writeLines(stdout_lines, file.path(run_dir, "stdout.txt"), useBytes = TRUE)
          writeLines(stderr_lines, file.path(run_dir, "stderr.txt"), useBytes = TRUE)
          jsonlite::write_json(payload, file.path(run_dir, "result.json"), auto_unbox = TRUE, null = "null", pretty = FALSE)
          jsonlite::write_json(list(images = unname(as.list(artifacts)), elapsed_ms = elapsed_ms), file.path(run_dir, "artifacts.json"), auto_unbox = TRUE, null = "null", pretty = FALSE)
        }})
        """
    ).strip()

    script_path = run_dir / "runner.R"
    script_path.write_text(runner, encoding="utf-8")

    try:
        completed = subprocess.run(
            [runtime_path, str(script_path), str(input_path), str(run_dir.resolve())],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=35,
            cwd=run_dir,
        )
    except subprocess.TimeoutExpired as exc:
        raise HTTPException(status_code=408, detail=f"R execution timed out after {exc.timeout} seconds.") from exc

    stdout_path = run_dir / "stdout.txt"
    stderr_path = run_dir / "stderr.txt"
    result_path = run_dir / "result.json"
    artifact_path = run_dir / "artifacts.json"

    stdout = stdout_path.read_text(encoding="utf-8", errors="replace") if stdout_path.exists() else completed.stdout
    stderr = stderr_path.read_text(encoding="utf-8", errors="replace") if stderr_path.exists() else completed.stderr
    result_payload = (
        json.loads(result_path.read_text(encoding="utf-8"))
        if result_path.exists()
        else {"kind": "text", "value": completed.stdout}
    )
    artifact_payload = (
        json.loads(artifact_path.read_text(encoding="utf-8"))
        if artifact_path.exists()
        else {"images": [], "elapsed_ms": 0}
    )

    if completed.returncode != 0 and not stderr.strip():
        stderr = completed.stderr or completed.stdout or f"Rscript exit {completed.returncode}"
    if completed.returncode != 0 and not result_path.exists():
        raise HTTPException(status_code=400, detail=f"R execution failed: {stderr.strip() or f'Rscript exit {completed.returncode}'}")

    return {
        "language": "r",
        "dataset_name": dataset_name,
        "active_sheet": sheet_name,
        "stdout": stdout,
        "stderr": stderr,
        "result_kind": result_payload.get("kind"),
        "table": result_payload.get("value") if result_payload.get("kind") == "table" else None,
        "result": result_payload.get("value") if result_payload.get("kind") != "table" else None,
        "images": [f"/storage/runs/{run_id}/{image}" for image in artifact_payload.get("images", [])],
        "elapsed_ms": artifact_payload.get("elapsed_ms", 0),
    }
