from helpers.db_helpers import execute_query
import hashlib
import os
from datetime import datetime, timedelta
from helpers.db_helpers import fetch_one, execute_query


class ZKPAuthentication:
    @staticmethod
    def generate_proof(client_id, password):
        """
        Generate a proof for the client using a challenge and password.
        Stores the challenge, proof, and expiry in the database.
        """
        challenge = os.urandom(32).hex()
        proof_input = (password + challenge).encode('utf-8')
        proof = hashlib.sha256(proof_input).hexdigest()

        # Store the challenge in the database
        query = """
        INSERT INTO challenges (client_id, challenge, proof, expires_at)
        VALUES (?, ?, ?, DATEADD(day, 1, GETDATE()));
        """
        execute_query(query, (client_id, challenge, proof))
        
        return proof



    @staticmethod
    def verify_proof(conn, client_id, proof, provided_password):
        """
        Verify the provided proof against the stored challenge.
        """
        try:
            cursor = conn.cursor()

            # Fetch the challenge and proof from the database
            query = """
            SELECT challenge, proof, expires_at
            FROM challenges
            WHERE client_id = ? AND proof = ?;
            """
            cursor.execute(query, (client_id, proof))
            result = cursor.fetchone()
            print("Here at verify proof 1")
            if not result:
                print("Here at verify proof 2")
                return False  # Challenge or proof not found

            challenge, stored_proof, expires_at = result
            if datetime.utcnow() > expires_at:
                print("Here at verify proof 2")
                return False  # Challenge expired

            # Recalculate the proof
            expected_proof_input = (provided_password + challenge).encode('utf-8')
            expected_proof = hashlib.sha256(expected_proof_input).hexdigest()

            # Clean up the used challenge
            delete_query = "DELETE FROM challenges WHERE proof = ?;"
            cursor.execute(delete_query, (proof,))
            conn.commit()

            return proof == expected_proof
        except Exception as e:
            print(f"Error in verify_proof: {e}")
            return False