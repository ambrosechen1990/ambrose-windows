import os
import subprocess
import sys

def run_command(command):
    print(f"\n执行命令: {command}")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(result.stdout)
        return result
    except subprocess.CalledProcessError as e:
        print(f"命令执行失败: {command}")
        print(e.stderr)
        sys.exit(1)

def main():
    # 1. 切换到 softwaretest 目录
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    # 2. 初始化 git 仓库
    if not os.path.exists(".git"):
        run_command("git init")

    # 3. 添加远程仓库（如已存在则跳过）
    result = subprocess.run("git remote", shell=True, capture_output=True, text=True)
    if "origin" not in result.stdout.split():
        run_command("git remote add origin git@github.com:ambrosechen1990/ambrose-windows.git")
    else:
        print("远程仓库 'origin' 已存在")

    # 4. 添加 .gitignore（可选，防止上传 .venv、dist 等）
    if not os.path.exists(".gitignore"):
        with open(".gitignore", "w", encoding="utf-8") as f:
            f.write(".venv/\ndist/\n__pycache__/\n*.pyc\n.idea/\n")

    # 5. 添加并提交
    run_command("git add .")
    run_command('git commit -m "upload softwaretest code"')

    # 6. 推送
    run_command("git branch -M master")
    run_command("git push -u origin master")

if __name__ == "__main__":
    main() 