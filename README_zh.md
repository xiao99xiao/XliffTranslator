# XLIFF 翻译工具

一个基于 Claude AI 的 XLIFF 文件翻译工具，专门用来处理 Xcode 生成的本地化文件。

## 目录

- [安装](#安装)
- [使用方法](#使用方法)
- [Xcode 本地化文件处理](#xcode-本地化文件处理)
  - [导出 XLIFF 文件](#导出-xliff-文件)
  - [导入翻译文件](#导入翻译文件)
- [命令行选项](#命令行选项)
- [应用上下文配置](#应用上下文配置)
- [翻译提示词](#翻译提示词)
- [辅助脚本](#辅助脚本)
  - [导出本地化文件](#导出本地化文件)
  - [导入本地化文件](#导入本地化文件)

## 安装

1. 克隆这个仓库
2. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```
3. 在项目根目录创建 `.env` 文件，添加你的 Claude API 密钥：
   ```bash
   echo "CLAUDE_API_KEY=你的密钥" > .env
   ```
4. 复制示例配置文件并根据你的应用进行自定义：
   ```bash
   cp app_context.example.yaml app_context.yaml
   ```
   然后编辑 `app_context.yaml`，填入你应用的具体信息。这个文件会被 git 忽略，所以不用担心泄露应用信息。

## 使用方法

单个文件模式：

```bash
python main.py --input 文件路径.xliff --target-language es
```

Xcode 导出文件夹模式：

```bash
# 翻译所有语言
python main.py --folder 导出文件夹路径

# 只翻译指定语言
python main.py --folder 导出文件夹路径 --languages "es,fr,ja"
```

## Xcode 本地化文件处理

### 导出 XLIFF 文件

用下面的命令从 Xcode 项目导出 XLIFF 文件：

```bash
# 导出所有语言
xcodebuild -exportLocalizations -project "你的项目.xcodeproj" -localizationPath ./Localizations

# 导出特定语言
xcodebuild -exportLocalizations -project "你的项目.xcodeproj" -localizationPath ./Localizations -exportLanguage fr
```

### 导入翻译文件

Xcode（包括界面和命令行）一次只能导入一种语言，这很麻烦。所以我们提供了一个脚本，可以一次性导入所有翻译好的语言：

1. 复制示例脚本：

   ```bash
   cp scripts/import_localizations.example.sh scripts/import_localizations.sh
   ```

2. 编辑脚本，设置你的路径：

   ```bash
   LOCALIZATIONS_DIR="本地化文件夹路径"  # 你的 .xcloc 文件所在位置
   PROJECT_PATH="项目路径.xcodeproj"    # 你的 Xcode 项目文件
   ```

3. 给脚本添加执行权限并运行：
   ```bash
   chmod +x scripts/import_localizations.sh
   ./scripts/import_localizations.sh
   ```

这个脚本会自动找到并导入所有翻译文件（不包括 en.xcloc），省去了手动一个个导入的麻烦。

## 命令行选项

- `--input`：要翻译的单个 XLIFF 文件（会直接修改原文件，并创建 .bak 备份）
- `--folder`：包含 .xcloc 文件夹的 Xcode 导出文件夹（和 --input 二选一）
- `--target-language`：目标语言代码（单文件模式必需）
- `--languages`：要处理的语言代码列表，用逗号分隔（文件夹模式可选）
- `--context-file`：应用上下文配置文件路径（默认：app_context.yaml）
- `--prompts-file`：提示词文件路径（默认：prompts.yaml 或 prompts.example.yaml）
- `--translate-all`：翻译所有字符串，包括已翻译的

## 应用上下文配置

应用上下文配置帮助 Claude 提供更准确和更符合语境的翻译。配置包括：

- 应用描述和用途
- 关键术语和定义
- 文风指南和语气偏好
- 目标用户信息

在 `app_context.example.yaml` 中提供了示例配置。使用方法：

1. 将 `app_context.example.yaml` 复制为 `app_context.yaml`
2. 编辑 `app_context.yaml`，填入你应用的具体信息
3. 保持敏感信息私密 - `app_context.yaml` 默认会被 git 忽略

配置文件结构示例：

```yaml
preserve_names:
  app_names: ["你的应用名称"]
  product_models: ["产品型号"]

app_description: |
  你的应用描述和用途...

terminology:
  - term: "重要术语"
    description: "术语定义"
    note: "使用说明"

style_guide:
  tone: "语气风格"
  formality: "正式程度"
  technical_level: "技术水平"
  key_points:
    - "翻译指南..."
```

这些上下文信息帮助 Claude 理解你的应用领域，提供符合你期望风格和术语的翻译。

## 翻译提示词

这个工具使用可自定义的提示词来指导 Claude 的翻译过程。提示词以 YAML 格式存储：

1. 将 `prompts.example.yaml` 复制为 `prompts.yaml`
2. 根据需要自定义提示词

提示词文件包含两个主要部分：

- `system_prompt`：设置 Claude 的角色和回复格式
- `translation_prompt`：指导具体的翻译过程

两种提示词都支持在翻译过程中自动填充的变量：

- `{target_lang}`：目标语言代码
- `{app_context}`：来自你的应用上下文文件的内容
- `{num_texts}`：要翻译的字符串数量
- `{numbered_texts}`：实际要翻译的字符串

你的自定义提示词在 `prompts.yaml` 中默认会被 git 忽略，以保护应用特定信息。

## 辅助脚本

### 导出本地化文件

你可以用提供的脚本从 Xcode 项目导出 XLIFF 文件：

1. 复制示例脚本：

   ```bash
   cp scripts/export_localizations.example.sh scripts/export_localizations.sh
   ```

2. 编辑脚本，设置你的路径和语言：

   ```bash
   PROJECT_PATH="项目路径.xcodeproj"  # 你的 Xcode 项目文件
   EXPORT_DIR="导出文件夹路径"        # 保存 .xcloc 文件的位置
   LANGUAGES="fr es ja zh-Hans zh-Hant"  # 要导出的语言（留空则导出所有语言）
   ```

3. 给脚本添加执行权限：

   ```bash
   chmod +x scripts/export_localizations.sh
   ```

4. 运行脚本：
   ```bash
   ./scripts/export_localizations.sh
   ```

这个脚本会：

- 如果导出目录不存在就创建它
- 导出指定语言的 XLIFF 文件（如果没指定就导出所有语言）
- 显示每个导出操作的状态

### 导入本地化文件

翻译完 XLIFF 文件后，你可以用提供的脚本把它们导入回 Xcode 项目：

1. 复制示例脚本：

   ```bash
   cp scripts/import_localizations.example.sh scripts/import_localizations.sh
   ```

2. 编辑脚本，设置你的路径：

   ```bash
   LOCALIZATIONS_DIR="本地化文件夹路径"  # 你的 .xcloc 文件所在位置
   PROJECT_PATH="项目路径.xcodeproj"    # 你的 Xcode 项目文件
   ```

3. 给脚本添加执行权限：

   ```bash
   chmod +x scripts/import_localizations.sh
   ```

4. 运行脚本：
   ```bash
   ./scripts/import_localizations.sh
   ```

这个脚本会：

- 在指定目录中找到所有 .xcloc 文件（不包括 en.xcloc）
- 把每个本地化文件导入到你的 Xcode 项目中
- 显示每个导入操作的状态
