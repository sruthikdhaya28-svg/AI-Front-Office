"""
Simple webhook test - NO Google Sheets needed
This tests your WhatsApp integration only
"""
from flask import Flask, request
from config import Config
from send_whatsapp import send_whatsapp_message

app = Flask(__name__)

print("🚀 Simple WhatsApp Test Server Starting...")
print(f"✅ Config loaded - Port {Config.FLASK_PORT}")

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    # Verification (GET)
    if request.method == "GET":
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        
        if mode == "subscribe" and token == Config.WEBHOOK_VERIFY_TOKEN:
            print("✅ Webhook verified!")
            return challenge, 200
        return "Forbidden", 403
    
    # Message handling (POST)
    data = request.get_json()
    
    try:
        # Check if this is a message event
        value = data["entry"][0]["changes"][0]["value"]
        
        if "messages" not in value:
            print("⏭️ Not a message event")
            return "EVENT_RECEIVED", 200
        
        # Get message
        message = value["messages"][0]
        phone = message["from"]
        text = message["text"]["body"]
        
        print(f"📨 Message from {phone}: {text}")
        
        # Simple echo reply
        reply = f"✅ Got your message: '{text}'\n\nThis is a test! Your WhatsApp integration is working! 🎉"
        
        send_whatsapp_message(phone, reply)
        print("✅ Reply sent!")
        
        return "EVENT_RECEIVED", 200
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return "EVENT_RECEIVED", 200

@app.route("/health")
def health():
    return {"status": "healthy", "test_mode": True}, 200

if __name__ == "__main__":
    print(f"🌐 Server starting on port {Config.FLASK_PORT}")
    print("📝 This is TEST MODE - no Google Sheets needed")
    app.run(port=Config.FLASK_PORT, debug=False)
