"""
CLI 入口
"""
import click
import subprocess
import sys
from pathlib import Path


@click.group()
def cli():
    """Stock Review - 股票筛选与分析工具"""
    pass


@cli.command()
def init():
    """初始化配置"""
    click.echo("初始化配置...")
    config_dir = Path(__file__).parent.parent.parent / "configs"
    config_dir.mkdir(exist_ok=True)
    click.echo(f"配置目录已创建：{config_dir}")


@cli.command()
def fetch():
    """获取/更新数据"""
    click.echo("数据获取功能开发中...")


@cli.command()
def server():
    """启动后端服务"""
    click.echo("启动服务器...")
    subprocess.run(
        [sys.executable, "-m", "uvicorn", "src.api.app:app", "--reload", "--port", "8000"],
        cwd=Path(__file__).parent.parent.parent
    )


if __name__ == "__main__":
    cli()
