#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, Matthania
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS, JB, Jacques Brunel Ajout Duplication de r�glements
# Copyright:       (c) 2010-11 Ivan LUCAS, JB
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------


from Utils.UTILS_Traduction import _
import Chemins
import wx
from Ctrl import CTRL_Bouton_image
from Ol import OL_Reglements
from Dlg import DLG_LettrageVentil
import GestionDB
import wx.lib.agw.hyperlink as Hyperlink
from Utils import UTILS_Utilisateurs


class Hyperlien(Hyperlink.HyperLinkCtrl):
    def __init__(self, parent, id=-1, label="", infobulle="", URL=""):
        Hyperlink.HyperLinkCtrl.__init__(self, parent, id, label, URL=URL)
        self.parent = parent
        
        if self.parent.GetGrandParent().GetName() == "notebook" :
            self.SetBackgroundColour(self.parent.GetGrandParent().GetThemeBackgroundColour())

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
        self.parent.OnClic()
        self.UpdateLink()


# ------------------------------------------------------------------------------------------------------------------------------------------------------------------

class CTRL_Prelevement(wx.Panel):
    def __init__(self, parent, IDfamille=None):
        wx.Panel.__init__(self, parent, id=-1, style=wx.TAB_TRAVERSAL)        
        self.IDfamille = IDfamille

        self.image_valide = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Ok4.png"), wx.BITMAP_TYPE_ANY)
        self.image_nonvalide = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Interdit2.png"), wx.BITMAP_TYPE_ANY)

        self.ctrl_image = wx.StaticBitmap(self, -1, self.image_nonvalide)
        self.hyper_prelevement = Hyperlien(self, label=_("Pr�l�vement automatique"), infobulle=_("Cliquez ici pour activer le pr�l�vement automatique et saisir les coordonn�es bancaires de la famille"), URL="prelevement")

        grid_sizer_base = wx.FlexGridSizer(rows=1, cols=2, vgap=5, hgap=5)
        grid_sizer_base.Add(self.ctrl_image, 1, wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_base.Add(self.hyper_prelevement, 1, wx.ALIGN_CENTER_VERTICAL, 0)
        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)
        self.Layout()
                
    def OnClic(self):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("familles_prelevement", "modifier") == False : return
        from Dlg import DLG_Active_prelevement
        dlg = DLG_Active_prelevement.Dialog(self, IDfamille=self.IDfamille)
        dlg.ShowModal() 
        dlg.Destroy()
        self.MAJ() 
        
    def MAJ(self):
        DB = GestionDB.DB()
        req = """SELECT IDfamille, prelevement_activation
        FROM familles 
        WHERE IDfamille=%d;""" % self.IDfamille
        DB.ExecuterReq(req,MsgBox="ExecuterReq")
        listeDonnees = DB.ResultatReq()
        DB.Close()
        if len(listeDonnees) > 0:
            temp, activation = listeDonnees[0]
            if activation == 1 :
                self.ctrl_image.SetBitmap(self.image_valide)
            else :
                self.ctrl_image.SetBitmap(self.image_nonvalide)

# ------------------------------------------------------------------------------------------------------------------------------------------------------------------

class CTRL_Recu(wx.Panel):
    def __init__(self, parent, IDfamille=None):
        wx.Panel.__init__(self, parent, id=-1, style=wx.TAB_TRAVERSAL)        
        self.IDfamille = IDfamille

        self.image_valide = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Ok4.png"), wx.BITMAP_TYPE_ANY)
        self.image_nonvalide = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Interdit2.png"), wx.BITMAP_TYPE_ANY)

        self.ctrl_image = wx.StaticBitmap(self, -1, self.image_nonvalide)
        self.hyper_prelevement = Hyperlien(self, label=_("Re�us par Email"), infobulle=_("Cliquez ici pour activer l'envoi automatique par email des re�us de r�glements"), URL="recu")

        grid_sizer_base = wx.FlexGridSizer(rows=1, cols=2, vgap=5, hgap=5)
        grid_sizer_base.Add(self.ctrl_image, 1, wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_base.Add(self.hyper_prelevement, 1, wx.ALIGN_CENTER_VERTICAL, 0)
        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)
        self.Layout()
                
    def OnClic(self):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("familles_recu_email", "modifier") == False : return
        from Dlg import DLG_Selection_email
        intro = _("S�lectionnez ici l'adresse Email � laquelle envoyer les re�us de r�glements. Noethys proposera ainsi juste apr�s la saisie d'un r�glement l'envoi du re�u correspondant.")
        titre = _("Activation de l'envoi des re�us par Email")
        dlg = DLG_Selection_email.Dialog(self, IDfamille=self.IDfamille, champ="email_recus", intro=intro, titre=titre)
        dlg.ShowModal() 
        dlg.Destroy()
        self.MAJ() 
        
    def MAJ(self):
        DB = GestionDB.DB()
        req = """SELECT IDfamille, email_recus FROM familles WHERE IDfamille=%d;""" % self.IDfamille
        DB.ExecuterReq(req,MsgBox="ExecuterReq")
        listeDonnees = DB.ResultatReq()
        DB.Close()
        if len(listeDonnees) == 0:
            return
        if listeDonnees[0][1] != None :
            self.ctrl_image.SetBitmap(self.image_valide)
        else :
            self.ctrl_image.SetBitmap(self.image_nonvalide)

# ------------------------------------------------------------------------------------------------------------------------------------------------------------------

class CTRL_Depot(wx.Panel):
    def __init__(self, parent, IDfamille=None):
        wx.Panel.__init__(self, parent, id=-1, style=wx.TAB_TRAVERSAL)        
        self.IDfamille = IDfamille

        self.image_valide = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Ok4.png"), wx.BITMAP_TYPE_ANY)
        self.image_nonvalide = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Interdit2.png"), wx.BITMAP_TYPE_ANY)

        self.ctrl_image = wx.StaticBitmap(self, -1, self.image_nonvalide)
        self.hyper_prelevement = Hyperlien(self, label=_("Avis de d�p�t par Email"), infobulle=_("Cliquez ici pour activer l'envoi automatique par email des avis de d�p�t des r�glements"), URL="depot")

        grid_sizer_base = wx.FlexGridSizer(rows=1, cols=2, vgap=5, hgap=5)
        grid_sizer_base.Add(self.ctrl_image, 1, wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_base.Add(self.hyper_prelevement, 1, wx.ALIGN_CENTER_VERTICAL, 0)
        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)
        self.Layout()
                
    def OnClic(self):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("familles_depot_email", "modifier") == False : return
        from Dlg import DLG_Selection_email
        intro = _("S�lectionnez ici l'adresse Email � laquelle envoyer les avis de d�p�t des r�glements. Noethys enverra ainsi un avis de d�p�t apr�s la validation d'un d�p�t de r�glements.")
        titre = _("Activation de l'envoi des avis de d�p�t par Email")
        dlg = DLG_Selection_email.Dialog(self, IDfamille=self.IDfamille, champ="email_depots", intro=intro, titre=titre)
        dlg.ShowModal() 
        dlg.Destroy()
        self.MAJ() 
        
    def MAJ(self):
        DB = GestionDB.DB()
        req = """SELECT IDfamille, email_depots FROM familles WHERE IDfamille=%d;""" % self.IDfamille
        DB.ExecuterReq(req,MsgBox="ExecuterReq")
        listeDonnees = DB.ResultatReq()
        DB.Close()
        if len(listeDonnees) == 0:
            return
        if listeDonnees[0][1] != None :
            self.ctrl_image.SetBitmap(self.image_valide)
        else :
            self.ctrl_image.SetBitmap(self.image_nonvalide)

# ------------------------------------------------------------------------------------------------------------------------------------------------------------------

class Panel(wx.Panel):
    def __init__(self, parent, IDfamille=None):
        wx.Panel.__init__(self, parent, id=-1, name="panel_reglements", style=wx.TAB_TRAVERSAL)
        self.parent = parent
        self.IDfamille = IDfamille
        self.IDcompte_payeur = None
        
        self.staticbox_reglements = wx.StaticBox(self, -1, _("R�glements"))
        
        # OL Prestations
        self.listviewAvecFooter = OL_Reglements.ListviewAvecFooter(self, kwargs={}) 
        self.ctrl_reglements = self.listviewAvecFooter.GetListview()
        self.ctrl_recherche = OL_Reglements.CTRL_Outils(self, listview=self.ctrl_reglements)
        self.ctrl_recherche.SetBackgroundColour((255, 255, 255))
        
        # Commandes boutons
        self.bouton_ajouter = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Ajouter.png"), wx.BITMAP_TYPE_ANY))
        self.bouton_modifier = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Modifier.png"), wx.BITMAP_TYPE_ANY))
        self.bouton_supprimer = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Supprimer.png"), wx.BITMAP_TYPE_ANY))
        self.bouton_dupliquer = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Dupliquer.png"), wx.BITMAP_TYPE_ANY))
        self.bouton_imprimer = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Imprimante.png"), wx.BITMAP_TYPE_ANY))
        self.bouton_ventilationAuto = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Magique.png"), wx.BITMAP_TYPE_ANY))

        # Abonnements
        self.ctrl_prelevement = CTRL_Prelevement(self, IDfamille)
        self.ctrl_recu = CTRL_Recu(self, IDfamille)
        self.ctrl_depot = CTRL_Depot(self, IDfamille)
        
        # Binds
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAjouter, self.bouton_ajouter)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonModifier, self.bouton_modifier)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonSupprimer, self.bouton_supprimer)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonDupliquer, self.bouton_dupliquer)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonImprimer, self.bouton_imprimer)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonVentilationAuto, self.bouton_ventilationAuto)

        # Propri�t�s
        self.bouton_ajouter.SetToolTip(_("Cliquez ici pour saisir un r�glement"))
        self.bouton_modifier.SetToolTip(_("Cliquez ici pour modifier le r�glement s�lectionn�"))
        self.bouton_supprimer.SetToolTip(_("Cliquez ici pour supprimer le r�glement s�lectionn�"))
        self.bouton_dupliquer.SetToolTip(_("Dupliquer le r�glement s�lectionn�"))
        self.bouton_imprimer.SetToolTip(_("Voir ou Imprimer la liste"))
        self.bouton_ventilationAuto.SetToolTip(_("Ventilations !"))

        # Layout
        grid_sizer_base = wx.FlexGridSizer(rows=1, cols=2, vgap=5, hgap=5)
        staticbox_reglements = wx.StaticBoxSizer(self.staticbox_reglements, wx.VERTICAL)
        grid_sizer_reglements = wx.FlexGridSizer(rows=2, cols=2, vgap=5, hgap=5)
        
        grid_sizer_reglements.Add(self.listviewAvecFooter, 1, wx.EXPAND, 0)
        
        grid_sizer_boutons = wx.FlexGridSizer(rows=7, cols=1, vgap=5, hgap=5)
        grid_sizer_boutons.Add(self.bouton_ajouter, 0, wx.ALL, 0)
        grid_sizer_boutons.Add(self.bouton_modifier, 0, wx.ALL, 0)
        grid_sizer_boutons.Add(self.bouton_supprimer, 0, wx.ALL, 0)
        grid_sizer_boutons.Add( (2, 2), 0, wx.ALL, 0)
        grid_sizer_boutons.Add(self.bouton_dupliquer, 0, wx.ALL, 0)
        grid_sizer_boutons.Add(self.bouton_imprimer, 0, wx.ALL, 0)
        grid_sizer_boutons.Add(self.bouton_ventilationAuto, 0, wx.ALL, 0)
        grid_sizer_reglements.Add(grid_sizer_boutons, 1, wx.ALL, 0)
        
        grid_sizer_options = wx.FlexGridSizer(rows=1, cols=8, vgap=5, hgap=5)
        grid_sizer_options.Add(self.ctrl_prelevement, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_options.Add(self.ctrl_recu, 0, wx.LEFT|wx.ALIGN_CENTER_VERTICAL, 5)
        grid_sizer_options.Add(self.ctrl_depot, 0, wx.LEFT|wx.ALIGN_CENTER_VERTICAL, 5)
        grid_sizer_options.Add( (70, 5), 0, wx.ALL, 0)
        grid_sizer_options.Add(self.ctrl_recherche, 0, wx.EXPAND|wx.ALL, 0)
        grid_sizer_options.AddGrowableCol(4)
        
        grid_sizer_reglements.Add(grid_sizer_options, 1, wx.ALIGN_CENTER_VERTICAL|wx.EXPAND, 0)
        
        grid_sizer_reglements.AddGrowableCol(0)
        grid_sizer_reglements.AddGrowableRow(0)
        staticbox_reglements.Add(grid_sizer_reglements, 1, wx.EXPAND|wx.ALL, 5)
        
        grid_sizer_base.Add(staticbox_reglements, 1, wx.EXPAND|wx.ALL, 5)
        
        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)
        grid_sizer_base.AddGrowableCol(0)
        grid_sizer_base.AddGrowableRow(0)
    
    def OnBoutonAjouter(self, event):
        self.ctrl_reglements.Ajouter(None)
    
    def ReglerFacture(self, IDfacture=None):
        self.ctrl_reglements.ReglerFacture(IDfacture)

    def OnBoutonModifier(self, event):
        self.ctrl_reglements.Modifier(None)

    def OnBoutonSupprimer(self, event):
        self.ctrl_reglements.Supprimer(None)

    def OnBoutonDupliquer(self, event):
        self.ctrl_reglements.Dupliquer(None)

    def OnBoutonImprimer(self, event):
        if len(self.ctrl_reglements.Selection()) == 0:
            noSelection = True
        else:
            noSelection = False
            ID = self.ctrl_reglements.Selection()[0].IDreglement
                
        # Cr�ation du menu contextuel
        menuPop = wx.Menu()
        
        # Item Recu 
        item = wx.MenuItem(menuPop, 10, _("Editer un re�u (PDF)"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Apercu.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.ImpressionRecu, id=10)
        if noSelection == True : item.Enable(False)
        
        menuPop.AppendSeparator()
        
        # Item Apercu avant impression
        item = wx.MenuItem(menuPop, 20, _("Aper�u avant impression"))
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

    def ImpressionRecu(self, event):
        self.ctrl_reglements.EditerRecu(None)

    def Imprimer(self, event):
        self.ctrl_reglements.Imprimer(None)

    def Apercu(self, event):
        self.ctrl_reglements.Apercu(None)
        
    def OnBoutonRepartition(self, event):
        from Dlg import DLG_Repartition
        dlg = DLG_Repartition.Dialog(self, IDfamille=self.IDfamille)
        dlg.ShowModal()
        dlg.Destroy()
    
    def OnBoutonVentilationAuto(self, event):
        """ Ventilation automatique """        
        if len(self.ctrl_reglements.Selection()) == 0:
            noSelection = True
        else:
            noSelection = False

        # Cr�ation du menu contextuel
        menuPop = wx.Menu()
        
        item = wx.MenuItem(menuPop, 201, _("Ventiler automatiquement le r�glement s�lectionn�"))
        item.SetBitmap(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Magique.png"), wx.BITMAP_TYPE_PNG))
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.ctrl_reglements.VentilationAuto, id=201)
        if noSelection == True : item.Enable(False)

        item = wx.MenuItem(menuPop, 202, _("Ventiler automatiquement tous les r�glements"))
        item.SetBitmap(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Magique.png"), wx.BITMAP_TYPE_PNG))
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.ctrl_reglements.VentilationAuto, id=202)

        item = wx.MenuItem(menuPop, 203, _("Voir la ventilation des r�glements"))
        item.SetBitmap(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Magique.png"), wx.BITMAP_TYPE_PNG))
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.AppelLettrage, id=203)

        self.PopupMenu(menuPop)
        menuPop.Destroy()

    def AppelLettrage(self,event):
        DLG_LettrageVentil.Lettrage(self.IDfamille)

    def IsLectureAutorisee(self):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("familles_reglements", "consulter", afficheMessage=False) == False : 
            return False
        return True

    def MAJ(self):
        """ MAJ integrale du controle avec MAJ des donnees """
        if self.IDcompte_payeur == None :
            DB = GestionDB.DB()
            req = """SELECT IDcompte_payeur
            FROM familles
            WHERE IDfamille=%d
            """ % self.IDfamille
            ret = DB.ExecuterReq(req,MsgBox="ExecuterReq")
            listeDonnees = DB.ResultatReq()
            DB.Close()
            if len(listeDonnees) > 0:
                self.IDcompte_payeur = listeDonnees[0][0]
                self.ctrl_reglements.SetIDcompte_payeur(self.IDcompte_payeur)
        # MAJ des contr�les
        self.ctrl_reglements.MAJ() 
        self.ctrl_prelevement.MAJ() 
        self.ctrl_recu.MAJ() 
        self.ctrl_depot.MAJ() 
        self.Refresh()
                
    def ValidationData(self):
        """ Return True si les donn�es sont valides et pretes � �tre sauvegard�es """
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
        self.ctrl= Panel(panel, IDfamille=1)
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