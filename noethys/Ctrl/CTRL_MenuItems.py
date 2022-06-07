#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#-----------------------------------------------------------
# Application :    Noethys, branche Matthania
# Module : Items du Menu principal déporté de mainFrame
# Auteur:          Ivan LUCAS, JB
# Copyright:       (c) 2010-12 Ivan LUCAS, JB
# Licence:         Licence GNU GPL
#-----------------------------------------------------------

import wx
import FonctionsPerso
import codecs
from Utils.UTILS_Traduction import _
from Ctrl import CTRL_Saisie_transport
from Utils import UTILS_Utilisateurs
from Utils import UTILS_Fichiers


# ID pour la barre des menus
ID_DERNIER_FICHIER = 700
ID_PREMIERE_PERSPECTIVE = 500
ID_AFFICHAGE_PANNEAUX = 600

# ID pour la barre d'outils
ID_TB_GESTIONNAIRE = wx.Window.NewControlId()
ID_TB_LISTE_CONSO = wx.Window.NewControlId()
ID_TB_BADGEAGE = wx.Window.NewControlId()
ID_TB_REGLER_FACTURE = wx.Window.NewControlId()
ID_TB_CALCULATRICE = wx.Window.NewControlId()
ID_TB_UTILISATEUR = wx.Window.NewControlId()

# Destcription des items de la barre de menu
def GetListItemsMenu(self,menuTransports):
    return [
        # Fichier
        {"code": "menu_fichier", "label": _("Fichier"), "items": [
            {"code": "nouveau_fichier",
             "label": _("Créer un nouveau fichier"),
             "infobulle": _("Créer un nouveau fichier"),
             "image": "Images/16x16/Fichier_nouveau.png",
             "action": self.parent.On_fichier_Nouveau},
            {"code": "ouvrir_fichier", "label": _("Ouvrir un fichier"),
             "infobulle": _("Ouvrir un fichier existant"),
             "image": "Images/16x16/Fichier_ouvrir.png",
             "action": self.On_fichier_Ouvrir},
            {"code": "fermer_fichier", "label": _("Fermer le fichier"),
             "infobulle": _("Fermer le fichier ouvert"),
             "image": "Images/16x16/Fichier_fermer.png",
             "action": self.On_fichier_Fermer, "actif": False},
            "-",
            {"code": "fichier_informations",
             "label": _("Informations base de données"),
             "infobulle": _("Informations sur le fichier"),
             "image": "Images/16x16/Information.png",
             "action": self.On_fichier_Informations, "actif": False},
            "-",
            {"code": "creer_sauvegarde",
             "label": _("Créer une sauvegarde"),
             "infobulle": _("Créer une sauvegarde"),
             "image": "Images/16x16/Sauvegarder.png",
             "action": self.On_fichier_Sauvegarder},
            {"code": "restaurer_sauvegarde",
             "label": _("Restaurer une sauvegarde"),
             "infobulle": _("Restaurer une sauvegarde"),
             "image": "Images/16x16/Restaurer.png",
             "action": self.On_fichier_Restaurer},
            {"code": "sauvegardes_auto",
             "label": _("Sauvegardes automatiques"),
             "infobulle": _("Paramétrage des sauvegardes automatiques"),
             "image": "Images/16x16/Sauvegarder_param.png",
             "action": self.On_fichier_Sauvegardes_auto},
            "-",
            {"code": "convertir_fichier_reseau",
             "label": _("Convertir en fichier réseau"),
             "infobulle": _("Convertir le fichier en mode réseau"),
             "image": "Images/16x16/Conversion_reseau.png",
             "action": self.On_fichier_Convertir_reseau, "actif": False},
            {"code": "convertir_fichier_local",
             "label": _("Convertir en fichier local"),
             "infobulle": _("Convertir le fichier en mode local"),
             "image": "Images/16x16/Conversion_local.png",
             "action": self.On_fichier_Convertir_local, "actif": False},
            "-",
            {"code": "upgrade_base",
             "label": _("Upgrade de la Base de donnée"),
             "infobulle": _("Cet outil ajoute les tables et champs manquants"),
             "image": "Images/16x16/Outils.png",
             "action": self.On_upgrade_base, "actif": False},
            {"code": "upgrade_modules",
             "label": _("Mise à jour Noethys"),
             "infobulle": _("Cet outil permet d'importer un nouvelle version des programmes "),
             "image": "Images/16x16/Outils.png",
             "action": self.On_upgrade_modules, "actif": True},
            "-",
            {"code": "quitter", "label": _("Quitter"),
             "infobulle": _("Quitter Noethys"),
             "image": "Images/16x16/Quitter.png",
             "action": self.On_fichier_Quitter}
        ],
         },

        # Paramétrage
        {"code": "menu_parametrage", "label": _("Paramétrage"), "items": [
            {"code": "preferences", "label": _("Préférences"),
             "infobulle": _("Préférences"),
             "image": "Images/16x16/Mecanisme.png",
             "action": self.On_param_preferences},
            "-",
            {"code": "utilisateurs", "label": _("Utilisateurs"),
             "infobulle": _("Paramétrage des utilisateurs"),
             "image": "Images/16x16/Personnes.png",
             "action": self.On_param_utilisateurs},
            {"code": "modeles_droits", "label": _("Modèles de droits"),
             "infobulle": _("Paramétrage des modèles de droits"),
             "image": "Images/16x16/Droits.png",
             "action": self.On_param_modeles_droits},
            "-",
            {"code": "organisateur", "label": _("Organisateur"),
             "infobulle": _("Paramétrage des données sur l'organisateur"),
             "image": "Images/16x16/Organisateur.png",
             "action": self.On_param_organisateur},
            {"code": "groupes_activites",
             "label": _("Groupes d'activités"),
             "infobulle": _("Paramétrage des groupes d'activités"),
             "image": "Images/16x16/Groupe_activite.png",
             "action": self.On_param_groupes_activites},
            {"code": "activites", "label": _("Activités"),
             "infobulle": _("Paramétrage des activités"),
             "image": "Images/16x16/Activite.png",
             "action": self.On_param_activites},
            "-",
            {"code": "menu_parametrage_modeles", "label": _(u"Modèles"),
             "items": [
                 {"code": "modeles_documents",
                  "label": _(u"Modèles de documents"),
                  "infobulle": _(u"Paramétrage des modèles de documents"),
                  "image": "Images/16x16/Document.png",
                  "action": self.On_param_documents},
                 {"code": "modeles_emails", "label": _(u"Modèles d'Emails"),
                  "infobulle": _(u"Paramétrage des modèles d'Emails"),
                  "image": "Images/16x16/Emails_modele.png",
                  "action": self.On_param_modeles_emails},
                 {"code": "modeles_tickets", "label": _(u"Modèles de tickets"),
                  "infobulle": _(u"Paramétrage des modèles de tickets"),
                  "image": "Images/16x16/Ticket.png",
                  "action": self.On_param_modeles_tickets},
                 {"code": "modeles_contrats",
                  "label": _(u"Modèles de contrats"),
                  "infobulle": _(u"Paramétrage des modèles de contrats"),
                  "image": "Images/16x16/Contrat.png",
                  "action": self.On_param_modeles_contrats},
                 {"code": "modeles_plannings",
                  "label": _(u"Modèles de plannings"),
                  "infobulle": _(u"Paramétrage des modèles de plannings"),
                  "image": "Images/16x16/Calendrier.png",
                  "action": self.On_param_modeles_plannings},
                 {"code": "modeles_aides",
                  "label": _(u"Modèles d'aides journalières"), "infobulle": _(
                     u"Paramétrage des modèles d'aides journalières"),
                  "image": "Images/16x16/Mecanisme.png",
                  "action": self.On_param_modeles_aides},
                 {"code": "modeles_prestations",
                  "label": _(u"Modèles de prestations"),
                  "infobulle": _(u"Paramétrage des modèles de prestations"),
                  "image": "Images/16x16/Euro.png",
                  "action": self.On_param_modeles_prestations},
                 {"code": "modeles_commandes",
                  "label": _(u"Modèles de commandes de repas"), "infobulle": _(
                     u"Paramétrage des modèles de commandes de repas"),
                  "image": "Images/16x16/Repas.png",
                  "action": self.On_param_modeles_commandes},
             ],
             },
            "-",
            {"code": "procedures_badgeage",
             "label": _("Procédures de badgeage"),
             "infobulle": _("Paramétrage des procédures de badgeage"),
             "image": "Images/16x16/Badgeage.png",
             "action": self.On_param_badgeage},
            "-",
            {"code": "menu_parametrage_factures",
             "label": _("Facturation"), "items": [
                {"code": "gestion_articles",
                 "label": _("Gestion des articles"), "infobulle": _(
                    "Paramétrage des articles possibles sur les lignes de factures"),
                 "image": "Images/16x16/Activite.png",
                 "action": self.On_param_gestion_articles},
                {"code": "gestion_tarifs",
                 "label": _("Gestion des tarifs"), "infobulle": _(
                    "Paramétrage des associations d'articles par tarifs"),
                 "image": "Images/16x16/Mecanisme.png",
                 "action": self.On_param_gestion_tarifs},
                {"code": "lots_factures", "label": _("Lots de factures"),
                 "infobulle": _("Paramétrage des lots de factures"),
                 "image": "Images/16x16/Lot_factures.png",
                 "action": self.On_param_lots_factures},
                {"code": "lots_rappels", "label": _("Lots de rappels"),
                 "infobulle": _("Paramétrage des lots de rappels"),
                 "image": "Images/16x16/Lot_factures.png",
                 "action": self.On_param_lots_rappels},
            ],
             },
            {"code": "menu_parametrage_reglements",
             "label": _("Comptabilité"), "items": [
                {"code": "comptes_bancaires",
                 "label": _("Comptes bancaires"),
                 "infobulle": _("Paramétrage des comptes bancaires"),
                 "image": "Images/16x16/Reglement.png",
                 "action": self.On_param_comptes},
                {"code": "compta_comptes",
                 "label": _("Comptes comptables des articles"),
                 "infobulle": _(
                     "Paramétrage des comptes comptables des articles"),
                 "image": "Images/16x16/Reglement.png",
                 "action": self.On_param_comptes_comptables},
                "-",
                {"code": "modes_reglements",
                 "label": _("Modes de règlements"),
                 "infobulle": _("Paramétrage des modes de règlements"),
                 "image": "Images/16x16/Mode_reglement.png",
                 "action": self.On_param_modes_reglements},
                {"code": "emetteurs",
                 "label": _("Emetteurs de règlements"),
                 "infobulle": _("Paramétrage des émetteurs de règlements"),
                 "image": "Images/16x16/Mode_reglement.png",
                 "action": self.On_param_emetteurs},
                "-",
                {"code": "compta_exercices",
                 "label": _("Exercices comptables"),
                 "infobulle": _("Paramétrage des exercices comptables"),
                 "image": "Images/16x16/Reglement.png",
                 "action": self.On_param_exercices},
            ],
             },
            {"code": "menu_parametrage_prelevements",
             "label": _("Prélèvement automatique"), "items": [
                {"code": "etablissements_bancaires",
                 "label": _("Etablissements bancaires"), "infobulle": _(
                    "Paramétrage des établissements bancaires"),
                 "image": "Images/16x16/Banque.png",
                 "action": self.On_param_banques},
            ],
             },
            "-",
            {"code": "menu_parametrage_renseignements",
             "label": _("Renseignements"), "items": [
                {"code": "questionnaires", "label": _("Questionnaires"),
                 "infobulle": _("Paramétrage des questionnaires"),
                 "image": "Images/16x16/Questionnaire.png",
                 "action": self.On_param_questionnaires},
                {"code": "types_pieces", "label": _("Types de pièces"),
                 "infobulle": _("Paramétrage des types de pièces"),
                 "image": "Images/16x16/Piece.png",
                 "action": self.On_param_pieces},
                {"code": "regimes_sociaux", "label": _("Régimes sociaux"),
                 "infobulle": _("Paramétrage des régimes sociaux"),
                 "image": "Images/16x16/Mecanisme.png",
                 "action": self.On_param_regimes},
                {"code": "caisses", "label": _("Caisses"),
                 "infobulle": _("Paramétrage des caisses"),
                 "image": "Images/16x16/Mecanisme.png",
                 "action": self.On_param_caisses},
                {"code": "categories_travail",
                 "label": _("Catégories socio-professionnelles"),
                 "infobulle": _(
                     "Paramétrage des catégories socio-professionnelles"),
                 "image": "Images/16x16/Camion.png",
                 "action": self.On_param_categories_travail},
                {"code": "villes", "label": _("Villes et codes postaux"),
                 "infobulle": _("Paramétrage des villes et codes postaux"),
                 "image": "Images/16x16/Carte.png",
                 "action": self.On_param_villes},
                {"code": "secteurs", "label": _("Pays postaux"),
                 "infobulle": _("Paramétrage des pays des adresses"),
                 "image": "Images/16x16/Secteur.png",
                 "action": self.On_param_secteurs},
                {"code": "types_sieste", "label": _("Types de sieste"),
                 "infobulle": _("Paramétrage des types de sieste"),
                 "image": "Images/16x16/Reveil.png",
                 "action": self.On_param_types_sieste},
                {"code": "maladies", "label": _("Maladies"),
                 "infobulle": _("Paramétrage des maladies"),
                 "image": "Images/16x16/Medical.png",
                 "action": self.On_param_maladies},
                {"code": "vaccins", "label": _("Vaccins"),
                 "infobulle": _("Paramétrage des vaccins"),
                 "image": "Images/16x16/Seringue.png",
                 "action": self.On_param_vaccins},
                {"code": "medecins", "label": _("Médecins"),
                 "infobulle": _("Paramétrage des médecins"),
                 "image": "Images/16x16/Medecin.png",
                 "action": self.On_param_medecins},
            ],
             },
            menuTransports,
            "-",
            {"code": "categories_messages",
             "label": _("Catégories de messages"),
             "infobulle": _("Paramétrage des catégories de messages"),
             "image": "Images/16x16/Mail.png",
             "action": self.On_param_categories_messages},
            {"code": "adresses_exp_mails",
             "label": _("Adresses d'expédition d'Emails"), "infobulle": _(
                "Paramétrage des adresses d'expédition d'Emails"),
             "image": "Images/16x16/Emails_exp.png",
             "action": self.On_param_emails_exp},
            {"code": "listes_diffusion", "label": _("Listes de diffusion"),
             "infobulle": _("Paramétrage des listes de diffusion"),
             "image": "Images/16x16/Liste_diffusion.png",
             "action": self.On_param_listes_diffusion},
            "-",
            {"code": "menu_parametrage_calendrier",
             "label": _("Calendrier"), "items": [
                {"code": "vacances", "label": _("Vacances"),
                 "infobulle": _("Paramétrage des vacances"),
                 "image": "Images/16x16/Calendrier.png",
                 "action": self.On_param_vacances},
                {"code": "feries", "label": _("Jours fériés"),
                 "infobulle": _("Paramétrage des jours fériés"),
                 "image": "Images/16x16/Jour.png",
                 "action": self.On_param_feries},
            ],
             },
            "-",
            {"code": "menu_parametrage_complements",
             "label": _("Compléments d'origine"), "items": [
                {"code": "types_cotisations", "label": _(u"Cotisations"),
                 "infobulle": _(u"Paramétrage des types de cotisations"),
                 "image": "Images/16x16/Identite.png",
                 "action": self.On_param_types_cotisations},
                {"code": "menu_parametrage_locations",
                 "label": _(u"Locations"), "items": [
                    {"code": "categories_produits",
                     "label": _(u"Catégories de produits"),
                     "infobulle": _(u"Paramétrage des catégories de produits"),
                     "image": "Images/16x16/Categorie_produits.png",
                     "action": self.On_param_categories_produits},
                    {"code": "produits", "label": _(u"Produits"),
                     "infobulle": _(u"Paramétrage des produits"),
                     "image": "Images/16x16/Produit.png",
                     "action": self.On_param_produits},
                ],
                 },
                "-",
                {"code": "periodes_gestion",
                 "label": _(u"Périodes de gestion"),
                 "infobulle": _(u"Paramétrage des périodes de gestion"),
                 "image": "Images/16x16/Mecanisme.png",
                 "action": self.On_param_periodes_gestion},
                "-",
                {"code": "menu_restauration", "label": _(u"Restauration"),
                 "items": [
                     {"code": "restaurateurs",
                      "label": _(u"Restaurateurs"),
                      "infobulle": _(u"Paramétrage des restaurateurs"),
                      "image": "Images/16x16/Restaurateur.png",
                      "action": self.On_param_restaurateurs},
                     {"code": "menus_categories",
                      "label": _(u"Catégories de menus"), "infobulle": _(
                         u"Paramétrage des catégories de menus"),
                      "image": "Images/16x16/Menu.png",
                      "action": self.On_param_menus_categories},
                     {"code": "menus_legendes",
                      "label": _(u"Légendes de menus"),
                      "infobulle": _(u"Paramétrage des légendes de menus"),
                      "image": "Images/16x16/Etiquettes.png",
                      "action": self.On_param_menus_legendes},
                 ],
                 },
                "-",
            ],
             },
            "-",
        ],
         },

        # Affichage
        {"code": "menu_affichage", "label": _("Affichage"), "items": [
            {"code": "perspective_defaut",
             "label": _("Disposition par défaut"),
             "infobulle": _("Afficher la disposition par défaut"),
             "action": self.On_affichage_perspective_defaut,
             "genre": wx.ITEM_CHECK},
            "-",
            {"code": "perspective_save",
             "label": _("Sauvegarder la disposition actuelle"),
             "infobulle": _("Sauvegarder la disposition actuelle"),
             "image": "Images/16x16/Perspective_ajouter.png",
             "action": self.On_affichage_perspective_save},
            {"code": "perspective_suppr",
             "label": _("Supprimer des dispositions"),
             "infobulle": _("Supprimer des dispositions enregistrées"),
             "image": "Images/16x16/Perspective_supprimer.png",
             "action": self.On_affichage_perspective_suppr},
            "-",
            "-",
            {"code": "affichage_barres_outils",
             "label": _("Barres d'outils personnelles"),
             "infobulle": _("Barres d'outils personnelles"),
             "image": "Images/16x16/Barre_outils.png",
             "action": self.On_affichage_barres_outils},
            "-",
            {"code": "actualiser_affichage",
             "label": _("Actualiser l'affichage\tF11"),
             "infobulle": _("Actualiser l'affichage de la page d'accueil"),
             "image": "Images/16x16/Actualiser2.png",
             "action": self.On_affichage_actualiser},
        ],
         },

        # Outils
        {"code": "menu_outils", "label": _("Outils"), "items": [
            {"code": "statistiques", "label": _(u"Statistiques"),
             "infobulle": _(u"Statistiques"),
             "image": "Images/16x16/Barres.png",
             "action": self.On_outils_stats},
            "-",
            {"code": "commandes_repas", "label": _(u"Commandes des repas"),
             "infobulle": _(u"Commandes des repas"),
             "image": "Images/16x16/Repas.png",
             "action": self.On_conso_commandes},
            {"code": "menus", "label": _(u"Menus des repas"),
             "infobulle": _(u"Menus des repas"),
             "image": "Images/16x16/Menu.png", "action": self.On_conso_menus},
            "-",
            {"code": "nomadhys_synchro",
             "label": _(u"Nomadhys - L'application nomade"), "infobulle": _(
                u"Synchroniser et configurer Nomadhys, l'application nomade de Noethys"),
             "image": "Images/16x16/Nomadhys.png",
             "action": self.On_outils_nomadhys_synchro},
            "-",
            {"code": "connecthys_synchro",
             "label": _(u"Connecthys - Le portail internet"), "infobulle": _(
                u"Synchroniser et configurer Connecthys, le portail internet de Noethys"),
             "image": "Images/16x16/Connecthys.png",
             "action": self.On_outils_connecthys_synchro},
            {"code": "connecthys_traiter",
             "label": _(u"Traiter les demandes du portail"),
             "infobulle": _(u"Traiter les demandes du portail"),
             "image": "Images/16x16/Connecthys.png",
             "action": self.On_outils_connecthys_traiter},
            "-",
            {"code": "carnet_adresses", "label": _(u"Carnet d'adresses"),
             "infobulle": _(u"Carnet d'adresses"),
             "image": "Images/16x16/Carnet.png",
             "action": self.On_outils_carnet},
            {"code": "editeur_emails", "label": _(u"Editeur d'Emails"),
             "infobulle": _(u"Editeur d'Emails"),
             "image": "Images/16x16/Editeur_email.png",
             "action": self.On_outils_emails},
            {"code": "envoi_sms", "label": _(u"Envoi de SMS"),
             "infobulle": _(u"Envoi de SMS"), "image": "Images/16x16/Sms.png",
             "action": self.On_outils_sms},
            "-",
            {"code": "calculatrice", "label": _(u"Calculatrice\tF12"),
             "infobulle": _(u"Calculatrice"),
             "image": "Images/16x16/Calculatrice.png",
             "action": self.On_outils_calculatrice},
            {"code": "calendrier", "label": _(u"Calendrier"),
             "infobulle": _(u"Calendrier"),
             "image": "Images/16x16/Calendrier.png",
             "action": self.On_outils_calendrier},
            "-",
            {"code": "villes2", "label": _(u"Villes et codes postaux"),
             "infobulle": _(u"Villes et codes postaux"),
             "image": "Images/16x16/Carte.png",
             "action": self.On_outils_villes},
            {"code": "geolocalisation", "label": _(u"Géolocalisation GPS"),
             "infobulle": _(u"Géolocalisation GPS"),
             "image": "Images/16x16/Carte.png", "action": self.On_outils_gps},
            {"code": "horaires_soleil", "label": _(u"Horaires du soleil"),
             "infobulle": _(u"Horaires du soleil"),
             "image": "Images/16x16/Soleil.png",
             "action": self.On_outils_horaires_soleil},
            "-",
            {"code": "connexions_reseau",
             "label": _(u"Liste des connexions réseau"),
             "infobulle": _(u"Liste des connexions réseau"),
             "image": "Images/16x16/Connexion.png",
             "action": self.On_outils_connexions},
            "-",
            {"code": "messages", "label": _(u"Messages"),
             "infobulle": _(u"Liste des messages"),
             "image": "Images/16x16/Mail.png",
             "action": self.On_outils_messages},
            {"code": "historique", "label": _(u"Historique"),
             "infobulle": _(u"Historique"),
             "image": "Images/16x16/Historique.png",
             "action": self.On_outils_historique},
            "-",
            {"code": "menu_outils_utilitaires",
             "label": _("Utilitaires administrateur"), "items": [
                {"code": "correcteur",
                 "label": _("Correcteur d'anomalies"),
                 "infobulle": _("Correcteur d'anomalies"),
                 "image": "Images/16x16/Depannage.png",
                 "action": self.On_outils_correcteur},
                {"code": "coherence", "label": _("Vérification cohérence"),
                 "infobulle": _(
                     "Vérification cohérence des tables Noethys"),
                 "image": "Images/16x16/Smile.png",
                 "action": self.On_outils_coherence},
                "-",
                {"code": "outils_informations",
                 "label": _("Informations base de données"),
                 "infobulle": _("Informations sur le fichier"),
                 "image": "Images/16x16/Information.png",
                 "action": self.On_fichier_Informations, "actif": True},
                {"code": "outils_upgrade_base",
                 "label": _("Upgrade de la Base de donnée"),
                 "infobulle": _(
                     "Cet outil ajoute les tables et champs manquants"),
                 "image": "Images/16x16/Outils.png",
                 "action": self.On_upgrade_base, "actif": True},
                {"code": "outils_upgrade_modules",
                 "label": _("Mise à jour Noethys"),
                 "infobulle": _(
                     "Cet outil permet d'importer un nouvelle version des programmes "),
                 "image": "Images/16x16/Outils.png",
                 "action": self.On_upgrade_modules, "actif": True},
                {"code": "purger_historique",
                 "label": _("Purger l'historique"),
                 "infobulle": _("Purger l'historique"),
                 "image": "Images/16x16/Poubelle.png",
                 "action": self.On_outils_purger_historique},
                {"code": "purger_journal_badgeage",
                 "label": _("Purger le journal de badgeage"),
                 "infobulle": _("Purger le journal de badgeage"),
                 "image": "Images/16x16/Poubelle.png",
                 "action": self.On_outils_purger_journal_badgeage},
                {"code": "purger_archives_badgeage",
                 "label": _("Purger les archives des badgeages importés"),
                 "infobulle": _(
                     "Purger les archives des badgeages importés"),
                 "image": "Images/16x16/Poubelle.png",
                 "action": self.On_outils_purger_archives_badgeage},
                {"code": "purger_repertoire_updates",
                 "label": _("Purger le répertoire Updates"),
                 "infobulle": _("Purger le répertoire Updates"),
                 "image": "Images/16x16/Poubelle.png",
                 "action": self.On_outils_purger_rep_updates},
                "-",
                {"code": "extensions", "label": _("Extensions"),
                 "infobulle": _("Extensions"),
                 "image": "Images/16x16/Terminal.png",
                 "action": self.On_outils_extensions},
                {"code": "procedures", "label": _("Procédures"),
                 "infobulle": _("Procédures"),
                 "image": "Images/16x16/Outils.png",
                 "action": self.On_outils_procedures},
                {"code": "reinitialisation", "label": _(
                    "Réinitialisation du fichier de configuration"),
                 "infobulle": _(
                     "Réinitialisation du fichier de configuration"),
                 "image": "Images/16x16/Outils.png",
                 "action": self.On_outils_reinitialisation},
                {"code": "transfert_tables",
                 "label": _("Transférer des tables"),
                 "infobulle": _("Transférer des tables de données"),
                 "image": "Images/16x16/Outils.png",
                 "action": self.On_outils_transfert_tables},
                "-",
                {"code": "liste_prestations_sans_conso", "label": _(
                    "Liste des prestations sans consommations associées"),
                 "infobulle": _(
                     "Liste des prestations sans conso. associées"),
                 "image": "Images/16x16/Medecin3.png",
                 "action": self.On_outils_prestations_sans_conso},
                {"code": "liste_conso_sans_prestations", "label": _(
                    "Liste des consommations sans prestations associées"),
                 "infobulle": _(
                     "Liste des conso. sans prestations associées"),
                 "image": "Images/16x16/Medecin3.png",
                 "action": self.On_outils_conso_sans_prestations},
                {"code": "deverrouillage_forfaits", "label": _(
                    "Déverrouillage des consommations de forfaits"),
                 "infobulle": _(
                     "Déverrouillage des consommations de forfaits"),
                 "image": "Images/16x16/Medecin3.png",
                 "action": self.On_outils_deverrouillage_forfaits},
                "-",
                {"code": "appliquer_tva", "label": _(
                    "Appliquer un taux de TVA à un lot de prestations"),
                 "infobulle": _(
                     "Appliquer un taux de TVA à un lot de prestations"),
                 "image": "Images/16x16/Outils.png",
                 "action": self.On_outils_appliquer_tva},
                {"code": "appliquer_code_comptable", "label": _(
                    "Appliquer un code comptable à un lot de prestations"),
                 "infobulle": _(
                     "Appliquer un code comptable à des prestations"),
                 "image": "Images/16x16/Outils.png",
                 "action": self.On_outils_appliquer_code_comptable},
                {"code": "conversion_rib_sepa",
                 "label": _("Convertir les RIB nationaux en mandats SEPA"),
                 "infobulle": _(
                     "Convertir les RIB nationaux en mandats SEPA"),
                 "image": "Images/16x16/Outils.png",
                 "action": self.On_outils_conversion_rib_sepa},
                {"code": "creation_titulaires_helios",
                 "label": _("Création automatique des titulaires Hélios"),
                 "infobulle": _(
                     "Création automatique des titulaires Hélios"),
                 "image": "Images/16x16/Outils.png",
                 "action": self.On_outils_creation_titulaires_helios},
                "-",
                {"code": "console_python", "label": _("Console Python"),
                 "infobulle": _("Console Python"),
                 "image": "Images/16x16/Python.png",
                 "action": self.On_outils_console_python},
                {"code": "console_sql", "label": _("Console SQL"),
                 "infobulle": _("Console SQL"),
                 "image": "Images/16x16/Sql.png",
                 "action": self.On_outils_console_sql},
                {"code": "liste_perso",
                 "label": _("Liste personnalisée SQL"),
                 "infobulle": _("Liste personnalisée SQL"),
                 "image": "Images/16x16/Sql.png",
                 "action": self.On_outils_liste_perso},
            ],
             },
            {"code": "ajoutTables", "label": _(u"Ajout de tables optionnelles"),
             "infobulle": _(u"Ajoute des tables optionnelles"),
             "image": "Images/16x16/Depannage.png",
             "action": self.On_outils_ajoutTables},
            "-",
        ],
         },

        # Individus
        {"code": "menu_individus", "label": _("Individus"), "items": [
            {"code": "liste_inscriptions",
             "label": _("Liste inscriptions aux activités"),
             "infobulle": _(
                 "Editer une liste des inscriptions pluri-activités et paramétrable"),
             "image": "Images/16x16/Smile.png",
             "action": self.On_individus_inscriptions},
            {"code": "liste_inscriptions_Y",
             "label": _("Liste inscriptions à une activité"),
             "infobulle": _(
                 "Editer une liste simple des inscriptions mono activité"),
             "image": "Images/16x16/Activite.png",
             "action": self.On_individus_inscriptions_Y},
            {"code": "export_remplissage",
             "label": _("Export vers synthèse remplissage"),
             "infobulle": _(
                 "Export d'un fichier excel à copier-coller dans de la bureautique"),
             "image": "Images/16x16/Smile.png",
             "action": self.On_export_remplissage},
            "-",
            {"code": "liste_contrats", "label": _("Liste des contrats"),
             "infobulle": _("Editer une liste des contrats"),
             "image": "Images/16x16/Contrat.png",
             "action": self.On_individus_contrats},
            {"code": "liste_individus", "label": _("Liste des individus"),
             "infobulle": _("Editer une liste des individus"),
             "image": "Images/16x16/Personnes.png",
             "action": self.On_individus_individus},
            {"code": "liste_familles", "label": _("Liste des familles"),
             "infobulle": _("Liste des familles"),
             "image": "Images/16x16/Famille.png",
             "action": self.On_individus_familles},
            {"code": "individus_edition_etiquettes",
             "label": _("Edition d'étiquettes Matthania"), "infobulle": _(
                "Edition d'étiquettes et de badges au format PDF"),
             "image": "Images/16x16/Smile.png",
             "action": self.On_individus_edition_etiquettes},
            "-",
            {"code": "menu_individus_transports",
             "label": _(u"Liste des transports"), "items": [
                {"code": "liste_detail_transports",
                 "label": _(u"Liste récapitulative des transports"),
                 "infobulle": _(
                     u"Editer une liste récapitulative des transports"),
                 "image": "Images/16x16/Transport.png",
                 "action": self.On_individus_transports_recap},
                {"code": "liste_recap_transports",
                 "label": _(u"Liste détaillée des transports"),
                 "infobulle": _(u"Editer une liste détaillée des transports"),
                 "image": "Images/16x16/Transport.png",
                 "action": self.On_individus_transports_detail},
                "-",
                {"code": "liste_prog_transports",
                 "label": _(u"Liste des programmations de transports"),
                 "infobulle": _(
                     u"Editer une liste des programmations de transports"),
                 "image": "Images/16x16/Transport.png",
                 "action": self.On_individus_transports_prog},
            ],
             },
            "-",
            {"code": "liste_anniversaires",
             "label": _(u"Liste des anniversaires"),
             "infobulle": _(u"Editer une liste des anniversaires"),
             "image": "Images/16x16/Anniversaire.png",
             "action": self.On_individus_anniversaires},
            {"code": "liste_infos_medicales",
             "label": _(u"Liste des informations médicales"),
             "infobulle": _(u"Editer une liste des informations médicales"),
             "image": "Images/16x16/Medical.png",
             "action": self.On_individus_infos_med},
            {"code": "liste_pieces_fournies",
             "label": _(u"Liste des pièces fournies"),
             "infobulle": _(u"Editer la liste des pièces fournies"),
             "image": "Images/16x16/Piece.png",
             "action": self.On_individus_pieces_fournies},
            {"code": "liste_pieces_fournies",
             "label": _(u"Liste des pièces manquantes"),
             "infobulle": _(u"Editer la liste des pièces manquantes"),
             "image": "Images/16x16/Piece.png",
             "action": self.On_individus_pieces_manquantes},
            {"code": "liste_regimes_caisses",
             "label": _(u"Liste des régimes et caisses des familles"),
             "infobulle": _(
                 u"Editer la liste des régimes et caisses des familles"),
             "image": "Images/16x16/Mecanisme.png",
             "action": self.On_individus_regimes_caisses},
            {"code": "liste_quotients",
             "label": _(u"Liste des quotients familiaux/revenus"),
             "infobulle": _(
                 u"Editer la liste des quotients familiaux/revenus des familles"),
             "image": "Images/16x16/Calculatrice.png",
             "action": self.On_individus_quotients},
            {"code": "liste_mandats_sepa",
             "label": _(u"Liste des mandats SEPA"),
             "infobulle": _(u"Editer la liste des mandats SEPA"),
             "image": "Images/16x16/Prelevement.png",
             "action": self.On_individus_mandats},
            {"code": "liste_codes_comptables",
             "label": _(u"Liste des codes comptables"), "infobulle": _(
                u"Editer la liste des codes comptables des familles"),
             "image": "Images/16x16/Export_comptable.png",
             "action": self.On_individus_codes_comptables},
            {"code": "liste_comptes_internet",
             "label": _(u"Liste des comptes internet"),
             "infobulle": _(u"Editer la liste des comptes internet"),
             "image": "Images/16x16/Connecthys.png",
             "action": self.On_individus_comptes_internet},
            "-",
            {"code": "importer_photos",
             "label": _(u"Importer des photos individuelles"),
             "infobulle": _(u"Importer des photos individuelles"),
             "image": "Images/16x16/Photos.png",
             "action": self.On_individus_importer_photos},
            "-",
            {"code": "menu_individus_importation",
             "label": _(u"Importer des familles ou des individus"), "items": [
                {"code": "importation_individus_csv", "label": _(
                    u"Importer des individus ou des familles depuis un fichier Excel ou CSV"),
                 "infobulle": _(u"Importer des individus ou des familles"),
                 "image": "Images/16x16/Document_import.png",
                 "action": self.On_individus_importer_csv},
                {"code": "importation_individus_fichier", "label": _(
                    u"Importer des familles depuis un fichier Noethys"),
                 "infobulle": _(
                     u"Importer des familles depuis un fichier Noethys"),
                 "image": "Images/16x16/Document_import.png",
                 "action": self.On_individus_importer_fichier},
            ],
             },
            {"code": "exporter_familles",
             "label": _(u"Exporter les familles au format XML"),
             "infobulle": _(u"Exporter les familles au format XML"),
             "image": "Images/16x16/Document_export.png",
             "action": self.On_individus_exporter_familles},
            {"code": "archiver_individus",
             "label": _(u"Archiver et effacer des individus"),
             "infobulle": _(u"Archiver et effacer des individus"),
             "image": "Images/16x16/Archiver.png",
             "action": self.On_individus_archiver_individus},
            "-",
            {"code": "individus_edition_etiquettes",
             "label": _(u"Edition d'étiquettes et de badges"), "infobulle": _(
                u"Edition d'étiquettes et de badges au format PDF"),
             "image": "Images/16x16/Etiquette2.png",
             "action": self.On_individus_etiquettes_original},
        ],
         },

        # Consommations
        {"code": "menu_consommations", "label": _("Consommations"),
         "items": [
             {"code": "liste_consommations",
              "label": _("Liste des consommations"),
              "infobulle": _("Editer une liste des consommations"),
              "image": "Images/16x16/Imprimante.png",
              "action": self.On_imprim_conso_journ},
             {"code": "gestionnaire_conso",
              "label": _("Gestionnaire des consommations"),
              "infobulle": _("Gestionnaire des consommations"),
              "image": "Images/16x16/Calendrier.png",
              "action": self.On_conso_gestionnaire},
             "-",
             {"code": "traitement_lot_conso",
              "label": _("Traitement par lot"),
              "infobulle": _("Traitement par lot"),
              "image": "Images/16x16/Calendrier_modification.png",
              "action": self.On_conso_traitement_lot},
             "-",
             {"code": "liste_attente", "label": _("Liste d'attente"),
              "infobulle": _("Liste d'attente"),
              "image": "Images/16x16/Liste_attente.png",
              "action": self.On_conso_attente},
             {"code": "liste_refus",
              "label": _("Liste des places refusées"),
              "infobulle": _("Liste des places refusées"),
              "image": "Images/16x16/Places_refus.png",
              "action": self.On_conso_refus},
             {"code": "liste_absences", "label": _("Liste des absences"),
              "infobulle": _("Liste des absences"),
              "image": "Images/16x16/absenti.png",
              "action": self.On_conso_absences},
             "-",
             {"code": "synthese_conso",
              "label": _("Synthèse des consommations"),
              "infobulle": _("Synthèse des consommations"),
              "image": "Images/16x16/Diagramme.png",
              "action": self.On_conso_synthese_conso},
             {"code": "etat_global", "label": _("Etat global"),
              "infobulle": _("Etat global"),
              "image": "Images/16x16/Tableaux.png",
              "action": self.On_conso_etat_global},
             {"code": "etat_nominatif", "label": _("Etat nominatif"),
              "infobulle": _("Etat nominatif"),
              "image": "Images/16x16/Tableaux.png",
              "action": self.On_conso_etat_nominatif},
             "-",
             {"code": "badgeage", "label": _("Badgeage"),
              "infobulle": _("Badgeage"),
              "image": "Images/16x16/Badgeage.png",
              "action": self.On_conso_badgeage},
             {"code": "remplissage", "label": _("Remplissage Jours"),
              "infobulle": _("Suivi des consommations par jour"),
              "image": "Images/16x16/Badgeage.png",
              "action": self.On_conso_remplissage},
         ],
         },

        # Facturation
        {"code": "menu_facturation", "label": _("Facturation"), "items": [
            {"code": "facturation_verification_ventilation",
             "label": _("Vérifier la ventilation"),
             "infobulle": _("Vérifier la ventilation des règlements"),
             "image": "Images/16x16/Repartition.png",
             "action": self.On_reglements_ventilation},
            "-",
            {"code": "menu_facturation_rappels",
             "label": _("Lettres de rappel"), "items": [
                {"code": "rappels_generation", "label": _("Génération"),
                 "infobulle": _("Génération des lettres de rappel"),
                 "image": "Images/16x16/Generation.png",
                 "action": self.On_facturation_rappels_generation},
                "-",
                {"code": "rappels_email",
                 "label": _("Transmettre par Email"), "infobulle": _(
                    "Transmettre les lettres de rappel par Email"),
                 "image": "Images/16x16/Emails_exp.png",
                 "action": self.On_facturation_rappels_email},
                {"code": "rappels_imprimer", "label": _("Imprimer"),
                 "infobulle": _("Imprimer des lettres de rappel"),
                 "image": "Images/16x16/Imprimante.png",
                 "action": self.On_facturation_rappels_imprimer},
                "-",
                {"code": "rappels_liste",
                 "label": _("Liste des lettres de rappel"),
                 "infobulle": _("Liste des lettres de rappel"),
                 "image": "Images/16x16/Facture.png",
                 "action": self.On_facturation_rappels_liste},
            ],
             },
            {"code": "menu_facturation_attestations",
             "label": _("Attestations de présence"), "items": [
                {"code": "attestations_generation",
                 "label": _("Génération attestations de présence"),
                 "infobulle": _("Génération des attestations de présence"),
                 "image": "Images/16x16/Generation.png",
                 "action": self.On_facturation_attestations_generation},
                {"code": "attestations_liste",
                 "label": _("Liste des attestations de présence"),
                 "infobulle": _(
                     "Liste des attestations de présence générées"),
                 "image": "Images/16x16/Facture.png",
                 "action": self.On_facturation_attestations_liste},
            ],
             },
            {"code": "attestations_cerfa_generation",
             "label": _("CERFA Dons aux oeuvres"), "infobulle": _(
                "Génération des attestations fiscale pour les dons"),
             "image": "Images/16x16/Smile.png",
             "action": self.On_facturation_attestations_cerfa_generation},
            "-",
            {"code": "liste_prestations",
             "label": _("Liste des prestations"),
             "infobulle": _("Liste des prestations"),
             "image": "Images/16x16/Smile.png",
             "action": self.On_facturation_liste_prestations},
            {"code": "recalcul_prestations",
             "label": _("Recalculer des prestations"),
             "infobulle": _("Recalculer des prestations"),
             "image": "Images/16x16/Impayes.png",
             "action": self.On_facturation_recalculer_prestations},
            "-",
            {"code": "liste_parrainages",
             "label": _("Liste des parrainages"),
             "infobulle": _("Liste de contrôle des parrainages"),
             "image": "Images/16x16/Smile.png",
             "action": self.On_facturation_liste_parrainages},
            "-",
            {"code": "liste_soldes_familles", "label": _("Balance âgée"),
             "infobulle": _("Liste des soldes avec antériorité"),
             "image": "Images/16x16/Smile.png",
             "action": self.On_facturation_soldes},
            {"code": "liste_soldes_individus",
             "label": _("Liste des soldes individuels"),
             "infobulle": _("Liste des soldes individuels"),
             "image": "Images/16x16/Euro.png",
             "action": self.On_facturation_soldes_individuels},
            "-",
            {"code": "synthese_impayes",
             "label": _("Synthèse des impayés"),
             "infobulle": _("Synthèse des impayés"),
             "image": "Images/16x16/Diagramme.png",
             "action": self.On_facturation_synthese_impayes},
            {"code": "solder_impayes", "label": _("Solder les impayés"),
             "infobulle": _("Solder les impayés"),
             "image": "Images/16x16/Impayes.png",
             "action": self.On_facturation_solder_impayes},
            "-",
            {"code": "synthese_prestations",
             "label": _("Synthèse des prestations"),
             "infobulle": _("Synthèse des prestations"),
             "image": "Images/16x16/Diagramme.png",
             "action": self.On_facturation_synthese_prestations},
            {"code": "prestations_villes",
             "label": _("Liste des prestations par famille"),
             "infobulle": _("Liste des prestations par famille"),
             "image": "Images/16x16/Euro.png",
             "action": self.On_facturation_prestations_villes},
            "-",
            {"code": "export_compta", "label": _("Analyse facturation"),
             "infobulle": _(
                 "Analyser les transferts comptables ou le reste à transférer"),
             "image": "Images/16x16/Smile.png",
             "action": self.On_facturation_analyse_facturation},
            {"code": "export_compta",
             "label": _("Export des écritures comptables"),
             "infobulle": _("Exporter les écritures comptables"),
             "image": "Images/16x16/Smile.png",
             "action": self.On_facturation_export_compta},
            {"code": "menu_facturation_complements",
             "label": _("Compléments d'origine"), "items": [
                # Cotisations
                {"code": "menu_cotisations", "label": _(u"Cotisations"),
                 "items": [
                     {"code": "liste_cotisations",
                      "label": _(u"Liste des cotisations"),
                      "infobulle": _(u"Liste des cotisations"),
                      "image": "Images/16x16/Cotisation.png",
                      "action": self.On_cotisations_recherche},
                     {"code": "liste_cotisations_manquantes",
                      "label": _(u"Liste des cotisations manquantes"),
                      "infobulle": _(u"Liste des cotisations manquantes"),
                      "image": "Images/16x16/Cotisation.png",
                      "action": self.On_cotisations_manquantes},
                     "-",
                     {"code": "saisir_lot_cotisations",
                      "label": _(u"Saisir un lot de cotisations"),
                      "infobulle": _(u"Saisir un lot de cotisations"),
                      "image": "Images/16x16/Cotisation.png",
                      "action": self.On_cotisations_saisir_lot_cotisations},
                     "-",
                     {"code": "cotisations_email",
                      "label": _(u"Transmettre des cotisations par Email"),
                      "infobulle": _(u"Transmettre des cotisations par Email"),
                      "image": "Images/16x16/Emails_exp.png",
                      "action": self.On_cotisations_email},
                     {"code": "cotisations_imprimer",
                      "label": _(u"Imprimer des cotisations"),
                      "infobulle": _(u"Imprimer une ou plusieurs cotisations"),
                      "image": "Images/16x16/Imprimante.png",
                      "action": self.On_cotisations_imprimer},
                     "-",
                     {"code": "cotisations_depots",
                      "label": _(u"Gestion des dépôts de cotisations"),
                      "infobulle": _(u"Gestion des dépôts de cotisations"),
                      "image": "Images/16x16/Depot_cotisations.png",
                      "action": self.On_cotisations_depots},
                 ],
                 },

                # Locations
                {"code": "menu_locations", "label": _(u"Locations"), "items": [
                    {"code": "locations_produits",
                     "label": _(u"Liste des produits"),
                     "infobulle": _(u"Liste des produits"),
                     "image": "Images/16x16/Produit.png",
                     "action": self.On_locations_produits},
                    "-",
                    {"code": "locations_locations",
                     "label": _(u"Liste des locations"),
                     "infobulle": _(u"Liste des locations"),
                     "image": "Images/16x16/Location.png",
                     "action": self.On_locations_locations},
                    {"code": "locations_email",
                     "label": _(u"Transmettre des locations par Email"),
                     "infobulle": _(u"Transmettre des locations par Email"),
                     "image": "Images/16x16/Emails_exp.png",
                     "action": self.On_locations_email},
                    {"code": "locations_imprimer",
                     "label": _(u"Imprimer des locations"),
                     "infobulle": _(u"Imprimer une ou plusieurs locations"),
                     "image": "Images/16x16/Imprimante.png",
                     "action": self.On_locations_imprimer},
                    "-",
                    {"code": "locations_demandes",
                     "label": _(u"Liste des demandes"),
                     "infobulle": _(u"Liste des demandes de locations"),
                     "image": "Images/16x16/Location_demande.png",
                     "action": self.On_locations_demandes},
                    {"code": "locations_demandes_email",
                     "label": _(u"Transmettre des demandes par Email"),
                     "infobulle": _(u"Transmettre des demandes par Email"),
                     "image": "Images/16x16/Emails_exp.png",
                     "action": self.On_locations_demandes_email},
                    {"code": "locations_demandes_imprimer",
                     "label": _(u"Imprimer des demandes"),
                     "infobulle": _(u"Imprimer une ou plusieurs demandes"),
                     "image": "Images/16x16/Imprimante.png",
                     "action": self.On_locations_demandes_imprimer},
                    "-",
                    {"code": "locations_planning",
                     "label": _(u"Planning des locations"),
                     "infobulle": _(u"Consultation du planning des locations"),
                     "image": "Images/16x16/Calendrier.png",
                     "action": self.On_locations_planning},
                    {"code": "locations_chronologie",
                     "label": _(u"Chronologie des locations"), "infobulle": _(
                        u"Consultation de la chronologie des locations"),
                     "image": "Images/16x16/Timeline.png",
                     "action": self.On_locations_chronologie},
                    {"code": "locations_tableau",
                     "label": _(u"Tableau des locations"),
                     "infobulle": _(u"Consultation du tableau des locations"),
                     "image": "Images/16x16/Tableau_ligne.png",
                     "action": self.On_locations_tableau},
                    "-",
                    {"code": "synthese_locations",
                     "label": _(u"Synthèse des locations"),
                     "infobulle": _(u"Synthèse des locations"),
                     "image": "Images/16x16/Diagramme.png",
                     "action": self.On_locations_synthese},
                    "-",
                    {"code": "locations_images",
                     "label": _(u"Images interactives"),
                     "infobulle": _(u"Consultation des images interactives"),
                     "image": "Images/16x16/Image_interactive.png",
                     "action": self.On_locations_images},
                ],
                 },

                # Consommations
                {"code": "menu_consommations", "label": _(u"Consommations"),
                 "items": [
                     {"code": "liste_consommations",
                      "label": _(u"Liste des consommations"),
                      "infobulle": _(u"Editer une liste des consommations"),
                      "image": "Images/16x16/Imprimante.png",
                      "action": self.On_imprim_conso_journ},
                     {"code": "gestionnaire_conso",
                      "label": _(u"Gestionnaire des consommations"),
                      "infobulle": _(u"Gestionnaire des consommations"),
                      "image": "Images/16x16/Calendrier.png",
                      "action": self.On_conso_gestionnaire},
                     "-",
                     {"code": "traitement_lot_conso",
                      "label": _(u"Traitement par lot"),
                      "infobulle": _(u"Traitement par lot"),
                      "image": "Images/16x16/Calendrier_modification.png",
                      "action": self.On_conso_traitement_lot},
                     "-",
                     {"code": "liste_detail_consommations",
                      "label": _(u"Liste détaillée des consommations"),
                      "infobulle": _(u"Liste détaillée des consommations"),
                      "image": "Images/16x16/Calendrier.png",
                      "action": self.On_conso_liste_detail_conso},
                     {"code": "liste_attente", "label": _(u"Liste d'attente"),
                      "infobulle": _(u"Liste d'attente"),
                      "image": "Images/16x16/Liste_attente.png",
                      "action": self.On_conso_attente},
                     {"code": "liste_refus",
                      "label": _(u"Liste des places refusées"),
                      "infobulle": _(u"Liste des places refusées"),
                      "image": "Images/16x16/Places_refus.png",
                      "action": self.On_conso_refus},
                     {"code": "liste_absences",
                      "label": _(u"Liste des absences"),
                      "infobulle": _(u"Liste des absences"),
                      "image": "Images/16x16/absenti.png",
                      "action": self.On_conso_absences},
                     "-",
                     {"code": "synthese_conso",
                      "label": _(u"Synthèse des consommations"),
                      "infobulle": _(u"Synthèse des consommations"),
                      "image": "Images/16x16/Diagramme.png",
                      "action": self.On_conso_synthese_conso},
                     {"code": "etat_global", "label": _(u"Etat global"),
                      "infobulle": _(u"Etat global"),
                      "image": "Images/16x16/Tableaux.png",
                      "action": self.On_conso_etat_global},
                     {"code": "etat_nominatif", "label": _(u"Etat nominatif"),
                      "infobulle": _(u"Etat nominatif"),
                      "image": "Images/16x16/Tableaux.png",
                      "action": self.On_conso_etat_nominatif},
                     "-",
                     {"code": "badgeage", "label": _(u"Badgeage"),
                      "infobulle": _(u"Badgeage"),
                      "image": "Images/16x16/Badgeage.png",
                      "action": self.On_conso_badgeage},
                 ],
                 },

                # Facturation
                {"code": "menu_facturation", "label": _(u"Facturation"),
                 "items": [
                     {"code": "facturation_verification_ventilation",
                      "label": _(u"Vérifier la ventilation"), "infobulle": _(
                         u"Vérifier la ventilation des règlements"),
                      "image": "Images/16x16/Repartition.png",
                      "action": self.On_reglements_ventilation},
                     "-",
                     {"code": "menu_facturation_factures",
                      "label": _(u"Factures"), "items": [
                         {"code": "factures_generation",
                          "label": _(u"Génération"),
                          "infobulle": _(u"Génération des factures"),
                          "image": "Images/16x16/Generation.png",
                          "action": self.On_facturation_factures_generation},
                         "-",
                         {"code": "factures_helios",
                          "label": _(u"Export vers le Trésor Public"),
                          "infobulle": _(
                              u"Exporter les factures vers le Trésor Public"),
                          "image": "Images/16x16/Helios.png",
                          "action": self.On_facturation_factures_helios},
                         {"code": "factures_prelevement",
                          "label": _(u"Prélèvement automatique"),
                          "infobulle": _(
                              u"Gestion du prélèvement automatique"),
                          "image": "Images/16x16/Prelevement.png",
                          "action": self.On_facturation_factures_prelevement},
                         {"code": "factures_email",
                          "label": _(u"Transmettre par Email"), "infobulle": _(
                             u"Transmettre les factures par Email"),
                          "image": "Images/16x16/Emails_exp.png",
                          "action": self.On_facturation_factures_email},
                         {"code": "factures_imprimer", "label": _(u"Imprimer"),
                          "infobulle": _(u"Imprimer des factures"),
                          "image": "Images/16x16/Imprimante.png",
                          "action": self.On_facturation_factures_imprimer},
                         "-",
                         {"code": "factures_liste",
                          "label": _(u"Liste des factures"),
                          "infobulle": _(u"Liste des factures générées"),
                          "image": "Images/16x16/Facture.png",
                          "action": self.On_facturation_factures_liste},
                     ],
                      },
                     {"code": "menu_facturation_rappels",
                      "label": _(u"Lettres de rappel"), "items": [
                         {"code": "rappels_generation",
                          "label": _(u"Génération"),
                          "infobulle": _(u"Génération des lettres de rappel"),
                          "image": "Images/16x16/Generation.png",
                          "action": self.On_facturation_rappels_generation},
                         "-",
                         {"code": "rappels_email",
                          "label": _(u"Transmettre par Email"), "infobulle": _(
                             u"Transmettre les lettres de rappel par Email"),
                          "image": "Images/16x16/Emails_exp.png",
                          "action": self.On_facturation_rappels_email},
                         {"code": "rappels_imprimer", "label": _(u"Imprimer"),
                          "infobulle": _(u"Imprimer des lettres de rappel"),
                          "image": "Images/16x16/Imprimante.png",
                          "action": self.On_facturation_rappels_imprimer},
                         "-",
                         {"code": "rappels_liste",
                          "label": _(u"Liste des lettres de rappel"),
                          "infobulle": _(u"Liste des lettres de rappel"),
                          "image": "Images/16x16/Facture.png",
                          "action": self.On_facturation_rappels_liste},
                     ],
                      },
                     {"code": "menu_facturation_attestations",
                      "label": _(u"Attestations de présence"), "items": [
                         {"code": "attestations_generation",
                          "label": _(u"Génération"), "infobulle": _(
                             u"Génération des attestations de présence"),
                          "image": "Images/16x16/Generation.png",
                          "action": self.On_facturation_attestations_generation},
                         {"code": "attestations_liste",
                          "label": _(u"Liste des attestations de présence"),
                          "infobulle": _(
                              u"Liste des attestations de présence générées"),
                          "image": "Images/16x16/Facture.png",
                          "action": self.On_facturation_attestations_liste},
                     ],
                      },
                     {"code": "menu_facturation_attestations_fiscales",
                      "label": _(u"Attestations fiscales"), "items": [
                         {"code": "attestations_fiscales_generation",
                          "label": _(u"Génération"), "infobulle": _(
                             u"Génération des attestations fiscales"),
                          "image": "Images/16x16/Generation.png",
                          "action": self.On_facturation_attestations_fiscales_generation},
                     ],
                      },
                     "-",
                     {"code": "liste_tarifs", "label": _(u"Liste des tarifs"),
                      "infobulle": _(u"Liste des tarifs des activités"),
                      "image": "Images/16x16/Euro.png",
                      "action": self.On_facturation_liste_tarifs},
                     "-",
                     {"code": "validation_contratspsu",
                      "label": _(u"Validation des contrats P.S.U."),
                      "infobulle": _(u"Validation des contrats P.S.U."),
                      "image": "Images/16x16/Contrat.png",
                      "action": self.On_facturation_validation_contratspsu},
                     "-",
                     {"code": "liste_prestations",
                      "label": _(u"Liste des prestations"),
                      "infobulle": _(u"Liste des prestations"),
                      "image": "Images/16x16/Euro.png",
                      "action": self.On_facturation_liste_prestations},
                     {"code": "recalcul_prestations",
                      "label": _(u"Recalculer des prestations"),
                      "infobulle": _(u"Recalculer des prestations"),
                      "image": "Images/16x16/Euro.png",
                      "action": self.On_facturation_recalculer_prestations},
                     {"code": "verrou_prestations",
                      "label": _(u"Verrouiller les prestations"),
                      "infobulle": _(
                          u"Verrouillage des prestations grâce aux périodes de gestion"),
                      "image": "Images/16x16/Cadenas.png",
                      "action": self.On_param_periodes_gestion},
                     "-",
                     {"code": "synthese_deductions",
                      "label": _(u"Synthèse des déductions"),
                      "infobulle": _(u"Synthèse des déductions"),
                      "image": "Images/16x16/Diagramme.png",
                      "action": self.On_facturation_synthese_deductions},
                     {"code": "liste_deductions",
                      "label": _(u"Liste des déductions"),
                      "infobulle": _(u"Liste des déductions"),
                      "image": "Images/16x16/Euro.png",
                      "action": self.On_facturation_liste_deductions},
                     {"code": "saisir_lot_deductions",
                      "label": _(u"Saisir un lot de déductions"),
                      "infobulle": _(u"Saisir un lot de déductions"),
                      "image": "Images/16x16/Impayes.png",
                      "action": self.On_facturation_saisir_deductions},
                     "-",
                     {"code": "saisir_lot_forfaits_credits",
                      "label": _(u"Saisir un lot de forfaits-crédits"),
                      "infobulle": _(u"Saisir un lot de forfaits-crédits"),
                      "image": "Images/16x16/Euro.png",
                      "action": self.On_facturation_saisir_lot_forfaits_credits},
                     "-",
                     {"code": "liste_soldes_familles",
                      "label": _(u"Liste des soldes"),
                      "infobulle": _(u"Liste des soldes des comptes familles"),
                      "image": "Images/16x16/Euro.png",
                      "action": self.On_facturation_soldes},
                     {"code": "liste_soldes_individus",
                      "label": _(u"Liste des soldes individuels"),
                      "infobulle": _(u"Liste des soldes individuels"),
                      "image": "Images/16x16/Euro.png",
                      "action": self.On_facturation_soldes_individuels},
                     "-",
                     {"code": "synthese_impayes",
                      "label": _(u"Synthèse des impayés"),
                      "infobulle": _(u"Synthèse des impayés"),
                      "image": "Images/16x16/Diagramme.png",
                      "action": self.On_facturation_synthese_impayes},
                     {"code": "solder_impayes",
                      "label": _(u"Solder les impayés"),
                      "infobulle": _(u"Solder les impayés"),
                      "image": "Images/16x16/Impayes.png",
                      "action": self.On_facturation_solder_impayes},
                     "-",
                     {"code": "synthese_prestations",
                      "label": _(u"Synthèse des prestations"),
                      "infobulle": _(u"Synthèse des prestations"),
                      "image": "Images/16x16/Diagramme.png",
                      "action": self.On_facturation_synthese_prestations},
                     {"code": "prestations_villes",
                      "label": _(u"Liste des prestations par famille"),
                      "infobulle": _(u"Liste des prestations par famille"),
                      "image": "Images/16x16/Euro.png",
                      "action": self.On_facturation_prestations_villes},
                     "-",
                     {"code": "export_compta",
                      "label": _(u"Export des écritures comptables"),
                      "infobulle": _(u"Exporter les écritures comptables"),
                      "image": "Images/16x16/Export_comptable.png",
                      "action": self.On_facturation_export_compta},
                 ],
                 },

                # Règlements
                {"code": "menu_reglements", "label": _(u"Règlements"),
                 "items": [
                     {"code": "regler_facture",
                      "label": _(u"Régler une facture\tF4"), "infobulle": _(
                         u"Régler une facture à partir de son numéro"),
                      "image": "Images/16x16/Codebarre.png",
                      "action": self.On_reglements_regler_facture},
                     "-",
                     {"code": "liste_recus_reglements",
                      "label": _(u"Liste des reçus de règlements"),
                      "infobulle": _(
                          u"Consulter la liste des reçus de règlements"),
                      "image": "Images/16x16/Note.png",
                      "action": self.On_reglements_recus},
                     {"code": "liste_reglements",
                      "label": _(u"Liste des règlements"),
                      "infobulle": _(u"Consulter la liste des règlements"),
                      "image": "Images/16x16/Reglement.png",
                      "action": self.On_reglements_recherche},
                     {"code": "liste_reglements_detail",
                      "label": _(u"Liste détaillée des règlements"),
                      "infobulle": _(
                          u"Consulter la liste détaillée des règlements"),
                      "image": "Images/16x16/Reglement.png",
                      "action": self.On_reglements_detail},
                     "-",
                     {"code": "reglements_verification_ventilation",
                      "label": _(u"Vérifier la ventilation"), "infobulle": _(
                         u"Vérifier la ventilation des règlements"),
                      "image": "Images/16x16/Repartition.png",
                      "action": self.On_reglements_ventilation},
                     {"code": "depot_prestations",
                      "label": _(u"Détail des prestations d'un dépôt"),
                      "infobulle": _(u"Détail des prestations d'un dépôt"),
                      "image": "Images/16x16/Diagramme.png",
                      "action": self.On_reglements_depot_prestations},
                     {"code": "analyse_ventilation", "label": _(
                         u"Tableau d'analyse croisée ventilation/dépôts"),
                      "infobulle": _(
                          u"Tableau d'analyse croisée ventilation/dépôts"),
                      "image": "Images/16x16/Diagramme.png",
                      "action": self.On_reglements_analyse_ventilation},
                     {"code": "syntheses_modes_reglements",
                      "label": _(u"Synthèse des modes de règlements"),
                      "infobulle": _(u"Synthèse des modes de règlements"),
                      "image": "Images/16x16/Diagramme.png",
                      "action": self.On_reglements_synthese_modes},
                     "-",
                     {"code": "reglements_prelevement",
                      "label": _(u"Prélèvement automatique"),
                      "infobulle": _(u"Gestion du prélèvement automatique"),
                      "image": "Images/16x16/Prelevement.png",
                      "action": self.On_facturation_factures_prelevement},
                     {"code": "reglements_depots",
                      "label": _(u"Gestion des dépôts"),
                      "infobulle": _(u"Gestion des dépôts de règlements"),
                      "image": "Images/16x16/Banque.png",
                      "action": self.On_reglements_depots},
                 ],
                 },

                # Comptabilité
                {"code": "menu_comptabilite", "label": _(u"Comptabilité"),
                 "items": [
                     {"code": "liste_comptes",
                      "label": _(u"Liste des comptes"), "infobulle": _(
                         u"Consulter ou modifier la liste des comptes"),
                      "image": "Images/16x16/Operations.png",
                      "action": self.On_Comptabilite_comptes},
                     {"code": "liste_operations_tresorerie",
                      "label": _(u"Liste des opérations de trésorerie"),
                      "infobulle": _(
                          u"Consulter ou modifier la liste des opérations de trésorerie"),
                      "image": "Images/16x16/Operations.png",
                      "action": self.On_Comptabilite_operations_tresorerie},
                     {"code": "liste_operations_budgetaires",
                      "label": _(u"Liste des opérations budgétaires"),
                      "infobulle": _(
                          u"Consulter ou modifier la liste des opérations budgétaires"),
                      "image": "Images/16x16/Operations.png",
                      "action": self.On_Comptabilite_operations_budgetaires},
                     {"code": "liste_virements",
                      "label": _(u"Liste des virements"), "infobulle": _(
                         u"Consulter ou modifier la liste des virements"),
                      "image": "Images/16x16/Operations.png",
                      "action": self.On_Comptabilite_virements},
                     "-",
                     {"code": "rapprochement_bancaire",
                      "label": _(u"Rapprochement bancaire"),
                      "infobulle": _(u"Rapprochement bancaire"),
                      "image": "Images/16x16/Document_coches.png",
                      "action": self.On_Comptabilite_rapprochement},
                     "-",
                     {"code": "suivi_tresorerie",
                      "label": _(u"Suivi de la trésorerie"),
                      "infobulle": _(u"Suivre la trésorerie"),
                      "image": "Images/16x16/Tresorerie.png",
                      "action": self.On_Comptabilite_tresorerie},
                     {"code": "suivi_budgets",
                      "label": _(u"Suivi des budgets"),
                      "infobulle": _(u"Suivre les budgets"),
                      "image": "Images/16x16/Tresorerie.png",
                      "action": self.On_Comptabilite_budgets},
                     "-",
                     {"code": "compta_graphiques", "label": _(u"Graphiques"),
                      "infobulle": _(u"Graphiques"),
                      "image": "Images/16x16/Diagramme.png",
                      "action": self.On_Comptabilite_graphiques},
                 ],
                 },
            ],
             },
        ],
         },

        # Règlements
        {"code": "menu_reglements", "label": _("Règlements"), "items": [
            {"code": "regler_facture",
             "label": _("Régler une facture\tF4"),
             "infobulle": _("Régler une facture à partir de son numéro"),
             "image": "Images/16x16/Codebarre.png",
             "action": self.On_reglements_regler_facture},
            "-",
            {"code": "liste_recus_reglements",
             "label": _("Liste des reçus de règlements"),
             "infobulle": _("Consulter la liste des reçus de règlements"),
             "image": "Images/16x16/Note.png",
             "action": self.On_reglements_recus},
            {"code": "liste_reglements",
             "label": _("Liste des règlements"),
             "infobulle": _("Consulter la liste des règlements"),
             "image": "Images/16x16/Reglement.png",
             "action": self.On_reglements_recherche},
            "-",
            {"code": "reglements_verification_ventilation",
             "label": _("Vérifier la ventilation"),
             "infobulle": _("Vérifier la ventilation des règlements"),
             "image": "Images/16x16/Repartition.png",
             "action": self.On_reglements_ventilation},
            {"code": "analyse_ventilation",
             "label": _("Tableau d'analyse croisée ventilation/dépôts"),
             "infobulle": _(
                 "Tableau d'analyse croisée ventilation/dépôts"),
             "image": "Images/16x16/Diagramme.png",
             "action": self.On_reglements_analyse_ventilation},
            {"code": "syntheses_modes_reglements",
             "label": _("Synthèse des modes de règlements"),
             "infobulle": _("Synthèse des modes de règlements"),
             "image": "Images/16x16/Diagramme.png",
             "action": self.On_reglements_synthese_modes},
            "-",
            {"code": "reglements_prelevement",
             "label": _("Prélèvement automatique"),
             "infobulle": _("Gestion du prélèvement automatique"),
             "image": "Images/16x16/Prelevement.png",
             "action": self.On_facturation_factures_prelevement},
            {"code": "reglements_depots", "label": _("Gestion des dépôts"),
             "infobulle": _("Gestion des dépôts de règlements"),
             "image": "Images/16x16/Banque.png",
             "action": self.On_reglements_depots},
        ],
         },

        # A propos
        {"code": "menu_a_propos", "label": _("A propos"), "items": [
            {"code": "notes_versions", "label": _("Notes de versions"),
             "infobulle": _("Notes de versions"),
             "image": "Images/16x16/Versions.png",
             "action": self.On_propos_versions},
            {"code": "licence_logiciel", "label": _("Licence"),
             "infobulle": _("Licence du logiciel"),
             "image": "Images/16x16/Licence.png",
             "action": self.On_propos_licence},
            "-",
            {"code": "soutenir_noethys", "label": _("Soutenir Noethys"),
             "infobulle": _("Soutenir Noethys"),
             "image": "Images/16x16/Soutenir_noethys.png",
             "action": self.On_propos_soutenir},
            "-",
            {"code": "a_propos", "label": _("A propos"),
             "infobulle": _("A propos"),
             "image": "Images/16x16/Information.png",
             "action": self.On_propos_propos},
        ],
         },

    ]

class Menu(object):
    def __init__(self, parent):
        self.parent = parent

    def GetItemsMenu(self):
        mnt = CTRL_Saisie_transport.MenuTransports(self)
        menuTransports = mnt.GetMenuTransports()
        return GetListItemsMenu(self,menuTransports)

    def On_fichier_Ouvrir(self, event):
        self.parent.On_fichier_Ouvrir(event)

    def On_fichier_Fermer(self, event):
        """ Fermer le fichier ouvert """
        self.parent.Fermer(event)

    def On_fichier_Informations(self, event):
        """ Fichier : Informations sur le fichier """
        from Dlg import DLG_Infos_fichier
        dlg = DLG_Infos_fichier.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_fichier_Sauvegarder(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "fichier_sauvegarde_manuelle", "creer") == False: return
        from Dlg import DLG_Sauvegarde
        dlg = DLG_Sauvegarde.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_fichier_Restaurer(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "fichier_restauration", "creer") == False: return
        from Dlg import DLG_Restauration
        fichier = DLG_Restauration.SelectionFichier()
        if fichier != None:
            listeFichiersRestaures = []
            dlg = DLG_Restauration.Dialog(self.parent, fichier=fichier)
            if dlg.ShowModal() == wx.ID_OK:
                listeFichiersRestaures = dlg.GetFichiersRestaures()
            dlg.Destroy()
            # Ferme le fichier ouvert si c'est celui-ci qui est restauré
            nomFichier = self.parent.userConfig["nomFichier"]
            if "[RESEAU]" in nomFichier:
                nomFichier = nomFichier[nomFichier.index("[RESEAU]") + 8:]
            if nomFichier in listeFichiersRestaures:
                dlg = wx.MessageDialog(self.parent,
                                       _("Redémarrage du fichier restauré.\n\nAfin de finaliser la restauration, le fichier de données ouvert va être fermé puis ré-ouvert."),
                                       _("Redémarrage du fichier restauré"),
                                       wx.OK | wx.ICON_INFORMATION)
                dlg.ShowModal()
                dlg.Destroy()
                self.parent.Fermer(sauvegarde_auto=False)
                self.parent.OuvrirDernierFichier()

    def On_fichier_Sauvegardes_auto(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "fichier_sauvegardes_auto", "consulter") == False: return
        from Dlg import DLG_Sauvegardes_auto
        dlg = DLG_Sauvegardes_auto.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_fichier_Convertir_reseau(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "fichier_conversions", "creer") == False: return
        nomFichier = self.parent.userConfig["nomFichier"]
        from Utils import UTILS_Conversion_fichier
        resultat = UTILS_Conversion_fichier.ConversionLocalReseau(self,
                                                                  nomFichier)
        print("Succes de la procedure : ", resultat)

    def On_fichier_Convertir_local(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "fichier_conversions", "creer") == False: return
        nomFichier = self.parent.userConfig["nomFichier"]
        from Utils import UTILS_Conversion_fichier
        resultat = UTILS_Conversion_fichier.ConversionReseauLocal(self.parent,
                                                                  nomFichier)
        print("Succes de la procedure : ", resultat)

    def On_upgrade_base(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "fichier_restauration", "creer") == False: return
        import UpgradeDB
        UpgradeDB.MAJ_TablesEtChamps(self.parent,mode='ctrl')

    def On_upgrade_modules(self, event):
        from Dlg import DLG_Release
        dlg = DLG_Release.Dialog(self.parent)
        ret = dlg.ShowModal()
        dlg.Destroy()
        if ret == wx.ID_OK:
            self.parent.Quitter()

    def On_fichier_Quitter(self,event):
        self.parent.Quitter()

    def On_param_preferences(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "parametrage_preferences", "consulter") == False: return
        from Dlg import DLG_Preferences
        dlg = DLG_Preferences.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_param_enregistrement(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "parametrage_enregistrement", "consulter") == False: return
        from Dlg import DLG_Enregistrement
        dlg = DLG_Enregistrement.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_param_utilisateurs(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "parametrage_utilisateurs", "consulter") == False: return
        from Dlg import DLG_Utilisateurs
        dlg = DLG_Utilisateurs.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()
        self.parent.listeUtilisateurs = self.parent.GetListeUtilisateurs()
        self.parent.RechargeUtilisateur()

    def On_param_modeles_droits(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "parametrage_modeles_droits", "consulter") == False: return
        from Dlg import DLG_Droits
        dlg = DLG_Droits.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()
        self.parent.listeUtilisateurs = self.parent.GetListeUtilisateurs()
        self.parent.RechargeUtilisateur()

    def On_param_utilisateurs_reseau(self, event):
        if "[RESEAU]" not in self.parent.userConfig["nomFichier"]:
            dlg = wx.MessageDialog(self.parent,
                                   _("Cette fonction n'est accessible que si vous utilisez un fichier réseau !"),
                                   _("Accès non autorisé"),
                                   wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            return
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "parametrage_utilisateurs_reseau", "consulter") == False: return
        from Dlg import DLG_Utilisateurs_reseau
        dlg = DLG_Utilisateurs_reseau.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_param_organisateur(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "parametrage_organisateur", "consulter") == False: return
        from Dlg import DLG_Organisateur
        dlg = DLG_Organisateur.Dialog(self.parent)
        dlg.ShowModal()
        try:
            dlg.Destroy()
        except:
            pass
        customize = self.parent.GetCustomize()
        if customize.GetValeur("ephemeride", "actif", "1") == "1":
            self.parent.ctrl_ephemeride.Initialisation()

    def On_param_groupes_activites(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "parametrage_groupes_activites", "consulter") == False: return
        from Dlg import DLG_Groupes_activites
        dlg = DLG_Groupes_activites.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()
        self.parent.ctrl_remplissage.MAJ()

    def On_param_activites(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "parametrage_activites", "consulter") == False: return
        from Dlg import DLG_Activites
        dlg = DLG_Activites.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()
        self.parent.ctrl_remplissage.MAJ()

    def On_param_documents(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "parametrage_modeles_docs", "consulter") == False: return
        from Dlg import DLG_Modeles_docs
        dlg = DLG_Modeles_docs.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_param_modeles_emails(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "parametrage_modeles_emails", "consulter") == False: return
        from Dlg import DLG_Modeles_emails
        dlg = DLG_Modeles_emails.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_param_modeles_tickets(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "parametrage_modeles_tickets", "consulter") == False: return
        from Dlg import DLG_Modeles_tickets
        dlg = DLG_Modeles_tickets.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_param_modeles_contrats(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "parametrage_modeles_contrats", "consulter") == False: return
        from Dlg import DLG_Modeles_contrats
        dlg = DLG_Modeles_contrats.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_param_modeles_plannings(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "parametrage_modeles_plannings", "consulter") == False: return
        from Dlg import DLG_Modeles_plannings
        dlg = DLG_Modeles_plannings.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_param_badgeage(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "parametrage_procedures_badgeage", "consulter") == False: return
        from Dlg import DLG_Badgeage_procedures
        dlg = DLG_Badgeage_procedures.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_param_periodes_gestion(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "parametrage_periodes_gestion", "consulter") == False: return
        from Dlg import DLG_Periodes_gestion
        dlg = DLG_Periodes_gestion.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_param_categories_messages(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "parametrage_categories_messages", "consulter") == False: return
        from Dlg import DLG_Categories_messages
        dlg = DLG_Categories_messages.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()
        self.parent.ctrl_messages.MAJ()

    def On_param_pieces(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "parametrage_types_pieces", "consulter") == False: return
        from Dlg import DLG_Types_pieces
        dlg = DLG_Types_pieces.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_param_categories_travail(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "parametrage_categories_travail", "consulter") == False: return
        from Dlg import DLG_Categories_travail
        dlg = DLG_Categories_travail.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_param_villes(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "parametrage_villes", "consulter") == False: return
        from Dlg import DLG_Villes
        dlg = DLG_Villes.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_param_secteurs(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "parametrage_secteurs", "consulter") == False: return
        from Dlg import DLG_Secteurs
        dlg = DLG_Secteurs.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_param_types_sieste(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "parametrage_types_siestes", "consulter") == False: return
        from Dlg import DLG_Types_sieste
        dlg = DLG_Types_sieste.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_param_categories_medicales(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "parametrage_categories_medicales", "consulter") == False: return
        from Dlg import DLG_Categories_medicales
        dlg = DLG_Categories_medicales.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_param_vacances(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "parametrage_vacances", "consulter") == False: return
        from Dlg import DLG_Vacances
        dlg = DLG_Vacances.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()
        self.parent.ctrl_remplissage.MAJ()

    def On_param_feries(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "parametrage_feries", "consulter") == False: return
        from Dlg import DLG_Feries
        dlg = DLG_Feries.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()
        self.parent.ctrl_remplissage.MAJ()

    def On_param_maladies(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "parametrage_maladies", "consulter") == False: return
        from Dlg import DLG_Types_maladies
        dlg = DLG_Types_maladies.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_param_vaccins(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "parametrage_vaccins", "consulter") == False: return
        from Dlg import DLG_Types_vaccins
        dlg = DLG_Types_vaccins.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_param_medecins(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "parametrage_medecins", "consulter") == False: return
        from Dlg import DLG_Medecins
        dlg = DLG_Medecins.Dialog(self.parent, mode="gestion")
        dlg.ShowModal()
        dlg.Destroy()

    def On_param_restaurateurs(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "parametrage_restaurateurs", "consulter") == False: return
        from Dlg import DLG_Restaurateurs
        dlg = DLG_Restaurateurs.Dialog(self.parent, mode="gestion")
        dlg.ShowModal()
        dlg.Destroy()

    def On_param_menus_categories(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "parametrage_menus_categories", "consulter") == False: return
        from Dlg import DLG_Menus_categories
        dlg = DLG_Menus_categories.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_param_menus_legendes(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "parametrage_menus_legendes", "consulter") == False: return
        from Dlg import DLG_Menus_legendes
        dlg = DLG_Menus_legendes.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_param_comptes(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "parametrage_comptes_bancaires", "consulter") == False: return
        from Dlg import DLG_Comptes_bancaires
        dlg = DLG_Comptes_bancaires.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_param_modes_reglements(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "parametrage_modes_reglements", "consulter") == False: return
        from Dlg import DLG_Modes_reglements
        dlg = DLG_Modes_reglements.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_param_emetteurs(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "parametrage_emetteurs", "consulter") == False: return
        from Dlg import DLG_Emetteurs
        dlg = DLG_Emetteurs.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_param_exercices(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "parametrage_exercices", "consulter") == False: return
        from Dlg import DLG_Exercices
        dlg = DLG_Exercices.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_param_gestion_tarifs(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "parametrage_exercices", "consulter") == False: return
        from Dlg import DLG_TarifsListe
        dlg = DLG_TarifsListe.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_param_gestion_articles(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "parametrage_exercices", "consulter") == False: return
        from Dlg import DLG_Articles
        dlg = DLG_Articles.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_param_analytiques(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "parametrage_analytiques", "consulter") == False: return
        from Dlg import DLG_Analytiques
        dlg = DLG_Analytiques.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_param_categories_comptables(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "parametrage_categories_comptables", "consulter") == False: return
        from Dlg import DLG_Categories_operations
        dlg = DLG_Categories_operations.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_param_comptes_comptables(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "parametrage_comptes_comptables", "consulter") == False: return
        from Dlg import DLG_PlanComptable
        dlg = DLG_PlanComptable.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_param_tiers(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "parametrage_tiers", "consulter") == False: return
        from Dlg import DLG_Tiers
        dlg = DLG_Tiers.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_param_budgets(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "parametrage_budgets", "consulter") == False: return
        from Dlg import DLG_Budgets
        dlg = DLG_Budgets.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_param_releves_bancaires(self, event):
        from Dlg import DLG_Releves_compta
        dlg = DLG_Releves_compta.Dialog(self.parent, titre=_(
            "Gestion des relevés bancaires"))
        dlg.ShowModal()
        dlg.Destroy()

    def On_param_banques(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "parametrage_banques", "consulter") == False: return
        from Dlg import DLG_Banques
        dlg = DLG_Banques.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_param_perceptions(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "parametrage_perceptions", "consulter") == False: return
        from Dlg import DLG_Perceptions
        dlg = DLG_Perceptions.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_param_categories_produits(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "parametrage_categories_produits", "consulter") == False: return
        from Dlg import DLG_Categories_produits
        dlg = DLG_Categories_produits.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()
        self.parent.ctrl_remplissage.MAJ()

    def On_param_produits(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "parametrage_produits", "consulter") == False: return
        from Dlg import DLG_Produits
        dlg = DLG_Produits.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()
        self.parent.ctrl_remplissage.MAJ()

    def On_param_regies_factures(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "parametrage_regies_factures", "consulter") == False: return
        from Dlg import DLG_Regies_factures
        dlg = DLG_Regies_factures.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_param_prefixes_factures(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "parametrage_prefixes_factures", "consulter") == False: return
        from Dlg import DLG_Prefixes_factures
        dlg = DLG_Prefixes_factures.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_param_lots_factures(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "parametrage_lots_factures", "consulter") == False: return
        from Dlg import DLG_Lots_factures
        dlg = DLG_Lots_factures.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_param_lots_rappels(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "parametrage_lots_rappels", "consulter") == False: return
        from Dlg import DLG_Lots_rappels
        dlg = DLG_Lots_rappels.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_param_regimes(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "parametrage_regimes", "consulter") == False: return
        from Dlg import DLG_Regimes
        dlg = DLG_Regimes.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_param_caisses(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "parametrage_caisses", "consulter") == False: return
        from Dlg import DLG_Caisses
        dlg = DLG_Caisses.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_param_types_quotients(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "parametrage_types_quotients", "consulter") == False: return
        from Dlg import DLG_Types_quotients
        dlg = DLG_Types_quotients.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_param_modeles_aides(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "parametrage_modeles_aides", "consulter") == False: return
        from Dlg import DLG_Modeles_aides
        dlg = DLG_Modeles_aides.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_param_modeles_prestations(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "parametrage_modeles_prestations", "consulter") == False: return
        from Dlg import DLG_Modeles_prestations
        dlg = DLG_Modeles_prestations.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_param_modeles_commandes(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "parametrage_modeles_commandes", "consulter") == False: return
        from Dlg import DLG_Modeles_commandes
        dlg = DLG_Modeles_commandes.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_param_types_cotisations(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "parametrage_types_cotisations", "consulter") == False: return
        from Dlg import DLG_Types_cotisations
        dlg = DLG_Types_cotisations.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_param_emails_exp(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "parametrage_emails_exp", "consulter") == False: return
        from Dlg import DLG_Emails_exp
        dlg = DLG_Emails_exp.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_param_listes_diffusion(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "parametrage_listes_diffusion", "consulter") == False: return
        from Dlg import DLG_Listes_diffusion
        dlg = DLG_Listes_diffusion.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_param_questionnaires(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "parametrage_questionnaires", "consulter") == False: return
        from Dlg import DLG_Questionnaires
        dlg = DLG_Questionnaires.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_param_images_interactives(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "parametrage_images_interactives", "consulter") == False: return
        from Dlg import DLG_Images_interactives
        dlg = DLG_Images_interactives.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()
        self.parent.ctrl_remplissage.MAJ()

    def On_param_niveaux_scolaires(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "parametrage_niveaux_scolaires", "consulter") == False: return
        from Dlg import DLG_Niveaux_scolaires
        dlg = DLG_Niveaux_scolaires.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_param_ecoles(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "parametrage_ecoles", "consulter") == False: return
        from Dlg import DLG_Ecoles
        dlg = DLG_Ecoles.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_param_classes(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "parametrage_classes", "consulter") == False: return
        from Dlg import DLG_Classes
        dlg = DLG_Classes.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_param_compagnies_bus(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "parametrage_compagnies", "consulter") == False: return
        from Dlg import DLG_Compagnies
        dlg = DLG_Compagnies.Dialog(self.parent, categorie="bus", mode="gestion")
        dlg.ShowModal()
        dlg.Destroy()

    def On_param_compagnies_car(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "parametrage_compagnies", "consulter") == False: return
        from Dlg import DLG_Compagnies
        dlg = DLG_Compagnies.Dialog(self.parent, categorie="car", mode="gestion")
        dlg.ShowModal()
        dlg.Destroy()

    def On_param_compagnies_navette(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "parametrage_compagnies", "consulter") == False: return
        from Dlg import DLG_Compagnies
        dlg = DLG_Compagnies.Dialog(self.parent, categorie="navette", mode="gestion")
        dlg.ShowModal()
        dlg.Destroy()

    def On_param_compagnies_taxi(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "parametrage_compagnies", "consulter") == False: return
        from Dlg import DLG_Compagnies
        dlg = DLG_Compagnies.Dialog(self.parent, categorie="taxi", mode="gestion")
        dlg.ShowModal()
        dlg.Destroy()

    def On_param_compagnies_avion(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "parametrage_compagnies", "consulter") == False: return
        from Dlg import DLG_Compagnies
        dlg = DLG_Compagnies.Dialog(self.parent, categorie="avion", mode="gestion")
        dlg.ShowModal()
        dlg.Destroy()

    def On_param_compagnies_bateau(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "parametrage_compagnies", "consulter") == False: return
        from Dlg import DLG_Compagnies
        dlg = DLG_Compagnies.Dialog(self.parent, categorie="bateau", mode="gestion")
        dlg.ShowModal()
        dlg.Destroy()

    def On_param_compagnies_train(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "parametrage_compagnies", "consulter") == False: return
        from Dlg import DLG_Compagnies
        dlg = DLG_Compagnies.Dialog(self.parent, categorie="train", mode="gestion")
        dlg.ShowModal()
        dlg.Destroy()

    def On_param_compagnies_metro(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "parametrage_compagnies", "consulter") == False: return
        from Dlg import DLG_Compagnies
        dlg = DLG_Compagnies.Dialog(self.parent, categorie="metro", mode="gestion")
        dlg.ShowModal()
        dlg.Destroy()

    def On_param_lieux_gares(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "parametrage_lieux", "consulter") == False: return
        from Dlg import DLG_Lieux
        dlg = DLG_Lieux.Dialog(self.parent, categorie="gare", mode="gestion")
        dlg.ShowModal()
        dlg.Destroy()

    def On_param_lieux_aeroports(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "parametrage_lieux", "consulter") == False: return
        from Dlg import DLG_Lieux
        dlg = DLG_Lieux.Dialog(self.parent, categorie="aeroport", mode="gestion")
        dlg.ShowModal()
        dlg.Destroy()

    def On_param_lieux_ports(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "parametrage_lieux", "consulter") == False: return
        from Dlg import DLG_Lieux
        dlg = DLG_Lieux.Dialog(self.parent, categorie="port", mode="gestion")
        dlg.ShowModal()
        dlg.Destroy()

    def On_param_lieux_stations(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "parametrage_lieux", "consulter") == False: return
        from Dlg import DLG_Lieux
        dlg = DLG_Lieux.Dialog(self.parent, categorie="station", mode="gestion")
        dlg.ShowModal()
        dlg.Destroy()

    def On_param_lignes_bus(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "parametrage_lignes", "consulter") == False: return
        from Dlg import DLG_Lignes
        dlg = DLG_Lignes.Dialog(self.parent, categorie="bus", mode="gestion")
        dlg.ShowModal()
        dlg.Destroy()

    def On_param_lignes_car(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "parametrage_lignes", "consulter") == False: return
        from Dlg import DLG_Lignes
        dlg = DLG_Lignes.Dialog(self.parent, categorie="car", mode="gestion")
        dlg.ShowModal()
        dlg.Destroy()

    def On_param_lignes_navette(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "parametrage_lignes", "consulter") == False: return
        from Dlg import DLG_Lignes
        dlg = DLG_Lignes.Dialog(self.parent, categorie="navette", mode="gestion")
        dlg.ShowModal()
        dlg.Destroy()

    def On_param_lignes_bateau(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "parametrage_lignes", "consulter") == False: return
        from Dlg import DLG_Lignes
        dlg = DLG_Lignes.Dialog(self.parent, categorie="bateau", mode="gestion")
        dlg.ShowModal()
        dlg.Destroy()

    def On_param_lignes_metro(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "parametrage_lignes", "consulter") == False: return
        from Dlg import DLG_Lignes
        dlg = DLG_Lignes.Dialog(self.parent, categorie="metro", mode="gestion")
        dlg.ShowModal()
        dlg.Destroy()

    def On_param_lignes_pedibus(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "parametrage_lignes", "consulter") == False: return
        from Dlg import DLG_Lignes
        dlg = DLG_Lignes.Dialog(self.parent, categorie="pedibus", mode="gestion")
        dlg.ShowModal()
        dlg.Destroy()

    def On_param_arrets_bus(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "parametrage_arrets", "consulter") == False: return
        from Dlg import DLG_Arrets
        dlg = DLG_Arrets.Dialog(self.parent, categorie="bus")
        dlg.ShowModal()
        dlg.Destroy()

    def On_param_arrets_navette(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "parametrage_arrets", "consulter") == False: return
        from Dlg import DLG_Arrets
        dlg = DLG_Arrets.Dialog(self.parent, categorie="navette")
        dlg.ShowModal()
        dlg.Destroy()

    def On_param_arrets_car(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "parametrage_arrets", "consulter") == False: return
        from Dlg import DLG_Arrets
        dlg = DLG_Arrets.Dialog(self.parent, categorie="car")
        dlg.ShowModal()
        dlg.Destroy()

    def On_param_arrets_bateau(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "parametrage_arrets", "consulter") == False: return
        from Dlg import DLG_Arrets
        dlg = DLG_Arrets.Dialog(self.parent, categorie="bateau")
        dlg.ShowModal()
        dlg.Destroy()

    def On_param_arrets_metro(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "parametrage_arrets", "consulter") == False: return
        from Dlg import DLG_Arrets
        dlg = DLG_Arrets.Dialog(self.parent, categorie="metro")
        dlg.ShowModal()
        dlg.Destroy()

    def On_param_arrets_pedibus(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "parametrage_arrets", "consulter") == False: return
        from Dlg import DLG_Arrets
        dlg = DLG_Arrets.Dialog(self.parent, categorie="pedibus")
        dlg.ShowModal()
        dlg.Destroy()

    def MAJmenuAffichage(self, event):
        """ Met à jour la liste des panneaux ouverts du menu Affichage """
        menuOuvert = event.GetMenu()
        if menuOuvert == self.parent.dictInfosMenu["menu_affichage"]["ctrl"] :
            for dictPanneau in self.parent.listePanneaux :
                IDmenuItem = dictPanneau["IDmenu"]
                item = menuOuvert.FindItemById(IDmenuItem)
                panneau = self.parent._mgr.GetPane(dictPanneau["code"])
                if panneau.IsShown() == True :
                    item.Check(True)
                else:
                    item.Check(False)

    def On_affichage_perspective_defaut(self, event):
        self.parent.MAJ()
        self.parent._mgr.LoadPerspective(self.parent.perspective_defaut)
        self.parent.perspective_active = None
        self.parent.MAJmenuPerspectives()
        self.parent._mgr.Update()
        self.parent.Refresh()

    def On_affichage_perspective_perso(self, event):
        index = event.GetId() - ID_PREMIERE_PERSPECTIVE
        self.parent._mgr.LoadPerspective(self.parent.perspectives[index]["perspective"])
        self.parent.perspective_active = index
        self.parent.ForcerAffichagePanneau("ephemeride")
        self.parent.MAJmenuPerspectives()
        self.parent._mgr.Update()
        self.parent.Refresh()
        event.Skip()

    def On_affichage_perspective_save(self, event):
        newIDperspective = len(self.parent.perspectives)
        dlg = wx.TextEntryDialog(self.parent,
                                 _("Veuillez saisir un intitulé pour cette disposition :"),
                                 "Sauvegarde d'une disposition")
        dlg.SetValue(_("Disposition %d") % (newIDperspective + 1))
        reponse = dlg.ShowModal()
        if reponse != wx.ID_OK:
            dlg.Destroy()
            return
        label = dlg.GetValue()
        dlg.Destroy()

        # Vérifie que ce nom n'est pas déjà attribué
        for dictPerspective in self.parent.perspectives:
            if label == dictPerspective["label"]:
                dlg = wx.MessageDialog(self.parent,
                                       _("Ce nom est déjà attribué à une autre disposition !"),
                                       _("Erreur de saisie"),
                                       wx.OK | wx.ICON_EXCLAMATION)
                dlg.ShowModal()
                dlg.Destroy()
                return

        # Sauvegarde de la perspective
        self.parent.perspectives.append(
            {"label": label, "perspective": self.parent._mgr.SavePerspective()})
        self.parent.perspective_active = newIDperspective
        event.Skip()
        # MAJ Menu Affichage
        self.parent.MAJmenuPerspectives()

    def On_affichage_perspective_suppr(self, event):
        listeLabels = []
        for dictPerspective in self.parent.perspectives:
            listeLabels.append(dictPerspective["label"])
        dlg = wx.MultiChoiceDialog(self.parent,
                                   _("Cochez les dispositions que vous souhaitez supprimer :"),
                                   _("Supprimer des dispositions"),
                                   listeLabels)
        if dlg.ShowModal() == wx.ID_OK:
            selections = dlg.GetSelections()
            selections.sort(reverse=True)
            for index in selections:
                self.parent.perspectives.pop(index)
            if self.parent.perspective_active in selections:
                self.parent._mgr.LoadPerspective(self.parent.perspective_defaut)
            self.parent.perspective_active = None
            self.parent.MAJmenuPerspectives()
        dlg.Destroy()

    def On_affichage_panneau_afficher(self, event):
        index = event.GetId() - ID_AFFICHAGE_PANNEAUX
        panneau = self.parent._mgr.GetPane(self.parent.listePanneaux[index]["code"])
        if panneau.IsShown():
            panneau.Hide()
        else:
            panneau.Show()
        self.parent._mgr.Update()

    def On_affichage_barres_outils(self, event):
        # Récupère la liste des codes des barres actuelles
        texteBarres = self.parent.userConfig["barres_outils_perso"]
        if len(texteBarres) > 0:
            listeTextesBarresActuelles = texteBarres.split("@@@@")
        else:
            listeTextesBarresActuelles = []
        listeCodesBarresActuelles = []
        for texteBarre in listeTextesBarresActuelles:
            code, label, observations, style, contenu = texteBarre.split("###")
            listeCodesBarresActuelles.append(code)

        # Charge la DLG de gestion des barres d'outils
        from Dlg import DLG_Barres_outils
        texte = self.parent.userConfig["barres_outils_perso"]
        dlg = DLG_Barres_outils.Dialog(self.parent, texte=texte)
        dlg.ShowModal()
        texteBarres = dlg.GetTexte()
        listeBarresAffichees = dlg.GetListeAffichees()
        dlg.Destroy()
        self.parent.userConfig["barres_outils_perso"] = texteBarres

        # Met à jour chaque barre d'outils
        if len(texteBarres) > 0:
            listeTextesBarres = texteBarres.split("@@@@")
        else:
            listeTextesBarres = []

        listeCodesBarresNouvelles = []
        for texte in listeTextesBarres:
            code, label, observations, style, contenu = texte.split("###")
            listeCodesBarresNouvelles.append(code)
            panneau = self.parent._mgr.GetPane(code)

            if panneau.IsOk():
                # Si la barre existe déjà
                tb = self.parent.dictBarresOutils[code]["ctrl"]

                # Modification de la barre
                if self.parent.dictBarresOutils[code]["texte"] != texte:
                    self.parent.CreerBarreOutils(texte, ctrl=tb)
                    panneau.BestSize(tb.DoGetBestSize())
                    self.parent.dictBarresOutils[code]["texte"] = texte

                # Affichage ou masquage
                if code in listeBarresAffichees:
                    panneau.Show()
                else:
                    panneau.Hide()
                self.parent._mgr.Update()
            else:
                # Si la barre n'existe pas
                self.parent.CreerBarreOutils(texte)

        # Suppression des barres supprimées
        for code in listeCodesBarresActuelles:
            if code not in listeCodesBarresNouvelles:
                tb = self.parent.dictBarresOutils[code]["ctrl"]
                panneau = self.parent._mgr.GetPane(code)
                self.parent._mgr.ClosePane(panneau)
                self.parent._mgr.Update()

    def On_affichage_actualiser(self, event):
        self.parent.MAJ()

    def On_outils_stats(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "outils_stats", "consulter") == False: return
        from Dlg import DLG_Stats
        dlg = DLG_Stats.Dialog(self.parent)
        if dlg.ModificationParametres(premiere=True) == True:
            dlg.ShowModal()
        dlg.Destroy()

    def On_outils_nomadhys_synchro(self, event):
        from Dlg import DLG_Synchronisation
        dlg = DLG_Synchronisation.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()
        if hasattr(self.parent, "ctrl_serveur_nomade"):
            self.parent.ctrl_serveur_nomade.MAJ()

    def On_outils_connecthys_synchro(self, event):
        from Dlg import DLG_Portail_config
        dlg = DLG_Portail_config.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()
        self.parent.AfficherServeurConnecthys()
        self.parent.ctrl_remplissage.MAJ()

    def On_outils_connecthys_traiter(self, event):
        from Dlg import DLG_Portail_demandes
        dlg = DLG_Portail_demandes.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()
        self.parent.ctrl_remplissage.MAJ()
        if hasattr(self, "ctrl_serveur_portail"):
            self.parent.ctrl_serveur_portail.MAJ()

    def On_outils_villes(self, event):
        from Dlg import DLG_Villes
        dlg = DLG_Villes.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_outils_calculatrice(self, event):
        FonctionsPerso.OuvrirCalculatrice()

    def On_outils_calendrier(self, event):
        from Dlg import DLG_Calendrier
        dlg = DLG_Calendrier.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_outils_meteo(self, event):
        dlg = wx.MessageDialog(self.parent,
                               _("Cette fonction n'est plus accessible pour le moment car Noethys utilisait une API Météo que Google vient de supprimer définitivement. Je dois donc prendre le temps de trouver une API équivalente.\n\nMerci de votre compréhension.\n\nIvan"),
                               _("Fonction indisponible"),
                               wx.OK | wx.ICON_EXCLAMATION)
        dlg.ShowModal()
        dlg.Destroy()

    ##        from Dlg import DLG_Meteo
    ##        dlg = DLG_Meteo.Dialog(self.parent)
    ##        dlg.ShowModal()
    ##        dlg.Destroy()

    def On_outils_horaires_soleil(self, event):
        from Dlg import DLG_Horaires_soleil
        dlg = DLG_Horaires_soleil.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_outils_gps(self, event):
        from Dlg import DLG_Geolocalisation
        dlg = DLG_Geolocalisation.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_outils_carnet(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "outils_carnet", "consulter") == False: return
        from Dlg import DLG_Contacts
        dlg = DLG_Contacts.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_outils_emails(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "outils_editeur_emails", "consulter") == False: return
        from Dlg import DLG_Mailer
        dlg = DLG_Mailer.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_outils_sms(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "outils_envoi_sms", "consulter") == False: return
        from Dlg import DLG_Envoi_sms
        dlg = DLG_Envoi_sms.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_outils_connexions(self, event):
        """ Connexions réseau """
        if "[RESEAU]" not in self.parent.userConfig["nomFichier"]:
            dlg = wx.MessageDialog(self.parent,
                                   _("Cette fonction n'est accessible que si vous utilisez un fichier réseau !"),
                                   _("Accès non autorisé"),
                                   wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            return
        from Dlg import DLG_Connexions
        dlg = DLG_Connexions.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_outils_messages(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "outils_messages", "consulter") == False: return
        from Dlg import DLG_Liste_messages
        dlg = DLG_Liste_messages.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()
        self.parent.ctrl_messages.MAJ()

    def On_outils_historique(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "outils_historique", "consulter") == False: return
        from Dlg import DLG_Historique
        dlg = DLG_Historique.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_outils_correcteur(self, event):
        """ Purger l'historique """
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "outils_utilitaires", "consulter") == False: return
        from Dlg import DLG_Depannage
        dlg = DLG_Depannage.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_outils_coherence(self, event):
        """ recherche et correction de cohérence tables matthania """
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "outils_utilitaires", "consulter") == False: return
        from Gest import GestionCoherence
        dlg = GestionCoherence.DLG_Diagnostic()
        del dlg

    def On_outils_purger_historique(self, event):
        """ Purger l'historique """
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "outils_utilitaires", "consulter") == False: return
        from Dlg import DLG_Purge_Historique
        dlg = DLG_Purge_Historique.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_outils_purger_journal_badgeage(self, event):
        """ Purger le journal de badgeage """
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "outils_utilitaires", "consulter") == False: return
        from Ol import OL_Badgeage_log
        OL_Badgeage_log.Purger()

    def On_outils_purger_archives_badgeage(self, event):
        """ Purger les archives de badgeage importés """
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "outils_utilitaires", "consulter") == False: return
        from Dlg import DLG_Badgeage_importation
        DLG_Badgeage_importation.Purger()

    def On_outils_purger_rep_updates(self, event):
        """ Purger le répertoire Updates """
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "outils_utilitaires", "consulter") == False: return
        dlg = wx.MessageDialog(self.parent,
                               _("Souhaitez-vous vraiment purger le répertoire Updates ?"),
                               _("Purger"),
                               wx.YES_NO | wx.NO_DEFAULT | wx.CANCEL | wx.ICON_INFORMATION)
        if dlg.ShowModal() == wx.ID_YES:
            FonctionsPerso.VideRepertoireUpdates(forcer=True)
        dlg.Destroy()

    def On_outils_ouvrir_rep_utilisateur(self, event):
        """ Ouvrir le répertoire Utilisateur """
        UTILS_Fichiers.OuvrirRepertoire(UTILS_Fichiers.GetRepUtilisateur())

    def On_outils_ouvrir_rep_donnees(self, event):
        """ Ouvrir le répertoire Utilisateur """
        UTILS_Fichiers.OuvrirRepertoire(UTILS_Fichiers.GetRepData())

    def On_outils_extensions(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "outils_utilitaires", "consulter") == False: return
        from Dlg import DLG_Extensions
        dlg = DLG_Extensions.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_outils_procedures(self, event):
        """ Commande spéciale """
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "outils_utilitaires", "consulter") == False: return
        from Utils import UTILS_Procedures
        dlg = wx.TextEntryDialog(self,
                                 _("Entrez le code de procédure qui vous a été communiqué :"),
                                 _("Procédure"), "")
        if dlg.ShowModal() == wx.ID_OK:
            code = dlg.GetValue()
            UTILS_Procedures.Procedure(code)
        dlg.Destroy()

    def On_outils_procedure_e4072(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "outils_utilitaires", "consulter") == False: return
        from Utils import UTILS_Procedures
        UTILS_Procedures.E4072()

    def On_outils_creation_titulaires_helios(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "outils_utilitaires", "consulter") == False: return
        from Utils import UTILS_Procedures
        UTILS_Procedures.A7650()

    def On_outils_reinitialisation(self, event):
        """ Réinitialisation du fichier de configuration """
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "outils_utilitaires", "consulter") == False: return
        message = _(
            "Pour réinitialiser votre fichier configuration, vous devez quitter Noethys et le relancer en conservant la touche ALT gauche de votre clavier enfoncée.\n\nCette fonctionnalité est sans danger : Seront par exemple réinitialisés la liste des derniers fichiers ouverts, les périodes de références, les affichages personnalisés, etc...")
        dlg = wx.MessageDialog(self.parent, message, _("Réinitialisation"),
                               wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()

    def On_outils_transfert_tables(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "outils_utilitaires", "consulter") == False: return
        from Dlg import DLG_Transfert_tables
        dlg = DLG_Transfert_tables.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_outils_prestations_sans_conso(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "outils_utilitaires", "consulter") == False: return
        from Dlg import DLG_Prestations_sans_conso
        dlg = DLG_Prestations_sans_conso.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_outils_conso_sans_prestations(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "outils_utilitaires", "consulter") == False: return
        from Dlg import DLG_Conso_sans_prestations
        dlg = DLG_Conso_sans_prestations.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_outils_deverrouillage_forfaits(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "outils_utilitaires", "consulter") == False: return
        from Dlg import DLG_Deverrouillage_forfaits
        dlg = DLG_Deverrouillage_forfaits.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_outils_appliquer_tva(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "outils_utilitaires", "consulter") == False: return
        from Utils import UTILS_Appliquer_tva
        UTILS_Appliquer_tva.Appliquer()

    def On_outils_appliquer_code_comptable(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "outils_utilitaires", "consulter") == False: return
        from Utils import UTILS_Appliquer_code_compta
        UTILS_Appliquer_code_compta.Appliquer()

    def On_outils_appliquer_code_produit_local(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "outils_utilitaires", "consulter") == False: return
        from Utils import UTILS_Appliquer_code_produit_local
        UTILS_Appliquer_code_produit_local.Appliquer()

    def On_outils_conversion_rib_sepa(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "outils_utilitaires", "consulter") == False: return
        from Dlg import DLG_Transfert_RIB
        dlg = DLG_Transfert_RIB.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_outils_console_python(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "outils_utilitaires", "consulter") == False: return
        from Dlg import DLG_Console_python
        dlg = DLG_Console_python.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_outils_console_sql(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "outils_utilitaires", "consulter") == False: return
        from Dlg import DLG_Console_sql
        dlg = DLG_Console_sql.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_outils_liste_perso(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "outils_utilitaires", "consulter") == False: return
        from Dlg import DLG_Liste_perso
        dlg = DLG_Liste_perso.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_outils_traductions(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "outils_traductions", "consulter") == False: return
        from Dlg import DLG_Traductions
        dlg = DLG_Traductions.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()
        self.parent.ChargeTraduction()

    def On_outils_ajoutTables(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "outils_utilitaires", "consulter") == False: return
        from Dlg import DLG_Nouveau_fichier
        dlg = DLG_Nouveau_fichier.DlgAjoutTables(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_reglements_regler_facture(self, event):
        from Ctrl import CTRL_Numfacture
        dlg = CTRL_Numfacture.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_reglements_recus(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "reglements_recus", "consulter") == False: return
        from Dlg import DLG_Liste_recus
        dlg = DLG_Liste_recus.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_reglements_recherche(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "reglements_liste", "consulter") == False: return
        from Dlg import DLG_Liste_reglements
        dlg = DLG_Liste_reglements.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_reglements_detail(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "reglements_detail", "consulter") == False: return
        from Dlg import DLG_Liste_reglements_detail
        dlg = DLG_Liste_reglements_detail.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_reglements_ventilation(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "facturation_ventilation", "consulter") == False: return
        from Dlg import DLG_Verification_ventilation
        dlg = DLG_Verification_ventilation.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_reglements_depot_prestations(self, event):
        if self.VerificationVentilation() == False: return
        from Dlg import DLG_Depots_prestations
        dlg = DLG_Depots_prestations.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_reglements_analyse_ventilation(self, event):
        # Vérification de la ventilation
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "facturation_ventilation", "consulter") == False: return
        if self.VerificationVentilation() == False: return
        from Dlg import DLG_Synthese_ventilation
        dlg = DLG_Synthese_ventilation.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_reglements_synthese_modes(self, event):
        # Vérification de la ventilation
        if self.VerificationVentilation() == False: return
        from Dlg import DLG_Synthese_modes_reglements
        dlg = DLG_Synthese_modes_reglements.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_reglements_depots(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "reglements_depots", "consulter") == False: return
        from Dlg import DLG_Depots
        dlg = DLG_Depots.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_facturation_attestations(self, event):
        from Dlg import DLG_Liste_attestations
        dlg = DLG_Liste_attestations.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def VerificationVentilation(self):
        # Vérification de la ventilation
        from Dlg import DLG_Verification_ventilation
        tracks = DLG_Verification_ventilation.Verification()
        if len(tracks) > 0:
            dlg = wx.MessageDialog(self.parent,
                                   _("Un ou plusieurs règlements peuvent être ventilés.\n\nSouhaitez-vous le faire maintenant (conseillé) ?"),
                                   _("Ventilation"),
                                   wx.YES_NO | wx.YES_DEFAULT | wx.CANCEL | wx.ICON_EXCLAMATION)
            reponse = dlg.ShowModal()
            dlg.Destroy()
            if reponse == wx.ID_YES:
                dlg = DLG_Verification_ventilation.Dialog(
                    self)  # , tracks=tracks)
                dlg.ShowModal()
                dlg.Destroy()
            if reponse == wx.ID_CANCEL:
                return False
        return True

    def On_facturation_factures_generation(self, event):
        if self.VerificationVentilation() == False: return
        from Dlg import DLG_Factures_generation
        dlg = DLG_Factures_generation.Dialog(self.parent)
        dlg.ShowModal()
        try:
            dlg.Destroy()
        except:
            pass

    def On_facturation_factures_liste(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "facturation_factures", "consulter") == False: return
        if self.VerificationVentilation() == False: return
        from Dlg import DLG_Liste_factures
        dlg = DLG_Liste_factures.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_facturation_factures_prelevement(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "facturation_prelevements", "consulter") == False: return
        if self.VerificationVentilation() == False: return
        from Dlg import DLG_Lots_prelevements
        dlg = DLG_Lots_prelevements.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_facturation_factures_helios(self, event):
        if self.VerificationVentilation() == False: return
        from Utils import UTILS_Pes

        # Obsolète, donc PES imposé
        choix = "pes"  # UTILS_Pes.DemanderChoix(self.parent)

        if choix == "rolmre":
            from Dlg import DLG_Export_helios
            dlg = DLG_Export_helios.Dialog(self.parent)
            dlg.ShowModal()
            dlg.Destroy()

        if choix == "pes":
            if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
                "facturation_helios", "consulter") == False: return
            if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
                "facturation_helios", "creer") == False: return
            from Dlg import DLG_Lots_pes
            dlg = DLG_Lots_pes.Dialog(self.parent)
            dlg.ShowModal()
            dlg.Destroy()

    def On_facturation_factures_email(self, event):
        if self.VerificationVentilation() == False: return
        from Dlg import DLG_Factures_email
        dlg = DLG_Factures_email.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_facturation_factures_imprimer(self, event):
        if self.VerificationVentilation() == False: return
        from Dlg import DLG_Factures_impression
        dlg = DLG_Factures_impression.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_facturation_rappels_generation(self, event):
        if self.VerificationVentilation() == False: return
        from Dlg import DLG_Rappels_generation
        dlg = DLG_Rappels_generation.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_facturation_rappels_email(self, event):
        if self.VerificationVentilation() == False: return
        from Dlg import DLG_Rappels_email
        dlg = DLG_Rappels_email.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_facturation_rappels_imprimer(self, event):
        if self.VerificationVentilation() == False: return
        from Dlg import DLG_Rappels_impression
        dlg = DLG_Rappels_impression.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_facturation_rappels_liste(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "facturation_rappels", "consulter") == False: return
        if self.VerificationVentilation() == False: return
        from Dlg import DLG_Liste_rappels
        dlg = DLG_Liste_rappels.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_facturation_attestations_generation(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "facturation_attestations", "creer") == False: return
        if self.VerificationVentilation() == False: return
        from Dlg import DLG_Attestations_annuelles
        dlg = DLG_Attestations_annuelles.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_facturation_attestations_liste(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "facturation_attestations", "consulter") == False: return
        from Dlg import DLG_Liste_attestations
        dlg = DLG_Liste_attestations.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_facturation_attestations_cerfa_generation(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "facturation_attestations", "creer") == False: return
        if self.VerificationVentilation() == False: return
        from Dlg import DLG_Attestations_cerfa
        dlg = DLG_Attestations_cerfa.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_facturation_attestations_fiscales_generation(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "facturation_attestations", "creer") == False: return
        if self.VerificationVentilation() == False: return
        from Dlg import DLG_Attestations_fiscales_generation
        dlg = DLG_Attestations_fiscales_generation.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_facturation_liste_tarifs(self, event):
        from Dlg import DLG_Liste_tarifs
        dlg = DLG_Liste_tarifs.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_facturation_validation_contratspsu(self, event):
        if self.VerificationVentilation() == False: return
        from Dlg import DLG_Contratpsu_validation
        dlg = DLG_Contratpsu_validation.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_facturation_liste_prestations(self, event):
        if self.VerificationVentilation() == False: return
        from Dlg import DLG_Liste_prestations
        dlg = DLG_Liste_prestations.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_facturation_recalculer_prestations(self, event):
        from Dlg import DLG_Recalculer_prestations
        dlg = DLG_Recalculer_prestations.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_facturation_synthese_deductions(self, event):
        from Dlg import DLG_Synthese_deductions
        dlg = DLG_Synthese_deductions.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_facturation_liste_deductions(self, event):
        if self.VerificationVentilation() == False: return
        from Dlg import DLG_Liste_deductions
        dlg = DLG_Liste_deductions.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_facturation_saisir_deductions(self, event):
        if self.VerificationVentilation() == False: return
        from Dlg import DLG_Saisie_lot_deductions
        dlg = DLG_Saisie_lot_deductions.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_facturation_liste_parrainages(self, event):
        from Dlg import DLG_Liste_parrainages
        dlg = DLG_Liste_parrainages.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_facturation_saisir_lot_forfaits_credits(self, event):
        from Dlg import DLG_Saisie_lot_forfaits_credits
        dlg = DLG_Saisie_lot_forfaits_credits.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_facturation_soldes(self, event):
        if self.VerificationVentilation() == False:
            return
        from Dlg import DLG_Soldes
        dlg = DLG_Soldes.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_facturation_soldes_individuels(self, event):
        if self.VerificationVentilation() == False:
            return
        from Dlg import DLG_Liste_nominative_soldes
        dlg = DLG_Liste_nominative_soldes.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_facturation_solder_impayes(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "facturation_solder_impayes", "creer") == False: return
        if self.VerificationVentilation() == False:
            return
        from Dlg import DLG_Solder_impayes
        dlg = DLG_Solder_impayes.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_facturation_prestations_villes(self, event):
        if self.VerificationVentilation() == False:
            return
        from Dlg import DLG_Liste_prestations_villes
        dlg = DLG_Liste_prestations_villes.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_facturation_synthese_prestations(self, event):
        if self.VerificationVentilation() == False:
            return
        from Dlg import DLG_Synthese_prestations
        dlg = DLG_Synthese_prestations.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_facturation_synthese_impayes(self, event):
        if self.VerificationVentilation() == False:
            return
        from Dlg import DLG_Synthese_impayes
        dlg = DLG_Synthese_impayes.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_facturation_analyse_facturation(self, event):
        if self.VerificationVentilation() == False:
            return
        # JB
        from Dlg import DLG_Liste_facturation
        dlg = DLG_Liste_facturation.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_facturation_export_compta(self, event):
        if self.VerificationVentilation() == False:
            return
        from Dlg import DLG_Export_compta
        dlg = DLG_Export_compta.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_cotisations_recherche(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "cotisations_liste", "consulter") == False: return
        from Dlg import DLG_Liste_cotisations
        dlg = DLG_Liste_cotisations.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_cotisations_manquantes(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "cotisations_manquantes", "consulter") == False: return
        from Dlg import DLG_Cotisations_manquantes
        dlg = DLG_Cotisations_manquantes.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_cotisations_saisir_lot_cotisations(self, event):
        from Dlg import DLG_Saisie_lot_cotisations
        dlg = DLG_Saisie_lot_cotisations.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_cotisations_imprimer(self, event):
        if self.VerificationVentilation() == False: return
        from Dlg import DLG_Cotisations_impression
        dlg = DLG_Cotisations_impression.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_cotisations_email(self, event):
        if self.VerificationVentilation() == False: return
        from Dlg import DLG_Cotisations_email
        dlg = DLG_Cotisations_email.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_cotisations_depots(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "cotisations_depots", "consulter") == False: return
        from Dlg import DLG_Depots_cotisations
        dlg = DLG_Depots_cotisations.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_locations_produits(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "locations_produits", "consulter") == False: return
        from Dlg import DLG_Produits_liste
        dlg = DLG_Produits_liste.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()
        self.parent.ctrl_remplissage.MAJ()

    def On_locations_locations(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "locations_locations", "consulter") == False: return
        from Dlg import DLG_Locations
        dlg = DLG_Locations.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()
        self.parent.ctrl_remplissage.MAJ()

    def On_locations_imprimer(self, event):
        from Dlg import DLG_Locations_impression
        dlg = DLG_Locations_impression.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_locations_email(self, event):
        from Dlg import DLG_Locations_email
        dlg = DLG_Locations_email.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_locations_demandes(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "locations_demandes", "consulter") == False: return
        from Dlg import DLG_Locations_demandes
        dlg = DLG_Locations_demandes.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()
        self.parent.ctrl_remplissage.MAJ()

    def On_locations_demandes_imprimer(self, event):
        from Dlg import DLG_Locations_demandes_impression
        dlg = DLG_Locations_demandes_impression.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_locations_demandes_email(self, event):
        from Dlg import DLG_Locations_demandes_email
        dlg = DLG_Locations_demandes_email.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_locations_planning(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "locations_planning", "consulter") == False: return
        from Dlg import DLG_Locations_planning
        dlg = DLG_Locations_planning.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()
        self.parent.ctrl_remplissage.MAJ()

    def On_locations_chronologie(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "locations_chronologie", "consulter") == False: return
        from Dlg import DLG_Locations_chronologie
        dlg = DLG_Locations_chronologie.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()
        self.parent.ctrl_remplissage.MAJ()

    def On_locations_tableau(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "locations_tableau", "consulter") == False: return
        from Dlg import DLG_Locations_tableau
        dlg = DLG_Locations_tableau.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()
        self.parent.ctrl_remplissage.MAJ()

    def On_locations_synthese(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "locations_synthese", "consulter") == False: return
        from Dlg import DLG_Synthese_locations
        dlg = DLG_Synthese_locations.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_locations_images(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "locations_images", "consulter") == False: return
        from Dlg import DLG_Categories_produits_images
        dlg = DLG_Categories_produits_images.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()
        self.parent.ctrl_remplissage.MAJ()

    def On_imprim_conso_journ(self, event):
        from Dlg import DLG_Impression_conso
        dlg = DLG_Impression_conso.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_conso_gestionnaire(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "consommations_conso", "consulter") == False: return
        from Dlg import DLG_Gestionnaire_conso
        dlg = DLG_Gestionnaire_conso.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()
        self.parent.ctrl_remplissage.MAJ()

    def On_conso_traitement_lot(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "consommations_conso", "saisie") == False: return
        from Dlg import DLG_Saisie_lot_conso_global
        dlg = DLG_Saisie_lot_conso_global.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()
        self.parent.ctrl_remplissage.MAJ()

    def On_conso_liste_detail_conso(self, event):
        from Dlg import DLG_Liste_consommations
        dlg = DLG_Liste_consommations.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()
        self.parent.ctrl_remplissage.MAJ()

    def On_conso_attente(self, event):
        self.parent.ctrl_remplissage.OuvrirListeAttente()

    def On_conso_refus(self, event):
        self.parent.ctrl_remplissage.OuvrirListeRefus()

    def On_conso_absences(self, event):
        from Dlg import DLG_Liste_absences
        dlg = DLG_Liste_absences.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_conso_synthese_conso(self, event):
        from Dlg import DLG_Synthese_conso
        dlg = DLG_Synthese_conso.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_conso_etat_global(self, event):
        from Dlg import DLG_Etat_global
        dlg = DLG_Etat_global.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_conso_etat_nominatif(self, event):
        from Dlg import DLG_Etat_nomin
        dlg = DLG_Etat_nomin.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_conso_badgeage(self, event):
        from Dlg import DLG_Badgeage
        dlg = DLG_Badgeage.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_conso_remplissage(self, event):
        from Dlg import DLG_Remplissage
        dlg = DLG_Remplissage.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_conso_commandes(self, event):
        from Dlg import DLG_Commandes
        dlg = DLG_Commandes.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_conso_menus(self, event):
        from Dlg import DLG_Menus
        dlg = DLG_Menus.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_individus_scolarite(self, event):
        from Dlg import DLG_Inscriptions_scolaires
        dlg = DLG_Inscriptions_scolaires.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_individus_inscriptions(self, event):
        from Dlg import DLG_Liste_inscriptions
        dlg = DLG_Liste_inscriptions.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_individus_inscriptions_Y(self, event):
        from Dlg import DLG_Liste_inscriptions_Y
        dlg = DLG_Liste_inscriptions_Y.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_export_remplissage(self, event):
        from Dlg import DLG_Tableau_bord
        dlg = DLG_Tableau_bord.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_individus_saisir_lot_inscriptions(self, event):
        from Dlg import DLG_Saisie_lot_inscriptions
        dlg = DLG_Saisie_lot_inscriptions.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_inscriptions_imprimer(self, event):
        from Dlg import DLG_Inscriptions_impression
        dlg = DLG_Inscriptions_impression.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_inscriptions_email(self, event):
        from Dlg import DLG_Inscriptions_email
        dlg = DLG_Inscriptions_email.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_inscriptions_attente(self, event):
        from Dlg import DLG_Inscriptions_attente
        dlg = DLG_Inscriptions_attente.Dialog(self.parent, liste_activites=None,
                                              mode="attente")
        reponse = dlg.ShowModal()
        dlg.Destroy()
        self.parent.ctrl_remplissage.MAJ()

    def On_inscriptions_refus(self, event):
        from Dlg import DLG_Inscriptions_attente
        dlg = DLG_Inscriptions_attente.Dialog(self.parent, liste_activites=None,
                                              mode="refus")
        reponse = dlg.ShowModal()
        dlg.Destroy()
        self.parent.ctrl_remplissage.MAJ()

    def On_individus_contrats(self, event):
        from Dlg import DLG_Liste_contrats
        dlg = DLG_Liste_contrats.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()
        self.parent.ctrl_remplissage.MAJ()

    def On_individus_individus(self, event):
        from Dlg import DLG_Liste_individus
        dlg = DLG_Liste_individus.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_individus_familles(self, event):
        from Dlg import DLG_Liste_familles
        dlg = DLG_Liste_familles.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_individus_transports_recap(self, event):
        from Dlg import DLG_Liste_transports_recap
        dlg = DLG_Liste_transports_recap.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_individus_transports_detail(self, event):
        from Dlg import DLG_Liste_transports_detail
        dlg = DLG_Liste_transports_detail.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_individus_transports_prog(self, event):
        from Dlg import DLG_Liste_transports_prog
        dlg = DLG_Liste_transports_prog.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_individus_anniversaires(self, event):
        from Dlg import DLG_Anniversaires
        dlg = DLG_Anniversaires.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_individus_infos_med(self, event):
        from Dlg import DLG_Impression_infos_medicales
        dlg = DLG_Impression_infos_medicales.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_individus_pieces_fournies(self, event):
        from Dlg import DLG_Pieces_fournies
        dlg = DLG_Pieces_fournies.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_individus_pieces_manquantes(self, event):
        from Dlg import DLG_Pieces_manquantes
        dlg = DLG_Pieces_manquantes.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_individus_regimes_caisses(self, event):
        from Dlg import DLG_Liste_regimes
        dlg = DLG_Liste_regimes.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_individus_quotients(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "familles_quotients", "consulter") == False: return
        from Dlg import DLG_Liste_quotients
        dlg = DLG_Liste_quotients.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_individus_mandats(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "familles_mandats", "consulter") == False: return
        from Dlg import DLG_Liste_mandats
        dlg = DLG_Liste_mandats.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_individus_codes_comptables(self, event):
        from Dlg import DLG_Liste_codes_comptables
        dlg = DLG_Liste_codes_comptables.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_individus_comptes_internet(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "familles_comptes_internet", "consulter") == False: return
        from Dlg import DLG_Comptes_internet
        dlg = DLG_Comptes_internet.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_individus_importer_photos(self, event):
        from Dlg import DLG_Importation_photos
        dlg = DLG_Importation_photos.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_individus_importer_csv(self, event):
        from Dlg import DLG_Importation_individus
        dlg = DLG_Importation_individus.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()
        self.parent.ctrl_individus.MAJ()

    def On_individus_importer_fichier(self, event):
        from Dlg import DLG_Importation_fichier
        dlg = DLG_Importation_fichier.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()
        self.parent.ctrl_individus.MAJ()

    def On_individus_archiver_individus(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "individus_archiver", "creer") == False: return
        from Dlg import DLG_Archivage
        dlg = DLG_Archivage.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()
        self.parent.ctrl_individus.MAJ()

    def On_individus_exporter_familles(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "familles_export", "creer") == False: return
        from Dlg import DLG_Export_familles
        dlg = DLG_Export_familles.Dialog(self.parent, IDfamille=None)
        dlg.ShowModal()
        dlg.Destroy()

    def On_individus_edition_etiquettes(self, event):
        from Dlg import DLG_Impression_etiquettes
        dlg = DLG_Impression_etiquettes.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_individus_etiquettes_original(self, event):
        from Dlg import DLG_Impression_etiquettesORIGINAL
        dlg = DLG_Impression_etiquettesORIGINAL.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_Comptabilite_comptes(self, event):
        from Dlg import DLG_Liste_comptes
        dlg = DLG_Liste_comptes.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_Comptabilite_operations_tresorerie(self, event):
        from Dlg import DLG_Liste_operations_tresorerie
        dlg = DLG_Liste_operations_tresorerie.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_Comptabilite_operations_budgetaires(self, event):
        from Dlg import DLG_Liste_operations_budgetaires
        dlg = DLG_Liste_operations_budgetaires.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_Comptabilite_virements(self, event):
        from Dlg import DLG_Liste_virements
        dlg = DLG_Liste_virements.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_Comptabilite_rapprochement(self, event):
        from Dlg import DLG_Releves_compta
        dlg = DLG_Releves_compta.Dialog(self.parent,
                                        titre=_("Rapprochement bancaire"))
        dlg.ShowModal()
        dlg.Destroy()

    def On_Comptabilite_tresorerie(self, event):
        from Dlg import DLG_Tresorerie
        dlg = DLG_Tresorerie.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_Comptabilite_budgets(self, event):
        from Dlg import DLG_Suivi_budget
        dlg = DLG_Suivi_budget.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_Comptabilite_graphiques(self, event):
        from Dlg import DLG_Compta_graphiques
        dlg = DLG_Compta_graphiques.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

    def On_aide_aide(self, event):
        from Utils import UTILS_Aide
        UTILS_Aide.Aide(None)

    def On_aide_guide_demarrage(self, event):
        """ Accéder à la page de téléchargement du guide de démarrage rapide """
        FonctionsPerso.LanceFichierExterne(
            "https://www.noethys.com/index.php?option=com_content&view=article&id=118&Itemid=45")

    def On_aide_forum(self, event):
        """ Accéder au forum d'entraide """
        FonctionsPerso.LanceFichierExterne(
            "https://www.noethys.com/index.php?option=com_kunena&Itemid=7")

    def On_aide_videos(self, event):
        """ Accéder au tutoriels vidéos """
        FonctionsPerso.LanceFichierExterne(
            "https://www.noethys.com/index.php?option=com_content&view=article&id=27&Itemid=16")

    def On_aide_telechargements(self, event):
        """ Accéder à la plate-forme de téléchargements communautaire """
        FonctionsPerso.LanceFichierExterne(
            "https://www.noethys.com/index.php?option=com_phocadownload&view=section&id=2&Itemid=21")

    def On_aide_services(self, event):
        """ L'offre de services de Noethys """
        from Dlg import DLG_Financement
        dlg = DLG_Financement.Dialog(None, code="documentation")
        dlg.ShowModal()
        dlg.Destroy()

    def On_aide_auteur(self, event):
        """ Envoyer un email à l'auteur """
        FonctionsPerso.LanceFichierExterne(
            "https://www.noethys.com/index.php?option=com_contact&view=contact&id=1&Itemid=13")

    def On_propos_versions(self, event):
        """ A propos : Notes de versions """
        # Lecture du fichier
        fichier = codecs.open(
            FonctionsPerso.GetRepertoireProjet("Versions.txt"),
            encoding='utf-8', mode='r')
        msg = fichier.read()
        fichier.close()
        from Dlg import DLG_Messagebox
        dlg = DLG_Messagebox.Dialog(self.parent, titre=_("Notes de versions"),
                                    introduction=_(
                                        "Liste des versions du logiciel :"),
                                    detail=msg, icone=wx.ICON_INFORMATION,
                                    boutons=[_("Fermer"), ], defaut=0)
        dlg.ShowModal()
        dlg.Destroy()

    def On_propos_licence(self, event):
        """ A propos : Licence """
        import wx.lib.dialogs
        fichier = codecs.open(
            FonctionsPerso.GetRepertoireProjet("Licence.txt"),
            encoding='utf-8', mode='r')
        msg = fichier.read()
        fichier.close()
        dlg = wx.lib.dialogs.ScrolledMessageDialog(self.parent, msg, _("Licence"),
                                                   size=(500, 500))
        dlg.ShowModal()

    def On_propos_soutenir(self, event):
        """ A propos : Soutenir Noethys """
        from Dlg import DLG_Financement
        dlg = DLG_Financement.Dialog(None, code="documentation")
        dlg.ShowModal()
        dlg.Destroy()

    def On_propos_propos(self, event):
        """ A propos : A propos """
        from Dlg import DLG_A_propos
        dlg = DLG_A_propos.Dialog(self.parent)
        dlg.ShowModal()
        dlg.Destroy()

