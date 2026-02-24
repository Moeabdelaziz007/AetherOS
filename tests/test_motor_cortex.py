import pytest
from unittest.mock import AsyncMock, Mock, patch
import json
from agent.aether_forge.motor_cortex import AetherMotorCortex
from agent.aether_forge.aether_forge import AetherForge

@pytest.fixture
def mock_forge():
    # Mock AetherForge to avoid async init issues
    mock = Mock(spec=AetherForge)
    return mock

@pytest.mark.asyncio
async def test_dispatch_known_tool(mock_forge):
    cortex = AetherMotorCortex(forge=mock_forge)

    # Mock the internal methods
    cortex._execute_api_request = AsyncMock(return_value={"success": True})
    
    # Re-initialize tools to point to the mock
    cortex.tools["execute_api_request"] = cortex._execute_api_request

    result = await cortex.dispatch("execute_api_request", {"service": "coingecko"})

    assert result == {"success": True}
    cortex._execute_api_request.assert_called_once_with({"service": "coingecko"})

@pytest.mark.asyncio
async def test_dispatch_unknown_tool(mock_forge):
    cortex = AetherMotorCortex(forge=mock_forge)
    result = await cortex.dispatch("unknown_tool", {})
    assert "error" in result
    assert "unknown to the Motor Cortex" in result["error"]

@pytest.mark.asyncio
async def test_execute_api_missing_service(mock_forge):
    cortex = AetherMotorCortex(forge=mock_forge)
    result = await cortex._execute_api_request({})
    assert result == {"error": "Missing 'service' parameter. Use: coingecko, github, weather"}

@pytest.mark.asyncio
async def test_manipulate_dom(mock_forge):
    cortex = AetherMotorCortex(forge=mock_forge)
    result = await cortex._manipulate_dom({"element_id": "btn-1", "action": "click"})
    assert result["success"] is True
    assert result["message"] == "Executed 'click' on element 'btn-1'."

@pytest.mark.asyncio
async def test_generate_ui(mock_forge):
    cortex = AetherMotorCortex(forge=mock_forge)
    # Mock the UI callback
    mock_callback = AsyncMock()
    cortex.set_ui_callback(mock_callback)
    
    args = {
        "type": "crypto",
        "title": "Bitcoin Price",
        "data": {"price": 50000}
    }
    
    result = await cortex.dispatch("generate_ui", args)
    
    assert result["success"] is True
    assert result["component"] == "CryptoCard"
    mock_callback.assert_called_once()
