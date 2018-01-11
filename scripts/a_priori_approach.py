

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


path="../data/labeled_fromvids.csv"  #my path to the file 
dat=pd.read_csv(path)#opening the file

#form the csv extracting the interest columns
nam=dat.columns.values
ok=nam[2:18]
ok= ok[ok!="AU14_r"]
ok= ok[ok!="AU23_r"]
opend=dat.iloc[:,2:18]
del opend["AU14_r"]
del opend["AU23_r"]


#rescale to [0,1] the dataset
((opend>0).sum())/327<0.60

openda=opend.loc[:,((( opend>0).sum())/len(dat.iloc[:,0]) <0.60) ]

opendat=openda.loc[:,openda.max()>0]



prova=np.array(opendat)
prova[(prova>3)]=3




dati=prova/prova.max(axis=0)
a=(dati>1)
a.sum().sum()

#creating the a priori matrix
mat=np.zeros((7,14))
mat[:]=[anger,disgust,fear,happyness,sadness,surprise,neutral]
matrix=pd.DataFrame(mat, columns=ok )

matrix=matrix.loc[:,((opend>0).sum())/len(dat.iloc[:,0]) <0.60]
matrix=matrix.loc[:,openda.max()>0]


#EUCLIDEA

#create a dataframe with the distances computed with the euclidean 
lis_fin=[]
for i in range(len(dati[:,0])):
    photo=dati[i,:]
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

a=ris.iloc[325,:].tolist()
a.sort()
c=np.array(temp)
c[a[0]==ris.iloc[325,:]][0]

#selecting the minimal distance between each photo and the emotions
clas=[]
for i in range(len(ris.iloc[:,0])):
    a=ris.iloc[i,:].tolist()
    a.sort()
    c=np.array(temp)
    q=c[a[0]==ris.iloc[i,:]][0]

    '''m=ris.loc[i,:]==min(ris.loc[i,:])
    rev=m.tolist()
    rr=emotions[rev][0].tolist()[0]
    clas.append(rr)'''
    clas.append(q)

papa=pd.Series(clas)


#percentage of right clissified emotions
((dat["emotion"]==papa).sum())/327


#MINKOWSKI

#like in the euclidean distance, but here we compute the distance with the minkowski degree going from 1 to 201
lis_ne=[]
for v in range(200):
    for i in range(len(dati[:,0])):
        photo=dati[i,:]
        lis_parz=[]
        for u in range(7):
            emo=matrix.loc[u,:]
            dist=scipy.spatial.distance.minkowski(emo,photo,p=v+1)
            lis_parz.append(dist)
            
        lis_ne.append(lis_parz)   
 

 
      
'''
for i in range(len(dati.iloc[:,0])):
    photo=dati.iloc[i,:]
    lis_parz=[]
    for u in range(7):
        emo=matrix.loc[u,:]
        dist=scipy.spatial.distance.minkowski(emo,photo,p=1)
        lis_parz.append(dist)
    lis_ne.append(lis_parz)   
 '''   
ris_m=pd.DataFrame(lis_ne)        


ris_m.T /ris_m.sum(axis=1)





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
    temp=papa_m[i*len(dati[:,0]):len(dati[:,0])+i*len(dati[:,0])]
    temp.index=range(len(dati[:,0]))
    a=(dat["emotion"]==temp).sum() / len(dati[:,0])
    derr.append(a)
trend=pd.Series(derr)
trend

'''
((dat["emotion"]==papa_m).sum())/400


#percentage of accurancy usig the different degree
#print(trend)

'''














