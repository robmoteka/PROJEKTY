"""
Testy jednostkowe — mapowanie ról z claims JWT.

Scenariusze testowe:
- extract_user_info() z custom claim `roles` → zwraca role
- extract_user_info() z fallback `realm_access.roles` → zwraca role
- extract_user_info() bez ról → zwraca pustą listę
- require_role() z użytkownikiem posiadającym rolę → przepuszcza
- require_role() z użytkownikiem bez roli → HTTP 403
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from auth.jwt_utils import extract_user_info
from dependencies import require_role


# --------------------------------------------------------------------------- #
#  Testy extract_user_info() — mapowanie ról
# --------------------------------------------------------------------------- #


class TestExtractUserInfoRoles:
    """Testy ekstrakcji ról z claims ID tokenu."""

    def test_roles_z_custom_claim(self) -> None:
        """extract_user_info() odczytuje role z custom claim 'roles' (realm-roles-mapper)."""
        # Keycloak z protocol mapperem ustawiającym claim 'roles'
        claims: dict[str, Any] = {
            "sub": "user-123",
            "email": "dev@example.com",
            "name": "Dev User",
            "preferred_username": "devuser",
            "roles": ["developer", "viewer"],
        }
        result = extract_user_info(claims)
        assert result["roles"] == ["developer", "viewer"]

    def test_roles_z_realm_access_fallback(self) -> None:
        """extract_user_info() używa realm_access.roles gdy brak custom claim 'roles'."""
        # Keycloak bez custom mappera — standardowy format
        claims: dict[str, Any] = {
            "sub": "user-456",
            "email": "admin@example.com",
            "name": "Admin User",
            "preferred_username": "adminuser",
            "realm_access": {
                "roles": ["admin", "developer", "offline_access", "uma_authorization"]
            },
        }
        result = extract_user_info(claims)
        # Powinno zwrócić role z realm_access (bez filtrowania systemowych ról Keycloak)
        assert "admin" in result["roles"]
        assert "developer" in result["roles"]

    def test_pusta_lista_gdy_brak_rol(self) -> None:
        """extract_user_info() zwraca pustą listę ról gdy claims nie zawierają ról."""
        claims: dict[str, Any] = {
            "sub": "user-789",
            "email": "guest@example.com",
            "name": "Guest User",
            "preferred_username": "guest",
        }
        result = extract_user_info(claims)
        assert result["roles"] == []

    def test_custom_claim_ma_pierwszenstwo_przed_realm_access(self) -> None:
        """Custom claim 'roles' ma pierwszeństwo przed realm_access.roles."""
        claims: dict[str, Any] = {
            "sub": "user-101",
            "email": "test@example.com",
            "roles": ["viewer"],
            "realm_access": {"roles": ["admin"]},  # Powinno być zignorowane
        }
        result = extract_user_info(claims)
        # Custom claim ma wyższy priorytet
        assert result["roles"] == ["viewer"]
        assert "admin" not in result["roles"]

    def test_pusta_lista_roles_uzywa_fallback(self) -> None:
        """Gdy custom claim 'roles' jest pustą listą, używa realm_access.roles."""
        claims: dict[str, Any] = {
            "sub": "user-102",
            "email": "test@example.com",
            "roles": [],  # Pusty custom claim → fallback
            "realm_access": {"roles": ["developer"]},
        }
        result = extract_user_info(claims)
        assert result["roles"] == ["developer"]

    def test_zwraca_wszystkie_pola_uzytkownika(self) -> None:
        """extract_user_info() zwraca kompletny słownik z wszystkimi polami."""
        claims: dict[str, Any] = {
            "sub": "user-123",
            "email": "jan@example.com",
            "name": "Jan Kowalski",
            "preferred_username": "jkowalski",
            "roles": ["developer"],
        }
        result = extract_user_info(claims)
        # Weryfikacja wszystkich pól
        assert result["sub"] == "user-123"
        assert result["email"] == "jan@example.com"
        assert result["name"] == "Jan Kowalski"
        assert result["preferred_username"] == "jkowalski"
        assert result["roles"] == ["developer"]

    def test_brakujace_pola_zwracaja_defaulty(self) -> None:
        """extract_user_info() zwraca puste stringi/listy gdy brak pól w claims."""
        result = extract_user_info({})
        assert result["sub"] == ""
        assert result["email"] == ""
        assert result["name"] == ""
        assert result["preferred_username"] == ""
        assert result["roles"] == []


# --------------------------------------------------------------------------- #
#  Testy require_role() — kontrola dostępu
# --------------------------------------------------------------------------- #


class TestRequireRole:
    """Testy dependency require_role() — ochrona endpointów na podstawie ról."""

    @pytest.mark.asyncio
    async def test_uzytkownik_z_rola_dostaje_dostep(self) -> None:
        """require_role() przepuszcza użytkownika posiadającego wymaganą rolę."""
        # Użytkownik z rolą admin
        user_with_admin: dict[str, Any] = {
            "sub": "user-1",
            "email": "admin@example.com",
            "roles": ["admin", "developer"],
        }
        # Tworzymy dependency i wywołujemy z mockowanym użytkownikiem
        check = require_role("admin")
        result = await check(user=user_with_admin)
        # Użytkownik powinien być przepuszczony bez wyjątku
        assert result == user_with_admin

    @pytest.mark.asyncio
    async def test_uzytkownik_bez_roli_dostaje_403(self) -> None:
        """require_role() rzuca HTTPException 403 gdy użytkownik nie ma wymaganej roli."""
        # Użytkownik bez roli admin
        user_without_admin: dict[str, Any] = {
            "sub": "user-2",
            "email": "dev@example.com",
            "roles": ["developer"],
        }
        check = require_role("admin")
        with pytest.raises(HTTPException) as exc_info:
            await check(user=user_without_admin)
        # Sprawdzamy kod statusu i treść błędu
        assert exc_info.value.status_code == 403
        assert "admin" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_uzytkownik_z_pusta_lista_rol_dostaje_403(self) -> None:
        """require_role() blokuje użytkownika z pustą listą ról."""
        user_no_roles: dict[str, Any] = {
            "sub": "user-3",
            "email": "guest@example.com",
            "roles": [],
        }
        check = require_role("viewer")
        with pytest.raises(HTTPException) as exc_info:
            await check(user=user_no_roles)
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_uzytkownik_bez_pola_roles_dostaje_403(self) -> None:
        """require_role() blokuje gdy słownik użytkownika nie zawiera klucza 'roles'."""
        user_legacy: dict[str, Any] = {
            "sub": "user-4",
            "email": "legacy@example.com",
            # Brak klucza 'roles'
        }
        check = require_role("developer")
        with pytest.raises(HTTPException) as exc_info:
            await check(user=user_legacy)
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_rozne_role_sa_niezalezne(self) -> None:
        """require_role() sprawdza tylko konkretną rolę — inne nie dają dostępu."""
        user: dict[str, Any] = {"sub": "u1", "roles": ["viewer"]}
        # Viewer ma dostęp do endpointu viewer
        check_viewer = require_role("viewer")
        result = await check_viewer(user=user)
        assert result == user
        # Viewer nie ma dostępu do endpointu developer
        check_developer = require_role("developer")
        with pytest.raises(HTTPException) as exc_info:
            await check_developer(user=user)
        assert exc_info.value.status_code == 403
