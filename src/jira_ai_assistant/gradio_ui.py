"""
Interactive Gradio 6 UI for orchestrating the Jira AI Assistant crew.
"""

from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import gradio as gr

from jira_ai_assistant.crew import JiraAiAssistant
from jira_ai_assistant.tools.jira_tools import (
    JiraGetAllEpicsTool,
    JiraGetAllIssuesWithDetailsTool,
    JiraGetAllSprintsTool,
    JiraGetAllUsersTool,
    JiraGetIssueDetailsTool,
    JiraGetSprintIssuesTool,
    JiraGetUserHistoryTool,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_PLAN_PATH = PROJECT_ROOT / "output" / "plan_epic_backlog.md"
OUTPUT_EXECUTION_PATH = PROJECT_ROOT / "output" / "execute_epic_backlog.md"


def _build_blocks_container() -> gr.Blocks:
    """Create the Blocks container, falling back if the theme kwarg is unsupported."""
    kwargs: Dict[str, Any] = {"title": "Jira AI Assistant"}
    soft_theme = None
    try:
        soft_theme = gr.themes.Soft()
    except AttributeError:
        soft_theme = None

    if soft_theme is not None:
        try:
            return gr.Blocks(theme=soft_theme, **kwargs)
        except TypeError:
            pass
    return gr.Blocks(**kwargs)


def _stringify(data: Any) -> str:
    """Convert crew or tool results into a readable string."""
    if data is None:
        return "No data returned."
    if hasattr(data, "model_dump_json"):
        try:
            return data.model_dump_json(indent=2)
        except TypeError:
            return data.model_dump_json()
    if hasattr(data, "model_dump"):
        return json.dumps(data.model_dump(), indent=2, default=str)
    if isinstance(data, (dict, list)):
        return json.dumps(data, indent=2, default=str)
    return str(data)


def _read_output_file(path: Path) -> str:
    """Read helper to surface plan/execution artifacts."""
    if path.exists():
        try:
            return path.read_text(encoding="utf-8")
        except OSError as exc:  # pragma: no cover - UI helper
            return f"Could not read {path.name}: {exc}"
    return f"No output written yet at {path}"


def _merge_inputs(project_key: str, epic_key: str, extra_inputs: str) -> Dict[str, Any]:
    base_inputs: Dict[str, Any] = {
        "project_key": (project_key or "").strip(),
        "epic_key": (epic_key or "").strip(),
    }
    if not base_inputs["project_key"] or not base_inputs["epic_key"]:
        raise gr.Error("Project key and epic key are both required.")

    if extra_inputs and extra_inputs.strip():
        try:
            parsed = json.loads(extra_inputs)
        except json.JSONDecodeError as exc:
            raise gr.Error(f"Could not parse additional inputs as JSON: {exc}") from exc
        if not isinstance(parsed, dict):
            raise gr.Error("Additional inputs must be a JSON object.")
        base_inputs.update(parsed)
    return base_inputs


def kickoff_assistant(project_key: str, epic_key: str, extra_inputs: str) -> tuple[str, str, str, str]:
    """Trigger the crew run and surface status plus latest markdown outputs."""
    inputs = _merge_inputs(project_key, epic_key, extra_inputs)
    crew = JiraAiAssistant().crew()

    start_time = time.time()
    try:
        result = crew.kickoff(inputs=inputs)
    except Exception as exc:  # pragma: no cover - exercised via UI
        raise gr.Error(f"Failed to run the crew: {exc}") from exc
    elapsed = time.time() - start_time
    status = f"Completed run in {elapsed:0.1f}s at {datetime.now():%Y-%m-%d %H:%M:%S}"

    return (
        status,
        _stringify(result),
        _read_output_file(OUTPUT_PLAN_PATH),
        _read_output_file(OUTPUT_EXECUTION_PATH),
    )


def refresh_outputs() -> tuple[str, str]:
    """Re-read persisted markdown files without a full rerun."""
    return (
        _read_output_file(OUTPUT_PLAN_PATH),
        _read_output_file(OUTPUT_EXECUTION_PATH),
    )


def fetch_epics(project_key: str) -> str:
    project = (project_key or "").strip()
    if not project:
        raise gr.Error("Provide a project key to load epics.")
    data = JiraGetAllEpicsTool()._run(project_key=project)
    return _stringify(data)


def fetch_users(project_key: str) -> str:
    project = (project_key or "").strip()
    if not project:
        raise gr.Error("Provide a project key to list assignable users.")
    return _stringify(JiraGetAllUsersTool()._run(project_key=project))


def fetch_sprints(project_key: str) -> str:
    project = (project_key or "").strip()
    if not project:
        raise gr.Error("Provide a project key to inspect sprints.")
    return _stringify(JiraGetAllSprintsTool()._run(project_key=project))


def fetch_project_issues(project_key: str, epic_filter: str) -> str:
    project = (project_key or "").strip()
    if not project:
        raise gr.Error("Provide a project key to list issues.")
    epic = (epic_filter or "").strip() or None
    data = JiraGetAllIssuesWithDetailsTool()._run(project_key=project, epic_key=epic)
    return _stringify(data)


def fetch_issue(issue_key: str) -> str:
    issue = (issue_key or "").strip()
    if not issue:
        raise gr.Error("Provide an issue key to inspect issue details.")
    return _stringify(JiraGetIssueDetailsTool()._run(issue_key=issue))


def fetch_user_history(account_id: str) -> str:
    account = (account_id or "").strip()
    if not account:
        raise gr.Error("Provide an account ID to pull history.")
    return _stringify(JiraGetUserHistoryTool()._run(account_id=account))


def fetch_sprint_issues(sprint_id_text: str) -> str:
    sprint_id_text = (sprint_id_text or "").strip()
    if not sprint_id_text:
        raise gr.Error("Provide a sprint ID.")
    try:
        sprint_id = int(sprint_id_text)
    except ValueError as exc:
        raise gr.Error("Sprint ID must be a number returned by Jira.") from exc
    return _stringify(JiraGetSprintIssuesTool()._run(sprint_id=sprint_id))


def build_interface() -> gr.Blocks:
    """Configure the full UI."""
    blocks = _build_blocks_container()
    with blocks as demo:
        gr.Markdown(
            """
            # Jira AI Assistant Control Center
            Launch the full crew, inspect generated backlog artifacts, and query Jira data from one place.
            """
        )

        with gr.Tab("Run Assistant"):
            with gr.Row():
                project_key_box = gr.Textbox(label="Project Key", placeholder="e.g. MH", autofocus=True)
                epic_key_box = gr.Textbox(label="Epic Key", placeholder="e.g. MH-3")
            run_button = gr.Button("Run Your AI JIRA Assistant!", variant="primary")
            run_status = gr.Textbox(label="Status", interactive=False)
            result_display = gr.Code(label="Crew Result", language="json")
            plan_display = gr.Textbox(label="Latest plan_epic_backlog.md", lines=14)
            exec_display = gr.Textbox(label="Latest execute_epic_backlog.md", lines=14)

            run_button.click(
                kickoff_assistant,
                inputs=[project_key_box, epic_key_box],
                outputs=[run_status, result_display, plan_display, exec_display],
                queue=True,
            )

        with gr.Tab("Outputs Overview"):
            refresh_button = gr.Button("Refresh from disk")
            plan_view = gr.Textbox(label="Plan Output", lines=16)
            exec_view = gr.Textbox(label="Execution Output", lines=16)
            refresh_button.click(refresh_outputs, outputs=[plan_view, exec_view], queue=False)

        with gr.Tab("Jira Utilities"):
            with gr.Accordion("Project Context", open=True):
                project_util_box = gr.Textbox(label="Project Key", placeholder="Same as above")
                epic_filter_box = gr.Textbox(label="Epic Filter (optional)", placeholder="MH-3")
                with gr.Row():
                    list_epics_btn = gr.Button("List Epics")
                    list_users_btn = gr.Button("List Assignable Users")
                with gr.Row():
                    epics_output = gr.Code(label="Epics", language="json", scale=1)
                    users_output = gr.Code(label="Assignable Users", language="json", scale=1)
                with gr.Row():
                    list_issues_btn = gr.Button("List Project Issues")
                    list_sprints_btn = gr.Button("List Project Sprints")
                with gr.Row():
                    issues_output = gr.Code(label="Project Issues", language="json", scale=1)
                    sprints_output = gr.Code(label="Sprints", language="json", scale=1)

                list_epics_btn.click(fetch_epics, inputs=[project_util_box], outputs=[epics_output])
                list_users_btn.click(fetch_users, inputs=[project_util_box], outputs=[users_output])
                list_issues_btn.click(
                    fetch_project_issues,
                    inputs=[project_util_box, epic_filter_box],
                    outputs=[issues_output],
                )
                list_sprints_btn.click(fetch_sprints, inputs=[project_util_box], outputs=[sprints_output])

            with gr.Accordion("Issue & Sprint Inspectors", open=False):
                issue_box = gr.Textbox(label="Issue Key", placeholder="MH-9")
                sprint_id_box = gr.Textbox(label="Sprint ID", placeholder="123")
                account_box = gr.Textbox(label="Account ID", placeholder="5fcfd938e40b82006e36206f")
                issue_out = gr.Code(label="Issue Details", language="json")
                sprint_out = gr.Code(label="Sprint Issues", language="json")
                user_history_out = gr.Code(label="User History", language="json")

                gr.Button("Fetch Issue Details").click(fetch_issue, inputs=[issue_box], outputs=[issue_out])
                gr.Button("Fetch Sprint Issues").click(
                    fetch_sprint_issues, inputs=[sprint_id_box], outputs=[sprint_out]
                )
                gr.Button("Fetch User History").click(
                    fetch_user_history,
                    inputs=[account_box],
                    outputs=[user_history_out],
                )

        demo.queue(max_size=8, default_concurrency_limit=2)
    return demo


def launch(**launch_kwargs: Any) -> None:
    """Entrypoint used by the CLI script."""
    interface = build_interface()
    interface.launch(**launch_kwargs)
