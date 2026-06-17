import sys
import os
import subprocess

def main():
    if len(sys.argv) != 3:
        print("用法: python run_pytest_loop.py link编号 循环次数")
        print("示例: python run_pytest_loop.py 4 100")
        sys.exit(1)

    try:
        link_num = int(sys.argv[1])
        run_total = int(sys.argv[2])
    except ValueError:
        print("错误：link编号、运行次数必须是数字")
        sys.exit(1)

    mark = f"link{link_num}"
    # 获取项目根目录
    script_abs = os.path.abspath(__file__)
    workflows_folder = os.path.dirname(script_abs)
    project_root = os.path.dirname(workflows_folder)

    pytest_cmd = ["pytest", "-m", mark]

    print(f"开始批量执行 {mark}，总次数：{run_total}\n")

    for curr in range(1, run_total + 1):
        ret = subprocess.run(
            pytest_cmd,
            cwd=project_root,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        # 根据返回码展示Pass/Fail，不打印数字返回码
        status = "Pass" if ret.returncode == 0 else "Fail"
        print(f"进度：{curr}/{run_total} | {status}")

    print(f"\n✅ {mark} {run_total} 轮全部执行完毕")

if __name__ == "__main__":
    main()