import pandas as pd
from pymongo import MongoClient
from datetime import datetime
import os

def run_tests():

    CSV_PATH = "data/healthcare_dataset.csv"
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27018/")

    # --------------- FONCTIONS DE TESTS AVANT MIGRATION ---------------

    # Test : Vérifie l'absence de valeurs manquantes dans le fichier CSV
    def test_csv_valeurs_manquantes(df):
        manquants = df.isnull().sum()
        for champ, count in manquants.items():
            assert count == 0, f"FAILURE : {count} valeurs manquantes dans la colonne CSV '{champ}'"
        print("[SUCCESS] Aucune valeur manquante dans le CSV.")

    # Test : Vérifie l'absence de doublons dans le fichier CSV
    def test_csv_doublons(df):
        doublons = df.duplicated().sum()
        if doublons:
            print(f"[FAILURE] {doublons} doublons détectés dans le CSV.")
        else:
            print("[SUCCESS] Aucun doublon dans le CSV.")

    # Test : Vérifie que les types des champs du Dataframe sont corrects
    def test_csv_types(df):
        assert df["Age"].dtype in ["int64", "float64"], "FAILURE : Age doit être numérique"
        assert df["Billing Amount"].dtype == "float64", "FAILURE : Billing Amount doit être float"
        assert df["Room Number"].dtype in ["int64", "float64"], "FAILURE : Room Number doit être numérique"
        print("[SUCCESS] Types des colonnes CSV corrects.")


    # --------------- FONCTIONS DE TESTS APRES MIGRATION ---------------

    # Test: Vérifie que le nombre de documents MongoDB est égale au nombre de lignes dans CSV
    def test_count(df, col):
        csv_count   = len(df)
        mongo_count = col.count_documents({})
        assert csv_count == mongo_count, f"FAILURE : CSV={csv_count} lignes, MongoDB={mongo_count} documents"
        print(f"[SUCCESS] Nombre de documents : {mongo_count} = nombre de lignes dans le CSV")

    # Test : Vérifie que chaque champ attendu est présent dans tous les documents
    def test_champs_presents(col):
        champs = [
            "name",
            "age",
            "gender",
            "blood_type",
            "medical_condition",
            "date_of_admission",
            "discharge_date",
            "doctor",
            "hospital",
            "insurance_provider",
            "billing_amount",
            "room_number",
            "admission_type",
            "medication",
            "test_results"
        ]
        for champ in champs:
            missingCol = col.count_documents({champ: {"$exists": False}}) # $exists est un opérateur MongoDB qui vérifie si un champ existe ou non.
            assert missingCol == 0, f"FAILURE : champ '{champ}' absent dans {missingCol} documents"
        print("[SUCCESS] Tous les champs sont présents.")

    # Test : Vérifie que le type des champs est correct
    def test_types(col):
        doc = col.find_one() # récupère un seul document de la collection (MongoDB)

        string_fields = [
            "name",
            "gender",
            "blood_type",
            "medical_condition",
            "doctor",
            "hospital",
            "insurance_provider",
            "admission_type",
            "medication",
            "test_results"
        ]

        for field in string_fields:
            assert isinstance(doc[field], str), f"FAILURE : {field} doit être de type string"

        assert isinstance(doc["age"],int), "FAILURE : Age doit être de type int"
        assert isinstance(doc["room_number"],int), "FAILURE : Room Number doit être de type int"
        assert isinstance(doc["billing_amount"], float), "FAILURE : Billing Amount doit être de type float"
        assert isinstance(doc["date_of_admission"], datetime), "FAILURE : Date of Admission doit être de type datetime"
        assert isinstance(doc["discharge_date"], datetime), "FAILURE : Date of Admission doit être de type datetime"
        print("[SUCCESS] Types des champs corrects.")


    # Test : Vérifie l'absence de doublons
    def test_doublons(col):

        dataToCheck = [
            {
                "$group": {
                    "_id": {
                    "name": "$name",
                    "age": "$age",
                    "gender": "$gender",
                    "blood_type": "$blood_type",
                    "medical_condition": "$medical_condition",
                    "date_of_admission": "$date_of_admission",
                    "discharge_date": "$discharge_date",
                    "doctor": "$doctor",
                    "hospital": "$hospital",
                    "insurance_provider": "$insurance_provider",
                    "billing_amount": "$billing_amount",
                    "room_number": "$room_number",
                    "admission_type": "$admission_type",
                    "medication": "$medication",
                    "test_results": "$test_results"
                    },
                    "count": {"$sum": 1}
                }
            },
            {"$match": {"count": {"$gt": 1}}}
        ]

        doublons = list(col.aggregate(dataToCheck))

        if doublons:
            print(f"[FAILURE] {len(doublons)} doublons détectés.")
        else:
            print("[SUCCESS] Aucun doublon détecté.")

    # Test : Vérifie l'absence de valeurs manquantes (nulle ou vide)
    def test_valeurs_manquantes(col):
        champs = ["name", "age", "gender", "blood_type", "medical_condition",
                "date_of_admission", "discharge_date", "doctor", "hospital",
                "insurance_provider", "billing_amount", "room_number",
                "admission_type", "medication", "test_results"]
        for champ in champs:
            manquants = col.count_documents({champ: {"$in": [None, "", float("nan")]}})
            assert manquants == 0, f"FAILURE : {manquants} valeurs manquantes dans le champ '{champ}'"
        print("[SUCCESS] Aucune valeur manquante.")


    # --------------- LANCEMENT DES TESTS ---------------

    # Chargement du CSV
    df = pd.read_csv(CSV_PATH)

    print("=== Démarrage des tests AVANT migration ===")
    test_csv_valeurs_manquantes(df)
    test_csv_doublons(df)
    test_csv_types(df)

    # Connexion + chargement
    # client = MongoClient("mongodb://localhost:27017/") # connexion au serveur MongoDB en local
    client = MongoClient(MONGO_URI)                      # connexion au serveur MongoDB depuis Docker
    col    = client["healthcare_db"]["patients"]

    # Lancement des tests
    print("=== Démarrage des tests APRES migration ===")
    test_count(df, col)
    test_champs_presents(col)
    test_types(col)
    test_doublons(col)
    test_valeurs_manquantes(col)
    print("=== Tests terminés ===")

    # Fermeture de la connexion
    client.close()