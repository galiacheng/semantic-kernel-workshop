# Semantic Kernel to Agent Framework Migration Guide (Python)

## Executive Summary

Agent Framework for Python replaces Semantic Kernel with a simplified, unified interface across AI providers. Key improvements include direct client usage (no kernel required), built-in thread management, simplified tool registration, and enhanced memory capabilities.

## Quick Migration Reference

### Core Client Mapping

| **Semantic Kernel** | **Agent Framework** | **Key Improvement** |
|---------------------|-------------------- |-------------------|
| `AzureChatCompletion` + `Kernel` | `AzureChatClient` | Direct client, no kernel |
| `OpenAIChatCompletion` + `Kernel` | `OpenAIChatClient` | Simplified API calls |
| `AzureOpenAIAssistantAgent` | `AzureAssistantsClient` | Built-in lifecycle management |
| `OpenAIAssistantAgent` | `OpenAIAssistantsClient` | Native file/tool support |
| `AzureAIAgent` | `FoundryChatClient` | Azure AI Studio integration |
| Not available | `AzureResponsesClient` / `OpenAIResponsesClient` | Memory-enhanced conversations |

### Available Clients by Category

#### Chat Clients (Basic Conversations)
- `AzureChatClient` - Azure OpenAI Chat Completion
- `OpenAIChatClient` - OpenAI Chat Completion  
- `FoundryChatClient` - Azure AI Studio integration

#### Assistant Clients (Advanced Features)
- `AzureAssistantsClient` - Azure OpenAI Assistants with file/code capabilities
- `OpenAIAssistantsClient` - OpenAI Assistants with full toolset

#### Memory-Enhanced Clients (Next Generation)
- `AzureResponsesClient` - Azure + conversation memory
- `OpenAIResponsesClient` - OpenAI + conversation memory

#### Custom Implementation
- `BaseChatClient` - Foundation for custom AI integrations
- `ChatAgent` - Universal agent wrapper for any client

## Architectural Changes Overview

### 1. Import Simplification

**Before (Semantic Kernel):**
```python
from semantic_kernel import Kernel
from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.connectors.ai.azure_chat_completion import AzureChatCompletion
```

**After (Agent Framework):**
```python
from agent_framework import ChatAgent
from agent_framework.azure import AzureChatClient
from agent_framework.foundry import FoundryChatClient
```

### 2. Agent Creation Evolution

**Before (Complex Kernel Pattern):**
```python
# Multi-step setup with kernel dependency
kernel = Kernel()
kernel.add_service(AzureChatCompletion(...))
agent = ChatCompletionAgent(
    kernel=kernel,
    instructions="You are a helpful assistant"
)
```

**After (Direct Client Pattern):**
```python
# Method 1: Direct agent creation
agent = ChatAgent(
    chat_client=AzureChatClient(credential=AzureCliCredential()),
    instructions="You are a helpful assistant",
    tools=[weather_function]
)

# Method 2: Client factory (recommended)
agent = AzureChatClient(credential=AzureCliCredential()).create_agent(
    instructions="You are a helpful assistant",
    tools=[weather_function]
)

# Method 3: Azure AI Studio (with async context)
async with (
    AzureCliCredential() as credential,
    FoundryChatClient(async_credential=credential).create_agent(
        instructions="You are a helpful assistant"
    ) as agent,
):
    response = await agent.run("Hello!")
```

### 3. Thread Management Revolution

**Before (Manual Management):**
```python
# Complex thread handling per provider
thread_id = "thread_123"
conversation_history = []
# Manual state management required
```

**After (Automatic Management):**
```python
# Automatic thread creation
response = await agent.run("Hello!")

# Explicit threads for conversation persistence  
thread = agent.get_new_thread()
response1 = await agent.run("Hello!", thread=thread)
response2 = await agent.run("What did I say?", thread=thread)  # Remembers context

# Restore from existing messages
thread = AgentThread(message_store=ChatMessageList(previous_messages))
response = await agent.run("Continue our chat", thread=thread)
```

### 4. Tool Registration Simplification

**Before (Plugin System):**
```python
from semantic_kernel.functions import kernel_function

class WeatherPlugin:
    @kernel_function(description="Get weather for location")
    def get_weather(self, location: str) -> str:
        return f"Weather in {location}: sunny"

kernel.add_plugin(WeatherPlugin(), "weather")
```

**After (Direct Functions):**
```python
from typing import Annotated
from pydantic import Field

def get_weather(
    location: Annotated[str, Field(description="Location to get weather for")]
) -> str:
    """Get weather for a given location."""
    return f"Weather in {location}: sunny"

# Direct registration - no decorators needed
agent = ChatAgent(chat_client=client, tools=[get_weather])
```

### 5. API Method Changes

**Before (Complex Invocation):**
```python
# Multiple methods with complex handling
async for response in agent.invoke_async(user_input, thread):
    print(response.content)

async for chunk in agent.invoke_streaming_async(user_input, thread):
    print(chunk.content, end="")
```

**After (Unified API):**
```python
# Single run method for all interactions
response = await agent.run("Hello!")
print(response.text)  # Direct access
print(response)       # Also works - has __str__

# Simple streaming
async for update in agent.run_stream("Hello!"):
    if update.text:
        print(update.text, end="")
```

## Client Implementation Patterns

### Azure Clients

#### AzureChatClient (Standard Azure OpenAI)
```python
from agent_framework.azure import AzureChatClient
from azure.identity import AzureCliCredential

# Basic setup
client = AzureChatClient(
    endpoint="https://your-resource.openai.azure.com/",
    credential=AzureCliCredential(),
    deployment_name="gpt-4o"
)

agent = client.create_agent(
    instructions="You are a helpful assistant",
    temperature=0.7
)
```

#### FoundryChatClient (Azure AI Studio - Recommended)
```python
from agent_framework.foundry import FoundryChatClient
from azure.identity.aio import AzureCliCredential

async def main():
    async with (
        AzureCliCredential() as credential,
        FoundryChatClient(async_credential=credential).create_agent(
            name="Assistant",
            instructions="You are a helpful assistant"
        ) as agent,
    ):
        response = await agent.run("Hello!")
        print(response)
```

#### AzureAssistantsClient (File Processing & Code Execution)
```python
from agent_framework.azure import AzureAssistantsClient

async with AzureAssistantsClient(
    endpoint="https://your-resource.openai.azure.com/",
    credential=AzureCliCredential()
).create_agent(
    instructions="You are a coding assistant",
    tools=[{"type": "code_interpreter"}, {"type": "file_search"}]
) as agent:
    response = await agent.run(
        "Analyze this data file",
        attachments=["data.csv"]
    )
```

### OpenAI Clients

#### OpenAIChatClient (Direct OpenAI)
```python
from agent_framework.openai import OpenAIChatClient

# Using environment variable OPENAI_API_KEY
agent = OpenAIChatClient().create_agent(
    instructions="You are a creative assistant",
    model="gpt-4o",
    temperature=0.9
)

response = await agent.run("Write a haiku about coding")
```

#### OpenAIResponsesClient (Memory-Enhanced)
```python
from agent_framework.openai import OpenAIResponsesClient

client = OpenAIResponsesClient()
agent = client.create_agent(
    instructions="You are a personal assistant with perfect memory",
    memory_enabled=True
)

# Memory persists across conversations
await agent.run("My name is Alice and I love hiking")
response = await agent.run("What outdoor activities do I enjoy?")
# Responds: "You enjoy hiking!"
```

## Environment Configuration

### Required Environment Variables

**Azure OpenAI:**
- `AZUREOPENAI_ENDPOINT` - Your Azure OpenAI endpoint
- `AZUREOPENAI_DEPLOYMENT_NAME` - Model deployment (optional, defaults to gpt-4o)

**OpenAI:**
- `OPENAI_API_KEY` - Your OpenAI API key

**Azure AI Studio:**
- Azure CLI login required: `az login`
- No additional environment variables needed for FoundryChatClient

### Authentication Setup

```python
# Azure CLI authentication (most common)
from azure.identity import AzureCliCredential
credential = AzureCliCredential()

# For Foundry (requires async)
from azure.identity.aio import AzureCliCredential
async with AzureCliCredential() as credential:
    # Use with FoundryChatClient
```

## Advanced Features

### Streaming Responses
```python
async def stream_example():
    print("Agent: ", end="", flush=True)
    async for chunk in agent.run_stream("Explain quantum computing"):
        if chunk.text:
            print(chunk.text, end="", flush=True)
    print()  # New line
```

### Rich Type Annotations for Tools
```python
from typing import Annotated, Literal
from pydantic import Field

def advanced_tool(
    location: Annotated[str, Field(description="City or address")],
    unit: Annotated[Literal["celsius", "fahrenheit"], Field(description="Temperature unit")] = "celsius",
    forecast: Annotated[bool, Field(description="Include 5-day forecast")] = False
) -> str:
    """Get weather with optional forecast."""
    return f"Weather in {location}: 22°{unit[0].upper()}"

agent = ChatAgent(chat_client=client, tools=[advanced_tool])
```

### Conversation Persistence
```python
async def persistent_conversation():
    thread = agent.get_new_thread()
    
    # Multi-turn conversation
    await agent.run("My name is Alice", thread=thread)
    await agent.run("I live in Seattle", thread=thread)
    
    # Save conversation state
    messages = await thread.message_store.list_messages()
    # Store messages to database/file
    
    # Later, restore conversation
    restored_thread = AgentThread(message_store=ChatMessageList(messages))
    response = await agent.run("What's my name?", thread=restored_thread)
    # Response: "Your name is Alice"
```

## Client Selection Guide

| **Use Case** | **Recommended Client** | **Why** |
|-------------|------------------------|---------|
| **Azure AI Studio Projects** | `FoundryChatClient` | Native integration, managed services |
| **Enterprise Azure** | `AzureChatClient` | Security, compliance, direct API |
| **File Analysis/Code** | `AzureAssistantsClient` / `OpenAIAssistantsClient` | Built-in file processing |
| **Long Conversations** | `AzureResponsesClient` / `OpenAIResponsesClient` | Memory capabilities |
| **Cost Optimization** | `OpenAIChatClient` | Direct pricing |
| **Latest Features** | `OpenAIChatClient` / `OpenAIAssistantsClient` / `OpenAIResponsesClient` | First access to new capabilities |
| **Custom Integration** | `BaseChatClient` | Full customization |

## Common Migration Issues

### Authentication Errors
```python
# Error: 401 Unauthorized
# Solution: Ensure Azure CLI login
# Terminal: az login

# For sync Azure services
from azure.identity import AzureCliCredential
credential = AzureCliCredential()

# For async services (Foundry)
from azure.identity.aio import AzureCliCredential
async with AzureCliCredential() as credential:
    # Use with async clients
```

### Import Errors
```python
# OLD (incorrect)
from agent_framework import ChatClientAgent

# NEW (correct)  
from agent_framework import ChatAgent
```

### Async Context Issues
```python
# Always wrap async operations
import asyncio

async def main():
    response = await agent.run("Hello")
    return response

if __name__ == "__main__":
    result = asyncio.run(main())
```

## Best Practices

### 1. Resource Management
```python
# Use async context managers for automatic cleanup
async with (
    AzureCliCredential() as credential,
    FoundryChatClient(async_credential=credential).create_agent(...) as agent,
):
    # Agent automatically cleaned up after use
    response = await agent.run("Hello")
```

### 2. Tool Design
```python
# Keep tools simple and fast
def efficient_tool(x: int, y: int) -> int:
    """Fast calculation."""
    return x * y

# For I/O operations, use async
async def async_tool(query: str) -> str:
    """Database lookup."""
    result = await database.fetch(query)
    return str(result)
```

### 3. Error Handling
```python
from agent_framework.exceptions import AuthenticationException, ServiceException

async def robust_interaction():
    try:
        response = await agent.run("Hello")
        return response.text
    except AuthenticationException:
        return "Authentication failed - check login"
    except ServiceException as e:
        return f"Service error: {e}"
    except Exception as e:
        return f"Unexpected error: {e}"
```

### 4. Configuration Management
```python
from dataclasses import dataclass

@dataclass
class AgentConfig:
    instructions: str
    temperature: float = 0.7
    max_tokens: int = 1000

config = AgentConfig(
    instructions="You are a helpful assistant",
    temperature=0.8
)

agent = AzureChatClient(credential=credential).create_agent(
    instructions=config.instructions,
    temperature=config.temperature,
    max_tokens=config.max_tokens
)
```

## Complete Migration Example

**Before (Semantic Kernel):**
```python
import os
from azure.identity import AzureCliCredential
from semantic_kernel import Kernel
from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.connectors.ai.azure_chat_completion import AzureChatCompletion

async def old_pattern():
    # Complex setup with environment variables
    endpoint = os.environ["AZURE_AI_AGENT_ENDPOINT"]
    deployment = os.environ["AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME"]
    
    kernel = Kernel()
    kernel.add_service(AzureChatCompletion(
        endpoint=endpoint,
        deployment_name=deployment,
        azure_ad_token_provider=AzureCliCredential().get_token
    ))
    
    agent = ChatCompletionAgent(
        kernel=kernel,
        name="Assistant",
        instructions="Answer questions helpfully"
    )
    
    # Manual thread management
    thread = agent.get_new_thread()
    
    for question in ["Hello", "What's the weather?"]:
        response = await agent.run(question, thread)
        print(f"Assistant: {response.text}")
```

**After (Agent Framework):**
```python
from azure.identity.aio import AzureCliCredential
from agent_framework.foundry import FoundryChatClient

async def new_pattern():
    # Simple setup, no environment variables needed
    async with (
        AzureCliCredential() as credential,
        FoundryChatClient(async_credential=credential).create_agent(
            name="Assistant",
            instructions="Answer questions helpfully"
        ) as agent,
    ):
        # Automatic thread management
        for question in ["Hello", "What's the weather?"]:
            response = await agent.run(question)
            print(f"Assistant: {response}")
```

This migration demonstrates the core improvements: simplified imports, no kernel dependency, automatic resource management, built-in thread handling, and cleaner async patterns.