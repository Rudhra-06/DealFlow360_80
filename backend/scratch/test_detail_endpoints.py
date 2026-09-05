import urllib.request
import json
import sys

base_url = "http://127.0.0.1:8000/api/v1"

# Login to get token
login_data = json.dumps({"email": "salesrep.demo@example.com", "password": "DealFlow360Demo123!"}).encode('utf-8')
req = urllib.request.Request(f"{base_url}/auth/login", data=login_data, headers={"Content-Type": "application/json"})
with urllib.request.urlopen(req) as resp:
    res = json.loads(resp.read().decode('utf-8'))
    token = res["access_token"]
    print("Token acquired.")

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

# 1. Test List Invoices
req = urllib.request.Request(f"{base_url}/invoices?limit=10", headers=headers)
with urllib.request.urlopen(req) as resp:
    inv_list = json.loads(resp.read().decode('utf-8'))
    print(f"List Invoices returned {len(inv_list)} invoices.")

# 2. Test Get Invoice Detail for each invoice
for inv in inv_list[:3]:
    inv_id = inv["id"]
    try:
        req = urllib.request.Request(f"{base_url}/invoices/{inv_id}", headers=headers)
        with urllib.request.urlopen(req) as resp:
            inv_detail = json.loads(resp.read().decode('utf-8'))
            print(f"Invoice {inv_id} GET detail OK: {inv_detail.get('invoice_number')}")
    except Exception as e:
        print(f"Invoice {inv_id} GET detail FAILED: {e}")

# 3. Test List Subscriptions
req = urllib.request.Request(f"{base_url}/subscriptions?limit=10", headers=headers)
with urllib.request.urlopen(req) as resp:
    sub_list = json.loads(resp.read().decode('utf-8'))
    print(f"List Subscriptions returned {len(sub_list)} subscriptions.")

# 4. Test Get Subscription Detail for each subscription
for sub in sub_list[:3]:
    sub_id = sub["id"]
    try:
        req = urllib.request.Request(f"{base_url}/subscriptions/{sub_id}", headers=headers)
        with urllib.request.urlopen(req) as resp:
            sub_detail = json.loads(resp.read().decode('utf-8'))
            print(f"Subscription {sub_id} GET detail OK: {sub_detail.get('subscription_number')} (Schedules: {len(sub_detail.get('schedules', []))})")
    except Exception as e:
        print(f"Subscription {sub_id} GET detail FAILED: {e}")
