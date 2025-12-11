from pydantic_ai import Agent, WebSearchTool

websearch = WebSearchTool(
    api_key=os.getenv("TAVILY_API_KEY"),
    max_results=5,
    include_images=False,
    bing_domain="api.bing.microsoft.com"
)

truth_agent = Agent(
    'groq/compound', builtin_tools=[WebSearchTool()]
)