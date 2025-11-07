#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-11 Ivan LUCAS
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------

import wx

def GetIDutilisateur():
    """ Récupère le IDutilisateur actif dans la fenêtre principale """
    IDutilisateur = None
    topWindow = wx.GetApp().GetTopWindow()
    if topWindow:
        nomWindow = topWindow.GetName()
    else: nomWindow = None
    if nomWindow == "general" : 
        dictUtilisateur = topWindow.dictUtilisateur
        if dictUtilisateur:
            IDutilisateur = dictUtilisateur["IDutilisateur"]
    return IDutilisateur

def GetDictUtilisateur():
    """ Récupère le dictUtilisateur actif dans la fenêtre principale """
    topWindow = wx.GetApp().GetTopWindow()
    nomWindow = topWindow.GetName()
    if nomWindow == "general" : 
        dictUtilisateur = topWindow.dictUtilisateur
    else:
        from Ctrl import CTRL_Identification
        dlg = CTRL_Identification.Dialog(None)
        dlg.ShowModal()
        dictUtilisateur = dlg.GetDictUtilisateur()
    return dictUtilisateur

def GetAutreDictUtilisateur(IDutilisateur=None):
    """ Récupère un dictUtilisateur autre que l'utilisateur actif """
    dictUtilisateur = None
    topWindow = wx.GetApp().GetTopWindow()
    nomWindow = topWindow.GetName()
    if nomWindow == "general" : 
        listeUtilisateurs = topWindow.listeUtilisateurs
        for dictTemp in listeUtilisateurs :
            if dictTemp["IDutilisateur"] == IDutilisateur :
                return dictTemp
    return dictUtilisateur

def GetDictUtilSqueleton():
    # schéma des items fournis par: UTILS_Utilisateurs.GetListeUtilisateurs()
    return { "IDutilisateur":0, "nom":"nom", "prenom":"prenom", "sexe":"H",
             "mdp": "", "mdpcrypt": "", "profil": "", "actif": 1,
             "image":"", "droits":{} }
