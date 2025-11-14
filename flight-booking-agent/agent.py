import logging

from dotenv import load_dotenv

from agent_framework import AgentThread
from agent_framework.azure import AzureOpenAIChatClient
from azure.identity import DefaultAzureCredential

load_dotenv("../.env")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class SemanticKernelFlightBookingAgent:
    """A flight booking agent using Agent Framework and Azure OpenAI."""

    def __init__(self):
        """Initialize the flight booking agent with Azure OpenAI service."""
        logger.info("Initializing SemanticKernelFlightBookingAgent.")

        # Create Azure OpenAI client
        client = AzureOpenAIChatClient(
            credential=DefaultAzureCredential()
        )

        # Create agent with instructions
        self.chat_agent = client.create_agent(
            instructions=(
                "You are a helpful flight booking assistant. "
                "Your task is to help users book flights by gathering necessary information "
                "such as departure city, destination city, travel dates, number of passengers, "
                "and preferred class of service. Once you have all the required information, "
                "provide a confirmation summary and simulate a successful booking."
            )
        )

        # Store threads per context to maintain conversation state
        self.thread_store: dict[str, AgentThread] = {}

        logger.info(
            "SemanticKernelFlightBookingAgent initialized successfully.")

    def _get_or_create_thread(self, context_id: str) -> AgentThread:
        """Get existing thread or create a new one for the given context."""
        thread = self.thread_store.get(context_id)

        if thread is None:
            # Let the agent create a new thread
            thread = self.chat_agent.get_new_thread()
            self.thread_store[context_id] = thread
            logger.info(
                f"Created new thread for context ID: {context_id}")

        return thread

    async def book_flight(self, user_input: str, context_id: str) -> str:
        """
        Process a flight booking request from the user.

        Args:
            user_input: The user's request for flight booking
            context_id: The context ID for maintaining conversation state

        Returns:
            The response from the flight booking agent

        Raises:
            ValueError: If user input is empty
        """
        logger.info(
            f"Received flight booking request: {user_input} with context ID: {context_id}")

        if not user_input or not user_input.strip():
            logger.error("User input is empty.")
            raise ValueError("User input cannot be empty.")

        try:
            # Get or create thread for the context
            thread = self._get_or_create_thread(context_id)

            # Get response from the agent
            response = await self.chat_agent.run(user_input, thread=thread)

            logger.info(
                f"Flight booking agent response: {response.text}")

            return response.text

        except Exception as e:
            logger.error(f"Error processing flight booking request: {e}")
            return f"I apologize, but I encountered an error while processing your flight booking request: {e!s}"
