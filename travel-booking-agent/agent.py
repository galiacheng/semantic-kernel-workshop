import os
import logging
from uuid import uuid4
from typing import Annotated

import httpx
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse

from agent_framework import ChatAgent, AgentThread
from agent_framework.azure import AzureOpenAIChatClient
from azure.identity import DefaultAzureCredential

from a2a.client import A2ACardResolver, A2AClient
from a2a.types import MessageSendParams, SendMessageRequest

load_dotenv("../.env")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Configuration
SERVER_HOST = "localhost"
SERVER_PORT = 8080
FLIGHT_BOOKING_AGENT_URL = os.getenv("A2A_SERVER_URL")

# Initialize FastAPI app
app = FastAPI(title="Travel Booking Agent",
              description="A travel planning assistant with flight booking capabilities")

# Global thread store
thread_store: dict[str, AgentThread] = {}


class FlightBookingTool:
    """Tool for booking flights using the flight booking agent."""

    async def book_flight(self, user_input: Annotated[str, "The user's flight booking request"]) -> str:
        """
        Book a flight using the external flight booking agent.

        Args:
            user_input: The user's flight booking request

        Returns:
            The response from the flight booking agent
        """
        try:
            async with httpx.AsyncClient() as httpx_client:
                resolver = A2ACardResolver(
                    httpx_client=httpx_client, base_url=FLIGHT_BOOKING_AGENT_URL)
                agent_card = await resolver.get_agent_card()

                client = A2AClient(httpx_client=httpx_client,
                                   agent_card=agent_card)

                request = SendMessageRequest(
                    id=str(uuid4()),
                    params=MessageSendParams(
                        message={
                            "messageId": uuid4().hex,
                            "role": "user",
                            "parts": [{"text": user_input}],
                            "contextId": "travel_booking_context",
                        }
                    )
                )

                response = await client.send_message(request)
                result = response.model_dump(mode="json", exclude_none=True)

                logger.info(f"Flight booking tool response: {result}")
                return result["result"]["parts"][0]["text"]

        except Exception as e:
            logger.error(f"Error booking flight: {e}")
            return f"Sorry, I encountered an error while trying to book your flight: {e!s}"


def create_travel_agent() -> ChatAgent:
    """Create and configure the travel planning agent."""
    # Create Azure OpenAI client
    client = AzureOpenAIChatClient(
        credential=DefaultAzureCredential()
    )

    # Create tool instance
    flight_tool = FlightBookingTool()

    # Create agent with tools
    return client.create_agent(
        instructions=(
            "You are a helpful travel planning assistant. "
            "Use the provided tools to assist users with their travel plans. "
            "When users ask about flights, use the book_flight tool to help them."
        ),
        tools=[flight_tool.book_flight]
    )


def get_or_create_thread(context_id: str) -> AgentThread:
    """Get existing thread or create a new one for the given context."""
    thread = thread_store.get(context_id)

    if thread is None:
        # Let the agent create a new thread
        thread = travel_planning_agent.get_new_thread()
        thread_store[context_id] = thread
        logger.info(f"Created new thread for context ID: {context_id}")

    return thread


# Initialize the travel agent
travel_planning_agent = create_travel_agent()


@app.post("/chat")
async def chat(user_input: str = Form(...), context_id: str = Form("default")):
    """
    Handle chat requests from users.

    Args:
        user_input: The user's message
        context_id: Context identifier for maintaining chat history

    Returns:
        JSON response with the agent's reply
    """
    logger.info(
        f"Received chat request: {user_input} with context ID: {context_id}")

    try:
        # Get or create thread for the context
        thread = get_or_create_thread(context_id)

        # Get response from the agent
        response = await travel_planning_agent.run(user_input, thread=thread)

        logger.info(f"Travel agent response: {response.text}")

        return {"response": response.text}

    except Exception as e:
        logger.error(f"Error processing chat request: {e}")
        return {"response": "Sorry, I encountered an error processing your request. Please try again."}


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Serve the main HTML interface."""
    try:
        html_path = os.path.join(os.path.dirname(__file__), "index.html")
        logger.info(f"Loading HTML from: {html_path}")
        with open(html_path, "r", encoding="utf-8") as f:  # noqa: ASYNC230
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except FileNotFoundError:
        logger.error("index.html file not found")
        return HTMLResponse(
            content="<h1>Error: index.html not found!</h1>",
            status_code=404
        )


def main() -> None:
    """Main entry point for the travel booking agent server."""
    logger.info("Starting Travel Booking Agent Server.")
    logger.info(f"Starting server on {SERVER_HOST}:{SERVER_PORT}")
    uvicorn.run(app, host=SERVER_HOST, port=SERVER_PORT)


if __name__ == "__main__":
    main()
