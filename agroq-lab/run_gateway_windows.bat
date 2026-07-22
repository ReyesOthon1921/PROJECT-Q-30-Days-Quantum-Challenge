@echo off
setlocal
if "%AGROQ_SECRET_KEY%"=="" (
  echo Set AGROQ_SECRET_KEY to a long, unique local value before LAN startup.
  exit /b 1
)
set "AGROQ_GATEWAY_NAME=agroq-acre-gateway"
set "AGROQ_SITE_ID=AGQ-SITE-001"
set "AGROQ_DEPLOYMENT_MODE=field"
set "AGROQ_BIND_HOST=0.0.0.0"
set "AGROQ_PORT=5000"
set "AGROQ_DEBUG=false"
python app.py
