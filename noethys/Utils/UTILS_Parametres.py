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
import wx
import six
import GestionDB

TYPE_COULEUR = wx._core.Colour

def ParametresCategorie(mode="get", categorie="", dictParametres={}, nomFichier=""):
    """ Pour m�moriser ou r�cup�rer des param�tres dans la base de donn�es """
    """ Renseigner categorie et dictParametres obligatoirement !!!  (pour avoir les valeurs par d�faut et deviner les types de valeur) """
    """ dictParametres = {nom:valeur, nom:valeur, ....} """
    # Recherche du parametre
    DB = GestionDB.DB(nomFichier=nomFichier)
    
    # Si aucun fichier n'est charg�, on renvoie la valeur par d�faut :
    if DB.echec == 1 :
        return dictParametres

    req = """SELECT IDparametre, nom, parametre FROM parametres WHERE categorie="%s";""" % categorie
    DB.ExecuterReq(req,MsgBox="ExecuterReq")
    listeDonnees = DB.ResultatReq()
    dictDonnees = {}
    for IDparametre, nom, parametre in listeDonnees :
        dictDonnees[nom] = parametre
    
    listeAjouts = []
    listeModifications = []
    dictFinal = {}
    
    # On boucle sur chaque valeur
    for nom, valeur in dictParametres.items() :

        # Pr�paration de la valeur par d�faut
        type_parametre = type(valeur)
        if type_parametre == int : valeurTmp = str(valeur)
        elif type_parametre == float : valeurTmp = str(valeur)
        elif type_parametre == str : valeurTmp = valeur
        elif type_parametre == six.text_type : valeurTmp = valeur
        elif type_parametre == tuple : valeurTmp = str(valeur)
        elif type_parametre == list : valeurTmp = str(valeur)
        elif type_parametre == dict : valeurTmp = str(valeur)
        elif type_parametre == bool : valeurTmp = str(valeur)
        elif type_parametre == TYPE_COULEUR : valeurTmp = str(valeur)
        else : valeurTmp = ""

        if nom in dictDonnees :
            
            if mode == "get" :
                # Un parametre existe :
                valeur = dictDonnees[nom]
                # On le formate pour le r�cup�rer sous son vrai format
                try :
                    if type_parametre == int : valeur = int(valeur)
                    if type_parametre == float : valeur = float(valeur)
                    if type_parametre == str : valeur = valeur
                    if type_parametre == six.text_type : valeur = valeur
                    if type_parametre == tuple : valeur = eval(valeur)
                    if type_parametre == list : valeur = eval(valeur)
                    if type_parametre == dict : valeur = eval(valeur)
                    if type_parametre == bool : valeur = eval(valeur)
                    if type_parametre == TYPE_COULEUR and valeur != "" : valeur = eval(valeur)
                except :
                    valeur = None
                dictFinal[nom] = valeur
                
            if mode == "set" :
                # On modifie la valeur du param�tre
                dictFinal[nom] = valeur
                if dictDonnees[nom] != valeurTmp :
                    listeModifications.append((valeurTmp, categorie, nom))
                
        else:
            # Le parametre n'existe pas, on le cr�� :
            listeAjouts.append((categorie, nom, valeurTmp))
            dictFinal[nom] = valeur

    # Sauvegarde des modifications
    if len(listeModifications) > 0 :
        DB.Executermany("UPDATE parametres SET parametre=? WHERE categorie=? and nom=?", listeModifications, commit=False)

    # Sauvegarde des ajouts
    if len(listeAjouts) > 0 :
        DB.Executermany("INSERT INTO parametres (categorie, nom, parametre) VALUES (?, ?, ?)", listeAjouts, commit=False)
        
    # Commit et fermeture de la DB
    if len(listeModifications) > 0 or len(listeAjouts) > 0 :
        DB.Commit() 
    DB.Close()
    return dictFinal

def Parametres(mode="get", categorie="", nom="", valeur=None, nomFichier=""):
    """ M�morise ou r�cup�re un param�tre quelconque dans la base de donn�es
        Le param�tre doit �tre str ou unicode obligatoirement
        si mode = 'get' : valeur est la valeur par d�faut
        si mode = 'set' : valeur est la valeur � donner au param�tre """
   
    # Pr�paration de la valeur par d�faut
    type_parametre = type(valeur)
    if type_parametre == int : valeurTmp = str(valeur)
    elif type_parametre == float : valeurTmp = str(valeur)
    elif type_parametre == str : valeurTmp = valeur
    elif type_parametre == six.text_type : valeurTmp = valeur
    elif type_parametre == tuple : valeurTmp = str(valeur)
    elif type_parametre == list : valeurTmp = str(valeur)
    elif type_parametre == dict : valeurTmp = str(valeur)
    elif type_parametre == bool : valeurTmp = str(valeur)
    else : valeurTmp = ""
    
    # Recherche du parametre
    DB = GestionDB.DB(nomFichier=nomFichier)
    
    # Si aucun fichier n'est charg�, on renvoie la valeur par d�faut :
    if DB.echec == 1 :
        erreur = DB.erreur
        DB.Close()
        if mode == "get":
            return valeur
        else:
            mess= "Echec d'acc�s � la base: %s\n\nErr: %s" % (nomFichier,erreur)
            wx.MessageBox(mess,"Erreur base",style=wx.ICON_STOP)
            return erreur

    req = """SELECT IDparametre, parametre FROM parametres WHERE categorie="%s" AND nom="%s" ;""" % (categorie, nom)
    DB.ExecuterReq(req,MsgBox="ExecuterReq")
    listeDonnees = DB.ResultatReq()
    if len(listeDonnees) != 0 :
        if mode == "get" :
            # Un parametre existe :
            valeurTmp = listeDonnees[0][1]
            # On le formate pour le r�cup�rer sous son vrai format
            if type_parametre == int : valeurTmp = int(valeurTmp)
            if type_parametre == float : valeurTmp = float(valeurTmp)
            if type_parametre == str : valeurTmp = valeurTmp
            if type_parametre == six.text_type : valeurTmp = valeurTmp
            if type_parametre == tuple : valeurTmp = eval(valeurTmp)
            if type_parametre == list : valeurTmp = eval(valeurTmp)
            if type_parametre == dict : valeurTmp = eval(valeurTmp)
            if type_parametre == bool : valeurTmp = eval(valeurTmp)
        else:
            # On modifie la valeur du param�tre
            IDparametre = listeDonnees[0][0]
            listeDonnees = [("categorie",  categorie), ("nom",  nom), ("parametre",  valeurTmp),]
            DB.ReqMAJ("parametres", listeDonnees, "IDparametre", IDparametre)
            valeurTmp = valeur
    else:
        # Le parametre n'existe pas, on le cr�� :
        listeDonnees = [("categorie",  categorie), ("nom",  nom), ("parametre",  valeurTmp),]
        newID = DB.ReqInsert("parametres", listeDonnees)
        valeurTmp = valeur
    DB.Close()
    return valeurTmp

# ----------------------- TESTS --------------------------------------------------------------------------------------------------------------------------------------------------------------------

def TestParametre(categorie="", nom="", valeur=None, nomFichier=""):
    """ V�rifie si un param�tre existe dans le fichier """
    DB = GestionDB.DB(nomFichier=nomFichier)
    req = """SELECT IDparametre, parametre FROM parametres WHERE categorie="%s" AND nom="%s" ;""" % (categorie, nom)
    DB.ExecuterReq(req,MsgBox="ExecuterReq")
    listeDonnees = DB.ResultatReq()
    DB.Close() 
    if len(listeDonnees) == 0 :
        return False
    else:
        return True

if __name__ == "__main__":
    #print(ParametresCategorie(mode="get", categorie="parametres_grille_conso", dictParametres={"affiche_colonne_memo":True, "test":u"�a marche !"}, nomFichier=""))
    reponse = Parametres(mode="get", categorie="dlg_ouvertures", nom="afficher_tous_groupes", valeur=False)
    print(reponse, type(reponse))
    
    