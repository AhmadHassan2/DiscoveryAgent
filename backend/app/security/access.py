"""Permission filtering boundary.

The PoC has no enterprise authentication. Every request runs as a placeholder principal and
`MockPermissionFilter` applies the per-record ACL metadata delivered by the connectors:

* records marked `restricted` are hidden unless the principal is in an allowed group;
* Teams content is only indexed from channels explicitly authorised for indexing
  (`authorized_for_indexing`); private chats are never connected.

In production, replace `Principal` with the SSO identity and implement `PermissionFilter`
using each source system's own permission model (or the search platform's security trimming).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from app.schemas.records import NormalizedRecord


@dataclass(frozen=True)
class Principal:
    id: str
    groups: frozenset[str] = field(default_factory=lambda: frozenset({"all-employees"}))
    is_authenticated: bool = False  # True only once real SSO is integrated


class PermissionFilter(Protocol):
    def filter(self, records: list[NormalizedRecord], principal: Principal) -> tuple[list[NormalizedRecord], int]: ...


class MockPermissionFilter:
    def filter(self, records: list[NormalizedRecord], principal: Principal) -> tuple[list[NormalizedRecord], int]:
        allowed: list[NormalizedRecord] = []
        hidden = 0
        for rec in records:
            acl = rec.acl
            if not acl.authorized_for_indexing:
                hidden += 1
                continue
            if acl.classification == "restricted" or acl.visibility == "restricted":
                if not principal.groups & set(acl.groups):
                    hidden += 1
                    continue
            allowed.append(rec)
        return allowed, hidden


def default_principal(user_id: str) -> Principal:
    return Principal(id=user_id)
