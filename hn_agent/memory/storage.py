"""
记忆存储：原子文件 I/O。

MemoryStorage 使用"写入临时文件 → os.rename 原子重命名"策略，
确保记忆数据写入不会因进程中断而损坏。
"""

from __future__ import annotations

import logging
import os
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)


class MemoryStorage:
    """原子文件 I/O 的记忆存储。

    每个用户的记忆存储为独立的文本文件：``{storage_dir}/{user_id}.md``

    Parameters
    ----------
    storage_dir : str
        记忆文件存储目录路径。
    """

    def __init__(self, storage_dir: str = "./data/memory") -> None:
        self._storage_dir = Path(storage_dir)

    @property
    def storage_dir(self) -> Path:
        return self._storage_dir

    def _user_path(self, user_id: str) -> Path:
        """返回用户记忆文件路径。"""
        # 防止路径注入
        safe_id = user_id.replace("/", "_").replace("\\", "_").replace("..", "_")
        return self._storage_dir / f"{safe_id}.md"

    def read(self, user_id: str) -> str:
        """读取用户的记忆文件。

        Parameters
        ----------
        user_id : str
            用户 ID。

        Returns
        -------
        str
            记忆内容。文件不存在时返回空字符串。
        """
        path = self._user_path(user_id)
        try:
            return path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return ""
        except Exception:
            logger.exception("读取记忆文件失败: %s", path)
            return ""

    def write(self, user_id: str, content: str) -> None:
        """原子写入用户的记忆文件。

        先写入同目录下的临时文件，再通过 os.rename 原子重命名，
        确保写入过程中断不会损坏已有数据。

        Parameters
        ----------
        user_id : str
            用户 ID。
        content : str
            要写入的记忆内容。
        """
        path = self._user_path(user_id)

        try:
            # 确保目录存在
            path.parent.mkdir(parents=True, exist_ok=True)

            # 在同一目录创建临时文件（确保同一文件系统，os.rename 才是原子的）
            fd, tmp_path = tempfile.mkstemp(
                dir=str(path.parent),
                prefix=f".{path.stem}_",
                suffix=".tmp",
            )
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    f.write(content)
                    f.flush()
                    os.fsync(f.fileno())

                # 原子重命名
                os.replace(tmp_path, str(path))
            except Exception:
                # 清理临时文件
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass
                raise
        except Exception:
            logger.exception("写入记忆文件失败: %s（保留旧数据）", path)

    def exists(self, user_id: str) -> bool:
        """检查用户记忆文件是否存在。"""
        return self._user_path(user_id).exists()

    def delete(self, user_id: str) -> None:
        """删除用户记忆文件。"""
        path = self._user_path(user_id)
        try:
            path.unlink(missing_ok=True)
        except Exception:
            logger.exception("删除记忆文件失败: %s", path)
