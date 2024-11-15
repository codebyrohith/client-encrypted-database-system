from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from config.db import get_db_connection
from config.encryption import ECCEncryption
from zkp.zkp import ZKProof
from models import Client
import os
from datetime import datetime

# Database dependency
def get_db():
    conn = get_db_connection()
    try:
        yield conn.cursor()
    finally:
        conn.close()

# API Routes
@app.post("/register", response_model=dict)
async def register_client(
    client_data: dict,
    cursor: Session = Depends(get_db)
):
    # Generate ECC key pair
    private_key, public_key = ECCEncryption.generate_key_pair()
    
    # Encrypt sensitive data
    encrypted_name = ECCEncryption.encrypt_data(public_key, client_data["name"])
    encrypted_ssn = ECCEncryption.encrypt_data(public_key, client_data["ssn"])
    encrypted_address = ECCEncryption.encrypt_data(public_key, client_data["address"])
    
    # Generate ZKP proof
    zkp_auth = ZKProof()
    proof = zkp_auth.generate_proof(client_data["password"])
    
    # Create client record
    cursor.execute(
        "INSERT INTO clients (encrypted_name, encrypted_ssn, encrypted_address, public_key, created_at, last_accessed) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (encrypted_name, encrypted_ssn, encrypted_address, public_key.to_hex(), datetime.utcnow(), datetime.utcnow())
    )
    cursor.commit()
    
    return {
        "status": "success",
        "client_id": cursor.lastrowid,
        "private_key": private_key.to_hex(),  # Should be securely transmitted
        "proof": proof,
        "message": "Client registered successfully"
    }

@app.post("/authenticate", response_model=dict)
async def authenticate_client(
    auth_data: dict,
    cursor: Session = Depends(get_db)
):
    cursor.execute("SELECT id FROM clients WHERE id = ?", (auth_data["client_id"],))
    client = cursor.fetchone()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    zkp_auth = ZKProof()
    if not zkp_auth.verify_proof(auth_data["proof"], auth_data["password"]):
        raise HTTPException(status_code=401, detail="Authentication failed")
    
    cursor.execute(
        "UPDATE clients SET last_accessed = ? WHERE id = ?",
        (datetime.utcnow(), auth_data["client_id"])
    )
    cursor.commit()
    
    return {
        "status": "success",
        "message": "Authentication successful",
        "session_token": os.urandom(32).hex()  # Generate session token
    }

@app.get("/client/{client_id}", response_model=dict)
async def get_client_data(
    client_id: int,
    private_key_hex: str,
    session_token: str,
    cursor: Session = Depends(get_db)
):
    # Verify session token (implement proper session management in production)
    if not session_token:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    cursor.execute("SELECT * FROM clients WHERE id = ?", (client_id,))
    client = cursor.fetchone()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    try:
        private_key = ECCEncryption.generate_eth_key(bytes.fromhex(private_key_hex))
        decrypted_data = {
            "name": ECCEncryption.decrypt_data(private_key, client.encrypted_name),
            "ssn": ECCEncryption.decrypt_data(private_key, client.encrypted_ssn),
            "address": ECCEncryption.decrypt_data(private_key, client.encrypted_address),
            "last_accessed": client.last_accessed.isoformat()
        }
        
        cursor.execute(
            "UPDATE clients SET last_accessed = ? WHERE id = ?",
            (datetime.utcnow(), client_id)
        )
        cursor.commit()
        
        return {
            "status": "success",
            "data": decrypted_data
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail="Decryption failed")

# Additional utility endpoints
@app.get("/client/{client_id}/access-log")
async def get_access_log(client_id: int, cursor: Session = Depends(get_db)):
    cursor.execute("SELECT created_at, last_accessed FROM clients WHERE id = ?", (client_id,))
    client = cursor.fetchone()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    return {
        "created_at": client.created_at.isoformat(),
        "last_accessed": client.last_accessed.isoformat()
    }