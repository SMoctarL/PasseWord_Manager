import argparse
import getpass
from dotenv import load_dotenv
import sys
from database import init_db, register_user, verify_user, add_password, get_password

def main():
    load_dotenv() # Charger les variables d'environnement depuis .env
    init_db()
    
    parser = argparse.ArgumentParser(description='Password Manager')
    
    # On va utiliser une approche différente pour éviter les conflits
    parser.add_argument('-r', '--register', metavar='USERNAME', help='Register new user')
    parser.add_argument('-u', '--user', metavar='USERNAME', help='Username for password operations')
    parser.add_argument('-a', '--add', nargs=2, metavar=('LABEL', 'PASSWORD'), help='Add password: -a label password')
    parser.add_argument('-s', '--show', metavar='LABEL', help='Show password: -s label')
    
    args = parser.parse_args()
    
    # Mode inscription
    if args.register:
        master_password = getpass.getpass(f'Enter {args.register} master password: ')
        if register_user(args.register, master_password):
            print(f"User {args.register} successfully registered!")
        else:
            print("Error: User already exists!")
    
    # Mode ajout de mot de passe
    elif args.user and args.add:
        master_password = getpass.getpass(f'Enter {args.user} master password: ')
        if verify_user(args.user, master_password):
            label, password = args.add
            if add_password(args.user, label, password, master_password):
                print(f"Password {label} successfully saved!")
            else:
                print("Error: Could not save password!")
        else:
            print("Error: Invalid master password or user not found!")
    
    # Mode affichage de mot de passe
    elif args.user and args.show:
        master_password = getpass.getpass(f'Enter {args.user} master password: ')
        if verify_user(args.user, master_password):
            password = get_password(args.user, args.show, master_password)
            if password:
                print(f"Password {args.show} is: {password}")
            else:
                print("Error: Label not found!")
        else:
            print("Error: Invalid master password or user not found!")
    
    else:
        print("Error: Invalid command. Use:")
        print("  -r USERNAME to register")
        print("  -u USERNAME -a LABEL PASSWORD to add password")
        print("  -u USERNAME -s LABEL to show password")

if __name__ == '__main__':
    main()