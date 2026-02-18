#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#-----------------------------------------------------------
# Application :    Noethys, Matthania
# Auteur:          Ivan LUCAS, JB, Jacques Brunel
# Modifs sur gestion des Prix,
#-----------------------------------------------------------

from Utils.UTILS_Traduction import _
import Chemins
import wx
import datetime
import GestionDB
from Dlg import DLG_InscriptionMenu

from Ctrl.CTRL_ObjectListView import FastObjectListView, ColumnDefn, Filter


TAILLE_IMAGE = (40, 40)
LOGO_ORGANISATEUR = None

def RecadreImg(img=None):
    # Recadre l'image en fonction de la taille du staticBitmap
    tailleMaxi = max(TAILLE_IMAGE)
    largeur, hauteur = img.GetSize()
    if max(largeur, hauteur) > tailleMaxi :
        if largeur > hauteur :
            hauteur = hauteur * tailleMaxi / largeur
            largeur = tailleMaxi
        else:
            largeur = largeur * tailleMaxi / hauteur
            hauteur = tailleMaxi
    img.Rescale(width=largeur, height=hauteur, quality=wx.IMAGE_QUALITY_HIGH)
    position = (((TAILLE_IMAGE[0]/2.0) - (largeur/2.0)), ((TAILLE_IMAGE[1]/2.0) - (hauteur/2.0)))
    img.Resize(TAILLE_IMAGE, position, 255, 255, 255)
    return img

class Track(object):
    def __init__(self, parent, donnees):
        self.IDinscription = donnees[0]
        self.IDindividu = donnees[1]
        self.IDfamille = donnees[2]
        self.IDactivite = donnees[3]
        self.IDgroupe = donnees[4]
        self.IDcategorie_tarif = donnees[5]
        self.date_inscription = donnees[6]
        self.nom_activite = donnees[7]
        self.nom_groupe = donnees[8]
        self.nom_categorie = donnees[9]
        self.parti = donnees[10]
        self.date_debut = donnees[11]
        self.date_fin = donnees[12]

        # Nom des titulaires de famille
        self.nomTitulaires = _("IDfamille n°%d") % self.IDfamille
        if parent.dictFamillesRattachees != None :
            if self.IDfamille in parent.dictFamillesRattachees : 
                self.nomTitulaires = parent.dictFamillesRattachees[self.IDfamille]["nomsTitulaires"]

        # Validité de la pièce
        if str(datetime.date.today()) <= self.date_fin and self.parti != 1 :
            self.valide = True
        else:
            self.valide = False
    #fin Track

class ListView(FastObjectListView):
    def __init__(self,parent, *args, **kwds):
        # Récupération des paramètres perso
        #(IDindividu=IDindividu, dictFamillesRattachees=self.dictFamillesRattachees)
        self.module="OL_IndividuInscriptions.ListView"
        self.IDindividu = kwds.pop("IDindividu", None)
        self.parent = parent
        self.dictFamillesRattachees = kwds.pop("dictFamillesRattachees", {} )
        self.activeDoubleclick = kwds.pop("activeDoubleclick", True)
        self.nbreFamilles = 0
        self.selectionID = None
        self.selectionTrack = None
        self.criteres = ""
        self.itemSelected = False
        self.popupIndex = -1
        self.listeFiltres = []
        self.listeListeView = []
        FastObjectListView.__init__(self, *args, **kwds)
        # Binds perso
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnItemActivated)
        self.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)

        #fGest = GestionInscription.Forfaits(self)
        self.GetTracks()
        self.InitObjectListView()
        # Recherche si l'individu est rattaché à d'autres familles
        self.listeNoms = []
        self.listeFamille = []
        for IDfamille, dictFamille in self.dictFamillesRattachees.items() :
            self.listeFamille.append(IDfamille)
            self.listeNoms.append(dictFamille["nomsTitulaires"])
        self.IDfamille = self.parent.parent.IDfamille

    def OnItemActivated(self,event):
        self.Modifier(None)

    def InitModel(self):
        self.donnees = self.GetTracks()

    # groupé avec def InitModel(self):
    def GetTracks(self):
        """ Récupération des données """
        listeID = None
        DB = GestionDB.DB()
        req = """SELECT IDinscription, IDindividu, IDfamille,
        inscriptions.IDactivite, inscriptions.IDgroupe, inscriptions.IDcategorie_tarif, date_inscription,
        activites.nom, groupes.nom, categories_tarifs.nom,
        inscriptions.parti, activites.date_debut, activites.date_fin
        FROM inscriptions
        LEFT JOIN activites ON inscriptions.IDactivite=activites.IDactivite
        LEFT JOIN groupes ON inscriptions.IDgroupe=groupes.IDgroupe
        LEFT JOIN categories_tarifs ON inscriptions.IDcategorie_tarif=categories_tarifs.IDcategorie_tarif
        WHERE IDindividu=%d
        ORDER BY activites.nom; """ % self.IDindividu
        DB.ExecuterReq(req,MsgBox="ExecuterReq")
        listeDonnees = DB.ResultatReq()
        DB.Close()
        listeListeView = []
        listeIDfamilles = []
        for item in listeDonnees :
            IDfamille = item[2]
            if IDfamille not in listeIDfamilles :
                listeIDfamilles.append(IDfamille)
            valide = True
            if listeID != None :
                if item[0] not in listeID :
                    valide = False
            if valide == True :
                track = Track(self, item)
                listeListeView.append(track)
                if self.selectionID == item[0] :
                    self.selectionTrack = track
        self.nbreFamilles = len(listeIDfamilles)
        self.listeListeView = listeListeView
        # fin GetTrack

    def InitObjectListView(self):            
        # Couleur en alternance des lignes
        self.oddRowsBackColor = "#F0FBED" 
        self.evenRowsBackColor = wx.Colour(255, 255, 255)
        self.useExpansionColumn = True

        def DateEngFr(textDate):
            if textDate != None :
                text = str(textDate[8:10]) + "/" + str(textDate[5:7]) + "/" + str(textDate[:4])
            else:
                text = ""
            return text

        def rowFormatter(listItem, track):
            if track.valide == False :
                listItem.SetTextColour((180, 180, 180))

        if self.nbreFamilles > 1 :
            liste_Colonnes = [
                ColumnDefn(_("ID"), "left", 0, "IDinscription", typeDonnee="entier"),
                ColumnDefn(_("Date"), 'center', 70, "date_inscription", typeDonnee="date", stringConverter=DateEngFr),
                ColumnDefn(_("Nom de l'activité"), 'left', 110, "nom_activite", typeDonnee="texte", isSpaceFilling=True),
                ColumnDefn(_("Groupe"), 'left', 80, "nom_groupe", typeDonnee="texte"),
                ColumnDefn(_("Catégorie de tarifs"), 'left', 110, "nom_categorie_tarif", typeDonnee="texte"),
                ColumnDefn(_("Famille"), 'left', 110, "nomTitulaires", typeDonnee="texte"),
                ]
        else:
            liste_Colonnes = [
                ColumnDefn(_("ID"), "left", 0, "IDinscription", typeDonnee="entier"),
                ColumnDefn(_("Date"), 'center', 70, "date_inscription", typeDonnee="date", stringConverter=DateEngFr),
                ColumnDefn(_("Nom de l'activité"), 'left', 160, "nom_activite", typeDonnee="texte", isSpaceFilling=True),
                ColumnDefn(_("Groupe"), 'left', 100, "nom_groupe", typeDonnee="texte"),
                ColumnDefn(_("Catégorie de tarifs"), 'left', 100, "nom_categorie_tarif", typeDonnee="texte"),
                ]

        self.rowFormatter = rowFormatter
        self.SetColumns(liste_Colonnes)
        self.SetEmptyListMsg(_("Aucune activité"))
        self.SetEmptyListMsgFont(wx.FFont(11, wx.DEFAULT, faceName="Tekton"))
        self.SetSortColumn(self.columns[1],ascending=False)
        self.SetObjects(self.listeListeView)

    def Ajouter(self,event):
        dlg= DLG_InscriptionMenu.DlgMenu(self,self.Selection(),"ajouter",IDindividu=self.IDindividu,
                                          dictFamillesRattachees=self.dictFamillesRattachees)

    def Modifier(self,event):
        dlg= DLG_InscriptionMenu.DlgMenu(self,self.Selection(),"modifier",IDindividu=self.IDindividu,
                                         dictFamillesRattachees=self.dictFamillesRattachees)

    def Supprimer(self,event):
        dlg= DLG_InscriptionMenu.DlgMenu(self,self.Selection(),"supprimer",IDindividu=self.IDindividu, dictFamillesRattachees=self.dictFamillesRattachees)

    def MAJ(self, ID=None):
        if ID != None :
            self.selectionID = ID
        else:
            self.selectionID = None
        self.selectionTrack = None
        self.GetTracks()
        self.InitObjectListView()
        # Sélection d'un item
        if self.selectionTrack != None :
            self.SelectObject(self.selectionTrack, deselectOthers=True, ensureVisible=True)
        self.selectionID = None
        self.selectionTrack = None
        self._ResizeSpaceFillingColumns() 
    
    def Selection(self):
        return self.GetSelectedObjects()

    def OnContextMenu(self, event):
        """Ouverture du menu contextuel """
        if len(self.Selection()) == 0:
            noSelection = True
        else:
            noSelection = False
            ID = self.Selection()[0].IDinscription
                
        # Création du menu contextuel
        menuPop = wx.Menu()

        # Item Modifier
        item = wx.MenuItem(menuPop, 10, _("Ajouter"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Ajouter.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.Ajouter, id=10)

        # Item Ajouter
        item = wx.MenuItem(menuPop, 20, _("Modifier"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Modifier.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.Modifier, id=20)
        if noSelection == True : item.Enable(False)
        
        # Item Supprimer
        item = wx.MenuItem(menuPop, 30, _("Supprimer"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Supprimer.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.Supprimer, id=30)
        if noSelection == True : item.Enable(False)
                
        menuPop.AppendSeparator()

        # Item Editer Confirmation d'inscription
        item = wx.MenuItem(menuPop, 60, _("Editer une confirmation d'inscription (PDF)"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Apercu.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.EditerConfirmation, id=60)
        if noSelection == True : item.Enable(False)
        
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
        prt = UTILS_Printer.ObjectListViewPrinter(self, titre=_("Liste des inscriptions"), format="A", orientation=wx.PORTRAIT)
        prt.Preview()

    def Imprimer(self, event):
        from Utils import UTILS_Printer
        prt = UTILS_Printer.ObjectListViewPrinter(self, titre=_("Liste des inscriptions"), format="A", orientation=wx.PORTRAIT)
        prt.Print()

    def ExportTexte(self, event):
        from Utils import UTILS_Export
        UTILS_Export.ExportTexte(self, titre=_("Liste des inscriptions"))
        
    def ExportExcel(self, event):
        from Utils import UTILS_Export
        UTILS_Export.ExportExcel(self, titre=_("Liste des inscriptions"))

    def GetListeActivites(self):
        """ Retourne la liste des activités sur lesquelles l'individu est inscrit """
        """ Sert pour le ctrl DLG_Individu_inscriptions (saisir d'un forfait daté) """
        listeActivites = []
        for track in self.listeListeView:
            listeActivites.append(track.IDactivite)
        listeActivites.sort()
        return listeActivites

    def EditerConfirmation(self, event):
        if len(self.Selection()) == 0 :
            dlg = wx.MessageDialog(self, _("Vous n'avez sélectionné aucune inscription dans la liste !"), _("Erreur"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        self.IDinscription = self.Selection()[0].IDinscription
        from Dlg import DLG_Impression_inscription
        dlg = DLG_Impression_inscription.Dialog(self, IDinscription= self.IDinscription)
        dlg.ShowModal()
        dlg.Destroy()

# -------------------------------------------------------------------------------------------------------------------------------------
class BarreRecherche(wx.SearchCtrl):
    def __init__(self, parent):
        wx.SearchCtrl.__init__(self, parent, size=(-1, -1), style=wx.TE_PROCESS_ENTER)
        self.parent = parent
        self.rechercheEnCours = False
        
        self.SetDescriptiveText(_("Rechercher une inscription..."))
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

class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self, -1, name="test1")
        self.IDindividu = 10175
        self.dictFamillesRattachees = {6163: {'listeNomsTitulaires': ['ABALAIN Jessica'], 'nomsTitulaires': 'ABALAIN Jessica', 'IDcompte_payeur': 6163, 'nomCategorie': 'repr\xe9sentant', 'IDcategorie': 1}}
        self.myOlv = ListView(panel, id=-1, IDindividu=self.IDindividu, dictFamillesRattachees=self.dictFamillesRattachees, name="OL_test", style=wx.LC_REPORT|wx.SUNKEN_BORDER|wx.LC_SINGLE_SEL|wx.LC_HRULES|wx.LC_VRULES)
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_1.Add(panel, 1, wx.ALL|wx.EXPAND)
        self.SetSizer(sizer_1)
        self.myOlv.MAJ()
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_2.Add(self.myOlv, 1, wx.ALL|wx.EXPAND, 4)
        panel.SetSizer(sizer_2)
        self.Layout()
        self.myOlv.Ajouter(wx.EVT_BUTTON)

if __name__ == '__main__':
    app = wx.App(0)
    #wx.InitAllImageHandlers()
    frame_1 = MyFrame(None, -1, "OL TEST")
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()
