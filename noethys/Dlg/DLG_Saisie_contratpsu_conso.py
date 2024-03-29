#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activit�s
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-15 Ivan LUCAS
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------


import Chemins
from Utils import UTILS_Adaptations
from Utils.UTILS_Traduction import _
import wx
from Ctrl import CTRL_Bouton_image
import datetime
from Ctrl import CTRL_Saisie_date
from Ol import OL_Contrats_planning_elements
import GestionDB
from Utils import UTILS_Dates
import wx.lib.dialogs as dialogs
import copy

from Ctrl import CTRL_Calendrier
from Dlg.DLG_Saisie_contrat_conso_detail import CTRL_Unites




class Panel_planning(wx.Panel):
    def __init__(self, parent, clsbase=None):
        wx.Panel.__init__(self, parent, id=-1, style=wx.TAB_TRAVERSAL)
        self.parent = parent
        self.clsbase = clsbase

        self.date_debut = self.clsbase.GetValeur("date_debut")
        self.date_fin = self.clsbase.GetValeur("date_fin")
        self.IDactivite = self.clsbase.GetValeur("IDactivite")
        self.IDunite_prevision = self.clsbase.GetValeur("IDunite_prevision")

        # G�n�ralit�s
        self.box_generalites_staticbox = wx.StaticBox(self, wx.ID_ANY, _("P�riode d'application"))
        self.label_periode = wx.StaticText(self, wx.ID_ANY, _("Dates :"))
        self.ctrl_date_debut = CTRL_Saisie_date.Date2(self)
        self.label_au = wx.StaticText(self, wx.ID_ANY, _("au"))
        self.ctrl_date_fin = CTRL_Saisie_date.Date2(self)

        # Planning
        self.box_planning_staticbox = wx.StaticBox(self, wx.ID_ANY, _("Planning"))

        self.ctrl_planning_detail = OL_Contrats_planning_elements.ListView(self, id=-1, IDactivite=self.IDactivite, IDunite=self.IDunite_prevision, style=wx.LC_REPORT|wx.SUNKEN_BORDER|wx.LC_SINGLE_SEL|wx.LC_HRULES|wx.LC_VRULES)
        self.ctrl_planning_detail.SetMinSize((50, 50))

        self.bouton_ajouter = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Ajouter.png"), wx.BITMAP_TYPE_ANY))
        self.bouton_modifier = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Modifier.png"), wx.BITMAP_TYPE_ANY))
        self.bouton_supprimer = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Supprimer.png"), wx.BITMAP_TYPE_ANY))

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_BUTTON, self.ctrl_planning_detail.Ajouter, self.bouton_ajouter)
        self.Bind(wx.EVT_BUTTON, self.ctrl_planning_detail.Modifier, self.bouton_modifier)
        self.Bind(wx.EVT_BUTTON, self.ctrl_planning_detail.Supprimer, self.bouton_supprimer)

        self.ctrl_date_debut.SetDate(self.date_debut)
        self.ctrl_date_fin.SetDate(self.date_fin)
        self.ctrl_planning_detail.MAJ()

    def __set_properties(self):
        self.ctrl_date_debut.SetToolTip(wx.ToolTip(_("Saisissez une date de d�but")))
        self.ctrl_date_fin.SetToolTip(wx.ToolTip(_("Saisissez une date de fin")))
        self.bouton_ajouter.SetToolTip(wx.ToolTip(_("Cliquez ici pour ajouter un param�tre")))
        self.bouton_modifier.SetToolTip(wx.ToolTip(_("Cliquez ici pour modifier un param�tre")))
        self.bouton_supprimer.SetToolTip(wx.ToolTip(_("Cliquez ici pour supprimer un param�tre")))

    def __do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(3, 1, 10, 10)

        # G�n�ralit�s
        box_generalites = wx.StaticBoxSizer(self.box_generalites_staticbox, wx.VERTICAL)
        grid_sizer_generalites = wx.FlexGridSizer(2, 2, 10, 10)
        grid_sizer_generalites.Add(self.label_periode, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_periode = wx.FlexGridSizer(1, 3, 5, 5)
        grid_sizer_periode.Add(self.ctrl_date_debut, 0, 0, 0)
        grid_sizer_periode.Add(self.label_au, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_periode.Add(self.ctrl_date_fin, 0, 0, 0)
        grid_sizer_generalites.Add(grid_sizer_periode, 1, wx.EXPAND, 0)
        box_generalites.Add(grid_sizer_generalites, 1, wx.ALL | wx.EXPAND, 10)
        grid_sizer_base.Add(box_generalites, 1, wx.TOP | wx.EXPAND, 10)

        # Planning
        box_planning = wx.StaticBoxSizer(self.box_planning_staticbox, wx.VERTICAL)
        grid_sizer_planning = wx.FlexGridSizer(1, 2, 5, 5)
        grid_sizer_planning.Add(self.ctrl_planning_detail, 1, wx.EXPAND, 0)

        grid_sizer_commandes = wx.FlexGridSizer(3, 1, 5, 5)
        grid_sizer_commandes.Add(self.bouton_ajouter, 0, 0, 0)
        grid_sizer_commandes.Add(self.bouton_modifier, 0, 0, 0)
        grid_sizer_commandes.Add(self.bouton_supprimer, 0, 0, 0)
        grid_sizer_planning.Add(grid_sizer_commandes, 1, wx.EXPAND, 0)

        grid_sizer_planning.AddGrowableRow(0)
        grid_sizer_planning.AddGrowableCol(0)

        box_planning.Add(grid_sizer_planning, 1, wx.ALL | wx.EXPAND, 10)
        grid_sizer_base.Add(box_planning, 1, wx.LEFT | wx.RIGHT | wx.EXPAND, 0)

        self.SetSizer(grid_sizer_base)
        grid_sizer_base.AddGrowableRow(1)
        grid_sizer_base.AddGrowableCol(0)
        self.Layout()

    def Validation(self):
        if self.ctrl_date_debut.GetDate() == None :
            dlg = wx.MessageDialog(self, _("Vous devez obligatoirement saisir la date de d�but d'application !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            self.ctrl_date_debut.SetFocus()
            return False

        if self.ctrl_date_fin.GetDate() == None :
            dlg = wx.MessageDialog(self, _("Vous devez obligatoirement saisir la date de fin d'application !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            self.ctrl_date_fin.SetFocus()
            return False

        if self.ctrl_date_debut.GetDate() > self.ctrl_date_fin.GetDate() :
            dlg = wx.MessageDialog(self, _("La date de d�but doit �tre inf�rieure � la date de fin !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return False

        if self.ctrl_date_debut.GetDate() < self.date_debut :
            dlg = wx.MessageDialog(self, _("La date de d�but ne peut pas �tre inf�rieure � la date de d�but du contrat !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return False

        if self.ctrl_date_fin.GetDate() > self.date_fin :
            dlg = wx.MessageDialog(self, _("La date de fin ne peut pas �tre sup�rieure � la date de fin du contrat !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return False

        donnees = self.GetDonnees()
        if len(donnees) == 0 :
            dlg = wx.MessageDialog(self, _("Vous devez obligatoirement d�finir au moins un param�tre de planning !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return False

        return True

    def GetDonnees(self):
        # R�cup�ration des param�tres
        date_debut = self.ctrl_date_debut.GetDate()
        date_fin = self.ctrl_date_fin.GetDate()
        listeConso = self.ctrl_planning_detail.GetConso(date_debut, date_fin)
        return listeConso


class Panel_calendrier(wx.Panel):
    def __init__(self, parent, clsbase=None):
        wx.Panel.__init__(self, parent, id=-1, style=wx.TAB_TRAVERSAL)
        self.parent = parent
        self.clsbase = clsbase

        self.date_debut = self.clsbase.GetValeur("date_debut")
        self.date_fin = self.clsbase.GetValeur("date_fin")
        self.IDactivite = self.clsbase.GetValeur("IDactivite")
        self.IDunite_prevision = self.clsbase.GetValeur("IDunite_prevision")

        # Calendrier
        self.box_calendrier_staticbox = wx.StaticBox(self, -1, _("Calendrier"))
        self.ctrl_calendrier = CTRL_Calendrier.CTRL(self, afficheBoutonAnnuel=True, multiSelections=True)
        self.ctrl_calendrier.SetMinSize((200, 200))

        # Unites
        self.box_unites_staticbox = wx.StaticBox(self, -1, _("Unit�s"))
        self.ctrl_unites = CTRL_Unites(self, IDactivite=self.IDactivite, IDunite=self.IDunite_prevision)
        self.ctrl_unites.SetMinSize((330, 100))

        self.__do_layout()

        # Init
        self.ctrl_unites.MAJ()

    def __do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(rows=4, cols=1, vgap=10, hgap=10)

        # Calendrier
        box_calendrier = wx.StaticBoxSizer(self.box_calendrier_staticbox, wx.VERTICAL)
        box_calendrier.Add(self.ctrl_calendrier, 1, wx.EXPAND | wx.ALL, 10)
        grid_sizer_base.Add(box_calendrier, 1, wx.TOP|wx.EXPAND, 10)

        # Unit�s
        box_unites = wx.StaticBoxSizer(self.box_unites_staticbox, wx.VERTICAL)
        box_unites.Add(self.ctrl_unites, 1, wx.ALL|wx.EXPAND, 10)
        grid_sizer_base.Add(box_unites, 1, wx.LEFT|wx.RIGHT|wx.EXPAND, 0)

        self.SetSizer(grid_sizer_base)
        grid_sizer_base.AddGrowableRow(0)
        grid_sizer_base.AddGrowableCol(0)
        self.Layout()

    def Validation(self):
        listeDates = self.ctrl_calendrier.GetSelections()
        listeDates.sort()
        if len(listeDates) == 0 :
            dlg = wx.MessageDialog(self, _("Vous devez obligatoirement s�lectionner au moins une date dans le calendrier !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return False

        if self.ctrl_unites.Validation() == False :
            return False

        if listeDates[0] < self.date_debut :
            dlg = wx.MessageDialog(self, _("La date de d�but ne peut pas �tre inf�rieure � la date de d�but du contrat !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return False

        if listeDates[-1] > self.date_fin :
            dlg = wx.MessageDialog(self, _("La date de fin ne peut pas �tre sup�rieure � la date de fin du contrat !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return False

        return True

    def GetDonnees(self):
        listeDates = self.ctrl_calendrier.GetSelections()
        listeUnites = self.ctrl_unites.GetDonnees()
        listeConso = []

        for date in listeDates :

            for dictUnite in listeUnites :
                IDunite = dictUnite["IDunite"]
                options = dictUnite["options"]

                if "heure_debut" in options:
                    heure_debut = options["heure_debut"]
                else :
                    heure_debut = self.dictUnites[IDunite]["heure_debut"]
                if "heure_fin" in options:
                    heure_fin = options["heure_fin"]
                else :
                    heure_fin = self.dictUnites[IDunite]["heure_fin"]

                if "quantite" in options:
                    quantite = options["quantite"]
                else :
                    quantite = None

                dictConso = {
                    "IDconso" : None,
                    "date" : date,
                    "IDunite" : IDunite,
                    "heure_debut" : heure_debut,
                    "heure_fin" : heure_fin,
                    "quantite" : quantite,
                    "etat" : "reservation",
                    "etiquettes" : [],
                    }
                listeConso.append(dictConso)

        return listeConso

class Notebook(wx.Choicebook):
    def __init__(self, parent, clsbase=None):
        wx.Choicebook.__init__(self, parent, id=-1, style= wx.BK_DEFAULT)
        self.clsbase = clsbase

        self.dictPages = {}

        self.listePages = [
            ("planning", _("Mode planning"), Panel_planning(self, clsbase=clsbase), "Calendrier.png"),
            ("calendrier", _("Mode Calendrier"), Panel_calendrier(self, clsbase=clsbase), "Calendrier.png"),
            ]

        # ImageList pour le NoteBook
        il = wx.ImageList(32, 32)
        index = 0
        self.dictImages = {}
        for codePage, labelPage, ctrlPage, imgPage in self.listePages :
            self.dictImages[codePage] = il.Add(wx.Bitmap(Chemins.GetStaticPath('Images/32x32/%s' % imgPage), wx.BITMAP_TYPE_PNG))
            index += 1
        self.AssignImageList(il)

        # Cr�ation des pages
        index = 0
        for codePage, labelPage, ctrlPage, imgPage in self.listePages :
            self.AddPage(ctrlPage, labelPage)
            self.SetPageImage(index, self.dictImages[codePage])
            self.dictPages[codePage] = {'ctrl' : ctrlPage, 'index' : index}
            index += 1

    def AffichePage(self, codePage="", forcer=False):
        indexPage = self.dictPages[codePage]["index"]
        self.SetSelection(indexPage)
        if forcer == True :
            self.GetChoiceCtrl().Enable(False)

    def GetCodePage(self):
        index = self.GetSelection()
        return self.listePages[index][0]

    def GetPage(self):
        index = self.GetSelection()
        return self.listePages[index][2]

    def Validation(self) :
        page = self.dictPages[self.GetCodePage()]["ctrl"]
        return page.Validation()

    def GetDonnees(self):
        page = self.dictPages[self.GetCodePage()]["ctrl"]
        return page.GetDonnees()


class Dialog(wx.Dialog):
    def __init__(self, parent, clsbase=None):
        wx.Dialog.__init__(self, parent, -1, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX)
        self.parent = parent
        self.clsbase = clsbase
        self.IDconso = None

        self.notebook = Notebook(self, clsbase=clsbase)

        # Boutons
        self.bouton_aide = CTRL_Bouton_image.CTRL(self, texte=_("Aide"), cheminImage="Images/32x32/Aide.png")
        self.bouton_ok = CTRL_Bouton_image.CTRL(self, texte=_("Ok"), cheminImage="Images/32x32/Valider.png")
        self.bouton_annuler = CTRL_Bouton_image.CTRL(self, texte=_("Annuler"), cheminImage="Images/32x32/Annuler.png")

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_BUTTON, self.OnBoutonAide, self.bouton_aide)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonOk, self.bouton_ok)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAnnuler, self.bouton_annuler)

        # # Init
        # self.dictUnites = self.Importation_unites()
        # self.dictOuvertures = self.GetOuverturesUnites()



    def __set_properties(self):
        self.SetTitle(_("G�n�ration de consommations"))
        self.bouton_aide.SetToolTip(wx.ToolTip(_("Cliquez ici pour obtenir de l'aide")))
        self.bouton_ok.SetToolTip(wx.ToolTip(_("Cliquez ici pour valider")))
        self.bouton_annuler.SetToolTip(wx.ToolTip(_("Cliquez ici pour annuler")))
        self.SetMinSize((400, 580))

    def __do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(3, 1, 10, 10)
        
        grid_sizer_base.Add(self.notebook, 1, wx.LEFT | wx.RIGHT | wx.TOP | wx.EXPAND, 10)
        
        # Boutons
        grid_sizer_boutons = wx.FlexGridSizer(1, 4, 10, 10)
        grid_sizer_boutons.Add(self.bouton_aide, 0, 0, 0)
        grid_sizer_boutons.Add((20, 20), 0, wx.EXPAND, 0)
        grid_sizer_boutons.Add(self.bouton_ok, 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_annuler, 0, 0, 0)
        grid_sizer_boutons.AddGrowableCol(1)
        grid_sizer_base.Add(grid_sizer_boutons, 1, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 10)
        
        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)
        grid_sizer_base.AddGrowableRow(0)
        grid_sizer_base.AddGrowableCol(0)
        self.Layout()
        self.CenterOnScreen()

    def OnBoutonAide(self, event): 
        from Utils import UTILS_Aide
        UTILS_Aide.Aide("Contrats")

    def OnBoutonAnnuler(self, event): 
        self.EndModal(wx.ID_CANCEL)   

    def OnBoutonOk(self, event):
        if self.notebook.Validation()  == False :
            return False

        # G�n�ration des consommations
        listeConso = self.parent.Generation(listeConso=self.notebook.GetDonnees(), IDconso=self.IDconso)
        if listeConso == False :
            return
        else :
            self.listeConso = listeConso

        # Fermeture de la fen�tre
        self.EndModal(wx.ID_OK)
    

    # def Importation_unites(self):
    #     # R�cup�ration des unit�s
    #     DB = GestionDB.DB()
    #     req = """SELECT IDunite, nom, abrege, type, heure_debut, heure_fin
    #     FROM unites
    #     WHERE IDactivite=%d
    #     ORDER BY ordre;""" % self.clsbase.GetValeur("IDactivite")
    #     DB.ExecuterReq(req,MsgBox="ExecuterReq")
    #     listeDonnees = DB.ResultatReq()
    #     dictUnites = {}
    #     for IDunite, nom, abrege, type, heure_debut, heure_fin in listeDonnees :
    #         dictUnites[IDunite] = {"nom":nom, "abrege":abrege, "type":type, "heure_debut":heure_debut, "heure_fin":heure_fin, "unites_incompatibles" : []}
    #
    #     # R�cup�re les incompatibilit�s entre unit�s
    #     req = """SELECT IDunite_incompat, IDunite, IDunite_incompatible
    #     FROM unites_incompat;"""
    #     DB.ExecuterReq(req,MsgBox="ExecuterReq")
    #     listeDonnees = DB.ResultatReq()
    #     DB.Close()
    #     for IDunite_incompat, IDunite, IDunite_incompatible in listeDonnees :
    #         if dictUnites.has_key(IDunite) : dictUnites[IDunite]["unites_incompatibles"].append(IDunite_incompatible)
    #         if dictUnites.has_key(IDunite_incompatible) : dictUnites[IDunite_incompatible]["unites_incompatibles"].append(IDunite)
    #
    #     return dictUnites
    #
    # def GetOuverturesUnites(self):
    #     DB = GestionDB.DB()
    #     req = """SELECT IDouverture, IDunite, IDgroupe, date
    #     FROM ouvertures
    #     WHERE IDactivite=%d
    #     ORDER BY date; """ % self.clsbase.GetValeur("IDactivite")
    #     DB.ExecuterReq(req,MsgBox="ExecuterReq")
    #     listeDonnees = DB.ResultatReq()
    #     DB.Close()
    #     dictOuvertures = {}
    #     for IDouverture, IDunite, IDgroupe, date in listeDonnees :
    #         date = UTILS_Dates.DateEngEnDateDD(date)
    #         dictOuvertures[(date, IDunite, IDgroupe)] = IDouverture
    #     return dictOuvertures
    #
    # def VerifieCompatibilitesUnites(self, IDunite1=None, IDunite2=None):
    #     listeIncompatibilites = self.dictUnites[IDunite1]["unites_incompatibles"]
    #     if IDunite2 in listeIncompatibilites :
    #         return False
    #     return True
    #
    # def Generation(self):
    #     listeConso = self.notebook.GetDonnees()
    #
    #     # V�rification de la validit� des dates
    #     listeAnomalies = []
    #     nbreConsoValides = 0
    #     self.listeConso = []
    #
    #     for dictConso in listeConso :
    #
    #         index = 0
    #         dateFr = UTILS_Dates.DateDDEnFr(dictConso["date"])
    #         valide = True
    #
    #         # Recherche si pas d'incompatibilit�s avec les conso d�j� saisies
    #         # for dictConsoTemp in listeConso :
    #         #     if dictConso["date"] == dictConsoTemp["date"] :
    #         #         nomUnite1 = self.dictUnites[dictConso["IDunite"]]["nom"]
    #         #         nomUnite2 = self.dictUnites[dictConsoTemp["IDunite"]]["nom"]
    #         #
    #         #         if self.VerifieCompatibilitesUnites(dictConsoTemp["IDunite"], dictConso["IDunite"]) == False :
    #         #             listeAnomalies.append(_("%s : Unit� %s incompatible avec unit� %s d�j� pr�sente") % (dateFr, nomUnite1, nomUnite2))
    #         #             valide = False
    #         #
    #         #         if dictConso["IDunite"] == dictConsoTemp["IDunite"] :
    #         #             if self.dictUnites[dictConso["IDunite"]]["type"] == "Multihoraire" :
    #         #                 if dictConso["heure_fin"] > dictConsoTemp["heure_debut"] and dictConso["heure_debut"] < dictConsoTemp["heure_fin"] :
    #         #                     listeAnomalies.append(_("%s : L'unit� multihoraires %s chevauche une consommation d'une unit� identique") % (dateFr, nomUnite1))
    #         #                     valide = False
    #         #             else :
    #         #                 listeAnomalies.append(_("%s : Unit� %s d�j� pr�sente") % (dateFr, nomUnite1))
    #         #                 valide = False
    #
    #         # V�rifie si unit� ouverte
    #         IDgroupe = self.clsbase.GetValeur("IDgroupe")
    #         if IDgroupe != None and self.dictOuvertures.has_key((dictConso["date"], dictConso["IDunite"], IDgroupe)) == False :
    #             listeAnomalies.append(_("%s : Unit� %s ferm�e") % (dateFr, self.dictUnites[dictConso["IDunite"]]["nom"]))
    #             valide = False
    #
    #         # IDconso pour les modifications
    #         if self.IDconso != None :
    #             dictConso["IDconso"] = self.IDconso
    #
    #         # Insertion de la conso valid�e
    #         if valide == True :
    #             self.listeConso.append(dictConso)
    #             nbreConsoValides += 1
    #
    #             index += 1
    #
    #     # Signalement des anomalies
    #     if len(listeAnomalies) :
    #         message1 = _("Les %d anomalies suivantes ont �t� trouv�es.\n\nSouhaitez-vous tout de m�me g�n�rer les %d autres consommations ?") % (len(listeAnomalies), nbreConsoValides)
    #         message2 = "\n".join(listeAnomalies)
    #         dlg = dialogs.MultiMessageDialog(self, message1, caption = _("G�n�ration"), msg2=message2, style = wx.ICON_EXCLAMATION | wx.YES|wx.CANCEL|wx.YES_DEFAULT, btnLabels={wx.ID_YES : _("Oui"), wx.ID_CANCEL : _("Annuler")})
    #         reponse = dlg.ShowModal()
    #         dlg.Destroy()
    #         if reponse != wx.ID_YES :
    #             return False
    #
    #     if nbreConsoValides == 0 :
    #         dlg = wx.MessageDialog(self, _("Il n'y a aucune consommation valide � g�n�rer !"), _("G�n�ration"), wx.OK | wx.ICON_EXCLAMATION)
    #         dlg.ShowModal()
    #         dlg.Destroy()
    #         return False
    #
    #     # Demande de confirmation
    #     if self.IDconso == None :
    #         dlg = wx.MessageDialog(self, _("Confirmez-vous la g�n�ration de %d consommations ?") % nbreConsoValides, _("G�n�ration"), wx.YES_NO|wx.NO_DEFAULT|wx.CANCEL|wx.ICON_QUESTION)
    #         reponse = dlg.ShowModal()
    #         dlg.Destroy()
    #         if reponse != wx.ID_YES :
    #             return False
    #
    #     return True

    def GetListeConso(self):
        return self.listeConso

    def SetConso(self, track=None):
        self.notebook.AffichePage("calendrier", forcer=True)
        pageCalendrier = self.notebook.GetPage()

        # M�morise l'IDconso
        self.IDconso = track.IDconso

        # S�lectionne la date
        pageCalendrier.ctrl_calendrier.SelectJours([track.date,])
        pageCalendrier.ctrl_calendrier.Enable(False)

        # S�lectionne les unit�s
        listeUnites = [
            {"IDunite" : track.IDunite, "options" : {"interdit_ajout" : True, "heure_debut" : track.heure_debut, "heure_fin" : track.heure_fin, "quantite" : track.quantite}},
            ]
        pageCalendrier.ctrl_unites.SetDonnees(listeUnites)






if __name__ == "__main__":
    app = wx.App(0)
    #wx.InitAllImageHandlers()
    # Importation d'un contrat pour les tests
    from Dlg.DLG_Saisie_contratpsu import Base
    clsbase = Base(IDcontrat=8)
    clsbase.Calculer()
    # Ouverture DLG
    dlg = Dialog(None, clsbase=clsbase)
    app.SetTopWindow(dlg)
    dlg.ShowModal()
    app.MainLoop()
