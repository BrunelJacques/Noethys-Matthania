#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activit�s
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-11 Ivan LUCAS
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------


import Chemins
from Utils.UTILS_Traduction import _
import GestionDB


class AnalyseLocalisation():
    """ Renvoie les noms des lieux de d�part et d'arriv�e """
    def __init__(self):
        self.MAJ()
    
    
    def MAJ(self):
        """ R�cup�re les donn�es dans la base """
        DB = GestionDB.DB()
        
        # Arr�ts
        req = """SELECT IDarret, nom FROM transports_arrets;"""
        DB.ExecuterReq(req,MsgBox="ExecuterReq")
        listeDonnees = DB.ResultatReq()
        self.dict_arrets = {}
        for IDarret, nom in listeDonnees :
            self.dict_arrets[IDarret] = nom
            
        # Lieux
        req = """SELECT IDlieu, nom FROM transports_lieux;"""
        DB.ExecuterReq(req,MsgBox="ExecuterReq")
        listeDonnees = DB.ResultatReq()
        self.dict_lieux = {}
        for IDlieu, nom in listeDonnees :
            self.dict_lieux[IDlieu] = nom
        
        # Activit�s
        req = """SELECT IDactivite, nom FROM activites;"""
        DB.ExecuterReq(req,MsgBox="ExecuterReq")
        listeDonnees = DB.ResultatReq()
        self.dict_activites = {}
        for IDactivite, nom in listeDonnees :
            self.dict_activites[IDactivite] = nom

        # Ecoles
        req = """SELECT IDecole, nom FROM ecoles;"""
        DB.ExecuterReq(req,MsgBox="ExecuterReq")
        listeDonnees = DB.ResultatReq()
        self.dict_ecoles = {}
        for IDecole, nom in listeDonnees :
            self.dict_ecoles[IDecole] = nom

        DB.Close()
    
    def Analyse(self, IDarret=None, IDlieu=None, localisation=None):
        # Analyse du d�part ou de l'arriv�e
        nom = ""
        if IDarret != None and IDarret in self.dict_arrets :
            nom = self.dict_arrets[IDarret]
        if IDlieu != None and IDlieu in self.dict_lieux :
            nom = self.dict_lieux[IDlieu]
        if localisation != None :
            nom = self.Localisation(localisation)
        return nom
        
    def Localisation(self, texte=""):
        # Analyse des localisations
        code = texte.split(";")[0]
        if code == "DOMI" :
            return _("Domicile")
        if code == "ECOL" :
            IDecole = int(texte.split(";")[1])
            if IDecole in self.dict_ecoles:
                return self.dict_ecoles[IDecole]
        if code == "ACTI" :
            IDactivite = int(texte.split(";")[1])
            if IDactivite in self.dict_activites:
                return self.dict_activites[IDactivite]
        if code == "AUTR" :
            code, nom, rue, cp, ville = texte.split(";")
            return "%s %s %s %s" % (nom, rue, cp, ville)
        return ""

            
if __name__ == '__main__':
    pass
    