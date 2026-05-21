# Healthcare Data Migration — MongoDB

## Contexte
Migration d'un dataset de données médicales (CSV) vers MongoDB
dans le cadre d'une solution Big Data scalable pour DataSoluTech.

## Concepts MongoDB utilisés
| Concept      | Définition                                          | Équivalent SQL |
|-------------|-----------------------------------------------------|----------------|
| Document    | Enregistrement JSON/BSON (une ligne du CSV)         | Ligne          |
| Collection  | Groupe de documents (`patients`)                    | Table          |
| Base de données | Conteneur de collections (`healthcare_db`)     | Schéma/BDD     |

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
Dans un contexte de production, on limiterait les index aux champs les plus interrogés (par exemple : `name`, `medical_condition`, `doctor`, `date_of_admission`, `billing_amount`).

---

## Utilisation

```bash
# 1. Créer l'environnement virtuel pour Python
python -m venv venv
source venv/bin/activate        # Windows : venv\Scripts\activate

# 2. Installer les dépendances
pip install -r requirements.txt

# 3. Lancer la migration
python migrate.py

# 4. Vérifier l'intégrité
python test_migration.py
```

## Déploiement avec Docker

Construire et démarrer les containers

```bash
docker compose up --build
```

Depuis MongoDB Compass en local

```bash
mongodb://localhost:27018
````

---

## Logique de migration (`migrate.py`)

1. **Chargement** du CSV avec pandas
2. **Renommage** des colonnes en snake_case 
3. **Typage** explicite des colonnes (`age` en int, `billing_amount` en float, dates en datetime )
4. **Conversion** de chaque ligne en document Python (dict)
5. **Suppression** de la collection existante (évite les doublons si on relance le script)
6. **Insertion** en masse avec `insert_many()`
7. **Indexation** des champs les plus interrogés
8. **Fermeture de la connexion**

---

## Tests d'intégrité (`test_migration.py`)

Les tests sont exécutés en deux temps :

### Avant la migration — sur le CSV

| Test                    | Description                                        |
|------------------------|----------------------------------------------------|
| `test_csv_valeurs_manquantes` | Vérifie qu'aucune colonne ne contient de valeur nulle |
| `test_csv_doublons`    | Vérifie l'absence de lignes entièrement dupliquées |
| `test_csv_types`       | Vérifie que les colonnes numériques sont bien typées |

### Après la migration — sur MongoDB

| Test                      | Description                                           |
|--------------------------|-------------------------------------------------------|
| `test_count`             | Vérifie que le nombre de documents = nombre de lignes CSV |
| `test_champs_presents`   | Vérifie la présence de tous les champs dans chaque document |
| `test_types`             | Vérifie le type des champs critiques                  |
| `test_doublons`          | Vérifie l'absence de documents entièrement dupliqués  |
| `test_valeurs_manquantes`| Vérifie qu'aucun champ ne contient de valeur nulle ou vide |


