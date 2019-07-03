
""" 
The idea of this script is to work with multiprocess in Python 2.7 to create a Gaussian noise signal and use it to move a visual stimulus 
in the screen (with a child process) while we keep tracking of the value of the Gaussian signal that is used at each instant. 
To do this the matplotlib animation ffunction is used

Developed by Diego Alonso San Alberto
"""

#import sys
#print(sys.executable)

import pygame as pg
import sys, time, os
import numpy as np
import multiprocessing as mProc
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from random import seed, gauss
from pandas import Series #required to use the describe method

SIZE=6000


#Fct to read the amount of cores in the workstation
def system_info():
    print ("Total amount of cores: %s"%(mProc.cpu_count()))


#----- Gaussian white noise serries-----
def gaussian_noise_fct(numSamples):
    #Seed for the random Number generator
    seed(1)
    #Gaussian White noise series
    gaussNoise= [gauss(0.0, 1.0) for i in range(numSamples)]
    gaussNoise= Series(gaussNoise)

    #Print gaussian noise information
    print ("\n--- GAUSSIAN WHITE NOISE Information ---")
    print ("Mean must be near 0.0 and Standard Deviation must be near 1.0")
    print(gaussNoise.describe())

    xMax= int(round(max(gaussNoise)))
    xMin= int(round(min(gaussNoise)))
    gaussMod = [((gaussNoise[i]-xMin)/(xMax-xMin)) * (1980 - 0) + 0 for i in range(numSamples)]
    return gaussMod
#----------------------------------------------------------


#------- FCT to display a rectangle using PYGAME V3------
def visual_graph_v3(conn, screen): 
    print (' * Starting pygame square')
    blue=(0,0,255)
    black=(0,0,0)
    startP= time.time()
    index=0

    while index< SIZE-2:
        #if index < 10 or index > SIZE-10:
        #    print index
        #Update the frames with the new position
        elem= conn.recv()
        screen.fill(black)
        pg.draw.rect(screen, blue, (elem, 0, 150, winH))
        #pgClock.tick(fps)
        pg.display.update()
        index+=1
    #print "\n -Points Displayed: %s -- Duration of the process: %s seconds"%(SIZE, time.time()-startP)
    conn.close()
    #Close the pygame windows
    pg.display.quit()
    pg.quit()
    
#--------------------------------------------------


#----- ANIMATE GRAPH V3 -----
def animate_graph_v3(conn, positionList, fig, ax, ln):

    print(' * Starting animated_graph')
    startTimer=time.time()
    #Generate the Y-axis values
    x=[v for v in range(size)]

    plt.title(" Gaussian White Noise")
    # Get current size
    fig_size = plt.rcParams["figure.figsize"]
    print "  -Window size: %s"%fig_size
    # Set figure width to 9 and height to 12
    fig_size[0] = 10
    fig_size[1] = 40
    plt.rcParams["figure.figsize"] = fig_size
    
    fig_size = plt.rcParams["figure.figsize"]
    
    print "  -Current window size: %s"%fig_size

    #Plot the full signal as background 
    plt.plot(positionList, x,'g')
    
    #set the x axis limits as the windows size
    plt.xlim(0, winW)

    #load index values and (x,y) positions together 
    data=[]
    for i, elem in enumerate(positionList):
        data.append((i,elem))

    #Function generator to provide the index with .next when required
    ctrl=update_ctrl()

    
    print(' * Launching plot animation ')
    ani= FuncAnimation(fig, update_animation, frames=data, init_func=init_animation, fargs=(conn,ctrl,),  interval=100, blit=True, repeat= False)
    plt.show()



    #print "Points counted: %s -- Animation duration: %s seconds"%(len(data),time.time()-startTimer)  
    
    #Once finished, stop the animation, delete it and close the plot window
    ani.event_source.stop()
    del ani
    plt.close()
    fig.close()



# Method to update the index value in the datapoints list. 
# It allows to send the next position to pygame from matplotlib animation
def update_ctrl():
    for i in range(SIZE):
        yield int(i)


#fct to init the animation in Matplotlib 
def init_animation():
    ax.set_xlim(0, 680)
    ax.set_ylim(0, 6000)
    return ln,


# Pick the new (x,y) point, update the red dot in the Matplotlib animation and
# send the point to the visual_graph fct to update the visual stim
def update_animation(frame,conn, c,):
    ctrl= c.next()
    if ctrl== SIZE-2:
        print '\n * Animation finished. Close the plot window to exit\n'
        xdata= 0
        ydata= 0
        conn.send(xdata)            #send the newPosition to the child_processor (pygame)
        ln.set_data(xdata, ydata)   #give the new position to matplotlib.funcAnimation
        #conn.close()
        #sys.exit()                 #to force exit of the script at the end of animation

    else:
        xdata= frame[1]
        ydata= frame[0]
        conn.send(xdata)            #send the newPosition to the child_processor (pygame)
        ln.set_data(xdata, ydata)   #give the new position to matplotlib.funcAnimation
    return ln, 
    
#--------------------------------------------------




# -- MAIN --

#Print system information
system_info()

winW=640
size=6000
#Generate  1000 points as x-axis values (positions between 0 and length of the screen)
positionList=[]
positionList_1= [np.random.randint(0, winW) for x in range(size)]
posistionList_2=[]
positionList_2= gaussian_noise_fct(size)
xMax=max(positionList_2)
xMin= min(positionList_2)
positionList_3= [((positionList_2[i]-xMin)/(xMax-xMin)) * (winW-150 - 150) + 150 for i in range(len(positionList_2))]

fps= 60 #set the fps value
fig, ax = plt.subplots()   
ln, = plt.plot([], []   , 'ro', animated=True)

winW=640
winH=480
# The point (0,0) is at the upper left hand corner of the screen.
# x coordinates increase from left to right, y coordinates increase from top to bottom, so:
#         Upper right is (640,0)
#         Lower left is (0,480)
#         Lower right is (640,480)
screen= pg.display.set_mode((winW, winH))


# creating a pipe
parent_conn, child_conn = mProc.Pipe()
p1= mProc.Process(target= animate_graph_v3, args=(parent_conn, positionList_3, fig, ax, ln)) 
p2= mProc.Process(target= visual_graph_v3, args=(child_conn,screen,))

# running processes
p1.start()
p2.start()

# wait until parent process had finished (no more points to use)
p1.join()

#Exit the system
sys.exit()