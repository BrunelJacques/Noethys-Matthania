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

TYPES_PRESTATIONS = [
        # ( IDtypePrestation, label ),
        ("","_____ Saisir le type ou fl�cher _____"),
        ("don", "Don � l'association"),
        ("donsscerfa", "Don sans Cerfa"),
        ("debour", "Frais ou d�bour d� par client"),
        ("autre", "Paiement autre client (ou autres cas)"),
        ("consommation", "Prestation issue de pi�ce li�e � une inscription"),
        ("consoavoir", "Prestation de pi�ce annul�e par un avoir"),
        ]

def GetLstTypesPrest(consos=True, dons=True, autres=True):
    # retourne deux listes pour un choix � l'�cran
    lstIDtypes, lstLibTypes = [], []
    for IDtypePrestation, libTypePrestation in TYPES_PRESTATIONS :
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

def GetLstComptes(DB):
    # retourne la liste de tuples de matPlanComptable tri�e sur le libell�
    req = """
        SELECT pctCodeComptable, pctLibelle, pctCompte
        FROM matPlanComptable; 
    """
    DB.ExecuterReq(req,MsgBox="DATA_Types_prestations.GetMatPlanCpte")
    lstDonnees = [x for x in sorted(DB.ResultatReq(), key=lambda item: item[1])]
    return lstDonnees
