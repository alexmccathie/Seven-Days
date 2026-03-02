/#!/usr/bin/env python3
"""
Seven Days — Automated Weekly Newsletter Generator

Generates a global news briefing using the Claude API (with web search),
converts it to styled HTML, and publishes via the Beehiiv API.

Usage:
    python generate.py                  # Generate + publish (sends to subscribers)
    python generate.py --draft          # Generate + create draft (no send)
    python generate.py --preview        # Generate + save locally only
    python generate.py --date-range "February 19–26, 2026"  # Override date range
"""

import os
import sys
import json
import argparse
import re
from datetime import datetime, timedelta
from pathlib import Path

import anthropic
import requests
import markdown


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

CLAUDE_MODEL = "claude-sonnet-4-20250514"
MAX_TOKENS = 8192

BEEHIIV_API_BASE = "https://api.beehiiv.com/v2"


# ---------------------------------------------------------------------------
# Date helpers
# ---------------------------------------------------------------------------

def get_date_range() -> str:
    """Return the date range string for the past 7 days ending yesterday."""
    today = datetime.utcnow().date()
    end = today - timedelta(days=1)
    start = end - timedelta(days=6)

    def fmt(d):
        return d.strftime("%B %-d, %Y")

    return f"{fmt(start)} – {fmt(end)}"


def get_week_label() -> str:
    """Short label for filenames and subject lines."""
    today = datetime.utcnow().date()
    end = today - timedelta(days=1)
    start = end - timedelta(days=6)
    return f"{start.strftime('%b %-d')}–{end.strftime('%-d, %Y')}"


# ---------------------------------------------------------------------------
# Prompt loader
# ---------------------------------------------------------------------------

def load_prompt(date_range: str, special_focus: str = "") -> str:
    """Load the newsletter prompt template and inject variables."""
    template_path = Path(__file__).parent / "prompt_template.txt"
    template = template_path.read_text()
    template = template.replace("{$DATE_RANGE}", date_range)
    template = template.replace("{$SPECIAL_FOCUS}", special_focus or "None provided.")
    return template


# ---------------------------------------------------------------------------
# Claude API call
# ---------------------------------------------------------------------------

def generate_newsletter(date_range: str, special_focus: str = "") -> str:
    """Call Claude API with web search to generate the newsletter markdown."""
    client = anthropic.Anthropic()  # Uses ANTHROPIC_API_KEY env var

    prompt_text = load_prompt(date_range, special_focus)

    print(f"[Seven Days] Generating newsletter for: {date_range}")
    print(f"[Seven Days] Using model: {CLAUDE_MODEL}")

    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=MAX_TOKENS,
        tools=[
            {
                "type": "web_search_20250305",
                "name": "web_search",
            }
        ],
        messages=[
            {
                "role": "user",
                "content": prompt_text,
            }
        ],
    )

    # Extract text content from response (skip tool use blocks)
    output_parts = []
    for block in response.content:
        if block.type == "text":
            output_parts.append(block.text)

    full_output = "\n".join(output_parts)

    # Extract content within <newsletter> tags if present
    match = re.search(r"<newsletter>(.*?)</newsletter>", full_output, re.DOTALL)
    if match:
        return match.group(1).strip()

    # Otherwise return everything after </scratchpad> if present
    if "</scratchpad>" in full_output:
        return full_output.split("</scratchpad>", 1)[1].strip()

    return full_output.strip()


# ---------------------------------------------------------------------------
# Markdown → HTML conversion with email styling
# ---------------------------------------------------------------------------

def markdown_to_email_html(md_content: str) -> str:
    """Convert newsletter markdown to a fully styled HTML email."""

    # Convert markdown to HTML
    html_body = markdown.markdown(
        md_content,
        extensions=["tables", "fenced_code", "nl2br"],
    )

    # Load the email template
    template_path = Path(__file__).parent / "email_template.html"
    template = template_path.read_text()

    # Inject the body content
    styled_html = template.replace("{{NEWSLETTER_BODY}}", html_body)

    # Inject the week label
    week_label = get_week_label()
    styled_html = styled_html.replace("{{WEEK_LABEL}}", week_label)

    # Inject the current year
    styled_html = styled_html.replace("{{YEAR}}", str(datetime.utcnow().year))

    return styled_html


# ---------------------------------------------------------------------------
# Beehiiv publishing
# ---------------------------------------------------------------------------

def publish_to_beehiiv(subject: str, html_content: str, send: bool = True) -> dict:
    """Create a post in Beehiiv and optionally send it."""
    api_key = os.environ["BEEHIIV_API_KEY"]
    pub_id = os.environ["BEEHIIV_PUBLICATION_ID"]

    url = f"{BEEHIIV_API_BASE}/publications/{pub_id}/posts"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "title": subject,
        "subtitle": "Your weekly global news briefing",
        "status": "confirmed" if send else "draft",
        "content_html": html_content,
        "send_to": "all" if send else None,
    }

    # Remove None values
    payload = {k: v for k, v in payload.items() if v is not None}

    print(f"[Seven Days] Publishing to Beehiiv (send={send})...")
    resp = requests.post(url, headers=headers, json=payload, timeout=30)
    if not resp.ok:
        print(f"[Seven Days] Beehiiv error {resp.status_code}: {resp.text}")
        resp.raise_for_status()

    result = resp.json()
    print(f"[Seven Days] Published! Post ID: {result.get('data', {}).get('id', 'unknown')}")
    return result


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Seven Days — Weekly Newsletter Generator")
    parser.add_argument("--draft", action="store_true", help="Create draft in Beehiiv (don't send)")
    parser.add_argument("--preview", action="store_true", help="Save locally only (don't publish)")
    parser.add_argument("--date-range", type=str, help="Override date range (e.g. 'February 19–26, 2026')")
    parser.add_argument("--special-focus", type=str, default="", help="Optional spotlight topic")
    args = parser.parse_args()

    # Determine date range
    date_range = args.date_range or get_date_range()

    # Generate the newsletter
    newsletter_md = generate_newsletter(date_range, args.special_focus)

    # Save raw markdown
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)

    date_slug = datetime.utcnow().strftime("%Y-%m-%d")
    md_path = output_dir / f"seven-days-{date_slug}.md"
    md_path.write_text(newsletter_md)
    print(f"[Seven Days] Markdown saved: {md_path}")

    # Convert to HTML
    html_content = markdown_to_email_html(newsletter_md)

    html_path = output_dir / f"seven-days-{date_slug}.html"
    html_path.write_text(html_content)
    print(f"[Seven Days] HTML saved: {html_path}")

    if args.preview:
        print("[Seven Days] Preview mode — not publishing.")
        return

    # Build subject line
    week_label = get_week_label()
    subject = f"Seven Days — {week_label}"

    # Publish
    should_send = not args.draft
    publish_to_beehiiv(subject, html_content, send=should_send)

    status = "sent" if should_send else "saved as draft"
    print(f"[Seven Days] Done! Newsletter {status}.")


if __name__ == "__main__":
    main()
