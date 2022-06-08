#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys branche Matthania
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS, JB
# Copyright:       (c) 2010-11 Ivan LUCAS, JB
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------


import Chemins
from Utils.UTILS_Traduction import _
import wx
from Ctrl import CTRL_Bouton_image
import os
import datetime
import re
import sys
import decimal
from Dlg import DLG_Selection_liste
import FonctionsPerso
from Ctrl import CTRL_Bandeau
from Utils import UTILS_Fichiers
from Utils import UTILS_Dates
from Utils import UTILS_Config

SYMBOLE = UTILS_Config.GetParametre("monnaie_symbole", "�")

from Ctrl.CTRL_ObjectListView import FastObjectListView, ColumnDefn, Filter, CTRL_Outils


def GetValeursListview(listview=None, format="texte", onlyCheck = False):
    """ R�cup�re les valeurs affich�es sous forme de liste """
    """ format = "texte" ou "original" """
    # R�cup�re les labels de colonnes
    listeColonnes = []
    for colonne in listview.columns :
        listeColonnes.append((colonne.title, colonne.align, colonne.width, colonne.valueGetter))
    
    # R�cup�re les valeurs
    listeValeurs = []
    if onlyCheck:
        listeObjects = listview.GetCheckedObjects() # listview.GetFilteredObjects()
    else:
        listeObjects = listview.innerList # listview.GetFilteredObjects()

    for object in listeObjects :
        valeursLigne = []
        for indexCol in range(0, listview.GetColumnCount() ) :
            if format == "texte" :
                valeur = listview.GetStringValueAt(object, indexCol)
            else :
                valeur = listview.GetValueAt(object, indexCol)
            valeursLigne.append(valeur)
        listeValeurs.append(valeursLigne)
    return listeColonnes, listeValeurs


def GetValeursGrid(grid=None):
    """ R�cup�re les valeurs affich�es sous forme de liste """
    # R�cup�re les labels de colonnes
    listeColonnes = [("titre_ligne", None, grid.GetColLabelSize(), "titre_ligne"),]
    for numCol in range(0, grid.GetNumberCols()):
        listeColonnes.append((grid.GetColLabelValue(numCol), None, grid.GetColSize(numCol), grid.GetColLabelValue(numCol)))
                
    # R�cup�re les valeurs
    listeValeurs = []
    for numLigne in range(0, grid.GetNumberRows()) :
        labelLigne = grid.GetRowLabelValue(numLigne)
        valeursLigne = [labelLigne,]
        for numCol in range(0, grid.GetNumberCols()) :
            valeur = grid.GetCellValue(numLigne, numCol)
            if type(valeur) not in ("str", "unicode") :
                valeur = str(valeur)
            valeursLigne.append(valeur)
        listeValeurs.append(valeursLigne)
        
    return listeColonnes, listeValeurs


def ExportTexte(listview=None, grid=None, titre="", listeColonnes=None, listeValeurs=None, autoriseSelections=True):
    """ Export de la liste au format texte """
    if (listview != None and len(listview.donnees) == 0) or (grid != None and (grid.GetNumberRows() == 0 or grid.GetNumberCols() == 0)):
        dlg = wx.MessageDialog(None, _("Il n'y a aucune donn�e dans la liste !"), "Erreur", wx.OK | wx.ICON_ERROR)
        dlg.ShowModal()
        dlg.Destroy()
        return

    # R�cup�ration des valeurs
    if listview != None and listeColonnes == None and listeValeurs == None :
        listeColonnes, listeValeurs = GetValeursListview(listview, format="texte")
        
    if grid != None and listeColonnes == None and listeValeurs == None :
        autoriseSelections = False
        listeColonnes, listeValeurs = GetValeursGrid(grid)

    # Selection des lignes
    if autoriseSelections == True :
        dlg = DLG_Selection_liste.Dialog(None, listeColonnes, listeValeurs, type="exportTexte")
        if dlg.ShowModal() == wx.ID_OK:
            listeSelections = dlg.GetSelections()
            dlg.Destroy()
        else:
            dlg.Destroy()
            return False
    
    # Demande � l'utilisateur le nom de fichier et le r�pertoire de destination
    nomFichier = "ExportTexte_%s.txt" % datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    wildcard = "Fichier texte (*.txt)|*.txt|" \
                    "All files (*.*)|*.*"
    sp = wx.StandardPaths.Get()
    cheminDefaut = sp.GetDocumentsDir()
    dlg = wx.FileDialog(
        None, message = _("Veuillez s�lectionner le r�pertoire de destination et le nom du fichier"), defaultDir=cheminDefaut,
        defaultFile = nomFichier, 
        wildcard = wildcard, 
        style = wx.FD_SAVE
        )
    dlg.SetFilterIndex(0)
    if dlg.ShowModal() == wx.ID_OK:
        cheminFichier = dlg.GetPath()
        dlg.Destroy()
    else:
        dlg.Destroy()
        return
    
    # Le fichier de destination existe d�j� :
    if os.path.isfile(cheminFichier) == True :
        dlg = wx.MessageDialog(None, _("Un fichier portant ce nom existe d�j�. \n\nVoulez-vous le remplacer ?"), "Attention !", wx.YES_NO | wx.NO_DEFAULT | wx.ICON_EXCLAMATION)
        if dlg.ShowModal() == wx.ID_NO :
            dlg.Destroy()
            return False
        else:
            dlg.Destroy()

    # Cr�ation du fichier texte
    texte = ""
    separateur = ";"
    for labelCol, alignement, largeur, code in listeColonnes :
        try :
            if "CheckState" in str(code) :
                code = "Coche"
        except :
            pass
        texte += code + separateur
    texte = texte[:-1] + "\n"

    for valeurs in listeValeurs :
        if valeurs[0] in (None,'') : valeurs[0] = 0
        if autoriseSelections == False or int(valeurs[0]) in listeSelections :
            for valeur in valeurs :
                if valeur == None :
                    valeur = ""
                texte += "%s%s" % (valeur, separateur)
            texte = texte[:-1] + "\n"
    
    # Elimination du dernier saut � la ligne
    texte = texte[:-1]

    # Cr�ation du fichier texte
    f = open(cheminFichier, "w")
    f.write(texte.encode("utf-8"))
    f.close()
    
    # Confirmation de cr�ation du fichier et demande d'ouverture directe dans Excel
    txtMessage = _("Le fichier Texte a �t� cr�� avec succ�s. Souhaitez-vous l'ouvrir d�s maintenant ?")
    dlgConfirm = wx.MessageDialog(None, txtMessage, _("Confirmation"), wx.YES_NO|wx.NO_DEFAULT|wx.ICON_QUESTION)
    reponse = dlgConfirm.ShowModal()
    dlgConfirm.Destroy()
    if reponse == wx.ID_NO:
        return
    else:
        FonctionsPerso.LanceFichierExterne(cheminFichier)
        

# -------------------------------------------------------------------------------------------------------------------------------


def ExportExcel(listview=None, grid=None, titre=_("Liste"), listeColonnes=None, listeValeurs=None, autoriseSelections=True, onlyCheck = False):
    """ Export de la liste au format Excel """
    # Plus de s�lection pour �viter les bugs !!!!
    autoriseSelections = False 
    if listview:
        nbLignes = len(listview.donnees)
    else: nbLignes = 0

    if onlyCheck :
        if len(listview.GetCheckedObjects()) == 0:
            onlyCheck = False

    # V�rifie si donn�es bien pr�sentes
    if (listview != None and nbLignes == 0) or (grid != None and (grid.GetNumberRows() == 0 or grid.GetNumberCols() == 0)):
        dlg = wx.MessageDialog(None, _("Il n'y a aucune donn�e dans la liste !"), "Erreur", wx.OK | wx.ICON_ERROR)
        dlg.ShowModal()
        dlg.Destroy()
        return
        
    # R�cup�ration des valeurs
    if listview != None and listeColonnes == None and listeValeurs == None :
        listeColonnes, listeValeurs = GetValeursListview(listview, format="original", onlyCheck= onlyCheck)
        
    if grid != None and listeColonnes == None and listeValeurs == None :
        autoriseSelections = False
        listeColonnes, listeValeurs = GetValeursGrid(grid)
    
    # Selection des lignes
    if autoriseSelections == True :
        dlg = DLG_Selection_liste.Dialog(None, listeColonnes, listeValeurs, type="exportExcel")
        if dlg.ShowModal() == wx.ID_OK:
            listeSelections = dlg.GetSelections()
            dlg.Destroy()
        else:
            dlg.Destroy()
            return False

    # Choix Action
    dlg = DLG_Choix_action(None)
    reponse = dlg.ShowModal()
    dlg.Destroy()
    if reponse == 100 :
        mode = "enregistrer"
    elif reponse == 200 :
        mode = "email"
    else :
        return

    # D�finit le nom et le chemin du fichier
    nomFichier = "ExportExcel_%s.xlsx" % datetime.datetime.now().strftime("%Y%m%d%H%M%S")

    # Mode Enregistrer
    if mode == "enregistrer" :

        # Demande � l'utilisateur le nom de fichier et le r�pertoire de destination
        wildcard = "Fichier Excel (*.xlsx)|*.xlsx|" \
                        "All files (*.*)|*.*"
        sp = wx.StandardPaths.Get()
        cheminDefaut = sp.GetDocumentsDir()
        dlg = wx.FileDialog(
            None, message = _("Veuillez s�lectionner le r�pertoire de destination et le nom du fichier"), defaultDir=cheminDefaut,
            defaultFile = nomFichier,
            wildcard = wildcard,
            style = wx.FD_SAVE
            )
        dlg.SetFilterIndex(0)
        if dlg.ShowModal() == wx.ID_OK:
            cheminFichier = dlg.GetPath()
            dlg.Destroy()
        else:
            dlg.Destroy()
            return

        # Le fichier de destination existe d�j� :
        if os.path.isfile(cheminFichier) == True :
            dlg = wx.MessageDialog(None, _("Un fichier portant ce nom existe d�j�. \n\nVoulez-vous le remplacer ?"), "Attention !", wx.YES_NO | wx.NO_DEFAULT | wx.ICON_EXCLAMATION)
            if dlg.ShowModal() == wx.ID_NO :
                return False
                dlg.Destroy()
            else:
                dlg.Destroy()

    # Mode Envoyer par Email
    if mode == "email" :
        cheminFichier = UTILS_Fichiers.GetRepTemp(fichier=nomFichier)


    # Export
    import xlsxwriter
    classeur = xlsxwriter.Workbook(cheminFichier)
    feuille = classeur.add_worksheet()

    format_money = classeur.add_format({'num_format': '# ##0.00'})
    format_titre = classeur.add_format({'align': 'center', 'bold': True, 'bg_color': '#E7EAED'})
    format_date = classeur.add_format({'num_format': 'dd/mm/yyyy'})
    format_heure = classeur.add_format({'num_format': '[hh]:mm'})

    # Cr�ation des labels de colonnes
    x = 0
    y = 0
    for labelCol, alignement, largeur, nomChamp in listeColonnes :
        try :
            if "CheckState" in str(nomChamp) :
                nomChamp = "Coche"
        except :
            pass
        feuille.write(x, y, labelCol)
        feuille.set_column(y, y, largeur // 4)
        y += 1

    # -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------

    # Cr�ation des lignes
    def RechercheFormatFromChaine(valeur):
        """ Recherche le type de la cha�ne """
        # Si c'est un nombre traitement � minima
        if isinstance(valeur,(int,float,bool)):
            if isinstance(valeur,float):
                return (round(valeur,2),None)
            return (valeur,None)
        if isinstance(valeur,datetime.date):
            valeur = str(valeur)
        if valeur == None:
            valeur = ""
        # pour les cha�nes
        try :
            if valeur.startswith("- ") :
                valeur = valeur.replace("- ", "-")
            nbre = float(valeur)
            return (nbre, None)
        except :
            pass
        
        # Si c'est une date
        try :
            if len(valeur) == 10 :
                if valeur[2] == "/" and valeur[5] == "/" :
                    return (valeur, format_date)
        except :
            pass

        if type(valeur) == datetime.timedelta :
            return (valeur, format_heure)

        # Si c'est une heure
        try :
            if len(valeur) > 3 :
                if ":" in valeur :
                    separateur = ":"
                elif "h" in valeur :
                    separateur = "h"
                else :
                    separateur = None
                if separateur != None :
                    heures, minutes = valeur.split(separateur)
                    valeur = datetime.timedelta(minutes= int(heures)*60 + int(minutes))
                    return (valeur, format_heure)
        except :
            pass

        return str(valeur), None

    # -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------

    def RechercheFormat(valeur):
        """ Recherche le type de la donn�e """
        if type(valeur) == decimal.Decimal :
            valeur = float(valeur)
            return (valeur, format_money)
                
        if type(valeur) == float :
            return (valeur, None)
                
        if type(valeur) == int :
            return (valeur, None)
        
        if type(valeur) == datetime.date :
            valeur = UTILS_Dates.DateDDEnFr(valeur)
            return (valeur, format_date)

        if type(valeur) == datetime.timedelta :
            return (valeur, format_heure)

        try :
            if len(valeur) > 3 :
                if ":" in valeur :
                    separateur = ":"
                elif "h" in valeur :
                    separateur = "h"
                else :
                    separateur = None
                if separateur != None :
                    donnees = valeur.split(separateur)
                    if len(donnees) == 2 :
                        heures, minutes = donnees
                    if len(donnees) == 3 :
                        heures, minutes, secondes = donnees
                    valeur = datetime.timedelta(minutes= int(heures)*60 + int(minutes))
                    return (valeur, format_heure)
        except :
            pass

        if type(valeur) in (str,) :
            if len(valeur) == 10 :
                if valeur[2] == "/" and valeur[5] == "/" : return (valeur, format_date)
                if valeur[4] == "-" and valeur[7] == "-" : return (UTILS_Dates.DateEngFr(valeur), format_date)
                
        return str(valeur), None

    # -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------

    x = 1
    y = 0
    for valeurs in listeValeurs :
        if autoriseSelections == False or int(valeurs[0]) in listeSelections :
            for valeur in valeurs :
                if valeur == None :
                    valeur = ""
                    
                # Recherche s'il y a un format de nombre ou de montant
                if listview != None :
                    valeur, format = RechercheFormat(valeur)
                else :
                    valeur, format = RechercheFormatFromChaine(valeur)
                        
                # Enregistre la valeur
                if format != None :
                    feuille.write(x, y, valeur, format)
                else:
                    feuille.write(x, y, valeur)

                y += 1
            x += 1
            y = 0
            
    # Finalisation du fichier xls
    try :
        classeur.close()
    except :
        dlg = wx.MessageDialog(None, _("Il est impossible d'enregistrer le fichier Excel. Veuillez v�rifier que ce fichier n'est pas d�j� ouvert en arri�re-plan."), "Erreur", wx.OK | wx.ICON_ERROR)
        dlg.ShowModal()
        dlg.Destroy()
        return

    # Confirmation de cr�ation du fichier et demande d'ouverture directe dans Excel
    if mode == "enregistrer" :
        txtMessage = _("Le fichier Excel a �t� cr�� avec succ�s. Souhaitez-vous l'ouvrir d�s maintenant ?")
        dlgConfirm = wx.MessageDialog(None, txtMessage, _("Confirmation"), wx.YES_NO|wx.NO_DEFAULT|wx.ICON_QUESTION)
        reponse = dlgConfirm.ShowModal()
        dlgConfirm.Destroy()
        if reponse == wx.ID_NO:
            return
        else:
            FonctionsPerso.LanceFichierExterne(cheminFichier)

    # Envoyer par Email
    if mode == "email" :
        from Dlg import DLG_Mailer
        dlg = DLG_Mailer.Dialog(None)
        dlg.ChargerModeleDefaut()
        dlg.SetPiecesJointes([cheminFichier,])
        dlg.ShowModal()
        dlg.Destroy()


# -------------------------------------------------------------------------------------------------------------------------------------------------------------

class DLG_Choix_action(wx.Dialog):
    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, -1, name="DLG_Choix_action", style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER | wx.MAXIMIZE_BOX | wx.MINIMIZE_BOX)
        self.parent = parent

        # Bandeau
        intro = _("S�lectionnez l'action � effectuer. Vous pouvez enregistrer le fichier g�n�r� dans le r�pertoire souhait� ou l'envoyer par email.")
        titre = _("Exporter vers Excel")
        self.ctrl_bandeau = CTRL_Bandeau.Bandeau(self, titre=titre, texte=intro, hauteurHtml=30, nomImage="Images/32x32/Excel.png")

        self.bouton_enregistrer = CTRL_Bouton_image.CTRL(self, texte=_("Enregistrer sous"), cheminImage="Images/48x48/Sauvegarder.png", tailleImage=(48, 48), margesImage=(40, 20, 40, 0), positionImage=wx.TOP, margesTexte=(10, 10))
        self.bouton_enregistrer.SetToolTip(wx.ToolTip(_("Enregistrer le fichier Excel")))

        self.bouton_email = CTRL_Bouton_image.CTRL(self, texte=_("Envoyer par Email"), cheminImage="Images/48x48/Email.png", tailleImage=(48, 48), margesImage=(40, 20, 40, 0), positionImage=wx.TOP, margesTexte=(10, 10))
        self.bouton_email.SetToolTip(wx.ToolTip(_("Envoyer le fichier Excel par Email")))

        self.bouton_aide = CTRL_Bouton_image.CTRL(self, texte=_("Aide"), cheminImage="Images/32x32/Aide.png")
        self.bouton_annuler = CTRL_Bouton_image.CTRL(self, id=wx.ID_CANCEL, texte=_("Annuler"), cheminImage="Images/32x32/Annuler.png")

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_BUTTON, self.OnBoutonEnregistrer, self.bouton_enregistrer)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonEmail, self.bouton_email)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAide, self.bouton_aide)

    def __set_properties(self):
        self.SetTitle(_("Exporter vers Excel"))
        self.bouton_aide.SetToolTip(wx.ToolTip(_("Obtenir de l'aide")))
        self.bouton_annuler.SetToolTip(wx.ToolTip(_("Annuler")))
        self.SetMinSize((370, 300))

    def __do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(rows=3, cols=1, vgap=10, hgap=10)
        grid_sizer_boutons = wx.FlexGridSizer(rows=1, cols=3, vgap=10, hgap=10)
        grid_sizer_contenu = wx.FlexGridSizer(rows=1, cols=2, vgap=10, hgap=10)
        grid_sizer_base.Add(self.ctrl_bandeau, 0, wx.EXPAND, 0)
        grid_sizer_contenu.Add(self.bouton_enregistrer, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALIGN_CENTER_VERTICAL, 10)
        grid_sizer_contenu.Add(self.bouton_email, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALIGN_CENTER_VERTICAL, 10)
        grid_sizer_contenu.AddGrowableRow(0)
        grid_sizer_contenu.AddGrowableCol(0)
        grid_sizer_contenu.AddGrowableCol(1)
        grid_sizer_base.Add(grid_sizer_contenu, 1, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)
        grid_sizer_boutons.Add(self.bouton_aide, 0, 0, 0)
        grid_sizer_boutons.Add((20, 20), 0, wx.EXPAND, 0)
        grid_sizer_boutons.Add(self.bouton_annuler, 0, 0, 0)
        grid_sizer_boutons.AddGrowableCol(1)
        grid_sizer_base.Add(grid_sizer_boutons, 1, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 10)
        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)
        grid_sizer_base.AddGrowableRow(1)
        grid_sizer_base.AddGrowableCol(0)
        self.Layout()
        self.CenterOnScreen()

    def OnBoutonEnregistrer(self, event):
        self.EndModal(100)

    def OnBoutonEmail(self, event):
        self.EndModal(200)

    def OnBoutonAide(self, event):
        from Utils import UTILS_Aide
        UTILS_Aide.Aide("")




# ------------------------- POUR LES TESTS ---------------------------------------------

class Track(object):
    def __init__(self, donnees):
        self.ID = donnees["ID"]
        self.texte = donnees["texte"]
        self.entier = donnees["entier"]
        self.date = donnees["date"]
        self.montant = donnees["montant"]
        self.heure = donnees["heure"]


class ListView(FastObjectListView):
    def __init__(self, *args, **kwds):
        FastObjectListView.__init__(self, *args, **kwds)

    def InitObjectListView(self):

        def FormateDate(dateDD):
            return UTILS_Dates.DateComplete(dateDD)

        def FormateMontant(montant):
            if montant == None or montant == "" : return ""
            return "%.2f %s" % (montant, SYMBOLE)

        self.SetColumns([
            ColumnDefn(u"ID", "left", 50, "ID", typeDonnee="entier"),
            ColumnDefn(u"Texte", "left", 100, "texte", typeDonnee="texte"),
            ColumnDefn(u"Entier", "left", 100, "entier", typeDonnee="entier"),
            ColumnDefn(u"Date", "left", 100, "date", stringConverter=FormateDate, typeDonnee="date"),
            ColumnDefn(u"Montant", "left", 100, "montant", stringConverter=FormateMontant, typeDonnee="montant"),
            ColumnDefn(u"Heure", "left", 100, "heure", typeDonnee="texte"),
        ])

        self.SetObjects(self.donnees)


    def MAJ(self, ID=None):
        # Cr�ation de donn�es exemples
        dictDonnees = {
            "ID" : 1,
            "texte" : "Texte unicode",
            "entier" : 22,
            "date" : datetime.date.today(),
            "montant" : decimal.Decimal(13.50),
            "heure" : "35h30",
        }
        self.donnees = []
        for x in range(10) :
            self.donnees.append(Track(dictDonnees))
        # MAJ
        self.InitObjectListView()



class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self, -1, name="test1")
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_1.Add(panel, 1, wx.ALL|wx.EXPAND)
        self.SetSizer(sizer_1)
        self.listview = ListView(panel, id=-1, name="OL_test", style=wx.LC_REPORT|wx.SUNKEN_BORDER|wx.LC_SINGLE_SEL|wx.LC_HRULES|wx.LC_VRULES)
        self.listview.MAJ() 
        # Test de l'export Texte
        ExportExcel(listview=self.listview)
        
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_2.Add(self.listview, 1, wx.ALL|wx.EXPAND, 4)
        panel.SetSizer(sizer_2)
        self.Layout()

if __name__ == '__main__':
    app = wx.App(0)
    #wx.InitAllImageHandlers()
    frame_1 = MyFrame(None, -1, "OL Test Export")
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()
