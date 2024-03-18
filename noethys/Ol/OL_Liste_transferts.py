#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys branche Matthania
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS, JB
# Copyright:       (c) 2010-14 Ivan LUCAS, JB
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------

import copy
import Chemins
import wx
import GestionDB
import datetime
from Utils.UTILS_Traduction import _
from Ctrl.CTRL_ObjectListView import FastObjectListView, ColumnDefn, Filter, CTRL_Outils, PanelAvecFooter

def Nz(valeur):
    if valeur == None:
        valeur = 0
    return valeur

def DateEngDateFr(date):
    textDate = str(date)
    text = str(textDate[8:10]) + "/" + str(textDate[5:7]) + "/" + str(textDate[:4])
    return text

def DateDblDateEng(dateDbl):
    if not dateDbl:
        return None
    textDate = str(dateDbl)
    return "%s-%s-%s"%(textDate[:4],textDate[4:6],textDate[6:8])

class Track(object):
    def __init__(self, donnees):
        if not isinstance(donnees["transfert"],int):
            self.transfert = donnees["transfert"]
        else:
            self.transfert = str(DateDblDateEng(donnees["transfert"]))
        self.noLigne= self.IDfacture = donnees["noLigne"]
        #for champ in ("prestations","reglements","mvt","cumul"):
        #    donnees[champ] = Decimal(donnees[champ])
        self.prestations = donnees["prestations"]
        self.reglements = donnees["reglements"]
        self.mvt = donnees["mvt"]
        self.cumul = donnees["cumul"]

class TrackSepare(object):
    def __init__(self, texte,noLigne):
        self.transfert = texte
        self.noLigne= noLigne
        self.prestations = 0.0
        self.reglements = 0.0
        self.mvt = 0.0
        self.cumul = 0.0
        
class ListView(FastObjectListView):
    def __init__(self, *args, **kwds):
        self.dateFin = kwds.pop("dateFin", datetime.date.today())
        # Initialisation du listCtrl
        FastObjectListView.__init__(self, *args, **kwds)
        # Binds perso
        self.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)
        
    def InitModel(self):
        self.donnees = self.GetTracks()

    def GetTracks(self):
        """ Récupération des données groupées par date de transfert"""
        DB = GestionDB.DB()        

        """     CALCULS DES MONTANTS COMPTA PAR DATE DE TRANSFERTS      """

        # Recherche les bornes de l'exercice
        self.dateDeb, self.dateFin = DB.GetExercice(self.dateFin, alertes=True, approche=True)
        strDateMin = str(self.dateDeb)
        strDateMax = str(self.dateFin)
        # conditions de ruptures sur dates d'écritures
        jusquAN = "< '%s'"%strDateMin
        avant = "BETWEEN '%s' AND '%s'" %(strDateMin, strDateMax)
        apres = "> '%s'" %strDateMax
        lstConditions = [(0,"Exercices précédents",jusquAN),
                         (1,"Exercice %s"%strDateMax[:4],avant),
                         (2,"Ecritures post %s"%DateEngDateFr(strDateMax),apres)]
        
        dictTransferts = {}
        dictVide ={ "transfert": "",
                    "prestations": 0.0,
                    "reglements": 0.0,
                    "mvt":0.0,
                    "cumul":0.0}
        # déroulé des trois périodes de ruptures 
        for rupture, lblCondition, condition in lstConditions:
            dictTransferts[(rupture,"")] = copy.deepcopy(dictVide)
            dictTransferts[(rupture, "")]["transfert"]: lblCondition
            # Lecture des prestations hors 'conso' et transférées
            req = """SELECT compta,Sum(montant)
            FROM prestations
            WHERE (categorie NOT LIKE 'conso%%') 
                    AND prestations.date %s
            GROUP BY compta
            ORDER BY compta;""" % condition
            DB.ExecuterReq(req,MsgBox = "OL_Liste_transferts GetTracks11")
            listeTransferts = DB.ResultatReq()

            for transfert, montant in listeTransferts:
                transfert = DateDblDateEng(transfert)
                if not transfert:
                    dictTransferts[(rupture,"")]["prestations"] += montant
                    continue
                labels = (rupture,transfert)
                dictTransferts[labels] = copy.deepcopy(dictVide)

                dictTransferts[labels]["transfert"] = transfert
                dictTransferts[labels]["prestations"] = montant
                dictTransferts[labels]["reglements"] = 0.00

            # Lecture des transports sur les pièces factures
            req = """SELECT matPieces.pieComptaFac, Sum(matPieces.piePrixTranspAller), Sum(matPieces.piePrixTranspRetour)
                    FROM matPieces
                    WHERE (matPieces.pieComptaFac IS NOT NULL) AND matPieces.pieDateFacturation %s
                    GROUP BY matPieces.pieComptaFac
                    ORDER BY matPieces.pieComptaFac;""" %condition
            DB.ExecuterReq(req,MsgBox = "OL_Liste_transferts GetTracks12")
            listeTransferts = DB.ResultatReq()
            for transfert, mttTranspAller, mttTranspRetour in listeTransferts:
                transfert = DateDblDateEng(transfert)
                if not transfert:
                    dictTransferts[(rupture,"")]["prestations"] += montant
                    continue
                labels = (rupture,transfert)
                montant = Nz(mttTranspAller) + Nz(mttTranspRetour)
                if not labels in dictTransferts:
                    dictTransferts[labels] = copy.deepcopy(dictVide)
                    dictTransferts[labels]["transfert"] = transfert
                dictTransferts[labels]["prestations"] += montant

            # Lecture des lignes des pièces factures
            req = """SELECT matPieces.pieComptaFac, Sum(matPiecesLignes.ligMontant)
                    FROM (  matPieces
                            LEFT JOIN matPiecesLignes ON matPieces.pieIDnumPiece = matPiecesLignes.ligIDnumPiece)
                    WHERE (matPieces.pieComptaFac IS NOT NULL) AND (matPieces.pieDateFacturation %s)
                    GROUP BY matPieces.pieComptaFac
                    ORDER BY matPieces.pieComptaFac;""" % condition
            DB.ExecuterReq(req,MsgBox = "OL_Liste_transferts GetTracks12")
            listeTransferts = DB.ResultatReq()
            for transfert, mttLignes in listeTransferts:
                transfert = DateDblDateEng(transfert)
                if not transfert:
                    dictTransferts[(rupture,"")]["prestations"] += montant
                    continue
                labels = (rupture,transfert)
                montant = Nz(mttLignes)
                if not labels in dictTransferts:
                    dictTransferts[labels] = copy.deepcopy(dictVide)
                    dictTransferts[labels]["transfert"] = transfert
                dictTransferts[labels]["prestations"] += montant

            # Lecture des transports avoirs
            req = """SELECT matPieces.pieComptaAvo, Sum(matPieces.piePrixTranspAller), Sum(matPieces.piePrixTranspRetour)
                    FROM  matPieces
                    WHERE (matPieces.pieComptaAvo IS NOT NULL) AND (matPieces.pieDateAvoir %s)
                    GROUP BY matPieces.pieComptaAvo
                    ORDER BY matPieces.pieComptaAvo;""" % condition
            DB.ExecuterReq(req,MsgBox = "OL_Liste_transferts GetTracks13")
            listeTransferts = DB.ResultatReq()
            for transfert, mttTranspAller, mttTranspRetour in listeTransferts:
                transfert = DateDblDateEng(transfert)
                if not transfert:
                    dictTransferts[(rupture,"")]["prestations"] += montant
                    continue
                labels = (rupture,transfert)
                montant = -Nz(mttTranspAller)-Nz(mttTranspRetour)
                if not labels in dictTransferts:
                    dictTransferts[labels] = copy.deepcopy(dictVide)
                    dictTransferts[labels]["transfert"] = transfert
                dictTransferts[labels]["prestations"] += montant

            # Lecture des avoirs
            req = """SELECT matPieces.pieComptaAvo, Sum(matPiecesLignes.ligMontant)
                    FROM (  matPieces
                            LEFT JOIN matPiecesLignes ON matPieces.pieIDnumPiece = matPiecesLignes.ligIDnumPiece)
                    WHERE (matPieces.pieComptaAvo IS NOT NULL) AND (matPieces.pieDateAvoir %s)
                    GROUP BY matPieces.pieComptaAvo
                    ORDER BY matPieces.pieComptaAvo;""" % condition
            DB.ExecuterReq(req,MsgBox = "OL_Liste_transferts GetTracks13")
            listeTransferts = DB.ResultatReq()
            for transfert, mttLignes in listeTransferts:
                transfert = DateDblDateEng(transfert)
                if not transfert:
                    dictTransferts[(rupture,"")]["prestations"] += montant
                    continue
                labels = (rupture,transfert)
                montant = -Nz(mttLignes)
                if not labels in dictTransferts:
                    dictTransferts[labels] = copy.deepcopy(dictVide)
                    dictTransferts[labels]["transfert"] = transfert
                dictTransferts[labels]["prestations"] += montant

            """     REGLEMENTS   """

            # Lecture des dates de transferts des reglements
            req = """SELECT compta, Sum(reglements.montant)
                    FROM reglements 
                    LEFT JOIN depots ON reglements.IDdepot = depots.IDdepot
                    WHERE (((depots.date Is Null) 
                                    AND (reglements.date %s )) 
                             OR depots.date %s )
                    GROUP BY compta;""" % (condition, condition)
            DB.ExecuterReq(req,MsgBox = "OL_Liste_transferts GetTracks2")
            listeTransf2 = DB.ResultatReq()
            for transfert, montant in listeTransf2:
                transfert = DateDblDateEng(transfert)
                if not transfert:
                    dictTransferts[(rupture,"")]["reglements"] += montant
                    continue
                labels = (rupture,transfert)
                if not labels in dictTransferts:
                    dictTransferts[labels] = copy.deepcopy(dictVide)
                    dictTransferts[labels]["transfert"] = transfert
                # Analyse des opérations
                dictTransferts[labels]["reglements"] += montant
        dictTransferts[(99,"")] = copy.deepcopy(dictVide)

        """     REPRISE SUR RUPTURES PUIS PAR DATE TRANSFERTS     """

        #calcul ID et génération lignes et calcul des cumuls
        listeListeView = []
        cumul = 0.00
        noLigne = 1
        oldRupture = 0
        dictAnterieur = copy.deepcopy(dictVide)

        lstKeys = [x for x in dictTransferts.keys()]
        for (rupture,transfert) in sorted(lstKeys):
            if rupture == 0:
                if transfert == "":
                    # pour l'antérieur on ne cumule que le transféré
                    #dictAnteNoTrans = dictTransferts[(rupture,transfert)]
                    continue
                else:
                    dicTransf = dictTransferts[(rupture,transfert)]
                dictAnterieur["reglements"] += dicTransf["reglements"]
                dictAnterieur["prestations"] += dicTransf["prestations"]
                dictAnterieur["mvt"] += dicTransf["prestations"] - dicTransf["reglements"]
                oldRupture = rupture
                continue
            if rupture != oldRupture:
                oldTransfert = lstConditions[oldRupture][1]
                if oldRupture == 0:
                    # pose l'antérieur sur une seule ligne
                    dictAnterieur["transfert"] = oldTransfert
                    dictAnterieur["noLigne"] = noLigne
                    cumul += dictAnterieur["mvt"]
                    dictAnterieur["cumul"] = cumul
                    listeListeView.append(Track(dictAnterieur))
                    noLigne += 1
                    #dictTransferts[(oldRupture, "")] = dictAnteNoTrans
                dictNoTrans = dictTransferts[(oldRupture, "")]
                dictNoTrans["mvt"] = dictNoTrans["prestations"] - dictNoTrans["reglements"]
                # pose le non transféré groupé de la rupture
                if dictNoTrans["mvt"] != 0.0:
                    dictNoTrans["transfert"] = "Non transféré %s"%oldTransfert
                    dictNoTrans["noLigne"] = noLigne
                    #cumul += dictNoTrans["mvt"]
                    dictNoTrans["cumul"] = cumul
                    listeListeView.append(Track(dictNoTrans))
                    noLigne += 1
                # pose une ligne séparation
                if rupture < 3:
                    track = TrackSepare(lstConditions[rupture][1], noLigne)
                    listeListeView.append(track)
                    noLigne += 1
                oldRupture = rupture
                
            if transfert == "":
                # le non transféré sera repris au changement de rupture
                continue
            dictTrans = dictTransferts[(rupture,transfert)]
            dictTrans["noLigne"] = noLigne
            dictTrans["mvt"] = dictTrans["prestations"] - dictTrans[
                "reglements"]
            cumul += dictTrans["mvt"]
            dictTrans["cumul"] = cumul
            listeListeView.append(Track(dictTrans))
            noLigne += 1

        """     AJOUT DERNIER TRANSFERT DEPOT   """

        # Lecture des dates de transferts des reglements
        req = """SELECT Max(depots.date)
                FROM reglements INNER JOIN depots ON reglements.IDdepot = depots.IDdepot
                WHERE (reglements.compta Is Not Null);"""
        DB.ExecuterReq(req,MsgBox = "OL_Liste_transferts GetTracks5")
        recordset = DB.ResultatReq()
        lastReglement = recordset[0][0]
        strLastReglement = DateEngDateFr(lastReglement)
        track = TrackSepare("Dernier dépôt transféré: %s"%strLastReglement,noLigne)
        listeListeView.append(track)
        noLigne += 1

        DB.Close()
        return listeListeView

    def InitObjectListView(self):            
        # Couleur en alternance des lignes
        self.oddRowsBackColor = "#F0FBED" 
        self.evenRowsBackColor = wx.Colour(255, 255, 255)
        self.useExpansionColumn = True

        def FormateDate(date):
            if len(date) != 10:
                return date
            return DateEngDateFr(date)

        def FormateMontant(montant):
            if montant == None : return ""
            if montant == 0.0:
                return ""
            strMontant = '{:,.2f}'.format(montant).replace(',', ' ')
            return strMontant

        def FormateEntier(entier):
            if entier == None : return ""
            strMontant = ('   {:.0f}'.format(entier))[-3:]
            return strMontant

        liste_Colonnes = [
            ColumnDefn("Ligne", "left", 45, "noLigne", typeDonnee="entier", stringConverter=FormateEntier),
            ColumnDefn("Transferts", "left", 200, "transfert", typeDonnee="texte", stringConverter=FormateDate),
            ColumnDefn(_("Prestations"), 'right', 90, "prestations", typeDonnee="montant", stringConverter=FormateMontant,),
            ColumnDefn(_("Règlements"), 'right', 90, "reglements", typeDonnee="montant", stringConverter=FormateMontant),
            ColumnDefn(_("Mvt Clients"), "right", 90, "mvt", typeDonnee="montant", stringConverter=FormateMontant),
            ColumnDefn(_("Transféré"), "right", 120, "cumul", typeDonnee="montant", stringConverter=FormateMontant),
            ]

        self.SetColumns(liste_Colonnes)
        self.SetEmptyListMsg(_("Aucun transfert"))
        self.SetEmptyListMsgFont(wx.FFont(11, wx.DEFAULT, faceName="Tekton"))
        self.SetSortColumn(self.columns[0])
        self.SetObjects(self.donnees)
       
    def MAJ(self, track=None):
        self.Freeze()
        self.InitModel()
        self.InitObjectListView()
        # Sélection d'un item
        if track != None :
            self.SelectObject(track, deselectOthers=True, ensureVisible=True)
        # MAJ listctrl
        self._ResizeSpaceFillingColumns() 
        self.Thaw() 

    def Selection(self):
        return self.GetSelectedObjects()

    def OnContextMenu(self, event):
        """Ouverture du menu contextuel """
        if len(self.Selection()) == 0:
            noSelection = True
        else:
            noSelection = False
            ID = self.Selection()[0].noLigne
                
        # Création du menu contextuel
        menuPop = wx.Menu()


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
        prt = UTILS_Printer.ObjectListViewPrinter(self, titre=_("Liste des transferts"), format="A", orientation=wx.PORTRAIT)
        prt.Preview()

    def Imprimer(self, event):
        from Utils import UTILS_Printer
        prt = UTILS_Printer.ObjectListViewPrinter(self, titre=_("Liste des transferts"), format="A", orientation=wx.PORTRAIT)
        prt.Print()

    def ExportTexte(self, event):
        from Utils import UTILS_Export
        UTILS_Export.ExportTexte(self, titre=_("Liste des transferts"))
        
    def ExportExcel(self, event):
        from Utils import UTILS_Export
        UTILS_Export.ExportExcel(self, titre=_("Liste des transferts"))
    
# -------------------------------------------------------------------------------------------------------------------------------------------

class BarreRecherche(wx.SearchCtrl):
    def __init__(self, parent, listview=None):
        wx.SearchCtrl.__init__(self, parent, size=(-1, -1), style=wx.TE_PROCESS_ENTER)
        self.parent = parent
        self.rechercheEnCours = False
        
        self.SetDescriptiveText(_("Rechercher..."))
        self.ShowSearchButton(True)
        
        self.listView = listview
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
            "transfert" : {"mode" : "nombre", "singulier" : _("transfert"), "pluriel" : _("lignes"), "alignement" : wx.ALIGN_LEFT},
            "prestations" : {"mode" : "total"},
            "reglements" : {"mode" : "total"},
            "mvt" : {"mode" : "total"},
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

        self.listviewAvecFooter = ListviewAvecFooter(panel) 
        self.ctrl_transferts = self.listviewAvecFooter.GetListview()
        self.ctrl_transferts.MAJ()
        
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_2.Add(self.listviewAvecFooter, 1, wx.ALL|wx.EXPAND)
        panel.SetSizer(sizer_2)
        self.Layout()



if __name__ == '__main__':
    app = wx.App(0)
    #wx.InitAllImageHandlers()
    frame_1 = MyFrame(None, -1, "OL TEST")
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()
