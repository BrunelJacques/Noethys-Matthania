#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys branche Matthania
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS, JB, Jacques Brunel
# Copyright:       (c) 2010-11 Ivan LUCAS, JB
# Licence:         Licence GNU GPL
# Derive de OL_Prestations.py
#------------------------------------------------------------------------

import wx
import Chemins
import copy
import datetime
import GestionDB

from Utils.UTILS_Traduction import _
import FonctionsPerso as fp

from Dlg import DLG_Apercu_facture
from Gest import GestionInscription
from Data import DATA_Tables
import wx.lib.agw.pybusyinfo as PBI
from Utils import UTILS_Facturation
from Utils import UTILS_Config
from Utils.UTILS_Decimal import FloatToDecimal as FloatToDecimal
from Ctrl.CTRL_ObjectListView import ObjectListView, ColumnDefn, Filter, CTRL_Outils, PanelAvecFooter # CTRL_Outils appelé by parent

SYMBOLE = UTILS_Config.GetParametre("monnaie_symbole", "€")

def DateEngFr(textDate):
    if textDate == None: return ""
    textDate = str(textDate)
    text = str(textDate[8:10]) + "/" + str(textDate[5:7]) + "/" + str(textDate[:4])
    return text

def Decod(valeur):
    return GestionDB.Decod(valeur)

def DateComplete(dateDD):
    """ Transforme une date DD en date complète : Ex : lundi 15 janvier 2008 """
    listeJours = (_("Lundi"), _("Mardi"), _("Mercredi"), _("Jeudi"), _("Vendredi"), _("Samedi"), _("Dimanche"))
    listeMois = (_("janvier"), _("février"), _("mars"), _("avril"), _("mai"), _("juin"), _("juillet"), _("août"), _("septembre"), _("octobre"), _("novembre"), _("décembre"))
    dateComplete = listeJours[dateDD.weekday()] + " " + str(dateDD.day) + " " + listeMois[dateDD.month-1] + " " + str(dateDD.year)
    return dateComplete

def DateEngEnDateDD(dateEng):
    if dateEng and not isinstance(dateEng,str): dateEng = str(dateEng)
    return datetime.date(int(dateEng[:4]), int(dateEng[5:7]), int(dateEng[8:10]))

def ContractNom(individu,longueur):
    if len(individu) > longueur :
        decoupe = individu.split(' ')
        nb = int(longueur/len(decoupe))+1
        individu = ""
        for item in decoupe:
            if len(item) > nb:
                sep = "."
            else: sep = " "
            try : individu = individu + item[:nb] + sep
            except: individu = str(individu) + str(item[:nb]) + str(sep)
    return individu

def OlvToDict(self,listeChamps,track):
        # Transforme une ligne Olv (Track) en dictionnaire
        # pour tous les champs on peut aussi utiliser diretement : self.GetSelectedObject().__dict__
        dictDonnees = {}
        for champ in listeChamps:
            if hasattr(track, f"{champ}"):
                dictDonnees["%s" %champ] = track.__dict__["%s" % champ]
        return dictDonnees

# ---------------------------------------- LISTVIEW DATES -----------------------------------------------------------------------

class Track(object):
    def __init__(self, track):
        try:
            if isinstance(track["commentaire"],memoryview):
                track["commentaire"] = ""
        except:
            pass
        self.__dict__ = copy.deepcopy(track)

class ListView(ObjectListView):
    def __init__(self, parent,*args, **kwds):
        self.IDpayeur =  kwds.pop("IDpayeur", None)
        self.listeActivites = kwds.pop("activites", None)
        self.factures = kwds.pop("factures", None)
        self.parent = kwds.pop("parent", None)
        self.dictOptions = {}
        ObjectListView.__init__(self, parent, *args, **kwds)

        if hasattr(parent,'DB'):
            self.DB = parent.DB
        elif hasattr(self.GrandParent,'DB'):
            self.DB = self.GrandParent.DB
        else:
            self.DB = GestionDB.DB()

        self.pointe = None
        if self.IDpayeur == None:
            self.multi = True
        else:
            self.multi = False
        self.selectionID = None
        self.selectionTrack = None
        self.listeFactures = []
        self.listeIDprestation = []
        self.total = 0.0
        # Binds perso
        self.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)
        #self.SetShowGroups(False)
        self.InitObjectListView()
        self.CocheTout()

    def InitObjectListView(self):
        self.donnees = self.GetListePieces(IDpayeur=self.IDpayeur)
        # ImageList
        self.imgVert = self.AddNamedImages("vert", wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Ventilation_vert.png"), wx.BITMAP_TYPE_PNG))
        self.imgRouge = self.AddNamedImages("rouge", wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Ventilation_rouge.png"), wx.BITMAP_TYPE_PNG))
        self.imgOrange = self.AddNamedImages("orange", wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Ventilation_orange.png"), wx.BITMAP_TYPE_PNG))

        def GetImageVentilation(track):
            color = self.imgRouge
            try:
                if track.montant == track.mttRegle :
                    color = self.imgVert
                if track.mttRegle == FloatToDecimal(0.0) or track.mttRegle == None :
                    color = self.imgRouge
                if track.mttRegle < track.montant :
                    color = self.imgOrange
            except: pass
            return color

        def FormateDate(dateDD):
            return DateEngFr(str(dateDD))

        def FormateMontant(montant):
            if montant == None or montant == "" : return ""
            return "%.2f %s" % (montant, SYMBOLE)

        # Couleur en alternance des lignes
        self.oddRowsBackColor = wx.Colour(255, 255, 255) #"#EEF4FB" # Bleu
        self.evenRowsBackColor = "#F0FBED" # Vert

        # Paramètres ListView
        self.useExpansionColumn = True
        if self.multi :
            listeColonnes = ["IDnumPiece", "payeur", "activite", "piece", "label", "montant", "mttRegle", "duGlobal", "dateCreation", "utilisateurModif"]
        else:
            listeColonnes = ["IDnumPiece", "dateCreation", "payeur", "famille", "activite", "label", "montant", "mttRegle", "piece", "utilisateurModif"]
        if self.factures :
            libPiece = "N° Facture"
            valPiece = "numeros"
            datePiece = "dateFacturation"
        else:
            libPiece = "Piece"
            valPiece = "nature"
            datePiece = "dateCreation"

        dictColonnes = {
            "IDnumPiece" : ColumnDefn(_(""), "left", 0, "IDnumPiece", typeDonnee="entier"),
            "dateCreation" : ColumnDefn(_("Date"), "left", 90, datePiece, typeDonnee="date", stringConverter=FormateDate),
            "payeur" : ColumnDefn(_("Payeur"), "left", 100, "payeur", typeDonnee="texte"),
            "famille" : ColumnDefn(_("Famille "), "left", 100, "famille", typeDonnee="texte"),
            "activite" : ColumnDefn(_("Activité"), "left", 60, "activite", typeDonnee="texte"),
            "label" : ColumnDefn(_("Ref. Inscription"), "left", 200, "label", typeDonnee="texte",isSpaceFilling = True),
            "montant" : ColumnDefn(_("Montant"), "right", 90, "montant", typeDonnee="montant", stringConverter=FormateMontant),
            "mttRegle" : ColumnDefn(_("Réglé"), "right", 90, "mttRegle", typeDonnee="montant", stringConverter=FormateMontant, imageGetter=GetImageVentilation),
            "duGlobal" : ColumnDefn(_("Dû Global"), "right", 90, "duGlobal", typeDonnee="montant", stringConverter=FormateMontant, imageGetter=GetImageVentilation),
            "piece" : ColumnDefn(_(libPiece), "left", 60, valPiece, typeDonnee="texte"),
            "utilisateurModif" : ColumnDefn(_("User"), "left", 50, "utilisateurModif", typeDonnee="texte"),}

        self.SetColumns([dictColonnes[code] for code in listeColonnes])
        self.SetSortColumn(self.columns[2])
        self.CreateCheckStateColumn()
        #self.SetShowItemCounts(False)
        if self.factures:
            self.SetEmptyListMsg(_("Aucune facture"))
        else : self.SetEmptyListMsg(_("Aucune piece non facturée"))
        self.SetEmptyListMsgFont(wx.FFont(11, wx.DEFAULT, faceName="Tekton"))
        self.SetObjects(self.donnees)
        #fin initObjectListView

    def GetListePieces(self, IDpayeur=1):
        # alimentation des données pour l'initialisation du listCtrl
        if self.multi :
            dlgAttente = PBI.PyBusyInfo(_("Appel des données en cours..."), parent=None, title=_("Veuillez patienter..."), icon=wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Logo.png"), wx.BITMAP_TYPE_ANY))
            wx.Yield()
            activites = fp.ListeToStr(self.listeActivites)
            conditions = "(matPiecesLignes.ligMontant <> 0) AND (matPieces.pieIDactivite IN ( %s )) AND (matPieces.pieNature NOT IN ('FAC', 'AVO'))" % activites
        else :
            if self.factures:
                conditions = "matPieces.pieIDcompte_payeur = %s AND (matPieces.pieNature IN ('FAC', 'AVO')) " % IDpayeur
            else:
                conditions = "matPieces.pieIDcompte_payeur = %s AND (matPieces.pieNature NOT IN ('FAC', 'AVO'))" % IDpayeur

        # Composition des champs
        dicoDB = DATA_Tables.DB_DATA
        listeChamps = []
        champsReq =""
        for descr in dicoDB["matPieces"]:
            if descr[1] != "blob" :
                nomChamp = descr[0]
                listeChamps.append(nomChamp)
                champsReq += nomChamp + ","

        self.champsPieceReq = copy.deepcopy(champsReq)
        self.listeChampsPiece = copy.deepcopy(listeChamps)
        listeChampsAutres = ["activite","label","montant","mttPrest","mttRegle","duGlobal"]
        champsAutresReq = "activites.abrege AS activite,prestations.label, Sum(matPiecesLignes.ligMontant) AS mttLignes, prestations.montant AS mttPrest"
        champsGroupBy = champsReq
        champsReq += champsAutresReq
        champsGroupBy += "activite,prestations.label, mttPrest"
        self.listeChamps = self.listeChampsPiece + listeChampsAutres

        #récupération des éléments principaux des pièces
        req = """
        SELECT %s
        FROM matPieces
                LEFT JOIN matPiecesLignes ON matPieces.pieIDnumPiece = matPiecesLignes.ligIDnumPiece
                LEFT JOIN activites ON matPieces.pieIDactivite = activites.IDactivite
                LEFT JOIN prestations ON (matPieces.pieIDcompte_payeur = prestations.IDcompte_payeur) AND (matPieces.pieIDprestation = prestations.IDprestation)
        WHERE %s
        GROUP BY %s
        ORDER BY matPieces.pieIDnumPiece;
        """ % (champsReq, conditions, champsGroupBy)
        retour = self.DB.ExecuterReq(req,MsgBox="ExecuterReq")
        if retour != "ok" :
            GestionDB.MessageBox(self,retour)
            return None
        recordset = self.DB.ResultatReq()

        listeRecords = []
        listePieces = []
        listePayeurs = []
        iPayeur = listeChamps.index("pieIDcompte_payeur")
        iNumPiece = listeChamps.index("pieIDnumPiece")
        #constitution de la listePiece première partie
        # et liste payeurs pour compléter en ajout des pièces activité 0 (niveau famille)
        for record in recordset:
            if not record[iPayeur] in listePayeurs:
                listePayeurs.append(record[iPayeur])
            listeRecords.append(record)
            listePieces.append(record[iNumPiece])
        payeurs = fp.ListeToStr(listePayeurs)

        if self.multi:
            #récupération des pièces d'activité 0
            if payeurs == "*":
                conditions = " ( pieIDactivite = 0  AND (matPieces.pieNature NOT IN ('FAC', 'AVO')))"
            else:
                conditions = " ( pieIDactivite = 0 AND pieIDcompte_payeur IN ( %s )  AND (matPieces.pieNature NOT IN ('FAC', 'AVO')))" % payeurs
            req = """
            SELECT %s
            FROM matPieces
                    LEFT JOIN matPiecesLignes ON matPieces.pieIDnumPiece = matPiecesLignes.ligIDnumPiece
                    LEFT JOIN activites ON matPieces.pieIDactivite = activites.IDactivite
                    LEFT JOIN prestations ON (matPieces.pieIDcompte_payeur = prestations.IDcompte_payeur) AND (matPieces.pieIDprestation = prestations.IDprestation)
            WHERE %s
            GROUP BY %s
            ORDER BY matPieces.pieIDnumPiece;
            """ % (champsReq, conditions,champsGroupBy)
            retour = self.DB.ExecuterReq(req,MsgBox="ExecuterReq")
            if retour != "ok" :
                GestionDB.MessageBox(self,retour)
                return None
            recordset = self.DB.ResultatReq()

            for record in recordset:
                listeRecords.append(record)
                listePieces.append(record[iNumPiece])

        #tri sur IDnumPiece première position de Records
        listeRecords.sort()
        listePieces.sort()

        if len(listeRecords)>0:
            pieces = fp.ListeToStr(listePieces)

            #récupération des règlements ventilés
            conditions = " ( pieIDnumPiece IN ( %s ))" % pieces
            req = """
            SELECT matPieces.pieIDnumPiece, Sum(ventilation.montant) AS mttRegle
            FROM matPieces
            LEFT JOIN ventilation ON (matPieces.pieIDcompte_payeur = ventilation.IDcompte_payeur) AND (matPieces.pieIDprestation = ventilation.IDprestation)
            WHERE %s
            GROUP BY matPieces.pieIDnumPiece
            ORDER BY matPieces.pieIDnumPiece;
            """ % (conditions)
            retour = self.DB.ExecuterReq(req,MsgBox="ExecuterReq")
            if retour != "ok" :
                GestionDB.MessageBox(self,retour)
                return None
            listeReglements = self.DB.ResultatReq()

            #récupération montant des prestations
            req = """
            SELECT matPieces.pieIDnumPiece, SUM(prestations.montant)
            FROM matPieces
            LEFT JOIN prestations ON prestations.IDcompte_payeur = matPieces.pieIDcompte_payeur
            WHERE %s
            GROUP BY matPieces.pieIDnumPiece
            ORDER BY matPieces.pieIDnumPiece;
            """ % (conditions)
            retour = self.DB.ExecuterReq(req,MsgBox="ExecuterReq")
            if retour != "ok" :
                GestionDB.MessageBox(self,retour)
                return None
            listeMttPrestations = self.DB.ResultatReq()

            #récupération mtt total règlements
            req = """
            SELECT matPieces.pieIDnumPiece, SUM(reglements.montant)
            FROM matPieces
            LEFT JOIN reglements ON reglements.IDcompte_payeur = matPieces.pieIDcompte_payeur
            WHERE %s
            GROUP BY matPieces.pieIDnumPiece
            ORDER BY matPieces.pieIDnumPiece;
            """ % (conditions)
            retour = self.DB.ExecuterReq(req,MsgBox="ExecuterReq")
            if retour != "ok" :
                GestionDB.MessageBox(self,retour)
                return None
            listeMttReglements = self.DB.ResultatReq()

        #constitution de la listePiece deuxième partie
        # agrégation des données sur IDnumPiece
        listeDonnees = []
        self.dictComptes = {}
        i = 0
        for piece  in listeRecords :
            if listeReglements[i][1] == None:
                regle = 0.00
            else : regle = listeReglements[i][1]
            if listeMttPrestations[i][1] == None:
                mttPrest = 0.00
            else : mttPrest = listeMttPrestations[i][1]
            if listeMttReglements[i][1] == None:
                mttRegl = 0.00
            else : mttRegl = listeMttReglements[i][1]
            donnee = []
            for item in piece:
                donnee.append(item)
            donnee.append(regle)
            donnee.append(mttPrest - mttRegl)
            listeDonnees.append(donnee)
            i+= 1

        self.nbPieces = len(listeDonnees)
        if self.nbPieces == 0 :
            return None

        # composition des tracks
        listeOLV=[]
        self.listeIDprestation=[]
        payeur = Decod(self.DB.GetNomFamille(IDpayeur, first="nom"))
        famille = Decod(self.DB.GetNomFamille(IDpayeur, first="prenom"))

        for record in listeDonnees:
            dictDonnees = GestionInscription.DictTrack(self.listeChamps,record)
            ligne = Track(dictDonnees)
            if ligne.activite == None:
                ligne.activite = ligne.IDinscription
            if ligne.noAvoir != None :
                if ligne.noFacture == None :
                    ligne.numeros = " AV "+str(ligne.noAvoir)
                else:
                    ligne.numeros = str(ligne.noFacture)+","+str(ligne.noAvoir)
            else :
                ligne.numeros = str(ligne.noFacture)
            if ligne.IDindividu == None : ligne.IDindividu = 0
            if ligne.IDactivite == None : ligne.IDactivite = 0
            if ligne.montant == None : ligne.montant = 0
            if ligne.prixTranspAller != None:
                ligne.montant += ligne.prixTranspAller
            if ligne.prixTranspRetour != None:
                ligne.montant += ligne.prixTranspRetour
            #La pièce devenue avoir compte pour zéro
            if ligne.nature=="AVO":
                if ligne.noFacture != None :
                    ligne.montant = 0
                    label = "Annulé: "
                else :
                    #sauf si c'est un avoir sans facture
                    ligne.montant = -ligne.montant
                    label = "Reprise: "
            else: label = ""

            ligne.payeur= payeur
            ligne.famille= famille
            individu = Decod(self.DB.GetNomIndividu(ligne.IDindividu))
            if len(individu)>16:
                individu = ContractNom(individu,16)
            elif individu == None: individu = ""
            activite = self.DB.GetNomActivite(ligne.IDactivite).split('-')[0]
            activite = " - " + activite
            groupe = " - " + (self.DB.GetNomGroupe(ligne.IDgroupe))

            if not (ligne.IDindividu * ligne.IDactivite == 0):
                try :
                    texte = label + individu + activite + groupe
                except :
                    try :
                        texte = label + individu + activite
                    except :
                        try :
                            texte = label + individu
                        except :
                                texte = individu
                ligne.label = texte
            else :
                if label == None : label = ""
                if ligne.label == None : ligne.label = ""
                ligne.label = label + ligne.label
            listeOLV.append(ligne)
            if ligne.IDprestation != None:
                self.listeIDprestation.append(ligne.IDprestation)
        if self.multi:
            del dlgAttente
        return listeOLV

    def MAJ(self, ID=None):
        self.InitObjectListView()
        self.Refresh()

    def OnContextMenu(self, event):
        """Ouverture du menu contextuel """
        if len(self.GetSelectedObjects()) > 0 :
            ID = self.GetSelectedObjects()[0].IDprestation
        
        # Création du menu contextuel
        menuPop = wx.Menu()

        # Item Monter
        if self.IDpayeur != None :
            item = wx.MenuItem(menuPop, 10, _("Monter"))
            bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Fleche_haut.png"), wx.BITMAP_TYPE_PNG)
            item.SetBitmap(bmp)
            menuPop.Append(item)
            self.Bind(wx.EVT_MENU, self.Monter, id=10)

        # Item Descendre
        item = wx.MenuItem(menuPop, 20, _("Descendre"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Fleche_bas.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.Descendre, id=20)
        if len(self.GetSelectedObjects()) == 0 : item.Enable(False)

        # Item Supprimer
        item = wx.MenuItem(menuPop, 30, _("Supprimer"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Supprimer.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.Supprimer, id=30)
        if len(self.GetSelectedObjects()) == 0 : item.Enable(False)
        
        menuPop.AppendSeparator()

        # Item Tout cocher
        item = wx.MenuItem(menuPop, 70, _("Tout cocher"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Cocher.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.CocheTout, id=70)

        # Item Tout décocher
        item = wx.MenuItem(menuPop, 80, _("Tout décocher"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Decocher.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.CocheRien, id=80)

        menuPop.AppendSeparator()

        # Item Imprimer la sélection (ex Apercu avant impression)
        item = wx.MenuItem(menuPop, 40, _("Imprimer la pièce"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Apercu.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.ImprimerPieces, id=40)

        # Item Envoyer la facture par Email
        item = wx.MenuItem(menuPop, 90, _("Envoyer la pièce par Email"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Emails_exp.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.EnvoyerEmail, id=90)

        # Item Imprimer (la liste pas la facture)
        item = wx.MenuItem(menuPop, 50, _("Imprimer la liste"))
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

    def EnvoyerEmail(self, event):
        """ Envoyer la facture par Email """
        listePieces = self.GetSelectedObjects()
        if listePieces:
            self.dictOptions = self.GetOptions(mail=True)  # sera repris par creation pdf
            if not self.dictOptions:
                return
            IDmodel = self.dictOptions["IDmodelMail"]
            # Envoi du mail
            from Utils import UTILS_Envoi_email
            firstPiece = listePieces[0]
            nature = firstPiece.nature
            if nature == "FAC":
                ID = firstPiece.noFacture
            elif nature == "AVO":
                ID = firstPiece.noAvoir
            else: ID = firstPiece.IDnumPiece
            IDfamille = firstPiece.IDfamille
            nomDoc = f"{nature} {ID}"
            UTILS_Envoi_email.EnvoiEmailFamilles(parent=self,
                                                 IDfamille=IDfamille,
                                                 nomDoc= nomDoc,
                                                 CreationPDF=self.CreationPDF,
                                                 categorie="facture",
                                                 IDmodel=IDmodel)

    def CreationPDF(self, nomDoc="", afficherDoc=True,repertoireTemp=True):
        """ Création du PDF pour Email """
        listePieces = self.GetListeIDpieces()
        if listePieces:
            dictOptions = self.dictOptions
            if not dictOptions:
                return
            facturation = UTILS_Facturation.Facturation()
            resultat = facturation.Impression(listePieces=listePieces,
                                              nomDoc=nomDoc,
                                              afficherDoc=afficherDoc,
                                              repertoireTemp=repertoireTemp,
                                              dictOptions=dictOptions)
            if resultat == False :
                return False
            del facturation
            return resultat

    def GetTracksCoches(self):
        return self.GetSelectedObjects()

    def GetListeIDpieces(self):
        listePieces = []
        for obj in self.GetChoicesObjects():
            if not obj.IDnumPiece in listePieces:
                listePieces.append(obj.IDnumPiece)
        return listePieces
        #fin GetListeIDpieces

    def GetOptions(self,mail=True):
        dlg = DLG_Apercu_facture.Dialog(self,
                                        titre="Sélection des paramètres pour factures",
                                        intro="Sélectionnez ici les paramètres d'affichage des factures.",
                                        mail=mail)
        if dlg.ShowModal() == wx.ID_OK:
            dictOptions = dlg.GetParametres()
            dlg.Destroy()
            return dictOptions
        else:
            return False

    def LanceImpression(self,lancement,liste):
        dictOptions = self.GetOptions(mail=False)
        if not dictOptions:
            return
        fFact = UTILS_Facturation.Facturation()
        nomDoc = f"{lancement} {self.IDpayeur}"
        fFact.Impression(listePieces=liste,
                         nomDoc=nomDoc,
                         afficherDoc=True,
                         dictOptions=dictOptions,
                         repertoireTemp=False)
        del fFact
        #fin LanceImpression

    def ImprimerPieces(self, event):
        listePieces = self.GetListeIDpieces()
        prefix = "DEV"
        if self.factures:
            prefix = "FAC"
        if listePieces != None:
            if len(listePieces) > 0 :
                self.LanceImpression(prefix,listePieces)
        #fin ImprimerPieces

    def Imprimer(self, event):
        from Utils import UTILS_Printer
        prt = UTILS_Printer.ObjectListViewPrinter(self, titre=_("Liste des Pièces"), format="A", orientation=wx.PORTRAIT)
        prt.Preview()

    def ExportTexte(self, event):
        from Utils import UTILS_Export
        UTILS_Export.ExportTexte(self, titre=_("Liste des prestations"))
        
    def ExportExcel(self, event):
        from Utils import UTILS_Export
        UTILS_Export.ExportExcel(self, titre=_("Liste des pieces"))

    def Monter(self, event):
        if len(self.GetSelectedObjects()) == 0 :
            dlg = wx.MessageDialog(self, _("Vous n'avez sélectionné aucune ligne !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
        else:
            self.donnees = self.GetObjects()
            for obj in self.donnees:
                if self.GetSelectedObject() == obj:
                    idx = self.donnees.index(obj)
                    obj2 = obj
                    if idx >0:
                        self.donnees.insert(idx-1,self.donnees.pop(idx))
            self.SetObjects(self.donnees)
            self.SelectObject(obj2, deselectOthers=True, ensureVisible=True)
            self.Refresh()
            #fin Monter

    def Descendre(self, event):
        if len(self.GetSelectedObjects()) == 0 :
            dlg = wx.MessageDialog(self, _("Vous n'avez sélectionné aucune ligne !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
        else:
            self.donnees = self.GetObjects()
            for obj in self.donnees:
                if self.GetSelectedObject() == obj:
                    idx = self.donnees.index(obj)
                    obj2 = obj
                    if idx < len(self.donnees):
                        self.donnees.insert(idx+1,self.donnees.pop(idx))
            self.SetObjects(self.donnees)
            self.SelectObject(obj2, deselectOthers=True, ensureVisible=True)
            self.Refresh()
            #fin Descendre

    def Supprimer(self, event):
        objects = self.GetChoicesObjects()
        nature = ""
        label = ""
        for obj in objects:
            dictDonnees =  obj.__dict__
            if (nature == ""):
                nature = dictDonnees["nature"]
                label = dictDonnees["label"]
            if dictDonnees["nature"] in ["AVO","FAC"]:
                if dictDonnees['nature'] != nature :
                    GestionDB.MessageBox(self,"Les pièces facturées sont de natures différentes : %s et %s !\nFaire un choix homogènes par les natures de pièces" %(nature,dictDonnees["nature"]), titre="Traitement impossible")
                    return
        nbSel = len(objects)
        if nbSel == 1:
            txtNbPiece = "la pièce '%s '%s'" %(nature,label)
        else: txtNbPiece = "les %d pièces '%s' cochées " % (nbSel,nature)

        if nature == 'FAC':
            texte = "Oui je veux rétrograder " + txtNbPiece + " en Commande"
        elif nature == 'AVO':
            texte = "Oui je veux rétrograder " + txtNbPiece + " en Facture"
        else:
            texte = "Oui je veux supprimer " + txtNbPiece
        retour = GestionDB.Messages().Choix(listeTuples=[(1,texte),(2,"J'abandonne"),], titre = ("La pièce cochée va être supprimée "), intro = "Suppression demandée")
        if retour[0] != 1 :
            return
        #pour chaque ligne sélectionnée
        for obj in objects:
            dictDonnees =  obj.__dict__
            fGest = GestionInscription.Forfaits(self,self.DB)
            if dictDonnees['nature'] in ('FAC'):
                fGest.RetroFact(self.parent,dictDonnees)
            elif dictDonnees['nature'] in ('AVO'):
                fGest.RetroAvo(self.parent,dictDonnees)
            else:
                fGest.SuppressionPiece(self, dictDonnees)

        self.InitObjectListView()
        self.Refresh()
        return wx.OK
        #fin Supprimer

    def CocheTout(self, event=None):
        if self.GetFilter() != None :
            listeObjets = self.GetFilteredObjects()
        else :
            listeObjets = self.GetObjects()
        for track in listeObjets :
            self.Check(track)
            self.RefreshObject(track)

    def CocheRien(self, event=None):
        if not self.donnees or len(self.donnees) == 0:
            return
        for track in self.donnees :
            self.Uncheck(track)
            self.RefreshObject(track)

    #def GetTracksCoches(self):
    #    return self.GetCheckedObjects()

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

            "label" : {"mode" : "nombre", "singulier" : _("pièce :"), "pluriel" : _("pièces :"), "alignement" : wx.ALIGN_RIGHT},
            "montant" : {"mode" : "total"},
            "mttRegle" : {"mode" : "total"},
            }
        PanelAvecFooter.__init__(self, parent, ListView, kwargs, dictColonnes)


# ----------------- FRAME DE TEST ----------------------------------------------------------------

class MyFrame(wx.Frame):
    def __init__(self, footer, factures, *args, **kwargs):
        wx.Frame.__init__(self, *args, **kwargs)
        panel = wx.Panel(self, -1,name="test1")
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_1.Add(panel, 1, wx.ALL|wx.EXPAND)
        self.SetSizer(sizer_1)
        sizer_2 = wx.BoxSizer(wx.VERTICAL)

        if footer == "sans":
            self.myOlv = ListView(panel, -1,activites = [396,397], IDpayeur = None, factures = factures, style=wx.LC_REPORT|wx.SUNKEN_BORDER,)
            self.myOlv.MAJ()
        else:
            self.myOlv = ListviewAvecFooter(panel,kwargs={"activites" : [396,397], "IDpayeur" : None, "factures" : factures, "parent":self})
            self.olv_piecesFiltrees = self.myOlv.GetListview()
            self.olv_piecesFiltrees.MAJ()
            self.Refresh()
        sizer_2.Add(self.myOlv, 1, wx.ALL|wx.EXPAND, 4)
        panel.SetSizer(sizer_2)
        self.SetSize((900, 400))
        self.Layout()


if __name__ == '__main__':
    app = wx.App(0)
    # Paramétres MyFrame (footer,factures, parent, id, titre)
    frame_1 = MyFrame("sans", False, None, -1,"OL TEST")
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()
