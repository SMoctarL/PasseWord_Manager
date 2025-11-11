# 🔐 Password Manager 
Un **gestionnaire de mots de passe en ligne de commande** (CLI) développé en **Python**, utilisant **SQLite** pour le stockage et **AES-256** pour le chiffrement des mots de passe.  
Le but est de comprendre les bases de la **cryptographie appliquée**, de la **gestion sécurisée des utilisateurs** et de la **protection des données sensibles**.

---

## 📁 Structure du projet

```
password-manager/
├── db/
│   └── data.sqlite          # Base de données SQLite
└── src/
    ├── .env.example         # Exemple de configuration d'environnement
    ├── cli.py               # Interface en ligne de commande
    ├── crypto.py            # Fonctions de chiffrement et dérivation de clés
    ├── database.py          # Gestion de la base de données SQLite
    ├── main.py              # Point d'entrée principal du programme
    ├── requirements.txt     # Dépendances Python
    └── __pycache__/         # Cache Python (auto-généré)

```

---

## ⚙️ Installation

### 1️⃣ Cloner le projet
```bash
https://github.com/SMoctarL/PasseWord_Manager.git
cd password-manager/src
```

### 2️⃣ Créer un environnement virtuel
```bash
python -m venv venv
source venv/bin/activate   # Linux / Mac
venv\Scripts\activate      # Windows
```

### 3️⃣ Installer les dépendances
```bash
pip install -r requirements.txt
```

### 4️⃣ Créer la base de données
```bash
python main.py
```

---

## 🚀 Utilisation

### 🧍 Enregistrer un utilisateur
```bash
python main.py -r <USERNAME>
```

### ➕ Ajouter un mot de passe
```bash
python main.py -u <USERNAME> -a <LABEL> <PASSWORD>
```

### 🔍 Afficher un mot de passe
```bash
python main.py -u <USERNAME> -s <LABEL>
```

---

## 🧠 Fonctionnement interne

| Module | Rôle |
|--------|------|
| **crypto.py** | Gère le chiffrement AES-256 (CBC) et la dérivation de clé PBKDF2. |
| **database.py** | Initialise et gère la base SQLite. Stocke les utilisateurs et mots de passe chiffrés. |
| **cli.py** | Fournit l’interface utilisateur via la ligne de commande (argparse). |
| **main.py** | Point d’entrée du programme, relie tout le système. |

---

## 🔒 Sécurité intégrée

- 🔑 **Hachage SHA-256** du mot de passe maître (avec salt unique).
- 🔐 **Chiffrement AES-256 (CBC)** des mots de passe stockés.
- 🧂 **Salt aléatoire** généré pour chaque utilisateur et mot de passe.
- 🚫 Aucun mot de passe en clair n’est stocké dans la base de données.

---

## 👨‍💻 Auteur

**Sidy Moctar LO**  
💼 Étudiant en informatique — Passionné par la cybersécurité, l’intelligence artificielle et l’automatisation.
