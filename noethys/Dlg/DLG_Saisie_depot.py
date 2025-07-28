#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys branche Matthania
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS, JB
# Copyright:       (c) 2010-11 Ivan LUCAS, JB
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------

from Utils.UTILS_Traduction import _
import wx
from Ctrl import CTRL_Bouton_image
import datetime
import wx.html as html

from Ctrl import CTRL_Saisie_date
from Ol import OL_Reglements_depots
from Dlg import DLG_Saisie_depot_ajouter
from Utils import UTILS_Titulaires

import Chemins
import GestionDB

from Utils import UTILS_Config
SYMBOLE = UTILS_Config.GetParametre("monnaie_symbole", "€")

def DateEngFr(textDate):
    if textDate == None: return ""
    textDate = str(textDate)
    text = str(textDate[8:10]) + "/" + str(textDate[5:7]) + "/" + str(textDate[:4])
    return text

def DateComplete(dateDD):
    """ Transforme une date DD en date complète : Ex : lundi 15 janvier 2008 """
    listeJours = (_("Lundi"), _("Mardi"), _("Mercredi"), _("Jeudi"), _("Vendredi"), _("Samedi"), _("Dimanche"))
    listeMois = (_("janvier"), _("février"), _("mars"), _("avril"), _("mai"), _("juin"), _("juillet"), _("août"), _("septembre"), _("octobre"), _("novembre"), _("décembre"))
    dateComplete = listeJours[dateDD.weekday()] + " " + str(dateDD.day) + " " + listeMois[dateDD.month-1] + " " + str(dateDD.year)
    return dateComplete

def DateEngEnDateDD(dateEng):
    if dateEng and not isinstance(dateEng,str): dateEng = str(dateEng)
    return datetime.date(int(dateEng[:4]), int(dateEng[5:7]), int(dateEng[8:10]))


class Choix_compte(wx.Choice):
    def __init__(self, parent):
        wx.Choice.__init__(self, parent, -1) 
        self.parent = parent
        self.listeNoms = []
        self.listeID = []
        self.dictNumeros = {}
        self.SetListeDonnees() 
        self.SetID(0)
    
    def SetListeDonnees(self):
        self.listeNoms = [_("------- Aucun compte bancaire -------")]
        self.listeID = [0,]
        DB = GestionDB.DB()
        req = """SELECT IDcompte, nom, numero
        FROM comptes_bancaires 
        ORDER BY nom;"""
        DB.ExecuterReq(req,MsgBox="DLG_Saisie_depot")
        listeDonnees = DB.ResultatReq()
        DB.Close()
        if len(listeDonnees) == 0 : return
        for IDcompte, nom, numero in listeDonnees :
            self.listeNoms.append(nom)
            self.listeID.append(IDcompte)
            self.dictNumeros[IDcompte] = numero
        self.SetItems(self.listeNoms)
    
    def SetID(self, ID=None):
        index = 0
        for IDcompte in self.listeID :
            if IDcompte == ID :
                 self.SetSelection(index)
            index += 1

    def GetID(self):
        index = self.GetSelection()
        if index == -1 : return None
        if index == 0 : return 0
        return self.listeID[index]
    
    def GetNumero(self):
        IDcompte = self.GetID() 
        if IDcompte != 0 and IDcompte != None :
            return self.dictNumeros[IDcompte]
        else:
            return None

class zzChoix_mode(wx.ComboCtrl):
    # choix du mode de réglement à proposer comme nom par défaut
    def __init__(self, parent):
        wx.ComboCtrl.__init__(self, parent, -1,style=wx.TE_PROCESS_ENTER)
        self.parent = parent
        self.listeNoms = []
        self.listeID = []
        self.SetListeDonnees()
        self.SetID(0)

    def SetListeDonnees(self):
        self.listeNoms = [
            _("------- Aucun mode de règlement choisi -------")]
        self.listeID = [0, ]
        DB = GestionDB.DB()
        req = """SELECT IDmode, label
        FROM modes_reglements 
        ORDER BY IDmode;"""
        DB.ExecuterReq(req, MsgBox="DLG_Saisie_depot.choix_mode")
        listeDonnees = DB.ResultatReq()
        DB.Close()
        if len(listeDonnees) == 0: return
        i = 0
        for IDmode, nom in listeDonnees:
            self.listeNoms.append(nom)
            self.listeID.append(IDmode)
            self.SetValue(nom)
            i += 1

    def SetID(self, ID=None):
        index = 0
        for IDcompte in self.listeID:
            if IDcompte == ID:
                self.SetSelection(index)
            index += 1

    def GetID(self):
        index = self.GetSelection()
        if index == -1: return None
        if index == 0: return 0
        return self.listeID[index]

    def zzGetValue(self):
        index = self.GetID()
        return self.listeNoms[index]

class Choix_mode(wx.ComboCtrl):
    def __init__(self, parent):
        wx.ComboCtrl.__init__(self, parent, -1,"",style=wx.TE_PROCESS_ENTER)
        self.popup = ListCtrlComboPopup()
        self.SetPopupControl(self.popup)
        self.listeNoms = []
        self.listeID = []
        self.SetListeDonnees()

    def SetListeDonnees(self):
        nom = "------- Aucun mode de règlement choisi -------"
        self.SetText(nom)
        DB = GestionDB.DB()
        req = """SELECT IDmode, label
        FROM modes_reglements 
        ORDER BY IDmode;"""
        DB.ExecuterReq(req, MsgBox="DLG_Saisie_depot.choix_mode")
        listeDonnees = DB.ResultatReq()
        DB.Close()
        if len(listeDonnees) == 0: return
        i = 0
        for IDmode, nom in listeDonnees:
            self.listeNoms.append(nom)
            self.listeID.append(IDmode)
            self.popup.AddItem(nom)
            i += 1

    def GetID(self):
        value = self.GetValue()
        if value in self.listeNoms:
            index = self.listeNoms.index(value)
        else:
            return None
        return self.listeID[index]

class ListCtrlComboPopup(wx.ComboPopup):
    def Init(self):
        self.value = -1
        self.curitem = -1

    def Create(self, parent):
        self.lc = wx.ListCtrl(parent, style=wx.LC_LIST | wx.LC_SINGLE_SEL | wx.SIMPLE_BORDER)
        self.lc.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
        return True

    def GetControl(self):
        return self.lc

    def AddItem(self, text):
        self.lc.InsertItem(self.lc.GetItemCount(), text)

    def OnLeftDown(self, event):
        item, _ = self.lc.HitTest(event.GetPosition())
        if item >= 0:
            self.value = item
            self.Dismiss()

    def GetStringValue(self):
        if self.value >= 0:
            return self.lc.GetItemText(self.value)
        return ""



# ------------------------------------------------------------------------------------------------------------------------------------------

class CTRL_Infos(html.HtmlWindow):
    def __init__(self, parent, texte="", hauteur=32,  couleurFond=(255, 255, 255), style=0):
        html.HtmlWindow.__init__(self, parent, -1, style=style)#, style=wx.html.HW_NO_SELECTION | wx.html.HW_SCROLLBAR_NEVER | wx.NO_FULL_REPAINT_ON_RESIZE)
        self.parent = parent
        if "gtk2" in wx.PlatformInfo:
            self.SetStandardFonts()
        self.SetBorders(3)
        self.SetMinSize((-1, hauteur))
        self.couleurFond = couleurFond
        font = self.parent.GetFont()
        self.SetFont(font)
        self.SetLabel(texte)
    
    def SetLabel(self, texte=""):
        self.SetPage(u"""<BODY><FONT SIZE=2 COLOR='#000000'>%s</FONT></BODY>""" % texte)
        self.SetBackgroundColour(self.couleurFond)
    
# ---------------------------------------------------------------------------------------------------------------------------------------

class Track(object):
    def __init__(self, donnees):
        self.IDreglement = donnees[0]
        self.compte_payeur = donnees[1]
        self.date = DateEngEnDateDD(donnees[2])
        self.IDmode = donnees[3]
        self.nom_mode = donnees[4]
        self.IDemetteur = donnees[5]
        self.nom_emetteur = donnees[6]
        self.numero_piece = donnees[7]
        self.montant = donnees[8]
        self.IDpayeur = donnees[9]
        self.nom_payeur = donnees[10]
        self.observations = donnees[11]
        self.numero_quittancier = donnees[12]
        self.IDprestation_frais = donnees[13]
        self.IDcompte = donnees[14]
        self.date_differe = donnees[15]
        if self.date_differe != None :
            self.date_differe = DateEngEnDateDD(self.date_differe)
        self.encaissement_attente = donnees[16]
        self.IDdepot = donnees[17]
        self.date_depot = donnees[18]
        if self.date_depot != None :
            self.date_depot = DateEngEnDateDD(self.date_depot)
        self.nom_depot = donnees[19]
        self.verrouillage_depot = donnees[20]
        self.date_saisie = donnees[21]
        if self.date_saisie != None :
            self.date_saisie = DateEngEnDateDD(self.date_saisie)
        self.IDutilisateur = donnees[22]
        self.montant_ventilation = donnees[23]
        if self.montant_ventilation == None :
            self.montant_ventilation = 0.0
        self.nom_compte = donnees[24]
        self.IDfamille = donnees[25]
        self.email_depots = ""
        self.adresse_intitule = donnees[26]
        self.avis_depot = donnees[27]
        self.compta = donnees[28]

        # Etat
        if self.IDdepot == None or self.IDdepot == 0 :
            self.inclus = False
        else:
            self.inclus = True

# ---------------------------------------------------------------------------------------------------------------------------------------------

class Dialog(wx.Dialog):
    def __init__(self, parent, IDdepot=None):
        wx.Dialog.__init__(self, parent, -1, name="DLG_Saisie_depot", style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX)
        self.parent = parent
        self.IDdepot = IDdepot
        self.initial = True
        self.nom = ""
        self.saisie = False
        # Reglements
        self.staticbox_parametres_staticbox = wx.StaticBox(self, -1, _("Paramètres"))
        self.label_nom = wx.StaticText(self, -1, _("Nom du dépôt :"))
        self.ctrl_nom = Choix_mode(self)

        self.label_date = wx.StaticText(self, -1, _("Date du dépôt :"))
        self.ctrl_date = CTRL_Saisie_date.Date2(self)
        self.label_verrouillage = wx.StaticText(self, -1, _("Verrouillage :"))
        self.ctrl_verrouillage = wx.CheckBox(self, -1, "")
        self.label_code_compta = wx.StaticText(self, -1, _("Forcer compta :"))
        self.ctrl_code_compta = wx.TextCtrl(self, -1, "")
        self.label_compte = wx.StaticText(self, -1, _("Compte bancaire :"))
        self.ctrl_compte = Choix_compte(self)
        self.label_observations = wx.StaticText(self, -1, _("Observations :"))
        self.ctrl_observations = wx.TextCtrl(self, -1, "", style=wx.TE_MULTILINE)
        
        # Reglements
        self.staticbox_reglements_staticbox = wx.StaticBox(self, -1, _("Règlements"))
        self.listviewAvecFooter = OL_Reglements_depots.ListviewAvecFooter(self, kwargs={"inclus" : True, "selectionPossible" : False}) 
        self.ctrl_reglements = self.listviewAvecFooter.GetListview()
        
        self.ctrl_infos = CTRL_Infos(self, hauteur=32, couleurFond="#F0FBED" , style=wx.html.HW_NO_SELECTION | wx.html.HW_SCROLLBAR_NEVER | wx.SUNKEN_BORDER)
        self.bouton_ajouter = CTRL_Bouton_image.CTRL(self, texte=_("Ajouter ou retirer des règlements"), cheminImage="Images/32x32/Reglement_ajouter.png")
        
        # Boutons
        self.bouton_aide = CTRL_Bouton_image.CTRL(self, texte=_("Aide"), cheminImage="Images/32x32/Aide.png")
        self.bouton_imprimer = CTRL_Bouton_image.CTRL(self, texte=_("Imprimer"), cheminImage="Images/32x32/Imprimante.png")
        self.bouton_avis_depots = CTRL_Bouton_image.CTRL(self, texte=_("Envoyer les avis de dépôt"), cheminImage="Images/32x32/Emails_exp.png")
        self.bouton_nouveau = CTRL_Bouton_image.CTRL(self, texte=_("Ok\nNouveau"), cheminImage="Images/32x32/Valider.png")
        self.bouton_ok = CTRL_Bouton_image.CTRL(self, texte=_("Ok"), cheminImage="Images/32x32/Valider.png")
        self.bouton_annuler = CTRL_Bouton_image.CTRL(self, texte=_("Annuler"), cheminImage="Images/32x32/Annuler.png")

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_BUTTON, self.OnBoutonAjouter, self.bouton_ajouter)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAide, self.bouton_aide)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonImprimer, self.bouton_imprimer)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAvisDepots, self.bouton_avis_depots)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonNouveau, self.bouton_nouveau)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonOk, self.bouton_ok)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAnnuler, self.bouton_annuler)
        self.Bind(wx.EVT_CHECKBOX, self.OnCheckVerrouillage, self.ctrl_verrouillage)

        # Importation lors d'une modification
        if self.IDdepot != None :
            self.SetTitle(_("Modification d'un dépôt"))
            self.Importation()
            self.OnCheckVerrouillage(None)
        else:
            self.SetTitle(_("Saisie d'un dépôt"))
            self.ctrl_date.SetDate(datetime.date.today())
        self.Init()

    def Init(self):
        # Importation des règlements
        self.tracks = self.GetTracks()
        self.ctrl_reglements.MAJ(tracks=self.tracks) 
        self.MAJinfos()

    def __set_properties(self):
        self.ctrl_date.SetToolTip(wx.ToolTip(_("Saisissez la date de dépôt")))
        self.bouton_imprimer.SetToolTip(wx.ToolTip(_("Cliquez ici pour imprimer la liste des règlements du dépôt")))
        self.bouton_avis_depots.SetToolTip(wx.ToolTip(_("Cliquez ici pour envoyer par Email des avis de dépôts")))
        self.ctrl_verrouillage.SetToolTip(wx.ToolTip(_("Cochez cette case si le dépôt doit être verrouillé. Dans ce cas, il devient impossible de modifier la liste des règlements qui le contient !")))
        self.ctrl_nom.SetToolTip(wx.ToolTip("Sélectionnez un mode règlement pour nom dépôt, modifiable ensuite"))
        self.ctrl_code_compta.SetToolTip(wx.ToolTip(_("Ce code comptable s'il est numérique aura priorité sur celui de l'organisme bancaire. Utile uniquement pour déroger aux comptes par défaut")))
        self.ctrl_compte.SetToolTip(wx.ToolTip(_("Sélectionnez le compte bancaire d'encaissement")))
        self.ctrl_observations.SetToolTip(wx.ToolTip(_("[Optionnel] Saisissez des commentaires")))
        self.bouton_ajouter.SetToolTip(wx.ToolTip(_("Cliquez ici pour ajouter ou retirer des règlements de ce dépôt")))
        self.bouton_aide.SetToolTip(wx.ToolTip(_("Cliquez ici obtenir de l'aide")))
        self.bouton_nouveau.SetToolTip(wx.ToolTip(_("Cliquez ici pour valider et créer un nouveau dépôt")))
        self.bouton_ok.SetToolTip(wx.ToolTip(_("Cliquez ici pour valider")))
        self.bouton_annuler.SetToolTip(wx.ToolTip(_("Cliquez ici pour annuler")))
        self.ctrl_code_compta.SetMinSize((120,20))
        self.SetMinSize((890, 720))

    def __do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(rows=3, cols=1, vgap=10, hgap=10)
        staticbox_reglements = wx.StaticBoxSizer(self.staticbox_reglements_staticbox, wx.VERTICAL)
        grid_sizer_reglements = wx.FlexGridSizer(rows=2, cols=1, vgap=10, hgap=10)
        grid_sizer_bas_reglements = wx.FlexGridSizer(rows=1, cols=2, vgap=10, hgap=10)
        staticbox_parametres = wx.StaticBoxSizer(self.staticbox_parametres_staticbox, wx.VERTICAL)
        grid_sizer_parametres = wx.FlexGridSizer(rows=1, cols=2, vgap=10, hgap=30)
        grid_sizer_haut_droit = wx.FlexGridSizer(rows=2, cols=2, vgap=5, hgap=5)
        grid_sizer_haut_gauche = wx.FlexGridSizer(rows=3, cols=2, vgap=5, hgap=5)
        grid_sizer_haut_gauche.Add(self.label_nom, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_haut_gauche.Add(self.ctrl_nom, 0,wx.EXPAND, 0)

        grid_sizer_haut_gauche.Add(self.label_date, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)

        grid_sizer_haut_date = wx.FlexGridSizer(rows=1, cols=5, vgap=5, hgap=5)
        grid_sizer_haut_date.Add(self.ctrl_date, 0, 0, 0)
        grid_sizer_haut_date.Add( (5, 5), 0, wx.EXPAND, 0)
        grid_sizer_haut_date.Add(self.label_verrouillage, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_haut_date.Add(self.ctrl_verrouillage, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_haut_date.AddGrowableCol(1)
        grid_sizer_haut_gauche.Add(grid_sizer_haut_date, 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0)

        grid_sizer_haut_gauche.Add(self.label_code_compta, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_haut_gauche.Add(self.ctrl_code_compta, 0, 0, 0)
        grid_sizer_haut_gauche.AddGrowableCol(1)
        grid_sizer_parametres.Add(grid_sizer_haut_gauche, 1, wx.EXPAND, 0)

        grid_sizer_haut_droit.Add(self.label_compte, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_haut_droit.Add(self.ctrl_compte, 0, wx.EXPAND, 0)
        grid_sizer_haut_droit.Add(self.label_observations, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_haut_droit.Add(self.ctrl_observations, 0, wx.EXPAND, 0)
        grid_sizer_haut_droit.AddGrowableRow(1)
        grid_sizer_haut_droit.AddGrowableCol(1)
        grid_sizer_parametres.Add(grid_sizer_haut_droit, 1, wx.EXPAND, 0)

        grid_sizer_parametres.AddGrowableCol(0)
        grid_sizer_parametres.AddGrowableCol(1)
        staticbox_parametres.Add(grid_sizer_parametres, 1, wx.ALL|wx.EXPAND, 10)
        grid_sizer_base.Add(staticbox_parametres, 1, wx.LEFT|wx.RIGHT|wx.TOP|wx.EXPAND, 10)
        grid_sizer_reglements.Add(self.listviewAvecFooter, 1, wx.EXPAND, 0)
        grid_sizer_bas_reglements.Add(self.ctrl_infos, 0, wx.EXPAND, 0)
        grid_sizer_bas_reglements.Add(self.bouton_ajouter, 0, wx.EXPAND, 0)
        grid_sizer_bas_reglements.AddGrowableCol(0)
        grid_sizer_reglements.Add(grid_sizer_bas_reglements, 1, wx.EXPAND, 0)
        grid_sizer_reglements.AddGrowableRow(0)
        grid_sizer_reglements.AddGrowableCol(0)
        staticbox_reglements.Add(grid_sizer_reglements, 1, wx.ALL|wx.EXPAND, 10)
        grid_sizer_base.Add(staticbox_reglements, 1, wx.LEFT|wx.RIGHT|wx.EXPAND, 10)
        
        grid_sizer_boutons = wx.FlexGridSizer(rows=1, cols=7, vgap=10, hgap=10)
        grid_sizer_boutons.Add(self.bouton_aide, 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_imprimer, 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_avis_depots, 0, 0, 0)
        grid_sizer_boutons.Add((20, 20), 0, wx.EXPAND, 0)
        grid_sizer_boutons.Add(self.bouton_nouveau, 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_ok, 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_annuler, 0, 0, 0)
        grid_sizer_boutons.AddGrowableCol(2)
        grid_sizer_base.Add(grid_sizer_boutons, 1, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 10)
        
        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)
        grid_sizer_base.AddGrowableRow(1)
        grid_sizer_base.AddGrowableCol(0)
        self.Layout()
        self.CenterOnScreen() 

    def GetTracks(self):
        """ Récupération des données """
        if self.IDdepot == None : 
            IDdepot = 0
        else:
            IDdepot = self.IDdepot
            
        db = GestionDB.DB()
        req = """SELECT 
        reglements.IDreglement, reglements.IDcompte_payeur, reglements.date, 
        reglements.IDmode, modes_reglements.label, 
        reglements.IDemetteur, emetteurs.nom, 
        reglements.numero_piece, reglements.montant, 
        payeurs.IDpayeur, payeurs.nom, 
        reglements.observations, numero_quittancier, IDprestation_frais, reglements.IDcompte, date_differe, 
        encaissement_attente, 
        reglements.IDdepot, depots.date, depots.nom, depots.verrouillage, 
        date_saisie, IDutilisateur, 
        SUM(ventilation.montant) AS total_ventilation,
        comptes_bancaires.nom,
        familles.IDfamille, 
        familles.adresse_intitule,
        reglements.avis_depot,
        reglements.compta
        FROM reglements
        LEFT JOIN ventilation ON reglements.IDreglement = ventilation.IDreglement
        LEFT JOIN modes_reglements ON reglements.IDmode=modes_reglements.IDmode
        LEFT JOIN emetteurs ON reglements.IDemetteur=emetteurs.IDemetteur
        LEFT JOIN payeurs ON reglements.IDpayeur=payeurs.IDpayeur
        LEFT JOIN depots ON reglements.IDdepot=depots.IDdepot
        LEFT JOIN comptes_bancaires ON comptes_bancaires.IDcompte=reglements.IDcompte
        LEFT JOIN comptes_payeurs ON comptes_payeurs.IDcompte_payeur = reglements.IDcompte_payeur
        LEFT JOIN familles ON familles.IDfamille = comptes_payeurs.IDfamille
        WHERE reglements.IDdepot IS NULL OR reglements.IDdepot=%d
        GROUP BY reglements.IDreglement
        ORDER BY reglements.date;
        """ % IDdepot
        db.ExecuterReq(req,MsgBox="DLG_Saisie_depot")
        listeDonnees = db.ResultatReq()
        db.Close()
        
        listeListeView = []
        for item in listeDonnees :
            track = Track(item)
            listeListeView.append(track)
        return listeListeView

    def Importation(self):
        """ Importation des données """
        DB = GestionDB.DB()
        req = """SELECT IDdepot, date, nom, verrouillage, IDcompte, observations, code_compta
        FROM depots 
        WHERE IDdepot=%d;""" % self.IDdepot
        DB.ExecuterReq(req,MsgBox="DLG_Saisie_depot")
        listeDonnees = DB.ResultatReq()
        DB.Close()
        if len(listeDonnees) == 0 : return
        IDdepot, date, nom, verrouillage, IDcompte, observations, code_compta = listeDonnees[0]

        # Date
        self.ctrl_date.SetDate(date)
        # Nom
        self.ctrl_nom.SetValue(nom)
        # Verrouillage
        if verrouillage == 1 :
            self.ctrl_verrouillage.SetValue(True)
        # Compte
        if IDcompte != None :
            self.ctrl_compte.SetID(IDcompte)
        # Observations
        if observations != None :
            self.ctrl_observations.SetValue(observations)
        # Code compta
        if code_compta != None :
            self.ctrl_code_compta.SetValue(code_compta)

    def OnBoutonAjouter(self, event): 
        # Vérifier si compte sélectionné
        IDcompte = self.ctrl_compte.GetID()
        IDmode = None
        if self.IDdepot == None:
            IDmode = self.ctrl_nom.GetID()
        if IDcompte == 0 or IDcompte == None : 
            dlg = wx.MessageDialog(self, _("Vous devez obligatoirement sélectionner un compte bancaire !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            self.ctrl_compte.SetFocus()
            return False
        date = self.ctrl_date.GetDate()
        # Vérifier le dépot contient des règlements transférés en compta
        haltela = False
        for track in self.tracks:
            if track.compta:
                haltela = True
        if haltela :
            dlg = wx.MessageDialog(self, _("Un règlement transféré en compta bloque la modif du dépôt !\n"
                                           "Regardez la dernière colonne du tableau"), _("Impossible"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return False

        # Ouverture DLG Sélection réglements
        dlg = DLG_Saisie_depot_ajouter.Dialog(self, tracks=self.tracks,
                                              IDcompte=IDcompte,
                                              IDmode=IDmode,
                                              date=date)
        if dlg.ShowModal() == wx.ID_OK:
            modemodif = dlg.ctrl_mode.GetID()
            if "----" in self.ctrl_nom.GetValue():
                try:
                    self.ctrl_nom.SetID(modemodif)
                except: pass
            self.tracks = dlg.GetTracks()
            self.ctrl_reglements.MAJ(self.tracks)
            self.MAJinfos()
            self.saisie = True
        dlg.Destroy() 
        
    def OnCheckVerrouillage(self, event):
        if self.ctrl_verrouillage.GetValue() == True :
            self.bouton_ajouter.Enable(False)
        else:
            self.bouton_ajouter.Enable(True)

    def OnBoutonAide(self, event): 
        from Utils import UTILS_Aide
        UTILS_Aide.Aide("Gestiondesdpts")

    def OnBoutonAnnuler(self, event):
        if self.saisie:
            dlg = wx.MessageDialog(self, _("Souhaitez-vous vraiment annuler ?\n\nLes éventuelles modifications effectuées seront perdues..."), _("Annulation"), wx.YES_NO|wx.YES_DEFAULT|wx.CANCEL|wx.ICON_QUESTION)
            reponse = dlg.ShowModal()
            dlg.Destroy()
            if reponse != wx.ID_YES :
                return
        self.EndModal(wx.ID_CANCEL)

    def OnBoutonOk(self, event):
        if self.Sauvegardes():
            # Fermeture
            self.EndModal(wx.ID_OK)

    def OnBoutonNouveau(self,event):
        if self.Sauvegardes():
            self.IDdepot = None
            self.Init()
            nom = self.ctrl_nom.GetValue()
            try:
                IDmode = self.ctrl_nom.GetID()
            except:
                IDmode = None
            if IDmode:
                self.ctrl_nom.SetID(IDmode)
            elif nom in self.ctrl_nom.listeNoms:
                ix = self.ctrl_nom.listeNoms.index(nom)
                self.ctrl_nom.SetID(ix)
            self.Layout()

    def Sauvegardes(self):
        # Sauvegarde des paramètres
        etat = self.Sauvegarde_depot()
        if etat == False :
            return False
        # Sauvegarde des règlements
        self.Sauvegarde_reglements()
        return True

    def Sauvegarde_depot(self):
        # Nombre de lignes
        if len(self.ctrl_reglements.modelObjects) == 0:
            if self.IDdepot == None:
                dlg = wx.MessageDialog(self,
                                   "Aucun règlement dans ce dépôt, Abandonnez ou Ajoutez-en",
                                   "Erreur de saisie", wx.OK | wx.ICON_EXCLAMATION)
            else:
                dlg = wx.MessageDialog(self,
                                   "Aucune ligne! Si le dépôt éxistait préalablement, Abandonnez puis supprimez-le à partir de la liste des dépôts",
                                   "Erreur de saisie", wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            self.ctrl_nom.SetFocus()
            return False

        # Date
        date = self.ctrl_date.GetDate()
        if date == None :
            dlg = wx.MessageDialog(self, _("Etes-vous sûr de ne pas vouloir saisir de date de dépôt ?"), _("Confirmation"), wx.YES_NO|wx.NO_DEFAULT|wx.CANCEL|wx.ICON_INFORMATION)
            reponse = dlg.ShowModal()
            dlg.Destroy()
            if reponse !=  wx.ID_YES :
                return False
        
        # Verrouillage
        verrouillage = self.ctrl_verrouillage.GetValue()
        if verrouillage == True :
            verrouillage = 1
        else:
            verrouillage = 0
        
        # Compte
        IDcompte = self.ctrl_compte.GetID()
        if IDcompte == 0 : 
            IDcompte = None
            dlg = wx.MessageDialog(self, _("Etes-vous sûr de ne pas vouloir sélectionner de compte bancaire pour ce dépôt ?"), _("Confirmation"), wx.YES_NO|wx.NO_DEFAULT|wx.CANCEL|wx.ICON_INFORMATION)
            reponse = dlg.ShowModal()
            dlg.Destroy()
            if reponse !=  wx.ID_YES :
                return False
        
        # Observations
        observations = self.ctrl_observations.GetValue()
        
        # Code compta
        code_compta = self.ctrl_code_compta.GetValue() 
        
        DB = GestionDB.DB()
        listeDonnees = [    
                ("nom", self.nom),
                ("date", date),
                ("verrouillage", verrouillage),
                ("IDcompte", IDcompte),
                ("observations", observations),
                ("code_compta", code_compta),
            ]
        if self.IDdepot == None :
            self.IDdepot = DB.ReqInsert("depots", listeDonnees)
        else:
            DB.ReqMAJ("depots", listeDonnees, "IDdepot", self.IDdepot)
        DB.Close()
        
        return True
        
    def Sauvegarde_reglements(self):
        DB = GestionDB.DB()
        for track in self.tracks :
            # Ajout
            if track.IDdepot == None and track.inclus == True :
                DB.ReqMAJ("reglements", [("IDdepot", self.IDdepot),], "IDreglement", track.IDreglement)
            # Retrait
            if track.IDdepot != None and track.inclus == False :
                DB.ReqMAJ("reglements", [("IDdepot", None),], "IDreglement", track.IDreglement)
        DB.Close()

    def GetIDdepot(self):
        return self.IDdepot
    
    def MAJinfos(self):
        """ Créé le texte infos avec les stats du dépôt """
        # Récupération des chiffres
        nbreTotal = 0
        montantTotal = 0.0
        dictDetails = {}
        for track in self.tracks :
            if track.inclus == True :
                # Montant total
                nbreTotal += 1
                # Nbre total
                montantTotal += track.montant
                # Détail
                if (track.IDmode in dictDetails) == False :
                    dictDetails[track.IDmode] = { "label" : track.nom_mode, "nbre" : 0, "montant" : 0.0}
                dictDetails[track.IDmode]["nbre"] += 1
                dictDetails[track.IDmode]["montant"] += track.montant
        # Création du texte
        self.nom = ""
        texte = _("<B>%d règlements (%.2f %s) : </B>") % (nbreTotal, montantTotal, SYMBOLE)
        for IDmode, dictDetail in dictDetails.items() :
            texteDetail = "%d %s (%.2f %s), " % (dictDetail["nbre"], dictDetail["label"], dictDetail["montant"], SYMBOLE)
            texte += texteDetail
            abrege = dictDetail["label"].split(" ")[0]
            self.nom += "%s "%abrege[:10]
        if len(dictDetails) > 0 :
            texte = texte[:-2] + "."
        else:
            texte = texte[:-7] + "</B>"
        self.ctrl_infos.SetLabel(texte)
        # Label de staticbox
        self.staticbox_reglements_staticbox.SetLabel(self.ctrl_reglements.GetLabelListe(_("règlements")))
    
    def OnBoutonImprimer(self, event):
        # Création du menu contextuel
        menuPop = wx.Menu()

        # Item Apercu avant impression
        item = wx.MenuItem(menuPop, 20, _("Aperçu avant impression"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Apercu.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.Apercu, id=20)

        # Item Imprimer
        item = wx.MenuItem(menuPop, 30, _("Imprimer"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Imprimante.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.Imprimer, id=30)

        self.PopupMenu(menuPop)
        menuPop.Destroy()

    def Apercu(self, event):
        self.ctrl_reglements.Apercu(None)

    def Imprimer(self, event):
        self.ctrl_reglements.Imprimer(None)

    def GetLabelParametres(self):
        listeParametres = []

        nom = self.ctrl_nom.GetValue()
        listeParametres.append(_("Nom du dépôt : %s") % nom)
        
        date = self.ctrl_date.GetDate() 
        if date == None : 
            date = _("Non spécifiée")
        else :
            date = DateEngFr(str(date))
        listeParametres.append(_("Date : %s") % date)

        IDcompte = self.ctrl_compte.GetID() 
        if IDcompte != 0 and IDcompte != None :
            nomCompte = self.ctrl_compte.GetStringSelection()
            numCompte = self.ctrl_compte.GetNumero()
        else:
            nomCompte = ""
            numCompte = ""
        listeParametres.append(_("Compte : %s %s") % (nomCompte, numCompte))

        if self.ctrl_verrouillage.GetValue() == True :
            listeParametres.append(_("Dépôt verrouillé"))
        else :
            listeParametres.append(_("Dépôt déverrouillé"))
        
        labelParametres = " | ".join(listeParametres)
        return labelParametres
    
    def GetNbreAvisDepots(self):
        nbreAbonnes = 0
        for track in self.tracks :
            if track.email_depots != None and track.inclus == True and track.avis_depot == None :
                nbreAbonnes += 1
        return nbreAbonnes

    def OnBoutonAvisDepots(self, event=None):
        self.EnvoyerAvisDepots() 
    
    def EnvoyerAvisDepots(self):
        """ Envoi des avis de dépôt par Email aux familles """                        
        # Recherche des adresses des individus
        DB = GestionDB.DB()
        req = """SELECT individus.IDindividu, mail, travail_mail
        FROM individus;"""
        DB.ExecuterReq(req,MsgBox="DLG_Saisie_depot")
        listeAdressesIndividus = DB.ResultatReq()
        DB.Close() 
        dictAdressesIndividus = {}
        for IDindividu, mail, travail_mail in listeAdressesIndividus :
            dictAdressesIndividus[IDindividu] = {"perso" : mail, "travail" : travail_mail}
        
        # Recherche des titulaires
        dictTitulaires = UTILS_Titulaires.GetTitulaires() 
        
        # Recherche les familles abonnées à ce service
        listeDonnees = []
        for track in self.tracks :
            if (not(track.email_depots in (None, ""))) and track.inclus == True :
                
                # Recherche de l'adresse d'envoi
                IDindividu, categorie, adresse = track.email_depots.split(";")
                if IDindividu != "" :
                    try :
                        if int(IDindividu) in dictAdressesIndividus :
                            adresse = dictAdressesIndividus[int(IDindividu)][categorie]
                    except :
                        adresse = ""
                
                # Nom de correspondant de la famille
                nomTitulaires = dictTitulaires[track.IDfamille]["titulairesSansCivilite"]
                
                # Champs sur le règlement
                dictChamps = {
                    "{ID_REGLEMENT}" : str(track.IDreglement),
                    "{DATE_REGLEMENT}" : DateEngFr(str(track.date)),
                    "{MODE_REGLEMENT}" : track.nom_mode,
                    "{NOM_EMETTEUR}" : track.nom_emetteur,
                    "{NUM_PIECE}" : track.numero_piece,
                    "{MONTANT_REGLEMENT}" : "%.2f %s" % (track.montant, SYMBOLE),
                    "{NOM_PAYEUR}" : track.nom_payeur,
                    "{NUM_QUITTANCIER}" : track.numero_quittancier,
                    "{DATE_SAISIE}" : DateEngFr(str(track.date_saisie)),
                    }
                
                listeDonnees.append({"nomTitulaires": nomTitulaires, "IDreglement" : track.IDreglement, "avis_depot" : track.avis_depot, "IDfamille" : track.IDfamille, "adresse" : adresse, "pieces" : [], "champs" : dictChamps})
        
        from Dlg import DLG_Selection_avis_depots
        dlg = DLG_Selection_avis_depots.Dialog(self, listeDonnees=listeDonnees)
        reponse = dlg.ShowModal()
        listeSelections = dlg.GetListeSelections() 
        dlg.Destroy()
        if reponse != wx.ID_OK :
            return
        
        listeDonnees2 = []
        for index in listeSelections :
            listeDonnees2.append(listeDonnees[index])
        
        # Chargement du Mailer
        from Dlg import DLG_Mailer
        dlg = DLG_Mailer.Dialog(self, categorie="reglement")
        dlg.SetDonnees(listeDonnees2, modificationAutorisee=True)
        dlg.ChargerModeleDefaut()
        dlg.ShowModal()
        listeSucces = dlg.listeSucces
        dlg.Destroy()
        
        # Mémorisation des avis envoyés avec succès
        DB = GestionDB.DB()
        listeIDreglements = []
        for track in listeSucces :
            IDreglement = int(track.champs["{ID_REGLEMENT}"])
            listeIDreglements.append(IDreglement)
            DB.ReqMAJ("reglements", [("avis_depot", str(datetime.date.today()) ),], "IDreglement", IDreglement)
        DB.Close()
        
        for track in self.tracks :
            if track.IDreglement in listeIDreglements :
                track.avis_depot = datetime.date.today()
                self.ctrl_reglements.RefreshObject(track)

if __name__ == "__main__":
    app = wx.App(0)
    #wx.InitAllImageHandlers()
    #dialog_1 = Dialog(None, IDdepot=3357)
    dialog_1 = Dialog(None, IDdepot=None)
    app.SetTopWindow(dialog_1)
    dialog_1.ShowModal()
    app.MainLoop()