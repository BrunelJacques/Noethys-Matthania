#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, Matthania, modif des colonnes et de l'affichage des activités et gestion des catégories supprimées
# Site internet :  www.noethys.com, Matthania
# Auteur:           Ivan LUCAS, JB
# Copyright:       (c) 2010-11 Ivan LUCAS, JB
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------


from Utils.UTILS_Traduction import _
import Chemins
import wx
import GestionDB
import datetime
import decimal
from Utils import UTILS_Utilisateurs
from Data import DATA_Civilites as Civilites
from Utils import UTILS_Config
from Ctrl.CTRL_ParamListeInscriptions import DLD_CHAMPS, DD_SELECT
from Ctrl.CTRL_ObjectListView import GroupListView, ColumnDefn, Filter, CTRL_Outils, PanelAvecFooter

DICT_CIVILITES = Civilites.GetDictCivilites()
SYMBOLE = UTILS_Config.GetParametre("monnaie_symbole", "€")


def Nz(valeur):
    if valeur == None:
        valeur = 0
    return valeur

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

def InitListeChamps():
    global LISTE_CHAMPS
    LISTE_CHAMPS = []

def Compacte(adresse):
    compactee = ""
    if adresse:
        lst=adresse.split("\n")
        for ligne in lst:
            if len(ligne) > 0:
                compactee += ligne + "\n"
        if len(compactee)>0:
            compactee = compactee[:-1]
    return compactee
# ---------------------------------------- LISTVIEW  -----------------------------------------------------------------------

class Track(object):
    def __init__(self, donnees, lstColonnes):
        for (code,champ) in lstColonnes :
            if code in donnees:
                setattr(self, code, donnees[code])
            else:
                setattr(self, code, None)
                if champ == None:
                    print("La colonne %s n'est pas composée dans GetTracks !"% (code))

class ListView(GroupListView):
    def __init__(self, *args, **kwds):
        GroupListView.__init__(self, *args, **kwds)
        InitListeChamps()
        self.listeChamps = LISTE_CHAMPS
        self.selectionID = None
        self.selectionTrack = None
        self.donnees = []
        self.listeActivites = None
        self.listeGroupes = []
        self.listeCategories = []
        self.listeOptions = []
        self.listeColonnes = []
        self.labelParametres = ""
        # Binds perso
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OuvrirFicheFamille)
        self.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)

    def GetTracks(self):
        listeListeView = []
        if len(self.listeActivites) == 0:
            return listeListeView
        self.DB = GestionDB.DB()
                
        # Condition Activites
        if len(self.listeActivites) == 0 : conditionActivites = "()"
        elif len(self.listeActivites) == 1 : conditionActivites = "(%d)" % self.listeActivites[0]
        else : conditionActivites =  str(tuple(self.listeActivites))

        # Condition Groupes
        if len(self.listeGroupes) == 0 : conditionGroupes = "()"
        elif len(self.listeGroupes) == 1 : conditionGroupes = "(%d)" % self.listeGroupes[0]
        else : conditionGroupes = str(tuple(self.listeGroupes))

        # Condition Catégories
        if len(self.listeCategories) == 0 : conditionCategories = " "
        elif len(self.listeCategories) == 1 : conditionCategories = "(%d)" % self.listeCategories[0]
        else : conditionCategories =  str(tuple(self.listeCategories))

        #-----------------------------------------------------
        # Composition des données composées à partir des valeurs simples, absentes dans les select
        #-----------------------------------------------------
        def ComposeExtend(dictTemp, donnees, champs):
            if len(champs) != len(donnees):
                print("Nombre de champs1 et donnees1 differents !", len(champs), len(donnees))
                return None
            for champ in champs:
                index = champs.index(champ)
                dictTemp[champ] = donnees[index]

        def age(dictTemp):
            # Compose Age
            dateNaiss = dictTemp["individus.date_naiss"]
            if dateNaiss == None:
                age = None
            else:
                try:
                    datenaissDD = datetime.date(year=int(dateNaiss[:4]), month=int(dateNaiss[5:7]), day=int(dateNaiss[8:10]))
                    datedujour = datetime.date.today()
                    age = (datedujour.year - datenaissDD.year) - int(
                        (datedujour.month, datedujour.day) < (datenaissDD.month, datenaissDD.day))
                except:
                    age = None
            dictTemp["age"] = age

        def nomPrenom(dictTemp):
            # Nom Complet
            nom = dictTemp["individus.nom"]
            prenom = dictTemp["individus.prenom"]
            if prenom != None:
                nom += ", " + prenom
            dictTemp["nomPrenom"] = nom

        def adresse(dictTemp):
            # Adresse auto ou manuelle
            adresse_auto = dictTemp["individus.adresse_auto"]
            if adresse_auto != None:
                dictTemp["rue"] = Compacte(dictTemp["individus_1.rue_resid"])
                dictTemp["cp"] = dictTemp["individus_1.cp_resid"]
                dictTemp["ville"] = Compacte(dictTemp["individus_1.ville_resid"])
            else:
                dictTemp["rue"] = Compacte(dictTemp["individus.rue_resid"])
                dictTemp["cp"] = dictTemp["individus.cp_resid"]
                dictTemp["ville"] = Compacte(dictTemp["individus.ville_resid"])

        def anneeMois(dictTemp):
            # mois d'inscription
            date = dictTemp["inscriptions.date_inscription"]
            if date != None:
                date = date[:7]
            dictTemp["anneemois"] = date

        def civilite(dictTemp):
            # Infos sur la civilité
            IDcivilite = dictTemp["individus.IDcivilite"]
            if IDcivilite == None:
                IDcivilite = 1
            dictTemp["genre"] = DICT_CIVILITES[IDcivilite]["sexe"]
            dictTemp["categorieCivilite"] = DICT_CIVILITES[IDcivilite]["categorie"]
            dictTemp["civilitelong"] = DICT_CIVILITES[IDcivilite]["civiliteLong"]
            dictTemp["civilite"] = DICT_CIVILITES[IDcivilite]["civiliteAbrege"]
            dictTemp["nomImage"] = DICT_CIVILITES[IDcivilite]["nomImage"]

        def getTelFamille(IDfamille):
            # elargissement de la recherche aux représentants de la famille
            lstSelectTel = "individus.tel_mobile,individus.tel_domicile, individus.travail_tel, individus.tel_fax "
            req = """
                    SELECT %s 
                    FROM rattachements 
                    INNER JOIN individus ON rattachements.IDindividu = individus.IDindividu
                    WHERE ((rattachements.IDcategorie =1) AND ((rattachements.IDfamille)= %d));
                    """ % (lstSelectTel, dictTemp["inscriptions.IDfamille"])
            self.DB.ExecuterReq(req,MsgBox="ExecuterReq")
            recordset = self.DB.ResultatReq()
            no_1, no_2 = None, None
            for lstTel in recordset:
                for tel in lstTel:
                    if tel != None:
                        if len(tel) > 6:
                            if no_1 == None:
                                no_1 = "resp " + tel
                            else:
                                if no_2 == None:
                                    no_2 = tel
            ntel = no_1
            if no_2 != None:
                ntel += ", " + no_2
            return ntel

        def telephones(dictTemp):
            no_1, no_2 = None, None
            lstKeysTel = ["individus.tel_mobile", "individus.tel_domicile", "individus.travail_tel", "individus.tel_fax"]
            for tel in lstKeysTel:
                if dictTemp[tel] != None:
                    if len(dictTemp[tel]) > 6:
                        if no_1 == None:
                            no_1 = dictTemp[tel]
                        else:
                            if no_2 == None:
                                no_2 = dictTemp[tel]
            dictTemp["telephones"] = no_1
            if no_2 != None:
                dictTemp["telephones"] += ", " + no_2

            if dictTemp["telephones"] == None:
                dictTemp["telephones"] = getTelFamille(dictTemp["inscriptions.IDfamille"])

        def getMailFamille(IDfamille):
            # elargissement de la recherche aux représentants de la famille
            lstSelectMail = "individus.mail, individus.travail_mail "
            req = """
                    SELECT %s 
                    FROM rattachements 
                    INNER JOIN individus ON rattachements.IDindividu = individus.IDindividu
                    WHERE ((rattachements.IDcategorie =1) AND ((rattachements.IDfamille)= %d));
                    """ % (lstSelectMail, dictTemp["inscriptions.IDfamille"])
            self.DB.ExecuterReq(req,MsgBox="ExecuterReq")
            recordset = self.DB.ResultatReq()
            no_1, no_2 = None, None
            for lstMail in recordset:
                for mail in lstMail:
                    if mail != None:
                        if len(mail) > 6:
                            if no_1 == None:
                                no_1 = "resp " + mail
                            else:
                                if no_2 == None:
                                    no_2 = mail
            nmail = no_1
            if no_2 != None:
                nmail += ", " + no_2
            return nmail

        def mails(dictTemp):
            no_1, no_2 = None, None
            lstKeysMel = ["individus.mail", "individus.travail_mail", ]
            for mel in lstKeysMel:
                if dictTemp[mel] != None:
                    if len(dictTemp[mel]) > 6:
                        if no_1 == None:
                            no_1 = dictTemp[mel]
                        else:
                            if no_2 == None:
                                no_2 = dictTemp[mel]
            dictTemp["mails"] = no_1
            if no_2 != None:
                dictTemp["mails"] += ", " + no_2

            if dictTemp["mails"] == None:
                dictTemp["mails"] = getMailFamille(dictTemp["inscriptions.IDfamille"])

        def soldPrest(dictTemp):
            if "mttPrest" in list(dictTemp.keys()) and "montantRegle" in list(dictTemp.keys()):
                mtt = Nz(dictTemp["mttPrest"]) - Nz(dictTemp["montantRegle"])
            elif "mttPrest" in list(dictTemp.keys()):
                mtt = Nz(dictTemp["mttPrest"])
            else:
                mtt = None
            if mtt == 0.0: mtt = None
            dictTemp["soldPrest"] = mtt

        def nomPrenom_F(dictTemp):
            # Nom Complet
            nom = dictTemp["individus_F.nom"]
            prenom = dictTemp["individus_F.prenom"]
            if prenom != None:
                nom += ", " + prenom
            dictTemp["nomPrenom_F"] = nom

        def adresse_F(dictTemp):
            # Adresse auto ou manuelle
            adresse_auto = dictTemp["individus_F.adresse_auto"]
            if adresse_auto != None:
                dictTemp["rue_F"] = Compacte(dictTemp["individus_F1.rue_resid"])
                dictTemp["cp_F"] = dictTemp["individus_F1.cp_resid"]
                dictTemp["ville_F"] = Compacte(dictTemp["individus_F1.ville_resid"])
            else:
                dictTemp["rue_F"] = Compacte(dictTemp["individus_F.rue_resid"])
                dictTemp["cp_F"] = dictTemp["individus_F.cp_resid"]
                dictTemp["ville_F"] = Compacte(dictTemp["individus_F.ville_resid"])

        def civilite_F(dictTemp):
            # Infos sur la civilité
            IDcivilite = dictTemp["individus_F.IDcivilite"]
            if IDcivilite == None:
                IDcivilite = 1
            dictTemp["genre_F"] = DICT_CIVILITES[IDcivilite]["sexe"]
            dictTemp["categorieCivilite_F"] = DICT_CIVILITES[IDcivilite]["categorie"]
            dictTemp["civilitelong_F"] = DICT_CIVILITES[IDcivilite]["civiliteLong"]
            dictTemp["civilite_F"] = DICT_CIVILITES[IDcivilite]["civiliteAbrege"]

        def telephones_F(dictTemp):
            no_1, no_2 = None, None
            for tel in ["individus_F.tel_mobile", "individus_F.tel_domicile", "individus_F.travail_tel", "individus_F.tel_fax"]:
                if len(tel) > 6:
                    if no_1 == None:
                        no_1 = dictTemp[tel]
                    else:
                        if no_2 == None:
                            no_2 = dictTemp[tel]
            dictTemp["telephones_F"] = no_1
            if no_2 != None:
                dictTemp["telephones_F"] += ", " + no_2
            if dictTemp["telephones_F"] == None:
                dictTemp["telephones_F"] = getTelFamille(dictTemp["inscriptions.IDfamille"])

        def mails_F(dictTemp):
            no_1, no_2 = None, None
            for mail in ["individus_F.mail", "individus_F.travail_mail"]:
                if len(mail) > 6:
                    if no_1 == None:
                        no_1 = dictTemp[mail]
                    else:
                        if no_2 == None:
                            no_2 = dictTemp[mail]
            dictTemp["mails_F"] = no_1
            if no_2 != None:
                dictTemp["mails_F"] += ", " + no_2
            if dictTemp["mails_F"] == None:
                dictTemp["mails_F"] = getMailFamille(dictTemp["inscriptions.IDfamille"])

        #-----------------------------------------------------
        # Composition de la première requête recherche Base de l'info commune
        # la même structure sera reprise pour les options
        #-----------------------------------------------------
        dictDonnees={}
        reqSelect = "SELECT "
        lenSelect = len(reqSelect)
        reqConditions = " WHERE inscriptions.IDactivite IN %s AND inscriptions.IDgroupe IN %s AND inscriptions.IDcategorie_tarif IN %s " % (
        conditionActivites, conditionGroupes, conditionCategories)
        reqGroupBy = "GROUP BY "
        reqFrom = ""
        compose = ""
        lstColonnes1 = []
        if not self.listeOptions: self.listeOptions = ['entete']
        for option in self.listeOptions[:1]:
            for dictChamp in DLD_CHAMPS[option]:
                lstColonnes1.append((dictChamp["code"],dictChamp["champ"]))
                if dictChamp["champ"] != None:
                    reqSelect += dictChamp["champ"] + ","
                    if "(" not in dictChamp["champ"]:
                        reqGroupBy += dictChamp["champ"] + ","
            reqSelect += DD_SELECT[option]["select"]
            reqFrom += DD_SELECT[option]["from"]
            compose += DD_SELECT[option]["compose"]

        listeSelect = reqSelect[lenSelect:-1].split(",")
        listeCompose = compose.split(",")
        reqSelect = reqSelect[:-1]
        reqGroupBy = reqGroupBy[:-1]
        # Lancement de la requête
        req = """
        %s
        %s
        %s
        %s
        ;
        """ % (reqSelect, reqFrom, reqConditions, reqGroupBy)
        self.DB.ExecuterReq(req, MsgBox="Execute first Select lignes")
        recordset = self.DB.ResultatReq()

        conditionInscriptions = []
        for valeurs in recordset:
            dictTemp = {}
            dictTemp["IDindividu"] = valeurs[0]

            # Infos directe du recordset dans les champs OLV
            for (code,champ) in lstColonnes1:
                if champ != None:
                    index = listeSelect.index(champ)
                    dictTemp[code] = valeurs[index]
                    if code == "IDinscription": conditionInscriptions.append(valeurs[index])

            # ajout des valeurs simples à composer dans dictTemp
            ComposeExtend(dictTemp, valeurs, listeSelect)
            # ajout des valeurs composées
            for champ in listeCompose:
                try:
                    eval(champ + '(dictTemp)')
                except:
                    print("Echec programmation de la composition de ", champ)
            #stockage de la ligne
            dictDonnees[dictTemp["IDinscription"]] = dictTemp

        #-----------------------------------------------------------------
        # Deuxième passage pour composerde la requête des options choisies
        #-----------------------------------------------------------------
        lstColonnes3 = []
        if len(self.listeOptions) >1 :
            lenSelect = 7
            reqSelect0 = "SELECT inscriptions.IDinscription,"
            reqFrom0 = " FROM inscriptions "
            reqConditions0 = " WHERE inscriptions.IDinscription IN ( %s ) " %(str(conditionInscriptions)[1:-1])
            reqGroupBy0 = " GROUP BY inscriptions.IDinscription, "

            compose = ""
            for option in self.listeOptions[1:]:
                lstColonnes2 = []
                reqSelect = reqSelect0
                reqFrom = reqFrom0
                reqConditions = reqConditions0
                reqGroupBy = reqGroupBy0

                for dictChamp in DLD_CHAMPS[option]:
                    lstColonnes2.append((dictChamp["code"], dictChamp["champ"]))
                    if dictChamp["champ"] != None:
                        reqSelect += dictChamp["champ"]+","
                        if "(" not in dictChamp["champ"]:
                                reqGroupBy += dictChamp["champ"]+","
                reqSelect += DD_SELECT[option]["select"]
                reqFrom += DD_SELECT[option]["from"]
                compose += DD_SELECT[option]["compose"]

                listeSelect = reqSelect[lenSelect:-1].split(",")
                listeCompose = compose.split(",")
                reqSelect = reqSelect[:-1]
                reqGroupBy = reqGroupBy[:-1]
                # Lancement de la requête
                req = """
                %s
                %s
                %s
                %s
                ;
                """ % (reqSelect, reqFrom, reqConditions, reqGroupBy)
                self.DB.ExecuterReq(req,MsgBox="Execute Select lignes")
                recordset = self.DB.ResultatReq()

                # le premier champ sert pour regrouper la table principale et eviter les doublons
                champDoublon = DLD_CHAMPS[option][0]["champ"]
                lstDoublons =[]

                if champDoublon in listeSelect:
                    ixDoublon = listeSelect.index(champDoublon)
                else: ixDoublon = None
                for valeurs in recordset :
                    dictTemp = dictDonnees[valeurs[0]]
                    if ixDoublon and valeurs[ixDoublon] in lstDoublons:
                        goDoublon = False
                    else:
                        goDoublon = True
                    # Infos directe du recordset dans les champs OLV
                    for (code, champ) in lstColonnes2:
                        if champ != None:
                            # les champs prestations ne peuvent être pris qu'une fois par ID prestation
                            if champ.split('.')[0] == champDoublon.split('.')[0] and  not goDoublon:
                                continue
                            index = listeSelect.index(champ)
                            if not valeurs[index]:
                                continue
                            if not code in list(dictTemp.keys()):
                                dictTemp[code] = valeurs[index]
                            elif dictTemp[code] and isinstance(valeurs[index],str):
                                dictTemp[code] += ";"+valeurs[index]
                            elif dictTemp[code] and isinstance(valeurs[index],(int,float,decimal.Decimal)):
                                dictTemp[code] += valeurs[index]
                            else:
                                dictTemp[code] = valeurs[index]
                    if ixDoublon and not valeurs[ixDoublon] in lstDoublons:
                        lstDoublons.append(valeurs[ixDoublon])

                    #ajout des valeurs simples à composer dans dictTemp
                    ComposeExtend(dictTemp,valeurs,listeSelect)
                    # ajout des valeurs composées
                    for champ in listeCompose:
                        try:
                            eval(champ + '(dictTemp)')
                        except :
                            print("Echec programmation2 de la composition de ",champ)
                    dictDonnees[dictTemp["IDinscription"]] = dictTemp
                lstColonnes3 += lstColonnes2
        for colonne in lstColonnes3:
            lstColonnes1.append(colonne)

        for inscription in dictDonnees:
            # Formatage sous forme de TRACK
            track = Track(dictDonnees[inscription], lstColonnes1)
            listeListeView.append(track)

        self.DB.Close()
        return listeListeView

    def InitObjectListView(self):
        # Création du imageList
        for categorie, civilites in Civilites.LISTE_CIVILITES :
            for IDcivilite, CiviliteLong, Civilite, nomImage, genre in civilites :
                indexImg = self.AddNamedImages(nomImage, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/%s") % nomImage, wx.BITMAP_TYPE_PNG))

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
        #self.SetChampsAffiches(self.listeColonnes)

        # Création des colonnes
        listeColonnes = []

        for dictChamp in LISTE_CHAMPS :
            # stringConverter
            if "stringConverter" in dictChamp :
                stringConverter = dictChamp["stringConverter"]
                if stringConverter == "date" : stringConverter=FormateDate
                elif stringConverter == "age" : stringConverter=FormateAge
                elif stringConverter == "montant" : stringConverter=FormateMontant
                elif stringConverter == "solde" : stringConverter=FormateSolde
                else : stringConverter = None
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
        
        """# Regroupement
        if self.regroupement != None :
            self.SetColonneTri(self.regroupement)
            self.SetShowGroups(True)
            self.useExpansionColumn = False
        else:
            self.SetShowGroups(False)
            self.useExpansionColumn = False
        """
        self.SetShowGroups(False)
        self.useExpansionColumn = False
        self.SetShowItemCounts(True)
        if len(self.columns) > 0 :
            self.SetSortColumn(self.columns[0])
        self.SetEmptyListMsg(_("La liste se remplira après validation de la sélection"))
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
                    
    def MAJ(self, IDindividu=None, listeActivites=None, listeGroupes=[], listeCategories=[], listeOptions=['entete'], listeColonnes=[], labelParametres=""):
        global LISTE_CHAMPS
        LISTE_CHAMPS = self.listeChamps
        self.listeActivites = listeActivites
        self.listeGroupes = listeGroupes
        self.listeCategories = listeCategories
        self.listeOptions = listeOptions
        self.listeColonnes = listeColonnes
        self.labelParametres = labelParametres
        if IDindividu != None :
            self.selectionID = IDindividu
            self.selectionTrack = None
        else:
            self.selectionID = None
            self.selectionTrack = None
        attente = wx.BusyInfo(_("Recherche des données..."), self)
        self.donnees = self.GetTracks()

        self.InitObjectListView()
        del attente
        # Sélection d'un item
        if self.selectionTrack != None :
            self.SelectObject(self.selectionTrack, deselectOthers=True, ensureVisible=True)
        self.selectionID = None
        self.selectionTrack = None
        #fin MAJ
    
    def Selection(self):
        return self.GetSelectedObjects()

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
        item = wx.MenuItem(menuPop, 10, _("Ouvrir la fiche famille"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Famille.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.OuvrirFicheFamille, id=10)
        
        menuPop.AppendSeparator()
        
        # Item Apercu avant impression
        item = wx.MenuItem(menuPop, 40, _("Aperçu avant impression"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Apercu.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.Apercu, id=40)
        
        # Item Imprimer
        item = wx.MenuItem(menuPop, 50, _("Imprimer"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Imprimante.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.Imprimer, id=50)
        
        menuPop.AppendSeparator()
    
        # Item Export Texte
        item = wx.MenuItem(menuPop, 600, _("Exporter au format Texte"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Texte2.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.ExportTexte, id=600)
        
        # Item Export Excel
        item = wx.MenuItem(menuPop, 700, _("Exporter au format Excel"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Excel.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.ExportExcel, id=700)

        self.PopupMenu(menuPop)
        menuPop.Destroy()
    
    def OuvrirFicheFamille(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("familles_fiche", "consulter") == False : return
        if len(self.Selection()) == 0 :
            dlg = wx.MessageDialog(self, _("Vous n'avez sélectionné aucune fiche famille à ouvrir !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        IDfamille = self.Selection()[0].IDfamille
        from Dlg import DLG_Famille
        dlg = DLG_Famille.Dialog(self, IDfamille)
        dlg.ShowModal()
        dlg.Destroy()
        
    def Apercu(self, event):
        nbreIndividus = len(self.donnees) 
        from Utils import UTILS_Printer
        prt = UTILS_Printer.ObjectListViewPrinter(self, titre=_("Liste des inscriptions"), intro=self.labelParametres, total=_("> %d individus") % nbreIndividus, format="A", orientation=wx.LANDSCAPE)
        prt.Preview()

    def Imprimer(self, event):
        nbreIndividus = len(self.donnees) 
        from Utils import UTILS_Printer
        prt = UTILS_Printer.ObjectListViewPrinter(self, titre=_("Liste des inscriptions"), intro=self.labelParametres, total=_("> %d individus") % nbreIndividus, format="A", orientation=wx.LANDSCAPE)
        prt.Print()

    def ExportTexte(self, event):
        from Utils import UTILS_Export
        UTILS_Export.ExportTexte(self, titre=_("Liste des inscriptions"), autoriseSelections=False)
        
    def ExportExcel(self, event):
        from Utils import UTILS_Export
        UTILS_Export.ExportExcel(self, titre=_("Liste des inscriptions"), autoriseSelections=False)

# -------------------------------------------------------------------------------------------------------------------------------------------

class ListviewAvecFooter(PanelAvecFooter):
    def __init__(self, parent, kwargs={}):
        dictColonnes = {
            "nomPrenom" : {"mode" : "nombre", "singulier" : _("ligne"), "pluriel" : _("lignes"), "alignement" : wx.ALIGN_CENTER},
            }
        PanelAvecFooter.__init__(self, parent, ListView, kwargs, dictColonnes)

# ----------------- FRAME DE TEST ----------------------------------------------------------------

class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self, -1)
        #sizer_1 = wx.BoxSizer(wx.VERTICAL)
        #sizer_1.Add(panel, 1, wx.ALL|wx.EXPAND)
        #self.SetSizer(sizer_1)

        #self.myOlv = ListView(panel, -1, style=wx.LC_REPORT|wx.SUNKEN_BORDER)
        #self.myOlv.MAJ(listeActivites=[1], listeGroupes=[1, 2], listeCategories=[1, 2], listeColonnes=["nomComplet", "age"])

        self.listviewAvecFooter = ListviewAvecFooter(self, kwargs={})
        self.myOlv = self.listviewAvecFooter.GetListview()
        self.myOlv.MAJ(listeActivites=[1], listeGroupes=[1, 2], listeCategories=[1, 2], listeColonnes=["nomComplet", "age"])

        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_2.Add(self.myOlv, 1, wx.ALL|wx.EXPAND, 4)
        panel.SetSizer(sizer_2)
        self.SetSize((200, 200))
        self.Layout()

if __name__ == '__main__':

    app = wx.App(0)
    #wx.InitAllImageHandlers()
    frame_1 = MyFrame(None, -1, "GroupListView")
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()
