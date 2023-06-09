#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#-----------------------------------------------------------
# Application :    Noethys, Matthania ajout des tables spécifiques
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS, JB, Jacques Brunel
# Copyright:       (c) 2010-11 Ivan LUCAS, JB
# Licence:         Licence GNU GPL
#-----------------------------------------------------------

TABLES_IMPORTATION_OPTIONNELLES = [
        ["Périodes de vacances, scolarité", ("vacances","scolarite","classes",), True],
        ["Jours fériés", ("jours_feries",), True],
        ["Vaccins et maladies", ("types_vaccins", "vaccins_maladies", "types_maladies","categories_medicales",), True],
        ["Types de sieste", ("types_sieste",), True],
        ["Catégories socio-professionnelles", ("categories_travail",), True],
        ["Niveaux scolaires", ("niveaux_scolaires",), True],
        ["Types de quotients", ("types_quotients",), True],
        ["Eléments de pages du portail", ("portail_elements",), True],
        ['Aides sociales', ('aides_beneficiaires','aides_combi_unites','aides_combinaisons','aides_montants','deductions',), True],
        ['Badges', ('badgeage_actions','badgeage_archives','badgeage_journal','badgeage_messages','badgeage_procedures',), True],
        ['Budgets', ('compta_budgets','compta_categories_budget','compta_operations_budgetaires',), True],
        ['Contrats Noethys', ('contrats','contrats_tarifs','corrections_phoniques',), True],
        ['Cotisations Noethys', ('cotisations_activites','depots_cotisations',), True],
        ['Etats nominatifs', ('etat_nomin_champs','etat_nomin_profils','etat_nomin_selections',), True],
        ['Portail', ('portail_actions','portail_blocs','portail_messages',
                     'portail_pages','portail_periodes','portail_renseignements',
                     'portail_reservations','portail_reservations_locations','portail_unites',), True],
        ['Tarifs Noethys', ('combi_tarifs','combi_tarifs_unites',), True],
        ] # [Nom Categorie, (liste des tables...,), Selectionné]

# ----------------------------------------------------------------------------------------

DB_DATA = {

    "individus":[
                ("IDindividu", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID de la personne"),
                ("IDcivilite", "INTEGER", "Civilité de la personne"),
                ("nom", "VARCHAR(100)", "Nom de famille de la personne"),
                ("nom_jfille", "VARCHAR(100)", "Nom de jeune fille de la personne"),
                ("prenom", "VARCHAR(100)", "Prénom de la personne"),
                ("num_secu", "VARCHAR(21)", "Numéro de sécurité sociale de la personne"),
                ("IDnationalite", "INTEGER", "Nationalité de la personne"),
                ("date_naiss", "DATE", "Date de naissance de la personne"),
                ("IDpays_naiss", "INTEGER", "ID du Pays de naissance de la personne"),
                ("cp_naiss", "VARCHAR(10)", "Code postal du lieu de naissance de la personne"),
                ("ville_naiss", "VARCHAR(100)", "Ville du lieu de naissance de la personne"),
                ("deces", "INTEGER", "Est décédé (0/1)"),
                ("annee_deces", "INTEGER", "Année de décès"),

                ("adresse_auto", "INTEGER", "IDindividu dont l'adresse est à reporter"),
                ("rue_resid", "VARCHAR(255)", "Adresse de la personne"),
                ("cp_resid", "VARCHAR(10)", "Code postal de la personne"),
                ("ville_resid", "VARCHAR(100)", "Ville de la personne"),
                ("IDsecteur", "INTEGER", "pays postal"),

                ("IDcategorie_travail", "INTEGER", "IDcategorie socio-professionnelle"),
                ("profession", "VARCHAR(100)", "Profession de la personne"),
                ("employeur", "VARCHAR(100)", "Employeur de la personne"),
                ("travail_tel", "VARCHAR(50)", "Tel travail de la personne"),
                ("travail_fax", "VARCHAR(50)", "obsolète n'est plus géré"),
                ("travail_mail", "VARCHAR(50)", "Email travail de la personne"),

                ("tel_domicile", "VARCHAR(50)", "Tel domicile de la personne"),
                ("tel_mobile", "VARCHAR(50)", "Tel mobile perso de la personne"),
                ("tel_fax", "VARCHAR(50)", "Fax perso de la personne"),
                ("mail", "VARCHAR(200)", "Email perso de la personne"),

                ("travail_tel_sms", "INTEGER", "SMS autorisé (0/1)"),
                ("tel_domicile_sms", "INTEGER", "SMS autorisé (0/1)"),
                ("tel_mobile_sms", "INTEGER", "SMS autorisé (0/1)"),
        
                ("IDmedecin", "INTEGER", "ID du médecin traitant de l'individu"),
                ("memo", "VARCHAR(2000)", "Mémo concernant l'individu"),
                ("IDtype_sieste", "INTEGER", "Type de sieste"),
        
                ("date_creation", "DATE", "Date de création de la fiche individu"),
                ("etat", "VARCHAR(50)", "Etat"),
                ("refus_pub", "INTEGER", "Refus de publicités papier"),
                ("refus_mel", "INTEGER", "Refus de publicités demat"),
                ("adresse_normee", "INTEGER", "1 normalisation automatique, 2 validée éprouvée, 3 saisie forcée"),
            ], # Les individus

    "exadresses": [
                ("IDindividu", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID de la personne"),
                ("rue_resid", "VARCHAR(255)", "Adresse de la personne"),
                ("cp_resid", "VARCHAR(10)", "Code postal de la personne"),
                ("ville_resid", "VARCHAR(100)", "Ville de la personne"),
                ("adresse_normee", "INTEGER", "1 normalisation automatique, 2 validée éprouvée"),
                ("date_modification", "DATE", "Date de modification de la fiche"),
            ],  # anciennes adresses

    "liens":[
                ("IDlien", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID du lien"),
                ("IDfamille", "INTEGER", "IDfamille"),
                ("IDindividu_sujet", "INTEGER", "IDindividu sujet du lien"),
                ("IDtype_lien", "INTEGER", "IDtype_lien"),
                ("IDindividu_objet", "INTEGER", "IDindividu objet du lien"),
                ("responsable", "INTEGER", "=1 si l'individu SUJET est responsable de l'individu objet"),
                ("IDautorisation", "INTEGER", "ID autorisation"),
                ], # Les liens entre les individus

    "familles":[    ("IDfamille", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID de la famille"),
                ("date_creation", "DATE", "Date de création de la fiche famille"),
                ("IDcompte_payeur", "INTEGER", "ID du compte payeur"),
                ("IDcaisse", "INTEGER", "ID de la caisse d'allocation"),
                ("num_allocataire", "VARCHAR(100)", "Numéro d'allocataire"),
                ("allocataire", "INTEGER", "ID de l'individu allocataire principal"),
                ("internet_actif", "INTEGER", "(0/1) Compte internet actif"),
                ("internet_identifiant", "VARCHAR(300)", "Code identifiant internet"),
                ("internet_mdp", "VARCHAR(300)", "Mot de passe internet"),
                ("memo", "VARCHAR(2000)", "Mémo concernant la famille"),
                ("prelevement_activation", "INTEGER", "Activation du prélèvement"),
                ("prelevement_etab", "VARCHAR(50)", "Prélèvement - Code étab"),
                ("prelevement_guichet", "VARCHAR(50)", "Prélèvement - Code guichet"),
                ("prelevement_numero", "VARCHAR(50)", "Prélèvement - Numéro de compte"),
                ("prelevement_cle", "VARCHAR(50)", "Prélèvement - Code clé"),
                ("prelevement_banque", "INTEGER", "Prélèvement - ID de la Banque"),
                ("prelevement_individu", "INTEGER", "Prélèvement - ID Individu"),
                ("prelevement_nom", "VARCHAR(200)", "Prélèvement - nom titulaire"),
                ("prelevement_rue", "VARCHAR(400)", "Prélèvement - rue titulaire"),
                ("prelevement_cp", "VARCHAR(50)", "Prélèvement - cp titulaire"),
                ("prelevement_ville", "VARCHAR(400)", "Prélèvement - ville titulaire"),
                ("prelevement_cle_iban", "VARCHAR(10)", "Prélèvement - Clé IBAN"),
                ("prelevement_iban", "VARCHAR(100)", "Prélèvement - Clé IBAN"),
                ("prelevement_bic", "VARCHAR(100)", "Prélèvement - BIC"),
                ("prelevement_reference_mandat", "VARCHAR(300)", "Prélèvement - Référence mandat"),
                ("prelevement_date_mandat", "DATE", "Prélèvement - Date mandat"),
                ("prelevement_memo", "VARCHAR(450)", "Prélèvement - Mémo"),
                ("email_factures", "VARCHAR(450)", "Adresse Email pour envoi des factures"),
                ("email_recus", "VARCHAR(450)", "Adresse Email pour envoi des reçus de règlements"),
                ("email_depots", "VARCHAR(450)", "Adresse Email pour avis d'encaissement des règlements"),
                ("titulaire_helios", "INTEGER", "IDindividu du titulaire Hélios"),
                ("code_comptable", "VARCHAR(450)", "Code comptable pour facturation et export logiciels compta"),
                ("idtiers_helios", "VARCHAR(300)", "IDtiers pour Hélios"),
                ("natidtiers_helios", "INTEGER", "Nature IDtiers pour Hélios"),
                ("reftiers_helios", "VARCHAR(300)", "Référence locale du tiers pour Hélios"),
                ("cattiers_helios", "INTEGER", "Catégorie de tiers pour Hélios"),
                ("natjur_helios", "INTEGER", "Nature juridique du tiers pour Hélios"),
                ("autorisation_cafpro", "INTEGER", "Autorisation de consultation CAFPRO (0/1)"),
                ("autre_adresse_facturation", "VARCHAR(450)", "Autre adresse de facturation"),
                ("etat", "VARCHAR(50)", "Etat"),

                ("refus_pub", "INTEGER", "Refus de publicités papier"),
                ("refus_mel", "INTEGER", "Refus de publicités demat"),
                ("adresse_intitule", "VARCHAR(40)", "libellé de la famille pour les adresses"),
                ("adresse_individu", "INTEGER", "Individu dont l'adresse est celle de la famille"),
                ("aides_vacances", "TINYINT", "famille bénéficiaire d'aides par le passé"),
                ], # Les familles
    
    "rattachements":[
                ("IDrattachement", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID rattachement"),
                ("IDindividu", "INTEGER", "IDindividu sujet du rattachement"),
                ("IDfamille", "INTEGER", "IDfamille objet du rattachement"),
                ("IDcategorie", "INTEGER", "IDcategorie du rattachement (responsable|enfant|contact)"),
                ("titulaire", "INTEGER", "=1 si individu est titulaire de la fiche famille"),
                ], # Les rattachements à une ou plusieurs familles
            
    "types_maladies":[     ("IDtype_maladie", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID type_maladie"),
                ("nom", "VARCHAR(100)", "Nom de la maladie"),
                ("vaccin_obligatoire", "INTEGER", "=1 si vaccin obligatoire"),
                ], # Types de maladies
            
    "types_vaccins":[       ("IDtype_vaccin", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID type_vaccin"),
                ("nom", "VARCHAR(100)", "Nom du vaccin"),
                ("duree_validite", "VARCHAR(50)", "Durée de validité"),
                ], # Les types de vaccins
            
    "vaccins_maladies":[  ("IDvaccins_maladies", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID vaccins_maladies"),
                ("IDtype_vaccin", "INTEGER", "IDtype_vaccin"),
                ("IDtype_maladie", "INTEGER", "IDtype_maladie"),
                ], # Liens entre les vaccins et les maladies concernées
            
    "medecins":[              ("IDmedecin", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID du médecin"),
                ("nom", "VARCHAR(100)", "Nom de famille du médecin"),
                ("prenom", "VARCHAR(100)", "Prénom du médecin"),
                ("rue_resid", "VARCHAR(255)", "Adresse du médecin"),
                ("cp_resid", "VARCHAR(10)", "Code postal du médecin"),
                ("ville_resid", "VARCHAR(100)", "Ville du médecin"),  
                ("tel_cabinet", "VARCHAR(50)", "Tel du cabinet du médecin"),  
                ("tel_mobile", "VARCHAR(50)", "Tel du mobile du médecin"),  
                ], # Les médecins
            
    "vaccins":[                 ("IDvaccin", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID du vaccin"),
                ("IDindividu", "INTEGER", "ID de l'individu concerné"),
                ("IDtype_vaccin", "INTEGER", "ID du vaccin concerné"),
                ("date", "DATE", "date du vaccin"),
                ], # Les vaccins des individus    
            
    "problemes_sante":[   ("IDprobleme", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID du probleme de santé"),
                ("IDindividu", "INTEGER", "ID de l'individu"),
                ("IDtype", "INTEGER", "ID du type de problème"),
                ("intitule", "VARCHAR(100)", "Intitulé du problème"),
                ("date_debut", "DATE", "Date de début du problème"),
                ("date_fin", "DATE", "Date de fin du problème"),
                ("description", "VARCHAR(2000)", "Description du problème"),
                ("traitement_medical", "INTEGER", "Traitement médical (1/0)"),
                ("description_traitement", "VARCHAR(2000)", "Description du traitement médical"),
                ("date_debut_traitement", "DATE", "Date de début du traitement"),
                ("date_fin_traitement", "DATE", "Date de fin du traitement"),
                ("eviction", "INTEGER", "Eviction (1/0)"),
                ("date_debut_eviction", "DATE", "Date de début de l'éviction"),
                ("date_fin_eviction", "DATE", "Date de fin de l'éviction"),
                ("diffusion_listing_enfants", "INTEGER", "Diffusion listing enfants (1/0)"),
                ("diffusion_listing_conso", "INTEGER", "Diffusion listing consommations (1/0)"),
                ("diffusion_listing_repas", "INTEGER", "Diffusion commande des repas (1/0)"),
                ], # Les problèmes de santé des individus  
            
    "vacances":[              ("IDvacance", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID periode vacances"),
                ("nom", "VARCHAR(100)", "Nom de la période de vacances"),
                ("annee", "INTEGER", "Année de la période de vacances"),
                ("date_debut", "DATE", "Date de début"),
                ("date_fin", "DATE", "Date de fin"),
                ], # Calendrier des jours de vacances
            
    "jours_feries":[           ("IDferie", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID jour férié"),
                ("type", "VARCHAR(10)", "Type de jour férié : fixe ou variable"),
                ("nom", "VARCHAR(100)", "Nom du jour férié"),
                ("jour", "INTEGER", "Jour de la DATE"),
                ("mois", "INTEGER", "Mois de la DATE"),
                ("annee", "INTEGER", "Année de la DATE"),
                ], # Calendrier des jours fériés variables et fixes
            
    "categories_travail":[   ("IDcategorie", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID catégorie socio-professionnelle"),
                ("nom", "VARCHAR(100)", "Nom de la catégorie"),
                ], # Catégories socio-professionnelles des individus
            
    "types_pieces":[        ("IDtype_piece", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID type pièce"),
                ("nom", "VARCHAR(100)", "Nom de la pièce"),
                ("public", "VARCHAR(12)", "Public (individu ou famille)"),
                ("duree_validite", "VARCHAR(50)", "Durée de validité"),
                ("valide_rattachement", "INTEGER", "(0|1) Valide même si individu rattaché à une autre famille"),
                ], # Types de pièces
            
    "pieces":[                  ("IDpiece", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID Pièce"),
                ("IDtype_piece", "INTEGER", "IDtype_piece"),
                ("IDindividu", "INTEGER", "IDindividu"),
                ("IDfamille", "INTEGER", "IDfamille"),
                ("date_debut", "DATE", "Date de début"),
                ("date_fin", "DATE", "Date de fin"),
                ("titre", "VARCHAR(200)", "Titre de la pièce"),
                ], # Pièces rattachées aux individus ou familles
            
    "organisateur":[          ("IDorganisateur", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID Organisateur"),
                ("nom", "VARCHAR(200)", "Nom de l'organisateur"),
                ("rue", "VARCHAR(200)", "Adresse"),
                ("cp", "VARCHAR(10)", "Code postal"),
                ("ville", "VARCHAR(100)", "Ville"),  
                ("tel", "VARCHAR(50)", "Tel travail"),  
                ("fax", "VARCHAR(50)", "Fax travail"),  
                ("mail", "VARCHAR(100)", "Email organisateur"),  
                ("site", "VARCHAR(100)", "Adresse site internet"),  
                ("num_agrement", "VARCHAR(100)", "Numéro d'agrément"),  
                ("num_siret", "VARCHAR(100)", "Numéro SIRET"),  
                ("code_ape", "VARCHAR(100)", "Code APE"),
                ("logo", "BLOB", "Logo de l'organisateur en binaire"),
                ("gps", "VARCHAR(200)", "Coordonnées GPS au format 'lat;long' "),
                ], # Organisateur
            
    "responsables_activite":[("IDresponsable", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID Responsable"),
                ("IDactivite", "INTEGER", "ID de l'activité concernée"),
                ("sexe", "VARCHAR(10)", "Sexe de l'individu (H/F)"),
                ("nom", "VARCHAR(200)", "Nom du responsable"),
                ("fonction", "VARCHAR(200)", "Fonction"),
                ("defaut", "INTEGER", "(0/1) Responsable sélectionné par défaut"),
                ("logo_update", "VARCHAR(50)", "Horodatage de la dernière modification du logo"),
                ], # Responsables de l'activité
            
    "activites":[("IDactivite", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID Activité"),
                ("nom", "VARCHAR(200)", "Nom complet de l'activité"),
                ("abrege", "VARCHAR(50)", "Nom abrégé de l'activité"),
                ("coords_org", "INTEGER", "(0/1) Coordonnées identiques à l'organisateur"),
                ("rue", "VARCHAR(200)", "Adresse"),
                ("cp", "VARCHAR(10)", "Code postal"),
                ("ville", "VARCHAR(100)", "Ville"),  
                ("tel", "VARCHAR(50)", "Tel travail"),  
                ("fax", "VARCHAR(50)", "Fax travail"),  
                ("mail", "VARCHAR(100)", "Email"),  
                ("site", "VARCHAR(100)", "Adresse site internet"),
                ("logo_org", "INTEGER", "(0/1) Logo identique à l'organisateur"),
                ("logo", "LONGBLOB", "Logo de l'activité en binaire"),
                ("date_debut", "DATE", "Date de début de validité"),
                ("date_fin", "DATE", "Date de fin de validité"),
                ("public", "VARCHAR(20)", "Liste du public"),
                ("vaccins_obligatoires", "INTEGER", "(0/1) Vaccins obligatoires pour l'individu inscrit"),
                ("date_creation", "DATE", "Date de création de l'activité"),
                ("nbre_inscrits_max", "INTEGER", "Nombre d'inscrits max"),
                ("code_comptable", "VARCHAR(10)", "Code analytique à ajouter au compte lors d'export logiciels compta"),
                ("psu_activation", "INTEGER", "Mode PSU : Activation"),
                ("psu_unite_prevision", "INTEGER", "Mode PSU : IDunite prévision"),
                ("psu_unite_presence", "INTEGER", "Mode PSU : IDunite présence"),
                ("psu_tarif_forfait", "INTEGER", "Mode PSU : IDtarif forfait-crédit"),
                ("psu_etiquette_rtt", "INTEGER", "Mode PSU : IDetiquette Absences RTT"),
                ("portail_inscriptions_affichage", "INTEGER", "Inscriptions autorisées sur le portail (0/1)"),
                ("portail_inscriptions_date_debut", "DATETIME", "Inscriptions autorisées - début d'affichage"),
                ("portail_inscriptions_date_fin", "DATETIME", "Inscriptions autorisées - fin d'affichage"),
                ("portail_reservations_affichage", "INTEGER", "Réservations autorisées sur le portail (0/1)"),
                ("portail_reservations_limite", "VARCHAR(100)", "Date limite de modification d'une réservation"),
                ("portail_reservations_absenti", "VARCHAR(100)", "Application d'une absence injustifiée"),
                ("portail_unites_multiples", "INTEGER", "Sélection multiple d'unités autorisée (0/1)"),
                ("regie", "INTEGER", "ID de la régie associée"),
                ("code_produit_local", "VARCHAR(200)", "Code produit local pour export compta"),
                ("inscriptions_multiples", "INTEGER", "Autoriser les inscriptions multiples (0/1)"),
                ("code_transport", "VARCHAR(10)", "Code analytique des transports liés à l'activitéà ajouter au compte lors d'export logiciels compta"),
                ], # Activités
            
    "agrements":[            ("IDagrement", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID Agrément"),
                ("IDactivite", "INTEGER", "ID de l'activité concernée"),
                ("agrement", "VARCHAR(200)", "Numéro d'agrément"),
                ("date_debut", "DATE", "Date de début de validité"),
                ("date_fin", "DATE", "Date de fin de validité"),
                ], # Agréments de l'activité

    "groupes":[
                ("IDgroupe", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID Groupe"),
                ("IDactivite", "INTEGER", "ID de l'activité concernée"),
                ("nom", "VARCHAR(200)", "Nom du groupe"),
                ("abrege", "VARCHAR(100)", "Nom abrégé du groupe"),
                ("ordre", "INTEGER", "Ordre"),
                ("nbre_inscrits_max", "INTEGER", "Nombre d'inscrits max"),
                ("ageMini", "INTEGER", "Age minimum pour le groupe"),
                ("ageMaxi", "INTEGER", "Age maximum pour le groupe"),
                ("observation", "BLOB", "Observations sur le groupe"),
                ("campeur","TINYINT", "0 anim, 1 campeur, 2 autre")
                ], # Groupes

    "pieces_activites":[    ("IDpiece_activite", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID Pièce activité"),
                ("IDactivite", "INTEGER", "ID de l'activité concernée"),
                ("IDtype_piece", "INTEGER", "ID du type de pièce à fournir"),
                ], # Pièces à fournir pour une activité

    "cotisations_activites":[("IDcotisation_activite", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID Cotisation activité"),
                ("IDactivite", "INTEGER", "ID de l'activité concernée"),
                ("IDtype_cotisation", "INTEGER", "ID du type de cotisation à fournir"),
                ], # Cotisations à avoir pour une activité
    
    "renseignements_activites":[("IDrenseignement", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID Renseignement"),
                ("IDactivite", "INTEGER", "ID de l'activité concernée"),
                ("IDtype_renseignement", "INTEGER", "ID du type de renseignement à fournir"),
                ], # Informations à renseigner par les individus pour une activité
    
    "restaurateurs":[        ("IDrestaurateur", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID Restaurateur"),
                ("nom", "VARCHAR(200)", "Nom du restaurateur"),
                ("rue", "VARCHAR(200)", "Adresse"),
                ("cp", "VARCHAR(10)", "Code postal"),
                ("ville", "VARCHAR(100)", "Ville"),  
                ("tel", "VARCHAR(50)", "Tel travail"),  
                ("fax", "VARCHAR(50)", "Fax travail"),  
                ("mail", "VARCHAR(100)", "Email"),  
                ], # Restaurateurs
    
    "unites":[                   ("IDunite", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID Unité"),
                ("IDactivite", "INTEGER", "ID de l'activité concernée"),
                ("ordre", "INTEGER", "Ordre"),
                ("nom", "VARCHAR(200)", "Nom de l'unité"),
                ("abrege", "VARCHAR(50)", "Nom abrégé"),
                ("type", "VARCHAR(20)", "Type (unitaire/horaire)"),
                ("heure_debut", "DATE", "Horaire minimum"),
                ("heure_debut_fixe", "INTEGER", "Heure de début fixe (0/1)"),
                ("heure_fin", "DATE", "Horaire maximal"),  
                ("heure_fin_fixe", "INTEGER", "Heure de fin fixe (0/1)"),
                ("repas", "INTEGER", "Repas inclus (0/1)"),  
                ("IDrestaurateur", "INTEGER", "IDrestaurateur"),
                ("date_debut", "DATE", "Date de début de validité"),  
                ("date_fin", "DATE", "Date de fin de validité"),
                ("touche_raccourci", "VARCHAR(30)", "Touche de raccourci pour la grille de saisie"), 
                ("largeur", "INTEGER", "Largeur de colonne en pixels"),
                ("coeff", "VARCHAR(50)", "Coeff pour état global"),
                ("autogen_active", "INTEGER", "Autogénération activée (0/1)"),
                ("autogen_conditions", "VARCHAR(400)", "Conditions de l'autogénération"),
                ("autogen_parametres", "VARCHAR(400)", "Paramètres de l'autogénération"),
                ], # Unités
    
    "unites_groupes":[      ("IDunite_groupe", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID Unité_groupe"),
                ("IDunite", "INTEGER", "ID de l'unité concernée"),
                ("IDgroupe", "INTEGER", "ID du groupe associé"),  
                ], # Groupes concernés par l'unité
    
    "unites_incompat":[    ("IDunite_incompat", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID Unité_incompat"),
                ("IDunite", "INTEGER", "ID de l'unité concernée"),
                ("IDunite_incompatible", "INTEGER", "ID de l'unité incompatible"),  
                ], # Unités incompatibles entre elles
    
    "unites_remplissage":[("IDunite_remplissage", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID Unité_remplissage"),
                ("IDactivite", "INTEGER", "ID de l'activité concernée"),
                ("ordre", "INTEGER", "Ordre"),
                ("nom", "VARCHAR(200)", "Nom de l'unité de remplissage"),
                ("abrege", "VARCHAR(50)", "Nom abrégé"),
                ("date_debut", "DATE", "Date de début de validité"),  
                ("date_fin", "DATE", "Date de fin de validité"),
                ("seuil_alerte", "INTEGER", "Seuil d'alerte de remplissage"),
                ("heure_min", "DATE", "Plage horaire conditionnelle - Heure min"),
                ("heure_max", "DATE", "Plage horaire conditionnelle - Heure max"),  
                ("afficher_page_accueil", "INTEGER", "Afficher dans le cadre Effectifs de la page d'accueil"),
                ("afficher_grille_conso", "INTEGER", "Afficher dans la grille des conso"),
                ("etiquettes", "VARCHAR(450)", "Etiquettes associées"),
                ("largeur", "INTEGER", "Largeur de colonne en pixels"),
                ], # Unités de remplissage
    
    "unites_remplissage_unites":[("IDunite_remplissage_unite", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID Unité_remplissage_unite"),
                ("IDunite_remplissage", "INTEGER", "ID de l'unité de remplissage concernée"),
                ("IDunite", "INTEGER", "ID de l'unité associée"),  
                ], # Unités associées aux unités de remplissage
                
    "ouvertures":[             ("IDouverture", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID ouverture"),
                ("IDactivite", "INTEGER", "ID de l'activité concernée"),
                ("IDunite", "INTEGER", "ID de l'unité concernée"),
                ("IDgroupe", "INTEGER", "ID du groupe concerné"),
                ("date", "DATE", "Date de l'ouverture"),  
                ], # Jours de fonctionnement des unités
                
    "remplissage":[          ("IDremplissage", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID remplissage"),
                ("IDactivite", "INTEGER", "ID de l'activité concernée"),
                ("IDunite_remplissage", "INTEGER", "ID de l'unité de remplissage concernée"),
                ("IDgroupe", "INTEGER", "ID du groupe concerné"),
                ("date", "DATE", "Date de l'ouverture"),
                ("places", "INTEGER", "Nbre de places"),  
                ], # Nbre de places maxi pour chaque unité de remplissage
    
    "categories_tarifs":[    ("IDcategorie_tarif", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID Catégorie de tarif"),
                ("IDactivite", "INTEGER", "ID de l'activité concernée"),
                ("nom", "VARCHAR(200)", "Nom de la catégorie"),
                ("campeur", "TINYINT", "Compter dans les effectifs O anim, 1 campeur, 2 autre(enfants personnel...)"),
         ], # Catégories de tarifs
    
    "categories_tarifs_villes":[("IDville", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID Ville"),
                ("IDcategorie_tarif", "INTEGER", "ID de la catégorie de tarif concernée"),
                ("cp", "VARCHAR(10)", "Code postal"),
                ("nom", "VARCHAR(100)", "Nom de la ville"),
                ], # Villes rattachées aux catégories de tarifs
    
    "noms_tarifs":[           ("IDnom_tarif", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID nom tarif"),
                ("IDactivite", "INTEGER", "ID de l'activité concernée"),
                ("IDcategorie_tarif", "INTEGER", "ID categorie_tarif rattachée"),
                ("nom", "VARCHAR(200)", "Nom du tarif"),
                ], # Noms des tarifs
    
    "tarifs":[                    ("IDtarif", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID tarif"),
                ("IDactivite", "INTEGER", "ID de l'activité concernée"),
                ("type", "VARCHAR(50)", "Type de tarif"),
                ("IDcategorie_tarif", "INTEGER", "ID categorie_tarif rattachée"),
                ("IDnom_tarif", "INTEGER", "ID nom du tarif"),
                ("date_debut", "DATE", "Date de début de validité"),
                ("date_fin", "DATE", "Date de fin de validité"),  
                ("condition_nbre_combi", "INTEGER", ""),
                ("condition_periode", "VARCHAR(100)", "Type de tarif (prédéfini ou automatique)"),
                ("condition_nbre_jours", "INTEGER", ""),
                ("condition_conso_facturees", "INTEGER", ""),
                ("condition_dates_continues", "INTEGER", ""),
                ("forfait_saisie_manuelle", "INTEGER", "Saisie manuelle du forfait possible (0/1)"),
                ("forfait_saisie_auto", "INTEGER", "Saisie automatique du forfait quand inscription (0/1)"),
                ("forfait_suppression_auto", "INTEGER", "Suppression manuelle impossible (0/1)"),
                ("methode", "VARCHAR(50)", "Code de la méthode de calcul"),
                ("categories_tarifs", "VARCHAR(300)", "Catégories de tarifs rattachées à ce tarif"),
                ("groupes", "VARCHAR(300)", "Groupes rattachés à ce tarif"),
                ("forfait_duree", "VARCHAR(50)", "Durée du forfait"),
                ("forfait_beneficiaire", "VARCHAR(50)", "Bénéficiaire du forfait (famille|individu)"),
                ("cotisations", "VARCHAR(300)", "Cotisations rattachées à ce tarif"),
                ("caisses", "VARCHAR(300)", "Caisses rattachées à ce tarif"),
                ("description", "VARCHAR(450)", "Description du tarif"),
                ("jours_scolaires", "VARCHAR(100)", "Jours scolaires"),
                ("jours_vacances", "VARCHAR(100)", "Jours de vacances"),
                ("options", "VARCHAR(450)", "Options diverses"),
                ("observations", "VARCHAR(450)", "Observations sur le tarif"),
                ("tva", "FLOAT", "Taux TVA"),
                ("code_compta", "VARCHAR(200)", "Code comptable pour export vers logiciels de compta"),
                ("date_facturation", "VARCHAR(450)", "Date de facturation de la prestation"),
                ("etiquettes", "VARCHAR(450)", "Etiquettes rattachées à ce tarif"),
                ("etats", "VARCHAR(150)", "Etats de consommations rattachés à ce tarif"),
                ("IDtype_quotient", "INTEGER", "ID du type de quotient"),
                ("label_prestation", "VARCHAR(300)", "Label de la prestation"),
                ("IDevenement", "INTEGER", "ID de l'évènement associé"),
                ("IDproduit", "INTEGER", "ID du produit associé"),
                ("code_produit_local", "VARCHAR(200)", "Code produit local pour export compta"),
                ], # Tarifs
    
    "combi_tarifs":          [("IDcombi_tarif", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID combinaison de tarif"),
                ("IDtarif", "INTEGER", "ID du tarif"),
                ("type", "VARCHAR(50)", "Type de combinaison"),
                ("date", "DATE", "Date si dans forfait"),
                ("quantite_max", "INTEGER", "Quantité max d'unités"),
                ("IDgroupe", "INTEGER", "ID du groupe concerné"),
                ], # Obsolète Combinaisons d'unités pour les tarifs
    
    "combi_tarifs_unites":[("IDcombi_tarif_unite", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID combinaison de tarif"),
                ("IDcombi_tarif", "INTEGER", "ID du combi_tarif"),
                ("IDtarif", "INTEGER", "ID du tarif"),
                ("IDunite", "INTEGER", "ID de l'unité"),
                ], # Obsolète Combinaisons d'unités pour les tarifs
    
    "tarifs_lignes":          [("IDligne", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID ligne de tarif"),
                ("IDactivite", "INTEGER", "ID de l'activité concernée"),
                ("IDtarif", "INTEGER", "ID du tarif"),
                ("code", "VARCHAR(50)", "Code de la méthode"),
                ("num_ligne", "INTEGER", "Numéro de ligne"),
                ("tranche", "VARCHAR(10)", "Nom de tranche"),
                ("qf_min", "FLOAT", "Montant QF min"),
                ("qf_max", "FLOAT", "Montant QF max"),
                ("montant_unique", "FLOAT", "Montant unique"),
                ("montant_enfant_1", "FLOAT", "Montant pour 1 enfant"),
                ("montant_enfant_2", "FLOAT", "Montant pour 2 enfants"),
                ("montant_enfant_3", "FLOAT", "Montant pour 3 enfants"),
                ("montant_enfant_4", "FLOAT", "Montant pour 4 enfants"),
                ("montant_enfant_5", "FLOAT", "Montant pour 5 enfants"),
                ("montant_enfant_6", "FLOAT", "Montant pour 6 enfants et plus"),
                ("nbre_enfants", "INTEGER", "Nbre d'enfants pour le calcul par taux d'effort"),
                ("coefficient", "FLOAT", "Coefficient"),
                ("montant_min", "FLOAT", "Montant mini pour le calcul par taux d'effort"),
                ("montant_max", "FLOAT", "Montant maxi pour le calcul par taux d'effort"),
                ("heure_debut_min", "DATE", "Heure début min pour unités horaires"),  
                ("heure_debut_max", "DATE", "Heure début max pour unités horaires"),  
                ("heure_fin_min", "DATE", "Heure fin min pour unités horaires"),  
                ("heure_fin_max", "DATE", "Heure fin max pour unités horaires"), 
                ("duree_min", "DATE", "Durée min pour unités horaires"), 
                ("duree_max", "DATE", "Durée min pour unités horaires"), 
                ("date", "DATE", "Date conditionnelle"), 
                ("label", "VARCHAR(300)", "Label personnalisé pour la prestation"), 
                ("temps_facture", "DATE", "Temps facturé pour la CAF"), 
                ("unite_horaire", "DATE", "Unité horaire pour base de calcul selon coefficient"), 
                ("duree_seuil", "DATE", "Durée seuil"), 
                ("duree_plafond", "DATE", "Durée plafond"), 
                ("taux", "FLOAT", "Taux d'effort"), 
                ("ajustement", "FLOAT", "Ajustement (majoration/déduction)"), 
                ("montant_questionnaire", "INTEGER", "IDquestion de la table questionnaires"),
                ("revenu_min", "FLOAT", "Montant revenu min"),
                ("revenu_max", "FLOAT", "Montant revenu max"),
                ("IDmodele", "INTEGER", "IDmodele de prestation"),
                ], # Obsolète Lignes du tableau de calcul de tarifs
                
    "inscriptions":[           ("IDinscription", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID inscription"),
                ("IDindividu", "INTEGER", "ID de l'individu"),
                ("IDfamille", "INTEGER", "ID de la famille"),
                ("IDactivite", "INTEGER", "ID de l'activité"),
                ("IDgroupe", "INTEGER", "ID du groupe"),
                ("IDcategorie_tarif", "INTEGER", "ID de la catégorie de tarif"),
                ("IDcompte_payeur", "INTEGER", "ID du compte payeur par défaut"), 
                ("date_inscription", "DATE", "Date de l'inscription"),
                ("parti", "INTEGER", "(0/1) est parti"),
                ("date_desinscription", "DATE", "Date de désinscription"),
                ("statut", "VARCHAR(100)", "Statut de l'inscription"),
                ("jours", "INTEGER", "Nbre de jours forcé"),
                ], # Inscriptions des individus à des activités
    
    "consommations":[    ("IDconso", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID consommation"),
                ("IDindividu", "INTEGER", "ID de l'individu"),
                ("IDinscription", "INTEGER", "ID de l'inscription"),
                ("IDactivite", "INTEGER", "ID de l'activité"),
                ("date", "DATE", "Date de la consommation"),
                ("IDunite", "INTEGER", "ID de l'unité"),
                ("IDgroupe", "INTEGER", "ID du groupe"),
                ("heure_debut", "DATE", "Heure min pour unités horaires"),  
                ("heure_fin", "DATE", "Heure max pour unités horaires"),  
                ("etat", "VARCHAR(20)", "Etat"),
                ("verrouillage", "INTEGER", "1 si la consommation est verrouillée"),
                ("date_saisie", "DATE", "Date de saisie de la consommation"),
                ("IDutilisateur", "INTEGER", "Utilisateur qui a fait la saisie"),
                ("IDcategorie_tarif", "INTEGER", "ID de la catégorie de tarif"), 
                ("IDcompte_payeur", "INTEGER", "ID du compte payeur"),
                ("IDprestation", "INTEGER", "ID de la prestation"),
                ("forfait", "INTEGER", "Type de forfait : 0 : Aucun | 1 : Suppr possible | 2 : Suppr impossible"),
                ("quantite", "INTEGER", "Quantité de consommations"),
                ("etiquettes", "VARCHAR(50)", "Etiquettes"),
                ("IDevenement", "INTEGER", "ID de l'évènement"),
                ("badgeage_debut", "DATETIME", "Date et heure de badgeage du début"),
                ("badgeage_fin", "DATETIME", "Date et heure de badgeage de fin"),
                ], # Consommations
    
    "memo_journee":[      ("IDmemo", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID memo"),
                ("IDindividu", "INTEGER", "ID de l'individu"),
                ("date", "DATE", "Date"),
                ("texte", "VARCHAR(200)", "Texte du mémo"),
                ("couleur", "VARCHAR(50)", "Couleur"),
                ], # Mémo journées
    
    "prestations":[           ("IDprestation", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID prestation"),
                ("IDcompte_payeur", "INTEGER", "ID du compte payeur"),
                ("date", "DATE", "Date de la prestation"),
                ("categorie", "VARCHAR(50)", "Catégorie de la prestation"),
                ("label", "VARCHAR(200)", "Label de la prestation"),
                ("montant_initial", "FLOAT", "Montant de la prestation AVANT déductions"),
                ("montant", "FLOAT", "Montant de la prestation"),
                ("IDactivite", "INTEGER", "ID de l'activité"),
                ("IDtarif", "INTEGER", "ID du tarif"),
                ("IDfacture", "INTEGER", "ID de la facture"),
                ("IDfamille", "INTEGER", "ID de la famille concernée"),
                ("IDindividu", "INTEGER", "ID de l'individu concerné"),
                ("forfait", "INTEGER", "Type de forfait : 0 : Aucun | 1 : Suppr possible | 2 : Suppr impossible"),
                ("temps_facture", "DATE", "Temps facturé format 00:00"),  
                ("IDcategorie_tarif", "INTEGER", "ID de la catégorie de tarif"),
                ("forfait_date_debut", "DATE", "Date de début de forfait"),
                ("forfait_date_fin", "DATE", "Date de fin de forfait"),
                ("reglement_frais", "INTEGER", "ID du règlement"),
                ("tva", "FLOAT", "Taux TVA"),
                ("code_compta", "VARCHAR(200)", "Code comptable pour export vers logiciels de compta"),
                ("IDcontrat", "INTEGER", "ID du contrat associé"),
                ("date_valeur", "DATE", "Date de valeur comptable de la prestation"),
                ("IDdonnee", "INTEGER", "ID d'une donnée associée"),
                ("code_produit_local", "VARCHAR(200)", "Code produit local pour export compta"),
                ("compta", "INTEGER", "Pointeur de transfert en compta"),
                ], # Prestations
    
    "comptes_payeurs":[  ("IDcompte_payeur", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID compte_payeur"),
                ("IDfamille", "INTEGER", "ID de la famille concernée"),
                ("IDindividu", "INTEGER", "ID de l'individu concerné"),
                ], # Comptes payeurs
    
    "modes_reglements":[("IDmode", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID mode de règlement"),
                ("label", "VARCHAR(100)", "Label du mode"),
                ("image", "LONGBLOB", "Image du mode"),
                ("numero_piece", "VARCHAR(10)", "Numéro de pièce (None|ALPHA|NUM)"),
                ("nbre_chiffres", "INTEGER", "Nbre de chiffres du numéro"),
                ("frais_gestion", "VARCHAR(10)", "Frais de gestion None|LIBRE|FIXE|PRORATA"),
                ("frais_montant", "FLOAT", "Montant fixe des frais"),
                ("frais_pourcentage", "FLOAT", "Prorata des frais"),
                ("frais_arrondi", "VARCHAR(20)", "Méthode d'arrondi"),
                ("frais_label", "VARCHAR(200)", "Label de la prestation"),
                ("type_comptable", "VARCHAR(200)", "Type comptable (banque ou caisse)"),
                ("code_compta", "VARCHAR(200)", "Code comptable pour export vers logiciels de compta"),
                ("IDcompte", "INTEGER","Code du compte bancaire par défaut pour dépots"),
           ], # Modes de règlements
    
    "emetteurs":[             ("IDemetteur", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID Emetteur"),
                ("IDmode", "INTEGER", "ID du mode concerné"),
                ("nom", "VARCHAR(200)", "Nom de l'émetteur"),
                ("image", "LONGBLOB", "Image de l'emetteur"),
                ], # Emetteurs pour les modes de règlements
    
    "payeurs":[                ("IDpayeur", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID Payeur"),
                ("IDcompte_payeur", "INTEGER", "ID du compte payeur concerné"),
                ("nom", "VARCHAR(100)", "Nom du payeur"),
                ], # Payeurs
    
    "comptes_bancaires":[("IDcompte", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID Compte"),
                ("nom", "VARCHAR(100)", "Intitulé du compte"),
                ("numero", "VARCHAR(50)", "Numéro du compte"),
                ("defaut", "INTEGER", "(0/1) Compte sélectionné par défaut"),
                ("raison", "VARCHAR(400)", "Raison sociale"),
                ("code_etab", "VARCHAR(400)", "Code établissement"),
                ("code_guichet", "VARCHAR(400)", "Code guichet"),
                ("code_nne", "VARCHAR(400)", "Code NNE pour prélèvements auto."),
                ("cle_rib", "VARCHAR(400)", "Clé RIB pour prélèvements auto."),
                ("cle_iban", "VARCHAR(400)", "Clé IBAN pour prélèvements auto."),
                ("iban", "VARCHAR(400)", "Numéro IBAN pour prélèvements auto."),
                ("bic", "VARCHAR(400)", "Numéro BIC pour prélèvements auto."),
                ("code_ics", "VARCHAR(400)", "Code NNE pour prélèvements auto."),
                ("dft_titulaire", "VARCHAR(400)", "Titulaire du compte DFT"),
                ("dft_iban", "VARCHAR(400)", "Numéro IBAN du compte DFT"),
                ], # Comptes bancaires de l'organisateur
                
    "reglements":[            ("IDreglement", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID Règlement"),
                ("IDcompte_payeur", "INTEGER", "ID du compte payeur"),
                ("date", "DATE", "Date d'émission du règlement"),
                ("IDmode", "INTEGER", "ID du mode de règlement"),
                ("IDemetteur", "INTEGER", "ID de l'émetteur du règlement"),
                ("numero_piece", "VARCHAR(30)", "Numéro de pièce"),
                ("montant", "FLOAT", "Montant du règlement"),
                ("IDpayeur", "INTEGER", "ID du payeur"),
                ("observations", "VARCHAR(200)", "Observations"),
                ("numero_quittancier", "VARCHAR(30)", "Numéro de quittancier"),
                ("IDprestation_frais", "INTEGER", "ID de la prestation de frais de gestion"),
                ("IDcompte", "INTEGER", "ID du compte bancaire pour l'encaissement"),
                ("date_differe", "DATE", "Date de l'encaissement différé"),
                ("encaissement_attente", "INTEGER", "(0/1) Encaissement en attente"),
                ("IDdepot", "INTEGER", "ID du dépôt"),
                ("date_saisie", "DATE", "Date de saisie du règlement"),
                ("IDutilisateur", "INTEGER", "Utilisateur qui a fait la saisie"),
                ("IDprelevement", "INTEGER", "ID du prélèvement"),
                ("avis_depot", "DATE", "Date de l'envoi de l'avis de dépôt"),
                ("IDpiece", "INTEGER", "IDpiece pour PES V2 ORMC"),
                ("compta", "INTEGER", "Pointeur de transfert en compta"),
                ], # Règlements
    
    "ventilation":[("IDventilation", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID Ventilation"),
                ("IDcompte_payeur", "INTEGER", "ID du compte payeur"),
                ("IDreglement", "INTEGER", "ID du règlement"),
                ("IDprestation", "INTEGER", "ID de la prestation"),
                ("montant", "FLOAT", "Montant de la ventilation"),
                ("lettrage", "VARCHAR(64)", "Lettre de l'enregistrement"),
                ], # Ventilation
    
    "depots":[                  ("IDdepot", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID Dépôt"),
                ("date", "DATE", "Date du dépôt"),
                ("nom", "VARCHAR(200)", "Nom du dépôt"),
                ("verrouillage", "INTEGER", "(0/1) Verrouillage du dépôt"),
                ("IDcompte", "INTEGER", "ID du compte d'encaissement"),
                ("observations", "VARCHAR(500)", "Observations"),
                ("code_compta", "VARCHAR(200)", "Code comptable pour export vers logiciels de compta"),
                ], # Dépôts
    
    "quotients":[              ("IDquotient", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID Quotient familial"),
                ("IDfamille", "INTEGER", "ID de la famille"),
                ("date_debut", "DATE", "Date de début de validité"),
                ("date_fin", "DATE", "Date de fin de validité"),
                ("quotient", "INTEGER", "Quotient familial"),
                ("observations", "VARCHAR(500)", "Observations"),
                ("revenu", "FLOAT", "Montant du revenu"),
                ("IDtype_quotient", "INTEGER", "Type de quotient"),
                ], # Quotients familiaux
    
    "caisses":[                ("IDcaisse", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID Caisse"),
                ("nom", "VARCHAR(255)", "Nom de la caisse"),
                ("IDregime", "INTEGER", "Régime social affilié"),
                ], # Caisses d'allocations
    
    "regimes":[                ("IDregime", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID Régime"),
                ("nom", "VARCHAR(255)", "Nom du régime social"),
                ], # Régimes sociaux
    
    "aides":[                    ("IDaide", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID Aide"),
                ("IDfamille", "INTEGER", "ID de la famille"),
                ("IDactivite", "INTEGER", "ID de l'activité"),
                ("nom", "VARCHAR(200)", "Nom de l'aide"),
                ("date_debut", "DATE", "Date de début de validité"),
                ("date_fin", "DATE", "Date de fin de validité"),
                ("IDcaisse", "INTEGER", "ID de la caisse"),
                ("montant_max", "FLOAT", "Montant maximal de l'aide"),
                ("nbre_dates_max", "INTEGER", "Nbre maximal de DATEs"),
                ("jours_scolaires", "VARCHAR(50)", "Jours scolaires"),
                ("jours_vacances", "VARCHAR(50)", "Jours de vacances"),
                ], # Aides journalières
    
    "aides_beneficiaires":[("IDaide_beneficiaire", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID bénéficiaire"),
                ("IDaide", "INTEGER", "ID de l'aide"),
                ("IDindividu", "INTEGER", "ID de l'individu"),
                ], # Bénéficiaires des aides journalières
    
    "aides_montants":[    ("IDaide_montant", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID Aide montant"),
                ("IDaide", "INTEGER", "ID de l'aide"),
                ("montant", "FLOAT", "Montant"),
                ], # Montants des aides journalières
    
    "aides_combinaisons":[("IDaide_combi", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID Combinaison"),
                ("IDaide", "INTEGER", "ID de l'aide"),
                ("IDaide_montant", "INTEGER", "ID de l'aide"),
                ], # Combinaisons d'unités pour les aides journalières
    
    "aides_combi_unites":[("IDaide_combi_unite", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID unité pour Combinaison"),
                ("IDaide", "INTEGER", "ID de l'aide"),
                ("IDaide_combi", "INTEGER", "ID de la combinaison"),
                ("IDunite", "INTEGER", "ID de l'unité"),
                ], # Unités des combinaisons pour les aides journalières
    
    "deductions":[           ("IDdeduction", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID déduction"),
                ("IDprestation", "INTEGER", "ID de la prestation"),
                ("IDcompte_payeur", "INTEGER", "IDcompte_payeur"),
                ("date", "DATE", "Date de la déduction"),
                ("montant", "FLOAT", "Montant"),
                ("label", "VARCHAR(200)", "Label de la déduction"),
                ("IDaide", "INTEGER", "ID de l'aide"),
                ], # Déductions pour les prestations
    
    "types_cotisations":[  ("IDtype_cotisation", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID type cotisation"),
                ("nom", "VARCHAR(200)", "Nom de la cotisation"),
                ("type", "VARCHAR(50)", "Type de cotisation (individu/famille)"),
                ("carte", "INTEGER", "(0/1) Est une carte d'adhérent"),
                ("defaut", "INTEGER", "(0/1) Cotisation sélectionnée par défaut"),
                ("code_comptable", "VARCHAR(450)", "Code comptable pour facturation et export logiciels compta"),
                ("code_produit_local", "VARCHAR(200)", "Code produit local pour export compta"),
                ], # Types de cotisations
    
    "unites_cotisations":[ ("IDunite_cotisation", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID unité cotisation"),
                ("IDtype_cotisation", "INTEGER", "ID du type de cotisation"),
                ("date_debut", "DATE", "Date de début de validité"),
                ("date_fin", "DATE", "Date de fin de validité"),
                ("nom", "VARCHAR(200)", "Nom de l'unité de cotisation"),
                ("montant", "FLOAT", "Montant"),
                ("label_prestation", "VARCHAR(200)", "Label de la prestation"),
                ("defaut", "INTEGER", "(0/1) Unité sélectionnée par défaut"),
                ("duree", "VARCHAR(100)", "Durée de validité"),
                ], # Unités de cotisation
    
    "cotisations":[            ("IDcotisation", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID cotisation"),
                ("IDfamille", "INTEGER", "ID de la famille"),
                ("IDindividu", "INTEGER", "ID de l'individu"),
                ("IDtype_cotisation", "INTEGER", "ID du type de cotisation"),
                ("IDunite_cotisation", "INTEGER", "ID de l'unité de cotisation"),
                ("date_saisie", "DATE", "Date de saisie"),
                ("IDutilisateur", "INTEGER", "ID de l'utilisateur"),
                ("date_creation_carte", "DATE", "Date de création de la carte"),
                ("numero", "VARCHAR(50)", "Numéro d'adhérent"),
                ("IDdepot_cotisation", "INTEGER", "ID du dépôt des cotisations"),
                ("date_debut", "DATE", "Date de début de validité"),
                ("date_fin", "DATE", "Date de fin de validité"),
                ("IDprestation", "INTEGER", "ID de la prestation associée"),
                ("observations", "VARCHAR(1000)", "Observations"),
                ("activites", "VARCHAR(450)", "Liste d'activités associées"),
                ], # Cotisations
    
    "depots_cotisations":[("IDdepot_cotisation", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID Dépôt Cotisation"),
                ("date", "DATE", "Date du dépôt"),
                ("nom", "VARCHAR(200)", "Nom du dépôt"),
                ("verrouillage", "INTEGER", "(0/1) Verrouillage du dépôt"),
                ("observations", "VARCHAR(1000)", "Observations"),
                ], # Dépôts de cotisations
    
    "parametres":[           ("IDparametre", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID parametre"),
                ("categorie", "VARCHAR(200)", "Catégorie"),
                ("nom", "VARCHAR(200)", "Nom"),
                ("parametre", "VARCHAR(100000)", "Parametre"),
                ], # Paramètres
    
    "types_groupes_activites":[("IDtype_groupe_activite", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID type groupe activité"),
                ("nom", "VARCHAR(255)", "Nom"),
                ("observations", "VARCHAR(500)", "Observations"),
                ("anaTransports", "VARCHAR(8)", "Analytique Transports"),
                ], # Types de groupes d'activités
    
    "groupes_activites":[  ("IDgroupe_activite", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID type groupe activité"),
                ("IDtype_groupe_activite", "INTEGER", "ID du groupe d'activité"),
                ("IDactivite", "INTEGER", "ID de l'activité concernée"),
                ], # Groupes d'activités
    
    "secteurs":[               ("IDsecteur", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID pays postal"),
                ("nom", "VARCHAR(255)", "Nom du pays postal"),
                ], # pays postaux
    
    "types_sieste":[         ("IDtype_sieste", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID type sieste"),
                ("nom", "VARCHAR(255)", "Nom du type de sieste"),
                ], # Types de sieste
    
    "factures_messages":[("IDmessage", "INTEGER PRIMARY KEY AUTOINCREMENT", "IDmessage"),
                ("titre", "VARCHAR(255)", "Titre du message"),
                ("texte", "VARCHAR(1000)", "Contenu du message"),
                ], # Messages dans les factures
    
    "factures":[                ("IDfacture", "INTEGER PRIMARY KEY AUTOINCREMENT", "IDfacture"),
                ("numero", "INTEGER", "Numéro de facture"),
                ("IDcompte_payeur", "INTEGER", "ID du compte payeur"),
                ("date_edition", "DATE", "Date d'édition de la facture"),
                ("date_echeance", "DATE", "Date d'échéance de la facture"),
                ("activites", "VARCHAR(500)", "Liste des IDactivité séparées par ;"),
                ("individus", "VARCHAR(500)", "Liste des IDindividus séparées par ;"),
                ("IDutilisateur", "INTEGER", "Utilisateur qui a créé la facture"),
                ("date_debut", "DATE", "Date de début de période"),
                ("date_fin", "DATE", "Date de fin de période"),
                ("total", "FLOAT", "Montant total de la période"),
                ("regle", "FLOAT", "Montant réglé pour la période"),
                ("solde", "FLOAT", "Solde à régler pour la période"),
                ("IDlot", "INTEGER", "ID du lot de factures"),
                ("prestations", "VARCHAR(500)", "Libellé rappelant l'origine (non exploité)"),
                ("etat", "VARCHAR(100)", "Etat de la facture"),
                ("IDprefixe", "INTEGER", "ID du préfixe"),
                ("IDregie", "INTEGER", "ID de la régie"),
                ("mention1", "VARCHAR(300)", "Mention 1"),
                ("mention2", "VARCHAR(300)", "Mention 2"),
                ("mention3", "VARCHAR(300)", "Mention 3"),
                ], # Factures éditées
    
    "textes_rappels":[      ("IDtexte", "INTEGER PRIMARY KEY AUTOINCREMENT", "IDtexte"),
                ("label", "VARCHAR(255)", "Label du texte"),
                ("couleur", "VARCHAR(50)", "Couleur"),
                ("retard_min", "INTEGER", "Minimum retard"),
                ("retard_max", "INTEGER", "Maximum retard"),
                ("titre", "VARCHAR(255)", "Titre du rappel"),
                ("texte_xml", "VARCHAR(5000)", "Contenu du texte version XML"),
                ("texte_pdf", "VARCHAR(5000)", "Contenu du texte version PDF"),
                ], # Textes pour les lettres de rappel
    
    "rappels":[                 ("IDrappel", "INTEGER PRIMARY KEY AUTOINCREMENT", "IDrappel"),
                ("numero", "INTEGER", "Numéro du rappel"),
                ("IDcompte_payeur", "INTEGER", "ID du compte payeur"),
                ("date_edition", "DATE", "Date d'édition du rappel"),
                ("activites", "VARCHAR(500)", "Liste des IDactivité séparées par ;"),
                ("IDutilisateur", "INTEGER", "Utilisateur qui a créé le rappel"),
                ("IDtexte", "INTEGER", "ID du texte de rappel"),
                ("date_reference", "DATE", "Date de référence"),
                ("solde", "FLOAT", "Solde à régler"),
                ("date_min", "DATE", "Date min"),
                ("date_max", "DATE", "Date max"),
                ("IDlot", "INTEGER", "ID du lot de rappels"),
                ("prestations", "VARCHAR(500)", "Liste des types de prestations intégrées"),
                ], # Rappels édités
    
    "utilisateurs":[            ("IDutilisateur", "INTEGER PRIMARY KEY AUTOINCREMENT", "IDutilisateur"),
                ("sexe", "VARCHAR(5)", "Sexe utilisateur"),
                ("nom", "VARCHAR(200)", "Nom utilisateur"),
                ("prenom", "VARCHAR(200)", "Prenom utilisateur"),
                ("mdp", "VARCHAR(100)", "Mot de passe"),
                ("profil", "VARCHAR(100)", "Profil (Administrateur ou utilisateur)"),
                ("actif", "INTEGER", "Utilisateur actif"),
                ("image", "VARCHAR(200)", "Images"),
                ("mdpcrypt", "VARCHAR(200)", "Mot de passe crypté"),
                ("internet_actif", "INTEGER", "(0/1) Compte internet actif"),
                ("internet_identifiant", "VARCHAR(300)", "Code identifiant internet"),
                ("internet_mdp", "VARCHAR(300)", "Mot de passe internet"),
                ], # Utilisateurs
    
    "messages":[            ("IDmessage", "INTEGER PRIMARY KEY AUTOINCREMENT", "IDmessage"),
                ("type", "VARCHAR(30)", "Type (instantané ou programmé)"),
                ("IDcategorie", "INTEGER", "ID de la catégorie"),
                ("date_saisie", "DATE", "Date de saisie"),
                ("IDutilisateur", "INTEGER", "ID de l'utilisateur"),
                ("date_parution", "DATE", "Date de parution"),
                ("priorite", "VARCHAR(30)", "Priorité"),
                ("afficher_accueil", "INTEGER", "Afficher sur la page d'accueil"),
                ("afficher_liste", "INTEGER", "Afficher sur la liste des conso"),
                ("afficher_commande", "INTEGER", "Afficher sur la commande des repas"),
                ("rappel", "INTEGER", "Rappel à l'ouverture du fichier"),
                ("IDfamille", "INTEGER", "IDfamille"),
                ("IDindividu", "INTEGER", "IDindividu"),
                ("nom", "VARCHAR(255)", "Nom de la famille ou de l'individu"),
                ("texte", "VARCHAR(500)", "Texte du message"),
                ("afficher_facture", "INTEGER", "Afficher sur les factures de la famille"),
                ("rappel_famille", "INTEGER", "Rappel à l'ouverture de la fiche famille"),
                ], # Messages
    
    "messages_categories":[("IDcategorie", "INTEGER PRIMARY KEY AUTOINCREMENT", "IDcategorie"),
                ("nom", "VARCHAR(255)", "Nom de la catégorie"),
                ("priorite", "VARCHAR(30)", "Priorité"),
                ("afficher_accueil", "INTEGER", "Afficher sur la page d'accueil"),
                ("afficher_liste", "INTEGER", "Afficher sur la liste des conso"),
                ], # Catégories de messages
    
    "historique":[              ("IDaction", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID de l'action"),
                ("date", "DATE", "Date de l'action"),
                ("heure", "DATE", "Heure de l'action"),
                ("IDutilisateur", "INTEGER", "ID de l'utilisateur"),
                ("IDfamille", "INTEGER", "ID de la famille"),
                ("IDindividu", "INTEGER", "ID de l'individu"),
                ("IDcategorie", "INTEGER", "ID de la catégorie d'action"),
                ("action", "VARCHAR(500)", "Action"),
                ("IDdonnee", "INTEGER", "Donnée associée à l'action"),
                ], # Historique
    
    "attestations":[           ("IDattestation", "INTEGER PRIMARY KEY AUTOINCREMENT", "IDattestation"),
                ("numero", "INTEGER", "Numéro d'attestation"),
                ("IDfamille", "INTEGER", "ID de la famille"),
                ("date_edition", "DATE", "Date d'édition de l'attestation"),
                ("activites", "VARCHAR(450)", "Liste des IDactivité séparées par ;"),
                ("individus", "VARCHAR(450)", "Liste des IDindividus séparées par ;"),
                ("IDutilisateur", "INTEGER", "Utilisateur qui a créé l'attestation"),
                ("date_debut", "DATE", "Date de début de période"),
                ("date_fin", "DATE", "Date de fin de période"),
                ("total", "FLOAT", "Montant total de la période"),
                ("regle", "FLOAT", "Montant réglé pour la période"),
                ("solde", "FLOAT", "Solde à régler pour la période"),
                ], # Attestation de présence éditées
    
    "recus":[                   ("IDrecu", "INTEGER PRIMARY KEY AUTOINCREMENT", "IDrecu"),
                ("numero", "INTEGER", "Numéro du recu"),
                ("IDfamille", "INTEGER", "ID de la famille"),
                ("date_edition", "DATE", "Date d'édition du recu"),
                ("IDutilisateur", "INTEGER", "Utilisateur qui a créé l'attestation"),
                ("IDreglement", "INTEGER", "ID du règlement"),
                ], # Recus de règlements
    
    "adresses_mail":  [    ("IDadresse", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID"),
                ("adresse", "VARCHAR(200)", "Adresse de messagerie"),
                ("nom_adresse", "VARCHAR(200)", "Nom d'affichage de l'adresse de messagerie"),
                ("motdepasse", "VARCHAR(200)", "Mot de passe si SSL"),
                ("smtp", "VARCHAR(200)", "Adresse SMTP"),
                ("port", "INTEGER", "Numéro du port"),
                ("connexionssl", "INTEGER", "N'est plus utilisé !"),
                ("defaut", "INTEGER", "Adresse utilisée par défaut (1/0)"),
                ("connexionAuthentifiee", "INTEGER", "Authentification activée (1/0)"),
                ("startTLS", "INTEGER", "startTLS activé (1/0)"),
                ("utilisateur", "VARCHAR(200)", "Nom d'utilisateur"),
                ("moteur", "VARCHAR(200)", "Moteur d'envoi"),
                ("parametres", "VARCHAR(1000)", "Autres paramètres"),
                ], # Adresses d'expéditeur de mail
    
    "listes_diffusion":  [    ("IDliste", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID"),
                ("nom", "VARCHAR(200)", "Nom de la liste de diffusion"),
                ("abrege", "VARCHAR(8)", "Abrégé de la liste de diffusion"),
                ], # Listes de diffusion
    
    "abonnements":    [    ("IDabonnement", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID"),
                ("IDliste", "INTEGER", "ID de la liste de diffusion"),
                ("IDindividu", "INTEGER", "ID de l'individu abonné"),
                ], # Abonnements aux listes de diffusion
    
    "documents_modeles":[("IDmodele", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID"),
                ("nom", "VARCHAR(200)", "Nom du modèle"),
                ("categorie", "VARCHAR(200)", "Catégorie du modèle (ex : facture)"),
                ("supprimable", "INTEGER", "Est supprimable (1/0)"),
                ("largeur", "INTEGER", "Largeur en mm"),
                ("hauteur", "INTEGER", "Hauteur en mm"),
                ("observations", "VARCHAR(400)", "Observations"),
                ("IDfond", "INTEGER", "IDfond du modèle"),
                ("defaut", "INTEGER", "Modèle utilisé par défaut (1/0)"),
                ("IDdonnee", "INTEGER", "Donnée associée au document"),
                ], # Modèles de documents
    
    "documents_objets":[ ("IDobjet", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID"),
                ("IDmodele", "INTEGER", "ID du modèle rattaché"),
                ("nom", "VARCHAR(200)", "Nom de l'objet"),
                ("categorie", "VARCHAR(200)", "Catégorie d'objet (ex : rectangle)"),
                ("champ", "VARCHAR(200)", "Champ"),
                ("ordre", "INTEGER", "Ordre"),
                ("obligatoire", "INTEGER", "Est obligatoire (0/1)"),
                ("nbreMax", "INTEGER", "Nbre max d'objets dans le document"),
                ("texte", "VARCHAR(600)", "Texte"),
                ("points", "VARCHAR(600)", "Points de lignes ou de polygones"),
                ("image", "LONGBLOB", "Image"),
                ("typeImage", "VARCHAR(100)", "Type de l'image (logo, fichier)"),
                ("x", "INTEGER", "Position x"),
                ("y", "INTEGER", "Position y"),
                ("verrouillageX", "INTEGER", "Verrouillage X (0/1)"),
                ("verrouillageY", "INTEGER", "Verrouillage Y (0/1)"),
                ("Xmodifiable", "INTEGER", "Position X est modifiable (0/1)"),
                ("Ymodifiable", "INTEGER", "Position Y est modifiable (0/1)"),
                ("largeur", "INTEGER", "Largeur de l'objet"),
                ("hauteur", "INTEGER", "Hauteur de l'objet"),
                ("largeurModifiable", "INTEGER", "Largeur modifiable (0/1)"),
                ("hauteurModifiable", "INTEGER", "Hauteur modifiable (0/1)"),
                ("largeurMin", "INTEGER", "Largeur min"),
                ("largeurMax", "INTEGER", "Largeur max"),
                ("hauteurMin", "INTEGER", "Hauteur min"),
                ("hauteurMax", "INTEGER", "Hauteur max"),
                ("verrouillageLargeur", "INTEGER", "Hauteur verrouillée (0/1)"),
                ("verrouillageHauteur", "INTEGER", "Hauteur verrouillée (0/1)"),
                ("verrouillageProportions", "INTEGER", "Proportion verrouillée (0/1)"),
                ("interditModifProportions", "INTEGER", "Modification proportions interdite (0/1)"),
                ("couleurTrait", "VARCHAR(100)", "Couleur du trait"),
                ("styleTrait", "VARCHAR(100)", "Style du trait"),
                ("epaissTrait", "FLOAT", "Epaisseur du trait"),
                ("coulRemplis", "VARCHAR(100)", "Couleur du remplissage"),
                ("styleRemplis", "VARCHAR(100)", "Style du remplissage"),
                ("couleurTexte", "VARCHAR(100)", "Couleur du texte"),
                ("couleurFond", "VARCHAR(100)", "Couleur du fond"),
                ("padding", "FLOAT", "Padding du texte"),
                ("interligne", "FLOAT", "Interligne"),
                ("taillePolice", "INTEGER", "Taille de la police"),
                ("nomPolice", "VARCHAR(100)", "Nom de la police"),
                ("familyPolice", "INTEGER", "Famille de la police"),
                ("stylePolice", "INTEGER", "Style de la police"),
                ("weightPolice", "INTEGER", "weight de la police"),
                ("soulignePolice", "INTEGER", "Texte souligné (0/1)"),
                ("alignement", "VARCHAR(100)", "Alignement du texte"),
                ("largeurTexte", "INTEGER", "Largeur du bloc de texte"),
                ("norme", "VARCHAR(100)", "Norme code-barres"),
                ("afficheNumero", "INTEGER", "Affiche numéro code-barres"),
                ("IDdonnee", "INTEGER", "Donnée associée pour zone interactive"),
                ], # Objets des modèles de documents
    
    "questionnaire_categories": [("IDcategorie", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID"),
                ("ordre", "INTEGER", "Ordre"),
                ("visible", "INTEGER", "Visible (0/1)"),
                ("type", "VARCHAR(100)", "Individu ou Famille"),
                ("couleur", "VARCHAR(100)", "Couleur de la catégorie"),
                ("label", "VARCHAR(400)", "Label de la question"),
                ], # Catégories des questionnaires
    
    "questionnaire_questions": [("IDquestion", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID"),
                ("IDcategorie", "INTEGER", "ID de la catégorie"),
                ("ordre", "INTEGER", "Ordre"),
                ("visible", "INTEGER", "Visible (0/1)"),
                ("label", "VARCHAR(400)", "Label de la question"),
                ("controle", "VARCHAR(200)", "Nom du contrôle"),
                ("defaut", "VARCHAR(400)", "Valeur par défaut"),
                ("options", "VARCHAR(400)", "Options de la question"),
                ], # Questions des questionnaires
    
    "questionnaire_choix": [("IDchoix", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID"),
                ("IDquestion", "INTEGER", "ID de la question rattachée"),
                ("ordre", "INTEGER", "Ordre"),
                ("visible", "INTEGER", "Visible (0/1)"),
                ("label", "VARCHAR(400)", "Label de la question"),
                ], # Choix de réponses des questionnaires
    
    "questionnaire_reponses": [("IDreponse", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID"),
                ("IDquestion", "INTEGER", "ID de la question rattachée"),
                ("IDindividu", "INTEGER", "ID de l'individu rattaché"),
                ("IDfamille", "INTEGER", "ID de la famille rattachée"),
                ("reponse", "VARCHAR(400)", "Réponse"),
                ("type", "VARCHAR(100)", "Type : Individu ou Famille, etc..."),
                ("IDdonnee", "INTEGER", "ID de la donnée rattachée (IDindividu, IDfamille, etc...)"),
                ], # Réponses des questionnaires
    
    "questionnaire_filtres": [("IDfiltre", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID"),
                ("IDquestion", "INTEGER", "ID de la question rattachée"),
                ("categorie", "VARCHAR(100)", "Catégorie (ex: 'TARIF')"),
                ("choix", "VARCHAR(400)", "Choix (ex : 'EGAL'"),
                ("criteres", "VARCHAR(600)", "Criteres (ex : '4;5')"),
                ("IDtarif", "INTEGER", "IDtarif rattaché"),
                ("IDdonnee", "INTEGER", "ID de la donnée rattachée)"),
                ], # Filtres des questionnaires
    
    "niveaux_scolaires":  [("IDniveau", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID"),
                ("ordre", "INTEGER", "Ordre"),
                ("nom", "VARCHAR(400)", "Nom du niveau (ex : Cours préparatoire)"),
                ("abrege", "VARCHAR(200)", "Abrégé du niveau (ex : CP)"),
                ], # Niveaux scolaires
    
    "ecoles":[                  ("IDecole", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID Ecole"),
                ("nom", "VARCHAR(300)", "Nom du restaurateur"),
                ("rue", "VARCHAR(200)", "Adresse"),
                ("cp", "VARCHAR(10)", "Code postal"),
                ("ville", "VARCHAR(200)", "Ville"),  
                ("tel", "VARCHAR(50)", "Tel"),  
                ("fax", "VARCHAR(50)", "Fax"),  
                ("mail", "VARCHAR(100)", "Email"),  
                ("secteurs", "VARCHAR(200)", "Liste des IDsecteur"),  
                ], # Ecoles
    
    "classes":[                ("IDclasse", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID Classe"),
                ("IDecole", "INTEGER", "ID de l'école"),
                ("nom", "VARCHAR(400)", "Nom de la classe"),
                ("date_debut", "DATE", "Date de début de période"),
                ("date_fin", "DATE", "Date de fin de période"),
                ("niveaux", "VARCHAR(300)", "Liste des niveaux scolaires de la classe"),  
                ], # Classes
    
    "scolarite":[               ("IDscolarite", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID Scolarite"),
                ("IDindividu", "INTEGER", "ID de l'individu"),
                ("date_debut", "DATE", "Date de début de scolarité"),
                ("date_fin", "DATE", "Date de fin de scolarité"),
                ("IDecole", "INTEGER", "ID de l'école"),
                ("IDclasse", "INTEGER", "ID de la classe"),
                ("IDniveau", "INTEGER", "ID du niveau scolaire"),
                ], # Scolarité
    
    "transports_compagnies":[("IDcompagnie", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID Compagnie"),
                ("categorie", "VARCHAR(200)", "Catégorie de la compagnie (taxi,train,avion,etc...)"),
                ("nom", "VARCHAR(300)", "Nom de la compagnie"),
                ("rue", "VARCHAR(200)", "Rue"),
                ("cp", "VARCHAR(10)", "Code postal"),
                ("ville", "VARCHAR(200)", "Ville"),  
                ("tel", "VARCHAR(50)", "Tél"),  
                ("fax", "VARCHAR(50)", "Fax"),  
                ("mail", "VARCHAR(100)", "Email"),  
                ], # Compagnies de transport
    
    "transports_lieux":[    ("IDlieu", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID Lieu"),
                ("categorie", "VARCHAR(200)", "Catégorie du lieu (gare,aeroport,port,station)"),
                ("nom", "VARCHAR(300)", "Nom du lieu"),
                ("cp", "VARCHAR(10)", "Code postal"),
                ("ville", "VARCHAR(200)", "Ville"),  
                ], # Lieux pour les transports
    
    "transports_lignes":[   ("IDligne", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID Ligne"),
                ("categorie", "VARCHAR(200)", "Catégorie de la ligne (bus, car, métro, etc...)"),
                ("nom", "VARCHAR(300)", "Nom de la ligne"),
                ], # Lignes régulières pour les transports
    
    "transports_arrets":[   ("IDarret", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID Arrêt"),
                ("IDligne", "INTEGER", "ID de la ligne"),
                ("ordre", "INTEGER", "Ordre"),
                ("nom", "VARCHAR(300)", "Nom de l'arrêt"),
                ], # Arrêts des lignes régulières pour les transports
    
    "transports":[
                ("IDtransport", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID Transport"),
                ("IDindividu", "INTEGER", "ID Individu"),
                ("mode", "VARCHAR(100)", "Mode : TRANSP | PROG | MODELE"),
                ("categorie", "VARCHAR(100)", "Catégorie du moyen de locomotion"),
                ("IDcompagnie", "INTEGER", "ID Compagnie"),
                ("IDligne", "INTEGER", "ID Ligne"),
                ("numero", "VARCHAR(200)", "Numéro du vol ou du train"),
                ("details", "VARCHAR(300)", "Détails"),
                ("observations", "VARCHAR(400)", "Observations"),
                ("depart_date", "DATE", "Date du départ"),
                ("depart_heure", "DATE", "Heure du départ"),
                ("depart_IDarret", "INTEGER", "ID Arrêt du départ"),
                ("depart_IDlieu", "INTEGER", "ID Lieu du départ"),
                ("depart_localisation", "VARCHAR(400)", "Localisation du départ"),
                ("arrivee_date", "DATE", "Date de l'arrivée"),
                ("arrivee_heure", "DATE", "Heure de l'arrivée"),
                ("arrivee_IDarret", "INTEGER", "ID Arrêt de l'arrivée"),
                ("arrivee_IDlieu", "INTEGER", "ID Lieu de l'arrivée"),
                ("arrivee_localisation", "VARCHAR(400)", "Localisation de l'arrivée"),
                ("date_debut", "DATE", "Date de début"),
                ("date_fin", "DATE", "Date de fin"),
                ("actif", "INTEGER", "Actif (1/0)"),
                ("jours_scolaires", "VARCHAR(100)", "Jours scolaires"),
                ("jours_vacances", "VARCHAR(100)", "Jours de vacances"),
                ("unites", "VARCHAR(480)", "Liste des unités de conso rattachées"),
                ("prog", "INTEGER", "IDtransport du modèle de programmation"),
                ], # Transports
    
    "etat_nomin_champs":[("IDchamp", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID Champ"),
                ("code", "VARCHAR(300)", "Code du champ"),
                ("label", "VARCHAR(400)", "Nom du champ"),
                ("formule", "VARCHAR(450)", "Formule"),
                ("titre", "VARCHAR(400)", "Titre"),
                ], # Champs personnalisés pour Etat Caisse nominatif
    
    "etat_nomin_selections":[("IDselection", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID Sélection"),
                ("IDprofil", "VARCHAR(400)", "Nom de profil"),
                ("code", "VARCHAR(300)", "Code du champ"),
                ("ordre", "INTEGER", "Ordre"),
                ], # Sélection des Champs personnalisés pour Etat Nominatif
    
    "etat_nomin_profils":[("IDprofil", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID Profil"),
                ("label", "VARCHAR(400)", "Nom de profil"),
                ], # Profils pour Etat Caisse nominatif
    
    "badgeage_actions":   [("IDaction", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID Action"),
                ("IDprocedure", "INTEGER", "IDprocedure"),
                ("ordre", "INTEGER", "Ordre"),
                ("condition_activite", "VARCHAR(400)", "Activité"),
                ("condition_heure", "VARCHAR(400)", "Heure"),
                ("condition_periode", "VARCHAR(400)", "Période"),
                ("condition_poste", "VARCHAR(400)", "Poste réseau"),
                ("condition_questionnaire", "VARCHAR(490)", "Questionnaire"),
                ("action", "VARCHAR(400)", "Code de l'action"),
                ("action_activite", "VARCHAR(450)", "Activité"),
                ("action_unite", "VARCHAR(450)", "Unités"),
                ("action_etat", "VARCHAR(400)", "Etat de la conso"),
                ("action_demande", "VARCHAR(40)", "Demande si début ou fin"),
                ("action_heure_debut", "VARCHAR(450)", "Heure de début"),
                ("action_heure_fin", "VARCHAR(450)", "Heure de fin"),
                ("action_message", "VARCHAR(450)", "Message unique"),
                ("action_icone", "VARCHAR(400)", "Icone pour boite de dialogue"),
                ("action_duree", "VARCHAR(50)", "Durée d'affichage du message"),
                ("action_frequence", "VARCHAR(450)", "Frequence diffusion message"),
                ("action_vocal", "VARCHAR(400)", "Synthese vocale activation"),
                ("action_question", "VARCHAR(450)", "Question"),
                ("action_date", "VARCHAR(450)", "Date à proposer"),
                ("action_attente", "VARCHAR(450)", "Proposer attente"),
                ("action_ticket", "VARCHAR(450)", "Impression_ticket"),
                ], # Badgeage : Actions
    
    "badgeage_messages":[("IDmessage", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID Message"),
                ("IDprocedure", "INTEGER", "IDprocedure"),
                ("IDaction", "INTEGER", "IDaction rattachée"),
                ("message", "VARCHAR(480)", "Texte du message"),
                ], # Badgeage : Messages pour Actions
    
    "badgeage_procedures":[("IDprocedure", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID Procédure"),
                ("nom", "VARCHAR(450)", "Nom"),
                ("defaut", "INTEGER", "Défaut (0/1)"),
                ("style", "VARCHAR(400)", "Style interface"),
                ("theme", "VARCHAR(400)", "Thème interface"),
                ("image", "VARCHAR(400)", "Image personnalisée pour thème"),
                ("systeme", "VARCHAR(400)", "Système de saisie"),
                ("activites", "VARCHAR(400)", "Liste ID activites pour saisie par liste d'individus"),
                ("confirmation", "INTEGER", "Confirmation identification (0/1)"),
                ("vocal", "INTEGER", "Activation synthèse vocale (0/1)"),
                ("tutoiement", "INTEGER", "Activation du tutoiement dans les messages (0/1)"),
                ], #  Badgeage : Procédures
    
    "badgeage_journal":[ ("IDaction", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID Action"),
                ("date", "DATE", "Date de l'action"),
                ("heure", "VARCHAR(50)", "Heure"),
                ("IDindividu", "INTEGER", "ID de l'individu"),
                ("individu", "VARCHAR(450)", "Nom de l'individu"),
                ("action", "VARCHAR(450)", "Action réalisée"),
                ("resultat", "VARCHAR(450)", "Résultat de l'action"),
                ], #  Badgeage : Journal
    
    "badgeage_archives":[ ("IDarchive", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID Archive"),
                ("date_archivage", "DATE", "Date de l'archivage"),
                ("codebarres", "VARCHAR(200)", "Code-barres"),
                ("date", "DATE", "Date badgée"),
                ("heure", "VARCHAR(50)", "Heure badgée"),
                ], #  Badgeage : Archives des importations
    
    "corrections_phoniques":[("IDcorrection", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID Correction"),
                ("mot", "VARCHAR(400)", "Mot à corriger"),
                ("correction", "VARCHAR(400)", "Correction phonique"),
                ], # Corrections phoniques pour la synthèse vocale
    
    "corrections_villes":[("IDcorrection", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID Correction"),
                ("mode", "VARCHAR(100)", "Mode de correction"),
                ("IDville", "INTEGER", "ID ville"),
                ("nom", "VARCHAR(450)", "Nom de la ville"),
                ("cp", "VARCHAR(100)", "Code postal"),
                ("pays", "VARCHAR(48)", "Pays postal correspond au secteur"),
                ], # Personnalisation des villes et codes postaux
    
    "modeles_emails":[ ("IDmodele", "INTEGER PRIMARY KEY AUTOINCREMENT", "IDmodele"),
                ("categorie", "VARCHAR(455)", "Catégorie du modèle"),
                ("nom", "VARCHAR(455)", "Nom du modèle"),
                ("description", "VARCHAR(455)", "Description du modèle"),
                ("objet", "VARCHAR(455)", "Texte objet du mail"),
                ("texte_xml", "VARCHAR(25000)", "Contenu du texte version XML"),
                ("IDadresse", "INTEGER", "IDadresse d'expédition de mails"),
                ("defaut", "INTEGER", "Modèle par défaut (0/1)"),
                ], # Modèles d'Emails
    
    "banques":[                ("IDbanque", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID de la banque"),
                ("nom", "VARCHAR(100)", "Nom de la banque"),
                ("rue_resid", "VARCHAR(255)", "Adresse de la banque"),
                ("cp_resid", "VARCHAR(10)", "Code postal de la banque"),
                ("ville_resid", "VARCHAR(100)", "Ville de la banque"),  
                ], # Les établissements bancaires pour le prélèvement automatique
    
    "lots_factures":[         ("IDlot", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID lot de factures"),
                ("nom", "VARCHAR(400)", "Nom du lot"),
                ], # Lots de factures
    
    "lots_rappels":[         ("IDlot", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID lot de rappels"),
                ("nom", "VARCHAR(400)", "Nom du lot"),
                ], # Lots de rappels
    
    "prelevements":[         ("IDprelevement", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID prélèvement"),
                ("IDlot", "INTEGER", "ID du lot de prélèvements"),
                ("IDfamille", "INTEGER", "ID de la famille destinataire"),
                ("prelevement_etab", "VARCHAR(50)", "Prélèvement - Code étab"),
                ("prelevement_guichet", "VARCHAR(50)", "Prélèvement - Code guichet"),
                ("prelevement_numero", "VARCHAR(50)", "Prélèvement - Numéro de compte"),
                ("prelevement_banque", "INTEGER", "Prélèvement - ID de la Banque"),
                ("prelevement_cle", "VARCHAR(50)", "Prélèvement - Code clé"),
                ("prelevement_iban", "VARCHAR(100)", "Prélèvement - Clé IBAN"),
                ("prelevement_bic", "VARCHAR(100)", "Prélèvement - BIC"),
                ("prelevement_reference_mandat", "VARCHAR(300)", "Prélèvement - Référence mandat"),
                ("prelevement_date_mandat", "DATE", "Prélèvement - Date mandat"),
                ("titulaire", "VARCHAR(400)", "Titulaire du compte"),
                ("type", "VARCHAR(400)", "Type du prélèvement"),
                ("IDfacture", "INTEGER", "ID de la facture"),
                ("libelle", "VARCHAR(400)", "Libellé du prélèvement"),
                ("montant", "FLOAT", "Montant du prélèvement"),
                ("statut", "VARCHAR(100)", "Statut du prélèvement"),
                ("IDmandat", "INTEGER", "ID du mandat"),
                ("sequence", "VARCHAR(100)", "Séquence SEPA"),
                ], # Prélèvement
    
    "lots_prelevements":[  ("IDlot", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID du lot de prélèvement"),
                ("nom", "VARCHAR(200)", "Nom du lot de prélèvements"),
                ("date", "DATE", "Date du prélèvement"),
                ("verrouillage", "INTEGER", "(0/1) Verrouillage du lot"),
                ("IDcompte", "INTEGER", "ID du compte créditeur"),
                ("IDmode", "INTEGER", "ID du mode de règlement"),
                ("reglement_auto", "INTEGER", "Règlement automatique (0/1)"),
                ("observations", "VARCHAR(500)", "Observations"),
                ("type", "VARCHAR(100)", "Type (national ou SEPA)"),
                ("format", "VARCHAR(200)", "Format du prélèvement"),
                ("encodage", "VARCHAR(200)", "Encodage du fichier"),
                ("IDperception", "INTEGER", "ID de la perception"),
                ("motif", "VARCHAR(300)", "Motif du prélèvement"),
                ("identifiant_service", "VARCHAR(200)", "Identifiant du service"),
                ("poste_comptable", "VARCHAR(200)", "Poste comptable ou codique"),
                ], # Lots de prélèvements
    
    "modeles_tickets":[ ("IDmodele", "INTEGER PRIMARY KEY AUTOINCREMENT", "IDmodele"),
                ("categorie", "VARCHAR(455)", "Catégorie du modèle"),
                ("nom", "VARCHAR(455)", "Nom du modèle"),
                ("description", "VARCHAR(455)", "Description du modèle"),
                ("lignes", "VARCHAR(5000)", "lignes du ticket"),
                ("defaut", "INTEGER", "Modèle par défaut (0/1)"),
                ("taille", "INTEGER", "Taille de police"),
                ("interligne", "INTEGER", "Hauteur d'interligne"),
                ("imprimante", "VARCHAR(455)", "Nom de l'imprimante"),
                ], # Modèles de tickets
    
    "sauvegardes_auto":[ ("IDsauvegarde", "INTEGER PRIMARY KEY AUTOINCREMENT", "IDsauvegarde"),
                ("nom", "VARCHAR(455)", "Nom de la procédure de sauvegarde auto"),
                ("observations", "VARCHAR(455)", "Observations"),
                ("date_derniere", "DATE", "Date de la dernière sauvegarde"),
                ("sauvegarde_nom", "VARCHAR(455)", "Sauvegarde Nom"),
                ("sauvegarde_motdepasse", "VARCHAR(455)", "Sauvegarde mot de passe"),
                ("sauvegarde_repertoire", "VARCHAR(455)", "sauvegarde Répertoire"),
                ("sauvegarde_emails", "VARCHAR(455)", "Sauvegarde Emails"),
                ("sauvegarde_fichiers_locaux", "VARCHAR(455)", "Sauvegarde fichiers locaux"),
                ("sauvegarde_fichiers_reseau", "VARCHAR(455)", "Sauvegarde fichiers réseau"),
                ("condition_jours_scolaires", "VARCHAR(455)", "Condition Jours scolaires"),
                ("condition_jours_vacances", "VARCHAR(455)", "Condition Jours vacances"),
                ("condition_heure", "VARCHAR(455)", "Condition Heure"),
                ("condition_poste", "VARCHAR(455)", "Condition Poste"),
                ("condition_derniere", "VARCHAR(455)", "Condition Date dernière sauvegarde"),
                ("condition_utilisateur", "VARCHAR(455)", "Condition Utilisateur"),
                ("option_afficher_interface", "VARCHAR(455)", "Option Afficher interface (0/1)"),
                ("option_demander", "VARCHAR(455)", "Option Demander (0/1)"),
                ("option_confirmation", "VARCHAR(455)", "Option Confirmation (0/1)"),
                ("option_suppression", "VARCHAR(455)", "Option Suppression sauvegardes obsolètes"),
                ], # procédures de sauvegardes automatiques
    
    "droits":[                   ("IDdroit", "INTEGER PRIMARY KEY AUTOINCREMENT", "IDdroit"),
                ("IDutilisateur", "INTEGER", "IDutilisateur"),
                ("IDmodele", "INTEGER", "IDmodele"),
                ("categorie", "VARCHAR(200)", "Categorie de droits"),
                ("action", "VARCHAR(200)", "Type action"),
                ("etat", "VARCHAR(455)", "Etat"),
                ], # Droits des utilisateurs
    
    "modeles_droits":[     ("IDmodele", "INTEGER PRIMARY KEY AUTOINCREMENT", "IDmodele"),
                ("nom", "VARCHAR(455)", "Nom du modèle"),
                ("observations", "VARCHAR(455)", "Observations"),
                ("defaut", "INTEGER", "Modèle par défaut (0/1)"),
                ], # Modèles de droits
    
    "mandats":[               ("IDmandat", "INTEGER PRIMARY KEY AUTOINCREMENT", "IDmandat"),
                ("IDfamille", "INTEGER", "Famille rattachée"),
                ("rum", "VARCHAR(100)", "RUM du mandat"),
                ("type", "VARCHAR(100)", "Type de mandat (récurrent ou ponctuel)"),
                ("date", "DATE", "Date de signature du mandat"),
                ("IDbanque", "INTEGER", "ID de la banque"),
                ("IDindividu", "INTEGER", "ID de l'individu"),
                ("individu_nom", "VARCHAR(400)", "Nom du titulaire de compte"),
                ("individu_rue", "VARCHAR(400)", "Rue du titulaire de compte"),
                ("individu_cp", "VARCHAR(50)", "CP du titulaire de compte"),
                ("individu_ville", "VARCHAR(400)", "Ville du titulaire de compte"),
                ("iban", "VARCHAR(100)", "IBAN"),
                ("bic", "VARCHAR(100)", "BIC"),
                ("memo", "VARCHAR(450)", "Mémo"),
                ("sequence", "VARCHAR(100)", "Prochaine séquence"),
                ("actif", "INTEGER", "actif (0/1)"),
                ], # Mandats SEPA
    
    "pes_pieces":[           ("IDpiece", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID piece"),
                ("IDlot", "INTEGER", "ID du lot PES"),
                ("IDfamille", "INTEGER", "ID de la famille destinataire"),
                ("prelevement", "INTEGER", "Prélèvement activé (0/1)"),
                ("prelevement_iban", "VARCHAR(100)", "IBAN"),
                ("prelevement_bic", "VARCHAR(100)", "BIC"),
                ("prelevement_rum", "VARCHAR(300)", "Référence Unique Mandat"),
                ("prelevement_date_mandat", "DATE", "Date mandat"),
                ("prelevement_IDmandat", "INTEGER", "ID du mandat"),
                ("prelevement_sequence", "VARCHAR(100)", "Séquence SEPA"),
                ("prelevement_titulaire", "VARCHAR(400)", "Titulaire du compte bancaire"),
                ("prelevement_statut", "VARCHAR(100)", "Statut du prélèvement"),
                ("titulaire_helios", "INTEGER", "Tiers Trésor public"),
                ("type", "VARCHAR(400)", "Type du prélèvement"),
                ("IDfacture", "INTEGER", "ID de la facture"),
                ("numero", "INTEGER", "Numéro de facture"),
                ("libelle", "VARCHAR(400)", "Libellé de la pièce"),
                ("montant", "FLOAT", "Montant du prélèvement"),
                ], # Pièces PESV2 ORMC
    
    "pes_lots":[               ("IDlot", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID du lot"),
                ("nom", "VARCHAR(200)", "Nom du lot"),
                ("verrouillage", "INTEGER", "(0/1) Verrouillage du lot"),
                ("observations", "VARCHAR(500)", "Observations"),
                ("reglement_auto", "INTEGER", "Règlement automatique (0/1)"),
                ("IDcompte", "INTEGER", "ID du compte créditeur"),
                ("IDmode", "INTEGER", "ID du mode de règlement"),
                ("exercice", "INTEGER", "Exercice"),
                ("mois", "INTEGER", "Numéro de mois"),
                ("objet_dette", "VARCHAR(450)", "Objet de la dette"),
                ("date_emission", "DATE", "Date d'émission"),
                ("date_prelevement", "DATE", "Date du prélèvement"),
                ("date_envoi", "DATE", "Date d'avis d'envoi"),
                ("id_bordereau", "VARCHAR(200)", "Identifiant bordereau"),
                ("id_poste", "VARCHAR(200)", "Poste comptable"),
                ("id_collectivite", "VARCHAR(200)", "ID budget collectivité"),
                ("code_collectivite", "VARCHAR(200)", "Code Collectivité"),
                ("code_budget", "VARCHAR(200)", "Code Budget"),
                ("code_prodloc", "VARCHAR(200)", "Code Produit Local"),
                ("code_etab", "VARCHAR(100)", "Code Etablissement"),
                ("prelevement_libelle", "VARCHAR(450)", "Libellé du prélèvement"),
                ("objet_piece", "VARCHAR(450)", "Objet de la pièce"),
                ("format", "VARCHAR(100)", "Format du lot"),
                ("options", "VARCHAR(1000)", "Options diverses"),
                ], # Lots PESV2 ORMC
    
    "contrats":[               ("IDcontrat", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID contrat"),
                ("IDindividu", "INTEGER", "ID de l'individu"),
                ("IDinscription", "INTEGER", "ID de l'inscription"),
                ("date_debut", "DATE", "Date de début"),
                ("date_fin", "DATE", "Date de fin"),
                ("observations", "VARCHAR(500)", "Observations"),
                ("IDtarif", "INTEGER", "ID du tarif"),
                ("IDactivite", "INTEGER", "ID de l'activité"),
                ("type", "VARCHAR(100)", "Type de contrat"),
                ("nbre_absences_prevues", "INTEGER", "Nombre d'absences prévues PSU"),
                ("nbre_heures_regularisation", "INTEGER", "Nombre d'heures de régularisation PSU"),
                ("arrondi_type", "VARCHAR(50)", "Type d'arrondi sur les heures"),
                ("arrondi_delta", "INTEGER", "Delta en minutes de l'arrondi sur les heures"),
                ("duree_absences_prevues", "VARCHAR(50)", "Temps d'absences prévues PSU"),
                ("duree_heures_regularisation", "VARCHAR(50)", "Temps de régularisation PSU"),
                ("duree_tolerance_depassement", "VARCHAR(50)", "Temps de tolérance dépassements PSU"),
                ("planning", "VARCHAR(900)", "Données de planning serialisées"),
                ], # Contrats
    
    "modeles_contrats":[ ("IDmodele", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID modèle"),
                ("nom", "VARCHAR(450)", "Nom du modèle"),
                ("IDactivite", "INTEGER", "ID de l'activité"),
                ("date_debut", "DATE", "Date de début"),
                ("date_fin", "DATE", "Date de fin"),
                ("observations", "VARCHAR(500)", "Observations"),
                ("IDtarif", "INTEGER", "ID du tarif"),
                ("donnees", "LONGBLOB", "Données en binaire"),
                ], # Modèles de contrats
    
    "modeles_plannings":[("IDmodele", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID modèle"),
                ("IDactivite", "INTEGER", "ID de l'activités concernée"),
                ("nom", "VARCHAR(450)", "Nom du modèle"),
                ("donnees", "VARCHAR(900)", "Données serialisées"),
                ], # Modèles de plannings
    
    "compta_operations":[("IDoperation", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID opération"),
                ("type", "VARCHAR(200)", "Type de données (debit/crédit)"),
                ("date", "DATE", "Date de l'opération"),
                ("libelle", "VARCHAR(400)", "Libellé de l'opération"),
                ("IDtiers", "INTEGER", "ID du tiers"),
                ("IDmode", "INTEGER", "ID du mode de règlement"),
                ("num_piece", "VARCHAR(200)", "Numéro de pièce"),
                ("ref_piece", "VARCHAR(200)", "Référence de la pièce"),
                ("IDcompte_bancaire", "INTEGER", "ID du compte bancaire"),
                ("IDreleve", "INTEGER", "ID du relevé bancaire"),
                ("montant", "FLOAT", "Montant de l'opération"),
                ("observations", "VARCHAR(450)", "Observations"),
                ("IDvirement", "INTEGER", "IDvirement associé"),
                ], # Compta : Opérations
    
    "compta_virements":[ ("IDvirement", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID virement"),
                ("IDoperation_debit", "INTEGER", "ID opération débiteur"),
                ("IDoperation_credit", "INTEGER", "ID opération créditeur"),
                ], # Compta : Virements
    
    "compta_ventilation":[("IDventilation", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID ventilation"),
                ("IDoperation", "INTEGER", "ID de l'opération"),
                ("IDexercice", "INTEGER", "ID de l'exercice"),
                ("IDcategorie", "INTEGER", "ID de la catégorie"),
                ("IDanalytique", "INTEGER", "ID du poste analytique"),
                ("libelle", "VARCHAR(400)", "Libellé de la ventilation"),
                ("montant", "FLOAT", "Montant de la ventilation"),
                ("date_budget", "DATE", "Date d'impact budgétaire"),
                ], # Compta : Ventilation des opérations
                
    "compta_exercices":[("IDexercice", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID Exercice"),
                ("nom", "VARCHAR(400)", "Nom de l'exercice"),
                ("date_debut", "DATE", "Date de début"),
                ("date_fin", "DATE", "Date de fin"),
                ("defaut", "INTEGER", "Défaut (0/1)"),
                ("actif", "INTEGER", "Actif pour écritures nouvelles (0/1)"),
                ("cloture", "INTEGER", "Clôturé, ne peut plus être actif(0/1)"),
                ], # Compta : Exercices
    
    
    "compta_analytiques":[("IDanalytique", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID Analytique"),
                ("nom", "VARCHAR(400)", "Nom du poste analytique"),
                ("abrege", "VARCHAR(200)", "Abrégé du poste analytique"),
                ("defaut", "INTEGER", "Défaut (0/1)"),
                ], # Compta : Postes analytiques
    
    "compta_categories":            [("IDcategorie", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID Catégorie"),
                ("type", "VARCHAR(200)", "Type de données (debit/crédit)"),
                ("nom", "VARCHAR(400)", "Nom de la catégorie"),
                ("abrege", "VARCHAR(200)", "Abrégé de la catégorie"),
                ("journal", "VARCHAR(200)", "Code journal"),
                ("IDcompte", "INTEGER", "ID du compte comptable"),
                ], # Compta : Catégories de ventilation
    
    "compta_comptes_comptables":    [("IDcompte", "INTEGER PRIMARY KEY AUTOINCREMENT", "IDcompte"),
                ("numero", "VARCHAR(200)", "Numéro"),
                ("nom", "VARCHAR(400)", "Nom du code"),
                ], # Compta : Comptes comptables
    
    "compta_tiers":                 [("IDtiers", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID Tiers"),
                ("nom", "VARCHAR(400)", "Nom du tiers"),
                ("observations", "VARCHAR(450)", "Observations"),
                ("IDcode_comptable", "INTEGER", "ID du code comptable"),
                ], # Compta : Tiers
    
    "compta_budgets":               [("IDbudget", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID Budget"),
                ("IDexercice", "INTEGER", "ID de l'exercice"),
                ("nom", "VARCHAR(400)", "Nom du budget"),
                ("observations", "VARCHAR(200)", "Observations sur le budget"),
                ("analytiques", "VARCHAR(450)", "Liste des postes analytiques associés"),
                ("date_debut", "DATE", "Date de début de période"),
                ("date_fin", "DATE", "Date de fin de période"),
                ], # Compta : Budgets
    
    "compta_categories_budget":     [("IDcategorie_budget", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID Categorie budget"),
                ("IDbudget", "INTEGER", "ID du budget"),
                ("type", "VARCHAR(200)", "Type de données (debit/crédit)"),
                ("IDcategorie", "INTEGER", "ID de la catégorie rattachée"),
                ("valeur", "VARCHAR(450)", "Valeur ou formule"),
                ], # Compta : Catégories de budget
    
    "compta_releves":               [("IDreleve", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID Relevé"),
                ("nom", "VARCHAR(400)", "Nom du relevé"),
                ("date_debut", "DATE", "Date de début"),
                ("date_fin", "DATE", "Date de fin"),
                ("IDcompte_bancaire", "INTEGER", "ID du compte bancaire"),
                ], # Compta : Relevés de comptes
    
    "compta_operations_budgetaires":[("IDoperation_budgetaire", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID opération budgétaire"),
                ("type", "VARCHAR(200)", "Type de données (debit/crédit)"),
                ("date_budget", "DATE", "Date d'impact budgétaire"),
                ("IDcategorie", "INTEGER", "ID de la catégorie"),
                ("IDanalytique", "INTEGER", "ID du poste analytique"),
                ("libelle", "VARCHAR(400)", "Libellé de la ventilation"),
                ("montant", "FLOAT", "Montant de la ventilation"),
                ], # Compta : Ventilation des opérations
    
    "nomade_archivage":             [("IDarchive", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID Archive"),
                ("nom_fichier", "VARCHAR(400)", "Nom du fichier"),
                ("ID_appareil", "VARCHAR(100)", "ID de l'appareil"),
                ("date", "DATE", "Date de l'archivage"),
                ], # Synchronisation Nomadhys : Archivage des fichiers
    
    "etiquettes":                   [("IDetiquette", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID Etiquette"),
                ("label", "VARCHAR(300)", "Label de l'étiquette"),
                ("IDactivite", "INTEGER", "ID de l'activité"),
                ("parent", "INTEGER", "Parent de l'étiquette"),
                ("ordre", "INTEGER", "Ordre"),
                ("couleur", "VARCHAR(30)", "Couleur de l'étiquette"),
                ("active", "INTEGER", "Etiquette active (0/1)"),
                ], # Etiquettes de consommations

    "matTarifs":        [
        ("trfIDactivite", "INTEGER", "noethys.activites.IDactivite"),
        ("trfIDgroupe", "INTEGER", "noethys.groupe.IDgroupe"),
        ("trfIDcategorie_tarif", "INTEGER", "noethys.categorie_tarifs.IDcategorie_tarif"),
        ("trfCodeTarif", "VARCHAR(16)", "matTarifsNoms.trnCodeTarif"),
        ("trfPrix", "FLOAT", "Prix de base pour calcul du montant"),
        ("trfCumul","INTEGER" , "Exclu de la réduction cumul car prix faible"),
    ],  # fin de matTarifs, affectations des tarifs
    "matTarifsNoms":    [
        ("trnCodeTarif", "VARCHAR(16)", "matTarifs.trfCodeTarif"),
        ("trnLibelle", "VARCHAR(128)", "Nom du tarif"),
    ],  # fin de matTarifsNoms, libellés des tarifs
    "matTarifsLignes":  [
        ("trlCodeTarif", "VARCHAR(16)", "Code tarif"),
        ("trlNoLigne", "INTEGER", "Ordre"),
        ("trlCodeArticle", "VARCHAR(16)", "Référence article"),
        ("trlPreCoche", "INTEGER", "Précoché dans la proposition"),
    ],  # fin de matTarifsLignes, composition des tarifs
    "matArticles":      [
        ("artCodeArticle", "VARCHAR(16)", "ID_Article"),
        ("artLibelle", "VARCHAR(128)", "Nom de l'article"),
        ("artConditions", "VARCHAR(16)", "Condition de blocage ou d'alerte"),
        ("artModeCalcul", "VARCHAR(16)",
         "Calcul pour générer des lignes, peut modifier le libellé, et propose une quantité et un prix en fonction du context"),
        ("artPrix1", "FLOAT", "Prix de base actualisé chaque année"),
        ("artPrix2", "FLOAT", "Pour les cas ou un deuxième prix est nécessaire au calcul"),
        ("artCodeBlocFacture", "VARCHAR(16)",
         "matBlocsFactures.LFA_CodeBlocFacture      Pour Regroupement sur les lignes de facturation"),
        ("artCodeComptable", "VARCHAR(16)",
         "matPlanComptable.PCT_CodeComptable   Pour Regroupement dans la compta par l'intermédiaire d'une table naturecomptabl"),
        ("artNiveauFamille", "INTEGER", "Proposé au niveau famille"),
        ("artNiveauActivite", "INTEGER", "Proposé au niveau de l'inscription"),
    ],  # fin de matArticles, articles de facturation
    "matPlanComptable": [
        ("pctCodeComptable", "VARCHAR(16)", "Numero compte gescom"),
        ("pctLibelle", "VARCHAR(128)", "Désignation de la nature comptable"),
        ("pctCompte", "VARCHAR(16)", "Numéro de compte dans la compa"),
    ],  # fin de matPlanComptable, comptes
    "matPieces":        [
        ("pieIDnumPiece", "INTEGER PRIMARY KEY AUTOINCREMENT", "Numéro de pièce unique"),
        ("pieIDinscription", "INTEGER", "Ref inscription ou année pour un niveau famille"),
        ("pieIDprestation", "INTEGER", "Ref prestation récap"),
        ("pieIDindividu", "INTEGER", "Participant ou 999 pour un niveau famille"),
        ("pieIDfamille", "INTEGER", "Famille qui demande l'inscription"),
        ("pieIDcompte_payeur", "INTEGER", "Famille qui paye"),
        ("pieIDactivite", "INTEGER", "activité ou 1 pour la cotisation ou x pour autres pièces niveau famille"),
        ("pieIDgroupe", "INTEGER", "groupe"),
        ("pieIDcategorie_tarif", "INTEGER", "catégorie de tarification"),
        ("pieDateCreation", "DATE", "Date de Première action"),
        ("pieUtilisateurCreateur", "VARCHAR(32)", "Premier utilisateur"),
        ("pieDateModif", "DATE", "Date de dernière action"),
        ("pieUtilisateurModif", "VARCHAR(32)", "Dernier utilisateur"),
        ("pieNature", "VARCHAR(8)", "DEVis REServé COMmande FACture AVOir"),
        ("pieEtat", "VARCHAR(8)", "1=cree, 2=imprimé, 3=transféré 9=supprimé pour 5 positions nature"),
        ("pieDateFacturation", "DATE", "Date de la facture"),
        ("pieNoFacture", "INTEGER", "Numéro de la facture"),
        ("pieDateEcheance", "DATE", "DATE échéance"),
        ("pieDateAvoir", "DATE", "Date de l'annulation"),
        ("pieNoAvoir", "INTEGER", "Numéro d'avoir"),
        ("pieIDtranspAller", "INTEGER", "Ref transport aller"),
        ("piePrixTranspAller", "FLOAT", "Prix du transport aller"),
        ("pieIDtranspRetour", "INTEGER", "Ref transport retour"),
        ("piePrixTranspRetour", "FLOAT", "Prix du transport retour"),
        ("pieIDparrain", "INTEGER", "IDindividu du Parrain prescripteur de l'inscription"),
        ("pieParrainAbandon", "INTEGER", "1- Le Parrain abondonne son crédit au profit du filleul, 2- Neutralisé"),
        ("pieCommentaire", "BLOB", "Commentaire libre sur vie de la pièce"),
        ("pieComptaFac", "INTEGER", "Pointeur transfert en compta de la facture"),
        ("pieComptaAvo", "INTEGER", "Pointeur transfert en compta de l'avoir"),
    ],  # fin de matPieces, pièces pour ventes
    "matPiecesLignes":  [
        ("ligIDnumLigne", "INTEGER PRIMARY KEY AUTOINCREMENT", "Numéro de ligne pièce unique"),
        ("ligIDnumPiece", "INTEGER", "référence de la pièe"),
        ("ligDate", "DATE", "DATE de l'entrée de la ligne"),
        ("ligUtilisateur", "VARCHAR(32)", "dernier utilisateur"),
        ("ligCodeArticle", "VARCHAR(32)", "article"),
        ("ligLibelle", "VARCHAR(128)", "libellé article modifié"),
        ("ligQuantite", "FLOAT", "quantité"),
        ("ligPrixUnit", "FLOAT", "prix unitaire calculé origine"),
        ("ligMontant", "FLOAT", "Montant retenu"),
    ],  # fin de matPiecesLignes, détail des pièces
    "matParams":        [
        ("prmUser", "VARCHAR(16)", "Code de l'utilisateu"),
        ("prmParam", "VARCHAR(32)", "Code du paramètre pour l'appel"),
        ("prmInteger", "INTEGER", "Paramétre entier"),
        ("prmDate", "DATE", "Paramétre DATE"),
        ("prmString", "VARCHAR(128)", "Paramétre chaîne"),
        ("prmFloat", "FLOAT", "Paramétre Numérique réel"),
    ],  # fin de matParams, stockage alternatif
    "matParrainages":   [
        ("parIDinscription", "INTEGER", "Code ID inscription du filleul"),
        ("parIDligneParr", "INTEGER", "Code ID de la ligne de pièce imputaion de la réduc parrainage"),
        ("parSolde", "INTEGER", "7xxx forcé par opérateur xxx, 999 correction auto"),
        ("parAbandon", "INTEGER", "1 pour abandon au filleul lors de l'affectation"),
    ],  # fin de matParrainages, suivi des parrainages
    "matCerfas":        [
        ("crfIDcerfa", "INTEGER", "IDcerfa"),
        ("crfIDfamille", "INTEGER", "ID de la famille"),
        ("crfDateEdition", "DATE", "Date d'édition du cerfa"),
        ("crfIDutilisateur", "INTEGER", "Utilisateur qui a créé le cerfa"),
        ("crfDateDebut", "DATE", "Date de début des règlements"),
        ("crfDateFin", "DATE", "Date de fin des règlements"),
        ("crfTotal", "FLOAT", "Montant total du Cerfa pour contrôle"),
        ("crfCerfa", "BLOB", "Info complémentaire du Cerfa sous forme de dictionnaire"),
    ], # matCerfas, Stockage des cerfas édités
    "matCerfasLignes":  [
        ("crlIDcerfa", "INTEGER", "Numéro du cerfa"),
        ("crlIDprestation", "INTEGER", "ID de la prestation"),
        ("crlIDligne", "INTEGER", "ID de la ligne de la pièce"),
        ("crlReglements", "VARCHAR(256)", "liste des règlements de la prestation"),
        ("crlIDfamille", "INTEGER", "ID de la famille"),
        ("crlMontant", "FLOAT", "montant du don"),
        ], # matCerfasLignes, Lignes détail des cerfas

    "contrats_tarifs":              [("IDcontrat_tarif", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID contrat tarif"),
            ("IDcontrat", "INTEGER", "ID du contrat"),
            ("date_debut", "DATE", "Date de début de validité"),
            ("revenu", "FLOAT", "Revenu de la famille"),
            ("quotient", "INTEGER", "Quotient familial de la famille"),
            ("taux", "FLOAT", "Taux d'effort"),
            ("tarif_base", "FLOAT", "Montant du tarif de base"),
            ("tarif_depassement", "FLOAT", "Montant du tarif de dépassement"),
            ], # Tarifs de contrats

    "types_quotients":              [("IDtype_quotient", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID Type quotient"),
            ("nom", "VARCHAR(255)", "Nom du type de quotient"),
            ], # Types de quotients

    "factures_prefixes":            [("IDprefixe", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID préfixe facture"),
            ("nom", "VARCHAR(450)", "Nom du préfixe"),
            ("prefixe", "VARCHAR(100)", "Préfixe de facture"),
            ], # Préfixes de factures

    "factures_regies":              [("IDregie", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID régie de facturation"),
            ("nom", "VARCHAR(450)", "Nom de la régie"),
            ("numclitipi", "VARCHAR(50)", "Numéro de client TIPI"),
            ("email_regisseur", "VARCHAR(100)", "email du régisseur"),
            ("IDcompte_bancaire", "INTEGER", "ID du compte bancaire associé"),
            ], # RÃ©gies de facturation

    "portail_periodes":             [("IDperiode", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID période"),
            ("IDactivite", "INTEGER", "ID de l'activité"),
            ("nom", "VARCHAR(300)", "Nom de la période"),
            ("date_debut", "DATE", "Date de début de la période"),
            ("date_fin", "DATE", "Date de fin de la période"),
            ("affichage", "INTEGER", "Affiché sur le portail (0/1)"),
            ("affichage_date_debut", "DATETIME", "Date et heure de début d'affichage"),
            ("affichage_date_fin", "DATETIME", "Date et heure de fin d'affichage"),
            ("IDmodele", "INTEGER", "IDmodele d'email rattaché à la période"),
            ("introduction", "VARCHAR(1000)", "Texte d'introduction"),
            ("prefacturation", "INTEGER", "Préfacturation (0/1)"),
            ], # Périodes de réservations pour le portail

    "portail_unites":               [("IDunite", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID unité"),
            ("IDactivite", "INTEGER", "ID de l'activité"),
            ("nom", "VARCHAR(300)", "Nom de l'unité de réservation"),
            ("unites_principales", "VARCHAR(300)", "Unités de consommation principales"),
            ("unites_secondaires", "VARCHAR(300)", "Unités de consommation secondaires"),
            ("ordre", "INTEGER", "Ordre"),
            ], # Unités de réservations pour le portail

    "portail_actions":              [("IDaction", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID action"),
            ("horodatage", "DATETIME", "Horodatage de l'action"),
            ("IDfamille", "INTEGER", "ID de la famille"),
            ("IDindividu", "INTEGER", "ID de l'individu"),
            ("IDutilisateur", "INTEGER", "ID de l'utilisateur"),
            ("categorie", "VARCHAR(50)", "Catégorie de l'action"),
            ("action", "VARCHAR(50)", "Nom de l'action"),
            ("description", "VARCHAR(300)", "Description de l'action"),
            ("commentaire", "VARCHAR(300)", "Commentaire de l'action"),
            ("parametres", "VARCHAR(300)", "Paramètres de l'action"),
            ("etat", "VARCHAR(50)", "Etat de l'action"),
            ("traitement_date", "DATE", "Date du traitement de l'action"),
            ("IDperiode", "INTEGER", "ID de la période"),
            ("ref_unique", "VARCHAR(50)", "Référence unique de l'action"),
            ("reponse", "VARCHAR(450)", "Réponse à l'action"),
            ("email_date", "DATE", "Date de l'envoi de l'email de réponse"),
            ("IDpaiement", "INTEGER", "ID du paiement en ligne"),
            ("ventilation", "VARCHAR(5000)", "Ventilation du paiement"),
            ], # Actions enregistrées sur le portail

    "portail_reservations":         [("IDreservation", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID réservation"),
            ("date", "DATE", "Date de la consommation"),
            ("IDinscription", "INTEGER", "ID de l'inscription"),
            ("IDunite", "INTEGER", "ID de l'unité"),
            ("IDaction", "INTEGER", "ID de l'action"),
            ("etat", "INTEGER", "Ajout ou suppression de la réservation (1/0)"),
            ], # Réservations enregistrées sur le portail

    "portail_renseignements":       [("IDrenseignement", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID renseignement"),
             ("champ", "VARCHAR(255)", "Nom du champ"),
             ("valeur", "VARCHAR(255)", "Valeur du renseignement"),
             ("IDaction", "INTEGER", "ID de l'action"),
             ],  # Renseignements enregistrés sur le portail

    "portail_reservations_locations":[("IDreservation", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID réservation"),
            ("date_debut", "DATETIME", "Date de début de la réservation"),
            ("date_fin", "DATETIME", "Date de fin de la réservation"),
            ("IDlocation", "VARCHAR(255)", "ID de la location"),
            ("IDproduit", "INTEGER", "ID du produit associé"),
            ("IDaction", "INTEGER", "ID de l'action"),
            ("etat", "VARCHAR(100)", "ajouter, modifier ou supprimer"),
            ("resultat", "VARCHAR(100)", "Résultat du traitement"),
            ("partage", "INTEGER", "Partage du produit (0/1)"),
            ("description", "VARCHAR(200)", "Description"),
            ], # Réservations de locations enregistrées sur le portail

    "portail_messages":             [("IDmessage", "INTEGER PRIMARY KEY AUTOINCREMENT", "IDmessage"),
            ("titre", "VARCHAR(255)", "Titre du message"),
            ("texte", "VARCHAR(1000)", "Contenu du message"),
            ("affichage_date_debut", "DATETIME", "Date et heure de début d'affichage"),
            ("affichage_date_fin", "DATETIME", "Date et heure de fin d'affichage"),
             ], # Messages pour la page d'accueil du portail

    "profils":                      [("IDprofil", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID Profil"),
            ("label", "VARCHAR(400)", "Nom de profil"),
            ("categorie", "VARCHAR(200)", "Catégorie du profil"),
            ("defaut", "INTEGER", "(0/1) Profil sélectionné par défaut"),
            ],  # Profils de paramètres

    "profils_parametres":           [("IDparametre", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID parametre"),
            ("IDprofil", "INTEGER", "ID du profil"),
            ("nom", "VARCHAR(200)", "Nom"),
            ("parametre", "VARCHAR(10000)", "Parametre"),
            ("type_donnee", "VARCHAR(200)", "Type de données"),
            ],  # Paramètres des profils

    "evenements":                  [("IDevenement", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID évènement"),
            ("IDactivite", "INTEGER", "ID de l'activité associée"),
            ("IDunite", "INTEGER", "ID de l'unité de conso associée"),
            ("IDgroupe", "INTEGER", "ID du groupe associé"),
            ("date", "DATE", "Date de l'évènement"),
            ("nom", "VARCHAR(200)", "Nom de l'évènement"),
            ("description", "VARCHAR(1000)", "Description de l'évènement"),
            ("capacite_max", "INTEGER", "Nombre d'inscrits max sur l'évènement"),
            ("heure_debut", "DATE", "Heure de début de l'évènement"),
            ("heure_fin", "DATE", "Heure de fin de l'évènement"),
            ("montant", "FLOAT", "Montant fixe de la prestation"),
            ],  # Evènements

    "modeles_prestations":          [("IDmodele", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID prestation"),
            ("categorie", "VARCHAR(50)", "Catégorie de la prestation"),
            ("label", "VARCHAR(200)", "Label de la prestation"),
            ("IDactivite", "INTEGER", "ID de l'activité"),
            ("IDtarif", "INTEGER", "ID du tarif"),
            ("IDcategorie_tarif", "INTEGER", "ID de la catégorie de tarif"),
            ("tva", "FLOAT", "Taux TVA"),
            ("code_compta", "VARCHAR(200)", "Code comptable pour export vers logiciels de compta"),
            ("public", "VARCHAR(50)", "Type de public : famille ou individu"),
            ("IDtype_quotient", "INTEGER", "ID du type de quotient"),
             ],  # Modèles de prestations


    "produits_categories":          [("IDcategorie", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID Catégorie de produits"),
            ("nom", "VARCHAR(200)", "Nom de la catégorie"),
            ("observations", "VARCHAR(1000)", "Observations sur la catégorie"),
            ("image", "LONGBLOB", "Image de la catégorie en binaire"),
            ],  # Catégories de produits

    "produits":                     [("IDproduit", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID Produit"),
            ("IDcategorie", "INTEGER", "ID de la catégorie associée"),
            ("nom", "VARCHAR(200)", "Nom du produit"),
            ("observations", "VARCHAR(1000)", "Observations sur le produit"),
            ("image", "LONGBLOB", "Image du produit en binaire"),
            ("quantite", "INTEGER", "Quantité du produit"),
            ("montant", "FLOAT", "Montant fixe de la prestation"),
            ("activation_partage", "INTEGER", "Activer le partage de la ressource (0/1)"),
            ],  # Produits

    "locations":                    [("IDlocation", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID location"),
            ("IDfamille", "INTEGER", "ID de la famille"),
            ("IDproduit", "INTEGER", "ID du produit"),
            ("observations", "VARCHAR(1000)", "Observations sur la location"),
            ("date_saisie", "DATE", "Date de saisie de la location"),
            ("date_debut", "DATETIME", "Date et heure de début de location"),
            ("date_fin", "DATETIME", "Date et heure de fin de location"),
            ("quantite", "INTEGER", "Quantité du produit"),
            ("IDlocation_portail", "VARCHAR(100)", "IDlocation sur le portail"),
            ("serie", "VARCHAR(100)", "uuid de la série"),
            ("partage", "INTEGER", "Autoriser le partage de la ressource (0/1)"),
            ("description", "VARCHAR(200)", "Description"),
            ],  # Locations


    "locations_demandes":           [("IDdemande", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID Demande"),
            ("date", "DATETIME", "Date et heure de la demande"),
            ("IDfamille", "INTEGER", "ID de la famille"),
            ("observations", "VARCHAR(1000)", "Observations sur la location"),
            ("categories", "VARCHAR(1000)", "liste ID categories souhaitées"),
            ("produits", "VARCHAR(1000)", "liste ID produits souhaités"),
            ("statut", "VARCHAR(100)", "Statut de la demande"),
            ("motif_refus", "VARCHAR(1000)", "Motif du refus"),
            ("IDlocation", "INTEGER", "ID de la location attribuée"),
            ],  # Demandes de locations

    "periodes_gestion":             [("IDperiode", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID Période"),
            ("date_debut", "DATE", "Date de début de la période"),
            ("date_fin", "DATE", "Date de fin de la période"),
            ("observations", "VARCHAR(1000)", "Observations"),
            ("verrou_consommations", "INTEGER", "Verrouillage"),
            ("verrou_prestations", "INTEGER", "Verrouillage"),
            ("verrou_factures", "INTEGER", "Verrouillage"),
            ("verrou_reglements", "INTEGER", "Verrouillage"),
            ("verrou_depots", "INTEGER", "Verrouillage"),
            ("verrou_cotisations", "INTEGER", "Verrouillage"),
            ],  # Périodes de gestion

    "categories_medicales":         [("IDcategorie", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID Catégorie"),
            ("nom", "VARCHAR(300)", "Nom de la catégorie"),
            ],  # Catégories médicales

    "modeles_commandes":            [("IDmodele", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID modèle"),
            ("nom", "VARCHAR(300)", "Nom du modèle"),
            ("IDrestaurateur", "INTEGER", "ID du restaurateur"),
            ("parametres", "VARCHAR(8000)", "Parametres"),
            ("defaut", "INTEGER", "(0/1) Modèle par défaut"),
            ],  # Modèles de commandes de repas

    "modeles_commandes_colonnes":   [("IDcolonne", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID colonne"),
            ("IDmodele", "INTEGER", "ID du modèle de commande"),
            ("ordre", "INTEGER", "Ordre de la colonne"),
            ("nom", "VARCHAR(300)", "Nom de la colonne"),
            ("largeur", "INTEGER", "Largeur de la colonne en pixels"),
            ("categorie", "VARCHAR(100)", "Catégorie de la colonne"),
            ("parametres", "VARCHAR(8000)", "Parametres"),
            ],  # Colonnes des modèles de commandes de repas

    "commandes":                    [("IDcommande", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID commande"),
            ("IDmodele", "INTEGER", "ID du modèle de commande"),
            ("nom", "VARCHAR(300)", "Nom de la commande"),
            ("date_debut", "DATE", "Date de début de la période"),
            ("date_fin", "DATE", "Date de fin de la période"),
            ("observations", "VARCHAR(1000)", "Observations"),
            ],  # Commandes de repas

    "commandes_valeurs":            [("IDvaleur", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID valeur"),
            ("IDcommande", "INTEGER", "ID de la commande"),
            ("date", "DATE", "Date"),
            ("IDcolonne", "INTEGER", "ID de la colonne"),
            ("valeur", "VARCHAR(1000)", "Valeur"),
            ],  # Valeurs des commandes de repas

    "portail_pages":                [("IDpage", "INTEGER PRIMARY KEY AUTOINCREMENT", "IDpage"),
           ("titre", "VARCHAR(300)", "Titre de la page"),
           ("couleur", "VARCHAR(100)", "Couleur"),
           ("ordre", "INTEGER", "Ordre de la page"),
           ],  # Pages personnalisées pour le portail

    "portail_blocs":                [("IDbloc", "INTEGER PRIMARY KEY AUTOINCREMENT", "IDbloc"),
            ("IDpage", "INTEGER", "ID de la page parente"),
            ("titre", "VARCHAR(300)", "Titre de la page"),
            ("couleur", "VARCHAR(100)", "Couleur"),
            ("categorie", "VARCHAR(200)", "Type de contrôle"),
            ("ordre", "INTEGER", "Ordre de la page"),
            ("parametres", "VARCHAR(5000)", "Paramètres divers"),
            ],  # Blocs pour les pages personnalisées du portail

    "portail_elements":             [("IDelement", "INTEGER PRIMARY KEY AUTOINCREMENT", "IDelement"),
            ("IDbloc", "INTEGER", "ID du bloc parent"),
            ("ordre", "INTEGER", "Ordre de l'élément"),
            ("titre", "VARCHAR(300)", "Titre de l'élément"),
            ("categorie", "VARCHAR(200)", "Catégorie de l'élément"),
            ("date_debut", "DATETIME", "Date et heure de début"),
            ("date_fin", "DATETIME", "Date et heure de fin"),
            ("parametres", "VARCHAR(5000)", "Paramètres divers"),
            ("texte_xml", "VARCHAR(5000)", "Contenu du texte version XML"),
            ("texte_html", "VARCHAR(5000)", "Contenu du texte version HTML"),
            ],  # Elements pour les pages du portail

    "menus":                        [("IDmenu", "INTEGER PRIMARY KEY AUTOINCREMENT", "IDmenu"),
            ("IDrestaurateur", "INTEGER", "ID du restaurateur"),
            ("IDcategorie", "INTEGER", "ID de la catégorie"),
            ("date", "DATE", "Date"),
            ("texte", "VARCHAR(1000)", "Texte du menu"),
            ],  # Menus

    "menus_categories":             [("IDcategorie", "INTEGER PRIMARY KEY AUTOINCREMENT", "IDcategorie"),
            ("nom", "VARCHAR(300)", "Nom de la catégorie"),
            ("ordre", "INTEGER", "Ordre"),
            ],  # Catégories des menus

    "menus_legendes":               [("IDlegende", "INTEGER PRIMARY KEY AUTOINCREMENT", "IDlegende"),
             ("nom", "VARCHAR(300)", "Nom de la légende"),
             ("couleur", "VARCHAR(100)", "Couleur"),
             ],  # Légendes des menus

    "perceptions":                  [("IDperception", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID de la perception"),
            ("nom", "VARCHAR(200)", "Nom de la perception"),
            ("rue_resid", "VARCHAR(255)", "Adresse de la perception"),
            ("cp_resid", "VARCHAR(10)", "Code postal de la perception"),
            ("ville_resid", "VARCHAR(100)", "Ville de la perception"),
             ], # Les perceptions pour le prélèvement automatique

    "devis":                        [("IDdevis", "INTEGER PRIMARY KEY AUTOINCREMENT", "IDdevis"),
             ("numero", "INTEGER", "Numéro de devis"),
             ("IDfamille", "INTEGER", "ID du devis"),
             ("date_edition", "DATE", "Date d'édition du devis"),
             ("activites", "VARCHAR(450)", "Liste des IDactivité séparées par ;"),
             ("individus", "VARCHAR(450)", "Liste des IDindividus séparées par ;"),
             ("IDutilisateur", "INTEGER", "Utilisateur qui a créé l'attestation"),
             ("date_debut", "DATE", "Date de début de période"),
             ("date_fin", "DATE", "Date de fin de période"),
             ("total", "FLOAT", "Montant total de la période"),
             ("regle", "FLOAT", "Montant réglé pour la période"),
             ("solde", "FLOAT", "Solde à régler pour la période"),
             ], # Devis

    "contacts": [("IDcontact", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID du contact"),
             ("nom", "VARCHAR(100)", "Nom du contact"),
             ("prenom", "VARCHAR(100)", "Prénom du contact"),
             ("rue_resid", "VARCHAR(255)", "Adresse du contact"),
             ("cp_resid", "VARCHAR(10)", "Code postal du contact"),
             ("ville_resid", "VARCHAR(100)", "Ville du contact"),
             ("tel_domicile", "VARCHAR(50)", "Tel de domicile du contact"),
             ("tel_mobile", "VARCHAR(50)", "Tel du mobile du contact"),
             ("mail", "VARCHAR(200)", "Email perso du contact"),
             ("site", "VARCHAR(100)", "Adresse site internet"),
             ("memo", "VARCHAR(2000)", "Mémo concernant le contact"),
             ], # Les contacts du carnet d'adresses

    }

DB_PHOTOS = {
    "photos": [
        ("IDphoto", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID de la photo"),
        ("IDindividu", "INTEGER", "ID de la personne"),
        ("photo", "BLOB", "Photo individu en binaire"),
        ],  # BLOB photos
    }

DB_DOCUMENTS = {
    "documents":[            ("IDdocument", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID du document"),
            ("IDpiece", "INTEGER", "ID de la pièce"),
            ("IDreponse", "INTEGER", "ID de la réponse du Questionnaire"),
            ("IDtype_piece", "INTEGER", "ID du type de pièce"),
            ("document", "LONGBLOB", "Document converti en binaire"),
            ("type", "VARCHAR(50)", "Type de document : jpeg, pdf..."),
            ("label", "VARCHAR(400)", "Label du document"),
            ("last_update", "VARCHAR(50)", "Horodatage de la dernière modification du document"),
            ], # BLOB documents
    "releases": [
        ("IDrelease", "INTEGER PRIMARY KEY AUTOINCREMENT", "ID de la release"),
        ("categorie", "VARCHAR(16)", "Préfixe de la série"),
        ("niveau", "INTEGER", "Niveau du groupe de release"),
        ("echelon", "INTEGER", "échelon dans le niveau"),
        ("description", "BLOB", "Description de la release"),
        ("fichier", "LONGBLOB", "Fichier zip de la release"),
        ("dateImport", "VARCHAR(32)","date de l'importation"),
        ],
    }
# ----------------------------------------------------------------------------------------
DB_PK = {
        "PK_matArticles_artCodeArticle"  :  {"table"  :  "matArticles",  "champ" : "artCodeArticle", },
        "PK_matPlanComptable_pctCodeComptable"  :  {"table"  :  "matPlanComptable",  "champ" : "pctCodeComptable", },
        "PK_matTarifs_trfActGroupCat"  :  {"table"  :  "matTarifs",  "champ" : "trfIDactivite,trfIDgroupe,trfIDcategorie_tarif", },
        "PK_matTarifsLignes_trlTarLigArt"  :  {"table"  :  "matTarifsLignes",  "champ" : "trlCodeTarif,trlNoLigne,trlCodeArticle", },
        "PK_matTarifsNoms_trnCodeTarif"  :  {"table"  :  "matTarifsNoms",  "champ" : "trnCodeTarif", },
        "PK_matParams_param"  :  {"table"  :  "matParams",  "champ" : "prmUser,prmParam", },
        "PK_individus_IDindividu": {"table": "individus", "champ": "IDindividu"},
        "PK_matParrainages_"  :  {"table"  :  "matParrainages",  "champ": "parIDinscription,parIDligneParr", },
        "PK_matCerfas_crfIDcerfa"  :  {"table"  :  "matCerfas",  "champ" : "crfIDcerfa", },
        "PK_matCerfasLignes_crlIDcerfa"  :  {"table"  :  "matCerfasLignes",  "champ" : "crlIDcerfa,crlIDprestation,crlIDligne",},
        }

DB_INDEX = {
        "IX_matCerfas_crfIDfamille"  :  {"table"  :  "matCerfas",  "champ" : "crfIDfamille", },
        "IX_matCerfasLignes_crlIDfamille"  :  {"table"  :  "matCerfasLignes",  "champ" : "crlIDfamille", },
        "IX_matArticles_artCodeComptable"  :  {"table"  :  "matArticles",  "champ" : "artCodeComptable", },
        "IX_matArticles_artCodeBlocFacture"  :  {"table"  :  "matArticles",  "champ" : "artCodeBlocFacture", },
        "IX_matArticles_artConditions"  :  {"table"  :  "matArticles",  "champ" : "artConditions", },
        "IX_matArticles_artModeCalcul"  :  {"table"  :  "matArticles",  "champ" : "artModeCalcul", },
        "IX_matPieces_pieDateAvoir"  :  {"table"  :  "matPieces",  "champ" : "pieDateAvoir", },
        "IX_matPieces_pieDateEcheance"  :  {"table"  :  "matPieces",  "champ" : "pieDateEcheance", },
        "IX_matPieces_pieDateFacturation"  :  {"table"  :  "matPieces",  "champ" : "pieDateFacturation", },
        "IX_matPieces_pieDateModif"  :  {"table"  :  "matPieces",  "champ" : "pieDateModif", },
        "IX_matPieces_pieIDactivite"  :  {"table"  :  "matPieces",  "champ" : "pieIDactivite", },
        "IX_matPieces_pieIDcategorie_tarif"  :  {"table"  :  "matPieces",  "champ" : "pieIDcategorie_tarif", },
        "IX_matPieces_pieIDcompte_payeur"  :  {"table"  :  "matPieces",  "champ" : "pieIDcompte_payeur", },
        "IX_matPieces_pieIDfamille"  :  {"table"  :  "matPieces",  "champ" : "pieIDfamille", },
        "IX_matPieces_pieIDgroupe"  :  {"table"  :  "matPieces",  "champ" : "pieIDgroupe", },
        "IX_matPieces_pieIDindividu"  :  {"table"  :  "matPieces",  "champ" : "pieIDindividu", },
        "IX_matPieces_pieIDinscription"  :  {"table"  :  "matPieces",  "champ" : "pieIDinscription", },
        "IX_matPieces_pieNoAvoir"  :  {"table"  :  "matPieces",  "champ" : "pieNoAvoir", },
        "IX_matPieces_pieNoFacture"  :  {"table"  :  "matPieces",  "champ" : "pieNoFacture", },
        "IX_matPieces_pieIDtranspAller"  :  {"table"  :  "matPieces",  "champ" : "pieIDtranspAller", },
        "IX_matPieces_pieIDtranspRetour"  :  {"table"  :  "matPieces",  "champ" : "pieIDtranspRetour", },
        "IX_matPiecesLignes_ligCodeArticle"  :  {"table"  :  "matPiecesLignes",  "champ" : "ligCodeArticle", },
        "IX_matPiecesLignes_ligIDnumPiece"  :  {"table"  :  "matPiecesLignes",  "champ" : "ligIDnumPiece", },
        "IX_matTarifs_trfCodeTarif"  :  {"table"  :  "matTarifs",  "champ" : "trfCodeTarif", },
        "IX_matTarifs_trfIDactivite"  :  {"table"  :  "matTarifs",  "champ" : "trfIDactivite", },
        "IX_matTarifsLignes_trlCodeArticle"  :  {"table"  :  "matTarifsLignes",  "champ" : "trlCodeArticle", },
        "IX_matTarifsLignes_trlCodeTarif"  :  {"table"  :  "matTarifsLignes",  "champ" : "trlCodeTarif", },
        "IX_transports_depart_date"  :  {"table"  :  "transports",  "champ" : "depart_date", },
        "index_photos_IDindividu": {"table": "photos", "champ": "IDindividu"},
        "index_liens_IDfamille": {"table": "liens", "champ": "IDfamille"},
        "index_familles_IDcompte_payeur": {"table": "familles", "champ": "IDcompte_payeur"},
        "index_rattachements_IDfamille": {"table": "rattachements", "champ": "IDfamille"},
        "index_rattachements_IDindividu": {"table": "rattachements", "champ": "IDindividu"},
        "index_pieces_IDfamille": {"table": "pieces", "champ": "IDfamille"},
        "index_pieces_IDindividu": {"table": "pieces", "champ": "IDindividu"},
        "index_ouvertures_IDactivite": {"table": "ouvertures", "champ": "IDactivite"},
        "index_ouvertures_date": {"table": "ouvertures", "champ": "date"},
        "index_remplissage_IDactivite": {"table": "remplissage", "champ": "IDactivite"},
        "index_remplissage_date": {"table": "remplissage", "champ": "date"},
        "index_inscriptions_IDindividu": {"table": "inscriptions", "champ": "IDindividu"},
        "index_inscriptions_IDfamille": {"table": "inscriptions", "champ": "IDfamille"},
        "index_consommations_IDinscription": {"table": "consommations", "champ": "IDinscription"},
        "index_consommations_IDcompte_payeur": {"table": "consommations", "champ": "IDcompte_payeur"},
        "index_consommations_IDindividu": {"table": "consommations", "champ": "IDindividu"},
        "index_consommations_IDactivite": {"table": "consommations", "champ": "IDactivite"},
        "index_consommations_date": {"table": "consommations", "champ": "date"},
        "index_prestations_IDfamille": {"table": "prestations", "champ": "IDfamille"},
        "index_prestations_IDcompte_payeur": {"table": "prestations", "champ": "IDcompte_payeur"},
        "index_prestations_date": {"table": "prestations", "champ": "date"},
        "index_prestations_IDactivite": {"table": "prestations", "champ": "IDactivite"},
        "index_comptes_payeurs_IDfamille": {"table": "comptes_payeurs", "champ": "IDfamille"},
        "index_reglements_IDcompte_payeur": {"table": "reglements", "champ": "IDcompte_payeur"},
        "index_ventilation_IDcompte_payeur": {"table": "ventilation", "champ": "IDcompte_payeur"},
        "index_ventilation_IDprestation": {"table": "ventilation", "champ": "IDprestation"},
        "index_factures_IDcompte_payeur": {"table": "factures", "champ": "IDcompte_payeur"},
        "index_matParrainages_parIDligneParr": {"table": "matParrainages", "champ": "parIDligneParr"},
        "index_familles_etat": {"table": "familles", "champ": "etat"},
        "index_individus_etat": {"table": "individus", "champ": "etat"},
}


# ----------------------------------------------------------------------------------------

def GetChamps_DATA_Tables(nomTable=None):
    lstChamps = []
    if nomTable:
        for nom, type, info in DB_DATA[nomTable] :
            lstChamps.append(nom)
    return lstChamps

def GetComplementInscription(DB,where,mess=None):
    # appel de natures
    wherePiece = where.replace("IDinscription","pieIDinscription")
    req = """
        SELECT pieIDinscription,pieNature
        FROM matPieces 
        WHERE %s ;"""%(wherePiece)
    ret = DB.ExecuterReq(req,MsgBox=mess)
    dicRetour = {}
    if ret == "ok" :
        recordset = DB.ResultatReq()
        for IDinscription,nature in recordset:
            if not IDinscription in dicRetour:
                dicRetour[IDinscription] = {'natures':"",'nbreConsos':0, 'parti':0}
            if not nature in dicRetour[IDinscription]['natures']:
                dicRetour[IDinscription]["natures"] += nature
    else: return {}

    # Appel nbreConsos
    req = """
        SELECT IDinscription, COUNT(IDconso)
        FROM consommations
        WHERE %s
        GROUP BY IDinscription;"""%(where)
    ret = DB.ExecuterReq(req,MsgBox=mess)
    if ret == "ok" :
        recordset = DB.ResultatReq()
        for IDinscription,nbreConsos in recordset:
            if not IDinscription in dicRetour:
                dicRetour[IDinscription] = {'natures':"",'nbreConsos':0, 'parti':0}
            if nbreConsos:
                dicRetour[IDinscription]['nbreConsos'] = nbreConsos
    else: return {}

    # Calcul inscription active => parti ou non
    req = """
        SELECT IDindividu, IDactivite, COUNT(IDinscription)
        FROM inscriptions
        WHERE %s
        GROUP BY IDindividu, IDactivite
        HAVING COUNT(IDinscription) > 1 ;"""%(where)
    ret = DB.ExecuterReq(req,MsgBox=mess)
    if ret == "ok" :
        tplDoublons = DB.ResultatReq()
        for IDindividu, IDactivite, nbreInscr in tplDoublons:
            req = """
                SELECT IDinscription,IDactivite
                FROM inscriptions
                WHERE IDindividu = %d AND IDactivite = %d 
                ;"""%(IDindividu,IDactivite)
            ret = DB.ExecuterReq(req,MsgBox=mess)
            if ret == "ok" :
                tplInscriptions = DB.ResultatReq()
                maxID = 0
                for IDinscription,IDactivite in tplInscriptions:
                    if IDinscription > maxID:
                        maxID = IDinscription
                    # présumé tous partis sauf le plus récent
                    dicRetour[IDinscription]['parti'] = 1
                dicRetour[maxID]['parti'] = 0
            else: return {}
    return dicRetour

def GetDictRecord(DB,nomTable,ID,mess=None):
    # retrourne le dictionnaire du record d'une table
    lstChamps = GetChamps_DATA_Tables(nomTable)
    req = """
        SELECT * 
        FROM %s 
        WHERE %s = %d ;"""%(nomTable,lstChamps[0],ID)
    ret = DB.ExecuterReq(req,MsgBox=mess)
    dicRetour = {}
    if ret == "ok" :
        recordset = DB.ResultatReq()
        if len(recordset) > 0:
            for ix in range(len(lstChamps)):
                dicRetour[lstChamps[ix]] = recordset[0][ix]
    else: raise Exception("DATA_Tables.GetDictRecord req: %s"%req)
    if nomTable == "inscriptions":
        # ajout de natures et nbconsos
        where = "IDinscription = %d"%ID
        ddCompl = GetComplementInscription(DB,where,mess)
        if ID in ddCompl:
            dicRetour.update(ddCompl[ID])
    return dicRetour

def GetDdRecords(DB,nomTable,where,lstChamps=None,mess=None):
    # retrourne les dictionnaires des records d'une table filtrée where, premier champ doit être l'ID pk

    if lstChamps and not isinstance(lstChamps,list):
        raise Exception("lstChamp type not list! : %s"%str(lstChamps))
    if not lstChamps:
        lstChamps = GetChamps_DATA_Tables(nomTable)
    req = """SELECT %s FROM %s WHERE %s ;"""%(", ".join(lstChamps),nomTable,where)
    ret = DB.ExecuterReq(req,MsgBox=mess)
    ddRetour = {}
    if ret == "ok" :
        recordset = DB.ResultatReq()
        for record in recordset:
            dicOne = {}
            for ix in range(len(lstChamps)):
                dicOne[lstChamps[ix]] = record[ix]
            ddRetour[dicOne[lstChamps[0]]] = dicOne
    else: raise Exception("DATA_Tables.GetDdRecords req: %s"%req)
    if nomTable == "inscriptions":
        # ajout de natures et nbconsos
        ddComplements = GetComplementInscription(DB,where,mess)
        for IDinscription, dic in ddComplements.items():
            if not IDinscription in ddRetour:
                # inscription de matPiece ou consommations non connue dans inscriptions
                continue
            ddRetour[IDinscription].update(dic)
    return ddRetour

def GetLstTablesOptions(lstOptions=[]):
    # fonctionne soit en choix de sélection ou en exclusion selon arg
    lstTables = []
    if len(lstOptions) == 0:
        lstlstTablesOptionnelles = TABLES_IMPORTATION_OPTIONNELLES
    else:
        # des choix de catégories ont été faits
        lstlstTablesOptionnelles = lstOptions

    # Importation des tables optionnelles
    for nomCategorie, listeTables, selection in lstlstTablesOptionnelles:
        if selection == True:
            for nomTable in listeTables:
                lstTables.append(nomTable)
    return lstTables


if __name__ == "__main__":
    """ Affichage de stats sur les tables """
    nbreChamps = 0
    for nomTable, listeChamps in DB_DATA.items() :
        nbreChamps += len(listeChamps)
    print("Nbre de champs DATA =", nbreChamps)
    print("Nbre de tables DATA =", len(list(DB_DATA.keys())))