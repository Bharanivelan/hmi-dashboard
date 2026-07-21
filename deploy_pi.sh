#!/bin/bash
# =========================================================================
#  Automated Raspberry Pi Hardware Appliance Deployment Script
#  Configures I2C, installs dependencies, sets up Systemd services,
#  and configures the Chromium Kiosk Boot Animation.
# =========================================================================

echo "🚀 Starting Raspberry Pi Hardware Setup..."

# 1. Enable I2C natively
echo "[1/4] Enabling Hardware I2C..."
sudo raspi-config nonint do_i2c 0

# 2. Install Python Dependencies
echo "[2/4] Installing Python Libraries..."
sudo apt-get update
sudo apt-get install -y python3-pip
pip3 install adafruit-circuitpython-ads1x15 gpiozero

# 3. Create Backend Joystick Service
echo "[3/4] Creating hmi_controller Systemd Service..."
cat << EOF | sudo tee /etc/systemd/system/hmi-joystick.service
[Unit]
Description=SIYI Gimbal Joystick Controller
After=network.target

[Service]
# Automatically detect the current path and user
ExecStart=/usr/bin/python3 $(pwd)/hardware_controller/hmi_controller.py
WorkingDirectory=$(pwd)/
Restart=always
User=${SUDO_USER:-$USER}

[Install]
WantedBy=multi-user.target
EOF

# 4. Create Hardware Ignition Key Service
echo "[4/4] Creating hmi_ignition Systemd Service..."
cat << EOF | sudo tee /etc/systemd/system/hmi-ignition.service
[Unit]
Description=Hardware Ignition Key Monitor
After=network.target

[Service]
ExecStart=/usr/bin/python3 $(pwd)/hardware_controller/ignition_controller.py
WorkingDirectory=$(pwd)/
Restart=always
User=${SUDO_USER:-$USER}

[Install]
WantedBy=multi-user.target
EOF

# Enable and start the services
sudo systemctl daemon-reload
sudo systemctl enable hmi-joystick.service
sudo systemctl enable hmi-ignition.service
sudo systemctl restart hmi-joystick.service
sudo systemctl restart hmi-ignition.service

echo "✅ Backend Python services are now running permanently in the background!"


echo "🎉 Raspberry Pi Setup Complete! The joystick is now live."
