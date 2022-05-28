#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, Matthania
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS, JB
# Copyright:       (c) 2010-14 Ivan LUCAS, JB
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------


from Utils.UTILS_Traduction import _
import Chemins
import wx
from Ctrl import CTRL_Bouton_image
from Utils import UTILS_Utilisateurs
import GestionDB
from Ctrl import CTRL_Choix_modele
from Ol import OL_Attestations_cerfa_selection
from Utils import UTILS_Attestations_cerfa
import wx.lib.agw.hyperlink as Hyperlink
import wx.lib.agw.pybusyinfo as PBI


TEXTE_INTRO = _("Veuillez trouver ci-dessous le montant réglé à notre organisme au titre des dons ouvrant droit à déduction fiscale :")

def DateEngFr(textDate):
    if textDate == None: return ""
    textDate = str(textDate)
    text = str(textDate[8:10]) + "/" + str(textDate[5:7]) + "/" + str(textDate[:4])
    return text

def GetTexteNoms(listeNoms=[]):
    """ Récupère les noms sous la forme David DUPOND et Maxime DURAND... """
    texteNoms = ""
    nbreIndividus = len(listeNoms)
    if nbreIndividus == 0 : texteNoms = ""
    if nbreIndividus == 1 : texteNoms = listeNoms[0]
    if nbreIndividus == 2 : texteNoms = _("%s et %s") % (listeNoms[0], listeNoms[1])
    if nbreIndividus > 2 :
        for texteNom in listeNoms[:-2] :
            texteNoms += "%s, " % texteNom
        texteNoms += _("%s et %s") % (listeNoms[-2], listeNoms[-1])
    return texteNoms

def Supprime_accent(texte):
    liste = [ ("é", "e"), ("è", "e"), ("ê", "e"), ("ë", "e"), ("à", "a"), ("û", "u"), ("ô", "o"), ("ç", "c"), ("î", "i"), ("ï", "i"),]
    for a, b in liste :
        texte = texte.replace(a, b)
        texte = texte.replace(a.upper(), b.upper())
    return texte

# ----------------------------------------------------------------------------------------------------------------------------------

class Hyperlien(Hyperlink.HyperLinkCtrl):
    def __init__(self, parent, id=-1, label="", infobulle="", URL="", size=(-1, -1), pos=(0, 0)):
        Hyperlink.HyperLinkCtrl.__init__(self, parent, id, label, URL=URL, size=size, pos=pos)
        self.parent = parent
        
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
        if self.URL == "tout" : self.parent.CocheTout()
        if self.URL == "rien" : self.parent.DecocheTout() 
        self.UpdateLink()
    

class CTRL_Options(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, id=-1, style=wx.TAB_TRAVERSAL)
        self.parent = parent
        
        self.label_modele = wx.StaticText(self, -1, _("Modèle :"))
        self.ctrl_modele = CTRL_Choix_modele.CTRL_Choice(self, categorie="attestation_fiscale")
        self.bouton_gestion_modeles = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Mecanisme.png"), wx.BITMAP_TYPE_ANY))

        self.Bind(wx.EVT_BUTTON, self.OnBoutonModeles, self.bouton_gestion_modeles)


        self.__set_properties()
        self.__do_layout()

    def __set_properties(self):
        self.ctrl_modele.SetToolTip(_("Sélectionnez un modèle de documents"))

    def __do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(rows=3, cols=1, vgap=10, hgap=10)
        
        # Options
        grid_sizer_options = wx.FlexGridSizer(rows=3, cols=2, vgap=15, hgap=10)
        
        # Modèle
        grid_sizer_options.Add(self.label_modele, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.TOP, 10)
        grid_sizer_modele = wx.FlexGridSizer(rows=1, cols=2, vgap=5, hgap=5)
        grid_sizer_modele.Add(self.ctrl_modele, 0, wx.EXPAND, 0)
        grid_sizer_modele.Add(self.bouton_gestion_modeles, 0, 0, 0)
        grid_sizer_modele.AddGrowableCol(0)
        grid_sizer_options.Add(grid_sizer_modele, 1, wx.EXPAND|wx.TOP, 10)
        
        grid_sizer_options.AddGrowableCol(1)
        grid_sizer_base.Add(grid_sizer_options, 1, wx.EXPAND|wx.TOP|wx.LEFT|wx.RIGHT, 0)
                        
        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)
        grid_sizer_base.AddGrowableRow(1)
        grid_sizer_base.AddGrowableCol(0)
        self.Layout()

    def OnBoutonModeles(self, event):
        from Dlg import DLG_Modeles_docs
        dlg = DLG_Modeles_docs.Dialog(self, categorie="attestation_fiscale")
        dlg.ShowModal() 
        dlg.Destroy()
        self.ctrl_modele.MAJ()

    def GetOptions(self):
        dictOptions = {} 
        dictOptions["signataire"] = {
            "nom" : "",
            "fonction" : "",
            "sexe" : "",
            "genre" : "",
            }
        
        # Répertoire
        repertoire = None
                
        # Récupération du modèle
        IDmodele = self.ctrl_modele.GetID() 
        if IDmodele == None :
            dlg = wx.MessageDialog(self, _("Vous devez obligatoirement sélectionner un modèle !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return False
        
        # Constitution du dictOptions
        dictOptions["IDmodele"] = IDmodele
        dictOptions["repertoire"] = repertoire
        dictOptions["intro"] = ""
        
        return dictOptions

# ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

class Panel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, id=-1, name="DLG_Attestations_cerfa_selection", style=wx.TAB_TRAVERSAL)
        self.parent = parent
        self.impressionEffectuee = False
        self.donnees = {}
        
        # Options
        self.ctrl_options = CTRL_Options(self)
        
        # Attestations
        self.staticbox_attestations_staticbox = wx.StaticBox(self, -1, _("Attestations à générer"))
        self.listviewAvecFooter = OL_Attestations_cerfa_selection.ListviewAvecFooter(self,  kwargs={})
        self.ctrl_attestations = self.listviewAvecFooter.GetListview()
        self.ctrl_recherche = OL_Attestations_cerfa_selection.CTRL_Outils(self, listview=self.ctrl_attestations, afficherCocher=True)

        self.bouton_apercu_liste = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Apercu.png"), wx.BITMAP_TYPE_ANY))
        self.bouton_imprimer_liste = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Imprimante.png"), wx.BITMAP_TYPE_ANY))
        self.bouton_export_texte = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Texte2.png"), wx.BITMAP_TYPE_ANY))
        self.bouton_export_excel = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Excel.png"), wx.BITMAP_TYPE_ANY))

        # Actions
        self.bouton_generation = CTRL_Bouton_image.CTRL(self, texte=_("Générer\nles Cerfas"), tailleImage=(32, 32), margesImage=(4, 4, 0, 0), margesTexte=(-5, 1), cheminImage="Images/32x32/Configuration2.png")
        self.bouton_visualiser = CTRL_Bouton_image.CTRL(self, texte=_("Prévisualiser"), tailleImage=(32, 32), margesImage=(4, 0, 0, 0), margesTexte=(-5, 1), cheminImage="Images/32x32/Apercu.png")
        self.bouton_generation.SetMinSize((200, -1))
        self.bouton_visualiser.SetMinSize((200, -1))
        
        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_BUTTON, self.ctrl_attestations.Apercu, self.bouton_apercu_liste)
        self.Bind(wx.EVT_BUTTON, self.ctrl_attestations.Imprimer, self.bouton_imprimer_liste)
        self.Bind(wx.EVT_BUTTON, self.ctrl_attestations.ExportTexte, self.bouton_export_texte)
        self.Bind(wx.EVT_BUTTON, self.ctrl_attestations.ExportExcel, self.bouton_export_excel)
        self.Bind(wx.EVT_BUTTON, self.Generation, self.bouton_generation)
        self.Bind(wx.EVT_BUTTON, self.Apercu, self.bouton_visualiser)

    def __set_properties(self):
        self.bouton_apercu_liste.SetToolTip(_("Cliquez ici pour afficher un aperçu avant impression de la liste"))
        self.bouton_imprimer_liste.SetToolTip(_("Cliquez ici pour imprimer la liste"))
        self.bouton_export_texte.SetToolTip(_("Cliquez ici pour exporter la liste au format texte"))
        self.bouton_export_excel.SetToolTip(_("Cliquez ici pour exporter la liste au format Excel"))
        self.bouton_generation.SetToolTip(_("Cliquez ici pour générer les Cerfas"))
        self.bouton_visualiser.SetToolTip(_("Cliquez ici pour prévisualiser les Cerfas sans numéro ni signature"))

    def __do_layout(self):

        grid_sizer_base = wx.FlexGridSizer(rows=3, cols=1, vgap=10, hgap=10)
        # Attestations
        staticbox_attestations = wx.StaticBoxSizer(self.staticbox_attestations_staticbox, wx.VERTICAL)
        grid_sizer_attestations = wx.FlexGridSizer(rows=3, cols=2, vgap=5, hgap=5)
        grid_sizer_attestations.Add(self.listviewAvecFooter, 1, wx.EXPAND, 0)

        grid_sizer_commandes = wx.FlexGridSizer(rows=6, cols=1, vgap=5, hgap=5)
        grid_sizer_commandes.Add(self.bouton_apercu_liste, 0, 0, 0)
        grid_sizer_commandes.Add(self.bouton_imprimer_liste, 0, 0, 0)
        grid_sizer_commandes.Add(self.bouton_export_texte, 0, 0, 0)
        grid_sizer_commandes.Add(self.bouton_export_excel, 0, 0, 0)

        grid_sizer_attestations.Add(grid_sizer_commandes, 1, wx.EXPAND, 0)
        grid_sizer_attestations.Add(self.ctrl_recherche, 0, wx.EXPAND, 5)

        grid_sizer_attestations.AddGrowableCol(0)
        grid_sizer_attestations.AddGrowableRow(0)
        
        staticbox_attestations.Add(grid_sizer_attestations, 1, wx.ALL|wx.EXPAND, 5)
        grid_sizer_base.Add(staticbox_attestations, 1, wx.EXPAND|wx.LEFT|wx.RIGHT, 0)        
        
        # Gridsizer bas
        grid_sizer_bas = wx.FlexGridSizer(rows=1, cols=2, vgap=10, hgap=10)
        grid_sizer_bas.AddGrowableCol(0)
        grid_sizer_bas.AddGrowableRow(0)

        # Options
        grid_sizer_bas.Add(self.ctrl_options, 1, wx.ALL|wx.EXPAND, 5)
        
        # Boutons d'actions
        staticbox_actions = wx.FlexGridSizer(rows=1, cols=2, vgap=5, hgap=5)
        #staticbox_actions = wx.StaticBoxSizer(self.staticbox_actions_staticbox, wx.VERTICAL)
        staticbox_actions.Add(self.bouton_visualiser, 1, wx.EXPAND|wx.ALL, 5)
        staticbox_actions.Add(self.bouton_generation, 1, wx.EXPAND|wx.ALL, 5)
        grid_sizer_bas.Add(staticbox_actions, 1, wx.EXPAND, 0)
        
        grid_sizer_base.Add(grid_sizer_bas, 1, wx.EXPAND|wx.TOP|wx.LEFT|wx.RIGHT, 0)
        
        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)
        grid_sizer_base.AddGrowableRow(0)
        grid_sizer_base.AddGrowableCol(0)
        self.Layout()

    def CocheTout(self):
        self.ctrl_attestations.CocherTout()

    def DecocheTout(self):
        self.ctrl_attestations.CocherRien()
    
    def Validation(self):
        pass

    def MAJ(self):
        #listeActivites = self.GetParent().page1.GetActivites()
        #self.ctrl_options.ctrl_signataire.MAJ(listeActivites)
        self.bouton_generation.Enable(True)

        dlgAttente = PBI.PyBusyInfo(_("Recherche des données..."), parent=None, title=_("Veuillez patienter..."), icon=wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Logo.png"), wx.BITMAP_TYPE_ANY))
        wx.Yield()
        listePrestations = self.GetParent().page1.GetPrestations()
        periode = self.GetParent().page1.GetPeriode()
        self.ctrl_attestations.MAJ(listePrestations,periode)
        del dlgAttente

    def EcritStatusbar(self, texte=""):
        try :
            topWindow = wx.GetApp().GetTopWindow() 
            topWindow.SetStatusText(texte)
        except : 
            pass

    def GetOptions(self):
        dictOptions = self.ctrl_options.GetOptions()
        if dictOptions == False :
            return False
        
        dictOptions["date_debut"], dictOptions["date_fin"] = self.GetParent().page1.GetPeriode()
        dictOptions["titre"] = _("Attestation Fiscale")
        return dictOptions

    def Generation(self, event=None):
        # Génération des enregistrement Cerfas qui valent attribution d'un numéro
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("familles_factures", "creer") == False :
            GestionDB.MessageBox(self,"Vous n'avez pas les droits pour créer des factures auxquelles sont assimilées les attestations")
            return
        # Validation des données saisies
        tracks = self.ctrl_attestations.GetTracksCoches()
        if len(tracks) == 0 :
            dlg = wx.MessageDialog(self, _("Vous n'avez sélectionné aucun reçu à générer !"), _("Erreur"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        mess = "La génération est irréversible!\n\nConfirmez la génération de %d cerfa(s)"%len(tracks)
        ok = wx.MessageBox(mess,"Génération Cerfas",style=wx.YES_NO)
        if ok == wx.YES:
            action = self.ctrl_attestations.Generation()
            if action:
                # Après la génération aboutie le bouton est grisé pour ne pas relancer une deuxieme fois
                self.bouton_generation.Enable(False)
                self.parent.Onbouton_suite(None)

    def Apercu(self, event=None): 
        """ Aperçu PDF des attestations """
        # Validation des données saisies
        tracks = self.ctrl_attestations.GetTracksCoches() 
        if len(tracks) == 0 : 
            dlg = wx.MessageDialog(self, _("Vous n'avez sélectionné aucun reçu à visualiser !"), _("Erreur"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        
        # Récupération des options
        dictOptions = self.GetOptions() 
        if dictOptions == False :
            return False
        
        # Impression des cotisations sélectionnées
        x = UTILS_Attestations_cerfa.Attestations_fiscales()
        x.Impression(tracks=tracks,
                     afficherDoc=True,
                     dictOptions=dictOptions,
                     repertoire=dictOptions["repertoire"])


# Pour tests --------------------------------------------------------------------------------------------------------

class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self, -1)
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_1.Add(panel, 1, wx.ALL|wx.EXPAND)
        self.SetSizer(sizer_1)
        self.ctrl = Panel(panel)
        self.boutonTest = wx.Button(panel, -1, _("Bouton de test"))
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_2.Add(self.ctrl, 1, wx.ALL|wx.EXPAND, 4)
        sizer_2.Add(self.boutonTest, 0, wx.ALL|wx.EXPAND, 4)
        panel.SetSizer(sizer_2)
        self.Layout()
        self.CentreOnScreen()
        self.panel = panel
        self.Bind(wx.EVT_BUTTON, self.OnBoutonTest, self.boutonTest)
        
    def OnBoutonTest(self, event):
        """ Bouton Test """
        self.ctrl.Validation()
        print(self.panel.dictParametres)

if __name__ == '__main__':
    app = wx.App(0)
    #wx.InitAllImageHandlers()
    frame_1 = MyFrame(None, -1, _("TEST"), size=(700, 500))
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()

##    from Dlg import DLG_Attestations_cerfa_generation
##    dlg = DLG_Attestations_cerfa_generation.Dialog(None)
##    dlg.ShowModal()
##    dlg.Destroy()

