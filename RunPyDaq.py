###############################################################################
###
### RunPyDaq
### This file is part of CoreDataLogging
### This file was created by Dr Daniel Parker 
###    Twitter: @DrDanParker     GitHub:https://github.com/DrDanParker 
###     
### Copyright (C) 2018 University of Salford - All Rights Reserved
### You may use, distribute and modify this code under the terms of MIT Licence
### See RunPyDaq/LICENSE or go to https://tldrlegal.com/license/mit-license for full licence details
###
### Based on the following:
###     Daq Class: From danieljfarrell - https://github.com/danieljfarrell/pydaq/blob/master/DAQ.py
###     Live Plot: Adapted from TopTechBoy - https://goo.gl/jSHqhT 
###
###############################################################################




import ctypes
import numpy as np
import matplotlib.pyplot as plt
from string import atoi
from time import sleep
from drawnow import drawnow



# Class constants
nidaq = ctypes.windll.nicaiu
#nidaq  = ctypes.cdll.LoadLibrary(find_library('nidaqmxbase')) ### Removed as was not effective for NIDAQ 6008
int32 = ctypes.c_long
uInt32 = ctypes.c_ulong
uInt64 = ctypes.c_ulonglong
float64 = ctypes.c_double
TaskHandle = uInt32
DAQmx_Val_Cfg_Default = int32(-1)
DAQmx_Val_Default     = int32(-1)
DAQmx_Val_Volts = 10348
DAQmx_Val_Amps  = 10342
DAQmx_Val_Rising = 10280
DAQmx_Val_FiniteSamps = 10178
DAQmx_Val_GroupByChannel = 0
DAQmx_Val_GroupByScanNumber = 1
max_num_samples = 2
sampling_frequency = 2500
data = np.zeros((max_num_samples,),dtype=np.float64)

def CHK(err):
    """a simple error checking routine"""
    if err < 0:
        buf_size = 100
        buf = ctypes.create_string_buffer('\000' * buf_size)
        nidaq.DAQmxGetErrorString(err,ctypes.byref(buf),buf_size)
        raise RuntimeError('nidaq call failed with error %d: %s'%(err,repr(buf.value)))

class DAQ:
    def __init__(self, channel):
        #Channel sets the analogue input channel to measure from as a string
        # e.g. "Dev1/ai0"
        CHK(nidaq.DAQmxResetDevice (channel[0:4]))
        sleep(0.25)
        self.channel = channel

        #Does channel have a range?
        index = channel.rfind(":")
        if index != -1:
            self.number_of_channels = atoi(channel[index+1:len(channel)]) + 1
        else:
            self.number_of_channels = 1

        print "Using device " + channel[0:4] + " and %d channel(s):" % self.number_of_channels
        for i in range(0,self.number_of_channels):
            print channel[4:index-1] + "%d" % i
    
    
    def voltage(self):
        taskHandle = taskHandle = TaskHandle(0)
        CHK(nidaq.DAQmxCreateTask("",ctypes.byref(taskHandle)))
        CHK(nidaq.DAQmxCreateAIVoltageChan(taskHandle,self.channel,"",DAQmx_Val_Cfg_Default,float64(-10.0),float64(10.0),DAQmx_Val_Volts,None))
        CHK(nidaq.DAQmxCfgSampClkTiming(taskHandle,"",float64(sampling_frequency),
                                DAQmx_Val_Rising,DAQmx_Val_FiniteSamps,
                                uInt64(max_num_samples)));
        CHK(nidaq.DAQmxStartTask(taskHandle))
        
        read = int32()
        data = np.zeros((max_num_samples*self.number_of_channels,),dtype=np.float64)
        CHK(nidaq.DAQmxReadAnalogF64(taskHandle,max_num_samples,float64(10.0),
                             DAQmx_Val_GroupByScanNumber,data.ctypes.data,
                             len(data),ctypes.byref(read),None))
        recorded_points = read.value
        CHK(nidaq.DAQmxStopTask(taskHandle))
        CHK(nidaq.DAQmxClearTask(taskHandle))
        return data[0:self.number_of_channels]
    
    def current(self):
        taskHandle = TaskHandle(0)
        CHK(nidaq.DAQmxCreateTask("",ctypes.byref(taskHandle)))
        # Is this the current channel ? "SC1Mod1/ai0"
        CHK(nidaq.DAQmxCreateAICurrentChan(taskHandle,self.channel,"",DAQmx_Val_Cfg_Default,float64(0.0),float64(0.02),DAQmx_Val_Amps,DAQmx_Val_Default,float64(249.0),""))
        CHK(nidaq.DAQmxCfgSampClkTiming(taskHandle,"",float64(sampling_frequency),
                                DAQmx_Val_Rising,DAQmx_Val_FiniteSamps,
                                uInt64(max_num_samples)));
        CHK(nidaq.DAQmxStartTask(taskHandle))
        
        read = int32()
        data = np.zeros((max_num_samples*self.number_of_channels,),dtype=np.float64)
        CHK(nidaq.DAQmxReadAnalogF64(taskHandle,max_num_samples,float64(10.0),
                             DAQmx_Val_GroupByScanNumber,data.ctypes.data,
                             len(data),ctypes.byref(read),None))
        
        recorded_points = read.value
        CHK(nidaq.DAQmxStopTask(taskHandle))
        CHK(nidaq.DAQmxClearTask(taskHandle))
        return data[0:self.number_of_channels]


def makeFig(): #Create a function that makes our desired plot
    # plt.ylim(-5,5)
    plt.title('My Live Streaming Sensor Data')      #Plot the title
    # plt.grid(True)                                  #Turn the grid on

    plt.subplot(411)
    plt.plot(VOL[0], 'r', label='Voltage')       #plot the temperature

    # for i in range(0,n_channels):
    #     plt.subplot(n_channels,1,i+1)
    #     plt.plot(VOL[i])
    
    
#Setup Live Plot
plt.close('all')
plt.ion()         #Tell matplotlib you want interactive mode to plot live data
cnt=0


#Define Daq and Datasets
n_channels = 4
daq = DAQ("Dev1/ai0:"+str(n_channels-1))
DATALOG = []
VOL = np.empty((4,1))
CUR = np.empty((4,1))
count=-1


#Start Recording
try:        
    while True: # While loop that loops forever
        V= daq.voltage()
        C= daq.current()
        
        DATALOG.append(V)
        count=count+1
        print "Voltage", V,' Log Count: ',count
        for j in range(len(V)):
            VOL[j]+[float(V[-1])]
            CUR[j]+[float(C[-1])]
        
        
        drawnow(makeFig)          #Call drawnow to update our live graph
        plt.pause(.000001)              #Pause Briefly. Important to keep drawnow from crashing
        cnt=cnt+1
        # if(cnt>50):                     #If you have 50 or more points, delete the first one from the array
        #     VOL[0].pop(0)               #This allows us to just see the last 50 data points
        #     VOL[1].pop(0)
        #     VOL[2].pop(0)
        #     VOL[3].pop(0)

# End Recording
except KeyboardInterrupt:
    print str(len(DATALOG)) + 'Samples of data colleted'


    
# Convert DAQ Output to Data Structure and Output to CSV    
Volts = DATALOG
Volts = zip(*Volts)
print len(Volts)


plt.figure()
for i in range(len(Volts)):
    val = np.array(Volts[i])
    offset = np.mean(val[:20])
    val = val - offset
    plt.plot(val)



Condition = 'Calib_3581'
headers = 'V1,V2,V3,V4,\n'


f = open('C:/Syncplicity/UoS Work/Projects/FlowOx/FlowOx_2/FlowOxPressureData/Data/Positioner/'+Condition +'.csv', 'w')
f.write(headers)
for i in range(len(Volts[0])):
    line = ''
    for j in range(len(Volts)):
        line = line + str(Volts[j][i])+','
    line = line+ '\n'
    f.write(line)

f.close()


