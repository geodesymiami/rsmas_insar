```
mkdir -p ~/local_git 
cd ~/local_git
echo "downloading miniconda ..."
wget http://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh; 
chmod +x ./Miniconda3-latest-Linux-x86_64.sh
./Miniconda3-latest-Linux-x86_64.sh -b -p ./miniconda3
miniconda3/bin/conda install git --yes 
alias git='~/local_git/miniconda3/bin/git'
```
