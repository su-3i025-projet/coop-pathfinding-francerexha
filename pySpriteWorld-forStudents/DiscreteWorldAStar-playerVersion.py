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


class Node():
    
    def __init__(self, coord, g, father):
        self.x = coord[0]
        self.y = coord[1]
        self.g=g
        self.father=father
        
    def expand(self, p):
        """retourne l'ensemble des noeuds fils"""
        l=[]
        for i in [(0,1),(1,0),(0,-1),(-1,0)]:
            if(p.notWall((self.x+i[0],self.y+i[1]))):
                l.append(Node((self.x+i[0], self.y+i[1]), self.g+1, self))
        return l
    
    def backWay(self):
        """
        Retourne la liste des couples d'actions à effectuer dans l'ordre depuis le départ
        """
        actions=[]
        way=[]
        while(self.father!=None):#Tant que je ne suis pas la racine
            actions.insert(0, (self.x-self.father.x, self.y-self.father.y))
            way.insert(0, (self.x, self.y))
            self=self.father
        
        """
        while(self.father!=None):#Tant que je ne suis pas la racine
            l.insert(0, self.etat)
            self=self.father
        """
        return actions, way
    
    def __lt__(self, other):
        return True
    
    def __str__(self):
        return "("+str(self.x)+","+str(self.y)+")"
    

class Problem():
    
    def __init__(self, init, goal, wallStates, hauteur=20, largeur=20):
        """
        depart et but son des couples (coordonnées)
        """
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
        return False
    else:
        return bestNoeud.backWay()
    

def printFrontiere(frontiere):
    st="["
    for e in frontiere:
        f,n=e
        st+="("+str(f)+","+str(n)+")"
    st+="]"
    return st







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
    
    #-------------------------------
    # Building the best path with A*
    #-------------------------------
    # print(initStates)
    prob = Problem(initStates[0],goalStates[0], wallStates, hauteur=20, largeur=20)
    actions, way = astar(prob)
    print(actions)
    print(way)
   
    #-------------------------------
    # Moving along the path
    #-------------------------------
       
    row,col = initStates[0]
    #row2,col2 = (5,5)

    for i in range(len(actions)):
        x_inc,y_inc = actions[i]# A*
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
    


