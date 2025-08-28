# EPIC CRM — CLI (Python)

Outil **CLI** de gestion CRM (utilisateurs, clients, contrats, événements) en Python.  
Interface en console via **Click** et affichages soignés (Rich).

## Aperçu

-   Authentification (login/logout)
    
-   Gestion **Users / Clients / Contracts / Events**
    
-   Filtres et listing
    
-   Journalisation/Audit avec **logging** + **Sentry**
    
-   Commandes simples, pensées pour un workflow développeur
    

----------

## Prérequis

-   **Python 3.10+**
    
-   `git`, `pip`, `virtualenv` (ou équivalent)
    

----------

## Installation

1.  **Cloner**

```bash
git clone https://github.com/AlBlanchard/epic_crm.git
cd epic_crm
```

2.  **Installer l'environnement virtuel**

```bash
python -m venv venv
```

3.  **Activer l'environnement virtuel**

- Sur **Linux/macOS**:

```bash
source venv/bin/activate
```

- Sur **Windows**:

```bash
.\venv\Scripts\activate
```

4.  **Installer les dépendances**

```bash
pip install -r requirements.txt
```


Problème d'interpreter dans VS Code :

Si certains imports de dépendances ne sont pas reconnus dans VS Code,
1.  Dand VS Code, appuyez sur Ctrl+Shift+P et sélectionnez "Python: Select Interpreter".
2.  Choisissez l'interpreter  .venv 
3.  Redémarrez VS Code si besoin
----------

## Configuration (.env)

Crée un fichier **.env** à la racine (non versionné) :

```dotenv
# Vos ID admin postgre, pour créer la DB
ADMIN_USER=<votre ID>
ADMIN_PASSWORD=<votre mdp>

# Configuration de la DB et création d'un utilisateur
DB_USER=<nom d'utilisateur>
DB_PASSWORD=<le mdp associé>
DB_HOST=<si local: localhost>
DB_PORT=<généralement 5432 si local>
DB_NAME=<nom de la DB>

# Configuration des tokens
JWT_SECRET_KEY=<votre clée secrète>
JWT_ALGORITHM=<algo des JWT, par ex. HS256, HS384, HS512>
JWT_ACCESS_TOKEN_EXPIRES=<durée en h (ex: 3h)>
JWT_REFRESH_TOKEN_EXPIRES=<durée en d (ex: 10d)>

# Sentry (facultatif mais recommandé)
SENTRY_DSN= https://<public_key>@sentry.io/<project_id>
```

> Si `SENTRY_DSN` est vide, Sentry est simplement désactivé (aucun crash).

----------

## Base de données (premier lancement)

Initialise le schéma / les données de départ :

```bash
python main.py init

```

Réinitialise entièrement la base (destructif) il faut être connecté comme admin :

```bash
python main.py reset-hard

```

----------

## Lancer l’application

Interface menu (mode interactif) :

```bash
python main.py

```

----------

## Commandes CLI (Click)

> Les commandes suivantes se lancent via `python main.py <commande>`.  
> Certaines acceptent des options/arguments (ajoutés plus tard).

### Auth

```text
login            # Se connecter
logout           # Se déconnecter

```

### Menu

```text
menu             # Ouvre le menu principal en console

```

### Users

```text
create-user
list-users
update-user
update-user-password
update-user-infos
delete-user
add-user-role
remove-user-role

```

### Clients

```text
create-client
list-clients
update-client
update-sales-contact
delete-client

```

### Contracts

```text
create-contract
list-contracts
sign-contract
update-contract-amount
delete-contract

```

### Events

```text
create-event
list-events
update-event
add-event-note
delete-note
update-support
delete-event

```

### Filtres

```text
filter

```

----------

## Journalisation & Sentry

Le projet s’intègre à **Sentry** pour :

-   **Exceptions non gérées** (via `sys.excepthook`) → issues Sentry
    
-   **Logs** (`logging`) :
    
    -   `INFO/WARNING` → **breadcrumbs** (contexte)
        
    -   `ERROR/CRITICAL` → **issues** Sentry (via `LoggingIntegration`)
        
-   **Événements métier** (audit) :
    
    -   `audit_breadcrumb(category, message, data)`
        
    -   `audit_event(message, data, level="info"|"warning"|"error"|...)`
        

> Les helpers Sentry/Audit sont centralisés (ex. `crm/utils/sentry_config.py`) et initialisés au démarrage.

----------