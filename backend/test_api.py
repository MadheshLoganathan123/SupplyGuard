from fastapi.testclient import TestClient
from main import app
import traceback

client = TestClient(app)
try:
    response = client.get("/api/v1/shipments")
    print("Status:", response.status_code)
    try:
        print("Body:", response.json())
    except:
        print("Body:", response.text)
except Exception as e:
    traceback.print_exc()
