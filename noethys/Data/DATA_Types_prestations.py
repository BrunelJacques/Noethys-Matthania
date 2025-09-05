#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#-----------------------------------------------------------
# Application :    Noethys, gestion multi-activit�s
# Site internet :  www.noethys.com
# Auteur:           JB
# Licence:         Licence GNU GPL
#-----------------------------------------------------------

# Types de prestations dans champ cat�gorie des prestations

import wx
import GestionDB

LISTE_TYPES_PRESTATIONS = [
            ("don", "Don � l'association", "DC"), # ID, label, prefix-pi�ce cpta
            ("donsscerfa", "Don sans Cerfa", "DS"),
            ("debour", "Frais ou d�bour d� par client", "PR"),
            ("autre", "Paiement autre client (ou autres cas)", "XX"),
            ("consommation", "Prestation issue de pi�ce li�e � une inscription","FA"),
            ("consoavoir", "Prestation de pi�ce annul�e par un avoir","AV"),
            ]

def GetLstTypes(avecConsos:False):
    # retourne deux listes pour un choix � l'�cran
    lstIDtypes, lstLibTypes = ["",], ["",]
    for IDtypePrestation, libTypePrestation, prefix in LISTE_TYPES_PRESTATIONS :
        if not avecConsos and IDtypePrestation.startswith("conso"):
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

def GetMatPlanCpte(DB):
    req = """
        SELECT pctCodeComptable, pctLibelle, pctCompte
        FROM matPlanComptable; 
    """
    DB.ExecuterReq(req,MsgBox="DATA_Types_prestations.GetMatPlanCpte")
    lstDonnees = [('',"____Choisir un compte____",""),]
    lstDonnees += [x for x in sorted(DB.ResultatReq(), key=lambda item: item[1])]
    # retourne la liste tri�e sur le libell�
    return lstDonnees
