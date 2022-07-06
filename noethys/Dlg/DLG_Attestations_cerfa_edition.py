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
from Ctrl import CTRL_Bouton_image
import datetime
import decimal
import os
import sys
import traceback
import GestionDB
from Ctrl import CTRL_Choix_modele
from Ol import OL_Attestations_cerfa_edition
from Utils import UTILS_Identification
from Utils import UTILS_Historique
from Utils import UTILS_Attestations_cerfa
from Utils import UTILS_Envoi_email
import wx.lib.agw.pybusyinfo as PBI


TEXTE_INTRO = _("Veuillez trouver ci-dessous le montant réglé à notre organisme au titre des dons ouvrant droit à déduction fiscale :")

def DateEngEnDateDD(dateEng):
    if dateEng and not isinstance(dateEng,str): dateEng = str(dateEng)
    return datetime.date(int(dateEng[:4]), int(dateEng[5:7]), int(dateEng[8:10]))

def DateEngFr(textDate):
    if textDate == None: return ""
    textDate = str(textDate)
    text = str(textDate[8:10]) + "/" + str(textDate[5:7]) + "/" + str(textDate[:4])
    return text

def GetTexteNoms(listeNoms=[]):
    """ Récupère les noms sous la forme David DUPOND et Maxime DURAND... """
    texteNoms = ""
    nbreIndividus = len(listeNoms)
    if nbreIndividus == 0 : texteNoms = ""
    if nbreIndividus == 1 : texteNoms = listeNoms[0]
    if nbreIndividus == 2 : texteNoms = _("%s et %s") % (listeNoms[0], listeNoms[1])
    if nbreIndividus > 2 :
        for texteNom in listeNoms[:-2] :
            texteNoms += "%s, " % texteNom
        texteNoms += _("%s et %s") % (listeNoms[-2], listeNoms[-1])
    return texteNoms

def Supprime_accent(texte):
    liste = [ ("é", "e"), ("è", "e"), ("ê", "e"), ("ë", "e"), ("à", "a"), ("û", "u"), ("ô", "o"), ("ç", "c"), ("î", "i"), ("ï", "i"),]
    for a, b in liste :
        texte = texte.replace(a, b)
        texte = texte.replace(a.upper(), b.upper())
    return texte

class TrackOut(object):
    def __init__(self, dictValeurs):
        lstChamps = list(dictValeurs.keys())
        for champ in lstChamps:
            valeur = dictValeurs[champ]
            if champ in ['IDfamille', 'IDcerfa']:
                valeur = int(valeur)
            if champ in ['montant_retenu', 'IDfamille', 'IDcerfa', 'montant_regul', 'montant_dons']:
                valeur = decimal.Decimal(valeur)
            elif champ in ['dateJour', 'debut', 'fin']:
                valeur = DateEngEnDateDD(valeur)
            else:
                valeur = "%s" %(valeur)
            action = "self.%s = valeur"  %(champ)
            try:
                #exec (action)
                setattr(self,"%s"%champ,valeur)
            except:
                print("echec TrackOut2 : ",action)

# -----------------------------------------------------------------------------------------------------------------------

class CTRL_Options(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, id=-1, style=wx.TAB_TRAVERSAL)
        self.parent = parent
        
        self.label_modele = wx.StaticText(self, -1, _("Modèle :"))
        self.ctrl_modele = CTRL_Choix_modele.CTRL_Choice(self, categorie="attestation_fiscale")
        self.bouton_gestion_modeles = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Mecanisme.png"), wx.BITMAP_TYPE_ANY))
        
        # Répertoire
        self.label_repertoire = wx.StaticText(self, -1, _("Un par un :"))
        self.checkbox_repertoire = wx.CheckBox(self, -1, _("Enregistrer les PDF dans le répertoire :"))
        self.ctrl_repertoire = wx.TextCtrl(self, -1, "")
        self.bouton_repertoire = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Repertoire.png"), wx.BITMAP_TYPE_ANY))
        
        self.Bind(wx.EVT_BUTTON, self.OnBoutonModeles, self.bouton_gestion_modeles)
        self.Bind(wx.EVT_CHECKBOX, self.OnCheckRepertoire, self.checkbox_repertoire)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonRepertoire, self.bouton_repertoire)

        self.__set_properties()
        self.__do_layout()

        # Init contrôles
        self.OnCheckRepertoire(None)

    def __set_properties(self):
        self.ctrl_modele.SetToolTip(_("Sélectionnez un modèle de documents"))
        self.checkbox_repertoire.SetToolTip(_("Cochez cette case pour enregistrer un exemplaire de chaque attestation de rappel au format PDF dans le répertoire indiqué"))
        self.bouton_repertoire.SetToolTip(_("Cliquez ici pour sélectionner un répertoire de destination"))

    def __do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(rows=3, cols=1, vgap=10, hgap=10)
        
        # Options
        grid_sizer_options = wx.FlexGridSizer(rows=3, cols=2, vgap=15, hgap=10)
        
        # Modèle
        grid_sizer_options.Add(self.label_modele, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.TOP, 10)
        grid_sizer_modele = wx.FlexGridSizer(rows=1, cols=2, vgap=5, hgap=5)
        grid_sizer_modele.Add(self.ctrl_modele, 0, wx.EXPAND, 0)
        grid_sizer_modele.Add(self.bouton_gestion_modeles, 0, 0, 0)
        grid_sizer_modele.AddGrowableCol(0)
        grid_sizer_options.Add(grid_sizer_modele, 1, wx.EXPAND|wx.TOP, 10)
        
        # Répertoire
        grid_sizer_options.Add(self.label_repertoire, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_repertoire = wx.FlexGridSizer(rows=1, cols=3, vgap=5, hgap=5)
        grid_sizer_repertoire.Add(self.checkbox_repertoire, 0, wx.EXPAND, 0)
        grid_sizer_repertoire.Add(self.ctrl_repertoire, 0, wx.EXPAND, 0)
        grid_sizer_repertoire.Add(self.bouton_repertoire, 0, 0, 0)
        grid_sizer_repertoire.AddGrowableCol(1)
        grid_sizer_options.Add(grid_sizer_repertoire, 1, wx.EXPAND, 0)

        grid_sizer_options.AddGrowableCol(1)
        grid_sizer_base.Add(grid_sizer_options, 1, wx.EXPAND|wx.TOP|wx.LEFT|wx.RIGHT, 0)
                        
        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)
        grid_sizer_base.AddGrowableRow(1)
        grid_sizer_base.AddGrowableCol(0)
        self.Layout()

    def OnBoutonModeles(self, event):
        from Dlg import DLG_Modeles_docs
        dlg = DLG_Modeles_docs.Dialog(self, categorie="attestation_fiscale")
        dlg.ShowModal() 
        dlg.Destroy()
        self.ctrl_modele.MAJ() 

    def OnCheckRepertoire(self, event):
        etat = self.checkbox_repertoire.GetValue()
        self.ctrl_repertoire.Enable(etat)
        self.bouton_repertoire.Enable(etat)

    def OnBoutonRepertoire(self, event): 
        if self.ctrl_repertoire.GetValue != "" : 
            cheminDefaut = self.ctrl_repertoire.GetValue()
            if os.path.isdir(cheminDefaut) == False :
                cheminDefaut = ""
        else:
            cheminDefaut = ""
        dlg = wx.DirDialog(self, _("Veuillez sélectionner un répertoire de destination :"), defaultPath=cheminDefaut, style=wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST)
        if dlg.ShowModal() == wx.ID_OK:
            self.ctrl_repertoire.SetValue(dlg.GetPath())
        dlg.Destroy()

    def OnChoixIntitules(self, event=None):
        typeLabel = self.ctrl_intitules.GetID()
        self.ctrl_attestations.typeLabel = typeLabel
        self.ctrl_attestations.MAJ() 

    def GetOptions(self):
        dictOptions = {} 
        dictOptions["signataire"] = {
            "nom" : "",
            "fonction" : "",
            "sexe" : "",
            "genre" : "",
            }
        
        # Répertoire
        if self.checkbox_repertoire.GetValue() == True :
            repertoire = self.ctrl_repertoire.GetValue() 
            # Vérifie qu'un répertoire a été saisie
            if repertoire == "" :
                dlg = wx.MessageDialog(self, _("Vous devez obligatoirement sélectionner un répertoire de destination !"), _("Erreur"), wx.OK | wx.ICON_EXCLAMATION)
                dlg.ShowModal()
                dlg.Destroy()
                self.ctrl_repertoire.SetFocus()
                return False
            # Vérifie que le répertoire existe
            if os.path.isdir(repertoire) == False :
                dlg = wx.MessageDialog(self, _("Le répertoire de destination que vous avez saisi n'existe pas !"), _("Erreur"), wx.OK | wx.ICON_EXCLAMATION)
                dlg.ShowModal()
                dlg.Destroy()
                self.ctrl_repertoire.SetFocus()
                return False
        else:
            repertoire = None
                
        # Récupération du modèle
        IDmodele = self.ctrl_modele.GetID() 
        if IDmodele == None :
            dlg = wx.MessageDialog(self, _("Vous devez obligatoirement sélectionner un modèle !"), _("Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return False
        
        # Constitution du dictOptions
        dictOptions["IDmodele"] = IDmodele
        dictOptions["repertoire"] = repertoire
        dictOptions["intro"] = ""
        
        return dictOptions

# ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

class Panel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, id=-1, name="DLG_Attestations_cerfa_edition", style=wx.TAB_TRAVERSAL)
        self.parent = parent
        
        self.impressionEffectuee = False
        self.tous = False
        self.donnees = {}
        # Options
        self.staticbox_options_staticbox = wx.StaticBox(self, -1, _("Options d'impression"))
        self.ctrl_options = CTRL_Options(self)

        # Cerfas
        self.staticbox_attestations_staticbox = wx.StaticBox(self, -1, _("Cerfas à éditer"))
        self.listviewAvecFooter = OL_Attestations_cerfa_edition.ListviewAvecFooter(self,  kwargs={})
        self.ctrl_attestations = self.listviewAvecFooter.GetListview()

        self.ctrl_recherche = OL_Attestations_cerfa_edition.CTRL_Outils(self, listview=self.ctrl_attestations, afficherCocher=True)

        self.bouton_apercu_liste = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Apercu.png"), wx.BITMAP_TYPE_ANY))
        self.bouton_imprimer_liste = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Imprimante.png"), wx.BITMAP_TYPE_ANY))
        self.bouton_export_texte = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Texte2.png"), wx.BITMAP_TYPE_ANY))
        self.bouton_export_excel = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Excel.png"), wx.BITMAP_TYPE_ANY))

        # Actions
        self.staticbox_actions_staticbox = wx.StaticBox(self, -1, _("Actions"))
        self.bouton_email = CTRL_Bouton_image.CTRL(self, texte=_("Transmettre\npar Email"), tailleImage=(22, 22), margesImage=(4, 4, 0, 0), margesTexte=(-5, 1), cheminImage="Images/32x32/Emails_exp.png")
        self.bouton_imprimer = CTRL_Bouton_image.CTRL(self, texte=_("Imprimer"), tailleImage=(22, 22), margesImage=(4, 0, 0, 0), margesTexte=(-5, 1), cheminImage="Images/32x32/Imprimante.png")
        self.bouton_email.SetMinSize((150, -1))
        self.bouton_imprimer.SetMinSize((150, -1))
        
        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_BUTTON, self.ctrl_attestations.Imprimer, self.bouton_imprimer_liste)
        self.Bind(wx.EVT_BUTTON, self.ctrl_attestations.ExportTexte, self.bouton_export_texte)
        self.Bind(wx.EVT_BUTTON, self.ctrl_attestations.ExportExcel, self.bouton_export_excel)
        self.Bind(wx.EVT_BUTTON, self.EnvoiEmail, self.bouton_email)
        self.Bind(wx.EVT_BUTTON, self.Apercu, self.bouton_imprimer)

    def __set_properties(self):
        self.bouton_apercu_liste.SetToolTip(_("Cliquez ici pour afficher un aperçu avant impression de la liste"))
        self.bouton_imprimer_liste.SetToolTip(_("Cliquez ici pour imprimer la liste"))
        self.bouton_export_texte.SetToolTip(_("Cliquez ici pour exporter la liste au format texte"))
        self.bouton_export_excel.SetToolTip(_("Cliquez ici pour exporter la liste au format Excel"))
        self.bouton_email.SetToolTip(_("Cliquez ici pour accéder à l'envoi des attestations fiscales par Email"))
        self.bouton_imprimer.SetToolTip(_("Cliquez ici pour imprimer les attestations fiscales générées"))

    def __do_layout(self):

        grid_sizer_base = wx.FlexGridSizer(rows=3, cols=1, vgap=10, hgap=10)
        # Attestations
        staticbox_attestations = wx.StaticBoxSizer(self.staticbox_attestations_staticbox, wx.VERTICAL)
        grid_sizer_attestations = wx.FlexGridSizer(rows=2, cols=2, vgap=5, hgap=5)

        grid_sizer_attestations.Add(self.listviewAvecFooter, 1, wx.EXPAND, 0)

        grid_sizer_commandes = wx.FlexGridSizer(rows=6, cols=1, vgap=5, hgap=5)
        grid_sizer_commandes.Add(self.bouton_apercu_liste, 0, 0, 0)
        grid_sizer_commandes.Add(self.bouton_imprimer_liste, 0, 0, 0)
        grid_sizer_commandes.Add(self.bouton_export_texte, 0, 0, 0)
        grid_sizer_commandes.Add(self.bouton_export_excel, 0, 0, 0)
        grid_sizer_attestations.Add(grid_sizer_commandes, 1, wx.EXPAND, 0)

        grid_sizer_recherches = wx.FlexGridSizer(rows=1, cols=2, vgap=5, hgap=5)
        grid_sizer_recherches.Add(self.ctrl_recherche, 0, wx.EXPAND, 5)
        grid_sizer_recherches.AddGrowableCol(0)
        grid_sizer_attestations.Add(grid_sizer_recherches, 0, wx.EXPAND, 0)

        grid_sizer_attestations.AddGrowableCol(0)
        grid_sizer_attestations.AddGrowableRow(0)
        
        staticbox_attestations.Add(grid_sizer_attestations, 1, wx.ALL|wx.EXPAND, 5)
        grid_sizer_base.Add(staticbox_attestations, 1, wx.EXPAND|wx.LEFT|wx.RIGHT, 0)        
        
        # Gridsizer bas
        grid_sizer_bas = wx.FlexGridSizer(rows=1, cols=2, vgap=10, hgap=10)
        grid_sizer_bas.AddGrowableCol(0)
        grid_sizer_bas.AddGrowableRow(0)

        # Options
        staticbox_options = wx.StaticBoxSizer(self.staticbox_options_staticbox, wx.VERTICAL)
        staticbox_options.Add(self.ctrl_options, 1, wx.ALL|wx.EXPAND, 5)
        grid_sizer_bas.Add(staticbox_options, 1, wx.EXPAND, 0)
        
        # Boutons d'actions
        staticbox_actions = wx.StaticBoxSizer(self.staticbox_actions_staticbox, wx.HORIZONTAL)
        staticbox_actions.Add(self.bouton_email, 1, wx.EXPAND|wx.ALL,10)
        staticbox_actions.Add(self.bouton_imprimer, 1, wx.EXPAND|wx.ALL, 10)
        grid_sizer_bas.Add(staticbox_actions, 1, wx.EXPAND, 0)
        
        grid_sizer_base.Add(grid_sizer_bas, 1, wx.EXPAND|wx.TOP|wx.LEFT|wx.RIGHT, 0)
        
        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)
        grid_sizer_base.AddGrowableRow(0)
        grid_sizer_base.AddGrowableCol(0)
        self.Layout()

    def CocheTout(self):
        self.ctrl_attestations.CocherTout()

    def DecocheTout(self):
        self.ctrl_attestations.CocherRien()

    def Validation(self):
        pass

    def MAJ(self):
        dlgAttente = PBI.PyBusyInfo(_("Recherche des données..."), parent=None, title=_("Veuillez patienter..."), icon=wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Logo.png"), wx.BITMAP_TYPE_ANY))
        wx.Yield()
        listeCerfasGeneres = self.parent.page2.ctrl_attestations.listeCerfasGeneres
        periode = self.GetParent().page1.GetPeriode()
        self.ctrl_attestations.MAJ(listeCerfasGeneres,periode)
        del dlgAttente

    def EcritStatusbar(self, texte=""):
        try :
            topWindow = wx.GetApp().GetTopWindow() 
            topWindow.SetStatusText(texte)
        except : 
            pass

    def Sauvegarder(self):
        """ Sauvegarde des attestations """
        # Demande la confirmation de sauvegarde
        dlg = wx.MessageDialog(self, _("Souhaitez-vous mémoriser les attestations ?\n\n(Cliquez NON si c'était juste un test sinon cliquez OUI)"), _("Sauvegarde"), wx.YES_NO|wx.YES_DEFAULT|wx.CANCEL|wx.ICON_INFORMATION)
        reponse = dlg.ShowModal() 
        dlg.Destroy()
        if reponse != wx.ID_YES :
            return

        dlgAttente = PBI.PyBusyInfo(_("Sauvegarde des attestations en cours..."), parent=None, title=_("Veuillez patienter..."), icon=wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Logo.png"), wx.BITMAP_TYPE_ANY))
        wx.Yield() 

        DB = GestionDB.DB()
        
        try :
            for IDfamille, dictCompte in self.donnees.items() :
                if dictCompte["select"] == True :
                    numero = dictCompte["num_attestation"]
                    IDfamille = dictCompte["IDfamille"] 
                    listePrestations = dictCompte["listePrestations"] 
                    total = dictCompte["total"] 
                    regle = dictCompte["ventilation"] 
                    solde = total - regle

                    # Liste des activités
                    texteActivites = ""
                    for IDactivite in self.listeActivites :
                        texteActivites += "%d;" % IDactivite
                    if len(self.listeActivites) > 0 :
                        texteActivites = texteActivites[:-1]
                    # Liste des individus
                    texteIndividus = ""
                    for IDindividu in list(dictCompte["individus"].keys()) :
                        texteIndividus += "%d;" % IDindividu
                    if len(list(dictCompte["individus"].keys())) > 0 :
                        texteIndividus = texteIndividus[:-1]
                    
                    IDutilisateur = UTILS_Identification.GetIDutilisateur()
                    
                    # Sauvegarde de la facture
                    listeDonnees = [ 
                        ("numero", numero), 
                        ("IDfamille", IDfamille), 
                        ("date_edition", str(datetime.date.today())), 
                        ("activites", texteActivites), 
                        ("individus", texteIndividus), 
                        ("IDutilisateur", IDutilisateur), 
                        ("date_debut", str(self.date_debut)), 
                        ("date_fin", str(self.date_fin)), 
                        ("total", float(total)), 
                        ("regle", float(regle)), 
                        ("solde", float(solde)), 
                        ]

                    IDattestation = DB.ReqInsert("attestations", listeDonnees)
                                        
                    # Mémorisation de l'action dans l'historique
                    UTILS_Historique.InsertActions([{
                            "IDfamille" : IDfamille,
                            "IDcategorie" : 27, 
                            "action" : _("Edition d'un Cerfa  pour la période du %s au %s pour un total de %.02f € ") % (DateEngFr(str(self.date_debut)), DateEngFr(str(self.date_fin)), total),
                            },])

            DB.Close() 
            del dlgAttente

        except Exception as err:
            DB.Close() 
            del dlgAttente
            traceback.print_exc(file=sys.stdout)
            dlg = wx.MessageDialog(self, _("Désolé, le problème suivant a été rencontré dans la sauvegarde des attestations : \n\n%s") % err, _("Erreur"), wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            return False

    def GetOptions(self):
        dictOptions = self.ctrl_options.GetOptions()
        if dictOptions == False :
            return False

        dictOptions["date_debut"], dictOptions["date_fin"] = self.GetParent().page1.GetPeriode()
        dictOptions["titre"] = _("Attestation Fiscale")
        return dictOptions

    def GenerePDF(self,afficherDoc = False):
        tracks = self.ctrl_attestations.GetTracksCoches()
        if len(tracks) == 0:
            if afficherDoc: texte = "à imprimer"
            else: texte = "à envoyer"
            dlg = wx.MessageDialog(self, _("Vous n'avez sélectionné aucune attestation %s !")%texte, _("Erreur"),
                                   wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return False

        """ Aperçu PDF des attestations """
        # Validation des données saisies
        self.tracksOut = []
        for track in tracks:
            #complémentation des track
            if isinstance(track.cerfa,str):
                strCerfa = track.cerfa
            else:
                strCerfa = track.cerfa.decode()
            strCerfa = strCerfa[1:-1]
            lstCerfa = strCerfa.split("##")
            dictCerfa = {}
            for item in lstCerfa:
                lstItem = item.split("::")
                if len(lstItem) == 2:
                    dictCerfa[str(lstItem[0])] = lstItem[1]
            dictCerfa["IDcerfa"] = track.IDcerfa
            trackOut = TrackOut(dictCerfa)
            self.tracksOut.append(trackOut)

        # Récupération des options
        dictOptions = self.GetOptions()
        if dictOptions == False :
            return False

        # Impression des cotisations sélectionnées
        x = UTILS_Attestations_cerfa.Attestations_fiscales()
        resultat = x.Impression(tracks=self.tracksOut,
                                afficherDoc=afficherDoc,
                                dictOptions=dictOptions,
                                repertoire=dictOptions["repertoire"],
                                )
        return resultat

    def Apercu(self, event=None):
        resultat = self.GenerePDF(afficherDoc = True)
        if resultat == False:
            return False

    def EnvoiEmail(self, event=None): 
        """ Envoi par Email des attestations fiscales """
        resultat =  self.GenerePDF(afficherDoc = False)
        if resultat == False :
            return False
        dictChampsFusion, dictPieces = resultat
        
        def SupprimerFichiersTemp():
            for ID, fichier in dictPieces.items() :
                os.remove(fichier)  

        # Récupération de toutes les adresses Emails
        DB = GestionDB.DB()
        req = """SELECT IDindividu, mail, travail_mail
        FROM individus;"""
        DB.ExecuterReq(req,MsgBox="ExecuterReq")
        listeAdressesIndividus = DB.ResultatReq()
        DB.Close() 
        dictAdressesIndividus = {}
        for IDindividu, mail, travail_mail in listeAdressesIndividus :
            dictAdressesIndividus[IDindividu] = {"perso" : mail, "travail" : travail_mail}
                
        # Récupération des données adresse + champs + pièces
        listeDonnees = []
        listeAnomalies = []
        listeEnvoiNonDemande = []
        for track in self.tracksOut :
            adresse = UTILS_Envoi_email.GetAdresseFamille(track.IDfamille,
                                                          choixMultiple=False,
                                                          muet=False,
                                                          nomTitulaires=track.nomPrenom)
            # Mémorisation des données
            if adresse not in (None, "", []) : 
                if track.IDcerfa in dictPieces :
                    fichier = dictPieces[track.IDcerfa]
                    champs = dictChampsFusion[track.IDcerfa]
                    listeDonnees.append({"adresse" : adresse, "pieces" : [fichier,], "champs" : champs})
            else :
                listeAnomalies.append(track.nomPrenom)
        
        # Annonce les anomalies trouvées
        if len(listeAnomalies) > 0 :
            texte = _("%d des familles sélectionnées n'ont pas d'adresse Email.\n\n") % len(listeAnomalies)
            texte += _("Souhaitez-vous quand même continuer avec les %d autres familles ?") % len(listeDonnees)
            dlg = wx.MessageDialog(self, texte, _("Avertissement"), wx.YES_NO|wx.NO_DEFAULT|wx.CANCEL|wx.ICON_EXCLAMATION)
            reponse = dlg.ShowModal() 
            dlg.Destroy()
            if reponse != wx.ID_YES :
                SupprimerFichiersTemp()
                return        
        
        # Dernière vérification avant transfert
        if len(listeDonnees) == 0 : 
            dlg = wx.MessageDialog(self, _("Il ne reste finalement aucune attestation fiscale à envoyer par Email !"), _("Erreur"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            SupprimerFichiersTemp()
            return

        # Transfert des données vers DLG Mailer
        from Dlg import DLG_Mailer
        dlg = DLG_Mailer.Dialog(self, categorie="attestation_fiscale")
        dlg.SetDonnees(listeDonnees, modificationAutorisee=False)
        dlg.ChargerModeleDefaut()
        dlg.ShowModal() 
        dlg.Destroy()

        # Suppression des PDF temporaires
        SupprimerFichiersTemp()


# -------------------------------------------------------------------------------------------------------------------------------------------

class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self, -1)
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_1.Add(panel, 1, wx.ALL|wx.EXPAND)
        self.SetSizer(sizer_1)
        self.ctrl = Panel(panel)
        self.boutonTest = wx.Button(panel, -1, _("Bouton de test"))
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_2.Add(self.ctrl, 1, wx.ALL|wx.EXPAND, 4)
        sizer_2.Add(self.boutonTest, 0, wx.ALL|wx.EXPAND, 4)
        panel.SetSizer(sizer_2)
        self.Layout()
        self.CentreOnScreen()
        self.panel = panel
        self.Bind(wx.EVT_BUTTON, self.OnBoutonTest, self.boutonTest)
        
    def OnBoutonTest(self, event):
        """ Bouton Test """
        self.ctrl.Validation()
        print(self.panel.dictParametres)

if __name__ == '__main__':
    app = wx.App(0)
    #wx.InitAllImageHandlers()
    frame_1 = MyFrame(None, -1, _("TEST"), size=(700, 500))
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()
