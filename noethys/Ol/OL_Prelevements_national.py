#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activit�s
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-11 Ivan LUCAS
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------


import Chemins
from Utils import UTILS_Adaptations
from Utils.UTILS_Traduction import _
import wx
from Ctrl import CTRL_Bouton_image
import datetime
import decimal
import GestionDB
from Utils import UTILS_Dates
from Dlg import DLG_Saisie_prelevement
from Utils import UTILS_Identification
from Utils import UTILS_Prelevements

from Utils import UTILS_Config
SYMBOLE = UTILS_Config.GetParametre("monnaie_symbole", "�")


from Utils import UTILS_Interface
from Ctrl.CTRL_ObjectListView import FastObjectListView, ColumnDefn, Filter, CTRL_Outils

from Utils import UTILS_Titulaires

DICT_BANQUES = {}


class Track(object):
    def __init__(self, donnees, dictTitulaires):
        self.dictTitulaires = dictTitulaires
        self.IDprelevement = donnees["IDprelevement"]
        self.IDfamille = donnees["IDfamille"]
        self.IDcompte_payeur = donnees["IDcompte_payeur"]
        self.prelevement_etab = donnees["prelevement_etab"]
        self.prelevement_guichet = donnees["prelevement_guichet"]
        self.prelevement_numero = donnees["prelevement_numero"]
        self.prelevement_banque = donnees["prelevement_banque"]
        self.prelevement_cle = donnees["prelevement_cle"]
        self.prelevement_iban =  donnees["prelevement_iban"]
        self.prelevement_bic =  donnees["prelevement_bic"]
        self.prelevement_reference_mandat =  donnees["prelevement_reference_mandat"]
        self.prelevement_date_mandat =  donnees["prelevement_date_mandat"]
        
        # Si IBAN manquant, on le calcule
        if self.prelevement_iban == None and self.prelevement_etab != None and self.prelevement_guichet != None and self.prelevement_numero != None and self.prelevement_cle != None :
            rib = self.prelevement_etab + self.prelevement_guichet + self.prelevement_numero + self.prelevement_cle
            self.prelevement_iban = UTILS_Prelevements.ConvertirRIBenIBAN(rib, codePays="FR")
                
        self.titulaire = donnees["titulaire"]
        self.type = donnees["type"]
        self.IDfacture = donnees["IDfacture"]
        self.libelle = donnees["libelle"]
        self.montant = donnees["montant"]
        self.statut = donnees["statut"]
        self.IDlot = donnees["IDlot"]
        
        self.MAJnomBanque()
        
        self.titulaires = ""
        self.InitNomsTitulaires() 
        
        self.IDreglement = donnees["IDreglement"]
        if self.IDreglement == None :
            self.reglement = False
        else :
            self.reglement = True
        self.dateReglement = donnees["dateReglement"]
        self.IDdepot = donnees["IDdepot"]

        self.etat = donnees["etat"] # "ajout", "modif"
    
    def InitNomsTitulaires(self):
        if self.IDfamille != None :
            self.titulaires = self.dictTitulaires[self.IDfamille]["titulairesSansCivilite"]
    
    def MAJnomBanque(self):
        if self.prelevement_banque in DICT_BANQUES :
            self.nomBanque = DICT_BANQUES[self.prelevement_banque]
        else :
            self.nomBanque = ""


def GetTracks(IDlot=None):
    """ R�cup�ration des donn�es """
    dictTitulaires = UTILS_Titulaires.GetTitulaires() 
    if IDlot == None :
        return []
    DB = GestionDB.DB()
    req = """SELECT 
    prelevements.IDprelevement, prelevements.IDfamille, 
    prelevements.prelevement_etab, prelevements.prelevement_guichet, prelevements.prelevement_numero, 
    prelevements.prelevement_banque, prelevements.prelevement_cle,
    prelevements.prelevement_iban, prelevements.prelevement_bic, 
    prelevements.prelevement_reference_mandat, prelevements.prelevement_date_mandat,
    prelevements.titulaire, prelevements.type, prelevements.IDfacture, prelevements.libelle, 
    prelevements.montant, prelevements.statut, prelevements.IDlot,
    banques.nom,
    reglements.IDreglement, reglements.date, reglements.IDdepot,
    comptes_payeurs.IDcompte_payeur
    FROM prelevements
    LEFT JOIN banques ON banques.IDbanque = prelevements.prelevement_banque
    LEFT JOIN reglements ON reglements.IDprelevement = prelevements.IDprelevement
    LEFT JOIN comptes_payeurs ON comptes_payeurs.IDfamille = prelevements.IDfamille
    WHERE IDlot=%d
    ;""" % IDlot
    DB.ExecuterReq(req,MsgBox="ExecuterReq")
    listeDonnees = DB.ResultatReq()
    DB.Close()
    listeListeView = []
    for IDprelevement, IDfamille, prelevement_etab, prelevement_guichet, prelevement_numero, prelevement_banque, prelevement_cle, prelevement_iban, prelevement_bic, prelevement_reference_mandat, prelevement_date_mandat, titulaire, type_prelevement, IDfacture, libelle, montant, statut, IDlot, nomBanque, IDreglement, dateReglement, IDdepot, IDcompte_payeur in listeDonnees :
        dictTemp = {
            "IDprelevement" : IDprelevement, "IDfamille" : IDfamille, "prelevement_etab" : prelevement_etab, "prelevement_guichet" : prelevement_guichet, "prelevement_numero" : prelevement_numero, 
            "prelevement_banque" : prelevement_banque, "prelevement_cle" : prelevement_cle, "prelevement_iban" : prelevement_iban, 
            "prelevement_bic" : prelevement_bic, "prelevement_reference_mandat" : prelevement_reference_mandat, "prelevement_date_mandat" : prelevement_date_mandat,
            "titulaire" : titulaire, "type" : type_prelevement, "IDfacture" : IDfacture, 
            "libelle" : libelle, "montant" : montant, "statut" : statut, "IDlot" : IDlot, "nomBanque" : nomBanque, "etat" : None,
            "IDreglement" : IDreglement, "dateReglement" : dateReglement, "IDdepot" : IDdepot, "IDcompte_payeur" : IDcompte_payeur,
            }
        track = Track(dictTemp, dictTitulaires)
        listeListeView.append(track)
    return listeListeView


        
    
class ListView(FastObjectListView):
    def __init__(self, *args, **kwds):
        # R�cup�ration des param�tres perso
        self.IDlot = kwds.pop("IDlot", None)
        self.typePrelevement = kwds.pop("typePrelevement", "national")
        self.selectionID = None
        self.selectionTrack = None
        self.criteres = ""
        self.itemSelected = False
        self.popupIndex = -1
        self.listeFiltres = []
        self.tracks = []
        self.numColonneTri = 2
        self.ordreAscendant = True
        self.listeSuppressions = []
        self.dictBanques = {}
        self.reglement_auto = False
        # Initialisation du listCtrl
        self.InitBanques() 
        self.nom_fichier_liste = __file__
        FastObjectListView.__init__(self, *args, **kwds)
        # Binds perso
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnItemActivated)
        self.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)
        
    def OnItemActivated(self,event):
        self.Modifier()

    def InitModel(self, tracks=None, IDcompte=None, IDmode=None):
        self.InitBanques() 
        if tracks != None :
            self.tracks = tracks
        self.donnees = self.tracks
        
    def InitBanques(self):
        global DICT_BANQUES
        DICT_BANQUES = self.GetNomsBanques()
    
    def GetNomsBanques(self):
        DB = GestionDB.DB()
        req = """SELECT IDbanque, nom
        FROM banques;"""
        DB.ExecuterReq(req,MsgBox="ExecuterReq")
        listeDonnees = DB.ResultatReq()
        DB.Close()
        dictBanques = {}
        for IDbanque, nom in listeDonnees :
            dictBanques[IDbanque] = nom
        return dictBanques
    
    def MAJnomsBanquesTracks(self):
        self.InitBanques() 
        for track in self.GetObjects() :
            track.MAJnomBanque()
            self.RefreshObject(track)
            
    def InitObjectListView(self):            
        # Couleur en alternance des lignes
        self.oddRowsBackColor = UTILS_Interface.GetValeur("couleur_tres_claire", wx.Colour(240, 251, 237))
        self.evenRowsBackColor = wx.Colour(255, 255, 255)
        self.useExpansionColumn = True
                
        # Image list
        self.imgValide = self.AddNamedImages("valide", wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Ok.png"), wx.BITMAP_TYPE_PNG))
        self.imgRefus = self.AddNamedImages("refus", wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Interdit.png"), wx.BITMAP_TYPE_PNG))
        self.imgAttente = self.AddNamedImages("attente", wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Attente.png"), wx.BITMAP_TYPE_PNG))
        
        def GetImageStatut(track):
            if track.statut == "valide" : return self.imgValide
            if track.statut == "refus" : return self.imgRefus
            if track.statut == "attente" : return self.imgAttente

        def GetImageReglement(track):
            if track.reglement == False :
                return self.imgRefus
            else :
                return self.imgValide

        def FormateDateCourt(dateDD):
            if dateDD == None :
                return ""
            else:
                return UTILS_Dates.DateEngFr(str(dateDD))

        def FormateMontant(montant):
            if montant == None : return ""
            return "%.2f %s" % (montant, SYMBOLE)

        def FormateType(statut):
            if statut == "manuel" : return _("Manuel")
            if statut == "facture" : return _("Facture")
            return ""

        def FormateStatut(statut):
            if statut == "valide" : return _("Valide")
            if statut == "refus" : return _("Refus")
            if statut == "attente" : return _("Attente")

        def FormateReglement(reglement):
            if reglement == True :
                return _("Oui")
            else:
                return ""

        liste_Colonnes = [
            ColumnDefn(_("ID"), "left", 0, "IDprelevement"),
            ColumnDefn(_("Famille"), 'left', 230, "titulaires"),
##            ColumnDefn(_("Type"), 'left', 70, "type", stringConverter=FormateType),
            ColumnDefn(_("Libell�"), 'left', 110, "libelle"),
##            ColumnDefn(_("Banque"), 'left', 120, "nomBanque"),
            ColumnDefn(_("Montant"), 'right', 70, "montant", stringConverter=FormateMontant),
            ColumnDefn(_("Statut"), 'left', 80, "statut", stringConverter=FormateStatut, imageGetter=GetImageStatut),
            ColumnDefn(_("R�glement"), 'left', 70, "reglement", stringConverter=FormateReglement, imageGetter=GetImageReglement),
##            ColumnDefn(_("IBAN"), 'left', 190, "prelevement_iban"),
##            ColumnDefn(_("BIC"), 'left', 80, "prelevement_bic"),
            ColumnDefn(_("Etab."), 'left', 50, "prelevement_etab"),
            ColumnDefn(_("Guich."), 'left', 50, "prelevement_guichet"),
            ColumnDefn(_("Compte"), 'left', 90, "prelevement_numero"),
            ColumnDefn(_("Cl�"), 'left', 30, "prelevement_cle"),
            ColumnDefn(_("Banque"), 'left', 130, "nomBanque"),
            ColumnDefn(_("Titulaire du compte"), 'left', 160, "titulaire"),
            ]
        

        self.SetColumns(liste_Colonnes)
        self.CreateCheckStateColumn(1)
        self.SetEmptyListMsg(_("Aucun pr�l�vement"))
        self.SetEmptyListMsgFont(wx.FFont(11, wx.DEFAULT, False, "Tekton"))
##        self.SetSortColumn(self.columns[self.numColonneTri])
        self.SortBy(self.numColonneTri, ascending=self.ordreAscendant)
        self.SetObjects(self.donnees)
       
    def MAJ(self, tracks=None, ID=None, selectionTrack=None, nextTrack=None, IDcompte=None, IDmode=None):
        self.InitModel(tracks, IDcompte, IDmode)
        self.InitObjectListView()
        # S�lection d'un item
        if selectionTrack != None :
            self.SelectObject(selectionTrack, deselectOthers=True, ensureVisible=True)
            if self.GetSelectedObject() == None :
                self.SelectObject(nextTrack, deselectOthers=True, ensureVisible=True)

    def Selection(self):
        return self.GetSelectedObjects()

    def OnContextMenu(self, event):
        """Ouverture du menu contextuel """
        if len(self.Selection()) == 0:
            noSelection = True
        else:
            noSelection = False
            ID = self.Selection()[0].IDprelevement
                
        # Cr�ation du menu contextuel
        menuPop = UTILS_Adaptations.Menu()

        # Item Saisie manuelle
##        item = wx.MenuItem(menuPop, 10, _("Ajouter un pr�l�vement manuel"))
##        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Ajouter.png"), wx.BITMAP_TYPE_PNG)
##        item.SetBitmap(bmp)
##        menuPop.AppendItem(item)
##        self.Bind(wx.EVT_MENU, self.Saisie_manuelle, id=10)

        # Item Saisie de factures
        item = wx.MenuItem(menuPop, 11, _("Ajouter une ou plusieurs factures"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Ajouter.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.Saisie_factures, id=11)

        menuPop.AppendSeparator()

        # Item Modifier
        item = wx.MenuItem(menuPop, 20, _("Modifier"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Modifier.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.Modifier, id=20)
        if noSelection == True : item.Enable(False)
                
        # Item Supprimer
        item = wx.MenuItem(menuPop, 30, _("Supprimer"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Supprimer.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.Supprimer, id=30)
                
        menuPop.AppendSeparator()
    
        # Item Apercu avant impression
        item = wx.MenuItem(menuPop, 40, _("Aper�u avant impression"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Apercu.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.Apercu, id=40)
        
        # Item Imprimer
        item = wx.MenuItem(menuPop, 50, _("Imprimer"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Imprimante.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.Imprimer, id=50)
        
        menuPop.AppendSeparator()
    
        # Item Export Texte
        item = wx.MenuItem(menuPop, 600, _("Exporter au format Texte"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Texte2.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.ExportTexte, id=600)
        
        # Item Export Excel
        item = wx.MenuItem(menuPop, 700, _("Exporter au format Excel"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Excel.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.ExportExcel, id=700)

        self.PopupMenu(menuPop)
        menuPop.Destroy()

    def Impression(self):
        # R�cup�re l'intitul� du compte
        txtIntro = self.GetParent().GetLabelParametres()
        # R�cup�re le total
        total = 0.0
        for track in self.donnees :
            total += track.montant
        txtTotal = self.GetTexteTotaux().replace("<B>", "").replace("</B>", "")
        from Utils import UTILS_Printer
        prt = UTILS_Printer.ObjectListViewPrinter(self, titre=_("Liste des pr�l�vements"), intro=txtIntro, total=txtTotal, format="A", orientation=wx.LANDSCAPE)
        return prt
        
    def Apercu(self, event=None):
        self.Impression().Preview()

    def Imprimer(self, event=None):
        self.Impression().Print()

    def ExportTexte(self, event=None):
        from Utils import UTILS_Export
        UTILS_Export.ExportTexte(self, titre=_("Liste des pr�l�vements"))
        
    def ExportExcel(self, event=None):
        from Utils import UTILS_Export
        UTILS_Export.ExportExcel(self, titre=_("Liste des pr�l�vements"))
        
    def Saisie_manuelle(self, event=None):
        """ Saisie manuelle """
        dictTitulaires = UTILS_Titulaires.GetTitulaires() 
        dictTemp = {
            "IDprelevement" : None, "IDfamille" : None, "prelevement_etab" : "", "prelevement_guichet" : "", "prelevement_numero" : "", 
            "prelevement_banque" : "", "prelevement_cle" : "", "prelevement_iban" : "", "prelevement_bic" : "", 
            "prelevement_reference_mandat" : "", "prelevement_date_mandat" : None,
            "titulaire" : "", "type" : "manuel", "IDfacture" : None, 
            "libelle" : "", "montant" : 0.00, "statut" : "attente", "IDlot" : self.IDlot, "nomBanque" : "", "etat" : "ajout",
            "IDreglement" : None, "dateReglement" : None, "IDdepot" : None, "IDcompte_payeur" : None,
            }
        track = Track(dictTemp, dictTitulaires)
        dlg = DLG_Saisie_prelevement.Dialog(self, track=track)      
        if dlg.ShowModal() == wx.ID_OK:
            track = dlg.GetTrack()
            self.AddObject(track)
            self.MAJtotaux() 
        dlg.Destroy() 
        
    def Saisie_factures(self, event=None):
        """ Saisie de factures """
        from Dlg import DLG_Prelevements_factures
        dlg = DLG_Prelevements_factures.Dialog(self)
        reponse = dlg.ShowModal()
        tracks = dlg.GetTracks()
        dlg.Destroy()
        if reponse != wx.ID_OK :
            return
        self.AjoutFactures(tracks)
    
    def AjoutFactures(self, tracks=[]):
        # V�rifie que cette facture n'est pas d�j� pr�sente dans le lot
        listeFacturesPresentes = []
        for track in self.GetObjects() :
            if track.IDfacture != None :
                listeFacturesPresentes.append(track.IDfacture)
        
        # MAJ de la liste affich�e
        dictTitulaires = UTILS_Titulaires.GetTitulaires() 
        listeNewTracks = []
        for track in tracks :
            dictTemp = {
                "IDprelevement" : None, "IDfamille" : track.IDfamille, "prelevement_etab" : track.prelevement_etab, "prelevement_guichet" : track.prelevement_guichet, "prelevement_numero" : track.prelevement_numero, 
                "prelevement_banque" : track.prelevement_banque, "prelevement_cle" : track.prelevement_cle, "prelevement_iban" : track.prelevement_iban, 
                "prelevement_bic" : track.prelevement_bic, "prelevement_reference_mandat" : track.prelevement_reference_mandat, "prelevement_date_mandat" : track.prelevement_date_mandat,
                "titulaire" : track.prelevement_payeur, "type" : "facture", "IDfacture" : track.IDfacture, 
                "libelle" : _("FACT%06d") % track.numero, "montant" : -track.solde, "statut" : "attente", "IDlot" : self.IDlot, "nomBanque" : "", "etat" : "ajout", "IDreglement" : None, "dateReglement" : None,
                "IDdepot" : None, "IDcompte_payeur" : track.IDcompte_payeur,
                }
            if track.IDfacture not in listeFacturesPresentes :
                listeNewTracks.append(Track(dictTemp, dictTitulaires))
        self.AddObjects(listeNewTracks)
        self.MAJtotaux() 

    def Modifier(self, event=None):
        if len(self.Selection()) == 0 :
            dlg = wx.MessageDialog(self, _("Vous n'avez s�lectionn� aucun pr�l�vement � modifier dans la liste !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        track = self.Selection()[0]
        dlg = DLG_Saisie_prelevement.Dialog(self, track=track, activeMontant=False)      
        if dlg.ShowModal() == wx.ID_OK:
            if track.etat != "ajout" :
                track.etat = "modif"
            self.RefreshObject(track)
            self.MAJtotaux() 
        dlg.Destroy() 
        self.MAJnomsBanquesTracks()

    def Supprimer(self, event=None):
        if len(self.Selection()) == 0 and len(self.GetTracksCoches()) == 0 :
            dlg = wx.MessageDialog(self, _("Vous n'avez s�lectionn� aucun pr�l�vement � supprimer dans la liste !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        
        if len(self.GetTracksCoches()) > 0 :
            # Suppression multiple
            listeSelections = self.GetTracksCoches()
            dlg = wx.MessageDialog(self, _("Souhaitez-vous vraiment supprimer les %d pr�l�vements coch�s ?") % len(listeSelections), _("Suppression"), wx.YES_NO|wx.NO_DEFAULT|wx.CANCEL|wx.ICON_INFORMATION)
            reponse = dlg.ShowModal() 
            dlg.Destroy()
            if reponse != wx.ID_YES :
                return
        
        else :
            # Suppression unique
            listeSelections = self.Selection()
            dlg = wx.MessageDialog(self, _("Souhaitez-vous vraiment supprimer le pr�l�vement s�lectionn� ?"), _("Suppression"), wx.YES_NO|wx.NO_DEFAULT|wx.CANCEL|wx.ICON_INFORMATION)
            reponse = dlg.ShowModal() 
            dlg.Destroy()
            if reponse != wx.ID_YES :
                return

        # V�rifie que le r�glement n'est pas d�j� d�pos� en banque
        listeDepots = []
        for track in listeSelections :
            if track.IDdepot != None :
                listeDepots.append(track)
        if len(listeDepots) > 0 :
            dlg = wx.MessageDialog(self, _("Suppression interdite car %d pr�l�vement(s) de la s�lection ont d�j� un r�glement attribu� � un d�p�t de r�glement !") % len(listeDepots), _("Remarque"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        
        # Suppression
        for track in listeSelections :
            if track.etat in (None, "modif") :
                self.listeSuppressions.append(track)
            self.RemoveObject(track)
        self.MAJtotaux() 
        

    def CocheTout(self, event=None):
        if self.GetFilter() != None :
            listeObjets = self.GetFilteredObjects()
        else :
            listeObjets = self.GetObjects()
        for track in listeObjets :
            self.Check(track)
            self.RefreshObject(track)
        
    def CocheRien(self, event=None):
        for track in self.donnees :
            self.Uncheck(track)
            self.RefreshObject(track)

    def GetTracksCoches(self):
        return self.GetCheckedObjects()
    
    def SetStatut(self, statut="attente") :
        listeDepots = []
        for track in self.GetObjects() :
            if self.IsChecked(track) :
                # Changement de statut
                track.statut = statut
                
                # R�glement automatique
                if self.reglement_auto == True and statut == "valide" :
                    track.reglement = True   
                
                # Annulation du r�glement si statut = refus
                if statut == "refus" :
                    if track.IDdepot != None :
                        listeDepots.append(track)
                    else :
                        track.reglement = False
                             
                if track.etat != "ajout" :
                    track.etat = "modif"
                self.RefreshObject(track)
                
        self.MAJtotaux() 
        
        if len(listeDepots) > 0 :
            dlg = wx.MessageDialog(self, _("Notez que Noethys n'a pas proc�d� changement de statut de %d pr�l�vement(s) car le r�glement correspondant appartient d�j� � un d�p�t de r�glement !") % len(listeDepots), _("Remarque"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return


    def SetRegle(self, etat=False) :
        listeAnomalies = []
        listeDepots = []
        for track in self.GetObjects() :                
            if self.IsChecked(track) :
    
                if etat == True :
                    # Si on veut r�gler
                    if track.statut in ("valide", "attente") :
                        track.reglement = True
                        if track.etat != "ajout" :
                            track.etat = "modif"
                        self.RefreshObject(track)
                    else :
                        listeAnomalies.append(track)
                
                if etat == False :
                    # Si on veut annuler le r�glement
                    if track.IDdepot != None :
                        listeDepots.append(track)
                    else :
                        track.reglement = False
                        if track.etat != "ajout" :
                            track.etat = "modif"
                        self.RefreshObject(track)

        if len(listeAnomalies) > 0 :
            dlg = wx.MessageDialog(self, _("Notez que Noethys n'a pas proc�d� au r�glement de %d pr�l�vement(s) en raison de leur statut 'Refus'.") % len(listeAnomalies), _("Remarque"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return

        if len(listeDepots) > 0 :
            dlg = wx.MessageDialog(self, _("Notez que Noethys n'a pas proc�d� � la suppression de %d pr�l�vement(s) car le r�glement correspondant appartient d�j� � un d�p�t de r�glement !") % len(listeDepots), _("Remarque"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return

        self.MAJtotaux() 

    def GetLabelListe(self):
        """ R�cup�re le nombre de pr�l�vements et le montant total de la liste """
        nbre = 0
        montant = 0.0
        for track in self.GetObjects() :
            nbre += 1
            montant += track.montant
        # Label de staticbox
        if nbre > 1 :
            texte = _("pr�l�vements")
        else :
            texte = _("pr�l�vement")
        label = "%d %s (%.2f %s)" % (nbre, texte, montant, SYMBOLE)
        return label          

    def MAJtotaux(self):
        """ Cr�� le texte infos avec les stats du lot """
        if self.GetParent().GetName() != "DLG_Saisie_prelevement_lot" :
            return
        # Label de staticbox
        texte = self.GetTexteTotaux()
        self.GetParent().ctrl_totaux.SetLabel(texte)
        self.GetParent().box_prelevements_staticbox.SetLabel(self.GetLabelListe())

    def GetTexteTotaux(self):
        # R�cup�ration des chiffres
        nbreTotal = 0
        montantTotal = 0.0
        dictDetails = {}
        for track in self.GetObjects() :
            nbreTotal += 1
            montantTotal += track.montant
            # Regroupement par statut
            if (track.statut in dictDetails) == False :
                dictDetails[track.statut] = {"nbre" : 0, "montant" : 0.0}
            dictDetails[track.statut]["nbre"] += 1
            dictDetails[track.statut]["montant"] += track.montant
            # Regroupement par r�glemennt
            if track.reglement == True :
                reglement = "regle"
            else :
                reglement = "pasregle"
            if (reglement in dictDetails) == False :
                dictDetails[reglement] = {"nbre" : 0, "montant" : 0.0}
            dictDetails[reglement]["nbre"] += 1
            dictDetails[reglement]["montant"] += track.montant
            
        # Cr�ation du texte
        if nbreTotal == 0 :
            texte = _("<B>Aucun pr�l�vement.   </B>")
        elif nbreTotal == 1 :
            texte = _("<B>%d pr�l�vement (%.2f %s) : </B>") % (nbreTotal, montantTotal, SYMBOLE)
        else :
            texte = _("<B>%d pr�l�vements (%.2f %s) : </B>") % (nbreTotal, montantTotal, SYMBOLE)
        
        for key in ("attente", "valide", "refus", "regle", "pasregle") :
            if key in dictDetails :
                dictDetail = dictDetails[key]
                if dictDetail["nbre"] == 1 :
                    if key == "attente" : label = _("en attente")
                    if key == "valide" : label = _("valid�")
                    if key == "refus" : label = _("refus�")
                    if key == "regle" : label = _("r�gl�")
                    if key == "pasregle" : label = _("non r�gl�")
                else :
                    if key == "attente" : label = _("en attente")
                    if key == "valide" : label = _("valid�s")
                    if key == "refus" : label = _("refus�s")
                    if key == "regle" : label = _("r�gl�s")
                    if key == "pasregle" : label = _("non r�gl�s")
                texteDetail = "%d %s (%.2f %s), " % (dictDetail["nbre"], label, dictDetail["montant"], SYMBOLE)
                texte += texteDetail
        if len(dictDetails) > 0 :
            texte = texte[:-2] + "."
        else:
            texte = texte[:-7] + "</B>"
        return texte

    def Sauvegarde(self, IDlot=None, datePrelevement=None, IDcompte=None, IDmode=None):
        """ Sauvegarde des donn�es """
        DB = GestionDB.DB()
        
        # Ajouts et suppressions
        for track in self.GetObjects() :

            listeDonnees = [
                ("IDlot", IDlot ),
                ("IDfamille", track.IDfamille),
                ("prelevement_etab", track.prelevement_etab),
                ("prelevement_guichet", track.prelevement_guichet),
                ("prelevement_numero", track.prelevement_numero),
                ("prelevement_banque", track.prelevement_banque),
                ("prelevement_cle", track.prelevement_cle),
                ("prelevement_iban", track.prelevement_iban),
                ("prelevement_bic", track.prelevement_bic),
                ("prelevement_reference_mandat", track.prelevement_reference_mandat),
                ("prelevement_date_mandat", track.prelevement_date_mandat),
                ("titulaire", track.titulaire),
                ("type", track.type),
                ("IDfacture", track.IDfacture),
                ("libelle", track.libelle),
                ("montant", track.montant),
                ("statut", track.statut),
                ]

            # Ajout
            if track.etat == "ajout" :
                track.IDprelevement = DB.ReqInsert("prelevements", listeDonnees)
                self.RefreshObject(track)
            
            # Modification
            if track.etat == "modif" :
                DB.ReqMAJ("prelevements", listeDonnees, "IDprelevement", track.IDprelevement)
        
        # Supppressions
        for track in self.listeSuppressions :
            if track.IDprelevement != None :
                DB.ReqDEL("prelevements", "IDprelevement", track.IDprelevement)
            if track.IDreglement != None :
                DB.ReqDEL("reglements", "IDreglement", track.IDreglement)
                DB.ReqDEL("ventilation", "IDreglement", track.IDreglement)

        DB.Close() 
        
        # Sauvegarde des r�glements
        self.SauvegardeReglements(date=datePrelevement, IDcompte=IDcompte, IDmode=IDmode)


    def SauvegardeReglements(self, date=None, IDcompte=None, IDmode=None):
        """ A effectuer apr�s la sauvegarde des pr�l�vements """
        DB = GestionDB.DB()
        
        # Recherche des payeurs
        req = """SELECT IDpayeur, IDcompte_payeur, nom
        FROM payeurs;"""
        DB.ExecuterReq(req,MsgBox="ExecuterReq")
        listeDonnees = DB.ResultatReq()
        dictPayeurs = {}
        for IDpayeur, IDcompte_payeur, nom in listeDonnees :
            if (IDcompte_payeur in dictPayeurs) == False :
                dictPayeurs[IDcompte_payeur] = []
            dictPayeurs[IDcompte_payeur].append({"nom" : nom, "IDpayeur" : IDpayeur})

        
        # R�cup�ration des prestations � ventiler pour chaque facture
        listeIDfactures = []
        for track in self.GetObjects() :
            if track.IDfacture != None :
                listeIDfactures.append(track.IDfacture)
        
        if len(listeIDfactures) == 0 : conditionFactures = "()"
        elif len(listeIDfactures) == 1 : conditionFactures = "(%d)" % listeIDfactures[0]
        else : conditionFactures = str(tuple(listeIDfactures))
            
        req = """SELECT 
        prestations.IDprestation, prestations.IDcompte_payeur, prestations.montant, 
        prestations.IDfacture, SUM(ventilation.montant) AS montant_ventilation
        FROM prestations
        LEFT JOIN ventilation ON prestations.IDprestation = ventilation.IDprestation
        WHERE prestations.IDfacture IN %s
        GROUP BY prestations.IDprestation
        ;""" % conditionFactures
        DB.ExecuterReq(req,MsgBox="ExecuterReq")
        listeDonnees = DB.ResultatReq()
        
        dictFactures = {}
        for IDprestation, IDcompte_payeur, montant, IDfacture, ventilation in listeDonnees :
            if ventilation == None : 
                ventilation = 0.0
            montant = decimal.Decimal(montant)
            ventilation = decimal.Decimal(ventilation)
            aventiler = montant - ventilation
            if aventiler > decimal.Decimal(0.0) :
                if (IDfacture in dictFactures) == False :
                    dictFactures[IDfacture] = []
                dictFactures[IDfacture].append({"IDprestation" : IDprestation, "IDcompte_payeur" : IDcompte_payeur, "montant" : montant, "ventilation" : ventilation, "aventiler" : aventiler})
                        
        # Sauvegarde des r�glements + ventilation
        listeSuppressionReglements = []
        for track in self.GetObjects() :

            # Ajouts et modifications
            if track.reglement == True :
                
                # Recherche du payeur
                IDpayeur = None
                if track.IDcompte_payeur in dictPayeurs :
                    for dictPayeur in dictPayeurs[track.IDcompte_payeur] :
                        if dictPayeur["nom"] == track.titulaire :
                            IDpayeur = dictPayeur["IDpayeur"]
                
                # Si pas de payeur correspond au titulaire du compte trouv� :
                if IDpayeur == None :
                    IDpayeur = DB.ReqInsert("payeurs", [("IDcompte_payeur", track.IDcompte_payeur), ("nom", track.titulaire)])
                    
                # Cr�ation des donn�es � sauvegarder
                listeDonnees = [
                    ("IDcompte_payeur", track.IDcompte_payeur),
                    ("date", date),
                    ("IDmode", IDmode),
                    ("IDemetteur", None),
                    ("numero_piece", None),
                    ("montant", track.montant),
                    ("IDpayeur", IDpayeur),
                    ("observations", None),
                    ("numero_quittancier", None),
                    ("IDcompte", IDcompte),
                    ("date_differe", None),
                    ("encaissement_attente", 0),
                    ("date_saisie", datetime.date.today()),
                    ("IDutilisateur", UTILS_Identification.GetIDutilisateur() ),
                    ("IDprelevement", track.IDprelevement),
                    ]
                

                # Ajout
                if track.IDreglement == None :
                    track.IDreglement = DB.ReqInsert("reglements", listeDonnees)
                    
                # Modification
                else:
                    DB.ReqMAJ("reglements", listeDonnees, "IDreglement", track.IDreglement)
                track.dateReglement = date
                
                # ----------- Sauvegarde de la ventilation ---------
                if track.IDfacture in dictFactures :
                    for dictFacture in dictFactures[track.IDfacture] :
                        listeDonnees = [    
                                ("IDreglement", track.IDreglement),
                                ("IDcompte_payeur", track.IDcompte_payeur),
                                ("IDprestation", dictFacture["IDprestation"]),
                                ("montant", float(dictFacture["aventiler"])),
                            ]
                        IDventilation = DB.ReqInsert("ventilation", listeDonnees)        
            
            # Suppression de r�glements et ventilation
            else :

                if track.IDreglement != None :
                    DB.ReqDEL("reglements", "IDreglement", track.IDreglement)
                    DB.ReqDEL("ventilation", "IDreglement", track.IDreglement)
            
            # MAJ du track
            self.RefreshObject(track)
        
        DB.Close() 





# -------------------------------------------------------------------------------------------------------------------------------------------

class BarreRecherche(wx.SearchCtrl):
    def __init__(self, parent):
        wx.SearchCtrl.__init__(self, parent, size=(-1, -1), style=wx.TE_PROCESS_ENTER)
        self.parent = parent
        self.rechercheEnCours = False
        
        self.SetDescriptiveText(_("Rechercher un pr�l�vement..."))
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
        txtSearch = self.GetValue()
        self.ShowCancelButton(len(txtSearch))
        self.listView.GetFilter().SetText(txtSearch)
        self.listView.RepopulateList()
        self.Refresh() 


# -------------------------------------------------------------------------------------------------------------------------------------------

class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self, -1, name="test1")
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_1.Add(panel, 1, wx.ALL|wx.EXPAND)
        self.SetSizer(sizer_1)
        
        self.myOlv = ListView(panel, id=-1, name="OL_test", style=wx.LC_REPORT|wx.SUNKEN_BORDER|wx.LC_SINGLE_SEL|wx.LC_HRULES|wx.LC_VRULES)
        tracks = GetTracks(IDlot=1)
        self.myOlv.MAJ(tracks=tracks) 
        
        self.bouton_test = wx.Button(panel, -1, _("Bouton test"))
        self.Bind(wx.EVT_BUTTON, self.OnBoutonTest, self.bouton_test)
        
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_2.Add(self.myOlv, 1, wx.ALL|wx.EXPAND, 4)
        sizer_2.Add(self.bouton_test, 0, wx.ALL|wx.EXPAND, 4)
        panel.SetSizer(sizer_2)
        self.Layout()
        self.SetSize((800, 400))
        self.CenterOnScreen()
        
    def OnBoutonTest(self, event):
        print("Test de la sauvegarde des reglements :")
        self.myOlv.SauvegardeReglements(date=datetime.date.today(), IDcompte=99)
        
        
        
        

if __name__ == '__main__':
    app = wx.App(0)
    #wx.InitAllImageHandlers()
    frame_1 = MyFrame(None, -1, "OL TEST")
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()
