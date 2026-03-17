# PennyLane MCP — Mecanicus Group

Connecteur MCP qui donne à Claude un accès direct aux données PennyLane :
factures, écritures, transactions bancaires (Qonto/MemoBank/CE/SG), P&L, bilan.

## Déploiement en 3 étapes

### 1. Récupérer le token API PennyLane

Dans PennyLane : **Paramètres → Intégrations → API → Créer un token**

Copier le token généré.

### 2. Déployer sur Railway (gratuit, 2 minutes)

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/template)

1. Aller sur [railway.app](https://railway.app) → New Project → Deploy from GitHub
2. Fork ce repo ou uploader le dossier
3. Dans les variables d'environnement Railway, ajouter :
   ```
   PENNYLANE_API_TOKEN=ton_token_ici
   PENNYLANE_COMPANY_ID=ton_company_id  (optionnel)
   ```
4. Railway génère une URL publique (ex: `https://pennylane-mcp-production.up.railway.app`)

### 3. Enregistrer dans Cowork

Dans Cowork → Settings → Connectors → Add MCP Server :
```
URL: https://pennylane-mcp-production.up.railway.app
Nom: PennyLane Mecanicus
```

C'est tout. Claude a maintenant accès live à PennyLane.

---

## Utilisation locale (optionnel)

```bash
pip install -e .
export PENNYLANE_API_TOKEN="ton_token"
pennylane-mcp
```

## Outils disponibles

| Outil | Description |
|-------|-------------|
| `get_income_statement` | P&L sur une période |
| `get_balance_sheet` | Bilan à une date |
| `get_trial_balance` | Balance des comptes (grand livre) |
| `get_journal_entries` | Écritures comptables, filtrables par compte |
| `get_invoices` | Factures clients (ventes) |
| `get_supplier_invoices` | Factures fournisseurs (achats véhicules, Mecanicus, Caption) |
| `get_bank_transactions` | Transactions bancaires (toutes banques connectées à PL) |
| `get_company_info` | Info entreprise + comptes bancaires |
| `get_chart_of_accounts` | Plan comptable |

## Notes

- PennyLane ingère automatiquement Qonto, MemoBank, CE et SG → `get_bank_transactions` retourne tout
- Pour filtrer par entité (SM1/SM2/Mecanicus), utiliser plusieurs tokens (un par company dans PennyLane)
- Le token API est par company PennyLane — déployer une instance par entité si nécessaire
