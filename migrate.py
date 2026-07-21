import pandas as pd
from pymongo import MongoClient
from test_before_migration import run_tests_before
from test_after_migration import run_tests_after
import os

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
    user  = read_secret("mongo_user_admin_id")
    pw    = read_secret("mongo_user_admin_pw")
    db    = read_secret("mongo_db")

    uri = f"mongodb://{user}:{pw}@mongodb:27017/{db}?authSource={db}"
    return MongoClient(uri)

#----------------------

def backup_collection(col, col_backup):
    # Copie la collection principale dans une collection temporaire
    col_backup.drop() # Vide/supprime la collection de sauvegarde
    documents = list(col.find({}, {"_id": 0}))  # Copie/Récupère tous les documents de la collection et exclut les _id pour éviter les conflits
    if documents:
        col_backup.insert_many(documents)
        print(f"[BACKUP] {len(documents)} documents sauvegardés dans la collection temporaire.")
    else:
        print("[BACKUP] Collection principale vide, aucune sauvegarde nécessaire.")

def rollback(col, col_backup):
    # Vide la collection principale et restaure depuis la collection temporaire
    print("============ ROLLBACK EN COURS ============")
    documents_backup = list(col_backup.find({}, {"_id": 0}))
    col.drop()
    if documents_backup:
        col.insert_many(documents_backup)
        print(f"[ROLLBACK] {len(documents_backup)} documents restaurés dans la collection principale.")
    else:
        print("[ROLLBACK] Collection temporaire vide, collection principale laissée vide.")
    print("============ ROLLBACK EFFECTUÉ ============")

# def clean_backup(col_backup):
#     # Supprime la collection temporaire après une migration réussie
#     col_backup.drop()
#     print("[CLEAN] Collection temporaire supprimée.")

#----------------------

def migrate(df_clean):
    print("============ LANCEMENT DE LA MIGRATION ============")
    # 1. Chargement du CSV
    df = df_clean.copy()

    # 2. Renommage des colonnes
    df = df.rename(columns={
        "Name": "name",
        "Age": "age",
        "Gender": "gender",
        "Blood Type": "blood_type",
        "Medical Condition": "medical_condition",
        "Date of Admission": "date_of_admission",
        "Doctor": "doctor",
        "Hospital": "hospital",
        "Insurance Provider": "insurance_provider",
        "Billing Amount": "billing_amount",
        "Room Number": "room_number",
        "Admission Type": "admission_type",
        "Discharge Date": "discharge_date",
        "Medication": "medication",
        "Test Results": "test_results"
    })

    # 3. Typage des colonnes
    df["age"] = df["age"].astype(int)
    df["room_number"] = df["room_number"].astype(int)
    df["billing_amount"] = df["billing_amount"].astype(float)
    df["date_of_admission"] = pd.to_datetime(df["date_of_admission"], errors="raise")
    df["discharge_date"] = pd.to_datetime(df["discharge_date"], errors="raise")

    # 4. Conversion en documents MongoDB
    documents = df.to_dict(orient="records")

    # 5. Connexion à MongoDB via secrets
    client  = get_mongo_client()
    db_name = read_secret("mongo_db")
    db = client[db_name]
    col = db["patients"]
    col_backup = db["patients_backup"]

    try:
        # 6. Sauvegarde de la collection actuelle
        backup_collection(col, col_backup)

        # 7. Suppression de la collection principale
        col.drop()

        # 8. Insertion de tous les documents en une seule fois
        col.insert_many(documents)

        # 9. Création des index
        indexes = [
            "name",
            "age",
            "doctor",
            "hospital",
            "date_of_admission"
        ]
        for field in indexes:
            col.create_index(field)

        print("============ MIGRATION EFFECTUÉE ============")
        print(f"{len(documents)} documents insérés avec succès.")

    except Exception as e:
        print(f"[ERREUR] Migration échouée : {e}")
        # Vide patients et restaure le contenu de patients_backup. Appelé automatiquement dans le except si la migration échoue.
        rollback(col, col_backup)
        client.close()
        raise  # relève l'erreur pour stopper le script
    finally:
        client.close()
        
    return col, col_backup, client

if __name__ == "__main__":
    df_data_csv = run_tests_before()
    df_to_migrate = df_data_csv.copy()

    migrate(df_to_migrate)
    run_tests_after(df_to_migrate)
