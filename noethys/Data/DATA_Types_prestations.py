#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#-----------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:           JB
# Licence:         Licence GNU GPL
#-----------------------------------------------------------

# Types de prestations dans champ catégorie des prestations

import wx
import GestionDB

LISTE_TYPES_PRESTATIONS = [
            ("","_____ Saisir le type ou flécher _____",""),
            ("don", "Don à l'association", "DC"), # ID, label, prefix-pièce cpta
            ("donsscerfa", "Don sans Cerfa", "DS"),
            ("debour", "Frais ou débour dû par client", "PR"),
            ("autre", "Paiement autre client (ou autres cas)", "XX"),
            ("consommation", "Prestation issue de pièce liée à une inscription","FA"),
            ("consoavoir", "Prestation de pièce annulée par un avoir","AV"),
            ]

def GetLstTypes(consos=True, dons=True, autres=True):
    # retourne deux listes pour un choix à l'écran
    lstIDtypes, lstLibTypes = [], []
    for IDtypePrestation, libTypePrestation, prefix in LISTE_TYPES_PRESTATIONS :
        if not consos and IDtypePrestation.startswith("conso"):
            continue
        if not dons and IDtypePrestation.startswith("don"):
            continue
        if not autres and not (IDtypePrestation.startswith("don")
                               or IDtypePrestation.startswith("conso")):
            continue
        lstIDtypes.append(IDtypePrestation)
        lstLibTypes.append(libTypePrestation)
    return lstIDtypes, lstLibTypes

def GetDicPrefixes(avecConsos:False):
    dictTypes = {}
    for IDtypePrestation, libTypePrestation, prefix in LISTE_TYPES_PRESTATIONS:
        if not avecConsos and IDtypePrestation.startswith("conso"):
            continue
        dictTypes[IDtypePrestation] = prefix
    return dictTypes

def GetLstComptes(DB,consos=True, dons=True, autres=True):
    req = """
        SELECT pctCodeComptable, pctLibelle, pctCompte
        FROM matPlanComptable; 
    """
    DB.ExecuterReq(req,MsgBox="DATA_Types_prestations.GetMatPlanCpte")
    lstDonnees = [('',"___ Saisir le début d'un compte ____",""),]
    lstDonnees += [x for x in sorted(DB.ResultatReq(), key=lambda item: item[1])]
    # retourne la liste triée sur le libellé
    return lstDonnees
