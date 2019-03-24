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
    
def getGroupesCompat(wallStates, posPlayers, goalsPlayer):
    groupes = []
    trajets = []
    actions = []
    for player in range(len(posPlayers)):#pour chaque joueur
        addedToGroup = False
        if len(groupes)>0:#si on a au moins un groupe
            for groupe in range(len(groupes)):
                print("groupe: "+str(groupe))
                wallsGroupe = wallStates[:]#on prend en compte les murs
                for playersInGroup in range(len(groupes[groupe])):
                    wallsGroupe += trajets[playersInGroup] #on ajoute le trajet des joueurs du groupe
                prob = Problem(posPlayers[player],goalsPlayer[player], wallsGroupe, hauteur=20, largeur=20)# on cherche s'il existe un trajet compatible pour le joueur
                actionsPlayer, wayPlayer = astar(prob)
                if actionsPlayer != False and wayPlayer != False: #si le trajet du nouveau joueur n'est pas compatible
                    #on associe le joueur à ce groupe
                    groupes[groupe].append(player)
                    trajets.append(wayPlayer)#on mémorise le trajet du nouveau joueur
                    actions.append(actionsPlayer)
                    addedToGroup = True
                    break
                #sinon on continue de chercher dans les autres groupes    
        if len(groupes)==0 or addedToGroup == False:
            #on créé d'office un groupe avec ce joueur
            prob = Problem(posPlayers[player],goalsPlayer[player], wallStates, hauteur=20, largeur=20)# on cherche s'il existe un trajet compatible pour le joueur
            actionsPlayer, wayPlayer = astar(prob)
            newGroup = []
            newGroup.append(player)
            groupes.append(newGroup)#on créé un nouveau groupe
            trajets.append(wayPlayer)
            actions.append(actionsPlayer)#on mémorise le trajet du nouveau joueur  
    return groupes, trajets, actions

def getGroupesCompat2(wallStates, posPlayers, goalsPlayer):
    groupes = []
    trajets = []
    actions = []
    dureeGroupes = [] #longueur du plus long trajet du groupe
    dureeMaxGroupes = [] #longueur des plus longs trajets des groupes temporaire (avec le nouveau joueur)
    for player in range(len(posPlayers)):#pour chaque joueur
        addedToGroup = False
        createNewGroup = True
        if len(groupes)>0:#si on a au moins un groupe
            #coutMeilleur = 1000000000
            indiceMeilleur = -1
            meilleurTrajet = []
            meilleursActions = []
            for groupe in range(len(groupes)):
                print("groupe: "+str(groupe))
                wallsGroupe = wallStates[:]#on prend en compte les murs
                for playersInGroup in range(len(groupes[groupe])):
                    wallsGroupe += trajets[playersInGroup] #on ajoute le trajet des joueurs du groupe
                prob = Problem(posPlayers[player],goalsPlayer[player], wallsGroupe, hauteur=20, largeur=20)# on cherche s'il existe un trajet compatible pour le joueur
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
                prob = Problem(posPlayers[player],goalsPlayer[player], wallStates, hauteur=20, largeur=20)# on cherche s'il existe un trajet compatible pour le joueur
                actionsPlayer, wayPlayer = astar(prob)
                ecartGroupe = dureeMaxGroupes[indiceMeilleur] - dureeGroupes[indiceMeilleur]
                ecartSeul = len(actionsPlayer) 
                if ecartSeul < ecartGroupe :
                    #créer un nouveau groupe
                    createNewGroup = True
                else:
                    createNewGroup = False
                    groupes[indiceMeilleur].append(player)
                    trajets.append(meilleurTrajet)#on mémorise le trajet du nouveau joueur
                    actions.append(meilleursActions)
                    if dureeGroupes[groupe] < len(actionsPlayer):
                        dureeGroupes[groupe] = len(actionsPlayer)
                        dureeMaxGroupes[groupe] = len(actionsPlayer)
            
        if len(groupes)==0 or createNewGroup == True:
            #on créé d'office un groupe avec ce joueur
            prob = Problem(posPlayers[player],goalsPlayer[player], wallStates, hauteur=20, largeur=20)# on cherche s'il existe un trajet compatible pour le joueur
            actionsPlayer, wayPlayer = astar(prob)
            newGroup = []
            newGroup.append(player)
            groupes.append(newGroup)#on créé un nouveau groupe
            trajets.append(wayPlayer)
            actions.append(actionsPlayer)#on mémorise le trajet du nouveau joueur 
            dureeGroupes.append(len(actionsPlayer))
            dureeMaxGroupes.append(len(actionsPlayer))
    return groupes, trajets, actions
    
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

    init("match")
    
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

    
    #NOUVELLE VERSION AVEC GROUPES COMPATIBLES  :
    
    goalsPlayer = []
    actualGroup = 0 #le groupe qu'on fait bouger
    posPlayers = initStates
    etapeTrajet = []#on stoque l'itération en cours du trajet de chaque joueur
    listFinish = []#la liste des joueurs ayant fini leur trajet, pour savoir quand faire passer les autres.
    for k in range(nbPlayers):
        goalK = nearestDispo(posPlayers[k], goalStates, goalsPlayer)# ON DEFINI LA FIOLE CIBLEE INITIALE
        goalsPlayer.append(goalK)
        etapeTrajet.append(0)
    groupes, trajets, actions = getGroupesCompat2(wallStates, posPlayers, goalsPlayer)
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
                break
        for j in range(nbPlayers): # on fait bouger chaque joueur séquentiellement
            if j not in listFinish and j in groupes[actualGroup]: #ON FAIT BOUGER TOUS LES JOUEURS QUI NE SE GENENT PAS DANS LEURS TRAJETS
                row,col = posPlayers[j]
                if (row,col) == goalsPlayer[j] and goalsPlayer[j] in goalStates:# si on a  trouvé la fiole voulue, on la ramasse
                    print ("Objet trouvé par le joueur ", j)
                    o = players[j].ramasse(game.layers)
                    game.mainiteration()
                    goalStates.remove((row,col)) # on enlève ce goalState de la liste
                    score[j]+=1
                    listFinish.append(j)
                else:
                    #on effectue le mouvement suivant s'il n'y a pas de joueur qui nous en empêche (sur la case destination)
                    if(len(actions[j])>etapeTrajet[j]):
                        x_inc,y_inc = actions[j][etapeTrajet[j]]   
                        etapeTrajet[j] = etapeTrajet[j]+1
                        next_row = row+x_inc
                        next_col = col+y_inc
                        players[j].set_rowcol(next_row,next_col)
                        game.mainiteration()
                        posPlayers[j]=(next_row,next_col)
                        
                    else:
                        print ("trajet terminé")
                        listFinish.append(j)
    pygame.quit()
    """
    #-------------------------------
    # Boucle principale de déplacements 
    #-------------------------------
    wallJoueurs = []
    etapeTrajet = []#on stoque l'itération en cours du trajet de chaque joueur
    posPlayers = initStates
    trajetPlayers = []
    goalsPlayer = []#liste des coordonnées du but de chaque joueur
    ordrePassage = [] #liste contenant les joueurs n'ayant pas de trajets compatibles, et devant passer les uns après les autres
    
    for k in range(nbPlayers): #ON INITIALISE LES OBJECTIFS ET LES TRAJETS
        etapeTrajet.append(0)
        wallJoueurs.append([])
        tempWalls = wallStates[:]#on prend en compte les murs
        for z in range(k):
            for t in range(len(wallJoueurs[z])):
                tempWalls.append(wallJoueurs[z][t])#on prend en compte le trajet de tous les autres joueurs
        print("Obstacles total : ")
        print (tempWalls)  
        goalK = nearestDispo(posPlayers[k], goalStates, goalsPlayer)# ON DEFINI LA FIOLE CIBLEE INITIALE
        goalsPlayer.append(goalK)
        prob = Problem(posPlayers[k],goalK, tempWalls, hauteur=20, largeur=20)
        actions, way = astar(prob)
        if actions == False and way == False : #Si il n'y a pas de trajet compatible pour ce joueur
            ordrePassage.append(k)#on marque ce joueur comme devant passer après les autres
            goalsPlayer.append(goalK)
            prob = Problem(posPlayers[k],goalK, wallStates, hauteur=20, largeur=20) #on relance Astar mais sans prendre en compte le trajet des autres joueurs
            actions, way = astar(prob)
            print("le joueur"+str(k)+" jouera après les autres")
        tempPos = posPlayers[k]
        print(tempPos)
        for u in range(len(actions)): #on considère ce trajet comme un obstacle pour les autres joueurs
            tempPosX = tempPos[0] + actions[u][0]
            tempPosY = tempPos[1] + actions[u][1]
            tempPos = (tempPosX, tempPosY)
            wallJoueurs[k].append(tempPos)
            print(tempPos)
        print ("Murs trajet", str(wallJoueurs[k]))
        trajetPlayers.append(actions)#on sauvegarde le trajet prévu
        print ("Trajet OK pour le joueur ", k)    
        #on ne garde que les trajets n'ayant pas de cases en commun :
    
    
    listFinish = []#la liste des joueurs ayant fini leur trajet, pour savoir quand faire passer les autres.
    for i in range(iterations):
        if len(listFinish) < nbPlayers - len(ordrePassage):# SI TOUS LES JOUEURS NE SE GENANT PAS ONT FINI DE JOUER
            for j in range(nbPlayers): # on fait bouger chaque joueur séquentiellement
                if j not in ordrePassage and j not in listFinish: #ON FAIT BOUGER TOUS LES JOUEURS QUI NE SE GENENT PAS DANS LEURS TRAJETS
                    row,col = posPlayers[j]
                    ###print("Pos ",j, ":", row, col)
                    ###print("goalX ",j, ":", goalsPlayer[j])
                    if (row,col) == goalsPlayer[j] and goalsPlayer[j] in goalStates:# si on a  trouvé la fiole voulue, on la ramasse
                        print ("Objet trouvé par le joueur ", j)
                        o = players[j].ramasse(game.layers)
                        game.mainiteration()
                        goalStates.remove((row,col)) # on enlève ce goalState de la liste
                        score[j]+=1
                        listFinish.append(j)
                    else:
                        ###print ("deplacement")
                        #on effectue le mouvement suivant s'il n'y a pas de joueur qui nous en empêche (sur la case destination)
                        if(len(trajetPlayers[j])>etapeTrajet[j]):
                            x_inc,y_inc = trajetPlayers[j][etapeTrajet[j]]   
                            etapeTrajet[j] = etapeTrajet[j]+1
                            next_row = row+x_inc
                            next_col = col+y_inc
                            players[j].set_rowcol(next_row,next_col)
                            ###print ("pos :", j, next_row,next_col)
                            game.mainiteration()
                            posPlayers[j]=(next_row,next_col)
                            
                        else:
                            print ("trajet terminé")
                            listFinish.append(j)
        else:
            if len(ordrePassage)>0 :
                j = ordrePassage.pop(0) #ON FAIT BOUGER LES JOUEURS RESTANTS QUI SE GENAIENT DANS LEURS TRAJETS
                for it in range(len(trajetPlayers[j])):
                    row,col = posPlayers[j]
                    ###print("Pos ",j, ":", row, col)
                    ###print("goalX ",j, ":", goalsPlayer[j])
                    if (row,col) == goalsPlayer[j] and goalsPlayer[j] in goalStates:# si on a  trouvé la fiole voulue, on la ramasse
                        print ("Objet trouvé par le joueur ", j)
                        o = players[j].ramasse(game.layers)
                        game.mainiteration()
                        goalStates.remove((row,col)) # on enlève ce goalState de la liste
                        score[j]+=1
                        listFinish.append(j)
                    else:
                        ###print ("deplacement")
                        if(len(trajetPlayers[j])>etapeTrajet[j]):
                            x_inc,y_inc = trajetPlayers[j][etapeTrajet[j]]   
                            etapeTrajet[j] = etapeTrajet[j]+1
                            next_row = row+x_inc
                            next_col = col+y_inc
                            players[j].set_rowcol(next_row,next_col)
                            ###print ("pos :", j, next_row,next_col)
                            game.mainiteration()
                            posPlayers[j]=(next_row,next_col)
                            
                        else:
                            print ("trajet terminé")
                            listFinish.append(j)
            else:
                break
                   
    print ("scores:", score)
    pygame.quit()
    
        
    """
   

if __name__ == '__main__':
    main()
    


