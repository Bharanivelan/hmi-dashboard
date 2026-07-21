#!/bin/bash
echo "Installing HMI Controller Service..."

sudo cp hmi_controller.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable hmi_controller.service
sudo systemctl start hmi_controller.service

echo "Service installed and started!"
echo "Check status with: sudo systemctl status hmi_controller.service"
echo "View logs with: journalctl -u hmi_controller.service -f"
