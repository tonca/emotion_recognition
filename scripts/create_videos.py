import glob
from shutil import copyfile
import subprocess

img_folder = "data/cohn-kanade-images"
lbl_folder = "data/Emotion"
out_folder = "data/sorted"

emotions = ["neutral", "anger", "contempt", "disgust", "fear", "happy", "sadness", "surprise"] #Define emotion order
participants = glob.glob(img_folder+"/*") #Returns a list of all folders with participant numbers

for x in participants:

    part = "%s" %x[-4:] #store current participant number
    
    for sessions in glob.glob("%s/*" %x): #Store list of sessions for current participant
        print(x)
        print(sessions)
        vid_name = glob.glob(sessions+"/*")[-1].split("/")[-1]
        print(vid_name)
        bashCommand = "ffmpeg -start_number 0 -i {}/{}%02d.png -vcodec mpeg4 ./data/ckplus_vids/{}.avi".format(sessions,vid_name[:15],vid_name[:17])


        process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
        output, error = process.communicate()
                
                
