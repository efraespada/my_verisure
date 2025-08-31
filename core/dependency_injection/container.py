"""Dependency injection container for My Verisure integration."""

from typing import Type, TypeVar, Callable, Any, Dict, Optional

T = TypeVar("T")


class DependencyContainer:
    """Simple dependency injection container (similar to Koin)."""

    def __init__(self):
        """Initialize the container."""
        self._providers: Dict[Type, Callable[[], Any]] = {}
        self._singletons: Dict[Type, Any] = {}

    def register(
        self, interface: Type[T], implementation: Callable[[], T]
    ) -> None:
        """Register a dependency provider."""
        self._providers[interface] = implementation

    def register_singleton(
        self, interface: Type[T], implementation: Callable[[], T]
    ) -> None:
        """Register a singleton dependency provider."""

        def singleton_provider():
            if interface not in self._singletons:
                self._singletons[interface] = implementation()
            return self._singletons[interface]

        self._providers[interface] = singleton_provider

    def resolve(self, interface: Type[T]) -> T:
        """Resolve a dependency."""
        if interface not in self._providers:
            raise KeyError(f"No provider registered for {interface}")

        return self._providers[interface]()

    def get(self, interface: Type[T]) -> Optional[T]:
        """Get a dependency if available, None otherwise."""
        try:
            return self.resolve(interface)
        except KeyError:
            return None

    def clear(self) -> None:
        """Clear all registered dependencies and singletons."""
        self._providers.clear()
        self._singletons.clear()


# Global container instance
_container = DependencyContainer()


def get_container() -> DependencyContainer:
    """Get the global dependency container."""
    return _container


def register(interface: Type[T], implementation: Callable[[], T]) -> None:
    """Register a dependency in the global container."""
    _container.register(interface, implementation)


def register_singleton(
    interface: Type[T], implementation: Callable[[], T]
) -> None:
    """Register a singleton dependency in the global container."""
    _container.register_singleton(interface, implementation)


def resolve(interface: Type[T]) -> T:
    """Resolve a dependency from the global container."""
    return _container.resolve(interface)


def get(interface: Type[T]) -> Optional[T]:
    """Get a dependency from the global container if available."""
    return _container.get(interface)
