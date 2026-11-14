# 代理节点池订阅 · 每日自动整合

每天由 GitHub Actions 在云端自动运行：抓取公开节点池 → 去重 → 查询归属地 → 实测延迟与下载速度 → 生成一份可直接导入的 Clash Meta 订阅，并把结果提交回本仓库。

**订阅地址（把 `<用户名>` `<仓库名>` 换成你自己的）**

| 用途 | 地址 |
|---|---|
| jsDelivr（国内一般可直连，推荐） | `https://cdn.jsdelivr.net/gh/<用户名>/<仓库名>@main/sub/clash.yaml` |
| GitHub 原始文件 | `https://raw.githubusercontent.com/<用户名>/<仓库名>/main/sub/clash.yaml` |
| 最新测速报告 | `https://cdn.jsdelivr.net/gh/<用户名>/<仓库名>@main/reports/latest.md` |

## 数据来源

上游为公开仓库 `free9999/ipupdate` 的 `backup/img/1/2/ipp` 目录，取其中四个文件夹：

- `clash.meta2`（6 份 config.yaml）
- `hysteria`（4 份 config.json）
- `hysteria2`（4 份 config.json）
- `quick`（4 份 config.yaml）

## 处理流程

1. **抓取**：走 GitLab raw 直链，遇到 429 限流自动重试，并回退到上次缓存。
2. **解析**：分别处理 Clash YAML、Hysteria v1 JSON、Hysteria2 JSON 三种格式。
3. **去重**：以「服务器 + 端口 + 认证口令 + SNI」四要素为唯一键，合并内容重复的配置。
4. **归属地**：调用 ip-api.com 批量接口，域名先本地解析成 IP。
5. **测速**：
   - ICMP 往返延迟与丢包（`ping`）
   - 真实代理时延与吞吐：下载 mihomo 二进制，用同一进程实拨全部节点，测 204 握手延迟 + 8 秒限时下载
6. **输出**：`sub/clash.yaml`（订阅）、`sub/nodes.csv`、`reports/YYYY-MM-DD.md`、`reports/latest.md`

## 节点命名规则

节点名 = **来源文件夹名 + 两位序列号**，例如 `clash.meta2-03` 表示来自 `clash.meta2` 文件夹的第 3 个节点。

- 序列号按文件夹各自独立递增，从 `01` 开始。
- 序号基于**去重后**的节点，因此若某文件夹内有重复配置被合并，序号会短于原配置文件数量（`clash.meta2` 有 6 份配置、去重后仅 4 个节点，因此只到 `-04`）。
- 国家地区不写入节点名，统一在 `reports/latest.md` 与 `sub/nodes.csv` 的「国家地区」列标注；CSV 的「合并自」列可反查该节点由哪几份原始配置合并而来。

## 文件结构

```
.github/workflows/daily.yml   定时任务定义
pipeline.py                   主流程（Windows / Linux 通用）
requirements.txt              仅依赖 PyYAML
sub/clash.yaml                订阅文件（自动生成，勿手改）
sub/nodes.csv                 节点明细表（自动生成）
reports/                      每日测速报告
```

## 已知限制

- **定时延迟**：GitHub Actions 的 cron 采用 UTC，且高负载时实际触发可能比设定时间晚数分钟到数十分钟，这是平台行为，不是配置错误。
- **IPv6 节点**：GitHub 托管运行器通常没有 IPv6 出口，纯 IPv6 节点会被测为不可用，属于测试环境限制。
- **速度波动**：免费公共节点质量本身不稳定，同一节点在不同轮次可能从 5 Mbps 掉到 0.01 Mbps，单日结果仅供横向参考。
- **仓库活跃度**：GitHub 会停用长期无提交仓库的定时任务；本工作流每轮都会提交结果，因此可长期保持启用。
- **凭据**：工作流使用仓库自带的 `GITHUB_TOKEN`，无需另外配置 Secret。

## 手动触发

仓库页面 → Actions → `daily-subscription` → Run workflow。也可以本地运行：

```bash
pip install -r requirements.txt
python pipeline.py          # 输出到 out/ 目录
python pipeline.py --ci     # 输出到 sub/ 与 reports/
python pipeline.py --offline  # 使用上次抓取的缓存，跳过网络抓取
```
