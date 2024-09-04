#!\\usr\\bin\\env python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------
# Auteur: Ivan LUCAS Noethys adaptations Noethys-Matthania
#-----------------------------------------------------------

import sys
import os
import glob
import os.path
import zipfile
import shutil


# Chemins
REP_COURANT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, REP_COURANT)
NOETHYS_PATH = os.path.join(REP_COURANT, "noethys")
sys.path.insert(1, NOETHYS_PATH)

from setuptools import setup, find_packages

manifest = """
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0">
  <assemblyIdentity
    version="5.0.0.0"
    processorArchitecture="x86"
    name="Noethys"
    type="win32"
  />
  <description>Noethys</description>
  <trustInfo xmlns="urn:schemas-microsoft-com:asm.v3">
    <security>
      <requestedPrivileges>
        <requestedExecutionLevel
            level="asInvoker"
            uiAccess="false">
        </requestedExecutionLevel>
      </requestedPrivileges>
    </security>
  </trustInfo>
  <dependency>
    <dependentAssembly>
      <assemblyIdentity
            type="win32"
            name="Microsoft.VC90.CRT"
            version="9.0.21022.8"
            processorArchitecture="x86"
            publicKeyToken="1fc8b3b9a1e18e3b">
      </assemblyIdentity>
    </dependentAssembly>
  </dependency>
  <dependency>
    <dependentAssembly>
        <assemblyIdentity
            type="win32"
            name="Microsoft.Windows.Common-Controls"
            version="6.0.0.0"
            processorArchitecture="X86"
            publicKeyToken="6595b64144ccf1df"
            language="*"
        />
    </dependentAssembly>
  </dependency>
</assembly>
"""

def GetVersion():
    """ Recherche du numéro de version """
    fichierVersion = open(os.path.join(NOETHYS_PATH, "Versions.txt"), "r")
    txtVersion = fichierVersion.readlines()[0]
    fichierVersion.close()
    pos_debut_numVersion = txtVersion.find("n")
    pos_fin_numVersion = txtVersion.find("(")
    numVersion = txtVersion[pos_debut_numVersion+1:pos_fin_numVersion].strip()
    return numVersion

VERSION_APPLICATION = GetVersion()

options = {}

def GetDossiers(rep) :
    listeFichiers = filter(os.path.isfile, glob.glob(os.path.join("noethys", rep, "*")))
    return rep, listeFichiers

data_files=[
            # Images
            GetDossiers("Static/Images/16x16"),
            GetDossiers("Static/Images/22x22"),
            GetDossiers("Static/Images/32x32"),
            GetDossiers("Static/Images/48x48"),
            GetDossiers("Static/Images/80x80"),
            GetDossiers("Static/Images/128x128"),
            GetDossiers("Static/Images/BoutonsImages"),
            GetDossiers("Static/Images/Drapeaux"),
            GetDossiers("Static/Images/Special"),
            GetDossiers("Static/Images/Badgeage"),
            GetDossiers("Static/Images/Menus"),
            GetDossiers("Static/Images/Teamword"),
            GetDossiers("Static/Images/Avatars/16x16"),
            GetDossiers("Static/Images/Avatars/128x128"),
            GetDossiers("Static/Images/Interface/Vert"),
            GetDossiers("Static/Images/Interface/Bleu"),
            GetDossiers("Static/Images/Interface/Noir"),

            # Databases
            GetDossiers("Static/Databases"),

            # Divers
            GetDossiers("Static/Divers"),

            # Exemples
            GetDossiers("Static/Exemples"),

            # Lang
            GetDossiers("Static/Lang"),

            # Polices
            GetDossiers("Static/Polices"),

            # Fichiers à importer :
            ('', ['noethys/Versions.txt', 'noethys/Licence.txt', 'noethys/Icone.ico']),

            ]

setup(
    name = "Noethys",
    version = VERSION_APPLICATION,
    author = "Ivan LUCAS",
    description = u"Noethys, le logiciel libre et gratuit de gestion multi-activités",
    long_description = open("README.md").read().decode("utf-8"),
    url = "http://www.noethys.com",
    license = "GPL V3",
    plateformes = "ALL",
    classifiers = [ "Topic :: Office/Business",
                    "Topic :: Education"
                    "Topic :: Utilities"],
    options = options,
    data_files = data_files,
    #dependency_links = [],
    packages = ["noethys", "noethys.Ctrl", "noethys.Data", "noethys.Dlg", "noethys.Gest", "noethys.Olv", "noethys.Ol", "noethys.Outils", "noethys.Utils"],
    install_requires = open("requirements.txt").readlines(),
    windows = [
        {
            "script" : "noethys/Noethys.py",
            "icon_resources" : [(1, "noethys/Icone.ico")],
            "other_resources": [(24,1, manifest)]
        }

    ],)


print("Fini !")
