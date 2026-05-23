module.exports = {
  extends: ["@commitlint/config-conventional"],
  rules: {
    // 类型必须在指定列表中
    "type-enum": [
      2,
      "always",
      [
        "feat", // 新功能
        "fix", // Bug 修复
        "docs", // 文档更新
        "style", // 代码格式（不影响功能）
        "refactor", // 重构
        "perf", // 性能优化
        "test", // 测试相关
        "chore", // 构建/工具链
        "ci", // CI/CD 配置
        "build", // 构建系统
        "revert", // 回滚
      ],
    ],
    // 类型必须小写
    "type-case": [2, "always", "lower-case"],
    // 类型不能为空
    "type-empty": [2, "never"],
    // Scope 可以为空
    "scope-empty": [0],
    // Subject 不能为空
    "subject-empty": [2, "never"],
    // Subject 大小写不限制（支持中英文混排）
    "subject-case": [0],
    // Subject 必须以动词开头，描述做了什么
    "subject-full-stop": [2, "never", "."],
    // Subject 长度限制
    "subject-max-length": [2, "always", 100],
    // Body 每行长度限制
    "body-max-line-length": [2, "always", 200],
    // Footer 格式检查
    "footer-leading-blank": [1, "always"],
  },
  prompt: {
    messages: {
      skip: ":skip",
      max: "upper %d chars",
      min: "%d chars at least",
      emptyWarning: "can not be empty",
      upperLimitWarning: "over limit",
      lowerLimitWarning: "below limit",
    },
    questions: {
      type: {
        description: "选择你要提交的类型",
        enum: {
          feat: {
            description: "✨ 新功能",
            title: "Features",
            emoji: "✨",
          },
          fix: {
            description: "🐛 Bug 修复",
            title: "Bug Fixes",
            emoji: "🐛",
          },
          docs: {
            description: "📚 文档更新",
            title: "Documentation",
            emoji: "📚",
          },
          style: {
            description: "💎 代码格式（不影响功能）",
            title: "Styles",
            emoji: "💎",
          },
          refactor: {
            description: "📦 代码重构",
            title: "Code Refactoring",
            emoji: "📦",
          },
          perf: {
            description: "🚀 性能优化",
            title: "Performance Improvements",
            emoji: "🚀",
          },
          test: {
            description: "🚨 测试相关",
            title: "Tests",
            emoji: "🚨",
          },
          chore: {
            description: "⚙️ 构建/工具链",
            title: "Chores",
            emoji: "⚙️",
          },
          ci: {
            description: "🔧 CI/CD 配置",
            title: "Continuous Integrations",
            emoji: "🔧",
          },
          build: {
            description: "🏗️ 构建系统",
            title: "Build System",
            emoji: "🏗️",
          },
          revert: {
            description: "⏪ 回滚",
            title: "Reverts",
            emoji: "⏪",
          },
        },
      },
      scope: {
        description:
          "本次修改的范围（如: web-admin, mcp-hub, ui, types, utils, docs）",
      },
      subject: {
        description: "简短描述本次修改的内容",
      },
      body: {
        description: "详细描述（可选）",
      },
    },
  },
};
