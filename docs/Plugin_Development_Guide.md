# Plugin Development Guide — TextShield v2.2

## Framework
`app/plugins/` isolated lifecycle: `initialize`, `shutdown`, `metadata`, `capabilities`, `health`.

## Example
```python
# app/plugins/my_plugin.py
class MyPlugin:
    name = "my_plugin"
    version = "1.0.0"
    def initialize(self): ...
    def shutdown(self): ...
    @property
    def metadata(self): return {"name": self.name, "capabilities": ["custom_rule"]}
    def health_check(self): return {"healthy": True}
    async def analyze(self, text: str): return {"score": 0.5}
```

Register via `PluginRegistry.register(MyPlugin())` or `GET /api/v2/plugins`.

## Events
Internal `app/events/` pub/sub: `MessageReceived`, `AnalysisStored`, `WebhookTriggered`. Hook via `event_bus.subscribe("AnalysisStored", my_handler)`.

## Webhooks
`POST /api/v2/webhooks` (event, url, secret, retries, signing). See `docs/v2.1/`.

## Testing
Add `tests/plugins/test_my_plugin.py`; ensure `health_check` + graceful degrade.

See `examples/plugin_example.py`.
