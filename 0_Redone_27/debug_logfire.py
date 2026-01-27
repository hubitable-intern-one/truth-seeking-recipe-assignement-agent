import logfire
import time

# 1. HARDCODE the token you gave me (ensure no spaces around it)
# TEST_TOKEN = "pylf_v2_us_dcbdf21c-e172-44fa-ade9-95e3679e07c4_pwW1b0H58SJLpqb7bs11Hl1mKBLqlpvsZvRddbbl5htj"
TEST_TOKEN = "pylf_v1_us_n9r2Zl1ML2xnD8WWRDbZG8hZktB9PDN1v4551PxSTpL6"

print(f"🔑 Testing Token: {TEST_TOKEN[:10]}...")

try:
    # 2. Configure with the specific token
    logfire.configure(token=TEST_TOKEN)
    
    # 3. Send a test log
    with logfire.span("Debug Connection Test"):
        logfire.info("Hello from the debugger!")
        time.sleep(1)
        
    print("\n✅ SUCCESS! The token is valid.")
    print("Check your dashboard for a 'Debug Connection Test' entry.")

except Exception as e:
    print(f"\n❌ FAILURE: {e}")