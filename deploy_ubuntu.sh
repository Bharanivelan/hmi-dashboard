#!/bin/bash
# =========================================================================
#  Automated Ubuntu Server (192.168.1.4) Deployment Script
#  Installs Nginx, hosts the Dashboard, and configures go2rtc.
# =========================================================================

echo "🚀 Starting Ubuntu Deployment..."

# 1. Update and install Nginx safely
echo "[1/4] Installing Nginx..."
sudo apt-get update
sudo apt-get install -y nginx

# 2. Deploy the Dashboard UI
echo "[2/4] Deploying Web UI..."
sudo rm -rf /var/www/html/*
sudo cp index.html /var/www/html/
sudo cp styles.css /var/www/html/
sudo cp app.js /var/www/html/
sudo cp ignition.html /var/www/html/
sudo cp -r assets /var/www/html/
sudo systemctl restart nginx
echo "✅ UI is now live at http://192.168.1.4"

# 3. Setup go2rtc Video Streamer
echo "[3/4] Installing go2rtc..."
sudo mkdir -p /opt/go2rtc
# Download the latest Linux AMD64 version of go2rtc
sudo wget -O /opt/go2rtc/go2rtc https://github.com/AlexxIT/go2rtc/releases/latest/download/go2rtc_linux_amd64
sudo chmod +x /opt/go2rtc/go2rtc
# Copy our custom configuration
sudo cp go2rtc.yaml /opt/go2rtc/go2rtc.yaml

# 4. Create Systemd Service for go2rtc
echo "[4/4] Configuring Systemd Service..."
cat << EOF | sudo tee /etc/systemd/system/go2rtc.service
[Unit]
Description=go2rtc WebRTC Camera Streamer
After=network.target

[Service]
ExecStart=/opt/go2rtc/go2rtc -config /opt/go2rtc/go2rtc.yaml
WorkingDirectory=/opt/go2rtc
Restart=always
User=root

[Install]
WantedBy=multi-user.target
EOF

# Enable and start the service
sudo systemctl daemon-reload
sudo systemctl enable go2rtc.service
sudo systemctl restart go2rtc.service

echo "✅ go2rtc is now streaming video in the background!"
echo "🎉 Ubuntu Server Setup Complete!"
