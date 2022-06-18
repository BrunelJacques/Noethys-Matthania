#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, Matthania
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS, JB
# Copyright:       (c) 2010-11 Ivan LUCAS, JB
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------

from Utils.UTILS_Traduction import _
import GestionDB
import copy

from Data import DATA_Civilites as Civilites

DICT_CIVILITES = Civilites.GetDictCivilites()

def Ajout(part1, part2, sep="; "):
    # Concaténation de deux parties si non nulles avec un séparateur
    final = ""
    # ajour d'un séparateur si part1 non vide
    if part1 and (len(part1.strip()) > 0):
        final = part1.strip()
        if part2 and len(part2.strip()) > 0:
            final += sep
    if part2 and (len(part2.strip()) > 0):
        final += part2.strip()
    return final

def AjoutContacts(dFamille, dIndividu):
    # insère dans dFamille, les mails et téléphones présents dans dIndividu
    if not "telephones" in dFamille:
        dFamille["telephones"] = ""
    nb = 0
    for key in ("tel_mobile","tel_mobile2","tel_domicile","tel_travail"):
        if key in dIndividu and dIndividu[key]:
            # le champ mobile2 est l'ancien travail_fax, il contient des numéros de fax à éviter
            if key == "tel_mobile2" and not dIndividu[key][:2] in ("06","07"):
                continue
            lg = len(dFamille["telephones"])
            dFamille["telephones"] = Ajout(dFamille["telephones"],dIndividu[key])
            if lg != len(dFamille["telephones"]):
                nb +=1
        # deux numéros de téléphone maxi
        if nb == 2:
            break
    dFamille["telephones"] = dFamille["telephones"].replace('.', ' ')

    if not "mails" in dFamille or len(dFamille["mails"]) == 0:
        dFamille["mails"] = ""
        dFamille["mail_famille"] = ""

    for key in ("mail","travail_mail"):
            dFamille["mails"] = Ajout(dFamille["mails"],dIndividu[key])
    # cas du correspondant mail et téléphone seront ceux de la famille
    if not "correspondant" in list(dFamille.keys()):
        dFamille["correspondant"] = None

    if "IDindividu" in dIndividu and dFamille["correspondant"] == dIndividu["IDindividu"]:
        dFamille["mail_famille"] = dIndividu["mail"]
        if not dIndividu["mail"] : dFamille["mail_famille"] = dIndividu["travail_mail"]
        dFamille["telephone_famille"] = dIndividu["tel_domicile"]
        if not dIndividu["tel_domicile"]: dFamille["telephone_famille"] = dIndividu["tel_mobile"]

    # pas de return car w dans le pointeur dict

def AjoutNomAdresse(dFamille, dIndividu):
    strIDcivilite = dIndividu["IDcivilite"]
    if strIDcivilite != None:
        nomCivilite = ("%s " % DICT_CIVILITES[int(strIDcivilite)][
            "civiliteAbrege"]).strip()
    else:
        nomCivilite = ""
    # Recherche de l'adresse du correspondant
    dictAdresse = {}
    dictAdresse["rue"] = dIndividu["rue"]
    dictAdresse["cp"] = dIndividu["cp"]
    dictAdresse["ville"] = dIndividu["ville"]

    dFamille["IDcivilite"] = strIDcivilite
    dFamille["civilite"] = nomCivilite
    dFamille["nom"] = dIndividu["nom"]
    dFamille["prenom"] = dIndividu["prenom"]
    dFamille["adresse"] = dictAdresse


def GetFamillesEtiq(listeIDfamille=[]):
    # Composition du where sur les rattachements
    """ si listeIDfamille == [] alors renvoie toutes les familles avec titulaires"""
    if len(listeIDfamille) == 0:
        conditionFamilles = "WHERE (rattachements.titulaire = 1  OR familles.adresse_individu = rattachements.IDindividu)"
    elif len(listeIDfamille) == 1:
        conditionFamilles = "WHERE (rattachements.titulaire = 1  OR familles.adresse_individu = rattachements.IDindividu) AND rattachements.IDfamille=%d" % \
                            listeIDfamille[0]
    else:
        conditionFamilles = "WHERE  (rattachements.titulaire = 1  OR familles.adresse_individu = rattachements.IDindividu) AND rattachements.IDfamille IN %s" % str(
            tuple(listeIDfamille))

    DB = GestionDB.DB()

    # Récupération de tous les titulaires des familles ou des correspondants
    req = """
    SELECT rattachements.IDfamille,rattachements.IDindividu, rattachements.IDcategorie, 
            individus.IDcivilite, individus.nom, individus.prenom, individus.date_naiss, individus.adresse_auto, 
            individus.rue_resid, individus.cp_resid, individus.ville_resid,individus.adresse_normee, individus.refus_pub,
            individus.refus_mel,individus.mail, individus.travail_mail, 
            individus.tel_domicile, individus.tel_mobile,individus.tel_fax, 
            individus.travail_tel, familles.adresse_intitule, familles.refus_pub, familles.refus_mel, familles.adresse_individu,
            individus_1.rue_resid, individus_1.cp_resid, individus_1.ville_resid, individus_1.adresse_normee
    FROM ((rattachements
            INNER JOIN individus ON rattachements.IDindividu = individus.IDindividu) 
            INNER JOIN familles ON rattachements.IDfamille = familles.IDfamille) 
            LEFT JOIN individus AS individus_1 ON individus.adresse_auto = individus_1.IDindividu
    %s
    ORDER BY rattachements.IDindividu
    ;""" % conditionFamilles
    DB.ExecuterReq(req, MsgBox="UTILS_Titulaires 1")
    ltplIndividus = DB.ResultatReq()
    dictIndividus = {}
    dictFamilles = {}
    DB.Close()

    def compacte(adresse):
        compactee = ""
        if adresse:
            lst = adresse.split("\n")
            for ligne in lst:
                if len(ligne) > 0:
                    compactee += ligne + "\n"
            if len(compactee) > 0:
                compactee = compactee[:-1]
        return compactee

    # Constitution de deux dictionnaires famille et individu
    for IDfamille, IDindividu, IDcategorie, IDcivilite, nom, prenom, date_naiss, adresse_auto, rue_resid, cp_resid, ville_resid, \
        adresse_normee, refus_pub_ind, refus_mel_ind, mail, travail_mail, tel_domicile, tel_mobile, tel_mobile2, travail_tel, \
        designation_famille, refus_pub_fam, refus_mel_fam, correspondant, rue_resid_1, cp_resid_1, ville_resid_1, adresse_normee_1 \
            in ltplIndividus:
        if adresse_auto:
            rue_resid = rue_resid_1
            cp_resid = cp_resid_1
            ville_resid = ville_resid_1
            adresse_normee = adresse_normee_1
        if not rue_resid: rue_resid = ''
        if not cp_resid: cp_resid = ''
        if not prenom:  prenom = ""
        if not nom:  nom = ""
        # priorité des refus actés sur les non actés
        if refus_pub_fam:
            refus_pub_ind = refus_pub_fam
        if refus_mel_fam:
            refus_mel_ind = refus_mel_fam
        rue_resid = compacte(rue_resid)
        ville_resid = compacte(ville_resid)
        dictIndividus[IDindividu] = {
            "IDindividu":IDindividu,
            "IDcivilite": str(IDcivilite), "nom": nom, "prenom": prenom, "date_naiss": date_naiss,
            "rue": rue_resid, "cp": cp_resid, "ville": ville_resid, "adresse_normee": adresse_normee,
            "mail": mail,
            "travail_mail": travail_mail,
            "tel_domicile": tel_domicile,
            "tel_mobile": tel_mobile,
            "tel_mobile2": tel_mobile2,
            "travail_tel": travail_tel,
            "designation_famille": designation_famille, "refus_pub": refus_pub_ind, "refus_mel": refus_mel_ind,
        }

        lstTitulaires = [(IDindividu, IDfamille, IDcategorie,), ]
        lstIDtitulaires = [ IDindividu,]

        if (IDfamille in dictFamilles) == False:
            dictFamilles[IDfamille] = {
                "IDcompte_payeur": IDfamille,
                "IDfamille": IDfamille,
                "titulaires": lstTitulaires,
                "IDtitulaires": lstIDtitulaires,
                "designation_famille": designation_famille,
                "correspondant": correspondant,
                "refus_pub": refus_pub_fam, "refus_mel": refus_mel_fam,
                "mail_famille":"","mails":"",
                "telephone_famille":"","telephones":""}
        else:
            dictFamilles[IDfamille]["titulaires"] += lstTitulaires
            dictFamilles[IDfamille]["IDtitulaires"] += lstIDtitulaires

    # Reprise pour détermination des adresses principales et secondaires
    lstCorrespondants = []
    dictBis = {}
    for IDfamille in list(dictFamilles.keys()):
        if IDfamille == 709:
            print()
        # recherche des coordonnées du correspondant de la famille
        dictFamille = dictFamilles[IDfamille]
        designation_famille = dictFamille["designation_famille"]
        correspondant = dictFamille["correspondant"]
        if (not correspondant) or (not correspondant in dictFamille["IDtitulaires"]):
            # pas de correspondant dans la famille on prend le premier titulaire sinon on passe
            if len(dictFamille["IDtitulaires"]) == 0:
                continue
            correspondant = dictFamille["IDtitulaires"][0]
            dictFamille["correspondant"] = correspondant

        AjoutNomAdresse(dictFamille,dictIndividus[correspondant])
        AjoutContacts(dictFamille, dictIndividus[correspondant]) # ajoute les telephones et mail de l'individu

        dictFamille["typeRattachement"] = "C"
        dictFamille["titulairesSansCivilite"] = "%s %s" % (dictFamille["nom"], dictFamille["prenom"])
        dictFamille["titulairesAvecCivilite"] = "%s%s %s" % (
                    dictFamille["civilite"],
                    dictFamille["nom"],
                    dictFamille["prenom"])

        lstCorrespondants.append(IDindividu)
        dictFamille["titulaires"] = [(x,y,z) for (x,y,z) in dictFamille["titulaires"] if x != correspondant]
        dictFamille["IDtitulaires"].remove(correspondant)

        if IDindividu in list(dictBis.keys()):
            # ce titulaire a fait l'objet d'une fiche en tant que non correspondant, on la supprime
            del dictBis["I" + str(IDindividu)]

        # traitement des titulaires non correspondants.
        for IDindividu, IDfamilleTmp, IDcategorie, in dictFamille["titulaires"]:
            if IDindividu in list(dictBis.keys()):
                # reçoit déjà un courrier à son adresse perso
                continue
            dictIndividu = dictIndividus[IDindividu]
            dictAdresse = dictFamilles[IDfamille]["adresse"]
            # cas d'une adresse commune on enrichit les données de la famille par cumuls des noms,civilité,mel,téléphone
            if dictAdresse["rue"] + dictAdresse["cp"] == dictIndividu["rue"] + dictIndividu["cp"]:
                IDcivilite2 = dictIndividu["IDcivilite"]
                dictFamille["IDcivilite"] += " " + str(IDcivilite2)
                if IDcivilite2 != None:
                    nomCivilite2 = (" %s" % DICT_CIVILITES[int(IDcivilite2)]["civiliteAbrege"]).strip()
                else:
                    nomCivilite2 = ""
                dictFamille["civilite"] += nomCivilite2
                nom, prenom = dictIndividu["nom"], dictIndividu["prenom"]
                if dictFamille["nom"] == nom:
                    # même nom pour le nouveau titulaire
                    dictFamille["prenom"] += " et " + prenom
                else:
                    # nom différent pour le nouveau titulaire
                    nomprenom1 = dictFamille["nom"] + ' ' + dictFamille["prenom"]
                    nomprenom2 = nom + ' ' + prenom
                    dictFamille["prenom"] = ""
                    dictFamille["nom"] = nomprenom1 + " et " + nomprenom2
                dictFamille["typeRattachement"] += 'T'
                dictFamille["titulairesSansCivilite"] = "%s %s" % (dictFamille["nom"], dictFamille["prenom"])
                dictFamille["titulairesAvecCivilite"] = "%s %s %s" % (dictFamille["civilite"], dictFamille["nom"],
                                                                      dictFamille["prenom"])
                dictFamille["IDtitulaires"].append(IDindividu)
                AjoutContacts(dictFamille, dictIndividu) # ajoute les telephones et mail de l'individu

            # le nouveau titulaire à une adresse différente on crée une occurence de type I
            else:
                # son étiquette sera sous le numéro de l'individu (crée un famille virtuelle Ixxxx)
                titulaire = "I" + str(IDindividu)
                # reprend les éléments de la famille
                dictBis[titulaire] = copy.deepcopy(dictFamilles[IDfamille])
                dest = dictBis[titulaire]

                # personnalise les éléments de base
                AjoutNomAdresse(dest, dictIndividu)
                AjoutContacts(dest, dictIndividu)
                # adapte comme une pseudo famille
                dest["typeRattachement"] = 'T'
                dest["titulairesSansCivilite"] = "%s %s" % (dest["nom"], dest["prenom"])
                dest["titulairesAvecCivilite"] = "%s%s %s" % (dest["civilite"], dest["nom"], dest["prenom"])

                dest["correspondant"] = IDindividu
                dest["designation_famille"] = dest["nom"] + " " + dest["prenom"]

    # Fusion des titulaires aux adresses différentes
    for cle, dict in dictBis.items():
        dictFamilles[cle] = dict
    return dictFamilles

def GetTitulaires(listeIDfamille=[]):
    """ si listeIDfamille == [] alors renvoie toutes les familles """
    dictFamilles = {}
    # Condition
    if len(listeIDfamille) == 0:
        conditionFamilles = ""
    elif len(listeIDfamille) == 1 and listeIDfamille[0] == None:
        return dictFamilles
    elif len(listeIDfamille) == 1:
        conditionFamilles = "WHERE IDfamille=%d" % listeIDfamille[0]
    else:
        conditionFamilles = "WHERE IDfamille IN %s" % str(tuple(listeIDfamille))

    DB = GestionDB.DB()

    # Récupération des familles
    req = """
    SELECT IDfamille, IDcompte_payeur,adresse_intitule,adresse_individu
    FROM familles
    %s;""" % conditionFamilles
    DB.ExecuterReq(req,MsgBox="UTILS_Titulaires.GetTitulaires")
    listeFamilles = DB.ResultatReq()
    for IDfamille, IDcompte_payeur, designation, individu in listeFamilles:
        dictFamilles[IDfamille] = {"IDcompte_payeur": IDcompte_payeur, "designation": designation,
                                   "correspondant": individu}

    # Récupération des rattachements
    req = """SELECT IDrattachement, IDindividu, IDfamille, IDcategorie, titulaire
    FROM rattachements
    %s;""" % conditionFamilles
    DB.ExecuterReq(req,MsgBox="ExecuterReq")
    listeDonnees = DB.ResultatReq()
    dictRattachements = {}
    lstIDindividus = []
    for IDrattachement, IDindividu, IDfamille, IDcategorie, titulaire in listeDonnees:
        lstIDindividus.append(IDindividu)
        if (IDfamille in dictRattachements) == False:
            dictRattachements[IDfamille] = [(IDrattachement, IDindividu, IDfamille, IDcategorie, titulaire), ]
        else:
            dictRattachements[IDfamille].append((IDrattachement, IDindividu, IDfamille, IDcategorie, titulaire))

    # Récupération des individus rattachés

    def compacte(adresse):
        compactee = ""
        if adresse:
            lst = adresse.split("\n")
            for ligne in lst:
                if len(ligne) > 0:
                    compactee += ligne + "\n"
            if len(compactee) > 0:
                compactee = compactee[:-1]
        return compactee

    def getDictIndividus(lstIDindividus):
        dictIndividus = {}
        listeIndividus = []
        if len(lstIDindividus) > 0:
            req = """
            SELECT IDindividu, IDcivilite, individus.nom, prenom, date_naiss, adresse_auto, rue_resid, cp_resid, ville_resid,
                    mail, travail_mail, individus.IDsecteur, secteurs.nom, 
                    tel_domicile, tel_mobile, individus.tel_fax, travail_tel
            FROM individus
            LEFT JOIN secteurs ON secteurs.IDsecteur = individus.IDsecteur
            WHERE IDindividu in (%s)
            ;""" % str(lstIDindividus)[1:-1]
            DB.ExecuterReq(req, MsgBox="UTILS_Titulaires 1")
            listeIndividus = DB.ResultatReq()

        for IDindividu, IDcivilite, nom, prenom, date_naiss, adresse_auto, rue_resid, cp_resid, ville_resid, mail, travail_mail, \
            IDsecteur, nomSecteur, tel_domicile, tel_mobile, tel_mobile2, travail_tel in listeIndividus:
            rue_resid = compacte(rue_resid)
            ville_resid = compacte(ville_resid)
            dictIndividus[IDindividu] = {
                "IDcivilite": IDcivilite, "nom": nom, "prenom": prenom,
                "date_naiss": date_naiss, "adresse_auto": adresse_auto,
                "rue_resid": rue_resid, "cp_resid": cp_resid, "ville_resid": ville_resid,
                "mail": mail,
                "travail_mail": travail_mail,
                "IDsecteur": IDsecteur, "nomSecteur": nomSecteur,
                "tel_domicile": tel_domicile,
                "tel_mobile": tel_mobile,
                "tel_mobile2": tel_mobile2,
                "travail_tel": travail_tel
            }
        return dictIndividus

    dictIndividus = getDictIndividus(lstIDindividus)

    # Recherche des noms des titulaires pour composer un dictFamilles envoyé en return
    for IDfamille, dictFamille in dictFamilles.items():
        # Il y a au moins un titulaire rattaché à la famille
        if IDfamille in dictRattachements:
            listeIndividusFamilles = dictRattachements[IDfamille]
            listeTitulaires = []
            nbreTitulaires = 0
            aine = 0
            NaissanceAine = "9999-99-99"
            listeMembres = []

            # constitution d'un dictTitulaires
            for IDrattachement, IDindividuTmp, IDfamilleTmp, IDcategorie, titulaire in listeIndividusFamilles:
                if IDindividuTmp in dictIndividus:
                    listeMembres.append(IDindividuTmp)
                    if str(dictIndividus[IDindividuTmp]["date_naiss"]) < str(NaissanceAine):
                        NaissanceAine = dictIndividus[IDindividuTmp]["date_naiss"]
                        aine = IDindividuTmp
                    if titulaire == 1:
                        nom = dictIndividus[IDindividuTmp]["nom"]
                        prenom = dictIndividus[IDindividuTmp]["prenom"]
                        if prenom == None: prenom = ""
                        IDcivilite = dictIndividus[IDindividuTmp]["IDcivilite"]
                        if IDcivilite != None :
                            libCivilite = ("%s " % DICT_CIVILITES[IDcivilite]["civiliteAbrege"]).strip()
                        else:
                            libCivilite = ""
                        mail = dictIndividus[IDindividuTmp]["mail"]
                        dictTemp = {
                            "IDindividu": IDindividuTmp, "IDcivilite": IDcivilite, "nom": nom, "prenom": prenom,
                            "mail": mail,
                            "nomSansCivilite": "%s %s" % (nom, prenom),
                            "nomAvecCivilite": "%s%s %s" % (libCivilite, nom, prenom),
                            "civilite": "%s" % libCivilite,
                            "travail_mail": dictIndividus[IDindividuTmp]["travail_mail"],
                            "tel_domicile": dictIndividus[IDindividuTmp]["tel_domicile"],
                            "tel_mobile": dictIndividus[IDindividuTmp]["tel_mobile"],
                            "tel_mobile2": dictIndividus[IDindividuTmp]["tel_mobile2"],
                            "travail_tel": dictIndividus[IDindividuTmp]["travail_tel"],
                        }
                        listeTitulaires.append(dictTemp)
                        nbreTitulaires += 1

            # gestion de l'absence de titulaire en prenant l'ainé
            if nbreTitulaires == 0:
                nbreTitulaires = 1
                IDcivilite = dictIndividus[aine]["IDcivilite"]
                if IDcivilite != None :
                    libCivilite = ("%s " % DICT_CIVILITES[IDcivilite]["civiliteAbrege"]).strip()
                else:
                    libCivilite = ""
                nom = dictIndividus[aine]["nom"]
                prenom = dictIndividus[aine]["prenom"]
                dictIndividus[aine]["nomSansCivilite"] = "%s %s" % (nom, prenom)
                dictIndividus[aine]["nomAvecCivilite"] = "%s%s %s" % (libCivilite, nom, prenom),
                dictIndividus[aine]["civilite"] = "%s" % libCivilite
                dictIndividus[aine]["IDindividu"] = aine
                listeTitulaires.append(dictIndividus[aine])

            # Gestion de la désignation et adresse de la famille
            civilite = ComposeCivilites(listeTitulaires)
            if nbreTitulaires == 1:
                nomsTitulaires = {
                    "IDcivilite": listeTitulaires[0]["IDcivilite"],
                    "sansCivilite": listeTitulaires[0]["nomSansCivilite"],
                    "avecCivilite": civilite + " " + listeTitulaires[0]["nomAvecCivilite"],
                    "civilite": civilite,
                }
            if nbreTitulaires == 2:
                # le nom est commun
                if listeTitulaires[0]["nom"] == listeTitulaires[1]["nom"]:
                    nomsTitulaires = {
                        "IDcivilite": listeTitulaires[0]["IDcivilite"],
                        "sansCivilite": _("%s %s et %s") % (listeTitulaires[0]["nom"],
                                                             listeTitulaires[0]["prenom"],
                                                             listeTitulaires[1]["prenom"]),
                        "avecCivilite": _("%s %s et %s") % (listeTitulaires[0]["nom"],
                                                             listeTitulaires[0]["prenom"],
                                                             listeTitulaires[1]["prenom"]),
                        "civilite": civilite
                    }
                else:
                    # chacun a gardé son nom
                    nomsTitulaires = {
                        "IDcivilite": listeTitulaires[0]["IDcivilite"],
                        "sansCivilite": _("%s et %s") % (
                        listeTitulaires[0]["nomSansCivilite"], listeTitulaires[1]["nomSansCivilite"]),
                        "avecCivilite": _("%s et %s") % (
                        listeTitulaires[0]["nomAvecCivilite"], listeTitulaires[1]["nomAvecCivilite"]),
                        "civilite": civilite
                    }
            if nbreTitulaires > 2:
                nomsSansCivilite = ""
                nomsAvecCivilite = ""
                for dictTemp in listeTitulaires[:-2]:
                    nomsAvecCivilite += "%s, " % dictTemp["nomAvecCivilite"]
                    nomsSansCivilite += "%s, " % dictTemp["nomSansCivilite"]
                nomsAvecCivilite += _("%s et %s") % (
                listeTitulaires[-2]["nomAvecCivilite"], listeTitulaires[-1]["nomAvecCivilite"])
                nomsSansCivilite += _("%s et %s") % (
                listeTitulaires[-2]["nomSansCivilite"], listeTitulaires[-1]["nomSansCivilite"])
                nomsTitulaires = {
                    "IDcivilite": listeTitulaires[0]["IDcivilite"],
                    "sansCivilite": nomsSansCivilite,
                    "avecCivilite": nomsAvecCivilite,
                    "civilite": civilite
                }

            # récup du correspondant dans la table famille qui va écraser les test précédents sauf si désignation null
            if dictFamilles[IDfamille]["designation"] and len(dictFamilles[IDfamille]["designation"]) > 0:
                dictFamilles[IDfamille]["nom"] = dictFamilles[IDfamille]["designation"]
                designation = dictFamilles[IDfamille]["designation"]
                (civilite, nom) = CutCivilite(designation)
                nomsTitulaires = {
                    "IDcivilite": listeTitulaires[0]["IDcivilite"],
                    "sansCivilite": nom,
                    "avecCivilite": designation,
                    "civilite": civilite
                }
            if dictFamilles[IDfamille]["correspondant"]:
                IDcorrespondant = dictFamilles[IDfamille]["correspondant"]
            else:
                IDcorrespondant = listeTitulaires[0]["IDindividu"]

            # Recherche de l'adresse de la famille
            lstChampsAdr = ['rue_resid', 'cp_resid', 'ville_resid',
                            'IDsecteur', 'nomSecteur','adresse_auto',]
            lstClesAdr = ["rue", "cp", "ville", "IDsecteur", "nomSecteur" ]

            def getAdresse(ID):
                # récupére l'adresse d'un individu
                if ID in list(dictIndividus.keys()):
                    dictTemp = {ID:dictIndividus[ID]}
                else:
                    # l'adresse cherchée est hors des familles en liste
                    dictTemp = getDictIndividus([ID,])
                adresse = {'rue_residence':"Adresse non trouvée"}
                if ID in list(dictTemp.keys()) and  len(list(dictTemp[ID].keys()))>= len(lstClesAdr):
                    for ix in range(len(lstClesAdr)):
                        adresse[lstClesAdr[ix]] = dictTemp[ID][lstChampsAdr[ix]]
                    # boucle jusqu'à trouver une adresse non auto
                    if dictTemp[ID]['adresse_auto'] and dictTemp[ID]['adresse_auto'] > 0 and dictTemp[ID]['adresse_auto'] != ID:
                        adresse = getAdresse(dictTemp[ID]['adresse_auto'])
                return adresse

            # le correspondant peut ne pas avoir une adresse en propre
            adresse = {"rue": "", "cp": "", "ville": "", "IDsecteur": None, "nomSecteur": ""}
            adresse.update(getAdresse(IDcorrespondant))
            # Recherche des adresses Emails des titulaires
            mails = []
            for dictTemp in listeTitulaires:
                AjoutContacts(dictFamilles[IDfamille],dictTemp)

            # Définit les noms des titulaires
            dictFamilles[IDfamille]["IDcivilite"] = nomsTitulaires["IDcivilite"]
            dictFamilles[IDfamille]["titulairesAvecCivilite"] = nomsTitulaires["avecCivilite"]
            dictFamilles[IDfamille]["titulairesSansCivilite"] = nomsTitulaires["sansCivilite"]
            dictFamilles[IDfamille]["titulairesCivilite"] = nomsTitulaires["civilite"]
            dictFamilles[IDfamille]["listeTitulaires"] = listeTitulaires
            dictFamilles[IDfamille]["adresse"] = adresse
            dictFamilles[IDfamille]["listeMembres"] = listeMembres

        # Aucun rattachement pour cette famille
        else:
            dictFamilles[IDfamille]["IDcivilite"] = 0
            dictFamilles[IDfamille]["titulairesAvecCivilite"] = _("%d sans titulaire" % IDfamille)
            dictFamilles[IDfamille]["titulairesSansCivilite"] = _("%d sans titulaire" % IDfamille)
            dictFamilles[IDfamille]["titulairesCivilite"] = ""
            dictFamilles[IDfamille]["listeTitulaires"] = []
            dictFamilles[IDfamille]["adresse"] = {"rue": "Aucun rattachement", "cp": "", "ville": "",
                                                  "IDsecteur": None, "nomSecteur": "",}
            dictFamilles[IDfamille]["mails"] = ""
            dictFamilles[IDfamille]["mail_famille"] = ""
            dictFamilles[IDfamille]["listeMails"] = []
            dictFamilles[IDfamille]["tel_famille"] = ""
            dictFamilles[IDfamille]["telephones"] = ""
            dictFamilles[IDfamille]["listeMembres"] = []

        # pour la compatibilité avec Noethys original
        lstMails =  dictFamille["mails"].split(";")
        if len(dictFamille["mail_famille"]) > 0:
            lstAutres = [x for x in lstMails if x.strip() != dictFamille["mail_famille"].strip() ]
            dictFamille["listeMails"] = [dictFamille["mail_famille"],] + lstAutres
        else:
            dictFamille["listeMails"] = lstMails
    DB.Close()
    return dictFamilles

def GetIndividus(listeIDindividus=[]):
    # retourne un dictionnaire de dictionnaires des cordonnées des individus de la liste
    if len(listeIDindividus) == 0:
        conditionIndividus = ""
    elif len(listeIDindividus) == 1:
        conditionIndividus = "WHERE IDindividu=%d" % listeIDindividus[0]
    else:
        conditionIndividus = "WHERE IDindividu IN %s" % str(tuple(listeIDindividus))

    """ Importe les individus et recherche leurs noms et adresses """
    DB = GestionDB.DB()
    req = """
    SELECT IDindividu, IDcivilite, individus.nom, prenom, date_naiss, adresse_auto, rue_resid, cp_resid, ville_resid,
            mail, individus.IDsecteur, secteurs.nom
    FROM individus
    LEFT JOIN secteurs ON secteurs.IDsecteur = individus.IDsecteur
    %s
    ;""" % conditionIndividus
    DB.ExecuterReq(req,MsgBox="ExecuterReq")
    listeDonnees = DB.ResultatReq()
    DB.Close()
    dictTemp = {}
    for IDindividu, IDcivilite, nom, prenom, date_naiss, adresse_auto, rue_resid, cp_resid, ville_resid, mail, IDsecteur, nomSecteur in listeDonnees:
        if nomSecteur == None: nomSecteur = ""
        dictTemp[IDindividu] = {
            "IDcivilite": IDcivilite, "nom": nom, "prenom": prenom, "date_naiss": date_naiss,
            "adresse_auto": adresse_auto, "rue": rue_resid, "cp": cp_resid, "ville": ville_resid, "mail": mail,
            "IDsecteur": IDsecteur, "nomSecteur": nomSecteur}

    # Recherche les noms et adresses de chaque individu
    dictIndividus = {}
    for IDindividu, dictIndividu in dictTemp.items():

        # Civilité
        IDcivilite = dictIndividu["IDcivilite"]
        if IDcivilite == None:
            IDcivilite = 1
        dictIndividu["civiliteAbrege"] = DICT_CIVILITES[IDcivilite]["civiliteAbrege"]
        dictIndividu["civiliteLong"] = DICT_CIVILITES[IDcivilite]["civiliteLong"]
        dictIndividu["sexe"] = DICT_CIVILITES[IDcivilite]["sexe"]

        # Nom complet
        if dictIndividu["prenom"] != None:
            dictIndividu["nom_complet"] = "%s %s" % (dictIndividu["nom"], dictIndividu["prenom"])
        else:
            dictIndividu["nom_complet"] = dictIndividu["nom"]

        # Adresse
        adresse_auto = dictIndividu["adresse_auto"]
        if adresse_auto != None and adresse_auto in dictTemp:
            dictIndividu["rue"] = dictTemp[adresse_auto]["rue"]
            dictIndividu["cp"] = dictTemp[adresse_auto]["cp"]
            dictIndividu["ville"] = dictTemp[adresse_auto]["ville"]
            dictIndividu["IDsecteur"] = dictTemp[adresse_auto]["IDsecteur"]
            dictIndividu["nomSecteur"] = dictTemp[adresse_auto]["nomSecteur"]

        dictIndividus[IDindividu] = dictIndividu

    return dictIndividus

def CutCivilite(designation):
    if designation[-4:] == ' et ':
        designation = designation[:-4]
    nom = designation
    civilite = ''
    lstmots = designation.split(' ')
    if len(lstmots) > 1:
        nom = ''
        # Extraction d'un radical de civilité dans chaque mot
        for ix in range(len(lstmots)):
            mot = lstmots[ix]
            # Repère les mots commençant par une civilité
            if lstmots[ix][:2] in ('Mr', 'MM', 'Mm', 'M.', 'Ml', 'M&','Fa',"M"):
                isCivil = False
                # Tronque les mots commençant par l'une de ces civilités
                for item in ('MrMme', 'MmeMr', 'Mmes', 'Mlle', 'MM.','MMr','Mme', 'Famille'):
                    # l'item est entier au début, on le prend
                    if mot[:len(item)] == item:
                        rad = item
                        isCivil = True
                        break
                # Le radical peut se limiter aux deux premiers caractères repérés
                if not isCivil and mot[:2]!= 'Fa':
                    rad = mot[:2]
                    isCivil = True               
                if isCivil:
                    # découpe du radical
                    civilite += rad + ' '
                    mot = mot[len(rad):]
                    # Suppression des liaisons ramenées en début
                    for sep in ('&', ',', 'et', '-', '.'):
                        if mot[:len(sep)] == sep:
                            civilite += sep + ' '
                            mot = mot[len(sep):]
                        # cas du mot suivant qui contient la liaison on la prend avec
                        else:
                            if (ix < len(lstmots) - 1) and (lstmots[ix + 1][:len(sep)] == sep):
                                civilite += sep + ' '
                                lstmots[ix + 1] = lstmots[ix + 1][len(sep):]

            # recompose le nom
            if len(mot)>0:
                nom += (mot+' ')
    civilite = civilite.replace(' ,', ',')
    civilite = civilite.replace(' -', ',')
    while len(designation) > len(nom):
        designation = nom
        civ, nom = CutCivilite(nom)
        civilite += civ
    return civilite.strip(), nom.strip()

def ComposeCivilites(lstTitulaires=[]):
    # ajoute les civilités dans l'ordre des clés croissante des individus
    civilite = ""
    lstCivilites = []
    for dict in lstTitulaires:
        if "civilite" in dict:
            if not dict["civilite"] in lstCivilites:
                lstCivilites.append(dict["civilite"])
    for civil in lstCivilites:
        civilite += civil
    return civilite.strip()

def GetCorrespondants(listeIDfamille=[]):
    # Composition du where sur les rattachements
    """ si listeIDfamille == [] alors renvoie toutes les familles"""
    if len(listeIDfamille) == 0:
        conditionFamilles = ""
    elif len(listeIDfamille) == 1:
        conditionFamilles = "WHERE familles.IDfamille=%d" % listeIDfamille[0]
    else:
        conditionFamilles = "WHERE familles.IDfamille IN %s" % str(tuple(listeIDfamille))

    DB = GestionDB.DB()

    # Récupération coordonnées des correspondants
    champs = ["IDfamille","IDindividu","designation","IDcivilite", "nom", "prenom", "date_naiss", "adresse_auto",
              "rue_resid", "cp_resid", "ville_resid", "mail", "travail_mail",
              "tel_domicile", "tel_mobile","tel_mobile2", "travail_tel", "refus_pub", "refus_mel"]
    req = """
    SELECT  familles.IDfamille, individus.IDindividu, familles.adresse_intitule,
            individus.IDcivilite, individus.nom, individus.prenom, individus.date_naiss, individus.adresse_auto,
            individus.rue_resid, individus.cp_resid, individus.ville_resid, 
            individus.mail, individus.travail_mail, 
            individus.tel_domicile, individus.tel_mobile, individus.tel_fax,individus.travail_tel, 
            individus.refus_pub,individus.refus_mel

    FROM familles INNER JOIN individus ON familles.adresse_individu = individus.IDindividu
    %s
    ;""" % conditionFamilles
    DB.ExecuterReq(req, MsgBox="UTILS_Titulaires.GetCorrespondants")
    listeDonnees = DB.ResultatReq()
    dictFamilles = {}

    def compacte(adresse):
        compactee = ""
        if adresse:
            lst = adresse.split("\n")
            for ligne in lst:
                if len(ligne) > 0:
                    compactee += ligne + "\n"
            if len(compactee) > 0:
                compactee = compactee[:-1]
        return compactee

    # Constitution du dictionnaire famille


    # alimenentation des coordonnées du représentant, (un record maxi)
    for record in listeDonnees:
        dRepres = {}
        for champ in champs:
            dRepres[champ] = record[champs.index(champ)]

        dRepres["rue_resid"] = compacte(dRepres["rue_resid"])
        dRepres["ville_resid"] = compacte(dRepres["ville_resid"])
        dRepres["prenomNom"] = dRepres["prenom"] + " " + dRepres["nom"]
        AjoutContacts(dRepres,dRepres)

        # Civilité
        IDcivilite = dRepres["IDcivilite"]
        if IDcivilite == None:
            IDcivilite = 1
        dRepres["civiliteAbrege"] = DICT_CIVILITES[IDcivilite]["civiliteAbrege"]
        dRepres["civiliteLong"] = DICT_CIVILITES[IDcivilite]["civiliteLong"]
        dRepres["sexe"] = DICT_CIVILITES[IDcivilite]["sexe"]

        # Nom complet
        if dRepres["prenom"] != None:
            dRepres["nom_complet"] = "%s %s" % (dRepres["nom"], dRepres["prenom"])
        else:
            dRepres["nom_complet"] = dRepres["nom"]
        dictFamilles[dRepres["IDfamille"]] = dRepres
    # Reprise pour détermination des adresses pricipales et secondaires
    return dictFamilles

def GetCorrespondant(IDfamille=None, IDindividu=None):
    # retourne un dictionnaire avec les coordonnées postales, téléphones, mails du représentant de la famille
    if not (IDfamille or IDindividu): return None
    DB = GestionDB.DB()
    IDrepresentant = None
    dict = None
    # recherche de la famille si ID individu
    designation = None
    if not IDfamille:
        req = """SELECT rattachements.IDfamille
                FROM rattachements
                WHERE (((rattachements.IDindividu) = %d) AND ((rattachements.IDcategorie)<3))
                ORDER BY rattachements.IDfamille DESC;
        ;""" % IDindividu
        DB.ExecuterReq(req, MsgBox="UTILS_Titulaires.GetCorrespondant(IDindividu=%d)" % IDindividu)
        recordset = DB.ResultatReq()
        # si pas de famille en tant qu'enfant ou parent l'individu se représente lui-même
        if len(recordset) < 1:
            IDrepresentant = IDindividu
        else:
            IDfamille = recordset[0][0]
    # recherche du représentant de la famille
    isRepres = False
    designation = "!!! %d "%IDindividu
    if IDfamille:
        req = """SELECT adresse_individu, adresse_intitule
                FROM familles
                WHERE (familles.IDfamille = %d);
        ;""" % IDfamille
        DB.ExecuterReq(req, MsgBox="UTILS_Titulaires.GetCorrespondant(IDfamille=%d)" % IDfamille)
        recordset = DB.ResultatReq()
        # si pas représentant de sa famille l'individu se representera lui-même
        if len(recordset) < 1 or recordset[0][0] == None:
            IDrepresentant = IDindividu
        else:
            IDrepresentant = recordset[0][0]
            designation = recordset[0][1]
            isRepres = True
    # appel des coordonnées du représentant
    if IDrepresentant:
        champs = ["IDcivilite", "nom", "prenom", "date_naiss", "adresse_auto", "rue_resid",
                  "cp_resid", "ville_resid", "mail", "travail_mail",
                  "tel_domicile", "tel_mobile", "tel_mobile2", "travail_tel", "refus_pub", "refus_mel"]
        req = """
        SELECT individus.IDcivilite,individus.nom, individus.prenom, individus.date_naiss, individus.adresse_auto, individus.rue_resid,
            individus.cp_resid, individus.ville_resid, individus.mail, individus.travail_mail, 
            individus.tel_domicile, individus.tel_mobile, individus.tel_fax,individus.travail_tel, individus.refus_pub, individus.refus_mel
        FROM individus
        WHERE IDindividu = %d
        ;""" % IDrepresentant
        DB.ExecuterReq(req, MsgBox="UTILS_Titulaires.GetCorrespondant(IDrepresentat=%d)" % IDrepresentant)
        listeDonnees = DB.ResultatReq()

        # alimenentation des coordonnées du représentant, (un record maxi)
        for record in listeDonnees:
            dict = {}
            for champ in champs:
                dict[champ] = record[champs.index(champ)]
            # cas improbable d'un représentant sans adresse perso
            if dict["adresse_auto"]:
                req = """
                SELECT individus.nom, individus.prenom, individus.date_naiss, individus.adresse_auto, individus.rue_resid,
                    individus.cp_resid, individus.ville_resid, individus.mail, individus.travail_mail, 
                    individus.tel_domicile, individus.tel_mobile, individus.tel_fax,individus.travail_tel, individus.refus_pub, individus.refus_mel
                FROM individus
                WHERE IDindividu == %d
                ;""" % dict["adresse_auto"]
                DB.ExecuterReq(req, MsgBox="UTILS_Titulaires.GetCorrespondant(adresse_auto=%d)" % dict["adresse_auto"])
                listeAuto = DB.ResultatReq()
                for champ in champs[4:]:
                    dict[champ] = listeAuto[champs.index(champ)]
            if not isRepres:
                dict["prenom"] = designation + dict["prenom"]
            dict["designation"] = designation
            dict["prenomNom"] = dict["prenom"] + " " + dict["nom"]
            AjoutContacts(dict,dict)

            # Civilité
            IDcivilite = dict["IDcivilite"]
            if IDcivilite == None:
                IDcivilite = 1
            dict["civiliteAbrege"] = DICT_CIVILITES[IDcivilite]["civiliteAbrege"]
            dict["civiliteLong"] = DICT_CIVILITES[IDcivilite]["civiliteLong"]
            dict["sexe"] = DICT_CIVILITES[IDcivilite]["sexe"]

            # Nom complet
            if dict["prenom"] != None:
                dict["nom_complet"] = "%s %s" % (dict["nom"], dict["prenom"])
            else:
                dict["nom_complet"] = dict["nom"]

    DB.Close()
    return dict

if __name__ == '__main__':
    #print GetCorrespondant(IDindividu=16672)
    dic = GetTitulaires(listeIDfamille=[709,])
    for k in list(dic.keys()):
        if len(dic[k]["titulairesCivilite"])>0:
            print((dic[k]["titulairesCivilite"],'   >>  ',dic[k]['titulairesSansCivilite']))
