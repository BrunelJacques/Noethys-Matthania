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
from Ctrl.CTRL_ObjectListView import ObjectListView, FastObjectListView, ColumnDefn, Filter, CTRL_Outils, PanelAvecFooter
from Utils import UTILS_Config
from Utils.UTILS_Decimal import FloatToDecimal as FloatToDecimal
from Utils import UTILS_Titulaires

SYMBOLE = UTILS_Config.GetParametre("monnaie_symbole", "€")

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
                    "IDcerfa",
                    "designation",
                    "mail_famille",
                    "montant",
                    "debut",
                    "fin",
                    "dateCerfa",
                    "cerfa",
                    ]
        for champ in lstChamps:
            action = "self.%s = dictValeurs[%s]" %(champ,"'"+champ+"'")
            try:
                #exec (action)
                setattr(self, "%s"%champ, dictValeurs["%s" % champ])
            except:
                print("OL_Attestations_cerfa_edition echec Track : ",action)
                pass

class ListView(FastObjectListView):
    def __init__(self, *args, **kwds):
        # Initialisation du listCtrl
        FastObjectListView.__init__(self, *args, **kwds)
        self.cerfasEmis = False
        # Binds perso
        self.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)
        self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)

    def OnLeftDown(self, event):
        event.Skip() 
        wx.CallAfter(self.MAJLabelListe)

    def InitModel(self):
        self.donnees = self.GetTracks()

    def GetTracks(self):
        # Récupération des données
        dictComptes = {}
        self.listeFamilles = []
        if self.cerfasEmis :
            # affichage de tous les cerfas de la période
            DB = GestionDB.DB()
            req = """
                    SELECT crfIDcerfa, crfIDfamille, crfDateEdition, crfIDutilisateur, 
                            crfDateDebut, crfDateFin, crfTotal, crfCerfa
                    FROM matCerfas
                    WHERE (crfDateDebut Between '%s' And '%s') OR (crfDateFin Between '%s' And '%s')
                ;""" % (self.periodeDeb, self.periodeFin, self.periodeDeb, self.periodeFin)
            ok = DB.ExecuterReq(req, MsgBox="OL_Attestations_cerfa_edition 1")
            recordset = DB.ResultatReq()
            for crfIDcerfa, crfIDfamille, crfDateEdition, crfIDutilisateur, crfDateDebut, crfDateFin, crfTotal, crfCerfa in recordset:
                self.listeFamilles.append(crfIDfamille)
            # Get noms Titulaires
            dictInfoFamilles = UTILS_Titulaires.GetTitulaires(self.listeFamilles)

            for crfIDcerfa, crfIDfamille, crfDateEdition, crfIDutilisateur, crfDateDebut, crfDateFin, crfTotal, crfCerfa in recordset:
                dictInfosTitulaires = dictInfoFamilles[crfIDfamille]
                if (crfIDcerfa in dictComptes) == False:
                    dictComptes[crfIDcerfa] = {
                        "IDfamille": crfIDfamille,
                        "dateCerfa": crfDateEdition,
                        "IDcerfa": crfIDcerfa,
                        "designation": dictInfosTitulaires["designation"],
                        "mail_famille": dictInfoFamilles[crfIDfamille]["mail_famille"],
                        "montant": crfTotal,
                        "debut": crfDateDebut,
                        "fin": crfDateFin,
                        "cerfa": "%s"%crfCerfa.decode('utf8')
                        }
        else:
            # cas de reprise des Cerfas générés sur la page précédente
            listeCerfasGeneres = self.listeCerfasGeneres
            for track in listeCerfasGeneres:
                self.listeFamilles.append(track.IDfamille)
            if len(self.listeFamilles) > 0:
                # Get noms Titulaires
                dictInfoFamilles = UTILS_Titulaires.GetTitulaires(self.listeFamilles)
                for track in listeCerfasGeneres :
                    IDcerfa = track.IDcerfa
                    dictInfosTitulaires = dictInfoFamilles[track.IDfamille]
                    if (IDcerfa in dictComptes) == False :
                        dictComptes[IDcerfa] = {
                            "IDfamille" : track.IDfamille,
                            "dateCerfa" : track.dateJour,
                            "IDcerfa" : IDcerfa,
                            "nomsTitulaires" : dictInfosTitulaires["designation"],
                            "mail": dictInfosTitulaires["mail_famille"],
                            "montant" : track.montant_retenu,
                            "debut": track.debut,
                            "fin": track.fin,
                            "cerfa":track.cerfa
                            }
        listeListeView = []
        # Transformation de dictComptes en listeListeView
        for IDcerfa, dictValeurs in dictComptes.items() :
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
            ColumnDefn(_("IDfamille"), 'right',40, "IDfamille", typeDonnee="entier",),
            ColumnDefn(_("Emission"), "centre", 80, "dateCerfa", typeDonnee="date",  stringConverter=FormateDateDD),
            ColumnDefn(_("IDcerfa"), 'right',80, "IDcerfa", typeDonnee="entier",),
            ColumnDefn(_("Famille"), 'left', 180, "designation", typeDonnee="texte",),
            ColumnDefn(_("mail"), 'left', 80, "mail_famille", typeDonnee="texte",),
            ColumnDefn(_("Montant"), "right", 70, "montant", typeDonnee="montant", stringConverter=FormateMontant),
            ColumnDefn(_("du"), "centre", 80, "debut", typeDonnee="date",  stringConverter=FormateDateDD),
            ColumnDefn(_("au"), "centre", 80, "fin", typeDonnee="date",  stringConverter=FormateDateDD),
            ]
        self.SetColumns(liste_Colonnes)
        self.CreateCheckStateColumn(0)
        self.SetEmptyListMsg(_("Aucune donnée"))
        self.SetEmptyListMsgFont(wx.FFont(11, wx.DEFAULT, faceName="Tekton"))
        self.SetSortColumn(self.columns[2])
        self.SetObjects(self.donnees)
        self.cellEditMode = FastObjectListView.CELLEDIT_DOUBLECLICK

    def MAJ(self, listeCerfasGeneres=[],periode = (None,None)):
        self.listeCerfasGeneres = listeCerfasGeneres
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
        if self.GetParent().GetName() == "DLG_Attestations_cerfa_edition" :
            self.GetParent().staticbox_attestations_staticbox.SetLabel(_("Cerfas générés (%d)") % len(self.GetTracksCoches()))

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

    def OnCerfasEmis(self):
        periode = self.GetParent().parent.page1.GetPeriode()
        periodeDeb, periodeFin = periode
        self.periodeDeb = periodeDeb
        self.periodeFin = periodeFin
        self.cerfasEmis = True
        self.donnees = self.GetTracks()
        self.InitObjectListView()
        self._ResizeSpaceFillingColumns()
        self.cerfasEmis = False

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

    def Impression(self, mode="preview"):
        if self.donnees == None or len(self.donnees) == 0 :
            dlg = wx.MessageDialog(self, _("Il n'y a aucune donnée à imprimer !"), _("Erreur"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        from Utils import UTILS_Printer
        prt = UTILS_Printer.ObjectListViewPrinter(self.GetSelectedObjects(), titre=_("Liste des dons pour cerfas"),
                                                  intro="", total="", format="A", orientation=wx.LANDSCAPE)
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
        self.parent = parent.parent
        dictColonnes = {
            "nomsTitulaires" : {"mode" : "nombre", "singulier" : _("famille"), "pluriel" : _("familles"),
                           "alignement" : wx.ALIGN_CENTER},
            "montant" : {"mode" : "total"},
            }
        PanelAvecFooter.__init__(self, parent, ListView, kwargs, dictColonnes)


# -------------------------------------------------------------------------------------------------------------------------------------------

if __name__ == '__main__':
    app = wx.App(0)
    from Dlg import DLG_Attestations_cerfa
    dlg = DLG_Attestations_cerfa.Dialog(None)
    dlg.ShowModal()
    dlg.Destroy()
    app.MainLoop()