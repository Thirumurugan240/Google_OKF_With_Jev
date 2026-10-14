# OKF + Jev + CrewAI (OpenAI)

A beginner friendly AI agent that answers questions about your company
using **your own company knowledge**, not guesses.

It combines three things:

| Part | What it is | Job in this project |
|---|---|---|
| **OKF** (Open Knowledge Format, by Google Cloud) | A folder of Markdown files with YAML frontmatter | The source of truth: metrics, tables, runbooks |
| **Jev** (by TypeSafe) | A decision model. It does not write text, it picks options and gives a confidence score | Picks the right knowledge file and decides if the question is simple or hard |
| **CrewAI + OpenAI** | An agent framework running a text LLM | Reads the knowledge files and writes the final answer |

**Main idea:** the cheap, fast model (Jev) decides. The expensive model (OpenAI) only writes.
OKF makes sure both use your company's real definitions.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│  STEP 0: LOAD (once, at startup)                             │
│  company-knowledge/*.md  ──►  read frontmatter  ──►  docs{}   │
└──────────────────────────────────────────────────────────────┘
                              │
        User types a question ▼
┌──────────────────────────────────────────────────────────────┐
│  STEP 1: JEV DECIDES (one API call, under a second)          │
│    Question A: Which knowledge file is relevant?             │
│                options = descriptions of all files + "none"  │
│    Question B: Is this "simple" or "super"?                  │
│    Jev returns: choice + confidence for each                 │
└──────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│  STEP 2: PYTHON ROUTES (plain if/else, no AI)                │
│    simple  ──►  gpt-5.4-mini                                 │
│    super   ──►  gpt-5.4                                      │
│    confidence >= 0.7  ──►  picked file + its linked files    │
│    confidence <  0.7  ──►  all files (let the agent decide)  │
└──────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│  STEP 3: CREWAI AGENT ANSWERS (OpenAI model)                 │
│    Gets: the question + the chosen knowledge files           │
│    Rule: answer ONLY from the files, never guess             │
└──────────────────────────────────────────────────────────────┘
                              │
                              ▼
                     Answer printed on screen
```

---

## Example run

```
Ask a question (or type 'exit'): How do we calculate monthly revenue?

[Jev] File : monthly_revenue | confidence: 0.91
[Jev] Level: simple | confidence: 0.84
[Route] Model: gpt-5.4-mini
[Route] Files: ['monthly_revenue', 'orders']

========== ANSWER ==========
Monthly revenue is the sum of `amount` from the `orders` table where
status = 'completed'. Refunds and cancelled orders are not counted.
Do not use `orders_old`, it is deprecated.
(Sources: monthly_revenue, orders)
```

Notice the `orders` file was included automatically because
`monthly-revenue.md` links to it in its frontmatter.

---

## Folder structure

```
okf_with_jev/
├── app.py                      the whole program (no classes, no functions)
├── README.md                   this file
├── .env                        your API keys (you create this)
└── company-knowledge/          the OKF bundle
    ├── index.md                map of all files (type: index)
    ├── log.md                  append-only history of changes (type: log)
    ├── metrics/
    │   └── monthly-revenue.md
    ├── tables/
    │   └── orders.md
    └── runbooks/
        └── refund-process.md
```

---

## What an OKF file looks like

Each file describes **one concept**. The part between `---` lines is the frontmatter.

```markdown
---
type: metric
name: Monthly Revenue
description: How monthly revenue is calculated and which rules apply
owner: finance-team
links: [orders]
---

# Monthly Revenue
Sum of `amount` from orders where status = 'completed'...
```

| Field | Used for |
|---|---|
| `description` | Jev reads this to decide if the file matches the question. Write it clearly. |
| `links` | Related files, which the agent also gets. Use the file name with `_` instead of `-`, and no `.md` (`refund-process.md` becomes `refund_process`). |
| `type`, `name`, `owner` | Information for humans and the agent |

**To add knowledge:** drop a new `.md` file anywhere inside `company-knowledge/`
and restart the app. You don't need to change any code.

---

## Setup

### 1. Create a virtual environment (inside this folder)

```powershell
cd C:\Users\THIRU\OneDrive\Desktop\ai_youtube\okf_with_jev
python -m venv .venv
.venv\Scripts\activate
```

### 2. Install packages

```powershell
pip install crewai typesafe-sdk pyyaml python-dotenv
```

### 3. Create a `.env` file

```
OPENAI_API_KEY=sk-...
TYPESAFE_API_KEY=sk-...
```

### 4. Run

```powershell
python app.py
```

Type `exit` to quit.

---

## Settings you can change (top of app.py)

| Setting | Default | Meaning |
|---|---|---|
| `SIMPLE_MODEL` | `gpt-5.4-mini` | OpenAI model for simple questions |
| `SUPER_MODEL` | `gpt-5.4` | OpenAI model for hard questions |
| `MIN_CONFIDENCE` | `0.7` | Jev's file pick is trusted only above this |

---

## Why use Jev instead of keyword matching?

| Keyword matching | Jev |
|---|---|
| "revenue" in the question picks the revenue file | Understands meaning, for example "how much did we earn" matches the revenue file too |
| No idea when it is wrong | Returns a confidence score, so we can fall back safely |
| Needs a list of words for each case | Just give it the options and their descriptions |

Jev is also very fast (about 70 to 500 ms) and cheap (about $0.042 per million input tokens, output is free).

---

## Limits and notes

- Jev's `Choice` supports up to 255 options. For a very large knowledge base, let Jev pick a folder first, then a file.
- Jev's state limit is about 32k tokens, which is plenty for one question.
- When confidence is low, **all** files go to the agent. That's fine for a small bundle, but a large one would make the prompt too long.
- Check that the OpenAI model IDs above match the current OpenAI models page.
- The Jev SDK names (`typesafe-sdk`, `system_one`, `Choice`, `.choice`, `.confidence`) are taken from public guides. Check them against TypeSafe's official docs if anything fails.
