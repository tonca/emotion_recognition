import pandas as pd
import numpy as np
import scipy

#implementing the a priori matrix
anger=pd.Series([0.17,0.10,0.33,0.25,0.03,0.05,0.00,0.1,0,0.05,0.06,0.4,0.31,0.49])
disgust=pd.Series([0.01,0.01,0.35,0.01,0.06,0.36,0.06,0.21,0,0,0,0.25,0.32,0.4])
fear=pd.Series([0.12,0.01,0.33,0.55,0,0.29,0.0,0.03,0,0.04,0.04,0.25,0.20,0.75])
happyness=pd.Series([0.07,0.09,0.01,0.05,0.94,0.01,0.05,0.0,0.92,0.0,0.0,0.02,0.34,0.55])
sadness=pd.Series([0.22,0.01,0.25,0.0,0.03,0.39,0.0,0.05,0.05,0.09,0.17,0.07,0.14,0.20])
surprise=pd.Series([0.15,0.19,0.08,0.76,0.0,0.02,0.0,0.10,0.04,0.0,0.04,0.09,0.26,0.72])
neutral=pd.Series([0,0,0,0,0,0,0,0,0,0,0,0,0,0])


path="../data/labeled_light.csv"  #my path to the file 
dat=pd.read_csv(path)#opening the file
 
#form the csv extracting the interest columns
nam=dat.columns.values
ok=nam[2:18]
ok= ok[ok!="AU14_r"]
ok= ok[ok!="AU23_r"]
opendat=dat.iloc[:,2:18]
del opendat["AU14_r"]
del opendat["AU23_r"]

a=(opendat>3)
a.sum().sum()
dati=opendat/5
a=(dati>1)
a.sum().sum()

#creating th ea priori matrix
mat=np.zeros((7,14))
mat[:]=[anger,disgust,fear,happyness,sadness,surprise,neutral]
matrix=pd.DataFrame(mat, columns=ok )



#EUCLIDEA

#create a dataframe with the distances computed with the euclidean 
lis_fin=[]
for i in range(len(dati.iloc[:,0])):
    photo=dati.iloc[i,:]
    lis_parz=[]
    for u in range(7):
        emo=matrix.loc[u,:]
        dist=np.sqrt(sum((emo-photo)*(emo-photo)))
        lis_parz.append(dist)
        
    lis_fin.append(lis_parz)   
    
ris=pd.DataFrame(lis_fin)        



ris.columns=["anger","disgust","fear","happyness","sadness","surprise","neutral"]


temp=[1,3,4,5,6,7,0]
emotions=pd.DataFrame(temp)



clas=[]
for i in range(len(ris.iloc[:,0])):
    
    m=ris.loc[i,:]==min(ris.loc[i,:])
    rev=m.tolist()
    rr=emotions[rev][0].tolist()[0]
    clas.append(rr)

papa=pd.Series(clas)



(dat["emotion"]==papa).sum()


#MINKOWSKI



lis_ne=[]
for v in range(200):
    for i in range(len(dati.iloc[:,0])):
        photo=dati.iloc[i,:]
        lis_parz=[]
        for u in range(7):
            emo=matrix.loc[u,:]
            dist=scipy.spatial.distance.minkowski(emo,photo,p=v+1)
            lis_parz.append(dist)
            
#        lis_parz.append(v+1)
        lis_ne.append(lis_parz)   
    
ris_m=pd.DataFrame(lis_ne)        


ris_m.columns=["anger","disgust","fear","happyness","sadness","surprise","neutral"]

temp=[1,3,4,5,6,7,0]
emotions=pd.DataFrame(temp)



clas=[]
for i in range(len(ris_m.iloc[:,0])):
    
    m=ris_m.loc[i,:]==min(ris_m.loc[i,:])
    rev=m.tolist()
    rr=emotions[rev][0].tolist()[0]
    clas.append(rr)

papa_m=pd.Series(clas)



derr=[]
for i in range(200):
    temp=papa_m[i*400:400+i*400]
    temp.index=range(400)
    a=(dat["emotion"]==temp).sum() / 400
    derr.append(a)
trend=pd.Series(derr)