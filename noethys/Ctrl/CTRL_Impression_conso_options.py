#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activit�s
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
from Ctrl import CTRL_Propertygrid
import wx.propgrid as wxpg
import copy




class CTRL(CTRL_Propertygrid.CTRL):
    def __init__(self, parent):
        CTRL_Propertygrid.CTRL.__init__(self, parent)

    def Remplissage(self):

        # Cat�gorie
        self.Append(wxpg.PropertyCategory(_("Page")))

        # Orientation page
        propriete = CTRL_Propertygrid.Propriete_choix(label=_("Orientation de la page"), name="orientation", liste_choix=[("automatique", _("Automatique")), ("portrait", _("Portrait")), ("paysage", _("Paysage"))], valeur="automatique")
        propriete.SetEditor("EditeurChoix")
        propriete.SetHelpString(_("S�lectionnez l'orientation de la page"))
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)


        # Cat�gorie
        self.Append(wxpg.PropertyCategory(_("Lignes")))

        # Tri
        liste_choix = [("nom", _("Nom")), ("prenom", _("Pr�nom")), ("age", _("�ge"))]
        propriete = CTRL_Propertygrid.Propriete_choix(label=_("Tri"), name="tri", liste_choix=liste_choix, valeur="nom")
        propriete.SetEditor("EditeurChoix")
        propriete.SetHelpString(_("S�lectionnez le tri"))
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)

        # Ordre
        liste_choix = [("croissant", _("Croissant")), ("decroissant", _("D�croissant"))]
        propriete = CTRL_Propertygrid.Propriete_choix(label=_("Ordre"), name="ordre", liste_choix=liste_choix, valeur="croissant")
        propriete.SetEditor("EditeurChoix")
        propriete.SetHelpString(_("S�lectionnez l'ordre"))
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)

        # Afficher lignes vierges
        propriete = wxpg.IntProperty(label=_("Lignes vierges"), name="nbre_lignes_vierges", value=3)
        propriete.SetEditor("SpinCtrl")
        propriete.SetHelpString(_("Nombre de lignes vierges � afficher en fin de liste"))
        propriete.SetAttribute("obligatoire", True)
        propriete.SetAttribute("Min", 0)
        self.Append(propriete)

        # Afficher tous les inscrits
        propriete = wxpg.BoolProperty(label=_("Afficher tous les inscrits"), name="afficher_inscrits", value=False)
        propriete.SetHelpString(_("Cochez cette case pour afficher tous les inscrits"))
        propriete.SetAttribute("UseCheckbox", True)
        self.Append(propriete)

        # Hauteur ligne individu
        liste_choix = [("automatique", _("Automatique")),]
        for x in range(5, 205, 5):
            liste_choix.append((str(x), "%d pixels" % x))
        propriete = CTRL_Propertygrid.Propriete_choix(label=_("Hauteur de la ligne Individu"), name="hauteur_ligne_individu", liste_choix=liste_choix, valeur="automatique")
        propriete.SetEditor("EditeurChoix")
        propriete.SetHelpString(_("S�lectionnez la hauteur de la ligne de l'individu (en pixels)"))
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)

        # Couleur du fond de titre
        propriete = wxpg.ColourProperty(label=_("Couleur ligne de titre"), name="couleur_fond_titre", value=wx.Colour(208, 208, 208) )
        propriete.SetHelpString(_("S�lectionnez la couleur de fond de la ligne de titre"))
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)

        # Couleur du fond d'ent�te de colonne
        propriete = wxpg.ColourProperty(label=_("Couleur ligne des ent�tes"), name="couleur_fond_entetes", value=wx.Colour(240, 240, 240) )
        propriete.SetHelpString(_("S�lectionnez la couleur de fond de la ligne des ent�tes"))
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)

        # Couleur du fond de total
        propriete = wxpg.ColourProperty(label=_("Couleur ligne de total"), name="couleur_fond_total", value=wx.Colour(208, 208, 208) )
        propriete.SetHelpString(_("S�lectionnez la couleur de fond de la ligne de total"))
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)

        # Taille nom activit�
        propriete = wxpg.IntProperty(label=_("Taille de police du nom d'activit�"), name="activite_taille_nom", value=5)
        propriete.SetEditor("SpinCtrl")
        propriete.SetHelpString(_("Taille de police du nom d'activit�"))
        propriete.SetAttribute("obligatoire", True)
        propriete.SetAttribute("Min", 0)
        self.Append(propriete)

        # Cat�gorie
        self.Append(wxpg.PropertyCategory(_("Colonne Photo")))

        # Afficher les photos
        liste_choix = [("non", _("Non")), ("petite", _("Petite taille")), ("moyenne", _("Moyenne taille")), ("grande", _("Grande taille"))]
        propriete = CTRL_Propertygrid.Propriete_choix(label=_("Afficher les photos"), name="afficher_photos", liste_choix=liste_choix, valeur="non")
        propriete.SetEditor("EditeurChoix")
        propriete.SetHelpString(_("Afficher les photos individuelles"))
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)

        # Cat�gorie
        self.Append(wxpg.PropertyCategory(_("Colonne Individu")))

        # Largeur colonne nom
        liste_choix = [("automatique", _("Automatique")),]
        for x in range(5, 305, 5):
            liste_choix.append((str(x), "%d pixels" % x))
        propriete = CTRL_Propertygrid.Propriete_choix(label=_("Largeur de la colonne"), name="largeur_colonne_nom", liste_choix=liste_choix, valeur="automatique")
        propriete.SetEditor("EditeurChoix")
        propriete.SetHelpString(_("S�lectionnez la largeur de la colonne Nom de l'individu (en pixels)"))
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)

        # Cat�gorie
        self.Append(wxpg.PropertyCategory(_("Colonne �ge")))

        # Afficher l'�ge des individus
        propriete = wxpg.BoolProperty(label=_("Afficher la colonne"), name="afficher_age", value=True)
        propriete.SetHelpString(_("Cochez cette case pour afficher de la colonne de l'�ge des individus"))
        propriete.SetAttribute("UseCheckbox", True)
        self.Append(propriete)

        # Largeur colonne �ge
        liste_choix = [("automatique", _("Automatique")),]
        for x in range(5, 305, 5):
            liste_choix.append((str(x), "%d pixels" % x))
        propriete = CTRL_Propertygrid.Propriete_choix(label=_("Largeur de la colonne"), name="largeur_colonne_age", liste_choix=liste_choix, valeur="automatique")
        propriete.SetEditor("EditeurChoix")
        propriete.SetHelpString(_("S�lectionnez la largeur de la colonne �ge de l'individu (en pixels)"))
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)

        # Cat�gorie
        self.Append(wxpg.PropertyCategory(_("Colonnes des unit�s")))

        # Afficher les �v�nements
        propriete = wxpg.BoolProperty(label=_("Afficher les �v�nements"), name="afficher_evenements", value=False)
        propriete.SetHelpString(_("Cochez cette case pour afficher les �v�nements"))
        propriete.SetAttribute("UseCheckbox", True)
        self.Append(propriete)

        # Afficher les �tiquettes
        propriete = wxpg.BoolProperty(label=_("Afficher les �tiquettes"), name="afficher_etiquettes", value=False)
        propriete.SetHelpString(_("Cochez cette case pour afficher les �tiquettes"))
        propriete.SetAttribute("UseCheckbox", True)
        self.Append(propriete)

        # Masquer les consommations
        propriete = wxpg.BoolProperty(label=_("Masquer les consommations"), name="masquer_consommations", value=False)
        propriete.SetHelpString(_("Cochez cette case pour masquer les consommations"))
        propriete.SetAttribute("UseCheckbox", True)
        self.Append(propriete)

        # Largeur colonne unit�s
        liste_choix = [("automatique", _("Automatique")),]
        for x in range(5, 105, 5):
            liste_choix.append((str(x), "%d pixels" % x))
        propriete = CTRL_Propertygrid.Propriete_choix(label=_("Largeur de la colonne"), name="largeur_colonne_unite", liste_choix=liste_choix, valeur="automatique")
        propriete.SetEditor("EditeurChoix")
        propriete.SetHelpString(_("S�lectionnez la largeur de chaque colonne unit� (en pixels)"))
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)

        # Cat�gorie
        self.Append(wxpg.PropertyCategory(_("Colonnes personnalis�es")))

        # Largeur colonne unit�s
        liste_choix = []
        for x in range(5, 105, 5):
            liste_choix.append((str(x), "%d pixels" % x))
        propriete = CTRL_Propertygrid.Propriete_choix(label=_("Largeur par d�faut des colonnes"), name="largeur_colonne_perso", liste_choix=liste_choix, valeur="40")
        propriete.SetEditor("EditeurChoix")
        propriete.SetHelpString(_("S�lectionnez la largeur par d�faut de toutes les colonnes personnalis�es (en pixels)"))
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)

        # Cat�gorie
        self.Append(wxpg.PropertyCategory(_("Colonne Informations")))

        # Afficher les informations
        propriete = wxpg.BoolProperty(label=_("Afficher la colonne"), name="afficher_informations", value=True)
        propriete.SetHelpString(_("Cochez cette case pour afficher la colonne Informations"))
        propriete.SetAttribute("UseCheckbox", True)
        self.Append(propriete)

        # Masquer les informations
        propriete = wxpg.BoolProperty(label=_("Masquer les informations"), name="masquer_informations", value=False)
        propriete.SetHelpString(_("Cochez cette case pour masquer le contenu de la colonne Informations"))
        propriete.SetAttribute("UseCheckbox", True)
        self.Append(propriete)

        # Afficher les cotisations manquantes
        propriete = wxpg.BoolProperty(label=_("Afficher les cotisations manquantes"), name="afficher_cotisations_manquantes", value=False)
        propriete.SetHelpString(_("Cochez cette case pour afficher les cotisations manquantes"))
        propriete.SetAttribute("UseCheckbox", True)
        self.Append(propriete)

        # Afficher les pi�ces manquantes
        propriete = wxpg.BoolProperty(label=_("Afficher les pi�ces manquantes"), name="afficher_pieces_manquantes", value=False)
        propriete.SetHelpString(_("Cochez cette case pour afficher les pi�ces manquantes"))
        propriete.SetAttribute("UseCheckbox", True)
        self.Append(propriete)

        # Largeur colonne informations
        liste_choix = [("automatique", _("Automatique")),]
        for x in range(5, 505, 5):
            liste_choix.append((str(x), "%d pixels" % x))
        propriete = CTRL_Propertygrid.Propriete_choix(label=_("Largeur de la colonne"), name="largeur_colonne_informations", liste_choix=liste_choix, valeur="automatique")
        propriete.SetEditor("EditeurChoix")
        propriete.SetHelpString(_("S�lectionnez la largeur de la colonne Informations (en pixels)"))
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)









    def Validation(self):
        """ Validation des donn�es saisies """
        # V�rifie que les donn�es obligatoires ont �t� saisies
        for nom, valeur in self.GetPropertyValues().items():
            propriete = self.GetPropertyByName(nom)
            if self.GetPropertyAttribute(propriete, "obligatoire") == True:
                if valeur == "" or valeur == None:
                    dlg = wx.MessageDialog(self, _("Vous devez obligatoirement renseigner le param�tre '%s' !") % self.GetPropertyLabel(nom), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
                    dlg.ShowModal()
                    dlg.Destroy()
                    return False

        # V�rifie les tranches de QF perso
        if self.GetPropertyByName("regroupement_principal").GetValue() == "qf_perso" :
            if self.GetPropertyByName("tranches_qf_perso").GetValue() == []:
                dlg = wx.MessageDialog(self, _("Vous devez obligatoirement saisir au moins une tranche de QF personnalis�e !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
                dlg.ShowModal()
                dlg.Destroy()
                return False

        return True

    def Importation(self):
        """ Importation des valeurs dans le contr�le """
        return False

    def GetParametres(self):
        return copy.deepcopy(self.GetPropertyValues())

    def SetParametres(self, dictParametres={}):
        # R�initialisation
        if dictParametres == None :
            self.Reinitialisation(afficher_dlg=False)
            return

        # Envoi des param�tres au Ctrl
        for nom, valeur in dictParametres.items():
            try :
                propriete = self.GetPropertyByName(nom)
                propriete.SetValue(valeur)
            except :
                pass


class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self, -1)
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_1.Add(panel, 1, wx.ALL|wx.EXPAND)
        self.SetSizer(sizer_1)        
        self.ctrl = CTRL(panel)
        self.boutonTest = wx.Button(panel, -1, _("Sauvegarder"))
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_2.Add(self.ctrl, 1, wx.ALL|wx.EXPAND, 4)
        sizer_2.Add(self.boutonTest, 0, wx.ALL|wx.EXPAND, 4)
        panel.SetSizer(sizer_2)
        self.Layout()
        self.CentreOnScreen()
        self.Bind(wx.EVT_BUTTON, self.OnBoutonTest, self.boutonTest)
        
    def OnBoutonTest(self, event):
        """ Bouton Test """
        self.ctrl.Sauvegarde()

if __name__ == '__main__':
    app = wx.App(0)
    #wx.InitAllImageHandlers()
    frame_1 = MyFrame(None, -1, _("TEST"), size=(700, 500))
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()


