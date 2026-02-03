"""
MCP Proxy Server - Traduit les requêtes MCP (JSON-RPC 2.0) vers l'API REST SanteCall
"""

import os
import sys
import logging
from datetime import datetime
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Force flush pour Railway
class FlushHandler(logging.StreamHandler):
    def emit(self, record):
        super().emit(record)
        self.flush()

# Remplacer le handler par défaut
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)
logging.root.addHandler(FlushHandler(sys.stdout))
logging.root.setLevel(logging.INFO)

app = Flask(__name__)
CORS(app)

# Configuration
SANTECALL_API_URL = os.getenv("SANTECALL_API_URL", "https://hds.santecall.ai/public/lookup")
SANTECALL_TOKEN = os.getenv("SANTECALL_TOKEN", "")
DEFAULT_VOLUBILE_ID = os.getenv("DEFAULT_VOLUBILE_ID", "")

# Definition des outils disponibles
TOOLS = [
    {
        "name": "search_patient",
        "description": "Recherche un patient par son numéro de téléphone. Retourne les informations du patient, ses rendez-vous programmés, et les informations du cabinet.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "phone": {
                    "type": "string",
                    "description": "Numéro de téléphone du patient (format international, ex: +33678951483)"
                },
                "volubile_id": {
                    "type": "string",
                    "description": "ID du cabinet (optionnel, utilise la valeur par défaut si non fourni)"
                }
            },
            "required": ["phone"]
        }
    }
]


def make_jsonrpc_response(id, result):
    """Crée une réponse JSON-RPC 2.0 valide"""
    return {
        "jsonrpc": "2.0",
        "id": id,
        "result": result
    }


def make_jsonrpc_error(id, code, message):
    """Crée une erreur JSON-RPC 2.0 valide"""
    return {
        "jsonrpc": "2.0",
        "id": id,
        "error": {
            "code": code,
            "message": message
        }
    }


def call_santecall_api(phone, volubile_id=None):
    """Appelle l'API SanteCall et retourne les données du patient"""
    logger.info(f"[SanteCall API] Appel avec phone={phone}, volubile_id={volubile_id or DEFAULT_VOLUBILE_ID}")

    params = {
        "phone": phone,
        "token": SANTECALL_TOKEN,
        "volubile_id": volubile_id or DEFAULT_VOLUBILE_ID
    }

    try:
        response = requests.get(SANTECALL_API_URL, params=params, timeout=30)
        logger.info(f"[SanteCall API] Réponse status={response.status_code}")
        response.raise_for_status()
        data = response.json()
        logger.info(f"[SanteCall API] Patient trouvé: {data.get('first_name', 'N/A')} {data.get('last_name', 'N/A')}")
        return data
    except requests.exceptions.RequestException as e:
        logger.error(f"[SanteCall API] Erreur: {str(e)}")
        raise Exception(f"Erreur API SanteCall: {str(e)}")


def format_patient_response(data):
    """Formate les données patient pour une réponse lisible par l'IA"""
    if not data:
        return "Aucun patient trouvé avec ce numéro de téléphone."

    # Construire une réponse textuelle structurée
    lines = []

    # Infos patient
    lines.append(f"=== PATIENT ===")
    lines.append(f"Civilité: {data.get('civilite', 'Non renseigné')}")
    lines.append(f"Prénom: {data.get('first_name', 'Non renseigné')}")
    lines.append(f"Nom: {data.get('last_name', 'Non renseigné')}")
    lines.append(f"Téléphone: {data.get('phone_number', 'Non renseigné')}")
    lines.append(f"Email: {data.get('email_patient', 'Non renseigné')}")
    lines.append(f"Statut cabinet: {data.get('cabinet_status', 'Non renseigné')}")

    # Infos cabinet
    lines.append(f"\n=== CABINET ===")
    lines.append(f"Nom: {data.get('cabinet_nom', 'Non renseigné')}")
    lines.append(f"Adresse: {data.get('cabinet_adresse', 'Non renseigné')}")
    lines.append(f"Horaires: {data.get('cabinet_horaires_texte', 'Non renseigné')}")
    if data.get('cabinet_fermeture_exception'):
        lines.append(f"Fermetures exceptionnelles: {data.get('cabinet_fermeture_exception')}")
    lines.append(f"Logiciel: {data.get('software_type', 'Non renseigné')}")

    # Praticiens
    if data.get('patient_prat'):
        lines.append(f"Praticien du patient: {data.get('patient_prat')}")
    if data.get('cabinet_prats'):
        lines.append(f"Praticiens du cabinet: {data.get('cabinet_prats')}")

    # Fonctionnalités disponibles
    lines.append(f"\n=== FONCTIONNALITÉS ===")
    lines.append(f"Confirmation RDV: {'Oui' if data.get('confirmation_rdv_enabled') else 'Non'}")
    lines.append(f"Annulation RDV: {'Oui' if data.get('annulation_rdv_enabled') else 'Non'}")
    lines.append(f"Prise de RDV: {'Oui' if data.get('prise_rdv_enabled') else 'Non'}")

    # Rendez-vous programmés
    appointments = data.get('scheduled_appointments', [])
    if appointments:
        lines.append(f"\n=== RENDEZ-VOUS PROGRAMMÉS ({len(appointments)}) ===")
        for i, appt in enumerate(appointments, 1):
            date = appt.get('date', 'Date inconnue')
            practitioner = appt.get('practitioner_id', 'Praticien inconnu')
            acte = appt.get('acte_id', 'Acte non précisé')
            lines.append(f"{i}. {date} - {practitioner} - {acte}")
    else:
        lines.append(f"\n=== RENDEZ-VOUS PROGRAMMÉS ===")
        lines.append("Aucun rendez-vous programmé")

    return "\n".join(lines)


def handle_initialize(request_id, params):
    """Gère la requête initialize (handshake MCP)"""
    client_version = params.get("protocolVersion", "unknown")
    client_info = params.get("clientInfo", {})
    logger.info(f"[MCP] initialize - Client: {client_info.get('name', 'unknown')} v{client_info.get('version', 'unknown')}, Protocol: {client_version}")

    return make_jsonrpc_response(request_id, {
        "protocolVersion": "2025-11-25",
        "capabilities": {
            "tools": {}
        },
        "serverInfo": {
            "name": "SanteCall MCP Proxy",
            "version": "1.2.0"
        }
    })


def handle_tools_list(request_id):
    """Gère la requête tools/list"""
    logger.info(f"[MCP] tools/list - Retourne {len(TOOLS)} outil(s)")
    return make_jsonrpc_response(request_id, {"tools": TOOLS})


def handle_tools_call(request_id, params):
    """Gère la requête tools/call"""
    tool_name = params.get("name")
    arguments = params.get("arguments", {})

    logger.info(f"[MCP] tools/call - Outil: {tool_name}, Arguments: {arguments}")

    if tool_name == "search_patient":
        phone = arguments.get("phone")
        if not phone:
            logger.warning(f"[MCP] search_patient - Numéro de téléphone manquant")
            return make_jsonrpc_response(request_id, {
                "content": [{"type": "text", "text": "Erreur: Le numéro de téléphone est requis."}],
                "isError": True
            })

        volubile_id = arguments.get("volubile_id")

        try:
            data = call_santecall_api(phone, volubile_id)
            formatted_response = format_patient_response(data)
            logger.info(f"[MCP] search_patient - Succès pour {phone}")

            return make_jsonrpc_response(request_id, {
                "content": [{"type": "text", "text": formatted_response}],
                "isError": False
            })
        except Exception as e:
            logger.error(f"[MCP] search_patient - Erreur: {str(e)}")
            return make_jsonrpc_response(request_id, {
                "content": [{"type": "text", "text": f"Erreur lors de la recherche: {str(e)}"}],
                "isError": True
            })
    else:
        logger.warning(f"[MCP] Outil inconnu: {tool_name}")
        return make_jsonrpc_error(request_id, -32602, f"Outil inconnu: {tool_name}")


@app.route("/", methods=["GET"])
def health():
    """Health check endpoint"""
    logger.info(f"[HTTP] GET / - Health check")
    return jsonify({
        "status": "ok",
        "service": "MCP Proxy SanteCall",
        "version": "1.2.0"
    })


@app.route("/", methods=["POST"])
@app.route("/mcp", methods=["POST"])
def mcp_endpoint():
    """
    Endpoint MCP principal - Reçoit les requêtes JSON-RPC 2.0
    Supporte: tools/list, tools/call
    """
    # Log de la requête entrante
    logger.info(f"[HTTP] POST /mcp - Requête reçue de {request.remote_addr}")
    logger.info(f"[HTTP] Headers: {dict(request.headers)}")

    try:
        data = request.get_json()
        logger.info(f"[HTTP] Body: {data}")

        if not data:
            logger.error(f"[HTTP] Erreur: JSON invalide")
            return jsonify(make_jsonrpc_error(None, -32700, "Parse error: Invalid JSON")), 400

        jsonrpc = data.get("jsonrpc")
        if jsonrpc != "2.0":
            logger.error(f"[HTTP] Erreur: jsonrpc != 2.0")
            return jsonify(make_jsonrpc_error(data.get("id"), -32600, "Invalid Request: jsonrpc must be '2.0'")), 400

        method = data.get("method")
        request_id = data.get("id")
        params = data.get("params", {})

        logger.info(f"[MCP] Méthode: {method}, ID: {request_id}")

        # Router vers le bon handler
        if method == "initialize":
            response = handle_initialize(request_id, params)
        elif method == "tools/list":
            response = handle_tools_list(request_id)
        elif method == "tools/call":
            response = handle_tools_call(request_id, params)
        elif method.startswith("notifications/"):
            # Les notifications MCP n'ont pas besoin de réponse
            logger.info(f"[MCP] Notification reçue: {method} (ignorée)")
            return "", 204  # No Content
        else:
            logger.warning(f"[MCP] Méthode inconnue: {method}")
            response = make_jsonrpc_error(request_id, -32601, f"Method not found: {method}")

        logger.info(f"[HTTP] Réponse envoyée")
        return jsonify(response)

    except Exception as e:
        logger.error(f"[HTTP] Erreur interne: {str(e)}")
        return jsonify(make_jsonrpc_error(None, -32603, f"Internal error: {str(e)}")), 500


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5002))
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"

    logger.info("=" * 50)
    logger.info("MCP Proxy SanteCall - Démarrage")
    logger.info("=" * 50)
    logger.info(f"Port: {port}")
    logger.info(f"Endpoint MCP: POST /mcp")
    logger.info(f"API SanteCall: {SANTECALL_API_URL}")
    logger.info(f"Debug: {debug}")
    logger.info("=" * 50)

    app.run(host="0.0.0.0", port=port, debug=debug)
