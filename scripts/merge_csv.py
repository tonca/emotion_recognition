import glob

fout = open("data/labeled_test.csv","w+")

files = glob.glob("data/openface_output/*")

# TODO
# Add the AU labels to the CSV
for file in files:
    f = open(file)
    
    # FACS labels
    facs_label_path = "data/FACS/%s/%s/*"%(file[21:25],file[26:29])    
    facs_label_path = glob.glob(facs_label_path)[0]
    facs_labels = "{ "
    for line in open(facs_label_path, 'r'):
        tokens = line[2:].split("   ")

        facs_id = int(float(tokens[0]))
        facs_val = float(tokens[1])
        facs_labels = facs_labels+" \"AU{:02d}\": {},".format(facs_id,facs_val)

    facs_labels = facs_labels[:-1]+" }"
    print(facs_labels)



# first file:
for line in open(files[0]):   
    head_ext = ", {}, {}\n".format("img_name", "emotion")
    fout.write(line[:-1]+head_ext)
    break

# now the rest:    
for file in files:
    f = open(file)

    # Image name
    img_name = file.split("/")[-1].split(".")[0]

    # Emotion labels
    emo_label_path = "data/Emotion/%s/%s/*"%(file[21:25],file[26:29])    
    emo_label_path = glob.glob(emo_label_path)[0]
    temp = open(emo_label_path, 'r') 
    label_value = int(float(temp.readline()))


    # Skip the header
    next(f) 

    # Write line
    new_cols = ", {}, {}\n".format(img_name, label_value)
    fout.write(next(f)[:-1]+new_cols)    

    # Not really needed
    f.close() 

fout.close()

import pandas as pd

df = pd.read_csv("data/labeled_test.csv")


print(df.head())
