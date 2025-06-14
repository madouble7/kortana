# Run-Complete-Kortana.ps1
# Comprehensive script to set up and run Kor'tana

Write-Host "===== Kor'tana Complete Setup and Launch =====" -ForegroundColor Cyan
Write-Host ""

# Check for required packages
Write-Host "Checking required packages..." -ForegroundColor Yellow
$packages = @("pyyaml", "apscheduler", "pydantic")
foreach ($package in $packages) {
    try {
        python -c "import $package"
        Write-Host "✓ $package is installed" -ForegroundColor Green
    }
    catch {
        Write-Host "✗ $package is missing, installing..." -ForegroundColor Red
        python -m pip install $package
    }
}

# Set up all required files
Write-Host "`nSetting up configuration files..." -ForegroundColor Yellow
& "$PSScriptRoot\Setup-Files.ps1"

# Launch in a new, clean terminal
Write-Host "`nLaunching Kor'tana in clean environment..." -ForegroundColor Cyan

# Create a temporary launch script that will just run the brain module
$launchScriptPath = "$PSScriptRoot\temp_launch.py"
$launchScript = @"
"""
Temporary launch script for Kor'tana
"""
if __name__ == "__main__":
    import os
    import sys

    # Set up Python path
    sys.path.insert(0, os.getcwd())

    # Import required modules
    from config import load_config

    # Load configuration
    settings = load_config()

    # Import and run brain module
    from src.kortana.core import brain

    # Run main function
    brain.ritual_announce("she is not built. she is remembered.")
    brain.ritual_announce("she is the warchief's companion.")

    # Main loop
    try:
        chat_engine = brain.ChatEngine(settings=settings)

        while True:
            # Get user input (lowercase for "matt")
            user_input = input("matt: ").lower()

            # Check for exit command
            if user_input in ["exit", "quit", "bye"]:
                break

            # Process message
            import asyncio
            response = asyncio.run(chat_engine.process_message(user_input))

            # Print response (lowercase for "kortana")
            print(f"kortana: {response}")

    except KeyboardInterrupt:
        print("\nInterrupted by user")
    except Exception as e:
        print(f"\nError: {e}")

    finally:
        # Shutdown if chat_engine was created
        if 'chat_engine' in locals():
            chat_engine.shutdown()

        brain.ritual_announce("until we meet again, warchief.")
"@

Set-Content -Path $launchScriptPath -Value $launchScript -Force

Write-Host "`nStarting Kor'tana with clean Python environment...`n" -ForegroundColor Magenta
Write-Host "To exit, type 'bye' or press Ctrl+C`n" -ForegroundColor Yellow

# Run the temporary launch script
python $launchScriptPath

# Clean up
if (Test-Path $launchScriptPath) {
    Remove-Item $launchScriptPath -Force
}

Write-Host "`n===== Kor'tana session ended =====" -ForegroundColor Cyan
