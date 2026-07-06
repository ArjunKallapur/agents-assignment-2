# Assignment 2 Reflection

**Name:** 
Arjun Kallapur
**Option:** 
Option A - Calendar
**Date:** 
July 5, 2026

---

## Tool Design Decisions

### Tools Implemented
1. **list_upcoming_events**: Lists events from the user's calendar given a time range
2. **find_available_slots**: Uses Calendar data to find available time slots.
3. **create_event**: Creates a confirmed calendar meeting with a title, start/end time, optional description, location, and attendees.
4. **check_conflicts**: Checks whether a proposed meeting time has a time conflict with an existing event.
5. **reschedule_event**: Moves an existing calendar event to a new start and end time after the user confirms the change.
6. **GitHub McpToolset**: Connects the agent to the GitHub MCP server so it can list repositories, inspect files, view open issues, and create issues.
7. **search_github_tools**: Searches a local catalog of GitHub MCP tool capabilities so the bonus agent can reduce upfront tool-schema context and load only the most common GitHub tools by default.

### Why These Tools?
Since I was using OpenAI's Codex coding assistant, I was able to quickly
implement the tools, so I chose to implement all options available to me. 

I chose to implement the Calendar tools as that seemed most useful to me, with the most practical applicability. 

### Description Strategy
I wrote the tool descriptions as short contracts that tell the LLM when to use each tool, what information the tool needs, and what it returns. I used action-oriented names like `list`, `find`, `create`, `check`, and `reschedule` so the tool name matches the user's intent. The Calendar descriptions include common scheduling keywords such as "upcoming events," "free time," "availability," "conflicts," "meeting," and "move an event." For write actions like creating or rescheduling events, I also made the descriptions emphasize confirmation so the agent does not modify the calendar too early.

For the GitHub MCP tools, I described the main user-facing capabilities rather than every implementation detail: repositories, issues, file contents, and issue creation. For the bonus tool search pattern, `search_github_tools` uses keywords like "repository," "issues," "README," and "pull request" so the agent can discover the right GitHub capability without loading every MCP tool into context up front.

---

## Challenges Encountered
Since I used Codex, I didn't face coding challenges. Here are the other challenges faced: 

### Challenge 1: Getting the Agent to return data in one turn
- **Problem:** For the `check_conflicts` tool, I couldn't get the tool to return the name of the conflicting meeting along with just if there was a conflict or not
- **Solution:** I tried to fix it by explicitly specifying that the specific conflicts are returned, as well as having the Agent instructions say to return the conflict, but couldn't get it to work consistently. 

### Challenge 2: Context Bloat
- **Problem:** Loading all Github tools bloated the context
- **Solution:** I solved it by implementing the tool search pattern, so that context could be saved. 

---

## Error Handling Approach

My error handling approach was to make sure the tools return structured errors instead of crashing the agent loop. Each Calendar tool uses a `try`/`except` block and returns a dictionary with `status: "success"` or `status: "error"`. When something goes wrong, the tool returns a user-friendly `message` field that the agent can explain back to the user.

I anticipated a few main types of errors: unclear or unsupported date/time input, missing required information like an event title or event ID, and some API failures. For validation errors, the tools return specific messages such as asking for a clearer ISO datetime or explaining that the end time must be after the start time. For Google API or credential errors, the tools convert the exception into a readable message instead of exposing a raw stack trace. 

---

## Ideas for Improvement

If you had more time, what would you add or change?

1. I would add some retry mechanism so that transient API failures can be caught and retried without the user needing to see those
2. I would add a feature to prepare a "daily digest" for the user's meetings coming up that day, and the required preparation for these, such as documents to be read, items to be brought, and so on. This could then be proactively emailed to the user or surfaced as a notification. 
3. I would add more robust error handling to ensure that all input edge cases are adequately handled. As an example, I currently hardcode a preferred timezone, but this approach won't work well if a user is traveling, or if the user wants to schedule events with someone in a different timezone. 

---

## Key Learnings

What did you learn from this assignment about building AI agents?

I think I got a good look at the functionality that can be implemented with AI agents. It's almost magical that with a bit of configuration and plumbing, I was able to implement a working Calendar integration and MCP. 

I also got a good understanding of the importance of how instructions are specified to the agent, and how we have to be careful when writing these as to ensure there are no unintended consequences of our instructions. 

Finally, I got to see just how the tool search functionality can easily save a lot of context bloat. 

---

## Bonus Reflection

| Mode | Tools Loaded | Approx Tokens |
| -------- | -------- | -------- |
| Without `defer_loading`  | All tools  | ~5K tokens |
| With `defer_loading`  | 2 Github tools `search_repositories`, `list_issues` + Calendar tools  | ~3K tokens  |

~40% token savings
