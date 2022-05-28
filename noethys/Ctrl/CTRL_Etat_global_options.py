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
            ("annee", _("Année")),
            ("activite", _("Activité")),
            ("groupe", _("Groupe")),
            ("evenement", _("Evènement")),
            ("evenement_date", _("Evènement (avec date)")),
            ("etiquette", _("Etiquette")),
            ("unite_conso", _("Unité de consommation")),
            ("categorie_tarif", _("Catégorie de tarif")),
            ("ville_residence", _("Ville de résidence")),
            ("secteur", _("Secteur géographique")),
            ("genre", _("Genre (M/F)")),
            ("age", _("Age")),
            ("ville_naissance", _("Ville de naissance")),
            ("nom_ecole", _("Ecole")),
            ("nom_classe", _("Classe")),
            ("nom_niveau_scolaire", _("Niveau scolaire")),
            ("individu", _("Individu")),
            ("famille", _("Famille")),
            ("regime", _("Régime social")),
            ("caisse", _("Caisse d'allocations")),
            ("qf_perso", _("Quotient familial (tranches personnalisées)")),
            ("qf_tarifs", _("Quotient familial (tranches paramétrées)")),
            ("qf_100", _("Quotient familial (tranches de 100)")),
            ("categorie_travail", _("Catégorie de travail")),
            ("categorie_travail_pere", _("Catégorie de travail du père")),
            ("categorie_travail_mere", _("Catégorie de travail de la mère")),
            ]

        # Intégration des questionnaires
        q = UTILS_Questionnaires.Questionnaires()
        for public in ("famille", "individu") :
            for dictTemp in q.GetQuestions(public) :
                label = _("Question %s. : %s") % (public[:3], dictTemp["label"])
                code = "question_%s_%d" % (public, dictTemp["IDquestion"])
                liste_regroupements.append((code, label))

        propriete = CTRL_Propertygrid.Propriete_choix(label=_("Regroupement principal"), name="regroupement_principal", liste_choix=liste_regroupements, valeur="aucun")
        propriete.SetEditor("EditeurChoix")
        propriete.SetHelpString(_("Sélectionnez un niveau de regroupement principal"))
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)

        # Tranches d'âge
        propriete = CTRL_Propertygrid.Propriete_liste(label=_("Regroupement par tranches d'âge"), name="regroupement_age", liste_selections=[])
        propriete.SetHelpString(_("Saisissez les tranches d'âge souhaitées séparées par des virgules. Exemple : '3, 6, 12'"))
        propriete.SetAttribute("obligatoire", False)
        self.Append(propriete)

        # Tranches de QF perso
        propriete = CTRL_Propertygrid.Propriete_liste(label=_("Regroupement par tranches de QF"), name="tranches_qf_perso", liste_selections=[])
        propriete.SetHelpString(_("Attention, à utiliser avec le regroupement principal 'Quotient familial (tranches personnalisées)'. Saisissez les tranches de QF souhaitées séparées par des virgules. Exemple : '650, 800, 1200'"))
        propriete.SetAttribute("obligatoire", False)
        self.Append(propriete)

        # Afficher les périodes détaillées
        propriete = wxpg.BoolProperty(label=_("Regroupement par périodes détaillées"), name="periodes_detaillees", value=False)
        propriete.SetHelpString(_("Cochez cette case pour afficher les périodes détaillées"))
        propriete.SetAttribute("UseCheckbox", True)
        self.Append(propriete)

        # Données
        self.Append(wxpg.PropertyCategory(_("Données")))

        propriete = CTRL_Propertygrid.Propriete_choix(label=_("Format des données"), name="format_donnees", liste_choix=[("horaire", _("Horaire")), ("decimal", _("Décimal"))], valeur="horaire")
        propriete.SetEditor("EditeurChoix")
        propriete.SetHelpString(_("Sélectionnez le format d'affichage des données"))
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)

        # Afficher l'avertissement 'familles sans régime'
        propriete = wxpg.BoolProperty(label=_("Avertissement si régime famille inconnu"), name="afficher_regime_inconnu", value=True)
        propriete.SetHelpString(_("Cochez cette case pour afficher un avertissement si le régime d'une ou plusieurs familles est inconnu"))
        propriete.SetAttribute("UseCheckbox", True)
        self.Append(propriete)

        # Associer régime inconnu
        DB = GestionDB.DB()
        req = """SELECT IDregime, nom FROM regimes ORDER BY nom;"""
        DB.ExecuterReq(req,MsgBox="ExecuterReq")
        liste_regimes = DB.ResultatReq()
        DB.Close()
        liste_regimes.insert(0, ("non", _("Non")))
        propriete = CTRL_Propertygrid.Propriete_choix(label=_("Associer régime inconnu à un régime"), name="associer_regime_inconnu", liste_choix=liste_regimes, valeur="non")
        propriete.SetEditor("EditeurChoix")
        propriete.SetHelpString(_("Sélectionnez le régime dans lequel vous souhaitez inclure les familles au régime inconnu"))
        propriete.SetAttribute("obligatoire", False)
        self.Append(propriete)

        # Plafond journalier par individu
        propriete = wxpg.IntProperty(label=_("Plafond journalier par individu (en minutes)"), name="plafond_journalier_individu", value=0)
        propriete.SetHelpString(_("Saisissez un plafond journalier (en minutes) par individu, toutes activités confondues (0 = désactivé). Exemple : une valeur de 120 (minutes) plafonnera le temps retenu pour chaque individu à hauteur de 2 heures."))
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)

        # Filtres
        self.Append(wxpg.PropertyCategory(_("Filtres")))

        # Jours hors vacances
        liste_jours = [(0, _("Lundi")), (1, _("Mardi")), (2, _("Mercredi")), (3, _("Jeudi")), (4, _("Vendredi")), (5, _("Samedi")), (6, _("Dimanche"))]
        propriete = CTRL_Propertygrid.Propriete_multichoix(label=_("Jours hors vacances"), name="jours_hors_vacances", liste_choix=liste_jours, liste_selections=[0, 1, 2, 3, 4, 5, 6])
        propriete.SetHelpString(_("Sélectionnez les jours hors vacances à inclure dans les calculs. Cliquez sur le bouton à droite du champ de saisie pour accéder à la fenêtre de sélection."))
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)

        # Jours de vacances
        propriete = CTRL_Propertygrid.Propriete_multichoix(label=_("Jours de vacances"), name="jours_vacances", liste_choix=liste_jours, liste_selections=[0, 1, 2, 3, 4, 5, 6])
        propriete.SetHelpString(_("Sélectionnez les jours de vacances à inclure dans les calculs. Cliquez sur le bouton à droite du champ de saisie pour accéder à la fenêtre de sélection."))
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)

        # Etat des consommations
        self.liste_codes_etats = ["reservation", "present", "absentj", "absenti"]
        liste_etats = [(0, _("Pointage en attente")), (1, _("Présent")), (2, _("Absence justifiée")), (3, _("Absence injustifiée"))]
        propriete = CTRL_Propertygrid.Propriete_multichoix(label=_("Etat des consommations"), name="etat_consommations", liste_choix=liste_etats, liste_selections=[0, 1, 2, 3])
        propriete.SetHelpString(_("Sélectionnez les états de consommations à inclure dans les calculs. Cliquez sur le bouton à droite du champ de saisie pour accéder à la fenêtre de sélection."))
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)

        # Affichage
        self.Append(wxpg.PropertyCategory(_("Affichage")))

        # Orientation page
        propriete = CTRL_Propertygrid.Propriete_choix(label=_("Orientation de la page"), name="orientation", liste_choix=[("portrait", _("Portrait")), ("paysage", _("Paysage"))], valeur="portrait")
        propriete.SetEditor("EditeurChoix")
        propriete.SetHelpString(_("Sélectionnez l'orientation de la page"))
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)

        # Couleur Ligne tranche d'âge
        propriete = wxpg.ColourProperty(label=_("Couleur de la ligne tranche d'âge"), name="couleur_ligne_age", value=wx.Colour(192,192,192) )
        propriete.SetHelpString(_("Sélectionnez la couleur de la ligne tranche d'âge"))
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)

        # Couleur Ligne total
        propriete = wxpg.ColourProperty(label=_("Couleur de la ligne total"), name="couleur_ligne_total", value=wx.Colour(234,234,234) )
        propriete.SetHelpString(_("Sélectionnez la couleur de la ligne total"))
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)

        # Couleur case regroupement principal
        propriete = wxpg.ColourProperty(label=_("Couleur de la case regroupement principal"), name="couleur_case_regroupement", value=wx.Colour(0, 0, 0) )
        propriete.SetHelpString(_("Sélectionnez la couleur de la case regroupement principal"))
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)

        # Couleur texte regroupement principal
        propriete = wxpg.ColourProperty(label=_("Couleur du texte regroupement principal"), name="couleur_texte_regroupement", value=wx.Colour(255, 255, 255) )
        propriete.SetHelpString(_("Sélectionnez la couleur du texte regroupement principal"))
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)



    def Validation(self):
        """ Validation des données saisies """
        # Vérifie que les données obligatoires ont été saisies
        for nom, valeur in self.GetPropertyValues().items():
            propriete = self.GetPropertyByName(nom)
            if self.GetPropertyAttribute(propriete, "obligatoire") == True:
                if valeur == "" or valeur == None:
                    dlg = wx.MessageDialog(self, _("Vous devez obligatoirement renseigner le paramètre '%s' !") % self.GetPropertyLabel(nom), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
                    dlg.ShowModal()
                    dlg.Destroy()
                    return False

        # Vérifie les tranches de QF perso
        if self.GetPropertyByName("regroupement_principal").GetValue() == "qf_perso" :
            if self.GetPropertyByName("tranches_qf_perso").GetValue() == []:
                dlg = wx.MessageDialog(self, _("Vous devez obligatoirement saisir au moins une tranche de QF personnalisée !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
                dlg.ShowModal()
                dlg.Destroy()
                return False

        return True

    def Importation(self):
        """ Importation des valeurs dans le contrôle """
        return False

    def GetParametres(self):
        parametres = copy.deepcopy(self.GetPropertyValues())
        parametres["etat_consommations"] = [self.liste_codes_etats[index] for index in parametres["etat_consommations"]]
        return parametres

    def SetParametres(self, dictParametres={}):
        # Réinitialisation
        if dictParametres == None :
            self.Reinitialisation(afficher_dlg=False)
            return

        # Envoi des paramètres au Ctrl
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


