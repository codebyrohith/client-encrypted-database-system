from flask import Blueprint, request, jsonify
from helpers.zkp_helper import ZKPAuthentication
from config.database import get_db_connection
import os
from datetime import datetime

# Define Blueprint
auth_bp = Blueprint('auth', __name__)

# Authentication route
@auth_bp.route('/authenticate', methods=['POST'])
def authenticate_client():
    data = request.json
    conn = None
    try:
        conn = get_db_connection()
        if not conn:
            raise Exception("Failed to connect to the database")
        print("Database connection successful")

        cursor = conn.cursor()

        # Fetch client by ID
        query = "SELECT id FROM clients WHERE id = ?;"
        print("Executing query to fetch client")
        cursor.execute(query, (data["client_id"]))
        client = cursor.fetchone()
        if not client:
            return jsonify({"status": "error", "message": "Client not found"}), 404

        # Verify ZKP proof
        zkp_auth = ZKPAuthentication()
        if not zkp_auth.verify_proof(conn, data["client_id"], data["proof"], data["password"]):
            print("Proof verification failed")
            return jsonify({"status": "error", "message": "Authentication failed"}), 401

        # Generate session token
        session_token = os.urandom(32).hex()
        query = """
        INSERT INTO sessions (client_id, session_token, expires_at)
        VALUES (?, ?, DATEADD(day, 1, GETDATE()));  -- Expiry increased to 1 day
        """
        cursor.execute(query, (client[0], session_token))
        conn.commit()

        print("Session token inserted successfully")
        return jsonify({"status": "success", "session_token": session_token})
    except Exception as e:
        print(f"Error in authenticate_client: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        if conn:
            conn.close()
            print("Database connection closed")
