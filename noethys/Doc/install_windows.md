Installer Noethys-Matthania sur Windows (version accompagnée : cf TutoInstallation.odt )
===============================================================

# Procédure d'installation:
Sur Windows, vous devez aller sur les sites des auteurs pour 
rechercher et installer les bibliothèques suivantes.
- Python 3.11 avec l'option pip (http://www.python.org/)
- wxPython 4+ - version unicode (http://www.wxpython.org/) se charge par :
- dans un terminal shell lancez 'pip install -U wxPython'
- créez un répertoire c:\'Program Files\Noethys-Matthania'
- Accordez le controle total à tous les utilisateurs via propriétés/sécurité

# installer git  par https://git-scm.com/download/win
ouvrir une fenêtre shell en mode administrateur (clic droit  sur la proposition windows)
- cd c:\'Program Files'
- git clone https://github.com/BrunelJacques/Noethys-Matthania
- cd Noethys-Matthania
- pip install -r requirements.txt

# Installez un raccourci sur le bureau
- cible: "C:\Program Files\Python311\python.exe" Noethys.py
- démarrer: C:\Program Files\Noethys-Matthania\noethys\
- icone: C:\Program Files\Noethys-Matthania\noethys\Static\Images\Icone.ico

# Compléments

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


En installant PyCharm Community Edition on peut facilement créer un environnement 
et vérifier les modules qui ont été chargés 

Pour install personnalisée:
sources présentes sur  https://github.com/BrunelJacques/Noethys-Matthania
