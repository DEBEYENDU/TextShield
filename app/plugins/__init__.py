from __future__ import annotations

import importlib
import os
import sys
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, Type

from app.events import Event, EventTypes, get_event_bus


class PluginABC(ABC):
    """Abstract base class for all TextShield plugins."""

    @abstractmethod
    def initialize(self) -> None:
        """Called when the plugin is loaded."""
        pass

    @abstractmethod
    def shutdown(self) -> None:
        """Called when the plugin is unloaded."""
        pass

    @abstractmethod
    def metadata(self) -> Dict[str, Any]:
        """Return plugin metadata (name, version, author, etc.)."""
        pass

    @abstractmethod
    def capabilities(self) -> List[str]:
        """Return list of capabilities this plugin provides."""
        pass

    @abstractmethod
    def health(self) -> Dict[str, Any]:
        """Return plugin health status."""
        pass

    def on_event(self, event: Event) -> None:
        """Called when an event is emitted. Override if needed."""
        pass


class PluginLoader:
    """Loads and manages plugins from a specified directory."""

    def __init__(self, plugin_dir: str = "app/plugins"):
        self.plugin_dir = plugin_dir
        self._loaded_plugins: Dict[str, PluginABC] = {}
        self._plugin_metadata: Dict[str, Dict[str, Any]] = {}
        self._event_bus = get_event_bus()

    def discover_plugins(self) -> List[str]:
        """Discover plugin files in the plugin directory."""
        if not os.path.exists(self.plugin_dir):
            return []

        plugin_files = []
        for filename in os.listdir(self.plugin_dir):
            if filename.endswith(".py") and not filename.startswith("_"):
                plugin_files.append(filename[:-3])  # Remove .py extension

        return plugin_files

    def load_plugin(self, plugin_name: str) -> Optional[PluginABC]:
        """Load a specific plugin by name."""
        if plugin_name in self._loaded_plugins:
            return self._loaded_plugins[plugin_name]

        try:
            # Add plugin dir to sys.path if not already there
            if self.plugin_dir not in sys.path:
                sys.path.insert(0, self.plugin_dir)

            # Import the plugin module
            module = importlib.import_module(plugin_name)

            # Get the PluginABC subclass
            plugin_class = getattr(module, plugin_name.title().replace("_", ""))

            # Instantiate
            plugin_instance = plugin_class()

            # Initialize
            plugin_instance.initialize()

            # Register with event bus
            self._register_plugin_events(plugin_instance)

            # Store
            self._loaded_plugins[plugin_name] = plugin_instance
            self._plugin_metadata[plugin_name] = plugin_instance.metadata()

            return plugin_instance

        except Exception as e:
            print(f"Failed to load plugin {plugin_name}: {e}")
            return None

    def _register_plugin_events(self, plugin: PluginABC) -> None:
        """Register plugin for relevant events."""
        # Subscribe to knowledge_updated events by default
        self._event_bus.subscribe(
            EventTypes.KNOWLEDGE_UPDATED,
            lambda event: plugin.on_event(event),
        )

    def unload_plugin(self, plugin_name: str) -> bool:
        """Unload a plugin."""
        if plugin_name not in self._loaded_plugins:
            return False

        plugin = self._loaded_plugins[plugin_name]
        try:
            plugin.shutdown()
            del self._loaded_plugins[plugin_name]
            del self._plugin_metadata[plugin_name]

            # Unsubscribe from events
            self._event_bus.unsubscribe(
                EventTypes.KNOWLEDGE_UPDATED,
                lambda event: plugin.on_event(event),
            )

            return True
        except Exception:
            return False

    def get_plugin(self, plugin_name: str) -> Optional[PluginABC]:
        """Get a loaded plugin instance."""
        return self._loaded_plugins.get(plugin_name)

    def get_all_plugins(self) -> Dict[str, PluginABC]:
        """Get all loaded plugins."""
        return dict(self._loaded_plugins)

    def get_plugin_metadata(self, plugin_name: str) -> Optional[Dict[str, Any]]:
        """Get plugin metadata."""
        return self._plugin_metadata.get(plugin_name)

    def list_plugins(self) -> List[Dict[str, Any]]:
        """List all loaded plugins with metadata."""
        return [
            {
                "name": name,
                "metadata": metadata,
            }
            for name, metadata in self._plugin_metadata.items()
        ]

    def emit_plugin_event(
        self,
        event_type: str,
        data: Dict[str, Any],
        source: str = "plugin_system",
    ) -> None:
        """Emit an event to all plugins."""
        event = Event(
            event_type=event_type,
            source=source,
            data=data,
        )
        asyncio.get_event_loop().run_until_complete(
            self._event_bus.emit(event)
        )


# Global plugin loader instance
_plugin_loader: Optional[PluginLoader] = None


def get_plugin_loader() -> PluginLoader:
    """Get the global plugin loader instance."""
    global _plugin_loader
    if _plugin_loader is None:
        _plugin_loader = PluginLoader()
    return _plugin_loader


def load_all_plugins() -> Dict[str, any]:
    """Load all discovered plugins."""
    loader = get_plugin_loader()
    plugin_names = loader.discover_plugins()
    results = {}
    for name in plugin_names:
        plugin = loader.load_plugin(name)
        if plugin:
            results[name] = {
                "metadata": loader.get_plugin_metadata(name),
                "plugin": plugin,
            }
    return results