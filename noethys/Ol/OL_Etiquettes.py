#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, Matthania
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS, JB, Jacques Brunel
# Copyright:       (c) 2010-14 Ivan LUCAS, JB
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------


from Utils.UTILS_Traduction import _
import Chemins
import wx
import GestionDB
import datetime
from Utils import UTILS_Utilisateurs
from Utils import UTILS_Titulaires
from Utils import UTILS_Questionnaires
from Data import DATA_Civilites as Civilites
from Ctrl.CTRL_ObjectListView import FastObjectListView, ColumnDefn, Filter, CTRL_Outils, PanelAvecFooter

def DateEngEnDateDD(dateEng):
    if dateEng and not isinstance(dateEng,str): dateEng = str(dateEng)
    return datetime.date(int(dateEng[:4]), int(dateEng[5:7]), int(dateEng[8:10]))

def FormateStr(valeur=""):
    try :
        if valeur == None : return ""
        elif type(valeur) == int : return str(valeur)
        elif type(valeur) == float : return str(valeur)
        else : return valeur
    except :
        return ""

def FormateDate(dateStr):
    if dateStr == "" or dateStr == None : return ""
    date = str(datetime.date(year=int(dateStr[:4]), month=int(dateStr[5:7]), day=int(dateStr[8:10])))
    text = str(date[8:10]) + "/" + str(date[5:7]) + "/" + str(date[:4])
    return text

def GetInfosOrganisme():
    # Récupération des infos sur l'organisme
    DB = GestionDB.DB()
    req = """SELECT nom, rue, cp, ville, tel, fax, mail, site, num_agrement, num_siret, code_ape
    FROM organisateur
    WHERE IDorganisateur=1;"""
    DB.ExecuterReq(req,MsgBox="ExecuterReq")
    listeDonnees = DB.ResultatReq()
    DB.Close()
    dictOrganisme = {}
    for nom, rue, cp, ville, tel, fax, mail, site, num_agrement, num_siret, code_ape in listeDonnees :
        if ville != None : ville = ville.capitalize()
        dictOrganisme["{ORGANISATEUR_NOM}"] = nom
        dictOrganisme["{ORGANISATEUR_RUE}"] = rue
        dictOrganisme["{ORGANISATEUR_CP}"] = cp
        dictOrganisme["{ORGANISATEUR_VILLE}"] = ville
        dictOrganisme["{ORGANISATEUR_TEL}"] = tel
        dictOrganisme["{ORGANISATEUR_FAX}"] = fax
        dictOrganisme["{ORGANISATEUR_MAIL}"] = mail
        dictOrganisme["{ORGANISATEUR_SITE}"] = site
        dictOrganisme["{ORGANISATEUR_AGREMENT}"] = num_agrement
        dictOrganisme["{ORGANISATEUR_SIRET}"] = num_siret
        dictOrganisme["{ORGANISATEUR_APE}"] = code_ape
    return dictOrganisme

class DictDiffusion(object):
    def __init__(self):
        DB = GestionDB.DB()
        # récupération des nom de listes
        req = """
            SELECT listes_diffusion.IDliste,listes_diffusion.nom
            FROM ((individus INNER JOIN abonnements ON individus.IDindividu = abonnements.IDindividu)
                             INNER JOIN listes_diffusion ON abonnements.IDliste = listes_diffusion.IDliste)
                 LEFT JOIN individus AS individus_1 ON individus.adresse_auto = individus_1.IDindividu
            GROUP BY listes_diffusion.IDliste,listes_diffusion.nom;
            """
        DB.ExecuterReq(req,MsgBox="ExecuterReq")
        recordset = DB.ResultatReq()
        self.lstIDdiffusions = []
        self.lstNomsDiffusions = []
        self.dictDiffusions = {}
        # récupération des abonnés à chacune des listes
        for IDdiffusion, nomDiffusion in recordset:
            self.lstIDdiffusions.append(IDdiffusion)
            self.lstNomsDiffusions.append(nomDiffusion)
            strIDdiffusions = str(self.lstIDdiffusions)[1:-1]
            req = """
                SELECT abonnements.IDindividu
                FROM abonnements
                WHERE (abonnements.IDliste = %d )
                GROUP BY abonnements.IDindividu;
                ;""" % IDdiffusion
            DB.ExecuterReq(req,MsgBox="ExecuterReq")
            tupleIDabonne = DB.ResultatReq()
            self.dictDiffusions[IDdiffusion]={}
            self.dictDiffusions[IDdiffusion]["nom"]= nomDiffusion
            self.dictDiffusions[IDdiffusion]["tplIDs"]= tupleIDabonne
        DB.Close()

#-----------INDIVIDUS-----------

class TrackIndividu(object):
    def __init__(self, listview, donnees,refusPub):
        self.listview = listview
        self.IDindividu = donnees["individus.IDindividu"]
        self.IDfamille = donnees["MIN(rattachements.IDfamille)"]
        if self.IDfamille == None : self.IDfamille = 0
        if donnees["individus.IDcivilite"]:
            self.IDcivilite = str(donnees["individus.IDcivilite"])
        else: self.IDcivilite = ""
        self.nom = donnees["individus.nom"]
        self.civiliteAbrege = donnees["civiliteAbrege"]
        if not self.civiliteAbrege or len(self.civiliteAbrege.strip()) == 0:
            self.civiliteAbrege = ""
        else:
            self.civiliteAbrege = self.civiliteAbrege.strip()+" "
        self.prenom = donnees["individus.prenom"]
        self.designation = (self.civiliteAbrege + self.nom + " " + self.prenom).strip()
        self.date_naiss = donnees["individus.date_naiss"]
        self.age = donnees["age"]
        self.adresse_auto = donnees["individus.adresse_auto"]
        self.refus_pub = donnees["individus.refus_pub"]
        self.refus_mel = donnees["individus.refus_mel"]

        # Adresse auto ou manuelle
        if self.adresse_auto != None :
            if not donnees["individus_1.ville_resid"]: donnees["individus_1.ville_resid"]=""
            self.rue_resid = donnees["individus_1.rue_resid"]
            self.ville_resid = donnees["individus_1.ville_resid"]
            self.cp = donnees["individus_1.cp_resid"]
            lstville = donnees["individus_1.ville_resid"].split("\n")
            if len(lstville)>0 : self.ville = lstville[0]
            else: self.ville = ""
            if len(lstville)>1:
                self.pays = lstville[1]
            else: self.pays = ""
        else:
            if not donnees["individus.ville_resid"]: donnees["individus.ville_resid"]=""
            self.rue_resid = donnees["individus.rue_resid"]
            self.ville_resid = donnees["individus.ville_resid"]
            self.cp = donnees["individus.cp_resid"]
            lstville = donnees["individus.ville_resid"].split("\n")
            if len(lstville)>0 : self.ville = lstville[0]
            else: self.ville = ""
            if len(lstville)>1:
                self.pays = lstville[1]
            else: self.pays = ""
        if not self.cp: self.cp = ""
        # gestion des sauts de lignes dans la rue
        if donnees["individus.rue_resid"] == None: donnees["individus.rue_resid"]=""
        if not self.rue_resid : self.rue_resid = ""
        lstRue = self.rue_resid.split("\n")
        lenRue = len(lstRue)
        # compléter la liste à 4lignes mais les vides seront ignorées à l'édition
        if len(self.designation) >=39 and lenRue < 4:
            if len(self.civiliteAbrege + self.nom) >= 39:
                # une partie du nom va glisser au début du prénom
                lnom = self.nom.split(" ")
                while len(self.civiliteAbrege + self.nom) >= 39 and len(lnom) > 1:
                    self.prenom = lnom[-1] + " " +self.prenom
                    del lnom[-1]
                    self.nom = ""
                    for mot in lnom:
                        self.nom += mot + " "
                    self.nom = self.nom.strip()
                    self.prenom = self.prenom.strip()
            # le prénom prend une deuxième ligne dans le nom pour forcer le saut de ligne
            if len(self.prenom) > 0:
                self.nom = self.nom + "\n" + self.prenom
                self.prenom = ""
        for i in range(lenRue,4):
            lstRue.append("")
        self.rue1 = lstRue[0]
        self.rue2 = lstRue[1]
        self.rue3 = lstRue[2]
        self.rue4 = lstRue[3]
        self.dpt = None
        if len(str(self.cp))>2 and ((not self.pays) or len(self.pays)>0):
            self.dpt = str(self.cp)[:2]
        self.valide = True
        if refusPub:
            if len(self.cp) == 0: self.valide = False
            elif self.cp[:2] in ('0 ','00','  '): self.valide = False
            elif len(self.cp) == 1 and self.cp[:1] in ('0',' '): self.valide = False
            elif self.refus_pub: self.valide = False

        # Ajout des adresses Emails des titulaires
        self.mails = ""
        if donnees["individus.mail"] != None :
            self.mails = donnees["individus.mail"] + "; "
        if donnees["individus.travail_mail"] != None :
            self.mails += donnees["individus.travail_mail"]

        # Ajout des téléphones des titulaires
        self.telephones = ""
        liste = ["individus.tel_domicile","individus.tel_mobile","individus.travail_tel","individus.tel_fax","individus.travail_fax"]
        for nomTel in liste:
            if donnees[nomTel] != None:
                if len(donnees[nomTel])> 3:
                    self.telephones += donnees[nomTel] + "; "
        if len(self.telephones) > 0 :
            self.telephones = str(self.telephones)[:-2]

        self.genre = donnees["genre"]
        self.categorieCivilite = donnees["categorieCivilite"]
        self.civiliteLong = donnees["civiliteLong"]
        self.nomImage = donnees["nomImage"]

        # Récupération des réponses des questionnaires
        for dictQuestion in self.listview.LISTE_QUESTIONS :
            exec("self.question_%d = self.listview.GetReponse(%d, %s)" % (dictQuestion["IDquestion"], dictQuestion["IDquestion"], self.IDindividu))

        # Récupération des appartenances aux listes de diffusion
        for IDdiffusion in list(self.listview.dictDiffusions.keys()) :
            if (self.IDindividu,) in self.listview.dictDiffusions[IDdiffusion]["tplIDs"] :
                exec("self.diffusion_%d = 'x'" % (IDdiffusion))
            else: exec("self.diffusion_%d = None" % (IDdiffusion))

    def GetDict(self):

        dictTemp = {
            "{IDINDIVIDU}" : str(self.IDindividu),
            "{IDFAMILLE}" : str(self.IDfamille),
            "{CODEBARRES_ID_INDIVIDU}" : "I%06d" % self.IDindividu,
            "{INDIVIDU_CIVILITE_LONG}" : FormateStr(self.civiliteLong),
            "{INDIVIDU_CIVILITE_COURT}" : FormateStr(self.civiliteAbrege),
            "{INDIVIDU_GENRE}" : self.genre,
            "{INDIVIDU_NOM}" : FormateStr(self.nom),
            "{INDIVIDU_PRENOM}" : FormateStr(self.prenom),
            "{INDIVIDU_DATE_NAISS}" : FormateDate(self.date_naiss),
            "{INDIVIDU_AGE}" : FormateStr(self.age),
            "{INDIVIDU_RUE}" : FormateStr(self.rue_resid),
            "{INDIVIDU_CP}" : FormateStr(self.cp),
            "{INDIVIDU_VILLE}" : FormateStr(self.ville_resid),
            "{INDIVIDU_PAYS}" : FormateStr(self.pays),
            "{INDIVIDU_NOMSECTEUR}" : FormateStr(self.pays),
            "{INDIVIDU_DPT}" : FormateStr(self.dpt),
            "{INDIVIDU_EMAILS}" : FormateStr(self.mails),
            "{INDIVIDU_TELEPHONES}" : FormateStr(self.telephones),
            "{CODEBARRES_ID_FAMILLE}" : "A%06d" % self.IDfamille,
            "{FAMILLE_NOM}": FormateStr(self.designation),
            "{FAMILLE_RUE}" : FormateStr(self.rue_resid),
            "{FAMILLE_CP}" : FormateStr(self.cp),
            "{FAMILLE_VILLE}" : FormateStr(self.ville_resid),
            "{FAMILLE_PAYS}" : FormateStr(self.pays),
            "nomImage" : self.nomImage,
            }

        # Questionnaires
        for dictQuestion in self.listview.LISTE_QUESTIONS :
            exec("dictTemp['{QUESTION_%d}'] = FormateStr(self.question_%d)" % (dictQuestion["IDquestion"], dictQuestion["IDquestion"]))
            if dictQuestion["controle"] == "codebarres" :
                exec("dictTemp['{CODEBARRES_QUESTION_%d}'] = FormateStr(self.question_%d)" % (dictQuestion["IDquestion"], dictQuestion["IDquestion"]))

        return dictTemp

def GetListeIndividus(listview, IDindividu=None, isoles = None, refusPub=False, actif=None):

    # Condition Individu donné
    if IDindividu != None :
        conditionIndividus = "WHERE individus.IDindividu=%d" % IDindividu
    elif actif:
        # benevoles actifs caractérisés par le tarif contenant le radical de Bénévolat et la participation à une activité
        conditionIndividus = "WHERE Left(activites.date_fin,4) >= '%s' AND  (categories_tarifs.nom Like '%%énévol%%')" % actif
    elif isoles :
        conditionIndividus = "WHERE ( rattachements.IDfamille IS NULL) "
    else:
        conditionIndividus = ""


    # Récupération des individus
    listeChamps = (
        "individus.IDindividu", "MIN(rattachements.IDfamille)", "individus.IDcivilite", "individus.nom", "individus.prenom", "individus.date_naiss",
        "individus.adresse_auto", "individus.rue_resid", "individus.cp_resid", "individus.ville_resid",
        "individus.travail_tel", "individus.travail_fax", "individus.travail_mail",
        "individus.tel_domicile", "individus.tel_mobile", "individus.tel_fax", "individus.mail",
        "individus_1.rue_resid","individus_1.cp_resid","individus_1.ville_resid",
        "individus.adresse_normee","individus.refus_pub",'individus.refus_mel'
    )
    listeChampsGroupBy = (
        "individus.IDindividu", "individus.IDcivilite", "individus.nom", "individus.prenom", "individus.date_naiss",
        "individus.adresse_auto", "individus.rue_resid", "individus.cp_resid", "individus.ville_resid",
        "individus.travail_tel", "individus.travail_fax", "individus.travail_mail",
        "individus.tel_domicile", "individus.tel_mobile", "individus.tel_fax", "individus.mail",
        "individus_1.rue_resid","individus_1.cp_resid","individus_1.ville_resid",
        "individus.adresse_normee", "individus.refus_pub", 'individus.refus_mel'
    )
    DB = GestionDB.DB()
    req = """
    SELECT %s
    FROM ((((individus 
            LEFT JOIN rattachements ON individus.IDindividu = rattachements.IDindividu) 
            LEFT JOIN individus AS individus_1 ON individus.adresse_auto = individus_1.IDindividu) 
            LEFT JOIN inscriptions ON individus.IDindividu = inscriptions.IDindividu) 
            LEFT JOIN activites ON inscriptions.IDactivite = activites.IDactivite) 
            LEFT JOIN categories_tarifs ON inscriptions.IDcategorie_tarif = categories_tarifs.IDcategorie_tarif
    %s
    GROUP BY %s
    ;""" % (",".join(listeChamps), conditionIndividus,",".join(listeChampsGroupBy))

    DB.ExecuterReq(req,MsgBox="OL_Etiquettes GetListeIndividus")
    listeDonnees = DB.ResultatReq()
    DB.Close()

    # Récupération des civilités
    dictCivilites = Civilites.GetDictCivilites()

    def compacte(adresse):
        compactee = ""
        if adresse:
            lst=adresse.split("\n")
            for ligne in lst:
                if len(ligne) > 0:
                    compactee += ligne + "\n"
            if len(compactee)>0:
                compactee = compactee[:-1]
        return compactee
    # Depackage les données
    listeListeView = []
    for valeurs in listeDonnees :
        dictTemp = {}
        dictTemp["IDindividu"] = valeurs[0]
        # Infos de la table Individus
        for index in range(0, len(listeChamps)) :
            nomChamp = listeChamps[index]
            if ("rue_resid" in nomChamp) or "ville_resid" in nomChamp:
                dictTemp[nomChamp] = compacte(valeurs[index])
            else:
                dictTemp[nomChamp] = valeurs[index]
        # Infos sur la civilité
        if dictTemp["individus.IDcivilite"] == None or dictTemp["individus.IDcivilite"] == "" :
            IDcivilite = 1
        else :
            IDcivilite = dictTemp["individus.IDcivilite"]
        dictTemp["genre"] = dictCivilites[IDcivilite]["sexe"]
        dictTemp["categorieCivilite"] = dictCivilites[IDcivilite]["categorie"]
        dictTemp["civiliteLong"]  = dictCivilites[IDcivilite]["civiliteLong"]
        dictTemp["civiliteAbrege"] = dictCivilites[IDcivilite]["civiliteAbrege"]
        dictTemp["nomImage"] = dictCivilites[IDcivilite]["nomImage"]

        if dictTemp["individus.date_naiss"] == None :
            dictTemp["age"] = None
        else:
            datenaissDD = datetime.date(year=int(dictTemp["individus.date_naiss"][:4]), month=int(dictTemp["individus.date_naiss"][5:7]), day=int(dictTemp["individus.date_naiss"][8:10]))
            datedujour = datetime.date.today()
            age = (datedujour.year - datenaissDD.year) - int((datedujour.month, datedujour.day) < (datenaissDD.month, datenaissDD.day))
            dictTemp["age"] = age

        # Formatage sous forme de TRACK
        track = TrackIndividu(listview, dictTemp, refusPub)
        if track.valide:
            listeListeView.append(track)
    return listeListeView


#-----------FAMILLES-----------

class TrackFamille(object):
    def __init__(self, listview, donnees, refusPub):
        self.cp = donnees["adresse"]["cp"]
        if not self.cp: self.cp = ""
        self.refus_pub = donnees["refus_pub"]
        self.refus_mel = donnees["refus_mel"]
        self.valide = True
        if refusPub:
            if len(self.cp) == 0:
                self.valide = False
            elif self.cp[:2] in ('0 ','00','  '): self.valide = False
            elif len(self.cp) == 1 and self.cp[:1] in ('0',' '): self.valide = False
            elif self.refus_pub: self.valide = False

        self.listview = listview
        self.IDfamille = donnees["IDfamille"]
        self.IDcivilite = donnees["IDcivilite"]
        self.nomTitulaires = donnees["titulaires"]
        self.designation = donnees["designation_famille"]
        self.nom = donnees["nom"]
        # gestion des sauts de lignes dans la rue
        lstville = donnees["adresse"]["ville"].split("\n")
        if len(lstville) > 0:
            ville = lstville[0]
        else:
            ville = ""
        if len(lstville) > 1:
            pays = lstville[1]
        else: pays = ""
        if donnees["adresse"]["rue"] == None: donnees["adresse"]["rue"]=""
        lstRue = donnees["adresse"]["rue"].split("\n")
        if len(lstRue)<4:
            for i in range(len(lstRue),4):
                lstRue.append("")
        self.rue1 = lstRue[0]
        self.rue2 = lstRue[1]
        self.rue3 = lstRue[2]
        self.rue4 = lstRue[3]
        self.prenom = donnees["prenom"]
        self.rue_resid = donnees["adresse"]["rue"]
        self.ville_resid = ville
        self.ville = ville
        self.pays = pays
        self.dpt = ''
        if self.cp != None :
            if len(self.cp) > 1 and ((not self.pays) or len(self.pays)==0):
                self.dpt = str(self.cp)[:2]

        # Ajout des adresses Emails des titulaires
        self.mail = donnees["mail_famille"]
        self.mails = donnees["mails"]
        # Ajout des téléphones des titulaires
        self.telephones = donnees["telephones"]
        self.telephone = donnees["telephone_famille"]

        # Récupération des réponses des questionnaires
        for dictQuestion in self.listview.LISTE_QUESTIONS :
            exec("self.question_%d = self.listview.GetReponse(%d, %s)" % (dictQuestion["IDquestion"], dictQuestion["IDquestion"], self.IDfamille))

        # Récupération des appartenances aux listes de diffusion
        # un individu titulaire emporte la famille
        for IDdiffusion in list(self.listview.dictDiffusions.keys()) :
            exec("self.diffusion_%d = None" % (IDdiffusion))
            for IDindividu in donnees["IDtitulaires"]:
                if (IDindividu,) in self.listview.dictDiffusions[IDdiffusion]["tplIDs"] :
                    exec("self.diffusion_%d = 'x'" % (IDdiffusion))

    def GetDict(self):
        dictTemp = {
            "{IDFAMILLE}" : str(self.IDfamille),
            "{CODEBARRES_ID_FAMILLE}" : "A%06d" % self.IDfamille,
            "{FAMILLE_TITULAIRES}" : FormateStr(self.nomTitulaires),
            "{FAMILLE_NOM}": FormateStr(self.designation),
            "{INDIVIDU_NOM}" : FormateStr(self.nom),
            "{INDIVIDU_PRENOM}" : FormateStr(self.prenom),
            "{FAMILLE_RUE}" : FormateStr(self.rue_resid),
            "{FAMILLE_CP}" : FormateStr(self.cp),
            "{FAMILLE_VILLE}" : FormateStr(self.ville_resid),
            "{FAMILLE_PAYS}" : FormateStr(self.pays),
            }

        # Questionnaires
        for dictQuestion in self.listview.LISTE_QUESTIONS :
            exec("dictTemp['{QUESTION_%d}'] = FormateStr(self.question_%d)" % (dictQuestion["IDquestion"], dictQuestion["IDquestion"]))
            if dictQuestion["controle"] == "codebarres" :
                exec("dictTemp['{CODEBARRES_QUESTION_%d}'] = FormateStr(self.question_%d)" % (dictQuestion["IDquestion"], dictQuestion["IDquestion"]))

        return dictTemp

def GetListeFamilles(listview=None, IDfamille=None, refusPub=False, actif=None):
    # Condition Famille donnée
    if IDfamille != None :
        conditionFamilles = "WHERE rattachements.IDfamille=%d" % IDfamille
    elif actif:
        conditionFamilles = "WHERE Left(date_fin,4) >= '%s'"%actif
    else:
        conditionFamilles = ""

    # Récup de la liste de toutes les familles possibles
    DB = GestionDB.DB()
    req = """
            SELECT rattachements.IDfamille
            FROM rattachements 
            LEFT JOIN ( inscriptions 
                        LEFT JOIN activites ON inscriptions.IDactivite = activites.IDactivite)  
                    ON (rattachements.IDindividu = inscriptions.IDindividu) 
                        AND (rattachements.IDfamille = inscriptions.IDfamille)
            %s
            GROUP BY rattachements.IDfamille
            ORDER BY rattachements.IDfamille;
        ;""" % ( conditionFamilles)

    DB.ExecuterReq(req,MsgBox="ExecuterReq")
    recordset = DB.ResultatReq()
    DB.Close()
    listeFamilles = []
    for record in recordset:
        if record[0] not in listeFamilles:
            listeFamilles.append(record[0])

    # Formatage des données
    listeListeView = []
    titulaires = UTILS_Titulaires.GetFamillesEtiq(listeFamilles)
    """
    # version ancienne remaniée
    for IDfamille, dictFamille in titulaires.items() :
        if IDfamille in listeFamilles:
            # pour détecter ensuiteles familles sans titulaires
            listeFamilles.remove(IDfamille)
        ID = IDfamille
        IDcivilite = ""
        nom = ""
        prenom = ""
        designation = ""
        rue_resid = ""
        cp = ""
        ville = ""
        ville_resid = ""
        pays = ""
        mails = ""
        telephones = ""
        listeMembres = []
        nomTitulaires = ""
        refus_pub = 0
        refus_mel = 0
        if "titulaires" in dictFamille and not "nom" in dictFamille:
            nomTitulaires = _(u"Un titulaire de la famille %d est aussi titulaire par ailleurs"%(IDfamille))

        elif IDfamille != None  and "nom" in dictFamille:
            IDcivilite = str(dictFamille["IDcivilite"])
            nomTitulaires = dictFamille["titulairesSansCivilite"]
            nom = dictFamille["nom"]
            prenom = dictFamille["prenom"]
            designation = dictFamille["designation_famille"]
            rue_resid = dictFamille["adresse"]["rue"]
            cp = dictFamille["adresse"]["cp"]
            ville_resid = dictFamille["adresse"]["ville"]
            lstville = dictFamille["adresse"]["ville"].split(u"\n")
            if len(lstville)>0 : ville = lstville[0]
            else: ville = ""
            if len(lstville)>1:
                pays = lstville[1]
            else: pays = ""
            if not "mails" in dictFamille.keys():
                if "mail" in dictFamille.keys():
                    dictFamille["mails"] = dictFamille["mail"]
                else: dictFamille["mails"] = ""
            if not "telephones" in dictFamille.keys():
                if "telephone" in dictFamille.keys():
                    dictFamille["telephones"] = dictFamille["telephone"]
                else: dictFamille["telephones"] = ""
            telephones = dictFamille["telephones"]
            listeMembres = dictFamille["IDtitulaires"]
            ID = dictFamille["IDfamille"]
            refus_pub = dictFamille["refus_pub"]
            refus_mel = dictFamille["refus_mel"]
        else: wx.MessageBox("A voir la famille %d"%IDfamille)
        dictTemp = {
            "IDcivilite":IDcivilite,"IDfamille":ID, "titulaires":nomTitulaires,"nom":nom, "prenom":prenom,"designation":designation,
            "rue_resid":rue_resid, "cp" : cp, "ville_resid":ville_resid, "ville":ville, "pays":pays, "mails" : mails,"telephones" : telephones,
            "listeMembres" : listeMembres,"refus_pub":refus_pub,"refus_mel": refus_mel
            }        
        # Formatage sous forme de TRACK
        track = TrackFamille(listview, dictTemp, refusPub)
    """    
    for IDfamille, dictFamille in titulaires.items() :
        # Formatage sous forme de TRACK

        track = TrackFamille(listview, dictFamille, refusPub)
        if track.valide:
            listeListeView.append(track)


    return listeListeView

#-----------LISTVIEW-----------

class ListView(FastObjectListView):
    def __init__(self, *args, **kwds):
        # Récupération des paramètres perso
        self.categorie = kwds.pop("categorie", "individus")
        self.IDindividu = kwds.pop("IDindividu", None)
        self.IDfamille = kwds.pop("IDfamille", None)
        self.questions = False
        self.diffusions = False
        self.refusPub = False
        # Infos organisme
        self.dictOrganisme = GetInfosOrganisme()
        self.UtilsQuestionnaires = UTILS_Questionnaires.Questionnaires()
        self.LISTE_QUESTIONS = []
        self.LISTE_QUESTIONNAIRES = []
        # Initialisation du listCtrl
        FastObjectListView.__init__(self, *args, **kwds)
        # Binds perso
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OuvrirFicheFamille)
        self.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)

    def InitModel(self):
        self.LISTE_QUESTIONS = []
        self.LISTE_QUESTIONNAIRES = []
        self.dictDiffusions = {}
        if self.categorie != None :
            if self.questions:
                # Récupération des questions
                self.LISTE_QUESTIONS = self.UtilsQuestionnaires.GetQuestions(type=self.categorie)
                # Récupération des questionnaires
                self.DICT_QUESTIONNAIRES = self.UtilsQuestionnaires.GetReponses(type=self.categorie)
            if self.diffusions:
                # Récupération des listes de diffusion
                ddf = DictDiffusion()
                self.dictDiffusions = ddf.dictDiffusions

        # Récupération des tracks
        if self.categorie in ("individu","individus","benevole_actif" ):
            self.donnees = GetListeIndividus(self, self.IDindividu, refusPub=self.refusPub, actif=self.actif)
        elif self.categorie in ("famille","familles", "famille_actif"):
            self.donnees = GetListeFamilles(self, self.IDfamille, refusPub=self.refusPub,  actif = self.actif)
        elif self.categorie == "isole":
            if (not hasattr(self,"donnees")):
                self.donnees = []
            if len(self.donnees) == 0:
                wx.MessageBox("Vous avez choisi d'ajouter les 'individus sans famille' à une liste vide\n" +
                              "Si vous lancez une autre liste, elle ne s'ajoutera pas à celle-ci!\n"+
                              "Vous pouviez lancer 'Familles' avant, pour y ajouter ensuite les 'sans famille'")
            self.donnees += GetListeIndividus(self, refusPub=self.refusPub, isoles = True)
        else: self.donnees = []

    def InitObjectListView(self):
        # Création du imageList
        for categorie, civilites in Civilites.LISTE_CIVILITES :
            for IDcivilite, CiviliteLong, CiviliteAbrege, nomImage, genre in civilites :
                indexImg = self.AddNamedImages(nomImage, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/%s") % nomImage, wx.BITMAP_TYPE_PNG))
        
        def GetImageCivilite(track):
            return track.nomImage

        def FormateDate(dateStr):
            if dateStr == "" or dateStr == None : return ""
            date = str(datetime.date(year=int(dateStr[:4]), month=int(dateStr[5:7]), day=int(dateStr[8:10])))
            text = str(date[8:10]) + "/" + str(date[5:7]) + "/" + str(date[:4])
            return text
        
        def FormateAge(age):
            if age == None : return ""
            return _("%d ans") % age
        
        # Couleur en alternance des lignes
        self.oddRowsBackColor = "#F0FBED" 
        self.evenRowsBackColor = wx.Colour(255, 255, 255)
        self.useExpansionColumn = True

        # Définition des colonnes
        if self.categorie in ["individu","benevole_actif"] :
            # INDIVIDUS
            liste_Colonnes = [
                ColumnDefn(_("Civilité"), "left", 20, "IDcivilite", typeDonnee="texte"),
                ColumnDefn(_("IDfamille"), "left", 50, "IDfamille", typeDonnee="entier"),
                ColumnDefn(_("Désignation"), 'left', 100, "designation", typeDonnee="texte"),
                ColumnDefn(_("Rue1"), "left", 120, "rue1", typeDonnee="texte"),
                ColumnDefn(_("Rue2"), "left", 120, "rue2", typeDonnee="texte"),
                ColumnDefn(_("Rue3"), "left", 80, "rue3", typeDonnee="texte"),
                ColumnDefn(_("Rue4"), "left", 60, "rue4", typeDonnee="texte"),
                ColumnDefn(_("C.P."), "left", 50, "cp", typeDonnee="texte"),
                ColumnDefn(_("Ville"), "left", 120, "ville", typeDonnee="texte"),
                ColumnDefn(_("Pays"), "left", 80, "pays", typeDonnee="texte"),
                ColumnDefn(_("dpt"), "left", 30, "dpt", typeDonnee="texte"),
                ColumnDefn(_("Emails"), "left", 100, "mails", typeDonnee="texte"),
                ColumnDefn(_("Teléphones"), "left", 100, "telephones", typeDonnee="texte"),
                ColumnDefn(_("koPub"), "left", 50, "refus_pub", typeDonnee="entier"),
                ColumnDefn(_("koMel"), "left", 50, "refus_mel", typeDonnee="entier"),
                ColumnDefn(_("Civilité"), 'left', 50, "civiliteAbrege", typeDonnee="texte"),
                ColumnDefn(_("Nom"), 'left', 100, "nom", typeDonnee="texte"),
                ColumnDefn(_("Prénom"), "left", 80, "prenom", typeDonnee="texte"),
                ColumnDefn("IDind", "left", 60, "IDindividu", typeDonnee="entier", imageGetter=GetImageCivilite),
                ColumnDefn(_("Date naiss."), "left", 72, "date_naiss", typeDonnee="date", stringConverter=FormateDate),
                ColumnDefn(_("Age"), "left", 50, "age", typeDonnee="entier", stringConverter=FormateAge),
                ]
            # Ajout des listes de diffusion
            for IDdiffusion in self.dictDiffusions :
                nom = self.dictDiffusions[IDdiffusion]["nom"]
                liste_Colonnes.append(ColumnDefn( nom, "left", 100, "diffusion_%d" % IDdiffusion, typeDonnee="texte"))

        else:
            # FAMILLES ou isole
            liste_Colonnes = [
                ColumnDefn(_("Civilités"), "left", 40, "IDcivilite", typeDonnee="texte"),
                ColumnDefn(_("Famille"), "left", 40, "IDfamille", typeDonnee="entier"),
                ColumnDefn(_("Désignation"), "left", 200, "designation", typeDonnee="texte"),
                ColumnDefn(_("Rue1"), "left", 120, "rue1", typeDonnee="texte"),
                ColumnDefn(_("Rue2"), "left", 120, "rue2", typeDonnee="texte"),
                ColumnDefn(_("Rue3"), "left", 80, "rue3", typeDonnee="texte"),
                ColumnDefn(_("Rue4"), "left", 80, "rue4", typeDonnee="texte"),
                ColumnDefn(_("C.P."), "left", 50, "cp", typeDonnee="texte"),
                ColumnDefn(_("Ville"), "left", 120, "ville", typeDonnee="texte"),
                ColumnDefn(_("Pays"), "left", 80, "pays", typeDonnee="texte"),
                ColumnDefn(_("dpt"), "left", 30, "dpt", typeDonnee="texte"),
                ColumnDefn(_("Email"), "left", 100, "mail", typeDonnee="texte"),
                ColumnDefn(_("Teléphones"), "left", 100, "telephones", typeDonnee="texte"),
                ColumnDefn(_("koPub"), "left", 50, "refus_pub", typeDonnee="entier"),
                ColumnDefn(_("koMel"), "left", 50, "refus_mel", typeDonnee="entier"),
            ]
            # Ajout des listes de diffusion
            for IDdiffusion in self.dictDiffusions :
                nom = self.dictDiffusions[IDdiffusion]["nom"]
                liste_Colonnes.append(ColumnDefn( nom, "left", 100, "diffusion_%d" % IDdiffusion, typeDonnee="texte"))

        # Ajout des questions des questionnaires
        for dictQuestion in self.LISTE_QUESTIONS :
            #nomChamp = "question_%d" % dictQuestion["IDquestion"]
            filtre = dictQuestion["filtre"]
            if filtre == "texte" : typeDonnee = "texte"
            elif filtre == "entier" : typeDonnee = "entier"
            elif filtre == "montant" : typeDonnee = "montant"
            elif filtre == "choix" : typeDonnee = "texte"
            elif filtre == "coche" : typeDonnee = "texte"
            elif filtre == "date" : typeDonnee = "date"
            else : typeDonnee = "texte"
            liste_Colonnes.append(ColumnDefn(dictQuestion["label"], "left", 150, "question_%d" % dictQuestion["IDquestion"], typeDonnee=typeDonnee))

        self.SetColumns(liste_Colonnes)
        self.CreateCheckStateColumn(0)

        def rowFormatter(listItem, track):
            nopub = (track.refus_pub or not track.cp or (track.cp+"00")[:2]=="00")
            nomel = track.refus_mel == True
            if nopub:
                listItem.SetTextColour(wx.Colour(200, 0,100))
            elif nomel:
                listItem.SetTextColour(wx.Colour(100,0,200))

        if self.categorie == "individu" :
            self.SetEmptyListMsg(_("Aucun individu"))
        else:
            self.SetEmptyListMsg(_("Aucune famille"))
        self.SetEmptyListMsgFont(wx.FFont(11, wx.DEFAULT, faceName="Tekton"))
        self.SetSortColumn(self.columns[3])
        self.SetObjects(self.donnees)
        self.rowFormatter = rowFormatter
        nbcoches = 0
        nblignes = len(self.GetObjects())
        try:
            dlg = self.GrandParent.parent
            dlg.box_donnees_staticbox.SetLabel("Lignes %ss : (%d), cochées %d" % (self.categorie,nblignes,nbcoches))
        except : pass

    def MAJ(self, categorie=None, questions=False, diffusions=False, refusPub=False, actif=None):
        self.questions = questions
        self.diffusions = diffusions
        self.refusPub = refusPub
        self.actif = actif
        if categorie != None :
            self.categorie = categorie
        self.InitModel()
        self.InitObjectListView()

    def GetReponse(self, IDquestion=None, ID=None):
        if IDquestion in self.DICT_QUESTIONNAIRES :
            if ID in self.DICT_QUESTIONNAIRES[IDquestion] :
                return self.DICT_QUESTIONNAIRES[IDquestion][ID]
        return ""

    def Selection(self):
        return self.GetSelectedObjects()
    
    def GetTracksCoches(self):
        return self.GetCheckedObjects()

    def GetInfosCoches(self):
        listeDonnees = []
        for track in self.GetTracksCoches() :
            dictTemp = track.GetDict()
            for code, valeur in self.dictOrganisme.items() :
                dictTemp[code] = valeur
            listeDonnees.append(dictTemp)
        return listeDonnees

    def SetIDcoches(self, listeID=[]):
        for track in self.donnees :
            if self.categorie in ("individu","isole","benevole_actif") :
                ID = track.IDindividu
            else :
                ID = track.IDfamille
            if ID in listeID :
                self.Check(track)
                self.RefreshObject(track)
    
    def OnCheck(self, track=None):
        try :
            self.GetParent().OnCheck(track)
        except :
            pass

    def OnContextMenu(self, event):
        """Ouverture du menu contextuel """            
        # Création du menu contextuel
        menuPop = wx.Menu()

        # Item Ouverture fiche famille
        item = wx.MenuItem(menuPop, 10, _("Ouvrir la fiche famille"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Famille.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.OuvrirFicheFamille, id=10)

        # Tout sélectionner
        item = wx.MenuItem(menuPop, 20, _("Tout cocher"))
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.CocheListeTout, id=20)

        # Tout dé-sélectionner
        item = wx.MenuItem(menuPop, 21, _("Tout décocher"))
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.CocheListeRien, id=21)

        # Inverser coches jusqua
        item = wx.MenuItem(menuPop, 22, _("Inverser jusqu'à Selection"))
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.CocheJusqua, id=22)

        menuPop.AppendSeparator()
        
        # Apercu avant impression
        item = wx.MenuItem(menuPop, 40, _("Aperçu étiquettes"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Apercu.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.Apercu, id=40)


        # Imprimer
        item = wx.MenuItem(menuPop, 50, _("Imprimer la liste"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Imprimante.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.Impression, id=50)
        
        menuPop.AppendSeparator()
    
        # Export Texte
        item = wx.MenuItem(menuPop, 600, _("Exporter au format Texte"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Texte2.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.ExportTexte, id=600)
        
        # Export Excel
        item = wx.MenuItem(menuPop, 700, _("Exporter au format Excel"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Excel.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.ExportExcel, id=700)

        self.PopupMenu(menuPop)
        menuPop.Destroy()

    def OuvrirFicheFamille(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("familles_fiche", "consulter") == False: return
        if len(self.Selection()) == 0:
            dlg = wx.MessageDialog(self, _("Vous n'avez sélectionné aucune fiche famille à ouvrir !"),
                                   _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        IDfamille = self.Selection()[0].IDfamille
        if (not IDfamille) or IDfamille == 0:
            dlg = wx.MessageDialog(self, _("Il n'y a pas de famille associée !"),
                                   _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        from Dlg import DLG_Famille
        dlg = DLG_Famille.Dialog(self, IDfamille)
        dlg.ShowModal()
        dlg.Destroy()

    def Impression(self, mode="preview"):
        if self.donnees == None or len(self.donnees) == 0 :
            dlg = wx.MessageDialog(self, _("Il n'y a aucune donnée à imprimer !"), _("Erreur"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        from Utils import UTILS_Printer
        prt = UTILS_Printer.ObjectListViewPrinter(self, titre=_("Liste des %ss") % self.categorie, intro="", total="", format="A", orientation=wx.LANDSCAPE)
        if mode == "preview" :
            prt.Preview()
        else:
            prt.Print()
        
    def Apercu(self, event):
        parent = self.GetGrandParent()
        parent.parent.OnBoutonOk(event)
        #self.Impression("preview")

    def ExportTexte(self, event):
        from Utils import UTILS_Export
        UTILS_Export.ExportTexte(self, titre=_("Liste des %s") % self.categorie)
        
    def ExportExcel(self, event):
        from Utils import UTILS_Export
        UTILS_Export.ExportExcel(self, titre=_("Liste des %s") % self.categorie, onlyCheck = True)

# -------------------------------------------------------------------------------------------------------------------------------------

class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args)
        panel = wx.Panel(self, -1, name="test1")
        panel.parent = self
        IDfamille = kwds.pop("IDfamille", None)
        IDindividu = kwds.pop("IDindividu", None)
        self.parent = self
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_1.Add(panel, 1, wx.ALL|wx.EXPAND)
        self.SetSizer(sizer_1)
        self.myOlv = ListView(panel, id=-1, name="OL_test",
                              IDfamille= IDfamille,
                              IDindividu= IDindividu,
                              style=wx.LC_REPORT|wx.SUNKEN_BORDER|wx.LC_SINGLE_SEL|wx.LC_HRULES|wx.LC_VRULES)
        self.myOlv.MAJ(categorie="individu")
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_2.Add(self.myOlv, 1, wx.ALL|wx.EXPAND, 4)
        panel.SetSizer(sizer_2)
        self.Layout()

if __name__ == '__main__':
    app = wx.App(0)
    #wx.InitAllImageHandlers()
    print("lance Myframe")
    frame_1 = MyFrame(None, -1, "OL TEST",IDindividu = 9)
    app.SetTopWindow(frame_1)
    print("lance Show")
    frame_1.Show()
    print("lance MainLoop")
    app.MainLoop()

