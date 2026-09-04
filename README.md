# mac-vision-ocr

macOS local OCR MCP server — zero-cost, offline, ~1s per image. / macOS 本地 OCR 的 MCP 封装，离线免费，单图约 1 秒。

用 macOS 自带 **Vision 框架**（Swift）做文字识别，再用一页 Python 包成 [Model Context Protocol](https://modelcontextprotocol.io) 工具，供 Claude Code 等 MCP 客户端调用。中英混排识别接近满准（聊天截图、报错截图、代码截图的主场）。

- **本地离线**：不过云、不要 API key、不烧任何 quota
- **快**：单图约 1 秒（首次 Swift 编译 10-30 秒属正常）
- **免费**：Vision 是 macOS 系统能力
- **格式干净**：默认纯文字按版面顺序排好，`coords=True` 可带 `y= x=` 归一化坐标前缀

> 核心识别脚本源自本家 hermes 的 `apple-vision-ocr` 技能（2026-09-03 验证、2026-09-04 收编立项）。

## 安装

```bash
git clone git@github.com:mangxy/mac-vision-ocr.git
cd mac-vision-ocr
./install.sh
```

`install.sh` 做三件事（幂等，可重复跑）：

1. 拷贝 `ocr_vision.swift` 与 `server.py` 到 `~/.claude/bin/`
2. 在 `~/.claude.json` 的 user 级 `mcpServers` 注册 `mac-vision-ocr`
3. 依赖由 [uv](https://docs.astral.sh/uv/) 在启动时自动拉起（`mcp<2`），无需手动装包

安装后**重启 Claude Code**（新会话生效），工具面板即出现 `ocr` 工具。

## 使用

对 MCP 客户端（Claude Code）来说就是一个工具：

| 参数 | 说明 |
|------|------|
| `path` | 图片绝对路径（png/jpg 截图等） |
| `langs` | 逗号分隔语言码，默认 `zh-Hans,en-US` |
| `coords` | 是否带 `y= x= |` 坐标前缀，默认 `False`（纯文字） |

返回按版面排序的纯文字。返回「图里没抠出文字」说明是纯图/照片，应改用视觉理解类工具（多模态模型）。

```text
ocr("/Users/you/Desktop/screenshot.png")
→ …识别出的文字…
```

## 附赠：`see` 本地看图工具（可选）

`ocr` 只抠字，不懂图。若本机跑着 **oMLX** 并加载了多模态模型（如 Qwen 系列 omni），同目录注册的 `see` 工具可离线问图：

| 参数 | 说明 |
|------|------|
| `path` | 图片绝对路径（png/jpg/webp/gif/bmp） |
| `question` | 想问什么，默认"详细描述这张图的内容" |
| `timeout` | 等待秒数，默认 300 |

- 接口配置自动读 `~/.openviking/ov.conf` 的 `vlm` 块（或 env `OMLX_BASE_URL` / `OMLX_API_KEY` / `OMLX_MODEL`），**key 不进仓库**
- oMLX 队列被批处理（如索引烧库）占满时会排队很久，超时会明说，改走云端视觉工具即可
- 没有 oMLX？`see` 会报「没找到本地 VLM 配置」，`ocr` 不受影响

## 卸载

```bash
./uninstall.sh
```

## 已知边界

- 小字号英文 UI 词偶有字母错认（如 `ultra`→`uetra`）；中文大段文本基本满准
- 纯图标/照片/漫画无文字时返回空，此时走多模态理解更合适
- boundingBox 左下原点已换算为左上原点坐标（脚本内处理）

## License

MIT
