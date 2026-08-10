"""Tests for the explicit dependency composition root."""

from injector import Module, provider, singleton

from custom_components.my_verisure.core.dependency_injection.composition_root import (
    CompositionRoot,
    build_my_verisure_composition_root,
)


class _Service:
    """Test dependency."""


class _TestModule(Module):
    @singleton
    @provider
    def provide_service(self) -> _Service:
        return _Service()


def test_composition_root_resolves_dependencies_without_global_state():
    root = CompositionRoot(_TestModule())

    first = root.get(_Service)
    second = root.get(_Service)

    assert first is second


def test_composition_roots_are_isolated():
    first_root = CompositionRoot(_TestModule())
    second_root = CompositionRoot(_TestModule())

    assert first_root.get(_Service) is not second_root.get(_Service)


def test_production_factory_builds_an_isolated_root():
    root = build_my_verisure_composition_root()

    assert isinstance(root, CompositionRoot)
