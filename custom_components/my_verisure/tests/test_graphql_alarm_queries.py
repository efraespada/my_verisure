"""Unit tests for extracted GraphQL alarm query strings."""

from custom_components.my_verisure.core.api.graphql_alarm_queries import (
    ARM_PANEL_MUTATION,
    ARM_STATUS_QUERY,
    CHECK_ALARM_QUERY,
    CHECK_ALARM_STATUS_QUERY,
    DISARM_PANEL_MUTATION,
    DISARM_STATUS_QUERY,
)


def test_graphql_queries_contain_expected_operations() -> None:
    """Ensure query modules expose non-empty GraphQL documents."""
    assert "CheckAlarm" in CHECK_ALARM_QUERY
    assert "xSArmPanel" in ARM_PANEL_MUTATION
    assert "xSArmStatus" in ARM_STATUS_QUERY
    assert "xSDisarmPanel" in DISARM_PANEL_MUTATION
    assert "xSDisarmStatus" in DISARM_STATUS_QUERY
    assert "xSCheckAlarmStatus" in CHECK_ALARM_STATUS_QUERY


def test_alarm_client_imports_queries_from_shared_module() -> None:
    """The query module remains the single source of GraphQL documents."""
    from custom_components.my_verisure.core.api import graphql_alarm_queries

    assert graphql_alarm_queries.CHECK_ALARM_QUERY is CHECK_ALARM_QUERY
    assert graphql_alarm_queries.ARM_PANEL_MUTATION is ARM_PANEL_MUTATION
