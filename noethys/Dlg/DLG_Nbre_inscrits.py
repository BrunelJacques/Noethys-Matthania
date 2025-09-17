#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#-----------------------------------------------------------
# Application :    Noethys branche Matthania
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS, JB
# Copyright:       (c) 2010-12 Ivan LUCAS, JB
# Licence:         Licence GNU GPL
#-----------------------------------------------------------

from Dlg import DLG_Parametres_nbre_inscrits
from Utils.UTILS_Traduction import _
import Chemins
import wx
import GestionDB
from Utils import UTILS_Config
import wx.lib.agw.ultimatelistctrl as ULC

COULEUR_TRAIT = wx.Colour(200, 200, 200)
COULEUR_TEXTE = "BLACK"
COULEUR_DISPONIBLE = "#E3FEDB"
COULEUR_ALERTE = "#FEFCDB"
COULEUR_COMPLET = "#F7ACB2"
COULEUR_GAUGE_FOND = "WHITE"

class Renderer_gauge(object):
    def __init__(self, parent):
        self.parent = parent
        self.hauteurGauge = 18
        self.seuil_alerte = self.parent.seuil_alerte
        self.nbrePlacesPrises = 0
        self.nbrePlacesDispo = 0
        self.nbrePlacesAttente = 0

    def DrawSubItem(self, dc, rect, line, highlighted, enabled):
        canvas = wx.Bitmap(rect.width, rect.height)
        mdc = wx.MemoryDC()
        mdc.SelectObject(canvas)
        
        # Dessin du fond
        if highlighted:
            mdc.SetBackground(wx.Brush(wx.systemSettings.GetColour(wx.SYS_COLOUR_HIGHLIGHT)))
        else:
            couleurFond = self.parent.couleurFond
            mdc.SetBackground(wx.Brush(couleurFond))
        mdc.Clear()
        
        # Dessin de la gauge
        self.DrawGauge(mdc, 0, 0, rect.width, rect.height)
        
        # Dessin du texte
        mdc.SetFont(wx.Font(7, wx.SWISS, wx.NORMAL, wx.NORMAL))
        if self.nbrePlacesPrises == 1 :
            texte = _("1 inscrit")
        else :
            texte = _("%d inscrits") % self.nbrePlacesPrises
        if self.nbrePlacesAttente > 0 :
            texte += _(" + %d en attente") % self.nbrePlacesAttente
        if self.nbrePlacesDispo > 0 :
            texte += _(" / %d places") % self.nbrePlacesDispo
        else :
            texte += _(" / places illimitées")
        textWidth, dummy = mdc.GetTextExtent(texte)
        mdc.SetTextForeground(COULEUR_TEXTE)
        #x = rect.width/2 - textWidth/2
        x = 0 + 4
        mdc.DrawText(texte, x, int(rect.height/2) - int(dummy/2))
        
        # Double buffering
        dc.SetClippingRegion(rect.x, rect.y, rect.width, rect.height)
        dc.Blit(rect.x+3, rect.y, rect.width-6, rect.height, mdc, 0, 0)
        dc.DestroyClippingRegion()
        
    def GetLineHeight(self):
        return self.hauteurGauge + 3

    def GetSubItemWidth(self):
        return 10

    def DrawGauge(self, dc, x, y, w, h):
        w -= 8

        # Gauge de fond
        dc.SetBrush(wx.Brush(COULEUR_GAUGE_FOND))
        dc.SetPen(wx.TRANSPARENT_PEN)
        dc.DrawRectangle(0, (int((h-self.hauteurGauge)/2)) , int(w), int(self.hauteurGauge))

        # Gauge d'inscriptions
        if self.nbrePlacesDispo != 0 :
            largeurGauge = 1.0 * self.nbrePlacesPrises / self.nbrePlacesDispo * w
        else :
            largeurGauge = w
        if largeurGauge > w :
            largeurGauge = w
        
        etat = "disponible"
        if self.nbrePlacesDispo == 0 :
            couleur = COULEUR_DISPONIBLE
        else :
            nbrePlacesRestantes = self.nbrePlacesDispo - self.nbrePlacesPrises
            if nbrePlacesRestantes > self.seuil_alerte : 
                etat = "disponible"
                couleur = COULEUR_DISPONIBLE
            if nbrePlacesRestantes > 0 and nbrePlacesRestantes <= self.seuil_alerte : 
                etat = "alerte"
                couleur = COULEUR_ALERTE
            if nbrePlacesRestantes <= 0 : 
                etat = "complet"
                couleur = COULEUR_COMPLET

        dc.SetBrush(wx.Brush(couleur))
        dc.SetPen(wx.Pen(COULEUR_TRAIT, 1))
        dc.DrawRectangle(0, (int((h-self.hauteurGauge)/2)) , int(largeurGauge), int(self.hauteurGauge))
        
        if etat == "alerte" :
            tailleImage = 16
            dc.DrawBitmap(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Attention.png"),
                                    wx.BITMAP_TYPE_ANY) ,
                          int(largeurGauge-tailleImage-2),
                          int((h-tailleImage)/2))

    def SetValeurs(self, nbrePlacesPrises=0, nbrePlacesDispo=0, nbrePlacesAttente=0):
        self.nbrePlacesPrises = nbrePlacesPrises
        self.nbrePlacesDispo = nbrePlacesDispo
        self.nbrePlacesAttente = nbrePlacesAttente

# ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
            
class CTRL(ULC.UltimateListCtrl):
    def __init__(self, parent, style=ULC.ULC_SINGLE_SEL | ULC.ULC_REPORT | ULC.ULC_NO_HEADER | ULC.ULC_HAS_VARIABLE_ROW_HEIGHT):
        ULC.UltimateListCtrl.__init__(self, parent, -1, agwStyle=style)
        self.parent = parent
        self.listeActivites = []
        
        self.couleurFond = wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW)
        # self.couleurFond = wx.SystemSettings.GetColour(wx.SYS_COLOUR_FRAMEBK)
        self.SetBackgroundColour(self.couleurFond)
        
        # Création des colonnes
        self.InsertColumn(0, _("Nom de l'activité"), width=200, format=ULC.ULC_FORMAT_RIGHT)
        self.InsertColumn(1, _("Nbre inscrits"), width=200, format=ULC.ULC_FORMAT_CENTRE)
        
        # Binds        
        self.Bind(wx.EVT_RIGHT_DOWN, self.OnContextMenu)
        self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)

    def OnLeftDown(self, event):
        pass

    def OnContextMenu(self, event):
        pass

    def MAJ(self, forcerActualisation=False):
        condition = ""
        
        # Recherche des paramètres
        activites = UTILS_Config.GetParametre("nbre_inscrits_parametre_activites", defaut=None)
        if activites and ("###" in activites ):
            label, activites = activites.split("###")
        if activites != None and activites != '':
            listeID = []
            for ID in activites.split(";") :
                    listeID.append(int(ID))
            condition = "WHERE inscriptions.IDactivite IN %s" % GestionDB.ConvertConditionChaine(listeID)
        else:
            condition = "WHERE 1 = 0"

        # Tri
        choixTri= UTILS_Config.GetParametre("nbre_inscrits_parametre_tri", 3)
        libelle,champTrie = DLG_Parametres_nbre_inscrits.CHOICES_TRI_ACTIVITES[choixTri]
        if isinstance(champTrie,str):
            tri = champTrie
        else: tri = ""

        # Sens
        choixSens = UTILS_Config.GetParametre("nbre_inscrits_parametre_sens", 1)
        if choixSens == 0:
            sens = ""
        else :
            sens = "DESC"
        order = ""
        if len(tri)>0:
            order = "ORDER BY %s %s"%(tri, sens)

        # Seuil d'alerte
        self.seuil_alerte = UTILS_Config.GetParametre("nbre_inscrits_parametre_alerte", 5)

        # Recherche des données
        DB = GestionDB.DB()
        if DB.echec > 0:
            return
        req = """SELECT activites.IDactivite, activites.nom, activites.abrege, activites.nbre_inscrits_max, COUNT(inscriptions.IDinscription) as nbreInscrits
        FROM activites
        LEFT JOIN inscriptions ON inscriptions.IDactivite = activites.IDactivite
        LEFT JOIN groupes_activites ON groupes_activites.IDactivite = activites.IDactivite
        %s
        GROUP BY activites.IDactivite
        %s
        ;""" % (condition, order)
        ret = DB.ExecuterReq(req,MsgBox="DLG_Nbre_inscrits.MAJ")
        listeDonnees = []
        if ret == "ok":
            listeDonnees = DB.ResultatReq()
            DB.Close()
        listeActivitesTemp = []

        def tauxRemplis(inscrits,places):
            if places == 0:
                if sens == "DESC":
                    txRemplis = -1.0
                else:
                    txRemplis = 101.0
            else:
                txRemplis = round(100 * float(inscrits) / float(places) ,2)
            # pour différencier les exequos sans places dispos, ajout de décimale sur nbre d'inscrits
            txRemplis += float(inscrits) / 100
            return  txRemplis

        for IDactivite, nom, abrege, nbre_inscrits_max, nbre_inscrits in listeDonnees :
            if nbre_inscrits_max == None : nbre_inscrits_max = 0
            if nbre_inscrits == None : nbre_inscrits = 0
            if nom == None : nom = _("Sans nom !")
            listeActivitesTemp.append({"IDactivite" : IDactivite,
                                       "nom" : nom,
                                       "abrege" : abrege,
                                       "nbrePlacesDispo" : nbre_inscrits_max,
                                       "nbrePlacesPrises" : nbre_inscrits,
                                       "txRemplis" : tauxRemplis(nbre_inscrits,nbre_inscrits_max),
                                       "nbrePlacesAttente" : 0}) # nbrePlacesAttente à coder plus tard
        def takeFirst(item):
            return item[0]

        if champTrie == 99:
            # composition de tuples dont [0] servira de tri
            lstActivitesPourTri = [ (x["txRemplis"],x) for x in listeActivitesTemp]
            if sens == "DESC":
                rev = True
            else: rev = False
            lstActivitesPourTri.sort(reverse=rev, key=takeFirst)
            # oublie la clé de tri pour refaire la liste initiale
            listeActivitesTemp = [y for (x,y) in lstActivitesPourTri]

        # Pour éviter l'actualisation de l'affichage si aucune modification des données
        if self.listeActivites != listeActivitesTemp or forcerActualisation == True :
            self.listeActivites = listeActivitesTemp
        else :
            return
        
        # MAJ du contrôle
        self.DeleteAllItems() 
        
        self.dictRenderers = {}
        index = 0
        for dictActivite in self.listeActivites :
            # Colonne Activité
            label = " " + dictActivite["nom"]
            self.InsertStringItem(index, label)
            self.SetItemData(index, dictActivite)
            
            # Colonne Gauge
            renderer = Renderer_gauge(self)
            renderer.SetValeurs(nbrePlacesPrises=dictActivite["nbrePlacesPrises"], nbrePlacesDispo=dictActivite["nbrePlacesDispo"], nbrePlacesAttente=dictActivite["nbrePlacesAttente"])
            self.dictRenderers[index] = renderer
            self.SetItemCustomRenderer(index, 1, renderer)
                
            index += 1
        
        # Ajuste la taille des colonnes
        self.SetColumnWidth(0, wx.LIST_AUTOSIZE)
        self.SetColumnWidth(1, ULC.ULC_AUTOSIZE_FILL)
        
        # Actualiser l'affichage pour éviter bug de positionnement
        try :
            self.DoLayout() 
        except :
            pass
            
    def Tests(self):
        """ UNIQUEMENT POUR TESTS : Test de mise à jour des gauges sur 50 """
        import random
        for index in range(0, self.GetItemCount()) :
            renderer = self.dictRenderers[index]
            nbrePlacesDispo = random.randint(0, 10)
            nbrePlacesPrises = random.randint(0, nbrePlacesDispo+1)
            nbrePlacesAttente = 0#random.randint(0, 1)
            renderer.SetValeurs(nbrePlacesPrises=nbrePlacesPrises, nbrePlacesDispo=nbrePlacesDispo, nbrePlacesAttente=nbrePlacesAttente)
            self.RefreshItem(index)

# ----------------------------------------------------------------------------------------------------------------------        

class Panel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, id=-1, style=wx.TAB_TRAVERSAL)
        self.parent = parent

        # Messages
        self.ctrl_inscriptions = CTRL(self)
        
        # Commandes
        self.bouton_parametres = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Mecanisme.png"), wx.BITMAP_TYPE_PNG))
        self.bouton_parametres.SetToolTip(_("Cliquez ici pour modifier les paramètres d'affichage"))
        self.bouton_outils = wx.BitmapButton(self, -1,wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Outils.png"), wx.BITMAP_TYPE_PNG))
        self.bouton_outils.SetToolTip(_("Cliquez ici pour accéder aux outils"))

        self.__do_layout()
        
        # Binds
        self.Bind(wx.EVT_BUTTON, self.OnBoutonParametres, self.bouton_parametres)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonOutils, self.bouton_outils)

    def __do_layout(self):
        sizer_base = wx.BoxSizer(wx.VERTICAL)
        grid_sizer = wx.FlexGridSizer(rows=2, cols=2, vgap=5, hgap=5)
        grid_sizer.Add(self.ctrl_inscriptions, 1, wx.EXPAND|wx.TOP|wx.LEFT|wx.BOTTOM, 10)
        grid_sizer_boutons = wx.FlexGridSizer(rows=4, cols=1, vgap=5, hgap=5)
        grid_sizer_boutons.Add(self.bouton_parametres, 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_outils, 0, 0, 0)
        grid_sizer.Add(grid_sizer_boutons, 1, wx.EXPAND|wx.TOP|wx.RIGHT|wx.BOTTOM, 10)
        grid_sizer.AddGrowableRow(0)
        grid_sizer.AddGrowableCol(0)
        self.SetSizer(grid_sizer)
        self.Layout()
    
    def MAJ(self):
        self.ctrl_inscriptions.MAJ() 

    def OnBoutonParametres(self, event):
        from Dlg import DLG_Parametres_nbre_inscrits
        dlg = DLG_Parametres_nbre_inscrits.DlgActivites(self)
        reponse = dlg.ShowModal()
        if reponse == wx.ID_OK :
            self.ctrl_inscriptions.MAJ(forcerActualisation=True) 
        
    def OnBoutonOutils(self, event):
        # Création du menu contextuel
        menuPop = wx.Menu()

        # Item Actualiser
        item = wx.MenuItem(menuPop, 10, _("Actualiser"))
        item.SetBitmap(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Actualiser2.png"), wx.BITMAP_TYPE_PNG))
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.Actualiser, id=10)

        menuPop.AppendSeparator()
        
        item = wx.MenuItem(menuPop, 20, _("Aide"), _("Aide"))
        item.SetBitmap(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Aide.png"), wx.BITMAP_TYPE_PNG))
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.Aide, id=20)

        self.PopupMenu(menuPop)
        menuPop.Destroy()
    
    def Actualiser(self, event):
        self.ctrl_inscriptions.MAJ(forcerActualisation=True) 
    
    def Aide(self, event):
        from Utils import UTILS_Aide
        UTILS_Aide.Aide("Villesetcodespostaux")

# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------

class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self, -1)
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_1.Add(panel, 1, wx.ALL|wx.EXPAND)
        self.SetSizer(sizer_1)

        self.ctrl = Panel(panel)
        self.ctrl.MAJ() 
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_2.Add(self.ctrl, 1, wx.ALL|wx.EXPAND, 4)
        panel.SetSizer(sizer_2)
        self.Layout()
        self.CentreOnScreen()

if __name__ == '__main__':
    app = wx.App(0)
    #wx.InitAllImageHandlers()
    frame_1 = MyFrame(None, -1, "TEST", size=(800, 400))
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()