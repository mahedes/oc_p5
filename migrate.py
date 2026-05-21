import pandas as pd
from pymongo import MongoClient
from test_migration import run_tests  
import os

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
CSV_PATH = "data/healthcare_dataset.csv"

def migrate():
    # 1. Chargement du CSV
    df = pd.read_csv(CSV_PATH)

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
    df["date_of_admission"] = (pd.to_datetime(df["date_of_admission"]))
    df["discharge_date"] = (pd.to_datetime(df["discharge_date"]))

    # 4. Conversion en documents MongoDB
    documents = df.to_dict(orient="records")

    # 5. Connexion à MongoDB
    #client = MongoClient("mongodb://localhost:27017/")  # connexion au serveur MongoDB en local
    client = MongoClient(MONGO_URI)  # connexion au serveur MongoDB depuis Docker
    col = client["healthcare_db"]["patients"]           # sélection de la base "healthcare_db" et de la collection "patients"

    # 6. Suppression de la collection si elle existe déjà (évite les doublons si on relance le script)
    col.drop()

    # 7. Insertion de tous les documents en une seule fois
    col.insert_many(documents)

    # 8. Création des index
    col.create_index("name")
    col.create_index("age")
    col.create_index("gender")
    col.create_index("blood_type")
    col.create_index("medical_condition")
    col.create_index("date_of_admission")
    col.create_index("doctor")
    col.create_index("hospital")
    col.create_index("insurance_provider")
    col.create_index("billing_amount")
    col.create_index("room_number")
    col.create_index("admission_type")
    col.create_index("discharge_date")
    col.create_index("medication")
    col.create_index("test_results")

    print(f"{len(documents)} documents insérés avec succès.")

    # 9. Fermeture de la connexion
    client.close()

if __name__ == "__main__":
    migrate()
    run_tests() 