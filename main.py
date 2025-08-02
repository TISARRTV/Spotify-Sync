import click
import json
import schedule
import time
import logging
from datetime import datetime
from colorama import init, Fore, Style
from auth_manager import SpotifyAuthManager
from sync_manager import SpotifySyncManager
from utils import format_french_datetime

# Initialiser colorama pour les couleurs dans le terminal
init()

def setup_logging():
    """Configure le système de logging avec format français"""
    from utils import format_french_datetime
    
    # Configuration personnalisée avec format français
    class FrenchFormatter(logging.Formatter):
        def formatTime(self, record, datefmt=None):
            from datetime import datetime
            ct = datetime.fromtimestamp(record.created)
            return format_french_datetime(ct)
    
    # Créer un formatter français
    french_formatter = FrenchFormatter('%(asctime)s - %(levelname)s - %(message)s')
    
    # Configuration du logging
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

def print_banner():
    """Affiche la bannière de l'application"""
    banner = f"""
{Fore.CYAN}╔═══════════════════════════════════════════════════════════════════════╗
║                          SPOTIFY SYNC TOOL                           ║
║                   Synchronisation de comptes Spotify                 ║
╚═══════════════════════════════════════════════════════════════════════╝{Style.RESET_ALL}
"""
    print(banner)

def print_sync_summary(sync_manager: SpotifySyncManager, success: bool, duration: float):
    """Affiche un résumé de la synchronisation"""
    stats = sync_manager.get_sync_stats()
    
    status_color = Fore.GREEN if success else Fore.RED
    status_text = "SUCCÈS" if success else "ÉCHEC"
    
    print(f"\n{Fore.YELLOW}═══ RÉSUMÉ DE LA SYNCHRONISATION ═══{Style.RESET_ALL}")
    print(f"Statut: {status_color}{status_text}{Style.RESET_ALL}")
    print(f"Durée: {duration:.2f} secondes")
    print(f"Chansons synchronisées: {Fore.CYAN}{stats['synced_tracks_count']}{Style.RESET_ALL}")
    print(f"Playlists synchronisées: {Fore.CYAN}{stats['synced_playlists_count']}{Style.RESET_ALL}")
    print(f"Heure: {format_french_datetime()}")
    print(f"{Fore.YELLOW}{'═' * 40}{Style.RESET_ALL}\n")

@click.command()
@click.option('--watch', is_flag=True, help='Mode surveillance continue')
@click.option('--interval', type=int, default=None, help='Intervalle de synchronisation en minutes (mode surveillance)')
@click.option('--config', default='config.json', help='Chemin vers le fichier de configuration')
@click.option('--dry-run', is_flag=True, help='Simulation sans modifications réelles')
def main(watch, interval, config, dry_run):
    """
    Outil de synchronisation automatique entre deux comptes Spotify.
    
    Synchronise les chansons likées et les playlists du compte source vers le compte destination.
    """
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Charger la configuration pour récupérer l'intervalle par défaut
    try:
        with open(config, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        default_interval = config_data.get('sync_settings', {}).get('sync_interval_minutes', 30)
    except:
        default_interval = 30
    
    # Utiliser l'intervalle de la config si pas spécifié en ligne de commande
    if interval is None:
        interval = default_interval
    
    # S'assurer que l'intervalle est un entier positif
    try:
        interval = int(interval)
        if interval < 1:
            print(f"{Fore.RED}❌ Erreur: L'intervalle doit être un nombre entier positif{Style.RESET_ALL}")
            return
    except (ValueError, TypeError):
        print(f"{Fore.RED}❌ Erreur: L'intervalle doit être un nombre entier{Style.RESET_ALL}")
        return
    
    print_banner()
    
    if dry_run:
        print(f"{Fore.YELLOW}⚠️  MODE SIMULATION ACTIVÉ - Aucune modification ne sera effectuée{Style.RESET_ALL}\n")
    
    try:
        # Initialiser le gestionnaire d'authentification
        print(f"{Fore.BLUE}🔐 Authentification en cours...{Style.RESET_ALL}")
        auth_manager = SpotifyAuthManager()
        
        # Obtenir les clients authentifiés
        source_client, target_client = auth_manager.get_authenticated_clients()
        
        if not source_client or not target_client:
            print(f"{Fore.RED}❌ Erreur d'authentification. Vérifiez votre configuration.{Style.RESET_ALL}")
            return
        
        print(f"{Fore.GREEN}✅ Authentification réussie{Style.RESET_ALL}")
        
        # Afficher les comptes connectés
        auth_manager.display_connected_accounts()
        
        # Initialiser le gestionnaire de synchronisation
        sync_manager = SpotifySyncManager(source_client, target_client, config)
        
        def perform_sync():
            """Effectue une synchronisation"""
            print(f"\n{Fore.BLUE}🔄 Début de la synchronisation...{Style.RESET_ALL}")
            start_time = time.time()
            
            # Réinitialiser les compteurs de session
            sync_manager.reset_session_counters()
            
            if dry_run:
                print(f"{Fore.YELLOW}📋 Simulation de la synchronisation...{Style.RESET_ALL}")
                # En mode dry-run, on simule juste une synchronisation réussie
                success = True
                time.sleep(2)  # Simulation d'une opération
            else:
                success = sync_manager.full_sync()
            
            duration = time.time() - start_time
            print_sync_summary(sync_manager, success, duration)
            
            return success
        
        if watch:
            print(f"{Fore.YELLOW}👁️  Mode surveillance activé (intervalle: {interval} minutes){Style.RESET_ALL}")
            print(f"{Fore.YELLOW}   Appuyez sur Ctrl+C pour arrêter{Style.RESET_ALL}\n")
            
            # Programmation de la synchronisation périodique
            schedule.every(interval).minutes.do(perform_sync)
            
            # Effectuer une première synchronisation immédiatement
            perform_sync()
            
            # Boucle de surveillance
            try:
                while True:
                    schedule.run_pending()
                    time.sleep(60)  # Vérifier chaque minute
            except KeyboardInterrupt:
                print(f"\n{Fore.YELLOW}⏹️  Arrêt du mode surveillance{Style.RESET_ALL}")
                logger.info("Mode surveillance arrêté par l'utilisateur")
        else:
            # Synchronisation unique
            success = perform_sync()
            exit_code = 0 if success else 1
            exit(exit_code)
    
    except Exception as e:
        logger.error(f"Erreur critique: {e}")
        print(f"{Fore.RED}💥 Erreur critique: {e}{Style.RESET_ALL}")
        exit(1)

@click.group()
def cli():
    """Outils de gestion pour Spotify Sync"""
    pass

@cli.command()
def setup():
    """Assistant de configuration initial"""
    print_banner()
    print(f"{Fore.BLUE}🛠️  Assistant de configuration Spotify Sync{Style.RESET_ALL}\n")
    
    print("Pour utiliser cet outil, vous devez créer deux applications Spotify :")
    print("1. Une pour le compte SOURCE (lecture)")
    print("2. Une pour le compte DESTINATION (écriture)")
    print()
    print(f"{Fore.YELLOW}📋 Étapes à suivre:{Style.RESET_ALL}")
    print("1. Visitez https://developer.spotify.com/dashboard/")
    print("2. Créez deux applications Spotify")
    print("3. Configurez l'URI de redirection: http://localhost:8080/callback")
    print("4. Copiez le fichier .env.example vers .env")
    print("5. Remplissez les valeurs dans le fichier .env")
    print()
    
    # Vérifier si le fichier .env existe
    import os
    if os.path.exists('.env'):
        print(f"{Fore.GREEN}✅ Fichier .env trouvé{Style.RESET_ALL}")
    else:
        print(f"{Fore.YELLOW}⚠️  Fichier .env non trouvé. Copiez .env.example vers .env{Style.RESET_ALL}")
    
    print(f"\n{Fore.CYAN}💡 Conseil: Utilisez --dry-run pour tester votre configuration{Style.RESET_ALL}")

@cli.command()
def status():
    """Affiche le statut de la configuration"""
    print_banner()
    
    import os
    from dotenv import load_dotenv
    load_dotenv()
    
    required_vars = [
        'SPOTIFY_CLIENT_ID',
        'SPOTIFY_CLIENT_SECRET', 
        'REDIRECT_URI'
    ]
    
    print(f"{Fore.BLUE}🔍 Vérification de la configuration...{Style.RESET_ALL}\n")
    
    all_set = True
    for var in required_vars:
        value = os.getenv(var)
        if value and value != f'your_{var.lower()}_here':
            print(f"{Fore.GREEN}✅{Style.RESET_ALL} {var}")
        else:
            print(f"{Fore.RED}❌{Style.RESET_ALL} {var} - Non configuré")
            all_set = False
    
    print()
    if all_set:
        print(f"{Fore.GREEN}🎉 Configuration complète !{Style.RESET_ALL}")
    else:
        print(f"{Fore.YELLOW}⚠️  Configuration incomplète. Utilisez 'python main.py setup' pour l'aide{Style.RESET_ALL}")

# Ajouter les commandes au groupe principal
cli.add_command(setup)
cli.add_command(status)

if __name__ == '__main__':
    # Vérifier si on appelle une sous-commande
    import sys
    if len(sys.argv) > 1 and sys.argv[1] in ['setup', 'status']:
        cli()
    else:
        main()
