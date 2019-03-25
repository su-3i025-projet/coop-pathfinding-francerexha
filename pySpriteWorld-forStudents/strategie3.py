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
import heapq
import glo

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
        if listeGoals[i] in goalsDispo:
            goalsDispo.remove(listeGoals[i])
    return nearestGoal(coord, goalsDispo)
    
def randDispo(coord, listeFioles, listeGoals):
    done = []
    while len(done)<len(listeFioles):
        x = random.randint(0,len(listeFioles)-1)
        if x not in done :
            done.append(x)
            if listeFioles[x] not in listeGoals:
                return listeFioles[x]
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
    
class ReservationTable(): 
     
    def __init__(self, largeur, hauteur, time):
        self.largeur=largeur
        self.hauteur=hauteur
        self.time=time
        self.locked=np.zeros((largeur,hauteur,time),dtype=bool) # [0,0,0]   
        
    def is_Blocked(self,l ,h, t):
        return self.locked[l][h][t]
    
    def checkAvailableCase(self,l, h, t):
        if(l>=0 and l<self.largeur and h>=0 and h<self.hauteur and t>=0 and t<self.time) and self.locked[l][h][t]==False:
            return True
        return False
    
    def block_the_Case(self,l,h,t):
        if self.checkAvailableCase(l, h, t)==True:
            self.locked[l][h][t]=True
            
    def block_forever(self, l, h, t):
        if self.checkAvailableCase(l, h, t)==True:
            print("case ("+str(l)+","+str(h)+") bloquée à partir de "+str(t))
            for t2 in range(t,self.time) :
                self.locked[l][h][t2]=True
                
    def checkAvailableCaseForever(self,l, h, t):
        if self.checkAvailableCase(l, h, t) :
            for t2 in range(t,self.time) :
                if self.is_Blocked(l ,h, t2):
                    return False
        return True
    
    def searchNearestStayPlace(self,l, h, t, wallStates):
        for (x,y) in [(0,1),(1,0),(0,-1),(-1,0)]:
            if (l+x, h+y) not in wallStates and self.checkAvailableCaseForever(l+x, h+y, t)==True:
                return (l+x, h+y), (x,y) #case, action
        return False, False
                

def getTrajetsCompat(wallStates, posPlayers, goalsPlayer):
    tableResa = ReservationTable(tailleH,tailleV,iterations)
    trajets = []
    actions = []
    ordreJoueurs = []     
    for k in range(len(posPlayers)):#pour chaque joueur
        player = k
        ordreJoueurs.append(player)
        trajetTrouve = False
        casesCollisions = []
        actionsPlayer = []
        wayPlayer = []
        while trajetTrouve==False :
            wallsGroupe = wallStates[:]#on prend en compte les murs
            wallsGroupe += casesCollisions
            prob = Problem(posPlayers[player],goalsPlayer[player], wallsGroupe, hauteur=20, largeur=20)
            actionsPlayer, wayPlayer = astar(prob)
            if actionsPlayer != False and wayPlayer !=False:
                print("solution Astar trouvée joueur "+str(player))
                trajetTrouve = True
                for i in range(len(wayPlayer)):
                    case = wayPlayer[i]
                    if tableResa.checkAvailableCase(case[0],case[1], i)==False :
                        print("case ("+str(case[0])+","+str(case[1])+","+str(i)+") occupée")
                        trajetTrouve = False
                        casesCollisions.append(case)
                    else:#on vérifie qu'il n'y a pas de croisement de face
                        for j in range(len(trajets)):
                            if len(trajets[j])>i+1:
                                if trajets[j][i-1]==wayPlayer[i] and trajets[j][i]==wayPlayer[i-1]: #s'il y a un croisement
                                    print("case ("+str(case[0])+","+str(case[1])+","+str(i)+") croisement")
                                    trajetTrouve = False
                                    casesCollisions.append(case)
            else:
                print("pas de solution")
        print("longeur trajet :"+str(len(wayPlayer)))
        if len(wayPlayer)==0:
            wayPlayer.append(posPlayers[k])#on considère qu'il a un trajet de taille 1 avec un mouvement sur place (evite les OOBE)
            actionsPlayer.append((0,0))
        for i in range(len(wayPlayer)-1):#on réserve les cases, sauf la dernière qui sera bloquée pour de bon après 
            case = wayPlayer[i]
            tableResa.block_the_Case(case[0],case[1],i)
        if(tableResa.checkAvailableCaseForever(wayPlayer[len(wayPlayer)-1][0], wayPlayer[len(wayPlayer)-1][1], len(wayPlayer)-1)):
            print("le joueur reste sur place")
            tableResa.block_forever(wayPlayer[len(wayPlayer)-1][0], wayPlayer[len(wayPlayer)-1][1], len(wayPlayer)-1)#on vérouille jusqu'à la fin la case sur laquelle le joueur reste
        else:
            print("le joueur ne peut pas rester sur cette case: ("+str(wayPlayer[len(wayPlayer)-1][0])+","+str(wayPlayer[len(wayPlayer)-1][1])+")")
            tableResa.block_the_Case(wayPlayer[len(wayPlayer)-1][0], wayPlayer[len(wayPlayer)-1][1], len(wayPlayer)-1)#on bloque à l'instant où on va sur la case
            wallsGroupe = wallStates[:]#on prend en compte les murs
            wallsGroupe += casesCollisions
            case ,action =  tableResa.searchNearestStayPlace(wayPlayer[len(wayPlayer)-1][0], wayPlayer[len(wayPlayer)-1][1], len(wayPlayer),wallsGroupe)
            if case!=False and action!=False:
                #alors on a une case voisine qu'on peut bloquer éternellement sans gêner
                wayPlayer.append(case)
                actionsPlayer.append(action)
                tableResa.block_forever(case[0],case[1], len(wayPlayer)-1)#on se met sur la case voisine sur laqeulle on peut rester
                print("le joueur se décale en ("+str(case[0])+","+str(case[1])+") pour ne pas gêner")
        trajets.append(wayPlayer)
        actions.append(actionsPlayer)
    return ordreJoueurs, trajets, actions
        
def main():
    global iterations
    #for arg in sys.argv:
    iterations = 100 # default
    if len(sys.argv) == 2:
        iterations = int(sys.argv[1])
    print ("Iterations: ")
    print (iterations)

    init("pathfindingWorld_MultiPlayer4")
    
    #-------------------------------
    # Initialisation
    #-------------------------------
       
    players = [o for o in game.layers['joueur']]
    nbPlayers = len(players)
    score = [0]*nbPlayers
    
    # on localise tous les états initiaux (loc du joueur)
    initStates = [o.get_rowcol() for o in game.layers['joueur']]
    print ("Init states:", initStates)

    # on localise tous les murs
    wallStates = [w.get_rowcol() for w in game.layers['obstacle']]
    
    #-------------------------------
    # Placement aleatoire des fioles de couleur 
    #-------------------------------
    
    goalStates = []
    for o in game.layers['ramassable']: # les rouges puis jaunes puis bleues
    # et on met la fiole qqpart au hasard
        x = random.randint(1,19)
        y = random.randint(1,19)
        while (x,y) in wallStates or (x,y) in goalStates:
            x = random.randint(1,19)
            y = random.randint(1,19)
        o.set_rowcol(x,y)
        goalStates.append((x,y))
        game.layers['ramassable'].add(o)
        game.mainiteration()                           

    print(game.layers['ramassable'])
    print ("Goal states:", goalStates)
    
    goalsPlayer = []
    posPlayers = initStates
    etapeTrajet = []#on stoque l'itération en cours du trajet de chaque joueur
    listFinish = []#la liste des joueurs ayant fini leur trajet, pour savoir quand faire passer les autres.
    for k in range(nbPlayers):
        goalK = randDispo(posPlayers[k], goalStates, goalsPlayer) #nearestDispo(posPlayers[k], goalStates, goalsPlayer)
        goalsPlayer.append(goalK)
        etapeTrajet.append(0)
    ordreJoueurs, trajets, actions = getTrajetsCompat(wallStates, posPlayers, goalsPlayer)
    print(trajets)
    for i in range(iterations):
        if len(listFinish) == nbPlayers:
            print("iterations:",  i)
            break
        for j in range(nbPlayers): # on fait bouger chaque joueur
            if j not in listFinish: 
                row,col = posPlayers[j]
                if (row,col) == goalsPlayer[j] and goalsPlayer[j] in goalStates:# si on a  trouvé la fiole voulue, on la ramasse
                    print ("Objet trouvé par le joueur ", j)
                    o = players[j].ramasse(game.layers)
                    goalStates.remove((row,col)) # on enlève ce goalState de la liste
                    score[j]+=1
                else:
                    if(len(actions[j])>etapeTrajet[j]):
                        x_inc,y_inc = actions[j][etapeTrajet[j]]   
                        next_row = row+x_inc
                        next_col = col+y_inc
                        players[j].set_rowcol(next_row,next_col)
                        posPlayers[j]=(next_row,next_col)
                        etapeTrajet[j] = etapeTrajet[j]+1 
                    else:
                        print ("trajet terminé")
                        listFinish.append(j)
        game.mainiteration()
    pygame.quit()


if __name__ == '__main__':
    main()
    


