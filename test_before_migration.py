import pandas as pd
from pymongo import MongoClient
import sys
import os
from clean_csv import run_clean_data_duplicated

def read_secret(secret_name: str) -> str:
    # Lit un Docker Secret depuis /run/secrets/
    secret_path = f"/run/secrets/{secret_name}"
    try:
        with open(secret_path, "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        value = os.getenv(secret_name.upper())
        if not value:
            raise RuntimeError(f"Secret '{secret_name}' introuvable dans /run/secrets/ ni en variable d'environnement")
        return value

def get_mongo_client() -> MongoClient:
    # Construit le MongoClient depuis les secrets Docker
    user = read_secret("mongo_user_admin_id")
    pw   = read_secret("mongo_user_admin_pw")
    db   = read_secret("mongo_db")

    uri = f"mongodb://{user}:{pw}@mongodb:27017/{db}?authSource={db}"
    return MongoClient(uri)

# --------------- FONCTIONS DE TESTS AVANT MIGRATION ---------------

def test_csv_valeurs_manquantes(df):
    manquants = df.isnull().sum()

    if manquants.sum() > 0:
        print(f"FAILURE : Le fichier contient {manquants} valeurs manquantes.")
        print("=== LA MIGRATION A ETE BLOQUÉ ===")
        sys.exit(1)
    
    for champ, count in manquants.items():
        if count != 0:
            print(f"FAILURE : {count} valeurs manquantes dans la colonne CSV '{champ}'")
            print("=== LA MIGRATION A ETE BLOQUÉ ===")
            sys.exit(1)

    print("[SUCCESS] Aucune valeur manquante dans le CSV.")
    #return True

def test_csv_doublons(df):
    doublons = df.duplicated().sum()
    if doublons:
        print(f"[FAILURE] {doublons} doublons détectés dans le CSV.")
    else:
        print("[SUCCESS] Aucun doublon dans le CSV.")
    
    return doublons

def test_csv_types(df):

    col_string = [
        "Name", "Gender", "Blood Type", "Medical Condition",
        "Date of Admission", "Doctor", "Hospital", "Insurance Provider",
        "Admission Type", "Discharge Date", "Medication", "Test Results"
    ]

    for elt in col_string:
        if df[elt].dtype not in ["object", "string"]:
            print(f"{elt} n'est pas de type chaîne : {df[elt].dtype}")
            sys.exit(1)

    if df["Age"].dtype not in ["int64", "float64"]:
        sys.exit("FAILURE : Age doit être numérique")

    if df["Billing Amount"].dtype != "float64":
        sys.exit("FAILURE : Billing Amount doit être float")

    if df["Room Number"].dtype not in ["int64", "float64"]:
        sys.exit("FAILURE : Room Number doit être numérique")

    print("[SUCCESS] Types des colonnes CSV corrects.")
    #return True

def test_csv_coherence_dates(df):
    # Vérifie le format YYYY-MM-DD, la parsabilité et que admission < sortie 

    regex_date = r"^\d{4}-\d{2}-\d{2}$"

    # Vérification du format YYYY-MM-DD
    for colonne in ["Date of Admission", "Discharge Date"]:
        masque_format = ~df[colonne].astype(str).str.match(regex_date)
        invalides_format = df[masque_format]
        if len(invalides_format) > 0:
            print(f"[FAILURE] {len(invalides_format)} ligne(s) avec un format de date invalide dans '{colonne}' (attendu YYYY-MM-DD) :")
            print(invalides_format[["Name", colonne]].to_string(index=False))

    print("[SUCCESS] Format des dates vérifié (YYYY-MM-DD).")
        
    # Vérifie que Date of Admission < Discharge Date
    df_dates = df.copy()
    df_dates["Date of Admission"] = pd.to_datetime(df_dates["Date of Admission"], errors="coerce")
    df_dates["Discharge Date"] = pd.to_datetime(df_dates["Discharge Date"], errors="coerce")

    # Dates non parsables
    dates_invalides = df_dates[
        df_dates["Date of Admission"].isna() | df_dates["Discharge Date"].isna()
    ]
    if len(dates_invalides) > 0:
        print(f"[FAILURE] {len(dates_invalides)} ligne(s) avec des dates non parsables.")
        sys.exit(1)

    # Admission après sortie
    incoherentes = df_dates[df_dates["Date of Admission"] > df_dates["Discharge Date"]]
    if len(incoherentes) > 0:
        print(f"[FAILURE] {len(incoherentes)} ligne(s) où Date of Admission > Discharge Date :")
        print(incoherentes[["Name", "Date of Admission", "Discharge Date"]].to_string(index=False))
        sys.exit(1)

    print("[SUCCESS] Cohérence des dates vérifiée (admission < sortie).")
    #return True

def test_csv_coherence_age(df):
    # Vérifie que l'âge est compris entre 0 et 120 (Test en guise d'alerte - non bloquant)
    invalides = df[(df["Age"] < 0) | (df["Age"] > 120)]
    if len(invalides) > 0:
        print(f"[FAILURE] {len(invalides)} ligne(s) avec un âge incohérent (hors 0-120) :")
        print(invalides[["Name", "Age"]].to_string(index=False))
    print("[SUCCESS] Cohérence des âges vérifiée (0-120).")
    #return True


def run_tests_before():

    # --------------- LANCEMENT DES TESTS ---------------

    CSV_PATH = "data/healthcare_dataset.csv"
    df = pd.read_csv(CSV_PATH)
    tests = [
        test_csv_valeurs_manquantes,
        test_csv_types,
        test_csv_coherence_dates,
        test_csv_coherence_age,
    ]

    print("=== Démarrage des tests AVANT migration ===")
    for test in tests:
        test(df)
    duplicated_count = test_csv_doublons(df)

    if duplicated_count > 0 :
        print("=== Activation de clean_csv (NETTOYAGE PARTIEL AUTOMATISÉ - SUPPRESSION DES DOUBLONS) ===")
        print(f"=== Le fichier CSV contient {len(df)} lignes AVANT nettoyage (fichier brut)===")
        df_clean = run_clean_data_duplicated(df)
        df = df_clean.copy()
        print(f"=== Le fichier CSV contient {len(df)} lignes APRÈS nettoyage (fichier nettoyé)===")
        print("=== Re-démarrage des tests APRES NETTOYAGE PARTIEL ===")

        for test in tests:
            test(df)
        duplicated_count = test_csv_doublons(df)
        if duplicated_count > 0 :
            sys.exit("Les doublons détectés n'ont pas pu être supprimé")


    return df