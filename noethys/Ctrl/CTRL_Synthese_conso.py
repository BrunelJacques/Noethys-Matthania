#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#-----------------------------------------------------------
# Application :    Noethys, Modifs pour pouvoir prendre toutes les activités
# Site internet :  www.noethys.com, Jacques Brunel
# Auteur:           Ivan LUCAS, JB
# Copyright:       (c) 2010-12 Ivan LUCAS, JB
# Licence:         Licence GNU GPL
#-----------------------------------------------------------


from Utils.UTILS_Traduction import _

import wx
import Chemins
import wx.grid as gridlib
import wx.lib.wordwrap as wordwrap
import Outils.gridlabelrenderer as glr
import datetime
import FonctionsPerso
import sys
import traceback
import GestionDB
from Utils import UTILS_Fichiers
from Utils import UTILS_Organisateur
import wx.lib.agw.pybusyinfo as PBI

LISTE_MOIS = (_("janvier"), _("février"), _("mars"), _("avril"), _("mai"), _("juin"), _("juillet"), _("août"), _("septembre"), _("octobre"), _("novembre"), _("décembre"))

def DateComplete(dateDD):
    """ Transforme une date DD en date complète : Ex : lundi 15 janvier 2008 """
    listeJours = (_("Lundi"), _("Mardi"), _("Mercredi"), _("Jeudi"), _("Vendredi"), _("Samedi"), _("Dimanche"))
    dateComplete = listeJours[dateDD.weekday()] + " " + str(dateDD.day) + " " + LISTE_MOIS[dateDD.month-1] + " " + str(dateDD.year)
    return dateComplete

def FormateMois(xxx_todo_changeme):
    (annee, mois) = xxx_todo_changeme
    return "%s %d" % (LISTE_MOIS[mois-1].capitalize(), annee)
    
def DateEngEnDateDD(dateEng):
    if dateEng and not isinstance(dateEng,str): dateEng = str(dateEng)
    return datetime.date(int(dateEng[:4]), int(dateEng[5:7]), int(dateEng[8:10]))

def DateEngFr(textDate):
    if textDate == None: return ""
    textDate = str(textDate)
    text = str(textDate[8:10]) + "/" + str(textDate[5:7]) + "/" + str(textDate[:4])
    return text

def HeureStrEnTime(heureStr):
    if heureStr == None or heureStr == "" : return datetime.time(0, 0)
    heures, minutes = heureStr.split(":")
    return datetime.time(int(heures), int(minutes))
    
##def FormateValeur(valeur, mode="quantite"):
##    if mode == "quantite" :
##        return str(valeur)
##    if "temps" in mode :
##        if "." not in str(valeur) :
##            valeur = float(valeur)
##        hr, dec = str(valeur).split(".")
##        if len(dec) == 1 : 
##            mn = int(dec) * 0.1
##        else:
##            mn = int(dec) * 0.01
##        mn = mn * 60 #int(dec)*60/100.0
##        mn = math.ceil(mn)
##        return "%sh%02d" % (hr, mn)

def FormateValeur(valeur, mode="quantite"):
    if mode == "quantite" :
        return str(valeur)
    if "temps" in mode :
        heures = (valeur.days*24) + (valeur.seconds/3600)
        minutes = valeur.seconds%3600/60
        return "%dh%02d" % (heures, minutes)


    
class MyRowLabelRenderer(glr.GridLabelRenderer):
    def __init__(self, bgcolor):
        self._bgcolor = bgcolor
        
    def Draw(self, grid, dc, rect, row):
        if self._bgcolor != None :
            dc.SetBrush(wx.Brush(self._bgcolor))
            dc.SetPen(wx.TRANSPARENT_PEN)
            dc.DrawRectangle(rect)
        else:
            pass
        hAlign, vAlign = grid.GetRowLabelAlignment()
        text = grid.GetRowLabelValue(row)
        self.DrawBorder(grid, dc, rect)
        self.DrawText(grid, dc, rect, text, hAlign, vAlign)
    
    def MAJ(self, couleur):
        self._bgcolor = couleur
        

class MyColLabelRenderer(glr.GridLabelRenderer):
    def __init__(self, typeColonne=None, bgcolor=None):
        self.typeColonne = typeColonne
        self._bgcolor = bgcolor
        
    def Draw(self, grid, dc, rect, col):
        if self._bgcolor != None :
            dc.SetBrush(wx.Brush(self._bgcolor))
            dc.SetPen(wx.TRANSPARENT_PEN)
            dc.DrawRectangle(rect)
        hAlign, vAlign = grid.GetColLabelAlignment()
        text = grid.GetColLabelValue(col)
        if self.typeColonne == "unite" :
            text = wordwrap.wordwrap(text, LARGEUR_COLONNE_UNITE, dc)
        if self.typeColonne == "unite" :
            self.DrawBorder(grid, dc, rect)
        self.DrawText(grid, dc, rect, text, hAlign, vAlign)



class CTRL(gridlib.Grid, glr.GridWithLabelRenderersMixin): 
    def __init__(self, parent):
        gridlib.Grid.__init__(self, parent, -1, style=wx.WANTS_CHARS)
        glr.GridWithLabelRenderersMixin.__init__(self)
        self.moveTo = None
        self.GetGridWindow().SetToolTip("")
        self.CreateGrid(0, 0)
        self.SetRowLabelSize(200)
        self.SetColLabelSize(45)
        self.DisableDragColSize()
        self.DisableDragRowSize()
        
        # Paramètres par défaut
        self.date_debut = None
        self.date_fin = None
        self.IDactivite = []
        self.detail_groupes = False
        self.affichage_regroupement = "jour"
        self.affichage_donnees = "quantite"
        self.affichage_mode = "reservation"
        self.affichage_etat = ["reservation", "present"]
        self.labelParametres = ""
                

    def MAJ(self, date_debut=None, date_fin=None, IDactivite=None, listeGroupes=[], detail_groupes=False, affichage_donnees="quantite", 
                        affichage_regroupement="jour", affichage_mode="reservation", affichage_etat=["reservation", "present"], labelParametres=""):     

        # Chargement des informations individuelles
        """if self.date_debut != date_debut :
            self.infosIndividus = UTILS_Infos_individus.Informations(date_reference=date_debut, qf=True, inscriptions=True, messages=False, infosMedicales=False, cotisationsManquantes=False, piecesManquantes=False, questionnaires=True, scolarite=True)
            self.dictInfosIndividus = self.infosIndividus.GetDictValeurs(mode="individu", ID=None, formatChamp=False)
            self.dictInfosFamilles = self.infosIndividus.GetDictValeurs(mode="famille", ID=None, formatChamp=False)
        """
        # Mémorisation des paramètres
        self.IDactivite = IDactivite
        self.date_debut = date_debut
        self.date_fin = date_fin
        self.listeIDactivite = []
        self.listeIDgroupe =[]
        if IDactivite != None :
            self.touteActivite = False
            self.listeIDactivite.append(IDactivite)
            self.listeIDgroupe = listeGroupes
        else :
            self.touteActivite = True
            DB = GestionDB.DB()
            req = """SELECT IDactivite
                    FROM activites
                    WHERE (date_debut <= '%s' ) and ( date_fin >= '%s')
                    ;""" % (date_fin,date_debut)
            DB.ExecuterReq(req,MsgBox="ExecuterReq")
            recordset = DB.ResultatReq()
            for record in recordset:
                self.listeIDactivite.append(record[0])
            req = """SELECT IDgroupe
                    FROM groupes
                    WHERE IDactivite in ( %s )
                    ;""" % (str(self.listeIDactivite)[1:-1])
            DB.ExecuterReq(req,MsgBox="ExecuterReq")
            recordset = DB.ResultatReq()
            for record in recordset:
                self.listeIDgroupe.append(record[0])
            DB.Close()
        self.detail_groupes = detail_groupes
        self.affichage_donnees = affichage_donnees
        self.affichage_regroupement = affichage_regroupement
        self.affichage_mode = affichage_mode
        self.affichage_etat = affichage_etat
        self.labelParametres = labelParametres

        # init grid
        try :
            dlgAttente = PBI.PyBusyInfo(_("Veuillez patienter durant la recherche des données..."), parent=None, title=_("Calcul en cours"), icon=wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Logo.png"), wx.BITMAP_TYPE_ANY))
            wx.Yield() 
            self.InitGrid() 
            del dlgAttente
        except Exception as err:
            del dlgAttente
            traceback.print_exc(file=sys.stdout)
            dlg = wx.MessageDialog(self, _("Désolé, le problème suivant a été rencontré dans la recherche des données de la synthèse des consommations : \n\n%s") % err, _("Erreur"), wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            return False

    def Importation(self):
        # Récupération des données
        if self.touteActivite :
            dictResultats, listeUnites, listeGroupes, listeColonnes = self.ImportMulti()
        else :
            dictResultats, listeUnites, listeGroupes, listeColonnes = self.ImportMono()
        return dictResultats, listeUnites, listeGroupes, listeColonnes

    def ImportMulti(self):
        DB = GestionDB.DB()
        if len(self.listeIDgroupe) == 0 : conditionGroupes = "()"
        elif len(self.listeIDgroupe) == 1 : conditionGroupes = "(%d)" % self.listeIDgroupe[0]
        else : conditionGroupes = str(tuple(self.listeIDgroupe))

        if self.affichage_mode == "reservation" :
            if len(self.affichage_etat) == 0 :
                conditionEtat = "()"
            elif len(self.affichage_etat) == 1 :
                conditionEtat = "('%s')" % self.affichage_etat[0]
            else :
                conditionEtat = str(tuple(self.affichage_etat))
        elif self.affichage_mode == "attente" :
            conditionEtat = "('attente')"
        elif self.affichage_mode == "refus" :
            conditionEtat = "('refus')"
        else :
            conditionEtat = "()"

        # Consommations
        req = """SELECT IDconso, consommations.date, consommations.IDindividu, consommations.IDunite, consommations.IDgroupe, consommations.IDactivite,
                heure_debut, heure_fin, etat, quantite, consommations.IDprestation, prestations.temps_facture,
                comptes_payeurs.IDfamille, activites.nom, groupes.abrege, categories_tarifs.nom
                FROM consommations
                LEFT JOIN prestations ON prestations.IDprestation = consommations.IDprestation
                LEFT JOIN comptes_payeurs ON comptes_payeurs.IDcompte_payeur = consommations.IDcompte_payeur
                LEFT JOIN activites ON activites.IDactivite = consommations.IDactivite
                LEFT JOIN groupes ON groupes.IDgroupe = consommations.IDgroupe
                LEFT JOIN categories_tarifs ON categories_tarifs.IDcategorie_tarif = consommations.IDcategorie_tarif
                WHERE consommations.IDactivite in ( %s ) AND consommations.IDgroupe IN %s
                AND consommations.date>='%s' AND consommations.date<='%s'
                AND etat IN %s
                ;""" % (str(self.listeIDactivite)[1:-1], conditionGroupes, self.date_debut, self.date_fin, conditionEtat)
        DB.ExecuterReq(req,MsgBox="ExecuterReq")
        listeConsommations = DB.ResultatReq()

        # Calcul des données
        dictResultats = {}
        for IDconso, date, IDindividu, IDunite, IDgroupe, IDactivite, heure_debut, heure_fin, etat, quantite, IDprestation, tempsFacture, IDfamille, nomActivite, nomGroupe, nomCategorie in listeConsommations :
            date = DateEngEnDateDD(date)
            mois = date.month
            annee = date.year

            # Recherche du regroupement
            try :
                if self.affichage_regroupement == "jour" : regroupement = date
                if self.affichage_regroupement == "mois" : regroupement = (annee, mois)
                if self.affichage_regroupement == "annee" : regroupement = annee
                if self.affichage_regroupement == "activite" : regroupement = nomActivite
                if self.affichage_regroupement == "groupe" : regroupement = nomGroupe
                if self.affichage_regroupement == "categorie_tarif" : regroupement = nomCategorie

            except :
                regroupement = None

            if regroupement in ("", None) :
                regroupement = _("- Non renseigné -")

            # Quantité
            if quantite == None :
                quantite = 1

            if self.detail_groupes == True :
                groupe = IDgroupe
            else :
                groupe = None

            valeur = quantite
            defaut = 0

            if (groupe in dictResultats) == False :
                dictResultats[groupe] = {}
            if (IDunite in dictResultats[groupe]) == False :
                dictResultats[groupe][IDunite] = {}
            if (regroupement in dictResultats[groupe][IDunite]) == False :
                dictResultats[groupe][IDunite][regroupement] = defaut
            dictResultats[groupe][IDunite][regroupement] += valeur

        lstIDgroupes = list(dictResultats.keys())
        lstIDunite = []
        listeColonnes = []
        for IDgroupe in lstIDgroupes:
            lstIDunite.extend(list(dictResultats[IDgroupe].keys()))
            listeColonnes.append((IDgroupe,list(dictResultats[IDgroupe].keys())))

        # Unités
        req = """SELECT unites.IDunite, unites.abrege, activites.abrege
                FROM unites
                LEFT JOIN activites ON activites.IDactivite = unites.IDactivite
                WHERE unites.IDunite IN ( %s );""" % (str(lstIDunite)[1:-1])
        DB.ExecuterReq(req, MsgBox = "CTRL_Synthese_conso")
        recordset = DB.ResultatReq()
        listeUnites = []
        for ID, unite, activite in recordset:
            if unite == None : unite = " "
            if activite == None : activite = " "
            listeUnites.append((ID,activite + "\n" + unite))
        # Groupes
        req = """SELECT IDgroupe,abrege
                FROM groupes
                WHERE IDgroupe in ( %s )
                ;""" % (str(lstIDgroupes)[1:-1])
        DB.ExecuterReq(req,MsgBox="ExecuterReq")
        listeGroupes = DB.ResultatReq()
        DB.Close()
        return dictResultats, listeUnites, listeGroupes, listeColonnes
        #fin ImportMulti

    def ImportMono(self):
        DB = GestionDB.DB()
        if len(self.listeIDgroupe) == 0 : conditionGroupes = "()"
        elif len(self.listeIDgroupe) == 1 : conditionGroupes = "(%d)" % self.listeIDgroupe[0]
        else : conditionGroupes = str(tuple(self.listeIDgroupe))
        
        if self.affichage_mode == "reservation" :
            if len(self.affichage_etat) == 0 : 
                conditionEtat = "()"
            elif len(self.affichage_etat) == 1 : 
                conditionEtat = "('%s')" % self.affichage_etat[0]
            else : 
                conditionEtat = str(tuple(self.affichage_etat))
        elif self.affichage_mode == "attente" :
            conditionEtat = "('attente')"
        elif self.affichage_mode == "refus" :
            conditionEtat = "('refus')"
        else :
            conditionEtat = "()"
        
        # Unités
        req = """SELECT IDunite, abrege
                FROM unites
                WHERE IDactivite=%d
                ORDER BY ordre;""" % self.IDactivite
        DB.ExecuterReq(req,MsgBox="ExecuterReq")
        listeUnites = DB.ResultatReq()
        
        # Groupes
        req = """SELECT IDgroupe, abrege
                FROM groupes
                WHERE IDactivite=%d
                ORDER BY ordre;""" % self.IDactivite
        DB.ExecuterReq(req,MsgBox="ExecuterReq")
        listeGroupes = DB.ResultatReq()

        # Consommations
        req = """SELECT IDconso, consommations.date, consommations.IDindividu, consommations.IDunite, consommations.IDgroupe, consommations.IDactivite, consommations.etiquettes,
        heure_debut, heure_fin, etat, quantite, consommations.IDprestation, prestations.temps_facture,
        comptes_payeurs.IDfamille,  
        activites.nom,
        groupes.nom,
        categories_tarifs.nom
        FROM consommations
        LEFT JOIN prestations ON prestations.IDprestation = consommations.IDprestation
        LEFT JOIN comptes_payeurs ON comptes_payeurs.IDcompte_payeur = consommations.IDcompte_payeur
        LEFT JOIN activites ON activites.IDactivite = consommations.IDactivite
        LEFT JOIN groupes ON groupes.IDgroupe = consommations.IDgroupe
        LEFT JOIN categories_tarifs ON categories_tarifs.IDcategorie_tarif = consommations.IDcategorie_tarif
        WHERE consommations.IDactivite=%d AND consommations.IDgroupe IN %s 
        AND consommations.date>='%s' AND consommations.date<='%s'
        AND etat IN %s
        ;""" % (self.IDactivite, conditionGroupes, self.date_debut, self.date_fin, conditionEtat)
        DB.ExecuterReq(req,MsgBox="ExecuterReq")
        listeConsommations = DB.ResultatReq()
        DB.Close() 
        
        # Calcul des données
        dictResultats = {}
        listePrestationsTraitees = []
        for IDconso, date, IDindividu, IDunite, IDgroupe, IDactivite, etiquettes, heure_debut, heure_fin, etat, quantite, IDprestation, tempsFacture, IDfamille, nomActivite, nomGroupe, nomCategorie in listeConsommations :
            date = DateEngEnDateDD(date)
            mois = date.month
            annee = date.year           
            
            # Recherche du regroupement
            try :
                if self.affichage_regroupement == "jour" : regroupement = date
                if self.affichage_regroupement == "mois" : regroupement = (annee, mois)
                if self.affichage_regroupement == "annee" : regroupement = annee
                if self.affichage_regroupement == "activite" : regroupement = nomActivite
                if self.affichage_regroupement == "groupe" : regroupement = nomGroupe
                if self.affichage_regroupement == "categorie_tarif" : regroupement = nomCategorie

            except :
                regroupement = None
            
            if regroupement in ("", None) :
                regroupement = _("- Non renseigné -")
            
            # Quantité
            if quantite == None :
                quantite = 1

            if self.detail_groupes == True :
                groupe = IDgroupe
            else :
                groupe = None
                
            valeur = quantite
            defaut = 0

            # En cas de regroupements multiples :
            if type(regroupement) == list :
                listeRegroupements = regroupement
            else :
                listeRegroupements = [regroupement,]

            for regroupement in listeRegroupements :
                if (groupe in dictResultats) == False :
                    dictResultats[groupe] = {}
                if (IDunite in dictResultats[groupe]) == False :
                    dictResultats[groupe][IDunite] = {}
                if (regroupement in dictResultats[groupe][IDunite]) == False :
                    dictResultats[groupe][IDunite][regroupement] = defaut
                dictResultats[groupe][IDunite][regroupement] += valeur
        lstIDgroupes = list(dictResultats.keys())
        listeColonnes = []
        for IDgroupe in lstIDgroupes:
            listeColonnes.append((IDgroupe,list(dictResultats[IDgroupe].keys())))
        DB.Close()
        return dictResultats, listeUnites, listeGroupes, listeColonnes
        #fin ImportMono

    def ResetGrid(self):
        # Reset grille
        if self.GetNumberRows() > 0 : 
            self.DeleteRows(0, self.GetNumberRows())
        if self.GetNumberCols() > 0 : 
            self.DeleteCols(0, self.GetNumberCols())
        self.ClearGrid()
        
    def InitGrid(self):
        self.ResetGrid() 
        
        # Récupération des données
        dictResultats, listeUnites, listeGroupes, listeColonnes = self.Importation()
        
        if self.affichage_donnees == "quantite" :
            defaut = 0
        else :
            defaut = datetime.timedelta(hours=0, minutes=0)

        #listeGroupesUtilises = []
        #listeUnitesUtilises = []
        listeRegroupement = []
        dictTotaux = { "lignes" : {}, "colonnes" : {} }
        for IDgroupe, dictGroupe in dictResultats.items() :
            #if IDgroupe not in listeGroupesUtilises :
            #    listeGroupesUtilises.append(IDgroupe)
            for IDunite, dictUnite in dictGroupe.items() :
            #    if IDunite not in listeUnitesUtilises :
            #        listeUnitesUtilises.append(IDunite)
                for regroupement, valeur in dictUnite.items() :
                    if regroupement not in listeRegroupement :
                        listeRegroupement.append(regroupement)
                    # Calcul des totaux
                    if ((IDgroupe, IDunite) in dictTotaux["lignes"]) == False :
                        dictTotaux["lignes"][(IDgroupe, IDunite)] = defaut
                    dictTotaux["lignes"][(IDgroupe, IDunite)] += valeur
                    if (regroupement in dictTotaux["colonnes"]) == False :
                        dictTotaux["colonnes"][regroupement] = defaut
                    dictTotaux["colonnes"][regroupement] += valeur
        
        # Création des colonnes
        largeur_colonne = 80
        dictColonnes = {}
        if self.detail_groupes == True :
            index = 0
            for idGroupe, lstUnites in listeColonnes:
                self.AppendCols(len(lstUnites) )
                for idUnite in lstUnites:
                    self.SetColSize(index, largeur_colonne)
                    for id, abregeGroupe in listeGroupes:
                        if id == idGroupe : libGroupe = abregeGroupe
                    for id, abregeUnite in listeUnites:
                        if id == idUnite : libUnite = abregeUnite
                    self.SetColLabelValue(index, "%s\n%s" % (libGroupe, libUnite))
                    dictColonnes[(idGroupe, idUnite)] = index
                    index += 1
        else :
            self.AppendCols(len(listeUnites))
            index = 0
            for IDunite, nomUnite in listeUnites :
                self.SetColSize(index, largeur_colonne)
                self.SetColLabelValue(index, "%s" % nomUnite)
                dictColonnes[(None, IDunite)] = index
                index += 1
        
        # Colonne Total
        self.AppendCols(1)
        self.SetColSize(index, largeur_colonne)
        self.SetColLabelValue(index, _("TOTAL"))
        dictColonnes["total"] = index

        # Création des lignes
        listeRegroupement.sort()
        self.AppendRows(len(listeRegroupement))
        
        index = 0
        dictLignes = {}
        for regroupement in listeRegroupement :
            if self.affichage_regroupement == "jour" : 
                label = DateComplete(regroupement)
            elif self.affichage_regroupement == "mois" : 
                label = FormateMois(regroupement)
            elif self.affichage_regroupement == "annee" : 
                label = str(regroupement)
            else :
                label = str(regroupement)
            
            self.SetRowLabelValue(index, label)
            self.SetRowSize(index, 30)
            dictLignes[regroupement] = index
            index += 1
        
        # Ligne Total
        self.AppendRows(1)
        self.SetRowLabelValue(index, _("TOTAL"))
        self.SetRowSize(index, 30)
        dictLignes["total"] = index

        # Remplissage des valeurs
        for IDgroupe, dictGroupe in dictResultats.items() :
            for IDunite, dictUnite in dictGroupe.items() :
                for regroupement, valeur in dictUnite.items() :
                    label = FormateValeur(valeur, self.affichage_donnees)
                    numLigne = dictLignes[regroupement]
                    numColonne = dictColonnes[(IDgroupe, IDunite)]
                    self.SetCellValue(numLigne, numColonne, label)
                    self.SetCellAlignment(numLigne, numColonne, wx.ALIGN_CENTRE, wx.ALIGN_CENTRE)
                    self.SetReadOnly(numLigne, numColonne, True)
        
        # Remplissage des totaux        
        for (IDgroupe, IDunite), valeur in dictTotaux["lignes"].items() :
            label = FormateValeur(valeur, self.affichage_donnees)
            numLigne = dictLignes["total"]
            numColonne = dictColonnes[(IDgroupe, IDunite)]
            self.SetCellValue(numLigne, numColonne, label)
            self.SetCellAlignment(numLigne, numColonne, wx.ALIGN_CENTRE, wx.ALIGN_CENTRE)
            self.SetReadOnly(numLigne, numColonne, True)
        
        total_general = defaut
        for regroupement, valeur in dictTotaux["colonnes"].items() :
            total_general += valeur
            label = FormateValeur(valeur, self.affichage_donnees)
            numLigne = dictLignes[regroupement]
            numColonne = dictColonnes["total"]
            self.SetCellValue(numLigne, numColonne, label)
            self.SetCellAlignment(numLigne, numColonne, wx.ALIGN_CENTRE, wx.ALIGN_CENTRE)
            self.SetReadOnly(numLigne, numColonne, True)
        
        # Total général
        label = FormateValeur(total_general, self.affichage_donnees)
        numLigne = dictLignes["total"]
        numColonne = dictColonnes["total"]
        self.SetCellValue(numLigne, numColonne, label)
        self.SetCellAlignment(numLigne, numColonne, wx.ALIGN_CENTRE, wx.ALIGN_CENTRE)
        self.SetReadOnly(numLigne, numColonne, True)
        
        # Coloration des TOTAUX
        couleurFond = (240, 240, 240)
        for x in range(0, numLigne+1):
            self.SetCellBackgroundColour(x, numColonne, couleurFond)
        for y in range(0, numColonne):
            self.SetCellBackgroundColour(numLigne, y, couleurFond)
                
    def Apercu(self):
        """ Impression tableau de données """
        if self.GetNumberRows() == 0 or self.GetNumberCols() == 0 :
            dlg = wx.MessageDialog(self, _("Il n'y a rien à imprimer !"), "Erreur", wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return None

        avecCouleurs = True
        
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

        def ConvertCouleur(couleur):
            r, g, b = couleur
            return r/255.0, g/255.0, b/255.0
        
        # Récupération des données du tableau
        tableau = self
        nbreColonnes = tableau.GetNumberCols()
        nbreLignes = tableau.GetNumberRows()
        
        # Initialisation du tableau
        story = []
        dataTableau = []
        listeCouleurs = []
        
        # Création des colonnes
        largeursColonnes = []
        largeurColonne = 33
        largeurColonneLabel = 90
        for col in range(0, nbreColonnes+1) :
            if col == 0 : largeursColonnes.append(largeurColonneLabel)
            else: largeursColonnes.append(largeurColonne)
        
        listeStyles = [
                            ('GRID', (0,0), (-1,-1), 0.25, colors.black), # Crée la bordure noire pour tout le tableau
                            ('VALIGN', (0, 0), (-1,-1), 'MIDDLE'), # Centre verticalement toutes les cases
                            ('ALIGN', (0, 0), (-1, 0), 'CENTRE'), # Centre les labels de colonne
                            ('ALIGN', (1, 1), (-1,- 1), 'CENTRE'), # Valeurs à gauche
                            ('ALIGN', (0, 1), (0, -1), 'CENTRE'), # Colonne Label Ligne centrée
                            ('FONT',(0, 0),(-1,-1), "Helvetica", 6), # Donne la police de caract. + taille de police de la ligne de total
                            ('FONT',(0, 0),(-1,0), "Helvetica-Bold", 6), # Donne la police de caract. + taille de police de la ligne de total
                            ]
        
        # Création de l'entete
        valeursLigne = ["",]
        for numColonne in range(0, nbreColonnes) :
            labelColonne = tableau.GetColLabelValue(numColonne)
            valeursLigne.append(labelColonne)
        dataTableau.append(valeursLigne)
        
        # Création des lignes
        for numLigne in range(0, nbreLignes) :
            labelLigne = tableau.GetRowLabelValue(numLigne)
            valeursLigne = [labelLigne,]
            for numCol in range(0, nbreColonnes) :
                valeurCase = tableau.GetCellValue(numLigne, numCol)
                couleurCase = tableau.GetCellBackgroundColour(numLigne, numCol)
                if couleurCase != (255, 255, 255, 255) and avecCouleurs == True :
                    r, g, b = ConvertCouleur(couleurCase)
                    listeStyles.append( ('BACKGROUND', (numCol+1, numLigne+1), (numCol+1, numLigne+1), (r, g, b) ) )
                if numLigne == 0 :
                    valeurCase = valeurCase.replace(" ", "\n")
                valeursLigne.append(valeurCase)
            dataTableau.append(valeursLigne)
    
        # Style du tableau
        style = TableStyle(listeStyles)
        
        # Création du tableau
        tableau = Table(dataTableau, largeursColonnes,  hAlign='LEFT')
        tableau.setStyle(style)
        story.append(tableau)
        story.append(Spacer(0,20))
        
        # Calcul du format de la page
        tailleMarge = 20
        if sum(largeursColonnes) > A4[0] - (tailleMarge*2) :
            hauteur, largeur = A4
        else :
            largeur, hauteur = A4

        # Création du titre du document
        dataTableau = []
        largeurContenu = largeur - (tailleMarge*2)
        largeursColonnes = ( (largeurContenu-100, 100) )
        dateDuJour = DateEngFr(str(datetime.date.today()))
        dataTableau.append( (_("Synthèse des consommations"), _("%s\nEdité le %s") % (UTILS_Organisateur.GetNom(), dateDuJour)) )
        style = TableStyle([
                ('BOX', (0,0), (-1,-1), 0.25, colors.black), 
                ('VALIGN', (0,0), (-1,-1), 'TOP'), 
                ('ALIGN', (0,0), (0,0), 'LEFT'), 
                ('FONT',(0,0),(0,0), "Helvetica-Bold", 16), 
                ('ALIGN', (1,0), (1,0), 'RIGHT'), 
                ('FONT',(1,0),(1,0), "Helvetica", 6), 
                ])
        tableau = Table(dataTableau, largeursColonnes)
        tableau.setStyle(style)
        story.insert(0, tableau)
        story.insert(1, Spacer(0, 10))       
        
        # Insertion du label Paramètres
        styleA = ParagraphStyle(name="A", fontName="Helvetica", fontSize=6, spaceAfter=20)
        story.insert(2, Paragraph(self.labelParametres, styleA))       

        # Enregistrement du PDF
        nomFichier = "Synthese_conso_%s.pdf" % FonctionsPerso.GenerationIDdoc()
        nomDoc = UTILS_Fichiers.GetRepTemp(nomFichier)


        if sys.platform.startswith("win") : nomDoc = nomDoc.replace("/", "\\")
        doc = SimpleDocTemplate(nomDoc, pagesize=(largeur, hauteur), leftMargin=tailleMarge, rightMargin=tailleMarge, topMargin=tailleMarge, bottomMargin=tailleMarge)
        doc.build(story)
        
        # Affichage du PDF
        FonctionsPerso.LanceFichierExterne(nomDoc)

    def ExportTexte(self, event=None):
        from Utils import UTILS_Export
        UTILS_Export.ExportTexte(grid=self, titre=_("Synthèse des consommations"))
        
    def ExportExcel(self, event=None):
        from Utils import UTILS_Export
        UTILS_Export.ExportExcel(grid=self, titre=_("Synthèse des consommations"))


# -------------------------------------------------------------------------------------------------------------------------------------------

class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self, -1)
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_1.Add(panel, 1, wx.ALL|wx.EXPAND)
        self.SetSizer(sizer_1)
        self.grille = CTRL(panel)
        self.grille.MAJ(IDactivite=32, date_debut=datetime.date(2015, 11, 1), date_fin=datetime.date(2015, 12, 20), listeGroupes=[41,],
                                detail_groupes=False, affichage_donnees="quantite", affichage_regroupement="etiquette") 
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_2.Add(self.grille, 1, wx.EXPAND, 0)
        panel.SetSizer(sizer_2)
        self.SetSize((750, 400))
        self.Layout()
        
        

if __name__ == '__main__':
    app = wx.App(0)
    #wx.InitAllImageHandlers()
    frame_1 = MyFrame(None, -1, "TEST", name="test")
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()
