#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, Matthania
# Auteur:          Ivan LUCAS, JB, Jacques Brunel
# Licence:         Licence GNU GPL
# Gestion de la validation de la pièce liée à l'inscription
# Adapté à partir de DLG_SaisieArticles
#------------------------------------------------------------------------

from Utils.UTILS_Traduction import _
import wx
import Chemins
from Ctrl import CTRL_Bouton_image
from Gest import GestionArticle
from Ctrl.CTRL_ObjectListView import FastObjectListView, ColumnDefn
import copy
from Ctrl import CTRL_Bandeau


def ValideSaisie(tracks,testSejour=True):
    #contrôle le sens des lignes de facturation quand forcé
    ret = True
    for track in tracks:
        if track.montantCalcul * track.montant < 0.0:
            dlg = wx.MessageDialog(None, _("Un montant forcé n'a pas le signe habituel! \n\nConfirmez-vous le sens du montant de l'article %s" % track.codeArticle), "Avertissement", wx.YES_NO |wx.NO_DEFAULT|wx.CANCEL| wx.ICON_INFORMATION)
            rep = dlg.ShowModal()
            if rep != wx.ID_YES :
                ret = False
            dlg.Destroy()
            if not ret:
                break
    if not ret : return ret
    if testSejour :
        # Vérif de la présence d'un article séjour.
        ret = False
        for track in tracks:
            if track.typeLigne == "Sejour":
                ret = True
        if not ret :
            dlg = wx.MessageDialog(None, _("Pas de séjour dans cette pièce !\n\nElle ne pourra faire l'objet de réduction séjour.\nConfirmez-vous ?"), "Avertissement", wx.YES_NO |wx.NO_DEFAULT|wx.CANCEL| wx.ICON_INFORMATION)
            rep = dlg.ShowModal()
            if rep == wx.ID_YES : ret = True
            dlg.Destroy()
    return ret

def DoubleLigne(tracks,IDinscription, db, IDnumPiece=None, IDfamille=None):
    # censure la présence de doublon dans les libellés de lignes
    valide = True
    #Cas de création de pièce inutile de rechercher des doublons
    if not IDinscription:
        return valide
    lstLibelles = [x.libelle for x in tracks]
    # test sur les lignes présentes dans la piece encours
    for x in tracks:
        if lstLibelles.count(x.libelle) >1:
            mess = "Ligne '%s' en double\n\n" % x.libelle
            mess += "%d lignes ont un même libellé\n" % (lstLibelles.count(x.libelle))
            mess += "Précisez les libellés si vous souhaites conserver les lignes..."
            wx.MessageBox(mess, "Modifiez une ligne", wx.ICON_INFORMATION)
            valide = False
            return valide
    # test sur les pièces existantes
    recordset = []
    if len(lstLibelles) > 0:
        conditionPiece = ""
        if IDnumPiece:
            conditionPiece = "AND (matPieces.pieIDnumPiece <> %d)" % IDnumPiece
        req = """
        SELECT matPieces.pieIDactivite, activites.nom, matPiecesLignes.ligCodeArticle, 
                matPiecesLignes.ligLibelle, Sum(matPiecesLignes.ligMontant), 
                Count(matPiecesLignes.ligIDnumLigne)
        FROM (matPieces 
        INNER JOIN matPiecesLignes 
            ON matPieces.pieIDnumPiece = matPiecesLignes.ligIDnumPiece) 
        LEFT JOIN activites 
            ON matPieces.pieIDactivite = activites.IDactivite
        WHERE ((( matPieces.pieIDinscription = %d ) 
                AND ( matPieces.pieIDfamille = %d ))
                AND (matPiecesLignes.ligLibelle in ( %s) )
                %s)
        GROUP BY matPieces.pieIDactivite, activites.nom, matPiecesLignes.ligCodeArticle, 
                matPiecesLignes.ligLibelle
        HAVING Sum(matPiecesLignes.ligMontant) <> 0 
        ;""" % ( IDinscription, IDfamille, str(lstLibelles)[1:-1], conditionPiece)
        db.ExecuterReq(req,MsgBox = "DLG_ChoixTypePiece.WarnDblLigne")
        recordset = db.ResultatReq()
    if len(recordset) > 0:
        # test la présence antérieure de même ligne
        for IDactivite, nomActivite, codeArticle, libelle, mtt, nbre in recordset:
            for track in tracks:
                if (track.libelle != libelle) or track.codeArticle != codeArticle:
                    continue
                montant = mtt + track.montant
                if round(montant,2) == 0.0:
                    continue
                if not nomActivite:
                    nomActivite = str(IDactivite) # peut être l'année pour famille
                mess = "Ligne '%s' en double\n\n"% libelle
                mess += "L'activité '%s' a %d lignes avec un même libellé\n"% (nomActivite,nbre)
                mess += "article '%s' pour un prix total de %8.2f€ est déjà présent!\n"% (codeArticle,montant)
                mess += "Précisez les libellés si vous souhaites conserver les lignes..."
                wx.MessageBox(mess, "Modifiez une ligne", wx.ICON_INFORMATION)
                valide = False
    return valide

# -----------------------------------------------------------------------------------------------------------------
class Dialog(wx.Dialog):
    def __init__(self, parent, mode):
        wx.Dialog.__init__(self, parent, -1, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX)
        self.parent = parent
        self.titre = ("Gestion de l'état de la pièce")
        intro = ("L'état de la pièce conditionne l'étape dans le processus de l'inscription")
        self.SetTitle("DLG_ChoixTypePiece")
        self.ctrl_bandeau = CTRL_Bandeau.Bandeau(self, titre=self.titre, texte=intro,  hauteurHtml=15, nomImage="Images/22x22/Smiley_nul.png")
        self.liste_naturePiece = copy.deepcopy(GestionArticle.LISTEnaturesPieces)
        self.staticbox_CARACTER = wx.StaticBox(self, -1, _("Choix de l'état de la pièce"))
        self.staticbox_BOUTONS= wx.StaticBox(self, -1, )

        #Elements gérés
        self.liste_codesNaturesPiece = [str((a)) for a,b,c in self.liste_naturePiece]
        self.liste_commentNaturesPiece = [c for a,b,c in self.liste_naturePiece]
        self.resultsOlv = FastObjectListView(self)
        self.txt_naturesPiece = wx.TextCtrl(self, -1, "", style=wx.TE_MULTILINE)

        self.ctrl_nature = wx.TextCtrl(self, -1, "",size=(100, 20))
        self.ctrl_nature.Label = "Choisir"
        self.codeNature = " "
        self.bouton_ok = CTRL_Bouton_image.CTRL(self, texte=_("Valider"), cheminImage=Chemins.GetStaticPath("Images/32x32/Valider.png"))
        self.bouton_annuler = CTRL_Bouton_image.CTRL(self, id=wx.ID_CANCEL, texte=_("Annuler"), cheminImage=Chemins.GetStaticPath("Images/32x32/Annuler.png"))

        self.__set_properties()
        self.__do_layout()

    def __set_properties(self):
        self.resultsOlv.SetToolTip(_("Cliquez pour choisir"))
        self.resultsOlv.useExpansionColumn = True
        self.resultsOlv.SetColumns([
            ColumnDefn("Code", "left", 0, 0),
            ColumnDefn("Code", "left", 50, 0),
            ColumnDefn("Libelle", "left", 100, 1,isSpaceFilling = True),
            ])
        self.resultsOlv.SetObjects(self.liste_naturePiece)

        self.ctrl_nature.SetToolTip(_("Faites le choix dans la liste ci-dessus"))
        self.bouton_ok.SetToolTip(_("Cliquez ici pour valider et fermer"))
        self.bouton_annuler.SetToolTip(_("Cliquez ici pour annuler et fermer"))
        self.SetMinSize((300, 350))
        self.Bind(wx.EVT_BUTTON, self.OnBoutonOk, self.bouton_ok)
        self.resultsOlv.Bind(wx.EVT_COMMAND_LEFT_CLICK, self.OnResultsOLV)
        self.resultsOlv.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnResultsOLV)

    def __do_layout(self):
        gridsizer_BASE = wx.FlexGridSizer(rows=3, cols=1, vgap=0, hgap=0)
        gridsizer_BASE.Add(self.ctrl_bandeau, 1, wx.EXPAND, 0)

        staticsizer_CARACTER = wx.StaticBoxSizer(self.staticbox_CARACTER, wx.VERTICAL)
        gridsizer_CARACTER = wx.FlexGridSizer(rows=1, cols=2, vgap=5, hgap=5)
        gridsizer_CARACTER.Add(self.resultsOlv, 1, wx.LEFT, 10)
        gridsizer_CARACTER.Add(self.txt_naturesPiece, 1, wx.LEFT|wx.EXPAND, 0)
        staticsizer_CARACTER.Add(gridsizer_CARACTER, 1, wx.RIGHT|wx.EXPAND,10)
        gridsizer_CARACTER.AddGrowableCol(1)
        gridsizer_BASE.Add(staticsizer_CARACTER, 1,wx.TOP|wx.EXPAND, 10)

        gridsizer_BOUTONS = wx.FlexGridSizer(rows=1, cols=5, vgap=10, hgap=10)
        staticsizer_BOUTONS = wx.StaticBoxSizer(self.staticbox_BOUTONS, wx.VERTICAL)
        gridsizer_BOUTONS.Add(self.ctrl_nature, 0, 0, 0)
        gridsizer_BOUTONS.Add((15, 15), 0, 0, 0)
        gridsizer_BOUTONS.Add(self.bouton_ok, 0, 0, 0)
        gridsizer_BOUTONS.Add(self.bouton_annuler, 0, 0, 0)
        gridsizer_BOUTONS.AddGrowableCol(1)
        staticsizer_BOUTONS.Add(gridsizer_BOUTONS, 1, wx.RIGHT|wx.EXPAND, 10)
        gridsizer_BASE.Add(staticsizer_BOUTONS, 1, wx.BOTTOM|wx.LEFT|wx.RIGHT|wx.EXPAND, 10)

        self.SetSizer(gridsizer_BASE)
        gridsizer_BASE.Fit(self)
        gridsizer_BASE.AddGrowableRow(1)
        gridsizer_BASE.AddGrowableCol(0)
        self.Layout()
        self.CentreOnScreen()

    def OnResultsOLV(self, event):
        if self.resultsOlv.GetSelectedObject() and len(self.resultsOlv.GetSelectedObject())>1:
            self.ctrl_nature.SetValue( str(self.resultsOlv.GetSelectedObject()[1]))
            self.txt_naturesPiece.SetValue( self.resultsOlv.GetSelectedObject()[2])
            self.codeNature = self.resultsOlv.GetSelectedObject()[0]
        event.Skip()
        return

    def OnBoutonOk(self, event):
        # Vérification des données saisies
        textCode = self.ctrl_nature.GetValue()
        if textCode == "Choisir" :
            dlg = wx.MessageDialog(self, _("Vous devez obligatoirement choisir l'état de cette pièce !"), _("Erreur"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        # Fermeture de la fenêtre
        self.EndModal(wx.ID_OK)

if __name__ == "__main__":
    app = wx.App(0)
    #wx.InitAllImageHandlers()
    dialog_1 = Dialog(None,"ajout")
    app.SetTopWindow(dialog_1)
    dialog_1.ShowModal()
    app.MainLoop()