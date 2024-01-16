Noethys-Matthania
==================
Le célébre outil de gestion Noethys a été repris par Matthania pour ses besoin de gestion de camps.
Les spécificités ajoutées permettent de gérer des articles et des tarifs avec des modules de réductions spécifiques.
L'autre particularité est de gérer des pièces changeant d'état: Devis, Réservation, Commande, Facture, Avoir.

Plus d'infos sur les fonctions de base de Noethys sur : www.noethys.com

Les premières modification ont été apportées à partir de Noethys 2016, à l'occasion de la transposition en python3 un merge a été fait à partir de Noethys 1.3.0.8 (30/03/2022)
Par simplification La compatibilité avec Python27 n'est plus assurée, ni la traduction dans une autre langue.

Installation sur Windows
------------------
voir 'noethys/Doc/install_windows.md'

Installation sur Ubuntu 22.04
------------------

Lancez dans votre console Linux les commandes suivantes :
```
sudo apt-get install git curl libsdl2-mixer-2.0-0 libsdl2-image-2.0-0 libsdl2-2.0-0 python3-pip python3-pyscard python3-dev default-libmysqlclient-dev build-essential
sudo apt install pkg-config
pip3 install -U -f https://extras.wxpython.org/wxPython4/extras/linux/gtk3/ubuntu-22.04 wxPython
git clone https://github.com/BrunelJacques/Noethys-Matthania
pip3 install -r Noethys/requirements.txt
python3 Noethys/noethys/Noethys.py
```
pour plus de détail voir 'noethys/Doc/install_linux.md'


