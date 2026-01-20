# 核心原则
1. 始终基于最新的 main 分支创建/更新个人分支。
2. 严禁直接推送 main，所有改动必须通过 Merge Request (MR)。

# 开发前：同步主干，保持最新
git fetch origin main:main && git merge main
# (解释：更新本地 main 指针并合并到当前分支)

# 开发中：随时同步远程 main，避免后期冲突过多
git stash                  # 暂存当前未完成的工作
git fetch origin main:main # 拉取最新的主干代码
git merge main            # 使用 merge 合并main改动
git stash pop              # 恢复工作区
# (注意：如果 merge 过程中有冲突，按提示修改后 git merge --continue)

# 开发后：提交并推送
git add .
git commit -m "<type>(<scope>): <subject> "
git push --set-upstream origin HEAD    # HEAD 代表当前分支名，省去打分支名的麻烦