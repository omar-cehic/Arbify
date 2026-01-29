# PowerShell script to run both frontend and backend for development

# Function to display colored text
function Write-ColorText {
    param (
        [string]$Text,
        [string]$Color = "White"
    )
    Write-Host $Text -ForegroundColor $Color
}

Write-ColorText "Starting Arbify Development Environment..." "Green"
Write-ColorText "===================================" "Green"

# Start the backend server
Write-ColorText "Starting the backend server..." "Cyan"
# Use Start-Process to run in a new window, keeping the current window free
# We use 'python -m uvicorn' to ensure we use the python from the current environment
Start-Process -NoNewWindow powershell -ArgumentList "-Command", "& {cd $PSScriptRoot; python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000; Read-Host 'Press Enter to exit'}"

# Wait a moment for the backend to start
Start-Sleep -Seconds 3

# Start the frontend (Vite) server
Write-ColorText "Starting the frontend Vite server..." "Yellow"
Start-Process -NoNewWindow powershell -ArgumentList "-Command", "& {cd $PSScriptRoot/frontend; npm run dev; Read-Host 'Press Enter to exit'}"

Write-ColorText "Both servers are starting. Check the terminal windows for details." "Green"
Write-ColorText "Backend URL: http://localhost:8000" "Cyan"
Write-ColorText "Frontend URL: http://localhost:5173" "Yellow"
Write-ColorText "===================================" "Green"
Write-ColorText "Press Ctrl+C in each terminal window to stop the servers when finished." "White"