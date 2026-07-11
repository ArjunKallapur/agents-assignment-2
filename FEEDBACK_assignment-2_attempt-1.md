## Grade: 100 / 100

**Assignment:** Google Workspace Assistant + GitHub MCP (ADK)  
**Attempt:** 1 of 2  ·  **Graded:** 2026-07-11  ·  Commit `14f3496`

### Score breakdown
| Criterion | Max | Earned | Notes |
|-----------|-----|--------|-------|
| tool_design | 18 | 18 | Five Calendar tools (list_upcoming_events, find_available_slots, create_event, check_conflicts, reschedule_event) as plain functions with action-oriented names, complete Args/Returns docstrings, and typed parameters, all collected into the calendar_tools list (calendar_tools.py:410). Well above the 3-tool minimum. (`workspace_assistant/tools/calendar_tools.py:410`) |
| agent_instructions | 14 | 14 | System instruction is clear and scoped: it enumerates each tool with when-to-use guidance, sets timezone defaults, and enforces safe behavior by requiring confirmation before create_event/reschedule_event while allowing read-only tools to run directly (agent.py:68-71). (`workspace_assistant/agent.py:38`) |
| error_handling | 14 | 14 | Every tool wraps API calls in try/except and returns {status, message} dicts. Edge cases are validated (empty title, end<=start, non-positive duration, missing event_id) and _friendly_google_error (calendar_tools.py:129) converts HttpError/FileNotFoundError into readable messages instead of stack traces. (`workspace_assistant/tools/calendar_tools.py:177`) |
| functionality | 14 | 14 | Tools call the correct Calendar v3 API via get_calendar_service (auth.py:44): events().list, freebusy().query, events().insert, events().get/update. find_available_slots correctly computes free gaps between sorted busy blocks (calendar_tools.py:232-244); reschedule_event fetches then updates the event. Statically correct. (`workspace_assistant/tools/calendar_tools.py:173`) |
| code_quality | 10 | 10 | Readable, well-organized code with shared helpers (_parse_datetime, _event_summary, _friendly_google_error) and clear docstrings; tools wired into an LlmAgent via create_agent() (agent.py:93-107). (`workspace_assistant/agent.py:93`) |
| mcp_configured | 10 | 10 | McpToolset configured correctly for the GitHub MCP server over stdio (npx @modelcontextprotocol/server-github) via StdioServerParameters/StdioConnectionParams (mcp_tools.py:108-141) and attached to the agent when a token is configured (agent.py:99-100). (`workspace_assistant/tools/mcp_tools.py:116`) |
| github_queries | 15 | 15 | The GitHub MCP toolset is wired into the agent unfiltered, exposing repo/issue/PR/file operations; the instruction (agent.py:78-88) and reflection describe listing repos, reading files, listing/creating issues. Statically the queries route correctly through the McpToolset. (`workspace_assistant/agent.py:99`) |
| mcp_error_handling | 5 | 5 | Missing/placeholder token is handled gracefully: _github_server_params raises a clear ValueError (mcp_tools.py:110-111) and _github_token_is_configured (agent.py:20) guards attachment so a missing token degrades to Calendar-only rather than crashing. (`workspace_assistant/tools/mcp_tools.py:108`) |
| _bonus_ | +25 | +25 | |
| Integrity deduction | — | 0 | Provided files unmodified |
| **Total** | **100** | **100** | |

### What went well
- Implemented all five Calendar tools (well beyond the 3-tool minimum) with consistent {status, message} contracts, action-oriented names, and complete typed docstrings.
- Consistent, defensive error handling across every tool: input validation for edge cases plus a shared _friendly_google_error helper that hides raw stack traces.
- Completed all three bonus components correctly: search_github_tools, defer_loading=True (handled version-safely), and create_agent_with_tool_search with a reflection comparison.
- Clear, scoped agent instruction that enforces confirmation before write actions (create/reschedule) while letting read-only tools run directly.

### What to improve (actionable)
- The bonus token comparison in the reflection uses self-estimated numbers (~5K vs ~3K); an actual measured before/after context size would strengthen the analysis.
- MCP error handling covers the missing-token case but not runtime failures of the MCP server (e.g. npx unavailable or server crash) — consider wrapping toolset startup.
- Timezone is hard-coded to America/Los_Angeles (calendar_tools.py:12), which the student notes; making it configurable would handle traveling users and cross-timezone attendees.
- check_conflicts returns busy blocks but not event titles/names, which the student flagged as an unresolved limitation in the reflection.

### Automated checks
- ✅ All required files implemented
- ✅ Provided files unmodified
- ✅ 0/0 output artifacts committed
- ✅ Reflection 920 words

### Resubmission
You may resubmit **once**. Push fixes to this repo, then notify the instructor; we'll re-grade as **Attempt 2 (final)**. This is attempt 1 of 2.

---
*Graded automatically with Claude Code against the course rubric. Questions → contact the instructor.*


---
<sub>🔎 **Autograder record** — attempt 1 of 2 · graded at commit `14f3496` · delivered 2026-07-11T18:00:55Z. Commits pushed to `main` after this timestamp are treated as a resubmission.</sub>
