#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys branche Matthania
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS, JB
# Copyright:       (c) 2010-14 Ivan LUCAS, JB
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------


import Chemins
from Utils.UTILS_Traduction import _
import wx
from Ctrl import CTRL_Bouton_image
from Ctrl import CTRL_Bandeau
from Utils import UTILS_Parametres

def ConvertListeEnTexte(listeColonnes=[]):
    listeChaines = []
    for col in listeColonnes :
        nom = col.valueGetter
        if col.visible == True :
            visible = "oui"
        else :
            visible = "non"
        listeChaines.append("%s;%s" % (nom, visible))
    texte = "##".join(listeChaines)
    return texte

def SauvegardeConfiguration(nomListe=None, listeColonnes=[]):
    texte = ConvertListeEnTexte(listeColonnes)
    UTILS_Parametres.Parametres(mode="set", categorie="configuration_liste_colonnes", nom=nomListe, valeur=texte)
    
def RestaurationConfiguration(nomListe=None, listeColonnesDefaut=[]):
    listeColonnesFinale = []

    # M�morise les colonnes par d�faut
    dictColonnes = {}
    for col in listeColonnesDefaut :
        dictColonnes[col.valueGetter] = col
    
    # Lecture du param�tres stock�
    texteDefaut = ConvertListeEnTexte(listeColonnesDefaut)
    texte = UTILS_Parametres.Parametres(mode="get", categorie="configuration_liste_colonnes", nom=nomListe, valeur=texteDefaut)
    if texte:
        listeChaines = texte.split("##")
    else: listeChaines = []
    listeNomsTemp = []
    for chaine in listeChaines :
        try :
            nom, visible = chaine.split(";")
            if visible == "oui" :
                visible = True
            else :
                visible = False

            if nom in dictColonnes :
                col = dictColonnes[nom]
                col.visible = visible
                listeColonnesFinale.append(col)
                listeNomsTemp.append(nom)
        except :
            pass

    # V�rifie que toutes les colonnes de la liste initiale ont �t� trait�es
    for nom, col in dictColonnes.items() :
        if nom not in listeNomsTemp :
            listeColonnesFinale.append(col)

    return listeColonnesFinale




# -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

class Dialog(wx.Dialog):
    def __init__(self, parent, listeDonnees=[], listeDonneesDefaut=[]):
        wx.Dialog.__init__(self, parent, -1, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX)
        self.parent = parent
        self.listeDonnees = listeDonnees
        self.listeDonneesDefaut = listeDonneesDefaut

        intro = _("Vous pouvez configurer ici les colonnes de la liste. Utilisez les fl�ches pour modifier l'ordre des colonnes et d�cochez les colonnes � masquer.")
        titre = _("Configuration de la liste")
        self.SetTitle(titre)
        self.ctrl_bandeau = CTRL_Bandeau.Bandeau(self, titre=titre, texte=intro, hauteurHtml=30, nomImage="Images/32x32/Configuration2.png")

        self.ctrl_colonnes = wx.CheckListBox(self, -1, choices=[])

        self.bouton_premier = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Fleche_double_haut.png"), wx.BITMAP_TYPE_ANY))
        self.bouton_monter = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Fleche_haut.png"), wx.BITMAP_TYPE_ANY))
        self.bouton_descendre = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Fleche_bas.png"), wx.BITMAP_TYPE_ANY))
        self.bouton_dernier = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Fleche_double_bas.png"), wx.BITMAP_TYPE_ANY))
        self.bouton_reinitialiser = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Actualiser.png"), wx.BITMAP_TYPE_ANY))

        self.bouton_aide = CTRL_Bouton_image.CTRL(self, texte=_("Aide"), cheminImage=Chemins.GetStaticPath("Images/32x32/Aide.png"))
        self.bouton_ok = CTRL_Bouton_image.CTRL(self, texte=_("Ok"), cheminImage=Chemins.GetStaticPath("Images/32x32/Valider.png"))
        self.bouton_fermer = CTRL_Bouton_image.CTRL(self, id=wx.ID_CANCEL, texte=_("Annuler"), cheminImage=Chemins.GetStaticPath("Images/32x32/Annuler.png"))

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_BUTTON, self.Premier, self.bouton_premier)
        self.Bind(wx.EVT_BUTTON, self.Monter, self.bouton_monter)
        self.Bind(wx.EVT_BUTTON, self.Descendre, self.bouton_descendre)
        self.Bind(wx.EVT_BUTTON, self.Dernier, self.bouton_dernier)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAide, self.bouton_aide)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonOk, self.bouton_ok)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonReinit, self.bouton_reinitialiser)

        # Init contr�le
        self.Remplissage(listeDonnees)

    def __set_properties(self):
        self.bouton_premier.SetToolTip(_("Cliquez ici pour d�placer la colonne s�lectionn�e au d�but de la liste"))
        self.bouton_monter.SetToolTip(_("Cliquez ici pour d�placer la colonne s�lectionn�e vers le haut"))
        self.bouton_descendre.SetToolTip(_("Cliquez ici pour d�placer la colonne s�lectionn�e vers le bas"))
        self.bouton_dernier.SetToolTip(_("Cliquez ici pour d�placer la colonne s�lectionn�e � la fin de la liste"))
        self.bouton_reinitialiser.SetToolTip(_("Cliquez ici restaurer les valeurs par d�faut"))
        self.bouton_aide.SetToolTip(_("Cliquez ici pour obtenir de l'aide"))
        self.bouton_fermer.SetToolTip(_("Cliquez ici pour fermer"))
        self.bouton_ok.SetToolTip(_("Cliquez ici pour valider"))
        self.SetMinSize((500, 500))

    def __do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(rows=3, cols=1, vgap=10, hgap=10)
        grid_sizer_base.Add(self.ctrl_bandeau, 0, wx.EXPAND, 0)

        grid_sizer_contenu = wx.FlexGridSizer(rows=1, cols=2, vgap=5, hgap=5)

        grid_sizer_gauche = wx.FlexGridSizer(rows=3, cols=1, vgap=10, hgap=10)
        grid_sizer_gauche.Add(self.ctrl_colonnes, 0, wx.EXPAND, 0)
        grid_sizer_gauche.AddGrowableRow(0)
        grid_sizer_gauche.AddGrowableCol(0)
        grid_sizer_contenu.Add(grid_sizer_gauche, 1, wx.EXPAND, 0)

        grid_sizer_droit = wx.FlexGridSizer(rows=8, cols=1, vgap=5, hgap=5)
        grid_sizer_droit.Add(self.bouton_premier, 0, 0, 0)
        grid_sizer_droit.Add(self.bouton_monter, 0, 0, 0)
        grid_sizer_droit.Add(self.bouton_descendre, 0, 0, 0)
        grid_sizer_droit.Add(self.bouton_dernier, 0, 0, 0)
        grid_sizer_droit.Add( (5, 5), 0, 0, 0)
        grid_sizer_droit.Add(self.bouton_reinitialiser, 0, 0, 0)
        grid_sizer_contenu.Add(grid_sizer_droit, 1, wx.EXPAND, 0)

        grid_sizer_contenu.AddGrowableRow(0)
        grid_sizer_contenu.AddGrowableCol(0)
        grid_sizer_base.Add(grid_sizer_contenu, 1, wx.LEFT|wx.RIGHT|wx.EXPAND, 10)

        grid_sizer_boutons = wx.FlexGridSizer(rows=1, cols=4, vgap=10, hgap=10)
        grid_sizer_boutons.Add(self.bouton_aide, 0, 0, 0)
        grid_sizer_boutons.Add((20, 20), 0, wx.EXPAND, 0)
        grid_sizer_boutons.Add(self.bouton_ok, 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_fermer, 0, 0, 0)
        grid_sizer_boutons.AddGrowableCol(1)
        grid_sizer_base.Add(grid_sizer_boutons, 1, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 10)
        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)
        grid_sizer_base.AddGrowableRow(1)
        grid_sizer_base.AddGrowableCol(0)
        self.Layout()
        self.CenterOnScreen()

    def Remplissage(self, liste=[]):
        for nom, visible in liste :
            index = self.ctrl_colonnes.Append(nom)
            self.ctrl_colonnes.Check(index, visible)

    def Premier(self, event):
        self.Deplacer("premier")

    def Monter(self, event):
        self.Deplacer(-1)

    def Descendre(self, event):
        self.Deplacer(+1)

    def Dernier(self, event):
        self.Deplacer("dernier")

    def Deplacer(self, deplacement=-1):
        index = self.ctrl_colonnes.GetSelection()
        if index == wx.NOT_FOUND :
            return
        if deplacement == -1 and index == 0 :
            return
        if deplacement == +1 and index == len(self.listeDonnees) - 1 :
            return
        nom = self.ctrl_colonnes.GetString(index)
        visible = self.ctrl_colonnes.IsChecked(index)
        self.ctrl_colonnes.Delete(index)
        if deplacement == "premier" :
            newIndex = 0
        elif deplacement == "dernier" :
            newIndex = len(self.listeDonnees) - 1
        else :
            newIndex = index + deplacement
        self.ctrl_colonnes.Insert(nom, newIndex)
        self.ctrl_colonnes.Check(newIndex, visible)
        self.ctrl_colonnes.Select(newIndex)
        self.ctrl_colonnes.EnsureVisible(newIndex)

    def GetListeDonnees(self):
        """ Renvoie les r�sultats """
        listeDonnees = []
        for index in range(0, len(self.listeDonnees)) :
            nom = self.ctrl_colonnes.GetString(index)
            visible = self.ctrl_colonnes.IsChecked(index)
            listeDonnees.append((nom, visible))
        return listeDonnees

    def OnBoutonReinit(self, event=None):
        self.ctrl_colonnes.Clear()
        self.Remplissage(self.listeDonneesDefaut)

    def OnBoutonAide(self, event): 
        from Utils import UTILS_Aide
        UTILS_Aide.Aide("")
        
    def OnBoutonOk(self, event):
        self.EndModal(wx.ID_OK)


if __name__ == "__main__":
    app = wx.App(0)
    #wx.InitAllImageHandlers()
    dialog_1 = Dialog(None, listeDonnees=[(_("Colonne1"), True), (_("Colonne 2"), True), (_("Colonne 3"), False)])
    app.SetTopWindow(dialog_1)
    dialog_1.ShowModal()
    app.MainLoop()
