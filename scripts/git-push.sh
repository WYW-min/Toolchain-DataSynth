git checkout dev/wyw   # 切到自己的个人分支（永远是这一步开头）
git checkout main      # 切到main中转站
git push --set-upstream origin main


git checkout dev/wyw
git merge main

git add .
git commit -m "dev/wyw：完成xxx开发/修复xxx问题"



echo "Done."