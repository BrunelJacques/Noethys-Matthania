#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
# -----------------------------------------------------------
# Application :    Noethys, Matthania
# Auteur:          Ivan LUCAS, JB, Jacques Brunel
# Ecran de tarification derrière une inscription en cours
#  Derive de DLG_Appliquer_forfait.py
# -----------------------------------------------------------

import Chemins
import wx
import datetime
from operator import attrgetter
import wx.lib.agw.hyperlink as Hyperlink
from Ctrl.CTRL_ObjectListView import FastObjectListView, ColumnDefn, CTRL_Outils
import Olv.Filter as Filter
import copy
from Ctrl import CTRL_Bouton_image
from Ctrl import CTRL_Bandeau
from Utils import UTILS_Config
from Utils import UTILS_Utilisateurs
import GestionDB
from Dlg import DLG_ChoixLigne
from Dlg import DLG_ChoixTypePiece
from Gest import GestionArticle

from Utils.UTILS_Decimal import FloatToDecimal as FloatToDecimal

SYMBOLE = UTILS_Config.GetParametre("monnaie_symbole", "€")

def Fmt2d(montant):
    # Convert the given montant into a string with zero null
    if montant != 0:
        return "%.2f" % (montant)
    else:
        return " "

def FmtXd(montant):
    # Convert the given montant into décimales variables
    fmt = "%.4f" % montant
    if (1000*montant) % 1 < 0.01: fmt = "%.3f" % montant
    if (100*montant) % 1 < 0.001: fmt = "%.2f" % montant
    if (10*montant) % 1 < 0.0001: fmt = "%.1f" % montant
    if (montant) % 1 < 0.00001: fmt = "%.0f" % montant
    if montant == 0: fmt = " "
    return fmt

class Track(object):
    def __init__(self, track):
        self.codeArticle = track["codeArticle"]
        self.libelle =  track["libelle"]
        self.prix1 = track["prix1"]
        self.prix2 = track["prix2"]
        self.typeLigne = track["typeLigne"]
        self.condition = track["condition"]
        self.modeCalcul = track["modeCalcul"]
        self.force = track["force"]
        self.ordre = track["ordre"]
        if track["origine"] == "articles":
            #ChampsTrack = ["codeArticle", "libelle", "prix1", "prix2", "typeLigne", "conditions", "modeCalcul", "force"]
            self.qte = 1
            montant = 0
            self.prixUnit = track["prix1"]
            self.saisie = False
        if track["origine"] == "lignes":
            #listeChamps=["codeArticle","libelle","quantite","prixUnit","montant"]
            #liste2=["prix2", "typeLigne", "condition", "modeCalcul", "force"]
            self.prixUnit = track["prixUnit"]
            self.qte =  track["quantite"]
            self.saisie = True
            montant =  track["montant"]
        if self.prixUnit == None: self.prixUnit = 0
        if self.qte == None: self.qte = 0
        self.montantCalcul = self.prixUnit * self.qte
        if montant == None: montant = 0
        self.montant = float(montant)
        self.qte = float(self.qte)
        if self.montant == self.qte * self.prixUnit:
            self.montant = 0.00
            self.saisie = False

class CTRL_Solde(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, id=-1, name="panel_solde", style=wx.SUNKEN_BORDER | wx.TAB_TRAVERSAL,
                          size=(100, 40))
        self.parent = parent
        self.value = 0.0
        # Solde du compte
        self.ctrl_solde = wx.StaticText(self, -1, "0.00 %s " % SYMBOLE)
        font = wx.Font(11, wx.SWISS, wx.NORMAL, wx.BOLD)
        self.ctrl_solde.SetFont(font)

        # Layout
        grid_sizer_base = wx.FlexGridSizer(rows=1, cols=1, vgap=5, hgap=5)
        grid_sizer_base.Add(self.ctrl_solde, 1, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL | wx.ALL, 10)
        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)
        grid_sizer_base.AddGrowableCol(0)
        grid_sizer_base.AddGrowableRow(0)
        # self.SetToolTip(u"Solde")
        self.ctrl_solde.SetToolTip("Solde")

    def SetSolde(self, montant=FloatToDecimal(0.0)):
        """ MAJ integrale du controle avec MAJ des donnees """
        if montant > FloatToDecimal(0.0):
            label = "+ %.2f %s" % (montant, SYMBOLE)
            self.SetBackgroundColour("#C4BCFC")  # Bleu
        elif montant == FloatToDecimal(0.0):
            label = "0.00 %s" % SYMBOLE
            self.SetBackgroundColour("#5DF020")  # Vert
        else:
            label = "- %.2f %s" % (-montant, SYMBOLE)
            self.SetBackgroundColour("#F81515")  # Rouge
        self.ctrl_solde.SetLabel(label)
        self.value = montant
        self.Layout()
        self.Refresh()

# ---Gestion écran tarification --------------------------------------------------------------
class OLVtarification(FastObjectListView):
    def __init__(self,parent,dictDonnees,*args, **kwds):
        self.parent = parent
        self.dictDonnees = dictDonnees
        self.objectSelected = None
        FastObjectListView.__init__(self, parent, *args, **kwds)
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("familles_factures", "creer") == False :
            GestionDB.MessageBox(self,"Vous n'avez pas les droits pour créer des factures")
            self.cellEditMode = FastObjectListView.CELLEDIT_NONE
        else :
            self.cellEditMode = FastObjectListView.CELLEDIT_SINGLECLICK
        self.listeChampsTrack = ["codeArticle", "libelle", "montant", "prix1", "prix2", "typeLigne", "condition", "modeCalcul","force"]

        # pour ajouter l'ordre les lignes dans les tracks et trier pour les calculs
        self.dicTypesLignes = {}
        for code, libel, ordre in GestionArticle.LISTEtypeLigne:
            self.dicTypesLignes[code] = ordre
        #fin __init__

    def InitObjectListView(self):
        if self.dictDonnees["origine"] == "ajout":
            listeOLV = self.AppelDonneesTarifs()
        elif self.dictDonnees["origine"] == "compl":
            listeOLV = []
        else :
            listeOLV = self.AppelDonneesAnte()
        self.listeOLV = sorted(listeOLV,key=attrgetter('ordre'))
        # Couleur en alternance des lignes
        self.oddRowsBackColor = "#F0FBED"
        self.evenRowsBackColor = wx.Colour(255, 255, 255)
        self.useExpansionColumn = True
        liste_Colonnes = [
            ColumnDefn("Code", "center", 100, "codeArticle",typeDonnee="texte",isEditable=False),
            ColumnDefn("Libelle (libelles modifiables)", "left", 300,"libelle",typeDonnee="texte",isSpaceFilling = True ),
            ColumnDefn("Qté", "right", 50, "qte",typeDonnee="montant",stringConverter=FmtXd ),
            ColumnDefn("Calculé", "right", 100, "montantCalcul",typeDonnee="montant",stringConverter="%.2f",isEditable=False),
            ColumnDefn("Forcé", "right", 100, "montant",typeDonnee="montant",stringConverter=Fmt2d),
            ]
        self.SetColumns(liste_Colonnes)
        self.SetEmptyListMsg("Aucun tarif défini")
        self.SetEmptyListMsgFont(wx.FFont(11, wx.DEFAULT, faceName="Tekton"))
        self.CreateCheckStateColumn()
        #self.SetSortColumn(self.columns[1])
        self.SetObjects(self.listeOLV)
        #fin InitObjectListView

    def AppelDonneesTarifs(self):
        """ Récupération des données en mode ajout """
        DB = self.dictDonnees['db']
        #self.listeChampsTrack = ["codeArticle", "libelle", "montant", "prix1", "prix2",
        #                        "typeLigne","condition", "modeCalcul","force"]
        req = """SELECT matArticles.artCodeArticle, matArticles.artLibelle, matArticles.artPrix1, matArticles.artPrix1,
                        matArticles.artPrix2,matArticles.artCodeBlocFacture as lfaTypeLigne, matArticles.artConditions,
                        matArticles.artModeCalcul, matTarifsLignes.trlPreCoche as foorce
                FROM ((matTarifs
                INNER JOIN matTarifsLignes ON matTarifs.trfCodeTarif = matTarifsLignes.trlCodeTarif)
                INNER JOIN matArticles ON matTarifsLignes.trlCodeArticle = matArticles.artCodeArticle)
                WHERE ((matTarifs.trfIDactivite=%s) AND (matTarifs.trfIDgroupe=%s) AND (matTarifs.trfIDcategorie_tarif=%s))
                GROUP BY matArticles.artCodeArticle,matArticles.artLibelle, matArticles.artPrix1, matArticles.artPrix2, 
                        lfaTypeLigne, matArticles.artConditions, matArticles.artModeCalcul, foorce;
                """ % (str(self.dictDonnees["IDactivite"]),str(self.dictDonnees["IDgroupe"]),str(self.dictDonnees["IDcategorie_tarif"]))
        mess = "DLG_PrixActivite.AppelDonneesTarifs"
        retour = DB.ExecuterReq(req,MsgBox=mess)
        if retour != "ok" : DB.AfficheErr(self,retour)
        recordset = DB.ResultatReq()
        listeOLV = []
        if len(recordset) > 0:
            listeOLV = self.AjoutDonneesOLV(recordset,listeOLV)
            listeOLV = self.AjoutArticles_x(listeOLV)
        else:
                DB.AfficheErr(self,"Aucun articles ne s'affiche car aucun tarif n'est associé à ce camp\n Les tarifs se gérent à partir de l'ajout de ligne en bas de l'écran.")
        return listeOLV
        #fin AppelDonneesTarifs

    def AppelDonneesAnte(self):
        # Ressortir les lignes des saisies précédentes provenant de table PieceLignes
        listeLignes= self.dictDonnees["lignes_piece"]
        listeOLV = self.EnrichirDonnees(listeLignes,forcer = True)
        # Ajout des articles communs
        listeOLV = self.AjoutArticles_x(listeOLV)
        return listeOLV

    def AjoutArticles_x(self,listeOLV):
            DB = self.dictDonnees['db']
            # Ajout des articles communs prfixés '$'
            req = """SELECT matArticles.artCodeArticle, matArticles.artLibelle, matArticles.artPrix1, 
                matArticles.artPrix1, matArticles.artPrix2, matArticles.artCodeBlocFacture, 
                matArticles.artConditions, matArticles.artModeCalcul, 1 as foorce
                    FROM matArticles
                    WHERE (matArticles.artCodeArticle LIKE '$%%') AND matArticles.artNiveauActivite = 1;
                    """
            retour = DB.ExecuterReq(req,MsgBox="ExecuterReq")
            if retour != "ok" : DB.AfficheErr(self,retour)
            else:
                recordset = DB.ResultatReq()
                if len(recordset) > 0:
                    listeOLV = self.AjoutDonneesOLV(recordset,listeOLV)
            return listeOLV

    def AjoutDonneesOLV(self,recordset,listeOLV):
        # Ajoute le contenu de recordset à listeOLV avec étape intermédiaire en liste de dictionnaires
        donnees= []
        for item in recordset:
            i = 0
            record = {}
            for champ in self.listeChampsTrack :
                record[champ] = item[i]
                i= i +1
            if record['typeLigne'] in list(self.dicTypesLignes.keys()):
                record['ordre'] = self.dicTypesLignes[record['typeLigne']]
            else: record['ordre'] = 99
            record["quantite"] = 1
            record["prixUnit"] = record["montant"]
            # test de présence pour éviter les doubles
            ok = True
            for ligne in listeOLV:
                if ligne.codeArticle == record["codeArticle"]: ok = False
            if ok:
                donnees.append(record)
        #Transpose les données de type listes avec clés en objets tracks avec attributs pour OLV
        aCond= GestionArticle.ActionsConditions(self.dictDonnees)
        for item in donnees:
            # priorité au tarif renseigné dans le tarif pour les articles séjour
            if "trfPrix" in list(self.dictDonnees.keys()) and item["typeLigne"] == "Sejour":
                item["prix1"] = self.dictDonnees["trfPrix"]
            # inclu dans l'olv seulement si la condition est respectée
            if aCond.Condition(item["condition"],item["codeArticle"]):
                item["origine"]="articles"
                track = Track(item)
                listeOLV.append(track)

        return listeOLV
        # fin AjoutDonneesOLV

    def EnrichirDonnees(self,listeLignes, forcer = False):
        # Complete les articles simples en lignes-piece pour les champs liste2 liés à l'article et bascule en track la liste de dictionnaire
        donnees = []
        listeChamps=["codeArticle","libelle","quantite","prixUnit","montant"]
        liste2=["prix1","prix2", "typeLigne", "condition", "modeCalcul", "force"]
        DB = self.dictDonnees['db']
        # Transposition des données SQL avec les noms de champs utilisés en track
        if listeLignes != None:
            for dictLigne in listeLignes:
                record = {}
                i=0
                for champLigne in listeChamps:
                    record[champLigne] = dictLigne[champLigne]
                    i += 1
                req = """SELECT matArticles.artCodeArticle, matArticles.artLibelle, matArticles.artPrix1, 
                                matArticles.artPrix2, matArticles.artCodeBlocFacture, matArticles.artConditions, 
                                matArticles.artModeCalcul, 1 as foorce
                    FROM matArticles
                    WHERE (((matArticles.artCodeArticle) = '%s'));
                    """ % record["codeArticle"]
                retour = DB.ExecuterReq(req,MsgBox="ExecuterReq")
                if retour != "ok" : DB.AfficheErr(self,retour)
                recordset = DB.ResultatReq()
                i=2
                for champLigne in liste2:
                    if len(recordset)>0:
                        record[champLigne] = recordset[0][i]
                    else: record[champLigne] = None
                    i += 1
                if record['typeLigne'] in list(self.dicTypesLignes.keys()):
                    record['ordre'] = self.dicTypesLignes[record['typeLigne']]
                else: record['ordre'] = 99
                donnees.append(record)

        #Transpose les données de type listes avec clés en objets tracks avec attributs pour OLV
        listeOLV = []
        aCond= GestionArticle.ActionsConditions(self.dictDonnees)
        for item in donnees:
            cond = False
            if forcer : cond = True
            else :
                if aCond.Condition(item["condition"],item["codeArticle"]): cond = True
            if cond :
                item["origine"]="lignes"
                track = Track(item)
                listeOLV.append(track)
        return listeOLV
        #fin EnrichirDonnees

    def AjoutParrain(self,checked):
        if checked:
            DB = self.dictDonnees['db']
            # Apel article parrain
            req = """SELECT matArticles.artCodeArticle, matArticles.artLibelle, matArticles.artPrix1, matArticles.artPrix1, matArticles.artPrix2,matArticles.artCodeBlocFacture as lfaTypeLigne, 'Sans', 'AbParrain', 0 as foorce
                    FROM matArticles
                    WHERE (matArticles.artCodeArticle = '$$PARRAIN');
                    """
            retour = DB.ExecuterReq(req,MsgBox="ExecuterReq")
            if retour != "ok" :
                DB.AfficheErr(self,retour)
            else:
                recordset = DB.ResultatReq()
                if len(recordset) > 0:
                    # suppression d'une éventuelle ligne précédente
                    self.parent.data = [x for x in self.parent.data if x.codeArticle != "$$PARRAIN"]
                    lignes = []
                    lignes = self.AjoutDonneesOLV(recordset,lignes)
                    for ligne in lignes:
                        self.parent.data.append(ligne)
                        self.parent.resultsOlv.SetCheckState(ligne, True)

        else:
            for ligne in self.parent.data:
                if ligne.codeArticle == "$$PARRAIN":
                    self.parent.data.remove(ligne)
        #fin AjoutParrain

class DlgTarification(wx.Dialog):
    def __init__(self, parent, dictDonnees):
        """Constructor   |wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX"""
        wx.Dialog.__init__(self, parent,-1, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX)
        if dictDonnees["origine"] in ("ajout","compl","modif"):
            self.rw = True
        else :
            self.rw = False
        # Verrouillage utilisateurs
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("individus_inscriptions", "creer", IDactivite=dictDonnees["IDactivite"]) == False :
            self.rw = False
        self.parent = parent
        self.listeLignesPiece=[]
        # dicDonnees ne sera mis à jour qu'en cas de succés
        self.dDonneesOrig = dictDonnees
        self.dictDonnees = {}
        for key, don in dictDonnees.items():
            self.dictDonnees[key] = don          
        self.dictDonnees = dictDonnees
        # DB sera utilisé dans tous les enfants via dictDonnees
        self.DB = GestionDB.DB()
        self.dictDonnees['db'] = self.DB
        self.GetTrfPrix() # alimente la clé trfPrix dans dictDonnees
        self.SetTitle("DLG_PrixActivite")
        self.IDfamille = dictDonnees["IDfamille"]
        self.IDindividu = dictDonnees["IDindividu"]
        self.IDactivite = dictDonnees["IDactivite"]
        self.IDgroupe = dictDonnees["IDgroupe"]
        self.IDparrain = dictDonnees["IDparrain"]
        if  dictDonnees["parrainAbandon"] in (0,None, False):
            self.parrainAbandon = False
        else: self.parrainAbandon = True

        self.codeNature = None
        self.modifJours = False
        self.nbreJours = None
        self.IDcategorieTarif = dictDonnees["IDcategorie_tarif"]
        if  dictDonnees["nom_activite"] == None : dictDonnees["nom_activite"] = "-"
        if  dictDonnees["nom_groupe"] == None : dictDonnees["nom_groupe"] = "-"
        if  dictDonnees["nom_categorie_tarif"] == None : dictDonnees["nom_categorie_tarif"] = "-"
        ligneInfo = "Activité: " + dictDonnees["nom_activite"] + " | Groupe: " + dictDonnees["nom_groupe"]+ " | Tarif: " + dictDonnees["nom_categorie_tarif"]
        soustitreFenetre = "Campeur : " + dictDonnees["nom_individu"] + " | Famille : " + dictDonnees["nom_famille"]
        self.ctrl_bandeau = CTRL_Bandeau.Bandeau(self, titre=ligneInfo, texte=soustitreFenetre, hauteurHtml=10,nomImage="Images/22x22/Smiley_nul.png")
        # Verrouillage utilisateurs
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("individus_inscriptions", "creer", IDactivite=dictDonnees["IDactivite"]) == False :
            self.rw = False
        # conteneur des données
        self.resultsOlv = OLVtarification(self, dictDonnees, id=-1, name="DLG_PrixActivite", style=wx.LC_REPORT )
        self.resultsOlv.InitObjectListView()
        if 'coches' in self.dictDonnees:
            if self.dictDonnees['coches']:
                self.PreCoche()
        else: self.PreCoche()
        self.ctrl_recherche = CTRL_Outils(self, listview=self.resultsOlv)
        self.data = self.resultsOlv.listeOLV
        self.dataorigine = copy.deepcopy(self.data)
        # gestion du parrainage
        self.parrain_staticbox = wx.StaticBox(self, -1, "Parrainage")
        self.label_parrain = wx.StaticText(self, -1,  "Parrain :")
        self.ctrl_nom_parrain = wx.TextCtrl(self, -1, "",size=(80, 20))
        self.bouton_parrain = wx.Button(self, -1, "...", size=(20, 20))
        self.label_abandon = wx.StaticText(self, -1, "Abandon à filleul :")
        self.ctrl_abandon = wx.CheckBox(self)
        # pour conteneur des actions en pied d'écran
        self.pied_staticbox = wx.StaticBox(self, -1, "Actions")
        self.hyper_tout = Hyperlien(self, label="Tout cocher", infobulle="Cliquez ici pour tout cocher",
                                    URL="tout")
        self.hyper_rien = Hyperlien(self, label="Tout décocher", infobulle="Cliquez ici pour tout décocher",
                                    URL="rien")
        self.hyper_ajoutArticle = Hyperlien(self, label="| Ajouter Ligne", infobulle="Ajouter un article", URL="article")
        self.hyper_ajoutCommentaire = Hyperlien(self, label="| Commentaire", infobulle="En Projet : ajouter un commentaire Libre", URL="commentaire")
        self.bouton_ok = CTRL_Bouton_image.CTRL(self, texte="Choix Piece", cheminImage="Images/32x32/Valider.png")
        self.bouton_oj = CTRL_Bouton_image.CTRL(self, texte="Piece idem", cheminImage="Images/BoutonsImages/Retour_L72.png")
        if self.rw :
            self.bouton_annuler = wx.BitmapButton(self, wx.ID_CANCEL,wx.Bitmap(Chemins.GetStaticPath("Images/BoutonsImages/Annuler_L72.png"), wx.BITMAP_TYPE_ANY))
        else:
            self.bouton_annuler = wx.BitmapButton(self, wx.ID_CANCEL,wx.Bitmap(Chemins.GetStaticPath("Images/BoutonsImages/Retour_L72.png"), wx.BITMAP_TYPE_ANY))
        self.ctrl_solde = CTRL_Solde(self)
        self.ctrl_solde.SetSolde(1000)
        self.ctrl_abandon.SetValue(self.parrainAbandon)
        self.ctrl_nom_parrain.SetValue(self.GetParrain(self.IDparrain))
        #Test du parrainage
        self.isParrainable = True

        req = """SELECT individus_1.date_creation,individus_1.nom,individus_1.prenom
                FROM ((individus
                INNER JOIN rattachements ON individus.IDindividu = rattachements.IDindividu)
                INNER JOIN rattachements AS rattachements_1 ON rattachements.IDfamille = rattachements_1.IDfamille)
                INNER JOIN individus AS individus_1 ON rattachements_1.IDindividu = individus_1.IDindividu
                WHERE (((individus.IDindividu)=%d) AND ((rattachements_1.IDcategorie)<>3));
             """ % (self.IDindividu)
        retour = self.DB.ExecuterReq(req,MsgBox="ExecuterReq")
        if "dateCreation" in dictDonnees:
            annee = dictDonnees["dateCreation"][:4]
        else: annee = str(datetime.date.today())[:4]
        if retour != "ok" : self.DB.AfficheErr(self,retour)
        recordset = self.DB.ResultatReq()
        self.prenomNom =""
        if len(recordset)>0:
            for (creationIndividu,nom,prenom) in recordset:
                if creationIndividu ==None:
                    #création ancienne
                    self.isParrainable = False
                    self.prenomNom = prenom+" "+nom
                elif creationIndividu[:4] < annee :
                    #individu de la famille pas de l'année de création de la pièce
                    self.prenomNom = prenom+" "+nom
                    self.isParrainable = False

        self.__set_properties()
        self.__do_layout()
        self.resultsOlv.Bind(wx.EVT_LIST_ITEM_SELECTED, self.Selected)
        self.resultsOlv.Bind(wx.EVT_TEXT, self.Texte)
        self.Bind(wx.EVT_BUTTON, self.OnParrain, self.bouton_parrain)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonOk, self.bouton_ok)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonOj, self.bouton_oj)
        self.Bind(wx.EVT_BUTTON, self.FinSaisie, self.bouton_annuler)
        self.Bind(wx.EVT_CHECKBOX, self.OnAbandonFilleul, self.ctrl_abandon)
        self.ctrl_nom_parrain.Bind(wx.EVT_LEFT_DOWN, self.OnNomParrain)

        self.dataorigine = copy.deepcopy(self.data)
        self.lastObj = None
        self.obj = None
        self.CalculSolde()
        self.lastBind = "clic"
        # fin de init

    def __set_properties(self):
        if not self.rw :
            self.bouton_ok.Enable(False)
            self.bouton_oj.Enable(False)
            self.resultsOlv.Enable(False)
            self.hyper_ajoutArticle.Enable(False)
            self.hyper_ajoutCommentaire.Enable(False)
            self.hyper_rien.Enable(False)
            self.hyper_tout.Enable(False)
        if self.dictDonnees["origine"] in ("ajout","compl"):
            self.bouton_oj.Enable(False)
        self.bouton_ok.SetToolTip("Cliquez ici pour chaîner sur le type de pièce")
        self.bouton_oj.SetToolTip("Cliquez ici pour valider sans changer le type de pièce")
        self.bouton_annuler.SetToolTip("Cliquez ici pour annuler")
        self.ctrl_solde.SetToolTip("Ne Saisissez pas le montant ici, mais sur les lignes cochées")
        self.ctrl_solde.ctrl_solde.SetToolTip("Ne Saisissez pas le montant ici, mais sur les lignes cochées")
        self.ctrl_nom_parrain.SetToolTip("Choisir le parrain avec le bouton à droite")
        self.bouton_parrain.SetToolTip("Choix du parrain prescripteur")
        self.label_abandon.SetToolTip("Cocher si le parrain renonce à son crédit au profit du filleul")
        self.ctrl_abandon.SetToolTip("Cocher si le parrain renonce à son crédit au profit du filleul")

    def __do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(rows=5, cols=1, vgap=5, hgap=5)
        grid_sizer_base.Add(self.ctrl_bandeau, 0, wx.EXPAND, 0)
        grid_sizer_base.Add(self.resultsOlv, 0, wx.EXPAND, 0)
        grid_sizer_base.Add(self.ctrl_recherche, 0, wx.EXPAND, 0)

        parrain_staticboxSizer = wx.StaticBoxSizer(self.parrain_staticbox, wx.VERTICAL)
        grid_sizer_parrain = wx.FlexGridSizer(rows=1, cols=5, vgap=3, hgap=3)
        grid_sizer_parrain.Add(self.label_parrain, 0, wx.LEFT, 30)
        grid_sizer_parrain.Add(self.ctrl_nom_parrain, 1, wx.EXPAND, 0)
        grid_sizer_parrain.Add(self.bouton_parrain, 0, 0, 0)
        grid_sizer_parrain.Add(self.label_abandon, 0, wx.LEFT, 20)
        grid_sizer_parrain.Add(self.ctrl_abandon, 0, wx.RIGHT, 20)
        grid_sizer_parrain.AddGrowableCol(1)
        parrain_staticboxSizer.Add(grid_sizer_parrain, 1, wx.EXPAND, 5)
        grid_sizer_base.Add(parrain_staticboxSizer, 1, wx.EXPAND, 5)

        pied_staticboxSizer = wx.StaticBoxSizer(self.pied_staticbox, wx.VERTICAL)
        grid_sizer_pied = wx.FlexGridSizer(rows=1, cols=6, vgap=3, hgap=3)

        grid_sizer_cocher = wx.FlexGridSizer(rows=2, cols=1, vgap=1, hgap=10)
        grid_sizer_cocher.Add(self.hyper_tout, 0, wx.ALL, 0)
        grid_sizer_cocher.Add(self.hyper_rien, 0, wx.ALL, 0)
        grid_sizer_pied.Add(grid_sizer_cocher, 1, wx.EXPAND, 0)

        grid_sizer_outils = wx.FlexGridSizer(rows=2, cols=1, vgap=1, hgap=10)
        grid_sizer_outils.Add(self.hyper_ajoutArticle, 0, wx.ALL, 0)
        grid_sizer_outils.Add(self.hyper_ajoutCommentaire, 0, wx.ALL, 0)
        grid_sizer_pied.Add(grid_sizer_outils, 1, wx.EXPAND, 0)

        grid_sizer_pied.Add(self.bouton_oj, 0, 0, 0)
        grid_sizer_pied.Add(self.bouton_ok, 0, 0, 0)
        grid_sizer_pied.Add(self.bouton_annuler, 0, 0, 0)
        grid_sizer_pied.Add(self.ctrl_solde, 0, 0, 0)
        grid_sizer_pied.AddGrowableCol(1)

        pied_staticboxSizer.Add(grid_sizer_pied, 1, wx.EXPAND, 5)
        grid_sizer_base.Add(pied_staticboxSizer, 1, wx.EXPAND, 5)

        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)
        grid_sizer_base.AddGrowableRow(1)
        grid_sizer_base.AddGrowableCol(0)
        self.SetMinSize((650, 550))
        self.Layout()
        self.CenterOnScreen()

    def OnBoutonOk(self, event):
        # Choix de la nature de la pièce
        if self.dictDonnees["origine"] != "modif" :
            testSejour = True
        else : testSejour = False
        # Complète l'info en cas de création
        if not "IDinscription" in self.dictDonnees:
            self.dictDonnees["IDinscription"] = None
        if not "IDnumPiece" in self.dDonneesOrig:
            self.dDonneesOrig["IDnumPiece"] = None

        tracks = self.resultsOlv.GetCheckedObjects()
        valide1 = DLG_ChoixTypePiece.ValideSaisie(tracks,testSejour=testSejour)
        valide2 = DLG_ChoixTypePiece.DoubleLigne(tracks,self.dictDonnees["IDinscription"],
                                                 self.DB,
                                                 IDnumPiece=self.dDonneesOrig["IDnumPiece"],
                                                 IDfamille= self.dictDonnees["IDfamille"])
        if valide1 and valide2 :
            endModal = wx.ID_CANCEL
            if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("familles_factures", "creer")  :
                dlg = DLG_ChoixTypePiece.Dialog(self,"ajout")
                interroChoix = dlg.ShowModal()
                self.codeNature = dlg.codeNature
                self.listeLignesPiece = []
                dlg.Destroy()
                if interroChoix == wx.ID_OK and self.codeNature :
                    endModal = wx.ID_OK
                    self.FinSaisie(event)
            self.Sortie(endModal)

    def OnBoutonOj(self, event):
        # Piece idem, la nature reste en l'état, cas de modification pas de création
        if self.dictDonnees["origine"] != "compl" :
            testSejour = True
        else : testSejour = False
        # Complète l'info en cas de création
        if not "IDinscription" in self.dictDonnees:
            self.dictDonnees["IDinscription"] = None
        if not "IDnumPiece" in self.dDonneesOrig:
            self.dDonneesOrig["IDnumPiece"] = None

        tracks = self.resultsOlv.GetCheckedObjects()
        valide1 = DLG_ChoixTypePiece.ValideSaisie(tracks,testSejour=testSejour)
        valide2 = DLG_ChoixTypePiece.DoubleLigne(tracks,self.dictDonnees["IDinscription"],
                                                 self.DB,
                                                 IDnumPiece=self.dDonneesOrig["IDnumPiece"],
                                                 IDfamille= self.dictDonnees["IDfamille"])
        if valide1 and valide2 :
            self.FinSaisie(event)

    def FinSaisie(self,event):
        # oriente vers final avec cancel ou ok
        self.listeLignesPiece = self.ListeDict(self.resultsOlv)
        if event and event.Id == wx.ID_CANCEL:
            self.Sortie(wx.ID_CANCEL)
            return
        # Validation du montant
        endModal = wx.ID_CANCEL
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("familles_factures", "creer")  :
            endModal= wx.ID_OK
        self.Sortie(endModal)
        #fin FinSaisie

    def SauveDonnees(self):
        # sauvegarde des données qui seront enregistrées par le parent
        listeCodesNature = []
        for item in GestionArticle.LISTEnaturesPieces :
            listeCodesNature.append(item[0])
        etatPiece = "00000"
        i = listeCodesNature.index(self.codeNature)
        # Mise à "1" du caractère en la position correspondant à la nature de la pièce (ex: FAC = 4eme)
        etatPiece = etatPiece[:i] + "1" + etatPiece[i + 1:]
        self.dictDonnees["nature"] = self.codeNature
        self.dictDonnees["etat"] = etatPiece
        self.dictDonnees["lignes_piece"] = self.listeLignesPiece
        self.dictDonnees["nbreJours"] = self.nbreJours
        if not "IDprestation" in self.dictDonnees:
            self.dictDonnees["IDprestation"] = None
        # enrichi le dictinnaire reçu
        self.dDonneesOrig.update(self.dictDonnees)

    def Sortie(self, endModal):
        self.DB.Close()
        if self.codeNature and endModal == wx.ID_OK and len(self.codeNature)>0:
            self.SauveDonnees()
        self.EndModal(endModal)

    def ListeDict(self,olv,):
        # Permet de récupérer le format liste de dictionnaires pour les lignes de la pièce
        objects = olv.GetObjects()
        listeLignesPiece = []
        for obj in objects:
            if olv.IsChecked(obj) == True:
                dictTemp = {}
                dictTemp["codeArticle"]= obj.codeArticle
                dictTemp["libelle"]= obj.libelle
                dictTemp["quantite"]= obj.qte
                dictTemp["prixUnit"]= obj.prixUnit
                dictTemp["montant"]= obj.montant
                listeLignesPiece.append(dictTemp)
        return listeLignesPiece

    def CocheTout(self, state):
        objects = self.resultsOlv.GetObjects()
        for obj in objects:
            self.resultsOlv.SetCheckState(obj, state)
        self.CalculSolde()
        self.resultsOlv.RefreshObjects(objects)

    def OnNomParrain(self,event):
        self.OnParrain(event)

    def OnParrain(self, typeLigne):
        if not self.isParrainable:
            wx.MessageBox("%s pas 'nouveau client'\n\nLe parrainage n'est pas sensé être appliqué"%self.prenomNom +
                          " quand un représentant ou un enfant de la famille est connu, mais ce n'est pas bloquant")
        dlg = DLG_ChoixLigne.DlgChoixFamille(self)
        choix= False
        self.IDparrain = None
        if dlg.ShowModal() == wx.ID_OK:
            choix = True
        if choix:
            self.ctrl_nom_parrain.SetValue(dlg.nomChoix)
            self.IDparrain = dlg.IDchoix
            if self.IDparrain == None:
                self.ctrl_abandon.SetValue(False)
                self.OnAbandonFilleul(None)
            self.GetDictParrain()
        dlg.Close()

    def OnAbandonFilleul(self, event):
        self.parrainAbandon = self.ctrl_abandon.GetValue()
        testok =  self.GetDictParrain()
        if self.ctrl_abandon.IsChecked() and testok:
            if len(self.ctrl_nom_parrain.Value) < 3:
                GestionDB.MessageBox(self,
                                     "Pas de Parrain, pas de crédit à son filleul...",
                                     titre="Refus d'action")
                self.ctrl_abandon.SetValue(False)
                self.parrainAbandon = False
            self.resultsOlv.AjoutParrain(True)
            self.parrainAbandon = True
        if not self.ctrl_abandon.IsChecked():
            self.resultsOlv.AjoutParrain(False)
            self.ctrl_nom_parrain.Enable(True)
            self.bouton_parrain.Enable(True)
            self.parrainAbandon = False
        self.resultsOlv.SetObjects(self.data)
        self.CalculSolde()

    def AjouteLigne(self, typeLigne):
        if typeLigne == "article":
            self.listeLignes = []
            # la liste est alimentée par le ok du dlg
            dlg = DLG_ChoixLigne.DlgChoixArticle(self,niveau='activite')
            if dlg.ShowModal() == wx.ID_OK:
                self.ActionAjout(self.listeLignes)

    def ActionAjout(self, listeLignes):
        # Ajout d'une ligne article
        fOLV = OLVtarification(self,self.dictDonnees,)
        listeLignesPlus = fOLV.EnrichirDonnees(listeLignes,forcer = True)
        if len(listeLignesPlus)>0:
            for ligne in listeLignesPlus:
                ligne.saisie = False
                ligne2= copy.deepcopy(ligne)
                self.data.append(ligne)
                self.dataorigine.append(ligne2)
                self.resultsOlv.SetCheckState(ligne, True)
            self.resultsOlv.SetObjects(self.data)
            self.CalculSolde()
        fOLV.Destroy()

    def Texte(self, event):
        if self.lastBind != "texte":
            self.lastObj = copy.deepcopy(self.obj)
            self.lastBind = "texte"
            self.lastLigne =  self.resultsOlv.GetFocusedRow()

    def Selected(self, event):
        if self.obj == None :
            self.obj = self.resultsOlv.GetSelectedObject()
            self.lastBind = "select"
            self.lastLigne = 0

        #  reprise d'un éléments si nouvelle coche
        if self.resultsOlv.IsChecked(self.obj) == True:
            for objOrigine in self.dataorigine:
                if objOrigine.codeArticle == self.obj.codeArticle:
                    self.obj.prixUnit = objOrigine.prixUnit
                    self.obj.saisie = True

        # une saisie texte a eu lieu des contrôles et actions sont nécessaires
        if self.lastBind == "texte" :
            objects = self.resultsOlv.GetObjects()
            i = 0
            for obj in objects :
                if self.lastLigne == i:
                    # la quantité a été modifiée
                    if (self.lastObj.qte != obj.qte) and (self.lastObj.codeArticle == obj.codeArticle) :
                        if obj.codeArticle:
                            self.modifJours = True
                            self.qte = obj.qte
                            self.nbreJours=self.qte
                    # le zéro saisi en montant doit désactiver la ligne
                    if obj.montant == 0 and self.lastObj.montant != 0:
                        self.resultsOlv.SetCheckState(obj, False)
                    obj.saisie = True
                i +=1
        self.lastBind = "select"
        self.CalculSolde()
        self.obj = self.resultsOlv.GetSelectedObject()

    def CalculSolde(self):
        if self.modifJours:
            self.modifJours = False
            texte1 = "La quantité saisie " + str(self.qte) + " correspond à un nombre de jours de l'activité"
            texte2 = "Avec " + str(self.qte) + " nuits, l'activité court sur " + str(self.qte +1 ) + " jours"
            texte3 = "La quantité ne concerne pas la durée de l'activité"
            retour = GestionDB.Messages().Choix(listeTuples=[(1,texte1),(2,texte2),(3,texte3),], titre = ("Quel est le sens de cette quantité modifiée "), intro = "Quantité de " + str(self.lastObj.qte)+" -> " + str(self.qte))
            if retour[0] == 1 :
                self.nbreJours = self.qte
            if retour[0] == 2 :
                self.nbreJours = self.qte +1
            self.dictDonnees["nbreJours"] = self.nbreJours
        total = 0
        aCalc= GestionArticle.ActionsModeCalcul(self.dictDonnees)

        objects = self.resultsOlv.GetObjects()
        # ajout de l'attribut coché
        for obj in objects:
            obj.isChecked = self.resultsOlv.IsChecked(obj)

        for obj in sorted(objects,key=attrgetter('ordre')):
            if obj.isChecked == False:
                obj.montant = 0.0
                obj.prixUnit = 0.0
                obj.montantCalcul = 0.0
            else:
                # recalcul des arcticles selon leur mode de calcul.
                obj.montantCalcul = obj.prixUnit * obj.qte
                qte,mtt = aCalc.ModeCalcul(obj,objects)
                if qte == None : qte = 1
                if mtt != None:
                    if qte > 0:
                        obj.prixUnit = round(float(mtt) / float(qte),2)
                    if not obj.saisie :
                        obj.qte = qte
                    obj.montantCalcul = round(float(obj.prixUnit) * float(obj.qte),2)
                # calcul du total avec lignes cochées et priorité au montants saisis
                if obj.montant != 0:
                    total += obj.montant
                else: total += (obj.montantCalcul)
            obj.montant = float(obj.montant)
            obj.qte = float(obj.qte)
            obj.montantCalcul = float(obj.montantCalcul)

        self.ctrl_solde.SetSolde(total)
        self.resultsOlv.SetObjects(objects)
        self.resultsOlv.RefreshObjects(objects)
        #fin CalculSolde

    def PreCoche(self):
        objects = self.resultsOlv.GetObjects()
        for obj in objects:
            if obj.force == 0:
                self.resultsOlv.SetCheckState(obj, False)
                obj.montant = 0.00
            else:
                self.resultsOlv.SetCheckState(obj, True)
            self.resultsOlv.RefreshObjects(objects)

    def GetParrain(self,IDparrain):
        nomChoix = " "
        if IDparrain != None:
            dlg = DLG_ChoixLigne.OLVchoixFamille(self)
            dlg.GetParrain(IDparrain)
            nomChoix = dlg.nomChoix
            dlg.Destroy()
        return nomChoix

    def GetDictParrain(self):
        if not 'IDinscription' in self.dictDonnees or not self.dictDonnees['IDinscription']:
            self.dictDonnees['IDinscription'] = 0
        #préparation des seuls paramètres parrainage
        lstOldIDpar = []
        req = """SELECT matPieces.pieIDfamille, matParrainages.parIDligneParr
                FROM matParrainages 
                    INNER JOIN matPiecesLignes ON matParrainages.parIDligneParr = matPiecesLignes.ligIDnumLigne 
                    INNER JOIN matPieces ON matPiecesLignes.ligIDnumPiece = matPieces.pieIDnumPiece
                WHERE parIDinscription = %d
            """ % self.dictDonnees["IDinscription"]
        retour = self.DB.ExecuterReq(req,MsgBox="ExecuterReq")
        if retour == "ok" and self.dictDonnees['IDinscription'] > 0:
            recordset = self.DB.ResultatReq()
            for IDparrain, IDligne in recordset:
                if IDparrain != self.dictDonnees['IDfamille']:
                    dlgErr = wx.MessageDialog(self,
                        "Cette inscription a déjà fait l'objet d'une réduction pour la famille %d,\n supprimez-la d'abord."%IDparrain ,
                        "MODIFCATION IMPOSSIBLE !", wx.ICON_EXCLAMATION)
                    self.dictDonnees['parrainAbandon'] = False
                    self.ctrl_abandon.SetValue(False)
                    dlgErr.ShowModal()
                    dlgErr.Destroy()
                    return False
                else:
                    lstOldIDpar.append(IDligne)
        self.dictDonnees['selfParrainage'] = {}
        self.dictDonnees['selfParrainage']['codeArticle'] = '$$PARRAIN'
        self.dictDonnees['selfParrainage']['parIDligneParr'] = None
        self.dictDonnees['selfParrainage']['lstIDoldPar'] = lstOldIDpar
        self.dictDonnees['selfParrainage']['parIDinscription'] = self.dictDonnees['IDinscription']
        self.dictDonnees['selfParrainage']['parAbandon'] = int(self.parrainAbandon)
        self.dictDonnees["IDparrain"] = self.IDparrain
        self.dictDonnees["parrainAbandon"] = self.parrainAbandon
        return True

    def GetTrfPrix(self):
        # récupération du prix de base séjour dans matTarifs, mis dans dictDonnees
        req = """
                SELECT trfPrix
                FROM matTarifs
                WHERE ((matTarifs.trfIDactivite=%s) AND (matTarifs.trfIDgroupe=%s) AND (matTarifs.trfIDcategorie_tarif=%s))
                ;""" % (str(self.dictDonnees["IDactivite"]),
                        str(self.dictDonnees["IDgroupe"]),
                        str(self.dictDonnees["IDcategorie_tarif"]))
        retour = self.DB.ExecuterReq(req,MsgBox="ExecuterReq")
        if retour != "ok" : self.DB.AfficheErr(self,retour)
        recordset = self.DB.ResultatReq()
        trfPrix = None
        if len(recordset) == 1:
            trfPrix = recordset[0][0]
        if trfPrix and trfPrix > 0.0:
            self.dictDonnees["trfPrix"] = trfPrix

# -------------------------------------------------------------------------------------------------------------------------------------------
class BarreRecherche(wx.SearchCtrl):
    def __init__(self, parent):
        wx.SearchCtrl.__init__(self, parent, size=(-1, -1), style=wx.TE_PROCESS_ENTER)
        self.parent = parent
        self.rechercheEnCours = False

        self.SetDescriptiveText("Rechercher un Bloc...")
        self.ShowSearchButton(True)

        self.listView = self.parent.resultsOlv
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
        txtSearch = self.GetValue()
        self.ShowCancelButton(len(txtSearch))
        self.listView.GetFilter().SetText(txtSearch)
        self.listView.RepopulateList()
        self.Refresh()

class Hyperlien(Hyperlink.HyperLinkCtrl):
    def __init__(self, parent, id=-1, label="", infobulle="", URL=""):
        Hyperlink.HyperLinkCtrl.__init__(self, parent, id, label, URL=URL)
        self.parent = parent
        self.URL = URL
        self.AutoBrowse(False)

        # SetColours(1,2,3 )1'link':à l'ouverture, 2`visited`: survol avant clic, 3`rollover`: après le clic,
        self.SetColours("BLUE", "BLUE", "PURPLE")

        # SetUnderlines(1,2,3 ) 1'link':`True` underlined(à l'ouverture),2`visited`:'True` underlined(lors du survol avant clic), 3`rollover`:`True` (trace après le clic),
        self.SetUnderlines(False, True, False)
        self.SetBold(False)
        self.EnableRollover(True)
        self.SetToolTip(wx.ToolTip(infobulle))
        self.UpdateLink()
        self.DoPopup(False)
        self.Bind(Hyperlink.EVT_HYPERLINK_LEFT, self.OnLeftLink)

    def OnLeftLink(self, event):
        if self.URL == "tout": self.parent.CocheTout(True)
        if self.URL == "rien": self.parent.CocheTout(False)
        if self.URL == "article": self.parent.AjouteLigne("article")
        if self.URL == "commentaire": self.parent.AjouteLigne("commentaire")
        self.UpdateLink()

# --------------------Lancement de test ----------------------
if __name__ == "__main__":
    app = wx.App(0)
    listeDonnees = [
        ("origine", "ajout"),
        ("IDindividu", 9),
        ("IDfamille", 9),
        ("IDactivite", 716),
        ("IDgroupe", 2019),
        ("IDcategorie_tarif", 1597),
        ("IDcompte_payeur", 9),
        ("date_inscription", str(datetime.date.today())),
        ("parti", False),
        ("IDparrain", None),
        ("parrainAbandon", None),
        ("nom_activite", "Sejou"),
        ("nom_famille", "ma famille"),
        ("nom_groupe", "Groupe Pasto Plus"),
        ("nom_categorie_tarif", "Tarif Normal"),
        ("nom_individu", "nom de  l'individu"),
        ("lignes_piece", [{'utilisateur': 'NoName', 'quantite': 3, 'montant': 480.5, 'codeArticle': 'SEJ_CORSE_S1', 'libelle': 'Séjour Jeunes Corse S1', 'IDnumPiece': 5, 'prixUnit': 480.0, 'date': '2016-07-24', 'IDnumLigne': 128}
]),
    ]
    dictDonnees = {}
    for donnee in listeDonnees:
        champ = donnee[0]
        valeur = donnee[1]
        dictDonnees[champ] = valeur

    f = DlgTarification(None, dictDonnees)
    app.SetTopWindow(f)
    if f.ShowModal() == wx.ID_OK:
        print("OK")
    else:
        print("KC")
    app.MainLoop()
