#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys branche Matthania
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS, JB, Jacques Brunel
# Copyright:       (c) 2010-11 Ivan LUCAS, JB
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------


import Chemins
from Utils.UTILS_Traduction import _
import wx
import GestionDB
import datetime

from Utils.UTILS_Decimal import FloatToDecimal as FloatToDecimal

from Utils import UTILS_Titulaires
from Utils import UTILS_Dates
from Utils import UTILS_Utilisateurs
from Utils import UTILS_Config
SYMBOLE = UTILS_Config.GetParametre("monnaie_symbole", "�")

from Ctrl.CTRL_ObjectListView import FastObjectListView, ColumnDefn, Filter, CTRL_Outils, PanelAvecFooter

class Track(object):
    def __init__(self, donnees):
        self.IDfacture = donnees["IDfacture"]
        self.numero = donnees["numero"]
        if self.numero == None : self.numero = 0
        self.IDcompte_payeur = donnees["IDcompte_payeur"]
        self.etat = donnees["etat"]
        self.date_edition = donnees["date_edition"]
        self.date_echeance = donnees["date_echeance"]
        self.IDutilisateur = donnees["IDutilisateur"]
        self.date_debut = donnees["date_debut"]
        self.date_fin = donnees["date_fin"]
        self.total = donnees["totalPrestations"]
        self.regle = donnees["totalVentilation"]
        self.totalVentilation = donnees["totalVentilation"]
        if self.totalVentilation == None :
            self.totalVentilation = FloatToDecimal(0.0)
        self.soldeActuel = self.totalVentilation - self.total
        if self.etat == "annulation" :
            self.soldeActuel = None
        self.IDfamille = donnees["IDfamille"]
        self.nomsTitulaires =  donnees["titulaires"]
        self.IDlot =  donnees["IDlot"]
        self.nomLot =  donnees["nomLot"]
        self.adresse_famille = donnees["adresse_famille"]
        self.titulaire_helios = donnees["titulaire_helios"]
        
        
        # Pr�l�vement
        self.prelevement_activation =  donnees["prelevement_activation"]
        self.prelevement_etab =  donnees["prelevement_etab"]
        self.prelevement_guichet =  donnees["prelevement_guichet"]
        self.prelevement_numero =  donnees["prelevement_numero"]
        self.prelevement_cle =  donnees["prelevement_cle"]
        self.prelevement_banque =  donnees["prelevement_banque"]
        self.prelevement_individu =  donnees["prelevement_individu"]
        self.prelevement_nom =  donnees["prelevement_nom"]
        self.prelevement_rue =  donnees["prelevement_rue"]
        self.prelevement_cp =  donnees["prelevement_cp"]
        self.prelevement_ville =  donnees["prelevement_ville"]
        self.prelevement_cle_iban =  donnees["prelevement_cle_iban"]
        self.prelevement_iban =  donnees["prelevement_iban"]
        self.prelevement_bic =  donnees["prelevement_bic"]
        self.prelevement_reference_mandat =  donnees["prelevement_reference_mandat"]
        self.prelevement_date_mandat =  donnees["prelevement_date_mandat"]

        if self.prelevement_activation == 1 :
            self.prelevement = True
        else :
            self.prelevement = False
        
        self.nomPayeur = donnees["nomPayeur"]
        self.prenomPayeur = donnees["prenomPayeur"]
        if self.nomPayeur == None : self.nomPayeur = ""
        if self.prenomPayeur == None : self.prenomPayeur = ""
        if self.prelevement_individu == None :
            self.prelevement_payeur = self.prelevement_nom
        else :
            self.prelevement_payeur = "%s %s" % (self.nomPayeur, self.prenomPayeur)
        
        # Envoi par Email
        self.email_factures =  donnees["email_factures"]
        
        if self.email_factures != None :
            self.email = True
        else :
            self.email = False

class ListView(FastObjectListView):
    def __init__(self, *args, **kwds):
        # Initialisation du listCtrl
        self.IDcompte_payeur = kwds.pop("IDcompte_payeur", None)
        self.codesColonnes = kwds.pop("codesColonnes", [])
        self.checkColonne = kwds.pop("checkColonne", False)
        self.triColonne = kwds.pop("triColonne", "numero")
        self.afficherAnnulations = kwds.pop("afficherAnnulations", False)
        self.filtres = None
        self.selectionID = None
        self.selectionTrack = None
        FastObjectListView.__init__(self, *args, **kwds)
        # Binds perso
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnActivated)
        self.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)
    
    def SetIDcompte_payeur(self, IDcompte_payeur=None):
        self.IDcompte_payeur = IDcompte_payeur
        
    def OnActivated(self,event):
        self.Reedition(None)

    def InitModel(self):
        self.donnees = self.GetTracks()
    
    def SetFiltres(self, filtres=None):
        """
        None ->                     filtre = None
        IDfacture_intervalle ->  filtre = {"type" : "IDfacture_intervalle", "IDfacture_min" : 22, "IDfacture_max" : 28}
        IDfacture_liste ->         filtre = {"type" : "IDfacture_liste", "liste" : [10, 300, 20] }
        Lot de factures ->        filtre = {"type" : "lot", "IDlot" : 22}
        Date d'�mission ->      filtre = {"type" : "date_emission", "date_debut" : ___, "date_fin" : ___}
        Date d'�ch�ance ->      filtre = {"type" : "date_echance", "date_debut" : ___, "date_fin" : ___}
        numero_intervalle ->    filtre = {"type" : "numero_intervalle", "numero_min" : 210, "numero_max" : 215}
        numero_liste ->           filtre = {"type" : "numero_liste", "liste" : [10, 300, 20] }
        """
        self.filtres = filtres

    def GetListeFactures(self):
        dictTitulaires = UTILS_Titulaires.GetTitulaires([self.IDcompte_payeur,])

        DB = GestionDB.DB()
        
        # Conditions
        listeConditions = []
        
        if self.IDcompte_payeur != None :
            listeConditions.append("prestations.IDcompte_payeur = %d" % self.IDcompte_payeur)
        
        # 1�re s�rie de filtres
        if self.filtres != None :
            for filtre in self.filtres :
            
                # IDfacture_intervalle
                if filtre["type"] == "IDfacture_intervalle" :
                    listeConditions.append( "(factures.IDfacture>=%d AND factures.IDfacture<=%d)" % (filtre["IDfacture_min"], filtre["IDfacture_max"]) )

                # IDfacture_liste
                if filtre["type"] == "IDfacture_liste" :
                    if len(filtre["liste"]) == 0 : listeTemp = "()" 
                    elif len(filtre["liste"]) == 1 : listeTemp = "(%d)" % filtre["liste"][0]
                    else : listeTemp = str(tuple(filtre["liste"]))
                    listeConditions.append( "factures.IDfacture IN %s" % listeTemp)

                # Lot de factures
                if filtre["type"] == "lot" :
                    listeConditions.append( "factures.IDlot=%d" % filtre["IDlot"] )
            
                # Date d'�mission
                if filtre["type"] == "date_emission" :
                    listeConditions.append( "(factures.date_edition>='%s' AND factures.date_edition<='%s')" % (filtre["date_min"], filtre["date_max"]) )

                # Date d'�ch�ance
                if filtre["type"] == "date_echeance" :
                    listeConditions.append( "(factures.date_echeance>='%s' AND factures.date_echeance<='%s')" % (filtre["date_min"], filtre["date_max"]) )

                # numero_intervalle
                if filtre["type"] == "numero_intervalle" :
                    listeConditions.append( "(factures.numero>=%d AND factures.numero<=%d)" % (filtre["numero_min"], filtre["numero_max"]) )

                # numero_liste
                if filtre["type"] == "numero_liste" :
                    if len(filtre["liste"]) == 0 : listeTemp = "()" 
                    elif len(filtre["liste"]) == 1 : listeTemp = "(%d)" % filtre["liste"][0]
                    else : listeTemp = str(tuple(filtre["liste"]))
                    listeConditions.append( "factures.numero IN %s" % listeTemp)

        if len(listeConditions) > 0 :
            conditions = "WHERE %s" % " AND ".join(listeConditions)
        else :
            conditions = ""
        
        # R�cup�ration des totaux des prestations pour chaque facture
        req = """
        SELECT 
        prestations.IDfacture, SUM(prestations.montant)
        FROM prestations
        LEFT JOIN factures ON factures.IDfacture = prestations.IDfacture
        %s
        GROUP BY prestations.IDfacture
        ;""" % conditions
        DB.ExecuterReq(req,MsgBox="OL_Factures")
        listeDonnees = DB.ResultatReq()     
        dictPrestations = {}
        for IDfacture, totalPrestations in listeDonnees :
            if IDfacture != None :
                dictPrestations[IDfacture] = totalPrestations
        
        # R�cup�ration des factures
        req = """
        SELECT factures.IDfacture, factures.numero, factures.IDcompte_payeur, 
        factures.date_edition, factures.date_echeance, factures.IDutilisateur,
        factures.date_debut, factures.date_fin, factures.total, factures.regle, factures.solde,
        comptes_payeurs.IDfamille, factures.IDlot, lots_factures.nom, factures.etat
        FROM factures
        LEFT JOIN comptes_payeurs ON comptes_payeurs.IDcompte_payeur = factures.IDcompte_payeur
        LEFT JOIN lots_factures ON lots_factures.IDlot = factures.IDlot
        %s
        ORDER BY factures.date_edition
        ;""" % conditions.replace("prestations.IDcompte_payeur", "comptes_payeurs.IDcompte_payeur")
        DB.ExecuterReq(req,MsgBox="OL_Factures")
        listeFactures = DB.ResultatReq()
        
        # R�cup�ration de la ventilation
        req = """
        SELECT prestations.IDfacture, SUM(ventilation.montant)
        FROM ventilation
        LEFT JOIN prestations ON prestations.IDprestation = ventilation.IDprestation
        LEFT JOIN comptes_payeurs ON comptes_payeurs.IDcompte_payeur = prestations.IDcompte_payeur
        LEFT JOIN factures ON factures.IDfacture = prestations.IDfacture
        %s
        GROUP BY prestations.IDfacture
        ;""" % conditions
        DB.ExecuterReq(req,MsgBox="OL_Factures")
        listeVentilation = DB.ResultatReq()
        dictVentilation = {}
        for IDfacture, montantVentilation in listeVentilation :
            if IDfacture != None :
                dictVentilation[IDfacture] = montantVentilation
        
        # Infos Pr�l�vement + Envoi par Email des factures
        if self.IDcompte_payeur != None :
            conditions = "WHERE comptes_payeurs.IDcompte_payeur = %d" % self.IDcompte_payeur
        else:
            conditions = ""

        req = """
        SELECT 
        prelevement_activation, prelevement_etab, prelevement_guichet, prelevement_numero, prelevement_cle, prelevement_banque,
        prelevement_individu, prelevement_nom, prelevement_rue, prelevement_cp, prelevement_ville, 
        prelevement_cle_iban, prelevement_iban, prelevement_bic, prelevement_reference_mandat, prelevement_date_mandat, 
        email_factures,
        comptes_payeurs.IDcompte_payeur,
        individus.nom, individus.prenom,
        titulaire_helios
        FROM familles
        LEFT JOIN comptes_payeurs ON comptes_payeurs.IDfamille = familles.IDfamille
        LEFT JOIN individus ON individus.IDindividu = prelevement_individu
        %s
        ;""" % conditions
        DB.ExecuterReq(req,MsgBox="OL_Factures")
        listeInfosFamilles = DB.ResultatReq()
        dictInfosFamilles = {}
        for prelevement_activation, prelevement_etab, prelevement_guichet, prelevement_numero, prelevement_cle, prelevement_banque, prelevement_individu, prelevement_nom, prelevement_rue, prelevement_cp, prelevement_ville, prelevement_cle_iban, prelevement_iban, prelevement_bic, prelevement_reference_mandat, prelevement_date_mandat, email_factures, IDcompte_payeur, nomPayeur, prenomPayeur, titulaire_helios in listeInfosFamilles :
            prelevement_date_mandat = UTILS_Dates.DateEngEnDateDD(prelevement_date_mandat) 
            dictInfosFamilles[IDcompte_payeur] = {
                    "prelevement_activation" : prelevement_activation, "prelevement_etab" : prelevement_etab, "prelevement_guichet" : prelevement_guichet, 
                    "prelevement_numero" : prelevement_numero, "prelevement_cle" : prelevement_cle, "prelevement_banque" : prelevement_banque, 
                    "prelevement_individu" : prelevement_individu, "prelevement_nom" : prelevement_nom, "prelevement_rue" : prelevement_rue, 
                    "prelevement_cp" : prelevement_cp, "prelevement_ville" : prelevement_ville, 
                    "prelevement_cle_iban" : prelevement_cle_iban, "prelevement_iban" : prelevement_iban, "prelevement_bic" : prelevement_bic,
                    "prelevement_reference_mandat" : prelevement_reference_mandat, "prelevement_date_mandat" : prelevement_date_mandat,
                    "email_factures" : email_factures, "nomPayeur" : nomPayeur, "prenomPayeur" : prenomPayeur, "titulaire_helios" : titulaire_helios,
                    }
        
        DB.Close() 
                
        listeResultats = []
        for IDfacture, numero, IDcompte_payeur, date_edition, date_echeance, IDutilisateur, date_debut, date_fin, \
                    total, regle, solde, IDfamille, IDlot, nomLot, etat in listeFactures :
            if numero == None : numero = 0
            date_edition = UTILS_Dates.DateEngEnDateDD(date_edition) 
            date_debut = UTILS_Dates.DateEngEnDateDD(date_debut)
            date_fin = UTILS_Dates.DateEngEnDateDD(date_fin)
            date_echeance = UTILS_Dates.DateEngEnDateDD(date_echeance)       
            total = FloatToDecimal(total)
            if IDfacture in dictVentilation :
                totalVentilation = FloatToDecimal(dictVentilation[IDfacture])
            else :
                totalVentilation = FloatToDecimal(0.0)
            if IDfacture in dictPrestations :
                totalPrestations = FloatToDecimal(dictPrestations[IDfacture])
            else :
                totalPrestations = FloatToDecimal(0.0)
            solde_actuel = totalPrestations - totalVentilation
            if (IDfamille in dictTitulaires) == True :
                
                titulaires = dictTitulaires[IDfamille]["titulairesSansCivilite"]
                adresse_famille = dictTitulaires[IDfamille]["adresse"]
                
                dictTemp = {
                    "IDfacture" : IDfacture, "numero" : numero, "IDcompte_payeur" : IDcompte_payeur, "date_edition" : date_edition, "date_echeance" : date_echeance,
                    "IDutilisateur" : IDutilisateur, "date_debut" : date_debut, "date_fin" : date_fin, "total" : total, "regle" : regle, "solde" : solde, 
                    "totalPrestations" : totalPrestations, "totalVentilation" : totalVentilation, "IDfamille" : IDfamille, "titulaires" : titulaires, "IDlot" : IDlot, "nomLot" : nomLot,
                    "adresse_famille" : adresse_famille, "etat" : etat,
                    }
                
                if IDcompte_payeur in dictInfosFamilles :
                    dictTemp.update(dictInfosFamilles[IDcompte_payeur])

                valide = True
                
                # 2�me s�rie de filtres
                if self.filtres != None :
                    for filtre in self.filtres :
                
                        # IDfacture_intervalle
                        if filtre["type"] == "solde_initial" :
                            if self.ComparateurFiltre(-solde, filtre["operateur"], filtre["montant"]) == False :
                                valide = False

                        if filtre["type"] == "solde_actuel" :
                            if self.ComparateurFiltre(-solde_actuel, filtre["operateur"], filtre["montant"]) == False :
                                valide = False

                        if filtre["type"] == "prelevement" :
                            if filtre["choix"] == True :
                                if dictTemp["prelevement_activation"] == None : valide = False
                            else :
                                if dictTemp["prelevement_activation"] != None : valide = False

                        if filtre["type"] == "email" :
                            if filtre["choix"] == True :
                                if dictTemp["email_factures"] == None : valide = False
                            else :
                                if dictTemp["email_factures"] != None : valide = False
                
                if etat == "annulation" and self.afficherAnnulations == False :
                    valide = False
                    
                # M�morisation des valeurs
                if valide == True :                    
                    listeResultats.append(dictTemp)
            
        return listeResultats
    
    def ComparateurFiltre(self, valeur1=12.00, operateur=">=", valeur2=0.0):
        if operateur == "=" : 
            if valeur1 == valeur2 : return True
        if operateur == "<>" : 
            if valeur1 != valeur2 : return True
        if operateur == ">" : 
            if valeur1 > valeur2 : return True
        if operateur == "<" : 
            if valeur1 < valeur2 : return True
        if operateur == ">=" : 
            if valeur1 >= valeur2 : return True
        if operateur == "<=" : 
            if valeur1 <= valeur2 : return True
        return False

    def GetTracks(self):
        # R�cup�ration des donn�es
        listeID = None
        listeDonnees = self.GetListeFactures() 
    
        listeListeView = []
        for item in listeDonnees :
            valide = True
            if listeID != None :
                if item[0] not in listeID :
                    valide = False
            if valide == True :
                track = Track(item)
                listeListeView.append(track)
                if self.selectionID == item["IDfacture"] :
                    self.selectionTrack = track
        return listeListeView

    def InitObjectListView(self):
        
        # ImageList
        self.imgVert = self.AddNamedImages("vert", wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Ventilation_vert.png"), wx.BITMAP_TYPE_PNG))
        self.imgRouge = self.AddNamedImages("rouge", wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Ventilation_rouge.png"), wx.BITMAP_TYPE_PNG))
        self.imgOrange = self.AddNamedImages("orange", wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Ventilation_orange.png"), wx.BITMAP_TYPE_PNG))
        self.imgPrelevement = self.AddNamedImages("prelevement", wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Prelevement.png"), wx.BITMAP_TYPE_PNG))
        self.imgEmail = self.AddNamedImages("email", wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Emails_exp.png"), wx.BITMAP_TYPE_PNG))
        self.imgAnnulation = self.AddNamedImages("annulation", wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Supprimer_2.png"), wx.BITMAP_TYPE_PNG))

        def GetImageSoldeActuel(track):
            if track.etat == "annulation" : 
                return self.imgAnnulation
            if track.soldeActuel == FloatToDecimal(0.0) :
                return self.imgVert
            if track.soldeActuel < FloatToDecimal(0.0) and track.soldeActuel != -track.total :
                return self.imgOrange
            return self.imgRouge
        
        def GetImagePrelevement(track):
            if track.prelevement == True :
                return self.imgPrelevement

        def GetImageEmail(track):
            if track.email == True :
                return self.imgEmail
        
        def FormateNumero(numero):
            if numero == None :
                return ""
            if type(numero) == str or type(numero) == str :
                numero = int(numero)
            return "%06d" % numero

        def FormateDate(dateDD):
            if dateDD == None : return ""
            return UTILS_Dates.DateEngFr(str(dateDD))

        def FormateMontant(montant):
            if montant == None or montant == "" : return ""
            return "%.2f %s" % (montant, SYMBOLE)
                   
        def rowFormatter(listItem, track):
            if track.etat == "annulation" :
                listItem.SetTextColour(wx.Colour(255, 0, 0))
                
        # Couleur en alternance des lignes
        self.oddRowsBackColor = wx.Colour(255, 255, 255) #"#EEF4FB" # Bleu
        self.evenRowsBackColor = "#F0FBED" # Vert

        # Param�tres ListView
        self.useExpansionColumn = True
        
        dictColonnes = {
            "IDfacture" : ColumnDefn("", "left", 0, "IDfacture", typeDonnee="entier"),
            "date" : ColumnDefn(_("Date"), "centre", 80, "date_edition", typeDonnee="date", stringConverter=FormateDate),
            "numero" : ColumnDefn("N�", "centre", 65, "numero", typeDonnee="entier", stringConverter=FormateNumero),
            "famille" : ColumnDefn(_("Famille"), "left", 180, "nomsTitulaires", typeDonnee="texte"),
            "date_debut" : ColumnDefn(_("Date d�but"), "centre", 80, "date_debut", typeDonnee="date", stringConverter=FormateDate),
            "date_fin" : ColumnDefn(_("Date fin"), "centre", 80, "date_fin", typeDonnee="date", stringConverter=FormateDate),
            "total" : ColumnDefn(_("Total"), "right", 65, "total", typeDonnee="montant", stringConverter=FormateMontant),
            "regle" : ColumnDefn(_("R�gl�"), "right", 65, "regle", typeDonnee="montant", stringConverter=FormateMontant),
            "solde_actuel" : ColumnDefn(_("Solde"), "right", 90, "soldeActuel", typeDonnee="montant", stringConverter=FormateMontant, imageGetter=GetImageSoldeActuel),
            "date_echeance" : ColumnDefn(_("Ech�ance"), "centre", 80, "date_echeance", typeDonnee="date", stringConverter=FormateDate),
            "nom_lot" : ColumnDefn(_("Lot"), "left", 150, "nomLot", typeDonnee="texte"),
            "prelevement" : ColumnDefn("P", "left", 20, "", imageGetter=GetImagePrelevement),
            "email" : ColumnDefn("E", "left", 20, "", imageGetter=GetImageEmail),
            }
            
        listeColonnes = []
        tri = None
        index = 0
        for codeColonne in self.codesColonnes :
            listeColonnes.append(dictColonnes[codeColonne])
            # Checkbox 
            if codeColonne == self.triColonne :
                tri = index
            index += 1

        self.rowFormatter = rowFormatter
        self.SetColumns(listeColonnes)
        if self.checkColonne == True :
            self.CreateCheckStateColumn(1)
        if tri != None :
            if self.checkColonne == True : tri += 1
            self.SetSortColumn(self.columns[tri])

        self.SetEmptyListMsg(_("Aucune facture"))
        self.SetEmptyListMsgFont(wx.FFont(11, wx.DEFAULT, False, "Tekton"))
        self.SetObjects(self.donnees)

    def MAJ(self, ID=None):
        if ID != None :
            self.selectionID = ID
            self.selectionTrack = None
        else:
            self.selectionID = None
            self.selectionTrack = None
        self.InitModel()
        self.InitObjectListView()
        # S�lection d'un item
        if self.selectionTrack != None :
            self.SelectObject(self.selectionTrack, deselectOthers=True, ensureVisible=True)
        self.selectionID = None
        self.selectionTrack = None
        # MAJ du total du panel
        try :
            if self.GetParent().GetName() == "panel_prestations" :
                self.GetParent().MAJtotal()
        except :
            pass
    
    def Selection(self):
        return self.GetSelectedObjects()
    
    def DefilePremier(self):
        if len(self.GetObjects()) > 0 :
            self.EnsureCellVisible(0, 0)

    def OnContextMenu(self, event):
        """Ouverture du menu contextuel """
        if len(self.Selection()) > 0 :
            ID = self.Selection()[0].IDfacture
        
        # Cr�ation du menu contextuel
        menuPop = wx.Menu()

        # Item R��diter la facture
        item = wx.MenuItem(menuPop, 60, _("Aper�u PDF de la facture"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Apercu.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.Reedition, id=60)

        # Item Envoyer la facture par Email
        item = wx.MenuItem(menuPop, 90, _("Envoyer la facture par Email"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Emails_exp.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.EnvoyerEmail, id=90)
        
        menuPop.AppendSeparator()

        # Item Supprimer
        item = wx.MenuItem(menuPop, 30, _("Supprimer ou annuler"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Supprimer.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.Supprimer, id=30)
        if len(self.Selection()) == 0 and len(self.GetTracksCoches()) == 0 : item.Enable(False)

        menuPop.AppendSeparator()
        
        if self.checkColonne == True :

            # Item Tout cocher
            item = wx.MenuItem(menuPop, 70, _("Tout cocher"))
            item.SetBitmap(wx.Bitmap("Static/Images/16x16/Cocher.png", wx.BITMAP_TYPE_PNG))
            menuPop.Append(item)
            self.Bind(wx.EVT_MENU, self.CocheTout, id=70)

            # Item Tout d�cocher
            item = wx.MenuItem(menuPop, 80, _("Tout d�cocher"))
            item.SetBitmap(wx.Bitmap("Static/Images/16x16/Decocher.png", wx.BITMAP_TYPE_PNG))
            menuPop.Append(item)
            self.Bind(wx.EVT_MENU, self.CocheRien, id=80)

            menuPop.AppendSeparator()

        # Item Apercu avant impression
        item = wx.MenuItem(menuPop, 40, _("Aper�u avant impression"))
        bmp = wx.Bitmap("Static/Images/16x16/Apercu.png", wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.Apercu, id=40)

        # Item Imprimer
        item = wx.MenuItem(menuPop, 50, _("Imprimer"))
        bmp = wx.Bitmap("Static/Images/16x16/Imprimante.png", wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.Imprimer, id=50)

        menuPop.AppendSeparator()

        # Item Export Texte
        item = wx.MenuItem(menuPop, 600, _("Exporter au format Texte"))
        bmp = wx.Bitmap("Static/Images/16x16/Texte2.png", wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.ExportTexte, id=600)

        # Item Export Excel
        item = wx.MenuItem(menuPop, 700, _("Exporter au format Excel"))
        bmp = wx.Bitmap("Static/Images/16x16/Excel.png", wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.ExportExcel, id=700)

        self.PopupMenu(menuPop)
        menuPop.Destroy()

    def GetlstIDfactures(self):
        tracks = self.Selection()
        if len(tracks) == 0 :
            dlg = wx.MessageDialog(self, _("Vous n'avez s�lectionn� aucune facture � imprimer !"),
                                   _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return None
        lstIDfactures = []
        for track in tracks:
            if track.etat == "annulation" :
                dlg = wx.MessageDialog(self, _("Vous ne pouvez pas agir sur une facture annul�e !"),
                                       _("Information"), wx.OK | wx.ICON_EXCLAMATION)
                dlg.ShowModal()
                dlg.Destroy()
            else:
                lstIDfactures.append(track.IDfacture)
        return lstIDfactures

    def Reedition(self, event):
        lstIDfactures = self.GetlstIDfactures()
        if lstIDfactures:
            from Utils import UTILS_Facturation
            facturation = UTILS_Facturation.Facturation()
            facturation.Impression(listeFactures=lstIDfactures,typeLancement="factures")
    
    def EnvoyerEmail(self, event):
        """ Envoyer la facture par Email """
        lstIDfactures = self.GetlstIDfactures()
        if lstIDfactures:
            # Envoi du mail
            from Utils import UTILS_Envoi_email
            total = self.Selection()[0].total
            if total < 0: nature = "AVOIR"
            else: nature = "FACTURE"
            ID = self.Selection()[0].numero
            horodatage = datetime.datetime.now().strftime("%Y%m%d")
            IDdoc = "%s-%d" % (horodatage,ID)
            IDfamille = self.Selection()[0].IDfamille
            from Utils import UTILS_Fichiers
            nomDoc = UTILS_Fichiers.GetRepTemp("%s%s.pdf" %(nature,IDdoc))
            UTILS_Envoi_email.EnvoiEmailFamille(parent=self, IDfamille=IDfamille,
                                                nomDoc= nomDoc ,
                                                categorie="facture")

    def CreationPDF(self, nomDoc="", afficherDoc=True):        
        """ Cr�ation du PDF pour Email  Indissociable de EnvoyerEmail car appel� par UTILS_Envoi_email"""
        lstIDfactures = self.GetlstIDfactures()
        if lstIDfactures:
            from Utils import UTILS_Facturation
            facturation = UTILS_Facturation.Facturation()
            resultat = facturation.Impression(listeFactures=lstIDfactures, nomDoc=nomDoc, afficherDoc=afficherDoc)
            if resultat == False :
                return False
            dictChampsFusion, dictPieces = resultat
            del facturation
            return dictChampsFusion[list(dictChampsFusion.keys())[0]]
    
    def GetTextesImpression(self):
        total = _("%d factures. ") % len(self.donnees)
        if self.filtres != None :
            from Dlg.DLG_Filtres_factures import GetTexteFiltres 
            intro = total + _("Filtres de s�lection : %s") % GetTexteFiltres(self.filtres)
        else :
            intro = None
        return intro, total

    def Apercu(self, event=None):
        from Utils import UTILS_Printer
        txtIntro, txtTotal = self.GetTextesImpression()
        prt = UTILS_Printer.ObjectListViewPrinter(self, titre=_("Liste des factures"), intro=txtIntro, total=txtTotal, format="A", orientation=wx.PORTRAIT)
        prt.Preview()

    def Imprimer(self, event=None):
        from Utils import UTILS_Printer
        txtIntro, txtTotal = self.GetTextesImpression()
        prt = UTILS_Printer.ObjectListViewPrinter(self, titre=_("Liste des factures"), intro=txtIntro, total=txtTotal, format="A", orientation=wx.PORTRAIT)
        prt.Print()

    def ExportTexte(self, event=None):
        from Utils import UTILS_Export
        UTILS_Export.ExportTexte(self, titre=_("Liste des factures"))

    def ExportExcel(self, event=None):
        from Utils import UTILS_Export
        UTILS_Export.ExportExcel(self, titre=_("Liste des factures"))

    def CocheTout(self, event=None):
        if self.GetFilter() != None :
            listeObjets = self.GetFilteredObjects()
        else :
            listeObjets = self.GetObjects()
        for track in listeObjets :
            self.Check(track)
            self.RefreshObject(track)

    def CocheRien(self, event=None):
        for track in self.donnees :
            self.Uncheck(track)
            self.RefreshObject(track)

    def GetTracksCoches(self):
        return self.GetCheckedObjects()
    
    def GetTracksTous(self):
        return self.donnees

    def Supprimer(self, event):
        if self.IDcompte_payeur != None and UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("familles_factures", "supprimer") == False : return
        if self.IDcompte_payeur == None and UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("facturation_factures", "supprimer") == False : return
        # Avertissements
        dlg = wx.MessageDialog(self, _("Passez par FACTURATION ou par INSCRIPTION pour g�rer des avoirs"), _("Refus"), wx.CANCEL|wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()
        return False

    def OuvrirFicheFamille(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("familles_fiche", "consulter") == False : return
        if len(self.Selection()) == 0 :
            dlg = wx.MessageDialog(self, _("Vous n'avez s�lectionn� aucune fiche famille � ouvrir !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        IDfamille = self.Selection()[0].IDfamille
        IDfacture = self.Selection()[0].IDfacture
        from Dlg import DLG_Famille
        dlg = DLG_Famille.Dialog(self, IDfamille)
        if dlg.ShowModal() == wx.ID_OK:
            self.MAJ(IDfacture)
        dlg.Destroy()


# -------------------------------------------------------------------------------------------------------------------------------------------

class BarreRecherche(wx.SearchCtrl):
    def __init__(self, parent, listview=None):
        wx.SearchCtrl.__init__(self, parent, size=(-1, -1), style=wx.TE_PROCESS_ENTER)
        self.parent = parent
        self.rechercheEnCours = False
        
        self.SetDescriptiveText(_("Rechercher..."))
        self.ShowSearchButton(True)
        
        if listview != None :
            self.listView = listview
        else :
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
            "date_edition" : {"mode" : "nombre", "singulier" : _("facture"), "pluriel" : _("factures"), "alignement" : wx.ALIGN_CENTER},
            "total" : {"mode" : "total"},
            "regle" : {"mode" : "total"},
            "soldeActuel" : {"mode" : "total"},
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

        IDcompte_payeur = None
        codesColonnes = ["IDfacture", "date", "numero", "famille", "prelevement", "email", "date_debut", "date_fin", "total", "regle", "solde_actuel", "date_echeance", "nom_lot"]
        checkColonne = True
        triColonne = "numero"

##        listview = ListView(panel, -1, IDcompte_payeur=IDcompte_payeur, codesColonnes=codesColonnes, checkColonne=checkColonne, triColonne=triColonne, style=wx.LC_HRULES|wx.LC_VRULES|wx.LC_REPORT|wx.SUNKEN_BORDER)
##        listview.MAJ() 

        ctrl = ListviewAvecFooter(panel, kwargs={"IDcompte_payeur" : IDcompte_payeur, "codesColonnes" : codesColonnes, "checkColonne" : checkColonne, "triColonne" : triColonne}) 
        listview = ctrl.GetListview()
        listview.MAJ() 

        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_2.Add(ctrl, 1, wx.ALL|wx.EXPAND, 4)
        panel.SetSizer(sizer_2)
        self.SetSize((1150, 400))
        self.Layout()


if __name__ == '__main__':
    app = wx.App(0)
    #wx.InitAllImageHandlers()
    frame_1 = MyFrame(None, -1, "GroupListView")
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()
