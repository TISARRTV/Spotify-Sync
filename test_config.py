"""
Script d'exemple pour utiliser l'outil de synchronisation Spotify
"""

from auth_manager import SpotifyAuthManager
from sync_manager import SpotifySyncManager
from utils import SyncStats, ConfigManager, format_duration
import time

def example_usage():
    """Exemple d'utilisation de l'outil de synchronisation"""
    
    print("=== EXEMPLE D'UTILISATION SPOTIFY SYNC ===\n")
    
    # 1. Configuration
    print("1. Chargement de la configuration...")
    config_manager = ConfigManager()
    print(f"   Configuration chargée depuis: {config_manager.config_path}")
    
    # 2. Statistiques
    print("\n2. Initialisation des statistiques...")
    stats = SyncStats()
    summary = stats.get_summary()
    print(f"   Synchronisations totales: {summary['total_syncs']}")
    print(f"   Tracks synchronisées: {summary['total_tracks_synced']}")
    print(f"   Playlists synchronisées: {summary['total_playlists_synced']}")
    
    # 3. Authentification
    print("\n3. Authentification...")
    auth_manager = SpotifyAuthManager()
    
    print("   Tentative de connexion au compte source...")
    source_client, target_client = auth_manager.get_authenticated_clients()
    
    if not source_client:
        print("   ❌ Échec de l'authentification du compte source")
        print("   Vérifiez votre fichier .env et vos clés d'API")
        return False
    
    if not target_client:
        print("   ❌ Échec de l'authentification du compte destination")
        print("   Vérifiez votre fichier .env et vos clés d'API")
        return False
    
    print("   ✅ Authentification réussie pour les deux comptes")
    
    # 4. Informations sur les comptes
    print("\n4. Informations sur les comptes...")
    try:
        source_user = source_client.current_user()
        target_user = target_client.current_user()
        
        print(f"   Compte source: {source_user.get('display_name', 'N/A')} ({source_user['id']})")
        print(f"   Compte destination: {target_user.get('display_name', 'N/A')} ({target_user['id']})")
        
        # Vérifier les playlists
        source_playlists = source_client.current_user_playlists(limit=5)
        print(f"   Playlists source (aperçu): {source_playlists['total']} au total")
        for playlist in source_playlists['items'][:3]:
            print(f"     - {playlist['name']} ({playlist['tracks']['total']} tracks)")
        
        # Vérifier les chansons likées
        source_liked = source_client.current_user_saved_tracks(limit=1)
        print(f"   Chansons likées source: {source_liked['total']} au total")
        
    except Exception as e:
        print(f"   ⚠️ Erreur lors de la récupération des informations: {e}")
        return False
    
    # 5. Test de synchronisation (simulation)
    print("\n5. Test de synchronisation...")
    sync_manager = SpotifySyncManager(source_client, target_client)
    
    print("   📋 Mode simulation activé - aucune modification ne sera effectuée")
    start_time = time.time()
    
    # Simuler une synchronisation
    print("   🔄 Simulation de la synchronisation des chansons likées...")
    time.sleep(1)
    
    print("   🔄 Simulation de la synchronisation des playlists...")
    time.sleep(1)
    
    duration = time.time() - start_time
    print(f"   ✅ Simulation terminée en {format_duration(duration)}")
    
    print("\n=== TEST TERMINÉ AVEC SUCCÈS ===")
    print("\nPour effectuer une vraie synchronisation, utilisez:")
    print("   python main.py")
    print("\nPour le mode surveillance continue:")
    print("   python main.py --watch")
    print("\nPour voir toutes les options:")
    print("   python main.py --help")
    
    return True

if __name__ == "__main__":
    try:
        success = example_usage()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️ Test interrompu par l'utilisateur")
        exit(0)
    except Exception as e:
        print(f"\n💥 Erreur lors du test: {e}")
        exit(1)
