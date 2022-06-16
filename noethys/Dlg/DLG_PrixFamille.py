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
from operator import attrgetter
import wx.lib.agw.hyperlink as Hyperlink
from Ctrl.CTRL_ObjectListView import FastObjectListView, ColumnDefn,Filter, CTRL_Outils
import copy
from Ctrl import CTRL_Bouton_image
from Ctrl import CTRL_Bandeau
from Utils import UTILS_Config
from Utils import UTILS_Utilisateurs
import GestionDB
from Dlg import DLG_ChoixLigne
from Dlg import DLG_FacturationPieces
from Dlg import DLG_ValidationPiece
from Gest import GestionArticle
from Gest import GestionInscription
from Gest import GestionPieces
from Utils.UTILS_Decimal import FloatToDecimal as FloatToDecimal

SYMBOLE = UTILS_Config.GetParametre("monnaie_symbole", "€")

def Nz(valeur):
    try:
        u = float(valeur)
    except:
        valeur = 0
    return valeur

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

def GetTypesLignes():
    # pour ajouter l'ordre les lignes dans les tracks et trier pour les calculs
    dicTypesLignes = {}
    for code, libel, ordre in GestionArticle.LISTEtypeLigne:
        dicTypesLignes[code] = ordre
    return dicTypesLignes

def Calcul(dictDonnees,obj,objects):
    aCalc = GestionArticle.ActionsModeCalcul(dictDonnees)
    qte, mtt = aCalc.ModeCalcul(obj, objects)
    if mtt != None:
        mtt = round(mtt, 2)
        obj.montantCalcul = mtt
        obj.qte = qte

def Multilignes(listeOLV,dictDonnees):
    # démultiplication des articles multi lignes
    dictConditionsMulti = {}
    for ligne in listeOLV:
        if ligne.condition != None:
            if len(ligne.condition)>5:
                if ligne.condition[0:5] in ["Multi", "Parra"]:
                     if ligne.condition not in dictConditionsMulti:
                         dictConditionsMulti[ligne.condition]=ligne.codeArticle
    if len(list(dictConditionsMulti.keys()))>0:
        aCond = GestionArticle.ActionsConditions(dictDonnees)
        for condition in list(dictConditionsMulti.keys()) :
            aCond.ConditionMulti(condition,dictConditionsMulti[condition],listeOLV)
    return listeOLV

def NormaliseLignes(lignes):
    #permet de les comparer
    champs = ['quantite', 'montant','codeArticle','libelle','IDnumPiece','prixUnit','IDnumLigne']
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

def GetLignes999(parent,DB):
    # appel des lignes famille de la piece en cours non facturée ou des factures de l'exercice
    if not parent.facture:
        pGest = GestionPieces.Forfaits(parent,DB=DB)
        pGest.CoherenceParrainages(parent.IDpayeur,DB=DB)

    fGest = GestionInscription.Forfaits(parent.parent,DB=DB)
    listePieces = fGest.GetPieceModif999(parent,parent.IDpayeur,parent.exerciceFin.year,facture=parent.facture)
    presence999 = len(listePieces)
    # rassemble les lignes des pièces existantes pour l'exercice
    lignes999 = None # cas d'absence de pièce
    if presence999 > 0:
        lignes999 = [] # présence de pièce, pas forcément avec des lignes
        # on déroule la liste des pièces se rapportant aux conditions
        for key in list(listePieces[0].keys()):
            #constitution préalable de dictDonnées à partir de la première pièce
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
                if piece['nature'] in ("AVO","FAC"):
                    continue
                # controle l'unicité de la pièce famille non facturée
                if 'pieceEnCours' in list(parent.dictDonnees.keys()) and parent.dictDonnees['pieceEnCours'] != piece['IDnumPiece']:
                    texte = "Anomalie!\n\nPlusieurs pièces non facturées pour le niveau famille sont en cours."
                    texte += "\nIl faut en supprimer pour pouvoir gérer correctement la modification d'une seule"
                    wx.MessageBox(texte,"DLG_PrixFamille - lancement")

                parent.dictDonnees['pieceEnCours'] = piece['IDnumPiece']
                parent.dictDonnees['pieceOrigine'] = piece

                for ligne in piece["lignes_piece"]:
                    lignes999.append(ligne)
                if hasattr(parent,'listeIDpiecesOrigine'):
                    parent.listeIDpiecesOrigine.append(piece["IDnumPiece"])

                if piece["IDprestation"] != None and hasattr(parent,'lstIDprestationsOrigine'):
                    parent.lstIDprestationsOrigine.append(piece["IDprestation"])
    return lignes999

def GetArticles(annee,dictDonnees):
    DB = dictDonnees['db']
    # appel des articles automatiques à insérer
    champsMatArticles = ["codeArticle", "libelle", "prix1", "prix2", "typeLigne", "condition", "modeCalcul"]
    lignesModel = []  # modèle permet de déterminer les articles qui résulteraient d'une initialisation

    # Récupération des articles niveau famille à ajouter à listeOLV
    req = """SELECT matArticles.artCodeArticle, matArticles.artLibelle, matArticles.artPrix1, matArticles.artPrix2, matArticles.artCodeBlocFacture as lfaTypeLigne, matArticles.artConditions, matArticles.artModeCalcul
            FROM matArticles
            WHERE artNiveauFamille = 1 AND (matArticles.artCodeArticle LIKE '$%%');
            """
    DB.ExecuterReq(req,MsgBox = "AppelArticles")
    recordset = DB.ResultatReq()

    if len(recordset) > 0:
        # Ajoute le contenu de recordset à listeOLV avec étape intermédiaire en liste de dictionnaires
        for item in recordset:
            i = 0
            ligne = {}
            for champ in champsMatArticles :
                ligne[champ] = item[i]
                i= i +1
            ligne["libelleArticle"] = ligne["libelle"]
            # pour article cotisation, inclusion de l'année dans le libellé
            i = ligne["libelle"].upper().find("COTIS")
            if i != -1 :
                ligne["libelle"] += " "+str(annee)
            ligne["ordre"] = 100+i
            ligne["origine"] = "articles"
            lignesModel.append(Track(ligne))
    lignesModel = Multilignes(lignesModel,dictDonnees)
    # Parrainages: renseigner les inscriptions parrainées dans la piece en cours de modif
    lstArtParr = []
    lstInscrParr = []
    if "dicParrainages" in list(dictDonnees.keys()):
        for (inscr,dicParr) in list(dictDonnees["dicParrainages"].items()):
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
    #fin GetArticles

def FormateLignes(listeOLV,dictDonnees):
    # précoche ou non via force
    for obj in listeOLV:
        if "article" in obj.origine and obj.montantCalcul != 0.0:
            obj.force = "OUI"
        elif obj.condition == "Sans" :
            obj.force = "OUI"

    # colorisation des lignes
    for obj in listeOLV:
        if not 'nature' in dictDonnees:
            obj.couleur = wx.BLUE
        elif dictDonnees['nature'] in ('FAC','AVO'):
            obj.couleur = wx.BLUE
        else:
            # cas des lignes modifiables
            if (dictDonnees["origine"] == "ajout"):
                obj.couleur = wx.BLUE
            else:
                if obj.origine == "lignes":
                    if obj.condition == 'Sans':
                        obj.couleur = wx.BLACK
                    elif obj.montant != obj.montantCalcul:
                        obj.couleur = wx.RED
                    else:
                        obj.couleur = wx.BLUE
                elif obj.origine == "articles":
                    obj.couleur = wx.BLUE
                elif obj.origine == "lignart":
                    if hasattr(obj,'oldValue') and float(obj.montantCalcul) != float(obj.oldValue):
                        obj.couleur = wx.RED
                    elif float(obj.montantCalcul) != float(obj.montantCalcul) and obj.montantCalcul != 0.0:
                        obj.couleur = wx.RED
                    else: obj.couleur = wx.BLUE
                else:
                    obj.couleur = wx.GREEN

def InserArticles(listeOLV = [],articles=[],dictDonnees={}):
    # ajout des articles manquant dans olv et retraitement de l'antérieur.
    lstSupprimer = []
    aCond= GestionArticle.ActionsConditions(dictDonnees)
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
        # test de présence pour alimenter la liste à supprimer
        present = False
        for ligne in listeOLV:
            if ligne.origine != 'lignes': continue
            # les articles parrainages ont pu être renumérotés
            ok = False
            if float(ligne.montant) == 0.0:
                ligne.montant = ligne.montantCalcul

            if article.codeArticle[:6] == '$$PARR' and ligne.codeArticle[:6] == '$$PARR':
                article.origine = "lignart"
                # recherce dans le dicParr
                dicParrainages = dictDonnees['dicParrainages']
                for IDinscr, dicParr in list(dicParrainages.items()):
                    if not hasattr(ligne,'IDnumLigne'):
                        print("coucou")
                    if ligne.IDnumLigne and article.IDinscription:
                        if ligne.IDnumLigne == dicParr['IDligneParrain'] and article.IDinscription == IDinscr:
                            lstSupprimer.append(ligne)
                            article.oldValue = ligne.montant
                            article.IDnumLigne = ligne.IDnumLigne
                            article.IDnumPiece = ligne.IDnumPiece
                            article.force = "OUI"
                            ok = True
                            break
                if ok : break
            else:
                if ligne.codeArticle == article.codeArticle:
                    article.origine = "lignart"
                    if ligne.montant == article.montantCalcul:
                        present = True
                        ligne.montantCalcul = article.montantCalcul
                        ligne.oldValue = article.montantCalcul
                        continue
                    else:
                        article.oldValue = article.montantCalcul
                        ligne.montantCalcul = article.montantCalcul
                        ligne.oldValue = article.montantCalcul
                        article.force = "NON"
                        continue

        if article.typeLigne in list(dicTypesLignes.keys()):
            article.ordre = dicTypesLignes[article.typeLigne]
        else: article.ordre = 99
        if not present:
            listeOLV.append(article)

    # suppression des anciennes lignes
    for ligne in lstSupprimer:
        listeOLV.remove(ligne)
    return
    #fin InserArticles

class Track(object):
    def __init__(self, track):
        for champ in list(track.keys()):
            setattr(self,champ,track[champ])
        if "libelleArticle" in list(track.keys()):
            self.libelleArticle =  track["libelleArticle"]
        else: self.libelleArticle =  track["libelle"]
        if track["origine"] == "articles":
            self.prixUnit = round(track["prix1"],4)
            self.qte = 1
            montant = 0
            self.prixUnit = track["prix1"]
            self.saisie = False
        if track["origine"]== "lignes":
            self.prixUnit = round(track["prixUnit"],4)
            self.qte =  track["quantite"]
            self.saisie = True
            montant =  track["montant"]
        if self.prixUnit == None: self.prixUnit = 0
        if self.qte == None: self.qte = 0
        self.montantCalcul = round(self.prixUnit * self.qte,2)
        self.montant = float(montant)
        self.qte = float(self.qte)
        if self.montant == round(self.qte * self.prixUnit,2):
            self.saisie = False
        self.montant = round(self.montant,2)
        self.montantCalcul = round(self.montantCalcul,2)
        if "force" in track:
            self.force = track["force"]
        else: self.force = None
    #fin Track

class CTRL_Solde(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, id=-1, name="panel_solde", style=wx.SUNKEN_BORDER | wx.TAB_TRAVERSAL,
                          size=(100, 40))
        self.parent = parent

        # Solde du compte
        self.ctrl_solde = wx.StaticText(self, -1, "0.00 %s " % SYMBOLE)
        font = wx.Font(11, wx.SWISS, wx.NORMAL, wx.BOLD)
        self.ctrl_solde.SetFont(font)

        # Layout
        self.grid_sizer = wx.FlexGridSizer(rows=1, cols=1, vgap=5, hgap=5)
        self.grid_sizer.Add(self.ctrl_solde, 1, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL | wx.ALL, 10)
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

# ---Gestion écran tarification --------------------------------------------------------------
class OLVtarification(FastObjectListView):
    def __init__(self,parent,DB,IDpayeur, exerciceFin, facture=False, *args, **kwds):
        self.DB = DB
        self.name = kwds.pop('name','noName')
        self.parent = parent
        self.facture = facture
        self.IDpayeur = IDpayeur
        self.exerciceFin = exerciceFin
        self.annee = self.exerciceFin.year
        self.lstIDprestationsOrigine = []
        self.lstOLVmodele = []
        FastObjectListView.__init__(self, parent, *args, **kwds)
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("familles_factures", "creer") == False :
            GestionDB.MessageBox(self,"Vous n'avez pas les droits pour créer des factures")
            self.cellEditMode = FastObjectListView.CELLEDIT_NONE
        else :
            self.cellEditMode = FastObjectListView.CELLEDIT_SINGLECLICK
        if facture:
            self.cellEditMode = FastObjectListView.CELLEDIT_NONE

        #lecture de pièce présente antérieurement
        self.lastObj = None
        self.listeIDpiecesOrigine=[]

        self.dictDonnees = {"IDindividu":0,
                            "IDfamille":IDpayeur,
                            "IDactivite": 0,
                            "IDgroupe": None,
                            "IDinscription":datetime.date.today().year, #ajout 10/09/2021
                            "db":DB,
                            "annee": self.annee,
                            "exercice": self.exerciceFin
                            }

        self.InitModel()
        #fin init

    def InitModel(self):
        # Charge la pièce existante et non facturée
        lignes999 = GetLignes999(self,self.DB)
        lignesPieces = []

        if lignes999 != None:
            self.dictDonnees["origine"] = "modif"
            lignesPieces = NormaliseLignes(lignes999)
        else:
            self.dictDonnees["origine"] = "ajout"
        self.dictDonnees["lignes_piece"] = lignesPieces
        self.dictDonnees["lignes_pieceOrigine"] = [x for x in lignesPieces]
        self.dictDonnees['lstIDprestationsOrigine'] = self.lstIDprestationsOrigine

        if not self.facture:
            if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("familles_factures", "creer") == True :
                self.cellEditMode = FastObjectListView.CELLEDIT_SINGLECLICK
        return

    def InitObjectListView(self,rappel=False):
        if rappel:
            self.InitModel()
        #composition du listView avec complémentation par les articles communs
        listeOLV=[]
        # on insère d'abord la piece999 complétées des attributs de l'article original
        if (self.dictDonnees["origine"] == "modif"):
            listeOLV = self.EnrichirDonnees(self.dictDonnees["lignes_piece"])

        if rappel:
            for obj in listeOLV:
                obj.force = "OUI"
                obj.couleur = wx.GREEN

        # puis on ajoute les articles manquants
        if not self.facture and not rappel:
            listeArticles = GetArticles(self.annee,self.dictDonnees)
            InserArticles(listeOLV,listeArticles,self.dictDonnees)

        def rowFormatter(listItem, track):
            if hasattr(track,'couleur'):
                listItem.SetTextColour(track.couleur)

        self.listeOLV = sorted(listeOLV,key=attrgetter('ordre'))

        # Couleur en alternance des lignes
        self.oddRowsBackColor = "#F0FBED"
        self.evenRowsBackColor = wx.Colour(255, 255, 255)
        self.useExpansionColumn = True

        liste_Colonnes = [
            ColumnDefn("Code", "center", 100, "codeArticle",typeDonnee="texte"),
            ColumnDefn("Libelle (libelles modifiables)", "left", 300,"libelle",typeDonnee="texte",isSpaceFilling = True ),
            ColumnDefn("Qté", "right", 50, "qte",typeDonnee="montant",stringConverter=FmtXd),
            ColumnDefn("Calculé", "right", 100, "montantCalcul",typeDonnee="montant",stringConverter="%.2f"),
            ColumnDefn("Forcé", "right", 100, "montant",typeDonnee="montant",stringConverter=Fmt2d),
            ]

        FormateLignes(self.listeOLV,self.dictDonnees)
        self.rowFormatter = rowFormatter
        self.SetColumns(liste_Colonnes)
        self.SetEmptyListMsg(_("Aucune ligne trouvée"))
        self.SetEmptyListMsgFont(wx.FFont(11, wx.DEFAULT, faceName="Tekton"))
        if not self.facture:
            self.CreateCheckStateColumn()
        self.SetObjects(self.listeOLV)
        #fin InitObjectListView

    def EnrichirDonnees(self,listeLignes, forcer = True):
        # Complete les articles simples en lignes-piece pour les champs liste2 liés à l'article, puis met en track
        DB = self.dictDonnees['db']
        donnees = []
        liste2=["prix1","prix2", "typeLigne", "condition", "modeCalcul"]
        # Transposition des données SQL avec les noms de champs utilisés en track
        if listeLignes != None:
            for dictLigne in listeLignes:
                # recherche de l'article pour compléter les infos de la ligne stockée
                dicDonnees = {}
                for champLigne in list(dictLigne.keys()):
                    dicDonnees[champLigne] = dictLigne[champLigne]
                champs = ["codeArticle", "libelle", "prix1", "prix2", "typeLigne", "condition", "modeCalcul"]

                req = """
                    SELECT matArticles.artCodeArticle, matArticles.artLibelle, matArticles.artPrix1, 
                           matArticles.artPrix2, matArticles.artCodeBlocFacture, matArticles.artConditions, 
                           matArticles.artModeCalcul
                    FROM matArticles
                    WHERE (matArticles.artCodeArticle = '%s');
                    """ % dicDonnees["codeArticle"]
                retour = DB.ExecuterReq(req,MsgBox="ExecuterReq")
                if retour != "ok" :
                    DB.AfficheErr(self,retour)
                    continue
                recordset = DB.ResultatReq()
                if len(recordset) == 0:
                    #article non trouvé car multi et ajouté sur les deux derniers caractère
                    req = """SELECT matArticles.artCodeArticle, matArticles.artLibelle, matArticles.artPrix1, 
                                    matArticles.artPrix2, matArticles.artCodeBlocFacture,matArticles.artConditions, 
                                    matArticles.artModeCalcul
                        FROM matArticles
                        WHERE (matArticles.artCodeArticle LIKE '%s');
                        """ % (dicDonnees["codeArticle"][0:-2]+"%%")
                    retour = DB.ExecuterReq(req,MsgBox="ExecuterReq")
                    if retour != "ok" : DB.AfficheErr(self,retour)
                    recordset = DB.ResultatReq()
                for champLigne in liste2:
                    if len(recordset)>0:
                        ix = champs.index(champLigne)
                        dicDonnees[champLigne] = recordset[0][ix]
                    else: dicDonnees[champLigne] = None
                dicTypesLignes = GetTypesLignes()
                if dicDonnees['typeLigne'] in list(dicTypesLignes.keys()):
                    dicDonnees['ordre'] = dicTypesLignes[dicDonnees['typeLigne']]
                else: dicDonnees['ordre'] = 99
                donnees.append(dicDonnees)
        #Transpose les données de type listes avec clés en objets tracks avec attributs pour OLV
        listeOLV = []
        aCond= GestionArticle.ActionsConditions(self.dictDonnees)
        for item in donnees:
            item["origine"]="lignes"
            cond = False
            if forcer :
                cond = True
                item["force"] = "OUI"
            else :
                if aCond.Condition(item["condition"],item["codeArticle"]):
                    cond = True
            if cond :
                track = Track(item)
                track.donnees = item
                listeOLV.append(track)
        return listeOLV
        #fin EnrichirDonnees

class DlgTarification(wx.Dialog):
    def __init__(self,parent,dictDonneesParent,fromIndividu = False,fromAvoir = False):
        self.parent = parent
        self.fromIndividu = fromIndividu
        self.fromAvoir = fromAvoir
        self.total = 0.0
        self.rappel = False
        wx.Dialog.__init__(self, None, -1, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX,
                           size=(800, 600))
        self.dictDonneesParent = dictDonneesParent

        self.DB = GestionDB.DB()
        if not 'IDactivite' in list(self.dictDonneesParent.keys()):
            self.dictDonneesParent['IDactivite'] = None
        self.exerciceDeb,self.exerciceFin = GestionArticle.AnneeAcad(self.DB,IDactivite = dictDonneesParent["IDactivite"])
        self.annee = self.exerciceFin.year
        self.IDcompte_payeur = dictDonneesParent["IDcompte_payeur"]
        # Verrouillage utilisateurs
        self.rw = True
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("individus_inscriptions", "creer") == False :
            self.rw = False

        # Pose les titres
        self.SetTitle(_("DLG_PrixFamille"))

        self.payeur = self.DB.GetNomIndividu(self.IDcompte_payeur)
        titre = "NIVEAU FAMILLE "
        self.ctrl_bandeau = CTRL_Bandeau.Bandeau(self, titre=titre, texte=self.payeur, hauteurHtml=10,
                                                 nomImage="Images/22x22/Smiley_nul.png")

        self.SetBandeau()

        # conteneur des données
        self.staticbox_facture = wx.StaticBox(self, -1, _("Déjà facturé..."))
        self.staticbox_nonFacture = wx.StaticBox(self, -1, _("Non facturé modifiable ..."))
        self.resultsOlv = OLVtarification(self,self.DB,self.IDcompte_payeur, self.exerciceFin, facture=False,id=1,
                                          name="OLV_Saisie",
                                          style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.LC_HRULES | wx.LC_VRULES)
        self.ctrl_recherche = CTRL_Outils(self, listview=self.resultsOlv)
        self.resultsOlvFact = OLVtarification(self,self.DB,self.IDcompte_payeur, self.exerciceFin, facture=True, id=2,
                                              name="OLV_Facture",
                                              style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.LC_HRULES | wx.LC_VRULES)
        self.ctrl_solde = CTRL_Solde(self)
        self.ctrl_solde.SetSolde(1000)

        # pour conteneur des actions en pied d'écran
        self.pied_staticbox = wx.StaticBox(self, -1, _("Actions"))
        self.hyper_tout = Hyperlien(self, label=_("Tout cocher"), infobulle=_("Cliquez ici pour tout cocher"),
                                    URL="tout")
        self.hyper_rien = Hyperlien(self, label=_("Tout décocher"), infobulle=_("Cliquez ici pour tout décocher"),
                                    URL="rien")
        self.hyper_annee = Hyperlien(self, label=_("Change Année"), infobulle=_("Cliquez ici pour choisir un autre exercice"),
                                    URL="annee")
        self.hyper_ajoutArticle = Hyperlien(self, label=_("| Ajouter Ligne"), infobulle=_("Ajouter un article"), URL="article")
        self.hyper_ajoutReinitialiser = Hyperlien(self, label=_("| Réinitialiser"),
                                                  infobulle=_("Pour oublier une saisie antérieure"), URL="reinitialiser")
        self.bouton_oj = CTRL_Bouton_image.CTRL(self, texte=_("Autre\nInscription"), cheminImage="Images/32x32/Fleche_gauche.png")
        self.bouton_ok = CTRL_Bouton_image.CTRL(self, texte=_("OK vers\nFacturation"), cheminImage="Images/32x32/Fleche_droite.png")
        self.bouton_annuler = CTRL_Bouton_image.CTRL(self, texte=_("Ignorer\nFamille"), cheminImage="Images/32x32/Annuler.png")
        if not self.fromIndividu :
            self.bouton_oj.Enable(False)
        self.__set_properties()
        self.Sizer()

        self.resultsOlv.Bind(wx.EVT_COMMAND_LEFT_CLICK, self.Activated)
        self.resultsOlv.Bind(wx.EVT_LIST_ITEM_SELECTED, self.Selected)
        self.resultsOlv.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.Activated)
        self.resultsOlv.Bind(wx.EVT_TEXT, self.OnTexte)
        self.resultsOlv.Bind(wx.EVT_LIST_KEY_DOWN, self.OnKeyDown)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonOj, self.bouton_oj)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonOk, self.bouton_ok)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAnnuler, self.bouton_annuler)
        self.SetExercice(self.annee)
        # fin de init

    def ListeDict(self,olv):
        # Permet de récupérer le format liste de dictionnaires pour les lignes de la pièce
        objects = olv.GetObjects()
        listeLignesPiece = []
        for obj in objects:
            if olv.IsChecked(obj) == True:
                dictTemp = {}
                if hasattr(obj,"donnees"):
                    dictTemp = obj.donnees
                dictTemp["codeArticle"]= obj.codeArticle
                dictTemp["libelle"]= obj.libelle
                if obj.qte == None: obj.qte = 1
                dictTemp["quantite"]= obj.qte
                if obj.qte != 0.0 :
                    dictTemp["prixUnit"]= round(obj.montantCalcul / obj.qte,4)
                else : dictTemp["prixUnit"] = 0.0
                dictTemp["montant"]= obj.montant
                listeLignesPiece.append(dictTemp)
        return listeLignesPiece

    def SetExercice(self,annee):
        # Application de l'année
        # cas d'un deuxième passage après init, l'année a changé
        if not annee == self.exerciceFin.year:
            dte = datetime.date(annee,self.exerciceFin.month,self.exerciceFin.day)
            self.exerciceDeb, self.exerciceFin = GestionArticle.AnneeAcad(self.DB, IDactivite=None, date=dte)

            # mise à jour de l'olv modifiable
            self.resultsOlv.exerciceFin = self.exerciceFin
            self.resultsOlv.dictDonnees['annee'] = annee
            del self.resultsOlv.dictDonnees['dicCumul']
            self.resultsOlv.InitModel()

            # mise à jour du bandeau
            self.SetBandeau()

            # mise à jour de l'OLV factures
            self.resultsOlvFact.exerciceFin = self.exerciceFin
            self.resultsOlvFact.InitModel()
            self.SetSizer(self.grid_sizer)
            self.Layout()

        # vérif de la présence d'une inscription
        if "IDactivite" not in self.resultsOlv.dictDonnees:
            # Recherche de pièces
            req = """SELECT Count(pieIDnumPiece)
                    FROM matPieces
                    WHERE pieIDcompte_payeur = %d ;""" % self.IDcompte_payeur
            self.DB.ExecuterReq(req,MsgBox="ExecuterReq")
            nbrePieces = self.DB.ResultatReq()
            if nbrePieces == 0:
                GestionDB.MessageBox(self,"Aucune inscription n'existe : Impossible de facturer même un complement",titre = "DLG_Famille.Init" )
                fGest = GestionInscription.Forfaits(self)
                fGest.NeutraliseReport(self.IDcompte_payeur,None,None)
                self.Destroy()
                return
        self.obj = None
        self.lastObj = None
        self.resultsOlv.InitObjectListView()
        self.resultsOlvFact.InitObjectListView()
        self.dataorigine = [ copy.deepcopy(x) for x in self.resultsOlv.listeOLV]
        self.PreCoche()
        self.CalculSolde()
        self.SupprimeDejaFacture()
        return

    def SetBandeau(self):
        self.annee = self.exerciceFin.year
        texte = "Payeur : " + self.payeur + " - Période du " \
                + self.exerciceDeb.strftime("%d/%m/%Y") + " au " + self.exerciceFin.strftime("%d/%m/%Y")
        titre = "NIVEAU FAMILLE - année %s" % str(self.annee)
        self.ctrl_bandeau.ctrl_titre.SetLabel(titre)
        self.ctrl_bandeau.ctrl_intro.SetPage(texte)

    def __set_properties(self):
        if not self.rw :
            self.bouton_ok.Enable(False)
            self.resultsOlv.Enable(False)
            self.hyper_ajoutArticle.Enable(False)
            self.hyper_ajoutReinitialiser.Enable(False)
            self.hyper_rien.Enable(False)
            self.hyper_annee.Enable(False)
            self.hyper_tout.Enable(False)
        self.bouton_ok.SetToolTip(_("Chaîner sur la synthèse famille et la facturation"))
        self.bouton_oj.SetToolTip(_("Retour sur les inscriptions, sans passer par la facturation"))
        self.bouton_annuler.SetToolTip(_("Cliquez ici pour ignorer les modifs du niveau famille"))
        self.ctrl_solde.SetToolTip(_("Ne Saisissez pas le montant ici, mais sur les lignes cochées"))
        self.ctrl_solde.ctrl_solde.SetToolTip(_("Ne Saisissez pas le montant ici, mais sur les lignes cochées"))

    def Sizer(self):
        self.grid_sizer = wx.FlexGridSizer(rows=5, cols=1, vgap=5, hgap=5)
        self.grid_sizer.Add(self.ctrl_bandeau, 0, wx.EXPAND, 0)
        staticsizer_facture = wx.StaticBoxSizer(self.staticbox_facture, wx.VERTICAL)
        grid_sizer_facture = wx.FlexGridSizer(rows=2, cols=1, vgap=1, hgap=10)

        grid_sizer_facture.Add(self.resultsOlvFact, 1, wx.EXPAND, 0)
        grid_sizer_facture.AddGrowableCol(0)
        grid_sizer_facture.AddGrowableRow(0)
        staticsizer_facture.Add(grid_sizer_facture, 1, wx.RIGHT|wx.EXPAND,5)
        self.grid_sizer.Add(staticsizer_facture, 1, wx.EXPAND, 0)

        staticsizer_nonFacture = wx.StaticBoxSizer(self.staticbox_nonFacture, wx.VERTICAL)
        grid_sizer_nonFacture = wx.FlexGridSizer(rows=2, cols=1, vgap=1, hgap=10)

        grid_sizer_nonFacture.Add(self.resultsOlv, 0, wx.EXPAND, 0)
        grid_sizer_nonFacture.Add(self.ctrl_recherche, 0, wx.EXPAND, 0)
        grid_sizer_nonFacture.AddGrowableCol(0)
        grid_sizer_nonFacture.AddGrowableRow(0)
        staticsizer_nonFacture.Add(grid_sizer_nonFacture, 1, wx.RIGHT|wx.EXPAND,5)
        self.grid_sizer.Add(staticsizer_nonFacture, 1, wx.EXPAND, 0)

        pied_staticboxSizer = wx.StaticBoxSizer(self.pied_staticbox, wx.VERTICAL)
        grid_sizer_pied = wx.FlexGridSizer(rows=1, cols=7, vgap=3, hgap=3)

        grid_sizer_cocher = wx.FlexGridSizer(rows=3, cols=1, vgap=1, hgap=10)
        grid_sizer_cocher.Add(self.hyper_tout, 0, wx.ALL, 0)
        grid_sizer_cocher.Add(self.hyper_rien, 0, wx.ALL, 0)
        grid_sizer_cocher.Add(self.hyper_annee, 0, wx.ALL, 0)
        grid_sizer_pied.Add(grid_sizer_cocher, 1, wx.EXPAND, 0)

        grid_sizer_outils = wx.FlexGridSizer(rows=2, cols=1, vgap=1, hgap=10)
        grid_sizer_outils.Add(self.hyper_ajoutArticle, 0, wx.ALL, 0)
        grid_sizer_outils.Add(self.hyper_ajoutReinitialiser, 0, wx.ALL, 0)
        grid_sizer_pied.Add(grid_sizer_outils, 1, wx.EXPAND, 0)

        grid_sizer_pied.Add(self.bouton_oj, 0, 0, 0)
        grid_sizer_pied.Add(self.bouton_ok, 0, 0, 0)
        grid_sizer_pied.Add(self.bouton_annuler, 0, 0, 0)
        grid_sizer_pied.Add(self.ctrl_solde, 0, 0, 0)
        grid_sizer_pied.AddGrowableCol(1)

        pied_staticboxSizer.Add(grid_sizer_pied, 1, wx.EXPAND, 5)        
        self.grid_sizer.Add(pied_staticboxSizer, 1, wx.EXPAND, 5)

        #self.grid_sizer.Fit(self)
        self.grid_sizer.AddGrowableRow(1)
        self.grid_sizer.AddGrowableRow(2)
        self.grid_sizer.AddGrowableCol(0)
        self.SetMinSize((650, 550))
        self.SetSizer(self.grid_sizer)
        self.Layout()
        self.CenterOnScreen()

    def Final(self):       
        self.IDuser = self.DB.IDutilisateurActuel()
        dictDonnees = self.resultsOlv.dictDonnees
        lstLignesPiece = self.ListeDict(self.resultsOlv)
        fGest = GestionInscription.Forfaits(self,DB=self.DB)
        lstNonNull = [ x for x in lstLignesPiece if (x["prixUnit"] * x["quantite"]) + x["montant"] != 0]
        
        # détermination de la prochaine nature
        if self.fromIndividu and not self.fromAvoir:
            # nature héritée de l'activité si non avoir
            nature = self.dictDonneesParent["nature"]
        elif dictDonnees["origine"] == "modif":
            # reprise de la nature de la pièce qui préexistait
            nature = dictDonnees["pieceOrigine"]["nature"]
        else:
            nature = fGest.GetNatureDevis(dictDonnees["IDfamille"])
        if dictDonnees["origine"] == "ajout" and len(lstNonNull) > 0:
            # Enregistre dans Pieces
            dDonnees = fGest.AjoutPiece999(self,dictDonnees["IDfamille"],self.IDcompte_payeur,
                                              self.exerciceFin, nature)

            dictDonnees.update(dDonnees)
            dictDonnees["lstIDprestationsOrigine"].append(dictDonnees["IDprestation"])
        dictDonnees["lignes_piece"] = NormaliseLignes(lstNonNull)

        if len(lstLignesPiece) > 0 :
            if 'dicParrainages' in list(self.resultsOlv.dictDonnees.keys()):
                dictDonnees['dicParrainages'] = self.resultsOlv.dictDonnees['dicParrainages']

        # enregistrement de la pièce et de ses prolongements prestation
        ret = fGest.ModifiePiece999(self,dictDonnees,nature)
        self.dictDonnees =  dictDonnees
        return ret
        #fin Final

    def Sortie(self,wxID = wx.ID_OK):
        self.DB.Close()
        self.EndModal(wxID)

    def OnBoutonOj(self, event):
        self.Sortie()

    def OnBoutonOk(self, event):
        valide = DLG_ValidationPiece.ValideSaisie(self.resultsOlv.GetCheckedObjects(),testSejour=False)
        if valide:
            #lancer la synthèse
            if not self.fromAvoir :
                    ret =self.Final()
                    dlg = DLG_FacturationPieces.Dialog(self,self.IDcompte_payeur)
                    dlg.ShowModal()
                    del dlg
            else:
                #cas du complément famille lié à un avoir
                ret =self.Final()
                if ret == "ok":
                    #après avoir validé la pièce en commande on la facture avec le numéro d'avoir de l'activité mis par Final()
                    lstLignesPiece = self.ListeDict(self.resultsOlv)
                    mtt = 0.0
                    for ligne in lstLignesPiece:
                        ligne["montant"] = round(ligne["montant"],2)
                        # calcul du total avec lignes cochées et priorité aux montants saisis
                        if ligne["montant"] != 0.0:
                            mtt += abs(ligne["montant"])
                        else: mtt += abs(Nz(ligne["quantite"]) * Nz(ligne["prixUnit"]))
                    pGest = GestionPieces.Forfaits(self)
                    pGest.AugmenteFacture(self.dictDonneesParent["noAvoir"],-mtt,self.dictDonnees["IDprestation"])
                    dlg = DLG_FacturationPieces.Dialog(self,self.IDcompte_payeur)
                    dlg.ShowModal()
                    del dlg
            self.Sortie()

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

    def ChangeAnnee(self):
        self.SetExercice(self.annee-1)

    def AjouteLigne(self, typeLigne):
        if typeLigne == "article":
            self.listeLignes = []
            # la listeLignes est alimentée par le ok du dlg
            dlg = DLG_ChoixLigne.DlgChoixArticle(self)
            if dlg.ShowModal() == wx.ID_OK:
                self.ActionAjout(self.listeLignes)
            del dlg

    def ActionAjout(self, listeLignes,forcer = False):
        # Ajout d'une ligne article
        fOLV = OLVtarification(self,self.DB,self.IDcompte_payeur,self.exerciceDeb, self.exerciceFin)
        listeLignesPlus = fOLV.EnrichirDonnees(listeLignes, forcer = True)
        if len(listeLignesPlus)>0:
            lstCodeArt = []
            for ligne in listeLignesPlus:
                # l'origine ajoutLigne déclenchera la condition MultiFam dans le calcul article calRedFam et donc génèrera les lignes
                ligne.origine="ajoutLigne"
                ligne.force = "NON"
                ligne.saisie = False
                self.resultsOlv.listeOLV.append(ligne)
                lstCodeArt.append(ligne.codeArticle)
                self.resultsOlv.SetCheckState(ligne, True)
            dictConditionsMulti = {}
            for ligne in self.resultsOlv.listeOLV:
                for codeArt in lstCodeArt:
                    if codeArt == ligne.codeArticle[:len(codeArt)]:
                        # Composition des lignes multi
                        if ligne.condition != None:
                            if len(ligne.condition)>5:
                                if ligne.condition[0:5] in ["Multi", "Parra"]:
                                     if ligne.condition not in dictConditionsMulti:
                                         dictConditionsMulti[ligne.condition]=ligne.codeArticle
            if len(list(dictConditionsMulti.keys()))>0:
                aCond = GestionArticle.ActionsConditions(self.resultsOlv.dictDonnees)
                for condition in list(dictConditionsMulti.keys()) :
                        aCond.ConditionMulti(condition,dictConditionsMulti[condition],self.resultsOlv.listeOLV)
            self.resultsOlv.SetObjects(self.resultsOlv.listeOLV)
            for ligne in self.resultsOlv.listeOLV:
                for codeArt in lstCodeArt:
                    if codeArt == ligne.codeArticle[:len(codeArt)]:
                        # Les lignes ajoutées par Multi ne sont pas cochée
                        self.resultsOlv.SetCheckState(ligne, True)
            self.CalculSolde()
            self.resultsOlv.Refresh()
        fOLV.Destroy()
        #fin ActionAjout

    def Reinitialiser(self):
        self.rappel = not self.rappel
        self.resultsOlv.InitObjectListView(rappel=self.rappel)
        self.PreCoche()
        self.CalculSolde()
        self.resultsOlv.Refresh()
        #self.SupprimeDejaFacture()

    def OnKeyDown(self, event):
        pass

    def OnTexte(self, event):
        # l'évènement OnTexte ne valide pas la saisie, test impossible sur les valeurs de track
        if not self.obj: return
        self.obj.saisie = True

    def OnSelected(self, event):
        # Controle montant forcé à zéro
        if self.lastObj != None :
            if self.obj.codeArticle != None and self.obj.saisie == True :
                listeOLV = self.resultsOlv.GetObjects()
                # une saisie texte a eu lieu le zéro doit être pris en compte
                try :
                    saisie = False
                    ix = listeOLV.index(self.obj)
                    for item in ["montant","qte","libelle"]:
                        if self.lastObj.__dict__[item] != listeOLV[ix].__dict__[item]:
                            saisie = True
                    if saisie :
                        self.resultsOlv.SetCheckState(self.obj, True)
                    if listeOLV[ix].montant == 0.0 and self.lastObj.montant != 0.0:
                        listeOLV[ix].qte = 0
                    if listeOLV[ix].qte == 0.0 and self.lastObj.qte != 0.0:
                        listeOLV[ix].montant = 0
                    listeOLV[ix].force = "OUI"
                    self.resultsOlv.SetObjects(listeOLV)
                except : pass
        if len(self.resultsOlv.GetSelectedObjects()) > 0 :
            self.obj = self.resultsOlv.GetSelectedObjects()[0]
        else : self.obj = self.resultsOlv.GetObjects()[0]
        self.lastObj = None
        self.CalculSolde()
        self.resultsOlv.Refresh()
        #fin OnSelected

    def Selected(self, event):
        if self.obj == None :
            self.obj = self.resultsOlv.GetSelectedObject()
            self.lastBind = "select"
            self.lastLigne = 0
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

    def Activated(self, event):
        obj = self.resultsOlv.GetSelectedObject()
        #if len(selection)>0:
        #    obj = selection[0]
        # reprend un montant antérieur si retour d'une coche après décoche
        if self.resultsOlv.IsChecked(obj) == True:
            for objOrigine in self.dataorigine:
                if objOrigine.codeArticle == obj.codeArticle:
                    obj.prixUnit = objOrigine.prixUnit
        self.CalculSolde()

    def OnActivated(self, event):
        self.lastObj = copy.deepcopy(self.obj)
        selection = self.resultsOlv.GetSelectedObjects()
        if len(selection)>0:
            obj = selection[0]
            # reprend un montant antérieur si retour d'une coche après décoche
            if self.resultsOlv.IsChecked(obj) == True and not obj.saisie:
                for objOrigine in self.dataorigine:
                    if (objOrigine.codeArticle, objOrigine.libelle) == (obj.codeArticle, obj.libelle):
                        obj.prixUnit = objOrigine.prixUnit
                        obj.montantCalcul = objOrigine.montantCalcul
                        obj.qte = objOrigine.qte
            self.CalculSolde()
            self.resultsOlv.Refresh()

    def CalculSolde(self):
        objects = self.resultsOlv.GetObjects()
        # ajout de l'attribut coché
        for obj in objects:
            obj.isChecked = self.resultsOlv.IsChecked(obj)
        total, mtt = 0, 0
        for obj in sorted(objects,key=attrgetter('ordre')):
            if obj.isChecked == False:
                if obj.qte == 0: obj.qte = 1
                obj.prixUnit = round(obj.montantCalcul / obj.qte,4)
                obj.montant = 0.0
                obj.montantCalcul = 0.0
                obj.saisie = False
                obj.force = "NON"
            # les cochés sont recalculés
            if self.resultsOlv.IsChecked(obj) == True:
                obj.montantCalcul = round(obj.prixUnit * obj.qte,2)
                if obj.saisie == False :
                    Calcul(self.resultsOlv.dictDonnees,obj,objects)
                if obj.montantCalcul != 0.0:
                    #correctif pour ne pas refacturer deux fois le même article
                    for objfac in self.resultsOlvFact.GetObjects():
                        if objfac.codeArticle == obj.codeArticle:
                            if obj.force == "NON" :
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
                else: total += (obj.montantCalcul)
            obj.montant = round(float(Nz(obj.montant)),2)
            obj.qte = float(Nz(obj.qte))
            obj.prixUnit = round(float(Nz(obj.prixUnit)),4)
            obj.montantCalcul = round(float(Nz(obj.montantCalcul)),2)
        self.ctrl_solde.SetSolde(round(total,2))
        self.total = round(total,2)
        #fin CalculSolde

    def SupprimeDejaFacture(self):
        dictSuppression = {}
        dictDecompte = {}
        for obj in self.resultsOlv.listeOLV :
            testFact = False
            for objfac in self.resultsOlvFact.listeOLV:
                if (objfac.codeArticle,objfac.libelle) == (obj.codeArticle,obj.libelle): testFact = True
            if testFact:
                #normalisation du montant
                if obj.montant == 0: mtt = obj.montantCalcul
                else : mtt = obj.montant
                #cumul des  montants par code article
                if obj.codeArticle in dictSuppression:
                    dictSuppression[str(obj.codeArticle)] += mtt
                    dictDecompte[str(obj.codeArticle)] += 1
                else :
                    dictSuppression[str(obj.codeArticle)] = mtt
                    dictDecompte[str(obj.codeArticle)] = 1
        # suppression des articles dont le total du montant est à zéro
        for code in list(dictSuppression.keys()):
            if dictSuppression[str(code)] == 0:
                while dictDecompte[str(code)] > 0 :
                    for obj in self.resultsOlv.listeOLV :
                        if obj.codeArticle == code :
                            self.resultsOlv.listeOLV.remove(obj)
                    dictDecompte[str(code)]-=1
        self.resultsOlv.SetObjects(self.resultsOlv.listeOLV)
        return
        #fin SupprimeDejaFacture

    def RazUnchecked(self):
        objects = self.resultsOlv.GetObjects()
        for obj in objects:
            if self.resultsOlv.IsChecked(obj) == False:
                obj.montant = 0
                obj.prixUnit = 0

    def PreCoche(self):
        objects = self.resultsOlv.GetObjects()
        for obj in objects:
            if not obj.force == "OUI" :
                self.resultsOlv.SetCheckState(obj, False)
                obj.montant = 0.00
            else:
                self.resultsOlv.SetCheckState(obj, True)
            self.resultsOlv.RefreshObjects(objects)

# -------------------------------------------------------------------------------------------------------------------------------------------
class BarreRecherche(wx.SearchCtrl):
    def __init__(self, parent):
        wx.SearchCtrl.__init__(self, parent, size=(-1, -1), style=wx.TE_PROCESS_ENTER)
        self.parent = parent
        self.rechercheEnCours = False

        self.SetDescriptiveText(_("Rechercher un Bloc..."))
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
        txtSearch = self.GetValue().replace("'","\\'")
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
        if self.URL == "annee": self.parent.ChangeAnnee()
        if self.URL == "article": self.parent.AjouteLigne("article")
        if self.URL == "reinitialiser": self.parent.Reinitialiser()
        self.UpdateLink()

# --------------------Lancement de test ----------------------
if __name__ == "__main__":
    app = wx.App(0)
    listeDonnees = [
        ("origine", "modif"),
        ("IDindividu", 4616),
        ("IDfamille", 4616),
        ("IDactivite", 421),
        ("IDgroupe", 442),
        ("IDcategorie_tarif", 795),
        ("nature", "COM"),
        ("noFacture", 0),
        ("IDcompte_payeur", 4616),
        ("IDinscription", 0),
        ("date_inscription", datetime.date.today()),
        ("parti", False),
        ("nom_activite", "Sejour 41"),
        ("nom_payeur", "ma famille"),
        ("nom_groupe", "Groupe Pasto Plus"),
        ("nom_categorie_tarif", "Tarif Normal"),
        ("nom_individu", "nom de  l'individu"),
        ("lignes_piece", [{'utilisateur': 'NoName', 'quantite': 1, 'montant': 480.5, 'codeArticle': 'SEJ_CORSE_S1', 'libelle': 'Séjour Jeunes Corse S1', 'IDnumPiece': 5, 'prixUnit': 480.0, 'date': '2016-07-24', 'IDnumLigne': 128}]),
        ]
    dictDonnees = {}
    for donnee in listeDonnees:
        champ = donnee[0]
        valeur = donnee[1]
        dictDonnees[champ] = valeur
    f = DlgTarification(None,dictDonnees,)
    app.SetTopWindow(f)
    if f.ShowModal() == wx.ID_OK:
        print("OKfin_main")
    else:
        print("KC")
    app.MainLoop()
