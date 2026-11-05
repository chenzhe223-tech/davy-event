def test_mcp_server_module_imports():
    from davy_event.adapters import mcp as adapter_package
    from davy_event.adapters.mcp import server

    assert adapter_package is not None
    assert server.mcp.name == "davy-event"
