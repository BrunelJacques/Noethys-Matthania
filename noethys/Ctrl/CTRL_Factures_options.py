#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
# ------------------------------------------------------------------------
# Application :    Noethys branche Matthania
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS, JB
# Copyright:       (c) 2010-13 Ivan LUCAS, JB
# Licence:         Licence GNU GPL
# ------------------------------------------------------------------------

import wx
import wx.propgrid as wxpg
import copy

import Chemins
import GestionDB

from Utils.UTILS_Traduction import _
from Utils import UTILS_Parametres
from Ctrl import CTRL_Bouton_image
from Ctrl import CTRL_Propertygrid
from Data import DATA_Tables


# Implémentation de la grille wx.propertygrid ---------------------------------------
class CTRL_Parametres(CTRL_Propertygrid.CTRL):
    def __init__(self, parent, mail=False):
        self.mail = mail
        CTRL_Propertygrid.CTRL.__init__(self, parent)
    
    def Remplissage(self):
        listeChamps = [
            "{NUM_FACTURE}", "{DATE_DEBUT}", "{DATE_FIN}", "{DATE_ECHEANCE}",
            "{SOLDE}", "{SOLDE_LETTRES}", "{TOTAL_REPORTS}",
            "{NOM_LOT}", "{FAMILLE_NOM}", "{IDFAMILLE}", "{FAMILLE_RUE}", "{FAMILLE_CP}",
            "{FAMILLE_VILLE}", "{DATE_EDITION_LONG}", "{DATE_EDITION_COURT}",
            "{ORGANISATEUR_NOM}", "{ORGANISATEUR_RUE}", "{ORGANISATEUR_CP}",
            "{ORGANISATEUR_VILLE}", "{ORGANISATEUR_TEL}",
            "{ORGANISATEUR_FAX}", "{ORGANISATEUR_MAIL}", "{ORGANISATEUR_SITE}",
            "{ORGANISATEUR_AGREMENT}", "{ORGANISATEUR_SIRET}",
            "{ORGANISATEUR_APE}",
        ]

        # Catégorie
        self.Append(wxpg.PropertyCategory(_("Modèle")))

        propriete = wxpg.EnumProperty(label=_("Modèle de document PDF"),
                                      name="IDmodele", value=0)
        propriete.SetHelpString(_("Sélectionnez le modèle de document à utiliser"))
        propriete.SetEditor("EditeurComboBoxAvecBoutons")
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)

        if self.mail:
            propriete = wxpg.EnumProperty(label=_("Modèle de mail"),
                                          name="IDmodelMail", value=0)
            propriete.SetHelpString(
                _("Sélectionnez le modèle de corps du mail à utiliser"))
            propriete.SetEditor("EditeurComboBoxAvecBoutons")
            propriete.SetAttribute("obligatoire", True)
            self.Append(propriete)

        self.MAJ_modeles()

        # Catégorie
        self.Append(wxpg.PropertyCategory(_("Mémorisation")))

        # Mémorisation des paramètres
        propriete = wxpg.BoolProperty(label=_("Mémoriser les paramètres"),
                                      name="memoriser_les_parametres", value=True)
        propriete.SetHelpString(_("Cochez cette case si vous souhaitez mémoriser les paramètres de cette liste"))
        propriete.SetAttribute("UseCheckbox", True)
        self.Append(propriete)

        # Répertoire de sauvegarde
        propriete = wxpg.DirProperty(label=_("Répertoire pour copie du fichier"),
                                     name="repertoire_copie", value="")
        propriete.SetHelpString(_("Enregistrer une copie de chaque document dans le répertoire sélectionné. Sinon laissez vide ce champ."))
        self.Append(propriete)

        # Catégorie
        self.Append(wxpg.PropertyCategory(_("Eléments à afficher")))

        # Affichage des factures si avoirs globaux
        propriete = wxpg.EnumProperty(label=_("Factures-Avoirs"),
                                      name="imprimer_factures",
                                      labels=[_("Un seul Avoir ou Facture"),
                                              _("Tout imprimer"), _("Seulement Avoirs"),
                                              _("Seulement Factures")],
                                      values=[0, 1, 2, 3], value=0)
        propriete.SetHelpString(
            _("Sélectionnez les pièces à retenir au moment de la génération de la facture)"))
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)

        # Affichage condensé ou détaillé
        propriete = wxpg.EnumProperty(label=_("Afficher le solde"),
                                      name="affichage_solde",
                                      labels=[_("Actuel"), _("Initial")], values=[0, 1],
                                      value=0)
        propriete.SetHelpString(
            _("Sélectionnez un type d'affichage pour le solde (Actuel=Solde à ce jour / Initial=Solde au moment de la génération de la facture)"))
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)

        # Inversion Avoir Facture des soldes négatis
        propriete = wxpg.BoolProperty(label=_("Inversion Facture/Avoir si négatifs"),
                                      name="inversion_solde", value=True)
        propriete.SetHelpString(
            _("Cochez cette case si vous souhaitez permuter la nature Facture ou Avoir quand les soldes sont négatifs, ils deviendront positifs"))
        propriete.SetAttribute("UseCheckbox", True)
        self.Append(propriete)

        # Afficher le rappel des impayés
        propriete = wxpg.BoolProperty(label=_("Afficher le rappel des impayés"),
                                      name="afficher_impayes", value=True)
        propriete.SetHelpString(
            _("Cochez cette case si vous souhaitez afficher le rappel des impayés dans le document"))
        propriete.SetAttribute("UseCheckbox", True)
        self.Append(propriete)

        # Intégrer les impayés au solde
        propriete = wxpg.BoolProperty(label=_("Intégrer les impayés au solde"),
                                      name="integrer_impayes", value=False)
        propriete.SetHelpString(
            _("Cochez cette case si vous souhaitez intégrer les impayés dans le solde"))
        propriete.SetAttribute("UseCheckbox", True)
        self.Append(propriete)

        # Afficher les coupons-réponse
        propriete = wxpg.BoolProperty(label=_("Afficher le coupon-réponse"),
                                      name="afficher_coupon_reponse", value=True)
        propriete.SetHelpString(
            _("Cochez cette case si vous souhaitez afficher un coupon-réponse dans le document"))
        propriete.SetAttribute("UseCheckbox", True)
        self.Append(propriete)

        # Afficher les messages
        propriete = wxpg.BoolProperty(label=_("Afficher les messages"),
                                      name="afficher_messages", value=True)
        propriete.SetHelpString(
            _("Cochez cette case si vous souhaitez afficher les messages dans le document"))
        propriete.SetAttribute("UseCheckbox", True)
        self.Append(propriete)

        # Afficher les codes-barres
        propriete = wxpg.BoolProperty(label=_("Afficher les codes-barres"),
                                      name="afficher_codes_barres", value=True)
        propriete.SetHelpString(
            _("Cochez cette case si vous souhaitez afficher les codes-barres dans le document"))
        propriete.SetAttribute("UseCheckbox", True)
        self.Append(propriete)

        # Afficher les règlements
        propriete = wxpg.BoolProperty(label=_("Afficher les règlements"),
                                      name="afficher_reglements", value=True)
        propriete.SetHelpString(
            _("Cochez cette case si vous souhaitez afficher les règlements dans le document"))
        propriete.SetAttribute("UseCheckbox", True)
        self.Append(propriete)

        # Afficher les avis de prélèvements
        propriete = wxpg.BoolProperty(label=_("Afficher les avis de prélèvements"),
                                      name="afficher_avis_prelevements", value=True)
        propriete.SetHelpString(
            _("Cochez cette case si vous souhaitez afficher les avis de prélèvements dans le document"))
        propriete.SetAttribute("UseCheckbox", True)
        self.Append(propriete)

        # Afficher les QF aux dates concernées
        propriete = wxpg.BoolProperty(label=_("Afficher les QF"),
                                      name="afficher_qf_dates", value=True)
        propriete.SetHelpString(
            _("Cochez cette case si vous souhaitez afficher les QF aux dates concernées dans le document"))
        propriete.SetAttribute("UseCheckbox", True)
        self.Append(propriete)

        # Catégorie
        self.Append(wxpg.PropertyCategory(_("Texte d'introduction")))

        propriete = wxpg.LongStringProperty(label=_("Texte d'introduction"),
                                            name="texte_introduction", value="")
        propriete.SetHelpString(
            _("Saisissez un texte d'introduction (Aucun par défaut). Vous pouvez intégrer les mots-clés suivants : %s") % ", ".join(
                listeChamps))
        self.Append(propriete)

        propriete = wxpg.IntProperty(label=_("Taille de texte d'introduction"),
                                     name="taille_texte_introduction", value=9)
        propriete.SetHelpString(
            _("Saisissez la taille de texte d'introduction (9 par défaut)"))
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)
        self.SetPropertyEditor("taille_texte_introduction", "SpinCtrl")

        propriete = wxpg.EnumProperty(label=_("Style de texte introduction"),
                                      name="style_texte_introduction",
                                      labels=[_("Normal"), _("Italique"), "Gras",
                                              _("Italique + Gras")], values=[0, 1, 2, 3],
                                      value=0)
        propriete.SetHelpString(_("Sélectionnez un style de texte"))
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)

        propriete = wxpg.ColourProperty(label=_("Couleur de fond introduction"),
                                        name="couleur_fond_introduction",
                                        value=wx.Colour(255, 255, 255))
        propriete.SetHelpString(
            _("Sélectionnez une couleur de fond pour le texte d'introduction"))
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)

        propriete = wxpg.ColourProperty(label=_("Couleur de bord introduction"),
                                        name="couleur_bord_introduction",
                                        value=wx.Colour(255, 255, 255))
        propriete.SetHelpString(
            _("Sélectionnez une couleur de bord pour le texte d'introduction"))
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)

        propriete = wxpg.EnumProperty(label=_("Alignement du texte d'introduction"),
                                      name="alignement_texte_introduction",
                                      labels=[_("Gauche"), _("Centre"), _("Droite")],
                                      values=[0, 1, 2], value=0)
        propriete.SetHelpString(
            _("Sélectionnez un type d'alignement pour le texte d'introduction"))
        self.Append(propriete)

        # Catégorie
        self.Append(wxpg.PropertyCategory(_("Texte de conclusion")))

        propriete = wxpg.LongStringProperty(label=_("Texte de conclusion"),
                                            name="texte_conclusion", value="")
        propriete.SetHelpString(
            _("Saisissez un texte de conclusion (Aucun par défaut). Vous pouvez intégrer les mots-clés suivants : %s") % ", ".join(
                listeChamps))
        self.Append(propriete)

        propriete = wxpg.IntProperty(label=_("Taille de texte de conclusion"),
                                     name="taille_texte_conclusion", value=9)
        propriete.SetHelpString(
            _("Saisissez la taille de texte de conclusion (9 par défaut)"))
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)
        self.SetPropertyEditor("taille_texte_conclusion", "SpinCtrl")

        propriete = wxpg.EnumProperty(label=_("Style de texte conclusion"),
                                      name="style_texte_conclusion",
                                      labels=[_("Normal"), _("Italique"), "Gras",
                                              _("Italique + Gras")], values=[0, 1, 2, 3],
                                      value=0)
        propriete.SetHelpString(_("Sélectionnez un style de texte"))
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)

        propriete = wxpg.ColourProperty(label=_("Couleur de fond conclusion"),
                                        name="couleur_fond_conclusion",
                                        value=wx.Colour(255, 255, 255))
        propriete.SetHelpString(
            _("Sélectionnez une couleur de fond pour le texte de conclusion"))
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)

        propriete = wxpg.ColourProperty(label=_("Couleur de bord conclusion"),
                                        name="couleur_bord_conclusion",
                                        value=wx.Colour(255, 255, 255))
        propriete.SetHelpString(
            _("Sélectionnez une couleur de bord pour le texte de conclusion"))
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)

        propriete = wxpg.EnumProperty(label=_("Alignement du texte de conclusion"),
                                      name="alignement_texte_conclusion",
                                      labels=[_("Gauche"), _("Centre"), _("Droite")],
                                      values=[0, 1, 2], value=0)
        propriete.SetHelpString(
            _("Sélectionnez un type d'alignement pour le texte de conclusion"))
        self.Append(propriete)

        # Signature
        self.Append(wxpg.PropertyCategory(_("Signature")))

        propriete = wxpg.ImageFileProperty(label=_("Image de signature"),
                                           name="image_signature")
        propriete.SetHelpString(
            _("Sélectionnez l'image d'une signature à insérer en fin de document"))
        self.Append(propriete)

        propriete = wxpg.IntProperty(label=_("Taille de l'image (en %)"),
                                     name="taille_image_signature", value=100)
        propriete.SetHelpString(
            _("Saisissez la taille de l'image en pourcentage (100 par défaut)"))
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)
        self.SetPropertyEditor("taille_image_signature", "SpinCtrl")

        propriete = wxpg.EnumProperty(label=_("Alignement de l'image"),
                                      name="alignement_image_signature",
                                      labels=[_("Gauche"), _("Centre"), _("Droite")],
                                      values=[0, 1, 2], value=0)
        propriete.SetHelpString(
            _("Sélectionnez un type d'alignement pour l'image de signature"))
        self.Append(propriete)

        # Catégorie
        self.Append(wxpg.PropertyCategory(_("Titre")))

        # Afficher le titre
        propriete = wxpg.BoolProperty(label=_("Afficher le titre"), name="afficher_titre",
                                      value=True)
        propriete.SetHelpString(
            _("Cochez cette case si vous souhaitez afficher le titre du le document"))
        propriete.SetAttribute("UseCheckbox", True)
        self.Append(propriete)

        propriete = wxpg.StringProperty(label=_("Titre du document"), name="texte_titre",
                                        value=_("Facture"))
        propriete.SetHelpString(
            _("Saisissez le titre du document (Par défaut 'Facture'). Vous pouvez intégrer les mots-clés suivants : %s") % ", ".join(
                listeChamps))
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)

        propriete = wxpg.IntProperty(label=_("Taille de texte du titre"),
                                     name="taille_texte_titre", value=19)
        propriete.SetHelpString(
            _("Saisissez la taille de texte du titre (29 par défaut)"))
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)
        self.SetPropertyEditor("taille_texte_titre", "SpinCtrl")

        propriete = wxpg.BoolProperty(label=_("Afficher la période de facturation"),
                                      name="afficher_periode", value=True)
        propriete.SetHelpString(
            _("Cochez cette case si vous souhaitez afficher la période de facturation dans le document"))
        propriete.SetAttribute("UseCheckbox", True)
        self.Append(propriete)

        propriete = wxpg.IntProperty(label=_("Taille de texte de la période"),
                                     name="taille_texte_periode", value=8)
        propriete.SetHelpString(
            _("Saisissez la taille de texte de la période (8 par défaut)"))
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)
        self.SetPropertyEditor("taille_texte_periode", "SpinCtrl")

        # Catégorie
        self.Append(wxpg.PropertyCategory(_("Tableau des prestations")))

        # Affichage condensé ou détaillé
        propriete = wxpg.EnumProperty(label=_("Affichage des prestations"),
                                      name="affichage_prestations",
                                      labels=[_("Détaillé"), _("Regroupement par label"),
                                              _("Regroupement par label et montant unitaire")],
                                      values=[0, 1, 2], value=0)
        propriete.SetHelpString(_("Sélectionnez un type d'affichage"))
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)

        # Intitulés des prestations
        labels = [_("Intitulé original"),
                  _("Intitulé original + état 'Absence injustifiée'"), _("Nom du tarif"),
                  _("Nom de l'activité")]
        propriete = wxpg.EnumProperty(label=_("Intitulés des prestations"),
                                      name="intitules", labels=labels,
                                      values=[0, 1, 2, 3], value=0)
        propriete.SetHelpString(
            _("Sélectionnez le type d'intitulé à afficher pour les prestations"))
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)

        # Couleur 1
        propriete = wxpg.ColourProperty(label=_("Couleur de fond 1"),
                                        name="couleur_fond_1",
                                        value=wx.Colour(204, 204, 255))
        propriete.SetHelpString(_("Sélectionnez la couleur 1"))
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)

        # Couleur 2
        propriete = wxpg.ColourProperty(label=_("Couleur de fond 2"),
                                        name="couleur_fond_2",
                                        value=wx.Colour(234, 234, 255))
        propriete.SetHelpString(_("Sélectionnez la couleur 2"))
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)

        # Largeur colonne Date
        propriete = wxpg.IntProperty(label=_("Largeur de la colonne Date (ou Qté)"),
                                     name="largeur_colonne_date", value=50)
        propriete.SetHelpString(
            _("Saisissez la largeur de la colonne Date (50 par défaut)"))
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)
        self.SetPropertyEditor("largeur_colonne_date", "SpinCtrl")

        # Largeur colonne Montant HT
        propriete = wxpg.IntProperty(label=_("Largeur de la colonne Montant HT"),
                                     name="largeur_colonne_montant_ht", value=50)
        propriete.SetHelpString(
            _("Saisissez la largeur de la colonne Montant HT (50 par défaut)"))
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)
        self.SetPropertyEditor("largeur_colonne_montant_ht", "SpinCtrl")

        # Largeur colonne Montant TVA
        propriete = wxpg.IntProperty(label=_("Largeur de la colonne Montant TVA"),
                                     name="largeur_colonne_montant_tva", value=50)
        propriete.SetHelpString(
            _("Saisissez la largeur de la colonne Montant TVA (50 par défaut)"))
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)
        self.SetPropertyEditor("largeur_colonne_montant_tva", "SpinCtrl")

        # Largeur colonne Montant TTC
        propriete = wxpg.IntProperty(label=_("Largeur de la colonne Montant TTC"),
                                     name="largeur_colonne_montant_ttc", value=70)
        propriete.SetHelpString(
            _("Saisissez la largeur de la colonne Montant TTC (70 par défaut)"))
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)
        self.SetPropertyEditor("largeur_colonne_montant_ttc", "SpinCtrl")

        # Taille de texte du nom de l'individu
        propriete = wxpg.IntProperty(label=_("Taille de texte de l'individu"),
                                     name="taille_texte_individu", value=9)
        propriete.SetHelpString(
            _("Saisissez la taille de texte de l'individu (9 par défaut)"))
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)
        self.SetPropertyEditor("taille_texte_individu", "SpinCtrl")

        # Taille de texte du nom de l'activité
        propriete = wxpg.IntProperty(label=_("Taille de texte de l'activité"),
                                     name="taille_texte_activite", value=6)
        propriete.SetHelpString(
            _("Saisissez la taille de texte de l'activité (6 par défaut)"))
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)
        self.SetPropertyEditor("taille_texte_activite", "SpinCtrl")

        # Taille de texte des noms de colonnes
        propriete = wxpg.IntProperty(label=_("Taille de texte des noms de colonnes"),
                                     name="taille_texte_noms_colonnes", value=5)
        propriete.SetHelpString(
            _("Saisissez la taille de texte des noms de colonnes (5 par défaut)"))
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)
        self.SetPropertyEditor("taille_texte_noms_colonnes", "SpinCtrl")

        # Taille de texte des prestations
        propriete = wxpg.IntProperty(label=_("Taille de texte des prestations"),
                                     name="taille_texte_prestation", value=7)
        propriete.SetHelpString(
            _("Saisissez la taille de texte des prestations (7 par défaut)"))
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)
        self.SetPropertyEditor("taille_texte_prestation", "SpinCtrl")

        # Taille de texte des messages
        propriete = wxpg.IntProperty(label=_("Taille de texte des messages"),
                                     name="taille_texte_messages", value=7)
        propriete.SetHelpString(
            _("Saisissez la taille de texte des messages (7 par défaut)"))
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)
        self.SetPropertyEditor("taille_texte_messages", "SpinCtrl")

        # Taille de texte des labels totaux
        propriete = wxpg.IntProperty(label=_("Taille de texte des labels totaux"),
                                     name="taille_texte_labels_totaux", value=9)
        propriete.SetHelpString(
            _("Saisissez la taille de texte des labels totaux (9 par défaut)"))
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)
        self.SetPropertyEditor("taille_texte_labels_totaux", "SpinCtrl")

        # Taille de texte des totaux
        propriete = wxpg.IntProperty(label=_("Taille de texte des montants totaux"),
                                     name="taille_texte_montants_totaux", value=10)
        propriete.SetHelpString(
            _("Saisissez la taille de texte des montants totaux (10 par défaut)"))
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)
        self.SetPropertyEditor("taille_texte_montants_totaux", "SpinCtrl")

    def Validation(self):
        """ Validation des données saisies """
        for nom, valeur in self.GetPropertyValues().items():
            propriete = self.GetPropertyByName(nom)
            if self.GetPropertyAttribute(propriete, "obligatoire") == True:
                if valeur == "" or valeur == None:
                    dlg = wx.MessageDialog(self,
                                           _("Vous devez obligatoirement renseigner le paramètre '%s' !") % nom,
                                           _("Erreur de saisie"),
                                           wx.OK | wx.ICON_EXCLAMATION)
                    dlg.ShowModal()
                    dlg.Destroy()
                    return False
        return True

    def Importation(self):
        """ Importation des valeurs dans le contrôle """
        # Récupération des noms et valeurs par défaut du contrôle
        dictValeurs = copy.deepcopy(self.GetPropertyValues())
        # Recherche les paramètres mémorisés
        dictParametres = UTILS_Parametres.ParametresCategorie(mode="get",
                                                              categorie="impression_facture",
                                                              dictParametres=dictValeurs)
        # Envoie les paramètres dans le contrôle
        for nom, valeur in dictParametres.items():
            propriete = self.GetPropertyByName(nom)
            # remet toujours la mémorisation par défaut, ne reproduit pas l'antérieur
            if nom == "memoriser_les_parametres" and not valeur:
                valeur = True
            propriete.SetValue(valeur)

    def Sauvegarde(self, forcer=False):
        """ Mémorisation des valeurs du contrôle """
        if self.GetPropertyByName("memoriser_les_parametres").GetValue() == True or forcer == True :
            dictValeurs = copy.deepcopy(self.GetPropertyValues())
            UTILS_Parametres.ParametresCategorie(mode="set", categorie="impression_facture",
                                                 dictParametres=dictValeurs)

    def GetValeurs(self):
        return self.GetPropertyValues()

    def MAJ_modeles(self):
        self.MAJpropriete("IDmodele", "documents_modeles")
        self.MAJpropriete("IDmodelMail", "modeles_emails")

    def MAJpropriete(self, name, table):
        lstChamps = DATA_Tables.GetChamps_DATA_Tables(table)

        DB = GestionDB.DB()
        req = """SELECT *
        FROM %s
        WHERE categorie = 'facture'
        ORDER BY nom;""" % (table)
        DB.ExecuterReq(req, MsgBox="CTRL_Factures_options.MAJ_modele")
        listeDonnees = DB.ResultatReq()
        DB.Close()
        self.dictDonnees = {}
        choix = wxpg.PGChoices()
        selectionDefaut = None
        for record in listeDonnees:
            dicTemp = {}
            ix = 0
            ID = record[0]
            for champ in lstChamps:
                dicTemp[champ] = record[ix]
                ix += 1
            choix.Add(dicTemp["nom"], ID)
            self.dictDonnees[ID] = dicTemp
            if dicTemp["defaut"]:
                selectionDefaut = ID
        propriete = self.GetPropertyByName(name)
        if propriete:
            propriete.SetChoices(choix)
            self.RefreshProperty(propriete)
            if selectionDefaut != None:
                propriete.SetValue(selectionDefaut)

    def OnBoutonParametres(self, propriete=None):
        # ancienneValeur = propriete.GetValue()
        name = propriete.GetName()
        if name == "IDmodele":
            from Dlg import DLG_Modeles_docs
            dlg = DLG_Modeles_docs.Dialog(self, categorie="facture")
            dlg.ShowModal()
            ID = dlg.GetIDmodele()
            dlg.Destroy()
            if ID:
                propriete.SetValue(ID)
            self.MAJ_modeles()
        elif name == "IDmodelMail":
            from Dlg import DLG_Modeles_emails
            dlg = DLG_Modeles_emails.Dialog(self, categorie="recu_reglement")
            dlg.ShowModal()
            ID = dlg.GetIDmodele()
            dlg.Destroy()
            if ID:
                propriete.SetValue(ID)
            self.MAJ_modeles()

# Gestion des messages en bas de page ----------------------------------------------

class ListBox_Messages(wx.ListBox):
    def __init__(self, parent):
        wx.ListBox.__init__(self, parent, -1)
        self.parent = parent
        self.MAJ()

    def MAJ(self):
        self.dictDonnees = {}
        self.listeMessages = []
        self.Clear()
        DB = GestionDB.DB()
        req = """SELECT IDmessage, titre, texte
        FROM factures_messages
        ORDER BY titre;"""
        DB.ExecuterReq(req, MsgBox="ExecuterReq")
        listeMessages = DB.ResultatReq()
        DB.Close()
        if len(listeMessages) == 0: return None
        listeDonnees = []
        self.dictDonnees = {}
        self.listeMessages = []
        for IDmessage, titre, texte in listeMessages:
            self.Insert(titre, self.GetCount(), IDmessage)
            self.dictDonnees[IDmessage] = {"IDmessage": IDmessage, "titre": titre,
                                           "texte": texte}
            self.listeMessages.append((titre, texte))
        return listeDonnees

    def GetSelectionMessage(self):
        index = self.GetSelection()
        if index == -1: return None
        IDmessage = self.GetClientData(index)
        if IDmessage in self.dictDonnees:
            return self.dictDonnees[IDmessage]
        else:
            return None

    def Ajouter(self):
        dlg = Saisie_Message(self)
        if dlg.ShowModal() == wx.ID_OK:
            titre = dlg.GetTitre()
            texte = dlg.GetTexte()
            DB = GestionDB.DB()
            listeDonnees = [
                ("titre", titre),
                ("texte", texte),
            ]
            IDmessage = DB.ReqInsert("factures_messages", listeDonnees)
            DB.Close()
            self.MAJ()
        dlg.Destroy()

    def Modifier(self):
        message = self.GetSelectionMessage()
        if message == None:
            dlg = wx.MessageDialog(self,
                                   _("Vous n'avez sélectionné aucun message à modifier dans la liste !"),
                                   _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        IDmessage = message["IDmessage"]
        titre = message["titre"]
        texte = message["texte"]
        dlg = Saisie_Message(self, IDmessage, titre, texte)
        if dlg.ShowModal() == wx.ID_OK:
            titre = dlg.GetTitre()
            texte = dlg.GetTexte()
            DB = GestionDB.DB()
            listeDonnees = [
                ("titre", titre),
                ("texte", texte),
            ]
            DB.ReqMAJ("factures_messages", listeDonnees, "IDmessage", IDmessage)
            DB.Close()
            self.MAJ()
        dlg.Destroy()

    def Supprimer(self):
        message = self.GetSelectionMessage()
        if message == None:
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
            IDmessage = message["IDmessage"]
            DB = GestionDB.DB()
            DB.ReqDEL("factures_messages", "IDmessage", IDmessage)
            DB.Close()
            self.MAJ()
        dlg.Destroy()

    def GetMessages(self):
        """ Récupère les messages formatés pour l'impression des factures """
        messages = []
        for titre, texte in self.listeMessages:
            if texte[-1] != ".": texte += "."
            messages.append("<b>%s : </b>%s" % (titre, texte))
        return messages

class Saisie_Message(wx.Dialog):
    def __init__(self, parent, IDmessage=None, titre="", texte=""):
        wx.Dialog.__init__(self, parent, -1,
                           style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER | wx.MAXIMIZE_BOX | wx.MINIMIZE_BOX)
        self.parent = parent

        self.label_titre = wx.StaticText(self, -1, _("Titre :"))
        self.ctrl_titre = wx.TextCtrl(self, -1, titre)
        self.label_texte = wx.StaticText(self, -1, _("Texte :"))
        self.ctrl_texte = wx.TextCtrl(self, -1, texte, style=wx.TE_MULTILINE)

        self.bouton_aide = CTRL_Bouton_image.CTRL(self, texte=_("Aide"),
                                                  cheminImage=Chemins.GetStaticPath(
                                                      "Images/32x32/Aide.png"))
        self.bouton_ok = CTRL_Bouton_image.CTRL(self, texte=_("Ok"),
                                                cheminImage=Chemins.GetStaticPath(
                                                    "Images/32x32/Valider.png"))
        self.bouton_annuler = CTRL_Bouton_image.CTRL(self, id=wx.ID_CANCEL,
                                                     texte=_("Annuler"),
                                                     cheminImage=Chemins.GetStaticPath(
                                                         "Images/32x32/Annuler.png"))

        if IDmessage == None:
            self.SetTitle(_("Saisie d'un message"))
        else:
            self.SetTitle(_("Modification d'un message"))
        self.SetMinSize((350, 220))

        grid_sizer_base = wx.FlexGridSizer(rows=3, cols=1, vgap=10, hgap=10)
        grid_sizer_boutons = wx.FlexGridSizer(rows=1, cols=4, vgap=10, hgap=10)
        grid_sizer_contenu = wx.FlexGridSizer(rows=2, cols=2, vgap=10, hgap=10)
        grid_sizer_contenu.Add(self.label_titre, 0,
                               wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_contenu.Add(self.ctrl_titre, 0, wx.EXPAND, 0)
        grid_sizer_contenu.Add(self.label_texte, 0,
                               wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_contenu.Add(self.ctrl_texte, 0, wx.EXPAND, 0)
        grid_sizer_contenu.AddGrowableCol(1)
        grid_sizer_contenu.AddGrowableRow(1)
        grid_sizer_base.Add(grid_sizer_contenu, 1, wx.ALL | wx.EXPAND, 10)
        grid_sizer_boutons.Add(self.bouton_aide, 0, 0, 0)
        grid_sizer_boutons.Add((20, 20), 0, wx.EXPAND, 0)
        grid_sizer_boutons.Add(self.bouton_ok, 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_annuler, 0, 0, 0)
        grid_sizer_boutons.AddGrowableCol(1)
        grid_sizer_base.Add(grid_sizer_boutons, 1,
                            wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 10)
        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)
        grid_sizer_base.AddGrowableCol(0)
        grid_sizer_base.AddGrowableRow(0)
        self.Layout()
        self.CenterOnScreen()

        self.Bind(wx.EVT_BUTTON, self.OnBoutonOk, self.bouton_ok)

    def GetTitre(self):
        return self.ctrl_titre.GetValue()

    def GetTexte(self):
        return self.ctrl_texte.GetValue()

    def OnBoutonOk(self, event):
        if self.GetTitre() == "":
            dlg = wx.MessageDialog(self,
                                   _("Vous devez obligatoirement saisir un titre !"),
                                   _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            self.ctrl_titre.SetFocus()
            return

        if self.GetTexte() == "":
            dlg = wx.MessageDialog(self,
                                   _("Vous devez obligatoirement saisir un texte !"),
                                   _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            self.ctrl_texte.SetFocus()
            return

        self.EndModal(wx.ID_OK)

class CTRL_Messages(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, id=-1, style=wx.TAB_TRAVERSAL)
        self.parent = parent

        self.ctrl_messages = ListBox_Messages(self)
        self.ctrl_messages.SetMinSize((50, 50))

        self.bouton_ajouter_message = wx.BitmapButton(self, -1, wx.Bitmap(
            Chemins.GetStaticPath(u"Images/16x16/Ajouter.png"), wx.BITMAP_TYPE_ANY))
        self.bouton_modifier_message = wx.BitmapButton(self, -1, wx.Bitmap(
            Chemins.GetStaticPath(u"Images/16x16/Modifier.png"), wx.BITMAP_TYPE_ANY))
        self.bouton_supprimer_message = wx.BitmapButton(self, -1, wx.Bitmap(
            Chemins.GetStaticPath(u"Images/16x16/Supprimer.png"), wx.BITMAP_TYPE_ANY))

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_BUTTON, self.OnAjouterMessage, self.bouton_ajouter_message)
        self.Bind(wx.EVT_BUTTON, self.OnModifierMessage, self.bouton_modifier_message)
        self.Bind(wx.EVT_BUTTON, self.OnSupprimerMessage, self.bouton_supprimer_message)

    def __set_properties(self):
        self.ctrl_messages.SetToolTip(wx.ToolTip(
            _("Saisissez ou ou plusieurs messages qui apparaitront à la fin du document")))
        self.bouton_ajouter_message.SetToolTip(
            wx.ToolTip(_("Cliquez ici pour ajouter un message")))
        self.bouton_modifier_message.SetToolTip(wx.ToolTip(
            _("Cliquez ici pour modifier le message sélectionné dans la liste")))
        self.bouton_supprimer_message.SetToolTip(wx.ToolTip(
            _("Cliquez ici pour supprimer le message sélectionné dans la liste")))

    def __do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(rows=1, cols=2, vgap=5, hgap=5)
        grid_sizer_base.Add(self.ctrl_messages, 0, wx.EXPAND, 0)

        grid_sizer_boutons_message = wx.FlexGridSizer(rows=3, cols=1, vgap=1, hgap=2)
        grid_sizer_boutons_message.Add(self.bouton_ajouter_message, 0, 0, 0)
        grid_sizer_boutons_message.Add(self.bouton_modifier_message, 0, 0, 0)
        grid_sizer_boutons_message.Add(self.bouton_supprimer_message, 0, 0, 0)
        grid_sizer_base.Add(grid_sizer_boutons_message, 0, wx.EXPAND, 0)
        grid_sizer_base.AddGrowableCol(0)
        grid_sizer_base.AddGrowableRow(0)

        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)

    def OnAjouterMessage(self, event):
        self.ctrl_messages.Ajouter()

    def OnModifierMessage(self, event):
        self.ctrl_messages.Modifier()

    def OnSupprimerMessage(self, event):
        self.ctrl_messages.Supprimer()

    def GetMessages(self):
        return self.ctrl_messages.GetMessages()

# -----------------------------------------------------------------------------------

# Trame d'accompagnement propgrid avec message et boutons sauvegarde-reinit des choix
class CTRL(wx.Panel):
    def __init__(self, parent, affichage="horizontal", mail=False):
        wx.Panel.__init__(self, parent, id=-1, style=wx.TAB_TRAVERSAL)
        self.parent = parent
        self.affichage = affichage

        # Paramètres
        self.box_options_staticbox = wx.StaticBox(self, -1, _("Options d'impression"))
        self.ctrl_parametres = CTRL_Parametres(self, mail=mail)
        self.ctrl_parametres.Importation()
        self.bouton_reinit = CTRL_Propertygrid.Bouton_reinit(self, self.ctrl_parametres)
        self.bouton_sauve = CTRL_Propertygrid.Bouton_sauve(self, self.ctrl_parametres)
        self.ctrl_parametres.SetMinSize((440, 120))

        # Messages
        self.box_messages_staticbox = wx.StaticBox(self, -1, _("Messages"))
        self.ctrl_messages = CTRL_Messages(self)
        self.ctrl_messages.SetMinSize((200, -1))

        self.__do_layout()

    def __do_layout(self):
        if self.affichage == "horizontal":
            grid_sizer_base = wx.FlexGridSizer(rows=1, cols=2, vgap=10, hgap=20)
            grid_sizer_base.AddGrowableCol(1)
            grid_sizer_base.AddGrowableRow(0)
        else:
            grid_sizer_base = wx.FlexGridSizer(rows=2, cols=1, vgap=10, hgap=20)
            grid_sizer_base.AddGrowableCol(0)
            grid_sizer_base.AddGrowableRow(0)

        # Paramètres
        box_options = wx.StaticBoxSizer(self.box_options_staticbox, wx.VERTICAL)
        grid_sizer_parametres = wx.FlexGridSizer(rows=1, cols=2, vgap=5, hgap=5)
        grid_sizer_parametres.Add(self.ctrl_parametres, 1, wx.EXPAND, 0)

        grid_sizer_boutons = wx.FlexGridSizer(rows=3, cols=1, vgap=5, hgap=5)
        grid_sizer_boutons.Add(self.bouton_reinit, 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_sauve, 0, 0, 0)

        grid_sizer_parametres.Add(grid_sizer_boutons, 0, 0, 0)
        grid_sizer_parametres.AddGrowableRow(0)
        grid_sizer_parametres.AddGrowableCol(0)
        box_options.Add(grid_sizer_parametres, 1, wx.EXPAND | wx.ALL, 10)
        grid_sizer_base.Add(box_options, 1, wx.EXPAND, 0)

        # Messages
        box_messages = wx.StaticBoxSizer(self.box_messages_staticbox, wx.VERTICAL)
        box_messages.Add(self.ctrl_messages, 1, wx.EXPAND | wx.ALL, 10)
        grid_sizer_base.Add(box_messages, 1, wx.EXPAND, 0)

        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)

    def MemoriserParametres(self):
        self.ctrl_parametres.Sauvegarde()

    def GetOptions(self):
        dictOptions = {}

        # Récupération des paramètres
        if self.ctrl_parametres.Validation() == False:
            return False
        for nom, valeur in self.ctrl_parametres.GetValeurs().items():
            dictOptions[nom] = valeur

        # Récupération des messages
        dictOptions["messages"] = self.ctrl_messages.GetMessages()

        return dictOptions

# -- Pour tests -------------------------------------------------------------------

class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self, -1)
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_1.Add(panel, 1, wx.ALL | wx.EXPAND)
        self.SetSizer(sizer_1)
        self.ctrl = CTRL_Parametres(panel)
        self.boutonTest = wx.Button(panel, -1, _("Bouton de test"))
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_2.Add(self.ctrl, 1, wx.ALL | wx.EXPAND, 4)
        sizer_2.Add(self.boutonTest, 0, wx.ALL | wx.EXPAND, 4)
        panel.SetSizer(sizer_2)
        self.Layout()
        self.CentreOnScreen()
        self.Bind(wx.EVT_BUTTON, self.OnBoutonTest, self.boutonTest)

    def OnBoutonTest(self, event):
        """ Bouton Test """
        pass


if __name__ == '__main__':
    app = wx.App(0)
    # wx.InitAllImageHandlers()
    frame_1 = MyFrame(None, -1, _("TEST"), size=(700, 800))
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()


