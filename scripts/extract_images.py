import glob
from shutil import copyfile
import subprocess

img_folder = "data\\cohn-kanade-images"
lbl_folder = "data\\Emotion"
out_folder = "data\\sorted"

emotions = ["neutral", "anger", "contempt", "disgust", "fear", "happy", "sadness", "surprise"] #Define emotion order
participants = glob.glob(lbl_folder+"\\*") #Returns a list of all folders with participant numbers

for x in participants:

    part = "%s" %x[-4:] #store current participant number
    
    for sessions in glob.glob("%s\\*" %x): #Store list of sessions for current participant
        for files in glob.glob("%s\\*" %sessions):
            print(files)
            current_session = files.split('\\')[3]
            print(current_session)
            file = open(files, 'r')
            
            emotion = int(float(file.readline())) #emotions are encoded as a float, readline as float, then convert to integer.
            
            print("%s\\%s\\%s\\*" %(img_folder, part, current_session))
            sourcefiles = glob.glob("%s\\%s\\%s\\*" %(img_folder, part, current_session)) #get path for last image in sequence, which contains the emotion
            print(sourcefiles)
            for img in sourcefiles:
                
                bashCommand = "%sFeatureExtraction.exe -f %s -of Out\\%s.txt"%("C:\\Users\\luigimissri\\Desktop\\gianni\\uni\\open_face\\",img,img[-21:-4])
                process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
                output, error = process.communicate() 
            

                # SAVE OUTPUT TO CSV :)
                
                
