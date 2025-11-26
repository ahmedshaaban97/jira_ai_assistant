"""
Pydantic output models for CrewAI tasks.
These models define the structured output expected from each task.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


# ============================================================================
# Plan Epic Backlog Output Models
# ============================================================================

class RiskItem(BaseModel):
    """Risk item model for epic planning."""
    id: str = Field(..., description="Unique risk identifier")
    description: str = Field(..., description="Description of the risk")
    impact: str = Field(..., description="Impact assessment (e.g., 'High', 'Medium', 'Low')")
    mitigation: str = Field(..., description="Proposed mitigation strategy")


class BacklogItem(BaseModel):
    """Individual backlog item model."""
    title: str = Field(..., description="Concise issue title")
    type: str = Field(..., description="One of: 'Story', 'Task', 'Bug', 'Sub-task'")
    parent_hint: Optional[str] = Field(None, description="Epic key or parent issue key/name if it should be a Sub-task")
    description: str = Field(..., description="Clear plain-text description, including acceptance criteria")
    labels: Optional[List[str]] = Field(None, description="List of suggested labels")
    components: Optional[List[str]] = Field(None, description="List of suggested components")
    story_points_hint: Optional[int] = Field(None, description="Suggested story points value")
    candidate_assignees: List[str] = Field(default_factory=list, description="Ordered list of accountId or names with reasoning")
    dependency_hints: Optional[List[str]] = Field(None, description="List of titles/keys that should precede this item")
    schedule_hint: Optional[str] = Field(None, description="Suggested start/due date ranges relative to epic timeline")


class PlanEpicBacklogOutput(BaseModel):
    """Output model for plan_epic_backlog task."""
    epic_summary: str = Field(..., description="Short plain-text summary of the epic")
    assumptions: List[str] = Field(default_factory=list, description="List of assumptions about scope, timelines, and capacity")
    risks: List[RiskItem] = Field(default_factory=list, description="List of risk items")
    backlog_items: List[BacklogItem] = Field(default_factory=list, description="Array of backlog items to be created")
    schedule_overview: str = Field(..., description="Plain-text explanation of how work should be sequenced")


# ============================================================================
# Execute Epic Backlog Output Models
# ============================================================================

class CreatedIssue(BaseModel):
    """Model for a created Jira issue."""
    issue_key: str = Field(..., description="Jira issue key (e.g., 'MH-123')")
    issue_type: str = Field(..., description="Type: 'Story', 'Task', 'Bug', 'Sub-task'")
    summary: str = Field(..., description="Final issue summary/title")
    assignee: Optional[str] = Field(None, description="Display name or accountId of assignee")
    start_date: Optional[str] = Field(None, description="Start date in YYYY-MM-DD format or null")
    due_date: Optional[str] = Field(None, description="Due date in YYYY-MM-DD format or null")
    story_points: Optional[int] = Field(None, description="Story points value or null")
    parent_key: Optional[str] = Field(None, description="Parent issue key for sub-tasks, else null")


class UpdatedIssue(BaseModel):
    """Model for an updated Jira issue."""
    issue_key: str = Field(..., description="Jira issue key (e.g., 'MH-123')")
    issue_type: str = Field(..., description="Type: 'Story', 'Task', 'Bug', 'Sub-task'")
    summary: str = Field(..., description="Final issue summary/title")
    assignee: Optional[str] = Field(None, description="Display name or accountId of assignee")
    start_date: Optional[str] = Field(None, description="Start date in YYYY-MM-DD format or null")
    due_date: Optional[str] = Field(None, description="Due date in YYYY-MM-DD format or null")
    story_points: Optional[int] = Field(None, description="Story points value or null")
    parent_key: Optional[str] = Field(None, description="Parent issue key for sub-tasks, else null")
    updated_fields: List[str] = Field(default_factory=list, description="List of fields that were updated")


class CommentAdded(BaseModel):
    """Model for a comment added to a Jira issue."""
    issue_key: str = Field(..., description="Issue key where the comment was added")
    comment_summary: str = Field(..., description="Short description of the comment content (not full text)")


class ExecuteEpicBacklogOutput(BaseModel):
    """Output model for execute_epic_backlog task."""
    epic_key: str = Field(..., description="The epic key being executed")
    created_issues: List[CreatedIssue] = Field(default_factory=list, description="Array of created issues")
    updated_issues: List[UpdatedIssue] = Field(default_factory=list, description="Array of updated issues")
    comments_added: List[CommentAdded] = Field(default_factory=list, description="Array of comments added to issues")
    capacity_notes: str = Field(..., description="Plain-text explanation of capacity and availability considerations")

