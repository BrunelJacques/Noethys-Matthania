#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys branche Matthania,
# Module:  Exports Compta Matthania, façon EBP_COMPTA
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS, JB
# Copyright:       (c) 2010-14 Ivan LUCAS, JB
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------

from Utils.UTILS_Traduction import _
import Chemins
import wx
from Ctrl import CTRL_Bouton_image
import os
import datetime
import copy
import GestionDB
from Ctrl import CTRL_Bandeau
from Ctrl import CTRL_Saisie_date
from Gest import GestionInscription
from Gest import GestionCoherence
from Utils.UTILS_Decimal import FloatToDecimal
import FonctionsPerso
from Utils import UTILS_Config
from Utils import UTILS_Parametres
import wx.lib.agw.pybusyinfo as PBI
import wx.propgrid as wxpg
from Ctrl import CTRL_Propertygrid
from wx.adv import BitmapComboBox

SYMBOLE = UTILS_Config.GetParametre("monnaie_symbole", "€")
CPTCLIENTS = "pas de compte client"
CONTEXT = "choix logiciel à faire"

def TakeFirst(item):
    return item[0]

def DateEngEnDateDD(dateEng):
    if dateEng and not isinstance(dateEng,str): dateEng = str(dateEng)
    return datetime.date(int(dateEng[:4]), int(dateEng[5:7]), int(dateEng[8:10]))

def DateDDenEng(dateDD):
    if dateDD == None: return None
    return dateDD.strftime("%Y-%m-%d")

def DateStrenQuad(date):
    if date == None: return None
    return date[-2:] + date[5:7] + date[2:4]

def Nz(valeur):
    if valeur == None:
        valeur = 0
    return valeur

def Decod(valeur):
    return GestionDB.Decod(valeur)

def FormateDate(dateDD=None, format="%d/%m/%y") :
    if dateDD == None or dateDD == "" :
        return ""
    else :
        return dateDD.strftime(format)
    
def zzzFormateLibelle(texte="", valeurs=[]):
    for motcle, valeur in valeurs :
        texte = texte.replace(motcle, valeur)
    return texte

def GetKeysDictTries(dictValeurs={}, key=""):
    """ Renvoie une liste de keys de dictionnaire triés selon la sous key indiquée """
    listeKeys = []
    for ID, dictTemp in dictValeurs.items() :
        listeKeys.append((dictTemp[key], ID))
    listeKeys.sort()
    listeResultats = []
    for keyTemp, ID in listeKeys() :
        listeResultats.append(ID)
    return listeResultats

def GetSens(montant, sens):
    # suppression de tout signe négatif
    if montant < FloatToDecimal(0.0) :
        montant = -montant
        if sens == "D" :
            sens = "C"
        else :
            sens = "D"
    return montant, sens

def Auxilliaire(compte):
    # passer du collectif au compte client
    if compte[:len(CPTCLIENTS)] == CPTCLIENTS:
        if CONTEXT == "QUADRA":
            return "01" + ("00000" + compte[len(CPTCLIENTS):])[-5:]
    return compte

class DataType(object):
    #Classe permetant la conversion facile vers le format souhaité (nombre de caractéres, alignement, décimales)
    def __init__(self,cat=int,length=1,align="<",precision=2):
        """
        initialise l'objet avec les paramétres souhaité
        """
        self.cat = cat
        self.length = length
        self.align = align
        self.precision = precision

    def Convert(self,data):
        # format souhaité
        ret_val = ""
        if data == None:
            data = ""

        if self.cat == int:                        #si l'on veux des entier
            if data!="":
                try:                                #on vérifie qu'il s'agit bien d'un nombre
                    data=int(data)
                except ValueError as e:
                    print("/!\ Erreur de format, impossible de convertir en int /!\\")
                    print(e)
                    data=0
                ret_val = "{0:{align}0{length}d}".format(data,align=self.align,length=self.length)
            else:
                ret_val = "{0:{align}0{length}s}".format(data,align=self.align,length=self.length)

        elif self.cat == str:                      #si l'on veux des chaines de caractéres
            if not isinstance(data,str): data = str(data)
            for a in ['\\',';',',']:
                data = data.replace(a,'')
            ret_val = "{0: {align}0{length}s}".format(data,align=self.align,length=self.length)

        elif self.cat == 'strdt':                      #si l'on veux des chaines de caractéres
            for a in ['/','-',' ']:
                data = data.replace(a,'')
            data = data.replace("-/","")
            ret_val = "{0: {align}0{length}s}".format(data,align=self.align,length=self.length)

        elif self.cat == float:                    #si l'on veux un nombre a virgule
            if data!="":
                try:
                    data=float(data)
                    #on vérifie qu'il s'agit bien d'un nombre
                except ValueError as e:
                    print("/!\ Erreur de format, impossible de convertir en float /!\\")
                    print(e)
                    data=0
                ret_val = "{0: {align}0{length}.{precision}f}".format(data,align=self.align,length=self.length,precision=self.precision)
            else:
                ret_val = "{0: {align}0{length}s}".format(data,align=self.align,length=self.length)

        if len(ret_val)>self.length:                #on tronc si la chaine est trop longue
            ret_val=ret_val[:self.length]
        return ret_val
        #fin Convert
    #fin class DataType

# --------Descriptifs des datas pour le format à largeur fixe mais aussi pour le formatage nombre ou dates -------------

dataTypesMatth = {"compte":[DataType(int,7,"<"),"@"],
             "libCompte":[DataType(str,25,"<"),"A"],
             "date":[DataType('strdt',8,">"),"B"],
             "journal":[DataType(str,2,"<"),"C"],
             "noPiece":[DataType(int,6,">"),"D"],
             "reference":[DataType(str,7,"<"),"E"],
             "pointage":[DataType(str,8,"<"),"F"],
             "libEcriture":[DataType(str,25,"<"),"G"],
             "montant":[DataType(float,13,">"),"H"],
             "sens":[DataType(str,1,"<"),"I"],
             "ecart":[DataType(float,10,">"),"J"],
             "jx":[DataType(str,1,">"),"K"],
             "gl":[DataType(str,1,">"),"L"],
             "mod":[DataType(str,1,">"),"M"]
             }

dataTypesQuadra = {
            "typ": [DataType(str, 1, "<"), "A"],
            "compte": [DataType(str, 8, "<"), "B"],
            "jr": [DataType(str, 2, "<"), "C"],
            "fol": [DataType(str, 3, "<"), "D"],
            "date": [DataType(str, 6, ">"), "E"],
            "div1": [DataType(str, 21, ">"), "F"],
            "sens": [DataType(str, 1, "<"), "G"],
            "signe": [DataType(str, 1, "<"), "H"],
            "valeur": [DataType(float, 12, ">",), "I"],
            "div2": [DataType(str, 44, ">"), "J"],
            "noPiece": [DataType(int, 8, ">"), "K"],
            "devise": [DataType(str, 3, "<"), "L"],
            "jrn": [DataType(str, 3, "<"), "M"],
            "div3": [DataType(str, 3, "<"), "N"],
            "libEcriture": [DataType(str, 30, "<"), "O"],
            "div4": [DataType(str, 2, "<"), "P"],
            "no_piece": [DataType(str, 10, "<"), "Q"],
            "div5": [DataType(str, 73, "<"), "R"],
             }

dataCptQuadra = {
            "typ": [DataType(str, 1, "<"), "A"],
            "compte": [DataType(str, 8, "<"), "B"],
            "libelle": [DataType(str, 30, "<"), "C"],
            "cle": [DataType(str, 7, "<"), "D"],
            "div1":[DataType(str, 47, ">"), "E"],
            "coll": [DataType(str, 8, ">"), "F"],
            "div2": [DataType(str, 350, ">"), "G"],
             }

# ------- Formats de fichiers d'export ---------------------------------------------------------------------------------

class XImportLine(object):
    #importé de UTILS_XImport, ligne telle que formaté dans un fichier XImport
    def __init__(self,ligne,num_ligne,cpt=False):
        # Récupére les donnée utiles fournis en paramétres, les convertis et les enregistre
        dataTypes = None
        if cpt:
            # cas du plan comptable Quadra
            dataTypes = dataCptQuadra
        elif CONTEXT == "MATTH":
            dataTypes = dataTypesMatth
        elif CONTEXT == "QUADRA":
            # ligne d'écriture espacement fixe
            dataTypes = dataTypesQuadra

        if ligne == None:
            listeEntete = {}
            self.entete = ""
            for key in list(dataTypes.keys()):
                listeEntete[dataTypes[key][1]] = key[:dataTypes[(key)][0].length] \
                                                 + " " * (dataTypes[(key)][0].length - len(key))
            for key in sorted(listeEntete.keys()):
                self.entete += listeEntete[key]
            return

        # compléments de variables composées spéciales Quadra
        if CONTEXT == "QUADRA" and not cpt:
            signe = "+"
            montant = ligne["montant"]
            if montant < 0.0 : signe = "-"
            valeur = int(round(abs(montant)*100,0))
            ligne["signe"] = signe
            ligne["valeur"] = valeur
            ligne["jr"] = ligne["journal"][:2]
            ligne["jrn"] = ligne["journal"][:3]
            ligne["date"] = DateStrenQuad(ligne["date"])
            ligne["no_piece"] = ligne["noPiece"]
        ligne["compte"] = Auxilliaire(ligne["compte"])

        values = dict()         #contient les valeurs fournies et non converties
        self.values = dict()    #contiendra les valeurs convertie

        for key in list(ligne.keys()):
            values[key] = ligne[key]
        values["numLigne"]=num_ligne #le numéro de mouvement est le numéro de la ligne ?

        for cle in list(dataTypes.keys()):  #Convertit toutes les données
            if cle in values:
                # Si la donnée a bien été fournie, on la converti
                self.values[cle]=dataTypes[cle][0].Convert(values[cle])
            else:                   #Sinon on remplis de blanc, pour respecter la largeur des colones
                self.values[cle]=dataTypes[cle][0].Convert("")

    def __getattr__(self,name):
        """
        gére l'acces aux attributs, pour plus de souplesse, les attributs inconnus renvoient None
        """
        if name in self.values:
            return self.values[name]
        else:
            return None

    def getDataMatth(self):
        """
        Retourne la ligne telle qu'elle doit être enregistré dans le fichier XImport
        """
        return  str(self.compte)+\
                str(self.libCompte)+\
                str(self.date)+\
                str(self.journal)+\
                str(self.noPiece)+\
                str(self.reference)+\
                str("        ")+\
                str(self.libEcriture)+\
                str(self.montant)+\
                str(self.sens)+\
                str("      0.00")+\
                str("F")+\
                str("F")+\
                str(" ")

    def getDataQuadra(self):
        #Retourne la ligne telle qu'elle doit sortir. L'attribut est géré par __getattr__ qui renvoit la clé de values
        return  \
            str("M")+\
            str(self.compte)+\
            str(self.jr)+\
            str("000")+\
            str(self.date)+\
            str(self.div1)+\
            str(self.sens)+ \
            str(self.signe) + \
            str(self.valeur) + \
            str(self.div2) + \
            str(self.noPiece) +\
            str("EUR")+ \
            str(self.jrn) + \
            str(self.div3) + \
            str(self.libEcriture) + \
            str(self.div4) + \
            str(self.no_piece) + \
            str(self.div5)

    def getCptaQuadra(self):
        #Retourne la ligne telle qu'elle doit être enregistré dans le fichier XImport

        return  \
            str("C")+\
            str(self.compte)+\
            str(self.libelle)+\
            str(self.cle)+\
            str(self.div1)+\
            str(self.coll)+\
            str(self.div2)


def Export_compta_matt_delimite(ligne):
    """ Formate les lignes au format Matthania pseudo EBP Compta """
    dataTypes = dataTypesMatth
    separateur = ","
    if ligne == None:
        entete = "compte;date;journal;noPiece;reference;pointage;libelleEcriture;montant;sens;ecart;jx;gl;mod".replace(";",separateur)
        return entete
    montant = ligne["montant"]
    sens = ligne["sens"]
    montant=(dataTypes["montant"][0].Convert(montant)).strip()
    date = dataTypes["date"][0].Convert(ligne["date"])
    libEcriture = dataTypes["libEcriture"][0].Convert(ligne["libEcriture"]).strip()
    libCompte = dataTypes["libCompte"][0].Convert(ligne["libCompte"]).strip()

    # fixation du guillemet pour encadrer le texte
    g = chr(34)
    ligneTemp = [
        g+ligne["compte"][:7]+g,
        g+libCompte[:25]+g,
        g+date+g,
        ligne["journal"][:2],
        str(ligne["noPiece"])[:6],
        g+ligne["reference"][:7]+g,
        "",
        g+libEcriture[:25]+g,
        str(montant).replace('.','.')[-13:],
        g+sens+g,
        "0.00",
        "F",
        "F",
        g+g
        ]
    retour = separateur.join(ligneTemp)
    return retour

def Export_compta_EBP(ligne, numLigne):
    """ Formate les lignes au format EBP Compta """
    dataTypes = dataTypesMatth
    separateur = ";"
    if ligne == None:
        #retour des champs entete
        entete = "noLigne;date;journal;compte;libelleCompte;libelleEcriture;noPiece;montant;sens;echeance;devise;reference;analytique".replace(";",separateur)
        return entete
    montant = ligne["montant"]
    sens = ligne["sens"]
    montant=(dataTypes["montant"][0].Convert(montant)).strip()
    date = dataTypes["date"][0].Convert(ligne["date"])
    echeance = dataTypes["echeance"][0].Convert(ligne["echeance"]).strip()
    libEcriture = dataTypes["date"][0].Convert(ligne["libEcriture"]).strip()
    libCompte = dataTypes["date"][0].Convert(ligne["libCompte"]).strip()

    ligneTemp = [
        str(numLigne),
        date,
        ligne["journal"],
        ligne["compte"],
        libCompte,
        libEcriture,
        str(ligne["noPiece"]),
        str(montant),
        sens,
        echeance,
        "EUR",
        ligne["reference"],
        ligne["analytique"],
        ]
    return separateur.join(ligneTemp)

# ------- Fonctions de traitement des données  -------------------------------------------------------------------------

class Donnees():
    def __init__(self, dictParametres={}):
        self.date_debut = dictParametres["date_debut"]
        self.date_fin =dictParametres["date_fin"]
        self.dictParametres = dictParametres
        self.fGest = GestionInscription.Forfaits(self)

        # Premier contrôle idem aux accès facturation pour tout le non transféré
        dlgAttente = PBI.PyBusyInfo(_("Vérif cohérence du 'à transférer' ..."), parent=None, title=_("Veuillez patienter..."), icon=wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Logo.png"), wx.BITMAP_TYPE_ANY))
        wx.Yield()
        gCoh = GestionCoherence.Diagnostic(self,None,inCpta=False, noInCpta=True,
                                           params = self.dictParametres)
        self.coherent = gCoh.Coherence()
        del gCoh
        del dlgAttente
        # Autres contrôles propres au transfert
        if self.coherent:
            coherVte = True
            if dictParametres["export_ventes"] == True :
                coherVte = self.CoherenceVentes()
            coherBqe = True
            if dictParametres["export_reglements"] == True :
                coherBqe = self.CoherenceBanques()
            self.coherent = coherVte and coherBqe
        self.nbreAttente = 0
        self.nbreDifferes = 0
        self.dictPC = {}
        # fin __init__

    def CoherenceVentes(self):
        DB = GestionDB.DB()
        dlgAttente = PBI.PyBusyInfo(_("Vérification de la cohérence des ventes..."), parent=None, title=_("Veuillez patienter..."), icon=wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Logo.png"), wx.BITMAP_TYPE_ANY))
        wx.Yield()
        if not self.dictParametres["retransfert"] :
            condTransfert = " AND ( prestations.compta IS NULL )"
        else : condTransfert = ""

        condition  = " (NOT (prestations.categorie = 'import')) AND (prestations.montant <> 0) AND ((prestations.date >= '%s'  AND prestations.date <= '%s' AND (prestations.IDfacture IS NULL)) OR (factures.date_edition >= '%s'  AND factures.date_edition <= '%s' AND ( NOT prestations.IDfacture IS NULL))) %s " %(self.date_debut, self.date_fin, self.date_debut, self.date_fin, condTransfert)

        #requête d'après celle qui appelle les prestations dans GetPrestations, doit récupérer les mêmes lignes
        req = """
            SELECT  prestations.IDprestation, matPieces.pieIDprestation, prestations.IDfamille, matPieces.pieIDfamille, prestations.IDfacture,
            prestations.IDcontrat, prestations.categorie, matPieces.pieNature, prestations.date, pieDateFacturation, pieDateAvoir, factures.date_edition,
            prestations.montant, prestations.label, prestations.code_compta, activites.abrege, activites.code_comptable, 
            activites.code_transport, MAX(individus_1.nom), factures.numero, groupes.analytique, pieIDnumPiece, pieNoFacture, pieNoAvoir

            FROM (((((	prestations
			LEFT JOIN 
				(
					inscriptions
					LEFT JOIN groupes 
					ON inscriptions.IDgroupe = groupes.IDgroupe)
				ON ((prestations.IDactivite = inscriptions.IDactivite) 
					AND (prestations.IDindividu = inscriptions.IDindividu)))
            LEFT JOIN 
				activites 
				ON prestations.IDactivite = activites.IDactivite)
            LEFT JOIN 
				rattachements 
				ON prestations.IDfamille = rattachements.IDfamille)
            LEFT JOIN 
				individus AS individus_1 
				ON rattachements.IDindividu = individus_1.IDindividu)
            LEFT JOIN 
				factures 
				ON factures.IDfacture = prestations.IDfacture)
            LEFT JOIN 
				matPieces 
				ON (matPieces.pieIDprestation = prestations.IDprestation 
					OR matPieces.pieIDnumPiece = prestations.IDcontrat)            
			WHERE %s
            GROUP BY  prestations.IDprestation, matPieces.pieIDprestation, prestations.IDfamille, matPieces.pieIDfamille, prestations.IDfacture,
            prestations.IDcontrat, prestations.categorie, matPieces.pieNature, prestations.date, pieDateFacturation, pieDateAvoir, factures.date_edition,
            prestations.montant, prestations.label, prestations.code_compta, activites.abrege, activites.code_comptable, 
            activites.code_transport, factures.numero, groupes.analytique, pieIDnumPiece, pieNoFacture, pieNoAvoir
            ;""" % (condition)
        retour = DB.ExecuterReq(req,MsgBox="DLG_Export_compta.CoherenceVentes_1")
        if retour != "ok" :
            del dlgAttente
            DB.Close()
            return False
        listeDonnees = DB.ResultatReq()
        texte = "\n"
        """
        prestations.IDprestation, matPieces.pieIDprestation, prestations.IDfamille, matPieces.pieIDfamille, prestations.IDfacture,
        prestations.IDcontrat, prestations.categorie, matPieces.pieNature, prestations.date, pieDateFacturation, pieDateAvoir, factures.date_edition,
        prestations.montant, prestations.label, prestations.code_compta, activites.abrege, activites.code_comptable,
        activites.code_transport, MAX(individus_1.nom), factures.numero, groupes.analytique, pieIDnumPiece, pieNoFacture, pieNoAvoir"""

        for IDprestation, pieIDprestation, IDfamille, pieIDfamille , IDfacture,\
            IDcontrat, categorie, nature, datePrestation, dateFacturation, dateAvoir, dateFacture,\
            montant, label, codeComptaPrestation, abregeActivite, actAnalytique, \
            actAnalyTransp, nomFamille, numero, analytique, pieIDnumPiece, noFacture, noAvoir in listeDonnees :
            #analyse des consos
            if categorie.startswith("conso"):
                #prestation facturée
                if IDfacture != None:
                    #cohérence noFacture dans matPieces
                    if noFacture == None and noAvoir == None:
                        # perte du lien prestation-facture-piece pour une conso
                        texte += "Famille %d %s: IDfacture %d en prestation %d, mais pas de pièce facturée!\n" % (IDfamille,nomFamille,IDfacture,IDprestation,)
                    if noFacture != numero and noAvoir != numero:
                        texte += "Famille %d %s: facture %d en prestation %d, mais pas dans une pièce via factures!\n" % (IDfamille,nomFamille,numero,IDprestation,)
                        continue
                    if not nature in ['FAC','AVO']:
                        texte += "Famille %d %s: noFacture %d dans une pièce de nature %s\n" % (IDfamille,nomFamille,noFacture,nature)
                    if noFacture !=None:
                        # noFacture sur mauvaise pièce
                        if IDfamille != pieIDfamille:
                            texte += "Famille %d %s: noFacture %d dans une pièce de la famille %d\n" % (IDfamille,nomFamille,noFacture,pieIDfamille)
                        if dateFacture != dateFacturation and IDprestation == pieIDprestation:
                            texte += "Famille %d %s: dateFacture %s diffère de date Facturation %s de la pièce %d\n" % (IDfamille,nomFamille,dateFacture,dateFacturation,pieIDnumPiece)
                        if noFacture == numero:
                            if IDprestation != pieIDprestation:
                                texte += "Famille %d %s: IDprestation %d diffère de pieIDprestation %d de la pièce %d\n" % (IDfamille,nomFamille,IDprestation,pieIDprestation,pieIDnumPiece)
                    if noAvoir !=None:
                        # noAvoir sur mauvaise pièce
                        if IDfamille != pieIDfamille:
                            texte += "Famille %d %s: noAvoir %d dans une pièce de la famille %d\n" % (IDfamille,nomFamille,noAvoir,pieIDfamille)
                        if dateFacture != dateAvoir and IDcontrat == pieIDprestation:
                            texte += "Famille %d %s: dateFacture de l'avoir %s diffère de dateAvoir %s de la pièce %d\n" % (IDfamille,nomFamille,dateFacture,dateAvoir, pieIDnumPiece)
                        if noAvoir == numero:
                            if IDcontrat != pieIDnumPiece:
                                texte += "Famille %d %s: IDcontrat %d diffère de pieIDprestation %d de la pièce %d\n" % (IDfamille,nomFamille,IDcontrat,pieIDprestation,pieIDnumPiece)

                #prestation conso non facturée
                else:
                    if nature != 'COM':
                        texte += "Famille %d %s: prestation %s no: %d pas facturée par pièce %s %d\n" % (IDfamille,nomFamille,categorie,IDprestation,nature,pieIDnumPiece)

            #analyse des prestations non consos à ne pas facturer
            else:
                if IDfacture != None:
                    texte += "Famille %d %s: prestation %s no:%d facturée par IDfacture %d de no %d \n" % (IDfamille,nomFamille,categorie,IDprestation, IDfacture,numero)
                if pieIDnumPiece != None:
                    texte += "Famille %d %s: prestation %s no:%d pointe la pièce %s %d \n" % (IDfamille,nomFamille,categorie,IDprestation,nature,pieIDnumPiece)

        #nouvelle requête si détail des ventes pour vérif des comptes
        if self.dictParametres["option_ventes"] == 0 :
            if not self.dictParametres["retransfert"] :
                condTransfert = " AND ( pieComptaFac IS NULL )"
            else : condTransfert = ""
            condition  = """(matPlanComptable.pctCompte Is Null) 
                            AND (ligMontant <> 0) 
                            AND (   (pieDateFacturation >= '%s' 
                                    AND pieDateFacturation <= '%s' ) 
                                OR (pieDateAvoir >= '%s' 
                                    AND pieDateAvoir <= '%s' )
                                ) %s """ %(self.date_debut, self.date_fin,self.date_debut, self.date_fin, condTransfert)

            req = """
                    SELECT matPiecesLignes.ligCodeArticle, matArticles.artLibelle
                    FROM ((matPieces
                    LEFT JOIN matPiecesLignes ON matPieces.pieIDnumPiece = matPiecesLignes.ligIDnumPiece)
                    LEFT JOIN matArticles ON matPiecesLignes.ligCodeArticle = matArticles.artCodeArticle)
                    LEFT JOIN matPlanComptable ON matArticles.artCodeComptable = matPlanComptable.pctCodeComptable
                    WHERE  %s
                    GROUP BY matPiecesLignes.ligCodeArticle, matArticles.artLibelle
                ;""" % condition
            retour = DB.ExecuterReq(req,MsgBox="DLG_Export_compta.CoherenceVentes_2")
            if retour != "ok" :
                del dlgAttente
                DB.Close()
                return False
            comptesNull = DB.ResultatReq()
            self.dictArtCptNull={}
            self.dictArtLib = {}
            for codeArticle, libelle in comptesNull:
                if not codeArticle in self.dictArtCptNull:
                    ok = False
                    # recherche sur le radical, utile pour les RED-FAMILL
                    for i in range(len(codeArticle),3,-1):
                        code = codeArticle[:i].upper()
                        req = """
                            SELECT matPlanComptable.pctCompte, matPlanComptable.pctCodeComptable
                            FROM matArticles LEFT JOIN matPlanComptable ON matArticles.artCodeComptable = matPlanComptable.pctCodeComptable
                            WHERE matArticles.artCodeArticle = '%s'
                            ;""" % code
                        ret = DB.ExecuterReq(req,MsgBox="DLG_Export_compta.CoherenceVentes_3")
                        if ret == "ok" :
                            recordset = DB.ResultatReq()
                            for record in recordset:
                                compte = record[0]
                                if compte != None:
                                    if len(compte) > 0 :
                                        ok = True
                        if ok:
                            self.dictArtCptNull[codeArticle] = compte
                            self.dictArtLib[codeArticle] = record[1]
                            continue
                    if not ok:
                        texte += "Pas de no de compte pour l'article %s\n" % codeArticle

            #requête de vérification d'enregistrements disparus
            condition  = "((pieDateFacturation >= '%s' AND pieDateFacturation <= '%s' ) OR (pieDateAvoir >= '%s' AND pieDateAvoir <= '%s' )) " %(self.date_debut, self.date_fin,self.date_debut, self.date_fin)
            # famille perdue
            req = """
                SELECT matPieces.pieIDnumPiece, matPieces.pieIDfamille, familles.IDfamille
                FROM matPieces
                     LEFT JOIN familles ON matPieces.pieIDfamille = familles.IDfamille
                WHERE   %s
                        AND ( familles.IDfamille IS NULL )
                GROUP BY matPieces.pieIDnumPiece, matPieces.pieIDfamille, familles.IDfamille;
                """ % condition
            retour = DB.ExecuterReq(req,MsgBox="DLG_Export_compta.CoherenceVentes_4")
            if retour != "ok" :
                del dlgAttente
                DB.Close()
                return False
            orphelines = DB.ResultatReq()
            for IDnumPiece, IDfamille, famille in orphelines:
                texte += "Pour la famille no %d la pièce %d ne trouve rien dans la table famille,\n " % (IDfamille,IDnumPiece)

            # prestation perdue
            req = """
                SELECT matPieces.pieIDnumPiece, matPieces.pieIDfamille, prestations.IDprestation
                FROM matPieces
                    LEFT JOIN prestations ON matPieces.pieIDprestation = prestations.IDprestation
                WHERE   %s
                        AND ( prestations.IDprestation IS NULL ) AND ( matPieces.pieNature = 'FAC')
                GROUP BY matPieces.pieIDnumPiece, matPieces.pieIDfamille, prestations.IDprestation;
                """ % condition
            retour = DB.ExecuterReq(req,MsgBox="DLG_Export_compta.CoherenceVentes_5")
            if retour != "ok" :
                del dlgAttente
                DB.Close()
                return False
            orphelines = DB.ResultatReq()
            for IDnumPiece, IDfamille, prestation in orphelines:
                texte += "Pour la famille no %d la pièce %d ne trouve pas la prestation associée,\n " % (IDfamille,IDnumPiece)
            # individu rattaché
            req = """
                SELECT matPieces.pieIDnumPiece, matPieces.pieIDfamille, rattachements.IDindividu
                FROM matPieces
                LEFT JOIN (rattachements
                            LEFT JOIN individus ON rattachements.IDindividu = individus.IDindividu) ON matPieces.pieIDfamille = rattachements.IDfamille
                WHERE   %s
                        AND ( rattachements.IDindividu IS NULL )
                GROUP BY matPieces.pieIDnumPiece, matPieces.pieIDfamille, rattachements.IDindividu;
                """ % condition
            retour = DB.ExecuterReq(req,MsgBox="DLG_Export_compta.CoherenceVentes_6")
            if retour != "ok" :
                del dlgAttente
                DB.Close()
                return False
            orphelines = DB.ResultatReq()
            for IDnumPiece, IDfamille, Nom in orphelines:
                texte += "Pour la famille no %d la pièce %d ne trouve aucun individu rattaché,\n " % (IDfamille,IDnumPiece)

        DB.Close()
        if texte != "\n":
            del dlgAttente
            # Avertissement et bloquage du process
            wx.MessageBox( _("Vérifiez la facturation des familles suivantes !%s")%texte,"Incohérence à réduire avant transfert")
            return False
        del dlgAttente
        return True
        #fin CoherenceVentes

    def CoherenceBanques(self):
        dlgAttente = PBI.PyBusyInfo(_("Vérification de la cohérence des règlements..."), parent=None, title=_("Veuillez patienter..."), icon=wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Logo.png"), wx.BITMAP_TYPE_ANY))
        wx.Yield()
        # vérifie la cohérence des règlements
        DB = GestionDB.DB()
        texte = "\n"
        if not self.dictParametres["retransfert"] :
            condTransfert = " AND ( reglements.compta IS NULL )"
        else : condTransfert = ""
        condition = "reglements.date>='%s' AND reglements.date<='%s' " % (self.date_debut, self.date_fin)
        condition += condTransfert

        # règlements orphelins de leur dépot, car ils seront ignorés des transferts
        req = """SELECT reglements.IDcompte_payeur, reglements.date, reglements.montant
                FROM reglements
                LEFT JOIN depots ON depots.IDdepot = reglements.IDdepot
                WHERE (depots.IDdepot Is Null) AND (reglements.IDdepot Is Not Null) AND %s
        ;""" % condition
        retour = DB.ExecuterReq(req,MsgBox="DLG_Export_compta.CoherenceBanques")
        if retour != "ok" :
            del dlgAttente
            DB.Close()
            return False
        comptesNull = DB.ResultatReq()
        for IDcomptePayeur, date, montant in comptesNull:
            texte += "Famille %d : Le depot du règlement de %s du %s n'est plus accessible !\n" % (IDcomptePayeur,str(montant),str(date))

        # Dépot sur une banque sans code comptable
        if self.dictParametres["option_reglements"] == 0 :
            condition = "reglements.IDdepot IS NOT NULL AND depots.date IS NOT NULL AND depots.date>='%s' AND depots.date<='%s'" % (self.date_debut, self.date_fin)
        else :
            condition = "reglements.date>='%s' AND reglements.date<='%s' " % (self.date_debut, self.date_fin)
        condition += condTransfert
        req = """SELECT comptes_bancaires.nom, modes_reglements.label
                FROM ((reglements
                INNER JOIN depots ON reglements.IDdepot = depots.IDdepot)
                LEFT JOIN comptes_bancaires ON depots.IDcompte = comptes_bancaires.IDcompte)
                LEFT JOIN modes_reglements ON reglements.IDmode = modes_reglements.IDmode
                WHERE (comptes_bancaires.code_NNE IS NULL)
                    AND (modes_reglements.code_compta Is Null)
                    AND (depots.code_compta Is Null)
                    AND %s
                GROUP BY comptes_bancaires.nom, modes_reglements.label
                ;""" % condition

        retour = DB.ExecuterReq(req,MsgBox="DLG_Export_compta.CoherenceBanques")
        if retour != "ok" :
            del dlgAttente
            DB.Close()
            return []
        comptesNull = DB.ResultatReq()
        for nomBanque, nomEmetteur in comptesNull:
            texte += "Le couple banque %s et emetteur %s est sans compte bancaire associé!\n" % (nomBanque,nomEmetteur)

        DB.Close()
        del dlgAttente
        if texte != "\n":
            # Avertissement et bloquage du process
            wx.MessageBox(_("Vérifiez les anomalies sur les règlements :%s")%texte,"Incohérence à réduire avant transfert")
            return False
        return True
        #fin CoherenceBanque

    def ComposePC(self,compte,libCompte,libEcriture):
        # Composition de du plan comptable des écritures générées
        if CONTEXT == 'QUADRA':
            compte = Auxilliaire(compte)
            if not compte in list(self.dictPC.keys()):
                if (not libCompte) or (len(libCompte) == 0): libCompte = libEcriture
                self.dictPC[compte] = libCompte
        return

    def DictEcritureComplete(self,cat,date,journal,compte,libCompte,libEcriture,noPiece,montant,sens,reference=" ",
                             echeance=" ",pointage=" ",analytique=" ",):
        # le champ 'echeance' de EBP est remplacé par la notion de 'reference' qui est un complément au numéro de pièce
        dictEcriture = {}
        dictEcriture["cat"] = cat
        dictEcriture["date"] = date
        dictEcriture["journal"] = journal
        dictEcriture["compte"] = compte
        dictEcriture["libCompte"] = libCompte
        dictEcriture["libEcriture"] = libEcriture
        dictEcriture["noPiece"] = noPiece
        dictEcriture["montant"] = montant
        dictEcriture["sens"] = sens
        dictEcriture["reference"] = reference
        dictEcriture["echeance"] = echeance
        dictEcriture["pointage"] = pointage
        dictEcriture["analytique"] = analytique
        self.ComposePC(compte,libCompte,libEcriture)
        return dictEcriture
        #fin DictEcritureComplete

    def SetPointeursPieces(self,DB,listeNoPiecesFac,listeNoPiecesAvo):
        dtTransfert = datetime.date.today().year*10000 + datetime.date.today().month*100 + datetime.date.today().day

        if len(listeNoPiecesFac) > 0 :
            listeSQL = "( " +str(listeNoPiecesFac)[1:-1] + " )"
            req = """SELECT  pieIDnumPiece, pieEtat, pieCommentaire,pieNature
                    FROM matPieces
                    WHERE pieIDnumPiece IN %s ;""" % (str(listeSQL))
            DB.ExecuterReq(req,MsgBox="DLG_Exportcompta.SetPointeursPieces1")
            listePieces = DB.ResultatReq()
            #date du transfert dans le memo commentaire et dans la zone pieComptaFac de la pièce
            for IDnumPiece, etat, commentaire, nature in listePieces:
                ligneComm = "Facture transférée en compta"
                etat = etat + '      '
                etat = etat[:5]+'4'
                commentaire = "%s : %s \n%s"  %(GestionInscription.DateIntToString(dtTransfert),ligneComm, DataType(commentaire))
                DB.ReqMAJ('matPieces',[('pieCommentaire',commentaire),('pieEtat',etat),('pieComptaFac',dtTransfert)],'pieIDnumPiece',IDnumPiece,MsgBox = 'DLG_Export_compta.SetPointeursPieces11')
            action = "TransfertCompta"
            ligneComm = "%d Pieces Fac transférées" % len(listeNoPiecesFac)
            self.fGest.Historise(None,None,action,ligneComm)

        if len(listeNoPiecesAvo) > 0 :
            listeSQL = "( " +str(listeNoPiecesAvo)[1:-1] + " )"
            req = """SELECT  pieIDnumPiece, pieEtat, pieCommentaire
                    FROM matPieces
                    WHERE pieIDnumPiece IN %s ;""" % (str(listeSQL))
            DB.ExecuterReq(req,MsgBox="DLG_Exportcompta.SetPointeursPieces2")
            listePieces = DB.ResultatReq()
            #date du transfert dans le memo commentaire et dans la zone pieComptaAvo de la pièce
            for IDnumPiece, etat, commentaire in listePieces:
                action = "TransfertCompta"
                ligneComm = "Avoir transféré en compta"
                etat = etat + '      '
                etat = etat[:5]+'4'
                commentaire = "%s : %s \n%s"  %(GestionInscription.DateIntToString(dtTransfert),ligneComm,Decod(commentaire))
                DB.ReqMAJ('matPieces',[('pieCommentaire',commentaire),('pieEtat',etat),('pieComptaAvo',dtTransfert)],'pieIDnumPiece',IDnumPiece,MsgBox = 'DLG_Export_compta.SetPointeursPieces21')
            action = "TransfertCompta"
            ligneComm = "%d Pieces Fac transférées" % len(listeNoPiecesAvo)
            self.fGest.Historise(None,None,action,ligneComm)
        DB.Close()
        return
        #fin SetPointeursPieces

    def SetPointeursPrestations(self,DB,listeIDprestations,listeIDcontrats):
        dtTransfert = datetime.date.today().year*10000 + datetime.date.today().month*100 + datetime.date.today().day
        if len(listeIDprestations) > 0:
            listeSQL = "( " +str(listeIDprestations)[1:-1] + " )"
            req = """UPDATE prestations
                    SET  compta = %d
                    WHERE IDprestation IN %s ;""" % (dtTransfert,str(listeSQL))
            DB.ExecuterReq(req,MsgBox="DLG_Exportcompta.SetPointeursPrestations1")

        if len(listeIDcontrats) > 0:
            listeContratsSQL = "( " +str(listeIDcontrats)[1:-1] + " )"
            req = """UPDATE prestations
                    SET  compta = %d
                    WHERE compta IS NULL AND IDcontrat IN %s ;""" % (dtTransfert,str(listeContratsSQL))
            DB.ExecuterReq(req,MsgBox="DLG_Exportcompta.SetPointeursPrestations2")
        return

    def SetPointeursReglements(self,DB,listeNoReglements):
        dtTransfert = datetime.date.today().year*10000 + datetime.date.today().month*100 + datetime.date.today().day
        if len(listeNoReglements) > 0 :
            listeSQL = "( " +str(listeNoReglements)[1:-1] + " )"
            req = """UPDATE reglements
                    SET  compta = %d
                    WHERE IDreglement IN %s ;""" % (dtTransfert,str(listeSQL))
            DB.ExecuterReq(req,MsgBox="DLG_Exportcompta.SetPointeursReglements")
        DB.Close()
        return

    def GetPrestations(self,datePrestPourConsos=False):
        listeDictLignes = []
        # Récupération des prestations de type OD
        DB = GestionDB.DB()
        code_clients = CPTCLIENTS
        if code_clients == None : code_clients = "41"
        code_ventes = (self.dictParametres["code_ventes"]+"000")[:3]

        if not self.dictParametres["retransfert"] :
            condTransfert = " AND ( prestations.compta IS NULL )"
        else : condTransfert = ""
        if datePrestPourConsos:
            # prépare le regroupement dans les clients par No Piece
            # On ignore la date de la pièce pour ne retenir que la date de la prestation
            journal = (self.dictParametres["journal_ventes"])
            complChamp = ", pieNoFacture, pieNoAvoir, factures.date_edition  "
            complJoin = " LEFT JOIN factures ON factures.IDfacture = prestations.IDfacture LEFT JOIN matPieces ON (matPieces.pieIDprestation = prestations.IDprestation OR matPieces.pieIDnumPiece = prestations.IDcontrat )"
            condition  = " (NOT prestations.IDfacture IS NULL ) AND (prestations.categorie LIKE 'conso%%') AND (prestations.montant <> 0) AND (factures.date_edition >= '%s' ) AND (factures.date_edition <= '%s' ) %s " %(self.date_debut, self.date_fin, condTransfert)
        else:
            # regroupement dans les clients par No prestation
            journal = (self.dictParametres["journal_od_ventes"])
            complChamp = ", NULL, NULL, NULL "
            complJoin = ""
            condition  = " (NOT (prestations.categorie LIKE 'conso%%')) AND (NOT (prestations.categorie = 'import')) AND (prestations.montant <> 0) AND (prestations.date >= '%s' ) AND (prestations.date <= '%s' ) %s " %(self.date_debut, self.date_fin, condTransfert)

        req = """
            SELECT  prestations.IDprestation, prestations.IDfamille, prestations.categorie, prestations.date, prestations.montant, prestations.label, prestations.code_compta,
            activites.abrege, activites.code_comptable, activites.code_transport, nomsFamille.nom,nomsFamille.prenom, individus.nom, individus.prenom, groupes.analytique
            %s
            FROM ((((prestations
            LEFT JOIN (inscriptions
                LEFT JOIN groupes ON inscriptions.IDgroupe = groupes.IDgroupe)
            ON (prestations.IDactivite = inscriptions.IDactivite) AND (prestations.IDindividu = inscriptions.IDindividu))
            LEFT JOIN activites ON prestations.IDactivite = activites.IDactivite)
            LEFT JOIN individus ON prestations.IDindividu = individus.IDindividu)
            LEFT JOIN
                (
                SELECT titulaires.IDfamille, individus.IDindividu, individus.nom, individus.prenom
                FROM (
                    SELECT rattachements.IDfamille, rattachements.titulaire, Min(rattachements.IDindividu) AS MinDeIDindividu
                    FROM rattachements
                    GROUP BY rattachements.IDfamille, rattachements.titulaire
                    HAVING rattachements.titulaire = 1
                     ) as titulaires
				INNER JOIN individus ON titulaires.MinDeIDindividu = individus.IDindividu
				) as nomsFamille
			ON prestations.IDfamille = nomsFamille.IDfamille)
			%s
            WHERE %s
            ;""" % (complChamp, complJoin, condition)

        retour = DB.ExecuterReq(req,MsgBox = "ReqPrestations")
        if retour != "ok" :
            GestionDB.MessageBox(None,retour)
            DB.Close()
            return False
        listeDonnees = DB.ResultatReq()
        if datePrestPourConsos : cat = "consos"
        else: cat = "od"
        dlgAttente = PBI.PyBusyInfo(_("Traitement de  %d prestations de type %s pour transfert compta...")%(len(listeDonnees),cat), parent=None, title=_("Veuillez patienter..."), icon=wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Logo.png"), wx.BITMAP_TYPE_ANY))
        wx.Yield()

        listeIDprestations = []
        for IDprestation, IDfamille, categorie, datePrestation, montant, label, codeComptaPrestation, abregeActivite, actAnalytique, actAnalyTransp, nomFamille, prenomFamille, nomIndividu, prenomIndividu, analytique, noFacture, noAvoir, dateFacture in listeDonnees :
            ok = True
            if datePrestPourConsos:
                if noFacture == None and noAvoir == None:
                    # perte du lien prestation-facture-piece pour une conso : on ne transfère pas une anomalie
                    ok = False
            if ok:
                listeIDprestations.append(IDprestation)
                if Nz(montant) != FloatToDecimal(0.0) :
                    if datePrestPourConsos:
                        date = dateFacture
                    else: date = datePrestation
                    if label == None : label = "prest: " + str(IDprestation)
                    if nomFamille == None : nomFamille = "fam: %s" % str(IDfamille)
                    if prenomFamille == None : prenomFamille = " "
                    nomFamille = nomFamille[:18] + " " + prenomFamille
                    if abregeActivite == None : reference = categorie.replace('import','Imp')
                    else: reference = abregeActivite

                    if codeComptaPrestation == None: codeComptaPrestation = ""
                    if codeComptaPrestation == "":
                        if categorie[:3] == "don":
                            codeComptaPrestation = self.dictParametres["dons"]
                        elif categorie == "debour":
                            codeComptaPrestation = self.dictParametres["debours"]
                        elif categorie in ["importOD","importAnnul]"]:
                            codeComptaPrestation = code_ventes
                        else: codeComptaPrestation = self.dictParametres["autres"]
                    if actAnalytique == None: actAnalytique = "00"
                    if analytique == None: analytique = ""
                    code_compta = codeComptaPrestation
                    analytique = ("00" + actAnalytique)[-2:]
                    if analytique != None :
                        if analytique == "00": analytique = ("00" + analytique)[-2:]
                    if analytique != "00" and len(analytique) == 2:
                        code_compta = code_compta[:3] + analytique
                        analytique = ''
                    libCompte = categorie
                    noPiece= IDprestation
                    libEcriture = categorie[:3]+ " "+ nomFamille[:5] +"-"+label

                    # -------------- Ventes crédit : Ventilation par prestation sans regroupement ---------------
                    dictLigne = self.DictEcritureComplete("ODprestation",str(date),journal,code_compta,libCompte,libEcriture ,noPiece,
                                                          FloatToDecimal(montant),"C",reference=str(IDfamille),analytique=analytique)
                    listeDictLignes.append((noPiece,dictLigne))
                    # -------------- Ventes débit : Ventilation par prestation sans regroupement ---------------
                    dictLigne2 = copy.deepcopy(dictLigne)
                    dictLigne2["sens"] = "D"
                    dictLigne2["compte"] = code_clients + ("00000" + str(IDfamille))[-5:]
                    dictLigne2["libCompte"] = nomFamille
                    dictLigne2["libEcriture"] = libEcriture
                    dictLigne2["reference"] = reference
                    self.ComposePC(dictLigne2["compte"], nomFamille,"")
                    listeDictLignes.append((noPiece,dictLigne2))
        # Modif des pointeurs de transferts
        self.SetPointeursPrestations(DB,listeIDprestations,[])

        if len(listeIDprestations) > 0 :
            listeSQL = "( " +str(listeIDprestations)[1:-1] + " )"
            req = """SELECT matPieces.pieIDnumPiece
                        FROM (prestations
                        INNER JOIN factures ON prestations.IDfacture = factures.IDfacture)
                        INNER JOIN matPieces ON factures.numero = matPieces.pieNoFacture
                     WHERE IDprestation IN %s ;""" % listeSQL

            retour = DB.ExecuterReq(req,MsgBox="DLG_Exportcompta.GetODprestations2")
            if retour != "ok" :
                GestionDB.MessageBox(None,retour)
                DB.Close()
                return False
            recordset = DB.ResultatReq()
            listeNoPiecesFac = []
            for IDnumPiece in recordset:
                listeNoPiecesFac.append(IDnumPiece[0])

            req = """SELECT matPieces.pieIDnumPiece
                        FROM (prestations
                        INNER JOIN factures ON prestations.IDfacture = factures.IDfacture)
                        INNER JOIN matPieces ON factures.numero = matPieces.pieNoAvoir
                     WHERE IDprestation IN %s ;""" % listeSQL
            retour = DB.ExecuterReq(req,MsgBox="DLG_Exportcompta.GetODprestations3")
            if retour != "ok" :
                GestionDB.MessageBox(None,retour)
                DB.Close()
                return False
            recordset = DB.ResultatReq()
            listeNoPiecesAvo = []
            for IDnumPiece in recordset:
                listeNoPiecesAvo.append(IDnumPiece[0])
            if len(listeNoPiecesFac)+ len(listeNoPiecesAvo) > 0:
                self.SetPointeursPieces(DB,listeNoPiecesFac,listeNoPiecesAvo)
        DB.Close()
        del  dlgAttente
        return listeDictLignes
        #fin GetPrestations

    def GetPieces(self):
        # Transfert des ventes regroupées par pièces comptables
        DB = GestionDB.DB()

        # Recherche compte et libellé 'transport' dans le plan comptable
        if "Ventes" in self.dictParametres:
            compteTransp = self.dictParametres["Ventes"]
        else:
            compteTransp = "706"
        libCompteTransp = "code *TRANSP* pas dans matPlanComptable"

        req = """
            SELECT pctCompte, pctLibelle
            FROM matPlanComptable
            WHERE  pctCodeComptable LIKE '%%TRANSP%%'
            ;"""
        ret = DB.ExecuterReq(req,MsgBox="DLG_Export_compta.GetPieces")
        if ret == "ok" :
            recordset = DB.ResultatReq()
            for record in recordset:
                compteTransp = record[0]+"00"
                libCompteTransp = record[1]

        # Récup des lignes des pièces Factures puis Avoir à transférer
        listeDictLignes = []
        dictClients = {}
        listeIDprestations = []
        listeIDcontrats = []
        listeNoPiecesFac = []
        listeNoPiecesAvo = []
        nbPieces = 0
        for facture in [True,False]:
            if facture :
                if not self.dictParametres["retransfert"] :
                    condTransfert = " AND ( pieComptaFac IS NULL )"
                else : condTransfert = ""
                condition  = " ((ligMontant <> 0) OR (piePrixTranspAller IS NOT NULL )OR (piePrixTranspRetour IS NOT NULL ) ) AND (pieDateFacturation >= '%s' ) AND (pieDateFacturation <= '%s' ) %s " %(self.date_debut, self.date_fin, condTransfert)

                req = """
                    SELECT  matPieces.pieIDnumPiece, matPiecesLignes.ligIDnumLigne, matPieces.pieDateFacturation, activites.abrege,
                    activites.code_comptable, activites.code_transport,
                    groupes.analytique, matPieces.pieIDfamille, nomsFamille.nom, nomsFamille.prenom,individus.nom, individus.prenom, matPieces.pieNoFacture,
                    matPieces.piePrixTranspAller, matPieces.piePrixTranspRetour, matPiecesLignes.ligLibelle, matPiecesLignes.ligMontant, matPiecesLignes.ligCodeArticle,
                    matPlanComptable.pctCompte, matPlanComptable.pctCodeComptable, matPieces.pieIDprestation
                    FROM ((((((matPieces
                    LEFT JOIN groupes ON matPieces.pieIDgroupe = groupes.IDgroupe)
                    LEFT JOIN activites  ON matPieces.pieIDactivite = activites.IDactivite)
                    LEFT JOIN individus ON matPieces.pieIDindividu = individus.IDindividu)
                    LEFT JOIN matPiecesLignes ON matPieces.pieIDnumPiece = matPiecesLignes.ligIDnumPiece)
                    LEFT JOIN (
                            SELECT titulaires.IDfamille, individus.IDindividu, individus.nom, individus.prenom
                            FROM (
                                SELECT rattachements.IDfamille, rattachements.titulaire, Min(rattachements.IDindividu) AS MinDeIDindividu
                                FROM rattachements
                                WHERE rattachements.titulaire = 1
                                GROUP BY rattachements.IDfamille, rattachements.titulaire
                                 ) as titulaires
                            INNER JOIN individus ON titulaires.MinDeIDindividu = individus.IDindividu
                            ) as nomsFamille
                    ON matPieces.pieIDfamille = nomsFamille.IDfamille)
                    LEFT JOIN matArticles ON matPiecesLignes.ligCodeArticle = matArticles.artCodeArticle)
                    LEFT JOIN matPlanComptable ON matArticles.artCodeComptable = matPlanComptable.pctCodeComptable
                    WHERE %s
                    ORDER BY matPieces.pieIDnumPiece
                    ;""" % (condition)
            else:
                if not self.dictParametres["retransfert"] :
                    condTransfert = " AND ( pieComptaAvo IS NULL )"
                else : condTransfert = ""
                condition  = " ((ligMontant <> 0) OR (piePrixTranspAller IS NOT NULL )OR (piePrixTranspRetour  IS NOT NULL)) AND (pieDateAvoir >= '%s' ) AND (pieDateAvoir <= '%s' ) %s " %(self.date_debut, self.date_fin, condTransfert)

                req = """
                    SELECT  matPieces.pieIDnumPiece, matPiecesLignes.ligIDnumLigne, matPieces.pieDateAvoir, activites.abrege,
                    activites.code_comptable, activites.code_transport,
                    groupes.analytique, matPieces.pieIDfamille, nomsFamille.nom, nomsFamille.prenom, individus.nom, 
                    individus.prenom, matPieces.pieNoAvoir, matPieces.piePrixTranspAller, matPieces.piePrixTranspRetour,
                    matPiecesLignes.ligLibelle, matPiecesLignes.ligMontant, matPiecesLignes.ligCodeArticle, 
                    matPlanComptable.pctCompte, matPlanComptable.pctCodeComptable, matPieces.pieIDprestation
                    FROM ((((((matPieces
                    LEFT JOIN groupes ON matPieces.pieIDgroupe = groupes.IDgroupe)
                    LEFT JOIN activites ON matPieces.pieIDactivite = activites.IDactivite)
                    LEFT JOIN individus ON matPieces.pieIDindividu = individus.IDindividu)
                    LEFT JOIN matPiecesLignes ON matPieces.pieIDnumPiece = matPiecesLignes.ligIDnumPiece)
                    LEFT JOIN
                        (
                        SELECT titulaires.IDfamille, individus.IDindividu, individus.nom, individus.prenom
                        FROM (
                            SELECT rattachements.IDfamille, rattachements.titulaire, Min(rattachements.IDindividu) AS MinDeIDindividu
                            FROM rattachements
                            GROUP BY rattachements.IDfamille, rattachements.titulaire
                            HAVING rattachements.titulaire = 1
                             ) as titulaires
                        INNER JOIN individus ON titulaires.MinDeIDindividu = individus.IDindividu
                        ) as nomsFamille
                        ON matPieces.pieIDfamille = nomsFamille.IDfamille)
                    LEFT JOIN matArticles ON matPiecesLignes.ligCodeArticle = matArticles.artCodeArticle)
                    LEFT JOIN matPlanComptable ON matArticles.artCodeComptable = matPlanComptable.pctCodeComptable
                    WHERE %s
                    ORDER BY matPieces.pieIDnumPiece
                    ;""" % (condition)

            retour = DB.ExecuterReq(req,MsgBox="GetPieces")
            if retour != "ok" :
                GestionDB.MessageBox(None,retour)
                DB.Close()
                return False
            listeDonnees = DB.ResultatReq()

            if facture:
                cat = "facture"
            else:
                cat = "avoir"
            nbPieces += len(listeDonnees)
            dlgAttente = PBI.PyBusyInfo(_("Traitement de  %d pièces %ss pour transfert compta...")%(len(listeDonnees),cat), parent=None, title=_("Veuillez patienter..."), icon=wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Logo.png"), wx.BITMAP_TYPE_ANY))
            wx.Yield()

            journal = self.dictParametres["journal_ventes"]
            oldIDnumpiece = 0
            #listeChampsLigne = ["IDnumPiece","IDnumLigne", "date", "abrege", "actAnalytique", "analytique", "IDfamille",
            # "nomFamille", "nomIndividu", "prenom", "noPiece", "prixTranspAller", "prixTranspRetour", "libelle", "montant",
            # "codeArticle", "compte", "libCompte", "IDprestation]
            for IDnumPiece, IDnumLigne, date, abrege, actAnalytique, actAnalyTransp, analytique, IDfamille, nomFamille, \
                prenomFamille, nomIndividu, prenom, noPiece, prixTranspAller, prixTranspRetour, libelle, montant, codeArticle, \
                compte, libCompte,IDprestation in listeDonnees :
                montant = Nz(montant)
                prixTranspAller = Nz(prixTranspAller)
                prixTranspRetour = Nz(prixTranspRetour)
                if codeArticle == None:
                    codeArticle = "noArt."
                date = str(date)

                if actAnalytique == None : actAnalytique = "00"
                if nomFamille == None : nomFamille = "Sans responsable"
                if prenomFamille == None : prenomFamille = " "
                nomFamille = nomFamille[:18] + " " + prenomFamille
                if nomIndividu == None :
                    nomIndividu = "Famille"
                    prenom = nomFamille
                if prenom == None : prenom = " "
                lgNom = len(nomIndividu[:10])
                libVte = nomIndividu[:10] + " " + (prenom + "               ")[:16-lgNom] + " " + codeArticle[:7]
                if abrege == None :
                    abrege = ""
                else : abrege = " - " + abrege[:8]
                analytique = ("00" + actAnalytique)[-2:]
                if analytique != None : analytique += analytique
                reference = ("00000" + str(IDfamille))[-4:]
                if noPiece == None :
                    GestionDB.MessageBox(None,"Problème de logique : pas de no facture ou avoir pour la famille %s %d avec date de facturation" % (nomFamille,IDfamille), titre="Anomalie à corriger")
                    DB.Close()
                    del dlgAttente
                    return False
                if compte == None :
                    if codeArticle in self.dictArtCptNull:
                        compte = self.dictArtCptNull[codeArticle]
                        libCompte = self.dictArtLib[codeArticle]

                if compte == None and facture and Nz(montant) != 0.0:
                    GestionDB.MessageBox(None,"3 Pas de no de compte pour l'article %s " % codeArticle , titre="Compte vente par défaut")
                if compte == None :
                    compte = self.dictParametres["code_ventes"]

                if libCompte == None : libCompte = ""
                if len(compte)<5 :
                    compte = compte + "000"
                    compte = compte[:3]
                    compte += actAnalytique
                if len(compteTransp)<5 :
                    compteTransp = compteTransp + "000"
                    compteTransp = compteTransp[:5]
                if actAnalyTransp != None and actAnalyTransp != '':
                    compteTransp = compteTransp[:3] + actAnalyTransp
                #constitution de la liste de dictionnaires par ligne de produit (crédit)
                if montant != 0.0:
                    montant = round(montant,2)
                    if facture :
                        dictTemp = self.DictEcritureComplete(cat,date,journal,compte,libCompte + abrege,libVte,noPiece,
                                                             montant,"C",reference=reference, analytique=analytique)
                    else :
                        dictTemp = self.DictEcritureComplete(cat,date,journal,compte,libCompte + abrege,libVte,noPiece,
                                                             montant,"D",reference=reference, analytique=analytique)
                    listeDictLignes.append((noPiece,dictTemp))
                mttTransp = 0.0
                if oldIDnumpiece != IDnumPiece :
                    oldIDnumpiece = IDnumPiece
                    if prixTranspAller != None : mttTransp += prixTranspAller
                    if prixTranspRetour != None : mttTransp += prixTranspRetour
                if mttTransp != 0.0:
                    mttTransp = round(mttTransp,2)
                    libelle = "Transport " + prenom + " " + nomIndividu
                    if facture:
                        dictTemp = self.DictEcritureComplete(cat,date,journal,compteTransp,libCompteTransp + abrege,libelle,noPiece,mttTransp,"C",reference=reference, analytique=analytique)
                    else:
                        dictTemp = self.DictEcritureComplete(cat,date,journal,compteTransp,libCompteTransp + abrege,libelle,noPiece,mttTransp,"D",reference=reference, analytique=analytique)
                    listeDictLignes.append((noPiece,dictTemp))

                # Stockage pour les débits
                if (IDfamille,noPiece) not in dictClients:
                    dictClients[(IDfamille,noPiece)] = {"date" : date, "montant" : montant + mttTransp,
                                                        "nomFamille" : nomFamille, "cat" : cat}
                else :
                    if dictClients[(IDfamille,noPiece)]["cat"] == cat:
                        dictClients[(IDfamille,noPiece)]["montant"] += montant + mttTransp
                    else:
                        GestionDB.MessageBox(None,"Le no de pièce %d est utilsé à la fois comme avoir et facture" % noPiece , titre="Anomalie à corriger")
                        dictClients[(IDfamille,noPiece)]["montant"] -= (montant + mttTransp)
                        DB.Close()
                        del dlgAttente
                        return False

                #stockage pour les pointeurs de transfert
                if facture :
                    if (not IDprestation in listeIDprestations) and IDprestation != None:
                        listeIDprestations.append(IDprestation)
                    if not IDnumPiece in listeNoPiecesFac:
                        listeNoPiecesFac.append(IDnumPiece)
                else:
                    if (not IDnumPiece in listeIDcontrats) and IDnumPiece != None:
                        listeIDcontrats.append(IDnumPiece)
                    if not IDnumPiece in listeNoPiecesAvo:
                        listeNoPiecesAvo.append(IDnumPiece)
            del dlgAttente

        dlgAttente = PBI.PyBusyInfo(_("Préparation de %d écritures potentielles de ventes pour transfert compta...")%(nbPieces), parent=None, title=_("Veuillez patienter..."), icon=wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Logo.png"), wx.BITMAP_TYPE_ANY))
        wx.Yield()
        # générations des contreparties client
        for (IDfamille,noPiece) in list(dictClients.keys()) :
            date = dictClients[(IDfamille,noPiece)]["date"]
            montant = dictClients[(IDfamille,noPiece)]["montant"]
            libCompte = dictClients[(IDfamille,noPiece)]["nomFamille"]
            code_clients = CPTCLIENTS
            if code_clients == None : code_clients = "41"
            compte = code_clients + ("00000" + str(IDfamille))[-5:]
            if dictClients[(IDfamille,noPiece)]["cat"] == "facture" :
                libelle = "Fac " + str(noPiece) + " " + libCompte
                dictTemp = self.DictEcritureComplete(cat,date,journal,compte,libCompte,libelle,noPiece,montant,"D",'conso')
            else :
                libelle = "Avo " + str(noPiece) + " " + libCompte
                dictTemp = self.DictEcritureComplete(cat,date,journal,compte,libCompte,libelle,noPiece,montant,"C",'annul')
            listeDictLignes.append((noPiece,dictTemp))
        # Modif des pointeurs de transferts
        self.SetPointeursPrestations(DB,listeIDprestations,listeIDcontrats)
        self.SetPointeursPieces(DB,listeNoPiecesFac,listeNoPiecesAvo)
        del dlgAttente
        return listeDictLignes
        #fin GetPieces

    def GetReglements_OD(self):
        # selection des réglements de type OD et pas d'un mode 'Ban*"
        listeDictLignes = []
        DB = GestionDB.DB()
        journal = (self.dictParametres["journal_banque"])
        codeClients = CPTCLIENTS
        if codeClients == None : codeClients = "41"
        codeBanque = self.dictParametres["code_banque"]

        # Condition de sélection des règlements
        condDate = "(( reglements.date>='%s' AND reglements.date<='%s' )" \
                   "OR( reglements.date_differe >='%s' AND reglements.date_differe <='%s' ))" % (self.date_debut, self.date_fin,self.date_debut, self.date_fin)

        if not self.dictParametres["retransfert"] :
            condTransfert = " AND ( reglements.compta IS NULL )"
        else :
            condTransfert = " "
        condition = condDate + condTransfert
        # tous réglements sans considération des dépots
        req = """
            SELECT reglements.IDreglement, reglements.Date, reglements.date_differe, reglements.encaissement_attente, 
                    emetteurs.nom, reglements.IDcompte_payeur, reglements.numero_piece, reglements.montant, reglements.date_saisie, 
                    modes_reglements.label, modes_reglements.code_compta, nomsFamille.nom, nomsFamille.prenom
            FROM (  (   reglements
                        LEFT JOIN modes_reglements ON reglements.IDmode = modes_reglements.IDmode
                    )
                    LEFT JOIN emetteurs ON (reglements.IDemetteur = emetteurs.IDemetteur) AND (reglements.IDmode = emetteurs.IDmode)
                )
                LEFT JOIN ( SELECT titulaires.IDfamille, individus.IDindividu, individus.nom, individus.prenom
                            FROM (  SELECT rattachements.IDfamille, rattachements.titulaire, Min(rattachements.IDindividu) AS MinDeIDindividu
                                    FROM rattachements
                                    WHERE rattachements.titulaire = 1
                                    GROUP BY rattachements.IDfamille, rattachements.titulaire
                                ) as titulaires
                            INNER JOIN individus ON titulaires.MinDeIDindividu = individus.IDindividu
                )  AS nomsFamille
                ON reglements.IDcompte_payeur = nomsFamille.IDfamille
            WHERE %s
            ;""" % condition
        retour = DB.ExecuterReq(req,MsgBox="DLG_Export_compta.GetReglements_OD")
        if retour != "ok" :
            DB.Close()
            return []
        listeDonnees = DB.ResultatReq()
        dlgAttente = PBI.PyBusyInfo(_("Traitement de %d règlements pour transfert compta...")%(len(listeDonnees)), parent=None, title=_("Veuillez patienter..."), icon=wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Logo.png"), wx.BITMAP_TYPE_ANY))
        wx.Yield()
        listeIDreglements = []
        #priorité à la date de différé si elle est non nulle
        for IDreglement, dateReglement, dateDiffere, attente, nomEmetteur, IDcompte_payeur, numeroCheque, montant, dateSaisie, modeReglement, comptaMode, nomFamille, prenomFamille in listeDonnees :
            # les règlements en attente sont ignorés
            if attente != 0 :
                self.nbreAttente += 1
                continue
            # les règlements différés attendent leur date de différé pour être transférés
            if dateDiffere != None:
                if DateEngEnDateDD(dateDiffere) > self.date_fin:
                    self.nbreDifferes +=1
                    continue
                dateComptaRegl = dateDiffere
            else:
                dateComptaRegl = dateReglement
            listeIDreglements.append(IDreglement)
            if nomFamille == None : nomFamille = " "
            if prenomFamille == None : prenomFamille = " "
            nomPayeur = nomFamille[:18] + " " + prenomFamille
            if comptaMode == None:
                comptaMode = ""
            # compte du mode de réglement puis le compte de la banque associée au règlement
            codeCompta = comptaMode
            if len(codeCompta) < 2:
                codeCompta = codeBanque

            #composition crédit
            codeClient = codeClients+ ("00000"+str(IDcompte_payeur))[-5:]
            emission = "???"
            if nomEmetteur != None:
                emission = nomEmetteur
            else:
                if modeReglement != None:
                    emission = modeReglement
            label = "%s %s %s" % (FormateDate(DateEngEnDateDD(dateReglement)), emission[:7] ,nomPayeur)
            noPiece = IDreglement

            dictLigne = self.DictEcritureComplete("reglement",str(dateComptaRegl),journal,codeClient,nomPayeur,label ,noPiece,
                                                  FloatToDecimal(montant),"C",reference= modeReglement)
            listeDictLignes.append((noPiece,dictLigne))

            #reprise pour débit
            label = "%s %s-%s" % (modeReglement[:3],emission[:7],nomPayeur)

            # -------------- Règlement débit : sans regroupement ---------------
            dictLigne2 = copy.deepcopy(dictLigne)
            dictLigne2["sens"] = "D"
            dictLigne2["compte"] = codeCompta
            dictLigne2["libCompte"] = emission
            dictLigne2["libEcriture"] = label
            dictLigne2["reference"] = modeReglement
            listeDictLignes.append((noPiece,dictLigne2))
        # Modif des pointeurs de transferts
        self.SetPointeursReglements(DB,listeIDreglements)

        del dlgAttente
        if self.nbreAttente >0 or True:
            # Avertissement de présence de règlements en attente
            wx.MessageBox( _("Il y a %d règlements en attente qui n'ont pas été transférés !")% self.nbreAttente,"Règlements non transférés")
        if self.nbreDifferes >0:
            # Avertissement de présence de règlements avec dates différées postérieures
            wx.MessageBox( _("Il y a %d règlements avec des dates futures qui n'ont pas été transférés !")% self.nbreDifferes,"Règlements non transférés")
        return listeDictLignes
        #fin GetReglements_OD

    def GetReglements_Depots(self):
        # selection des réglements ayant fait l'objet d'un dépôt
        listeDictLignes = []
        DB = GestionDB.DB()
        journal = (self.dictParametres["journal_banque"])
        codeClients = CPTCLIENTS
        if codeClients == None : codeClients = "41"
        codeBanque = self.dictParametres["code_banque"]
        # Condition de sélection des règlements
        if not self.dictParametres["retransfert"] :
            condTransfert = " AND ( reglements.compta IS NULL )"
        else : condTransfert = ""

        condition = "reglements.IDdepot IS NOT NULL AND depots.date IS NOT NULL AND depots.date>='%s' AND depots.date<='%s'" % (self.date_debut, self.date_fin)
        condition += condTransfert
        # réglements ayant fait l'objet d'un dépôt et n'étant pas déjà transférés
        req = """
        SELECT depots.IDdepot, depots.Date, depots.nom, comptes_bancaires.nom, comptes_bancaires.numero, reglements.IDcompte_payeur,
                reglements.numero_piece, reglements.montant, reglements.date,  modes_reglements.IDmode, modes_reglements.label,
                modes_reglements.code_compta,depots.code_compta, comptes_bancaires.code_nne, nomsFamille.nom, nomsFamille.prenom,
                reglements.IDreglement, modes_reglements.type_comptable, reglements.IDemetteur, emetteurs.nom, payeurs.nom
                
        FROM (( (   (   (depots
                        LEFT JOIN reglements ON depots.IDdepot = reglements.IDdepot)
                    LEFT JOIN modes_reglements ON reglements.IDmode = modes_reglements.IDmode)
                LEFT JOIN payeurs ON reglements.IDpayeur = payeurs.IDpayeur)
            LEFT JOIN comptes_bancaires ON depots.IDcompte = comptes_bancaires.IDcompte)

        LEFT JOIN (
                SELECT titulaires.IDfamille, individus.IDindividu, individus.nom, individus.prenom
                FROM (
                    SELECT rattachements.IDfamille, rattachements.titulaire, Min(rattachements.IDindividu) AS MinDeIDindividu
                    FROM rattachements
                    WHERE rattachements.titulaire = 1
                    GROUP BY rattachements.IDfamille, rattachements.titulaire
                     ) as titulaires
                    INNER JOIN individus ON titulaires.MinDeIDindividu = individus.IDindividu
                    ) as nomsFamille ON reglements.IDcompte_payeur = nomsFamille.IDfamille)
	    LEFT JOIN emetteurs ON (reglements.IDemetteur = emetteurs.IDemetteur) AND (reglements.IDmode = emetteurs.IDmode)
        WHERE %s
        ;""" % condition

        retour = DB.ExecuterReq(req,MsgBox="DLG_ExportCompta.GetReglements_Depots")
        if retour != "ok" :
            DB.Close()
            return []
        listeDonnees = DB.ResultatReq()

        dictDepots = {}
        listeIDreglements = []
        for IDdepot, dateDepot, nomDepot, nomBanque, numeroBanque,IDcompte_payeur, numeroReglement,montant,dateReglement,\
            IDmode, modeReglement,comptaMode,comptaDepot,comptaBanque,nomFamille, prenomFamille,IDreglement,\
            group,IDemetteur, nomEmetteur, nomPayeur in listeDonnees :
            if nomFamille == None : nomFamille = " "
            if nomEmetteur == None: nomEmetteur = ""
            if nomPayeur == None: nomPayeur = ""
            if prenomFamille == None : prenomFamille = " "
            listeIDreglements.append(IDreglement)
            if nomPayeur == None:
                nomPayeur = nomFamille[:6] + " " + prenomFamille
            if comptaMode == None:
                comptaMode = ""
            if comptaBanque == None:
                comptaBanque = ""
            # priorité est donnée au code comptable du dépot s'il est numérique
            try:
                codeCompta = str(int(comptaDepot))
            except: codeCompta = ""

            if len(codeCompta) < 2 :
                # ensuite compte de la banque associée au dépot puis le compte du mode de réglement
                if len(codeCompta) < 2:
                    codeCompta = comptaBanque
                if len(codeCompta) < 2:
                    codeCompta = comptaMode
                if len(codeCompta) < 2:
                    codeCompta = codeBanque


            if montant == None: montant = FloatToDecimal(0.0)
            if nomDepot == None: nomDepot = ""
            dateCpta = dateDepot
            dateLib = dateReglement
            modeLib = modeReglement[:3]
            if group == "banque":
                cle = (IDdepot, IDmode)
                label = "%s-%s" % (modeReglement[:7],nomDepot)
                ref = "Bq:%s" %nomBanque[:7]
            elif group == 'bancaf':
                cle = (IDdepot,IDemetteur)
                label = "%s-%s-%s" % (modeReglement[:3],nomBanque[:3],nomEmetteur)
                ref = "Dep:%s" %nomDepot[:7]
            elif group == 'regreg':
                #dateCpta = dateReglement
                #dateLib = dateDepot
                modeLib = 'Dep'
                cle = (IDreglement,0)
                if len(nomEmetteur) == 0:
                    nomEmetteur = nomPayeur
                label = "%s%s %s" % (modeReglement[:3],modeLib+FormateDate(DateEngEnDateDD(dateLib))[:5],
                                       nomEmetteur)
                ref = "%s" % nomEmetteur
            else :
                cle = (IDreglement,0)
                label = "%s %s %s" % (modeReglement[:3]+nomEmetteur[:5],
                                       FormateDate(DateEngEnDateDD(dateLib))[:5],nomPayeur)
                ref = "%s" %nomPayeur
            #regroupements pour debits
            if (cle,codeCompta) in dictDepots:
                dictDepots[(cle,codeCompta)]["nbre"]+=1
                dictDepots[(cle,codeCompta)]["montant"]+=FloatToDecimal(montant)
            else:
                dictDepots[(cle,codeCompta)]={}
                dictDepots[(cle,codeCompta)]["nbre"]=1
                dictDepots[(cle,codeCompta)]["montant"]=FloatToDecimal(montant)
                dictDepots[(cle,codeCompta)]["date"]= dateCpta
                dictDepots[(cle,codeCompta)]["IDdepot"]=IDdepot
                dictDepots[(cle,codeCompta)]["nomDepot"]=nomDepot
                dictDepots[(cle,codeCompta)]["nomBanque"]=nomBanque.replace(" ","")
                dictDepots[(cle,codeCompta)]["numeroBanque"]=numeroBanque
                dictDepots[(cle,codeCompta)]["codeCompta"]=codeCompta
                dictDepots[(cle,codeCompta)]["label"]=label
                dictDepots[(cle,codeCompta)]["ref"]=ref

            #composition crédit
            listeLignes = []
            codeClient = codeClients+ ("00000"+str(IDcompte_payeur))[-5:]
            if modeLib[:3] == modeReglement[:3]: modeLib = ''
            if numeroReglement and len(numeroReglement)>0:
                label = "%s %s %s" % (modeReglement[:3]+str(numeroReglement)[-4:], modeLib[:3]+FormateDate(DateEngEnDateDD(dateLib))[:5],nomPayeur)
            else:
                label = "%s%s %s" % (modeReglement[:3], modeLib[:3]+FormateDate(DateEngEnDateDD(dateLib))[:5],nomPayeur)

            dictLigne = self.DictEcritureComplete("depot",str(dateCpta),journal,codeClient,nomPayeur,label ,IDdepot,
                                                  FloatToDecimal(montant),"C",reference= ("Bq:"+ nomBanque.replace(" ","")))
            listeDictLignes.append((cle,dictLigne))

        #reprise des totaux par dépot pour débits
        for (cle,codeCompta) in list(dictDepots.keys()):
            nbre = str(dictDepots[(cle,codeCompta)]["nbre"])
            if nbre in ["0","1"]: nbre = ""
            label = "%s%s" % (nbre, dictDepots[(cle,codeCompta)]["label"])
            ref = dictDepots[(cle,codeCompta)]["ref"]

            # DictEcritureComplete(self,type,date,journal,compte,     libCompte,libEcriture,noPiece,    montant,sens,reference="
            dictLigne = self.DictEcritureComplete("depot",str(dictDepots[(cle,codeCompta)]["date"]),journal,dictDepots[(cle,codeCompta)]["codeCompta"],
                                                  dictDepots[(cle,codeCompta)]["nomBanque"],label ,dictDepots[(cle,codeCompta)]["IDdepot"],
                                                  dictDepots[(cle,codeCompta)]["montant"],"D",reference= ref)
            listeDictLignes.append((cle,dictLigne))
        # Modif des pointeurs de transferts
        self.SetPointeursReglements(DB,listeIDreglements)

        return listeDictLignes
        #fin GetReglements_Depots

# -------------------------------------------------------------------------------------------------------------------------------------------

class CTRL_Logiciel(BitmapComboBox):
    def __init__(self, parent, size=(-1,  -1)):
        BitmapComboBox.__init__(self, parent, size=size, style=wx.CB_READONLY)
        self.parent = parent
        self.listeFormats = [
            {"code" : "compta_quadra_fixe", "label" : _("Quadratus Compta (Champs fixes)"), "image" : wx.Bitmap(Chemins.GetStaticPath('Images/48x48/Quadra.png'), wx.BITMAP_TYPE_PNG)},
            {"code" : "compta_matt_delimite", "label" : _("Matth Compta (Champs délimités)"), "image" : wx.Bitmap(Chemins.GetStaticPath('Images/48x48/Sync_upload.png'), wx.BITMAP_TYPE_PNG)},
            {"code" : "compta_matt_fixe", "label" : _("Matth Compta (Largeurs fixes)"), "image" : wx.Bitmap(Chemins.GetStaticPath('Images/48x48/Sync_upload.png'), wx.BITMAP_TYPE_PNG)},
            {"code" : "compta_ebp", "label" : _("EBP Compta"), "image" : wx.Bitmap(Chemins.GetStaticPath('Images/48x48/Logiciel_ebp.png'), wx.BITMAP_TYPE_PNG)},
            ]
        for dictFormat in self.listeFormats :
            self.Append(dictFormat["label"], dictFormat["image"], dictFormat["label"])
        self.SetSelection(0)
        self.Importation() 
    
    def SetCode(self, code=""):
        index = 0
        for dictFormat in self.listeFormats :
            if dictFormat["code"] == code :
                 self.SetSelection(index)
            index += 1

    def GetCode(self):
        index = self.GetSelection()
        if index == -1 : return None
        return self.listeFormats[index]["code"]
    
    def Importation(self):
        format = UTILS_Parametres.Parametres(mode="get", categorie="export_compta", nom="nom_format", valeur="compta_matt_delimite")
        self.SetCode(format) 

    def Sauvegarde(self):
        UTILS_Parametres.Parametres(mode="set", categorie="export_compta", nom="nom_format", valeur=self.GetCode())

class CTRL_Codes(wxpg.PropertyGrid):
    def __init__(self, parent, dictCodes=None, keyStr=False):
        wxpg.PropertyGrid.__init__(self, parent, -1, style=wxpg.PG_SPLITTER_AUTO_CENTER)
        self.parent = parent
        self.dictCodes = dictCodes
        self.keyStr = keyStr
        self.SetExtraStyle(wxpg.PG_EX_HELP_AS_TOOLTIPS)
        couleurFond = "#e5ecf3"
        self.SetCaptionBackgroundColour(couleurFond)
        self.SetMarginColour(couleurFond)

        # Remplissage des valeurs
        if keyStr == True:
            listeIntitules = list(dictCodes.keys())
            listeIntitules.sort()
            for intitule in listeIntitules:
                valeur = dictCodes[intitule]["code_compta"]
                if valeur == None: valeur = ""
                propriete = wxpg.StringProperty(label=intitule, name=intitule, value=valeur)
                self.Append(propriete)
        else:
            for ID, dictValeurs in dictCodes.items():
                valeur = dictValeurs["code_compta"]
                if valeur == None: valeur = ""
                if "label" in dictValeurs: intitule = dictValeurs["label"]
                if "intitule" in dictValeurs: intitule = dictValeurs["intitule"]
                propriete = wxpg.StringProperty(label=intitule, name=str(ID), value=valeur)
                self.Append(propriete)

    def Validation(self):
        for label, valeur in self.GetPropertyValues().items():
            if valeur == "":
                if self.keyStr == False:
                    ID = int(label)
                    if "label" in self.dictCodes[ID]: label = self.dictCodes[ID]["label"]
                    if "intitule" in self.dictCodes[ID]: label = self.dictCodes[ID]["intitule"]
                dlg = wx.MessageDialog(None, _(
                    "Vous n'avez pas renseigné le code comptable de la ligne '%s'.\n\nSouhaitez-vous tout de même continuer ? (Si oui, cette ligne ne sera pas exportée)") % label,
                                       _("Information manquante"), wx.YES_NO | wx.YES_DEFAULT | wx.ICON_EXCLAMATION)
                reponse = dlg.ShowModal()
                dlg.Destroy()
                if reponse == wx.ID_NO:
                    return False

        return True

    def GetCodes(self):
        dictCodes = self.GetPropertyValues()
        return dictCodes

class CTRL_Parametres(CTRL_Propertygrid.CTRL):#(wxpg.PropertyGrid) :
    def __init__(self, parent, listeDonnees=[]):
        CTRL_Propertygrid.CTRL.__init__(self, parent)
        self.parent = parent
        self.listeDonnees = listeDonnees
        self.SetExtraStyle(wxpg.PG_EX_HELP_AS_TOOLTIPS)
        couleurFond = "#e5ecf3"
        self.SetCaptionBackgroundColour(couleurFond)
        self.SetMarginColour(couleurFond)
        self.FitColumns()
        self.DB = GestionDB.DB()
  
    def Remplissage(self):        
        # Autres lignes
        for valeur in self.listeDonnees :
            if type(valeur) == dict :
                if valeur["cat"] == "chaine" :
                    propriete = wxpg.StringProperty(label=valeur["label"], name=valeur["code"], value=valeur["defaut"])
                if valeur["cat"] == "choix" :
                    propriete = wxpg.EnumProperty(label=valeur["label"], name=valeur["code"], labels=valeur["choix"], values=list(range(0, len(valeur["choix"]))), value=valeur["defaut"])
                if valeur["cat"] == "check" :
                    propriete = wxpg.BoolProperty(label=valeur["label"], name=valeur["code"], value=valeur["defaut"])
                    propriete.SetAttribute("UseCheckbox", True)
                propriete.SetHelpString(valeur["tip"]) 
                self.Append(propriete)
            else :
                self.Append(wxpg.PropertyCategory(valeur))

    def Importation(self):
        """ Importation des valeurs dans le contrôle """
        # Récupération des noms et valeurs par défaut du contrôle
        dictValeurs = copy.deepcopy(self.GetPropertyValues())
        # Recherche les paramètres mémorisés
        dictParametres = UTILS_Parametres.ParametresCategorie(mode="get", categorie="export_compta", dictParametres=dictValeurs)
        # Envoie les paramètres dans le contrôle
        for nom, valeur in dictParametres.items() :
            propriete = self.GetPropertyByName(nom)
            ancienneValeur = propriete.GetValue() 
            propriete.SetValue(valeur)
    
    def Sauvegarde(self,forcer = False):
        """ Mémorisation des valeurs du contrôle"""
        dictValeurs = copy.deepcopy(self.GetPropertyValues())
        UTILS_Parametres.ParametresCategorie(mode="set", categorie="export_compta", dictParametres=dictValeurs)
        self.parent.ctrl_logiciel.Sauvegarde()

    def Validation(self):
        # Période
        if self.parent.ctrl_date_debut.GetDate() == None :
            dlg = wx.MessageDialog(self, _("Vous devez obligatoirement renseigner la date de début de période !"), _("Information"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return False
        else:
            debutExercice,finExercice = self.DB.GetExercice(self.parent.ctrl_date_debut.GetDate())
            if debutExercice == None:
                return False

        if self.parent.ctrl_date_fin.GetDate() == None :
            dlg = wx.MessageDialog(self, _("Vous devez obligatoirement renseigner la date de fin de période !"), _("Information"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return False
        else:
            debutExercice2,finExercice2 = self.DB.GetExercice(self.parent.ctrl_date_fin.GetDate())
            if debutExercice2 == None:
                return False
        if debutExercice != debutExercice2:
            dlg = wx.MessageDialog(self, _("Non bloquant: Les dates début et fin ne sont pas dans le même exercice comptable !"), _("Ecritures possibles hors exercice"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()

        # Paramètres
        for valeur in self.listeDonnees :
            if type(valeur) == dict :
                if valeur["cat"] == "chaine" and valeur["obligatoire"] == True and self.GetPropertyValue(valeur["code"]) == "" :
                    dlg = wx.MessageDialog(self, _("Vous devez obligatoirement renseigner l'information '%s' !") % valeur["description"], _("Information"), wx.OK | wx.ICON_EXCLAMATION)
                    dlg.ShowModal()
                    dlg.Destroy()
                    return False
        return True

    def GetParametres(self):
        dictParametres = self.GetPropertyValues()
        dictParametres["date_debut"] = self.parent.ctrl_date_debut.GetDate() 
        dictParametres["date_fin"] = self.parent.ctrl_date_fin.GetDate()
        global CPTCLIENTS
        CPTCLIENTS = dictParametres["code_clients"]
        return dictParametres

    def CreationFichier(self, nomFichier="", texte="", iso = "iso-8859-15"):
        # Demande à l'utilisateur le nom de fichier et le répertoire de destination
        wildcard = "Fichier texte (*.txt)|*.txt|" \
                        "All files (*.*)|*.*"
        sp = wx.StandardPaths.Get()
        cheminDefaut = sp.GetDocumentsDir()
        dlg = wx.FileDialog(
            None, message = _("Veuillez sélectionner le répertoire de destination et le nom du fichier"), defaultDir=cheminDefaut, 
            defaultFile = nomFichier, 
            wildcard = wildcard, 
            style = wx.FD_SAVE
            )
        dlg.SetFilterIndex(0)
        if dlg.ShowModal() == wx.ID_OK:
            cheminFichier = dlg.GetPath()
            dlg.Destroy()
        else:
            dlg.Destroy()
            return
        
        # Le fichier de destination existe déjà :
        if os.path.isfile(cheminFichier) == True :
            dlg = wx.MessageDialog(None, _("Un fichier portant ce nom existe déjà. \n\nVoulez-vous le remplacer ?"), "Attention !", wx.YES_NO | wx.NO_DEFAULT | wx.ICON_EXCLAMATION)
            if dlg.ShowModal() == wx.ID_NO :
                return False
                dlg.Destroy()
            else:
                dlg.Destroy()

        # Création du fichier texte
        f = open(cheminFichier, "w")
        if iso == "sans":
            # tous ces caractères sont transposés avec plusieurs par unidecode ex : € -> EUR
            car  = ["€","°","£","\\","?","§","é","è",]
            carR = ["E","o","$","/","-","$","e","e"]
            for i in range(0,len(car)):
                texte=texte.replace(car[i],carR[i])
            try:
                from unidecode import unidecode
                f.write(unidecode(texte))
            except:
                txtMessage = _("Il faut installer le module unidecode par la commande systeme PIP INSTALL unidecode")
                dlgConfirm = wx.MessageDialog(None, txtMessage, _(" "), wx.YES_NO|wx.NO_DEFAULT|wx.ICON_QUESTION)
                dlgConfirm.ShowModal()
                dlgConfirm.Destroy()
        else:
            if iso == 'latin':
                texte=texte.replace("€","E")
            f.write(texte.encode(iso))
        f.close()
        
        # Confirmation de création du fichier et demande d'ouverture directe dans Excel
        txtMessage = _("Le fichier a été créé avec succès.\n\nSouhaitez-vous l'ouvrir dès maintenant ?")
        dlgConfirm = wx.MessageDialog(None, txtMessage, _("Confirmation"), wx.YES_NO|wx.NO_DEFAULT|wx.ICON_QUESTION)
        reponse = dlgConfirm.ShowModal()
        dlgConfirm.Destroy()
        if reponse == wx.ID_NO:
            return
        else:
            FonctionsPerso.LanceFichierExterne(cheminFichier)

class CTRL_Lanceur(CTRL_Parametres):
    def __init__(self, parent):
        self.listeDonnees = [
            _("Options générales"),
            {"cat": "check", "label": _("Export des Ventes"), "description": _("Export des Ventes"),
             "code": "export_ventes",
             "tip": _("Cochez pour exporter les ventes, les avoirs et les prestations saisies"), "defaut": True,
             "obligatoire": True},
            {"cat": "check", "label": _("Export des Règlements"), "description": _("Export des Règlements"),
             "code": "export_reglements", "tip": _("Cochez pour exporter les règlements"), "defaut": True,
             "obligatoire": True},
            {"cat": "check", "label": _("Ecritures déjà transférées"),
             "description": _("Ecritures déjà transférées"), "code": "retransfert",
             "tip": _("Attention risque de doublon dans la compta"), "defaut": False, "obligatoire": True},
            {"cat": "choix", "label": _("Détails ventes pour clients"),
             "description": _("Option regroupement des ventes"), "code": "option_ventes",
             "tip": _("Sélectionnez le mode de regroupement des ventes dans le compte client"),
             "choix": [_("Par numero de pièce comptable"), _("Par prestation")], "defaut": 0, "obligatoire": True},
            {"cat": "choix", "label": _("Option type de règlements         "),
             "description": _("Option sélection des règlements"), "code": "option_reglements",
             "tip": _("La date comptable des règlements dépend de ce choix"),
             "choix": [_("Seuls les règlements avec dépôt sur la période sont transférés"),
                       _("Transfère tous les règlements à leur date de saisie (déposés ou pas)")], "defaut": 0,
             "obligatoire": True},
            {"cat": "check", "label": _("Insérer une ligne d'entête"),
             "description": _("Insérer ligne noms des champs"), "code": "ligne_noms_champs",
             "tip": _("Cochez pour insérer en début de fichier une ligne avec les noms des champs"), "defaut": False,
             "obligatoire": True},
            {"cat": "check", "label": _("Mémoriser les paramètres"),
             "description": _("Mémoriser les modifications de paramètres"), "code": "memoriser_parametres",
             "tip": _("Cochez pour mémoriser les paramètres à chaque sortie"), "defaut": False, "obligatoire": True},
            {"cat": "choix", "label": _("Encodage des caractères"),
             "description": _("Encodage des caractèers en sortie"), "code": "encodage",
             "tip": _("Si les accents posent problème préférer le sans accent"),
             "choix": [_("UTF8 standard"), _("Supprimer les accents"), _("DOS Latin"), _("Windows iso-8859-15")],
             "defaut": 0, "obligatoire": True},
            _("Codes journaux par défaut"),
            {"cat": "chaine", "label": _("Ventes"), "description": _("Code journal des ventes"),
             "code": "journal_ventes", "tip": _("Saisissez le code journal des ventes"), "defaut": _("VE"),
             "obligatoire": True},
            {"cat": "chaine", "label": _("Banque"), "description": _("Code journal des banques"),
             "code": "journal_banque", "tip": _("Saisissez le code journal de la banque"), "defaut": _("BQ"),
             "obligatoire": True},
            {"cat": "chaine", "label": _("ODventes"),
             "description": _("Code journal pour les prestations sans pièce"), "code": "journal_od_ventes",
             "tip": _("Code journal des prestations saisies directement"), "defaut": _("VT"), "obligatoire": True},
            _("Codes comptables par défaut"),
            {"cat": "chaine", "label": _("Ventes"), "description": _("Code comptable des ventes"),
             "code": "code_ventes", "tip": _(
                "Saisissez le code comptable des ventes (Peut être ajusté en détail dans le paramétrage des activités, des cotisations, des tarifs et des prestations)"),
             "defaut": "706", "obligatoire": True},
            {"cat": "chaine", "label": _("Collectif Clients"), "description": _("Code comptable des clients"),
             "code": "code_clients", "tip": _("Saisissez le code comptable des clients"), "defaut": "411",
             "obligatoire": True},
            {"cat": "chaine", "label": _("Règlements"), "description": _("Code comptable de la banque"),
             "code": "code_banque", "tip": _("Saisissez le code comptable de la banque"), "defaut": "512",
             "obligatoire": True},
            {"cat": "chaine", "label": _("Débours"), "description": _("Débours saisis en prestation"),
             "code": "debours", "tip": _("Saisissez le code comptable utilisé pour les débours saisis en prestations"),
             "defaut": "58140", "obligatoire": True},
            {"cat": "chaine", "label": _("Dons"), "description": _("Dons saisis en prestation"), "code": "dons",
             "tip": _("Saisissez le code comptable utilisé pour les dons saisis en prestation"), "defaut": "758",
             "obligatoire": True},
            {"cat": "chaine", "label": _("Autres"), "description": _("Prestations de type autres"), "code": "autres",
             "tip": _("Saisissez le code comptable des pestations de type 'autre'"), "defaut": "4711",
             "obligatoire": True},
        ]
        """_("Formats des libellés"),
        {"type":"chaine", "label":_("Client - Prestation"), "description":_("Format du libellé des ventes au client"), "code":"format_clients_ventes", "tip":_("Saisissez le format du libellé du total des ventes. Vous pouvez utiliser les mots-clés suivants : {DATE_DEBUT} {DATE_FIN}."), "defaut":_("Prestations du {DATE_DEBUT} au {DATE_FIN}"), "obligatoire":True},
        {"type":"chaine", "label":_("Client - Règlement"), "description":_("Format du libellé des règlements du client"), "code":"format_clients_reglements", "tip":_("Saisissez le format du libellé du total des règlements. Vous pouvez utiliser les mots-clés suivants : {DATE_DEBUT} {DATE_FIN}."), "defaut":_("Règlements du {DATE_DEBUT} au {DATE_FIN}"), "obligatoire":True},
        {"type":"chaine", "label":_("Prestation"), "description":_("Format du libellé des prestations"), "code":"format_prestation", "tip":_("Saisissez le format du libellé des prestations. Vous pouvez utiliser les mots-clés suivants : {NOM_PRESTATION} {DATE_DEBUT} {DATE_FIN}."), "defaut":u"{NOM_PRESTATION}", "obligatoire":True},
        {"type":"chaine", "label":_("Dépôt"), "description":_("Format du libellé des dépôts"), "code":"format_depot", "tip":_("Saisissez le format du libellé des dépôts. Vous pouvez utiliser les mots-clés suivants : {IDDEPOT} {NOM_DEPOT} {DATE_DEPOT} {MODE_REGLEMENT} {TYPE_COMPTABLE} {NBRE_REGLEMENTS}."), "defaut":u"{NOM_DEPOT} - {DATE_DEPOT}", "obligatoire":True},
        {"type":"chaine", "label":_("Règlement"), "description":_("Format du libellé des règlements"), "code":"format_reglement", "tip":_("Saisissez le format du libellé des règlements. Vous pouvez utiliser les mots-clés suivants : {IDREGLEMENT} {DATE} {MODE_REGLEMENT} {NOM_FAMILLE} {NUMERO_PIECE} {NOM_PAYEUR} {NUMERO_QUITTANCIER} {DATE_DEPOT} {NOM_DEPOT}."), "defaut":u"{MODE_REGLEMENT} {NOM_FAMILLE}", "obligatoire":True},
        ]"""
        CTRL_Parametres.__init__(self, parent, self.listeDonnees)

    def Generation(self, format="compta_ebp"):
        if self.Validation() == False:
            return False
        # Récupération des paramètres, puis test cohérence
        dictParametres = self.GetParametres()
        fDon = Donnees(dictParametres)
        if fDon.coherent == False:
            return False
        numLigne = 1
        listeLignesTxt = []

        iso = 'utf-8'
        encodage = dictParametres["encodage"]
        if encodage == 1:
            iso = 'sans'
        elif encodage == 2:
            iso = 'latin'
        elif encodage == 3:
            iso = 'iso-8859-15'

        # Ligne d'entête
        if dictParametres["ligne_noms_champs"] == True:
            if format in ("compta_quadra_fixe", "compta_matt_fixe"):
                wx.MessageBox(
                    "La présence d'une entête dans le fichier générera un message 'ligne incorrecte' lors l'import",
                    x=1000, y=1000)
            listeLignesTxt.append(self.EnteteLigne(format))

        dlgAttente = PBI.PyBusyInfo(_("Appel de données préalables au traitement..."), parent=None,
                                    title=_("Veuillez patienter..."),
                                    icon=wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Logo.png"), wx.BITMAP_TYPE_ANY))
        wx.Yield()
        # Ventes: traitement des lignes de factures et prestations
        if dictParametres["export_ventes"] == True:
            if dictParametres["option_ventes"] == 0:
                lignesVentes = fDon.GetPieces()
            elif dictParametres["option_ventes"] == 1:
                lignesVentes = fDon.GetPrestations(datePrestPourConsos=True)
            if lignesVentes != False:
                for ID, ligne in sorted(lignesVentes, key=TakeFirst):
                    if ligne["montant"] != FloatToDecimal(0.0):
                        listeLignesTxt.append(self.FormateLigne(format, ligne, numLigne))
                        numLigne += 1
                lignesVtes = fDon.GetPrestations(datePrestPourConsos=False)
                if lignesVtes != False:
                    for ID, ligne in sorted(lignesVtes, key=TakeFirst):
                        if ligne["montant"] != FloatToDecimal(0.0):
                            listeLignesTxt.append(self.FormateLigne(format, ligne, numLigne))
                            numLigne += 1

        # Banque: Traitement des lignes de règlements
        if dictParametres["export_reglements"] == True:
            if dictParametres["option_reglements"] != 0:
                lignesBanques = fDon.GetReglements_OD()
                if len(lignesBanques) > 0:
                    for ID, ligne in sorted(lignesBanques, key=TakeFirst):
                        if ligne["montant"] != FloatToDecimal(0.0):
                            listeLignesTxt.append(self.FormateLigne(format, ligne, numLigne))
                            numLigne += 1
            else:
                lignesBanques = fDon.GetReglements_Depots()
                if len(lignesBanques) > 0:
                    for ID, ligne in sorted(lignesBanques, key=TakeFirst):
                        if ligne["montant"] != FloatToDecimal(0.0):
                            listeLignesTxt.append(self.FormateLigne(format, ligne, numLigne))
                            numLigne += 1
        del dlgAttente

        # Génération des lignes 'plan comptable', insérées devant les lignes d'écriture
        listeCptTxt = []
        numCpt = 0
        for compte, libCompte in fDon.dictPC.items():

            listeCptTxt.append(self.FormateCompte(format,(compte,libCompte),numLigne))
            numCpt +=1
        if numCpt >0:
            listeLignesTxt = listeCptTxt + listeLignesTxt
            numLigne += numCpt

        # Finalisation du texte
        if numLigne == 1:
            dlg = wx.MessageDialog(self, _("Aucune ligne ne correspond à cette selection !"), _("Information"),
                                   wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
        else:
            texte = "\n".join(listeLignesTxt)
            fin = chr(10) + chr(26)
            nomFichier = _("Noethys")
            self.CreationFichier(nomFichier=nomFichier, texte=texte + fin, iso=iso)

    def EnteteLigne(self, format):
        if format == "compta_matt_delimite":
            return Export_compta_matt_delimite(None)
        if format == "compta_matt_fixe":
            return XImportLine(None, None).entete
        if format == "compta_ebp":
            return Export_compta_EBP(None, None)
        if format == "compta_quadra_fixe":
            return XImportLine(None, None).entete

    def FormateLigne(self, format, ligne, numLigne):
        montant = ligne["montant"]
        sens = ligne["sens"]
        ligne["montant"], ligne["sens"] = GetSens(montant, sens)

        if format == "compta_matt_delimite":
            return Export_compta_matt_delimite(ligne)

        if format == "compta_matt_fixe":
            return XImportLine(ligne, numLigne).getDataMatth()

        if format == "compta_ebp":
            return Export_compta_EBP(ligne, numLigne)

        if format == "compta_quadra_fixe":
            return XImportLine(ligne, numLigne).getDataQuadra()

    def FormateCompte(self, format, tplCpt, numLigne):
        compte, libelle = tplCpt
        lib = libelle.strip().replace(" ","")
        ligne = {"compte": compte, "libelle": libelle, "cle": lib[:7]}
        if compte[:2]=='01':
            ligne["coll"] = CPTCLIENTS
        if format == "compta_quadra_fixe":
            return XImportLine(ligne, numLigne, cpt=True).getCptaQuadra()

class Dialog(wx.Dialog):
    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, -1, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX)
        self.parent = parent
        self.DB = GestionDB.DB()
        dateDebut = self.DB.GetParam(param="DebutCompta",type="date",user = "Any")
        if dateDebut == None:
            #fixation d'une date de Migration
            dateDebut = str(datetime.date(datetime.date.today().year,0o1,0o1))
            self.DB.SetParam(param="DebutCompta", value=dateDebut, type="date", user = "Any", unique= True)
        dateFin = DateDDenEng(datetime.date.today())
        self.DB.SetParam(param="FinCompta", value=dateFin, type="date", user = "Any", unique = True)

        # Bandeau
        intro = _("Sélectionnez les dates de la période à exporter, choisissez le format d'export correspondant à votre logiciel de compatibilité puis renseignez les paramètres nécessaires avant cliquer sur Générer. Vous obtiendrez un fichier qu'il vous suffira d'importer depuis votre logiciel de comptabilité.")
        titre = _("DLG_Export_compta : Export des écritures comptables")
        self.SetTitle(titre)
        self.ctrl_bandeau = CTRL_Bandeau.Bandeau(self, titre=titre, texte=intro, hauteurHtml=30, nomImage="Images/22x22/Smiley_nul.png")
        
        # Période
        self.box_periode_staticbox = wx.StaticBox(self, wx.ID_ANY, _("Période"))
        self.label_date_debut = wx.StaticText(self, wx.ID_ANY, "Du")
        self.ctrl_date_debut = CTRL_Saisie_date.Date2(self)
        self.label_date_fin = wx.StaticText(self, wx.ID_ANY, _("au"))
        self.ctrl_date_fin = CTRL_Saisie_date.Date2(self)
        self.ctrl_date_debut.SetDate(dateDebut)
        self.ctrl_date_fin.SetDate(str(dateFin))

        # Logiciel de sortie
        self.box_logiciel_staticbox = wx.StaticBox(self, -1, _("Format d'export"))
        self.ctrl_logiciel = CTRL_Logiciel(self)

        # Paramètres
        self.box_parametres_staticbox = wx.StaticBox(self, wx.ID_ANY, _("Paramètres"))
        self.ctrl_parametres = CTRL_Lanceur(self)
        
        self.bouton_reinitialisation = CTRL_Propertygrid.Bouton_reinitialisation(self, self.ctrl_parametres)
        self.bouton_sauvegarde = CTRL_Propertygrid.Bouton_sauvegarde(self, self.ctrl_parametres)

        # Boutons
        self.bouton_aide = CTRL_Bouton_image.CTRL(self, texte=_("Aide"), cheminImage=Chemins.GetStaticPath("Images/32x32/Aide.png"))
        self.bouton_ok = CTRL_Bouton_image.CTRL(self, texte=_("Générer le fichier"), cheminImage=Chemins.GetStaticPath("Images/32x32/Disk.png"))
        self.bouton_recap = CTRL_Bouton_image.CTRL(self, texte=_("Récap des transferts"), cheminImage=Chemins.GetStaticPath("Images/32x32/Facture.png"))
        self.bouton_fermer = CTRL_Bouton_image.CTRL(self, texte=_("Fermer"), cheminImage=Chemins.GetStaticPath("Images/32x32/Fermer.png"))

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_BUTTON, self.OnBoutonAide, self.bouton_aide)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonOk, self.bouton_ok)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonRecap, self.bouton_recap)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonFermer, self.bouton_fermer)
        self.Bind(wx.EVT_CLOSE, self.OnBoutonFermer)
        
        wx.CallAfter(self.ctrl_date_debut.SetFocus)

    def __set_properties(self):
        self.ctrl_date_debut.SetToolTip(wx.ToolTip(_("Saisissez la date de début de la période à exporter")))
        self.ctrl_date_fin.SetToolTip(wx.ToolTip(_("Saisissez la date de fin de la période à exporter")))
        self.bouton_aide.SetToolTip(wx.ToolTip(_("Cliquez ici pour obtenir de l'aide")))
        self.bouton_ok.SetToolTip(wx.ToolTip(_("Cliquez ici pour lancer la génération des fichiers d'exportation")))
        self.bouton_recap.SetToolTip(wx.ToolTip(_("Cliquez ici pour un récapitulatif des exportations")))
        self.bouton_fermer.SetToolTip(wx.ToolTip(_("Cliquez ici pour fermer")))
        self.SetMinSize((700, 680))

    def __do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(4, 1, 10, 10)
        
        grid_sizer_haut = wx.FlexGridSizer(1, 2, 10, 10)
        
        box_periode = wx.StaticBoxSizer(self.box_periode_staticbox, wx.VERTICAL)
        grid_sizer_periode = wx.FlexGridSizer(2, 2, 5, 5)
        grid_sizer_base.Add(self.ctrl_bandeau, 0, wx.EXPAND, 0)
        grid_sizer_periode.Add(self.label_date_debut, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_periode.Add(self.ctrl_date_debut, 0, 0, 0)
        grid_sizer_periode.Add(self.label_date_fin, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_periode.Add(self.ctrl_date_fin, 0, 0, 0)
        box_periode.Add(grid_sizer_periode, 1, wx.ALL|wx.EXPAND, 10)
        grid_sizer_haut.Add(box_periode, 1, wx.EXPAND, 10)
        
        box_logiciel = wx.StaticBoxSizer(self.box_logiciel_staticbox, wx.VERTICAL)
        grid_sizer_logiciel = wx.FlexGridSizer(1, 2, 5, 5)
        grid_sizer_logiciel.Add(self.ctrl_logiciel, 0, wx.EXPAND, 0)
        grid_sizer_logiciel.AddGrowableCol(0)
        box_logiciel.Add(grid_sizer_logiciel, 1, wx.ALL|wx.EXPAND, 10)
        grid_sizer_haut.Add(box_logiciel, 1, wx.EXPAND, 10)
        
        grid_sizer_haut.AddGrowableCol(1)
        grid_sizer_base.Add(grid_sizer_haut, 1, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)
        
        box_parametres = wx.StaticBoxSizer(self.box_parametres_staticbox, wx.VERTICAL)
        grid_sizer_parametres = wx.FlexGridSizer(1, 2, 5, 5)
        grid_sizer_parametres.Add(self.ctrl_parametres, 1, wx.ALL | wx.EXPAND, 0) 

        grid_sizer_parametres_boutons = wx.FlexGridSizer(5, 1, 5, 5)
        grid_sizer_parametres_boutons.Add(self.bouton_reinitialisation, 1, wx.ALL | wx.EXPAND, 0) 
        grid_sizer_parametres_boutons.Add(self.bouton_sauvegarde, 1, wx.ALL | wx.EXPAND, 0) 
        grid_sizer_parametres.Add(grid_sizer_parametres_boutons, 1, wx.ALL | wx.EXPAND, 0) 
        
        grid_sizer_parametres.AddGrowableRow(0)
        grid_sizer_parametres.AddGrowableCol(0)
        box_parametres.Add(grid_sizer_parametres, 1, wx.ALL | wx.EXPAND, 10) 
        grid_sizer_base.Add(box_parametres, 1, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)
        
        grid_sizer_boutons = wx.FlexGridSizer(1, 5, 10, 10)
        grid_sizer_boutons.Add(self.bouton_aide, 0, 0, 0)
        grid_sizer_boutons.Add((20, 20), 0, wx.EXPAND, 0)
        grid_sizer_boutons.Add(self.bouton_ok, 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_recap, 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_fermer, 0, 0, 0)
        grid_sizer_boutons.AddGrowableCol(1)
        grid_sizer_base.Add(grid_sizer_boutons, 1, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 10)
        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)
        grid_sizer_base.AddGrowableRow(2)
        grid_sizer_base.AddGrowableCol(0)
        self.Layout()
        self.CenterOnScreen() 

    def OnBoutonAide(self, event):  
        from Utils import UTILS_Aide
        UTILS_Aide.Aide("")

    def OnBoutonFermer(self, event): 
        if self.ctrl_parametres.GetPropertyByName("memoriser_parametres").GetValue() == True :
            self.ctrl_parametres.Sauvegarde()
        dateDebut = self.ctrl_date_debut.GetDate()
        self.DB.SetParam(param="DebutCompta", value=dateDebut, type="date", user = "Any", unique = True)
        dateFin = self.ctrl_date_fin.GetDate()
        self.DB.SetParam(param="FinCompta", value=dateFin, type="date", user = "Any", unique = True)
        self.EndModal(wx.ID_CANCEL)

    def OnBoutonOk(self, event): 
        global CONTEXT
        CONTEXT = None
        format = self.ctrl_logiciel.GetCode()
        if format == "compta_matt_fixe":
            CONTEXT = 'MATTH'
        if format == "compta_quadra_fixe":
            CONTEXT ='QUADRA'
        self.ctrl_parametres.Generation(format)

    def OnBoutonRecap(self, event):
        from Dlg import DLG_Liste_transferts
        dateFin = self.ctrl_date_fin.GetDate()
        dlg = DLG_Liste_transferts.Dialog(self,dateFin = dateFin)
        dlg.ShowModal()

# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

if __name__ == "__main__":
    app = wx.App(0)
    dlg = Dialog(None)
    app.SetTopWindow(dlg)
    dlg.ShowModal()
    app.MainLoop()

