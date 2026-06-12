// Ce script est exécuté automatiquement au premier démarrage de MongoDB
db = db.getSiblingDB(process.env.MONGO_DB);

// Utilisateur pour la migration (lecture + écriture)
db.createUser({
  user: process.env.MONGO_USER_ADMIN_ID,
  pwd: process.env.MONGO_USER_ADMIN_PW,
  roles: [{ role: "readWrite", db: process.env.MONGO_DB }]
});

// Utilisateur pour les analystes (lecture seule)
db.createUser({
  user: process.env.MONGO_USER_VISITOR_ID,
  pwd: process.env.MONGO_USER_VISITOR_PW,
  roles: [{ role: "read", db: process.env.MONGO_DB }]
});

print("Utilisateurs créés avec succès.");