"""
Script pour vérifier l'ordre chronologique des titres likés
Permet de comparer l'ordre entre le compte source et destination
"""

import os
from datetime import datetime
from auth_manager import SpotifyAuthManager
from colorama import init, Fore, Style
from utils import format_french_date, format_french_time

# Initialiser colorama pour les couleurs
init()

def get_liked_songs_with_dates(client, account_name):
    """Récupère les chansons likées avec leurs dates d'ajout"""
    print(f"📥 Récupération des likes du compte {account_name}...")
    
    liked_songs = []
    offset = 0
    limit = 50
    
    while True:
        try:
            results = client.current_user_saved_tracks(limit=limit, offset=offset)
            
            if not results['items']:
                break
            
            for item in results['items']:
                track = item['track']
                if track and track['id']:
                    liked_songs.append({
                        'id': track['id'],
                        'name': track['name'],
                        'artists': ' & '.join([artist['name'] for artist in track['artists']]),
                        'added_at': item['added_at'],
                        'added_at_parsed': datetime.fromisoformat(item['added_at'].replace('Z', '+00:00'))
                    })
            
            offset += limit
            
            # Afficher le progrès
            print(f"   📊 {len(liked_songs)} chansons récupérées...", end='\r')
            
        except Exception as e:
            print(f"\n❌ Erreur lors de la récupération: {e}")
            break
    
    print(f"\n✅ {len(liked_songs)} chansons récupérées pour {account_name}")
    return liked_songs

def compare_order(source_songs, target_songs):
    """Compare l'ordre des chansons entre source et destination"""
    print(f"\n🔍 Analyse de l'ordre chronologique...")
    
    # Créer un mapping des IDs vers l'index dans la liste source
    source_order = {song['id']: i for i, song in enumerate(source_songs)}
    
    # Vérifier l'ordre dans la destination
    order_issues = []
    correctly_ordered = 0
    
    for i, target_song in enumerate(target_songs):
        track_id = target_song['id']
        
        if track_id in source_order:
            source_index = source_order[track_id]
            
            # Vérifier si l'ordre est respecté (index similaire)
            if abs(source_index - i) <= 2:  # Tolérance de 2 positions
                correctly_ordered += 1
            else:
                order_issues.append({
                    'track': target_song,
                    'target_position': i + 1,
                    'source_position': source_index + 1,
                    'difference': abs(source_index - i)
                })
    
    return correctly_ordered, order_issues

def display_first_last_songs(songs, account_name, count=5):
    """Affiche les premières et dernières chansons"""
    print(f"\n📋 {count} premiers likes de {account_name} (plus anciens):")
    for i, song in enumerate(songs[:count]):
        date_str = format_french_date(song['added_at_parsed']) + " à " + format_french_time(song['added_at_parsed'])
        print(f"   {i+1:2d}. {song['name']} - {song['artists']} ({date_str})")
    
    print(f"\n📋 {count} derniers likes de {account_name} (plus récents):")
    for i, song in enumerate(songs[-count:]):
        date_str = format_french_date(song['added_at_parsed']) + " à " + format_french_time(song['added_at_parsed'])
        pos = len(songs) - count + i + 1
        print(f"   {pos:2d}. {song['name']} - {song['artists']} ({date_str})")

def check_chronological_order(songs, account_name):
    """Vérifie si les chansons sont dans l'ordre chronologique"""
    print(f"\n⏰ Vérification de l'ordre chronologique de {account_name}...")
    
    is_chronological = True
    issues = []
    
    for i in range(1, len(songs)):
        current_date = songs[i]['added_at_parsed']
        previous_date = songs[i-1]['added_at_parsed']
        
        # Dans l'ordre chronologique, chaque chanson doit être plus récente que la précédente
        if current_date < previous_date:
            is_chronological = False
            issues.append({
                'position': i + 1,
                'current': songs[i],
                'previous': songs[i-1]
            })
    
    if is_chronological:
        print(f"   ✅ Ordre chronologique parfait !")
    else:
        print(f"   ❌ {len(issues)} problèmes d'ordre détectés")
        
        # Afficher quelques exemples
        for issue in issues[:3]:
            curr = issue['current']
            prev = issue['previous']
            print(f"      Position {issue['position']}: {curr['name']} ({format_french_date(curr['added_at_parsed'])}) "
                  f"avant {prev['name']} ({format_french_date(prev['added_at_parsed'])})")
    
    return is_chronological, len(issues)

def main():
    """Fonction principale"""
    print(f"{Fore.CYAN}╔═══════════════════════════════════════════════════════════════╗")
    print(f"║                    VÉRIFICATION DE L'ORDRE                   ║")
    print(f"║                   Titres Likés Spotify                       ║")
    print(f"╚═══════════════════════════════════════════════════════════════╝{Style.RESET_ALL}")
    
    try:
        # Authentification
        print(f"\n{Fore.BLUE}🔐 Authentification...{Style.RESET_ALL}")
        auth_manager = SpotifyAuthManager()
        source_client, target_client = auth_manager.get_authenticated_clients()
        
        if not source_client or not target_client:
            print(f"{Fore.RED}❌ Erreur d'authentification{Style.RESET_ALL}")
            return
        
        print(f"{Fore.GREEN}✅ Authentification réussie{Style.RESET_ALL}")
        
        # Récupérer les informations des comptes
        source_user = source_client.current_user()
        target_user = target_client.current_user()
        
        source_name = source_user['display_name']
        target_name = target_user['display_name']
        
        print(f"\n📱 Comptes connectés:")
        print(f"   🎵 Source: {source_name}")
        print(f"   🎯 Destination: {target_name}")
        
        # Récupérer les chansons likées
        print(f"\n{Fore.YELLOW}📊 Récupération des données...{Style.RESET_ALL}")
        
        source_songs = get_liked_songs_with_dates(source_client, source_name)
        target_songs = get_liked_songs_with_dates(target_client, target_name)
        
        # Inverser l'ordre pour avoir chronologique (API retourne récent → ancien)
        source_songs.reverse()
        target_songs.reverse()
        
        # Afficher les statistiques
        print(f"\n{Fore.YELLOW}📈 Statistiques:{Style.RESET_ALL}")
        print(f"   Source ({source_name}): {len(source_songs)} chansons likées")
        print(f"   Destination ({target_name}): {len(target_songs)} chansons likées")
        
        # Vérifier l'ordre chronologique de chaque compte
        source_chrono, source_issues = check_chronological_order(source_songs, source_name)
        target_chrono, target_issues = check_chronological_order(target_songs, target_name)
        
        # Afficher les premières et dernières chansons
        if source_songs:
            display_first_last_songs(source_songs, source_name)
        
        if target_songs:
            display_first_last_songs(target_songs, target_name)
        
        # Comparer l'ordre si les deux comptes ont des chansons
        if source_songs and target_songs:
            print(f"\n{Fore.YELLOW}🔄 Comparaison de l'ordre...{Style.RESET_ALL}")
            
            # Trouver les chansons communes
            source_ids = {song['id'] for song in source_songs}
            target_ids = {song['id'] for song in target_songs}
            common_ids = source_ids & target_ids
            
            print(f"   📊 Chansons communes: {len(common_ids)}")
            print(f"   📊 Uniquement source: {len(source_ids - target_ids)}")
            print(f"   📊 Uniquement destination: {len(target_ids - source_ids)}")
            
            if common_ids:
                # Filtrer pour ne garder que les chansons communes
                common_source = [s for s in source_songs if s['id'] in common_ids]
                common_target = [t for t in target_songs if t['id'] in common_ids]
                
                correctly_ordered, order_issues = compare_order(common_source, common_target)
                
                print(f"\n📋 Résultats de la comparaison:")
                print(f"   ✅ Chansons dans le bon ordre: {correctly_ordered}/{len(common_ids)}")
                print(f"   ❌ Chansons mal ordonnées: {len(order_issues)}")
                
                if order_issues:
                    print(f"\n⚠️  Exemples de problèmes d'ordre (top 5):")
                    for issue in order_issues[:5]:
                        track = issue['track']
                        print(f"      {track['name']}: position {issue['target_position']} "
                              f"(devrait être ~{issue['source_position']}, écart: {issue['difference']})")
        
        # Résumé final
        print(f"\n{Fore.CYAN}📋 RÉSUMÉ:{Style.RESET_ALL}")
        
        if source_chrono:
            print(f"   ✅ Ordre source ({source_name}): Parfait")
        else:
            print(f"   ❌ Ordre source ({source_name}): {source_issues} problèmes")
            
        if target_chrono:
            print(f"   ✅ Ordre destination ({target_name}): Parfait")
        else:
            print(f"   ❌ Ordre destination ({target_name}): {target_issues} problèmes")
        
        if source_songs and target_songs and common_ids:
            accuracy = (correctly_ordered / len(common_ids)) * 100
            print(f"   📊 Précision de la synchronisation: {accuracy:.1f}%")
            
            if accuracy >= 95:
                print(f"   🎉 Excellente synchronisation !")
            elif accuracy >= 85:
                print(f"   👍 Bonne synchronisation")
            else:
                print(f"   ⚠️  Synchronisation à améliorer")
    
    except KeyboardInterrupt:
        print(f"\n\n{Fore.YELLOW}⏹️  Vérification interrompue{Style.RESET_ALL}")
    except Exception as e:
        print(f"\n{Fore.RED}💥 Erreur: {e}{Style.RESET_ALL}")

if __name__ == "__main__":
    main()
