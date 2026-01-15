import pandas as pd
import os

def charger_donnees_crime():
    # Construction du chemin absolu vers le fichier de données (../../TP1/crime_reports_broken.csv)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    nom_fichier = os.path.join(base_dir, "..", "..", "TP1", "crime_reports_broken.csv")
    
    # 1. Vérification si le fichier existe
    if not os.path.exists(nom_fichier):
        print(f"❌ Erreur : Le fichier '{nom_fichier}' est introuvable.")
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

        # 5. Analyse des valeurs manquantes
        print("\n--- Valeurs manquantes par colonne ---")
        print(df.isnull().sum())

        # 6. Analyse des doublons
        print("\n--- Doublons ---")
        nb_doublons = df.duplicated().sum()
        print(f"Nombre de lignes complètement dupliquées : {nb_doublons}")

        # 7. Analyse de la cohérence (Exemple: Colonne 'Category')
        if 'Crime' in df.columns:
            print("\n--- Valeurs uniques pour 'Crime' (Aperçu) ---")
            print(df['Crime'].unique())
            print(f"Nombre de valeurs uniques : {df['Crime'].nunique()}")

        # 8. Vérification du format des dates
        # On essaie de convertir la colonne 'Crime Date Time' en datetime et on compte les échecs
        col_date = 'Crime Date Time'
        if col_date in df.columns:
            print(f"\n--- Vérification des dates ({col_date}) ---")
            # tentative de conversion avec format explicite pour éviter le warning
            fmt = '%m/%d/%Y %H:%M'
            dates_invalides = pd.to_datetime(df[col_date], format=fmt, errors='coerce').isna().sum() - df[col_date].isna().sum()
            print(f"Format de date invalide (non convertible) : {dates_invalides}")
        
        return df
        
    except Exception as e:
        print(f"💥 Une erreur est survenue : {e}")
        return None

def afficher_dictionnaire():
    meta_donnees = [
        {"Variable": "File Number", "Type": "Entier/Texte", "Définition": "Identifiant unique du rapport", "Exemple": "2016-02648"},
        {"Variable": "Date of Report", "Type": "Date", "Définition": "Date du signalement", "Exemple": "04/21/2016..."},
        {"Variable": "Crime Date Time", "Type": "Date/Heure", "Définition": "Date et heure du crime", "Exemple": "04/14/2016 18:00"},
        {"Variable": "Crime", "Type": "Texte", "Définition": "Type de crime", "Exemple": "Larceny from Building"},
        {"Variable": "Reporting Area", "Type": "Entier", "Définition": "Code zone de rapport", "Exemple": "504"},
        {"Variable": "Neighborhood", "Type": "Texte", "Définition": "Quartier", "Exemple": "Cambridgeport"},
        {"Variable": "Location", "Type": "Texte", "Définition": "Adresse approximative", "Exemple": "800 Block of..."}
    ]
    
    print("\n--- Dictionnaire des Données ---")
    df_meta = pd.DataFrame(meta_donnees)
    # On ajuste l'affichage pour bien voir tout le tableau
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 1000)
    pd.set_option('display.max_colwidth', None)
    print(df_meta)
    print("-" * 50)

# --- Fonctions d'indicateurs de qualité ---

def indicateur_completude(df, colonnes):
    """Calcule le % de valeurs non nulles pour une liste de colonnes."""
    resultats = {}
    for col in colonnes:
        if col in df.columns:
            taux = (1 - df[col].isnull().mean()) * 100
            resultats[col] = taux
        else:
            resultats[col] = 0.0
    return pd.Series(resultats)

def indicateur_unicite(df, colonne):
    """Calcule le % de valeurs uniques (proportion par rapport au total)."""
    if colonne not in df.columns: return 0.0
    return (df[colonne].nunique() / len(df)) * 100

def indicateur_doublons(df):
    """Calcule le % de lignes strictement identiques."""
    return (df.duplicated().sum() / len(df)) * 100

def indicateur_date_valide(df, colonne):
    """Calcule le % de dates parsables."""
    if colonne not in df.columns: return 0.0
    
    # Format spécifique pour 'Date of Report' et 'Crime Date Time'
    fmt = None
    if colonne == 'Date of Report':
        fmt = '%m/%d/%Y %I:%M:%S %p'
    elif colonne == 'Crime Date Time':
        fmt = '%m/%d/%Y %H:%M'
        
    # On force la conversion
    # Si fmt est fourni, c'est plus rapide et sans warning. Sinon on tente 'mixed'
    if fmt:
        dates_valides = pd.to_datetime(df[colonne], format=fmt, errors='coerce').notna().sum()
    else:
        dates_valides = pd.to_datetime(df[colonne], errors='coerce').notna().sum()
        
    return (dates_valides / len(df)) * 100

def indicateur_coherence_temporelle(df, col_report, col_crime):
    """Calcule le % de lignes où Date of Report >= Crime Date Time."""
    if col_report not in df.columns or col_crime not in df.columns: return 0.0
    
    # Formats spécifiques connus
    fmt_report = '%m/%d/%Y %I:%M:%S %p'
    fmt_crime = '%m/%d/%Y %H:%M'
    
    dt_report = pd.to_datetime(df[col_report], format=fmt_report, errors='coerce')
    dt_crime = pd.to_datetime(df[col_crime], format=fmt_crime, errors='coerce')
    
    # On ne garde que les lignes où les deux dates sont valides
    valid_mask = dt_report.notna() & dt_crime.notna()
    if valid_mask.sum() == 0: return 0.0
    
    # Cohérent si Report >= Crime
    nb_coherents = (dt_report[valid_mask] >= dt_crime[valid_mask]).sum()
    
    return (nb_coherents / len(df)) * 100

def indicateur_conformite_area(df, colonne):
    """Calcule le % de valeurs numériques dans Reporting Area."""
    if colonne not in df.columns: return 0.0
    # On essaie de convertir en numérique
    conformes = pd.to_numeric(df[colonne], errors='coerce').notna().sum()
    return (conformes / len(df)) * 100

def auditer_qualite(df):
    """Fonction principale regroupant les indicateurs."""
    print("\n📊 --- AUDIT DE QUALITÉ --- 📊")
    
    stats = {}
    
    # 1. Complétude
    completude = indicateur_completude(df, ['File Number', 'Crime', 'Neighborhood'])
    for col, val in completude.items():
        stats[f"Complétude [{col}]"] = val
        
    # 2. Unicité
    stats["Unicité [File Number]"] = indicateur_unicite(df, 'File Number')
    
    # 3. Doublons
    stats["Taux Doublons Exacts"] = indicateur_doublons(df)
    
    # 4. Validité Dates
    stats["Validité Date [Date of Report]"] = indicateur_date_valide(df, 'Date of Report')
    
    # 5. Cohérence Temporelle
    stats["Cohérence Temporelle (Report >= Crime)"] = indicateur_coherence_temporelle(df, 'Date of Report', 'Crime Date Time')
    
    # 6. Conformité Reporting Area
    stats["Conformité [Reporting Area]"] = indicateur_conformite_area(df, 'Reporting Area')
    
    # Affichage avec seuils
    seuils = {
        "Complétude": 95.0, # Doit être >
        "Unicité [File Number]": 100.0, # Doit être proche de
        "Taux Doublons Exacts": 0.0, # Doit être proches de 0 (attention logique inverse)
        "Validité Date": 95.0, 
        "Cohérence": 98.0,
        "Conformité": 95.0
    }
    
    resultats_series = pd.Series(stats)
    
    for indicateur, valeur in stats.items():
        status = "✅"
        # Logique simplifiée de seuil (adaptable)
        if "Doublons" in indicateur:
            if valeur > 0: status = "❌ (> 0%)"
        else:
            if valeur < 95.0: status = "❌ (< 95%)" # Seuil générique 95% pour l'exemple
            
        print(f"{indicateur:<40} : {valeur:.2f}% {status}")
        
    return resultats_series

# --- Fonctions de Nettoyage et Enrichissement ---

VALID_NEIGHBORHOODS = {
    "Cambridgeport",
    "East Cambridge",
    "Mid-Cambridge",
    "North Cambridge",
    "Riverside",
    "Area 4",
    "West Cambridge",
    "Peabody",
    "Inman/Harrington",
    "Highlands",
    "Agassiz",
    "MIT",
    "Strawberry Hill",
}

def nettoyer_donnees(df):
    """Nettoie le dataset selon les règles métier."""
    print("\n🧹 --- NETTOYAGE DES DONNÉES --- 🧹")
    df_clean = df.copy()
    initial_len = len(df_clean)
    
    # 1. Doublons
    # Doublons exacts
    df_clean = df_clean.drop_duplicates()
    print(f"- Doublons exacts supprimés : {initial_len - len(df_clean)}")
    
    # Unicité ID (File Number) - on garde le premier
    len_before = len(df_clean)
    if 'File Number' in df_clean.columns:
        df_clean = df_clean.drop_duplicates(subset=['File Number'], keep='first')
    print(f"- Doublons d'ID supprimés   : {len_before - len(df_clean)}")
    
    # 2. Crime null
    if 'Crime' in df_clean.columns:
        len_before = len(df_clean)
        df_clean = df_clean.dropna(subset=['Crime'])
        print(f"- Lignes 'Crime' null suppr : {len_before - len(df_clean)}")

    # 3. Dates
    fmt_report = '%m/%d/%Y %I:%M:%S %p'
    fmt_crime = '%m/%d/%Y %H:%M'
    
    # Conversion et suppression des invalides
    len_before = len(df_clean)
    if 'Date of Report' in df_clean.columns:
        df_clean['Date of Report'] = pd.to_datetime(df_clean['Date of Report'], format=fmt_report, errors='coerce')
        df_clean = df_clean.dropna(subset=['Date of Report'])
        
    if 'Crime Date Time' in df_clean.columns:
        df_clean['Crime Date Time'] = pd.to_datetime(df_clean['Crime Date Time'], format=fmt_crime, errors='coerce')
        df_clean = df_clean.dropna(subset=['Crime Date Time'])
    print(f"- Dates invalides suppr     : {len_before - len(df_clean)}")
    
    # Incohérence temporelle (Report < Crime)
    len_before = len(df_clean)
    if 'Date of Report' in df_clean.columns and 'Crime Date Time' in df_clean.columns:
        df_clean = df_clean[df_clean['Date of Report'] >= df_clean['Crime Date Time']]
    print(f"- Incohérences temp. suppr  : {len_before - len(df_clean)}")

    # 4. Reporting Area invalide
    if 'Reporting Area' in df_clean.columns:
        len_before = len(df_clean)
        # On force en numérique, les erreurs deviennent NaN, puis on drop
        df_clean['Reporting Area'] = pd.to_numeric(df_clean['Reporting Area'], errors='coerce')
        df_clean = df_clean.dropna(subset=['Reporting Area'])
        # On cast en int pour être propre
        df_clean['Reporting Area'] = df_clean['Reporting Area'].astype(int)
        print(f"- Reporting Area invalides  : {len_before - len(df_clean)}")

    # 5. Neighborhood invalide
    if 'Neighborhood' in df_clean.columns:
        len_before = len(df_clean)
        df_clean = df_clean[df_clean['Neighborhood'].isin(VALID_NEIGHBORHOODS)]
        print(f"- Neighborhood invalides    : {len_before - len(df_clean)}")

    print(f"Assignation finale : {len(df_clean)} lignes (Total supprimé : {initial_len - len(df_clean)})")
    return df_clean

def enrichir_donnees(df):
    """Ajoute des colonnes dérivées."""
    print("\n✨ --- ENRICHISSEMENT --- ✨")
    df_enrich = df.copy()
    
    # 1. Reporting Area Group
    if 'Reporting Area' in df_enrich.columns:
        # Groupe de centaines (ex: 602 -> 6)
        # Attention, Reporting Area est int maintenant
        df_enrich['reporting_area_group'] = df_enrich['Reporting Area'] // 100
        
        # Validation
        valeurs_aberrantes = df_enrich[df_enrich['reporting_area_group'] < 0]
        if not valeurs_aberrantes.empty:
            print(f"⚠️ Attention : {len(valeurs_aberrantes)} valeurs négatives détectées dans le groupe.")
            # On pourrait décider de les supprimer ou de prendre la valeur absolue.
            # Pour l'exercice, on filtre.
            df_enrich = df_enrich[df_enrich['reporting_area_group'] >= 0]
            
        print("Colonnes ajoutées : ['reporting_area_group']")
        
    return df_enrich

if __name__ == "__main__":
    # 0. Afficher le dictionnaire des données
    afficher_dictionnaire()

    # 1. Charger et analyser les données
    data = charger_donnees_crime()
    
    if data is not None:
        # 2. Lancer l'audit complet (Avant nettoyage)
        print("\n--- AVANT NETTOYAGE ---")
        stats_avant = auditer_qualite(data)
        
        # 3. Nettoyer les données
        data_clean = nettoyer_donnees(data)
        
        # 4. Enrichir les données
        data_enriched = enrichir_donnees(data_clean)
        
        # 5. Audit final (Après nettoyage)
        print("\n--- APRÈS NETTOYAGE ---")
        stats_apres = auditer_qualite(data_enriched)
        
        # 6. Comparaison et Monitoring
        print("\n📈 --- MONITORING DE LA QUALITÉ (AVANT vs APRÈS) --- 📈")
        comparison = pd.DataFrame({
            'Avant (%)': stats_avant,
            'Après (%)': stats_apres
        })
        comparison['Evolution'] = comparison['Après (%)'] - comparison['Avant (%)']
        
        # On ajuste l'affichage
        pd.set_option('display.float_format', '{:.2f}'.format)
        print(comparison)
        
        print("\n--- Évolutions Significatives (> 1%) ---")
        sig_changes = comparison[comparison['Evolution'].abs() > 1.0]
        if not sig_changes.empty:
            print(sig_changes[['Avant (%)', 'Après (%)', 'Evolution']])
        else:
            print("Aucune évolution majeure détectée.")

        # 7. Export
        # Export dans le même dossier que le script (tp1-crime/tp1-crime/)
        base_dir = os.path.dirname(os.path.abspath(__file__))
        output_file = "crime_reports_clean.csv"
        output_path = os.path.join(base_dir, output_file)
        
        data_enriched.to_csv(output_path, index=False)
        print(f"\n✅ Fichier nettoyé exporté vers : {output_path}")