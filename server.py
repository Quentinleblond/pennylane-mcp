"""
PennyLane MCP Server — Mecanicus Group
Gère les 3 sociétés (SM1, SM2, Mecanicus) avec un seul déploiement.
"""

import asyncio
import json
import os
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

from .client import PennyLaneClient

# ── Tokens par société (injectés via variables d'environnement Railway) ───
TOKENS = {
    "SM1":       os.environ.get("PENNYLANE_TOKEN_SM1", ""),
    "SM2":       os.environ.get("PENNYLANE_TOKEN_SM2", ""),
    "Mecanicus": os.environ.get("PENNYLANE_TOKEN_MECANICUS", ""),
}

_clients: dict[str, PennyLaneClient] = {}

def get_client(company: str) -> PennyLaneClient:
    company = company.strip()
    if company not in TOKENS:
        raise ValueError(f"Société inconnue: '{company}'. Valeurs acceptées: SM1, SM2, Mecanicus")
    token = TOKENS[company]
    if not token:
        raise ValueError(f"Token manquant pour {company} (variable PENNYLANE_TOKEN_{company.upper()} non configurée)")
    if company not in _clients:
        _clients[company] = PennyLaneClient(token)
    return _clients[company]

def fmt(data: Any) -> list[types.TextContent]:
    return [types.TextContent(type="text", text=json.dumps(data, ensure_ascii=False, indent=2))]

COMPANY_PARAM = {
    "company": {
        "type": "string",
        "description": "Société : 'SM1' (Scuderia Meca), 'SM2' (Scuderia Meca 2), ou 'Mecanicus'",
        "enum": ["SM1", "SM2", "Mecanicus"],
    }
}

server = Server("pennylane-mcp")

# ── Tool definitions ──────────────────────────────────────────────────────
@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="get_income_statement",
            description=(
                "Compte de résultat PennyLane (P&L) sur une période. "
                "Retourne produits, charges et résultat par compte PCG. "
                "Inclut toutes les lignes : ventes véhicules (707), achats (607), "
                "frais de gestion Mecanicus (622), intérêts Caption (661), etc."
            ),
            inputSchema={
                "type": "object",
                "properties": {**COMPANY_PARAM,
                    "date_from": {"type": "string", "description": "Date début YYYY-MM-DD"},
                    "date_to":   {"type": "string", "description": "Date fin YYYY-MM-DD"},
                },
                "required": ["company", "date_from", "date_to"],
            },
        ),
        types.Tool(
            name="get_balance_sheet",
            description="Bilan PennyLane à une date donnée (actif, passif, capitaux propres).",
            inputSchema={
                "type": "object",
                "properties": {**COMPANY_PARAM,
                    "date": {"type": "string", "description": "Date YYYY-MM-DD"},
                },
                "required": ["company", "date"],
            },
        ),
        types.Tool(
            name="get_trial_balance",
            description=(
                "Balance des comptes (grand livre agrégé) — solde de chaque compte PCG "
                "sur une période. Utile pour voir les 707, 607, 603, 661, 622, 47x, etc."
            ),
            inputSchema={
                "type": "object",
                "properties": {**COMPANY_PARAM,
                    "date_from": {"type": "string", "description": "Date début YYYY-MM-DD"},
                    "date_to":   {"type": "string", "description": "Date fin YYYY-MM-DD"},
                },
                "required": ["company", "date_from", "date_to"],
            },
        ),
        types.Tool(
            name="get_journal_entries",
            description=(
                "Écritures comptables (journal) sur une période. "
                "Filtrable par compte PCG (ex: '707' pour ventes, '607' pour achats, "
                "'661' pour intérêts Caption, '622' pour frais Mecanicus). "
                "Retourne toutes les lignes d'écriture avec date, libellé, débit/crédit."
            ),
            inputSchema={
                "type": "object",
                "properties": {**COMPANY_PARAM,
                    "date_from":      {"type": "string", "description": "Date début YYYY-MM-DD"},
                    "date_to":        {"type": "string", "description": "Date fin YYYY-MM-DD"},
                    "account_number": {"type": "string", "description": "Filtre compte PCG (optionnel, ex: '707')"},
                },
                "required": ["company", "date_from", "date_to"],
            },
        ),
        types.Tool(
            name="get_invoices",
            description=(
                "Factures clients (ventes) PennyLane sur une période. "
                "Inclut montant HT/TTC, date, statut paiement, client. "
                "Utile pour réconcilier le CA avec Airtable (cut-off)."
            ),
            inputSchema={
                "type": "object",
                "properties": {**COMPANY_PARAM,
                    "date_from": {"type": "string", "description": "Date début YYYY-MM-DD"},
                    "date_to":   {"type": "string", "description": "Date fin YYYY-MM-DD"},
                    "status":    {"type": "string", "description": "Statut : 'paid', 'unpaid', 'draft' (optionnel)"},
                },
                "required": ["company", "date_from", "date_to"],
            },
        ),
        types.Tool(
            name="get_supplier_invoices",
            description=(
                "Factures fournisseurs (achats) PennyLane sur une période. "
                "Inclut achats véhicules, frais de gestion Mecanicus (FAC000xxx), "
                "coupons Caption, frais d'immatriculation, entretiens."
            ),
            inputSchema={
                "type": "object",
                "properties": {**COMPANY_PARAM,
                    "date_from": {"type": "string", "description": "Date début YYYY-MM-DD"},
                    "date_to":   {"type": "string", "description": "Date fin YYYY-MM-DD"},
                },
                "required": ["company", "date_from", "date_to"],
            },
        ),
        types.Tool(
            name="get_bank_transactions",
            description=(
                "Transactions bancaires importées dans PennyLane — "
                "toutes les banques connectées : Qonto, MemoBank, Caisse d'Épargne, SG. "
                "Retourne chaque mouvement avec date, libellé, montant, banque. "
                "C'est la source pour le P&L 2026 en temps réel."
            ),
            inputSchema={
                "type": "object",
                "properties": {**COMPANY_PARAM,
                    "date_from":  {"type": "string", "description": "Date début YYYY-MM-DD"},
                    "date_to":    {"type": "string", "description": "Date fin YYYY-MM-DD"},
                    "account_id": {"type": "string", "description": "ID compte bancaire pour filtrer (optionnel)"},
                },
                "required": ["company", "date_from", "date_to"],
            },
        ),
        types.Tool(
            name="get_company_info",
            description="Info société + liste des comptes bancaires connectés à PennyLane.",
            inputSchema={
                "type": "object",
                "properties": COMPANY_PARAM,
                "required": ["company"],
            },
        ),
    ]


# ── Tool handlers ─────────────────────────────────────────────────────────
@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    company = arguments.get("company", "SM1")
    try:
        client = get_client(company)

        if name == "get_income_statement":
            data = await client.get_income_statement(arguments["date_from"], arguments["date_to"])
            return fmt({"company": company, **data})

        elif name == "get_balance_sheet":
            data = await client.get_balance_sheet(arguments["date"])
            return fmt({"company": company, **data})

        elif name == "get_trial_balance":
            data = await client.get_trial_balance(arguments["date_from"], arguments["date_to"])
            return fmt({"company": company, **data})

        elif name == "get_journal_entries":
            entries = await client.get_all_journal_entries(
                date_from=arguments.get("date_from"),
                date_to=arguments.get("date_to"),
                account_number=arguments.get("account_number"),
            )
            return fmt({"company": company, "count": len(entries), "entries": entries})

        elif name == "get_invoices":
            invoices = await client.get_all_invoices(
                date_from=arguments.get("date_from"),
                date_to=arguments.get("date_to"),
            )
            total_ht  = sum(float(i.get("amount", 0)) for i in invoices)
            total_ttc = sum(float(i.get("amount_with_tax", i.get("total_amount", 0))) for i in invoices)
            return fmt({"company": company, "count": len(invoices),
                        "total_ht": round(total_ht, 2), "total_ttc": round(total_ttc, 2),
                        "invoices": invoices})

        elif name == "get_supplier_invoices":
            invoices = await client.get_all_supplier_invoices(
                date_from=arguments.get("date_from"),
                date_to=arguments.get("date_to"),
            )
            total = sum(float(i.get("amount", i.get("total_amount", 0))) for i in invoices)
            return fmt({"company": company, "count": len(invoices),
                        "total": round(total, 2), "invoices": invoices})

        elif name == "get_bank_transactions":
            txns = await client.get_all_bank_transactions(
                date_from=arguments.get("date_from"),
                date_to=arguments.get("date_to"),
                account_id=arguments.get("account_id"),
            )
            credits = sum(float(t.get("amount", 0)) for t in txns
                          if float(t.get("amount", 0)) > 0)
            debits  = sum(abs(float(t.get("amount", 0))) for t in txns
                          if float(t.get("amount", 0)) < 0)
            return fmt({"company": company, "count": len(txns),
                        "total_credits": round(credits, 2),
                        "total_debits":  round(debits, 2),
                        "net": round(credits - debits, 2),
                        "transactions": txns})

        elif name == "get_company_info":
            data = await client.get_company()
            return fmt({"company": company, **data})

        else:
            return fmt({"error": f"Outil inconnu: {name}"})

    except Exception as e:
        return fmt({"error": str(e), "company": company, "tool": name})


# ── Entry point ───────────────────────────────────────────────────────────
async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())

def run():
    asyncio.run(main())
