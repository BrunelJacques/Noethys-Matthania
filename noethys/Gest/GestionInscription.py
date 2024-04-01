#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#-----------------------------------------------------------
# Derive de DLG_Appliquer_forfait.py class Forfaits
# pour gerer l'enregistrement des inscriptions
# Application :    Noethys, Matthania
# Auteur:          Ivan LUCAS, Jacques Brunel
# Traitement des inscriptions derrière la tarification
# -----------------------------------------------------------
from Utils.UTILS_Traduction import _
import wx
import datetime
import GestionDB
from Data import DATA_Tables
import GestionPieces
from Utils import UTILS_Historique


DictActions = {
    "Inscription" : 79,
    "AjoutInscription" : 79,
    "ModificationInscription" : 78,
    "SuppressionInscription" : 77,
    "Facturation" : 76,
    "AjoutFacturation" : 76,
    "AvoirGénéré": 76,
    "ModificationFacturation" : 75,
    "SuppressionFacturation" : 74,
    "MiseEnCoherence" : 73,
    "Diagnostic" : 80,
    "TransfertCompta" : 72,
    "EnvoiMail": 71,
    }

def Nz(valeur):
    if valeur == None:
        valeur = 0
    return valeur

def Decod(valeur):
    return GestionDB.Decod(valeur)

def AjoutCom(commentaire, ajout):
    if commentaire == None: commentaire = " -\n"
    commentaire = Decod(commentaire)
    return datetime.date.today().strftime("%d/%m/%y : ") + ajout + "\n" + commentaire

def DateIntToString(dateInt, format="%d/%m/%y"):
    if not isinstance(dateInt,int):
        return "noINT"
    annee = int(dateInt/10000)
    mois = int((dateInt-(annee*10000))/100)
    jour = int(dateInt - (annee*10000) - (mois*100))
    return datetime.date(annee,mois,jour).strftime(format)

def DateComplete(dateDD):
    """ Transforme une date DD en date complète : Ex : lundi 15 janvier 2008 """
    listeJours = (_("Lundi"), _("Mardi"), _("Mercredi"), _("Jeudi"), _("Vendredi"), _("Samedi"), _("Dimanche"))
    listeMois = (
    _("janvier"), _("février"), _("mars"), _("avril"), _("mai"), _("juin"), _("juillet"), _("août"),
    _("septembre"), _("octobre"), _("novembre"), _("décembre"))
    dateComplete = listeJours[dateDD.weekday()] + " " + str(dateDD.day) + " " + listeMois[dateDD.month - 1] + " " + str(
        dateDD.year)
    return dateComplete

def DateEngEnDateDD(dateEng):
    if dateEng and not isinstance(dateEng,str): dateEng = str(dateEng)
    return datetime.date(int(dateEng[:4]), int(dateEng[5:7]), int(dateEng[8:10]))

def GetNoFactureSuivant():
    DB = GestionDB.DB()
    req = "SELECT MAX(pieNoFacture),MAX(pieNoAvoir) FROM matPieces;"
    retour = DB.ExecuterReq(req,MsgBox="GestionInscription.GetNoFactureSuivant")
    if retour != "ok" :
        return
    retour = DB.ResultatReq()
    if (retour[0][0]== None) or (len(retour) == 0) : noFacture = 1
    else:
        if retour[0][1] == None:
            noAvoir = 0
        else : noAvoir = retour[0][1]
        noFacture = max(int(retour[0][0])+1,int(noAvoir)+1)
    # test de non utilisation
    test = True
    i = 0
    while test :
        req = """SELECT Count(IDfacture)
                FROM factures
                WHERE numero= %s ;
                """ % str(noFacture)
        DB.ExecuterReq(req,MsgBox="Ctrl Unicité Facture " + str(noFacture))
        recordset = DB.ResultatReq()
        nbre = recordset[0][0]
        if nbre == 0:
            # le numero est libre
            test = False
        else:
            noFacture +=1
        i += 1
        if i > 20 :
            dlg = wx.MessageDialog(None, _("Il est impossible de trouver un numero de facture ! \n\nLe programe boucle"), "Erreur", wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            break
    DB.Close
    return noFacture

def GetNoFactureMin():
    # principe : lors d'une suppression de facture le numéro et sa date sont mis dans matParams avec clé prmUser = "NoLibre",prmParam = str(numero), prmInt = numero, prmDate = dateFact
    # la recherche d'un numero trouve le plus petit prmInt et sa date puis le supprime
    # pour la date, priorité sera donnée à celle de la première ventilation associée si elle existe à une date antérieure à la facture.
    value,noFacture,date = None,None,None
    DB = GestionDB.DB()
    req = "SELECT MIN(prmInteger) FROM matParams WHERE prmUser = 'NoLibre';"
    retour = DB.ExecuterReq(req,MsgBox="GestionInscription.GetNoFactureMin")
    if retour != "ok" :
        return
    recordset = DB.ResultatReq()
    if len(recordset)>0 :
        if len(recordset[0])>0 :
            value = recordset[0][0]
            if value != None:
                # test de non utilisation
                req = """SELECT Count(IDfacture)
                        FROM factures
                        WHERE numero= %s ;
                        """ % str(value)
                DB.ExecuterReq(req,MsgBox="Ctrl Unicité Facture " + str(value))
                recordset = DB.ResultatReq()
                nbre = recordset[0][0]
                if nbre > 0:
                    # le numero n'était pas vraiment libre
                    req = "DELETE FROM matParams WHERE prmUser = 'NoLibre' AND prmInteger = %d ;" % str(value)
                    date = None
                else:
                    # reprise de la date de facture
                    req = "SELECT prmInteger,prmDate FROM matParams WHERE prmUser = 'NoLibre' AND prmInteger = %d ;" % value
                    retour = DB.ExecuterReq(req,MsgBox="GestionInscription.GetNoFactureMin")
                    if retour != "ok" :
                        return
                    recordset = DB.ResultatReq()
                    noFacture = recordset[0][0]
                    dateRet = recordset[0][1]
                    req = "DELETE FROM matParams WHERE prmUser = 'NoLibre' AND prmInteger = %d ;" % value
                    retour = DB.ExecuterReq(req,commit = True,MsgBox="GestionInscription.GetNoFactureMin")
                    if retour != "ok" :
                        return
                # condition année civile en cours
                if dateRet != None:
                    date = DateEngEnDateDD(dateRet)
                    if date.year != datetime.date.today().year:
                        date=None
    # quand il n'y a plus de numéro libre on prend le suivant du plus grand
    if date == None:
        date = datetime.date.today()
    if noFacture== None:
        noFacture = GetNoFactureSuivant()
    DB.Close
    return noFacture,date

def RecordsToListeDict(listeChamps,records):
    # retourne une liste de tuples, où [0] est le premier champ de la table (l'ID) et [1] le dictionnaire de tous les champs
    listeDict = []
    if len(records) > 0:
        for record in records:
            if record != None:
                tup = (record[0],DictTrack(listeChamps,record))
                listeDict.append(tup)
    return listeDict

def DictToListeTuples(listeChamps,dictDonnees):
    # retourne une liste en extrayant les champs du dictionnaire pour Insert SQL
    listeTuples=[]
    for champ in listeChamps:
        listeTuples.append((champ,dictDonnees[champ]))
    return listeTuples

def DictTrack(listeChamps, valeurs, prefixe = "pie"):
    #transforme en dictionnaire un record de  requête (liste de valeurs ) selon liste champs (prefixe oté si présent)
    dictTrack = {}
    if listeChamps == None : listeChamps=[]
    if valeurs == None : valeurs = []
    newListe = StandardiseNomsChamps(listeChamps)
    if len(newListe) != len(valeurs):
        Mess = GestionDB.Messages()
        message = "Le nombre de champs et de valeurs ne correspondent pas \nNb champs : %d   Nb valeurs : %d !" % (len(newListe),len(valeurs))
        Mess.Box(titre="GestionInscription.DictTrack", message= message)
        raise Exception(message)
    for champ in newListe:
        idx = newListe.index(champ)
        if champ[:3] == prefixe:
            champ = champ[3:]
        if champ[:2]=="ID":
            nom =  champ
        else : nom = champ[0].lower()+ champ[1:]
        if idx <= len(valeurs)-1 :
            valeur = valeurs[idx]
            dictTrack[nom] = valeur
    return dictTrack

def StandardiseNomsChamps(listeChamps, prefixe = "pie"):
    #ote le prefixe au nom du champ et lower sur premier caractère
    newListe=[]
    for champ in listeChamps:
        idx = listeChamps.index(champ)
        if champ[:3] == prefixe:
            champ = champ[3:]
        if champ[:2]=="ID":
            nom =  champ
        else : nom = champ[0].lower()+ champ[1:]
        newListe.append(nom)
    return newListe

def RecordsetToDict(lstCles,recordset):
    # le dictionnaire généré contient pour clé le premier champ de chaque record et un dict des valeurs du record
    dict = {}
    for record in recordset:
        dict[record[0]]= {}
        for cle in lstCles:
            idx = lstCles.index(cle)
            dict[record[0]][cle] = record[idx]
    return dict

# Forfaits dans le sens de definition des consommations forfaitisées par un prix de camp
class Forfaits():
    def __init__(self,parent,DB=None):
        self.parent = parent
        if not DB:
            self.DB = GestionDB.DB()
        else:
            self.DB = DB
        self.user = self.DB.UtilisateurActuel()
        self.fGest = self
        
    def GetActivite(self,IDactivite):
        # Données de l'activité avec liste des unités, groupes auant des dates d'ouverture
        req = """
                SELECT activites.IDactivite, activites.nom, activites.abrege, activites.date_debut, 
                        activites.date_fin,ouvertures.IDunite,ouvertures.IDgroupe
                FROM activites
                INNER JOIN ouvertures ON activites.IDactivite = ouvertures.IDactivite
                WHERE activites.IDactivite = %d
                GROUP BY activites.IDactivite, activites.nom, activites.abrege, activites.date_debut, 
                        activites.date_fin,ouvertures.IDunite,ouvertures.IDgroupe
                ;""" %(IDactivite)
        self.DB.ExecuterReq(req,MsgBox= "GestionInscription.GetActivite")
        recordset = self.DB.ResultatReq()
        if len(recordset) == 0: return
        dictActivite = None
        for IDact, nom, abrege, date_debut, date_fin, IDunite, IDgroupe in recordset:
            if not dictActivite:
                dictActivite = { "nom": nom, "abrege": abrege,
                                 "debut": date_debut, "fin": date_fin,
                                 "date_debut": date_debut, "date_fin": date_fin,
                                 "unites": [], "groupes": [] }
                if date_debut != None : date_debut = DateEngEnDateDD(date_debut)
                if date_fin != None : date_fin = DateEngEnDateDD(date_fin)
            unites = dictActivite["unites"]
            groupes = dictActivite["groupes"]
            if IDunite and IDunite not in unites: unites.append(IDunite)
            if IDgroupe and IDgroupe not in groupes: groupes.append(IDgroupe)
        return dictActivite

    def GetOuvertures(self,IDactivite,IDgroupe=None,IDunite=None):
        # liste des jours d'ouverture pour une activité-unité-groupe, première unité ou groupe est par défaut
        ldOuvertures = []
        dictActivite = self.GetActivite(IDactivite)
        # compose requête
        if not IDunite:
            if len(dictActivite["unites"]) == 0:
                return []
            IDunite = dictActivite["unites"][0]
        whereUnite = "AND activites.IDunite = %d"%IDunite
        if not IDgroupe:
            if len(dictActivite["groupes"]) == 0:
                return []
            IDgroupe = dictActivite["groupes"][0]
        whereGroupe = "AND activites.IDgroupe = %d"%IDgroupe
        # Recherche des ouvertures de l'activité sur sa période d'ouverture
        req = """SELECT date
        FROM ouvertures
        WHERE IDactivite = %d 
                AND IDunite = %d 
                AND IDgroupe = %d
                AND date >= '%s'
                AND date <= '%s'
        ORDER BY date;""" % (IDactivite, IDunite, IDgroupe, dictActivite["debut"],dictActivite["fin"])
        self.DB.ExecuterReq(req,MsgBox="GestionInscription.GetOuvertures")
        listeOuvertures = self.DB.ResultatReq()

        # recherche élargie hors dates d'activité si nécessaire
        if len(listeOuvertures) == 0:
            req = """SELECT date
            FROM ouvertures
            WHERE IDactivite = %d 
                    AND IDunite = %d 
                    AND IDgroupe = %d
            ORDER BY date;""" % (IDactivite, IDunite, IDgroupe)
            self.DB.ExecuterReq(req,MsgBox="GestionInscription.GetOuvertures")
            listeOuvertures = self.DB.ResultatReq()

        for (date,) in listeOuvertures:
            date = DateEngEnDateDD(date)
            ldOuvertures.append({"date":date, "IDunite":IDunite})
            # plafonnement du nombre d'ouvertures au delà d'un mois continu, seulement la première date gardée
            if len(listeOuvertures) >27:
                break
        return ldOuvertures
        #fin GetOuvertures

    def ChoixPiece(self,retour):
        # On demande quelle piece supprimer  et on récupére la ligne retour
        msg = GestionDB.Messages()
        listeTuples = []
        for ligneRetour in retour:
            listeTuples.append((ligneRetour[0],ligneRetour[9]))
        ixChoix,nom = msg.Choix(listeTuples=listeTuples, titre = ("Cette inscription est rattachée à  %d pièces")% len(listeTuples), intro = "Double clic pour choisir la pièce")
        if ixChoix == None:
            return None
        else:
            #appel de la piece choisie
            for tuple in listeTuples:
                if ixChoix == tuple[0]:
                    for ligne in retour:
                        if ligne[0] == ixChoix:
                            ligneRetour = ligne
        return ligneRetour

    # Outil correctif : Mise en cohérence des autres tables aller retour en devis
    def ChangeNaturePiece(self,parent,dictPiece,natureNew):
        dictOldPiece = {}
        # dPpiece ne contient que les éléments de base pour trouver la pièce complète
        liste_codesNaturePiece = ["DEV","RES","COM","FAC","AVO"]
        # complète la pièce, getPieceModif alimente self.dictPiece
        if dictPiece["IDindividu"] > 0:
            niveau = "individu"
            ret = self.GetPieceModif(parent,dictPiece["IDindividu"],dictPiece["IDactivite"],
                                      IDnumPiece=dictPiece["IDnumPiece"],DB=self.DB)
            if ret == False:
                return "Echec GetPiece"
            natureOld = self.dictPiece["nature"]
            dictOldPiece.update(self.dictPiece)
            self.dictPiece.update(dictPiece)
            # Priorité aux données transmises après récup d'éventuels champs manquants
            dictPiece.update(self.dictPiece)

        else:
            # pièce niveau famille
            niveau = "famille"
            lstPieces = self.GetPieceModif999(parent,dictPiece["IDcompte_payeur"],dictPiece["IDinscription"],
                                               dictPiece["IDnumPiece"])
            dictOri = lstPieces[0]
            natureOld = dictOri["nature"]
            dictOldPiece.update(dictOri)
            # Priorité aux données transmises, mais on récupére des clés manquantes
            dictOri.update(dictPiece)
            dictPiece.update(dictOri)
            
        etatPiece = dictPiece["etat"]
        if not natureOld in ("DEV","RES","COM"):
            messStr = "Changement de nature %s non prevu ici!!!"%natureOld
            wx.MessageBox(messStr,"Pb de programmation, non géré")
            raise Exception(messStr)
    
        dictPiece["origine"]= "modif"
        i = liste_codesNaturePiece.index(natureOld)
        # Mise à "1" du caractère en la position correspondant à la nature de la pièce (ex: FAC = 4eme)
        etatPiece = etatPiece[:i]+"1"+ etatPiece[i+1:]
        dictPiece["etat"] = etatPiece
    
        # modification de matPieces
        commentaire = "%s"%(GestionDB.Decod(dictPiece["commentaire"]))
        commentaire = str(datetime.date.today()) + " Nature: " + natureOld + "\n" + commentaire
        dictPiece["commentaire"] = commentaire
        dictNewPiece = {}
        dictNewPiece.update(dictPiece)
        listeDonnees = [("nature", natureNew),
                        ("etat", etatPiece),]
        if natureNew in ("DEV","RES"):
            listeDonnees.append(("IDprestation", None))
        for champ, valeur in listeDonnees :
            dictNewPiece[champ] = valeur
        ret = self.ModifiePiece(parent,dictNewPiece)
        ajout = True
        # gestion des autres tables liées
        if natureOld == "DEV":
            if natureNew == "RES" and niveau == "individu":
                ajout = self.AjoutConsommations(parent,dictNewPiece)
            if natureNew == "COM":
                if  niveau == "individu":
                    ajout = self.AjoutConsommations(parent,dictNewPiece)
                IDprestation = self.AjoutPrestation(parent,dictNewPiece,modif=True)
                if IDprestation > 0:
                    dictNewPiece["IDprestation"] = IDprestation
                self.ModifieConsoCree(parent,dictNewPiece)
                self.ModifiePieceCree(parent,dictNewPiece)
        if natureOld == "RES":
            if natureNew == "DEV" and niveau == "individu":
                retDel = self.DelConsommations(parent,dictNewPiece)
            if natureNew == "COM":
                if niveau == "individu":
                    IDprestation = self.AjoutPrestation(parent,dictNewPiece,modif=True)
                else:
                    IDprestation = self.AjoutPrestation999(parent,dictNewPiece,modif=False)
                if IDprestation > 0:
                    dictNewPiece["IDprestation"] = IDprestation
                    dictPiece['IDprestation'] = IDprestation
                if niveau == "individu":
                    self.ModifieConsoCree(parent,dictNewPiece)
                self.ModifiePieceCree(parent,dictNewPiece)
        if natureOld == "COM":
            if natureNew == "DEV":
                if niveau == "individu":
                    retDel = self.DelConsommations(parent,dictOldPiece)
                    if retDel != "ok": ret = retDel
                retDel = self.DelPrestations(parent,dictDonnees=dictOldPiece)
                if retDel != "ok": ret = retDel
    
        if natureNew == "RES":
            self.DelPrestations(parent,dictDonnees=dictOldPiece)
        if not ajout: ret = "ko"
        dictPiece.update(dictNewPiece)
        return ret
        # fin ChangeNaturePiece
    
    def AjoutPiece(self,parent,dictDonnees):
        # Sauvegarde de la piece
        echeance = datetime.date.today() + datetime.timedelta(10)
        datefacture = None
        self.noFacture= None
        listeDonnees = [
            ("pieIDinscription", dictDonnees["IDinscription"]),
            ("pieIDprestation", dictDonnees["IDprestation"]),
            ("pieIDindividu", dictDonnees["IDindividu"]),
            ("pieIDfamille", dictDonnees["IDfamille"]),
            ("pieIDcompte_payeur", dictDonnees["IDcompte_payeur"]),
            ("pieIDactivite", dictDonnees["IDactivite"]),
            ("pieIDgroupe", dictDonnees["IDgroupe"]),
            ("pieIDcategorie_tarif", dictDonnees["IDcategorie_tarif"]),
            ("pieDateCreation", str(datetime.date.today())),
            ("pieUtilisateurCreateur", self.user),
            ("pieDateModif",str(datetime.date.today())),
            ("pieUtilisateurModif", None),
            ("pieNature", dictDonnees["nature"]),
            ("pieEtat",dictDonnees["etat"]),
            ("pieDateFacturation", datefacture),
            ("pieNoFacture", self.noFacture),
            ("pieDateEcheance", echeance),
            ("pieDateAvoir", None),
            ("pieNoAvoir",None ),
            ("pieCommentaire", GestionDB.Decod(dictDonnees["commentaire"])),
            ]
        retour = self.DB.ReqInsert("matPieces", listeDonnees, retourID=False)
        if retour != "ok" :
            GestionDB.MessageBox(parent,retour)
            return None
        IDnumPiece = self.DB.newID
       # Enregistre dans PiecesLignes
        listeInit = [
            ("ligIDnumPiece", IDnumPiece),
            ("ligDate",str(datetime.date.today())),
            ("ligUtilisateur", self.user),
            ]
        listeLignesPiece = dictDonnees["lignes_piece"]
        for ligne in listeLignesPiece:
            listeDonnees = listeInit[:]
            listeDonnees.append(("ligCodeArticle",ligne["codeArticle"]))
            listeDonnees.append(("ligLibelle",ligne["libelle"]))
            listeDonnees.append(("ligQuantite",ligne["quantite"]))
            listeDonnees.append(("ligPrixUnit",ligne["prixUnit"]))
            if ligne["montant"] == 0:
                ligne["montant"] = ligne["prixUnit"] * ligne["quantite"]
            listeDonnees.append(("ligMontant",ligne["montant"]))
            retour = self.DB.ReqInsert("matPiecesLignes", listeDonnees,retourID = False)
            if retour != "ok" :
                GestionDB.MessageBox(parent,retour)
                return None
        return IDnumPiece
        # fin AjoutPiece

    def AjoutPiece999(self,parent,IDfamille,IDcomptePayeur,exercice, nature="COM", IDnumPiece=None):
        #ajout piece de niveau famille, sans les lignes, champs vides
        dictPiece={}
        listeChamps=[]
        for champ, natureChamp, comment in DATA_Tables.DB_DATA["matPieces"]:
            dictPiece[champ]=None
        #compléments d'infos
        dictPiece["pieIDinscription"]= exercice.year
        dictPiece["pieIDindividu"]=0
        dictPiece["pieIDcompte_payeur"]=IDcomptePayeur
        dictPiece["pieIDactivite"]=0
        dictPiece["pieIDfamille"]=IDfamille
        dictPiece["pieDateCreation"]=str(datetime.date.today())
        dictPiece["pieUtilisateurCreateur"]=self.user
        dictPiece["pieDateModif"]=str(datetime.date.today())
        dictPiece["pieNature"]=nature
        dictPiece["pieEtat"]="11100"
        #creation de la liste pour insert
        del dictPiece["pieIDnumPiece"]
        listeDonnees = []
        listeTuples = []
        for key in list(dictPiece.keys()):
            listeDonnees.append(dictPiece[key])
            listeChamps.append(key)
            listeTuples.append((key,dictPiece[key]))
        retour = self.DB.ReqInsert("matPieces", listeTuples, retourID=False, MsgBox="AjoutPiece999")
        if retour != "ok":
            GestionDB.MessageBox(parent,retour)
            return False
        if not IDnumPiece :
            IDnumPiece = self.DB.newID
        dictDonnees = DictTrack(listeChamps,listeDonnees)
        dictDonnees["IDnumPiece"]=IDnumPiece
        self.AjoutPrestation999(self,dictDonnees)
        return dictDonnees
        # fin AjoutPiece999

    def AjoutConsommations(self,parent,dictDonnees,force=False) :
        if not force and ("nature" in dictDonnees) and dictDonnees["nature"] in ("DEV","AVO"):
            # pas de consommations à ajouter dans les avoirs ou les devis
            return True
        IDinscription = dictDonnees["IDinscription"]
        IDindividu = dictDonnees["IDindividu"]
        IDactivite = dictDonnees["IDactivite"]
        IDgroupe = dictDonnees["IDgroupe"]
        IDfamille = dictDonnees["IDcompte_payeur"]
        # Récupération des consommations à créer
        ldConsommations = self.GetOuvertures(IDactivite,IDgroupe)
        if len(ldConsommations) == 0:
            wx.MessageBox("Aucun jour d'ouverture pour l'activité %d, groupe %d!!!"%(IDactivite,IDgroupe))
        listeDatesStr = []
        for dOuverture in ldConsommations:
            if dOuverture["date"] not in listeDatesStr : listeDatesStr.append(str(dOuverture["date"]))

        # Vérifie que les dates ne sont pas déjà prises pour alerte conflit
        if len(listeDatesStr) == 0 : conditionDates = " "
        elif len(listeDatesStr) == 1 : conditionDates = " AND date IN('%s')" % listeDatesStr[0]
        else :
            conditionDates = " AND date IN %s"%str(tuple(listeDatesStr))
        req = """
                SELECT consommations.IDinscription, consommations.IDcompte_payeur, consommations.IDindividu,
                        consommations.IDactivite,consommations.IDgroupe, consommations.IDcategorie_tarif
                FROM consommations
                WHERE IDinscription=%d %s
                GROUP BY consommations.IDcompte_payeur, consommations.IDindividu, consommations.IDactivite, 
                        consommations.IDgroupe, consommations.IDcategorie_tarif
                ; """ % (IDinscription, conditionDates)
        self.DB.ExecuterReq(req,MsgBox="GestionInscription.AjoutConsos")
        listeConsoExistantes = self.DB.ResultatReq()
        if len(listeConsoExistantes) > 0 :
            cle = "Famille %d, individu %d,activité %d, groupe %d"%(IDfamille,IDindividu,IDactivite,IDgroupe)
            mess = "Déjà inscrit impossible d'enregistrer de nouvelles consommations! \n\n"
            mess += "Des consommations existent déjà:\n%s\n"%(cle)
            wx.MessageBox(mess, "Inscriptions redondantes", wx.OK | wx.ICON_ERROR)
            return False

        # Enregistre des consommations
        for conso in ldConsommations :
            date = conso["date"]
            IDunite = conso["IDunite"]
            # Récupération des données
            if (not "nature" in dictDonnees) or dictDonnees["nature"] in ("COM","FAC",):
                etatConsommation = "present"
            else : etatConsommation = "reservation"
            listeDonnees = [
                ("IDindividu", IDindividu),
                ("IDinscription", dictDonnees["IDinscription"]),
                ("IDactivite", dictDonnees["IDactivite"]),
                ("date", str(date)),
                ("IDunite", IDunite),
                ("IDgroupe", IDgroupe),
                ("etat", etatConsommation),
                ("forfait", 2),
                ("verrouillage", False),
                ("date_saisie", str(datetime.date.today())),
                ("IDutilisateur", self.DB.IDutilisateurActuel()),
                ("IDcategorie_tarif", dictDonnees["IDcategorie_tarif"]),
                ("IDcompte_payeur", IDfamille),
                ]
            if "IDprestation" in dictDonnees:
                listeDonnees.append(("IDprestation", dictDonnees["IDprestation"]))

            # Insertion des données
            retour = self.DB.ReqInsert("consommations", listeDonnees,retourID=False,MsgBox="AjoutConso")
            if not retour == "ok":
                return False
        return True
        #fin AjoutConsommations

    def AjoutPrestation(self,parent,dictDonnees,modif=False,recree=False) :
        if dictDonnees['IDindividu'] == 0:
            ret = self.AjoutPrestation999(parent, dictDonnees,modif)
            return ret
        nom_individu = dictDonnees["nom_individu"]
        nom_activite = dictDonnees["nom_activite"]
        nom_groupe = dictDonnees["nom_groupe"]
        # Prestation camp
        montant = 0.00
        for item in dictDonnees["lignes_piece"]:
            montant += item["montant"]
        if dictDonnees["prixTranspAller"]!=None:
            montant += dictDonnees["prixTranspAller"]
        if dictDonnees["prixTranspRetour"]!=None:
            montant += dictDonnees["prixTranspRetour"]
        if dictDonnees["nature"]=="AVO":
            montant = -montant
            modif = False
        dateCreation = str(datetime.date.today())
        if modif :
            if 'date' in dictDonnees :
                dateCreation = dictDonnees["date"]
        # Sauvegarde de la prestation camp
        IDfacture = None
        if Nz(dictDonnees["noFacture"]) > 0:
            req = """SELECT IDfacture
                    FROM factures
                    WHERE numero = '%s'
                    ; """ % str(dictDonnees["noFacture"])
            self.DB.ExecuterReq(req,MsgBox="GestionInscription.AjouPrest")
            recordset = self.DB.ResultatReq()
            if len(recordset) >0:
                IDfacture = recordset[0][0]
        listeDonnees = [
            ("IDcompte_payeur", dictDonnees["IDcompte_payeur"]),
            ("date", dateCreation),
            ("categorie", "consommation"),
            ("label", nom_individu + " - " + nom_activite + " - " + nom_groupe),
            ("IDfacture", IDfacture),
            ("montant_initial", montant),
            ("montant", montant),
            ("forfait", 2),
            ("IDactivite",dictDonnees["IDactivite"]),
            ("IDfamille", dictDonnees["IDfamille"]),
            ("IDindividu", dictDonnees["IDindividu"]),
            ("IDcategorie_tarif", dictDonnees["IDcategorie_tarif"]),
            ("IDcontrat", dictDonnees["IDnumPiece"]),
            ]
        IDprestation = dictDonnees["IDprestation"]
        if modif and Nz(IDprestation) >0:
            self.DB.ReqMAJ("prestations", listeDonnees,"IDprestation",IDprestation,MsgBox="AjoutPrestMAJ")
        elif recree and Nz(IDprestation) >0:
            listeDonnees.append(("IDprestation",IDprestation))
            self.DB.ReqInsert("prestations", listeDonnees,retourID = True,MsgBox="AjoutPrestInsert")
            IDprestation = self.DB.newID
        else:
            ret = self.DB.ReqInsert("prestations", listeDonnees,retourID = False,MsgBox=None)
            if ret == "ok":
                IDprestation = self.DB.newID
            else:
                self.DB.ReqMAJ("prestations", listeDonnees,"IDprestation",IDprestation,MsgBox=None)

        return Nz(IDprestation)
        # fin AjoutPrestation

    def AjoutAvoPrestation(self,parent,dictDonnees) :
        nom_individu = dictDonnees["nom_individu"]
        nom_activite = dictDonnees["nom_activite"]
        nom_groupe = dictDonnees["nom_groupe"]
        # Prestation camp
        montant = 0.00
        for item in dictDonnees["lignes_piece"]:
            montant += item["montant"]
        if dictDonnees["prixTranspAller"]!=None:
            montant += dictDonnees["prixTranspAller"]
        if dictDonnees["prixTranspRetour"]!=None:
            montant += dictDonnees["prixTranspRetour"]
        montant = -montant
        dateCreation = str(datetime.date.today())
        if 'date' in dictDonnees :
            dateCreation = dictDonnees["date"]
        # Sauvegarde de la prestation camp
        IDfacture = None
        if Nz(dictDonnees["noAvoir"]) > 0:
            req = """SELECT IDfacture
                    FROM factures
                    WHERE numero = '%s'
                    ; """ % str(dictDonnees["noAvoir"])
            self.DB.ExecuterReq(req,MsgBox="GestionInscription.AjouAvoPrest")
            recordset = self.DB.ResultatReq()
            if len(recordset) >0:
                IDfacture = recordset[0][0]
        listeDonnees = [
            ("IDcompte_payeur", dictDonnees["IDcompte_payeur"]),
            ("date", dateCreation),
            ("categorie", "consoavoir"),
            ("label", nom_individu + " - " + nom_activite + " - " + nom_groupe),
            ("IDfacture", IDfacture),
            ("montant_initial", montant),
            ("montant", montant),
            ("forfait", 2),
            ("IDactivite",dictDonnees["IDactivite"]),
            ("IDfamille", dictDonnees["IDfamille"]),
            ("IDindividu", dictDonnees["IDindividu"]),
            ("IDcategorie_tarif", dictDonnees["IDcategorie_tarif"]),
            ("IDcontrat", dictDonnees["IDnumPiece"]),
            ]
        self.DB.ReqInsert("prestations", listeDonnees,retourID = True,MsgBox="AjoutAvoPrestInsert")
        IDprestation = self.DB.newID
        return Nz(IDprestation)
        # fin AjoutAvoPrestation

    def AjoutPrestation999(self,parent,dictDonnees,modif = False) :
        # origine : niveau famille) ajoute la prestation et modifie la pièce pour IDprestation
        montant = 0.00
        montantInit = 0.00
        if "lignes_piece" in dictDonnees:
            for item in dictDonnees["lignes_piece"]:
                montantInit += item["quantite"] * item["prixUnit"]
                if item["montant"] != 0:
                    montant += item["montant"]
                else: montant += (item["quantite"] * item["prixUnit"])
        if dictDonnees["nature"]=="AVO":
            montant = -montant
            montantInit = -montantInit
            modif = False
        if dictDonnees["nature"] == "AVO":
            categorie =  "consoavoir"
            label = "Avoir famille"
        else:
            categorie =  "consommation"
            if montant < 0.0:
                label = "Correctif famille"
            else:
                label = "Niveau famille"
        newID = None
        IDprestation = None
        if dictDonnees["nature"] in ["COM","FAC","AVO"]:
            # Sauvegarde de la prestation
            if "IDfacture" not in dictDonnees:
                dictDonnees["IDfacture"] = None
            listeDonnees = [
                ("IDcompte_payeur", dictDonnees["IDcompte_payeur"]),
                ("date", str(datetime.date.today())),
                ("categorie", categorie),
                ("label", label),
                ("IDfacture", dictDonnees["IDfacture"]),
                ("montant_initial", montantInit),
                ("montant", montant),
                ("forfait", 1),
                ("IDactivite",dictDonnees["IDactivite"]),
                ("IDfamille", dictDonnees["IDfamille"]),
                ("IDindividu", dictDonnees["IDindividu"]),
                ("IDcategorie_tarif", dictDonnees["IDcategorie_tarif"]),
                ("IDcontrat", dictDonnees["IDnumPiece"]),
                ]
            if modif:
                IDprestation = dictDonnees["IDprestation"]
                self.DB.ReqMAJ("prestations", listeDonnees,"IDprestation",IDprestation,MsgBox="AjoutPrestation999")
            else:
                self.DB.ReqInsert("prestations", listeDonnees,retourID = True,MsgBox="AjoutPrestation2")
                newID = self.DB.newID
        # maj de l'ID prestation dans la pièce
        if newID :
            listeDonnees = [("pieIDprestation", newID),]
            ret = self.DB.ReqMAJ("matPieces", listeDonnees,"pieIDnumPiece",dictDonnees["IDnumPiece"],MsgBox="AjoutPrestation3")
            IDprestation = newID
            dictDonnees["IDprestation"] = IDprestation
        return IDprestation
        # fin AjoutPrestation

    def GetPieceModif(self,parent,IDindividu,IDactivite,IDnumPiece = None,DB=None):
        try:
            DBfourni = (DB.connexion.open == 1) # ajout tardif, on gère aussi le DB non fourni en kwds
        except: DBfourni = False
        if not DBfourni:
            DB = GestionDB.DB()
        dicoDB = DATA_Tables.DB_DATA
        listeChamps = []
        for descr in dicoDB["matPieces"]:
            nomChamp = descr[0]
            #typeChamp = descr[1]
            listeChamps.append(nomChamp)
        if IDnumPiece== None:
            #la recherche se fait prioritairement sur le IDnumPiece s'il est connu
            conditions = "pieIDindividu= %d AND pieIDactivite = %d;" % (IDindividu,IDactivite)
        else: conditions = "pieIDnumPiece= %d" % (IDnumPiece)
        req =  "SELECT * FROM matPieces WHERE " + conditions
        retour = DB.ExecuterReq(req,MsgBox="GestionInscription.GetPieceModift")
        if retour != "ok" :
            # abandon
            GestionDB.MessageBox(parent,retour)
            if not DBfourni: DB.Close()
            return False
        retour = DB.ResultatReq()
        self.nbPieces = len(retour)
        if self.nbPieces == 0 :
            GestionDB.MessageBox(parent,"Anomalie : Rien dans matPieces pour cette inscription => pas de modif possible voir si suppression possible")
            if not DBfourni: DB.Close()
            return None
        if self.nbPieces == 1:
            self.dictPiece = DictTrack(listeChamps,retour[0])
        else:
            retour = self.ChoixPiece(retour)
            if retour == None:
                return False
            self.dictPiece = DictTrack(listeChamps,retour)
        # Appel des lignes de la pièce pour ajouter dans le dictPiece
        listeChamps = []
        for descr in dicoDB["matPiecesLignes"]:
            nomChamp = descr[0]
            listeChamps.append(nomChamp)
        conditions = "ligIDnumPiece= %d ;" % (self.dictPiece["IDnumPiece"])
        req =  "SELECT * FROM matPiecesLignes WHERE " + conditions
        retour = DB.ExecuterReq(req,MsgBox="GestionInscription.GetPieceModift")
        if retour != "ok" :
            if not DBfourni: DB.Close()
            return False
        retour = DB.ResultatReq()
        listeLignes = []
        total = 0.00
        for ligne in retour:
            dicLigne = DictTrack(listeChamps,ligne,prefixe="lig")
            listeLignes.append(dicLigne)
            total += dicLigne["montant"]
        self.dictPiece["lignes_piece"] = listeLignes
        self.dictPiece["total"] = total
        self.dictPiece["nom_individu"] = DB.GetNomIndividu(self.dictPiece["IDindividu"])
        self.dictPiece["nom_famille"] = DB.GetNomFamille(self.dictPiece["IDfamille"])
        self.dictPiece["nom_payeur"] = DB.GetNomFamille(self.dictPiece["IDcompte_payeur"])
        self.dictPiece["nom_activite"] = DB.GetNomActivite(self.dictPiece["IDactivite"])
        self.dictPiece["nom_groupe"] = DB.GetNomGroupe(self.dictPiece["IDgroupe"])
        if self.dictPiece["IDcategorie_tarif"] == None:
            self.dictPiece["nom_categorie_tarif"]="Famille"
        else: self.dictPiece["nom_categorie_tarif"] = DB.GetNomCategorieTarif(self.dictPiece["IDcategorie_tarif"])
        if not DBfourni: DB.Close()
        return True
        #fin GetPieceModif

    def GetPieceModif999(self,parent,IDcomptePayeur,exercice,IDnumPiece=None,facture=False):
        self.IDcomptePayeur = IDcomptePayeur
        dicoDB = DATA_Tables.DB_DATA
        listeChamps = []
        for descr in dicoDB["matPieces"]:
            nomChamp = descr[0]
            listeChamps.append(nomChamp)
        if IDnumPiece == None and not facture:
            conditions = "pieNature NOT in ('FAC','AVO') AND pieIDcompte_payeur= %d AND pieIDinscription = %d ;" \
                               % (IDcomptePayeur,exercice)
        elif IDnumPiece == None and facture:
            conditions = "pieNature in ('FAC') AND pieIDcompte_payeur= %d AND pieIDinscription = %d ;" \
                         % (IDcomptePayeur, exercice)
        else:
            conditions = " pieIDnumPiece = %d ; " % IDnumPiece
        req =  "SELECT * FROM matPieces WHERE " + conditions
        retour = self.DB.ExecuterReq(req,MsgBox="GestionInscription.GetPieceModif999")
        if retour != "ok" :
            return []
        lstPieces = self.DB.ResultatReq()
        self.nbPieces = len(lstPieces)
        if self.nbPieces == 0 :
            return []
        listeChampsLignes = []
        for descr in dicoDB["matPiecesLignes"]:
            nomChamp = descr[0]
            listeChampsLignes.append(nomChamp)
        listePieces = []
        for piece in lstPieces:
            dictPiece = DictTrack(listeChamps,piece)
            # Appel des lignes de la pièce pour ajouter dans le dictPiece
            conditions = "ligIDnumPiece= %d ;" % (dictPiece["IDnumPiece"])
            req =  "SELECT * FROM matPiecesLignes WHERE " + conditions
            retour = self.DB.ExecuterReq(req,MsgBox="GestionInscription.GetPieceModif999")
            if retour != "ok" :
                GestionDB.MessageBox(parent,retour)
            else:
                retlignes = self.DB.ResultatReq()
                listeLignes = []
                for ligne in retlignes:
                    listeLignes.append(DictTrack(listeChampsLignes,ligne,prefixe="lig"))
                dictPiece["lignes_piece"] = listeLignes
                dictPiece["nom_payeur"] = self.DB.GetNomFamille(self.IDcomptePayeur)
                listePieces.append(dictPiece)
        return listePieces
        #fin GetPieceModif999

    def GetPiece_Supprimer(self, parent, IDinscription, IDindividu, IDactivite):
        #retourne False pour abandon, None pour suppression sans piece, True pour self.dictPiece alimentée
        self.dictPiece = {}
        listeChamps = ["pieIDnumPiece", "pieIDinscription", "pieIDprestation", "pieIDfamille","pieDateCreation", "pieUtilisateurCreateur", "pieNature", "pieNature", "pieEtat", "pieCommentaire"]
        champs=" "
        for item in listeChamps :
            champs = champs + item +","
        champs = champs[:-1]
        conditions = "pieIDindividu= %d AND pieIDactivite = %d;" % (IDindividu,IDactivite)
        req =  "SELECT" + champs + " FROM matPieces WHERE " + conditions
        retour = self.DB.ExecuterReq(req,MsgBox="GestionInscription.GetPieceSupprime")
        if retour != "ok" :
            GestionDB.MessageBox(parent,retour)
            return False
        retour = self.DB.ResultatReq()
        self.nbPieces = len(retour)
        if self.nbPieces == 0 :
            GestionDB.MessageBox(parent,"Anomalie : Rien dans matPieces pour cette inscription, pas de suppression de prestation")
            return None
        if self.nbPieces == 1:
            if IDinscription == retour[0][1]:
                reqPiece = self.GetPieceModif(self.parent,IDindividu,IDactivite)
                if reqPiece: return True
                else: return False
            #la piece ne correspond pas à l'inscription
            else:
                dlg = GestionDB.MessageBox(parent, _("Suppression impossible car NoInscription dans piece différent "), titre = "Confirmation")
                return False
        else:
            # On demande quelle piece supprimer  et on récupére l'IDinscription
            reqPiece = self.GetPieceModif(self.parent,IDindividu,IDactivite)
            if reqPiece : return True
            return False
        #fin GetPieceSupprime

    # modif de la pièce dans matPièce seulement
    def ModifiePieceCree(self,parent,dictDonnees):
        # ne s'occupe pas des dépendances de la pièce ni de ses lignes
        listeDonnees = [
            ("pieIDinscription", dictDonnees["IDinscription"]),
            ("pieIDprestation", dictDonnees["IDprestation"]),
            ("pieNature", dictDonnees["nature"]),
            ("pieEtat",dictDonnees["etat"]),
            ("pieIDtranspAller", dictDonnees["IDtranspAller"]),
            ("piePrixTranspAller", dictDonnees["prixTranspAller"]),
            ("pieIDtranspRetour", dictDonnees["IDtranspRetour"]),
            ("piePrixTranspRetour", dictDonnees["prixTranspRetour"]),
            ("pieIDparrain",dictDonnees["IDparrain"]),
            ("pieParrainAbandon",dictDonnees["parrainAbandon"]),
            ]
        retour = self.DB.ReqMAJ("matPieces", listeDonnees,"pieIDnumPiece",dictDonnees["IDnumPiece"],MsgBox="ModifiePieceCree")
        return retour

    def ModifieInscription(self,parent,dictDonnees):
        if dictDonnees["nature"]=="AVO":
            return
        listeDonnees = [
            ("IDindividu", dictDonnees["IDindividu"] ),
            ("IDfamille", dictDonnees["IDfamille"] ),
            ("IDcompte_payeur", dictDonnees["IDcompte_payeur"]),
            ("IDactivite", dictDonnees["IDactivite"]),
            ("IDgroupe", dictDonnees["IDgroupe"]),
            ("IDcategorie_tarif", dictDonnees["IDcategorie_tarif"]),
            ]
        retour = self.DB.ReqMAJ("inscriptions", listeDonnees,"IDinscription",dictDonnees["IDinscription"])
        if retour != "ok" :
            GestionDB.MessageBox(parent,retour)
        return retour

    def RazTransport(self,parent,dictDonnees,sens = "deux"):
        # supprime dans les tables transports et matPiece les références transports
        # conserve les montants facturés
        listeDonnees = []
        def Raz(listeDonnees,IDnumPiece,IDtransport):
            self.SupprimeTransport(IDtransport)
            retour = self.DB.ReqMAJ("matPieces", listeDonnees,"pieIDnumPiece",IDnumPiece,MsgBox="RazTransports/matPiece")
            if retour != "ok" :
                GestionDB.MessageBox(parent,retour)
        if sens in ("aller","deux"):
            listeDonnees = [("pieIDtranspAller", 0),]
            if not dictDonnees["nature"] in ("FAC","AVO"):
                listeDonnees.append(("piePrixTranspAller",0.00))
            Raz(listeDonnees,dictDonnees["IDnumPiece"],dictDonnees["IDtranspAller"])
        if sens in ("retour","deux"):
            listeDonnees = [("pieIDtranspRetour",0),]
            if not dictDonnees["nature"] in ("FAC","AVO"):
                listeDonnees.append(("piePrixTranspRetour",0.00))
            Raz(listeDonnees,dictDonnees["IDnumPiece"], dictDonnees["IDtranspRetour"])
        #fin RazTransport

    def SupprimeTransport(self,IDtransport):
        #le transport ne sera supprimé que s'il n'y a qu'une seule pièce qui le référence
        if IDtransport and IDtransport >0 :
            req =  """SELECT COUNT(pieIDnumPiece)
                        FROM matPieces WHERE pieIDtranspAller = %d OR pieIDtranspRetour = %d
                        GROUP BY pieIDindividu""" % (IDtransport,IDtransport)
            retour = self.DB.ExecuterReq(req,MsgBox="GestionInscription.SupprimeTransports")
            if retour != "ok" :
                GestionDB.MessageBox(self.parent,retour)
                return False
            recordset = self.DB.ResultatReq()
            nbre = 0
            if len(recordset) >0:
                if len(recordset[0]) >0:
                    nbre = recordset[0][0]
            if nbre <=1:
                retour = self.DB.ReqDEL("transports","IDtransport",IDtransport,MsgBox = "SupprimeTransport")
                if retour != "ok" :
                    GestionDB.MessageBox(self.parent,retour)
            else:
                GestionDB.MessageBox(self.parent,"Le transport %d est pointé par plusieurs pièces !\n pas de suppression" % IDtransport,titre = "Remarque")
        #fin SupprimeTransport

    def ModifPrestationVentilation999(self, DB, dictDonnees):
        if len(dictDonnees['lignes_piece']) == 0:
            self.Suppression999(dictDonnees)
            return

        # Appelle AjoutPrestation, mais gère avant cela la ventilation associée
        lstVentilation = []
        # Réservation des éventuelles ventilations de règlements
        IDprestation = None
        for IDprestation in dictDonnees['lstIDprestationsOrigine']:
            if IDprestation != None and IDprestation > 0 :
                req = """SELECT IDventilation, montant
                        FROM ventilation
                        WHERE IDprestation = %d
                        ;""" % IDprestation
                retour = DB.ExecuterReq(req,MsgBox = "GestionInscriptions.ModifPrestation")
                if retour == "ok":
                    recordset = DB.ResultatReq()
                    if len(recordset) > 0:
                            for IDventil, montant in recordset:
                                lstVentilation.append((IDventil, montant))

        # appelle l'ajout de prestation
        if IDprestation != None:
            for ID in dictDonnees['lstIDprestationsOrigine'][:-1]:
                # suppression d'éventuelles prestations en surnombre
                DB.ReqDEL("prestations", "IDprestation", ID)
            IDprestation = self.AjoutPrestation999(None,dictDonnees, modif = True)
        else:
            IDprestation = self.AjoutPrestation999(None,dictDonnees, modif = False)

        # traitement des ventilations
        mttPrestation = 0
        for lig in dictDonnees['lignes_piece']:
            mttPrestation += lig['montant']
        for IDventil, montant in lstVentilation:
            if mttPrestation >= 0:
                if mttPrestation >= montant and montant > 0 : # on conserve la ventilation que règle partiellement la prestation
                    mttPrestation -= montant
                elif montant >0: # on réduit le montant pour ne pas sur ventiler
                    montant = mttPrestation
                    mttPrestation == 0
                    DB.ReqMAJ('ventilation',[('montant',montant),],'IDventilation',IDventil,MsgBox="GestionInscription MAJ ventilation %d"%IDventil )
                else: # on ne garde pas
                    DB.ReqDEL('ventilation','IDventilation',IDventil,MsgBox="GestionInscription DEL ventilation %d"%IDventil )
            else: # mttPrestation négatif
                if mttPrestation <= montant and montant < 0 : # on conserve la ventilation que règle partiellement la prestation
                    mttPrestation -= montant
                elif montant <0: # on réduit le montant pour ne pas sur ventiler
                    montant = mttPrestation
                    mttPrestation == 0
                    DB.ReqMAJ('ventilation',[('montant',montant),],'IDventilation',IDventil,MsgBox="GestionInscription MAJ ventilation %d"%IDventil )
                else: # on ne garde pas
                    DB.ReqDEL('ventilation','IDventilation',IDventil,MsgBox="GestionInscription DEL ventilation %d"%IDventil )

    # Modif de la pièce et de ses lignes
    def ModifiePiece(self,parent,dictDonnees):
        # recherche date d'échéance
        if dictDonnees["nature"] in  ('FAC','AVO'):
            # gestion des dates de pièce
            dateFact = self.DB.GetDateFacture(dictDonnees["IDinscription"],dictDonnees["IDactivite"],datetime.date.today())
            dictActivite = self.GetActivite(dictDonnees["IDactivite"])
            dd = dictActivite["date_debut"]
            try:
                echeance = max(dd + datetime.timedelta(-30),datetime.date.today() + datetime.timedelta(10))
            except:
                echeance = datetime.date.today() + datetime.timedelta(10)
        else:
            echeance = datetime.date.today() + datetime.timedelta(10)
        dictDonnees["dateEcheance"] = str(echeance)
        
        if dictDonnees["nature"]=="AVO":
            dictDonnees["dateAvoir"] = dateFact
        elif dictDonnees["nature"]=="FAC":
            dictDonnees["dateFacturation"] = dateFact
        else:
            dictDonnees["dateFacturation"] = None
            dictDonnees["noFacture"] = None
            dictDonnees["dateAvoir"] = None
            dictDonnees["noAvoir"] = None

        # composition des valeurs matPiece à mettre à jour
        listeDonnees = [
            ("pieIDinscription", dictDonnees["IDinscription"]),
            ("pieIDprestation", dictDonnees["IDprestation"]),
            ("pieIDindividu", dictDonnees["IDindividu"]),
            ("pieIDfamille", dictDonnees["IDfamille"]),
            ("pieIDcompte_payeur", dictDonnees["IDcompte_payeur"]),
            ("pieIDactivite", dictDonnees["IDactivite"]),
            ("pieIDgroupe", dictDonnees["IDgroupe"]),
            ("pieIDcategorie_tarif", dictDonnees["IDcategorie_tarif"]),
            ("pieDateModif",str(datetime.date.today())),
            ("pieUtilisateurModif",self.user),
            ("pieNature", dictDonnees["nature"]),
            ("pieEtat",dictDonnees["etat"]),
            ("pieDateFacturation", dictDonnees["dateFacturation"]),
            ("pieNoFacture", dictDonnees["noFacture"]),
            ("pieDateAvoir", dictDonnees["dateAvoir"]),
            ("pieNoAvoir", dictDonnees["noAvoir"]),
            ("pieDateEcheance", dictDonnees["dateEcheance"]),
            ("pieCommentaire", GestionDB.Decod(dictDonnees["commentaire"])),
            ("pieIDtranspAller", dictDonnees["IDtranspAller"]),
            ("piePrixTranspAller", dictDonnees["prixTranspAller"]),
            ("pieIDtranspRetour", dictDonnees["IDtranspRetour"]),
            ("piePrixTranspRetour", dictDonnees["prixTranspRetour"]),
            ("pieIDparrain",dictDonnees["IDparrain"]),
            ("pieParrainAbandon",dictDonnees["parrainAbandon"]),
            ]
        retour = self.DB.ReqMAJ("matPieces", listeDonnees,"pieIDnumPiece",dictDonnees["IDnumPiece"],
                                MsgBox="GestionInscription.ModifiePiece")
        if retour != "ok" :
            GestionDB.MessageBox(parent,retour)
            return None
        if dictDonnees["nature"]=="AVO" and dictDonnees["noFacture"] != None :
            return None
        
        # Purge les lignes précédentes
        ret = self.DB.ReqDEL("matPiecesLignes", "ligIDNumPiece",dictDonnees["IDnumPiece"])
        if 'selfParrainage' in dictDonnees:
            for IDligne in dictDonnees['selfParrainage']['lstIDoldPar']:
                ret = self.DB.ReqDEL("matParrainages", "parIDlignePar", IDligne)
        # Enregistre dans PiecesLignes
        listeInit = [
            ("ligIDnumPiece", dictDonnees["IDnumPiece"]),
            ("ligDate",str(datetime.date.today())),
            ("ligUtilisateur", self.user),
            ]
        # recalcul du montant non forcé pour stockage avec valeur
        for item in dictDonnees["lignes_piece"]:
            if item["montant"] == 0:
                item["montant"] = (item["quantite"] * item["prixUnit"])

        listeLignesPiece = dictDonnees["lignes_piece"]
        if listeLignesPiece != None:
            for ligne in listeLignesPiece:
                listeDonnees = listeInit[:]
                listeDonnees.append(("ligCodeArticle",ligne["codeArticle"]))
                listeDonnees.append(("ligLibelle",ligne["libelle"]))
                listeDonnees.append(("ligQuantite",ligne["quantite"]))
                listeDonnees.append(("ligPrixUnit",round(ligne["prixUnit"],4)))
                if ligne["montant"] == 0:
                    ligne["montant"] = ligne["prixUnit"] * ligne["quantite"]
                listeDonnees.append(("ligMontant",round(ligne["montant"],2)))
                IDnumLigne = self.DB.ReqInsert("matPiecesLignes", listeDonnees,retourID = True)
                if not isinstance(IDnumLigne,int):
                    GestionDB.MessageBox(parent,self.DB.retour)
                    return None
                if 'selfParrainage' in dictDonnees:
                    dicParr = dictDonnees['selfParrainage']
                    if dicParr['codeArticle'] == ligne['codeArticle']:
                        dicParr['parIDligneParr'] = IDnumLigne
                        self.InsertParrain(self,dicParr)
        return retour
        #fin ModifiePiece

    # Modif de la pièce famille et de toutes ses dépendances
    def ModifiePiece999(self,parent,dictDonnees,nature):
        if len(dictDonnees['lignes_piece']) == 0:
            return  self.Suppression999(dictDonnees)

        # à supprimer toutes les lignes plus présentes
        lstLignesDel = [lig for lig in dictDonnees['lignes_pieceOrigine'] if not lig in dictDonnees['lignes_piece']]
        lstIDlignesDel = [lig['IDnumLigne'] for lig in lstLignesDel]

        # à insérer toutes les nouvelles lignes présentes
        lstLignesInsert = [lig for lig in dictDonnees['lignes_piece'] if not lig in dictDonnees['lignes_pieceOrigine']]

        # on ne modifie pas les lignes à inserer ou déja présentes sans changement
        lstLignesModif = [x for x in dictDonnees['lignes_piece'] if not ((x in lstLignesInsert)
                                                                         or (x in dictDonnees['lignes_pieceOrigine'])) ]

        mttOrigine = 0
        for lig in dictDonnees['lignes_pieceOrigine']:
            mttOrigine += lig['montant']
        mttNew = 0
        for lig in dictDonnees['lignes_piece']:
            if lig['montant'] == 0.0 and lig['quantite'] * lig['prixUnit'] != 0.0:
                lig['montant'] = lig['quantite'] * lig['prixUnit']
            mttNew += lig['montant']

        # contrôle cohérence programmation
        if (len(dictDonnees['lignes_pieceOrigine']) - len(lstIDlignesDel) + len(lstLignesInsert) - len(dictDonnees['lignes_piece'])) != 0:
            raise Exception("Revoir la programmation en GestionInscription.ModifiePieceTout, variation du nbre de ligne incorrecte")
        if len(dictDonnees['lignes_pieceOrigine'])  - len(lstIDlignesDel) < len(lstLignesModif):
            raise Exception("Revoir la programmation en GestionInscription.ModifiePieceTout, trop de modifs")

        # la nature héritée de la pièce individu,a pu changer celle de la piece
        if 'pieceOrigine' in dictDonnees:
            natureOld = dictDonnees['pieceOrigine']['nature']
            if natureOld != nature:
                ret = self.ChangeNaturePiece(self,dictDonnees,nature)
        # actions prestation
        if mttOrigine != mttNew:
            ret = self.ModifPrestationVentilation999(self.DB,dictDonnees)


        # action sur la pièce
        dateFact = self.DB.GetDateFacture(dictDonnees["IDinscription"],
                                     dictDonnees["IDactivite"],
                                     datetime.date.today())
        # recherche date d'échéance
        if dictDonnees["nature"] in  ('FAC','AVO'):
            dictActivite = self.GetActivite(dictDonnees["IDactivite"])
            dd = dictActivite["date_debut"]
            try:
                echeance = max(dd + datetime.timedelta(-30),datetime.date.today() + datetime.timedelta(10))
            except:
                echeance = datetime.date.today() + datetime.timedelta(10)
        else:
            echeance = datetime.date.today() + datetime.timedelta(10)
        dictDonnees["dateEcheance"] = str(echeance)

        if dictDonnees["nature"]=="AVO":
            dictDonnees["dateAvoir"] = dateFact
        elif dictDonnees["nature"]=="FAC":
            dictDonnees["dateFacturation"] = dateFact
        else:
            dictDonnees["dateFacturation"] = None
            dictDonnees["noFacture"] = None
            dictDonnees["dateAvoir"] = None
            dictDonnees["noAvoir"] = None

        # composition des valeurs matPiece à mettre à jour
        listeDonnees = [
            ("pieIDinscription", dictDonnees["IDinscription"]),
            ("pieIDprestation", dictDonnees["IDprestation"]),
            ("pieIDindividu", dictDonnees["IDindividu"]),
            ("pieIDfamille", dictDonnees["IDfamille"]),
            ("pieIDcompte_payeur", dictDonnees["IDfamille"]),
            ("pieIDactivite", dictDonnees["IDactivite"]),
            ("pieIDgroupe", dictDonnees["IDgroupe"]),
            ("pieIDcategorie_tarif", dictDonnees["IDcategorie_tarif"]),
            ("pieDateModif",str(datetime.date.today())),
            ("pieUtilisateurModif",self.user),
            ("pieNature", dictDonnees["nature"]),
            ("pieEtat",dictDonnees["etat"]),
            ("pieDateFacturation", dictDonnees["dateFacturation"]),
            ("pieNoFacture", dictDonnees["noFacture"]),
            ("pieDateAvoir", dictDonnees["dateAvoir"]),
            ("pieNoAvoir", dictDonnees["noAvoir"]),
            ("pieDateEcheance", dictDonnees["dateEcheance"]),
            ("pieCommentaire", GestionDB.Decod(dictDonnees["commentaire"])),
            ("pieIDtranspAller", dictDonnees["IDtranspAller"]),
            ("piePrixTranspAller", dictDonnees["prixTranspAller"]),
            ("pieIDtranspRetour", dictDonnees["IDtranspRetour"]),
            ("piePrixTranspRetour", dictDonnees["prixTranspRetour"]),
            ("pieIDparrain",dictDonnees["IDparrain"]),
            ("pieParrainAbandon",dictDonnees["parrainAbandon"]),
        ]
        retour = self.DB.ReqMAJ("matPieces", listeDonnees,"pieIDnumPiece",dictDonnees["IDnumPiece"],MsgBox="ModifiePiece")
        if retour != "ok" :
            GestionDB.MessageBox(parent,retour)
            return None
        if dictDonnees["nature"]=="AVO" and dictDonnees["noFacture"] != None :
            return None

        # Purge les lignes à supprimer dans matLignes et matParrainages
        for ID in lstIDlignesDel:
            ret = self.DB.ReqDEL("matPiecesLignes", "ligIDNumLigne",ID,MsgBox="GestionInscription.ModifiePiece999.del matPieceLigne")
            ret = self.DB.ReqDEL("matParrainages","parIDligneParr",ID,MsgBox="GestionInscription.ModifiePiece999.del matParrainages")

        # Enregistre dans PiecesLignes et matParrainages les nouvelles lignes
        listeInit = [
            ("ligIDnumPiece", dictDonnees["IDnumPiece"]),
            ("ligDate",str(datetime.date.today())),
            ("ligUtilisateur", self.user),]
        for ligne in lstLignesInsert:
            if ligne["montant"] == 0:
                ligne["montant"] = (ligne["quantite"] * ligne["prixUnit"])
            listeDonnees = [x for x in  listeInit ]
            listeDonnees.append(("ligCodeArticle",ligne["codeArticle"]))
            listeDonnees.append(("ligLibelle",ligne["libelle"]))
            listeDonnees.append(("ligQuantite",ligne["quantite"]))
            listeDonnees.append(("ligPrixUnit",round(ligne["prixUnit"],4)))
            if ligne["montant"] == 0:
                ligne["montant"] = ligne["prixUnit"] * ligne["quantite"]
            listeDonnees.append(("ligMontant",round(ligne["montant"],2)))
            IDnumLigne = self.DB.ReqInsert("matPiecesLignes", listeDonnees,retourID = True)
            if not isinstance(IDnumLigne,int):
                GestionDB.MessageBox(parent,self.DB.retour)
                return None
            if 'dicParrainages' in list(dictDonnees.keys()):
                for IDinscription, dicParr in dictDonnees['dicParrainages'].items():
                    if dicParr['codeArticle'] == ligne['codeArticle']:
                        dicParr['parIDligneParr'] = IDnumLigne
                        self.InsertParrain(self,dicParr)

        # modifie les lignes changées
        for ligne in lstLignesModif:
            if ligne["montant"] == 0.0:
                ligne["montant"] = (ligne["quantite"] * ligne["prixUnit"])
            elif ligne["quantite"] != 0:
                ligne["prixUnit"] = (ligne["montant"] / ligne["quantite"])
            listeDonnees = [x for x in  listeInit ]
            listeDonnees.append(("ligCodeArticle",ligne["codeArticle"]))
            listeDonnees.append(("ligLibelle",ligne["libelle"]))
            listeDonnees.append(("ligQuantite",ligne["quantite"]))
            listeDonnees.append(("ligPrixUnit",round(ligne["prixUnit"],4)))
            if ligne["montant"] == 0:
                ligne["montant"] = ligne["prixUnit"] * ligne["quantite"]
            listeDonnees.append(("ligMontant",round(ligne["montant"],2)))
            ret = self.DB.ReqMAJ("matPiecesLignes", listeDonnees, 'ligIDnumLigne', ligne['IDnumLigne'])
            if ret != "ok":
                GestionDB.MessageBox(parent,self.DB.retour)
                return None
            if 'dicParrainages' in list(dictDonnees.keys()):
                for IDinscription, dicParr in dictDonnees['dicParrainages'].items():
                    if dicParr['codeArticle'] == ligne['codeArticle']:
                        dicParr['parIDligneParr'] = IDnumLigne
                        self.InsertParrain(self,dicParr)
        return retour
        #fin ModifiePiece

    def ModifieConsommations(self,parent,dictDonnees,fromInscr=None):
        if dictDonnees["nature"] in ("AVO","DEV"):
            wx.MessageBox("Consommation à supprimer si avoir, pas à modifier","Cf program")
            return False

        if not fromInscr:
            self.DB.ReqDEL("consommations", "IDinscription", dictDonnees["IDinscription"])
            return self.AjoutConsommations(parent,dictDonnees)
        # modification de l'existant
        else:
            lstChamps = ["IDcons","IDindividu","IDactivite"]
            where = "IDinscription = %d"%fromInscr
            mess = "GestionInscription.ModifieConsommations"
            ltConsos =  DATA_Tables.GetDdRecords(self.DB,where,lstChamps,mess)
            lstID = []
            for IDcons, IDind, IDact in ltConsos:
                if dictDonnees["IDindividu"] == IDind and dictDonnees["IDactivite"] == IDact:
                    lstID.append(IDcons)
            lstDonnees = [
                ("IDindividu", dictDonnees["IDindividu"]),
                ("IDinscription", dictDonnees["IDinscription"]),
                ("IDactivite", dictDonnees["IDactivite"]),
                ("IDcompte_payeur", dictDonnees["IDfamille"]),
               ]
            for ID in lstID:
                ret = self.DB.ReqMAJ("consommations",lstDonnees,"IDconso",ID)
                if ret != "ok":
                    break
        return ret

    def ModifieConsoCree(self,parent,dictDonnees):
        listeDonnees = [
            ("IDprestation", dictDonnees["IDprestation"]),
            ("IDcompte_payeur", dictDonnees["IDcompte_payeur"]),
            ]
        retour = self.DB.ReqMAJ("consommations", listeDonnees,"IDinscription",dictDonnees["IDinscription"])
        if retour != "ok" :
            GestionDB.MessageBox(parent,retour)
        return retour

    def PieceModifiable(self,parent,dictDonnees) :
        if len(dictDonnees["etat"])<4 : return True
        #etatFacture = int(dictDonnees["etat"][3])
        if dictDonnees["nature"] in ("FAC","AVO"):
            #if etatFacture > 2:return False
            return False
        return True

    def SupprReducParrainage(self, parIDligneParr,IDfamFilleul=None):
        # Tente la suppression d'une ligne de réduction parrainage chez le parrain
        if not parIDligneParr > 0:
            return False
        req = """
            SELECT matPieces.pieIDnumPiece, matPieces.pieIDinscription, 
                matPieces.pieNature, matPieces.pieIDfamille, familles.adresse_intitule, 
                matPiecesLignes.ligLibelle, matPiecesLignes.ligMontant,
                matPiecesLignes.ligIDnumLigne
            FROM (matPiecesLignes 
            INNER JOIN matPieces ON matPiecesLignes.ligIDnumPiece = matPieces.pieIDnumPiece) 
            LEFT JOIN familles ON matPieces.pieIDfamille = familles.IDfamille
            WHERE (matPiecesLignes.ligIDnumLigne = %d)
            ;"""%parIDligneParr
        ret = self.DB.ExecuterReq(req,MsgBox="GestionInscription.SupprLigneParrainage")
        if ret != "ok" :
            return False
        recordset = self.DB.ResultatReq()
        retDel = None
        for IDpiece,IDinscription,nature,IDfamille,nom,libelle,montant,IDligne in recordset:
            if nature == 'FAC' :
                mess = "Réduction parrainage à annuler\n\n"
                mess +="La famille %d %s a bénéficié d'une réduction de facture:\n"%(IDfamille,nom,)
                mess += "%.2f€ '%s'"%(montant,libelle)
                mess += "Il convient de refacturer l'annulation de ce parrainage"
                wx.MessageBox(mess,"A FAIRE",style=wx.ICON_WARNING)
            elif nature == 'AVO':
                # la réduc pratiquée a été annulée par l'avoir
                pass
            elif IDfamFilleul == IDfamille:
                # c'était un abandon à filleul dans la pièce qui va être supprimée
                pass
            else:
                # Suppression d'une ligne dans la pièce du parrain non facturée
                retDel = self.DB.ReqDEL('matPiecesLignes','ligIDnumLigne',IDligne,
                               MsgBox="SupprReducParrainage.matPiecesLignes")
            self.DB.ReqDEL('matParrainages', 'parIDligneParr', IDligne,
                           MsgBox="SupprReducParrainage.matParrainages")

            mess = "Inscription parrainée\n\n"
            mess += "La famille %d %s avait bénéficié d'une réduction de facture:\n" % (
                IDfamille, nom,)
            if retDel == 'ok':
                mess += "Cette ligne de réduction a été enlevée"
            else: mess += "Il FAUT REFACTURER LE parrain de cette annulation"
            wx.MessageBox(mess, "INFO IMPORTANTE",style=wx.ICON_WARNING)
        return True

    def InsertParrain(self, parent, dictParrain):
        # enregistre dans la table matParainages
        lstChamps = ['parIDinscription','parIDligneParr','parAbandon']
        listeDonnees = DictToListeTuples(lstChamps, dictParrain)
        IDuser = self.DB.IDutilisateurActuel()
        listeDonnees.append(('parSolde',7000 + IDuser))
        ret = self.DB.ReqInsert("matParrainages",listeDonnees,retourID=False)
        if ret != "ok" :
            del listeDonnees[0]
            ret = self.DB.ReqMAJ("matParrainages", listeDonnees, 'parIDinscription', dictParrain['parIDinscription'])
            if ret != "ok":
                GestionDB.MessageBox("Modif matParrainages",ret)
        return

    def GetNomParrain(self,DB,IDparrain):
        # appel du nom de famille d'un parrain
        nom = "Inconnu"
        req = """SELECT familles.adresse_intitule
                FROM familles
                WHERE (familles.IDfamille = %d)
                ;"""%IDparrain
        ret = DB.ExecuterReq(req, MsgBox='GestionInscription.Suppression')
        if ret == 'ok':
            recordset = DB.ResultatReq()
            for record in recordset:
                nom = record[0]
        return nom

    def ParrainageIsImpute(self,DB,IDinscription):
        # vérifie si un parrainage est imputé
        test = False
        req = """SELECT matParrainages.parIDligneParr
                FROM matParrainages
                WHERE (matParrainages.parIDinscription=%d);
                """%IDinscription
        ret = DB.ExecuterReq(req, MsgBox='GestionInscription.Suppression')
        if ret == 'ok':
            recordset = DB.ResultatReq()
            for record in recordset:
                if record[0]>0:
                    test = True
        return test

    def SuppressionInscription(self,IDinscription):
        #pour cette inscription suppression des consos et prestation éventuelle
        conditions = "IDinscription = %d" % (IDinscription)
        req =  """
            SELECT IDindividu, IDfamille,IDactivite,IDcategorie_tarif,IDgroupe
            FROM inscriptions WHERE IDinscription = %d;"""%IDinscription
        retour = self.DB.ExecuterReq(req,MsgBox="GestionInscription.SuppressionInscription_1")
        if retour != "ok" :
            return False
        retour = self.DB.ResultatReq()
        if len(retour) == 0:
            wx.MessageBox("Inscription '%d' non trouvée!!"%IDinscription,"Problème",style=wx.ICON_ERROR)
            return

        # recherche d'un éventuel IDprestation correspondant à l'inscription de manière floue
        for IDindividu, IDfamille,IDactivite,IDcategorie_tarif,IDgroupe in retour :
            req =  """
            SELECT IDprestation
            FROM prestations 
            WHERE  (compta IS NULL)
                    AND (IDfamille = %d)
                    AND (IDindividu = %d)
                    AND (IDactivite = %d)
                    AND (IDcategorie_tarif = %d)            
            ;"""%(IDfamille,IDindividu,IDactivite,IDcategorie_tarif)
            retour = self.DB.ExecuterReq(req,MsgBox="GestionInscription.SuppressionInscription_2")
            IDprestation = None
            if retour == "ok" :
                retour = self.DB.ResultatReq()
                if len(retour)>0:
                    IDprestation = retour[0][0]
            # suppression de l'inscription
            self.DB.ReqDEL("consommations", "IDinscription", IDinscription)
            self.DB.ReqDEL("inscriptions", "IDinscription", IDinscription)
            if IDprestation:
                self.DB.ReqDEL("deductions", "IDprestation", IDprestation)
                self.DB.ReqDEL("ventilation", "IDprestation", IDprestation)
                self.DB.ReqDEL("prestations", "IDprestation", IDprestation)
        #fin SuppressionInscription

    def SuppressionPiece(self, parent, dictDonnees):
        #suppression d'une pièce non facturée et de tout ce qui va avec
        IDinscription = dictDonnees["IDinscription"]
        IDprestation = dictDonnees["IDprestation"]
        IDnumPiece = dictDonnees["IDnumPiece"]
        IDtranspAller = dictDonnees["IDtranspAller"]
        IDtranspRetour = dictDonnees["IDtranspRetour"]

        # suppression du transport
        self.SupprimeTransport(IDtranspAller)
        self.SupprimeTransport(IDtranspRetour)

        # suppression du parrainage affecté
        if dictDonnees['IDparrain'] and dictDonnees['IDparrain'] > 0 :
            mess = "GestionInscription.Suppression.recherche_parrainage"
            where = "parIDinscription = %d"%IDinscription
            ddParrainages = DATA_Tables.GetDdRecords(self.DB,
                                                     'matParrainages',
                                                     where=where,mess=mess)
            for IDinscr,dictPar in ddParrainages.items():
                ret = self.SupprReducParrainage(dictPar['parIDligneParr'],dictDonnees['IDfamille'])

        # alerte suppression du parrainage
        if self.ParrainageIsImpute(self.DB, dictDonnees["IDinscription"]):
            if not dictDonnees["IDparrain"]:
                dictDonnees["IDparrain"]=0
            nomParrain = self.GetNomParrain(self.DB,dictDonnees['IDparrain'])
            parrain = "Parrain : %d - %s\nRetournez sur sa fiche"%(dictDonnees["IDparrain"],nomParrain)
            wx.MessageBox("Inscription parrainée!\n\n%s"%parrain)

        # suppression de la pièce et de ses lignes
        self.DB.ReqDEL("matPiecesLignes", "ligIDNumPiece", IDnumPiece)
        self.DB.ReqDEL("matPieces", "pieIDNumPiece", IDnumPiece)

        # suppression des liens prestation dans prestations, ventilations, deductions
        if IDprestation != None:
            self.DB.ReqDEL("deductions", "IDprestation", IDprestation)
            self.DB.ReqDEL("ventilation", "IDprestation", IDprestation)
            self.DB.ReqDEL("prestations", "IDprestation", IDprestation)

        # supression des liens inscription, conso
        if IDinscription != None:
            self.DB.ReqDEL("consommations", "IDinscription", IDinscription)
            self.DB.ReqDEL("inscriptions", "IDinscription", IDinscription)

        #fin Suppression

    def Suppression999(self,dictDonnees):
        # suppression d'une pièce niveau famille
        if "IDnumPiece" in dictDonnees:
            # suppression de la pièce et des parrainages qu'elle peut contenir
            IDnumPiece = dictDonnees["IDnumPiece"]
            req = """
                SELECT matParrainages.parIDligneParr
                FROM matPieces 
                INNER JOIN (matPiecesLignes 
                    INNER JOIN matParrainages 
                    ON matPiecesLignes.ligIDnumLigne = matParrainages.parIDligneParr) 
                ON matPieces.pieIDnumPiece = matPiecesLignes.ligIDnumPiece
                WHERE (matPiecesLignes.ligIDnumPiece = %d);""" %IDnumPiece
            ret = self.DB.ExecuterReq(req,MsgBox='Suppression999')
            if ret == "ok" :
                records = self.DB.ResultatReq()
                for ligIDnumLigne in records:
                    self.DB.ReqDEL("matParrainages", "parIDligneParr", ligIDnumLigne)
            self.DB.ReqDEL("matPiecesLignes", "ligIDNumPiece", IDnumPiece)
            self.DB.ReqDEL("matPieces", "pieIDNumPiece", IDnumPiece)
        if "IDprestation" in dictDonnees:
            IDprestation = dictDonnees["IDprestation"]
            if IDprestation != None:
                self.DB.ReqDEL("deductions", "IDprestation", IDprestation)
                self.DB.ReqDEL("ventilation", "IDprestation", IDprestation)
                self.DB.ReqDEL("prestations", "IDprestation", IDprestation)
        #fin Suppression999

    def DelConsommations(self,parent,dictDonnees=None):
        if not dictDonnees:
            dictDonnees = parent.dictDonnees
        # Suppression consommations
        IDinscription = dictDonnees["IDinscription"]
        if IDinscription != None:
            return self.DB.ReqDEL("consommations", "IDinscription", IDinscription)

    def DelPrestations(self,parent,dictDonnees=None):
        if not dictDonnees:
            dictDonnees = parent.dictDonnees
        # Suppression prestations
        IDprestation = dictDonnees["IDprestation"]
        IDnumPiece = dictDonnees["IDnumPiece"]
        ret = "ko"
        if "compta" in dictDonnees and dictDonnees["compta"] != None:
            # sécurité: pas modifier une prestation transférée en compta
            return ret
        if IDprestation != None:
            ret = self.DB.ReqDEL("prestations", "IDprestation", IDprestation)
            if ret =="ok": ret = self.DB.ReqDEL("deductions", "IDprestation", IDprestation)
            if ret =="ok": ret = self.DB.ReqDEL("ventilation", "IDprestation", IDprestation)
            if ret =="ok" and IDnumPiece and IDnumPiece != 0:
                ret = self.DB.ExecuterReq("""
                    UPDATE matPieces 
                    SET pieIDprestation = NULL 
                    WHERE pieIDnumPiece = %d
                    ;""" % IDnumPiece,MsgBox = "GestionInscr.DelPrestation")
        dictDonnees["IDprestation"] = None
        return ret

    def RetroFact(self,parent,dictDonnees):
        if dictDonnees["comptaFac"] != None:
            date = DateIntToString(dictDonnees["comptaFac"])
            GestionDB.MessageBox(self.parent,"Cette facture a été transférée en compta le %s" % date, titre="Traitement impossible")
            return
        if dictDonnees["noAvoir"] != None:
            GestionDB.MessageBox(self.parent,"Cette facture a un no d'avoir !\nProblème logique", titre="Traitement impossible")
            return
        #Rétrogradation d'une piece de type facture en commande
        if dictDonnees["noFacture"] == None:
            GestionDB.MessageBox(self.parent,"Cette facture n'a pas de no de facture !\nProblème logique", titre="Traitement impossible")
        else:
            DB = GestionDB.DB()
            pGest = GestionPieces.Forfaits(parent)
            #recharge la pièce pour avoir tous les champs
            ok = self.GetPieceModif(self.parent,None,None,IDnumPiece=dictDonnees['IDnumPiece'])
            dictDonnees = self.dictPiece
            commentaire = Decod(dictDonnees['commentaire'])
            if commentaire == None: commentaire = " -\n"
            #on traite le numero facture
            ligneComm = " "
            action = ""
            if pGest.FactureMonoPiece(dictDonnees["noFacture"],dictDonnees["IDnumPiece"]):
                # suppression de la facture et stockage du numéro
                if pGest.DestroyFacture(dictDonnees["noFacture"],dictDonnees["IDcompte_payeur"]):
                    DB.SetParam(param = str(dictDonnees["noFacture"]),value= dictDonnees["noFacture"],user = "NoLibre",
                                type = "integer",unique=False)
                    ligneComm = " Suppression Facture %s " % dictDonnees['noFacture']
                    action = "SuppressionFacturation"
            else:
                # simple diminution du montant de la facture
                mtt = Nz(dictDonnees["total"])+ Nz(dictDonnees["prixTranspAller"]) +  Nz(dictDonnees["prixTranspRetour"])
                pGest.ReduitFacture(dictDonnees["noFacture"],mtt,dictDonnees["IDprestation"])
                ligneComm = " Rétrogradation %s " % dictDonnees['nature']
                action = "ModificationFacturation"
            commentaire = datetime.date.today().strftime("%d/%m/%y : ") + ligneComm + "\n" + commentaire
            #force à None l'IDfacture dans la prestation
            DB.ReqMAJ('prestations',[('IDfacture',None),],'IDprestation',dictDonnees['IDprestation'],MsgBox = 'RAZ IDfacture en prestation')
            #on traite la pièce
            DB.ReqMAJ('matPieces',[('pieNoFacture',None),('pieNoAvoir',None),('pieNature','COM'),
                                   ('pieDateFacturation',None),('pieDateAvoir',None),
                                   ('pieCommentaire',commentaire)],
                      'pieIDnumPiece',dictDonnees["IDnumPiece"],MsgBox = 'qGestionInscription.Retrofac')
            self.Historise(dictDonnees['IDindividu'],dictDonnees['IDfamille'],action,ligneComm)
            del pGest
        #fin RetroFact

    def RetroAvo(self,parent,dictDonnees):
        #Rétrogradation d'une piece de type Avoir en Facture normale
        if dictDonnees["comptaAvo"] != None:
            date = DateIntToString(dictDonnees["comptaAvo"],format = "%d/%m/%Y")
            GestionDB.MessageBox(self.parent,"Cet Avoir a été transférée en compta le %s\nVous pouvez faire un complement en saisie d'inscription" % date, titre="Traitement impossible")
            return
        if dictDonnees["noAvoir"] == None:
            GestionDB.MessageBox(self,"Cette pièce n'est pas un avoir !", titre="Traitement impossible")
        else:
            DB = GestionDB.DB()
            pGest = GestionPieces.Forfaits(parent)
            #recharge la pièce pour avoir tous les champs
            ok = self.GetPieceModif(self.parent,None,None,IDnumPiece=dictDonnees['IDnumPiece'])
            dictDonnees = self.dictPiece
            commentaire = Decod(dictDonnees['commentaire'])
            if commentaire == None: commentaire = " -\n"
            #on traite le numero avoir
            ligneComm = " "
            action = ""
            #récupérer l'IDfacture pour recherche ultérieur
            IDfacture = 0
            req = """ SELECT IDfacture
                    FROM factures
                    WHERE numero = %d;
                      """ % (dictDonnees["noAvoir"])
            ret = DB.ExecuterReq(req,MsgBox="GestionInscription.RestoAvo")
            if ret != "ok" :
                GestionDB.MessageBox(self,ret)
                DB.Close()
                return None
            recordset = DB.ResultatReq()
            if len(recordset)>0:
                IDfacture = recordset[0][0]

            if pGest.FactureMonoPiece(dictDonnees["noAvoir"],dictDonnees["IDnumPiece"]):
                # suppression de l'avoir et stockage du numéro
                if pGest.DestroyFacture(dictDonnees["noAvoir"],dictDonnees["IDcompte_payeur"]):
                    DB.SetParam(param = str(dictDonnees["noFacture"]),value= dictDonnees["noAvoir"],
                                user = "NoLibre",type = "integer",unique=False)
                    ligneComm = " Suppression Avoir %s " % dictDonnees['noAvoir']
                    action = "SuppressionFacturation"
            else:
                # Modification du montant de la facture
                mtt = Nz(dictDonnees["total"])+ Nz(dictDonnees["prixTranspAller"]) +  Nz(dictDonnees["prixTranspRetour"])
                pGest.ReduitFacture(dictDonnees["noAvoir"],-mtt,dictDonnees["IDprestation"])
                ligneComm = " Rétrogradation %s " % dictDonnees['nature']
                action = "ModificationFacturation"
            commentaire = datetime.date.today().strftime("%d/%m/%y : ") + ligneComm + "\n" + commentaire
            #pour supprimer la prestation il faut récupérer son ID
            req = """ SELECT prestations.IDprestation
                    FROM prestations INNER JOIN matPieces ON (prestations.IDactivite = matPieces.pieIDactivite) AND (prestations.IDindividu = matPieces.pieIDindividu)
                    WHERE prestations.IDfacture = %d;
                      """ % (IDfacture)
            retout = DB.ExecuterReq(req,MsgBox="GestionInscription.RestoAvo")
            if retout != "ok" :
                GestionDB.MessageBox(self,retout)
                DB.Close()
                return None
            recordset = DB.ResultatReq()
            for record in recordset :
                IDprestAvoir = record[0]
                DB.ReqDEL('prestations','IDprestation',IDprestAvoir,True,MsgBox = 'GestionInscription.RetroFact prestation Avoir')
            DB.ReqMAJ('matPieces',[('pieNoAvoir',None),('pieDateAvoir',None),('pieNature','FAC'),
                                   ('pieCommentaire',commentaire)],
                      'pieIDnumPiece',dictDonnees["IDnumPiece"],MsgBox = 'qGestionInscription.RetroAvoir')
            dictDonnees["nature"]='FAC'
            self.Historise(dictDonnees['IDindividu'],dictDonnees['IDfamille'],action,ligneComm)
            #remet les consos
            if dictDonnees["IDindividu"] != 0:
                self.AjoutConsommations(self,dictDonnees)
            DB.Close()
        #fin RetroAvo

    def NeutraliseReport(self,IDcomptePayeur,IDindividu,IDactivite):
        dlg = wx.ID_ABORT
        if IDindividu != None:
            condition = "inscriptions.IDindividu = %d AND inscriptions.IDactivite = %d" % (IDindividu, IDactivite)
            dlg = GestionDB.MessageBox(self.parent,  _("Souhaitez-vous neutraliser cette inscriptions pour la refaire ?"), titre = "NeutraliseReport", YesNo = True)
        # Gestion des inscriptions importées qui ne permettront pas de calculer les réductions
        if dlg != wx.ID_YES:
            print("KO !")
            return
        #Suppresion des consommations et inscriptions
        req = """SELECT inscriptions.IDinscription, activites.date_debut,activites.date_fin
                FROM inscriptions
                INNER JOIN activites ON inscriptions.IDactivite = activites.IDactivite
                WHERE %s ; """ % (condition)
        retour = self.DB.ExecuterReq(req,MsgBox="GestionInscription.NeutraliseReport")
        if retour != "ok" :
            return None
        recordset = self.DB.ResultatReq()
        listeInscriptions = []
        for IDinscription, dateDebut, dateFin in recordset :
            listeInscriptions.append(IDinscription)

        if len(listeInscriptions)>0 :
            for IDinscription in listeInscriptions:
                self.DB.ReqDEL("consommations","IDinscription",IDinscription,True,MsgBox="Neutral Conso")
                self.DB.ReqDEL("inscriptions","IDinscription",IDinscription,True,MsgBox="Neutral Inscription")

        #neutralisation des prestations et des ventilations
        if IDindividu == None:
            condition = "IDcompte_payeur = %d " % IDcomptePayeur
        else:
            from Dlg import DLG_Famille_prestations
            dlg = DLG_Famille_prestations.Dialog(self.parent, IDcomptePayeur)
            dlg.panel.MAJ()
            dlg.ShowModal()
            self.selection = dlg.panel.ctrl_prestations.Selection()

            condition = "IDindividu = %d AND IDactivite = %d" % (IDindividu, IDactivite)

        req = """SELECT prestations.IDprestation, prestations.date,prestations.montant
                FROM prestations
                WHERE %s;
                """ % (condition)
        retour = self.DB.ExecuterReq(req,MsgBox="GestionInscription.NeutraliseReport")
        if retour != "ok" :
            GestionDB.MessageBox(self.parent,retour)
            return None
        recordset = self.DB.ResultatReq()
        bascule = DateEngEnDateDD("2016-12-31")
        listeIDprestations = []
        listePrestations = []
        for IDprestation, date, montant in recordset :
            dateDD = DateEngEnDateDD(date)
            if (dateDD == bascule) or (montant == 7):
                listePrestations.append((IDprestation,montant))
                listeIDprestations.append(IDprestation)
        if len(listePrestations)>0:
            listePrestationsNeutr=[]
            condition = " IDprestation IN ("+ str(listeIDprestations)[1:-1]+ ")"
            champs = ["IDprestation","IDcompte_payeur", "date", "label", "categorie", "montant_initial", "montant", "IDactivite", "IDtarif", "IDfamille", "IDindividu", "forfait", "IDcategorie_tarif"]
            listeSql = ", ".join(champs)
            req =  "SELECT " + listeSql + " FROM prestations WHERE " + condition
            retour = self.DB.ExecuterReq(req,MsgBox="GestionInscription.NeutraliseReport")
            if retour != "ok" :
                GestionDB.MessageBox(self.parent,retour)
                return None
            recordset = self.DB.ResultatReq()
            dictPrestations = RecordsToListeDict(champs,recordset)
            for IDprestation,dictPrestation in dictPrestations:
                # génération d'une prestation de neutralisation
                dictPrestation["montant"] = -1 * dictPrestation["montant"]
                dictPrestation["label"] = "Annul "+ dictPrestation["label"]
                dictPrestation["categorie"] = "importAnnul"
                dictPrestation["date"] = str(datetime.date.today())
                listeDonnees = DictToListeTuples(champs[1:],dictPrestation)
                # Insertion de la prestation
                self.DB.ReqInsert("prestations", listeDonnees, retourID=True, MsgBox="Neutralise prestation")
                listePrestationsNeutr.append((self.DB.newID,dictPrestation["montant"]))
            # génération d'un réglement à zéro pour les ventilations.
            listeDonnees = [
                ("IDcompte_payeur" ,IDcomptePayeur ),
                ("date" , datetime.date.today() ),
                ("IDmode" , 7 ),
                ("montant" , 0 ),
                ("IDcomptePayeur" , IDcomptePayeur ),
                ("IDcompte" , 1 ),
                ("encaissement_attente" , 0 ),
                ("date_saisie" , datetime.date.today() )]
                # Insertion de la prestation
            self.DB.ReqInsert("reglements", listeDonnees, retourID=True, MsgBox="Reglement zero")
            IDreglement = self.DB.newID
            # génération des ventilations.
            for IDprestation, montant in listePrestations:
                listeDonnees = [
                    ("IDcompte_payeur" ,IDcomptePayeur ),
                    ( "IDreglement" , IDreglement ),
                    ( "IDprestation" , IDprestation ),
                    ( "montant" , montant)]
                self.DB.ReqInsert("ventilation", listeDonnees, retourID=False, MsgBox="Ventilation")
            for IDprestation, montant in listePrestationsNeutr:
                listeDonnees = [
                    ("IDcompte_payeur" ,IDcomptePayeur ),
                    ( "IDreglement" , IDreglement ),
                    ( "IDprestation" , IDprestation ),
                    ( "montant" , montant)]
                self.DB.ReqInsert("ventilation", listeDonnees, retourID=False, MsgBox="Ventilation")
        return
        #fin NeutraliseReport

    def GetDictDonnees(self,parent,listeDonnees):
        nom_individu = self.DB.GetNomIndividu(parent.IDindividu)
        nom_famille = self.DB.GetNomIndividu(parent.IDfamille)
        listeDonnees2 = [
            ("nom_individu", nom_individu),
            ("nom_famille", nom_famille),
            ]
        dictDonnees = {}
        for donnee in listeDonnees + listeDonnees2 :
            champ = donnee[0]
            valeur = donnee[1]
            dictDonnees[champ] = valeur
        return dictDonnees
        #fin GetDictDonnees

    def ModifDictDonnees(self,parent,listeDonnees):
        # Enrichissement de dictDonnees par liste de tuples
        dictDonnees = parent.dictDonnees
        for donnee in listeDonnees :
            champ = donnee[0]
            valeur = donnee[1]
            dictDonnees[champ] = valeur
        return dictDonnees
        #fin AjoutDictDonnees

    def GetPayeurFamille(self,parent, IDfamille = None) :
        #Récupère le compte_payeur par défaut de la famille
        req = """SELECT IDfamille, IDcompte_payeur
        FROM familles
        WHERE IDfamille=%d;""" % IDfamille
        retour = self.DB.ExecuterReq(req,MsgBox="GestionInscription.GetPayeurFamille")
        if retour != "ok" :
            GestionDB.MessageBox(parent,retour)
            return None
        listeDonnees = self.DB.ResultatReq()
        if len(listeDonnees) == 0 : return None
        IDcompte_payeur = listeDonnees[0][1]
        return IDcompte_payeur

    def GetFamille(self,parent):
        # Fixe IDfamille listeFamille (unique) listeNOms (des membres ) si l'individu est rattaché à d'autres familles
        parent.listeNoms = []
        parent.listeFamille = []
        # Vérifie que l'individu est rattaché comme REPRESENTANT ou ENFANT à une famille
        if parent.dictFamillesRattachees == None: return False
        valide = False
        self.nbreFamilles = 0
        msg = GestionDB.Messages()
        lastIDfamille = None
        for parent.IDfamille, dictFamille in parent.dictFamillesRattachees.items() :
            if dictFamille["IDcategorie"] in (1, 2) :
                self.nbreFamilles += 1
                lastIDfamille = parent.IDfamille
                valide = True
        if valide == False :
            msg.Box(message = "Pour être inscrit à une activité, un individu doit obligatoirement être\nrattaché comme représentant ou enfant à une fiche famille !")
            return False
        if self.nbreFamilles == 1 :
            parent.IDfamille = lastIDfamille
            parent.listeFamille.append(lastIDfamille)
            parent.listeNoms.append(parent.dictFamillesRattachees[parent.IDfamille]["nomsTitulaires"])
        else:
            # Si rattachée à plusieurs familles
            listeTuplesFamilles = []
            for IDfamille, dictFamille in parent.dictFamillesRattachees.items() :
                IDcategorie = dictFamille["IDcategorie"]
                if IDcategorie in (1, 2) :
                    parent.listeFamille.append(IDfamille)
                    parent.listeNoms.append(dictFamille["nomsTitulaires"])
                    listeTuplesFamilles.append((IDfamille,dictFamille["nomsTitulaires"]))
            # On demande à quelle famille rattacher cette inscription
            retour = GestionDB.Messages().Choix(listeTuples=listeTuplesFamilles, titre = ("Cet individu est rattaché à %d familles")
                    % len(parent.listeNoms), intro = "Double clic pour rattacher cette inscription à une famille !")
            ixChoix = retour[0]
            famille = retour[1]
            if  ixChoix != None:
                parent.IDfamille = ixChoix
                parent.nom_famille = famille
            else:
                return False
        return True
        #fin GetFamille

    def Historise(self,IDindividu,IDfamille,action, commentaire):
        try:
            comment = "%s"%commentaire
        except: comment = Decod(commentaire)

        # Mémorise l'action dans l'historique
        if action in DictActions :
            IDcat = DictActions[action]
            texte = "'%s'"%comment
        else :
            mess = "Transmettre au développeur:\n\nHistorisation action '%s' non codée\n"%action
            mess += "cf GestionInscription.Historise"
            wx.MessageBox(mess, "Problème mineur à signaler")
            IDcat = None
            texte = "%s'%s'"%(action,comment)

        UTILS_Historique.InsertActions([{
            "IDindividu" : IDindividu,
            "IDfamille" : IDfamille,
            "IDcategorie" : IDcat,
            "action" : texte
            },],self.DB)

# --------------------Lancement de test ----------------------
if __name__ == "__main__":
    app = wx.App(0)
    listeDonnees = [
        ("IDinscription", None),
        ("IDindividu", 6163),
        ("IDfamille", 6163),
        ("IDactivite", 221),
        ("IDgroupe", 442),
        ("IDcategorie_tarif", 795),
        ("IDcompte_payeur", 6163),
        ("date_inscription", str(datetime.date.today())),
        ("parti", False),
        ("nature", "COM"),
        ("nom_activite", "Sejour 41"),
        ("nom_groupe", "Groupe Pasto Plus"),
        ("nom_categorie", "Tarif Normal"),
        ("nom_individu", "nom de  l'individu"),
        ("nom_famille", "nom de la famille"),
        ("lignes_piece", [("art","test article",150.70),]),
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
    f = Forfaits(None)
    retour = f.GetOuvertures(688,1923)
    print(retour)
    app.MainLoop()

