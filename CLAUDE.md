# CLAUDE.md - Guide pour les agents Claude

## Vue d'ensemble du projet

MCP Proxy SanteCall est un serveur proxy qui traduit les requêtes MCP (Model Context Protocol / JSON-RPC 2.0) vers l'API REST SanteCall. Il permet à Reecall d'interroger la base de données patients SanteCall.

```
Reecall ──(MCP/JSON-RPC)──> Ce serveur ──(REST/GET)──> hds.santecall.ai
```

## Structure du projet

```
mcp-proxy-santecall/
├── src/
│   └── server.py       # Serveur Flask MCP (point d'entrée principal)
├── Dockerfile          # Config Docker pour Railway
├── railway.json        # Config Railway (sans healthcheck custom)
├── requirements.txt    # Dépendances Python
├── .env.example        # Template variables d'environnement
├── test_mcp.sh         # Script de test des endpoints
└── README.md
```

## Déploiement actuel

- **URL de production** : https://mpc-proxy-production.up.railway.app
- **Endpoint MCP** : https://mpc-proxy-production.up.railway.app/mcp
- **Hébergeur** : Railway (déploiement automatique depuis GitHub)
- **Repo GitHub** : https://github.com/clousty8/mpc-proxy

## Commandes utiles

### Tester le serveur en local
```bash
source venv/bin/activate
python src/server.py
# Puis dans un autre terminal :
./test_mcp.sh
```

### Tester le serveur de production
```bash
./test_mcp.sh https://mpc-proxy-production.up.railway.app
```

### Déployer une modification
```bash
git add .
git commit -m "Description du changement"
git push
# Railway redéploie automatiquement
```

## Variables d'environnement (Railway)

Ces variables sont configurées dans Railway → Settings → Variables :
- `SANTECALL_API_URL` : URL de l'API SanteCall (défaut: https://hds.santecall.ai/public/lookup)
- `SANTECALL_TOKEN` : Token d'authentification SanteCall
- `DEFAULT_VOLUBILE_ID` : ID du cabinet par défaut
- `PORT` : Assigné automatiquement par Railway

## Endpoints disponibles

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/` | Health check |
| POST | `/` ou `/mcp` | Endpoint MCP (JSON-RPC 2.0) |

## Outils MCP exposés

### `search_patient`
Recherche un patient par numéro de téléphone.

**Paramètres :**
- `phone` (requis) : Numéro au format international (+33...)
- `volubile_id` (optionnel) : ID du cabinet

**Retourne :** Infos patient, cabinet, rendez-vous programmés, fonctionnalités disponibles.

## Notes techniques

- Le Dockerfile copie `src/server.py` directement dans `/app/server.py` (pas de sous-dossier)
- Gunicorn utilise `server:app` comme point d'entrée
- Le healthcheck Railway est désactivé dans `railway.json` pour éviter les faux positifs au démarrage
- CORS est activé pour permettre les appels depuis n'importe quelle origine

## Problèmes connus et solutions

### Le healthcheck Railway échoue
Le healthcheck a été désactivé dans `railway.json`. Si besoin de le réactiver, s'assurer que le serveur démarre assez vite (< 30s).

### Erreur 401 sur search_patient
Les variables d'environnement `SANTECALL_TOKEN` et/ou `DEFAULT_VOLUBILE_ID` ne sont pas configurées sur Railway.
