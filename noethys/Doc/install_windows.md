Installer Noethys-Matthania sur Windows (version accompagnée : cf TutoInstallation.odt )
===============================================================

# Procédure d'installation:
Sur Windows, vous devez aller sur les sites des auteurs pour 
rechercher et installer les bibliothèques suivantes.
- Python 3.11 avec l'option pip (http://www.python.org/)
- créez un répertoire "c:/MatthProgram"
- Accordez le controle total à tous les utilisateurs via propriétés/sécurité

# installer git  par https://git-scm.com/download/win  (ou équivalent standalone)
ouvrir une fenêtre shell en mode administrateur (clic droit  sur la proposition windows)
- cd c:/MatthProgram
- git clone https://github.com/BrunelJacques/Noethys-Matthania
- cd Noethys-Matthania

# verifier si pip est installé, sinon version py et installer pip par py:  
- pip -V
  - py -V
  - py -3.11 -m pip install package
  
# installer les bibiliothèques à partir du fichier requirements
- pip install -r requirements.txt

# Installez un raccourci sur le bureau
- cible: "C:/Program Files/Python311/python.exe" Noethys.py
- démarrer: "C:/MatthProgram/Noethys-Matthania/noethys/"
- icone: C:/MatthProgram/Noethys-Matthania/noethys/Static/Images/Icone.ico

# Dans Noethys lancé, il faudra paramétrer les accès à une base de données ou la créer

# Compléments
vérifier les versions python installées: py -0
version active : py -V

Pour installation en copier coller:
- aller à l'adresse : https://github.com/BrunelJacques/Noethys-Matthania pour copier/coller


Liste des modules qui ont dû être chargés par pip install
- dateutil (http://pypi.python.org/pypi/python-dateutil)
- MySQLdb (http://sourceforge.net/projects/mysql-python/)
- NumPy (http://new.scipy.org/download.html)
- PIL (http://www.pythonware.com/products/pil/)
- PyCrypto (https://www.dlitz.net/software/pycrypto/)
- PyCrypt (https://sites.google.com/site/reachmeweb/pycrypt)
- ReportLab (http://www.reportlab.com/software/opensource/rl-toolkit/download/)
- MatPlotLib (http://matplotlib.sourceforge.net/)
- ObjectListView (http://objectlistview.sourceforge.net/python/)
- XlsxWriter (https://pypi.org/project/XlsxWriter/) depuis la version 1.2.7.3
- videoCapture (http://videocapture.sourceforge.net/)
- Pyttsx (https://pypi.python.org/pypi/pyttsx)
- Appdirs (https://pypi.python.org/pypi/appdirs)
- Psutil (https://pypi.python.org/pypi/psutil)
- Paramiko (https://pypi.python.org/pypi/paramiko)
- Lxml (https://pypi.python.org/pypi/lxml)
- pystrich (https://pypi.org/project/pyStrich/)
- etc...

Avec PyCharm Community Edition, on peut facilement créer un environnement particulier
et vérifier les modules qui ont été chargés ou manquant en mode débug.
