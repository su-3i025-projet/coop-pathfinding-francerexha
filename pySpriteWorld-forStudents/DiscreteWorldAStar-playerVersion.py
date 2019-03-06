# -*- coding: utf-8 -*-

# Nicolas, 2015-11-18

from __future__ import absolute_import, print_function, unicode_literals
from gameclass import Game,check_init_game_done
from spritebuilder import SpriteBuilder
from players import Player
from sprite import MovingSprite
from ontology import Ontology
from itertools import chain
import pygame
import glo
import heapq

import random 
import numpy as np
import sys


# ---- ---- ---- ---- ---- ----
# ---- Misc                ----
# ---- ---- ---- ---- ---- ----


def AETOILE(coordDepart, coordBut, grille): #coord format: [ligne, colonne]
    #on récupère les positions de départ et de but :
    posX = coordDepart[0]
    posY= coordDepart[1]
    butX= coordBut[0]
    butY= coordBut[1]
    print(butX)
    print(butY)
    
    # on créé le noeud racine, où on se trouve au début du problème :
    h =  heuristique(coordDepart, coordBut)
    noeudRacine = {'posX':posX,'posY':posY,'imat_provenance':0,'g':0,'h':h,'immatriculation':0}#on ne met plus la grille dans les noeuds (trop lourd), on stoque l'imatriculation du parent à la place et on remontera tout depuis le but pour trouver le chemin
    imatNb = 1#nombre de noeuds, détermine l'immatriculation des noeuds
    #on initialise la frontière : (indexée 'clé | valeur' = f | noeud)
    # frontiere = [(h,noeudRacine)]  #PB DUPLICATION car f égaux multiples en clée
    noeudsOuverts = [noeudRacine]
    #on initialise la liste des noeuds déjà traités :
    noeudsFermes = []
   # print(str(posX)+" : "+str(posY))
   # print(str(butX)+" : "+str(butY))
    #on boucle tant qu'on a pas épuisé toutes les possibilités
    while noeudsOuverts != []:              
        #  (currH,currNoeud) = heapq.heappop(frontiere)#on récupère le plus proche élément de la frontière  
        (currNoeud, noeudsOuverts) = depilerPlusPetit(noeudsOuverts)#on dépile l'élément d eplus petit f du tableau, équivalent à l'ancienne frontière mais pas de pb de duplication du coup !
        #print(noeudsOuverts)
        #print(currNoeud)
        #grille[currNoeud.get('posX')][currNoeud.get('posY')] = 'X'
        #print(grille)
        if currNoeud.get('posX')==butX and currNoeud.get('posY')==butY:#si on a atteint le but :
            print("but atteint")
           # print(currNoeud)
            (chemin, listeChemin) = tracerChemin(grille, noeudsOuverts, noeudsFermes, currNoeud)#on trace le chemin en remontant les noeuds de provenance
            return (chemin, listeChemin) #terminaison du programme
        #sinon:
        (nouveauxNoeuds, imatNb) = voisins(currNoeud, coordBut, imatNb, grille)#on récupère les noeuds fils explorables et le nouveau nombre de noeuds
       # print(nouveauxNoeuds)
        for noeud in nouveauxNoeuds:
            if existeAvecCoutInf(noeud, noeudsFermes)==1 or existeAvecCoutInf(noeud, noeudsOuverts)==1:#si ouvert ou fermé avec cout moindre
                #ne rien faire
                continue
                #print("noeud inintéressant")#un message au hasard juste pour respecter l'identation python ^^
            else:#sinon
                #f = noeud.get('g')+noeud.get('h')
                #heapq.heappush(frontiere, (f,noeud)))# PB dans la frontière (problème de duplication comme f identiques)
                noeudsOuverts.append(noeud)#pas de pb de duplication mais pas de tri sur f
        noeudsFermes.append(currNoeud)#on ferme le noeud courrant pour le moment
    return 1 #terminaison du programme
                
def tracerChemin(grille, noeudsOuverts, noeudsFermes, noeudFinal):
    listeChemin = []
    noeud = noeudFinal
    precedent = noeud.get('imat_provenance')
    print("tracer chemin:")
    print(noeud)
    print(precedent)
    while precedent != -1 :
        grille[noeud.get('posX')][noeud.get('posY')] = 'C'
        oldX = noeud.get('posX')
        oldY = noeud.get('posY')
        if chercherNoeud(precedent, noeudsOuverts)!=0 :
            noeud = chercherNoeud(precedent, noeudsOuverts)
            precedent = noeud.get('imat_provenance')
        else:
            if chercherNoeud(precedent, noeudsFermes)!=0 :
                noeud = chercherNoeud(precedent, noeudsFermes)
                precedent = noeud.get('imat_provenance')
            else:
                precedent = -1
        newX = noeud.get('posX')
        newY = noeud.get('posY')
        if newX!=oldX or newY!=oldY :
            deplacementCol= oldY-newY
            deplacementLign = oldX-newX
            #listeChemin.append((deplacementCol,deplacementLign))
            listeChemin.insert(0,(deplacementLign,deplacementCol))
        else :
            return (grille, listeChemin)
    return (grille, listeChemin)
    
def chercherNoeud(imat, tableau):
    for noeud in tableau:
        if noeud.get('immatriculation')==imat:
            return noeud
    return 0
           
def depilerPlusPetit(tableau):
    min = 10000000 #valur au hasard très grande, pour être sur que n'importe quel valeur de f sera plus petite !
    minNode = 0
    for noeud in tableau:#on récupère le noeud de plus petit f
        f = noeud.get('g')+noeud.get('h')
        if f < min :
            min = f
            minNode = noeud
    tableau.remove(minNode)
    return (minNode, tableau) #on 'dépile' l'élément du tableau et on le retourne, on retourne le tableau modifié dans le doute (pas sûr que ce soit du passage de référence en paramètre pour les tableaux)
    
def getIndice(noeudVoulu, tableau):# au cas où ça sert
    for i in range(len(tableau)):
        if tableau[i].get('immatriculation') == noeudVoulu.get('immatriculation'):
            return i
    return -1
    
def existeAvecCoutInf(noeud, tableau):
    for i in range(len(tableau)):
        if tableau[i].get('posX') == noeud.get('posX') and tableau[i].get('posY') == noeud.get('posY'):
            if tableau[i].get('g') < noeud.get('g'):
                return 1
    return -1
    
def heuristique(coord, but):
    return abs(coord[0]-but[0])+abs(coord[1]-but[1])
    
    
def voisins(noeud, coordBut, imatCount, grille):
    tailleV = len(grille)#taille verticale de la grille (nombre de lignes), vérifier que c'est bien les bonnes dimensions (pas inversées !)
    tailleH = len(grille[0])#taille horizontale de la grille(nombre de colonnes)
    butX= coordBut[0]
    butY = coordBut[1]
    posX= noeud.get('posX')
    posY=noeud.get('posY')
    nouveauxNoeuds = []
    g = noeud.get('g')
    imat_prov = noeud.get('immatriculation')
    #case du haut :
    if(posX>0 and (grille[posX-1][posY]==' ' or (posX-1==butX and posY==butY))):
        #case explorable
        h = heuristique([posX-1,posY], coordBut)+g+1 #l'heuristique du noeud vaut le coût du parent plus la distance au but
        caseHaut = {'posX':posX-1,'posY':posY, 'imat_provenance':imat_prov,'g':g+1, 'h':h,'immatriculation':imatCount}
        imatCount= imatCount+1
        nouveauxNoeuds.append(caseHaut)
    if(posX<tailleV-1 and (grille[posX+1][posY]==' ' or (posX+1==butX and posY==butY))):
        #case explorable
        h = heuristique([posX+1,posY], coordBut)+g+1
        caseBas = {'posX':posX+1,'posY':posY,'imat_provenance':imat_prov,'g':g+1,'h':h,'immatriculation':imatCount}
        imatCount= imatCount+1
        nouveauxNoeuds.append(caseBas)
    if(posY>0 and (grille[posX][posY-1]==' ' or (posX==butX and posY-1==butY))):
        #case explorable
        h = heuristique([posX,posY-1], coordBut)+g+1
        caseGauche = {'posX':posX,'posY':posY-1, 'imat_provenance':imat_prov,'g':g+1,'h':h,'immatriculation':imatCount}
        imatCount= imatCount+1
        nouveauxNoeuds.append(caseGauche)
    if(posY<tailleH-1 and (grille[posX][posY+1]==' ' or (posX==butX and posY+1==butY))):
        #case explorable
        h = heuristique([posX,posY+1], coordBut)+g+1
        caseDroite = {'posX':posX,'posY':posY+1, 'imat_provenance':imat_prov,'g':g+1,'h':h,'immatriculation':imatCount}
        imatCount= imatCount+1
        nouveauxNoeuds.append(caseDroite)
    return (nouveauxNoeuds, imatCount)

#
#grille = [[' ','#',' ',' ',' ',' '],[' ','#',' ',' ',' ',' '],[' ',' ',' ',' ','#',' '],['#','#','#',' ','#',' '],[' ','#','#',' ','#',' '],[' ',' ',' ',' ','#',' ']]
#print(grille)
#(chemin, listeChemin) = AETOILE([0,0], [5,0], grille)
#print(chemin)
#print (listeChemin)






# ---- ---- ---- ---- ---- ----
# ---- Main                ----
# ---- ---- ---- ---- ---- ----

game = Game()

def init(_boardname=None):
    global player,game, tailleV, tailleH
    name = _boardname if _boardname is not None else 'pathfindingWorld3'
    game = Game('Cartes/' + name + '.json', SpriteBuilder)
    game.O = Ontology(True, 'SpriteSheet-32x32/tiny_spritesheet_ontology.csv')
    game.populate_sprite_names(game.O)
    game.fps = 5  # frames per second
    game.mainiteration()
    player = game.player
    tailleV = game.spriteBuilder.rowsize
    tailleH = game.spriteBuilder.colsize
    
def main():
    
    #for arg in sys.argv:
#    iterations = 100 # default
#    if len(sys.argv) == 2:
#        iterations = int(sys.argv[1])
#    print ("Iterations: ")
#    print (iterations)

    init()
    
    #-------------------------------
    # Building the matrix
    #-------------------------------
    
           
    # on localise tous les états initiaux (loc du joueur)
    initStates = [o.get_rowcol() for o in game.layers['joueur']]
    print ("Init states:", initStates)
    
    # on localise tous les objets ramassables
    goalStates = [o.get_rowcol() for o in game.layers['ramassable']]
    print ("Goal states:", goalStates)
        
    # on localise tous les murs
    wallStates = [w.get_rowcol() for w in game.layers['obstacle']]
    #print ("Wall states:", wallStates)
    
    #on créé une grille vide :
    grille = []
    for i in range(tailleV):
        ligne = []
        for j in range(tailleH):
            ligne.append(' ')
        grille.append(ligne)
   
    
    #on ajoute les obstacles :
    
    for i in range(len(wallStates)):
        x= wallStates[i][0]
        y = wallStates[i][1]
        grille[x][y]='#'
    
    print(grille)
    #-------------------------------
    # Building the best path with A*
    #-------------------------------
    # print(initStates)
    (chemin, liste) = AETOILE(initStates[0], goalStates[0], grille)
    print(chemin)
    print(liste)
   
    #-------------------------------
    # Moving along the path
    #-------------------------------
        
    # bon ici on fait juste un random walker pour exemple...
    

    row,col = initStates[0]
    #row2,col2 = (5,5)

    for i in range(len(liste)):
        x_inc,y_inc = liste[i]# A*
        next_row = row+x_inc
        next_col = col+y_inc
        if ((next_row,next_col) not in wallStates) and next_row>=0 and next_row<=20 and next_col>=0 and next_col<=20:
            player.set_rowcol(next_row,next_col)
            print ("pos:",next_row,next_col)
            game.mainiteration()

            col=next_col
            row=next_row

            
        
            
        # si on a  trouvé l'objet on le ramasse
        if (row,col)==goalStates[0]:
            o = game.player.ramasse(game.layers)
            game.mainiteration()
            print ("Objet trouvé!", o)
            break
        '''
        #x,y = game.player.get_pos()
    
        '''
    
    pygame.quit()
    
        
    
   

if __name__ == '__main__':
    main()
    


