"""Coordinator composition boundary tests."""

import inspect

from custom_components.my_verisure.coordinator import MyVerisureDataUpdateCoordinator


def test_coordinator_accepts_entry_scoped_composition_root():
    """The HA coordinator boundary can receive an already-built graph."""
    parameters = inspect.signature(MyVerisureDataUpdateCoordinator.__init__).parameters

    assert "composition_root" in parameters
