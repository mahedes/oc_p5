# Healthcare Data Migration — MongoDB

## Contexte
Un client opère dans le secteur médical et gère un volume croissant de données patients au quotidien. 

Face à la croissance de leurs données, ils rencontrent des problèmes de scalabilité avec leur système actuel :
- Les requêtes deviennent de plus en plus lentes
- Le système actuel ne supporte pas la montée en charge
- La gestion des données patients devient difficile à maintenir

L'entreprise a proposé une migration vers une solution Big Data scalable horizontalement, reposant sur :

- MongoDB : base de données NoSQL orientée documents, adaptée aux données médicales semi-structurées
- Docker : conteneurisation de l'application pour garantir portabilité et reproductibilité
- AWS : recherche AWS sur le déploiement cloud pour assurer la scalabilité et la haute disponibilité

---

## Concepts MongoDB utilisés

| Concept          | Définition                                      | Équivalent SQL |
|-----------------|-------------------------------------------------|----------------|
| Document        | Enregistrement JSON/BSON (une ligne du CSV)     | Ligne          |
| Collection      | Groupe de documents (`patients`)                | Table          |
| Base de données | Conteneur de collections (`healthcare_db`)      | Schéma/BDD     |

---

## Arborescence fichiers

```
healthcare-migration/
├── data/
│   └── healthcare_dataset.csv (fichier CSV fourni par le client)
│   └── doublons_detectes.csv
├── secrets/
│   └── mongo_db.txt
│   └── mongo_root_pw.txt
│   └── mongo_root_user.txt
│   └── mongo_user_admin_id.txt
│   └── mongo_user_admin_pw.txt
│   └── mongo_user_visitor_id.txt
│   └── mongo_user_visitor_pw.txt
├── .gitignore
├── clean_csv.py
├── docker-compose.yml
├── Dockerfile
├── init_mongo.py
├── migrate.py
├── README.md
├── requirements.txt
├── test_before_migration.py
└── test_after_migration.py


```

---

## Schéma de la collection `patients`

```json
{
  "_id":                ObjectId,
  "name":               String,
  "age":                Int32,
  "gender":             String,
  "blood_type":         String,
  "medical_condition":  String,
  "date_of_admission":  Date,
  "discharge_date":     Date,
  "doctor":             String,
  "hospital":           String,
  "insurance_provider": String,
  "billing_amount":     Double,
  "room_number":        Int32,
  "admission_type":     String,
  "medication":         String,
  "test_results":       String
}
```

---

## Index créés

Les index ont été créés sur les champs les plus susceptibles d'être utilisés dans des recherches métier :

- `name` : recherche d'un patient.
- `age` : filtrage par tranche d'âge.
- `date_of_admission` : historique des admissions.
- `doctor` : patients suivis par un médecin.
- `hospital` : patients d'un établissement.

Tous les champs n'ont volontairement pas été indexés afin de limiter la consommation mémoire et le coût des opérations d'insertion.

---

## Système d'authentification et rôles utilisateurs

L'authentification est activée sur MongoDB via `--auth` (par défaut). 
Des utilisateurs sont créés automatiquement au démarrage par `init_mongo.py` :

| Utilisateur      | Rôle        | Droits                        | Utilisé par         |
|-----------------|-------------|-------------------------------|---------------------|
| `root_user`         | root        | Accès total                   | Administrateur      |
| `admin_user`| readWrite   | Lire + écrire les données     | fichier `migrate.py`        |
| `visitor_user`  | read        | Lire les données uniquement   | Médecins/analystes  |

---

## Utilisation

### Avec Docker

```
# Lancer tous les conteneurs
docker compose up --build

# Voir les logs de la migration
docker compose logs migration

# Voir les logs de MongoDB
docker compose logs mongodb
```
---

## Commandes utiles

| Commande | Rôle |
|---|---|
| `docker compose up --build` | Lance tout et reconstruit l'image |
| `docker compose logs migration` | Affiche les logs du script de migration |
| `docker compose logs mongodb` | Affiche les logs de MongoDB |
| `docker compose down` | Arrête les conteneurs |
| `docker compose down -v` | Arrête et supprime les volumes |
| `docker compose build --no-cache` | Reconstruit sans cache |
| `docker compose up` | Lance les conteneurs sans reconstruire l'image |
---

### Connexion depuis MongoDB Compass

```
mongodb://identifiant:motdepasse@localhost:27018/indique_ici_nom_mongo_db?authSource=indique_ici_nom_mongo_db
```

## Création des secrets Docker

Le projet utilise les secrets Docker Compose afin d'éviter de stocker les identifiants directement dans le fichier `docker-compose.yml`.

Avant de lancer les conteneurs, créer les fichiers secrets suivants :

```
secrets/
├── mongo_db.txt
├── mongo_root_pw.txt
├── mongo_root_user.txt
├── mongo_user_admin_id.txt
├── mongo_user_admin_pw.txt
├── mongo_user_visitor_id.txt
└── mongo_user_visitor_pw.txt
```
Note: Pour installer ce prototype, vous pouvez utiliser les identifiants et mots de passe de démonstration fournis ci-dessous pour faciliter l'installation. Ces identifiants seront à modifier par la suite pour sécuriser l'accès de l'application.
Ces valeurs sont uniquement destinées à un environnement de démonstration.
Elles ne doivent pas être utilisées en production.

```bash
mkdir -p secrets

echo "healthcare_db" > secrets/mongo_db.txt
echo "root_user" > secrets/mongo_root_user.txt
echo "root_password" > secrets/mongo_root_pw.txt

echo "admin_user" > secrets/mongo_user_admin_id.txt
echo "admin_password" > secrets/mongo_user_admin_pw.txt

echo "visitor_user" > secrets/mongo_user_visitor_id.txt
echo "visitor_password" > secrets/mongo_user_visitor_pw.txt

```

---
## Architecture de la migration

```
CSV
 │
 ▼
Tests avant migration
 ├── Absence de valeurs manquantes 
 ├── Typage correct
 ├── Cohérence des dates
 ├── Cohérence des âges
 ├── Absence de doublons
 │
 ▼
Nettoyage automatique
 ├──  sauvegarde des doublons dans un fichier CSV secondaire
 ├──  suppression des doublons du fichier CSV principale
 │
 ▼
Migration MongoDB
 ├── sauvegarde de la collection
 ├── suppression de l'ancienne collection si existante
 ├── insertion
 ├── création des index
 ├── rollback en cas d'erreur
 │
 ▼
Tests après migration
 ├── Nombre de documents de la base identique au nombre de ligne du fichier CSV
 ├── Présence des champs
 ├── Types correcte
 ├── Absence de doublons
 └── Absence de valeurs manquantes
```

## Logique de migration (`migrate.py`)

1. Chargement du fichier CSV.
2. Validation des données (tests avant migration depuis `test_before_migration.py`).
3. Nettoyage et sauvegarde automatique des doublons détectés depuis `clean_csv.py`
4. Renommage des colonnes en `snake_case`.
5. Conversion des types (`int`, `float`, `datetime`).
6. Sauvegarde de la collection MongoDB existante (`patients_backup`).
7. Suppression de la collection principale.
8. Insertion en masse (`insert_many`).
9. Création des index.
10. En cas d'erreur, restauration automatique depuis la sauvegarde (rollback).
11. Exécution des tests après migration (depuis `test_after_migration.py`)


---

## Sauvegarde et rollback

Avant chaque migration :

- la collection `patients` est copiée dans `patients_backup`.

En cas d'échec :

- la collection principale est supprimée ;
- la sauvegarde est automatiquement restaurée.

---

## Tests d'intégrité (`test_before_migration.py`, `test_after_migration.py`)

Les tests sont exécutés automatiquement avant et après chaque migration :

### Avant la migration — sur le CSV

| Test                          | Description                                           | Test bloquant |
|------------------------------|--------------------------------------------------------|---------------|
| `test_csv_valeurs_manquantes` | Vérifie qu'aucune colonne ne contient de valeur nulle | OUI           |
| `test_csv_doublons`           | Vérifie l'absence de lignes entièrement dupliquées    | OUI si échec après nettoyage           |
| `test_csv_types`              | Vérifie que les colonnes numériques sont bien typées  | OUI           |
| `test_csv_coherence_dates`    | Vérifie le format des dates et que la date de sortie est postérieure à la date d'admission  | OUI           |
| `test_csv_coherence_age`    | Vérifie que les âges sont compris entre 0 et 120 ans  | NON (simple alerte)          |

### Après la migration — sur MongoDB

| Test                      | Description                                               | Test bloquant |
|---------------------------|-----------------------------------------------------------|----|
| `test_count`              | Vérifie que le nombre de documents = nombre de lignes CSV | NON |
| `test_champs_presents`    | Vérifie la présence de tous les champs dans chaque document | NON |
| `test_types`              | Vérifie que les documents sont bien enregistrés avec les types attendus                      | NON |
| `test_doublons`           | Vérifie l'absence de documents entièrement dupliqués      | NON |
| `test_valeurs_manquantes` | Vérifie qu'aucun champ ne contient de valeur nulle ou vide | NON |
````
````

### Exemple d'améliorations possibles

- Dans le cadre des tests avant migration, compléter le message d'alerte du test vérifiant que les dates sont non parsables en indiquant l'index (équivament à la ligne dans le fichier CSV) de la ou des donnée(s) problématique(s)
- Isoler toutes les lignes problématiques dans un fichier CSV et les exclure du dataframe pour toutes les problématiques détectées par les tests avant migration (valeurs manquantes, problèmes de type, etc...) en plus des valeurs en doublons. Possibilité de créer une interface pour gérer les données problématiques manuellement.
- Si un test après migration ne passe pas, proposer à l'utilisateur un retour en arrière (roolback) via un prompt ou autres.