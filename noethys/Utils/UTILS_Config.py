#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activit�s
# Site internet :  www.noethys.com
# Auteur:          Ivan LUCAS
# Copyright:       (c) 2010-19 Ivan LUCAS
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------

import wx
import os
import shutil
import random
from Utils import UTILS_Fichiers
from Utils import UTILS_Json

def GetNomFichierConfig(nomFichier="Config.json"):
    return UTILS_Fichiers.GetRepUtilisateur(nomFichier)

def IsFichierExists() :
    nomFichier = GetNomFichierConfig()
    return os.path.isfile(nomFichier)

def GenerationFichierConfig():
    dictDonnees = {}
    nouveau_fichier = True

    # Importe l'ancien fichier 'config' s'il existe
    nom_fichier_dat = UTILS_Fichiers.GetRepUtilisateur("Config.dat")

    # Cr�e les nouvelles donn�es
    if nouveau_fichier == True :
        dictDonnees = {
            "nomFichier": "",
            "derniersFichiers": [],
            "taille_fenetre": (0, 0),
            "dict_selection_periodes_activites": {
                'listeActivites': [],
                'listeSelections': (),
                'listePeriodes': [],
                'modeAffichage': 'nbrePlacesPrises',
                'dateDebut': None,
                'dateFin': None,
                'annee': None,
                'page': 0,
                },
            "assistant_demarrage": False,
            "perspectives": [],
            "perspective_active": None,
            "annonce": None,
            "autodeconnect": None,
            "interface_mysql": "mysqldb",
            "pool_mysql": 5,
            }

    # Cr�ation d'un nouveau fichier json
    cfg = FichierConfig()
    cfg.SetDictConfig(dictConfig=dictDonnees)

    print("nouveau_fichier = %s" % nouveau_fichier)
    return nouveau_fichier

def SupprimerFichier():
    nomFichier = GetNomFichierConfig()
    os.remove(nomFichier)

class FichierConfig():
    def __init__(self):
        nomFichier = GetNomFichierConfig()
        self.nomFichier = nomFichier
        
    def GetDictConfig(self):
        """ Recupere une copie du dictionnaire du fichier de config """
        data = {}
        try :
            data = UTILS_Json.Lire(self.nomFichier)
        except:
            nom_fichier_bak = self.nomFichier + ".bak"
            if os.path.isfile(nom_fichier_bak):
                print("Recuperation de config.json.bak")
                data = UTILS_Json.Lire(nom_fichier_bak)
        return data

    def SetDictConfig(self, dictConfig={}):
        """ Remplace le fichier de config pr�sent sur le disque dur par le dict donn� """
        UTILS_Json.Ecrire(nom_fichier=self.nomFichier, data=dictConfig)
        # Cr�ation d'une copie de sauvegarde du config
        nom_fichier_bak = self.nomFichier + ".bak"
        if not os.path.isfile(nom_fichier_bak) or random.randint(0, 5) == 0:
            shutil.copyfile(self.nomFichier, nom_fichier_bak)

    def GetItemConfig(self, key, defaut=None):
        """ R�cup�re une valeur du dictionnaire du fichier de config """
        data = self.GetDictConfig()
        if key in data :
            valeur = data[key]
        else:
            valeur = defaut
        return valeur
    
    def SetItemConfig(self, key, valeur ):
        """ Remplace une valeur dans le fichier de config """
        data = self.GetDictConfig()
        data[key] = valeur
        self.SetDictConfig(data)

    def SetItemsConfig(self, dictParametres={}):
        """ Remplace plusieurs valeur dans le fichier de config """
        """ dictParametres = {nom : valeur, nom : valeur...} """
        data = self.GetDictConfig()
        for key, valeur in dictParametres.items():
            data[key] = valeur
        self.SetDictConfig(data)

    def DelItemConfig(self, key ):
        """ Supprime une valeur dans le fichier de config """
        data = self.GetDictConfig()
        del data[key]
        self.SetDictConfig(data)

def GetParametre(nomParametre="", defaut=None):
    parametre = None
    try :
        topWindow = wx.GetApp().GetTopWindow()
        nomWindow = topWindow.GetName()
    except :
        nomWindow = None
    if nomWindow == "general" : 
        # Si la frame 'General' est charg�e, on y r�cup�re le dict de config
        if nomParametre in topWindow.userConfig :
            parametre = topWindow.userConfig[nomParametre]
        else :
            parametre = defaut
    else:
        # R�cup�ration du nom de la DB directement dans le fichier de config sur le disque dur
        cfg = FichierConfig()
        parametre = cfg.GetItemConfig(nomParametre, defaut)
    return parametre

def SetParametre(nomParametre="", parametre=None):
    try :
        topWindow = wx.GetApp().GetTopWindow()
        nomWindow = topWindow.GetName()
    except :
        nomWindow = None
    if nomWindow == "general" : 
        # Si la frame 'General' est charg�e, on y r�cup�re le dict de config
        topWindow.userConfig[nomParametre] = parametre
    else:
        # Enregistrement du nom de la DB directement dans le fichier de config sur le disque dur
        cfg = FichierConfig()
        cfg.SetItemConfig(nomParametre, parametre)

# --------------Traitement par lot ------------------------------------------------------------------------------------------

def GetParametres(dictParametres={}):
    """ dictParametres = {nom : valeur, nom: valeur...} """
    dictFinal = {}
    try :
        topWindow = wx.GetApp().GetTopWindow()
        nomWindow = topWindow.GetName()
    except :
        nomWindow = None
        
    # Cherche la sources des donn�es
    if nomWindow == "general" : 
        dictSource = topWindow.userConfig
    else :
        cfg = FichierConfig()
        dictSource = cfg.GetDictConfig()
        
    # Lit les donn�es
    for nom, valeur in dictParametres.items() :
        if nom in dictSource :
            dictFinal[nom] = dictSource[nom]
        else :
            dictFinal[nom] = valeur
    return dictFinal

def SetParametres(dictParametres={}):
    """ dictParametres = {nom : valeur, nom: valeur...} """
    try :
        topWindow = wx.GetApp().GetTopWindow()
        nomWindow = topWindow.GetName()
    except :
        nomWindow = None
    if nomWindow == "general" : 
        # Si la frame 'General' est charg�e, on y r�cup�re le dict de config
        for nom, valeur in dictParametres.items() :
            topWindow.userConfig[nom] = valeur
    else:
        # Enregistrement dans le fichier de config sur le disque dur
        cfg = FichierConfig()
        cfg.SetItemsConfig(dictParametres)
    return dictParametres

# --------------- TESTS ----------------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    print("GET :", GetParametres( {"nbre_inscrits_parametre_activites" : 0} ))
    #print("SET :", SetParametres( {"test1" : True, "test2" : True} ))

