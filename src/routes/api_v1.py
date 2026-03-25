"""API v1 endpoints for PDF accessibility compliance"""
from flask import Blueprint, request, jsonify
from src.services.compliance import ComplianceService

api_v1_bp = Blueprint('api_v1', __name__)
compliance_service = ComplianceService()


@api_v1_bp.route('/scan', methods=['POST'])
def scan():
    """
    POST /api/v1/scan
    Scan PDF files for accessibility issues
    """
    try:
        data = request.get_json()
        
        if not data or 'fileUrls' not in data:
            return jsonify({"error": "fileUrls is required"}), 400
        
        file_urls = data['fileUrls']
        
        if not isinstance(file_urls, list) or len(file_urls) == 0:
            return jsonify({"error": "fileUrls must be a non-empty array"}), 400
        
        # Process the scan request
        result = compliance_service.scan_files(file_urls)
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_v1_bp.route('/remediate', methods=['POST'])
def remediate():
    """
    POST /api/v1/remediate
    Provide remediation guidance for accessibility issues
    """
    try:
        data = request.get_json()
        
        if not data or 'fileUrls' not in data:
            return jsonify({"error": "fileUrls is required"}), 400
        
        file_urls = data['fileUrls']
        
        if not isinstance(file_urls, list) or len(file_urls) == 0:
            return jsonify({"error": "fileUrls must be a non-empty array"}), 400
        
        # Process the remediation request
        result = compliance_service.remediate_files(file_urls)
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_v1_bp.route('/dashboard', methods=['POST'])
def dashboard():
    """
    POST /api/v1/dashboard
    Generate compliance dashboard for batch of files
    """
    try:
        data = request.get_json()
        
        if not data or 'fileUrls' not in data:
            return jsonify({"error": "fileUrls is required"}), 400
        
        file_urls = data['fileUrls']
        
        if not isinstance(file_urls, list) or len(file_urls) == 0:
            return jsonify({"error": "fileUrls must be a non-empty array"}), 400
        
        # Process the dashboard request
        result = compliance_service.generate_dashboard(file_urls)
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Made with Bob
