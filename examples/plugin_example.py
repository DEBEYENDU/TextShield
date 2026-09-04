"""Plugin example — custom rule plugin"""
class MyPlugin:
    name = "my_plugin"
    version = "1.0.0"
    def initialize(self): print("MyPlugin init")
    def shutdown(self): print("MyPlugin shutdown")
    @property
    def metadata(self): return {"name": self.name, "capabilities": ["custom_rule"]}
    def health_check(self): return {"healthy": True}
    async def analyze(self, text: str):
        return {"score": 0.9 if "prize" in text.lower() else 0.1}

# register
# from app.plugins.registry import PluginRegistry
# PluginRegistry().register(MyPlugin())
