#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#-----------------------------------------------------------
# Derive de DLG_Appliquer_forfait.py class Forfaits
# pour gerer l'enregistrement des inscriptions
# Application :    Matthania
# Auteur:          Jacques Brunel
# Traitement des factures pieces prestations en contexte facturation
# -----------------------------------------------------------

from Utils.UTILS_Traduction import _
import wx
import FonctionsPerso as fp
import datetime
import GestionDB
from Data import DATA_Tables
from Gest import GestionInscription
from Gest import GestionArticle
from Ol import OL_FacturationPieces
from Ctrl import CTRL_ChoixListe

def Transport(xxx_todo_changeme):
    (aller,retour) = xxx_todo_changeme
    prix = 0.00
    if aller != None: prix += aller
    if retour != None: prix += retour
    return prix

def Nz(valeur):
    if valeur == None:
        valeur = 0
    return valeur

def Decod(valeur):
    retour = GestionDB.Decod(valeur)
    return valeur

def Supprime_accent(self, texte):
    liste = [("/", " "), ("\\", " "),(":", " "),(".", " "),(",", " "),("<", " "),(">", " "),("*", " "),("?", " ")]
    for a, b in liste :
        texte = texte.replace(a, b)
    liste = [ ("é", "e"), ("è", "e"), ("ê", "e"), ("ë", "e"), ("ä", "a"), ("à", "a"), ("û", "u"), ("ô", "o"), ("ç", "c"), ("î", "i"), ("ï", "i")]
    for a, b in liste :
        texte = texte.replace(a, b)
        texte = texte.replace(a.upper(), b.upper())
    return texte

# Forfaits dans le sens de definition des consommations forfaitisées par un prix de camp
class Forfaits():
    def __init__(self,parent,DB=None):
        self.parent = parent
        if not DB:
            DB = GestionDB.DB()
        self.fGest = GestionInscription.Forfaits(self.parent,DB=DB)
        self.IDuser = DB.IDutilisateurActuel()

    def AjoutInscription(self,dictDonnees) :
        # anomalie de perte d'inscription à recreer à partir de pièce
        self.listeDonneesInscriptions = []
        IDactivite = dictDonnees["IDactivite"]
        IDgroupe = dictDonnees["IDgroupe"]
        # Récupération des inscriptions à créer
        listeInscriptions = []
        # Sauvegarde des inscriptions
        DB = GestionDB.DB()
        listeDonnees = [
            ("IDindividu",  dictDonnees["IDindividu"]),
            ("IDfamille",  dictDonnees["IDfamille"]),
            ("IDactivite",  dictDonnees["IDactivite"]),
            ("IDgroupe",  dictDonnees["IDgroupe"]),
            ("IDcategorie_tarif",  dictDonnees["IDcategorie_tarif"]),
            ("IDcompte_payeur",  dictDonnees["IDcompte_payeur"]),
            ("date_inscription",  dictDonnees["dateCreation"]),
            ("parti", 0)
            ]
        # Insertion des données
        DB.ReqInsert("inscriptions", listeDonnees,retourID=True, MsgBox="AjoutInscription")
        IDinscription = DB.newID
        DB.Close()
        return IDinscription
        #fin AjoutInscription

    def CoherenceParrainages(self,IDfamille,forcerGestion=False,DB=None):
        # recherche des parrainages acquis dans les pièces de la famille, forcer passe en mode muet
        self.forcerGestion = forcerGestion
        req = """
            SELECT  matPieces.pieIDinscription, min(matPieces.pieDateCreation), min(matPieces.pieIDfamille), individus.nom, 
                    individus.prenom, Sum(matPiecesLignes.ligMontant), activites.abrege
            FROM    (matPieces 
                    LEFT JOIN individus ON matPieces.pieIDindividu = individus.IDindividu) 
                    LEFT JOIN matPiecesLignes ON matPieces.pieIDnumPiece = matPiecesLignes.ligIDnumPiece
                    LEFT JOIN activites ON matPieces.pieIDactivite = activites.IDactivite
            WHERE (((   matPieces.pieIDparrain= %d) AND (matPieces.pieParrainAbandon = 0))
                        OR ((matPieces.pieIDfamille = %d) AND (matPieces.pieParrainAbandon <> 0)))
                    AND (matPieces.pieNature <> 'AVO')                 
            GROUP BY matPieces.pieIDinscription, individus.nom,individus.prenom,activites.abrege;
            """ %(IDfamille,IDfamille)
        retour = DB.ExecuterReq(req, MsgBox="GestionPiece.CoherenceParrainages1")
        dicInscriptions = {}
        lstInscr = []
        lstChampsInscr = ["date", "famille", "activite", "nom", "prenom", "montant"]
        if retour == "ok":
            recordset = DB.ResultatReq()
            for IDinscription, dteInscr, IDfamilleInscr, nom, prenom, mttInscr, activite in recordset:
                dicInscriptions[IDinscription] = [dteInscr, IDfamille, activite, nom, prenom,  mttInscr]
                lstInscr.append(str(IDinscription))

        # recherche des parrainages imputés dans les lignes de pièces
        req = """
            SELECT  matPiecesLignes.ligIDnumLigne, matPieces.pieDateCreation, matPieces.pieDateFacturation, matPieces.pieNature, 
                    matPiecesLignes.ligCodeArticle, matPiecesLignes.ligLibelle, matPiecesLignes.ligMontant
            FROM    matPiecesLignes 
                    INNER JOIN matPieces ON matPiecesLignes.ligIDnumPiece = matPieces.pieIDnumPiece
            WHERE ((matPiecesLignes.ligCodeArticle Like '$$PARR%%') OR (matPiecesLignes.ligLibelle Like '%%parrain%%'))
                    AND (matPieces.pieIDfamille= %d) 
            ;
            """ %(IDfamille)
        retour = DB.ExecuterReq(req, MsgBox="GestionPiece.CoherenceParrainages2")
        dicLignes = {}
        lstChampsLigne = None
        if retour == "ok":
            recordset2 = DB.ResultatReq()
            lstChampsLigne = ["date", "nature", "article", "libelle", "montant"]
            for IDnumLigne,dteCrea, dteFact, nature, article, libelle, mttLigne in recordset2:
                if not dteFact or len(dteFact) == 0:
                    dteFact = dteCrea
                dicLignes[IDnumLigne] = [dteFact, nature, article, libelle, mttLigne]

        # recherche de lettrages des inscriptions des pièces parrainées dans matParrainages
        lstLignes = [str(x) for x in list(dicLignes.keys())]
        req = """
            SELECT matParrainages.parIDinscription, matParrainages.parIDligneParr, matParrainages.parSolde
            FROM matParrainages
            LEFT JOIN matPieces ON matParrainages.parIDinscription = matPieces.pieIDinscription
            WHERE ((matPieces.pieIDinscription In (%s))
                    OR (matParrainages.parIDligneParr In (%s)))
            GROUP BY matParrainages.parIDinscription, matParrainages.parIDligneParr,matParrainages.parSolde;
            """ %(str(lstInscr)[1:-1],str(lstLignes)[1:-1])
        retour = DB.ExecuterReq(req, MsgBox="GestionPiece.CoherenceParrainages3")
        dicLettrages = {}
        lstLignes = []
        if retour == "ok":
            recordset3 = DB.ResultatReq()
            for IDinscription,IDligne, solde in recordset3:
                if not IDinscription in list(dicLettrages.keys()):
                    dicLettrages[IDinscription] = []
                dicLettrages[IDinscription].append((IDligne,solde))
                lstLignes.append(IDligne)

        # Liste des parrainages correctement affectés
        lstInscrOK = []
        lstLigneOK = []
        for IDinscription in list(dicInscriptions.keys()):
            if IDinscription in list(dicLettrages.keys()):
                #inscription dans lettrage
                for (IDnumLigne,solde) in dicLettrages[IDinscription]:
                    if IDnumLigne == None or IDnumLigne == 0:
                        # inscription non encore affectée
                        lstInscrOK.append(IDinscription)
                    elif IDnumLigne in list(dicLignes.keys()):
                        # inscription affectée dans une ligne présente
                        if not IDnumLigne in lstLigneOK :
                            lstLigneOK.append(IDnumLigne)
                        lstInscrOK.append(IDinscription)
        lstInscrKO = [x for x in list(dicInscriptions.keys()) if (x not in lstInscrOK)]
        lstLigneKO = [x for x in list(dicLignes.keys()) if (x not in lstLignes)]

        # lettrages manquants rapprochement automatique par les radicaux des prenoms, complète matParrainages
        newLettres = []
        if len(lstInscrKO) * len(lstLigneKO) >0:
            for IDinscription in lstInscrKO:
                dteInscr, IDfamille, activite, nom, prenom,  mttInscr = dicInscriptions[IDinscription]
                mots = prenom.split(' ')
                stop = False
                for mot in mots:
                    mot = mot.strip().upper()
                    for IDnumLigne in lstLigneKO:
                        dteFact, nature, article, libelle, mttLigne = dicLignes[IDnumLigne]
                        if mot in libelle.upper() and dteInscr <= dteFact:
                            # l'affectation est postérieure et contient le prénom
                            newLettres.append((IDinscription,IDnumLigne))
                            if not IDinscription in list(dicLettrages.keys()):
                                dicLettrages[IDinscription] = []
                            dicLettrages[IDinscription].append((IDnumLigne,999))
                            stop = True
                            break
                    if stop : break

        # correction de parrainage
        mess1 = ""
        k = 0
        for IDinscription, IDnumLigne in newLettres:
            lstLigneKO.remove(IDnumLigne)
            lstLigneOK.append(IDnumLigne)
            lstInscrKO.remove(IDinscription)
            lstInscrOK.append(IDinscription)
            ret = DB.ReqInsert('matParrainages', [('parIDligneParr', IDnumLigne),
                                            ('parIDinscription', IDinscription),
                                            ('parSolde', 999)],
                                retourID=False,
                                MsgBox='Insert matParrainages clé: %d - %d ' %(IDinscription, IDnumLigne))
            if ret == "ok" : k =+ 1

        if k>0 : mess1 += ",\n\nLettrages automatiques ajoutés : %d"%k

        #purge des lignes de parrainages orphelines de lignes piece censées être imputées
        k=0
        for IDinscription, lstLigneSolde in dicLettrages.items():
            for IDnumLigne,solde in lstLigneSolde:
                if IDnumLigne in lstLigneKO or IDinscription in lstInscrKO:
                    req = """ DELETE FROM matParrainages
                              WHERE parIDinscription  = %d AND parIDligneParr = %d;"""%(IDinscription,IDnumLigne)
                    ret = DB.ExecuterReq(req, MsgBox="GestionPiece.CoherenceParrainages4")
                    if ret == "ok": k+=1
        if k >0 : mess1 += "\n\nLettrages erronés supprimés : %d"%k

        if len(lstLigneKO) >0:
            mess1 += "\n\nREDUCTIONS ORPHELINES d'un parrainage :"
            for ID in lstLigneKO:
                dteFact, nature, article, libelle, mttLigne = dicLignes[ID]
                mess1 += "\n     - %s" % libelle
        ret = wx.ID_ABORT
        if mess1 != "" and not self.forcerGestion:
            mess1 += '\n\nVoulez-vous voir les parrainages et les lettrages?'
            mess = GestionDB.Messages()
            ret = mess.Box("Cohérence parrainages",mess1,YesNo=True)
        # Gestion des parrainages à l'écran
        lstLettrages = []
        for IDinscription, lstLigneSolde in dicLettrages.items():
            for IDligne, solde in lstLigneSolde:
                lstLettrages.append((IDinscription, IDligne, solde))
        intro = "Le délettrage dissocie des débits et crédits qui n'auraient pas dû l'être, "
        intro += "le lettrage permet de classer les lignes qui n'apparaîtront plus après facturation des réductions."
        lstLettragesOrigine = [x for x in lstLettrages]
        dlg = CTRL_ChoixListe.DialogLettrage(self, dicInscriptions, lstChampsInscr, dicLignes, lstChampsLigne,
                                              lstLettrages, columnSort=5,
                                              intro=intro,
                                              titre="Lettrage des parrainages",
                                              minSize=(1100, 700))
        # appel du programme de lettrage
        if ret == wx.ID_OK or self.forcerGestion:
            # Action de lettrage manuel
            ret = dlg.ShowModal()

        # interventions sur les données
        if ret == wx.ID_OK or self.forcerGestion:
            lstLettragesNew = dlg.GetLettrage()
            # Suppression des anciennes associations inscription%réduction
            for lettre in lstLettrages :
                if lettre in lstLettragesNew:
                    lstLettragesNew.remove(lettre)
                else:
                    self.DissocieParrainage(DB,IDnumLigne)
            # Ajout des parrainages associés par lettrage
            for IDinscription, IDnumLigne, affecte in lstLettragesNew :
                self.AssocieParrainage(DB,IDinscription, IDnumLigne, affecte)
        dlg.Destroy()
        #fin coherenceParrainages

    def AssocieParrainage(self,DB,IDinscription,IDnumLigne, affecte):
        if not IDnumLigne: IDnumLigne = 0
        if not IDinscription: IDinscription = 0
        lstDonnees = [('parIDinscription', IDinscription),
                      ('parIDligneParr', IDnumLigne),
                      ('parSolde', affecte ),]
        ret = DB.ReqInsert('matParrainages', lstDonnees, retourID=False)
        if ret != "ok":
            mess = "Erreur d'écriture dans matParrainages!\n\n"
            mess += str(ret)
            wx.MessageBox(message=mess)

    def DissocieParrainage(self,DB,IDnumLigne=None):
        # suppression des associations propre à l'inscription
        if IDnumLigne:
            # cas où la ligne de la réduc parrainage est connue
            req = """   DELETE FROM matParrainages
                        WHERE parIDligneParr = %d
                        ;""" % (IDnumLigne)
            DB.ExecuterReq(req, MsgBox="GestionPiece.DissocieParrainage1")
        else:
            # cas général les inscriptions parrainées doivent être dans au moins une pièce
            req = """
                SELECT matParrainages.parIDinscription
                FROM matParrainages LEFT JOIN matPieces ON matParrainages.parIDinscription = matPieces.pieIDinscription
                WHERE (((matParrainages.parIDinscription)<>0))
                GROUP BY matParrainages.parIDinscription
                HAVING (((Count(matPieces.pieIDparrain))=0));
                ;"""
            ret = DB.ExecuterReq(req, MsgBox="GestionPiece.DissocieParrainage2")
            if ret == 'ok':
                recordset = DB.ResultatReq()
                if len(recordset)>0:
                    lst = [ str(x) for (x,) in recordset]
                    req = """
                        DELETE
                        FROM matParrainages
                        WHERE parIDinscription IN (%s)
                        ;""" %','.join(lst)
                    DB.ExecuterReq(req, MsgBox="GestionPiece.DissocieParrainage3")

        return

    def GenereAvoir(self,dictDonnees):
        # Création d'une facture d'avoir sur la pièce facturée
        end = wx.ID_OK
        delConsos = True
        # Calcul des champs de la table facture
        activites,individus = [],[]
        activites.append(dictDonnees["IDactivite"])
        individus.append(dictDonnees["IDindividu"])
        def listeChaine(maListe):
            chaine = ""
            for item in maListe:
                chaine = chaine + str(item) +";"
            chaine = chaine[:-1]
            return chaine
        numero = GestionInscription.GetNoFactureSuivant()
        DB = GestionDB.DB()
        self.IDuser = DB.IDutilisateurActuel()
        transports = Nz(dictDonnees["prixTranspAller"])+Nz(dictDonnees["prixTranspRetour"])
        montant = 0.00
        listeLignes = dictDonnees["lignes_piece"]
        for dictLigne in listeLignes:
            if dictLigne["montant"] == 0:
                montant -=  dictLigne["quantite"] * dictLigne["prixUnit"]
            else: montant -= dictLigne["montant"]
        montant -= transports
        today = datetime.date.today()
        dteFac = GestionDB.DateEngEnDateDD(dictDonnees["dateFacturation"])
        exDeb,exFin = DB.GetExercice(dteFac, alertes="date exercice de la facture", approche=True)
        if today <= exFin:
            dictDonnees["dateAvoir"] = str(today)
        else :
            dictDonnees["dateAvoir"] = str(exFin)
        # Composition de l'enregistrement facture
        listeDonnees = [
            ("numero",numero ),
            ("IDcompte_payeur", dictDonnees["IDcompte_payeur"]),
            ("date_edition", dictDonnees["dateAvoir"]),
            ("date_echeance", dictDonnees["dateAvoir"]),
            ("IDutilisateur", self.IDuser),
            ("IDlot", 2),
            ("prestations", "consoavoir"),
            ("etat", None),
            ("activites",listeChaine(activites)),
            ("individus",listeChaine(individus)),
            ("date_debut",datetime.date.today()),
            ("date_fin",datetime.date.today()),
            ("total",montant),
            ("regle",0.0),
            ("solde",montant),
            ]
        retour = DB.ReqInsert("factures", listeDonnees, retourID=False)
        IDnumAvoir = DB.newID
        if retour != "ok" :
            GestionDB.MessageBox(self,retour)
            return wx.ID_ABORT
        dictDonnees["IDnumAvoir"] = IDnumAvoir
        dictDonnees["noAvoir"] = numero
        dictDonnees["etat"] = dictDonnees["etat"][0:4]+"1"
        commentaire = Decod(dictDonnees["commentaire"])
        commentaire = "%s Generation Avoir Piece\n%s" %(datetime.date.today().strftime("%d/%m/%y : "), commentaire)
        dictDonnees["commentaire"] = commentaire

        # Ecriture du numéro d'avoir dans la piece, pas dans la prestation
        self.MajNoAvoir(self,dictDonnees)

        #generation d'une prestation avoir
        dictDonnees["IDavoir"] = IDnumAvoir
        IDprestation = dictDonnees["IDprestation"]
        dicoDB = DATA_Tables.DB_DATA
        lstChamps = []
        for descr in dicoDB["prestations"]:
            nomChamp = descr[0]
            lstChamps.append(nomChamp)
        if IDprestation != None:
            retour = DB.ReqSelect("prestations", "IDprestation = %s ;"% IDprestation)
            if retour != "ok" :
                GestionDB.MessageBox(self,retour)
            retour = DB.ResultatReq()
            lstDictPrest = GestionInscription.RecordsToListeDict(lstChamps,retour)
            #RecordsToListeDict retourne une liste de tuples, où [0] est le premier champ de la table (l'ID) et [1] le dictionnaire de tous les champs
            if len(lstDictPrest) >0:
                DictPrest = lstDictPrest[0][1]
                DictPrest["date"] = dictDonnees["dateAvoir"]
                DictPrest["montant"] = -float(DictPrest["montant"])
                DictPrest["montant_initial"] = -float(DictPrest["montant_initial"])
                DictPrest["label"] = "Avoir "+ DictPrest["label"]
                DictPrest["categorie"] = "consoavoir"
                DictPrest["IDfacture"] = IDnumAvoir
                lstChamps.remove("IDprestation")
                lstChamps.remove("compta")
                listeDonnees = GestionInscription.DictToListeTuples(lstChamps,DictPrest)
                ret = DB.ReqInsert("prestations",listeDonnees,retourID=True,)
            else: GestionDB.MessageBox(self,"La Prestation associée à la pièce est introuvable,\n impossible de générer la prestation d'avoir")
        # Suppression ventilations
        DB.ReqDEL("deductions", "IDprestation", IDprestation)
        DB.ReqDEL("ventilation", "IDprestation", IDprestation)

        # Suppression consommations
        if delConsos:
            IDinscription = dictDonnees["IDinscription"]
            if IDinscription != None:
                DB.ReqDEL("consommations", "IDinscription", IDinscription)
        # Propose la suppression des transports
        sens = None
        if dictDonnees["IDtranspAller"] > 0:
            sens = "aller"
            txt = "un transport Aller précédent"
        if dictDonnees["IDtranspRetour"] > 0:
            if sens == None:
                sens = "retour"
                txt = "un transport Retour précédent"
            else:
                sens = "deux"
                txt = "deux transports précédents"

        if sens != None:
            listeTuples=[(1,"Supprimer %s" % txt)]
            listeTuples.append((2,"Conserver %s,\n     non facturés mais toujours présents dans les listes" % txt))
            ret = GestionDB.Messages().Choix(listeTuples=listeTuples, titre = ("Cet individu était dans les listes de transport"), intro = "Double clic pour choisir  !")
            ixChoix = ret[0]
            if  ixChoix != None:
                if ixChoix == 1:
                    self.fGest.RazTransport(self,dictDonnees,sens)
        return end
        #fin GenereAvoir

    def ReduitAvoir(self,numero,montant,IDprestation):
        # Modification dela valeur  d'une facture d'avoir existante, cas d'un correctif famille
        # Calcul des champs de la table facture
        DB = GestionDB.DB()
        req = """SELECT total, regle, solde
            FROM factures
            WHERE numero = %s;
            """ % (numero)
        DB.ExecuterReq(req,MsgBox="ReduitFacture " + str(numero))
        recordset = DB.ResultatReq()
        for total,regle, solde in recordset:
            nvTotal = Nz(total)-Nz(montant)
            nvRegle = Nz(regle)-Nz(montant)
            if nvRegle < 0:
                nvRegle = 0
            nvSolde = Nz(solde)-Nz(montant)
            if nvSolde < 0:
                nvSolde = 0
            if nvSolde != nvTotal - nvRegle:
                #recalcul du solde
                req = """SELECT sum(montant)
                    FROM ventilation
                    WHERE IDprestation = %s;
                    """ % (IDprestation)
                DB.ExecuterReq(req,MsgBox="GestionPiece.ReduitFactAvoir.calculSolde ")
                recordset = DB.ResultatReq()
                for mtRegle in recordset[0]:
                    nvRegle = Nz(mtRegle)
                    nvSolde = nvTotal- Nz(mtRegle)
            DB.ReqMAJ('factures',[('total',nvTotal),('regle',nvRegle),('solde',nvSolde)],'numero',numero,MsgBox="GestionPieces.ReduitFactAvoir")
        #fin ReduitAvoir

    def FactureMonoPiece(self,numero,IDnumPiece):
        DB = GestionDB.DB()
        # ctrl de présence d'autre pieces pointant la même facture
        req = """SELECT Count(pieIDnumPiece)
            FROM matPieces
            WHERE (pieIDnumPiece <> %s) AND ((pieNoFacture= %s) OR (pieNoAvoir) <> %s );
            """ % (IDnumPiece, numero, numero)
        DB.ExecuterReq(req,MsgBox="Autres Pieces sur facture " + str(numero))
        recordset = DB.ResultatReq()
        nbre = Nz(recordset[0][0])
        if nbre == 0:
            retFin = True
        else:
            retFin = False
        DB.Close()
        return retFin
        #fin FactureMonoPiece

    def ReduitFacture(self,numero,montant,IDprestation):
        # diminue le montant de la facture et supprime la ventilation de la prestation (contexte mono piece dans la facture)
        DB = GestionDB.DB()
        req = """SELECT total, regle, solde
            FROM factures
            WHERE numero = %s;
            """ % (numero)
        DB.ExecuterReq(req,MsgBox="ReduitFacture " + str(numero))
        recordset = DB.ResultatReq()
        i=0
        for total,regle, solde in recordset:
            i += 1
            if i==1 :
                nvTotal = round(Nz(total)-Nz(montant),2)
                nvRegle = round(Nz(regle)-Nz(montant),2)
                if nvRegle < 0.0:
                    nvRegle = 0.0
                nvSolde = Nz(solde)-Nz(montant)
                if nvSolde < 0.0:
                    nvSolde = 0.0
                if nvSolde != nvTotal - nvRegle:
                    #recalcul du solde
                    req = """SELECT sum(montant)
                        FROM ventilation
                        WHERE IDprestation = %s;
                        """ % (IDprestation)
                    DB.ExecuterReq(req,MsgBox="GestionPiece.ReduitFacture.calculSolde ")
                    recordset = DB.ResultatReq()
                    for mtRegle in recordset[0]:
                        nvRegle = Nz(mtRegle)
                        nvSolde = nvTotal- Nz(mtRegle)
                DB.ReqMAJ('factures',[('total',nvTotal),('regle',nvRegle),('solde',nvSolde)],'numero',numero,MsgBox="GestionPieces.ReduitFacture")
        if i == 1:
            if (nvTotal == 0.0):
                DB.ReqDEL('factures','numero',numero,MsgBox="GestionPieces.ReduitFactureSupprime")
        else :
            if i > 1 :
                texte =  " n'est pas unique \nUne analyse est nécessaire \n"
            else:
                texte =  " n'est pas trouvé \nUne analyse est nécessaire \n"
            mess = GestionDB.Messages()
            mess.Box(titre = "Problème de cohérence", message= "\n La facture de numéro " + str(numero) + texte)
        DB.Close()
        return
        #fin ReduitFacture

    def AugmenteFacture(self,numero,montant,IDprestation):
        lstIDprestations = []
        lstIDprestations.append(IDprestation)
        # Augmente le montant de la facture (contexte famille ajouté à un avoir sur activité dans la facture)
        DB = GestionDB.DB()
        req = """SELECT IDfacture, total, regle, solde
            FROM factures
            WHERE numero = %s;
            """ % (numero)
        DB.ExecuterReq(req,MsgBox="ModifFacture " + str(numero))
        recordset = DB.ResultatReq()
        i=0
        for IDfacture, total,regle, solde in recordset:
            self.IDfacture = IDfacture
            i += 1
            if i==1 :
                # récupération des autres prestations associées au numero facture
                req = """SELECT IDprestation
                    FROM prestations
                    WHERE IDfacture = %s;
                    """ % (IDfacture)
                DB.ExecuterReq(req,MsgBox="ModifFacture " + str(numero))
                recordset = DB.ResultatReq()
                for (IDprest,) in recordset:
                    lstIDprestations.append(IDprest)
                # recalcul du solde
                nvTotal = round(Nz(total)-Nz(montant),2)
                nvRegle = round(Nz(regle)-Nz(montant),2)
                if nvRegle < 0.0:
                    nvRegle = 0.0
                nvSolde = Nz(solde)-Nz(montant)
                if nvSolde < 0.0:
                    nvSolde = 0.0
                if nvSolde != nvTotal - nvRegle:
                    #recalcul du solde
                    req = """SELECT sum(montant)
                        FROM ventilation
                        WHERE IDprestation in ( %s ) ;
                        """ % (fp.ListeToStr(lstIDprestations))
                    DB.ExecuterReq(req,MsgBox="GestionPiece.ReduitFacture.calculSolde ")
                    recordset2 = DB.ResultatReq()
                    for mtRegle in recordset2[0]:
                        nvRegle = Nz(mtRegle)
                        nvSolde = nvTotal- Nz(mtRegle)
                DB.ReqMAJ('factures',[('total',nvTotal),('regle',nvRegle),('solde',nvSolde)],'numero',numero,MsgBox="GestionPieces.ReduitFacture")
                for IDprestation in lstIDprestations:
                    DB.ReqMAJ('prestations',[('IDfacture',self.IDfacture),],'IDprestation',IDprestation,MsgBox = 'Modif IDfacture en prestations')
        if i != 1:
            if i > 1 :
                texte =  " n'est pas unique \nUne analyse est nécessaire \n"
            else:
                texte =  " n'est pas trouvé \nUne analyse est nécessaire \n"
            mess = GestionDB.Messages()
            mess.Box(titre = "Problème de cohérence", message= "\n La facture de numéro " + str(numero) + texte)
        DB.Close()
        return
        #fin Augmente Facture

    def DestroyFacture(self,numero,IDcomptePayeur):
        DB = GestionDB.DB()
        retFin = False
        # ctrl d'unicité du numero facture entre tiers différents
        req = """SELECT Count(factures.IDfacture)
            FROM factures
            WHERE (factures.numero= %s) AND (factures.IDcompte_payeur) <> %s ;
            """ % (numero, IDcomptePayeur)
        DB.ExecuterReq(req,MsgBox="Ctrl Unicite Facture " + str(numero))
        recordset = DB.ResultatReq()
        nbre = Nz(recordset[0][0])
        if nbre > 0:
            GestionDB.MessageBox(self.parent,"\n LE NUMERO DE FACTURE " + str(numero) + " EST UTILISE PAR UN AUTRE TIERS \nUne analyse est nécessaire avant de corriger \n")
        else:
            retour = DB.ReqDEL("factures","numero",numero,MsgBox = "GestionPieces.DestroyFacture")
            if retour == "ok":
                retFin = True
        DB.Close()
        return retFin
        #fin DestroyFacture

    def CreeFacture(self,IDcomptePayeur,lstIDpieces,IDuser,preExiste = False, retourID = False):
        # Création d'une facture avec toutes les pièces de la liste

        DB = GestionDB.DB()
        listDictDon = []
        datesFacture = []
        # Champs de la table facture
        activites = []
        inscriptions = []
        individus = []
        date_debut = "2999-01-01"
        date_fin =  "1900-01-01"
        total = 0.00
        regle = 0.00
        echeance = None
        lstSuppr = []
        lstSupprID = []
        dateFacturation = wx.ID_ABORT
        retour = False

        # analyse préalable
        for IDpiece in lstIDpieces:
            self.fGest.GetPieceModif(self,None,None,IDnumPiece=IDpiece)
            dictDonnees = self.fGest.dictPiece
            # constitution de la liste des données sous forme dictionnaire
            listDictDon.append(dictDonnees)
            ligne = OL_FacturationPieces.Track(dictDonnees)
            if ligne.IDactivite > 0:
                activite = ligne.IDactivite
                inscription = 0
                dd = GestionArticle.DebutOuvertures(DB, ligne.IDactivite, ligne.IDgroupe)
                if echeance == None:
                    echeance = dd
                else:
                    if echeance > dd: echeance = dd
            else:
                inscription = ligne.IDinscription
                activite = 0
            date, exercice = DB.GetDateFacture(inscription, activite,
                                               datetime.date.today(), alertes=False,
                                               retourExercice=True)
            if exercice == (None, None):
                # l'exercice n'est pas encore ouvert pour cette ligne
                GestionDB.Messages().Box(titre="Exercices comptables",
                                         message="Présence d'une pièce se rapportant à un exercice non ouvert\nSa facturation n'est pas possible")
                lstSuppr.append(dictDonnees)
                lstSupprID.append(IDpiece)
                continue
            inscriptions.append(inscription)
            activites.append(activite)
            if not (date in datesFacture):
                datesFacture.append(date)
            if ligne.IDindividu > 0: individus.append(ligne.IDindividu)
            if ligne.dateModif < date_debut:
                date_debut = ligne.dateModif
            if ligne.dateModif > date_fin:
                date_fin = ligne.dateModif
            if ligne.total != None: total += ligne.total
            total += Transport((ligne.prixTranspAller, ligne.prixTranspRetour))
            ligne.mttRegle = 0

        if len(lstSuppr) > 0:
            for dic in lstSuppr:
                listDictDon.remove(dic)
            for IDpiece in lstSupprID:
                lstIDpieces.remove(IDpiece)

        if len(datesFacture) != 1 or datesFacture[0] == None:
            # plusieurs dates de facturation sont possibles
            echeance = None
            ix = 2
            listeChoix = [(1, "Date du jour   : " + str(datetime.date.today()))]
            listeDates = [datetime.date.today()]
            if len(datesFacture) == 0:
                retour = False
            for date in datesFacture:
                if date != datetime.date.today() and date != None:
                    listeChoix.append((ix, "Date d'activité : " + str(date)))
                    listeDates.append(date)
                    ix += 1
            retour = GestionDB.Messages().Choix(listeChoix,
                                                "Cet ensemble de pièces, est censé être facturé à des dates différentes\nQuel est votre choix?")
            if retour[0] == None:
                retour = False
            else:
                dateFacturation = listeDates[retour[0] - 1]
                retour = True
                if DB.GetExercice(dateFacturation, alertes=True) == (None, None):
                    # l'exercice n'est pas ouvert pour la date choisie
                    GestionDB.Messages().Box(titre="Exercices comptables",
                                             message="Pas d'exercice ouvert pour la date choisie\nLa facture n'est pas possible")
                    retour = False
        else:
            dateFacturation = datesFacture[0]
            retour = True

        if dateFacturation == wx.ID_ABORT:
            # abandon lors du choix de dates
            retour = False

        # sortie sur echec
        if not retour or not dateFacturation:
            DB.Close()
            return False

        # début des modifs
        for IDpiece in lstIDpieces:
            dictDonnees = listDictDon[lstIDpieces.index(IDpiece)]
            #les devis n'avaient pas enregistré les consommations
            if dictDonnees["nature"] == "DEV" and dictDonnees["IDactivite"] > 0 :
                self.fGest.AjoutConsommations(self.parent,dictDonnees,force=True)
            # ajout des prestations non encore enregistrées
            if dictDonnees["nature"] in ("RES","DEV"):
                dictDonnees["exnature"] = dictDonnees["nature"]
                dictDonnees["nature"] = 'FAC'
                IDprestation = self.fGest.AjoutPrestation(self.parent,dictDonnees)
                dictDonnees["IDprestation"] = IDprestation
                if IDprestation > 0 :
                    self.fGest.ModifiePieceCree(self.parent,dictDonnees)
                    self.fGest.ModifieConsoCree(self.parent,dictDonnees)
                    dictDonnees["IDprestation"] = IDprestation

        if echeance == None:
            echeance = dateFacturation + datetime.timedelta(days=30)
        else:
            echeance = echeance + datetime.timedelta(days=-30)
            if echeance < datetime.date.today():
                echeance = datetime.date.today() + datetime.timedelta(days=10)
        def listeChaine(maListe):
            chaine = ""
            for item in maListe:
                chaine = chaine + str(item) +";"
            chaine = chaine[:-1]
            return chaine
        if preExiste:
            numero = dictDonnees["noFacture"]
        else:
            numero, date = GestionInscription.GetNoFactureMin()

        # test des ventilations de réglement sur les prestations
        # Composition de l'enregistrement facture
        listeDonnees = [
            ("numero",numero ),
            ("IDcompte_payeur", IDcomptePayeur),
            ("date_edition", dateFacturation),
            ("date_echeance", str(echeance)),
            ("IDutilisateur", IDuser),
            ("IDlot", 1),
            ("prestations", "Origine Piece Facture"),
            ("etat", None),
            ("activites",listeChaine(activites)),
            ("individus",listeChaine(individus)),
            ("date_debut",date_debut),
            ("date_fin",date_fin),
            ("total",total),
            ("regle",regle),
            ("solde",(total-regle)),
            ]
        retour = DB.ReqInsert("factures", listeDonnees, retourID=False)
        if retour != "ok" :
            GestionDB.MessageBox(self.parent,retour)
            retour = False
        elif preExiste:
            retour = True
        else:
            IDfacture = DB.newID
            # Ecriture du numéro de facture dans les pieces, ecrire l'IDfacture dans les prestations.
            for dictDonnees in listDictDon:
                retour = self.MajNoFact(self.parent,dictDonnees,listeDonnees,IDfacture)
        DB.Close()
        if not retour:
            return False
        elif retourID:
            return IDfacture
        else:
            return True
        #fin CreeFacture

    def ReparAvoir(self,IDcomptePayeur,lstIDpieces,IDuser):
        # création automatique d'un avoir pour corriger incohérence
        DB = GestionDB.DB()
        # Création d'un avoir avec toutes les pièces de la liste
        listDictDon = []
        for IDpiece in lstIDpieces:
            self.fGest.GetPieceModif(self,None,None,IDnumPiece=IDpiece)
            dictDonnees = self.fGest.dictPiece
            # constitution de la liste des données sous forme dictionnaire
            listDictDon.append(dictDonnees)
        # Calcul des champs de la table facture
        activites = []
        inscriptions = []
        individus = []
        date_debut = "2999-01-01"
        date_fin =  "1900-01-01"
        total = 0.00
        regle = 0.00
        echeance = None
        def listeChaine(maListe):
            chaine = ""
            for item in maListe:
                chaine = chaine + str(item) +";"
            chaine = chaine[:-1]
            return chaine
        for dictDonnees in listDictDon:
            ligne = OL_FacturationPieces.Track(dictDonnees)
            if ligne.IDactivite > 0:
                activites.append(ligne.IDactivite)
                inscriptions.append(ligne.IDactivite)
                dd = GestionArticle.DebutOuvertures(DB,ligne.IDactivite,ligne.IDgroupe)
                if echeance == None:
                    echeance = dd
                else:
                    if echeance > dd : echeance = dd
            if ligne.IDindividu > 0:individus.append(ligne.IDindividu)
            if ligne.dateModif < date_debut:
                date_debut = ligne.dateModif
            if ligne.dateModif > date_fin:
                date_fin = ligne.dateModif
            if ligne.total != None: total -= ligne.total
            total -= Transport((ligne.prixTranspAller,ligne.prixTranspRetour))
            ligne.mttRegle = 0
            dictDonnees = {
                "IDcompte_payeur": IDcomptePayeur,
                "date_echeance": str(echeance),
                "IDutilisateur": IDuser,
                "IDlot": 1,
                "prestations": "Origine Piece Avoir",
                "etat": None,
                "activites": listeChaine(activites),
                "individus": listeChaine(individus),
                "date_debut": date_debut,
                "date_fin": date_fin,
                "total": total,
                "regle": regle,
                "solde": (total-regle),
            }
            dictDonnees["noAvoir"],dictDonnees["date_edition"] = GestionInscription.GetNoFactureMin()
            retour = DB.ReqInsert("factures", dictDonnees, retourID=False)
            if retour != "ok" :
                GestionDB.MessageBox(self.parent,retour)
                return None
            dictDonnees["IDnumAvoir"] = DB.newID
            # Ecriture du numéro de facture dans les pieces, ecrire l'IDfacture dans les prestations.
            retour = self.MajNoAvoir(self.parent,dictDonnees,prest=True)
        DB.Close()
        return True
        #fin ReparAvoir

    def CompleteAvoir(self,IDcomptePayeur,dictDonnees, montant, numero):
        DB = GestionDB.DB()
        # Cromplete un avoir au numero existant avec la pièce (cas d'un correctif niveau famille)
        #table factures
        req = """
            SELECT IDfacture,total, solde
            FROM factures
            WHERE numero = %d;
            """ %numero
        DB.ExecuterReq(req,MsgBox="CompleteAvoir ouvertures")
        recordset = DB.ResultatReq()
        for IDfacture, total, solde in recordset:
            listeDonnees = [
                ("total", total + montant ),
                ("solde", solde + montant),
                ]
            retour = DB.ReqMAJ("factures", listeDonnees,"IDfacture",IDfacture,MsgBox = "GestionPiece.CompleteAvoir")
            if retour != "ok" :
                GestionDB.MessageBox(self.parent,retour)
                return None

            #table prestations
            retour = DB.ReqMAJ("prestations", [("IDfacture",IDfacture),],"IDprestation",dictDonnees["IDprestation"],MsgBox = "GestionPiece.CompleteAvoir")
            if retour != "ok" :
                GestionDB.MessageBox(self.parent,retour)
                return None

        #table matPieces
        etat = dictDonnees['etat'][:3]+"1" + dictDonnees['etat'][4:]
        commentaire = Decod(dictDonnees["commentaire"])
        if commentaire == None: commentaire = " -\n"
        ajout = " Facturé %s " % dictDonnees['exnature']
        commentaire = datetime.date.today().strftime("%d/%m/%y : ") + ajout + "\n" + commentaire

        listeDonnees = [
            ("pieNoFacture", numero ),
            ("pieNature", "FAC"),
            ("pieEtat", etat),
            ("pieDateFacturation", dictDonnees["dateModif"]),
            ("pieCommentaire", commentaire),
            ]
        retour = DB.ReqMAJ("matPieces", listeDonnees,"pieIDnumPiece",dictDonnees["IDnumPiece"],MsgBox = "GestionPiece.CompleteAvoir")
        if retour != "ok" :
            GestionDB.MessageBox(self.parent,retour)
            return None
        DB.Close()
        return True
        #fin CompleteAvoir

    def MajNoFact(self,parent, dictPiece, listeDonneesFacture, IDnumFacture):
        DB = GestionDB.DB()
        #Après la création d'une facture mise à niveau des correspondances prestation piece
        listeChampsFacture = []
        listeValeursFacture = []
        for champ, valeur in listeDonneesFacture:
            listeChampsFacture.append(champ)
            listeValeursFacture.append(valeur)
        dictFacture = GestionInscription.DictTrack(listeChampsFacture,listeValeursFacture,"xxx")
        # modif de la pièce facturée
        etat = dictPiece['etat'][:3]+"1" + dictPiece['etat'][4:]
        commentaire = Decod(dictPiece["commentaire"])
        ajout = " Facturé %s " % dictPiece['nature']
        commentaire = GestionInscription.AjoutCom(commentaire,ajout)
        dateFacture = dictFacture["date_edition"]
        listeDonnees = [
            ("pieDateModif",str(datetime.date.today())),
            ("pieUtilisateurModif",DB.UtilisateurActuel()),
            ("pieNature","FAC"),
            ("pieEtat",etat),
            ("pieDateFacturation", dateFacture),
            ("pieNoFacture",dictFacture["numero"]),
            ("pieDateEcheance", dictFacture["date_echeance"]),
            ("pieCommentaire", commentaire),
            ]
        retour = DB.ReqMAJ("matPieces", listeDonnees,"pieIDnumPiece",dictPiece['IDnumPiece'])
        if retour != "ok" :
            GestionDB.MessageBox(parent,retour)
            DB.Close()
            return None
        self.fGest.Historise(dictPiece['IDindividu'],dictPiece['IDfamille'],'Facturation',ajout)
        # Modif de la prestation associée à la piece
        if dictPiece['IDprestation'] == None:
            if not dictPiece['nature'] in ("DEV","RES"):
                GestionDB.MessageBox(parent,"la piece %d est sans prestation associée" % dictPiece['IDnumPiece'])
            DB.Close()
            return None
        listeDonnees = [
            ("IDfacture", IDnumFacture),
            ("date", dateFacture)
            ]
        #("date", dateFacture)
        retour = DB.ReqMAJ("prestations", listeDonnees,"IDprestation",dictPiece['IDprestation'])
        if retour != "ok" :
            GestionDB.MessageBox(parent,retour)
            DB.Close()
            return None
        DB.Close()
        return True
        #fin MajNoFact

    def MajNoAvoir(self,parent, dictDonnees,prest=False):
        DB = GestionDB.DB()
        #Après la création d'un avoir mise à niveau des correspondances prestation piece
        etat = dictDonnees['etat'][:4]+"1" + dictDonnees['etat'][5:]
        ajout = " Facturé %s " % dictDonnees['nature']
        commentaire = GestionInscription.AjoutCom(Decod(dictDonnees["commentaire"]),ajout)
        listeDonnees = [
            ("pieDateModif",str(datetime.date.today())),
            ("pieUtilisateurModif",DB.UtilisateurActuel()),
            ("pieNature","AVO"),
            ("pieEtat",etat),
            ("pieDateAvoir", dictDonnees["dateAvoir"]),
            ("pieNoAvoir",dictDonnees["noAvoir"]),
            ("pieDateEcheance", dictDonnees["dateEcheance"]),
            ("pieCommentaire", commentaire),
            ]
        retour = DB.ReqMAJ("matPieces", listeDonnees,"pieIDnumPiece",dictDonnees['IDnumPiece'])
        if retour != "ok" :
            GestionDB.MessageBox(parent,retour)
            DB.Close()
            return None
        self.fGest.Historise(dictDonnees['IDindividu'],dictDonnees['IDfamille'],'Facturation',ajout)
        if prest:
            # Modif de la prestation associée à la piece
            if dictDonnees['IDprestation'] == None:
                if not dictDonnees['nature'] in ("DEV","RES"):
                    GestionDB.MessageBox(parent,"la piece %d est sans prestation associée" % dictDonnees['IDnumPiece'])
                DB.Close()
                return None
            listeDonnees = [
                ("IDfacture", dictDonnees["IDnumAvoir"]),
                ]
            retour = DB.ReqMAJ("prestations", listeDonnees,"IDprestation",dictDonnees['IDprestation'])
            if retour != "ok" :
                GestionDB.MessageBox(parent,retour)
                DB.Close()
                return None
        DB.Close()
        return True
        #fin MajNoAvoir

    def MajPiece(self,dictPiece,lstChampsMatPieces):
        listeDonnees = []
        fGest = GestionInscription
        champsDonnees = fGest.StandardiseNomsChamps(lstChampsMatPieces)
        for champ in lstChampsMatPieces:
            idx = lstChampsMatPieces.index(champ)
            donnee = champsDonnees[idx]
            listeDonnees.append((champ,dictPiece[donnee]))
        DB = GestionDB.DB()
        retour = DB.ReqMAJ("matPieces", listeDonnees,"pieIDnumPiece",dictPiece["IDnumPiece"],MsgBox="ReWritePiece")
        if retour != "ok":
            GestionDB.MessageBox(self.parent,retour)
            DB.Close()
            return None
        DB.Close()

# --------------------Lancement de test ----------------------
if __name__ == "__main__":
    app = wx.App(0)
    #app.MainLoop()
