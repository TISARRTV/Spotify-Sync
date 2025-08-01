import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
import json
import logging
from typing import Optional, Dict, List
from dotenv import load_dotenv
from utils import format_french_datetime

class SpotifyAuthManager:
    """Gestionnaire d'authentification pour les comptes Spotify"""
    
    def __init__(self):
        load_dotenv()
        self.setup_logging()
        self.accounts_file = ".spotify_accounts.json"
        
    def setup_logging(self):
        """Configure le système de logging"""
        # Configuration personnalisée avec format français
        class FrenchFormatter(logging.Formatter):
            def formatTime(self, record, datefmt=None):
                from datetime import datetime
                ct = datetime.fromtimestamp(record.created)
                return format_french_datetime(ct)
        
        # Créer un formatter français
        french_formatter = FrenchFormatter('%(asctime)s - %(levelname)s - %(message)s')
        
        # Configuration du logging avec format français
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('spotify_sync.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        
        # Appliquer le formatter français aux handlers existants
        logger = logging.getLogger()
        for handler in logger.handlers:
            handler.setFormatter(french_formatter)
            
        self.logger = logging.getLogger(__name__)
    
    def save_account_info(self, account_type: str, user_info: dict):
        """Sauvegarde les informations du compte connecté"""
        try:
            accounts_data = {}
            if os.path.exists(self.accounts_file):
                with open(self.accounts_file, 'r', encoding='utf-8') as f:
                    accounts_data = json.load(f)
            
            accounts_data[account_type] = {
                'display_name': user_info.get('display_name', 'Inconnu'),
                'id': user_info.get('id', ''),
                'email': user_info.get('email', ''),
                'last_connected': user_info.get('id', '')
            }
            
            with open(self.accounts_file, 'w', encoding='utf-8') as f:
                json.dump(accounts_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self.logger.warning(f"Impossible de sauvegarder les infos du compte: {e}")
    
    def load_account_info(self) -> dict:
        """Charge les informations des comptes sauvegardés"""
        try:
            if os.path.exists(self.accounts_file):
                with open(self.accounts_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.warning(f"Impossible de charger les infos des comptes: {e}")
        return {}
    
    def authenticate_source_account(self) -> Optional[spotipy.Spotify]:
        """Authentifie le compte Spotify source"""
        try:
            client_id = os.getenv('SPOTIFY_CLIENT_ID')
            client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
            
            if not all([client_id, client_secret]):
                self.logger.error("Variables d'environnement manquantes")
                return None
            
            scope = "user-library-read playlist-read-private playlist-read-collaborative"
            
            # Port différent pour la source
            redirect_uri = "http://127.0.0.1:8888/callback"
            
            auth_manager = SpotifyOAuth(
                client_id=client_id,
                client_secret=client_secret,
                redirect_uri=redirect_uri,
                scope=scope,
                cache_path=".cache_source",
                show_dialog=True  # Force l'affichage de la boîte de dialogue de connexion
            )
            
            sp = spotipy.Spotify(auth_manager=auth_manager)
            
            # Test de connexion et sauvegarde des infos
            user_info = sp.current_user()
            self.save_account_info('source', user_info)
            self.logger.info(f"Connecté au compte source: {user_info['display_name']} ({user_info['id']})")
            
            return sp
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'authentification du compte source: {e}")
            return None
    
    def authenticate_target_account(self) -> Optional[spotipy.Spotify]:
        """Authentifie le compte Spotify destination"""
        try:
            client_id = os.getenv('SPOTIFY_CLIENT_ID')
            client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
            
            if not all([client_id, client_secret]):
                self.logger.error("Variables d'environnement manquantes")
                return None
            
            scope = "user-library-read user-library-modify playlist-read-private playlist-read-collaborative playlist-modify-private playlist-modify-public"
            
            # Port différent pour la destination
            redirect_uri = "http://127.0.0.1:8889/callback"
            
            auth_manager = SpotifyOAuth(
                client_id=client_id,
                client_secret=client_secret,
                redirect_uri=redirect_uri,
                scope=scope,
                cache_path=".cache_target",
                show_dialog=True  # Force l'affichage de la boîte de dialogue de connexion
            )
            
            sp = spotipy.Spotify(auth_manager=auth_manager)
            
            # Test de connexion et sauvegarde des infos
            user_info = sp.current_user()
            self.save_account_info('target', user_info)
            self.logger.info(f"Connecté au compte destination: {user_info['display_name']} ({user_info['id']})")
            
            return sp
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'authentification du compte destination: {e}")
            return None
    
    def get_authenticated_clients(self) -> tuple[Optional[spotipy.Spotify], Optional[spotipy.Spotify]]:
        """Retourne les clients authentifiés pour les deux comptes"""
        print("🔐 Authentification du compte SOURCE (celui avec les musiques à copier)...")
        print("   ⚠️  IMPORTANT: Connectez-vous avec le compte qui contient vos musiques/playlists")
        source_client = self.authenticate_source_account()
        
        if not source_client:
            return None, None
            
        print("\n🔐 Authentification du compte DESTINATION (celui qui va recevoir)...")
        print("   ⚠️  IMPORTANT: Déconnectez-vous de Spotify dans le navigateur, puis connectez-vous avec l'AUTRE compte")
        print("   💡 Astuce: Utilisez un navigateur privé ou incognito pour éviter la confusion")
        
        target_client = self.authenticate_target_account()
        
        return source_client, target_client
    
    def display_connected_accounts(self):
        """Affiche les comptes actuellement connectés"""
        accounts = self.load_account_info()
        
        print("\n📱 Comptes Spotify connectés:")
        if 'source' in accounts:
            print(f"   🎵 Source: {accounts['source']['display_name']} ({accounts['source']['id']})")
        else:
            print("   🎵 Source: Non connecté")
            
        if 'target' in accounts:
            print(f"   🎯 Destination: {accounts['target']['display_name']} ({accounts['target']['id']})")
        else:
            print("   🎯 Destination: Non connecté")
        print()
        
        # Vérifier si ce sont les mêmes comptes
        if ('source' in accounts and 'target' in accounts and 
            accounts['source']['id'] == accounts['target']['id']):
            print("⚠️  ATTENTION: Même compte utilisé pour source ET destination !")
            print("   Pour synchroniser entre deux comptes différents:")
            print("   1. Supprimez les fichiers .cache_source et .cache_target")
            print("   2. Relancez le script") 
            print("   3. Connectez-vous avec des comptes différents")
            print()

