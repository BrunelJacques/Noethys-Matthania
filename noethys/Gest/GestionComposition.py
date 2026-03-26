#!/usr/bin/env python
# -*- coding: utf-8 -*-
#----------------------------------------------------------
# Application :    Matthania-Noethys
# Auteur:          Jacques BRUNEL
# Licence:         Licence GNU GPL
# Regroupe toutes la gestion des compositions familles
# et rattachement  des individus
#-----------------------------------------------------------

import Chemins
import wx
import datetime
import GestionDB

from Utils import UTILS_Historique
from Utils import UTILS_SaisieAdresse
from Utils import UTILS_Utilisateurs
from Dlg import DLG_Individu
from Data import DATA_Civilites as Civilites
from Data import DATA_Liens as Liens
from Ctrl import CTRL_Photo
from wx.lib.agw.supertooltip import SuperToolTip,ToolTipWindow
from wx.lib.agw.hypertreelist import HyperTreeList,TR_COLUMN_LINES,TR_ROW_LINES

DICT_TYPES_LIENS = Liens.DICT_TYPES_LIENS

def MAJ(self):
    # appellée par GestCompo
    if hasattr(self, 'MAJ'):
        self.MAJ()
    if hasattr(self, 'MAJnotebook'):
        self.MAJnotebook()

# ---------- Superclasses de la composition famille ----------------------------------

class GetValeurs():
    def __init__(self, IDfamille=None):
        self.IDfamille = IDfamille
        (self.lstIndividus,
         self.dictIndividus,
         self.listeLiens) = self.GetInfosIndividus()
        self.dictInfosIndividus = self.dictIndividus # synonyme nécessaire/Getion Composition

    def GetLiensCadres(self):
        """ Retourne les liens de filiation ou de couple """
        dictRelations = {}
        for numCol in [1, 2, 3]:
            dictRelations[numCol] = {"filiation": {}, "couple": [], "ex-couple": []}
            for IDindividu in self.lstIndividus:
                if self.dictIndividus[IDindividu]["categorie"] == numCol:
                    listeLiensIndividus = self.RechercheLien(IDindividu)
                    for IDindividu_objet, IDtype_lien, typeRelation in listeLiensIndividus:
                        if IDindividu_objet in self.dictIndividus:
                            # Relations de couple
                            if (
                                    typeRelation == "couple" or typeRelation == "ex-couple") and (
                            IDindividu_objet, IDindividu) not in dictRelations[numCol][
                                typeRelation]:
                                dictRelations[numCol][typeRelation].append(
                                    (IDindividu, IDindividu_objet))
                            # Relations de filiation
                            if typeRelation == "enfant":
                                IDenfant = IDindividu
                                IDparent = IDindividu_objet
                                if (IDenfant in dictRelations[numCol][
                                    "filiation"]) == False:
                                    dictRelations[numCol]["filiation"][IDenfant] = [
                                        IDparent, ]
                                else:
                                    if IDparent not in dictRelations[numCol]["filiation"][
                                        IDenfant]:
                                        dictRelations[numCol]["filiation"][
                                            IDenfant].append(IDparent)

        return dictRelations

    def RechercheLien(self, IDindividu):
        listeLiens = []
        for IDlien, IDfamille, IDindividu_sujet, IDtype_lien, IDindividu_objet, responsable in self.listeLiens:
            if IDindividu == IDindividu_sujet:
                if IDtype_lien != None:
                    typeRelation = DICT_TYPES_LIENS[IDtype_lien]["type"]
                    listeLiens.append((IDindividu_objet, IDtype_lien, typeRelation))
        return listeLiens

    def GetInfosIndividus(self):
        dictInfos = {}
        lstIndividus = []
        listeLiens = []

        # Recherche des individus rattachés
        DB = GestionDB.DB()
        req = """SELECT rattachements.IDrattachement, rattachements.IDindividu, rattachements.IDcategorie,
                        rattachements.titulaire, familles.adresse_individu
                FROM rattachements 
                LEFT JOIN familles ON rattachements.IDfamille = familles.IDfamille
                WHERE rattachements.IDfamille=%d;""" % self.IDfamille
        DB.ExecuterReq(req, MsgBox="ExecuterReq")
        listeRattachements = DB.ResultatReq()
        if len(listeRattachements) == 0:
            DB.Close()
            return lstIndividus, dictInfos, listeLiens

        # Intégration de ces premières valeurs dans le dictValeurs
        for IDrattachement, IDindividu, IDcategorie, titulaire, IDcorrespondant in listeRattachements:
            if not IDindividu: continue
            lstIndividus.append(IDindividu)
            dictInfos[IDindividu] = {"categorie": IDcategorie,
                                     "titulaire": titulaire,
                                     "IDrattachement": IDrattachement,
                                     "IDcorrespondant": IDcorrespondant}

        # Recherche des liens existants dans la base
        if len(lstIndividus) == 1:
            condition = "(%d)" % lstIndividus[0]
        else:
            condition = str(tuple(lstIndividus))
        req = """SELECT IDlien, IDfamille, IDindividu_sujet, IDtype_lien, IDindividu_objet, responsable
        FROM liens WHERE IDindividu_sujet IN %s;""" % condition
        DB.ExecuterReq(req, MsgBox="ExecuterReq")
        listeLiens = DB.ResultatReq()

        # Recherche des inscriptions des membres de la famille
        dictInscriptions = {}
        req = """SELECT 
        IDinscription, IDindividu, date_inscription, parti,
        activites.nom, activites.date_debut, activites.date_fin,
        groupes.nom, categories_tarifs.nom
        FROM inscriptions
        LEFT JOIN activites ON activites.IDactivite = inscriptions.IDactivite
        LEFT JOIN groupes ON groupes.IDgroupe = inscriptions.IDgroupe
        LEFT JOIN categories_tarifs ON categories_tarifs.IDcategorie_tarif = inscriptions.IDcategorie_tarif
        WHERE IDfamille=%d;""" % self.IDfamille
        DB.ExecuterReq(req, MsgBox="ExecuterReq")
        listeInscriptions = DB.ResultatReq()
        for IDinscription, IDindividu, dateInscription, parti, nomActivite, activiteDebut, activiteFin, nomGroupe, nomCategorie in listeInscriptions:
            if (IDindividu in dictInscriptions) == False:
                dictInscriptions[IDindividu] = []
            dictTemp = {
                "IDinscription": IDinscription, "dateInscription": dateInscription,
                "parti": parti,
                "nomActivite": nomActivite, "activiteDebut": activiteDebut,
                "activiteFin": activiteFin,
                "nomGroupe": nomGroupe, "nomCategorie": nomCategorie
            }
            dictInscriptions[IDindividu].append(dictTemp)

            # Recherche des infos détaillées sur chaque individu
        dictCivilites = Civilites.GetDictCivilites()
        listeChamps = (
            "IDcivilite", "nom", "prenom", "num_secu", "IDnationalite",
            "date_naiss", "IDpays_naiss", "cp_naiss", "ville_naiss",
            "adresse_auto", "rue_resid", "cp_resid", "ville_resid",
            "IDcategorie_travail", "profession", "employeur", "travail_tel",
            "travail_fax", "travail_mail",
            "tel_domicile", "tel_mobile", "tel_fax", "mail"
        )
        for IDindividu in lstIndividus:
            # Infos de la table Individus
            req = """SELECT %s
            FROM individus WHERE IDindividu=%d;""" % (",".join(listeChamps), IDindividu)
            DB.ExecuterReq(req, MsgBox="ExecuterReq")
            listeIndividus = DB.ResultatReq()
            for index in range(0, len(listeChamps)):
                nomChamp = listeChamps[index]
                dictInfos[IDindividu][nomChamp] = listeIndividus[0][index]
            # Infos sur la civilité
            IDcivilite = dictInfos[IDindividu]["IDcivilite"]
            if IDcivilite:
                dictInfos[IDindividu]["genre"] = dictCivilites[IDcivilite]["sexe"]
                dictInfos[IDindividu]["categorieCivilite"] = dictCivilites[IDcivilite]["categorie"]
                dictInfos[IDindividu]["civiliteLong"] = dictCivilites[IDcivilite]["civiliteLong"]
                dictInfos[IDindividu]["civiliteAbrege"] = dictCivilites[IDcivilite]["civiliteAbrege"]
                dictInfos[IDindividu]["nomImage"] = dictCivilites[IDcivilite]["nomImage"]
            else:
                dictInfos[IDindividu]["genre"] = ""
                dictInfos[IDindividu]["categorieCivilite"] = ""
                dictInfos[IDindividu]["civiliteLong"] = ""
                dictInfos[IDindividu]["civiliteAbrege"] = ""
                dictInfos[IDindividu]["nomImage"] = None

        DB.Close()

        # Recherche des photos
        listeIndividusTemp = []
        for IDindividu, dictValeursTemp in dictInfos.items():
            nomFichier = Chemins.GetStaticPath(
                "Images/128x128/%s" % dictValeursTemp["nomImage"])
            listeIndividusTemp.append((IDindividu, nomFichier))
        dictPhotos = CTRL_Photo.GetPhotos(listeIndividus=listeIndividusTemp,
                                          taillePhoto=(128, 128),
                                          qualite=wx.IMAGE_QUALITY_HIGH)

        # ----------------------------------------------
        # 2ème tournée : Infos détaillées
        # ----------------------------------------------

        for IDindividu in lstIndividus:

            # Nom
            if dictInfos[IDindividu]["categorieCivilite"] != "ENFANT":
                nomComplet1 = "%s %s" % (dictInfos[IDindividu]["nom"],
                                         dictInfos[IDindividu]["prenom"])
                nomComplet2 = "%s %s %s" % ("%d %s" % (IDindividu,
                                                       dictInfos[IDindividu][
                                                           "civiliteAbrege"]),
                                            dictInfos[IDindividu]["nom"],
                                            dictInfos[IDindividu]["prenom"])
            else:
                nomComplet1 = "%s %s" % (dictInfos[IDindividu]["prenom"],
                                         dictInfos[IDindividu]["nom"])
                nomComplet2 = "%d %s" % (IDindividu, nomComplet1)
            dictInfos[IDindividu]["nomComplet1"] = nomComplet1
            dictInfos[IDindividu]["nomComplet2"] = nomComplet2

            # Date de naissance
            datenaissComplet = self.GetTxtDateNaiss(dictInfos, IDindividu)
            dictInfos[IDindividu]["datenaissComplet"] = datenaissComplet

            # Adresse
            adresse_auto = dictInfos[IDindividu]["adresse_auto"]
            if adresse_auto != None and adresse_auto in dictInfos:
                rue_resid = dictInfos[adresse_auto]["rue_resid"]
                cp_resid = dictInfos[adresse_auto]["cp_resid"]
                ville_resid = dictInfos[adresse_auto]["ville_resid"]
            else:
                rue_resid = dictInfos[IDindividu]["rue_resid"]
                cp_resid = dictInfos[IDindividu]["cp_resid"]
                ville_resid = dictInfos[IDindividu]["ville_resid"]
            if cp_resid == None: cp_resid = ""
            if ville_resid == None: ville_resid = ""
            if rue_resid == None: rue_resid = ""
            dictInfos[IDindividu]["adresse_ligne1"] = rue_resid.strip().replace("\n",
                                                                                " - ")
            dictInfos[IDindividu]["adresse_ligne2"] = "%s %s" % (cp_resid, ville_resid)

            # Coordonnées
            tel_domicile = dictInfos[IDindividu]["tel_domicile"]
            if tel_domicile != None:
                dictInfos[IDindividu]["tel_domicile_complet"] = "Tél. domicile : %s" % tel_domicile
            else:
                dictInfos[IDindividu]["tel_domicile_complet"] = None
            tel_mobile = dictInfos[IDindividu]["tel_mobile"]
            if tel_mobile != None:
                dictInfos[IDindividu]["tel_mobile_complet"] =  "Tél. mobile : %s" % tel_mobile
            else:
                dictInfos[IDindividu]["tel_mobile_complet"] = None
            mail = dictInfos[IDindividu]["mail"]
            if mail != None:
                dictInfos[IDindividu]["mail_complet"] = "Email : %s" % mail
            else:
                dictInfos[IDindividu]["mail_complet"] = None
            travail_tel = dictInfos[IDindividu]["travail_tel"]
            if travail_tel != None:
                dictInfos[IDindividu]["travail_tel_complet"] = "Tél. travail : %s" % travail_tel
            else:
                dictInfos[IDindividu]["travail_tel_complet"] = None

                # Infos sur les activités inscrites
            if (IDindividu in dictInscriptions) == True:
                dictInfos[IDindividu]["inscriptions"] = True
                dictInfos[IDindividu]["listeInscriptions"] = dictInscriptions[IDindividu]
            else:
                dictInfos[IDindividu]["inscriptions"] = False
                dictInfos[IDindividu]["listeInscriptions"] = []

            # Photo
            if IDindividu in dictPhotos:
                bmp = dictPhotos[IDindividu]["bmp"]
            else:
                bmp = None
            dictInfos[IDindividu]["photo"] = bmp

        return lstIndividus, dictInfos, listeLiens

    def GetDictCadres(self):
        """ Crée le dictionnaire spécial pour l'affichage des cadres individus """
        dictCadres = {}
        for IDindividu in self.lstIndividus:
            listeLignes = []
            # Ligne NOM
            nomComplet1 = self.dictIndividus[IDindividu]["nomComplet1"]
            listeLignes.append((nomComplet1, 8, "bold"))
            # Ligne Date de naissance
            if self.dictIndividus[IDindividu]["categorie"] == 2:
                txtDatenaiss = self.dictIndividus[IDindividu]["datenaissComplet"]
                listeLignes.append((txtDatenaiss, 7, "normal"))
            # Spacer
            listeLignes.append(("#SPACER#", 1, "normal"))
            # Adresse de résidence
            adresse_ligne1 = self.dictIndividus[IDindividu]["adresse_ligne1"]
            adresse_ligne2 = self.dictIndividus[IDindividu]["adresse_ligne2"]
            if adresse_ligne1 != None and adresse_ligne1 != "": listeLignes.append(
                (adresse_ligne1, 7, "light"))
            if adresse_ligne2 != None and adresse_ligne2 != "": listeLignes.append(
                (adresse_ligne2, 7, "light"))
            # Spacer
            listeLignes.append(("#SPACER#", 1, "normal"))
            # Téléphones
            tel_domicile_complet = self.dictIndividus[IDindividu][
                "tel_domicile_complet"]
            tel_mobile_complet = self.dictIndividus[IDindividu]["tel_mobile_complet"]
            travail_tel_complet = self.dictIndividus[IDindividu][
                "travail_tel_complet"]

            if tel_domicile_complet != None:
                listeLignes.append((tel_domicile_complet, 7, "light"))
            elif tel_mobile_complet != None:
                listeLignes.append((tel_mobile_complet, 7, "light"))
            elif travail_tel_complet != None:
                listeLignes.append((travail_tel_complet, 7, "light"))
            else:
                pass

            # Création du dictionnaire spécial
            dictCadres[IDindividu] = {}
            dictCadres[IDindividu]["textes"] = listeLignes
            dictCadres[IDindividu]["nomImage"] = self.dictIndividus[IDindividu][
                "nomImage"]
            dictCadres[IDindividu]["genre"] = self.dictIndividus[IDindividu]["genre"]
            dictCadres[IDindividu]["categorie"] = self.dictIndividus[IDindividu][
                "categorie"]
            dictCadres[IDindividu]["ctrl"] = None
            dictCadres[IDindividu]["titulaire"] = self.dictIndividus[IDindividu][
                "titulaire"]
            dictCadres[IDindividu]["IDcorrespondant"] = \
            self.dictIndividus[IDindividu]["IDcorrespondant"]
            dictCadres[IDindividu]["correspondant"] = IDindividu == \
                                                      self.dictIndividus[IDindividu][
                                                          "IDcorrespondant"]
            dictCadres[IDindividu]["IDrattachement"] = \
            self.dictIndividus[IDindividu]["IDrattachement"]
            dictCadres[IDindividu]["inscriptions"] = self.dictIndividus[IDindividu][
                "inscriptions"]
            dictCadres[IDindividu]["photo"] = self.dictIndividus[IDindividu]["photo"]
            dictCadres[IDindividu]["adresse_auto"] = self.dictIndividus[IDindividu][
                "adresse_auto"]

        return dictCadres

    def GetDictInfoBulles(self):
        dictInfoBulles = {}
        for IDindividu in self.lstIndividus:
            txtInfoBulle = ""
            # Ligne NOM
            nomComplet2 = self.dictIndividus[IDindividu]["nomComplet2"]
            txtInfoBulle += "----------- %s -----------\n\n" % nomComplet2
            # Ligne Date de naissance
            if self.dictIndividus[IDindividu]["date_naiss"] != None:
                txtDatenaiss = self.dictIndividus[IDindividu]["datenaissComplet"]
                txtInfoBulle += txtDatenaiss + "\n\n"
            # Adresse de résidence
            adresse_ligne1 = self.dictIndividus[IDindividu]["adresse_ligne1"]
            adresse_ligne2 = self.dictIndividus[IDindividu]["adresse_ligne2"]
            if adresse_ligne1 != None and adresse_ligne1 != "": txtInfoBulle += adresse_ligne1 + "\n"
            if adresse_ligne2 != None and adresse_ligne2 != "": txtInfoBulle += adresse_ligne2 + "\n"
            # Spacer
            txtInfoBulle += "\n"
            # Téléphones
            tel_domicile_complet = self.dictIndividus[IDindividu][
                "tel_domicile_complet"]
            tel_mobile_complet = self.dictIndividus[IDindividu]["tel_mobile_complet"]
            travail_tel_complet = self.dictIndividus[IDindividu][
                "travail_tel_complet"]
            mail_complet = self.dictIndividus[IDindividu]["mail_complet"]
            if tel_domicile_complet != None:
                txtInfoBulle += tel_domicile_complet + "\n"
            if tel_mobile_complet != None:
                txtInfoBulle += tel_mobile_complet + "\n"
            if travail_tel_complet != None:
                txtInfoBulle += travail_tel_complet + "\n"
            if mail_complet != None:
                txtInfoBulle += mail_complet + "\n"

            # Création du dictionnaire spécial
            dictInfoBulles[IDindividu] = txtInfoBulle

        return dictInfoBulles

    def GetTxtDateNaiss(self, dictInfos, IDindividu):
        datenaiss = dictInfos[IDindividu]["date_naiss"]
        txtDatenaiss = "Date de naissance inconnue"
        if datenaiss != None:
            try:
                datenaissDD = datetime.date(year=int(datenaiss[:4]),
                                            month=int(datenaiss[5:7]),
                                            day=int(datenaiss[8:10]))
                datenaissFR = str(datenaiss[8:10]) + "/" + str(
                    datenaiss[5:7]) + "/" + str(datenaiss[:4])
                datedujour = datetime.date.today()
                age = (datedujour.year - datenaissDD.year) - int(
                    (datedujour.month, datedujour.day) < (
                    datenaissDD.month, datenaissDD.day))
                if dictInfos[IDindividu]["genre"] == "M":
                    txtDatenaiss = "Né le %s (%d ans)" % (datenaissFR, age)
                else:
                    txtDatenaiss = "Née le %s (%d ans)" % (datenaissFR, age)
            except:
                pass
        return txtDatenaiss

class GestCompo:
    def __init__(self, parent, IDfamille=None):
        self.parent = parent
        self.IDfamille = IDfamille
        self.IDindividu = None
        self.dIndividus = {}
        self.dictRattach = {}

        self.tip = SuperToolTip("ici le Supertooltip")
        self.tip.SetTarget(self)
        #self.tip.DoHideNow()
        self.tip.IDindividu = None

        # Bind possible, car GestCompo toujours associée à une window acceptant Bind
        self.Bind(wx.EVT_ENTER_WINDOW, self.OnEnterWindow)
        self.Bind(wx.EVT_MOTION, self.OnMotion)
        self.Bind(wx.EVT_LEAVE_WINDOW, self.OnLeaveWindow)


    # ----------- Fonctions tooltip --------------

    def ActiveTooltip(self,IDindividu=None):
        # Si on ne pointe pas un cadre individu
        if not IDindividu:
            return
        # Si l'individu pointé est celui du tip
        if IDindividu == self.tip.IDindividu and self.parent.ToolTip:
            return

        # Active le tooltip
        tipFrame = hasattr(self.parent, "tipFrame")
        timer = hasattr(self.parent, "timerTip")
        if not (tipFrame or timer):
            self.timerTip = wx.PyTimer(self.SetIntoTooltip)
            self.timerTip.Start(1000)
            self.tip.IDindividu = IDindividu


    def SetIntoTooltip(self):

        taillePhoto = 30
        font = self.GetFont()

        # Récupération des infos sur l'individu
        IDindividu = self.tip.IDindividu
        dIndividu = self.getVal.dictIndividus[IDindividu]

        cadreIndividu = self.dictCadres[IDindividu]["ctrl"]

        # Paramétrage du tooltip
        self.tip.SetHyperlinkFont(
            wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL,
                    False, 'Arial'))

        if dIndividu["genre"] == "F":
            # Couleur du toolTip version FILLE
            self.tip.SetTopGradientColour(wx.Colour(255, 255, 255))
            self.tip.SetMiddleGradientColour(wx.Colour(251, 229, 243))
            self.tip.SetBottomGradientColour(wx.Colour(255, 210, 226))
            self.tip.SetTextColor(wx.Colour(76, 76, 76))
        else:
            # Couleur du toolTip version GARCON
            self.tip.SetTopGradientColour(wx.Colour(255, 255, 255))
            self.tip.SetMiddleGradientColour(wx.Colour(242, 246, 251))
            self.tip.SetBottomGradientColour(wx.Colour(202, 218, 239))
            self.tip.SetTextColor(wx.Colour(76, 76, 76))

        qualite = wx.IMAGE_QUALITY_BICUBIC


        # Titre du tooltip
        nomImage = Civilites.GetDictCivilites()[self.getVal.dictIndividus[IDindividu]["IDcivilite"]]["nomImage"]
        if nomImage == None : nomImage = "Personne.png"
        nomFichier = Chemins.GetStaticPath("Images/128x128/%s" % nomImage)

        IDphoto, bmp = CTRL_Photo.GetPhoto(IDindividu=IDindividu, nomFichier=nomFichier, taillePhoto=(taillePhoto, taillePhoto), qualite=100)

        if self.Name == 'graphique':
            bmp = cadreIndividu.bmp

        if bmp != None:
            bmp = bmp.ConvertToImage()
            bmp = bmp.Rescale(width=taillePhoto, height=taillePhoto, quality=qualite)
            bmp = bmp.ConvertToBitmap()
            self.tip.SetHeaderBitmap(bmp)

        self.tip.SetHeaderFont(
            wx.Font(10, font.GetFamily(), font.GetStyle(), wx.BOLD, font.GetUnderlined(),
                    font.GetFaceName()))
        self.tip.SetHeader(dIndividu["nomComplet2"])


        self.tip.SetDrawHeaderLine(True)

        # Corps du tooltip
        message = ""

        if dIndividu["datenaissComplet"] != None: message += "%s\n" % \
                                                                    dIndividu[
                                                                        "datenaissComplet"]

        adresse = ""
        if dIndividu["adresse_ligne1"] not in (None, ""): adresse += "</b>%s\n" % \
                                                                            dIndividu[
                                                                                "adresse_ligne1"]
        if dIndividu["adresse_ligne2"] not in (None, ""): adresse += "</b>%s\n" % \
                                                                            dIndividu[
                                                                                "adresse_ligne2"]
        if len(adresse) > 3:
            message += "\n" + adresse

        coords = ""
        if dIndividu["tel_domicile_complet"] not in (None, ""): coords += "%s\n" % \
                                                                                 dIndividu[
                                                                                     "tel_domicile_complet"]
        if dIndividu["tel_mobile_complet"] not in (None, ""): coords += "%s\n" % \
                                                                               dIndividu[
                                                                                   "tel_mobile_complet"]
        if dIndividu["travail_tel_complet"] not in (None, ""): coords += "%s\n" % \
                                                                                dIndividu[
                                                                                    "travail_tel_complet"]
        if len(coords) > 3:
            message += "\n" + coords
        if dIndividu["mail_complet"] != None: message += "\n%s \n" % \
                                                                dIndividu[
                                                                    "mail_complet"]

        # Liste des inscriptions de l'individu
        if dIndividu["genre"] == "F":
            lettreGenre = "e"
        else:
            lettreGenre = ""
        if dIndividu["prenom"] != None:
            prenom = dIndividu["prenom"]
        else:
            prenom = ""
        if dIndividu["inscriptions"] == True:
            nbreInscriptions = len(dIndividu["listeInscriptions"])
            message += "\n"
            if nbreInscriptions == 1:
                message += "%s est inscrit%s à 1 activité : \n" % (prenom, lettreGenre)
            else:
                message += "%s est inscrit%s à %d activités : \n" % (
                prenom, lettreGenre, nbreInscriptions)
            for dictInscription in dIndividu["listeInscriptions"]:
                message += "> %s (%s - %s) \n" % (
                dictInscription["nomActivite"], dictInscription["nomGroupe"],
                dictInscription["nomCategorie"])

        self.tip.SetMessage(message)

        # Pied du tooltip
        self.tip.SetDrawFooterLine(True)
        self.tip.SetFooterBitmap(
            wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Ok_2.png"),
                      wx.BITMAP_TYPE_ANY))
        self.tip.SetFooterFont(
            wx.Font(7, font.GetFamily(), font.GetStyle(), wx.LIGHT, font.GetUnderlined(),
                    font.GetFaceName()))
        self.tip.SetFooter("Cliquez pour fermer")

        # Affichage du Frame tooltip
        self.parent.tipFrame = ToolTipWindow(self, self.tip)
        # self.parent.tipFrame.CalculateBestSize() # calcule incorrectement
        self.parent.tipFrame.SetSize((350, 300))
        x, y = wx.GetMousePosition()
        self.parent.tipFrame.SetPosition((x + 15, y + 17))
        self.parent.tipFrame.DropShadow(True)
        self.parent.tipFrame.Show()

        # Arrêt du timer
        self.timerTip.Stop()
        del self.timerTip

    def DesactiveTooltip(self):
        # Désactive le tooltip
        if hasattr(self, "timerTip"):
            if self.timerTip.IsRunning():
                self.timerTip.Stop()
                del self.timerTip
                self.tip.IDindividu = None
        else:
            pass
        self.CacheTooltip()

    def CacheTooltip(self):
        # Fermeture du tooltip
        if hasattr(self.parent, "tipFrame"):
            try:
                self.parent.tipFrame.Destroy()
            except:
                pass
            del self.parent.tipFrame

    def OnLeaveWindow(self, event):
        self.CacheTooltip()
        #event.Skip()

    def OnEnterWindow(self, event):
        self.tip.DoHideNow()
        pass

    # ------------- Autres fonctions ----------------------

    def OuvrirCalendrier(self, IDindividu=None):
        """ Ouverture du calendrier de l'individu """
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("consommations_conso",
                                                                  "consulter") == False: return
        self.parent.Sauvegarde()
        from Dlg import DLG_Grille
        dlg = DLG_Grille.Dialog(self, IDfamille=self.IDfamille,
                                selectionIndividus=[IDindividu, ])
        if dlg.ShowModal() == wx.ID_OK:
            self.MAJnotebook()
        try:
            dlg.Destroy()
        except:
            pass

    def CreateMenu(self,ctrlSelf):
        # Creation du pop menu clic Droit
        menu = wx.Menu()
        IDindividu = ctrlSelf.IDindividu_menu

        # Ajouter
        id = wx.Window.NewControlId()
        item = wx.MenuItem(menu, id, "Rattacher un individu")
        item.SetBitmap(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Ajouter.png"),
                                 wx.BITMAP_TYPE_PNG))
        menu.Append(item)
        ctrlSelf.Bind(wx.EVT_MENU, self.Rattacher_composition, id=id)

        if IDindividu != None:
            menu.AppendSeparator()

            # Modifier
            id = wx.Window.NewControlId()
            item = wx.MenuItem(menu, id, "Modifier")
            item.SetBitmap(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Modifier.png"),
                                     wx.BITMAP_TYPE_PNG))
            menu.Append(item)
            ctrlSelf.Bind(wx.EVT_MENU, self.Modifier_menu, id=id)

            # Détacher ou supprimer
            id = wx.Window.NewControlId()
            item = wx.MenuItem(menu, id, "Détacher ou supprimer")
            item.SetBitmap(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Supprimer.png"),
                                     wx.BITMAP_TYPE_PNG))
            menu.Append(item)
            ctrlSelf.Bind(wx.EVT_MENU, self.Supprimer_menu, id=id)

            menu.AppendSeparator()

            # Changer de catégorie
            sousMenuCategorie = wx.Menu()

            item = wx.MenuItem(sousMenuCategorie, 601, "Représentant",
                               kind=wx.ITEM_RADIO)
            sousMenuCategorie.Append(item)

            ctrlSelf.Bind(wx.EVT_MENU, self.Changer_categorie, id=601)
            if self.dictCadres[self.IDindividu_menu]["categorie"] == 1: item.Check(True)

            item = wx.MenuItem(sousMenuCategorie, 602, "Enfant", kind=wx.ITEM_RADIO)
            sousMenuCategorie.Append(item)
            ctrlSelf.Bind(wx.EVT_MENU, self.Changer_categorie, id=602)
            if self.dictCadres[self.IDindividu_menu]["categorie"] == 2: item.Check(True)

            item = wx.MenuItem(sousMenuCategorie, 603, "Contact", kind=wx.ITEM_RADIO)
            sousMenuCategorie.Append(item)
            ctrlSelf.Bind(wx.EVT_MENU, self.Changer_categorie, id=603)
            if self.dictCadres[self.IDindividu_menu]["categorie"] == 3: item.Check(True)

            menu.AppendSubMenu(sousMenuCategorie,"Changer de catégorie")

            # Définir comme titulaire
            if self.dictCadres[self.IDindividu_menu]["categorie"] == 1:
                id = wx.Window.NewControlId()
                item = wx.MenuItem(menu, id, "Définir comme titulaire",
                                   kind=wx.ITEM_CHECK)
                menu.Append(item)
                ctrlSelf.Bind(wx.EVT_MENU, self.On_SetTitulaire, id=id)
                if self.dictCadres[self.IDindividu_menu]["titulaire"] == 1:
                    item.Check(True)

            # Définir correspondant famille
            if self.dictCadres[self.IDindividu_menu]["categorie"] == 1:
                id = wx.Window.NewControlId()
                item = wx.MenuItem(menu, id, "Définir correspondant famille",
                                   kind=wx.ITEM_CHECK)
                menu.Append(item)
                ctrlSelf.Bind(wx.EVT_MENU, self.On_SetCorrespondant, id=id)
                if self.dictCadres[self.IDindividu_menu]["correspondant"] == 1:
                    item.Check(True)

        # Finalisation du menu
        ctrlSelf.PopupMenu(menu)
        menu.Destroy()
        self.IDindividu_menu = None

    def Modifier_menu(self, event):
        """ Modifier une fiche à partir du menu contextuel """
        IDindividu = self.IDindividu_menu
        self.Modifier(IDindividu)
        self.IDindividu_menu = None

    def SetDonnees(self, donnees):
        self.donnees = donnees # nom historique
        self.getVal = donnees # opérationnel dans ce module

    def Changer_categorie(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("individus_fiche",
                                                                  "modifier") == False: return
        IDcategorie = event.GetId() - 600
        IDrattachement = self.dictCadres[self.IDindividu_menu]["IDrattachement"]
        if self.dictCadres[self.IDindividu_menu]["categorie"] == 1:
            # risque d'incohérences avec titulaires et correspondants
            if self.dictCadres[self.IDindividu_menu]["titulaire"] == 1 or \
                    self.dictCadres[self.IDindividu_menu]["correspondant"]:
                mess = "Avant de changer la catégorie d'un titulaire ou d'un correspondant il faut désactiver ces fonctions"
                wx.MessageBox(mess, "Blocage")
                return
        if IDcategorie != self.dictCadres[self.IDindividu_menu]["categorie"]:
            dlg = wx.MessageDialog(None,
                                   "Souhaitez-vous vraiment modifier la catégorie de rattachement de cet individu ?",
                                   "Changement de catégorie",
                                   wx.YES_NO | wx.NO_DEFAULT | wx.CANCEL | wx.ICON_QUESTION)
            if dlg.ShowModal() == wx.ID_YES:
                DB = GestionDB.DB()
                DB.ReqMAJ("rattachements", [("IDcategorie", IDcategorie), ],
                          "IDrattachement", IDrattachement)
                DB.Close()
                MAJ(self)
            dlg.Destroy()

    def On_SetTitulaire(self, event):
        if self.dictCadres[self.IDindividu_menu]["titulaire"] == 1:
            # Recherche s'il restera au moins un titulaire dans cette famille
            nbreTitulaires = 0
            for IDindividu, dictCadre in self.dictCadres.items():
                if dictCadre["titulaire"] == 1:
                    nbreTitulaires += 1
            if nbreTitulaires == 1:
                dlg = wx.MessageDialog(self,
                                       "Vous devez avoir au moins un titulaire de dossier dans une famille !",
                                       "Erreur de saisie", wx.OK | wx.ICON_EXCLAMATION)
                dlg.ShowModal()
                dlg.Destroy()
                return
            etat = 0
            self.dictCadres[self.IDindividu_menu]["titulaire"] = 0
        else:
            etat = 1
            self.dictCadres[self.IDindividu_menu]["titulaire"] = 1
        DB = GestionDB.DB()
        req = "UPDATE rattachements SET titulaire=%d WHERE IDindividu=%d AND IDfamille=%d;" % (
        etat, self.IDindividu_menu, self.IDfamille)
        DB.ExecuterReq(req, MsgBox="ExecuterReq")
        DB.Commit()
        DB.Close()
        MAJ(self)

    def On_SetCorrespondant(self, event):
        if self.dictCadres[self.IDindividu_menu]["correspondant"]:
            # déjà le correspondant de cette famille
            mess = "Individu déjà correspondant de cette famille !\n"\
                   "pour changer choisissez un autre titulaire"
            dlg = wx.MessageDialog(self,
                       mess,
                       "Erreur de saisie", wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return

        if not self.dictCadres[self.IDindividu_menu]["titulaire"]:
            # Un correspondant doit être titulaire
            mess = "Individu non titulaire de cette famille ne peut être correspondant!\n" \
                   "pour changer choisissez un autre titulaire"
            dlg = wx.MessageDialog(self,
                                   mess,
                                   "Erreur de saisie", wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return

        # Récup de l'ancien correspondant
        exCorresp = None
        for IDindividu, dict in self.dictCadres.items():
            if dict["correspondant"]:
                exCorresp = IDindividu

        # Changement de correspondant de la famille
        designation = UTILS_SaisieAdresse.DesignationFamille(self.IDfamille,
                                                             partant=exCorresp)
        wx.MessageBox(
            "La nouvelle désignation pour la famille est '%s'\nVous pouvez la gérer dans les coordonnées d'un individu..." % designation)
        DB = GestionDB.DB()
        DB.ReqMAJ("familles", [('adresse_intitule', designation),
                               ('adresse_individu', self.IDindividu_menu)],
                  'IDfamille', self.IDfamille,
                  MsgBox="CTRL_Composition.On_SetCorrespondant")

        # Récup d'une adresse en propre à partir de son adresse auto
        if self.dictCadres[self.IDindividu_menu]["adresse_auto"]:
            exAdress = self.dictCadres[self.IDindividu_menu]["adresse_auto"]
            self.dictCadres[self.IDindividu_menu]["adresse_auto"] = None
            lstDonnees = [("adresse_auto", None), ]
            for item in ("rue_resid", "cp_resid", "ville_resid"):
                lstDonnees.append(
                    (item, self.getVal.dictInfosIndividus[exAdress][item]))
                self.dictCadres[self.IDindividu_menu][item] = \
                self.getVal.dictInfosIndividus[exAdress][item]
            DB.ReqMAJ("individus", lstDonnees, 'IDindividu', self.IDindividu_menu,
                      MsgBox="CTRL_Composition.On_SetCorrespondant2")

        # S'approprie les adresses auto de la famille pointant l'ancien correspondant
        if exCorresp:
            dictInfosIndividus = self.getVal.GetInfosIndividus()[1]
            for IDindividu, dictInfo in dictInfosIndividus.items():
                if dictInfo[
                    "adresse_auto"] == exCorresp and IDindividu != self.IDindividu_menu:
                    DB.ReqMAJ("individus", [("adresse_auto", self.IDindividu_menu), ],
                              'IDindividu', IDindividu,
                              MsgBox="CTRL_Composition.On_SetCorrespondant3 ID %d" % IDindividu)
                for item in ("rue_resid", "cp_resid", "ville_resid"):
                    self.dictCadres[self.IDindividu_menu][item] = \
                    dictInfosIndividus[self.IDindividu_menu][item]
        DB.Close()
        MAJ(self)

    def CreateIDindividu(self):
        """ Crée la fiche individu dans la base de données afin d'obtenir un IDindividu """
        DB = GestionDB.DB()
        date_creation = str(datetime.date.today())
        listeDonnees = [
            ("date_creation", date_creation),
            ("nom", self.dictRattach["nom"]),
            ("prenom", self.dictRattach["prenom"]),
            ]
        self.IDindividu = DB.ReqInsert("individus", listeDonnees)
        # Mémorise l'action dans l'historique
        nomPrenom = f"{self.dictRattach['prenom']} {self.dictRattach['nom']}"
        action = f"Création de l'individu {self.IDindividu}-{nomPrenom}"
        UTILS_Historique.InsertActions([{
                "IDindividu" : self.IDindividu,
                "IDcategorie" : 11,
                "action" : action
                },])
        DB.Close()
        return self.IDindividu

    def SetNewIndividu(self, dIndividu):
        self.parent.dIndividu = dIndividu

    def Rattacher_composition(self, event=None):
        if not UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("individus_fiche",
                                                                  "creer"):
            return

        # Appel de l'écran de rattachement
        from Dlg import DLG_Rattachement
        dlg = DLG_Rattachement.Dialog(None, IDfamille=self.IDfamille)
        if dlg.ShowModal() == wx.ID_OK:
            ok = True
        else:
            ok = False
        if not ok:
            dlg.Destroy()
            return
        # retour de rattachement
        tuplRattach = dlg.GetData()
        self.dictRattach = dlg.GetDictData()
        dlg.Destroy()
        mode, IDcategorie, titulaire, IDindividu, nom, prenom = tuplRattach
        self.IDindividu = IDindividu

        if mode == "creation":
            # Création d'un nouvel individu
            self.Ajouter_individu(self.dictRattach)
        else:
            # Rattachement d'un individu existant
            self.RattacherIndividu(IDindividu, IDcategorie, titulaire)
        # MAJ de l'affichage
        MAJ(self)
        return IDindividu

    def Ajouter_individu(self, dictRattach=None):
        # Rattacher un nouvel individu, dont l'identité est issue de DLG_Rattachement
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("individus_fiche",
                                                                  "creer") == False: return
        ok = True
        self.dictRattach = dictRattach
        if not dictRattach:
            # session de rattrapage
            from Dlg import DLG_Rattachement
            dlg = DLG_Rattachement.Dialog(None, IDfamille=self.IDfamille)
            if dlg.ShowModal() == wx.ID_OK:
                ok = True
                self.dictRattach = dlg.GetDictData()
            else:
                ok = False
            dlg.Destroy()
        if ok:
            if self.dictRattach['mode'] == "creation":
                # Création d'un nouvel individu rattaché
                IDindividu = self.CreateIDindividu()
                self.dictRattach['IDindividu'] = IDindividu
                self.RattacherIndividu(**self.dictRattach)
                # composition de l'individu
                dlg = DLG_Individu.Dialog(self, IDindividu=self.IDindividu,
                                          IDfamille = self.IDfamille,
                                          dictRattach=self.dictRattach)
                if dlg.ShowModal() != wx.ID_OK:
                    self.IDindividu = None
                    self.SupprimerFamille()
                dlg.Destroy()
            else:
                # Rattachement d'un individu existant
                args = [self.dictRattach[x] for x in ('IDindividu','IDcategorie','titulaire')]
                self.RattacherIndividu(*args)

            # MAJ de l'affichage
            MAJ(self)
            return self.IDindividu
        else:
            self.SupprimerFamille()
            return self.IDindividu

    def SupprimerFamille(self):
        # Supprime la fiche famille lorsqu'on annule le rattachement du premier titulaire
        DB = GestionDB.DB()
        req = """SELECT IDrattachement, IDfamille FROM rattachements 
        WHERE IDfamille=%d""" % self.IDfamille
        DB.ExecuterReq(req, MsgBox="ExecuterReq")
        listeDonnees = DB.ResultatReq()
        DB.Close()
        if len(listeDonnees) == 0:
            self.GetParent().SupprimerFicheFamille()

    def RattacherIndividu(self, IDindividu=None, IDcategorie=None, titulaire=0,**kwd):
        if not IDindividu or not self.IDfamille:
            return False
        # Saisie dans la base d'un rattachement
        DB = GestionDB.DB()
        listeDonnees = [
            ("IDindividu", IDindividu),
            ("IDfamille", self.IDfamille),
            ("IDcategorie", IDcategorie),
            ("titulaire", titulaire),
        ]
        ID = DB.ReqInsert("rattachements", listeDonnees)
        if self.dictRattach:
            self.dictRattach['IDrattachement'] = ID
            self.dictRattach['IDfamille'] = self.IDfamille
        # Mémorise l'action dans l'historique
        labelCategorie = "???"
        if IDcategorie == 1: labelCategorie = "représentant"
        if IDcategorie == 2: labelCategorie = "enfant"
        if IDcategorie == 3: labelCategorie = "contact"

        action = "Rattachement de l'individu %d à la famille %d en tant que %s"%(
                      IDindividu, self.IDfamille, labelCategorie)

        UTILS_Historique.InsertActions([{
            "IDindividu": self.IDindividu,
            "IDfamille": self.IDfamille,
            "IDcategorie": 13,
            "action": action,
        }, ], DB)
        DB.Close()
        return True

    def Supprimer_menu(self, event):
        IDindividu = self.IDindividu_menu
        self.Supprimer(IDindividu)
        self.IDindividu_menu = None

    def zzzModifier_selection(self, event=None):
        """ Modifier une fiche à partir du bouton Modifier """
        IDindividu = self.selectionCadre
        self.selectionCadre = None
        if IDindividu == None:
            dlg = wx.MessageDialog(self,
                                   "Vous devez d'abord sélectionner un individu dans le cadre Composition !",
                                   "Erreur de saisie", wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        else:
            self.Modifier(IDindividu)

    def zzzSupprimer_selection(self, event=None):
        """ Supprimer ou detacher """
        IDindividu = self.selectionCadre
        self.selectionCadre = None
        if IDindividu == None:
            dlg = wx.MessageDialog(self,
                                   "Vous devez d'abord sélectionner un individu dans le cadre Composition !",
                                   "Erreur de saisie", wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        else:
            self.Supprimer(IDindividu)

    def Modifier(self, IDindividu=None):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("individus_fiche",
                                                                  "modifier") == False: return
        dlg = DLG_Individu.Dialog(None, IDindividu=IDindividu, IDfamille=self.IDfamille)
        ret = dlg.ShowModal()
        if ret != wx.ID_OK:
            return
        # dlg.Destroy()
        MAJ(self)

    def Supprimer(self, IDindividu=None):
        """ Supprimer un individu """
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("individus_fiche",
                                                                  "modifier") == False: return
        from Dlg import DLG_Supprimer_fiche
        dlg = DLG_Supprimer_fiche.Dialog(self, IDindividu=IDindividu,
                                         IDfamille=self.IDfamille)
        reponse = dlg.ShowModal()
        dlg.Destroy()

        # MAJ de la fiche famille
        if reponse:
            # MAJ de l'affichage
            MAJ(self)

    def MAJ_common(self):
        # Mise à jour non spécifiques au mode Visu
        getVal = GetValeurs(self.IDfamille)
        self.getVal = getVal
        self.dictCadres = getVal.GetDictCadres()
        self.dictInfoBulles = getVal.GetDictInfoBulles()
        self.dictLiensCadres = getVal.GetLiensCadres()

    def MAJnotebook(self):
        """ MAJ la page active du notebook de la fenêtre famille """
        self.parent.MAJpageActive()

class ToolTipGC():
    # SuperClass ajoutant un SuperToolTip
    def __init__(self, name="tiptool",message=""):
        if not message:
            message = f"Message de {name}-Extension\n\n Me voici, je suis {name}!!!\n"
        self.tooltip = SuperToolTip(message)
        self.tooltip.SetTarget(self)
        self.Bind(wx.EVT_ENTER_WINDOW, self.OnEnterWindow)
        self.Bind(wx.EVT_LEAVE_WINDOW, self.OnLeaveWindow)

    def OnEnterWindow(self, event):
        self.tooltip.Show()
        event.Skip()

    def OnLeaveWindow(self, event):
        if self.tooltip:
            self.tooltip.DoHideNow()
        event.Skip()


# ----------- Tutos de SuperToolTip sur Bouton, DCgraphique, HyperTreeList ------------

class PanelCadre(wx.Panel,ToolTipGC):
    def __init__(self, parent,name="PanelCadre"):
        wx.Panel.__init__(self,parent,name=name,size=(200,80))
        ToolTipGC.__init__(self,name=name)
        self.parent = parent

        # Création du PseudoDC
        self.pdc = wx.adv.PseudoDC()

        # Dessin de quelques objets graphiques
        self.draw_objects()

        # Événement de dessin
        self.Bind(wx.EVT_PAINT, self.on_paint)

    # Création du graphique
    def draw_objects(self):

        # Cercle
        self.pdc.SetId(2)
        self.pdc.SetPen(wx.Pen("red", 2))
        self.pdc.SetBrush(wx.Brush("pink"))
        self.pdc.DrawCircle(100, 70, 40)

        # Texte
        self.pdc.SetId(4)
        font = wx.Font(12, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL,
                       wx.FONTWEIGHT_BOLD)
        self.pdc.SetFont(font)
        self.pdc.DrawText("Venez dans le cadre", 10, 10)

        # Rectangle
        self.pdc.SetId(1)
        self.pdc.SetPen(wx.Pen("black", 2))
        self.pdc.SetBrush(wx.Brush("light blue"))
        self.pdc.DrawRectangle(50, 50, 120, 10)

        # Ligne
        self.pdc.SetId(3)
        self.pdc.SetPen(wx.Pen("green", 3))
        self.pdc.DrawLine(190, 30, 100, 70)


    # dépose le graphique dans home fenêtre
    def on_paint(self, event):
        dc = wx.PaintDC(self)
        self.pdc.DrawToDC(dc)

class Button(wx.Button, ToolTipGC):
    def __init__(self,parent,name="bouton",label="Approchez la souris sur les objets",
                 size=(150,40)):
        wx.Button.__init__(self,parent,id=1,label=label,size=size)
        ToolTipGC.__init__(self,name=name)

class PanelHyperTree(wx.Panel):
    def __init__(self,parent):
        super().__init__(parent, name="HyperTreeList", size=(200,150))

        self.tree = self.ComposeHyperTree()
        self.tree.ExpandAll()

        # Tooltip
        self.tipHTL = SuperToolTip(" supertooltip de PanelHyperTree")
        self.tipHTL.SetTarget(self.tree)
        self.tipHTL.SetEndDelay(5)

        self.lastItem = None

        self.tree.Bind(wx.EVT_MOTION, self.OnMotionTree)
        self.tree.Bind(wx.EVT_LEAVE_WINDOW, self.OnLeaveTree)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.tree, 1, wx.EXPAND)
        self.SetSizer(sizer)

    # ----Fonctions de l'HyperTree ----------------------------------------

    def ComposeHyperTree(self):
        style = (
                wx.TR_HAS_BUTTONS |
                wx.TR_FULL_ROW_HIGHLIGHT |
                TR_COLUMN_LINES |
                TR_ROW_LINES
        )

        tree = HyperTreeList(self, style=style)

        tree.AddColumn("Nom")
        tree.SetMainColumn(0)

        # Construction de l'arbre
        root = tree.AddRoot("Familles")

        fam1 = tree.AppendItem(root, "Famille Dupont")
        bob = tree.AppendItem(fam1, "Bob")
        tree.AppendItem(bob, "Adresse")
        tree.AppendItem(bob, "Téléphone")

        fam2 = tree.AppendItem(root, "Famille Martin")
        paul = tree.AppendItem(fam2, "Paul")
        tree.AppendItem(paul, "Adresse")
        return tree

    def GetRoot(self, item):

        parent = self.tree.GetItemParent(item)

        while parent and parent.IsOk():
            item = parent
            parent = self.tree.GetItemParent(item)

        return item

    def GetItemPath(self, item):
        """Construit le chemin complet d'un item"""

        path = []

        while item and item.IsOk():

            text = self.tree.GetItemText(item)

            if text:
                path.append(text)

            item = self.tree.GetItemParent(item)

        path.reverse()

        return " → ".join(path)

    def OnMotionTree(self, event):

        pos = event.GetPosition()

        item, flags, col = self.tree.HitTest(pos)
        # Problème réponse GPT
        """Comportement connu: HitTest() ne renvoie un item que si la position de la souris 
        tombe exactement sur la zone de l’item, pas forcément sur toute la ligne. 
        Avec FULL_ROW_HIGHLIGHT, la ligne est visuellement sélectionnée, 
        mais la zone sensible reste petite."""

        if item:
            mess = f"item {item.IsOk}"
        else:
            mess = "no item"
        if not item:
            pass

        if item:
            self.lastItem = item

            if item and item.IsOk():

                root = self.GetRoot(item)

                root_text = self.tree.GetItemText(root)

                path = self.GetItemPath(item)

                message = f"{root_text} \n {path}"
                self.tipHTL.SetMessage(message)
                self.tipHTL.Show()

            else:
                self.tipHTL.DoHideNow()

        event.Skip()

    def OnLeaveTree(self, event):
        self.lastItem = None
        self.tipHTL.DoHideNow()

        event.Skip()

    # ---- Fonctions pour boutons -----------------------------------------
    def GetBouton(self,name):
        btn = wx.Button(self.panel, label= f"Passe la souris / {name}")
        btn.name = name
        self.tipBTN = SuperToolTip(f"tipBTN message de {name}\n\n")
        self.tipBTN.SetTarget(btn)

        btn.Bind(wx.EVT_ENTER_WINDOW, self.on_enterBTN)
        btn.Bind(wx.EVT_LEAVE_WINDOW, self.on_leaveBTN)
        return btn

    def on_enterBTN(self, event):
        self.tipBTN.Show()
        event.Skip()

    def on_leaveBTN(self, event):
        if self.tipBTN:
            self.tipBTN.DoHideNow()
        event.Skip()

# -------------- Lanceur test et tutos  -------------------------------------

KWCADRE = {'IDindividu': 18912,
           'listeTextes': [ ('AFOCAL ALSACE LORRAINE -', 8, 'bold'),
                            ('#SPACER#', 1, 'normal'),
                            ('37 RUE DU GÉNÉRAL LE BOCQ', 7, 'light'),
                            ('67270 HOCHFELDEN\n', 7, 'light'),
                            ('#SPACER#', 1, 'normal'),
                            ('Tél. domicile : 03 88 91 70 04', 7, 'light')],
           'genre': '', 'photo': None,
           'xCentre': -260.0, 'yCentre': -4.728624535315987,
           'largeur': 210, 'hauteur': 28,
           'numCol': 1, 'titulaire': 1, 'correspondant': False, 'calendrierActif': True} # paramètres pour un cadre individu dans CTRLComposition

class FrameTest(wx.Frame):
    def __init__(self):
        super().__init__(None, title="GestionComposition.FrameTest",size=(500,800))
        panel = wx.Panel(self, -1, name='panel_test')

        panelCadre = PanelCadre(panel)
        panelCadre.SetBackgroundColour((235, 255, 235))

        panelHTL = PanelHyperTree(panel)

        btn = Button(panel,name="btn_panel",size=(200,50))

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(panelCadre, 1, wx.ALL|wx.ALIGN_CENTER, 20)
        sizer.Add(panelHTL, 0, wx.ALL, 10)
        sizer.Add(btn, 0, wx.ALL|wx.ALIGN_CENTER, 40)
        sizer.Add((10,10),1,wx.EXPAND)
        panel.SetSizer(sizer)
        self.CentreOnScreen()

if __name__ == "__main__":
    app = wx.App()
    frame = FrameTest()
    #frame = FrameTutos()
    frame.Show()
    app.MainLoop()