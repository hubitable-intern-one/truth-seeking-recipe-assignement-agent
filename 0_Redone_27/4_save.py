import asyncio
import os
import json
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Load environment variables (for Mongo URI)
load_dotenv()

async def main():
    # 1. Connect to MongoDB
    # Uses the same connection string as your app
    uri = os.getenv("MONGO_URI", "mongodb://root:password@localhost:27017")
    client = AsyncIOMotorClient(uri)
    collection = client.recipe_crawler.recipes

    print("🕵️‍♂️ Connecting to MongoDB to check for saved reports...")

    # 2. Query: Find recipes where the 'analysis' field exists
    # "$exists": True checks if the field is present in the document
    cursor = collection.find({"analysis": {"$exists": True}})
    
    found_count = 0
    
    # 3. Iterate and Print
    async for recipe in cursor:
        found_count += 1
        title = recipe.get('title', 'Unknown Title')
        score = recipe.get('health_score', 'N/A')
        job_id = recipe.get('last_analyzed', 'N/A')
        
        print(f"\n==================================================")
        print(f"✅ FOUND ANALYZED RECIPE: {title}")
        print(f"==================================================")
        print(f"   ❤️ Health Score: {score}/100")
        print(f"   🆔 Job ID:       {job_id}")
        print(f"   📂 Database ID:  {recipe.get('_id')}")
        print(f"\n   📄 SAVED JSON CONTENT (Snippet):")
        
        # Get the analysis object
        analysis_data = recipe.get('analysis', {})
        
        # Pretty print it (formatted JSON)
        # We dump it to a string with indentation for readability
        json_str = json.dumps(analysis_data, indent=2)
        print(json_str)
        print("\n")

    if found_count == 0:
        print("\n❌ No analyzed recipes found.")
        print("   (Tip: Run a job via 'python 3_testq.py' or the Streamlit App first!)")
    else:
        print(f"🎉 Total Analyzed Recipes Found: {found_count}")

if __name__ == "__main__":
    asyncio.run(main())