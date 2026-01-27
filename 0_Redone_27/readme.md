📂 Project Structure
1. The Brain (AI Logic)
agents/truth_seeking_agent.py: The core AI logic.

Defines the Agent (Llama 3 on Groq).

Sets the System Prompt (Clinical Dietitian Persona).

Manages the tool usage (Web Search) to prevent hallucinations.

models/recipe_context.py: The Data Contract.

Defines the strict Pydantic Models for the output.

Enforces rules like Verdict.AVOID (Enum) and ensures the output is valid JSON.

config/synthetic_users.py: The Patient Database.

Contains the 6 Clinical Profiles (Type 1 Diabetic, Renal Patient, Bodybuilder, etc.) used for testing and analysis.

2. The Body (Backend & Processing)
worker.py: The Task Manager.

Listens for jobs from the queue.

Runs the truth_seeking_agent.

Routing Logic:

✅ Success: Saves result to MongoDB collection new job.

❌ Failure: Saves error log to MongoDB collection failed job 2.

tools/web_search_tool.py: The Eyes.

Performs optimized, parallel web searches using DuckDuckGo.

Includes logic to prevent rate limiting.

tools/verifier_tool.py: The Auditor.

"Ghostbusters" logic that visits the URLs found by the search to ensure they are real (HTTP 200) and contain relevant text

📊 Data Flow
Select: User picks a recipe in the Streamlit App (app.py).

Queue: App sends the recipe text + ID to Redis.

Process: Worker (worker.py) picks up the job.

Analyze: Worker calls the Agent (truth_seeking_agent.py).

Agent checks synthetic_users.py for the 6 profiles.

Agent calls web_search_tool.py to find evidence.

Save:

If successful, Worker saves the full JSON report to MongoDB collection new job.

If failed (crash/timeout), Worker saves the error to failed job 2.

Display: Streamlit polls the job status and renders the results once complete.

🛠 Configuration
MONGO_URI: Set this in your .env file (defaults to localhost).

GROQ_API_KEY: Required for Llama 3 inference.

LOGFIRE_TOKEN: Optional, for observability logging.