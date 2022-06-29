#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activit�s
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-16 Ivan LUCAS
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------

import Chemins
import wx
import os
import io
import sys
import shutil
import platform
import subprocess
from Utils import UTILS_Customize
import appdirs
import zipfile

def GetRepData(fichier=""):
    # V�rifie si un r�pertoire 'Portable' existe
    chemin = Chemins.GetMainPath("Portable")
    if os.path.isdir(chemin):
        chemin = os.path.join(chemin, "Data")
        if not os.path.isdir(chemin):
            os.mkdir(chemin)
        return os.path.join(chemin, fichier)

    # Recherche s'il existe un chemin personnalis� dans le Customize.ini
    chemin = UTILS_Customize.GetValeur("repertoire_donnees", "chemin", "")
    #chemin = chemin.decode("iso-8859-15")
    if chemin != "" and os.path.isdir(chemin):
        return os.path.join(chemin, fichier)

    # Recherche le chemin du r�pertoire des donn�es
    if sys.platform == "win32" and platform.release() != "Vista" :

        chemin = appdirs.site_data_dir(appname=None, appauthor=None)
        #chemin = chemin.decode("iso-8859-15")

        chemin = os.path.join(chemin, "noethys")
        if not os.path.isdir(chemin):
            os.mkdir(chemin)

    else :

        chemin = appdirs.user_data_dir(appname=None, appauthor=None)
        #chemin = chemin.decode("iso-8859-15")

        chemin = os.path.join(chemin, "noethys")
        if not os.path.isdir(chemin):
            os.mkdir(chemin)

        chemin = os.path.join(chemin, "Data")
        if not os.path.isdir(chemin):
            os.mkdir(chemin)

    # Ajoute le dirname si besoin
    return os.path.join(chemin, fichier)

def GetRepTemp(fichier=""):
    chemin = GetRepUtilisateur("Temp")
    return os.path.join(chemin, fichier)

def GetRepUpdates(fichier=""):
    path = GetRepUtilisateur("Updates")
    return os.path.join(path, fichier)

def GetRepLang(fichier=""):
    chemin = GetRepUtilisateur("Lang")
    return os.path.join(chemin, fichier)

def GetRepSync(fichier=""):
    chemin = GetRepUtilisateur("Sync")
    return os.path.join(chemin, fichier)

def GetRepExtensions(fichier=""):
    chemin = GetRepUtilisateur("Extensions")
    return os.path.join(chemin, fichier)

def GetRepUtilisateur(fichier=""):
    """ Recherche le r�pertoire Utilisateur pour stockage des fichiers de config et provisoires """
    # V�rifie si un r�pertoire 'Portable' existe
    chemin = Chemins.GetMainPath("Portable")
    if os.path.isdir(chemin):
        return os.path.join(chemin, fichier)

    # Recherche le chemin du r�pertoire de l'utilisateur
    chemin = appdirs.user_config_dir(appname=None, appauthor=None, roaming=True)
    #chemin = chemin.decode("iso-8859-15")

    # Ajoute 'noethys' dans le chemin et cr�ation du r�pertoire
    chemin = os.path.join(chemin, "noethys")
    if not os.path.isdir(chemin):
        os.mkdir(chemin)

    # Ajoute le dirname si besoin
    return os.path.join(chemin, fichier)

def DeplaceFichiers():
    """ V�rifie si des fichiers du r�pertoire Data ou du r�pertoire Utilisateur sont � d�placer vers le r�pertoire Utilisateur>AppData>Roaming """

    # D�place les fichiers de config et le journal
    for nom in ("journal.log", "Config.json", "Customize.ini") :
        for rep in ("", Chemins.GetMainPath("Data"), os.path.join(os.path.expanduser("~"), "noethys")) :
            fichier = os.path.join(rep, nom)
            if os.path.isfile(fichier) :
                print(["d�placement fichier config :", fichier, " > ", GetRepUtilisateur(nom)])
                shutil.move(fichier, GetRepUtilisateur(nom))

    # D�place les fichiers xlang
    if os.path.isdir(Chemins.GetMainPath("Lang")) :
        for nomFichier in os.listdir(Chemins.GetMainPath("Lang")) :
            if nomFichier.endswith(".xlang") :
                print(["d�placement fichier xlang :", fichier, " > ", GetRepLang(nomFichier)])
                shutil.move(u"Lang/%s" % nomFichier, GetRepLang(nomFichier))

    # D�place les fichiers du r�pertoire Sync
    if os.path.isdir(Chemins.GetMainPath("Sync")) :
        for nomFichier in os.listdir(Chemins.GetMainPath("Sync")) :
            shutil.move(Chemins.GetMainPath("Sync/%s" % nomFichier), GetRepSync(nomFichier))

    # D�place les fichiers de donn�es du r�pertoire Data
    if GetRepData() != "Data/" and os.path.isdir(Chemins.GetMainPath("Data")) :
        for nomFichier in os.listdir(Chemins.GetMainPath("Data")) :
            if nomFichier.endswith(".dat") and "_" in nomFichier and "EXEMPLE_" not in nomFichier and "_archive.dat" not in nomFichier :
                # D�place le fichier vers le r�pertoire des fichiers de donn�es
                print(["copie base de donnees :", nomFichier, " > ", GetRepData(nomFichier)])
                shutil.copy(Chemins.GetMainPath(u"Data/%s" % nomFichier), GetRepData(nomFichier))
                # Renomme le fichier de donn�es en archive (par s�curit�)
                try :
                    os.rename(Chemins.GetMainPath(u"Data/%s" % nomFichier), Chemins.GetMainPath(u"Data/%s" % nomFichier.replace(".dat", "_archive.dat")))
                except :
                    pass

def DeplaceExemples():
    """ D�place les fichiers exemples vers le r�pertoire des fichiers de donn�es """
    if GetRepData() != "Data/" :
        chemin = Chemins.GetStaticPath("Exemples")
        for nomFichier in os.listdir(chemin) :
            if nomFichier.endswith(".dat") and "EXEMPLE_" in nomFichier :
                # D�place le fichier vers le r�pertoire des fichiers de donn�es
                shutil.copy(os.path.join(chemin, nomFichier), GetRepData(nomFichier))

def OuvrirRepertoire(rep):
    if platform.system() == "Windows":
        subprocess.Popen(["explorer", rep])
    elif platform.system() == "Darwin":
        subprocess.Popen(["open", rep])
    else:
        subprocess.Popen(["xdg-open", rep])

def GetUnicodeFromFile(fileName):
    # lecture du contenu unicode d'un fichier
    import codecs
    fichier = codecs.open(fileName, encoding='utf-8', mode='r')
    return fichier.read()

def GetBytesFromFile(fileName, buffer=True):
    # lecture du contenu 'nature' via buffer d'un fichier
    file = open(fileName, "rb")
    data = file.read()
    file.close()
    if not buffer:
        return data
    buffer = io.BytesIO(data)
    bytesBuffer = buffer.read()
    return bytesBuffer

def SetFileFromBytes(fileName,dataBytes):
    # Cr�ation du fichier dans le r�pertoire Temp
    try:
        file = open(fileName, "wb")
        file.write(dataBytes)
        file.close()
    except Exception as err:
        print(err)
        return err
    return 'ok'

#- Gestion des fichiers Zip -------------------------------------------------

def VerificationZip(fichier=""):
    """ V�rifie que le fichier est une archive zip valide """
    return zipfile.is_zipfile(fichier)

def SelectionFichier(intro="Choix",wildcard="*.zip",defaultDir=None,
                     style=wx.FD_OPEN,
                     retourCourt=False,
                     verifZip=False):
    # Demande l'emplacement d'un fichier lambda (si non zip modifier wildcard)
    if not defaultDir:
        standardPath = wx.StandardPaths.Get()
        defaultDir = standardPath.GetDocumentsDir()
    dlg = wx.FileDialog(None, message=intro,
                        defaultDir=defaultDir,
                        defaultFile="",
                        wildcard=wildcard,
                        style=style)
    if dlg.ShowModal() == wx.ID_OK:
        if retourCourt:
            fichier = dlg.GetFilename()
        else:
            fichier = dlg.GetPath()
    else:
        fichier =None
    dlg.Destroy()
    if fichier and verifZip:
        # V�rifie que c'est un fichier ZIP ok
        valide = VerificationZip(fichier)
        if valide == False:
            dlg = wx.MessageDialog(None,
                       "Le fichier ZIP semble corrompu !",
                       "Erreur", wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            fichier = None
    return fichier

def GetZipFile(nameFile='',modeRW='r'):
    # connecte au fichier en mode �criture ou lecture, retourne fichier ou message erreur
    try:
        zip =  zipfile.ZipFile(nameFile, modeRW, compression=zipfile.ZIP_DEFLATED)
    except Exception as err:
        zip = "Acc�s au fichier Zip impossible \n%s" % err
    return zip

def GetListeFichiersZip(fichierZip):
    """ R�cup�re la liste des fichiers du ZIP """
    listeFichiers = []
    for fichier in fichierZip.namelist():
        listeFichiers.append(fichier)
    return listeFichiers

def GetOneFileInZip(myZipFile,oneFile):
    with myZipFile.open(oneFile) as myFile:
        return myFile.read()


if __name__ == "__main__":
    # Teste les d�placements de fichiers
    # DeplaceFichiers()

    # R�pertoire utilisateur
    print(GetRepUtilisateur())

    # R�pertoire des donn�es
    chemin = GetRepData()
    print(1, os.path.join(chemin, "Test�.pdf"))
    print(2, os.path.join(chemin, "Test.pdf"))