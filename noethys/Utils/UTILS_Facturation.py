#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, Matthania gestion multi-activités
# Module:          Génération du fichier pour UTILS_Impression_facture
# Auteur:          Jacques BRUNEL refonte du module 02/2022
# Licence:         Licence GNU GPL
# gére l'édition proforma à partir des pièces regroupées sur numero de facture
# et prend les lignes pièces au lieu des prestations
#------------------------------------------------------------------------

from Utils.UTILS_Traduction import _
import Chemins
import wx
import datetime
import sys
import traceback
import FonctionsPerso as fp
import wx.lib.agw.pybusyinfo as PBI
from Utils import UTILS_Conversion
from Utils import UTILS_Fichiers
from Utils import UTILS_Config
from Data import DATA_Civilites as Civilites
from Utils import UTILS_Titulaires
from Utils.UTILS_Questionnaires import ChampsEtReponses
from Utils import UTILS_Dates
from Dlg import DLG_Apercu_facture
from Utils import UTILS_Impression_facture
from Gest import GestionInscription
import GestionDB
from Gest import GestionArticle
from Ctrl import CTRL_Saisie_transport
from Utils.UTILS_Decimal import FloatToDecimal as FloatToDecimal

SYMBOLE = UTILS_Config.GetParametre("monnaie_symbole", "€")
MONNAIE_SINGULIER = UTILS_Config.GetParametre("monnaie_singulier", _("Euro"))
MONNAIE_DIVISION = UTILS_Config.GetParametre("monnaie_division", _("Centime"))
DICT_CIVILITES = Civilites.GetDictCivilites()

def Supprime_accent(self, texte):
    liste = [("/", " "), ("\\", " "),(":", " "),(".", " "),(",", " "),("<", " "),
             (">", " "),("*", " "),("?", " ")]
    for a, b in liste :
        texte = texte.replace(a, b)
    liste = [ ("é", "e"), ("è", "e"), ("ê", "e"), ("ë", "e"), ("ä", "a"),
              ("à", "a"), ("û", "u"), ("ô", "o"), ("ç", "c"), ("î", "i"), ("ï", "i")]
    for a, b in liste :
        texte = texte.replace(a, b)
        texte = texte.replace(a.upper(), b.upper())
    return texte

def ComposeLibelles(dictCompte,dictOptions):
    # personnalisation des libellés de soldes
    nature = dictCompte["nature"]
    libMontant = "Montant :"
    # premier mot de la nature mis en minuscule
    motNature = dictCompte["{NATURE}"].split(" ")[0]
    libSolde = "Solde sur %s"% motNature
    libReports = "Autres impayés"
    libSoldeDu = "Reste à payer"

    signe = +1 # en cas d'avoir les dus sont négatifs
    if nature == "AVO":
        libMontant = _("Montant AVOIR :")
        signe = -1
    elif nature == "FAC":
        libMontant = _("Montant Facture :")
    elif nature == "COM":
        libMontant = _("Montant Inscription :")
    elif nature in ["DEV","RES"] :
        libMontant = _("Total Devis :")

    # solde pièce positif
    if round(dictCompte["solde"] ,1) <= 0.1 and nature != "AVO":
        libSolde = "%s acquittée "% motNature

    #gestion des soldes globalement positifs
    if round(dictCompte["solde_du"],1) == FloatToDecimal(0.0) and nature != "AVO":
        libSolde = "%s acquittée "% motNature
    elif round(dictCompte["solde_du"],1) * signe  < 0:
        libSoldeDu = "Reporté à votre crédit:"

    if round(dictCompte["total_reports"],1) * signe  < 0:
        libReports = "Autres crédits"

    if nature in ["DEV", "RES"]:
        # total du : cas de devis
        libReports = "Report anterieur"

    return {"{LIB_MONTANT}": libMontant,
            "{LIB_SOLDE}": libSolde,
            "{LIB_REPORTS}": libReports, # ne sera pas exporté, seulement dans l'impression
            "{LIB_SOLDE_DU}": libSoldeDu,
            }

def Nz(valeur):
    try:
        u = float(valeur)
    except:
        valeur = 0
    return valeur

def DateEngEnDateDD(dateEng):
    if dateEng == None or dateEng == "" : return ""
    if not isinstance(dateEng,str):
        dateEng = str(dateEng)
    return datetime.date(int(dateEng[:4]), int(dateEng[5:7]), int(dateEng[8:10]))

def DateEngFr(textDate):
    if textDate == None: return ""
    textDate = str(textDate)
    text = str(textDate[8:10]) + "/" + str(textDate[5:7]) + "/" + str(textDate[:4])
    return text

def RecordsetToListe(recordset):
    myListe = []
    for  record in recordset:
        lstRecord = []
        for val in record:
            lstRecord.append(val)
        myListe.append(lstRecord)    
    return myListe

def Tronque(emetteur,payeur, lgMax=35):
    def TronqueMots(mots, nbmax):
        lstMots = mots.split(" ")
        # enlève les espaces doubles entre mots
        lstMots = [ "%s"% x for x in lstMots if len(x)>0]
        # nbre d'espaces à prévoir
        nbsp = len(lstMots) - 1
        # longeur max moyenne mais on garde un minimum de 3caractères par mot
        nbmoy = max(int((nbmax - nbsp) / len(lstMots)),3)
        newLst = []
        for mot in lstMots[:-1]:
            if len(mot)> nbmoy:
                mot = mot[:nbmoy]
            newLst.append("%s"% mot)
        # le dernier mot prend le rab
        reste = int(nbmax - nbsp)
        newmot = ""
        for item in newLst:
            newmot += item + " "
            reste -= len(item)
        rest = max(reste,3)
        newmot += lstMots[-1][:reste]
        return newmot

    if not payeur: payeur = ""
    if not emetteur: emetteur = ""
    emetteur = emetteur.strip()
    if len(emetteur + payeur) > lgMax:
        if len(emetteur) > ((lgMax - 3) / 2):
            emetteur = TronqueMots(emetteur,int(lgMax / 2))
    payeur = payeur.strip()
    if len(payeur) > (lgMax - len(emetteur)):
        payeur = TronqueMots(payeur,lgMax - len(emetteur))
    return emetteur,payeur

def ContrepartieReglement(lettreOrigine,IDreglement,recordset):
    # retourne le libellé de la contrepartie
    lstMatch = []
    def testLettre(letA,letB):
        test = False
        # la correspondance des lettres peut être inversée
        lstParts = lettreOrigine
        if "_" in lettreOrigine:
            lstParts = letA.split("_")
        # test soit 1e et dernière lettre soit les deux parties séparées par '_'
        if (lstParts[0] in letB) and lstParts[-1] in letB:
            test = True
        return test

    def extraitContrepartie(record):
        (IDreglement, date_reglement, differe, mode, observations, emetteur, payeur,
        ventile, surMontant, IDprestation, IDfamille, lblPrest, dtePrest, lettre) = record
        if lettre and testLettre(lettreOrigine,lettre):
            if observations:
                return "%s %s"%(observations,mode)
            return mode
        return None

    # reprend la liste des champs du recordset cf requête originale
    if lettreOrigine:
        for record in recordset:
            if record[0] == IDreglement:
                continue
            mode = extraitContrepartie(record)
            if mode:
                lstMatch.append(mode)
    label = "autre affectation"
    if len(lstMatch) >0:
        label = lstMatch[0]
    return label

class Facturation():
    def __init__(self):
        #préparation des conteneurs d'initialisation
        self.dictIndividus = {}
        self.dictMessageFamiliaux = {}
        self.dictOrganisme = {}
        self.dictActivites = {}
        self.dictGroupes = {}
        self.reportInclus = False
        # " Récupération des questionnaires"
        self.Questionnaires = ChampsEtReponses(type="famille")
        # "fin __init__"

    def RechercheAgrement(self, IDactivite, date):
        agrement = self.dictActivites[IDactivite]["agrement"]
        date_debut = self.dictActivites[IDactivite]["date_debut"]
        date_fin = self.dictActivites[IDactivite]["date_fin"]
        if not date:
            return agrement
        if date >= date_debut and date <= date_fin :
            return agrement
        return None

    def RecherchePresence(self, IDactivite, IDindividu, IDgroupe):
        # Recherche nbre de jours d'ouverture
        if IDactivite > 0:
            nbJours = GestionArticle.NbreJoursActivite(self.DB,IDactivite,IDgroupe,IDindividu=IDindividu)
            dateDebut,dateFin= GestionArticle.DebutFin_Consos(self.DB,IDactivite,IDindividu)
            date_debut = UTILS_Dates.DateEngEnDateDD(dateDebut)
            date_fin = UTILS_Dates.DateEngEnDateDD(dateFin)
        else:
            nbJours = 0
            date_debut, date_fin = None, None
        return nbJours, date_debut, date_fin

    def EcritStatusbar(self, texte=""):
        try :
            topWindow = wx.GetApp().GetTopWindow() 
            topWindow.SetStatusText(texte)
        except : 
            pass
    
    def RemplaceMotsCles(self, texte="", dictValeurs={}):
        for key, valeur, in dictValeurs.items() :
            if key in texte :
                texte = texte.replace(key, valeur)
        return texte

    # ----------------------------- Structure de dictToPdf -------------------------------------------------------------
    """
    [IDfamille]
        [IDpage] as dictToPage
            ["individus"][IDindividu] as dictToIndividu
                                ["activites"][IDactivite] as dictToActivite
                                                   ["presences"][date]
                                                                   ["unites"] = list[dictPrestation,]
                                                                   ["montant"] = decimal
                                ["nom"] = str
                                ["texte"] = str
                                ["montant"] = decimal
                                ["ventilation"] = decimal
            ["reports"][str(periode)]
                                [nature] = decimal 
            ["reglements"][IDreglement] = dictReglement
            autres clé  int: IDfamille,IDpage,noPage,noFact,select,nature,nomSansCivilite,texte_introduction,
                        str: numero, date_echeance,nature,{LIB_MONTANT},{LIB_SOLDE},{LIB_REPORTS},{LIB_SOLDE_DU}
                        decimal: montant,ventilation,solde,total_reports,solde_du, 
                        date: date_edition,date_debut,date_fin, 
                                
    """

    # gestion d'une activité correspondant à une pièce pour ce IDpage
    def GetActivite(self,**kw):
        IDactivite = kw["IDactivite"]
        IDindividu = kw["IDindividu"]
        IDgroupe = kw.get("IDgroupe", None)
        IDinscription = kw.get("IDinscription", None)
        dictToPage = kw["dictToPage"]
        dictDonActivite = kw["dictDonActivite"]
        dictDonIndividu = kw["dictDonIndividu"]

        # Recherche nbre de jours d'ouverture de l'inscription

        nbJours, dateDebut, dateFin = self.RecherchePresence(IDactivite,IDindividu,IDgroupe)

        # Ajout de l'activité
        nomActivite = None
        if IDactivite > 0:
            nomActivite = self.dictActivites[IDactivite]["nom"]
        if nomActivite == None :
            nomActivite = "calculées sur l'année "
        if IDgroupe :
            nomGroupe = self.dictGroupes[IDgroupe]["nom"]
        else: nomGroupe = " "
        texteActivite = nomActivite + " " + nomGroupe
        if dateFin != None:
            texteActivite += _("\nDu %s au %s soit %d jours") % (DateEngFr(str(dateDebut)), DateEngFr(str(dateFin)), nbJours)
            #texteActivite += label

        if IDactivite > 0:
            agrement = self.RechercheAgrement(IDactivite, None)
        else: agrement = None
        if agrement != None :
            texteActivite += _(" - n° agrément : %s") % agrement

        # création dictToActivite
        dictToActivite = { "texte": texteActivite,
                        "presences": {dateDebut: {"unites" : [],
                                                  "montant" : FloatToDecimal(0.0)}}}
        
        # Recherche des déductions
        deductions = []

        # Mémorisation des déductions pour total
        for dictDeduction in deductions :
            dictToPage["listeDeductions"].append(dictDeduction)

        # appel des unites et lignes détail
        dictToActivite["presences"][dateDebut]["unites"] = []
        lstUnites = dictToActivite["presences"][dateDebut]["unites"]

        # fonction d'incorporation d'une ligne dans les "unites"
        def ajouteLigne(dLigne):
            dicTo = {}
            for champ in ("label", "montant", "tva", "deductions"):
                dicTo[champ] = dLigne[champ]
            lstUnites.append(dicTo)
            dictToPage["montant"] += FloatToDecimal(dicTo["montant"])
            dictDonIndividu["montant"] += FloatToDecimal(dicTo["montant"])


        # déroulé des pièces de l'activité pour génération des lignes
        for IDpiece in list(dictDonActivite.keys()):
            # pointe le paquet de lignes de la pièce puis ajoute la ligne transport
            for dictLigne in  self.dictPieces[IDpiece]["lstLignes"]:
                ajouteLigne(dictLigne)
            if len(self.dictPieces[IDpiece]["dictTransport"]) > 0:
                ajouteLigne(self.dictPieces[IDpiece]["dictTransport"])

        return dictToActivite

    def GetIndividu(self,**kw):
        IDindividu = kw["IDindividu"]
        dictDonIndividu = kw["dictDonIndividu"]

        # création dictToIndividu
        dictToIndividu = { "activites" : {}}

        # appel niveau inférieur
        for keyInscription in list(dictDonIndividu.keys()):
            if len(keyInscription) == 3:
                (IDactivite, IDgroupe, IDtarif) = keyInscription
                kw["IDactivite"] = IDactivite
                kw["IDgroupe"] = IDgroupe
                kw["IDtarif"] = IDtarif
                kw["dictDonActivite"] = dictDonIndividu[keyInscription]
                dictToIndividu["activites"][keyInscription] = self.GetActivite(**kw)

        # données propres à l'incividu
        if IDindividu > 0:
            IDcivilite = self.dictIndividus[IDindividu]["IDcivilite"]
            nomIndividu = self.dictIndividus[IDindividu]["nom"]
            prenomIndividu = self.dictIndividus[IDindividu]["prenom"]
            dateNaiss = self.dictIndividus[IDindividu]["date_naiss"]
            if dateNaiss != None :
                if DICT_CIVILITES[IDcivilite]["sexe"] == "M" :
                    texteDateNaiss = _(", né le %s") % UTILS_Dates.DateEngFr(str(dateNaiss))
                else:
                    texteDateNaiss = _(", née le %s") % UTILS_Dates.DateEngFr(str(dateNaiss))
            else:
                texteDateNaiss = ""
            texteIndividu = _("<b>%s %s</b><font size=7>%s</font>") % (nomIndividu, prenomIndividu, texteDateNaiss)
            nom = "%s %s" % (nomIndividu, prenomIndividu)
        else:
            # Si c'est pour une prestation familiale on créé un individu ID 0 :
            nom = _("Prestations familiales")
            texteIndividu = "<b>%s</b>" % nom
        dictToIndividu["montant"] = dictDonIndividu["montant"]
        dictToIndividu["texte"] = texteIndividu
        dictToIndividu["ventilation"] = FloatToDecimal(0.0)
        dictToIndividu["nom"] = nom

        return dictToIndividu

    # Analyse et regroupement des données dans les comptes pour constituer la page pdf
    def GetPage(self, IDfamille, IDpage, dictOptions):
        # génération de dictToPage : racourci vers le conteneur de données pour une page
        dictDonPage = self.dictDonnees[IDfamille][IDpage]

        #  préalable: récup des données concernant la page
        dateDebut, dateFin = "2999-12-31", "1900-01-01"
        for IDactivite in dictDonPage["lstIDactivites"]:
            # Recherche dates de période
            if IDactivite > 0:
                date_debut = self.dictActivites[IDactivite]["date_debut"]
                date_fin = self.dictActivites[IDactivite]["date_fin"]
            else:
                date_debut, date_fin = None, None

            if date_debut and (date_debut < dateDebut): dateDebut = date_debut
            if date_fin   and (date_fin   > dateFin):   dateFin   = date_fin

        date_debut = UTILS_Dates.DateEngEnDateDD(dateDebut)
        date_fin = UTILS_Dates.DateEngEnDateDD(dateFin)

        date_edition = UTILS_Dates.DateEngEnDateDD(dictDonPage["date_edition"])
        date_echeance = UTILS_Dates.DateEngEnDateDD(dictDonPage["date_echeance"])

        nature = dictDonPage["nature"]
        if nature == "FAC" : titre = _("Facture")
        elif nature == "AVO" : titre = _("Avoir")
        elif nature == "DEV" : titre = _("Devis sans réservation")
        elif nature == "RES" : titre = _("Devis à confirmer")
        elif nature == "COM" : titre = _("Inscription")
        else : titre = _("Attestation de présence")
        titrePiece = titre.split(' ')[0]

        dictInfosTitulaires = self.dictNomsTitulaires[IDfamille]
        nomsTitulairesAvecCivilite = dictInfosTitulaires["titulairesAvecCivilite"]
        nomsTitulairesSansCivilite = dictInfosTitulaires["titulairesSansCivilite"]
        nomsTitulairesCivilite = dictInfosTitulaires["titulairesCivilite"]
        rue_resid = dictInfosTitulaires["adresse"]["rue"]
        cp_resid = dictInfosTitulaires["adresse"]["cp"]
        ville_resid = dictInfosTitulaires["adresse"]["ville"]
        facturesNo = dictDonPage["facturesNo"]
        txtNumeroA = ""
        # Compose un texte numéro de page et de facture
        def composeNo():
            if nature == "AVO" : txtNumeroA = "Avoir  N°:"
            if nature == "FAC" : txtNumeroA = "Facture  N°:"
            if nature in ("DEV","RES","COM") : txtNumeroA = "Ref N°:"

            if facturesNo == 0: # cas des devis ou commande
                txtNumeroB = "%s %s-%03d"%(nature[0:1],str(IDfamille), datetime.date.today().timetuple().tm_yday)
                numFacture = ""
            else:
                numFacture = "%06d" % facturesNo
                txtNumeroB = "%06d" % facturesNo
            numero = "%s %s"%(txtNumeroA, txtNumeroB)
            return numero, numFacture
        numero, numFacture = composeNo()

        # création de la page
        dictToPage = {
            "IDpage": IDpage,
            "date_debut" : date_debut,
            "date_fin" : date_fin,
            "date_edition" : date_edition,
            "date_echeance": date_echeance,
            "individus" : {},
            "IDfamille" : IDfamille,
            "montant" : FloatToDecimal(0.0),
            "nomSansCivilite" : nomsTitulairesSansCivilite,
            "nature" : nature,
            "solde" : FloatToDecimal(0.0),
            "ventilation" : FloatToDecimal(0.0),
            "qfdates" : {},
            "reports" : {},
            "total_reports" : FloatToDecimal(0.0),
            "select" : True,
            "messages_familiaux" : [],
            "reglements" : {},
            "numero" : numero,
            "noFact" : facturesNo,
            "{IDFAMILLE}" : str(IDfamille),
            "{NUM_FACTURE}" : "%06d" % facturesNo,
            "{CODEBARRES_NUM_FACTURE}" :"F%06d" % facturesNo,
            "{TEXTE_NUMERO}" : numero,
            "{NATURE}" : titre,
            "{FAMILLE_NOM}" : nomsTitulairesAvecCivilite,
            "{FAMILLE_NOM_SANS}" : nomsTitulairesSansCivilite,
            "{FAMILLE_CIVILITE}" : nomsTitulairesCivilite,
            "{FAMILLE_RUE}" : rue_resid,
            "{FAMILLE_CP}" : cp_resid,
            "{FAMILLE_VILLE}" : ville_resid,
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
        kw = {"IDfamille": IDfamille,
              "IDpage": IDpage,
              "dictToPage": dictToPage}
        for IDindividu in dictDonPage["lstIDindividus"]:
            kw["IDindividu"] = IDindividu
            kw["dictDonIndividu"] = dictDonPage[IDindividu]
            dictToPage["individus"][IDindividu] = self.GetIndividu(**kw)

        # Ajoute les réponses des questionnaires
        for dictReponse in self.Questionnaires.GetDonnees(IDfamille) :
            dictToPage[dictReponse["champ"]] = dictReponse["reponse"]
            if dictReponse["controle"] == "codebarres" :
                dictToPage["{CODEBARRES_QUESTION_%d}" % dictReponse["IDquestion"]] = dictReponse["reponse"]

        # Ajoute les messages familiaux
        if IDfamille in self.dictMessageFamiliaux :
            dictToPage["messages_familiaux"] = self.dictMessageFamiliaux[IDfamille]

        # fonction Ajout totaux en allant chercher dans dictVentilations
        def cumuleDansPage():
            montant = FloatToDecimal(0.0)
            ventilation = FloatToDecimal(0.0)
            reglements = {}
            dictReglFinal = {}

            # calcul du montant des prestations et des ventilations par règlements affectés
            if len(dictDonPage["lstIDprestations"]) > 0:
                for IDprestation in  dictDonPage["lstIDprestations"]:
                    dictPrestation = self.dictVentilations[IDfamille]["prestations"][IDprestation]
                    montant += dictPrestation["montant"]
                    if len(dictPrestation["reglAffectes"]) > 0:
                        for IDreglement, dictReglement in dictPrestation["reglAffectes"].items():
                            ventilation += FloatToDecimal(dictReglement["ventilation"])
                            if IDreglement in reglements:
                                reglements[IDreglement]["ventilation"] += dictReglement["ventilation"]
                            else:
                                reglements[IDreglement] = dictReglement
                # Ajouts des affectations complémentaires des règlements
                for IDreglement, dictReglement in reglements.items():
                    ix = 0
                    # ligne du règlement proprement dit
                    cle1 = "%s_%04.f"%(str(dictReglement["dateReglement"]),IDreglement)
                    cle2 = "_%02.f"%(ix)
                    dictReglFinal[cle1+cle2] = dictReglement
                    if IDreglement in self.dictAutresAffect[IDfamille] \
                            and (round(dictReglement["ventilation"] - dictReglement["montant"],2)) != 0:
                        # lignes des autres affectations
                        for (label, ventile, surMontant, IDprestation, lettre) in self.dictAutresAffect[IDfamille][IDreglement]:
                            ix += 1
                            cle2 = "_%02.f" % (ix)
                            texte = "______  (%9.2f%s sur %s)"%(ventile,SYMBOLE,label)
                            dictReglFinal[cle1 + cle2] = {"autreAffect":texte}

            # vérif du montant des pièces qui doit égaler les prestations
            mttPieces = dictToPage["montant"]
            # pour inversion du sens pour les avoirs
            signe = +1
            if dictToPage["nature"] == "AVO": signe = -1
            if dictToPage["nature"] in ("DEV", "RES"):
                signe = 0 # les devis et réservation n'ont pas de prestation encore due
            if montant != (mttPieces * signe):
                mess = "Total Prestations: %.2f, total Pieces: %.2f, pour famille %d!"%(montant,mttPieces,IDfamille)
                mess += "\nsur pièce : %s"%dictToPage["numero"]
                wx.MessageBox(mess, "Incohérence dans les données")
                return None

            # Insert les montants pour le compte
            dictToPage["ventilation"] = ventilation
            dictToPage["reglements"] = dictReglFinal

            return "ok"
        ret = cumuleDansPage()
        if not ret == "ok": return

        # fonction d'ajout REPORT des impayés et des règlemments libres qui n'ont pas été imputés
        def defReportImpayes():
            # Déduction des reglements libres sur les impayés
            dictTousImpayes = self.dictVentilations[IDfamille]["impayes"]
            dictReglLibres = self.dictVentilations[IDfamille]["reglementsLibres"]
            #déroulement des impayes pour les mettre dans les reports
            for IDprestation, dictImpayes in dictTousImpayes.items():
                # on ignore les prestations dues dans la page en cours
                if IDprestation in dictDonPage["lstIDprestations"]:
                    continue
                solde = 0
                # on déroule pour chaque autre prestation non présente dans la page pour les reporter
                if (dictToPage["nature"] != "AVO" ):
                    for periode in dictImpayes:
                        for type in dictImpayes[periode]:
                            montant_impaye = dictImpayes[periode][type]
                            # presence de comptes à éditer
                            if (periode in dictToPage["reports"]) == False :
                                dictToPage["reports"][str(periode)] = {}
                            if (type in dictToPage["reports"][str(periode)]) == False :
                                dictToPage["reports"][str(periode)][type] = FloatToDecimal(0.0)
                            solde += montant_impaye
                            dictToPage["reports"][str(periode)][type] += montant_impaye
                    dictToPage["total_reports"] += solde

            # Reports: déduction des règlements toujours libres
            mtt = FloatToDecimal(0.0)
            if len(dictReglLibres)>0:
                for IDreglement, dictRegl in dictReglLibres.items():
                    if dictRegl["montant"]: mtt += dictRegl["montant"]
                    if dictRegl["ventilation"]: mtt -= dictRegl["ventilation"]
                if mtt !=  FloatToDecimal(0.0):
                    if mtt > 0 :
                        period = "Affecter"
                        dictToPage["reports"][period] = {"Reg":mtt}
                    else:
                        period = "AutresDus"
                        dictToPage["reports"][period] = {"Deb":mtt}
                    dictToPage["total_reports"] -= mtt
            duReel = self.dictSoldes[IDfamille]['prestations']
            duReel -= self.dictSoldes[IDfamille]['reglements']
            duPage = - dictToPage["ventilation"]
            if dictToPage['nature'] in ['FAC', 'AVO', 'COM']:
                duPage += dictToPage["montant"]
            duPage += dictToPage["total_reports"]
            mtt = duPage - FloatToDecimal(duReel)
            if abs(mtt) >= 0.1:
                period = "Reprise"
                if mtt > 0:
                    dictToPage["reports"][period] = {"Crédit": mtt}
                else:
                    dictToPage["reports"][period] = {"Débit": mtt}
                dictToPage["total_reports"] -= mtt

            if abs(dictToPage["total_reports"]) < FloatToDecimal(0.1) : dictToPage["total_reports"] = FloatToDecimal(0)

            return
            #fin defReportImpayes

        defReportImpayes()

        # inversion éventuelle de la nature de la pièce
        negatif = (dictToPage["montant"] < 0)
        if dictOptions["inversion_solde"] and negatif :
            dictToPage["montant"] = -dictToPage["montant"]
            if dictToPage["nature"] == "FAC" :
                dictToPage["nature"] = "AVO"
                dictToPage["{NATURE}"] = _("Avoir")
            elif dictToPage["nature"] == "AVO"  :
                dictToPage["nature"] = "FAC"
                dictToPage["{NATURE}"] = _("Facture")

        if  dictToPage["nature"] == "AVO":
            dictToPage["ventilation"] = -dictToPage["ventilation"]
            dictToPage["total_reports"] = -dictToPage["total_reports"]

        dictToPage["solde"] = dictToPage["montant"] - dictToPage["ventilation"]
        dictToPage["solde_du"] = dictToPage["montant"] - dictToPage["ventilation"] + dictToPage["total_reports"]


        dictToPage["{DATE_EDITION_COURT}"] = UTILS_Dates.DateEngFr(dictToPage["date_edition"])

        for IDindividu, dictIndividu in dictToPage["individus"].items() :
            dictIndividu["select"] = True

        # recherche des prélèvements (désactivée)
        """# Recherche de prélèvements
        dictPrelevements = self.GetPrelevements(dictDonPage["IDfacture"]
        if dictPrelevements.has_key(IDpage) :
            if datePrelevement < dictToPage["date_edition"] :
                verbe = _("a été")
            else :
                verbe = _("sera")
            montant = dictPrelevements[IDpage]["montant"]
            datePrelevement = dictPrelevements[IDpage]["datePrelevement"]
            iban = dictPrelevements[IDpage]["iban"]
            rum = dictPrelevements[IDpage]["rum"]
            code_ics = dictPrelevements[IDpage]["code_ics"]
            if iban != None :
                dictToPage["prelevement"] = _("La somme de %.2f %s %s prélevée le %s sur le compte ***%s") % (montant, SYMBOLE, verbe, UTILS_Dates.DateEngFr(str(datePrelevement)), iban[-7:])
            else :
                dictToPage["prelevement"] = _("La somme de %.2f %s %s prélevée le %s") % (montant, SYMBOLE, verbe, UTILS_Dates.DateEngFr(str(datePrelevement)))
            if rum != None :
                dictToPage["prelevement"] += _("<br/>Réf. mandat unique : %s / Code ICS : %s") % (rum, code_ics)
        else :
            dictToPage["prelevement"] = None"""

        # Champs de fusion pour Email par famille
        IDfamille = dictToPage['IDfamille']
        if not IDfamille in list(self.dictChampsFusion.keys()):
            self.dictChampsFusion[IDfamille] = {}
        dictChampsFusion = self.dictChampsFusion[IDfamille]

        # stockage des valeurs dates
        lstKeysTxt = ["DATE_DEBUT","DATE_FIN","DATE_ECHEANCE"]
        for keyTxt in lstKeysTxt:
            # dates en lettre avec clé mise entre crochet
            dictChampsFusion["{%s}"% keyTxt] = UTILS_Dates.DateEngFr(str(dictToPage[keyTxt.lower()]))

        dictChampsFusion["{DATE_EDITION_COURT}"] = UTILS_Dates.DateEngFr(dictToPage["date_edition"])
        dictChampsFusion["{DATE_EDITION_LONG}"] = UTILS_Dates.DateComplete(dictToPage["date_edition"])

        # personnalise les clés libellés de soldes
        dictToPage.update(ComposeLibelles(dictToPage,dictOptions))

        # Gère la casse et le contenu des textes en concaténant si plusieurs factures nature diff
        lstKeys = ["{TEXTE_NUMERO}","{NUM_FACTURE}","{NATURE}","{LIB_MONTANT}", "{LIB_SOLDE}", "{LIB_SOLDE_DU}"]
        for key in lstKeys:
            if (key in list(dictChampsFusion.keys())) and (key[:4] != "{LIB"):
                # ne concatène que si élément différent
                if len(dictToPage[key]) > 0 and not dictToPage[key].lower() in dictChampsFusion[key]:
                    dictChampsFusion[key] += "%s, "%dictToPage[key]
            else:
                # nouvel clé ou LIB pour qui on ne garde que le dernier passage
                dictChampsFusion[key] = dictToPage[key]

            if key[:4] != "{LIB":
                dictChampsFusion[key] = dictChampsFusion[key].lower()


        # vers cumuls tts pièces "{MONTANT}","{VENTILATION}","{SOLDE}"
        lstKeys = ["montant","ventilation","solde"]
        for key in lstKeys:
            # présence d'un pièce précédente on cumule dans la clé lower
            if key in list(dictChampsFusion.keys()):
                valeur = dictChampsFusion[key] + dictDonPage[key]
                dictChampsFusion["{%s}"%key.upper()] = "%.2f %s" % (valeur, SYMBOLE)
            else:
                dictChampsFusion["{%s}"%key.upper()] = "%.2f %s" % (dictToPage[key], SYMBOLE)

        dictToPage["{SOLDE_LETTRES}"] = UTILS_Conversion.trad(dictToPage["solde"],
                                                              MONNAIE_SINGULIER,
                                                              MONNAIE_DIVISION).strip().capitalize()

        # Fusion pour textes personnalisés
        if len(dictOptions["texte_introduction"]) > 0:
            dictToPage["texte_introduction"] = self.RemplaceMotsCles(dictOptions["texte_introduction"], dictToPage)
        if len(dictOptions["texte_conclusion"]) >0:
            dictToPage["texte_conclusion"] = self.RemplaceMotsCles(dictOptions["texte_conclusion"], dictToPage)

        # fin Ajout totaux

        return dictToPage
        #fin GetPage

    # constitution du fichier qui sera envoyé à l'impession PDF
    def GetDonnees(self, dictOptions=None):

        dictToPdf = {}
        self.EcritStatusbar(_("Recherche des factures"))
        # Récupération des données de facturation
        typeLabel = 0
        if dictOptions != None and "intitules" in dictOptions :
            typeLabel = dictOptions["intitules"]
            
        # Génération des pages :passe par le squelette l'ensemble des infos de page est appelé
        for IDfamille in list(self.dictDonnees.keys()):
            for IDpage in list(self.dictDonnees[IDfamille].keys()):
                # dictToPdf a pour clé: IDpage, dictChampsFusion: IDfamille usage pour mails (sous ensemble de champs)
                dictToPage = self.GetPage(IDfamille,IDpage, dictOptions)
                # l'échec de cohérence peut avoir renvoyé None: on n'imprime pas
                if dictToPage:
                    dictToPdf[IDpage] = dictToPage
        self.EcritStatusbar("")
        return dictToPdf
        #fin GetDonnees

    #-------------------- Fin de la construction de dictToPdf ----------------------------

    # Récupère les éléments libres d'affectation à une prestation
    def GetReglementsLibres(self):

        # Get liste présumés libres : IDreglements non complètement ventilés
        req = """
                SELECT  reglements.IDreglement, reglements.montant, SUM(ventilation.montant)
                FROM reglements
                LEFT JOIN ventilation ON reglements.IDreglement = ventilation.IDreglement       
                WHERE reglements.IDcompte_payeur IN (%s)
                GROUP BY reglements.IDreglement, reglements.montant
                ;""" % str(self.lstIDfamilles)[1:-1]
        retour = self.DB.ExecuterReq(req, MsgBox="UTILS_Facturation.GetReglementsLibres_2")
        recordset = self.DB.ResultatReq()
        lstIDregl = [ x for (x,y,z) in recordset if (not z) or (round(y,2) != round(z,2))]
        # Get des reglements partiellement ventilés ou sans ventilation
        if len(lstIDregl) == 0:
            return

        # suite en appelant de l'info plus détaillée sur les présumés libres
        req = """
            SELECT  reglements.IDreglement,reglements.Date, reglements.date_differe, modes_reglements.label, 
                    reglements.observations, emetteurs.nom, payeurs.nom, reglements.montant, 
                    SUM(ventilation.montant), reglements.IDcompte_payeur
            FROM (((reglements
            LEFT JOIN ventilation   ON reglements.IDreglement = ventilation.IDreglement)
            LEFT JOIN emetteurs     ON reglements.IDemetteur = emetteurs.IDemetteur)
            LEFT JOIN modes_reglements ON reglements.IDmode = modes_reglements.IDmode)
            LEFT JOIN payeurs       ON reglements.IDpayeur = payeurs.IDpayeur
            WHERE reglements.IDreglement in ( %s ) 
            GROUP BY reglements.IDreglement,reglements.Date, reglements.date_differe, modes_reglements.label, 
                    reglements.observations, emetteurs.nom, payeurs.nom, reglements.montant, reglements.IDcompte_payeur
            ORDER BY reglements.IDcompte_payeur, reglements.Date
            ;""" % str(lstIDregl)[1:-1]
        retour = self.DB.ExecuterReq(req, MsgBox="UTILS_Facturation.GetReglementsLibres_3")
        recordset = self.DB.ResultatReq()

        lstReglNegatifs = []
        lstReglPositifs = []
        reglements = {}
        # champs de l'info dans dictReglement
        lstChampsRegl = ["IDreglement", None, None, "mode", "observations", "emetteur",
                         "payeur", "montant", "ventilation", "IDfamille"]
        # Prépare l'Imputation des réglemnents négatifs ou sur ventilés sur les positifs
        ix = -1
        for IDreglement,dateR,differe,mode,observations,emetteur,payeur,montant,ventilation,IDfamille in recordset:
            ix +=1
            if Nz(montant) - Nz(ventilation) < 0 :
                lstReglNegatifs.append(IDreglement)
            else: lstReglPositifs.append(IDreglement)

            # ajustement de la date
            if differe != None:
                dateR = differe
            dateR = DateEngEnDateDD(dateR)

            # composition du dictionnaire des champs du règlement libre
            reglements[IDreglement] = {"dateReglement" : dateR }
            iy = -1
            for champ in lstChampsRegl:
                iy +=1
                if not champ: continue
                value = recordset[ix][iy]
                if not value and champ == "ventilation": value = FloatToDecimal(0.0)
                if isinstance(value, float):
                    value = FloatToDecimal(value)
                reglements[IDreglement][champ] = value

        lstSupprime = []
        # Action d'imputation des réglemnents négatifs ou sur ventilés sur les positifs
        for IDreglNeg in lstReglNegatifs:
            dReglNeg = reglements[IDreglNeg]
            affectable = -dReglNeg["montant"] + dReglNeg["ventilation"]
            for IDreglPos in lstReglPositifs:
                dReglPos = reglements[IDreglPos]
                impute = min(affectable, dReglPos["montant"] - dReglPos["ventilation"])
                if impute == 0: continue
                dReglPos["ventilation"] += impute
                dReglNeg["ventilation"] -= impute
                affectable -=impute
                if round(dReglPos["montant"] - dReglPos["ventilation"],1) == 0:
                    lstSupprime.append(dReglPos["IDreglement"])
                if affectable <= 0:
                    break
            if round(dReglNeg["montant"] - dReglNeg["ventilation"],1) == 0:
                lstSupprime.append(dReglNeg["IDreglement"])

        # purge des règlements totalement ventilés à moins d'un €
        for IDreglement in lstSupprime:
            del reglements[IDreglement]

        # fonction d'écriture dans dictVentilations
        def setReglements(reglements):
            for IDreglement, dRegl in reglements.items():
                # pointeur de niveau IDprestation dans self.dictVentilations
                dictReglLibres = self.dictVentilations[IDfamille]["reglementsLibres"]
                dRegl["emetteur"],dRegl["payeur"] = Tronque(dRegl["emetteur"],dRegl["payeur"])
                # stockage dans self.dictVentilations[IDfamille]"reglementsLibres"
                dictReglLibres[IDreglement] = dRegl
        setReglements(reglements)

    # Récupération des règlements ventilés sur des prestations du lot
    def GetReglementsAffectes(self):
        # appel des règlements des familles
        req = """
            SELECT  reglements.IDreglement,reglements.Date, reglements.date_differe, modes_reglements.label, 
                    reglements.observations, emetteurs.nom, payeurs.nom, ventilation.montant, reglements.montant, 
                    ventilation.IDprestation, reglements.IDcompte_payeur, 
                    prestations.label, prestations.date, ventilation.lettrage
            FROM ((((reglements LEFT JOIN emetteurs ON reglements.IDemetteur = emetteurs.IDemetteur) 
            LEFT JOIN modes_reglements ON reglements.IDmode = modes_reglements.IDmode) 
            LEFT JOIN payeurs ON reglements.IDpayeur = payeurs.IDpayeur) 
            LEFT JOIN ventilation ON reglements.IDreglement = ventilation.IDreglement) 
            LEFT JOIN prestations ON ventilation.IDprestation = prestations.IDprestation
            WHERE (reglements.IDcompte_payeur in (%s) )
            ORDER BY reglements.Date
            ;""" % str(self.lstIDfamilles)[1:-1]

        retour = self.DB.ExecuterReq(req, MsgBox="UTILS_Facturation.GetReglementsAffectes")
        recordset = self.DB.ResultatReq()

        #pour chaque ventilation on crée un dictVentil stocké en self.dictVentilations
        lstChampsRegl = ["IDreglement", "mode", "observations", "emetteur",
                       "payeur", "ventilation", "montant", "IDprestation", "IDfamille"]
        lstIDreglements = []
        for IDreglement, date_reglement, differe, mode, observations, emetteur, payeur, \
               ventile, surMontant, IDprestation, IDfamille, lblPrest, dtePrest, lettre in recordset :
            # test cohérence
            if not IDfamille in self.dictVentilations:
                mess = "Problème avec le règlements %d de la famille %d\n"%(IDreglement, IDfamille)
                mess += "Il est ventilé sur la prestation '%d' d'une autre famille,\n"%IDprestation
                mess += "refaites la ventilation!"
                wx.MessageBox(mess,"Anomalie dans les données")
                continue

            # stockage des ventil non directement pour prestations de la page, mais...
            if not IDfamille in self.dictAutresAffect:
                self.dictAutresAffect[IDfamille] = {}
            if not IDreglement in self.dictAutresAffect[IDfamille]:
                self.dictAutresAffect[IDfamille][IDreglement] = []

            # Traitement des règlements ne pointant pas une des prestations
            if (IDprestation == 0) or IDprestation not in self.lstIDprestations:
                # compose la ligne autre affectation
                label = mode
                if observations and len(observations)>0:
                    label = observations
                if IDprestation == 0:
                    label = ContrepartieReglement(lettre,IDreglement,recordset)
                if lblPrest:
                    label = lblPrest
                record = (label, ventile, surMontant, IDprestation, lettre)
                self.dictAutresAffect[IDfamille][IDreglement].append(record)
                continue

            # Traitement des règlements des prestations
            if not IDreglement in lstIDreglements:
                lstIDreglements.append(IDreglement)
            dictPrestations = self.dictVentilations[IDfamille]["prestations"]
            emetteur, payeur = Tronque(emetteur,payeur)
            record = (IDreglement, mode, observations, emetteur,
                      payeur, ventile, surMontant, IDprestation, IDfamille )
            if differe != None:
                date_reglement = differe
            date = DateEngEnDateDD(date_reglement)

            # dictionnaire des champs du règlement ventilé
            dictRegl= {"dateReglement" : date}
            i=0
            for item in record :
                if lstChampsRegl[i] != None :
                    if isinstance(item, float): item = FloatToDecimal(item)
                    dictRegl[lstChampsRegl[i]] = item
                i += 1
            if dictRegl["ventilation"] == None :
                dictRegl["ventilation"] = FloatToDecimal(0.0)

            #regroupement des ventilations par IDprestation et par réglement
            if IDprestation not in dictPrestations:
                # clé censée être dans le squelette
                raise Exception("Pb logique : UTILS_Facturation.GetReglementsAffectes pour IDprestation '%d'"%IDprestation)
            #stocke la ventilation d'un reglement / IDprestation
            dictPrestations[IDprestation]["reglAffectes"][IDreglement] = dictRegl
            # doublon dictPrestations[IDprestation]["regle"] += FloatToDecimal(ventile)

    # Prestations impayées : self.dictVentialations[IDfamille]["impayes"][IDprestation][periode][nature] = montantImpaye
    def GetImpayes(self):
        #appel de toutes les prestations pour toutes les familles du lot
        condition = " WHERE prestations.IDfamille in ( %s ) "% str(self.lstIDfamilles)[1:-1]
        req = """
            SELECT  prestations.IDprestation, prestations.montant, SUM(ventilation.montant)
            FROM prestations
            LEFT JOIN ventilation ON prestations.IDprestation = ventilation.IDprestation
            WHERE prestations.IDfamille IN (%s)
            GROUP BY prestations.IDprestation, prestations.montant
            ;""" % str(self.lstIDfamilles)[1:-1]
        retour = self.DB.ExecuterReq(req, MsgBox="UTILS_Facturation.GetImpayes_1")
        recordset = self.DB.ResultatReq()
        lstIDprest = []
        dictPrestVentilation = {}
        for IDprestation, montant, regle in recordset:
            if not regle: regle = 0.0
            if round(montant,2) != round(regle,2):
                lstIDprest.append(IDprestation)
                dictPrestVentilation[IDprestation] = {"montant": FloatToDecimal(montant),
                                                      "regle": FloatToDecimal(regle)}
        if len(lstIDprest) == 0:
            return

        #appel des prestations non soldées avec plus de détail
        condition = " WHERE prestations.IDprestation in ( %s ) "% str(lstIDprest)[1:-1]
        req = """
            SELECT prestations.IDprestation, prestations.IDfamille, prestations.Date, 
                    prestations.montant, prestations.label,
                    matPieces.pieNature, matPieces.pieDateFacturation, matPieces.pieDateAvoir
            FROM prestations
            LEFT JOIN matPieces ON prestations.IDcontrat = matPieces.pieIDnumPiece
            %s
            ORDER BY prestations.date
            ;""" % condition
        retour = self.DB.ExecuterReq(req,MsgBox="UTILS_Facturation.GetImpayes_2")
        recordset = self.DB.ResultatReq()

        # constitution des impayes dans dictVentilations
        for IDprestation, IDfamille, date, montant,label,nature,dateFacture,dateAvoir in recordset :
            if not IDprestation in self.dictVentilations[IDfamille]["impayes"]:
                self.dictVentilations[IDfamille]["impayes"][IDprestation] = {}
            dictImpayes = self.dictVentilations[IDfamille]["impayes"][IDprestation]
            if nature == None : nature = 'VTE'
            if nature == 'FAC':
                date = dateFacture
            elif nature == 'AVO':
                if montant > 0.0:
                    date = dateFacture
                else:
                    date = dateAvoir
            date = UTILS_Dates.DateEngEnDateDD(date)
            mois = date.month
            annee = date.year
            periode = str((annee, mois))+ " " + label
            if periode not in dictImpayes :
                dictImpayes[periode] = {}
                dictImpayes[periode][nature] = FloatToDecimal(0.0)
            if nature not in dictImpayes[periode]:
                dictImpayes[periode][nature] = FloatToDecimal(0.0)
            dictImpayes[periode][nature] += dictPrestVentilation[IDprestation]["montant"]
            dictImpayes[periode][nature] -= dictPrestVentilation[IDprestation]["regle"]

    # Alimente le fichier self.dictVentilations des paiements
    def GetVentilations(self):
        #appel des prestations
        condition = " WHERE prestations.IDprestation in ( %s ) "% str(self.lstIDprestations)[1:-1]
        req = """
            SELECT prestations.IDprestation, prestations.IDcompte_payeur, prestations.Date, prestations.montant, matPieces.pieNature, matPieces.pieDateFacturation, matPieces.pieDateAvoir
            FROM prestations
            LEFT JOIN matPieces ON prestations.IDcontrat = matPieces.pieIDnumPiece
            %s
            ORDER BY prestations.date
            ;""" % condition
        retour = self.DB.ExecuterReq(req,"GetVentilations appel prestations")
        if retour != "ok" :
            return
        recordset = self.DB.ResultatReq()
        # constitution de dictPrestations avec clé 'réglé' à zéro
        for IDprestation, IDcompte_payeur, date, montant,nature,dateFacture,dateAvoir in recordset :
            dictPrestations = self.dictVentilations[IDcompte_payeur]["prestations"]
            ok = True
            if montant == FloatToDecimal(0.0):
                ok = False
            if nature == None : nature = 'VTE'
            if ok :
                # détermine la date de prestation
                if nature == 'FAC':
                    dictPrestations[IDprestation]["date"] = dateFacture
                    nat = nature
                elif nature == 'AVO':
                    if montant > FloatToDecimal(0.0):
                        nat='FAC'
                        dictPrestations[IDprestation]["date"] = dateFacture
                    else:
                        nat='AVO'
                        dictPrestations[IDprestation]["date"] = dateAvoir
                else :
                    nat = nature
                    dictPrestations[IDprestation]["date"] = date

                dictPrestations[IDprestation]["montant"] = FloatToDecimal(montant)
                dictPrestations[IDprestation]["regle"] = FloatToDecimal(0.0)
                dictPrestations[IDprestation]["nature"] = nat

        #Appel des règlements affectés aux prestations
        condition = " WHERE ventilation.IDprestation in ( %s ) "% str(self.lstIDprestations)[1:-1]
        req = """
            SELECT ventilation.IDprestation, reglements.IDreglement, reglements.IDcompte_payeur, reglements.date, 
                    reglements.montant, modes_reglements.label, ventilation.montant
            FROM ventilation
            INNER JOIN reglements ON (ventilation.IDreglement = reglements.IDreglement )
                                 AND (ventilation.IDcompte_payeur = reglements.IDcompte_payeur )
            LEFT JOIN modes_reglements ON reglements.IDmode = modes_reglements.IDmode
            %s
            ORDER BY reglements.date
            ;""" % condition
        retour = self.DB.ExecuterReq(req,MsgBox="UTILS_Facturation GetVentilations appel règlements 1")
        if retour != "ok" :
            return
        recordset = self.DB.ResultatReq()
        # affectation des règlements aux prestations
        for IDprestation, IDreglement, IDcompte_payeur, date, montant, modeReglement, ventilation in recordset :
            dictPrestations = self.dictVentilations[IDcompte_payeur]["prestations"]
            dictPrestations[IDprestation]["regle"] += FloatToDecimal(ventilation)
            """
            if modeReglement == None : modeReglement = "REGL"
            mode = GestionDB.Decod(modeReglement)
            if not dictAllReglements.has_key(IDcompte_payeur):
                dictAllReglements[IDcompte_payeur]={}
            if not dictAllReglements[IDcompte_payeur].has_key(IDreglement):
                dictAllReglements[IDcompte_payeur][IDreglement]={"ventilation":FloatToDecimal(0.0)}
            dictAllReglements[IDcompte_payeur][IDreglement]["dateReglement"] = date
            dictAllReglements[IDcompte_payeur][IDreglement]["montant"] = FloatToDecimal(montant)
            dictAllReglements[IDcompte_payeur][IDreglement]["ventilation"] -= FloatToDecimal(ventilation)
            dictAllReglements[IDcompte_payeur][IDreglement]["mode"] = mode[:4]"""
            
        # complète les ventilations par les règlements affectés aux prestations ou libres de ventilation
        if len(self.lstIDprestations) > 0:
            self.GetReglementsAffectes()
        self.GetImpayes()
        self.GetReglementsLibres()
        #fin GetVentilations

    # Infos connexes necessaires à toutes les pages
    def GetInfos(self):
        # Récupération des individus
        if len(self.lstIDindividus) == 1:
            condition = "WHERE IDindividu in (%s) " % str(self.lstIDindividus[0])
        elif len(self.lstIDindividus) == 0:
            condition = "WHERE IDindividu = 0 "
        else:
            condition = "WHERE IDindividu in ("
            for ind in self.lstIDindividus:
                condition += str(ind) +','
            condition = condition[:-1]+") "

        req = """SELECT IDindividu, IDcivilite, nom, prenom, date_naiss, adresse_auto, rue_resid, cp_resid, ville_resid
        FROM individus %s;""" % condition
        retour = self.DB.ExecuterReq(req,MsgBox="ExecuterReq")
        if retour != "ok" :
            Msg = GestionDB.Messages()
            Msg.Box( message= retour)
            Msg.Close()
            return None
        listeIndividus = self.DB.ResultatReq()
        for IDindividu, IDcivilite, nom, prenom, date_naiss, adresse_auto, rue_resid, cp_resid, ville_resid in listeIndividus :

            self.dictIndividus[IDindividu] = {"IDcivilite":IDcivilite, "nom":nom, "prenom":prenom, "date_naiss":date_naiss,
                                              "adresse_auto":adresse_auto, "rue_resid":rue_resid, "cp_resid":cp_resid,
                                              "ville_resid":ville_resid}

        # Récupération de tous les messages familiaux à afficher
        req = """SELECT IDmessage, IDcategorie, date_parution, priorite, IDfamille, nom, texte
        FROM messages
        WHERE afficher_facture=1 AND IDfamille IS NOT NULL;"""
        retour = self.DB.ExecuterReq(req,MsgBox="ExecuterReq")
        if retour != "ok" :
            msg = GestionDB.Messages()
            msg.Box("Problème sql", retour)
            return
        listeMessagesFamiliaux = self.DB.ResultatReq()
        for IDmessage, IDcategorie, date_parution, priorite, IDfamille, nom, texte in listeMessagesFamiliaux :
            date_parution = UTILS_Dates.DateEngEnDateDD(date_parution)
            if (IDfamille in self.dictMessageFamiliaux) == False :
                self.dictMessageFamiliaux[IDfamille] = []
            self.dictMessageFamiliaux[IDfamille].append({"IDmessage":IDmessage, "IDcategorie":IDcategorie, "date_parution":date_parution, "priorite":priorite, "nom":nom, "texte":texte})

        # Récupération des infos sur l'organisme
        req = """SELECT nom, rue, cp, ville, tel, fax, mail, site, num_agrement, num_siret, code_ape
        FROM organisateur
        WHERE IDorganisateur=1;"""
        retour = self.DB.ExecuterReq(req,MsgBox="ExecuterReq")
        if retour != "ok" :
            msg = GestionDB.Messages()
            msg.Box("Problème sql", retour)
            return
        listeDonnees = self.DB.ResultatReq()
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

        # Get noms Titulaires
        self.dictNomsTitulaires = UTILS_Titulaires.GetTitulaires(self.lstIDfamilles)

        # Recherche des infos activités numéros d'agréments, dates, nom
        if len(self.lstIDactivites) > 0:
            req = """
                SELECT activites.IDactivite, activites.nom, activites.abrege, activites.date_debut, 
                        activites.date_fin, agrements.agrement
                FROM activites 
                LEFT JOIN agrements ON activites.IDactivite = agrements.IDactivite
                WHERE activites.IDactivite in ( %s ) ;""" % str(self.lstIDactivites)[1:-1]
            retour = self.DB.ExecuterReq(req, MsgBox="UTILS_Facturation.GetInfos_1")
            if retour != "ok" :
                msg = GestionDB.Messages()
                msg.Box("Problème sql", retour)
                return
            recordset = self.DB.ResultatReq()
            for IDactivite, nom, abrege, date_debut, date_fin, agrement in recordset:
                self.dictActivites[IDactivite] = {"agrement": agrement,
                                                  "date_debut": date_debut,
                                                  "date_fin": date_fin,
                                                  "nom":nom,
                                                  "abrege": abrege}

            # recherche des noms des groupes
            req = """SELECT IDgroupe, nom
            FROM groupes
            WHERE IDactivite in ( %s ) ;""" % str(self.lstIDactivites)[1:-1]
            retour = self.DB.ExecuterReq(req,MsgBox="ExecuterReq")
            if retour != "ok" :
                msg = GestionDB.Messages()
                msg.Box("Problème sql", retour)
                return
            recordset = self.DB.ResultatReq()
            for IDgroupe, nom in recordset:
                self.dictGroupes[IDgroupe] = {"nom": nom}

        # Récupération des questionnaires
        self.Questionnaires = ChampsEtReponses(type="famille")

    # Recherche des prestations recomposées par les lignes de toutes les pièces
    def GetPieces(self):
        champsLignes=["IDnumPiece","label","quantite", "prixUnit", "montant", "typeLigne"]

        # prestation-piece sans le détail des lignes de pièce
        champsPieces=["IDnumPiece","IDinscription","IDcompte_payeur","nature","noFacture","dateModif",
                      "IDactivite","IDgroupe","tarif","IDinscription","IDindividu",
                      "IDfamille","prixTranspAller","prixTranspRetour","IDtranspAller","IDtranspRetour"]

        conditions = " WHERE matPieces.pieIDnumPiece in (" + str(self.lstIDpieces)[1:-1] + ") "
        req =   """            
                SELECT pieIDnumPiece, pieIDinscription, pieIDcompte_payeur, pieNature, pieNoFacture, pieDateModif, 
                        pieIDactivite, pieIDgroupe, pieIDcategorie_tarif, pieIDinscription, pieIDindividu, 
                        pieIDfamille, piePrixTranspAller, piePrixTranspRetour, pieIDtranspAller, pieIDtranspRetour
                FROM matPieces 
                %s
                ORDER BY matPieces.pieIDnumPiece
                ;""" % conditions
        retour = self.DB.ExecuterReq(req,MsgBox="ExecuterReq")
        if retour != "ok" :
            msg = GestionDB.Messages()
            msg.Box("Problème sql", retour)
            return
        recordset = self.DB.ResultatReq()

        lstRecordset = RecordsetToListe(recordset)

        # ajoute la pièce dans self.dictPieces
        for piece in lstRecordset:
            IDpiece = piece[0]
            dicPiece = {"lstLignes":[],"dictTransport":{},"mttPiece": FloatToDecimal(0.0)}
            i = 0
            # alimente le dictionnaire de la piece
            for champ in champsPieces:
                dicPiece[champ] = piece[i]
                i +=1

            # Ajout du transport dans la ligne
            dictAjoutTransport = GestionInscription.DictTrack(champsPieces,piece)
            if dictAjoutTransport['prixTranspAller']  == None :
                dictAjoutTransport['prixTranspAller']  = FloatToDecimal(0.0)
                dictAjoutTransport['IDtranspAller']  = 0
            if dictAjoutTransport['prixTranspRetour'] == None :
                dictAjoutTransport['prixTranspRetour'] = FloatToDecimal(0.0)
                dictAjoutTransport['IDtranspRetour'] = 0
            dictAjoutTransport["label"] = ''
            dictAjoutTransport["montant"] = FloatToDecimal(0.0)
            dictAjoutTransport["prixUnit"] = FloatToDecimal(0.0)
            dictAjoutTransport["tva"] = FloatToDecimal(0.0)
            dictAjoutTransport["deductions"] = []

            # composition du libelle composé des transports aller et retour
            ligneTransp = []
            if dictAjoutTransport["IDactivite"] != 0:
                dateDebut = GestionArticle.DebutOuvertures(self.DB,dictAjoutTransport["IDactivite"],dictAjoutTransport["IDgroupe"])
                dateFin = GestionArticle.FinOuvertures(self.DB,dictAjoutTransport["IDactivite"],dictAjoutTransport["IDgroupe"])
                record = []
                champsTransports = ["IDtransport","categorie","dateDepart","nomDepart","nomArrivee","arretDep","arretArr"]
                if dictAjoutTransport['IDtranspAller'] != 0 or dictAjoutTransport['IDtranspRetour'] != 0 :
                    #recherche par les ID stockés dans la pièce
                    req = """SELECT transports.IDtransport, transports.categorie, transports.depart_date, 
                            transports_lieux.nom, transports_lieux_1.nom, transports_arrets.nom, transports_arrets_1.nom
                            FROM (((transports 
                            LEFT JOIN transports_lieux ON transports.depart_IDlieu = transports_lieux.IDlieu) 
                            LEFT JOIN transports_lieux AS transports_lieux_1 ON transports.arrivee_IDlieu = transports_lieux_1.IDlieu) 
                            LEFT JOIN transports_arrets ON transports.depart_IDarret = transports_arrets.IDarret) 
                            LEFT JOIN transports_arrets AS transports_arrets_1 ON transports.arrivee_IDarret = transports_arrets_1.IDarret
                            WHERE   transports.IDindividu = %d AND transports.IDtransport IN (%d,%d)
                            ORDER BY transports.depart_date;
                        """ % (dictAjoutTransport["IDindividu"], Nz(dictAjoutTransport['IDtranspAller']), Nz(dictAjoutTransport['IDtranspRetour']))
                    retour = self.DB.ExecuterReq(req,MsgBox="ExecuterReq")
                    if retour != "ok" :
                        msg = GestionDB.Messages()
                        msg.Box(titre= "UTILS_Facturation.SELECT transports",message = retour)
                        return None
                    record = self.DB.ResultatReq()
                    if len(record) < 1:
                        #recherche par les dates car anomalie sur les ID
                        #mais PB de between on prend tous et on filtre après!
                        req = """SELECT transports.IDtransport, transports.categorie, transports.depart_date, 
                                transports_lieux.nom, transports_lieux_1.nom, transports_arrets.nom, transports_arrets_1.nom
                                FROM (((transports 
                                LEFT JOIN transports_lieux ON transports.depart_IDlieu = transports_lieux.IDlieu) 
                                LEFT JOIN transports_lieux AS transports_lieux_1 ON transports.arrivee_IDlieu = transports_lieux_1.IDlieu) 
                                LEFT JOIN transports_arrets ON transports.depart_IDarret = transports_arrets.IDarret) 
                                LEFT JOIN transports_arrets AS transports_arrets_1 ON transports.arrivee_IDarret = transports_arrets_1.IDarret
                                WHERE   transports.IDindividu = %d
                                ORDER BY transports.depart_date;
                            """ % (dictAjoutTransport["IDindividu"])
                        retour = self.DB.ExecuterReq(req,MsgBox="ExecuterReq")
                        if retour != "ok" :
                            msg = GestionDB.Messages()
                            msg.Box(titre= "UTILS_Facturation.SELECT transports 2",message = retour)
                            return None
                        record2 = self.DB.ResultatReq()
                        #élargissement de la plage de date pour récupérer les transports sans englober des trajets d'autres camps
                        dDebut = dateDebut - datetime.timedelta(days= 1)
                        dFin = dateFin + datetime.timedelta(days= 1)
                        for voyage in record2:
                            dDep   = voyage[champsTransports.index("dateDepart")]
                            if (dDep >= str(dDebut)) and (dDep <= str(dFin) ):
                                record.append(voyage)
                #composition des labels trajets
                ft = FloatToDecimal
                if len(record)>0:
                    # des enregistrements table 'transport' ont été identifiés
                    dictAjoutTransport["lprixUnit"] = Nz(dictAjoutTransport["prixTranspAller"]) + Nz(dictAjoutTransport["prixTranspRetour"])
                    dictAjoutTransport["ordre"] = 9999
                    dictAjoutTransport["IDnumLigne"] = 9999
                    dictAjoutTransport["quantite"] = 1
                    dictAjoutTransport["typeLigne"] = ""
                    texte = ""
                    ar = ""
                    if len(record) > 1:
                        ar = "aller: "
                    for voyage in record:
                        dDep   = voyage[champsTransports.index("dateDepart")]
                        cat    = voyage[champsTransports.index("categorie")]
                        nomDep = voyage[champsTransports.index("nomDepart")]
                        nomArr = voyage[champsTransports.index("nomArrivee")]
                        arretDep = voyage[champsTransports.index("arretDep")]
                        arretArr = voyage[champsTransports.index("arretArr")]

                        if cat == "" : cat = None
                        if nomDep == "" : nomDep = None
                        if nomArr == "" : nomArr = None
                        if nomDep == nomArr: nomArr = None
                        if arretDep == "" : arretDep = None
                        if arretArr == "" : arretArr = None
                        if arretDep == arretArr: arretArr = None
                        if cat:
                            nomCat = CTRL_Saisie_transport.DICT_CATEGORIES[cat]["label"]
                            nomTrajet = ""
                            if nomDep :
                                nomTrajet += nomDep
                                if nomArr : nomTrajet += "-"+nomArr
                            elif nomArr : nomTrajet += nomArr
                            elif arretDep :
                                nomTrajet += arretDep
                                if arretArr : nomTrajet += "-"+arretArr
                            elif arretArr:
                                nomTrajet += arretArr

                            sep = ""
                            if len(texte) > 0 :
                                sep = "; "
                            if not dDep or dDep == str(dateDebut) or dDep == str(dateFin):
                                texte += sep + ar + nomCat + " " + nomTrajet
                            else:
                                texte += sep + ar +nomCat +  " le " + DateEngFr(dDep) + " " + nomTrajet
                            if len(record) > 1:
                                ar = "retour: "

                    dictAjoutTransport["label"] = texte
                    dictAjoutTransport["montant"] = ft(dictAjoutTransport["prixTranspAller"] + dictAjoutTransport["prixTranspRetour"])
                elif Nz(dictAjoutTransport["prixTranspAller"]) + Nz(dictAjoutTransport["prixTranspRetour"]) != FloatToDecimal(0.0) :
                    #cas d'un IDtransport à zéro mais des montants
                    dictAjoutTransport["label"] = 'Coût du transport'
                    dictAjoutTransport["montant"] = ft(Nz(dictAjoutTransport["prixTranspAller"]) + Nz(dictAjoutTransport["prixTranspRetour"]))

                if dictAjoutTransport["montant"] < -FloatToDecimal(0.01):
                    dictAjoutTransport["label"] = 'Transport correction de prix'

                #constitution de la ligne à ajouter pour le transport
                if not (dictAjoutTransport["label"] == ""):
                    dicPiece["dictTransport"] = dictAjoutTransport

            self.dictPieces[IDpiece] = dicPiece

        #complete les pieces par leurs lignes: reprend les champs de champsLignes
        req =   """
                SELECT matPieces.pieIDnumPiece, matPiecesLignes.ligLibelle, matPiecesLignes.ligQuantite, 
                    matPiecesLignes.ligPrixUnit, matPiecesLignes.ligMontant, matArticles.artCodeBlocFacture
                FROM (matPieces 
                LEFT JOIN matPiecesLignes ON matPieces.pieIDnumPiece = matPiecesLignes.ligIDnumPiece) 
                LEFT JOIN matArticles ON matPiecesLignes.ligCodeArticle = matArticles.artCodeArticle
                %s
                ORDER BY matPieces.pieIDnumPiece, matPiecesLignes.ligIDnumLigne
                ;""" % conditions
        retour = self.DB.ExecuterReq(req,MsgBox="ExecuterReq")
        if retour != "ok" :
            msg = GestionDB.Messages()
            msg.Box("Problème sql", retour)
            return
        recordset = self.DB.ResultatReq()

        # Balayage des lignes de toutes les pièces à regrouper par pièce
        for ligne in recordset:
            IDpiece = ligne[0]
            dictLigne = {"tva": FloatToDecimal(0.0), "deductions":[]}
            ix = 0
            for champ in champsLignes:
                val = ligne[ix]
                # Gestion des nombres
                if (ix >= champsLignes.index("quantite")) and (ix <= champsLignes.index("montant")):
                    if not val: val = 0.0
                    val = FloatToDecimal(val)
                dictLigne[champ] = val
                ix +=1
            self.dictPieces[IDpiece]["lstLignes"].append(dictLigne)
            self.dictPieces[IDpiece]["mttPiece"] += FloatToDecimal(dictLigne["montant"])
        return
        #fin GetPieces

    def GetSoldes(self):
        # Recherche les soldes_du de chaque famille, retourne un dictionnaire
        for famille in self.lstIDfamilles:
            self.dictSoldes[famille] = {'prestations':0.0,'reglements':0.0}
        for table in ('prestations','reglements'):
            req = """
                SELECT IDcompte_payeur, SUM(montant)
                FROM %s
                WHERE (IDcompte_payeur In ( %s ))
                GROUP BY IDcompte_payeur
                ;""" % (table, str(self.lstIDfamilles)[1:-1])
            retour = self.DB.ExecuterReq(req,MsgBox="UTILS_Facturation.GetSoldes_%s"%table)
            if retour != "ok" :
                return
            recordset = self.DB.ResultatReq()
            for IDfamille, montant in recordset:
                self.dictSoldes[IDfamille][table] = montant
        return self.dictSoldes

    # doc ----------------------------- Structure de dictDonnees -------------------------------------------------------
    """
    [IDfamille]
        [IDpage] as dictDonPage
            [IDindividu1] as dictDonIndividu
                [(IDactivite,IDgroupe,IDtarif)] as dictDonActivite
                    [IDpiece] = dictDonPiece
            [IDindividu2...]...

            ["IDfacture"] int
            ["nature"] str
            ["lstIDindividus"] lst [IDindividu,...]
            ["lstIDpieces"] lst [IDpiece,...]
            ["lstIDactivite"] lst [IDactivite,...]
            ["lstIDprestations"] lst [IDprestation,...]
            ["date_echeance"] str
            ["date_edition"] str
            ["montant"] decimal
            ["ventilation"] decimal
            ["facturesNo"]
    """

    # doc ----------------------------- Structure de dictVentilations --------------------------------------------------
    """
    [IDfamille]
        ["prestations"]
            [IDprestation] as dictPrestation
                ["nature"] str
                ["date"] str
                ["montant"] decimal
                ["regle"] decimal
                ["reglAffectes"]
                    [IDreglement] as dictReglement
                        ["montant"] decimal
                        ["ventilation"] decima
                        [...]
        ["impayes"]
            [IDprestation] as dictPrestation
                [(annee,mois)]
                    [nature] = montant decimal
        ["reglementsLibres"] as dictReglLibres
            [IDreglement] as dictRegl
                ["montant"] decimal
                ["ventilation"] decimal
                ...etc
    """

    # Composition des listes de base pour self
    def ConstruitSquelette(self, listePieces, listeFactures):
        self.dictDonnees = {}
        self.dictPieces = {}
        self.dictVentilations = {}
        self.dictAutresAffect = {}
        self.dictIndividus = {}
        self.dictSoldes = {}
        self.lstIDindividus = []
        self.lstIDactivites = []
        self.lstIDpieces = []
        self.lstIDprestations = [] # pour alimenter les Ventilations
        self.lstIDfamilles = []
        lstNoFactAvo = [] # stocke temporairement la liste qui permet d'étendre la recherche des pièces aux conjointes

        if len(listeFactures) + len(listePieces) == 0:
            return False

        # -------- fonction qui alimente les clés dictVentilations, dictDonnees -----------
        def ajoutSquelette(retourReq):
            ix = 0 # indice du record dans recordset
            for IDpiece,IDfamille,IDprestation,IDindividu,IDactivite,IDgroupe,IDtarif,nature,noFacture,noAvoir,\
                facturesNo,date_edition, date_echeance, IDfacture in retourReq:

                # alimente les listes générales qui seront reprises pour alimenter les dictionnaires
                listes = [self.lstIDpieces,self.lstIDfamilles,self.lstIDprestations,self.lstIDindividus,self.lstIDactivites]
                for ixx in range(len(listes)):
                    val = retourReq[ix][ixx]
                    if val and (not val in listes[ixx]):
                        listes[ixx].append(val)
                ix += 1        
                                    
                # Alimente dictVentilations eu égard à sa structure plus complexe
                if IDfamille not in self.dictVentilations:
                    self.dictVentilations[IDfamille] = {"prestations":{},"impayes":{}, "reglementsLibres":{}}
                if IDprestation and (IDprestation not in self.dictVentilations[IDfamille]["prestations"]):
                    nat = None
                    if facturesNo and facturesNo == noFacture:
                        nat = "FAC"
                    if facturesNo and facturesNo == noAvoir:
                        nat = "AVO"
                    self.dictVentilations[IDfamille]["prestations"][IDprestation] = {"nature":nat,
                                                                                     "montant": FloatToDecimal(0.0),
                                                                                     "regle": FloatToDecimal(0.0),
                                                                                     "reglAffectes": {}}
               
                #si pas de no facture on force un pseudo noFacture pour regrouper les pièces par nature
                tplDevis = ("DEV", "RES", "COM")
                if nature in tplDevis:
                    IDpage = tplDevis.index(nature)
                    facturesNo = 0
                elif facturesNo == noFacture and (nature in ("FAC", "AVO")):
                    IDpage = facturesNo
                    nature = "FAC"
                elif facturesNo == noAvoir  and (nature == "AVO"):
                    IDpage = facturesNo
                else:
                    raise Exception("Pb Piece %d!!! nature %s, noFacture %d, noAvoir %d, facture %d"%(IDpiece, nature,noFacture,
                                                                                            noAvoir, facturesNo))

                # Alimente DictDonnees niveau famille
                if IDfamille not in self.dictDonnees:
                    self.dictDonnees[IDfamille] = {}

                # niveau no facture (page)
                def ajoutPage(IDpage):
                    if IDpage not in self.dictDonnees[IDfamille]:
                        # création du dictDonPage
                        dictDonPage = {"nature": nature,
                                       "date_edition": date_edition,
                                       "date_echeance": date_echeance,
                                       "facturesNo": facturesNo,
                                       "IDfacture": IDfacture}
                        for cle in ["lstIDpieces","lstIDprestations","lstIDindividus","lstIDactivites"]:
                            dictDonPage[cle] = []
                        self.dictDonnees[IDfamille][IDpage] = dictDonPage
                    # listes favorisant la synthèse au niveau de la page
                    if IDpiece not in self.dictDonnees[IDfamille][IDpage]["lstIDpieces"]:
                        self.dictDonnees[IDfamille][IDpage]["lstIDpieces"].append(IDpiece)
                    if IDprestation and (IDprestation not in self.dictDonnees[IDfamille][IDpage]["lstIDprestations"]):
                        self.dictDonnees[IDfamille][IDpage]["lstIDprestations"].append(IDprestation)
                    if IDindividu not in self.dictDonnees[IDfamille][IDpage]["lstIDindividus"]:
                        self.dictDonnees[IDfamille][IDpage]["lstIDindividus"].append(IDindividu)
                    if IDactivite not in self.dictDonnees[IDfamille][IDpage]["lstIDactivites"]:
                        self.dictDonnees[IDfamille][IDpage]["lstIDactivites"].append(IDactivite)

                    # niveau individu
                    if IDindividu not in self.dictDonnees[IDfamille][IDpage]:
                        self.dictDonnees[IDfamille][IDpage][IDindividu] = {"montant": FloatToDecimal(0.0)}

                    # niveau activite, groupe, tarif
                    cle = (IDactivite,IDgroupe,IDtarif)
                    if cle not in self.dictDonnees[IDfamille][IDpage][IDindividu]:
                        self.dictDonnees[IDfamille][IDpage][IDindividu][cle] = {}


                    # niveau piece
                    if IDpiece not in self.dictDonnees[IDfamille][IDpage][IDindividu][cle]:
                        self.dictDonnees[IDfamille][IDpage][IDindividu][cle][IDpiece] = {}


                ajoutPage(IDpage)

                # ajoute la partie avoir
                if nature in ("FAC","AVO"):
                    if noAvoir:
                        if not noAvoir in lstNoFactAvo:
                            lstNoFactAvo.append(noAvoir)
                    if not facturesNo in lstNoFactAvo:
                        lstNoFactAvo.append(facturesNo)

        # Premier appel selon la listePieces  fournie
        conditionWhere = ""

        #recherche des éléments de base de la piece
        if len(listePieces) > 0:
            conditionWhere ="(matPieces.pieIDnumPiece In (%s)) "% str(listePieces)[1:-1]
            req = """
                SELECT pieIDnumPiece, pieIDfamille, pieIDprestation, pieIDindividu, 
                        pieIDactivite, pieIDgroupe, pieIDcategorie_tarif, pieNature, pieNoFacture, pieNoAvoir,
                        Null, pieDateModif, pieDateEcheance,Null
                FROM matPieces 
                WHERE %s        
            ;""" % conditionWhere
            retour = self.DB.ExecuterReq(req, MsgBox="UTILS_facturation.ConstruitListe")
            retourReq = self.DB.ResultatReq()
            # Sépare les devis des factures
            ixNat,ixFact, ixAvo = 7, 8, 8  # position des champs dans le record
            lstDevis = []
            for record in retourReq:
                if record[ixNat] in ("DEV", "RES", "COM"):
                    lstDevis.append(record)
                elif record[ixFact] > 0:
                    lstNoFactAvo.append(record[ixFact])
                    # a la fois facture et avoir
                    if record[ixAvo] > 0:
                        lstNoFactAvo.append(record[ixAvo])
                # avoir seulement pas facture (cas impossible à ce jour)
                elif record[ixAvo] > 0:
                    lstNoFactAvo.append(record[ixAvo])
                else:
                    raise Exception("pieIDnumPiece '%d' nature '%s': type facture sans numéro facture"%(record[0],record[ixNat]))

            # ajoute les non-factures dans le squelette
            ajoutSquelette(lstDevis)

        # listefacture fournie contient des IDfacture : les transpose en no utilisés dans les pièces
        if len(listeFactures) > 0:
            #recherche des éléments de base dans factures
            req = """
                SELECT factures.numero
                FROM factures
                WHERE (factures.IDfacture In ( %s ))
                ;""" % str(listeFactures)[1:-1]
            retour = self.DB.ExecuterReq(req, MsgBox="UTILS_facturation.ConstruitListe.2")
            retourReq = self.DB.ResultatReq()
            for (facturesNo,) in retourReq:
                if not (facturesNo in lstNoFactAvo):
                    lstNoFactAvo.append(facturesNo)

        # deuxième appel à partir des no : étend aux pièces avec numeroFacture ou Avoir commun
        if len(lstNoFactAvo) > 0:
            conditionWhere = """(matPieces.pieNoFacture In ( %s ))  
                            OR (((matPieces.pieNoAvoir) In ( %s )))"""% (str(lstNoFactAvo)[1:-1],
                                                                         str(lstNoFactAvo)[1:-1])

        req = """
            SELECT matPieces.pieIDnumPiece, matPieces.pieIDfamille, prestations.IDprestation, matPieces.pieIDindividu,
                    matPieces.pieIDactivite, matPieces.pieIDgroupe, matPieces.pieIDcategorie_tarif, matPieces.pieNature, 
                    matPieces.pieNoFacture, matPieces.pieNoAvoir,
                    factures.numero, pieDateFacturation, pieDateEcheance, factures.IDfacture
            FROM (factures 
            LEFT JOIN prestations ON factures.IDfacture = prestations.IDfacture) 
            LEFT JOIN matPieces ON prestations.IDcontrat = matPieces.pieIDnumPiece
            WHERE %s         
            GROUP BY matPieces.pieIDnumPiece, matPieces.pieIDfamille, prestations.IDprestation, 
                    matPieces.pieIDindividu, matPieces.pieIDgroupe, matPieces.pieIDcategorie_tarif, 
                    matPieces.pieNature, matPieces.pieNoFacture, matPieces.pieNoAvoir,
                    factures.numero, factures.date_edition
        ;""" % conditionWhere
        retour = self.DB.ExecuterReq(req, MsgBox="UTILS_facturation.ConstruitListe3")
        retourReq = self.DB.ResultatReq()
        ajoutSquelette(retourReq)
        return True
        #fin ConstruitSquelette

    def Impression(self, listeFactures=[], listePieces=[], nomDoc=None,afficherDoc=True,
                   dictOptions=None, repertoire= None , repertoireTemp=False,**kwd):
        """ Impression des factures à partie de trois listes possibles """
        self.DB = GestionDB.DB()

        # Récupération des paramètres d'affichage
        if dictOptions == None :
            dlg = DLG_Apercu_facture.Dialog(None,
                        titre=_("Sélection des paramètres de la facture"),
                        intro=_("Sélectionnez ici les paramètres d'affichage de la facture à envoyer par Email."))
            dlg.bouton_ok.SetImageEtTexte("Images/32x32/Valider.png", _("Ok"))
            if dlg.ShowModal() == wx.ID_OK:
                dictOptions = dlg.GetParametres()
                dlg.Destroy()
            else :
                self.DB.Close()
                return False

        if not nomDoc:
            # recherche de la première famille
            mess = 'UTILS_Facturation.Impression'
            if len(listePieces) > 0:
                lstChamps = ["pieIDcompte_payeur", ]
                table = "matPieces"
                condition = "pieIDnumPiece = %d"%listePieces[0]
            elif len(listeFactures) > 0:
                lstChamps = ["IDcompte_payeur", ]
                table = "factures"
                condition = "IDfacture = %d"%listeFactures[0]
            # appel du nom de la famille
            try:
                ret = self.DB.ReqSelect(table,condition,mess,lstChamps=lstChamps)
                ret = self.DB.ResultatReq()
                nomDoc = self.DB.GetNomFamille(ret[0][0], first="nom")
                nomDoc = fp.NoPunctuation(nomDoc)
            except: pass
            now = str(datetime.datetime.strftime(datetime.datetime.now(),
                                                 "%Y-%m-%d %Hh%M %S%f"))[:22]
            # l'unicitié du nom de fichier est obtenue par les secondes et millisecondes
            nomDoc = "%s %s"%(nomDoc ,now)

        # ajout du chemin devant le nom
        if not nomDoc.endswith(".pdf"):
            nomDoc = "%s.pdf" %(nomDoc)
        if not repertoire:
            nomDoc = UTILS_Fichiers.GetRepTemp(nomDoc)

        self.dictChampsFusion = {}

        # imprimer les factures si pièce de type AVO
        self.impFacAvo = 1
        if "imprimer_factures" in dictOptions:
            self.impFacAvo = dictOptions["imprimer_factures"]

        # Structurer les données nécessaires aux listes fournies, étendue aux factures concernées
        ret = self.ConstruitSquelette(listePieces, listeFactures)
        if len(self.dictDonnees) == 0:
            return False

        # alimenter le dictPieces et les autres dictionnaires complémentaires
        dlgAttente = PBI.PyBusyInfo(_("Recherche des données générales..."),
                                    parent=None, title=_("Veuillez patienter..."),
                                    icon=wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Logo.png"), wx.BITMAP_TYPE_ANY))
        self.GetPieces()
        self.GetInfos()
        self.GetVentilations()
        self.GetSoldes()
        del dlgAttente

        # Récupération des données
        dictToPdf = self.GetDonnees(dictOptions)
        self.DB.Close()
        if len(dictToPdf) == 0 :
            return False

        # Création des PDF à l'unité
        def CreationPDFeclates(repertoireCible=""):
            if repertoireCible in (None, "",''):
                if "repertoire_copie" in dictOptions:
                    repertoireCible = dictOptions["repertoire_copie"]
    
            dictCheminsPdf = {}
            dlgAttente = PBI.PyBusyInfo(_("Génération des factures à l'unité au format PDF..."), parent=None, title=_("Veuillez patienter..."), icon=wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Logo.png"), wx.BITMAP_TYPE_ANY))
            try :
                wx.Yield() 
            except :
                pass
            try :
                index = 0
                for noFact, dictToPage in dictToPdf.items() :
                    if dictToPage["select"] == True :
                        num_facture = dictToPage["num_facture"]
                        nomTitulaires = Supprime_accent(dictToPage["nomSansCivilite"])
                        nomTitulaires = fp.NoPunctuation(nomTitulaires)
                        nomFichier = _("Facture %d - %s") % (num_facture, nomTitulaires)
                        cheminFichier = "%s/%s.pdf" % (repertoireCible, nomFichier)
                        dictToPdfTemp = {noFact : dictToPage}
                        self.EcritStatusbar(_("Edition de la facture %d/%d : %s") % (index, len(dictToPdf), nomFichier))
                        UTILS_Impression_facture.Impression(dictToPdfTemp, dictOptions, IDmodele=dictOptions["IDmodele"],
                                                            ouverture=False, nomFichier=cheminFichier, mode = None)
                        dictCheminsPdf[noFact] = cheminFichier
                        index += 1
                self.EcritStatusbar("")
                del dlgAttente
                return dictCheminsPdf
            except Exception as err:
                del dlgAttente
                traceback.print_exc(file=sys.stdout)
                dlg = wx.MessageDialog(None, _("Désolé, le problème suivant a été rencontré dans l'édition des factures : \n\n%s") % err, _("Erreur"), wx.OK | wx.ICON_ERROR)
                dlg.ShowModal()
                dlg.Destroy()
                return False
            #fin CreationPDFeclates
        
        # Répertoire souhaité par l'utilisateur
        if repertoire not in (None, "",'') :
            resultat = CreationPDFeclates(repertoire)
            if resultat == False :
                return False

        # Répertoire TEMP (pour Emails)
        dictCheminsPdf = {}
        if repertoireTemp == True :
            dictCheminsPdf = CreationPDFeclates("Temp")
            if dictCheminsPdf == False :
                return False

        # Fabrication du PDF global
        if repertoireTemp == False :
            dlgAttente = PBI.PyBusyInfo(_("Création du PDF des factures..."), parent=None, title=_("Veuillez patienter..."), icon=wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Logo.png"), wx.BITMAP_TYPE_ANY))
            try :
                wx.Yield() 
            except :
                pass
            self.EcritStatusbar(_("Création du PDF des factures en cours... veuillez patienter..."))
            try :
                # ------------------------------------Lancement de l'impression ----------------------------------------
                UTILS_Impression_facture.Impression(dictToPdf, dictOptions, IDmodele=dictOptions["IDmodele"],
                                                     ouverture=afficherDoc, nomFichier=nomDoc, mode=None)
                self.EcritStatusbar("")
                del dlgAttente
            except Exception as err:
                del dlgAttente
                traceback.print_exc(file=sys.stdout)
                err = str(err)
                dlg = wx.MessageDialog(None, _("Désolé, le problème suivant a été rencontré dans l'édition des factures : \n\n%s") % err, _("Erreur"), wx.OK | wx.ICON_ERROR)
                dlg.ShowModal()
                dlg.Destroy()
                return False
        # pointeurs d'impression
        self.DB = GestionDB.DB()
        req = """SELECT pieIDnumPiece, pieNature, pieEtat, pieCommentaire
                FROM matPieces
                WHERE  pieIDnumPiece in ( %s ) ;""" % str(self.lstIDpieces)[1:-1]
        retour = self.DB.ExecuterReq(req,MsgBox="UTILS_Facturation.Pointeurs")
        if retour == "ok" :
            retour = self.DB.ResultatReq()
            if len(retour) > 0:
                for IDnumPiece,nature,etat, commentaire in retour:
                    commentaire = GestionInscription.AjoutCom(commentaire,"Impression")
                    ix = ['DEV','RES','COM','FAC','AVO'].index(nature)
                    etat = etat[:ix]+"2"+etat[ix+1:]
                    self.DB.ReqMAJ('matPieces',[('pieEtat',etat),('pieCommentaire',commentaire)],
                                   'pieIDnumPiece',IDnumPiece,MsgBox = 'UTILS_Facturation.MAJpointeurs')
        self.DB.Close()
        return self.dictChampsFusion, dictCheminsPdf
        #fin Impression

def SuppressionFacture(listeIDFactures=[]):
    """ Suppression d'une facture façon Noethys, suppose ensuite d'entrer en facturation pour retouver de la cohérence """
    dlgAttente = PBI.PyBusyInfo(_("Suppression des factures en cours..."), parent=None, title=_("Veuillez patienter..."), icon=wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Logo.png"), wx.BITMAP_TYPE_ANY))
    wx.Yield()

    DB = GestionDB.DB()
    for IDfacture in listeIDFactures :
        DB.ReqMAJ("prestations", [("IDfacture", None),], "IDfacture", IDfacture)
        DB.ReqDEL("factures", "IDfacture", IDfacture)

    DB.Close() 
    del dlgAttente
    return True

if __name__ == '__main__':
    app = wx.App(0)
    listePieces = [19300]
    listeIDfactures = []
    dictOptions =  {'inversion_solde': True, 'largeur_colonne_date': 50, 'texte_conclusion': '',
                    'image_signature': '', 'taille_texte_prestation': 7,
                    'afficher_avis_prelevements': True, 'taille_texte_messages': 7, 'afficher_qf_dates': True,
                    'taille_texte_activite': 6, 'affichage_prestations': 0, 'affichage_solde': 0,
                    'afficher_coupon_reponse': True, 'taille_image_signature': 100, 'alignement_image_signature': 0,
                    'couleur_fond_conclusion': wx.Colour(255, 255, 255, 255), 'alignement_texte_introduction': 0,
                    'couleur_bord_conclusion': wx.Colour(255, 255, 255, 255),
                    'afficher_reglements': True, 'intitules': 0,
                    'integrer_impayes': True, 'taille_texte_introduction': 9,
                    'afficher_impayes': True,
                    'taille_texte_noms_colonnes': 5, 'texte_introduction': '', 'taille_texte_individu': 9,
                    'taille_texte_conclusion': 9, 'taille_texte_labels_totaux': 9, 'afficher_periode': False,
                    'couleur_bord_introduction': wx.Colour(255, 255, 255, 255), 'afficher_codes_barres': True,
                    'couleur_fond_introduction': wx.Colour(255, 255, 255, 255), 'taille_texte_titre': 19,
                    'taille_texte_periode': 8, 'IDmodele': 5, 'couleur_fond_2': wx.Colour(234, 234, 255, 255),
                    'afficher_titre': True, 'couleur_fond_1': wx.Colour(204, 204, 255, 255),
                    'largeur_colonne_montant_ht': 50, 'messages': [],
                    'memoriser_parametres': True, 'afficher_messages': True, 'largeur_colonne_montant_ttc': 70,
                    'taille_texte_montants_totaux': 10, 'alignement_texte_conclusion': 0,
                    'style_texte_introduction': 0, 'style_texte_conclusion': 0, 'repertoire_copie': '',
                    'largeur_colonne_montant_tva': 50}
    facturation = Facturation()
    retour = facturation.Impression(listePieces=listePieces, listeFactures= listeIDfactures, dictOptions=dictOptions,
                                    afficherDoc=True,repertoire=dictOptions["repertoire_copie"])
    app.MainLoop()
    # mettre un point d'arrêt pour voir le pdf
    print("fin")
