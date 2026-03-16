# Write-Up

## Why Product Support

I chose Track A because it felt most relevant to the role and has the most real-world value. Support teams at small software companies are expensive to scale, and most of the volume is repetitive — "How do I do X?", "What plan am I on?", "This isn't working." An agent that handles those well and knows when to escalate directly reduces support burden and lets the team focus on harder problems.

## Key Design Decisions

**Knowledge base as markdown, not hardcoded responses.** Help content lives in markdown files organized by topic, split into ~24 searchable chunks at startup. Improving the agent's answers is a content edit, not a code change — and the KB is auditable and version-controlled.

**Keyword search over vector embeddings.** At ~24 chunks, keyword search with stop word filtering and heading-match boosting is fast, predictable, and good enough. A vector DB would add infrastructure complexity without meaningfully improving retrieval at this scale.

**Real escalation via email.** When the agent can't resolve an issue, it creates a support ticket in the database and sends a structured context summary to the support team via Postmark, CC'ing the user.

**Mock customer context for personalization.** Each demo user gets a generated customer account (clinic name, plan, seats, billing cycle, past tickets). The system prompt is injected with this data so the agent gives specific answers ("Your next bill is March 28") rather than generic ones.

**Streaming and markdown rendering.** Responses stream token-by-token via SSE with real-time markdown rendering. For a support agent, perceived responsiveness matters.

## Tradeoffs

**Single agent vs. specialist routing.** One agent with tool-routing instructions in the system prompt is simpler and works at this scope, but a production system would benefit from dedicated agents for billing, technical, and sales that can be tuned independently.

**Markdown KB vs. CMS.** Markdown files are easy to write and version-control but don't scale if non-technical team members need to update content. A real product would move to a lightweight CMS or admin UI.

**No feedback loop.** The agent has no way to learn which responses were helpful. Thumbs up/down and resolution tracking would be the fastest way to improve quality.

## What I'd Build Next

Vector search for retrieval as the KB grows, ticket status tracking in the UI, a resolution feedback mechanism, and multi-agent routing — a classifier that sends billing, technical, and upgrade questions to specialist agents with their own tuned prompts and tool access.
