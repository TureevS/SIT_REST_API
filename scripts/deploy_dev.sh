cd ../
git add -A
git commit -m "update"
git push origin master
ssh sodnom@128.199.122.96 'cd project-dev/scripts && sh build.sh'