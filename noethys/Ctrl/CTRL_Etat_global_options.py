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
from Utils import UTILS_Parametres
from Utils import UTILS_Questionnaires
from Ctrl import CTRL_Propertygrid
import wx.propgrid as wxpg
import copy





class CTRL(CTRL_Propertygrid.CTRL):
    def __init__(self, parent):
        CTRL_Propertygrid.CTRL.__init__(self, parent)

    def Remplissage(self):
        # Regroupement
        self.Append(wxpg.PropertyCategory(_("Regroupement")))

        # Regroupement principal
        liste_regroupements = [
            ("aucun", _("Aucun")),
            ("jour", _("Jour")),
            ("mois", _("Mois")),
            ("annee", _("Ann�e")),
            ("activite", _("Activit�")),
            ("groupe", _("Groupe")),
            ("evenement", _("Ev�nement")),
            ("evenement_date", _("Ev�nement (avec date)")),
            ("etiquette", _("Etiquette")),
            ("unite_conso", _("Unit� de consommation")),
            ("categorie_tarif", _("Cat�gorie de tarif")),
            ("ville_residence", _("Ville de r�sidence")),
            ("secteur", _("Secteur g�ographique")),
            ("genre", _("Genre (M/F)")),
            ("age", _("Age")),
            ("ville_naissance", _("Ville de naissance")),
            ("nom_ecole", _("Ecole")),
            ("nom_classe", _("Classe")),
            ("nom_niveau_scolaire", _("Niveau scolaire")),
            ("individu", _("Individu")),
            ("famille", _("Famille")),
            ("regime", _("R�gime social")),
            ("caisse", _("Caisse d'allocations")),
            ("qf_perso", _("Quotient familial (tranches personnalis�es)")),
            ("qf_tarifs", _("Quotient familial (tranches param�tr�es)")),
            ("qf_100", _("Quotient familial (tranches de 100)")),
            ("categorie_travail", _("Cat�gorie de travail")),
            ("categorie_travail_pere", _("Cat�gorie de travail du p�re")),
            ("categorie_travail_mere", _("Cat�gorie de travail de la m�re")),
            ]

        # Int�gration des questionnaires
        q = UTILS_Questionnaires.Questionnaires()
        for public in ("famille", "individu") :
            for dictTemp in q.GetQuestions(public) :
                label = _("Question %s. : %s") % (public[:3], dictTemp["label"])
                code = "question_%s_%d" % (public, dictTemp["IDquestion"])
                liste_regroupements.append((code, label))

        propriete = CTRL_Propertygrid.Propriete_choix(label=_("Regroupement principal"), name="regroupement_principal", liste_choix=liste_regroupements, valeur="aucun")
        propriete.SetEditor("EditeurChoix")
        propriete.SetHelpString(_("S�lectionnez un niveau de regroupement principal"))
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)

        # Tranches d'�ge
        propriete = CTRL_Propertygrid.Propriete_liste(label=_("Regroupement par tranches d'�ge"), name="regroupement_age", liste_selections=[])
        propriete.SetHelpString(_("Saisissez les tranches d'�ge souhait�es s�par�es par des virgules. Exemple : '3, 6, 12'"))
        propriete.SetAttribute("obligatoire", False)
        self.Append(propriete)

        # Tranches de QF perso
        propriete = CTRL_Propertygrid.Propriete_liste(label=_("Regroupement par tranches de QF"), name="tranches_qf_perso", liste_selections=[])
        propriete.SetHelpString(_("Attention, � utiliser avec le regroupement principal 'Quotient familial (tranches personnalis�es)'. Saisissez les tranches de QF souhait�es s�par�es par des virgules. Exemple : '650, 800, 1200'"))
        propriete.SetAttribute("obligatoire", False)
        self.Append(propriete)

        # Afficher les p�riodes d�taill�es
        propriete = wxpg.BoolProperty(label=_("Regroupement par p�riodes d�taill�es"), name="periodes_detaillees", value=False)
        propriete.SetHelpString(_("Cochez cette case pour afficher les p�riodes d�taill�es"))
        propriete.SetAttribute("UseCheckbox", True)
        self.Append(propriete)

        # Donn�es
        self.Append(wxpg.PropertyCategory(_("Donn�es")))

        propriete = CTRL_Propertygrid.Propriete_choix(label=_("Format des donn�es"), name="format_donnees", liste_choix=[("horaire", _("Horaire")), ("decimal", _("D�cimal"))], valeur="horaire")
        propriete.SetEditor("EditeurChoix")
        propriete.SetHelpString(_("S�lectionnez le format d'affichage des donn�es"))
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)

        # Afficher l'avertissement 'familles sans r�gime'
        propriete = wxpg.BoolProperty(label=_("Avertissement si r�gime famille inconnu"), name="afficher_regime_inconnu", value=True)
        propriete.SetHelpString(_("Cochez cette case pour afficher un avertissement si le r�gime d'une ou plusieurs familles est inconnu"))
        propriete.SetAttribute("UseCheckbox", True)
        self.Append(propriete)

        # Associer r�gime inconnu
        DB = GestionDB.DB()
        req = """SELECT IDregime, nom FROM regimes ORDER BY nom;"""
        DB.ExecuterReq(req,MsgBox="ExecuterReq")
        liste_regimes = DB.ResultatReq()
        DB.Close()
        liste_regimes.insert(0, ("non", _("Non")))
        propriete = CTRL_Propertygrid.Propriete_choix(label=_("Associer r�gime inconnu � un r�gime"), name="associer_regime_inconnu", liste_choix=liste_regimes, valeur="non")
        propriete.SetEditor("EditeurChoix")
        propriete.SetHelpString(_("S�lectionnez le r�gime dans lequel vous souhaitez inclure les familles au r�gime inconnu"))
        propriete.SetAttribute("obligatoire", False)
        self.Append(propriete)

        # Plafond journalier par individu
        propriete = wxpg.IntProperty(label=_("Plafond journalier par individu (en minutes)"), name="plafond_journalier_individu", value=0)
        propriete.SetHelpString(_("Saisissez un plafond journalier (en minutes) par individu, toutes activit�s confondues (0 = d�sactiv�). Exemple : une valeur de 120 (minutes) plafonnera le temps retenu pour chaque individu � hauteur de 2 heures."))
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)

        # Filtres
        self.Append(wxpg.PropertyCategory(_("Filtres")))

        # Jours hors vacances
        liste_jours = [(0, _("Lundi")), (1, _("Mardi")), (2, _("Mercredi")), (3, _("Jeudi")), (4, _("Vendredi")), (5, _("Samedi")), (6, _("Dimanche"))]
        propriete = CTRL_Propertygrid.Propriete_multichoix(label=_("Jours hors vacances"), name="jours_hors_vacances", liste_choix=liste_jours, liste_selections=[0, 1, 2, 3, 4, 5, 6])
        propriete.SetHelpString(_("S�lectionnez les jours hors vacances � inclure dans les calculs. Cliquez sur le bouton � droite du champ de saisie pour acc�der � la fen�tre de s�lection."))
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)

        # Jours de vacances
        propriete = CTRL_Propertygrid.Propriete_multichoix(label=_("Jours de vacances"), name="jours_vacances", liste_choix=liste_jours, liste_selections=[0, 1, 2, 3, 4, 5, 6])
        propriete.SetHelpString(_("S�lectionnez les jours de vacances � inclure dans les calculs. Cliquez sur le bouton � droite du champ de saisie pour acc�der � la fen�tre de s�lection."))
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)

        # Etat des consommations
        self.liste_codes_etats = ["reservation", "present", "absentj", "absenti"]
        liste_etats = [(0, _("Pointage en attente")), (1, _("Pr�sent")), (2, _("Absence justifi�e")), (3, _("Absence injustifi�e"))]
        propriete = CTRL_Propertygrid.Propriete_multichoix(label=_("Etat des consommations"), name="etat_consommations", liste_choix=liste_etats, liste_selections=[0, 1, 2, 3])
        propriete.SetHelpString(_("S�lectionnez les �tats de consommations � inclure dans les calculs. Cliquez sur le bouton � droite du champ de saisie pour acc�der � la fen�tre de s�lection."))
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)

        # Affichage
        self.Append(wxpg.PropertyCategory(_("Affichage")))

        # Orientation page
        propriete = CTRL_Propertygrid.Propriete_choix(label=_("Orientation de la page"), name="orientation", liste_choix=[("portrait", _("Portrait")), ("paysage", _("Paysage"))], valeur="portrait")
        propriete.SetEditor("EditeurChoix")
        propriete.SetHelpString(_("S�lectionnez l'orientation de la page"))
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)

        # Couleur Ligne tranche d'�ge
        propriete = wxpg.ColourProperty(label=_("Couleur de la ligne tranche d'�ge"), name="couleur_ligne_age", value=wx.Colour(192,192,192) )
        propriete.SetHelpString(_("S�lectionnez la couleur de la ligne tranche d'�ge"))
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)

        # Couleur Ligne total
        propriete = wxpg.ColourProperty(label=_("Couleur de la ligne total"), name="couleur_ligne_total", value=wx.Colour(234,234,234) )
        propriete.SetHelpString(_("S�lectionnez la couleur de la ligne total"))
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)

        # Couleur case regroupement principal
        propriete = wxpg.ColourProperty(label=_("Couleur de la case regroupement principal"), name="couleur_case_regroupement", value=wx.Colour(0, 0, 0) )
        propriete.SetHelpString(_("S�lectionnez la couleur de la case regroupement principal"))
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)

        # Couleur texte regroupement principal
        propriete = wxpg.ColourProperty(label=_("Couleur du texte regroupement principal"), name="couleur_texte_regroupement", value=wx.Colour(255, 255, 255) )
        propriete.SetHelpString(_("S�lectionnez la couleur du texte regroupement principal"))
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
        parametres = copy.deepcopy(self.GetPropertyValues())
        parametres["etat_consommations"] = [self.liste_codes_etats[index] for index in parametres["etat_consommations"]]
        return parametres

    def SetParametres(self, dictParametres={}):
        # R�initialisation
        if dictParametres == None :
            self.Reinitialisation(afficher_dlg=False)
            return

        # Envoi des param�tres au Ctrl
        for nom, valeur in dictParametres.items():
            if valeur and nom == "etat_consommations":
                valeur = [self.liste_codes_etats.index(x) for x in valeur]

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
        print(self.ctrl.GetParametres())

if __name__ == '__main__':
    app = wx.App(0)
    #wx.InitAllImageHandlers()
    frame_1 = MyFrame(None, -1, _("TEST"), size=(700, 500))
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()


