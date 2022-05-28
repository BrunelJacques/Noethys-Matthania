#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, dérive de OL_Attestations_cerfa, pour ctrl parrainages
# Auteur:           Ivan LUCAS, JB
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------

import Chemins
import wx
import GestionDB 
import datetime
from Utils import UTILS_Config
from Utils import UTILS_Utilisateurs
from Dlg import DLG_Famille
from Utils.UTILS_Traduction import _
from Ctrl.CTRL_ObjectListView import ObjectListView, ColumnDefn, Filter, CTRL_Outils, PanelAvecFooter

SYMBOLE = UTILS_Config.GetParametre("monnaie_symbole", "€")

FondCyste = wx.Colour(255, 200, 250) # Mauve clair
FondRose = wx.Colour(255, 117, 117) # Rose clair
FondSaumon = wx.Colour(255, 186, 151) # Saumon clair
FondAzur = wx.Colour(200, 236, 255) # bleu clair


def DateEngFr(textDate):
    if textDate == None: return ""
    textDate = str(textDate)
    text = str(textDate[8:10]) + "/" + str(textDate[5:7]) + "/" + str(textDate[:4])
    return text

def DateEngEnDateDD(dateEng):
    if dateEng and not isinstance(dateEng,str): dateEng = str(dateEng)
    return datetime.date(int(dateEng[:4]), int(dateEng[5:7]), int(dateEng[8:10]))

# ---------------------------------------- LISTVIEW -----------------------------------------------------------------------

class Track(object):
    def __init__(self, dicDonnees):
        action = "-"
        try:
            for key, donnee in dicDonnees.items():
                if isinstance(donnee,list):
                    txt = ""
                    for item in donnee:
                        txt += "%s;"%item
                    donnee = txt
                setattr(self, "%s" % key, donnee)

        except: raise Exception("Track: exec " + action)


class ListView(ObjectListView):
    def __init__(self, *args, **kwds):
        # Initialisation du listCtrl
        self.selectionID = None
        self.selectionTrack = None
        ObjectListView.__init__(self,  **kwds)
        self.parent = kwds["parent"].Parent
        self.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)

    def GetDonnees(self, IDfamille=None, listeComptesPayeurs=[]):
        DB = GestionDB.DB()
        
        # Filtres de l'utilisateur
        where = self.GetFiltre()
        # Appel des lignes
        champs = ['IDinscription','IDparrain','libParrain','IDfilleul','libFilleul','prenom','abandon','nature',
                  'date','montant','IDligneParr','prorata','ligDate','reduction','IDprestation']

        req = """
            SELECT matPieces.pieIDinscription, matPieces.pieIDparrain, familles.adresse_intitule, matPieces.pieIDfamille, 
                    familles_1.adresse_intitule, individus.prenom, matPieces.pieParrainAbandon, matPieces.pieNature, 
                    matPieces.pieDateCreation, Sum(prestations.montant),matParrainages.parIDligneParr,matParrainages.parSolde,
                    matPiecesLignes.ligDate, matPiecesLignes.ligMontant, prestations.IDprestation
            FROM (((((	matPieces 
                        LEFT JOIN matParrainages ON matPieces.pieIDinscription = matParrainages.parIDinscription)
                        LEFT JOIN matPiecesLignes ON matParrainages.parIDligneParr = matPiecesLignes.ligIDnumLigne) 
                        LEFT JOIN familles ON matPieces.pieIDparrain = familles.IDfamille) 
                        LEFT JOIN familles AS familles_1 ON matPieces.pieIDfamille = familles_1.IDfamille) 
                        LEFT JOIN individus ON matPieces.pieIDindividu = individus.IDindividu)
                        LEFT JOIN prestations ON matPieces.pieIDprestation = prestations.IDprestation
             %s
            GROUP BY matPieces.pieIDinscription, matPieces.pieIDparrain, familles.adresse_intitule, matPieces.pieIDfamille, 
                    familles_1.adresse_intitule, individus.prenom, matPieces.pieParrainAbandon, matPieces.pieNature, 
                    matPieces.pieDateCreation, matParrainages.parIDligneParr, matPiecesLignes.ligDate, 
                    matPiecesLignes.ligMontant, prestations.IDprestation
            ORDER BY matPieces.pieIDparrain
            ;""" % (where)

        DB.ExecuterReq(req,MsgBox="OL_Liste_parrainages.GetDonnees1")
        lstParrainages = DB.ResultatReq()

        dictParrainages = {}
        lstIDparrains = []
        lstIDfilleuls = []
        lstIDprestations = []
        dictKeys = {}
        # regroupement de l'info dans dictParrainages
        if len(lstParrainages) > 0:
             for item in lstParrainages:
                periode = item[champs.index('date')] >= str(self.dteDebut)
                IDparrain = item[champs.index('IDparrain')]
                IDfilleul = item[champs.index('IDfilleul')]
                IDprestation = item[champs.index('IDprestation')]

                # liste IDparrains pour rechercher les orphelines
                if not IDparrain in lstIDparrains:
                    lstIDparrains.append(IDparrain)

                # liste IDfilleuls pour rechercher les ventiltions
                if not IDfilleul in lstIDfilleuls:
                    lstIDfilleuls.append(IDfilleul)
                if not IDprestation in lstIDprestations:
                    lstIDprestations.append(IDprestation)

                # exclusion des réductions hors période
                dteReduc = item[champs.index('ligDate')]
                post=1
                if (not self.post) and dteReduc and dteReduc > str(self.dteFin):
                    post = 0
                reduc = 0
                if item[champs.index('reduction')]:
                    reduc = 1 * post

                # nouveau parrain dans la periode, on alimente tous les champs simples
                if not (periode,IDparrain,IDfilleul) in list(dictParrainages.keys()):
                    dictParrainages[(periode,IDparrain,IDfilleul)] = {}
                    dictP = dictParrainages[(periode,IDparrain,IDfilleul)]
                    for champ in champs:
                        dictP[champ] = item[champs.index(champ)]
                    dictP['periode'] = periode
                    for champ in ('prenoms','datesReduc','lstIDprest'):
                        dictP[champ] = []
                    for champ in ('nbInscriptions','nbAbandons','nbAttente','flagOk'):
                        dictP[champ] = 0
                    for champ in ('mttReduc','caFilleuls','solde','regle','ratio',):
                        dictP[champ] = 0.0
                    if not IDparrain in list(dictKeys.keys()):
                        dictKeys[IDparrain] = (periode,IDparrain,IDfilleul)
                    dictP['lstIDprestations'] = []
                dictP = dictParrainages[(periode,IDparrain,IDfilleul)]
                # première série de calculs
                # ['prenoms','nbInscriptions','nbAbandons','nbAttente','caFilleuls','solde','regle','mttReduc','datesReduc','ratio','flagOk']
                dictP['prenoms'].append("%s"%item[champs.index('prenom')])
                if reduc:
                    dictP['datesReduc'].append("%s"%DateEngFr(item[champs.index('ligDate')]))
                dictP['lstIDprestations'].append(IDprestation)
                dictP['nbInscriptions'] += 1
                if item[champs.index('abandon')] == 1:
                    dictP['nbAbandons'] += 1
                prorata = item[champs.index('prorata')]
                # premières versions, les prorata étaient en % et non en /10000 et calculés différemment
                if prorata and (int(prorata) > 1000):
                    prorata = float(prorata) / 10000
                else: prorata = 1.0

                if item[champs.index('reduction')] == None or not reduc:
                    if dictP['IDligneParr'] != 0:
                       dictP['nbAttente'] += 1
                else: dictP['mttReduc'] -= (item[champs.index('reduction')]) * prorata

                if item[champs.index('montant')] != None:
                    dictP['caFilleuls'] += item[champs.index('montant')]

        # recherche des ventilations réglant les prestations
        req = """
            SELECT ventilation.IDcompte_payeur, ventilation.IDprestation, Sum(ventilation.montant)
            FROM ventilation
            WHERE ((ventilation.IDprestation In (%s)) AND (ventilation.IDcompte_payeur In (%s)))
            GROUP BY ventilation.IDcompte_payeur, ventilation.IDprestation
            ;"""%(str(lstIDprestations)[1:-1],str(lstIDfilleuls)[1:-1],)
        DB.ExecuterReq(req,MsgBox="OL_Liste_parrainages.GetDonnees3")
        lstReglements = DB.ResultatReq()
        # constitution d'un dictionnaire des règlements
        dictReglements = {}
        if len(lstReglements) > 0:
            for IDfilleul, IDprestation,regle in lstReglements:
                if not IDfilleul in list(dictReglements.keys()):
                    dictReglements[(IDfilleul,IDprestation)] = 0.0
                dictReglements[IDfilleul,IDprestation] += regle

        # recherche réductions orphelines sur les parrains retenus
        where = """
            WHERE (matPiecesLignes.ligCodeArticle Like '%%parrain%%')
                    AND (matParrainages.parIDligneParr Is Null) 
                    AND ((matPieces.pieIDfamille) In (%s))"""%str(lstIDparrains)[1:-1]
        if not self.anterieur:
            where += """
                    AND (matPiecesLignes.ligDate >= '%s')"""%self.dteDebut
        if not self.post:
            where += """
                    AND (matPiecesLignes.ligDate <= '%s')"""%self.dteFin
        req = """
            SELECT matPieces.pieIDfamille, Sum(matPiecesLignes.ligMontant)
            FROM (matPieces 
            INNER JOIN matPiecesLignes ON matPieces.pieIDnumPiece = matPiecesLignes.ligIDnumPiece) 
            LEFT JOIN matParrainages ON matPiecesLignes.ligIDnumLigne = matParrainages.parIDligneParr
            %s
            GROUP BY matPieces.pieIDfamille;
            """%where
        DB.ExecuterReq(req,MsgBox="OL_Liste_parrainages.GetDonnees2")
        lstReductions = DB.ResultatReq()
        DB.Close()
        # inclusion des réductions orphelines sur la première clé du parrain
        if len(lstReductions) > 0:
            for IDparrain, montant in lstReductions:
                dictP = dictParrainages[dictKeys[IDparrain]]
                dictP['mttReduc'] -= montant
                dictP['datesReduc'].append("orphelines")
                # maqueur flag présence d'au moins une orpheline
                if dictP['flagOk'] & 1 == 0:
                    dictP['flagOk'] = 1 | dictP['flagOk']

        # complète les champs calculés
        for key, dictP in dictParrainages.items() :
            (periode, IDparrain, IDfilleul) = key
            # ajout des ventilations de la prestation dans le réglé
            for IDprestation in dictP['lstIDprestations']:
                dictP['regle'] += dictReglements[(IDfilleul, IDprestation)]

            dictP['solde'] = round(dictP['caFilleuls'] - dictP['regle'],2)
            if dictP['reduction']:
                dictP['reduction'] = round(dictP['reduction'],2)
            if dictP['solde'] < 10: dictP['solde'] = 0.0
            if dictP['caFilleuls'] == 0: dictP['caFilleuls'] = 1.0
            dictP['ratio'] = round(100 * dictP['mttReduc'] / dictP['caFilleuls'] )

            # marqueur flag réduction perdue
            if dictP['IDligneParr'] >0 and ((not dictP['reduction']) or dictP['reduction'] == 0):
                if dictP['flagOk'] & 2 == 0:
                    dictP['flagOk'] = 2 | dictP['flagOk']
            # marqueur flag parrain perdu
            if not dictP['libParrain'] or len(dictP['libParrain']) ==0:
                if dictP['flagOk'] & 4 == 0:
                    dictP['flagOk'] = 4 | dictP['flagOk']

        return dictParrainages
        # fin GetDonnees

    def GetTracks(self):
        # Récupération des données prestations
        lstDonneesOlv = []
        for key, dict in self.GetDonnees().items() :
            track = Track(dict)
            lstDonneesOlv.append(track)
        return lstDonneesOlv

    def InitObjectListView(self):
        # ImageList
        self.imgOk = self.AddNamedImages("ok", wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Ok.png"), wx.BITMAP_TYPE_PNG))
        self.imgVert = self.AddNamedImages("vert", wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Ventilation_vert.png"), wx.BITMAP_TYPE_PNG))
        self.imgRouge = self.AddNamedImages("rouge", wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Ventilation_rouge.png"), wx.BITMAP_TYPE_PNG))
        self.imgOrange = self.AddNamedImages("orange", wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Ventilation_orange.png"), wx.BITMAP_TYPE_PNG))
        self.imgDepannage = self.AddNamedImages("depannage", wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Depannage.png"), wx.BITMAP_TYPE_PNG))

        def GetImgParrain(track):
            # nom du parrain absent non pointé par la table matParrainages
            ret = None
            if track.flagOk & 4 == 4:
                ret =  self.imgDepannage
            return ret

        def GetImgReduc(track):
            ret = None
            # cumul 1 et 2 :Présence de réduction orphelines de pointeur et parrainages pointant du vide
            if track.flagOk & 3 == 3:
                ret = self.imgVert
            # le pointage a été forcé
            elif track.IDligneParr == 0:
                ret = self.imgOk
            # Présence de réduction orphelines de pointeur
            elif track.flagOk & 1:
                ret = self.imgOrange
            # Réduction: parrainages pointe du vide dans les lignes de réductions
            elif track.flagOk & 2:
                ret =  self.imgRouge
            return ret

        def GetImgSolde(track):
            # non réglé mais pas de réduction accordée
            if track.solde > 0 and track.reduction == 0:
                return self.imgVert
            # non réglé
            if track.solde > 0 :
                return self.imgRouge
            return

        def GetImgRatio(track):
            if track.ratio > 10:
                return self.imgOrange
            return

        def FmtMontant(montant):
            if montant == None or montant == "" : return ""
            if int(montant) == 0 : return ""
            return "%.2f " % (montant )

        def FmtEntier(montant):
            if montant == None or montant == "" : return ""
            if int(montant) == 0 : return ""
            return "%.f " % (montant )

        def FmtBool(valeur):
            if valeur == None: return ""
            if valeur : return "x"
            return "-"

        def FmtListe(lst):
            if lst == None: return ""
            if isinstance(lst,list) :
                texte = ""
                for item in lst:
                    texte += "%s;"%item
                return texte
            return lst

        def rowFormatter(listItem, track):
            #
            if track.flagOk & 1:
                listItem.SetBackgroundColour(FondCyste)
            elif track.flagOk & 2:
                listItem.SetBackgroundColour(FondSaumon)
            elif track.flagOk & 4:
                listItem.SetBackgroundColour(FondRose)
            elif (track.solde > 0 and track.reduction < 0) or track.ratio > 10:
                listItem.SetBackgroundColour(FondAzur)
            #listItem.SetTextColour(wx.Colour(150, 150, 150))


        # Couleur en alternance des lignes
        self.oddRowsBackColor = wx.Colour(255, 255, 255) #blanc) ("#EEF4FB" pour faire Bleu)
        self.evenRowsBackColor = "#F0FBED" # Vert clair
        self.rowFormatter = rowFormatter

        # Paramètres ListView
        self.useExpansionColumn = True

        lstColonnes = [
            ColumnDefn("Periode", 'right', 30, 'periode', typeDonnee='entier',stringConverter=FmtBool),
            ColumnDefn("No parr.", 'right', 40, 'IDparrain', typeDonnee='entier'),
            ColumnDefn("Parrain", 'left', -1, 'libParrain', typeDonnee='texte',isSpaceFilling=True,
                       imageGetter = GetImgParrain),
            ColumnDefn("No filleul", 'right', 40, 'IDfilleul', typeDonnee='entier'),
            ColumnDefn("Fam. filleuls", 'left', -1, 'libFilleul', typeDonnee='texte',isSpaceFilling=True),
            ColumnDefn("Prénoms des filleuls", 'left', 100, 'prenoms', typeDonnee='texte',
                       stringConverter=FmtListe),
            ColumnDefn("Inscrits ", 'right', 50, 'nbInscriptions', typeDonnee='entier'),
            ColumnDefn("Abandon Filleul", 'right', 50, 'nbAbandons', typeDonnee='entier'),
            ColumnDefn("Attente Réduc", 'right', 50, 'nbAttente', typeDonnee='entier'),
            ColumnDefn("Facturé", 'right', 80, 'caFilleuls', typeDonnee='entier',stringConverter=FmtMontant),
            ColumnDefn("Reste à régler", 'right', 80, 'solde', typeDonnee='entier',stringConverter=FmtMontant,
                        imageGetter = GetImgSolde),
            ColumnDefn("Réductions", 'right', 60, 'mttReduc', typeDonnee='entier',stringConverter=FmtMontant,
                       imageGetter = GetImgReduc),
            ColumnDefn("Dates Réductions", 'left', 120, 'datesReduc', typeDonnee='texte',
                        stringConverter=FmtListe),
            ColumnDefn("% réduc /  CA ", 'center', 50, 'ratio', typeDonnee='entier',stringConverter=FmtEntier,
                       imageGetter = GetImgRatio),
            ColumnDefn("ko", 'center', 60, 'flagOk', typeDonnee='texte')]
        
        self.SetColumns(lstColonnes)
        self.SetSortColumn(self.columns[1])
        self.SetEmptyListMsg(_("Aucun parrainage sur la période"))
        self.SetEmptyListMsgFont(wx.FFont(11, wx.DEFAULT, faceName="Tekton"))
        self.SetObjects(self.donnees)

    def GetFiltre(self):
        self.dteDebut = self.parent.ctrl_date_debut.GetDate()
        self.dteFin = self.parent.ctrl_date_fin.GetDate()
        self.anterieur = self.parent.ctrl_anterieur.GetValue()
        self.post = self.parent.ctrl_post.GetValue()
        filtreSQL = """
        WHERE 	(	(matPieces.pieIDparrain Is Not Null) 
				    AND	(matPieces.pieDateCreation Between '%s' And '%s'))"""%(self.dteDebut,self.dteFin)
        if self.anterieur:
            filtreSQL = """
        WHERE 	(matPieces.pieIDparrain Is Not Null)
				AND (	(matPieces.pieDateCreation Between '%s' And '%s')
						OR	(	(matPieces.pieDateCreation < '%s')
								AND	(matPieces.pieParrainAbandon = 0) 
								AND	(matPiecesLignes.ligDate >= '%s')))
					    """%(self.dteDebut,self.dteFin,self.dteDebut,self.dteDebut)
        return filtreSQL

    def MAJ(self, ID=None):
        if ID != None :
            self.selectionID = ID
            self.selectionTrack = None
        else:
            self.selectionID = None
            self.selectionTrack = None
        self.donnees = self.GetTracks()
        self.InitObjectListView()
        # Sélection d'un item
        if self.selectionTrack != None :
            self.SelectObject(self.selectionTrack, deselectOthers=True, ensureVisible=True)
        self.selectionID = None
        self.selectionTrack = None
        if ID == None :
            self.DefileDernier() 
        # MAJ du total du panel
        try :
            if self.GetParent().GetName() == "panel_prestations" :
                self.GetParent().MAJtotal()
        except :
            pass
        self.Refresh()
    
    def Selection(self):
        return self.GetSelectedObjects()
    
    def OnContextMenu(self, event):
        """Ouverture du menu contextuel """
        if len(self.Selection()) > 0 :
            ID = self.Selection()[0].IDparrain
        
        # Création du menu contextuel
        menuPop = wx.Menu()
        
        menuPop.AppendSeparator()

        # Accès au parrain
        item = wx.MenuItem(menuPop, 10, _("Accéder à la fiche parrain"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Responsable_legal.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.OuvrirFicheParrain, id=10)

        # Accès au filleul
        item = wx.MenuItem(menuPop, 20, _("Accéder à la fiche filleul"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Famille.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.OuvrirFicheFilleul, id=20)

        menuPop.AppendSeparator()

        # Item Apercu avant impression
        item = wx.MenuItem(menuPop, 40, _("Aperçu avant impression"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Apercu.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.Apercu, id=40)
        
        # Item Imprimer
        item = wx.MenuItem(menuPop, 50, _("Imprimer"))
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

    def Apercu(self, event):
        from Utils import UTILS_Printer
        prt = UTILS_Printer.ObjectListViewPrinter(self, titre=_("Liste des prestations"), format="A", orientation=wx.PORTRAIT)
        prt.Preview()

    def Imprimer(self, event):
        from Utils import UTILS_Printer
        prt = UTILS_Printer.ObjectListViewPrinter(self, titre=_("Liste des prestations"), format="A", orientation=wx.PORTRAIT)
        prt.Print()

    def ExportTexte(self, event):
        from Utils import UTILS_Export
        UTILS_Export.ExportTexte(self, titre=_("Liste des prestations"))
        
    def ExportExcel(self, event):
        from Utils import UTILS_Export
        UTILS_Export.ExportExcel(self, titre=_("Liste des parrainages"))

    def OuvrirFicheParrain(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("familles_fiche", "consulter") == False : return
        if len(self.Selection()) == 0 :
            dlg = wx.MessageDialog(self, _("Vous n'avez sélectionné aucune famille à ouvrir !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        track = self.Selection()[0]
        dlg = DLG_Famille.Dialog(self, track.IDparrain)
        dlg.ShowModal()
        dlg.Destroy()

    def OuvrirFicheFilleul(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("familles_fiche", "consulter") == False : return
        if len(self.Selection()) == 0 :
            dlg = wx.MessageDialog(self, _("Vous n'avez sélectionné aucune famille à ouvrir !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        track = self.Selection()[0]
        dlg = DLG_Famille.Dialog(self, track.IDfilleul)
        dlg.ShowModal()
        dlg.Destroy()

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
        # definition des sous-totaux de colonnes
        dictColonnes = {
            "libParrain" : {"mode" : "nombre", "singulier" : _("ligne"), "pluriel" : _("lignes"), "alignement" : wx.ALIGN_CENTER},
            "nbInscriptions" : {"mode" : "total"},
            "nbAttente" : {"mode" : "total"},
            "caFilleuls" : {"mode" : "total"},
            "solde" : {"mode" : "total"},
            "mttReduc" : {"mode" : "total"},
            }

        PanelAvecFooter.__init__(self, parent, ListView, kwargs, dictColonnes)


# ----------------- FRAME DE TEST ----------------------------------------------------------------

class MyFrame(wx.Frame):
    def __init__(self, footer,*args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self, -1)
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_1.Add(panel, 1, wx.ALL|wx.EXPAND)
        self.SetSizer(sizer_1)
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        #import time
        #t = time.time()
        if footer == "sans":
            self.myOlv = ListView(panel, -1, style=wx.LC_REPORT|wx.SUNKEN_BORDER)
            self.myOlv.MAJ()
            sizer_2.Add(self.myOlv, 1, wx.ALL|wx.EXPAND, 4)
        else:
            self.listviewAvecFooter = ListviewAvecFooter(self, kwargs={})
            self.ctrl_parrainages = self.listviewAvecFooter.GetListview()
            self.ctrl_recherche = CTRL_Outils(self, listview=self.ctrl_parrainages, afficherCocher=True)
            self.ctrl_recherche.SetBackgroundColour((255, 255, 255))
            sizer_2.Add(self.listviewAvecFooter, 1, wx.ALL|wx.EXPAND, 4)
        panel.SetSizer(sizer_2)
        self.SetSize((900, 400))
        self.Layout()

if __name__ == '__main__':
    app = wx.App(0)
    frame_1 = MyFrame("avec",None, -1, "ObjectListView")
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()
