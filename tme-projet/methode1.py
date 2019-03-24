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

class Node():
    
    def __init__(self, coord, g, father):
        self.x = coord[0]
        self.y = coord[1]
        self.g=g
        self.father=father
        
    def expand(self, p):
        l=[]
        for i in [(0,1),(1,0),(0,-1),(-1,0)]:
            if(p.notWall((self.x+i[0],self.y+i[1]))):
                l.append(Node((self.x+i[0], self.y+i[1]), self.g+1, self))
        return l
    
    def backWay(self):
        actions=[]
        way=[]
        while(self.father!=None):#Tant que je ne suis pas la racine
            actions.insert(0, (self.x-self.father.x, self.y-self.father.y))
            way.insert(0, (self.x, self.y))
            self=self.father
        return actions, way
    
    def __lt__(self, other):
        return True
    
    def __str__(self):
        return "("+str(self.x)+","+str(self.y)+")"
    

class Problem():
    
    def __init__(self, init, goal, wallStates, hauteur=20, largeur=20):
        self.init=init
        self.goal = goal
        self.wallStates=wallStates
        self.hauteur=hauteur
        self.largeur=largeur
        
    def isGoal(self, pos):
        return pos==self.goal
    
    def notWall(self, pos):
        return pos[0]>=0 and pos[0]<self.largeur and pos[1]>=0 and pos[1]<self.hauteur and pos not in self.wallStates
  
    
def heuristique(coord, goal):
        return abs(coord[0]-goal[0])+abs(coord[1]-goal[1])
    
def astar(p):
    nodeInit = Node(p.init,0,None)
    frontiere = [(nodeInit.g+heuristique((nodeInit.x, nodeInit.y),p.goal),nodeInit)] 
    reserve = {}        
    bestNoeud = nodeInit
    
    while frontiere != [] and not p.isGoal((bestNoeud.x, bestNoeud.y)):
        
        (min_f,bestNoeud) = heapq.heappop(frontiere)         
    # Suppose qu'un noeud en réserve n'est jamais ré-étendu 
    # Hypothèse de consistence de l'heuristique
    # ne gère pas les duplicatas dans la frontière
    
        if (bestNoeud.x, bestNoeud.y) not in reserve:            
            reserve[(bestNoeud.x, bestNoeud.y)] = bestNoeud.g #maj de reserve
            nouveauxNoeuds = bestNoeud.expand(p)            
            for n in nouveauxNoeuds:
                f = n.g+heuristique((n.x, n.y),p.goal)
                heapq.heappush(frontiere, (f,n))       
                
    # Afficher le résultat                 
    if(not p.isGoal((bestNoeud.x, bestNoeud.y))):
        return False , False
    else:
        return bestNoeud.backWay()
    

def printFrontiere(frontiere):
    st="["
    for e in frontiere:
        f,n=e
        st+="("+str(f)+","+str(n)+")"
    st+="]"
    return st


def nearestGoal(coord,liste):
    nearest = 10000
    idNear = -1
    for i in range(len(liste)):
        h = heuristique(coord, liste[i])
        if h < nearest :
            idNear = i
            nearest = h
    if idNear > -1:
        return liste[idNear]
    else:
        return -1
    
def nearestDispo(coord, listeFioles, listeGoals):
    goalsDispo = listeFioles[:]
    for i in range(len(listeGoals)):
        if listeGoals[i] in  goalsDispo:
            goalsDispo.remove(listeGoals[i])
    goal = nearestGoal(coord, goalsDispo)
    if goal != -1:    
        return goal
    else:
        return -1
# ---- ---- ---- ---- ---- ----
# ---- Main                ----
# ---- ---- ---- ---- ---- ----
    
    
game = Game()

def init(_boardname=None):
    global player,game, tailleV, tailleH
    # pathfindingWorld_MultiPlayer4
    name = _boardname if _boardname is not None else 'match'
    game = Game('Cartes/' + name + '.json', SpriteBuilder)
    game.O = Ontology(True, 'SpriteSheet-32x32/tiny_spritesheet_ontology.csv')
    game.populate_sprite_names(game.O)
    game.fps = 5  # frames per second
    game.mainiteration()
    game.mask.allow_overlaping_players = True
    tailleV = game.spriteBuilder.rowsize
    tailleH = game.spriteBuilder.colsize
    #player = game.player
    
def main():

    #for arg in sys.argv:
    iterations = 100 # default
    if len(sys.argv) == 2:
        iterations = int(sys.argv[1])
    print ("Iterations: ")
    print (iterations)

    init()

    #-------------------------------
    # Initialisation
    #-------------------------------
       
    players = [o for o in game.layers['joueur']]
    nbPlayers = len(players)
    score = [0]*nbPlayers
    
    
    # on localise tous les états initiaux (loc du joueur)
    initStates = [o.get_rowcol() for o in game.layers['joueur']]
    print ("Init states:", initStates)
    
    
    # on localise tous les objets ramassables
    goalStates = [o.get_rowcol() for o in game.layers['ramassable']]
    print ("Goal states:", goalStates)
        
    # on localise tous les murs
    wallStates = [w.get_rowcol() for w in game.layers['obstacle']]
    #print ("Wall states:", wallStates)
    
    #-------------------------------
    # Placement aleatoire des fioles de couleur 
    #-------------------------------
    
    for o in game.layers['ramassable']: # les rouges puis jaunes puis bleues
    # et on met la fiole qqpart au hasard
        x = random.randint(1,19)
        y = random.randint(1,19)
        while (x,y) in wallStates:
            x = random.randint(1,19)
            y = random.randint(1,19)
        o.set_rowcol(x,y)
        game.layers['ramassable'].add(o)
        game.mainiteration()                

    print(game.layers['ramassable'])
    
    #on met à jour dans la liste :
    goalStates = [o.get_rowcol() for o in game.layers['ramassable']]
    print ("Goal states:", goalStates)

    
    
    #-------------------------------
    # Boucle principale de déplacements 
    #-------------------------------
    etapeTrajet = []#on stoque l'itération en cours du trajet de chaque joueur
    posPlayers = initStates
    trajetPlayers = []
    goalsPlayer = []#liste des coordonnées du but de chaque joueur
    for k in range(nbPlayers):
        etapeTrajet.append(0)
        #goalK = goalStates[k]#On attribue une fiole à chaque joueur
        #goalK = nearestGoal(posPlayers[k],goalStates) #basé sur la fiole la plus proche de chacun
        goalK = nearestDispo(posPlayers[k], goalStates, goalsPlayer)#pour pas que 2 aient la même fiole
        goalsPlayer.append(goalK)
        prob = Problem(posPlayers[k],goalK, wallStates, hauteur=20, largeur=20)
        trajet, way = astar(prob)
        print ("Trajet OK pour le joueur ", k)
        trajetPlayers.append(trajet)#on sauvegarde le trajet prévu
        #on cherche un trajet initial, on regardera après s'il y a des croisements
    
    listFinish = []
    for i in range(iterations):
        
        for j in range(nbPlayers): # on fait bouger chaque joueur séquentiellement
            if j not in listFinish:
                row,col = posPlayers[j]
                ###print("Pos ",j, ":", row, col)
                ###print("goalX ",j, ":", goalsPlayer[j])
                if (row,col) == goalsPlayer[j] and goalsPlayer[j] in goalStates:# si on a  trouvé la fiole voulue, on la ramasse
                    print ("Objet trouvé par le joueur ", j)
                    o = players[j].ramasse(game.layers)
                    game.mainiteration()
                    goalStates.remove((row,col)) # on enlève ce goalState de la liste
                    score[j]+=1
                    #on définit le nouvel objectif (une autre fiole) :
                    """goalK = nearestDispo((row,col), goalStates, goalsPlayer)#pour pas que 2 aient la même fiole, on prend la plus proche dispo
                    # goalK = nearestGoal((row,col),goalStates) #basé sur la fiole la plus proche de chacun
                    if goalK != -1:
                        print("NEW GOAL: ", goalK)
                        goalsPlayer[j]= goalK
                        prob = Problem((row,col),goalK, wallStates, hauteur=20, largeur=20)
                        trajet, way = astar(prob)
                        print ("Trajet OK pour le joueur ", k)
                        trajetPlayers[j] = trajet  #on supprime l'ancien trajet
                        etapeTrajet[j] = 0 #on place le curseur au début du nouveau trajet
                    else:
                        #pas de fiole restante à récolter
                        print ("plus de fiole dispo pour "+str(j))"""
                    listFinish.append(j)
                    #break
                else:
                    ###print ("deplacement")
                    #on effectue le mouvement suivant s'il n'y a pas de joueur qui nous en empêche (sur la case destination)
                    if(len(trajetPlayers[j])>etapeTrajet[j]):
                        x_inc,y_inc = trajetPlayers[j][etapeTrajet[j]]   
                        etapeTrajet[j] = etapeTrajet[j]+1
                        next_row = row+x_inc
                        next_col = col+y_inc
                        notMoved = True
                        while(notMoved):#on actualise le chemin si besoin jusqu'à pouvoir faire un mouvement valide :  ESQUIVE DES JOUEURS
                            if ((next_row,next_col) not in wallStates) and ((next_row,next_col) not in posPlayers) and next_row>=0 and next_row<=19 and next_col>=0 and next_col<=19:
                                players[j].set_rowcol(next_row,next_col)
                                ###print ("pos :", j, next_row,next_col)
                                game.mainiteration()
                                posPlayers[j]=(next_row,next_col)
                                notMoved = False
                            else:
                                #si il y a un joueur sur la case, on cherche un autre itinéraire:
                                #on relance A étoile en considérant cette case comme un obstacle
                                print ("Obstacle pos:",next_row,next_col)
                                tempWallStates = wallStates[:]
                                tempWallStates.append((next_row,next_col))
                                prob = Problem(posPlayers[j],goalsPlayer[j], tempWallStates, hauteur=20, largeur=20)
                                trajet, way = astar(prob)
                                #on remplace l'ancien trajet par le nouveau
                                trajetPlayers[j] = trajet  #on supprime l'ancien trajet
                                etapeTrajet[j] = 0 #on place le curseur au début du nouveau trajet
                                x_inc,y_inc = trajetPlayers[j][etapeTrajet[j]]   #on prépare le 1er déplacement
                                etapeTrajet[j] = etapeTrajet[j]+1        
                                next_row = row+x_inc
                                next_col = col+y_inc
                    else:
                        print ("trajet de "+str(j)+ "terminé")
                        listFinish.append(j)

    print ("scores:", score)
    pygame.quit()
    
        
    
   

if __name__ == '__main__':
    main()
    


