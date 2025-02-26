# blenderai_zealo

<p align="left">
  <a href="../README.md">English</a> |
  简体中文
</p>

[![Blender 版本](https://img.shields.io/badge/Blender-3.6%2B-orange)](https://www.blender.org/)
[![许可证](https://img.shields.io/badge/许可证-GPLv3-blue)](https://www.gnu.org/licenses/gpl-3.0.en.html)
[![GitHub 发布](https://img.shields.io/badge/发布版本-最新-green)](https://github.com/diversitymattesr/blenderai_zealo/releases)
[![Modelscope仓库](https://img.shields.io/badge/Modelscope-仓库-purple)](https://www.modelscope.cn/models/zhiliaomatters/blenderai_zealo)


这是一个 Blender 插件，可以使用 Tripo API 或在本地运行的 Trellis 生成器来生成 3D 模型。该插件旨在让 Blender 用户能够轻松利用 AI 制作 3D 模型。  
**注意：** Tripo API 是一项收费服务，而 Trellis 生成器是在本地运行的，因此 Trellis 是免费的。

## 目录
- [功能](#功能)
- [预先要求](#预先要求)
- [安装](#安装)
- [使用](#使用)
- [配置](#配置)
- [支持](#支持)
- [贡献](#贡献)
- [许可证](#许可证)
- [鸣谢](#鸣谢)

## 功能
- 利用 Tripo API 生成 3D 模型，无需访问其网站，节省 Blender 用户使用 AI 生成模型时间。  
- 利用 Microsoft Trellis 团队发布的强大 Trellis 生成器生成 3D 模型。  
- 本项目对官方 Trellis 代码进行了优化，使其可以在较低的显存下运行（经测试峰值显存占用为 4.6GB）。

## 预先要求
- Windows 10 或更高版本  
- 较新版本的 Blender  
- 支持 CUDA 的 Nvidia 显卡，且显存大于 4.6GB

## 安装
1. 从 [发布页面](https://github.com/diversitymattesr/blenderai_zealo/releases) 下载最新版本。  
2. 在 Blender 中：
   - 前往 `编辑 > 偏好设置 > 插件`  
   - 点击 `从磁盘安装` 并选择下载的 `.zip` 文件  
   - 勾选左上角正方形方框启用插件  
   - 在底部的偏好设置区域中设置 Tripo API 密钥，以便使用 Tripo 服务。获取 [Tripo API 密钥](https://platform.tripo3d.ai/api-keys)

## 使用
### 基本使用
1. 打开侧边栏：在 3D 视图中点击 `侧边栏 > AI 生成器`（或按快捷键 N 打开侧边栏）  
2. 在新打开的 AI 生成器面板中，将显示所有 AI 生成器的状态，例如：Tripo API 密钥是否正确、Python 依赖是否已安装、以及 Trellis AI 模型是否已下载并准备就绪。只需按照面板中的按钮提示完成各项准备工作。
   - 对于 Tripo 生成器：
     - **步骤 1**：检查是否已安装 Python 依赖。  
     - **步骤 2**：检查 API 密钥是否正确。
   - 对于 Trellis 生成器：
     - **步骤 1**：检查 Nvidia 驱动版本是否 >= 527.41。  
     - **步骤 2**：检查是否已安装 Python 依赖。  
     - **步骤 3**：首次准备 Trellis 生成器时，会花费较长时间下载所有所需的 AI 模型。
   - 如何选择 Trellis 生成器的启动参数：如果显存较低，建议选择 `设备模式: 动态 + 精度: float16`。选择其他选项会增加所需的显存。
3. 当所有 AI 生成器均已准备就绪后，点击相应按钮打开一个独立的面板：
   - **Tripo 生成器**：目前支持`文本转3D`和`图像转3D`。点击添加按钮后，输入文本或选择图片，其它任务参数都很直观。等待任务完成后，即可导入生成结果。
   - **Trellis 生成器**：目前仅支持`图像转3D`。点击添加按钮后，选择图片，等待任务完成后导入生成结果。

### 演示
[进行中]()

## 配置
- 通过 `编辑 > 偏好设置 > 插件 > blenderai_zealo` 进入设置  
- 核心配置：
  - 输入 Tripo API 密钥

## 支持
### 已知问题
- 暂无：期待您提出问题

### 故障排除
- 暂无：期待未来添加故障排除指南

### 问题报告
请在 [GitHub 问题](https://github.com/diversitymattesr/blenderai_zealo/issues) 页面中报告 bug 及功能需求。

## 贡献
欢迎您的贡献！请按照以下步骤：
1. Fork 仓库  
2. 创建功能分支  
3. 提交 Pull Request

## 许可证
该项目采用 [GNU 通用公共许可证 v3.0](https://www.gnu.org/licenses/gpl-3.0.en.html) 授权 —— 与 Blender 的许可要求兼容。

## 鸣谢
1. [Trellis](https://github.com/microsoft/TRELLIS)