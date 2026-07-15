import pandas as pd
from pymongo import MongoClient
from datetime import datetime
import os

def read_secret(secret_name: str) -> str:
    #Lit un Docker Secret depuis /run/secrets/
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

# --------------- FONCTIONS DE TESTS APRES MIGRATION ---------------

def test_count(df_before, collection_after):
    csv_count   = len(df_before)
    mongo_count = collection_after.count_documents({})
    assert csv_count == mongo_count, f"FAILURE : CSV={csv_count} lignes, MongoDB={mongo_count} documents"
    print(f"[SUCCESS] Nombre de documents : {mongo_count} = nombre de lignes dans le fichier CSV : {csv_count}")

def test_champs_presents(collection_after):
    champs = [
        "name", "age", "gender", "blood_type", "medical_condition",
        "date_of_admission", "discharge_date", "doctor", "hospital",
        "insurance_provider", "billing_amount", "room_number",
        "admission_type", "medication", "test_results"
    ]
    for champ in champs:
        missingCol = collection_after.count_documents({champ: {"$exists": False}})
        assert missingCol == 0, f"FAILURE : champ '{champ}' absent dans {missingCol} documents"
    print("[SUCCESS] Tous les champs sont présents.")

def test_types(collection_after):

    for doc in collection_after.find():
        string_fields = [
            "name", "gender", "blood_type", "medical_condition", "doctor",
            "hospital", "insurance_provider", "admission_type", "medication", "test_results"
        ]

        for field in string_fields:
            assert isinstance(doc[field], str), f"FAILURE : {field} doit être de type string"

        assert isinstance(doc["age"], int), "FAILURE : Age doit être de type int"
        assert isinstance(doc["room_number"], int), "FAILURE : Room Number doit être de type int"
        assert isinstance(doc["billing_amount"], float), "FAILURE : Billing Amount doit être de type float"
        assert isinstance(doc["date_of_admission"], datetime), "FAILURE : Date of Admission doit être de type datetime"
        assert isinstance(doc["discharge_date"], datetime), "FAILURE : Discharge Date doit être de type datetime"
    
    print("[SUCCESS] Types des champs corrects.")

def test_doublons(collection_after):
    dataToCheck = [
        {
            "$group": {
                "_id": {
                    "name": "$name", "age": "$age", "gender": "$gender",
                    "blood_type": "$blood_type", "medical_condition": "$medical_condition",
                    "date_of_admission": "$date_of_admission", "discharge_date": "$discharge_date",
                    "doctor": "$doctor", "hospital": "$hospital",
                    "insurance_provider": "$insurance_provider", "billing_amount": "$billing_amount",
                    "room_number": "$room_number", "admission_type": "$admission_type",
                    "medication": "$medication", "test_results": "$test_results"
                },
                "count": {"$sum": 1}
            }
        },
        {"$match": {"count": {"$gt": 1}}}
    ]
    doublons = list(collection_after.aggregate(dataToCheck))
    if doublons:
        print(f"[FAILURE] {len(doublons)} doublons détectés.")
    else:
        print("[SUCCESS] Aucun doublon détecté.")

def test_valeurs_manquantes(collection_after):
    champs = ["name", "age", "gender", "blood_type", "medical_condition",
                "date_of_admission", "discharge_date", "doctor", "hospital",
                "insurance_provider", "billing_amount", "room_number",
                "admission_type", "medication", "test_results"]
    for champ in champs:
        manquants = collection_after.count_documents({champ: {"$in": [None, "", float("nan")]}})
        assert manquants == 0, f"FAILURE : {manquants} valeurs manquantes dans le champ '{champ}'"
    print("[SUCCESS] Aucune valeur manquante.")


def run_tests_after(df_data_before_migration):
    df_before = df_data_before_migration

    # --------------- LANCEMENT DES TESTS ---------------

    # Connexion via secrets Docker
    client  = get_mongo_client()
    db_name = read_secret("mongo_db")
    collection_after    = client[db_name]["patients"]

    print("=== Démarrage des tests APRES migration ===")

    try: 
        test_count(df_before, collection_after)
        test_champs_presents(collection_after)
        test_types(collection_after)
        test_doublons(collection_after)
        test_valeurs_manquantes(collection_after)
        print("=== Tests terminés ===")
    finally:
        client.close()