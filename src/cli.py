import argparse
import getpass
import sys
from datetime import datetime
from database import init_db, register_user, verify_user, add_password, get_password, update_password, check_password_reuse, is_user_locked, record_login_attempt, reset_login_attempts, delete_password, delete_user, get_all_users_with_labels

class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

def print_banner():
    banner = f"""
{Colors.CYAN}{Colors.BOLD}
╔══════════════════════════════════════════════╗
║         -GESTIONNAIRE DE MOTS DE PASSE       ║
║         -PASSWORD MANAGER                    ║
╚══════════════════════════════════════════════╝
{Colors.END}
"""
    print(banner)

def print_success(message):
    print(f"{Colors.GREEN}✅ {message}{Colors.END}")

def print_error(message):
    print(f"{Colors.RED}❌ {message}{Colors.END}")

def print_info(message):
    print(f"{Colors.BLUE}ℹ️  {message}{Colors.END}")

def print_warning(message):
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.END}")

def print_password(label, password):
    print(f"\n{Colors.MAGENTA}{Colors.BOLD}🔐 Mot de passe trouvé :{Colors.END}")
    print(f"{Colors.CYAN}Label: {Colors.BOLD}{label}{Colors.END}")
    print(f"{Colors.GREEN}Mot de passe: {Colors.BOLD}{password}{Colors.END}\n")

def print_users_table(users_data):
    """Affiche un tableau formaté de tous les utilisateurs et leurs labels"""
    if not users_data:
        print_warning("Aucun utilisateur enregistré dans le système.")
        return
    
    print(f"\n{Colors.CYAN}{Colors.BOLD}📋 LISTE DES UTILISATEURS ET LEURS LABELS{Colors.END}\n")
    
    # Calculer les largeurs des colonnes
    max_username_length = max(len(user[0]) for user in users_data)
    max_username_length = max(max_username_length, len("UTILISATEUR"))
    
    max_labels_length = max(len(user[1] if user[1] else "Aucun") for user in users_data)
    max_labels_length = max(max_labels_length, len("LABELS"))
    
    # Limiter la largeur maximale pour les labels
    max_labels_length = min(max_labels_length, 80)
    
    # En-tête du tableau
    header_separator = "+" + "-" * (max_username_length + 2) + "+" + "-" * (max_labels_length + 2) + "+"
    
    print(f"{Colors.BOLD}{header_separator}{Colors.END}")
    print(f"{Colors.BOLD}| {'UTILISATEUR'.ljust(max_username_length)} | {'LABELS'.ljust(max_labels_length)} |{Colors.END}")
    print(f"{Colors.BOLD}{header_separator}{Colors.END}")
    
    # Lignes de données
    for username, labels in users_data:
        labels_display = labels if labels else "Aucun"
        
        # Si les labels sont trop longs, les couper sur plusieurs lignes
        if len(labels_display) > max_labels_length:
            # Première ligne
            print(f"| {Colors.CYAN}{username.ljust(max_username_length)}{Colors.END} | {Colors.GREEN}{labels_display[:max_labels_length]}{Colors.END} |")
            
            # Lignes suivantes
            remaining = labels_display[max_labels_length:]
            while remaining:
                chunk = remaining[:max_labels_length]
                remaining = remaining[max_labels_length:]
                print(f"| {' '.ljust(max_username_length)} | {Colors.GREEN}{chunk.ljust(max_labels_length)}{Colors.END} |")
        else:
            print(f"| {Colors.CYAN}{username.ljust(max_username_length)}{Colors.END} | {Colors.GREEN}{labels_display.ljust(max_labels_length)}{Colors.END} |")
    
    print(f"{Colors.BOLD}{header_separator}{Colors.END}")
    
    # Statistiques
    total_users = len(users_data)
    total_labels = sum(1 if user[1] else 0 for user in users_data)
    
    print(f"\n{Colors.BLUE}📊 Statistiques:{Colors.END}")
    print(f"  • Total d'utilisateurs: {Colors.BOLD}{total_users}{Colors.END}")
    print(f"  • Utilisateurs avec au moins un label: {Colors.BOLD}{total_labels}{Colors.END}\n")

def print_usage():
    usage = f"""
{Colors.YELLOW}{Colors.BOLD}UTILISATION:{Colors.END}

{Colors.CYAN}Inscription:{Colors.END}
  {Colors.WHITE}python main.py -r {Colors.BOLD}username{Colors.END}

{Colors.CYAN}Ajouter un mot de passe pour un Label:{Colors.END}
  {Colors.WHITE}python main.py -u {Colors.BOLD}username{Colors.END} -a {Colors.BOLD}label mot_de_passe{Colors.END}

{Colors.CYAN}Modifier un mot de passe existant:{Colors.END}
  {Colors.WHITE}python main.py -u {Colors.BOLD}username{Colors.END} -m {Colors.BOLD}label{Colors.END}

{Colors.CYAN}Afficher le mot de passe associé à un label quelconque:{Colors.END}
  {Colors.WHITE}python main.py -u {Colors.BOLD}username{Colors.END} -s {Colors.BOLD}label{Colors.END}

{Colors.CYAN}Supprimer un mot de passe (label):{Colors.END}
  {Colors.WHITE}python main.py -u {Colors.BOLD}username{Colors.END} -d {Colors.BOLD}label{Colors.END}

{Colors.CYAN}Supprimer un utilisateur et tous ses mots de passe:{Colors.END}
  {Colors.WHITE}python main.py -u {Colors.BOLD}username{Colors.END} --delete-user{Colors.END}

{Colors.CYAN}Lister tous les utilisateurs et leurs labels:{Colors.END}
  {Colors.WHITE}python main.py -l{Colors.END} ou {Colors.WHITE}python main.py --list{Colors.END}

{Colors.CYAN}Exemples:{Colors.END}
  {Colors.WHITE}python main.py -r john{Colors.END}
  {Colors.WHITE}python main.py -u john -a email MonSuperPass123{Colors.END}
  {Colors.WHITE}python main.py -u john -m email{Colors.END}
  {Colors.WHITE}python main.py -u john -s email{Colors.END}
  {Colors.WHITE}python main.py -u john -d email{Colors.END}
  {Colors.WHITE}python main.py -u john --delete-user{Colors.END}
  {Colors.WHITE}python main.py -l{Colors.END}
"""
    print(usage)

def confirm_password_input(prompt_text):
    """Demande à l'utilisateur de taper le mot de passe deux fois pour confirmation"""
    while True:
        password1 = getpass.getpass(f'{Colors.YELLOW}🔒 {prompt_text}: {Colors.END}')
        password2 = getpass.getpass(f'{Colors.YELLOW}🔒 Confirmez le mot de passe: {Colors.END}')
        
        if password1 == password2:
            return password1
        else:
            print_error("Les mots de passe ne correspondent pas. Réessayez.")

def check_and_warn_password_reuse(username, password, master_password, exclude_label=None):
    """Vérifie la réutilisation du mot de passe et demande confirmation"""
    duplicate_labels = check_password_reuse(username, password, master_password, exclude_label)
    
    if duplicate_labels:
        print_warning(f"ATTENTION: Ce mot de passe est déjà utilisé pour le(s) label(s): {', '.join(duplicate_labels)}")
        print_info("Réutiliser le même mot de passe pour plusieurs services diminue votre sécurité.")
        
        response = input(f"{Colors.YELLOW}Voulez-vous continuer quand même? (y/n): {Colors.END}").lower().strip()
        return response == 'y' or response == 'yes'
    
    return True

def verify_user_with_lockout(username, master_password):
    """Vérifie l'utilisateur avec protection contre les tentatives multiples"""
    # Vérifier si l'utilisateur est bloqué
    is_locked, remaining_minutes = is_user_locked(username)
    
    if is_locked:
        print_error(f"Compte temporairement bloqué! Réessayez dans {remaining_minutes} minute(s).")
        print_warning("Trop de tentatives de connexion échouées.")
        return False
    
    # Vérifier les credentials
    is_valid = verify_user(username, master_password)
    
    # Enregistrer la tentative
    record_login_attempt(username, is_valid)
    
    if is_valid:
        # Réinitialiser les tentatives échouées
        reset_login_attempts(username)
        return True
    else:
        # Compter combien de tentatives restent
        conn = get_db_connection()
        cursor = conn.cursor()
        from datetime import datetime, timedelta
        lockout_time = datetime.now() - timedelta(minutes=15)
        
        cursor.execute('''
            SELECT COUNT(*) 
            FROM login_attempts 
            WHERE username = ? 
            AND success = 0 
            AND attempt_time > ?
        ''', (username, lockout_time))
        
        failed_attempts = cursor.fetchone()[0]
        conn.close()
        
        remaining = 3 - failed_attempts
        if remaining > 0:
            print_warning(f"Il vous reste {remaining} tentative(s) avant le blocage du compte.")
        
        return False

def get_db_connection():
    """Importe la fonction depuis database.py"""
    import sqlite3
    conn = sqlite3.connect('../db/data.sqlite')
    return conn

def main():
    print_banner()
    init_db()
    
    parser = argparse.ArgumentParser(description='Password Manager - Gestion sécurisée des mots de passe', add_help=False)
    
    parser.add_argument('-r', '--register', metavar='USERNAME', help='Inscrire un nouvel utilisateur')
    parser.add_argument('-u', '--user', metavar='USERNAME', help="Nom d'utilisateur pour les opérations")
    parser.add_argument('-a', '--add', nargs=2, metavar=('LABEL', 'PASSWORD'), help='Ajouter un mot de passe: -a label mot_de_passe')
    parser.add_argument('-m', '--modify', metavar='LABEL', help='Modifier un mot de passe existant: -m label')
    parser.add_argument('-s', '--show', metavar='LABEL', help='Afficher un mot de passe: -s label')
    parser.add_argument('-d', '--delete', metavar='LABEL', help='Supprimer un mot de passe: -d label')
    parser.add_argument('--delete-user', action='store_true', help='Supprimer un utilisateur et tous ses mots de passe')
    parser.add_argument('-l', '--list', action='store_true', help='Lister tous les utilisateurs et leurs labels')
    parser.add_argument('-h', '--help', action='store_true', help="Afficher ce message d'aide")
    
    args = parser.parse_args()
    
    if args.help or len(sys.argv) == 1:
        print_usage()
        return
    
    # Mode inscription
    if args.register:
        print(f"\n{Colors.CYAN}{Colors.BOLD}📝 INSCRIPTION NOUVEL UTILISATEUR{Colors.END}")
        print(f"{Colors.WHITE}Utilisateur: {Colors.BOLD}{args.register}{Colors.END}")
        master_password = confirm_password_input(f'Entrez le master password pour {args.register}')
        
        if register_user(args.register, master_password):
            print_success(f"Utilisateur {args.register} inscrit avec succès!")
        else:
            print_error("Erreur: Cet utilisateur existe déjà!")
    
    # Mode ajout de mot de passe
    elif args.user and args.add:
        print(f"\n{Colors.CYAN}{Colors.BOLD}➕ AJOUT D'UN MOT DE PASSE{Colors.END}")
        print(f"{Colors.WHITE}Utilisateur: {Colors.BOLD}{args.user}{Colors.END}")
        label, password = args.add
        print(f"{Colors.WHITE}Label: {Colors.BOLD}{label}{Colors.END}")
        
        master_password = getpass.getpass(f'{Colors.YELLOW}🔒 Entrez le master password pour {args.user}: {Colors.END}')
        
        if verify_user_with_lockout(args.user, master_password):
            # Vérification de la réutilisation du mot de passe
            if check_and_warn_password_reuse(args.user, password, master_password):
                if add_password(args.user, label, password, master_password):
                    print_success(f"Mot de passe '{label}' sauvegardé avec succès!")
                else:
                    print_error("Erreur: Impossible de sauvegarder le mot de passe (label peut-être déjà utilisé)!")
            else:
                print_info("Opération annulée.")
        else:
            print_error("Erreur: Master password invalide ou utilisateur non trouvé!")
    
    # Mode modification de mot de passe
    elif args.user and args.modify:
        print(f"\n{Colors.CYAN}{Colors.BOLD}✏️  MODIFICATION D'UN MOT DE PASSE{Colors.END}")
        print(f"{Colors.WHITE}Utilisateur: {Colors.BOLD}{args.user}{Colors.END}")
        print(f"{Colors.WHITE}Label: {Colors.BOLD}{args.modify}{Colors.END}")
        
        master_password = getpass.getpass(f'{Colors.YELLOW}🔒 Entrez le master password pour {args.user}: {Colors.END}')
        
        if verify_user_with_lockout(args.user, master_password):
            # Vérifier que le label existe
            old_password = get_password(args.user, args.modify, master_password)
            if not old_password:
                print_error("Erreur: Aucun mot de passe trouvé pour ce label!")
                return
            
            print_info(f"Mot de passe actuel trouvé pour '{args.modify}'")
            new_password = confirm_password_input('Entrez le nouveau mot de passe')
            
            # Vérification de la réutilisation du mot de passe
            if check_and_warn_password_reuse(args.user, new_password, master_password, exclude_label=args.modify):
                if update_password(args.user, args.modify, new_password, master_password):
                    print_success(f"Mot de passe '{args.modify}' modifié avec succès!")
                else:
                    print_error("Erreur: Impossible de modifier le mot de passe!")
            else:
                print_info("Opération annulée.")
        else:
            print_error("Erreur: Master password invalide ou utilisateur non trouvé!")
    
    # Mode affichage de mot de passe
    elif args.user and args.show:
        print(f"\n{Colors.CYAN}{Colors.BOLD}🔍 RECHERCHE DE MOT DE PASSE{Colors.END}")
        print(f"{Colors.WHITE}Utilisateur: {Colors.BOLD}{args.user}{Colors.END}")
        print(f"{Colors.WHITE}Label: {Colors.BOLD}{args.show}{Colors.END}")
        
        master_password = getpass.getpass(f'{Colors.YELLOW}🔒 Entrez le master password pour {args.user}: {Colors.END}')
        
        if verify_user_with_lockout(args.user, master_password):
            password = get_password(args.user, args.show, master_password)
            if password:
                print_password(args.show, password)
            else:
                print_error("Erreur: Aucun mot de passe trouvé pour ce label!")
        else:
            print_error("Erreur: Master password invalide ou utilisateur non trouvé!")
    
    # Mode suppression de mot de passe (label)
    elif args.user and args.delete:
        print(f"\n{Colors.CYAN}{Colors.BOLD}🗑️  SUPPRESSION D'UN MOT DE PASSE{Colors.END}")
        print(f"{Colors.WHITE}Utilisateur: {Colors.BOLD}{args.user}{Colors.END}")
        print(f"{Colors.WHITE}Label: {Colors.BOLD}{args.delete}{Colors.END}")
        
        master_password = getpass.getpass(f'{Colors.YELLOW}🔒 Entrez le master password pour {args.user}: {Colors.END}')
        
        if verify_user_with_lockout(args.user, master_password):
            # Vérifier que le label existe
            password = get_password(args.user, args.delete, master_password)
            if not password:
                print_error("Erreur: Aucun mot de passe trouvé pour ce label!")
                return
            
            print_warning(f"Vous êtes sur le point de supprimer le mot de passe pour '{args.delete}'")
            confirmation = input(f"{Colors.YELLOW}Êtes-vous sûr? (y/n): {Colors.END}").lower().strip()
            
            if confirmation == 'y' or confirmation == 'yes':
                if delete_password(args.user, args.delete):
                    print_success(f"Mot de passe '{args.delete}' supprimé avec succès!")
                else:
                    print_error("Erreur: Impossible de supprimer le mot de passe!")
            else:
                print_info("Opération annulée.")
        else:
            print_error("Erreur: Master password invalide ou utilisateur non trouvé!")
    
    # Mode suppression d'utilisateur
    elif args.user and args.delete_user:
        print(f"\n{Colors.CYAN}{Colors.BOLD}⚠️  SUPPRESSION D'UTILISATEUR{Colors.END}")
        print(f"{Colors.WHITE}Utilisateur: {Colors.BOLD}{args.user}{Colors.END}")
        
        master_password = getpass.getpass(f'{Colors.YELLOW}🔒 Entrez le master password pour {args.user}: {Colors.END}')
        
        if verify_user_with_lockout(args.user, master_password):
            print_warning(f"ATTENTION: Vous êtes sur le point de supprimer l'utilisateur '{args.user}'")
            print_warning("Tous les mots de passe associés seront également supprimés!")
            print_warning("Cette action est IRRÉVERSIBLE!")
            
            confirmation = input(f"{Colors.RED}{Colors.BOLD}Tapez le nom d'utilisateur pour confirmer: {Colors.END}").strip()
            
            if confirmation == args.user:
                if delete_user(args.user):
                    print_success(f"Utilisateur '{args.user}' et tous ses mots de passe ont été supprimés!")
                else:
                    print_error("Erreur: Impossible de supprimer l'utilisateur!")
            else:
                print_info("Opération annulée (confirmation incorrecte).")
        else:
            print_error("Erreur: Master password invalide ou utilisateur non trouvé!")
    
    # Mode liste de tous les utilisateurs
    elif args.list:
        users_data = get_all_users_with_labels()
        print_users_table(users_data)
    
    else:
        print_error("Commande invalide!")
        print_usage()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}👋 Arrêt du programme. Au revoir!{Colors.END}")
    except Exception as e:
        print_error(f"Erreur inattendue: {str(e)}")