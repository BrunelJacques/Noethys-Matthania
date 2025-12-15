#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#-----------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-11 Ivan LUCAS
# Licence:         Licence GNU GPL
#-----------------------------------------------------------

import wx
from Dlg import DLG_Saisie_utilisateur
from Ctrl import CTRL_Bouton_image
from hashlib import sha256

# L'attribut TE_PASSWORD ne fonctionnait pas sous Ubuntu, SearchCtrl remplacé par TextCtrl
#class CTRL(wx.SearchCtrl):
class CTRL(wx.TextCtrl):
    def __init__(self, parent, listeUtilisateurs=[], size=(-1, -1), modeDLG=False):
        #wx.SearchCtrl.__init__(self, parent, size=size, style=wx.TE_PROCESS_ENTER | wx.TE_PASSWORD)
        wx.TextCtrl.__init__(self, parent, size=size, style=wx.TE_PROCESS_ENTER | wx.TE_PASSWORD)
        self.parent = parent
        self.listeUtilisateurs = listeUtilisateurs
        self.modeDLG = modeDLG

        # Options SearchCtrl
        #self.SetDescriptiveText(u"   ")
        #self.ShowSearchButton(True)
        #self.SetCancelBitmap(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Interdit.png"), wx.BITMAP_TYPE_PNG))
        #self.SetSearchBitmap(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Cadenas.png"), wx.BITMAP_TYPE_PNG))
        
        # Binds
        #self.Bind(wx.EVT_SEARCHCTRL_SEARCH_BTN, self.OnSearch) # Options SearchCtrl
        #self.Bind(wx.EVT_SEARCHCTRL_CANCEL_BTN, self.OnCancel) # Options SearchCtrl
        self.Bind(wx.EVT_TEXT_ENTER, self.OnDoSearch)
        self.Bind(wx.EVT_TEXT, self.OnDoSearch)

    def OnSearch(self, event):
        self.Recherche()
        event.Skip() 
            
    def OnCancel(self, event):
        self.SetValue("")
        self.Recherche()
        event.Skip() 

    def OnDoSearch(self, event):
        self.Recherche()
        event.Skip() 

    def Recherche(self):
        txtSearch = self.GetValue()
        mdpcrypt = sha256(txtSearch.encode('utf-8')).hexdigest()
        if self.modeDLG == True :
            listeUtilisateurs = self.listeUtilisateurs
        else:
            listeUtilisateurs = self.GetGrandParent().listeUtilisateurs
        # Recherche de l'utilisateur
        okMdp = False
        dictUtilisateur = None
        for dictUtilisateur in listeUtilisateurs :
            if (txtSearch == dictUtilisateur["mdp"] or mdpcrypt == dictUtilisateur["mdpcrypt"]) : # txtSearch == dictUtilisateur["mdp"] or à retirer plus tard
                okMdp = True
                break

        # Fin de la recherche si ok, on contrôle la validité
        if okMdp and dictUtilisateur:
            IDutilisateur = dictUtilisateur['IDutilisateur']
            titre = "CHANGEZ VOTRE MOT DE PASSE"
            intro = "Veuillez saisir un NOUVEAU mot de passe plus complexe:"
            intro += "\n\n (minima: %d caractères, %d majuscule, %d minuscule, %d chiffre)"%DLG_Saisie_utilisateur.EXIGEMDP
            dlg = DLG_Saisie_utilisateur.DLG_Saisie_mdp(self,IDutilisateur,titre,intro)
            if not dlg.Security(txtSearch,mute=True):
                mess = ("La sécurité a été renforcée\n\nCe mot de passe est trop simple")
                wx.MessageBox(mess,"CHANGEMENT",style=wx.ICON_INFORMATION)
                dlg.ctrl_mdp.SetValue(txtSearch)
                ret = dlg.ShowModal()
                if ret == wx.ID_OK:
                    dlg.SaveModifPassword()
                else:
                    mess = "Abandon non encore bloquant!\n\nLe process sera redemandé à la prochaine connection"
                    wx.MessageBox(mess, 'ABANDON du Changement MDP', style=wx.ICON_ERROR)
            dlg.Destroy()
            # Version pour la DLG du dessous
            if self.modeDLG == True :
                self.GetParent().ChargeUtilisateur(dictUtilisateur)
            # Version pour la barre Identification de la page d'accueil
            if self.modeDLG == False :
                mainFrame = self.GetGrandParent()
                if mainFrame.GetName() == "general" :
                    mainFrame.ChargeUtilisateur(dictUtilisateur)
            self.SetValue("")
            self.Refresh()
    

# --------------------------- DLG de saisie de mot de passe ----------------------------

class Dialog(wx.Dialog):
    def __init__(self, parent, id=-1, title="Identification", listeUtilisateurs=[], nomFichier=None):
        wx.Dialog.__init__(self, parent, id, title, name="DLG_mdp")
        self.parent = parent
        if not listeUtilisateurs:
            self.listeUtilisateurs = self.GetListeUtilisateurs()
        else:
            self.listeUtilisateurs = listeUtilisateurs

        self.nomFichier = nomFichier
        self.dictUtilisateur = None
        
        if self.nomFichier != None :
            self.SetTitle("Ouverture du fichier %s" % self.nomFichier)
            
        self.staticbox = wx.StaticBox(self, -1, "")
        self.label = wx.StaticText(self, -1, "Veuillez saisir votre code d'identification personnel :")
        self.ctrl_mdp = CTRL(self, listeUtilisateurs=self.listeUtilisateurs, modeDLG=True)
        
        # Texte pour rappeller mot de passe du fichier Exemple
        self.label_exemple = wx.StaticText(self, -1, "Le mot de passe des fichiers exemples est 'aze'")
        self.label_exemple.SetFont(wx.Font(7, wx.SWISS, wx.NORMAL, wx.NORMAL))
        self.label_exemple.SetForegroundColour((130, 130, 130))
        if nomFichier == None or nomFichier.startswith("EXEMPLE_") == False :
            self.label_exemple.Show(False)
        
        self.bouton_annuler = CTRL_Bouton_image.CTRL(self, id=wx.ID_CANCEL, texte="Annuler", cheminImage="Images/32x32/Annuler.png")
        
        self.__set_properties()
        self.__do_layout()
        
        self.ctrl_mdp.SetFocus() 
        
    def __set_properties(self):
        self.bouton_annuler.SetToolTip(wx.ToolTip("Cliquez ici pour annuler"))
        self.ctrl_mdp.SetMinSize((300, -1))

    def __do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(rows=3, cols=1, vgap=0, hgap=0)
        
        # Intro
        grid_sizer_base.Add(self.label, 0, wx.ALL, 10)
        
        # Staticbox
        staticbox = wx.StaticBoxSizer(self.staticbox, wx.HORIZONTAL)
        grid_sizer_contenu = wx.FlexGridSizer(rows=2, cols=1, vgap=2, hgap=2)
        grid_sizer_contenu.Add(self.ctrl_mdp, 1, wx.EXPAND, 0)
        grid_sizer_contenu.Add(self.label_exemple, 1, wx.ALIGN_RIGHT, 0)
        grid_sizer_contenu.AddGrowableCol(0)
        staticbox.Add(grid_sizer_contenu, 1, wx.ALL|wx.EXPAND, 10)
        grid_sizer_base.Add(staticbox, 1, wx.LEFT|wx.RIGHT|wx.EXPAND, 10)
        
        # Boutons
        grid_sizer_boutons = wx.FlexGridSizer(rows=1, cols=3, vgap=10, hgap=10)
        grid_sizer_boutons.Add((20, 20), 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_annuler, 0, 0, 0)
        grid_sizer_boutons.AddGrowableCol(0)
        grid_sizer_base.Add(grid_sizer_boutons, 1, wx.ALL|wx.EXPAND, 10)
        
        self.SetSizer(grid_sizer_base)
        grid_sizer_base.AddGrowableCol(0)
        grid_sizer_base.Fit(self)
        self.Layout()
        self.CentreOnScreen()

    def GetListeUtilisateurs(self):
        """ Récupère la liste des utilisateurs dans la base """
        from Utils import UTILS_Utilisateurs
        return UTILS_Utilisateurs.GetListeUtilisateurs()

    def ChargeUtilisateur(self, dictUtilisateur={}):
        self.dictUtilisateur = dictUtilisateur
        # Fermeture de la fenêtre
        self.EndModal(wx.ID_OK)
    
    def GetDictUtilisateur(self):
        return self.dictUtilisateur

# ---------------------------------------------------------------------------------------

class TestDlg(wx.Dialog):
    def __init__(self, parent, title= "test"):
        wx.Dialog.__init__(self,parent, -1, title, name="DLG_test")

        # Create a panel
        panel = wx.Panel(self)
        self.SetMinSize((200,400))

        # Create a TextCtrl with TE_PASSWORD style
        textLabel = wx.StaticText(panel, -1, "Avec TextCtrl")
        text_ctrl = wx.TextCtrl(panel, style=wx.TE_PASSWORD)

        # Create a SearchCtrl with TE_PASSWORD style
        searchLabel = wx.StaticText(panel, -1, "Avec SearchCtrl")
        search_ctrl = wx.SearchCtrl(panel, style=wx.TE_PASSWORD)

        # Add controls to a sizer for layout
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(textLabel, 0, wx.EXPAND | wx.ALL, 10)
        sizer.Add(text_ctrl, 0, wx.EXPAND | wx.ALL, 10)
        sizer.Add(searchLabel, 0, wx.EXPAND | wx.ALL, 10)
        sizer.Add(search_ctrl, 0, wx.EXPAND | wx.ALL, 10)

        panel.SetSizer(sizer)

    def GetDictUtilisateur(self):
        return 'fin'

if __name__ == '__main__':
    app = wx.App(0)
    dlg = Dialog(None, listeUtilisateurs=[])
    #dlg = TestDlg(None,title="wxPython TE_PASSWORD Example")
    app.SetTopWindow(dlg)
    dlg.ShowModal()
    print(dlg.GetDictUtilisateur())
    app.MainLoop()

