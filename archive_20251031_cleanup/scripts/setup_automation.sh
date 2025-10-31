#!/bin/bash
# Full Pipeline Automation Setup
# Sets up weekly automated updates

PROJECT_DIR="/Users/souravamseekarmarti/Projects/uk_bus_analytics"
PYTHON_PATH="/usr/bin/python3"

echo "=========================================="
echo "UK Bus Analytics - Automation Setup"
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

echo ""
echo "Setting up weekly automated pipeline updates..."
echo "Schedule: Every Monday at 6:00 AM"
echo ""

# macOS - LaunchAgent
if [ "$SYSTEM" == "macos" ]; then
    PLIST_FILE="$HOME/Library/LaunchAgents/com.busanalytics.pipeline.plist"

    cat > "$PLIST_FILE" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.busanalytics.pipeline</string>

    <key>ProgramArguments</key>
    <array>
        <string>$PYTHON_PATH</string>
        <string>$PROJECT_DIR/scripts/smart_pipeline_update.py</string>
    </array>

    <key>WorkingDirectory</key>
    <string>$PROJECT_DIR</string>

    <key>StartCalendarInterval</key>
    <dict>
        <key>Weekday</key>
        <integer>1</integer>
        <key>Hour</key>
        <integer>6</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>

    <key>StandardOutPath</key>
    <string>$PROJECT_DIR/logs/pipeline_auto.log</string>

    <key>StandardErrorPath</key>
    <string>$PROJECT_DIR/logs/pipeline_auto_error.log</string>

    <key>RunAtLoad</key>
    <false/>
</dict>
</plist>
EOF

    # Load the LaunchAgent
    launchctl unload "$PLIST_FILE" 2>/dev/null
    launchctl load "$PLIST_FILE"

    echo "✅ macOS LaunchAgent installed: $PLIST_FILE"
    echo "   Schedule: Every Monday at 6:00 AM"
    echo ""
    echo "To check status: launchctl list | grep busanalytics"
    echo "To uninstall: launchctl unload $PLIST_FILE"

# Linux - Cron
elif [ "$SYSTEM" == "linux" ]; then
    # Add to crontab
    CRON_ENTRY="0 6 * * 1 cd $PROJECT_DIR && $PYTHON_PATH scripts/smart_pipeline_update.py >> logs/pipeline_auto.log 2>&1"

    # Check if entry already exists
    if crontab -l 2>/dev/null | grep -q "smart_pipeline_update.py"; then
        echo "⚠️  Cron job already exists"
    else
        (crontab -l 2>/dev/null; echo "$CRON_ENTRY") | crontab -
        echo "✅ Cron job installed"
        echo "   Schedule: Every Monday at 6:00 AM"
    fi

    echo ""
    echo "To view crontab: crontab -l"
    echo "To remove: crontab -e (then delete the line)"
fi

echo ""
echo "=========================================="
echo "Dashboard Auto-Start Setup (Optional)"
echo "=========================================="
echo ""
echo "To auto-start dashboard on system boot:"
echo ""

if [ "$SYSTEM" == "macos" ]; then
    echo "Run: ./scripts/setup_dashboard_service.sh"
elif [ "$SYSTEM" == "linux" ]; then
    echo "Run: sudo ./scripts/setup_dashboard_service.sh"
fi

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Next pipeline update: Next Monday at 6:00 AM"
echo "Logs will be saved to: $PROJECT_DIR/logs/"
echo ""
echo "To test now: python3 scripts/smart_pipeline_update.py"
