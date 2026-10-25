# wupzl 的学习书架

首页汇总 PyTorch、AI 纪元、数据帝国、RAG 帝国和系统设计五个阅读项目。GitHub Pages 从 `master` 分支根目录发布。

## 更新首页

修改 `index.html` 中的章节数和状态。当前为 PyTorch 13 章（连载，第十四章待续）、AI 纪元 12 章（第一卷完）、数据帝国 13 章（主线完成）、RAG 帝国 9 章（全书完结）、系统设计 8 章（连载，第九章待续）。

## 本地验收

将本仓库放在 `bookshelf/`，其余五个仓库放在同级的 `pytorch-apprentice/`、`ai-era-reader/`、`data-empire-reader/`、`rag-empire-reader/`、`system-design-reader/` 目录中，各自保留已生成的 `docs/`。

在这些目录的共同父目录运行：

```bash
python -m pip install -r bookshelf/requirements-test.txt -r system-design-reader/requirements-test.txt
python -m playwright install chromium
python bookshelf/verify.py
```

无需启动服务器。脚本检查首页章节数与各项目 `docs/chapters.json` 一致、四种完结状态、本地链接与锚点、全部页面在 390/768/1440px 下的布局、五项目切换菜单、返回书架及三种主题持久化。外部插图请求被拦截，不依赖第三方图片服务。截图输出到仓库外的同级 `bookshelf-validation/`。

工作区原有 `python verify_bookshelf.py` 命令继续可用，调用本仓库内的同一份脚本。

PyTorch 的完整阅读功能验收另需在一个终端运行 `python -m http.server 4174 --directory pytorch-apprentice/docs --bind 127.0.0.1`，在另一个终端运行 `python pytorch-apprentice/verify.py`。

## 持续检查

`.github/workflows/verify-readers.yml` 在本仓库 push、pull request、每天北京时间 08:00 及手动运行时检出五个阅读仓库的 `main` 分支，执行总验收、系统设计阅读验收与 PyTorch 完整验收。每日检查用于发现阅读仓库更新后首页尚未同步的情况。运行页面可下载验收截图；失败时保留已有截图以便排查。
