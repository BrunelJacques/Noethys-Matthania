#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys branche Matthania,
# seulement modifié pour chaîner sur OL_Perstations
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS, JB
# Copyright:       (c) 2010-11 Ivan LUCAS, JB
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------


from Utils.UTILS_Traduction import _
import wx
import Chemins
from Ol import OL_Prestations
import wx.lib.agw.hyperlink as Hyperlink
from Utils import UTILS_Utilisateurs
from Utils import UTILS_Config
from Utils.UTILS_Decimal import FloatToDecimal as FloatToDecimal
SYMBOLE = UTILS_Config.GetParametre("monnaie_symbole", "€")

class CTRL_Solde(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, id=-1, name="panel_solde", style=wx.SUNKEN_BORDER | wx.TAB_TRAVERSAL,
                          size=(150, 40))
        self.parent = parent

        # Solde du compte
        self.ctrl_solde = wx.StaticText(self, -1, "0.00 %s " % SYMBOLE)
        font = wx.Font(11, wx.SWISS, wx.NORMAL, wx.BOLD)
        self.ctrl_solde.SetFont(font)

        # Layout
        grid_sizer_base = wx.FlexGridSizer(rows=1, cols=1, vgap=5, hgap=5)
        grid_sizer_base.Add(self.ctrl_solde, 1, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL | wx.ALL, 10)
        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)
        grid_sizer_base.AddGrowableCol(0)
        grid_sizer_base.AddGrowableRow(0)
        # self.SetToolTip(u"Solde")
        self.ctrl_solde.SetToolTip("Solde")

    def SetSolde(self, montant=FloatToDecimal(0.0)):
        """ MAJ integrale du controle avec MAJ des donnees """
        if montant > FloatToDecimal(0.0):
            label = "+ %.2f %s" % (montant, SYMBOLE)
        elif montant == FloatToDecimal(0.0):
            label = "0.00 %s" % SYMBOLE
        else:
            label = "- %.2f %s" % (-montant, SYMBOLE)
        self.SetBackgroundColour("#C4BCFC")  # Bleu
        self.ctrl_solde.SetLabel(label)
        self.Layout()
        self.Refresh()

class Hyperlien_regroupement(Hyperlink.HyperLinkCtrl):
    def __init__(self, parent, id=-1, label="", infobulle="", URL="", listeChoix=[], indexChoixDefaut=None, size=(-1, -1), pos=(0, 0)):
        Hyperlink.HyperLinkCtrl.__init__(self, parent, id, label, URL=URL, size=size, pos=pos)
        self.parent = parent
        self.listeChoix = listeChoix
        self.indexChoixDefaut = indexChoixDefaut

        if self.GetGrandParent().GetName() == "notebook" :
            self.SetBackgroundColour(self.GetGrandParent().GetThemeBackgroundColour())

        self.URL = URL
        self.AutoBrowse(False)
        self.SetColours("BLUE", "BLUE", "BLUE")
        self.SetUnderlines(False, False, True)
        self.SetBold(False)
        self.EnableRollover(True)
        self.SetToolTip(wx.ToolTip(infobulle))
        self.UpdateLink()
        self.DoPopup(False)
        self.Bind(Hyperlink.EVT_HYPERLINK_LEFT, self.OnLeftLink)
    
    def SetListeChoix(self, listeChoix=[]):
        self.listeChoix = listeChoix
        
    def OnLeftLink(self, event):
        dlg = wx.SingleChoiceDialog(self, _("Choisissez un item dans la liste :"), _("Choix"), self.listeChoix, wx.CHOICEDLG_STYLE)
        if self.indexChoixDefaut != None and self.indexChoixDefaut < len(self.listeChoix) :
            dlg.SetSelection(self.indexChoixDefaut)
        if dlg.ShowModal() == wx.ID_OK:
            indexChoix = dlg.GetSelection()
            # Modification du label de l'hyperlien
            self.SetLabel(self.listeChoix[indexChoix])
            self.indexChoixDefaut = indexChoix
            # MAJ du listView
            self.parent.ctrl_prestations.SetColonneTri(indexChoix+1)
##            self.parent.MAJtotal()
            self.parent.grid_sizer_options.Layout() 
            self.parent.Refresh() 
        dlg.Destroy()
        self.UpdateLink()
# -----------------------------------------------------------------------------------------------------------------------

class Hyperlien_periodes(Hyperlink.HyperLinkCtrl):
    def __init__(self, parent, id=-1, label="", infobulle="", URL="", size=(-1, -1), pos=(0, 0)):
        Hyperlink.HyperLinkCtrl.__init__(self, parent, id, label, URL=URL, size=size, pos=pos)
        self.parent = parent

        if self.GetGrandParent().GetName() == "notebook" :
            self.SetBackgroundColour(self.GetGrandParent().GetThemeBackgroundColour())

        self.URL = URL
        self.AutoBrowse(False)
        self.SetColours("BLUE", "BLUE", "BLUE")
        self.SetUnderlines(False, False, True)
        self.SetBold(False)
        self.EnableRollover(True)
        self.SetToolTip(wx.ToolTip(infobulle))
        self.UpdateLink()
        self.DoPopup(False)
        self.Bind(Hyperlink.EVT_HYPERLINK_LEFT, self.OnLeftLink)
        
    def OnLeftLink(self, event):
        from Dlg import DLG_Choix_periodes
        dlg = DLG_Choix_periodes.Dialog(self)
        if dlg.ShowModal() == wx.ID_OK:
            listePeriodes = dlg.GetListePeriodes()
            # Label
            if listePeriodes == None :
                self.SetLabel(_("Toutes les périodes"))
            else:
                self.SetLabel(_("Sélection"))
            # MAJ
            self.parent.ctrl_prestations.SetListePeriodes(listePeriodes)
##            self.parent.MAJtotal()
            self.parent.grid_sizer_options.Layout() 
            self.parent.Refresh() 
        dlg.Destroy()
        self.UpdateLink()
# -----------------------------------------------------------------------------------------------------------------------

class Hyperlien(Hyperlink.HyperLinkCtrl):
    def __init__(self, parent, id=-1, label="", infobulle="", URL="", listeChoix=[], indexChoixDefaut=None, champFiltre="", labelDefaut="", size=(-1, -1), pos=(0, 0)):
        Hyperlink.HyperLinkCtrl.__init__(self, parent, id, label, URL=URL, size=size, pos=pos)
        self.parent = parent
        self.listeChoix = listeChoix
        self.indexChoixDefaut = indexChoixDefaut
        self.champFiltre = champFiltre
        self.labelDefaut = labelDefaut

        if self.GetGrandParent().GetName() == "notebook" :
            self.SetBackgroundColour(self.GetGrandParent().GetThemeBackgroundColour())

        self.URL = URL
        self.AutoBrowse(False)
        self.SetColours("BLUE", "BLUE", "BLUE")
        self.SetUnderlines(False, False, True)
        self.SetBold(False)
        self.EnableRollover(True)
        self.SetToolTip(wx.ToolTip(infobulle))
        self.UpdateLink()
        self.DoPopup(False)
        self.Bind(Hyperlink.EVT_HYPERLINK_LEFT, self.OnLeftLink)
    
    def SetListeChoix(self, listeChoix=[]):
        self.listeChoix = listeChoix
        
    def OnLeftLink(self, event):
        self.listeChoix.sort()
        listeItems = [self.labelDefaut,]
        for label, ID in self.listeChoix :
            listeItems.append(label)
        dlg = wx.SingleChoiceDialog(self, _("Choisissez un filtre dans la liste suivante :"), _("Filtrer la liste"), listeItems, wx.CHOICEDLG_STYLE)
        if self.indexChoixDefaut != None and self.indexChoixDefaut < len(self.listeChoix) :
            dlg.SetSelection(self.indexChoixDefaut)
        if dlg.ShowModal() == wx.ID_OK:
            indexChoix = dlg.GetSelection() - 1
            # Modification du label de l'hyperlien
            if indexChoix == -1 :
                self.SetLabel(self.labelDefaut)
                self.indexChoixDefaut = None
                ID = None
            else:
                self.SetLabel(self.listeChoix[indexChoix][0])
                self.indexChoixDefaut = self.listeChoix[indexChoix][1]
                ID = self.listeChoix[indexChoix][1]
            # MAJ
            self.parent.ctrl_prestations.SetFiltre(self.champFiltre, ID)
##            self.parent.MAJtotal()
            self.parent.grid_sizer_options.Layout() 
            self.parent.Refresh() 
        dlg.Destroy()
        self.UpdateLink()
# -----------------------------------------------------------------------------------------------------------------------

class Panel(wx.Panel):
    def __init__(self, parent, IDfamille=None):
        wx.Panel.__init__(self, parent, id=-1, name="panel_prestations", style=wx.TAB_TRAVERSAL)
        self.parent = parent
        self.IDfamille = IDfamille
        
        self.staticbox_prestations = wx.StaticBox(self, -1, _("Prestations"))

        # OL Prestations JB
        self.ctrl_solde = CTRL_Solde(self)
        #self.ctrl_solde.SetSolde(0.00)
        self.listviewAvecFooter = OL_Prestations.ListviewAvecFooter(self, kwargs={"IDfamille" : IDfamille})
        self.ctrl_prestations = self.listviewAvecFooter.GetListview()
        self.olv = self.listviewAvecFooter.ctrl_listview
        self.ctrl_recherche = OL_Prestations.CTRL_Outils(self, listview=self.ctrl_prestations, afficherCocher=True)
        self.ctrl_recherche.SetBackgroundColour((255, 255, 255))

        # Commandes boutons
        self.bouton_ajouter = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Ajouter.png"), wx.BITMAP_TYPE_ANY))
        self.bouton_modifier = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Modifier.png"), wx.BITMAP_TYPE_ANY))
        self.bouton_supprimer = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Supprimer.png"), wx.BITMAP_TYPE_ANY))
        self.bouton_imprimer = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Imprimante.png"), wx.BITMAP_TYPE_ANY))

        # Binds
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAjouter, self.bouton_ajouter)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonModifier, self.bouton_modifier)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonSupprimer, self.bouton_supprimer)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonImprimer, self.bouton_imprimer)
        self.olv.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnActivated)
        self.olv.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnActivated)
        self.olv.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.OnActivated)
        #self.olv.Bind(wx.EVT_COMMAND_LEFT_CLICK, self.OnSwapCheck)
        self.olv.Bind(wx.EVT_CHOICE, self.OnActivated)

        # Propriétés
        self.bouton_ajouter.SetToolTip(_("Cliquez ici pour saisir une prestation"))
        self.bouton_modifier.SetToolTip(_("Cliquez ici pour modifier la prestation sélectionnée"))
        self.bouton_supprimer.SetToolTip(_("Cliquez ici pour supprimer la prestation sélectionnée"))

        # Layout
        grid_sizer_base = wx.FlexGridSizer(rows=1, cols=1, vgap=5, hgap=5)
        staticbox_prestations = wx.StaticBoxSizer(self.staticbox_prestations,wx.VERTICAL)
        grid_sizer_prestations = wx.FlexGridSizer(rows=2, cols=2, vgap=5, hgap=5)
        
        grid_sizer_prestations.Add(self.listviewAvecFooter, 1, wx.EXPAND, 0)
        
        grid_sizer_boutons = wx.FlexGridSizer(rows=5, cols=1, vgap=5, hgap=5)
        grid_sizer_boutons.Add(self.bouton_ajouter, 0, wx.ALL, 0)
        grid_sizer_boutons.Add(self.bouton_modifier, 0, wx.ALL, 0)
        grid_sizer_boutons.Add(self.bouton_supprimer, 0, wx.ALL, 0)
        grid_sizer_boutons.Add( (10, 10), 0, wx.ALL, 0)
        grid_sizer_boutons.Add(self.bouton_imprimer, 0, wx.ALL, 0)
        grid_sizer_prestations.Add(grid_sizer_boutons, 1, wx.ALL, 0)
        
        grid_sizer_prestations.AddGrowableCol(0)
        grid_sizer_prestations.AddGrowableRow(0)
        staticbox_prestations.Add(grid_sizer_prestations, 1, wx.EXPAND|wx.ALL, 5)

        grid_sizer_ligneBas = wx.FlexGridSizer(rows=1, cols=2, vgap=5, hgap=5)
        grid_sizer_ligneBas.Add(self.ctrl_recherche, 0, wx.EXPAND|wx.ALL, 0)
        grid_sizer_ligneBas.Add(self.ctrl_solde, 0, wx.EXPAND|wx.ALL, 0)
        grid_sizer_ligneBas.AddGrowableCol(0)

        staticbox_prestations.Add(grid_sizer_ligneBas, 0, wx.EXPAND|wx.ALL, 5)

        grid_sizer_base.Add(staticbox_prestations, 1, wx.EXPAND|wx.ALL, 5)

        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)
        grid_sizer_base.AddGrowableCol(0)
        grid_sizer_base.AddGrowableRow(0)
    
    def OnSwapCheck(self,event):
        if self.olv.IsChecked(self.olv.GetSelectedObject()):
            self.olv.SetCheckState(self.olv.GetSelectedObject(),False)
        else:
            self.olv.SetCheckState(self.olv.GetSelectedObject(),True)
        self.OnActivated(event)

    def OnActivated(self,event):
        self.olv.Refresh()
        mtt = 0.0
        for obj in self.olv.GetObjects():
            if self.olv.IsChecked(obj) == True:
                mtt += float(obj.montant)
        self.ctrl_solde.SetSolde(mtt)
        self.olv.Refresh()
        self.Refresh()

    def OnBoutonAjouter(self, event):
        self.ctrl_prestations.Ajouter(None)

    def OnBoutonModifier(self, event):
        self.ctrl_prestations.Modifier(None)

    def OnBoutonSupprimer(self, event):
        self.ctrl_prestations.Supprimer(None)

    def OnBoutonImprimer(self, event):
        self.ctrl_prestations.Imprimer(None)

    def OnBoutonImprimer(self, event):
        if len(self.ctrl_prestations.Selection()) == 0:
            noSelection = True
        else:
            noSelection = False
            ID = self.ctrl_prestations.Selection()[0].IDprestation
                
        # Création du menu contextuel
        menuPop = wx.Menu()
        
        # Item Apercu avant impression
        item = wx.MenuItem(menuPop, 20, _("Aperçu avant impression"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Apercu.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.Apercu, id=20)
        
        # Item Imprimer
        item = wx.MenuItem(menuPop, 30, _("Imprimer"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Imprimante.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.Imprimer, id=30)
        
        self.PopupMenu(menuPop)
        menuPop.Destroy()

    def Apercu(self, event):
        self.ctrl_prestations.Apercu(None)

    def Imprimer(self, event):
        self.ctrl_prestations.Imprimer(None)

    """def OnCheckRegroupement(self, event):
        if self.ctrl_regroupement.GetValue() == True :
            self.hyper_regroupement.Enable(True)
            self.ctrl_prestations.SetShowGroups(True)
        else:
            self.hyper_regroupement.Enable(False)
            self.ctrl_prestations.SetShowGroups(False)"""

    def IsLectureAutorisee(self):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("familles_prestations", "consulter", afficheMessage=False) == False : 
            return False
        return True

    def MAJ(self):
        """ MAJ integrale du controle avec MAJ des donnees """
        self.ctrl_prestations.MAJ() 
        self.Refresh()
        
    def MAJtotal(self):
        self.ctrl_total.SetLabel(_("Total : %.2f %s") % (self.ctrl_prestations.GetTotal(), SYMBOLE))
            
    def ValidationData(self):
        """ Return True si les données sont valides et pretes à être sauvegardées """
        return True
    
    def Sauvegarde(self):
        pass


class Dialog(wx.Dialog):
    def __init__(self, parent, IDfamille= 1,size=(800, 500),titre=_("Gestion des prestations ! pointez puis supprimez...")):
        wx.Dialog.__init__(self, parent, -1,size= size, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX)
        self.SetTitle(titre)
        self.panel = Panel(self,IDfamille=IDfamille)
        self.panel.MAJ()

    def __do_layout(self):
        gridsizer_base = wx.FlexGridSizer(rows=1, cols=1, vgap=0, hgap=0)
        gridsizer_base.Add(self.panel, 1, wx.EXPAND, 0)
        self.Layout()
        self.CenterOnScreen()


class MyFrame(wx.Frame):
    def __init__(self, IDfamille, *args, **kwds):
        wx.Frame.__init__(self,IDfamille, *args, **kwds)
        panel = wx.Panel(self, -1)
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_1.Add(panel, 1, wx.ALL|wx.EXPAND)
        self.SetSizer(sizer_1)
        self.ctrl= Panel(panel, IDfamille)
        self.ctrl.MAJ() 
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_2.Add(self.ctrl, 1, wx.ALL|wx.EXPAND, 4)
        panel.SetSizer(sizer_2)
        self.Layout()
        self.CentreOnScreen()

if __name__ == '__main__':
    app = wx.App(0)
    #wx.InitAllImageHandlers()
    frame_1 = MyFrame( None, 1861, size=(800, 400))
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()