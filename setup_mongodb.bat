@echo off
echo ===================================================
echo MongoDB Setup Script for Django E-Commerce Platform
echo ===================================================
echo.

REM Check if MongoDB is installed
where mongod >nul 2>nul
if %errorlevel% neq 0 (
    echo ERROR: MongoDB is not installed or not in PATH
    echo Please install MongoDB first: https://www.mongodb.com/try/download/community
    pause
    exit /b 1
)

echo MongoDB found. Setting up authentication...
echo.

REM Create data directories if they don't exist
if not exist "C:\data\db" (
    echo Creating data directory...
    mkdir "C:\data\db"
)

if not exist "C:\data\log" (
    echo Creating log directory...
    mkdir "C:\data\log"
)

echo.
echo ===================================================
echo IMPORTANT: Follow these steps manually
echo ===================================================
echo.
echo 1. Stop MongoDB service if running:
echo    net stop MongoDB
echo.
echo 2. Start MongoDB without auth:
echo    mongod --port 27017 --dbpath "C:\data\db"
echo.
echo 3. In NEW command prompt, run:
echo    mongo --port 27017
echo.
echo 4. Create admin user:
echo    use admin
echo    db.createUser({
echo      user: "admin",
echo      pwd: "YourSecureAdminPassword123!",
echo      roles: [
echo        { role: "userAdminAnyDatabase", db: "admin" },
echo        { role: "readWriteAnyDatabase", db: "admin" }
echo      ]
echo    })
echo.
echo 5. Create app user:
echo    use ecommerce_db
echo    db.createUser({
echo      user: "ecommerce_user",
echo      pwd: "YourSecureAppPassword123!",
echo      roles: [
echo        { role: "readWrite", db: "ecommerce_db" }
echo      ]
echo    })
echo.
echo 6. Exit mongo shell: exit
echo.
echo 7. Stop mongod (Ctrl+C) and restart with auth:
echo    net start MongoDB
echo.
echo ===================================================
echo After completing above steps, update your .env file
echo with the credentials you created.
echo ===================================================
echo.
pause