#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activit�s
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-15 Ivan LUCAS
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------


import Chemins
from Utils import UTILS_Adaptations
from Utils.UTILS_Traduction import _
import wx
from Ctrl import CTRL_Bouton_image
import wx.lib.dialogs as dialogs
import GestionDB
from Utils import UTILS_Dates
from Utils import UTILS_Titulaires
from Utils import UTILS_Historique
from Dlg import DLG_Appliquer_forfait

import datetime
import time


from Utils import UTILS_Interface
from Ctrl.CTRL_ObjectListView import FastObjectListView, ColumnDefn, Filter, CTRL_Outils


class Track(object):
    def __init__(self, donnees):
        self.IDindividu = donnees["IDindividu"]
        self.nom = donnees["nom"]
        self.prenom = donnees["prenom"]
        self.date_naiss = donnees["date_naiss"]
        self.age = donnees["age"]
        self.nomTitulaires = donnees["nomTitulaires"]
        self.IDcompte_payeur = donnees["IDcompte_payeur"]
        self.IDfamille = donnees["IDfamille"]
        self.rue = donnees["rue"]
        self.cp = donnees["cp"]
        self.ville = donnees["ville"]
        self.nomSecteur = donnees["nomSecteur"]
        self.inscrit = "non"
        
        
    
class ListView(FastObjectListView):
    def __init__(self, *args, **kwds):
        # Initialisation du listCtrl
        self.IDactivite = None
        self.nom_fichier_liste = __file__
        FastObjectListView.__init__(self, *args, **kwds)
        # Binds perso
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnItemActivated)
        self.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)
        
    def OnItemActivated(self,event):
        print("ok")
                
    def InitModel(self):
        self.donnees = self.GetTracks()

    def GetTracks(self):
        """ R�cup�ration des donn�es """
        dictTitulaires = UTILS_Titulaires.GetTitulaires()
        
        DB = GestionDB.DB()
        
        # R�cup�ration des inscriptions existantes
        req = """SELECT IDinscription, IDindividu, IDfamille, IDactivite, IDgroupe, IDcategorie_tarif, IDcompte_payeur, date_inscription, parti
        FROM inscriptions
        WHERE (NOT inscriptions.statut LIKE 'ko%%');"""
        DB.ExecuterReq(req,MsgBox="ExecuterReq")
        listeDonnees = DB.ResultatReq()
        self.dictInscriptions = {}
        for IDinscription, IDindividu, IDfamille, IDactivite, IDgroupe, IDcategorie_tarif, IDcompte_payeur, date_inscription, parti in listeDonnees :
            self.dictInscriptions[(IDindividu, IDfamille, IDactivite) ] = {"IDinscription" : IDinscription, "IDgroupe" : IDgroupe, "IDcategorie_tarif" : IDcategorie_tarif} 
        
        # R�cup�ration des individus
        req = """SELECT individus.IDindividu, nom, prenom, date_naiss, rattachements.IDfamille, comptes_payeurs.IDcompte_payeur
        FROM individus
        LEFT JOIN rattachements ON rattachements.IDindividu = individus.IDindividu
        LEFT JOIN comptes_payeurs ON comptes_payeurs.IDfamille = rattachements.IDfamille
        WHERE IDcategorie IN (1, 2) AND rattachements.IDfamille IS NOT NULL
        GROUP BY individus.IDindividu, rattachements.IDfamille, comptes_payeurs.IDcompte_payeur;"""
        DB.ExecuterReq(req,MsgBox="ExecuterReq")
        listeDonnees = DB.ResultatReq()
        
        DB.Close()
        listeListeView = []
        for IDindividu, nom, prenom, date_naiss, IDfamille, IDcompte_payeur in listeDonnees :
            date_naiss = UTILS_Dates.DateEngEnDateDD(date_naiss)
            age = UTILS_Dates.CalculeAge(date_naiss=date_naiss)
            nomTitulaires = dictTitulaires[IDfamille]["titulairesSansCivilite"]
            rue = dictTitulaires[IDfamille]["adresse"]["rue"]
            cp = dictTitulaires[IDfamille]["adresse"]["cp"]
            ville = dictTitulaires[IDfamille]["adresse"]["ville"]
            nomSecteur = dictTitulaires[IDfamille]["adresse"]["nomSecteur"]
            dictTemp = {
                "IDindividu" : IDindividu, "nom" : nom, "prenom" : prenom, "date_naiss" : date_naiss, "age" : age, "nomTitulaires" : nomTitulaires, "IDfamille" : IDfamille, "IDcompte_payeur" : IDcompte_payeur,
                "rue" : rue, "cp" : cp, "ville" : ville, "nomSecteur" : nomSecteur,
                }
            listeListeView.append(Track(dictTemp))
        return listeListeView
      
    def InitObjectListView(self):            
        # Couleur en alternance des lignes
        self.oddRowsBackColor = UTILS_Interface.GetValeur("couleur_tres_claire", wx.Colour(240, 251, 237))
        self.evenRowsBackColor = wx.Colour(255, 255, 255)
        self.useExpansionColumn = True

        def FormateDate(date):
            return UTILS_Dates.DateDDEnFr(date)
        
        def FormateAge(age):
            if age == None : return ""
            return _("%d ans") % age
        
        def FormateInscrit(inscrit):
            if inscrit == "oui" :
                return "Oui"
            else :
                return ""
            
        liste_Colonnes = [
            ColumnDefn(_("IDindividu"), "left", 0, "IDindividu", typeDonnee="entier"),
            ColumnDefn(_("Inscrit"), 'left', 50, "inscrit", typeDonnee="texte", stringConverter=FormateInscrit),
            ColumnDefn(_("Nom"), 'left', 120, "nom", typeDonnee="texte"),
            ColumnDefn(_("Pr�nom"), "left", 120, "prenom", typeDonnee="texte"),
            ColumnDefn(_("Date naiss."), "left", 80, "date_naiss", typeDonnee="date", stringConverter=FormateDate),
            ColumnDefn(_("Age"), "left", 60, "age", typeDonnee="entier", stringConverter=FormateAge),
            ColumnDefn(_("Famille"), "left", 280, "nomTitulaires", typeDonnee="texte"),
            ColumnDefn(_("Rue"), "left", 200, "rue", typeDonnee="texte"),
            ColumnDefn(_("CP"), "left", 50, "cp", typeDonnee="texte"),
            ColumnDefn(_("Ville"), "left", 150, "ville", typeDonnee="texte"),
            ColumnDefn(_("Secteur"), "left", 150, "nomSecteur", typeDonnee="texte"),
            ]
        
        self.SetColumns(liste_Colonnes)
        self.CreateCheckStateColumn(0)
        self.SetEmptyListMsg(_("Aucun individu"))
        self.SetEmptyListMsgFont(wx.FFont(11, wx.DEFAULT, False, "Tekton"))
        self.SetSortColumn(self.columns[3])
        self.SetObjects(self.donnees)
       
    def MAJ(self):
        self.InitModel()
        self.InitObjectListView()
    
    def Selection(self):
        return self.GetSelectedObjects()

    def OnContextMenu(self, event):
        """Ouverture du menu contextuel """
        # Cr�ation du menu contextuel
        menuPop = UTILS_Adaptations.Menu()
    
        # Item Apercu avant impression
        item = wx.MenuItem(menuPop, 40, _("Aper�u avant impression"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Apercu.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.Apercu, id=40)
        
        # Item Imprimer
        item = wx.MenuItem(menuPop, 50, _("Imprimer"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Imprimante.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.Imprimer, id=50)

        menuPop.AppendSeparator()
    
        # Item Export Texte
        item = wx.MenuItem(menuPop, 600, _("Exporter au format Texte"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Texte2.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.ExportTexte, id=600)
        
        # Item Export Excel
        item = wx.MenuItem(menuPop, 700, _("Exporter au format Excel"))
        bmp = wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Excel.png"), wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.ExportExcel, id=700)

        self.PopupMenu(menuPop)
        menuPop.Destroy()

    def Apercu(self, event):
        from Utils import UTILS_Printer
        prt = UTILS_Printer.ObjectListViewPrinter(self, titre=_("Liste des individus � inscrire"), format="A", orientation=wx.PORTRAIT)
        prt.Preview()

    def Imprimer(self, event):
        from Utils import UTILS_Printer
        prt = UTILS_Printer.ObjectListViewPrinter(self, titre=_("Liste des individus � inscrire"), format="A", orientation=wx.PORTRAIT)
        prt.Print()

    def ExportTexte(self, event):
        from Utils import UTILS_Export
        UTILS_Export.ExportTexte(self, titre=_("Liste des individus � inscrire"))
        
    def ExportExcel(self, event):
        from Utils import UTILS_Export
        UTILS_Export.ExportExcel(self, titre=_("Liste des individus � inscrire"))
    
    def SetIDactivite(self, IDactivite=None):
        self.IDactivite = IDactivite
        listeTemp = []
        for track in self.donnees :
            key = (track.IDindividu, track.IDfamille, IDactivite)
            if key in self.dictInscriptions :
                track.inscrit = "oui"
            else :
                track.inscrit = "non"
            listeTemp.append(track)
        self.RefreshObjects(listeTemp) 
        
    def Inscrire(self, IDactivite=None, nomActivite="", IDgroupe=None, nomGroupe="", IDcategorie_tarif=None, nomCategorie=""):
        """ Lance la proc�dure d'inscription """
        tracks = self.GetCheckedObjects() 
        if len(tracks) == 0 :
            dlg = wx.MessageDialog(self, _("Vous devez cocher au moins un individu dans la liste !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return

        dlg = wx.MessageDialog(self, _("Souhaitez-vous vraiment inscrire %d individus � l'activit� '%s' ?") % (len(tracks), nomActivite), _("Confirmation"), wx.YES_NO|wx.NO_DEFAULT|wx.CANCEL|wx.ICON_INFORMATION)
        reponse = dlg.ShowModal()
        dlg.Destroy() 
        if reponse  != wx.ID_YES :
            return
        
        dlgprogress = wx.ProgressDialog(_("Veuillez patienter"), _("Lancement de la proc�dure..."), maximum=len(tracks), parent=None, style= wx.PD_SMOOTH | wx.PD_ESTIMATED_TIME | wx.PD_REMAINING_TIME | wx.PD_CAN_ABORT | wx.PD_AUTO_HIDE | wx.PD_APP_MODAL)
        
        listeAnomalies = []
        listeValidees = []
        index = 0
        for track in tracks :            
            # Recherche du nom de l'individu
            if track.prenom == None :
                nomIndividu = track.nom
            else :
                nomIndividu = "%s %s" % (track.nom, track.prenom)
            
            keepGoing, skip = dlgprogress.Update(index, _("[%d/%d] Inscription de %s...") % (index, len(tracks), nomIndividu))
            
            # V�rifie si individu d�j� inscrit
            if track.inscrit == "oui" :
                listeAnomalies.append(_("%s (Famille de %s) : Individu d�j� inscrit") % (nomIndividu, track.nomTitulaires))
                index += 1
                
            else :
                # Sauvegarde
                DB = GestionDB.DB()
                listeDonnees = [
                    ("IDindividu", track.IDindividu ),
                    ("IDfamille", track.IDfamille ),
                    ("IDactivite", IDactivite ),
                    ("IDgroupe", IDgroupe),
                    ("IDcategorie_tarif", IDcategorie_tarif),
                    ("IDcompte_payeur", track.IDcompte_payeur),
                    ("date_inscription", str(datetime.date.today()) ),
                    ("statut", "ok"),
                    ("parti", 0),
                    ]
                IDinscription = DB.ReqInsert("inscriptions", listeDonnees)
                DB.Close()
                
                # M�morise l'action dans l'historique
                UTILS_Historique.InsertActions([{
                    "IDindividu" : track.IDindividu,
                    "IDfamille" : track.IDfamille,
                    "IDcategorie" : 18, 
                    "action" : _("Inscription � l'activit� '%s' sur le groupe '%s' avec la tarification '%s'") % (nomActivite, nomGroupe, nomCategorie)
                    },])
                
                # Saisie de forfaits auto
                f = DLG_Appliquer_forfait.Forfaits(IDfamille=track.IDfamille, listeActivites=[IDactivite,], listeIndividus=[track.IDindividu,], saisieManuelle=False, saisieAuto=True)
                f.Applique_forfait(selectionIDcategorie_tarif=IDcategorie_tarif, inscription=True, selectionIDactivite=IDactivite) 
                            
                # Actualise l'affichage
                self.dictInscriptions[(track.IDindividu, track.IDfamille, IDactivite)] = {"IDinscription" : IDinscription, "IDgroupe" : IDgroupe, "IDcategorie_tarif" : IDcategorie_tarif} 
                track.inscrit = "oui"
                self.RefreshObject(track)
                
                # Attente
                listeValidees.append(track)
                time.sleep(0.2)
                index += 1
            
            # Stoppe la proc�dure
            if keepGoing == False :
                break
            
        # Fermeture dlgprogress
        dlgprogress.Destroy()
        
        # Messages de fin
        if len(listeAnomalies) > 0 :
            message1 = _("%d inscriptions ont �t� cr��es avec succ�s mais les %d anomalies suivantes ont �t� trouv�es :") % (len(listeValidees), len(listeAnomalies))
            message2 = "\n".join(listeAnomalies)
            dlg = dialogs.MultiMessageDialog(self, message1, caption = _("Inscription"), msg2=message2, style = wx.ICON_EXCLAMATION | wx.YES|wx.YES_DEFAULT, btnLabels={wx.ID_YES : _("Ok")})
            reponse = dlg.ShowModal() 
            dlg.Destroy() 
        else :
            dlg = wx.MessageDialog(self, _("%d inscriptions ont �t� cr��es avec succ�s !") % len(listeValidees), _("Fin"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()










# -------------------------------------------------------------------------------------------------------------------------------------

class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self, -1, name="test1")
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_1.Add(panel, 1, wx.ALL|wx.EXPAND)
        self.SetSizer(sizer_1)
        self.myOlv = ListView(panel, id=-1, style=wx.LC_REPORT|wx.SUNKEN_BORDER|wx.LC_SINGLE_SEL|wx.LC_HRULES|wx.LC_VRULES)
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
