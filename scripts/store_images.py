import glob
from shutil import copyfile
import subprocess

img_folder = "data/cohn-kanade-images"
lbl_folder = "data/Emotion"
out_folder = "data/stored"

participants = glob.glob(img_folder+"/*") #Returns a list of all folders with participant numbers

for x in participants:

    part = "%s" %x[-4:] #store current participant number
    neu_img = glob.glob(glob.glob("%s/*" %x)[0]+"/*")[0]
    print(neu_img)

    copyfile(neu_img, out_folder+"/"+neu_img.split("/")[-1])
    for sessions in glob.glob("%s/*" %x): #Store list of sessions for current participant
        print(sessions)
        emo_img = glob.glob("%s/*" %sessions)[-1]
        print(emo_img)

        copyfile(emo_img, out_folder+"/"+emo_img.split("/")[-1])

        
                
