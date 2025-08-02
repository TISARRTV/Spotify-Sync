"""
Script de nettoyage pour le compte Spotify destination
Permet de supprimer toutes les playlists et unliker tous les titres
⚠️ ATTENTION: Ce script est destructif et irréversible !
"""

import time
from typing import List, Dict
from colorama import init, Fore, Style
from auth_manager import SpotifyAuthManager
from utils import format_french_datetime

# Initialiser colorama pour les couleurs
init()

class SpotifyCleanup:
    """Classe pour nettoyer complètement un compte Spotify"""
    
    def __init__(self, client):
        self.client = client
        self.user_info = client.current_user()
        self.user_id = self.user_info['id']
        self.display_name = self.user_info.get('display_name', 'Inconnu')
        
    def print_warning(self):
        """Affiche un avertissement de sécurité"""
        print(f"{Fore.RED}{'═' * 80}")
        print(f"║{' ' * 30}⚠️  AVERTISSEMENT ⚠️{' ' * 30}║")
        print(f"║{' ' * 78}║")
        print(f"║  Ce script va SUPPRIMER DÉFINITIVEMENT:                              ║")
        print(f"║  • TOUTES les playlists de votre compte                              ║")
        print(f"║  • TOUS les titres likés de votre compte                             ║")
        print(f"║                                                                      ║")
        print(f"║  Cette action est IRRÉVERSIBLE !                                    ║")
        print(f"║                                                                      ║")
        print(f"║  Compte concerné: {self.display_name:<45} ║")
        print(f"║  ID: {self.user_id:<61} ║")
        print(f"{'═' * 80}{Style.RESET_ALL}")
    
    def get_all_playlists(self) -> List[Dict]:
        """Récupère toutes les playlists de l'utilisateur"""
        print(f"\n📋 Récupération des playlists...")
        
        playlists = []
        offset = 0
        limit = 50
        
        while True:
            try:
                results = self.client.current_user_playlists(limit=limit, offset=offset)
                
                if not results['items']:
                    break
                
                for playlist in results['items']:
                    # Ne récupérer que les playlists appartenant à l'utilisateur
                    if playlist['owner']['id'] == self.user_id:
                        playlists.append({
                            'id': playlist['id'],
                            'name': playlist['name'],
                            'tracks_count': playlist['tracks']['total'],
                            'public': playlist['public'],
                            'collaborative': playlist['collaborative']
                        })
                
                offset += limit
                time.sleep(0.1)
                
            except Exception as e:
                print(f"   ❌ Erreur lors de la récupération des playlists: {e}")
                break
        
        print(f"   ✅ {len(playlists)} playlists trouvées")
        return playlists
    
    def get_all_liked_songs(self) -> List[str]:
        """Récupère tous les IDs des chansons likées"""
        print(f"\n❤️ Récupération des chansons likées...")
        
        liked_track_ids = []
        offset = 0
        limit = 50
        
        while True:
            try:
                results = self.client.current_user_saved_tracks(limit=limit, offset=offset)
                
                if not results['items']:
                    break
                
                for item in results['items']:
                    if item['track'] and item['track']['id']:
                        liked_track_ids.append(item['track']['id'])
                
                offset += limit
                time.sleep(0.1)
                
            except Exception as e:
                print(f"   ❌ Erreur lors de la récupération des likes: {e}")
                break
        
        print(f"   ✅ {len(liked_track_ids)} chansons likées trouvées")
        return liked_track_ids
    
    def delete_playlist(self, playlist: Dict) -> bool:
        """Supprime une playlist"""
        try:
            self.client.current_user_unfollow_playlist(playlist['id'])
            print(f"   ✅ Playlist supprimée: {playlist['name']}")
            return True
        except Exception as e:
            print(f"   ❌ Erreur suppression '{playlist['name']}': {e}")
            return False
    
    def unlike_songs_batch(self, track_ids: List[str]) -> int:
        """Unlike un lot de chansons (max 50 par batch)"""
        try:
            self.client.current_user_saved_tracks_delete(tracks=track_ids)
            return len(track_ids)
        except Exception as e:
            print(f"   ❌ Erreur lors du unlike d'un batch: {e}")
            return 0
    
    def delete_all_playlists(self) -> bool:
        """Supprime toutes les playlists de l'utilisateur"""
        playlists = self.get_all_playlists()
        
        if not playlists:
            print(f"   ℹ️ Aucune playlist à supprimer")
            return True
        
        print(f"\n🗑️ Suppression de {len(playlists)} playlists...")
        
        success_count = 0
        for i, playlist in enumerate(playlists, 1):
            print(f"   [{i}/{len(playlists)}] Suppression: {playlist['name']} ({playlist['tracks_count']} tracks)")
            
            if self.delete_playlist(playlist):
                success_count += 1
                
            # Pause entre les suppressions
            time.sleep(0.5)
        
        print(f"\n✅ {success_count}/{len(playlists)} playlists supprimées avec succès")
        return success_count == len(playlists)
    
    def unlike_all_songs(self) -> bool:
        """Unlike toutes les chansons likées"""
        track_ids = self.get_all_liked_songs()
        
        if not track_ids:
            print(f"   ℹ️ Aucune chanson likée à supprimer")
            return True
        
        print(f"\n💔 Unlike de {len(track_ids)} chansons...")
        
        # Traiter par batches de 50 (limite de l'API)
        batch_size = 50
        total_unliked = 0
        
        for i in range(0, len(track_ids), batch_size):
            batch = track_ids[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(track_ids) + batch_size - 1) // batch_size
            
            print(f"   [{batch_num}/{total_batches}] Unlike batch de {len(batch)} chansons...")
            
            unliked_count = self.unlike_songs_batch(batch)
            total_unliked += unliked_count
            
            # Pause entre les batches
            time.sleep(1)
        
        print(f"\n✅ {total_unliked}/{len(track_ids)} chansons unlikées avec succès")
        return total_unliked == len(track_ids)
    
    def full_cleanup(self) -> bool:
        """Nettoyage complet : playlists + likes"""
        print(f"\n🧹 Début du nettoyage complet...")
        start_time = time.time()
        
        # Supprimer les playlists
        playlists_success = self.delete_all_playlists()
        
        # Unlike les chansons
        likes_success = self.unlike_all_songs()
        
        duration = time.time() - start_time
        
        print(f"\n{'═' * 60}")
        if playlists_success and likes_success:
            print(f"✅ Nettoyage terminé avec succès en {duration:.1f} secondes")
            print(f"Le compte {self.display_name} a été entièrement nettoyé")
        else:
            print(f"⚠️ Nettoyage terminé avec des erreurs en {duration:.1f} secondes")
            if not playlists_success:
                print(f"   - Problèmes lors de la suppression des playlists")
            if not likes_success:
                print(f"   - Problèmes lors du unlike des chansons")
        
        return playlists_success and likes_success

def confirm_action(message: str) -> bool:
    """Demande confirmation à l'utilisateur"""
    while True:
        response = input(f"{message} (oui/non): ").lower().strip()
        if response in ['oui', 'o', 'yes', 'y']:
            return True
        elif response in ['non', 'n', 'no']:
            return False
        else:
            print("Veuillez répondre par 'oui' ou 'non'")

def main():
    """Fonction principale"""
    print(f"{Fore.CYAN}╔══════════════════════════════════════════════════════════════════════╗")
    print(f"║                     SPOTIFY CLEANUP TOOL                            ║")
    print(f"║                Nettoyage complet d'un compte                        ║")
    print(f"╚══════════════════════════════════════════════════════════════════════╝{Style.RESET_ALL}")
    
    try:
        # Authentification
        print(f"\n🔐 Authentification du compte à nettoyer...")
        print(f"   ⚠️ ATTENTION: Connectez-vous avec le compte que vous voulez NETTOYER")
        
        auth_manager = SpotifyAuthManager()
        
        # On utilise la méthode pour le compte destination (permissions d'écriture)
        target_client = auth_manager.authenticate_target_account()
        
        if not target_client:
            print(f"❌ Erreur d'authentification")
            return False
        
        # Créer l'objet de nettoyage
        cleanup = SpotifyCleanup(target_client)
        
        # Afficher l'avertissement
        cleanup.print_warning()
        
        # Demander confirmation
        if not confirm_action(f"\n❓ Voulez-vous vraiment nettoyer ce compte"):
            print(f"\n🛑 Opération annulée par l'utilisateur")
            return False
        
        # Dernière confirmation
        print(f"\n{Fore.RED}⚠️ DERNIÈRE CHANCE ! Cette action est IRRÉVERSIBLE !{Style.RESET_ALL}")
        if not confirm_action(f"Tapez 'oui' pour confirmer définitivement"):
            print(f"\n🛑 Opération annulée par l'utilisateur")
            return False
        
        # Menu des options
        print(f"\n📋 Que voulez-vous nettoyer ?")
        print(f"1. Supprimer uniquement les playlists")
        print(f"2. Unlike uniquement les chansons")
        print(f"3. Nettoyage complet (playlists + chansons)")
        print(f"4. Annuler")
        
        while True:
            choice = input(f"\nVotre choix (1-4): ").strip()
            
            if choice == '1':
                success = cleanup.delete_all_playlists()
                break
            elif choice == '2':
                success = cleanup.unlike_all_songs()
                break
            elif choice == '3':
                success = cleanup.full_cleanup()
                break
            elif choice == '4':
                print(f"\n🛑 Opération annulée")
                return False
            else:
                print(f"Choix invalide. Veuillez choisir 1, 2, 3 ou 4")
        
        if success:
            print(f"\n🎉 Nettoyage terminé avec succès !")
            print(f"Heure: {format_french_datetime()}")
        else:
            print(f"\n⚠️ Le nettoyage s'est terminé avec des erreurs")
        
        return success
        
    except KeyboardInterrupt:
        print(f"\n\n⏹️ Opération interrompue par l'utilisateur")
        return False
    except Exception as e:
        print(f"\n💥 Erreur inattendue: {e}")
        return False

if __name__ == "__main__":
    try:
        success = main()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n💥 Erreur critique: {e}")
        exit(1)
