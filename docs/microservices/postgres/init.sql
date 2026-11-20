-- Execute une seule fois, au premier demarrage du conteneur PostgreSQL.
-- Une base de donnees separee pour chaque microservice.
CREATE DATABASE catalogue_db;
CREATE DATABASE commandes_db;
CREATE DATABASE notifications_db;
