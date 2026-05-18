import feedparser
import requests
import os
import sys
from datetime import datetime, timedelta, timezone
from openai import OpenAI

# ── Credentials ──────────────────────────────────────────────────────────────
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID   = os.environ.get("TELEGRAM_CHAT_ID")
EURI_API_KEY       = os.environ.get("EURI_API_KEY")

euri_client = OpenAI(
    api_key=EURI_API_KEY,
    base_url="https://api.euron.one/api/v1/euri",
)

# ── RSS feeds — focused on model releases, frameworks, research ───────────────
RSS_FEEDS = [
    # Official lab blogs — first to announce new models
    {"name": "OpenAI",             "url": "https://openai.com/news/rss.xml"},
    {"name": "Anthropic",          "url": "https://www.anthropic.com/rss.xml"},
    {"name": "Google DeepMind",    "url": "https://deepmind.google/blog/rss.xml"},
    {"name": "Meta AI",            "url": "https://ai.meta.com/blog/feed/"},
    {"name": "Microsoft AI",       "url": "https://blogs.microsoft.com/ai/feed/"},
    {"name": "HuggingFace Blog",   "url": "https://huggingface.co/blog/feed.xml"},
    {"name": "Mistral AI",         "url": "https://mistral.ai/news/rss"},

    # Community — fastest for open-source model & framework drops
    {"name": "Reddit LocalLLaMA",  "url": "https://www.reddit.com/r/LocalLLaMA/.rss"},
    {"name": "Reddit MachineLearning", "url": "https://www.reddit.com/r/MachineLearning/.rss"},
    {"name": "Hacker News AI",     "url": "https://hnrss.org/newest?q=LLM+OR+AI+model+OR+open+source+AI&points=15"},

    # Research
    {"name": "Papers With Code",   "url": "https://paperswithcode.com/rss"},
    {"name": "Arxiv CS.AI",        "url": "https://arxiv.org/rss/cs.AI"},
    {"name": "Arxiv CS.LG",        "url": "https://arxiv.org/rss/cs.LG"},

    # News & analysis
    {"name": "The Decoder",        "url": "https://the-decoder.com/feed/"},
    {"name": "VentureBeat AI",     "url": "https://venturebeat.com/category/ai/feed/"},
    {"name": "TechCrunch AI",      "url": "https://techcrunch.com/category/artificial-intelligence/feed/"},
]

# Keywords that signal a real AI tech update (model/framework/tool/research)
RELEASE_KEYWORDS = [
    # Model releases
    "releases", "launched", "launches", "introduces", "announcing", "announced",
    "new model", "open source", "open-source", "weights", "checkpoint",
    # Model names — catch new versions
    "llama", "mistral", "gemini", "gpt", "claude", "phi", "qwen", "deepseek",
    "grok", "falcon", "mixtral", "command-r", "stable diffusion", "flux",
    "whisper", "sora", "dall-e", "midjourney", "runway",
    # Frameworks & tools
    "langchain", "llamaindex", "llama index", "crewai", "autogen", "dspy",
    "ollama", "vllm", "transformers", "pytorch", "jax", "tensorflow",
    "hugging face", "huggingface", "litellm", "haystack", "semantic kernel",
    "langgraph", "instructor", "guidance", "outlines",
    # Research signals
    "benchmark", "state-of-the-art", "sota", "beats", "outperforms",
    "paper", "arxiv", "research", "breakthrough", "multimodal", "reasoning",
    "agentic", "rag", "fine-tun", "quantiz", "lora", "rlhf",
]

# Noise to filter out (business news, not tech releases)
NOISE_KEYWORDS = [
    "funding", "raises $", "valuation", "ipo", "acquisition", "lawsuit",
    "regulation", "policy", "layoff", "fired", "ceo", "hired",
    "stock", "revenue", "quarterly", "earnings",
]


def is_relevant(title: str, summary: str = "") -> bool:
    text = (title + " " + summary).lower()
    if any(noise in text for noise in NOISE_KEYWORDS):
        return False
    return any(kw in text for kw in RELEASE_KEYWORDS)


def relevance_score(title: str, summary: str = "") -> int:
    """Higher = more relevant. Used to rank articles."""
    text = (title + " " + summary).lower()
    return sum(1 for kw in RELEASE_KEYWORDS if kw in text)


def parse_time(entry) -> datetime | None:
    for attr in ("published_parsed", "updated_parsed"):
        t = getattr(entry, attr, None)
        if t:
            return datetime(*t[:6], tzinfo=timezone.utc)
    return None


def escape_html(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# ── Fetch & filter articles ───────────────────────────────────────────────────

def fetch_recent_articles(hours: int = 13) -> list[dict]:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    articles: list[dict] = []
    seen_titles: set[str] = set()

    for feed in RSS_FEEDS:
        try:
            parsed = feedparser.parse(feed["url"], request_headers={"User-Agent": "Mozilla/5.0"})
            for entry in parsed.entries[:10]:
                title    = entry.get("title", "").strip()
                link     = entry.get("link", "")
                summary  = entry.get("summary", "")
                pub_time = parse_time(entry)

                if not title or title in seen_titles:
                    continue
                if pub_time and pub_time < cutoff:
                    continue
                if not is_relevant(title, summary):
                    continue

                seen_titles.add(title)
                articles.append({
                    "source":    feed["name"],
                    "title":     title,
                    "link":      link,
                    "published": pub_time,
                    "score":     relevance_score(title, summary),
                })
        except Exception as e:
            print(f"[WARN] {feed['name']}: {e}")

    # Sort: relevance score first, then recency
    articles.sort(key=lambda x: (
        x["score"],
        x["published"] or datetime.min.replace(tzinfo=timezone.utc),
    ), reverse=True)

    return articles[:12]


# ── AI digest via EURI ────────────────────────────────────────────────────────

def generate_ai_digest(articles: list[dict], period: str) -> str:
    if not articles:
        return ""

    headlines = "\n".join(
        f"{i}. [{art['source']}] {art['title']}"
        for i, art in enumerate(articles, 1)
    )

    prompt = (
        f"You are an AI engineer who tracks every new model release, framework update, "
        f"and research breakthrough. Below are today's {period.split()[0].lower()} headlines.\n\n"
        f"{headlines}\n\n"
        "Write 4–5 bullet points (• emoji) covering:\n"
        "- Which new models or versions dropped\n"
        "- Which frameworks or tools got updated\n"
        "- Any research breakthroughs worth noting\n"
        "Be specific (include model names, version numbers, benchmarks). Max 200 words."
    )

    try:
        response = euri_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a precise AI tech analyst. No fluff, only facts."},
                {"role": "user",   "content": prompt},
            ],
            max_tokens=350,
            temperature=0.5,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[WARN] EURI API error: {e}")
        return ""


# ── Format Telegram message ───────────────────────────────────────────────────

# Category tags for article labels
def category_tag(title: str, source: str) -> str:
    t = title.lower()
    if any(k in t for k in ["releases", "launched", "introduces", "new model", "weights"]):
        return "🆕 New Release"
    if any(k in t for k in ["langchain", "llamaindex", "crewai", "autogen", "ollama", "vllm",
                             "transformers", "pytorch", "framework", "library", "tool"]):
        return "🛠 Framework/Tool"
    if any(k in t for k in ["paper", "arxiv", "benchmark", "research", "sota", "outperforms"]):
        return "📄 Research"
    if source in ("Reddit LocalLLaMA", "Reddit MachineLearning", "Hacker News AI"):
        return "💬 Community"
    return "📰 News"


def format_message(articles: list[dict], period: str, ai_digest: str) -> str:
    now_ist  = datetime.now(timezone.utc) + timedelta(hours=5, minutes=30)
    date_str = now_ist.strftime("%d %B %Y  •  %I:%M %p IST")

    # ── Header ────────────────────────────────────────────────────────────────
    lines = [
        "╔══════════════════════════╗",
        f"   🤖  <b>Daily AI Tech Digest</b>",
        f"   {period}",
        "╚══════════════════════════╝",
        f"📅  <i>{date_str}</i>",
        "",
    ]

    # ── AI Summary ────────────────────────────────────────────────────────────
    if ai_digest:
        lines += [
            "┌─────────────────────────┐",
            "  🧠  <b>Key Highlights</b>",
            "└─────────────────────────┘",
            "",
        ]
        for line in ai_digest.splitlines():
            if line.strip():
                lines.append(escape_html(line))
        lines += [""]

    # ── Articles ──────────────────────────────────────────────────────────────
    if not articles:
        lines.append("🔍  No major AI updates in the last 13 hours. Check back soon!")
    else:
        lines += [
            "┌─────────────────────────┐",
            "  🔗  <b>Latest Updates</b>",
            "└─────────────────────────┘",
            "",
        ]
        for i, art in enumerate(articles, 1):
            title  = escape_html(art["title"])
            source = escape_html(art["source"])
            tag    = category_tag(art["title"], art["source"])
            link   = art["link"]

            if link:
                lines.append(f'<b>{i}.</b>  <a href="{link}">{title}</a>')
            else:
                lines.append(f"<b>{i}.</b>  {title}")
            lines.append(f"      {tag}  │  <i>{source}</i>")
            lines.append("")

    # ── Footer ────────────────────────────────────────────────────────────────
    lines += [
        "─────────────────────────────",
        "⚡  Next update in <b>12 hours</b>",
        "─────────────────────────────",
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
    print(f"Fetching AI tech news ({period}) ...")

    articles = fetch_recent_articles(hours=13)
    print(f"Found {len(articles)} relevant articles.")

    print("Generating digest via EURI ...")
    ai_digest = generate_ai_digest(articles, period)

    message = format_message(articles, period, ai_digest)
    send_telegram(message)
