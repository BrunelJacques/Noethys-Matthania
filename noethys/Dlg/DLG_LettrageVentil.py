#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------
# Application :    Matthania Juin 2020
# Auteur:          Jacques BRUNEL
# Licence:         Licence GNU GPL
#-----------------------------------------------------------

import wx
import GestionDB
from Ctrl import CTRL_ChoixListe

def GetPrestations(IDfamille=None):
    ddDebits = {}
    DB = GestionDB.DB()

    req = """SELECT prestations.label,prestations.IDprestation, prestations.date, prestations.categorie,  
            matPieces.pieIDnumPiece, matPieces.pieNature, prestations.montant, matPieces.pieNoFacture,matPieces.pieNoAvoir
            FROM prestations 
            LEFT JOIN matPieces ON prestations.IDcontrat = matPieces.pieIDnumPiece
            WHERE (prestations.IDcompte_payeur = %d) 
                    AND NOT prestations.montant = 0 ;
            """%IDfamille
    DB.ExecuterReq(req,MsgBox="ExecuterReq")
    prestations = DB.ResultatReq()
    DB.Close()
    for label,IDprestation,date,categorie,IDpiece,pieNature,montant,noFacture,noAvoir in prestations:
        nature = categorie
        if categorie[:5] == 'conso':
            nature = pieNature
        ddDebits[IDprestation] = {  'designations':[label,date,nature],
                                    'montant':montant,
                                    'IDpiece':IDpiece,
                                    'noFacture':noFacture,
                                    'noAvoir':noAvoir}
    return ddDebits

def GetReglements(IDfamille=None):
    ddCredits = {}
    DB = GestionDB.DB()
    req = """SELECT modes_reglements.label,reglements.IDreglement, reglements.date,  reglements.numero_piece, 
                    payeurs.nom, reglements.observations,reglements.montant
                    FROM (reglements 
                    LEFT JOIN modes_reglements ON reglements.IDmode = modes_reglements.IDmode) 
                    LEFT JOIN payeurs ON reglements.IDpayeur = payeurs.IDpayeur
            WHERE (reglements.IDcompte_payeur = %d)
                    AND NOT reglements.montant = 0;
            """%IDfamille
    DB.ExecuterReq(req,MsgBox="DLG_LettrageVentil.GetReglements")
    reglements = DB.ResultatReq()
    DB.Close()
    for mode,IDreglement,date, noPiece,payeur,observations,montant in reglements:
        label = "Pb règlement no %d" %IDreglement
        try:
            label= mode[:2]+": "+noPiece+" " + observations + " "+ payeur
        except: pass
        ddCredits[IDreglement] = {  'designations':[label, date, mode,],
                                    'montant': montant}
    return ddCredits

def GetVentilations(IDfamille=None):
    ltVentilations = []
    DB = GestionDB.DB()
    req = """   SELECT IDventilation, IDprestation, IDreglement, montant
                FROM ventilation 
                WHERE (ventilation.IDcompte_payeur = %d);
                """%IDfamille
    DB.ExecuterReq(req,MsgBox="DLG_LettrageVentil.GetVentilations")
    ventilations = DB.ResultatReq()
    DB.Close()
    for IDventilation, IDprestation, IDreglement, montant in ventilations:
        ltVentilations.append((IDprestation,IDreglement,montant))
    return ltVentilations

class Lettrage(object):
    def __init__(self,IDfamille=None):
        lstChamps = ["Libellé","date","Nature"]
        dictFooter = {  "dlibelle": {"mode" : "nombre","singulier":"ligne afichée","pluriel":"lignes afichées"},
                        "debit" :   {"mode" : "total"},
                        "mtt" :     {"mode" : "total"},
                        "credit" :  {"mode" : "total"},}
        dicPrestations = GetPrestations(IDfamille)
        dicReglements = GetReglements(IDfamille)
        dlg = CTRL_ChoixListe.DLGventilations(self,ddDebits=dicPrestations,ddCredits=dicReglements,
                        ltVentilations=GetVentilations(IDfamille),lChampsDesign=lstChamps,
                        dictFooter= dictFooter,
                        size=(1100, 600),titre="Ventilation des règlements sur les pièces",
                        pos=wx.Point(100,50)
                        )
        ret = dlg.ShowModal()
        if ret == wx.ID_OK:
            DB = GestionDB.DB()
            self.SupprVentilations(DB,dlg.GetVentilSuppr(),IDfamille)
            self.CreeVentilations(DB,dlg.GetVentilNews(),IDfamille)
            DB.Close()
        dlg.Destroy()

    def SupprVentilations(self,DB,ltVentil,IDfamille):
        lprest = [ x for (x,y,z) in ltVentil]
        lregl = [ y for (x,y,z) in ltVentil]
        req = """   DELETE FROM ventilation 
                    WHERE   IDcompte_payeur = %d
                            AND IDprestation in (%s)
                            AND IDreglement in (%s);
                    """ %(IDfamille,str(lprest)[1:-1],str(lregl)[1:-1])
        DB.ExecuterReq(req, MsgBox="DLG_LettrageVentil.SupprVentilations")

    def CreeVentilations(self,DB,ltVentil,IDfamille):
        for IDprestation,IDreglement, montant in ltVentil:
            donnees = [("IDcompte_payeur",IDfamille),
                       ("IDreglement",IDreglement),
                       ("IDprestation",IDprestation),
                       ("montant",montant)]
            ret = DB.ReqInsert('ventilation',donnees,retourID=False,MsgBox="DLG_LettrageVentil.CreeVentilations")

    # -----------------------------------------------------------------------------------------------------

if __name__ == "__main__":
    app = wx.App(0)
    Lettrage(IDfamille = 1684)
    app.MainLoop()
