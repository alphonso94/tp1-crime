import pandas as pd
import os

def charger_donnees_crime():
    # Nom exact de ton fichier
    nom_fichier = "crime_reports.csv"
    
    # 1. Vérification si le fichier existe
    if not os.path.exists(nom_fichier):
        print(f"❌ Erreur : Le fichier '{nom_fichier}' est introuvable.")
        print(f"Fichiers présents dans le dossier : {os.listdir('.')}")
        return None
    
    try:
        # 2. Chargement du fichier
        # On utilise low_memory=False pour éviter les avertissements sur les colonnes mixtes
        df = pd.read_csv(nom_fichier, low_memory=False)
        
        print(f"✅ Chargement réussi : {nom_fichier}")
        print(f"📊 Taille du jeu de données : {df.shape[0]} lignes et {df.shape[1]} colonnes\n")
        
        # 3. Affichage des premières lignes pour vérifier le contenu
        print("--- Aperçu des données ---")
        print(df.head())
        
        # 4. Analyse rapide des types de colonnes
        print("\n--- Infos colonnes ---")
        print(df.info())
        
        return df
        
    except Exception as e:
        print(f"💥 Une erreur est survenue : {e}")
        return None

if __name__ == "__main__":
    # Appel de la fonction
    data = charger_donnees_crime()