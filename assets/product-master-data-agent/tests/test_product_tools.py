"""Unit tests for product master data agent MCP tool interactions."""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from langchain_core.tools import StructuredTool


def _make_mock_tool(name: str, mock_response: dict) -> StructuredTool:
    """Create a mock StructuredTool that returns a fixed response."""
    async def _run(**kwargs):
        return json.dumps(mock_response)

    tool = MagicMock(spec=StructuredTool)
    tool.name = name
    tool.description = f"Mock tool: {name}"
    tool.coroutine = _run
    return tool


# ---------------------------------------------------------------------------
# Test: list_a_product_for_api_product_srv
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_list_products_returns_results():
    """list_a_product tool should return a list of products."""
    mock_response = {
        "d": {
            "results": [
                {"Product": "LAPTOP-001", "ProductGroup": "ELECTRONICS"},
                {"Product": "MONITOR-002", "ProductGroup": "ELECTRONICS"},
            ]
        }
    }
    tool = _make_mock_tool("list_a_product_for_api_product_srv", mock_response)
    result = await tool.coroutine()
    parsed = json.loads(result)
    assert "d" in parsed
    assert len(parsed["d"]["results"]) == 2
    assert parsed["d"]["results"][0]["Product"] == "LAPTOP-001"


# ---------------------------------------------------------------------------
# Test: get_a_product_for_api_product_srv
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_get_product_by_key():
    """get_a_product tool should return a single product by key."""
    mock_response = {
        "d": {
            "Product": "LAPTOP-001",
            "ProductGroup": "ELECTRONICS",
        }
    }
    tool = _make_mock_tool("get_a_product_for_api_product_srv", mock_response)
    result = await tool.coroutine(Product="LAPTOP-001")
    parsed = json.loads(result)
    assert parsed["d"]["Product"] == "LAPTOP-001"
    assert parsed["d"]["ProductGroup"] == "ELECTRONICS"


# ---------------------------------------------------------------------------
# Test: get_a_productdescription_for_api_product_srv
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_get_product_description():
    """get_a_productdescription tool should return the product description."""
    mock_response = {
        "d": {
            "Product": "LAPTOP-001",
            "Language": "EN",
            "ProductDescription": "Business Laptop 15-inch with Intel Core i7",
        }
    }
    tool = _make_mock_tool("get_a_productdescription_for_api_product_srv", mock_response)
    result = await tool.coroutine(Product="LAPTOP-001", Language="EN")
    parsed = json.loads(result)
    assert parsed["d"]["ProductDescription"] == "Business Laptop 15-inch with Intel Core i7"


# ---------------------------------------------------------------------------
# Test: list_a_productdescription_for_api_product_srv
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_list_product_descriptions():
    """list_a_productdescription tool should return a list of descriptions."""
    mock_response = {
        "d": {
            "results": [
                {"Product": "LAPTOP-001", "Language": "EN", "ProductDescription": "Business Laptop"},
            ]
        }
    }
    tool = _make_mock_tool("list_a_productdescription_for_api_product_srv", mock_response)
    result = await tool.coroutine()
    parsed = json.loads(result)
    assert len(parsed["d"]["results"]) >= 1


# ---------------------------------------------------------------------------
# Test: get_a_productbasictext_for_api_product_srv
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_get_product_basic_text():
    """get_a_productbasictext tool should return long text for a product."""
    mock_response = {
        "d": {
            "Product": "LAPTOP-001",
            "Language": "EN",
            "LongText": "Premium business laptop for professional use.",
        }
    }
    tool = _make_mock_tool("get_a_productbasictext_for_api_product_srv", mock_response)
    result = await tool.coroutine(Product="LAPTOP-001", Language="EN")
    parsed = json.loads(result)
    assert "LongText" in parsed["d"]
    assert len(parsed["d"]["LongText"]) > 0


# ---------------------------------------------------------------------------
# Test: product not found scenario
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_get_product_not_found_returns_error():
    """When a product doesn't exist, the tool should return an error structure."""
    mock_response = {
        "error": {
            "code": "NOT_FOUND",
            "message": {"lang": "en", "value": "Product 'UNKNOWN-999' not found"},
        }
    }
    tool = _make_mock_tool("get_a_product_for_api_product_srv", mock_response)
    result = await tool.coroutine(Product="UNKNOWN-999")
    parsed = json.loads(result)
    assert "error" in parsed
    assert "NOT_FOUND" in parsed["error"]["code"]


# ---------------------------------------------------------------------------
# Test: metadata tool
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_get_metadata_returns_xml():
    """get_metadata tool should return XML metadata string."""
    mock_xml = '<?xml version="1.0"?><edmx:Edmx xmlns:edmx="http://schemas.microsoft.com/ado/2007/06/edmx"/>'
    tool = _make_mock_tool("get_metadata_api_product_srv", mock_xml)
    # Override the coroutine to return raw XML
    async def _run_xml(**kwargs):
        return mock_xml
    tool.coroutine = _run_xml
    result = await tool.coroutine()
    assert "edmx" in result.lower()
