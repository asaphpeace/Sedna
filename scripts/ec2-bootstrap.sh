#!/usr/bin/env bash
# Run once on a fresh Ubuntu 22.04/24.04 EC2 instance (as ec2-user/ubuntu, via SSH).
# Installs Docker + Compose plugin and clones the repo. Does NOT start the app —
# that happens in scripts/deploy.sh after you've filled in .env.
set -euo pipefail

echo "== Updating packages =="
sudo apt-get update -y
sudo apt-get upgrade -y

echo "== Installing Docker =="
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker "$USER"

echo "== Installing git =="
sudo apt-get install -y git

echo "== Enabling swap (free-tier t2/t3.micro has only 1GB RAM) =="
if [ ! -f /swapfile ]; then
  sudo fallocate -l 2G /swapfile
  sudo chmod 600 /swapfile
  sudo mkswap /swapfile
  sudo swapon /swapfile
  echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
fi

echo "== Cloning repo =="
read -rp "Git repo URL to clone: " REPO_URL
git clone "$REPO_URL" ~/sedna
cd ~/sedna

echo "== Done =="
echo "Next steps:"
echo "  1. cp .env.production.example .env && nano .env   (fill in real values)"
echo "  2. Point your domain's DNS A record at this instance's public IP"
echo "  3. Log out and back in (for the docker group to take effect), then run scripts/deploy.sh"
