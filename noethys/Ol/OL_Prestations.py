#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, modifié pour supprimer les pièces, appellé par DLG_Famille_prestations
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS, JB
# Copyright:       (c) 2010-11 Ivan LUCAS, JB
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------


from Utils.UTILS_Traduction import _
import Chemins
import wx
import GestionDB as GestionDB
from Gest import GestionInscription
import datetime
import copy

from Utils import UTILS_Config

SYMBOLE = UTILS_Config.GetParametre("monnaie_symbole", "€")
from Utils import UTILS_Utilisateurs

from Utils.UTILS_Decimal import FloatToDecimal as FloatToDecimal

from Ctrl.CTRL_ObjectListView import ObjectListView, ColumnDefn, Filter, CTRL_Outils, PanelAvecFooter

def DateEngFr(textDate):
    if textDate == None: return ""
    textDate = str(textDate)
    text = str(textDate[8:10]) + "/" + str(textDate[5:7]) + "/" + str(textDate[:4])
    return text

def DateComplete(dateDD):
    """ Transforme une date DD en date complète : Ex : lundi 15 janvier 2008 """
    listeJours = (_("Lundi"), _("Mardi"), _("Mercredi"), _("Jeudi"), _("Vendredi"), _("Samedi"), _("Dimanche"))
    listeMois = (_("janv"), _("fév"), _("mars"), _("avr"), _("mai"), _("juin"), _("juil"), _("août"), _("sept"), _("oct"), _("nov"), _("déc"))
    #dateComplete = listeJours[dateDD.weekday()] + " " + str(dateDD.day) + " " + listeMois[dateDD.month-1] + " " + str(dateDD.year)
    dateComplete = str(dateDD.day) + " " + listeMois[dateDD.month-1] + " " + str(dateDD.year)
    return dateComplete

def DateEngEnDateDD(dateEng):
    try:
        dt = datetime.date(int(dateEng[:4]), int(dateEng[5:7]), int(dateEng[8:10]))
    except: dt = datetime.date(1900, 1, 1)
    return dt

# ---------------------------------------- LISTVIEW DATES -----------------------------------------------------------------------

class Track(object):
    def __init__(self, donnees):
        self.IDprestation = donnees["IDprestation"]
        self.IDcompte_payeur = donnees["IDcompte_payeur"]
        self.date = donnees["date"]
        self.categorie = donnees["categorie"]
        self.label = donnees["label"]
        self.montant = donnees["montant"]
        self.IDactivite = donnees["IDactivite"]
        self.nomActivite = donnees["nomActivite"]
        self.nomAbregeActivite = donnees["nomAbregeActivite"]
        self.IDtarif = donnees["IDtarif"]
        self.nomTarif = donnees["nomTarif"]
        self.nomCategorieTarif = donnees["nomCategorieTarif"]
        self.IDfacture = donnees["IDfacture"]
        self.compta = donnees["compta"]
        if self.IDfacture == None :
            self.label_facture = ""
        else:
            num_facture = donnees["num_facture"]
            date_facture = donnees["date_facture"]
            if num_facture != None :
                if type(num_facture) == int :
                    num_facture = str(num_facture)
                self.label_facture = "n°%s" % num_facture
            else :
                self.label_facture = ""
        self.IDfamille = donnees["IDfamille"]
        self.IDindividu = donnees["IDindividu"]
        self.nomIndividu = donnees["nomIndividu"]
        self.prenomIndividu = donnees["prenomIndividu"]
        if self.prenomIndividu != None :
            self.nomCompletIndividu = "%s %s" % (self.nomIndividu, self.prenomIndividu)
        else :
            self.nomCompletIndividu = self.nomIndividu
        self.montant_ventilation = donnees["montant_ventilation"]
        self.montant_deduction = donnees["montant_deduction"]
        self.nbre_deductions = donnees["nbre_deductions"]
        self.forfait = donnees["forfait"]
        self.reglement_frais = donnees["reglement_frais"]

class ListView(ObjectListView):
    def __init__(self, *args, **kwds):
        # Initialisation du listCtrl

        self.IDfamille = kwds.pop("IDfamille", None)
        self.selectionID = None
        self.selectionTrack = None
##        locale.setlocale(locale.LC_ALL, 'FR')
        ObjectListView.__init__(self, *args, **kwds)
        self.listePeriodes = []
        self.listeIndividus = []
        self.listeActivites = []
        self.listeFactures = []
        self.total = 0.0
        self.dictFiltres = {}
        self.pointe = None
        # Binds perso
        self.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)

    def InitModel(self):
        self.donnees = self.GetTracks()

    def GetSQLdates(self, listePeriodes=[]):
        texteSQL = ""
        for date_debut, date_fin in listePeriodes :
            texteSQL += "(prestations.date>='%s' AND prestations.date<='%s') OR " % (date_debut, date_fin)
        if len(texteSQL) > 0 :
            texteSQL = "  (" + texteSQL[:-4] + ")"
        else:
            texteSQL = ""
        return texteSQL

    def GetListePrestations(self, IDfamille=None, listeComptesPayeurs=[]):
        DB = GestionDB.DB()
        
        # Condition Famille
        if IDfamille == None or IDfamille == 0 :
            conditionFamille = "IDfamille>0"
        else:
            conditionFamille = "IDfamille=%d" % IDfamille
        
        # Condition PERIODES
        conditions = self.GetSQLdates(self.listePeriodes)
        if len(conditions) > 0 :
            conditionDates = " AND %s" % conditions
        else:
            conditionDates = ""
        
        # Condition COMPTES PAYEURS
        if len(listeComptesPayeurs) == 0 : conditionComptes = "AND prestations.IDcompte_payeur > 0"
        elif len(listeComptesPayeurs) == 1 : conditionComptes = "AND prestations.IDcompte_payeur IN (%d)" % listeComptesPayeurs[0]
        else : conditionComptes = "AND prestations.IDcompte_payeur IN %s" % str(tuple(listeComptesPayeurs))
        
        # Filtres de l'utilisateur
        filtreSQL = self.GetFiltres() 
        
        req = """
        SELECT prestations.IDprestation, prestations.IDcompte_payeur, prestations.date, categorie,
        prestations.label, prestations.montant, 
        prestations.IDactivite, activites.nom, activites.abrege,
        prestations.IDtarif, noms_tarifs.nom, categories_tarifs.nom, prestations.IDfacture, factures.numero, factures.date_edition,
        prestations.forfait, prestations.IDcategorie_tarif,IDfamille, prestations.IDindividu,
        individus.nom, individus.prenom, SUM(deductions.montant) AS montant_deduction,
        COUNT(deductions.IDdeduction) AS nbre_deductions, reglement_frais,prestations.compta
        FROM prestations
        LEFT JOIN activites ON prestations.IDactivite = activites.IDactivite
        LEFT JOIN individus ON prestations.IDindividu = individus.IDindividu
        LEFT JOIN tarifs ON prestations.IDtarif = tarifs.IDtarif
        LEFT JOIN noms_tarifs ON tarifs.IDnom_tarif = noms_tarifs.IDnom_tarif
        LEFT JOIN categories_tarifs ON prestations.IDcategorie_tarif = categories_tarifs.IDcategorie_tarif
        LEFT JOIN deductions ON deductions.IDprestation = prestations.IDprestation
        LEFT JOIN factures ON prestations.IDfacture = factures.IDfacture
        WHERE %s %s %s %s
        GROUP BY prestations.IDprestation
        ORDER BY prestations.date
        ;""" % (conditionFamille, conditionComptes, conditionDates, filtreSQL)
        DB.ExecuterReq(req,MsgBox="OL_Prestations")
        listeDonnees = DB.ResultatReq()

        req = """
        SELECT ventilation.IDprestation, SUM(ventilation.montant) AS montant_ventilation
        FROM ventilation
        LEFT JOIN prestations ON prestations.IDprestation = ventilation.IDprestation
        LEFT JOIN activites ON prestations.IDactivite = activites.IDactivite
        LEFT JOIN individus ON prestations.IDindividu = individus.IDindividu
        LEFT JOIN tarifs ON prestations.IDtarif = tarifs.IDtarif
        LEFT JOIN noms_tarifs ON tarifs.IDnom_tarif = noms_tarifs.IDnom_tarif
        LEFT JOIN categories_tarifs ON prestations.IDcategorie_tarif = categories_tarifs.IDcategorie_tarif
        LEFT JOIN factures ON prestations.IDfacture = factures.IDfacture
        WHERE %s %s %s %s
        GROUP BY ventilation.IDprestation
        ;""" % (conditionFamille, conditionComptes, conditionDates, filtreSQL)
        DB.ExecuterReq(req,MsgBox="OL_Prestations")
        listeVentilation = DB.ResultatReq() 
        dictVentilation = {}
        for IDprestation, montantVentilation in listeVentilation :
            dictVentilation[IDprestation] = montantVentilation
        DB.Close() 
        
        listePrestations = []
        listeIndividus = []
        listeActivites = []
        listeFactures = []
        total = 0.0
        for IDprestation, IDcompte_payeur, date, categorie, label, montant, IDactivite, nomActivite, nomAbregeActivite, IDtarif, nomTarif, nomCategorieTarif, IDfacture, num_facture, date_facture, forfait, IDcategorie_tarif, IDfamille, IDindividu, nomIndividu, prenomIndividu, montant_deduction, nbre_deductions, reglement_frais, compta in listeDonnees :
            date = DateEngEnDateDD(date)  
            if IDprestation in dictVentilation :
                montant_ventilation = FloatToDecimal(dictVentilation[IDprestation])
            else :
                montant_ventilation = FloatToDecimal(0.0)
            if montant == None :
                montant = 0.0 
                
            dictTemp = {
                "IDprestation" : IDprestation,  "IDcompte_payeur" : IDcompte_payeur, "date" : date, "categorie" : categorie,
                "label" : label, "montant" : FloatToDecimal(montant), "IDactivite" : IDactivite, "nomActivite" : nomActivite, "nomAbregeActivite" : nomAbregeActivite, "IDtarif" : IDtarif, "nomTarif" : nomTarif, 
                "nomCategorieTarif" : nomCategorieTarif, "IDfacture" : IDfacture, "num_facture" : num_facture, "date_facture" : date_facture, "forfait" : forfait,
                "IDfamille" : IDfamille, "IDindividu" : IDindividu, "nomIndividu" : nomIndividu, "prenomIndividu" : prenomIndividu,
                "montant_ventilation" : FloatToDecimal(montant_ventilation), "montant_deduction" : FloatToDecimal(montant_deduction), 
                "nbre_deductions" : nbre_deductions, "reglement_frais" : reglement_frais,"compta":compta
                }
            listePrestations.append(dictTemp)
            
            # Mémorisation des individus
            if IDindividu != None and prenomIndividu != None and (prenomIndividu, IDindividu) not in listeIndividus :
                listeIndividus.append((prenomIndividu, IDindividu))
            
            # Mémorisation des activités
            if IDactivite != None and nomActivite != None and (nomActivite, IDactivite) not in listeActivites :
                listeActivites.append((nomActivite, IDactivite))
                
            # Mémorisation des factures
            if IDfacture != None and ("N° %d" % IDfacture, IDfacture) not in listeFactures :
                listeFactures.append(("N° %d" % IDfacture, IDfacture))
            
            # Mémorisation du total des prestations affichées
            total += montant
        return listePrestations, listeIndividus, listeActivites, listeFactures, total
        #fin GetListePrestations

    def GetTracks(self):
        # Récupération des données
        listeID = None
        listeDonnees, self.listeIndividus, self.listeActivites, self.listeFactures, self.total = self.GetListePrestations(IDfamille=self.IDfamille) 
    
        listeListeView = []
        for item in listeDonnees :
            valide = True
            if listeID != None :
                if item[0] not in listeID :
                    valide = False            
            if valide == True :
                track = Track(item)
                listeListeView.append(track)
                if self.selectionID == item["IDprestation"] :
                    self.selectionTrack = track
        return listeListeView

    def InitObjectListView(self):
        # ImageList
        self.imgVert = self.AddNamedImages("vert", wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Ventilation_vert.png"), wx.BITMAP_TYPE_PNG))
        self.imgRouge = self.AddNamedImages("rouge", wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Ventilation_rouge.png"), wx.BITMAP_TYPE_PNG))
        self.imgOrange = self.AddNamedImages("orange", wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Ventilation_orange.png"), wx.BITMAP_TYPE_PNG))

        def GetImageVentilation(track):
            if track.montant == track.montant_ventilation :
                return self.imgVert
            if track.montant_ventilation == FloatToDecimal(0.0) or track.montant_ventilation == None :
                return self.imgRouge
            if track.montant_ventilation < track.montant :
                return self.imgOrange
            return self.imgRouge

        def FormateDate(dateDD):
            return DateComplete(dateDD)

        def FormateMontant(montant):
            if montant == None or montant == "" : return ""
            return "%.2f %s" % (montant, SYMBOLE)
                   
        def rowFormatter(listItem, track):
            if track.valide == False :
                listItem.SetTextColour(wx.Colour(150, 150, 150))
                
        # Couleur en alternance des lignes
        self.oddRowsBackColor = wx.Colour(255, 255, 255) #"#EEF4FB" # Bleu
        self.evenRowsBackColor = "#F0FBED" # Vert
        
        # Paramètres ListView
        self.useExpansionColumn = True
        
        if self.IDfamille != None :
            listeColonnes = ["case","IDprestation", "categorie_prestation", "date", "prenom_individu", "nom_activite", "label", "montant", "regle", "categorie_tarif", "num_facture","compta"]
        else :
            listeColonnes = ["case","IDprestation", "categorie_prestation", "date", "nom_complet_individu", "nom_activite", "label", "montant", "regle", "categorie_tarif", "num_facture","compta"]
        
        dictColonnes = {
            "case" : ColumnDefn("", "left", 10, "case", typeDonnee="entier"),
            "IDprestation" : ColumnDefn("ID", "left", 50, "IDprestation", typeDonnee="entier"),
            "date" : ColumnDefn(_("Date"), "left", 80, "date", typeDonnee="date", stringConverter=FormateDate),
            "categorie_prestation" : ColumnDefn(_("Catégorie"), "left", 70, "categorie", typeDonnee="texte"),
            "prenom_individu" : ColumnDefn(_("Individu"), "left", 100, "prenomIndividu", typeDonnee="texte"),
            "nom_complet_individu" : ColumnDefn(_("Individu"), "left", 100, "nomCompletIndividu", typeDonnee="texte"),
            "nom_activite" : ColumnDefn(_("Activité"), "left", 70, "nomAbregeActivite", typeDonnee="texte"),
            "label" : ColumnDefn(_("Label"), "left", 250, "label", typeDonnee="texte"),
            "montant" : ColumnDefn(_("Montant"), "right", 65, "montant", typeDonnee="montant", stringConverter=FormateMontant),
            "regle" : ColumnDefn(_("Réglé"), "right", 75, "montant_ventilation", typeDonnee="montant", stringConverter=FormateMontant, imageGetter=GetImageVentilation),
            "deductions" : ColumnDefn(_("Déduc."), "right", 55, "montant_deduction", typeDonnee="montant", stringConverter=FormateMontant),
            "nom_tarif" : ColumnDefn(_("Tarif"), "left", 140, "nomTarif", typeDonnee="texte"),
            "categorie_tarif" : ColumnDefn(_("Catégorie de tarif"), "left", 100, "nomCategorieTarif", typeDonnee="texte"),
            "num_facture" : ColumnDefn(_("N° Facture"), "left", 70, "label_facture", typeDonnee="texte"),
            "compta" : ColumnDefn(_("Compta"), "right", 60, "compta", typeDonnee="entier"),
        }
        
        self.SetColumns([dictColonnes[code] for code in listeColonnes])
        
##        self.SetShowGroups(False)
        self.CreateCheckStateColumn(0)
        #self.SetShowItemCounts(False)
        self.SetSortColumn(self.columns[2])
        self.SetEmptyListMsg(_("Aucune prestation"))
        self.SetEmptyListMsgFont(wx.FFont(11, wx.DEFAULT, faceName="Tekton"))
##        self.rowFormatter = rowFormatter
        self.SetObjects(self.donnees)
    
    def GetListeIndividus(self):
        return self.listeIndividus
    
    def GetListeActivites(self):
        return self.listeActivites
    
    def GetListeFactures(self):
        return self.listeFactures
    
    def GetTotal(self):
        return self.total 
    
    def GetTitresColonnes(self):
        listeColonnes = []
        for index in range(0, self.GetColumnCount()) :
            listeColonnes.append(self.columns[index].title)
        return listeColonnes
    
    def SetColonneTri(self, indexColonne=1):
##        self.SetAlwaysGroupByColumn(indexColonne)
        self.MAJ()
        self.SetAlwaysGroupByColumn(indexColonne+1)
##        self.SetSortColumn(self.columns[indexColonne-1], resortNow=True)
    
    def GetFiltres(self):
        filtreSQL = ""
        for champFiltre, valeur in self.dictFiltres.items() :
            if "COMPLEXE" in champFiltre and valeur != None :
                filtreSQL += " AND %s" % valeur
            else :
                if valeur != None :
                    filtreSQL += " AND %s = %s" % (champFiltre, valeur)
        return filtreSQL
        
    def SetFiltre(self, champFiltre, valeur):
        self.dictFiltres[champFiltre] = valeur
        self.MAJ() 
        
    def SetListePeriodes(self, listePeriodes=[]):
        if listePeriodes == None :
            self.listePeriodes = []
        else:
            self.listePeriodes = listePeriodes
        self.MAJ() 
        
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
        # MAJ du total du panel
        try :
            if self.GetParent().GetName() == "panel_prestations" :
                self.GetParent().MAJtotal()
        except :
            pass
        self.Refresh()
    
    def Selection(self):
        return self.GetSelectedObjects()
    
    def OnContextMenu(self, event):
        """Ouverture du menu contextuel """
        if len(self.Selection()) > 0 :
            ID = self.Selection()[0].IDprestation
        
        # Création du menu contextuel
        menuPop = wx.Menu()

        # Item Ajouter
        if self.IDfamille != None :
            item = wx.MenuItem(menuPop, 10, _("Ajouter"))
            bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Ajouter.png"), wx.BITMAP_TYPE_PNG)
            item.SetBitmap(bmp)
            menuPop.Append(item)
            self.Bind(wx.EVT_MENU, self.Ajouter, id=10)

        # Item Modifier
        item = wx.MenuItem(menuPop, 20, _("Modifier"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Modifier.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.Modifier, id=20)
        if len(self.Selection()) == 0 : item.Enable(False)

        # Item Supprimer
        item = wx.MenuItem(menuPop, 30, _("Supprimer"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Supprimer.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.Supprimer, id=30)
        if len(self.Selection()) == 0 : item.Enable(False)
        
        menuPop.AppendSeparator()

        # Item Tout cocher
        item = wx.MenuItem(menuPop, 70, _("Tout cocher"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Cocher.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.CocheTout, id=70)

        # Item Tout décocher
        item = wx.MenuItem(menuPop, 80, _("Tout décocher"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Decocher.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.CocheRien, id=80)

        menuPop.AppendSeparator()

        # Item Apercu avant impression
        item = wx.MenuItem(menuPop, 40, _("Aperçu avant impression"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Apercu.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.Apercu, id=40)
        
        # Item Imprimer
        item = wx.MenuItem(menuPop, 50, _("Imprimer"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Imprimante.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.Imprimer, id=50)
        
        menuPop.AppendSeparator()
    
        # Item Export Texte
        item = wx.MenuItem(menuPop, 600, _("Exporter au format Texte"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Texte2.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.ExportTexte, id=600)
        
        # Item Export Excel
        item = wx.MenuItem(menuPop, 700, _("Exporter au format Excel"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Excel.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.ExportExcel, id=700)

        self.PopupMenu(menuPop)
        menuPop.Destroy()

    def Apercu(self, event):
        from Utils import UTILS_Printer
        prt = UTILS_Printer.ObjectListViewPrinter(self, titre=_("Liste des prestations"), format="A", orientation=wx.PORTRAIT)
        prt.Preview()

    def Imprimer(self, event):
        from Utils import UTILS_Printer
        prt = UTILS_Printer.ObjectListViewPrinter(self, titre=_("Liste des prestations"), format="A", orientation=wx.PORTRAIT)
        prt.Print()

    def ExportTexte(self, event):
        from Utils import UTILS_Export
        UTILS_Export.ExportTexte(self, titre=_("Liste des prestations"))
        
    def ExportExcel(self, event):
        from Utils import UTILS_Export
        UTILS_Export.ExportExcel(self, titre=_("Liste des prestations"))

    def Ajouter(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("familles_prestations", "creer") == False : return
        from Dlg import DLG_Saisie_prestation
        dlg = DLG_Saisie_prestation.Dialog(self, IDprestation=None, IDfamille=self.IDfamille)
        if dlg.ShowModal() == wx.ID_OK:
            IDprestation = dlg.GetIDprestation()
            self.MAJ(IDprestation)
        dlg.Destroy()

    def Validation(self,track, mode="modif"):
        if mode == "modif":
            verbe = "modifier"
            impossible = "Modification impossible"
        else:
            verbe = "supprimer"
            impossible = "Suppression impossible"
        if track.categorie == "import":
            dlg = wx.MessageDialog(self, _("Cette prestation est antérieure. Il est donc impossible de la %s."%verbe),
                                   impossible, wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return

        # Vérifie le transfert en compta
        if track.compta != None:
            date = GestionInscription.DateIntToString(track.compta, format="%d/%m/%Y")
            dlg = wx.MessageDialog(self, _(
                "La prestation :\n'%s'\n a été transférée en compta le %s.\n\nVous ne pouvez donc pas la %s !"% (
                                   track.label, date, verbe)), impossible, wx.OK | wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return

        if track.IDfacture != None:
            dlg = wx.MessageDialog(self, _(
                "Cette prestation apparaît sur une facture. Il est donc impossible de la %s sans la rétrograder."%(verbe)),
                                   impossible, wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return

        if track.categorie == "consommation":
            dlg = wx.MessageDialog(self, _(
                "Pour %s la prestation d'une consommation, allez directement dans la gestion de l'inscription !"%verbe),
                                   _("Information"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        return track

    def Modifier(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("familles_prestations", "modifier") == False : return
        if len(self.Selection()) == 0 :
            dlg = wx.MessageDialog(self, _("Vous n'avez sélectionné aucune prestation dans la liste"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        mode = "modif"
        track = self.Validation(self.Selection()[0],mode)
        if not track :
            mode = "visu"
            track = self.Selection()[0]

        from Dlg import DLG_Saisie_prestation
        dlg = DLG_Saisie_prestation.Dialog(self, IDprestation=track.IDprestation, IDfamille=track.IDfamille, mode=mode)
        if dlg.ShowModal() == wx.ID_OK:
            self.MAJ()
        dlg.Destroy()

    def Dupliquer(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("familles_prestations", "dupliquer") == False : return
        if len(self.Selection()) == 0 :
            dlg = wx.MessageDialog(self, _("Vous n'avez sélectionné aucune prestation à dupliquer dans la liste !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        IDprestation = self.Selection()[0].IDprestation
        if self.Selection()[0].categorie.lower().startswith("conso"):
            mess = "A gérer par la facturation\n\n"
            mess += "Les consommations gérées par les inscriptions ou la famille ne sont pas duplicables"
            wx.MessageBox(mess,"Duplication impossible")
            return
        # Charge les noms des champs
        from Data import DATA_Tables
        dicoDB = DATA_Tables.DB_DATA
        lstChamps = []
        for descr in dicoDB["prestations"]:
            lstChamps.append(descr[0])
        # rappelle le prestation pour avoir toute les données dans l'ordre des champs
        DB = GestionDB.DB()
        req = """SELECT * FROM prestations
        WHERE IDprestation=%d;
        """ % IDprestation
        DB.ExecuterReq(req)
        recordset = DB.ResultatReq()
        # reprise des valeurs mais pas tous les champs
        for record in recordset:
            lstDonnees = []
            i = 0
            for valeur in record :
                if i != 0:
                    if lstChamps[i] == "IDfacture": valeur = None
                    if lstChamps[i] == "compta": valeur = None
                    if lstChamps[i] == "date": valeur = str(datetime.date.today())
                    lstDonnees.append((lstChamps[i],valeur))
                i += 1
        newID = DB.ReqInsert("prestations",lstDonnees,commit = True,retourID=True,MsgBox = "Insertion de prestation par dupliquer")
        DB.Close()
        # MAJ de l'affichage
        self.MAJ()
        selection = [x for x in self.innerList if x.IDprestation == newID]
        # Chaîne sur une modif et vérifie un changement
        if len(selection) >=1:
            self.SelectObjects(selection)
            flag = (selection[0].label,selection[0].date)
            self.Modifier(None)
            obj = self.Selection()[0]
            if flag == (obj.label,obj.date):
                mess = "Risque de doublon!\n\n"
                mess += "La duplication n'a pas été suivie d'une modification de date ou d'intitulé."
                wx.MessageBox(mess,"Remarque non bloquante")
        #fin Dupliquer

    def Supprimer(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("familles_prestations", "supprimer") == False : return
        if len(self.Selection()) > 0 and len(self.GetTracksCoches()) == 0:
            for obj in self.Selection():
                self.SetCheckState(obj,True)
        if len(self.GetTracksCoches()) == 0 :
            dlg = wx.MessageDialog(self, _("Vous n'avez sélectionné aucune prestation à supprimer dans la liste !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return

        imp, noimp,nbimp,nbnoimp = False,False,0,0
        for track in self.GetTracksCoches():
            track = self.Validation(self.Selection()[0], "suppr")
            if not track: return
            nbnoimp += 1
        verbe = 'supprimer %d' %(nbnoimp)

        if len(self.GetTracksCoches()) > 1 :
            # Suppression multiple
            texte = _("Souhaitez-vous vraiment " + verbe +  " prestations cochées ?")
        else:
            texte = _("Souhaitez-vous vraiment " + verbe +  " prestation cochée ?")

        dlg = wx.MessageDialog(self, texte, _("Suppression"), wx.YES_NO|wx.NO_DEFAULT|wx.CANCEL|wx.ICON_INFORMATION)
        reponse = dlg.ShowModal()
        dlg.Destroy()
        if reponse != wx.ID_YES :
            return

        nePlusDemanderConfirmation = False
        listeSuppressions = []
        DB = GestionDB.DB()
        for track in self.GetTracksCoches() :
            valide = True
            if track.categorie == "import":
                # compensation
                trackOD = copy.deepcopy(track)
                trackOD.categorie = "importOD"
                trackOD.label = "annul "+track.label
                trackOD.montant = -track.montant
                trackOD.date = datetime.date.today()
                listeDonnees = [
                        ("IDcompte_payeur", trackOD.IDcompte_payeur),
                        ("date", trackOD.date),
                        ("categorie", trackOD.categorie),
                        ("label", trackOD.label),
                        ("montant_initial", float(trackOD.montant)),
                        ("montant", float(trackOD.montant)),
                        ("IDactivite", trackOD.IDactivite),
                        ("IDtarif", trackOD.IDtarif),
                        ("IDfamille", trackOD.IDfamille),
                        ("IDindividu", trackOD.IDindividu),
                        ("IDcategorie_tarif", trackOD.IDtarif),]
                trackOD.IDprestation =  DB.ReqInsert("prestations", listeDonnees)
                valide = False

            # Vérifie le transfert en compta
            if valide == True and track.compta != None :
                date = GestionInscription.DateIntToString(track.compta,format="%d/%m/%Y")
                dlg = wx.MessageDialog(self, _("La prestation :\n'%s'\n a été transférée en compta le %s.\n\nVous ne pouvez donc pas la supprimer !") % (track.label, date), _("Suppression impossible"), wx.OK | wx.ICON_INFORMATION)
                dlg.ShowModal()
                dlg.Destroy()
                valide = False

            # Vérifie qu'aucune facture n'y est rattachée
            if valide == True and track.IDfacture != None :
                req = """ SELECT * FROM factures WHERE IDfacture = %d ; """ % track.IDfacture
                DB.ExecuterReq(req,MsgBox = True)
                retour = DB.ResultatReq()
                if len(retour) >0:
                    if retour[0][0]!= None:
                        dlg = wx.MessageDialog(self, _("La prestation n°%d apparaît déjà sur la facture %s.\n\nVous ne pouvez donc pas la supprimer !") % (track.IDprestation, track.label_facture), _("Suppression impossible"), wx.OK | wx.ICON_INFORMATION)
                        dlg.ShowModal()
                        dlg.Destroy()
                        valide = False
            # Recherche la piece associée
            if valide == True:
                req = """ SELECT * FROM matPieces WHERE pieIDprestation = %d ; """ % track.IDprestation
                DB.ExecuterReq(req,MsgBox = True)
                retour = DB.ResultatReq()
                if len(retour) >0:
                    if retour[0][0]!= None:
                        ret = []
                        fGest = GestionInscription.Forfaits(self)
                        # Ne gère que les prestations niveau famille
                        if track.IDactivite == 0:
                            ret = fGest.GetPieceModif999(self,track.IDcompte_payeur, None, IDnumPiece = retour[0][0])
                            if len(ret) == 0: ret = fGest.GetPieceModif999(self,track.IDcompte_payeur, None, IDnumPiece = track.IDcontrat )
                        if len(ret) > 0:
                            for piece in ret:
                                dictDonnees = piece
                                suppressible = fGest.PieceModifiable(self,dictDonnees)
                                if not suppressible :
                                    GestionDB.MessageBox(self, "Piece associée bloquée, ne peut pas être supprimée!\nElle est consultable et peut faire l'objet d'un avoir")
                                    return
                                fGest.Suppression(self,dictDonnees)
                            self.MAJ()
             # Recherche si des consommations y sont attachées
            req = """
            SELECT IDconso, date, consommations.etat, consommations.IDunite, unites.nom, 
            consommations.IDindividu, individus.nom, individus.prenom
            FROM consommations
            LEFT JOIN unites ON unites.IDunite = consommations.IDunite
            LEFT JOIN individus ON individus.IDindividu = consommations.IDindividu
            WHERE IDprestation=%d
            ORDER BY date
            ;""" % track.IDprestation
            DB.ExecuterReq(req,MsgBox="OL_Prestations")
            listeConsommations = DB.ResultatReq() 
            listeIDconso = []
            nbreVerrouillees = 0
            
            if len(listeConsommations) > 0 and valide == True :
                lignesConso = []
                for IDconso, date, etat, IDunite, nomUnite, IDindividu, nomIndividu, prenomIndividu in listeConsommations :
                    listeIDconso.append(IDconso)
                    if etat == "present" :
                        nbreVerrouillees += 1
                    dateDD = DateEngEnDateDD(date)
                    dateFr = DateComplete(dateDD)
                    if IDindividu == 0 or IDindividu == None :
                        individu = ""
                    else:
                        individu = _("pour %s %s") % (nomIndividu, prenomIndividu)
                    ligneTexte = _("   - Le %s : %s %s\n") % (dateFr, nomUnite, individu)
                    #message += ligneTexte
                    lignesConso.append(ligneTexte)
                
                detail = ""
                maxAffichage = 20
                if len(lignesConso) > maxAffichage :
                    detail += "".join(lignesConso[:maxAffichage]) + _("   - Et %d autres consommations...\n") % (len(lignesConso) - maxAffichage)
                else :
                    detail += "".join(lignesConso)

                introduction = _("Attention, la prestation n°%d est rattachée aux %d consommation(s) suivantes :") % (track.IDprestation, len(listeConsommations))
                conclusion = _("Souhaitez-vous supprimer également ces consommations (conseillé) ?\n\n(Si vous répondez non, les consommations seront conservées dans le calendrier mais seront considérées comme gratuites)")

                # Demande confirmation pour supprimer les consommations associées
                if nePlusDemanderConfirmation == False :
                    from Dlg import DLG_Messagebox
                    dlg = DLG_Messagebox.Dialog(self, titre=_("Avertissement"), introduction=introduction, detail=detail, conclusion=conclusion, icone=wx.ICON_EXCLAMATION, boutons=[_("Oui"), _("Oui pour tout"), _("Non"), _("Annuler")], defaut=0)
                    reponse = dlg.ShowModal() 
                    dlg.Destroy() 
                else :
                    reponse = 0
                    
                if reponse == 0 or reponse == 1 or nePlusDemanderConfirmation == True :
                    if nbreVerrouillees > 0 :
                        # Annule la procédure d'annulation si des consommations sont déjà pointées sur 'présent' :
                        dlg = wx.MessageDialog(self, _("La prestation %d est rattachée à %d consommation(s) déjà pointées.\nIl vous est donc impossible de le(s) supprimer !\n\nProcédure de suppression annulée.") % (track.IDprestation, nbreVerrouillees), _("Suppression impossible"), wx.OK | wx.ICON_EXCLAMATION)
                        dlg.ShowModal()
                        dlg.Destroy()
                        valide = False
                    else :
                        # Suppression des consommations associées
                        for IDconso in listeIDconso :
                            DB.ReqDEL("consommations", "IDconso", IDconso)
                            
                    if reponse == 1 :
                        nePlusDemanderConfirmation = True

                if reponse == 2 :
                    # Supprime la référence à la prestation des consommations
                    for IDconso in listeIDconso :
                        listeDonnees = [("IDprestation", None),]
                        DB.ReqMAJ("consommations", listeDonnees, "IDconso", IDconso)

                if reponse == 3 :
                    return

            # Recherche s'il s'agit d'une prestation de frais de gestion pour un règlement
            if valide == True and track.reglement_frais != None :
                dlg = wx.MessageDialog(self, _("La prestation n°%d est rattachée au règlement n°%d en tant que frais de gestion de règlement.\n\nSouhaitez-vous vraiment supprimer cette prestation ?") % (track.IDprestation, track.reglement_frais), _("Avertissement"), wx.YES_NO|wx.NO_DEFAULT|wx.CANCEL|wx.ICON_QUESTION)
                reponse = dlg.ShowModal() 
                dlg.Destroy()
                if reponse != wx.ID_YES :
                    valide = False
            
            # Suppression de la prestation
            if valide == True :
                DB.ReqDEL("prestations", "IDprestation", track.IDprestation)
                DB.ReqDEL("ventilation", "IDprestation", track.IDprestation)
                DB.ReqDEL("deductions", "IDprestation", track.IDprestation)
                listeSuppressions.append(track)
            
            # MAJ du listeView
            self.MAJ()

        DB.Close() 
 
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

    def OuvrirFicheFamille(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("familles_fiche", "consulter") == False : return
        if len(self.Selection()) == 0 :
            dlg = wx.MessageDialog(self, _("Vous n'avez sélectionné aucune fiche famille à ouvrir !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        track = self.Selection()[0]
        from Dlg import DLG_Famille
        dlg = DLG_Famille.Dialog(self, track.IDfamille)
        if dlg.ShowModal() == wx.ID_OK:
            self.MAJ(track.IDfacture)
        dlg.Destroy()

# -------------------------------------------------------------------------------------------------------------------------------------------

class BarreRecherche(wx.SearchCtrl):
    def __init__(self, parent):
        wx.SearchCtrl.__init__(self, parent, size=(-1, -1), style=wx.TE_PROCESS_ENTER)
        self.parent = parent
        self.rechercheEnCours = False
        
        self.SetDescriptiveText(_("Rechercher..."))
        self.ShowSearchButton(True)
        
        self.listView = self.parent.ctrl_listview
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
            "date" : {"mode" : "nombre", "singulier" : _("prestation"), "pluriel" : _("prestations"), "alignement" : wx.ALIGN_CENTER},
            "montant" : {"mode" : "total"},
            "montant_ventilation" : {"mode" : "total"},
            "montant_deduction" : {"mode" : "total"},
            }

        PanelAvecFooter.__init__(self, parent, ListView, kwargs, dictColonnes)


# ----------------- FRAME DE TEST ----------------------------------------------------------------

class MyFrame(wx.Frame):
    def __init__(self, footer,*args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self, -1)
        sizer_frame = wx.BoxSizer(wx.VERTICAL)
        sizer_frame.Add(panel, 1, wx.ALL|wx.EXPAND)
        self.SetSizer(sizer_frame)
        sizer_panel = wx.BoxSizer(wx.VERTICAL)
        if footer == "sans":
            # sans footer ni outils de recherche
            self.myOlv = ListView(panel, -1, IDfamille=281, style=wx.LC_REPORT|wx.SUNKEN_BORDER)
            self.myOlv.MAJ()
            sizer_panel.Add(self.myOlv, 1, wx.ALL|wx.EXPAND, 4)
        elif footer == "footer":
            self.myOlv = ListviewAvecFooter(panel, kwargs={"IDfamille": 272})
            self.myOlv.ctrl_listview.MAJ()
            sizer_panel.Add(self.myOlv, 1, wx.ALL | wx.EXPAND, 4)
        elif footer == "outils":
            self.myOlv = ListView(panel, -1, IDfamille=281, style=wx.LC_REPORT|wx.SUNKEN_BORDER)
            self.myOlv.MAJ()
            #spécifique pour outils de recherche
            self.ctrl_recherche = CTRL_Outils(panel, listview=self.myOlv.GetListview(), afficherCocher=True)
            self.ctrl_recherche.SetBackgroundColour((255, 255, 255))
            ###
            sizer_panel.Add(self.myOlv, 1, wx.ALL|wx.EXPAND, 4)
            sizer_panel.Add(self.ctrl_recherche, 0, wx.ALL | wx.EXPAND, 4)
        else:
            self.myOlv = ListviewAvecFooter(panel, kwargs={"IDfamille": 272})
            self.myOlv.ctrl_listview.MAJ()
            self.ctrl_recherche = CTRL_Outils(panel, listview=self.myOlv.GetListview(), afficherCocher=True)
            self.ctrl_recherche.SetBackgroundColour((255, 255, 255))
            sizer_panel.Add(self.myOlv, 1, wx.ALL|wx.EXPAND, 4)
            sizer_panel.Add(self.ctrl_recherche, 0, wx.ALL | wx.EXPAND, 4)
        panel.SetSizer(sizer_panel)
        self.SetSize((900, 400))
        self.Layout()

if __name__ == '__main__':
    app = wx.App(0)
    frame_1 = MyFrame("zzoutils",None, -1, "ObjectListView")
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()
