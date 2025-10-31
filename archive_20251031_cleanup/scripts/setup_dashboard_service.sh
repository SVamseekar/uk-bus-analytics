#!/bin/bash
# Dashboard Auto-Start Service Setup
# Keeps dashboard running 24/7

PROJECT_DIR="/Users/souravamseekarmarti/Projects/uk_bus_analytics"
PYTHON_PATH="/usr/bin/python3"

echo "=========================================="
echo "Dashboard Auto-Start Service Setup"
echo "=========================================="
echo ""

# Check if running on macOS or Linux
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "Detected: macOS"
    SYSTEM="macos"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "Detected: Linux"
    SYSTEM="linux"
else
    echo "Unsupported OS: $OSTYPE"
    exit 1
fi

# macOS - LaunchAgent for dashboard
if [ "$SYSTEM" == "macos" ]; then
    PLIST_FILE="$HOME/Library/LaunchAgents/com.busanalytics.dashboard.plist"

    cat > "$PLIST_FILE" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.busanalytics.dashboard</string>

    <key>ProgramArguments</key>
    <array>
        <string>$PYTHON_PATH</string>
        <string>-m</string>
        <string>streamlit</string>
        <string>run</string>
        <string>$PROJECT_DIR/dashboard/Home.py</string>
        <string>--server.port=8501</string>
        <string>--server.headless=true</string>
    </array>

    <key>WorkingDirectory</key>
    <string>$PROJECT_DIR</string>

    <key>RunAtLoad</key>
    <true/>

    <key>KeepAlive</key>
    <true/>

    <key>StandardOutPath</key>
    <string>$PROJECT_DIR/logs/dashboard.log</string>

    <key>StandardErrorPath</key>
    <string>$PROJECT_DIR/logs/dashboard_error.log</string>
</dict>
</plist>
EOF

    # Load the LaunchAgent
    launchctl unload "$PLIST_FILE" 2>/dev/null
    launchctl load "$PLIST_FILE"

    echo "✅ Dashboard service installed"
    echo "   Access at: http://localhost:8501"
    echo ""
    echo "Service will:"
    echo "  • Start automatically on system boot"
    echo "  • Restart if it crashes"
    echo "  • Run continuously in background"
    echo ""
    echo "To stop: launchctl unload $PLIST_FILE"
    echo "To restart: launchctl kickstart -k gui/\$(id -u)/com.busanalytics.dashboard"

# Linux - Systemd service
elif [ "$SYSTEM" == "linux" ]; then
    if [ "$EUID" -ne 0 ]; then
        echo "❌ Error: Must run with sudo on Linux"
        exit 1
    fi

    SERVICE_FILE="/etc/systemd/system/busanalytics-dashboard.service"

    cat > "$SERVICE_FILE" << EOF
[Unit]
Description=UK Bus Analytics Dashboard
After=network.target

[Service]
Type=simple
User=$SUDO_USER
WorkingDirectory=$PROJECT_DIR
ExecStart=$PYTHON_PATH -m streamlit run dashboard/Home.py --server.port=8501 --server.headless=true
Restart=always
RestartSec=10
StandardOutput=append:$PROJECT_DIR/logs/dashboard.log
StandardError=append:$PROJECT_DIR/logs/dashboard_error.log

[Install]
WantedBy=multi-user.target
EOF

    # Reload systemd and enable service
    systemctl daemon-reload
    systemctl enable busanalytics-dashboard.service
    systemctl start busanalytics-dashboard.service

    echo "✅ Dashboard service installed"
    echo "   Access at: http://localhost:8501"
    echo ""
    echo "Service commands:"
    echo "  sudo systemctl status busanalytics-dashboard"
    echo "  sudo systemctl restart busanalytics-dashboard"
    echo "  sudo systemctl stop busanalytics-dashboard"
fi

echo ""
echo "=========================================="
echo "Dashboard is now running!"
echo "=========================================="
echo ""
echo "Open in browser: http://localhost:8501"
echo "Logs: tail -f logs/dashboard.log"
