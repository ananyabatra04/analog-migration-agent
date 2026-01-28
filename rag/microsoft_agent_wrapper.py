import asyncio
import logging
import os
import warnings
from typing import Annotated
from pydantic import Field
from dotenv import load_dotenv

from agent_framework import ChatAgent, ai_function
from agent_framework.openai import OpenAIResponsesClient
from query_engine import PDKQueryEngine

load_dotenv()
logging.getLogger("lightrag").setLevel(logging.ERROR)
logging.getLogger("raganything").setLevel(logging.ERROR)
logging.getLogger("nano-vectordb").setLevel(logging.ERROR)
warnings.filterwarnings("ignore")

pdk_engine = PDKQueryEngine(pdk_name="skywater130")

# Query tool
@ai_function(
    name="query_pdk_knowledge_base", 
    description="Retrieves technical specifications, device types, and design rules for the Skywater 130nm PDK."
)
async def query_pdk(
    question: Annotated[str, Field(description="The specific technical question about the PDK.")]
) -> str:
    try:
        result = await pdk_engine.query(question, mode="hybrid")
        
        return str(result)
    except Exception as e:
        return f"Error retrieving data from PDK Knowledge Base: {str(e)}"

# 4. Main Interactive Loop
async def main():
    # Initialize the client (Note: model_id is used per your version's error message)
    client = OpenAIResponsesClient(
        model_id="gpt-4o",
        api_key=os.getenv("OPENAI_API_KEY")
    )

    # Create the Agent
    agent = ChatAgent(
        chat_client=client,
        name="PDKExpert",
        instructions="""You are a senior analog design engineer specializing in the Skywater 130nm node. 
        Always use the query_pdk_knowledge_base tool to answer technical questions. 
        Always reference the PDK docs""",
        tools=[query_pdk]
    )

    # Thread for conversation memory
    thread = agent.get_new_thread()
    
    print("="*60)
    print("Ask questions about Skywater 130nm (Type 'exit' to quit)")
    print("="*60)

    while True:
        try:
            user_input = input("\n You: ")
            
            if user_input.lower() in ["exit"]:
                break
            
            result = await agent.run(user_input, thread=thread)
            
            print(f"\n Agent: {result.text}")
            
        except KeyboardInterrupt:
            print("\n Session ended.")
            break
        except Exception as e:
            print(f"\n An error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(main())