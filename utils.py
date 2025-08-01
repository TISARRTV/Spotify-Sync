"""
Utilitaires pour la synchronisation Spotify
"""

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
import os

# Timezone français (UTC+1 en hiver, UTC+2 en été)
FRENCH_TZ = timezone(timedelta(hours=1))  # Heure d'hiver, sera ajusté automatiquement

def get_french_datetime() -> datetime:
    """Retourne la date/heure actuelle en timezone français"""
    # Pour la France : UTC+1 en hiver, UTC+2 en été
    # Approximation simple : UTC+1 
    try:
        # Essayer d'utiliser zoneinfo pour Python 3.9+
        import zoneinfo
        french_tz = zoneinfo.ZoneInfo("Europe/Paris")
        return datetime.now(french_tz)
    except (ImportError, Exception):
        # Fallback pour Windows ou Python < 3.9
        # Utiliser UTC+1 comme approximation
        utc_now = datetime.utcnow()
        french_offset = timedelta(hours=1)  # Heure d'hiver
        return utc_now + french_offset

def format_french_datetime(dt: datetime = None) -> str:
    """Formate une date/heure au format français"""
    if dt is None:
        dt = get_french_datetime()
    return dt.strftime('%d/%m/%Y à %H:%M:%S')

def format_french_date(dt: datetime = None) -> str:
    """Formate une date au format français"""
    if dt is None:
        dt = get_french_datetime()
    return dt.strftime('%d/%m/%Y')

def format_french_time(dt: datetime = None) -> str:
    """Formate une heure au format français"""
    if dt is None:
        dt = get_french_datetime()
    return dt.strftime('%H:%M:%S')

class SyncLogger:
    """Logger spécialisé pour la synchronisation Spotify"""
    
    def __init__(self, log_file: str = "spotify_sync.log"):
        self.log_file = log_file
        self.setup_logger()
    
    def setup_logger(self):
        """Configure le logger"""
        self.logger = logging.getLogger("SpotifySync")
        self.logger.setLevel(logging.INFO)
        
        # Éviter les doublons de handlers
        if not self.logger.handlers:
            # Handler pour fichier
            file_handler = logging.FileHandler(self.log_file, encoding='utf-8')
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(file_formatter)
            
            # Handler pour console
            console_handler = logging.StreamHandler()
            console_formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(console_formatter)
            
            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)
    
    def info(self, message: str):
        """Log d'information"""
        self.logger.info(message)
    
    def error(self, message: str):
        """Log d'erreur"""
        self.logger.error(message)
    
    def warning(self, message: str):
        """Log d'avertissement"""
        self.logger.warning(message)

class ConfigManager:
    """Gestionnaire de configuration avancé"""
    
    def __init__(self, config_path: str = "config.json"):
        self.config_path = config_path
        self.config = self.load_config()
    
    def load_config(self) -> Dict:
        """Charge la configuration depuis le fichier"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return self.create_default_config()
        except json.JSONDecodeError:
            logging.error(f"Erreur de format dans {self.config_path}")
            return self.create_default_config()
    
    def create_default_config(self) -> Dict:
        """Crée une configuration par défaut"""
        default_config = {
            "sync_settings": {
                "sync_liked_songs": True,
                "sync_playlists": True,
                "sync_interval_minutes": 30,
                "max_tracks_per_sync": 1000,
                "batch_size": 50
            },
            "playlist_settings": {
                "excluded_playlists": [
                    "Discover Weekly",
                    "Release Radar",
                    "Daily Mix 1",
                    "Daily Mix 2",
                    "Daily Mix 3",
                    "Daily Mix 4",
                    "Daily Mix 5",
                    "Daily Mix 6"
                ],
                "create_copy_suffix": " (Sync)",
                "preserve_playlist_order": True,
                "sync_collaborative_playlists": False,
                "update_existing_playlists": True
            },
            "authentication": {
                "token_refresh_threshold_minutes": 30,
                "auto_refresh_tokens": True,
                "cache_tokens": True
            },
            "logging": {
                "level": "INFO",
                "file": "spotify_sync.log",
                "console_output": True,
                "max_log_size_mb": 10
            },
            "rate_limiting": {
                "requests_per_second": 10,
                "retry_attempts": 3,
                "retry_delay_seconds": 1
            }
        }
        
        # Sauvegarder la configuration par défaut
        self.save_config(default_config)
        return default_config
    
    def save_config(self, config: Dict):
        """Sauvegarde la configuration"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            logging.error(f"Erreur lors de la sauvegarde de la configuration: {e}")
    
    def get(self, key_path: str, default=None):
        """Récupère une valeur de configuration avec notation point"""
        keys = key_path.split('.')
        current = self.config
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        
        return current
    
    def set(self, key_path: str, value):
        """Définit une valeur de configuration avec notation point"""
        keys = key_path.split('.')
        current = self.config
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value
        self.save_config(self.config)

class SyncStats:
    """Gestionnaire de statistiques de synchronisation"""
    
    def __init__(self, stats_file: str = "sync_stats.json"):
        self.stats_file = stats_file
        self.stats = self.load_stats()
    
    def load_stats(self) -> Dict:
        """Charge les statistiques depuis le fichier"""
        try:
            with open(self.stats_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return self.create_default_stats()
        except json.JSONDecodeError:
            return self.create_default_stats()
    
    def create_default_stats(self) -> Dict:
        """Crée des statistiques par défaut"""
        return {
            "total_syncs": 0,
            "total_tracks_synced": 0,
            "total_playlists_synced": 0,
            "last_sync_date": None,
            "sync_history": [],
            "errors": []
        }
    
    def save_stats(self):
        """Sauvegarde les statistiques"""
        try:
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump(self.stats, f, indent=4, ensure_ascii=False)
        except Exception as e:
            logging.error(f"Erreur lors de la sauvegarde des statistiques: {e}")
    
    def record_sync(self, tracks_synced: int, playlists_synced: int, success: bool, duration: float):
        """Enregistre une synchronisation"""
        sync_record = {
            "date": get_french_datetime().isoformat(),
            "tracks_synced": tracks_synced,
            "playlists_synced": playlists_synced,
            "success": success,
            "duration_seconds": duration
        }
        
        self.stats["total_syncs"] += 1
        if success:
            self.stats["total_tracks_synced"] += tracks_synced
            self.stats["total_playlists_synced"] += playlists_synced
        
        self.stats["last_sync_date"] = sync_record["date"]
        self.stats["sync_history"].append(sync_record)
        
        # Garder seulement les 100 dernières synchronisations
        if len(self.stats["sync_history"]) > 100:
            self.stats["sync_history"] = self.stats["sync_history"][-100:]
        
        self.save_stats()
    
    def record_error(self, error_message: str, error_type: str = "general"):
        """Enregistre une erreur"""
        error_record = {
            "date": get_french_datetime().isoformat(),
            "type": error_type,
            "message": error_message
        }
        
        self.stats["errors"].append(error_record)
        
        # Garder seulement les 50 dernières erreurs
        if len(self.stats["errors"]) > 50:
            self.stats["errors"] = self.stats["errors"][-50:]
        
        self.save_stats()
    
    def get_summary(self) -> Dict:
        """Retourne un résumé des statistiques"""
        recent_syncs = [s for s in self.stats["sync_history"] 
                       if datetime.fromisoformat(s["date"]) > get_french_datetime() - timedelta(days=7)]
        
        successful_syncs = [s for s in recent_syncs if s["success"]]
        
        return {
            "total_syncs": self.stats["total_syncs"],
            "total_tracks_synced": self.stats["total_tracks_synced"],
            "total_playlists_synced": self.stats["total_playlists_synced"],
            "last_sync_date": self.stats["last_sync_date"],
            "recent_syncs_count": len(recent_syncs),
            "recent_success_rate": len(successful_syncs) / len(recent_syncs) * 100 if recent_syncs else 0,
            "recent_errors_count": len([e for e in self.stats["errors"] 
                                       if datetime.fromisoformat(e["date"]) > get_french_datetime() - timedelta(days=7)])
        }

def format_duration(seconds: float) -> str:
    """Formate une durée en secondes vers un format lisible"""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"

def validate_spotify_uri(uri: str) -> bool:
    """Valide un URI Spotify"""
    if not uri.startswith('spotify:'):
        return False
    
    parts = uri.split(':')
    if len(parts) != 3:
        return False
    
    valid_types = ['track', 'album', 'artist', 'playlist', 'user']
    return parts[1] in valid_types

def sanitize_playlist_name(name: str) -> str:
    """Nettoie le nom d'une playlist pour éviter les caractères problématiques"""
    # Caractères interdits dans les noms de playlist
    forbidden_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
    
    clean_name = name
    for char in forbidden_chars:
        clean_name = clean_name.replace(char, '_')
    
    # Limiter la longueur (Spotify limite à 100 caractères)
    if len(clean_name) > 95:  # Laisser de la place pour le suffixe
        clean_name = clean_name[:95]
    
    return clean_name.strip()

def chunk_list(lst: List, chunk_size: int) -> List[List]:
    """Divise une liste en chunks de taille donnée"""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]
