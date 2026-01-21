#!/bin/bash
# Script de setup initial pour serveur Ubuntu 22.04/24.04
# Ce script installe Docker et prepare l'environnement pour OSFeed

set -e

echo "=========================================="
echo "  OSFeed - Setup Serveur Production"
echo "=========================================="

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Fonction pour afficher les messages
info() { echo -e "${GREEN}[INFO]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Verification root
if [ "$EUID" -ne 0 ]; then
    error "Ce script doit etre execute en tant que root"
    echo "Utilisez: sudo $0"
    exit 1
fi

# Mise a jour du systeme
info "Mise a jour du systeme..."
apt update && apt upgrade -y

# Installation des dependances de base
info "Installation des outils de base..."
apt install -y \
    curl \
    wget \
    git \
    nano \
    htop \
    ufw \
    fail2ban

# Installation de Docker
if command -v docker &> /dev/null; then
    info "Docker est deja installe"
    docker --version
else
    info "Installation de Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh

    # Ajouter l'utilisateur au groupe docker (si pas root)
    if [ -n "$SUDO_USER" ]; then
        usermod -aG docker "$SUDO_USER"
        info "Utilisateur $SUDO_USER ajoute au groupe docker"
    fi
fi

# Verification de Docker Compose
info "Verification de Docker Compose..."
docker compose version

# Configuration du pare-feu
info "Configuration du pare-feu UFW..."
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable
info "Pare-feu configure (SSH, HTTP, HTTPS autorises)"

# Configuration de fail2ban
info "Configuration de fail2ban..."
systemctl enable fail2ban
systemctl start fail2ban

# Creation du dossier pour OSFeed
INSTALL_DIR="/opt/osfeed"
if [ ! -d "$INSTALL_DIR" ]; then
    info "Creation du dossier $INSTALL_DIR..."
    mkdir -p "$INSTALL_DIR"
fi

# Afficher les informations finales
echo ""
echo "=========================================="
echo -e "${GREEN}  Setup termine avec succes!${NC}"
echo "=========================================="
echo ""
echo "Prochaines etapes:"
echo "1. Cloner le projet: cd $INSTALL_DIR && git clone <URL_REPO> ."
echo "2. Configurer .env: cp .env.example .env && nano .env"
echo "3. Configurer le domaine dans Caddyfile"
echo "4. Lancer: docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build"
echo ""
echo "IP du serveur: $(curl -s ifconfig.me 2>/dev/null || echo 'Non disponible')"
echo ""
