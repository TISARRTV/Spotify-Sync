# Installation et Configuration - Spotify Transfer

Guide complet pour installer et configurer l'application de synchronisation Spotify.

## 📋 Prérequis

- **Python 3.7+** avec pip
- **Deux comptes Spotify** (source et destination) 
- **Accès développeur** au [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/)

## 🚀 Installation

### 1. Dépendances Python
```bash
# Dans le dossier du projet
pip install -r requirements.txt
```

### 2. Configuration Spotify Developer

#### Créer une application Spotify
1. Allez sur [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/)
2. Connectez-vous avec votre compte Spotify
3. Cliquez sur **"Create App"**

#### Configuration de l'application
- **App name** : `Spotify Sync`
- **App description** : `Application de synchronisation entre comptes Spotify`
- **Website** : `Vous pouvez laisser vide`
- **Redirect URIs** : **IMPORTANT**
  ```
  http://127.0.0.1:8888/callback
  http://127.0.0.1:8889/callback
  ```
- **APIs utilisées** : Spotify Web API
- **Cochez bien la case : I understand and agree with Spotify's Developer Terms of Service and Design Guidelines** 
- **Appuyez sur save**

#### Ajouter le second compte dans User Management
1. Dans votre app Spotify Developer Dashboard
2. Cliquez sur l'onglet **"User Management"**
3. **Ajoutez l'email du second compte Spotify** (le compte de destination)
4. Cliquez sur **"Add User"**

> ⚠️ **Important** : Cette étape est obligatoire pour que le second compte puisse s'authentifier avec votre application.

#### Récupérer les clés
1. Cliquez sur votre app dans le dashboard
2. Notez le **Client ID**
3. Cliquez sur **"View Client Secret"** → notez le **Client Secret**

### 3. Configuration locale

#### Créer le fichier `.env`
```bash
# Copier le template
cp .env.example .env
```

#### Éditer `.env` avec vos clés
```env
# UNE SEULE application Spotify suffit - utilise la même pour les deux comptes
SPOTIFY_CLIENT_ID=your_client_id_here
SPOTIFY_CLIENT_SECRET=your_client_secret_here

# URIs de redirection (utilisés automatiquement)
REDIRECT_URI=http://127.0.0.1:8888/callback

# Configuration optionnelle
SYNC_INTERVAL_MINUTES=30
LOG_LEVEL=INFO
```

## ✅ Vérification de l'installation

### Test rapide
```bash
# Vérifier la configuration
python main.py status

# Test complet avec simulation
python test_config.py
```

### Test d'authentification
```bash
# Mode simulation (aucune modification)
python main.py --dry-run
```

Lors du premier lancement :
1. **Navigateur s'ouvre automatiquement** pour le compte source
2. **Connectez-vous avec le compte qui CONTIENT vos musiques**
3. **Autorisez l'application** 
4. **Deuxième navigateur** s'ouvre pour le compte destination
5. **IMPORTANT** : Déconnectez-vous de Spotify dans le navigateur
6. **Connectez-vous avec le compte qui va RECEVOIR les musiques**
7. **Autorisez l'application**

### Vérification finale
```bash
# Vérifier l'ordre chronologique des likes
python check_order.py
```

## 🎯 Première synchronisation

### Test en simulation
```bash
# Test sans aucune modification
python main.py --dry-run
```

### Synchronisation réelle
```bash
# Synchronisation unique
python main.py

# Mode surveillance (continue)
python main.py --watch

# Avec intervalle personnalisé
python main.py --watch --interval 60
```

## ⚙️ Configuration avancée

### Fichier `config.json`
```json
{
  "sync_settings": {
    "sync_liked_songs": true,          // Synchroniser les likes
    "sync_playlists": false,           // Synchroniser les playlists
    "max_tracks_per_sync": 100,        // Limite par session
    "sync_interval_minutes": 30        // Fréquence mode surveillance
  },
  "playlist_settings": {
    "excluded_playlists": [            // Playlists ignorées
      "Discover Weekly",
      "Release Radar", 
      "Daily Mix"
    ],
    "create_copy_suffix": " (Copy)",   // Suffixe ajouté
    "preserve_playlist_order": true,   // Préserver l'ordre
    "sync_collaborative_playlists": false
  },
  "authentication": {
    "token_refresh_threshold_minutes": 30,
    "auto_refresh_tokens": true
  }
}
```

### Options en ligne de commande
```bash
# Aide complète
python main.py --help

# Configuration personnalisée
python main.py --config ma_config.json

# Mode simulation
python main.py --dry-run

# Mode surveillance avec intervalle
python main.py --watch --interval 60

# Commandes utilitaires
python main.py setup    # Assistant configuration
python main.py status   # Vérifier l'état
```

## 🔒 Sécurité

### Protection des clés
- **Fichier `.env`** exclu du contrôle de version (`.gitignore`)
- **Tokens OAuth** stockés localement dans `.cache_source` et `.cache_target`
- **Aucune transmission** vers des serveurs externes

### Permissions Spotify
- **Compte source** : `user-library-read`, `playlist-read-*` (lecture seule)
- **Compte destination** : `user-library-modify`, `playlist-modify-*` (écriture)
- **Principe du moindre privilège** : permissions minimales par compte

### Limitation des taux
- **Respect automatique** des limites de l'API Spotify
- **Retry intelligent** en cas d'erreur temporaire
- **Logs détaillés** pour traçabilité

## � Résolution de problèmes

### Erreur d'authentification
```
❌ Erreur d'authentification. Vérifiez votre configuration.
```
**Solutions** :
1. Vérifiez les clés dans `.env`
2. Vérifiez les URIs de redirection dans Spotify Dashboard
3. Supprimez `.cache_*` et recommencez

### Erreur de permissions (403)
```
403 Forbidden - Insufficient client scope
```
**Solution** :
1. Supprimez les fichiers `.cache_source` et `.cache_target`
2. Relancez l'authentification
3. Les nouvelles permissions seront appliquées

### Même compte détecté
**L'app détecte automatiquement** si vous utilisez le même compte pour source et destination et vous avertit.

### Ordre chronologique incorrect
```bash
# Vérifier l'ordre avec l'utilitaire dédié
python check_order.py
```

## 📞 Support

### Fichiers de diagnostic
- **Logs** : `spotify_sync.log`
- **Statistiques** : `sync_stats.json` 
- **Configuration** : `config.json`

### Utilitaires de debug
```bash
python test_config.py    # Test configuration complète
python check_order.py    # Vérification ordre chronologique  
python demo.py           # Démonstrations interactives
python main.py status    # État de la configuration
python cleanup.py        # ⚠️ Nettoyage complet d'un compte (DESTRUCTIF)
```

### Messages d'erreur courants
- **Variables d'environnement manquantes** → Vérifiez `.env`
- **Erreur réseau** → Vérifiez votre connexion internet
- **API rate limit** → L'app attend automatiquement et réessaie
- **Playlist non trouvée** → Vérifiez les exclusions dans `config.json`

## 🧹 Nettoyage d'un compte

### Script de nettoyage
Le script `cleanup.py` permet de remettre à zéro complètement un compte Spotify :

```bash
# Nettoyer complètement un compte (⚠️ DESTRUCTIF)
python cleanup.py
```

**⚠️ ATTENTION** : Ce script est **DESTRUCTIF** et **IRRÉVERSIBLE** !

### Options de nettoyage
1. **Supprimer uniquement les playlists** - Supprime toutes vos playlists
2. **Unlike uniquement les chansons** - Unlike tous vos titres likés  
3. **Nettoyage complet** - Supprime playlists ET unlike tous les titres
4. **Annuler** - Annule l'opération

### Cas d'usage
- **Recommencer une synchronisation** depuis zéro
- **Nettoyer un compte de test** après des expérimentations
- **Corriger des erreurs** de synchronisation précédentes

### Sécurités intégrées
- **Double confirmation** obligatoire avant exécution
- **Affichage du compte** concerné pour éviter les erreurs
- **Progression détaillée** avec compteurs
- **Gestion d'erreurs** robuste

L'application est conçue pour être robuste et gérer automatiquement la plupart des erreurs courantes.