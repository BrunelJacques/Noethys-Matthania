#!/usr/bin/env python
# -*- coding: utf8 -*-
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
from Ctrl import CTRL_Bouton_image
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

def DateTimeToInt(date):
    return date.year * 10000 + date.month * 100 + date.day


def DateEngDateFr(date):
    textDate = str(date)
    text = str(textDate[8:10]) + "/" + str(textDate[5:7]) + "/" + str(textDate[:4])
    return text

def DateDblDateFr(dateDbl):
    textDate = str(dateDbl)
    text = str(textDate[6:8]) + "/" + str(textDate[4:6]) + "/" + str(textDate[:4])
    return text

class Track(object):
    def __init__(self, donnees):
        if not isinstance(donnees["nature"],int):
            self.nature = donnees["nature"]
        else:
            self.nature = str(DateDblDateFr(donnees["nature"]))
        self.prestations = donnees["prestations"]
        self.reglements = donnees["reglements"]
        self.echus = donnees["echus"]
        self.nonechus = donnees["reglements"] - donnees["echus"]
        self.mvt = donnees["mvt"]
        self.id = donnees["id"]

class TrackSepare(object):
    def __init__(self, texte,idx):
        self.id = idx
        self.nature = texte
        self.prestations = None
        self.reglements = None
        self.mvt = None
        self.cumul = None
    
class ListView(FastObjectListView):
    def __init__(self, *args, **kwds):
        self.dateAnalyse = kwds.pop("dateFin", None)
        # Initialisation du listCtrl
        FastObjectListView.__init__(self, *args, **kwds)
        # Binds perso
        self.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)

    def InitModel(self):
        self.donnees = self.GetTracks()

    def GetTracks(self):
        """ Récupération des données groupées par nature"""
        DB = GestionDB.DB()        

        """     ETAT DES MONTANTS COMPTA NON TRANSFERES     """

        # Recherche la date fin de l'exercice
        lstClotures = DB.GetClotures()

        if self.dateAnalyse == None:
            self.dateAnalyse = lstClotures[-1]

        dictNatures = {}
        debut = ''
        for cloture in lstClotures:
            condition = debut + " AND (prestations.date <= '"+cloture+ "')"
            if debut == '':
                periode = " Pour clôtures jusqu'au "+ DateEngDateFr(cloture)
            else:
                periode = cloture
            debut = " AND (prestations.date > '"+cloture + "')"
            # Lecture des prestations non transférése
            req = """SELECT categorie,Sum(montant)
            FROM prestations
            WHERE (categorie NOT LIKE 'conso%%') 
                    AND (compta IS NULL) 
                    %s
                    AND (prestations.date <= '%s') 
            GROUP BY categorie
            ORDER BY categorie;""" % (condition,self.dateAnalyse)
            DB.ExecuterReq(req,MsgBox = "OL_Liste_natures GetTracks11")
            lstNatures = DB.ResultatReq()

            for nature, montant in lstNatures:
                labels = ("%s"%( periode),nature)
                dictNatures[labels] = {}
                dictNatures[labels]["nature"] = nature
                dictNatures[labels]["prestations"] = montant
                dictNatures[labels]["reglements"] = 0.00
                dictNatures[labels]["nonechus"] = 0.00
                dictNatures[labels]["echus"] = 0.00

            # Lecture des transports sur les pièces
            condition2 = condition.replace('prestations.date','matPieces.pieDateFacturation')
            condition1 = condition.replace('prestations.date','matPieces.pieDateEcheance')
            req = """SELECT matPieces.pieNature, Sum(matPieces.piePrixTranspAller), Sum(matPieces.piePrixTranspRetour)
                    FROM matPieces
                    WHERE (matPieces.pieComptaFac IS NULL) 
                            AND (   (   (matPieces.pieDateFacturation IS NULL)
                                        %s
                                        AND (matPieces.pieDateEcheance <= '%s'))
                                    OR ((matPieces.pieDateFacturation IS NOT NULL)
                                        %s
                                        AND (matPieces.pieDateFacturation <= '%s') ))
                    GROUP BY matPieces.pieNature
                    ORDER BY matPieces.pieNature;""" %(condition1,self.dateAnalyse,condition2,self.dateAnalyse)
            DB.ExecuterReq(req,MsgBox = "OL_Liste_natures GetTracks12")
            lstNatures = DB.ResultatReq()
            for nature, mttTranspAller, mttTranspRetour in lstNatures:
                labels = ("%s"%periode,nature)
                montant = Nz(mttTranspAller) + Nz(mttTranspRetour)
                if labels in dictNatures:
                    dictNatures[labels]["prestations"] += montant
                else:
                    dictNatures[labels] = {}
                    dictNatures[labels]["nature"] = nature
                    dictNatures[labels]["prestations"] = montant
                dictNatures[labels]["reglements"] = 0.00
                dictNatures[labels]["nonechus"] = 0.00
                dictNatures[labels]["echus"] = 0.00

            # Lecture des lignes des pièces factures
            req = """SELECT matPieces.pieNature, Sum(matPiecesLignes.ligMontant)
                    FROM (  matPieces
                            LEFT JOIN matPiecesLignes ON matPieces.pieIDnumPiece = matPiecesLignes.ligIDnumPiece)
                    WHERE (matPieces.pieComptaFac IS NULL) 
                            AND (   (   (matPieces.pieDateFacturation IS NULL)
                                        %s
                                        AND (matPieces.pieDateEcheance <= '%s') 
                                    )
                                    OR 
                                    (   (matPieces.pieDateFacturation IS NOT NULL)
                                        %s
                                        AND (matPieces.pieDateFacturation <= '%s')
                                    )
                                )
                    GROUP BY matPieces.pieNature
                    ORDER BY matPieces.pieNature;""" %(condition1,self.dateAnalyse,condition2,self.dateAnalyse)
            DB.ExecuterReq(req,MsgBox = "OL_Liste_natures GetTracks13")
            lstNatures = DB.ResultatReq()
            for nature, mttLignes in lstNatures:
                labels = ("%s"%( periode),nature)
                montant = Nz(mttLignes)
                if labels in dictNatures:
                    dictNatures[labels]["prestations"] += montant
                    dictNatures[labels]["reglements"] = 0.00
                    dictNatures[labels]["nonechus"] = 0.00
                    dictNatures[labels]["echus"] = 0.00

            # Lecture des transports avoirs
            condition2 = condition.replace('prestations.date','matPieces.pieDateAvoir')
            condition1 = condition.replace('prestations.date','matPieces.pieDateEcheance')
            req = """SELECT matPieces.pieNature, Sum(matPieces.piePrixTranspAller), Sum(matPieces.piePrixTranspRetour)
                    FROM  matPieces
                    WHERE   (matPieces.pieComptaAvo IS NULL)
                            AND (matPieces.pieNature = 'AVO') 
                            AND (   (   (matPieces.pieDateAvoir IS NULL)
                                        %s
                                        AND (matPieces.pieDateEcheance <= '%s') 
                                    )
                                    OR 
                                    (   (matPieces.pieDateAvoir IS NOT NULL)
                                        %s
                                        AND (matPieces.pieDateAvoir <= '%s') 
                                    )
                                )
                    GROUP BY matPieces.pieNature
                    ORDER BY matPieces.pieNature;""" %(condition1,self.dateAnalyse,condition2,self.dateAnalyse)
            DB.ExecuterReq(req,MsgBox = "OL_Liste_natures GetTracks14")
            lstNatures = DB.ResultatReq()
            for nature, mttTranspAller, mttTranspRetour in lstNatures:
                labels = ("%s"%( periode),nature)
                montant = -Nz(mttTranspAller)-Nz(mttTranspRetour)
                if labels in dictNatures:
                    dictNatures[labels]["prestations"] += montant
                else:
                    dictNatures[labels] = {}
                    dictNatures[labels]["nature"] = nature
                    dictNatures[labels]["prestations"] = montant
                dictNatures[labels]["reglements"] = 0.00
                dictNatures[labels]["nonechus"] = 0.00
                dictNatures[labels]["echus"] = 0.00

            # Lecture des avoirs
            req = """SELECT matPieces.pieComptaAvo, Sum(matPiecesLignes.ligMontant)
                    FROM (  matPieces
                            LEFT JOIN matPiecesLignes ON matPieces.pieIDnumPiece = matPiecesLignes.ligIDnumPiece)
                    WHERE   (matPieces.pieComptaAvo IS NULL) 
                            AND (matPieces.pieNature = 'AVO') 
                            AND (   (   (matPieces.pieDateAvoir IS NULL)
                                        %s
                                        AND (matPieces.pieDateEcheance <= '%s')
                                    )
                                    OR 
                                    (   (matPieces.pieDateAvoir IS NOT NULL)
                                        %s
                                        AND (matPieces.pieDateAvoir <= '%s')
                                    )
                                )
                    GROUP BY matPieces.pieComptaAvo
                    ORDER BY matPieces.pieComptaAvo;""" %(condition1,self.dateAnalyse,condition2,self.dateAnalyse)
            DB.ExecuterReq(req,MsgBox = "OL_Liste_natures GetTracks15")
            lstNatures = DB.ResultatReq()
            for nature, mttLignes in lstNatures:
                labels = ("%s"%( periode),nature)
                montant = -Nz(mttLignes)
                if labels in dictNatures:
                    dictNatures[labels]["prestations"] += montant
                    dictNatures[labels]["reglements"] = 0.00
                    dictNatures[labels]["nonechus"] = 0.00
                    dictNatures[labels]["echus"] = 0.00

            """     REGLEMENTS   """

            # Lecture des dates de natures des reglements
            condition1 = condition.replace('prestations.date','reglements.date')
            condition2 = condition.replace('prestations.date','depots.date')
            req = """SELECT modes_reglements.label, Sum(reglements.montant),
                            IF ((reglements.date_differe IS NULL
                                    OR reglements.date_differe <= '%s'),
                                True,False) as echu
                    FROM reglements 
                    LEFT JOIN modes_reglements ON reglements.IDmode = modes_reglements.IDmode
                    LEFT JOIN depots ON reglements.IDdepot = depots.IDdepot
                    WHERE   (reglements.date <= '%s') 
                            %s
                            AND (   (reglements.compta IS NULL)  
                                    OR( depots.date > '%s')
                                )
                    GROUP BY modes_reglements.label, echu;""" % (self.dateAnalyse,self.dateAnalyse,condition1,cloture)

            DB.ExecuterReq(req,MsgBox = "OL_Liste_natures GetTracks2")
            listeTransf2 = DB.ResultatReq()
            for nature, montant, echu in listeTransf2:
                labels = ("%s"%( periode),'regl : %s'%nature)
                if labels not in dictNatures:
                    dictNatures[labels] = {}
                    dictNatures[labels]["nature"] = 'regl : %s'%nature
                    dictNatures[labels]["prestations"] = 0.00
                    dictNatures[labels]["reglements"] = 0.00
                    dictNatures[labels]["echus"] = 0.00
                # Analyse des opérations
                if labels in list(dictNatures.keys()):
                    dictNatures[labels]["reglements"] += montant
                    if echu:
                        dictNatures[labels]["echus"] += montant
                else:
                    dictNatures[labels]["reglements"] = montant
                    if echu:
                        dictNatures[labels]["echus"] = montant
                    else:
                        dictNatures[labels]["echus"] = 0.0

        """     REPRISE SUR CHARNIERE FIN D'EXERCICE PUIS PAR NATURE     """
        # purge des périodes à zéro
        for cle in list(dictNatures.keys()) :
            if dictNatures[cle]['reglements']== 0.0 and dictNatures[cle]['prestations']== 0.0:
                del dictNatures[cle]

        #calcul ID et génération lignes et calcul des cumuls
        listeListeView = []

        # boucle sur les lignes
        id = 0
        encours = ''
        for (periode,nature) in sorted(dictNatures.keys()) :
            if periode[:5] == ' Pour':
                texte = periode
            else:
                strDate = DateEngDateFr(periode)
                texte = " Pour clôture du %s" %strDate
            if periode != encours:
                track = TrackSepare(texte,id)
                listeListeView.append(track)
                encours = periode
            dicTransf = dictNatures[(periode,nature)]
            dicTransf["id"]= id+1
            if dicTransf["reglements"] == None: dicTransf["reglements"] = 0.00
            if dicTransf["prestations"] == None: dicTransf["prestations"] = 0.00
            dicTransf["mvt"] = dicTransf["prestations"] - dicTransf["reglements"]
            track = Track(dicTransf)
            listeListeView.append(track)
            id +=2
        texte = "Analysé au %s"%DateEngDateFr(self.dateAnalyse)
        track = TrackSepare(texte, id)
        listeListeView.append(track)

        DB.Close()
        return listeListeView

    def InitObjectListView(self):            
        # Couleur en alternance des lignes
        self.oddRowsBackColor = "#F0FBED" 
        self.evenRowsBackColor = wx.Colour(255, 255, 255)
        self.useExpansionColumn = True

        def FormateDate(date):
            return UTILS_Dates.DateDDEnFr(date)

        def FormateMontant(montant):
            if montant == None : return ""
            strMontant = '{:,.2f}'.format(montant).replace(',', ' ')
            return strMontant

        liste_Colonnes = [
            ColumnDefn("ID", 'right', 0, "id", typeDonnee="nombre"),
            ColumnDefn("Nature", "left", 200, "nature", typeDonnee="texte"),
            ColumnDefn(_("Prestations"), 'right', 100, "prestations", typeDonnee="montant", stringConverter=FormateMontant),
            ColumnDefn(_("Règlements"), 'right', 100, "reglements", typeDonnee="montant", stringConverter=FormateMontant),
            ColumnDefn(_("Dont échus"), "right", 100, "echus", typeDonnee="montant", stringConverter=FormateMontant),
            ColumnDefn(_("Dont non échus"), "right", 100, "nonechus", typeDonnee="montant", stringConverter=FormateMontant),
            ColumnDefn(_("Mvt Clients"), "right", 100, "mvt", typeDonnee="montant", stringConverter=FormateMontant),
            ]

        self.SetColumns(liste_Colonnes)
        self.SetEmptyListMsg(_("Aucund données"))
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
        dte = DateEngDateFr(self.dateAnalyse)
        prt = UTILS_Printer.ObjectListViewPrinter(self, titre=_("Liste des écritures non transférées en compta au %s"%dte), format="A", orientation=wx.PORTRAIT)
        prt.Preview()

    def Imprimer(self, event):
        from Utils import UTILS_Printer
        dte = DateEngDateFr(self.dateAnalyse)
        prt = UTILS_Printer.ObjectListViewPrinter(self, titre=_("Liste des écritures non transférées en compta au %s"%dte), format="A", orientation=wx.PORTRAIT)
        prt.Print()

    def ExportTexte(self, event):
        from Utils import UTILS_Export
        UTILS_Export.ExportTexte(self, titre=_("Liste des natures"))
        
    def ExportExcel(self, event):
        from Utils import UTILS_Export
        UTILS_Export.ExportExcel(self, titre=_("Liste des natures"))
    
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
            "nature" : {"mode" : "nombre", "singulier" : _("nature"), "pluriel" : _("lignes"), "alignement" : wx.ALIGN_LEFT},
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
        self.ctrl_natures = self.listviewAvecFooter.GetListview()
        self.ctrl_natures.MAJ()
        
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
