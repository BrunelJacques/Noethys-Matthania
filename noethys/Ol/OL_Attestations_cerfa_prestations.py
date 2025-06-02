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
import GestionDB
import datetime
from Ctrl.CTRL_ObjectListView import ObjectListView, ColumnDefn, CTRL_Outils, PanelAvecFooter

from Utils.UTILS_Decimal import FloatToDecimal as FloatToDecimal
from Utils import UTILS_Config

SYMBOLE = UTILS_Config.GetParametre("monnaie_symbole", "€")

def DateEngEnDateDD(dateEng):
    if dateEng == None : return datetime.date(1900, 1, 1)
    return datetime.date(int(dateEng[:4]), int(dateEng[5:7]), int(dateEng[8:10]))

def DateEngFr(textDate):
    if textDate == None: return ""
    textDate = str(textDate)
    text = str(textDate[8:10]) + "/" + str(textDate[5:7]) + "/" + str(textDate[:4])
    return text

def FmtEnt(montant):
    # Convert the given montant into a string with zero null
    if montant != 0:
        val = "%.0f" % (montant)
        val = ("    " + val)[-4:]
        return val
    else:
        return "    "

class Track(object):
    def __init__(self, dictValeurs):
        lstChamps = [
                    "IDprestation",
                    "IDfamille",
                    "labelDon",
                    "payeurs",
                    "montantDon",
                    "montantDonHors",
                    "montantRegleHors",
                    "regul",
                    "montantRegle",
                    "debut",
                    "fin",
                    "designation",
                    "mail_famille",
                    "nomPrenom",
                    "origine",
                    "rue_resid",
                    "cp_resid",
                    "ville_resid",
                    "dateDon",
                    "listeIDreglements",
                    "listeIDlignes",
                    "labelModeRegl",
                    ]

        for champ in lstChamps:
            action = "self.%s = dictValeurs[%s]" %(champ,"'"+champ+"'")
            try:
                setattr(self, "%s"%champ, dictValeurs["%s"% champ])
            except:
                wx.MessageBox("Erreur try in 'cerfa_prestations.Track' : %s"%action)

class ListView(ObjectListView):
    def __init__(self, *args, **kwds):
        ObjectListView.__init__(self, *args, **kwds)
        #self.SetShowGroups(False)

        # Variables
        self.date_debut = None
        self.date_fin = None
        self.listeModes = []
        # Binds perso
        self.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OuvrirFicheFamille)

    def GetTracks(self):
        """ Récupération des données """

        # Récupération des conditions
        if len(self.listeModes) == 0 : conditionModes = "()"
        elif len(self.listeModes) == 1 : conditionModes = "(%d)" % self.listeModes[0]
        else : conditionModes = str(tuple(self.listeModes))
            
        # Appel des prestations puis des factures
        DB = GestionDB.DB()
        lstPrestations = []
        lstDons = []
        dtDebSql = "%s"%str(self.date_debut)
        dtFinSql = "%s"%str(self.date_fin)
        if self.prestations:
            # Recherche des prestations et de leur règlement ventilé
            # IF(cond,val-oui,val-non) remplacé par CASE (colonne) THEN cond THEN val-oui ELSE val-non END
            reqPrest = """
                SELECT prestations.IDprestation,0,prestations.label,prestations.IDcompte_payeur,
                        prestations.date, prestations.montant,'PREST'
                FROM ((prestations
                    LEFT JOIN ventilation ON prestations.IDprestation = ventilation.IDprestation)
                    LEFT JOIN reglements ON ventilation.IDreglement = reglements.IDreglement)
                    LEFT JOIN matCerfasLignes ON prestations.IDprestation = matCerfasLignes.crlIDprestation
                WHERE
                    (prestations.categorie = '%s')
                    AND ( ( (prestations.date >= '%s')
                            AND (prestations.date <='%s'))
                          OR(
                            (reglements.date>='%s')
                             And (reglements.date <='%s')
                             And (reglements.montant >0)
                            ))
                    AND (matCerfasLignes.crlIDcerfa Is Null)
                GROUP BY prestations.IDprestation,prestations.label,prestations.IDcompte_payeur,
                        prestations.date, prestations.montant
                ;"""%("%s"%("don"),dtDebSql, dtFinSql,dtDebSql, dtFinSql)

            ret = DB.ExecuterReq(reqPrest,MsgBox="OL_Attestations_cerfa_prestations")
            lstPrestations = DB.ResultatReq()

        if self.factures:
            # Recherche des lignes de pièce de type don... et leur réglement
            reqFact = """
                SELECT prestations.IDprestation, matPiecesLignes.ligIDnumLigne, matPiecesLignes.ligLibelle, 
                        prestations.IDcompte_payeur, matPieces.pieDateFacturation, matPiecesLignes.ligMontant,'FAC'
                FROM (((((matPiecesLignes
                    INNER JOIN matPieces ON matPiecesLignes.ligIDnumPiece = matPieces.pieIDnumPiece)
                    LEFT JOIN prestations ON matPieces.pieIDprestation = prestations.IDprestation)
                    LEFT JOIN ventilation ON prestations.IDprestation = ventilation.IDprestation)
                    LEFT JOIN reglements ON ventilation.IDreglement = reglements.IDreglement)
                    LEFT JOIN matArticles ON matPiecesLignes.ligCodeArticle = matArticles.artCodeArticle)
                    LEFT JOIN matCerfasLignes ON matPiecesLignes.ligIDnumLigne = matCerfasLignes.crlIDligne
                WHERE 
                    (matArticles.artCodeComptable LIKE'%s')
                    AND (matPieces.pieNature = 'FAC')
                    AND (  ((matPieces.pieDateFacturation >= '%s')
                             And (matPieces.pieDateFacturation <='%s'))
                        OR ((reglements.Date >='%s')
                             And (reglements.Date <= '%s')
                             And (reglements.montant >0)
                             And (reglements.IDmode in %s))
                        )
                    AND (matCerfasLignes.crlIDcerfa Is Null)
                GROUP BY prestations.IDprestation, matPiecesLignes.ligIDnumLigne, matPiecesLignes.ligLibelle, 
                        prestations.IDcompte_payeur, matPieces.pieDateFacturation, matPiecesLignes.ligMontant
                ;"""% ("%s%%%%"%("DON"),dtDebSql, dtFinSql, dtDebSql, dtFinSql, conditionModes)

            ret = DB.ExecuterReq(reqFact,MsgBox="OL_Attestations_cerfa_lignesFactures")
            lstDons = DB.ResultatReq()

        # Fusion des deux origines
        lstDons += lstPrestations

        # appel des règlements
        lstIdPrest = [ x[0] for x in lstDons]
        reqRegl = """
            SELECT prestations.IDprestation,SUM(reglements.montant), modes_reglements.label,
                    payeurs.nom, reglements.date, reglements.IDreglement
            FROM (((prestations
                    INNER JOIN ventilation ON prestations.IDprestation = ventilation.IDprestation)
                    INNER JOIN reglements ON ventilation.IDreglement = reglements.IDreglement)
                    INNER JOIN modes_reglements ON reglements.IDmode = modes_reglements.IDmode)
                    LEFT JOIN payeurs ON reglements.IDpayeur = payeurs.IDpayeur
            WHERE
                prestations.IDprestation IN (%s)
                AND (reglements.montant > 0)
                AND (reglements.IDmode in %s)
            GROUP BY prestations.IDprestation, modes_reglements.label, payeurs.nom, reglements.date,
                    reglements.IDreglement
            ;""" % (str(lstIdPrest)[1:-1], conditionModes)

        ret = DB.ExecuterReq(reqRegl, MsgBox="OL_Attestations_cerfa_lignesRèglements")
        lstReglements = DB.ResultatReq()

        dictDons = {}
        lstIDfamilles = []        

        # Déroulé des lignes de don, constitution d'un dictionnaire de dons avec clé IDprestation
        for IDprestation, IDligne, labelDon, IDfamille, dateDon, montantDon, origine in lstDons:
            if IDfamille not in lstIDfamilles :
                lstIDfamilles.append(IDfamille) 

            montantDonHors = FloatToDecimal((0.0))
            if (dateDon < dtDebSql) or (dateDon > dtFinSql):
                montantDonHors = FloatToDecimal(montantDon)
                montantDon = FloatToDecimal(0.0)

            if (IDprestation in dictDons) == False :
                dictDons[IDprestation] = {
                    "IDprestation": IDprestation,
                    "IDfamille" : IDfamille,
                    "origine"   : "%s"%origine ,
                    "dateDon":dateDon,
                    "labelDon" : "",
                    "montantDon" : FloatToDecimal(0.0),
                    "montantDonHors" : FloatToDecimal(0.0),
                    "montantRegleHors" : FloatToDecimal(0.0),
                    "regul": FloatToDecimal(0.0),

                    "payeurs" : "",
                    "debut" : None,
                    "fin"   : None,
                    "montantRegle" : FloatToDecimal(0.0),
                    "listeIDreglements": [],
                    "listeIDlignes": [],
                    "labelModeRegl": "",

                    "nom": "",
                }
            dictDons[IDprestation]["montantDon"] += FloatToDecimal(montantDon)
            dictDons[IDprestation]["montantDonHors"] += FloatToDecimal(montantDonHors)
            dictDons[IDprestation]["labelDon"] += (labelDon +(", " ))
            dictDons[IDprestation]["listeIDlignes"].append(int(IDligne))

        # enrichissement des informations de règlement
        for  IDprestation, montantRegl,labelModeRegl,nomPayeur,dateRegl,IDreglement in lstReglements :
            dic = dictDons[IDprestation]
            if montantRegl == None :
                montantRegl = FloatToDecimal(0.0)
                (labelModeRegl, nomPayeur) = ("","",)

            if (dateRegl < dtDebSql) or (dateRegl > dtFinSql):
                dic["montantRegleHors"] += FloatToDecimal(montantRegl)
                montantRegl = FloatToDecimal(0.0)

            # Mémorisation du don en regroupant les ventilations, payeurs et mode de règlement
            dic["montantRegle"] = min((dic["montantDon"]+dic["montantDonHors"]), dic["montantRegle"]+FloatToDecimal(montantRegl))

            # le mot nature dans le label est prioritaire sur le préfixe
            if "nature" in labelModeRegl.lower():
                labelModeRegl = "Nature"

            if not labelModeRegl[:3] in dic["labelModeRegl"]:
                dic["labelModeRegl"] += (labelModeRegl[:3]+",")
            dic["listeIDreglements"].append(IDreglement)

            if not dic["debut"] : dic["debut"] = dateRegl
            if not dic["fin"] : dic["fin"] = dateRegl

            if nomPayeur and nomPayeur not in dic["payeurs"]:
                dic["payeurs"]+= nomPayeur + ", "
            if dateRegl < dic["debut"]:
                dic["debut"] = dateRegl
            if dateRegl > dic["fin"]:
                dic["fin"]=dateRegl


        # recherche des noms des titulaires
        req = """
            SELECT familles.IDfamille, familles.adresse_intitule,individus.mail, individus.nom, individus.prenom,
                    individus.rue_resid, individus.cp_resid, individus.ville_resid, 
                    individus.adresse_auto, individus_1.rue_resid, individus_1.cp_resid, individus_1.ville_resid
            FROM familles 
                LEFT JOIN ( individus 
                            LEFT JOIN individus AS individus_1 ON individus.adresse_auto = individus_1.IDindividu) 
                ON familles.adresse_individu = individus.IDindividu
            WHERE familles.IDfamille In (%s)
            GROUP BY familles.IDfamille, familles.adresse_intitule,individus.mail, individus.rue_resid, 
                    individus.cp_resid, individus.ville_resid, individus.adresse_auto, individus_1.rue_resid, 
                    individus_1.cp_resid, individus_1.ville_resid;
			""" % str(lstIDfamilles)[1:-1]
        ok = DB.ExecuterReq(req,MsgBox="OL_Attestations_cerfa_famille")
        listeFamilles = DB.ResultatReq()
        DB.Close()
        dictFamilles = {}

        # gestion de l'adresse de la famille avec son nom commun de désignation
        for IDfamille, designation, mail_famille, nom, prenom, rue_resid, cp_resid, ville_resid, adresse_auto, rue_resid_1, \
            cp_resid_1, ville_resid_1 in listeFamilles:
            dictFamilles[IDfamille] = {}
            dictFamilles[IDfamille]["nomPrenom"] = "%s %s"%(nom,prenom)
            dictFamilles[IDfamille]["designation"] = "%s"%(designation)
            dictFamilles[IDfamille]["mail_famille"] = mail_famille
            if adresse_auto == None:
                dictFamilles[IDfamille]["rue_resid"] = rue_resid
                dictFamilles[IDfamille]["cp_resid"] = cp_resid
                dictFamilles[IDfamille]["ville_resid"] = ville_resid
            else:
                dictFamilles[IDfamille]["rue_resid"] = rue_resid_1
                dictFamilles[IDfamille]["cp_resid"] = cp_resid_1
                dictFamilles[IDfamille]["ville_resid"] = ville_resid_1

        # Composition des champs complexes et mise en track dans listview
        listeListeView = []
        for ID,dictValeurs in dictDons.items() :
            # Composition de l'adrese
            dictValeurs["designation"] = dictFamilles[dictValeurs["IDfamille"]]["designation"]
            dictValeurs["mail_famille"] = dictFamilles[dictValeurs["IDfamille"]]["mail_famille"]
            dictValeurs["nomPrenom"] = dictFamilles[dictValeurs["IDfamille"]]["nomPrenom"]
            dictValeurs["rue_resid"] = dictFamilles[dictValeurs["IDfamille"]]["rue_resid"]
            dictValeurs["cp_resid"] = dictFamilles[dictValeurs["IDfamille"]]["cp_resid"]
            dictValeurs["ville_resid"] = dictFamilles[dictValeurs["IDfamille"]]["ville_resid"]
            # composition du non réglé
            dictValeurs["regul"]= dictValeurs["montantDonHors"] + dictValeurs["montantRegleHors"]
            if dictValeurs["regul"] < 0.0 : dictValeurs["regul"] = 0.0

            nonregle = dictValeurs["montantDon"] - dictValeurs["montantRegle"]
            if nonregle > 0 : dictValeurs["regul"] += nonregle

            if dictValeurs["origine"] == "FAC":
                if dictValeurs["montantRegle"] > (dictValeurs["montantDon"] + dictValeurs["montantDonHors"]):
                        dictValeurs["montantRegle"] = (dictValeurs["montantDon"] + dictValeurs["montantDonHors"])

            track = Track(dictValeurs)
            listeListeView.append(track)
        return listeListeView

    def InitObjectListView(self):

        def FormateMontant(montant):
            if montant == None or montant == "" : return ""
            return "%.2f %s" % (montant, SYMBOLE)

        def FormateDateDD(dateDD):
            if dateDD == None : return ""
            return DateEngFr(str(dateDD))

        def rowFormatter(listItem, track):
            if track.montantDon > track.montantRegle :
                listItem.SetTextColour(wx.Colour(0, 200,200))
            if track.montantDon < track.montantRegle :
                listItem.SetTextColour(wx.Colour(200, 0,200))
            if track.montantDon <= 1:
                listItem.SetTextColour(wx.Colour(200,200, 0))

        # Couleur en alternance des lignes
        self.oddRowsBackColor = "#F0FBED" 
        self.evenRowsBackColor = wx.Colour(255,  255, 255)
        self.useExpansionColumn = True
        #lst ["IDdon","IDfamille","labelDon","labelModeRegl","payeurs","montantDon","montantRegleHors","montantRegle","debut","fin", "nomPrenom",]

        # Définition des colonnes
        liste_Colonnes = [
            ColumnDefn(_("Prestation"), 'right', 0, "IDprestation", typeDonnee="entier"),
            ColumnDefn(_("IDfamille"), 'right',40, "IDfamille", typeDonnee="entier"),
            ColumnDefn(_("Famille"), 'left', 130, "designation", typeDonnee="texte"),
            ColumnDefn(_("Correspondant"), 'left', 130, "nomPrenom", typeDonnee="texte"),
            ColumnDefn(_("Mail"), 'left', 80, "mail_famille", typeDonnee="texte"),
            ColumnDefn(_("Payeurs"), 'left', 100, "payeurs", typeDonnee="texte"),
            ColumnDefn(_("Description"), "left", 120, "labelDon", typeDonnee="texte"),
            ColumnDefn(_("Montant"), "right", 70, "montantDon", typeDonnee="montant", stringConverter=FormateMontant),
            ColumnDefn(_("DateDon"), "left", 80, "dateDon", typeDonnee="date",stringConverter=FormateDateDD),
            ColumnDefn(_("HorsPériode"), "right", 60, "regul", typeDonnee="montant",stringConverter=FormateMontant),
            ColumnDefn(_("Réglé"), "right", 60, "montantRegle", typeDonnee="montant",stringConverter=FormateMontant),
            ColumnDefn(_("du"), "centre", 80, "debut", typeDonnee="date", stringConverter=FormateDateDD),
            ColumnDefn(_("au"), "centre", 80, "fin", typeDonnee="date", stringConverter=FormateDateDD),
            ColumnDefn(_("ModeRegl."), "left", 50, "labelModeRegl", typeDonnee="texte"),
            ColumnDefn(_("Origine"), "left", 50, "origine", typeDonnee="texte"),
            ColumnDefn(_("Rue"), "left", 80, "rue_resid", typeDonnee="texte"),
            ColumnDefn(_("Cp"), "left", 50, "cp_resid", typeDonnee="texte"),
            ColumnDefn(_("Ville"), "left", 80, "ville_resid", typeDonnee="texte"),
            ]
        self.SetColumns(liste_Colonnes)
        self.CreateCheckStateColumn(0)
        self.rowFormatter = rowFormatter

        self.SetEmptyListMsg(_("Aucun don sur la période"))
        self.SetEmptyListMsgFont(wx.FFont(11, wx.DEFAULT, faceName="Tekton"))
        self.SetSortColumn(self.columns[4])
        self.SetObjects(self.donnees)

    def MAJ(self, date_debut=None, date_fin=None, listeModes=[],prestFact=(True,True)):
        self.prestations,self.factures = prestFact
        self.date_debut = date_debut
        self.date_fin = date_fin
        self.listeModes = listeModes
        self.donnees = self.GetTracks()
        self.InitObjectListView()
        self._ResizeSpaceFillingColumns()
        for track in self.GetObjects():
            if track.montantDon == track.montantRegle and abs(track.montantDon) >= 3:
                self.Check(track)
                self.RefreshObject(track)

    def Selection(self):
        return self.GetSelectedObjects()

    def GetTracksCoches(self):
        return self.GetCheckedObjects()

    def OnContextMenu(self, event):
        """Ouverture du menu contextuel """            
        # Création du menu contextuel
        menuPop = wx.Menu()
                
        # Tout sélectionner
        item = wx.MenuItem(menuPop, 20, _("Tout cocher"))
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.CocheListeTout, id=20)

        # Tout dé-sélectionner
        item = wx.MenuItem(menuPop, 21, _("Tout décocher"))
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.CocheListeRien, id=21)

        # Inverser
        item = wx.MenuItem(menuPop, 22, _("Inverser jusqu'à sélection"))
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.CocheJusqua, id=22)

        menuPop.AppendSeparator()

        # Appel de la famille
        item = wx.MenuItem(menuPop, 30, _("Accéder à la famille"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Famille.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.OuvrirFicheFamille, id=30)

        menuPop.AppendSeparator()

        # Apercu avant impression
        item = wx.MenuItem(menuPop, 40, _("Aperçu avant impression"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Apercu.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.Apercu, id=40)
        
        # Imprimer
        item = wx.MenuItem(menuPop, 50, _("Imprimer"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Imprimante.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.Imprimer, id=50)
        
        menuPop.AppendSeparator()
    
        # Export Texte
        item = wx.MenuItem(menuPop, 600, _("Exporter au format Texte"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Texte2.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.ExportTexte, id=600)
        
        # Export Excel
        item = wx.MenuItem(menuPop, 700, _("Exporter au format Excel"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Excel.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.ExportExcel, id=700)

        self.PopupMenu(menuPop)
        menuPop.Destroy()

    def Impression(self, mode="preview"):
        if self.donnees == None or len(self.donnees) == 0 :
            dlg = wx.MessageDialog(self, _("Il n'y a aucune donnée à imprimer !"), _("Erreur"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        from Utils import UTILS_Printer
        prt = UTILS_Printer.ObjectListViewPrinter(self, titre=_("Liste des dons"), intro="", total="", format="A", orientation=wx.LANDSCAPE)
        if mode == "preview" :
            prt.Preview()
        else:
            prt.Print()
        
    def Apercu(self, event):
        self.Impression("preview")

    def Imprimer(self, event):
        self.Impression("print")

    def OuvrirFicheFamille(self,event):
        # Ouverture de la fiche famille
        if len(self.Selection()) == 0 :
            dlg = wx.MessageDialog(self, _("Vous n'avez sélectionné aucune fiche famille à ouvrir !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        IDfamille = self.Selection()[0].IDfamille
        from Dlg import DLG_Famille
        dlg = DLG_Famille.Dialog(self, IDfamille)
        if dlg.ShowModal() == wx.ID_OK:
            self.MAJ()
        dlg.Destroy()

    def ExportTexte(self, event):
        from Utils import UTILS_Export
        UTILS_Export.ExportTexte(self, titre=_("Liste des dons"))
        
    def ExportExcel(self, event):
        from Utils import UTILS_Export
        UTILS_Export.ExportExcel(self, titre=_("Liste des dons"))

# -------------------------------------------------------------------------------------------------------------------------------------------

class ListviewAvecFooter(PanelAvecFooter):
    def __init__(self, parent, kwargs={}):
        dictColonnes = {
            "nomPrenom" : {"mode" : "nombre", "singulier" : _("famille"), "pluriel" : _("familles"), "alignement" : wx.ALIGN_CENTER},
            "montantDon" : {"mode" : "total"},
            }
        PanelAvecFooter.__init__(self, parent, ListView, kwargs, dictColonnes)

# -------------------------------------------------------------------------------------------------------------------------------------------

class MyFrame(wx.Frame):
    def __init__(self, parent):
        wx.Frame.__init__(self, parent, -1)
        panel = wx.Panel(self, -1, name="test1")
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_1.Add(panel, 1, wx.ALL|wx.EXPAND)
        self.SetSizer(sizer_1)
        self.myOlv = ListView(panel, id=-1, name="OL_test", style=wx.LC_REPORT|wx.SUNKEN_BORDER|wx.LC_SINGLE_SEL|wx.LC_HRULES|wx.LC_VRULES)
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_2.Add(self.myOlv, 1, wx.ALL|wx.EXPAND, 4)
        panel.SetSizer(sizer_2)
        self.Layout()

if __name__ == '__main__':
    app = wx.App(0)
    #wx.InitAllImageHandlers()
    frame_1 = MyFrame(None)
    frame_1.SetSize((900, 500))
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()
