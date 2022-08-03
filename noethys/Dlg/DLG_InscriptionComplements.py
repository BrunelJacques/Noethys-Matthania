#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, Matthania
# Auteur:          Ivan LUCAS, JB, Jacques Brunel
# Licence:         Licence GNU GPL
# Gestion des compléemnts transports cotisation et réductions famille
# Adapté à partir de DLG_Saisie_transport.Dialog
#------------------------------------------------------------------------

from Utils.UTILS_Traduction import _
import wx
import Chemins
from Utils import UTILS_Utilisateurs
from Ctrl import CTRL_Bouton_image
from Ctrl import CTRL_Bandeau
from Ctrl import CTRL_Saisie_nombre
from Gest import GestionArticle
from Ctrl import CTRL_Saisie_transport
import GestionDB
import datetime

def DateEngEnDateDD(dateEng):
    if isinstance(dateEng,datetime.date): return dateEng
    if dateEng == None:
        dateEng = '1900-01-01'
    return datetime.date(int(dateEng[:4]), int(dateEng[5:7]), int(dateEng[8:10]))

def Nz(valeur):
    if valeur == None:
        valeur = 0.0
    if valeur == "":
        valeur = 0.0
    return valeur

# -----------------------------------------------------------------------------------------------------------------
class DlgTransports(wx.Dialog):
    def __init__(self, dictDonnees,modeVirtuel = False):
        wx.Dialog.__init__(self, None, -1, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX)
        self.titre = ("Gestion des compléments à l'inscription : Transports puis cotisation/réductions")
        self.SetTitle("DLG_InscriptionComplements")
        self.dictDonnees = dictDonnees
        self.modeVirtuel = modeVirtuel
        droitCreation = UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("individus_inscriptions", "creer")
        if not droitCreation : self.modeVirtuel = True
        self.IDfamille = dictDonnees["IDfamille"]
        self.IDindividu = dictDonnees["IDindividu"]
        self.IDactivite = dictDonnees["IDactivite"]
        self.IDgroupe = dictDonnees["IDgroupe"]
        self.codeNature = None
        self.IDcategorieTarif = dictDonnees["IDcategorie_tarif"]
        ligneInfo = "Activité: " + dictDonnees["nom_activite"] + " | Groupe: " + dictDonnees["nom_groupe"]+ " | Tarif: " + dictDonnees["nom_categorie_tarif"]
        soustitreFenetre = "Campeur : " + dictDonnees["nom_individu"] + " | Famille : " + dictDonnees["nom_famille"]
        self.ctrl_bandeau = CTRL_Bandeau.Bandeau(self, titre=ligneInfo, texte=soustitreFenetre, hauteurHtml=10,nomImage="Images/22x22/Smiley_nul.png")

        # Contenu
        self.__setData()
        self.staticbox_aller = wx.StaticBox(self, -1, _("Transport    ALLER"))
        self.staticbox_retour = wx.StaticBox(self, -1, _("Transport    RETOUR"))
        self.ctrl_saisie_aller = CTRL_Saisie_transport.CTRL(self, IDtransport=self.IDtranspAller, IDindividu=self.IDindividu,
                                                             dictDonnees={},verrouilleBoutons=self.modeVirtuel,ar="aller")
        self.ctrl_saisie_retour = CTRL_Saisie_transport.CTRL(self, IDtransport=self.IDtranspRetour,IDindividu=self.IDindividu,
                                                              dictDonnees={}, verrouilleBoutons=self.modeVirtuel,ar="retour")
        self.label_prixAller = wx.StaticText(self, -1, _("Prix du transport ALLER:"))
        self.ctrl_prixAller = CTRL_Saisie_nombre.CTRL(self, verif=False)
        self.label_prixRetour = wx.StaticText(self, -1, _("Prix du transport RETOUR:"))
        self.ctrl_prixRetour = CTRL_Saisie_nombre.CTRL(self,verif=False)
        self.ctrl_prixAller.SetValue(str(self.prixTranspAller))
        self.ctrl_prixRetour.SetValue(str(self.prixTranspRetour))

        # Boutons
        self.bouton_aide = CTRL_Bouton_image.CTRL(self, texte=_("Aide"), cheminImage=Chemins.GetStaticPath("Images/32x32/Aide.png"))
        self.bouton_swap = CTRL_Bouton_image.CTRL(self, texte=_("Copie Retour"), cheminImage=Chemins.GetStaticPath("Images/16x16/Actualiser.png"))
        self.bouton_ok = CTRL_Bouton_image.CTRL(self, texte=_("Valider"), cheminImage=Chemins.GetStaticPath("Images/32x32/Suivant.png"))
        self.bouton_annuler = CTRL_Bouton_image.CTRL(self, id=wx.ID_CANCEL, texte=_("Ignorer"), cheminImage=Chemins.GetStaticPath("Images/32x32/Annuler.png"))
        if self.modeVirtuel:
            self.ctrl_prixAller.Enable(False)
            self.ctrl_prixRetour.Enable(False)
            self.bouton_ok.Enable(False)
            self.bouton_swap.Enable(False)

        self.__set_properties()
        self.VerifDatesActivite()
        self.__do_layout()

    def __setData(self):
        DB = GestionDB.DB()
        self.IDtranspAller = 0
        self.IDtranspRetour = 0
        self.prixTranspAller = 0.0
        self.prixTranspRetour = 0.0
        if not "IDtranspAller" in self.dictDonnees:
            self.dictDonnees["IDtranspAller"] = None
            self.dictDonnees["prixTranspAller"] = 0.0
        if not "IDtranspRetour" in self.dictDonnees:
            self.dictDonnees["IDtranspRetour"] = None
            self.dictDonnees["prixTranspRetour"] = 0.0
        if not self.modeVirtuel:
            #Vérif double transport
            IDactivite = self.dictDonnees["IDactivite"]
            IDindividu = self.dictDonnees["IDindividu"]
            IDnumPiece = self.dictDonnees["IDnumPiece"]
            req = """
                SELECT pieIDnumPiece,pieIDtranspAller, piePrixTranspAller, pieIDtranspRetour, piePrixTranspRetour
                FROM matPieces
                WHERE pieIDactivite = %d AND pieIDindividu = %d AND pieIDnumPiece <> %d;""" % (IDactivite, IDindividu, IDnumPiece)
            DB.ExecuterReq(req,MsgBox="ExecuterReq")
            recordset = DB.ResultatReq()
            nbre = 0
            prix = 0.00
            if len(recordset)>0:
                for IDnumPiece,IDtranspAller, prixTranspAller, IDtranspRetour, prixTranspRetour in recordset:
                    if not IDtranspAller: IDtranspAller = 0
                    if not IDtranspRetour: IDtranspRetour = 0
                    if IDtranspAller > 0:
                        nbre += 1
                    if IDtranspRetour > 0:
                        nbre += 1
                    if prixTranspAller != None :
                        prix += prixTranspAller
                    if prixTranspRetour != None :
                        prix += prixTranspRetour
            if nbre != 0 or prix != 0.00:
                GestionDB.Messages().Box(titre = "Non Bloquant !",message = "Cet individu est déjà inscrit à %d transports pour cette activité pour un montant de %d €\n tenez en compte dans la nouvelle saisie ils s'ajouteront"%(nbre,prix))

            # Récup d'un éventuel transport perdu
            req = """
                SELECT transports.IDtransport
                FROM (transports 
                    LEFT JOIN matPieces ON transports.IDtransport = matPieces.pieIDtranspAller) 
                    LEFT JOIN matPieces AS matPieces_1 ON transports.IDtransport = matPieces_1.pieIDtranspRetour
                WHERE ((matPieces.pieIDtranspAller Is Null) 
                        AND (matPieces_1.pieIDtranspRetour Is Null) 
                        AND (transports.IDindividu) = %d);
                """ % (IDindividu)
            DB.ExecuterReq(req,MsgBox="ExecuterReq")
            recordset = DB.ResultatReq()
            if len(recordset) > 0 :
                if not (self.dictDonnees["IDtranspAller"] > 0):
                    mess = "Un transport orphelin d'une inscription vient d'être rattaché à l'aller, vérifiez si c'est juste"
                    self.dictDonnees["IDtranspAller"] = recordset[0][0]
                elif not (self.dictDonnees["IDtranspRetour"] > 0):
                    mess = "Un transport orphelin d'une inscription vient d'être rattaché au retour, vérifiez si c'est juste"
                    self.dictDonnees["IDtranspRetour"] = recordset[0][0]
                else:
                    mess = "Il y a des transports orphelins d'une inscription pour cet individu\n"
                    mess += "Supprimez les transports visibles, validez puis revenez pour rattacher les orphelins"
                wx.MessageBox(mess,"Anomalie",style=wx.ICON_EXCLAMATION)


        self.existAller = False
        self.prixTranspAller = self.dictDonnees["prixTranspAller"]
        if self.dictDonnees["IDtranspAller"]!= None:
            if self.dictDonnees["IDtranspAller"]!= 0:
                self.IDtranspAller = self.dictDonnees["IDtranspAller"]
                req = """SELECT depart_DATE, arrivee_DATE
                            FROM transports
                            WHERE IDtransport=%d;""" % (self.IDtranspAller)
                DB.ExecuterReq(req,MsgBox="ExecuterReq")
                result = DB.ResultatReq()
                if len(result)>0:
                    if len(result[0])> 0 :
                        allerDepartDate, allerArriveeDate = result[0]
                        self.existAller = True
        self.existRetour = False
        self.prixTranspRetour = self.dictDonnees["prixTranspRetour"]
        if self.dictDonnees["IDtranspRetour"]!= None:
            if self.dictDonnees["IDtranspRetour"]!= 0:
                self.IDtranspRetour = self.dictDonnees["IDtranspRetour"]
                req = """SELECT depart_DATE, arrivee_DATE
                            FROM transports
                            WHERE IDtransport=%d;""" % (self.IDtranspRetour)
                DB.ExecuterReq(req,MsgBox="ExecuterReq")
                result = DB.ResultatReq()
                if len(result)>0:
                    if len(result[0])> 0 :
                        retourDepartDate, retourArriveeDate = result[0]
                        self.existRetour = True

        #recherche des dates d'activité pour alimenter les dates de transport
        IDactivite = self.dictDonnees["IDactivite"]
        IDgroupe = self.dictDonnees["IDgroupe"]
        self.date_debut_activite = GestionArticle.DebutOuvertures(DB,IDactivite,IDgroupe)
        self.date_fin_activite = GestionArticle.FinOuvertures(DB,IDactivite,IDgroupe)
        if self.prixTranspAller == None: self.prixTranspAller= 0.0
        if self.prixTranspRetour == None: self.prixTranspRetour= 0.0
        DB.Close()

    def VerifDatesActivite(self):
        dicAller = self.ctrl_saisie_aller.GetDictDonnees()
        allerDepartDate = dicAller["depart_date"]
        dicRetour = self.ctrl_saisie_retour.GetDictDonnees()
        retourDepartDate = dicRetour["depart_date"]
        #vérif de cohérence de date
        if allerDepartDate and self.date_debut_activite != DateEngEnDateDD(allerDepartDate) :
            text1 = "Changer la date du transport pour correspondre à l'activité"
            text2 = "Conserver une arrivée le %s pour une activité commençant le %s" %(allerDepartDate,self.date_debut_activite)
            rep = GestionDB.Messages().Choix(listeTuples=[(1,text1),(2,text2),], titre = ("Les dates de transports ne correspondent pas à l'activité"), intro = "Choix nécessaire")
            if rep[0] == 1 :
                dicAller["depart_date"] = self.date_debut_activite
                dicRetour["depart_date"] = self.date_fin_activite
                listeDonnees = [("depart_date",self.date_debut_activite),
                                ("arrivee_date",self.date_debut_activite)]
                self.ctrl_saisie_aller.RemplitChamps(listeDonnees)
                listeDonnees = [("depart_date",self.date_fin_activite),
                                ("arrivee_date",self.date_fin_activite)]
                self.ctrl_saisie_retour.RemplitChamps(listeDonnees)
        #vérif de cohérence de date
        if retourDepartDate and self.date_fin_activite != DateEngEnDateDD(retourDepartDate) :
            GestionDB.Messages().Box("Vérif nécessaire",message = "La date retour n'est pas la fin de l'activité!")

    def __set_properties(self):
        self.bouton_aide.SetToolTip(_("Cliquez ici pour obtenir de l'aide"))
        self.bouton_swap.SetToolTip(_("Cliquez ici pour répliquer l'aller sur le retour"))
        self.bouton_ok.SetToolTip(_("Cliquez ici pour valider"))
        self.bouton_annuler.SetToolTip(_("Cliquez ici pour annuler"))
        self.SetMinSize((850, 750))
        if self.modeVirtuel:
            self.ctrl_saisie_aller.Enable(False)
            self.ctrl_saisie_retour.Enable(False)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonSwap, self.bouton_swap)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonOk, self.bouton_ok)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAide, self.bouton_aide)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAnnuler, self.bouton_annuler)

    def __do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(rows=3, cols=1, vgap=10, hgap=10)
        grid_sizer_base.Add(self.ctrl_bandeau, 1, wx.EXPAND, 0)

        grid_sizer_transports = wx.FlexGridSizer(rows=1, cols=2, vgap=0, hgap=0)

        staticsizer_aller = wx.StaticBoxSizer(self.staticbox_aller, wx.VERTICAL)
        grid_sizer_aller = wx.FlexGridSizer(rows=2, cols=1, vgap=0, hgap=0)
        grid_sizer_aller.Add(self.ctrl_saisie_aller, 1, wx.LEFT|wx.RIGHT|wx.EXPAND, 10)

        grid_sizer_prix_aller = wx.FlexGridSizer(rows=1, cols=2, vgap=0, hgap=0)
        grid_sizer_prix_aller.Add(self.label_prixAller, 0, wx.ALL|wx.ALIGN_TOP, 5)
        grid_sizer_prix_aller.Add(self.ctrl_prixAller, 0, wx.LEFT|wx.RIGHT|wx.EXPAND, 10)
        grid_sizer_prix_aller.AddGrowableCol(1)
        grid_sizer_aller.Add(grid_sizer_prix_aller, 1, wx.ALL|wx.EXPAND, 10)
        grid_sizer_aller.AddGrowableCol(0)
        grid_sizer_aller.AddGrowableRow(0)
        staticsizer_aller.Add(grid_sizer_aller, 1, wx.RIGHT|wx.EXPAND,5)

        grid_sizer_transports.Add(staticsizer_aller, 0,wx.ALL|wx.EXPAND, 3)

        staticsizer_retour = wx.StaticBoxSizer(self.staticbox_retour, wx.VERTICAL)
        grid_sizer_retour = wx.FlexGridSizer(rows=2, cols=1, vgap=0, hgap=0)
        grid_sizer_retour.Add(self.ctrl_saisie_retour, 1, wx.LEFT|wx.RIGHT|wx.EXPAND, 10)

        grid_sizer_prix_retour = wx.FlexGridSizer(rows=1, cols=2, vgap=0, hgap=0)
        grid_sizer_prix_retour.Add(self.label_prixRetour, 0, wx.ALL|wx.ALIGN_TOP, 5)
        grid_sizer_prix_retour.Add(self.ctrl_prixRetour, 0, wx.LEFT|wx.RIGHT|wx.EXPAND, 10)
        grid_sizer_prix_retour.AddGrowableCol(1)
        grid_sizer_retour.Add(grid_sizer_prix_retour, 1, wx.ALL|wx.EXPAND, 10)
        grid_sizer_retour.AddGrowableCol(0)
        grid_sizer_retour.AddGrowableRow(0)

        staticsizer_retour.Add(grid_sizer_retour, 1, wx.RIGHT|wx.EXPAND,5)

        grid_sizer_transports.Add(staticsizer_retour, 0,wx.ALL|wx.EXPAND, 3)

        grid_sizer_transports.AddGrowableCol(0)
        grid_sizer_transports.AddGrowableCol(1)
        grid_sizer_transports.AddGrowableRow(0)
        grid_sizer_base.Add(grid_sizer_transports, 1,wx.ALL|wx.EXPAND, 3)

        grid_sizer_boutons = wx.FlexGridSizer(rows=1, cols=5, vgap=10, hgap=10)
        grid_sizer_boutons.Add(self.bouton_aide, 0, 0, 0)
        grid_sizer_boutons.Add((20, 20), 0, wx.EXPAND, 0)
        grid_sizer_boutons.Add(self.bouton_swap, 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_ok, 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_annuler, 0, 0, 0)
        grid_sizer_boutons.AddGrowableCol(1)
        grid_sizer_base.Add(grid_sizer_boutons, 1, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 10)
        grid_sizer_base.AddGrowableCol(0)
        grid_sizer_base.AddGrowableRow(1)
        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)
        self.Layout()
        self.CenterOnScreen()

    def OnBoutonAide(self, event):
        from Utils import UTILS_Aide
        UTILS_Aide.Aide("Transports1")

    def OnBoutonSwap(self,event):
        self.ctrl_prixRetour.SetValue(str(self.ctrl_prixAller.GetValue()))
        self.dictRetour = self.ctrl_saisie_retour.GetDictDonnees()
        self.dictAller = self.ctrl_saisie_aller.GetDictDonnees()
        self.SwapDictAller('depart_IDarret','arrivee_IDarret')
        self.SwapDictAller('depart_IDlieu','arrivee_IDlieu')
        self.SwapDictAller('depart_localisation','arrivee_localisation')
        listeChamps = ['mode','categorie','IDcompagnie','IDligne','depart_IDarret',
                       'depart_IDlieu','depart_localisation','arrivee_IDarret',
                       'arrivee_IDlieu','arrivee_localisation',]
        listeDonnees=[]
        for key in listeChamps:
            if key in self.dictAller:
                listeDonnees.append((key,self.dictAller[key]))
        self.ctrl_saisie_retour.RemplitChamps(listeDonnees)

    def SwapDictAller(self,depart,arrivee):
        temp = self.dictAller[depart]
        self.dictAller[depart]=self.dictAller[arrivee]
        self.dictAller[arrivee]=temp
        return dict

    def OnBoutonOk(self, event):
        # Validation des données
        if self.Validation() == False :
            return
        # Fermeture sans sauvegarde
        if self.modeVirtuel == True :
            self.EndModal(wx.ID_OK)
            return
        # Sauvegarde
        DB = GestionDB.DB()
        resultat = True
        from Gest import GestionInscription
        fGest = GestionInscription.Forfaits(self,DB=DB)
        if self.ctrl_saisie_aller.categorie == "noTransport":
            fGest.SupprimeTransport(self.IDtranspAller)
            if self.existAller:
                DB.ReqMAJ("matPieces", [("pieIDtranspAller",0),],"pieIDtranspAller",self.IDtranspAller , MsgBox="Transport raz matPieces")

            self.ctrl_saisie_aller.IDtransport = 0
        else:
            resultat = self.ctrl_saisie_aller.Sauvegarde(mode="unique", )
        resultatRetour = True
        if self.ctrl_saisie_retour.categorie == "noTransport":
            fGest.SupprimeTransport(self.IDtranspRetour)
            if self.existRetour:
                DB.ReqMAJ("matPieces", [("pieIDtranspRetour",0),],"pieIDtranspRetour",self.IDtranspRetour , MsgBox="Transport raz matPieces")
            self.ctrl_saisie_retour.IDtransport = 0
        else:
            resultatRetour = self.ctrl_saisie_retour.Sauvegarde(mode="unique", )

        # vérif au passage de la présence d'anomalies
        req = "DELETE FROM transports WHERE IDindividu IS NULL ;"
        DB.ExecuterReq(req,commit=True,MsgBox="Purge transports null")
        DB.Close()
        if resultat and resultatRetour == True :
            self.EndModal(wx.ID_OK)
            return
        else:
            msg = GestionDB.Messages()
            msg.Box(message = "Problème avec l'enregistrement des transports !")
            self.EndModal(wx.ID_CANCEL)

    def OnBoutonAnnuler(self, event):
        if self.Validation() == False :
            mess = "L'anomalie reste en l'état\n\n"
            mess += "Il vous faudra corriger l'erreur sur transport puis valider votre saisie"
            wx.MessageBox(mess,"Incohérence",style=wx.ICON_ERROR)
        self.EndModal(wx.ID_CANCEL)

    def GetDictDonnees(self,dictDonnees):
        dictDonnees["IDtranspAller"] = self.ctrl_saisie_aller.GetIDtransport()
        prix = self.ctrl_prixAller.GetValue()
        prix = prix.replace(' ','')
        if prix == "" : prix = 0.00
        if prix != "None": dictDonnees["prixTranspAller"] = float(prix)
        else: dictDonnees["prixTranspAller"] = 0.00
        dictDonnees["IDtranspRetour"] = self.ctrl_saisie_retour.GetIDtransport()
        prix = self.ctrl_prixRetour.GetValue()
        prix = prix.replace(' ','')
        if prix == "" : prix = 0.00
        if prix != "None": dictDonnees["prixTranspRetour"] = float(prix)
        else: dictDonnees["prixTranspRetour"] = 0.00
        return dictDonnees

    def Validation(self):
        # Validation de la saisie
        resultatAller = self.ctrl_saisie_aller.Validation()
        resultatRetour = self.ctrl_saisie_retour.Validation()
        resultat = resultatAller and resultatRetour
        dd = self.GetDictDonnees(self.dictDonnees)
        noAller = self.ctrl_saisie_aller.categorie == "noTransport"
        noRetour = self.ctrl_saisie_retour.categorie == "noTransport"
        if dd["prixTranspAller"] > 0.0 and noAller:
            wx.MessageBox("Facturer un aller, sans le définir est impossible!")
            resultat = False
        if dd["prixTranspRetour"] > 0.0 and noRetour:
            wx.MessageBox("Facturer un retour, sans le définir est impossible!")
            resultat = False

        if noAller and self.IDtranspAller > 0:
            wx.MessageBox("La trace d'un ancien aller disparaîtra par la validation")
        if noRetour and self.IDtranspRetour > 0:
            wx.MessageBox("La trace d'un ancien retour disparaîtra par la validation")
        return resultat

if __name__ == "__main__":
    app = wx.App(0)
    listeDonnees = [
        ("IDinscription", None),
        ("IDindividu", 14522),
        ("IDfamille", 6163),
        ("origine", "modif"),
        ("IDnumPiece", 14459),
        ("etat", "00000"),
        ("IDactivite", 221),
        ("IDgroupe", 442),
        ("IDcategorie_tarif", 795),
        ("IDcompte_payeur", 6163),
        ("date_inscription", "2016-01-01"),
        ("parti", False),
        ("nature", "COM"),
        ("IDtranspAller", 494),
        ("prixTranspAller", 50.50),
        ("IDtranspRetour", 495),
        ("prixTranspRetour", 90.10),
        ("nom_activite", "Sejour 41 Mon activite"),
        ("nom_groupe", "Groupe Pasto Plus"),
        ("nom_payeur", "celui qui paye"),
        ("nom_categorie_tarif", "Tarif Normal"),
        ("nom_individu", "nom de  l'individu"),
        ("commentaire", "differents commentaires"),
        ("nom_famille", "nom de la famille"),
        ("lignes_piece",[{'utilisateur': 'NoName', 'quantite': 1.0, 'montant': 800.0, 'codeArticle': 'SEJ_CORSE_S1', 'libelle': 'Sejour Jeunes Corse S1', 'IDnumPiece': 10, 'prixUnit': 500.0, 'date': '2016-07-27', 'IDnumLigne': 190}, {'utilisateur': 'NoName', 'quantite': 1.0, 'montant': 10.0, 'codeArticle': 'ZLUN', 'libelle': 'Option lunettes de soleil', 'IDnumPiece': 10, 'prixUnit': 10.0, 'date': '2016-07-27', 'IDnumLigne': 191}, {'utilisateur': 'NoName', 'quantite': 1.0, 'montant': 90.0, 'codeArticle': 'ART4', 'libelle': 'Quatrieme article', 'IDnumPiece': 10, 'prixUnit': 90.0, 'date': '2016-07-27', 'IDnumLigne': 192}]),
        ]
    dictDonnees = {}
    listeChamps = []
    listeValeurs = []
    for donnee in listeDonnees:
        champ = donnee[0]
        valeur = donnee[1]
        dictDonnees[champ] = valeur
        listeChamps.append(champ)
        listeValeurs.append(valeur)

    dlg = DlgTransports(dictDonnees)
    app.SetTopWindow(dlg)
    dlg.ShowModal()
    app.MainLoop()