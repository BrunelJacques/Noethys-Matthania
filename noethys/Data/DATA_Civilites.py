#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#-----------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-11 Ivan LUCAS
# Licence:         Licence GNU GPL
#-----------------------------------------------------------


""" Liste des civilités d'individus (pour la fiche individu)"""

LISTE_CIVILITES = (
    ("ADULTE",
        (
        (1, "Monsieur", "Mr", "Homme.png", "M"),
        (10, "Monsieur et Madame", "MrMme", "Homme.png", "M"),
        (2, "Mademoiselle", "Melle", "Femme.png", "F"),
        (3, "Madame", "Mme", "Femme.png", "F"),
        )),
    ("ENFANT",
        (
        (4, "Garçon", "Mr", "Garcon.png", "M"),
        (5, "Fille", "Melle", "Fille.png", "F"),
        )),
    ("AUTRE",
        (
        (6, "Collectivité/Foyer", "", "Organisme.png", ""),
        (7, "Asso/Orga/Mission", "",  "Organisme.png", ""),
        (8, "Eglise", "", "Organisme.png", ""),
        (9, "Asso laïque", "", "Organisme.png", ""),
        (90, "Fournisseur", "", "Organisme.png", ""),
        )),
    ) # Rubrique > (ID, CiviliteLong, CiviliteAbrege, nomImage, Masculin/Féminin)


def GetDictCivilites():
    dictCivilites = {}
    for categorie, civilites in LISTE_CIVILITES :
        for IDcivilite, civiliteLong, civiliteAbrege, nomImage, sexe in civilites :
            dictCivilites[IDcivilite] = {"categorie" : categorie, "civiliteLong" : civiliteLong, "civiliteAbrege" : civiliteAbrege, "nomImage" : nomImage, "sexe" : sexe}
    return dictCivilites