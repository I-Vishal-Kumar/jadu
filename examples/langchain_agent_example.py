"""Example of using the Audio Transcription tools with a LangChain agent."""

import asyncio
from typing import List

from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage

from src.config import settings
from src.tools import get_all_tools


def create_audio_processing_agent(provider: str = "openai") -> AgentExecutor:
    """
    Create a LangChain agent with audio processing capabilities.

    Args:
        provider: LLM provider to use ('openai' or 'anthropic')

    Returns:
        AgentExecutor configured with audio processing tools
    """
    # Get all audio processing tools
    tools = get_all_tools()

    # Create LLM based on provider
    if provider == "openai":
        llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0,
            api_key=settings.openai_api_key,
        )
    elif provider == "anthropic":
        llm = ChatAnthropic(
            model="claude-sonnet-4-20250514",
            temperature=0,
            api_key=settings.anthropic_api_key,
        )
    else:
        raise ValueError(f"Unsupported provider: {provider}")

    # Create prompt template
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an AI assistant specialized in audio transcription and analysis.
You have access to the following capabilities:
1. Transcribe audio files to text
2. Translate text between languages
3. Summarize text content
4. Detect intent and sentiment in text
5. Extract keywords and topics from text

When given an audio file, you can process it through various analysis stages.
Always explain what you're doing and provide clear, structured results.

If the user asks about audio content, first transcribe it, then perform the requested analysis."""),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    # Create agent
    agent = create_tool_calling_agent(llm, tools, prompt)

    # Create executor
    executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        max_iterations=10,
        handle_parsing_errors=True,
    )

    return executor


class AudioProcessingChatbot:
    """Interactive chatbot for audio processing tasks."""

    def __init__(self, provider: str = "openai"):
        self.agent = create_audio_processing_agent(provider)
        self.chat_history: List = []

    async def chat(self, message: str) -> str:
        """
        Send a message to the chatbot and get a response.

        Args:
            message: User message

        Returns:
            Agent response
        """
        response = await self.agent.ainvoke({
            "input": message,
            "chat_history": self.chat_history,
        })

        # Update chat history
        self.chat_history.append(HumanMessage(content=message))
        self.chat_history.append(AIMessage(content=response["output"]))

        return response["output"]

    def reset(self):
        """Reset chat history."""
        self.chat_history = []


async def example_agent_conversation():
    """Example conversation with the audio processing agent."""
    print("=" * 60)
    print("Audio Processing Agent Demo")
    print("=" * 60)

    chatbot = AudioProcessingChatbot(provider="openai")

    # Example conversation
    conversations = [
        "Can you summarize this text: 'Our company has achieved record sales this quarter, driven by strong performance in the Asian market. We're planning to expand our product line next year.'",
        "What is the intent behind this message: 'I've been waiting for two weeks and still haven't received my order. This is unacceptable!'",
        "Extract the key topics from: 'Machine learning models are being used in healthcare to predict patient outcomes, diagnose diseases from medical images, and optimize treatment plans.'",
    ]

    for message in conversations:
        print(f"\n👤 User: {message}\n")
        response = await chatbot.chat(message)
        print(f"🤖 Agent: {response}\n")
        print("-" * 40)


async def example_audio_file_processing():
    """Example of processing an audio file through the agent."""
    print("=" * 60)
    print("Audio File Processing Demo")
    print("=" * 60)

    chatbot = AudioProcessingChatbot(provider="openai")

    # Note: Replace with actual audio file path
    audio_path = "path/to/your/audio.mp3"

    message = f"""Please process the audio file at '{audio_path}' and:
1. Transcribe it
2. Summarize the content
3. Detect the intent
4. Extract key topics"""

    print(f"👤 User: {message}\n")
    response = await chatbot.chat(message)
    print(f"🤖 Agent: {response}")


async def interactive_mode():
    """Run an interactive chat session."""
    print("=" * 60)
    print("Interactive Audio Processing Agent")
    print("Type 'quit' to exit, 'reset' to clear history")
    print("=" * 60)

    chatbot = AudioProcessingChatbot(provider="openai")

    while True:
        try:
            user_input = input("\n👤 You: ").strip()

            if user_input.lower() == "quit":
                print("Goodbye!")
                break
            elif user_input.lower() == "reset":
                chatbot.reset()
                print("Chat history cleared.")
                continue
            elif not user_input:
                continue

            response = await chatbot.chat(user_input)
            print(f"\n🤖 Agent: {response}")

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")


async def main():
    """Run the examples."""
    # Run demo conversation
    await example_agent_conversation()

    # Uncomment for interactive mode
    # await interactive_mode()

    # Uncomment to process actual audio file
    # await example_audio_file_processing()


if __name__ == "__main__":
    asyncio.run(main())
