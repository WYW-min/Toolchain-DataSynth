# git提交规范
参考 [Conventional Commits](https://www.conventionalcommits.org/zh-hans/v1.0.0/) 标准。

格式：
```
<type>(<scope>): <subject>  
// 空一行
<body (可选)>  
// 空一行
<footer (可选)>  
```

- type：提交类型
  - feat: ✨ 新功能
  - fix: 🐛 修补 Bug
  - refactor: ♻️ 重构代码 (不影响逻辑)
  - docs: 📝 修改文档
  - style: 💄 格式修改 (空格/分号等)
  - perf: 🚀 性能优化
  - test: ✅ 增加测试
  - chore: 🔧 杂事（构建/配置/依赖）

- scope：(可选) 影响范围，如 `cli`, `adapter`, `parser`
- subject：简短描述，动词开头，不加句号。
- body: (可选) 用来解释 **“为什么要这么改”以及“具体改了什么逻辑”**，描述修改动机和与之前行为的对比。
- footer: (可选，当前不需要) 主要用于机器识别（自动化工具）和标记重大变更。它位于提交信息的最后。

示例：

```text
feat(adapter): 增加word适配器组件
```

```
fix(cli): 修复参数解析时的路径报错
```

```
fix(auth): 修复 Token 过期后没有自动登出的问题   <-- Header

之前 Token 过期时，前端会无限重试请求，导致页面卡死。   <-- Body 开始
本次修改做了如下调整：
1. 在拦截器中增加了 401 状态码的判断
2. 捕获异常后强制清除本地存储的用户信息
3. 重定向回登录页
```
