# ClinicSoft Support Agent

A conversational AI agent that handles product support for dental/medical clinic practice management software. Built as part of a role assessment for [Harbor](https://harborautomation.com).

**[Try the live demo →](https://v2.harborautomation.com/clinic-agent)**

---

## What It Does

Clinic staff (office managers, front desk) interact with the agent to get help with their practice management software. The agent handles multi-step conversations across five categories:

- **Software questions** — "How do I add a provider to the schedule?", "Where's the insurance tab?"
- **Billing & plans** — "What plan am I on?", "Why was I charged twice?"
- **Troubleshooting** — "Claims aren't submitting", "I can't see yesterday's appointments"
- **Upgrades** — Plan comparisons, upgrade paths, seat changes
- **Escalation** — Detects unresolvable issues, summarizes context, creates a support ticket, and emails the support team (CC'ing the user)

The agent is grounded in a knowledge base of help articles and has access to mock customer account data, so responses are personalized ("You're on the Standard plan with 3 seats") rather than generic.

## Live Demo

The fastest way to evaluate this is the deployed version:

1. Go to [v2.harborautomation.com/clinic-agent](https://v2.harborautomation.com/clinic-agent)
2. Click **Try the Demo** → sign up with any email (via Auth0)
3. Complete the short setup form
4. You'll land in the chat with a personalized welcome message

**Things to try:**
- Ask a software question ("How do I export a report?")
- Ask about your plan or billing ("What plan am I on?", "When's my next bill?")
- Trigger troubleshooting and then escalation ("Claims aren't submitting" → "I already tried that, still broken" → "still not working")
- Ask something off-topic ("What's the weather?") to see the guardrails
- Check the **Customer Account** panel on the right for your mock account and support ticket history

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | SvelteKit |
| Backend | FastAPI (Python) |
| Database | PostgreSQL |
| AI | Anthropic API (Claude) |
| Auth | Auth0 |
| Email | Postmark |
| Hosting | Render |

## Architecture

```
┌─────────────────────────────────────────────┐
│  SvelteKit Frontend                         │
│  Chat UI · Account Panel · Landing Page     │
└──────────────┬──────────────────────────────┘
               │ SSE streaming
┌──────────────▼──────────────────────────────┐
│  FastAPI Backend                            │
│                                             │
│  ┌─────────────┐  ┌──────────────────────┐  │
│  │ Chat Engine │  │ Tool Executor        │  │
│  │ (streaming) │──│  search_help_articles│  │
│  │             │  │  get_account_info    │  │
│  │  System     │  │  get_billing_history │  │
│  │  Prompt +   │  │  check_upgrade_opts  │  │
│  │  Account    │  │  list_support_tickets│  │
│  │  Context    │  │  create_support_ticket│ │
│  │             │  │  escalate_to_human   │  │
│  └─────────────┘  └──────┬───────────────┘  │
│                          │                  │
│  ┌───────────────┐  ┌────▼───────────────┐  │
│  │ Knowledge Base│  │ PostgreSQL         │  │
│  │ (markdown)    │  │ Accounts · Tickets │  │
│  └───────────────┘  │ Conversations      │  │
│                     └────────────────────┘  │
│                          │                  │
│                     ┌────▼───────────────┐  │
│                     │ Postmark           │  │
│                     │ (escalation email) │  │
│                     └────────────────────┘  │
└─────────────────────────────────────────────┘
```

## About This Repo

This is a curated extract of the agent-specific code from a larger production platform ([Harbor](https://harborautomation.com)). It includes everything that makes the agent work — the chat engine, tool schemas, tool execution, knowledge base, data models, system prompt, and the full frontend — but omits platform-level infrastructure like auth, deployment config, and shared utilities.

**The live demo is the best way to evaluate the agent end-to-end.** This repo is for reviewing the code.

```
backend/
├── Dockerfile
├── requirements.txt
├── scripts/
│   └── seed_clinic_agent_prompt.py        # System prompt seed script
└── src/
    ├── db/
    │   ├── session.py                     # DB session setup
    │   └── models/clinic/
    │       ├── __init__.py
    │       ├── clinic_conversation.py
    │       ├── clinic_customer_account.py
    │       ├── clinic_message.py
    │       └── clinic_support_ticket.py
    ├── integrations/
    │   └── anthropic.py                   # Anthropic client setup
    ├── knowledge_bases/clinic_agent/
    │   ├── billing-faq.md
    │   ├── patient-records.md
    │   ├── plans-and-upgrading.md
    │   └── scheduling.md
    ├── repositories/clinic/
    │   ├── __init__.py
    │   ├── clinic_conversations.py
    │   ├── clinic_customer_accounts.py
    │   └── clinic_support_tickets.py
    └── services/solutions/clinic_agent/
        ├── chat.py                        # Chat endpoint, streaming, tool call loop
        ├── kb_loader.py                   # KB loader + keyword search w/ heading boost
        ├── sample_data.py                 # Demo account generator
        ├── tool_executor.py               # Dispatch + Postmark escalation emails
        └── tools.py                       # 7 Anthropic tool schemas

frontend/
├── Dockerfile
├── package.json
├── svelte.config.js
├── vite.config.js
└── src/
    ├── app.css
    ├── app.html
    ├── lib/clinic-agent/
    │   ├── ClinicChatView.svelte          # Main chat component
    │   └── styles.css
    └── routes/clinic-agent/
        ├── +layout.server.ts              # Route guard
        ├── +page.svelte                   # Landing page
        ├── chat/+page.svelte              # Chat view
        └── setup/
            ├── +page.server.ts
            ├── +page.svelte               # Onboarding form
            └── setup.css
```

## Key Design Decisions

- **Knowledge base over hardcoded responses.** Help articles live as markdown files organized by topic, searched with keyword matching and heading-boost scoring. This means the agent's answers improve by editing a text file, not code.
- **Real escalation via email.** When the agent can't resolve an issue, it creates a support ticket in the DB and sends a structured summary to the support team via Postmark, CC'ing the user. This is a real action, not a simulated one.
- **Mock customer context for personalization.** Each demo user gets a customer account (plan, seats, billing cycle) so the agent can give specific answers ("Your next bill is March 28") instead of generic ones.
- **Keyword search over vector DB.** For a knowledge base of ~24 chunks, keyword search with stop word filtering and heading-match boosting is fast, predictable, and good enough. A vector DB would be the right move at scale but adds complexity without meaningfully improving results at this size.
- **Streaming for responsiveness.** Responses stream token-by-token via SSE. The frontend renders markdown in real time, so the agent feels conversational rather than batch-response.

## What I'd Build Next

- **Vector search** — replace keyword matching as the KB grows beyond what keyword search handles well
- **Ticket tracking in the UI** — let users see status updates on their escalated tickets
- **Analytics on common questions** — identify KB gaps from conversation patterns
- **Multi-agent routing** — specialist agents for billing vs. technical vs. sales, with a router deciding who handles each message
- **Resolution feedback loop** — thumbs up/down on agent responses to measure and improve quality

## Author

Built by [Your Name] — [your email or portfolio link]
