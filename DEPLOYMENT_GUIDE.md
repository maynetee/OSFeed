# Guide de Déploiement Production - OSFeed

Ce guide vous accompagne pas à pas pour déployer OSFeed sur un serveur de production pour **100 utilisateurs**.

## 1. Choix du Serveur (VPS)

Pour supporter 100 utilisateurs et 1000 canaux Telegram suivis, il nous faut un serveur capable de gérer la base de données vectorielle (Qdrant) en mémoire RAM.

**Recommandation :**
- **Type** : VPS (Virtual Private Server)
- **CPU** : 4 vCPU (Pour gérer les tâches de fond et les requêtes simultanées)
- **RAM** : 8 Go (Minimum recommandé pour la fluidité avec Qdrant + Postgres)
- **Disque** : 80 Go - 160 Go NVMe (SSD rapide est crucial pour la base de données)
- **OS** : Ubuntu 24.04 LTS (ou 22.04)

**Hébergeurs conseillés (Rapport Qualité/Prix) :**
1. **Hetzner Cloud** : Modèle **CPX31** (~15€/mois) -> *Meilleur choix*
2. **DigitalOcean** : Droplet "General Purpose" ou "Basic" 8GB (~40-50$/mois)
3. **Scaleway** : Instance PRO2-S (~30€/mois)

---

## 2. Préparation des Fichiers de Production

Sur votre ordinateur local, nous allons créer deux fichiers de configuration qui seront envoyés sur le serveur.

### A. `docker-compose.prod.yml`
Ce fichier modifie la configuration Docker pour la production (optimisation, sécurité, HTTPS).

Créez ce fichier à la racine du projet :

```yaml
services:
  # Backend : Mode Production (pas de reload, plus de workers)
  backend:
    build: ./backend
    restart: always
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
    volumes: [] # On retire le montage de volume pour la performance
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G

  # Frontend : Mode Production (Nginx statique)
  frontend:
    build:
      context: ./frontend
      target: production # Utilise l'étape Nginx du Dockerfile
    restart: always
    volumes: []
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 512M

  # Caddy : Serveur Web & HTTPS Automatique
  caddy:
    image: caddy:2-alpine
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile
      - caddy_data:/data
      - caddy_config:/config
    depends_on:
      - frontend
      - backend

  postgres:
    restart: always
    deploy:
      resources:
        limits:
          memory: 2G

  qdrant:
    restart: always
    deploy:
      resources:
        limits:
          memory: 2G

  redis:
    restart: always

volumes:
  caddy_data:
  caddy_config:
```

### B. `Caddyfile`
Ce fichier dit au serveur web comment diriger le trafic. Remplacez `votre-domaine.com` par votre vrai nom de domaine (ex: `osfeed.mon-entreprise.com`).

Créez ce fichier à la racine du projet :

```caddyfile
votre-domaine.com {
    # Frontend (Interface utilisateur)
    reverse_proxy frontend:80

    # Backend (API)
    handle_path /api/* {
        reverse_proxy backend:8000
    }

    # Documentation API (Optionnel)
    handle_path /docs* {
        reverse_proxy backend:8000
    }
    
    # OpenAPI JSON (Requis pour /docs)
    handle_path /openapi.json {
        reverse_proxy backend:8000
    }
}
```

---

## 3. Installation sur le Serveur

Une fois votre VPS acheté, vous recevrez une adresse IP (ex: `192.168.1.50`) et un mot de passe root.

### Étape 1 : Connexion SSH
Ouvrez votre terminal sur Mac :
```bash
ssh root@votre-ip-serveur
# Entrez le mot de passe fourni par l'hébergeur
```

### Étape 2 : Installation de Docker
Copiez-collez ces commandes une par une sur le serveur :

```bash
# Mettre à jour le système
apt update && apt upgrade -y

# Installer Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Vérifier que ça marche
docker compose version
```

### Étape 3 : Récupération du Projet
```bash
# Créer le dossier
mkdir -p /opt/osfeed
cd /opt/osfeed

# Cloner votre projet (Méthode simple via HTTPS)
# Remplacez l'URL par la vôtre
git clone https://github.com/votre-compte/osfeed.git .
```

*Note : Si votre projet est privé, vous devrez peut-être générer une clé SSH ou utiliser un "Personal Access Token".*

### Étape 4 : Configuration
Créez le fichier `.env` de production :
```bash
cp .env.example .env
nano .env
```
Modifiez les valeurs sensibles (Mots de passe DB, Clés API, Secret Key).
**Astuce** : Pour quitter nano, faites `Ctrl+X`, puis `Y`, puis `Entrée`.

Créez les fichiers de prod (ou transférez-les depuis votre Mac) :
```bash
nano docker-compose.prod.yml
# Collez le contenu du fichier créé à l'étape 2A

nano Caddyfile
# Collez le contenu du fichier créé à l'étape 2B (avec votre vrai domaine !)
```

---

## 4. Lancement et Maintenance

### Démarrer l'application
```bash
# Cette commande utilise la configuration de base + la surcharge de production
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```
*Le `--build` est important la première fois pour construire la version optimisée du frontend.*

### Vérifier que tout va bien
```bash
docker compose logs -f
```
Vous devriez voir "Backend started", "Database system is ready", etc.

### Mettre à jour l'application
Quand vous faites des modifications sur votre Mac :
1. Poussez les changements sur Git (`git push`)
2. Sur le serveur :
```bash
cd /opt/osfeed
git pull
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build --remove-orphans
```

---

## 5. Résumé des coûts et prérequis

| Élément | Recommandation | Coût estimé |
|---------|----------------|-------------|
| Serveur VPS | Hetzner CPX31 (4 vCPU / 8GB RAM) | ~15€ / mois |
| Domaine | Namecheap / OVH / Gandi | ~10€ / an |
| Stockage | Inclus dans le VPS (80-160 Go) | Inclus |
| Certificat SSL | Automatique via Caddy (Let's Encrypt) | Gratuit |

## Checklist avant lancement
- [ ] J'ai acheté un nom de domaine (ex: `mon-osfeed.com`)
- [ ] J'ai configuré l'enregistrement DNS `A` de mon domaine vers l'IP du VPS
- [ ] J'ai mis des mots de passe forts dans le fichier `.env` du serveur
- [ ] J'ai vérifié que le port 80 et 443 sont ouverts sur le pare-feu du VPS (souvent ouvert par défaut)
