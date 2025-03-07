@echo off
echo Creating Spades Master Web project structure...

:: Create main directories
mkdir backend
mkdir backend\api
mkdir backend\services
mkdir backend\models
mkdir backend\utils
mkdir frontend
mkdir frontend\static
mkdir frontend\static\css
mkdir frontend\static\js
mkdir frontend\static\img
mkdir frontend\templates

:: Create backend files
echo # Backend initialization > backend\__init__.py
echo # Flask application > backend\app.py

:: Create API files
echo # API initialization > backend\api\__init__.py
echo # Server profiles endpoints > backend\api\server_profiles.py
echo # Execution endpoints > backend\api\execution.py
echo # Results endpoints > backend\api\results.py

:: Create services files
echo # Services initialization > backend\services\__init__.py
echo # Job management service > backend\services\job_manager.py

:: Create models files
echo # Models initialization > backend\models\__init__.py
echo # Server profile model > backend\models\server_profile.py

:: Create utils files
echo # Utils initialization > backend\utils\__init__.py
echo # Logging utilities > backend\utils\logging_utils.py
echo # SSH utilities > backend\utils\ssh_utils.py
echo # WebSocket updater > backend\utils\socket_updater.py

:: Create frontend files
echo /* Main application styles */ > frontend\static\css\styles.css

echo // Main JavaScript file > frontend\static\js\main.js
echo // Profiles management > frontend\static\js\profiles.js
echo // Execution management > frontend\static\js\execution.js
echo // Results visualization > frontend\static\js\results.js

:: Create HTML templates
echo <!-- Base template with menu --> > frontend\templates\base.html
echo <!-- Dashboard template --> > frontend\templates\dashboard.html
echo <!-- Profiles management template --> > frontend\templates\profiles.html
echo <!-- Execution template --> > frontend\templates\execution.html
echo <!-- Results template --> > frontend\templates\results.html

:: Create root files
echo # Web application entry point > app.py
echo # Standalone application launcher > app_launcher.py
echo # Project dependencies > requirements.txt
echo # Installation script > setup.py
echo # Spades Master Web Documentation > README.md

echo Project structure created successfully!