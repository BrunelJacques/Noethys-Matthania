#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Matthania JB : un seul point de greffage from Ol import OL_IndividuInscriptions
# Application :    Noethys branche Matthania
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS, JB
# Copyright:       (c) 2010-11 Ivan LUCAS, JB
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------

import Chemins
import wx
import GestionDB
from Utils.UTILS_Traduction import _
from Utils import UTILS_Utilisateurs
from Ol import OL_IndividuInscriptions
from Ol import OL_Contrats
from Ctrl import CTRL_Informations


class PanelMessages(wx.Panel):
    def __init__(self, parent, IDindividu=None, dictFamillesRattachees={}):
        wx.Panel.__init__(self, parent, id=-1, name="panel_Messages",
                          style=wx.TAB_TRAVERSAL)
        self.parent = parent
        self.IDindividu = IDindividu
        self.dictFamillesRattachees = dictFamillesRattachees

        self.staticbox_infos = wx.StaticBox(self, -1, _("Messages individu à diffuser"))

        # HTL
        self.ctrl_infos = CTRL_Informations.CTRL(self, IDfamille=None,
                                                 IDindividu=self.IDindividu,
                                                 dictFamillesRattachees=self.dictFamillesRattachees)
        self.ctrl_infos.SetMinSize((20, 20))

        # Commandes boutons
        self.bouton_ajouter = wx.BitmapButton(self, -1, wx.Bitmap(
            Chemins.GetStaticPath(u"Images/16x16/Ajouter.png"), wx.BITMAP_TYPE_ANY))
        self.bouton_modifier = wx.BitmapButton(self, -1, wx.Bitmap(
            Chemins.GetStaticPath(u"Images/16x16/Modifier.png"), wx.BITMAP_TYPE_ANY))
        self.bouton_supprimer = wx.BitmapButton(self, -1, wx.Bitmap(
            Chemins.GetStaticPath(u"Images/16x16/Supprimer.png"), wx.BITMAP_TYPE_ANY))

        # Binds
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAjouter, self.bouton_ajouter)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonModifier, self.bouton_modifier)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonSupprimer, self.bouton_supprimer)

        # Propriétés
        self.bouton_ajouter.SetToolTip(
            wx.ToolTip(_("Cliquez ici pour saisir un mémo individuel")))
        self.bouton_modifier.SetToolTip(
            wx.ToolTip(_("Cliquez ici pour modifier le mémo individuel sélectionné")))
        self.bouton_supprimer.SetToolTip(
            wx.ToolTip(_("Cliquez ici pour supprimer le mémo individuel sélectionné")))

        # Layout
        grid_sizer_base = wx.FlexGridSizer(rows=1, cols=2, vgap=5, hgap=5)
        staticbox_infos = wx.StaticBoxSizer(self.staticbox_infos, wx.VERTICAL)
        grid_sizer_infos = wx.FlexGridSizer(rows=2, cols=2, vgap=5, hgap=5)

        grid_sizer_infos.Add(self.ctrl_infos, 1, wx.EXPAND, 0)

        grid_sizer_boutons = wx.FlexGridSizer(rows=6, cols=1, vgap=5, hgap=5)
        grid_sizer_boutons.Add(self.bouton_ajouter, 0, wx.ALL, 0)
        grid_sizer_boutons.Add(self.bouton_modifier, 0, wx.ALL, 0)
        grid_sizer_boutons.Add(self.bouton_supprimer, 0, wx.ALL, 0)
        grid_sizer_infos.Add(grid_sizer_boutons, 1, wx.ALL, 0)

        grid_sizer_infos.AddGrowableCol(0)
        grid_sizer_infos.AddGrowableRow(0)
        staticbox_infos.Add(grid_sizer_infos, 1, wx.EXPAND | wx.ALL, 5)

        grid_sizer_base.Add(staticbox_infos, 1, wx.EXPAND | wx.ALL, 5)

        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)
        grid_sizer_base.AddGrowableCol(0)
        grid_sizer_base.AddGrowableRow(0)
        self.MAJ()

    def OnBoutonAjouter(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("individus_messages",
                                                                  "creer") == False: return
        from Dlg import DLG_Saisie_message
        dlg = DLG_Saisie_message.Dialog(self, IDmessage=None, IDindividu=self.IDindividu,
                                        mode="individu")
        if dlg.ShowModal() == wx.ID_OK:
            self.MAJ()
        dlg.Destroy()

    def OnBoutonModifier(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("individus_messages",
                                                                  "modifier") == False: return
        item = self.ctrl_infos.GetSelection()
        try:
            dataItem = self.ctrl_infos.GetPyData(item)
        except:
            dataItem = None
        if dataItem == None or dataItem["type"] != "message":
            dlg = wx.MessageDialog(self,
                                   _("Vous n'avez sélectionné aucun message à modifier dans la liste !"),
                                   _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        IDmessage = dataItem["IDmessage"]
        from Dlg import DLG_Saisie_message
        dlg = DLG_Saisie_message.Dialog(self, IDmessage=IDmessage, mode="individu")
        if dlg.ShowModal() == wx.ID_OK:
            self.MAJ()
        dlg.Destroy()

    def OnBoutonSupprimer(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("individus_messages",
                                                                  "supprimer") == False: return
        item = self.ctrl_infos.GetSelection()
        try:
            dataItem = self.ctrl_infos.GetPyData(item)
        except:
            dataItem = None
        if dataItem == None or dataItem["type"] != "message":
            dlg = wx.MessageDialog(self,
                                   _("Vous n'avez sélectionné aucun message à supprimer dans la liste !"),
                                   _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        dlg = wx.MessageDialog(self, _("Souhaitez-vous vraiment supprimer ce message ?"),
                               _("Suppression"),
                               wx.YES_NO | wx.NO_DEFAULT | wx.CANCEL | wx.ICON_INFORMATION)
        if dlg.ShowModal() == wx.ID_YES:
            IDmessage = dataItem["IDmessage"]
            DB = GestionDB.DB()
            DB.ReqDEL("messages", "IDmessage", IDmessage)
            DB.Close()
            self.MAJ()
        dlg.Destroy()

    def MAJ(self):
        """ MAJ integrale du controle avec MAJ des donnees """
        self.ctrl_infos.MAJ()

    def ValidationData(self):
        """ Return True si les données sont valides et pretes à être sauvegardées """
        return True

    def Sauvegarde(self):
        pass

class Panel(wx.Panel):
    def __init__(self, parent, IDindividu=None, dictFamillesRattachees={}):
        wx.Panel.__init__(self, parent, id=-1, name="panel_inscriptions", style=wx.TAB_TRAVERSAL)
        self.parent = parent
        self.module = "DLG_Individu_inscriptions.Panel"
        self.IDindividu = IDindividu
        self.dictFamillesRattachees = dictFamillesRattachees
        
        # Inscriptions
        self.staticbox_inscriptions = wx.StaticBox(self, -1, _("Inscriptions"))
        self.ctrl_inscriptions = OL_IndividuInscriptions.ListView(self,self, IDindividu=IDindividu, dictFamillesRattachees=self.dictFamillesRattachees, id=-1, name="OL_inscriptions", style=wx.LC_HRULES|wx.LC_VRULES|wx.LC_REPORT|wx.SUNKEN_BORDER|wx.LC_SINGLE_SEL)
        self.ctrl_inscriptions.SetMinSize((150, 50))
        
        self.bouton_ajouter_inscription = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath(u"Images/16x16/Ajouter.png"), wx.BITMAP_TYPE_ANY))
        self.bouton_modifier_inscription = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath(u"Images/16x16/Modifier.png"), wx.BITMAP_TYPE_ANY))
        self.bouton_supprimer_inscription = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath(u"Images/16x16/Supprimer.png"), wx.BITMAP_TYPE_ANY))
        self.bouton_imprimer = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath(u"Images/16x16/Imprimante.png"), wx.BITMAP_TYPE_ANY))
        self.bouton_forfait = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath(u"Images/16x16/Forfait.png"), wx.BITMAP_TYPE_ANY))

        self.panelMessages = PanelMessages(self,self.IDindividu,self.dictFamillesRattachees)

        # Binds
        self.Bind(wx.EVT_BUTTON, self.ctrl_inscriptions.Ajouter, self.bouton_ajouter_inscription)
        self.Bind(wx.EVT_BUTTON, self.ctrl_inscriptions.Modifier, self.bouton_modifier_inscription)
        self.Bind(wx.EVT_BUTTON, self.ctrl_inscriptions.Supprimer, self.bouton_supprimer_inscription)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonImprimer, self.bouton_imprimer)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonForfait, self.bouton_forfait)

        # Propriétés
        self.bouton_ajouter_inscription.SetToolTip(wx.ToolTip(_("Cliquez ici pour inscrire l'individu à une activité")))
        self.bouton_modifier_inscription.SetToolTip(wx.ToolTip(_("Cliquez ici pour modifier l'inscription sélectionnée")))
        self.bouton_supprimer_inscription.SetToolTip(wx.ToolTip(_("Cliquez ici pour supprimer l'inscription sélectionnée")))
        self.bouton_forfait.SetToolTip(wx.ToolTip(_("Cliquez ici pour saisir manuellement des forfaits datés")))

        # Layout
        #grid_sizer_base = wx.FlexGridSizer(rows=2, cols=1, vgap=0, hgap=0)
        grid_sizer_base = wx.BoxSizer(wx.VERTICAL) # préférable pour growing différencié

        # Inscriptions
        staticbox_inscriptions = wx.StaticBoxSizer(self.staticbox_inscriptions, wx.VERTICAL)
        grid_sizer_inscriptions = wx.FlexGridSizer(rows=1, cols=2, vgap=5, hgap=5)
        
        grid_sizer_inscriptions.Add(self.ctrl_inscriptions, 1, wx.EXPAND, 0)
        
        grid_sizer_boutons = wx.FlexGridSizer(rows=6, cols=1, vgap=5, hgap=5)
        grid_sizer_boutons.Add(self.bouton_ajouter_inscription, 0, wx.ALL, 0)
        grid_sizer_boutons.Add(self.bouton_modifier_inscription, 0, wx.ALL, 0)
        grid_sizer_boutons.Add(self.bouton_supprimer_inscription, 0, wx.ALL, 0)
        grid_sizer_boutons.Add( (5, 5), 0, wx.ALL, 0)
        grid_sizer_boutons.Add(self.bouton_imprimer, 0, wx.ALL, 0)
        grid_sizer_boutons.Add(self.bouton_forfait, 0, wx.ALL, 0)
        grid_sizer_inscriptions.Add(grid_sizer_boutons, 1, wx.ALL, 0)
        
        grid_sizer_inscriptions.AddGrowableCol(0)
        grid_sizer_inscriptions.AddGrowableRow(0)
        staticbox_inscriptions.Add(grid_sizer_inscriptions, 1, wx.EXPAND|wx.ALL, 5)

        # Box sizer tient compte du growing double pour l'expand, (pas un flexgrid)
        grid_sizer_base.Add(staticbox_inscriptions, 2, wx.EXPAND|wx.ALL, 5)
        grid_sizer_base.Add(self.panelMessages, 1, wx.EXPAND|wx.ALL, 5)

        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)

    def OnBoutonImprimer(self, event):
        if len(self.ctrl_inscriptions.Selection()) == 0:
            noSelection = True
        else:
            noSelection = False
            ID = self.ctrl_inscriptions.Selection()[0].IDinscription

        # Création du menu contextuel
        menuPop = wx.Menu()

        # Item Recu
        item = wx.MenuItem(menuPop, 10, _("Editer une confirmation d'inscription (PDF)"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Apercu.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.ctrl_inscriptions.EditerConfirmation, id=10)
        if noSelection == True : item.Enable(False)
        
        menuPop.AppendSeparator()
        
        # Item Apercu avant impression
        item = wx.MenuItem(menuPop, 20, _("Aperçu avant impression"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Apercu.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.ctrl_inscriptions.Apercu, id=20)
        
        # Item Imprimer
        item = wx.MenuItem(menuPop, 30, _("Imprimer"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Imprimante.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.ctrl_inscriptions.Imprimer, id=30)
        
        self.PopupMenu(menuPop)
        menuPop.Destroy()
        
    def OnBoutonForfait(self, event):
        """ Saisir un forfait daté """
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("consommations_conso", "creer") == False : return
        
        # Recherche si l'individu est rattaché à d'autres familles
        listeNoms = []
        listeFamille = []
        # Vérifie que l'individu est rattaché comme REPRESENTANT ou ENFANT à une famille
        if self.dictFamillesRattachees != None :
            valide = False
            for IDfamille, dictFamille in self.dictFamillesRattachees.items() :
                if dictFamille["IDcategorie"] in (1, 2) :
                    valide = True
            if valide == False :
                dlg = wx.MessageDialog(self, _("Pour être inscrit à une activité, un individu doit obligatoirement être rattaché comme représentant ou enfant à une fiche famille !"), _("Inscription impossible"), wx.OK | wx.ICON_EXCLAMATION)
                dlg.ShowModal()
                dlg.Destroy()
                return
        
        if len(self.dictFamillesRattachees) == 1 :
            IDfamille = list(self.dictFamillesRattachees.keys())[0]
            listeFamille.append(IDfamille)
            listeNoms.append(self.dictFamillesRattachees[IDfamille]["nomsTitulaires"])
        else:
            # Si rattachée à plusieurs familles
            for IDfamille, dictFamille in self.dictFamillesRattachees.items() :
                IDcategorie = dictFamille["IDcategorie"]
                if IDcategorie in (1, 2) :
                    listeFamille.append(IDfamille)
                    listeNoms.append(dictFamille["nomsTitulaires"])
                
            if len(listeFamille) == 1 :
                IDfamille = listeFamille[0]
            else:
                # On demande à quelle famille rattacher cette inscription
                dlg = wx.SingleChoiceDialog(self, _("Cet individu est rattaché à %d familles.\nA quelle famille souhaitez-vous rattacher cette inscription ?") % len(listeNoms), _("Rattachements multiples"), listeNoms, wx.CHOICEDLG_STYLE)
                if dlg.ShowModal() == wx.ID_OK:
                    indexSelection = dlg.GetSelection()
                    IDfamille = listeFamille[indexSelection]
                    dlg.Destroy()
                else:
                    dlg.Destroy()
                    return
        
        # Récupère la liste des activités sur lesquelle l'individu est inscrit
        listeActivites = self.ctrl_inscriptions.GetListeActivites()
        
        # Affiche la fenêtre de saisie d'un forfait daté
        from Dlg import DLG_Appliquer_forfait
        dlg = DLG_Appliquer_forfait.Dialog(self, IDfamille=IDfamille, listeActivites=listeActivites, listeIndividus=[self.IDindividu,])
        if dlg.ShowModal() == wx.ID_OK :
            pass
        dlg.Destroy()

    def MAJ(self):
        """ MAJ integrale du controle avec MAJ des donnees """
        self.IDindividu = self.GetGrandParent().IDindividu
        if self.IDindividu == None :
            print("pas de IDindividu !")
            return
        self.ctrl_inscriptions.MAJ()
        self.panelMessages.MAJ()

    def Sauvegarde(self):
        pass

class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self, -1)
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_1.Add(panel, 1, wx.ALL|wx.EXPAND)
        self.SetSizer(sizer_1)
        self.IDindividu = 21739
        self.ctrl = Panel(panel, IDindividu=self.IDindividu)
        self.ctrl.MAJ()
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_2.Add(self.ctrl, 1, wx.ALL|wx.EXPAND, 4)
        panel.SetSizer(sizer_2)
        self.Layout()
        self.CentreOnScreen()

if __name__ == '__main__':
    app = wx.App(0)
    #wx.InitAllImageHandlers()
    frame_1 = MyFrame(None, -1, _("TEST"), size=(800, 400))
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()