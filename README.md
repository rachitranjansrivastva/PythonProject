# AI Assistant

A command-line AI Assistant built for a Prompt Engineering major project. It performs four
distinct tasks, each guided by three purpose-built prompts, and includes a feedback loop
that learns which prompt style actually works.

## Features

- **4 functions:** Answer a Question, Summarize Text, Generate Creative Content, Get Advice
- **12 designed prompts** — 3 per function, deliberately varied by length, tone, and specificity
  (not just reworded versions of the same instruction)
- **Feedback loop** — every response is rated helpful/not helpful, logged to `feedback_log.csv`,
  and the assistant proactively suggests switching prompt styles after repeated negative feedback
- **Runs free** — powered by the Gemini API (no credit card required); OpenAI supported as an
  alternate paid option
- **Demo mode** — runs and is fully testable even with no API key set

## Setup

```bash
pip install -r requirements.txt
```

Get a free Gemini API key at [aistudio.google.com/apikey](https://aistudio.google.com/apikey)
(sign in with any Google account, no card needed), then set it as an environment variable:

```bash
# macOS / Linux
export GEMINI_API_KEY=your-key-here

# Windows (cmd)
set GEMINI_API_KEY=your-key-here

# Windows (PowerShell)
$env:GEMINI_API_KEY="your-key-here"
```

## Run it

```bash
python ai_assistant.py
```

The first line printed confirms the mode:
```
Mode: LIVE (using the Gemini API)
```
If no key is set, it prints `Mode: DEMO` instead and runs on placeholder responses so you can
still test the full menu, prompt, and feedback flow.

## Example

```
===== AI ASSISTANT =====
1. Answer a Question
2. Summarize Text
3. Generate Creative Content
4. Get Advice on a Topic
5. View Feedback Summary
6. Exit
Select an option: 3

--- Generate Creative Content ---
  1. Short Story
  2. Poem
  3. Essay Opening
Choose a prompt style: 1
  Enter your topic or idea: tortoise and rabbit, the famous one

  [LIVE] Response:
  Decades after their legendary race, Silas the Tortoise and Barnaby the Hare
  were no longer rivals; they were business partners...
```

## Why 3 prompt styles per function?

| Function | Style 1 | Style 2 | Style 3 |
|---|---|---|---|
| Answer a Question | Quick Fact | Detailed Explanation | Simple / ELI5 |
| Summarize Text | Quick Summary | Detailed Summary | Bullet Points |
| Generate Creative Content | Short Story | Poem | Essay Opening |
| Get Advice on a Topic | Quick Tip | Step-by-Step Plan | Friendly Mentor |

Each style is a genuinely different prompt structure, not a reworded copy — which is what makes
the feedback loop meaningful: if one style keeps getting rated unhelpful, switching to another
actually changes the kind of response you get.

## Tech

- Python (standard library only, aside from the API client)
- [google-genai](https://pypi.org/project/google-genai/) for Gemini API access
- CSV-based feedback logging, no database required

## Notes

Model names on Gemini's free tier change fairly often. If you hit a `404 NOT_FOUND` error, it's
usually a retired model ID — this project already tries a short fallback list of current model
names automatically before giving up.
