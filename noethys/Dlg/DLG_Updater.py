#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activit�s
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-16 Ivan LUCAS
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------


import Chemins
from Utils import UTILS_Adaptations
from Utils.UTILS_Traduction import _
import wx
from Ctrl import CTRL_Bouton_image
import FonctionsPerso
import sys 
from time import sleep 
from threading import Thread 
from six.moves.urllib.request import Request, urlopen, urlretrieve
import os
import six
import zipfile
import glob, codecs

from Ctrl import CTRL_Bandeau
from Utils import UTILS_Fichiers



#------------------------------------------------------------------------------------------
# Pour les tests, mettre sur True
DEBUG = False
#------------------------------------------------------------------------------------------


def AffichetailleFichier(fichierURL):
    tailleFichier = 0
    try :
        fichier = urlopen(fichierURL)
        if six.PY3:
            tailleFichier = fichier.headers['Content-Length']
        else:
            infoFichier = (fichier.info().getheaders('Content-Length'))
            if len(infoFichier) > 0 :
                tailleFichier = infoFichier[0]
    except IOError :
        tailleFichier = 0
    return tailleFichier

def AffichePourcentage(stade, taille):
    pourcent = int(stade*100/taille)
    pourcent = str(pourcent) + " %"
    return pourcent
    
def FormateTailleFichier(taille):
    if 0 <= taille <1000 :
        texte = str(taille) + " octets"
    elif 1000 <= taille < 1000000 :
        texte = str(taille//1000) + " Ko"
    else :
        texte = str(taille//1000000) + " Mo"
    return texte


    
##def zipdirectory(journal, filezip, pathzip):
##    """ Sauvegarde globale """
##    lenpathparent = len(pathzip)+1
##    
##    def _zipdirectory(zfile, path):
##        for i in glob.glob(path+'/*'):
##            if os.path.isdir(i): 
##                if i.endswith("Updates") == False : # On sauvegarde pas le dossier Updates
##                    _zipdirectory(zfile, i )
##            else:
##                nomFichier = os.path.split(i)[1]
##                journal.WriteText("..." + nomFichier + "\n")
##                zfile.write(i, i[lenpathparent:]) 
##    zfile = zipfile.ZipFile(filezip,'w',compression=zipfile.ZIP_DEFLATED)
##    _zipdirectory(zfile, pathzip)
##    zfile.close()
    


class zipdirectory(Thread):
    def __init__(self, parent, journal, filezip, pathzip):
        Thread.__init__(self)
        self.parent = parent
        self.journal = journal
        self.filezip = filezip
        self.pathzip = pathzip
        self.lenpathparent = len(pathzip)+1
        self.Terminated = False
        self.nbreFichiers = 0
        
    def run(self):
        def _zipdirectory(zfile, path):
            for i in glob.glob(path+'/*'):
                if os.path.isdir(i): 
                    if i.endswith("Updates") == False : # On sauvegarde pas le dossier Updates
                        _zipdirectory(zfile, i )
                else:
                    nomFichier = os.path.split(i)[1]
                    if "linux" not in sys.platform :
                        self.journal.WriteText("..." + nomFichier + "\n")
                    zfile.write(i, i[self.lenpathparent:]) 
                    self.nbreFichiers += 1
        
        zfile = zipfile.ZipFile(self.filezip,'w',compression=zipfile.ZIP_DEFLATED)
        _zipdirectory(zfile, self.pathzip)
        zfile.close()
        self.journal.WriteText(str(self.nbreFichiers) + _(" fichiers ont �t� sauvegard�s avec succ�s."))
        
        # Lance la suite de l'installation
        self.parent._Installation()
        
    def stop(self):
        self.Terminated = True    
    



class Abort(Exception): 
    pass 

class Download(Thread): 

    def __init__(self, parent, fichierURL, fichierDest, progressBar, zoneTexte): 
        Thread.__init__(self) 
        self.parent = parent
        self.succes = False
        self.fichierURL = fichierURL 
        self.stop = False 
        self.fichierDest = fichierDest
        self.progressBar = progressBar
        self.zoneTexte = zoneTexte
        self.frameParente = self.parent.GetParent()
        #print "Telechargement de la nouvelle version : etape 4"

    def _hook(self, nb_blocs, taille_bloc, taille_fichier):
        #print "Telecharge=", nb_blocs*taille_bloc, _("/ total="), taille_fichier
        if nb_blocs*taille_bloc >= taille_fichier:
            #print "Le telechargement est termine !"
            self.succes = True
            self.zoneTexte.SetLabel(_("Le t�l�chargement est termin�. Veuillez patienter..."))
            self.frameParente.SetTitle(_("Mises � jour Internet"))
            raise Abort
        if self.stop: 
            raise Abort
        count = int(nb_blocs*taille_bloc)
        self.progressBar.SetValue(count+1)
        #print "Telechargement de la nouvelle version : etape 6"
        if nb_blocs % 5 == 0 :
            if "linux" not in sys.platform :
                texteInfo = _("T�l�chargement en cours...  ") + FormateTailleFichier(nb_blocs*taille_bloc)+" / "+FormateTailleFichier(taille_fichier)
                if texteInfo != self.zoneTexte.GetLabel() :
                    self.zoneTexte.SetLabel(texteInfo)
                self.frameParente.SetTitle(AffichePourcentage(nb_blocs*taille_bloc, taille_fichier) + _(" | T�l�chargement d'une mise � jour"))

    def run(self): 
        #print "Telechargement de la nouvelle version : etape 5"
        try: 
            if "linux" in sys.platform :
                self.zoneTexte.SetLabel(_("T�l�chargement en cours..."))
            urlretrieve(self.fichierURL, self.fichierDest, self._hook)
        except Abort as KeyBoardInterrupt: 
            #print 'Aborted ici !' 
            if self.succes == True :
                # T�l�chargement r�ussi
                self.parent.Suite(succes=True)
            else:
                # T�l�chargement non complet
                self.parent.Suite(succes=False)
        except: 
            self.stop = True 
            raise 

    def abort(self): 
        self.stop = True
        
        
        
        
# ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# PAGE RECHERCHE DE MAJ INTERNET
# ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

class Page_recherche(wx.Panel):
    def __init__(self, parent, ID=-1):
        wx.Panel.__init__(self, parent, ID, name="page_recherche", style=wx.TAB_TRAVERSAL)
        self.parent = parent
        
        # Cr�ation des widgets
        texteIntro = _("Cliquez sur le bouton 'Rechercher' pour lancer la recherche.")
        self.label_introduction = wx.StaticText(self, -1, texteIntro) #FonctionsPerso.StaticWrapText(self, -1, texteIntro)
        self.gauge = wx.Gauge(self, -1)
        
        # R�glages pour la gauge
        self.count = 0
        self.Bind(wx.EVT_TIMER, self.TimerHandler)
        self.timer = wx.Timer(self)
                
        # Boutons
        self.bouton_aide = CTRL_Bouton_image.CTRL(self, texte=_("Aide"), cheminImage="Images/32x32/Aide.png")
        self.bouton_ok = CTRL_Bouton_image.CTRL(self, texte=_("Rechercher"), cheminImage="Images/32x32/Loupe.png")
        self.bouton_annuler = CTRL_Bouton_image.CTRL(self, texte=_("Annuler"), cheminImage="Images/32x32/Annuler.png")
        
        self.__set_properties()
        self.__do_layout()
        
        self.Bind(wx.EVT_BUTTON, self.Onbouton_aide, self.bouton_aide)
        self.Bind(wx.EVT_BUTTON, self.Onbouton_ok, self.bouton_ok)
        self.Bind(wx.EVT_BUTTON, self.Onbouton_annuler, self.bouton_annuler)

    def __del__(self):
        self.timer.Stop()

    def TimerHandler(self, event):
        self.count = self.count + 1
        if self.count >= 50:
            self.count = 0
        self.gauge.Pulse()
        
    def __set_properties(self):
        self.bouton_aide.SetToolTip(wx.ToolTip(_("Cliquez ici pour obtenir de l'aide")))
        self.bouton_ok.SetToolTip(wx.ToolTip(_("Cliquez ici pour valider")))
        self.bouton_annuler.SetToolTip(wx.ToolTip(_("Cliquez pour annuler et fermer")))

    def __do_layout(self):        
        # Sizer Boutons
        grid_sizer_boutons = wx.FlexGridSizer(rows=1, cols=6, vgap=10, hgap=10)
        grid_sizer_boutons.Add(self.bouton_aide, 0, 0, 0)
        grid_sizer_boutons.Add((20, 20), 0, wx.EXPAND, 0)
        grid_sizer_boutons.Add(self.bouton_ok, 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_annuler, 0, 0, 0)
        grid_sizer_boutons.AddGrowableCol(1)
        # Sizer principal
        grid_sizer_base = wx.FlexGridSizer(rows=5, cols=1, vgap=0, hgap=0)
        grid_sizer_base.Add(self.label_introduction, 1, wx.ALL|wx.EXPAND, 10)
        grid_sizer_base.Add(self.gauge, 1, wx.ALL|wx.EXPAND, 10)
        grid_sizer_base.Add((5, 5), 1, wx.ALL|wx.EXPAND, 10)
        grid_sizer_base.Add(grid_sizer_boutons, 1, wx.ALL|wx.EXPAND, 10)
        grid_sizer_base.AddGrowableRow(2)
        grid_sizer_base.AddGrowableCol(0)       
        self.SetSizer(grid_sizer_base)
        self.Layout()
        
    def Onbouton_aide(self, event):
        self.parent.Aide()
                    
    def Onbouton_annuler(self, event):
        self.parent.Fermer()
        
    def Onbouton_ok(self, event):
        self.Recherche()

    def Activation(self):
        if self.parent.afficher_page_recherche == False :
            self.Recherche()
        
    def GetVersionLogiciel(self):
        """ Recherche du num�ro de version du logiciel """
        fichierVersion = codecs.open(Chemins.GetMainPath("Versions.txt"), encoding='utf-8', mode='r')
        txtVersion = fichierVersion.readlines()[0]
        fichierVersion.close() 
        pos_debut_numVersion = txtVersion.find("n")
        pos_fin_numVersion = txtVersion.find("(")
        numVersion = txtVersion[pos_debut_numVersion+1:pos_fin_numVersion].strip()
        return numVersion

    def ConvertVersionTuple(self, texteVersion=""):
        """ Convertit un num�ro de version texte en tuple """
        tupleTemp = []
        for num in texteVersion.split(".") :
            tupleTemp.append(int(num))
        return tuple(tupleTemp)

    def Recherche(self):
        """ Recherche internet """
        texteIntro = _("Recherche d'une mise � jour internet en cours...")
        self.label_introduction.SetLabel(texteIntro)
        
        # Active la gauge
        self.timer.Start(20)
        
        # Recherche si le fichier de versions est pr�sent sur internet
        try :
            if "linux" in sys.platform :
                # Version Debian
                fichierVersions = urlopen('https://raw.githubusercontent.com/Noethys/Noethys/master/noethys/Versions.txt', timeout=10)
            else:
                # Version Windows
                if six.PY2:
                    fichierVersions = urlopen('http://www.noethys.com/fichiers/windows/Versions.txt', timeout=10)
                else:
                    fichierVersions = urlopen('http://www.noethys.com/fichiers/windows/phoenix/Versions.txt', timeout=10)
            self.texteNouveautes= fichierVersions.read()
            fichierVersions.close()
        except :
            self.Suite(etat="erreur") 
            return

        # Recherche du num�ro de version
        if six.PY3:
            self.texteNouveautes = self.texteNouveautes.decode("iso-8859-15")
        pos_debut_numVersion = self.texteNouveautes.find("n")
        pos_fin_numVersion = self.texteNouveautes.find("(")
        self.versionData = self.texteNouveautes[pos_debut_numVersion+1:pos_fin_numVersion].strip()
        
        # Si la mise � jour n'est pas n�cessaire :
        versionLogiciel = self.ConvertVersionTuple(self.GetVersionLogiciel())
        versionInternet = self.ConvertVersionTuple(self.versionData)
        
##        print "versionLogiciel=", versionLogiciel, " | versionInternet=", versionInternet
        if versionInternet <= versionLogiciel and DEBUG == False :
            self.Suite(etat="aucune")
            return

        # Recherche la taille du fichier � t�l�charger
        taille = int(AffichetailleFichier(self.parent.fichierURL))
        self.tailleFichier = FormateTailleFichier(taille)
        self.parent.tailleFichier = taille
        if self.tailleFichier == 0 :
            self.Suite(etat="erreur")
        
        # Si le fichier est bien trouv�, on passe � la suite...
        self.Suite(etat="trouvee")
        
        
    def Suite(self, etat):
        """ Apr�s la recherche passe � la suite """
        # Recherche termin�e
        if etat == "erreur" :
            # Probl�me de recherche internet
            self.label_introduction.SetLabel(_("Connexion au serveur de mise � jour impossible."))
            self.timer.Stop()
            self.Layout()
        if etat == "aucune" :
            # Aucune mise � jour n'a �t� trouv�e
            self.label_introduction.SetLabel(_("Vous disposez d�j� de la derni�re version du logiciel."))
            self.timer.Stop()
            self.bouton_ok.Show(True)
            self.Layout()
        if etat == "trouvee" :
            # Une mise � jour a �t� trouv�e !
            self.parent.versionData = self.versionData
            self.parent.fichierDest = UTILS_Fichiers.GetRepUpdates(fichier=self.parent.versionData)
            if sys.platform.startswith("win") : self.parent.fichierDest = self.parent.fichierDest.replace("/", "\\")
            # V�rifie qu'elle n'a pas d�j� �t� t�l�charg�e sur le disque dur
            fichierAverifier = self.parent.fichierDest+ "/" + self.parent.nomFichier
            if sys.platform.startswith("win") : fichierAverifier = fichierAverifier.replace("/", "\\")
            if os.path.isfile(fichierAverifier) == True :
                tailleFichierAverifier = os.path.getsize(fichierAverifier)  
                tailleFichierOrigin = self.parent.tailleFichier
                if tailleFichierAverifier == tailleFichierOrigin :
                    # Ok le fichier existe bien d�j�
                    texteIntro1 = _("La mise � jour ") + self.versionData + _(" a d�j� �t� t�l�charg�e pr�c�demment.")
                    self.parent.GetPage("page_fin_telechargement").label_introduction1.SetLabel(texteIntro1)
                    self.parent.Active_page("page_fin_telechargement")
            else:
                # Sinon, on la t�l�charge...
                texteIntro1 = _("La version ") + self.versionData + " de Noethys est disponible (" + self.tailleFichier + ")."
                self.parent.GetPage("page_disponible").label_introduction1.SetLabel(texteIntro1)
                texteNouveautes = self.texteNouveautes
                if six.PY2:
                    texteNouveautes = texteNouveautes.decode("iso-8859-15")
                self.parent.GetPage("page_disponible").textCtrl_nouveautes.SetValue(texteNouveautes)
                self.parent.Active_page("page_disponible")
              

# ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# PAGE MAJ DISPONIBLE
# ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

class Page_disponible(wx.Panel):
    def __init__(self, parent, ID=-1):
        wx.Panel.__init__(self, parent, ID, name="page_disponible", style=wx.TAB_TRAVERSAL)
        self.parent = parent
        
        # Cr�ation des widgets
        texteIntro1 = ""
        self.label_introduction1 = wx.StaticText(self, -1, texteIntro1) # FonctionsPerso.StaticWrapText(self, -1, texteIntro1)
        texteIntro2 = _("Souhaitez-vous la t�l�charger maintenant ?")
        self.label_introduction2 = wx.StaticText(self, -1, texteIntro2) # FonctionsPerso.StaticWrapText(self, -1, texteIntro2)
        self.textCtrl_nouveautes = wx.TextCtrl(self, -1,"", size=(-1, 50), style=wx.TE_MULTILINE)
        
        # Boutons
        self.bouton_aide = CTRL_Bouton_image.CTRL(self, texte=_("Aide"), cheminImage="Images/32x32/Aide.png")
        self.bouton_ok = CTRL_Bouton_image.CTRL(self, texte=_("T�l�charger"), cheminImage="Images/32x32/Telecharger.png")
        self.bouton_annuler = CTRL_Bouton_image.CTRL(self, texte=_("Annuler"), cheminImage="Images/32x32/Annuler.png")
        
        self.__set_properties()
        self.__do_layout()
        
        self.Bind(wx.EVT_BUTTON, self.Onbouton_aide, self.bouton_aide)
        self.Bind(wx.EVT_BUTTON, self.Onbouton_ok, self.bouton_ok)
        self.Bind(wx.EVT_BUTTON, self.Onbouton_annuler, self.bouton_annuler)

    def __set_properties(self):
        self.bouton_aide.SetToolTip(wx.ToolTip(_("Cliquez ici pour obtenir de l'aide")))
        self.bouton_ok.SetToolTip(wx.ToolTip(_("Cliquez ici pour valider")))
        self.bouton_annuler.SetToolTip(wx.ToolTip(_("Cliquez pour annuler et fermer")))

    def __do_layout(self):        
        # Sizer Boutons
        grid_sizer_boutons = wx.FlexGridSizer(rows=1, cols=6, vgap=10, hgap=10)
        grid_sizer_boutons.Add(self.bouton_aide, 0, 0, 0)
        grid_sizer_boutons.Add((20, 20), 0, wx.EXPAND, 0)
        grid_sizer_boutons.Add(self.bouton_ok, 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_annuler, 0, 0, 0)
        grid_sizer_boutons.AddGrowableCol(1)
        # Sizer principal
        grid_sizer_base = wx.FlexGridSizer(rows=5, cols=1, vgap=0, hgap=0)
        grid_sizer_base.Add(self.label_introduction1, 1, wx.ALL|wx.EXPAND, 10)
        grid_sizer_base.Add(self.label_introduction2, 1, wx.ALL|wx.EXPAND, 10)
        grid_sizer_base.Add(self.textCtrl_nouveautes, 1, wx.TOP|wx.LEFT|wx.RIGHT|wx.EXPAND, 10)
        grid_sizer_base.Add(grid_sizer_boutons, 1, wx.ALL|wx.EXPAND, 10)
        grid_sizer_base.AddGrowableRow(2)
        grid_sizer_base.AddGrowableCol(0)       
        self.SetSizer(grid_sizer_base)
        self.Layout()
        self.grid_sizer_base = grid_sizer_base
        
    def Onbouton_aide(self, event):
        self.parent.Aide()
                    
    def Onbouton_annuler(self, event):
        # Fermeture
        #print "annuler"
        self.parent.Fermer()
        
    def Onbouton_ok(self, event):
        # T�l�charger
        self.parent.Active_page("page_telechargement")

    def Activation(self):
        # Pour contrer bug de Layout
        self.SetSize((500, 700))
        
        
        
# ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# PAGE TELECHARGEMENT
# ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

class Page_telechargement(wx.Panel):
    def __init__(self, parent, ID=-1):
        wx.Panel.__init__(self, parent, ID, name="page_telechargement", style=wx.TAB_TRAVERSAL)
        self.parent = parent
        
        # Cr�ation des widgets
        texteIntro = _("Le t�l�chargement va commencer dans quelques instants...")
        self.label_introduction = wx.StaticText(self, -1, texteIntro) # FonctionsPerso.StaticWrapText(self, -1, texteIntro)
        self.gauge = wx.Gauge(self, -1)
        
        # Boutons
        self.bouton_aide = CTRL_Bouton_image.CTRL(self, texte=_("Aide"), cheminImage="Images/32x32/Aide.png")
        self.bouton_ok = CTRL_Bouton_image.CTRL(self, texte=_("T�l�charger"), cheminImage="Images/32x32/Telecharger.png")
        self.bouton_annuler = CTRL_Bouton_image.CTRL(self, texte=_("Annuler"), cheminImage="Images/32x32/Annuler.png")
        self.bouton_ok.Show(False)
        
        self.__set_properties()
        self.__do_layout()
        
        self.Bind(wx.EVT_BUTTON, self.Onbouton_aide, self.bouton_aide)
        self.Bind(wx.EVT_BUTTON, self.Onbouton_ok, self.bouton_ok)
        self.Bind(wx.EVT_BUTTON, self.Onbouton_annuler, self.bouton_annuler)

    def __set_properties(self):
        self.bouton_aide.SetToolTip(wx.ToolTip(_("Cliquez ici pour obtenir de l'aide")))
        self.bouton_ok.SetToolTip(wx.ToolTip(_("Cliquez ici pour lancer le t�l�chargement")))
        self.bouton_annuler.SetToolTip(wx.ToolTip(_("Cliquez pour annuler et fermer")))

    def __do_layout(self):        
        # Sizer Boutons
        grid_sizer_boutons = wx.FlexGridSizer(rows=1, cols=6, vgap=10, hgap=10)
        grid_sizer_boutons.Add(self.bouton_aide, 0, 0, 0)
        grid_sizer_boutons.Add((20, 20), 0, wx.EXPAND, 0)
        grid_sizer_boutons.Add(self.bouton_ok, 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_annuler, 0, 0, 0)
        grid_sizer_boutons.AddGrowableCol(1)
        # Sizer principal
        grid_sizer_base = wx.FlexGridSizer(rows=5, cols=1, vgap=0, hgap=0)
        grid_sizer_base.Add(self.label_introduction, 1, wx.ALL|wx.EXPAND, 10)
        grid_sizer_base.Add(self.gauge, 1, wx.ALL|wx.EXPAND, 10)
        grid_sizer_base.Add((5, 5), 1, wx.ALL|wx.EXPAND, 10)
        grid_sizer_base.Add(grid_sizer_boutons, 1, wx.ALL|wx.EXPAND, 10)
        grid_sizer_base.AddGrowableRow(2)
        grid_sizer_base.AddGrowableCol(0)       
        self.SetSizer(grid_sizer_base)
        self.Layout()
        
    def Onbouton_aide(self, event):
        self.parent.Aide()
                    
    def Onbouton_annuler(self, event):
        self.Arreter_telechargement()
        
    def Onbouton_ok(self, event):
        self.Lancer_telechargement()

    def Activation(self):
        # Cr�e une petite attente avant le d�but du t�l�chargement
        self.count = 0
        self.Bind(wx.EVT_TIMER, self.TimerHandler)
        self.timer = wx.Timer(self)
        self.timer.Start(1)

    def __del__(self):
        try:
            self.timer.Stop()
        except:
            pass

    def TimerHandler(self, event):
        self.count = self.count + 1
        if self.count == 10 :
            self.timer.Stop()
            # Lance le t�l�chargement
            #print "Telechargement de la nouvelle version : etape 1"
            self.Lancer_telechargement()
            
    def Suite(self, succes):
        """ Apr�s le t�l�chargement passe � la suite """
        # V�rifie que le fichier est bien entier :
        tailleFichierDest = os.path.getsize(self.parent.fichierDest+ "/" + self.parent.nomFichier)  
        tailleFichierOrigin = self.parent.tailleFichier
        if tailleFichierDest != tailleFichierOrigin :
            succes = False
        
        # T�l�chargement termin�
        if succes == True :
            # On attribue un ID unique qui permet de compter les t�l�chargements
            IDfichier = FonctionsPerso.GetIDfichier()
            if len(IDfichier) > 7 :
                id = IDfichier[-7:]
            else :
                id = ""
            # On envoie le signal pour le compteur de t�l�chargement
            if "linux" in sys.platform :
                typeFichier = "linux"
            else:
                typeFichier = "windows"
            try :
                versionData = self.parent.versionData
                fichier = "%s-%s-%s" % (typeFichier, versionData, id)
                req = Request("http://www.noethys.com/fichiers/telechargement.cgi?fichier=%s" % fichier)
                handle = urlopen(req)
            except :
                pass
            # Si t�l�chargement complet, on passe � la page de fin de t�l�chargement
            sleep(1) # Attend 2 secondes avant de continuer
            self.parent.Active_page("page_fin_telechargement")
        else:
            # Vidage du rep Updates
            FonctionsPerso.VideRepertoireUpdates(forcer=True)
            # Le t�l�chargement n'est pas complet, demande � l'utilisateur de recommencer
            self.label_introduction.SetLabel(_("Le t�l�chargement n'est pas complet. Voulez-vous recommencer ?"))
            self.bouton_ok.Show(True)
            self.Layout()
        
    def Lancer_telechargement(self):
        """ Lance le thread de t�l�chargement """
        #print "Telechargement de la nouvelle version : etape 2"
        # Cr�ation du r�pertoire de destination
        if os.path.isdir(self.parent.fichierDest) == False :
            os.mkdir(self.parent.fichierDest)
        # T�l�chargement
        max = int(AffichetailleFichier(self.parent.fichierURL))
        self.gauge.SetRange(max)
        self.downloader = Download(self, self.parent.fichierURL, self.parent.fichierDest + "/" + self.parent.nomFichier, self.gauge, self.label_introduction) 
        self.downloader.start()
        #print "Telechargement de la nouvelle version : etape 3"
        self.bouton_ok.Show(False)
        

    def Arreter_telechargement(self):
        """ Arrete le t�l�chargement """
        # On v�rifie si le thread n'a jamais �t� lanc� avant :
        try:
            downloadEnCours = self.downloader.isAlive()
        except AttributeError :
            downloadEnCours = False

        if downloadEnCours:
            # Demande la confirmation de l'arr�t
            dlgConfirm = wx.MessageDialog(self, _("Souhaitez-vous vraiment arr�ter le t�l�chargement ?"), _("Confirmation d'arr�t"), wx.YES_NO|wx.NO_DEFAULT|wx.ICON_QUESTION)
            reponse = dlgConfirm.ShowModal()
            dlgConfirm.Destroy()
            if reponse == wx.ID_NO:
                return
            # Si le t�l�chargement est en cours, on le stoppe :
            self.downloader.abort()
            self.label_introduction.SetLabel(_("Vous avez interrompu le t�l�chargement."))
            self.bouton_ok.Show(True)

            # Pour le debug, passe � la page suivante
            if DEBUG :
                self.parent.Active_page("page_fin_telechargement")
                return

        else:
            # Si le t�l�chargement n'est pas en cours, on ferme la fen�tre
            self.parent.Fermer()




# ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# PAGE FIN TELECHARGEMENT
# ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

class Page_fin_telechargement(wx.Panel):
    def __init__(self, parent, ID=-1):
        wx.Panel.__init__(self, parent, ID, name="page_fin_telechargement", style=wx.TAB_TRAVERSAL)
        self.parent = parent
        
        # Cr�ation des widgets
        texteIntro1 = _("La mise � jour a �t� t�l�charg�e avec succ�s.")
        self.label_introduction1 = wx.StaticText(self, -1, texteIntro1) # FonctionsPerso.StaticWrapText(self, -1, texteIntro1)
        texteIntro2 = _("Souhaitez-vous l'installer maintenant ?")
        self.label_introduction2 = wx.StaticText(self, -1, texteIntro2) # FonctionsPerso.StaticWrapText(self, -1, texteIntro2)
        
        # Boutons
        self.bouton_aide = CTRL_Bouton_image.CTRL(self, texte=_("Aide"), cheminImage="Images/32x32/Aide.png")
        self.bouton_ok = CTRL_Bouton_image.CTRL(self, texte=_("Installer"), cheminImage="Images/32x32/Installation.png")
        self.bouton_annuler = CTRL_Bouton_image.CTRL(self, texte=_("Annuler"), cheminImage="Images/32x32/Annuler.png")
        
        self.__set_properties()
        self.__do_layout()
        
        self.Bind(wx.EVT_BUTTON, self.Onbouton_aide, self.bouton_aide)
        self.Bind(wx.EVT_BUTTON, self.Onbouton_ok, self.bouton_ok)
        self.Bind(wx.EVT_BUTTON, self.Onbouton_annuler, self.bouton_annuler)

    def __set_properties(self):
        self.bouton_aide.SetToolTip(wx.ToolTip(_("Cliquez ici pour obtenir de l'aide")))
        self.bouton_ok.SetToolTip(wx.ToolTip(_("Cliquez ici pour valider")))
        self.bouton_annuler.SetToolTip(wx.ToolTip(_("Cliquez pour annuler et fermer")))

    def __do_layout(self):        
        # Sizer Boutons
        grid_sizer_boutons = wx.FlexGridSizer(rows=1, cols=6, vgap=10, hgap=10)
        grid_sizer_boutons.Add(self.bouton_aide, 0, 0, 0)
        grid_sizer_boutons.Add((20, 20), 0, wx.EXPAND, 0)
        grid_sizer_boutons.Add(self.bouton_ok, 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_annuler, 0, 0, 0)
        grid_sizer_boutons.AddGrowableCol(1)
        # Sizer principal
        grid_sizer_base = wx.FlexGridSizer(rows=5, cols=1, vgap=0, hgap=0)
        grid_sizer_base.Add(self.label_introduction1, 1, wx.ALL|wx.EXPAND, 10)
        grid_sizer_base.Add(self.label_introduction2, 1, wx.ALL|wx.EXPAND, 10)
        grid_sizer_base.Add((5, 5), 1, wx.ALL|wx.EXPAND, 10)
        grid_sizer_base.Add(grid_sizer_boutons, 1, wx.ALL|wx.EXPAND, 10)
        grid_sizer_base.AddGrowableRow(1)
        grid_sizer_base.AddGrowableCol(0)       
        self.SetSizer(grid_sizer_base)
        self.Layout()
        
    def Onbouton_aide(self, event):
        self.parent.Aide()
                    
    def Onbouton_annuler(self, event):
        # Fermeture
        #print "annuler"
        self.parent.Fermer()
        
    def Onbouton_ok(self, event):
        # T�l�chargement termin�e avec succ�s
        self.parent.Active_page("page_installation")

    def Activation(self):
        self.SetSize((500, 600))
        #self.SendSizeEvent()
        self.Refresh()
        
        
# ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# PAGE INSTALLATION
# ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

class Page_installation(wx.Panel):
    def __init__(self, parent, ID=-1):
        wx.Panel.__init__(self, parent, ID, name="page_installation", style=wx.TAB_TRAVERSAL)
        self.parent = parent
        
        # Cr�ation des widgets
        texteIntro = _("Installation de la mise � jour en cours...")
        self.label_introduction = wx.StaticText(self, -1, texteIntro) # FonctionsPerso.StaticWrapText(self, -1, texteIntro)
        self.journal = wx.TextCtrl(self, -1,"", size=(-1, 10), style=wx.TE_MULTILINE)
        
        # Boutons
        self.bouton_aide = CTRL_Bouton_image.CTRL(self, texte=_("Aide"), cheminImage="Images/32x32/Aide.png")
        self.bouton_ok = CTRL_Bouton_image.CTRL(self, texte=_("Installer"), cheminImage="Images/32x32/Installation.png")
        self.bouton_annuler = CTRL_Bouton_image.CTRL(self, texte=_("Annuler"), cheminImage="Images/32x32/Annuler.png")
        
        self.__set_properties()
        self.__do_layout()
        
        self.Bind(wx.EVT_BUTTON, self.Onbouton_aide, self.bouton_aide)
        self.Bind(wx.EVT_BUTTON, self.Onbouton_ok, self.bouton_ok)
        self.Bind(wx.EVT_BUTTON, self.Onbouton_annuler, self.bouton_annuler)

    def __set_properties(self):
        self.bouton_aide.SetToolTip(wx.ToolTip(_("Cliquez ici pour obtenir de l'aide")))
        self.bouton_ok.SetToolTip(wx.ToolTip(_("Cliquez ici pour valider")))
        self.bouton_annuler.SetToolTip(wx.ToolTip(_("Cliquez pour annuler et fermer")))

    def __do_layout(self):        
        # Sizer Boutons
        grid_sizer_boutons = wx.FlexGridSizer(rows=1, cols=6, vgap=10, hgap=10)
        grid_sizer_boutons.Add(self.bouton_aide, 0, 0, 0)
        grid_sizer_boutons.Add((20, 20), 0, wx.EXPAND, 0)
        grid_sizer_boutons.Add(self.bouton_ok, 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_annuler, 0, 0, 0)
        grid_sizer_boutons.AddGrowableCol(1)
        # Sizer principal
        grid_sizer_base = wx.FlexGridSizer(rows=5, cols=1, vgap=0, hgap=0)
        grid_sizer_base.Add(self.label_introduction, 1, wx.ALL|wx.EXPAND, 10)
        grid_sizer_base.Add(self.journal, 1, wx.TOP|wx.LEFT|wx.RIGHT|wx.EXPAND, 10)
        grid_sizer_base.Add(grid_sizer_boutons, 1, wx.ALL|wx.EXPAND, 10)
        grid_sizer_base.AddGrowableRow(1)
        grid_sizer_base.AddGrowableCol(0)       
        self.SetSizer(grid_sizer_base)
        self.Layout()
        
    def Onbouton_aide(self, event):
        self.parent.Aide()
                    
    def Onbouton_annuler(self, event):
        # Fermeture
        pass
        
    def Onbouton_ok(self, event):
        # Fermeture
        print("ok")

    def Activation(self):
        # Pour contrer bug de Layout
        self.SetSize((500, 700))
        self.Refresh()
        self.Installation()
    
    def Installation(self):
        """ Proc�dure d'installation """
        # Sauvegarde globale du r�pertoire teamWorks
        self.bouton_ok.Enable(False)
        self.bouton_annuler.Enable(False)
        
        # Lancement de la sauvegarde
        #self._Sauvegarde()

        wx.CallLater(5, self._Installation)
        
    def _Sauvegarde(self):
        """ Proc�dure de sauvegarde globale du r�pertoire """
        self.label_introduction.SetLabel(_("Sauvegarde des donn�es locales en cours..."))
        if "linux" not in sys.platform :
            self.journal.WriteText(_("> Sauvegarde des donn�es locales :\n\n"))
        
        fichierDest = self.parent.fichierDest + "/global_save.zip"
        if sys.platform.startswith("win") : fichierDest = fichierDest.replace("/", "\\")
        repApplication = os.getcwd()
        
        save = zipdirectory(self, self.journal, fichierDest, repApplication + "/Data")
        save.start()
        
    def _Installation(self):
        """ Proc�dure d'installation """
        self.label_introduction.SetLabel(_("Chargement de l'installeur..."))
        self.journal.WriteText(_("Installeur en cours de chargement. Veuillez patienter..."))

        sleep(1)

        # Lancement de l'installeur
        fichierMAJ = self.parent.fichierDest + "/" + self.parent.nomFichier
        if "linux" in sys.platform :
            dirTemp = UTILS_Fichiers.GetRepTemp()
            self.journal.WriteText(_("\n\nExtraction des fichiers. Veuillez patienter..."))
            os.system("unzip -d " + dirTemp + " " + fichierMAJ)
            self.journal.WriteText(_("\n\nCopie des fichiers. Veuillez patienter..."))
            os.system("cp -a " + dirTemp +"/Noethys-master/noethys/* .")
            self.journal.WriteText(_("\n\nEffacement fichiers temporaires. Veuillez patienter..."))
            os.system("rm -rf " + dirTemp +"/Noethys-master")
        else :
            try :
                FonctionsPerso.LanceFichierExterne(fichierMAJ)
            except :
                self.journal.WriteText(_("\nErreur : Impossible d'ouvrir l'installeur."))
                dlg = wx.MessageDialog(self, _("Noethys n'a pas r�ussi � ouvrir l'installeur.\n\nCe blocage peut peut-�tre venir de votre antivirus. Essayez �ventuellement de le d�sactiver le temps de l'installation de la mise � jour."), _("Erreur"), wx.OK | wx.ICON_ERROR)
                dlg.ShowModal()
                dlg.Destroy()
                return False
        
        # Fermeture de Noethys
        try :
            topWindow = wx.GetApp().GetTopWindow()
            nomWindow = topWindow.GetName()
        except :
            nomWindow = None
        if nomWindow == "general" : 
            # Si la frame 'General' est charg�e, on sauvegarde et on ferme le logiciel
            self.parent.installation = True
        # Fermeture de la dlg
        sleep(2)
        self.parent.Fermer()

        
# -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

class Dialog(wx.Dialog):
    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, -1, name="DLG_Updater", style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX)
        self.parent = parent
        self.installation = False
        
        intro = _("Vous pouvez ici t�l�charger et installer une mise � jour pour Noethys. Ces mises � jour vous permettent bien-s�r de gagner en stabilit� et en fonctionnalit�s.")
        titre = _("Mise � jour du logiciel")
        self.ctrl_bandeau = CTRL_Bandeau.Bandeau(self, titre=titre, texte=intro, hauteurHtml=30, nomImage="Images/32x32/Telecharger.png")
        
        self.page_active = ""
        
        # Changer ci-dessous pour ne pas afficher la page de recherche (1ere page)
        self.afficher_page_recherche = True 

        # Vider r�pertoire Updates
        FonctionsPerso.VideRepertoireUpdates(forcer=True)

        # Met en pause le serveur Connecthys si besoin
        try :
            self.parent.ctrl_serveur_portail.PauseServeur()
        except:
            pass

        # Fichiers
        if "linux" in sys.platform :
            # Version Debian
            self.nomFichier = "master.zip"
            self.fichierURL = "https://github.com/Noethys/Noethys/archive/" + self.nomFichier
        else:
            # Version Windows
            self.nomFichier = "Noethys.exe"
            if six.PY2:
                self.fichierURL = "http://www.noethys.com/fichiers/windows/" + self.nomFichier
            else:
                self.fichierURL = "http://www.noethys.com/fichiers/windows/phoenix/" + self.nomFichier
            
        self.fichierDest = ""
        self.tailleFichier = 0
        self.versionData = ""
        
        # Cr�ation du sizer
        self.sizer_base = wx.FlexGridSizer(rows=6, cols=1, vgap=0, hgap=0)
        self.sizer_base.Add(self.ctrl_bandeau, 1, wx.EXPAND, 0)
        self.sizer_base.AddGrowableCol(0)
        
        # Cr�ation des pages dans le sizer
        self.dictPages = {}
        self.Creation_page("page_recherche", Page_recherche)
        self.Creation_page("page_disponible", Page_disponible)
        self.Creation_page("page_telechargement", Page_telechargement)
        self.Creation_page("page_fin_telechargement", Page_fin_telechargement)
        self.Creation_page("page_installation", Page_installation)

        self.sizer_base.AddGrowableRow(1)
        self.sizer_base.AddGrowableRow(2)
        self.sizer_base.AddGrowableRow(3)
        self.sizer_base.AddGrowableRow(4)
        self.sizer_base.AddGrowableRow(5)
        
        # Chois de la page ouverte au d�marrage
        self.Active_page("page_recherche")
        
        # Finalisation du sizer
        self.SetSizer(self.sizer_base)
        self.Layout()
        
        self.SetMinSize((600, 500))
        self.SetSize((600, 500))
        self.CentreOnScreen()
        
        self.Bind(wx.EVT_CLOSE, self.OnClose)
    
    def GetEtat(self):
        return self.installation
    
    def Creation_page(self, nomPage="", classe=None):
        """ Cr�ation d'une page """
        page = classe(self)
        self.sizer_base.Add(page, 1, wx.EXPAND, 0)
        page.Show(False)
        self.dictPages[nomPage] = page

    def GetPage(self, nomPage=""):
        return self.dictPages[nomPage]

    def Active_page(self, choixPage=""):
        """ Active une page choisie """
        # Faire dispara�tre la page actuelle
        if self.page_active != "" :
            self.dictPages[self.page_active].Show(False)
        # Faire appara�tre et active la page choisie
        if choixPage != "" :
            self.page_active = choixPage
            self.dictPages[self.page_active].Show(True)
            self.dictPages[self.page_active].Activation()
            self.Layout()
    
    def Aide(self):
        from Utils import UTILS_Aide
        UTILS_Aide.Aide("Rechercherunemisejourdulogiciel")

    def SurFermeture(self):
        # Relance serveur Connecthys si besoin
        if self.GetEtat() == False :
            try :
                self.parent.ctrl_serveur_portail.RepriseServeur()
            except:
                pass

    def Fermer(self):
        self.SurFermeture()

        # Fermeture de la fen�tre
        self.EndModal(wx.ID_OK)

    def OnClose(self, event):
        self.SurFermeture()

        if self.page_active == "page_telechargement" :
            self.GetPage("page_telechargement").Arreter_telechargement()
        elif self.page_active == "page_installation" :
            pass
        else:
            self.Fermer()


               
if __name__ == "__main__":
    app = wx.App(0)
    #wx.InitAllImageHandlers()
    DEBUG = True
    frame_1 = Dialog(None)
    app.SetTopWindow(frame_1)
    frame_1.ShowModal()
    app.MainLoop()
