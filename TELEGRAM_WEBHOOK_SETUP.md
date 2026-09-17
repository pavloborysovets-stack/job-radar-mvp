# Telegram Bot Webhook Setup Guide 🤖

**Goal**: Configure Telegram bot to receive messages via webhook (production-ready)

**Time**: 10 minutes  
**Prerequisites**: 
- Bot token from @BotFather (starts with digits:letters)
- Public Replit URL (from Publish button)
- Running Job Radar application

---

## 🔄 Polling vs Webhook

### Polling (Development) ❌ Not ideal for production
```
Your App → Telegram API
           "Any new messages?" ← Every 2-3 seconds
           ↓ No new messages
           ↓ Wait 2 seconds
           ↓ Ask again
```
- Slow (2-3 sec delay)
- Uses more bandwidth
- Scales poorly with multiple bots

### Webhook (Production) ✅ Recommended
```
Telegram API → Your App
               "New message from user 123456"
               Your app processes instantly
```
- Instant (milliseconds)
- Efficient (only sends data when needed)
- Scalable
- Production standard

---

## 🚀 Setup Steps

### Step 1: Verify Bot Token

You should have received a token from @BotFather that looks like:
```
123456789:ABCDefGhIjKlMnOpQrStUvWxYzAbCdEfGhI
```

If you don't have it:
1. Open Telegram
2. Find @BotFather
3. Send `/newbot`
4. Follow prompts (name and username)
5. Copy the token

### Step 2: Set Up Replit Secrets

In Replit:
1. Click **"Secrets"** (lock icon) on left sidebar
2. Add new secret:
   - **Key**: `TELEGRAM_BOT_TOKEN`
   - **Value**: `123456789:ABCDefGhIjKlMnOpQrStUvWxYzAbCdEfGhI` (paste your token)
3. Click **"Add secret"**

Verify in console:
```bash
echo $TELEGRAM_BOT_TOKEN
# Should output: 123456789:ABCDefGhIjKlMnOpQrStUvWxYzAbCdEfGhI
```

### Step 3: Verify Application Running

1. Click **"Run"** in Replit (if not already running)
2. Wait for "Application startup complete" message
3. Click **"Publish"** to get public URL
4. Copy the URL: `https://job-radar-2-zip--pavloborysovets.replit.app`

### Step 4: Set Telegram Webhook

**Option A: Using cURL command** (Recommended)

```bash
# Replace <BOT_TOKEN> with your actual token
# Replace <PUBLIC_URL> with your Replit URL

curl -X POST "https://api.telegram.org/bot<BOT_TOKEN>/setWebhook" \
  -d "url=<PUBLIC_URL>/webhook/telegram"

# Example:
curl -X POST "https://api.telegram.org/bot123456789:ABCDefGhIjKlMnOpQrStUvWxYzAbCdEfGhI/setWebhook" \
  -d "url=https://job-radar-2-zip--pavloborysovets.replit.app/webhook/telegram"
```

**Expected response**:
```json
{
  "ok": true,
  "result": true,
  "description": "Webhook was set"
}
```

**Option B: Using Python script** (If cURL not available)

Create `setup_webhook.py`:
```python
import os
import requests
from config import get_settings

settings = get_settings()
token = settings.telegram_bot_token
public_url = os.getenv('REPLIT_URL', 'https://job-radar-2-zip--pavloborysovets.replit.app')

webhook_url = f"https://api.telegram.org/bot{token}/setWebhook"
response = requests.post(
    webhook_url,
    data={"url": f"{public_url}/webhook/telegram"}
)

print(f"Webhook response: {response.json()}")

if response.json()['ok']:
    print("✓ Webhook configured successfully!")
else:
    print("✗ Failed to set webhook")
    print(response.json())
```

Run it:
```bash
python setup_webhook.py
```

### Step 5: Verify Webhook Configuration

Check that webhook was set correctly:

```bash
# Replace <BOT_TOKEN>
curl -X GET "https://api.telegram.org/bot<BOT_TOKEN>/getWebhookInfo"

# Example:
curl -X GET "https://api.telegram.org/bot123456789:ABCDefGhIjKlMnOpQrStUvWxYzAbCdEfGhI/getWebhookInfo"
```

**Expected response**:
```json
{
  "ok": true,
  "result": {
    "url": "https://job-radar-2-zip--pavloborysovets.replit.app/webhook/telegram",
    "has_custom_certificate": false,
    "pending_update_count": 0,
    "last_error_date": null,
    "last_error_message": null,
    "max_connections": 40,
    "allowed_updates": []
  }
}
```

**Key fields to verify**:
- ✅ `url` matches your Replit URL
- ✅ `pending_update_count` = 0 (no backlog)
- ✅ `last_error_date` = null (no recent errors)
- ✅ `last_error_message` = null (no error message)

---

## 🧪 Test Webhook

### Step 1: Monitor Replit Logs

Keep Replit console open so you can see incoming webhook events.

### Step 2: Send Test Message

Open Telegram and find your bot (search for the name you gave it).

Send: `/start`

**In Replit console, you should see**:
```
2026-09-17 09:00:00.123 | INFO | Received update from Telegram
2026-09-17 09:00:00.124 | INFO | Update ID: 123456789
2026-09-17 09:00:00.125 | INFO | Message: /start
2026-09-17 09:00:00.126 | INFO | Processing in state: START
```

**In Telegram, bot should respond**:
```
Привет! 👋 Добро пожаловать в Job Radar

[Русский 🇷🇺] [English 🇬🇧] [Polski 🇵🇱] [Українська 🇺🇦]
```

### Step 3: Full FSM Flow Test

Follow the conversational flow:

1. ✅ Send `/start` → Language selection
2. ✅ Click language button → Geography confirmation
3. ✅ Click "Yes" → Job type input
4. ✅ Type "Python developer" → Get results
5. ✅ Click emoji button → See job card
6. ✅ Click 👍 or 👎 → See next job

Monitor console for errors or unexpected behavior.

---

## 🔧 Troubleshooting Webhook

### Problem 1: "Invalid webhook URL"

**Error message**:
```json
{
  "ok": false,
  "error_code": 400,
  "description": "Bad Request: HTTPS URL must be used"
}
```

**Solution**:
- Make sure URL starts with `https://` (not `http://`)
- Check URL is correct: `https://job-radar-2-zip--pavloborysovets.replit.app/webhook/telegram`
- No trailing slash!

### Problem 2: "Connection refused"

**Error message**:
```json
{
  "ok": false,
  "error_code": 400,
  "description": "Bad Request: Webhook URL unreachable"
}
```

**Solution**:
- Verify Replit app is running (click "Run")
- Verify URL is correct (click "Publish" to get fresh URL)
- Wait 30 seconds before retrying
- Check internet connection

### Problem 3: Webhook set but bot not responding

**Check 1**: Is app running?
- Replit should show green "Running" indicator
- Console should show startup messages

**Check 2**: Is webhook correctly set?
```bash
curl -X GET "https://api.telegram.org/bot<TOKEN>/getWebhookInfo" | jq .result.url
# Should output: "https://your-url/webhook/telegram"
```

**Check 3**: Can you access your app?
```bash
curl https://your-url/health
# Should return: {"status":"healthy",...}
```

**Check 4**: Check /webhook/telegram endpoint exists
```bash
# This should return 405 Method Not Allowed (POST required)
curl -X GET https://your-url/webhook/telegram
```

**Check 5**: Look at Replit logs for errors
- Scroll up in Replit console
- Look for ERROR or EXCEPTION lines
- Copy error text for debugging

### Problem 4: Webhook is old/stale

If you changed the URL or bot token, remove old webhook:

```bash
# Replace <BOT_TOKEN>
curl -X POST "https://api.telegram.org/bot<BOT_TOKEN>/deleteWebhook"

# Response:
# {"ok": true, "result": true, "description": "Webhook was deleted"}

# Then set new webhook:
curl -X POST "https://api.telegram.org/bot<BOT_TOKEN>/setWebhook" \
  -d "url=https://new-url/webhook/telegram"
```

### Problem 5: "Pending update count" > 0

This means there are messages waiting to be processed from before webhook was set.

**Solution**:
```bash
# Replace <BOT_TOKEN>
# Get up to 100 pending updates and delete them
curl -X POST "https://api.telegram.org/bot<BOT_TOKEN>/getUpdates" \
  -d "limit=100" | jq .result[].update_id

# Then delete webhook and re-set it
curl -X POST "https://api.telegram.org/bot<BOT_TOKEN>/deleteWebhook"
curl -X POST "https://api.telegram.org/bot<BOT_TOKEN>/setWebhook" \
  -d "url=https://your-url/webhook/telegram"
```

---

## 📊 Monitoring Webhook Health

Check webhook status regularly:

```bash
#!/bin/bash
# save as check_webhook.sh

BOT_TOKEN="123456789:ABCDefGhIjKlMnOpQrStUvWxYzAbCdEfGhI"

# Get webhook info
curl -s -X GET "https://api.telegram.org/bot$BOT_TOKEN/getWebhookInfo" | jq '
.result | 
"Webhook Status: \(if .url then "✓ Active" else "✗ Inactive" end)
URL: \(.url // "Not set")
Pending updates: \(.pending_update_count // 0)
Last error: \(.last_error_message // "None")"
'
```

Run periodically:
```bash
watch -n 300 bash check_webhook.sh  # Every 5 minutes
```

---

## 🔄 Fallback to Polling (If Webhook Fails)

If webhook doesn't work, you can use polling for development:

In Replit, open a second Terminal tab and run:
```bash
python run_bot_polling.py
```

This starts polling mode (asks Telegram for updates every 2-3 seconds).

**Note**: Polling is slower and uses more resources, so use webhook for production.

---

## 📋 Webhook Setup Checklist

- [ ] **Step 1**: Bot token obtained from @BotFather
- [ ] **Step 2**: Token set in Replit Secrets as `TELEGRAM_BOT_TOKEN`
- [ ] **Step 3**: Application running (click "Run")
- [ ] **Step 4**: Public URL obtained (click "Publish")
- [ ] **Step 5a**: Webhook set via cURL or script
- [ ] **Step 5b**: `getWebhookInfo` confirms URL is correct
- [ ] **Step 6**: Test `/start` command in Telegram
- [ ] **Step 7**: Verify bot responds in Telegram
- [ ] **Step 8**: Monitor console logs for errors
- [ ] **Step 9**: Run full FSM test flow
- [ ] **Step 10**: Webhook status looks good (no errors)

---

## 🎯 After Webhook is Working

You can now:
1. ✅ Test full bot conversation flow
2. ✅ Verify FSM state machine
3. ✅ Test database persistence (user data saved)
4. ✅ Test ranking algorithm (results make sense)
5. ✅ Test LLM integration (if configured)
6. ✅ Stress test with multiple users
7. ✅ Monitor performance and errors
8. ✅ Prepare for production deployment

---

## 🆘 Need Help?

If webhook setup is still not working:

1. **Run diagnostic tool**:
   ```bash
   python diagnose.py
   ```

2. **Check Telegram bot documentation**: https://core.telegram.org/bots

3. **Common issues**:
   - Invalid token format
   - Wrong URL (not https, not /webhook/telegram)
   - Replit app crashed or not running
   - Network/firewall blocking Telegram API

4. **Get bot logs**:
   ```bash
   tail -f /tmp/job_radar_bot.log
   ```

---

## ✨ Success Indicators

✅ Bot responds instantly to messages
✅ Webhook URL appears in getWebhookInfo
✅ No pending updates
✅ No error messages in logs
✅ User data persists across conversations
✅ FSM states change correctly
✅ Results appear in <2 seconds

---

**Setup Date**: 2026-09-17  
**Version**: 1.0  
**Next Step**: Run TESTING_GUIDE.md for full end-to-end testing

Good luck! 🚀
