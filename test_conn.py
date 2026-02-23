import urllib.request
import sys

def test_ping(url):
    try:
        print(f"Testing {url} ...")
        with urllib.request.urlopen(url, timeout=5) as response:
            status = response.getcode()
            body = response.read().decode()
            print(f"Status: {status}")
            print(f"Body: {body}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8081/ping"
    test_ping(url)
