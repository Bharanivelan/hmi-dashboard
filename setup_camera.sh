#!/bin/bash
# ═══════════════════════════════════════════════════════════════════
#  setup_camera.sh  —  Aerostat HMI Camera Integration Setup Script
#  Run this ONCE on the Raspberry Pi to install everything.
#  After first run, use start_camera.sh to launch services.
# ═══════════════════════════════════════════════════════════════════

set -e   # exit on any error

DASHBOARD_DIR="$(cd "$(dirname "$0")" && pwd)"
GO2RTC_VERSION="1.9.4"
ARCH=$(uname -m)

echo ""
echo "╔════════════════════════════════════════════╗"
echo "║   AEROSTAT HMI — Camera Setup             ║"
echo "╚════════════════════════════════════════════╝"
echo ""

# ── Detect Pi architecture ───────────────────────────────────────
if [ "$ARCH" = "aarch64" ]; then
    GO2RTC_BINARY="go2rtc_linux_arm64"
elif [ "$ARCH" = "armv7l" ]; then
    GO2RTC_BINARY="go2rtc_linux_arm"
else
    GO2RTC_BINARY="go2rtc_linux_amd64"
fi

echo "[1/4] Downloading go2rtc ($GO2RTC_BINARY)..."
wget -q --show-progress \
    "https://github.com/AlexxIT/go2rtc/releases/download/v${GO2RTC_VERSION}/${GO2RTC_BINARY}" \
    -O "$DASHBOARD_DIR/go2rtc"
chmod +x "$DASHBOARD_DIR/go2rtc"
echo "      ✓ go2rtc downloaded"

echo ""
echo "[2/4] Installing Python dependencies..."
pip3 install --quiet websockets
echo "      ✓ websockets installed"

echo ""
echo "[3/4] Creating launch script (start_camera.sh)..."
cat > "$DASHBOARD_DIR/start_camera.sh" << 'LAUNCH'
#!/bin/bash
# start_camera.sh — Launch camera services for Aerostat HMI
DASHBOARD_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "[AerostatHMI] Starting go2rtc (WebRTC video bridge)..."
"$DASHBOARD_DIR/go2rtc" -config "$DASHBOARD_DIR/go2rtc.yaml" &
GO2RTC_PID=$!

echo "[AerostatHMI] Starting gimbal control bridge (port 8765)..."
python3 "$DASHBOARD_DIR/gimbal_server.py" &
GIMBAL_PID=$!

echo "[AerostatHMI] ✓ Both services running."
echo "  go2rtc   PID: $GO2RTC_PID  (WebRTC on :1984)"
echo "  Gimbal   PID: $GIMBAL_PID  (WebSocket on :8765)"
echo ""
echo "Open the dashboard at: http://localhost"
echo "Press Ctrl+C to stop all services."

trap "kill $GO2RTC_PID $GIMBAL_PID 2>/dev/null; echo 'Services stopped.'" INT TERM
wait
LAUNCH
chmod +x "$DASHBOARD_DIR/start_camera.sh"
echo "      ✓ start_camera.sh created"

echo ""
echo "[4/4] Creating systemd service (optional auto-start on boot)..."
sudo tee /etc/systemd/system/aerostat-hmi.service > /dev/null << SERVICE
[Unit]
Description=Aerostat HMI Camera Services
After=network.target

[Service]
Type=forking
WorkingDirectory=$DASHBOARD_DIR
ExecStart=$DASHBOARD_DIR/start_camera.sh
Restart=on-failure
RestartSec=5
User=$(whoami)

[Install]
WantedBy=multi-user.target
SERVICE

sudo systemctl daemon-reload
echo "      ✓ systemd service created"
echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║  SETUP COMPLETE                                            ║"
echo "╠════════════════════════════════════════════════════════════╣"
echo "║  NEXT STEPS:                                               ║"
echo "║  1. Edit go2rtc.yaml  → set your CAMERA_IP + STREAM_PATH  ║"
echo "║  2. Edit gimbal_server.py → set CAMERA_IP                  ║"
echo "║  3. Run:  ./start_camera.sh                                ║"
echo "║                                                            ║"
echo "║  Auto-start on boot:                                       ║"
echo "║     sudo systemctl enable aerostat-hmi                     ║"
echo "║     sudo systemctl start  aerostat-hmi                     ║"
echo "╚════════════════════════════════════════════════════════════╝"
