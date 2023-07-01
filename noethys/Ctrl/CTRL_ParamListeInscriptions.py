#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    évolutions Matthania, modif des colonnes et de l'affichage des activités et gestion des catégories supprimées
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS, JB
# Copyright:       (c) 2010-11 Ivan LUCAS, JB
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------


from Utils.UTILS_Traduction import _
import Chemins
import wx
import copy
from Dlg import DLG_GestionParams
from Ctrl import CTRL_Bouton_image
import GestionDB
from Ctrl import CTRL_Saisie_date
from Dlg import DLG_calendrier_simple
import wx.lib.agw.hyperlink as Hyperlink

def StringToDict(texte):
    try:
        dict = eval(texte)
    except Exception as err:
        #"Ce n'est pas la forme d'un dictionnaire"
        dict = {"type(entree)": type(texte), "entree":texte, "erreur":err}
    return dict

def DateEngFr(textDate):
    if textDate == None: return ""
    textDate = str(textDate)
    text = str(textDate[8:10]) + "/" + str(textDate[5:7]) + "/" + str(textDate[:4])
    return text

def DateEngSQL(textDate):
    text = str(textDate[6:10]) + "-" + str(textDate[3:5]) + "-" +str(textDate[0:2])
    return text

ReqEntete = """
        FROM ((((((inscriptions
                    LEFT JOIN individus ON inscriptions.IDindividu = individus.IDindividu)
                    LEFT JOIN activites ON inscriptions.IDactivite = activites.IDactivite)
                    LEFT JOIN groupes ON inscriptions.IDgroupe = groupes.IDgroupe)
                    LEFT JOIN categories_tarifs ON inscriptions.IDcategorie_tarif = categories_tarifs.IDcategorie_tarif)
                    LEFT JOIN individus AS individus_1 ON individus.adresse_auto = individus_1.IDindividu)
                    LEFT JOIN categories_travail ON individus.IDcategorie_travail = categories_travail.IDcategorie)
        """

ReqPieces = """
		INNER JOIN (((matPieces
					LEFT JOIN matPiecesLignes ON matPieces.pieIDnumPiece = matPiecesLignes.ligIDnumPiece)
					LEFT JOIN matArticles ON matPiecesLignes.ligCodeArticle = matArticles.artCodeArticle)
					LEFT JOIN matPlanComptable ON matArticles.artCodeComptable = matPlanComptable.pctCodeComptable)
		            ON inscriptions.IDinscription = matPieces.pieIDinscription
        """

ReqFamilles = """
        LEFT JOIN (((
                ((SELECT rattachements.IDfamille, Min(rattachements.IDindividu) AS MinDeIDindividu, Count(rattachements.IDindividu) AS nbreIndividus
                FROM rattachements
                WHERE (rattachements.titulaire = 1)
                GROUP BY rattachements.IDfamille) AS z_titulaires)
            LEFT JOIN individus AS individus_F ON z_titulaires.MinDeIDindividu = individus_F.IDindividu)
            LEFT JOIN individus AS individus_F1 ON individus_F.adresse_auto = individus_F1.IDindividu)
            LEFT JOIN categories_travail AS categories_F ON individus_F.IDcategorie_travail = categories_F.IDcategorie)
            ON inscriptions.IDfamille = z_titulaires.IDfamille
        """

ReqPrestations = """
        LEFT JOIN (((prestations
            LEFT JOIN ventilation ON prestations.IDprestation = ventilation.IDprestation)
            LEFT JOIN reglements ON ventilation.IDreglement = reglements.IDreglement)
            LEFT JOIN modes_reglements ON reglements.IDmode = modes_reglements.IDmode)
        ON (inscriptions.IDactivite = prestations.IDactivite) AND (inscriptions.IDindividu = prestations.IDindividu) AND (inscriptions.IDfamille = prestations.IDfamille)
        """

ReqConsos = """
        INNER JOIN consommations ON inscriptions.IDinscription = consommations.IDinscription
        INNER JOIN unites ON consommations.IDunite = unites.IDunite
        """

ReqTranspAller = """
        LEFT JOIN matPieces AS matPiecesTA ON inscriptions.IDinscription = matPiecesTA.pieIDinscription
        LEFT JOIN ((((((transports AS transportsTA
            LEFT JOIN transports_compagnies AS transports_compagniesTA ON transportsTA.IDcompagnie = transports_compagniesTA.IDcompagnie)
            LEFT JOIN transports_lignes AS transports_lignesTA  ON transportsTA.IDligne = transports_lignesTA.IDligne)
            LEFT JOIN transports_lieux AS transports_lieuxTA ON transportsTA.depart_IDlieu = transports_lieuxTA.IDlieu)
            LEFT JOIN transports_arrets AS transports_arretsTA ON transportsTA.depart_IDarret = transports_arretsTA.IDarret)
            LEFT JOIN transports_arrets AS transports_arrets_1TA ON transportsTA.arrivee_IDarret = transports_arrets_1TA.IDarret)
            LEFT JOIN transports_lieux AS transports_lieux_1TA ON transportsTA.arrivee_IDlieu = transports_lieux_1TA.IDlieu)
        ON matPiecesTA.pieIDtranspAller = transportsTA.IDtransport
        """

ReqTranspRetour = """
        LEFT JOIN matPieces AS matPiecesTR ON inscriptions.IDinscription = matPiecesTR.pieIDinscription
        LEFT JOIN ((((((transports
                LEFT JOIN transports_compagnies ON transports.IDcompagnie = transports_compagnies.IDcompagnie)
                LEFT JOIN transports_lignes ON transports.IDligne = transports_lignes.IDligne)
                LEFT JOIN transports_lieux ON transports.depart_IDlieu = transports_lieux.IDlieu)
                LEFT JOIN transports_arrets ON transports.depart_IDarret = transports_arrets.IDarret)
                LEFT JOIN transports_arrets AS transports_arrets_1 ON transports.arrivee_IDarret = transports_arrets_1.IDarret)
                LEFT JOIN transports_lieux AS transports_lieux_1 ON transports.arrivee_IDlieu = transports_lieux_1.IDlieu)
        ON matPiecesTR.pieIDtranspRetour = transports.IDtransport
        """

DD_SELECT = {
"entete":{"from":ReqEntete,
          "select":"individus.IDcivilite,individus.nom,individus.prenom,individus.rue_resid,individus.cp_resid,individus.ville_resid,individus.tel_domicile,individus.tel_fax,individus.tel_mobile,individus.travail_tel,individus_1.rue_resid,individus_1.cp_resid,individus_1.ville_resid,inscriptions.date_inscription,individus.adresse_auto,individus.mail,individus.travail_mail,",
          "compose":"age,anneeMois,civilite,adresse,nomPrenom,telephones,mails,"},
"pieces":{"from":ReqPieces,
          "select":"",
          "compose":""},
"familles":{"from":ReqFamilles,
          "select":"individus_F.IDcivilite,individus_F.nom,individus_F.prenom,individus_F.num_secu,individus_F.rue_resid,individus_F.cp_resid,individus_F.ville_resid,individus_F.tel_domicile,individus_F.tel_fax,individus_F.tel_mobile,individus_F.travail_tel,individus_F1.rue_resid,individus_F1.cp_resid,individus_F1.ville_resid,individus_F.adresse_auto,individus_F.mail,individus_F.travail_mail,",
          "compose":"civilite_F,adresse_F,nomPrenom_F,telephones_F,mails_F,"},
"prestations":{"from":ReqPrestations,
          "select":"",
          "compose":"soldPrest,"},
"consos":{"from":ReqConsos,
          "select":"",
          "compose":""},
"transpAller":{"from":ReqTranspAller,
          "select":"",
          "compose":""},
"transpRetour":{"from":ReqTranspRetour,
          "select":"",
          "compose":""},
             }

DLD_CHAMPS ={
    "entete":[
            {"label":_("codeActiv"), "code":"abregeActivite", "champ":"activites.abrege", "typeDonnee":"texte","align":"left", "largeur":75, "stringConverter":None, "actif":True, "afficher":True},
            {"label":_("débutActiv"), "code":"debutActivite", "champ":"activites.date_debut", "typeDonnee":"date","align":"left", "largeur":75, "stringConverter":"date", "actif":True, "afficher":True},
            {"label":_("codeGroupe"), "code":"abregeGroupe", "champ":"groupes.abrege", "typeDonnee":"texte","align":"left", "largeur":75, "stringConverter":None, "actif":True, "afficher":True},
            {"label":_("civil"), "code":"civilite", "champ":None, "typeDonnee":"texte","align":"left", "largeur":40, "stringConverter":None, "actif":True, "afficher":False},
            {"label":_("civilitéLong"), "code":"civilitelong", "champ":None, "typeDonnee":"texte","align":"left", "largeur":60, "stringConverter":None, "actif":True, "afficher":True},
            {"label":_("nomPrénom"), "code":"nomPrenom", "champ":None, "typeDonnee":"texte","align":"left", "largeur":135, "stringConverter":None, "actif":True, "afficher":True},
            {"label":_("âge"), "code":"age", "champ":None, "typeDonnee":"entier","align":"left", "largeur":40, "stringConverter":None, "actif":True, "afficher":True},
            {"label":_("dteInscr"), "code":"dateInscription", "champ":"inscriptions.date_inscription", "typeDonnee":"date","align":"left", "largeur":55, "stringConverter":"date", "actif":False, "afficher":False},
            {"label":_("moisInscr"), "code":"anneemois", "champ":None, "typeDonnee":"texte","align":"left", "largeur":55, "stringConverter":None, "actif":True, "afficher":True},
            {"label":_("categorie"), "code":"categorie", "champ":"categories_travail.nom", "typeDonnee":"texte","align":"left", "largeur":95, "stringConverter":None, "actif":True, "afficher":False},
            {"label":_("genre"), "code":"genre", "champ":None, "typeDonnee":"texte","align":"left", "largeur":30, "stringConverter":None, "actif":True, "afficher":False},
            {"label":_("rue"), "code":"rue", "champ":None, "typeDonnee":"texte","align":"left", "largeur":135, "stringConverter":None, "actif":True, "afficher":True},
            {"label":_("codePostal"), "code":"cp", "champ":None, "typeDonnee":"texte","align":"left", "largeur":55, "stringConverter":None, "actif":True, "afficher":True},
            {"label":_("ville"), "code":"ville", "champ":None, "typeDonnee":"texte","align":"left", "largeur":125, "stringConverter":None, "actif":True, "afficher":True},
            {"label":_("mails"), "code":"mails", "champ":None, "typeDonnee":"texte","align":"left", "largeur":75, "stringConverter":None, "actif":True, "afficher":True},
            {"label":_("téléphones"), "code":"telephones", "champ":None, "typeDonnee":"texte","align":"left", "largeur":90, "stringConverter":None, "actif":True, "afficher":True},
            {"label":_("groupe"), "code":"groupe", "champ":"groupes.nom", "typeDonnee":"texte","align":"left", "largeur":75, "stringConverter":None, "actif":True, "afficher":False},
            {"label":_("IDinscr"), "code":"IDinscription", "champ":"inscriptions.IDinscription", "typeDonnee":"entier","align":"left", "largeur":75, "stringConverter":None, "actif":True, "afficher":False},
            {"label":_("IDact"), "code":"IDactivite", "champ":"inscriptions.IDactivite", "typeDonnee":"entier","align":"left", "largeur":75, "stringConverter":None, "actif":True, "afficher":False},
            {"label":_("IDfam"), "code":"IDfamille", "champ":"inscriptions.IDfamille", "typeDonnee":"entier","align":"left", "largeur":75, "stringConverter":None, "actif":True, "afficher":False},
            {"label":_("IDgroupe"), "code":"IDgroupe", "champ":"inscriptions.IDgroupe", "typeDonnee":"entier","align":"left", "largeur":75, "stringConverter":None, "actif":True, "afficher":False},
            {"label":_("IDindiv"), "code":"IDindividu", "champ":"inscriptions.IDindividu", "typeDonnee":"entier","align":"left", "largeur":50, "stringConverter":None, "actif":True, "afficher":True},
            {"label":_("IDnationalité"), "code":"IDnationalite", "champ":"individus.IDnationalite", "typeDonnee":"entier","align":"left", "largeur":75, "stringConverter":None, "actif":True, "afficher":False},
            {"label":_("IDtarif"), "code":"IDtarif", "champ":"inscriptions.IDcategorie_tarif", "typeDonnee":"entier","align":"left", "largeur":12, "stringConverter":None, "actif":True, "afficher":False},
            {"label":_("naissance"), "code":"naissance", "champ":"individus.date_naiss", "typeDonnee":"date","align":"left", "largeur":75, "stringConverter":"date", "actif":True, "afficher":False},
            {"label":_("nomActivité"), "code":"nomActivite", "champ":"activites.nom", "typeDonnee":"texte","align":"left", "largeur":75, "stringConverter":None, "actif":True, "afficher":False},
            {"label":_("noSecu"), "code":"noSecu", "champ":"individus.num_secu", "typeDonnee":"texte","align":"left", "largeur":75, "stringConverter":None, "actif":True, "afficher":True},
            {"label":_("profession"), "code":"profession", "champ":"individus.profession", "typeDonnee":"texte","align":"left", "largeur":75, "stringConverter":None, "actif":True, "afficher":False},
            {"label":_("tarifs"), "code":"tarifs", "champ":"categories_tarifs.nom", "typeDonnee":"texte","align":"left", "largeur":95, "stringConverter":None, "actif":True, "afficher":True},
            ],
    "pieces":[
            {"label":_("IDpiece"), "code":"IDpiece", "champ":"matPieces.pieIDnumPiece", "typeDonnee":"entier","align":"right", "largeur":75, "stringConverter":None, "actif":False, "afficher":False},
            {"label":_("natureP"), "code":"piece", "champ":"matPieces.pieNature", "typeDonnee":"texte","align":"left", "largeur":75, "stringConverter":None, "actif":True, "afficher":True},
            {"label":_("article"), "code":"article", "champ":"matArticles.artLibelle", "typeDonnee":"texte","align":"left", "largeur":75, "stringConverter":None, "actif":True, "afficher":False},
            {"label":_("codeArticle"), "code":"codeArticle", "champ":"matPiecesLignes.ligCodeArticle", "typeDonnee":"texte","align":"left", "largeur":75, "stringConverter":None, "actif":True, "afficher":False},
            {"label":_("compteCompta"), "code":"compteCompta", "champ":"matPlanComptable.pctCompte", "typeDonnee":"texte","align":"left", "largeur":75, "stringConverter":None, "actif":True, "afficher":False},
            {"label":_("blocFacture"), "code":"blocFacture", "champ":"matArticles.artCodeBlocFacture", "typeDonnee":"texte","align":"left", "largeur":75, "stringConverter":None, "actif":True, "afficher":False},
            {"label":_("dateAvoir"), "code":"dateAvoir", "champ":"matPieces.pieDateAvoir", "typeDonnee":"date","align":"left", "largeur":75, "stringConverter":"date", "actif":True, "afficher":False},
            {"label":_("dateFacture"), "code":"dateFacture", "champ":"matPieces.pieDateFacturation", "typeDonnee":"date","align":"left", "largeur":75, "stringConverter":"date", "actif":True, "afficher":False},
            {"label":_("dateEcheance"), "code":"dateEcheance", "champ":"matPieces.pieDateEcheance", "typeDonnee":"date","align":"left", "largeur":75, "stringConverter":"date", "actif":True, "afficher":True},
            {"label":_("IDparrain"), "code":"IDparrain", "champ":"matPieces.pieIDparrain", "typeDonnee":"entier","align":"left", "largeur":75, "stringConverter":None, "actif":True, "afficher":False},
            {"label":_("conditions"), "code":"conditions", "champ":"matArticles.artConditions", "typeDonnee":"texte","align":"left", "largeur":75, "stringConverter":None, "actif":True, "afficher":False},
            {"label":_("modeCalcul"), "code":"modeCalcul", "champ":"matArticles.artModeCalcul", "typeDonnee":"texte","align":"left", "largeur":75, "stringConverter":None, "actif":True, "afficher":False},
            {"label":_("montantLignes"), "code":"montantLignes", "champ":"Sum(ligMontant)", "typeDonnee":"montant","align":"right", "largeur":75, "stringConverter":"montant", "actif":True, "afficher":True},
            {"label":_("noAvoir"), "code":"noAvoir", "champ":"matPieces.pieNoAvoir", "typeDonnee":"entier","align":"left", "largeur":75, "stringConverter":None, "actif":True, "afficher":False},
            {"label":_("noFacture"), "code":"noFacture", "champ":"matPieces.pieNoFacture", "typeDonnee":"entier","align":"left", "largeur":75, "stringConverter":None, "actif":True, "afficher":False},
            {"label":_("parrainAbandon"), "code":"ParrainAbandon", "champ":"matPieces.pieParrainAbandon", "typeDonnee":"texte","align":"left", "largeur":75, "stringConverter":None, "actif":True, "afficher":False},
            {"label":_("prixTranspAller"), "code":"prixTranspAller", "champ":"Sum(matPieces.piePrixTranspAller)", "typeDonnee":"montant","align":"right", "largeur":75, "stringConverter":"montant", "actif":True, "afficher":True},
            {"label":_("prixTranspRetour"), "code":"prixTranspRetour", "champ":"Sum(matPieces.piePrixTranspRetour)", "typeDonnee":"montant","align":"right", "largeur":75, "stringConverter":"montant", "actif":True, "afficher":True},
            {"label":_("nbrePieces"), "code":"nbrePieces", "champ":"Count(matPieces.pieIDnumPiece)", "typeDonnee":"entier","align":"right", "largeur":75, "stringConverter":None, "actif":True, "afficher":False},
            {"label":_("nbreLignes"), "code":"nbreLignes", "champ":"Count(ligIDnumLigne)", "typeDonnee":"entier","align":"right", "largeur":75, "stringConverter":None, "actif":True, "afficher":False},
            {"label":_("qteLignes"), "code":"qteLignes", "champ":"Sum(ligQuantite)", "typeDonnee":"entier","align":"right", "largeur":75, "stringConverter":None, "actif":True, "afficher":False},
            {"label":_("dateModifPiece"), "code":"dateModifPiece", "champ":"matPieces.pieDateModif", "typeDonnee":"date","align":"left", "largeur":75, "stringConverter":"date", "actif":True, "afficher":False},
            {"label":_("etatPiece"), "code":"etatPiece", "champ":"matPieces.pieEtat", "typeDonnee":"texte","align":"left", "largeur":75, "stringConverter":None, "actif":True, "afficher":False},
            {"label":_("transfertCompta"), "code":"transfertCompta", "champ":"matPieces.pieComptaFac", "typeDonnee":"date","align":"left", "largeur":75, "stringConverter":"date", "actif":True, "afficher":False},
            {"label":_("transfertCptaAvo"), "code":"comptaAvo", "champ":"matPieces.pieComptaAvo", "typeDonnee":"date","align":"left", "largeur":75, "stringConverter":"date", "actif":True, "afficher":False},
            {"label":_("natureCompta"), "code":"natureCompta", "champ":"matPlanComptable.pctLibelle", "typeDonnee":"texte","align":"left", "largeur":75, "stringConverter":None, "actif":True, "afficher":False},
            {"label":_("utilisateurModifPiece"), "code":"utilisateurModifPiece", "champ":"matPieces.pieUtilisateurModif", "typeDonnee":"texte","align":"left", "largeur":75, "stringConverter":None, "actif":True, "afficher":False},
            ],
    "familles":[
            {"label":_("categorieFam"), "code":"categorieFamille", "champ":"categories_F.nom", "typeDonnee":"texte","align":"left", "largeur":95, "stringConverter":None, "actif":True, "afficher":False},
            {"label":_("civilitéFam"), "code":"civilite_F", "champ":None, "typeDonnee":"texte","align":"left", "largeur":30, "stringConverter":None, "actif":True, "afficher":False},
            {"label":_("rueFam"), "code":"rue_F", "champ":None, "typeDonnee":"texte","align":"left", "largeur":135, "stringConverter":None, "actif":True, "afficher":False},
            {"label":_("codePostalFam"), "code":"cp_F", "champ":None, "typeDonnee":"texte","align":"left", "largeur":75, "stringConverter":None, "actif":True, "afficher":False},
            {"label":_("villeFam"), "code":"ville_F", "champ":None, "typeDonnee":"texte","align":"left", "largeur":125, "stringConverter":None, "actif":True, "afficher":False},
            {"label":_("télsFam"), "code":"telephones_F", "champ":None, "typeDonnee":"texte","align":"left", "largeur":75, "stringConverter":None, "actif":True, "afficher":False},

            {"label":_("mailsFam"), "code":"mails_F", "champ":None, "typeDonnee":"texte","align":"left", "largeur":75, "stringConverter":None, "actif":True, "afficher":False},
            {"label":_("naissanceFam"), "code":"naissanceFamille", "champ":"individus_F.date_naiss", "typeDonnee":"entier","align":"left", "largeur":75, "stringConverter":None, "actif":True, "afficher":False},
            {"label":_("nationalitéFam"), "code":"nationaliteFamille", "champ":"individus_F.IDnationalite", "typeDonnee":"entier","align":"left", "largeur":75, "stringConverter":None, "actif":True, "afficher":False},
            {"label":_("nbreRespFam"), "code":"nbreRespFamille", "champ":"z_titulaires.nbreIndividus", "typeDonnee":"entier","align":"left", "largeur":75, "stringConverter":None, "actif":True, "afficher":False},
            {"label":_("désignationFam"), "code":"nomPrenom_F", "champ":None, "typeDonnee":"texte","align":"left", "largeur":135, "stringConverter":None, "actif":True, "afficher":False},
            {"label":_("nosecuFam"), "code":"nosecuFamille", "champ":"individus_F.num_secu", "typeDonnee":"texte","align":"left", "largeur":75, "stringConverter":None, "actif":True, "afficher":False},
            {"label":_("professionFam"), "code":"professionFamille", "champ":"individus_F.profession", "typeDonnee":"texte","align":"left", "largeur":75, "stringConverter":None, "actif":True, "afficher":False},
            ],
    "prestations":[
            {"label":_("IDprest"), "code":"idPrestation", "champ":"prestations.IDprestation", "typeDonnee":"entier","align":"left", "largeur":75, "stringConverter":None, "actif":False, "afficher":False},
            {"label":_("modeReglement"), "code":"modeReglement", "champ":"modes_reglements.label", "typeDonnee":"texte","align":"left", "largeur":75, "stringConverter":None, "actif":True, "afficher":False},
            {"label":_("mttPrest"), "code":"mttPrest", "champ":"prestations.montant", "typeDonnee":"montant","align":"right", "largeur":75, "stringConverter":"montant", "actif":True, "afficher":False},
            {"label":_("mttRegle"), "code":"montantRegle", "champ":"Sum(ventilation.montant)", "typeDonnee":"montant","align":"right", "largeur":75, "stringConverter":"montant", "actif":True, "afficher":True},
            {"label":_("prestation"), "code":"prestation", "champ":"prestations.label", "typeDonnee":"texte","align":"left", "largeur":75, "stringConverter":None, "actif":True, "afficher":False},
            {"label":_("soldPrest"), "code":"soldPrest", "champ":None, "typeDonnee":"montant","align":"right", "largeur":75, "stringConverter":"montant", "actif":True, "afficher":False},
            ],
    "consos":[
            {"label":_("abrégéConso"), "code":"abregeUniteConso", "champ":"unites.abrege", "typeDonnee":"texte","align":"left", "largeur":75, "stringConverter":None, "actif":True, "afficher":False},
            {"label":_("debutConsos"), "code":"debutConsos", "champ":"Min(consommations.Date)", "typeDonnee":"date","align":"left", "largeur":75, "stringConverter":"date", "actif":True, "afficher":False},
            {"label":_("finConsos"), "code":"finConsos", "champ":"Max(consommations.Date) ", "typeDonnee":"date","align":"left", "largeur":75, "stringConverter":"date", "actif":True, "afficher":False},
            {"label":_("nbreConsos"), "code":"nbreConsos", "champ":"Count(consommations.IDconso) ", "typeDonnee":"entier","align":"left", "largeur":75, "stringConverter":None, "actif":True, "afficher":False},
            {"label":_("nomUnitéConso"), "code":"nomUniteConso", "champ":"unites.nom", "typeDonnee":"texte","align":"left", "largeur":135, "stringConverter":None, "actif":True, "afficher":False},
            ],
    "transpAller":[
            {"label":_("arretArr"), "code":"arretArrivee", "champ":"transports_arrets_1TA.nom", "typeDonnee":"texte","align":"left", "largeur":75, "stringConverter":None, "actif":True, "afficher":False},
            {"label":_("arretDep"), "code":"arretDepart", "champ":"transports_arretsTA.nom", "typeDonnee":"texte","align":"left", "largeur":75, "stringConverter":None, "actif":True, "afficher":False},
            {"label":_("catTrans"), "code":"catTransport", "champ":"transportsTA.categorie", "typeDonnee":"texte","align":"left", "largeur":95, "stringConverter":None, "actif":True, "afficher":False},
            {"label":_("compagnie"), "code":"compagnie", "champ":"transports_compagniesTA.nom", "typeDonnee":"texte","align":"left", "largeur":75, "stringConverter":None, "actif":True, "afficher":False},
            {"label":_("dateArr"), "code":"dateArrivee", "champ":"transportsTA.arrivee_DATE", "typeDonnee":"date","align":"left", "largeur":75, "stringConverter":"date", "actif":True, "afficher":False},
            {"label":_("dateDep"), "code":"dateDepart", "champ":"transportsTA.depart_DATE", "typeDonnee":"date","align":"left", "largeur":75, "stringConverter":"date", "actif":True, "afficher":False},
            {"label":_("lieuArr"), "code":"lieuArrivee", "champ":"transports_lieux_1TA.nom", "typeDonnee":"texte","align":"left", "largeur":75, "stringConverter":None, "actif":True, "afficher":False},
            {"label":_("lieuDep"), "code":"lieuDepart", "champ":"transports_lieuxTA.nom", "typeDonnee":"texte","align":"left", "largeur":75, "stringConverter":None, "actif":True, "afficher":False},
            {"label":_("ligne"), "code":"ligne", "champ":"transports_lignesTA.nom", "typeDonnee":"texte","align":"left", "largeur":75, "stringConverter":None, "actif":True, "afficher":False},
            {"label":_("modeTransp"), "code":"modeTransport", "champ":"transportsTA.mode", "typeDonnee":"texte","align":"left", "largeur":75, "stringConverter":None, "actif":True, "afficher":False},
            ],
    "transpRetour":[
            {"label":_("arretArrRet"), "code":"arretArriveeRetour", "champ":"transports_arrets_1.nom", "typeDonnee":"texte","align":"left", "largeur":75, "stringConverter":None, "actif":True, "afficher":False},
            {"label":_("arretDepRet"), "code":"arretDepartRetour", "champ":"transports_arrets.nom", "typeDonnee":"texte","align":"left", "largeur":75, "stringConverter":None, "actif":True, "afficher":False},
            {"label":_("catTranspRet"), "code":"catTransportRetour", "champ":"transports.categorie", "typeDonnee":"texte","align":"left", "largeur":95, "stringConverter":None, "actif":True, "afficher":False},
            {"label":_("compagnieRet"), "code":"compagnieRetour", "champ":"transports_compagnies.nom", "typeDonnee":"texte","align":"left", "largeur":75, "stringConverter":None, "actif":True, "afficher":False},
            {"label":_("dateArrRet"), "code":"dateArriveeRetour", "champ":"transports.arrivee_DATE", "typeDonnee":"date","align":"left", "largeur":75, "stringConverter":"date", "actif":True, "afficher":False},
            {"label":_("dateDepRet"), "code":"dateDepartRetour", "champ":"transports.depart_DATE", "typeDonnee":"date","align":"left", "largeur":75, "stringConverter":"date", "actif":True, "afficher":False},
            {"label":_("lieuArrRet"), "code":"lieuArriveeRetour", "champ":"transports_lieux_1.nom", "typeDonnee":"texte","align":"left", "largeur":75, "stringConverter":None, "actif":True, "afficher":False},
            {"label":_("lieuDepRet"), "code":"lieuDepartRetour", "champ":"transports_lieux.nom", "typeDonnee":"texte","align":"left", "largeur":75, "stringConverter":None, "actif":True, "afficher":False},
            {"label":_("ligneRet"), "code":"ligneRetour", "champ":"transports_lignes.nom", "typeDonnee":"texte","align":"left", "largeur":75, "stringConverter":None, "actif":True, "afficher":False},
            {"label":_("modeTranspRet"), "code":"modeTransportRetour", "champ":"transports.mode", "typeDonnee":"texte","align":"left", "largeur":75, "stringConverter":None, "actif":True, "afficher":False},
            ],
    }


class ACheckListBox(wx.CheckListBox):
    def __init__(self, parent, *args, **kwargs):
        wx.CheckListBox.__init__(self, parent, -1, size = (50,50))
        self.parent = parent
        self.dictDonnees = {}
        self.listeDonnees = []
        self.oldListe= []
        self.oldListeChecked = []
        self.listNewChecked = []
        self.Bind(wx.EVT_CHECKLISTBOX, self.OnCheck)

    def MajBox(self,cocher = True):
        self.Clear()
        for item in self.listeDonnees :
            self.Append(item)
        #reprise des check
        for index in range(0, len(self.listeDonnees)):
            item = self.listeDonnees[index]
            if item in self.oldListe:
                if item in self.oldListeChecked:
                    self.Check(index,check = True)
                else:
                    self.Check(index,check = False)
            else:
                if cocher:
                    self.Check(index,check = True)

    def StockDonnees(self,recordset):
        self.dictDonnees = {}
        self.listeDonnees = []
        for ID, nom, IDchild in recordset:
            if ID != None :
                if nom not in self.dictDonnees: self.dictDonnees[nom] = {}
                if "lstID" not in self.dictDonnees[nom]:
                    self.dictDonnees[nom]["lstID"] = [ID]
                else:
                    self.dictDonnees[nom]["lstID"].append(ID)
                if "lstIDchild" not in self.dictDonnees[nom]:
                    self.dictDonnees[nom]["lstIDchild"] = []
                if IDchild !=None:
                    self.dictDonnees[nom]["lstIDchild"].append(IDchild)
                if not nom in self.listeDonnees:
                    self.listeDonnees.append(nom)

    def CocheTout(self,coche):
        for index in range(0, len(self.listeDonnees)):
            self.Check(index,check = coche)
            index += 1
        self.Modified()

    def CocheListe(self,liste):
        for index in range(0, len(self.listeDonnees)):
            item = self.listeDonnees[index]
            if item in liste:
                check = True
            else : check = False
            self.Check(index,check = check)
            index += 1
        self.Modified()

    def OnCheck(self, event):
        self.Modified()

    def GetListeChecked(self):
        listeChecked = []
        for item in self.GetCheckedStrings():
            listeChecked.append(item)
        return listeChecked

    def GetNewChecked(self, oldListeChecked):
        newListeChecked = self.GetCheckedStrings()
        newChecked = None
        listNewChecked = []
        listNewUnChecked = []
        #test nouvelle coche
        for item in newListeChecked :
            if oldListeChecked == [] :
                newChecked = item
                new = True
            else:
                new = True
                for oldItem in oldListeChecked:
                    if item == oldItem: new = False
                if new : newChecked = item
            if new : listNewChecked.append(newChecked)
        #test décoché
        for item in oldListeChecked :
            if newListeChecked == [] :
                newUnChecked = item
                bye = True
            else:
                bye = True
                for newItem in newListeChecked:
                    if item == newItem: bye = False
                if bye : newUnChecked = item
            if bye : listNewUnChecked.append(newUnChecked)
        return listNewChecked,listNewUnChecked

    def GetListeIDchecked(self):
        listeIDchecked = []
        for nom  in self.GetListeChecked():
            if nom in self.dictDonnees:
                if "lstID" in self.dictDonnees[nom]:
                    for ID in self.dictDonnees[nom]["lstID"]:
                        listeIDchecked.append(ID)
        listeIDchecked.sort()
        return listeIDchecked

    def GetListeIDchildrenChecked(self):
        listeIDchecked = []
        for nom  in self.GetListeChecked():
            if nom in self.dictDonnees:
                if "lstIDchild" in self.dictDonnees[nom]:
                    lstIDitem = self.dictDonnees[nom]["lstIDchild"]
                    for ID in lstIDitem:
                        if not ID in listeIDchecked:
                            listeIDchecked.append(ID)
        listeIDchecked.sort()
        return listeIDchecked

class Hyperlien(Hyperlink.HyperLinkCtrl):
    def __init__(self, parent, id=-1, label="", infobulle="", URL=""):
        Hyperlink.HyperLinkCtrl.__init__(self, parent, id, label, URL=URL)
        self.parent = parent
        self.URL = URL
        self.AutoBrowse(False)

        # SetColours(1,2,3 )1'link':à l'ouverture, 2`visited`: survol avant clic, 3`rollover`: après le clic,
        self.SetColours("BLUE", "BLUE", "PURPLE")

        # SetUnderlines(1,2,3 ) 1'link':`True` underlined(à l'ouverture),2`visited`:'True` underlined(lors du survol avant clic), 3`rollover`:`True` (trace après le clic),
        self.SetUnderlines(False, True, False)
        self.SetBold(False)
        self.EnableRollover(True)
        self.SetToolTip(wx.ToolTip(infobulle))
        self.UpdateLink()
        self.DoPopup(False)
        self.Bind(Hyperlink.EVT_HYPERLINK_LEFT, self.OnLeftLink)

    def OnLeftLink(self, event):
        if self.URL == "tout": self.parent.CocheTout(True)
        if self.URL == "rien": self.parent.CocheTout(False)
        self.UpdateLink()

class CocheToutRien(wx.Panel):
    def __init__(self, parent,IDparent):
        self.parent = parent
        self.IDparent = IDparent
        wx.Panel.__init__(self, parent, id=-1, style=wx.TAB_TRAVERSAL)
        self.hyper_tout = Hyperlien(self, label=_("Cocher"), infobulle=_("Cliquez ici pour tout cocher"),
                                    URL="tout")
        self.hyper_rien = Hyperlien(self, label=_("Décocher"), infobulle=_("Cliquez ici pour tout décocher"),
                                    URL="rien")
        grid_sizer_cocher = wx.FlexGridSizer(rows=2, cols=1, vgap=5, hgap=5)
        grid_sizer_cocher.Add(self.hyper_tout, 0, wx.TOP, 10)
        grid_sizer_cocher.Add(self.hyper_rien, 0, wx.ALL, 0)
        self.SetSizer(grid_sizer_cocher)
        grid_sizer_cocher.Fit(self)

    def CocheTout(self,bool):
        self.parent.CocheTout(bool,self.IDparent)

# ----------------------------------------------------------------------------------------------------------------------------------------------------------------

class CTRL_Groupes_activites(ACheckListBox):
    def __init__(self, parent):
        ACheckListBox.__init__(self, parent, -1)
        self.nomCtrl = "Grp d'activité"
        self.Importation()

    def Importation(self):
        dateDeb = DateEngSQL(self.parent.ctrl_date_debut.Value)
        dateFin = DateEngSQL(self.parent.ctrl_date_fin.Value)
        if self.parent.check_avecConsos.Value:
            condDates = " consommations.date  >= '%s' And consommations.date <= '%s'" %(dateDeb,dateFin)
            table = "consommations"
        else:
            condDates = " inscriptions.date_inscription >= '%s' And inscriptions.date_inscription <= '%s' " %(dateDeb,dateFin)
            table = "inscriptions"

        DB = GestionDB.DB()
        # appel des activités filtrées sur les dates
        req = """
                SELECT IDactivite
                FROM %s
                WHERE (%s)
                ORDER BY IDactivite;
                """ %(table, condDates)
        DB.ExecuterReq(req,MsgBox="CTRL_ParamListeInscription1")
        recordset = DB.ResultatReq()
        self.listeActivites = []
        for record in recordset:
            self.listeActivites.append(record[0])
        recordset = []
        if len(self.listeActivites) > 0:
            lstAct= str(self.listeActivites)[1:-1]
            # appel des groupes d'activites représentés dans la liste d'activités
            req= """
                    SELECT types_groupes_activites.IDtype_groupe_activite, types_groupes_activites.nom, groupes_activites.IDactivite
                    FROM (activites
    
                          INNER JOIN groupes_activites ON activites.IDactivite = groupes_activites.IDactivite)
                    INNER JOIN types_groupes_activites ON groupes_activites.IDtype_groupe_activite = types_groupes_activites.IDtype_groupe_activite
                    WHERE activites.IDactivite In ( %s )
                    ORDER BY types_groupes_activites.nom;
                    """ % lstAct
            DB.ExecuterReq(req,MsgBox="CTRL_ParamListeInscription.importation1")
            recordset = DB.ResultatReq()
        DB.Close()
        self.StockDonnees(recordset)
        return

    def MAJ(self):
        self.Clear()
        self.Importation()
        self.MajBox()
        self.Modified()

    def Modified(self):
        self.oldListe = self.GetItems()
        self.oldListeChecked = self.GetListeChecked()
        self.parent.ctrl_activites.MAJ()

class CTRL_Activites(ACheckListBox):
    def __init__(self, parent):
        ACheckListBox.__init__(self, parent, -1)
        self.nomCtrl = "Activité"

    def Importation(self):
        DB = GestionDB.DB()
        self.listeIDactivites = self.parent.ctrl_groupes_activites.GetListeIDchildrenChecked()
        if len(self.listeIDactivites) == 0:
            lstIDact = " NULL "
        else:
            lstIDact = str(self.listeIDactivites)[1:-1]

        # appel des activites représentés dans la liste des groupes d'activités
        req= """
                SELECT activites.IDactivite, activites.nom, groupes.IDgroupe
                FROM activites 
                LEFT JOIN groupes ON activites.IDactivite = groupes.IDactivite
                WHERE activites.IDactivite IN ( %s )
                ORDER BY activites.nom;
                """ % lstIDact
        DB.ExecuterReq(req,MsgBox="CTRL_ParamListeInscription.importation2")
        recordset = DB.ResultatReq()
        DB.Close()
        self.StockDonnees(recordset)
        return

    def MAJ(self):
        self.Clear()
        self.Importation()
        self.MajBox()
        self.Modified()

    def Modified(self):
        self.oldListe = self.GetItems()
        self.oldListeChecked = self.GetListeChecked()
        self.parent.ctrl_groupes.MAJ()

class CTRL_Groupes(ACheckListBox):
    def __init__(self, parent):
        ACheckListBox.__init__(self, parent, -1)
        self.nomCtrl = "Groupe"

    def Importation(self):
        DB = GestionDB.DB()
        self.listeIDgroupes = self.parent.ctrl_activites.GetListeIDchildrenChecked()
        if len(self.listeIDgroupes) == 0:
            lstID = " NULL "
        else:
            lstID = str(self.listeIDgroupes)[1:-1]

        # appel des groupes représentés dans la liste des activités
        req= """
                SELECT IDgroupe, abrege, 0
                FROM groupes
                WHERE IDgroupe IN ( %s )
                ORDER BY abrege;
                """ % lstID
        DB.ExecuterReq(req,MsgBox="CTRL_ParamListeInscription.importation3")
        recordset = DB.ResultatReq()
        DB.Close()
        self.StockDonnees(recordset)
        return

    def MAJ(self):
        self.Clear()
        self.Importation()
        self.MajBox()
        self.Modified()

    def Modified(self):
        self.oldListe = self.GetItems()
        self.oldListeChecked = self.GetListeChecked()
        self.parent.ctrl_categories.MAJ()

class CTRL_Categories(ACheckListBox):
    def __init__(self, parent):
        ACheckListBox.__init__(self, parent, -1)
        self.nomCtrl = "Catégorie"

    def Importation(self):
        DB = GestionDB.DB()
        self.listeID = self.parent.ctrl_activites.GetListeIDchecked()
        if len(self.listeID) == 0:
            lstID = " NULL "
        else:
            lstID = str(self.listeID)[1:-1]

        # appel des catégories représentés dans la liste des activités
        req= """
                SELECT IDcategorie_tarif, nom, 0
                FROM categories_tarifs
                WHERE IDactivite IN ( %s )
                ORDER BY nom;
                """ % lstID
        DB.ExecuterReq(req,MsgBox="CTRL_ParamListeInscription.importation4")
        recordset = DB.ResultatReq()
        self.StockDonnees(recordset)
        DB.Close()
        return

    def MAJ(self):
        self.Clear()
        self.Importation()
        self.MajBox()
        self.Modified()

    def Modified(self):
        self.oldListe = self.GetItems()
        self.oldListeChecked = self.GetListeChecked()
        self.listeIDcategories = self.GetListeIDchecked()

# ----------------------------------------------------------------------------------------------------------------------------------

class CTRL_Options(ACheckListBox):
    def __init__(self, parent):
        ACheckListBox.__init__(self, parent, -1)
        self.nomCtrl = "Options"
        self.listeDonnees = list(DLD_CHAMPS.keys())
        self.listeDonnees.remove("entete")
        self.MajBox()
        self.CocheTout(False)
        return

    def MAJ(self):
        self.Modified()

    def Modified(self):
        self.oldListe = self.GetItems()
        self.oldListeChecked = self.GetListeChecked()
        self.parent.ctrl_colonnes.Importation()
    #fin CTRL_Options

class CTRL_Colonnes(ACheckListBox):
    def __init__(self, parent):
        ACheckListBox.__init__(self, parent, -1)
        self.listeChamps = []
        self.listeLabels = []
        self.listeChecked = []
        self.parent = parent
        self.SetMinSize((-1, 200))
        self.first = True

    def Label(self,option,dictTemp):
        if not isinstance(dictTemp,dict):
            return dictTemp
        return dictTemp["label"] + " (%s_%s)"%(option,dictTemp["code"])

    def Importation(self, selectCode=None):
        self.oldListeChamps = [x for x in self.listeChamps]
        self.listeChamps = [("entete",x) for x in DLD_CHAMPS["entete"]]
        try:
            for option in self.parent.ctrl_options.GetListeChecked():
                self.listeChamps.extend([(option,x) for x in DLD_CHAMPS[option]])
        except:
            pass
        #ajout de nouveaux champs
        for option,dictTemp in self.listeChamps:
            label = self.Label(option,dictTemp)
            if not (label in self.listeLabels):
                self.listeLabels.append(label)
                if dictTemp["afficher"]:
                    self.listeChecked.append(label)
        #suppression de champs retirés
        for option,dictTemp in self.oldListeChamps:
            if not ((option,dictTemp) in self.listeChamps):
                label = self.Label(option,dictTemp)
                if label in self.listeLabels:
                    self.listeLabels.remove(label)
                if label in self.listeChecked:
                    self.listeChecked.remove(label)
        self.MAJ()

    def MAJ(self,selection=None):
        # recompose l'affichage de la box
        self.listeDonnees = []
        self.checkUp = True
        # remontée des précochées en premier
        noChecked = []
        select = None
        for label in self.listeLabels:
            if label in self.listeChecked:
                self.listeDonnees.append(label)
                select = label
            else:
                noChecked.append(label)
        if selection == None: selection = select
        #finalisation selection du dernier champ actif et constitution de la liste de choix et précoche
        for label in noChecked:
            self.listeDonnees.append(label)
        self.MajBox(cocher = False)
        idx = 0
        for label in self.listeDonnees:
            if idx < len(self.listeChecked):
                self.Check(idx, check = True)
            else :
                self.Check(idx, check = False)
            idx += 1
        # Sélection
        if selection != None :
            selectCode = self.listeDonnees.index(selection)
            self.Select(selectCode)
            self.EnsureVisible(selectCode)
        #fin MAJ

    def Modified(self):
        self.checkUp = False
        selection = None
        listeChecked = self.GetListeChecked()
        for label in listeChecked:
            if not label in self.listeChecked:
                self.listeChecked.append(label)
                selection = label
        for label in self.listeChecked:
            if not (label in listeChecked):
                self.listeChecked.remove(label)
        if selection != None:
            selectCode = self.listeDonnees.index(label)
            self.Select(selectCode)
            self.EnsureVisible(selectCode)

    def GetListeColonnes(self):
        listeLabels = []
        nbreItems = self.GetCount() 
        for index in range(0, nbreItems):
            if self.IsChecked(index):
                label = self.GetString(index) 
                listeLabels.append(label)
        return listeLabels
        
    def GetIDcoches(self):
        listeIDcoches = []
        NbreItems = len(self.listeCategories)
        for index in range(0, NbreItems):
            if self.IsChecked(index):
                listeIDcoches.append(self.listeCategories[index][1])
        return listeIDcoches

    def Monter(self):
        index = self.GetSelection() 
        if index == -1 :
            dlg = wx.MessageDialog(self, _("Vous n'avez sélectionné aucune colonne à déplacer !"), _("Erreur"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return False
        if index == 0 :
            dlg = wx.MessageDialog(self, _("Cette colonne est déjà la première de la liste !"), _("Erreur"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return False
        self.DeplacerColonne(index, -1) 
            
    def Descendre(self):
        index = self.GetSelection() 
        if index == -1 :
            dlg = wx.MessageDialog(self, _("Vous n'avez sélectionné aucune colonne à déplacer !"), _("Erreur"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return False
        if index == len(self.listeDonnees)-1 :
            dlg = wx.MessageDialog(self, _("Cette colonne est déjà la dernière de la liste !"), _("Erreur"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return False
        self.DeplacerColonne(index, 1) 

    def DeplacerColonne(self, index=None, sens=1):
        code = self.listeDonnees[index]
        if not self.checkUp:
            self.MAJ(code)
            index = self.listeDonnees.index(code)
        code2 = self.listeDonnees[index + sens]
        # Récupération des colonnes
        index = 0
        indexCode = 0
        indexCode2 = 0
        for option, dictTemp in self.listeChamps :
            if self.Label(option,dictTemp) == code :
                indexCode = index
                dictCode = (option,dictTemp)
            if self.Label(option,dictTemp) == code2 :
                indexCode2 = index
                dictCode2 = (option,dictTemp)
            index += 1
        # Déplacement des colonnes
        self.listeChamps[indexCode] = dictCode2
        self.listeChamps[indexCode2] = dictCode
        self.listeLabels[indexCode] = self.Label(*dictCode2)
        self.listeLabels[indexCode2] = self.Label(*dictCode)
        self.MAJ(self.Label(*dictCode))

    def PlacerColonnes(self, listeColonnes):
        oldLstChamps = copy.deepcopy(self.listeChamps)
        self.listeChamps = []
        self.listeLabels = []
        index = 0
        self.listeChecked = []
        #priorité et ordre des colonnes remontées
        for colonne in listeColonnes:
            for option,dict in oldLstChamps:
                if len(colonne.split("(")) > 1:
                    label = self.Label(option,dict)
                else:
                    # format ancien stockage
                    label = dict["label"]
                if  label == colonne:
                    dict["afficher"] = True
                    self.listeChamps.append((option,dict))
                    self.listeLabels.append(self.Label(option,dict))
                    self.listeChecked.append(self.Label(option,dict))
                    oldLstChamps.remove((option,dict))
            index += 1

        self.oldListe = self.listeLabels
        #ajouter le reste
        for option,dict in oldLstChamps:
            dict["afficher"] = False
            self.listeChamps.append((option,dict))
            self.listeLabels.append(self.Label(option,dict))

        self.MAJ()
    #finCTRL_Colonnes

# ----------------------------------------------------------------------------------------------------------------------------------

class Parametres(wx.Panel):
    def __init__(self, parent, listview=None):
        wx.Panel.__init__(self, parent, id=-1, name="panel_parametres", style=wx.TAB_TRAVERSAL)
        self.parent = parent

        try :
            self.notebook = self.parent.notebook
            self.fromNotebook = True
        except :
            self.fromNotebook = False

        self.listview = listview
        self.box_selection_staticbox = wx.StaticBox(self, -1, _("Sélection des lignes"))

        # Période
        self.label_date_debut = wx.StaticText(self, -1, "Du")
        self.ctrl_date_debut = CTRL_Saisie_date.Date(self)
        self.bouton_date_debut = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Calendrier.png"), wx.BITMAP_TYPE_ANY))
        self.label_date_fin = wx.StaticText(self, -1, _("Au"))
        self.ctrl_date_fin = CTRL_Saisie_date.Date(self)
        self.bouton_date_fin = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Calendrier.png"), wx.BITMAP_TYPE_ANY))
        self.check_avecConsos = wx.CheckBox(self, -1, _("Avec des consommations dans les dates"))
        self.check_avecConsos.SetValue(True)
        self.dateDebut,self.dateFin = self.GetExercice()
        self.ctrl_date_debut.SetValue(self.dateDebut)
        self.ctrl_date_fin.SetValue(self.dateFin)

        # Groupes d'activités
        self.box_groupes_activites_staticbox = wx.StaticBox(self, -1, _("Groupes d'activités"))
        self.ctrl_groupes_activites = CTRL_Groupes_activites(self)
        self.ctrl_groupes_activites.SetMinSize((50, 50))
        self.ctrl_coche_grpAct = CocheToutRien(self,"grpAct")
        self.ctrl_coche_act = CocheToutRien(self,"act")
        self.ctrl_coche_grp = CocheToutRien(self,"grp")
        self.ctrl_coche_cat = CocheToutRien(self,"cat")

        # Activités
        self.box_activites_staticbox = wx.StaticBox(self, -1, _("Activités"))
        self.ctrl_activites = CTRL_Activites(self)
        #self.ctrl_activites.SetMinSize((50, 50))

        # Groupes
        self.box_groupes_staticbox = wx.StaticBox(self, -1, _("Groupes"))
        self.ctrl_groupes = CTRL_Groupes(self)
        
        # Catégories
        self.box_categories_staticbox = wx.StaticBox(self, -1, _("Catégories"))
        self.ctrl_categories = CTRL_Categories(self)

        self.box_composition_staticbox = wx.StaticBox(self, -1, _("Composition contenu"))

        # Colonnes
        self.box_colonnes_staticbox = wx.StaticBox(self, -1, _("Colonnes"))
        self.ctrl_colonnes = CTRL_Colonnes(self)
        self.bouton_haut = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Fleche_haut.png"), wx.BITMAP_TYPE_ANY))
        self.bouton_bas = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Fleche_bas.png"), wx.BITMAP_TYPE_ANY))
        self.bouton_reinitialisation = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Actualiser.png"), wx.BITMAP_TYPE_ANY))
        self.bouton_sauvegarde = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Sauvegarder.png"), wx.BITMAP_TYPE_ANY))

        # Options
        self.box_options_staticbox = wx.StaticBox(self, -1, _("Options plus de colonnes"))
        self.ctrl_options = CTRL_Options(self)

        # Actualiser
        self.bouton_ok = CTRL_Bouton_image.CTRL(self, texte=_("Valider"), cheminImage=Chemins.GetStaticPath("Images/32x32/Valider.png"))

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_CHECKBOX, self.OnConsos, self.check_avecConsos)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonDateDebut, self.bouton_date_debut)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonDateFin, self.bouton_date_fin)
        self.Bind(wx.EVT_CHOICE, self.OnChoixGroupesActivtes, self.ctrl_groupes_activites)
        self.Bind(wx.EVT_CHOICE, self.OnChoixActivites, self.ctrl_activites)
        self.Bind(wx.EVT_CHOICE, self.OnChoixOptions, self.ctrl_options)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonActualiser, self.bouton_ok)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonHaut, self.bouton_haut)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonBas, self.bouton_bas)
        self.bouton_reinitialisation.Bind(wx.EVT_BUTTON, self.OnBoutonReinit)
        self.bouton_sauvegarde.Bind(wx.EVT_BUTTON, self.OnBoutonSauve)

    def __set_properties(self):
        self.ctrl_groupes_activites.SetToolTip(_("Cochez des groupes pour présélectionner les activités"))
        self.ctrl_activites.SetToolTip(_("Cochez les activités des groupes d'activités"))
        self.ctrl_groupes.SetToolTip(_("Cochez les groupes des activités"))
        self.ctrl_categories.SetToolTip(_("Cochez les catégories des activités"))
        self.ctrl_options.SetToolTip(_("Sélectionnez une options"))
        self.ctrl_colonnes.SetToolTip(_("Cochez les colonnes souhaitées"))
        self.bouton_ok.SetToolTip(_("Cliquez ici pour actualiser la liste"))
        self.bouton_haut.SetToolTip(_("Cliquez ici pour monter la colonne"))
        self.bouton_bas.SetToolTip(_("Cliquez ici pour descendre la colonne"))
        self.bouton_reinitialisation.SetToolTip(_("Cliquez ici pour restaurer des paramètres"))
        self.bouton_sauvegarde.SetToolTip(_("Cliquez ici pour mémoriser les paramètres"))
        self.ctrl_date_debut.SetToolTip(_("Saisissez ici une date de début"))
        self.bouton_date_debut.SetToolTip(_("Cliquez ici pour saisir une date de début"))
        self.ctrl_date_fin.SetToolTip(_("Saisissez ici une date de fin"))
        self.bouton_date_fin.SetToolTip(_("Cliquez ici pour saisir une date de fin"))
        self.check_avecConsos.SetToolTip(_("En décochant, le filtre sera sur les dates de création des inscriptions. \nLes devis et inscriptions sans consos seront alors inclus"))
        self.ctrl_groupes_activites.MAJ()

    def __do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(rows=2, cols=1, vgap=5, hgap=5)
        grid_sizer_contenu = wx.FlexGridSizer(rows=1, cols=2, vgap=5, hgap=5)
        # Gauche - sélection des lignes
        box_selection = wx.StaticBoxSizer(self.box_selection_staticbox, wx.VERTICAL)
        grid_sizer_gauche = wx.FlexGridSizer(rows=6, cols=1, vgap=5, hgap=5)

        # Période
        grid_sizer_dates = wx.FlexGridSizer(rows=1, cols=6, vgap=5, hgap=5)
        grid_sizer_dates.Add(self.label_date_debut, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_dates.Add(self.ctrl_date_debut, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_dates.Add(self.bouton_date_debut, 0, 0, 0)
        grid_sizer_dates.Add(self.label_date_fin, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_dates.Add(self.ctrl_date_fin, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_dates.Add(self.bouton_date_fin, 0, 0, 0)
        grid_sizer_gauche.Add(grid_sizer_dates, 1, wx.ALIGN_CENTER_HORIZONTAL, 0)
        grid_sizer_gauche.Add(self.check_avecConsos, 1, wx.LEFT|wx.EXPAND, 40)

        # Groupes d'activité
        box_grpactiv = wx.StaticBoxSizer(self.box_groupes_activites_staticbox, wx.HORIZONTAL)
        box_grpactiv.Add(self.ctrl_groupes_activites, 1, wx.ALL|wx.EXPAND, 5)
        box_grpactiv.Add(self.ctrl_coche_grpAct, 0, wx.ALL, 0)
        grid_sizer_gauche.Add(box_grpactiv, 1, wx.LEFT|wx.EXPAND, 25)

        # Activité
        box_activite = wx.StaticBoxSizer(self.box_activites_staticbox, wx.HORIZONTAL)
        box_activite.Add(self.ctrl_activites, 1, wx.ALL|wx.EXPAND, 5)
        box_activite.Add(self.ctrl_coche_act, 0, wx.ALL, 0)
        grid_sizer_gauche.Add(box_activite, 1, wx.LEFT|wx.EXPAND, 25)

        # Groupes
        box_groupes = wx.StaticBoxSizer(self.box_groupes_staticbox, wx.HORIZONTAL)
        box_groupes.Add(self.ctrl_groupes, 1, wx.ALL|wx.EXPAND, 5)
        box_groupes.Add(self.ctrl_coche_grp, 0, wx.ALL, 0)
        grid_sizer_gauche.Add(box_groupes, 1, wx.LEFT|wx.EXPAND, 25)
        
        # Catégories
        box_categories = wx.StaticBoxSizer(self.box_categories_staticbox, wx.HORIZONTAL)
        box_categories.Add(self.ctrl_categories, 1, wx.ALL|wx.EXPAND, 5)
        box_categories.Add(self.ctrl_coche_cat, 0, wx.ALL, 0)
        grid_sizer_gauche.Add(box_categories, 1, wx.LEFT|wx.EXPAND, 25)
        
        grid_sizer_gauche.AddGrowableRow(2)
        grid_sizer_gauche.AddGrowableRow(3)
        grid_sizer_gauche.AddGrowableRow(4)
        grid_sizer_gauche.AddGrowableRow(5)
        grid_sizer_gauche.AddGrowableCol(0)
        box_selection.Add(grid_sizer_gauche, 1,wx.LEFT|wx.EXPAND, 5)
        grid_sizer_contenu.Add(box_selection, 1, wx.LEFT|wx.EXPAND,5)

        # Droite - contenu des lignes
        box_composition = wx.StaticBoxSizer(self.box_composition_staticbox, wx.VERTICAL)
        grid_sizer_droite = wx.FlexGridSizer(rows=3, cols=1, vgap=5, hgap=5)

        # Options
        box_options = wx.StaticBoxSizer(self.box_options_staticbox, wx.VERTICAL)
        box_options.Add(self.ctrl_options, 1, wx.ALL|wx.EXPAND, 5)
        grid_sizer_droite.Add(box_options, 1, wx.LEFT|wx.EXPAND, 25)
        
        # Colonnes
        box_colonnes = wx.StaticBoxSizer(self.box_colonnes_staticbox, wx.VERTICAL)
        grid_sizer_colonnes = wx.FlexGridSizer(rows=1, cols=2, vgap=5, hgap=5)
        grid_sizer_colonnes.Add(self.ctrl_colonnes, 1, wx.EXPAND, 0)
        
        grid_sizer_boutons_colonnes = wx.FlexGridSizer(rows=5, cols=1, vgap= 5, hgap=5)
        grid_sizer_boutons_colonnes.Add(self.bouton_haut, 0, 0, 0)
        grid_sizer_boutons_colonnes.Add(self.bouton_bas, 0, 0, 0)
        grid_sizer_boutons_colonnes.Add((10,10), 0, 0, 0)
        grid_sizer_boutons_colonnes.Add(self.bouton_reinitialisation, 0, 0, 0)
        grid_sizer_boutons_colonnes.Add(self.bouton_sauvegarde, 0, 0, 0)
        grid_sizer_colonnes.Add(grid_sizer_boutons_colonnes, 0, wx.LEFT|wx.EXPAND, 0)
        
        grid_sizer_colonnes.AddGrowableRow(0)
        grid_sizer_colonnes.AddGrowableCol(0)
        box_colonnes.Add(grid_sizer_colonnes, 1, wx.ALL|wx.EXPAND, 5)
        grid_sizer_droite.Add(box_colonnes, 1, wx.LEFT|wx.EXPAND, 0)

        grid_sizer_droite.AddGrowableRow(0)
        grid_sizer_droite.AddGrowableCol(0)
        box_composition.Add(grid_sizer_droite, 1, wx.LEFT|wx.EXPAND, 5)
        grid_sizer_contenu.Add(box_composition, 1,wx.ALL| wx.EXPAND, 10)
        grid_sizer_contenu.AddGrowableRow(0)
        grid_sizer_contenu.AddGrowableCol(1)
        grid_sizer_contenu.AddGrowableCol(0)

        grid_sizer_base.Add(grid_sizer_contenu, 1, wx.ALL|wx.EXPAND, 0)

        # Bouton validation
        grid_sizer_validation = wx.FlexGridSizer(rows=1, cols=2, vgap=5, hgap=5)
        grid_sizer_validation.Add((20,20), 1, wx.EXPAND, 0)
        grid_sizer_validation.Add(self.bouton_ok, 1,wx.RIGHT|wx.LEFT| wx.EXPAND, 200)
        grid_sizer_validation.AddGrowableRow(0)
        grid_sizer_validation.AddGrowableCol(1)
        grid_sizer_base.Add(grid_sizer_validation, 1,wx.ALIGN_CENTER_HORIZONTAL|wx.EXPAND, 0)

        grid_sizer_base.AddGrowableRow(0)
        grid_sizer_base.AddGrowableCol(0)
        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)

    def OnChoixGroupesActivtes(self, event):
        lstIDgrpActivites = self.ctrl_groupes_activites.GetActivite()
        self.ctrl_activites.SetActivite(lstIDgrpActivites)
        self.OnChoixActivites()

    def OnChoixActivites(self, event):
        lstIDactivites = self.ctrl_activites.GetActivite()
        self.ctrl_groupes.SetActivite(lstIDactivites)
        self.ctrl_categories.SetActivite(lstIDactivites)

    def OnChoixOptions(self, event):
        pass
    
    def CocheTout(self,bool,ID):
        if ID == "grpAct" :
            self.ctrl_groupes_activites.CocheTout(bool)
        if ID == "act" :
            self.ctrl_activites.CocheTout(bool)
        if ID == "grp" :
            self.ctrl_groupes.CocheTout(bool)
        if ID == "cat" :
            self.ctrl_categories.CocheTout(bool)

    def OnChoixDate(self):
        self.ctrl_groupes_activites.MAJ()

    def OnConsos(self,event):
        self.ctrl_groupes_activites.MAJ()

    def OnBoutonDateDebut(self, event):
        dlg = DLG_calendrier_simple.Dialog(self)
        if dlg.ShowModal() == wx.ID_OK :
            date = dlg.GetDate()
            self.ctrl_date_debut.SetDate(date)
        self.ctrl_groupes_activites.MAJ()
        dlg.Destroy()

    def OnBoutonDateFin(self, event):
        dlg = DLG_calendrier_simple.Dialog(self)
        if dlg.ShowModal() == wx.ID_OK :
            date = dlg.GetDate()
            self.ctrl_date_fin.SetDate(date)
        dlg.Destroy()
        self.ctrl_groupes_activites.MAJ()

    def OnBoutonHaut(self, event):
        self.ctrl_colonnes.Monter()
        
    def OnBoutonBas(self, event):
        self.ctrl_colonnes.Descendre()

    def OnBoutonReinit(self,event):
        #reprise de param stockés
        dlg = DLG_GestionParams.Dialog(self,setGet="get",categorie="liste_inscriptions",titre="Reprise d'un paramétrage")
        ret = dlg.ShowModal()
        if ret == wx.ID_OK:
            strDictParams = dlg.GetParam()
            if len(strDictParams) > 5:
                dictParams = StringToDict(strDictParams)
                self.SetDictParams(dictParams)
        dlg.Destroy()

    def OnBoutonSauve(self,event):
        #sauve les params repris ensuite par reinit
        param = str(self.GetDictParams())
        dlg = DLG_GestionParams.Dialog(self,setGet="set",paramToSet=param,categorie="liste_inscriptions",titre="Sauvegarde du paramétrage")
        dlg.ShowModal()
        dlg.Destroy()

    def GetDictParams(self):
        #récupère l'ensemble des choix dans un dictionnaire
        dict={}
        dict["avecConsos"] = self.check_avecConsos.GetValue()
        dict["groupes_activites"]= self.ctrl_groupes_activites.GetListeChecked()
        dict["activites"]= self.ctrl_activites.GetListeChecked()
        dict["groupes"]= self.ctrl_groupes.GetListeChecked()
        dict["categories"]= self.ctrl_categories.GetListeChecked()
        dict["options"]= self.ctrl_options.GetListeChecked()
        dict["colonnes"]= self.ctrl_colonnes.GetListeChecked()
        return dict

    def SetDictParams(self,dict):
        #restaure l'ensemble des choix d'un dictionnaire
        self.check_avecConsos.SetValue(dict["avecConsos"])
        self.ctrl_groupes_activites.CocheListe(dict["groupes_activites"])
        self.ctrl_activites.CocheListe(dict["activites"])
        if len(self.ctrl_activites.GetListeChecked()) ==0:
            self.ctrl_activites.CocheTout(True)
        self.ctrl_groupes.CocheListe(dict["groupes"])
        self.ctrl_options.CocheListe(dict["options"])
        self.ctrl_colonnes.PlacerColonnes(dict["colonnes"])
        return

    def OnChoixMasquerActivite(self, event):
        self.ctrl_activites.MAJ()

    def OnBoutonActualiser(self, event):
        # Récupération des paramètres
        listeIDactivites = self.ctrl_activites.GetListeIDchecked()
        listeIDgroupes = self.ctrl_groupes.GetListeIDchecked()
        listeIDcategories = self.ctrl_categories.GetListeIDchecked()
        listeOptions = ["entete",]
        listeOptions.extend(self.ctrl_options.GetListeChecked())
        listeLabelsColonnes = self.ctrl_colonnes.GetListeColonnes()
        listeColonnes = []
        Label = self.ctrl_colonnes.Label
        for option in listeOptions:
            for champ in DLD_CHAMPS[option]:
                if Label(option,champ) in listeLabelsColonnes:
                    listeColonnes.append(champ["code"])
        # Vérifications
        if len(listeIDactivites) == 0 :
            dlg = wx.MessageDialog(self, _("Vous n'avez sélectionné aucune activité !"), _("Erreur"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return False

        if len(listeIDgroupes) == 0 :
            dlg = wx.MessageDialog(self, _("Vous devez sélectionner au moins un groupe !"), _("Erreur"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return False

        if len(listeIDcategories) == 0 :
            dlg = wx.MessageDialog(self, _("Vous devez sélectionner au moins une catégorie !"), _("Erreur"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return False

        if len(listeColonnes) == 0 :
            dlg = wx.MessageDialog(self, _("Vous devez cocher au moins une colonne !"), _("Erreur"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return False
        
        labelParametres = self.GetLabelParametres()
        listview = self.notebook.page1.ctrl_listview

        #listview.listeChamps pointe la variable globale LISTE_CHAMPS
        listview.listeChamps = []
        for labelChecked in listeLabelsColonnes:
            for option,dict in self.ctrl_colonnes.listeChamps:
                if self.ctrl_colonnes.Label(option,dict) == labelChecked :
                    listview.listeChamps.append(dict)
        if not "IDfam" in listview.listeChamps:
            for option,dict in self.ctrl_colonnes.listeChamps:
                if dict["label"] == "IDfam" :
                    listview.listeChamps.append(dict)
        # MAJ du listview
        if self.fromNotebook :
            self.notebook.page1.ctrl_listview.MAJ(listeActivites=listeIDactivites,  listeGroupes=listeIDgroupes, listeCategories=listeIDcategories, listeOptions=listeOptions, listeColonnes=listeColonnes, labelParametres=labelParametres)
            self.notebook.AffichePage("liste")

    def GetLabelParametres(self):
        listeParametres = []
        
        activites = self.ctrl_activites.GetListeChecked()
        listeParametres.append(_("Activités : %s") % activites)

        groupes = self.ctrl_groupes.GetListeChecked()
        listeParametres.append(_("Groupes : %s") % groupes)

        categories = self.ctrl_categories.GetListeChecked()
        listeParametres.append(_("Catégories : %s") % categories)

        labelParametres = " | ".join(listeParametres)
        return labelParametres

    def GetExercice(self):
        DB = GestionDB.DB()
        req = """SELECT date_debut, date_fin
                FROM compta_exercices """
        retour = DB.ExecuterReq(req,MsgBox="CTRL_ParamListeInscription.GetExercice")
        if retour != "ok" :
            wx.MessageBox(str(retour))
        recordset = DB.ResultatReq()
        dateDebut = None
        dateFin = None
        if len(recordset)>0 :
            dd, df  = recordset[0]
            dateDebut = DateEngFr(dd)
            dateFin = DateEngFr(df)
        DB.Close()
        return dateDebut,dateFin
    #fin Parametres

# Dialog pour test --------------------------------------------------------------------------------------------------------------------------------------------------
class Dialog(wx.Dialog):
    def __init__(self, parent, minSize=(100, 100)):
        wx.Dialog.__init__(self, parent, -1, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX)
        self.parent = parent
        self.SetMinSize(minSize)
        self.box_selection_staticbox = wx.StaticBox(self, -1, _("Objets pour test"))

        from Ol import OL_Liste_inscriptions
        self.listviewAvecFooter = OL_Liste_inscriptions.ListviewAvecFooter(self, kwargs={})
        self.ctrl_listview = self.listviewAvecFooter.GetListview()
        self.ctrl_recherche = OL_Liste_inscriptions.CTRL_Outils(self, listview=self.ctrl_listview)
        self.panel = Parametres(self, listview=self.ctrl_listview)

        sizer_2 = wx.FlexGridSizer(rows=2, cols=1, vgap=10, hgap=10)
        sizer_2.Add(self.panel, 1, wx.ALL|wx.EXPAND, 0)

        box_test = wx.StaticBoxSizer(self.box_selection_staticbox, wx.VERTICAL)
        #box_test.Add(self.ctrl_listview, 1, wx.LEFT|wx.EXPAND, 25)
        #box_test.Add(self.ctrl_recherche, 1, wx.ALL|wx.EXPAND, 0)
        sizer_2.Add(box_test, 1, wx.ALL|wx.EXPAND, 0)

        sizer_2.AddGrowableRow(0)
        sizer_2.AddGrowableCol(0)

        self.SetSizer(sizer_2)
        sizer_2.Fit(self)
        self.Layout()
        self.CenterOnScreen()
        #fin Dialog pour test


if __name__ == "__main__":
    app = wx.App(0)
    #wx.InitAllImageHandlers()
    dialog_1 = Dialog(None)
    app.SetTopWindow(dialog_1)
    print(dialog_1.ShowModal())
    app.MainLoop()

