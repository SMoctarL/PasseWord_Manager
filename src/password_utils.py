import re

def validate_password_strength(password):
    """
    Vérifie si le mot de passe respecte les critères de sécurité :
    - Au moins 8 caractères
    - Au moins un caractère spécial
    """
    if len(password) < 8:
        return False, "Le mot de passe doit contenir au moins 8 caractères."
    
    # Vérifier la présence d'un caractère spécial
    special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?/"
    if not any(char in special_chars for char in password):
        return False, "Le mot de passe doit contenir au moins un caractère spécial (!@#$%^&*()_+-=[]{}|;:,.<>?/)."
    
    return True, "Mot de passe valide."