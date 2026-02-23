from flask import Flask
app = Flask(__name__)

@app.route("/ping")
def ping():
    return "pong"

if __name__ == "__main__":
    print("Starting minimal server on 8081...")
    app.run(host='0.0.0.0', port=8081)
