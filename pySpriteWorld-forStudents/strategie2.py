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
        if listeGoals[i] in  goalsDispo:
            goalsDispo.remove(listeGoals[i])
    goal = nearestGoal(coord, goalsDispo)
    if goal != -1:    
        return goal
    else:
        return -1
    
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
    name = _boardname if _boardname is not None else 'match'
    game = Game('Cartes/' + name + '.json', SpriteBuilder)
    game.O = Ontology(True, 'SpriteSheet-32x32/tiny_spritesheet_ontology.csv')
    game.populate_sprite_names(game.O)
    game.fps = 5  # frames per second
    game.mainiteration()
    game.mask.allow_overlaping_players = True
    tailleV = game.spriteBuilder.rowsize
    tailleH = game.spriteBuilder.colsize

def getGroupesCompat(wallStates, posPlayers, goalsPlayer):
    groupes = []
    trajets = []
    actions = []
    dureeGroupes = [] #longueur du plus long trajet du groupe
    dureeMaxGroupes = [] #longueur des plus longs trajets des groupes temporaire (avec le nouveau joueur)
    for player in range(len(posPlayers)):#pour chaque joueur
        addedToGroup = False
        createNewGroup = True
        if len(groupes)>0:#si on a au moins un groupe
            indiceMeilleur = -1
            meilleurTrajet = []
            meilleursActions = []
            for groupe in range(len(groupes)):
                print("groupe: "+str(groupe))
                wallsGroupe = wallStates[:]#on prend en compte les murs
                for playersInGroup in range(len(groupes[groupe])):
                    wallsGroupe += trajets[playersInGroup] #on ajoute le trajet des joueurs du groupe
                obstacles = getObstaclesGroupe(wallsGroupe, groupes, trajets,player, goalsPlayer, posPlayers)#on ajoute les positions finales des joueurs
                print("obstacles: ",obstacles)
                prob = Problem(posPlayers[player],goalsPlayer[player], obstacles, hauteur=20, largeur=20)# on cherche s'il existe un trajet compatible pour le joueur
                actionsPlayer, wayPlayer = astar(prob)
                if actionsPlayer != False and wayPlayer != False: #si le trajet du nouveau joueur n'est pas compatible
                    dureeMaxGroupes[groupe] = max(dureeGroupes[groupe], len(actionsPlayer))#on calcule la durée du groupe
                    indiceMin = groupe
                    ecartActuel = dureeMaxGroupes[groupe] - dureeGroupes[groupe]#ecart actuel au groupe
                    ecartMin = ecartActuel
                    for grp in range(len(groupes)) :
                        tempNew = dureeMaxGroupes[grp]
                        actualTime = dureeGroupes[grp]
                        ecartGroupe =  tempNew - actualTime
                        if ecartGroupe < ecartMin :
                            indiceMin = grp
                            ecartMin = ecartGroupe
                    if ecartActuel == ecartMin :   #si on a trouvé le meilleur groupe actuel, on le choisit  #len(actionsPlayer) < coutMeilleur : 
                        indiceMeilleur = groupe
                        # coutMeilleur = len(actionsPlayer)
                        meilleurTrajet = wayPlayer
                        meilleursActions = actionsPlayer
                        addedToGroup = True
            #on associe le joueur à ce groupe
            if addedToGroup :
                obstacles = getObstaclesGroupe(wallStates, groupes, trajets, player, goalsPlayer, posPlayers)
                print("obstacles: ",obstacles)
                prob = Problem(posPlayers[player],goalsPlayer[player], obstacles, hauteur=20, largeur=20)# on cherche s'il existe un trajet compatible pour le joueur
                actionsPlayer, wayPlayer = astar(prob)
                ecartGroupe = dureeMaxGroupes[indiceMeilleur] - dureeGroupes[indiceMeilleur]
                ecartSeul = len(actionsPlayer) 
                if ecartSeul < ecartGroupe :
                    #créer un nouveau groupe
                    createNewGroup = True
                else:
                    createNewGroup = False
                    (groupes, trajets, actions) = ajoutGroupe(groupes, indiceMeilleur, player, trajets, actions, meilleurTrajet, meilleursActions)
                    if dureeGroupes[groupe] < len(actionsPlayer):
                        dureeGroupes[groupe] = len(actionsPlayer)
                        dureeMaxGroupes[groupe] = len(actionsPlayer)
            
        if len(groupes)==0 or createNewGroup == True:
            #on créé d'office un groupe avec ce joueur
            obstacles = getObstaclesGroupe(wallStates, groupes, trajets,player, goalsPlayer, posPlayers)
            print("obstacles: ",obstacles)
            prob = Problem(posPlayers[player],goalsPlayer[player], obstacles, hauteur=20, largeur=20)# on cherche s'il existe un trajet compatible pour le joueur
            actionsPlayer, wayPlayer = astar(prob)
            groupes = createGroup(player, groupes)
            trajets.append(wayPlayer)
            actions.append(actionsPlayer)#on mémorise le trajet du nouveau joueur 
            dureeGroupes.append(len(actionsPlayer))
            dureeMaxGroupes.append(len(actionsPlayer))
    return groupes, trajets, actions

def ajoutGroupe(groupes, indice, player, trajets, actions, trajetP, actionsP):
    groupes[indice].append(player)
    trajets.append(trajetP)#on mémorise le trajet du nouveau joueur
    actions.append(actionsP)
    return (groupes, trajets, actions)
    

def createGroup(player, groupes):
    newGroup = []
    newGroup.append(player)
    groupes.append(newGroup)#on créé un nouveau groupe
    return groupes
    
def getObstaclesGroupe(wallStates, groupes, trajets, player, goalsPlayers, posPlayers):
    obstacles = wallStates[:]
    for groupe in range(len(groupes)):
        for playersInGroup in range(len(groupes[groupe])):
            obstacles.append(trajets[playersInGroup][len(trajets[playersInGroup])-1])#on considère comme obstacle les cases où les joueurs finissent leur trajet
    for players in range(len(goalsPlayers)): #on considère aussi les buts des autres joueurs comme obstacles avant même que leur trajet soit prévu
        if players != player:
            obstacles.append(goalsPlayers[players])
    for players in range(len(goalsPlayers)): #on considère aussi les positions de départ comme des obstacles (si on joue avant un autre joueur)
        if players != player:
            obstacles.append(goalsPlayers[players])
            obstacles.append(posPlayers[players])
    return obstacles
    
def groupeEnded(actualGroupe, groupes, finished):
    for joueur in groupes[actualGroupe] :
        if joueur not in finished:
            return False
    return True
  
    
def main():

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
    
    #on met à jour dans la liste :
    goalStates = [o.get_rowcol() for o in game.layers['ramassable']]
    print ("Goal states:", goalStates)

    
    goalsPlayer = []
    actualGroup = 0 #le groupe qu'on fait bouger
    posPlayers = initStates
    etapeTrajet = []#on stoque l'itération en cours du trajet de chaque joueur
    listFinish = []#la liste des joueurs ayant fini leur trajet, pour savoir quand faire passer les autres.
    for k in range(nbPlayers):
        goalK = randDispo(posPlayers[k], goalStates, goalsPlayer)# ON DEFINI LA FIOLE CIBLEE INITIALE
        goalsPlayer.append(goalK)
        etapeTrajet.append(0)
    groupes, trajets, actions = getGroupesCompat(wallStates, posPlayers, goalsPlayer)
    print(groupes)
    print(trajets)
    
    for i in range(iterations):
        if groupeEnded(actualGroup, groupes, listFinish):#si on a terminé le groupe actuel
            print("groupe "+str(actualGroup)+" terminé")
            if actualGroup < len(groupes)-1 :#on passe au groupe suivant s'il y en a un
                actualGroup += 1
                print("groupe "+str(actualGroup)+" commence")
            else:#on termine le programme sinon
                print ("scores:", score)
                print("iterations:",  i)
                break
        for j in range(nbPlayers): # on fait bouger chaque joueur séquentiellement
            if j not in listFinish and j in groupes[actualGroup]: #ON FAIT BOUGER TOUS LES JOUEURS QUI NE SE GENENT PAS DANS LEURS TRAJETS
                row,col = posPlayers[j]
                if (row,col) == goalsPlayer[j] and goalsPlayer[j] in goalStates:# si on a  trouvé la fiole voulue, on la ramasse
                    print ("Objet trouvé par le joueur ", j)
                    o = players[j].ramasse(game.layers)
                    goalStates.remove((row,col)) # on enlève ce goalState de la liste
                    score[j]+=1
                    listFinish.append(j)
                else:
                    if(len(actions[j])>etapeTrajet[j]):
                        x_inc,y_inc = actions[j][etapeTrajet[j]]   
                        etapeTrajet[j] = etapeTrajet[j]+1
                        next_row = row+x_inc
                        next_col = col+y_inc
                        players[j].set_rowcol(next_row,next_col)
                        posPlayers[j]=(next_row,next_col)
                    else:
                        print ("trajet terminé")
                        listFinish.append(j)
        game.mainiteration()
    pygame.quit()

if __name__ == '__main__':
    main()
    


