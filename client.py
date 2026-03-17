"""PennyLane API client — wraps https://app.pennylane.com/api/external/v2/"""

import httpx
from typing import Any

PENNYLANE_BASE = "https://app.pennylane.com/api/external/v2"


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

    async def _get(self, path: str, params: dict | None = None) -> Any:
        r = await self._client.get(path, params=params or {})
        r.raise_for_status()
        return r.json()

    async def close(self):
        await self._client.aclose()

    # ── Company ──────────────────────────────────────────────────────────
    async def get_company(self) -> dict:
        return await self._get("/company")

    # ── Invoices (ventes) ────────────────────────────────────────────────
    async def get_invoices(
        self,
        date_from: str | None = None,
        date_to: str | None = None,
        status: str | None = None,
        page: int = 1,
        per_page: int = 100,
    ) -> dict:
        params = {"page": page, "per_page": per_page}
        if date_from:
            params["filter[date][gte]"] = date_from
        if date_to:
            params["filter[date][lte]"] = date_to
        if status:
            params["filter[status]"] = status
        return await self._get("/customer_invoices", params)

    async def get_all_invoices(self, date_from: str | None = None, date_to: str | None = None) -> list:
        results, page = [], 1
        while True:
            data = await self.get_invoices(date_from=date_from, date_to=date_to, page=page)
            items = data.get("invoices", data.get("data", []))
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
        params = {"page": page, "per_page": per_page}
        if date_from:
            params["filter[date][gte]"] = date_from
        if date_to:
            params["filter[date][lte]"] = date_to
        return await self._get("/supplier_invoices", params)

    async def get_all_supplier_invoices(self, date_from: str | None = None, date_to: str | None = None) -> list:
        results, page = [], 1
        while True:
            data = await self.get_supplier_invoices(date_from=date_from, date_to=date_to, page=page)
            items = data.get("invoices", data.get("data", []))
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
        params = {"page": page, "per_page": per_page}
        if date_from:
            params["filter[date][gte]"] = date_from
        if date_to:
            params["filter[date][lte]"] = date_to
        if account_number:
            params["filter[account_number]"] = account_number
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

    # ── Chart of accounts ────────────────────────────────────────────────
    async def get_chart_of_accounts(self) -> list:
        data = await self._get("/chart_of_accounts")
        return data.get("accounts", data.get("data", data))

    # ── Bank transactions ────────────────────────────────────────────────
    async def get_bank_transactions(
        self,
        date_from: str | None = None,
        date_to: str | None = None,
        account_id: str | None = None,
        page: int = 1,
        per_page: int = 200,
    ) -> dict:
        params = {"page": page, "per_page": per_page}
        if date_from:
            params["filter[date][gte]"] = date_from
        if date_to:
            params["filter[date][lte]"] = date_to
        if account_id:
            params["filter[account_id]"] = account_id
        return await self._get("/bank_transactions", params)

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

    # ── P&L / Balance sheet ──────────────────────────────────────────────
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
