from pathlib import Path
import json


# main.py位于：
# repo-mentor/src/repo_mentor/main.py
#
# parents[0] = repo_mentor
# parents[1] = src
# parents[2] = repo-mentor
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEMO_DATA_DIR = PROJECT_ROOT / "data" / "demo_repo"


def load_user_profile() -> dict:
    """读取用户学习资料。"""
    file_path = DEMO_DATA_DIR / "user_profile.json"

    if not file_path.exists():
        raise FileNotFoundError(f"找不到用户资料文件：{file_path}")

    with file_path.open("r", encoding="utf-8") as file:
        return json.load(file)


def load_text_file(filename: str) -> str:
    """读取演示仓库中的文本文件。"""
    file_path = DEMO_DATA_DIR / filename

    if not file_path.exists():
        raise FileNotFoundError(f"找不到文件：{file_path}")

    return file_path.read_text(encoding="utf-8")


def main() -> None:
    """程序入口。"""
    try:
        user_profile = load_user_profile()
        repository_readme = load_text_file("README.md")
        repository_tree = load_text_file("tree.txt")

        print("=" * 50)
        print("用户资料")
        print("=" * 50)
        print(json.dumps(user_profile, ensure_ascii=False, indent=2))

        print("\n" + "=" * 50)
        print("仓库README")
        print("=" * 50)
        print(repository_readme)

        print("\n" + "=" * 50)
        print("仓库目录")
        print("=" * 50)
        print(repository_tree)

    except FileNotFoundError as error:
        print(f"文件读取失败：{error}")
    except json.JSONDecodeError as error:
        print(f"JSON格式错误：{error}")
    except OSError as error:
        print(f"文件系统错误：{error}")


if __name__ == "__main__":
    main()