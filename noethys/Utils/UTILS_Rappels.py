#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, Matthania données sur selection IDfamilles
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS, JB
# Copyright:       (c) 2010-13 Ivan LUCAS, JB
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------


from Utils.UTILS_Traduction import _
import Chemins
import wx
import datetime
import decimal
import sys
import traceback
import wx.lib.agw.pybusyinfo as PBI
from Utils import UTILS_Config
from Data import DATA_Civilites as Civilites
import GestionDB
from Utils import UTILS_Titulaires
from Utils import UTILS_Infos_individus
from Utils import UTILS_Impression_rappel
from Utils import UTILS_Dates
from Dlg import DLG_Apercu_rappel
from Utils import UTILS_Conversion
from Dlg.DLG_Saisie_texte_rappel import MOTSCLES

DICT_CIVILITES = Civilites.GetDictCivilites()

SYMBOLE = UTILS_Config.GetParametre("monnaie_symbole", "€")
MONNAIE_SINGULIER = UTILS_Config.GetParametre("monnaie_singulier", _("Euro"))
MONNAIE_DIVISION = UTILS_Config.GetParametre("monnaie_division", _("Centime"))

def Nz(valeur):
    if valeur == None:
        valeur = 0
    valeur = float(valeur)
    return valeur

class Facturation():
    def __init__(self,lstIDfamilles=[]):
        """ Récupération de toutes les données de base """
        self.lstIDfamilles = lstIDfamilles
        DB = GestionDB.DB()
            
        # Récupération des infos sur l'organisme
        req = """SELECT nom, rue, cp, ville, tel, fax, mail, site, num_agrement, num_siret, code_ape
        FROM organisateur
        WHERE IDorganisateur=1;""" 
        DB.ExecuterReq(req,MsgBox="ExecuterReq")
        listeDonnees = DB.ResultatReq()      
        self.dictOrganisme = {}
        for nom, rue, cp, ville, tel, fax, mail, site, num_agrement, num_siret, code_ape in listeDonnees :
            self.dictOrganisme["nom"] = nom
            self.dictOrganisme["rue"] = rue
            self.dictOrganisme["cp"] = cp
            if ville != None : ville = ville.capitalize()
            self.dictOrganisme["ville"] = ville
            self.dictOrganisme["tel"] = tel
            self.dictOrganisme["fax"] = fax
            self.dictOrganisme["mail"] = mail
            self.dictOrganisme["site"] = site
            self.dictOrganisme["num_agrement"] = num_agrement
            self.dictOrganisme["num_siret"] = num_siret
            self.dictOrganisme["code_ape"] = code_ape


        # Récupération des textes de rappels
        req = """SELECT IDtexte, titre, texte_pdf
        FROM textes_rappels;""" 
        DB.ExecuterReq(req,MsgBox="ExecuterReq")
        listeDonnees = DB.ResultatReq()      
        self.dictTextesRappels = {}
        for IDtexte, titre, texte_pdf in listeDonnees :
            self.dictTextesRappels[IDtexte] = {"titre" : titre, "texte_pdf" : texte_pdf}

        DB.Close() 

        # Get noms Titulaires
        self.dictTitulaires = UTILS_Titulaires.GetTitulaires(listeIDfamille=lstIDfamilles)

        # Récupération des infos de base familles
        self.infosIndividus = UTILS_Infos_individus.Informations(lstIDfamilles=lstIDfamilles)

    def Supprime_accent(self, texte):
        liste = [ ("é", "e"), ("è", "e"), ("ê", "e"), ("ë", "e"), ("à", "a"), ("û", "u"), ("ô", "o"), ("ç", "c"), ("î", "i"), ("ï", "i"),]
        for a, b in liste :
            texte = texte.replace(a, b)
            texte = texte.replace(a.upper(), b.upper())
        return texte

    def EcritStatusbar(self, texte=""):
        try :
            topWindow = wx.GetApp().GetTopWindow() 
            topWindow.SetStatusText(texte)
        except : 
            pass

    def GetDonnees(self, listeIDfamilles=[], date_reference=None, date_edition=None):
        """ Recherche des rappels à créer """
        DB = GestionDB.DB()
        if listeIDfamilles == None : listeIDfamilles = []
        if len(listeIDfamilles) == 0:
            condition = ""
        elif listeIDfamilles == 1:
            condition = "WHERE prestations.IDcompte_payeur = %d" % listeIDfamilles[0]
        else:
            condition = "WHERE prestations.IDcompte_payeur IN (%s)" % str(listeIDfamilles)[1:-1]

        # Recherche des prestations par payeur
        req = """SELECT prestations.IDcompte_payeur, prestations.IDprestation, prestations.date, prestations.montant, Sum(ventilation.montant) as reglements
                FROM prestations
                LEFT JOIN ventilation ON prestations.IDprestation = ventilation.IDprestation
                %s
                GROUP BY prestations.IDcompte_payeur, prestations.IDprestation
                ;""" % condition
        DB.ExecuterReq(req,MsgBox = ("UTILS_Rappels.GetDonnees"))
        recordset = DB.ResultatReq()

        dictPrestations = {}
        for IDcompte_payeur, IDprestation, date, mttPrestation, mttReglements in recordset:
            if IDcompte_payeur in dictPrestations:
                dictPrestations[IDcompte_payeur]["prestations"] += Nz(mttPrestation)
                if Nz(mttPrestation) > Nz(mttReglements):
                    if date < dictPrestations[IDcompte_payeur]["date_min"]:
                        dictPrestations[IDcompte_payeur]["date_min"] = date
                    if date > dictPrestations[IDcompte_payeur]["date_max"]:
                        dictPrestations[IDcompte_payeur]["date_max"] = date
            else:
                dictPrestations[IDcompte_payeur] = {}
                dictPrestations[IDcompte_payeur]["prestations"] = Nz(mttPrestation)
                dictPrestations[IDcompte_payeur]["date_min"] = "20991231"
                dictPrestations[IDcompte_payeur]["date_max"] = "19000101"
                if Nz(mttPrestation) > Nz(mttReglements):
                    dictPrestations[IDcompte_payeur]["date_min"] = date
                    dictPrestations[IDcompte_payeur]["date_max"] = date

        # Récupération des règlements
        if len(listeIDfamilles) == 0:
            condition = ""
        elif listeIDfamilles == 1:
            condition = "WHERE reglements.IDcompte_payeur = %d" % listeIDfamilles[0]
        else:
            condition = "WHERE reglements.IDcompte_payeur IN (%s)" % str(listeIDfamilles)[1:-1]

        req = """SELECT reglements.IDcompte_payeur, SUM(reglements.montant)
                FROM reglements
                %s
                GROUP BY reglements.IDcompte_payeur
                ;""" % condition
        DB.ExecuterReq(req,MsgBox="ExecuterReq")
        listeReglement = DB.ResultatReq()
        dictReglement = {}
        for IDcompte_payeur, totalReglement in listeReglement :
            dictReglement[IDcompte_payeur] = float(totalReglement)
        DB.Close() 

        # constitution des comptes à relancer
        dictComptes = {}
        for IDcompte_payeur in listeIDfamilles :
            montant = 0.0
            if IDcompte_payeur in dictPrestations:
                montant = Nz(dictPrestations[IDcompte_payeur]["prestations"])
                date_min = dictPrestations[IDcompte_payeur]["date_min"]
                date_max = dictPrestations[IDcompte_payeur]["date_max"]
            montant_reglement = 0.0
            if IDcompte_payeur in dictReglement:
                montant_reglement = Nz(dictReglement[IDcompte_payeur])

            # conversion en decimal
            montant = decimal.Decimal(str(montant))
            montant_reglement = decimal.Decimal(str(montant_reglement))
            solde = montant_reglement - montant
            numero = 0

            if solde < decimal.Decimal("0.0") :
                dictComptes[IDcompte_payeur] = {
                    "IDfamille" : IDcompte_payeur,
                    "{IDFAMILLE}" : IDcompte_payeur,
                    "num_rappel" : numero,
                    "{NUM_RAPPEL}" : "%06d" % numero,
                    "{NOM_LOT}" : "",
                    "solde_num" : -solde,
                    "solde" : "%.02f %s" % (-solde, SYMBOLE),
                    "{SOLDE}" : "%.02f %s" % (-solde, SYMBOLE),
                    "solde_lettres" : UTILS_Conversion.trad(-solde, MONNAIE_SINGULIER, MONNAIE_DIVISION),
                    "{SOLDE_LETTRES}" : UTILS_Conversion.trad(-solde, MONNAIE_SINGULIER, MONNAIE_DIVISION),
                    "select" : True,
                    "num_codeBarre" :  "%07d" % numero,
                    "numero" : _("Rappel n°%07d") % numero,
                    "{CODEBARRES_NUM_RAPPEL}" : "F%06d" % numero,
                    "date_min" : UTILS_Dates.DateEngEnDateDD(date_min),
                    "date_max" : UTILS_Dates.DateEngEnDateDD(date_max),
                    "{DATE_MIN}" : UTILS_Dates.DateEngEnDateDD(date_min),
                    "{DATE_MAX}" : UTILS_Dates.DateEngEnDateDD(date_max),
                    "{DATE_EDITION_LONG}" : UTILS_Dates.DateComplete(date_edition),
                    "{DATE_EDITION_COURT}" : UTILS_Dates.DateEngFr(str(date_edition)),

                    "{ORGANISATEUR_NOM}" : self.dictOrganisme["nom"],
                    "{ORGANISATEUR_RUE}" : self.dictOrganisme["rue"],
                    "{ORGANISATEUR_CP}" : self.dictOrganisme["cp"],
                    "{ORGANISATEUR_VILLE}" : self.dictOrganisme["ville"],
                    "{ORGANISATEUR_TEL}" : self.dictOrganisme["tel"],
                    "{ORGANISATEUR_FAX}" : self.dictOrganisme["fax"],
                    "{ORGANISATEUR_MAIL}" : self.dictOrganisme["mail"],
                    "{ORGANISATEUR_SITE}" : self.dictOrganisme["site"],
                    "{ORGANISATEUR_AGREMENT}" : self.dictOrganisme["num_agrement"],
                    "{ORGANISATEUR_SIRET}" : self.dictOrganisme["num_siret"],
                    "{ORGANISATEUR_APE}" : self.dictOrganisme["code_ape"],
                    }
        # Get noms Titulaires
        self.dictTitulaires = UTILS_Titulaires.GetTitulaires(listeIDfamille=listeIDfamilles)

        # Récupération des questionnaires
        #self.Questionnaires = UTILS_Questionnaires.ChampsEtReponses(type="famille")

        # Analyse et regroupement des données
        for IDfamille in list(dictComptes.keys()) :
            if IDfamille in self.dictTitulaires:
                dictTemp= {
                    "{FAMILLE_NOM}" :  self.dictTitulaires[IDfamille]["titulairesAvecCivilite"],
                    "nomSansCivilite" :  self.dictTitulaires[IDfamille]["titulairesSansCivilite"],
                    "{FAMILLE_RUE}" : self.dictTitulaires[IDfamille]["adresse"]["rue"],
                    "{FAMILLE_CP}" : self.dictTitulaires[IDfamille]["adresse"]["cp"],
                    "{FAMILLE_VILLE}" : self.dictTitulaires[IDfamille]["adresse"]["ville"],
                    }
            else:
                dictTemp= {
                    "{FAMILLE_NOM}" :  "Titulaire inconnu",
                    "nomSansCivilite" :  "",
                    "{FAMILLE_RUE}" : "",
                    "{FAMILLE_CP}" : "",
                    "{FAMILLE_VILLE}" : "",
                    }
            for key in list(dictTemp.keys()):
                dictComptes[IDfamille][key] = dictTemp[key]

        return dictComptes

    def GetDonneesImpression(self, lstIDfamilles=[]):
        if len(lstIDfamilles) == 0:
            lstIDfamilles = self.lstIDfamilles
        """ Impression des factures """
        #dlgAttente = PBI.PyBusyInfo(_("Recherche des données de facturation..."), parent=None, title=_("Veuillez patienter..."), icon=wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Logo.png"), wx.BITMAP_TYPE_ANY))
        #wx.Yield()
        
        # Récupère les données de la facture
        if len(lstIDfamilles) == 0 : conditions = "()"
        elif len(lstIDfamilles) == 1 : conditions = "(%d)" % lstIDfamilles[0]
        else : conditions = str(tuple(lstIDfamilles))

        DB = GestionDB.DB()
        req = """
        SELECT 
        rappels.IDrappel, rappels.numero, rappels.IDcompte_payeur, 
        rappels.date_edition, rappels.activites, rappels.IDutilisateur,
        rappels.IDtexte, rappels.date_reference, rappels.solde,
        rappels.date_min, rappels.date_max, rappels.prestations,
        comptes_payeurs.IDfamille, lots_rappels.nom
        FROM rappels
        LEFT JOIN comptes_payeurs ON comptes_payeurs.IDcompte_payeur = rappels.IDcompte_payeur
        LEFT JOIN lots_rappels ON lots_rappels.IDlot = rappels.IDlot
        WHERE rappels.IDcompte_payeur IN %s
        GROUP BY rappels.IDrappel
        ORDER BY rappels.date_edition
        ;""" % conditions
        DB.ExecuterReq(req,MsgBox="ExecuterReq")
        listeDonnees = DB.ResultatReq()     
        DB.Close() 
        if len(listeDonnees) == 0 : 
            #del dlgAttente
            return False
        
        # Création des dictRappels
        dictRappels = {}
        dictChampsFusion = {}
        for IDrappel, numero, IDcompte_payeur, date_edition, activites, IDutilisateur, IDtexte, date_reference, \
            solde, date_min, date_max, prestations, IDfamille, nomLot in listeDonnees :

            if numero == None : numero = 0
            date_edition = UTILS_Dates.DateEngEnDateDD(date_edition) 
            date_reference = UTILS_Dates.DateEngEnDateDD(date_reference)    
            
            if nomLot == None :
                nomLot = ""   
            
            dictRappel = {
                "{FAMILLE_NOM}" :  self.dictTitulaires[IDfamille]["titulairesAvecCivilite"],
                "nomSansCivilite" :  self.dictTitulaires[IDfamille]["titulairesSansCivilite"],
                "IDfamille" : IDfamille,
                "{IDFAMILLE}" : IDfamille,
                "{FAMILLE_RUE}" : self.dictTitulaires[IDfamille]["adresse"]["rue"],
                "{FAMILLE_CP}" : self.dictTitulaires[IDfamille]["adresse"]["cp"],
                "{FAMILLE_VILLE}" : self.dictTitulaires[IDfamille]["adresse"]["ville"],
                "num_rappel" : numero,
                "{NUM_RAPPEL}" : "%06d" % numero,
                "{NOM_LOT}" : nomLot,
                "solde_num" : -solde,
                "solde" : "%.02f %s" % (solde, SYMBOLE),
                "{SOLDE}" : "%.02f %s" % (-solde, SYMBOLE),
                "solde_lettres" : UTILS_Conversion.trad(solde, MONNAIE_SINGULIER, MONNAIE_DIVISION),
                "{SOLDE_LETTRES}" : UTILS_Conversion.trad(-solde, MONNAIE_SINGULIER, MONNAIE_DIVISION),
                "select" : True,
                "num_codeBarre" :  "%07d" % numero,
                "numero" : _("Rappel n°%07d") % numero,
                "{CODEBARRES_NUM_RAPPEL}" : "F%06d" % numero,

                "date_min" : date_min,
                "date_max" : date_max,
                "{DATE_MIN}" : date_min,
                "{DATE_MAX}" : date_max,

                "{DATE_EDITION_LONG}" : UTILS_Dates.DateComplete(date_edition),
                "{DATE_EDITION_COURT}" : UTILS_Dates.DateEngFr(str(date_edition)),
                
                "{ORGANISATEUR_NOM}" : self.dictOrganisme["nom"],
                "{ORGANISATEUR_RUE}" : self.dictOrganisme["rue"],
                "{ORGANISATEUR_CP}" : self.dictOrganisme["cp"],
                "{ORGANISATEUR_VILLE}" : self.dictOrganisme["ville"],
                "{ORGANISATEUR_TEL}" : self.dictOrganisme["tel"],
                "{ORGANISATEUR_FAX}" : self.dictOrganisme["fax"],
                "{ORGANISATEUR_MAIL}" : self.dictOrganisme["mail"],
                "{ORGANISATEUR_SITE}" : self.dictOrganisme["site"],
                "{ORGANISATEUR_AGREMENT}" : self.dictOrganisme["num_agrement"],
                "{ORGANISATEUR_SIRET}" : self.dictOrganisme["num_siret"],
                "{ORGANISATEUR_APE}" : self.dictOrganisme["code_ape"],
                
                "titre" : self.dictTextesRappels[IDtexte]["titre"],
                "IDtexte" : IDtexte,
                }

            dictRappel["texte"] = self.Fusion(IDtexte, dictRappel)

            # Ajout les données de base familles
            dictRappel.update(self.infosIndividus.GetDictValeurs(mode="famille", ID=IDfamille, formatChamp=True))

            """
            # Ajoute les réponses des questionnaires
            for dictReponse in self.Questionnaires.GetDonnees(IDfamille) :
                dictRappel[dictReponse["champ"]] = dictReponse["reponse"]
                if dictReponse["controle"] == "codebarres" :
                    dictRappel["{CODEBARRES_QUESTION_%d}" % dictReponse["IDquestion"]] = dictReponse["reponse"]
            """
            dictRappels[IDrappel] = dictRappel
            
            # Champs de fusion pour Email
            dictChampsFusion[IDrappel] = {}
            dictChampsFusion[IDrappel]["{NUMERO_RAPPEL}"] = dictRappel["{NUM_RAPPEL}"]
            dictChampsFusion[IDrappel]["{DATE_MIN}"] = UTILS_Dates.DateEngFr(str(date_min))
            dictChampsFusion[IDrappel]["{DATE_MAX}"] = UTILS_Dates.DateEngFr(str(date_max))
            dictChampsFusion[IDrappel]["{DATE_EDITION_RAPPEL}"] = UTILS_Dates.DateEngFr(str(date_edition))
            dictChampsFusion[IDrappel]["{DATE_REFERENCE}"] = UTILS_Dates.DateEngFr(str(date_reference))
            dictChampsFusion[IDrappel]["{SOLDE_CHIFFRES}"] = dictRappel["solde"]
            dictChampsFusion[IDrappel]["{SOLDE_LETTRES}"] = dictRappel["{SOLDE_LETTRES}"]
        
        #del dlgAttente
        return dictRappels, dictChampsFusion

    def Fusion(self, IDtexte=None, dictRappel={}):
        # Fusion du texte avec les champs
        texte = self.dictTextesRappels[IDtexte]["texte_pdf"]
        for motCle, code in MOTSCLES :
            valeur = dictRappel[code]
            if type(valeur) == int : valeur = str(valeur)
            if type(valeur) == float : 
                if valeur < 0 : valeur = -valeur
                valeur = str(valeur)
            if type(valeur) == datetime.date : valeur = UTILS_Dates.DateEngFr(str(valeur))
            if valeur == None : valeur = ""
            texte = texte.replace(motCle, valeur)
        return texte

    def Impression(self, nomDoc=None, afficherDoc=True, dictOptions=None, repertoire=None,
                   repertoireTemp=False):
        """ Impression des factures """
        # Récupération des données à partir des IDrappel
        resultat = self.GetDonneesImpression(self.lstIDfamilles)
        if resultat == False :
            return False
        dictRappels, dictChampsFusion = resultat
        
        # Récupération des paramètres d'affichage
        if dictOptions == None :
            if afficherDoc == False :
                dlg = DLG_Apercu_rappel.Dialog(None, titre=_("Sélection des paramètres de la lettre de rappel"), intro=_("Sélectionnez ici les paramètres d'affichage du rappel à envoyer par Email."))
                dlg.bouton_ok.SetImageEtTexte("Images/32x32/Valider.png", _("Ok"))
            else :
                dlg = DLG_Apercu_rappel.Dialog(None)
            if dlg.ShowModal() == wx.ID_OK:
                dictOptions = dlg.GetParametres()
                dlg.Destroy()
            else :
                dlg.Destroy()
                return False

        # Création des PDF à l'unité
        def CreationPDFeclates(repertoireCible=""):
            dictPieces = {}
            dlgAttente = PBI.PyBusyInfo(_("Génération des lettres de rappel à l'unité au format PDF..."), parent=None, title=_("Veuillez patienter..."), icon=wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Logo.png"), wx.BITMAP_TYPE_ANY))
            wx.Yield() 
            try :
                index = 0
                for IDrappel, dictRappel in dictRappels.items() :
                    if dictRappel["select"] == True :
                        num_rappel = dictRappel["num_rappel"]
                        nomTitulaires = self.Supprime_accent(dictRappel["nomSansCivilite"])
                        nomFichier = _("Lettre de rappel %d - %s") % (num_rappel, nomTitulaires)
                        cheminFichier = "%s/%s.pdf" % (repertoireCible, nomFichier)
                        dictComptesTemp = {IDrappel : dictRappel}
                        self.EcritStatusbar(_("Edition de la lettre de rappel %d/%d : %s") % (index, len(dictRappel), nomFichier))
                        UTILS_Impression_rappel.Impression(dictComptesTemp, dictOptions, IDmodele=dictOptions["IDmodele"], ouverture=False, nomFichier=cheminFichier)
                        dictPieces[IDrappel] = cheminFichier
                        index += 1
                self.EcritStatusbar("")
                del dlgAttente
                return dictPieces
            except Exception as err:
                del dlgAttente
                traceback.print_exc(file=sys.stdout)
                dlg = wx.MessageDialog(None, _("Désolé, le problème suivant a été rencontré dans l'édition des lettres de rappel : \n\n%s") % err, _("Erreur"), wx.OK | wx.ICON_ERROR)
                dlg.ShowModal()
                dlg.Destroy()
                return False
        
        # Répertoire souhaité par l'utilisateur
        if repertoire != None :
            resultat = CreationPDFeclates(repertoire)
            if resultat == False :
                return False

        # Répertoire TEMP (pour Emails)
        dictPieces = {}
        if repertoireTemp == True :
            dictPieces = CreationPDFeclates("Temp")
            if dictPieces == False :
                return False

        # Fabrication du PDF global
        if repertoireTemp == False :
            dlgAttente = PBI.PyBusyInfo(_("Création du PDF des lettres de rappel..."), parent=None, title=_("Veuillez patienter..."), icon=wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Logo.png"), wx.BITMAP_TYPE_ANY))
            #wx.Yield()
            self.EcritStatusbar(_("Création du PDF des lettres de rappel en cours... veuillez patienter..."))
            try :
                UTILS_Impression_rappel.Impression(dictRappels, dictOptions, IDmodele=dictOptions["IDmodele"], ouverture=afficherDoc, nomFichier=nomDoc)
                self.EcritStatusbar("")
                del dlgAttente
            except Exception as err:
                del dlgAttente
                traceback.print_exc(file=sys.stdout)
                err = str(err).decode("iso-8859-15")
                dlg = wx.MessageDialog(None, _("Désolé, le problème suivant a été rencontré dans l'édition des lettres de rappel : \n\n%s") % err, _("Erreur"), wx.OK | wx.ICON_ERROR)
                dlg.ShowModal()
                dlg.Destroy()
                return False

        return dictChampsFusion, dictPieces



if __name__ == '__main__':
    app = wx.App(0)
    #wx.InitAllImageHandlers()
    
    # Test du module Facturation :
    facturation = Facturation(lstIDfamilles=list(range(1, 10)))
##    print len(facturation.GetDonnees( lstIDfamilles=[], liste_activites=[1, 2, 3], listeExceptionsComptes=[], date_reference=datetime.date.today(), date_edition=datetime.date.today(), prestations=["consommation", "cotisation", "autre"]))
##    print len(facturation.GetDonneesImpression(lstIDfamilles=[1, 2, 3]))
    facturation.Impression()
    app.MainLoop()
