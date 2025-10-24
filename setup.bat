@echo off
echo Creando entorno virtual...
python -m venv env

echo Activando entorno virtual...
call env\Scripts\activate

echo Instalando dependencias...
pip install -r requirements.txt

echo Configuracion completada. Ejecutando la aplicacion...
python main.py

pause
