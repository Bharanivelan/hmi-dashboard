#!/bin/bash
# =========================================================================
#  Automated Raspberry Pi ALL-IN-ONE Deployment Script
#  Installs Nginx, hosts the Dashboard, configures go2rtc (ARM version),
#  enables I2C, installs python hardware deps, and sets up all Systemd services.
# =========================================================================

echo "🚀 Starting Raspberry Pi All-in-One Setup..."

# 1. Update and install Nginx
echo "[1/6] Installing Nginx..."
sudo apt-get update
sudo apt-get install -y nginx

# 2. Deploy the Dashboard UI
echo "[2/6] Deploying Web UI..."
sudo rm -rf /var/www/html/*
sudo cp index.html /var/www/html/
sudo cp styles.css /var/www/html/
sudo cp app.js /var/www/html/
sudo systemctl restart nginx
echo "✅ UI is now live on the Pi's IP address"

# 3. Setup go2rtc Video Streamer (ARM64 version for Pi)
echo "[3/6] Installing go2rtc for ARM..."
sudo mkdir -p /opt/go2rtc
# Download the latest Linux ARM64 version of go2rtc
sudo wget -O /opt/go2rtc/go2rtc https://github.com/AlexxIT/go2rtc/releases/latest/download/go2rtc_linux_arm64
sudo chmod +x /opt/go2rtc/go2rtc
sudo cp go2rtc.yaml /opt/go2rtc/go2rtc.yaml

# Create Systemd Service for go2rtc
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

# 4. Enable Hardware I2C
echo "[4/6] Enabling Hardware I2C..."
sudo raspi-config nonint do_i2c 0

# 5. Install Python Dependencies
echo "[5/6] Installing Python Libraries..."
sudo apt-get install -y python3-pip
pip3 install adafruit-circuitpython-ads1x15 gpiozero

# 6. Create Hardware Services (Joystick & Ignition)
echo "[6/6] Creating Hardware Systemd Services..."
cat << EOF | sudo tee /etc/systemd/system/hmi-joystick.service
[Unit]
Description=SIYI Gimbal Joystick Controller
After=network.target

[Service]
ExecStart=/usr/bin/python3 /home/pi/hmi-dashboard/hardware_controller/hmi_controller.py
WorkingDirectory=/home/pi/hmi-dashboard/
Restart=always
User=pi

[Install]
WantedBy=multi-user.target
EOF

cat << EOF | sudo tee /etc/systemd/system/hmi-ignition.service
[Unit]
Description=Hardware Ignition Key Monitor
After=network.target

[Service]
ExecStart=/usr/bin/python3 /home/pi/hmi-dashboard/hardware_controller/ignition_controller.py
WorkingDirectory=/home/pi/hmi-dashboard/
Restart=always
User=pi

[Install]
WantedBy=multi-user.target
EOF

# Enable and start ALL services
sudo systemctl daemon-reload
sudo systemctl enable go2rtc.service
sudo systemctl enable hmi-joystick.service
sudo systemctl enable hmi-ignition.service
sudo systemctl restart go2rtc.service
sudo systemctl restart hmi-joystick.service
sudo systemctl restart hmi-ignition.service

echo "================================================================"
echo "⚠️  MANUAL STEP REQUIRED FOR KIOSK ⚠️"
echo "To make the Raspberry Pi boot to the Ignition Animation:"
echo "1. Run: nano ~/.config/wayfire.ini  (or /etc/xdg/openbox/autostart)"
echo "2. Add this exact line to the autostart section:"
echo "   chromium-browser --kiosk file:///home/pi/ignition.html"
echo "================================================================"

echo "🎉 All-in-One Raspberry Pi Setup Complete!"
echo "Your Web UI, Video Stream, and Hardware Controls are all running on this Pi!"
