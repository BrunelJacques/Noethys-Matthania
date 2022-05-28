#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activit�s
# Site internet :  www.noethys.com
# Auteur:          Ivan LUCAS
# Copyright:       (c) 2010-18 Ivan LUCAS
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------


import Chemins
from Utils import UTILS_Adaptations
from Utils.UTILS_Traduction import _
import wx
from Ctrl import CTRL_Bouton_image
from Utils import UTILS_Parametres
from Ctrl import CTRL_Bandeau
from Ctrl import CTRL_Propertygrid
from Ctrl import CTRL_Saisie_date
from Ctrl import CTRL_Vignettes_documents
import wx.propgrid as wxpg
import copy
import GestionDB
from PIL import Image
import six


LISTE_MODELES = [
    # Arc-en-ciel
    {"label": _("Arc-en-ciel"), "fichier": "Modele_arcenciel.png", "description": _("Format paysage / Mensuel"), "donnees" :
        {'case_fond_alpha': 100, 'case_macaron_hauteur': 12, 'titre_fond_couleur': wx.Colour(0, 128, 192, 255), 'type': u'mensuel', 'case_macaron_largeur': 12, 'pied_hauteur': 15, 'titre_bord_couleur': wx.Colour(0, 128, 192, 255), 'page_fond_image': u'Menus/Arcenciel.jpg',
        'entete_mix_couleurs': True, 'pied_texte_couleur': wx.Colour(255, 255, 255, 255), 'case_macaron_mix_couleurs': True, 'case_macaron_type': u'rond', 'case_macaron_taille_police': 11, 'pied_taille_police': 8}
     },

    # Cuisine
    {"label": _("Cuisine"), "fichier": "Modele_cuisine.png", "description": _("Format paysage / Hebdomadaire"), "donnees":
        {'pied_fond_alpha': 40, 'case_fond_alpha': 80, 'entete_bord_couleur': wx.Colour(128, 128, 255, 255), 'titre_fond_couleur': wx.Colour(0, 128, 255, 255),
         'case_separateur_image': u'aucune', 'titre_bord_couleur': wx.Colour(0, 128, 255, 255), 'page_fond_image': u'Menus/Table_bois.jpg',
         'entete_fond_couleur': wx.Colour(128, 128, 255, 255), 'case_macaron_afficher': False, 'case_taille_police': 12}
     },

    # Noir m�tallique
    {"label": _("Noir m�tallique"), "fichier": "Modele_noirmetallique.png", "description": _("Format paysage / Mensuel"), "donnees":
        {'case_macaron_type': u'rond', 'case_macaron_largeur': 12, 'case_macaron_hauteur': 12, 'page_fond_image': u'Interface/Noir/Fond.jpg', 'pied_hauteur': 20,
         'type': u'mensuel', 'case_macaron_taille_police': 10}
     },

    # Noir m�tallique
    {"label": _("Ballons multicolores"), "fichier": "Modele_ballons.png", "description": _("Format paysage / Mensuel"), "donnees":
        {'pied_fond_alpha': 0, 'case_fond_alpha': 80, 'pied_bord_alpha': 0, 'entete_mix_couleurs': True, 'pied_hauteur': 12, 'page_fond_image': u'Menus/Ballons.jpg',
         'case_bord_couleur': wx.Colour(64, 0, 128, 255), 'pied_taille_police': 8, 'case_macaron_mix_couleurs': True, 'case_rotation_aleatoire': True, 'type': u'mensuel'}
     },

    # Tableau de craie
    {"label": _("Tableau de craie"), "fichier": "Modele_tableaucraie.png", "description": _("Format portrait / Journalier"), "donnees":
        {'case_separateur_type': u'image', 'case_fond_alpha': 0, 'pied_afficher': False, 'entete_afficher': False, 'page_marge_haut': 180, 'page_marge_bas': 100, 'page_format': u'portrait',
         'titre_afficher': False, 'case_bord_alpha': 0, 'page_fond_image': u'Menus/Tableau_craie.jpg','case_texte_couleur': wx.Colour(255, 255, 255, 255),
         'page_marge_droite': 100, 'page_marge_gauche': 100, 'type': u'quotidien', 'case_macaron_afficher': False, 'case_taille_police': 25}
     },

    # Girly
    {"label": _("Girly"), "fichier": "Modele_girly.png", "description": _("Format paysage / Hebdomadaire"), "donnees":
        {'case_separateur_type': u'ligne', 'titre_fond_couleur': wx.Colour(255, 128, 192, 255), 'entete_mix_couleurs': True,
         'case_titre_hauteur': 30, 'entete_afficher': False, 'page_fond_image': u'Menus/Abstrait.jpg', 'case_titre_taille_police': 11,
         'pied_texte_couleur': wx.Colour(255, 255, 255, 255), 'case_titre_afficher': True, 'case_titre_mix_couleurs': True, 'case_macaron_afficher': False,
         'case_taille_police': 14}
     },

    # Raclette
    {"label": _("Raclette"), "fichier": "Modele_hivernal.png", "description": _("Format paysage / Hebdomadaire"), "donnees":
        {'pied_fond_alpha': 0, 'case_separateur_type': u'image', 'case_fond_alpha': 80, 'entete_afficher': False, 'titre_fond_couleur': wx.Colour(255, 255, 255, 255),
         'case_titre_afficher': True, 'case_titre_fond_couleur': wx.Colour(128, 64, 0, 255), 'case_titre_hauteur': 25, 'pied_bord_alpha': 0,
         'page_fond_image': u'Badgeage/Theme_sommets.jpg', 'case_texte_couleur': wx.Colour(128, 64, 0, 255), 'case_titre_taille_police': 12, 'titre_hauteur': 70,
         'titre_texte_couleur': wx.Colour(128, 64, 0, 255), 'titre_bord_couleur': wx.Colour(255, 255, 255, 255), 'case_macaron_afficher': False, 'case_taille_police': 14}
     },

    # Cadeau de No�l
    {"label": _("Cadeau de No�l"), "fichier": "Modele_cadeaunoel.png", "description": _("Format paysage / Hebdomadaire"), "donnees":
        {'case_separateur_type': u'image', 'case_macaron_bord_couleur': wx.Colour(255, 0, 0, 255), 'case_fond_alpha': 70, 'entete_bord_couleur': wx.Colour(0, 128, 0, 255),
         'titre_fond_couleur': wx.Colour(0, 128, 0, 255), 'pied_hauteur': 20, 'pied_taille_police': 9, 'case_separateur_image': u'Ligne_branche.png',
         'titre_bord_couleur': wx.Colour(0, 128, 0, 255), 'page_fond_image': u'Badgeage/Theme_noel.jpg', 'pied_texte_couleur': wx.Colour(255, 255, 255, 255),
         'entete_fond_couleur': wx.Colour(0, 128, 0, 255), 'case_macaron_fond_couleur': wx.Colour(255, 0, 0, 255), 'case_taille_police': 15}
     },

    # Fond marin
    {"label": _("Fond marin"), "fichier": "Modele_fondmarin.png", "description": _("Format paysage / Mensuel"), "donnees":
        {'pied_hauteur': 20, 'type': u'mensuel'}
     },

    # Ardoise
    {"label": _("Ardoise"), "fichier": "Modele_ardoise.png", "description": _("Format portrait / Mensuel"), "donnees":
        {'pied_fond_alpha': 0, 'case_fond_alpha': 0, 'entete_afficher': False, 'titre_fond_couleur': wx.Colour(255, 255, 255, 255), 'type': u'mensuel', 'pied_hauteur': 20, 'page_format': u'portrait',
         'titre_bord_couleur': wx.Colour(255, 255, 255, 255), 'pied_bord_alpha': 0, 'page_fond_image': u'Badgeage/Theme_bleu.jpg', 'case_texte_couleur': wx.Colour(255, 255, 255, 255),
         'pied_texte_couleur': wx.Colour(255, 255, 255, 255), 'case_radius': 0, 'case_titre_afficher': True, 'titre_texte_couleur': wx.Colour(0, 0, 0, 255), 'case_rotation_aleatoire': True,
         'case_titre_mix_couleurs': True, 'case_macaron_afficher': False, 'pied_taille_police': 8}
     },

    # Olive
    {"label": _("Olive"), "fichier": "Modele_olive.png", "description": _("Format paysage / Mensuel"), "donnees":
        {'pied_fond_alpha': 0, 'entete_afficher': False, 'titre_fond_couleur': wx.Colour(128, 128, 0, 255), 'case_titre_afficher': True, 'case_titre_fond_couleur': wx.Colour(128, 128, 0, 255),
         'titre_bord_couleur': wx.Colour(128, 128, 0, 255), 'pied_bord_alpha': 0, 'page_fond_image': u'Badgeage/Theme_defaut.png', 'pied_texte_couleur': wx.Colour(255, 255, 255, 255),
         'pied_hauteur': 14, 'type': u'mensuel', 'case_macaron_afficher': False, 'pied_taille_police': 8}
     },

    # Plage d'�t�
    {"label": _("Plage d'�t�"), "fichier": "Modele_plageete.png", "description": _("Format paysage / Hebdomadaire"), "donnees":
        {'pied_fond_alpha': 0, 'case_separateur_type': u'image', 'entete_bord_couleur': wx.Colour(228, 190, 142, 255), 'titre_fond_couleur': wx.Colour(228, 190, 142, 255),
         'case_titre_fond_couleur': wx.Colour(228, 190, 142, 255), 'pied_taille_police': 8, 'case_separateur_image': u'Ligne_bijou.png', 'pied_bord_alpha': 0,
         'page_fond_image': u'Badgeage/Theme_ocean.jpg', 'pied_texte_couleur': wx.Colour(255, 255, 255, 255), 'entete_fond_couleur': wx.Colour(228, 190, 142, 255),
         'pied_hauteur': 20, 'titre_texte_couleur': wx.Colour(37, 176, 242, 255), 'titre_bord_couleur': wx.Colour(228, 190, 142, 255), 'case_macaron_afficher': False, 'case_taille_police': 15}
     },

    # Bulles de couleur
    {"label": _("Bulles de couleur"), "fichier": "Modele_bullescouleur.png", "description": _("Format paysage / Mensuel"), "donnees":
        {'pied_fond_alpha': 0, 'entete_afficher': False, 'titre_fond_couleur': wx.Colour(128, 128, 255, 255), 'type': u'mensuel', 'pied_hauteur': 20, 'titre_bord_couleur': wx.Colour(128, 128, 255, 255),
         'pied_bord_alpha': 0, 'page_fond_image': u'Badgeage/Theme_vert.jpg', 'pied_texte_couleur': wx.Colour(255, 255, 255, 255), 'case_radius': 30, 'case_titre_afficher': True,
         'case_rotation_aleatoire': True, 'case_titre_mix_couleurs': True, 'case_macaron_afficher': False, 'pied_taille_police': 8}
     },

    # Noir et blanc
    {"label": _("Noir et blanc"), "fichier": "Modele_noiretblanc.png", "description": _("Format portrait / Journalier"), "donnees":
        {'pied_fond_alpha': 40, 'case_separateur_type': u'image', 'case_fond_alpha': 0, 'entete_afficher': False, 'titre_fond_couleur': wx.Colour(255, 255, 255, 255),
         'page_format': u'portrait', 'case_bord_alpha': 0, 'case_separateur_image': u'Ligne_ronds.png', 'titre_bord_couleur': wx.Colour(255, 255, 255, 255),
         'page_fond_image': u'Interface/Noir/Fond.jpg', 'case_texte_couleur': wx.Colour(255, 255, 255, 255), 'titre_hauteur': 80, 'titre_taille_police': 35,
         'titre_texte_couleur': wx.Colour(0, 0, 0, 255), 'type': u'quotidien', 'case_macaron_afficher': False, 'case_taille_police': 30}
     },

    # Montagnes blanches
    {"label": _("Montagnes blanches"), "fichier": "Modele_montagneshiver.png", "description": _("Format paysage / Hebdomadaire"), "donnees":
        {'case_titre_texte_couleur': wx.Colour(0, 128, 255, 255), 'case_fond_alpha': 20, 'pied_afficher': False, 'entete_afficher': False, 'titre_fond_couleur': wx.Colour(255, 255, 255, 255),
         'case_titre_fond_couleur': wx.Colour(255, 255, 255, 255), 'page_marge_bas': 250, 'case_separateur_image': u'Ligne_moderne.png', 'case_titre_hauteur': 30,
         'titre_bord_couleur': wx.Colour(255, 255, 255, 255), 'page_fond_image': u'Badgeage/Theme_hiver.jpg', 'case_texte_couleur': wx.Colour(255, 255, 255, 255), 'case_titre_taille_police': 11,
         'pied_texte_couleur': wx.Colour(192, 192, 192, 255), 'case_titre_afficher': True, 'titre_texte_couleur': wx.Colour(0, 128, 255, 255), 'case_macaron_afficher': False}
     },

    # Minimaliste
    {"label": _("Minimaliste"), "fichier": "Modele_minimaliste.png", "description": _("Format paysage / Hebdomadaire"), "donnees":
        {'legende_hauteur': 20, 'case_radius': 0, 'legende_type': u'carre', 'titre_fond_couleur': wx.Colour(255, 255, 255, 255), 'pied_hauteur': 30, 'page_fond_image': u'aucune',
         'case_titre_fond_couleur': wx.Colour(0, 0, 0, 255), 'entete_afficher': False, 'page_espace_vertical': 0, 'case_bord_couleur': wx.Colour(0, 0, 0, 255),
         'case_titre_taille_police': 10, 'pied_taille_police': 8, 'titre_hauteur': 70, 'case_titre_afficher': True, 'page_espace_horizontal': 0, 'titre_texte_couleur': wx.Colour(0, 0, 0, 255),
         'titre_bord_couleur': wx.Colour(255, 255, 255, 255), 'case_macaron_afficher': False}
     },


]



VALEURS_DEFAUT = {
    # Donn�es
    #"jours_semaine" : [0, 1, 2, 3, 4],
    #"titre_texte" : "",
    #"pied_texte": "Menus susceptibles de modifications",
    #"categories_menus" : [0,],

    "type" : "hebdomadaire",

    # Page
    "page_fond_image": "Interface/Bleu/Fond.jpg",
    "page_format": "paysage",
    "page_marge_gauche": 20,
    "page_marge_droite": 20,
    "page_marge_haut": 20,
    "page_marge_bas": 20,
    "page_espace_horizontal": 10,
    "page_espace_vertical": 10,
    "page_grille": False,

    # Entete
    "entete_afficher": True,
    "entete_fond_couleur": wx.Colour(254, 178, 0),
    "entete_fond_alpha": 1*100,
    "entete_bord_couleur": wx.Colour(254, 178, 0),
    "entete_bord_alpha": 1*100,
    "entete_texte_couleur": wx.WHITE,
    "entete_texte_alpha": 1*100,
    "entete_hauteur": 25,
    "entete_nom_police": "Helvetica-Bold", # Pas int�gr� dans le propertyGrid !
    "entete_taille_police": 15,
    "entete_radius": 5,
    "entete_mix_couleurs": False,

    # Case
    "case_hauteur": 0, # Pas int�gr� dans le propertyGrid !
    "case_radius": 5,
    "case_rotation_aleatoire": False,
    "case_bord_couleur": wx.WHITE,
    "case_bord_alpha": int(0.6*100),
    "case_bord_alpha_vide": int(0.2*100), # Pas int�gr� dans le propertyGrid !
    "case_fond_couleur": wx.WHITE,
    "case_fond_alpha": int(0.6*100),
    "case_fond_alpha_vide": int(0.2*100), # Pas int�gr� dans le propertyGrid !
    "case_repartition_verticale": True,
    "case_nom_police": "Helvetica", # Pas int�gr� dans le propertyGrid !
    "case_taille_police": 10,
    "case_texte_couleur": wx.BLACK,
    "case_marge_haut": 15,
    "case_espace_vertical": 5,
    "case_separateur_type": "aucun",
    "case_separateur_image": "Ligne_retro.png",

    # Case titre
    "case_titre_afficher": False,
    "case_titre_hauteur": 15,
    "case_titre_fond_couleur": wx.Colour(254, 178, 0),
    "case_titre_texte_couleur": wx.WHITE,
    "case_titre_mix_couleurs" : False,
    "case_titre_nom_police": "Helvetica-Bold", # Pas int�gr� dans le propertyGrid !
    "case_titre_taille_police": 8,

    # Macaron
    "case_macaron_afficher": True,
    "case_macaron_type": "carre",
    "case_macaron_radius": 5,
    "case_macaron_largeur": 25,
    "case_macaron_hauteur": 20,
    "case_macaron_bord_couleur": wx.Colour(254, 178, 0),
    "case_macaron_bord_alpha": 1*100,
    "case_macaron_fond_couleur": wx.Colour(254, 178, 0),
    "case_macaron_fond_alpha": 1*100,
    "case_macaron_nom_police": "Helvetica-Bold", # Pas int�gr� dans le propertyGrid !
    "case_macaron_taille_police": 13,
    "case_macaron_texte_couleur": wx.WHITE,
    "case_macaron_mix_couleurs" : False,

    # Titre de page
    "titre_afficher": True,
    "titre_hauteur": 50,
    "titre_bord_couleur": wx.Colour(254, 178, 0),
    "titre_fond_couleur": wx.Colour(254, 178, 0),
    "titre_nom_police": "Helvetica-Bold", # Pas int�gr� dans le propertyGrid !
    "titre_taille_police": 25,
    "titre_texte_couleur": wx.WHITE,

    # L�gende
    "legende_afficher": True,
    "legende_type": "numero",
    "legende_hauteur": 30,
    "legende_radius": 5,
    "legende_bord_couleur": wx.WHITE,
    "legende_bord_alpha": int(0.2 * 100),
    "legende_fond_couleur": wx.WHITE,
    "legende_fond_alpha": 30,
    "legende_nom_police": "Helvetica",  # Pas int�gr� dans le propertyGrid !
    "legende_taille_police": 8,
    "legende_texte_couleur": wx.BLACK,

    # Pied de page
    "pied_afficher": True,
    "pied_hauteur": 50,
    "pied_radius": 5,
    "pied_bord_couleur": wx.WHITE,
    "pied_bord_alpha": int(0.2*100),
    "pied_fond_couleur": wx.WHITE,
    "pied_fond_alpha": int(0.05*100),
    "pied_nom_police": "Helvetica", # Pas int�gr� dans le propertyGrid !
    "pied_taille_police": 10,
    "pied_texte_couleur": wx.BLACK,

}



class CTRL_Parametres(CTRL_Propertygrid.CTRL) :
    def __init__(self, parent, categorie=""):
        self.categorie = categorie
        CTRL_Propertygrid.CTRL.__init__(self, parent)

    
    def Remplissage(self):
        # Rubrique Donn�es
        self.Append(wxpg.PropertyCategory(_("Donn�es")))

        # Jours de la semaine
        nom = "jours_semaine"
        liste_jours = [(0, _("Lundi")), (1, _("Mardi")), (2, _("Mercredi")), (3, _("Jeudi")), (4, _("Vendredi")), (5, _("Samedi")), (6, _("Dimanche"))]
        propriete = CTRL_Propertygrid.Propriete_multichoix(label=_("Jours de la semaine"), name=nom, liste_choix=liste_jours, liste_selections=[0, 1, 2, 3, 4])
        propriete.SetHelpString(_("S�lectionnez les jours de la semaine � inclure. Cliquez sur le bouton � droite du champ de saisie pour acc�der � la fen�tre de s�lection."))
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)

        # Choix des cat�gories
        DB = GestionDB.DB()
        req = """SELECT IDcategorie, nom
        FROM menus_categories 
        ORDER BY ordre;"""
        DB.ExecuterReq(req,MsgBox="ExecuterReq")
        listeDonnees = DB.ResultatReq()
        DB.Close()
        liste_choix = [(0, _("Toutes")),]
        for IDcategorie, nom in listeDonnees:
            liste_choix.append((IDcategorie, nom))

        nom = "categories_menus"
        propriete = CTRL_Propertygrid.Propriete_multichoix(label=_("Cat�gories � afficher"), name=nom, liste_choix=liste_choix, liste_selections=[0,])
        propriete.SetHelpString(_("S�lectionnez les cat�gories de menus � afficher."))
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)

        # Texte de titre de page
        nom = "titre_texte"
        propriete = wxpg.LongStringProperty(label=_("Texte de titre de page"), name=nom, value=u"MENUS -")
        propriete.SetHelpString(_("Saisissez un texte de titre de page"))
        self.Append(propriete)

        # Texte de pied de page
        nom = "pied_texte"
        propriete = wxpg.LongStringProperty(label=_("Texte de pied de page"), name=nom, value=_("Menus susceptibles de modifications"))
        propriete.SetHelpString(_("Saisissez un texte de pied de page"))
        self.Append(propriete)

        # Rubrique page
        self.Append(wxpg.PropertyCategory(_("Page")))

        # Type d'affichage
        nom = "type"
        propriete = CTRL_Propertygrid.Propriete_choix(label=_("Type d'affichage"), name=nom, liste_choix=[("mensuel", _("Mensuel")), ("hebdomadaire", _("Hebdomadaire")), ("quotidien", _("Journalier"))], valeur=VALEURS_DEFAUT[nom])
        propriete.SetEditor("EditeurChoix")
        propriete.SetHelpString(_("S�lectionnez le type d'affichage de la page"))
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)

        # Orientation page
        nom = "page_format"
        propriete = CTRL_Propertygrid.Propriete_choix(label=_("Orientation de la page"), name=nom, liste_choix=[("portrait", _("Portrait")), ("paysage", _("Paysage"))], valeur=VALEURS_DEFAUT[nom])
        propriete.SetEditor("EditeurChoix")
        propriete.SetHelpString(_("S�lectionnez l'orientation de la page"))
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)


        # Image de fond de page
        nom = "page_fond_image"
        liste_images = [("aucune", _("Aucune")),
                        ("Menus/Table_bois.jpg", _("Cuisine")),
                        ("Menus/Abstrait.jpg", _("Abstrait")),
                        ("Menus/Arcenciel.jpg", _("Arc-en-ciel")),
                        ("Menus/Ballons.jpg", _("Ballons")),
                        ("Interface/Bleu/Fond.jpg", _("Fond marin")),
                        ("Menus/Tableau_craie.jpg", _("Tableau de craie")),
                        ("Interface/Noir/Fond.jpg", _("Noir m�tallique")),
                        ("Badgeage/Theme_vert.jpg", _("Vert pomme")),
                        ("Badgeage/Theme_sommets.jpg", _("Sommets enneig�s")),
                        ("Badgeage/Theme_ocean.jpg", _("Plage d'�t�")),
                        ("Badgeage/Theme_noel.jpg", _("Cadeau de No�l")),
                        ("Badgeage/Theme_hiver.jpg", _("Hiver blanc")),
                        ("Badgeage/Theme_bleu.jpg", _("Bleu sombre")),
                        ("Badgeage/Theme_defaut.png", _("Marron chic")),
                        ]
        propriete = CTRL_Propertygrid.Propriete_choix(label=_("Image de fond"), name=nom, liste_choix=liste_images, valeur=VALEURS_DEFAUT[nom])
        propriete.SetEditor("EditeurChoix")
        propriete.SetHelpString(_("S�lectionnez une image de fond"))
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)

        # Marges et espaces
        temp = [
            ("page_marge_gauche", _("Marge gauche")),
            ("page_marge_droite", _("Marge droite")),
            ("page_marge_haut", _("Marge haut")),
            ("page_marge_bas", _("Marge bas")),
            ("page_espace_horizontal", _("Espace horizontal")),
            ("page_espace_vertical", _("Espace vertical")),
        ]
        for nom, label in temp:
            propriete = wxpg.IntProperty(label=label, name=nom, value=VALEURS_DEFAUT[nom])
            propriete.SetHelpString(_("Saisissez une valeur num�rique"))
            propriete.SetAttribute("obligatoire", True)
            self.Append(propriete)
            self.SetPropertyEditor(nom, "SpinCtrl")

        # Afficher grille
        nom = "page_grille"
        propriete = wxpg.BoolProperty(label=_("Afficher la grille"), name=nom, value=VALEURS_DEFAUT[nom])
        propriete.SetHelpString(_("L'affichage de la grille peut faciliter votre travail de mise en page"))
        propriete.SetAttribute("UseCheckbox", True)
        self.Append(propriete)


        # Rubrique Titre de page
        self.Append(wxpg.PropertyCategory(_("Titre de page")))

        # Afficher titre
        nom = "titre_afficher"
        propriete = wxpg.BoolProperty(label=_("Afficher le titre de page"), name=nom, value=VALEURS_DEFAUT[nom])
        propriete.SetHelpString(_("Afficher les macarons"))
        propriete.SetAttribute("UseCheckbox", True)
        self.Append(propriete)

        # Hauteur
        nom = "titre_hauteur"
        propriete = wxpg.IntProperty(label=_("Hauteur"), name=nom, value=VALEURS_DEFAUT[nom])
        propriete.SetHelpString(_("Saisissez une valeur num�rique"))
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)
        self.SetPropertyEditor(nom, "SpinCtrl")

        # Fond et bord
        temp = [
            ("titre_fond", _("fond")),
            ("titre_bord", _("bord")),
        ]
        for code, label in temp:
            # Couleur
            nom = "%s_couleur" % code
            propriete = wxpg.ColourProperty(label=_("Couleur du %s") % label, name=nom, value=VALEURS_DEFAUT[nom])
            propriete.SetHelpString(_("S�lectionnez une couleur"))
            propriete.SetAttribute("obligatoire", True)
            self.Append(propriete)

        # Couleur de texte
        nom = "titre_texte_couleur"
        propriete = wxpg.ColourProperty(label=_("Couleur du texte"), name=nom, value=VALEURS_DEFAUT[nom])
        propriete.SetHelpString(_("S�lectionnez une couleur"))
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)

        # Taille de texte
        nom = "titre_taille_police"
        propriete = wxpg.IntProperty(label=_("Taille de texte"), name=nom, value=VALEURS_DEFAUT[nom])
        propriete.SetHelpString(_("Saisissez une taille de texte"))
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)
        self.SetPropertyEditor(nom, "SpinCtrl")


        # Rubrique Entete
        self.Append(wxpg.PropertyCategory(_("Ent�tes")))

        # Afficher ent�tes
        nom = "entete_afficher"
        propriete = wxpg.BoolProperty(label=_("Afficher les ent�tes des dates"), name=nom, value=VALEURS_DEFAUT[nom])
        propriete.SetHelpString(_("Les ent�tes affichent les dates"))
        propriete.SetAttribute("UseCheckbox", True)
        self.Append(propriete)

        # Fond, bord et texte
        temp = [
            ("entete_fond", _("fond")),
            ("entete_bord", _("bord")),
            ("entete_texte", _("texte")),
        ]
        for code, label in temp:

            # Couleur
            nom = "%s_couleur" % code
            propriete = wxpg.ColourProperty(label=_("Couleur du %s") % label, name=nom, value=VALEURS_DEFAUT[nom])
            propriete.SetHelpString(_("S�lectionnez une couleur"))
            propriete.SetAttribute("obligatoire", True)
            self.Append(propriete)

            # Transparence
            nom = "%s_alpha" % code
            propriete = wxpg.IntProperty(label=_("Opacit� du %s (en %%)") % label, name=nom, value=VALEURS_DEFAUT[nom])
            propriete.SetHelpString(_("Saisissez une valeur num�rique"))
            propriete.SetAttribute("obligatoire", True)
            self.Append(propriete)
            self.SetPropertyEditor(nom, "SpinCtrl")
            propriete.SetAttribute("Min", 0)
            propriete.SetAttribute("Max", 100)

        # Afficher ent�tes
        nom = "entete_mix_couleurs"
        propriete = wxpg.BoolProperty(label=_("Fond mix de couleurs"), name=nom, value=VALEURS_DEFAUT[nom])
        propriete.SetHelpString(_("Afficher un fond avec un mix de couleurs"))
        propriete.SetAttribute("UseCheckbox", True)
        self.Append(propriete)

        # Hauteur de l'entete
        nom = "entete_hauteur"
        propriete = wxpg.IntProperty(label=_("Hauteur"), name=nom, value=VALEURS_DEFAUT[nom])
        propriete.SetHelpString(_("Saisissez une valeur num�rique"))
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)
        self.SetPropertyEditor(nom, "SpinCtrl")

        # Valeur de l'arrondi
        nom = "entete_radius"
        propriete = wxpg.IntProperty(label=_("Valeur de l'arrondi"), name=nom, value=VALEURS_DEFAUT[nom])
        propriete.SetHelpString(_("Saisissez une valeur num�rique"))
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)
        self.SetPropertyEditor(nom, "SpinCtrl")

        # Taille de texte
        nom = "entete_taille_police"
        propriete = wxpg.IntProperty(label=_("Taille de texte"), name=nom, value=VALEURS_DEFAUT[nom])
        propriete.SetHelpString(_("Saisissez une taille de texte"))
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)
        self.SetPropertyEditor(nom, "SpinCtrl")


        # Rubrique Case titre
        self.Append(wxpg.PropertyCategory(_("Titre de case")))

        # Afficher titre de case
        nom = "case_titre_afficher"
        propriete = wxpg.BoolProperty(label=_("Afficher les titres de cases"), name=nom, value=VALEURS_DEFAUT[nom])
        propriete.SetHelpString(_("Afficher les titres de cases"))
        propriete.SetAttribute("UseCheckbox", True)
        self.Append(propriete)

        # Hauteur
        nom = "case_titre_hauteur"
        propriete = wxpg.IntProperty(label=_("Hauteur"), name=nom, value=VALEURS_DEFAUT[nom])
        propriete.SetHelpString(_("Saisissez une valeur num�rique"))
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)
        self.SetPropertyEditor(nom, "SpinCtrl")

        # Couleur de fond
        nom = "case_titre_fond_couleur"
        propriete = wxpg.ColourProperty(label=_("Couleur du fond"), name=nom, value=VALEURS_DEFAUT[nom])
        propriete.SetHelpString(_("S�lectionnez une couleur"))
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)

        # Couleur de texte
        nom = "case_titre_texte_couleur"
        propriete = wxpg.ColourProperty(label=_("Couleur du texte"), name=nom, value=VALEURS_DEFAUT[nom])
        propriete.SetHelpString(_("S�lectionnez une couleur"))
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)

        # Afficher ent�tes
        nom = "case_titre_mix_couleurs"
        propriete = wxpg.BoolProperty(label=_("Fond mix de couleurs"), name=nom, value=VALEURS_DEFAUT[nom])
        propriete.SetHelpString(_("Afficher un fond avec un mix de couleurs"))
        propriete.SetAttribute("UseCheckbox", True)
        self.Append(propriete)

        # Taille de texte
        nom = "case_titre_taille_police"
        propriete = wxpg.IntProperty(label=_("Taille de texte"), name=nom, value=VALEURS_DEFAUT[nom])
        propriete.SetHelpString(_("Saisissez une taille de texte"))
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)
        self.SetPropertyEditor(nom, "SpinCtrl")


        # Rubrique Macaron
        self.Append(wxpg.PropertyCategory(_("Macaron")))

        # Afficher macaron
        nom = "case_macaron_afficher"
        propriete = wxpg.BoolProperty(label=_("Afficher les macarons"), name=nom, value=VALEURS_DEFAUT[nom])
        propriete.SetHelpString(_("Afficher les macarons"))
        propriete.SetAttribute("UseCheckbox", True)
        self.Append(propriete)

        # Type de macaron
        nom = "case_macaron_type"
        propriete = CTRL_Propertygrid.Propriete_choix(label=_("Type de macaron"), name=nom, liste_choix=[("carre", _("Carr�")), ("rond", _("Rond"))], valeur=VALEURS_DEFAUT[nom])
        propriete.SetEditor("EditeurChoix")
        propriete.SetHelpString(_("S�lectionnez le type de macaron"))
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)

        # Valeur de l'arrondi
        nom = "case_macaron_radius"
        propriete = wxpg.IntProperty(label=_("Valeur de l'arrondi"), name=nom, value=VALEURS_DEFAUT[nom])
        propriete.SetHelpString(_("Saisissez une valeur num�rique"))
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)
        self.SetPropertyEditor(nom, "SpinCtrl")

        # Largeur
        nom = "case_macaron_largeur"
        propriete = wxpg.IntProperty(label=_("Largeur"), name=nom, value=VALEURS_DEFAUT[nom])
        propriete.SetHelpString(_("Saisissez une valeur num�rique"))
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)
        self.SetPropertyEditor(nom, "SpinCtrl")

        # Hauteur
        nom = "case_macaron_hauteur"
        propriete = wxpg.IntProperty(label=_("Hauteur"), name=nom, value=VALEURS_DEFAUT[nom])
        propriete.SetHelpString(_("Saisissez une valeur num�rique"))
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)
        self.SetPropertyEditor(nom, "SpinCtrl")

        # Fond et bord
        temp = [
            ("case_macaron_fond", _("fond")),
            ("case_macaron_bord", _("bord")),
        ]
        for code, label in temp:

            # Couleur
            nom = "%s_couleur" % code
            propriete = wxpg.ColourProperty(label=_("Couleur du %s") % label, name=nom, value=VALEURS_DEFAUT[nom])
            propriete.SetHelpString(_("S�lectionnez une couleur"))
            propriete.SetAttribute("obligatoire", True)
            self.Append(propriete)

            # Transparence
            nom = "%s_alpha" % code
            propriete = wxpg.IntProperty(label=_("Opacit� du %s (en %%)") % label, name=nom, value=VALEURS_DEFAUT[nom])
            propriete.SetHelpString(_("Saisissez une valeur num�rique"))
            propriete.SetAttribute("obligatoire", True)
            self.Append(propriete)
            self.SetPropertyEditor(nom, "SpinCtrl")
            propriete.SetAttribute("Min", 0)
            propriete.SetAttribute("Max", 100)

        # Afficher ent�tes
        nom = "case_macaron_mix_couleurs"
        propriete = wxpg.BoolProperty(label=_("Fond mix de couleurs"), name=nom, value=VALEURS_DEFAUT[nom])
        propriete.SetHelpString(_("Afficher un fond avec un mix de couleurs"))
        propriete.SetAttribute("UseCheckbox", True)
        self.Append(propriete)

        # Couleur de texte
        nom = "case_macaron_texte_couleur"
        propriete = wxpg.ColourProperty(label=_("Couleur du texte"), name=nom, value=VALEURS_DEFAUT[nom])
        propriete.SetHelpString(_("S�lectionnez une couleur"))
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)

        # Taille de texte
        nom = "case_macaron_taille_police"
        propriete = wxpg.IntProperty(label=_("Taille de texte"), name=nom, value=VALEURS_DEFAUT[nom])
        propriete.SetHelpString(_("Saisissez une taille de texte"))
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)
        self.SetPropertyEditor(nom, "SpinCtrl")



        # Rubrique Case
        self.Append(wxpg.PropertyCategory(_("Case")))

        # Hauteur de la case
        nom = "case_hauteur"
        propriete = wxpg.IntProperty(label=_("Hauteur (0=automatique)"), name=nom, value=VALEURS_DEFAUT[nom])
        propriete.SetHelpString(_("Saisissez une valeur num�rique en pixels"))
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)
        self.SetPropertyEditor(nom, "SpinCtrl")

        # Valeur de l'arrondi
        nom = "case_radius"
        propriete = wxpg.IntProperty(label=_("Valeur de l'arrondi"), name=nom, value=VALEURS_DEFAUT[nom])
        propriete.SetHelpString(_("Saisissez une valeur num�rique"))
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)
        self.SetPropertyEditor(nom, "SpinCtrl")

        # Rotation
        nom = "case_rotation_aleatoire"
        propriete = wxpg.BoolProperty(label=_("Rotation al�atoire"), name=nom, value=VALEURS_DEFAUT[nom])
        propriete.SetHelpString(_("Chaque case subit une l�g�re rotation al�atoire"))
        propriete.SetAttribute("UseCheckbox", True)
        self.Append(propriete)

        # Fond et bord
        temp = [
            ("case_fond", _("fond")),
            ("case_bord", _("bord")),
        ]
        for code, label in temp:

            # Couleur
            nom = "%s_couleur" % code
            propriete = wxpg.ColourProperty(label=_("Couleur du %s") % label, name=nom, value=VALEURS_DEFAUT[nom])
            propriete.SetHelpString(_("S�lectionnez une couleur"))
            propriete.SetAttribute("obligatoire", True)
            self.Append(propriete)

            # Transparence
            nom = "%s_alpha" % code
            propriete = wxpg.IntProperty(label=_("Opacit� du %s (en %%)") % label, name=nom, value=VALEURS_DEFAUT[nom])
            propriete.SetHelpString(_("Saisissez une valeur num�rique"))
            propriete.SetAttribute("obligatoire", True)
            self.Append(propriete)
            self.SetPropertyEditor(nom, "SpinCtrl")
            propriete.SetAttribute("Min", 0)
            propriete.SetAttribute("Max", 100)

        # R�partition verticale des texte
        nom = "case_repartition_verticale"
        propriete = wxpg.BoolProperty(label=_("R�partition verticale des textes"), name=nom, value=VALEURS_DEFAUT[nom])
        propriete.SetHelpString(_("Les lignes de texte sont r�partis verticalement"))
        propriete.SetAttribute("UseCheckbox", True)
        self.Append(propriete)

        # Taille de texte
        nom = "case_taille_police"
        propriete = wxpg.IntProperty(label=_("Taille de texte"), name=nom, value=VALEURS_DEFAUT[nom])
        propriete.SetHelpString(_("Saisissez une taille de texte"))
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)
        self.SetPropertyEditor(nom, "SpinCtrl")

        # Couleur de texte
        nom = "case_texte_couleur"
        propriete = wxpg.ColourProperty(label=_("Couleur du texte"), name=nom, value=VALEURS_DEFAUT[nom])
        propriete.SetHelpString(_("S�lectionnez une couleur"))
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)

        # Marge haut
        nom = "case_marge_haut"
        propriete = wxpg.IntProperty(label=_("Marge sup�rieure"), name=nom, value=VALEURS_DEFAUT[nom])
        propriete.SetHelpString(_("Saisissez une valeur num�rique"))
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)
        self.SetPropertyEditor(nom, "SpinCtrl")

        # Espace verticale
        nom = "case_espace_vertical"
        propriete = wxpg.IntProperty(label=_("Espace vertical"), name=nom, value=VALEURS_DEFAUT[nom])
        propriete.SetHelpString(_("Saisissez une valeur num�rique"))
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)
        self.SetPropertyEditor(nom, "SpinCtrl")

        # Type de s�parateur de ligne
        nom = "case_separateur_type"
        liste_choix = [("aucun", _("Aucun")), ("image", _("Image")), ("ligne", _("Ligne"))]
        propriete = CTRL_Propertygrid.Propriete_choix(label=_("S�parateur de ligne"), name=nom, liste_choix=liste_choix, valeur=VALEURS_DEFAUT[nom])
        propriete.SetHelpString(_("S�lectionnez un type de s�parateur de ligne"))
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)

        # Image du s�parateur
        nom = "case_separateur_image"
        liste_choix = [("aucune", _("Aucune")),
                       ("Ligne_retro.png", _("R�tro")),
                       ("Ligne_bijou.png", _("Bijou")),
                       ("Ligne_branche.png", _("Branche")),
                       ("Ligne_fleurs.png", _("Fleurs")),
                       ("Ligne_moderne.png", _("Moderne")),
                       ("Ligne_ronds.png", _("Ronds")),
                       ]
        propriete = CTRL_Propertygrid.Propriete_choix(label=_("Image du s�parateur"), name=nom, liste_choix=liste_choix, valeur=VALEURS_DEFAUT[nom])
        propriete.SetHelpString(_("S�lectionnez une image pour le s�parateur"))
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)


        # Rubrique L�gende
        self.Append(wxpg.PropertyCategory(_("L�gende")))

        # Afficher l�gende
        nom = "legende_afficher"
        propriete = wxpg.BoolProperty(label=_("Afficher la l�gende"), name=nom, value=VALEURS_DEFAUT[nom])
        propriete.SetHelpString(_("Afficher la l�gende"))
        propriete.SetAttribute("UseCheckbox", True)
        self.Append(propriete)

        # Type de l�gende
        nom = "legende_type"
        liste_choix = [("numero", _("Num�ro color�")), ("carre", _("Carr� de couleur")),]
        propriete = CTRL_Propertygrid.Propriete_choix(label=_("Type de l�gende"), name=nom, liste_choix=liste_choix, valeur=VALEURS_DEFAUT[nom])
        propriete.SetHelpString(_("S�lectionnez un type de l�gende"))
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)

        # Hauteur
        nom = "legende_hauteur"
        propriete = wxpg.IntProperty(label=_("Hauteur"), name=nom, value=VALEURS_DEFAUT[nom])
        propriete.SetHelpString(_("Saisissez une valeur num�rique"))
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)
        self.SetPropertyEditor(nom, "SpinCtrl")

        # Fond et bord
        temp = [
            ("legende_fond", _("fond")),
            ("legende_bord", _("bord")),
        ]
        for code, label in temp:

            # Couleur
            nom = "%s_couleur" % code
            propriete = wxpg.ColourProperty(label=_("Couleur du %s") % label, name=nom, value=VALEURS_DEFAUT[nom])
            propriete.SetHelpString(_("S�lectionnez une couleur"))
            propriete.SetAttribute("obligatoire", True)
            self.Append(propriete)

            # Transparence
            nom = "%s_alpha" % code
            propriete = wxpg.IntProperty(label=_("Opacit� du %s (en %%)") % label, name=nom, value=VALEURS_DEFAUT[nom])
            propriete.SetHelpString(_("Saisissez une valeur num�rique"))
            propriete.SetAttribute("obligatoire", True)
            self.Append(propriete)
            self.SetPropertyEditor(nom, "SpinCtrl")
            propriete.SetAttribute("Min", 0)
            propriete.SetAttribute("Max", 100)

        # Valeur de l'arrondi
        nom = "legende_radius"
        propriete = wxpg.IntProperty(label=_("Valeur de l'arrondi"), name=nom, value=VALEURS_DEFAUT[nom])
        propriete.SetHelpString(_("Saisissez une valeur num�rique"))
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)
        self.SetPropertyEditor(nom, "SpinCtrl")

        # Couleur de texte
        nom = "legende_texte_couleur"
        propriete = wxpg.ColourProperty(label=_("Couleur du texte"), name=nom, value=VALEURS_DEFAUT[nom])
        propriete.SetHelpString(_("S�lectionnez une couleur"))
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)

        # Taille de texte
        nom = "legende_taille_police"
        propriete = wxpg.IntProperty(label=_("Taille de texte"), name=nom, value=VALEURS_DEFAUT[nom])
        propriete.SetHelpString(_("Saisissez une taille de texte"))
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)
        self.SetPropertyEditor(nom, "SpinCtrl")


        # Rubrique Pied de page
        self.Append(wxpg.PropertyCategory(_("Pied de page")))

        # Afficher pied
        nom = "pied_afficher"
        propriete = wxpg.BoolProperty(label=_("Afficher le pied de page"), name=nom, value=VALEURS_DEFAUT[nom])
        propriete.SetHelpString(_("Afficher le pied de page"))
        propriete.SetAttribute("UseCheckbox", True)
        self.Append(propriete)

        # Hauteur
        nom = "pied_hauteur"
        propriete = wxpg.IntProperty(label=_("Hauteur"), name=nom, value=VALEURS_DEFAUT[nom])
        propriete.SetHelpString(_("Saisissez une valeur num�rique"))
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)
        self.SetPropertyEditor(nom, "SpinCtrl")

        # Fond et bord
        temp = [
            ("pied_fond", _("fond")),
            ("pied_bord", _("bord")),
        ]
        for code, label in temp:

            # Couleur
            nom = "%s_couleur" % code
            propriete = wxpg.ColourProperty(label=_("Couleur du %s") % label, name=nom, value=VALEURS_DEFAUT[nom])
            propriete.SetHelpString(_("S�lectionnez une couleur"))
            propriete.SetAttribute("obligatoire", True)
            self.Append(propriete)

            # Transparence
            nom = "%s_alpha" % code
            propriete = wxpg.IntProperty(label=_("Opacit� du %s (en %%)") % label, name=nom, value=VALEURS_DEFAUT[nom])
            propriete.SetHelpString(_("Saisissez une valeur num�rique"))
            propriete.SetAttribute("obligatoire", True)
            self.Append(propriete)
            self.SetPropertyEditor(nom, "SpinCtrl")
            propriete.SetAttribute("Min", 0)
            propriete.SetAttribute("Max", 100)

        # Valeur de l'arrondi
        nom = "pied_radius"
        propriete = wxpg.IntProperty(label=_("Valeur de l'arrondi"), name=nom, value=VALEURS_DEFAUT[nom])
        propriete.SetHelpString(_("Saisissez une valeur num�rique"))
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)
        self.SetPropertyEditor(nom, "SpinCtrl")

        # Couleur de texte
        nom = "pied_texte_couleur"
        propriete = wxpg.ColourProperty(label=_("Couleur du texte"), name=nom, value=VALEURS_DEFAUT[nom])
        propriete.SetHelpString(_("S�lectionnez une couleur"))
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)

        # Taille de texte
        nom = "pied_taille_police"
        propriete = wxpg.IntProperty(label=_("Taille de texte"), name=nom, value=VALEURS_DEFAUT[nom])
        propriete.SetHelpString(_("Saisissez une taille de texte"))
        propriete.SetAttribute("obligatoire", True)
        self.Append(propriete)
        self.SetPropertyEditor(nom, "SpinCtrl")



    def Validation(self):
        """ Validation des donn�es saisies """
        for nom, valeur in self.GetPropertyValues().items() :
            propriete = self.GetPropertyByName(nom)
            if self.GetPropertyAttribute(propriete, "obligatoire") == True :
                if valeur == "" or valeur == None :
                    dlg = wx.MessageDialog(self, _("Vous devez obligatoirement renseigner le param�tre '%s' !") % nom, _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
                    dlg.ShowModal()
                    dlg.Destroy()
                    return False
        return True
        
    def Importation(self):
        """ Importation des valeurs dans le contr�le """
        # R�cup�ration des noms et valeurs par d�faut du contr�le
        dictValeurs = copy.deepcopy(self.GetPropertyValues())
        # Recherche les param�tres m�moris�s
        dictParametres = UTILS_Parametres.ParametresCategorie(mode="get", categorie=self.categorie, dictParametres=dictValeurs)
        # Envoie les param�tres dans le contr�le
        for nom, valeur in dictParametres.items() :
            propriete = self.GetPropertyByName(nom)
            ancienneValeur = propriete.GetValue() 
            propriete.SetValue(valeur)
    
    def Sauvegarde(self, forcer=False):
        """ M�morisation des valeurs du contr�le """
        dictValeurs = copy.deepcopy(self.GetPropertyValues())
        UTILS_Parametres.ParametresCategorie(mode="set", categorie=self.categorie, dictParametres=dictValeurs)
        
    def GetValeurs(self) :
        return self.GetPropertyValues()

    def SetValeurs(self, dictDonnees={}):
        for nom, valeur in dictDonnees.items() :
            propriete = self.GetPropertyByName(nom)
            if propriete != None :
                propriete.SetValue(valeur)


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

class Track_modele(CTRL_Vignettes_documents.Track):
    def __init__(self, parent, buffer=None, type=None, label=None, description="", donnees={}):
        CTRL_Vignettes_documents.Track.__init__(self, parent, buffer=buffer, type=type, label=label)
        self.description = description
        self.donnees = donnees

    def GetInfobulle(self):
        texte = _("%s\n%s\n\nDouble-cliquez pour appliquer ce mod�le") % (self.label.upper(), self.description)
        return texte




class CTRL_Modeles(CTRL_Vignettes_documents.CTRL):
    def __init__(self, parent):
        CTRL_Vignettes_documents.CTRL.__init__(self, parent, type_donnee=None, tailleVignette=256,style=wx.BORDER_SUNKEN, afficheLabels=True)
        self.parent = parent
        self.ImportationModeles()
        self.SetMinSize((330, -1))
        self.SetPopupMenu(None)

    def OnDoubleClick(self, event):
        index = self.GetSelection()
        dictDonnees = self.GetItem(index).track.donnees
        self.parent.SetModele(dictDonnees)

    def ChargeImage(self, fichier):
        """Read a file into PIL Image object. Return the image and file size"""
        buf = six.BytesIO()
        f = open(fichier, "rb")
        while 1:
            rdbuf = f.read(8192)
            if not rdbuf: break
            buf.write(rdbuf)
        f.close()
        buf.seek(0)
        image = Image.open(buf).convert("RGB")
        return image, len(buf.getvalue())

    def ImportationModeles(self):
        for dictModele in LISTE_MODELES:
            nomFichier = dictModele["fichier"].capitalize()
            cheminFichier = Chemins.GetStaticPath("Images/Menus/%s" % nomFichier)
            imgPIL, poidsImg = self.ChargeImage(cheminFichier)
            blob = self.GetBufferImage(imgPIL)

            # Conserve l'image en m�moire
            track = Track_modele(self, buffer=blob, type=nomFichier[-3:], label=dictModele["label"],
                                 description=dictModele["description"], donnees=dictModele["donnees"])
            self.listePages.append(track)

        # MAJ de l'affichage
        self.MAJ()


    # ----------------------------------------------------------------------------------------------------------------------------

class CTRL(wx.Panel):
    def __init__(self, parent, periode=(None, None)):
        wx.Panel.__init__(self, parent, id=-1, style=wx.TAB_TRAVERSAL)
        self.parent = parent

        # P�riode
        self.staticbox_periode_staticbox = wx.StaticBox(self, -1, _("P�riode � afficher"))
        self.label_date_debut = wx.StaticText(self, -1, "Du")
        self.ctrl_date_debut = CTRL_Saisie_date.Date2(self)
        self.label_date_fin = wx.StaticText(self, -1, _("Au"))
        self.ctrl_date_fin = CTRL_Saisie_date.Date2(self)

        self.ctrl_date_debut.SetToolTip(wx.ToolTip(_("Saisissez la date de d�but de p�riode")))
        self.ctrl_date_fin.SetToolTip(wx.ToolTip(_("Saisissez la date de fin de p�riode")))

        # Param�tres g�n�raux
        self.box_options_staticbox = wx.StaticBox(self, -1, _("Options d'impression"))
        self.ctrl_parametres = CTRL_Parametres(self, categorie="impression_menu")
        self.ctrl_parametres.Importation()
        self.bouton_reinitialisation = CTRL_Propertygrid.Bouton_reinitialisation(self, self.ctrl_parametres)
        self.bouton_sauvegarde = CTRL_Propertygrid.Bouton_sauvegarde(self, self.ctrl_parametres)
        self.ctrl_parametres.SetMinSize((50, 50)) 

        # Mod�les
        self.box_modeles_staticbox = wx.StaticBox(self, -1, _("Mod�les pr�d�finis"))
        self.ctrl_modeles = CTRL_Modeles(self)

        self.__do_layout()

        # Init
        self.ctrl_date_debut.SetDate(periode[0])
        self.ctrl_date_fin.SetDate(periode[1])
        
    def __do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(rows=1, cols=2, vgap=10, hgap=10)

        grid_sizer_gauche = wx.FlexGridSizer(rows=2, cols=1, vgap=5, hgap=5)

        # P�riode de r�f�rence
        staticbox_periode = wx.StaticBoxSizer(self.staticbox_periode_staticbox, wx.VERTICAL)
        grid_sizer_periode = wx.FlexGridSizer(rows=2, cols=5, vgap=5, hgap=5)
        grid_sizer_periode.Add(self.label_date_debut, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_periode.Add(self.ctrl_date_debut, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_periode.Add(self.label_date_fin, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_periode.Add(self.ctrl_date_fin, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        staticbox_periode.Add(grid_sizer_periode, 1, wx.ALL|wx.EXPAND, 10)
        grid_sizer_gauche.Add(staticbox_periode, 1, wx.RIGHT|wx.EXPAND, 0)

        # Param�tres g�n�raux
        box_options = wx.StaticBoxSizer(self.box_options_staticbox, wx.VERTICAL)
        grid_sizer_parametres = wx.FlexGridSizer(rows=1, cols=2, vgap=5, hgap=5)
        grid_sizer_parametres.Add(self.ctrl_parametres, 1, wx.EXPAND, 0)

        grid_sizer_boutons = wx.FlexGridSizer(rows=3, cols=1, vgap=5, hgap=5)
        grid_sizer_boutons.Add(self.bouton_reinitialisation, 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_sauvegarde, 0, 0, 0)

        grid_sizer_parametres.Add(grid_sizer_boutons, 0, 0, 0)
        grid_sizer_parametres.AddGrowableRow(0)
        grid_sizer_parametres.AddGrowableCol(0)
        box_options.Add(grid_sizer_parametres, 1, wx.EXPAND|wx.ALL, 10)
        grid_sizer_gauche.Add(box_options, 1, wx.EXPAND, 0)

        grid_sizer_gauche.AddGrowableRow(1)
        grid_sizer_gauche.AddGrowableCol(0)
        grid_sizer_base.Add(grid_sizer_gauche, 1, wx.EXPAND, 0)

        # Mod�les
        box_modeles = wx.StaticBoxSizer(self.box_modeles_staticbox, wx.VERTICAL)
        box_modeles.Add(self.ctrl_modeles, 1, wx.EXPAND|wx.ALL, 10)
        grid_sizer_base.Add(box_modeles, 1, wx.EXPAND, 0)

        grid_sizer_base.AddGrowableRow(0)
        grid_sizer_base.AddGrowableCol(0)

        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)
            
    def MemoriserParametres(self):
        self.ctrl_parametres.Sauvegarde() 
            
    def GetOptions(self):
        dictOptions = copy.copy(VALEURS_DEFAUT)
        
        # R�cup�ration des param�tres
        if self.ctrl_parametres.Validation() == False :
            return False
        for nom, valeur in self.ctrl_parametres.GetValeurs().items()  :
            dictOptions[nom] = valeur

        # R�cup�ration de la p�riode
        date_debut = self.ctrl_date_debut.GetDate()
        if self.ctrl_date_debut.FonctionValiderDate() == False or date_debut == None:
            dlg = wx.MessageDialog(self, _("La date de d�but de p�riode ne semble pas valide !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            self.ctrl_date_debut.SetFocus()
            return False
        dictOptions["date_debut"] = date_debut

        date_fin = self.ctrl_date_fin.GetDate()
        if self.ctrl_date_fin.FonctionValiderDate() == False or date_fin == None:
            dlg = wx.MessageDialog(self, _("La date de fin de p�riode ne semble pas valide !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            self.ctrl_date_fin.SetFocus()
            return False
        dictOptions["date_fin"] = date_fin

        return dictOptions

    def SetModele(self, dictDonnees={}):
        self.ctrl_parametres.SetValeurs(VALEURS_DEFAUT)
        self.ctrl_parametres.SetValeurs(dictDonnees)



# -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

class Dialog(wx.Dialog):
    def __init__(self, parent, periode=(None, None), IDrestaurateur=None):
        wx.Dialog.__init__(self, parent, -1, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX)
        self.parent = parent
        if IDrestaurateur == None :
            IDrestaurateur = 0
        self.IDrestaurateur = IDrestaurateur

        # Bandeau
        titre = _("Options d'impression")
        intro = _("Vous pouvez ici modifier les param�tres d'impression du document. Double-cliquez sur un mod�le pr�d�fini, ajustez �ventuellement les param�tres souhait�s puis cliquez sur le bouton 'M�moriser les param�tres' (Image disquette) pour m�moriser votre mod�le pour les impressions suivantes.")
        self.SetTitle(titre)
        self.ctrl_bandeau = CTRL_Bandeau.Bandeau(self, titre=titre, texte=intro, hauteurHtml=30, nomImage="Images/32x32/Imprimante.png")

        # Param�tres
        self.ctrl_parametres = CTRL(self, periode=periode)

        # Boutons
        self.bouton_aide = CTRL_Bouton_image.CTRL(self, texte=_("Aide"), cheminImage="Images/32x32/Aide.png")
        self.bouton_ok = CTRL_Bouton_image.CTRL(self, texte=_("Aper�u"), cheminImage="Images/32x32/Apercu.png")
        self.bouton_annuler = CTRL_Bouton_image.CTRL(self, texte=_("Fermer"), cheminImage="Images/32x32/Annuler.png")

        self.__set_properties()
        self.__do_layout()
        
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAide, self.bouton_aide)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonOk, self.bouton_ok)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAnnuler, self.bouton_annuler)
        
        self.bouton_ok.SetFocus() 

    def __set_properties(self):
        self.bouton_ok.SetToolTip(wx.ToolTip(_("Cliquez ici pour valider")))
        self.bouton_aide.SetToolTip(wx.ToolTip(_("Cliquez ici pour obtenir de l'aide")))
        self.bouton_annuler.SetToolTip(wx.ToolTip(_("Cliquez ici pour annuler")))
        self.SetMinSize((870, 600))

    def __do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(rows=3, cols=1, vgap=10, hgap=10)
        grid_sizer_base.Add(self.ctrl_bandeau, 0, wx.EXPAND, 0)

        grid_sizer_base.Add(self.ctrl_parametres, 0, wx.EXPAND|wx.LEFT|wx.RIGHT, 10)

        # Boutons
        grid_sizer_boutons = wx.FlexGridSizer(rows=1, cols=4, vgap=10, hgap=10)
        grid_sizer_boutons.Add(self.bouton_aide, 0, 0, 0)
        grid_sizer_boutons.Add((20, 20), 0, wx.EXPAND, 0)
        grid_sizer_boutons.Add(self.bouton_ok, 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_annuler, 0, 0, 0)
        grid_sizer_boutons.AddGrowableCol(1)
        grid_sizer_base.Add(grid_sizer_boutons, 1, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 10)
        
        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)
        grid_sizer_base.AddGrowableRow(1)
        grid_sizer_base.AddGrowableCol(0)
        self.Layout()
        self.CenterOnScreen() 

    def OnBoutonAide(self, event):
        # Envoie les modification  dans le clipboard
        texte = six.text_type(self.GetProfilOptions())
        clipdata = wx.TextDataObject()
        clipdata.SetText(texte)
        wx.TheClipboard.Open()
        wx.TheClipboard.SetData(clipdata)
        wx.TheClipboard.Close()

        # Aide
        from Utils import UTILS_Aide
        UTILS_Aide.Aide("Menusdesrepas")

    def GetProfilOptions(self):
        dictModifications = {}
        dictDonnees = self.ctrl_parametres.GetOptions()
        for code, valeur in VALEURS_DEFAUT.items() :
            if code in dictDonnees:
                if dictDonnees[code] != valeur :
                    dictModifications[code] = dictDonnees[code]
        return dictModifications

    def OnBoutonAnnuler(self, event): 
        self.EndModal(wx.ID_CANCEL)        
        
    def GetOptions(self):
        return self.ctrl_parametres.GetOptions() 

    def OnBoutonOk(self, event):
        # R�cup�ration des options
        dictDonnees = self.ctrl_parametres.GetOptions()
        if dictDonnees == False :
            return

        # Compl�te le dictOptions
        dictDonnees["IDrestaurateur"] = self.IDrestaurateur

        # Affiche le PDF
        from Utils import UTILS_Impression_menu
        UTILS_Impression_menu.Impression(dictDonnees=dictDonnees)

        # Ferme la DLG
        #self.EndModal(wx.ID_OK)



if __name__ == "__main__":
    app = wx.App(0)
    dlg = Dialog(None)
    app.SetTopWindow(dlg)
    dlg.ShowModal()
    app.MainLoop()
