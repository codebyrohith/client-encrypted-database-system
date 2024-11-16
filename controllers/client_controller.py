from flask import Blueprint, request, jsonify
from helpers.ecc_encryption import ECCEncryption
from helpers.db_helpers import execute_query
from helpers.zkp_helper import ZKPAuthentication
import base64
from datetime import datetime
from config.database import get_db_connection

client_bp = Blueprint('client', __name__)

@client_bp.route('/register', methods=['POST'])
def register_client():
    data = request.json
    try:
        # Generate ECC key pair
        private_key, public_key = ECCEncryption.generate_key_pair()

        # Encrypt sensitive client data
        encrypted_name = ECCEncryption.encrypt_data(public_key, data["name"])
        encrypted_ssn = ECCEncryption.encrypt_data(public_key, data["ssn"])
        encrypted_address = ECCEncryption.encrypt_data(public_key, data["address"])

        # Insert client into the database
        query = """
        INSERT INTO clients (encrypted_name, encrypted_ssn, encrypted_address, public_key, created_at, last_accessed)
        OUTPUT INSERTED.id
        VALUES (?, ?, ?, ?, GETDATE(), GETDATE());
        """
        params = (encrypted_name, encrypted_ssn, encrypted_address, base64.b64encode(public_key).decode('utf-8'))
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        client_id = cursor.fetchone()[0]
        conn.commit()

        # Generate and store proof in the database
        zkp_auth = ZKPAuthentication()
        proof = zkp_auth.generate_proof(client_id, data["password"])

        # Return response
        return jsonify({
            "status": "success",
            "client_id": client_id,
            "private_key": private_key.secret.hex(),
            "proof": proof
        })
    except Exception as e:
        print(f"Error registering client: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        conn.close()




@client_bp.route('/<int:client_id>', methods=['GET'])
def get_client_by_id(client_id):
    """
    API to retrieve a client's decrypted data by their ID.
    Requires:
      - private_key: The ECC private key (hex string).
      - session_token: Valid session token from authentication.
    """
    private_key_hex = request.args.get("private_key")
    session_token = request.args.get("session_token")

    if not private_key_hex or not session_token:
        return jsonify({"status": "error", "message": "Missing private_key or session_token"}), 400

    conn = None
    try:
        # Open a single connection
        conn = get_db_connection()
        if not conn:
            raise Exception("Failed to connect to the database")

        cursor = conn.cursor()

        # Verify session token
        session_query = """
        SELECT client_id, expires_at
        FROM sessions
        WHERE session_token = ? AND client_id = ?;
        """
        cursor.execute(session_query, (session_token, client_id))
        session = cursor.fetchone()
        print(session)
        if not session or datetime.utcnow() > session[1]:
            return jsonify({"status": "error", "message": "Unauthorized access or session expired"}), 401

        # Fetch encrypted client data
        client_query = """
        SELECT encrypted_name, encrypted_ssn, encrypted_address, public_key, last_accessed
        FROM clients
        WHERE id = ?;
        """
        cursor.execute(client_query, (client_id,))
        client = cursor.fetchone()
        if not client:
            return jsonify({"status": "error", "message": "Client not found"}), 404

        encrypted_name, encrypted_ssn, encrypted_address, public_key, last_accessed = client

        # Convert private key from hex and decrypt data
        try:
            private_key = ECCEncryption.generate_key_pair()[0]
            private_key.secret = bytes.fromhex(private_key_hex)

            decrypted_data = {
                "name": ECCEncryption.decrypt_data(private_key, encrypted_name),
                "ssn": ECCEncryption.decrypt_data(private_key, encrypted_ssn),
                "address": ECCEncryption.decrypt_data(private_key, encrypted_address),
                "last_accessed": last_accessed.isoformat() if last_accessed else None
            }

            # Update last accessed timestamp
            update_query = "UPDATE clients SET last_accessed = GETDATE() WHERE id = ?;"
            cursor.execute(update_query, (client_id,))
            conn.commit()

            return jsonify({"status": "success", "data": decrypted_data})
        except Exception as e:
            print(f"Decryption failed: {e}")
            return jsonify({"status": "error", "message": "Decryption failed"}), 400

    except Exception as e:
        print(f"Error in get_client_by_id: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        if conn:
            conn.close()

