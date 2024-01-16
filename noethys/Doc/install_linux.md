Installer Noethys sur Linux
==================
L'installation de Noethys sur Linux se fait obligatoirement depuis les sources.
Vous devez télécharger le code source depuis Github et installer les dépendances.

Installation facile sur Ubuntu 22.04
------------------
Lancez dans votre console Linux les commandes suivantes :

```
sudo groupadd noegest
sudo mkdir /home/noegest
sudo useradd matthania noegest
sudo chgrp -R noegest /home/noegest
sudo chown -R matthania /home/noegest
su matthania
cd /home/noegest
apt-get install git curl libsdl2-mixer-2.0-0 libsdl2-image-2.0-0 libsdl2-2.0-0 python3-pip python3-pyscard python3-dev default-libmysqlclient-dev build-essential
apt install pkg-config
pip3 install -U -f https://extras.wxpython.org/wxPython4/extras/linux/gtk3/ubuntu-22.04 wxPython
git clone https://github.com/BrunelJacques/Noethys-Matthania
cd Noethys-Matthania
pip3 install -r requirements.txt
python3 noethys/Noethys.py
```


Installation manuelle sur Linux
------------------
si échec du 'git clone' télécharger les sources et extraire les fichiers

pour wxpython existe aussi la version ubuntu-22
extras.wxpython.org/wxPython4/extras/linux/gtk3/ubuntu-22.04 wxPython

si echec des accès mysql
```
sudo apt-get install python-mysqldb
pip3 install mysql-connector-python
```

préconisation Noethys:
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



## Obsolète: instructions à suivre uniquement sur d'anciennes versions de debian ou ubuntu ##

Dans le cas où votre version de debian ou d'ubuntu ne proposerait pas python-wxgtk3.0 (ce qui est le cas pour ubuntu LTS 14.04 et toute distribution basée sur cette version), la commande précédente retourne une erreur.

Exécutez alors la commande suivante:
```
apt-get install python-wxgtk2.8 libjpeg62 libwxgtk3.0-0
```

Puis téléchargez les paquets de la bibliothèque graphique correspondant à votre architecture (32 ou 64 bits), wxpython et wxwidgets, ainsi que libtiff4.

Vous trouverez ces fichiers sur le site de Noethys : **Menu Assistance > Ressources communautaires > Liste des ressources > Divers**.

Puis exécutez la commande suivante:
```
dpkg -i dossier/wxwidget*****.deb dossier/wxpython*****.deb dossier/libtiff4*****.deb
```

**dossier**: le dossier dans lequel vous avez téléchargé la bibliothèque
**wxwidget\*****.deb, wxpython\*****.deb et libtiff4\*****.deb** sont les fichiers correspondant à votre architecture que vous avez téléchargés.

**Vérifiez que vous avez choisi la version correspondant à votre architecture (32 ou 64 bits).**

