// Ce script est exécuté automatiquement au premier démarrage de MongoDB

db = db.getSiblingDB("healthcare_db");  // sélectionne la base healthcare_db

// Utilisateur pour la migration (lecture + écriture)
db.createUser({
  user: "userAdmin",
  pwd: "password123",
  roles: [{ role: "readWrite", db: "healthcare_db" }]
});

// Utilisateur pour les analystes (lecture seule)
db.createUser({
  user: "userVisitor",
  pwd: "password456",
  roles: [{ role: "read", db: "healthcare_db" }]
});

print("Utilisateurs créés avec succès.");