Installer Noethys sur Linux
==================
L'installation de Noethys sur Linux se fait obligatoirement depuis les sources.
Ci-dessous vous allez cloner le code source depuis Github et installer les dépendances.

Installation pas à pas sur Ubuntu 22.04
------------------
Lancez dans votre terminal Linux les commandes suivantes :

```
# creation d'un groupe pour les applications de gestion et autorisation rwx au groupe
sudo groupadd noegest
sudo usermod -aG noegest <myname>
sudo mkdir /home/noegest
sudo chgrp -R noegest /home/noegest
sudo 775 -R /home/noegest
cd /home/noegest
# creation d'un environnement de travail selon ma version de python
sudo apt install python3.10-venv
python3 -m venv envnoethys
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
cp noethys/Doc/lanceur_linux.sh /home/noegest/Noethys-Matthania/lancer_noethys.sh
sudo cp noethys/Doc/lancer_noethys.desktop  /usr/local/share/applications/
chmod +x /home/noegest/Noethys-Matthania/lancer_noethys.sh
deactivate
# lancement de noethys
source ../envnoethys/bin/activate
python3 noethys/Noethys.py
```
ou lancer par le desktop accessible dans les applications vues par Gnome

Installation manuelle sur Linux
------------------
si échec du 'git clone' télécharger les sources et extraire les fichiers

pour wxpython existe aussi la version ubuntu-22
extras.wxpython.org/wxPython4/extras/linux/gtk3/ubuntu-22.04 wxPython

Si echec pip3 install mysqlclient
```
sudo apt-get install python-mysqldb
pip3 install mysql-connector-python
```

préconisation Noethys original:
Téléchargez le code source de Noethys depuis Github puis installez les dépendances suivantes :
- python 3+ 
- python-wxgtk3.0 (Bibliothèque graphique wxPython)
- python-mysqldb (Pour l'utilisation en mode réseau)
- python-dateutil (Manipulation des dates)
- python-numpy (Calculs avancés)
- python-pil (Traitement des photos)
- python-reportlab (Création des PDF)
- python-matplotlib (Création de graphes)
- python-xlrd (Traitement de fichiers Excel)
- python-crypto (pour crypter les sauvegardes)
- python-xlsxwriter (pour les exports format excel)
- python-pyscard (pour pouvoir configurer les procédures de badgeage)
- python-opencv (pour la détection automatique des visages)
- python-pip (qui permet d'installer pyttsx et icalendar)
- python-espeak (pour la synthèse vocale, associé à pyttsx)
- python-appdirs (pour rechercher les répertoires de stockage des données)
- python-psutil (infos système)
- python-paramiko (Prise en charge SSH)
- python-lxml (Validation XSD des bordereaux PES)
- python-pystrich (Génération de datamatrix)

Ils s'installent depuis la console Linux avec la commande (**à exécuter si besoin avec sudo**):
```
apt-get install python-mysqldb python-dateutil python-numpy python-pil python-reportlab python-matplotlib 
python-xlrd python-xlsxwriter python-pip python-espeak python-pyscard python-opencv python-crypto python-appdirs
python-wxgtk3.0 python-sqlalchemy libcanberra-gtk-module python-psutil python-paramiko python-lxml
```

Et pour pyttsx et icalendar il faut avoir installé python-pip (ce qui a ét fait dans l'étape précédente) et les installer par:
```
pip install pyttsx
pip install icalendar
```
Pour lancer Noethys, lancez le terminal de Linux, placez-vous dans le répertoire d'installation de Noethys, puis saisissez la commande "python Noethys.py"
- - - -

