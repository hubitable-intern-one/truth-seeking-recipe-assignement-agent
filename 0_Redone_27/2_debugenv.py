import os
from dotenv import load_dotenv

# Force reload of .env
print("HIHII")
load_dotenv(override=True)

token = os.getenv("LOGFIRE_TOKEN")

print("-" * 30)
if token:
    print(f"✅ SUCCESS: Found token starting with: {token[:10]}...")
    print(f"   Token Length: {len(token)} characters")
    
    # Check for accidental spaces (Common mistake!)
    if " " in token:
        print("❌ ERROR: Your token has spaces in it! Check your .env file.")
    else:
        print("✅ FORMAT: No spaces found. Looks good.")
else:
    print("❌ FAILURE: Could not find LOGFIRE_TOKEN in .env file.")
    print(f"   Current Working Directory: {os.getcwd()}")
    print("   Make sure .env is in this folder!")
print("-" * 30)