#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, dérive de OL_Prestations pour détail des lignes de facturation
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS, JB
# Copyright:       (c) 2010-11 Ivan LUCAS, JB
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------

from Utils.UTILS_Traduction import _
import Chemins
import wx
import GestionDB 
from Gest import GestionInscription
import datetime
import copy

from Utils import UTILS_Config

SYMBOLE = UTILS_Config.GetParametre("monnaie_symbole", "€")
from Utils import UTILS_Utilisateurs

from Utils.UTILS_Decimal import FloatToDecimal as FloatToDecimal

from Ctrl.CTRL_ObjectListView import GroupListView, ColumnDefn, Filter, CTRL_Outils, PanelAvecFooter


def dateDDenSQL(dateDD):
    if not isinstance(dateDD,datetime.date): return ""
    return dateDD.strftime("%Y-%m-%d")

def Transport(xxx_todo_changeme):
    (aller,retour) = xxx_todo_changeme
    prix = 0.00
    if aller != None: prix += aller
    if retour != None: prix += retour
    return prix

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

def DateCourte(dateDD):
    """ Transforme une date DD en date courte : Ex : 01/01/2018 """
    dateComplete =  ('00' +str(dateDD.day))[-2:] + "/" + ('00'+str(dateDD.month))[-2:] + "/" + str(dateDD.year)
    return dateComplete

def DateEngEnDateDD(dateEng):
    if dateEng and not isinstance(dateEng,str): dateEng = str(dateEng)
    return datetime.date(int(dateEng[:4]), int(dateEng[5:7]), int(dateEng[8:10]))


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
        if self.IDfacture == None :
            self.label_facture = ""
        else:
            num_facture = donnees["num_facture"]
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
        self.montant_detail = donnees["montant_detail"]
        self.forfait = donnees["forfait"]
        self.reglement_frais = donnees["reglement_frais"]
        
                                
class ListView(GroupListView):
    def __init__(self, *args, **kwds):
        # Initialisation du listCtrl

        self.IDfamille = kwds.pop("IDfamille", None)
        self.selectionID = None
        self.selectionTrack = None
        GroupListView.__init__(self, *args, **kwds)

        self.periode = (None)
        self.dictFiltres = {'periode': None,'whereActivites': "FALSE",
                            'Options': {'avecDetail':False,
                                        'niveauFamille':False,
                                        'horsConsos':True}}
        self.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)
        self.SetShowGroups(False)

    def GetSQLdates(self, periode):
        debSQL = dateDDenSQL(periode[0])
        finSQL = dateDDenSQL(periode[1])
        return "(prestations.date BETWEEN '%s' AND '%s')" % (debSQL, finSQL)

    def GetWhereNiveauFamille(self):
        return "(prestations.IDactivite = 0)"

    def GetWhereHorsConsos(self):
        return "(NOT 'conso' in prestations.categorie)"

    def GetWhere(self):
        filtreSQL = """
           %s\nAND  ( """ % (self.GetSQLdates(self.dictFiltres['periode']))

        if not 'FALSE' in self.dictFiltres['whereActivites']:
            filtreSQL += "%s \n     OR "%self.dictFiltres['whereActivites']

        if self.dictFiltres['options']['niveauFamille']:
            filtreSQL += "%s \n     OR " % self.GetWhereNiveauFamille()

        if self.dictFiltres['options']['horsConsos']:
            filtreSQL += "%s \n     OR " % self.GetWhereHorsConsos()
        if filtreSQL[-3:] == "OR ":
            filtreSQL = filtreSQL[:-3]
        else: filtreSQL = "( FALSE "
        filtreSQL += ")"
        return filtreSQL

    def GetListePrestations(self, ):
        DB = GestionDB.DB()
        
        # Filtres de l'utilisateur
        filtreSQL = ''
        filtre = self.GetWhere()

        if len(filtre) >1 : filtreSQL = 'WHERE '+ filtre
        # Appel des prestations
        req = """
        SELECT prestations.IDprestation, prestations.IDcompte_payeur, prestations.date, categorie,
        prestations.label, prestations.montant,
        prestations.IDactivite, activites.nom, activites.abrege,
        categories_tarifs.nom, prestations.IDfacture, factures.numero, factures.date_edition,
        prestations.forfait, prestations.IDcategorie_tarif,
        IDfamille, prestations.IDindividu,
        individus.nom, individus.prenom,
        0 AS montant_detail,
        reglement_frais
        FROM prestations
        LEFT JOIN matPieces ON prestations.IDcontrat = matPieces.pieIDnumPiece
        LEFT JOIN activites ON prestations.IDactivite = activites.IDactivite
        LEFT JOIN individus ON prestations.IDindividu = individus.IDindividu
        LEFT JOIN categories_tarifs ON prestations.IDcategorie_tarif = categories_tarifs.IDcategorie_tarif
        LEFT JOIN factures ON prestations.IDfacture = factures.IDfacture
        %s
        ORDER BY prestations.date
        ;""" % (filtreSQL)

        DB.ExecuterReq(req,MsgBox="OL_Liste_prestations.famillesA")
        listeDonnees = DB.ResultatReq()
        dictFamilles = {}
        dictVentilation = {}
        listeDetail = []
        if len(listeDonnees) > 0:
            serieIDprestations = "(  "
            serieIDfamilles = "(  "
            for item in listeDonnees:
                serieIDprestations += (str(item[0])+ ", ")
                serieIDfamilles += (str(item[1])+ ", ")
            serieIDprestations = serieIDprestations[:-2]+" )"
            serieIDfamilles = serieIDfamilles[:-2]+" )"

            # Appel des noms de familles
            req = """
                    SELECT rattachements.IDfamille, Min(individus.nom), Min(individus.prenom)
                    FROM rattachements LEFT JOIN individus ON rattachements.IDindividu = individus.IDindividu
                    WHERE (rattachements.titulaire = 1) AND (rattachements.IDfamille in %s )
                    GROUP BY rattachements.IDfamille;
                    """ % serieIDfamilles
            DB.ExecuterReq(req,MsgBox="OL_Liste_prestations.famillesB")
            recordset = DB.ResultatReq()
            for IDfamille, nom, prenom in recordset:
                dictFamilles[IDfamille]= (nom,prenom)

            req = """
            SELECT ventilation.IDprestation, SUM(ventilation.montant) AS montant_ventilation
            FROM ventilation
            LEFT JOIN prestations ON prestations.IDprestation = ventilation.IDprestation
            LEFT JOIN activites ON prestations.IDactivite = activites.IDactivite
            LEFT JOIN individus ON prestations.IDindividu = individus.IDindividu
            LEFT JOIN categories_tarifs ON prestations.IDcategorie_tarif = categories_tarifs.IDcategorie_tarif
            LEFT JOIN factures ON prestations.IDfacture = factures.IDfacture
            WHERE ventilation.IDprestation in %s
            GROUP BY ventilation.IDprestation
            ;""" % (serieIDprestations)
            DB.ExecuterReq(req,MsgBox="OL_Liste_prestations")
            listeVentilation = DB.ResultatReq()
            for IDprestation, montantVentilation in listeVentilation :
                dictVentilation[IDprestation] = montantVentilation

            #Recherche du détail des lignes prestations dans les pièces
            req = """
            SELECT matPieces.pieIDprestation, matPiecesLignes.ligIDnumLigne, matPieces.pieDateCreation, matPieces.pieNature, matPieces.pieIDfamille,
                    individus.nom, individus.prenom, activites.abrege, matPlanComptable.pctLibelle, matArticles.artLibelle, matPiecesLignes.ligMontant,
                    matPieces.pieNoFacture, matPieces.piePrixTranspAller, matPieces.piePrixTranspRetour
            FROM matPieces
            LEFT JOIN matPiecesLignes ON matPieces.pieIDnumPiece = matPiecesLignes.ligIDnumPiece
            LEFT JOIN activites ON matPieces.pieIDactivite = activites.IDactivite
            LEFT JOIN individus ON matPieces.pieIDindividu = individus.IDindividu
            LEFT JOIN (matArticles
                        LEFT JOIN matPlanComptable ON matArticles.artCodeComptable = matPlanComptable.pctCodeComptable)
                    ON matPiecesLignes.ligCodeArticle = matArticles.artCodeArticle
            WHERE  matPieces.pieIDprestation IN %s
            ;""" %  serieIDprestations
            DB.ExecuterReq(req,MsgBox="OL_Liste_prestations.pieces")
            listeDetail = DB.ResultatReq()
            DB.Close()

        listePrestations = []
        numLigne = 0
        IDprestationOld = 0
        if self.dictFiltres['options'][0]:
            # composition de la liste à partir du détail
            #   pieIDprestation,IDnumLigne,DateCreation,Nature, IDfamille,  nom,  prenom, pctLibelle, artLibelle, Montant, NoFacture, prixTranspAller, prixTranspRetour
            for IDprestation,IDnumLigne, date, categorie, IDfamille, nomIndividu, prenomIndividu,nomAbregeActivite,nomCategorieTarif,label,montant_detail,num_facture, prixTranspAller, prixTranspRetour in listeDetail :
                if IDprestation != IDprestationOld:
                    numLigne=0
                    IDprestationOld = IDprestation
                numLigne += 1
                date = DateEngEnDateDD(date)
                if montant_detail == None :
                    montant_detail = 0.0
                dictTemp = {
                    "IDprestation" : ((IDprestation * 100)+numLigne),  "IDcompte_payeur" : None, "date" : date, "categorie" : categorie,
                    "label" : label, "montant" : FloatToDecimal(0.0), "IDactivite" : None, "nomActivite" : nomAbregeActivite, "nomAbregeActivite" : nomAbregeActivite, "IDtarif" : 0, "nomTarif" : "",
                    "nomCategorieTarif" : nomCategorieTarif, "IDfacture" : 0, "num_facture" : num_facture, "date_facture" : "", "forfait" : "",
                    "IDfamille" : IDfamille, "IDindividu" : 0, "nomIndividu" : nomIndividu, "prenomIndividu" : prenomIndividu,
                    "montant_ventilation" : FloatToDecimal(0.0), "montant_detail" : FloatToDecimal(montant_detail),
                    "reglement_frais" : FloatToDecimal(0.0)
                    }
                if dictTemp["nomIndividu"]== None :
                    dictTemp["nomIndividu"] = dictFamilles[dictTemp["IDfamille"]][0]
                    dictTemp["prenomIndividu"] = dictFamilles[dictTemp["IDfamille"]][1]
                listePrestations.append(dictTemp)
                #ajout d'une ligne transport avant l'insertin
                prixTransp = Transport((prixTranspAller,prixTranspRetour))
                if prixTransp != 0.0 and numLigne == 1 :
                    dictTransp = copy.deepcopy(dictTemp)
                    numLigne += 1
                    libelle = 'transport de ' + prenomIndividu
                    dictTransp["IDprestation"] = (IDprestation * 100)
                    dictTransp["nomCategorieTarif"] = "Transport"
                    dictTransp["label"] = libelle
                    dictTransp["montant_detail"] =  FloatToDecimal(prixTransp)
                    listePrestations.append(dictTransp)
        return listePrestations
        # fin GetListePrestations

    def GetTracks(self):
        # Récupération des données prestations
        listeID = None
        listeDonnees = self.GetListePrestations()

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
            return DateCourte(dateDD)

        def FormateMontant(montant):
            if montant == None or montant == "" : return ""
            if int(montant) == 0 : return ""
            return "%.2f " % (montant )
                   
        def FormateDetail(montant):
            if montant == None or montant == "" : return "T  "
            if int(montant) == 0 : return "T  "
            return "%.2f " % (montant)

        def rowFormatter(listItem, track):
            if track.valide == False :
                listItem.SetTextColour(wx.Colour(150, 150, 150))
                
        # Couleur en alternance des lignes
        self.oddRowsBackColor = wx.Colour(255, 255, 255) #"#EEF4FB" # Bleu
        self.evenRowsBackColor = "#F0FBED" # Vert
        
        # Paramètres ListView
        self.useExpansionColumn = True
        
        if self.IDfamille != None :
            listeColonnes = ["IDprestation", "date","categorie_prestation","IDfamille", "prenom_individu", "nom_activite", "label", "montant", "regle", "detail", "categorie_tarif", "num_facture"]
        else :
            listeColonnes = ["IDprestation", "date","categorie_prestation","IDfamille", "nom_complet_individu", "nom_activite", "label", "montant", "regle", "detail", "categorie_tarif", "num_facture"]
        
        dictColonnes = {
            "IDprestation" : ColumnDefn("", "left", 0, "IDprestation", typeDonnee="entier"),
            "date" : ColumnDefn(_("Date"), "left", 80, "date", typeDonnee="date", stringConverter=FormateDate),
            "categorie_prestation" : ColumnDefn(_("Catégorie"), "left", 70, "categorie", typeDonnee="texte"),
            "IDfamille" : ColumnDefn("Fam", "right", 50, "IDfamille", typeDonnee="entier"),
            "prenom_individu" : ColumnDefn(_("Prenom"), "left", 75, "prenomIndividu", typeDonnee="texte"),
            "nom_complet_individu" : ColumnDefn(_("Nom "), "left", 150, "nomCompletIndividu", typeDonnee="texte"),
            "nom_activite" : ColumnDefn(_("Activité"), "left", 70, "nomAbregeActivite", typeDonnee="texte"),
            "label" : ColumnDefn(_("Label"), "left", 155, "label", typeDonnee="texte"),
            "montant" : ColumnDefn(_("Montant"), "right", 65, "montant", typeDonnee="montant", stringConverter=FormateMontant),
            "regle" : ColumnDefn(_("Réglé"), "right", 72, "montant_ventilation", typeDonnee="montant", stringConverter=FormateMontant, imageGetter=GetImageVentilation),
            "detail" : ColumnDefn(_("Détail"), "right", 55, "montant_detail", typeDonnee="montant", stringConverter=FormateDetail),
            "nom_tarif" : ColumnDefn(_("Tarif"), "left", 140, "nomTarif", typeDonnee="texte"),
            "categorie_tarif" : ColumnDefn(_("Type de ligne"), "left", 100, "nomCategorieTarif", typeDonnee="texte"),
            "num_facture" : ColumnDefn(_("N° Facture"), "left", 70, "label_facture", typeDonnee="texte"),
        }
        
        self.SetColumns([dictColonnes[code] for code in listeColonnes])
        
##        self.SetShowGroups(False)
        self.CreateCheckStateColumn(0)
        self.SetShowItemCounts(False)
        self.SetSortColumn(self.columns[0])
        self.SetEmptyListMsg(_("Aucune prestation"))
        self.SetEmptyListMsgFont(wx.FFont(11, wx.DEFAULT, faceName="Tekton"))
##        self.rowFormatter = rowFormatter
        self.SetObjects(self.donnees)

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

    def MAJ(self, ID=None):
        if ID != None :
            self.selectionID = ID
            self.selectionTrack = None
        else:
            self.selectionID = None
            self.selectionTrack = None
        self.donnees = self.GetTracks()
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
            "montant_detail" : {"mode" : "total"},
            }

        PanelAvecFooter.__init__(self, parent, ListView, kwargs, dictColonnes)


# ----------------- FRAME DE TEST ----------------------------------------------------------------

class MyFrame(wx.Frame):
    def __init__(self, footer,*args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self, -1)
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_1.Add(panel, 1, wx.ALL|wx.EXPAND)
        self.SetSizer(sizer_1)
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        #import time
        #t = time.time()
        if footer == "sans":
            self.myOlv = ListView(panel, -1, IDfamille=281, style=wx.LC_REPORT|wx.SUNKEN_BORDER)
            self.myOlv.MAJ()
            sizer_2.Add(self.myOlv, 1, wx.ALL|wx.EXPAND, 4)
        else:
            self.listviewAvecFooter = ListviewAvecFooter(self, kwargs={"IDfamille" : 272})
            self.ctrl_prestations = self.listviewAvecFooter.GetListview()
            self.ctrl_recherche = CTRL_Outils(self, listview=self.ctrl_prestations, afficherCocher=True)
            self.ctrl_recherche.SetBackgroundColour((255, 255, 255))
            sizer_2.Add(self.listviewAvecFooter, 1, wx.ALL|wx.EXPAND, 4)
        self.SetSizer(sizer_2)
        self.SetSize((900, 400))
        self.Layout()

if __name__ == '__main__':
    app = wx.App(0)
    frame_1 = MyFrame("sans",None, -1, "GroupListView")
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()
