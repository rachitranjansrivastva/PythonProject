"""
AI Assistant - Major Project for Prompt Engineering (VaultofCodes)

A command-line AI Assistant with four functions (answering questions,
summarizing text, generating creative content, and giving advice), three
distinct, purpose-designed prompts per function, and a feedback loop that
logs ratings and nudges the user toward a better-performing prompt style
when one keeps getting rated "not helpful".

Setup (pick ONE provider):

    Option A - Gemini (FREE, no credit card, ~1,500 requests/day):
        pip install google-genai
        Get a key at https://aistudio.google.com/apikey (sign in with Google)
        Set the GEMINI_API_KEY environment variable to your key.

    Option B - OpenAI (paid, needs billing set up):
        pip install openai
        Set the OPENAI_API_KEY environment variable to your key.

    Without either key set, the assistant runs in DEMO MODE so you can still
    test the full flow (menus, prompts, feedback logging) at no cost.

    Windows (cmd):         set GEMINI_API_KEY=your-key-here
    Windows (PowerShell):  $env:GEMINI_API_KEY="your-key-here"
    macOS / Linux:         export GEMINI_API_KEY=your-key-here

    If both keys happen to be set, Gemini is used first (see
    get_active_provider() below) since it's the free option.
"""

import os
import csv
import datetime

OPENAI_MODEL = "gpt-4o-mini"          # change to any chat model your OpenAI key has access to

# Google renames/retires Gemini model IDs fairly often, and a key that works
# for one model can 404 on another (e.g. "no longer available to new users").
# Try each candidate in order and fall through to the next on a 404 instead
# of hardcoding a single model name that might go stale.
GEMINI_MODEL_CANDIDATES = ["gemini-3.6-flash", "gemini-2.5-flash-lite", "gemini-2.5-flash"]

FEEDBACK_FILE = "feedback_log.csv"

# ---------------------------------------------------------------------------
# Prompt design: 4 functions x 3 purpose-built prompt styles each.
# Styles are varied deliberately by length, specificity, tone, and complexity.
# ---------------------------------------------------------------------------

PROMPT_TEMPLATES = {
    "answer": {
        "1": {"name": "Quick Fact",
              "template": "Answer this question in one direct, factual sentence: {input}"},
        "2": {"name": "Detailed Explanation",
              "template": "Answer this question thoroughly. Include relevant context and one "
                           "concrete example: {input}"},
        "3": {"name": "Simple / ELI5",
              "template": "Explain the answer to this question in a friendly, casual tone, as "
                           "if explaining it to someone completely new to the topic: {input}"},
    },
    "summarize": {
        "1": {"name": "Quick Summary",
              "template": "Summarize the following text in 2-3 sentences:\n\n{input}"},
        "2": {"name": "Detailed Summary",
              "template": "Summarize the following text in a structured paragraph, covering "
                           "the main points and any conclusions:\n\n{input}"},
        "3": {"name": "Bullet Points",
              "template": "Summarize the following text as a bulleted list of the key "
                           "takeaways:\n\n{input}"},
    },
    "creative": {
        "1": {"name": "Short Story",
              "template": "Write a short, imaginative story (150-200 words) based on this "
                           "idea: {input}"},
        "2": {"name": "Poem",
              "template": "Write a short poem (4-8 lines) inspired by this theme: {input}"},
        "3": {"name": "Essay Opening",
              "template": "Write an engaging opening paragraph for an essay about: {input}"},
    },
    "advice": {
        "1": {"name": "Quick Tip",
              "template": "Give me one practical, actionable tip about: {input}"},
        "2": {"name": "Step-by-Step Plan",
              "template": "Give me a clear, step-by-step plan (4-5 steps) for: {input}"},
        "3": {"name": "Friendly Mentor",
              "template": "As a supportive mentor, give me encouraging and practical advice "
                           "about: {input}"},
    },
}

FUNCTION_NAMES = {
    "answer": "Answer a Question",
    "summarize": "Summarize Text",
    "creative": "Generate Creative Content",
    "advice": "Get Advice on a Topic",
}

FUNCTION_INPUT_LABELS = {
    "answer": "your question",
    "creative": "your topic or idea",
    "advice": "the topic you'd like advice on",
}


# ---------------------------------------------------------------------------
# AI call (with a transparent demo-mode fallback so the assistant is fully
# testable without an API key)
# ---------------------------------------------------------------------------

def demo_response(prompt):
    preview = prompt if len(prompt) <= 200 else prompt[:200] + "..."
    return (
        "[DEMO MODE - no working API key found]\n"
        "  This is a placeholder so you can test the assistant's full flow without an API key.\n"
        "  Set GEMINI_API_KEY (free) or OPENAI_API_KEY to get a real AI-generated response\n"
        "  to the prompt below:\n"
        f'  "{preview}"'
    )


def get_active_provider():
    """Gemini is checked first since it's the free, no-credit-card option."""
    if os.environ.get("GEMINI_API_KEY"):
        return "gemini"
    if os.environ.get("OPENAI_API_KEY"):
        return "openai"
    return None


def call_gemini(prompt):
    try:
        from google import genai
    except ImportError as e:
        return f"[google-genai not installed: {e}]\n\n" + demo_response(prompt), False

    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    last_error = None
    for model_name in GEMINI_MODEL_CANDIDATES:
        try:
            response = client.models.generate_content(model=model_name, contents=prompt)
            return response.text.strip(), True
        except Exception as e:
            last_error = e
            # A missing/renamed model (404) is worth retrying with the next
            # candidate. Anything else (e.g. a bad API key) won't be fixed
            # by trying a different model, so stop immediately.
            if "NOT_FOUND" not in str(e) and "404" not in str(e):
                break
    return f"[Error calling Gemini API: {last_error}]\n\n" + demo_response(prompt), False


def call_openai(prompt):
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=400,
            temperature=0.7,
        )
        return response.choices[0].message.content.strip(), True
    except Exception as e:
        return f"[Error calling OpenAI API: {e}]\n\n" + demo_response(prompt), False


def call_ai_model(prompt):
    """Returns (response_text, is_live). Falls back to demo mode on missing
    key or any API error, so the assistant never crashes on a bad connection."""
    provider = get_active_provider()
    if provider == "gemini":
        return call_gemini(prompt)
    if provider == "openai":
        return call_openai(prompt)
    return demo_response(prompt), False


# ---------------------------------------------------------------------------
# Feedback loop: logs every rating to a CSV, and once a specific prompt
# style has collected repeated "not helpful" feedback for a function, the
# assistant proactively suggests switching styles.
# ---------------------------------------------------------------------------

def log_feedback(function_key, style_name, helpful, comment=""):
    file_exists = os.path.isfile(FEEDBACK_FILE)
    with open(FEEDBACK_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["timestamp", "function", "prompt_style", "helpful", "comment"])
        writer.writerow([
            datetime.datetime.now().isoformat(timespec="seconds"),
            FUNCTION_NAMES[function_key],
            style_name,
            "yes" if helpful else "no",
            comment,
        ])


def suggest_improvement(function_key, style_name):
    if not os.path.isfile(FEEDBACK_FILE):
        return
    no_count = 0
    with open(FEEDBACK_FILE, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if (row["function"] == FUNCTION_NAMES[function_key]
                    and row["prompt_style"] == style_name
                    and row["helpful"] == "no"):
                no_count += 1
    if no_count >= 2:
        alternatives = [v["name"] for v in PROMPT_TEMPLATES[function_key].values()
                         if v["name"] != style_name]
        print(f"\n  Tip: '{style_name}' has gotten repeated 'not helpful' feedback for this "
              f"function.")
        print(f"  Consider trying '{alternatives[0]}' or '{alternatives[1]}' instead next "
              f"time.\n")


def show_feedback_summary():
    if not os.path.isfile(FEEDBACK_FILE):
        print("\n  No feedback recorded yet. Ratings will appear here after you use the "
              "assistant.\n")
        return

    total, helpful_total = 0, 0
    per_function = {}
    with open(FEEDBACK_FILE, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            total += 1
            is_helpful = row["helpful"] == "yes"
            helpful_total += is_helpful
            stats = per_function.setdefault(row["function"], {"total": 0, "helpful": 0})
            stats["total"] += 1
            stats["helpful"] += is_helpful

    print("\n===== FEEDBACK SUMMARY =====")
    print(f"  {helpful_total}/{total} responses marked helpful "
          f"({helpful_total / total * 100:.0f}%)\n")
    for func, stats in per_function.items():
        pct = stats["helpful"] / stats["total"] * 100
        print(f"  {func}: {stats['helpful']}/{stats['total']} helpful ({pct:.0f}%)")
    print()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def get_multiline_input():
    lines = []
    while True:
        line = input()
        if line == "":
            break
        lines.append(line)
    return "\n".join(lines)


def run_function(function_key):
    print(f"\n--- {FUNCTION_NAMES[function_key]} ---")
    styles = PROMPT_TEMPLATES[function_key]
    for k, v in styles.items():
        print(f"  {k}. {v['name']}")
    style_choice = input("Choose a prompt style: ").strip()
    if style_choice not in styles:
        print("  Invalid style choice. Returning to main menu.\n")
        return
    style = styles[style_choice]

    if function_key == "summarize":
        print("  Paste the text to summarize, then press Enter on an empty line when done:")
        user_input = get_multiline_input()
    else:
        label = FUNCTION_INPUT_LABELS[function_key]
        user_input = input(f"  Enter {label}: ").strip()

    if not user_input:
        print("  No input provided. Returning to main menu.\n")
        return

    prompt = style["template"].format(input=user_input)
    print("\n  Thinking...\n")
    response_text, is_live = call_ai_model(prompt)

    print(f"  [{'LIVE' if is_live else 'DEMO'}] Response:")
    print(f"  {response_text}\n")

    fb = input("  Was this response helpful? (yes/no): ").strip().lower()
    helpful = fb in ("y", "yes")
    comment = ""
    if not helpful:
        comment = input("  What could be improved? (press Enter to skip): ").strip()
    log_feedback(function_key, style["name"], helpful, comment)
    if not helpful:
        suggest_improvement(function_key, style["name"])


def show_main_menu():
    print("\n===== AI ASSISTANT =====")
    print("1. Answer a Question")
    print("2. Summarize Text")
    print("3. Generate Creative Content")
    print("4. Get Advice on a Topic")
    print("5. View Feedback Summary")
    print("6. Exit")


def main():
    print("Welcome to your AI Assistant!")
    provider = get_active_provider()
    if provider == "gemini":
        print("Mode: LIVE (using the Gemini API)")
    elif provider == "openai":
        print("Mode: LIVE (using the OpenAI API)")
    else:
        print("Mode: DEMO (set GEMINI_API_KEY - free - or OPENAI_API_KEY to enable real AI responses)")

    key_map = {"1": "answer", "2": "summarize", "3": "creative", "4": "advice"}
    while True:
        show_main_menu()
        choice = input("Select an option: ").strip()
        if choice in key_map:
            run_function(key_map[choice])
        elif choice == "5":
            show_feedback_summary()
        elif choice == "6":
            print("Goodbye!")
            break
        else:
            print("  Invalid choice. Please select 1-6.")


if __name__ == "__main__":
    main()