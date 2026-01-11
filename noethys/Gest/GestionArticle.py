#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#----------------------------------------------------------
# Application :    Matthania
# Auteur:          Jacques BRUNEL
# Licence:         Licence GNU GPL
# Fonctions calculs prix articles et application des conditions
# Contient aussi les listes descriptives des calculs et conditions
#-----------------------------------------------------------

import GestionDB
from Gest import GestionInscription
from Ctrl import CTRL_SaisieSimple
from Ctrl import CTRL_ChoixListe
import wx
import copy
import datetime
from Data import DATA_Tables

def Nz(valeur):
    if not valeur:
        valeur = 0
    return valeur

def AvecCondition(obj):
    if obj.condition in ('Sans',None,'ZZZ',''):
        return False
    return True

def AvecCalcul(obj):
    if obj.modeCalcul in ('Sans',None,''):
        return False
    return True

# Listes de parametres :

LISTEnaturesPieces = [
        ("DEV", "Devis", "Le devis n'enregistre pas de consommation, seulement l'inscription", ),
        ("RES", "Reservation", "La réservation enregistre l'inscription, la consommation pas la prestation", ),
        ("COM", "Commande", "La commande enregistre la prestation qui est due selon l'engagement reçu", ),
        ]

LISTEnaturesPiecesFac = [
        ("FAC", "Facture", "La Facture se transfère en compta, n'est plus modifiable, s'annule par un avoir", ),
        ("AVO", "Facture&AvoirGlobal", "Facture annulée par un Avoir Global par suppression d'une inscription facturée ou Faire Avoir", )
        ]

# les états sont déclinés sur 5 positions correspondant à chacune des natures successives possibles
LISTEetatsPieces = [
        ("0", "Non Fait", "Problème : Pas d'état pour cette nature de pièce", ),
        ("1", "Juste Créé", "nouvellement dans cette nature", ),
        ("2", "Imprimé", "dans cette nature", ),
        ("4", "|Transféré", "modif impossible", ),
        ]

# réductions en € selon le nombre d'inscriptions
LISTEredCumul = [0,40,50,60,70]

LISTEconditions = [
        ("Sans", "Pas de condition particulière\nsans condition = toujours réalisée", None, ),
        ("ZZZ", "Article obsolète, n'est plus proposé\nzzz condition jamais réalisée", False, ),
        ("AG0-2", "Enfant jusqu'à 3 ans\nAge >=0 et <3", "CondAg0_2", ),
        ("AG3-5", "Enfant de 3 à 5 ans\nAge >=3 et <6", "CondAg3_5", ),
        ("AG6-11", "Enfant de 6  à 11 ans\nAge >=6 et <12", "CondAg6_11", ),
        ("Annuelle", "N'apparaît qu'une fois dans l'année académique pour individu\nCf mode de calcul",  "CondAnnuelle",),
        ("Civile", "N'apparaît qu'une fois dans l'année civile pour individu\nCf mode de calcul",  "CondCivile",),
        ("AnnuelleFam", "N'apparaît qu'une fois dans l'année académique pour famille\nCf mode de calcul",  "CondAnnuFam",),
        ("CivileFam", "N'apparaît qu'une fois dans l'année civile pour la famille\nCf mode de calcul",  "CondCivilFam",),
        ("Cumul", "Famille à partir de deux inscriptions,\ncompte sur année civile: non NOCUMUL, age>6ans, nuits >= 6", "CondCumul", ),
        ("Parrain", "Parrain d'une inscription\nTeste les commandes et facture où un membre de la famille est parrain", "CondParrain", ),
        ("Ministere", "Présence d'un radical PASTEUR ou MISSION dans un nom de liste de diffusion\nTeste l'appartenance à une de ces listes de diffusion, d'un titulaire de la famille", "CondMinistere", ),
        ("NOCUMUL", "Avantage manuel qui exclura l'inscription des autres réductions,\ncalcul fait sur le séjour, pas au niveau familles", None, ),
        ]
        #le prefixe 'Multi' dans le code de la condition lance le traitement 'ArticleMulti'
        #caractères non alpha possibles dans le code article des lignes mais pas dans la fonction condition

# caractères non alpha possibles dans le code mais pas dans la fonction calcul
LISTEmodeCalcul = [
        ("Sans", "Pas de prix, article de type message", None,),
        ("Simple", "Param1 est le prix appliqué, sans autre calcul", "CalSimple",),
        ("4J-8J", "Param2 si plus de 5 jours d'ouvertures, Param 1 autres cas", "Cal4j8j", ),
        ("JOURS", "Prix = Param1 * nombre de jours de l'activité",  "CalJours",),
        ("NUITS", "Prix = Param1 * nombre de nuits de l'activité",  "CalNuits",),
        ("Parrain", "Réduction suite à parrainage d'inscription\nParam1 est le montant en € du parrainage", "CalParrain",),
        ("Reduction", "Déduction du produit : prix unitaire par quantité saisie\nParam1 est le montant en €", "CalReduction",),
        ("RedSejour", "La réduction est faite en % du prix du séjour,\nParam1 est la réduction en %", "CalRedSejour",),
        ("RedCumul", "La réduction en € selon le nombre d'inscriptions\nNiveau famille ou niveau activité mais pas les deux", "CalRedCumul",),
        ("Annuelle", "Force 0 si déja présent dans l'année civile et par individu dans une inscription\pas de param nécessaire", "CalAnnuelle",),
        ]

# code, libelllé, ordre sur la pièce
LISTEtypeLigne = [
        (" ", "Sans",50 ),
        ("Sejour", "Ligne obligatoire pour un séjour, le prix1 est substitué par celui de l'activité s'il est > 0",10 ),
        ("MajoSejour", "Complément regroupé du prix séjour en plus du prix de base", 15),
        ("OptionDetail", "Complément de prix correspondant aux options détaillées, faisant l'objet de lignes distinctes sur la facture", 20),
        ("Reductions", "Remises ou réductions apparaissant à la suite de l'activité", 25),
        ("MessageSejour", "Message sans montant, bas de l'activité ", 30 ),
        ("ComplFamille","Premières lignes du niveau famille",50),
        ("ReducFamille", "Remises ou réductions au niveau famille", 55),
        ("Parrainage", "Au niveau de la famille ", 60),
        ("MessageBas", "Message en bas de facture ", 90),
        ]

# Fonctions paramétrables

def AnneeAcad(DB,IDactivite=None, date= None, **kwargs):
    # Retourne les dates début et fin annee académique sur date debut d'activité
    if IDactivite:
        dictDonnees = {"IDactivite" : IDactivite,}
        annee = RechercheAnneeAcad(DB,dictDonnees)
    elif isinstance(date, datetime.date):
        annee = date.year
        if date.month >=9: annee +=1
    else:
        annee = datetime.date.today().year
        if datetime.date.today().month >=9: annee +=1
    deb = datetime.date(annee-1,9,1)
    fin = datetime.date(annee,8,31)
    return deb, fin
    #fin AnneeAcad

def DateEngEnDateDD(dateEng):
    if dateEng == None : return datetime.date(1900, 1, 1)
    return datetime.date(int(dateEng[:4]), int(dateEng[5:7]), int(dateEng[8:10]))

def DebutOuvertures(DB,IDactivite, IDgroupe = None):
    date = None
    if IDgroupe == None:
        condition = "WHERE ouvertures.IDactivite = %d AND ouvertures.date >= activites.date_debut" % IDactivite
    else: condition = "WHERE ouvertures.IDactivite = %d  AND ouvertures.IDgroupe = %d AND ouvertures.date >= activites.date_debut" % (IDactivite,IDgroupe)
    if IDactivite != None:
        req = """SELECT MIN(ouvertures.date),activites.date_debut
                FROM ouvertures
                INNER JOIN activites ON ouvertures.IDactivite = activites.IDactivite
                %s
                GROUP BY activites.IDactivite
                ; """ % condition
        DB.ExecuterReq(req,MsgBox="DebutOuvertures1")
        recordset = DB.ResultatReq()
        if len(recordset) > 0 :
            date = DateEngEnDateDD(recordset[0][0])
            # contrôle date ouverture sur début activité
            if recordset[0][1] != None:
                debActivite = DateEngEnDateDD(recordset[0][1])
                if date == None : date = debActivite
        else:
            if IDgroupe == None:
                GestionDB.MessageBox(None," Aucune date d'ouverture pendant la période de l'activité '%s' !\n Des dysfonctionnements frapperont les calculs de durée, d'âge et de présence.\n" % IDactivite,titre="Correction nécessaire")
            else:
                req = """SELECT activites.nom, groupes.nom
                        FROM activites
                        INNER JOIN groupes ON activites.IDactivite = groupes.IDactivite
                        WHERE activites.IDactivite = %d AND groupes.IDgroupe = %d
                        GROUP BY activites.nom, groupes.nom
                        ; """ % (IDactivite, IDgroupe)
                DB.ExecuterReq(req,MsgBox="DebutOuvertures2")
                recordset = DB.ResultatReq()
                GestionDB.MessageBox(None," Aucune date d'ouverture dans l'activité '%s' pour le groupe '%s' !\n Des dysfonctionnements frapperont les calculs de durée, d'âge et de présence.\n" % (recordset[0][0],recordset[0][1]),titre="Correction nécessaire")

    if date == None:
        date = datetime.date(2000,1,1)
    return date

def FinOuvertures(DB,IDactivite, IDgroupe = None):
    date = None
    if IDgroupe == None:
        conditionActivite = "WHERE ouvertures.IDactivite = %d" % IDactivite
    else: conditionActivite = "WHERE ouvertures.IDactivite = %d AND ouvertures.IDgroupe = %d" % (IDactivite,IDgroupe)

    if IDactivite != None:
        (dateDeb,dateFin) = DebutFin_Activite(DB,IDactivite)
        condition = """%s AND ouvertures.date >= '%s' AND ouvertures.date < '%s'""" % (conditionActivite,dateDeb,dateFin + datetime.timedelta(days=1))
        req = """SELECT MAX(ouvertures.date)
                FROM ouvertures
                INNER JOIN activites ON ouvertures.IDactivite = activites.IDactivite
                %s ; """ % condition
        DB.ExecuterReq(req,MsgBox="FinOuvertures")
        recordset = DB.ResultatReq()
        if len(recordset) > 0 :
            date = DateEngEnDateDD(recordset[0][0])
    if date == None:
        date = datetime.date(2099,12,31)
    return date

def DebutFin_Activite(DB,IDactivite):
    #recherche des bornes de date de l'activité
    req = """SELECT date_debut, date_fin
            FROM activites
            WHERE IDactivite = '%s' ; """ % IDactivite
    DB.ExecuterReq(req,MsgBox= "GestionArticle.DebutFin_Activite")
    recordset = DB.ResultatReq()
    dateDatDeb, dateDatFin = "1900-01-01","2900-01-01"
    if len(recordset) > 0 :
        (dateDeb, dateFin) = recordset[0]
        if dateDeb == None or dateFin == None :
            GestionDB.MessageBox(None," Il faut saisir des dates début et fin dans l'activité !\n Des dysfonctionnements suivront\n Activité: %s" % IDactivite,titre="Correction nécessaire")
            (dateDeb, dateFin) = (datetime.date(1900,1,1),datetime.date(2900,1,1))
        dateDatDeb = DateEngEnDateDD(dateDeb[:10])
        dateDatFin = DateEngEnDateDD(dateFin[:10])
    return (dateDatDeb,dateDatFin)

def DebutFin_Consos(DB,IDactivite,IDindividu):
    #recherche mini et maxi des consos de date de l'activité
    req = """SELECT MIN(date),MAX(date)
        FROM consommations
        WHERE IDactivite = %d AND IDindividu = %d
        ;""" % (IDactivite, IDindividu)
    DB.ExecuterReq(req,MsgBox= "GestionArticle.DebutFin_Consos")
    recordset = DB.ResultatReq()
    dateDeb, dateFin = datetime.date(1900,1,1),datetime.date(2900,1,1)
    if len(recordset) > 0 :
        (dateDeb, dateFin) = recordset[0]
        if dateDeb == None or dateFin == None :
            (dateDeb, dateFin)= DebutFin_Activite(DB,IDactivite)
    return (dateDeb,dateFin)

def NbreJoursActivite(DB,IDactivite, IDgroupe, IDinscription=None, IDindividu=None):
    # recherche des nbre de jours de participation
    # priorité : Consommations,Inscriptions.Jours,Ouvertures,activites.
    #Pour consommations et ouvertures, récup du premier IDunite au cas où il y en aurait plusieurs (suppose qu'ils aient les memes nbre de jours...)
    # dictDonnee["nbreJours"] est testé avant cette fonction
    nbreJours = 0

    # Première approche par les consos
    if IDinscription != None:
        req = """SELECT Count(date), IDunite, IDactivite, IDgroupe
            FROM consommations 
            WHERE IDinscription = %d
            GROUP BY IDunite, IDactivite, IDgroupe;""" %IDinscription
        DB.ExecuterReq(req,MsgBox="GestionArticle.NbreJoursActivite_1")
        recordset = DB.ResultatReq()
        nbreJours = 0.0
        if recordset != []:
            nbreJours = recordset[0][0]
    elif (IDindividu != None) and (IDactivite != None) :
        req = """
            SELECT Count(date), IDunite, IDgroupe
            FROM consommations 
            WHERE ( IDindividu = %d)
                    AND (IDactivite = %d ) 
            GROUP BY IDunite, IDgroupe
            ;""" %(IDindividu, IDactivite)
        DB.ExecuterReq(req,MsgBox="GestionArticle.NbreJoursActivite_2")
        recordset = DB.ResultatReq()
        nbreJours = 0.0
        if recordset != []:
            nbreJours = recordset[0][0]

    # Deuxième approche par les ouvertures de l'activité
    if nbreJours == 0.0:
        if IDactivite != None :
            if IDgroupe != None:
                condition = "AND IDgroupe = %d " %(IDgroupe)
            else:condition = ""
            req = """
                SELECT Count(ouvertures.date), ouvertures.IDactivite, ouvertures.IDunite, ouvertures.IDgroupe
                FROM ouvertures 
                INNER JOIN activites ON ouvertures.IDactivite = activites.IDactivite
                WHERE (((ouvertures.IDactivite = %d ) 
                        %s ) 
                        AND (ouvertures.date Between activites.date_debut 
                            AND activites.date_fin))
                GROUP BY ouvertures.IDactivite, ouvertures.IDunite, ouvertures.IDgroupe;
                """ % (IDactivite, condition)
            DB.ExecuterReq(req,MsgBox="GestionArticle.NbreJoursActivite_3")
            recordset = DB.ResultatReq()
            if len(recordset)>0:
                if recordset[0][0]!= None:
                    nbreJours = recordset[0][0]
        else:
            if IDinscription == None:
                GestionDB.MessageBox(None,"Problème de logique, IDactivité et IDinscription = None dans GestionArticle.NbreJoursActivite")
    return float(nbreJours)
    #fin NbreJoursActivite

def GroupeActivite(DB,IDactivite):
    # Il s'agit du code compta analytique de l'activité qui à l'origine était dans le groupe d'activité
    req = """SELECT activites.code_comptable, activites.code_transport, activites.nom
        FROM activites
        WHERE IDactivite = %d ;""" % (IDactivite)
    DB.ExecuterReq(req,MsgBox="GestionArticle.GroupeActivite")
    recordset = DB.ResultatReq()
    if len(recordset) == 0:
        code = "00"
    elif len(recordset[0]) == 0:
        code = "00"
    else: code = recordset[0][0]
    return code

def Saison(DB,IDactivite):
    analytique = GroupeActivite(DB,IDactivite)
    if not analytique: analytique = "00"
    if str(analytique)[:2] in ("31","32","33","34","35"):
        saison = "Hiver"
    else: saison = "Ete"
    return saison

def Naissance(DB,IDindividu):
    req = """SELECT date_naiss FROM individus WHERE IDindividu= %s ;""" % (IDindividu)
    DB.ExecuterReq(req,MsgBox="Naissance")
    recordset = DB.ResultatReq()
    if len(recordset) != 1: naissance = None
    else: naissance = recordset[0][0]
    return DateEngEnDateDD(naissance)

def AgeIndividu(DB,IDindividu,IDactivite,IDgroupe=None,mute=True):
    age = 0
    if IDactivite != None and IDactivite>0:
        if not IDgroupe:
            date,fin = DebutFin_Activite(DB,IDactivite)
        else:
            date = DebutOuvertures(DB,IDactivite,IDgroupe)
    else: date = datetime.date.today()
    if IDindividu != None:
        naissance = Naissance(DB,IDindividu)
        if naissance.year == 1900 and not mute:
            GestionDB.MessageBox(None,"Date Naissance inconnue => âge indéterminé pour %s" %DB.GetNomIndividu(IDindividu,first = "prenom"),titre="Remarque")
        if date != None and naissance != None:
            age = (date.year - naissance.year) - int((date.month, date.day) < (naissance.month, naissance.day))
    return age

def DeltaDate(debut,fin):
    # retourne le nombre de jours antre deux dates
    nbj = DateEngEnDateDD(fin) - DateEngEnDateDD(debut)
    return nbj.days

def PersonnePhysique(DB,IDfamille):
    # recherche la civilié du payeur de la famille, pour ne retenir que les 1- 5
    req = """SELECT Max(individus.IDcivilite)
            FROM individus INNER JOIN rattachements ON individus.IDindividu = rattachements.IDindividu
            WHERE (((rattachements.IDfamille)=%d)); """ % IDfamille
    DB.ExecuterReq(req,MsgBox="PersonnePhysique")
    retour = DB.ResultatReq()
    pp = False
    if len(retour) > 0:
        if len(retour[0]) > 0:
            retour0 = retour[0][0]
        else:
            retour0 = retour[0]
        if isinstance(retour0,int):
            if retour0 >0 and retour0 <6:
                pp=True
    return pp
    #fin PersonnePhysique

def GetListePiecesFam(DB,exercice,IDfamille):
    #récup des champs de matPiece et ajout des dates
    dicoDB = DATA_Tables.DB_DATA
    listeChamps = []
    for descr in dicoDB["matPieces"]:
        nomChamp = descr[0]
        listeChamps.append(nomChamp)
    condition = " (pieIDinscription = %d) AND (pieIDfamille = %d) " %(exercice[1].year,IDfamille)
    req = """SELECT matPieces.*
            FROM matPieces
            WHERE %s ;
            """ % condition
    DB.ExecuterReq(req,MsgBox = "GestionArticle.GetListePieces")
    retour = DB.ResultatReq()
    #composition du début de l'info listePieces
    listeDictPieces = GestionInscription.RecordsToListeDict(listeChamps,retour)
    return listeDictPieces

def GetComplementPiece(DB,dictDonnees):
    #recherche montantTotal et nbreJours
    condition = " ligIDnumPiece = %d " % dictDonnees["IDnumPiece"]
    req = """SELECT matArticles.artCodeBlocFacture AS lfaTypeLigne, matPiecesLignes.ligMontant, matPiecesLignes.ligQuantite, matPiecesLignes.ligPrixUnit
            FROM matPiecesLignes INNER JOIN matArticles ON matPiecesLignes.ligCodeArticle = matArticles.artCodeArticle
            WHERE %s ;""" % condition
    DB.ExecuterReq(req,MsgBox = "GestionArticle.GetComplementPiece")
    retour = DB.ResultatReq()
    sejour,montant = (False ,0)
    for typeLigne, montantLigne, qte, pu in retour:
        if typeLigne == "Sejour" : sejour = True
        if montantLigne != 0:
            montant += montantLigne
        else: montant += qte * pu
    #Appel du nombre de jours
    if "nbreJours" in dictDonnees:
        nbreJours = dictDonnees["nbreJours"]
    else :
        nbreJours = NbreJoursActivite(DB,dictDonnees["IDactivite"],dictDonnees["IDgroupe"], IDinscription = dictDonnees["IDinscription"])
    #recherche nom et age
    #champsCompletes =  ["nomIndividu","presenceSejour","montantTotal","nbreJours"]
    dictAjout = {}
    dictAjout["nomIndividu"]= DB.GetNomIndividu(dictDonnees["IDindividu"],first = "prenom")
    dictAjout["presenceSejour"]= sejour
    dictAjout["montantTotal"]= montant
    dictAjout["nbreJours"]= nbreJours
    listeAjout = []
    for champ in list(dictAjout.keys()):
        listeAjout.append((champ,dictAjout[champ]))
    return listeAjout

def PrixJournee(DB,saison,annee):
    texte = "PrixJour%s%s" % (saison[:3],str(annee))
    prixJour = DB.GetParam(param=texte,type="float",user="Any")
    if prixJour == None:
        dlg = CTRL_SaisieSimple.Dialog(None,nomParam="Prix de journée %s %s" % (saison,str(annee)))
        dlg.ShowModal()
        prixJour = dlg.saisie
        dlg.Destroy()
        if prixJour == None:
            prixJour=30
        else:
            if float(prixJour) > 0:
                DB.SetParam(param=texte,value=float(prixJour),type="float",user="Any",unique=False)
    return prixJour

def GetListeDictLignesFact(DB,dictDonnees,modele):
    codeArticle = modele.codeArticle
    #recherche lignes facturees
    condition = " ligIDnumPiece = %d AND ligCodeArticle LIKE '%s%%' " % (dictDonnees["IDnumPiece"],codeArticle)
    listeChamps = ["codeArticle", "montant", "quantite", "prixUnit", "libelle"]
    req = """SELECT ligCodeArticle, ligMontant, ligQuantite, ligPrixUnit, ligLibelle
            FROM matPiecesLignes
            WHERE %s ;""" % condition
    DB.ExecuterReq(req,MsgBox = "GestionArticle.GetListeDictLignesFact")
    retour = DB.ResultatReq()
    listeDictLignes = GestionInscription.RecordsToListeDict(listeChamps,retour)
    return listeDictLignes

#Programmation de chacune des conditions sur articles
def Age(dictDonnees):
    DB = dictDonnees['db']
    age = 0
    if dictDonnees != None:
        IDactivite = dictDonnees["IDactivite"]
        IDgroupe = dictDonnees["IDgroupe"]
        IDindividu = dictDonnees["IDindividu"]
        if IDactivite != None and IDgroupe != None and IDindividu != None:
            age = AgeIndividu(DB,IDindividu,IDactivite,IDgroupe)
    return age

# Enfant condition sur l'âge en début d'activité
def CondAg0_2(dictDonnees,codeArticle) :
    age = Age(dictDonnees)
    if age > 0 and age <3:
        return True
    else: return False

def CondAg3_5(dictDonnees,codeArticle) :
    age = Age(dictDonnees)
    if age >= 3 and age < 6:
        return True
    else: return False

def CondAg6_11(dictDonnees,codeArticle) :
    age = Age(dictDonnees)
    if age >= 6 and age < 12:
        return True
    else: return False

def RechercheAnneeAcad(DB,dictDonnees):
    # selon les cas d'entrée détermine la date fin de l'année académique en cours
    IDactivite = None
    if "IDactivite" in dictDonnees:
        IDactivite = dictDonnees["IDactivite"]
    annee  = None
    # cas d'une pièce famille reprise
    if "IDindividu" in dictDonnees and  dictDonnees["IDindividu"] == 0:
        millesime = dictDonnees["IDinscription"]
        if millesime > 2016 and millesime < 2099:
             annee= millesime
    elif IDactivite > 0:
        deb,fin = DebutFin_Activite(DB,IDactivite)
        annee = fin.year
    # cas d'une pièce activité ou famille en suite
    if "annee" in dictDonnees:
        annee = int(dictDonnees["annee"])
    if not annee:
        annee = datetime.date.today().year
    return annee

# Une seule fois par Annee académique
def CondAnnuelle(dictDonnees,codeArticle) :
    DB = dictDonnees['db']
    annee = RechercheAnneeAcad(DB,dictDonnees)
    IDindividu = dictDonnees["IDindividu"]
    listeIDnumPiece = PiecesAnneeAcademique(DB,annee,None,IDindividu)

    if "IDnumPiece" in dictDonnees:
        ID = dictDonnees["IDnumPiece"]
        if ID in listeIDnumPiece:
            listeIDnumPiece.remove(ID)
    present=ArticlePresent(DB,codeArticle,listeIDnumPiece)
    return not present

# Une seule fois par année civile
def CondCivile(dictDonnees,codeArticle) :
    ret = True
    qte,mtt = None,None
    DB = dictDonnees['db']
    if "IDactivite" in dictDonnees:
        if dictDonnees["IDactivite"] > 0:
            dateDeb = DebutOuvertures(DB,dictDonnees["IDactivite"],None)
            annee =  str(dateDeb.year)
            IDindividu = dictDonnees["IDindividu"]
            listeIDnumPiece = PiecesAnneeCivile(DB, annee, None, IDindividu, )
            if "IDnumPiece" in dictDonnees:
                ID = dictDonnees["IDnumPiece"]
                if ID in listeIDnumPiece:
                    listeIDnumPiece.remove(ID)
            present=ArticlePresent(DB,codeArticle,listeIDnumPiece)
            if present: ret = False
    return ret

# Une seule fois par année académique
def CondAnnuFam(dictDonnees,codeArticle) :
    ret = True
    DB = dictDonnees['db']
    annee = RechercheAnneeAcad(DB,dictDonnees)
    IDfamille = dictDonnees["IDfamille"]
    listeIDnumPiece = PiecesAnneeAcademique(DB,annee,IDfamille,None)
    if "IDnumPiece" in dictDonnees:
        ID = dictDonnees["IDnumPiece"]
        if ID in listeIDnumPiece:
            listeIDnumPiece.remove(ID)
    present=ArticlePresent(DB,codeArticle,listeIDnumPiece)
    if present:
        ret = False
    return ret

# Une seule fois par année civile
def CondCivilFam(dictDonnees,codeArticle) :
    ret = False
    DB = dictDonnees['db']
    annee = RechercheAnneeAcad(DB,dictDonnees)
    IDfamille = dictDonnees["IDfamille"]
    listeIDnumPiece = PiecesAnneeCivile(DB, annee, IDfamille, None)
    if "IDnumPiece" in dictDonnees:
        ID = dictDonnees["IDnumPiece"]
        if ID in listeIDnumPiece:
            listeIDnumPiece.remove(ID)
    present=ArticlePresent(DB,codeArticle,listeIDnumPiece)
    if present: ret = False
    return ret

def CondCumul(dictDonnees,codeArticle):
    # teste la présence des inscriptions à cumul et alimente un dic 'Cumul' dans dictDonnees
    DB = dictDonnees['db']

    # calcul de l'année civile concernée, année du début de l'exercice où débute l'activité ou année du niveau famille
    annee = RechercheAnneeAcad(DB,dictDonnees)
    dictDonnees['annee'] = annee
    condAnnee = """
                    AND (activites.date_debut Like '%d%%')""" % annee

    # recherche le nombre d'inscriptions de la famille y compris celles en cours
    req = """
        SELECT matPieces.pieIDnumPiece,matPieces.pieIDactivite, matPieces.pieIDgroupe, 
                ouvertures.IDunite,individus.date_naiss,matPieces.pieIDindividu,
                matPieces.pieNature,categories_tarifs.campeur,
                Count(ouvertures.Date),Min(ouvertures.Date),Max(ouvertures.Date) 
        FROM   (((matPieces 
                INNER JOIN activites ON matPieces.pieIDactivite = activites.IDactivite) 
                LEFT JOIN ouvertures ON (   matPieces.pieIDgroupe = ouvertures.IDgroupe) 
                                            AND (matPieces.pieIDactivite = ouvertures.IDactivite))
                LEFT JOIN individus ON matPieces.pieIDindividu = individus.IDindividu)
                LEFT JOIN categories_tarifs ON matPieces.pieIDcategorie_tarif = categories_tarifs.IDcategorie_tarif
        WHERE ((matPieces.pieIDfamille=%d)
                %s)
        GROUP BY matPieces.pieIDnumPiece, matPieces.pieIDactivite, matPieces.pieIDgroupe, ouvertures.IDunite, 
                individus.date_naiss, matPieces.pieIDindividu, matPieces.pieNature,categories_tarifs.campeur
        ;"""%(dictDonnees['IDfamille'],condAnnee)
    DB.ExecuterReq(req, MsgBox="CondCumul1")
    retour = DB.ResultatReq()
    # appel des inscriptions et comptage des types 'séjour' hors enfants <6 ans au début du séjour
    ddInscr = {}
    lstIDpieces = []
    lstIDactivite = []
    if len(retour) > 0:
        # analyse des inscriptions ouvrant droit au cumul
        for IDpiece, IDactivite, IDgroupe, IDunite, naiss, IDindividu, nature,\
            campeur, nbOuv, minOuv, maxOuv in retour:
            if campeur != 1:
                continue # a priorité sur le paramétrage trfCumul qui élude les tarifs campeur qui n'entrent pas dans les cumuls
            if (IDactivite, IDindividu) in lstIDactivite:
                # cas de plusieurs factures pour une même activité
                continue
            lstIDactivite.append((IDactivite, IDindividu))
            if not IDpiece in list(ddInscr.keys()):
                ddInscr[IDpiece] = {'nbOuv': 0,'nbConsos': 0,'age':None, 'noCumul':False,'nature':nature,
                                    'IDactivite':IDactivite, 'IDunite':None, 'IDindividu':IDindividu}
                if naiss and IDactivite:
                    age = AgeIndividu(DB,IDindividu,IDactivite,mute=True)
                else:
                    # l'age inconnu est supposé supérieur à 6 ans
                    age = 99
                ddInscr[IDpiece]['age'] = age
            # plage d'activité avec moins d'un manquant par semaine pour éviter les activités parsemées
            plage = DeltaDate(minOuv, maxOuv)
            if (nbOuv > ddInscr[IDpiece]['nbOuv']) and (plage < nbOuv * 7 / 6):
                ddInscr[IDpiece]['nbOuv'] = nbOuv
                ddInscr[IDpiece]['nbConsos'] = nbOuv
                ddInscr[IDpiece]['IDunite'] = IDunite
                lstIDpieces.append(IDpiece)

    # si non devis, il faut vérifier les nombres de consommations au lieu des ouvertures
    for IDpiece in lstIDpieces:
        if ddInscr[IDpiece]['nature'] != 'DEV':
            req = """
                SELECT Count(consommations.date)
                FROM consommations
                WHERE (consommations.IDactivite = %d)
                        AND (consommations.IDindividu = %d)
                        AND (consommations.IDunite = %d)
                ;"""%(ddInscr[IDpiece]['IDactivite'],ddInscr[IDpiece]['IDindividu'],ddInscr[IDpiece]['IDunite'])
            DB.ExecuterReq(req, MsgBox="CondCumul1")
            recordset = DB.ResultatReq()
            ddInscr[IDpiece]['nbConsos'] = recordset[0][0]
        else: ddInscr[IDpiece]['nbConsos'] = 0

    # Exclure les pièces ayant déjà eu des réduction non cumulables
    req = """
        SELECT matPieces.pieIDnumPiece
        FROM((matPieces 
            INNER JOIN matPiecesLignes ON matPieces.pieIDnumPiece = matPiecesLignes.ligIDnumPiece) 
            INNER JOIN matArticles ON matPiecesLignes.ligCodeArticle = matArticles.artCodeArticle)
            LEFT JOIN matTarifs ON (matPieces.pieIDcategorie_tarif = matTarifs.trfIDcategorie_tarif) 
                                    AND (matPieces.pieIDgroupe = matTarifs.trfIDgroupe) 
                                    AND (matPieces.pieIDactivite = matTarifs.trfIDactivite)
        WHERE   (matPieces.pieIDnumPiece IN (%s))
                AND ((matArticles.artConditions = "NOCUMUL")
                        OR matTarifs.trfCumul = 1)
        GROUP BY matPieces.pieIDnumPiece
        ;""" % (str(lstIDpieces)[1:-1])
    DB.ExecuterReq(req, MsgBox="CondCumul2")
    retour = DB.ResultatReq()
    for (IDpiece,) in retour:
        ddInscr[IDpiece]['noCumul']=True

    dicCumul = {'nbReduc':0,'mtReduc':0}

    # uniquement les séjours soit un minimum de 6 nuits soit au moins 7 jours d'activité
    lstIDsejours = [x for x in list(ddInscr.keys()) if ddInscr[x]['nbConsos'] > 6]
    dicCumul['nbSejours'] = len(lstIDsejours)
    dicCumul['nbEligibles'] = len([x for x in lstIDsejours if ddInscr[x]['age'] >= 6 and ddInscr[x]['noCumul']==False])

    # recherche des réductions cumul déja facturées pour le même article
    condPieEnCours = ""
    if "pieceEnCours" in list(dictDonnees.keys()) and dictDonnees["pieceEnCours"] > 0:
        condPieEnCours = "AND (NOT matPieces.pieIDnumPiece = %d)"%dictDonnees['pieceEnCours']
    req = """SELECT Sum(matPiecesLignes.ligQuantite),Sum(matPiecesLignes.ligMontant)
            FROM ( matPieces 
                    LEFT JOIN activites ON matPieces.pieIDactivite = activites.IDactivite) 
                    LEFT JOIN matPiecesLignes ON matPieces.pieIDnumPiece = matPiecesLignes.ligIDnumPiece
            WHERE   (matPieces.pieIDfamille = %d) 
                    AND (matPiecesLignes.ligCodeArticle = '%s') 
                    AND ((activites.date_debut Like '%d%%')             
                        OR (matPieces.pieIDinscription = %d)
                        )
                    AND matPieces.pieNature = 'FAC'
                    %s
            ;""" % (dictDonnees['IDfamille'], codeArticle, annee, annee, condPieEnCours)
    DB.ExecuterReq(req, MsgBox="CondCumul3")
    retour = DB.ResultatReq()
    if len(retour) > 0:
        for nbReduc, mtReduc in retour:
            dicCumul['nbReduc'] += Nz(nbReduc)
            dicCumul['mtReduc'] -= Nz(mtReduc)
    # Présence de lignes réduc déjà calculées
    dicCumul['dontPresNonFacture'] = int(0)
    for ligne in dictDonnees['lignes_piece']:
        if ligne['codeArticle'] == codeArticle :
            dicCumul['dontPresNonFacture'] += int(ligne['quantite'])
    dictDonnees['dicCumul'] = dicCumul
    if (dicCumul['nbEligibles'] - dicCumul['nbReduc'] ) < 1:
        return False
    return True

def CondMinistere(dictDonnees,codeArticle) :
    # teste la presence dans la liste de diffusion PASTEUR d'un titulaire de la famille
    # dict Donnee ne contient que IDcompte_payeur et IDfamille s'il vient de niveau famille, sinon c'est complet
    ret = False
    DB = dictDonnees['db']
    if "IDfamille" in dictDonnees:
        IDfamille = dictDonnees["IDfamille"]
        req = """SELECT COUNT(listes_diffusion.nom)
                FROM rattachements
                LEFT JOIN (abonnements
                LEFT JOIN listes_diffusion ON abonnements.IDliste = listes_diffusion.IDliste)
                        ON rattachements.IDindividu = abonnements.IDindividu
                WHERE (((UPPER(listes_diffusion.nom) LIKE '%%PASTEUR%%') 
                            OR (UPPER(listes_diffusion.nom) LIKE '%%MISSION%%'))
                        AND (rattachements.IDfamille = '%d') 
                        AND (rattachements.titulaire = '1'))
                ;""" % IDfamille
        DB.ExecuterReq(req,MsgBox = "GestionArticle.CondMinistere")
        retour = DB.ResultatReq()
        if retour[0][0]>0:
            ret = True
    # ajout d'une condition sur la nature du tarif utilisé
    if ret:
        # on appliquera la réduc ministère sur les seuls camps entrant dans les cumuls
        tplcond = (dictDonnees['IDactivite'],
                   dictDonnees['IDgroupe'],
                   dictDonnees['IDcategorie_tarif'])
        req = """
            SELECT matTarifs.trfCumul
            FROM matTarifs
            WHERE ((matTarifs.trfIDactivite = %d) 
                    AND (matTarifs.trfIDgroupe = %d) 
                    AND (matTarifs.trfIDcategorie_tarif = %d))
            ;""" % tplcond
        DB.ExecuterReq(req,MsgBox = "GestionArticle.CondMinistere_2")
        retour = DB.ResultatReq()
        if retour[0][0] and retour[0][0] > 0:
            ret = False
    return ret

def CondParrain(dictDonnees,codeArticle) :
    # teste la presence d'une inscription pointant un membre de la famille comme parrain sans avoir abandonné son droit
    ret = False
    DB = dictDonnees['db']
    if "IDfamille" in dictDonnees:
        IDfamille = dictDonnees["IDfamille"]
        req = """SELECT Count(matPieces.pieIDnumPiece)
                FROM    (matPieces 
                            INNER JOIN individus ON matPieces.pieIDindividu = individus.IDindividu) 
                        INNER JOIN activites ON matPieces.pieIDactivite = activites.IDactivite
                WHERE (((matPieces.pieParrainAbandon)=0) AND ((matPieces.pieIDparrain)=%d));
              """ % (IDfamille)
        DB.ExecuterReq(req,MsgBox = "GestionArticle.CondParrain")
        retour = DB.ResultatReq()
        for nbre in retour[0]:
            if nbre > 0 : ret = True
    return ret
    #fin CondParrain

def ArticlePresent(DB,codeArticle,listeIDnumPiece):
    # teste la présence de l'article dans la liste de pièces
    if len(listeIDnumPiece)==0: return False
    ret = False
    liste = ""
    for IDnumPiece in listeIDnumPiece:
        liste = liste + str(IDnumPiece) + ", "
    liste = liste[:-2]
    condition = "WHERE ligIDnumPiece in (%s) AND ligCodeArticle = '%s'" % (liste,codeArticle)
    req = """SELECT COUNT(ligIDnumLigne)
            FROM matPiecesLignes
            %s ;""" % condition
    DB.ExecuterReq(req,MsgBox = "GestionArticle.ArticlePresent")
    retour = DB.ResultatReq()
    if retour[0][0]>0:
        ret = True
    return ret

def PiecesAnneeCivile(DB, annee, IDfamille, IDindividu):
    # retourne la liste des pièces de l'année pour l'individu ou la famille
    datDeb = str(annee)+"-01-01"
    datFin = str(annee)+"-12-31"
    if IDindividu == None:
        # cas de recherche niveau famille l'IDindividu est 0 et l'année dans l'inscription
        req = """SELECT matPieces.pieIDnumPiece
                FROM matPieces
                WHERE pieIDinscription = '%s' AND pieIDfamille =  %d
                ;""" % (str(annee),IDfamille)
    else:
        # cas de recherche niveau activite
        req = """SELECT matPieces.pieIDnumPiece
                FROM matPieces INNER JOIN activites ON matPieces.pieIDactivite = activites.IDactivite
                WHERE activites.date_debut >= '%s' AND activites.date_debut <= '%s' AND pieIDindividu =  %d
                ;""" % (datDeb,datFin,IDindividu)
    ret = DB.ExecuterReq(req,MsgBox = "GestionArticle.PiecesAnneeCivile")
    recordset = DB.ResultatReq()
    listeIDnumPieces = []
    for record in recordset:
        listeIDnumPieces.append(record[0])
    return listeIDnumPieces

def PiecesAnneeAcademique(DB,annee,IDfamille,IDindividu):
    listeIDnumPieces = []
    try:
        # retourne la liste des pièces de l'année pour l'individu ou la famille
        if IDindividu == None or IDindividu == 0:
            # cas de recherche niveau famille l'IDindividu est 0, l'année dans l'IDinscription

            req = """SELECT matPieces.pieIDnumPiece
                    FROM matPieces
                    WHERE matPieces.pieIDinscription = %d AND pieIDfamille =  %d
                    ;""" % (int(annee),IDfamille)
        else:
            # cas de recherche niveau activite
            datDeb = "%d-%s"%(int(annee)-1,"09-01")
            datFin = "%d-%s"%(int(annee),"08-31")
            req = """SELECT matPieces.pieIDnumPiece
                    FROM matPieces INNER JOIN activites ON matPieces.pieIDactivite = activites.IDactivite
                    WHERE activites.date_debut >= '%s' AND activites.date_debut <= '%s' AND pieIDindividu =  %d
                    ;""" % (datDeb,datFin,IDindividu)
        ret = DB.ExecuterReq(req,MsgBox = "GestionArticle.PiecesAnneeCivile")
        recordset = DB.ResultatReq()
        for record in recordset:
            listeIDnumPieces.append(record[0])
    except: pass
    return listeIDnumPieces

def MultiParrain(codeArticle,dictDonnees,listeOLV):
    #la condition parrain a déjà été appliquée (présence de parrainages affectés ou pas)
    DB = dictDonnees['db']
    modele = None
    # Appel de l'article original pour test de modif de son libellé.
    req = """SELECT artCodeArticle, artLibelle
            FROM matArticles
            WHERE artCodeArticle LIKE '%s%%'
            GROUP BY artCodeArticle, artLibelle;
          """ % (codeArticle[:-2])
    DB.ExecuterReq(req,MsgBox = "GestionArticle.MultiParrain.matArticle")
    retArticle = DB.ResultatReq()
    # Vérifie qu'il n'y a qu'un seul article parrainage paramétré
    if len(retArticle) != 1:
        texte = "La recherche article %s ne retourne pas un seul article \n\nRetour : %s" %(codeArticle[:-2],str(retArticle))
        GestionDB.Messages().Box(("Incohérence à diagnostiquer "),texte)
        return
    (codeArticleModele, libelle) = retArticle[0]
    lgCodeArticle = len(codeArticleModele)

    i = 0
    #Récupère dans olv le modèle Parrain
    for ligne in listeOLV:
        if ligne.codeArticle[:lgCodeArticle] == codeArticleModele:
            i +=1
            if modele == None:
                modele = copy.deepcopy(ligne)
    modele.codeArticle = codeArticleModele

    # le modèle dans olv doit être supprimée car à personnaliser et dupliquer ensuite
    while i > 0 :
        # Problème si on essaie de faire un seul passage détection et suppression
        for ligne in listeOLV:
            if ligne.codeArticle[:lgCodeArticle] == codeArticleModele:
                listeOLV.remove(ligne)
                i-=1

    # constitution des lignes de parrainage
    # teste la presence de pièces pointant la famille comme parrain sans avoir abandonné son droit et non imputé
    IDpiece = 0
    if "pieceEnCours" in dictDonnees:
        IDpiece = dictDonnees["pieceEnCours"]
    if "IDfamille" in dictDonnees:
        IDfamille = dictDonnees["IDfamille"]
        req =   """
                SELECT matPieces.pieIDnumPiece, matPieces.pieIDinscription, matPieces.pieIDindividu, individus.nom, 
                        individus.prenom, activites.nom, matPieces.pieIDprestation,matPiecesLignes.ligIDnumLigne
                FROM (((matPieces 
                        INNER JOIN individus ON matPieces.pieIDindividu = individus.IDindividu) 
                        INNER JOIN activites ON matPieces.pieIDactivite = activites.IDactivite) 
                        LEFT JOIN matParrainages ON matPieces.pieIDinscription = matParrainages.parIDinscription) 
                        LEFT JOIN matPiecesLignes ON matParrainages.parIDligneParr = matPiecesLignes.ligIDnumLigne
                WHERE 	(matPieces.pieParrainAbandon = 0) 
                        AND (matPieces.pieIDparrain = %d)
                        AND (matParrainages.parIDligneParr Is Null)
                ; """ % (IDfamille)

        DB.ExecuterReq(req,MsgBox = "GestionArticle.MultiParrain")
        retPieces = DB.ResultatReq()
        listeParrainages = []
        dictDonnees['dicParrainages'] = {}
        alert = None
        txtIDuser = "8"+("0000"+ str(DB.IDutilisateurActuel()))[-4:]
        # déroulement des pièces parrainées afin de vérifier leur règlement
        for IDnumPieceFilleul, parIDinscription, IDfilleul, nomFilleul, prenomFilleul, nomActiviteFilleul, \
            IDprestationFilleul,IDligneParrain in retPieces:
            if not IDprestationFilleul:
                wx.MessageBox("Le filleul potentiel '%s' n'a pas d'inscription valide"%(prenomFilleul + " "+nomFilleul))
                alert = "SIMPLE DEVIS! "
            if parIDinscription == None: parIDinscription = 0
            if parIDinscription in list(dictDonnees['dicParrainages'].keys()):
                dicParr = dictDonnees['dicParrainages'][parIDinscription]
            else:
                dicParr = {}
                dicParr['parIDinscription'] = parIDinscription
                dicParr['IDligneParrain'] = IDligneParrain
                dicParr['parAbandon']= False
                dicParr['parSolde'] = txtIDuser
                dicParr["ligneChoix"]= ''
                dicParr["parLibelle"]= ''
            # recherche si le parrainé est encaissé sur IDprestationFilleul
            mttSolde = 0
            if alert == None:
                req = """SELECT prestations.montant, Sum(ventilation.montant)
                        FROM prestations
                        LEFT JOIN ventilation ON prestations.IDprestation = ventilation.IDprestation
                        WHERE prestations.IDprestation = %d
                        GROUP BY prestations.montant;
                      """ % (IDprestationFilleul)
                DB.ExecuterReq(req,MsgBox = "GestionArticle.CalParrain.ventilations")
                retVentil = DB.ResultatReq()
                if len(retVentil) > 0:
                    ventil =  retVentil[0][1]
                    if ventil == None :
                        mttSolde = 0
                    else:
                        mttSolde = int(100.0 * float(ventil) / float(retVentil[0][0]))
            prefixe = "Parrainage "
            if alert:
                pass
            elif mttSolde <= 90 :
                alert = "NON REGLE! "
            else :
                alert = "    ok     "
            libelle =  prenomFilleul + ' '+ nomFilleul+ ' / ' + nomActiviteFilleul
            # une seule pièce parrainée pour la même inscription
            if (dicParr["ligneChoix"] == ''):
                dicParr["ligneChoix"]= alert + libelle
                dicParr["parLibelle"]= prefixe + libelle
                dicParr['parSolde'] = txtIDuser
            dictDonnees['dicParrainages'][parIDinscription] = dicParr
        choixPossible = False
        i=0
        for parIDinscription, dicParr in list(dictDonnees['dicParrainages'].items()):
            listeParrainages.append((i+1, dicParr['ligneChoix']))
            choixPossible = True
            dicParr["ixLigneChoix"] = i+1
            i +=1

        # affichage et choix des lignes à imputer, suppression dans 'dicParrainages' des parrainages non retenus
        if choixPossible :
            if dictDonnees['origine'] == 'verif':
                # lors de la vérif on prend tous les parrainages possibles
                choix = listeParrainages
                interroChoix = wx.ID_OK
            else:
                intro = "Pour n'imputer aucun parrainage Annulez"
                dlg = CTRL_ChoixListe.DialogCoches(None,LargeurCode= 40,LargeurLib= 300,minSize = (500,300),
                                                    listeOriginale=listeParrainages,
                                                    checked=True,
                                                    titre = 'Choisissez les réductions parrainage à imputer !',
                                                    intro = intro)
                interroChoix = dlg.ShowModal()
                choix = dlg.choix
                dlg.Destroy()
            if interroChoix == wx.ID_OK :
                for item in listeParrainages :
                    # seuls les parrainages retenus sont stockés, enregistrement lors de la validation de la pièce
                    # stockage repris lors de l'enregistrement de la pièce  pour modifier parIDligneParr quand connu
                    if not item in choix:
                        for key, dicParr in list(dictDonnees['dicParrainages'].items()):
                            if dicParr['ixLigneChoix'] == item[0]:
                                del dictDonnees['dicParrainages'][key]
            else :
                choixPossible = False
        # ici on calcule le montant de la réduction pour chaque ligne
        if choixPossible :
            i = 0
            for dicParr in list(dictDonnees['dicParrainages'].values()):
                nbj = NbreJoursActivite(DB,None,None,IDinscription=dicParr['parIDinscription'])
                qte = 0
                if nbj > 6 : qte = 1
                modele.quantite = qte
                modele.montantCalcul = Nz(qte) * Nz(modele.prixUnit)
                modele.montant = Nz(qte) * Nz(modele.prixUnit)
                modele.modeCalcul = 'Sans'
                modele.saisie = True
                ligne = copy.deepcopy(modele)
                ligne.codeArticle += str(i + 1)
                dicParr['codeArticle']= ligne.codeArticle
                if qte == 0:
                    dicParr['parLibelle'] += " < 6 jours"
                ligne.libelle = dicParr['parLibelle']
                i += 1
                listeOLV.append(copy.deepcopy(ligne))
    return
    #fin MultiParrain

class ActionsConditions() :
        def __init__(self, dictDonnees={}):
            #pour le niveau famille dictDonnees doit contenir : IDfamille, IDactivite à minima
            self.dictDonnees= dictDonnees

        # Lancement de la fonction définie au dessus, retour du résultat
        def Condition(self,condition, codeArticle=None):
            result = True
            fonction= "KO"
            if condition:
                for item in LISTEconditions:
                    if item[0] == condition: fonction= item[2]
            else:
                fonction = None
            if fonction == "KO":
                GestionDB.MessageBox(None, "La condition '%s' de l'article '%s' n'est plus gérée!" %(condition,codeArticle) ,titre = "Article: condition obsolète !")
            elif fonction == False:
                result = False
            elif fonction == None:
                pass
            else:
                if fonction not in globals():
                    GestionDB.MessageBox(None, "La fonction '%s' est dans LISTEconditions mais non programmée dans GestionArticle.ActionsConditions!" % fonction ,titre = "Erreur Programmation !")
                else:
                    result = eval(fonction + '(self.dictDonnees,codeArticle)')
            return result #fin ActionsConditions

        # la condition Multi permet de générer plusieurs lignes de réduction pour un seul article dupliqué
        def ConditionMulti(self,condition,codeArticle, listeOLV):
            # la condition MultiFam était utilisée auparavant pour générer plusieurs lignes de réduc par enfant
            if condition=="Parrain": MultiParrain(codeArticle ,self.dictDonnees,listeOLV)
            return

#Programmation de chacun des modes de calcul des articles, retourne les éléments de prix calculés
def CalSimple(track, tracks, dictDonnees) :
    qte = 1.0
    mtt = qte * track.prixUnit
    return qte,mtt

def Cal4j8j(track, tracks, dictDonnees) :
    IDinscription = None
    if "IDinscription" in dictDonnees:
        IDinscription = dictDonnees["IDinscription"]
    DB = dictDonnees['db']
    if "nbreJours" in dictDonnees:
        qte = dictDonnees["nbreJours"]
    else :
        qte = NbreJoursActivite(DB,dictDonnees["IDactivite"],dictDonnees["IDgroupe"],IDinscription)
    if qte > 5 :
        qte = 1.0
        mtt = qte * track.prix2
    else:
        qte = 1.0
        mtt = qte * track.prixUnit
    return qte,mtt

def CalJours(track, tracks, dictDonnees) :
    # calcule le prix selon le nombre de jours de l'activité
    IDinscription = None
    if "IDinscription" in dictDonnees:
        IDinscription = dictDonnees["IDinscription"]
    DB = dictDonnees['db']
    if "nbreJours" in dictDonnees:
        qte = dictDonnees["nbreJours"]
    else :
        qte = NbreJoursActivite(DB,dictDonnees["IDactivite"],dictDonnees["IDgroupe"],IDinscription)
    mtt = float(qte) * float(track.prixUnit)
    return qte,mtt

def CalNuits(track, tracks, dictDonnees) :
    # calcule le prix selon le nombre de jours de l'activitétrack = {Track} <DLG_PrixActivite.Track object at 0x0D60FED0>
    IDinscription = None
    if "IDinscription" in dictDonnees:
        IDinscription = dictDonnees["IDinscription"]
    DB = dictDonnees['db']
    qte = 1.0
    if "nbreJours" in dictDonnees:
        qte = dictDonnees["nbreJours"]
    else :
        if "IDactivite" in dictDonnees and "IDgroupe" in dictDonnees:
            qte = NbreJoursActivite(DB,dictDonnees["IDactivite"],dictDonnees["IDgroupe"],IDinscription)
    if qte == None : qte = 1.0
    if qte > 1 : qte -= 1
    if track.prixUnit == None : track.prixUnit = 1.0
    mtt = qte * track.prixUnit
    return qte,mtt

def CalReduction(track, tracks, dictDonnees) :
    if track.saisie :
        qte = track.quantite
    else:
        qte = 0
    mtt = qte * track.prixUnit
    return qte,mtt

def CalRedSejour(track, tracks, dictDonnees):
    # réduction en pourcentage des lignes de type 'sejour'
    calcul = 0.0
    for altTrack in tracks:
        mtt = 0.0
        if altTrack.isChecked and altTrack.codeArticle != track.codeArticle and altTrack.typeLigne == 'Sejour':
            if altTrack.saisie: mtt = altTrack.montant
            else: mtt = altTrack.montantCalcul
            calcul -= (mtt * track.prix1 / 100)
    return 1,calcul

def CalRedCumul(track, tracks, dictDonnees) :

    if not 'dicCumul' in list(dictDonnees.keys()):
        CondCumul(dictDonnees,track.codeArticle)
    # réduction selon le nombre de camps >=6 nuits et enfants >=6 ans
    qteElig = dictDonnees['dicCumul']['nbEligibles']
    qte = qteElig
    # mot clé '{nbInscr}' dans le libellé (nbre de réduc / nbre éligibles)
    ante = dictDonnees['dicCumul']['nbReduc']
    txt = "%d"%int(max(qteElig,ante))
    if ante != 0:
        qte = qteElig - ante
        txt = "%d des "%int(qte) + txt
    montant = 0.0
    if qteElig > 0:
        for i in range(int(qteElig)):
            ix = min(i,len(LISTEredCumul)-1)
            montant -= LISTEredCumul[ix]
    montant += dictDonnees['dicCumul']['mtReduc']
    montant = round(montant,2)

    # intègre le nombre d'inscriptions dans le lbellé de réduction
    track.libelle = track.libelleArticle.replace('{nbInscr}',txt)
    return qte,montant
    #fin CalRedEnfEte

def CalAnnuelle(track, tracks, dictDonnees) :
    qte,mtt = None,None
    DB = dictDonnees['db']
    if "IDactivite" in dictDonnees:
        dateDeb = DebutOuvertures(DB,dictDonnees["IDactivite"],None)
        annee =  str(dateDeb.year)
        codeArticle = track.codeArticle
        IDindividu = dictDonnees["IDindividu"]
        listeIDnumPiece = PiecesAnneeCivile(DB, annee, None, IDindividu, )
        if "IDnumPiece" in dictDonnees:
            ID = dictDonnees["IDnumPiece"]
            if ID in listeIDnumPiece:
                listeIDnumPiece.remove(ID)
        present=ArticlePresent(DB,codeArticle,listeIDnumPiece)
        if present:
            track.libelle = "Justificatif à fournir année " + annee + " : " + track.libelle
            track.quantite = 0
            qte,mtt = 0,0
    return qte,mtt

def CalAbParrain(track, tracks, dictDonnees) :
    DB = dictDonnees['db']
    IDinscription = None
    nbreJours = 0
    if "IDinscription" in dictDonnees: IDinscription = dictDonnees["IDinscription"]
    if dictDonnees["IDactivite"] == None : dictDonnees["IDactivite"] = 0
    if dictDonnees["IDactivite"] >0:
        if "nbreJours" in dictDonnees:
            nbreJours = dictDonnees["nbreJours"]
        else :
            nbreJours = NbreJoursActivite(DB,dictDonnees["IDactivite"],dictDonnees["IDgroupe"],IDinscription)
    qte = 0
    if nbreJours > 6 : qte = 1
    else:
        qte = 0
    track.libelle = "Parrainage abandonné par le parrain"
    track.quantite = qte
    montant = track.prixUnit * qte
    return qte,montant

def CalParrain(track, *args) :
    # Les calculs ont été fait lors de la génération de la ligne; cf multiParrain
    qte,mtt = track.quantite,track.montantCalcul
    return qte,mtt
    #fin CalParrain

def ArticlePreExist(article, ligne, dictDonnees):
    # test pour l'article candidat à l'insertion, pour chaque ligne présente.
    brk = False # provoquera un break dans 'for ligne in listeOLV'
    artPres = False
    supprimer = False

    if article.codeArticle[:6] != ligne.codeArticle[:6]:
        # ne traite que si ça matche
        return artPres, supprimer, brk

    article.origine = "article_ligne"
    ligne.origine = "ligne_article"
    # C'est l'article qui sera retenu, il faut donc l'alimenter de parties de la ligne
    article.force = "OUI"
    article.saisie = True
    article.oldValue = ligne.oldValue
    article.oldLibelle = ligne.oldLibelle
    ligne.libelleArticle = article.libelle
    if ligne.montant == article.montantCalcul or ligne.montant == 0.0:
            artPres = True
            ligne.force = "OUI"
    else:
        # mais montant différent, le nouveau calcul sera présent
        ligne.force = "NON"
        ligne.origine += "_faux"
        if AvecCalcul(ligne):
            ligne.quantite = article.quantite

    ligne.montantCalcul = article.montantCalcul

    # CAS PARRAINAGE: les articles ont pu être renumérotés
    if article.codeArticle[:6] == '$$PARR' and ligne.codeArticle[:6] == '$$PARR':
        # recherche dans le dicParr
        dicParrainage = dictDonnees['dicParrainages']
        for IDinscr, dicParr in list(dicParrainage.items()):
            brk = True
            if ligne.IDnumLigne and article.IDinscription:
                if ligne.IDnumLigne == dicParr[
                    'IDligneParrain'] and article.IDinscription == IDinscr:
                    article.oldValue = ligne.montant
                    article.IDnumLigne = ligne.IDnumLigne
                    article.IDnumPiece = ligne.IDnumPiece
                    if not 'ok' in dicParr["ligneChoix"]:
                        article.force = "NON"
                    brk = False

    # CAS réduction cumul
    elif (ligne.codeArticle == "$RED-CUMUL") and '{' in article.libelle:
            ligne.libelle = article.libelle

    return artPres, supprimer, brk

class ActionsModeCalcul() :
        def __init__(self, dictDonnees={}):
            self.dictDonnees= dictDonnees

        # Lancement de la fonction définie ci-dessus, retour du résultat
        def ModeCalcul(self,track,tracks):
            if not tracks: track = [] # used in text for 'eval'
            qte,mtt= None,None
            modeCalcul = track.modeCalcul
            fonction = "KO"
            if modeCalcul == "AbParrain":
                qte,mtt = eval("CalAbParrain" + '(track,tracks,self.dictDonnees)')
                return qte,mtt
            if modeCalcul != None:
                for item in LISTEmodeCalcul:
                    if item[0] == modeCalcul: 
                        fonction= item[2]
            else:
                fonction = None
            if fonction == "KO":
                GestionDB.MessageBox(None, "Le mode de calcul '%s' de l'article '%s' n'est plus géré!" % (modeCalcul,track.codeArticle) ,titre = "Article: calcul obsolète !")
            else:
                if fonction:
                    if fonction not in globals():
                        GestionDB.MessageBox(None, "La fonction '%s' est dans la liste des modes de calcul mais pas programmée dans GestionArticle.ActionsModeCalcul!" % fonction ,titre = "Erreur Programmation !")
                    else:
                        qte,mtt = eval(fonction + '(track,tracks,self.dictDonnees)')

            return qte,mtt
            #fin ModeCalcul

#--------------------------------------------

if __name__ == "__main__":
    DB = GestionDB.DB()
    print(DebutFin_Activite(DB,740))
    NbreJoursActivite(DB,393,985, IDindividu= 1386)
    print(AnneeAcad(DB,None,None))

