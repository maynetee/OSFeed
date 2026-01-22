# Guide de Configuration HTTPS Production pour OSFeed

Ce guide explique comment configurer HTTPS avec des certificats Let's Encrypt valides pour une mise en production.

---

## Table des Matières

1. [Prérequis](#prérequis)
2. [Configuration DNS](#configuration-dns)
3. [Configuration du Firewall](#configuration-du-firewall)
4. [Configuration de Caddy](#configuration-de-caddy)
5. [Déploiement](#déploiement)
6. [Vérification](#vérification)
7. [Dépannage](#dépannage)
8. [Renouvellement des Certificats](#renouvellement-des-certificats)

---

## Prérequis

- Un serveur avec une IP publique fixe
- Un nom de domaine que vous contrôlez
- Docker et Docker Compose installés
- Ports 80 et 443 accessibles depuis Internet

---

## Configuration DNS

### Étape 1 : Créer les enregistrements DNS

Connectez-vous à votre registrar ou gestionnaire DNS (OVH, Cloudflare, Gandi, etc.) et créez les enregistrements suivants :

| Type | Nom | Valeur | TTL |
|------|-----|--------|-----|
| A | @ | `VOTRE_IP_SERVEUR` | 3600 |
| A | www | `VOTRE_IP_SERVEUR` | 3600 |

### Étape 2 : Vérifier la propagation DNS

Attendez la propagation DNS (peut prendre de quelques minutes à 48h). Vérifiez avec :

```bash
# Vérifier l'enregistrement A
dig +short votredomaine.com

# Ou avec nslookup
nslookup votredomaine.com
```

Le résultat doit afficher l'IP de votre serveur.

---

## Configuration du Firewall

### Sur le serveur (UFW - Ubuntu/Debian)

```bash
# Autoriser HTTP (nécessaire pour le challenge ACME)
sudo ufw allow 80/tcp

# Autoriser HTTPS
sudo ufw allow 443/tcp

# Vérifier le statut
sudo ufw status
```

### Sur le serveur (firewalld - CentOS/RHEL)

```bash
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

### Chez votre hébergeur cloud

Si vous utilisez AWS, GCP, Azure, OVH, etc., vérifiez également les **Security Groups** ou **Firewall Rules** dans votre console cloud :

- **Entrée TCP 80** : 0.0.0.0/0
- **Entrée TCP 443** : 0.0.0.0/0

---

## Configuration de Caddy

### Le fichier Caddyfile

Le projet utilise Caddy qui gère automatiquement les certificats Let's Encrypt. Voici la structure du `Caddyfile` :

```caddyfile
# Configuration globale
{
    # Utiliser Let's Encrypt en production
    acme_ca https://acme-v02.api.letsencrypt.org/directory

    # Email pour les notifications de certificat (optionnel mais recommandé)
    email votre@email.com
}

# Votre domaine avec HTTPS automatique
votredomaine.com, www.votredomaine.com {
    # Configuration TLS
    tls {
        issuer acme {
            # Si votre hébergeur bloque TLS-ALPN-01 (comme OVH)
            disable_tlsalpn_challenge
        }
    }

    # Routes vers le backend
    handle /api/* {
        reverse_proxy backend:8000
    }

    # Routes vers le frontend
    handle {
        reverse_proxy frontend:80
    }
}
```

### Modifier le domaine

1. Ouvrez le fichier `Caddyfile`
2. Remplacez `osfeed.com, www.osfeed.com` par votre domaine
3. Ajoutez votre email pour recevoir les alertes d'expiration

---

## Déploiement

### Étape 1 : Configurer les variables d'environnement

Créez ou modifiez le fichier `.env` :

```bash
# Domaine
DOMAIN=votredomaine.com

# Autres variables de production...
APP_ENV=production
```

### Étape 2 : Lancer les conteneurs

```bash
# Arrêter les conteneurs existants
./stop.sh

# Lancer en mode production
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

### Étape 3 : Surveiller l'obtention du certificat

```bash
# Voir les logs de Caddy
docker compose logs -f caddy
```

Vous devriez voir des messages comme :
```
caddy  | {"level":"info","msg":"certificate obtained successfully"}
caddy  | {"level":"info","msg":"enabling automatic TLS certificate management"}
```

---

## Vérification

### Test 1 : Accès HTTPS

```bash
# Tester l'accès HTTPS
curl -I https://votredomaine.com
```

Réponse attendue : `HTTP/2 200`

### Test 2 : Vérifier le certificat

```bash
# Afficher les infos du certificat
echo | openssl s_client -connect votredomaine.com:443 2>/dev/null | openssl x509 -noout -dates -issuer
```

Vous devriez voir :
- **Issuer** : Let's Encrypt ou R3/R10/E5 (autorités Let's Encrypt)
- **notAfter** : Date d'expiration (90 jours après émission)

### Test 3 : Test SSL Labs

Visitez https://www.ssllabs.com/ssltest/ et entrez votre domaine. Vous devriez obtenir une note **A** ou **A+**.

### Test 4 : Redirection HTTP vers HTTPS

```bash
curl -I http://votredomaine.com
```

Réponse attendue : `HTTP/1.1 308 Permanent Redirect` avec `Location: https://votredomaine.com/`

---

## Dépannage

### Problème : "acme: error: 403"

**Cause** : Le serveur ACME ne peut pas atteindre votre serveur sur le port 80.

**Solution** :
1. Vérifiez que le port 80 est ouvert
2. Vérifiez que le DNS pointe vers la bonne IP
3. Attendez la propagation DNS

### Problème : "too many certificates already issued"

**Cause** : Rate limiting Let's Encrypt (5 certificats par semaine par domaine).

**Solution** :
1. Attendez une semaine
2. Utilisez le staging pour les tests : changez `acme_ca` en `https://acme-staging-v02.api.letsencrypt.org/directory`

### Problème : Certificat staging au lieu de production

**Cause** : Le Caddyfile utilise le serveur staging.

**Solution** :
1. Supprimez les données Caddy : `docker volume rm osfeed_caddy_data`
2. Vérifiez que `acme_ca` pointe vers `https://acme-v02.api.letsencrypt.org/directory`
3. Relancez : `docker compose up -d`

### Problème : "TLS-ALPN-01 challenge failed"

**Cause** : Certains hébergeurs (OVH) bloquent ce type de challenge.

**Solution** : Ajoutez dans le bloc `tls` :
```caddyfile
tls {
    issuer acme {
        disable_tlsalpn_challenge
    }
}
```

### Voir les logs détaillés

```bash
# Logs Caddy en temps réel
docker compose logs -f caddy

# Logs avec plus de détails
docker compose exec caddy caddy validate --config /etc/caddy/Caddyfile
```

---

## Renouvellement des Certificats

### Automatique

Caddy renouvelle automatiquement les certificats **30 jours avant expiration**. Aucune action requise.

### Vérifier le statut des certificats

```bash
# Lister les certificats gérés
docker compose exec caddy caddy list-certificates
```

### Forcer le renouvellement (si nécessaire)

```bash
# Supprimer les données et recréer
docker compose down
docker volume rm osfeed_caddy_data
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

---

## Checklist de Mise en Production

- [ ] DNS configuré et propagé
- [ ] Ports 80 et 443 ouverts (serveur + cloud)
- [ ] Domaine modifié dans `Caddyfile`
- [ ] Email ajouté dans la config globale Caddy
- [ ] Variables d'environnement configurées
- [ ] Conteneurs démarrés avec la config production
- [ ] Certificat obtenu (vérifier les logs)
- [ ] Test HTTPS fonctionnel
- [ ] Redirection HTTP→HTTPS active
- [ ] Note SSL Labs satisfaisante (A ou A+)

---

## Ressources

- [Documentation Caddy](https://caddyserver.com/docs/)
- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)
- [SSL Labs Test](https://www.ssllabs.com/ssltest/)
- [Let's Encrypt Rate Limits](https://letsencrypt.org/docs/rate-limits/)
