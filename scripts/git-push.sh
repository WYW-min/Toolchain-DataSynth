git checkout <自己的分支名>   # 切到自己的个人分支（永远是这一步开头）
git checkout main      # 切到main中转站
git push --set-upstream origin main


# 本地main分支永远只执行这两个命令
git checkout <自己的分支名>
git merge main

git add .
git commit -m "<自己的分支名>：完成xxx开发/修复xxx问题"
git push

echo "Done."