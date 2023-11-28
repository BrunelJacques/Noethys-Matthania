#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, d�rive de OL_Prestations pour d�tail des lignes de facturation
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

SYMBOLE = UTILS_Config.GetParametre("monnaie_symbole", "�")
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
    """ Transforme une date DD en date compl�te : Ex : lundi 15 janvier 2008 """
    listeJours = (_("Lundi"), _("Mardi"), _("Mercredi"), _("Jeudi"), _("Vendredi"), _("Samedi"), _("Dimanche"))
    listeMois = (_("janvier"), _("f�vrier"), _("mars"), _("avril"), _("mai"), _("juin"), _("juillet"), _("ao�t"), _("septembre"), _("octobre"), _("novembre"), _("d�cembre"))
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
                self.label_facture = "n�%s" % num_facture
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
        self.dictFiltres = {'periode': None,'whereActivites': "FALSE",'lignes': None}
        self.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)
        self.SetShowGroups(False)

    def GetSQLdates(self, periode):
        debSQL = dateDDenSQL(periode[0])
        finSQL = dateDDenSQL(periode[1])
        return "(prestations.date BETWEEN '%s' AND '%s')" % (debSQL, finSQL)

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

            #Recherche du d�tail des lignes prestations dans les pi�ces
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
        if "detail" in self.dictFiltres['lignes']:
            # composition de la liste � partir du d�tail
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

        if "total" in self.dictFiltres['lignes']:
            #   IDprestation, IDcompte_payeur, date, categorie,label ,montant, IDactivite, nom,         abrege,             nom,                IDfacture, numero,  date_edition,    forfait, IDcategorie_tarif,IDfamille, IDindividu, nom,         prenom,         montant_detail, reglement_frais
            for IDprestation, IDcompte_payeur, date, categorie, label, montant, IDactivite, nomActivite, nomAbregeActivite, nomCategorieTarif, IDfacture, num_facture, date_facture, forfait, IDcategorie_tarif, IDfamille, IDindividu, nomIndividu, prenomIndividu, montant_detail, reglement_frais in listeDonnees :
                date = DateEngEnDateDD(date)
                if IDprestation in dictVentilation :
                    montant_ventilation = FloatToDecimal(dictVentilation[IDprestation])
                else :
                    montant_ventilation = FloatToDecimal(0.0)
                if montant == None :
                    montant = FloatToDecimal(0.0)

                dictTemp = {
                    "IDprestation" : (IDprestation * 100),  "IDcompte_payeur" : IDcompte_payeur, "date" : date, "categorie" : categorie,
                    "label" : label, "montant" : FloatToDecimal(montant), "IDactivite" : IDactivite, "nomActivite" : nomActivite, "nomAbregeActivite" : nomAbregeActivite, "IDtarif" : 0, "nomTarif" : "",
                    "nomCategorieTarif" : nomCategorieTarif, "IDfacture" : IDfacture, "num_facture" : num_facture, "date_facture" : date_facture, "forfait" : forfait,
                    "IDfamille" : IDfamille, "IDindividu" : IDindividu, "nomIndividu" : nomIndividu, "prenomIndividu" : prenomIndividu,
                    "montant_ventilation" : FloatToDecimal(montant_ventilation), "montant_detail" : FloatToDecimal(montant_detail),
                    "reglement_frais" : reglement_frais,
                    }
                if dictTemp["nomIndividu"]== None :
                    dictTemp["nomIndividu"] = dictFamilles[dictTemp["IDfamille"]][0]
                    dictTemp["prenomIndividu"] = dictFamilles[dictTemp["IDfamille"]][1]
                listePrestations.append(dictTemp)

        return listePrestations
        # fin GetListePrestations

    def GetTracks(self):
        # R�cup�ration des donn�es prestations
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
        
        # Param�tres ListView
        self.useExpansionColumn = True
        
        if self.IDfamille != None :
            listeColonnes = ["IDprestation", "date","categorie_prestation","IDfamille", "prenom_individu", "nom_activite", "label", "montant", "regle", "detail", "categorie_tarif", "num_facture"]
        else :
            listeColonnes = ["IDprestation", "date","categorie_prestation","IDfamille", "nom_complet_individu", "nom_activite", "label", "montant", "regle", "detail", "categorie_tarif", "num_facture"]
        
        dictColonnes = {
            "IDprestation" : ColumnDefn("", "left", 0, "IDprestation", typeDonnee="entier"),
            "date" : ColumnDefn(_("Date"), "left", 80, "date", typeDonnee="date", stringConverter=FormateDate),
            "categorie_prestation" : ColumnDefn(_("Cat�gorie"), "left", 70, "categorie", typeDonnee="texte"),
            "IDfamille" : ColumnDefn("Fam", "right", 50, "IDfamille", typeDonnee="entier"),
            "prenom_individu" : ColumnDefn(_("Prenom"), "left", 75, "prenomIndividu", typeDonnee="texte"),
            "nom_complet_individu" : ColumnDefn(_("Nom "), "left", 150, "nomCompletIndividu", typeDonnee="texte"),
            "nom_activite" : ColumnDefn(_("Activit�"), "left", 70, "nomAbregeActivite", typeDonnee="texte"),
            "label" : ColumnDefn(_("Label"), "left", 155, "label", typeDonnee="texte"),
            "montant" : ColumnDefn(_("Montant"), "right", 65, "montant", typeDonnee="montant", stringConverter=FormateMontant),
            "regle" : ColumnDefn(_("R�gl�"), "right", 72, "montant_ventilation", typeDonnee="montant", stringConverter=FormateMontant, imageGetter=GetImageVentilation),
            "detail" : ColumnDefn(_("D�tail"), "right", 55, "montant_detail", typeDonnee="montant", stringConverter=FormateDetail),
            "nom_tarif" : ColumnDefn(_("Tarif"), "left", 140, "nomTarif", typeDonnee="texte"),
            "categorie_tarif" : ColumnDefn(_("Type de ligne"), "left", 100, "nomCategorieTarif", typeDonnee="texte"),
            "num_facture" : ColumnDefn(_("N� Facture"), "left", 70, "label_facture", typeDonnee="texte"),
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
    
    def GetWhere(self):
        filtreSQL = ""
        if self.dictFiltres['periode']:
            filtreSQL += """
            %s"""%(self.GetSQLdates(self.dictFiltres['periode']))

        if self.dictFiltres['whereActivites']:
            filtreSQL += "\nAND " + self.dictFiltres['whereActivites']
        return filtreSQL

    def GetWhereLignes(self):
        return ""
    
    def MAJ(self, ID=None):
        if ID != None :
            self.selectionID = ID
            self.selectionTrack = None
        else:
            self.selectionID = None
            self.selectionTrack = None
        self.donnees = self.GetTracks()
        self.InitObjectListView()
        # S�lection d'un item
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
        
        # Cr�ation du menu contextuel
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

        # Item Tout d�cocher
        item = wx.MenuItem(menuPop, 80, _("Tout d�cocher"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Decocher.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.CocheRien, id=80)

        menuPop.AppendSeparator()

        # Item Apercu avant impression
        item = wx.MenuItem(menuPop, 40, _("Aper�u avant impression"))
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

    def Modifier(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("familles_prestations", "modifier") == False : return
        if len(self.Selection()) == 0 :
            dlg = wx.MessageDialog(self, _("Vous n'avez s�lectionn� aucune prestation dans la liste"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        track = self.Selection()[0]

        if track.categorie == "import" :
            dlg = wx.MessageDialog(self, _("Cette prestation est ant�rieure. Il est donc impossible de la modifier."), _("Modification impossible"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return

        if track.IDfacture != None :
            dlg = wx.MessageDialog(self, _("Cette prestation appara�t d�j� sur la facture %s. Il est donc impossible de la modifier.") , _("Modification impossible"), wx.OK | wx.ICON_EXCLAMATION)
            reponse = dlg.ShowModal() 
            dlg.Destroy()
            if reponse != wx.ID_YES :
                return
        
        if track.categorie == "cotisation" :
            dlg = wx.MessageDialog(self, _("Pour modifier la prestation d'une cotisation, allez directement dans la liste des cotisations !"), _("Information"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        
        from Dlg import DLG_Saisie_prestation
        dlg = DLG_Saisie_prestation.Dialog(self, IDprestation=track.IDprestation, IDfamille=track.IDfamille)
        if dlg.ShowModal() == wx.ID_OK:
            self.MAJ(track.IDprestation)
        dlg.Destroy()

    def Supprimer(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("familles_prestations", "supprimer") == False : return
        if len(self.Selection()) > 0 and len(self.GetTracksCoches()) == 0:
            for obj in self.Selection():
                self.SetCheckState(obj,True)
        if len(self.GetTracksCoches()) == 0 :
            dlg = wx.MessageDialog(self, _("Vous n'avez s�lectionn� aucune prestation � supprimer dans la liste !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return

        imp, noimp,nbimp,nbnoimp = False,False,0,0
        for track in self.GetTracksCoches():
            if track.categorie == "import":
                imp = True
                nbimp += 1
            else:
                noimp = True
                nbnoimp += 1
        if imp and noimp : verbe = 'supprimer %d et neutraliser %d' %(nbnoimp, nbimp)
        elif imp: verbe = 'neutraliser %d' % nbimp
        elif noimp: verbe = 'supprimer %d' % nbnoimp
        else: verbe = 'None'

        if len(self.GetTracksCoches()) > 1 :
            # Suppression multiple
            texte = _("Souhaitez-vous vraiment " + verbe +  " prestations coch�es ?")
        else:
            texte = _("Souhaitez-vous vraiment " + verbe +  " prestation coch�e ?")

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
                        ("IDindividu", trackOD.IDindividu),]
                trackOD.IDprestation =  DB.ReqInsert("prestations", listeDonnees)
                valide = False

            # V�rifie qu'aucune facture n'y est rattach�e
            if valide == True and track.IDfacture != None :
                req = """ SELECT * FROM factures WHERE IDfacture = %d ; """ % track.IDfacture
                DB.ExecuterReq(req,MsgBox = True)
                retour = DB.ResultatReq()
                if len(retour) >0:
                    if retour[0][0]!= None:
                        dlg = wx.MessageDialog(self, _("La prestation n�%d appara�t d�j� sur la facture %s.\n\nVous ne pouvez donc pas la supprimer !") % (track.IDprestation, track.label_facture), _("Suppression impossible"), wx.OK | wx.ICON_INFORMATION)
                        dlg.ShowModal()
                        dlg.Destroy()
                        valide = False
            # Recherche la piece associ�e
            if valide == True:
                req = """ SELECT * FROM matPieces WHERE pieIDprestation = %d ; """ % track.IDprestation
                DB.ExecuterReq(req,MsgBox = True)
                retour = DB.ResultatReq()
                if len(retour) >0:
                    if retour[0][0]!= None:
                        ret = []
                        fGest = GestionInscription.Forfaits(self)
                        # Ne g�re que les prestations niveau famille
                        if track.IDactivite == 0:
                            ret = fGest.GetPieceModif999(self,track.IDcompte_payeur, None, IDnumPiece = retour[0][0])
                            if len(ret) == 0: ret = fGest.GetPieceModif999(self,track.IDcompte_payeur, None, IDnumPiece = track.IDcontrat )
                        if len(ret) > 0:
                            for piece in ret:
                                dictDonnees = piece
                                suppressible = fGest.PieceModifiable(self,dictDonnees)
                                if not suppressible :
                                    GestionDB.MessageBox(self, "Piece associ�e bloqu�e, ne peut pas �tre supprim�e!\nElle est consultable et peut faire l'objet d'un avoir")
                                    return
                                fGest.Suppression(self,dictDonnees)
                            self.MAJ()
             # Recherche si des consommations y sont attach�es
            req = """
            SELECT IDconso, date, consommations.etat, consommations.IDunite, unites.nom, 
            consommations.IDindividu, individus.nom, individus.prenom
            FROM consommations
            LEFT JOIN unites ON unites.IDunite = consommations.IDunite
            LEFT JOIN individus ON individus.IDindividu = consommations.IDindividu
            WHERE IDprestation=%d
            ORDER BY date
            ;""" % track.IDprestation
            DB.ExecuterReq(req,MsgBox="OL_Liste_prestations")
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
                    dateFr = DateCourte(dateDD)
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

                introduction = _("Attention, la prestation n�%d est rattach�e aux %d consommation(s) suivantes :") % (track.IDprestation, len(listeConsommations))
                conclusion = _("Souhaitez-vous supprimer �galement ces consommations (conseill�) ?\n\n(Si vous r�pondez non, les consommations seront conserv�es dans le calendrier mais seront consid�r�es comme gratuites)")

                # Demande confirmation pour supprimer les consommations associ�es
                if nePlusDemanderConfirmation == False :
                    from Dlg import DLG_Messagebox
                    dlg = DLG_Messagebox.Dialog(self, titre=_("Avertissement"), introduction=introduction, detail=detail, conclusion=conclusion, icone=wx.ICON_EXCLAMATION, boutons=[_("Oui"), _("Oui pour tout"), _("Non"), _("Annuler")], defaut=0)
                    reponse = dlg.ShowModal() 
                    dlg.Destroy() 
                else :
                    reponse = 0
                    
                if reponse == 0 or reponse == 1 or nePlusDemanderConfirmation == True :
                    if nbreVerrouillees > 0 :
                        # Annule la proc�dure d'annulation si des consommations sont d�j� point�es sur 'pr�sent' :
                        dlg = wx.MessageDialog(self, _("La prestation %d est rattach�e � %d consommation(s) d�j� point�es.\nIl vous est donc impossible de le(s) supprimer !\n\nProc�dure de suppression annul�e.") % (track.IDprestation, nbreVerrouillees), _("Suppression impossible"), wx.OK | wx.ICON_EXCLAMATION)
                        dlg.ShowModal()
                        dlg.Destroy()
                        valide = False
                    else :
                        # Suppression des consommations associ�es
                        for IDconso in listeIDconso :
                            DB.ReqDEL("consommations", "IDconso", IDconso)
                            
                    if reponse == 1 :
                        nePlusDemanderConfirmation = True

                if reponse == 2 :
                    # Supprime la r�f�rence � la prestation des consommations
                    for IDconso in listeIDconso :
                        listeDonnees = [("IDprestation", None),]
                        DB.ReqMAJ("consommations", listeDonnees, "IDconso", IDconso)

                if reponse == 3 :
                    return

            # Recherche s'il s'agit d'une prestation de frais de gestion pour un r�glement
            if valide == True and track.reglement_frais != None :
                dlg = wx.MessageDialog(self, _("La prestation n�%d est rattach�e au r�glement n�%d en tant que frais de gestion de r�glement.\n\nSouhaitez-vous vraiment supprimer cette prestation ?") % (track.IDprestation, track.reglement_frais), _("Avertissement"), wx.YES_NO|wx.NO_DEFAULT|wx.CANCEL|wx.ICON_QUESTION)
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
            dlg = wx.MessageDialog(self, _("Vous n'avez s�lectionn� aucune fiche famille � ouvrir !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
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
