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

DICT_UTILISATEUR = {} # utilIsé comme variable globale

def GetIDutilisateur(facultatif=False):
    """ Récupère le IDutilisateur actif dans la fenêtre principale """
    IDutilisateur = None
    dictUtilisateur = None
    topWindow = wx.GetApp().GetTopWindow()
    if topWindow:
        nomWindow = topWindow.GetName()
    else: nomWindow = None
    if nomWindow == "general" : 
        dictUtilisateur = topWindow.dictUtilisateur
    elif not facultatif:
        dictUtilisateur = GetDictUtilisateur()

    if dictUtilisateur:
        IDutilisateur = dictUtilisateur["IDutilisateur"]
    return IDutilisateur

def GetDictUtilisateur():
    global DICT_UTILISATEUR
    dictUtilisateur = {}
    # Recherche les identifications précédentes encore actives
    if DICT_UTILISATEUR:
        # teste une recherche précédente par ce module
        dictUtilisateur = DICT_UTILISATEUR
    elif wx.GetApp().GetTopWindow():
        # teste le dictUtilisateur actif dans la fenêtre Noethys
        topWindow = wx.GetApp().GetTopWindow()
        nomWindow = topWindow.GetName()
        if nomWindow == "general" :
            dictUtilisateur = topWindow.dictUtilisateur
    if not dictUtilisateur:
        # nouvelle identification
        from Ctrl import CTRL_Identification
        dlg = CTRL_Identification.Dialog(None)
        dlg.ShowModal()
        dictUtilisateur = dlg.GetDictUtilisateur()
    DICT_UTILISATEUR = dictUtilisateur
    return DICT_UTILISATEUR

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

if __name__ == '__main__':
    app = wx.App(0)
    frame = wx.Frame()
    #frame.Show()
    print(GetDictUtilisateur())
    app.MainLoop()


