import spotipy
import json
import logging
from typing import List, Dict, Optional, Set
from datetime import datetime
import time
from utils import get_french_datetime

class SpotifySyncManager:
    """Gestionnaire principal pour la synchronisation entre deux comptes Spotify"""
    
    def __init__(self, source_client: spotipy.Spotify, target_client: spotipy.Spotify, config_path: str = "config.json"):
        self.source_client = source_client
        self.target_client = target_client
        self.config = self.load_config(config_path)
        self.logger = logging.getLogger(__name__)
        
        # Cache pour éviter les doublons
        self.synced_tracks = set()
        self.synced_playlists = set()
        
        # Compteurs pour la session actuelle
        self.session_synced_tracks = 0
        self.session_synced_playlists = 0
    
    def load_config(self, config_path: str) -> Dict:
        """Charge la configuration depuis le fichier JSON"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            self.logger.warning(f"Fichier de configuration {config_path} non trouvé, utilisation des valeurs par défaut")
            return self.get_default_config()
        except json.JSONDecodeError as e:
            self.logger.error(f"Erreur lors du parsing de la configuration: {e}")
            return self.get_default_config()
    
    def get_default_config(self) -> Dict:
        """Retourne la configuration par défaut"""
        return {
            "sync_settings": {
                "sync_liked_songs": True,
                "sync_playlists": True,
                "sync_interval_minutes": 30,
                "max_tracks_per_sync": 100
            },
            "playlist_settings": {
                "excluded_playlists": ["Discover Weekly", "Release Radar"],
                "create_copy_suffix": " (Copy)",
                "preserve_playlist_order": True,
                "sync_collaborative_playlists": False
            }
        }
    
    def get_liked_songs(self, client: spotipy.Spotify) -> List[Dict]:
        """Récupère toutes les chansons likées d'un compte"""
        liked_songs = []
        offset = 0
        limit = 50
        
        self.logger.info("Récupération des chansons likées...")
        
        while True:
            try:
                results = client.current_user_saved_tracks(limit=limit, offset=offset)
                
                if not results['items']:
                    break
                
                for item in results['items']:
                    track = item['track']
                    if track and track['id']:  # Vérifier que la track existe et a un ID
                        liked_songs.append({
                            'id': track['id'],
                            'name': track['name'],
                            'artists': [artist['name'] for artist in track['artists']],
                            'added_at': item['added_at']
                        })
                
                offset += limit
                
                # Respecter les limites de taux de l'API
                time.sleep(0.1)
                
            except Exception as e:
                self.logger.error(f"Erreur lors de la récupération des chansons likées: {e}")
                break
        
        # Inverser l'ordre pour préserver la chronologie originale
        # (API Spotify retourne les plus récentes en premier, on veut les plus anciennes d'abord)
        liked_songs.reverse()
        
        self.logger.info(f"Récupéré {len(liked_songs)} chansons likées (ordre chronologique préservé)")
        return liked_songs
    
    def sync_liked_songs(self) -> bool:
        """Synchronise les chansons likées du compte source vers le compte destination"""
        if not self.config['sync_settings']['sync_liked_songs']:
            self.logger.info("Synchronisation des chansons likées désactivée")
            return True
        
        try:
            self.logger.info("Début de la synchronisation des chansons likées")
            
            # Récupérer les chansons likées du compte source
            source_liked = self.get_liked_songs(self.source_client)
            
            # Récupérer les chansons déjà likées sur le compte destination
            target_liked = self.get_liked_songs(self.target_client)
            target_liked_ids = {song['id'] for song in target_liked}
            
            # Identifier les nouvelles chansons à liker
            new_tracks_to_like = []
            for track in source_liked:
                if track['id'] not in target_liked_ids and track['id'] not in self.synced_tracks:
                    new_tracks_to_like.append(track['id'])
            
            if not new_tracks_to_like:
                self.logger.info("Aucune nouvelle chanson à synchroniser")
                return True
            
            self.logger.info(f"Synchronisation de {len(new_tracks_to_like)} nouvelles chansons (une par une pour préserver l'ordre)")
            
            # Liker les chansons UNE PAR UNE pour préserver l'ordre chronologique exact
            for i, track_id in enumerate(new_tracks_to_like):
                success = False
                retry_count = 0
                max_retries = 3
                
                while not success and retry_count < max_retries:
                    try:
                        # Liker une seule chanson à la fois
                        self.target_client.current_user_saved_tracks_add(tracks=[track_id])
                        
                        # Marquer comme synchronisé
                        self.synced_tracks.add(track_id)
                        self.session_synced_tracks += 1  # Compter pour cette session
                        
                        self.logger.info(f"Chanson {i+1}/{len(new_tracks_to_like)} likée avec succès")
                        success = True
                        
                        # Pause optimisée pour éviter les timeouts
                        time.sleep(1)
                        
                    except Exception as e:
                        retry_count += 1
                        if retry_count < max_retries:
                            self.logger.warning(f"Erreur chanson {i+1} (tentative {retry_count}/{max_retries}): {e}")
                            self.logger.info(f"Retry dans 2 secondes...")
                            time.sleep(2.0)  # Pause plus longue avant retry
                        else:
                            self.logger.error(f"Échec définitif chanson {i+1} après {max_retries} tentatives: {e}")
                
                # Pas de pause - test de vitesse maximale
            
            self.logger.info("Synchronisation des chansons likées terminée avec succès")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la synchronisation des chansons likées: {e}")
            return False
    
    def get_playlists(self, client: spotipy.Spotify) -> List[Dict]:
        """Récupère toutes les playlists d'un utilisateur"""
        playlists = []
        offset = 0
        limit = 50
        
        self.logger.info("Récupération des playlists...")
        
        while True:
            try:
                results = client.current_user_playlists(limit=limit, offset=offset)
                
                if not results['items']:
                    break
                
                for playlist in results['items']:
                    # Filtrer les playlists exclues
                    if playlist['name'] not in self.config['playlist_settings']['excluded_playlists']:
                        # Filtrer les playlists collaboratives si désactivé
                        if not playlist['collaborative'] or self.config['playlist_settings']['sync_collaborative_playlists']:
                            playlists.append({
                                'id': playlist['id'],
                                'name': playlist['name'],
                                'description': playlist['description'],
                                'public': playlist['public'],
                                'collaborative': playlist['collaborative'],
                                'track_count': playlist['tracks']['total']
                            })
                
                offset += limit
                time.sleep(0.1)
                
            except Exception as e:
                self.logger.error(f"Erreur lors de la récupération des playlists: {e}")
                break
        
        self.logger.info(f"Récupéré {len(playlists)} playlists")
        return playlists
    
    def get_playlist_tracks(self, client: spotipy.Spotify, playlist_id: str) -> List[str]:
        """Récupère tous les IDs des tracks d'une playlist"""
        track_ids = []
        offset = 0
        limit = 100
        
        while True:
            try:
                results = client.playlist_tracks(playlist_id, limit=limit, offset=offset, fields="items(track(id))")
                
                if not results['items']:
                    break
                
                for item in results['items']:
                    if item['track'] and item['track']['id']:
                        track_ids.append(item['track']['id'])
                
                offset += limit
                time.sleep(0.1)
                
            except Exception as e:
                self.logger.error(f"Erreur lors de la récupération des tracks de la playlist: {e}")
                break
        
        return track_ids
    
    def create_playlist_copy(self, source_playlist: Dict) -> Optional[str]:
        """Crée une copie d'une playlist sur le compte destination"""
        try:
            # Obtenir l'ID de l'utilisateur destination
            user_info = self.target_client.current_user()
            user_id = user_info['id']
            
            # Créer le nom de la nouvelle playlist
            new_name = source_playlist['name'] + self.config['playlist_settings']['create_copy_suffix']
            
            # Créer la playlist
            new_playlist = self.target_client.user_playlist_create(
                user=user_id,
                name=new_name,
                public=source_playlist['public'],
                collaborative=False,  # Les copies ne sont pas collaboratives
                description=f"Copie automatique de: {source_playlist['name']} avec Spotify Sync"
            )
            
            return new_playlist['id']
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la création de la playlist '{source_playlist['name']}': {e}")
            return None
    
    def sync_playlists(self) -> bool:
        """Synchronise toutes les playlists du compte source vers le compte destination"""
        if not self.config['sync_settings']['sync_playlists']:
            self.logger.info("Synchronisation des playlists désactivée")
            return True
        
        try:
            self.logger.info("Début de la synchronisation des playlists")
            
            # Récupérer les playlists du compte source
            source_playlists = self.get_playlists(self.source_client)
            
            # Récupérer les playlists existantes sur le compte destination
            target_playlists = self.get_playlists(self.target_client)
            target_playlist_names = {pl['name'] for pl in target_playlists}
            
            synchronized_playlists = 0
            
            for source_playlist in source_playlists:
                playlist_copy_name = source_playlist['name'] + self.config['playlist_settings']['create_copy_suffix']
                
                # Vérifier si la playlist existe déjà
                if playlist_copy_name in target_playlist_names:
                    self.logger.info(f"Playlist '{playlist_copy_name}' existe déjà, passage à la suivante")
                    continue
                
                if source_playlist['id'] in self.synced_playlists:
                    continue
                
                self.logger.info(f"Synchronisation de la playlist: {source_playlist['name']}")
                
                # Créer la copie de la playlist
                new_playlist_id = self.create_playlist_copy(source_playlist)
                
                if not new_playlist_id:
                    continue
                
                # Récupérer les tracks de la playlist source
                track_ids = self.get_playlist_tracks(self.source_client, source_playlist['id'])
                
                if track_ids:
                    # Ajouter les tracks par lots de 100 (limite de l'API)
                    batch_size = 100
                    for i in range(0, len(track_ids), batch_size):
                        batch = track_ids[i:i + batch_size]
                        
                        try:
                            self.target_client.playlist_add_items(new_playlist_id, batch)
                            time.sleep(0.5)
                        except Exception as e:
                            self.logger.error(f"Erreur lors de l'ajout des tracks au lot {i//batch_size + 1}: {e}")
                            continue
                
                # Marquer comme synchronisé
                self.synced_playlists.add(source_playlist['id'])
                synchronized_playlists += 1
                self.session_synced_playlists += 1  # Compter pour cette session
                
                self.logger.info(f"Playlist '{source_playlist['name']}' synchronisée avec succès ({len(track_ids)} tracks)")
                
                # Pause entre les playlists
                time.sleep(1)
            
            self.logger.info(f"Synchronisation des playlists terminée: {synchronized_playlists} playlists synchronisées")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la synchronisation des playlists: {e}")
            return False
    
    def full_sync(self) -> bool:
        """Effectue une synchronisation complète (chansons likées + playlists)"""
        self.logger.info("Début de la synchronisation complète")
        
        start_time = get_french_datetime()
        
        # Synchroniser les chansons likées
        liked_songs_success = self.sync_liked_songs()
        
        # Synchroniser les playlists
        playlists_success = self.sync_playlists()
        
        end_time = get_french_datetime()
        duration = end_time - start_time
        
        success = liked_songs_success and playlists_success
        
        if success:
            self.logger.info(f"Synchronisation complète terminée avec succès en {duration}")
        else:
            self.logger.error(f"Synchronisation complète terminée avec des erreurs en {duration}")
        
        return success
    
    def reset_session_counters(self):
        """Remet à zéro les compteurs de la session actuelle"""
        self.session_synced_tracks = 0
        self.session_synced_playlists = 0
    
    def get_sync_stats(self) -> Dict:
        """Retourne des statistiques sur la dernière synchronisation"""
        return {
            'synced_tracks_count': self.session_synced_tracks,  # Nombre de cette session
            'synced_playlists_count': self.session_synced_playlists,  # Nombre de cette session
            'total_synced_tracks': len(self.synced_tracks),  # Total depuis le début
            'total_synced_playlists': len(self.synced_playlists),  # Total depuis le début
            'last_sync_time': get_french_datetime().strftime('%d/%m/%Y à %H:%M:%S')
        }
