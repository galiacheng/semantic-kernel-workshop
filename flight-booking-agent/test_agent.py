import pytest
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock
from uuid import uuid4

from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase

from agent import SemanticKernelFlightBookingAgent
from agent_executor import SemanticKernelFlightBookingAgentExecutor


class TestSemanticKernelFlightBookingAgent:
    """Test suite for SemanticKernelFlightBookingAgent."""

    @pytest.fixture
    def mock_chat_agent(self):
        """Create a mock chat agent."""
        mock_agent = MagicMock()
        mock_agent.name = "FlightBookingAssistant"
        mock_agent.get_response = AsyncMock()
        return mock_agent

    @pytest.fixture
    def agent(self, mock_chat_agent):
        """Create a flight booking agent instance for testing."""
        mock_service = MagicMock(spec=ChatCompletionClientBase)
        mock_service.service_id = "test_service"
        with patch('agent.AzureChatCompletion', return_value=mock_service):
            with patch('agent.ChatCompletionAgent', return_value=mock_chat_agent):
                return SemanticKernelFlightBookingAgent()

    @pytest.fixture
    def mock_response(self):
        """Create a mock response from the chat agent."""
        mock_resp = MagicMock()
        mock_resp.content.content = "I'd be happy to help you book a flight. Where would you like to fly from?"
        return mock_resp

    @pytest.mark.asyncio
    async def test_initialization(self, agent):
        """Test that the agent initializes correctly."""
        assert agent.chat_agent is not None
        assert agent.chat_agent.name == "FlightBookingAssistant"
        assert isinstance(agent.history_store, dict)
        assert len(agent.history_store) == 0

    @pytest.mark.asyncio
    async def test_book_flight_success(self, agent, mock_response):
        """Test successful flight booking request."""
        context_id = str(uuid4())
        user_input = "I want to book a flight from Seattle to New York"

        agent.chat_agent.get_response.return_value = mock_response
        response = await agent.book_flight(user_input, context_id)

        assert response == mock_response.content.content
        assert context_id in agent.history_store
        assert len(agent.history_store[context_id].messages) == 3  # System + User + Assistant

    @pytest.mark.asyncio
    async def test_book_flight_empty_input(self, agent):
        """Test that empty input raises ValueError."""
        context_id = str(uuid4())

        with pytest.raises(ValueError, match="User input cannot be empty"):
            await agent.book_flight("", context_id)

    @pytest.mark.asyncio
    async def test_book_flight_whitespace_input(self, agent):
        """Test that whitespace-only input raises ValueError."""
        context_id = str(uuid4())

        with pytest.raises(ValueError, match="User input cannot be empty"):
            await agent.book_flight("   ", context_id)

    @pytest.mark.asyncio
    async def test_book_flight_maintains_context(self, agent, mock_response):
        """Test that conversation context is maintained across multiple requests."""
        context_id = str(uuid4())
        user_input_1 = "I want to book a flight"
        user_input_2 = "From Seattle to New York"

        agent.chat_agent.get_response.return_value = mock_response
        await agent.book_flight(user_input_1, context_id)
        await agent.book_flight(user_input_2, context_id)

        # Should have 5 messages: 1 system + 2 user + 2 assistant
        assert len(agent.history_store[context_id].messages) == 5

    @pytest.mark.asyncio
    async def test_book_flight_different_contexts(self, agent, mock_response):
        """Test that different context IDs maintain separate histories."""
        context_id_1 = str(uuid4())
        context_id_2 = str(uuid4())

        agent.chat_agent.get_response.return_value = mock_response
        await agent.book_flight("Book flight from Seattle", context_id_1)
        await agent.book_flight("Book flight from Boston", context_id_2)

        assert context_id_1 in agent.history_store
        assert context_id_2 in agent.history_store
        assert len(agent.history_store[context_id_1].messages) == 3  # System + User + Assistant
        assert len(agent.history_store[context_id_2].messages) == 3  # System + User + Assistant

    @pytest.mark.asyncio
    async def test_book_flight_error_handling(self, agent):
        """Test error handling when agent raises an exception."""
        context_id = str(uuid4())
        user_input = "Book a flight"

        agent.chat_agent.get_response.side_effect = Exception("API Error")
        response = await agent.book_flight(user_input, context_id)

        assert "error" in response.lower()
        assert "API Error" in response

    @pytest.mark.asyncio
    async def test_get_or_create_chat_history_creates_new(self, agent):
        """Test that _get_or_create_chat_history creates a new history."""
        context_id = str(uuid4())

        chat_history = agent._get_or_create_chat_history(context_id)

        assert isinstance(chat_history, ChatHistory)
        assert context_id in agent.history_store
        # Chat history starts with a system message
        assert len(chat_history.messages) == 1
        assert chat_history.messages[0].role.value == "system"

    @pytest.mark.asyncio
    async def test_get_or_create_chat_history_returns_existing(self, agent):
        """Test that _get_or_create_chat_history returns existing history."""
        context_id = str(uuid4())

        # Create initial history
        chat_history_1 = agent._get_or_create_chat_history(context_id)
        chat_history_1.messages.append(
            ChatMessageContent(role="user", content="Test message"))

        # Retrieve the same history
        chat_history_2 = agent._get_or_create_chat_history(context_id)

        assert chat_history_1 is chat_history_2
        # System message + user message
        assert len(chat_history_2.messages) == 2


class TestSemanticKernelFlightBookingAgentExecutor:
    """Test suite for SemanticKernelFlightBookingAgentExecutor."""

    @pytest.fixture
    def executor(self):
        """Create an executor instance for testing."""
        with patch('agent_executor.SemanticKernelFlightBookingAgent'):
            return SemanticKernelFlightBookingAgentExecutor()

    @pytest.fixture
    def mock_context(self):
        """Create a mock RequestContext."""
        context = MagicMock()
        context.get_user_input.return_value = "I want to book a flight"
        context.current_task = None
        context.context_id = str(uuid4())
        
        # Create a proper mock message with required attributes
        mock_message = MagicMock()
        mock_message.role = "user"
        mock_message.task_id = str(uuid4())
        mock_message.context_id = str(uuid4())
        
        # Mock parts with proper structure
        mock_part = MagicMock()
        mock_text_part = MagicMock()
        mock_text_part.text = "I want to book a flight"
        type(mock_part).root = PropertyMock(return_value=mock_text_part)
        mock_message.parts = [mock_part]
        
        context.message = mock_message
        return context

    @pytest.fixture
    def mock_event_queue(self):
        """Create a mock EventQueue."""
        queue = MagicMock()
        queue.enqueue_event = AsyncMock()
        return queue

    @pytest.mark.asyncio
    async def test_executor_initialization(self, executor):
        """Test that the executor initializes correctly."""
        assert executor.agent is not None

    @pytest.mark.asyncio
    async def test_execute_success(self, executor, mock_context, mock_event_queue):
        """Test successful execution of a flight booking request."""
        executor.agent.book_flight = AsyncMock(
            return_value="Flight booking confirmed!")

        with patch('agent_executor.new_task') as mock_new_task:
            mock_task = MagicMock()
            mock_task.id = str(uuid4())
            mock_new_task.return_value = mock_task
            
            await executor.execute(mock_context, mock_event_queue)

        executor.agent.book_flight.assert_called_once_with(
            "I want to book a flight", mock_context.context_id)
        assert mock_event_queue.enqueue_event.call_count >= 1

    @pytest.mark.asyncio
    async def test_execute_with_existing_task(self, executor, mock_context, mock_event_queue):
        """Test execution when a task already exists."""
        mock_context.current_task = MagicMock()
        mock_context.current_task.id = str(uuid4())

        executor.agent.book_flight = AsyncMock(
            return_value="Flight booking confirmed!")

        await executor.execute(mock_context, mock_event_queue)

        executor.agent.book_flight.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_value_error(self, executor, mock_context, mock_event_queue):
        """Test execution when ValueError is raised."""
        executor.agent.book_flight = AsyncMock(
            side_effect=ValueError("Missing departure city"))

        with patch('agent_executor.new_task') as mock_new_task:
            mock_task = MagicMock()
            mock_task.id = str(uuid4())
            mock_new_task.return_value = mock_task
            
            await executor.execute(mock_context, mock_event_queue)

        # Should enqueue error message
        assert mock_event_queue.enqueue_event.call_count >= 1

    @pytest.mark.asyncio
    async def test_execute_unexpected_error(self, executor, mock_context, mock_event_queue):
        """Test execution when unexpected error occurs."""
        executor.agent.book_flight = AsyncMock(
            side_effect=Exception("Unexpected error"))

        with patch('agent_executor.new_task') as mock_new_task:
            mock_task = MagicMock()
            mock_task.id = str(uuid4())
            mock_new_task.return_value = mock_task
            
            await executor.execute(mock_context, mock_event_queue)

        # Should enqueue error message
        assert mock_event_queue.enqueue_event.call_count >= 1

    @pytest.mark.asyncio
    async def test_cancel_not_supported(self, executor, mock_context, mock_event_queue):
        """Test that cancel operation raises an exception."""
        with pytest.raises(Exception, match="Cancel operation not supported"):
            await executor.cancel(mock_context, mock_event_queue)
