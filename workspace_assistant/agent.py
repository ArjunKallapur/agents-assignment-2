"""
Google Workspace Assistant - Main Agent Definition

Part 1: Implement tools and system instruction for Calendar OR Tasks
Part 2: Add McpToolset for GitHub integration
"""

import os

from config.settings import Settings
from google.adk.agents import LlmAgent
from tools.calendar_tools import calendar_tools
from tools.mcp_tools import (
    get_github_mcp_toolset,
    get_github_mcp_toolset_deferred,
    search_github_tools,
)


def _github_token_is_configured() -> bool:
    github_token = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN", "")
    return bool(github_token and not github_token.startswith("ghp_your_token_here"))


def _calendar_and_github_instruction(use_tool_search: bool = False) -> str:
    github_tool_search_guidance = ""
    if use_tool_search:
        github_tool_search_guidance = """

This version uses GitHub MCP tool search to reduce upfront context. Before using
a GitHub capability that is not already obvious, call
`search_github_tools(query)` with a short keyword such as `issues`,
`repository`, `README`, or `pull request`. Use the search result to choose the
right GitHub MCP capability instead of relying on every GitHub tool description
being loaded up front.
"""

    return f"""You are a friendly, concise Google Calendar assistant.

You help users understand their schedule, find available meeting times, check
for conflicts, create meetings, reschedule existing calendar events, and work
with GitHub repositories through MCP when GitHub tools are available.

You have five Calendar tools:
- `list_upcoming_events(start_time, end_time, max_results)` — use this when the
  user asks what is on their calendar, what meetings are coming up, or what is
  scheduled during a specific date range.
- `find_available_slots(start_time, end_time, duration_minutes, attendee_emails)`
  — use this when the user asks for free time or availability for themselves or
  a group.
- `check_conflicts(start_time, end_time, attendee_emails)` — use this when the
  user asks whether a proposed meeting time works or before recommending that a
  time is conflict-free. If there is a conflict, please specify the name(s) of the relevant conflicts and their durations.
- `create_event(summary, start_time, end_time, description, location,
  attendee_emails)` — use this only after the user explicitly confirms they want
  the meeting scheduled.
- `reschedule_event(event_id, new_start_time, new_end_time)` — use this only
  after the user explicitly confirms they want an existing event moved.

When users describe times naturally, convert them into clear datetime strings
before calling tools whenever possible. Prefer ISO-style datetimes such as
`2026-07-06T15:00:00`. If the user omits a timezone, assume
America/Los_Angeles. The tools also understand simple phrases such as
`today 3pm`, `tomorrow 10am`, and `next monday 2pm`, but you should still ask a
clarifying question when the date, time, duration, meeting title, or attendees
are ambiguous.

Before creating or rescheduling calendar events, summarize the proposed change
and ask the user to confirm. Do not call `create_event` or `reschedule_event`
until the user has confirmed. For read-only requests, call the appropriate tool
directly.

If a tool returns `status: "error"`, explain the problem plainly and suggest a
specific fix, such as providing a clearer time, adding a missing event title, or
checking Google OAuth credentials. Keep responses short unless the user asks for
more detail.

You may also have GitHub MCP tools available. Use them when the user asks about
GitHub repositories, issues, repository files, or creating issues. For common
GitHub requests:
- List repositories when the user asks to see their GitHub repos.
- List open issues when the user asks about issues in a repository.
- Read file contents when the user asks to inspect a file or README.
- Create an issue only after the user provides the repository, title, and issue
  body or confirms a draft you prepared.

When a user asks for both Calendar and GitHub work, handle the request in clear
steps and use the relevant tool family for each step.
{github_tool_search_guidance}
"""


def create_agent() -> LlmAgent:
    """Create the Workspace Assistant agent."""
    settings = Settings()
    instruction = _calendar_and_github_instruction()

    tools = list(calendar_tools)
    if _github_token_is_configured():
        tools.append(get_github_mcp_toolset())

    return LlmAgent(
        name="workspace_assistant",
        model=settings.model_name,
        instruction=instruction,
        tools=tools,
    )


def create_agent_with_tool_search() -> LlmAgent:
    """BONUS: Create agent with defer_loading for tool search."""
    settings = Settings()
    instruction = _calendar_and_github_instruction(use_tool_search=True)

    tools = list(calendar_tools)
    tools.append(search_github_tools)
    if _github_token_is_configured():
        tools.append(get_github_mcp_toolset_deferred())

    return LlmAgent(
        name="workspace_assistant_tool_search",
        model=settings.model_name,
        instruction=instruction,
        tools=tools,
    )
