#!/bin/bash
cd /home/noegest/Noethys-Matthania
source /home/noegest/envnoethys/bin/activate
cd ./noethys
python3 -m Noethys
read -n1 -r -p "Tapez une touche pour finir..."
