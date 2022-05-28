#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys branche Matthania
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS, JB
# Copyright:       (c) 2010-14 Ivan LUCAS, JB
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------

from Utils.UTILS_Traduction import _
import GestionDB
import sqlite3
import datetime
import base64
import pickle

from Utils import UTILS_Dates
from Utils import UTILS_Titulaires
from Utils import UTILS_Cotisations_manquantes
from Utils import UTILS_Pieces_manquantes
from Utils import UTILS_Questionnaires
from Utils import UTILS_Fichiers

from Data.DATA_Liens import DICT_TYPES_LIENS, DICT_AUTORISATIONS
from Data import DATA_Civilites as Civilites
DICT_CIVILITES = Civilites.GetDictCivilites()


def GetTypeChamp(codeChamp=""):
    """ Renvoie le type de donnée d'un champ """
    codeChamp = codeChamp.replace("{", "").replace("}", "")
    dictTypes = {
        "INDIVIDU_AGE_INT" : "entier",
        }
    if codeChamp in dictTypes :
        return dictTypes[codeChamp]
    else :
        return "texte"


def GetNomsChampsPossibles(mode="individu+famille"):
    listeChamps = []
    
    # Individu
    listeChampsIndividu = [
            (_("ID de l'individu"), "253", "{IDINDIVIDU}"), 
            (_("Civilité courte de l'individu"), _("M."), "{INDIVIDU_CIVILITE_COURT}"), 
            (_("Civilité longue de l'individu"), _("Monsieur"), "{INDIVIDU_CIVILITE_LONG}"), 
            (_("Sexe de l'individu"), "H", "{INDIVIDU_SEXE}"), 
            (_("Nom complet de l'individu"), _("DUPOND Philippe"), "{INDIVIDU_NOM_COMPLET}"), 
            (_("Nom de famille de l'individu"), _("DUPOND"), "{INDIVIDU_NOM}"), 
            (_("Prénom de l'individu"), _("Philippe"), "{INDIVIDU_PRENOM}"), 
            (_("Numéro de sécu de l'individu"), "2 39 336...", "{INDIVIDU_NUM_SECU}"), 
            (_("Date de naissance de l'individu"), "23/01/2010", "{INDIVIDU_DATE_NAISS}"), 
            (_("Age de l'individu"), _("9 ans"), "{INDIVIDU_AGE}"), 
            (_("Code postal de la ville de naissance de l'individu"), "29200", "{INDIVIDU_CP_NAISS}"), 
            (_("Ville de naissance de l'individu"), _("BREST"), "{INDIVIDU_VILLE_NAISS}"), 
            (_("Année de décès de l'individu"), "2012", "{INDIVIDU_ANNEE_DECES}"),
            (_("Rue de l'adresse de l'individu"), _("10 rue des oiseaux"), "{INDIVIDU_RUE}"), 
            (_("Code postal de l'adresse de l'individu"), "29870", "{INDIVIDU_CP}"), 
            (_("Ville de l'adresse de l'individu"), _("LANNILIS"), "{INDIVIDU_VILLE}"), 
            (_("Secteur de l'adresse de l'individu"), _("Quartier sud"), "{INDIVIDU_SECTEUR}"), 
            (_("Catégorie socio-professionnelle de l'individu"), _("Ouvrier"), "{INDIVIDU_CATEGORIE_TRAVAIL}"), 
            (_("Profession de l'individu"), _("Peintre"), "{INDIVIDU_PROFESSION}"), 
            (_("Employeur de l'individu"), _("Pinceaux et Cie"), "{INDIVIDU_EMPLOYEUR}"),
            (_("Numéro de téléphone pro de l'individu"), "01.02.03.04.05", "{INDIVIDU_TEL_PRO}"), 
            (_("Numéro de fax pro de l'individu"), "01.02.03.04.05", "{INDIVIDU_FAX_PRO}"), 
            (_("Mail pro de l'individu"), "monadresse@pro.fr", "{INDIVIDU_MAIL_PRO}"), 
            (_("Numéro de téléphone domicile de l'individu"), "01.02.03.04.05", "{INDIVIDU_TEL_DOMICILE}"),
            (_("Numéro de téléphone portable de l'individu"), "06.02.03.04.05", "{INDIVIDU_TEL_MOBILE}"), 
            (_("Numéro de fax domicile de l'individu"), "01.02.03.04.05", "{INDIVIDU_FAX}"), 
            (_("Adresse Email de l'individu"), "monadresse@perso.fr", "{INDIVIDU_MAIL}"), 
            (_("Nom de famille du médecin traitant"), _("BERGOT"), "{MEDECIN_NOM}"), 
            (_("Prénom du médecin traitant"), _("Albert"), "{MEDECIN_PRENOM}"), 
            (_("Rue de l'adresse du médecin"), _("3 rue des allergies"), "{MEDECIN_RUE}"), 
            (_("Code postal de l'adresse du médecin traitant"), "29870", "{MEDECIN_CP}"), 
            (_("Ville de l'adresse du médecin traitant"), _("LANNILIS"), "{MEDECIN_VILLE}"), 
            (_("Numéro de téléphone du cabinet du médecin"), "01.02.03.04.05", "{MEDECIN_TEL_CABINET}"), 
            (_("Numéro de portable du médecin"), "06.02.03.04.05", "{MEDECIN_TEL_MOBILE}"), 
            (_("Mémo de l'individu"), _("informations diverses..."), "{INDIVIDU_MEMO}"), 
            (_("Date de création de la fiche individuelle"), "15/07/2014", "{INDIVIDU_DATE_CREATION}"), 
            ]
    
    if "individu" in mode :
        listeChamps.extend(listeChampsIndividu)
    
    # Inscriptions
    listeChampsInscription = [
            (_("Activité de l'inscription n°x"), _("Accueil de Loisirs"), "{INSCRIPTION_x_ACTIVITE}"),
            (_("Groupe de l'inscription n°x"), _("3-6 ans"), "{INSCRIPTION_x_GROUPE}"),
            (_("Catégorie de tarif de l'inscription n°x"), _("Hors commune"), "{INSCRIPTION_x_CATEGORIE_TARIF}"),
            (_("Famille rattachée à l'inscription n°x"), _("DUPOND Philippe et Marie"), "{INSCRIPTION_x_NOM_TITULAIRES}"),
            (_("Parti de l'inscription n°x"), _("Oui"), "{INSCRIPTION_x_PARTI}"),
            (_("Date de l'inscription n°x"), "15/07/2014", "{INSCRIPTION_x_DATE_INSCRIPTION}"),
            ]

    if "individu" in mode :
        listeChamps.extend(listeChampsInscription)

    # Infos médicales
    listeChampsInfosMedicales = [
            (_("Intitulé de l'information médicale n°x"), _("Allergie aux acariens"), "{MEDICAL_x_INTITULE}"),
            (_("Description de l'information médicale n°x"), _("Fait des boutons"), "{MEDICAL_x_DESCRIPTION}"),
            (_("Traitement médical de l'information médicale n°x"), _("Amoxicilline"), "{MEDICAL_x_TRAITEMENT_MEDICAL}"),
            (_("Description du traitement de l'information médicale n°x"), _("Prendre tous les midis"), "{MEDICAL_x_DESCRIPTION_TRAITEMENT}"),
            (_("Date de début de traitement de l'information médicale n°x"), "01/07/2014", "{MEDICAL_x_DATE_DEBUT_TRAITEMENT}"),
            (_("Date de fin de traitement de l'information médicale n°x"), "31/07/2014", "{MEDICAL_x_DATE_FIN_TRAITEMENT}"),
            ]

    if "individu" in mode :
        listeChamps.extend(listeChampsInfosMedicales)

    # Infos scolarité
    listeChampsScolarite = [
            (_("Date de début de l'étape de scolarité"), "01/09/2014", "{SCOLARITE_DATE_DEBUT}"),
            (_("Date de fin de l'étape de scolarité"), "30/06/2014", "{SCOLARITE_DATE_FIN}"),
            (_("Nom de l'école"), _("Ecole Jules Ferry"), "{SCOLARITE_NOM_ECOLE}"),
            (_("Nom de la classe"), _("CP/CE1 de Mme Machin"), "{SCOLARITE_NOM_CLASSE}"),
            (_("Nom du niveau scolaire"), _("Cours élémentaire 1"), "{SCOLARITE_NOM_NIVEAU}"),
            (_("Nom abrégé du niveau scolaire"), _("CE1"), "{SCOLARITE_ABREGE_NIVEAU}"),
            ]

    if "individu" in mode :
        listeChamps.extend(listeChampsScolarite)

    # Famille
    listeChampsFamille = [
            (_("Nom de correspondant de la famille"), _("DUPOND Philippe et Marie"), "{FAMILLE_NOM}"),
            (_("Rue de l'adresse de la famille"), _("10 rue des oiseaux"), "{FAMILLE_RUE}"),
            (_("Code postal de l'adresse de la famille"), "29870", "{FAMILLE_CP}"),
            (_("Ville de l'adresse de la famille"), _("LANNILIS"), "{FAMILLE_VILLE}"),
            (_("Secteur de l'adresse de la famille"), _("Quartier sud"), "{FAMILLE_SECTEUR}"),
            (_("Nom de la caisse d'allocations"), _("CAF"), "{FAMILLE_NOM_CAISSE}"),
            (_("Nom du régime social"), _("Régime général"), "{FAMILLE_NOM_REGIME}"),
            (_("Numéro allocataire"), _("1234567X"), "{FAMILLE_NUM_ALLOCATAIRE}"),
            (_("Nom de l'allocataire titulaire"), _("DUPOND Philippe"), "{FAMILLE_NOM_ALLOCATAIRE}"),
            (_("Mémo de la famille"), _("Informations diverses..."), "{FAMILLE_MEMO}"),
            (_("Date de création de la fiche familiale"), "15/07/2014", "{FAMILLE_DATE_CREATION}"),
            (_("Quotient familial actuel de la famille"), "340", "{FAMILLE_QF_ACTUEL}"),
            (_("Liste des cotisations manquantes"), _("Cotisation familiale"), "{COTISATIONS_MANQUANTES}"),
            (_("Liste des pièces manquantes"), _("Certificat médical"), "{PIECES_MANQUANTES}"),
            ]
            
    if "famille" in mode :
        listeChamps.extend(listeChampsFamille)

    # Messages
    listeChampsMessages = [
            (_("Date de saisie du message n°x"), "18/07/2014", "{MESSAGE_x_DATE_SAISIE}"),
            (_("Date de parution du message n°x"), "18/07/2014", "{MESSAGE_x_DATE_PARUTION}"),
            (_("Texte du message n°x"), _("Envoyer une facture à la famille"), "{MESSAGE_x_TEXTE}"),
            (_("Nom de l'individu ou de la famille rattachée au message n°x"), _("DUPOND Philippe et Marie"), "{MESSAGE_x_NOM}"),
            (_("Catégorie du message n°x"), _("Courrier"), "{MESSAGE_x_CATEGORIE}"),
            ]

    if "individu" in mode or "famille" in mode :
        listeChamps.extend(listeChampsMessages)

    # Rattachements
    listeRattachements = [
            ("REPRESENTANT_RATTACHE_x", _("le représentant rattaché n°x")),
            ("ENFANT_RATTACHE_x", _("l'enfant rattaché n°x")),
            ("CONTACT_RATTACHE_x", _("le contact rattaché n°x")),
            ]
    listeChampsRattachements = [
            (_("Nombre de représentants rattachés à la famille"), "2", "{NBRE_REPRESENTANTS_RATTACHES}"),
            (_("Nombre d'enfants rattachés à la famille"), "1", "{NBRE_ENFANTS_RATTACHES}"),
            (_("Nombre de contacts rattachés à la famille"), "3", "{NBRE_CONTACTS_RATTACHES}"),
            ]
    for champRattachement, labelRattachement in listeRattachements :
        for label, exemple, champ in listeChampsIndividu :
            if champ.startswith("{INDIVIDU") :
                label = label.replace(_("l'individu"), labelRattachement)
                champ = champ.replace(_("INDIVIDU"), champRattachement)
                listeChampsRattachements.append((label, exemple, champ))
        listeChampsRattachements.append((_("Liens pour %s") % labelRattachement, _("Philippe est concubin de Marie..."), "{%s_LIEN}" % champRattachement))
        listeChampsRattachements.append((_("%s est titulaire ?") % labelRattachement, _("Oui"), "{%s_TITULAIRE}" % champRattachement))

    if "famille" in mode :
        listeChamps.extend(listeChampsRattachements)
    
    # Liens
    listeLiensPossibles = [
            ("PERE", _("le père")),
            ("MERE", _("la mère")),
            ("CONJOINT", _("le ou la conjointe")),
            ("ENFANT", _("l'enfant n°x")),
            ("AUTRE_LIEN", _("l'autre lien n°x")),
            ]
    listeLiens = [
            (_("Nombre d'enfants de l'individu"), "2", "{NBRE_ENFANTS}"),
            (_("Nombre d'autres liens de l'individu"), "4", "{NBRE_AUTRES_LIENS}"),
            ]
    for champLien, labelLien in listeLiensPossibles :
        for label, exemple, champ in listeChampsIndividu :
            if champ.startswith("{INDIVIDU") :
                label = label.replace(_("l'individu"), labelLien)
                champ = champ.replace(_("INDIVIDU"), champLien)
                listeLiens.append((label, exemple, champ))
        listeLiens.append((_("Autorisation pour %s") % labelLien, _("Responsable légal"), "{%s_AUTORISATION}" % champLien))
        listeLiens.append((_("Nom du lien pour %s") % labelLien, _("Enfant"), "{%s_NOM_LIEN}" % champLien))
    
    if "individu" in mode :
        listeChamps.extend(listeLiens)

    return listeChamps


class Informations() :
    def __init__(self,
            date_reference=datetime.date.today(),
            qf = True,
            inscriptions = True,
            messages = True,
            infosMedicales = True,
            cotisationsManquantes = True,
            piecesManquantes = True,
            questionnaires = True,   
            scolarite = True,
            lstIDfamilles = [],
            ) :
        self.date_reference = date_reference
        self.qf = qf
        self.inscriptions = inscriptions
        self.messages = messages
        self.infosMedicales = infosMedicales
        self.cotisationsManquantes = cotisationsManquantes
        self.piecesManquantes = piecesManquantes
        self.questionnaires = questionnaires
        self.scolarite = scolarite
        self.conditionIndividu = ""
        self.conditionFamille = ""
        # Init DB
        self.DB = GestionDB.DB()

        if len(lstIDfamilles) > 0:
            self.conditionFamille = "WHERE IDfamille in (%s)"% str(lstIDfamilles)[1:-1]
            self.conditionIndividu = "WHERE IDindividu in (%s)"% str(self.GetIndividus())[1:-1]

        # Lancement du calcul
        self.dictTitulaires = UTILS_Titulaires.GetTitulaires(listeIDfamille=lstIDfamilles)
        self.Run()
        # Fermeture de la DB
        self.DB.Close()


    def Run(self):
        """ Procédure de recherche et de calcul des résultats """

        
        # Lecture des données de base
        self.dictIndividus = self.GetDictIndividus() 
        self.dictFamilles = self.GetDictFamilles() 
        self.dictLiens = self.GetLiens() 
        self.dictRattachements = self.GetRattachements() 

        # Lecture des autres types de données
        if self.qf : self.RechercheQF() 
        if self.inscriptions : self.RechercheInscriptions() 
        if self.messages : self.RechercheMessages()
        if self.infosMedicales : self.RechercheInfosMedicales()
        # abandon de ces détails pour un usage matthania
        if len(self.conditionFamille) == 0:
            if self.cotisationsManquantes : self.RechercheCotisationsManquantes()
            if self.piecesManquantes : self.RecherchePiecesManquantes()
            if self.questionnaires : self.RechercheQuestionnaires()
            if self.scolarite : self.RechercheScolarite()
        return self.dictIndividus
    
    def ReadDB(self, req=""):
        self.DB.ExecuterReq(req,MsgBox="UTILS_Infos_individus")
        listeDonnees = self.DB.ResultatReq()  
        return listeDonnees

    def GetIndividus(self):
        """ Récupération des individus des seules familles """
        req = """
        SELECT IDindividu
        FROM rattachements
        %s
        ;"""% self.conditionFamille
        lstDonnees = self.ReadDB(req)
        return [x for (x,) in lstDonnees]


    def GetNomsChampsReq(self, listeChamps={}):
        listeNomsCodes = []
        listeNomsChamps = []
        for code, champ in listeChamps :
            listeNomsCodes.append(code)
            listeNomsChamps.append(champ)
        return listeNomsCodes, listeNomsChamps
    
    def GetListeChampsIndividus(self):
            return [
                ("IDINDIVIDU" , "IDindividu"), ("individu_IDcivilite" , "IDcivilite"), ("INDIVIDU_NOM" , "individus.nom"), ("INDIVIDU_PRENOM" , "individus.prenom"), 
                ("INDIVIDU_NUM_SECU" , "num_secu"), ("INDIVIDU_DATE_NAISS" , "date_naiss"), ("INDIVIDU_CP_NAISS" , "cp_naiss"), ("INDIVIDU_VILLE_NAISS" , "ville_naiss"), ("INDIVIDU_ANNEE_DECES", "annee_deces"),
                ("individu_adresse_auto" , "adresse_auto"), ("INDIVIDU_RUE" , "individus.rue_resid"), ("INDIVIDU_CP" , "individus.cp_resid"), ("INDIVIDU_VILLE" , "individus.ville_resid"), ("INDIVIDU_SECTEUR" , "secteurs.nom"), 
                ("INDIVIDU_CATEGORIE_TRAVAIL" , "categories_travail.nom"), ("INDIVIDU_PROFESSION" , "profession"), ("INDIVIDU_EMPLOYEUR" , "employeur"),
                ("INDIVIDU_TEL_PRO" , "travail_tel"), ("INDIVIDU_FAX_PRO" , "travail_fax"), ("INDIVIDU_MAIL_PRO" , "travail_mail"), ("INDIVIDU_TEL_DOMICILE" , "tel_domicile"),
                ("INDIVIDU_TEL_MOBILE" , "individus.tel_mobile"), ("INDIVIDU_FAX" , "tel_fax"), ("INDIVIDU_MAIL" , "mail"), 
                ("MEDECIN_NOM" , "medecins.nom"), ("MEDECIN_PRENOM" , "medecins.prenom"), ("MEDECIN_RUE" , "medecins.rue_resid"), ("MEDECIN_CP" , "medecins.cp_resid"), 
                ("MEDECIN_VILLE" , "medecins.ville_resid"), ("MEDECIN_TEL_CABINET" , "medecins.tel_cabinet"), ("MEDECIN_TEL_MOBILE" , "medecins.tel_mobile"), 
                ("INDIVIDU_MEMO" , "individus.memo"), ("INDIVIDU_DATE_CREATION" , "individus.date_creation"), 
                ]

    def GetDictIndividus(self):
        """ Récupère toutes les infos de base sur les individus """
        listeNomsCodes, listeNomsChamps = self.GetNomsChampsReq(self.GetListeChampsIndividus())
        req = """SELECT %s
        FROM individus
        LEFT JOIN secteurs ON secteurs.IDsecteur = individus.IDsecteur
        LEFT JOIN categories_travail ON IDcategorie = individus.IDcategorie_travail
        LEFT JOIN medecins ON medecins.IDmedecin = individus.IDmedecin
        %s
        ;""" % (", ".join(listeNomsChamps), self.conditionIndividu)
        listeDonnees = self.ReadDB(req)
        dictTemp = {}
        for listeValeurs in listeDonnees :
            IDindividu = listeValeurs[0]
            dictTemp[IDindividu] = {}
            index = 0
            for valeur in listeValeurs :
                code = listeNomsCodes[index]
                if valeur == None : valeur = ""
                if code == "INDIVIDU_DATE_NAISS" : 
                    # Age
                    if valeur not in (None, "", "//") :
                        bday = UTILS_Dates.DateEngEnDateDD(valeur)
                        datedujour = self.date_reference
                        age = (datedujour.year - bday.year) - int((datedujour.month, datedujour.day) < (bday.month, bday.day))
                        dictTemp[IDindividu]["INDIVIDU_AGE"] = "%d ans" % age
                        dictTemp[IDindividu]["INDIVIDU_AGE_INT"] = age
                    else :
                        dictTemp[IDindividu]["INDIVIDU_AGE"] = ""
                        dictTemp[IDindividu]["INDIVIDU_AGE_INT"] = ""
                    valeur = UTILS_Dates.DateEngFr(valeur)
                if code == "INDIVIDU_DATE_CREATION" : valeur = UTILS_Dates.DateEngFr(valeur)
                dictTemp[IDindividu][code] = valeur
                index += 1
        
        # Recherche les noms et adresses de chaque individu
        dictIndividus = {}
        for IDindividu, dictIndividu in dictTemp.items() :
            
            # Civilité
            IDcivilite = dictIndividu["individu_IDcivilite"]
            if (IDcivilite in DICT_CIVILITES) == False : 
                IDcivilite = 1
            dictIndividu["INDIVIDU_CIVILITE_COURT"] = DICT_CIVILITES[IDcivilite]["civiliteAbrege"] 
            if dictIndividu["INDIVIDU_CIVILITE_COURT"] == None :
                dictIndividu["INDIVIDU_CIVILITE_COURT"] = ""
            dictIndividu["INDIVIDU_CIVILITE_LONG"] = DICT_CIVILITES[IDcivilite]["civiliteLong"] 
            dictIndividu["INDIVIDU_SEXE"] = DICT_CIVILITES[IDcivilite]["sexe"] 
            if dictIndividu["INDIVIDU_SEXE"] == None :
                dictIndividu["INDIVIDU_SEXE"] = ""
            
            # Nom complet
            if dictIndividu["INDIVIDU_PRENOM"] != None :
                dictIndividu["INDIVIDU_NOM_COMPLET"] = "%s %s" % (dictIndividu["INDIVIDU_NOM"], dictIndividu["INDIVIDU_PRENOM"])
            else :
                dictIndividu["INDIVIDU_NOM_COMPLET"] = dictIndividu["nom"]

            # Adresse 
            adresse_auto = dictIndividu["individu_adresse_auto"]
            if adresse_auto != None and adresse_auto in dictTemp :
                dictIndividu["INDIVIDU_RUE"] = dictTemp[adresse_auto]["INDIVIDU_RUE"]
                dictIndividu["INDIVIDU_CP"] = dictTemp[adresse_auto]["INDIVIDU_CP"]
                dictIndividu["INDIVIDU_VILLE"] = dictTemp[adresse_auto]["INDIVIDU_VILLE"]
                dictIndividu["INDIVIDU_SECTEUR"] = dictTemp[adresse_auto]["INDIVIDU_SECTEUR"]
            
            # Autre champs
            dictIndividu["NBRE_ENFANTS"] = 0
            dictIndividu["NBRE_AUTRES_LIENS"] = 0
            dictIndividu["liens"] = []

            dictIndividu["SCOLARITE_DATE_DEBUT"] = ""
            dictIndividu["SCOLARITE_DATE_FIN"] = ""
            dictIndividu["SCOLARITE_NOM_ECOLE"] = ""
            dictIndividu["SCOLARITE_NOM_CLASSE"] = ""
            dictIndividu["SCOLARITE_NOM_NIVEAU"] = ""
            dictIndividu["SCOLARITE_ABREGE_NIVEAU"] = ""

            # Mémorisation
            dictIndividus[IDindividu] = dictIndividu
        
        return dictIndividus
    
    def GetRattachements(self):
        """ Récupération des rattachements """
        req = """SELECT IDrattachement, IDindividu, IDfamille, IDcategorie, titulaire
        FROM rattachements
        %s
        ORDER BY IDcategorie, titulaire;"""% self.conditionFamille
        listeDonnees = self.ReadDB(req)
        dictRattachementsFamilles = {}
        dictRattachementsIndividus = {}
        for IDrattachement, IDindividu, IDfamille, IDcategorie, titulaire in listeDonnees :
            valeurs = {"IDrattachement" : IDrattachement, "IDindividu" : IDindividu, "IDfamille" : IDfamille, "IDcategorie" : IDcategorie, "titulaire" : titulaire}
            if (IDfamille in dictRattachementsFamilles) == False :
                dictRattachementsFamilles[IDfamille] = []
            dictRattachementsFamilles[IDfamille].append(valeurs)
            if (IDindividu in dictRattachementsIndividus) == False :
                dictRattachementsIndividus[IDindividu] = []
            dictRattachementsIndividus[IDindividu].append(valeurs)
        dictRattachements = {"familles" : dictRattachementsFamilles, "individus" : dictRattachementsIndividus}
        
        # Insertion des liens rattachés dans le dictFamilles
        for IDfamille, listeRattachements in dictRattachementsFamilles.items() :
            if IDfamille in self.dictFamilles :
                for dictValeurs in listeRattachements :
                    IDindividu = dictValeurs["IDindividu"]
                    IDcategorie = dictValeurs["IDcategorie"]
                    titulaire = dictValeurs["titulaire"]
                    if titulaire == 1 :
                        titulaireStr = _("Oui")
                    else :
                        titulaireStr = _("Non")
                    
                    dictCibles = {
                        1 : {"code" : "REPRESENTANT_RATTACHE", "key" : "NBRE_REPRESENTANTS_RATTACHES"},
                        2 : {"code" : "ENFANT_RATTACHE", "key" : "NBRE_ENFANTS_RATTACHES"},
                        3 : {"code" : "CONTACT_RATTACHE", "key" : "NBRE_CONTACTS_RATTACHES"},
                        }
                    
                    self.dictFamilles[IDfamille][dictCibles[IDcategorie]["key"]] += 1
                    index = self.dictFamilles[IDfamille][dictCibles[IDcategorie]["key"]]
                    codeCible = dictCibles[IDcategorie]["code"] + "_%d" % index
                    
                    # Récupération des infos sur l'individu pour transfert vers dictFamilles
                    for code, valeur in self.dictIndividus[IDindividu].items() :
                        if code.startswith("INDIVIDU") :
                            self.dictFamilles[IDfamille][code.replace("INDIVIDU", codeCible)] = valeur
                    self.dictFamilles[IDfamille][codeCible + "_TITULAIRE"] = titulaireStr
                    
                    # Récupération du lien de l'individu rattaché dans les liens
                    listeLiens = []
                    nom_sujet = self.dictIndividus[IDindividu]["INDIVIDU_PRENOM"]
                    for dictLien in self.dictFamilles[IDfamille]["liens"] :
                        if dictLien["IDindividu_sujet"] == IDindividu :
                            nom_objet = self.dictIndividus[dictLien["IDindividu_objet"]]["INDIVIDU_PRENOM"]
                            listeLiens.append(_("%s de %s") % (dictLien["lien"].lower(), nom_objet))
                    texte = ""
                    if len(listeLiens) == 1 :
                        texte = _("%s est %s") % (nom_sujet, listeLiens[0])
                    if len(listeLiens) > 1 :
                        texte = _("%s est ") % nom_sujet
                        texte += ", ".join(listeLiens[:-1])
                        texte += " et %s" % listeLiens[-1]
                    self.dictFamilles[IDfamille][codeCible + "_LIENS"] = texte

        return dictRattachements

    def GetLiens(self):
        """ Récupération des liens """
        req = """SELECT IDlien, IDfamille, IDindividu_sujet, IDtype_lien, IDindividu_objet, IDautorisation
        FROM liens
        %s
        ORDER BY IDtype_lien;"""% self.conditionFamille
        listeDonnees = self.ReadDB(req)
        dictLiens = {}
        for IDlien, IDfamille, IDindividu_sujet, IDtype_lien, IDindividu_objet, IDautorisation in listeDonnees :
            if IDfamille in self.dictFamilles and IDindividu_objet in self.dictIndividus and IDindividu_sujet in self.dictIndividus :
                
                # Recherche les détails du lien
                if IDtype_lien != None :
                    sexe = self.dictIndividus[IDindividu_sujet]["INDIVIDU_SEXE"]
                    if sexe in ("M", "F") :
                        nomLien = DICT_TYPES_LIENS[IDtype_lien][sexe].capitalize()
                        typeLien = DICT_TYPES_LIENS[IDtype_lien]["type"]
                        texteLien = DICT_TYPES_LIENS[IDtype_lien]["texte"][sexe]
                    else :
                        nomLien = ""
                        typeLien = ""
                        texteLien = ""
                    
                    if IDautorisation in DICT_AUTORISATIONS :
                        if sexe in (None, "") : sexe = "M"
                        autorisation = DICT_AUTORISATIONS[IDautorisation][sexe]
                    else :
                        autorisation = ""
                    
                    # Mémorisation de la liste 
                    self.dictIndividus[IDindividu_objet]["liens"].append({"IDindividu" : IDindividu_sujet, "lien" : nomLien, "type" : typeLien, "texte" : texteLien, "autorisation" : autorisation})
                    self.dictFamilles[IDfamille]["liens"].append({"IDindividu_sujet" : IDindividu_sujet, "IDindividu_objet" : IDindividu_objet, "lien" : nomLien, "type" : typeLien, "texte" : texteLien, "autorisation" : autorisation})
                    
                    # Mémorisation des informations sur le père et la mère de l'individu uniquement au format texte
                    if IDtype_lien == 1 :
                        if sexe == "M" : 
                            codeCible = "PERE"
                        else :
                            codeCible = "MERE"
                        for code, valeur in self.dictIndividus[IDindividu_sujet].items() :
                            if code.startswith("INDIVIDU") :
                                # Mémorisation dans dictIndividus
                                self.dictIndividus[IDindividu_objet][code.replace("INDIVIDU", codeCible)] = valeur
                                # Mémorisation dans dictFamilles
                                self.dictFamilles[IDfamille][code.replace("INDIVIDU", codeCible)] = valeur
                        self.dictIndividus[IDindividu_objet][codeCible + "_AUTORISATION"] = autorisation
                        self.dictIndividus[IDindividu_objet][codeCible + "_NOM_LIEN"] = nomLien

                    # Mémorisation des informations sur le conjoint de l'individu uniquement au format texte
                    elif IDtype_lien in (10, 11) :
                        for code, valeur in self.dictIndividus[IDindividu_sujet].items() :
                            if code.startswith("INDIVIDU") :
                                self.dictIndividus[IDindividu_objet][code.replace("INDIVIDU", "CONJOINT")] = valeur
                        self.dictIndividus[IDindividu_objet]["CONJOINT_AUTORISATION"] = autorisation
                        self.dictIndividus[IDindividu_objet]["CONJOINT_NOM_LIEN"] = nomLien

                    # Mémorisation des informations sur les enfants de l'individu uniquement au format texte
                    elif IDtype_lien == 2 :
                        self.dictIndividus[IDindividu_objet]["NBRE_ENFANTS"] += 1
                        codeCible = "ENFANT_%d" % self.dictIndividus[IDindividu_objet]["NBRE_ENFANTS"]
                        for code, valeur in self.dictIndividus[IDindividu_sujet].items() :
                            if code.startswith("INDIVIDU") :
                                # Mémorisation dans dictIndividus
                                self.dictIndividus[IDindividu_objet][code.replace("INDIVIDU", codeCible)] = valeur
                                # Mémorisation dans dictFamilles
                                self.dictFamilles[IDfamille][code.replace("INDIVIDU", codeCible)] = valeur
                        self.dictIndividus[IDindividu_objet][codeCible + "_AUTORISATION"] = autorisation
                        self.dictIndividus[IDindividu_objet][codeCible + "_NOM_LIEN"] = nomLien

                    # Mémorisation des informations sur les autres types de liens uniquement au format texte
                    else :
                        self.dictIndividus[IDindividu_objet]["NBRE_AUTRES_LIENS"] += 1
                        codeCible = "AUTRE_LIEN_%d" % self.dictIndividus[IDindividu_objet]["NBRE_AUTRES_LIENS"]
                        for code, valeur in self.dictIndividus[IDindividu_sujet].items() :
                            if code.startswith("INDIVIDU") :
                                # Mémorisation dans dictIndividus
                                self.dictIndividus[IDindividu_objet][code.replace("INDIVIDU", codeCible)] = valeur
                                # Mémorisation dans dictFamilles
                                self.dictFamilles[IDfamille][code.replace("INDIVIDU", codeCible)] = valeur
                        self.dictIndividus[IDindividu_objet][codeCible + "_AUTORISATION"] = autorisation
                        self.dictIndividus[IDindividu_objet][codeCible + "_NOM_LIEN"] = nomLien

        return dictLiens

    def GetDictFamilles(self):
        """ Récupération des infos de base sur les familles """
        req = """SELECT IDfamille, date_creation, IDcompte_payeur, 
        caisses.nom, regimes.nom, num_allocataire, allocataire, memo
        FROM familles
        LEFT JOIN caisses ON caisses.IDcaisse = familles.IDcaisse
        LEFT JOIN regimes ON regimes.IDregime = caisses.IDregime
        %s
        ;""" %self.conditionFamille
        listeDonnees = self.ReadDB(req)
        dictFamilles = {}
        for IDfamille, date_creation, IDcompte_payeur, caisse_nom, regime_nom, num_allocataire, IDallocataire, memo in listeDonnees :
            date_creation = UTILS_Dates.DateEngFr(date_creation)
            if IDallocataire in self.dictIndividus :
                allocataire_nom = self.dictIndividus[IDallocataire]["INDIVIDU_NOM_COMPLET"]
            else :
                allocataire_nom = ""
            # Recherche titulaires et adresse de la famille
            if IDfamille in self.dictTitulaires :
                nomsTitulaires = self.dictTitulaires[IDfamille]["titulairesSansCivilite"]
                dictAdresse = self.dictTitulaires[IDfamille]["adresse"]
            else :
                nomsTitulaires = "?"
                dictAdresse = {"rue":"", "cp":"", "ville":"", "IDsecteur":None, "nomSecteur":""}
            # Mémorisation
            dictFamilles[IDfamille] = {
                "FAMILLE_DATE_CREATION" : date_creation, "IDcompte_payeur" : IDcompte_payeur, "FAMILLE_NOM_CAISSE" : caisse_nom, "FAMILLE_NOM_REGIME" : regime_nom, 
                "FAMILLE_NUM_ALLOCATAIRE" : num_allocataire, "IDallocataire" : IDallocataire, "FAMILLE_NOM_ALLOCATAIRE" : allocataire_nom, "FAMILLE_MEMO" : memo, 
                "FAMILLE_NOM" : nomsTitulaires, "FAMILLE_RUE" : dictAdresse["rue"], "FAMILLE_CP" : dictAdresse["cp"], "FAMILLE_VILLE" : dictAdresse["ville"],
                "FAMILLE_SECTEUR" : dictAdresse["nomSecteur"], "IDFAMILLE" : IDfamille,
                }
            # Autres champs
            dictFamilles[IDfamille]["liens"] = []
            dictFamilles[IDfamille]["NBRE_REPRESENTANTS_RATTACHES"] = 0
            dictFamilles[IDfamille]["NBRE_ENFANTS_RATTACHES"] = 0
            dictFamilles[IDfamille]["NBRE_CONTACTS_RATTACHES"] = 0
            
        return dictFamilles
    
    def RechercheQF(self):
        """ Recherche les QF des familles """
        req = """SELECT IDquotient, IDfamille, date_debut, date_fin, quotient, observations
        FROM quotients
        %s;"""% self.conditionFamille
        listeDonnees = self.ReadDB(req)
        for IDquotient, IDfamille, date_debut, date_fin, quotient, observations in listeDonnees :
            date_debut = UTILS_Dates.DateEngEnDateDD(date_debut)
            date_fin = UTILS_Dates.DateEngEnDateDD(date_fin)
            
            if IDfamille in self.dictFamilles :
                # Mémorisation du QF actuel au format texte
                if date_debut <= self.date_reference and date_fin >= self.date_reference :
                    self.dictFamilles[IDfamille]["FAMILLE_QF_ACTUEL"] = str(quotient)
                    self.dictFamilles[IDfamille]["FAMILLE_QF_ACTUEL_INT"] = quotient
                # Mémorisation sous forme de liste
                if ("qf" in self.dictFamilles[IDfamille]) == False :
                    self.dictFamilles[IDfamille]["qf"] = []
                self.dictFamilles[IDfamille]["qf"].append({"IDquotient" : IDquotient, "date_debut" : UTILS_Dates.DateDDEnFr(date_debut), "date_fin" : UTILS_Dates.DateDDEnFr(date_fin), "quotient" : quotient, "observations" : observations})
        
        
    def RechercheInscriptions(self):
        """ Récupération des inscriptions à des activités """
        req = """SELECT IDinscription, IDindividu, IDfamille, activites.nom, groupes.nom, categories_tarifs.nom,
        IDcompte_payeur, date_inscription, parti
        FROM inscriptions
        LEFT JOIN activites ON activites.IDactivite = inscriptions.IDactivite
        LEFT JOIN groupes ON groupes.IDgroupe = inscriptions.IDgroupe
        LEFT JOIN categories_tarifs ON categories_tarifs.IDcategorie_tarif = inscriptions.IDcategorie_tarif
        %s
        ORDER BY activites.date_fin
        ;"""% self.conditionFamille
        listeDonnees = self.ReadDB(req)
        for IDinscription, IDindividu, IDfamille, activite, groupe, categorie_tarif, IDcompte_payeur, date_inscription, parti in listeDonnees :
            date_inscription = UTILS_Dates.DateEngFr(date_inscription)
            if IDfamille in self.dictTitulaires :
                nomTitulaires = self.dictTitulaires[IDfamille]["titulairesSansCivilite"]
            else :
                nomTitulaires = _("Famille inconnue")
            if parti == 1 : 
                parti = _("Oui")
            else :
                parti = _("Non")
                
            if IDindividu in self.dictIndividus :
                
                # Mémorise le nombre d'inscriptions
                if ("inscriptions" in self.dictIndividus[IDindividu]) == False :
                    self.dictIndividus[IDindividu]["inscriptions"] = {"nombre" : 0, "liste" : []}
                self.dictIndividus[IDindividu]["inscriptions"]["nombre"] += 1
                
                # Mémorise l'inscription au format texte
                index = self.dictIndividus[IDindividu]["inscriptions"]["nombre"]
                code = "INSCRIPTION_%d_" % index
                self.dictIndividus[IDindividu][code + "ACTIVITE"] = activite
                self.dictIndividus[IDindividu][code + "GROUPE"] = groupe
                self.dictIndividus[IDindividu][code + "CATEGORIE_TARIF"] = categorie_tarif
                self.dictIndividus[IDindividu][code + "NOM_TITULAIRES"] = nomTitulaires
                self.dictIndividus[IDindividu][code + "PARTI"] = parti
                self.dictIndividus[IDindividu][code + "DATE_INSCRIPTION"] = date_inscription
                
                # Mémorise l'inscription au format liste
                self.dictIndividus[IDindividu]["inscriptions"]["liste"].append({"index" : index, "activite" : activite, "groupe" : groupe, "categorie_tarif" : categorie_tarif, "nomTitulaires" : nomTitulaires, "parti" : parti, "date_inscription" : date_inscription})
        
    def RechercheInfosMedicales(self):
        """ Récupération des informations médicales des individus """
        req = """SELECT IDprobleme, IDindividu, IDtype, intitule, description, traitement_medical, description_traitement, date_debut_traitement, date_fin_traitement
        FROM problemes_sante
        %s
        ORDER BY IDprobleme;"""% self.conditionIndividu
        listeDonnees = self.ReadDB(req)
        for IDprobleme, IDindividu, IDtype, intitule, description, traitement_medical, description_traitement, date_debut_traitement, date_fin_traitement in listeDonnees :
            date_debut_traitement = UTILS_Dates.DateEngFr(date_debut_traitement)
            date_fin_traitement = UTILS_Dates.DateEngFr(date_fin_traitement)           
            
            if IDindividu in self.dictIndividus :
                
                # Mémorise le nombre d'informations médicales
                if ("medical" in self.dictIndividus[IDindividu]) == False :
                    self.dictIndividus[IDindividu]["medical"] = {"nombre" : 0, "liste" : []}
                self.dictIndividus[IDindividu]["medical"]["nombre"] += 1
                
                # Mémorise l'information médicale au format texte
                index = self.dictIndividus[IDindividu]["medical"]["nombre"]
                code = "MEDICAL_%d_" % index
                self.dictIndividus[IDindividu][code + "INTITULE"] = intitule
                self.dictIndividus[IDindividu][code + "DESCRIPTION"] = description
                self.dictIndividus[IDindividu][code + "TRAITEMENT_MEDICAL"] = traitement_medical
                self.dictIndividus[IDindividu][code + "DESCRIPTION_TRAITEMENT"] = description_traitement
                self.dictIndividus[IDindividu][code + "DATE_DEBUT_TRAITEMENT"] = date_debut_traitement
                self.dictIndividus[IDindividu][code + "DATE_FIN_TRAITEMENT"] = date_fin_traitement
                
                # Mémorise l'information médicale au format liste
                self.dictIndividus[IDindividu]["medical"]["liste"].append({
                    "IDtype":IDtype, "intitule":intitule, "description":description, "traitement_medical":traitement_medical, 
                    "description_traitement":description_traitement, "date_debut_traitement":date_debut_traitement, 
                    "date_fin_traitement":date_fin_traitement,
                    })
    
    def RechercheMessages(self):
        """ Recherche les messages des familles et des individus """
        req = """SELECT IDmessage, type, messages.IDcategorie, messages_categories.nom, date_saisie, IDutilisateur, date_parution, messages.priorite,
        messages.afficher_accueil, messages.afficher_liste, IDfamille, IDindividu, texte, messages.nom
        FROM messages
        LEFT JOIN messages_categories ON messages_categories.IDcategorie = messages.IDcategorie
        %s
        ;"""% self.conditionFamille
        listeDonnees = self.ReadDB(req)
        dictMessagesFamilles = {}
        dictMessagesIndividus = {}
        for IDmessage, typeTemp, IDcategorie, categorie_nom, date_saisie, IDutilisateur, date_parution, priorite, afficher_accueil, afficher_liste, IDfamille, IDindividu, texte, nom in listeDonnees :
            date_saisie = UTILS_Dates.DateEngFr(date_saisie)
            date_parution = UTILS_Dates.DateEngFr(date_parution)

            for ID, dictCible in [(IDindividu, self.dictIndividus), (IDfamille, self.dictFamilles)] :
                if ID != None :
                    if ID in dictCible :
                        if ("messages" in dictCible[ID]) == False :
                            dictCible[ID]["messages"] = {"nombre" : 0, "liste" : []}
                        dictCible[ID]["messages"]["nombre"] += 1
                    
                        # Mémorise l'information médicale au format texte
                        index = dictCible[ID]["messages"]["nombre"]
                        code = "MESSAGE_%d_" % index
                        dictCible[ID][code + "DATE_SAISIE"] = date_saisie
                        dictCible[ID][code + "DATE_PARUTION"] = date_parution
                        dictCible[ID][code + "TEXTE"] = texte
                        dictCible[ID][code + "NOM"] = nom
                        dictCible[ID][code + "CATEGORIE"] = categorie_nom
                        
                        # Mémorise l'information médicale au format liste
                        dictCible[ID]["messages"]["liste"].append({
                            "IDmessage":IDmessage, "type":typeTemp, "IDcategorie":IDcategorie, "date_saisie":date_saisie, 
                            "IDutilisateur":IDutilisateur, "date_parution":date_parution, "priorite":priorite, 
                            "afficher_accueil":afficher_accueil, "afficher_liste":afficher_liste, "texte":texte, "nom":nom, "categorie_nom" : categorie_nom,
                            })
    
    def RechercheCotisationsManquantes(self):
        """ Récupération de la liste des cotisations manquantes """
        dictCotisations = UTILS_Cotisations_manquantes.GetListeCotisationsManquantes(dateReference=self.date_reference)
        for IDfamille, dictValeurs in dictCotisations.items() :
            if IDfamille in self.dictFamilles :
                self.dictFamilles[IDfamille]["COTISATIONS_MANQUANTES"] = dictValeurs["cotisations"]

    def RecherchePiecesManquantes(self):
        """ Recherche des pièces manquantes """
        dictPieces = UTILS_Pieces_manquantes.GetListePiecesManquantes(dateReference=self.date_reference)
        for IDfamille, dictValeurs in dictPieces.items() :
            if IDfamille in self.dictFamilles :
                self.dictFamilles[IDfamille]["PIECES_MANQUANTES"] = dictValeurs["pieces"]
    
    def RechercheQuestionnaires(self):
        """ Récupération des questionnaires familiaux et individuels """
        for public, dictPublic in [("famille", self.dictFamilles), ("individu", self.dictIndividus)] :
            q = UTILS_Questionnaires.ChampsEtReponses(type=public) 
            for ID in list(dictPublic.keys()) :
                if ID in dictPublic :
                    if ("questionnaires" in dictPublic[ID]) == False :
                        dictPublic[ID]["questionnaires"] = []
                    listeDonnees = q.GetDonnees(ID, formatStr=False) 
                    for donnee in listeDonnees :
                        # Mémorisation de la liste
                        dictPublic[ID]["questionnaires"].append(donnee)
                        # Mémorisation au format texte
                        code = donnee["champ"].replace("{", "").replace("}", "")
                        dictPublic[ID][code] = donnee["reponse"]

    def RechercheScolarite(self):
        """ Recherche les étapes de scolarité des individus """
        req = """SELECT scolarite.IDscolarite, IDindividu, scolarite.date_debut, scolarite.date_fin, ecoles.nom, classes.nom, niveaux_scolaires.nom, niveaux_scolaires.abrege
        FROM scolarite
        LEFT JOIN ecoles ON ecoles.IDecole = scolarite.IDecole
        LEFT JOIN classes ON classes.IDclasse = scolarite.IDclasse
        LEFT JOIN niveaux_scolaires ON niveaux_scolaires.IDniveau = scolarite.IDniveau
        WHERE scolarite.date_debut<='%s' AND scolarite.date_fin>='%s'
        ;""" % (self.date_reference, self.date_reference)
        listeDonnees = self.ReadDB(req)
        for IDscolarite, IDindividu, date_debut, date_fin, ecole_nom, classes_nom, niveau_nom, niveau_abrege in listeDonnees :
            if ecole_nom == None : ecole_nom = ""
            if classes_nom == None : classes_nom = ""
            if niveau_nom == None : niveau_nom = ""
            if niveau_abrege == None : niveau_abrege = ""
            if IDindividu in self.dictIndividus :
                self.dictIndividus[IDindividu]["SCOLARITE_DATE_DEBUT"] = UTILS_Dates.DateEngFr(date_debut)
                self.dictIndividus[IDindividu]["SCOLARITE_DATE_FIN"] = UTILS_Dates.DateEngFr(date_fin)
                self.dictIndividus[IDindividu]["SCOLARITE_NOM_ECOLE"] = ecole_nom
                self.dictIndividus[IDindividu]["SCOLARITE_NOM_CLASSE"] = classes_nom
                self.dictIndividus[IDindividu]["SCOLARITE_NOM_NIVEAU"] = niveau_nom
                self.dictIndividus[IDindividu]["SCOLARITE_ABREGE_NIVEAU"] = niveau_abrege
                
# ---------------------------------------------------------------------------------------------------------------------------------
        
    def GetNomsChampsPresents(self, mode="individu+famille", listeID=None):
        """ Renvoie les noms des champs disponibles après calcul des données. """
        """ mode='individu' ou 'famille' ou 'individu+famille' """
        """ listeID = [liste IDindividu ou IDfamille] ou None pour tous """
        listeNomsChamps = []
        for modeTemp, dictTemp in [("individu", self.dictIndividus), ("famille", self.dictFamilles)] :
            if modeTemp in mode :
                for ID, dictValeurs in dictTemp.items()  :
                    if listeID == None or ID in listeID :
                        if type(dictValeurs) == dict :
                            for key, valeur in dictValeurs.items() :
                                if key[0] == key[0].upper() and key not in listeNomsChamps :
                                    listeNomsChamps.append(key)
        listeNomsChamps.sort() 
        return listeNomsChamps
        
    def GetDictValeurs(self, mode="individu", ID=None, formatChamp=True):
        """ mode = 'individu' ou 'famille' """
        """ ID = IDindividu ou IDfamille ou None pour avoir tout le monde """
        """ formatChamp = Pour avoir uniquement les keys pour publipostage au format {xxx} """
        def FormateDict(dictTemp2) :
            if formatChamp == True :
                dictFinal = {}
                for key, valeur in dictTemp2.items() :
                    if key[0] == key[0].upper() : 
                        dictFinal["{%s}" % key] = valeur
                return dictFinal
            else :
                return dictTemp2
            
        if mode == "individu" :
            dictTemp = self.dictIndividus
        else :
            dictTemp = self.dictFamilles
        if ID != None :
            if (ID in dictTemp) == False :
                return {}
            else :
                return FormateDict(dictTemp[ID])
        else :
            if formatChamp == True :
                dictFinal2 = {}
                for ID, dictValeurs in dictTemp.items() :
                    dictFinal2[ID] = FormateDict(dictValeurs)
                return dictFinal2
            else :
                return dictTemp
    
    def SetAsAttributs(self, parent=None, mode="individu", ID=None):
        """ Attribue les valeurs en tant que attribut à un module. Sert pour les tracks des objectlistview """
        dictDonnees = self.GetDictValeurs(mode=mode, ID=ID, formatChamp=False)
        for code, valeur in dictDonnees.items() :
            setattr(parent, code, valeur)
    
    def StockageTable(self, mode="famille"):
        """ Stockage des infos dans une table SQLITE """
        listeNomsChamps = self.GetNomsChampsPresents(mode=mode)
        
        DB = GestionDB.DB()

        nomTable = "table_test"

        # Suppression de la table si elle existe
        DB.ExecuterReq("DROP TABLE IF EXISTS %s" % nomTable)
        
        # Création de la table de données
        req = "CREATE TABLE IF NOT EXISTS %s (ID INTEGER PRIMARY KEY AUTOINCREMENT, " % nomTable
        for nom in listeNomsChamps :
            req += "%s %s, " % (nom, "VARCHAR(500)")
        req = req[:-2] + ")"
        DB.ExecuterReq(req,MsgBox="ExecuterReq")
        
        # Insertion des données
        dictValeurs = self.GetDictValeurs(mode=mode, formatChamp=False)
        listeDonnees = []
        for ID, dictTemp in dictValeurs.items() :
            listeValeurs = [ID,]
            for champ in listeNomsChamps :
                if champ in dictTemp :
                    valeur = dictTemp[champ]
                else:
                    valeur = ""
                listeValeurs.append(valeur)
            listeDonnees.append(listeValeurs)
            
        listeNomsChamps.insert(0, "ID")
        req = "INSERT INTO %s (%s) VALUES (%s)" % (nomTable, ", ".join(listeNomsChamps), ",".join("?" * len(listeNomsChamps) ))
        DB.Executermany(req=req, listeDonnees=listeDonnees, commit=True)
        
        DB.Close() 
    
    def StockagePickleFichier(self, mode="famille", nomFichier=UTILS_Fichiers.GetRepTemp(fichier="infos_individus.pickle")):
        import pickle
        dictValeurs = self.GetDictValeurs(mode=mode, formatChamp=False)
        fichier = open(nomFichier, 'wb')
        pickle.dump(dictValeurs, fichier)
    
    def GetPickleChaine(self, mode="famille", cryptage=False):
        dictValeurs = self.GetDictValeurs(mode=mode, formatChamp=False)
        chaine = pickle.dumps(dictValeurs)
        if cryptage == True :
            chaine = base64.b64encode(chaine)
        return chaine

    def EnregistreFichier(self, mode="famille", nomFichier = UTILS_Fichiers.GetRepTemp(fichier="infos_f.dat")):
        chaine = self.GetPickleChaine(mode=mode, cryptage=True)
        fichier = open(nomFichier, "w")
        fichier.write(chaine)
        fichier.close()
    
    def LectureFichier(self, nomFichier = UTILS_Fichiers.GetRepTemp(fichier="infos_f.dat")):
        fichier = open(nomFichier, "r")
        chaine = fichier.read()
        fichier.close()
        chaine = base64.b64decode(chaine)
        dictTemp = pickle.loads(chaine)
        return dictTemp
    
    def EnregistreDansDB(self, nomFichier = UTILS_Fichiers.GetRepTemp(fichier="database.dat")):
        dbdest = GestionDB.DB(suffixe=None, nomFichier=nomFichier, modeCreation=True)
        dictTables = {

            "individus":[               ("IDindividu", "INTEGER PRIMARY KEY AUTOINCREMENT", _("ID de la personne")),
                                            ("IDcivilite", "INTEGER", _("Civilité de la personne")),
                                            ("nom", "VARCHAR(100)", _("Nom de famille de la personne")),
                                            ("prenom", "VARCHAR(100)", _("Prénom de la personne")),
                                            ("photo", "BLOB", _("Photo de la personne")),
                                            ],

            "informations":[          ("IDinfo", "INTEGER PRIMARY KEY AUTOINCREMENT", _("ID de la ligne")),
                                            ("IDindividu", "INTEGER", _("ID de la personne")),
                                            ("champ", "VARCHAR(500)", _("Nom du champ")),
                                            ("valeur", "VARCHAR(500)", _("Valeur du champ")),
                                            ]
            }
        try :
            dbdest.CreationTables(dicoDB=dictTables)
        except :
            pass
        

        def Enregistre(nomTable, listeChamps, listeDonnees):
            txtChamps = ", ".join(listeChamps)
            txtQMarks = ", ".join(["?" for x in listeChamps])
            req = "INSERT INTO %s (%s) VALUES (%s)" % (nomTable, txtChamps, txtQMarks)
            dbdest.cursor.executemany(req, listeDonnees)


        # Insertion des données du dictIndividus
        dictValeurs = self.GetDictValeurs(mode="individu", formatChamp=False)
        listeDonnees = []
        for ID, dictTemp in dictValeurs.items() :
            for champ, valeur in dictTemp.items() :
                if type(valeur) in (str, str) and valeur not in ("", None) :
                    listeDonnees.append((ID, champ, valeur))
        
        Enregistre(nomTable="informations", listeChamps=["IDindividu", "champ", "valeur"], listeDonnees=listeDonnees)
        
        # Insertion des données individus
        db = GestionDB.DB(suffixe="PHOTOS")
        req = """SELECT IDindividu, photo FROM photos;"""
        db.ExecuterReq(req,MsgBox="ExecuterReq")
        listePhotos = db.ResultatReq()
        db.Close()
        dictPhotos = {}
        for IDindividu, photo in listePhotos :
            dictPhotos[IDindividu] = photo

        db = GestionDB.DB()
        req = """SELECT IDindividu, IDcivilite, nom, prenom FROM individus;"""
        db.ExecuterReq(req,MsgBox="ExecuterReq")
        listeIndividus = db.ResultatReq()
        db.Close()
        listeDonnees = []
        for IDindividu, IDcivilite, nom, prenom in listeIndividus :
            if IDindividu in dictPhotos :
                photo = sqlite3.Binary(dictPhotos[IDindividu])
            else :
                photo = None
            listeDonnees.append((IDindividu, IDcivilite, nom, prenom, photo))

        Enregistre(nomTable="individus", listeChamps=["IDindividu", "IDcivilite", "nom", "prenom", "photo"], listeDonnees=listeDonnees)
        
        
        # Cloture de la base
        dbdest.connexion.commit()
        dbdest.Close() 
        
        
# ---------------------------------------------------------------------------------------------------------------------------------
    
    def Tests(self):
        """ Pour les tests """
        # Récupération des noms des champs
        #print len(self.GetNomsChampsPresents(mode="individu", listeID=None))
##        print len(GetNomsChampsPossibles(mode="individu"))
        #for x in self.GetNomsChampsPresents(mode="individu", listeID=None) :
        # print x
        
        #self.EnregistreFichier(mode="individu", nomFichier="Temp/infos_individus.dat") 
        self.EnregistreDansDB()
##        print len(self.LectureFichier())
        
if __name__ == '__main__':
    infos = Informations()
    infos.Tests() 