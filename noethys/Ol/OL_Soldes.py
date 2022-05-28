#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys branche Matthania
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS, JB, modifié JB pour provisions
# Copyright:       (c) 2010-11 Ivan LUCAS, JB
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------


from Utils.UTILS_Traduction import _
import Chemins
import wx
import datetime
import GestionDB
from Utils import UTILS_Titulaires
from Utils.UTILS_Decimal import FloatToDecimal as FloatToDecimal
from Utils import UTILS_Utilisateurs
from Utils import UTILS_Config
SYMBOLE = UTILS_Config.GetParametre("monnaie_symbole", "€")

from Ctrl.CTRL_ObjectListView import FastObjectListView, ColumnDefn, Filter, CTRL_Outils, PanelAvecFooter


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

def DateEngEnDateDD(dateEng):
    if dateEng and not isinstance(dateEng,str): dateEng = str(dateEng)
    return datetime.date(int(dateEng[:4]), int(dateEng[5:7]), int(dateEng[8:10]))

def Nz(valeur):
    try:
        u = round(float(valeur),4)
    except:
        u = 0.0
    return u

# ----------------------------------------------------------------------------------------------------------------------------------------

def Importation(situation, afficherDebit, afficherCredit, afficherNul, afficherCompta,):
    DB = GestionDB.DB()
    nbannee = 5
    # Composition du filtre sur payeurs
    if afficherNul == False :
        fNul = """
        WHERE ((ROUND(mttRegl.Regl,2) <> ROUND(mttPrest.Prest,2)))
                OR (mttRegl.Regl IS NULL AND mttPrest.Prest IS NOT NULL)
                OR (mttRegl.Regl IS NOT NULL AND mttPrest.Prest IS NULL)"""
    else : fNul = ""

    if afficherCompta == True :
        fComptaPrest = "AND (prestations.compta IS NOT NULL )"
        fComptaRegl  = "AND (reglements.compta IS NOT NULL ) "
        fPrest = "(prestations.date <='%s') %s"%(situation,fComptaPrest)
        fRegl = "(depots.date <='%s') %s"%(situation,fComptaRegl)
    else :
        fComptaPrest = ""
        fComptaRegl  = ""
        fPrest = "1=1"
        fRegl = "1=1"
    # Récupère les comptes payeurs et les soldes
    req = """
        SELECT comptes_payeurs.IDcompte_payeur, mttPrest.Prest, mttRegl.Regl
        FROM comptes_payeurs
        LEFT JOIN
                ( SELECT prestations.IDcompte_payeur, Sum(prestations.montant) AS Prest
                FROM prestations
                WHERE ( %s )
                GROUP BY prestations.IDcompte_payeur)
            AS mttPrest
        ON comptes_payeurs.IDcompte_payeur = mttPrest.IDcompte_payeur

        LEFT JOIN
                ( SELECT reglements.IDcompte_payeur, Sum(reglements.montant) AS Regl
                FROM    reglements 
                        LEFT JOIN depots ON reglements.IDdepot = depots.IDdepot
                WHERE ( %s )
                GROUP BY reglements.IDcompte_payeur)
            AS mttRegl
        ON comptes_payeurs.IDcompte_payeur = mttRegl.IDcompte_payeur
        %s
        ;""" % (fPrest, fRegl, fNul)
    DB.ExecuterReq(req,MsgBox="OL_Soldes.Importation_soldes")
    listeComptes = DB.ResultatReq()
    listeIDpayeurs = []
    dictSoldes = {}

    # constitution du dict des soldes et des lignes à instruire
    for IDcompte_payeur,total_prestations, total_reglements in listeComptes :
        solde = Nz(total_prestations) - Nz(total_reglements)
        if afficherDebit == False and solde > 0.0 :
            continue
        if afficherCredit == False and solde < 0.0 :
            continue
        if afficherNul == False and abs(solde) < 0.01 :
            continue
        listeIDpayeurs.append(IDcompte_payeur)
        dictSoldes[IDcompte_payeur] = {}
        dictSoldes[IDcompte_payeur]['solde'] = solde
        dictSoldes[IDcompte_payeur]['debits'] = [0,] * nbannee
        dictSoldes[IDcompte_payeur]['credits'] = [0,] * nbannee

    # Récupère les antériorités de créances
    fID = "(" + str(listeIDpayeurs)[1:-1] + ")"
    for age in range(nbannee):
        an = situation.year - age
        if afficherCompta == True and age == 0 :
            fin = datetime.date(2999,12,31)
        else:
            fin = datetime.date(an,situation.month,situation.day)
        deb = datetime.date(an - 1,situation.month,situation.day)
        if age == nbannee - 1:
            deb = datetime.date(1900,1,1)
        #en chantier----------------
        fPrest = "prestations.date <= '%s' AND prestations.date > '%s' "%(fin,deb) + fComptaPrest
        if afficherCompta == True:
            condRegl = """
                    LEFT JOIN depots ON reglements.IDdepot = depots.IDdepot
                    WHERE ( depots.date <= '%s' AND depots.date > '%s'  )"""%(fin,deb) + fComptaRegl
        else:
            condRegl = """
                    WHERE ( reglements.date <= '%s' AND reglements.date > '%s'  )"""%(fin,deb) + fComptaRegl

        req = """
            SELECT comptes_payeurs.IDcompte_payeur, mttPrest.Prest, mttRegl.Regl
            FROM comptes_payeurs
            LEFT JOIN
                    ( SELECT prestations.IDcompte_payeur, Sum(prestations.montant) AS Prest
                    FROM prestations
                    WHERE ( %s )
                    GROUP BY prestations.IDcompte_payeur)
                AS mttPrest
            ON comptes_payeurs.IDcompte_payeur = mttPrest.IDcompte_payeur
    
            LEFT JOIN
                    ( SELECT reglements.IDcompte_payeur, Sum(reglements.montant) AS Regl
                    FROM reglements %s
                    GROUP BY reglements.IDcompte_payeur)
                AS mttRegl
            ON comptes_payeurs.IDcompte_payeur = mttRegl.IDcompte_payeur
            WHERE comptes_payeurs.IDcompte_payeur IN %s
            ;""" % (fPrest, condRegl, fID)

        DB.ExecuterReq(req,MsgBox="OL_Soldes.Importation_anterieur")
        recordset = DB.ResultatReq()
        for IDcompte_payeur, total_prestations, total_reglements in recordset:
            dictSoldes[IDcompte_payeur]['debits'][age]= Nz(total_prestations)
            dictSoldes[IDcompte_payeur]['credits'][age]= Nz(total_reglements)
    DB.Close()

    # Récupération des titulaires de familles
    dictTitulaires = UTILS_Titulaires.GetTitulaires(listeIDpayeurs)
    
    # Traitement des données
    lstLstView = []
    for IDfamille in list(dictSoldes.keys()):

        # Mémorisation
        item = {"IDfamille" : IDfamille,
                    "solde" : dictSoldes[IDfamille]['solde'],}
        for age in range(nbannee):
            if age == nbannee-1:  code = "plus"
            else: code = "an" + str(age+1)
            debit = dictSoldes[IDfamille]['debits'][age]
            credits = sum(dictSoldes[IDfamille]['credits'])
            debitsAnte = sum(dictSoldes[IDfamille]['debits'][age:])
            # formule = MAX(0;MIN(debit de l'année;-SOMME(credits)+SOMME(debits >= age)))
            item[code] = max(0.0,min(debit, -credits + debitsAnte))
        lstLstView.append(Track(dictTitulaires, item))
    return lstLstView
                
                
class Track(object):
    def __init__(self, dictTitulaires, donnees):
        for key in list(donnees.keys()):
            setattr(self,"%s"%key,donnees["%s"%key])
        self.solde = donnees["solde"]

        if self.IDfamille in dictTitulaires :
            self.nomsTitulaires =  dictTitulaires[self.IDfamille]["titulairesSansCivilite"]
        else:
            self.nomsTitulaires = _("Sans titulaires")

# ----------------------------------------------------------------------------------------------------------------------------------------

class ListView(FastObjectListView):
    def __init__(self, *args, **kwds):
        # Récupération des paramètres perso
        self.selectionID = None
        self.selectionTrack = None
        self.criteres = ""
        self.itemSelected = False
        self.popupIndex = -1
        self.listeFiltres = []
        self.date = None
        # Initialisation du listCtrl
        FastObjectListView.__init__(self, *args, **kwds)
        # Binds perso
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnItemActivated)
        self.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)
        self.donnees = []
        self.InitObjectListView()

    def OnItemActivated(self,event):
        self.OuvrirFicheFamille(None)
                
    def InitModel(self, date, afficherDebit, afficherCredit, afficherNul, afficherCompta):
        self.donnees = Importation(date, afficherDebit, afficherCredit, afficherNul, afficherCompta)
            
    def InitObjectListView(self):            
        # Couleur en alternance des lignes
        self.oddRowsBackColor = "#F0FBED" 
        self.evenRowsBackColor = wx.Colour(255, 255, 255)
        self.useExpansionColumn = True

        def FormateMontant(montant):
            if montant == None : return ""
            return "%.2f" % (montant)

        def FormateSolde(montant):
            if montant == None :
                return ""
            if montant == 0.0 : 
                return "%.2f" % (montant)
            if montant > FloatToDecimal(0.0) :
                return "+ %.2f" % (montant)
            if montant < FloatToDecimal(0.0) :
                return "- %.2f" % (-montant)
        
        liste_Colonnes = [
            ColumnDefn(_("IDfamille"), "left", 80, "IDfamille", typeDonnee="entier"),
            ColumnDefn(_("Famille"), 'left', 200, "nomsTitulaires", typeDonnee="texte"),
            ColumnDefn(_("SoldeDû"), 'right', 110, "solde", typeDonnee="montant", stringConverter=FormateSolde),
            ColumnDefn(_("<1an"), 'right', 110, "an1", typeDonnee="montant", stringConverter=FormateMontant),
            ColumnDefn(_("2ans"), 'right', 110, "an2", typeDonnee="montant", stringConverter=FormateMontant),
            ColumnDefn(_("3ans"), 'right', 110, "an3", typeDonnee="montant", stringConverter=FormateMontant),
            ColumnDefn(_("4ans"), 'right', 110, "an4", typeDonnee="montant", stringConverter=FormateMontant),
            ColumnDefn(_("plus"), 'right', 110, "plus", typeDonnee="montant", stringConverter=FormateMontant),
            ]
        
        self.SetColumns(liste_Colonnes)
        self.SetEmptyListMsg(_("Aucun solde"))
        self.SetEmptyListMsgFont(wx.FFont(11, wx.DEFAULT, faceName="Tekton"))
        self.SetSortColumn(2)
        
    def MAJ(self, date=None, afficherDebit=True, afficherCredit=False, afficherNul=False, afficherCompta=True):
        if date:
            self.date = date
            self.InitModel(date, afficherDebit, afficherCredit, afficherNul, afficherCompta)
            self.SetObjects(self.donnees)
    ##        self.AjouteLigneTotal(listeNomsColonnes=["solde", "total_prestations", "total_reglements"])

    def Selection(self):
        return self.GetSelectedObjects()

    def OnContextMenu(self, event):
        """Ouverture du menu contextuel """        
        # Création du menu contextuel
        menuPop = wx.Menu()

        # Item Ouverture fiche famille
        item = wx.MenuItem(menuPop, 10, _("Ouvrir la fiche famille"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Famille.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.OuvrirFicheFamille, id=10)
        
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
    
    def GetDateStr(self):
        if self.date == None :
            return ""
        else :
            return _("> Situation au %s.") % DateEngFr(str(self.date))
        
    def Apercu(self, event):
        from Utils import UTILS_Printer
        prt = UTILS_Printer.ObjectListViewPrinter(self, titre=_("Liste des soldes"), intro=self.GetDateStr() , format="A", orientation=wx.PORTRAIT)
        prt.Preview()

    def Imprimer(self, event):
        from Utils import UTILS_Printer
        prt = UTILS_Printer.ObjectListViewPrinter(self, titre=_("Liste des soldes"), intro=self.GetDateStr() , format="A", orientation=wx.PORTRAIT)
        prt.Print()

    def OuvrirFicheFamille(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("familles_fiche", "consulter") == False : return
        if len(self.Selection()) == 0 :
            dlg = wx.MessageDialog(self, _("Vous n'avez sélectionné aucune fiche famille à ouvrir !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        IDfamille = self.Selection()[0].IDfamille
        from Dlg import DLG_Famille
        dlg = DLG_Famille.Dialog(self, IDfamille)
        if dlg.ShowModal() == wx.ID_OK:
            self.MAJ()
        dlg.Destroy()

    def ExportTexte(self, event):
        from Utils import UTILS_Export
        UTILS_Export.ExportTexte(self, titre=_("Liste des soldes"), autoriseSelections=False)
        
    def ExportExcel(self, event):
        from Utils import UTILS_Export
        UTILS_Export.ExportExcel(self, titre=_("Liste des soldes"), autoriseSelections=False)


# -------------------------------------------------------------------------------------------------------------------------------------------

class BarreRecherche(wx.SearchCtrl):
    def __init__(self, parent):
        wx.SearchCtrl.__init__(self, parent, size=(-1, -1), style=wx.TE_PROCESS_ENTER)
        self.parent = parent
        self.rechercheEnCours = False
        
        self.SetDescriptiveText(_("Rechercher..."))
        self.ShowSearchButton(True)
        
        self.listView = self.parent.ctrl_soldes
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
            "nomsTitulaires" : {"mode" : "nombre", "singulier" : "famille", "pluriel" : "familles", "alignement" : wx.ALIGN_CENTER},
            "solde" : {"mode" : "total"},
            "an1" : {"mode" : "total"},
            "an2" : {"mode" : "total"},
            "an3" : {"mode" : "total"},
            "an4" : {"mode" : "total"},
            "plus": {"mode" : "total"},
            }
        PanelAvecFooter.__init__(self, parent, ListView, kwargs, dictColonnes)

##class ListviewAvecFooter(PanelAvecFooter):
##    def __init__(self, parent):
##        dictColonnes = {
##            "nomsTitulaires" : {"mode" : "nombre", "singulier" : "famille", "pluriel" : "familles", "alignement" : wx.ALIGN_CENTER, "font" : wx.Font(8, wx.SWISS, wx.NORMAL, wx.BOLD)},
##            "solde" : {"mode" : "total", "font" : wx.Font(8, wx.SWISS, wx.NORMAL, wx.BOLD)},
##            "total_prestations" : {"mode" : "total", "font" : wx.Font(8, wx.SWISS, wx.NORMAL, wx.BOLD), "couleur" : wx.Colour(0, 0, 0), },
##            "total_reglements" : {"mode" : "texte", "texte" : _("Coucou !"), "font" : wx.Font(8, wx.SWISS, wx.NORMAL, wx.BOLD)},
##            }
##        PanelAvecFooter.__init__(self, parent, ListView, dictColonnes)


class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self, -1, name="test1")
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_1.Add(panel, 1, wx.ALL|wx.EXPAND)
        self.SetSizer(sizer_1)
        
        ctrl = ListviewAvecFooter(panel) 
        listview = ctrl.GetListview()
        listview.MAJ(datetime.date.today())
        
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_2.Add(ctrl, 1, wx.ALL|wx.EXPAND, 10)
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
