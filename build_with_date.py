import os
import shutil
import datetime
import subprocess
import sys
import zipfile

# 配置
MAIN_SCRIPT = "Softwaretest.py"
ICON_DIR = "icons"
DIST_DIR = "dist"
BUILD_DIR = "build"

# 生成带日期的 exe 名称
today = datetime.datetime.now().strftime("%Y%m%d")
exe_name = f"Beatbot_{today}.exe"
zip_name = f"Beatbot_{today}.zip"

# 1. 打包
cmd = [
    sys.executable, '-m', 'PyInstaller',
    "--windowed",
    "--onefile",
    f'--add-data={ICON_DIR};{ICON_DIR}',
    "--name", exe_name.replace(".exe", ""),
    MAIN_SCRIPT,
    "--hidden-import=cv2.legacy",
    "--hidden-import=cv2.legacy.TrackerCSRT_create",
    "--hidden-import=cv2.legacy.TrackerCSRT",
    "--hidden-import=cv2.TrackerCSRT_create",
    "--hidden-import=openpyxl"
]
print("打包命令：", " ".join(cmd))
subprocess.run(cmd, check=True)

# 2. 移动并重命名 exe
src_exe = os.path.join(DIST_DIR, exe_name.replace(".exe", "") + ".exe")
dst_exe = os.path.join(DIST_DIR, exe_name)
# 只有名字不一致时才重命名，否则直接跳过
if src_exe != dst_exe and os.path.exists(src_exe):
    if os.path.exists(dst_exe):
        os.remove(dst_exe)
    os.rename(src_exe, dst_exe)

# 3. 打包 dist 目录为 zip
with zipfile.ZipFile(zip_name, "w", zipfile.ZIP_DEFLATED) as zipf:
    for root, dirs, files in os.walk(DIST_DIR):
        for file in files:
            file_path = os.path.join(root, file)
            arcname = os.path.relpath(file_path, DIST_DIR)
            zipf.write(file_path, arcname)
print(f"已生成压缩包：{zip_name}")

# 4. 清理 build、spec 文件
if os.path.exists(BUILD_DIR):
    shutil.rmtree(BUILD_DIR)
spec_file = MAIN_SCRIPT.replace(".py", ".spec")
if os.path.exists(spec_file):
    os.remove(spec_file)

print("打包完成！可分发 exe 或 zip 包。")

try:
    # 轨迹线绘制相关代码
    pass
except Exception as e:
    import traceback
    with open('error.log', 'a', encoding='utf-8') as f:
        f.write(traceback.format_exc()) 