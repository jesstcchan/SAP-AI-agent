"""Integration test: end-to-end agent flow with mocked LLM and MCP tools."""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from langchain_core.messages import AIMessage
from langchain_core.tools import StructuredTool


def _make_structured_tool(name: str, response: str) -> StructuredTool:
    """Build a minimal StructuredTool that returns a fixed JSON string."""
    from pydantic import BaseModel, Field

    class NoArgs(BaseModel):
        pass

    async def _run(**kwargs):
        return response

    return StructuredTool(
        name=name,
        description=f"Mock MCP tool: {name}",
        args_schema=NoArgs,
        coroutine=_run,
        handle_tool_error=True,
    )


@pytest.mark.asyncio
async def test_agent_invoke_product_query():
    """Integration: agent returns a product description given a natural language query."""
    # Arrange — mock LLM response
    mock_llm_response = AIMessage(
        content="The product LAPTOP-001 is a Business Laptop 15-inch with Intel Core i7 processor, 16GB RAM, 512GB SSD. It belongs to the ELECTRONICS category."
    )
    mock_tools = [
        _make_structured_tool(
            "get_a_productdescription_for_api_product_srv",
            json.dumps({
                "d": {
                    "Product": "LAPTOP-001",
                    "Language": "EN",
                    "ProductDescription": "Business Laptop 15-inch with Intel Core i7 processor, 16GB RAM, 512GB SSD",
                }
            }),
        )
    ]

    # Patch create_agent to return a graph that returns our mock response
    mock_graph = MagicMock()
    mock_graph.ainvoke = AsyncMock(
        return_value={"messages": [mock_llm_response]}
    )

    with patch("agent.create_agent", return_value=mock_graph), \
         patch("agent.create_checkpointer", return_value=MagicMock()), \
         patch("agent.ChatLiteLLM", return_value=MagicMock()), \
         patch("agent.SummarizationMiddleware", return_value=MagicMock()):

        from agent import SampleAgent
        agent = SampleAgent()
        result = await agent.invoke(
            query="What is the description of LAPTOP-001?",
            context_id="test-context-001",
            tools=mock_tools,
        )

    assert result.status == "completed"
    assert len(result.message) > 0


@pytest.mark.asyncio
async def test_agent_handles_no_tools_gracefully():
    """Integration: agent responds gracefully when no MCP tools are available."""
    mock_llm_response = AIMessage(
        content="Tools are temporarily unavailable. Please try again later."
    )
    mock_graph = MagicMock()
    mock_graph.ainvoke = AsyncMock(
        return_value={"messages": [mock_llm_response]}
    )

    with patch("agent.create_agent", return_value=mock_graph), \
         patch("agent.create_checkpointer", return_value=MagicMock()), \
         patch("agent.ChatLiteLLM", return_value=MagicMock()), \
         patch("agent.SummarizationMiddleware", return_value=MagicMock()):

        from agent import SampleAgent
        agent = SampleAgent()
        result = await agent.invoke(
            query="What is product X?",
            context_id="test-context-002",
            tools=[],
        )

    assert result.status == "completed"
    assert result.message is not None


@pytest.mark.asyncio
async def test_agent_milestone_logging(caplog):
    """Integration: milestone M1 and M2 log statements are emitted."""
    import logging
    mock_llm_response = AIMessage(content="Product LAPTOP-001: Business Laptop.")
    mock_graph = MagicMock()
    mock_graph.ainvoke = AsyncMock(
        return_value={"messages": [mock_llm_response]}
    )
    mock_tool = _make_structured_tool(
        "get_a_product_for_api_product_srv",
        json.dumps({"d": {"Product": "LAPTOP-001", "ProductGroup": "ELECTRONICS"}}),
    )

    with patch("agent.create_agent", return_value=mock_graph), \
         patch("agent.create_checkpointer", return_value=MagicMock()), \
         patch("agent.ChatLiteLLM", return_value=MagicMock()), \
         patch("agent.SummarizationMiddleware", return_value=MagicMock()):

        with caplog.at_level(logging.INFO, logger="agent"):
            from agent import SampleAgent
            agent = SampleAgent()
            result = await agent.invoke(
                query="Tell me about LAPTOP-001",
                context_id="test-context-003",
                tools=[mock_tool],
            )

    assert result.status == "completed"
    log_text = caplog.text
    assert "M1.achieved" in log_text
    assert "M2.achieved" in log_text
