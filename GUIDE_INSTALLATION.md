
# 🤖 Guide d'Installation - Bot Discord de Jeu de Rôle

## 📋 Prérequis

- Python 3.8 ou plus récent
- Un compte Discord
- Un serveur Discord où vous avez les permissions d'administrateur

## 🛠️ Installation

### 1. Préparer l'environnement

```bash
# Cloner ou télécharger les fichiers
mkdir mon-bot-discord
cd mon-bot-discord

# Installer les dépendances
pip install discord.py>=2.0.0 python-dotenv aiosqlite
```

### 2. Créer le bot sur Discord

1. Allez sur https://discord.com/developers/applications
2. Cliquez sur "New Application"
3. Donnez un nom à votre bot
4. Allez dans l'onglet "Bot" 
5. Cliquez sur "Add Bot"
6. Copiez le token (gardez-le secret!)

### 3. Configurer les permissions

Dans l'onglet "OAuth2" > "URL Generator":
- Sélectionnez "bot" et "applications.commands"
- Permissions requises:
  - Send Messages
  - Read Message History
  - Manage Roles
  - Use Slash Commands
  - View Channels

### 4. Inviter le bot sur votre serveur

1. Copiez l'URL générée
2. Ouvrez-la dans votre navigateur
3. Sélectionnez votre serveur
4. Autorisez le bot

### 5. Créer les rôles d'ancienneté

Sur votre serveur Discord, créez ces rôles (respectez l'orthographe exacte):
- `newcomer`
- `rising` 
- `yapper`
- `go outside touch some grass`

**Important**: Le rôle du bot doit être au-dessus de ces rôles dans la hiérarchie!

### 6. Configurer le code

1. Remplacez `"VOTRE_TOKEN_ICI"` par votre vrai token dans le fichier .py
2. Ou créez un fichier `.env` :

```
DISCORD_TOKEN=votre_token_ici
```

Et modifiez le code pour utiliser :
```python
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
```

### 7. Lancer le bot

```bash
python bot_discord_roleplay_complet.py
```

## 🎮 Utilisation

### Commandes disponibles:

#### 📊 Système de Niveaux
- `/niveau` - Voir votre niveau et XP
- `/classement` - Classement du serveur

#### 🎭 Personnages
- `/creer_personnage <nom>` - Créer un nouveau personnage
- `/mes_personnages` - Liste de vos personnages  
- `/stats_personnage <nom>` - Statistiques détaillées
- `/entrainer <nom> <statistique>` - Entraîner une statistique
- `/supprimer_personnage <nom>` - Supprimer un personnage

#### 🛡️ Administration
- `/admin_reset_user <utilisateur>` - Remettre à zéro un utilisateur (Admin seulement)

## 🔧 Fonctionnalités

### Système d'Ancienneté
- **XP automatique**: 3-5 points par message
- **Formule de progression**: p(1)=200, p(n+1)=p(n)×1.4
- **Rôles automatiques** tous les 10 niveaux

### Système de Personnages
- **10 spécialités** avec bonus uniques
- **7 statistiques** par personnage
- **Entraînement** avec gains d'XP variables
- **Limites** basées sur l'ancienneté

### Spécialités et Bonus

| Spécialité | Bonus |
|------------|-------|
| Chanteur | Chant niveau 3 |
| Danseur | Danse niveau 3 |
| Acteur | Acting niveau 3 |
| Reporter | Éloquence niveau 3 |
| Coach | Fitness niveau 3 |
| Mannequin | Esthétique niveau 3 |
| Étudiant | +10% XP entraînement |
| Professeur | Stat niveau 2 + 5% XP |
| Influenceur | Réputation 1000 |
| Autre | Spécialité personnalisée |

## 🐛 Dépannage

### Le bot ne répond pas
- Vérifiez que le token est correct
- Vérifiez les permissions du bot
- Regardez les logs dans la console

### Les rôles ne sont pas attribués
- Vérifiez que les rôles existent avec la bonne orthographe
- Le rôle du bot doit être au-dessus des autres rôles
- Vérifiez les permissions "Manage Roles"

### Les commandes slash n'apparaissent pas
- Attendez quelques minutes après le démarrage
- Réinvitez le bot avec les bonnes permissions
- Redémarrez Discord

## 📁 Structure des Fichiers

```
mon-bot-discord/
├── bot_discord_roleplay_complet.py  # Code principal
├── bot_database.db                  # Base de données (auto-créé)
├── requirements.txt                 # Dépendances
├── .env                            # Configuration (optionnel)
└── README.md                       # Ce guide
```

## 🔒 Sécurité

- Ne partagez JAMAIS votre token Discord
- Utilisez un fichier .env pour les secrets
- Ajoutez .env à votre .gitignore
- Régénérez le token si compromis

## 🚀 Améliorations Possibles

- Interface web d'administration
- Système de quêtes pour les personnages
- Événements programmés
- Intégration avec d'autres bots
- Système de guildes/équipes

## 📞 Support

En cas de problème:
1. Vérifiez ce guide
2. Consultez les logs d'erreur
3. Vérifiez la documentation Discord.py
4. Demandez de l'aide sur les forums Discord

Bon jeu de rôle! 🎭✨
