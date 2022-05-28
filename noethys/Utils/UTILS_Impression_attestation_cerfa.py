#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, Matthania
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS, JB
# Copyright:       (c) 2010-11 Ivan LUCAS, JB
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------


from Utils.UTILS_Traduction import _
import wx
import datetime
import FonctionsPerso

from Dlg import DLG_Noedoc
from Utils import UTILS_Dates
from Utils import UTILS_Fichiers
from Utils import UTILS_Config
SYMBOLE = UTILS_Config.GetParametre("monnaie_symbole", "€")

from reportlab.platypus.doctemplate import PageTemplate, BaseDocTemplate
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.platypus.frames import Frame, ShowBoundaryValue
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch, cm,mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus.flowables import DocAssign, Flowable


TAILLE_PAGE = A4
LARGEUR_PAGE = TAILLE_PAGE[0]
HAUTEUR_PAGE = TAILLE_PAGE[1]

TAILLE_CADRE_CONTENU = (5*cm, 5*cm, 14*cm, 17*cm)

DICT_COMPTES = {}
DICT_OPTIONS = {} 




class MyCanvas(Canvas):
    def __init__(self, filename,
                 pagesize=None,
                 bottomup = 1,
                 pageCompression=1,
                 invariant = None,
                 verbosity=0):
        Canvas.__init__(self, filename, pagesize=pagesize, bottomup=bottomup, pageCompression=pageCompression,
                        invariant=invariant, verbosity=verbosity)
        self.setPageSize(TAILLE_PAGE)

def Template(canvas, doc):
    """ Première page de l'attestation """
    doc.modeleDoc.DessineFond(canvas) 
    doc.modeleDoc.DessineFormes(canvas) 

class MyPageTemplate(PageTemplate):
    def __init__(self, id=-1, pageSize=TAILLE_PAGE, doc=None):
        self.pageWidth = pageSize[0]
        self.pageHeight = pageSize[1]
        
        # Récupère les coordonnées du cadre principal
        cadre_principal = doc.modeleDoc.FindObjet("cadre_principal")
        if cadre_principal:
            x, y, l, h = doc.modeleDoc.GetCoordsObjet(cadre_principal)
            global CADRE_CONTENU
            CADRE_CONTENU = (x, y, l, h)
            frame1 = Frame(x, y, l, h, id='F1', leftPadding=0, topPadding=0, rightPadding=0, bottomPadding=0)
            PageTemplate.__init__(self, id, [frame1], Template)

    def afterDrawPage(self, canvas, doc):
        IDcompte_payeur = doc._nameSpace["IDcompte_payeur"]
        dictCompte = DICT_COMPTES[IDcompte_payeur]
        canvas.saveState() 
                
        # Insertion des lignes de textes
        doc.modeleDoc.DessineImages(canvas, dictChamps=dictCompte)
        doc.modeleDoc.DessineTextes(canvas, dictChamps=dictCompte)
        
        canvas.restoreState()

def Template_PagesSuivantes(canvas, doc):
    """ Première page de l'attestation """
    canvas.saveState()

    canvas.setFont('Times-Roman', 12)
    pageNumber = canvas.getPageNumber()
    canvas.drawCentredString(10*cm, cm, str(pageNumber))

    canvas.restoreState()

class Bookmark(Flowable):
    """ Utility class to display PDF bookmark. """
    def __init__(self, title, key):
        self.title = title
        self.key = key
        Flowable.__init__(self)

    def wrap(self, availWidth, availHeight):
        """ Doesn't take up any space. """
        return (0, 0)

    def draw(self):
        # set the bookmark outline to show when the file's opened
        self.canv.showOutline()
        # step 1: put a bookmark on the 
        self.canv.bookmarkPage(self.key)
        # step 2: put an entry in the bookmark outline
        self.canv.addOutlineEntry(self.title, self.key, 0, 0)

class Impression():
    def __init__(self, dictComptes={}, dictOptions={}, IDmodele=None, ouverture=True, nomFichier=None):
        """ Impression """
        global DICT_COMPTES, DICT_OPTIONS
        DICT_COMPTES = dictComptes
        DICT_OPTIONS = dictOptions
        
        # Initialisation du document
        if nomFichier == None :
            nomFichier = "Attestations_fiscales_%s.pdf" % FonctionsPerso.GenerationIDdoc()
        nomDoc = nomFichier
        if not "\\" in nomFichier:
            nomDoc = UTILS_Fichiers.GetRepTemp(nomFichier)

        doc = BaseDocTemplate(nomDoc, pagesize=TAILLE_PAGE, showBoundary=False)

        # Mémorise le ID du modèle
        modeleDoc = DLG_Noedoc.ModeleDoc(IDmodele=IDmodele)
        doc.modeleDoc = modeleDoc

        # Vérifie qu'un cadre principal existe bien dans le document
        if doc.modeleDoc.FindObjet("cadre_principal") == None :
            mess = "Votre modèle de document doit obligatoirement comporter un cadre principal.\n"
            mess += "Retournez dans l'éditeur de document et utilisez pour votre modèle la commande:\n"
            mess += "'Insérer un objet spécial > Insérer le cadre principal'."
            wx.MessageBox(mess)

        # Mémorise le ID du modèle
        modeleDoc = DLG_Noedoc.ModeleDoc(IDmodele=IDmodele)
        doc.modeleDoc = modeleDoc
        
        # Importe le template de la première page
        doc.addPageTemplates(MyPageTemplate(pageSize=TAILLE_PAGE, doc=doc))
        
        story = []
        styleSheet = getSampleStyleSheet()
        h3 = styleSheet['Heading3']
        styleTexte = styleSheet['BodyText'] 
        styleTexte.fontName = "Helvetica"
        styleTexte.fontSize = 9
        styleTexte.borderPadding = 9
        styleTexte.leading = 12

        # ----------- Insertion du contenu des frames --------------
        listeNomsSansCivilite = []
        for IDcompte_payeur, dictCompte in dictComptes.items() :
            listeNomsSansCivilite.append((dictCompte["{FAMILLE_NOM}"], IDcompte_payeur))
        listeNomsSansCivilite.sort() 
        
        for nomSansCivilite, IDcompte_payeur in listeNomsSansCivilite :
            dictCompte = dictComptes[IDcompte_payeur]
                
            story.append(DocAssign("IDcompte_payeur", IDcompte_payeur))
            nomSansCivilite = dictCompte["{FAMILLE_NOM}"]
            story.append(Bookmark(nomSansCivilite, str(IDcompte_payeur)))
            
            # ------------------- TITRE -----------------
            dataTableau = []
            largeursColonnes = [ TAILLE_CADRE_CONTENU[2], ]
            dataTableau.append((dictOptions["titre"],))
            texteDateReference = UTILS_Dates.DateEngFr(str(datetime.date.today()))
            dataTableau.append((_("Période du %s au %s") % (UTILS_Dates.DateDDEnFr(dictOptions["date_debut"]), UTILS_Dates.DateDDEnFr(dictOptions["date_fin"])),))
            style = TableStyle([
                    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'), 
                    ('FONT',(0,0),(0,0), "Helvetica-Bold", 19), 
                    ('FONT',(0,1),(0,1), "Helvetica", 8), 
                    ('LINEBELOW', (0,0), (0,0), 0.25, (0,0,0)), 
                    ('ALIGN', (0,0), (-1,-1), 'LEFT'), 
                    ])
            tableau = Table(dataTableau, largeursColonnes)
            tableau.setStyle(style)
            story.append(tableau)
            story.append(Spacer(0, 30))
            
                
            couleurFond = (0.8, 0.8, 1)
            couleurFondActivite = (0.92, 0.92, 1)
                    
            # TEXTE CONTENU
            paraStyle = ParagraphStyle(name="contenu",
                          fontName="Helvetica",
                          fontSize=11,
                          leading=16,
                          spaceBefore=0,
                          spaceafter=0,
                          leftIndent=6,
                          rightIndent=6,
                        )
            
            # INTRO
            texte = ""
            """
            if texte != "" :
                listeParagraphes = texte.split("</para>")
                for paragraphe in listeParagraphes :
                    textePara = Paragraph(u"%s" % paragraphe, paraStyle)
                    story.append(textePara)
                
                story.append(Spacer(0, 25))
            # DETAIL par enfant
            dataTableau = [(_("Nom et prénom"), _("Date de naissance"), _("Montant")),]
            largeursColonnes = [ 220, 80, 80]
            
            paraStyle = ParagraphStyle(name="detail",
                                      fontName="Helvetica-Bold",
                                      fontSize=9,
                                    )

            style = TableStyle([
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), 
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('GRID', (0, 0), (-1, -2), 0.25, (0,0,0)),
                    ('FONT', (0, 0), (-1, 0), "Helvetica", 6), 
                    ('FONT', (0, 1), (-1, -1), "Helvetica", 10), 

                    ('TOPPADDING', (0, 1), (-1, -2), 10), 
                    ('BOTTOMPADDING', (0, 1), (-1, -2), 10), 
                    
                    ('GRID', (-1, -1), (-1, -1), 0.25, (0,0,0)),
                    ('FONT', (-1, -1), (-1, -1), "Helvetica-Bold", 10), 
                    story = {list: 5} [<reportlab.platypus.flowables.DocAssign instance at 0x0A367F80>, <UTILS_Impression_attestation_cerfa.Bookmark instance at 0x0A367DA0>, Table(\n rowHeights=[None, None],\n colWidths=[396.8503937007874],\n[['Attestation Fiscale'], ['P\xc3\xa9riode du 01/01/20? View
                    ('ALIGN', (-2, -1), (-2, -1), 'RIGHT'),
                    ('FONT', (-2, -1), (-2, -1), "Helvetica", 6), 
                    ])
            tableau = Table(dataTableau, largeursColonnes)
            tableau.setStyle(style)
            story.append(tableau)
            """

            # Saut de page
            story.append(PageBreak())
        
        # Finalisation du PDF
        doc.build(story)
        
        # Ouverture du PDF
        if ouverture == True :
            FonctionsPerso.LanceFichierExterne(nomDoc)





if __name__ == "__main__":
##    Impression()
    
    app = wx.App(0)
    from Dlg import DLG_Attestations_cerfa
    dlg = DLG_Attestations_cerfa.Dialog(None)
    dlg.ShowModal()
    dlg.Destroy()
    app.MainLoop()
