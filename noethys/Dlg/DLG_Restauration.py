#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, branche Matthania
# Modules : g�re les acc�s restauration, cf UTILS_Fichiers(JB)

# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-11 Ivan LUCAS
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------


from Utils.UTILS_Traduction import _
import wx
from Ctrl import CTRL_Bouton_image
import sys
import wx.lib.agw.customtreectrl as CT
from Ctrl import CTRL_Bandeau
import GestionDB
from Utils import UTILS_Sauvegarde
from Utils import UTILS_Fichiers
from Utils import UTILS_Cryptage_fichier
sys.modules['UTILS_Cryptage_fichier'] = UTILS_Cryptage_fichier

from Dlg import DLG_Saisie_param_reseau


LISTE_CATEGORIES = UTILS_Sauvegarde.LISTE_CATEGORIES


def SelectionFichier():
    """ S�lectionner le fichier � restaurer """
    # Demande l'emplacement du fichier
    wildcard = _("Sauvegarde Noethys (*.nod; *.noc)|*.nod;*.noc")
    standardPath = wx.StandardPaths.Get()
    rep = standardPath.GetDocumentsDir()
    dlg = wx.FileDialog(None, message=_("Veuillez s�lectionner le fichier de sauvegarde � restaurer"), defaultDir=rep, defaultFile="", wildcard=wildcard, style=wx.FD_OPEN)
    if dlg.ShowModal() == wx.ID_OK:
        fichier = dlg.GetPath()
    else:
        return None
    dlg.Destroy()
    
    # Fichier NOC : D�cryptage du fichier
    if fichier.endswith(".noc") == True :
        dlg = wx.PasswordEntryDialog(None, _("Veuillez saisir le mot de passe :"), _("Ouverture d'une sauvegarde crypt�e"))
        if dlg.ShowModal() == wx.ID_OK:
            motdepasse = dlg.GetValue()
        else:
            dlg.Destroy()
            return None
        dlg.Destroy()

        # D�cryptage du fichier
        nom_fichier_decrypte = UTILS_Fichiers.GetRepTemp(fichier="savedecrypte.zip")
        UTILS_Cryptage_fichier.DecrypterFichier(fichier, nom_fichier_decrypte, motdepasse)

        # V�rifie que le ZIP est ok
        valide = UTILS_Fichiers.VerificationZip(nom_fichier_decrypte)

        if valide == False :
            dlg = wx.MessageDialog(None, _("Le mot de passe que vous avez saisi semble erron� !"), _("Erreur"), wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            return None

        return nom_fichier_decrypte

    else:
        # Fichier NOD : V�rifie que le ZIP est ok
        valide = UTILS_Fichiers.VerificationZip(fichier)
        if valide == False:
            dlg = wx.MessageDialog(None, _("Le fichier de sauvegarde semble corrompu !"), _("Erreur"), wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            return None

        return fichier

class CTRL_Donnees(CT.CustomTreeCtrl):
    def __init__(self, parent, listeFichiers=[], id=wx.ID_ANY, pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.SUNKEN_BORDER) :
        CT.CustomTreeCtrl.__init__(self, parent, id, pos, size, style)
        self.listeFichiers = listeFichiers
        
        self.root = self.AddRoot(_("Donn�es"))
        self.SetBackgroundColour(wx.WHITE)
        self.SetAGWWindowStyleFlag(wx.TR_HIDE_ROOT | wx.TR_HAS_BUTTONS | wx.TR_HAS_VARIABLE_ROW_HEIGHT | CT.TR_AUTO_CHECK_CHILD)
        self.EnableSelectionVista(True)

        # Fichiers locaux
        listeFichiersLocaux = self.GetListeFichiersLocaux()
        if len(listeFichiersLocaux) > 0 :
            brancheType = self.AppendItem(self.root, _("Fichiers locaux"), ct_type=1)
            self.SetPyData(brancheType, _("locaux"))
            self.SetItemBold(brancheType)
            self.CheckItem(brancheType, True)
            
            for nomFichier in listeFichiersLocaux :
                brancheNom = self.AppendItem(brancheType, nomFichier, ct_type=1)
                self.SetPyData(brancheNom, nomFichier)
                self.CheckItem(brancheNom, True)
                
                for nomCategorie, codeCategorie in LISTE_CATEGORIES :
                    fichier = "%s_%s.dat" % (nomFichier, codeCategorie)
                    if fichier in self.listeFichiers :
                        brancheFichier = self.AppendItem(brancheNom, nomCategorie, ct_type=1)
                        self.SetPyData(brancheFichier, fichier)
                        self.CheckItem(brancheFichier, True)

        # Fichiers r�seaux
        listeFichiersReseau = self.GetListeFichiersReseau()
        if len(listeFichiersReseau) > 0 :
            brancheType = self.AppendItem(self.root, _("Fichiers r�seau"), ct_type=1)
            self.SetPyData(brancheType, _("reseau"))
            self.SetItemBold(brancheType)
            self.CheckItem(brancheType, True)
            
            for nomFichier in listeFichiersReseau :
                brancheNom = self.AppendItem(brancheType, nomFichier, ct_type=1)
                self.SetPyData(brancheNom, nomFichier)
                self.CheckItem(brancheNom, True)
                
                for nomCategorie, codeCategorie in LISTE_CATEGORIES :
                    fichier = "%s_%s.sql" % (nomFichier, codeCategorie.lower())
                    if fichier in self.listeFichiers :
                        brancheFichier = self.AppendItem(brancheNom, nomCategorie, ct_type=1)
                        self.SetPyData(brancheFichier, fichier)
                        self.CheckItem(brancheFichier, True)

        self.ExpandAll() 

    def GetListeFichiersLocaux(self):
        """ Trouver les fichiers locaux pr�sents dans le ZIP """
        listeLocaux = []
        for fichier in self.listeFichiers :
            if fichier[-9:] == "_DATA.dat" : 
                nomFichier = fichier[:-9]
                listeLocaux.append(nomFichier)
        listeLocaux.sort()
        return listeLocaux

    def GetListeFichiersReseau(self):
        """ Trouver les fichiers MySQL pr�sents dans le ZIP """
        listeReseau = []
        for fichier in self.listeFichiers :
            if fichier[-9:] == "_data.sql" : 
                nomFichier = fichier[:-9]
                listeReseau.append(nomFichier)
        listeReseau.sort()
        return listeReseau

    def GetCoches(self):
        """ Obtient la liste des �l�ments coch�s """
        dictDonnees = {}
        
        brancheType = self.GetFirstChild(self.root)[0]
        for index1 in range(self.GetChildrenCount(self.root, recursively=False)) :
            nomType = self.GetItemPyData(brancheType)
            dictDonnees[nomType] = []
            
            # Branche nom du fichier
            brancheNom = self.GetFirstChild(brancheType)[0]
            for index2 in range(self.GetChildrenCount(brancheType, recursively=False)) :
                nomFichier = self.GetItemPyData(brancheNom)
                
                # Branche code fichier
                brancheCode = self.GetFirstChild(brancheNom)[0]
                for index3 in range(self.GetChildrenCount(brancheNom, recursively=False)) :
                    nomFichierComplet = self.GetItemPyData(brancheCode)
                    
                    if self.IsItemChecked(brancheCode) :
                        dictDonnees[nomType].append(nomFichierComplet)
                    
                    brancheCode = self.GetNextChild(brancheNom, index3+1)[0]
                brancheNom = self.GetNextChild(brancheType, index2+1)[0]
            brancheType = self.GetNextChild(self.root, index1+1)[0]
                        
        return dictDonnees

# ------------------------------------------------------------------------------------------------------------------------------------------------

class Dialog(wx.Dialog):
    def __init__(self, parent, fichier=""):
        wx.Dialog.__init__(self, parent, -1, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX)
        self.parent = parent
        self.fichier = fichier
        self.listeFichiersRestaures = []
        
        # R�cup�ration du contenu du ZIP
        zipFile = UTILS_Fichiers.GetZipFile(fichier,'r')
        self.listeFichiers = UTILS_Fichiers.GetListeFichiersZip(zipFile)
        
        intro = _("Vous pouvez ici restaurer une sauvegarde. Vous devez s�lectionner dans la liste des donn�es pr�sentes dans la sauvegarde celles que vous souhaitez restaurer.")
        titre = _("Restauration")
        self.SetTitle(titre)
        self.ctrl_bandeau = CTRL_Bandeau.Bandeau(self, titre=titre, texte=intro, hauteurHtml=30, nomImage="Images/32x32/Restaurer.png")
                
        # Donn�es
        self.box_donnees_staticbox = wx.StaticBox(self, -1, _("Donn�es � restaurer"))
        self.ctrl_donnees = CTRL_Donnees(self, listeFichiers=self.listeFichiers)
        self.ctrl_donnees.SetMinSize((250, -1))
        
        # Boutons
        self.bouton_aide = CTRL_Bouton_image.CTRL(self, texte=_("Aide"), cheminImage="Images/32x32/Aide.png")
        self.bouton_ok = CTRL_Bouton_image.CTRL(self, texte=_("Ok"), cheminImage="Images/32x32/Valider.png")
        self.bouton_annuler = CTRL_Bouton_image.CTRL(self, texte=_("Annuler"), cheminImage="Images/32x32/Annuler.png")

        self.__set_properties()
        self.__do_layout()
        
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAide, self.bouton_aide)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonOk, self.bouton_ok)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAnnuler, self.bouton_annuler)

    def __set_properties(self):
        self.bouton_aide.SetToolTip(wx.ToolTip(_("Cliquez ici pour obtenir de l'aide")))
        self.bouton_ok.SetToolTip(wx.ToolTip(_("Cliquez ici pour lancer la restauration")))
        self.bouton_annuler.SetToolTip(wx.ToolTip(_("Cliquez ici pour annuler")))
        self.SetMinSize((420, 460))

    def __do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(rows=3, cols=1, vgap=10, hgap=10)
        grid_sizer_base.Add(self.ctrl_bandeau, 0, wx.EXPAND, 0)
        
        box_donnees = wx.StaticBoxSizer(self.box_donnees_staticbox, wx.VERTICAL)
        box_donnees.Add(self.ctrl_donnees, 1, wx.ALL|wx.EXPAND, 10)
        grid_sizer_base.Add(box_donnees, 1, wx.LEFT|wx.RIGHT|wx.EXPAND, 10)
        
        grid_sizer_boutons = wx.FlexGridSizer(rows=1, cols=4, vgap=10, hgap=10)
        grid_sizer_boutons.Add(self.bouton_aide, 0, 0, 0)
        grid_sizer_boutons.Add((20, 20), 0, wx.EXPAND, 0)
        grid_sizer_boutons.Add(self.bouton_ok, 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_annuler, 0, 0, 0)
        grid_sizer_boutons.AddGrowableCol(1)
        grid_sizer_base.Add(grid_sizer_boutons, 1, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 10)
        
        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)
        grid_sizer_base.AddGrowableRow(1)
        grid_sizer_base.AddGrowableCol(0)
        self.Layout()
        self.CenterOnScreen() 
    
    def OnBoutonAide(self, event): 
        from Utils import UTILS_Aide
        UTILS_Aide.Aide("Restaurerunesauvegarde")

    def OnBoutonAnnuler(self, event):
        self.EndModal(wx.ID_CANCEL)

    def OnBoutonOk(self, event):         
        # Donn�es � sauver
        dictDonnees = self.ctrl_donnees.GetCoches() 
        if "locaux" in dictDonnees :
            listeFichiersLocaux = dictDonnees["locaux"]
        else:
            listeFichiersLocaux = []
        if "reseau" in dictDonnees :
            listeFichiersReseau = dictDonnees["reseau"]
        else:
            listeFichiersReseau = []
        
        if len(listeFichiersLocaux) == 0 and len(listeFichiersReseau) == 0 :
            dlg = wx.MessageDialog(self, _("Vous devez s�lectionner au moins un fichier � restaurer !"), _("Erreur"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        
        # R�cup�ration des param�tres de connexion r�seau
        dictConnexion = None
        
        if len(listeFichiersReseau) > 0 :
            # R�cup�re les param�tres charg�s
            DB = GestionDB.DB() 
            if DB.echec != 1 :
                if DB.isNetwork == True :
                    dictConnexion = DB.GetParamConnexionReseau() 
            DB.Close() 
            
            # Demande les param�tres de connexion r�seau
            if dictConnexion == None :
                
                # Demande les param�tres de connexion
                intro = _("Les fichiers que vos souhaitez restaurer n�cessite une connexion r�seau.\nVeuillez saisir vos param�tres de connexion MySQL:")
                dlg = DLG_Saisie_param_reseau.Dialog(self, intro=intro)
                if dlg.ShowModal() == wx.ID_OK:
                    dictConnexion = dlg.GetDictValeurs()
                    dlg.Destroy()
                else:
                    dlg.Destroy()
                    return
                
                # V�rifie si la connexion est bonne
                resultat = DLG_Saisie_param_reseau.TestConnexion(dictConnexion)
                if resultat == False :
                    dlg = wx.MessageDialog(self, _("Echec du test de connexion.\n\nLes param�tres ne semblent pas exacts !"), _("Erreur"), wx.OK | wx.ICON_ERROR)
                    dlg.ShowModal()
                    dlg.Destroy()
                    return
         
        # Sauvegarde
        resultat = UTILS_Sauvegarde.Restauration(self.parent, self.fichier, listeFichiersLocaux, listeFichiersReseau, dictConnexion)
        if resultat == False :
            return
        self.listeFichiersRestaures = resultat
        
        # Fin du processus
        dlg = wx.MessageDialog(self, _("Le processus de restauration est termin�."), _("Restauration"), wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()

        # Fermeture
        self.EndModal(wx.ID_OK)
    
    def GetFichiersRestaures(self):
        """ R�cup�re la liste des fichiers restaur�s """
        listeTemp = []
        for fichier in self.listeFichiersRestaures :
            if fichier[-5:] in ("_DATA", "_data") : 
                nomFichier = fichier[:-5]
                listeTemp.append(nomFichier)
        return listeTemp
        
        


if __name__ == "__main__":
    app = wx.App(0)
    #wx.InitAllImageHandlers()
    fichier = SelectionFichier()
    if fichier != None :
        dialog_1 = Dialog(None, fichier=fichier)
        app.SetTopWindow(dialog_1)
        dialog_1.ShowModal()
    app.MainLoop()
