#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activit�s
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS, JB pour group by
# Copyright:       (c) 2010-11 Ivan LUCAS
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------


import Chemins
from Utils.UTILS_Traduction import _
import GestionDB
import datetime

from Utils import UTILS_Titulaires


def DateEngEnDateDD(dateEng):
    if not isinstance(dateEng,str): dateEng = str(dateEng)
    return datetime.date(int(dateEng[:4]), int(dateEng[5:7]), int(dateEng[8:10]))


def GetListePiecesManquantes(dateReference=None, listeActivites=None, presents=None, concernes=False):
    if dateReference == None : 
        dateReference = datetime.date.today()

    # R�cup�ration des donn�es
    dictItems = {}
    
    # Conditions Activites
    if listeActivites == None or listeActivites == [] :
        conditionActivites = ""
    else:
        if len(listeActivites) == 1 :
            conditionActivites = " AND consommations.IDactivite=%d" % listeActivites[0]
        else:
            conditionActivites = " AND consommations.IDactivite IN %s" % str(tuple(listeActivites))
            
    # Conditions Pr�sents
##    if presents == None :
##        conditionPresents = ""
##        jonctionPresents = ""
##    else:
##        conditionPresents = " AND (consommations.date>='%s' AND consommations.date<='%s')" % (str(presents[0]), str(presents[1]))
##        jonctionPresents = "LEFT JOIN consommations ON consommations.IDindividu = individus.IDindividu"
    
    DB = GestionDB.DB()

    # R�cup�ration des individus pr�sents
    listePresents = []
    if presents != None :
        req = """
        SELECT IDindividu, IDinscription
        FROM consommations
        WHERE date>='%s' AND date<='%s' AND consommations.etat IN ('reservation', 'present') %s
        GROUP BY IDindividu, IDinscription
        ;"""  % (str(presents[0]), str(presents[1]), conditionActivites)
        DB.ExecuterReq(req,MsgBox="ExecuterReq")
        listeIndividusPresents = DB.ResultatReq()
        for IDindividu, IDinscription in listeIndividusPresents :
            listePresents.append(IDindividu)


    req = """
    SELECT inscriptions.IDfamille, pieces_activites.IDtype_piece, types_pieces.nom, 
        types_pieces.public, types_pieces.valide_rattachement, individus.prenom, 
        individus.IDindividu
    FROM pieces_activites 
    LEFT JOIN types_pieces ON types_pieces.IDtype_piece = pieces_activites.IDtype_piece
    LEFT JOIN inscriptions ON inscriptions.IDactivite = pieces_activites.IDactivite
    LEFT JOIN individus ON individus.IDindividu = inscriptions.IDindividu
    LEFT JOIN activites ON activites.IDactivite = inscriptions.IDactivite
    WHERE (NOT inscriptions.statut LIKE 'ko%%') AND (inscriptions.date_desinscription IS NULL OR inscriptions.date_desinscription>='%s') %s AND activites.date_fin>='%s'
    GROUP BY inscriptions.IDfamille, pieces_activites.IDtype_piece, 
        individus.IDindividu, types_pieces.nom, 
        types_pieces.public, types_pieces.valide_rattachement, individus.prenom
    ;""" % (dateReference, conditionActivites.replace("consommations", "inscriptions"), dateReference)
    DB.ExecuterReq(req,MsgBox="ExecuterReq")
    listePiecesObligatoires = DB.ResultatReq()


    # Recherche des pi�ces d�j� fournies
    req = """
    SELECT IDpiece, pieces.IDtype_piece, IDindividu, IDfamille, date_debut, date_fin, public
    FROM pieces 
    LEFT JOIN types_pieces ON types_pieces.IDtype_piece = pieces.IDtype_piece
    WHERE date_debut <= '%s' AND date_fin >= '%s'
    ORDER BY date_fin
    """ % (str(dateReference), str(dateReference))
    DB.ExecuterReq(req,MsgBox="ExecuterReq")
    listePiecesFournies = DB.ResultatReq()
    DB.Close()
    dictPiecesFournies = {}
    for IDpiece, IDtype_piece, IDindividu, IDfamille, date_debut, date_fin, publicPiece in listePiecesFournies :
        # Pour les pi�ces familiales :
        if publicPiece == "famille" : IDindividu = None
        
        date_debut = DateEngEnDateDD(date_debut)
        date_fin = DateEngEnDateDD(date_fin)
        dictPiecesFournies[ (IDfamille, IDtype_piece, IDindividu) ] = (date_debut, date_fin)
    
    # Comparaison de la liste des pi�ces � fournir et la liste des pi�ces fournies
    dictDonnees = {}
    for IDfamille, IDtype_piece, nomPiece, publicPiece, rattachementPiece, prenom, IDindividu in listePiecesObligatoires :
        
        if presents == None or (presents != None and IDindividu in listePresents) :
            
            # Pour les pi�ces familiales :
            if publicPiece == "famille" : IDindividu = None
            # Pour les pi�ces qui sont ind�pendantes de la famille
            if rattachementPiece == 1 :
                IDfamilleTemp = None
            else:
                IDfamilleTemp = IDfamille
                
            # Pr�paration du label
            if publicPiece == "famille" or IDindividu == None :
                label = nomPiece
            else:
                label = _("%s de %s") % (nomPiece, prenom)
                        
            if (IDfamilleTemp, IDtype_piece, IDindividu) in dictPiecesFournies :
                date_debut, date_fin = dictPiecesFournies[(IDfamilleTemp, IDtype_piece, IDindividu)]
                nbreJoursRestants = (date_fin - datetime.date.today()).days
                if nbreJoursRestants > 15 :
                    valide = "ok"
                else:
                    valide = "attention"
            else:
                valide = "pasok"
                
            dictDonnees[(IDfamille, IDtype_piece, IDindividu)] = (IDfamille, IDtype_piece, nomPiece, publicPiece, prenom, IDindividu, valide, label)
        
    # R�partition par famille
    dictPieces = {}
    nbreFamilles = 0
    for key, valeurs in dictDonnees.items() :
        IDfamille = valeurs[0]
        if (IDfamille in dictPieces) == False :
            dictPieces[IDfamille] = []
            if IDfamille != None : 
                nbreFamilles += 1
        dictPieces[IDfamille].append(valeurs)
        dictPieces[IDfamille].sort()
    
    # Formatage des donn�es
    dictFinal = {}
    titulaires = UTILS_Titulaires.GetTitulaires() 
    for IDfamille, dictTemp in dictPieces.items() :

        if IDfamille != None and IDfamille in titulaires :
            nomTitulaires = titulaires[IDfamille]["titulairesSansCivilite"]
        else :
            nomTitulaires = _("Aucun titulaire")
        listePieces = []
        listeDetailPieces = []
        for piece in dictTemp :
            if piece[6] != "ok" :
                listePieces.append(piece[7])
                listeDetailPieces.append(piece)
        textePieces = ", ".join(listePieces)

        if concernes == False or (concernes == True and len(listePieces) > 0) :
            dictFinal[IDfamille] = {"titulaires" : nomTitulaires, "pieces" : textePieces, "nbre" : len(listePieces), "liste" : listeDetailPieces}
    
    return dictFinal
    
    
    
            
            
if __name__ == '__main__':
    print(len(GetListePiecesManquantes(dateReference=datetime.date.today(), listeActivites=[1,], presents=(datetime.date(2015, 8, 13), datetime.date(2015, 8, 13)), concernes=True)))