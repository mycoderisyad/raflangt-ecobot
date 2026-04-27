"""Health / info endpoints."""

from flask import Blueprint, jsonify
from src.config import get_settings

health_bp = Blueprint("health", __name__)


@health_bp.route("/", methods=["GET"])
def index():
    cfg = get_settings().app
    return jsonify({
        "name": cfg.name,
        "version": cfg.version,
        "environment": cfg.environment,
        "status": "running",
    })


@health_bp.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy"})
