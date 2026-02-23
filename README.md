# AI Front Office Manager

AI-powered WhatsApp assistant for electrical shops that automatically handles customer enquiries, captures leads, and manages follow-ups.

## 🎯 Features

- ✅ **WhatsApp Cloud API Integration** - Official Meta Business API
- ✅ **Smart Product Detection** - Keyword-based product matching
- ✅ **Slot-based Conversation** - Structured enquiry capture (Product → Quantity)
- ✅ **Lead Management** - Google Sheets as CRM
- ✅ **Duplicate Prevention** - Intelligent lead deduplication
- ✅ **Automated Follow-ups** - Scheduled reminder system
- ✅ **Cold Lead Management** - Automatic lead aging

## 📋 Prerequisites

- Python 3.8+
- WhatsApp Business API account (Meta)
- Google Cloud project with Sheets API enabled
- ngrok (for local webhook testing)

## 🚀 Setup Instructions

### 1. Clone Repository

```bash
git clone <your-repo>
cd Ai-FrontOffice-Manager
```

### 2. Install Dependencies

```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
# or
source .venv/bin/activate  # Linux/Mac

pip install -r requirements.txt
```

### 3. Configure Environment Variables

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env` with your actual values:
```
WHATSAPP_ACCESS_TOKEN=your_token_here
WHATSAPP_PHONE_NUMBER_ID=your_phone_id_here
WEBHOOK_VERIFY_TOKEN=your_custom_token
```

### 4. Set Up Google Sheets

1. Create a Google Cloud project
2. Enable Google Sheets API and Google Drive API
3. Create a service account and download `credentials.json`
4. Place `credentials.json` in the project root
5. Create a Google Sheet named `AI_Front_Office_Manager` with sheets:
   - `STOCK_MASTER` (columns: Product_Name, Brand, Base_Price, Available_Qty)
   - `LEADS_ACTIVE` (columns: Lead_ID, Customer_Name, Phone, Customer_Message, Product_ID, Product_Name, Brand, Quantity_Asked, Price_Shown, Lead_Date, Lead_Time, Status, Last_Action_Date, Last_Reminder_Date, No.of_Reminders_Pending)
   - `LEADS_COLD` (same structure as LEADS_ACTIVE)
6. Share the sheet with your service account email

### 5. Run the Webhook Server

```bash
python webhook.py
```

### 6. Expose with ngrok (for testing)

```bash
ngrok http 5000
```

Copy the ngrok URL and configure it in Meta Business Suite:
- Go to WhatsApp > Configuration
- Set Webhook URL: `https://your-ngrok-url.ngrok.io/webhook`
- Set Verify Token: (same as in your .env)
- Subscribe to `messages` events

## 🔄 Follow-up Automation

Run the follow-up scheduler daily to send reminders:

```bash
python follow_up_scheduler.py
```

**Recommended**: Set up a cron job (Linux) or Task Scheduler (Windows) to run this daily.

## 📁 Project Structure

```
.
├── webhook.py              # Main Flask webhook server
├── sheets_manager.py       # Google Sheets abstraction
├── send_whatsapp.py        # WhatsApp API integration
├── config.py               # Configuration management
├── follow_up_scheduler.py  # Automated follow-ups
├── requirements.txt        # Python dependencies
├── .env.example           # Environment template
└── credentials.json       # Google service account (not in git)
```

## 🎮 Usage

### Customer Flow

1. Customer sends: "LED bulb"
2. Bot replies: "Yes sir, LED Bulb 9W is available. Price ₹50. How many quantity do you need?"
3. Customer sends: "5"
4. Bot replies: "Perfect sir 👍 Noted 5 quantity for LED Bulb 9W. Total: ₹250. Anything else?"

### Conversation Rules

- **One lead per product per customer**
- **Duplicate prevention**: If same product mentioned again, bot acknowledges existing enquiry
- **Quantity validation**: Only numeric input accepted as quantity
- **Context awareness**: Remembers what product is waiting for quantity

## 🔧 Configuration

Edit `.env` to customize:

```
DEFAULT_REMINDERS=3           # Number of follow-up reminders
DAYS_BEFORE_REMINDER=2        # Days between reminders
FLASK_PORT=5000              # Webhook server port
DEBUG_MODE=False             # Enable debug logging
```

## 📊 Google Sheets Structure

### STOCK_MASTER
| Product_Name | Brand | Base_Price | Available_Qty |
|-------------|-------|------------|---------------|
| LED Bulb 9W | Philips | 50 | 100 |

### LEADS_ACTIVE
| Lead_ID | Phone | Product_Name | Quantity_Asked | Status | ... |
|---------|-------|--------------|----------------|--------|-----|
| abc123 | 91... | LED Bulb 9W | 5 | ACTIVE | ... |

## 🐛 Troubleshooting

### Webhook not receiving messages
- Check ngrok is running
- Verify webhook URL in Meta Business Suite
- Check verify token matches

### Google Sheets errors
- Verify service account has access to sheet
- Check sheet name matches exactly
- Ensure all required columns exist

### WhatsApp API errors
- Verify access token is valid
- Check phone number ID is correct
- Ensure 24-hour conversation window

## 📈 Roadmap

- [ ] Multi-slot support (color, size)
- [ ] OpenAI integration for better NLU
- [ ] Image-based product detection
- [ ] Admin dashboard
- [ ] Multi-shop support (SaaS)

## 📝 License

Proprietary - For internal use only

## 👨‍💻 Author

Built for electrical shops in India
