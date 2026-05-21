from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from chatbot.chatbot_service import ChatbotService

chatbot_bp = Blueprint("chatbot", __name__, url_prefix="/api/chatbot")


@chatbot_bp.route("/query", methods=["POST"])
@jwt_required()
def chatbot_query():
    user_id = int(get_jwt_identity())
    data = request.get_json()

    if not data or "query" not in data:
        return jsonify({"error": "Query is required"}), 400

    service = ChatbotService()
    result = service.process_query(data["query"], user_id)

    return jsonify(result), 200
