# Daily AI News — Telegram Bot

Sends curated AI news to your Telegram twice daily: **7 AM** and **7 PM IST**, via GitHub Actions.

## News Sources

| Source | Coverage |
|---|---|
| VentureBeat AI | Startup & enterprise AI |
| TechCrunch AI | Funding, launches |
| The Decoder | LLM & generative AI deep dives |
| MIT Technology Review | Research & policy |
| HuggingFace Blog | Open-source models |
| Google DeepMind | Research papers |
| Anthropic | Claude / safety research |
| OpenAI | GPT, product updates |
| Wired AI | Culture & industry |
| Ars Technica | Tech news (AI-filtered) |
| AI Business | Enterprise AI |

---

## One-Time Setup

### Step 1 — Create a Telegram Bot

1. Open Telegram → search **@BotFather**
2. Send `/newbot`, choose a name & username
3. Copy the **Bot Token** (looks like `123456789:ABCdef...`)

### Step 2 — Get your Telegram Chat ID

- Start your bot (send `/start`)
- Open: `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
- Find `"chat":{"id": XXXXXXX}` — that number is your **Chat ID**
- For a group/channel: add the bot as admin, send a message, then check the same URL

### Step 3 — Push to GitHub

```bash
# Inside "Daily ai News" folder — use it as the repo root
git init
git add .
git commit -m "Initial AI news bot setup"
git remote add origin https://github.com/<your-username>/daily-ai-news.git
git push -u origin main
```

### Step 4 — Add GitHub Secrets

In your GitHub repo: **Settings → Secrets and variables → Actions → New repository secret**

| Secret name | Value |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Token from BotFather |
| `TELEGRAM_CHAT_ID` | Your chat/group ID |

### Step 5 — Test Manually

Go to **Actions** tab → **Daily AI News to Telegram** → **Run workflow** → click **Run workflow**.

Check Telegram — you should receive the news message within ~30 seconds.

---

## Schedule

| Time (IST) | Cron (UTC) | Label |
|---|---|---|
| 07:00 AM | `30 1 * * *` | Morning ☀️ |
| 07:00 PM | `30 13 * * *` | Evening 🌙 |

---

## Local Testing

```bash
pip install -r requirements.txt
set TELEGRAM_BOT_TOKEN=your_token
set TELEGRAM_CHAT_ID=your_chat_id
python fetch_ai_news.py "Test 🧪"
```

---

Every run also saves the digest as a Markdown file under `digests/YYYY/MM/`, and the workflow commits it back to this repo — so this README's archive section and the commit history both grow daily.

<!-- DIGEST_INDEX_START -->

## 📚 Digest Archive

- [2026-08-16-morning](digests/2026/08/2026-08-16-morning.md)
- [2026-08-15-morning](digests/2026/08/2026-08-15-morning.md)
- [2026-08-15-evening](digests/2026/08/2026-08-15-evening.md)
- [2026-08-14-morning](digests/2026/08/2026-08-14-morning.md)
- [2026-08-14-evening](digests/2026/08/2026-08-14-evening.md)
- [2026-08-13-morning](digests/2026/08/2026-08-13-morning.md)
- [2026-08-13-evening](digests/2026/08/2026-08-13-evening.md)
- [2026-08-12-morning](digests/2026/08/2026-08-12-morning.md)
- [2026-08-12-evening](digests/2026/08/2026-08-12-evening.md)
- [2026-08-11-morning](digests/2026/08/2026-08-11-morning.md)
- [2026-08-11-evening](digests/2026/08/2026-08-11-evening.md)
- [2026-08-10-morning](digests/2026/08/2026-08-10-morning.md)
- [2026-08-10-evening](digests/2026/08/2026-08-10-evening.md)
- [2026-08-09-morning](digests/2026/08/2026-08-09-morning.md)
- [2026-08-09-evening](digests/2026/08/2026-08-09-evening.md)
- [2026-08-08-morning](digests/2026/08/2026-08-08-morning.md)
- [2026-08-08-evening](digests/2026/08/2026-08-08-evening.md)
- [2026-08-07-morning](digests/2026/08/2026-08-07-morning.md)
- [2026-08-07-evening](digests/2026/08/2026-08-07-evening.md)
- [2026-08-06-morning](digests/2026/08/2026-08-06-morning.md)
- [2026-08-05-morning](digests/2026/08/2026-08-05-morning.md)
- [2026-08-05-evening](digests/2026/08/2026-08-05-evening.md)
- [2026-08-04-morning](digests/2026/08/2026-08-04-morning.md)
- [2026-08-04-evening](digests/2026/08/2026-08-04-evening.md)
- [2026-08-03-morning](digests/2026/08/2026-08-03-morning.md)
- [2026-08-03-evening](digests/2026/08/2026-08-03-evening.md)
- [2026-08-02-morning](digests/2026/08/2026-08-02-morning.md)
- [2026-08-02-evening](digests/2026/08/2026-08-02-evening.md)
- [2026-08-01-morning](digests/2026/08/2026-08-01-morning.md)
- [2026-08-01-evening](digests/2026/08/2026-08-01-evening.md)
- [2026-07-31-morning](digests/2026/07/2026-07-31-morning.md)
- [2026-07-31-evening](digests/2026/07/2026-07-31-evening.md)
- [2026-07-30-morning](digests/2026/07/2026-07-30-morning.md)
- [2026-07-30-evening](digests/2026/07/2026-07-30-evening.md)
- [2026-07-29-morning](digests/2026/07/2026-07-29-morning.md)
- [2026-07-28-morning](digests/2026/07/2026-07-28-morning.md)
- [2026-07-28-evening](digests/2026/07/2026-07-28-evening.md)

<!-- DIGEST_INDEX_END -->
