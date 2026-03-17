"""PennyLane API client — wraps https://app.pennylane.com/api/external/v2/"""

import json
import httpx
from typing import Any

PENNYLANE_BASE = "https://app.pennylane.com/api/external/v2"


def _f(field: str, operator: str, value: str) -> tuple:
    """Build a single v2 filter tuple for httpx params."""
    return ("filters[]", json.dumps({"field": field, "operator": operator, "value": value}))


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

    # ── Invoices (ventes) ────────────────────────────────────────────────
    async def get_invoices(
        self,
        date_from: str | None = None,
        date_to: str | None = None,
        status: str | None = None,
        page: int = 1,
        per_page: int = 100,
    ) -> dict:
        params = [("page", page), ("per_page", per_page)]
        if date_from:
            params.append(_f("date", "gteq", date_from))
        if date_to:
            params.append(_f("date", "lteq", date_to))
        if status:
            params.append(_f("status", "eq", status))
        return await self._get("/customer_invoices", params)

    async def get_all_invoices(self, date_from: str | None = None, date_to: str | None = None) -> list:
        results, page = [], 1
        while True:
            data = await self.get_invoices(date_from=date_from, date_to=date_to, page=page)
            items = data.get("invoices", data.get("customer_invoices", data.get("data", [])))
            results.extend(items)
            meta = data.get("meta", data.get("pagination", {}))
            total_pages = meta.get("total_pages", meta.get("last_page", 1))
            if page >= total_pages:
                break
            page += 1
        return results

    # ── Supplier invoices (achats) ────────────────────────────────────────
    async def get_supplier_invoices(
        self,
        date_from: str | None = None,
        date_to: str | None = None,
        page: int = 1,
        per_page: int = 100,
    ) -> dict:
        params = [("page", page), ("per_page", per_page)]
        if date_from:
            params.append(_f("date", "gteq", date_from))
        if date_to:
            params.append(_f("date", "lteq", date_to))
        return await self._get("/supplier_invoices", params)

    async def get_all_supplier_invoices(self, date_from: str | None = None, date_to: str | None = None) -> list:
        results, page = [], 1
        while True:
            data = await self.get_supplier_invoices(date_from=date_from, date_to=date_to, page=page)
            items = data.get("invoices", data.get("supplier_invoices", data.get("data", [])))
            results.extend(items)
            meta = data.get("meta", data.get("pagination", {}))
            total_pages = meta.get("total_pages", meta.get("last_page", 1))
            if page >= total_pages:
                break
            page += 1
        return results

    # ── Journal entries / grand livre ────────────────────────────────────
    async def get_journal_entries(
        self,
        date_from: str | None = None,
        date_to: str | None = None,
        account_number: str | None = None,
        page: int = 1,
        per_page: int = 200,
    ) -> dict:
        params = [("page", page), ("per_page", per_page)]
        if date_from:
            params.append(_f("date", "gteq", date_from))
        if date_to:
            params.append(_f("date", "lteq", date_to))
        if account_number:
            params.append(_f("account_number", "eq", account_number))
        return await self._get("/accounting_entries", params)

    async def get_all_journal_entries(
        self,
        date_from: str | None = None,
        date_to: str | None = None,
        account_number: str | None = None,
    ) -> list:
        results, page = [], 1
        while True:
            data = await self.get_journal_entries(
                date_from=date_from, date_to=date_to,
                account_number=account_number, page=page
            )
            items = data.get("accounting_entries", data.get("data", []))
            results.extend(items)
            meta = data.get("meta", data.get("pagination", {}))
            total_pages = meta.get("total_pages", meta.get("last_page", 1))
            if page >= total_pages:
                break
            page += 1
        return results

    # ── Bank transactions ─────────────────────────────────────────────────
    # v2: endpoint is /transactions (not /bank_transactions)
    async def get_bank_transactions(
        self,
        date_from: str | None = None,
        date_to: str | None = None,
        account_id: str | None = None,
        page: int = 1,
        per_page: int = 200,
    ) -> dict:
        params = [("page", page), ("per_page", per_page)]
        if date_from:
            params.append(_f("date", "gteq", date_from))
        if date_to:
            params.append(_f("date", "lteq", date_to))
        if account_id:
            params.append(_f("bank_account_id", "eq", account_id))
        return await self._get("/transactions", params)

    async def get_all_bank_transactions(
        self,
        date_from: str | None = None,
        date_to: str | None = None,
        account_id: str | None = None,
    ) -> list:
        results, page = [], 1
        while True:
            data = await self.get_bank_transactions(
                date_from=date_from, date_to=date_to,
                account_id=account_id, page=page
            )
            items = data.get("transactions", data.get("data", []))
            results.extend(items)
            meta = data.get("meta", data.get("pagination", {}))
            total_pages = meta.get("total_pages", meta.get("last_page", 1))
            if page >= total_pages:
                break
            page += 1
        return results

    # ── P&L / Balance sheet / Trial balance ──────────────────────────────
    async def get_income_statement(
        self, date_from: str, date_to: str, compare: bool = False
    ) -> dict:
        params = {
            "filter[start_date]": date_from,
            "filter[end_date]": date_to,
        }
        if compare:
            params["compare"] = "true"
        return await self._get("/income_statement", params)

    async def get_balance_sheet(self, date: str) -> dict:
        return await self._get("/balance_sheet", {"filter[date]": date})

    async def get_trial_balance(
        self, date_from: str, date_to: str
    ) -> dict:
        return await self._get("/trial_balance", {
            "filter[start_date]": date_from,
            "filter[end_date]": date_to,
        })
