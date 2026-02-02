# MCP Proxy SanteCall

Serveur proxy qui traduit les requêtes MCP (Model Context Protocol / JSON-RPC 2.0) vers l'API REST SanteCall.

## Déploiement

**Production** : https://mpc-proxy-production.up.railway.app

**Endpoint MCP** : `https://mpc-proxy-production.up.railway.app/mcp`

## Architecture

```
Reecall ──(MCP/JSON-RPC)──> Ce serveur ──(REST/GET)──> hds.santecall.ai
```

## Outils disponibles

### `search_patient`
Recherche un patient par son numéro de téléphone.

**Paramètres:**
- `phone` (requis): Numéro de téléphone au format international (+33...)
- `volubile_id` (optionnel): ID du cabinet

**Retourne:**
- Informations patient (nom, prénom, email, téléphone)
- Informations cabinet (nom, adresse, horaires)
- Rendez-vous programmés
- Fonctionnalités disponibles (confirmation, annulation, prise RDV)

## Installation locale

```bash
# Cloner le repo
git clone https://github.com/VOTRE_USERNAME/mcp-proxy-santecall.git
cd mcp-proxy-santecall

# Créer l'environnement virtuel
python3 -m venv venv
source venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt

# Configurer les variables d'environnement
cp .env.example .env
# Éditer .env avec vos valeurs

# Lancer le serveur
python src/server.py
```

## Tests

```bash
# Rendre le script exécutable
chmod +x test_mcp.sh

# Tester en local
./test_mcp.sh

# Tester sur Railway
./test_mcp.sh https://votre-app.up.railway.app
```

## Déploiement sur Railway

Le projet est déjà déployé sur Railway et se redéploie automatiquement à chaque push sur `main`.

- **GitHub** : https://github.com/clousty8/mpc-proxy
- **Railway** : https://mpc-proxy-production.up.railway.app

### Variables d'environnement (déjà configurées sur Railway)

- `SANTECALL_API_URL` = `https://hds.santecall.ai/public/lookup`
- `SANTECALL_TOKEN` = token d'authentification
- `DEFAULT_VOLUBILE_ID` = ID du cabinet par défaut

### Redéployer

```bash
git add .
git commit -m "Description"
git push
# Railway redéploie automatiquement
```

### Voir les logs

Sur Railway → ton service → onglet "Logs"

## Enregistrer sur Reecall

Enregistrer le MCP sur Reecall:

```bash
curl -X POST "https://newprd.reecall.io/data_next/ai/mcp" \
  -H "Authorization: Bearer VOTRE_API_KEY_REECALL" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "SanteCall Patient Lookup",
    "description": "Recherche de patients dans la base SanteCall",
    "url": "https://mpc-proxy-production.up.railway.app/mcp"
  }'
```

Puis associer à un assistant:

```bash
curl -X PATCH "https://newprd.reecall.io/data_next/conversational/assistants/ASSISTANT_ID" \
  -H "Authorization: Bearer VOTRE_API_KEY_REECALL" \
  -H "Content-Type: application/json" \
  -d '{
    "mcpIds": ["MCP_ID_RETOURNÉ"]
  }'
```

## Format des requêtes MCP

### tools/list
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/list",
  "params": {}
}
```

### tools/call
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/call",
  "params": {
    "name": "search_patient",
    "arguments": {
      "phone": "+33678951483"
    }
  }
}
```

## Structure du projet

```
mcp-proxy-santecall/
├── src/
│   └── server.py       # Serveur Flask MCP
├── Dockerfile          # Config Docker
├── railway.json        # Config Railway
├── requirements.txt    # Dépendances Python
├── .env.example        # Template variables d'env
├── .gitignore
├── test_mcp.sh         # Script de test
└── README.md
```

## Licence

MIT
