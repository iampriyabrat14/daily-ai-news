import feedparser
import requests
import os
import sys
from datetime import datetime, timedelta, timezone
from openai import OpenAI

# ── Credentials (set as env vars / GitHub Secrets) ──────────────────────────
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID   = os.environ.get("TELEGRAM_CHAT_ID")
EURI_API_KEY       = os.environ.get("EURI_API_KEY")

# ── EURI client (OpenAI-compatible) ─────────────────────────────────────────
euri_client = OpenAI(
    api_key=EURI_API_KEY,
    base_url="https://api.euron.one/api/v1/euri",
)

# ── RSS feed sources ─────────────────────────────────────────────────────────
RSS_FEEDS = [
    {"name": "VentureBeat AI",   "url": "https://venturebeat.com/category/ai/feed/"},
    {"name": "TechCrunch AI",    "url": "https://techcrunch.com/category/artificial-intelligence/feed/"},
    {"name": "The Decoder",      "url": "https://the-decoder.com/feed/"},
    {"name": "MIT Tech Review",  "url": "https://www.technologyreview.com/feed/"},
    {"name": "HuggingFace Blog", "url": "https://huggingface.co/blog/feed.xml"},
    {"name": "Google DeepMind",  "url": "https://deepmind.google/blog/rss.xml"},
    {"name": "Anthropic",        "url": "https://www.anthropic.com/rss.xml"},
    {"name": "OpenAI",           "url": "https://openai.com/news/rss.xml"},
    {"name": "Wired AI",         "url": "https://www.wired.com/feed/category/artificial-intelligence/latest/rss"},
    {"name": "Ars Technica",     "url": "https://feeds.arstechnica.com/arstechnica/index"},
    {"name": "AI Business",      "url": "https://aibusiness.com/rss.xml"},
    {"name": "InfoQ AI",         "url": "https://feed.infoq.com/"},
]

AI_KEYWORDS = [
    "ai", "artificial intelligence", "machine learning", "deep learning",
    "llm", "gpt", "gemini", "claude", "chatgpt", "openai", "anthropic",
    "neural network", "generative", "transformer", "model", "agent",
    "automation", "robotics", "computer vision", "nlp", "diffusion",
    "multimodal", "foundation model", "fine-tuning", "inference",
]


# ── Helpers ──────────────────────────────────────────────────────────────────

def is_ai_related(title: str, summary: str = "") -> bool:
    text = (title + " " + summary).lower()
    return any(kw in text for kw in AI_KEYWORDS)


def parse_time(entry) -> datetime | None:
    for attr in ("published_parsed", "updated_parsed"):
        t = getattr(entry, attr, None)
        if t:
            return datetime(*t[:6], tzinfo=timezone.utc)
    return None


def escape_html(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# ── Fetch articles from RSS ──────────────────────────────────────────────────

def fetch_recent_articles(hours: int = 13) -> list[dict]:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    articles: list[dict] = []
    seen_titles: set[str] = set()

    for feed in RSS_FEEDS:
        try:
            parsed = feedparser.parse(feed["url"], request_headers={"User-Agent": "Mozilla/5.0"})
            for entry in parsed.entries[:8]:
                title    = entry.get("title", "").strip()
                link     = entry.get("link", "")
                summary  = entry.get("summary", "")
                pub_time = parse_time(entry)

                if not title or title in seen_titles:
                    continue
                if pub_time and pub_time < cutoff:
                    continue
                if feed["name"] in ("Ars Technica", "InfoQ AI") and not is_ai_related(title, summary):
                    continue

                seen_titles.add(title)
                articles.append({
                    "source":    feed["name"],
                    "title":     title,
                    "link":      link,
                    "published": pub_time,
                })
        except Exception as e:
            print(f"[WARN] {feed['name']}: {e}")

    articles.sort(
        key=lambda x: x["published"] or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )
    return articles[:12]


# ── AI-generated digest via EURI ─────────────────────────────────────────────

def generate_ai_digest(articles: list[dict], period: str) -> str:
    if not articles:
        return "No significant AI news in the last 13 hours."

    headlines = "\n".join(
        f"{i}. [{art['source']}] {art['title']}"
        for i, art in enumerate(articles, 1)
    )

    prompt = (
        f"You are an AI news analyst. Below are today's {period.split()[0].lower()} AI headlines.\n\n"
        f"{headlines}\n\n"
        "Write a sharp, engaging digest in 4–5 bullet points (use • emoji). "
        "Each bullet = one key insight or trend from the headlines. "
        "No fluff. Be specific. Max 180 words total."
    )

    try:
        response = euri_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a concise AI news analyst writing for a tech-savvy audience."},
                {"role": "user",   "content": prompt},
            ],
            max_tokens=300,
            temperature=0.65,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[WARN] EURI API error: {e}")
        return ""


# ── Format Telegram message ───────────────────────────────────────────────────

def format_message(articles: list[dict], period: str, ai_digest: str) -> str:
    now_ist  = datetime.now(timezone.utc) + timedelta(hours=5, minutes=30)
    date_str = now_ist.strftime("%d %B %Y  |  %I:%M %p IST")

    lines = [
        f"<b>🤖 Daily AI News — {period}</b>",
        f"📅 {date_str}",
        "━━━━━━━━━━━━━━━━━━━━━━",
    ]

    # AI-generated summary block
    if ai_digest:
        lines += ["", "<b>🧠 AI Digest (powered by gpt-4o-mini)</b>", ""]
        for line in ai_digest.splitlines():
            lines.append(escape_html(line))
        lines += ["", "━━━━━━━━━━━━━━━━━━━━━━"]

    # Article links
    if not articles:
        lines.append("\nNo new AI news in the last 13 hours. Check back soon! 🔍")
    else:
        lines += ["", "<b>📰 Top Headlines</b>", ""]
        for i, art in enumerate(articles, 1):
            title  = escape_html(art["title"])
            source = escape_html(art["source"])
            link   = art["link"]
            if link:
                lines.append(f'{i}. <a href="{link}"><b>{title}</b></a>')
            else:
                lines.append(f"{i}. <b>{title}</b>")
            lines.append(f"   📌 {source}")
            lines.append("")

    lines += [
        "━━━━━━━━━━━━━━━━━━━━━━",
        "🚀 Stay ahead in AI! Next update in 12 hours.",
    ]
    return "\n".join(lines)


# ── Send to Telegram ──────────────────────────────────────────────────────────

def send_telegram(text: str) -> None:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        raise ValueError("TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set.")

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    if len(text) > 4000:
        text = text[:3950] + "\n\n... <i>(truncated)</i>"

    resp = requests.post(url, json={
        "chat_id":                  TELEGRAM_CHAT_ID,
        "text":                     text,
        "parse_mode":               "HTML",
        "disable_web_page_preview": False,
    }, timeout=15)

    if resp.status_code != 200:
        raise RuntimeError(f"Telegram error {resp.status_code}: {resp.text}")

    print("✅ Message sent to Telegram.")


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    period = sys.argv[1] if len(sys.argv) > 1 else "Update"
    print(f"Fetching AI news ({period}) ...")

    articles = fetch_recent_articles(hours=13)
    print(f"Found {len(articles)} articles.")

    print("Generating AI digest via EURI ...")
    ai_digest = generate_ai_digest(articles, period)

    message = format_message(articles, period, ai_digest)
    send_telegram(message)
