#!/bin/bash
cd /home/noegest/Noethys-Matthania
source /home/noegest/Noethys-Matthania/venv/bin/activate
cd ./noethys
python3 -m Noethys
read -n1 -r -p "Tapez une touche pour finir..."
