# Quick Start Guide - AI Front Office Manager

## 🚀 First Time Setup (5 Minutes)

### 1. Activate Virtual Environment
```powershell
cd "c:\Users\praba\Ai FrontOffice Manager\Ai-FrontOffice-Manager"
.\.venv\Scripts\activate
```

### 2. Install Dependencies (if not done)
```powershell
pip install -r requirements.txt
```

### 3. Create Environment File
```powershell
# Copy template
Copy-Item .env.example .env

# Edit .env with your credentials
notepad .env
```

**Required in `.env`**:
- `WHATSAPP_ACCESS_TOKEN` - From Meta Business Suite
- `WHATSAPP_PHONE_NUMBER_ID` - From Meta Business Suite
- `WEBHOOK_VERIFY_TOKEN` - Choose any secure string

### 4. Verify Google Sheets Connection
```powershell
python -c "from sheets_manager import get_sheets_manager; sm = get_sheets_manager(); print(f'Products: {len(sm.get_products())}')"
```

---

## ▶️ Running the Webhook Server

### Start Server
```powershell
python webhook.py
```

**Expected output**:
```
INFO - 🚀 WhatsApp Webhook Server Starting...
INFO - 📦 Products loaded: 3
INFO - 🔑 Keywords indexed: 8
INFO - 🌐 Starting Flask server on port 5000
```

### Test Health Check
Open browser: http://localhost:5000/health

---

## 🌐 Expose with ngrok (Development)

### In a New Terminal:
```powershell
ngrok http 5000
```

**Copy the HTTPS URL** (e.g., `https://abc123.ngrok.io`)

### Configure in Meta Business Suite:
1. Go to **WhatsApp → Configuration**
2. **Callback URL**: `https://your-ngrok-url.ngrok.io/webhook`
3. **Verify Token**: (same as your `.env`)
4. Subscribe to: **messages**

---

## 📋 Daily Follow-up Automation

### Run Manually:
```powershell
python follow_up_scheduler.py
```

### Schedule Automatically:

**Option 1: Task Scheduler GUI**
- Open Task Scheduler
- Create Basic Task: "AI Followups"
- Daily at 9:00 AM
- Action: Start program
  - Program: `C:\Users\praba\Ai FrontOffice Manager\Ai-FrontOffice-Manager\.venv\Scripts\python.exe`
  - Arguments: `follow_up_scheduler.py`
  - Start in: `C:\Users\praba\Ai FrontOffice Manager\Ai-FrontOffice-Manager`

**Option 2: PowerShell Command**
```powershell
# Create scheduled task
$action = New-ScheduledTaskAction -Execute "C:\Users\praba\Ai FrontOffice Manager\Ai-FrontOffice-Manager\.venv\Scripts\python.exe" -Argument "follow_up_scheduler.py" -WorkingDirectory "C:\Users\praba\Ai FrontOffice Manager\Ai-FrontOffice-Manager"
$trigger = New-ScheduledTaskTrigger -Daily -At 9am
Register-ScheduledTask -TaskName "AI_FrontOffice_Followups" -Action $action -Trigger $trigger
```

---

## 🧪 Run Tests

```powershell
pytest test_webhook.py -v
```

---

## 🔧 Common Commands

### Check Python Version
```powershell
python --version
# Should be 3.8+
```

### Check Installed Packages
```powershell
pip list
```

### Update Dependencies
```powershell
pip install -r requirements.txt --upgrade
```

### View Recent Logs
```powershell
# While webhook.py is running, logs appear in terminal
# For production, redirect to file:
python webhook.py > webhook.log 2>&1
```

---

## 📊 Google Sheets Quick Check

### Verify Sheet Access:
1. Open: https://docs.google.com/spreadsheets
2. Find: `AI_Front_Office_Manager`
3. Check tabs: `STOCK_MASTER`, `LEADS_ACTIVE`, `LEADS_COLD`

### Add New Product:
Go to `STOCK_MASTER` sheet, add row:
```
Product_Name: Wire 2.5mm
Brand: Polycab
Base_Price: 120
Available_Qty: 100
```

**Restart webhook.py** to load new products.

---

## 🐛 Quick Troubleshooting

### "Module not found"
```powershell
# Activate venv
.\.venv\Scripts\activate
```

### "Google Sheets permission denied"
- Check service account email in `credentials.json`
- Verify it has Editor access to the sheet

### "Webhook verification failed"
- Check `WEBHOOK_VERIFY_TOKEN` matches in `.env` and Meta Business Suite
- Ensure ngrok is running

### WhatsApp messages not arriving
- Check ngrok tunnel is active
- Verify webhook is subscribed to `messages` event
- Look for errors in webhook.py terminal

---

## 📞 Test Conversation Flow

### Complete Example:

1. Send from phone: **"hi"**
   - Bot: "Good morning sir! 🙏 Welcome to our electrical shop..."

2. Send: **"LED bulb"**
   - Bot: "Yes sir, LED Bulb 9W is available. Price ₹50. How many quantity do you need?"

3. Send: **"5"**
   - Bot: "Perfect sir 👍 Noted 5 quantity for LED Bulb 9W. Total: ₹250. Anything else?"

4. Send: **"LED bulb"** (again)
   - Bot: "Sir, we already noted your enquiry for LED Bulb 9W. Quantity: 5..."

5. Check Google Sheets → `LEADS_ACTIVE`
   - ✅ Single lead row with quantity 5

---

## 🔄 Restart Everything

```powershell
# Stop webhook (Ctrl+C)
# Stop ngrok (Ctrl+C)

# Restart
python webhook.py
# In new terminal: ngrok http 5000
```

---

## 📁 Project File Overview

| File | Purpose |
|------|---------|
| `webhook.py` | Main Flask webhook server |
| `sheets_manager.py` | Google Sheets operations |
| `send_whatsapp.py` | WhatsApp API client |
| `config.py` | Configuration management |
| `follow_up_scheduler.py` | Automated follow-ups |
| `.env` | Your credentials (NOT in git) |
| `credentials.json` | Google service account (NOT in git) |
| `requirements.txt` | Python dependencies |

---

## 📚 Full Documentation

- **Detailed Setup**: See `deployment_guide.md` artifact
- **All Changes**: See `walkthrough.md` artifact
- **Code Analysis**: See `code_analysis.md` artifact
- **Architecture**: See `implementation_plan.md` artifact

---

## ✅ Success Checklist

- [ ] Virtual environment activated
- [ ] Dependencies installed
- [ ] `.env` file created with credentials
- [ ] Google Sheets accessible
- [ ] `webhook.py` starts without errors
- [ ] Health check returns 200
- [ ] ngrok tunnel running
- [ ] Meta webhook verified
- [ ] Test message works end-to-end
- [ ] Lead appears in Google Sheets
- [ ] Follow-up scheduler runs successfully

---

## 🎯 You're Ready!

Your AI Front Office Manager is now live and handling customer enquiries automatically! 🎉

**Monitor the webhook.py terminal** to see real-time message processing.
