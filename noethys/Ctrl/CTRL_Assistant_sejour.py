#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activit�s
# Site internet :  www.noethys.com
# Auteur:          Ivan LUCAS
# Copyright:       (c) 2010-18 Ivan LUCAS
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------


import Chemins
from Utils import UTILS_Adaptations
from Utils.UTILS_Traduction import _
import wx
import GestionDB
from dateutil import rrule
from Ctrl import CTRL_Assistant_base as Assistant



# ----------------------------------------
# GENERATION D'UN SEJOUR
# ----------------------------------------


class Page_introduction(Assistant.Page):
    def __init__(self, parent):
        Assistant.Page.__init__(self, parent)
        self.Ajouter_question(titre=_("Bienvenue dans l'assistant de g�n�ration d'une activit� de type s�jour (camps, mini-camps, colos, etc...)"))
        self.Ajouter_question(titre=_("Cliquez sur le bouton Suite pour commencer la saisie des donn�es..."))

    def Suite(self):
        return Page_generalites



class Page_generalites(Assistant.Page):
    def __init__(self, parent):
        Assistant.Page.__init__(self, parent)
        self.Ajouter_rubrique(titre=_("G�n�ralit�s"))
        self.Ajouter_question(code="nom", titre=_("Quel est le nom du s�jour ?"), commentaire=_("Exemple : 'S�jour neige - F�vrier 2018'"), ctrl=Assistant.CTRL_Texte, obligatoire=True)
        self.Ajouter_question(code="date_debut", titre=_("Quelle est la date de d�but du s�jour ?"), commentaire=None, ctrl=Assistant.CTRL_Date, obligatoire=True)
        self.Ajouter_question(code="date_fin", titre=_("Quelle est la date de fin du s�jour ?"), commentaire=None, ctrl=Assistant.CTRL_Date, obligatoire=True)
        self.Ajouter_question(code="num_agrement", titre=_("Quel est le num�ro d'agr�ment du s�jour ?"), commentaire=_("Exemple : '012321CL0121'. S'il n'y a pas d'agr�ment, laissez vide."), ctrl=Assistant.CTRL_Texte)
        self.Ajouter_question(code="nbre_inscrits_max", titre=_("Quel est le nombre maximal d'inscrits ?"), commentaire=_("S'il n'y aucune limitation globale du nombre d'inscrits, conservez la valeur 0."), ctrl=Assistant.CTRL_Nombre)
        self.Ajouter_question(code="groupes_activites", titre=_("Cochez les groupes d'activit�s associ�s � ce s�jour :"), commentaire=_("Les groupes d'activit�s permettent une s�lection plus rapide dans certaines fen�tres de Noethys."), ctrl=Assistant.CTRL_Groupes_activite)

    def Suite(self):
        # Validation des dates du s�jour
        if self.parent.dict_valeurs["date_debut"] > self.parent.dict_valeurs["date_fin"]:
            dlg = wx.MessageDialog(self, _("La date de fin du s�jour doit �tre sup�rieure � la date du d�but !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return False

        return Page_responsable


class Page_responsable(Assistant.Page_responsable):
    def __init__(self, parent):
        Assistant.Page_responsable.__init__(self, parent)

    def Suite(self):
        return Page_groupes



class Page_groupes(Assistant.Page):
    def __init__(self, parent):
        Assistant.Page.__init__(self, parent)
        self.Ajouter_rubrique(titre=_("Groupes"))
        self.Ajouter_question(code="has_groupes", titre=_("Le s�jour est-il constitu� de groupes distincts ?"), commentaire=_("Exemple : Les maternels et les primaires. Si vous n'�tes pas s�r, laissez non."), ctrl=Assistant.CTRL_Oui_non, defaut=False)

    def Suite(self):
        if self.parent.dict_valeurs["has_groupes"] == True :
            return Page_groupes_nombre
        else :
            return Page_renseignements


class Page_groupes_nombre(Assistant.Page):
    def __init__(self, parent):
        Assistant.Page.__init__(self, parent)
        self.Ajouter_rubrique(titre=_("Groupes"))
        self.Ajouter_question(code="nbre_groupes", titre=_("Quel est le nombre de groupes ?"), commentaire=None, ctrl=Assistant.CTRL_Nombre, obligatoire=True)

    def Suite(self):
        return Page_groupes_liste


class Page_groupes_liste(Assistant.Page):
    def __init__(self, parent):
        Assistant.Page.__init__(self, parent)
        self.Ajouter_rubrique(titre=_("Groupes"))
        for index in range(1, self.parent.dict_valeurs["nbre_groupes"]+1) :
            self.Ajouter_question(code="nom_groupe#%d" % index, titre=_("Quel est le nom du groupe n�%d ?") % index, commentaire=None, ctrl=Assistant.CTRL_Texte, obligatoire=True)

    def Suite(self):
        return Page_renseignements


class Page_renseignements(Assistant.Page_renseignements):
    def __init__(self, parent):
        Assistant.Page_renseignements.__init__(self, parent)

    def Suite(self):
        return Page_categories_tarifs


class Page_categories_tarifs(Assistant.Page):
    def __init__(self, parent):
        Assistant.Page.__init__(self, parent)
        self.Ajouter_rubrique(titre=_("Tarifs"))
        self.Ajouter_question(code="has_categories_tarifs", titre=_("Avez-vous plusieurs cat�gories de tarifs ?"), commentaire=_("On retrouve par exemple souvent 'Commune' et 'Hors commune'."), ctrl=Assistant.CTRL_Oui_non, defaut=False)

    def Suite(self):
        if self.parent.dict_valeurs["has_categories_tarifs"] == True :
            return Page_categories_tarifs_nombre
        else :
            return Page_tarifs


class Page_categories_tarifs_nombre(Assistant.Page):
    def __init__(self, parent):
        Assistant.Page.__init__(self, parent)
        self.Ajouter_rubrique(titre=_("Tarifs"))
        self.Ajouter_question(code="nbre_categories_tarifs", titre=_("Quel est le nombre de cat�gories de tarifs ?"), commentaire=None, ctrl=Assistant.CTRL_Nombre, obligatoire=True)

    def Suite(self):
        if self.parent.dict_valeurs["nbre_categories_tarifs"] < 2 :
            dlg = wx.MessageDialog(self, _("Le nombre de cat�gories doit �tre sup�rieur � 1 !\n\nSinon s�lectionnez Non � la question pr�c�dente."), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return False

        return Page_tarifs


class Page_tarifs(Assistant.Page):
    def __init__(self, parent):
        Assistant.Page.__init__(self, parent)

        # Si une seule cat�gorie de tarif
        if self.parent.dict_valeurs["has_categories_tarifs"] == False :
            self.Ajouter_rubrique(titre=_("Tarif"))
            self.Ajouter_question(code="tarif", titre=_("Quel est le tarif � appliquer ?"), commentaire=_("S�lectionnez une m�thode puis saisissez les param�tres demand�s."), ctrl=Assistant.CTRL_Tarif)
        # Si plusieurs cat�gories de tarifs
        else :
            for index in range(1, self.parent.dict_valeurs["nbre_categories_tarifs"]+1):
                self.Ajouter_rubrique(titre=_("Tarif n�%d") % index)
                self.Ajouter_question(code="nom_categorie_tarif#%d" % index, titre=_("Quel est le nom de la cat�gorie de tarifs n�%d ?") % index, commentaire=_("Exemples : 'Commune' ou 'Hors commune'."), ctrl=Assistant.CTRL_Texte, obligatoire=False)
                self.Ajouter_question(code="tarif#%d" % index, titre=_("Quel est le tarif � appliquer � la cat�gorie n�%d ?") % index, commentaire=_("S�lectionnez une m�thode puis saisissez les param�tres demand�s."), ctrl=Assistant.CTRL_Tarif)

    def Suite(self):
        return Page_conclusion


class Page_conclusion(Assistant.Page):
    def __init__(self, parent):
        Assistant.Page.__init__(self, parent)
        self.Ajouter_question(titre=_("F�licitations, vous avez termin� de param�trer votre s�jour !"))
        self.Ajouter_question(titre=_("Cliquez maintenant sur le bouton Valider pour g�n�rer cette activit�."))

    def Suite(self):
        DB = GestionDB.DB()
        self.parent.Sauvegarde_standard(DB)
        IDactivite = self.parent.dict_valeurs["IDactivite"]


        # Unit�s de consommation
        listeIDunite = []
        listeDonnees = [
            ("IDactivite", IDactivite),
            ("nom", _("Journ�e Camp")),
            ("abrege", _("JC")),
            ("type", "Unitaire"),
            ("date_debut", "1977-01-01"),
            ("date_fin", "2999-01-01"),
            ("repas", 0),
            ("ordre", 1)
            ]
        IDunite = DB.ReqInsert("unites", listeDonnees)
        listeIDunite.append(IDunite)

        # Unit� de remplissage
        listeIDuniteRemplissage = []
        listeDonnees = [
            ("IDactivite", IDactivite),
            ("nom", _("Journ�e Camp")),
            ("abrege", _("JC")),
            ("seuil_alerte", 5),
            ("date_debut", "1977-01-01"),
            ("date_fin", "2999-01-01"),
            ("afficher_page_accueil", 1),
            ("afficher_grille_conso", 1),
            ("ordre", 1),
            ]
        IDunite_remplissage = DB.ReqInsert("unites_remplissage", listeDonnees)
        listeIDuniteRemplissage.append(IDunite_remplissage)

        listeDonnees = [("IDunite_remplissage", IDunite_remplissage), ("IDunite", IDunite),]
        DB.ReqInsert("unites_remplissage_unites", listeDonnees)

        # Ouvertures
        listeAjouts = []
        listeDates = list(rrule.rrule(rrule.DAILY, dtstart=self.parent.dict_valeurs["date_debut"], until=self.parent.dict_valeurs["date_fin"]))
        for date in listeDates :
            for IDgroupe in self.parent.dict_valeurs["listeIDgroupe"]:
                for IDunite in listeIDunite :
                    listeAjouts.append((IDactivite, IDunite, IDgroupe, date.date()))

        if len(listeAjouts) > 0 :
            DB.Executermany("INSERT INTO ouvertures (IDactivite, IDunite, IDgroupe, date) VALUES (?, ?, ?, ?)", listeAjouts, commit=False)

        # Remplissage
        if self.parent.dict_valeurs["nbre_inscrits_max"] not in (None, 0) :
            listeAjouts = []
            for date in listeDates :
                for IDgroupe in self.parent.dict_valeurs["listeIDgroupe"] :
                    for IDunite_remplissage in listeIDuniteRemplissage :
                        listeAjouts.append((IDactivite, IDunite_remplissage, IDgroupe, date.date(), self.parent.dict_valeurs["nbre_inscrits_max"]))

            if len(listeAjouts) > 0 :
                DB.Executermany("INSERT INTO remplissage (IDactivite, IDunite_remplissage, IDgroupe, date, places) VALUES (?, ?, ?, ?, ?)", listeAjouts, commit=False)

        # Nom de tarif
        nom_tarif = self.parent.dict_valeurs["nom"]
        listeDonnees = [("IDactivite", IDactivite), ("nom", nom_tarif)]
        IDnom_tarif = DB.ReqInsert("noms_tarifs", listeDonnees)

        # Cat�gories de tarifs
        listeCategoriesEtTarifs = []

        # Si cat�gorie unique
        if self.parent.dict_valeurs["has_categories_tarifs"] == False :
            listeDonnees = [("IDactivite", IDactivite), ("nom", _("Cat�gorie unique"))]
            IDcategorie_tarif = DB.ReqInsert("categories_tarifs", listeDonnees)
            track_tarif = self.parent.dict_valeurs["tarif"]
            listeCategoriesEtTarifs.append((IDcategorie_tarif, track_tarif))

        # Si plusieurs cat�gories
        if self.parent.dict_valeurs["has_categories_tarifs"] == True :
            nbre_categories_tarifs = self.parent.dict_valeurs["nbre_categories_tarifs"]
            for index in range(1, nbre_categories_tarifs+1):
                nom_categorie_tarif = self.parent.dict_valeurs["nom_categorie_tarif#%d" % index]
                listeDonnees = [("IDactivite", IDactivite), ("nom", nom_categorie_tarif)]
                IDcategorie_tarif = DB.ReqInsert("categories_tarifs", listeDonnees)
                track_tarif = self.parent.dict_valeurs["tarif#%d" % index]
                listeCategoriesEtTarifs.append((IDcategorie_tarif, track_tarif))

        # Tarifs
        listeTarifs = []
        for IDcategorie_tarif, track_tarif in listeCategoriesEtTarifs :
            track_tarif.MAJ({
                "IDactivite": IDactivite,
                "IDnom_tarif": IDnom_tarif,
                "type": "FORFAIT",
                "date_debut" : self.parent.dict_valeurs["date_debut"],
                "categories_tarifs" : str(IDcategorie_tarif),
                "forfait_saisie_manuelle" : 0,
                "forfait_saisie_auto" : 1,
                "forfait_suppression_auto" : 1,
                "label_prestation" : "nom_tarif",
                "options" : "calendrier",
                })
            listeTarifs.append(track_tarif)

        self.parent.Sauvegarde_tarifs(DB, listeTarifs)

        DB.Close()

        # Fermeture
        self.parent.Quitter()
        return False






class Dialog(Assistant.Dialog):
    def __init__(self, parent):
        Assistant.Dialog.__init__(self, parent, page_introduction=Page_introduction)




if __name__ == "__main__":
    app = wx.App(0)
    #wx.InitAllImageHandlers()
    dialog_1 = Dialog(None)
    app.SetTopWindow(dialog_1)
    dialog_1.ShowModal()
    app.MainLoop()
