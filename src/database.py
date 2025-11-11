import sqlite3
import os
import base64
from crypto import hash_master_password, generate_salt, derive_aes_key, encrypt_password, decrypt_password

def get_db_connection():
    db_password = os.getenv('DB_PASSWORD', 'default_password')
    conn = sqlite3.connect('../db/data.sqlite')
    # Pour chiffrer la BD SQLite, on utiliserait normalement SQLCipher mais ici on simule juste l'ouverture avec un mot de passe
    return conn

def init_db():
    os.makedirs('db', exist_ok=True)
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Table utilisateurs
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL
        )
    ''')
    
    # Table mots de passe
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS passwords (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            label TEXT NOT NULL,
            encrypted_password TEXT NOT NULL,
            encryption_salt TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id),
            UNIQUE(user_id, label)
        )
    ''')
    
    conn.commit()
    conn.close()

def register_user(username, master_password):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    salt = generate_salt()
    password_hash = hash_master_password(master_password, salt)
    
    try:
        cursor.execute(
            'INSERT INTO users (username, password_hash, salt) VALUES (?, ?, ?)',
            (username, password_hash.decode(), base64.b64encode(salt).decode())
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False  # Utilisateur existe déjà
    finally:
        conn.close()

def verify_user(username, master_password):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT password_hash, salt FROM users WHERE username = ?', (username,))
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        return False
    
    stored_hash, stored_salt = result
    salt = base64.b64decode(stored_salt)
    computed_hash = hash_master_password(master_password, salt)
    
    return computed_hash.decode() == stored_hash

def add_password(username, label, password, master_password):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Récupérer le user_id et le salt de l'utilisateur
    cursor.execute('SELECT id, salt FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()
    if not user:
        conn.close()
        return False
    
    user_id, stored_salt = user
    salt = base64.b64decode(stored_salt)  # Décode le salt depuis la base64
    
    # Générer une clé AES et chiffrer le mot de passe
    encryption_salt = generate_salt()
    aes_key = derive_aes_key(master_password, encryption_salt)
    encrypted_password = encrypt_password(password, aes_key)
    
    try:
        cursor.execute(
            'INSERT INTO passwords (user_id, label, encrypted_password, encryption_salt) VALUES (?, ?, ?, ?)',
            (user_id, label, encrypted_password.decode(), base64.b64encode(encryption_salt).decode())
        )
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False  # Label déjà existant pour cet utilisateur

def get_password(username, label, master_password):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT p.encrypted_password, p.encryption_salt 
        FROM passwords p 
        JOIN users u ON p.user_id = u.id 
        WHERE u.username = ? AND p.label = ?
    ''', (username, label))
    
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        return None
    
    encrypted_password, encryption_salt = result
    encryption_salt = base64.b64decode(encryption_salt)
    aes_key = derive_aes_key(master_password, encryption_salt)
    
    return decrypt_password(encrypted_password, aes_key)