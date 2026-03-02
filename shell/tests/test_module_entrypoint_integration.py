"""
Testy integracyjne fallbacku Shell dla URL modułów.

Cel:
- Bezpośrednie wejście na `/modules/<name>/...` ma renderować pełny layout Shell,
  a następnie bootstrapować załadowanie partiala modułu przez HTMX.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient


class TestModuleEntrypoint:
    """Testy integracyjne endpointów fallbacku modułów w Shell."""

    @pytest.mark.asyncio
    async def test_modules_issues_renderuje_pelny_layout_shell(
        self,
        client: AsyncClient,
    ) -> None:
        """GET /modules/issues/ bez HTMX zwraca pełny layout z navbarem i bootstrapem HTMX."""
        response = await client.get("/modules/issues/")

        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")
        assert "id=\"main-content\"" in response.text
        assert "navbar" in response.text
        assert 'hx-get="/modules/issues/"' in response.text

    @pytest.mark.asyncio
    async def test_modules_nested_path_zachowuje_query_string(
        self,
        client: AsyncClient,
    ) -> None:
        """Fallback zachowuje zagnieżdżoną ścieżkę i query string dla bootstrapa HTMX."""
        response = await client.get("/modules/issues/list?status=NOWY")

        assert response.status_code == 200
        assert 'hx-get="/modules/issues/list?status=NOWY"' in response.text

    @pytest.mark.asyncio
    async def test_modules_unknown_zwraca_404(
        self,
        client: AsyncClient,
    ) -> None:
        """Nieobsługiwany moduł powinien zwrócić 404."""
        response = await client.get("/modules/nie-ma-takiego/")

        assert response.status_code == 404
