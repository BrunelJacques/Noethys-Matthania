#!/usr/bin/env python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------
# Application :    Noethys, Matthania
# Auteur:           Ivan LUCAS, JB
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------

import Chemins
from Utils.UTILS_Traduction import _
import sqlite3
import datetime
import wx
import os
import base64
from Data import DATA_Tables
from Ctrl import CTRL_ChoixListe
from Ctrl import CTRL_SaisieSimple
from Gest import GestionArticle
from Utils import UTILS_Fichiers
from Utils import UTILS_Dates as ut

MODE_TEAMWORKS = False
DICT_CONNEXIONS = {}
IX_CONNEXION = {"ix":0,"pointeurs":{}}

# Import MySQLdb
try :
    import MySQLdb
    from MySQLdb.constants import FIELD_TYPE
    from MySQLdb.converters import conversions
    IMPORT_MYSQLDB_OK = True
    INTERFACE_MYSQL = "mysqldb"
except Exception as err :
    IMPORT_MYSQLDB_OK = False

# import mysql.connector
try :
    import mysql.connector
    from mysql.connector.constants import FieldType
    from mysql.connector import conversion
    IMPORT_MYSQLCONNECTOR_OK = True
    if IMPORT_MYSQLDB_OK == False:
        INTERFACE_MYSQL = "mysql.connector"
except Exception as err :
    IMPORT_MYSQLCONNECTOR_OK = False

def SetInterfaceMySQL(nom="mysqldb", pool_mysql=5):
    """ Permet de sélectionner une interface MySQL """
    global INTERFACE_MYSQL, POOL_MYSQL
    if nom == "mysqldb" and IMPORT_MYSQLDB_OK == True :
        INTERFACE_MYSQL = "mysqldb"
    elif nom == "mysql.connector" and IMPORT_MYSQLCONNECTOR_OK == True :
        INTERFACE_MYSQL = "mysql.connector"
    elif IMPORT_MYSQLDB_OK == True:
        INTERFACE_MYSQL = "mysqldb"
    elif IMPORT_MYSQLCONNECTOR_OK == True :
        INTERFACE_MYSQL = "mysql.connector"
    else:
        mess = "Ni 'mysqldb' ni 'mysql.connector' ne sont opérationnels!!\n\n"
        mess += "refaire pip install xxxx"
        ret = wx.MessageBox(mess,"CONNEXION RESEAU IMPOSSIBLE",style= wx.ICON_ERROR)
        INTERFACE_MYSQL = None

    POOL_MYSQL = pool_mysql

# Vérifie si les certificats SSL sont présents dans le répertoire utilisateur
def GetCertificatsSSL():
    dict_certificats = {}
    liste_fichiers = [("ca", "ca-cert.pem"), ("key", "client-key.pem"), ("cert", "client-cert.pem"),]
    for nom, fichier in liste_fichiers :
        chemin_fichier = UTILS_Fichiers.GetRepUtilisateur(fichier)
        if os.path.isfile(chemin_fichier):
            dict_certificats[nom] = chemin_fichier
    return dict_certificats

CERTIFICATS_SSL = GetCertificatsSSL()

class DB():
    def __init__(self, suffixe="DATA", nomFichier="", modeCreation=False, IDconnexion=None, **kwd):
        self.echec = 2
        self.IDconnexion = IDconnexion # pour forcer un ID?
        self.isNetwork = False
        self.lstTables = None
        self.lstIndex = None
        self.grpConfigs = None
        self.cfgParams = None
        self.erreur = "__init__"

        # éviter la redondance suffixe quand reprise du nom précédent
        lstMotsFichier = nomFichier.split('_')
        suff = lstMotsFichier[-1]
        if len(lstMotsFichier) > 0  and suff in ("DATA", "DOCUMENT", "PHOTO"):
            suffixe = suff
            nomFichier = '_'.join(lstMotsFichier[:-1])

        """ Utiliser GestionDB.DB(nomFichier=Chemins.GetStaticPath("Databases/Geographie.dat"), suffixe=None) pour ouvrir un autre type de fichier """
        self.nomFichier = nomFichier
        self.modeCreation = modeCreation
        self.lstIndex=[]
        self.typeDB = ''

        # Si aucun nom de fichier n'est spécifié, on recherche celui par défaut dans le Config.dat
        if self.nomFichier == "":
            self.nomFichier = self.GetNomFichierDefaut()

        self.echec = 1
        self.erreur = "NomFichier DB: %s"%self.nomFichier
        if self.nomFichier != "":
            # Mémorisation de l'ouverture de la connexion et des requêtes
            if IDconnexion == None :
                IX_CONNEXION["ix"] += 1
                id = IX_CONNEXION["ix"]
                self.IDconnexion = id
                IX_CONNEXION["pointeurs"][id] = self
            else :
                self.IDconnexion = IDconnexion

            #if self.IDconnexion == 27: # 'debug connexions ouvertes' etape ON
            #    print("debug open")
            DICT_CONNEXIONS[self.IDconnexion] = []

            # On ajoute le préfixe de type de fichier et l'extension du fichier
            if MODE_TEAMWORKS == True and suffixe not in ("", None):
                if suffixe[0] != "T":
                    suffixe = _("T%s") % suffixe

            if suffixe != None :
                self.nomFichier += "_%s" % suffixe

            # Est-ce une connexion réseau ?
            if "[RESEAU]" in self.nomFichier :
                self.isNetwork = True
            else:
                self.isNetwork = False
                if suffixe != None :
                    self.nomFichier = UTILS_Fichiers.GetRepData(u"%s.dat" % self.nomFichier)

            # Ouverture de la base de données
            if self.isNetwork == True :
                self.OuvertureFichierReseau(self.nomFichier, suffixe)
            else:
                self.OuvertureFichierLocal(self.nomFichier)

    def GetNomPosteReseau(self):
        if self.isNetwork == False :
            return None
        return self.GetParamConnexionReseau()["user"]
        
    def OuvertureFichierLocal(self, nomFichier):
        """ Version LOCALE avec SQLITE """
        # Vérifie que le fichier sqlite existe bien
        self.typeDB = 'sqlite'
        if self.modeCreation == False :
            if os.path.isfile(nomFichier)  == False :
                #print "Le fichier SQLITE demandé n'est pas present sur le disque dur."
                self.echec = 1
                return
        # Initialisation de la connexion
        try :
            self.connexion = sqlite3.connect(nomFichier.encode('utf-8'))
            self.cursor = self.connexion.cursor()
            self.isNetwork = False
            self.echec = 0
        except Exception as err:
            print("La connexion avec la base de donnees SQLITE a echouee : \nErreur detectee :%s" % err)
            self.erreur = err
            self.echec = 1

    def GetParamConnexionReseau(self):
        """ Récupération des paramètres de connexion si fichier MySQL """
        pos = self.nomFichier.index("[RESEAU]")
        paramConnexion = self.nomFichier[:pos]
        port, host, user, passwd = paramConnexion.split(";")
        nomFichier = self.nomFichier[pos:].replace("[RESEAU]", "")
        nomFichier = nomFichier.lower()
        dictDonnees = {"port":int(port), "hote":host, "host":host, "user":user, "utilisateur":user, "mdp":passwd, "password":passwd, "fichier":nomFichier}
        return dictDonnees

    def OuvertureFichierReseau(self, nomFichier, suffixe):
        """ Version RESEAU avec MYSQL """
        self.echec = 0
        self.typeDB = 'mysql'
        try :
            self.connexion, nomFichier = GetConnexionReseau(nomFichier)
            self.cursor = self.connexion.cursor()
        except Exception as err:
            print("La connexion a MYSQL a echouee. Erreur :")
            print((err,))
            self.erreur = err
            self.echec = 1
            return

        # Création
        if self.modeCreation == True :
            try:
                self.cursor.execute("CREATE DATABASE IF NOT EXISTS %s CHARSET utf8 COLLATE utf8_unicode_ci;" % nomFichier)
            except Exception as err:
                print("La creation de la base MYSQL a echouee. Erreur :")
                print((err,))
                self.erreur = err
                self.echec = 1
                return

        # Utilisation
        if nomFichier not in ("", None, "_data") :
            try:
                self.cursor.execute("USE %s;" % nomFichier)
            except Exception as err:
                print("L'ouverture de la base MYSQL a echouee. Erreur :")
                print((err,))
                self.erreur = err
                self.echec = 1
                self.Close()

    def GetNomFichierDefaut(self):
        nomFichier = ""
        try :
            topWindow = wx.GetApp().GetTopWindow()
            nomWindow = topWindow.GetName()
        except :
            nomWindow = None
            topWindow = None
        if nomWindow == "general" : 
            # Si la frame 'General' est chargée, on y récupère le dict de config
            nomFichier = topWindow.userConfig["nomFichier"]
        else:
            # Récupération du nom de la DB directement dans le fichier de config sur le disque dur
            from Utils import UTILS_Config
            cfg = UTILS_Config.FichierConfig()
            nomFichier = cfg.GetItemConfig("nomFichier")
        return nomFichier

    def GetListeDatabasesMySQL(self):
        # Récupère la liste des databases présentes
        listeDatabases = []
        self.cursor.execute("SHOW DATABASES;")
        listeValeurs = self.cursor.fetchall()
        for valeurs in listeValeurs:
            listeDatabases.append(valeurs[0])
        return listeDatabases

    def GetVersionServeur(self):
        req = """SHOW VARIABLES LIKE "version";"""
        self.ExecuterReq(req,MsgBox="GestionDB.DB.GetVersionServeur")
        listeTemp = self.ResultatReq()
        if len(listeTemp) > 0:
            return listeTemp[0][1]
        return None

    def ComposeListeChamps(self,listeDonnees, separateur):
        champs = ""
        valeurs = []
        for donnee in listeDonnees:
            if self.isNetwork == True :
                # Version MySQL
                champs = champs + donnee[0] + "=%s" + separateur
            else:
                # Version Sqlite
                champs = champs + donnee[0] + "=?" + separateur
            valeurs.append(donnee[1])
        champs = champs[:-2]
        # pour la  composition de clés, le séparateur peut être ' AND '
        if len(separateur) == 5 : champs = champs[:-3]
        return champs,valeurs

    def AfficheErr(self,parent,retour):
        dlgErr = wx.MessageDialog(parent, _(retour), _("Retour SQL !"), wx.OK | wx.ICON_EXCLAMATION)
        dlgErr.ShowModal()
        dlgErr.Destroy()
        return

    def Commit(self):
        if self.connexion:
            self.connexion.commit()

    def ErrCursor(self,req,err):

        if not hasattr(self.cursor, "connection"):
            self.retourReq = ("Requete sqlite incorrecte :\n%s\npas de connection:\n%s") % (
            req, err)
        elif not hasattr(self.cursor.connection,"open"):
            self.retourReq= ("Requete sqlite incorrecte :\n%s\nErreur detectee:\n%s") % (req, err)
        elif self.cursor.connection.open == 0:
            ID = self.IDconnexion
            self.retourReq = "ID '%d': DB.Close() en trop!!!\n\nSur ExecuterReq: %s\nDB Connexion closed!!!"%(ID,req)
            wx.MessageBox(self.retourReq,"Problème de programmation")
        else:
            self.retourReq= ("Requete sql incorrecte :\n%s\nErreur detectee:\n%s") % (req, err)
        return self.retourReq

    def Close(self,all=False):
        if self.echec == 2:
            # l'ID connection n'était pas créé
            del self
            return
        #if self.IDconnexion == 30:# 'debug connexions ouvertes' etape off
        #    print("debug Close")
        try :
            if self.isNetwork and self.connexion.open != 0:
                self.connexion.close()
                del DICT_CONNEXIONS[self.IDconnexion]
                del IX_CONNEXION["pointeurs"][self.IDconnexion]
            elif not self.isNetwork:
                del DICT_CONNEXIONS[self.IDconnexion]
                del IX_CONNEXION["pointeurs"][self.IDconnexion]
        except Exception as err:
            print("GestionDB.Close ID %s: "%str(self.IDconnexion),type(err),err)
        if all:
            AfficheConnexionsOuvertes("-")
            try:
                lstID = [x for x in DICT_CONNEXIONS.keys()]
                for id in lstID:
                    IX_CONNEXION["pointeurs"][id].Close()
            except Exception as err:
                print("GestionDB.CloseALL ID %s: "%str(self.IDconnexion),err)
                pass
        del self

    def InsertPhoto(self, IDindividu=None, blobPhoto=None):
        if self.isNetwork == True :
            # Version MySQL
            if INTERFACE_MYSQL == "mysqldb" :
                blob = MySQLdb.escape_string(blobPhoto)
                sql = "INSERT INTO photos (IDindividu, photo) VALUES (%d, '%s')" % (IDindividu, blob)
                self.cursor.execute(sql)
            if INTERFACE_MYSQL == "mysql.connector" :
                self.cursor.execute("INSERT INTO photos (IDindividu, photo) VALUES (%s, %s)", (IDindividu, blobPhoto))
            self.connexion.commit()
            self.cursor.execute("SELECT LAST_INSERT_ID();")
        else:
            # Version Sqlite
            sql = "INSERT INTO photos (IDindividu, photo) VALUES (?, ?)"
            self.cursor.execute(sql, [IDindividu, sqlite3.Binary(blobPhoto)])
            self.connexion.commit()
            self.cursor.execute("SELECT last_insert_rowid() FROM Photos")
        newID = self.cursor.fetchall()[0][0]
        return newID

    def MAJPhoto(self, IDphoto=None, IDindividu=None, blobPhoto=None):
        if self.isNetwork == True :
            # Version MySQL
            if INTERFACE_MYSQL == "mysqldb" :
                blob = MySQLdb.escape_string(blobPhoto)
                sql = "UPDATE photos SET IDindividu=%d, photo='%s' WHERE IDphoto=%d" % (IDindividu, blob, IDphoto)
                self.cursor.execute(sql)
            if INTERFACE_MYSQL == "mysql.connector" :
                self.cursor.execute("UPDATE photos SET IDindividu=%s, photo=%s WHERE IDphoto=%s", (IDindividu, blobPhoto, IDphoto))
            self.connexion.commit()
        else:
            # Version Sqlite
            sql = "UPDATE photos SET IDindividu=?, photo=? WHERE IDphoto=%d" % IDphoto
            self.cursor.execute(sql, [IDindividu, sqlite3.Binary(blobPhoto)])
            self.connexion.commit()
        return IDphoto

    def MAJimage(self, table=None, key=None, IDkey=None, blobImage=None, nomChampBlob="image"):
        #Enregistre un blob 'image de fichier' dans une table
        if self.isNetwork == True :
            req = "UPDATE %s SET %s=XXBLOBXX WHERE %s=%s" % (table, nomChampBlob, key, IDkey)
            req = req.replace("XXBLOBXX", "%s")
            self.cursor.execute(req, (blobImage,))
            self.connexion.commit()
        else:
            # Version Sqlite
            sql = "UPDATE %s SET %s=? WHERE %s=%d" % (table, nomChampBlob, key, IDkey)
            self.cursor.execute(sql, [sqlite3.Binary(blobImage),])
            self.connexion.commit()

    def ReqInsert(self, nomTable="", listeDonnees=[], commit=True, retourID=True, MsgBox=None):
        """ Permet d'insérer des données dans une table """
        #retourID none et True : retourne l'ID, gére self.newID, False : retourne 'ok'
        # Préparation des données
        if retourID == None:   modeRetour = 1
        elif retourID == True: modeRetour = 2
        else :                 modeRetour = 3
        champs = "("
        interr = "("
        valeurs = []
        for donnee in listeDonnees:
            champs = champs + donnee[0] + ", "
            if self.isNetwork == True :
                # Version MySQL
                interr = interr + "%s, "
            else:
                # Version Sqlite
                interr = interr + "?, "
            valeurs.append(donnee[1])
        champs = champs[:-2] + ")"
        interr = interr[:-2] + ")"
        req = "INSERT INTO %s %s VALUES %s" % (nomTable, champs, interr )
        retourReq = "ok"
        self.newID= 0
        try:
            # Enregistrement
            self.cursor.execute(req, tuple(valeurs))
            if commit == True:
                self.Commit()

            # Récupération de l'ID
            if self.isNetwork == True:
                # Version MySQL
                self.cursor.execute("SELECT LAST_INSERT_ID();")
            else:
                # Version Sqlite
                self.cursor.execute("SELECT last_insert_rowid() FROM %s" % nomTable)
            self.newID = self.cursor.fetchall()[0][0]
            
        except Exception as err:
            mess = self.ErrCursor(req, err)
            if MsgBox != None and mess:
                msg = Messages()
                msg.Box(titre = "Erreur GestionDB",message="%s\n\n%s"%(MsgBox,self.retourReq))
                return
        self.retour = retourReq
        if modeRetour in [3]:
            retour = retourReq
        else :
            retour = self.newID

        # Retourne le message
        return retour

    def ReqMAJ(self, nomTable, listeDonnees, nomChampID, ID, IDestChaine=False, MsgBox = None):
        """ Permet d'insérer des données dans une table """
        # Préparation des données
        champs, valeurs = self.ComposeListeChamps(listeDonnees,", ")
        self.retourReq = "liste données mal définie\nRequete non lancée"
        if len(champs)>0:
            if IDestChaine == False and (type(ID)== int or type(ID)== int):
                req = "UPDATE %s SET %s WHERE %s=%d ;" % (nomTable, champs, nomChampID, ID)
            else:
                req = "UPDATE %s SET %s WHERE %s='%s' ;" % (nomTable, champs, nomChampID, ID)
            self.retourReq = "ok"
            # Enregistrement
            try:
                serieVal = tuple(valeurs)
                self.cursor.execute(req, serieVal)
                self.Commit()
            except Exception as err:
                mess = self.ErrCursor(req, err)
                if MsgBox != None and mess:
                    msg = Messages()
                    msg.Box(titre = "Erreur GestionDB",message="%s\n\n%s"%(MsgBox,self.retourReq))
                    return
        return self.retourReq

    def ReqMAJcles(self, nomTable, listeDonnees, listeCles, MsgBox = None):
        """ Permet d'insérer des données dans une table avec clés multiples """
        champs, valeurs = self.ComposeListeChamps(listeDonnees,", ")
        if isinstance(listeCles, (list, tuple)) :
            nomsCles, valeursCles =self.ComposeListeChamps(listeCles," and ")
            req = "UPDATE %s SET %s WHERE %s " % (nomTable, champs, nomsCles)
            for cle in valeursCles :
                valeurs.append(cle)
        else :
            self.retourReq = "Liste clé n'est pas une liste"
            return self.retourReq
        self.retourReq = "ko (non exécuté\n%s)"%req
        # Enregistrement
        try:
            self.cursor.execute(req, tuple(valeurs))
            self.Commit()
            self.retourReq= "ok"

        except Exception as err:
            mess = self.ErrCursor(req,err)
            if MsgBox != None and mess:
                msg = Messages()
                msg.Box(titre = "Erreur GestionDB",message="%s\n\n%s"%(MsgBox,self.retourReq))
                return
        return self.retourReq

    def ReqDEL(self, nomTable="", nomChampID="", ID=None, commit=True, MsgBox = False):
        """ Suppression d'un enregistrement """
        self.retourReq = "ok"
        if ID != None:
            if type(ID) == int :
               req = "DELETE FROM %s WHERE %s = %d;" % (nomTable, nomChampID, ID)
            elif type(ID) == int :
               req = "DELETE FROM %s WHERE %s = %d;" % (nomTable, nomChampID, ID)
            else :
                if ID[:1] != "'" :
                    ID = "'"+ID+"'"
                req = "DELETE FROM %s WHERE %s = %s;" % (nomTable, nomChampID, ID)
            try:
                ret = self.cursor.execute(req)
                if commit == True :
                    self.Commit()
            except Exception as err:
                mess = self.ErrCursor(req,err)
                if isinstance(MsgBox,str):
                    msg = Messages()
                    msg.Box(titre = "Err GestionDB: %s"%MsgBox,message=self.retourReq)
                    return
            return self.retourReq

    def ReqDELcles(self, nomTable, listeCles, MsgBox = None):
        """ Permet d'insérer des données dans une table avec clés multiples """
        if isinstance(listeCles, (list, tuple)) and len(listeCles) >0:
            condition = ""
            for nomCle, valeurCle in listeCles:
                if isinstance(valeurCle,(int,float)):
                    condition += "%s = %d AND "%(nomCle,valeurCle)
                else:
                    condition += "%s = '%s' AND "%(nomCle,valeurCle)
            condition = condition[:-4]
            req = "DELETE FROM %s WHERE %s ;" % (nomTable, condition)
        else :
            return "La liste des clés n'est pas une liste contenant des clés"
        self.retourReq = "ok"
        # Enregistrement
        try:
            self.cursor.execute(req)
            self.Commit()
        except Exception as err:
            self.ErrCursor(req,err)
            if MsgBox != None:
                msg = Messages()
                msg.Box(titre = "Err GestionDB: " + MsgBox,message=self.retourReq)
                return
        return self.retourReq

    def ReqSelect(self, nomTable, conditions, MsgBox = None, lstChamps=[]):
        """ Permet d'appeler des données d'une seule table selon conditions """
        if len(lstChamps) == 0:
            select = "*"
        else: select = ",".join(lstChamps)
        req = "SELECT %s  FROM %s WHERE %s " % (select, nomTable, conditions)
        self.retourReq = "ok"
        # Enregistrement
        try:
            self.cursor.execute(req)
            self.Commit()
        except Exception as err:
            self.retourReq= ("Requete ReqSelect incorrecte :\n%s\nErreur detectee:\n%s") % (req, err)
            mess = self.ErrCursor(req, err)
            if MsgBox != None and mess:
                msg = Messages()
                msg.Box(titre = "Erreur GestionDB",message="%s\n\n%s"%(MsgBox,self.retourReq))
                return
        return self.retourReq

    def ExecuterReq(self, req, commit=True, MsgBox = None):
        if self.echec >= 1:
            if not MsgBox: origine = "GestionDB.ExecuterReq"
            else: origine = MsgBox
            if self.erreur != "ErreurPubliee":
                mess = "Echec d'accès à la base de donnée\n\n%s"%origine
                wx.MessageBox(mess,"Ouverture DB",style = wx.ICON_ERROR)
            self.erreur = "ErreurPubliee"
            return False # lié au lancement sans connexion précédente
        if self.isNetwork == True :
            req = req.replace("()", "(10000000, 10000001)")
        self.retourReq = "ok"
        try:
            self.cursor.execute(req)
            DICT_CONNEXIONS[self.IDconnexion].append(MsgBox)
            if commit: self.Commit()
        except Exception as err:
            self.retourReq = self.ErrCursor(req,err)
            if MsgBox:
                if not isinstance(MsgBox, str):
                    MsgBox = str(MsgBox)
                msg = Messages()
                msg.Box(titre = "Erreur GestionDB",message="%s\n\n%s"%(MsgBox,self.retourReq))
                return

        # Retourne le message
        return self.retourReq

    def Executermany(self, req="", listeDonnees=[], commit=True):
        """ Executemany pour local ou réseau """
        """ Exemple de req : "INSERT INTO table (IDtable, nom) VALUES (?, ?)" """
        """ Exemple de listeDonnees : [(1, 2), (3, 4), (5, 6)] """
        # Adaptation réseau/local
        if self.isNetwork == True:
            # Version MySQL
            req = req.replace("?", "%s")
        else:
            # Version Sqlite
            req = req.replace("%s", "?")
        # Executemany
        self.cursor.executemany(req, listeDonnees)
        if commit == True:
            self.connexion.commit()

    def ResultatReq(self):
        if self.echec >= 1 : return []
        resultat = self.cursor.fetchall()
        try :
            # Pour contrer MySQL qui fournit des tuples alors que SQLITE fournit des listes
            if self.isNetwork == True and type(resultat) == tuple :
                resultat = list(resultat)
        except :
            pass
        return resultat

    def Modifier(self, table, ID, champs, valeurs, dicoDB, commit=True):
        # champs et valeurs sont des tuples

        # Recherche du nom de champ ID de la table
        nomID = dicoDB[table][0][0]

        # Creation du détail champs/valeurs à modifier
        detail = ""

        # Vérifie s'il y a plusieurs champs à modifier
        if isinstance(champs, tuple):
            x = 0
            while x < len(champs):
                detail = detail + champs[x] + "='" + valeurs[x] + "', "
                x += 1
            detail = detail[:-2]
        else:
            detail = champs + "='" + valeurs + "'"

        req = "UPDATE %s SET %s WHERE %s=%d" % (table, detail, nomID, ID)
        self.cursor.execute(req)
        if commit == True:
            self.connexion.commit()

    def Dupliquer(self, nomTable="", nomChampCle="", conditions="", dictModifications={}, renvoieCorrespondances=False,
                  IDmanuel=False):
        """ Dulpliquer un enregistrement d'une table :
             Ex : nomTable="modeles", nomChampCle="IDmodele", ID=22,
             conditions = "IDmodele=12 AND IDtruc>34",
             dictModifications={"nom" : _("Copie de modele"), etc...}
             renvoieCorrespondance = renvoie un dict de type {ancienID : newID, etc...}
             IDmanuel = Attribue le IDprécédent de la table + 1 (pour parer au bug de la table tarifs_ligne
        """
        listeNewID = []
        # Recherche des noms de champs
        listeChamps = []
        for nom, type, info in DATA_Tables.DB_DATA[nomTable]:
            listeChamps.append(nom)

        # Importation des données
        texteConditions = ""
        if len(conditions) > 0:
            texteConditions = "WHERE %s" % conditions
        req = "SELECT * FROM %s %s;" % (nomTable, texteConditions)
        self.ExecuterReq(req,MsgBox="GestionDB.DB.Dupliquer")
        listeDonnees = self.ResultatReq()
        if len(listeDonnees) == 0:
            return None

        # Copie des données
        dictCorrespondances = {}
        for enregistrement in listeDonnees:
            listeTemp = []
            index = 0
            ID = None
            for nomChamp in listeChamps:
                valeur = enregistrement[index]
                if nomChamp in dictModifications:
                    valeur = dictModifications[nomChamp]
                if nomChamp != nomChampCle:
                    listeTemp.append((nomChamp, valeur))
                else:
                    ID = valeur  # C'est la clé originale

                    # Si saisie manuelle du nouvel ID
                    if IDmanuel == True:
                        req = """SELECT max(%s) FROM %s;""" % (nomChampCle, nomTable)
                        self.ExecuterReq(req,MsgBox="GestionDB.DB.Dupliquer")
                        temp = self.ResultatReq()
                        if temp[0][0] == None:
                            newIDmanuel = 1
                        else:
                            newIDmanuel = temp[0][0] + 1
                        listeTemp.append((nomChampCle, newIDmanuel))

                index += 1
            newID = self.ReqInsert(nomTable, listeTemp)
            if IDmanuel == True:
                newID = newIDmanuel
            listeNewID.append(newID)
            dictCorrespondances[ID] = newID

        # Renvoie les correspondances
        if renvoieCorrespondances == True:
            return dictCorrespondances

        # Renvoie les newID
        if len(listeNewID) == 1:
            return listeNewID[0]
        else:
            return listeNewID

    def GetProchainID(self, nomTable=""):
        if self.isNetwork == False :
            # Version Sqlite
            req = "SELECT seq FROM sqlite_sequence WHERE name='%s';" % nomTable
            self.ExecuterReq(req,MsgBox="GestionDB.DB.GetProchainID")
            donnees = self.ResultatReq()

            # Renvoie le prochain ID
            if len(donnees) > 0 :
                return donnees[0][0] + 1

        else:
            # Version MySQL
            self.ExecuterReq("SHOW TABLE STATUS WHERE name='%s';" % nomTable)
            donnees = self.ResultatReq()
            if len(donnees) > 0 :
                return donnees[0][10]

        return 1

    def IsTableExists(self, nomTable=""):
        """ Vérifie si une table donnée existe dans la base """
        tableExists = False
        if not self.lstTables :
            # ne charge qu'une fois la liste des tables
            self.lstTables = self.GetListeTables()
        if nomTable.lower() in self.lstTables :
            tableExists = True
        return tableExists

    def IsIndexExists(self, nomIndex=""):
        """ Vérifie si un index existe dans la base """
        indexExists = False
        if self.lstIndex == []:
            self.lstIndex = self.GetListeIndex()
        if nomIndex in self.lstIndex :
            indexExists = True
        return indexExists

    def GetListeChamps2(self, nomTable=""):
        """ Affiche la liste des champs de la table donnée """
        listeChamps = []
        if not self.IsTableExists(nomTable):
            mess = "La table '%s' n'est pas présente"%nomTable
            wx.MessageBox(mess,"Anomalie détectée")
            return

        if self.isNetwork == False :
            # Version Sqlite
            req = "PRAGMA table_info('%s');" % nomTable
            self.ExecuterReq(req,MsgBox="GestionDB.DB.GetListeChamps2")
            listeTmpChamps = self.ResultatReq()
            for valeurs in listeTmpChamps :
                listeChamps.append( (valeurs[1], valeurs[2]) )
        else:
            # Version MySQL
            req = "SHOW COLUMNS FROM %s;" % nomTable
            self.ExecuterReq(req,MsgBox="GestionDB.DB.GetListeChamps2")
            listeTmpChamps = self.ResultatReq()
            for valeurs in listeTmpChamps :
                listeChamps.append( (valeurs[0], valeurs[1]) )
        return listeChamps

    def GetDataBases(self):
        self.cursor.execute("SHOW DATABASES;")
        listeBases = self.cursor.fetchall()
        return listeBases

    def CreationTable(self, nomTable="", dicoDB={}):
        # appellée pour gérer tables sqlite principalement, != CreationUneTable
        req = "CREATE TABLE %s (" % nomTable
        pk = ""
        for descr in dicoDB[nomTable]:
            nomChamp = descr[0]
            typeChamp = descr[1]
            # Adaptation à Sqlite
            if self.isNetwork == False and typeChamp == "LONGBLOB" : typeChamp = "BLOB"
            if self.isNetwork == False and typeChamp == "BIGINT": typeChamp = "INTEGER"
            # Adaptation à MySQL :
            if self.isNetwork == True and typeChamp == "INTEGER PRIMARY KEY AUTOINCREMENT" : typeChamp = "INTEGER PRIMARY KEY AUTO_INCREMENT"
            if self.isNetwork == True and typeChamp == "FLOAT" : typeChamp = "REAL"
            if self.isNetwork == True and typeChamp == "DATE" : typeChamp = "VARCHAR(10)"
            if self.isNetwork == True and typeChamp.startswith("VARCHAR") :
                nbreCaract = int(typeChamp[typeChamp.find("(")+1:typeChamp.find(")")])
                if nbreCaract > 255 :
                    typeChamp = "TEXT(%d)" % nbreCaract
                if nbreCaract > 20000 :
                    typeChamp = "MEDIUMTEXT"

            # ------------------------------
            req = req + "%s %s, " % (nomChamp, typeChamp)
        req = req[:-2] + ")"
        self.cursor.execute(req)

    def GetParam(self, param = None, type= "string",user= None):
        if user == None:
            user = self.UtilisateurActuel()
        if user == None : user = "NoName"
        self.type = "prm" + type[0].upper() + type[1:]
        if user == None : user = "NoName"
        req = "SELECT " + self.type + " FROM matParams WHERE prmUser = '" + user + "' and prmParam = '" + param +"';"
        retour = self.ExecuterReq(req,MsgBox="GestionDB.DB.GetParam")
        if retour != "ok" :
            msg = Messages()
            msg.Box(titre = "GetParam",message = retour)
        recordset = self.ResultatReq()
        value = None
        if len(recordset)>0 :
            if len(recordset[0])>0 :
                value = recordset[0][0]
        return value

    def SetParam(self, param= None, value= None, type= "string", user= None, unique=False):
        # tentative d'insertion puis MAJ avec Clé unique en couple données [0] puis clé primair double [:2]
        if user == None:
            user = self.UtilisateurActuel()
        if user == None : user = "NoName"
        self.type = "prm" + type[0].upper() + type[1:]
        table = "matParams"
        if unique:
            #suppression avant insertion
            req = """DELETE FROM %s WHERE prmUser = '%s' AND prmParam = '%s' ;""" % (table, user, param)
            try:
                self.cursor.execute(req)
                self.Commit()
            except Exception as err:
                pass
        listeDonnees = []
        listeDonnees.append(("prmUser",user))
        listeDonnees.append(("prmParam", param))
        listeDonnees.append((self.type, value))
        retour = self.ReqInsert(table, listeDonnees,retourID = False)
        if retour != "ok" :
            retour = self.ReqMAJ(table, listeDonnees[1:], nomChampID=listeDonnees[0][0],ID=listeDonnees[0][1])
            if retour != "ok" :
                retour = self.ReqMAJcles(table, listeDonnees[2:], listeDonnees[:2])
        return retour

    def SetAnnee(self, annee = None):
        if annee == None:
            import datetime
            annee = datetime.date.today().year
        retour= self.SetParam(param = "periodeAnnee",value=annee, type="string")
        return retour

    def GetAnnee(self):
        annee = str(self.GetParam("periodeAnnee","string"))
        if annee == 'None':
            import datetime
            annee = str(datetime.date.today().year)
        debut= str(annee + "-01-01")
        fin = str(annee + "-12-31")
        return annee, debut, fin

    def UtilisateurActuel(self):
        utilisateur = "NoName"
        try :
            topWindow = wx.GetApp().GetTopWindow()
            nomWindow = topWindow.GetName()
        except :
            nomWindow = None
        if nomWindow == "general" :
            # Si la frame 'General' est chargée, on y récupère le dict de config
            dictUtilisateur = topWindow.dictUtilisateur
            utilisateur = dictUtilisateur["prenom"] + " " + dictUtilisateur["nom"]
        return utilisateur

    def IDutilisateurActuel(self):
        IDutilisateur = 0
        try :
            topWindow = wx.GetApp().GetTopWindow()
            nomWindow = topWindow.GetName()
        except :
            nomWindow = None
        if nomWindow == "general" :
            # Si la frame 'General' est chargée, on y récupère le dict de config
            dictUtilisateur = topWindow.dictUtilisateur
            IDutilisateur = dictUtilisateur["IDutilisateur"]
        return IDutilisateur

    def GetNomIndividu(self,ID, first="prenom" ):
        if ID == None :
            value = " "
        else:
            if first == "prenom":
                select = "prenom, nom "
            else: select = "nom, prenom "
            if isinstance(ID,(int,float)):
                where = "individus.IDindividu = %d" % ID
            else:
                where = "individus.IDindividu = %s" % str(ID)
            req = """SELECT %s
                    FROM individus
                    WHERE %s;"""%(select, where)

            retour = self.ExecuterReq(req,MsgBox="GestionDB.GetNomIndividu")
            if retour == "ok":
                recordset = self.ResultatReq()
            value = " "
            if len(recordset)>0 :
                if len(recordset[0])>0 :
                    value = recordset[0][0] + " " + recordset[0][1]
        return value

    def GetNomFamille(self,ID, first="prenom" ):
        if ID == None :
            return "-"
        if type(ID) != str:
            ID = str(ID)
        if first == "prenom":
            selectReq = "SELECT individus.prenom, individus.nom "
        else: selectReq = "SELECT individus.nom, individus.prenom "

        whereReq = """WHERE (IDfamille = %s )""" % ID
        fromReq = "FROM familles INNER JOIN individus ON familles.adresse_individu = individus.IDindividu "

        sqlReq = selectReq + fromReq + whereReq
        
        def execReq(req):
            self.ExecuterReq(req, MsgBox="GestionDB.DB.GetNomFamille")
            recordset = self.ResultatReq()
            value = None
            if len(recordset) > 0:
                if len(recordset[0]) > 0:
                    value = "%s %s"%(recordset[0][0],recordset[0][1])
            return value
        value = execReq(sqlReq)
 
        if not value: # cas d'absence de correspondant on prend le premier individu entré
            fromReq = "FROM individus INNER JOIN rattachements ON individus.IDindividu = rattachements.IDindividu "
            sqlReq = selectReq + fromReq + whereReq + " ORDER BY individus.IDindividu;"
            value = execReq(sqlReq)
        return value

    def GetNomActivite(self,ID):
        if ID == None :
            value = " "
        else:
            req = """SELECT nom
                    FROM activites
                    WHERE (IDactivite = %s );""" % ID
            retour = self.ExecuterReq(req,MsgBox="GestionDB.DB.GetNomActivite")
            if retour != "ok" :
                wx.MessageBox(str(retour))
            recordset = self.ResultatReq()
            value = " "
            if len(recordset)>0 :
                if len(recordset[0])>0 :
                    value = recordset[0][0]
        return value

    def GetNomGroupe(self,ID):
        if ID == None :
            value = " "
        else:
            req = """SELECT nom
                    FROM groupes
                    WHERE (IDgroupe = %s );""" % ID
            retour = self.ExecuterReq(req,MsgBox="GestionDB.DB.GetNomGroupe")
            if retour != "ok" :
                wx.MessageBox(str(retour))
            recordset = self.ResultatReq()
            value = " "
            if len(recordset)>0 :
                if len(recordset[0])>0 :
                    value = recordset[0][0]
        return value

    def GetNomCategorieTarif(self,ID):
        if ID == None : Nom = "no name"
        req = """SELECT nom
                FROM categories_tarifs
                WHERE (IDcategorie_tarif = %s );""" % ID
        retour = self.ExecuterReq(req,MsgBox="GestionDB.DB.GetNomCatTarif")
        if retour != "ok" :
            wx.MessageBox(str(retour))
        recordset = self.ResultatReq()
        value = None
        if len(recordset)>0 :
            if len(recordset[0])>0 :
                value = recordset[0][0]
        return value

    def GetLastActivite(self,IDfamille):
        # recherche de la dernière activite inscrite pour cette famille
        if IDfamille == None : return None
        IDactivite = None
        # recherche de la dernière date de création de pièce niveau activité
        req = """SELECT Max(pieDateCreation)
                FROM matPieces
                WHERE (((pieIDfamille)=%d) AND ((pieIDactivite)<>0));
                """ % IDfamille
        self.ExecuterReq(req,MsgBox = True)
        recordset = self.ResultatReq()
        if len(recordset)>0 :
            if len(recordset[0])>0 :
                DateCreation = recordset[0][0]
                # récupération d'un activité à cette date
                req = """SELECT Max(pieIDactivite)
                        FROM matPieces
                        WHERE (((pieDateCreation)= '%s' ) AND ((pieIDactivite)<>0));
                        """ % DateCreation
                self.ExecuterReq(req,MsgBox = True)
                recordset = self.ResultatReq()
                if len(recordset)>0 :
                    if len(recordset[0])>0 :
                        IDactivite = recordset[0][0]
        return IDactivite

    def GetClotures(self):
        # recherche des dates de cloturee des exercices ouverts et N-1
        lstClotures = []
        firstDeb = '2999-01-01'
        req = """SELECT date_debut, date_fin
                FROM compta_exercices
                """
        retour = self.ExecuterReq(req,MsgBox="GestionDB.DB.GetClotures")
        if retour != "ok" :
            wx.MessageBox(str(retour))
        else:
            recordset = self.ResultatReq()
            for dd, df in recordset:
                if dd < firstDeb: firstDeb = dd
                lstClotures.append(df)
        firstdd = ut.DateEngEnDateDD(firstDeb)
        cl0 = firstdd + datetime.timedelta(days=-1)
        lst = [ut.DateDDEnDateEng(cl0),]
        lst.extend(lstClotures)
        return lst

    def GetExercice(self,dateInput = None,labelDate = "testée",alertes = True,approche = False):
        # recherche la date début et fin d'exercice de dateInput
        if not isinstance(dateInput, datetime.date):
            mess = "La valeur %s n'est pas une date : %s " % (labelDate,str(dateInput))
            if alertes : wx.MessageBox(mess)
            return (None,None)
        req = """SELECT date_debut, date_fin
                FROM compta_exercices;
                """
        retour = self.ExecuterReq(req,MsgBox="GestionDB.DB.GetExercices")
        if retour != "ok" :
            wx.MessageBox(str(retour))
        recordset = self.ResultatReq()
        dateDebut = None
        dateFin = None
        lastDeb = None
        lastFin = datetime.date(1900,1,1)
        if len(recordset)>0 :
            for dd, df in recordset:
                ddebut = ut.DateEngEnDateDD(dd)
                dfin = ut.DateEngEnDateDD(df)
                if (ddebut <= dateInput) and (dfin >= dateInput) :
                    dateDebut = ddebut
                    dateFin = dfin
                if dfin >lastFin :
                    lastDeb = ddebut
                    lastFin = dfin
        if dateDebut == None:
            mess = "Il n'y a pas d'exercice ouvert pour la date %s: %s \n Vérifiez la date comptable" % (labelDate,str(dateInput))
            if alertes : wx.MessageBox(mess)
            if approche and lastDeb != None :
                if dateInput.month >= lastDeb.month : 
                    anneeDeb = dateInput.year
                else: anneeDeb = dateInput.year - 1

                if dateInput.month > lastFin.month :
                    anneeFin = dateInput.year + 1
                else: anneeFin = dateInput.year
                dateDebut = datetime.date(anneeDeb,lastDeb.month,lastDeb.day)
                dateFin = datetime.date(anneeFin,lastFin.month,lastFin.day)
            else :
                return (None,None)
        if str(dateFin) > str(dateDebut):
            return (dateDebut,dateFin)
        else:
            mess = "Incohérence dans les dates de l'exercie du %s au %s" % (str(dateDebut),str(dateFin))
            if alertes : wx.MessageBox(mess)
        return (None,None)

    def GetUneDateCompta(self,label="Saisissez une date"):
        # retourne une date saisie, et son exercice s'il est ouvert'
        dlg = CTRL_SaisieSimple.DlgDate(None,label)
        dlg.ShowModal()
        dte = dlg.GetDate()
        exercice = (None, None)
        del dlg
        if dte:
            exercice =  self.GetExercice(dte)
            (deb,fin) = exercice
            if (not deb) or (not fin) or dte < deb or dte > fin:
                dte=None
                exercice = (None,None)
                mess = "La date saisie n'est pas dans un exercice ouvert!"
                wx.MessageBox(mess,caption="Date invalide")
        return dte, exercice

    def GetDateFacture(self,IDinscription, IDactivite,today,alertes = True, retourExercice = False ):
        msg = Messages()
        exercice = None
        dateFacture = None
        if IDactivite > 0:
            dateDeb, dateFin = GestionArticle.DebutFin_Activite(self,IDactivite)
            if dateFin == None or dateDeb == None:
                # l'activité n'a pas de dates définies
                    if alertes :
                        msg.Box(titre = "Date de l'activité non défine",message = "Il n'a pas été possible de trouver les dates de l'activité" )
        else:
            # le niveau famille stocke l'année de l'activité à la place de l'IDinscription, on l'affecte au 01 janvier
            dateDeb, dateFin = self.GetExercice(datetime.date(IDinscription,1,1), alertes = alertes)
            if dateDeb == None:
                dateDeb = datetime.date(IDinscription,1,1)
                dateFin = datetime.date(IDinscription,1,1)

        exTodayD,exTodayF = self.GetExercice(today, alertes= alertes )
        if dateFin != None and dateDeb != None:
            exActD,exActF = self.GetExercice(dateFin,labelDate = "de fin d'activité", alertes = alertes)
            if exActD != None:
                exercice = True
            else:
                exercice = False
            if today <= dateDeb :
                dateFacture = dateDeb
                if alertes :
                    # la date du jour précède le début de l'activité, choix nécessaire
                    txt1 = "Facture à la date du jour_____________ %s" %(str(today))
                    txt2 = "Facture à la date de début d'activité_ %s" %(str(dateDeb))
                    retour = msg.Choix([(1,txt1),(2,txt2)],"La facture n'est pas censée précéder l'activité,\nQuel est votre choix?")
                    if retour[0] == 1 :
                        dateFacture = today
                    elif retour[0] == 2:
                        dateFacture = dateDeb
                    else : dateFacture = None
            elif today > dateFin :
                # la fin d'activité précède la facture, on facture donc tardivement, vérifier la concordance des exercices
                if exActD == None:
                    #exercice de l'activité non ouvert
                    if alertes :
                        msg.Box(titre = "l'Exercice de l'activité est fermé",message = "Vous ne facturez pas cette activité dans le bon exercice" )
                    dateFacture = None
                else:
                    #exercice de l'activité ouvert
                    if exTodayD == None:
                        # seul l'exercice de l'activité est ouvert, on facture encore N-1, ok
                        dateFacture = exActF
                    else:
                        # les deux exercices sont ouverts
                        if exTodayD == exActD: # on est dans le même exercice, ok
                            dateFacture = today
                        else :
                            # choix nécessaire car le deux exerices sont différents
                            retour=[None]
                            dateFacture = dateFin
                            if alertes :
                                txt1 = "Exercice activité du %s au %s" %(str(exActD),str(exActF))
                                txt2 = "Exercice du jour  du %s au %s" %(str(exTodayD),str(exTodayF))
                                retour = msg.Choix([(1,txt1),(2,txt2)],"Deux exercices sont possibles, dans lequel faut-il affecter la pièce?")
                                if retour[0] == 1 :
                                    dateFacture = dateFin
                                elif retour[0] == 2:
                                    dateFacture = today
                                else :
                                    return wx.ID_ABORT
            else : #on facture pendant la durée de l'activité, ok
                dateFacture = today
        if dateFacture == None and dateFin != None:
            # on affecte la date fin activité mais il y a problème
            if alertes :
                msg.Box(titre = "Problème avec les Exercices comptables",message = "La facture prend la date de fin activité, \nmais ce n'est pas correct au vu des exercices ouverts" )
            dateFacture = dateFin
        if self.GetExercice(dateFacture, alertes = alertes) == (None,None):
            # aucun exercice ouvert n'a permis de fixer une date de facture
            mess = "Pas d'exercice ouvert pour cette activité\nSaisissez une date"
            (dateFacture, exercice) = self.GetUneDateCompta(mess)
        msg.Close()
        if retourExercice:
            return dateFacture,exercice
        return dateFacture

    # --------------------- MAJ de la base de donnée au démarrage ------------------------------------------------------

    def GetListeTables(self,lower=True):
        # appel des tables
        if self.isNetwork == False:
            # Version Sqlite
            req = "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"
            self.ExecuterReq(req,MsgBox="GestionDB.DB.GetListeTable")
            recordset = self.ResultatReq()
        else:
            # Version MySQL
            req = "SHOW TABLES;"
            self.ExecuterReq(req,MsgBox="GestionDB.DB.GetListeTable")
            recordset = self.ResultatReq()
        lstTables = []
        for (record,) in recordset:
            if lower:
                lstTables.append(record.lower())
            else: lstTables.append(record)
        return lstTables

    def GetListeChamps(self, nomTable=None):
        """ retrourne la liste des tuples(nom,type) des champs de la table donnée """
        lstChamps = []
        if not nomTable:
            """ Affiche la liste des champs de la précédente requête effectuée """
            for fieldDesc in self.cursor.description:
                lstChamps.append(fieldDesc[0])
            return lstChamps

        # dict de tables de liste
        if not hasattr(self,"ddTablesChamps"):
            self.dlTablesChamps = {}
        # un seul appel par table
        if not nomTable in self.dlTablesChamps.keys():
            if not self.isNetwork:
                # Version Sqlite
                req = "PRAGMA table_info('%s');" % nomTable
                self.ExecuterReq(req,MsgBox="GestionDB.DB.GetListeChamps")
                listeTmpChamps = self.ResultatReq()
                for valeurs in listeTmpChamps:
                    lstChamps.append((valeurs[1], valeurs[2]))
            else:
                # Version MySQL
                req = "SHOW COLUMNS FROM %s;" % nomTable
                ret = self.ExecuterReq(req,MsgBox = None)
                listeTmpChamps = self.ResultatReq()
                for valeurs in listeTmpChamps:
                    lstChamps.append((valeurs[0].lower(), valeurs[1].lower()))
            self.dlTablesChamps[nomTable] = lstChamps
        # la table a déjà été appellée
        else: lstChamps = self.dlTablesChamps[nomTable]
        return lstChamps

    def GetListeIndex(self):
        if self.isNetwork == False :
            # Version Sqlite
            req = "SELECT name FROM sqlite_master WHERE type='index' ORDER BY name;"
            self.ExecuterReq(req,MsgBox="GestionDB.DB.GetListeIndex")
            listeIndex = self.ResultatReq()
        else:
            # Version MySQL
            listeIndex = []
            for nomTable in self.GetListeTables(lower=False):
                req = "SHOW INDEX IN %s;" % str(nomTable)
                self.ExecuterReq(req,MsgBox="GestionDB.DB.GetListeIndex")
                for index in self.ResultatReq():
                    if str(index[2]) != 'PRIMARY':
                        listeIndex.append(str(index[2]))
        return listeIndex

def GetConnexionReseau(nomFichier=""):
    pos = nomFichier.index("[RESEAU]")
    paramConnexion = nomFichier[:pos]
    port, host, user, passwd = paramConnexion.split(";")
    nomFichier = nomFichier[pos:].replace("[RESEAU]", "")
    nomFichier = nomFichier.lower()
    passwd = DecodeMdpReseau(passwd)

    if INTERFACE_MYSQL == "mysqldb":
        my_conv = conversions
        my_conv[FIELD_TYPE.LONG] = int
        connexion = MySQLdb.connect(host=host, user=user, passwd=passwd, port=int(port), use_unicode=True, conv=my_conv, ssl=CERTIFICATS_SSL)
        connexion.set_character_set('utf8')

    if INTERFACE_MYSQL == "mysql.connector":
        if "_" in nomFichier :
            suffixe = nomFichier.split("_")[-1]
        else :
            suffixe = ""

        params = {
            "host": host,
            "user": user,
            "passwd": passwd,
            "port": int(port),
            "use_unicode": True,
        }

        # Activation du SSL
        if "ca" in CERTIFICATS_SSL:
            params["ssl_ca"] = CERTIFICATS_SSL["ca"]

        # Activation du pooling
        if POOL_MYSQL > 0 :
            params["pool_name"] = "mypool2%s" % suffixe
            params["pool_size"] = POOL_MYSQL

        connexion = mysql.connector.connect(**params)

    return connexion, nomFichier

def ConvertConditionChaine(liste=[]):
    """ Transforme une liste de valeurs en une condition chaine pour requête SQL """
    if len(liste) == 0 : condition = "()"
    elif len(liste) == 1 : condition = "(%d)" % liste[0]
    else : condition = str(tuple(liste))
    return condition

def TestConnexionMySQL(typeTest="fichier", nomFichier=""):
    """ typeTest=fichier ou reseau """
    dictResultats = {}
    cursor = None
    connexion = None

    # Test de connexion au réseau MySQL
    try :
        connexion, nomFichier = GetConnexionReseau(nomFichier)
        cursor = connexion.cursor()
        dictResultats["connexion"] =  (True, None)
        connexion_ok = True
    except Exception as err :
        dictResultats["connexion"] =  (False, err)
        connexion_ok = False

    # Test de connexion à une base de données
    if typeTest == "fichier" and connexion_ok == True:
        try:
            listeDatabases = []
            cursor.execute("SHOW DATABASES;")
            listeValeurs = cursor.fetchall()
            for valeurs in listeValeurs:
                listeDatabases.append(valeurs[0])
            if nomFichier in listeDatabases:
                # Ouverture Database
                cursor.execute("USE %s;" % nomFichier)
                # Vérification des tables
                cursor.execute("SHOW TABLES;")
                listeTables = cursor.fetchall()
                if not listeTables:
                    dictResultats["fichier"] = (False, _("La base de données est vide."))
                else:
                    dictResultats["fichier"] =  (True, None)
            else:
                dictResultats["fichier"] = (False, _("Accès au fichier impossible."))
        except Exception as err:
            dictResultats["fichier"] = (False, err)

    if connexion != None:
        connexion.close()
    return dictResultats

# -------------- Infos sur la base et outils --------------------------------

class GestionBase(wx.Frame):
    def __init__(self,suffixe='_data',nomBase=None):
        """Constructor"""
        #wx.Frame.__init__(self, parent=None, size=(550, 400))
        self.db = DB()
        if nomBase:
            nomFichier = self.db.nomFichier
            pos = nomFichier("[RESEAU]")
            nomFichier = nomFichier[:pos]+"[RESEAU]"+nomBase
            self.db = DB(suffixe=suffixe,nomFichier=nomFichier)
        print(('echec',self.db.echec))

    def GetOccupations(self):
        # pointer base: 'information_schema' valeurs plus hautes
        req = """SELECT name, file_size  
        FROM INNODB_SYS_TABLESPACES
        WHERE name LIKE 'matthania_data%%'
        ORDER BY file_size DESC
        ;"""
        req = """
            SELECT 
             TABLE_NAME,
             ROUND(((DATA_LENGTH + INDEX_LENGTH) / 1024 / 1024), 2) AS TailleMo 
            FROM information_schema.TABLES 
            WHERE TABLE_SCHEMA = 'matthania_data'
            ORDER BY TailleMo DESC;
            """
        ret = self.db.ExecuterReq(req,MsgBox="GestionDB.GestionBase.GetOccupation")
        print(('Execute:',ret))
        lstOccupations = self.db.ResultatReq()
        return lstOccupations

def ImporterFichierDonnees() :
    db = DB(nomFichier=Chemins.GetStaticPath("Databases/Prenoms.dat"), suffixe=None, modeCreation=True)
    db.CreationTable("prenoms",None)
    db.Close()

    txt = open("prenoms.txt", 'r').readlines()
    db = DB(nomFichier=Chemins.GetStaticPath("DatabasesPrenoms.dat"), suffixe=None)
    index = 0
    for ligne in txt :
        ID, prenom, genre = ligne.split(";")
        listeDonnees = [("prenom", prenom), ("genre", genre),]
        IDprenom = db.ReqInsert("prenoms", listeDonnees)
        index += 1
    db.Close()

def CreationBaseAnnonces():
    """ Création de la base de données sqlite pour les Annonces """
    DB_DATA_ANNONCES = {
            "annonces_aleatoires":[             ("IDannonce", "INTEGER PRIMARY KEY AUTOINCREMENT", _("ID Annonce")),
                                                            ("image", "VARCHAR(200)", _("Nom de l'image")),
                                                            ("titre", "VARCHAR(300)", _("Titre")),
                                                            ("texte_html", "VARCHAR(500)", _("Texte HTML")),
                                                            ("texte_xml", "VARCHAR(500)", _("texte XML")),
                                                            ],

            "annonces_dates":[                   ("IDannonce", "INTEGER PRIMARY KEY AUTOINCREMENT", _("ID Annonce")),
                                                            ("date_debut", "DATE", _("Date de début")),
                                                            ("date_fin", "DATE", _("Date de fin")),
                                                            ("image", "VARCHAR(200)", _("Nom de l'image")),
                                                            ("titre", "VARCHAR(300)", _("Titre")),
                                                            ("texte_html", "VARCHAR(500)", _("Texte HTML")),
                                                            ("texte_xml", "VARCHAR(500)", _("texte XML")),
                                                            ],

            "annonces_periodes":[              ("IDannonce", "INTEGER PRIMARY KEY AUTOINCREMENT", _("ID Annonce")),
                                                            ("jour_debut", "INTEGER", _("Jour début")),
                                                            ("mois_debut", "INTEGER", _("Mois début")),
                                                            ("jour_fin", "INTEGER", _("Jour fin")),
                                                            ("mois_fin", "INTEGER", _("Mois fin")),
                                                            ("image", "VARCHAR(200)", _("Nom de l'image")),
                                                            ("titre", "VARCHAR(300)", _("Titre")),
                                                            ("texte_html", "VARCHAR(500)", _("Texte HTML")),
                                                            ("texte_xml", "VARCHAR(500)", _("texte XML")),
                                                            ],

        }
    db = DB(nomFichier=Chemins.GetStaticPath("Databases/Annonces.dat"), suffixe=None, modeCreation=True)
    db.CreationTable("annonces_aleatoires", DB_DATA_ANNONCES)
    db.CreationTable("annonces_dates", DB_DATA_ANNONCES)
    db.CreationTable("annonces_periodes", DB_DATA_ANNONCES)
    db.Close()

def AfficheConnexionsOuvertes(msgFin="fin"):
    """ Affiche les connexions non fermées """
    if len(DICT_CONNEXIONS) > 1 :
        print("--------- Attention, il reste %d connexions encore ouvertes : ---------" % ((len(DICT_CONNEXIONS) - 1),))
        ix = 0
        for IDconnexion, msgs in DICT_CONNEXIONS.items() :
            # la première est celle de parent
            if ix == 0:
                ix += 1
                continue
            texte = ""
            for msg in msgs:
                if msg:
                    texte += "%s / "%msg
            print(">> IDconnexion = %d (%d requêtes) : %s" % (IDconnexion, len(msgs), texte))
    else: print(msgFin)

def DecodeMdpReseau(mdp=None):
    if mdp not in (None, "") and mdp.startswith("#64#"):
        try:
            mdp = base64.b64decode(mdp[4:])
            mdp = mdp.decode('utf-8')
        except:
            pass
    return mdp

def EncodeMdpReseau(mdp=None):
    mdp = mdp.encode()
    mdp = base64.b64encode(mdp)
    mdp = mdp.decode('utf-8')
    mdp = "#64#%s" % mdp
    return mdp

def EncodeNomFichierReseau(nom_fichier=None):
    if "[RESEAU]" in nom_fichier and "#64#" not in nom_fichier:
        pos = nom_fichier.index("[RESEAU]")
        parametres = nom_fichier[:pos]
        port, hote, utilisateur, motdepasse = parametres.split(";")
        fichier = nom_fichier[pos:].replace("[RESEAU]", "")
        nouveau_motdepasse = EncodeMdpReseau(motdepasse)
        nom_fichier = "%s;%s;%s;%s[RESEAU]%s" % (port, hote, utilisateur, nouveau_motdepasse, fichier)
    return nom_fichier

def Decod(valeur):
    if valeur == None:
        valeurDecod =  ""
    elif type(valeur) in (int, int, float):
        valeurDecod = str(valeur)
    else :
        try :
            valeurDecod = valeur.decode('utf8')
        except:
            try:
                valeurDecod = valeur.decode('iso-8859-15')
            except:
                valeurDecod = valeur
    return valeurDecod

# ------------- Affichages à remplacer par wx.MessageBox -------------------

def MessageBox(self,mess,titre = "Erreur Bloquante !",YesNo = False):
    if YesNo :
        dlg = wx.MessageDialog(self, _(mess),_(titre) , wx.YES_NO|wx.NO_DEFAULT|wx.CANCEL| wx.ICON_EXCLAMATION)
    else :
        dlg = wx.MessageDialog(self, _(mess),_(titre) , wx.OK | wx.ICON_EXCLAMATION)
    ret = dlg.ShowModal()
    dlg.Destroy()
    return ret

class Messages(wx.Frame):
    def __init__(self):
        """Constructor"""
        wx.Frame.__init__(self, parent=None, size=(550, 400))

    def Box(self, titre= "Erreur Bloquante", message= "Avertissement",YesNo = False ):
        if YesNo :
            dlg = wx.MessageDialog(self,  message, titre , wx.YES_NO|wx.NO_DEFAULT|wx.CANCEL| wx.ICON_QUESTION)
        else :
            dlg = wx.MessageDialog(self, message, titre, wx.OK | wx.ICON_EXCLAMATION)
        ret = dlg.ShowModal()
        dlg.Destroy()
        if ret == wx.ID_YES: ret = wx.ID_OK
        return ret

    def Choix(self,listeTuples=[(1,"a"),(2,"b")], titre = "Choisissez", intro = "Dans la liste"):
        dlg = CTRL_ChoixListe.Dialog(self,LargeurCode= 30,LargeurLib= 200,minSize = (500,300), listeOriginale=listeTuples, titre = titre, intro = intro)
        interroChoix = dlg.ShowModal()
        if interroChoix == wx.ID_OK :
            sel=dlg.choix
            return sel
        else:
            return None,None

if __name__ == "__main__":
    app = wx.App()
    #gdb = GestionBase()#nomFichier=u'3306;192.168.1.43;root;motdepasse[RESEAU]information_schema',suffixe=None
    #print(gdb.GetOccupations())

