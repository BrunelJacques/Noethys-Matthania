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
import datetime
import GestionDB
from Ctrl.CTRL_ObjectListView import FastObjectListView, ColumnDefn, CellEditor,PanelAvecFooter, CTRL_Outils
from Utils import UTILS_Config
from Utils.UTILS_Decimal import FloatToDecimal as FloatToDecimal
from Utils import UTILS_Titulaires

SYMBOLE = UTILS_Config.GetParametre("monnaie_symbole", "€")

def DictToUnicode(dic):
    texte = "{"
    for cle in list(dic.keys()):
        valeur = dic[cle]
        sep = ""
        texte += "%s::%s%s%s##" % (cle, sep, valeur, sep)
    texte += "}"
    return texte.encode('utf-8')

def Nz(valeur):
    try:
        u = float(valeur)
    except:
        u = 0.0
    return u

def Fmt2d(montant):
    # Convert the given montant into a string with zero null
    if montant != 0:
        return "%.2f" % (montant)
    else:
        return " "


def DateEngFr(textDate):
    if textDate == None: return ""
    textDate = str(textDate)
    text = str(textDate[8:10]) + "/" + str(textDate[5:7]) + "/" + str(textDate[:4])
    return text

class Track(object):
    def __init__(self, dictValeurs):
        lstChamps = [
                    "IDfamille",
                    "rue_resid",
                    "cp_resid",
                    "ville_resid",
                    "nomsTitulairesAvecCivilite",
                    "nomsTitulairesSansCivilite",
                    "montant_dons",
                    "montant_donsHors",
                    "montant_regul",
                    "montant_retenu",
                    "labelDon",
                    "debut",
                    "fin",
                    "dateJour",
                    "nomPrenom",
                    "designation",
                    "mail_famille",
                    "lstDons",
                    "labelModeRegl",
                    "IDcerfa"
                    ]
        test = dictValeurs
        for champ in lstChamps:
            try:
                setattr(self, "%s" %champ, dictValeurs["%s"%champ])
            except:
                wx.MessageBox("echec 'cerfa_selection.Track' sur: dictValeurs['%s']"%champ)

class ListView(FastObjectListView):
    def __init__(self, *args, **kwds):
        self.listeTracksDons = []
        self.listeCerfasGeneres = []
        # Initialisation du listCtrl
        FastObjectListView.__init__(self, *args, **kwds)
        # Binds perso
        self.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)
        self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnModifie)

    def OnModifie(self,event):
        for obj in self.GetObjects():
            obj.montant_retenu = Nz(obj.montant_dons) + Nz(FloatToDecimal(obj.montant_regul))

    def OnLeftDown(self, event):
        event.Skip() 
        wx.CallAfter(self.MAJLabelListe)

    def InitModel(self):
        self.donnees = self.GetTracks()

    def GetTracks(self):
        # Récupération des données
        listeTracksDons = self.listeTracksDons
        dictComptes = {}
        self.listeFamilles = []
        for track in listeTracksDons:
            self.listeFamilles.append(track.IDfamille)
        # Get noms Titulaires
        dictInfoFamilles = UTILS_Titulaires.GetTitulaires(self.listeFamilles)

        periodeDeb = "%s"%self.periodeDeb
        periodeFin = "%s"%self.periodeFin

        for track in listeTracksDons :
            if track.montantDon == None: track.montantDon = 0.0
            if track.montantRegle == None: track.montantRegle = 0.0

            montantDon = track.montantDon
            ddeb = track.dateDon
            dfin = track.dateDon
            ddebRegl = track.debut
            dfinRegl = track.fin
            regul = track.montantDonHors
            if track.montantRegle < montantDon :
                #don limité au règlement, le reste est forcé en régul
                regul += montantDon - track.montantRegle
                montantDon = track.montantRegle
            else:
                #règlement limité à la partie don de la prestation
                track.montantRegle = montantDon

            # ajustement des dates  pour entrer dans la période
            if ddeb < periodeDeb :
                if ddebRegl > periodeDeb and ddebRegl < periodeFin:
                    ddeb = ddebRegl
                else:
                    ddeb = periodeDeb
            elif ddeb > periodeFin:
                if ddebRegl < periodeFin and ddebRegl > periodeDeb:
                    ddeb = ddebRegl
                else:
                    ddeb = periodeDeb

            if dfin > periodeFin :
                if dfinRegl > periodeDeb and dfinRegl < periodeFin and dfinRegl>= ddeb:
                    dfin = dfinRegl
                else:
                    dfin = periodeFin
            elif dfin < periodeDeb:
                if dfinRegl > periodeDeb and dfinRegl < periodeFin:
                    dfin = dfinRegl
                else:
                    dfin = periodeFin

            IDfamille = track.IDfamille

            dictInfosTitulaires = dictInfoFamilles[IDfamille]
            if (IDfamille in dictComptes) == False :
                # Récupération des infos sur la famille
                rue_resid = track.rue_resid
                if rue_resid == None : rue_resid = ""
                cp_resid = track.cp_resid
                if cp_resid == None : cp_resid = ""
                ville_resid = track.ville_resid
                if ville_resid == None : ville_resid = ""
                dictComptes[IDfamille] = {
                    "IDfamille" : IDfamille,
                    "rue_resid" : rue_resid,
                    "cp_resid" : cp_resid,
                    "ville_resid" : ville_resid,
                    "nomsTitulairesAvecCivilite" : dictInfosTitulaires["titulairesAvecCivilite"],
                    "nomsTitulairesSansCivilite" : dictInfosTitulaires["titulairesSansCivilite"],
                    "montant_dons" : 0,
                    "montant_donsHors" : 0,
                    "montant_regul" : 0,
                    "montant_retenu" : 0,
                    "labelDon": "",
                    "debut": ddeb,
                    "fin": dfin,
                    "nomPrenom": track.nomPrenom ,
                    "designation": track.designation,
                    'mail_famille': track.mail_famille,
                    "dateJour" : datetime.date.today(),
                    "lstDons": [],
                    "listeIDreglements":[],
                    "listeIDventil":[],
                    "listeVentil":[],
                    "labelModeRegl": "",
                    "IDcerfa": 0,
                    }

            #regroupement des dons sur la famille
            dict = dictComptes[IDfamille]
            dict["montant_dons"] +=  FloatToDecimal(montantDon)
            dict["montant_regul"] += FloatToDecimal(regul)
            dict["montant_retenu"] +=  FloatToDecimal(montantDon) + FloatToDecimal(regul)
            dict["labelDon"] +=  track.labelDon + ", "
            dictDon = {"IDprestation": track.IDprestation,
                        "montantLigne": FloatToDecimal(montantDon) + FloatToDecimal(regul),
                        "listeIDreglements": track.listeIDreglements,
                        "listeIDlignes":track.listeIDlignes
                        }
            dict["lstDons"].append(dictDon)
            # recomposition des listes mode et montant des règlements ventilés
            if dict["debut"] > ddeb:
                dict["debut"] = ddeb
            if dict["fin"] < dfin:
                dict["fin"] = dfin

            # recomposition du label reglements cumulé sur tous les dons regroupés
            if not track.labelModeRegl in dict["labelModeRegl"]:
                dict["labelModeRegl"] += track.labelModeRegl

        listeListeView = []
        # Transformation de dictComptes en listeListeView
        for IDfamille, dictValeurs in dictComptes.items() :
            track = Track(dictValeurs)
            listeListeView.append(track)
        return listeListeView

    def InitObjectListView(self):

        def FormateDateDD(dateDD):
            if dateDD == None : return ""
            return DateEngFr(str(dateDD))

        def FormateMontant(montant):
            if montant == None or montant == "" or montant == FloatToDecimal(0.0) : return ""
            return "%.2f %s" % (montant, SYMBOLE)

        # Couleur en alternance des lignes
        self.oddRowsBackColor = "#F0FBED" 
        self.evenRowsBackColor = wx.Colour(255, 255, 255)
        self.useExpansionColumn = True

        liste_Colonnes = [
            ColumnDefn(_("IDfamille"), 'right',40, "IDfamille", typeDonnee="entier", isEditable=False),
            ColumnDefn(_("Famille"), 'left', 180, "designation", typeDonnee="texte",),
            ColumnDefn(_("mail"), 'left', 80, "mail_famille", typeDonnee="texte",),
            ColumnDefn(_("Description"), "left", 180, "labelDon", typeDonnee="texte", isEditable=False),
            ColumnDefn(_("Montant"), "right", 70, "montant_dons", typeDonnee="montant", isEditable=False, stringConverter=FormateMontant),
            ColumnDefn(_("Forcer"), "right", 70, "montant_regul", typeDonnee="montant", isEditable=True, stringConverter=Fmt2d,
                       cellEditorCreator = CellEditor.FloatEditor),
            ColumnDefn(_("Retenu"), "right", 70, "montant_retenu", typeDonnee="montant", isEditable=False, stringConverter=Fmt2d),
            ColumnDefn(_("du"), "centre", 80, "debut", typeDonnee="date", isEditable=True, stringConverter=FormateDateDD),
            ColumnDefn(_("au"), "centre", 80, "fin", typeDonnee="date", isEditable=True, stringConverter=FormateDateDD),
            ColumnDefn(_("ModeRegl."), "left", 150, "labelModeRegl", typeDonnee="texte", isEditable=True),
            ColumnDefn(_("Cp"), "left", 50, "cp_resid", typeDonnee="texte", isEditable=False),
            ]
        self.SetColumns(liste_Colonnes)
        self.CreateCheckStateColumn(0)
        self.SetEmptyListMsg(_("Aucune donnée"))
        self.SetEmptyListMsgFont(wx.FFont(11, wx.DEFAULT, faceName="Tekton"))
        self.SetSortColumn(self.columns[2])
        self.SetObjects(self.donnees)
        self.cellEditMode = FastObjectListView.CELLEDIT_DOUBLECLICK

    def MAJ(self, listeTracksDons=[],periode = (None,None)):
        self.listeTracksDons = listeTracksDons
        self.periodeDeb, self.periodeFin = periode
        #le millesime détermine la plage de numéros des Cerfas sur 9 chiffres
        self.millesime = self.periodeDeb.year
        self.noMax = ((self.millesime + 1) * 100000)-1
        self.noMin = self.millesime * 100000
        self.InitModel()
        self.InitObjectListView()
        self.CocherTout()
        self._ResizeSpaceFillingColumns() 

    def Selection(self):
        return self.GetSelectedObjects()

    def CocherTout(self, event=None):
        for track in self.donnees :
            self.Check(track)
            self.RefreshObject(track)
        self.MAJLabelListe() 

    def CocherRien(self, event=None):
        for track in self.donnees :
            self.Uncheck(track)
            self.RefreshObject(track)
        self.MAJLabelListe() 
    
    def MAJLabelListe(self):
        if self.GetParent().GetName() == "DLG_Attestations_cerfa_selection" :
            self.GetParent().staticbox_attestations_staticbox.SetLabel(_("Attestations à générer (%d)") % len(self.GetTracksCoches()))
        
    def GetTracksCoches(self):
        return self.GetCheckedObjects()
    
    def GetInfosCoches(self):
        listeDonnees = []
        for track in self.GetTracksCoches() :
            dictTemp = track.GetDict()
            for code, valeur in self.dictOrganisme.items() :
                dictTemp[code] = valeur
            listeDonnees.append(dictTemp)
        return listeDonnees

    def OnContextMenu(self, event):
        """Ouverture du menu contextuel """            
        # Création du menu contextuel
        menuPop = wx.Menu()

        # Tout sélectionner
        item = wx.MenuItem(menuPop, 20, _("Tout cocher"))
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.CocherTout, id=20)

        # Tout dé-sélectionner
        item = wx.MenuItem(menuPop, 30, _("Tout décocher"))
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.CocherRien, id=30)
        
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

    def Generation(self):
        self.listeCerfasGeneres = []
        DB = GestionDB.DB()
        # recherche du numéro cerfa
        req =   """
                SELECT Max(matCerfas.crfIDcerfa)
                FROM matCerfas
                WHERE ((matCerfas.crfIDcerfa > %d) AND (matCerfas.crfIDcerfa < %d))
                ;""" % (self.noMin, self.noMax)
        ok = DB.ExecuterReq(req,MsgBox="OL_Attestations_cerfa_selection_maxNumCerfa")
        recordset = DB.ResultatReq()
        IDcerfa = self.noMin + 1
        for (numMax,) in recordset:
            if numMax != None:
                IDcerfa = numMax +1
        user = DB.IDutilisateurActuel()
        # Alimentation de la table matCerfas des cotisations sélectionnées
        for track in self.GetTracksCoches() :
            track.dateJour = datetime.date.today()
            track.cerfa = DictToUnicode(track.__dict__)
            listeDonnees = [
                            ("crfIDcerfa",IDcerfa),
                            ("crfIDfamille", track.IDfamille),
                            ("crfDateEdition", track.dateJour),
                            ("crfIDutilisateur",user),
                            ("crfDateDebut", track.debut),
                            ("crfDateFin", track.fin),
                            ("crfTotal", float(track.montant_retenu)),
                            ("crfCerfa", track.cerfa),
                            ]
            DB.ReqInsert(nomTable = 'matCerfas', listeDonnees = listeDonnees, MsgBox = 'OL_Attestations_cerfa_selection_insertCerfa')
            track.IDcerfa = IDcerfa
            # géstion des lignes de dons portées par le Cerfas
            for don in track.lstDons:
                for IDligne in don["listeIDlignes"]:
                    listeDonnees=[
                                ("crlIDcerfa",IDcerfa),
                                ("crlIDprestation",don["IDprestation"]),
                                ("crlIDligne", IDligne),
                                ("crlIDfamille", track.IDfamille),
                                ("crlMontant", don["montantLigne"]),
                                ("crlReglements", str(don["listeIDreglements"])[1:-1]),
                    ]
                    DB.ReqInsert(nomTable = 'matCerfasLignes', listeDonnees = listeDonnees, MsgBox = 'OL_Attestations_cerfa_selection_insertCerfaLignes')
            self.listeCerfasGeneres.append(track)
            IDcerfa +=1
        DB.Close()
        if len(self.listeCerfasGeneres) != 1:
            mess = "%d cerfas ont été générés,\n\nvous pouvez les imprimer pour voir les numéros"%len(self.listeCerfasGeneres)
        else: mess = "%d cerfa a été généré,\n\nvous pouvez l'imprimer pour voir son numéro"%len(self.listeCerfasGeneres)
        wx.MessageBox(mess)
        return True

    def Impression(self, mode="preview"):
        if self.donnees == None or len(self.donnees) == 0 :
            dlg = wx.MessageDialog(self, _("Il n'y a aucune donnée à imprimer !"), _("Erreur"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        from Utils import UTILS_Printer
        prt = UTILS_Printer.ObjectListViewPrinter(self, titre=_("Liste des dons pour cerfas"), intro="", total="", format="A", orientation=wx.LANDSCAPE)
        if mode == "preview" :
            prt.Preview()
        else:
            prt.Print()
        
    def Apercu(self, event):
        self.Impression("preview")

    def Imprimer(self, event):
        self.Impression("print")

    def ExportTexte(self, event):
        from Utils import UTILS_Export
        UTILS_Export.ExportTexte(self, titre=_("Liste des dons pour cerfas"))
        
    def ExportExcel(self, event):
        from Utils import UTILS_Export
        UTILS_Export.ExportExcel(self, titre=_("Liste des dons pour cerfas"))

class ListviewAvecFooter(PanelAvecFooter):
    def __init__(self, parent, kwargs={}):
        dictColonnes = {
            "labelDon" : {"mode" : "nombre", "singulier" : _("famille"), "pluriel" : _("familles"),
                           "alignement" : wx.ALIGN_CENTER},
            "montant_retenu" : {"mode" : "total"},
            }
        PanelAvecFooter.__init__(self, parent, ListView, kwargs, dictColonnes)

# -------------------------------------------------------------------------------------------------------------------------------------------

class MyFrame(wx.Frame):
    def __init__(self, parent, listeTracksDons=[]):
        wx.Frame.__init__(self, parent, -1)
        panel = wx.Panel(self, -1, name="test1")
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_1.Add(panel, 1, wx.ALL|wx.EXPAND)
        self.SetSizer(sizer_1)
        self.myOlv = ListView(panel, id=-1, name="OL_test", style=wx.LC_REPORT|wx.SUNKEN_BORDER|wx.LC_SINGLE_SEL|wx.LC_HRULES|wx.LC_VRULES)
        self.myOlv.MAJ(listeTracksDons)
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_2.Add(self.myOlv, 1, wx.ALL|wx.EXPAND, 4)
        panel.SetSizer(sizer_2)
        self.Layout()

if __name__ == '__main__':
    app = wx.App(0)
    #wx.InitAllImageHandlers()
##    from Dlg import DLG_Attestations_cerfa_parametres
##    frame_1 = DLG_Attestations_cerfa_parametres.MyFrame(None)
##    frame_1.SetSize((980, 650))
##    frame_1.CenterOnScreen() 
##    app.SetTopWindow(frame_1)
##    frame_1.Show()
##    app.MainLoop()

    from Dlg import DLG_Attestations_cerfa
    dlg = DLG_Attestations_cerfa.Dialog(None)
    dlg.ShowModal()
    dlg.Destroy()
    app.MainLoop()