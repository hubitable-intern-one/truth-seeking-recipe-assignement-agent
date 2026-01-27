from tavily import TavilyClient

# 1. Initialize the client
# Replace with your actual API key from https://app.tavily.com/home
tavily = TavilyClient(api_key="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")

# 2. Run a simple search
print("🌍 Searching Tavily...")
response = tavily.search(query="Who won the Super Bowl in 2024?")

# 3. Print the results
# Tavily returns a dictionary with a 'results' list

# for result in response['results']:
#     print
#     print(f"\nTitle: {result['title']}")
#     print(f"URL: {result['url']}")
#     print(f"Content: {result['content'][:200]}...") # Print first 200 chars
print(type(response))
print(response)