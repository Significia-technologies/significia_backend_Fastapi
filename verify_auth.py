from fastapi.testclient import TestClient
from app.main import app
from app.database.session import engine
from app.database.base import Base

# Ensure the DB schema matches the models so tests run
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

client = TestClient(app)

print("--- Register User ---")
res = client.post("/api/v1/auth/register", json={
    "email": "test@example.com",
    "password": "password123",
    "company_name": "Acme Corp"
})
print(f"Status: {res.status_code}")
if res.status_code == 201:
    print(f"Data: {res.json()}")
else:
    print(f"Registration skipped or failed (User might exist): {res.json()}")

print("\n--- Login ---")
res = client.post("/api/v1/auth/login", json={
    "email": "test@example.com",
    "password": "password123"
})
print(f"Status: {res.status_code}")
login_data = res.json()
print(f"Data: {login_data}")
token = login_data.get("access_token")

if token:
    print("\n--- Protected /me Route ---")
    res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    print(f"Status: {res.status_code}")
    print(f"Data: {res.json()}")
