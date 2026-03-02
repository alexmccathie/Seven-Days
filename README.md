# Seven Days — Automated Weekly Newsletter

A fully automated global news briefing that generates and sends itself every week using the Claude API and Beehiiv.

## How It Works

1. **GitHub Actions** triggers every Thursday at 06:00 UTC
2. **Claude API** (with web search) researches and writes a 1,500–2,200 word briefing
3. **Markdown → HTML** conversion with a responsive email template
4. **Beehiiv API** publishes and sends to your subscriber list

Zero human intervention required. Total cost: ~$2–5/month (Claude API usage only).

---

## Setup Guide

### Step 1: Create a Beehiiv Account

1. Go to [beehiiv.com](https://www.beehiiv.com) and sign up (free tier supports 2,500 subscribers)
2. Create a new publication — name it "Seven Days"
3. Customise your publication settings (logo, description, colours)
4. Get your **Publication ID**:
   - Go to **Settings → General**
   - Your Publication ID is in the URL: `app.beehiiv.com/settings/.../{PUBLICATION_ID}`
5. Get your **API Key**:
   - Go to **Settings → Integrations → API**
   - Click **Create New API Key**
   - Give it **Full Access** permissions
   - Copy the key immediately (it won't be shown again)

### Step 2: Get an Anthropic API Key

1. Go to [console.anthropic.com](https://console.anthropic.com)
2. Sign up or log in
3. Navigate to **API Keys** and create a new key
4. Add credit ($5–10 is plenty to start — each newsletter costs roughly $0.05–0.15)

### Step 3: Create the GitHub Repository

1. Create a new **private** repository on GitHub (e.g. `seven-days-newsletter`)
2. Push all files from this package to the repository:

```bash
cd seven-days
git init
git add .
git commit -m "Initial commit — Seven Days newsletter automation"
git remote add origin git@github.com:YOUR_USERNAME/seven-days-newsletter.git
git push -u origin main
```

### Step 4: Add Secrets to GitHub

1. In your GitHub repo, go to **Settings → Secrets and variables → Actions**
2. Add three **Repository Secrets**:

| Secret Name                | Value                        |
|---------------------------|------------------------------|
| `ANTHROPIC_API_KEY`       | Your Anthropic API key       |
| `BEEHIIV_API_KEY`         | Your Beehiiv API key         |
| `BEEHIIV_PUBLICATION_ID`  | Your Beehiiv publication ID  |

### Step 5: Test It

Run a manual test before going live:

1. Go to the **Actions** tab in your GitHub repo
2. Click **"Generate & Send Seven Days Newsletter"** workflow
3. Click **"Run workflow"**
4. Set mode to **`draft`** for the first run (saves to Beehiiv without sending)
5. Check your Beehiiv dashboard — you should see a draft post
6. Review it, and if you're happy, you're all set

---

## Usage

### Automatic (default)
The workflow runs every **Thursday at 06:00 UTC** automatically. No action needed.

To change the schedule, edit the cron expression in `.github/workflows/weekly-newsletter.yml`:
```yaml
# Some examples:
- cron: '0 6 * * 4'    # Thursday 06:00 UTC (default)
- cron: '0 8 * * 1'    # Monday 08:00 UTC
- cron: '0 14 * * 5'   # Friday 14:00 UTC
```

### Manual Trigger
From the GitHub Actions tab, click **"Run workflow"** with options:

| Option          | Description                                    |
|-----------------|------------------------------------------------|
| **send**        | Generate and send to all subscribers           |
| **draft**       | Generate and save as draft (review before send)|
| **preview**     | Generate locally only (download as artifact)   |
| **date_range**  | Override dates (e.g. "February 19–26, 2026")   |
| **special_focus**| Force a specific Spotlight topic              |

### Run Locally
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export ANTHROPIC_API_KEY="sk-ant-..."
export BEEHIIV_API_KEY="..."
export BEEHIIV_PUBLICATION_ID="..."

# Preview only (no publishing)
python generate.py --preview

# Create draft in Beehiiv
python generate.py --draft

# Generate and send
python generate.py

# With overrides
python generate.py --date-range "February 19–26, 2026" --special-focus "SCOTUS tariff ruling"
```

---

## File Structure

```
seven-days/
├── generate.py                 # Main script — generation + publishing
├── prompt_template.txt         # Newsletter prompt (edit to change style/structure)
├── email_template.html         # HTML email template (edit to change design)
├── requirements.txt            # Python dependencies
├── .gitignore
├── .github/
│   └── workflows/
│       └── weekly-newsletter.yml   # GitHub Actions automation
└── output/                     # Generated newsletters (gitignored)
    ├── seven-days-2026-02-27.md
    └── seven-days-2026-02-27.html
```

---

## Customisation

### Change the send schedule
Edit the cron in `.github/workflows/weekly-newsletter.yml`

### Change the editorial style or structure
Edit `prompt_template.txt` — the entire personality, structure, and editorial rules are defined there

### Change the email design
Edit `email_template.html` — colours, fonts, layout are all in the inline CSS

### Key design tokens
| Token         | Current Value | Location            |
|---------------|---------------|---------------------|
| Navy bg       | `#0d1b2a`     | email_template.html |
| Gold accent   | `#c9a84c`     | email_template.html |
| Body font     | Georgia       | email_template.html |
| UI font       | Helvetica Neue| email_template.html |
| Max width     | 640px         | email_template.html |

---

## Optional: Add a Review Gate

If you want to review each newsletter before it sends (recommended for the first few weeks):

1. Change the default mode in the workflow from `send` to `draft`:
   ```yaml
   MODE="${{ github.event.inputs.mode || 'draft' }}"
   ```
2. Each Thursday, you'll get a draft in Beehiiv
3. Review it, make any edits, and click **"Send"** manually in Beehiiv
4. Once you're confident in the output, switch back to `send`

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Workflow not running | Check Actions tab is enabled. Free repos have Actions enabled by default. |
| API key errors | Verify secrets are set correctly in Settings → Secrets → Actions |
| Empty newsletter | Check Anthropic API has credit. The web search tool needs a funded account. |
| HTML looks wrong | Preview locally first with `--preview`, open the HTML file in a browser |
| Beehiiv 401 error | Regenerate API key in Beehiiv with Full Access permissions |

---

## Cost Estimate

| Component | Cost |
|-----------|------|
| Claude API (Sonnet, ~8k tokens out + web search) | ~$0.05–0.15 per run |
| GitHub Actions | Free (2,000 mins/month on free tier) |
| Beehiiv | Free up to 2,500 subscribers |
| **Total** | **~$2–5/month** |
