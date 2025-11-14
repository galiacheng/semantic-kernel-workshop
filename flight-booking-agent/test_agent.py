import pytest
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock
from uuid import uuid4

from agent_framework import ChatAgent, AgentThread, AgentRunResponse

from agent import SemanticKernelFlightBookingAgent
from agent_executor import SemanticKernelFlightBookingAgentExecutor


class TestSemanticKernelFlightBookingAgent:
    """Test suite for SemanticKernelFlightBookingAgent."""

    @pytest.fixture
    def mock_chat_agent(self):
        """Create a mock chat agent."""
        mock_agent = MagicMock(spec=ChatAgent)
        mock_agent.run = AsyncMock()
        mock_agent.get_new_thread = MagicMock()
        return mock_agent

    @pytest.fixture
    def agent(self, mock_chat_agent):
        """Create a flight booking agent instance for testing."""
        mock_client = MagicMock()
        mock_client.create_agent = MagicMock(return_value=mock_chat_agent)
        with patch('agent.AzureOpenAIChatClient', return_value=mock_client):
            with patch('agent.DefaultAzureCredential'):
                return SemanticKernelFlightBookingAgent()

    @pytest.fixture
    def mock_response(self):
        """Create a mock response from the chat agent."""
        mock_resp = MagicMock(spec=AgentRunResponse)
        mock_resp.text = "I'd be happy to help you book a flight. Where would you like to fly from?"
        return mock_resp

    @pytest.mark.asyncio
    async def test_initialization(self, agent):
        """Test that the agent initializes correctly."""
        assert agent.chat_agent is not None
        assert isinstance(agent.thread_store, dict)
        assert len(agent.thread_store) == 0

    @pytest.mark.asyncio
    async def test_book_flight_success(self, agent, mock_response):
        """Test successful flight booking request."""
        context_id = str(uuid4())
        user_input = "I want to book a flight from Seattle to New York"

        # Mock thread creation
        mock_thread = MagicMock(spec=AgentThread)
        agent.chat_agent.get_new_thread.return_value = mock_thread
        agent.chat_agent.run.return_value = mock_response
        
        response = await agent.book_flight(user_input, context_id)

        assert response == mock_response.text
        assert context_id in agent.thread_store

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

        # Mock thread creation
        mock_thread = MagicMock(spec=AgentThread)
        agent.chat_agent.get_new_thread.return_value = mock_thread
        agent.chat_agent.run.return_value = mock_response
        
        await agent.book_flight(user_input_1, context_id)
        await agent.book_flight(user_input_2, context_id)

        # Thread should be reused for same context
        assert context_id in agent.thread_store
        assert agent.chat_agent.run.call_count == 2

    @pytest.mark.asyncio
    async def test_book_flight_different_contexts(self, agent, mock_response):
        """Test that different context IDs maintain separate threads."""
        context_id_1 = str(uuid4())
        context_id_2 = str(uuid4())

        # Mock thread creation
        mock_thread_1 = MagicMock(spec=AgentThread)
        mock_thread_2 = MagicMock(spec=AgentThread)
        agent.chat_agent.get_new_thread.side_effect = [mock_thread_1, mock_thread_2]
        agent.chat_agent.run.return_value = mock_response
        
        await agent.book_flight("Book flight from Seattle", context_id_1)
        await agent.book_flight("Book flight from Boston", context_id_2)

        assert context_id_1 in agent.thread_store
        assert context_id_2 in agent.thread_store
        assert agent.thread_store[context_id_1] is mock_thread_1
        assert agent.thread_store[context_id_2] is mock_thread_2

    @pytest.mark.asyncio
    async def test_book_flight_error_handling(self, agent):
        """Test error handling when agent raises an exception."""
        context_id = str(uuid4())
        user_input = "Book a flight"

        # Mock thread creation
        mock_thread = MagicMock(spec=AgentThread)
        agent.chat_agent.get_new_thread.return_value = mock_thread
        agent.chat_agent.run.side_effect = Exception("API Error")
        
        response = await agent.book_flight(user_input, context_id)

        assert "error" in response.lower()
        assert "API Error" in response

    @pytest.mark.asyncio
    async def test_get_or_create_thread_creates_new(self, agent):
        """Test that _get_or_create_thread creates a new thread."""
        context_id = str(uuid4())

        # Mock thread creation
        mock_thread = MagicMock(spec=AgentThread)
        agent.chat_agent.get_new_thread.return_value = mock_thread
        
        thread = agent._get_or_create_thread(context_id)

        assert isinstance(thread, MagicMock)
        assert context_id in agent.thread_store
        agent.chat_agent.get_new_thread.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_or_create_thread_returns_existing(self, agent):
        """Test that _get_or_create_thread returns existing thread."""
        context_id = str(uuid4())

        # Create initial thread
        mock_thread = MagicMock(spec=AgentThread)
        agent.chat_agent.get_new_thread.return_value = mock_thread
        thread_1 = agent._get_or_create_thread(context_id)

        # Retrieve the same thread
        thread_2 = agent._get_or_create_thread(context_id)

        assert thread_1 is thread_2
        # get_new_thread should only be called once
        agent.chat_agent.get_new_thread.assert_called_once()


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
