#!/usr/bin/env python
# -*- coding: utf8 -*-
#------------------------------------------------------------------------
# Application :    Noethys, dérive de OL_Prestations pour suivi facturation
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS, JB
# Copyright:       (c) 2019-10
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

from Ctrl.CTRL_ObjectListView import GroupListView, ColumnDefn, Filter, CTRL_Outils, PanelAvecFooter

def Nz(valeur):
    if valeur == None:
        valeur = 0
    valeur = float(valeur)
    return valeur

def Transport(xxx_todo_changeme):
    (aller,retour) = xxx_todo_changeme
    prix = 0.00
    if aller != None: prix += aller
    if retour != None: prix += retour
    return prix

def DateEngFr(textDate):
    if not textDate : return ''
    if textDate == '': return ''
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
    if not dateDD: return ''
    if not isinstance(dateDD,datetime.date): return ''
    dateComplete =  ('00' +str(dateDD.day))[-2:] + "/" + ('00'+str(dateDD.month))[-2:] + "/" + str(dateDD.year)
    return dateComplete

def DateEngEnDateDD(dateEng):
    if not dateEng: return ''
    return datetime.date(int(dateEng[:4]), int(dateEng[5:7]), int(dateEng[8:10]))

# ---------------------------------------- LISTVIEW DATES -----------------------------------------------------------------------

class Track(object):
    def __init__(self, donnees):
        for key,donnee in donnees.items():
            if not donnee:
                if key in ('montant'):
                    donnees[key] = 0.0
                else:
                    donnees[key] = ''
        self.IDnumPiece = donnees["IDnumPiece"]
        self.date = donnees["date"]
        self.nature = donnees["nature"]
        self.IDfamille = donnees["IDfamille"]
        self.activite = donnees["activite"]
        self.nomPrenom = donnees["nomPrenom"]
        self.label = donnees["label"]
        self.montant = donnees["montant"]
        if 'noFacture' in donnees:
            self.operateur = donnees["operateur"]
            self.noFacture = donnees["noFacture"]
        self.transfert = donnees["transfert"]

class ListView(GroupListView):
    def __init__(self, *args, **kwds):
        # Initialisation du listCtrl
        self.selectionID = None
        self.selectionTrack = None
        GroupListView.__init__(self, *args, **kwds)
        self.periode = None
        self.transfert = False
        self.dictFiltres = {}
        self.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)
        self.SetShowGroups(False)

    def GetListePrestations(self):
        DB = GestionDB.DB()
        if DB.isNetwork:
            selectif = "IF(activites.abrege Is Null,matPieces.pieIDinscription,activites.abrege)"
        else: selectif = "matPieces.pieIDinscription"
        # Filtres de l'utilisateur
        filtresPoses = self.GetFiltres()
        if len(filtresPoses) >1 : filtresPoses += "\n AND "

        if self.periode:
            (dtDeb,dtFin) = self.periode
            filtrePeriode = """ 
                    (   ( matPieces.pieNature = 'AVO' AND matPieces.pieDateAvoir BETWEEN '%s' AND '%s' )
                        OR  ( matPieces.pieNature = 'FAC' AND matPieces.pieDateFacturation BETWEEN '%s' AND '%s' )
                        OR  ( matPieces.pieNature NOT IN ('FAC','AVO') AND matPieces.pieDateModif BETWEEN '%s' AND '%s' )
                    )\n AND """%(dtDeb,dtFin,dtDeb,dtFin,dtDeb,dtFin)
        else : filtrePeriode = ' False \n AND '

        if self.transfert :
            filtreTransfert = """
                    (   ( matPieces.pieNature = 'AVO' AND matPieces.pieComptaAvo IS NOT NULL)
                        OR  ( matPieces.pieNature <> 'AVO' AND matPieces.pieComptaFac IS NOT NULL )
                    )\n"""
        else:
            filtreTransfert = """
                    (   ( matPieces.pieNature = 'AVO' AND matPieces.pieComptaAvo IS NULL)
                        OR  ( matPieces.pieNature <> 'AVO' AND matPieces.pieComptaFac IS NULL )
                    )\n"""

        filtreSQL = "WHERE %s %s %s "%(filtresPoses,filtrePeriode,filtreTransfert)            
        # Appel des prestations
        if "total" == self.dictFiltres["COMPLEXE"]:
            req = """
                SELECT matPieces.pieIDnumPiece, matPieces.pieDateModif, matPieces.pieDateFacturation, matPieces.pieDateAvoir,
                    matPieces.pieNature,matPieces.pieIDfamille, %s ,individus.nom,individus.prenom, 
                    prestations.label,Sum(matPiecesLignes.ligMontant), Max(matPieces.piePrixTranspAller), 
                    Max(matPieces.piePrixTranspRetour), matPieces.pieNoFacture, matPieces.pieNoAvoir, matPieces.pieComptaFac, 
                    matPieces.pieComptaAvo,matPieces.pieUtilisateurCreateur, matPieces.pieUtilisateurModif
                FROM ((matPieces 
                    LEFT JOIN matPiecesLignes ON matPieces.pieIDnumPiece = matPiecesLignes.ligIDnumPiece) 
                    LEFT JOIN prestations ON matPieces.pieIDprestation = prestations.IDprestation) 
                    LEFT JOIN individus AS individus ON matPieces.pieIDindividu = individus.IDindividu
                    LEFT JOIN activites ON matPieces.pieIDactivite = activites.IDactivite
                %s
                GROUP BY matPieces.pieIDnumPiece, matPieces.pieDateModif, matPieces.pieDateFacturation, matPieces.pieDateAvoir, 
                matPieces.pieNature, matPieces.pieIDfamille, individus.nom, individus.prenom, 
                prestations.label, matPieces.pieNoFacture, matPieces.pieNoAvoir, matPieces.pieComptaFac, matPieces.pieComptaAvo, 
                matPieces.pieUtilisateurCreateur, matPieces.pieUtilisateurModif
                ;""" % (selectif,filtreSQL)

        if "detail" == self.dictFiltres["COMPLEXE"]:
            req = """
                SELECT matPieces.pieIDnumPiece, matPieces.pieDateModif, matPieces.pieDateFacturation, matPieces.pieDateAvoir,
                    matPieces.pieNature, matPieces.pieIDfamille,%s, individus_1.nom, individus_1.prenom,
                    matPiecesLignes.ligLibelle, matPiecesLignes.ligMontant, matPieces.piePrixTranspAller, 
                    matPieces.piePrixTranspRetour, matPieces.pieNoFacture, matPieces.pieNoAvoir, matPieces.pieComptaFac, 
                    matPieces.pieComptaAvo, matPieces.pieUtilisateurCreateur, matPieces.pieUtilisateurModif
                FROM ((matPieces 
                    LEFT JOIN matPiecesLignes ON matPieces.pieIDnumPiece = matPiecesLignes.ligIDnumPiece) 
                    LEFT JOIN individus AS individus_1 ON matPieces.pieIDindividu = individus_1.IDindividu)
                    LEFT JOIN activites ON matPieces.pieIDactivite = activites.IDactivite
                %s
                GROUP BY matPieces.pieIDnumPiece, matPieces.pieDateModif, matPieces.pieDateFacturation, matPieces.pieDateAvoir,
                 matPieces.pieNature, matPieces.pieIDfamille, individus_1.nom, individus_1.prenom,
                  matPiecesLignes.ligLibelle, matPiecesLignes.ligMontant, matPieces.piePrixTranspAller, 
                  matPieces.piePrixTranspRetour, matPieces.pieNoFacture, matPieces.pieNoAvoir, matPieces.pieComptaFac, 
                  matPieces.pieComptaAvo, matPieces.pieUtilisateurCreateur, matPieces.pieUtilisateurModif
                ;"""% (selectif,filtreSQL)

        if "noconso" == self.dictFiltres["COMPLEXE"]:
            if self.periode:
                (dtDeb, dtFin) = self.periode
                filtrePeriode = """ 
                         (   ( prestations.date BETWEEN '%s' AND '%s' )
                         )\n AND """ % (dtDeb, dtFin,)
            else:
                filtrePeriode = ' False \n AND '

            if self.transfert:
                filtreTransfert = """
                         (   prestations.compta IS NOT NULL 
                         )\n"""
            else:
                filtreTransfert = """
                         (   prestations.compta IS NULL
                         )\n"""

            filtreSQL = "WHERE %s %s %s " % (filtresPoses, filtrePeriode, filtreTransfert)
            req = """
                SELECT prestations.IDprestation, prestations.date, prestations.categorie, prestations.IDcompte_payeur,
                 activites.abrege, individus.nom, individus.prenom, prestations.label, prestations.montant, 
                 prestations.IDcontrat, prestations.code_compta, prestations.compta
                FROM prestations 
                    LEFT JOIN individus ON prestations.IDindividu = individus.IDindividu
                    LEFT JOIN activites ON prestations.IDactivite = activites.IDactivite
                %s AND prestations.categorie NOT LIKE 'conso%%'
                GROUP BY prestations.IDprestation, prestations.date, prestations.categorie, prestations.IDcompte_payeur, activites.abrege, individus.nom, individus.prenom, prestations.label, prestations.montant, prestations.IDcontrat, prestations.code_compta, prestations.compta
                ;"""%(filtreSQL) 

        DB.ExecuterReq(req,MsgBox="OL_Liste_facturation.GetListePrestations")
        listeDonnees = DB.ResultatReq()

        listePrestations = []

        # Traitement des données récupérées par la requête SQL
        if self.dictFiltres["COMPLEXE"] in ('total','detail'):
            for IDnumPiece, dateModif, dateFacturation, dateAvoir,nature,IDfamille,activite,nom,prenom, label,\
                    ligMontant, prixTranspAller, prixTranspRetour, noFacture, noAvoir, comptaFac, comptaAvo, createur,\
                    modificateur in listeDonnees :
                if nature == 'FAC':
                    noPiece = noFacture
                    transfert = comptaFac
                elif nature == 'AVO':
                    noPiece = noAvoir
                    transfert = comptaAvo
                else:
                    noPiece = ''
                    transfert = "%s %s"%(DateEngEnDateDD(comptaFac),DateEngEnDateDD(comptaAvo))
                montant = Nz(prixTranspAller) + Nz(prixTranspRetour) + Nz(ligMontant)
                if not nom: nom = ''
                if not prenom: prenom = ''
                nomPrenom = "%s %s"%(prenom,nom)
                if modificateur:
                    if len(modificateur) > 0 : operateur = modificateur
                else: operateur = createur
                if not operateur: operateur = ''
                if not activite: activite = ''
                if not label: label = ''

                dictTemp = {}
                dictTemp["IDnumPiece"] = IDnumPiece
                dictTemp["date"] = dateModif
                dictTemp["nature"] = nature
                dictTemp["IDfamille"] = IDfamille
                dictTemp["activite"] = activite
                dictTemp["nomPrenom"] = nomPrenom
                dictTemp["label"] = label
                dictTemp["montant"] = montant
                dictTemp["operateur"] = operateur
                dictTemp["noFacture"] = noPiece
                dictTemp["transfert"] = transfert
                listePrestations.append(dictTemp)

        if "noconso" == self.dictFiltres["COMPLEXE"]:
            # composition de la liste à partir de la requete
            for IDprestation, date, categorie, IDcompte_payeur,activite, nom, prenom, label, montant, \
                    IDcontrat, code_compta, compta in listeDonnees :
                nomPrenom = "%s %s"%(prenom,nom)
                dictTemp = {}
                dictTemp["IDnumPiece"] = IDprestation
                dictTemp["date"] = date
                dictTemp["nature"] = categorie
                dictTemp["IDfamille"] = IDcompte_payeur
                dictTemp["activite"] = activite
                dictTemp["nomPrenom"] = nomPrenom
                dictTemp["label"] = label
                dictTemp["montant"] = montant
                dictTemp["transfert"] = compta
                listePrestations.append(dictTemp)
        DB.Close()
        return listePrestations
        # fin GetListePrestations

    def GetTracks(self):
        # Récupération des données prestations
        listeListeView = []
        for item in self.GetListePrestations() :
            listeListeView.append(Track(item))
        return listeListeView

    def InitObjectListView(self):
        # ImageList
        self.imgVert = self.AddNamedImages("vert", wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Ventilation_vert.png"), wx.BITMAP_TYPE_PNG))
        self.imgRouge = self.AddNamedImages("rouge", wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Ventilation_rouge.png"), wx.BITMAP_TYPE_PNG))
        self.imgOrange = self.AddNamedImages("orange", wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Ventilation_orange.png"), wx.BITMAP_TYPE_PNG))

        def GetImageVentilation(track):
            if track.nature in ('DEV', 'RES') :
                return self.imgRouge
            elif track.nature in ('FAC', 'AVO'):
                return self.imgVert
            else:
                return self.imgOrange

        def FormateDate(dateDD):
            return DateEngFr(dateDD)

        def FormateMontant(montant):
            if montant == None or montant == "" : return ""
            if int(montant) == 0 : return ""
            return "%.2f " % (montant )
                   
        def rowFormatter(listItem, track):
            if track.valide == False :
                listItem.SetTextColour(wx.Colour(150, 150, 150))
                
        # Couleur en alternance des lignes
        self.oddRowsBackColor = wx.Colour(255, 255, 255) #"#EEF4FB" # Bleu
        self.evenRowsBackColor = "#F0FBED" # Vert
        
        # Paramètres ListView
        self.useExpansionColumn = True

        if self.dictFiltres["COMPLEXE"] in ('total','detail'):
            listeColonnes = ["piece", "date","type","famille", "activite","nomPrenom", "label", "montant", "operateur","noFacture","transfert"]
        else :
            listeColonnes = ["piece", "date","type","famille", "activite","nomPrenom", "label", "montant", "transfert"]

        dictColonnes = {
            "piece" : ColumnDefn("", "left", 0, "IDnumPiece", typeDonnee="entier"),
            "date" : ColumnDefn(_("Date"), "left", 80, "date", typeDonnee="date",stringConverter=FormateDate),
            "type" : ColumnDefn(_("Catégorie"), "left", 70, "nature", typeDonnee="texte", imageGetter=GetImageVentilation),
            "famille" : ColumnDefn("Famille", "right", 50, "IDfamille", typeDonnee="entier"),
            "activite" : ColumnDefn(_("Inscription"), "left", 70, "activite", typeDonnee="texte"),
            "nomPrenom" : ColumnDefn(_("Nom Prénom"), "left", 110, "nomPrenom", typeDonnee="texte"),
            "label" : ColumnDefn(_("Label"), "left", 230, "label", typeDonnee="texte"),
            "montant" : ColumnDefn(_("Montant"), "right", 65, "montant", typeDonnee="montant", stringConverter=FormateMontant),
            "operateur" : ColumnDefn(_("Operateur"), "left", 72, "operateur", typeDonnee="texte"),
            "noFacture" : ColumnDefn(_("N° Facture"), "left", 70, "noFacture", typeDonnee="entier"),
            "transfert": ColumnDefn(_("Transféré"), "left", 100, "transfert", typeDonnee="texte"),
        }
        self.SetColumns([dictColonnes[code] for code in listeColonnes])
        
##        self.SetShowGroups(False)
        self.CreateCheckStateColumn(0)
        self.SetShowItemCounts(False)
        self.SetSortColumn(self.columns[3])
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
    
    def GetFiltres(self):
        filtreSQL = ""
        for champFiltre, valeur in self.dictFiltres.items() :
            if (not "COMPLEXE" in champFiltre) and  (valeur != None) :
                if len(filtreSQL) > 1 : filtreSQL += " AND"
                filtreSQL += "%s" %(valeur)
        return filtreSQL

    def SetListePeriodes(self, periode=None):
        if periode == '' :
            periode = None
        self.periode = periode
        self.MAJ()
        
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
        self.Refresh()
    
    def Selection(self):
        return self.GetSelectedObjects()
    
    def OnContextMenu(self, event):
        """Ouverture du menu contextuel """
        if len(self.Selection()) > 0 :
            ID = self.Selection()[0].IDnumPiece
        
        # Création du menu contextuel
        menuPop = wx.Menu()

        # Item Modifier
        item = wx.MenuItem(menuPop, 20, _("Ouvrir fiche Famille"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Modifier.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.OuvrirFicheFamille, id=20)
        if len(self.Selection()) == 0 : item.Enable(False)

        menuPop.AppendSeparator()

        """
        # Item Tout cocher
        item = wx.MenuItem(menuPop, 70, _("Cocher"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Cocher.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        cocher = self.ctrl_recherche
        self.Bind(wx.EVT_MENU, cocher.OnBoutonCocher(None), id=70)
        # Item Tout décocher
        item = wx.MenuItem(menuPop, 80, _("Tout décocher"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Decocher.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.CocheRien, id=80)

        menuPop.AppendSeparator()
        """
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
        ret = dlg.ShowModal()
        """if ret == wx.ID_OK:
            self.MAJ()"""
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
        panel.SetSizer(sizer_2)
        self.SetSize((900, 400))
        self.Layout()

if __name__ == '__main__':
    app = wx.App(0)
    frame_1 = MyFrame("sans",None, -1, "GroupListView")
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()
