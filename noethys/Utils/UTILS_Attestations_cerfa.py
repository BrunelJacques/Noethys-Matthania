#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, Matthania
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS, JB
# Copyright:       (c) 2010-14 Ivan LUCAS, JB
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------


from Utils.UTILS_Traduction import _
import Chemins
import wx
import sys
import traceback
import FonctionsPerso as fp
import wx.lib.agw.pybusyinfo as PBI

from Utils import UTILS_Config
SYMBOLE = UTILS_Config.GetParametre("monnaie_symbole", "€")
MONNAIE_SINGULIER = UTILS_Config.GetParametre("monnaie_singulier", _("Euro"))
MONNAIE_DIVISION = UTILS_Config.GetParametre("monnaie_division", _("Centime"))

from Utils.UTILS_Decimal import FloatToDecimal as FloatToDecimal

from Data import DATA_Civilites as Civilites
DICT_CIVILITES = Civilites.GetDictCivilites()

import GestionDB
import FonctionsPerso
from Utils import UTILS_Titulaires
from Utils import UTILS_Questionnaires
from Utils import UTILS_Impression_attestation_cerfa
from Utils import UTILS_Dates
from Dlg import DLG_Apercu_attestation_fiscale
from Utils import UTILS_Conversion
from Utils import UTILS_Infos_individus
from Data import DATA_Civilites
DICT_CIVILITES = DATA_Civilites.GetDictCivilites()


class Attestations_fiscales():
    def __init__(self):
        """ Récupération de toutes les données de base """
        
        DB = GestionDB.DB()
            
        # Récupération des infos sur l'organisme
        req = """SELECT nom, rue, cp, ville, tel, fax, mail, site, num_agrement, num_siret, code_ape
        FROM organisateur
        WHERE IDorganisateur=1;""" 
        DB.ExecuterReq(req,MsgBox="UTILS_Attestations_cerfa")
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

        DB.Close()

    def EcritStatusbar(self, texte=""):
        try :
            topWindow = wx.GetApp().GetTopWindow() 
            topWindow.SetStatusText(texte)
        except : 
            pass

    def GetDonneesImpression(self, tracks=[], dictOptions={}):
        """ Impression des factures """
        dlgAttente = PBI.PyBusyInfo(_("Recherche des données..."), parent=None, title=_("Veuillez patienter..."), icon=wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Logo.png"), wx.BITMAP_TYPE_ANY))
        wx.Yield()
        lstIDfamilles = [int(x.IDfamille) for x in tracks]

        # Récupération des infos de base individus et familles
        self.infosIndividus = UTILS_Infos_individus.Informations(lstIDfamilles=lstIDfamilles)
        # Récupération des questionnaires
        self.Questionnaires = UTILS_Questionnaires.ChampsEtReponses(type="famille",lstIDfamilles=lstIDfamilles)

        dictDonnees = {}
        dictChampsFusion = {}

        ix = 0
        for track in tracks :
            IDfamille = track.IDfamille
            IDcerfa = track.IDcerfa
            if IDcerfa == 0:
                # numéro provisoire
                ix -=1
                IDcerfa = ix
            # Formatage du texte d'intro supprimé
            textIntro = ""
            if track.fin == track.debut:
                fin = None
            else:
                fin = track.fin

            # Mémorisation des données
            montant_lettres = ""
            mttLet = UTILS_Conversion.trad(track.montant_retenu, MONNAIE_SINGULIER, MONNAIE_DIVISION),
            if isinstance(mttLet, tuple):
                for mot in mttLet:
                    montant_lettres += mot
            else: montant_lettres = mttLet
            lstMtt = montant_lettres.split(MONNAIE_SINGULIER)
            montant_lettres = lstMtt[0] + MONNAIE_SINGULIER + "s\n" + lstMtt[1][1:].strip()

            dictDonnee = {
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

                "{IDFAMILLE}" : str(track.IDfamille),
                "{IDCOMPTE_PAYEUR}" : str(track.IDfamille),
                "{FAMILLE_NOM}" :  track.nomsTitulairesAvecCivilite,
                "{FAMILLE_RUE}" : track.rue_resid,
                "{FAMILLE_CP}" : track.cp_resid,
                "{FAMILLE_VILLE}" : track.ville_resid,
                
                "{DATE_EDITION_COURT}" : UTILS_Dates.DateDDEnFr(track.dateJour),
                "{DATE_EDITION_LONG}" : UTILS_Dates.DateComplete(track.dateJour),
                "{DATE_DEBUT}" : UTILS_Dates.DateDDEnFr(track.debut),
                "{DATE_FIN}" : UTILS_Dates.DateDDEnFr(fin),

                "{MONTANT_FACTURE}" : "%.2f %s" % (track.montant_retenu, SYMBOLE),
                "{MONTANT_FACTURE_LETTRES}" : montant_lettres,
                "{INTRO}" : str(track.IDcerfa),
                "{NUMERAIRE}" : "",
                "{AUTRES_MODES}" : "",
                "{CHEQUE}" : "",
                "{ESPECES}" : "",
                }
            # Mode de versement
            autre = True
            if "Chè" in track.labelModeRegl:
                autre = False
                dictDonnee["{NUMERAIRE}"]= "X"
                dictDonnee["{CHEQUE}"]= "X"
            if "Vir" in track.labelModeRegl:
                autre = False
                dictDonnee["{NUMERAIRE}"]= "X"
                dictDonnee["{CHEQUE}"]= "X"
            if "Prél" in track.labelModeRegl:
                autre = False
                dictDonnee["{NUMERAIRE}"]= "X"
                dictDonnee["{CHEQUE}"]= "X"
            if "Esp" in track.labelModeRegl:
                autre = False
                dictDonnee["{NUMERAIRE}"]= "X"
                dictDonnee["{ESPECES}"]= "X"
            if "Nat" in track.labelModeRegl or "nature" in track.labelDon:
                autre = False
                dictDonnee["{AUTRES_MODES}"]= "X                 en nature"
            if autre:
                dictDonnee["{AUTRES_MODES}"]="X"

            # Ajoute les infos de base familles
            dictDonnee.update(self.infosIndividus.GetDictValeurs(mode="famille", ID=IDfamille, formatChamp=True))

            # Ajoute les réponses des questionnaires
            for dictReponse in self.Questionnaires.GetDonnees(IDfamille) :
                dictDonnee[dictReponse["champ"]] = dictReponse["reponse"]
                if dictReponse["controle"] == "codebarres" :
                    dictDonnee["{CODEBARRES_QUESTION_%d}" % dictReponse["IDquestion"]] = dictReponse["reponse"]
            
            dictDonnees[IDcerfa] = dictDonnee
            
            # Champs de fusion pour Email
            dictChampsFusion[IDcerfa] = {}
            for key, valeur in dictDonnee.items() :
                if key[0] == "{" :
                    dictChampsFusion[IDcerfa][key] = valeur
        del dlgAttente
        return dictDonnees, dictChampsFusion
    #fin GetDonneesImpression

    def Impression(self, tracks=[], nomDoc=None, afficherDoc=True,
                   dictOptions=None, repertoire=None, repertoireTemp=False):
        """ Impression des factures """
        # Récupération des données à partir des IDrappel
        self.afficherDoc = afficherDoc
        resultat = self.GetDonneesImpression(tracks, dictOptions)
        if resultat == False :
            return False
        dictDonnees, dictChampsFusion = resultat
        
        # Récupération des paramètres d'affichage
        if dictOptions == None :
            if afficherDoc == False :
                dlg = DLG_Apercu_attestation_fiscale.Dialog(None, titre=_("Sélection des paramètres de l'attestation fiscale"), intro=_("Sélectionnez ici les paramètres d'affichage de l'attestation fiscale"))
                dlg.bouton_ok.SetImageEtTexte("Images/32x32/Valider.png", _("Ok"))
            else :
                dlg = DLG_Apercu_attestation_fiscale.Dialog(None)
            if dlg.ShowModal() == wx.ID_OK:
                dictOptions = dlg.GetParametres()
                dlg.Destroy()
            else :
                dlg.Destroy()
                return False

        # Création des PDF à l'unité
        def CreationPDFeclates(repertoireCible=""):
            dictPieces = {}
            if not repertoireCible:
                repertoireCible = ""
            dlgAttente = PBI.PyBusyInfo(_("Génération des attestations fiscales à l'unité au format PDF..."), parent=None, title=_("Veuillez patienter..."), icon=wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Logo.png"), wx.BITMAP_TYPE_ANY))
            wx.Yield()
            if self.afficherDoc and len(dictDonnees)>3:
                wx.MessageBox("Nous n'afficherons que les trois premiers fichiers,\nvous trouverez les autres dans le répertoire de destination des PDF")
            try :
                index = 0
                for IDcerfa, dictAttestation in dictDonnees.items() :
                    if index >= 3: self.afficherDoc = False
                    nomTitulaires = fp.NoPunctuation(dictAttestation["{FAMILLE_NOM}"])
                    nomFichier = "%s-%d" %(nomTitulaires,IDcerfa)
                    if repertoireCible == "":
                        from Utils import UTILS_Fichiers
                        cheminFichier = UTILS_Fichiers.GetRepTemp(nomFichier)
                    else:
                        cheminFichier = "%s/%s.pdf" % (repertoireCible, nomFichier)
                    dictComptesTemp = {IDcerfa : dictAttestation}
                    self.EcritStatusbar(_("Edition de l'attestation fiscale %d/%d : %s") % (index, len(dictAttestation), nomFichier))
                    UTILS_Impression_attestation_cerfa.Impression(dictComptesTemp, dictOptions, IDmodele=dictOptions["IDmodele"],
                                                                   ouverture=self.afficherDoc, nomFichier=cheminFichier)
                    dictPieces[IDcerfa] = cheminFichier
                    index += 1
                self.EcritStatusbar("")
                del dlgAttente
                return dictPieces
            except Exception as err:
                del dlgAttente
                traceback.print_exc(file=sys.stdout)
                dlg = wx.MessageDialog(None, _("Désolé, le problème suivant a été rencontré dans l'édition des attestations fiscales : \n\n%s") % err, _("Erreur"), wx.OK | wx.ICON_ERROR)
                dlg.ShowModal()
                dlg.Destroy()
                return False

        dictPieces = {}

        # Détail car Répertoire souhaité par l'utilisateur ou pour les Emails)
        if repertoire != None or afficherDoc == False:
            dictPieces = CreationPDFeclates(repertoire)
            if dictPieces == False :
                return False
        # Fabrication du PDF global
        else:
            dlgAttente = PBI.PyBusyInfo(_("Création du PDF des attestations fiscales..."), parent=None, title=_("Veuillez patienter..."), icon=wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Logo.png"), wx.BITMAP_TYPE_ANY))
            wx.Yield() 
            self.EcritStatusbar(_("Création du PDF des attestations fiscales en cours... veuillez patienter..."))
            try :
                UTILS_Impression_attestation_cerfa.Impression(dictDonnees, dictOptions, IDmodele=dictOptions["IDmodele"],
                                                               ouverture=afficherDoc, nomFichier=nomDoc)
                self.EcritStatusbar("")
                del dlgAttente
            except Exception as err:
                del dlgAttente
                traceback.print_exc(file=sys.stdout)
                dlg = wx.MessageDialog(None, _("Désolé, le problème suivant a été rencontré dans l'édition des attestations fiscales : \n\n%s") % err, _("Erreur"), wx.OK | wx.ICON_ERROR)
                dlg.ShowModal()
                dlg.Destroy()
                return False

        return dictChampsFusion, dictPieces

if __name__ == '__main__':
    app = wx.App(0)
    #wx.InitAllImageHandlers()

    from Dlg import DLG_Attestations_cerfa
    dlg = DLG_Attestations_cerfa.Dialog(None)
    dlg.ShowModal()
    dlg.Destroy()
    app.MainLoop()


