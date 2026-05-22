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
│   └── healthcare_dataset.csv
├── migrate.py
├── test_migration.py
├── requirements.txt
├── Dockerfile
├── docker compose.yml
├── init-mongo.js
└── README.md
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

Un index est créé sur chaque champ de la collection afin de maximiser les performances de recherche sur n'importe quelle colonne.

> **Note** : indexer tous les champs consomme plus de mémoire et ralentit légèrement les insertions.
> En production, on limiterait les index aux champs les plus interrogés (`name`, `medical_condition`, `doctor`, `date_of_admission`, `billing_amount`).

---

## Système d'authentification et rôles utilisateurs

L'authentification est activée sur MongoDB via `--auth` (par défaut). 
Trois utilisateurs sont créés automatiquement au démarrage par `init-mongo.js` :

| Utilisateur      | Rôle        | Droits                        | Utilisé par         |
|-----------------|-------------|-------------------------------|---------------------|
| `admin`         | root        | Accès total                   | Administrateur      |
| `userAdmin`| readWrite   | Lire + écrire les données     | fichier `migrate.py`        |
| `userVisitor`  | read        | Lire les données uniquement   | Médecins/analystes  |

---

## Utilisation

### En local (sans Docker)

```bash
# 1. Créer l'environnement virtuel
python -m venv venv
source venv/bin/activate        # Windows : venv\Scripts\activate

# 2. Installer les dépendances
pip install -r requirements.txt

# 3. Lancer la migration
python migrate.py
```

### Avec Docker

```bash
# Lancer tous les conteneurs
docker compose up --build

# Voir les logs de la migration
docker compose logs migration

# Voir les logs de MongoDB
docker compose logs mongodb
```

### Connexion depuis MongoDB Compass

```
mongodb://admin:admin123@localhost:27018/?authSource=admin
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

---

## Logique de migration (`migrate.py`)

1. **Chargement** du CSV avec pandas
2. **Renommage** des colonnes en snake_case (`Blood Type` → `blood_type`)
3. **Typage** explicite des colonnes (`age` en int, `billing_amount` en float, dates en datetime)
4. **Conversion** de chaque ligne en document Python (dict)
5. **Suppression** de la collection existante (évite les doublons si on relance le script)
6. **Insertion** en masse avec `insert_many()`
7. **Indexation** de tous les champs
8. **Tests d'intégrité** automatiques via `run_tests()`

---

## Tests d'intégrité (`test_migration.py`)

Les tests sont exécutés automatiquement à la fin de chaque migration en deux temps :

### Avant la migration — sur le CSV

| Test                          | Description                                           |
|------------------------------|-------------------------------------------------------|
| `test_csv_valeurs_manquantes` | Vérifie qu'aucune colonne ne contient de valeur nulle |
| `test_csv_doublons`           | Vérifie l'absence de lignes entièrement dupliquées    |
| `test_csv_types`              | Vérifie que les colonnes numériques sont bien typées  |

### Après la migration — sur MongoDB

| Test                       | Description                                               |
|---------------------------|-----------------------------------------------------------|
| `test_count`              | Vérifie que le nombre de documents = nombre de lignes CSV |
| `test_champs_presents`    | Vérifie la présence de tous les champs dans chaque document |
| `test_types`              | Vérifie le type des champs critiques                      |
| `test_doublons`           | Vérifie l'absence de documents entièrement dupliqués      |
| `test_valeurs_manquantes` | Vérifie qu'aucun champ ne contient de valeur nulle ou vide |
````