import sqlite3
import os
import base64
from datetime import datetime, timedelta
from crypto import hash_master_password, generate_salt, derive_aes_key, encrypt_password, decrypt_password

def get_db_connection():
    db_password = os.getenv('DB_PASSWORD', 'default_password')
    conn = sqlite3.connect('../db/data.sqlite')
    return conn

def init_db():
    os.makedirs('db', exist_ok=True)
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL
        )
    ''')
    
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
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS login_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            attempt_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            success INTEGER NOT NULL
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
        return False
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
    
    cursor.execute('SELECT id, salt FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()
    if not user:
        conn.close()
        return False
    
    user_id, stored_salt = user
    salt = base64.b64decode(stored_salt)
    
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
        return False

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

# NOUVELLE FONCTION: Modifier un mot de passe existant
def update_password(username, label, new_password, master_password):
    """Met à jour le mot de passe d'un label existant"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Vérifier que l'utilisateur et le label existent
    cursor.execute('''
        SELECT p.id 
        FROM passwords p 
        JOIN users u ON p.user_id = u.id 
        WHERE u.username = ? AND p.label = ?
    ''', (username, label))
    
    result = cursor.fetchone()
    if not result:
        conn.close()
        return False
    
    password_id = result[0]
    
    # Générer une nouvelle clé AES et chiffrer le nouveau mot de passe
    encryption_salt = generate_salt()
    aes_key = derive_aes_key(master_password, encryption_salt)
    encrypted_password = encrypt_password(new_password, aes_key)
    
    cursor.execute(
        'UPDATE passwords SET encrypted_password = ?, encryption_salt = ? WHERE id = ?',
        (encrypted_password.decode(), base64.b64encode(encryption_salt).decode(), password_id)
    )
    conn.commit()
    conn.close()
    return True

# NOUVELLE FONCTION: Vérifier si un mot de passe existe déjà pour un autre label
def check_password_reuse(username, new_password, master_password, exclude_label=None):
    """Vérifie si le mot de passe est déjà utilisé pour un autre label
    Retourne la liste des labels qui utilisent ce mot de passe"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT p.label, p.encrypted_password, p.encryption_salt 
        FROM passwords p 
        JOIN users u ON p.user_id = u.id 
        WHERE u.username = ?
    ''', (username,))
    
    results = cursor.fetchall()
    conn.close()
    
    duplicate_labels = []
    
    for label, encrypted_password, encryption_salt in results:
        # Exclure le label actuel si on modifie un mot de passe
        if exclude_label and label == exclude_label:
            continue
            
        encryption_salt = base64.b64decode(encryption_salt)
        aes_key = derive_aes_key(master_password, encryption_salt)
        stored_password = decrypt_password(encrypted_password, aes_key)
        
        if stored_password == new_password:
            duplicate_labels.append(label)
    
    return duplicate_labels

# NOUVELLE FONCTION: Supprimer un mot de passe (label)
def delete_password(username, label):
    """Supprime un mot de passe associé à un label"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        DELETE FROM passwords 
        WHERE user_id = (SELECT id FROM users WHERE username = ?) 
        AND label = ?
    ''', (username, label))
    
    rows_deleted = cursor.rowcount
    conn.commit()
    conn.close()
    
    return rows_deleted > 0

# NOUVELLE FONCTION: Supprimer un utilisateur et tous ses mots de passe
def delete_user(username):
    """Supprime un utilisateur et tous ses mots de passe associés"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Récupérer l'ID de l'utilisateur
        cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        
        if not user:
            conn.close()
            return False
        
        user_id = user[0]
        
        # Supprimer tous les mots de passe de l'utilisateur
        cursor.execute('DELETE FROM passwords WHERE user_id = ?', (user_id,))
        
        # Supprimer les tentatives de connexion
        cursor.execute('DELETE FROM login_attempts WHERE username = ?', (username,))
        
        # Supprimer l'utilisateur
        cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        conn.close()
        return False

# NOUVELLE FONCTION: Lister tous les utilisateurs
def list_all_users():
    """Récupère la liste de tous les utilisateurs"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT username FROM users ORDER BY username')
    users = cursor.fetchall()
    conn.close()
    
    return [user[0] for user in users]

# NOUVELLE FONCTION: Lister tous les labels d'un utilisateur
def list_user_labels(username):
    """Récupère tous les labels associés à un utilisateur"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT p.label 
        FROM passwords p 
        JOIN users u ON p.user_id = u.id 
        WHERE u.username = ?
        ORDER BY p.label
    ''', (username,))
    
    labels = cursor.fetchall()
    conn.close()
    
    return [label[0] for label in labels]

# NOUVELLE FONCTION: Obtenir toutes les données pour l'affichage tableau
def get_all_users_with_labels():
    """Récupère tous les utilisateurs avec leurs labels pour affichage en tableau"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT u.username, GROUP_CONCAT(p.label, ', ') as labels
        FROM users u
        LEFT JOIN passwords p ON u.id = p.user_id
        GROUP BY u.username
        ORDER BY u.username
    ''')
    
    results = cursor.fetchall()
    conn.close()
    
    return results

# NOUVELLE FONCTION: Vérifier si l'utilisateur est bloqué
def is_user_locked(username, max_attempts=3, lockout_duration_minutes=15):
    """Vérifie si l'utilisateur est temporairement bloqué après plusieurs tentatives échouées"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Calculer le moment à partir duquel les tentatives comptent
    lockout_time = datetime.now() - timedelta(minutes=lockout_duration_minutes)
    
    cursor.execute('''
        SELECT COUNT(*) 
        FROM login_attempts 
        WHERE username = ? 
        AND success = 0 
        AND attempt_time > ?
    ''', (username, lockout_time))
    
    failed_attempts = cursor.fetchone()[0]
    
    # Si l'utilisateur a atteint le max de tentatives, vérifier s'il est encore bloqué
    if failed_attempts >= max_attempts:
        cursor.execute('''
            SELECT attempt_time 
            FROM login_attempts 
            WHERE username = ? 
            AND success = 0 
            ORDER BY attempt_time DESC 
            LIMIT 1
        ''', (username,))
        
        last_attempt = cursor.fetchone()
        if last_attempt:
            last_attempt_time = datetime.strptime(last_attempt[0], '%Y-%m-%d %H:%M:%S')
            time_since_last = datetime.now() - last_attempt_time
            
            if time_since_last < timedelta(minutes=lockout_duration_minutes):
                remaining_time = timedelta(minutes=lockout_duration_minutes) - time_since_last
                conn.close()
                return True, int(remaining_time.total_seconds() / 60) + 1
    
    conn.close()
    return False, 0

# NOUVELLE FONCTION: Enregistrer une tentative de connexion
def record_login_attempt(username, success):
    """Enregistre une tentative de connexion (réussie ou échouée)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        'INSERT INTO login_attempts (username, attempt_time, success) VALUES (?, ?, ?)',
        (username, datetime.now(), 1 if success else 0)
    )
    conn.commit()
    conn.close()

# NOUVELLE FONCTION: Réinitialiser les tentatives après une connexion réussie
def reset_login_attempts(username):
    """Efface les tentatives échouées après une connexion réussie"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM login_attempts WHERE username = ? AND success = 0', (username,))
    conn.commit()
    conn.close()