import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import os

# Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_FILE = os.path.join(BASE_DIR, "crime_reports_clean.csv")
GEOJSON_FILE = os.path.join(BASE_DIR, "BOUNDARY_CDDNeighborhoods.geojson")
OUTPUT_MAP = os.path.join(BASE_DIR, "map.html")

def generer_carte():
    print("🗺️ --- GÉNÉRATION DE LA CARTE --- 🗺️")
    
    # 1. Chargement des données
    if not os.path.exists(CSV_FILE):
        print(f"❌ Erreur : Fichier CSV introuvable : {CSV_FILE}")
        return
    if not os.path.exists(GEOJSON_FILE):
        print(f"❌ Erreur : Fichier GeoJSON introuvable : {GEOJSON_FILE}")
        return
        
    df = pd.read_csv(CSV_FILE)
    print(f"Données chargées : {len(df)} crimes")
    
    gdf = gpd.read_file(GEOJSON_FILE)
    print(f"Quartiers chargés : {len(gdf)}")
    print(f"Colonnes GeoJSON : {gdf.columns.tolist()}")
    
    # 2. Agrégation par quartier
    # On compte le nombre d'occurrences par quartier
    # La colonne dans le CSV est 'Neighborhood'
    crimes_by_neighborhood = df['Neighborhood'].value_counts().reset_index()
    crimes_by_neighborhood.columns = ['Neighborhood', 'Crime_Count']
    
    print("\n--- Top 3 Quartiers (Crimes) ---")
    print(crimes_by_neighborhood.head(3))
    
    # Vérification somme
    total_aggregated = crimes_by_neighborhood['Crime_Count'].sum()
    print(f"Total crimes agrégés : {total_aggregated} (sur {len(df)} lignes)")
    
    # 3. Jointure
    # On doit trouver la colonne commune. 
    # SOUVENT dans ce fichier c'est 'NAME' ou 'Name' ou 'SV_NEIGHBORHOOD'
    # On va essayer de détecter automatiquement ou utiliser une convention.
    # Pour Cambridge, c'est souvent 'NAME'.
    
    geo_col = None
    possible_cols = ['NAME', 'Name', 'neighborhood', 'NEIGHBORHOOD']
    for col in possible_cols:
        if col in gdf.columns:
            geo_col = col
            break
            
    if not geo_col:
        print("❌ Impossible de trouver la colonne de nom de quartier dans le GeoJSON.")
        # Fallback sur la première colonne texte ou objet
        return

    print(f"Jointure sur la colonne GeoJSON : {geo_col}")
    
    # On uniformise pour la jointure (maj/min)
    # df['Neighborhood'] est souvent en Title Case ou Upper.
    # On tente une jointure directe d'abord.
    
    # Jointure
    gdf_joined = gdf.merge(crimes_by_neighborhood, left_on=geo_col, right_on='Neighborhood', how='left')
    
    # Remplir les NaN par 0 (quartiers sans crimes)
    gdf_joined['Crime_Count'] = gdf_joined['Crime_Count'].fillna(0)
    
    # Vérification orphelins
    orphans = gdf_joined[gdf_joined['Crime_Count'] == 0]
    if not orphans.empty:
        print(f"⚠️ Quartiers sans crimes correspondants (0 crimes): {orphans[geo_col].tolist()}")
    else:
        print("✅ Tous les quartiers ont des crimes associés.")
        
    # 4. Carte Choroplèthe (Interactive avec folium/explore)
    # geopandas.explore() nécessite folium et mapclassify
    try:
        m = gdf_joined.explore(
            column="Crime_Count", # Colonne à colorier
            tooltip=[geo_col, "Crime_Count"], # Info-bulle
            scheme="naturalbreaks", # Ou quantiles
            k=5,
            cmap="RdYlGn_r", # Rouge à Vert (renversé car Rouge = Danger ?) non, RdYlGn_r c'est Vert(High) -> Rouge(Low) ? 
                             # RdYlGn : Rouge(Low) -> Vert(High). On veut Vert(Low crime) -> Rouge(High Crime).
                             # Donc "RdYlGn_r" (Red-Yellow-Green reversed) : Vert -> Rouge.
            legend=True,
            tiles="CartoDB positron"
        )
        
        m.save(OUTPUT_MAP)
        print(f"\n✅ Carte interactive générée : {OUTPUT_MAP}")
        
        print("🌍 Ouverture automatique dans le navigateur...")
        # Détection environnement (WSL ou Autre)
        try:
            with open('/proc/version', 'r') as f:
                is_wsl = 'microsoft' in f.read().lower()
        except:
            is_wsl = False

        if is_wsl:
            # Sur WSL, il faut convertir le chemin Linux en chemin Windows pour explorer.exe
            import subprocess
            try:
                # On utilise wslpath -w pour obtenir le chemin Windows (ex: C:\Users\...)
                result = subprocess.run(['wslpath', '-w', OUTPUT_MAP], capture_output=True, text=True)
                if result.returncode == 0:
                    windows_path = result.stdout.strip()
                    print(f"Chemin Windows détecté : {windows_path}")
                    
                    # Méthode 1 : wslview (si installé)
                    # if shutil.which("wslview"):
                    #     os.system(f"wslview '{OUTPUT_MAP}'")
                    #     return

                    # Méthode 2 : cmd.exe /C start (plus robuste pour les accents et associations)
                    # Le premier "" est pour le titre de la fenêtre (bizarrerie de start)
                    print("Tentative ouverture via cmd.exe start...")
                    # On double-escape les backslashes pour python, mais ici f-string c'est ok.
                    # Attention aux caractères spéciaux.
                    import shlex
                    # escaping pour shell linux qui appelle cmd.exe... c'est complexe.
                    # On va faire simple : appel direct via subprocess sans shell=True si possible, 
                    # mais on appelle un exe windows depuis linux.
                    
                    # On tente os.system avec quotes.
                    cmd = f'cmd.exe /C start "" "{windows_path}"'
                    ret = os.system(cmd)
                    
                    if ret != 0:
                        print("⚠️ 'start' a échoué, tentative via explorer.exe...")
                        os.system(f'explorer.exe "{windows_path}"')
                        
                else:
                    print(f"⚠️ Échec de wslpath : {result.stderr}")
                    folder = os.path.dirname(OUTPUT_MAP)
                    os.system(f'explorer.exe "{folder}"')
            except Exception as wsl_e:
                 print(f"⚠️ Erreur lors de l'ouverture WSL : {wsl_e}")
        else:
            import webbrowser
            webbrowser.open('file://' + os.path.realpath(OUTPUT_MAP))

    except Exception as e:
        print(f"❌ Erreur lors de la génération de la carte interactive : {e}")
        print("Tentative de carte statique (matplotlib)...")
        fig, ax = plt.subplots(1, 1, figsize=(10, 10))
        gdf_joined.plot(column='Crime_Count', ax=ax, legend=True, cmap='OrRd')
        plt.title("Crimes par Quartier - Cambridge")
        plt.savefig(os.path.join(BASE_DIR, "map.png"))
        print("Carte statique sauvegardée : map.png")

if __name__ == "__main__":
    generer_carte()
