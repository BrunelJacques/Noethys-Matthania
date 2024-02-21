#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, Matthania ajout de champs sur les groupes conditions age, analytique etc...
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS, JB, Jacques Brunel
# Copyright:       (c) 2010-11 Ivan LUCAS, JB
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------

from Utils.UTILS_Traduction import _
import Chemins
import wx
from FonctionsPerso import Nz
from Ctrl import CTRL_Bouton_image
import GestionDB

from Ctrl.CTRL_ObjectListView import FastObjectListView, ColumnDefn, Filter, CTRL_Outils

def FormateMontant(montant):
    if montant == None or montant == "": return ""
    return "%.2f" % (montant)

def FormateEntier(nombre):
    if nombre == None or nombre == "": return ""
    return "%.0f" % (nombre)

def FormateBool(nombre):
    if nombre == None or nombre == "" or int(nombre) == 0: return ""
    if int(nombre) == 1 : return "x"
    return "?"

# -------------------------------------------------------------------------------------------------------------------------------------------

class OlvTarifsNoms(FastObjectListView):
    # cadre olv dans l'écran du choix d'un tarif (saisie)
    def __init__(self, parent, *args, **kwds):
        self.parent = parent
        # Initialisation du listCtrl
        FastObjectListView.__init__(self, parent, **kwds)
        # Binds perso
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnActivate)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnActivate)
        self.InitObjectListView()

    def InitObjectListView(self):
        # Couleur en alternance des lignes
        self.oddRowsBackColor = "#F0FBED"
        self.evenRowsBackColor = wx.Colour(255, 255, 255)
        self.useExpansionColumn = True
        liste_Colonnes = [
            ColumnDefn(_("Code"), 'left', 120, "codeTarif", typeDonnee="texte", isSpaceFilling=True ),
            ColumnDefn(_("Nom Tarif"), 'left', 200, "nomTarif", typeDonnee="texte", isSpaceFilling=True),
            ColumnDefn(_("Prix article"), 'left', 100, "prixArticle", typeDonnee="montant", stringConverter=FormateMontant),
            ColumnDefn(_("Last Usage"), 'left', 100, "annee", typeDonnee="entier", stringConverter=FormateEntier),
        ]

        self.SetColumns(liste_Colonnes)
        self.SetEmptyListMsg(_("Aucun Tarif"))
        self.SetEmptyListMsgFont(wx.FFont(11, wx.DEFAULT, faceName="Tekton"))
        self.SetSortColumn(self.columns[2],False,False)

    def InitModel(self):
        self.tracksOLV = self.parent.tracksTarifsNoms
        self.SetObjects(self.tracksOLV)

    def MAJ(self, ID=None):
        self.InitModel()
        # Sélection d'un item
        if ID != None:
            obj = self.parent.tracksTarifsNoms[ID]
            self.SelectObject(obj, deselectOthers=True, ensureVisible=True)
        self._ResizeSpaceFillingColumns()

    def OnActivate(self,evt):
        prixArticle = self.GetSelectedObjects()[0].prixArticle
        if not prixArticle:
            prixArticle = 0.0
        self.parent.prixArticle = prixArticle
        self.parent.prix = prixArticle
        self.parent.ctrl_prix.SetValue("{:6.2f}".format(prixArticle))
        self.parent.ctrl_prix.SetFocus()

class Saisie(wx.Dialog):
    # écran du choix d'un tarif à appliquer
    def __init__(self, parent, codeTarif="", prix=None, cumul=None):
        wx.Dialog.__init__(self, parent, -1,
                           size=(450, 700),
                           style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        self.parent = parent
        self.prixArticle = None
        self.prix = None
        self.champsNoms = ["codeTarif", "nomTarif", "prixArticle", "annee"]
        self.lstCodesNoms, self.tracksTarifsNoms = self.GetTarifsNoms()
        IDselect = None
        if codeTarif:
            IDselect = self.lstCodesNoms.index(codeTarif)

        info = "Le choix ci-dessous s'appliquera aux lignes précédemment sélectionnées\n(les choix multiples étaient possibles)"
        self.text_info = wx.TextCtrl(self, -1, "",
                                     style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_CENTER,
                                     size=(500, 50))
        self.text_info.SetDefaultStyle(wx.TextAttr(wx.BLUE))
        self.text_info.WriteText(info)
        self.text_info.Enable(False)

        self.label_prix = wx.StaticText(self, -1, _("Prix de base:"))
        self.ctrl_prix = wx.TextCtrl(self, -1, "")

        self.staticbox_tarifNom = wx.StaticBox(self, -1, "Choix du tarif")
        self.olvTarifsNoms = OlvTarifsNoms(self, id=-1,
                                           style=wx.LC_HRULES | wx.LC_VRULES | wx.LC_SINGLE_SEL)
        self.olvTarifsNoms.MAJ(IDselect)
        self.ctrl_recherche = CTRL_Outils(self, listview=self.olvTarifsNoms)

        if prix != None:
            self.ctrl_prix.SetValue(str(prix))
        self.ctrl_cumul = wx.CheckBox(self, -1, "Sans réduction cumul et ministère")
        if cumul == 1:
            self.ctrl_cumul.SetValue(True)

        self.bouton_ok = CTRL_Bouton_image.CTRL(self, texte=_("Ok"),
                                                cheminImage="Images/32x32/Valider.png")
        self.bouton_annuler = CTRL_Bouton_image.CTRL(self, id=wx.ID_CANCEL,
                                                     texte=_("Annuler"),
                                                     cheminImage="Images/32x32/Annuler.png")

        self.SetTitle(_("Affectation d'un tarif"))
        self.SetMinSize((300, 400))

        self.olvTarifsNoms.SetToolTip(_("Choisissez le tarif à affecter"))
        infoPrix = _(
            "Ce prix de base >0 se substituera au 'prixParam1' des articles de typeLigne 'Séjour'")
        self.label_prix.SetToolTip(infoPrix)
        self.ctrl_prix.SetToolTip(infoPrix)
        mess = "Cette case excluera les inscriptions à ce tarif de la réduction cumul\n"
        mess += " et la réduction ministère ne sera pas proposée"
        self.ctrl_cumul.SetToolTip(mess)

        grid_sizer_base = wx.FlexGridSizer(rows=3, cols=1, vgap=10, hgap=10)
        grid_sizer_base.Add(self.text_info, 0, 0, 0)
        staticbox_olv = wx.StaticBoxSizer(self.staticbox_tarifNom, wx.VERTICAL)
        staticbox_olv.Add(self.olvTarifsNoms, 1, wx.EXPAND | wx.ALL, 10)
        staticbox_olv.Add(self.ctrl_recherche, 0, wx.EXPAND | wx.ALL, 10)
        grid_sizer_base.Add(staticbox_olv, 0, wx.EXPAND, 0)

        grid_sizer_boutons = wx.FlexGridSizer(rows=1, cols=6, vgap=10, hgap=10)

        grid_sizer_boutons.Add(self.label_prix, 0,
                               wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_boutons.Add(self.ctrl_prix, 1, wx.EXPAND, 0)
        grid_sizer_boutons.Add(self.ctrl_cumul, 1, wx.EXPAND, 0)
        grid_sizer_boutons.Add((20, 20), 1, wx.EXPAND, 0)
        grid_sizer_boutons.Add(self.bouton_ok, 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_annuler, 0, 0, 0)
        grid_sizer_boutons.AddGrowableCol(3)
        grid_sizer_base.Add(grid_sizer_boutons, 0,
                            wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 10)
        grid_sizer_base.AddGrowableCol(0)
        grid_sizer_base.AddGrowableRow(1)
        self.SetSizerAndFit(grid_sizer_base)
        self.Layout()
        self.Bind(wx.EVT_BUTTON, self.OnBoutonOk, self.bouton_ok)

    def GetChoix(self):
        selection = self.olvTarifsNoms.GetSelectedObject()
        codeTarif = selection.codeTarif
        nomTarif = selection.nomTarif
        prix = self.prix
        cumul = self.ctrl_cumul.GetValue()
        return (codeTarif, nomTarif, prix, cumul)

    def GetIsPrixArt(self):
        if self.prix == self.prixArticle:
            return True
        return False

    def GetTarifsNoms(self):
        # Récupération des noms de tous les Tarifs
        DB = GestionDB.DB()
        req = """
            SELECT matTarifsNoms.trnCodeTarif, matTarifsNoms.trnLibelle, Max(activites.date_fin), 
                    Max(If(matArticles.artCodeBlocFacture='Sejour',matArticles.artPrix1,0))
            FROM (((matTarifsNoms 
            INNER JOIN matTarifsLignes ON matTarifsNoms.trnCodeTarif = matTarifsLignes.trlCodeTarif) 
            LEFT JOIN matTarifs ON matTarifsNoms.trnCodeTarif = matTarifs.trfCodeTarif) 
            LEFT JOIN activites ON matTarifs.trfIDactivite = activites.IDactivite) 
            LEFT JOIN matArticles ON matTarifsLignes.trlCodeArticle = matArticles.artCodeArticle
            GROUP BY matTarifsNoms.trnCodeTarif, matTarifsNoms.trnLibelle
            ;"""
        DB.ExecuterReq(req, MsgBox="OL_Tarifs.GetTarifsNoms")
        lstTarifs = DB.ResultatReq()
        # regroupements sur des clés 'codeTarif"
        ddTarifsNoms = {}
        for codeTarif, nomTarif, date, prix in lstTarifs:
            try:
                dte = int(date[:4])
            except:
                dte = 0
            ddTarifsNoms[codeTarif] = {"nom": nomTarif, "annee": dte, "prixArticle": prix}
        # transposition en tracks
        tracksTarifsNoms = []
        lstCodesNoms = []
        for code in list(ddTarifsNoms.keys()):
            donnees = [
                code,
                ddTarifsNoms[code]["nom"],
                ddTarifsNoms[code]["prixArticle"],
                ddTarifsNoms[code]["annee"], ]
            tracksTarifsNoms.append(Track(donnees, self.champsNoms))
            lstCodesNoms.append(code)
        DB.Close()
        return lstCodesNoms, tracksTarifsNoms

    def OnBoutonOk(self, event):
        if not self.olvTarifsNoms.GetSelectedObject():
            mess = "Vous n'avez pas choisi un tarif à appliquer"
            wx.MessageBox(mess, "Validation impossible", wx.OK | wx.ICON_ERROR)
            return
        try:
            valPrix = float(self.ctrl_prix.GetValue())
        except:
            valPrix = None
            self.ctrl_prix.SetValue("")
        if valPrix == None:
            mess = "Vous n'avez pas saisi un nombre"
            wx.MessageBox(mess, "Validation impossible", wx.OK | wx.ICON_ERROR)
            return
        self.prix = valPrix
        self.EndModal(wx.ID_OK)

# -------------------------------------------------------------------------------------------------------------------------------------------

class Track(object):
    def __init__(self, donnees, champs):
        ix =0
        for champ in champs:
            setattr(self,champ,donnees[ix])
            ix +=1
        self.donnees = [x for x in donnees]

class ListView(FastObjectListView):
    # olv dans l'activité onglet tarifs en bas
    def __init__(self, parent,*args, **kwds):
        self.donnees = []
        self.select = []
        self.parent = parent
        # Récupération des paramètres perso
        self.champs = ["IDactivite","IDgroupe","IDcateg","nomCateg","nomGroupe","codeTarif","nomTarif","prix","cumul"]
        self.IDactivite = kwds.pop("IDactivite", None)
        self.listeFiltres = []
        # Initialisation du listCtrl
        FastObjectListView.__init__(self, parent, **kwds)
        # Binds perso
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnItemActivated)
        self.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)
        
    def OnItemActivated(self,event):
        # étend la sélection par un double clic à tous les tarifs de même catégorie
        self.EtendreCategorie(event)
                
    def InitModel(self):
        self.tracksCateg = self.parent.ctrl_categories.donnees
        self.tracksOLV = self.GetTracks()

    def GetTracks(self):
        tracksOLV = []
        dictTarifs = {}
        ltCateg = [(x.IDcategorie_tarif,x.nom,x.campeur) for x in self.tracksCateg]

        # Récupération des groupes
        db = GestionDB.DB()
        req = """SELECT groupes.IDgroupe, groupes.abrege, groupes.campeur
                FROM groupes
                WHERE groupes.IDactivite=%d
                ORDER BY groupes.ordre;""" % self.IDactivite
        db.ExecuterReq(req,MsgBox = True)
        listeDonnees = db.ResultatReq()
        dictGroupes = {}
        for IDgroupe, nomGroupe, campeur in listeDonnees :
            dictGroupes[IDgroupe] = {'nom':nomGroupe,'campeur':campeur}

        # Récupération des matTarifs et prix article
        req = """
                SELECT matTarifs.trfIDactivite, matTarifs.trfIDgroupe, 
                    matTarifs.trfIDcategorie_tarif, matTarifs.trfCodeTarif, 
                    matTarifs.trfPrix, matTarifs.trfCumul, matTarifsNoms.trnLibelle, 
                    Max(If(matArticles.artCodeBlocFacture = 'Sejour', matArticles.artPrix1,0))
                FROM ((matTarifs 
                    LEFT JOIN matTarifsLignes ON matTarifs.trfCodeTarif = matTarifsLignes.trlCodeTarif) 
                    INNER JOIN matTarifsNoms ON matTarifs.trfCodeTarif = matTarifsNoms.trnCodeTarif) 
                    LEFT JOIN matArticles ON matTarifsLignes.trlCodeArticle = matArticles.artCodeArticle
                WHERE (matTarifs.trfIDactivite = %s)
                GROUP BY matTarifs.trfIDactivite, matTarifs.trfIDgroupe, 
                    matTarifs.trfIDcategorie_tarif, matTarifs.trfCodeTarif, 
                    matTarifs.trfPrix, matTarifs.trfCumul, matTarifsNoms.trnLibelle
                ;""" % self.IDactivite
        db.ExecuterReq(req,MsgBox = True)
        lstMatTarifs = db.ResultatReq()
        for IDactivite,IDgroupe,IDcateg,codeTarif,prix,cumul,nomTarif,pxArt in lstMatTarifs :
            if Nz(prix) == 0:
                prix = pxArt
            dictTarifs[(IDactivite,IDgroupe,IDcateg)] = (codeTarif,prix,cumul,nomTarif)

        # composition du produit cartésien des tarifs potentiels
        for IDcateg,nomCateg,campeurCateg in ltCateg:
            for IDgroupe,dictGroupe in dictGroupes.items():
                if (self.IDactivite,IDgroupe,IDcateg) in list(dictTarifs.keys()):
                    (codeTarif, prix, cumul, nomTarif) = dictTarifs[(self.IDactivite,IDgroupe,IDcateg)]
                else: (codeTarif, prix, cumul, nomTarif) = (None,None,None,None)

                # champs: IDactivite,IDgroupe,IDcateg,nomCateg, nomGroupe,codeTarif,nomTarif,prix,cumul
                donnees = [self.IDactivite,IDgroupe,IDcateg,nomCateg,dictGroupe['nom'],codeTarif,nomTarif,prix,cumul]

                # filtrage de corresponndance entre les types campeur des groupes et categories_tarifs
                if dictGroupe['campeur'] != campeurCateg: # and campeurCateg != 0:
                    continue
                track = Track(donnees,self.champs)
                tracksOLV.append(track)
        db.Close()
        return tracksOLV
      
    def InitObjectListView(self):            
        # Couleur en alternance des lignes
        self.oddRowsBackColor = "#F0FBED" 
        self.evenRowsBackColor = wx.Colour(255, 255, 255)
        self.useExpansionColumn = True
        liste_Colonnes = [
            ColumnDefn(_("IDactivite"), "left", 0, "IDactivite",isSearchable=False),
            ColumnDefn(_("IDgroupe"), "left", 0, "IDgroupe",isSearchable=False),
            ColumnDefn(_("IDcategorie_tarif"), "left", 0, "IDcateg",isSearchable=False),
            ColumnDefn(_("Catégorie"), 'left', 200, "nomCateg", typeDonnee="texte", isSpaceFilling=True),
            ColumnDefn(_("Groupe"), 'left', 200, "nomGroupe", typeDonnee="texte",isSpaceFilling=True),
            ColumnDefn(_("Code"), 'left', 80, "codeTarif",typeDonnee="texte",),
            ColumnDefn(_("Nom Tarif"), 'left', 200, "nomTarif",typeDonnee="texte", isSpaceFilling=True),
            ColumnDefn(_("Prix"), 'right', 80, "prix",typeDonnee="montant",stringConverter= FormateMontant),
            ColumnDefn(_("ExcluCumul"), 'left', 80, "cumul",typeDonnee="montant",stringConverter= FormateBool),
            ]
        
        self.SetColumns(liste_Colonnes)
        self.SetEmptyListMsg(_("Aucun groupe"))
        self.SetEmptyListMsgFont(wx.FFont(11, wx.DEFAULT, faceName="Tekton"))
        self.SetSortColumn(self.columns[3])
        self.SetObjects(self.tracksOLV)
       
    def MAJ(self, ID=None):
        self.InitModel()
        self.InitObjectListView()
        # Sélection d'un item
        if ID != None :
            self.SelectObject(self.innerList[min(ID,len(self.innerList))], deselectOthers=True, ensureVisible=True)
        self._ResizeSpaceFillingColumns()
    
    def Selection(self):
        return self.GetSelectedObjects() 

    def OnContextMenu(self, event):
        """Ouverture du menu contextuel """
        if len(self.Selection()) == 0:
            noSelection = True
        else:
            noSelection = False
            ID = self.Selection()[0].IDgroupe
                
        # Création du menu contextuel
        menuPop = wx.Menu()

        # Item Modifier
        item = wx.MenuItem(menuPop, 10, _("Modifier"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Modifier.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.Modifier, id=10)
        
        menuPop.AppendSeparator()

        # Item Supprimer
        item = wx.MenuItem(menuPop, 30, _("Supprimer"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Supprimer.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.Supprimer, id=30)
        if noSelection == True : item.Enable(False)

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
        
        self.PopupMenu(menuPop)
        menuPop.Destroy()

    def Apercu(self, event):
        from Utils import UTILS_Printer
        prt = UTILS_Printer.ObjectListViewPrinter(self, titre=_("Liste des groupes"), format="A", orientation=wx.PORTRAIT)
        prt.Preview()

    def Imprimer(self, event):
        from Utils import UTILS_Printer
        prt = UTILS_Printer.ObjectListViewPrinter(self, titre=_("Liste des groupes"), format="A", orientation=wx.PORTRAIT)
        prt.Print()

    def Ajouter(self, event):
        # Recherche numéro d'ordre à appliquer
        listeTemp = []
        for track in self.tracksOLV :
            listeTemp.append(track.ordre)
        if len(listeTemp) > 0 :
            ordre = max(listeTemp) + 1
        else :
            ordre = 1
        # DLG Saisie
        dlg = Saisie(self)
        if dlg.ShowModal() == wx.ID_OK:
            nom = dlg.GetNom()
            abrege = dlg.GetAbrege()
            DB = GestionDB.DB()
            listeDonnees = [ ("IDactivite", self.IDactivite), ("nom", nom), ("ordre", ordre), ("abrege", abrege)]
            IDgroupe = DB.ReqInsert("groupes", listeDonnees)
            DB.Close()
            self.MAJ(IDgroupe)
        dlg.Destroy()
        #fin Ajouter

    def EtendreCategorie(self,event):
        # étend la sélection à toute la catégorie
        categorie = self.Selection()[0].IDcateg
        select = []
        for track in self.innerList:
            if track.IDcateg == categorie:
                self.SelectObject(track,deselectOthers=False)

    def Modifier(self, event):
        self.select = self.Selection()
        if len(self.Selection()) == 0 :
            dlg = wx.MessageDialog(self, _("Vous n'avez sélectionné aucun groupe à modifier dans la liste"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        codeTarif = self.Selection()[0].codeTarif
        prix = self.Selection()[0].prix
        cumul = self.Selection()[0].cumul

        # DLG Saisie de nouvelles valeurs
        dlg = Saisie(self, codeTarif, prix, cumul)
        # stockage au retour
        if dlg.ShowModal() == wx.ID_OK:
            choix = dlg.GetChoix()
            isPrixArticle = dlg.GetIsPrixArt()
            self.SauveSelection(isPrixArticle,*choix)
        dlg.Destroy()
        #fin Modifier

    def SauveSelection(self,isPrixArticle,codeTarif,nomTarif,prix,cumul,*args):
        # Sauvegarde de l'info saisie
        DB = GestionDB.DB()
        # modif dans olv et table matTarif
        for track in self.GetSelectedObjects():
            track.codeTarif = codeTarif
            track.nomTarif = nomTarif
            track.cumul = cumul
            if isPrixArticle:
                prixSauve = None
            else: prixSauve = prix
            listeCles = [("trfIDactivite", track.IDactivite),
                         ("trfIDgroupe", track.IDgroupe),
                         ("trfIDcategorie_tarif", track.IDcateg), ]
            listeDonnees = [("trfCodeTarif", track.codeTarif),
                            ("trfPrix", prixSauve),
                            ("trfCumul", cumul), ]
            oldCodeTarif = track.donnees[self.champs.index("codeTarif")]
            oldPrix = track.donnees[self.champs.index("prix")]
            oldCumul = track.donnees[self.champs.index("cumul")]
            # pas de changement, on passe
            if (oldCodeTarif, oldPrix, oldCumul) == (codeTarif, prix, cumul):
                continue
            # nouveau tarif associé on insère ou modifie
            if track.codeTarif and len(track.codeTarif) > 0:
                ret = DB.ReqInsert("matTarifs", listeCles + listeDonnees)
                if ret != "ok":
                    ret = DB.ReqMAJcles("matTarifs", listeDonnees, listeCles, MsgBox="OL_Tarifs.Modifier-Insert")
            # il n'y a plus de tarif associé on supprime
            else:
                if oldCodeTarif and len(oldCodeTarif) > 0:
                    # pas de tarif associé, on supprime les enregistrements précédents
                    ret = DB.ReqDELcles("matTarifs", listeCles=listeCles, MsgBox="OL_Tarifs.Modifier-delete")
            # stockage interne pour prochaines
            if not prix:
                prix = ""
            track.donnees[self.champs.index("codeTarif")] = codeTarif
            track.donnees[self.champs.index("nomTarif")] = nomTarif
            track.donnees[self.champs.index("prix")] = prix
            track.donnees[self.champs.index("cumul")] = cumul
            track.prix = prix # nécessaire pour forcer le refresh sur lui seulement!!
        req = "FLUSH TABLES matTarifs;"
        DB.ExecuterReq(req,MsgBox="OL_Tarifs FLUSH matTarifs;")
        DB.Close()
        for item in self.select:
            self.Select(self.innerList.index(item))
        self.Refresh()
        return  # fin de Sauve

    def Supprimer(self, event):
        if len(self.Selection()) == 0 :
            dlg = wx.MessageDialog(self, _("Vous n'avez sélectionné aucune ligne dans la liste pour supprimer son tarif "),
                                   _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return

        # Confirmation de suppression
        dlg = wx.MessageDialog(self, _("Souhaitez-vous vraiment supprimer les affectations de tarifs?"), _("Suppression"), wx.YES_NO|wx.NO_DEFAULT|wx.CANCEL|wx.ICON_INFORMATION)
        if dlg.ShowModal() == wx.ID_YES :
            self.SauveSelection(None,"","",None,None)
        dlg.Destroy()

# -------------------------------------------------------------------------------------------------------------------------------------------

class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self, -1, name="MyFrame")
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_1.Add(panel, 1, wx.ALL|wx.EXPAND)
        self.SetSizer(sizer_1)
        panel.ctrl_categories = ListView(self)
        self.myOlv = ListView(panel, IDactivite=401, id=-1, name="OL_test",
                              style=wx.LC_REPORT|wx.SUNKEN_BORDER|wx.LC_SINGLE_SEL|wx.LC_HRULES|wx.LC_VRULES)
        self.myOlv.MAJ() 
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_2.Add(self.myOlv, 1, wx.ALL|wx.EXPAND, 4)
        panel.SetSizer(sizer_2)
        self.Layout()

if __name__ == '__main__':
    app = wx.App(0)
    #wx.InitAllImageHandlers()
    frame_1 = MyFrame(None, -1, "OL TEST")
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()
