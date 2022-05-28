#!/usr/bin/env python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------
# Application :    Noethys, Matthania remanié avec détail des règlements
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS, JB 04/2020
# Copyright:       (c) 2010-12 Ivan LUCAS, JB
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------


from Utils.UTILS_Traduction import _
from Utils import UTILS_Dates as ut
import Chemins
import wx
from Ctrl import CTRL_Bouton_image
import copy
import datetime
import wx.lib.colourselect as csel

import GestionDB
from Ctrl import CTRL_Bandeau
from Ol import OL_Releve_prestations
import FonctionsPerso
from Utils import UTILS_Titulaires
from Utils import UTILS_Envoi_email
from Utils import UTILS_Organisateur
from Utils import UTILS_Config
from Utils import UTILS_Impression_tableau

SYMBOLE = UTILS_Config.GetParametre("monnaie_symbole", "€")

COULEUR_FOND_TITRE = (0.8, 0.8, 1)

LISTE_MOIS = (_("Janvier"), _("Février"), _("Mars"), _("Avril"), _("Mai"), _("Juin"), _("Juillet"), _("Août"), _("Septembre"), _("Octobre"), _("Novembre"), _("Décembre"))

def Nz(valeur):
    try:
        u = float(valeur)
    except:
        u = 0.0
    return u

def DateEngFr(textDate):
    if textDate == None: return ""
    textDate = str(textDate)
    text = str(textDate)[8:10] + "/" + str(textDate)[5:7] + "/" + str(textDate)[:4]
    return text

def DateComplete(dateDD):
    """ Transforme une date DD en date complète : Ex : lundi 15 janvier 2008 """
    listeJours = (_("Lundi"), _("Mardi"), _("Mercredi"), _("Jeudi"), _("Vendredi"), _("Samedi"), _("Dimanche"))
    listeMois = (_("janvier"), _("février"), _("mars"), _("avril"), _("mai"), _("juin"), _("juillet"), _("août"), _("septembre"), _("octobre"), _("novembre"), _("décembre"))
    dateComplete = listeJours[dateDD.weekday()] + " " + str(dateDD.day) + " " + listeMois[dateDD.month-1] + " " + str(dateDD.year)
    return dateComplete

def DateEngEnDateDD(dateEng):
    if dateEng == None or dateEng == "" : return None
    dateEng = str(dateEng)
    return datetime.date(int(dateEng[:4]), int(dateEng[5:7]), int(dateEng[8:10]))

def FormateMontant(montant,lgmini = 7,tab="_",ent=False):
    if montant == None : txt = ""
    elif float(montant) == 0.0 : txt =  ""
    elif montant == "" : txt = ""
    elif ent :  txt = "%.0f" % (float(montant))
    else :  txt = "%.2f" % (float(montant))
    if  len(txt) < lgmini:
        txt = tab * lgmini + txt
        txt = txt[-lgmini:]
    return txt

def ConvertCouleurPDFpourWX(couleurpdf=(0, 0, 0)):
    return (couleurpdf[0]*255.0, couleurpdf[1]*255.0, couleurpdf[2]*255.0)

class Dialog(wx.Dialog):
    def __init__(self, parent, IDfamille=None):
        wx.Dialog.__init__(self, parent, -1, name="DLG_Emetteurs", style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX)
        self.parent = parent
        self.IDfamille = IDfamille
        
        # Bandeau
        intro = _("Vous pouvez éditer ici un état des prestations ou de la situation comptable pour la ou les périodes souhaitées.")
        titre = _("Edition d'un relevé des prestations")
        self.SetTitle(titre)
        self.ctrl_bandeau = CTRL_Bandeau.Bandeau(self, titre=titre, texte=intro, hauteurHtml=30, nomImage="Images/32x32/Euro.png")
                
        # Périodes
        self.staticbox_periodes_staticbox = wx.StaticBox(self, -1, _("Périodes"))
        self.ctrl_periodes = OL_Releve_prestations.ListView(self, id=-1, IDfamille=self.IDfamille,
                                                            style=wx.LC_REPORT|wx.SUNKEN_BORDER|wx.LC_SINGLE_SEL|wx.LC_HRULES|wx.LC_VRULES)
        self.bouton_ajouter = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Ajouter.png"), wx.BITMAP_TYPE_ANY))
        self.bouton_modifier = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Modifier.png"), wx.BITMAP_TYPE_ANY))
        self.bouton_supprimer = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Supprimer.png"), wx.BITMAP_TYPE_ANY))

        # Options
        self.staticbox_options_staticbox = wx.StaticBox(self, -1, _("Options"))
        self.check_memoriser_parametres = wx.CheckBox(self, -1, _("Mémoriser les périodes"))
        self.check_memoriser_parametres.SetValue(True) 
        
        self.checkbox_couleur = wx.CheckBox(self, -1, _("Couleur de fond de titre :"))
        self.ctrl_couleur = csel.ColourSelect(self, -1, "", COULEUR_FOND_TITRE, size=(60, 18))
        
        # Boutons
        self.bouton_aide = CTRL_Bouton_image.CTRL(self, texte=_("Aide"), cheminImage=Chemins.GetStaticPath("Images/32x32/Aide.png"))
        self.bouton_email = CTRL_Bouton_image.CTRL(self, texte=_("Envoyer par Email"), cheminImage=Chemins.GetStaticPath("Images/32x32/Emails_exp.png"))
        self.bouton_ok = CTRL_Bouton_image.CTRL(self, texte=_("Aperçu"), cheminImage=Chemins.GetStaticPath("Images/32x32/Apercu.png"))
        self.bouton_annuler = CTRL_Bouton_image.CTRL(self, texte=_("Fermer"), cheminImage=Chemins.GetStaticPath("Images/32x32/Fermer.png"))

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_CHECKBOX, self.OnCheckCouleur, self.checkbox_couleur)
        self.Bind(wx.EVT_BUTTON, self.OnAjouter, self.bouton_ajouter)
        self.Bind(wx.EVT_BUTTON, self.OnModifier, self.bouton_modifier)
        self.Bind(wx.EVT_BUTTON, self.OnSupprimer, self.bouton_supprimer)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAide, self.bouton_aide)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonEmail, self.bouton_email)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonOk, self.bouton_ok)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAnnuler, self.bouton_annuler)
        self.Bind(wx.EVT_CLOSE, self.OnBoutonAnnuler)
        
        # Init contrôles
        couleur = UTILS_Config.GetParametre("releve_prestations_couleur", defaut=ConvertCouleurPDFpourWX(COULEUR_FOND_TITRE))
        if couleur == False :
            couleur = ConvertCouleurPDFpourWX(COULEUR_FOND_TITRE)
        else :
            self.checkbox_couleur.SetValue(True)
        self.ctrl_couleur.SetColour(couleur)

        listePeriodes = UTILS_Config.GetParametre("releve_prestations_periodes", defaut=[])
        self.ctrl_periodes.MAJ(listePeriodes)

    def __set_properties(self):
        self.bouton_ajouter.SetToolTip(_("Cliquez ici pour ajouter une période"))
        self.bouton_modifier.SetToolTip(_("Cliquez ici pour modifier la période sélectionnée dans la liste"))
        self.bouton_supprimer.SetToolTip(_("Cliquez ici pour supprimer la période sélectionnée dans la liste"))
        self.checkbox_couleur.SetToolTip(_("Cochez cette case pour insérer une couleur"))
        self.check_memoriser_parametres.SetToolTip(_("Cochez cette case pour mémoriser les périodes"))
        self.bouton_aide.SetToolTip(_("Cliquez ici pour obtenir de l'aide"))
        self.bouton_email.SetToolTip(_("Cliquez ici pour envoyer ce document par Email"))
        self.bouton_ok.SetToolTip(_("Cliquez ici pour créer un aperçu du document PDF"))
        self.bouton_annuler.SetToolTip(_("Cliquez ici pour annuler"))
        self.SetMinSize((850, 400))

    def __do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(rows=4, cols=1, vgap=10, hgap=10)
        grid_sizer_base.Add(self.ctrl_bandeau, 0, wx.EXPAND, 0)
        
        # Périodes
        staticbox_periodes = wx.StaticBoxSizer(self.staticbox_periodes_staticbox, wx.VERTICAL)
        grid_sizer_periodes = wx.FlexGridSizer(rows=1, cols=2, vgap=5, hgap=5)
        grid_sizer_boutons_periodes = wx.FlexGridSizer(rows=4, cols=1, vgap=5, hgap=5)
        grid_sizer_periodes.Add(self.ctrl_periodes, 1, wx.EXPAND, 0)
        grid_sizer_boutons_periodes.Add(self.bouton_ajouter, 0, 0, 0)
        grid_sizer_boutons_periodes.Add(self.bouton_modifier, 0, 0, 0)
        grid_sizer_boutons_periodes.Add(self.bouton_supprimer, 0, 0, 0)
        grid_sizer_periodes.Add(grid_sizer_boutons_periodes, 1, wx.EXPAND, 0)
        grid_sizer_periodes.AddGrowableRow(0)
        grid_sizer_periodes.AddGrowableCol(0)
        staticbox_periodes.Add(grid_sizer_periodes, 1, wx.ALL|wx.EXPAND, 10)
        grid_sizer_base.Add(staticbox_periodes, 1, wx.LEFT|wx.RIGHT|wx.EXPAND, 10)
        
        # Options
        staticbox_options = wx.StaticBoxSizer(self.staticbox_options_staticbox, wx.VERTICAL)
        grid_sizer_options = wx.FlexGridSizer(rows=1, cols=6, vgap=2, hgap=2)
        grid_sizer_options.Add(self.check_memoriser_parametres, 0, wx.EXPAND, 0)
        grid_sizer_options.Add( (20, 10), 0, wx.EXPAND, 0)
        grid_sizer_options.Add(self.checkbox_couleur, 0, wx.EXPAND, 0)
        grid_sizer_options.Add(self.ctrl_couleur, 0, wx.EXPAND, 0)
        staticbox_options.Add(grid_sizer_options, 1, wx.ALL|wx.EXPAND, 10)
        grid_sizer_base.Add(staticbox_options, 1, wx.LEFT|wx.RIGHT|wx.EXPAND, 10)
        
        # Boutons
        grid_sizer_boutons = wx.FlexGridSizer(rows=1, cols=5, vgap=10, hgap=10)
        grid_sizer_boutons.Add(self.bouton_aide, 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_email, 0, 0, 0)
        grid_sizer_boutons.Add((20, 20), 0, wx.EXPAND, 0)
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

    def OnCheckCouleur(self, event): 
        if self.checkbox_couleur.GetValue() == True :
            self.ctrl_couleur.Enable(True)
        else:
            self.ctrl_couleur.Enable(False)

    def OnAjouter(self, event): 
        self.ctrl_periodes.Ajouter(None)

    def OnModifier(self, event): 
        self.ctrl_periodes.Modifier(None)

    def OnSupprimer(self, event): 
        self.ctrl_periodes.Supprimer(None)

    def OnBoutonAide(self, event): 
        from Utils import UTILS_Aide
        UTILS_Aide.Aide("Editerunrelevdesprestations")
    
    def OnBoutonOk(self, event): 
        self.CreationPDF()
    
    def CreationPDF(self, nomDoc="Releve_prestations.pdf", afficherDoc=True):
        if not "\\" in nomDoc:
            from Utils import UTILS_Fichiers
            nomDoc = UTILS_Fichiers.GetRepTemp(nomDoc)

        dictOptionsImpression = {}
        
        # Création PDF
        listePeriodes = self.ctrl_periodes.GetListePeriodes()
        if len(listePeriodes) == 0 :
            dlg = wx.MessageDialog(self, "Vous devez paramétrer au moins une période dans la liste !",
                                   "Erreur de saisie", wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return False
        
        # Récupère couleur fond de titre
        if self.checkbox_couleur.GetValue() == True :
            dictOptionsImpression["couleur"] = self.ctrl_couleur.GetColour()
        else :
            dictOptionsImpression["couleur"] = False
        
        # Composition de données
        composition = Composition(IDfamille=self.IDfamille, listePeriodes=listePeriodes,)
        lstTableaux, dictChampsFusion = composition.GetDonnees()

        # Impression et récup des champs pour le mail
        impression = UTILS_Impression_tableau.Impression(dictOptionsImpression)
        ret = impression.CompositionPDF(lstTableaux, nomDoc, afficherDoc) 
        return dictChampsFusion

    def OnBoutonAnnuler(self, event): 
        self.MemoriserParametres() 
        self.EndModal(wx.ID_CANCEL)
        
    def MemoriserParametres(self):
        # Couleur
        if self.checkbox_couleur.GetValue() == True :
            couleur = self.ctrl_couleur.GetColour()
        else :
            couleur = False
        UTILS_Config.SetParametre("releve_prestations_couleur", couleur)        
        # Périodes
        if self.check_memoriser_parametres.GetValue() == True :
            listePeriodes = self.ctrl_periodes.GetListePeriodes() 
            UTILS_Config.SetParametre("releve_prestations_periodes", listePeriodes)
        
    def OnBoutonEmail(self, event): 
        """ Envoi par mail """
        from Utils import UTILS_Fichiers
        nomDoc = UTILS_Fichiers.GetRepTemp("RELEVE%s.pdf" % FonctionsPerso.GenerationIDdoc())
        UTILS_Envoi_email.EnvoiEmailFamille(parent=self, IDfamille=self.IDfamille, nomDoc=nomDoc, categorie="releve_prestations")

class Composition():
    def __init__(self, IDfamille=None, listePeriodes=[],) :
        self.IDfamille = IDfamille
        self.listePeriodes = listePeriodes
        self.DB = GestionDB.DB()
        if IDfamille != None :
            # Récupération des données dans la base
            self.dictTitulaires = self.GetTitulaires()
            self.IDcompte_payeur = self.dictTitulaires[self.IDfamille]["IDcompte_payeur"]

        # largeurContenu = 520 ou 730 selon l'oritentation
        self.largeursLeft = [60, 290, 280]
        self.largeursRight = [50, 50, 60]
        self.largeurContenu = sum(self.largeursLeft) + sum(self.largeursRight)

    def GetTitulaires(self):
        dictNomsTitulaires = UTILS_Titulaires.GetTitulaires([self.IDfamille,]) 
        return dictNomsTitulaires

    def ClePeriode(self,dateEng,regroupement,periode):
        # Calcul de la clé de la ligne du tableau, key=None
        dat = DateEngEnDateDD(dateEng)
        datdeb = DateEngEnDateDD(periode[0])
        if dateEng > periode[1]:
            # Période post, filtrée pour prestations mais pas  pour les règlements ventilés
            key = None
        else:
            annee = dat.year
            mois = dat.month
            if not regroupement or regroupement == "date" :
                if dateEng < periode[0]:
                    key = datdeb + datetime.timedelta(days=-1)
                else:
                    key = dat
            elif regroupement == "mois" :
                if dateEng < periode[0]:
                    mois = (datdeb + datetime.timedelta(days=-28)).month
                    annee = (datdeb + datetime.timedelta(days=-28)).year
                key = (annee, mois)
            elif regroupement == "annee" :
                if dateEng < periode[0]: annee = (datdeb + datetime.timedelta(days=-365)).year
                key = annee
        return key

    def GetPrestations(self,periode,regroupement, encompta):
        # Recherche des prestations de la famille, et constitution d'un dictionnaire les regroupant ansi que ventilations
        dateDebut,dateFin = periode
        where = "WHERE prestations.IDfamille=%d AND prestations.date <= '%s'" % (self.IDfamille, dateFin)
        if encompta:
            where += " AND prestations.compta IS NOT NULL"

        req = """
        SELECT prestations.IDprestation, prestations.IDcompte_payeur, prestations.date, categorie, 
        label, prestations.montant, 
        prestations.IDactivite, activites.nom, activites.abrege,
        prestations.IDtarif, noms_tarifs.nom, categories_tarifs.nom, IDfacture, 
        prestations.IDindividu, prestations.IDfamille
        FROM prestations
        LEFT JOIN activites ON prestations.IDactivite = activites.IDactivite
        LEFT JOIN tarifs ON prestations.IDtarif = tarifs.IDtarif
        LEFT JOIN noms_tarifs ON tarifs.IDnom_tarif = noms_tarifs.IDnom_tarif
        LEFT JOIN categories_tarifs ON tarifs.IDcategorie_tarif = categories_tarifs.IDcategorie_tarif
        %s        
        ORDER BY prestations.date, prestations.IDindividu, prestations.label
        ;""" % (where)
        self.DB.ExecuterReq(req,MsgBox="ExecuterReq")
        listePrestationsTemp = self.DB.ResultatReq()
        dictVentilationPrestations = {}

        # Recherche de la ventilation des prestations de la famille
        if encompta:
            where = """WHERE prestations.IDfamille=%d 
                            AND prestations.date <= '%s' 
                            AND reglements.date <= '%s' 
                            AND prestations.compta IS NOT NULL
                            AND reglements.compta IS NOT NULL"""%(self.IDfamille,dateFin,dateFin)
        else:
            where = "WHERE prestations.IDfamille=%d AND prestations.date <= '%s' AND reglements.date <= '%s'"\
                    % (self.IDfamille,dateFin,dateFin)
        req = """
        SELECT ventilation.IDprestation, ventilation.IDventilation, Sum(ventilation.montant)
        FROM (ventilation 
        LEFT JOIN prestations ON ventilation.IDprestation = prestations.IDprestation) 
        LEFT JOIN reglements ON ventilation.IDreglement = reglements.IDreglement
        %s
        GROUP BY ventilation.IDprestation, ventilation.IDventilation
        ORDER BY prestations.Date, reglements.Date
        ;""" % (where)
        self.DB.ExecuterReq(req,MsgBox="ExecuterReq")
        listeVentilationPrestations = self.DB.ResultatReq()
        # Composition d'un dictionnaire tempo des ventilations
        for IDprestation,IDventilation, montant_ventilation in listeVentilationPrestations :
            if IDprestation in dictVentilationPrestations :
                dictVentilationPrestations[IDprestation]["mttVentil"] += montant_ventilation
                dictVentilationPrestations[IDprestation]["ventilations"].append(IDventilation)
            else:
                dictVentilationPrestations[IDprestation]={"mttVentil":montant_ventilation}
                dictVentilationPrestations[IDprestation]["ventilations"]=[IDventilation,]

        dictPrestations = {}
        # Constitution du dictionnaire prestations, à retourner
        for IDprestation, IDcompte_payeur, date, categorie, label, montant, IDactivite, nomActivite, abregeActivite, \
            IDtarif, nomTarif, nomCategorieTarif, IDfacture, IDindividu, IDfamille in listePrestationsTemp :

            key = self.ClePeriode(date,regroupement,periode)
            if key not in dictPrestations:
                dictPrestations[key] = {}
            if IDprestation in dictVentilationPrestations :
                mttVentil = dictVentilationPrestations[IDprestation]["mttVentil"]
                ventilations = dictVentilationPrestations[IDprestation]["ventilations"]
            else :
                mttVentil = 0.0
                ventilations = []
            reglee = (abs(montant - mttVentil) < 0.01)
            dictPrestations[key][IDprestation] = {
                        "IDprestation" : IDprestation,
                        "IDcompte_payeur" : IDcompte_payeur,
                        "date" : DateEngEnDateDD(date),
                        "categorie" : categorie,
                        "label" : label,
                        "montant_prestation" : montant,
                        "IDactivite" : IDactivite,
                        "nomActivite" : nomActivite,
                        "abregeActivite" : abregeActivite,
                        "IDtarif" : IDtarif,
                        "nomTarif" : nomTarif,
                        "nomCategorieTarif" : nomCategorieTarif,
                        "IDfacture" : IDfacture,
                        "IDindividu" : IDindividu,
                        "IDfamille" : IDfamille,
                        "montant_ventile" : mttVentil,
                        "ventilations": ventilations,
                        "reglee": reglee
                        }
        for key, ligne in list(dictPrestations.items()):
            du = 0.0
            regle = 0.0
            ventilations = []
            pieces=[]
            for IDprestation, dict in list(ligne.items()):
                du += dict["montant_prestation"]
                regle += dict["montant_ventile"]
                ventilations += dict["ventilations"]
                pieces.append(IDprestation)
            ligne["du"] = du
            ligne["regle"] = regle
            ligne["ventilations"] = ventilations

        return dictPrestations

    def GetReglements(self,periode,regroupement,cleventil,encompta):
        # Récupération des règlements sur un IDcomptePayeur, pour consituer un dictReglements[clé,IDprestation,IDreglement
        dateDebut,dateFin = periode
        where = "WHERE reglements.IDcompte_payeur = %d AND reglements.date <= '%s' " % (self.IDfamille, dateFin)
        if encompta: where += "AND reglements.compta IS NOT NULL """

        req = """
            SELECT  reglements.IDreglement,reglements.Date, reglements.date_differe, modes_reglements.label, reglements.numero_piece,
                    emetteurs.nom, payeurs.nom, ventilation.montant, reglements.montant, ventilation.IDventilation, matPieces.pieNature,
                    matPieces.pieNoFacture, prestations.date, matPieces.pieDateFacturation
            FROM (((((reglements
            LEFT JOIN ventilation ON reglements.IDreglement = ventilation.IDreglement)
            LEFT JOIN emetteurs ON reglements.IDemetteur = emetteurs.IDemetteur)
            LEFT JOIN modes_reglements ON reglements.IDmode = modes_reglements.IDmode)
            LEFT JOIN payeurs ON reglements.IDpayeur = payeurs.IDpayeur)
            LEFT JOIN matPieces ON ventilation.IDprestation = matPieces.pieIDprestation)
            LEFT JOIN prestations ON ventilation.IDprestation = prestations.IDprestation
            %s
            ORDER BY reglements.Date
            ;""" % where

        retour = self.DB.ExecuterReq(req,MsgBox="ExecuterReq")
        if retour != "ok" :
            GestionDB.MessageBox(None,retour)
        recordset = self.DB.ResultatReq()

        #pour chaque ventilation on crée un dictVentil stocké en dictVentilations
        dictCleRegl= {}
        dictIDregl = {}
        listeChamps = ["IDreglement","date_reglement", None, "mode", "numero", "emetteur", "payeur", None, "montant",
                       None, "nature", "noFacture",None,None]
        for IDreglement, date_reglement, date_differe, mode, noCheque, emetteur, payeur, ventile, surMontant,\
                    IDventilation, nature, noFacture, date_prestation, date_facture in recordset :
            if not ventile:
                ventile = 0.0
            if date_prestation > dateFin:
                ventile = 0.0
                IDventilation = None
            #if date_differe != None:
            #   date_reglement = date_differe
            date = DateEngEnDateDD(date_reglement)
            record = (IDreglement, date, date_differe, mode, noCheque, emetteur, payeur, ventile, surMontant, IDventilation,
                      nature, noFacture, date_prestation, date_facture )
            cleAN = False

            # le dictIDreglement, permet de reconstituer les non ventilations a posteriori
            if not IDreglement in list(dictIDregl.keys()):
                dictIDregl[IDreglement] = {"date_reglement":date_reglement,"montant":surMontant, "ventile":0.0,"cleAN":None}
            dictIDregl[IDreglement]["ventile"] += ventile

            # détermination de la ligne cible
            if date_prestation and date_prestation <= dateFin and cleventil:
                # les parties de règlement rejoignent les lignes des prestations qu'ils règlent
                key = self.ClePeriode(date_prestation,regroupement,periode)
                if date_prestation < dateDebut:
                    cleAN = True
            else:
                # si pas de ventilation dans la période le règlement conserve sa date pour la clé
                key = self.ClePeriode(date_reglement,regroupement,periode)
                if date_reglement < dateDebut:
                    cleAN = True
            if key:
                if key not in dictCleRegl:
                    dictCleRegl[key] = {}
                if IDreglement not in dictCleRegl[key]:
                    dictCleRegl[key][IDreglement] = {"montant_ventile":0.0,"ltventilations":[]}
                i = 0
                dict = dictCleRegl[key][IDreglement]
                dict["ltventilations"].append((IDventilation,ventile))
                dict["montant_ventile"] += ventile
                dict["cleAN"] = cleAN
                for item in record :
                    if listeChamps[i] != None :
                        dict[listeChamps[i]] = item
                    i += 1

        # reprise des règlements incomplètement ventilés pour leur part non ventilés

        for IDreglement, date_reglement, date_differe, mode, noCheque, emetteur, payeur, ventile, surMontant, \
            IDventilation, nature, noFacture, date_prestation, date_facture in recordset:
            if date_prestation > dateFin:
                ventile = 0.0
                IDventilation = None
            date = DateEngEnDateDD(date_reglement)
            record = (IDreglement, date, date_differe, mode, noCheque, emetteur, payeur, ventile, surMontant, IDventilation,
                      nature, noFacture, date_prestation, date_facture )
            dict = dictIDregl[IDreglement]
            if dict["montant"] == dict["ventile"]:
                continue
            if not ventile: ventile = 0.0

            # Composition d'un item de ligne.reglements
            key = self.ClePeriode(date_reglement,regroupement,periode)
            if date_reglement < dateDebut:
                cleAN = True
            else: cleAN = False
            if key:
                # l'IDreglement en négatif dans la ligne pointe la part non ventilée d'un règlement
                if key not in dictCleRegl:
                    dictCleRegl[key] = {}
                if -IDreglement not in dictCleRegl[key]:
                    dictCleRegl[key][-IDreglement] = {"montant_ventile":0.0,"ltventilations":[]}
                    dict = dictCleRegl[key][-IDreglement]
                    i = 0
                    for item in record:
                        if listeChamps[i] != None:
                            dict[listeChamps[i]] = item
                        i += 1
                else: dict = dictCleRegl[key][-IDreglement]

                dict["montant_ventile"] += ventile
                dict["cleAN"] = cleAN
                #if ventile == 0:
                    # ce réglement n'ayant aucun lien avec une prestation ne doit pas générer une ligne à zéro
                 #   del dictCleRegl[key][IDreglement]
        return dictCleRegl
        #fin GetReglements

    def GetDonnees(self):
        # Elaboration d'une liste de tableaux en format requis par UTILS_Impression_tableau et un dict pour mails
        lstTableaux = []
        dictChampsFusion = {}

        # Création du titre du document
        dataTableau = []
        dictTableau={}
        dateDuJour = DateEngFr(str(datetime.date.today()))
        dictChampsFusion["{DATE_EDITION_RELEVE}"] = dateDuJour

        titreDocument = ("Relevé de compte %s"%(UTILS_Organisateur.GetNom()), "titre")
        texteTitulaire = ("%d - %s"%(self.IDfamille, self.dictTitulaires[self.IDfamille]["titulairesSansCivilite"]), "titre")
        editeLe = (("<align='right'>Edité le %s") % (dateDuJour), "editele")
        dataTableau.append([[titreDocument,texteTitulaire], editeLe])

        dictTableau["dataLignes"] = dataTableau
        dictTableau["largeursCol"] =  [self.largeurContenu-200, 200]
        dictTableau["gridStyle"] = "tete"
        lstTableaux.append(copy.deepcopy(dictTableau))


        #déroulé des différentes périodes demandées, pour faire un tableau par période
        for periode in self.listePeriodes :
            if periode["selection"] == False :
                continue

            # Création des périodes
            globalTotalReste = 0.0
            dictPrestationsAffichees = {}

            # Récupération des paramètres de la période
            typeDonnees = periode["type"]
            dictPeriode = periode["periode"]
            dictOptions = periode["options"]
            ventil = dictOptions["ventil"]
            date_debut = dictPeriode["date_debut"]
            date_fin = dictPeriode["date_fin"]

            # toutes les prestations si flag encompta False
            encompta = False
            if typeDonnees == "factures":
                encompta = True
            if not typeDonnees in  ("prestations","factures"): continue

            # Impayés
            if "impayes" in dictOptions and dictOptions["impayes"] == True :
                impayesSeuls = True
            else: impayesSeuls = False
            periode = (ut.DateDDEnDateEng(date_debut), ut.DateDDEnDateEng(date_fin))

            # Initialisation des variables 'regroupement'
            regroupement = None
            labelRegroupement = "Date"
            if "regroupement" in dictOptions and dictOptions["regroupement"] != None :
                regroupement = dictOptions["regroupement"]
                labelRegroupement = ""

            # ---------------- Appel des données de base, regroupées par clé de regroupement ---------------------------
            self.dictPrestations = self.GetPrestations(periode, regroupement, encompta)

            # Appel des règlements détaillés par ventilation sur prestations, ou sur leur propre clé si non ventilés ---
            self.dictReglements = self.GetReglements(periode,regroupement,ventil, encompta)

            clesLignes = [x for x,y in list(self.dictPrestations.items())]

            # Récup des clés de règlements sans prestations sur la ligne
            for cle in list(self.dictReglements.keys()):
                if not cle in clesLignes:
                    clesLignes.append(cle)

            # Dessin du tableau de titre pour cette période
            dataTableau = []
            compl = ""
            if encompta:
                compl = "en compta"
            if impayesSeuls:
                optPrest = "Prestations impayées"
            else: optPrest = "Toutes prestations"
            if ventil:
                optVentil = "règlements ventilés, %s"%compl
            else: optVentil = "règlements NON ventilés, %s"%compl
            labelTitre = "%s, %s - %s"% (optPrest,optVentil,dictPeriode["label"])
            dataTableau.append([labelTitre,])

            dictTableau["dataLignes"] = dataTableau
            dictTableau["largeursCol"] = ([self.largeurContenu,])
            dictTableau["gridStyle"] = "hautdecorps"
            lstTableaux.append(copy.deepcopy(dictTableau))

            # Dessin du tableau pour les LIGNES et initialisations
            dataTableau = []

            if encompta :
                lblPrest = "Factures en compta"
            else:
                lblPrest = "Prestations commandées"
            if ventil :
                lblReste =  "Reste par Prestation"
                lblRegl = "Ventilation des règlements par date de prestation"
            else:
                lblReste = "Reste %s Cumulé"%SYMBOLE
                lblRegl = "Règlements perçus"
            dataTableau.append([labelRegroupement, lblPrest, lblRegl,"%s. %s"%(lblPrest[:4],SYMBOLE), "Réglé %s"%SYMBOLE,lblReste])

            dictTableau["dataLignes"] = dataTableau
            dictTableau["largeursCol"] = self.largeursLeft + self.largeursRight
            dictTableau["gridStyle"] = "hautdecorps"
            lstTableaux.append(copy.deepcopy(dictTableau))

            # Dessin du tableau pour les LIGNES et initialisations
            dataTableau = []

            tableauTotalDu, tableauTotalRegle, tableauTotalReste = 0.0, 0.0, 0.0
            clesLignes.sort()
            dictPrestationAN = {
                "IDprestation" : 0,
                "date" : date_debut + datetime.timedelta(days=-1),
                "label" : "Report antérieur",
                "montant_prestation" : 0.0,
                "montant_ventile" : 0.00,
                "montant_regle" : 0.00,
                }

            # Infos pour les règlements à supprimer
            lstVentilsIgnorees = []
            if impayesSeuls:
                for cle in clesLignes:
                    if cle in list(self.dictPrestations.keys()):
                        dictPrestations = self.dictPrestations[cle]
                        for IDprestation, prestation in list(dictPrestations.items()):
                            if not isinstance(IDprestation,int) :
                                continue
                            if prestation["reglee"]:
                                lstVentilsIgnorees += prestation["ventilations"]

            # -------- Boucle sur chaque clé  pouvant représenter une ligne --------------------------------------------
            for cle in clesLignes:
                listePrest = []
                listeRegl = []

                # appel des règlements de la ligne
                if not cle in list(self.dictReglements.keys()): self.dictReglements[cle] = {}

                # Gestion pour règlements non affectés
                dictReglNegatifs = {}
                for IDregl, reglement in list(self.dictReglements[cle].items()):
                    if ventil:
                        if reglement["cleAN"]:
                            continue
                        # gestion des règlements non associés à une prestation
                        if IDregl < 0:
                            # création d'une ligne de prestation virtuelle
                            dicttmp ={"IDprestation" : 0,
                                    "label" : "non affecté",
                                    "montant_prestation" : 0.0,
                                    "montant_ventile" : reglement["montant"]-reglement["montant_ventile"],}
                            listePrest.append(dicttmp)
                    else:
                        # si non ventil : regroupement des règlements sans aucune affectation (ID négatifs)
                        if IDregl < 0:
                            dictReglNegatifs[-IDregl] = reglement

                # si non ventil : regroupement des règlements sans aucune affectation (ID négatifs)
                if not ventil:
                    for IDregl,reglement in  list(dictReglNegatifs.items()):
                        if not IDregl in list(self.dictReglements[cle].keys()):
                            self.dictReglements[cle][IDregl] = reglement
                        del self.dictReglements[cle][-IDregl]

                # appel des prestations de la ligne
                if cle in list(self.dictPrestations.keys()):
                    dictPrestations = self.dictPrestations[cle]
                else:
                    dictPrestations = {}

                # ------------------ Composition de la liste des prestations à afficher --------------------------------
                for IDprestation, prestation in list(dictPrestations.items()):
                    # on ignore les totaux ajoutés par des clés str
                    if isinstance(IDprestation,str):
                        continue
                    # On oublie les soldés si non ne veut que les impayés
                    if impayesSeuls and prestation["reglee"]:
                        continue
                    # cas des antérieurs regroupés et perte du libellé détaillé
                    if prestation["date"] < date_debut :
                        if ventil:
                            dictPrestationAN["montant_prestation"] += (prestation["montant_prestation"]-prestation["montant_ventile"])
                        else:
                            dictPrestationAN["montant_prestation"] += (prestation["montant_prestation"])

                        # l'IDprestation sert de flag pour un seul dictPresatationAN dans la liste
                        if dictPrestationAN['IDprestation']==0:
                            dictPrestationAN['IDprestation'] += 1
                            listePrest.append(dictPrestationAN)

                    # la prestation est dans la période à détailler
                    else :
                        listePrest.append(prestation)

                # -------------------- Composition de la liste des règlements à afficher -------------------------------
                for IDregl, reglement in list(self.dictReglements[cle].items()):

                    # réduction du règlement si la ventilation correspondante est d'une prestation réglée non affichée
                    if impayesSeuls:
                        # pour les ventilations des prestations réglées
                        for IDventilation, ventile in reglement["ltventilations"]:
                            if IDventilation in lstVentilsIgnorees:
                                if ventil:
                                    reglement["montant_ventile"] -= ventile
                                else:
                                    reglement["montant"] -= ventile
                                    reglement["montant_ventile"] -= ventile

                    # Ignorer les lignes de règlements à valeur nulle
                    if ventil and impayesSeuls:
                        if IDregl >= 0 and abs(reglement["montant_ventile"]) <0.01:
                            continue
                        if IDregl < 0 and abs(reglement["montant"] - reglement["montant_ventile"]) <0.01:
                            continue
                    elif not ventil and impayesSeuls:
                        if abs(reglement["montant"]) <0.01:
                            continue

                    # cas des antérieurs regroupés sur ligne unique à écarter
                    if reglement["cleAN"]:
                        if ventil and IDregl < 0:
                            # règlements non ventilés caractérisés par IDregl négatif, diminuent le report antérieur
                            dictPrestationAN["montant_ventile"] += (reglement["montant"] - reglement["montant_ventile"])
                        # les prestations ventilées portent en elles leur règlement, mais pas les non ventilées
                        if not ventil:
                            dictPrestationAN["montant_prestation"] -= (reglement["montant"])
                        continue

                    # vérifie qu'il n'y a pas d'anomalie
                    if IDregl < 0 and (reglement["montant"]-reglement["montant_ventile"]) == 0.0:
                        wx.MessageBox("Pb avec le règlement %s, ID négatif: part non affectée et totalement ventilé!"%IDregl)
                        continue

                    # Composition du texte du règlement
                    if ventil:
                        texte = DateEngFr(reglement["date_reglement"]) + " "
                        if IDregl < 0:
                            # part non ventilée d'un règlement
                            texte += FormateMontant(reglement["montant"]-reglement["montant_ventile"],lgmini=4,ent=True) + " /" + \
                                     FormateMontant(reglement["montant"],lgmini=4,ent=True) + SYMBOLE + " "
                        else:
                            texte += FormateMontant(reglement["montant_ventile"],lgmini=4,ent=True) + " /" + \
                                     FormateMontant(reglement["montant"],lgmini=4,ent=True) + SYMBOLE + " "
                    else:
                        texte =  reglement["mode"][:3].lower()+" "+FormateMontant(reglement["montant"],lgmini=4,tab=".",ent=True)\
                                  + SYMBOLE + " "

                    for champ in ["mode", "numero", "emetteur", "payeur"]:
                        if reglement[champ] != None:
                            texte += reglement[champ] + " "
                    reglement["texte"] = texte

                    # ajoute dans la liste des règlements à afficher
                    listeRegl.append(reglement)

                #corps de la ligne (paragraphe), cle (de la ligne) est la période retenue
                cledeb = self.ClePeriode(periode[0],regroupement,periode)
                if cle < cledeb and regroupement: labelAvant = "jusqu'à"
                else: labelAvant = ""
                if type(cle) == datetime.date : labelKey = "%s %s"% (labelAvant , DateEngFr(str(cle)))
                if type(cle) == tuple : labelKey = "%s %s %d" % (labelAvant,LISTE_MOIS[cle[1]-1], cle[0])
                if type(cle) == int : labelKey = "%s Année %d"% (labelAvant, cle)

                # initialisation des composants de la ligne du tableau et soustotaux
                listePrestations, listeReglements = [],[]
                listeTotalDu, listeTotalRegle, listeTotalReste = [],[],[]
                ligneTotalDu, ligneTotalRegle, ligneTotalReste = 0.0, 0.0, 0.0

                # Composition de la ligne du tableau
                ligneNonVide = False
                montant, montant_regle = 0.0, 0.0

                # déroule les lignes prestations du paragraphe
                for dictPrestation in listePrest :
                    # Calcul des montants
                    montant = dictPrestation["montant_prestation"]
                    # Constitution de la liste des règlements du paragraphe et sous totaux
                    montant_regle = dictPrestation["montant_ventile"]

                    if montant != 0.00 or montant_regle!= 0.00 :
                        # Label de la prestation
                        if ventil:
                            labelPrestation = dictPrestation["label"]
                        else:
                            labelPrestation = FormateMontant(dictPrestation["montant_prestation"],lgmini=4,tab=".",ent=True) + "€ " +dictPrestation["label"]

                        listePrestations.append((labelPrestation[:53], "texte"))

                        # Total dû
                        listeTotalDu.append((montant, "nombre"))
                        ligneTotalDu += montant
                        ligneTotalReste += montant
                        if ventil:
                            # Réglé
                            listeTotalRegle.append((montant_regle, "nombre"))
                            ligneTotalRegle += montant_regle

                            # Reste dû
                            listeTotalReste.append((montant - montant_regle, "nombre"))
                            ligneTotalReste -= montant_regle

                        IDprestation = dictPrestation["IDprestation"]
                        if IDprestation not in dictPrestationsAffichees:
                            dictPrestationsAffichees[IDprestation] = 0
                        # comptage des vrais prestations affichées
                        if IDprestation >0:
                            dictPrestationsAffichees[IDprestation] += 1
                        if impayesSeuls:
                            if montant != montant_regle:
                                ligneNonVide = True
                        else:
                            ligneNonVide = True

                # ajustement des règlements de la ligne label et totaux ligne
                ligneReglements = 0.0
                for dictReglement in listeRegl:
                    if not ventil:
                        # sans ventilation les colonnes réglé et reste_dû sont groupées par ligne
                        montant_regle = dictReglement["montant"]

                        # Réglé
                        ligneTotalRegle += montant_regle

                        # Reste dû (les prestations ont déjà été ajoutées, mais pas leur réglements si non ventil)
                        ligneTotalReste -= montant_regle
                    else:
                        # avec  ventilation vérification des ventiles
                        ligneReglements += dictReglement["montant_ventile"]

                    # colonne Reglements
                    texteReglement = dictReglement["texte"]
                    if 'cleAN' in dictReglement:
                        if dictReglement["cleAN"]:
                            texteReglement = ""
                    listeReglements.append((texteReglement[:53], "texte"))
                    ligneNonVide = True

                if ventil and listePrestations == []:
                    if ligneTotalRegle != ligneReglements:
                        correctif = ligneReglements - ligneTotalRegle
                        listeTotalRegle.append(correctif)
                        listeTotalReste.append(-correctif)
                        ligneTotalRegle += correctif
                        ligneTotalReste -= correctif

                # totalisation
                tableauTotalDu += ligneTotalDu
                tableauTotalRegle += ligneTotalRegle
                tableauTotalReste += ligneTotalReste
                globalTotalReste += ligneTotalReste

                # Ecriture de la ligne
                if ligneNonVide :
                    texteKey = (labelKey, "texte")
                    # Selon type de ligne Total ou non
                    if not regroupement:
                        if ventil:
                            dataTableau.append([texteKey, listePrestations, listeReglements, listeTotalDu, listeTotalRegle, listeTotalReste])
                        else: dataTableau.append([texteKey, listePrestations, listeReglements, ligneTotalDu, ligneTotalRegle, tableauTotalReste])

                    else :
                        dataTableau.append([
                                None,
                                texteKey,
                                None,
                                (ligneTotalDu, "nombre"),
                                (ligneTotalRegle, "nombre"),
                                (ligneTotalReste, "nombre"),
                                ])

            #fin de la ligne : for cle in cleLignes   (déroulé des paragraphes)

            if len(dataTableau) > 0 :
                # Création du tableau de la période
                dictTableau["dataLignes"] = dataTableau
                dictTableau["largeursCol"] = self.largeursLeft + self.largeursRight
                dictTableau["gridStyle"] = "corps"
                lstTableaux.append(copy.deepcopy(dictTableau))

                # Insertion du total par période
                dataTableau = []
                listeLigne = [
                    ("Totaux :", "total"),
                    (tableauTotalDu, "nombre"),
                    (tableauTotalRegle, "nombre"),
                    (tableauTotalReste, "nombre"),
                    ]
                dataTableau.append(listeLigne)

                # Création du tableau de pied de période
                dictTableau["dataLignes"] = dataTableau
                dictTableau["largeursCol"] = [sum(self.largeursLeft),] + self.largeursRight
                dictTableau["gridStyle"] = "pied"
                lstTableaux.append(copy.deepcopy(dictTableau))


        # ---------------------------- Insertion du total du document --------------------------------------------------
        dataTableau = []
        if globalTotalReste < 0.0 :
            texte = "<align='right'><b>Reste en votre faveur :</b>"
            montant = -globalTotalReste
        else :
            texte = "<align='right'><b>Total dû :</b>"
            montant = globalTotalReste
        listeLigne = (
            (texte, "total"),
            ("<b>%s %s</b>" %(UTILS_Impression_tableau.FormateMontant(montant),SYMBOLE), "total"),)

        dataTableau.append(listeLigne)
        
        dictChampsFusion["{RESTE_DU}"] = "%.02f %s" % (globalTotalReste, SYMBOLE)

        # Création du tableau pied de formulaire
        dictTableau["dataLignes"] = dataTableau
        dictTableau["largeursCol"] = [sum(self.largeursLeft), sum(self.largeursRight)]
        dictTableau["gridStyle"] = "pied"
        lstTableaux.append(copy.deepcopy(dictTableau))

        # Renvoie les données pour impression et les champs pour fusion Email
        return lstTableaux, dictChampsFusion

if __name__ == "__main__":
    app = wx.App(0)
    #wx.InitAllImageHandlers()
    
    dialog_1 = Dialog(None, IDfamille= 2676)
    app.SetTopWindow(dialog_1)
    dialog_1.ShowModal()
    app.MainLoop()
