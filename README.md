# Emotion Recognition

## Instructions on how to use the repository

First of all you need to be added as contributor, you will need a github account for that ;) .   

### Clone the repository
`git clone git@github.com:tonca/emotion_recognition.git`

### After any change:

1. Verify that the code works

2. Verify which files have been changed__
`git status`

3. Add the changes to the git repository__
`git add .`

4. Commit changes__
`git commit -m "COMMIT DESCRIPTION"`

5. Update the local repository__
`git pull`

6. Update the remote repository__
`git push`

### The `data` folder

This folder is not loaded in the repository (this is autoatically managed by the `.gitignore` file).
This means that when you clone the repo you will have to add manually the data files that you will need.
Put all the heavy data files into this directory.

### The `scripts` folder

The scripts in this directory are not meant to be executed and you won't need to. 
I put this folder just to share what we did, so if you have some code that you want to share, you can put it into this folder.

### The `notebooks` folder

Here is where we will put out jupyter notebooks.