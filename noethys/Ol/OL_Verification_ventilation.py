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
from Utils import UTILS_Titulaires
from Utils import UTILS_Utilisateurs
from Utils.UTILS_Decimal import FloatToDecimal as FloatToDecimal

from Utils import UTILS_Config
SYMBOLE = UTILS_Config.GetParametre("monnaie_symbole", "�")


from Utils import UTILS_Interface
from Ctrl.CTRL_ObjectListView import FastObjectListView, ColumnDefn, Filter, CTRL_Outils, PanelAvecFooter


def DateEngFr(textDate):
    text = str(textDate[8:10]) + "/" + str(textDate[5:7]) + "/" + str(textDate[:4])
    return text

def DateComplete(dateDD):
    """ Transforme une date DD en date compl�te : Ex : lundi 15 janvier 2008 """
    listeJours = (_("Lundi"), _("Mardi"), _("Mercredi"), _("Jeudi"), _("Vendredi"), _("Samedi"), _("Dimanche"))
    listeMois = (_("janvier"), _("f�vrier"), _("mars"), _("avril"), _("mai"), _("juin"), _("juillet"), _("ao�t"), _("septembre"), _("octobre"), _("novembre"), _("d�cembre"))
    dateComplete = listeJours[dateDD.weekday()] + " " + str(dateDD.day) + " " + listeMois[dateDD.month-1] + " " + str(dateDD.year)
    return dateComplete

def DateEngEnDateDD(dateEng):
    if not isinstance(dateEng,str): dateEng = str(dateEng)
    return datetime.date(int(dateEng[:4]), int(dateEng[5:7]), int(dateEng[8:10]))

# ----------------------------------------------------------------------------------------------------------------------------------------

def Importation(onlyNonVentiles=True, IDcompte_payeur=None):
    DB = GestionDB.DB()
    
    if IDcompte_payeur != None :
        conditionCompte = "WHERE IDcompte_payeur=%d" % IDcompte_payeur
    else:
        conditionCompte = ""
    
    # R�cup�re les comptes payeurs
    req = """SELECT IDcompte_payeur, IDfamille
    FROM comptes_payeurs
    %s
    ORDER BY IDcompte_payeur
    ;""" % conditionCompte
    DB.ExecuterReq(req,MsgBox="ExecuterReq")
    listeComptes = DB.ResultatReq()

    # M�morise les IDfamille
    listeIDfamille = [IDfamille for temp, IDfamille in listeComptes]
    
    # R�cup�re la ventilation
    req = """SELECT IDcompte_payeur, SUM(montant) AS total_ventilations
    FROM ventilation
    %s
    GROUP BY IDcompte_payeur
    ORDER BY IDcompte_payeur
    ;""" % conditionCompte
    DB.ExecuterReq(req,MsgBox="ExecuterReq")
    listeVentilations = DB.ResultatReq()
    dictVentilations = {}
    for IDcompte_payeur, total_ventilations in listeVentilations :
        dictVentilations[IDcompte_payeur] = total_ventilations
    
    # R�cup�re les prestations
    req = """SELECT IDcompte_payeur, SUM(montant) AS total_prestations
    FROM prestations
    %s
    GROUP BY IDcompte_payeur
    ORDER BY IDcompte_payeur
    ;""" % conditionCompte
    DB.ExecuterReq(req,MsgBox="ExecuterReq")
    listePrestations = DB.ResultatReq()
    dictPrestations = {}
    for IDcompte_payeur, total_prestations in listePrestations :
        dictPrestations[IDcompte_payeur] = total_prestations
        
    # R�cup�re les r�glements
    req = """SELECT IDcompte_payeur, SUM(montant) AS total_reglements
    FROM reglements
    %s
    GROUP BY IDcompte_payeur
    ORDER BY IDcompte_payeur
    ;""" % conditionCompte
    DB.ExecuterReq(req,MsgBox="ExecuterReq")
    listeReglements = DB.ResultatReq()
    dictReglements = {}
    for IDcompte_payeur, total_reglements in listeReglements :
        dictReglements[IDcompte_payeur] = total_reglements
    
    DB.Close()
    
    # R�cup�ration des titulaires de familles
    dictTitulaires = UTILS_Titulaires.GetTitulaires(listeIDfamille=listeIDfamille)
    
    # Traitement des donn�es
    listeListeView = []
    for IDcompte_payeur, IDfamille in listeComptes :
        if IDcompte_payeur in dictVentilations :
            total_ventilations = FloatToDecimal(dictVentilations[IDcompte_payeur])
        else:
            total_ventilations = FloatToDecimal(0.0)
        if IDcompte_payeur in dictPrestations :
            total_prestations = FloatToDecimal(dictPrestations[IDcompte_payeur])
        else:
            total_prestations = FloatToDecimal(0.0)
        if IDcompte_payeur in dictReglements :
            total_reglements = FloatToDecimal(dictReglements[IDcompte_payeur])
        else:
            total_reglements = FloatToDecimal(0.0)
        item = (IDcompte_payeur, IDfamille, total_ventilations, total_reglements, total_prestations)
        track = Track(dictTitulaires, item)

        if onlyNonVentiles == True :
            # Afficher seulement ceux qui sont mal ventil�s
            if track.reste_a_ventiler > FloatToDecimal(0.0) :
                listeListeView.append(track)
        else:
            # Afficher toute la liste
            listeListeView.append(track)

    return listeListeView
                
                
class Track(object):
    def __init__(self, dictTitulaires, donnees):
        self.IDcompte_payeur = donnees[0]
        self.IDfamille = donnees[1]
        self.total_ventilations = donnees[2]
        self.total_reglements = donnees[3]
        self.total_prestations = donnees[4]
        if self.IDfamille in dictTitulaires :
            self.nomsTitulaires =  dictTitulaires[self.IDfamille]["titulairesSansCivilite"]
        else:
            self.nomsTitulaires = _("Sans titulaires")
        
        self.solde = self.total_reglements - self.total_prestations
        self.total_a_ventiler = min(self.total_reglements, self.total_prestations)
        self.reste_a_ventiler = self.total_a_ventiler - self.total_ventilations

# ----------------------------------------------------------------------------------------------------------------------------------------

def VentilationAuto(IDcompte_payeur=None, IDreglement=None):
    """ Ventilation auto de tous les r�glements d'un compte payeur ou d'un r�glement sp�cifique """
    DB = GestionDB.DB()

    if IDreglement != None :
        conditionReglement = "AND IDreglement=%d" % IDreglement
    else :
        conditionReglement = ""

    # R�cup�re la ventilation
    req = """SELECT IDventilation, IDreglement, IDprestation, montant
    FROM ventilation
    WHERE IDcompte_payeur=%d;""" % IDcompte_payeur
    DB.ExecuterReq(req,MsgBox="ExecuterReq")
    listeDonnees = DB.ResultatReq()
    dictVentilations = {}
    dictVentilationsReglement = {}
    dictVentilationsPrestation = {}
    for IDventilation, IDreglement, IDprestation, montant in listeDonnees :
        dictVentilations[IDventilation] = {"IDreglement" : IDreglement, "IDprestation" : IDprestation, "montant" : FloatToDecimal(montant)}
        
        if (IDreglement in dictVentilationsReglement) == False :
            dictVentilationsReglement[IDreglement] = []
        dictVentilationsReglement[IDreglement].append(IDventilation)

        if (IDprestation in dictVentilationsPrestation) == False :
            dictVentilationsPrestation[IDprestation] = []
        dictVentilationsPrestation[IDprestation].append(IDventilation)
    
    # R�cup�re les prestations
    req = """SELECT IDprestation, date, montant
    FROM prestations
    WHERE IDcompte_payeur=%d
    ORDER BY date;""" % IDcompte_payeur
    DB.ExecuterReq(req,MsgBox="ExecuterReq")
    listeDonnees = DB.ResultatReq()
    listePrestations = []
    for IDprestation, date, montant in listeDonnees :
        listePrestations.append({"IDprestation" : IDprestation, "date" : date, "montant" : FloatToDecimal(montant)})

    # V�rifie qu'il n'y a pas de prestations n�gatives
    for dictPrestation in listePrestations : 
        IDprestation = dictPrestation["IDprestation"]
                        
        montantVentilation = FloatToDecimal(0.0)
        if IDprestation in dictVentilationsPrestation :
            for IDventilation in dictVentilationsPrestation[IDprestation] :
                montantVentilation += dictVentilations[IDventilation]["montant"]
        
        ResteAVentiler = dictPrestation["montant"] - montantVentilation
        if ResteAVentiler < FloatToDecimal(0.0) :
            dlg = wx.MessageDialog(None, _("Ventilation automatique impossible !\n\nLa ventilation automatique n'est pas compatible avec les prestations comportant un montant n�gatif ! Vous devez donc effectuer une ventilation manuelle."), _("Information"), wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            DB.Close()
            return False

    # R�cup�re les r�glements
    req = """SELECT IDreglement, date, montant
    FROM reglements
    WHERE IDcompte_payeur=%d %s
    ORDER BY date;""" % (IDcompte_payeur, conditionReglement)
    DB.ExecuterReq(req,MsgBox="ExecuterReq")
    listeDonnees = DB.ResultatReq()
    listeReglements = []
    for IDreglement, date, montant in listeDonnees :
        listeReglements.append({"IDreglement" : IDreglement, "date" : date, "montant" : FloatToDecimal(montant)})
    
    # V�rification de la ventilation de chaque r�glement
    listeReglementsAVentiler = []
    for dictReglement in listeReglements :
        IDreglement = dictReglement["IDreglement"]
        
        # Recherche s'il reste du cr�dit � ventiler dans ce r�glement
        montantVentilation = FloatToDecimal(0.0)
        if IDreglement in dictVentilationsReglement :
            for IDventilation in dictVentilationsReglement[IDreglement] :
                montantVentilation += dictVentilations[IDventilation]["montant"]
                
        credit = dictReglement["montant"] - montantVentilation
        
        if credit > FloatToDecimal(0.0) :
    
            # Recherche s'il reste des prestations � ventiler pour cette famille
            listePrestationsAVentiler = []
            for dictPrestation in listePrestations : 
                IDprestation = dictPrestation["IDprestation"]
                                
                montantVentilation = FloatToDecimal(0.0)
                if IDprestation in dictVentilationsPrestation :
                    for IDventilation in dictVentilationsPrestation[IDprestation] :
                        montantVentilation += dictVentilations[IDventilation]["montant"]
                
                ResteAVentiler = dictPrestation["montant"] - montantVentilation
                if ResteAVentiler > FloatToDecimal(0.0) :
                    
                    # Calcul du montant qui peut �tre ventil�
                    montant = ResteAVentiler
                    if credit < montant :
                        montant = credit
                    
                    if montant > FloatToDecimal(0.0) :
                        
                        # Modification d'une ventilation existante
                        ventilationTrouvee = False
                        if IDprestation in dictVentilationsPrestation :
                            for IDventilation in dictVentilationsPrestation[IDprestation] :
                                if dictVentilations[IDventilation]["IDreglement"] == IDreglement :
                                    nouveauMontant = montant + montantVentilation
                                    
                                    DB.ReqMAJ("ventilation", [("montant", float(nouveauMontant)),], "IDventilation", IDventilation)
                                    
                                    # M�morisation du nouveau montant
                                    dictVentilations[IDventilation]["montant"] = nouveauMontant
                                    ResteAVentiler -= montant
                                    credit -= montant
                                    ventilationTrouvee = True
                                    
                        
                        # Cr�ation d'une ventilation
                        if ventilationTrouvee == False :
                            listeDonnees = [    
                                    ("IDreglement", IDreglement),
                                    ("IDcompte_payeur", IDcompte_payeur),
                                    ("IDprestation", IDprestation),
                                    ("montant", float(montant)),
                                ]
                            IDventilation = DB.ReqInsert("ventilation", listeDonnees)
                            
                            # M�morisation de la nouvelle ventilation
                            dictVentilations[IDventilation] = {"IDreglement" : IDreglement, "IDprestation" : IDprestation, "montant" : montant}
                            if (IDreglement in dictVentilationsReglement) == False :
                                dictVentilationsReglement[IDreglement] = []
                            dictVentilationsReglement[IDreglement].append(IDventilation)
                            if (IDprestation in dictVentilationsPrestation) == False :
                                dictVentilationsPrestation[IDprestation] = []
                            dictVentilationsPrestation[IDprestation].append(IDventilation)
                            ResteAVentiler -= montant
                            credit -= montant
    
    DB.Close()
    return True
    

# ----------------------------------------------------------------------------------------------------------------------------------------

class ListView(FastObjectListView):
    def __init__(self, *args, **kwds):
        # R�cup�ration des param�tres perso
        self.onlyNonVentiles = kwds.pop("onlyNonVentiles", False)
        self.IDcompte_payeur = kwds.pop("IDcompte_payeur", None)
        self.tracks = kwds.pop("tracks", None)
        self.colonneTri = kwds.pop("colonneTri", None)
        self.sensTri = kwds.pop("sensTri", True)
        self.selectionID = None
        self.selectionTrack = None
        self.criteres = ""
        self.itemSelected = False
        self.popupIndex = -1
        self.listeFiltres = []
        self.donnees = None
        # Initialisation du listCtrl
        self.nom_fichier_liste = __file__
        FastObjectListView.__init__(self, *args, **kwds)
        # Binds perso
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnItemActivated)
        self.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)
        
    def OnItemActivated(self,event):
        self.OuvrirFicheFamille(None)
                
    def InitModel(self):
        """ R�cup�ration des donn�es """
        if self.tracks == None or self.donnees != None :
            self.donnees = Importation(self.onlyNonVentiles, self.IDcompte_payeur)
        else:
            self.donnees = self.tracks

    def InitObjectListView(self):            
        # Couleur en alternance des lignes
        self.oddRowsBackColor = UTILS_Interface.GetValeur("couleur_tres_claire", wx.Colour(240, 251, 237))
        self.evenRowsBackColor = wx.Colour(255, 255, 255)
        self.useExpansionColumn = True
        
        self.imgVentilation = self.AddNamedImages("ventilation", wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Attention.png"), wx.BITMAP_TYPE_PNG))
        
        def GetImageVentilation(track):
            if track.reste_a_ventiler > FloatToDecimal(0.0) :
                return self.imgVentilation

        def FormateMontant(montant):
            if montant == None or montant == 0.0 or montant == FloatToDecimal(0.0) : 
                return ""
            return "%.2f %s" % (montant, SYMBOLE)

        def FormateSolde(montant):
            if montant == None or montant == 0.0 or montant == FloatToDecimal(0.0) : 
                return ""
            if montant >= decimal.Decimal(str("0.0")) :
                return "+ %.2f %s" % (montant, SYMBOLE)
            else:
                return "- %.2f %s" % (-montant, SYMBOLE)

        liste_Colonnes = [
            ColumnDefn(_("IDfamille"), "left", 0, "IDfamille", typeDonnee="entier"),
            ColumnDefn(_("Famille"), 'left', 250, "nomsTitulaires", typeDonnee="texte"),
            ColumnDefn(_("Solde"), 'right', 80, "solde", typeDonnee="montant", stringConverter=FormateSolde),
            ColumnDefn(_("Prestations"), 'right', 80, "total_prestations", typeDonnee="montant", stringConverter=FormateMontant),
            ColumnDefn(_("R�glements"), 'right', 80, "total_reglements", typeDonnee="montant", stringConverter=FormateMontant),
            ColumnDefn(_("Total ventil�"), 'right', 80, "total_ventilations", typeDonnee="montant", stringConverter=FormateMontant),
            ColumnDefn(_("A ventiler"), 'right', 80, "reste_a_ventiler", typeDonnee="montant", stringConverter=FormateMontant, imageGetter=GetImageVentilation),
            ]
        
        self.SetColumns(liste_Colonnes)
        self.CreateCheckStateColumn(0)
        self.SetEmptyListMsg(_("Aucun probl�me de ventilation"))
        self.SetEmptyListMsgFont(wx.FFont(11, wx.DEFAULT, False, "Tekton"))
        if self.colonneTri == None :
            self.SortBy(1, self.sensTri)
        else:
            self.SortBy(self.colonneTri, self.sensTri)
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
        # S�lection d'un item
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

        # Cr�ation du menu contextuel
        menuPop = UTILS_Adaptations.Menu()

        # Item Ouverture fiche famille
        item = wx.MenuItem(menuPop, 10, _("Ouvrir la fiche famille"))
        item.SetBitmap(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Famille.png"), wx.BITMAP_TYPE_PNG))
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.OuvrirFicheFamille, id=10)
        
        menuPop.AppendSeparator()
        
        # Item Ventilation Automatique
        sousMenuVentilation = UTILS_Adaptations.Menu()
        
        item = wx.MenuItem(sousMenuVentilation, 201, _("Uniquement la ligne s�lectionn�e"))
        item.SetBitmap(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Magique.png"), wx.BITMAP_TYPE_PNG))
        sousMenuVentilation.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.VentilationAuto, id=201)
        if noSelection == True : item.Enable(False)

        item = wx.MenuItem(sousMenuVentilation, 202, _("Uniquement les lignes coch�es"))
        item.SetBitmap(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Magique.png"), wx.BITMAP_TYPE_PNG))
        sousMenuVentilation.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.VentilationAuto, id=202)
        if len(self.GetTracksCoches()) == 0 : item.Enable(False)

        item = wx.MenuItem(sousMenuVentilation, 203, _("Toutes les lignes"))
        item.SetBitmap(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Magique.png"), wx.BITMAP_TYPE_PNG))
        sousMenuVentilation.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.VentilationAuto, id=203)

        menuPop.AppendMenu(wx.Window.NewControlId(), _("Ventilation automatique"), sousMenuVentilation)
        
        menuPop.AppendSeparator()

        # Item Tout cocher
        item = wx.MenuItem(menuPop, 70, _("Tout cocher"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Cocher.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.CocheTout, id=70)

        # Item Tout d�cocher
        item = wx.MenuItem(menuPop, 80, _("Tout d�cocher"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Decocher.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.CocheRien, id=80)

        menuPop.AppendSeparator()

        # Item Apercu avant impression
        item = wx.MenuItem(menuPop, 40, _("Aper�u avant impression"))
        item.SetBitmap(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Apercu.png"), wx.BITMAP_TYPE_PNG))
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.Apercu, id=40)
        
        # Item Imprimer
        item = wx.MenuItem(menuPop, 50, _("Imprimer"))
        item.SetBitmap(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Imprimante.png"), wx.BITMAP_TYPE_PNG))
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.Imprimer, id=50)
        
        menuPop.AppendSeparator()
    
        # Item Export Texte
        item = wx.MenuItem(menuPop, 600, _("Exporter au format Texte"))
        item.SetBitmap(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Texte2.png"), wx.BITMAP_TYPE_PNG))
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.ExportTexte, id=600)
        
        # Item Export Excel
        item = wx.MenuItem(menuPop, 700, _("Exporter au format Excel"))
        item.SetBitmap(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Excel.png"), wx.BITMAP_TYPE_PNG))
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.ExportExcel, id=700)

        self.PopupMenu(menuPop)
        menuPop.Destroy()

    def Apercu(self, event):
        from Utils import UTILS_Printer
        prt = UTILS_Printer.ObjectListViewPrinter(self, titre=_("Liste des soldes"), format="A", orientation=wx.PORTRAIT)
        prt.Preview()

    def Imprimer(self, event):
        from Utils import UTILS_Printer
        prt = UTILS_Printer.ObjectListViewPrinter(self, titre=_("Liste des soldes"), format="A", orientation=wx.PORTRAIT)
        prt.Print()

    def OuvrirFicheFamille(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("familles_fiche", "consulter") == False : return
        if len(self.Selection()) == 0 :
            dlg = wx.MessageDialog(self, _("Vous n'avez s�lectionn� aucune fiche famille � ouvrir !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        IDfamille = self.Selection()[0].IDfamille
        from Dlg import DLG_Famille
        dlg = DLG_Famille.Dialog(self, IDfamille)
        if dlg.ShowModal() == wx.ID_OK:
            pass
        dlg.Destroy()
        self.MAJ(IDfamille)

    def ExportTexte(self, event):
        from Utils import UTILS_Export
        UTILS_Export.ExportTexte(self, titre=_("Liste des soldes"), autoriseSelections=False)
        
    def ExportExcel(self, event):
        from Utils import UTILS_Export
        UTILS_Export.ExportExcel(self, titre=_("Liste des soldes"), autoriseSelections=False)

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

    def VentilationAuto(self, event=None, action=None):
        if action != None:
            ID = action
        else:
            ID = event.GetId()
        if ID == 201 :
            # Uniquement la ligne s�lectionn�e
            if len(self.Selection()) == 0 :
                dlg = wx.MessageDialog(self, _("Vous n'avez s�lectionn� aucune ligne !"), _("Erreur"), wx.OK | wx.ICON_EXCLAMATION)
                dlg.ShowModal()
                dlg.Destroy()
                return
            track = self.Selection()[0]
            VentilationAuto(IDcompte_payeur=track.IDcompte_payeur)
            self.MAJ(track.IDfamille)
        if ID == 202 :
            # Uniquement les lignes coch�es
            listeTracks = self.GetTracksCoches()
            if len(listeTracks) == 0 :
                dlg = wx.MessageDialog(self, _("Vous n'avez coch� aucune ligne !"), _("Erreur"), wx.OK | wx.ICON_EXCLAMATION)
                dlg.ShowModal()
                dlg.Destroy()
                return
            for track in listeTracks :
                VentilationAuto(IDcompte_payeur=track.IDcompte_payeur)
            self.MAJ()
        # Toutes les lignes
        if ID == 203 :
            if len(self.donnees) == 0 :
                dlg = wx.MessageDialog(self, _("La liste est vide !"), _("Erreur"), wx.OK | wx.ICON_EXCLAMATION)
                dlg.ShowModal()
                dlg.Destroy()
                return
            for track in self.donnees :
                VentilationAuto(IDcompte_payeur=track.IDcompte_payeur)
            self.MAJ()

# -------------------------------------------------------------------------------------------------------------------------------------------

class BarreRecherche(wx.SearchCtrl):
    def __init__(self, parent):
        wx.SearchCtrl.__init__(self, parent, size=(-1, -1), style=wx.TE_PROCESS_ENTER)
        self.parent = parent
        self.rechercheEnCours = False
        
        self.SetDescriptiveText(_("Rechercher une famille..."))
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



class ListviewAvecFooter(PanelAvecFooter):
    def __init__(self, parent, kwargs={}):
        dictColonnes = {
            "nomsTitulaires" : {"mode" : "nombre", "singulier" : "famille", "pluriel" : "familles", "alignement" : wx.ALIGN_CENTER},
            "solde" : {"mode" : "total"},
            "total_prestations" : {"mode" : "total"},
            "total_reglements" : {"mode" : "total"},
            "total_ventilations" : {"mode" : "total"},
            "reste_a_ventiler" : {"mode" : "total"},
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
        self.myOlv = ListView(panel, tracks=None, onlyNonVentiles=True, IDcompte_payeur=None, id=-1, name="OL_test", style=wx.LC_REPORT|wx.SUNKEN_BORDER|wx.LC_SINGLE_SEL|wx.LC_HRULES|wx.LC_VRULES)
        self.myOlv.MAJ() 
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_2.Add(self.myOlv, 1, wx.ALL|wx.EXPAND, 4)
        panel.SetSizer(sizer_2)
        self.Layout()
        self.SetSize((800, 400))

if __name__ == '__main__':
    app = wx.App(0)
    #wx.InitAllImageHandlers()
    frame_1 = MyFrame(None, -1, "OL TEST")
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()
