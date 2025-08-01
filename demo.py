"""
Exemple pratique d'utilisation de l'API Spotify Sync
Ce script démontre comment utiliser les différentes fonctionnalités
"""

import os
import time
from datetime import datetime
from auth_manager import SpotifyAuthManager
from sync_manager import SpotifySyncManager
from utils import SyncStats, ConfigManager, format_french_datetime

def demo_basic_sync():
    """Démonstration d'une synchronisation basique"""
    print("🎵 DÉMONSTRATION: Synchronisation basique")
    print("=" * 50)
    
    # Initialisation
    auth_manager = SpotifyAuthManager()
    source_client, target_client = auth_manager.get_authenticated_clients()
    
    if not source_client or not target_client:
        print("❌ Impossible de se connecter aux comptes Spotify")
        return False
    
    # Afficher les informations des comptes
    source_user = source_client.current_user()
    target_user = target_client.current_user()
    
    print(f"📱 Compte source: {source_user.get('display_name', 'N/A')}")
    print(f"📱 Compte destination: {target_user.get('display_name', 'N/A')}")
    print()
    
    # Créer le gestionnaire de synchronisation
    sync_manager = SpotifySyncManager(source_client, target_client)
    
    # Synchronisation des chansons likées
    print("🎵 Synchronisation des chansons likées...")
    success_liked = sync_manager.sync_liked_songs()
    
    # Synchronisation des playlists
    print("📋 Synchronisation des playlists...")
    success_playlists = sync_manager.sync_playlists()
    
    # Résultat
    if success_liked and success_playlists:
        print("✅ Synchronisation terminée avec succès!")
        stats = sync_manager.get_sync_stats()
        print(f"   Chansons synchronisées: {stats['synced_tracks_count']}")
        print(f"   Playlists synchronisées: {stats['synced_playlists_count']}")
    else:
        print("❌ Synchronisation terminée avec des erreurs")
    
    return success_liked and success_playlists

def demo_selective_sync():
    """Démonstration d'une synchronisation sélective"""
    print("\n🎯 DÉMONSTRATION: Synchronisation sélective")
    print("=" * 50)
    
    # Configuration personnalisée
    config = {
        "sync_settings": {
            "sync_liked_songs": True,
            "sync_playlists": False,  # Désactiver les playlists
            "max_tracks_per_sync": 100  # Limiter à 100 chansons
        }
    }
    
    # Sauvegarder temporairement la config
    config_manager = ConfigManager()
    original_config = config_manager.config.copy()
    config_manager.config.update(config)
    config_manager.save_config(config_manager.config)
    
    try:
        # Synchronisation avec la nouvelle config
        auth_manager = SpotifyAuthManager()
        source_client, target_client = auth_manager.get_authenticated_clients()
        
        if source_client and target_client:
            sync_manager = SpotifySyncManager(source_client, target_client)
            
            print("🎵 Synchronisation des chansons likées uniquement...")
            success = sync_manager.full_sync()
            
            if success:
                print("✅ Synchronisation sélective terminée!")
            else:
                print("❌ Erreur lors de la synchronisation sélective")
        
    finally:
        # Restaurer la configuration originale
        config_manager.config = original_config
        config_manager.save_config(config_manager.config)

def demo_monitoring():
    """Démonstration du monitoring et des statistiques"""
    print("\n📊 DÉMONSTRATION: Monitoring et statistiques")
    print("=" * 50)
    
    # Initialiser les statistiques
    stats_manager = SyncStats()
    
    # Simuler quelques synchronisations
    print("📈 Simulation de synchronisations...")
    for i in range(3):
        print(f"   Simulation {i+1}/3...")
        
        # Simuler une sync
        tracks_synced = 10 + i * 5
        playlists_synced = 1 + i
        success = True
        duration = 30.5 + i * 10
        
        stats_manager.record_sync(tracks_synced, playlists_synced, success, duration)
        time.sleep(1)
    
    # Afficher le résumé
    summary = stats_manager.get_summary()
    print("\n📊 Résumé des statistiques:")
    print(f"   Synchronisations totales: {summary['total_syncs']}")
    print(f"   Chansons synchronisées: {summary['total_tracks_synced']}")
    print(f"   Playlists synchronisées: {summary['total_playlists_synced']}")
    print(f"   Taux de succès récent: {summary['recent_success_rate']:.1f}%")
    print(f"   Dernière synchronisation: {summary['last_sync_date']}")

def demo_error_handling():
    """Démonstration de la gestion d'erreurs"""
    print("\n🔧 DÉMONSTRATION: Gestion d'erreurs")
    print("=" * 50)
    
    # Simuler des erreurs
    stats_manager = SyncStats()
    
    print("⚠️ Simulation d'erreurs...")
    errors = [
        ("authentication", "Impossible de s'authentifier sur le compte source"),
        ("api_limit", "Limite de taux de l'API atteinte"),
        ("network", "Erreur de connexion réseau"),
    ]
    
    for error_type, error_msg in errors:
        print(f"   Erreur {error_type}: {error_msg}")
        stats_manager.record_error(error_msg, error_type)
    
    # Afficher les erreurs récentes
    summary = stats_manager.get_summary()
    print(f"\n📋 Erreurs récentes: {summary['recent_errors_count']}")

def demo_configuration():
    """Démonstration de la gestion de configuration"""
    print("\n⚙️ DÉMONSTRATION: Gestion de configuration")
    print("=" * 50)
    
    config_manager = ConfigManager()
    
    # Afficher la configuration actuelle
    print("📋 Configuration actuelle:")
    print(f"   Sync chansons likées: {config_manager.get('sync_settings.sync_liked_songs')}")
    print(f"   Sync playlists: {config_manager.get('sync_settings.sync_playlists')}")
    print(f"   Intervalle: {config_manager.get('sync_settings.sync_interval_minutes')} minutes")
    
    # Playlists exclues
    excluded = config_manager.get('playlist_settings.excluded_playlists', [])
    print(f"   Playlists exclues: {len(excluded)} playlists")
    for playlist in excluded[:3]:
        print(f"     - {playlist}")
    
    # Modifier temporairement une valeur
    print("\n🔧 Test de modification de configuration...")
    original_interval = config_manager.get('sync_settings.sync_interval_minutes')
    config_manager.set('sync_settings.sync_interval_minutes', 60)
    print(f"   Nouvel intervalle: {config_manager.get('sync_settings.sync_interval_minutes')} minutes")
    
    # Restaurer
    config_manager.set('sync_settings.sync_interval_minutes', original_interval)
    print(f"   Intervalle restauré: {config_manager.get('sync_settings.sync_interval_minutes')} minutes")

def main():
    """Fonction principale pour exécuter toutes les démonstrations"""
    print("🎵 SPOTIFY SYNC - DÉMONSTRATIONS")
    print("=" * 60)
    print("Ce script démontre les fonctionnalités de Spotify Sync")
    print("Mode démonstration - les synchronisations réelles sont optionnelles")
    print()
    
    try:
        # Vérifier si la configuration existe
        if not os.path.exists('.env'):
            print("⚠️ Fichier .env non trouvé!")
            print("   Copiez .env.example vers .env et configurez vos clés d'API")
            print("   Puis relancez ce script")
            return
        
        # Démonstrations qui ne nécessitent pas de connexion réelle
        demo_configuration()
        demo_monitoring()
        demo_error_handling()
        
        # Demander s'il faut faire les démonstrations avec connexion réelle
        print("\n" + "=" * 60)
        response = input("Voulez-vous tester avec de vraies connexions Spotify? (y/N): ")
        
        if response.lower() in ['y', 'yes', 'o', 'oui']:
            print("\n🔐 Connexion aux comptes Spotify...")
            demo_basic_sync()
            demo_selective_sync()
        else:
            print("\n📋 Démonstrations sans connexion terminées")
            print("   Pour tester avec de vraies connexions, configurez .env et relancez")
        
        print("\n✅ Toutes les démonstrations sont terminées!")
        print("\n🚀 Pour utiliser l'outil:")
        print("   python main.py --help")
        
    except KeyboardInterrupt:
        print("\n\n⏹️ Démonstration interrompue par l'utilisateur")
    except Exception as e:
        print(f"\n💥 Erreur pendant la démonstration: {e}")

if __name__ == "__main__":
    main()
