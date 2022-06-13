#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys branche Matthania
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS, JB
# Copyright:       (c) 2010-14 Ivan LUCAS, JB
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------


from Utils.UTILS_Traduction import _
import Chemins
import wx
import GestionDB
import datetime

from Utils import UTILS_Config
SYMBOLE = UTILS_Config.GetParametre("monnaie_symbole", "€")

from Ctrl.CTRL_ObjectListView import FastObjectListView, ColumnDefn, Filter, CTRL_Outils, PanelAvecFooter

from Utils import UTILS_Dates

def Nz(valeur):
    if valeur == None:
        valeur = 0
    return valeur

def DateEngDateFr(date):
    textDate = str(date)
    text = str(textDate[8:10]) + "/" + str(textDate[5:7]) + "/" + str(textDate[:4])
    return text

def zzDateDblDateFr(dateDbl):
    textDate = str(dateDbl)
    text = str(textDate[6:8]) + "/" + str(textDate[4:6]) + "/" + str(textDate[:4])
    return text

def DateDblDateEng(dateDbl):
    textDate = str(dateDbl)
    return "%s-%s-%s"%(textDate[:4],textDate[4:6],textDate[6:8])

class Track(object):
    def __init__(self, donnees):
        if not isinstance(donnees["transfert"],int):
            self.transfert = donnees["transfert"]
        else:
            self.transfert = str(DateDblDateEng(donnees["transfert"]))
        self.IDtransfert = donnees["IDtransfert"]
        self.prestations = donnees["prestations"]
        self.reglements = donnees["reglements"]
        self.mvt = donnees["mvt"]
        self.cumul = donnees["cumul"]

class TrackSepare(object):
    def __init__(self, texte,idx):
        self.transfert = texte
        self.IDtransfert = idx
        self.prestations = None
        self.reglements = None
        self.mvt = None
        self.cumul = None
    
class ListView(FastObjectListView):
    def __init__(self, *args, **kwds):
        self.dateFin = kwds.pop("dateFin", None)
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

        # Recherche la date fin de l'exercice
        if self.dateFin == None:
            exdeb, exfin = DB.GetExercice(datetime.date.today(),alertes=False,approche=True)
            dateMax =  exdeb - datetime.timedelta(1)
        else:
            dateMax=self.dateFin

        avant = "<= '%s'" %dateMax
        apres = ">   '%s'" %dateMax

        dictTransferts = {}
        for condition in [avant, apres]:
            # Lecture des prestations non facturées
            req = """SELECT compta,Sum(montant)
            FROM prestations
            WHERE (categorie NOT LIKE 'conso%%') AND (compta IS NOT NULL) AND prestations.date %s
            GROUP BY compta
            ORDER BY compta;""" % condition
            DB.ExecuterReq(req,MsgBox = "OL_Liste_transferts GetTracks11")
            listeTransferts = DB.ResultatReq()

            for transfert, montant in listeTransferts:
                labels = ("%s"%( condition),transfert)
                dictTransferts[labels] = {}
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
                labels = ("%s"%condition,transfert)
                montant = Nz(mttTranspAller) + Nz(mttTranspRetour)
                if labels in dictTransferts:
                    dictTransferts[labels]["prestations"] += montant
                    dictTransferts[labels]["reglements"] = 0.00
                else:
                    dictTransferts[labels] = {}
                    dictTransferts[labels]["transfert"] = transfert
                    dictTransferts[labels]["prestations"] = montant
                    dictTransferts[labels]["reglements"] = 0.00

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
                labels = ("%s"%( condition),transfert)
                montant = Nz(mttLignes)
                if labels in dictTransferts:
                    dictTransferts[labels]["prestations"] += montant
                    dictTransferts[labels]["reglements"] = 0.00

            # Lecture des transports avoirs
            req = """SELECT matPieces.pieComptaAvo, Sum(matPieces.piePrixTranspAller), Sum(matPieces.piePrixTranspRetour)
                    FROM  matPieces
                    WHERE (matPieces.pieComptaAvo IS NOT NULL) AND (matPieces.pieDateAvoir %s)
                    GROUP BY matPieces.pieComptaAvo
                    ORDER BY matPieces.pieComptaAvo;""" % condition
            DB.ExecuterReq(req,MsgBox = "OL_Liste_transferts GetTracks13")
            listeTransferts = DB.ResultatReq()
            for transfert, mttTranspAller, mttTranspRetour in listeTransferts:
                labels = ("%s"%( condition),transfert)
                montant = -Nz(mttTranspAller)-Nz(mttTranspRetour)
                if labels in dictTransferts:
                    dictTransferts[labels]["prestations"] += montant
                    dictTransferts[labels]["reglements"] = 0.00
                else:
                    dictTransferts[labels] = {}
                    dictTransferts[labels]["transfert"] = transfert
                    dictTransferts[labels]["prestations"] = montant
                    dictTransferts[labels]["reglements"] = 0.00

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
                labels = ("%s"%( condition),transfert)
                montant = -Nz(mttLignes)
                if labels in dictTransferts:
                    dictTransferts[labels]["prestations"] += montant
                    dictTransferts[labels]["reglements"] = 0.00

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
                labels = ("%s"%( condition),transfert)
                if labels not in dictTransferts:
                    dictTransferts[labels] = {}
                    dictTransferts[labels]["transfert"] = transfert
                    dictTransferts[labels]["prestations"] = 0.00
                # Analyse des opérations
                dictTransferts[labels]["reglements"] = montant

        """     REPRISE SUR CHARNIERE FIN D'EXERCICE PUIS PAR DATE TRANSFERTS     """

        #calcul ID et génération lignes et calcul des cumuls
        listeListeView = []
        reste={}
        cumul = 0.00
        strDateMax = DateEngDateFr(dateMax)
        track = TrackSepare("Avant Clôture au %s"%strDateMax,0)
        listeListeView.append(track)
        idxavant = 1
        idxapres = 1000
        clereste= None

        def takeFirst(elem):
            return elem[0]

        # première boucle avant clôture
        for (condition,transfert) in sorted(dictTransferts.keys(), key=takeFirst) :
            if condition == avant:
                dicTransf = dictTransferts[(condition,transfert)]
                if dicTransf["reglements"] == None: dicTransf["reglements"] = 0.00
                if dicTransf["prestations"] == None: dicTransf["prestations"] = 0.00
                dicTransf["mvt"] = dicTransf["prestations"] - dicTransf["reglements"]
                if transfert != None :
                    dicTransf["IDtransfert"] = idxavant
                    idxavant += 1
                    cumul += dicTransf["mvt"]
                    dicTransf["cumul"]= cumul
                    track = Track(dicTransf)
                    listeListeView.append(track)
                else:
                    if condition != apres:
                        dicTransf["IDtransfert"] = idxapres-2
                        clereste = (condition,transfert)
                        reste=dicTransf
        if clereste != None:
            reste["transfert"]= "Non transféré"
            reste["cumul"]= reste["mvt"]+cumul
            listeListeView.append(Track(reste))

        # boucle après clôture
        track = TrackSepare(" ",idxapres-2)
        listeListeView.append(track)
        track = TrackSepare("Après Clôture au %s"%strDateMax,idxapres-1)
        listeListeView.append(track)

        clereste = None
        for (condition,transfert) in sorted(dictTransferts.keys(), key=takeFirst) :
            if condition == apres:
                dicTransf = dictTransferts[(condition,transfert)]
                if dicTransf["reglements"] == None: dicTransf["reglements"] = 0.00
                if dicTransf["prestations"] == None: dicTransf["prestations"] = 0.00
                dicTransf["mvt"] = dicTransf["prestations"] - dicTransf["reglements"]
                if transfert != None :
                    dicTransf["IDtransfert"] = idxapres
                    idxapres += 1
                    cumul += dicTransf["mvt"]
                    dicTransf["cumul"]= cumul
                    track = Track(dicTransf)
                    listeListeView.append(track)
                else:
                    if condition != avant:
                        dicTransf["IDtransfert"] = idxapres *2
                        clereste = (condition,transfert)
                        reste=dicTransf
        if clereste != None:
            reste["transfert"]= "Non transféré"
            reste["cumul"]= reste["mvt"]+cumul
            listeListeView.append(Track(reste))

        """     AJOUT DES DATES MAXI   """

        # Lecture des dates de transferts des reglements
        req = """SELECT Max(depots.date)
                FROM reglements INNER JOIN depots ON reglements.IDdepot = depots.IDdepot
                WHERE (reglements.compta Is Not Null);"""
        DB.ExecuterReq(req,MsgBox = "OL_Liste_transferts GetTracks5")
        recordset = DB.ResultatReq()
        lastReglement = recordset[0][0]
        strLastReglement = DateEngDateFr(lastReglement)
        track = TrackSepare("Dernier dépôt transféré: %s"%strLastReglement,idxapres*3)
        listeListeView.append(track)

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
            strMontant = '{:,.2f}'.format(montant).replace(',', ' ')
            return strMontant

        liste_Colonnes = [
            ColumnDefn("ID", "right", 0, "IDtransfert", typeDonnee="entier"),
            ColumnDefn("Transferts", "left", 200, "transfert", typeDonnee="texte", stringConverter=FormateDate),
            ColumnDefn(_("Prestations"), 'right', 90, "prestations", typeDonnee="montant", stringConverter=FormateMontant),
            ColumnDefn(_("Règlements"), 'right', 90, "reglements", typeDonnee="montant", stringConverter=FormateMontant),
            ColumnDefn(_("Mvt Clients"), "right", 90, "mvt", typeDonnee="montant", stringConverter=FormateMontant),
            ColumnDefn(_("Cumul clients"), "right", 120, "cumul", typeDonnee="montant", stringConverter=FormateMontant),
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
            ID = self.Selection()[0].IDtransfert
                
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
