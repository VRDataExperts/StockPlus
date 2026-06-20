#!/usr/bin/env bash
# StocksPlus VM provisioning — run ONCE on the DigitalOcean Droplet as root.
#   ssh root@YOUR_DROPLET_IP
#   bash provision.sh
#
# Installs: Java, IB Gateway (headless via Xvfb + IBC), Python venv + ib_async.
# It does NOT start trading. It prepares the box so you can run the connection test.
set -euo pipefail

# -------- config you can edit --------
IBC_VERSION="3.20.0"                       # check github.com/IbcAlpha/IBC/releases for latest
TRADING_MODE="paper"                       # 'paper' or 'live'
APP_USER="trader"
REPO_URL="https://github.com/VRDataExperts/StockPlus.git"
# -------------------------------------

echo "==> System packages"
apt-get update -y
apt-get install -y openjdk-17-jre xvfb x11vnc unzip wget curl git \
                   python3-venv python3-pip

echo "==> Create app user"
id -u "$APP_USER" &>/dev/null || adduser --disabled-password --gecos "" "$APP_USER"

echo "==> Download IB Gateway (stable, standalone)"
cd /opt
wget -q https://download2.interactivebrokers.com/installers/ibgateway/stable-standalone/ibgateway-stable-standalone-linux-x64.sh -O ibgateway-installer.sh
chmod +x ibgateway-installer.sh
# Silent install to /opt/ibgateway
yes "" | ./ibgateway-installer.sh -q -dir /opt/ibgateway || true

echo "==> Install IBC (keeps IB Gateway logged in & alive)"
cd /opt
wget -q "https://github.com/IbcAlpha/IBC/releases/download/${IBC_VERSION}/IBCLinux-${IBC_VERSION}.zip" -O ibc.zip
mkdir -p /opt/ibc && unzip -o ibc.zip -d /opt/ibc
chmod +x /opt/ibc/*.sh /opt/ibc/scripts/*.sh || true

echo "==> IBC config (credentials go in a SEPARATE, gitignored file)"
mkdir -p /opt/ibc/config
cat > /opt/ibc/config/config.ini <<EOF
# Fill these in on the VM only. NEVER commit this file.
IbLoginId=YOUR_IBKR_USERNAME
IbPassword=YOUR_IBKR_PASSWORD
TradingMode=${TRADING_MODE}
AcceptIncomingConnectionAction=accept
ReadOnlyApi=no
OverrideTwsApiPort=4002
EOF
chmod 600 /opt/ibc/config/config.ini

echo "==> Python environment for the engine"
sudo -u "$APP_USER" bash <<EOSU
cd /home/${APP_USER}
[ -d StockPlus ] || git clone ${REPO_URL}
cd StockPlus
python3 -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install -r engine/requirements.txt
EOSU

cat <<'NOTE'

============================================================
 DONE. Next manual steps:
 1) Edit /opt/ibc/config/config.ini  -> put your IBKR paper username/password.
 2) Start IB Gateway headless:
        xvfb-run -a /opt/ibc/scripts/ibcstart.sh --gateway --mode=paper
    (we'll turn this into a systemd service once the connection test passes)
 3) From the repo venv, run the connection test:
        cd /home/trader/StockPlus && . .venv/bin/activate
        python engine/test_connection.py
============================================================
NOTE
