#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Matthania déroute vers DLG_Saisie_reglement, et ajout colonne ventilation
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS, JB, Jacques Brunel
# Copyright:       (c) 2010-11 Ivan LUCAS, JB
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------


import Chemins
from Utils.UTILS_Traduction import _
import wx
import datetime
import decimal
import GestionDB
from Utils import UTILS_Historique
from Utils import UTILS_Utilisateurs
from Utils import UTILS_Identification
from Dlg import DLG_Saisie_reglement
from Utils import UTILS_Config
SYMBOLE = UTILS_Config.GetParametre("monnaie_symbole", "€")

from Ctrl.CTRL_ObjectListView import FastObjectListView, ColumnDefn, Filter, CTRL_Outils, PanelAvecFooter

from Utils.UTILS_Decimal import FloatToDecimal as FloatToDecimal


def DateEngFr(textDate):
    if textDate == None:
        return " "
    text = str(textDate[8:10]) + "/" + str(textDate[5:7]) + "/" + str(textDate[:4])
    return text

def DateComplete(dateDD):
    """ Transforme une date DD en date complète : Ex : Lun 15 janv 2008 """
    listeJours = ("Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim")
    listeMois = ("janv", "fév", "mars", "avr", "mai", "juin", "juil", "août", "sept", "oct", "nov", "déc")
    dateComplete = listeJours[dateDD.weekday()] + " " + str(dateDD.day) + " " + listeMois[dateDD.month-1] + " " + str(dateDD.year)
    return dateComplete

def DateEngEnDateDD(dateEng):
    if not dateEng:
        return
    if dateEng and not isinstance(dateEng,str): dateEng = str(dateEng)
    return datetime.date(int(dateEng[:4]), int(dateEng[5:7]), int(dateEng[8:10]))

class Track(object):
    def __init__(self, donnees):
        self.IDreglement = donnees[0]
        self.compte_payeur = donnees[1]
        self.IDcompte_payeur = self.compte_payeur
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
        self.date_differe = DateEngEnDateDD(donnees[15])
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
        self.montant_ventilation = FloatToDecimal(0.0)
        self.inclus = True
        self.IDprelevement = donnees[24]
        self.nbreVentilation = 0
        self.compta = donnees[26]
        self.resteAVentiler = self.montant
        self.utilisateur = donnees[28]
        #fin Track
    
class ListView(FastObjectListView):
    def __init__(self, *args, **kwds):
        # Récupération des paramètres perso
        self.IDcompte_payeur = kwds.pop("IDcompte_payeur", None)
        self.IDdepot = kwds.pop("IDdepot", None)
        self.mode = kwds.pop("mode", "famille")
        self.selectionID = None
        self.selectionTrack = None
        self.criteres = ""
        self.itemSelected = False
        self.popupIndex = -1
        self.listeFiltres = []
        self.numColonneTri = 1
        self.ordreAscendant = True
        # Initialisation du listCtrl
        FastObjectListView.__init__(self, *args, **kwds)
        # Binds perso
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnItemActivated)
        self.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)
    
    def SetIDcompte_payeur(self, IDcompte_payeur=None):
        self.IDcompte_payeur = IDcompte_payeur
        
    def OnItemActivated(self,event):
        self.Modifier(None)
                
    def InitModel(self):
        self.donnees = self.GetTracks()

    def GetTracks(self):
        """ Récupération des données """
        listeID = None
        if self.mode == "depot" :
            if self.IDdepot == None :
                criteres = "WHERE reglements.IDdepot IS NULL"
            else:
                criteres = "WHERE reglements.IDdepot=%d" % self.IDdepot
        elif self.mode == "liste" :
            criteres = ""
        elif self.IDcompte_payeur == None:
            return []
        else:
            criteres = "WHERE reglements.IDcompte_payeur=%d" % self.IDcompte_payeur
            
        # Filtres
        if len(self.listeFiltres) > 0 :
            filtreStr = " AND ".join(self.listeFiltres)
            if criteres == "" :
                criteres = "WHERE " + filtreStr
            else :
                criteres = criteres + " AND " + filtreStr
                
            
        db = GestionDB.DB()
        req = """
        SELECT reglements.IDreglement, reglements.IDcompte_payeur, reglements.Date, reglements.IDmode, 
                modes_reglements.label, reglements.IDemetteur, emetteurs.nom, reglements.numero_piece, 
                reglements.montant, payeurs.IDpayeur, payeurs.nom, reglements.observations, 
                reglements.numero_quittancier, reglements.IDprestation_frais, reglements.IDcompte, 
                reglements.date_differe, reglements.encaissement_attente, reglements.IDdepot, depots.Date, depots.nom, 
                depots.verrouillage, reglements.date_saisie, reglements.IDutilisateur, 
                SUM(ventilation.montant), reglements.IDprelevement, 
                COUNT(ventilation.montant),reglements.compta, 
                factures.numero,utilisateurs.prenom
        FROM (((((((reglements 
                LEFT JOIN ventilation ON reglements.IDreglement = ventilation.IDreglement) 
                LEFT JOIN modes_reglements ON reglements.IDmode = modes_reglements.IDmode) 
                LEFT JOIN emetteurs ON reglements.IDemetteur = emetteurs.IDemetteur) 
                LEFT JOIN payeurs ON reglements.IDpayeur = payeurs.IDpayeur) 
                LEFT JOIN depots ON reglements.IDdepot = depots.IDdepot) 
                LEFT JOIN prestations ON ventilation.IDprestation = prestations.IDprestation) 
                LEFT JOIN factures ON prestations.IDfacture = factures.IDfacture)
                LEFT JOIN utilisateurs on reglements.IDutilisateur = utilisateurs.IDutilisateur
        %s
        GROUP BY reglements.IDreglement, reglements.IDcompte_payeur, reglements.Date, reglements.IDmode, 
                modes_reglements.label, reglements.IDemetteur, emetteurs.nom, reglements.numero_piece, 
                reglements.montant, payeurs.IDpayeur, payeurs.nom, reglements.observations, 
                reglements.numero_quittancier, reglements.IDprestation_frais, reglements.IDcompte, 
                reglements.date_differe, reglements.encaissement_attente, reglements.IDdepot, 
                depots.Date, depots.nom, depots.verrouillage, reglements.date_saisie, reglements.IDutilisateur, 
                reglements.IDprelevement, reglements.compta, factures.numero, utilisateurs.prenom
        ORDER BY reglements.IDreglement
        ;""" % criteres
        db.ExecuterReq(req,MsgBox="OL_Reglements")
        listeDonnees = db.ResultatReq()
        db.Close()
        
        listeListeView = []

        track = None
        def finReglement(track,lstNumero):
            ventilation = ""
            for item in lstNumeros:
                ventilation += str(item) + ', '
            if len(ventilation)>2: ventilation = ventilation[:-2]
            track.ventilation = ventilation + " ( " + str(track.nbreVentilation)+" lignes)"
            listeListeView.append(track)

        IDreglement = 0
        for item in listeDonnees :
            # nouveau numero
            if item[0] != IDreglement:
                if IDreglement != 0:
                    #  fin du règlement précédent
                    finReglement(track,lstNumeros)
                track = Track(item)
                lstNumeros = []
                IDreglement = item[0]
            # même règlement à incrémenter
            else:
                numero = str(item[-1])
                if not numero in lstNumeros:
                    lstNumeros.append(numero)

            if item[23]:
                track.resteAVentiler -= item[23]
            track.nbreVentilation += item[25]
            if self.selectionID == item[0] :
                self.selectionTrack = track
        # fin du balayage des reglements
        if track:
            finReglement(track,lstNumeros)
        db.Close()
        return listeListeView
            
    def InitObjectListView(self):            
        # Couleur en alternance des lignes
        self.oddRowsBackColor = "#F0FBED" 
        self.evenRowsBackColor = wx.Colour(255, 255, 255)
        self.useExpansionColumn = True
        
        # Image list
        self.imgVert = self.AddNamedImages("ok", wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Ventilation_vert.png"), wx.BITMAP_TYPE_PNG))
        self.imgRouge = self.AddNamedImages("erreur", wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Ventilation_rouge.png"), wx.BITMAP_TYPE_PNG))
        self.imgOrange = self.AddNamedImages("addition", wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Ventilation_orange.png"), wx.BITMAP_TYPE_PNG))
        
        self.imgAttente = self.AddNamedImages("attente", wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Attente.png"), wx.BITMAP_TYPE_PNG))
        self.imgOk = self.AddNamedImages("ok", wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Ok.png"), wx.BITMAP_TYPE_PNG))
        self.imgNon = self.AddNamedImages("erreur", wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Interdit.png"), wx.BITMAP_TYPE_PNG))
        
        def GetImageVentilation(track):
            if track.montant < FloatToDecimal(0.0) :
                return None
            if track.montant_ventilation == None :
                return self.imgRouge
            if track.resteAVentiler == FloatToDecimal(0.0) :
                return self.imgVert
            if track.resteAVentiler > FloatToDecimal(0.0) :
                return self.imgOrange
            if track.resteAVentiler < FloatToDecimal(0.0) :
                return self.imgRouge
        
        def GetImageDepot(track):
            if track.IDdepot == None :
                if track.encaissement_attente == 1 :
                    return self.imgAttente
                else:
                    return self.imgNon
            else:
                return self.imgOk

        def FormateDateCourt(dateDD):
            if dateDD == None :
                return ""
            else:
                return DateEngFr(str(dateDD))

        def FormateMontant(montant):
            if montant == None : return ""
            return "%.2f %s" % (montant, SYMBOLE)

        liste_Colonnes = [
            ColumnDefn(_("ID"), "left", 0, "IDreglement", typeDonnee="entier"),
            ColumnDefn(_("Date"), 'left', 110, "date", typeDonnee="date",
                       stringConverter=DateComplete),
            ColumnDefn(_("Differé"), 'left', 110, "date_differe", typeDonnee="date",
                       stringConverter=DateComplete),
            ColumnDefn(_("Mode"), 'left', 120, "nom_mode", typeDonnee="texte"),
            ColumnDefn(_("Emetteur"), 'left', 80, "nom_emetteur", typeDonnee="texte"),
            ColumnDefn(_("Numéro"), 'left', 60, "numero_piece", typeDonnee="texte"),
            ColumnDefn(_("Payeur"), 'left', 130, "nom_payeur", typeDonnee="texte"),
            ColumnDefn(_("Montant"), 'right', 60, "montant", typeDonnee="montant", stringConverter=FormateMontant),
            #ColumnDefn(_(u"Ventilé"), 'right', 80, "montant_ventilation", typeDonnee="montant", stringConverter=FormateMontant, imageGetter=GetImageVentilation),
            ColumnDefn(_("A Ventiler"), 'right', 80, "resteAVentiler", typeDonnee="montant", stringConverter=FormateMontant, imageGetter=GetImageVentilation),
            ColumnDefn(_("Dépôt"), 'left', 90, "date_depot", typeDonnee="date", stringConverter=FormateDateCourt, imageGetter=GetImageDepot),
            ColumnDefn(_("IDDépôt"), "left", 40, "IDdepot", typeDonnee="entier"),
            ColumnDefn(_("VentilFactures no "), 'left', 110, "ventilation", typeDonnee="texte"),
            ColumnDefn(_("compta"), "left", 70, "compta", typeDonnee="entier"),
            ColumnDefn(_("user"), 'left', 70, "utilisateur", typeDonnee="texte"),
            ]
        
        self.SetColumns(liste_Colonnes)
        self.SetEmptyListMsg(_("Aucun règlement"))
        self.SetEmptyListMsgFont(wx.FFont(11, wx.DEFAULT, faceName="Tekton"))
##        self.SetSortColumn(self.columns[1])
        self.SortBy(self.numColonneTri, ascending=self.ordreAscendant)
        self.SetObjects(self.donnees)
       
    def MAJ(self, ID=None):
        if ID != None :
            self.selectionID = ID
            self.selectionTrack = None
        else:
            self.selectionID = None
            self.selectionTrack = None
        self.InitModel()
        self.InitObjectListView()
        # Sélection d'un item
        if self.selectionTrack != None :
            self.SelectObject(self.selectionTrack, deselectOthers=True, ensureVisible=True)
        self.selectionID = None
        self.selectionTrack = None
        if ID == None :
            self.DefileDernier() 

    def Selection(self):
        return self.GetSelectedObjects()

    def OnContextMenu(self, event):
        """Ouverture du menu contextuel """
        if len(self.Selection()) == 0:
            noSelection = True
        else:
            noSelection = False
            ID = self.Selection()[0].IDreglement
                
        # Création du menu contextuel
        menuPop = wx.Menu()

        if self.mode != "liste" :

            # Item Ajouter
            item = wx.MenuItem(menuPop, 10, _("Ajouter"))
            item.SetBitmap(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Ajouter.png"), wx.BITMAP_TYPE_PNG))
            menuPop.Append(item)
            self.Bind(wx.EVT_MENU, self.Ajouter, id=10)

        # Item Modifier
        item = wx.MenuItem(menuPop, 20, _("Modifier"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Modifier.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.Modifier, id=20)
        if noSelection == True : item.Enable(False)
        
        # Item Supprimer
        item = wx.MenuItem(menuPop, 30, _("Supprimer"))
        item.SetBitmap(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Supprimer.png"), wx.BITMAP_TYPE_PNG))
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.Supprimer, id=30)
        if noSelection == True : item.Enable(False)
        
        menuPop.AppendSeparator()

        # Item Ventilation Automatique
        sousMenuVentilation = wx.Menu()
        
        item = wx.MenuItem(sousMenuVentilation, 201, _("Uniquement le règlement sélectionné"))
        item.SetBitmap(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Magique.png"), wx.BITMAP_TYPE_PNG))
        sousMenuVentilation.Append(item)
        self.Bind(wx.EVT_MENU, self.VentilationAuto, id=201)
        if noSelection == True : item.Enable(False)

        item = wx.MenuItem(sousMenuVentilation, 202, "Tous les règlements")
        item.SetBitmap(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Magique.png"),
                                 wx.BITMAP_TYPE_PNG))
        sousMenuVentilation.Append(item)
        self.Bind(wx.EVT_MENU, self.VentilationAuto, id=202)

        menuPop.AppendSubMenu(sousMenuVentilation, "Ventilation automatique")
        
        menuPop.AppendSeparator()
        
        # Item Editer RECU
        item = wx.MenuItem(menuPop, 60, _("Editer un reçu (PDF)"))
        item.SetBitmap(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Apercu.png"), wx.BITMAP_TYPE_PNG))
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.EditerRecu, id=60)
        if noSelection == True : item.Enable(False)
        
        menuPop.AppendSeparator()
    
        # Génération automatique des fonctions standards
        self.GenerationContextMenu(menuPop, dictParametres=self.GetParametresImpression())

        self.PopupMenu(menuPop)
        menuPop.Destroy()

    def GetParametresImpression(self):
        intro = ""
        total = 0.0
        for track in self.donnees :
            total += track.montant
        total = self.GetDetailReglements()

        dictParametres = {
            "titre" : _("Liste des règlements"),
            "intro" : intro,
            "total" : total,
            "orientation" : wx.LANDSCAPE,
            }
        return dictParametres

    def EditerRecu(self, event):
        if len(self.Selection()) == 0 :
            dlg = wx.MessageDialog(self, _("Vous n'avez sélectionné aucun règlement dans la liste !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        IDreglement = self.Selection()[0].IDreglement
        from Dlg import DLG_Impression_recu
        dlg = DLG_Impression_recu.Dialog(self, IDreglement=IDreglement) 
        dlg.ShowModal()
        dlg.Destroy()

    def GetDetailReglements(self):
        # Récupération des chiffres
        nbreTotal = 0
        montantTotal = 0.0
        dictDetails = {}
        for track in self.donnees :
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
        texte = _("%d règlements (%.2f €) : ") % (nbreTotal, montantTotal)
        for IDmode, dictDetail in dictDetails.items() :
            texteDetail = "%d %s (%.2f €), " % (dictDetail["nbre"], dictDetail["label"], dictDetail["montant"])
            texte += texteDetail
        if len(dictDetails) > 0 :
            texte = texte[:-2] + "."
        else:
            texte = texte[:-7] 
        return texte

    def Impression(self, mode="preview"):
        if self.donnees == None or len(self.donnees) == 0 :
            dlg = wx.MessageDialog(self, _("Il n'y a aucune donnée à imprimer !"), _("Erreur"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        txtIntro = ""
        total = 0.0
        for track in self.donnees :
            total += track.montant
        txtTotal = self.GetDetailReglements()
        from Utils import UTILS_Printer
        prt = UTILS_Printer.ObjectListViewPrinter(self, titre=_("Liste des règlements"), intro=txtIntro, total=txtTotal, format="A", orientation=wx.LANDSCAPE)
        if mode == "preview" :
            prt.Preview()
        else:
            prt.Print()

    def Apercu(self, event):
        self.Impression("preview")

    def Imprimer(self, event):
        self.Impression("print")

    def ExportTexte(self, event):
        from Utils import UTILS_Export
        UTILS_Export.ExportTexte(self, titre=_("Liste des règlements"))

    def ExportExcel(self, event):
        from Utils import UTILS_Export
        UTILS_Export.ExportExcel(self, titre=_("Liste des règlements"))

    def Ajouter(self, event):
        if self.IDcompte_payeur != None and UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("familles_reglements", "creer") == False : return
        dlg = DLG_Saisie_reglement.Dialog(self, IDcompte_payeur=self.IDcompte_payeur, IDreglement=None)
        if dlg.ShowModal() == wx.ID_OK:
            IDreglement = dlg.GetIDreglement()
            self.MAJ(IDreglement)
        dlg.Destroy()

    def ReglerFacture(self, IDfacture=None):
        dlg = DLG_Saisie_reglement.Dialog(self, IDcompte_payeur=self.IDcompte_payeur, IDreglement=None)
        dlg.SelectionneFacture(IDfacture)
        if dlg.ShowModal() == wx.ID_OK:
            IDreglement = dlg.GetIDreglement()
            self.MAJ(IDreglement)
        dlg.Destroy()

    def Modifier(self, event):
        if self.IDcompte_payeur != None and UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("familles_reglements", "modifier") == False : return
        
        if len(self.Selection()) == 0 :
            dlg = wx.MessageDialog(self, _("Vous n'avez sélectionné aucun règlement à modifier dans la liste !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        IDreglement = self.Selection()[0].IDreglement

        # Avertissement si appartient à un prélèvement
        if self.Selection()[0].IDprelevement != None :
            dlg = wx.MessageDialog(self, _("Ce règlement est rattaché à un prélèvement automatique.\n\nSouhaitez-vous vraiment le modifier ?"), _("Avertissement"), wx.YES_NO|wx.NO_DEFAULT|wx.CANCEL|wx.ICON_EXCLAMATION)
            reponse = dlg.ShowModal() 
            dlg.Destroy()
            if reponse != wx.ID_YES :
                return

        dlg = DLG_Saisie_reglement.Dialog(self, IDcompte_payeur=self.IDcompte_payeur, IDreglement=IDreglement)
        if dlg.ShowModal() == wx.ID_OK:
            self.MAJ(IDreglement)
        dlg.Destroy()
        self.MAJ(IDreglement)

    def Supprimer(self, event):
        if self.IDcompte_payeur != None and UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("familles_reglements", "supprimer") == False : return
        
        if len(self.Selection()) == 0 :
            dlg = wx.MessageDialog(self, _("Vous n'avez sélectionné aucun règlement à supprimer dans la liste"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        IDreglement = self.Selection()[0].IDreglement
        IDdepot = self.Selection()[0].IDdepot
        montant = self.Selection()[0].montant
        compta = self.Selection()[0].compta
        # Si transféré en compta: annulation
        if compta != None :
            dlg = wx.MessageDialog(self, _("Ce règlement est déjà transféré en compta. Vous ne pouvez donc pas le supprimer !"), _("Règlement en compta"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return

        # Si appartient à un dépot : annulation
        if IDdepot != None and montant != 0:
            dlg = wx.MessageDialog(self, _("Ce règlement est déjà attribué à un dépôt. Vous ne pouvez donc pas le supprimer !"), _("Règlement déposé"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        
        # Avertissement si appartient à un prélèvement
        if self.Selection()[0].IDprelevement != None :
            dlg = wx.MessageDialog(self, _("Ce règlement est rattaché à un prélèvement automatique.\n\nSouhaitez-vous vraiment le supprimer ?"), _("Avertissement"), wx.YES_NO|wx.NO_DEFAULT|wx.CANCEL|wx.ICON_EXCLAMATION)
            reponse = dlg.ShowModal() 
            dlg.Destroy()
            if reponse != wx.ID_YES :
                return

        # Recherche si frais de gestion existant pour ce règlement
        DB = GestionDB.DB()
        req = """SELECT IDprestation, montant_initial, label
        FROM prestations
        WHERE reglement_frais=%d;
        """ % IDreglement
        DB.ExecuterReq(req,MsgBox="OL_Reglements")
        listeFrais = DB.ResultatReq()
        DB.Close()
        if len(listeFrais) > 0 :
            IDprestationFrais, montantFrais, labelFrais = listeFrais[0]
            dlg = wx.MessageDialog(self, _("Une prestation d'un montant de %.2f %s pour frais de gestion est associée à ce règlement. Cette prestation sera automatiquement supprimée en même temps que le règlement.\n\nConfirmez-vous tout de même la suppression de ce règlement ?") % (montantFrais, SYMBOLE), _("Avertissement"), wx.YES_NO|wx.NO_DEFAULT|wx.CANCEL|wx.ICON_EXCLAMATION)
            if dlg.ShowModal() != wx.ID_YES :
                return
        else :
            IDprestationFrais = None
        
        # Demande de confirmation de suppression
        dlg = wx.MessageDialog(self, _("Confirmez-vous la suppression de ce règlement ?"), _("Suppression"), wx.YES_NO|wx.NO_DEFAULT|wx.CANCEL|wx.ICON_INFORMATION)
        if dlg.ShowModal() == wx.ID_YES :
            DB = GestionDB.DB()
            DB.ReqDEL("reglements", "IDreglement", IDreglement)
            DB.ReqDEL("ventilation", "IDreglement", IDreglement)
            # Mémorise l'action dans l'historique
            req = """SELECT IDfamille
            FROM comptes_payeurs
            WHERE IDcompte_payeur=%d
            """ % self.Selection()[0].compte_payeur
            DB.ExecuterReq(req,MsgBox="OL_Reglements")
            IDfamille = DB.ResultatReq()[0][0]
            
            montant = "%.2f €" % self.Selection()[0].montant
            texteMode = self.Selection()[0].nom_mode
            textePayeur = self.Selection()[0].nom_payeur
            UTILS_Historique.InsertActions([{
                "IDfamille" : IDfamille,
                "IDcategorie" : 8, 
                "action" : _("Suppression du règlement ID%d : %s en %s payé par %s") % (IDreglement, montant, texteMode, textePayeur),
                },])
            
            # Suppression des frais de gestion
            if IDprestationFrais != None :
                DB.ReqDEL("prestations", "IDprestation", IDprestationFrais)
                DB.ReqDEL("ventilation", "IDprestation", IDprestationFrais)
            
            DB.Close()
            # MAJ de l'affichage
            self.MAJ()
        dlg.Destroy()

    def Dupliquer(self, event):
        if self.IDcompte_payeur != None and UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("familles_reglements", "dupliquer") == False : return
        if len(self.Selection()) == 0 :
            dlg = wx.MessageDialog(self, _("Vous n'avez sélectionné aucun règlement à dupliquer dans la liste !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        IDreglement = self.Selection()[0].IDreglement

        # Avertissement si appartient à un prélèvement
        if self.Selection()[0].IDprelevement != None :
            dlg = wx.MessageDialog(self, _("Ce règlement est rattaché à un prélèvement automatique.\n\nSouhaitez-vous vraiment le dupliquer ?"), _("Avertissement"), wx.YES_NO|wx.NO_DEFAULT|wx.CANCEL|wx.ICON_EXCLAMATION)
            reponse = dlg.ShowModal()
            dlg.Destroy()
            if reponse != wx.ID_YES :
                return
        # Charge les noms des champs
        from Data import DATA_Tables
        dicoDB = DATA_Tables.DB_DATA
        lstChamps = []
        for descr in dicoDB["reglements"]:
            lstChamps.append(descr[0])
        #champs = GestionDB.ListeToStr(lstChamps)
        # rappelle le règlement pour avoir toute les données dans l'ordre des champs
        DB = GestionDB.DB()
        req = """SELECT * FROM reglements
        WHERE IDreglement=%d;
        """ % IDreglement
        DB.ExecuterReq(req)
        recordset = DB.ResultatReq()
        for record in recordset:
            lstDonnees = []
            i = 0
            for valeur in record :
                if i != 0:
                    if lstChamps[i] == "IDdepot": valeur = None
                    if lstChamps[i] == "avis_depot": valeur = None
                    if lstChamps[i] == "compta": valeur = None
                    if lstChamps[i] == "IDpiece": valeur = None
                    if lstChamps[i] == "date_saisie": valeur = str(datetime.date.today())
                    if lstChamps[i] == "IDutilisateur": valeur = UTILS_Identification.GetIDutilisateur()
                    lstDonnees.append((lstChamps[i],valeur))
                i += 1
        newID = DB.ReqInsert("reglements",lstDonnees,commit = True,retourID=True,MsgBox = "Insertion de règlement par dupliquer")
        DB.Close()
        # MAJ de l'affichage
        self.MAJ()
        selection = [x for x in self.innerList if x.IDreglement == newID]
        # vérification de la modification de dates
        if len(selection) >=1:
            self.SelectObjects(selection)
            dates = (selection[0].date,selection[0].date_differe)
            self.Modifier(None)
            obj = self.Selection()[0]
            if dates == (obj.date,obj.date_differe):
                mess = "Risque de doublon!\n\n"
                mess += "La duplication n'a pas été suivie d'une modification de dates."
                wx.MessageBox(mess,"Remarque non bloquante")
        #fin Dupliquer

    def VentilationAuto(self, event):
        if self.IDcompte_payeur != None and UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("familles_reglements", "modifier") == False : return
        
        from Ol.OL_Verification_ventilation import VentilationAuto
        ID = event.GetId() 
        if ID == 201 :
            # Uniquement la ligne sélectionnée
            if len(self.Selection()) == 0 :
                dlg = wx.MessageDialog(self, _("Vous n'avez sélectionné aucun règlement !"), _("Erreur"), wx.OK | wx.ICON_EXCLAMATION)
                dlg.ShowModal()
                dlg.Destroy()
                return
            track = self.Selection()[0]
            VentilationAuto(IDcompte_payeur=track.IDcompte_payeur, IDreglement=track.IDreglement)
            self.MAJ(track.IDreglement)
        # Toutes les lignes
        if ID == 202 :
            if len(self.donnees) == 0 :
                dlg = wx.MessageDialog(self, _("La liste des règlements est vide !"), _("Erreur"), wx.OK | wx.ICON_EXCLAMATION)
                dlg.ShowModal()
                dlg.Destroy()
                return
            track = self.donnees[0]
            VentilationAuto(IDcompte_payeur=track.IDcompte_payeur)
            self.MAJ()

    def Rembourser(self, event=None):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("familles_remboursements", "creer") == False : return
        from Dlg import DLG_Saisie_remboursement

        # Recherche le solde de la famille
        solde = DLG_Saisie_remboursement.GetSolde(self.IDcompte_payeur)
        self.MAJ()

        if solde >= 0.0 :
            dlg = wx.MessageDialog(self, _("Il est impossible de créer un remboursement car il n'y a pas d'avoir !\n\nLe solde du compte est de %.2f %s.") % (-solde, SYMBOLE), _("Erreur"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return False

        dlg = DLG_Saisie_remboursement.Dialog(self, IDcompte_payeur=self.IDcompte_payeur, solde=-solde)
        dlg.ShowModal()
        dlg.Destroy()
        self.MAJ()

# -------------------------------------------------------------------------------------------------------------------------------------------

class BarreRecherche(wx.SearchCtrl):
    def __init__(self, parent):
        wx.SearchCtrl.__init__(self, parent, size=(-1, -1), style=wx.TE_PROCESS_ENTER)
        self.parent = parent
        self.rechercheEnCours = False
        
        self.SetDescriptiveText(_("Rechercher un règlement..."))
        self.ShowSearchButton(True)
        
        self.listView = self.parent.ctrl_reglements
        nbreColonnes = self.listView.GetColumnCount()
        self.listView.SetFilter(Filter.TextSearch(self.listView, self.listView.columns[0:nbreColonnes]))
        
        self.SetCancelBitmap(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Interdit.png"), wx.BITMAP_TYPE_PNG))
        self.SetSearchBitmap(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Loupe.png"), wx.BITMAP_TYPE_PNG))
        
        self.Bind(wx.EVT_SEARCHCTRL_SEARCH_BTN, self.OnSearch)
        self.Bind(wx.EVT_SEARCHCTRL_CANCEL_BTN, self.OnCancel)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnDoSearch)
        self.Bind(wx.EVT_TEXT, self.OnDoSearch)

    def OnSearch(self, evt):
        self.Recherche()
            
    def OnCancel(self, evt):
        self.SetValue("")
        self.Recherche()

    def OnDoSearch(self, evt):
        self.Recherche()
        
    def Recherche(self):
        txtSearch = self.GetValue().replace("'","\\'")
        self.ShowCancelButton(len(txtSearch))
        self.listView.GetFilter().SetText(txtSearch)
        self.listView.RepopulateList()
        self.Refresh() 

# -------------------------------------------------------------------------------------------------------------------------------------------

class ListviewAvecFooter(PanelAvecFooter):
    def __init__(self, parent, kwargs={}):
        dictColonnes = {
            "nom_mode" : {"mode" : "nombre", "singulier" : _("règlement"), "pluriel" : _("règlements"), "alignement" : wx.ALIGN_CENTER},
            "montant" : {"mode" : "total"},
            "resteAVentiler" : {"mode" : "total"},
            }
        PanelAvecFooter.__init__(self, parent, ListView, kwargs, dictColonnes)


# -------------------------------------------------------------------------------------------------------------------------------------------

class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self, -1, name="test1")
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_1.Add(panel, 1, wx.ALL|wx.EXPAND)
        self.SetSizer(sizer_1)
        self.myOlv = ListView(panel, id=-1, IDcompte_payeur=567, name="OL_test", style=wx.LC_REPORT|wx.SUNKEN_BORDER|wx.LC_SINGLE_SEL|wx.LC_HRULES|wx.LC_VRULES)
        self.myOlv.MAJ() 
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_2.Add(self.myOlv, 1, wx.ALL|wx.EXPAND, 4)
        panel.SetSizer(sizer_2)
        self.Layout()
        self.SetSize((800, 200))

if __name__ == '__main__':
    app = wx.App(0)
    #wx.InitAllImageHandlers()
    frame_1 = MyFrame(None, -1, "OL TEST")
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()
