# Spotify Transfer - Synchronisation de comptes Spotify

Application qui synchronise automatiquement les chansons likées et playlists entre deux comptes Spotify différents, en préservant l'ordre chronologique exact.

## 🎯 Fonctionnalités principales

### Synchronisation des likes
- **Ordre chronologique préservé** : Les chansons sont likées une par une dans l'ordre exact d'origine
- **Synchronisation intelligente** : Détecte automatiquement les nouvelles chansons à synchroniser  
- **Gestion des erreurs** : Système de retry automatique en cas de problème réseau

### Synchronisation des playlists
- **Recréation complète** : Toutes les playlists sont copiées avec leur contenu
- **Exclusions configurables** : Ignorer automatiquement "Discover Weekly", "Release Radar", etc.
- **Préservation des métadonnées** : Description, ordre des tracks, etc.

### Modes d'exécution
- **Synchronisation unique** : `python main.py`
- **Mode surveillance** : `python main.py --watch` (surveille et synchronise automatiquement)
- **Mode simulation** : `python main.py --dry-run` (teste sans modifications)

## 🏗️ Architecture technique

### Authentification sécurisée
- **Compte source** : Permissions de lecture uniquement (`user-library-read`, `playlist-read-*`)
- **Compte destination** : Permissions complètes (`user-library-modify`, `playlist-modify-*`)
- **OAuth 2.0** : Deux ports différents (8888/8889) pour éviter les conflits entre comptes

### Préservation de l'ordre chronologique
- **API inversée** : L'API Spotify retourne les plus récents d'abord, l'application inverse pour obtenir l'ordre chronologique
- **Synchronisation séquentielle** : Une chanson likée à la fois pour garantir l'ordre exact
- **Validation intégrée** : Script de vérification pour confirmer que l'ordre est respecté

## 🚀 Installation et démarrage

**Installation complète** : Voir [INSTALLATION.md](INSTALLATION.md) pour le guide détaillé.

### Démarrage rapide
```bash
# 1. Installer les dépendances
pip install -r requirements.txt

# 2. Créer et configurer .env
cp .env.example .env
# Éditez .env avec vos clés Spotify Developer

# 3. Tester la configuration
python test_config.py

# 4. Premier test en simulation
python main.py --dry-run

# 5. Synchronisation réelle
python main.py
```

## 🔧 Utilitaires disponibles

| Script | Description | Usage |
|--------|-------------|-------|
| `main.py` | Application principale | `python main.py [options]` |
| `check_order.py` | Vérifie l'ordre chronologique des likes | `python check_order.py` |
| `test_config.py` | Teste configuration et authentification | `python test_config.py` |
| `demo.py` | Démonstrations interactives | `python demo.py` |
| `cleanup.py` | **⚠️ Nettoie complètement un compte** | `python cleanup.py` |

### Commandes principales
```bash
# Synchronisation complète
python main.py

# Mode surveillance continue
python main.py --watch

# Vérifier la configuration
python main.py status

# Assistant de configuration
python main.py setup

# Vérifier l'ordre chronologique
python check_order.py

# Nettoyer complètement un compte (⚠️ DESTRUCTIF)
python cleanup.py

# Voir toutes les options
python main.py --help
```

## ⚙️ Configuration

Le fichier `config.json` permet de personnaliser le comportement :

```json
{
  "sync_settings": {
    "sync_liked_songs": true,        // Synchroniser les likes
    "sync_playlists": false,         // Synchroniser les playlists  
    "max_tracks_per_sync": 100,      // Limite par session
    "sync_interval_minutes": 30      // Fréquence mode surveillance
  },
  "playlist_settings": {
    "excluded_playlists": ["Discover Weekly", "Release Radar", "Daily Mix"],
    "create_copy_suffix": " (Copy)",
    "sync_collaborative_playlists": false
  }
}
```

## 🔒 Sécurité et confidentialité

- **OAuth 2.0** : Authentification sécurisée, aucun mot de passe stocké
- **Stockage local uniquement** : Tokens et données restent sur votre machine
- **Permissions minimales** : Scopes strictement nécessaires par compte
- **Protection des données** : Fichiers sensibles exclus du contrôle de version

## 📊 Monitoring et diagnostic

- **Logs détaillés** : `spotify_sync.log` avec horodatage français
- **Statistiques** : `sync_stats.json` pour suivre les performances  
- **Scripts de validation** : Vérification automatique de l'intégrité

L'application respecte les limitations de l'API Spotify et gère automatiquement les erreurs et timeouts.
