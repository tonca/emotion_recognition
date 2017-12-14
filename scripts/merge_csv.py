import glob


fout_path = "data/labeled.csv"

fout = open(fout_path,"w+")

files = glob.glob("data/openface_output/*")

# TODO
# Add the AU labels to the CSV
facs_list = set([])

for file in files:
    f = open(file)

    # FACS labels
    facs_label_path = "data/FACS/%s/%s/*"%(file[21:25],file[26:29])    
    facs_label_path = glob.glob(facs_label_path)[0]
    for line in open(facs_label_path, 'r'):
        tokens = line[2:].split("   ")
        facs_id = int(float(tokens[0]))

        facs_list.add("true_AU{:02d}".format(facs_id))

facs_head = ""
for col in sorted(facs_list):
    facs_head = facs_head+col+", "
facs_head = facs_head[:-2]


# first file:
for line in open(files[0]):

    head_ext = ", {}, {}, {}\n".format("img_name", "emotion", facs_head)
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


    # FACS labels
    facs_labels = [0] * len(facs_list)
    facs_label_path = "data/FACS/%s/%s/*"%(file[21:25],file[26:29])    
    facs_label_path = glob.glob(facs_label_path)[0]
    for line in open(facs_label_path, 'r'):
        tokens = line[2:].split("   ")
        facs_id = "true_AU{:02d}".format(int(float(tokens[0])))
        facs_val = float(tokens[1])
        if (facs_val == 0):
            facs_val = -1 
        facs_labels[sorted(facs_list).index(facs_id)] = facs_val

    facs_row = ""
    for col in sorted(facs_labels):
        facs_row = facs_row+str(col)+", "
    facs_row = facs_row[:-2]

    # Skip the header
    next(f) 

    # Write line
    new_cols = ", {}, {}, {}\n".format(img_name, label_value, facs_row)
    fout.write(next(f)[:-1]+new_cols)    

    # Not really needed
    f.close() 

fout.close()


import pandas as pd

df = pd.read_csv(fout_path)
df.columns = df.columns.str.replace('\s+', '')

selected_cols = [col for col in df.columns.values if col[:2] == 'AU' or col[:4] == "true"]
selected_cols.insert(0,"img_name")
selected_cols.append("emotion")

df[selected_cols].to_csv("data/labeled_light.csv")

df_lite = df[selected_cols].copy()


# Exclude images
sel_images = []

# Select images
label_files_path = "data/Emotion/*"    
for participant in glob.glob(label_files_path):
	for sequence in glob.glob(participant+"/*"):
		img_seq = glob.glob(sequence+"/*")
		if len(img_seq) > 0:
			file_ = img_seq[0].split("/")[-1][:-12] 
			sel_images.append(file_[-16:])


neutral_df = df_lite[df_lite["img_name"].apply(lambda img: img[-2:] == "01")].copy()
neutral_df["emotion"] = 0

emotion_df = df_lite[df_lite["img_name"].apply(lambda img: img[-16:] in sel_images )]

out_df = pd.concat([neutral_df,emotion_df], ignore_index=True)

# Save to file
out_df.to_csv("data/labeled_light.csv")
