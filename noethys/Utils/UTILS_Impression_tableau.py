#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------
# Application :    Matthania, outil d'impression PDF d'un tableau standard
# Site internet :  www.noethys.com
# Auteur:          Jacques BRUNEL
# Licence:         Licence GNU GPL
#-------------------------------------------------------------------------


from Utils.UTILS_Traduction import _
from Utils import UTILS_Fichiers
import wx
import sys
import datetime # ne pas enlever
import FonctionsPerso
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle

COULEUR_BLACK =(0, 0, 0)
TAILLE_PAGE = landscape(A4)

def DateEngFr(textDate):
    if textDate == None: return ""
    textDate = str(textDate)
    text = str(textDate)[8:10] + "/" + str(textDate)[5:7] + "/" + str(textDate)[:4]
    return text

def ConvertCouleurWXpourPDF(couleurwx=(0, 0, 0)):
    return (couleurwx[0]/255.0, couleurwx[1]/255.0, couleurwx[2]/255.0)

def FormateMontant(montant,lgmini=12,nbdecimales=2):
    if montant == None: return ""
    try:
        montant = float(montant)
    except:
        return "???"
    model = '{:%d,.%df}'%(lgmini,nbdecimales)
    strMontant = model.format(montant).replace(',', ' ')
    return strMontant

def ExtractAlign(texte):
    txt = texte
    align = ''
    lstparts = texte.split('>')
    for part in lstparts:
        if '<align' in part:
            ix = texte.index('<align')
            ix2 = part.index('<align')
            txt = texte[:ix]+texte[(ix-ix2+len(part)+1):]
            align = part[-ix2+1:]
    return align,txt

class Impression():
    def __init__(self, dictOptionsImpression={}):
        self.dictOptionsImpression = dictOptionsImpression
         # Recherche la couleur de titre
        couleur_fond_titre = ConvertCouleurWXpourPDF((204,204, 255))
        if "couleur" in self.dictOptionsImpression :
            if self.dictOptionsImpression["couleur"] != False :
                couleur_fond_titre = ConvertCouleurWXpourPDF(self.dictOptionsImpression["couleur"])

        #les styles sont appelés par chaque texte, leading est l'interligne, space le paragraphe
        self.dictStylesTexte = {
                "editele" : ParagraphStyle(
                                      name="editele",
                                      fontName="Helvetica",
                                      fontSize=8,
                                      leading=8,
                                      spaceBefore=5,
                                      spaceafter=5,),
                "titre" : ParagraphStyle(name="titre",
                                      fontName="Helvetica-Bold",
                                      fontSize=12,
                                      leading=18,
                                      spaceBefore=0,
                                      spaceafter=10,),
                "sstitre" : ParagraphStyle(name="sstitre",
                                      fontName="Helvetica-Bold",
                                      fontSize=18,
                                      leading=18,
                                      spaceBefore=10,
                                      spaceafter=10,),
                "texte" : ParagraphStyle(name="texte",
                                      fontName="Times-Roman",
                                      fontSize=10,
                                      leading=10,
                                      spaceBefore=0,
                                      spaceafter=0,),
                "nombre" : ParagraphStyle(name="nombre",
                                      fontName="Helvetica",
                                      fontSize=9,
                                      leading=10,
                                      spaceBefore=0,
                                      spaceafter=0,),
                "total" : ParagraphStyle(name="total",
                                      fontName="Helvetica-Bold",
                                      fontSize=12,
                                      leading=12,
                                      spaceBefore=50,
                                      spaceafter=50,),
                }

        # Le styleGrid est envoyé pour l'ensemble du tableau selon la clé du premier texte du premier paragraphe
        self.dictStylesGrid = {
                "tete": [
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONT', (0, 0), (-1, -1), "Helvetica", 14),],
                "hautdecorps": [
                        ('BOX', (0, 0), (-1, -1), 0.5, COULEUR_BLACK),
                        ('GRID', (0, 0), (-1, -1), 0.05, COULEUR_BLACK),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('BACKGROUND', (-1, -1), (-1, -1), couleur_fond_titre), ],
                "corps": [
                        ('BOX', (0, 0), (-1, -1), 0.5, COULEUR_BLACK),
                        ('GRID', (0, 0), (-1, -1), 0.05, COULEUR_BLACK),
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),],
                "pied" : [
                        ('BOX', (0, -1), (-1, -1), 0.5, COULEUR_BLACK),
                        ('GRID', (1, -1), (-1, -1), 0.05, COULEUR_BLACK),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
                        ('BACKGROUND', (-1, 0), (-1, -1), couleur_fond_titre),]}
        """ champs d'application :(colonneDébut, ligneDébut), (colonneFin, ligneFin) (-1 la dernière, -2 l'avantdern)
            BOX est le contour (champs,épaisseur,couleur)
            GRID  est un quadrillage
            BACKGROUND colorisation (champs , couleur) blanc est (255,255,255)
            FONT usage à préciser
            ALIGN usage à préciser, mais on utilise le mot RIGHT LEFT ou CENTER pour un alignement par défaut.
        """

    def CompositionPDF(self, lstTableaux=[], nomDoc=None, afficherDoc=True):
        # Les styles dans dicStyles peuvent avoir été modifié par le lanceur avant cet appel
        if not nomDoc:
            nomDoc = "Impression_noethys.pdf"
        if (not "/" in nomDoc) and not "\\" in nomDoc:
            nomDoc = UTILS_Fichiers.GetRepTemp("Impression_noethys.pdf")
        keysStylesTexte = list(self.dictStylesTexte.keys())+[None,]
        keysStylesGrid = list(self.dictStylesGrid.keys())+[None,]
        typesMultiples = (tuple,list,dict)
        NoneType = type(None)
        # Initialisation du document
        if sys.platform.startswith("win") : nomDoc = nomDoc.replace("/", "\\")
        doc = SimpleDocTemplate(nomDoc, topMargin=20, bottomMargin=10, pagesize=TAILLE_PAGE, showBoundary=False)
        story = []

        # Fonction de transformation en paragraphe reportlab (cellule)
        def paragraphe(champ,gridStyle=None):
            # Champ est un tuple (valeur, style)
            para = Paragraph("<para align='right'> !!!!! </para>", self.dictStylesTexte["texte"])
            if len(champ) != 2 or not isinstance(champ[1],(str,NoneType)):
                wx.MessageBox("Le champ %s n'est pas composé d'une valeur et d'un style" % str(champ))
                return para,"texte"
            style = champ[1]
            valeur = champ[0]
            if valeur == "lib12.2":
                pass
            align = ''
            if not style or len(style)<2:
                style = ''
            if style in list(self.dictStylesTexte.keys()):
                parastyle = self.dictStylesTexte[style]
            else: parastyle = self.dictStylesTexte["texte"]

            # le grid style détermine l'alignement par défaut
            if gridStyle:
                if not gridStyle in list(self.dictStylesGrid.keys()): wx.MessageBox("Le style '%s' n'est pas paramétré dans dictStylesGrid"%gridStyle)
                if "RIGHT" in str(self.dictStylesGrid[gridStyle]):
                    align = "align='right'"
                elif "LEFT" in str(self.dictStylesGrid[gridStyle]):
                    align = "align='left'"
                elif "CENTRE" in str(self.dictStylesGrid[gridStyle]):
                    align = "align='center'"
                elif "CENTER" in str(self.dictStylesGrid[gridStyle]):
                    align = "align='center'"

            # un nombre est toujours calé à droite, soit par sa nature soit par son style
            if isinstance(valeur, (int,bool,float)) or style == "nombre":
                align = "align='right'"

            if valeur in (None,):
                para = Paragraph("<para > </para>", parastyle)
            elif isinstance(valeur, str):
                # priorité à l'alignement précisé dans le champ
                if '<align' in valeur: align,valeur = ExtractAlign(valeur)
                para = Paragraph("<para %s> %s</para>"%(align,valeur), parastyle)
            elif isinstance(valeur, (int,float)):
                txtmtt = FormateMontant(valeur)
                para = Paragraph("<para %s> %s</para>"%(align,txtmtt), parastyle)
            else:
                txt = str(valeur)
                if '<align' in txt: align,txt = ExtractAlign(txt)
                para = Paragraph("<para %s> %s</para>"%(align,txt), parastyle)
            return para

        # Normalisation d'un champ simple en tuple contenant un style
        def tuplise(champ):
            # les tuple ou listes non vides ne sont pas traités
            if not champ or champ in ([],(),"","",0,0.0):
                champ = ("", None)
            elif isinstance(champ, (str,int,float)):
                champ = (champ, None)
            elif isinstance(champ, datetime.date):
                champ = (DateEngFr(str(champ)), None)
            elif isinstance(champ, (tuple,list)) and (len(champ)==1):
                champ = (champ[0],None)
            return champ

        # Découpage d'un champ composé en liste de champs simples
        def listparalise(champ,gridStyle=None):
            lstpara = []
            for item in champ:
                item = tuplise(item)
                if isinstance(item, tuple) and len(item)==2 and item[1] in keysStylesTexte:
                    para = paragraphe(item,gridStyle)
                    lstpara.append(para)
                else:
                    lstpara.extend(listparalise(item,gridStyle))
            return lstpara

        # Déroulé des champs composant le tableau, et mise au format

        for tableau in lstTableaux:
            dataTableau = []

            # Contrôles préalables
            if not "dataLignes" in list(tableau.keys()):
                wx.MessageBox("Le tableau '%d' ne contient la clé 'dataLignes'"%(lstTableaux.index(tableau)))
                break
            if not "largeursCol" in list(tableau.keys()):
                wx.MessageBox("Le tableau '%d' ne contient la clé 'largeursCol'"%(lstTableaux.index(tableau)))
                break
            if not "gridStyle" in list(tableau.keys()):
                wx.MessageBox("Le tableau en posistion '%d' ne contient de clé 'gridStyle'"%(lstTableaux.index(tableau)))
                break
            nbCol = len(tableau["largeursCol"])
            gridStyle = tableau["gridStyle"]
            if not gridStyle in list(self.dictStylesGrid.keys()):
                wx.MessageBox("Le gridStyle '%s' est non programmé!"%gridStyle)

            # Tableau / ligne / champ / [ligne du champ]
            for ligne in tableau["dataLignes"]:
                dataLigne = []
                if len(ligne)!=nbCol:
                    # ajouter des champs vides devant puis tronquer
                    ligne = ([None,]*nbCol+ligne)[nbCol-len(ligne):]
                for champ in ligne:
                    if not isinstance(champ,typesMultiples):
                        champ = tuplise(champ)
                    # champ est soit un tuple soit une liste
                    if isinstance(champ,tuple) and len(champ) == 2 and champ[1] in keysStylesTexte :
                        para = paragraphe(champ,gridStyle)
                        # Place dans le parapgraphe
                        dataLigne.append(para)
                    else:
                        # tous les composants du champ vont générer des lignes du parapgraphe
                        lstpara = listparalise(champ,gridStyle)
                        dataLigne.append(lstpara)
                dataTableau.append(dataLigne)

            tableau = Table(dataTableau, tableau["largeursCol"])
            if gridStyle:
                styletab = TableStyle(self.dictStylesGrid[gridStyle])
                tableau.setStyle(styletab)
            story.append(tableau)
            story.append(Spacer(0, 0))

        # Enregistrement et ouverture du PDF
        try :
            doc.build(story)
        except Exception as err :
            print("Erreur dans ouverture PDF :", err)
            dlg = wx.MessageDialog(None, _("Noethys ne peut pas créer le PDF.\n\nerr : '%s'\nVérifiez qu'un autre PDF n'est pas déjà ouvert en arrière-plan..."%err), _("Erreur d'édition"), wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            return "ko"
        
        # Affichage du PDF
        if afficherDoc == True :
            FonctionsPerso.LanceFichierExterne(nomDoc)
        return "ok"

if __name__ == "__main__":
    app = wx.App(0)

    tab1 = {"dataLignes":[  [    ( ("MON TITRE DE DOCUMENT","titre"),
                                   (1250.5,'nombre'),
                                   ('mon texte style texte',"texte"),
                                   "tableau de test sans style",
                                   ("<align=center>autre ligne 'align=center' dans le texte et sans style"),
                                   0,
                                   None,
                                   ),
                                (str(datetime.date.today()),"editele")
                            ],
                            [None,("nvl ligne deuxième champ")],
                         ],
            "largeursCol":[360,120],
            "gridStyle":"tete"}

    tab2 = {"dataLignes":[[("col1","texte"),[("col2.1total","total"),("<align='center'>col2.2")],("col3<b>b intexte</b>","centre"),("mt1","texte"),("mt2",),("mt3","nombre")],
                          [("titre","titre"),[("lib12.1 texte","texte"),("lib12.2","texte")],("lib13.1 sans","lib13.2"),(60.25,"texte"),0,(80,"nombre")],
                          ["lib21",("lib22","nombre"),("lib23","texte"),(None,"texte"),(100.2,"texte"),(810,"nombre")]],
            "largeursCol":[60,290,290,50,50,50],
            "gridStyle":"corps"
            }

    lstTableaux = [tab1,tab2]
    dialog_1 = Impression()
    dialog_1.CompositionPDF(lstTableaux)
    wx.MessageBox("fin")
    app.MainLoop()