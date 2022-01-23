cd ../
git stash
git pull origin master
git stash pop
source .env/bin/activate
pip install -r requirements.txt