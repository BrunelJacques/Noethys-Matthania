#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:          Ivan LUCAS
# Copyright:       (c) 2010-17 Ivan LUCAS
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------


import Chemins
from Utils import UTILS_Adaptations
from Utils.UTILS_Traduction import _
import wx
import GestionDB
from Utils import UTILS_Interface
from Utils import UTILS_Questionnaires
from Ctrl import CTRL_Bouton_image

from Ctrl.CTRL_ObjectListView import FastObjectListView, ColumnDefn, Filter, CTRL_Outils



class Track(object):
    def __init__(self, donnees={}, index=0):
        self.index = index
        self.nom = donnees["nom"]
        self.largeur = donnees["largeur"]
        self.donnee_code = donnees["donnee_code"]
        self.donnee_label = donnees["donnee_label"]

    def GetDict(self):
        dictDonnees = {"nom" : self.nom, "largeur" : self.largeur, "donnee_code" : self.donnee_code, "donnee_label" : self.donnee_label}
        return dictDonnees


    
class ListView(FastObjectListView):
    def __init__(self, *args, **kwds):
        self.liste_donnees = []
        # Initialisation du listCtrl
        self.nom_fichier_liste = __file__
        FastObjectListView.__init__(self, *args, **kwds)
        # Binds perso
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.Modifier)
        self.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)
                
    def InitModel(self):
        self.donnees = self.GetTracks()

    def GetTracks(self):
        """ Récupération des données """
        listeListeView = []
        index = 0
        for donnees in self.liste_donnees :
            track = Track(donnees, index)
            listeListeView.append(track)
            index += 1
        return listeListeView
      
    def InitObjectListView(self):            
        # Couleur en alternance des lignes
        self.oddRowsBackColor = UTILS_Interface.GetValeur("couleur_tres_claire", wx.Colour(240, 251, 237))
        self.evenRowsBackColor = wx.Colour(255, 255, 255)
        self.useExpansionColumn = True

        def FormateLargeur(largeur):
            if largeur == "automatique" :
                return _("Automatique")
            else :
                return "%s pixels" % largeur

        liste_Colonnes = [
            ColumnDefn(_("Index"), "left", 0, "index"),
            ColumnDefn(_("Nom"), 'left', 200, "nom", isSpaceFilling=True),
            ColumnDefn(_("Donnée"), 'left', 180, "donnee_label"),
            ColumnDefn(_("Largeur"), 'left', 120, "largeur", stringConverter=FormateLargeur),
        ]
        
        self.SetColumns(liste_Colonnes)
        self.SetEmptyListMsg(_("Aucune colonne personnalisée"))
        self.SetEmptyListMsgFont(wx.FFont(11, wx.DEFAULT, False, "Tekton"))
        self.SetSortColumn(self.columns[0])
        self.SetObjects(self.donnees)
       
    def MAJ(self, index=None):
        self.InitModel()
        self.InitObjectListView()
        # Sélection d'un item
        if index != None:
            self.SelectObject(self.donnees[index], deselectOthers=True, ensureVisible=True)
        self._ResizeSpaceFillingColumns()
    
    def Selection(self):
        return self.GetSelectedObjects() 

    def OnContextMenu(self, event):
        """Ouverture du menu contextuel """
        if len(self.Selection()) == 0:
            noSelection = True
        else:
            noSelection = False

        # Création du menu contextuel
        menuPop = UTILS_Adaptations.Menu()

        # Item Modifier
        item = wx.MenuItem(menuPop, 10, _("Ajouter"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Ajouter.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.Ajouter, id=10)

        # Item Modifier
        item = wx.MenuItem(menuPop, 20, _("Modifier"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Modifier.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.Modifier, id=20)
        if noSelection == True : item.Enable(False)
        
        # Item Supprimer
        item = wx.MenuItem(menuPop, 30, _("Supprimer"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Supprimer.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.Supprimer, id=30)
        if noSelection == True : item.Enable(False)

        menuPop.AppendSeparator()
        
        # Item Deplacer vers le haut
        item = wx.MenuItem(menuPop, 60, _("Déplacer vers le haut"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Fleche_haut.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.Monter, id=60)
        if noSelection == True : item.Enable(False)
        
        # Item Déplacer vers le bas
        item = wx.MenuItem(menuPop, 70, _("Déplacer vers le bas"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Fleche_bas.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.Descendre, id=70)
        if noSelection == True : item.Enable(False)
        
        menuPop.AppendSeparator()
    
        # Item Apercu avant impression
        item = wx.MenuItem(menuPop, 40, _("Aperçu avant impression"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Apercu.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.Apercu, id=40)
        
        # Item Imprimer
        item = wx.MenuItem(menuPop, 50, _("Imprimer"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Imprimante.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.Imprimer, id=50)
        
        self.PopupMenu(menuPop)
        menuPop.Destroy()

    def Apercu(self, event):
        from Utils import UTILS_Printer
        prt = UTILS_Printer.ObjectListViewPrinter(self, titre=_("Liste des colonnes"), format="A", orientation=wx.PORTRAIT)
        prt.Preview()

    def Imprimer(self, event):
        from Utils import UTILS_Printer
        prt = UTILS_Printer.ObjectListViewPrinter(self, titre=_("Liste des colonnes"), format="A", orientation=wx.PORTRAIT)
        prt.Print()


    def Ajouter(self, event):
        dlg = DLG_Saisie_colonne(self)
        if dlg.ShowModal() == wx.ID_OK:
            dictDonnees = dlg.GetDonnees()
            self.liste_donnees.append(dictDonnees)
            self.MAJ(index=len(self.liste_donnees)-1)
        dlg.Destroy()

    def Modifier(self, event):
        if len(self.Selection()) == 0 :
            dlg = wx.MessageDialog(self, _("Vous n'avez sélectionné aucune colonne à modifier dans la liste !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        track = self.Selection()[0]

        # DLG Saisie
        dlg = DLG_Saisie_colonne(self)
        dlg.SetDonnees(track.GetDict())
        if dlg.ShowModal() == wx.ID_OK:
            dictDonnees = dlg.GetDonnees()
            self.liste_donnees[track.index] = dictDonnees
            self.MAJ(index=track.index)
        dlg.Destroy()

    def Supprimer(self, event):
        if len(self.Selection()) == 0 :
            dlg = wx.MessageDialog(self, _("Vous n'avez sélectionné aucune colonne à supprimer dans la liste !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        track = self.Selection()[0]

        # Confirmation de suppression
        dlg = wx.MessageDialog(self, _("Souhaitez-vous vraiment supprimer cette colonne ?"), _("Suppression"), wx.YES_NO|wx.NO_DEFAULT|wx.CANCEL|wx.ICON_INFORMATION)
        if dlg.ShowModal() == wx.ID_YES :
            self.liste_donnees.pop(track.index)
            self.MAJ()
        dlg.Destroy()

    def Monter(self, event):
        if len(self.Selection()) == 0 :
            dlg = wx.MessageDialog(self, _("Vous n'avez sélectionné aucune colonne à déplacer !"), _("Erreur"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        track = self.Selection()[0]
        if track.index > 0 :
            item = self.liste_donnees.pop(track.index)
            self.liste_donnees.insert(track.index-1, item)
            self.MAJ(index=track.index-1)
    
    def Descendre(self, event):
        if len(self.Selection()) == 0 :
            dlg = wx.MessageDialog(self, _("Vous n'avez sélectionné aucune colonne à déplacer !"), _("Erreur"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        track = self.Selection()[0]
        if track.index < len(self.liste_donnees)-1 :
            item = self.liste_donnees.pop(track.index)
            self.liste_donnees.insert(track.index+1, item)
            self.MAJ(index=track.index+1)

    def SetParametres(self, dictParametres={}):
        if dictParametres == None :
            return False
        if "colonnes" in dictParametres:
            self.liste_donnees = dictParametres["colonnes"]
            self.MAJ()

    def GetParametres(self):
        dictParametres = {}
        dictParametres["colonnes"] = self.liste_donnees
        return dictParametres

# -------------------------------------------------------------------------------------------------------------------------------------------


class CTRL_Choix(wx.Choice):
    def __init__(self, parent, listeData=[]):
        wx.Choice.__init__(self, parent, -1)
        self.parent = parent
        self.listeData = listeData
        self.SetListe()

    def SetListe(self):
        self.Clear()
        self.listeData = self.listeData
        for code, label in self.listeData:
            self.Append(label)
        self.SetSelection(0)

    def SetID(self, code=None):
        index = 0
        for codeTemp, label in self.listeData:
            if codeTemp == code:
                self.SetSelection(index)
            index += 1

    def GetID(self):
        index = self.GetSelection()
        if index == -1: return None
        return self.listeData[index][0]



class DLG_Saisie_colonne(wx.Dialog):
    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, -1, style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER | wx.MAXIMIZE_BOX | wx.MINIMIZE_BOX)
        self.parent = parent

        # Généralités
        self.staticbox_generalites_staticbox = wx.StaticBox(self, -1, _("Généralités"))

        self.label_nom = wx.StaticText(self, -1, _("Nom :"))
        self.ctrl_nom = wx.TextCtrl(self, -1, "")

        self.label_donnee = wx.StaticText(self, -1, _("Donnée :"))
        liste_choix = [
            ("aucun", _("Aucune")),
            ("genre", _("Genre (M/F)")),
            ("date_naiss", _("Date de naissance")),
            ("ville_naissance", _("Ville de naissance")),
            ("medecin_nom", _("Nom du médecin")),
            ("tel_mobile", _("Tél. mobile")),
            ("tel_domicile", _("Tél. domicile")),
            ("mail", _("Email")),
            ("ville_residence", _("Ville de résidence")),
            ("adresse_residence", _("Adresse complète de résidence")),
            ("secteur", _("Secteur géographique")),
            ("nom_ecole", _("Ecole")),
            ("nom_classe", _("Classe")),
            ("nom_niveau_scolaire", _("Niveau scolaire")),
            ("famille", _("Famille")),
            ("regime", _("Régime social")),
            ("caisse", _("Caisse d'allocations")),
            ("codebarres_individu", _("Code-barres de l'individu")),
            ]

        # Intégration des questionnaires
        q = UTILS_Questionnaires.Questionnaires()
        for public in ("famille", "individu") :
            for dictTemp in q.GetQuestions(public) :
                label = _("Question %s. : %s") % (public[:3], dictTemp["label"])
                code = "question_%s_%d" % (public, dictTemp["IDquestion"])
                liste_choix.append((code, label))

        self.ctrl_donnee = CTRL_Choix(self, liste_choix)

        # Options
        self.staticbox_options_staticbox = wx.StaticBox(self, -1, _("Options"))
        self.label_largeur = wx.StaticText(self, -1, _("Largeur :"))
        liste_choix = [("automatique", _("Automatique")),]
        for x in range(5, 205, 5):
            liste_choix.append((str(x), "%d pixels" % x))
        self.ctrl_largeur = CTRL_Choix(self, liste_choix)

        # Boutons
        self.bouton_aide = CTRL_Bouton_image.CTRL(self, texte=_("Aide"), cheminImage="Images/32x32/Aide.png")
        self.bouton_ok = CTRL_Bouton_image.CTRL(self, texte=_("Ok"), cheminImage="Images/32x32/Valider.png")
        self.bouton_annuler = CTRL_Bouton_image.CTRL(self, id=wx.ID_CANCEL, texte=_("Annuler"), cheminImage="Images/32x32/Annuler.png")

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_BUTTON, self.OnBoutonOk, self.bouton_ok)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAide, self.bouton_aide)

        # Init
        self.SetTitle(_("Saisie d'une colonne"))


    def __set_properties(self):
        self.ctrl_nom.SetMinSize((300, -1))
        self.ctrl_nom.SetToolTip(wx.ToolTip(_("Saisissez ici le label de la colonne")))
        self.ctrl_donnee.SetToolTip(wx.ToolTip(_("Sélectionnez ici la donnée à insérer dans la colonne")))
        self.ctrl_largeur.SetToolTip(wx.ToolTip(_("Saisissez ici la largeur de la colonne (en pixels)")))
        self.bouton_aide.SetToolTip(wx.ToolTip(_("Cliquez ici pour obtenir de l'aide")))
        self.bouton_ok.SetToolTip(wx.ToolTip(_("Cliquez ici pour valider et fermer")))
        self.bouton_annuler.SetToolTip(wx.ToolTip(_("Cliquez ici pour annuler et fermer")))

    def __do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(rows=3, cols=1, vgap=10, hgap=10)

        # Généralités
        staticbox_generalites = wx.StaticBoxSizer(self.staticbox_generalites_staticbox, wx.VERTICAL)

        grid_sizer_generalites = wx.FlexGridSizer(rows=2, cols=2, vgap=10, hgap=10)
        grid_sizer_generalites.Add(self.label_nom, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_generalites.Add(self.ctrl_nom, 0, wx.EXPAND, 0)
        grid_sizer_generalites.Add(self.label_donnee, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_generalites.Add(self.ctrl_donnee, 0, wx.EXPAND, 0)
        grid_sizer_generalites.AddGrowableCol(1)
        staticbox_generalites.Add(grid_sizer_generalites, 1, wx.ALL | wx.EXPAND, 10)

        grid_sizer_base.Add(staticbox_generalites, 1, wx.LEFT | wx.RIGHT | wx.TOP | wx.EXPAND, 10)

        # Options
        staticbox_options = wx.StaticBoxSizer(self.staticbox_options_staticbox, wx.VERTICAL)

        grid_sizer_options = wx.FlexGridSizer(rows=2, cols=2, vgap=10, hgap=10)
        grid_sizer_options.Add(self.label_largeur, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_options.Add(self.ctrl_largeur, 0, 0, 0)
        grid_sizer_options.AddGrowableCol(1)
        staticbox_options.Add(grid_sizer_options, 1, wx.ALL | wx.EXPAND, 10)

        grid_sizer_base.Add(staticbox_options, 1, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)

        # Boutons
        grid_sizer_boutons = wx.FlexGridSizer(rows=1, cols=4, vgap=10, hgap=10)
        grid_sizer_boutons.Add(self.bouton_aide, 0, 0, 0)
        grid_sizer_boutons.Add((20, 20), 0, wx.EXPAND, 0)
        grid_sizer_boutons.Add(self.bouton_ok, 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_annuler, 0, 0, 0)
        grid_sizer_boutons.AddGrowableCol(1)
        grid_sizer_base.Add(grid_sizer_boutons, 1, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 10)

        self.SetSizer(grid_sizer_base)
        grid_sizer_base.AddGrowableCol(0)
        grid_sizer_base.Fit(self)
        self.Layout()
        self.SetMinSize(self.GetSize())
        self.CenterOnScreen()

    def SetDonnees(self, dictDonnees={}):
        self.SetTitle(_("Modification d'une colonne"))
        if "nom" in dictDonnees and dictDonnees["nom"] != None :
            self.ctrl_nom.SetValue(dictDonnees["nom"])
        if "donnee_code" in dictDonnees and dictDonnees["donnee_code"] != None :
            self.ctrl_donnee.SetID(dictDonnees["donnee_code"])
        if "largeur" in dictDonnees and dictDonnees["largeur"] != None :
            self.ctrl_largeur.SetID(dictDonnees["largeur"])

    def GetDonnees(self):
        nom = self.ctrl_nom.GetValue()
        donnee_code = self.ctrl_donnee.GetID()
        donnee_label = self.ctrl_donnee.GetStringSelection()
        largeur = self.ctrl_largeur.GetID()
        dictDonnees = {"nom" : nom, "largeur" : largeur, "donnee_code" : donnee_code, "donnee_label" : donnee_label}
        return dictDonnees

    def OnBoutonOk(self, event):
        nom = self.ctrl_nom.GetValue()
        if nom == "":
            dlg = wx.MessageDialog(self, _("Vous devez obligatoirement saisir un nom de groupe !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            self.ctrl_nom.SetFocus()
            return

        self.EndModal(wx.ID_OK)

    def OnBoutonAide(self, event):
        from Utils import UTILS_Aide
        UTILS_Aide.Aide("Listedesconsommations")





# -------------------------------------------------------------------------------------------------------------------------------------------

class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self, -1, name="test1")
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_1.Add(panel, 1, wx.ALL|wx.EXPAND)
        self.SetSizer(sizer_1)
        self.ctrl = ListView(panel, id=-1, name="OL_test", style=wx.LC_REPORT|wx.SUNKEN_BORDER|wx.LC_SINGLE_SEL|wx.LC_HRULES|wx.LC_VRULES)
        self.ctrl.MAJ()

        dictParametres = {}
        dictParametres["colonnes"] = [
            {"nom" : "Ville", "largeur" : "automatique", "donnee_code" : "ville_residence", "donnee_label" : "Ville de résidence"},
            {"nom": "Signature", "largeur": "50", "donnee_code": None, "donnee_label": None},
            ]
        self.ctrl.SetParametres(dictParametres)

        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_2.Add(self.ctrl, 1, wx.ALL|wx.EXPAND, 4)
        panel.SetSizer(sizer_2)
        self.Layout()

if __name__ == '__main__':
    app = wx.App(0)
    #wx.InitAllImageHandlers()
    frame_1 = MyFrame(None, -1, "OL TEST")
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()
