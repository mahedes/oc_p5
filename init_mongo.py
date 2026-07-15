import os
import time
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError

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

def connect_mongo(host: str, root_user: str, root_pw: str, retries: int = 10, delay: int = 3) -> MongoClient:
    # Attend que MongoDB soit prêt et retourne le client connecté
    for attempt in range(1, retries + 1):
        try:
            client = MongoClient(
                host=host,
                port=27017,
                username=root_user,
                password=root_pw,
                authSource="admin",
                serverSelectionTimeoutMS=3000
            )
            client.admin.command("ping")
            print(f"MongoDB prêt après {attempt} tentative(s).")
            return client  # on retourne le client au lieu de le fermer
        except ServerSelectionTimeoutError:
            print(f"Tentative {attempt}/{retries} : MongoDB pas encore prêt, attente {delay}s...")
            time.sleep(delay)
    raise RuntimeError("MongoDB non disponible après plusieurs tentatives.")

def init_mongodb():
    mongo_db   = read_secret("mongo_db")
    admin_id   = read_secret("mongo_user_admin_id")
    admin_pw   = read_secret("mongo_user_admin_pw")
    visitor_id = read_secret("mongo_user_visitor_id")
    visitor_pw = read_secret("mongo_user_visitor_pw")
    root_user  = read_secret("mongo_root_user")
    root_pw    = read_secret("mongo_root_pw")

    # Connexion à MongoDB
    client = connect_mongo("mongodb", root_user, root_pw)
    db = client[mongo_db]

    for user, pw, role in [
        (admin_id,   admin_pw,   "readWrite"),
        (visitor_id, visitor_pw, "read"),
    ]:
        try:
            db.command("createUser", user,
                pwd=pw,
                roles=[{"role": role, "db": mongo_db}]
            )
            print(f"Utilisateur '{user}' créé avec succès.")
        except Exception as e:
            if "already exists" in str(e):
                print(f"Utilisateur '{user}' existe déjà, on passe.")
            else:
                raise

    client.close()

if __name__ == "__main__":
    init_mongodb()