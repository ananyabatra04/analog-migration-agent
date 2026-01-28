import asyncio
import logging
from agent_framework import ChatAgent, ai_function
from agent_framework.openai import OpenAIResponsesClient

from query_engine import PDKQueryEngine

from typing import Annotated
from pydantic import Field
import os

logging.getLogger("lightrag").setLevel(logging.ERROR)
logging.getLogger("raganything").setLevel(logging.ERROR)
logging.getLogger("nano-vectordb").setLevel(logging.ERROR)

# Initialize your RAG engine
pdk_engine = PDKQueryEngine(pdk_name="skywater130")

@ai_function(
    name="query_pdk_knowledge_base", 
    description="Retrieves technical specifications, device types, and design rules for the Skywater 130nm PDK."
)
async def query_pdk(
    question: Annotated[str, Field(description="The specific technical question about the PDK.")]
) -> str:
    """Useful for answering questions about transistors, layers, and voltage domains."""
    try:
        # We use hybrid mode for high-quality technical answers
        result = await pdk_engine.query(question, mode="hybrid")
        return str(result)
    except Exception as e:
        return f"Error retrieving data: {str(e)}"
    

async def main():
    # 1. Initialize the specific OpenAI Responses client
    client = OpenAIResponsesClient(
        model_id="gpt-4o",
        api_key=os.getenv("OPENAI_API_KEY")
    )

    # 2. Create the Agent using ChatAgent explicitly
    agent = ChatAgent(
        chat_client=client,
        name="PDKExpert",
        instructions="You are a senior analog engineer. Use your tools to answer PDK questions.",
        tools=[query_pdk]
    )

    # 3. Run the conversation
    result = await agent.run("What are the voltage limits for the Skywater 130 nm NFET?")
    print(f"Agent: {result.text}")

if __name__ == "__main__":
    asyncio.run(main())