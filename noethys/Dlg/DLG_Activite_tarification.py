#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#-----------------------------------------------------------
# Application :    Noethys branche Matthania
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS, JB
# Copyright:       (c) 2010-11 Ivan LUCAS, JB
# Licence:         Licence GNU GPL
#-----------------------------------------------------------


from Utils.UTILS_Traduction import _
import wx
import Chemins
from Ol import OL_Tarifs
from Ol import OL_Categories_tarifs

class Panel(wx.Panel):
    def __init__(self, parent, IDactivite=None,**kwds):
        wx.Panel.__init__(self, parent, id=-1, name="panel_tarification", style=wx.TAB_TRAVERSAL)
        self.parent = parent
        self.IDactivite = IDactivite

        # Cat�gories de tarifs
        self.staticbox_categories_staticbox = wx.StaticBox(self, -1, _("Cat�gories de tarifs"))
        self.ctrl_categories = OL_Categories_tarifs.ListView(self, id=-1, IDactivite=IDactivite, name="OL_categories",
                                    style=wx.LC_REPORT|wx.SUNKEN_BORDER|wx.LC_SINGLE_SEL|wx.LC_HRULES|wx.LC_VRULES)
        self.ctrl_categories.MAJ() 

        self.bouton_ajouter_categorie = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath(u"Images/16x16/Ajouter.png"), wx.BITMAP_TYPE_ANY))
        self.bouton_modifier_categorie = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath(u"Images/16x16/Modifier.png"), wx.BITMAP_TYPE_ANY))
        self.bouton_supprimer_categorie = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath(u"Images/16x16/Supprimer.png"), wx.BITMAP_TYPE_ANY))

        # Tarifs
        self.staticbox_tarifs_staticbox = wx.StaticBox(self, -1, _("Affectations des tarifs selon type campeur"))

        self.ctrl_tarification = OL_Tarifs.ListView(self, id=-1, IDactivite=self.IDactivite,style=wx.LC_REPORT )
        #style=wx.LC_HRULES|wx.LC_VRULES
        self.ctrl_tarification.MAJ()
        self.ctrl_recherche = OL_Tarifs.CTRL_Outils(self, listview=self.ctrl_tarification)

        #self.bouton_ajouter_tarif = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath(u"Images/16x16/Ajouter.png"), wx.BITMAP_TYPE_ANY))
        self.bouton_modifier_tarif = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath(u"Images/16x16/Modifier.png"), wx.BITMAP_TYPE_ANY))
        self.bouton_supprimer_tarif = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath(u"Images/16x16/Supprimer.png"), wx.BITMAP_TYPE_ANY))
        #self.bouton_dupliquer_tarif = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath(u"Images/16x16/Dupliquer.png"), wx.BITMAP_TYPE_ANY))

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_BUTTON, self.OnBoutonAjouterCategorie, self.bouton_ajouter_categorie)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonModifierCategorie, self.bouton_modifier_categorie)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonSupprimerCategorie, self.bouton_supprimer_categorie)

        #self.Bind(wx.EVT_BUTTON, self.OnBoutonAjouterTarif, self.bouton_ajouter_tarif)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonModifierTarif, self.bouton_modifier_tarif)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonSupprimerTarif, self.bouton_supprimer_tarif)
        #self.Bind(wx.EVT_BUTTON, self.OnBoutonDupliquerTarif, self.bouton_dupliquer_tarif)
        
    def __set_properties(self):
        self.ctrl_tarification.SetToolTip(_("Seuls les groupes et cat�gories_tarifs avec type_campeur correspondantes sont affich�s"))
        self.bouton_ajouter_categorie.SetToolTip(_("Cliquez ici pour ajouter une cat�gorie de tarif"))
        self.bouton_modifier_categorie.SetToolTip(_("Cliquez ici pour modifier la cat�gorie s�lectionn�s"))
        self.bouton_supprimer_categorie.SetToolTip(_("Cliquez ici pour supprimer la cat�gorie s�lectionn�e"))
        #self.bouton_ajouter_tarif.SetToolTip(_(u"Cliquez ici pour ajouter un nom de prestation ou un tarif"))
        self.bouton_modifier_tarif.SetToolTip(_("Cliquez ici pour modifier l'item s�lectionn�"))
        self.bouton_supprimer_tarif.SetToolTip(_("Cliquez ici pour supprimer l'item s�lectionn�"))
        #self.bouton_dupliquer_tarif.SetToolTip(_(u"Cliquez ici pour dupliquer l'item s�lectionn�"))

    def __do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(rows=3, cols=1, vgap=10, hgap=10)
        
        # Cat�gories de tarifs
        staticbox_categories = wx.StaticBoxSizer(self.staticbox_categories_staticbox, wx.VERTICAL)
        grid_sizer_categories = wx.FlexGridSizer(rows=1, cols=2, vgap=5, hgap=5)
        grid_sizer_boutons_categories = wx.FlexGridSizer(rows=5, cols=1, vgap=5, hgap=5)
        grid_sizer_categories.Add(self.ctrl_categories, 1, wx.EXPAND, 0)
        grid_sizer_boutons_categories.Add(self.bouton_ajouter_categorie, 0, 0, 0)
        grid_sizer_boutons_categories.Add(self.bouton_modifier_categorie, 0, 0, 0)
        grid_sizer_boutons_categories.Add(self.bouton_supprimer_categorie, 0, 0, 0)
        grid_sizer_categories.Add(grid_sizer_boutons_categories, 1, wx.EXPAND, 0)
        grid_sizer_categories.AddGrowableRow(0)
        grid_sizer_categories.AddGrowableCol(0)
        staticbox_categories.Add(grid_sizer_categories, 1, wx.ALL|wx.EXPAND, 5)
        grid_sizer_base.Add(staticbox_categories, 1, wx.LEFT|wx.RIGHT|wx.TOP|wx.EXPAND, 10)
        
        # Tarifs
        staticbox_tarifs = wx.StaticBoxSizer(self.staticbox_tarifs_staticbox, wx.VERTICAL)
        grid_sizer_tarifs = wx.FlexGridSizer(rows=1, cols=2, vgap=5, hgap=5)
        grid_sizer_olv = wx.FlexGridSizer(rows=2, cols=1, vgap=5, hgap=5)
        grid_sizer_olv.Add(self.ctrl_tarification, 1, wx.EXPAND, 0)
        grid_sizer_olv.Add(self.ctrl_recherche, 1, wx.EXPAND, 0)
        grid_sizer_olv.AddGrowableRow(0)
        grid_sizer_olv.AddGrowableCol(0)

        grid_sizer_tarifs.Add(grid_sizer_olv, 1, wx.EXPAND, 0)
        grid_sizer_boutons_tarifs = wx.FlexGridSizer(rows=5, cols=1, vgap=5, hgap=5)
        #grid_sizer_boutons_tarifs.Add(self.bouton_ajouter_tarif, 0, 0, 0)
        grid_sizer_boutons_tarifs.Add(self.bouton_modifier_tarif, 0, 0, 0)
        grid_sizer_boutons_tarifs.Add(self.bouton_supprimer_tarif, 0, 0, 0)
        #grid_sizer_boutons_tarifs.Add( (5, 5), 0, 0, 0)
        #grid_sizer_boutons_tarifs.Add(self.bouton_dupliquer_tarif, 0, 0, 0)
        grid_sizer_tarifs.Add(grid_sizer_boutons_tarifs, 1, wx.EXPAND, 0)
        grid_sizer_tarifs.AddGrowableRow(0)
        grid_sizer_tarifs.AddGrowableCol(0)
        staticbox_tarifs.Add(grid_sizer_tarifs, 1, wx.ALL|wx.EXPAND, 5)
        grid_sizer_base.Add(staticbox_tarifs, 1, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 10)
        
        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)
        grid_sizer_base.AddGrowableRow(1)
        grid_sizer_base.AddGrowableCol(0)

    def OnBoutonAjouterCategorie(self, event): 
        self.ctrl_categories.Ajouter(None)

    def OnBoutonModifierCategorie(self, event): 
        self.ctrl_categories.Modifier(None)

    def OnBoutonSupprimerCategorie(self, event): 
        self.ctrl_categories.Supprimer(None)

    def OnBoutonModifierTarif(self, event): 
        self.ctrl_tarification.Modifier(None)

    def OnBoutonSupprimerTarif(self, event): 
        self.ctrl_tarification.Supprimer(None)

    def MAJtarifs(self):
        """ Met � jour le ctrl tarifs """
        self.ctrl_tarification.MAJ() 

    def Validation(self):
        return True

    def Sauvegarde(self):
        pass

class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self, -1)
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_1.Add(panel, 1, wx.ALL|wx.EXPAND)
        self.SetSizer(sizer_1)
        self.ctrl= Panel(panel, IDactivite=805)
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_2.Add(self.ctrl, 1, wx.ALL|wx.EXPAND, 4)
        panel.SetSizer(sizer_2)
        self.Layout()
        self.CentreOnScreen()

if __name__ == '__main__':
    app = wx.App(0)
    #wx.InitAllImageHandlers()
    frame_1 = MyFrame(None, -1, _("TEST"), size=(700, 500))
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()