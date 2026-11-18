"""Stage 3-4: search all enabled connectors concurrently, with isolation of failures."""
from __future__ import annotations

import asyncio
import time
from collections.abc import Callable

from app.config import get_settings
from app.connectors.base import ConnectorUnavailableError, SourceConnector
from app.schemas.records import ConnectorResult, ConnectorSearchRequest, ConnectorStatus, SourceSystem
from app.security.access import MockPermissionFilter, PermissionFilter, Principal

# Deterministic per-source simulated latency multipliers (mock connectors only).
_LATENCY_FACTOR = {"confluence": 1.0, "jira": 0.8, "github": 1.2, "sharepoint": 1.4, "teams": 0.9, "servicenow": 1.1, "idea_registry": 0.2}


async def search_connector(
    connector: SourceConnector,
    request: ConnectorSearchRequest,
    principal: Principal,
    permission_filter: PermissionFilter,
    forced_failures: set[str],
    on_start: Callable[[SourceSystem], None],
    on_done: Callable[[ConnectorResult], None],
) -> ConnectorResult:
    settings = get_settings()
    on_start(connector.source)
    started = time.perf_counter()
    try:
        if connector.mode == "mock" and settings.mock_connector_latency_ms > 0:
            await asyncio.sleep(settings.mock_connector_latency_ms * _LATENCY_FACTOR.get(connector.source.value, 1.0) / 1000)
        if connector.source.value in forced_failures:
            raise ConnectorUnavailableError(f"{connector.display_name} is unavailable (simulated outage)")
        records = await asyncio.wait_for(asyncio.to_thread(connector.search, request), timeout=settings.connector_timeout_seconds)
        allowed, hidden = permission_filter.filter(records, principal)
        result = ConnectorResult(source=connector.source, status=ConnectorStatus.ok, records=allowed,
                                 duration_ms=int((time.perf_counter() - started) * 1000), filtered_by_permissions=hidden, mode=connector.mode)
    except asyncio.TimeoutError:
        result = ConnectorResult(source=connector.source, status=ConnectorStatus.timeout, duration_ms=int((time.perf_counter() - started) * 1000),
                                 error=f"{connector.display_name} did not respond within {settings.connector_timeout_seconds:.0f}s", mode=connector.mode)
    except Exception as exc:  # connector isolation: one failure never fails the search
        result = ConnectorResult(source=connector.source, status=ConnectorStatus.error, duration_ms=int((time.perf_counter() - started) * 1000),
                                 error=str(exc), mode=connector.mode)
    on_done(result)
    return result


async def search_all(
    connectors: list[SourceConnector],
    request: ConnectorSearchRequest,
    principal: Principal,
    forced_failures: set[str],
    on_start: Callable[[SourceSystem], None],
    on_done: Callable[[ConnectorResult], None],
    permission_filter: PermissionFilter | None = None,
) -> list[ConnectorResult]:
    pf = permission_filter or MockPermissionFilter()
    failures = forced_failures | get_settings().failed_source_set
    return list(await asyncio.gather(*(search_connector(c, request, principal, pf, failures, on_start, on_done) for c in connectors)))
