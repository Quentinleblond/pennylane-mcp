"""PennyLane API client — wraps https://app.pennylane.com/api/external/v2/"""

import json
import httpx
from typing import Any

PENNYLANE_BASE = "https://app.pennylane.com/api/external/v2"


def _filters(*conditions: dict) -> list[tuple]:
    """Build v2 filters param: filters=[{...},{...}] as a single JSON array."""
    if not conditions:
        return []
    return [("filters", json.dumps(list(conditions)))]


def _f(field: str, operator: str, value: str) -> dict:
    """Build a single filter condition dict."""
    return {"field": field, "operator": operator, "value": value}


class PennyLaneClient:
    def __init__(self, api_token: str, company_id: str | None = None):
        self.api_token = api_token
        self.company_id = company_id
        self._client = httpx.AsyncClient(
            base_url=PENNYLANE_BASE,
            headers={
                "Authorization": f"Bearer {api_token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            timeout=30.0,
        )

    async def _get(self, path: str, params=None) -> Any:
        r = await self._client.get(path, params=params or {})
        r.raise_for_status()
        return r.json()

    async def close(self):
        await self._client.aclose()

    def _extract_items(self, data: dict, *keys: str) -> list:
        """Extract items from response, checking 'items' first, then fallback keys."""
        for key in ("items",) + keys:
            if key in data and isinstance(data[key], list):
                return data[key]
        return []

    async def _get_all_cursor(self, path: str, base_params: list, *item_keys: str) -> list:
        """Paginate through all pages using cursor-based pagination."""
        results = []
        cursor = None
        while True:
            params = list(base_params)
            if cursor:
                params.append(("cursor", cursor))
            data = await self._get(path, params)
            items = self._extract_items(data, *item_keys)
            results.extend(items)
            if not data.get("has_more", False):
                break
            cursor = data.get("next_cursor")
            if not cursor:
                break
        return results

    # ── Invoices (ventes) ────────────────────────────────────────────────
    async def get_invoices(
        self,
        date_from: str | None = None,
        date_to: str | None = None,
        status: str | None = None,
        per_page: int = 100,
        cursor: str | None = None,
    ) -> dict:
        conditions = []
        if date_from:
            conditions.append(_f("date", "gteq", date_from))
        if date_to:
            conditions.append(_f("date", "lteq", date_to))
        if status:
            conditions.append(_f("status", "eq", status))
        params = [("per_page", per_page)]
        if cursor:
            params.append(("cursor", cursor))
        params += _filters(*conditions)
        return await self._get("/customer_invoices", params)

    async def get_all_invoices(self, date_from: str | None = None, date_to: str | None = None) -> list:
        conditions = []
        if date_from:
            conditions.append(_f("date", "gteq", date_from))
        if date_to:
            conditions.append(_f("date", "lteq", date_to))
        base_params = [("per_page", 100)] + _filters(*conditions)
        return await self._get_all_cursor("/customer_invoices", base_params, "invoices", "customer_invoices", "data")

    # ── Supplier invoices (achats) ────────────────────────────────────────
    async def get_supplier_invoices(
        self,
        date_from: str | None = None,
        date_to: str | None = None,
        per_page: int = 100,
        cursor: str | None = None,
    ) -> dict:
        conditions = []
        if date_from:
            conditions.append(_f("date", "gteq", date_from))
        if date_to:
            conditions.append(_f("date", "lteq", date_to))
        params = [("per_page", per_page)]
        if cursor:
            params.append(("cursor", cursor))
        params += _filters(*conditions)
        return await self._get("/supplier_invoices", params)

    async def get_all_supplier_invoices(self, date_from: str | None = None, date_to: str | None = None) -> list:
        conditions = []
        if date_from:
            conditions.append(_f("date", "gteq", date_from))
        if date_to:
            conditions.append(_f("date", "lteq", date_to))
        base_params = [("per_page", 100)] + _filters(*conditions)
        all_items = await self._get_all_cursor("/supplier_invoices", base_params, "invoices", "supplier_invoices", "data")
        # Client-side date filter since server-side filter may not work
        if date_from or date_to:
            filtered = []
            for item in all_items:
                d = item.get("date")
                if d is None:
                    continue
                if date_from and d < date_from:
                    continue
                if date_to and d > date_to:
                    continue
                filtered.append(item)
            return filtered
        return all_items

    # ── Journal entries / grand livre ────────────────────────────────────
    async def get_journal_entries(
        self,
        date_from: str | None = None,
        date_to: str | None = None,
        account_number: str | None = None,
        per_page: int = 200,
        cursor: str | None = None,
    ) -> dict:
        conditions = []
        if date_from:
            conditions.append(_f("date", "gteq", date_from))
        if date_to:
            conditions.append(_f("date", "lteq", date_to))
        if account_number:
            conditions.append(_f("account_number", "eq", account_number))
        params = [("per_page", per_page)]
        if cursor:
            params.append(("cursor", cursor))
        params += _filters(*conditions)
        return await self._get("/accounting_entries", params)

    async def get_all_journal_entries(
        self,
        date_from: str | None = None,
        date_to: str | None = None,
        account_number: str | None = None,
    ) -> list:
        conditions = []
        if date_from:
            conditions.append(_f("date", "gteq", date_from))
        if date_to:
            conditions.append(_f("date", "lteq", date_to))
        if account_number:
            conditions.append(_f("account_number", "eq", account_number))
        base_params = [("per_page", 200)] + _filters(*conditions)
        return await self._get_all_cursor("/accounting_entries", base_params, "accounting_entries", "data")

    # ── Bank transactions ─────────────────────────────────────────────────
    async def get_bank_transactions(
        self,
        date_from: str | None = None,
        date_to: str | None = None,
        account_id: str | None = None,
        per_page: int = 200,
        cursor: str | None = None,
    ) -> dict:
        conditions = []
        if date_from:
            conditions.append(_f("date", "gteq", date_from))
        if date_to:
            conditions.append(_f("date", "lteq", date_to))
        if account_id:
            conditions.append(_f("bank_account_id", "eq", account_id))
        params = [("per_page", per_page)]
        if cursor:
            params.append(("cursor", cursor))
        params += _filters(*conditions)
        return await self._get("/transactions", params)

    async def get_all_bank_transactions(
        self,
        date_from: str | None = None,
        date_to: str | None = None,
        account_id: str | None = None,
    ) -> list:
        conditions = []
        if date_from:
            conditions.append(_f("date", "gteq", date_from))
        if date_to:
            conditions.append(_f("date", "lteq", date_to))
        if account_id:
            conditions.append(_f("bank_account_id", "eq", account_id))
        base_params = [("per_page", 200)] + _filters(*conditions)
        all_items = await self._get_all_cursor("/transactions", base_params, "transactions", "data")
        # Client-side date filter
        if date_from or date_to:
            filtered = []
            for item in all_items:
                d = item.get("date")
                if d is None:
                    continue
                if date_from and d < date_from:
                    continue
                if date_to and d > date_to:
                    continue
                filtered.append(item)
            return filtered
        return all_items

    # ── P&L / Balance sheet / Trial balance ──────────────────────────────
    async def get_income_statement(
        self, date_from: str, date_to: str, compare: bool = False
    ) -> dict:
        # v2: income_statement endpoint removed — use trial_balance instead
        return await self.get_trial_balance(date_from, date_to)

    async def get_balance_sheet(self, date: str) -> dict:
        params = _filters(_f("date", "lteq", date))
        return await self._get("/balance_sheet", params)

    async def get_trial_balance(
        self, date_from: str, date_to: str
    ) -> dict:
        params = _filters(
            _f("start_date", "eq", date_from),
            _f("end_date", "eq", date_to),
        )
        return await self._get("/trial_balance", params)

    async def get_company(self) -> dict:
        data = await self._get("/customer_invoices", [("per_page", 1)])
        return {"token_valid": True, "sample": self._extract_items(data)[:1]}
