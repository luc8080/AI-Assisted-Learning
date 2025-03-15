from agents import Agent, Runner, AsyncOpenAI, OpenAIChatCompletionsModel, WebSearchTool
from dotenv import load_dotenv
import os

# use Google Gemini on OpenAI Agents SDK example
load_dotenv()

client = AsyncOpenAI(
    base_url=os.getenv("GOOGLE_GEMINI_ENDPOINT"),
    api_key=os.getenv("GOOGLE_GEMINI_API_KEY")
)

model = OpenAIChatCompletionsModel(
    model="gemini-2.0-flash",
    openai_client=client
)

agent = Agent(
    name="Assistant",
    instructions="You are a helpful assistant",
    model=model
)

result = Runner.run_sync(
    agent,
    "Write a haiku about recursion in programming."
)

print(result.final_output)
