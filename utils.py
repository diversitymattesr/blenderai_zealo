import logging
import os
import sys
import bpy
import ensurepip
from pathlib import Path
from bpy.app.handlers import persistent

ADDON_NAME = __package__

def absolute_path(path: str):
    return os.path.normpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), path))

def open_console():
    if not sys.platform == "win32":
        return
    bpy.ops.wm.console_toggle()

def ensure_pip():
    try:
        import pip
    except ImportError:
        ensurepip.bootstrap()

@persistent
def initial_properties(dummy):
    print("================Initial Properties=====================")
    gen_props = bpy.context.scene.gen_props
    tripogen_props = bpy.context.scene.tripogen_props
    if len(tripogen_props.txt23d_tasks) == 0:
        tripogen_props.txt23d_tasks.add()
    if len(tripogen_props.img23d_tasks) == 0:
        tripogen_props.img23d_tasks.add()
    trellisgen_props = bpy.context.scene.trellisgen_props
    if len(trellisgen_props.img23d_tasks) == 0:
        trellisgen_props.img23d_tasks.add()

    bpy.ops.blenderai_zealo.check_windows_long_path_support()
    bpy.ops.blenderai_zealo.trellis_check_manifest_nvidia_driver()
    if gen_props.windows_long_path_support:
        bpy.ops.blenderai_zealo.tripo_check_python_dependencies()
        if gen_props.tripo_python_dependencies_installed:
            bpy.ops.blenderai_zealo.tripo_check_ready()

        if gen_props.trellis_manifest_nvidia_driver:
            bpy.ops.blenderai_zealo.trellis_check_python_dependencies()
            if gen_props.trellis_python_dependencies_installed:
                bpy.ops.blenderai_zealo.trellis_check_ready()

    
    print("======================End Initialization==================")

PYTHON_DEPENDENCIES_FOLDER = absolute_path("venv/python_dependencies")
os.makedirs(PYTHON_DEPENDENCIES_FOLDER, exist_ok=True)

TRIPOGEN_OUTPUT_FOLDER = absolute_path("./user_data/tripogen_output")
os.makedirs(TRIPOGEN_OUTPUT_FOLDER, exist_ok=True)

TRELLISGEN_OUTPUT_FOLDER = absolute_path("./user_data/trellisgen_output")
os.makedirs(TRELLISGEN_OUTPUT_FOLDER, exist_ok=True)

translations_dict = {'zh_HANS': {('*', 'Tripo API Key'): 'Tripo API密钥', ('*', 'Installing dependency: '): '正在安装依赖项：', ('*', 'Installation of Python dependency success: '): 'Python依赖项安装成功：', ('*', 'Try to launch Trellis Generator...'): '正在尝试启动Trellis建模器...', ('*', 'Trellis Generator exited with error since: '): 'Trellis建模器因以下错误退出：', ('*', 'Trellis Generator exited normally'): 'Trellis建模器正常退出', ('*', 'Trellis Generator exited with unexpected error since: '): 'Trellis建模器因意外错误退出：', ('*', 'No Trellis running'): '无Trellis进程运行', ('*', 'Error code: '): '错误代码：', ('*', 'Error message: '): '错误信息：', ('*', 'Suggestion: '): '建议：', ('*', 'There is something wrong on the local machine: '): '本地出现问题：', ('*', 'Bring the code and message and contact the admin of this blender addon'): '请携带错误代码和信息联系本Blender插件管理员', ('*', 'There is something wrong on the local machine to request a connection to'): '本地连接请求出现问题', ('*', 'since error: '): '因为此错误：', ('*', 'Please try to do it again or contact to admin of this blender addon'): '请重试或联系本Blender插件管理员', ('*', 'Task generation failed since an error: '): '此生成任务失败，错误原因：', ('*', 'Try to re-watch the task or contact the admin of this blender addon.'): '请重新查看任务进度或联系本Blender插件管理员', ('*', 'Something wrong on the local machine. Code: '): '本地出现问题。代码：', ('*', 'Reason: '): '原因：', ('*', 'Try to do it again or contact the admin of this blender addon.'): '请重试或联系本Blender插件管理员', ('*', 'Something wrong on the local machine: '): '本地出现问题：', ('*', 'An unexpected error occurred: '): '发生意外错误：', ('*', 'Bring the code and message and contact the admin of the blender addon'): '请携带错误代码和信息联系Blender插件管理员', ('*', 'Installing '): '正在安装：', ('*', 'Installation of this dep success: '): '依赖项安装成功：', ('*', 'Installation of this dep failed: '): '依赖项安装失败：', ('*', 'Checking Tripo API Key: '): '正在验证Tripo API密钥：', ('*', 'Tripo API Key Correct.'): 'Tripo API密钥正确', ('*', 'User Balance: '): '用户余额：', ('*', 'Tripo API Key Incorrect Since Error: '): 'Tripo API密钥验证失败，错误原因：', ('*', 'Something wrong on the task. The finalized status of this task is: '): '此生成任务出现问题，其最终状态为：', ('*', 'Check Windows Long Path Support'): '检查Windows是否支持长路径文件', ('*', 'Select Folder to Contain File'): '选择放置文件的文件夹', ('*', 'Folder'): '文件夹', ('*', 'Select a folder to contain the script'): '选择放置自动脚本的文件夹', ('*', 'Default to: '): '默认为', ('*', 'Copy file: '): '复制文件：', ('*', ' to: '): '至：', ('*', ' failed since error: '): '失败因为此错误：', ('*', 'Check Nvidia Driver Version if Manifest Min Version'): '检查NVIDIA驱动版本是否满足最低要求', ('*', 'Check Trellis Generator Python Dependencies'): '检查Trellis建模器Python依赖', ('*', 'Install Trellis Generator Python Dependencies'): '安装Trellis建模器Python依赖', ('*', 'Tripo is installing python dependencies currently. Please wait for it and then install for trellis.'): 'Tripo正在安装Python依赖项。请等待其完成再进行Trellis安装', ('*', 'Check Wether Trellis Generator is Ready'): '检查Trellis建模器是否就绪', ('*', 'Make Trellis Generator Ready'): '准备Trellis建模器', ('*', 'Terminate: '): '杀死该进程：', ('*', 'Precision'): '精度', ('*', 'float16'): 'float16', ('*', 'float32'): 'float32', ('*', 'Device Mode'): '设备模式', ('*', 'dynamic'): '动态', ('*', 'cuda'): 'CUDA', ('*', 'There is a process taking over port 8000 which not belongs to current process'): '有非当前进程占用了端口 8000', ('*', 'If you choose not to terminate, then you can not run trellis on current process.'): '如果不终止该进程，将无法在当前进程中运行Trellis', ('*', 'Default configuration of precision and device mode required least VRAM. Any changes would require more VRAM.'): '精度和设备模式的默认配置所需的显存最小，如果你改变默认配置，所需显存会增多', ('*', 'Manually Close Trellis Process'): '手动关闭Trellis进程', ('*', 'Manually close trellis process'): '手动关闭Trellis进程', ('*', 'Are you sure you want to terminate the process running Trellis?'): '你确定要强制关闭Trellis进程吗？', ('*', 'Toggle Trellis Generator Panel'): '切换Trellis建模器面板', ('*', 'Add Image to 3D Task in Trellis Generator'): '在Trellis建模器中添加图像转3D任务', ('*', 'Task Name'): '任务名称', ('*', 'Image Path'): '图像路径', ('*', 'Preprocess Image'): '去除图片背景', ('*', 'Output Type'): '输出类型', ('*', 'Model'): '模型', ('*', 'Base Model'): '基础模型', ('*', 'Task'): '任务', ('*', 'Only png and jpeg format.'): '仅支持PNG和JPEG图像格式', ('*', 'Now we can only support png and jepg image format.'): '目前仅支持PNG和JPEG图像格式', ('*', 'Remove Failed Image to 3D Task'): '移除失败的图像转3D任务', ('*', 'You can only remove a uploading failed task or creating failed task'): '只能移除上传失败或创建失败的任务', ('*', 'Rewatch Image to 3D Task'): '查看图像转3D任务进度', ('*', 'You can only re-watch a task with status watch_failed'): '只能重新查看状态为查看任务失败的任务', ('*', 'Redownload Image to 3D Task'): '重新下载图像转3D任务', ('*', 'You can only re-download model with status downloading_failed'): '只能重新下载状态为下载失败的任务', ('*', 'Trellis: Import Model Of Success Image 2 3D Task'): 'Trellis：导入成功图像转3D任务的模型', ('*', "The model hasn't been downloaded yet!"): '模型尚未下载！', ('*', 'Try to import glb file from: '): '尝试从以下位置导入 GLB 文件：', ('*', 'But get an error: '): '但出现错误：', ('*', 'No objects were imported.'): '没有导入任何对象', ('*', 'Imported object: '): '已导入对象：', ('*', 'Check Tripo Generator Python Dependencies'): '检查 Tripo 建模器 Python 依赖', ('*', 'Install Tripo Generator Python Dependencies'): '安装Tripo建模器Python依赖', ('*', 'Trellis is installing python dependencies currently. Please wait for it and then install for tripo.'): 'Trellis正在安装Python依赖项。请等待其完成再进行Tripo安装', ('*', 'Check Wether Tripo Generator is Ready'): '检查Tripo建模器是否就绪', ('*', 'Toggle Tripo Generator Panel'): '切换Tripo建模器面板', ('*', 'Add Text to 3D Task'): '添加文本转3D任务', ('*', 'Prompt'): '提示词', ('*', 'Model Version'): '模型版本', ('*', 'v2.0'): '版本2.0', ('*', 'v1.4'): '版本1.4', ('*', 'v1.3'): '版本1.3', ('*', 'PBR Model'): 'PBR模型', ('*', 'Remove Failed Text to 3D Task'): '移除失败的文本转3D任务', ('*', 'You can only remove a creating failed task'): '只能移除创建失败的任务', ('*', 'Rewatch Text to 3D Task'): '重新查看文本到3D任务', ('*', 'You can only rewatch a task with status watch_failed'): '只能重新查看状态为查看任务失败的任务', ('*', 'Redownload Text to 3D Task'): '重新下载文本到3D任务', ('*', 'You can only re-download model with status downloading_failed.'): '只能重新下载状态为下载失败的任务', ('*', 'Import Model Of Success Txt To 3D Task'): '导入成功的文本到3D任务模型', ('*', 'Add Image to 3D Task'): '创建图像到3D任务', ('*', 'Now we can only support png and jepg image format. '): '目前我们仅支持PNG和JPEG图像格式', ('*', 'Import Model Of Success Image to 3D Task'): '导入成功的图像到3D任务模型', ('*', 'AI Generator Status'): 'AI建模器状态', ('*', 'AI Generator'): 'AI建模器', ('*', 'Tripo Generator'): 'Tripo建模器', ('*', 'Close Tripo Generator'): '关闭Tripo建模器', ('*', 'Open Tripo Generator'): '打开Tripo建模器', ('*', 'The tripo api key is not correct'): 'Tripo API密钥不正确', ('*', 'Please go to addon preferences to modify it.'): '请前往插件偏好设置进行修改', ('*', 'Check API Key'): '检查API密钥', ('*', 'Installing Progress'): '安装进度', ('*', 'Install Python Dependencies'): '安装Python依赖项', ('*', 'Trellis Generator'): 'Trellis建模器', ('*', 'Close Trellis Generator'): '关闭Trellis建模器', ('*', 'Open Trellis Generator'): '打开Trellis建模器', ('*', 'Manually close Trellis process'): '手动关闭Trellis进程', ('*', 'Making Ready Progress'): '准备进度', ('*', 'Get Trellis Generator Ready'): '准备Trellis建模器', ('*', 'The version of your Nvidia driver should be at least 527.41. Please update your driver.'): '您的Nvidia驱动程序版本应至少为527.41。请更新您的驱动程序。', ('*', 'Check Nvidia Driver'): '检查Nvidia驱动', ('*', 'Method A (If you have Geforce Experience installed in your computer)'): '方法A（如果您的计算机中已安装Geforce Experience）', ('*', 'Step1: Open Geforce Experience'): '步骤1：打开Geforce Experience', ('*', 'Step2: Click Driver tab on top'): '步骤2：点击顶部的驱动程序选项卡', ('*', 'Step3: In available driver section, click download to get latest driver'): '步骤3：在可用驱动程序部分，点击下载以获取最新驱动程序', ('*', "Method B (If you don't have Geforce Experience installed in your computer)"): '方法B（如果您的计算机中未安装Geforce Experience）', ('*', 'Step1: '): '步骤1：', ('*', 'Get Programme to Update Nvidia Driver'): '获取用于更新Nvidia驱动的程序', ('*', 'Step2: In Manual Driver Search Area, Select Appropriate Type of Your Driver'): '步骤2：在手动驱动程序搜索区域中，选择适合您的驱动程序类型', ('*', 'Step3: In the Results, Choose any one between Studio Driver and Game Ready Driver'): '步骤3：在搜索结果中，选择Studio驱动或Game Ready驱动中的任意一个', ('*', 'Step4: After Downloaded, Follow Guided to Update Your Driver'): '步骤4：下载完成后，按照引导步骤更新驱动程序', ('*', 'Check if windows support long path'): '检查windows是否支持长路径文件', ('*', 'Your windows does not support long path.'): '你的windows不支持长文件路径', ('*', 'Try to configure your windows using following methods'): '使用以下方法配置你的windows', ('*', 'Method A: Manually'): '方法A：手动配置', ('*', 'Step1: Open Start Menu -> Search Registry Editor -> Open it in administration mode'): '步骤1：打开开始菜单 -> 搜索注册表编辑器 -> 以管理员身份运行', ('*', 'Step2: Navigate to: '): '步骤2： 导航至：', ('*', 'Step3: Find Key: LongPathsEnabled and set the value of it to 1'): '步骤3：找到键：LongPathEnabled 然后将其值设为1', ('*', 'Step4: Click the button above to check if windows now support long path'): '步骤4: 点击上面的按钮去查看windows是否已经支持长路径文件', ('*', 'Method B: Automatically'): '方法B: 自动脚本配置', ('*', 'Select a folder to contain the automatic script'): '选择一个文件夹放置自动脚本', ('*', 'Step2: Run the script in administration mode named '): '步骤2：以管理员身份运行此脚本：', ('*', 'Step3: Click the button above to check if windows now support long path'): '步骤3: 点击上面的按钮去查看windows是否已经支持长路径文件', ('*', 'The blender extension is in public test phrase.'): '本插件目前处于公测阶段。', ('*', 'If you encounter some issue, open blender console to check or bring the error to admin.'): '如果你遇到使用错误无法解决，请打开blender后台检查或者将错误信息带给本插件管理员检查。', ('*', 'Toggle blender console'): '打开/关闭blender后台', ('*', 'Name'): '名称', ('*', 'Image'): '图像', ('*', 'Output'): '输出', ('*', 'Create'): '创建', ('taskHeader', 'Watch'): '查看进度', ('*', 'Download'): '下载', ('*', 'Not Yet'): '尚未进入此阶段', ('*', 'Uploading'): '上传中', ('*', 'Failed'): '失败', ('*', 'Creating'): '创建中', ('*', 'Created'): '已创建', ('*', 'Success'): '成功', ('*', 'Trellis'): 'Trellis', ('*', 'Image to 3D Tasks'): '图像到3D任务', ('Operator', 'Add'): '创建', ('*', 'Remove Failed'): '移除失败项', ('*', 'Rewatch'): '重新查看', ('*', 'Redownload'): '重新下载', ('*', 'Import'): '导入', ('*', 'Tripo'): 'Tripo', ('*', 'Text to 3D Tasks'): '文本到3D任务'}}