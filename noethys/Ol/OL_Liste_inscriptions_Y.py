#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, Matthania, modif des colonnes et de l'affichage des activités et gestion des catégories supprimées
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS, JB
# Copyright:       (c) 2010-11 Ivan LUCAS, JB
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------


import Chemins
from Utils.UTILS_Traduction import _
import wx
import FonctionsPerso
import GestionDB
import datetime
import decimal
from Utils import UTILS_Utilisateurs
from Data import DATA_Civilites as Civilites
DICT_CIVILITES = Civilites.GetDictCivilites()

from Utils import UTILS_Config
SYMBOLE = UTILS_Config.GetParametre("monnaie_symbole", "€")

DICT_INFOS_INDIVIDUS = {}

from Ctrl.CTRL_ObjectListView import GroupListView, ColumnDefn, Filter, CTRL_Outils, PanelAvecFooter

LISTE_CHAMPS1 = [
    {"label":_("Nom complet"), "code":"nomComplet", "champ":None, "typeDonnee":"texte", "align":"left", "largeur":160, "stringConverter":None, "imageGetter":"civilite", "actif":True, "afficher":True},
    {"label":_("IDindividu"), "code":"IDindividu", "champ":"inscriptions.IDindividu", "typeDonnee":"entier", "align":"left", "largeur":30, "stringConverter":None, "actif":True, "afficher":True},
    {"label":_("IDinscription"), "code":"IDinscription", "champ":"inscriptions.IDinscription", "typeDonnee":"entier", "align":"left", "largeur":0, "stringConverter":None, "actif":False, "afficher":False},
    {"label":_("Age"), "code":"age", "champ":None, "typeDonnee":"entier", "align":"left", "largeur":55, "stringConverter":"age", "actif":True, "afficher":True},

    {"label":_("Groupe"), "code":"nomGroupe", "champ":"groupes.nom", "typeDonnee":"texte", "align":"left", "largeur":90, "stringConverter":None, "actif":True, "afficher":True},
    {"label":_("Tarif"), "code":"nomCategorie", "champ":"categories_tarifs.nom", "typeDonnee":"texte", "align":"left", "largeur":75, "stringConverter":None, "actif":True, "afficher":True},
    {"label":_("Date inscrip."), "code":"dateInscription", "champ":"inscriptions.date_inscription", "typeDonnee":"date", "align":"left", "largeur":75, "stringConverter":"date", "actif":True, "afficher":False},

    {"label":_("Arrivée"), "code":"dateArrivee", "champ":"MIN(consommations.date)", "typeDonnee":"date", "align":"left", "largeur":75, "stringConverter":"date", "actif":True, "afficher":True},
    {"label":_("Départ"), "code":"dateDepart", "champ":"MAX(consommations.date)", "typeDonnee":"date", "align":"left", "largeur":75, "stringConverter":"date", "actif":True, "afficher":True},

    {"label":_("Piece"), "code":"nature", "champ":None, "typeDonnee":"texte", "align":"left", "largeur":40, "stringConverter":None, "actif":True, "afficher":True},
    {"label":_("Facturé"), "code":"totalFacture", "champ":None, "typeDonnee":"montant", "align":"right", "largeur":65, "stringConverter":"montant", "actif":True, "afficher":False},
    {"label":_("Réglé"), "code":"totalRegle", "champ":None, "typeDonnee":"montant", "align":"right", "largeur":65, "stringConverter":"montant", "actif":True, "afficher":True},
    {"label":_("Solde"), "code":"totalSolde", "champ":None, "typeDonnee":"montant", "align":"right", "largeur":85, "stringConverter":"solde", "imageGetter":"ventilation", "actif":True, "afficher":True},

    {"label":_("IDcivilite"), "code":"IDcivilite", "champ":"individus.IDcivilite", "typeDonnee":"entier", "align":"left", "largeur":65, "stringConverter":None, "actif":False, "afficher":False},
    {"label":_("Nom"), "code":"nomIndividu", "champ":"individus.nom", "typeDonnee":"texte", "align":"left", "largeur":65, "stringConverter":None, "actif":True, "afficher":False},
    {"label":_("Prénom"), "code":"prenomIndividu", "champ":"individus.prenom", "typeDonnee":"texte", "align":"left", "largeur":65, "stringConverter":None, "actif":True, "afficher":False},

    {"label":_("Rue de l'inscrit"), "code":"rue_resid", "champ":"individus.rue_resid", "typeDonnee":"texte", "align":"left", "largeur":95, "stringConverter":None, "actif":True, "afficher":False},
    {"label":_("CP de l'inscrit"), "code":"cp_resid", "champ":"individus.cp_resid", "typeDonnee":"texte", "align":"left", "largeur":45, "stringConverter":None, "actif":True, "afficher":False},
    {"label":_("Ville de l'inscrit"), "code":"ville_resid", "champ":"individus.ville_resid", "typeDonnee":"texte", "align":"left", "largeur":110, "stringConverter":None, "actif":True, "afficher":False},

    {"label":_("Num. Sécu."), "code":"num_secu", "champ":"individus.num_secu", "typeDonnee":"texte", "align":"left", "largeur":90, "stringConverter":None, "actif":True, "afficher":False},
    {"label":_("Date naiss."), "code":"date_naiss", "champ":"individus.date_naiss", "typeDonnee":"date", "align":"left", "largeur":75, "stringConverter":"date", "actif":True, "afficher":True},
    {"label":_("CP naiss."), "code":"cp_naiss", "champ":"individus.cp_naiss", "typeDonnee":"texte", "align":"left", "largeur":45, "stringConverter":None, "actif":True, "afficher":False},
    {"label":_("Ville naiss."), "code":"ville_naiss", "champ":"individus.ville_naiss", "typeDonnee":"texte", "align":"left", "largeur":85, "stringConverter":None, "actif":False, "afficher":True},
    {"label":_("adresse_auto"), "code":"adresse_auto", "champ":"individus.adresse_auto", "typeDonnee":"texte", "align":"left", "largeur":75, "stringConverter":None, "actif":False, "afficher":False},

    {"label":_("Tél dom."), "code":"tel_domicile", "champ":"individus.tel_domicile", "typeDonnee":"texte", "align":"left", "largeur":75, "stringConverter":None, "actif":True, "afficher":False},
    {"label":_("Tél mobile"), "code":"tel_mobile", "champ":"individus.tel_mobile", "typeDonnee":"texte", "align":"left", "largeur":75, "stringConverter":None, "actif":True, "afficher":False},
    {"label":_("Email"), "code":"mail", "champ":"individus.mail", "typeDonnee":"texte", "align":"left", "largeur":75, "stringConverter":None, "actif":True, "afficher":False},

    {"label":_("Genre"), "code":"genre", "champ":None, "typeDonnee":"texte", "align":"left", "largeur":45, "stringConverter":None, "actif":True, "afficher":False},
    {"label":_("Civilité long"), "code":"civiliteAbrege", "champ":None, "typeDonnee":"texte", "align":"left", "largeur":75, "stringConverter":None, "actif":True, "afficher":False},
    {"label":_("nomImage"), "code":"nomImage", "champ":None, "typeDonnee":"texte", "align":"left", "largeur":45, "stringConverter":None, "actif":False, "afficher":False},

    {"label":_("IDfamille"), "code":"IDfamille", "champ":"inscriptions.IDfamille", "typeDonnee":"entier", "align":"left", "largeur":45, "stringConverter":None, "actif":False, "afficher":True},
    ]

LISTE_CHAMPS_2 = [
    {"label":_("Corresp_Désignation"), "code":"C_designation", "champ":None, "typeDonnee":"texte", "align":"left", "largeur":135, "stringConverter":None, "actif":True, "afficher":True},
    {"label":_("Corresp_Rue"), "code":"C_rue_resid", "champ":None, "typeDonnee":"texte", "align":"left", "largeur":125, "stringConverter":None, "actif":True, "afficher":True},
    {"label":_("Corresp_CP"), "code":"C_cp_resid", "champ":None, "typeDonnee":"texte", "align":"left", "largeur":45, "stringConverter":None, "actif":True, "afficher":True},
    {"label":_("Corresp_Ville"), "code":"C_ville_resid", "champ":None, "typeDonnee":"texte", "align":"left", "largeur":110, "stringConverter":None, "actif":True, "afficher":True},
    {"label":_("Repres_Professions"), "code":"R_professions", "champ":None, "typeDonnee":"texte", "align":"left", "largeur":75, "stringConverter":None, "actif":True, "afficher":False},
    {"label":_("Repres_Téléphones"), "code":"R_telephones", "champ":None, "typeDonnee":"texte", "align":"left", "largeur":200, "stringConverter":None, "actif":True, "afficher":True},
    {"label":_("Repres_Mails"), "code":"R_mails", "champ":None, "typeDonnee":"texte", "align":"left", "largeur":200, "stringConverter":None, "actif":True, "afficher":True},
    ]

LISTE_CHAMPS = LISTE_CHAMPS1 + LISTE_CHAMPS_2

def DateEngFr(textDate):
    if textDate == None: return ""
    textDate = str(textDate)
    text = str(textDate[8:10]) + "/" + str(textDate[5:7]) + "/" + str(textDate[:4])
    return text

def DateComplete(dateDD):
    """ Transforme une date DD en date complète : Ex : lundi 15 janvier 2008 """
    listeJours = (_("Lundi"), _("Mardi"), _("Mercredi"), _("Jeudi"), _("Vendredi"), _("Samedi"), _("Dimanche"))
    listeMois = (_("janvier"), _("février"), _("mars"), _("avril"), _("mai"), _("juin"), _("juillet"), _("août"), _("septembre"), _("octobre"), _("novembre"), _("décembre"))
    dateComplete = listeJours[dateDD.weekday()] + " " + str(dateDD.day) + " " + listeMois[dateDD.month-1] + " " + str(dateDD.year)
    return dateComplete

def DateEngEnDateDD(dateEng):
    if dateEng and not isinstance(dateEng,str): dateEng = str(dateEng)
    return datetime.date(int(dateEng[:4]), int(dateEng[5:7]), int(dateEng[8:10]))

def GetDictInfosIndividus():
    global DICT_INFOS_INDIVIDUS
    dictInfos = {}
    db = GestionDB.DB()
    req = """SELECT IDindividu, adresse_auto, rue_resid, cp_resid, ville_resid, profession, travail_tel, travail_fax,
                    travail_mail, tel_domicile, tel_mobile, tel_fax, mail
            FROM individus;"""
    db.ExecuterReq(req)
    listeDonnees = db.ResultatReq()
    db.Close()
    for IDindividu,auto,rue,cp,ville,profession,tel1,tel2,mail1,tel3,tel4,tel5,mail2 in listeDonnees :
        if not profession: profession = ""
        dictInfos[IDindividu] = { "adresse_auto" : auto, "rue_resid" : rue, "cp_resid" : cp, "ville_resid" : ville,
                                  "profession":profession,"telephones":"","mails":""}
        for champ in (tel1,tel2,tel3,tel4,tel5):
            if champ and len(champ)>0 : dictInfos[IDindividu]["telephones"] += champ+","
        for champ in (mail1,mail2):
            if champ and len(champ) > 0: dictInfos[IDindividu]["mails"] += champ + ","
    DICT_INFOS_INDIVIDUS = dictInfos

# ---------------------------------------- LISTVIEW  -----------------------------------------------------------------------

class Track(object):
    def __init__(self, donnees):
        for dictChamp in LISTE_CHAMPS :
            setattr(self, dictChamp["code"], donnees[dictChamp["code"]])

class ListView(GroupListView):
    def __init__(self, *args, **kwds):
        GroupListView.__init__(self, *args, **kwds)
        self.selectionID = None
        self.selectionTrack = None
        self.IDactivite = None
        self.toutesAnnees = True
        self.listeGroupes = []
        self.listeCategories = []
        self.regroupement = None
        self.lstChampsAffiches = []
        self.labelParametres = ""
        # Binds perso
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnActivated)
        self.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)
                
    def OnActivated(self,event):
        pass

    def InitModel(self):
        self.donnees = self.GetTracks()

    def GetTracks(self):
        listeListeView = []
        if self.IDactivite == None :
            return listeListeView

        DB = GestionDB.DB()

        # Condition Groupes
        if len(self.listeGroupes) == 0 : conditionGroupes = "()"
        elif len(self.listeGroupes) == 1 : conditionGroupes = "(%d)" % self.listeGroupes[0]
        else : conditionGroupes = str(tuple(self.listeGroupes))

        # Condition Catégories
        if len(self.listeCategories) == 0 : conditionCategories = " "
        elif len(self.listeCategories) == 1 : conditionCategories = "AND inscriptions.IDcategorie_tarif in (%d)" % self.listeCategories[0]
        else : conditionCategories = "AND inscriptions.IDcategorie_tarif IN " + str(tuple(self.listeCategories))

        # Infos sur tous les individus
        GetDictInfosIndividus()
        
        # Récupération de la facturation
        dictFacturation = {}

        # Récupère les prestations
        req = """SELECT IDfamille, IDindividu, SUM(montant)
        FROM prestations
        WHERE IDactivite=%d
        GROUP BY IDfamille, IDindividu
        ;""" % self.IDactivite
        DB.ExecuterReq(req)
        listePrestations = DB.ResultatReq()
        for IDfamille, IDindividu, total_prestations in listePrestations :
            dictFacturation[(IDfamille, IDindividu)] = {"prestations":total_prestations, "ventilation":0.0}

        # Récupère la ventilation
        req = """SELECT IDfamille, IDindividu, SUM(ventilation.montant)
        FROM ventilation
        LEFT JOIN prestations ON prestations.IDprestation = ventilation.IDprestation
        WHERE prestations.IDactivite=%d
        GROUP BY IDfamille, IDindividu
        ;""" % self.IDactivite
        DB.ExecuterReq(req)
        listeVentilations = DB.ResultatReq()
        for IDfamille, IDindividu, total_ventilation in listeVentilations :
            dictFacturation[(IDfamille, IDindividu)]["ventilation"] = total_ventilation

        # Récupère les pièces
        dictPieces = {}
        req = """SELECT pieIDindividu, pieNature
                FROM matPieces
                WHERE pieIDactivite = %d
                GROUP BY pieIDindividu, pieNature ; """ % self.IDactivite
        DB.ExecuterReq(req)
        listePieces = DB.ResultatReq()
        for IDindividu, nature in listePieces :
            if nature != 'AVO':
                if IDindividu in dictPieces:
                    if dictPieces[IDindividu] != nature:
                        dictPieces[IDindividu] += "-"+ nature
                else:
                    if nature != None :
                        dictPieces[IDindividu] = nature

        # Récupération des données sur les individus inscrits
        self.listeChamps = []
        for dictChamp in LISTE_CHAMPS1 :
            champ = dictChamp["champ"]
            if champ != None :
                self.listeChamps.append(champ)
        strChamps = ",".join(self.listeChamps)
        # les champs avec fonction SUM MIN MAX ne doivent pas être dans le 'group by'
        lstgroupby = [x for x in self.listeChamps if "(" not in x]
        strgroupby = ",".join(lstgroupby)
        req = """
        SELECT %s
        FROM (((inscriptions
        LEFT JOIN individus ON inscriptions.IDindividu = individus.IDindividu)
        LEFT JOIN groupes ON inscriptions.IDgroupe = groupes.IDgroupe)
        LEFT JOIN categories_tarifs ON inscriptions.IDcategorie_tarif = categories_tarifs.IDcategorie_tarif)
        LEFT JOIN consommations ON inscriptions.IDinscription = consommations.IDinscription
        WHERE ((inscriptions.IDactivite=%d) AND (inscriptions.IDgroupe IN %s))
        %s
        GROUP BY %s
        ;""" % (strChamps, self.IDactivite, conditionGroupes, conditionCategories, strgroupby)
        DB.ExecuterReq(req)
        listeDonnees = DB.ResultatReq()
        lstInscriptions = []
        dictInscriptions = {}
        ixIndividu = self.listeChamps.index("inscriptions.IDindividu")
        ixInscription = self.listeChamps.index("inscriptions.IDinscription")
        for valeurs in listeDonnees :
            dictTemp = {}
            IDindividu = valeurs[ixIndividu]
            IDinscription = valeurs[ixInscription]
            dictTemp["IDindividu"] = IDindividu

            lstInscriptions.append(IDinscription)
            
            # Infos issues directement de la requête
            index = 0
            for dictChamp in LISTE_CHAMPS1 :
                if dictChamp["champ"] != None :
                    code = dictChamp["code"]
                    dictTemp[code] = valeurs[index]
                    index += 1
                
            # Infos sur la civilité
            IDcivilite = dictTemp["IDcivilite"]
            if IDcivilite == None :
                IDcivilite = 1
            dictTemp["genre"] = DICT_CIVILITES[IDcivilite]["sexe"]
            dictTemp["categorieCivilite"] = DICT_CIVILITES[IDcivilite]["categorie"]
            dictTemp["civiliteLong"]  = DICT_CIVILITES[IDcivilite]["civiliteLong"]
            dictTemp["civiliteAbrege"] = DICT_CIVILITES[IDcivilite]["civiliteAbrege"]
            dictTemp["nomImage"] = DICT_CIVILITES[IDcivilite]["nomImage"]

            # Age
            if dictTemp["date_naiss"] == None :
                dictTemp["age"] = None
            else:
                datenaissDD = datetime.date(year=int(dictTemp["date_naiss"][:4]), month=int(dictTemp["date_naiss"][5:7]), day=int(dictTemp["date_naiss"][8:10]))
                datedujour = datetime.date.today()
                age = (datedujour.year - datenaissDD.year) - int((datedujour.month, datedujour.day) < (datenaissDD.month, datenaissDD.day))
                dictTemp["age"] = age
                dictTemp["date_naiss"] = datenaissDD

            # Nom Complet
            nomComplet = dictTemp["nomIndividu"]
            if dictTemp["prenomIndividu"] != None :
                nomComplet += ", " + dictTemp["prenomIndividu"]
            dictTemp["nomComplet"] = nomComplet

            # Adresse auto ou manuelle de l'inscrit
            adresse_auto = dictTemp["adresse_auto"]
            if adresse_auto != None and adresse_auto in DICT_INFOS_INDIVIDUS :
                dictTemp["rue_resid"] = DICT_INFOS_INDIVIDUS[adresse_auto]["rue_resid"]
                dictTemp["cp_resid"] = DICT_INFOS_INDIVIDUS[adresse_auto]["cp_resid"]
                dictTemp["ville_resid"] = DICT_INFOS_INDIVIDUS[adresse_auto]["ville_resid"]

            # Facturation
            totalFacture = decimal.Decimal(str(0.0))
            totalRegle = decimal.Decimal(str(0.0))
            totalSolde = decimal.Decimal(str(0.0))
            key = (dictTemp["IDfamille"], dictTemp["IDindividu"])
            # si IDfamille n'est pas null
            if valeurs[self.listeChamps.index("inscriptions.IDfamille")] != None:
                if key in dictFacturation :
                    totalFacture = decimal.Decimal(str(dictFacturation[key]["prestations"]))
                    if totalFacture == None : totalFacture = decimal.Decimal(str(0.0))
                    totalRegle = decimal.Decimal(str(dictFacturation[key]["ventilation"]))
                    if totalRegle == None : totalRegle = decimal.Decimal(str(0.0))
                    totalSolde = totalFacture - totalRegle
            dictTemp["totalFacture"] = totalFacture
            dictTemp["totalRegle"] = totalRegle
            dictTemp["totalSolde"] = totalSolde
            if dictTemp["nomCategorie"] == None:
                dictTemp["nomCategorie"] = "TARIF SUPPRIME DE L'ACTIVITE !!!"

            #Nature pièce
            IDindividu = dictTemp["IDindividu"]
            if IDindividu in dictPieces:
                nature = dictPieces[IDindividu]
                dictTemp["nature"] = nature
            else:
                # cas des avoirs
                dictTemp["nature"] = "sans"
            dictInscriptions[IDinscription]=dictTemp

        # Appel des liens pour trouver le correspondant et les titulaires de la famille
        req = """
                SELECT inscriptions.IDinscription,familles.adresse_intitule, familles.adresse_individu, rattachements.IDindividu
                FROM (  inscriptions 
                        LEFT JOIN rattachements ON inscriptions.IDfamille = rattachements.IDfamille) 
                        LEFT JOIN familles ON inscriptions.IDfamille = familles.IDfamille
                WHERE (rattachements.titulaire = 1)
                        AND ( inscriptions.IDinscription IN  (%s) )
                GROUP BY inscriptions.IDinscription,familles.adresse_intitule, familles.adresse_individu, rattachements.IDindividu;                
            """ % (str(lstInscriptions)[1:-1])
        DB.ExecuterReq(req)
        listeDonnees2 = DB.ResultatReq()
        DB.Close()
        dictTitulaires = {}
        # constitution du dict des liens
        for IDinscription, intitule, IDcorrespondant, IDtitulaire in listeDonnees2 :
            if not IDinscription in list(dictTitulaires.keys()):
                dictTitulaires[IDinscription] = {'designation':intitule,'IDcorrespondant':IDcorrespondant,'lstIDtitulaires':[]}
            dictTitulaires[IDinscription]['lstIDtitulaires'].append(IDtitulaire)

        # reprise des inscriptions pour compléments famille
        for IDinscription, dictTemp in dictInscriptions.items():
            dictTemp["C_designation"] = dictTitulaires[IDinscription]["designation"]
            IDcorresp = dictTitulaires[IDinscription]["IDcorrespondant"]
            #if DICT_INFOS_INDIVIDUS[IDcorresp]["adresse_auto"]:
            #    IDcorresp = DICT_INFOS_INDIVIDUS[IDcorresp]["adresse_auto"]
            dictTemp["C_rue_resid"] = dictTemp["rue_resid"]
            dictTemp["C_cp_resid"] = dictTemp["cp_resid"]
            dictTemp["C_ville_resid"] = dictTemp["ville_resid"]
            dictTemp["R_telephones"] = ""
            dictTemp["R_mails"] = ""
            dictTemp["R_professions"] = ""
            for titulaire in dictTitulaires[IDinscription]["lstIDtitulaires"]:
                dictTemp["R_telephones"] += DICT_INFOS_INDIVIDUS[titulaire]["telephones"]
                dictTemp["R_mails"] += DICT_INFOS_INDIVIDUS[titulaire]["mails"]
                dictTemp["R_professions"] += DICT_INFOS_INDIVIDUS[titulaire]["profession"]
            # Formatage sous forme de TRACK
            track = Track(dictTemp)
            # on écarte les pièces avoir qui ont généré une absence de nature
            if track.nature != "sans":
                listeListeView.append(track)

        return listeListeView

    def InitObjectListView(self):
        # Création du imageList
        for categorie, civilites in Civilites.LISTE_CIVILITES :
            for IDcivilite, CiviliteLong, CiviliteAbrege, nomImage, genre in civilites :
                indexImg = self.AddNamedImages(nomImage, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/%s" % nomImage), wx.BITMAP_TYPE_PNG))

        self.imgVert = self.AddNamedImages("vert", wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Ventilation_vert.png"), wx.BITMAP_TYPE_PNG))
        self.imgRouge = self.AddNamedImages("rouge", wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Ventilation_rouge.png"), wx.BITMAP_TYPE_PNG))
        self.imgOrange = self.AddNamedImages("orange", wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Ventilation_orange.png"), wx.BITMAP_TYPE_PNG))

        def GetImageCivilite(track):
            return track.nomImage

        def GetImageVentilation(track):
            if track.totalFacture == track.totalRegle :
                return self.imgVert
            if track.totalRegle == 0.0 or track.totalRegle == None :
                return self.imgRouge
            if track.totalRegle < track.totalFacture :
                return self.imgOrange
            return self.imgRouge

        def FormateDate(dateDD):
            if dateDD == None : return ""
            return DateEngFr(str(dateDD))

        def FormateMontant(montant):
            if montant == None or montant == "" : return ""
            return "%.2f %s" % (montant, SYMBOLE)

        def FormateSolde(montant):
            if montant == None : decimal.Decimal("0.0")
            if montant == decimal.Decimal("0.0") :
                return "%.2f %s" % (montant, SYMBOLE)
            elif montant > decimal.Decimal(str("0.0")) :
                return "- %.2f %s" % (montant, SYMBOLE)
            else:
                return "+ %.2f %s" % (montant, SYMBOLE)

        def FormateAge(age):
            if age == None : return ""
            return _("%d ans") % age

        def rowFormatter(listItem, track):
            if track.valide == False :
                listItem.SetTextColour(wx.Colour(150, 150, 150))
                
        # Couleur en alternance des lignes
        self.oddRowsBackColor = wx.Colour(255, 255, 255) #"#EEF4FB" # Bleu
        self.evenRowsBackColor = "#F0FBED" # Vert

        # Filtre des colonnes
        self.SetChampsAffiches(self.lstChampsAffiches)

        # Création des colonnes
        listeColonnes = []
        for dictChamp in LISTE_CHAMPS :
            if dictChamp["afficher"] == True :
                # stringConverter
                if "stringConverter" in dictChamp :
                    stringConverter = dictChamp["stringConverter"]
                    if stringConverter == "date" : stringConverter=FormateDate
                    elif stringConverter == "age" : stringConverter=FormateAge
                    elif stringConverter == "montant" : stringConverter=FormateMontant
                    elif stringConverter == "solde" : stringConverter=FormateSolde
                    else : stringConverter = None
                else:
                    stringConverter = None
                # Image Getter
                if "imageGetter" in dictChamp :
                    imageGetter = dictChamp["imageGetter"]
                    if imageGetter == "civilite" : imageGetter = GetImageCivilite
                    elif imageGetter == "ventilation" : imageGetter = GetImageVentilation
                    else : imageGetter = None
                else:
                    imageGetter = None
                # Création de la colonne
                colonne = ColumnDefn(dictChamp["label"], dictChamp["align"], dictChamp["largeur"], dictChamp["code"], typeDonnee=dictChamp["typeDonnee"], stringConverter=stringConverter, imageGetter=imageGetter)
                listeColonnes.append(colonne)
        self.SetColumns(listeColonnes)

        # Regroupement
        if self.regroupement != None :
            self.SetColonneTri(self.regroupement)
            self.SetShowGroups(True)
            self.useExpansionColumn = False
        else:
            self.SetShowGroups(False)
            self.useExpansionColumn = False

        self.SetShowItemCounts(True)
        if len(self.columns) > 0 :
            self.SetSortColumn(self.columns[0])
        self.SetEmptyListMsg(_("Aucune inscription"))
        self.SetEmptyListMsgFont(wx.FFont(11, wx.DEFAULT, faceName="Tekton"))
        self.SetObjects(self.donnees)

    def GetTitresColonnes(self):
        listeColonnes = []
        for index in range(0, self.GetColumnCount()) :
            listeColonnes.append(self.columns[index].title)
        return listeColonnes
    
    def SetColonneTri(self, label=""):
        index = 0
        for dictTemp in LISTE_CHAMPS :
            if dictTemp["afficher"] == True :
                if dictTemp["label"] == label :
                    self.SetAlwaysGroupByColumn(index)
                    return
                index += 1
                    
    def MAJ(self, IDindividu=None, IDactivite=None, toutesAnnees=True, listeGroupes=[], listeCategories=[], regroupement=None, listeColonnes=[], labelParametres=""):
        self.IDactivite = IDactivite
        self.toutesAnnees = toutesAnnees
        self.listeGroupes = listeGroupes
        self.listeCategories = listeCategories
        self.regroupement = regroupement
        if len(listeColonnes) > 0:
            self.lstChampsAffiches = listeColonnes
        self.labelParametres = labelParametres
        if IDindividu != None :
            self.selectionID = IDindividu
            self.selectionTrack = None
        else:
            self.selectionID = None
            self.selectionTrack = None
        attente = wx.BusyInfo(_("Recherche des données..."), self)
        self.InitModel()
        self.InitObjectListView()
        del attente
        # Sélection d'un item
        if self.selectionTrack != None :
            self.SelectObject(self.selectionTrack, deselectOthers=True, ensureVisible=True)
        self.selectionID = None
        self.selectionTrack = None
    
    def Selection(self):
        return self.GetSelectedObjects()
    
    def GetListeChamps(self):
        return LISTE_CHAMPS

    def SetChampsAffiches(self, listeLabels=[]):
        global LISTE_CHAMPS
        index = 0
        for dictTemp in LISTE_CHAMPS :
            if dictTemp["label"] in listeLabels :
                LISTE_CHAMPS[index]["afficher"] = True
            else:
                LISTE_CHAMPS[index]["afficher"] = False
            index += 1
    
    def OnContextMenu(self, event):
        """Ouverture du menu contextuel """        
        # Création du menu contextuel
        menuPop = wx.Menu()

        # Item Ouverture fiche famille
        item = wx.MenuItem(menuPop, 10, _(u"Ouvrir la fiche famille"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Famille.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.OuvrirFicheFamille, id=10)

        menuPop.AppendSeparator()

        # Génération automatique des fonctions standards
        self.GenerationContextMenu(menuPop, dictParametres=self.GetParametresImpression())

        self.PopupMenu(menuPop)
        menuPop.Destroy()

    def GetParametresImpression(self):
        dictParametres = {
            "titre" : _(u"Liste des inscriptions"),
            "intro" : self.labelParametres,
            "total" : _(u"> %s individus") % len(self.donnees),
            "orientation" : wx.PORTRAIT,
            }
        return dictParametres

    def OuvrirFicheFamille(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("familles_fiche", "consulter") == False : return
        if len(self.Selection()) == 0 :
            dlg = wx.MessageDialog(self, _(u"Vous n'avez sélectionné aucune fiche famille à ouvrir !"), _(u"Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        IDindividu = self.Selection()[0].IDindividu
        IDfamille = self.Selection()[0].IDfamille
        from Dlg import DLG_Famille
        dlg = DLG_Famille.Dialog(self, IDfamille)
        if dlg.ShowModal() == wx.ID_OK:
            self.MAJ(IDindividu=IDindividu, IDactivite=self.IDactivite, listeGroupes=self.listeGroupes, listeCategories=self.listeCategories, regroupement=self.regroupement)
        dlg.Destroy()

    def Apercu(self, event):
        nbreIndividus = len(self.donnees)
        from Utils import UTILS_Printer
        prt = UTILS_Printer.ObjectListViewPrinter(self, titre=_("Liste des inscriptions"), intro=self.labelParametres, total=_("> %d individus") % nbreIndividus, format="A", orientation=wx.LANDSCAPE)
        prt.Preview()

    def EnvoyerEmail(self, event):
        """ Envoyer l'inscription par Email """
        if len(self.Selection()) == 0 :
            dlg = wx.MessageDialog(self, _(u"Vous n'avez sélectionné aucune inscription à envoyer par Email !"), _(u"Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        track = self.Selection()[0]
        # Envoi du mail
        from Utils import UTILS_Envoi_email
        UTILS_Envoi_email.EnvoiEmailFamille(parent=self, IDfamille=track.IDfamille, nomDoc=FonctionsPerso.GenerationNomDoc("INSCRIPTION", "pdf") , categorie="inscription")

    def Imprimer(self, event):
        nbreIndividus = len(self.donnees)
        from Utils import UTILS_Printer
        prt = UTILS_Printer.ObjectListViewPrinter(self, titre=_("Liste des inscriptions"), intro=self.labelParametres, total=_("> %d individus") % nbreIndividus, format="A", orientation=wx.LANDSCAPE)
        prt.Print()

    def CreationPDF(self, nomDoc="", afficherDoc=True):
        """ Création du PDF pour Email """
        IDinscription = self.Selection()[0].IDinscription
        from Utils import UTILS_Inscriptions
        inscription = UTILS_Inscriptions.Inscription()
        resultat = inscription.Impression(listeInscriptions=[IDinscription,], nomDoc=nomDoc, afficherDoc=False)
        if resultat == False :
            return False
        dictChampsFusion, dictPieces = resultat
        return dictChampsFusion[IDinscription]

    def ExportTexte(self, event):
        from Utils import UTILS_Export
        UTILS_Export.ExportTexte(self, titre=_("Liste des inscriptions"), autoriseSelections=False)

    def ExportExcel(self, event):
        from Utils import UTILS_Export
        UTILS_Export.ExportExcel(self, titre=_("Liste des inscriptions"), autoriseSelections=False)

# -------------------------------------------------------------------------------------------------------------------------------------------

class BarreRecherche(wx.SearchCtrl):
    def __init__(self, parent):
        wx.SearchCtrl.__init__(self, parent, size=(-1, -1), style=wx.TE_PROCESS_ENTER)
        self.parent = parent
        self.rechercheEnCours = False

        self.SetDescriptiveText(_("Rechercher..."))
        self.ShowSearchButton(True)

        self.listView = self.parent.ctrl_listview
        nbreColonnes = self.listView.GetColumnCount()
        self.listView.SetFilter(Filter.TextSearch(self.listView, self.listView.columns[0:nbreColonnes]))

        self.SetCancelBitmap(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Interdit.png"), wx.BITMAP_TYPE_PNG))
        self.SetSearchBitmap(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Loupe.png"), wx.BITMAP_TYPE_PNG))

        self.Bind(wx.EVT_SEARCHCTRL_SEARCH_BTN, self.OnSearch)
        self.Bind(wx.EVT_SEARCHCTRL_CANCEL_BTN, self.OnCancel)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnDoSearch)
        self.Bind(wx.EVT_TEXT, self.OnDoSearch)

    def OnSearch(self, evt):
        self.Recherche()

    def OnCancel(self, evt):
        self.SetValue("")
        self.Recherche()

    def OnDoSearch(self, evt):
        self.Recherche()

    def Recherche(self):
        txtSearch = self.GetValue().replace("'","\\'")
        self.ShowCancelButton(len(txtSearch))
        self.listView.GetFilter().SetText(txtSearch)
        self.listView.RepopulateList()
        self.Refresh()


# -------------------------------------------------------------------------------------------------------------------------------------------

class ListviewAvecFooter(PanelAvecFooter):
    def __init__(self, parent, kwargs={}):
        dictColonnes = {
            "nomComplet" : {"mode" : "nombre", "singulier" : _("ligne"), "pluriel" : _("lignes"), "compter":"IDindividu", "alignement" : wx.ALIGN_CENTER},
            "totalFacture" : {"mode" : "total"},
            "totalRegle" : {"mode" : "total"},
            "totalSolde" : {"mode" : "total"},
            }
        PanelAvecFooter.__init__(self, parent, ListView, kwargs, dictColonnes)

# ----------------- FRAME DE TEST ----------------------------------------------------------------

class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self, -1)
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_1.Add(panel, 1, wx.ALL|wx.EXPAND)
        self.SetSizer(sizer_1)
        self.myOlv = ListView(panel, -1, style=wx.LC_REPORT|wx.SUNKEN_BORDER)
        self.myOlv.MAJ(IDactivite=396, listeGroupes=[1012,1036,802,803,928,982,981,983,1014,], listeCategories=[1074,], listeColonnes=["nomComplet", "age"])
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_2.Add(self.myOlv, 1, wx.ALL|wx.EXPAND, 4)
        panel.SetSizer(sizer_2)
        self.SetSize((800, 400))
        self.Layout()

def GetDictFacturation():
    DB = GestionDB.DB()

    # Récupère les prestations
    req = """SELECT IDfamille, IDindividu, SUM(montant)
    FROM prestations
    WHERE IDactivite=%d
    GROUP BY IDindividu, IDfamille
    ;""" % 1
    DB.ExecuterReq(req)
    listePrestations = DB.ResultatReq()
    dictPrestations = {}
    for IDfamille, IDindividu, total_prestations in listePrestations :
        dictPrestations[(IDfamille, IDindividu)] = {"prestations":total_prestations, "ventilation":0.0}


    # Récupère la ventilation
    req = """SELECT IDfamille, IDindividu, SUM(ventilation.montant)
    FROM ventilation
    LEFT JOIN prestations ON prestations.IDprestation = ventilation.IDprestation
    WHERE prestations.IDactivite=%d
    GROUP BY IDfamille, IDindividu
    ;""" % 1
    DB.ExecuterReq(req)
    listeVentilations = DB.ResultatReq()
    dictVentilations = {}
    for IDfamille, IDindividu, total_ventilation in listeVentilations :
        dictPrestations[(IDfamille, IDindividu)]["ventilation"] = total_ventilation

    DB.Close()

if __name__ == '__main__':
##    GetDictFacturation() 
    
    app = wx.App(0)
    #wx.InitAllImageHandlers()
    frame_1 = MyFrame(None, -1, "GroupListView")
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()
