def test_mcp_server_module_imports():
    from davy_event.adapters.mcp import server

    assert server.mcp is not None
    assert callable(server.discover_events)
    assert callable(server.extract_event)
