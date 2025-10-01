#!/usr/bin/env python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------
# Application :    Noethys, Matthania mars 2022
# Auteur:          Jacques BRUNEL
# Licence:         Licence GNU GPL
# Gestion du diagnostic de cohérence de la facturation et réparations
#------------------------------------------------------------------------

import wx
import GestionDB
import GestionInscription
import GestionPieces as fGest
from Data import DATA_Tables

def Nz(valeur):
    if valeur == None:
        valeur = 0.0
    return valeur

# fonctions lancées par RepareIncoherences via DICT_PARAMS
def Corr_ptnPrinc(parent,IDfamille, dLigne, **kw):

    def actionPrestation():
        # Changements incomplets: réalignement des données sur la pièce mère
        if dLigne["champ"] in ("IDactivite", "IDcategorie_tarif","IDindividu"):
            return parent.RebuildPrestation(IDfamille,dLigne)
        if dLigne["cleOrig"] == "IDcontrat":
            return parent.CheckPrestationToPiece(dLigne)
        if dLigne["cleOrig"] == "IDfacture":
            return parent.CheckPrestationToFacture(dLigne)
        if dLigne["champCible"] in ("IDprestation"):
            return parent.SynchroPrestationToPiece(dLigne)

    def actionPiece():

        # les données de la prestation ne correspondent pas à la pièce qui est prioritaire
        tc = dLigne["tblCible"] == "prestations"
        c = dLigne["cleOrig"] == "pieIDprestation"
        cc = dLigne["champCible"] in ("IDindividu","IDactivite","IDgroupe","IDcategorie_tarif","montant")
        if tc & c & cc:
            return parent.RebuildPrestation(IDfamille,dLigne)

        # l'ID prestation de la pièce n'est pas dans les prestations
        cc = dLigne["champCible"] == "IDprestation"
        st = dLigne["ssType"] == "NoCle"
        if tc & c & cc &st:

            return parent.SynchroPrestationToPiece(dLigne)

        # selon la nature de la piece absence des consos
        tc = dLigne["tblCible"] in ("inscriptions")
        cc = dLigne["champCible"] in ("nbreConsos")
        if tc & cc: return parent.RebuildConsommations(IDfamille,dLigne)

        # Inscription absente
        tc = dLigne["tblCible"] == "inscriptions"
        c = dLigne["cleOrig"] == "pieIDinscription"
        sst = dLigne["ssType"] in ("NoCle","zzNoCle", "CleNone","NoTbl")
        if tc & c & sst:
            return parent.RebuildInscription(IDfamille,dLigne)

        # l'Inscription prime sur les pièces
        tc = dLigne["tblCible"] == "inscriptions"
        c = dLigne["cleOrig"] == "pieIDinscription"
        sst = dLigne["ssType"] in ("NoAtt")
        if tc & c & sst:
            return parent.SynchroPieceToInscription(dLigne)

    def actionConsommations():
        # Changements incomplets: réalignement des données sur la pièce mère
        if dLigne["champ"] in ("IDfamille","IDindividu","IDactivite","IDgroupe","IDcategorie_tarif","nbreConsos"):
            return parent.RebuildConsommations(IDfamille,dLigne)
        if dLigne["champ"] == "IDinscription" and dLigne["ssType"] in ("NoTbl","NoCle"):
            return parent.RebuildConsommations(IDfamille,dLigne)

    def actionFacture():
        return parent.RebuildFacture(IDfamille,dLigne)

    corr = False
    # travaux différents selon table origine
    if dLigne["table"] == "prestations":
        return actionPrestation()
    if dLigne["table"] == "matPieces":
        return actionPiece()
    if dLigne["table"] in ("consommations"):
        return actionConsommations()
    if dLigne["table"] in ("factures"):
        return actionFacture()
    return corr

def Corr_ptIsNull(parent,IDfamille, dLigne, **kw):
    corr = False
    # Si la pièce a perdu sa prestation plusieurs actions pour les commandes
    t = dLigne["table"] == "matPieces"
    c = dLigne["champ"] == "pieIDprestation"
    ret = parent.SynchroPrestationToPiece(dLigne)
    if ret: return ret
    n = dLigne["nature"] in ("COM")
    if t & c & n:
        return parent.RebuildPiece(IDfamille,dLigne)
    return corr
    # La pièce a perdu sa prestation on essaie de la raccrocher à

def Corr_ptNoNull(parent,IDfamille, dLigne, **kw):
    corr = False

    # Un devis ou réservation ne génère pas de prestation, on supprime le pointeur
    t = dLigne["table"] == "matPieces"
    c = dLigne["champ"] == "pieIDprestation"
    n = dLigne["nature"] in ("DEV","RES")
    if t & c & n:
        lstDonnees = [("pieIDprestation",None)]
        ret = parent.DB.ReqMAJ("matPieces",lstDonnees,"pieIDnumPiece",dLigne["ID"])
        dLigne["mess"] += "\nReqMAJ('matPieces'.%d :%s"%(dLigne["ID"],str(lstDonnees))
        if ret == "ok" : return True
        return False
    return corr

DICT_PARAMS = {
    "ptnPrinc": Corr_ptnPrinc,
    "mpFamPay": None,   # correction immédiate effectuée
    "prFamPay": None,   # correction immédiate effectuée
    "ptIsNull": Corr_ptIsNull,
    "ptNoNull": Corr_ptNoNull,
}

# paramétrage des pointeurs de tables principales:[tblOrig,cleOrig,champOrig,tblCible,champCible,flou]
def GET_PARAMS_POINTEURS(dictPieces,dictPrestations,dictConsommations,dictInscriptions,dictFactures,dictNumeros):
    """ table origine: qui pointe une table cible
        cleOrig: Champ de la table d'origine qui contient la clé premier champ de la table cible
        champOrig: champ de la table d'origine qui contient la valeur à rechercher dans la cible,
                    champOrig=None fait chercher dans toutes les lignes pour la famille (c'est long)
        table cible: qui est pointée par l'origine
        champCible: dans la table cible c'est le champ qui contient la valeur à vérifier
        flou: cherche une autre ligne dans la table cible  qui aurait la valeur cherchée, idem None en champOrig"""
    return [
        [dictPieces,"pieIDprestation","pieIDprestation", dictPrestations,"IDprestation"],
        [dictPieces,"pieIDprestation","pieIDfamille", dictPrestations,"IDfamille"],
        [dictPieces,"pieIDprestation","pieIDindividu", dictPrestations,"IDindividu"],
        [dictPieces,"pieIDprestation","pieIDactivite", dictPrestations,"IDactivite"],
        [dictPieces,"pieIDprestation","pieIDcategorie_tarif", dictPrestations,"IDcategorie_tarif"],
        [dictPieces,"pieIDprestation","montant", dictPrestations,"montant"],

        [dictPieces,"pieIDinscription","pieIDfamille", dictInscriptions,"IDfamille"],
        [dictPieces,"pieIDinscription","pieIDindividu", dictInscriptions,"IDindividu"],
        [dictPieces,"pieIDinscription","pieIDactivite", dictInscriptions,"IDactivite"],
        [dictPieces,"pieIDinscription","pieIDgroupe", dictInscriptions,"IDgroupe"],
        [dictPieces,"pieIDinscription","pieIDcategorie_tarif", dictInscriptions,"IDcategorie_tarif"],
        [dictPieces,"pieIDinscription","pieNature", dictInscriptions,"natures"],
        [dictPieces,"pieIDinscription","consos", dictInscriptions,"nbreConsos"],

        [dictPieces,"pieNoFacture","pieNoFacture", dictNumeros,"numero"],
        [dictPieces,"pieNoAvoir","pieNoAvoir", dictNumeros,"numero"],

        [dictPrestations,"IDfacture","IDfacture", dictFactures,"IDfacture"],

        [dictFactures, "IDfacture","numero", dictPieces, "pieNoFacture"],
        [dictFactures,"IDfacture","total", dictFactures,"SUM(montant)"],

        [dictPrestations,"IDcontrat","IDcontrat", dictPieces,"pieIDnumPiece"],
        [dictPrestations,"IDcontrat","IDprestation", dictPieces,"pieIDprestation"],
        [dictPrestations,"IDcontrat","IDfamille", dictPieces,"pieIDfamille"],
        [dictPrestations,"IDcontrat","IDindividu", dictPieces,"pieIDindividu"],
        [dictPrestations,"IDcontrat","IDactivite", dictPieces,"pieIDactivite"],
        [dictPrestations,"IDcontrat","IDcategorie_tarif", dictPieces,"pieIDcategorie_tarif"],
        [dictPrestations,"IDcontrat","montant", dictPieces,"montant"],

        [dictConsommations,"IDinscription","IDinscription", dictInscriptions,"IDinscription"],

        [dictInscriptions,"IDinscription","IDinscription", dictConsommations,"IDinscription"],
        [dictInscriptions,"IDinscription","IDcompte_payeur", dictConsommations,"IDcompte_payeur"],
        [dictInscriptions,"IDinscription","IDindividu", dictConsommations,"IDindividu"],
        [dictInscriptions,"IDinscription","IDactivite", dictConsommations,"IDactivite"],
        [dictInscriptions,"IDinscription","IDgroupe", dictConsommations,"IDgroupe"],
        [dictInscriptions,"IDinscription","IDcategorie_tarif", dictConsommations,"IDcategorie_tarif"],
    ]

def HarmonisationPiece(dPiece):
    dPiece["IDfamille"] = dPiece["pieIDfamille"]
    mtTransport = Nz(dPiece["piePrixTranspAller"]) + Nz(dPiece["piePrixTranspRetour"])
    dPiece["montant"] = round(mtTransport + Nz(dPiece["SUM(ligMontant)"]), 2)

    # Appel de toutes les données. Sous forme de lignes de table en ddd: IDfamille-IDtable-dRecord

class DiagDonnees():
    def __init__(self,DB,famille,**kw):
        self.withCompta = kw
        self.famille = famille
        self.DB = DB
        self.echecGet = "ok"
        self.lstIDfactures = []
        self.lstNoFactures = []

    # fonction d'appel des principaux champs d'une table
    def GetDictUneTable(self,table,lstChamps,where=None,leftJoin="",groupBy=""):
        req = """SELECT %s
                FROM %s 
                %s 
                %s 
                %s ;""" % (",".join(lstChamps), table, leftJoin, where, groupBy)
        mess = "DLGFacPie.DiagDonnees table %s"%table
        ret = self.DB.ExecuterReq(req, MsgBox=mess)
        if not ret == "ok":
            self.echecGet = ret
            return ret
        recordset = self.DB.ResultatReq()
        def degraisseLstChamps():
            # seuls les champs dont le premier de la liste est préfixé par la table seront dégraissés
            if not "." in lstChamps[0]:
                return
            ix = 0
            for champ in lstChamps:
                # enlève ce qui est entre '(' et '.' exemple: COUNT(inscription.IDinscription) => COUNT(IDinscription)
                mots = champ.split(".")
                if len(mots) > 1:
                    ssMots = mots[0].split("(")
                    prefixe = ""
                    if len(ssMots)>1 :
                        prefixe = ssMots[0]+"("
                    lstChamps[ix] = prefixe + mots[-1]
                ix += 1
            return

        degraisseLstChamps()
        ddTable = GestionInscription.RecordsetToDict(lstChamps, recordset)
        # compose les transpositions
        def setIDfamille(dic):
            IDfamille = None
            for item in ("famille","ompte_payeur"):
                for champ in lstChamps:
                    if item in champ.lower() and dic[champ] > 0:
                        IDfamille = dic[champ]
                        dic["IDfamille"] = IDfamille
                        break
                if IDfamille: break
            if not IDfamille: raise
            return IDfamille
        def setIDinscription(dic):
            for item in ("IDinscription","pieIDinscription"):
                if item in lstChamps:
                    if dic[item] and dic[item] > 0:
                        dic["IDinscription"] = dic[item]
                        break
            return

        # applique les transpositions sur toute la table
        dddRetour = {}
        for ID,dic in ddTable.items():
            setIDinscription(dic)
            IDfamille = setIDfamille(dic)
            if not IDfamille in dddRetour:
                dddRetour[IDfamille] = {}
            dddRetour[IDfamille][ID] = dic
        return dddRetour

    def WhereFamille(self,champ1,champ2=None):
        if not self.famille:
            where = "TRUE"
        else:
            where1 = "%s = %d" %(champ1,self.famille)
            if champ2:
                where = """
                    (%s)
                    OR (%s = %d
                    )"""%(where1,champ2,self.famille)
            else: where = where1
        return where

    def WhereCompta(self,champ):
        # ni en compta ni à transférer
        if (self.withCompta["inCpta"] != True) and (self.withCompta["noInCpta"] != True):
            where = "FALSE"
        # seulement déjà en compta
        elif self.withCompta["inCpta"] == True and (self.withCompta["noInCpta"] != True):
            where = "%s IS NOT NULL"%champ
        # seulement à transférer
        elif self.withCompta["noInCpta"]  == True and (self.withCompta["inCpta"] != True):
            where = "%s IS NULL"%champ
        # toutes écritures
        else:
            where = "TRUE"
        return where

    def GetOneMatPieces(self,IDnumPiece):
        # ----------- préparation de l'appel de matPieces --------------------------------------------------------------
        table = "matPieces"
        lstChamps = ["pieIDnumPiece","pieIDfamille","pieIDcompte_payeur","pieIDprestation","pieIDactivite",
                     "pieIDindividu","pieIDinscription","pieIDcategorie_tarif","pieIDgroupe","pieNature",
                     "pieNoFacture","pieNoAvoir","pieComptaFac","pieComptaAvo",
                     "piePrixTranspAller","piePrixTranspRetour","SUM(ligMontant)","COUNT(ligIDnumLigne)"]
        leftJoin = "LEFT JOIN matPiecesLignes ON matPieces.pieIDnumPiece = matPiecesLignes.ligIDnumPiece"
        groupBy = "GROUP BY %s"%(", ".join(lstChamps[:-2]))

        # Gestion du filtre pieces sur envoyé à la compta
        where = """
                WHERE (pieIDnumPiece = %d)"""%(IDnumPiece)

        # appel des pièces dans matPieces et matPiecesLignes
        dddPieces = self.GetDictUneTable(table,lstChamps,where,leftJoin,groupBy)
        dictPiece = None
        for IDfamille, ddPieces in dddPieces.items():
            if IDfamille == "nomTable": continue
            dictPiece = ddPieces[IDnumPiece]
            HarmonisationPiece(dictPiece)
        return dictPiece

    def GetMatPieces(self):
        # ----------- préparation de l'appel de matPieces --------------------------------------------------------------
        table = "matPieces"
        lstChamps = ["pieIDnumPiece","pieIDfamille","pieIDcompte_payeur","pieIDprestation","pieIDactivite",
                     "pieIDindividu","pieIDinscription","pieIDcategorie_tarif","pieIDgroupe","pieNature",
                     "pieNoFacture","pieNoAvoir","pieComptaFac","pieComptaAvo",
                     "piePrixTranspAller","piePrixTranspRetour","SUM(ligMontant)","COUNT(ligIDnumLigne)"]
        leftJoin = "LEFT JOIN matPiecesLignes ON matPieces.pieIDnumPiece = matPiecesLignes.ligIDnumPiece"
        groupBy = "GROUP BY %s"%(", ".join(lstChamps[:-2]))

        # Gestion du filtre pieces sur envoyé à la compta
        def setFiltrePieces():
            whereFamPay = self.WhereFamille("pieIDfamille","pieIDcompte_payeur")
            whereCptaFac = self.WhereCompta("matPieces.pieComptaFac")
            whereCptaAvo = self.WhereCompta("matPieces.pieComptaAvo")
            where = """
            WHERE (
                (   %s
                )
                AND(
                    (%s)
                    OR( (%s)
                         AND ( pieNature = 'AVO')
                    )
                )    
            )"""%(whereFamPay,whereCptaFac,whereCptaAvo)
            return where
        where = setFiltrePieces()

        # appel des IDmax piece par inscription
        req = """
            SELECT pieIDinscription,MAX(pieIDnumPiece)
            FROM matPieces
            %s
            GROUP BY pieIDinscription;"""%where
        mess = "DLGFacPie.DiagDonnees table %s"%table
        ret = self.DB.ExecuterReq(req, MsgBox=mess)
        if not ret == "ok":
            self.echecGet = ret
            return ret
        recordset = self.DB.ResultatReq()
        dictPiecesMax = {}
        for IDinscription, IDmax in recordset:
            dictPiecesMax[IDinscription] = IDmax

        # appel des pièces dans matPieces et matPiecesLignes
        dddPieces = self.GetDictUneTable(table,lstChamps,where,leftJoin,groupBy)
        self.lstIDinscriptions = []
        dictPieces = {"nomTable":"matPieces"}
        for IDfamille, ddPieces in dddPieces.items():
            if IDfamille == "nomTable": continue
            dictPieces[IDfamille] = {"dictDon":ddPieces,}
            # composition des listes ds dictPieces
            for IDpiece, dPiece in dictPieces[IDfamille]["dictDon"].items():
                if dPiece["pieNoFacture"] and not (dPiece["pieNoFacture"] in self.lstNoFactures):
                    self.lstNoFactures.append(dPiece["pieNoFacture"])
                if dPiece["pieNoAvoir"] and not (dPiece["pieNoAvoir"] in self.lstNoFactures):
                    self.lstNoFactures.append(dPiece["pieNoAvoir"])
                # l'IDinscription pour la famille (IDindividu == 0) est l'année, ce n'est pas un ID
                if dPiece["pieIDindividu"] > 0:
                    self.lstIDinscriptions.append(dPiece["pieIDinscription"])
                # harmonisation utile pour comparer les familles lors des tests pointeurs
                HarmonisationPiece(dPiece)
        return dictPieces,dictPiecesMax

    def GetPrestations(self):
        # ----------- préparation de l'appel de prestations ------------------------------------------------------------
        table = "prestations"
        leftJoin = "LEFT JOIN matPieces ON prestations.IDcontrat = matPieces.pieIDnumPiece"

        lstChamps = ["IDprestation","IDfamille","IDcompte_payeur","IDcontrat","IDactivite","IDindividu",
                     "IDcategorie_tarif","IDfacture","categorie","montant","compta"]

        # Gestion du filtre de prestations sur envoyé à la compta
        def setFiltrePrestations():
            whereFamille = self.WhereFamille("prestations.IDcompte_payeur")
            whereCompta = self.WhereCompta("prestations.compta")
            where = """
        WHERE(  (%s)
                AND (%s)
        )"""%(whereFamille,whereCompta)
            return where
            
        where = setFiltrePrestations()
        where += """
            AND (categorie LIKE 'conso%%')"""

        # appel des prestations
        dddPrestations = self.GetDictUneTable(table,lstChamps,where,leftJoin)
        dictPrestations = {"nomTable":"prestations"}
        for IDfamille, ddPrestations in dddPrestations.items():
            if IDfamille == "nomTable": continue
            dictPrestations[IDfamille] = {"dictDon":ddPrestations,
                                          }
            # composition des listes dans dictPrestations[IDfamille]
            for IDprestation, dPrestation in dictPrestations[IDfamille]["dictDon"].items():
                #self.lstIDpieces.append(dPrestation["IDcontrat"])
                if dPrestation["IDfacture"] and not (dPrestation["IDfacture"] in self.lstIDfactures):
                    self.lstIDfactures.append(dPrestation["IDfacture"])
        return dictPrestations

    def GetFactures(self):
        # ----------- préparation de l'appel de factures ------------------------------------------------------------
        table = "factures"
        leftJoin = """
              LEFT JOIN prestations ON factures.IDfacture = prestations.IDfacture"""
        lstChamps = ["factures.IDfacture","factures.IDcompte_payeur","factures.numero",
                     "factures.total","SUM(prestations.montant)","MAX(prestations.IDprestation)"]
        groupBy = "GROUP BY %s"%(", ".join(lstChamps[:-2]))

        # Gestion du filtre de factures sur liste venant des  prestations
        def setFiltreFactures():
            whereFamille = self.WhereFamille("factures.IDcompte_payeur")
            condOrphan = "prestations.IDprestation IS NULL"
            whereCompta = self.WhereCompta("prestations.compta")
            if len(self.lstIDfactures) > 0:
                condID = f"(factures.IDfacture in ({str(self.lstIDfactures)[1:-1]}))"
            else: condID = True
            if len(self.lstNoFactures) > 0:
                condNo = f"(numero in ({str(self.lstNoFactures)[1:-1]}))"
            else: condNo = True
            where = f"""
            WHERE   ({whereFamille})
                AND ({whereCompta})
                AND ( 
                    ({condOrphan})
                    OR
                    ({condID})
                    OR
                    ({condNo}))
                AND (prestations.montant <> 0)
                """
            return where
        where = setFiltreFactures()

        # appel des factures
        dddFactures = self.GetDictUneTable(table,lstChamps,where,leftJoin,groupBy)
        dictFactures = {"nomTable":"factures"}
        dictNumeros = {"nomTable":"numeros"}
        for IDfamille, ddFactures in dddFactures.items():
            if IDfamille == "nomTable": continue
            dictFactures[IDfamille] = {"dictDon":ddFactures,}
            ddNumeros = {}
            for IDfacture,dFacture in ddFactures.items():
                ddNumeros[dFacture["numero"]] = dFacture
            dictNumeros[IDfamille] = {"dictDon":ddNumeros,}
        return dictFactures,dictNumeros

    def GetInscriptions(self):
        # ----------- préparation et appel de inscriptions -------------------------------------------------------

        dictInscriptions = {"nomTable":"inscriptions"}
        # requete sql lancement
        if len(self.lstIDinscriptions) > 0:
            # appel des inscriptions
            whereFamille = self.WhereFamille("inscriptions.IDfamille","inscriptions.IDcompte_payeur")
            where = """
                (   (%s
                    )
                    AND (IDinscription in ( %s )
                    )
                )"""%(whereFamille,str(self.lstIDinscriptions)[1:-1])
            lstChamps = ["IDinscription", "IDfamille", "IDcompte_payeur",
                         "IDindividu", "IDactivite", "IDgroupe",
                         "IDcategorie_tarif"]
            ddInscriptions = DATA_Tables.GetDdRecords(  self.DB,"inscriptions",where,
                                                        lstChamps=lstChamps,
                                                        mess="GestionCoherence.GetInscriptions1")
            for IDinscription, dInscr in ddInscriptions.items():
                IDfamille = dInscr["IDfamille"]
                if not IDfamille in dictInscriptions:
                    dictInscriptions[IDfamille] = {"dictDon":{},}
                dictInscriptions[IDfamille]["dictDon"][IDinscription] = dInscr

        return dictInscriptions

    def GetConsommations(self):
        # ----------- préparation et l'appel de consommations ------------------------------------------------------
        table = "consommations"
        lstChamps = ["IDinscription","IDcompte_payeur","IDindividu",
                     "IDactivite","IDgroupe","IDcategorie_tarif","COUNT(IDconso)"]

        # Gestion du filtre de consommations sur envoyé à la compta s'appuie sur les inscriptions dans matPieces
        dddConsommations = {}
        # appel des consommations
        if len(self.lstIDinscriptions) > 0:
            where = "WHERE IDinscription in ( %s )"%str(self.lstIDinscriptions)[1:-1]
            groupBy = "GROUP BY %s"%",".join(lstChamps[:-1])
            # appel des consommations
            dddConsommations = self.GetDictUneTable(table,lstChamps,where,groupBy=groupBy)
        dictConsommations = {"nomTable":"consommations"}
        for IDfamille, ddConsommations in dddConsommations.items():
            if IDfamille == "nomTable": continue
            dictConsommations[IDfamille] = {"dictDon":ddConsommations,}
        return dictConsommations

    def GetTables(self):
        if not self.famille:
            attente = wx.BusyInfo("Lecture matPieces...")
        dictPieces, dictPiecesMax = self.GetMatPieces()
        if self.echecGet != "ok": return self.echecGet
        if not self.famille:
            attente = wx.BusyInfo("Vérif cohérence: Lecture prestations...")
        dictPrestations = self.GetPrestations()
        if self.echecGet != "ok": return self.echecGet
        if not self.famille:
            attente = wx.BusyInfo("Vérif cohérence: Lecture factures...")
        dictFactures,dictNumeros = self.GetFactures()
        if self.echecGet != "ok": return self.echecGet
        if not self.famille:
            attente = wx.BusyInfo("Lecture inscriptions...")
        dictInscriptions = self.GetInscriptions()
        if self.echecGet != "ok": return self.echecGet
        if not self.famille:
            attente = wx.BusyInfo("Lecture consommations...")
        dictConsommations = self.GetConsommations()
        if self.echecGet != "ok": return self.echecGet
        return [dictPieces,dictPrestations,dictFactures,dictNumeros,dictConsommations,dictInscriptions,dictPiecesMax]

# Diagnostic de cohérence des données principales de facturation
class Diagnostic():
    def __init__(self,parent,famille,inCpta=False,noInCpta=True,mute=True):
        kw = {"inCpta": inCpta,"noInCpta":noInCpta}
        if not hasattr(parent,"fGest") :
            mute = False
            self.DB = GestionDB.DB() # on ne fermera pas DB car lancement manuel
            self.fGest = GestionInscription.Forfaits(self,self.DB)
            mess = "Lancement manuel pour maintenance\n\nSinon signaler au développement\n"
            mess += "DLG_FacturationPieces.Diagnostic"
            wx.MessageBox(mess,"Mode Test")
        else:
            self.fGest = parent.fGest
            self.DB = self.fGest.DB
        self.famille = famille
        self.diagDonnees = DiagDonnees(self.DB,famille,**kw)

        self.coherence = False
        self.dlAnomalies = {}

        # Action de diagnostic
        if self.TestAllFamilles(famille,inCpta):
            ret = self.Action(famille,mute,**kw)
            if ret and ret != "ok":
                wx.MessageBox("%s"%str(ret),"Echec du diagnostic",style=wx.ICON_ERROR)
        del self.diagDonnees
        #fin de init et sortie

    # main du diagnostic
    def Action(self,famille,mute,**kw):

        if not self.famille:
            attente = wx.BusyInfo(u"Lecture des tables...")
        ret = self.GetDonnees(famille,**kw)
        if not self.famille: del attente
        if not ret == "ok":
            return ret
        ret = self.VerifieCoherences(**kw)
        if not ret == "ok":
            return ret
        self.coherence = True

        # Tentative de correction et rapport
        self.nbt =0
        for IDfamille, lstAnomalies in self.dlAnomalies.items():
            self.nbt += len(lstAnomalies)
        self.nb = 0
        for IDfamille, lstAnomalies in self.dlAnomalies.items():
            if len(lstAnomalies) == 0:
                continue
            self.RepareIncoherences(IDfamille,**kw)
            for ligne in lstAnomalies:
                if not ligne["corr"]:
                    self.coherence = False

        # affiche la conclusion
        def composeRapport():
            txtAll = ""
            nbCorr = 0
            nbNonCorr = 0

            lstIDfamilles = sorted(self.dlAnomalies.keys())
            for IDfamille in lstIDfamilles:
                lstAnomalies = self.dlAnomalies[IDfamille]
                if len(lstAnomalies) == 0 :
                    continue
                lignesCorr = [x["mess"] for x in lstAnomalies if x["corr"] == True]
                lignesNonCorr = [x["mess"] for x in lstAnomalies if x["corr"]==None or not x["corr"]]

                txtFamille = "----- Famille %d -----"%(IDfamille)
                if len(lignesCorr) > 0:
                    txtFamille +="\nCorrigées:(%d)\n"%len(lignesCorr)
                    for mess in lignesCorr:
                        txtFamille += mess + "\n"
                if len(lignesNonCorr) > 0:
                    txtFamille +="\nNon Corrigées:(%d)\n"%len(lignesNonCorr)
                    for mess in lignesNonCorr:
                        txtFamille += mess + "\n\n"
                nbCorr += len(lignesCorr)
                nbNonCorr += len(lignesNonCorr)
                txtAll += txtFamille
            style = wx.ICON_INFORMATION
            if self.coherence:
                txtCoherence = "ok"
            elif nbNonCorr == 0:
                txtCoherence = "ok après corrections"
            else:
                txtCoherence = "échec"
                style = wx.ICON_STOP
            texte = ""
            if len(txtAll) > 0:
                texte = "Rapport de cohérence: %d corrigées, %d non corrigées\n\n%s"%(nbCorr,nbNonCorr,txtAll)
            texte += "Cohérence facturation: %s"%txtCoherence
            return texte, style, len(txtAll)
        texte,style,lenBody = composeRapport()
        if (not mute) or (lenBody > 0):
            wx.MessageBox(texte,"Rapport cohérences",style=style)
        # fin de Action

    #todo historisation "MiseEnCoherence"

    def ReqMAJ(self,dLigne,nomTable, listeDonnees, nomChampID, ID,MsgBox=None):
        # Mise à jour d'une table sur une clé
        ret = self.DB.ReqMAJ(nomTable, listeDonnees, nomChampID, ID,MsgBox=MsgBox)
        dLigne["mess"] += "\nReqMAJ(%s.%d :%s"%(nomTable,ID,str(listeDonnees))
        if ret == "ok" : return True
        return False

    def ReqDEL(self,dLigne,nomTable, nomChampID, ID,MsgBox=None):
        # Mise à jour d'une table sur une clé
        ret = self.DB.ReqDEL(nomTable, nomChampID, ID,MsgBox=MsgBox)
        dLigne["mess"] += "\nReqDEL(%s.%d"%(nomTable,ID)
        if ret == "ok" : return True
        return False

    def MaxPieceInscription(self,IDinscription,mess):
        req = """
            SELECT pieIDinscription,MAX(pieIDnumPiece)
            FROM matPieces
            WHERE pieIDinscription = %d
            GROUP BY pieIDinscription
            ;"""%IDinscription
        ret = self.DB.ExecuterReq(req,MsgBox=mess)
        if ret != "ok":
            return False
        recordset = self.DB.ResultatReq()
        if len(recordset) > 0:
            IDinscr,IDnumPiece = recordset[0]
            return IDnumPiece
        return False

    def SynchroPrestationToPiece(self,dLigne):

        def synchroConsos(IDprestation, IDinscription):
            # inscription de la pièce de la prestation
            if len(dPrest) == 0:
                return False
            lstDonnees = [("IDprestation", IDprestation)]
            return self.ReqMAJ(dLigne,"consommations",lstDonnees,"IDinscription",IDinscription,MsgBox=mess + "31")

        # la pièce est demandeuse on la corrige
        if dLigne["table"] == "matPieces" and  dLigne["champ"] == "pieIDprestation":
            IDfamille = dLigne["IDfamille"]
            dPiece = self.dictPieces[IDfamille]["dictDon"][dLigne["ID"]]
            IDnumPiece = dPiece["pieIDnumPiece"]
            montantPiece = dPiece["montant"]
            nature = dPiece["pieNature"]

            def majIDprestationInPiece(lstDonnees):
                # Mise à jour de l'IDprestation dans la pièce
                return self.ReqMAJ(dLigne,"matPieces",lstDonnees,"pieIDnumPiece",IDnumPiece)

            if nature in ("DEV","RES"):
                # l'ID prestation aurait dû être nulle RAZ de l'IDprestation dans pièce
                lstDonnees = [("pieIDprestation",None)]
                return majIDprestationInPiece(lstDonnees)

            # Recherche du contrat dans les prestations
            lstChamps = ("IDprestation","categorie","montant")
            req = "SELECT %s FROM prestations WHERE IDcontrat = %d"%(", ".join(lstChamps),IDnumPiece)
            ret = self.DB.ExecuterReq(req,MsgBox="DLG_FacturationPieces.SynchroPrestationToPiece")
            if ret != "ok":
                return False
            recordset = self.DB.ResultatReq()
            IDprestation = None
            if len(recordset) == 0 and nature == "COM":
                # retrograde la pièce en réservation si commande
                lstDonnees = [("pieIDprestation",None),("pieNature","RES")]
                return majIDprestationInPiece(lstDonnees)
            elif len(recordset) == 1:
                # une seule prestation trouvée on prend
                IDprestation = recordset[0][0]
            elif len(recordset)  == 2:
                # cas d'un avoir et de sa conso initiale. Choisir la conso initiale
                for IDprest,categorie,montant in recordset:
                    if categorie != "consommation":
                        continue
                    if montant == montantPiece:
                        IDprestation = IDprest
            if IDprestation:
                return majIDprestationInPiece([("pieIDprestation",IDprestation)])
            return False

        # la piece avoir n'a plus ID on vérifie s'il y a une prestation 'consoAvoir'
        elif dLigne["table"] == "matPieces" and dLigne["champ"] == "pieNoAvoir":
            where = " IDcontrat = %d AND categorie = 'consoavoir' "%dLigne['ID']
            ddPrestations = DATA_Tables.GetDdRecords(self.DB,"prestations",where,mess=" SynchroPrestationToPiece 10")
            if len(ddPrestations) == 0:
                # il n'y avait pas non plus de prestations, on change la nature
                lstDonnees = [('pieNature','FAC')]
                return self.ReqMAJ(dLigne, "matPieces", lstDonnees, "pieIDnumPiece",
                                   dLigne['ID'], MsgBox="SynchroPrestationToPiece 20")
            return False

        # la prestation est demandeuse on corrige sa cible
        elif dLigne["table"] == "prestations" and dLigne["champ"] == "IDprestation":
            IDprestation = dLigne["ID"]
            # appel prestation, pièce et inscription concernées
            mess = "DLGFacturationPieces.SynchroPrestationToPiece"
            # Reprise de la prestation demandeuse
            dPrest = DATA_Tables.GetDictRecord(self.DB,"prestations",IDprestation,mess=mess + " 1")
            if len(dPrest) == 0:
                return False

            IDcontrat = dPrest["IDcontrat"]
            # piece de la prestation
            dPiece = DATA_Tables.GetDictRecord(self.DB,"matPieces",IDcontrat,mess=mess + " 2")
            IDinscription = dPiece["pieIDinscription"]
            if len(dPrest) == 0:
                # si la prestation a disparu c'est qu'il y a dèjà eu une correction induite par matPiece
                return True
            # Verif nature
            if dPiece["pieNature"] == "AVO" and dLigne["ssType"] == "NoAtt":
                if dPrest["categorie"] != "consoavoir":
                    return self.ReqMAJ(dLigne,"prestations",[("categorie","consoavoir")],
                                       "IDprestation",IDprestation,MsgBox=mess)
            # mise en cohérence de pieIDprestation dans piece et les consos
            if dPiece["pieNature"] in ("FAC","COM"):
                lstDonnees = [("pieIDprestation", IDprestation),]
                ret = self.ReqMAJ(dLigne,"matPieces",lstDonnees,"pieIDnumPiece",IDcontrat,MsgBox=mess + " 3")
                if ret != "ok":
                    return False
                return synchroConsos(IDprestation, IDinscription)

            elif dPiece["pieNature"] == "AVO" and dPiece["pieIDprestation"] ==  None:
                # normal donc corrigé
                return True
            else:
                return False

        #raise Exception("Cas non prévu: %s"%str(dLigne))

    def SynchroInscriptionToConsommation(self,dLigne):
        # mises à jour des consommations d'une inscription par écrasement de ses valeurs communes
        IDinscription = dLigne["IDinscription"]
        lstChamps = ("IDcompte_payeur","IDindividu","IDactivite","IDgroupe","IDcategorie_tarif")
        req = "SELECT %s FROM inscriptions WHERE IDinscription = %d"%(", ".join(lstChamps),IDinscription)
        ret = self.DB.ExecuterReq(req,MsgBox="DLG_FacturationPieces.SynchroInscrToConsos")
        if ret == "ok":
            recordset = self.DB.ResultatReq()
            if len(recordset)>0:
                inscription = recordset[0]
            else: ret = "ko"
        if not ret == "ok":
            return False

        lstDonnees = []
        for champ in lstChamps:
            valeur = inscription[lstChamps.index(champ)]
            lstDonnees.append((champ,valeur))
        lstCles = [("IDinscription",IDinscription)]

        # correction dans fichier
        ret = self.DB.ReqMAJcles("consommations",lstDonnees,lstCles,MsgBox="DLG_FacturationPieces.SynchroInscrToConsos")
        if ret == "ok":
            dLigne["mess"] += "\nReqMAJ('consommations'.%d :%s"%(IDinscription,str(lstDonnees))
            return True
        return False

    def SynchroPieceToInscription(self,dLigne):
        IDfamille = dLigne["IDfamille"]
        IDinscription = dLigne["IDinscription"]
        mess = "DLG_FacturationPieces.SynchroPieceToInscription"
        # préalable recharger dPiece
        dPiece = self.dictPieces[IDfamille]["dictDon"][dLigne["ID"]]
        IDmax = self.MaxPieceInscription(IDinscription,mess)
        if dPiece["pieIDnumPiece"] != IDmax:
            # présence d'autre pièces pointant cette inscriptions, seule la dernière corrige
            return True
        else:
            lstDonnees = []
            for champ in ("IDindividu","IDactivite","IDgroupe","IDcategorie_tarif"):
                lstDonnees.append((champ,dPiece["pie"+champ]))
            # correction dans fichier
            return self.ReqMAJ(dLigne,"inscriptions",lstDonnees,"IDinscription",dPiece["pieIDinscription"],MsgBox=mess)

    def CheckPrestationToFacture(self,dLigne):
        if dLigne["table"] != "prestations" or dLigne["cleOrig"] != "IDfacture":
            raise Exception("Pb d'itineraire: %s"%str(dLigne))
            return False
        IDfamille = dLigne["IDfamille"]
        mess = "DLG_FacturationPieces.CheckPrestationToFacture"
        dPrest = DATA_Tables.GetDictRecord(self.DB,"prestations",dLigne["ID"],mess)
        if dLigne["champCible"] == "IDfacture" and dLigne["ssType"] == "NoCle":
            # Une seule pièce sans montant ne génére pas de facture
            if round(dPrest["montant"],2) == 0.0:
                return True

    def CheckPrestationToPiece(self,dLigne):
        if dLigne["table"] != "prestations" or dLigne["cleOrig"] != "IDcontrat":
            raise Exception("Pb d'itineraire: %s"%str(dLigne))
            return False
        IDfamille = dLigne["IDfamille"]
        # prestation orpheline de sa piece
        mess = "DLGFacPie.Corr_ptnPrinc GetDdRecords prestations"
        where = """
                        IDfamille = %d"""%IDfamille
        ddPrestations = DATA_Tables.GetDdRecords(self.DB,"prestations",where,mess=mess)
        try:
            dPrestation = ddPrestations[dLigne["ID"]]
            IDprestation = dLigne["ID"]
            IDnumPiece = dPrestation["IDcontrat"]
        except:
            return False
        if dLigne["ssType"] == "ToDel" and not dPrestation['compta']:
            # Reliquat de la prestation, avec la pièce en réservation non transféré
            ret = self.fGest.DelPrestations(self, {"IDprestation": IDprestation,
                                                   'IDnumPiece': None})
            dLigne["mess"] += "\nReqDEL('prestations'.%d" % (IDprestation)
            if ret == "ok": return True
        if not IDnumPiece:
            return False
        mess = "DLGFacPie.Corr_ptnPrinc prest orpheline"
        dPiece = DATA_Tables.GetDictRecord(self.DB,"matPieces",IDnumPiece,mess=mess) # piece pointée par la prestation
        # cas: la prestation pointe une pièce existante
        if dPiece != {}:
            IDprestTrouvee = dPiece["pieIDprestation"] # IDprestation pointée par la pièce
            if not IDprestTrouvee: # la pièce ne pointe pas de prestation
                if dPiece["pieNature"] in ('DEV','RES'):
                    if dPrestation["compta"] != None:
                        return False
                    # la pièce ne doit pas avoir de prestation, non transférée compta elle doit disparaître
                    ret = self.fGest.DelPrestations(self,{"IDprestation":dLigne["ID"],'IDnumPiece': None})
                    dLigne["mess"] += "\nReqDEL('prestations'.%d"%(dLigne["ID"])
                    if ret == "ok": return True

            # la piece pointe une prestation et la prestation une piece
            if IDprestTrouvee == IDprestation:
                # c'est la même: elles sont ensemble
                if dPiece["pieNature"] in  ("COM","FAC"):
                    # c'est ok, une correction a déjà dû passer
                    return True
                else:
                    # la piece n'aurait pas dû pointer cette prestation
                    return False
            else: # les deux ID diffèrent
                # vérifie le cas d'un avoir, seule la prestation de facture est pointée par celle de l'avoir
                if dPiece["pieNature"] == "AVO":
                    lstDonnees = [("categorie","consoavoir"),]
                    return self.ReqMAJ(dLigne,'prestations',lstDonnees,'IDprestation',dLigne["ID"])
                elif dPiece["pieNature"] in ("FAC","COM"):
                    altPrest = ddPrestations[IDprestTrouvee]
                    if altPrest["IDcontrat"] == IDnumPiece:
                        if dPrestation["compta"] != None:
                            # on ne pourra pas modifier un prestation transférée en compta
                            return False
                        # l'autre prestation est cohérente, avec la pièce, on la supprime
                        ret = self.fGest.DelPrestations(self,{"IDprestation":IDprestation,'IDnumPiece': None})
                        dLigne["mess"] += "\nReqDEL('prestations'.%d"%(IDprestation)
                        if ret == "ok": return True
                    return False
        # cas: cle piece non trouvée on cherche une éventuelle sansEnf pour la prestation orpheline
        mess = "DLGFacPie.Corr_ptnPrinc GetDdRecords matPieces"
        where = """
                pieIDfamille = %d"""%IDfamille
        ddPieces = DATA_Tables.GetDdRecords(self.DB,"matPieces",where,mess=mess)
        for IDlu, dPiece in ddPieces.items():
            if dPiece["pieIDprestation"] == dLigne["ID"]:
                # la piece a changé d'ID mais elle pointe toujours la prestation on réactualise le numero contrat
                lstDonnees = [("IDcontrat",dPiece["pieIDnumPiece"]),("categorie","consommation")]
                return self.ReqMAJ(dLigne,"prestations",lstDonnees,"IDprestation",dLigne["ID"])
        if (not ("IDindividu" in dPrestation.keys())) or (not ("IDactivite" in dPrestation.keys())):
            return False
        if dPrestation["IDindividu"] == 0 or dPrestation["IDactivite"] == 0:
            # il s'agit d'un niveau famille, sans pièce: on supprime la prestation
            mess = "DLGFacPie.CheckPrestationToPiece1"
            return self.ReqDEL(dLigne,"prestations","IDprestation",dPrestation["IDprestation"],MsgBox=mess)

        # cas: dernière recherche floue on cherche une correspondance activité-individu
        req = """SELECT pieIDnumPiece,pieIDprestation FROM matPieces WHERE pieIDactivite = %d and pieIDindividu = %d
                ;"""%(dPrestation["IDindividu"],dPrestation["IDactivite"] )
        mess = "DLGFacPie.CheckPrestationToPiece2"
        ret = self.DB.ExecuterReq(req, MsgBox=mess)
        if not ret == "ok":
            return ret
        recordset = self.DB.ResultatReq()
        for IDlu, IDprestlu in recordset:
            dPiece = DATA_Tables.GetDictRecord(self.DB,"matPieces",IDlu,mess=mess)
            prestLue = DATA_Tables.GetDictRecord(self.DB,"inscriptions",IDprestlu,mess=mess)

            # test de la non présence de la prestation pointée par la pièce, break si match
            if len(prestLue) == 0:
                continue
            # sansEnf trouvée pour l'orpheline mise en correspondance des deux
            lstDonnees = [("IDcontrat",dPiece["pieIDnumPiece"]),("categorie","consommation")]
            ret =  self.ReqMAJ(dLigne,"prestations",lstDonnees,"IDprestation",IDprestation)
            if ret != "ok": return False
            lstDonnees = [("pieIDprestation",IDprestation),]
            ret = self.ReqMAJ(dLigne,"matPieces",lstDonnees,"pieIDnumPiece",IDlu)
            if ret == "ok": return True
        # pas de piece sansEnf on supprime l'orpheline si pas niveau famillle
        if dPrestation["compta"] != None:
            # on ne pourra pas modifier un prestation transférée en compta
            return False
        ret = self.fGest.DelPrestations(self,{"IDprestation":IDprestation,'IDnumPiece': None})
        dLigne["mess"] += "\nReqDEL('prestations'.%d"%(IDprestation)
        if ret == "ok": return True

    def RebuildFacture(self,IDfamille,dLigne):
        mess = "DLGFactPiece.RebuildFacture"
        dFact = self.dictFactures[IDfamille]["dictDon"][dLigne["ID"]]
        if not (dLigne["table"] == "factures"):
            raise Exception("Pb d'itineraire: %s" % str(dLigne))

        if (dLigne["champCible"] == "SUM(montant)"):
            # appel des pièces de la facture pour vérif du montant attendu
            ddPieces = self.dictPieces[IDfamille]["dictDon"]
            mttPieces = 0.0
            for IDnumPiece, dPiece in ddPieces.items():
                if dPiece["pieNoFacture"] == dFact["numero"] or dPiece["pieNoAvoir"] == dFact["numero"]:
                    mttPieces += dPiece["montant"]
            if mttPieces == dFact["SUM(montant)"]:
                return self.ReqMAJ(dLigne,"factures",[("total",mttPieces),],
                                   "IDfacture",dLigne["ID"],MsgBox=mess)
        if ((dLigne["tblCible"] == "matPieces")
                and dLigne["champCible"].startswith("pieNo")
                and dLigne["table"] == "factures"):
            # la facture n'étant plus dans matPieces, vérif dans les prestations
            ok = False
            dfacture =  self.dictFactures[IDfamille]["dictDon"][dLigne["ID"]]
            if not dfacture["MAX(IDprestation)"]:
                # aucune prestation même en compta ne pointe cette facture
                ok = True
            if ok:
                ret = self.ReqDEL(dLigne,"factures","IDfacture",dLigne["ID"],mess)
                return ret
        return False

    def RebuildInscription(self,IDfamille,dLigne):
        # Appel des tables en relation
        ret = self.fGest.GetPieceModif(self,None,None,IDnumPiece = dLigne["ID"],DB=self.DB)
        if not ret:
            return False
        dPiece = self.fGest.dictPiece
        lstDonnees = []
        for champ in ("IDinscription","IDfamille","IDcompte_payeur","IDindividu",
                      "IDactivite","IDgroupe","IDcategorie_tarif"):
            lstDonnees.append((champ,dPiece[champ]))
        lstDonnees.append(("date_inscription",dPiece["dateCreation"]))
        # correction dans fichier
        ret = self.DB.ReqInsert("inscriptions",lstDonnees,retourID=False)
        dLigne["mess"] += "\nReqInsert('inscriptions'.%d :%s"%(dPiece["IDinscription"],str(lstDonnees))
        if ret == "ok":
            dLigne["IDinscription"] = dPiece["IDinscription"]
            self.RebuildConsommations(IDfamille,dLigne)
            return True
        return False

    def RebuildPrestation(self,IDfamille,dLigne):
        mess = "DLG_FacturationPiece.RebuildPrestation"
        # Appel des tables en relation
        if dLigne["table"] == "prestations":
            dPrestation = self.dictPrestations[IDfamille]["dictDon"][dLigne["ID"]]
            dPiece = self.dictPieces[IDfamille]["dictDon"][dPrestation["IDcontrat"]]
            if len(dPiece)>0 and dPiece["pieNature"] in ("FAC","COM"):
                dPrestation["categorie"] = "consommation"
            IDprestation = dLigne["ID"]
        elif dLigne["table"] == "matPieces":
            dPiece = self.dictPieces[IDfamille]["dictDon"][dLigne["ID"]]
            IDprestation = dPiece["pieIDprestation"]
            dPrestation = self.dictPrestations[IDfamille]["dictDon"][IDprestation]
        if dPrestation["compta"] == None:
            # traitement du montant
            if dLigne["champ"] == "montant" and len(dPiece) > 0:
                montant = dPiece["montant"]
                if dPiece["pieIDprestation"] == IDprestation and dPrestation["categorie"] == "consommation":
                    lstDonnees = [("montant",montant)]
                    return self.ReqMAJ(dLigne,"prestations",lstDonnees,
                                       "IDprestation",dPrestation["IDprestation"],MsgBox=mess)
                if dPiece["pieIDprestation"] != IDprestation and dPrestation["categorie"] == "consoavoir":
                    lstDonnees = [("montant",-montant)]
                    return self.ReqMAJ(dLigne,"prestations",lstDonnees,
                                       "IDprestation",dPrestation["IDprestation"],MsgBox=mess)
        lstDonnees = []
        for champ in ("IDfamille","IDcompte_payeur","IDindividu","IDactivite", "IDcategorie_tarif"):
            lstDonnees.append((champ,dPiece["pie"+champ]))
        # correction dans fichier de tout sauf montant
        if len(lstDonnees) >0:
            return self.ReqMAJ(dLigne,"prestations",lstDonnees,"IDprestation",dPrestation["IDprestation"],MsgBox=mess)

    def RebuildPiece(self,IDfamille,dLigne):
        #Reconstruction par dégradation en devis et retour nature d'origine ou del pièce si pas de liens
        dPiece = self.dictPieces[IDfamille]["dictDon"][dLigne["ID"]]
        # duplique les clé en noms standard
        dPiece["IDcompte_payeur"] = IDfamille
        for cle in ("IDinscription","IDactivite","IDnumPiece","IDindividu"):
            dPiece[cle] = dPiece["pie"+cle]

        # teste le montant
        def nbConsos(IDinscription):
            # les pièces niveau famille n'ont pas de conso
            if dPiece["pieIDindividu"] == 0:
                return 0
            try:
                nbConsos = self.dictConsommations[IDfamille]["dictDon"][IDinscription]["COUNT(ligIDnumLigne)"]
            except:
                mess = "Recherche l'Inscription de piece %d, absence innattendue"%dLigne["IDnumPiece"]
                raise Exception(mess)
        nbl = dPiece["COUNT(ligIDnumLigne)"]
        nbc = nbConsos(dLigne["IDinscription"])
        mtt = dPiece["montant"]
        nf = dPiece["pieIDindividu"] = 0
        # cas Del Piece
        if nbl < 2 and nbc == 0 and mtt == 0.0 and nf ==0:
            # une commande une ligne max,sans consos,sans prix_transports,niveau famille est vide on la supprime
            ret = self.DB.ReqDEL("matPieces","pieIDnumPiece",dPiece["pieIDnumPiece"])
            dLigne["mess"] += "\nReqDEL('matPieces'.%d"%(dPiece["pieIDnumPiece"])
            if ret == "ok" : return True
        # remet en devis puis dans la nature précédente pour tout réinitialiser
        natureOld = dPiece["pieNature"]
        ret1 = self.fGest.ChangeNaturePiece(self,dPiece,"DEV")
        ret2 = self.fGest.ChangeNaturePiece(self,dPiece,natureOld)
        if ret1 == "ok" and ret2 == "ok":
            dLigne["mess"] += "\nchgNature: %s=>DEV=>%s"%(natureOld,natureOld)
            return True
        return False

    def RebuildConsommations(self,IDfamille,dLigne):
        # Regénération des lignes de consommations à partir de l'inscription
        IDinscription = dLigne["IDinscription"]
        IDfamilleDligne = IDfamille
        # recherche par l'IDinscription poru confirmer la famille
        mess = "DLGFacPie.RebuildConsommations "
        req = """SELECT IDfamille FROM inscriptions WHERE IDinscription = %d"""%IDinscription
        ret = self.DB.ExecuterReq(req,MsgBox= mess + "1")
        recordset = []
        if ret == "ok":
            recordset = self.DB.ResultatReq()
            if len(recordset)>0:
                IDfamille = recordset[0][0]

        dInscr =  DATA_Tables.GetDictRecord(self.DB,"inscriptions",IDinscription,mess + "2")
        dCons =   DATA_Tables.GetDictRecord(self.DB,"consommations",IDinscription,mess + "21")

        # Cas de recherche d'inscription pas trouvée
        def rechercheFloueInscription():
            altIDinscr = None
            # l'inscription des consos n'existe pas, recherche par l'Individu activite de pièces sans consos
            req = """
                SELECT inscriptions.IDfamille, inscriptions.IDinscription
                FROM (inscriptions 
                LEFT JOIN consommations ON inscriptions.IDinscription = consommations.IDinscription) 
                INNER JOIN matPieces ON inscriptions.IDinscription = matPieces.pieIDinscription
                WHERE ((inscriptions.date_inscription > '2017-01-01') 
                        AND (consommations.IDconso) Is Null)
                        AND (matPieces.pieNature In ('FAC','COM','RES')
                        AND (IDindividu = %d)
                        AND (IDactivite = %d)
                GROUP BY inscriptions.IDfamille, inscriptions.IDinscription
                ;"""%(dCons["IDindividu"],dCons["IDactivite"])
            ret = self.DB.ExecuterReq(req,MsgBox="DLG_FacturationPieces.RebuildConsommations2")
            if ret == "ok":
                recordset = self.DB.ResultatReq()
                # récupére les données trouvées qui iront dans dLigne
                for altIDfam,   ltIDinscr in recordset:
                    altIDinscr
                    continue
            return altIDinscr
        if (len(dCons) > 0) and  (len(dInscr) == 0):
            altIDinscr = rechercheFloueInscription()
            if not altIDinscr:
                # pas d'inscription alternative Consos orphelines à supprimer
                return fGest.DelConsommations({"IDinscription":IDinscription})
            else:
                # on raccroche les consos orphelines sur l'activité veuve
                dictDonnees = DATA_Tables.GetDictRecord(self.DB,"inscriptions",altIDinscr,mess + "3")
                dLigne["mess"] += "\nModifeConsos pour inscription '%s'"%(dLigne["IDinscription"])
                return self.fGest.ModifieConsommations(self.dictDonnees,fromInscr=IDinscription)

        # les consos match une inscription: définit l'attendu
        if dInscr["parti"] == 1:
            consosAttendu = False
        else:
            if "AVO" in dInscr["natures"]:          consosAttendu = False
            elif not "DEV" in dInscr["natures"]:    consosAttendu = True
            elif "DEV" == dInscr["natures"]:        consosAttendu = False
            else: return False
        nbreConsos = dInscr["nbreConsos"]

        # cas traités
        if nbreConsos == 0 and consosAttendu != True:
            return self.SynchroInscriptionToConsommation(dLigne)

        # vérifier l'attendu et la réalité cohérence selon natures puis soit effacer soit regénérer
        if nbreConsos == 0 and consosAttendu == True:
            dLigne["mess"] += "\nAjoutConsos pour inscription '%s'"%(dLigne["IDinscription"])
            return self.fGest.AjoutConsommations(self,dInscr)

        # Envoi d'une simple synchro si on a trouvé une inscription
        if nbreConsos > 0 and consosAttendu == True:
            # il peut y avoir eu une confusion famille on reprend celle de l'inscription
            dLigne["IDfamille"] = IDfamille
            dLigne["IDinscription"] = IDinscription
            return self.SynchroInscriptionToConsommation(dLigne)

        # reste le cas : nbreConsos > 0 and consosAttendu != True
        dictDonnees = {}
        dictDonnees["IDinscription"] = IDinscription
        dictDonnees["IDfamille"] = IDfamille
        dictDonnees["IDprestation"] = None
        dLigne["mess"] += "\nDelConsos pour inscription '%s'"%(dLigne["IDinscription"])
        return self.fGest.DelConsommations(self,dictDonnees)

    # Lance la réparation des Incohérences
    def RepareIncoherences(self,IDfamille,**kw):
        # actions sur la table origine selon réponse cible
        lstAnomalies = self.dlAnomalies[IDfamille]
        if not self.famille:
            attente = wx.BusyInfo("Correction des anomalies...%d/%d"%(self.nb,self.nbt))
        for dLigne in lstAnomalies:
            self.nb +=1
            if dLigne["corr"] == True:
                continue
            if not (dLigne["type"] in DICT_PARAMS):
                mess = "Pb: GET_PARAMS_POINTEURS  presence type '%s' non present dans DICT_PARAMS"%dLigne["type"]
                raise Exception(mess)
            fn = DICT_PARAMS[dLigne["type"]]
            if not fn:
                continue
            # récupération dans 'corr' du résultat de la tentative de correction
            corr = fn(self,IDfamille,dLigne)
            if corr == True:
                # stockage de la dernière ligne du message d'anomalie enrichi de l'action de correction
                comm = dLigne["mess"].split("\n")[-1]
                self.fGest.Historise(None,IDfamille,"MiseEnCoherence",comm)
            dLigne["corr"] = corr

        if not self.famille: del attente

    # Lance les différents tests de cohérence
    def VerifieCoherences(self,**kw):
        lstTuplesTblCle = []
        dLigne = {"mess": "VerifieCoherence: "}

        # matPieces: test et correction de similitude IDcompte_payeur et IDfamille
        def piecesTestFamillePayeur():
            for IDfamille,ddPieces in self.dictPieces.items():
                if IDfamille == "nomTable": continue
                for ID, dict in ddPieces["dictDon"].items():
                    if dict["pieIDcompte_payeur"] == dict["pieIDfamille"]:
                        continue
                    corr = False
                    valeur = None
                    champ = None
                    IDfamille = dict["pieIDfamille"]
                    IDinscription = dict["IDinscription"]
                    if (not dict["pieIDcompte_payeur"]) and dict["pieIDfamille"]:
                        mess = "mpFamPay: Dans la table matPieces, famille %d, l'IDcompte_payeur avait disparu\n"%dict["pieIDfamille"]
                        champ = "pieIDcompte_payeur"
                        valeur = dict["pieIDfamille"]
                    elif (not dict["pieIDfamille"]) and dict["pieIDcompte_payeur"]:
                        mess = "mpFamPay=> Dans la table matPieces, famille %d, l'IDfamille avait disparu\n"%dict["pieIDcompte_payeur"]
                        champ = "pieIDfamille"
                        valeur = dict["pieIDcompte_payeur"]
                    else:
                        mess = "Dans la table matPiece, famille %d-%d, "%(dict["pieIDcompte_payeur"],dict["pieIDfamille"])
                        mess += "mpFamPay=> l'IDfamille et l'IDcompte_Payeur différent!!\n"
                    # correction immédiate
                    if valeur:
                        ret = self.ReqMAJ(dLigne,"matPieces",[(champ,valeur),],"pieIDnumPiece",dict["pieIDnumPiece"])
                        if ret == "ok":
                            corr = True
                            dict[champ] = valeur

                    if IDfamille not in self.dlAnomalies:
                        self.dlAnomalies[IDfamille] = []
                    lstAnomalies = self.dlAnomalies[IDfamille]
                    lstAnomalies.append({"type":"mpFamPay","table":"matPieces","ID":ID,"champ":champ,
                                         "valeur":valeur,"mess":mess,"corr":corr,
                                         "IDfamille":IDfamille,"IDinscription":IDinscription})
            return "ok"

        # autres tables: test et correction de similitude IDcompte_payeur et IDfamille
        def testFamillePayeur(dddtable):
            for IDfamille, ddtable in dddtable.items():
                if IDfamille == "nomTable": continue
                for ID, dict in ddtable["dictDon"].items():
                    if dict["IDcompte_payeur"] == dict["IDfamille"]:
                        continue
                    corr = False
                    champ = None
                    valeur = None
                    IDfamille = dict["IDfamille"]
                    IDinscription = None
                    if "IDinscription" in dict:
                        IDinscription = dict["IDinscription"]
                    if (not dict["IDcompte_payeur"]) and dict["IDfamille"]:
                        mess = "Dans la table %s, famille %d, "%(dddtable["nomTable"],dict["IDfamille"])
                        mess += "l'IDcompte_payeur avait disparu\n"
                        champ = "IDcompte_payeur"
                        valeur = dict["IDfamille"]
                    elif (not dict["IDfamille"]) and dict["IDcompte_payeur"]:
                        mess = "prFamPay: Dans la table %s, famille %d, "%(dddtable["nomTable"],dict["IDcompte_payeur"])
                        mess += "l'IDfamille avait disparu\n"
                        champ = "IDfamille"
                        valeur = dict["IDcompte_payeur"]
                    else:
                        mess = "Dans la table %s, la famille %d-%d,\n"%(dddtable["nomTable"],dict["pieIDcompte_payeur"],
                                                                         dict["pieIDfamille"])
                        mess += "prFamPay: l'IDfamille et l'IDcompte_Payeur différent!!\n"
                    # correction immédiate
                    nomCle = "ID"+dddtable["nomTable"][:-1]
                    if valeur:
                        ret = self.ReqMAJ(dLigne,dddtable["nomTable"],[(champ,valeur),],nomCle,dict[nomCle])
                        if ret == "ok":
                            corr = True
                            dict[champ] = valeur
                    if IDfamille not in self.dlAnomalies:
                        self.dlAnomalies[IDfamille] = []
                    lstAnomalies = self.dlAnomalies[IDfamille]
                    lstAnomalies.append({"type":"prFamPay","table":dddtable["nomTable"],
                                         "ID":ID,"champ":champ,"mess":mess,"corr":corr,
                                         "IDfamille":IDfamille,"IDinscription":IDinscription})

            return "ok"

        # à partir des pièces vérif présence des pointeurs
        def pointeursSelonNaturePiece():

            def ajoutAnomalie(tip,mess,nature,champ,valeur):
                if IDfamille not in self.dlAnomalies:
                    self.dlAnomalies[IDfamille] = []
                lstAnomalies = self.dlAnomalies[IDfamille]
                lstAnomalies.append({"type":tip,"table":"matPieces","ID":ID,
                                     "champ":champ,"valeur":valeur,"nature":nature,
                                     "mess":mess,"corr":False,"IDfamille":IDfamille,"IDinscription":IDinscription})
                lstTuplesTblCle.append(("matPieces",ID))

            def messNullInterdit(ID,nature,champ,valeur):
                tip = "ptIsNull"
                mess = "La piece '%d'de nature '%s' pointe '%s' '%s'\n"%(ID,nature,champ,str(valeur))
                mess += "%s=> Un pointeur est nécessaire pour la nature '%s'"%(tip,nature)
                ajoutAnomalie(tip,mess,nature,champ,valeur)

            def messNullAttendu(ID,nature,champ,valeur):
                tip = "ptNoNull"
                mess = "La piece '%d'de nature '%s' pointe '%s' '%s'\n"%(ID,nature,champ,str(valeur))
                mess += "%s=> La nature '%s' ne doit pas pointer d'%s"%(tip,nature,champ)
                ajoutAnomalie(tip,mess,nature,champ,valeur)
                nomCible = None
                if champ  == "pieIDprestation": nomCible = "prestations"
                elif champ == "pieIDinscription": nomCible = "inscriptions"
                elif champ in ("pieNoFacture","pieNoAvoir"): nomCible = "factures"
                if nomCible and valeur:
                    lstTuplesTblCle.append((nomCible,valeur))

            def testPointeur(ID,dictPiece,champ,lstNatures):
                # Test de champs attendus sinon interdits
                nature = dictPiece["pieNature"]
                valeur = dictPiece[champ]
                if not lstNatures:
                    if not valeur or valeur == 0:
                        messNullInterdit(ID,nature,champ,valeur)
                elif nature in lstNatures:
                    if not valeur or valeur == 0:
                        messNullInterdit(ID,nature,champ,valeur)
                else:
                    # exception avoirs peuvent avoir ou pas un no facture
                    if nature == "AVO":
                        return
                    if valeur and valeur > 0:
                        messNullAttendu(ID,nature,champ,valeur)

            # balayage des pièces
            for IDfamille, ddPieces in self.dictPieces.items():
                if IDfamille == "nomTable": continue
                for ID, dictPiece in ddPieces["dictDon"].items():
                    if ("matPieces",ID) in lstTuplesTblCle:
                        # pb déjà rencontré et signalé
                        continue
                    IDfamille = dictPiece["pieIDfamille"]
                    IDinscription = dictPiece["IDinscription"]
                    # Test de champs attendus sinon interdits
                    testPointeur(ID,dictPiece,"pieIDprestation",["COM","FAC","AVO"])
                    testPointeur(ID,dictPiece,"pieNoFacture",["FAC","AVO"])
                    testPointeur(ID,dictPiece,"pieNoAvoir",["AVO",])
                    testPointeur(ID,dictPiece,"pieIDinscription",None)
            return "ok"
            # fin pointeursSelonNaturePiece

        # tables pricipales vérification des correspondance
        def pointeursPrincipaux(dddTblOrig,cleOrig,champOrig,dddTblCible,champCible,flou=False):
            nomOrig = dddTblOrig["nomTable"]
            nomCible = dddTblCible["nomTable"]

            def ajoutAnomalie(ssType,IDcible,attendu,mess,):
                if not (IDfamille in self.dlAnomalies):
                    self.dlAnomalies[IDfamille] = []
                lstAnomalies = self.dlAnomalies[IDfamille]
                lstAnomalies.append({"type":"ptnPrinc","table": nomOrig,"cleOrig":cleOrig, "champ": champOrig, "ID":ID,
                                     "tblCible":nomCible, "champCible":champCible,
                                     "ssType":ssType,"valeur":attendu,"mess":mess,"corr":False,
                                     "IDfamille":IDfamille,"IDinscription":IDinscription})
                lstTuplesTblCle.append((nomOrig,ID))
                lstTuplesTblCle.append((nomCible,IDcible))

            def messNonAttendu(ID,IDcible,attendu,trouve):
                # valeur trouvée dans une autre ligne
                mess1 = "La '%s' '%d' pointe l'%s "%(str(nomOrig)[:-1],ID,champCible,)
                mess2 = "de la %s %s.\n"%(nomCible[:-1],IDcible)
                mess3 = "Attendu '%s', Trouvé: '%s'"%(str(attendu),str(trouve))
                return mess1 + mess2 + "ptnPrinc=>" + mess3
            def messNoCle(ID,IDcible):
                mess1 = "La '%s' '%d' pointe l'%s "%(nomOrig[:-1],ID,champCible)
                mess2 = " %s dans les '%s'.\n"%(str(IDcible),nomCible)
                mess3 = "Clé non présente"
                return mess1 + mess2 + "ptnPrinc=> " + mess3
            def messTrouveAilleurs(ID,IDtrouve):
                mess1 = "La '%s' '%d' pointe l'%s "%(str(nomOrig)[:-1],ID,champCible,)
                mess2 = "dans les '%s'.\n"%(nomCible)
                mess3 = "La valeur attendue est présente ailleurs avec clé %d"%IDtrouve
                return mess1 + mess2 + "ptnPrinc=> " + mess3
            def messNoTbl(ID,IDcible):
                mess1 = "La '%s' '%d' attend une '%s' %s\n"%(nomOrig[:-1],ID,nomCible[:-1],str(IDcible))
                mess3 = "La table %s est vide"%nomCible
                return mess1 + "tblVide => " + mess3
            def rechercheFloue(tblCible,attendu):
                # on recherche dans toutes les lignes de la cible, pour trouver la valeur attendue
                trouve = False
                for IDfamille,tblCible in dddTblCible.items():
                    if IDfamille == "nomTable": continue
                    for cle, dictc in tblCible["dictDon"].items():
                        if dictc[champCible] == attendu:
                            # vérification de l'identité de la famille
                            if tblOrig == "matPieces":
                                IDfamOrig = "pieIDfamille"
                            else: IDfamOrig = "IDfamille"
                            if tblCible == "matPieces":
                                IDfamCible = "pieIDfamille"
                            else: IDfamCible = "IDfamille"
                            if dict[IDfamOrig] != dictc[IDfamCible]:
                                continue
                            # trouvé
                            trouve = cle
                            break
                return trouve
            def rechercheElargie(tblCible,IDcible):
                mess = "GetionCoherence.rechercheElargie table %s" % tblCible
                dLigne= DATA_Tables.GetDictRecord(self.DB,tblCible,IDcible,mess)
                if tblCible == 'matPieces':
                    dLigne = self.diagDonnees.GetOneMatPieces(IDcible)
                return dLigne

            # -------------------------- Cohérence des pointeurs principaux --------------------------------------------
            for IDfamille, ddTblOrig in dddTblOrig.items():
                # pour chaque famille
                if IDfamille == "nomTable": continue
                if IDfamille in dddTblCible:
                    tblCible = dddTblCible[IDfamille]
                else:
                    tblCible = None

                # pour chaque ligne dans l'origine
                for ID, dict in ddTblOrig["dictDon"].items():
                    # définit la clé cible
                    if cleOrig:
                        IDcible = dict[cleOrig]
                    else: IDcible = None

                    # éluder les pièces familles pour cible inscription
                    if nomOrig == "matPieces" and cleOrig == "pieIDinscription" and  dict["pieIDindividu"] == 0:
                            continue
                    # presence de clé dans la cible
                    if tblCible and IDcible and IDcible in tblCible["dictDon"]:
                        dictCible = tblCible["dictDon"][IDcible]
                    elif IDcible and nomCible != 'numeros':
                        dictCible = rechercheElargie(nomCible,IDcible)
                    elif IDcible and nomCible == 'numeros':
                        dictCible = None
                        where = "factures.numero = %d"%IDcible
                        temp = DATA_Tables.GetDdRecords(self.DB,"factures",where,mess= "recherche numero facture ")
                        for key in temp.keys():
                            # prend la première clé
                            dictCible = temp[key]
                            break
                    else:
                        dictCible = None

                    if not "IDinscription" in dict:
                        IDinscription = None
                    else:
                        IDinscription = dict["IDinscription"]
                    # détermine l'attendu
                    attendu = "encore indefini"
                    if  not champOrig in dict:
                        # cas particuliers géré sans tentative d'accès direct
                        if champOrig  in ("consos"):
                            pass
                        else:
                            wx.MessageBox("Le champ origine: '%s' pas dans %s"%(champOrig,nomOrig),"Arret program")
                            raise Exception(str(("Cf Orig paramsPtnPrinc:",nomOrig,cleOrig,
                                                 champOrig,nomCible,champCible)))
                    # cas général, définit l'attendu de la pièce origine
                    else:
                        attendu = dict[champOrig]
                        if not attendu or attendu == 0:
                            continue

                    # Shunt: évite d'allonger la liste pour un même enregistrement avec plusieurs erreurs
                    if (nomOrig,ID) in lstTuplesTblCle:
                        continue

                    # ----------------------------- Exceptions de traitement -------------------------------------------
                    piece = (nomOrig == "matPieces") and ("pieIDindividu" in dict)
                    pieNivFamille = (piece and dict["pieIDindividu"] == 0)
                    # exception pour l'IDinscription d'une pièce famille qui est l'année et non l'inscription
                    if pieNivFamille and cleOrig == "pieIDinscription":
                        continue
                    if pieNivFamille and (champCible in ("IDactivite","IDcategorie_tarif")):
                        continue
                    # exception pour les prestations absentes des devis et reservations
                    if "pieNature" in dict: # Il s'agit de pièces pour la cible
                        if nomCible == "prestations" and dict["pieNature"] in ("DEV","RES"):
                            continue
                    # exception pour les consos dont l'IDprestation n'est pas dans la pièce désignée par IDcontrat
                    if nomOrig == "prestations":
                        if champCible == "pieIDprestation":
                            # prestation de type conso sans un numéro de pièce cas anormal
                            if "conso" in dict["categorie"] and not dict["IDcontrat"]:
                                attendu = "No contrat dans une conso*"
                                trouve = dict["IDcontrat"]
                                ajoutAnomalie("ToDel", IDcible, attendu,
                                              messNonAttendu(ID, IDcible, attendu,
                                                             trouve))
                                continue
                            # exception pour les prestations résiduelle de devis et reservations
                            if dictCible["pieNature"]  in ("DEV", "RES"):
                                attendu = "FAC ou AVO"
                                trouve = dictCible["pieNature"]
                                ajoutAnomalie("ToDel", IDcible, attendu,
                                              messNonAttendu(ID, IDcible,attendu,trouve))
                                continue
                            if dict["categorie"] == "consoavoir":
                                continue
                        elif champCible == "IDfacture":
                            if round(dict["montant"],2) == 0.0:
                                continue
                    # exception pour les consos ciblées dans inscription et absentes des devis et avoirs
                    if champCible == "nbreConsos":
                        if dictCible:
                            nbTrouve = dictCible[champCible]
                            # au moins une pièce de cette inscription est un avoir
                            if "AVO" in dictCible["natures"]:
                                if nbTrouve == 0:
                                    continue
                                else:
                                    attendu = "=0"
                                    ajoutAnomalie("NoAtt",IDcible,attendu,messNonAttendu(ID,IDcible,attendu,nbTrouve))
                            # une pièce devis ne génère pas de consos
                            elif not "DEV" in dictCible["natures"]:
                                if nbTrouve >0:
                                    continue
                                else:
                                    attendu = ">0"
                                    ajoutAnomalie("NoAtt",IDcible,attendu,messNonAttendu(ID,IDcible,attendu,nbTrouve))
                            elif "DEV" == dictCible["natures"]:
                                if nbTrouve == 0:
                                    continue
                                else:
                                    attendu = "=0"
                                    ajoutAnomalie("NoAtt",IDcible,attendu,messNonAttendu(ID,IDcible,attendu,nbTrouve))
                            else:
                                # devis et (facture ou commande)
                                attendu = "??"
                                ajoutAnomalie("NoAtt",IDcible,attendu,
                                              "Un devis est établi avec présence de consommations!!!")
                        else:
                            nbTrouve = 0
                    # exception pour les consos ciblées dans consommations et absentes des devis et avoirs
                    if nomCible == "consommations" and nomOrig == "inscriptions":
                        if dictCible:
                            valTrouvee = dictCible[champCible]
                        else: valTrouvee = 0
                        # au moins une pièce de cette inscription est un avoir
                        if "AVO" in dict["natures"]:
                            if valTrouvee == 0:
                                continue
                            else:
                                attendu = "=0"
                                ajoutAnomalie("NoAtt",IDcible,attendu,messNonAttendu(ID,IDcible,attendu,valTrouvee))
                        # une pièce devis ne génère pas de consos
                        elif not "DEV" in dict["natures"]:
                            if valTrouvee >0:
                                continue
                            else:
                                attendu = ">0"
                                ajoutAnomalie("NoAtt",IDcible,attendu,messNonAttendu(ID,IDcible,attendu,valTrouvee))
                        continue
                    # exception seule la dernière pièce peut corriger les inscriptions
                    if nomCible == "inscriptions" and nomOrig == "matPieces":
                        IDinscription = dict["pieIDinscription"]
                        if IDinscription in self.dictPiecesMax:
                            IDmax = self.dictPiecesMax[dict["pieIDinscription"]]
                            if ID != IDmax: continue
                    # exception pour recherche de factures.numero dans pièces
                    if nomCible == "matPieces" and champCible.startswith("pieNo"):
                        ok = False
                        if tblCible and "dictDon" in tblCible:
                            for ix,piece in tblCible["dictDon"].items():
                                if attendu == piece["pieNoFacture"] or attendu == piece["pieNoAvoir"]:
                                    ok = True
                                    break
                        if not ok:
                            mess = f"NoFacture ou Avoir {attendu} non trouvé dans {nomCible}"
                            mess += f"pourtant présent dans {nomOrig}"
                            ajoutAnomalie("NoFact", None, attendu,mess)
                        continue

                    # ---- Fin des exceptions - analyse des accès -----------------------------------------------------
                    if not dictCible:
                        if not tblCible:
                            ajoutAnomalie("NoTbl",IDcible,attendu,messNoTbl(ID,IDcible))
                            continue
                        elif not IDcible:
                            ajoutAnomalie("CleNone",IDcible,attendu,messNoCle(ID,IDcible))
                            continue
                    if not dictCible and not flou:
                        ajoutAnomalie("NoCle",IDcible,attendu,messNoCle(ID,IDcible))
                        continue
                    # ======== clé cible présente on teste l'accès direct ==============================================
                    if dictCible and not flou and champCible in dictCible:
                        trouve = dictCible[champCible]
                        # cas de vérif de nature dans inscriptions
                        if champCible == "natures":
                            if attendu in trouve:
                                continue
                        # cas montants float
                        elif isinstance(attendu,float):
                            signe = 1
                            if cleOrig == "IDcontrat" and dict["categorie"] == "consoavoir":
                                signe = -1
                            if nomCible == "prestations" and champCible == "montant" \
                                    and dictCible["categorie"] == "consoavoir":
                                signe = -1
                            try:
                                if round(trouve,2) == round(attendu,2) * signe:
                                    continue
                            except:
                                pass
                        # cas général
                        else:
                            if trouve == attendu:
                                continue
                        ajoutAnomalie("NoAtt",IDcible,attendu,messNonAttendu(ID,IDcible,attendu,trouve))
                        continue

                    # ========  la valeur attendue n'a pas été trouvée cas de recherche floue ==========================
                    IDtrouve = None
                    if nomCible in ("matPiece","prestations","factures"):
                        IDtrouve = rechercheFloue(tblCible,attendu)
                    if IDtrouve:
                        # normal pour une recherche floue ou clé cible non fournie
                        if (not flou) and cleOrig:
                            ajoutAnomalie("TrAil",IDcible,attendu,messTrouveAilleurs(ID,IDtrouve))
                        continue
                    else:
                        if flou:
                            ajoutAnomalie("NoFlou",IDcible,attendu,messNoCle(ID,dict[cleOrig]))
                        if not cleOrig:
                            ajoutAnomalie("zzCleNone",IDcible,attendu,messNoCle(ID,None))
                        else:
                            ajoutAnomalie("zzNoCle",IDcible,attendu,messNoCle(ID,dict[cleOrig]))
                        continue
            return "ok"
            #fin pointeursPrincipaux

        #---------------------------------  Traitement Vérification cohérences -----------------------------------------

        if not self.famille:
            attente = wx.BusyInfo("Vérifie familles-payeurs...")

        # test famille- compte_payeur sur Pieces
        ret = piecesTestFamillePayeur()
        if  not ret == "ok": return ret

        # test famille- compte_payeur sur autres tables
        for table in (self.dictPrestations,self.dictInscriptions):
            ret = testFamillePayeur(table)
            if not ret  == "ok":
                if not self.famille: del attente
                return ret

        if not self.famille:
            attente = wx.BusyInfo("Vérifie selon nature pièces...")

        # test présence des pointeurs entre tables selon nature des pièces
        ret = pointeursSelonNaturePiece()
        if not ret == "ok":
            if not self.famille: del attente
            return ret

        if not self.famille:
            attente = wx.BusyInfo("Vérification des pointeurs entre tables...")

        # test des pointeurs autres que clé des tables
        paramsPtnPrinc = GET_PARAMS_POINTEURS(self.dictPieces,self.dictPrestations,self.dictConsommations,
                                              self.dictInscriptions,self.dictFactures,self.dictNumeros)
        for args in paramsPtnPrinc:
            tblOrig,cleOrig,champOrig,tblCible,champCible = args[:5]
            mess = "Vérifie pointeurs entre tables...\n\n"
            mess += "%s.%s => %s.%s"%(tblOrig["nomTable"],cleOrig,tblCible["nomTable"],champCible)
            if not self.famille:
                attente = wx.BusyInfo(mess)
            if len(args) > 5:
                flou = args[-1]
            else: flou = False
            retw = pointeursPrincipaux(tblOrig,cleOrig,champOrig,tblCible,champCible,flou=flou)
            if retw  != "ok":
                if not self.famille:
                    del attente
                return retw

        if not self.famille: del attente
        return "ok"

    # génère les self.dict tables pricipales préchargées
    def GetDonnees(self,famille,**kw):
        lstTables = self.diagDonnees.GetTables()
        if not isinstance(lstTables,list):
            ret = self.diagDonnees.echecGet
        else:
            (self.dictPieces,self.dictPrestations,self.dictFactures,
             self.dictNumeros,self.dictConsommations,self.dictInscriptions,self.dictPiecesMax) = lstTables
            ret = "ok"
        return ret# fin GetDonnees

    # confirmation si demande de l'ensemble (risque de lenteur)
    def TestAllFamilles(self,IDfamille,inCpta):
        if (not IDfamille) and inCpta == True:
            mess = "Confirmez-vous le diagnostic de cohérence sur toutes les familles?"
            ret = wx.MessageBox(mess,"Confirmation traitement complet",wx.YES_NO)
            if not ret == wx.YES:
                return False
            else: return True
        return True

    # retoune la seule propriété self.coherence
    def Coherence(self):
        return self.coherence

class DLG_Diagnostic():
    def __init__(self,OneFamille=None):
        self.coherence = None
        import Dlg.DLG_Choix as DLG_Choix
        mess1 = "Seulement les écritures non transférées en compta seront testées "
        mess1 += "puis une tentative de correction sera lancée"
        if not OneFamille:
            mess2 = "Ce peut être pour plusieurs minutes sans interruption possible autre que la suppression de tâche, "
        else:
            mess2 = "Toutes les écritures de la famille %d seront testées"%OneFamille
        mess2 += "avec correction impossible sur les écritures bloquées"
        listeBoutons = [
            ("Seulement non transféré en compta", mess1),
            ("Y compris le transféré en compta", mess2),
        ]
        titre = "Quel type de vérification de cohérence voulez-vous lancer?"
        dlg = DLG_Choix.Dialog(None,titre=titre, listeBoutons=listeBoutons)
        reponse = dlg.ShowModal()
        dlg.Destroy()
        self.DB = GestionDB.DB()
        self.fGest = GestionInscription.Forfaits(self,self.DB)
        if reponse == 0:
            diag = Diagnostic(self,OneFamille,inCpta=False,noInCpta=True,mute=False)
        if reponse == 1:
            diag = Diagnostic(self,OneFamille,inCpta=True,noInCpta=True,mute=False)
        if reponse in (0,1):
            self.coherence = diag.Coherence()
            del diag
        del self.fGest
        self.DB.Close()

if __name__ == '__main__':
    app = wx.App(0)
    f = DLG_Diagnostic(OneFamille=3993)
    print((f.coherence))
