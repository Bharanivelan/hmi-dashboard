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
# Replace /home/pi with the actual path to your hardware_controller folder
ExecStart=/usr/bin/python3 /home/pi/hmi-dashboard/hardware_controller/hmi_controller.py
WorkingDirectory=/home/pi/hmi-dashboard/
Restart=always
User=pi

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
ExecStart=/usr/bin/python3 /home/pi/hmi-dashboard/hardware_controller/ignition_controller.py
WorkingDirectory=/home/pi/hmi-dashboard/
Restart=always
User=pi

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

# 5. Configure Kiosk Mode
echo "================================================================"
echo "⚠️  MANUAL STEP REQUIRED FOR KIOSK ⚠️"
echo "To make the Raspberry Pi boot to the Ignition Animation:"
echo "1. Run: nano ~/.config/wayfire.ini  (or /etc/xdg/openbox/autostart)"
echo "2. Add this exact line to the autostart section:"
echo "   chromium-browser --kiosk file:///home/pi/hmi-dashboard/ignition.html"
echo "================================================================"

echo "🎉 Raspberry Pi Setup Complete! The joystick is now live."
