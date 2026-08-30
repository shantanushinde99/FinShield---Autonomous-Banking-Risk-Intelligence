import httpx
import sys
import time

def simulate_omi_webhook(text: str, session_id: str = "demo_session_123"):
    url = "http://127.0.0.1:8000/api/v1/omi/webhook"
    
    payload = {
        "text": text,
        "session_id": session_id,
        "speaker": "bank_officer_1",
        "is_final": True
    }
    
    print(f"\n[USER SPEAKS] -> '{text}'")
    print("Sending transcript to FinShield Omi Webhook...")
    
    start = time.time()
    try:
        response = httpx.post(url, json=payload, timeout=120.0)
        duration = time.time() - start
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n[FINSHIELD RESPONDS] ({duration:.2f}s)")
            print(f"Status        : {data.get('status')}")
            print(f"Customer      : {data.get('customer_id')}")
            print(f"Risk Level    : {data.get('risk_level')}")
            print(f"Recommendation: {data.get('recommendation')}")
            print(f"Confidence    : {data.get('confidence')}")
            print(f"\n[VOICE SYNTHESIS]")
            print(f"\"{data.get('spoken_summary')}\"")
        else:
            print(f"Error: {response.status_code} - {response.text}")
            
    except httpx.RequestError as e:
        print(f"Failed to connect to API. Is the server running? Run 'python scripts/run_api.py'. Error: {e}")

if __name__ == "__main__":
    print("="*60)
    print("FINSHIELD - PHASE 6: OMI VOICE INTEGRATION DEMO")
    print("="*60)
    
    commands = [
        "Hello, how are you?",  # Should be rejected (unsupported intent)
        "Investigate the customer.",  # Should ask for clarification
        "Investigate customer FIN_000001.",  # Valid command -> Will take some time
        "Investigate customer FIN_000001."   # Should trigger duplicate protection
    ]
    
    # If a specific command was passed via CLI args
    if len(sys.argv) > 1:
        simulate_omi_webhook(" ".join(sys.argv[1:]))
    else:
        for cmd in commands:
            simulate_omi_webhook(cmd)
            time.sleep(2)
