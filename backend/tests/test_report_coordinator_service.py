from app.services.report_coordinator_service import ReportCoordinator


def test_attach_external_runtime_event_marks_runtime_source_and_query_state() -> None:
    coordinator = ReportCoordinator(
        dataset_name="demo-dataset",
        sheet_name="Sheet1",
        report_lens="generic_long_business_report",
        query_loop_id="report-loop-demo",
    )

    coordinator.attach_external_runtime_event(
        {
            "stage_id": "runtime_child::post_report_runtime_review::completed",
            "title": "Runtime child: Codex run completed",
            "detail": "The runtime child finished successfully.",
            "timestamp": "2026-04-30T00:00:00Z",
            "payload": {
                "status": "completed",
                "runtime_child_job_id": "codex-task-child-001",
            },
        }
    )

    snapshot = coordinator.snapshot()
    assert snapshot["stage_events"]
    assert snapshot["stage_events"][0]["payload"]["source"] == "runtime_child_task"
    assert snapshot["stage_events"][0]["payload"]["external_runtime"] is True
    assert "runtime_child::post_report_runtime_review::completed" in snapshot["query_state"]["completed_stages"]
