#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#-----------------------------------------------------------
# Application :    Noethys branche Matthania
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS, JB adapté aux groupes par Jacques BRUNEL
# Copyright:       (c) 2010-12 Ivan LUCAS, JB
# Licence:         Licence GNU GPL
#-----------------------------------------------------------
from Dlg import DLG_Parametres_nbre_inscrits
from Utils.UTILS_Traduction import _
import wx
import Chemins
import GestionDB
from Utils import UTILS_Config
from wx.lib.agw import ultimatelistctrl as ULC

COULEUR_TRAIT = wx.Colour(200, 200, 200)
COULEUR_TEXTE = "BLACK"
COULEUR_DISPONIBLE = "#E3FEDB"
COULEUR_ALERTE = "#FEFCDB"
COULEUR_COMPLET = "#F7ACB2"
COULEUR_GAUGE_FOND = "WHITE"


class Renderer_gauge(object):
    def __init__(self, parent):
        self.parent = parent
        self.hauteurGauge = 18
        self.seuil_alerte = self.parent.seuil_alerte
        self.nbreCampeurs = 0
        self.nbrePlacesDispo = 0
        self.nbreResas = 0
        self.nbreDevis = 0

    def DrawSubItem(self, dc, rect, line, highlighted, enabled):
        canvas = wx.Bitmap(rect.width, rect.height)
        mdc = wx.MemoryDC()
        mdc.SelectObject(canvas)
        
        # Dessin du fond
        if highlighted:
            mdc.SetBackground(wx.Brush(wx.SystemSettings_GetColour(wx.SYS_COLOUR_HIGHLIGHT)))
        else:
            couleurFond = self.parent.couleurFond
            mdc.SetBackground(wx.Brush(couleurFond))
        mdc.Clear()
        
        # Dessin de la gauge
        self.DrawGauge(mdc, 0, 0, rect.width, rect.height)
        
        # Dessin du texte
        mdc.SetFont(wx.Font(7, wx.SWISS, wx.NORMAL, wx.NORMAL))
        if self.nbreCampeurs == 1 :
            texte = _("1 campeur")
        else :
            texte = _("%d campeurs") % self.nbreCampeurs

        if self.nbreResas > 0 :
                texte += _(" + %d réserv.") % self.nbreResas

        if self.nbreDevis > 0 :
                texte += _(" + %d devis") % self.nbreDevis

        if self.nbrePlacesDispo > 0 :
            texte += _(" / %d places") % self.nbrePlacesDispo

        if self.nbreAnims > 0 :
            if self.nbreAnims == 1 :
                texte += _(" + un anim")
            else :
                texte += _(" + %d anims") % self.nbreAnims

        if self.nbreStaff > 0 :
            if self.nbreStaff == 1 :
                texte += _(" + un autre")
            else :
                texte += _(" + %d autres") % self.nbreStaff

        textWidth, dummy = mdc.GetTextExtent(texte)
        mdc.SetTextForeground(COULEUR_TEXTE)
        x = rect.width/2 - textWidth/2
        x = 0 + 4
        mdc.DrawText(texte, int(x), int(rect.height/2 - dummy/2))
        
        # Double buffering
        dc.SetClippingRegion(rect.x, rect.y, rect.width, rect.height)
        dc.Blit(rect.x+3, rect.y, rect.width-6, rect.height, mdc, 0, 0)
        dc.DestroyClippingRegion()
        
    def GetLineHeight(self):
        return self.hauteurGauge + 3

    def GetSubItemWidth(self):
        return 10

    def DrawGauge(self, dc, x, y, w, h):
        w -= 8

        # Gauge de fond
        dc.SetBrush(wx.Brush(COULEUR_GAUGE_FOND))
        dc.SetPen(wx.TRANSPARENT_PEN)
        dc.DrawRectangle(0, int((h-self.hauteurGauge)/2) , int(w), int(self.hauteurGauge))

        # Gauge d'inscriptions
        if self.nbrePlacesDispo != 0 :
            largeurGauge = 1.0 * (self.nbreCampeurs + self.nbreResas + self.nbreDevis) / self.nbrePlacesDispo * w
        else :
            largeurGauge = w
        if largeurGauge > w :
            largeurGauge = w
        
        etat = "disponible"
        couleur = None
        if self.nbrePlacesDispo == 0:
            couleur = COULEUR_DISPONIBLE
        else :
            nbreInscritsCamp = self.nbreCampeurs + self.nbreResas + self.nbreDevis
            nbrePlacesRestantes = self.nbrePlacesDispo - nbreInscritsCamp
            txRestantes = round(100 * nbrePlacesRestantes / self.nbrePlacesDispo ,2)
            if nbrePlacesRestantes <= 0:
                etat = "complet"
                couleur = COULEUR_COMPLET
            elif txRestantes <= self.seuil_alerte :
                etat = "alerte"
                couleur = COULEUR_ALERTE
            else:
                etat = "disponible"
                couleur = COULEUR_DISPONIBLE

        dc.SetBrush(wx.Brush(couleur))
        dc.SetPen(wx.Pen(COULEUR_TRAIT, 1))
        dc.DrawRectangle(0, int((h-self.hauteurGauge)/2) , int(largeurGauge), int(self.hauteurGauge))
        
        if etat == "alerte" :
            tailleImage = 16
            dc.DrawBitmap(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Attention.png"), wx.BITMAP_TYPE_ANY) , largeurGauge-tailleImage-2, (h-tailleImage)/2)

    def SetValeurs(self, nbreCampeurs=0, nbrePlacesDispo=0, nbreResas=0, nbreDevis=0, nbreAnims=0, nbreStaff=0):
        self.nbreCampeurs = nbreCampeurs
        self.nbrePlacesDispo = nbrePlacesDispo
        self.nbreResas = nbreResas
        self.nbreDevis = nbreDevis
        self.nbreAnims = nbreAnims
        self.nbreStaff = nbreStaff

# ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
            
class CTRL(ULC.UltimateListCtrl):
    def __init__(self, parent, style=ULC.ULC_SINGLE_SEL | ULC.ULC_REPORT | ULC.ULC_NO_HEADER | ULC.ULC_HAS_VARIABLE_ROW_HEIGHT):
        ULC.UltimateListCtrl.__init__(self, parent, -1, agwStyle=style)
        self.parent = parent
        self.listeGroupes = []
        
        self.couleurFond = wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW)
        # self.couleurFond = wx.SystemSettings.GetColour(wx.SYS_COLOUR_FRAMEBK)
        self.SetBackgroundColour(self.couleurFond)

        # Création des colonnes
        self.InsertColumn(0, _("Activité"), width=50, format=ULC.ULC_FORMAT_LEFT)
        self.InsertColumn(1, _("Nom du groupe"), width=200, format=ULC.ULC_FORMAT_RIGHT)
        self.InsertColumn(2, _("Nbre inscrits"), width=200, format=ULC.ULC_FORMAT_CENTRE)


        # Binds
        self.Bind(wx.EVT_RIGHT_DOWN, self.OnContextMenu)
        self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)

    def OnLeftDown(self, event):
        pass

    def OnContextMenu(self, event):
        pass

    def MAJ(self, forcerActualisation=False):
        condition = ""
        
        # Recherche des paramètres
        activites = UTILS_Config.GetParametre("nbre_campeurs_parametre_activites", defaut=None)
        if activites and ("###" in activites ):
            label, activites = activites.split("###")
        if activites != None and activites != '':
            listeID = []
            for ID in activites.split(";") :
                    listeID.append(int(ID))
            condition = "inscriptions.IDactivite IN %s" % GestionDB.ConvertConditionChaine(listeID)
        else:
            condition = "1 = 0"

        # Tri
        choixTri = UTILS_Config.GetParametre("nbre_campeurs_parametre_tri", 3)
        libelle,champTrie = DLG_Parametres_nbre_inscrits.CHOICES_TRI_GROUPES[choixTri]
        if isinstance(champTrie,str):
            tri = champTrie
        else: tri = ""

        # Sens
        choixSens = UTILS_Config.GetParametre("nbre_campeurs_parametre_sens", 1)
        if choixSens == 0:
            sens = ""
        else :
            sens = "DESC"
        order = ""
        if len(tri)>0:
            order = "ORDER BY %s %s"%(tri, sens)

        # Seuil d'alerte
        self.seuil_alerte = UTILS_Config.GetParametre("nbre_campeurs_parametre_alerte", 15)

        # Recherche des données
        DB = GestionDB.DB()
        # IDgroupe,nomAct,comptaAct,abregeGrp,nomGrp,nbreMaxi,ageMini,ageMaxi,nature,campeur,nbreInscrits
        req = """
        SELECT 	groupes.IDgroupe, activites.nom, activites.code_comptable, groupes.nom, groupes.abrege,
                groupes.nbre_inscrits_max,groupes.ageMini, groupes.ageMaxi, 
                natureInscription.pieNature, categories_tarifs.campeur,
                Count(inscriptions.IDinscription) AS nbreInscrits
        FROM ((((
            activites 
            LEFT JOIN groupes_activites ON activites.IDactivite = groupes_activites.IDactivite) 
            INNER JOIN 	groupes ON activites.IDactivite = groupes.IDactivite) 
                        LEFT JOIN inscriptions ON (groupes.IDgroupe = inscriptions.IDgroupe) 
                                    AND (groupes.IDactivite = inscriptions.IDactivite)) 
            LEFT JOIN categories_tarifs ON inscriptions.IDcategorie_tarif = categories_tarifs.IDcategorie_tarif) 
            LEFT JOIN 
                (	SELECT inscriptions.IDinscription, Max(matPieces.pieNature) AS pieNature
                    FROM inscriptions INNER JOIN matPieces ON inscriptions.IDinscription = matPieces.pieIDinscription
                    GROUP BY inscriptions.IDinscription
                ) AS natureInscription ON inscriptions.IDinscription = natureInscription.IDinscription
        WHERE %s
        GROUP BY groupes.IDgroupe, activites.nom, activites.code_comptable, groupes.nom, groupes.abrege, 
                groupes.nbre_inscrits_max, groupes.ageMini, groupes.ageMaxi, 
                natureInscription.pieNature,categories_tarifs.campeur
        %s
        ;""" % (condition, order)
        ret = DB.ExecuterReq(req,MsgBox="DLG_Nbre_pargroupe.MAJ")
        listeDonnees = DB.ResultatReq() 
        DB.Close()
        dictGroupesTemp = {}
        lstKeys = []

        # compose le texte limite d'age qui sera sur la ligne
        def LimitesAge():
            bas = False
            haut = False
            if ageMini and ageMini > 0:
                bas = True
            if ageMaxi and ageMaxi > 0:
                haut = True
            if bas and haut:
                txt = "(%d-%d)"%(bas,haut)
            elif bas:
                txt = "(+%d)"%(bas)
            else:
                txt = "(-%d)"%(haut)
            return txt

        def CalculeTauxRemplis(dictGrp):
            nbreInscritsCamp = dictGrp["nbreCampeurs"] + dictGrp["nbreResas"] + dictGrp["nbreDevis"]
            if dictGrp["nbrePlacesDispo"] == 0:
                if sens == "DESC":
                    txRemplis = -1.0
                else:
                    txRemplis = 101.0
            else:
                txRemplis = round(100 * float(nbreInscritsCamp) / float(dictGrp["nbrePlacesDispo"]) ,2)
            # pour différencier les exequos sans places dispos, ajout de décimale sur nbre d'inscrits
            txRemplis += float(dictGrp["nbreInscrits"]) / 100
            dictGrp["txRemplis"] = txRemplis

        # ------------------ Dictionnaire de données -----------------------------
        for IDgroupe,nomAct,comptaAct,nomGrp,abregeGrp,nbreMaxi,ageMini,ageMaxi,nature,campeur,nbreInscrits in listeDonnees :
            if nature in ("AVO",):
                continue
            lstKeys.append(IDgroupe)
            nbreCampeurs = 0
            nbreResas = 0
            nbreDevis = 0
            nbreAnims = 0
            nbreStaff = 0
            if nbreMaxi == None : nbreMaxi = 0
            if nbreInscrits == None : nbreInscrits = 0
            if campeur == None : campeur = 1
            if comptaAct == None: comptaAct = ""
            if nomGrp == None : nomGrp = _("Sans nom !")
            # normalisation préfixe compte analytique en début de nom
            if comptaAct == nomAct[:len(comptaAct)]:
                nomAct = nomAct[len(comptaAct):].strip()
            nomAct = ("%s %s"%(comptaAct,nomAct))[:22]
            nomGrp = nomGrp.strip()
            # affectation du nombre d'inscrit selon son type
            if campeur == 1:
                if nature == "DEV":
                    nbreDevis = nbreInscrits
                elif nature == "RES":
                    nbreResas = nbreInscrits
                else: nbreCampeurs = nbreInscrits
            elif campeur == 0:
                nbreAnims = nbreInscrits
            else:
                nbreStaff = nbreInscrits
            limiteAge = LimitesAge()
            if IDgroupe == 1923:
                pass

            if not IDgroupe in list(dictGroupesTemp.keys()):
                dictGroupesTemp[IDgroupe] = {"IDgroupe" : IDgroupe, "nomGrp" : nomGrp,"abregeGrp" : abregeGrp,
                                             "nomAct":nomAct,"comptaAct":comptaAct,"limitesAge":limiteAge,
                                             "nbreCampeurs":nbreCampeurs,"nbreResas":nbreResas,"nbreDevis":nbreDevis,
                                             "nbreAnims":nbreAnims,"nbreStaff":nbreStaff,
                                             "nbreInscrits": nbreInscrits, "nbrePlacesDispo" : nbreMaxi}
            else:
                dictGroupe = dictGroupesTemp[IDgroupe]
                for champ,valeur in [("nbreCampeurs",nbreCampeurs),("nbreResas",nbreResas),("nbreDevis",nbreDevis),
                                     ("nbreAnims",nbreAnims),("nbreStaff",nbreStaff),("nbreInscrits",nbreInscrits)]:
                    dictGroupe[champ] += valeur
            CalculeTauxRemplis(dictGroupesTemp[IDgroupe])
            if nbreAnims > 0:
                pass

        def takeFirst(item):
            return item[0]

        if champTrie == 99:
            # calcul des clés de tri sur taux de remplis
            ltCles = []
            for key, dictGroupe in dictGroupesTemp.items():
                tpl = (dictGroupe["txRemplis"],key)
                if not tpl in ltCles:
                    ltCles.append(tpl)
            if sens == "DESC":
                rev = True
            else: rev = False
            ltCles.sort(reverse=rev, key=takeFirst)
            lstKeys = [y for x,y in ltCles]
        listeGroupesTemp = []
        # tri des lignes par rappel de l'ordre dans select
        for key in lstKeys:
            dictGroupe = dictGroupesTemp[key]
            listeGroupesTemp.append(dictGroupe)
        # Pour éviter l'actualisation de l'affichage si aucune modification des données
        if self.listeGroupes != listeGroupesTemp or forcerActualisation == True :
            self.listeGroupes = listeGroupesTemp
        else :
            return
        
        # MAJ du contrôle
        self.DeleteAllItems() 
        
        self.dictRenderers = {}
        index = 0
        for dictGroupe in self.listeGroupes :
            
            # Colonne Activité
            label = " " + dictGroupe["nomAct"]
            self.InsertStringItem(index,label )
            # Colonne Groupe
            label = " " + dictGroupe["nomGrp"]
            self.SetStringItem(index, 1, label)
            #self.SetItemData(index, dictGroupe)

            # Colonne Gauge
            renderer = Renderer_gauge(self)
            renderer.SetValeurs(nbreCampeurs=dictGroupe["nbreCampeurs"],
                                nbrePlacesDispo=dictGroupe["nbrePlacesDispo"],
                                nbreResas = dictGroupe["nbreResas"],
                                nbreDevis = dictGroupe["nbreDevis"],
                                nbreAnims = dictGroupe["nbreAnims"],
                                nbreStaff = dictGroupe["nbreStaff"])
            self.dictRenderers[index] = renderer
            self.SetItemCustomRenderer(index, 2, renderer)
                
            index += 1
        
        # Ajuste la taille des colonnes
        self.SetColumnWidth(0, wx.LIST_AUTOSIZE)
        self.SetColumnWidth(1, wx.LIST_AUTOSIZE)
        self.SetColumnWidth(2, ULC.ULC_AUTOSIZE_FILL)
        
        # Actualiser l'affichage pour éviter bug de positionnement
        try :
            self.DoLayout() 
        except :
            pass

# ----------------------------------------------------------------------------------------------------------------------        

class Panel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, id=-1, style=wx.TAB_TRAVERSAL)
        self.parent = parent

        # Messages
        self.ctrl_inscriptions = CTRL(self)
        
        # Commandes
        self.bouton_parametres = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Mecanisme.png"), wx.BITMAP_TYPE_PNG))
        self.bouton_parametres.SetToolTip(_("Cliquez ici pour modifier les paramètres d'affichage"))
        self.bouton_outils = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Outils.png"), wx.BITMAP_TYPE_PNG))
        self.bouton_outils.SetToolTip(_("Cliquez ici pour accéder aux outils"))

        self.__do_layout()
        
        # Binds
        self.Bind(wx.EVT_BUTTON, self.OnBoutonParametres, self.bouton_parametres)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonOutils, self.bouton_outils)

    def __do_layout(self):
        sizer_base = wx.BoxSizer(wx.VERTICAL)
        grid_sizer = wx.FlexGridSizer(rows=2, cols=2, vgap=5, hgap=5)
        grid_sizer.Add(self.ctrl_inscriptions, 1, wx.EXPAND|wx.TOP|wx.LEFT|wx.BOTTOM, 10)
        grid_sizer_boutons = wx.FlexGridSizer(rows=4, cols=1, vgap=5, hgap=5)
        grid_sizer_boutons.Add(self.bouton_parametres, 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_outils, 0, 0, 0)
        grid_sizer.Add(grid_sizer_boutons, 1, wx.EXPAND|wx.TOP|wx.RIGHT|wx.BOTTOM, 10)
        grid_sizer.AddGrowableRow(0)
        grid_sizer.AddGrowableCol(0)
        self.SetSizer(grid_sizer)
        self.Layout()
    
    def MAJ(self):
        self.ctrl_inscriptions.MAJ() 

    def OnBoutonParametres(self, event):
        from Dlg import DLG_Parametres_nbre_inscrits
        dlg = DLG_Parametres_nbre_inscrits.DlgGroupes(self)
        reponse = dlg.ShowModal()
        if reponse == wx.ID_OK :
            self.ctrl_inscriptions.MAJ(forcerActualisation=True) 
        
    def OnBoutonOutils(self, event):
        # Création du menu contextuel
        menuPop = wx.Menu()

        # Item Actualiser
        item = wx.MenuItem(menuPop, 10, _("Actualiser"))
        item.SetBitmap(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Actualiser2.png"), wx.BITMAP_TYPE_PNG))
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.Actualiser, id=10)

        menuPop.AppendSeparator()
        
        item = wx.MenuItem(menuPop, 20, _("Aide"), _("Aide"))
        item.SetBitmap(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Aide.png"), wx.BITMAP_TYPE_PNG))
        menuPop.Append(item)
        self.Bind(wx.EVT_MENU, self.Aide, id=20)

        self.PopupMenu(menuPop)
        menuPop.Destroy()
    
    def Actualiser(self, event):
        self.ctrl_inscriptions.MAJ(forcerActualisation=True) 
    
    def Aide(self, event):
        from Utils import UTILS_Aide
        UTILS_Aide.Aide("Villesetcodespostaux")

# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------

class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self, -1)
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_1.Add(panel, 1, wx.ALL|wx.EXPAND)
        self.SetSizer(sizer_1)

        self.ctrl = Panel(panel)
        self.ctrl.MAJ() 
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_2.Add(self.ctrl, 1, wx.ALL|wx.EXPAND, 4)
        panel.SetSizer(sizer_2)
        self.Layout()
        self.CentreOnScreen()

if __name__ == '__main__':
    app = wx.App(0)
    #wx.InitAllImageHandlers()
    frame_1 = MyFrame(None, -1, "TEST", size=(800, 400))
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()