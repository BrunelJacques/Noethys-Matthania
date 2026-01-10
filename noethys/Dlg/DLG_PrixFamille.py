# Derive de DLG_PrixActivite.py
# -*- coding: iso-8859-15 -*-
# -----------------------------------------------------------
# Application :    Noethys, Matthania
# Auteur:          Ivan LUCAS, JB, Jacques Brunel
# Ecran de tarification niveau famille derrière inscription
# -----------------------------------------------------------

from Utils.UTILS_Traduction import _
import Chemins
import wx
import datetime
from FonctionsPerso import Nz
from operator import attrgetter
import wx.lib.agw.hyperlink as Hyperlink
from Ctrl.CTRL_ObjectListView import ObjectListView, ColumnDefn, Filter, CTRL_Outils
import copy
from Ctrl import CTRL_Bouton_image
from Ctrl import CTRL_Bandeau
from Utils import UTILS_Config
from Utils import UTILS_Utilisateurs
import GestionDB
from Dlg import DLG_ChoixLigne
from Dlg import DLG_FacturationPieces
from Dlg import DLG_ChoixTypePiece
from Dlg import DLG_Choix
from Gest import GestionArticle
from Gest import GestionInscription
from Gest import GestionPieces
from Utils.UTILS_Decimal import FloatToDecimal as FloatToDecimal

SYMBOLE = UTILS_Config.GetParametre("monnaie_symbole", "€")

PURPLE = "#781E6E"

def AvecCondition(obj):
    return GestionArticle.AvecCondition(obj)

def AvecCalcul(obj):
    return GestionArticle.AvecCalcul(obj)

def Nz(valeur):
    try:
        valFloat = float(valeur)
    except:
        valFloat = 0.0
    return valFloat

def Fmt2d(montant):
    # Convert the given montant into a string with zero null
    if montant != 0:
        return "%.2f" % montant
    else:
        return " "

def FmtXd(montant):
    # Convert the given montant into décimales variables
    fmt = "%.4f" % montant
    if (1000 * montant) % 1 < 0.01: fmt = "%.3f" % montant
    if (100 * montant) % 1 < 0.001: fmt = "%.2f" % montant
    if (10 * montant) % 1 < 0.0001: fmt = "%.1f" % montant
    if (montant) % 1 < 0.00001: fmt = "%.0f" % montant
    if montant == 0: fmt = " "
    return fmt

def GetTypesLignes():
    # pour ajouter l'ordre les lignes dans les tracks et trier pour les calculs
    dicTypesLignes = {}
    for code, libel, ordre in GestionArticle.LISTEtypeLigne:
        dicTypesLignes[code] = ordre
    return dicTypesLignes

def Calcul(dictDonnees, obj, objects):
    aCalc = GestionArticle.ActionsModeCalcul(dictDonnees)
    qte, mtt = aCalc.ModeCalcul(obj, objects)
    if mtt:
        mtt = round(mtt, 2)
        obj.montantCalcul = mtt
        obj.quantite = qte
        #obj.force = 'OUI'

def Multilignes(listeOLV, dictDonnees):
    # démultiplication des articles multi lignes
    dictConditionsMulti = {}
    for ligne in listeOLV:
        if ligne.condition != None:
            if len(ligne.condition) > 5:
                if ligne.condition[0:5] in ["Multi", "Parra"]:
                    if ligne.condition not in dictConditionsMulti:
                        dictConditionsMulti[ligne.condition] = ligne.codeArticle
    if len(list(dictConditionsMulti.keys())) > 0:
        aCond = GestionArticle.ActionsConditions(dictDonnees)
        for condition in list(dictConditionsMulti.keys()):
            aCond.ConditionMulti(condition, dictConditionsMulti[condition], listeOLV)
    return listeOLV

def NormaliseLignes(lignes):
    # permet de les comparer
    champs = ['quantite', 'montant', 'codeArticle', 'libelle', 'IDnumPiece', 'prixUnit',
              'IDnumLigne']
    lignesPieces = []
    for lig in lignes:
        dic = {}
        if lig['montant'] == 0.0 and lig['quantite'] * lig['prixUnit'] != 0.0:
            lig['montant'] = lig['quantite'] * lig['prixUnit']
        for champ in champs:
            if not champ in lig:
                dic[champ] = None
            else:
                dic[champ] = lig[champ]
        lignesPieces.append(dic)
    return lignesPieces

def GetLignes999(parent, annee, DB):
    # appel des lignes famille de la piece en cours non facturée ou des factures de l'exercice
    if not parent.facture:
        # vérif parrainages pour piece famille non facturée
        pGest = GestionPieces.Forfaits(parent, DB=DB)
        pGest.CoherenceParrainages(parent.IDpayeur, DB=DB)
        del pGest

    fGest = GestionInscription.Forfaits(parent.parent, DB=DB)
    listePieces = fGest.GetPieceModif999(parent, parent.IDpayeur, annee,
                                         facture=parent.facture)
    presence999 = len(listePieces)
    # rassemble les lignes des pièces existantes pour l'exercice
    lignes999 = None  # cas d'absence de pièce
    if presence999 > 0:
        lignes999 = []  # présence de pièce, pas forcément avec des lignes
        # on déroule la liste des pièces se rapportant aux conditions
        for key in list(listePieces[0].keys()):
            # constitution préalable de dictDonnées à partir de la première pièce
            parent.dictDonnees[key] = listePieces[0][key]
        # on déroule la liste des pièces se rapportant aux conditions
        for piece in listePieces:
            if parent.facture:
                if not piece['nature'] in ("FAC"):
                    continue
                parent.listeIDpiecesOrigine.append(piece["IDnumPiece"])
                for ligne in piece["lignes_piece"]:
                    lignes999.append(ligne)
            else:
                # cas d'une reprise d'une pièce en cours non facturée
                if piece['nature'] in ("AVO", "FAC"):
                    continue
                # controle l'unicité de la pièce famille non facturée
                if 'pieceEnCours' in list(parent.dictDonnees.keys()) and \
                        parent.dictDonnees['pieceEnCours'] != piece['IDnumPiece']:
                    texte = "Anomalie!\n\nPlusieurs pièces non facturées pour le niveau famille sont en cours."
                    texte += "\nIl faut en supprimer pour pouvoir gérer correctement la modification d'une seule"
                    wx.MessageBox(texte, "DLG_PrixFamille - lancement")

                parent.dictDonnees['pieceEnCours'] = piece['IDnumPiece']
                parent.dictDonnees['pieceOrigine'] = piece

                for ligne in piece["lignes_piece"]:
                    lignes999.append(ligne)
                if hasattr(parent, 'listeIDpiecesOrigine'):
                    parent.listeIDpiecesOrigine.append(piece["IDnumPiece"])

                if piece["IDprestation"] != None and hasattr(parent,
                                                             'lstIDprestationsOrigine'):
                    parent.lstIDprestationsOrigine.append(piece["IDprestation"])
    return lignes999

def GetArticles(annee, dictDonnees):
    DB = dictDonnees['db']
    # appel des articles automatiques à insérer
    champsMatArticles = ["codeArticle", "libelle", "prix1", "prix2", "typeLigne",
                         "condition", "modeCalcul"]
    lignesModel = []  # modèle permet de déterminer les articles qui résulteraient d'une initialisation

    # Récupération des articles niveau famille à ajouter à listeOLV
    req = """SELECT matArticles.artCodeArticle, matArticles.artLibelle, matArticles.artPrix1, 
                    matArticles.artPrix2, matArticles.artCodeBlocFacture, 
                    matArticles.artConditions, matArticles.artModeCalcul
            FROM matArticles
            WHERE artNiveauFamille = 1 AND (matArticles.artCodeArticle LIKE '$%%')
            GROUP BY matArticles.artCodeArticle, matArticles.artLibelle, matArticles.artPrix1, 
                    matArticles.artPrix2, matArticles.artCodeBlocFacture, 
                    matArticles.artConditions, matArticles.artModeCalcul
            ;"""
    DB.ExecuterReq(req, MsgBox="AppelArticles")
    recordset = DB.ResultatReq()

    if len(recordset) > 0:
        # Ajoute le contenu de recordset à listeOLV avec étape intermédiaire en liste de dictionnaires
        for item in recordset:
            i = 0
            ligne = {}
            for champ in champsMatArticles:
                ligne[champ] = item[i]
                i = i + 1
            # pour article cotisation, inclusion de l'année dans le libellé
            i = ligne["libelle"].upper().find("COTIS")
            if i != -1:
                ligne["libelle"] += " " + str(annee)
            ligne["ordre"] = 100 + i
            ligne["origine"] = "articles"
            lignesModel.append(Track(ligne))
    lignesModel = Multilignes(lignesModel, dictDonnees)
    # Parrainages: renseigner les inscriptions parrainées dans la piece en cours de modif
    lstArtParr = []
    lstInscrParr = []
    if 'dicParrainages' in list(dictDonnees.keys()):
        for (inscr, dicParr) in list(dictDonnees['dicParrainages'].items()):
            if not dicParr['IDligneParrain']: continue
            # seules les IDlignes de la pièce en cours sont renseignées ds dicParr
            lstInscrParr.append(inscr)
            lstArtParr.append(dicParr['codeArticle'])
    for ligne in lignesModel:
        ligne.IDinscription = None
        if ligne.codeArticle in lstArtParr:
            ligne.IDinscription = lstInscrParr[lstArtParr.index(ligne.codeArticle)]
        Calcul(dictDonnees, ligne, lignesModel)
    return lignesModel
    # fin GetArticles

def ColorLignes(listeOLV, dictDonnees):
    # colorisation des lignes
    for obj in listeOLV:
        if 'nature' in dictDonnees and dictDonnees['nature'] in ('FAC', 'AVO'):
            obj.couleur = wx.BLUE
        else:
            # cas des lignes modifiables
            obj.couleur = wx.BLUE

            if obj.codeArticle[0] != '$' or obj.montant != 0:
                # lignes ajoutées ou montant modifié
                obj.couleur = wx.BLACK
            if AvecCalcul(obj) and obj.montant != 0 and (obj.montant - obj.montantCalcul) != 0:
                # le calcul a été forcé à un autre montant
                obj.couleur = wx.RED
            if AvecCondition(obj) and obj.montantCalcul == 0 and obj.montant != 0:
                # condition non respectée
                obj.couleur = wx.RED
            if 'faux' in obj.origine and not obj.isChecked:
                # article recalculé et montant antérieur faux
                obj.couleur = wx.Colour(PURPLE)


def InserArticles(listeOLV=[], articles=[], dictDonnees={}):
    # ajout des articles manquant dans olv et retraitement de l'antérieur.
    lstSupprimer = []
    aCond = GestionArticle.ActionsConditions(dictDonnees)
    # pour ajouter l'ordre les lignes dans les tracks et trier pour les calculs
    dicTypesLignes = GetTypesLignes()

    lstArticlesLignes = [x.codeArticle for x in listeOLV]
    # insertion de chaque article
    for article in articles:
        # seulement si condition respectée
        conditionOk = aCond.Condition(article.condition, article.codeArticle)
        if not conditionOk:
            article.montantCalcul = 0
            # test dans les lignes d'une pièce préexistante et non encore facturée
            if not article.codeArticle in lstArticlesLignes:
                continue
        present = False
        # test de présence antérieure pour alimenter la liste à supprimer
        for ligne in listeOLV:
            if not 'ligne' in ligne.origine: continue
            if article.codeArticle[:6] != '$$PARR' \
                    and ligne.codeArticle != article.codeArticle:
                continue

            if float(ligne.montant) == 0.0 and not 'lig' in ligne.origine:
                ligne.montant = ligne.montantCalcul
            # match article déja présent et corrige les montants calculés dans ligne
            pres, suppr, brk = GestionArticle.ArticlePreExist(article, ligne, dictDonnees)
            if suppr:
                lstSupprimer.append(ligne)
            if pres:
                present = True

        if article.typeLigne in list(dicTypesLignes.keys()):
            article.ordre = dicTypesLignes[article.typeLigne]
        else:
            article.ordre = 99
        if not present:
            article.force = "OUI"
            listeOLV.append(article)

    # suppression des anciennes lignes
    for ligne in lstSupprimer:
        if ligne in listeOLV:
            listeOLV.remove(ligne)
    return
    # fin InserArticles

def IxItem(obj, objects):
    ix = None
    if objects and obj in objects:
        ix = objects.index(obj)
    return ix

# -----------------------------------------------------------------------------------

class Track(object):
    def __init__(self, track):
        # Transformation d'un dictionnaire partiel ou non en objet pour modelObjects
        montant = 0
        for champ in list(track.keys()):
            setattr(self, champ, track[champ])
        if "libelleArticle" in list(track.keys()):
            self.libelleArticle = track["libelleArticle"]
        else:
            self.libelleArticle = track["libelle"]
        if track["origine"] == "articles":
            self.prixUnit = round(track["prix1"], 4)
            self.quantite = 1
            montant = 0
            self.prixUnit = track["prix1"]
            self.saisie = False
        if track["origine"] == "lignes":
            self.prixUnit = round(track["prixUnit"], 4)
            self.quantite = track["quantite"]
            self.saisie = True
            montant = track["montant"]
        if self.prixUnit == None: self.prixUnit = 0
        if self.quantite == None: self.quantite = 0
        self.montantCalcul = round(self.prixUnit * self.quantite, 2)
        self.montant = float(montant)
        self.quantite = float(self.quantite)
        if self.montant == round(self.quantite * self.prixUnit, 2):
            self.saisie = False
        self.montant = round(self.montant, 2)
        self.montantCalcul = round(self.montantCalcul, 2)
        if "force" in track:
            self.force = track["force"]
        else:
            self.force = None
        self.isChecked = None
        self.oldValue = montant
        if not hasattr(self,'oldLibelle'):
            self.oldLibelle = "none"
        self.oldLibelle = track['libelle']
        self.couleur = None

    # fin Track

class CTRL_Solde(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, id=-1, name="panel_solde",
                          style=wx.SUNKEN_BORDER | wx.TAB_TRAVERSAL,
                          size=(100, 40))
        self.parent = parent

        # Solde du compte
        self.ctrl_solde = wx.StaticText(self, -1, "0.00 %s " % SYMBOLE)
        font = wx.Font(11, wx.SWISS, wx.NORMAL, wx.BOLD)
        self.ctrl_solde.SetFont(font)

        # Layout
        self.grid_sizer = wx.FlexGridSizer(rows=1, cols=1, vgap=5, hgap=5)
        self.grid_sizer.Add(self.ctrl_solde, 1,
                            wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL | wx.ALL, 10)
        self.SetSizer(self.grid_sizer)
        self.grid_sizer.Fit(self)
        self.grid_sizer.AddGrowableCol(0)
        self.grid_sizer.AddGrowableRow(0)
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
        self.Layout()
        self.Refresh()

# ------------------------------------------------------------------------------------

class OLVtarification(ObjectListView):
    # Gestion écran tarification à la fois pour factres et devis en deux écrans
    def __init__(self, parent, DB, IDpayeur, periode, facture=False, *args, **kwds):
        self.DB = DB
        self.name = kwds.pop('name', 'noName')
        self.parent = parent
        self.facture = facture
        self.IDpayeur = IDpayeur
        annee = periode[1].year
        self.lstIDprestationsOrigine = []
        self.lstOLVmodele = []
        ObjectListView.__init__(self, parent, *args, **kwds)
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("familles_factures",
                                                                  "creer") == False:
            GestionDB.MessageBox(self,
                                 "Vous n'avez pas les droits pour créer des factures")
            self.cellEditMode = ObjectListView.CELLEDIT_NONE
        else:
            self.cellEditMode = ObjectListView.CELLEDIT_SINGLECLICK
        if facture:
            self.cellEditMode = ObjectListView.CELLEDIT_NONE

        # lecture de pièce présente antérieurement
        self.lastObj = None
        self.listeIDpiecesOrigine = []

        self.dictDonnees = {"IDindividu": 0,
                            "IDfamille": IDpayeur,
                            "IDactivite": 0,
                            "IDgroupe": None,
                            "IDinscription": annee,
                            "db": DB,
                            "annee": annee,
                            "periode": (periode)
                            }

        # Mise en place des checkboxes wx > 3.1 sur listbox
        if not self.facture:
            self.EnableCheckBoxes(enable=True)
            # Bind the checkbox toggle event
            self.Bind(wx.EVT_LIST_ITEM_CHECKED, self.OnItemChecked)
            self.Bind(wx.EVT_LIST_ITEM_UNCHECKED, self.OnItemUnchecked)
        # fin init

    def InitModel(self):
        annee = self.parent.annee
        # Charge la pièce famille existante et non encore facturée
        lignes999 = GetLignes999(self, annee,self.DB)
        lignesPieces = []
        if lignes999:
            self.dictDonnees["origine"] = "modif"
            lignesPieces = NormaliseLignes(lignes999)
        else:
            self.dictDonnees["origine"] = "ajout"

        self.dictDonnees["lignes_piece"] = lignesPieces
        self.dictDonnees["lignes_pieceOrigine"] = [x for x in lignesPieces]
        self.dictDonnees['lstIDprestationsOrigine'] = self.lstIDprestationsOrigine

        # composition du listView avec complémentation par les articles communs
        listeOLV = []
        # on insère d'abord la piece999 complétées des attributs de l'article original
        if (self.dictDonnees["origine"] == "modif"):
            listeOLV = self.EnrichirDonnees(self.dictDonnees["lignes_piece"])

        # une reprise conserve l'existant PROVISOIREMENT avant constat d'erreur
        for obj in listeOLV:
            obj.force = "OUI"
            obj.couleur = wx.GREEN # pour repère débuggage

        # puis on ajoute les articles manquants
        if not self.facture:
            listeArticles = GetArticles(annee, self.dictDonnees)
            InserArticles(listeOLV, listeArticles, self.dictDonnees)

        # Colorisation des lignes factures
        if self.facture:
            # Pour les devis c"est chaque calcul qui formate les lignes
            ColorLignes(listeOLV, self.dictDonnees)

        # le listeOLV a vocation pour SetObjects
        self.listeOLV = sorted(listeOLV, key=attrgetter('ordre'))

        self.SetObjects(self.listeOLV)

    def InitObjectListView(self):

        def rowFormatter(listItem, track):
            if hasattr(track, 'couleur'):
                listItem.SetTextColour(track.couleur)

        # ouvre les autorisations de modif devis
        if not self.facture:
            if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
                    "familles_factures",
                    "creer") == True:
                self.cellEditMode = ObjectListView.CELLEDIT_SINGLECLICK

        # Couleur en alternance des lignes
        self.oddRowsBackColor = "#F0FBED"
        self.evenRowsBackColor = wx.Colour(255, 255, 255)
        self.useExpansionColumn = True

        liste_Colonnes = [
            ColumnDefn("Code", "center", 120, "codeArticle", typeDonnee="texte",
                       isEditable=False),
            ColumnDefn("Libelle (libelles modifiables)", "left", 300, "libelle",
                       typeDonnee="texte", isSpaceFilling=True),
            ColumnDefn("Qté", "right", 50, "quantite", typeDonnee="montant",
                       stringConverter=FmtXd),
            ColumnDefn("PxUn", "right", 70, "prixUnit", typeDonnee="montant",
                       stringConverter=Fmt2d, isEditable=False),
            ColumnDefn("Calculé", "right", 90, "montantCalcul", typeDonnee="montant",
                       stringConverter="%.2f", isEditable=False),
            ColumnDefn("Forcé", "right", 90, "montant", typeDonnee="montant",
                       stringConverter=Fmt2d),
        ]

        self.rowFormatter = rowFormatter
        self.SetColumns(liste_Colonnes)
        self.SetEmptyListMsg(_("Aucune ligne trouvée"))
        self.SetEmptyListMsgFont(wx.FFont(11, wx.DEFAULT, faceName="Tekton"))

        self.InitModel()
        # fin InitObjectListView

    def EnrichirDonnees(self, ldLignes, forcer=True):
        # Complete les articles simples en lignes-piece pour les champs liste2 liés à l'article, puis met en track
        DB = self.dictDonnees['db']
        donnees = []
        liste2 = ["prix1", "prix2", "typeLigne", "condition", "modeCalcul","libelleArticle"]
        # Transposition des données SQL avec les noms de champs utilisés en track
        if ldLignes:
            for dictLigne in ldLignes:
                # recherche de l'article pour compléter les infos de la ligne stockée
                dicDonnees = {}
                for champLigne in list(dictLigne.keys()):
                    dicDonnees[champLigne] = dictLigne[champLigne]
                champs = ["codeArticle", "libelleArticle", "prix1", "prix2", "typeLigne",
                          "condition", "modeCalcul"]

                req = """
                    SELECT matArticles.artCodeArticle, matArticles.artLibelle, matArticles.artPrix1, 
                           matArticles.artPrix2, matArticles.artCodeBlocFacture, matArticles.artConditions, 
                           matArticles.artModeCalcul
                    FROM matArticles
                    WHERE (matArticles.artCodeArticle = '%s');
                    """ % dicDonnees["codeArticle"]
                retour = DB.ExecuterReq(req, MsgBox="ExecuterReq")
                if retour != "ok":
                    DB.AfficheErr(self, retour)
                    continue
                recordset = DB.ResultatReq()
                if len(recordset) == 0:
                    # article non trouvé car multi et ajouté sur les deux derniers caractère
                    req = """SELECT matArticles.artCodeArticle, matArticles.artLibelle, matArticles.artPrix1, 
                                    matArticles.artPrix2, matArticles.artCodeBlocFacture,matArticles.artConditions, 
                                    matArticles.artModeCalcul
                        FROM matArticles
                        WHERE (matArticles.artCodeArticle LIKE '%s');
                        """ % (dicDonnees["codeArticle"][0:-2] + "%%")
                    retour = DB.ExecuterReq(req, MsgBox="ExecuterReq")
                    if retour != "ok": DB.AfficheErr(self, retour)
                    recordset = DB.ResultatReq()
                for champLigne in liste2:
                    if len(recordset) > 0:
                        ix = champs.index(champLigne)
                        dicDonnees[champLigne] = recordset[0][ix]
                    else:
                        dicDonnees[champLigne] = None
                dicTypesLignes = GetTypesLignes()
                if dicDonnees['typeLigne'] in list(dicTypesLignes.keys()):
                    dicDonnees['ordre'] = dicTypesLignes[dicDonnees['typeLigne']]
                else:
                    dicDonnees['ordre'] = 99
                donnees.append(dicDonnees)
        # Transpose les données de type listes avec clés en objets tracks avec attributs pour OLV
        listeOLV = []
        aCond = GestionArticle.ActionsConditions(self.dictDonnees)
        for item in donnees:
            item["origine"] = "lignes"
            cond = False
            if forcer:
                cond = True
                item["force"] = "OUI"
            else:
                if aCond.Condition(item["condition"], item["codeArticle"]):
                    cond = True
            if cond:
                track = Track(item)
                track.donnees = item
                listeOLV.append(track)
        return listeOLV
        # fin EnrichirDonnees

    # Event handlers for mouse clicks
    def OnToggle(self,event,check):
        # check and uncheck consequences
        ix = event.GetIndex()
        obj = self.modelObjects[ix]
        if not check:
            obj.montant = obj.oldValue
            obj.libelle = obj.oldLibelle
        self.parent.CalculSolde()
        self.RefreshObject(obj)

    # Evènement coche soit par souris, soit par fonction SetCheckState
    def OnItemChecked(self, event):
        self.OnToggle(event,True)

    def OnItemUnchecked(self, event):
        self.OnToggle(event,False)

    def SetCheckState(self,obj, state):
        ix = self.modelObjects.index(obj)
        self.CheckItem(ix,state)

    def GetCheckedObjects(self):
        objects = self.GetObjects()
        return[ x for x in objects if x.isChecked]


class DlgTarification(wx.Dialog):
    def __init__(self, parent, dictDonneesParent):
        self.parent = parent
        self.total = 0.0
        self.rappel = False
        wx.Dialog.__init__(self, None, -1,
                           style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER | wx.MAXIMIZE_BOX,
                           size=(800, 600))
        self.dictDonneesParent = dictDonneesParent
        self.DB = GestionDB.DB()
        if 'annee' in dictDonneesParent:
            dateAnnee = datetime.date(dictDonneesParent['annee'], 1, 1)
        else:
            dateAnnee = None

        if not 'IDactivite' in self.dictDonneesParent:
            self.dictDonneesParent['IDactivite'] = None

        periode = GestionArticle.AnneeAcad(self.DB,
                                                IDactivite=dictDonneesParent[
                                                    "IDactivite"],
                                                date=dateAnnee)
        (self.exerciceDeb, self.exerciceFin) = periode
        self.annee = self.exerciceFin.year
        self.IDcompte_payeur = dictDonneesParent["IDcompte_payeur"]

        # Verrouillage utilisateurs
        self.rw = True
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
                "individus_inscriptions",
                "creer") == False:
            self.rw = False

        # Pose les titres
        self.SetTitle(_("DLG_PrixFamille"))

        self.payeur = f"{self.IDcompte_payeur} {self.DB.GetNomIndividu(self.IDcompte_payeur)}"
        titre = "NIVEAU FAMILLE "
        self.ctrl_bandeau = CTRL_Bandeau.Bandeau(self, titre=titre,
                                                 texte=self.payeur,
                                                 hauteurHtml=10,
                                                 nomImage="Images/22x22/Smiley_nul.png")

        self.SetBandeau(annee=self.annee)

        # conteneur des données
        self.staticbox_facture = wx.StaticBox(self, -1, _("Déjà facturé..."))
        self.staticbox_nonFacture = wx.StaticBox(self, -1,
                                                 _("Non facturé modifiable ..."))
        self.resultsOlv = OLVtarification(self, self.DB, self.IDcompte_payeur,
                                          periode,
                                          facture=False, id=1,
                                          name="OLV_Saisie",
                                          style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.LC_HRULES | wx.LC_VRULES)
        self.ctrl_recherche = CTRL_Outils(self, listview=self.resultsOlv)
        self.resultsOlvFact = OLVtarification(self, self.DB, self.IDcompte_payeur,
                                              periode,
                                              facture=True, id=2,
                                              name="OLV_Facture",
                                              style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.LC_HRULES | wx.LC_VRULES)
        self.ctrl_solde = CTRL_Solde(self)
        self.ctrl_solde.SetSolde(1000)

        # pour conteneur des actions en pied d'écran
        self.pied_staticbox = wx.StaticBox(self, -1, _("Actions"))
        self.hyper_tout = Hyperlien(self, label=_("Tout cocher"),
                                    infobulle=_("Cliquez ici pour tout cocher"),
                                    URL="tout")
        self.hyper_rien = Hyperlien(self, label=_("Tout décocher"),
                                    infobulle=_("Cliquez ici pour tout décocher"),
                                    URL="rien")
        self.hyper_anneeprec = Hyperlien(self, label=_("Année Précédente"), infobulle=_(
            "Cliquez ici pour choisir un autre exercice"),
                                         URL="anneeprec")
        self.hyper_anneesuiv = Hyperlien(self, label=_("| Année Suivante"), infobulle=_(
            "Cliquez ici pour choisir un autre exercice"),
                                         URL="anneesuiv")
        self.hyper_ajoutArticle = Hyperlien(self, label=_("| Ajouter Ligne"),
                                            infobulle=_("Ajouter un article"),
                                            URL="article")
        self.hyper_ajoutReinitialiser = Hyperlien(self, label=_("| Réinitialiser"),
                                                  infobulle=_(
                                                      "Pour oublier une saisie antérieure"),
                                                  URL="reinitialiser")
        self.bouton_oj = CTRL_Bouton_image.CTRL(self, texte=_("Autre\nInscription"),
                                                cheminImage="Images/32x32/Fleche_gauche.png")
        self.bouton_ok = CTRL_Bouton_image.CTRL(self, texte=_("OK pour\nFacturation"),
                                                cheminImage="Images/32x32/Fleche_droite.png")
        self.bouton_annuler = CTRL_Bouton_image.CTRL(self, texte=_("Abandon\nFamille"),
                                                     cheminImage="Images/32x32/Annuler.png")
        if not 'individu' in self.dictDonneesParent['lanceur']:
            self.bouton_oj.Enable(False)
        self.__set_properties()
        self.Sizer()

        self.resultsOlv.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnSelected)
        self.resultsOlv.Bind(wx.EVT_TEXT, self.OnTexte)
        self.resultsOlv.Bind(wx.EVT_LIST_KEY_DOWN, self.OnKeyDown)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonOj, self.bouton_oj)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonOk, self.bouton_ok)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAnnuler, self.bouton_annuler)
        self.SetExercice(self.annee)
        # fin de init

    def ListeDict(self, olv):
        # Permet de récupérer le format liste de dictionnaires pour les lignes de la pièce
        objects = olv.GetObjects()
        ldLignesPiece = []
        for obj in objects:
            if (not hasattr(obj,'isChecked')) or obj.isChecked :
                dictTemp = {}
                if hasattr(obj, "donnees"):
                    dictTemp = obj.donnees
                dictTemp["codeArticle"] = obj.codeArticle
                dictTemp["libelle"] = obj.libelle
                if obj.quantite == None:
                    obj.quantite = 1
                dictTemp["quantite"] = obj.quantite
                if obj.quantite != 0.0:
                    dictTemp["prixUnit"] = round(obj.montantCalcul / obj.quantite, 4)
                else:
                    dictTemp["prixUnit"] = 0.0
                dictTemp["montant"] = obj.montant
                ldLignesPiece.append(dictTemp)
        return ldLignesPiece

    def SetExercice(self, annee):
        # cas d'un deuxième passage après init, l'année a changé
        if annee != self.exerciceFin.year:
            dte = datetime.date(annee, self.exerciceFin.month, self.exerciceFin.day)
            periode = GestionArticle.AnneeAcad(self.DB, IDactivite=None, date=dte)
            self.exerciceDeb, self.exerciceFin = periode

            # mise à jour de l'olv modifiable
            self.resultsOlv.exerciceFin = self.exerciceFin
            self.resultsOlv.dictDonnees['annee'] = annee
            del self.resultsOlv.dictDonnees['dicCumul']

            # mise à jour du bandeau et des factures
            self.SetBandeau(annee)
            self.MajOlvFact(periode)

        self.obj = None
        self.lastObj = None

        self.resultsOlv.InitObjectListView()
        self.resultsOlvFact.InitObjectListView()

        self.dataorigine = [copy.deepcopy(x) for x in self.resultsOlv.listeOLV]
        self.DeduitDejaFacture()
        self.PreCoche() # provoque des recalculs par l'évènement Check de listbox
        self.CalculSolde()
        return

    def MajOlvFact(self, periode):
        exerciceDeb, exerciceFin = periode
        # mise à jour de l'OLV factures
        self.resultsOlvFact.exerciceFin = exerciceFin
        self.resultsOlvFact.annee = exerciceFin.year
        self.resultsOlvFact.periode = periode
        self.resultsOlvFact.InitObjectListView()

    def SetBandeau(self,annee):
        texte = "Payeur : " + self.payeur + " - Période du " \
                + self.exerciceDeb.strftime(
            "%d/%m/%Y") + " au " + self.exerciceFin.strftime("%d/%m/%Y")
        titre = "NIVEAU FAMILLE - année %s" % str(annee)
        self.ctrl_bandeau.ctrl_titre.SetLabel(titre)
        self.ctrl_bandeau.ctrl_intro.SetPage(texte)

    def __set_properties(self):
        if not self.rw:
            self.bouton_ok.Enable(False)
            self.resultsOlv.Enable(False)
            self.hyper_ajoutArticle.Enable(False)
            self.hyper_ajoutReinitialiser.Enable(False)
            self.hyper_rien.Enable(False)
            self.hyper_annee.Enable(False)
            self.hyper_tout.Enable(False)
        self.bouton_ok.SetToolTip(_("Chaîner sur la synthèse famille et la facturation"))
        self.bouton_oj.SetToolTip(
            _("Retour sur les inscriptions, sans passer par la facturation"))
        self.bouton_annuler.SetToolTip(
            _("Cliquez ici pour ignorer les modifs du niveau famille"))
        self.ctrl_solde.SetToolTip(
            _("Ne Saisissez pas le montant ici, mais sur les lignes cochées"))
        self.ctrl_solde.ctrl_solde.SetToolTip(
            _("Ne Saisissez pas le montant ici, mais sur les lignes cochées"))

    def Sizer(self):
        self.grid_sizer = wx.FlexGridSizer(rows=5, cols=1, vgap=5, hgap=5)
        self.grid_sizer.Add(self.ctrl_bandeau, 0, wx.EXPAND, 0)
        staticsizer_facture = wx.StaticBoxSizer(self.staticbox_facture, wx.VERTICAL)
        grid_sizer_facture = wx.FlexGridSizer(rows=2, cols=1, vgap=1, hgap=10)

        grid_sizer_facture.Add(self.resultsOlvFact, 1, wx.EXPAND, 0)
        grid_sizer_facture.AddGrowableCol(0)
        grid_sizer_facture.AddGrowableRow(0)
        staticsizer_facture.Add(grid_sizer_facture, 1, wx.RIGHT | wx.EXPAND, 5)
        self.grid_sizer.Add(staticsizer_facture, 1, wx.EXPAND, 0)

        staticsizer_nonFacture = wx.StaticBoxSizer(self.staticbox_nonFacture, wx.VERTICAL)
        grid_sizer_nonFacture = wx.FlexGridSizer(rows=2, cols=1, vgap=1, hgap=10)

        grid_sizer_nonFacture.Add(self.resultsOlv, 0, wx.EXPAND, 0)
        grid_sizer_nonFacture.Add(self.ctrl_recherche, 0, wx.EXPAND, 0)
        grid_sizer_nonFacture.AddGrowableCol(0)
        grid_sizer_nonFacture.AddGrowableRow(0)
        staticsizer_nonFacture.Add(grid_sizer_nonFacture, 1, wx.RIGHT | wx.EXPAND, 5)
        self.grid_sizer.Add(staticsizer_nonFacture, 1, wx.EXPAND, 0)

        pied_staticboxSizer = wx.StaticBoxSizer(self.pied_staticbox, wx.VERTICAL)
        grid_sizer_pied = wx.FlexGridSizer(rows=1, cols=7, vgap=3, hgap=3)

        grid_sizer_cocher = wx.FlexGridSizer(rows=3, cols=1, vgap=1, hgap=10)
        grid_sizer_cocher.Add(self.hyper_tout, 0, wx.ALL, 0)
        grid_sizer_cocher.Add(self.hyper_rien, 0, wx.ALL, 0)
        grid_sizer_cocher.Add(self.hyper_anneeprec, 0, wx.ALL, 0)
        grid_sizer_pied.Add(grid_sizer_cocher, 1, wx.EXPAND, 0)

        grid_sizer_outils = wx.FlexGridSizer(rows=3, cols=1, vgap=1, hgap=10)
        grid_sizer_outils.Add(self.hyper_ajoutArticle, 0, wx.ALL, 0)
        grid_sizer_outils.Add(self.hyper_ajoutReinitialiser, 0, wx.ALL, 0)
        grid_sizer_outils.Add(self.hyper_anneesuiv, 0, wx.ALL, 0)
        grid_sizer_pied.Add(grid_sizer_outils, 1, wx.EXPAND, 0)

        grid_sizer_pied.Add(self.bouton_oj, 0, 0, 0)
        grid_sizer_pied.Add(self.bouton_ok, 0, 0, 0)
        grid_sizer_pied.Add(self.bouton_annuler, 0, 0, 0)
        grid_sizer_pied.Add(self.ctrl_solde, 0, 0, 0)
        grid_sizer_pied.AddGrowableCol(1)

        pied_staticboxSizer.Add(grid_sizer_pied, 1, wx.EXPAND, 5)
        self.grid_sizer.Add(pied_staticboxSizer, 1, wx.EXPAND, 5)

        # self.grid_sizer.Fit(self)
        self.grid_sizer.AddGrowableRow(1)
        self.grid_sizer.AddGrowableRow(2)
        self.grid_sizer.AddGrowableCol(0)
        self.SetMinSize((650, 550))
        self.SetSizer(self.grid_sizer)
        self.Layout()
        self.CenterOnScreen()

    def ChoixNatureOrigine(self, dictDonnees):
        if dictDonnees["origine"] == "modif":
            pGest = GestionPieces.Forfaits(self, self.DB)
            ddPieces = pGest.GetListePiecesEnCours(self.DB, dictDonnees["IDfamille"])
            del pGest
            nature = dictDonnees['nature']
            lstOptions = []
            for IDpiece, dictPiece in ddPieces.items():
                if nature != dictPiece['pieNature']:
                    nature = False
                    if not dictPiece['pieNature'] in lstOptions:
                        lstOptions.append(dictPiece['pieNature'])
            if not nature:
                # des choix sont possibles, car plusieurs natures dans les pièces
                if dictDonnees['nature'] and not dictDonnees['nature'] in lstOptions:
                    lstOptions.append(dictDonnees['nature'])
                listeBoutons = []
                for code in lstOptions:
                    txt = ""
                    if code == "DEV":
                        txt = "Devis sans réservation"
                    elif code == "RES":
                        txt = "Réservation sans prestation"
                    elif code == "COM":
                        txt = "Commande due par le client"
                    listeBoutons.append((code, txt))
                if len(listeBoutons) > 0:
                    titre = "Quelle nature pour cette pièce famille, choisissez!"
                    intro = "Cliquez sur la nature souhaitée"
                    dlg = DLG_Choix.Dialog(self, titre=titre, listeBoutons=listeBoutons,
                                           intro=intro)
                    ret = dlg.ShowModal()
                    dlg.Destroy()
                    if ret != wx.ID_CANCEL:
                        nature = listeBoutons[ret][0]
            return nature
        else:
            # une création n'a pas de nature d'origine
            return False

    def Final(self):
        self.CalculSolde()
        self.IDuser = self.DB.IDutilisateurActuel()
        dictDonnees = self.resultsOlv.dictDonnees
        lstLignesPiece = self.ListeDict(self.resultsOlv)
        fGest = GestionInscription.Forfaits(self, DB=self.DB)
        lstNonNull = [x for x in lstLignesPiece if
                      (x["prixUnit"] * x["quantite"]) + x["montant"] != 0]

        # détermination de la prochaine nature
        if 'individu' in self.dictDonneesParent['lanceur'] and (
        not 'avoir' in self.dictDonneesParent[
            'lanceur']) and "nature" in self.dictDonneesParent:
            # nature héritée de l'activité si non avoir
            dictDonnees['nature'] = self.dictDonneesParent["nature"]
        if (not 'nature' in dictDonnees) or not dictDonnees['nature']:
            dictDonnees['nature'] = "COM"
        nature = dictDonnees['nature']
        ret = self.ChoixNatureOrigine(dictDonnees)
        if ret:
            # reprise de la nature de la pièce qui préexistait
            nature = ret
            dictDonnees["nature"] = nature

        if dictDonnees["origine"] == "ajout" and len(lstNonNull) > 0:
            # Enregistre dans Pieces
            dDonnees = fGest.AjoutPiece999(self, dictDonnees["IDfamille"],
                                           self.IDcompte_payeur,
                                           self.exerciceFin, nature)

            dictDonnees.update(dDonnees)
            dictDonnees["lstIDprestationsOrigine"].append(dictDonnees["IDprestation"])
        dictDonnees["lignes_piece"] = NormaliseLignes(lstNonNull)

        if len(lstLignesPiece) > 0:
            if 'dicParrainages' in list(self.resultsOlv.dictDonnees.keys()):
                dictDonnees['dicParrainages'] = self.resultsOlv.dictDonnees[
                    'dicParrainages']

        # enregistrement de la pièce et de ses prolongements prestation
        ret = fGest.ModifiePiece999(self, dictDonnees, nature)
        self.dictDonnees = dictDonnees
        del fGest
        return ret
        # fin Final

    def Sortie(self, wxID=wx.ID_OK):
        self.DB.Close()
        self.EndModal(wxID)

    def OnBoutonOj(self, event):
        self.Sortie()

    def OnBoutonOk(self, event):
        tracks = self.resultsOlv.GetCheckedObjects()
        valide = True
        if len(tracks) > 0:
            IDnumPiece = None
            if self.resultsOlv.dictDonnees["origine"] == "modif":
                IDnumPiece = self.resultsOlv.dictDonnees["IDnumPiece"]
            valide1 = DLG_ChoixTypePiece.ValideSaisie(tracks, testSejour=False)
            valide2 = DLG_ChoixTypePiece.DoubleLigne(tracks, self.annee, self.DB,
                                                     IDnumPiece=IDnumPiece,
                                                     IDfamille=self.IDcompte_payeur)
            lstAno = [x for x in tracks if x.couleur == wx.RED]
            if lstAno :
                mess = "Etes-vous sûr du montant des lignes en rouge!\n\n"
                mess += "Vous pouvez les remplacer en enlevant le montant forcé, puis les recréer les montants souhaités avec un autre article non calculé\n\n"
                mess += "Faut-il valider quand même ?"
                ret = wx.MessageBox(mess, "Correction souhaitée",style= wx.ICON_INFORMATION | wx.YES_NO)
                if ret == wx.YES:
                    lstAno = None
            valide = valide1 and valide2 and not lstAno
        if valide:
            # lancer la synthèse
            ret = self.Final()
            idend = wx.ID_ABORT
            if 'facturation' in self.dictDonneesParent['lanceur']:
                # On continue le traitement iniié par DLG_Facturation_piece
                idend = wx.ID_OK
            elif 'avoir' in self.dictDonneesParent['lanceur']:
                # Cas du complément famille lié à un avoir
                if ret == "ok":
                    # après avoir validé la pièce en commande on la facture avec le numéro d'avoir de l'activité mis par Final()
                    lstLignesPiece = self.ListeDict(self.resultsOlv)
                    mtt = 0.0
                    for ligne in lstLignesPiece:
                        ligne["montant"] = round(ligne["montant"], 2)
                        # calcul du total avec lignes cochées et priorité aux montants saisis
                        if ligne["montant"] != 0.0:
                            mtt += abs(ligne["montant"])
                        else:
                            mtt += abs(Nz(ligne["quantite"]) * Nz(ligne["prixUnit"]))
                    pGest = GestionPieces.Forfaits(self, self.DB)
                    pGest.AugmenteFacture(self.dictDonneesParent["noAvoir"], -mtt,
                                          self.dictDonnees["IDprestation"])
                    dlg = DLG_FacturationPieces.Dialog(self, self.IDcompte_payeur)
                    dlg.ShowModal()
                    del dlg
                    del pGest
                    idend = wx.ID_OK
            else:
                # Simple appel de la facturation cas général pour famille ou individu
                dlg = DLG_FacturationPieces.Dialog(self, self.IDcompte_payeur)
                dlg.ShowModal()
                del dlg
                idend = wx.ID_OK
            self.Sortie(idend)

    def OnBoutonAnnuler(self, event):
        self.Sortie(wx.ID_ABORT)
        return True

    def CocheTout(self, state):
        objects = self.resultsOlv.GetObjects()
        for obj in objects:
            self.resultsOlv.SetCheckState(obj, state)
        self.RazUnchecked()
        self.CalculSolde()
        self.resultsOlv.RefreshObjects(objects)

    def ChangeAnnee(self, pas):
        self.annee += pas
        self.SetExercice(self.annee)

    def AjouteLigne(self, typeLigne):
        # appel du programme permettant un choix d'article
        if typeLigne == "article":
            dlg = DLG_ChoixLigne.DlgChoixArticle(self)
            if dlg.ShowModal() == wx.ID_OK:
                # incorpation des articles dans l'olv
                olv_articles = dlg.GetOlv()
                ldLignes = self.ListeDict(olv_articles)
                self.ActionAjout(ldLignes)
            del dlg

    def ActionAjout(self, ldLignes):
        # Ajout d'une ligne
        ldLignesPlus = self.resultsOlv.EnrichirDonnees(ldLignes, forcer=True)
        if len(ldLignesPlus) > 0:
            lstCodeArt = []
            for ligne in ldLignesPlus:
                # l'origine ajoutLigne déclenchera la condition MultiFam dans le calcul article calRedFam et donc génèrera les lignes
                ligne.origine = "ajoutLigne"
                ligne.force = "OUI"
                ligne.saisie = False
                self.resultsOlv.listeOLV.append(ligne)

                lstCodeArt.append(ligne.codeArticle)
                ligne.isChecked = True
            dictConditionsMulti = {}
            for ligne in self.resultsOlv.listeOLV:
                for codeArt in lstCodeArt:
                    if codeArt == ligne.codeArticle[:len(codeArt)]:
                        # Composition des lignes multi
                        if ligne.condition != None:
                            if len(ligne.condition) > 5:
                                if ligne.condition[0:5] in ["Multi", "Parra"]:
                                    if ligne.condition not in dictConditionsMulti:
                                        dictConditionsMulti[
                                            ligne.condition] = ligne.codeArticle
            if len(list(dictConditionsMulti.keys())) > 0:
                aCond = GestionArticle.ActionsConditions(self.resultsOlv.dictDonnees)
                for condition in list(dictConditionsMulti.keys()):
                    aCond.ConditionMulti(condition, dictConditionsMulti[condition],
                                         self.resultsOlv.listeOLV)
            self.resultsOlv.SetObjects(self.resultsOlv.listeOLV)
            for ligne in self.resultsOlv.listeOLV:
                ix = self.resultsOlv.listeOLV.index(ligne)
                self.resultsOlv.CheckItem(ix, True)
            self.CalculSolde()
            self.resultsOlv.Refresh()
        # fin ActionAjout

    def TestReprise(self):
        # Vérif du calcul réactualisé des articles
        dictDonnees = self.resultsOlv.dictDonnees
        # Recueil des données
        def getDdLines(lignes):
            ddLines = {}
            for x in lignes:
                if Nz(x['montant']) != 0:
                    montant = Nz(x['montant'])
                else: montant = x['montantCalcul']
                if x['codeArticle'][:6] in ddLines:
                    ddLines[x['codeArticle'][:6]]['mtt'] += montant
                else:
                    ddLines[x['codeArticle'][:6]] = {'article':x['codeArticle'][:6],
                                                  'libel':x['libelle'],
                                                  'mtt':montant}
            return ddLines
        ddLinesOrigin = getDdLines(dictDonnees['lignes_pieceOrigine'])
        tracks = self.resultsOlv.GetObjects()
        # seules les lignes checkées seront retenues
        ddLinesActual = getDdLines([x.__dict__ for x in tracks if x.isChecked])
        lstAnomalies = []
        for key, dic in ddLinesActual.items():
            ano = ""
            if not key in ddLinesOrigin:
                ano = f"Manque {key}: {dic['libel']}, non appelé pour {dic['mtt']} €"
            elif ddLinesOrigin[key]['mtt'] != dic['mtt']:
                montant = ddLinesOrigin[key]['mtt'] - dic['mtt']
                ano = f"Ecart sur {key}: {dic['libel']}, d'un montant de {montant} €"
            if ano:
                lstAnomalies.append(ano)
        return lstAnomalies

    def Reinitialiser(self):
        # Retrouve la situation de départ
        self.SetExercice(self.annee)

    def OnKeyDown(self, event):
        pass

    def OnTexte(self, event):
        # l'évènement OnTexte ne valide pas la saisie, test impossible sur les valeurs de track
        if not self.obj: return
        self.obj.saisie = True

    def OnSelected(self, event):
        if self.obj == None:
            self.obj = self.resultsOlv.GetSelectedObject()
            self.lastBind = "select"
            self.lastLigne = 0
        # une saisie texte a eu lieu des contrôles et actions sont nécessaires
        if self.lastBind == "texte":
            objects = self.resultsOlv.GetObjects()
            i = 0
            for obj in objects:
                if self.lastLigne == i:
                    # la quantité a été modifiée
                    if (self.lastObj.quantite != obj.quantite) and (
                            self.lastObj.codeArticle == obj.codeArticle):
                        if obj.codeArticle:
                            self.modifJours = True
                            self.quantite = obj.quantite
                            self.nbreJours = self.quantite
                    # le zéro saisi en montant doit désactiver la ligne
                    if obj.montant == 0 and self.lastObj.montant != 0:
                        self.resultsOlv.SetCheckState(obj, False)
                    obj.saisie = True
                i += 1
        self.lastBind = "select"
        self.CalculSolde()
        self.obj = self.resultsOlv.GetSelectedObject()

    def CalculSolde(self):
        objects = self.resultsOlv.modelObjects
        # ajout de l'attribut coché
        for obj in objects:
            obj.isChecked = self.resultsOlv.IsItemChecked(IxItem(obj,objects))
        total, mtt = 0, 0
        for obj in sorted(objects, key=attrgetter('ordre')):
            if not obj.isChecked:
                if obj.quantite == 0: obj.quantite = 1
                obj.prixUnit = round(obj.montantCalcul / obj.quantite, 4)
                #obj.montant = 0.0
                obj.saisie = False
                obj.force = "NON"
            # les cochés sont recalculés
            if obj.isChecked:
                obj.montantCalcul = round(obj.prixUnit * obj.quantite, 2)
                if obj.saisie == False:
                    Calcul(self.resultsOlv.dictDonnees, obj, objects)
                if obj.montantCalcul != 0.0:
                    # correctif pour ne pas refacturer deux fois le même article
                    for objfac in self.resultsOlvFact.GetObjects():
                        if objfac.codeArticle == obj.codeArticle:
                            if obj.force == "NON":
                                if objfac.montant == 0:
                                    obj.montantCalcul -= objfac.montantCalcul
                                else:
                                    obj.montantCalcul -= objfac.montant
                # un forçage au même montant que le résultat du calcul n'est plus une spécificité
                if obj.montant == obj.montantCalcul:
                    obj.montant = 0.0
                # calcul du total avec lignes cochées et priorité au montants saisis
                if obj.montant != 0.0:
                    total += obj.montant
                else:
                    total += (obj.montantCalcul)
            obj.montant = round(float(Nz(obj.montant)), 2)
            obj.quantite = float(Nz(obj.quantite))
            obj.prixUnit = round(float(Nz(obj.prixUnit)), 4)
            obj.montantCalcul = round(float(Nz(obj.montantCalcul)), 2)

        self.ctrl_solde.SetSolde(round(total, 2))
        self.total = round(total, 2)
        ColorLignes(objects, self.resultsOlv.dictDonnees)
        self.resultsOlv.RefreshObjects(objects)
        # fin CalculSolde

    def DeduitDejaFacture(self):
        dictCorrige = {}
        dictInFact = {}
        dictInCalc = {}
        def addDic(dic,key,obj):
            # ajoute le montant ou crée la clé dans le dic, si mtt != 0.0
            if obj.montant == 0.0:
                mtt = obj.montantCalcul
            else: mtt = obj.montant
            if mtt == 0.0:
                return
            if key in dic:
                dic[key]['mtt'] += mtt
                dic[key]['articles'].append((obj.codeArticle, mtt))
            else:
                dic[key] = {'mtt':mtt,'articles':[(obj.codeArticle,mtt),]}

        # regroupement des lignes facturées et calculées en devis
        for obj in self.resultsOlvFact.listeOLV:
            addDic(dictInFact,obj.codeArticle[:6],obj)
        for obj in self.resultsOlv.listeOLV:
            # les articles optionnels peuvent être redondants
            if obj.codeArticle[0] != '$':
                continue
            addDic(dictInCalc,obj.codeArticle[:6],obj)
        # recherche doublons
        for key,dic in dictInCalc.items():
            if not key in dictInFact or round(dictInFact[key]['mtt'],2) == 0.0:
                # non facturé ou déjà affecté
                continue
            # présence du déjà facturé
            if dictInFact[key]['mtt'] > 0.0:
                sign = 1
            else: sign = -1
            # négatifs possibles
            mttcortotal = min(sign * dictInFact[key]['mtt'], sign * dictInCalc[key]['mtt'])
            mttcortotal *= sign
            # préparer la réduction à appliquer par article
            for article, mtt in dictInCalc[key]['articles']:
                mttcorr = sign * min(sign * mttcortotal,sign * mtt)
                dictCorrige[article] = mttcorr
                mttcortotal -= mttcorr
                if round(mttcortotal,2) == 0.0:
                    break
            # appliquer la réduction
            for obj in self.resultsOlv.listeOLV:
                if obj.codeArticle in dictCorrige:
                    if obj.montant == 0.0:
                        mtt = obj.montantCalcul
                    else: mtt = obj.montant
                    mttcorr = sign * min(sign * dictCorrige[obj.codeArticle], sign * mtt)
                    if obj.montantCalcul != 0.0:
                        obj.montantCalcul -= mttcorr
                    if obj.montant != 0.0:
                        obj.montant -= mttcorr
                    dictCorrige[obj.codeArticle] -= mttcorr
                    if obj.montant == 0.0 and obj.montantCalcul == 0.0:
                        obj.force = "NON"
                        obj.quantite = 0
        # fin DeduitDejaFacture

    def RazUnchecked(self):
        objects = self.resultsOlv.GetObjects()
        for obj in objects:
            if not obj.isChecked:
                obj.montant = 0
                obj.prixUnit = 0

    def PreCoche(self):
        objects = self.resultsOlv.GetObjects()
        lstActions = []
        for obj in objects:
            lstActions.append((objects.index(obj),obj.force))
        for ix,force in lstActions:
            if force == "OUI":
                self.resultsOlv.SetCheckState(objects[ix], True)
            else:
                self.resultsOlv.SetCheckState(objects[ix], False)
        # différé suite à constat d'interférence liée aux évènements check
        for ix,force in lstActions:
            objects[ix].force = force
            if force == "OUI":
                objects[ix].isChecked = True
            else:
                objects[ix].isChecked = False

        self.resultsOlv.RefreshObjects(objects)

# ------------------------------------------------------------------------------------
class BarreRecherche(wx.SearchCtrl):
    def __init__(self, parent):
        wx.SearchCtrl.__init__(self, parent, size=(-1, -1), style=wx.TE_PROCESS_ENTER)
        self.parent = parent
        self.rechercheEnCours = False

        self.SetDescriptiveText(_("Rechercher un Bloc..."))
        self.ShowSearchButton(True)

        self.listView = self.parent.resultsOlv
        nbreColonnes = self.listView.GetColumnCount()
        self.listView.SetFilter(
            Filter.TextSearch(self.listView, self.listView.columns[0:nbreColonnes]))

        self.SetCancelBitmap(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Interdit.png"),
                                       wx.BITMAP_TYPE_PNG))
        self.SetSearchBitmap(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Loupe.png"),
                                       wx.BITMAP_TYPE_PNG))

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
        txtSearch = self.GetValue().replace("'", "\\'")
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
        if self.URL == "anneesuiv": self.parent.ChangeAnnee(1)
        if self.URL == "anneeprec": self.parent.ChangeAnnee(-1)
        if self.URL == "article": self.parent.AjouteLigne("article")
        if self.URL == "reinitialiser": self.parent.Reinitialiser()
        self.UpdateLink()


# --------------------Lancement de test ----------------------------------------------
if __name__ == "__main__":
    app = wx.App(0)

    """dictDonnees = {'IDcompte_payeur': 9810, 'IDfamille': 9810, 'lanceur': 'famille'}"""
    dictDonnees = {'IDactivite': 0, 'IDcompte_payeur': 9810, 'annee': 2026, 'lanceur': 'facturation', 'pieIDinscription': 2026}
    dlg = DlgTarification(None, dictDonnees, )
    # lancement simulé modif nature pièce
    try:
        lstAnomalies = dlg.TestReprise()
        if lstAnomalies:
            mess = "Anomalies dans la pièce 'Niveau famille'\n\n"
            for txt in lstAnomalies:
                mess += txt + "\n"
            mess += "\nLe niveau famille semble facturé anormalement, Voulez vous consulter ou corriger?"
            ret = wx.MessageBox(mess, "RECALCUL FAMILLE", style=wx.YES_NO | wx.ICON_WARNING)
            if ret == wx.YES:
                ret = dlg.ShowModal()
            if ret in (wx.ID_OK,):
                ok = True
        else:
            print("Aucune anomalie")
            ret = dlg.ShowModal()
    except Exception as err:
        print("pas de paramètres suffisant pour tests, lancé direct\n",err)
        # lancement original direct 'famille'
        if dlg.ShowModal() == wx.ID_OK:
            print("OKfin_main")
        else:
            print("KC")
    app.MainLoop()
