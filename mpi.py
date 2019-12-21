#!/usr/bin/env python3
from mpi4py import MPI
import numpy as np
import math  
from numpy import genfromtxt
import sys
import time

#Created by Taha Eyup Korkmaz - 2014400258
#Status: Compiling
#Working status: Working
#Notes: User can set the input,output and iteration numbers below

INPUT_FILE="test.txt" #assign the input file name here
OUTPUT_FILE="out.txt" #assign the output file name here
Iterations=10 #assign number of iterations

arrData =  genfromtxt(INPUT_FILE, delimiter=" ")
t=0 #initial state
COMM_WORLD = MPI.COMM_WORLD
rank = COMM_WORLD.Get_rank()
size = COMM_WORLD.Get_size()

arrData = np.array(arrData)
arrDataX = np.array(arrData)
slaveRankCount = size -1 #slaveRankCount assuming 16 as example
slavesPerDimension = int(math.sqrt(slaveRankCount))#sqrt of slave num 4 as example
lengthPerSlave = int(len(arrData)/slavesPerDimension)    #each slave's cell size
def findTop(rank):#finding the top slave
    if rank<=slavesPerDimension:
        return slaveRankCount-(slavesPerDimension-rank)
    else:
        return rank - slavesPerDimension
def findBot(rank):  #finding the bot slave
    if rank>slaveRankCount-slavesPerDimension:
        return slavesPerDimension-(slaveRankCount-rank)
    else:
        return rank + slavesPerDimension
def findLeft(rank): #finding the left slave
    a = int(rank-1)%slavesPerDimension 
    if a == 0:
        return rank + slavesPerDimension - 1
    else:
        return rank-1
def findRight(rank):    #finding the Right slave
    a = int(rank)%slavesPerDimension 
    if a == 0:
        return rank - slavesPerDimension + 1
    else:
        return rank + 1

def gameOfLife(mySliceInput):   #game of life calculation
    for j in range(1,lengthPerSlave+1):#for rows
        for k in range(1,lengthPerSlave+1):#for columns
            neighbor = mySliceInput[j-1][k-1]+mySliceInput[j-1][k]+mySliceInput[j-1][k+1]+mySliceInput[j][k-1]+mySliceInput[j][k+1]+mySliceInput[j+1][k-1]+mySliceInput[j+1][k]+mySliceInput[j+1][k+1]#calculating the sum of 1s in neighbors
            if mySliceInput[j][k]==0 and neighbor==3: #balance in all things
                mySliceX[j][k]=1
            elif mySliceInput[j][k]==1 and neighbor<2:#loneliness also kills
                mySliceX[j][k]=0
            elif  mySliceInput[j][k]==1 and neighbor>3: # overpopulation kills
                mySliceX[j][k]=0
            else:
                mySliceX[j][k]=np.copy(mySliceInput[j][k]) #remain same otherwise
    temp[1:lengthPerSlave+1,1:lengthPerSlave+1]=np.copy(mySliceX[1:lengthPerSlave+1,1:lengthPerSlave+1])
    sendSlice=np.copy(mySliceX[1:lengthPerSlave+1,1:lengthPerSlave+1])


sendSlice = [] #initialization the initial sent slice
for i in range(lengthPerSlave):
 column = []
 for j in range(lengthPerSlave):
  column.append(0)
 sendSlice.append(column)
sendSlice = np.array(sendSlice)

mySliceX = [] #initialization the big array that includes the recieved top/up/right/left etc
for i in range(lengthPerSlave+2):
 column = []
 for j in range(lengthPerSlave+2):
  column.append(0)
 mySliceX.append(column)
mySliceX = np.array(mySliceX)


if rank == 0:#for the manager 

    for i in range(1,slaveRankCount+1): ##for slaves
        row = int((i-1)/slavesPerDimension)
        column = i-(row*slavesPerDimension)-1
        for j in range(lengthPerSlave):  ##rows
            for k in range(lengthPerSlave):  ##columns
                #print(k)
                sendSlice[j][k] = np.copy(arrData[(row*lengthPerSlave)+j][(column*lengthPerSlave)+k]) #dividing the input to every slave
                
        COMM_WORLD.Send([sendSlice,MPI.INT],dest=i,tag=14) #sending the divided arrays to slaves

    for i in range(1,slaveRankCount+1): #for slaves
        row = int((i-1)/slavesPerDimension)
        column = i-(row*slavesPerDimension)-1
        COMM_WORLD.Recv([mySliceX,MPI.INT],source=i,tag=14) #receiving the last states from slaves
        #print(mySliceX,'came to the manager from ',i) 
        arrDataX[row*lengthPerSlave:(row+1)*lengthPerSlave,column*lengthPerSlave:(column+1)*lengthPerSlave]=np.copy(mySliceX[1:lengthPerSlave+1,1:lengthPerSlave+1]) #setting the end state
    arrData=np.copy(arrDataX)
    print('Ending and printing to the file', OUTPUT_FILE)
    np.savetxt(fname=OUTPUT_FILE,X=arrData,delimiter=" ", newline=" \n",fmt='%1d')


else:

    COMM_WORLD.Recv([sendSlice,MPI.INT],source=0,tag=14) #initial state recevie from the manager
    temp = np.empty((lengthPerSlave+2,lengthPerSlave+2),dtype=int)
    temp = np.array(temp)
    temp.fill(0)    
    len = len(sendSlice)
    temp[1:lengthPerSlave+1,1:lengthPerSlave+1]=np.copy(sendSlice)
    row = (rank-1)//slavesPerDimension
    column = rank-(row*slavesPerDimension)-1

    while(t<Iterations): # while for the iterations
        
        if rank%2==1:#For Odd Ones
            COMM_WORLD.Send([sendSlice,MPI.INT],dest=findRight(findTop(rank)),tag=14)#RightTop sending to evens
            COMM_WORLD.Send([sendSlice,MPI.INT],dest=findRight(rank),tag=14)#Right
            COMM_WORLD.Send([sendSlice,MPI.INT],dest=findRight(findBot(rank)),tag=14)#RightBot
            COMM_WORLD.Send([sendSlice,MPI.INT],dest=findLeft(findBot(rank)),tag=14)#LeftBot
            COMM_WORLD.Send([sendSlice,MPI.INT],dest=findLeft(rank),tag=14)#Left
            COMM_WORLD.Send([sendSlice,MPI.INT],dest=findLeft(findTop(rank)),tag=14)#LeftTop

            COMM_WORLD.Recv([sendSlice,MPI.INT],source=findRight(findTop(rank)),tag=14)#receive from right top even
            temp[0,len+1]=sendSlice[0,lengthPerSlave-1]
            COMM_WORLD.Recv([sendSlice,MPI.INT],source=findRight(rank),tag=14)#receive from right
            temp[1:len+1,len+1]=sendSlice[:,0]
            COMM_WORLD.Recv([sendSlice,MPI.INT],source=findBot(findRight(rank)),tag=14)#receive right bot
            temp[len+1,len+1]=sendSlice[0,0]
            COMM_WORLD.Recv([sendSlice,MPI.INT],source=findBot(findLeft(rank)),tag=14)#receive bot left
            temp[0,len+1]=sendSlice[0,lengthPerSlave-1]
            COMM_WORLD.Recv([sendSlice,MPI.INT],source=findLeft(rank),tag=14)# receive left
            temp[0,1:len+1]=sendSlice[:,lengthPerSlave-1]
            COMM_WORLD.Recv([sendSlice,MPI.INT],source=findTop(findLeft(rank)),tag=14)#receive top left
            temp[0,0]=sendSlice[lengthPerSlave-1,lengthPerSlave-1]

            if row%2==0:#Odd and Row even ie first row
                COMM_WORLD.Send([sendSlice,MPI.INT],dest=findTop(rank),tag=14)#Top
                COMM_WORLD.Send([sendSlice,MPI.INT],dest=findBot(rank),tag=14)#Bot Sends
                
                COMM_WORLD.Recv([sendSlice,MPI.INT],source=findBot(rank),tag=14)#tag14 receive from Bot
                temp[len+1,1:len+1]=np.copy(sendSlice[0,:])
                COMM_WORLD.Recv([sendSlice,MPI.INT],source=findTop(rank),tag=14)#tag14 receive from Top
                temp[0,1:len+1]=np.copy(sendSlice[lengthPerSlave-1,:])

            else:#Odd and Row odd ie second row
                
                COMM_WORLD.Recv([sendSlice,MPI.INT],source=findBot(rank),tag=14)#tag14 receive from Bot
                temp[len+1,1:len+1]=np.copy(sendSlice[0,:])
                COMM_WORLD.Recv([sendSlice,MPI.INT],source=findTop(rank),tag=14)#tag14 receive from Top
                temp[0,1:len+1]=np.copy(sendSlice[lengthPerSlave-1,:])

                COMM_WORLD.Send([sendSlice,MPI.INT],dest=findTop(rank),tag=14)#Top
                COMM_WORLD.Send([sendSlice,MPI.INT],dest=findBot(rank),tag=14)#Bot Sends

        else: #even
            COMM_WORLD.Recv([sendSlice,MPI.INT],source=findBot(findLeft(rank)),tag=14)#Left Bot Receive from the odds
            temp[len+1,0]=np.copy(sendSlice[0,lengthPerSlave-1])
            COMM_WORLD.Recv([sendSlice,MPI.INT],source=findLeft(rank),tag=14)#Left Receive
            temp[1:len+1,0]=np.copy(sendSlice[:,lengthPerSlave-1])
            COMM_WORLD.Recv([sendSlice,MPI.INT],source=findTop(findLeft(rank)),tag=14)#Left Top Receive
            temp[0,0]=np.copy(sendSlice[lengthPerSlave-1,lengthPerSlave-1])
            COMM_WORLD.Recv([sendSlice,MPI.INT],source=findRight(findTop(rank)),tag=14)#Rigt Top Receive
            temp[0,len+1]=np.copy(sendSlice[0,lengthPerSlave-1])
            COMM_WORLD.Recv([sendSlice,MPI.INT],source=findRight(rank),tag=14)#Right Receive
            temp[1:len+1,len+1]=np.copy(sendSlice[:,0])
            COMM_WORLD.Recv([sendSlice,MPI.INT],source=findBot(findRight(rank)),tag=14)#Right Bot Receive
            temp[len+1,len+1]=np.copy(sendSlice[0,0])
            
            COMM_WORLD.Send([sendSlice,MPI.INT],dest=findLeft(findBot(rank)),tag=14)#LeftBot sends to Odds
            COMM_WORLD.Send([sendSlice,MPI.INT],dest=findLeft(rank),tag=14)#Left
            COMM_WORLD.Send([sendSlice,MPI.INT],dest=findLeft(findTop(rank)),tag=14)#LeftTop
            COMM_WORLD.Send([sendSlice,MPI.INT],dest=findRight(findTop(rank)),tag=14)#RightTop
            COMM_WORLD.Send([sendSlice,MPI.INT],dest=findRight(rank),tag=14)#Right
            COMM_WORLD.Send([sendSlice,MPI.INT],dest=findRight(findBot(rank)),tag=14)#RightBot
            
            if row%2==0:#Even and even row ie first row
                COMM_WORLD.Recv([sendSlice,MPI.INT],source=findBot(rank),tag=14)#tag14 receive from Bot
                temp[len+1,1:len+1]=np.copy(sendSlice[0,:])
                COMM_WORLD.Recv([sendSlice,MPI.INT],source=findTop(rank),tag=14)#tag14 receive from Top
                temp[0,1:len+1]=np.copy(sendSlice[lengthPerSlave-1,:])

                COMM_WORLD.Send([sendSlice,MPI.INT],dest=findBot(rank),tag=14)#Top
                COMM_WORLD.Send([sendSlice,MPI.INT],dest=findTop(rank),tag=14)#Bot Sends

                
            else:#even and odd row ie second row
                COMM_WORLD.Send([sendSlice,MPI.INT],dest=findTop(rank),tag=14)#Bot Sends                
                COMM_WORLD.Send([sendSlice,MPI.INT],dest=findBot(rank),tag=14)#Top
                
                COMM_WORLD.Recv([sendSlice,MPI.INT],source=findTop(rank),tag=14)#tag14 receive from Top
                temp[0,1:len+1]=np.copy(sendSlice[lengthPerSlave-1,:])
                COMM_WORLD.Recv([sendSlice,MPI.INT],source=findBot(rank),tag=14)#tag14 receive from Bot
                temp[len+1,1:len+1]=np.copy(sendSlice[0,:])
        
        gameOfLife(temp)
        print(mySliceX,'is mySliceX for rank',rank,'at iteration',t+1)
        t+=1
    COMM_WORLD.Send([mySliceX,MPI.INT],dest=0,tag=14)#Return Back to Manager(rank=0)