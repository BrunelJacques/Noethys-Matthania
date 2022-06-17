#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys branche Matthania
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS, JB
# Copyright:       (c) 2010-15 Ivan LUCAS, JB
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------

import os, sys
import Chemins
import wx
import platform
import datetime
import traceback
import time
import GestionDB
import UpgradeDB
import FonctionsPerso
import random
import wx.lib.agw.aui as aui
import wx.lib.agw.advancedsplash as AS
import wx.lib.agw.toasterbox as Toaster
from Utils.UTILS_Traduction import _
from Utils import UTILS_Traduction
from Utils import UTILS_Linux
from Utils import UTILS_Config
from Utils import UTILS_Customize
from Utils import UTILS_Historique
from Utils import UTILS_Sauvegarde_auto
from Utils import UTILS_Rapport_bugs
from Utils import UTILS_Utilisateurs
from Utils import UTILS_Fichiers
from Utils import UTILS_Json
from Utils import UTILS_Parametres
from Ctrl import CTRL_MenuItems
from Ctrl import CTRL_Accueil
from Ctrl import CTRL_Messages
from Ctrl import CTRL_Identification
from Ctrl import CTRL_Numfacture
from Ctrl import CTRL_Recherche_individus
from Ctrl import CTRL_Ephemeride
from Dlg import DLG_Effectifs
from Dlg import DLG_Message_html
from Dlg import DLG_Enregistrement
from Ctrl import CTRL_Toaster
from Ctrl import CTRL_Portail_serveur
from Ctrl import CTRL_TaskBarIcon
from urllib.request import urlopen
from Crypto.Hash import SHA256
if "linux" in sys.platform :
    UTILS_Linux.AdaptationsDemarrage()

# Constantes générales
CUSTOMIZE = None
HEUREDEBUT = time.time()
VERSION_APPLICATION = FonctionsPerso.GetVersionLogiciel()
NOM_APPLICATION = "Noethys-Matthania"

# ID pour la barre des menus
ID_DERNIER_FICHIER = 700
ID_PREMIERE_PERSPECTIVE = 500
ID_AFFICHAGE_PANNEAUX = 600

# ID pour la barre d'outils
ID_TB_GESTIONNAIRE = wx.Window.NewControlId()
ID_TB_LISTE_CONSO = wx.Window.NewControlId()
ID_TB_BADGEAGE = wx.Window.NewControlId()
ID_TB_REGLER_FACTURE = wx.Window.NewControlId()
ID_TB_CALCULATRICE = wx.Window.NewControlId()
ID_TB_UTILISATEUR = wx.Window.NewControlId()


class MainFrame(wx.Frame):
    def __init__(self, parent):
        wx.Frame.__init__(self, parent, -1, title=_("Noethys-Matthania"), name="general", style=wx.DEFAULT_FRAME_STYLE)

        theme = CUSTOMIZE.GetValeur("interface", "theme", "Vert")

        # Icône
        try :
            icon = wx.Icon()
        except :
            icon = wx.EmptyIcon()
        icon.CopyFromBitmap(wx.Bitmap(Chemins.GetStaticPath("Images/Interface/%s/Icone.png" % theme), wx.BITMAP_TYPE_ANY))
        self.SetIcon(icon)

        # TaskBarIcon
        self.taskBarIcon = CTRL_TaskBarIcon.CustomTaskBarIcon()

        # Ecrit la date et l'heure dans le journal.log
        dateDuJour = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        systeme = "%s %s %s %s " % (sys.platform, platform.system(), platform.release(), platform.machine())
        version_python = "3"
        print("-------- %s | %s | Python %s | wxPython %s | %s --------" % (dateDuJour, VERSION_APPLICATION, version_python, wx.version(), systeme))

        # Diminution de la taille de la police sous linux
        from Utils import UTILS_Linux
        UTILS_Linux.AdaptePolice(self)

    def Initialisation(self):
        # Vérifie que le fichier de configuration existe bien
        self.nouveauFichierConfig = False
        if UTILS_Config.IsFichierExists() == False :
            print("Generation d'un nouveau fichier de config")
            self.nouveauFichierConfig = UTILS_Config.GenerationFichierConfig()

        # Récupération des fichiers de configuration
        self.userConfig = self.GetFichierConfig() # Fichier de config de l'utilisateur
        
        # Gestion des utilisateurs
        self.listeUtilisateurs = [] 
        self.dictUtilisateur = None

        #self.langue = UTILS_Config.GetParametre("langue_interface", None)
        #self.ChargeTraduction()

        # Récupération du nom du dernier fichier chargé
        self.nomDernierFichier = ""
        if "nomFichier" in self.userConfig :
            self.nomDernierFichier = self.userConfig["nomFichier"]
        self.userConfig["nomFichier"] = ""
        
        if "assistant_demarrage" in self.userConfig :
            if self.userConfig["assistant_demarrage"] == True :
                self.afficherAssistant = False
            else: self.afficherAssistant = True
        else:
            self.afficherAssistant = True

        # Recherche si une mise à jour internet existe
        self.MAJexiste = False
        """
        self.versionMAJ = None
        if sys.executable.endswith("python.exe") == True :
            self.MAJexiste = False
        else:
            self.MAJexiste = self.RechercheMAJinternet()
        
        if UTILS_Config.GetParametre("propose_maj", defaut=True) == False :
            self.MAJexiste = False
        """

        # Récupération des perspectives de la page d'accueil
        if ("perspectives" in self.userConfig) == True :
            self.perspectives = self.userConfig["perspectives"]
        else:
            self.perspectives = []
        if ("perspective_active" in self.userConfig) == True :
            self.perspective_active = self.userConfig["perspective_active"]
        else:
            self.perspective_active = None
        
        # Sélection de l'interface MySQL
        if "interface_mysql" in self.userConfig:
            interface_mysql = self.userConfig["interface_mysql"]
            if "pool_mysql" in self.userConfig:
                pool_mysql = self.userConfig["pool_mysql"]
            else:
                pool_mysql = 5
            GestionDB.SetInterfaceMySQL(interface_mysql, pool_mysql)
        
        # Affiche le titre du fichier en haut de la frame
        self.SetTitleFrame(nomFichier="")

        # Création du AUI de la fenêtre 
        self._mgr = aui.AuiManager()
        if "linux" not in sys.platform :
            try :
                self._mgr.SetArtProvider(aui.ModernDockArt(self))
            except :
                pass
        self._mgr.SetManagedWindow(self)

        # Barre des tâches
        self.CreateStatusBar()
        self.GetStatusBar().SetStatusText(_("Bienvenue dans %s...") % NOM_APPLICATION)
        
        # Création de la barre des menus
        self.CreationBarreMenus()
        
        # Création de la barre d'outils
        self.CreationBarresOutils() 
        
        # Création des panneaux
        self.CreationPanneaux()
        
        # Création des Binds
        self.CreationBinds()
        
        # Détermine la taille de la fenêtre
        self.SetMinSize((935, 740))
        if ("taille_fenetre" in self.userConfig) == False :
            self.userConfig["taille_fenetre"] = (0, 0)
        taille_fenetre = self.userConfig["taille_fenetre"]
        if taille_fenetre == (0, 0) or taille_fenetre == [0, 0]:
            self.Maximize(True)
        else:
            self.SetSize(taille_fenetre)
        self.CenterOnScreen()
        
        # Désactive les items de la barre de menus
        self.ActiveBarreMenus(False) 
        
        # Binds
        self.Bind(wx.EVT_CLOSE, self.OnClose)
##        self.Bind(wx.EVT_SIZE, self.OnSize)

        # Affiche un Toaster quand une mise à jour du logiciel est disponible
        if self.MAJexiste == True :
            texteToaster = _("Une nouvelle version de Noethys est disponible !")
            self.AfficheToaster(titre=_("Mise à jour"), texte=texteToaster, couleurFond="#81A8F0") 
        
        # Timer Autodeconnect
        self.autodeconnect_timer = wx.Timer(self, -1)
        self.autodeconnect_position = wx.GetMousePosition() 
        self.Bind(wx.EVT_TIMER, self.Autodeconnect, self.autodeconnect_timer)
        self.Start_autodeconnect_timer() 

    def Start_autodeconnect_timer(self):
        """ Lance le timer pour autodeconnexion de l'utilisateur """
        # Stoppe le timer si besoin
        if self.autodeconnect_timer.IsRunning():
            self.autodeconnect_timer.Stop()
        # Lance le timer
        if "autodeconnect" in self.userConfig :
            if self.userConfig["autodeconnect"] not in (0, None) :
                secondes = self.userConfig["autodeconnect"]
                self.autodeconnect_timer.Start(secondes * 1000)
        
    def ChargeTraduction(self):
        UTILS_Traduction.ChargeTraduction(self.langue)

    def Select_langue(self):
        # Recherche les fichiers de langues existants
        listeLabels = [u"Français (fr_FR - par défaut)",]
        listeCodes = [None,]

        for rep in (Chemins.GetStaticPath("Lang"), UTILS_Fichiers.GetRepLang()) :
            for nomFichier in os.listdir(rep) :
                if nomFichier.endswith("lang") :
                    code, extension = nomFichier.split(".")
                    data = UTILS_Json.Lire(os.path.join(rep, nomFichier), conversion_auto=True)

                    # Lecture des caractéristiques
                    dictInfos = data["###INFOS###"]
                    nom = dictInfos["nom_langue"]
                    code = dictInfos["code_langue"]

                    label = "%s (%s)" % (nom, code)
                    if code not in listeCodes :
                        listeLabels.append(label)
                        listeCodes.append(code)

        # DLG
        code = None
        dlg = wx.SingleChoiceDialog(self, "Sélectionnez la langue de l'interface :", "Bienvenue dans Noethys", listeLabels, wx.CHOICEDLG_STYLE)
        dlg.SetSize((400, 400))
        dlg.CenterOnScreen()
        if dlg.ShowModal() == wx.ID_OK:
            index = dlg.GetSelection()
            code = listeCodes[index]
        dlg.Destroy()
        
        return code

    def GetCustomize(self):
        return CUSTOMIZE

    def SetTitleFrame(self, nomFichier=""):
        if "[RESEAU]" in nomFichier :
            port, hote, user, mdp = nomFichier.split(";")
            nomFichier = nomFichier[nomFichier.index("[RESEAU]") + 8:]
            nomFichier = _("Fichier réseau : %s | %s | %s") % (nomFichier, hote, user)
        if nomFichier != "" :
            nomFichier = " - [" + nomFichier + "]"
        titreFrame = NOM_APPLICATION + " v" + VERSION_APPLICATION + nomFichier
        self.SetTitle(titreFrame)

    def GetFichierConfig(self):
        """ Récupère le dictionnaire du fichier de config """
        cfg = UTILS_Config.FichierConfig()
        return cfg.GetDictConfig()

    def SaveFichierConfig(self):
        """ Sauvegarde le dictionnaire du fichier de config """
        cfg = UTILS_Config.FichierConfig()
        cfg.SetDictConfig(dictConfig=self.userConfig )
    
    def OnSize(self, event):
        self.SetTitle(str(self.GetSize()))
        
    def OnClose(self, event):
        if self.Quitter() == False :
            return
        event.Skip()

    def Quitter(self, videRepertoiresTemp=True, sauvegardeAuto=True):
        """ Fin de l'application """

        # Vérifie si une synchronisation Connecthys n'est pas en route
        #if self.IsSynchroConnecthys() == True :
        #    return False

        # Mémorise l'action dans l'historique
        if self.userConfig["nomFichier"] != "" :
            try :
                UTILS_Historique.InsertActions([{
                    "IDcategorie" : 1,
                    "action" : _("Fermeture du fichier"),
                    },])
            except :
                pass
                
        # Mémorisation du paramètre de la taille d'écran
        if self.IsMaximized() == True :
            taille_fenetre = (0, 0)
        else:
            taille_fenetre = tuple(self.GetSize())
        self.userConfig["taille_fenetre"] = taille_fenetre
        
        # Mémorisation des perspectives
        self.SauvegardePerspectiveActive()
        self.userConfig["perspectives"] = self.perspectives
        self.userConfig["perspective_active"] = self.perspective_active
        
        if hasattr(self, "ctrl_remplissage") :
            self.userConfig["perspective_ctrl_effectifs"] = self.ctrl_remplissage.SavePerspective()
            self.userConfig["page_ctrl_effectifs"] = self.ctrl_remplissage.GetPageActive()

        # Codage du mdp réseau si besoin
        if "[RESEAU]" in self.userConfig["nomFichier"] and "#64#" not in self.userConfig["nomFichier"]:
            nom = GestionDB.EncodeNomFichierReseau(self.userConfig["nomFichier"])
            self.userConfig["nomFichier"] = nom

        derniersFichiers = []
        for nom in self.userConfig["derniersFichiers"]:
            if "[RESEAU]" in nom and "#64#" not in nom:
                nom = GestionDB.EncodeNomFichierReseau(nom)
            derniersFichiers.append(nom)
        self.userConfig["derniersFichiers"] = derniersFichiers

        # Sauvegarde du fichier de configuration
        self.SaveFichierConfig()

        # Sauvegarde automatique
        if self.userConfig["nomFichier"] != "" and sauvegardeAuto == True :
            resultat = self.SauvegardeAutomatique()
            if resultat == wx.ID_CANCEL :
                return False

        # Vidage des répertoires Temp
        if videRepertoiresTemp == True :
            FonctionsPerso.VideRepertoireTemp()
            FonctionsPerso.VideRepertoireUpdates()
        
        # Arrête le timer Autodeconnect
        if self.autodeconnect_timer.IsRunning():
            self.autodeconnect_timer.Stop()
        
        # Affiche les connexions restées ouvertes
        GestionDB.AfficheConnexionsOuvertes()

        # Détruit le taskBarIcon
        self.taskBarIcon.Cacher()
        self.taskBarIcon.Detruire()
        self.Destroy()

    def SauvegardeAutomatique(self):
        save = UTILS_Sauvegarde_auto.Sauvegarde_auto(self)
        resultat = save.Start() 
        return resultat
        
    def ChargeFichierExemple(self):
        """ Demande à l'utilisateur s'il souhaite charger le fichier Exemple """
        if self.nouveauFichierConfig == True :
            from Dlg import DLG_Bienvenue
            dlg = DLG_Bienvenue.Dialog(self)
            if dlg.ShowModal() == wx.ID_OK :
                nomFichier = dlg.GetNomFichier()
                dlg.Destroy()
            else :
                dlg.Destroy()
                return
            
            # Charge le fichier Exemple sélectionné
            self.nomDernierFichier = nomFichier
                
            import calendar
            annee = datetime.date.today().year
            numMois = datetime.date.today().month
            listeSelections = []
            listePeriodes = []
            for index in range(0, 3) :
                nbreJoursMois = calendar.monthrange(annee, numMois)[1]
                date_debut = datetime.date(annee, numMois, 1)
                date_fin = datetime.date(annee, numMois, nbreJoursMois)
                listeSelections.append(numMois - 1)
                listePeriodes.append((date_debut, date_fin))
                numMois += 1
                if numMois > 12 :
                    numMois = 1
        
            donnees = {
                    'listeActivites': [1,], 
                    'listeSelections': listeSelections, 
                    'listePeriodes': listePeriodes, 
                    'modeAffichage': 'nbrePlacesPrises', 
                    'dateDebut': None, 
                    'dateFin': None, 
                    'annee': annee, 
                    'page': 0,
                    }
            
            self.ctrl_remplissage.SetDictDonnees(donnees)
            return True
        return False
    
    def CreationPanneaux(self):
        # Panneau Rechercher un individu
        self.ctrl_individus = CTRL_Recherche_individus.Panel(self)
        self._mgr.AddPane(self.ctrl_individus, aui.AuiPaneInfo().Name("recherche").Caption(_("Individus")).
                          CenterPane().PaneBorder(True).CaptionVisible(True) )

        # Panneau Ephéméride
        if CUSTOMIZE.GetValeur("ephemeride", "actif", "1") == "1" :
            self.ctrl_ephemeride = CTRL_Ephemeride.CTRL(self)
            self._mgr.AddPane(self.ctrl_ephemeride, aui.AuiPaneInfo().Name("ephemeride").Caption(_("Ephéméride")).
                          Top().Layer(0).Row(1).Position(0).CloseButton(True).MaximizeButton(True).MinimizeButton(True).MinSize((-1, 100)).BestSize((-1, 100)) )

        # Panneau Serveur Nomadhys
        if UTILS_Config.GetParametre("synchro_serveur_activer", defaut=False) == True :
            from Ctrl import CTRL_Serveur_nomade
            self.ctrl_serveur_nomade = CTRL_Serveur_nomade.Panel(self)
            self._mgr.AddPane(self.ctrl_serveur_nomade, aui.AuiPaneInfo().Name("serveur_nomade").Caption(_("Nomadhys")).
                              Top().Layer(0).Row(2).Position(0).CloseButton(False).MaximizeButton(False).MinimizeButton(False).MinSize((-1, 85)).BestSize((-1, 85)) )

        # Panneau Effectifs
        self.ctrl_remplissage = DLG_Effectifs.CTRL(self)
        self._mgr.AddPane(self.ctrl_remplissage, aui.AuiPaneInfo().Name("effectifs").Caption(_("Tableau de bord")).
                Left().Layer(1).Position(0).CloseButton(True).MaximizeButton(True).MinimizeButton(True).MinSize((580, 200)).BestSize((630, 600)) )

        if ("page_ctrl_effectifs" in self.userConfig) == True :
            self.ctrl_remplissage.SetPageActive(self.userConfig["page_ctrl_effectifs"])
        
        # Panneau Messages
        self.ctrl_messages = CTRL_Messages.Panel(self)
        self._mgr.AddPane(self.ctrl_messages, aui.AuiPaneInfo().Name("messages").Caption(_("Messages")).
                          Left().Layer(1).Position(2).CloseButton(True).MinSize((600, 100)).MaximizeButton(True).MinimizeButton(True) )
        pi = self._mgr.GetPane("messages")
        pi.dock_proportion = 50000 # Proportion
        
        # Panneau Accueil
        self.ctrl_accueil = CTRL_Accueil.Panel(self)
        self._mgr.AddPane(self.ctrl_accueil, aui.AuiPaneInfo().Name("accueil").Caption(_("Accueil")).
                          Bottom().Layer(0).Position(1).Hide().CaptionVisible(False).CloseButton(False).MaximizeButton(False) )
        
        self._mgr.Update()
        
        # Sauvegarde de la perspective par défaut
        self.perspective_defaut = self._mgr.SavePerspective()
        
        # Cache tous les panneaux en attendant la saisie du mot de passe utilisateur
        for pane in self._mgr.GetAllPanes() :
            if pane.name != "accueil" :
                pane.Hide()
        self._mgr.GetPane("accueil").Show().Maximize()
        
        self._mgr.Update()
        
    def CreationBarresOutils(self):
        self.listeBarresOutils = []
        self.dictBarresOutils = {}
        
        # Barre raccourcis --------------------------------------------------
        tb = aui.AuiToolBar(self, -1, wx.DefaultPosition, wx.DefaultSize, agwStyle=aui.AUI_TB_DEFAULT_STYLE | aui.AUI_TB_OVERFLOW | aui.AUI_TB_TEXT | aui.AUI_TB_HORZ_TEXT)
        tb.SetToolBitmapSize(wx.Size(16, 16))
        tb.AddSimpleTool(ID_TB_LISTE_CONSO, _("Liste des conso."), wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Imprimante.png"), wx.BITMAP_TYPE_PNG), _("Imprimer une liste de consommations"))
        tb.AddSeparator()
        tb.AddSimpleTool(ID_TB_REGLER_FACTURE, _("Régler une facture"), wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Reglement.png"), wx.BITMAP_TYPE_PNG), _("Régler une facture à partir de son numéro"))
        self.ctrl_numfacture = CTRL_Numfacture.CTRL(tb, size=(100, -1))
        tb.AddControl(self.ctrl_numfacture)
        tb.AddSeparator()
        tb.AddSimpleTool(ID_TB_CALCULATRICE, _("Calculatrice"), wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Calculatrice.png"), wx.BITMAP_TYPE_PNG), _("Ouvrir la calculatrice"))

        tb.Realize()
        code = "barre_raccourcis"
        label = _("Barre de raccourcis")
        self.listeBarresOutils.append(code)
        self.dictBarresOutils[code] = {"label" : label, "ctrl" : tb}
        self._mgr.AddPane(tb, aui.AuiPaneInfo().Name(code).Caption(label).ToolbarPane().Top())
        self._mgr.Update()
        
        # Barre Utilisateur --------------------------------------------------
        tb = aui.AuiToolBar(self, -1, wx.DefaultPosition, wx.DefaultSize, agwStyle=aui.AUI_TB_DEFAULT_STYLE | aui.AUI_TB_OVERFLOW | aui.AUI_TB_TEXT | aui.AUI_TB_HORZ_TEXT)
        tb.SetToolBitmapSize(wx.Size(16, 16))
        self.ctrl_identification = CTRL_Identification.CTRL(tb, listeUtilisateurs=self.listeUtilisateurs, size=(80, -1))
        tb.AddControl(self.ctrl_identification)
        tb.AddSimpleTool(ID_TB_UTILISATEUR, "xxxxxxxxxxxxxxxxxxxxxxxxxxxx", wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Homme.png"), wx.BITMAP_TYPE_PNG), _("Utilisateur en cours"))
        tb.AddSpacer(50)
        
        tb.Realize()
        code = "barre_utilisateur"
        label = _("Barre Utilisateur")
        self.listeBarresOutils.append(code)
        self.dictBarresOutils[code] = {"label" : label, "ctrl" : tb}
        self._mgr.AddPane(tb, aui.AuiPaneInfo().Name(code).Caption(label).ToolbarPane().Top())
        self._mgr.Update()

        # Barres personnalisées --------------------------------------------
        if ("barres_outils_perso" in self.userConfig) == True :
            texteBarresOutils = self.userConfig["barres_outils_perso"]
        else :
            self.userConfig["barres_outils_perso"] = ""
            texteBarresOutils = ""
        if len(texteBarresOutils) > 0 :
            listeBarresOutils = texteBarresOutils.split("@@@@")
        else :
            listeBarresOutils = []
                
        index = 0
        for texte in listeBarresOutils :
            self.CreerBarreOutils(texte, index)
            index += 1
            
    def CreerBarreOutils(self, texte="", index=0, ctrl=None):
        # Analyse du texte (Nom, style, contenu)
        codeBarre, label, observations, style, contenu = texte.split("###")
        listeContenu = contenu.split(";")
        
        # Recherche des infos du menu
        dictItems = self.GetDictItemsMenu() 
        
        # Analyse du style
        if style == "textedroite" :
            agwStyle = aui.AUI_TB_OVERFLOW | aui.AUI_TB_HORZ_TEXT
        elif style == "textedessous" :
            agwStyle = aui.AUI_TB_OVERFLOW | aui.AUI_TB_TEXT
        elif style == "texteseul" :
            agwStyle = aui.AUI_TB_OVERFLOW | aui.AUI_TB_TEXT
        elif style == "imageseule" :
            agwStyle = aui.AUI_TB_OVERFLOW
        else :
            agwStyle = aui.AUI_TB_OVERFLOW | aui.AUI_TB_TEXT
        
        # Init ToolBar
        if ctrl == None :
            tb = aui.AuiToolBar(self, -1, wx.DefaultPosition, wx.DefaultSize, agwStyle=agwStyle)
            tb.SetToolBitmapSize(wx.Size(16, 16))
        else :
            tb = ctrl
            tb.Clear() 

        for code in listeContenu :
            if code == "|" :
                tb.AddSeparator()
            elif code == "-" :
                tb.AddStretchSpacer()
            elif code.startswith("label:"):
                # Ne fonctionne pas : Il y a un bug sur agw.aui avec la largeur du label
                label = code.replace("label:", "")
                tb.AddSimpleTool(wx.Window.NewControlId(), label, wx.NullBitmap, kind=aui.ITEM_LABEL)
            else :
                item = dictItems[code]
                if "image" in item and style != "texteseul" :
                    image = wx.Bitmap(Chemins.GetStaticPath(item["image"]), wx.BITMAP_TYPE_PNG)
                else :
                    image = wx.NullBitmap
                id = wx.Window.NewControlId()
                tb.AddSimpleTool(id, item["infobulle"], image, item["infobulle"])
                self.Bind(wx.EVT_TOOL, item["action"], id=id)
        
        # Finalisation ToolBar
        tb.Realize()
        self.SendSizeEvent() 

        if ctrl == None :
            self.listeBarresOutils.append(codeBarre)
            self.dictBarresOutils[codeBarre] = {"label" : label, "ctrl" : tb, "texte" : texte}
            self._mgr.AddPane(tb, aui.AuiPaneInfo().Layer(index+1).Name(codeBarre).Caption(label).ToolbarPane().Top())
        self._mgr.Update()

    def CreationBarreMenus(self):
        """ Construit la barre de menus """
        self.ctrlMenu = CTRL_MenuItems.Menu(self)
        self.listeItemsMenu = self.ctrlMenu.GetItemsMenu()
        # Création du menu
        def CreationItem(menuParent, item):
            id = wx.Window.NewControlId()
            if "genre" in item:
                genre = item["genre"]
            else :
                genre = wx.ITEM_NORMAL
            itemMenu = wx.MenuItem(menuParent, id, item["label"], item["infobulle"], genre)
            if "image" in item :
                itemMenu.SetBitmap(wx.Bitmap(Chemins.GetStaticPath(item["image"]), wx.BITMAP_TYPE_PNG))

            menuParent.Append(itemMenu)
            if "actif" in item :
                itemMenu.Enable(item["actif"])
            self.Bind(wx.EVT_MENU, item["action"], id=id)
            self.dictInfosMenu[item["code"]] = {"id" : id, "ctrl" : itemMenu}
            
        def CreationMenu(menuParent, item, sousmenu=False):
            menu = wx.Menu()
            id = wx.Window.NewControlId()
            for sousitem in item["items"] :
                if sousitem == "-" :
                    menu.AppendSeparator()
                elif "items" in sousitem :
                    CreationMenu(menu, sousitem, sousmenu=True)
                else :
                    CreationItem(menu, sousitem)
            if sousmenu == True:
                menuParent.AppendSubMenu(menu,item["label"])
            else :
                menuParent.Append(menu, item["label"])
            self.dictInfosMenu[item["code"]] = {"id" : id, "ctrl" : menu}

        self.menu = wx.MenuBar()
        self.dictInfosMenu = {}
        for item in self.listeItemsMenu :
            CreationMenu(self.menu, item)
        
        
        # -------------------------- AJOUT DES DERNIERS FICHIERS OUVERTS -----------------------------
        menu_fichier = self.dictInfosMenu["menu_fichier"]["ctrl"]

        # Intégration des derniers fichiers ouverts :
        if "derniersFichiers" in self.userConfig:
            listeDerniersFichiersTmp = self.userConfig["derniersFichiers"]
        else :
            listeDerniersFichiersTmp = []

        if len(listeDerniersFichiersTmp) > 0 :
            menu_fichier.AppendSeparator()
            
        # Vérification de la liste
        listeDerniersFichiers = []
        for nomFichier in listeDerniersFichiersTmp :
            if "[RESEAU]" in nomFichier :
                # Version RESEAU
                listeDerniersFichiers.append(nomFichier)
            else:
                # VERSION LOCAL
                fichier = UTILS_Fichiers.GetRepData(u"%s_DATA.dat" % nomFichier)
                test = os.path.isfile(fichier)
                if test == True : 
                    listeDerniersFichiers.append(nomFichier)
        self.userConfig["derniersFichiers"] = listeDerniersFichiers
        
        if len(listeDerniersFichiers) > 0 : 
            index = 0
            for nomFichier in listeDerniersFichiers :
                if "[RESEAU]" in nomFichier :
                    port, hote, user, mdp = nomFichier.split(";")
                    nomFichier = nomFichier[nomFichier.index("[RESEAU]"):]+ " - %s"%hote
                item = wx.MenuItem(menu_fichier, ID_DERNIER_FICHIER + index, "%d. %s" % (index+1, nomFichier), _("Ouvrir le fichier : '%s'") % nomFichier)
                menu_fichier.Append(item)
                index += 1
            self.Bind(wx.EVT_MENU_RANGE, self.On_fichier_DerniersFichiers, id=ID_DERNIER_FICHIER, id2=ID_DERNIER_FICHIER + index)

        # -------------------------- AJOUT DES PERSPECTIVES dans le menu AFFICHAGE -----------------------------
        if self.perspective_active == None : 
            self.dictInfosMenu["perspective_defaut"]["ctrl"].Check(True)
        
        index = 0
        position = 1
        menu_affichage = self.dictInfosMenu["menu_affichage"]["ctrl"]
        for dictPerspective in self.perspectives:
            label = dictPerspective["label"]
            item = wx.MenuItem(menu_affichage, ID_PREMIERE_PERSPECTIVE + index, label, _("Afficher la disposition '%s'") % label, wx.ITEM_CHECK)
            menu_affichage.Insert(position, item)
            if self.perspective_active == index : item.Check(True)
            position += 1
            index += 1
        self.Bind(wx.EVT_MENU_RANGE, self.ctrlMenu.On_affichage_perspective_perso, id=ID_PREMIERE_PERSPECTIVE, id2=ID_PREMIERE_PERSPECTIVE+99 )

        # -------------------------- AJOUT DES ELEMENTS A AFFICHER OU CACHER dans le menu AFFICHAGE -----------------------------
        self.listePanneaux = [
            { "label" : _("Tableau de bord"), "code" : "effectifs", "IDmenu" : None },
            { "label" : _("Messages"), "code" : "messages", "IDmenu" : None }, 
            { "label" : _("Ephéméride"), "code" : "ephemeride", "IDmenu" : None }, 
            { "label" : _("Barre de raccourcis"), "code" : "barre_raccourcis", "IDmenu" : None },
            { "label" : _("Barre utilisateur"), "code" : "barre_utilisateur", "IDmenu" : None },
            ]
        ID = ID_AFFICHAGE_PANNEAUX
        menu_affichage = self.dictInfosMenu["menu_affichage"]["ctrl"]
        position = self.RechercherPositionItemMenu("menu_affichage", "perspective_suppr") + 2
        for dictPanneau in self.listePanneaux :
            dictPanneau["IDmenu"] = ID
            label = dictPanneau["label"]
            item = wx.MenuItem(menu_affichage, dictPanneau["IDmenu"], label, _("Afficher l'élément '%s'") % label, wx.ITEM_CHECK)
            menu_affichage.Insert(position, item)
            position += 1
            ID += 1
        self.Bind(wx.EVT_MENU_RANGE, self.ctrlMenu.On_affichage_panneau_afficher, id=ID_AFFICHAGE_PANNEAUX, id2=ID_AFFICHAGE_PANNEAUX+len(self.listePanneaux) )
        
        # -------------------------- AJOUT MISE A JOUR INTERNET -----------------------------
        if self.MAJexiste == True :
            id = wx.Window.NewControlId()
            menu_maj = wx.Menu()
            item = wx.MenuItem(menu_maj, id, _("Télécharger la mise à jour"), _("Télécharger la nouvelle mise à jour"))
            item.SetBitmap(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Updater.png"), wx.BITMAP_TYPE_PNG))
            menu_maj.Append(item)
            self.menu.Append(menu_maj, _("<< Télécharger la mise à jour >>"))
            self.Bind(wx.EVT_MENU, self.On_outils_updater, id=id)

        # Finalisation Barre de menu
        self.SetMenuBar(self.menu)

    def CreationBinds(self):
        # Autres
        self.Bind(wx.EVT_MENU_OPEN, self.MAJmenuAffichage)
        # Barre d'outils
        self.Bind(wx.EVT_TOOL, self.ctrlMenu.On_conso_gestionnaire,
                  id=ID_TB_GESTIONNAIRE)
        self.Bind(wx.EVT_TOOL, self.ctrlMenu.On_imprim_conso_journ,
                  id=ID_TB_LISTE_CONSO)
        self.Bind(wx.EVT_TOOL, self.ctrlMenu.On_conso_badgeage, id=ID_TB_BADGEAGE)
        self.Bind(wx.EVT_TOOL, self.ctrlMenu.On_reglements_regler_facture,
                  id=ID_TB_REGLER_FACTURE)
        self.Bind(wx.EVT_TOOL, self.ctrlMenu.On_outils_calculatrice,
                  id=ID_TB_CALCULATRICE)

    def On_fichier_Nouveau(self, event):
        """ Créé une nouvelle base de données """
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "fichier_fichier", "creer") == False: return
        # Demande le nom du fichier
        from Dlg import DLG_Nouveau_fichier
        from Data import DATA_Tables as Tables
        dlg = DLG_Nouveau_fichier.MyDialog(self)
        if dlg.ShowModal() == wx.ID_OK:
            modeFichier = dlg.GetMode()
            nomFichier = dlg.GetNomFichier()
            listeTables = dlg.GetListeTables()
            dictAdministrateur = dlg.GetIdentiteAdministrateur()
            dlg.Destroy()
        else:
            dlg.Destroy()
            return False

        # Affiche d'une fenêtre d'attente
        message = _("Création du nouveau fichier en cours...")

        nbreEtapes = len(Tables.DB_DATA) + 7  # Tables + autres étapes
        dlgprogress = wx.ProgressDialog(message, _("Veuillez patienter..."),
                                        maximum=nbreEtapes, parent=None,
                                        style=wx.PD_SMOOTH | wx.PD_AUTO_HIDE | wx.PD_APP_MODAL)
        numEtape = 1

        if "[RESEAU]" in nomFichier:
            self.SetStatusText(
                _("Création du fichier '%s' en cours...") % nomFichier[
                                                            nomFichier.index(
                                                                "[RESEAU]"):])
        else:
            self.SetStatusText(
                _("Création du fichier '%s' en cours...") % nomFichier)

        # Vérification de validité du fichier
        if nomFichier == "":
            dlgprogress.Destroy()
            dlg = wx.MessageDialog(self,
                                   _("Le nom que vous avez saisi n'est pas valide !"),
                                   "Erreur", wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            if "[RESEAU]" in nomFichier:
                nomFichier = nomFichier[nomFichier.index("[RESEAU]"):]
            self.SetStatusText(
                _("Echec de la création du fichier '%s' : nom du fichier non valide.") % nomFichier)
            return False

        if "[RESEAU]" not in nomFichier:
            # Version LOCAL

            # Vérifie si un fichier ne porte pas déjà ce nom :
            fichier = UTILS_Fichiers.GetRepData(u"%s_DATA.dat" % nomFichier)
            test = os.path.isfile(fichier)
            if test == True:
                dlgprogress.Destroy()
                dlg = wx.MessageDialog(self,
                                       _("Vous possédez déjà un fichier qui porte le nom '") + nomFichier + _(
                                           "'.\n\nVeuillez saisir un autre nom."),
                                       "Erreur", wx.OK | wx.ICON_ERROR)
                dlg.ShowModal()
                dlg.Destroy()
                self.SetStatusText(
                    _("Echec de la création du fichier '%s' : Le nom existe déjà.") % nomFichier)
                return False

        else:
            # Version RESEAU
            dictResultats = GestionDB.TestConnexionMySQL(typeTest="fichier",
                                                         nomFichier="%s_DATA" % nomFichier)

            # Vérifie la connexion au réseau
            if dictResultats["connexion"][0] == False:
                dlgprogress.Destroy()
                erreur = dictResultats["connexion"][1]
                dlg = wx.MessageDialog(self,
                                       _("La connexion au réseau MySQL est impossible. \n\nErreur : %s") % erreur,
                                       _("Erreur de connexion"),
                                       wx.OK | wx.ICON_ERROR)
                dlg.ShowModal()
                dlg.Destroy()
                return False

            # Vérifie que le fichier n'est pas déjà utilisé
            if dictResultats["fichier"][
                0] == True and modeFichier != "internet":
                dlgprogress.Destroy()
                dlg = wx.MessageDialog(self, _("Le fichier existe déjà."),
                                       _("Erreur de création de fichier"),
                                       wx.OK | wx.ICON_ERROR)
                dlg.ShowModal()
                dlg.Destroy()
                return False

        ancienFichier = self.userConfig["nomFichier"]
        self.userConfig["nomFichier"] = nomFichier

        # Création de la base DATA
        DB = UpgradeDB.DB(suffixe="DATA", modeCreation=True)
        if DB.echec == 1:
            dlgprogress.Destroy()
            erreur = DB.erreur
            dlg = wx.MessageDialog(self,
                                   _("Erreur dans la création du fichier de données.\n\nErreur : %s") % erreur,
                                   _("Erreur de création de fichier"),
                                   wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            self.userConfig["nomFichier"] = ancienFichier
            return False
        self.SetStatusText(_("Création des tables de données..."))
        # DB.CreationTables(Tables.DB_DATA, fenetreParente=self)

        for table in Tables.DB_DATA:
            dlgprogress.Update(numEtape,
                               _("Création de la table '%s'...") % table);
            numEtape += 1
            DB.CreationUneTable(Tables.DB_DATA, table, )

        # Importation des données par défaut
        message = _("Importation des données par défaut...")
        self.SetStatusText(message)
        dlgprogress.Update(numEtape, message);
        numEtape += 1
        DB.Importation_valeurs_defaut(listeTables)
        DB.Close()

        # Création de la base PHOTOS
        if modeFichier != "internet":
            DB = GestionDB.DB(suffixe="PHOTOS", modeCreation=True)
            if DB.echec == 1:
                dlgprogress.Destroy()
                erreur = DB.erreur
                dlg = wx.MessageDialog(self,
                                       _("Erreur dans la création du fichier de photos.\n\nErreur : %s") % erreur,
                                       _("Erreur de création de fichier"),
                                       wx.OK | wx.ICON_ERROR)
                dlg.ShowModal()
                dlg.Destroy()
                self.userConfig["nomFichier"] = ancienFichier
                return False
            message = _("Création de la table de données des photos...")
            self.SetStatusText(message)
            dlgprogress.Update(numEtape, message);
            numEtape += 1
            DB.CreationTables(Tables.DB_PHOTOS)
            DB.Close()

        # Création de la base DOCUMENTS
        if modeFichier != "internet":
            DB = UpgradeDB.DB(suffixe="DOCUMENTS", modeCreation=True)
            if DB.echec == 1:
                dlgprogress.Destroy()
                erreur = DB.erreur
                dlg = wx.MessageDialog(self,
                                       _("Erreur dans la création du fichier de documents.\n\nErreur : %s") % erreur,
                                       _("Erreur de création de fichier"),
                                       wx.OK | wx.ICON_ERROR)
                dlg.ShowModal()
                dlg.Destroy()
                self.userConfig["nomFichier"] = ancienFichier
                return False
            message = _("Création de la table de données des documents...")
            self.SetStatusText(message)
            dlgprogress.Update(numEtape, message);
            numEtape += 1
            DB.CreationTables(Tables.DB_DOCUMENTS)
            DB.Close()

        # Création des index
        message = _("Création des index des tables...")
        self.SetStatusText(message)
        dlgprogress.Update(numEtape, message);
        numEtape += 1
        DB = UpgradeDB.DB(suffixe="DATA")
        DB.CreationTousIndex()
        DB.Close()
        DB = UpgradeDB.DB(suffixe="PHOTOS")
        DB.CreationTousIndex()
        DB.Close()

        # Créé un identifiant unique pour ce fichier
        message = _("Création des informations sur le fichier...")
        self.SetStatusText(message)
        dlgprogress.Update(numEtape, message);
        numEtape += 1
        d = datetime.datetime.now()
        IDfichier = d.strftime("%Y%m%d%H%M%S")
        for x in range(0, 3):
            IDfichier += random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ")

        # Mémorisation des informations sur le fichier
        listeDonnees = [
            ("date_creation", str(datetime.date.today())),
            ("version", VERSION_APPLICATION),
            ("IDfichier", IDfichier),
        ]
        DB = GestionDB.DB()
        for nom, valeur in listeDonnees:
            donnees = [("categorie", "fichier"), ("nom", nom),
                       ("parametre", valeur), ]
            DB.ReqInsert("parametres", donnees)
        DB.Close()

        # Sauvegarde et chargement de l'identité Administrateur
        message = _("Création de l'identité administrateur...")
        self.SetStatusText(message)
        dlgprogress.Update(numEtape, message);
        numEtape += 1

        DB = GestionDB.DB()
        listeDonnees = [
            ("sexe", dictAdministrateur["sexe"]),
            ("nom", dictAdministrateur["nom"]),
            ("prenom", dictAdministrateur["prenom"]),
            ("mdp", dictAdministrateur["mdp"]),
            ("mdpcrypt", dictAdministrateur["mdpcrypt"]),
            ("profil", dictAdministrateur["profil"]),
            ("actif", dictAdministrateur["actif"]),
            ("image", dictAdministrateur["image"]),
        ]
        IDutilisateur = DB.ReqInsert("utilisateurs", listeDonnees)
        DB.Close()

        # Procédures
        from Utils import UTILS_Procedures
        UTILS_Procedures.A9081()  # Création du profil de configuration de la liste des infos médicales

        message = _("Création terminée...")
        self.SetStatusText(message)
        dlgprogress.Update(numEtape, message);
        numEtape += 1

        # Chargement liste utilisateurs
        self.listeUtilisateurs = self.GetListeUtilisateurs()
        self.ChargeUtilisateur(IDutilisateur=IDutilisateur)

        # Met à jour l'affichage des panels
        self.MAJ()
        self.SetTitleFrame(nomFichier=nomFichier)
        if CUSTOMIZE.GetValeur("ephemeride", "actif", "1") == "1":
            self.ctrl_ephemeride.Initialisation()

        # Récupération de la perspective chargée
        if self.perspective_active != None:
            self._mgr.LoadPerspective(
                self.perspectives[self.perspective_active]["perspective"])
            self.ForcerAffichagePanneau("ephemeride")
        else:
            self._mgr.LoadPerspective(self.perspective_defaut)

        # Active les items de la barre de menus
        self.ActiveBarreMenus(True)

        # Met à jour la liste des derniers fichiers de la barre des menus
        self.MAJlisteDerniersFichiers(nomFichier)

        # Met à jour le menu
        self.MAJmenuDerniersFichiers()

        # Sauvegarde du fichier de configuration
        self.SaveFichierConfig()

        # Boîte de dialogue pour confirmer la création
        if "[RESEAU]" in nomFichier:
            nomFichier = nomFichier[nomFichier.index("[RESEAU]"):]

        # Fermeture de la fenêtre d'attente
        dlgprogress.Destroy()

        # Affichage d'un confirmation de succès de la création
        self.SetStatusText(
            _("Le fichier '%s' a été créé avec succès.") % nomFichier)
        dlg = wx.MessageDialog(self, _("Le fichier '") + nomFichier + _(
            "' a été créé avec succès.\n\nVous devez maintenant renseigner les informations concernant l'organisateur."),
                               _("Création d'un fichier"),
                               wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()

        # Demande de remplir les infos sur l'organisateur
        self.SetStatusText(
            _("Paramétrage des informations sur l'organisateur..."))
        from Dlg import DLG_Organisateur
        dlg = DLG_Organisateur.Dialog(self, empecheAnnulation=True)
        dlg.ShowModal()
        dlg.Destroy()

        self.SetStatusText("")

    def On_fichier_DerniersFichiers(self, event):
        """ Ouvre un des derniers fichiers ouverts """
        idMenu = event.GetId()
        nomFichier = self.userConfig["derniersFichiers"][
            idMenu - ID_DERNIER_FICHIER]
        self.OuvrirFichier(nomFichier)

    def On_fichier_Ouvrir(self, event):
        """ Ouvrir un fichier """
        # Boîte de dialogue pour demander le nom du fichier à ouvrir
        fichierOuvert = self.userConfig["nomFichier"]
        from Dlg import DLG_Ouvrir_fichier
        dlg = DLG_Ouvrir_fichier.MyDialog(self, fichierOuvert=fichierOuvert)
        if dlg.ShowModal() == wx.ID_OK:
            nomFichier = dlg.GetNomFichier()
            dlg.Destroy()
        else:
            dlg.Destroy()
            return False
        # Ouverture du fichier
        self.OuvrirFichier(nomFichier)

    def MAJmenuPerspectives(self,):
        # Supprime les perspectives perso dans le menu
        menu_affichage = self.dictInfosMenu["menu_affichage"]["ctrl"]
        item = menu_affichage.FindItemById(ID_PREMIERE_PERSPECTIVE)
        for index in range(0, 99):
            ID = ID_PREMIERE_PERSPECTIVE + index
            item = menu_affichage.FindItemById(ID)
            if item == None: break
            menu_affichage.Remove(ID)
            self.Disconnect(ID, -1, 10014)

            # Décoche la disposition par défaut si nécessaire
        if self.perspective_active == None:
            self.dictInfosMenu["perspective_defaut"]["ctrl"].Check(True)
        else:
            self.dictInfosMenu["perspective_defaut"]["ctrl"].Check(False)

        # Crée les entrées perspectives dans le menu :
        index = 0
        for dictPerspective in self.perspectives:
            label = dictPerspective["label"]
            item = wx.MenuItem(menu_affichage, ID_PREMIERE_PERSPECTIVE + index,
                               label,
                               _("Afficher la disposition '%s'") % label,
                               wx.ITEM_CHECK)
            menu_affichage.Insert(index + 1, item)
            if self.perspective_active == index: item.Check(True)
            index += 1
        self.Bind(wx.EVT_MENU_RANGE, self.ctrlMenu.On_affichage_perspective_perso,
                  id=ID_PREMIERE_PERSPECTIVE, id2=ID_PREMIERE_PERSPECTIVE + 99)

    def GetDictItemsMenu(self):
        """ Renvoie tous les items menu de type action sous forme de dictionnaire """
        dictItems = {}
        def AnalyseItem(listeItems):
            for item in listeItems :
                if type(item) == dict :
                    if "action" in item :
                        dictItems[item["code"]] = item
                    if "items" in item :
                        AnalyseItem(item["items"])
        
        AnalyseItem(self.listeItemsMenu)
        return dictItems

    def RechercherPositionItemMenu(self, codeMenu="", codeItem=""):
        menu = self.dictInfosMenu[codeMenu]["ctrl"]
        IDitem = self.dictInfosMenu[codeItem]["id"]
        index = 0
        for item in menu.GetMenuItems() :
            if item.GetId() == IDitem :
                return index
            index +=1
        return 0

    def MAJmenuAffichage(self, event):
        """ Met à jour la liste des panneaux ouverts du menu Affichage """
        menuOuvert = event.GetMenu()
        if menuOuvert == self.dictInfosMenu["menu_affichage"]["ctrl"] :
            for dictPanneau in self.listePanneaux :
                IDmenuItem = dictPanneau["IDmenu"]
                item = menuOuvert.FindItemById(IDmenuItem)
                panneau = self._mgr.GetPane(dictPanneau["code"])
                if panneau.IsShown() == True :
                    item.Check(True)
                else:
                    item.Check(False)

    def ForcerAffichagePanneau(self, nom="ephemeride"):
        """ Force l'affichage d'un panneau dans la perspective s'il n'y est pas. """
        """ Codé pour le panneau Ephemeride """
        self.ParadeAffichagePanneau(nom)

    def SauvegardePerspectiveActive(self):
        """ Sauvegarde la perspective active """
        if self.perspective_active != None :
            self.perspectives[self.perspective_active]["perspective"] = self._mgr.SavePerspective()

    def SupprimeToutesPerspectives(self):
        """ Supprime toutes les perspectives et sélectionne celle par défaut """
        dlg = wx.MessageDialog(self, _("Suite à la mise à jour de Noethys, %d disposition(s) personnalisée(s) de la page d'accueil sont désormais obsolètes.\n\nPour les besoins de la nouvelle version, elles vont être supprimées. Mais il vous suffira de les recréer simplement depuis le menu Affichage... Merci de votre compréhension !") % len(self.perspectives), _("Mise à jour"), wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()
        # Suppression
        self._mgr.LoadPerspective(self.perspective_defaut)
        self.perspective_active = None
        self.perspectives = []
        self.MAJmenuPerspectives() 
        print("Toutes les perspectives ont ete supprimees.")
        
    def ParadeAffichagePanneau(self, nom=""):
        """ Supprime toutes les perspectives si le panneau donné n'apparait pas """
        pb = False
        for perspective in self.perspectives :
            if nom not in perspective["perspective"] :
                pb = True
        if pb == True :
            self.SupprimeToutesPerspectives()

    def MAJ(self):
        """ Met à jour la page d'accueil """
        if hasattr(self, "ctrl_remplissage") : self.ctrl_remplissage.MAJ() 
        if hasattr(self, "ctrl_individus") : self.ctrl_individus.MAJ()
        if hasattr(self, "ctrl_messages") : self.ctrl_messages.MAJ() 
        if hasattr(self, "ctrl_serveur_nomade") : self.ctrl_serveur_nomade.MAJ()
        if hasattr(self, "ctrl_individus") : wx.CallAfter(self.ctrl_individus.ctrl_recherche.SetFocus)

    def Fermer(self, sauvegarde_auto=True):
        # Vérifie qu'un fichier est chargé
        if self.userConfig["nomFichier"] == "" :
            dlg = wx.MessageDialog(self, _("Il n'y a aucun fichier à fermer !"), _("Erreur"), wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            return
        
        # Mémorise l'action dans l'historique
        UTILS_Historique.InsertActions([{"IDcategorie" : 1, "action" : _("Fermeture du fichier")},])
        
        # Sauvegarde automatique
        if sauvegarde_auto == True :
            resultat = self.SauvegardeAutomatique() 
            if resultat == wx.ID_CANCEL :
                return
        
        # change le nom de fichier
        self.userConfig["nomFichier"] = ""
        self.SetTitleFrame()
        
        # Cache tous les panneaux
        for pane in self._mgr.GetAllPanes() :
            if pane.name != "accueil" :
                pane.Hide()
        self._mgr.GetPane("accueil").Show().Maximize()
        self._mgr.Update()
            
        # Active les items de la barre de menus
        self.ActiveBarreMenus(False) 

        # Désactive la commande FERMER du menu Fichier
        self.dictInfosMenu["fermer_fichier"]["ctrl"].Enable(False)
        self.dictInfosMenu["fichier_informations"]["ctrl"].Enable(False) 
        self.dictInfosMenu["convertir_fichier_reseau"]["ctrl"].Enable(False) 
        self.dictInfosMenu["convertir_fichier_local"]["ctrl"].Enable(False)

    def PurgeListeDerniersFichiers(self, nbre=1):
        listeFichiers = UTILS_Config.GetParametre("derniersFichiers", [])
        UTILS_Config.SetParametre("derniersFichiers", listeFichiers[:nbre])
        self.MAJmenuDerniersFichiers() 
        
    def MAJlisteDerniersFichiers(self, nomFichier=None) :
        """ MAJ la liste des derniers fichiers ouverts dans le config et la barre des menus """
        
        # MAJ de la liste des derniers fichiers ouverts :
        listeFichiers = UTILS_Config.GetParametre("derniersFichiers", defaut=[])
        nbreFichiersMax = UTILS_Config.GetParametre("nbre_derniers_fichiers", defaut=10)
        
        # Si le nom est déjà dans la liste, on le supprime :
        if nomFichier in listeFichiers : listeFichiers.remove(nomFichier)
           
        # On ajoute le nom du fichier en premier dans la liste :
        if nomFichier != None :
            listeFichiers.insert(0, nomFichier)
        listeFichiers = listeFichiers[:nbreFichiersMax]
        
        # On enregistre dans le Config :
        UTILS_Config.SetParametre("derniersFichiers", listeFichiers)

    def MAJmenuDerniersFichiers(self):
        """ Met à jour la liste des derniers fichiers dans le menu """
        # Suppression de la liste existante
        menuFichier = self.dictInfosMenu["menu_fichier"]["ctrl"]
        for index in range(ID_DERNIER_FICHIER, ID_DERNIER_FICHIER+10) :
            item = self.menu.FindItemById(index)
            if item == None : 
                break
            else:
                menuFichier.Remove(self.menu.FindItemById(index))


        # Ré-intégration des derniers fichiers ouverts :
        listeDerniersFichiers = self.userConfig["derniersFichiers"]
        if len(listeDerniersFichiers) > 0 : 
            index = 0
            for nomFichier in listeDerniersFichiers :
                # Version Reseau
                if "[RESEAU]" in nomFichier :
                    port, hote, user, mdp = nomFichier.split(";")
                    nomFichier = nomFichier[nomFichier.index(
                        "[RESEAU]"):] + " - %s" % hote
                item = wx.MenuItem(menuFichier, ID_DERNIER_FICHIER + index, "%d. %s" % (index+1, nomFichier), _("Ouvrir le fichier : '%s'") % nomFichier)
                menuFichier.Append(item)
                index += 1
            self.Bind(wx.EVT_MENU_RANGE, self.On_fichier_DerniersFichiers, id=ID_DERNIER_FICHIER, id2=ID_DERNIER_FICHIER + index)

    def OuvrirDernierFichier(self):
        # Chargement du dernier fichier chargé si assistant non affiché
        resultat = False
        if self.nomDernierFichier != "" :
            resultat = self.OuvrirFichier(self.nomDernierFichier)
        return resultat
                    
    def OuvrirFichier(self, nomFichier):
        """ Suite de la commande menu Ouvrir """
        self.SetStatusText(_("Ouverture d'un fichier en cours..."))

        # Vérifie que le fichier n'est pas déjà ouvert
        if self.userConfig["nomFichier"] == nomFichier :
            if "[RESEAU]" in nomFichier :
                nomFichier = nomFichier[nomFichier.index("[RESEAU]"):]
            dlg = wx.MessageDialog(self, _("Le fichier '") + nomFichier + _("' est déjà ouvert !"), _("Ouverture de fichier"), wx.OK | wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()
            self.SetStatusText(_("Le fichier '%s' est déjà ouvert.") % nomFichier)
            return False

        # Teste l'existence du fichier :
        self.isReseau = False
        if self.TesterUnFichier(nomFichier) == False :
            if "[RESEAU]" in nomFichier :
                nomFichier = nomFichier[nomFichier.index("[RESEAU]"):]
                self.isReseau = True
            self.SetStatusText(_("Impossible d'ouvrir le fichier '%s'.") % nomFichier)
            return False
        
        # Vérification du mot de passe
        listeUtilisateursFichier = self.GetListeUtilisateurs(nomFichier)
        if "[RESEAU]" in nomFichier :
            port, hote, user, mdp = nomFichier.split(";")
            nomFichierTmp = nomFichier[nomFichier.index("[RESEAU]"):] + " - %s" % hote
        else:
            nomFichierTmp = nomFichier
        if self.Identification(listeUtilisateursFichier, nomFichierTmp) == False :
            return False
        self.listeUtilisateurs = listeUtilisateursFichier
        
        # Applique le changement de fichier en cours
        ancienFichier = self.userConfig["nomFichier"]
        self.userConfig["nomFichier"] = nomFichier
        
        # Vérifie si la version du fichier est à jour
        if nomFichier != "" :
            if self.ValidationVersionFichier(nomFichier) == False :
                if "[RESEAU]" in nomFichier :
                    nomFichier = nomFichier[nomFichier.index("[RESEAU]"):]
                self.SetStatusText(_("Echec de l'ouverture du fichier '%s'.") % nomFichier)
                self.userConfig["nomFichier"] = ancienFichier
                return False

        # Met à jour l'affichage 
        self.MAJ()
        self.SetTitleFrame(nomFichier=nomFichier)
        if CUSTOMIZE.GetValeur("ephemeride", "actif", "1") == "1" :
            self.ctrl_ephemeride.Initialisation()
        
        # Récupération de la perspective chargée
        if self.perspective_active != None :
            self._mgr.LoadPerspective(self.perspectives[self.perspective_active]["perspective"])
            self.ForcerAffichagePanneau("ephemeride")
        else:
            self._mgr.LoadPerspective(self.perspective_defaut)

        # Met à jour la liste des derniers fichiers ouverts dans le CONFIG de la page
        self.MAJlisteDerniersFichiers(nomFichier) 

        # Active la commande Fermer du menu Fichier
        menuBar = self.GetMenuBar()
        self.dictInfosMenu["fermer_fichier"]["ctrl"].Enable(True)
        self.dictInfosMenu["fichier_informations"]["ctrl"].Enable(True)
        if "[RESEAU]" in nomFichier :
            self.dictInfosMenu["convertir_fichier_reseau"]["ctrl"].Enable(False) 
            self.dictInfosMenu["convertir_fichier_local"]["ctrl"].Enable(True) 
        else:
            self.dictInfosMenu["convertir_fichier_reseau"]["ctrl"].Enable(True) 
            self.dictInfosMenu["convertir_fichier_local"]["ctrl"].Enable(False) 
        
        # Met à jour le menu
        self.MAJmenuDerniersFichiers()

        # Sauvegarde du fichier de configuration
        self.SaveFichierConfig()
        
        # Active les items de la barre de menus
        self.ActiveBarreMenus(True) 
        
        # Confirmation de succès
        if "[RESEAU]" in nomFichier :
                nomFichier = nomFichier[nomFichier.index("[RESEAU]"):]
        self.SetStatusText(_("Le fichier '%s' a été ouvert avec succès.") % nomFichier)  
        
        # Mémorise dans l'historique l'ouverture du fichier
        try:
            UTILS_Historique.InsertActions([{"IDcategorie":1, "action":_("Ouverture du fichier %s") % nomFichier},])
        except:
            pass

        # Affiche les messages importants
        wx.CallLater(2000, self.AfficheMessagesOuverture)

        return True

    def AfficherServeurConnecthys(self):
        if UTILS_Config.GetParametre("client_synchro_portail_activation", defaut=False) == True and UTILS_Parametres.Parametres(mode="get", categorie="portail", nom="portail_activation", valeur=False) == True :

            if hasattr(self, "ctrl_serveur_portail") :
                self._mgr.GetPane("serveur_portail").Show(True)

            else :
                # Chargement du serveur
                self.ctrl_serveur_portail = CTRL_Portail_serveur.Panel(self)
                self._mgr.AddPane(self.ctrl_serveur_portail, aui.AuiPaneInfo().Name("serveur_portail").Caption(_("Connecthys")).
                                  Top().Layer(0).Row(3).Position(0).CloseButton(False).MaximizeButton(False).MinimizeButton(False).MinSize((-1, 90)).BestSize((-1, 90)) )

            # Lancement du serveur
            self._mgr.Update()
            self.ctrl_serveur_portail.MAJ()
            self.ctrl_serveur_portail.StartServeur()

        else :
            if hasattr(self, "ctrl_serveur_portail") :
                self._mgr.GetPane("serveur_portail").Show(False)
                self._mgr.Update()
                self.ctrl_serveur_portail.PauseServeur()

    def IsSynchroConnecthys(self):
        if hasattr(self, "ctrl_serveur_portail") :
            if self.ctrl_serveur_portail.HasSynchroEnCours() == True :
                import wx.lib.dialogs as dialogs
                dlg = dialogs.MultiMessageDialog(self, _("Une synchronisation Connecthys est en cours.\n\n Merci de patienter quelques instants..."), caption = _("Information"), msg2=None, style = wx.ICON_EXCLAMATION | wx.YES|wx.NO|wx.YES_DEFAULT, btnLabels={wx.ID_YES : _("Attendre (Conseillé)"), wx.ID_NO : _("Forcer la fermeture")})
                reponse = dlg.ShowModal()
                dlg.Destroy()
                if reponse != wx.ID_NO :
                    return True
        return False

    def TesterUnFichier(self, nomFichier):
        """ Fonction pour tester l'existence d'un fichier """
        if "[RESEAU]" in nomFichier :
            # Version RESEAU
            dictResultats = GestionDB.TestConnexionMySQL(typeTest='fichier', nomFichier="%s_DATA" % nomFichier)
            if dictResultats["connexion"][0] == False :
                # Connexion impossible au serveur MySQL
                erreur = dictResultats["connexion"][1]
                dlg = wx.MessageDialog(self, _("Il est impossible de se connecter au serveur MySQL.\n\nErreur : %s") % erreur, "Erreur d'ouverture de fichier", wx.OK | wx.ICON_ERROR)
                dlg.ShowModal()
                dlg.Destroy()
                return False
            if dictResultats["fichier"][0] == False :
                # Ouverture impossible du fichier MySQL demandé
                erreur = dictResultats["fichier"][1]
                dlg = wx.MessageDialog(self, _("La connexion avec le serveur MySQL fonctionne mais il est impossible d'ouvrir le fichier MySQL demandé.\n\nErreur : %s") % erreur, "Erreur d'ouverture de fichier", wx.OK | wx.ICON_ERROR)
                dlg.ShowModal()
                dlg.Destroy()
                return False
            
        else:
            # Test de validité du fichier SQLITE :
            fichier = UTILS_Fichiers.GetRepData(u"%s_DATA.dat" % nomFichier)
            test = os.path.isfile(fichier) 
            if test == False :
                dlg = wx.MessageDialog(self, _("Il est impossible d'ouvrir le fichier demandé !"), "Erreur d'ouverture de fichier", wx.OK | wx.ICON_ERROR)
                dlg.ShowModal()
                dlg.Destroy()
                return False
            else:
                return True

    def ConvertVersionTuple(self, txtVersion=""):
        """ Convertit un numéro de version texte en tuple """
        texteVersion = FonctionsPerso.ChiffresSeuls(txtVersion)
        tupleTemp = []
        for num in texteVersion.split(".") :
            tupleTemp.append(int(num))
        return tuple(tupleTemp)

    def ValidationVersionFichier(self, nomFichier):
        """ Vérifie que la version du fichier est à jour avec le logiciel """
        self.dictInfosMenu["upgrade_base"]["ctrl"].Enable(False)
        # Récupère les numéros de version
        versionLogiciel = self.ConvertVersionTuple(VERSION_APPLICATION)
        VERSION_FICHIER =  UTILS_Parametres.Parametres(mode="get", categorie="fichier", nom="version", valeur=VERSION_APPLICATION, nomFichier=nomFichier)
        versionFichier = self.ConvertVersionTuple(VERSION_FICHIER)
        resultat = True

        def EnregistreVersion():
            # Mémorisation de la nouvelle version du fichier
            UTILS_Parametres.Parametres(
                mode="set",
                categorie="fichier",
                nom="version",
                valeur=VERSION_APPLICATION,
                nomFichier=nomFichier)
            info = "Conversion %s -> %s reussie." % (
                VERSION_FICHIER,
                VERSION_APPLICATION)
            self.SetStatusText(info)
            print(info)

        def VersionTexte(versionTpl,nbItems=4):
            # retrourne une mise en texte du tuple version
            return str(versionTpl[:nbItems])[1:-1]

        message = "Le logiciel n'a pas convertit le fichier !\n\nAbandon du traitement"
        titre = "Abandon"
        style = wx.OK | wx.ICON_INFORMATION
        # Comparaison des versions par les tuples
        if versionFichier[:2] != versionLogiciel[:2]:
            # Changement majeur, MAJ base complète nécessaire
            self.dictInfosMenu["upgrade_modules"]["ctrl"].Enable(True)
            self.dictInfosMenu["upgrade_base"]["ctrl"].Enable(True)
            info = "Lancement de la conversion %s -> %s..."%(VERSION_FICHIER, VERSION_APPLICATION)
            self.SetStatusText(info)
            print(info)
            try:
                import UpgradeDB
                resultat = UpgradeDB.MAJ_TablesEtChamps(self)
                if resultat == True:
                    EnregistreVersion()
            except Exception as err:
                traceback.print_exc(file=sys.stdout)
                message = "Désolé, le problème suivant a été rencontré dans la mise à jour de la base de données : \n\n%s"% err
                titre = "Erreur"
                style = wx.OK | wx.ICON_ERROR
                resultat = False
        elif versionFichier < versionLogiciel:
            # Fait la conversion de la base par simple upgrade
            info = "Lancement de la conversion %s -> %s..." %(VERSION_FICHIER,VERSION_APPLICATION)
            self.SetStatusText(info)
            print(info)
            # Affiche d'une fenêtre d'attente
            try :
                messAttente = _("Mise à jour de la base de données en cours... Veuillez patienter...")
                attente = wx.BusyInfo(messAttente, None)
                import UpgradeDB
                DB = UpgradeDB.DB(nomFichier=nomFichier)
                resultat = DB.Upgrade(versionFichier)
                DB.Close()
                # Fermeture de la fenêtre d'attente
                del attente
                EnregistreVersion()
            except Exception as err:
                del attente
                traceback.print_exc(file=sys.stdout)
                message =  "Désolé, le problème suivant a été rencontré dans la mise à jour de la base de données : \n\n%s"% err
                titre = "Erreur"
                style = wx.OK | wx.ICON_ERROR
                resultat = False
        elif versionFichier[:3] > versionLogiciel[:3]:
            self.dictInfosMenu["upgrade_modules"]["ctrl"].Enable(True)
            message = "Votre station n'est pas à jour!\n\n"
            message += "Si vous n'avez pas fait la dernière MAJ '%s',\n"%VersionTexte(versionLogiciel,3)
            message += "Réinstallez le logiciel ou installez cette dernière version puis la nouvelle '%s'"%VersionTexte(versionFichier,3)
            titre = "Erreur"
            style = wx.OK | wx.ICON_EXCLAMATION
            resultat = False
        elif versionFichier > versionLogiciel:
            self.dictInfosMenu["upgrade_modules"]["ctrl"].Enable(True)
            message = "Votre station n'est pas à jour!\n\n"
            message += "installez la version '%s' ou travaillez en mode dégradé."%VERSION_APPLICATION
            titre = "Erreur"
            style = wx.OK | wx.ICON_EXCLAMATION
            resultat = False
        if resultat != True :
            dlg = wx.MessageDialog(self,message,titre,style=style)
            dlg.CenterOnParent()
            dlg.ShowModal()
            dlg.Destroy()
        return True
    
    def ActiveBarreMenus(self, etat=True):
        """ Active ou non des menus de la barre """
        for numMenu in range(1, 7):
            self.menu.EnableTop(numMenu, etat)
        self._mgr.GetPane("panel_recherche").Show(etat)

    def Identification(self, listeUtilisateurs=[], nomFichier=None):
        passmdp = CUSTOMIZE.GetValeur("utilisateur", "pass", "")
        if passmdp != "" :
            passmdpcrypt = SHA256.new(passmdp.encode('utf-8')).hexdigest()
            for dictTemp in listeUtilisateurs :
                if dictTemp["mdpcrypt"] == passmdpcrypt or dictTemp["mdp"] == passmdp : # or dictTemp["mdp"] == passmdp à retirer plus tard
                    self.ChargeUtilisateur(dictTemp)
                    return True
        # Permet de donner le focus à la fenetre de connection sur LXDE (Fonctionnait sans sur d'autres distributions)
        self.Raise()
        dlg = CTRL_Identification.Dialog(self, listeUtilisateurs=listeUtilisateurs, nomFichier=nomFichier)
        reponse = dlg.ShowModal() 
        dictUtilisateur = dlg.GetDictUtilisateur()
        dlg.Destroy()
        if reponse == wx.ID_OK:
            self.ChargeUtilisateur(dictUtilisateur)
            return True
        else:
            return False

    def GetListeUtilisateurs(self, nomFichier=""):
        """ Récupère la liste des utilisateurs dans la base """
        return UTILS_Utilisateurs.GetListeUtilisateurs(nomFichier) 
    
    def RechargeUtilisateur(self):
        """ A utiliser après un changement des droits par exemple """
        IDutilisateur = self.dictUtilisateur["IDutilisateur"]
        for dictTemp in self.listeUtilisateurs :
            if IDutilisateur == dictTemp["IDutilisateur"] :
                self.dictUtilisateur = dictTemp        
        self.ChargeUtilisateur(self.dictUtilisateur, afficheToaster=False)

    def ChargeUtilisateur(self, dictUtilisateur=None, IDutilisateur=None, afficheToaster=True):
        """Charge un utilisateur à partir de son dictUtilisateur OU de son IDutilisateur """
        # Modifie utilisateur en cours
        if dictUtilisateur != None :
            self.dictUtilisateur = dictUtilisateur
        else:
            for dictTemp in self.listeUtilisateurs :
                if IDutilisateur == dictTemp["IDutilisateur"] :
                    dictUtilisateur = dictTemp
                    self.dictUtilisateur = dictTemp
        # Modifie Barre outils
        if dictUtilisateur["image"] == None or dictUtilisateur["image"] == "Automatique" :
            if dictUtilisateur["sexe"] == "M" : 
                nomImage = "Homme"
            else:
                nomImage = "Femme"
        else :
            nomImage = dictUtilisateur["image"]
        # Affichage de l'image utilisateur dans la barre d'outils
        tb = self.dictBarresOutils["barre_utilisateur"]["ctrl"]
        tb.SetToolBitmap(ID_TB_UTILISATEUR, wx.Bitmap(Chemins.GetStaticPath("Images/Avatars/16x16/%s.png" % nomImage), wx.BITMAP_TYPE_PNG))
        tb.SetToolLabel(ID_TB_UTILISATEUR, "%s %s" % (dictUtilisateur["nom"], dictUtilisateur["prenom"]))
        tb.Refresh() 
        # Affiche le Toaster
        if afficheToaster == True and CUSTOMIZE.GetValeur("utilisateur", "pass", "") == "" :
            CTRL_Toaster.ToasterUtilisateur(self, prenom=dictUtilisateur["prenom"], nomImage=nomImage) 
    
    def AfficheMessagesOuverture(self):
        """ Affiche les messages à l'ouverture du fichier """
        listeMessages = self.ctrl_messages.GetMessages()
        for track in listeMessages :
            if track.rappel == 1 :
                texteToaster = track.texte
                if track.priorite == "HAUTE" : 
                    couleurFond="#FFA5A5"
                else:
                    couleurFond="#FDF095"
                self.AfficheToaster(titre=_("Message"), texte=texteToaster, couleurFond=couleurFond) 

    def AfficheToaster(self, titre=u"", texte=u"", taille=(200, 100), couleurFond="#F0FBED"):
        """ Affiche une boîte de dialogue temporaire """
        largeur, hauteur = taille
        tb = Toaster.ToasterBox(self, Toaster.TB_SIMPLE, Toaster.TB_DEFAULT_STYLE, Toaster.TB_ONTIME) # TB_CAPTION
        tb.SetTitle(titre)
        tb.SetPopupSize((largeur, hauteur))
        if 'phoenix' not in wx.PlatformInfo:
            largeurEcran, hauteurEcran = wx.ScreenDC().GetSizeTuple()
        else:
            largeurEcran, hauteurEcran = wx.ScreenDC().GetSize()
        tb.SetPopupPosition((largeurEcran-largeur-10, hauteurEcran-hauteur-50))
        tb.SetPopupPauseTime(2000)
        tb.SetPopupScrollSpeed(8)
        tb.SetPopupBackgroundColour(couleurFond)
        tb.SetPopupTextColour("#000000")
        tb.SetPopupText(texte)
        tb.Play()

    def zzRechercheMAJinternet(self):
        """ Recherche une mise à jour sur internet """
        # Récupère la version de l'application
        versionApplication = VERSION_APPLICATION
        # Récupère la version de la MAJ sur internet
        try :
            if "linux" in sys.platform :
                # Version Debian
                fichierVersions = urlopen('https://raw.githubusercontent.com/Noethys/Noethys/master/noethys/Versions.txt', timeout=5)
            else:
                # Version Windows
                fichierVersions = urlopen('http://www.noethys.com/fichiers/windows/phoenix/Versions.txt', timeout=5)
            texteNouveautes= fichierVersions.read()
            fichierVersions.close()
            pos_debut_numVersion =texteNouveautes.find("n")
            pos_fin_numVersion = texteNouveautes.find("(")
            versionMaj = texteNouveautes[pos_debut_numVersion+1:pos_fin_numVersion].strip()
        except :
            print("Recuperation du num de version de la MAJ sur internet impossible.")
            versionMaj = "0.0.0.0"
        # Compare les deux versions et renvois le résultat
        try :
            if self.ConvertVersionTuple(versionMaj) > self.ConvertVersionTuple(VERSION_APPLICATION) :
                self.versionMAJ = versionMaj
                return True
            else:
                return False
        except :
            return False

    def GetVersionAnnonce(self):
        if "annonce" in self.userConfig :
            versionAnnonce = self.userConfig["annonce"]
            if versionAnnonce != None :
                return tuple(versionAnnonce)

        return (0, 0, 0, 0)
        
    def Annonce(self):
        """ Création une annonce au premier démarrage du logiciel """
        nomFichier = sys.executable
        if nomFichier.endswith("python.exe") == False :
            versionAnnonce = self.GetVersionAnnonce()
            versionLogiciel = self.ConvertVersionTuple(VERSION_APPLICATION)
            if versionAnnonce < versionLogiciel :
                # Déplace les fichiers exemples vers le répertoire des fichiers de données
                try :
                    UTILS_Fichiers.DeplaceExemples()
                except Exception as err:
                    print("Erreur dans UTILS_Fichiers.DeplaceExemples :")
                    print((err,))
                # Affiche le message d'accueil
                from Dlg import DLG_Message_accueil
                dlg = DLG_Message_accueil.Dialog(self)
                dlg.ShowModal()
                dlg.Destroy()
                # Mémorise le numéro de version actuel
                self.userConfig["annonce"] = versionLogiciel
                return True
        return False
    
    def EstFichierExemple(self):
        """ Vérifie si c'est un fichier EXEMPLE qui est ouvert actuellement """
        if self.userConfig["nomFichier"] != None :
            if "EXEMPLE_" in self.userConfig["nomFichier"] :
                return True
        return False

    def zzProposeMAJ(self):
        """ Propose la MAJ immédiate """
        if self.MAJexiste == True :
            if self.versionMAJ != None :
                message = _("La version %s de Noethys est disponible.\n\nSouhaitez-vous télécharger cette mise à jour maintenant ?") % self.versionMAJ
            else :
                message = _("Une nouvelle version de Noethys est disponible.\n\nSouhaitez-vous télécharger cette mise à jour maintenant ?")
            dlg = wx.MessageDialog(self, message, _("Mise à jour disponible"), wx.YES_NO|wx.YES_DEFAULT|wx.ICON_INFORMATION)
            reponse = dlg.ShowModal()
            dlg.Destroy()
            if reponse == wx.ID_YES :
                self.On_outils_updater(None)
                return True
        return False
    
    def AnnonceTemoignages(self):
        # Se déclenche uniquement dans 40% des cas
        if random.randrange(1, 100) > 40 :
            return False
        
        # Vérifie si case Ne plus Afficher cochée ou non
        if UTILS_Parametres.Parametres(mode="get", categorie="ne_plus_afficher", nom="temoignages", valeur=False) == True :
            return False
        chemin = Chemins.GetStaticPath("Images")
        texte = """
<CENTER><IMG SRC="%s/32x32/Information.png">
<BR><BR>
<FONT SIZE=2>
<B>Appel à témoignages</B>
<BR><BR>
Vous utilisez et appréciez Noethys ? 
<BR><BR>
Participez à sa promotion en postant un témoignage sur le site internet de Noethys. L'occasion de décrire votre utilisation du logiciel et de donner ainsi envie aux lecteurs intéressés de s'y essayer.
<BR><BR>
Merci pour votre participation !
<BR><BR>
<A HREF="http://www.noethys.com/index.php/presentation/2013-09-08-15-48-17/temoignages">Cliquez ici pour accéder aux témoignages</A>
</FONT>
</CENTER>
"""%chemin
        dlg = DLG_Message_html.Dialog(self, texte=texte, titre=_("Information"), nePlusAfficher=True)
        dlg.ShowModal()
        nePlusAfficher = dlg.GetEtatNePlusAfficher()
        dlg.Destroy()
        if nePlusAfficher == True :
            UTILS_Parametres.Parametres(mode="set", categorie="ne_plus_afficher", nom="temoignages", valeur=nePlusAfficher)
        return True

    def AnnonceFinancement(self):
        # Vérifie si identifiant saisi et valide
        identifiant = UTILS_Config.GetParametre("enregistrement_identifiant", defaut=None)
        if identifiant != None :
            # Vérifie nbre jours restants
            code = UTILS_Config.GetParametre("enregistrement_code", defaut=None)
            validite = DLG_Enregistrement.GetValidite(identifiant, code)
            if validite != False :
                date_fin_validite, nbreJoursRestants = validite
                dateDernierRappel = UTILS_Config.GetParametre("enregistrement_dernier_rappel", defaut=None)
                
                if nbreJoursRestants < 0 :
                    # Licence périmée
                    if dateDernierRappel != None :
                        UTILS_Config.SetParametre("enregistrement_dernier_rappel", None)
                    
                elif nbreJoursRestants <= 30 :
                    # Licence bientôt périmée
                    UTILS_Config.SetParametre("enregistrement_dernier_rappel", datetime.date.today())
                    if dateDernierRappel != None :
                        nbreJoursDepuisRappel =  (dateDernierRappel - datetime.date.today()).days
                    else :
                        nbreJoursDepuisRappel = None
                    if nbreJoursDepuisRappel == None or nbreJoursDepuisRappel >= 10 :
                        from Dlg import DLG_Messagebox
                        image = wx.Bitmap(Chemins.GetStaticPath("Images/32x32/Cle.png"), wx.BITMAP_TYPE_ANY)
                        introduction = _("Votre licence d'accès au manuel de référence en ligne se termine dans %d jours. \n\nSi vous le souhaitez, vous pouvez continuer à bénéficier de cet accès et prolonger votre soutien financier au projet Noethys en renouvelant votre abonnement Classic ou Premium.") % nbreJoursRestants
                        dlg = DLG_Messagebox.Dialog(self, titre=_("Enregistrement"),
                                                    introduction=introduction, detail=None,
                                                    icone=image, boutons=[(u"Renouveler mon abonnement"), _("Fermer")], defaut=0)
                        reponse = dlg.ShowModal()
                        dlg.Destroy()
                        if reponse == 0:
                            FonctionsPerso.LanceFichierExterne("https://noethys.com/public/bon_commande_documentation.pdf")
                        return True
                else :
                    # Licence valide
                    if dateDernierRappel != None :
                        UTILS_Config.SetParametre("enregistrement_dernier_rappel", None)

        return False

    def AutodetectionAnomalies(self):
        """ Auto-détection d'anomalies """
        # Se déclenche uniquement dans 15% des cas
        if random.randrange(1, 100) > 15 :
            return False

        from Dlg import DLG_Depannage
        resultat = DLG_Depannage.Autodetection(self)
        if resultat == None :
            return False
        else :
            return True

    def Autodeconnect(self, event=None):
        """ Actionne l'Autodeconnect si inactivité durant un laps de temps """
        #print "Timer autodeconnect...  ", time.time()
        
        # Vérifie que la souris a bougé
        position_souris = wx.GetMousePosition()
        if self.autodeconnect_position != position_souris :
            self.autodeconnect_position = position_souris
            return False
        self.autodeconnect_position = position_souris
        
        # Vérifie que un fichier est bien ouvert
        if self.userConfig["nomFichier"] == "" :
            return False
                
        # Vérifie que aucune dialog ouverte
        if wx.GetActiveWindow() != None :
            if wx.GetActiveWindow().GetName() != "general" :
                return False
        else :
            for ctrl in wx.GetApp().GetTopWindow().GetChildren() :
                if "Dialog" in str(ctrl) :
                    return False
        
        # Demande le mot de passe de l'utilisateur
        nomFichier = self.nomDernierFichier
        listeUtilisateursFichier = self.GetListeUtilisateurs(nomFichier)
        if "[RESEAU]" in nomFichier :
            nomFichierTmp = nomFichier[nomFichier.index("[RESEAU]"):]
        else:
            nomFichierTmp = nomFichier
        if self.Identification(listeUtilisateursFichier, nomFichierTmp) == False :
            # Sinon ferme le fichier
            self.Fermer(sauvegarde_auto=False)
            return False
        self.listeUtilisateurs = listeUtilisateursFichier

# -----------------------------------------------------------------------------

class MyApp(wx.App):
    # def InitLocale(self):
    #     self.ResetLocale()

    def OnInit(self):
        heure_debut = time.time()

        # Réinitialisation du fichier des parametres en conservant la touche ALT ou CTRL enfoncée
        if wx.GetKeyState(307) == True or wx.GetKeyState(308) == True :
            dlg = wx.MessageDialog(None, _("Souhaitez-vous vraiment réinitialiser Noethys ?"), _("Réinitialisation"), wx.YES_NO|wx.NO_DEFAULT|wx.CANCEL|wx.ICON_QUESTION)
            if dlg.ShowModal() == wx.ID_YES :
                UTILS_Config.SupprimerFichier()
            dlg.Destroy()

        # Lit les paramètres de l'interface
        theme = CUSTOMIZE.GetValeur("interface", "theme", "Vert")

        # AdvancedSplashScreen
        if CUSTOMIZE.GetValeur("utilisateur", "pass", "") == "" :
            nom_fichier_splash = "Logo_splash_2019.png"
            bmp = wx.Bitmap(Chemins.GetStaticPath("Images/Interface/%s/%s" % (theme, nom_fichier_splash)), wx.BITMAP_TYPE_PNG)
            frame = AS.AdvancedSplash(None, bitmap=bmp, timeout=500, agwStyle=AS.AS_TIMEOUT | AS.AS_CENTER_ON_SCREEN)
            anneeActuelle = str(datetime.date.today().year)
            frame.SetText(u"Copyright © 2010-%s Ivan LUCAS" % anneeActuelle[2:])
            frame.SetTextFont(wx.Font(8, wx.SWISS, wx.NORMAL, wx.NORMAL, False))
            frame.SetTextPosition((425, 212))
            couleur_texte = "WHITE" #UTILS_Interface.GetValeur("couleur_claire", wx.Colour(255, 255, 255))
            frame.SetTextColour(couleur_texte)
            frame.Refresh()
            frame.Update()

        # Création de la frame principale
        frame = MainFrame(None)
        self.SetTopWindow(frame)
        frame.Initialisation()
        frame.Show()

        # Affiche une annonce si c'est un premier démarrage ou après une mise à jour
        #etat_annonce = frame.Annonce()
                
        # Charge le fichier Exemple si l'utilisateur le souhaite
        etat_exemple = frame.ChargeFichierExemple()
        
        # Charge le dernier fichier
        fichierOuvert = frame.OuvrirDernierFichier()

        # Active la page du tableau des effectifs après connexion et non avant comme dans MainFrame.OnInit
        #if ("page_ctrl_effectifs" in frame.userConfig) == True :
        #    frame.ctrl_remplissage.SetPageActive(frame.userConfig["page_ctrl_effectifs"])

        print("Temps de chargement ouverture de Noethys = ", time.time() - heure_debut)
        return True

class Redirect(object):
    def __init__(self, nomJournal=""):
        self.filename = open(nomJournal, "a")

    def write(self, text):
        if self.filename.closed:
            pass
        else:
            self.filename.write(text)
            self.filename.flush()

def main():
    # Vérifie l'existence des répertoires dans le répertoire Utilisateur
    for rep in ("Temp", "Updates", "Sync", "Lang", "Extensions") :
        rep = UTILS_Fichiers.GetRepUtilisateur(rep)
        if os.path.isdir(rep) == False :
            os.makedirs(rep)

    # Vérifie si des fichiers du répertoire Data sont à déplacer vers le répertoire Utilisateur
    UTILS_Fichiers.DeplaceFichiers()

    # Initialisation du fichier de customisation
    global CUSTOMIZE
    CUSTOMIZE = UTILS_Customize.Customize()

    # Crash report
    UTILS_Rapport_bugs.Activer_rapport_erreurs(version=VERSION_APPLICATION)

    # Log
    nomJournal = UTILS_Fichiers.GetRepUtilisateur(CUSTOMIZE.GetValeur("journal", "nom", "journal.log"))

    # Supprime le journal.log si supérieur à 1 Mo
    if os.path.isfile(nomJournal) :
        taille = os.path.getsize(nomJournal)
        if taille > 1000000 :
            os.remove(nomJournal)

    # Redirection vers un fichier
    nomFichier = sys.executable
    print(nomFichier)
    journal = CUSTOMIZE.GetValeur("journal", "actif", "1")
    nolog = os.path.isfile("nolog.txt")
    #if nomFichier.endswith("python.exe") == False and journal != "0" and nolog == False :
    if journal != "0" and nolog == False :
        sys.stdout = Redirect(nomJournal)

    # Lancement de l'application
    app = MyApp(redirect=False)
    app.MainLoop()

if __name__ == "__main__":
    main()