Installer Noethys sur Linux
===========================
L'installation de Noethys sur Linux se fait obligatoirement depuis les sources.
Ci-dessous vous allez cloner le code source depuis Github et installer les dépendances.

Installation pas à pas sur Ubuntu 22.04 Noethys-Matthania
---------------------------------------------------------
Lancez dans votre terminal Linux les commandes suivantes :

```
# creation d'un groupe pour les applications de gestion et autorisation rwx au groupe
sudo groupadd noegest
sudo usermod -aG noegest <myname>
sudo mkdir /home/noegest
sudo chgrp -R noegest /home/noegest
sudo cdmod 775 -R /home/noegest
cd /home/noegest
# creation d'un environnement de travail selon ma version de python
sudo apt install python3.10-venv
sudo python3 -m venv envnoethys
sudo chgrp noegest envnoethys
source envnoethys/bin/activate
# le prompt affiche l'environnement activé
# installation des paquets
sudo apt-get install git curl libsdl2-mixer-2.0-0 libsdl2-image-2.0-0 libsdl2-2.0-0 python3-pip python3-pyscard python3-dev default-libmysqlclient-dev build-essential
sudo apt install pkg-config
pip3 install --upgrade pip
pip3 install -U -f https://extras.wxpython.org/wxPython4/extras/linux/gtk3/ubuntu-22.04 wxPython
git clone https://github.com/BrunelJacques/Noethys-Matthania
cd Noethys-Matthania
pip3 install -r requirements.txt
cp noethys/Doc/lanceur_linux.sh ./lancer_noethys.sh
chmod +x ./lancer_noethys.sh
deactivate
# lancement de noethys
source ../envnoethys/bin/activate
python3 noethys/Noethys.py
```
pour une recherche par la barre 'activités'
```
sudo mkdir /usr/local/share/applications
sudo cp /home/noegest/Noethys-Matthania/noethys/Doc/lancer_noethys.desktop  /usr/local/share/applications/
sudo chmod +x /usr/local/share/applications/lancer_noethys.desktop
sudo chgrp noegest /usr/local/share/applications/lancer_noethys.desktop
```
Chaque user pourra ainsi 'voir' Noethys-Matthania et le mettre dans les favoris
ou lancer comme un programme '/home/noegest/Noethys-Matthania/lancer_noethys.sh'

pour un update
```
cp /home/noegest/Noethys-Matthania
git pull https://github.com/BrunelJacques/Noethys-Matthania
```

Installation manuelle sur Linux
-------------------------------
si échec du 'git clone' télécharger les sources et extraire les fichiers

pour wxpython existe aussi la version ubuntu-20
extras.wxpython.org/wxPython4/extras/linux/gtk3/ubuntu-20.04 wxPython

'mysqlclient' peut être enlevé de requirements.txt pour installer le reste.
Si echec pip3 install mysqlclient
```
sudo apt-get install python-mysqldb
pip3 install mysql-connector-python
```

préconisations Noethys original master:
https://github.com/Noethys/Noethys/tree/master/noethys/Doc

