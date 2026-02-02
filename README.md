# MCP Proxy SanteCall

Serveur proxy qui traduit les requêtes MCP (Model Context Protocol / JSON-RPC 2.0) vers l'API REST SanteCall.

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

### Option 1: Via GitHub (recommandé)

1. **Pusher sur GitHub:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit - MCP Proxy SanteCall"
   git branch -M main
   git remote add origin https://github.com/VOTRE_USERNAME/mcp-proxy-santecall.git
   git push -u origin main
   ```

2. **Sur Railway:**
   - Aller sur [railway.app](https://railway.app)
   - "New Project" → "Deploy from GitHub repo"
   - Sélectionner `mcp-proxy-santecall`
   - Railway détecte automatiquement le Dockerfile

3. **Configurer les variables d'environnement sur Railway:**
   - Dans Settings → Variables, ajouter:
     - `SANTECALL_API_URL` = `https://hds.santecall.ai/public/lookup`
     - `SANTECALL_TOKEN` = `votre_token`
     - `DEFAULT_VOLUBILE_ID` = `votre_volubile_id`

4. **Récupérer l'URL:**
   - Railway génère une URL publique (ex: `https://mcp-proxy-santecall-production.up.railway.app`)

### Option 2: Via Railway CLI

```bash
# Installer Railway CLI
npm install -g @railway/cli

# Login
railway login

# Initialiser le projet
railway init

# Déployer
railway up

# Voir les logs
railway logs
```

## Enregistrer sur Reecall

Une fois déployé, enregistrer le MCP sur Reecall:

```bash
curl -X POST "https://newprd.reecall.io/data_next/ai/mcp" \
  -H "Authorization: Bearer VOTRE_API_KEY_REECALL" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "SanteCall Patient Lookup",
    "description": "Recherche de patients dans la base SanteCall",
    "url": "https://votre-app.up.railway.app/mcp"
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
