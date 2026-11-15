# 代理节点池订阅 · 每日自动整合

每天由 GitHub Actions 在云端自动运行：抓取公开节点池 → 去重 → 查询归属地 → 实测延迟与下载速度 → 生成三份可直接导入的订阅（Clash Meta / Shadowrocket / v2rayNG），并把结果提交回本仓库。

## 订阅地址一览

国内客户端建议用 jsDelivr 地址；`raw.githubusercontent.com` 在国内经常连不上。

| 客户端 | 订阅地址 | 节点数 |
|---|---|---|
| Clash Meta / mihomo | `https://cdn.jsdelivr.net/gh/Brianshau/proxy-sub@main/sub/clash.yaml` | 11 |
| Shadowrocket | `https://cdn.jsdelivr.net/gh/Brianshau/proxy-sub@main/sub/shadowrocket.txt` | 10 |
| v2rayNG | `https://cdn.jsdelivr.net/gh/Brianshau/proxy-sub@main/sub/v2rayng.txt` | 1 |

对应的原始地址分别为：

- `https://raw.githubusercontent.com/Brianshau/proxy-sub/main/sub/clash.yaml`
- `https://raw.githubusercontent.com/Brianshau/proxy-sub/main/sub/shadowrocket.txt`
- `https://raw.githubusercontent.com/Brianshau/proxy-sub/main/sub/v2rayng.txt`

补充文件：

| 文件 | 内容 |
|---|---|
| `sub/*-links.txt` | 对应订阅的明文，方便核对或扫码 |
| `sub/nodes.csv` | 逐节点测速明细，含国家地区与去重来源 |
| `sub/generic-links.txt` | 全协议链接清单，含实验性 `mierus://` |
| `reports/latest.md` | 最新测速排行 |
| `reports/client-compatibility.md` | 双客户端逐节点兼容性判定与依据 |

## 数据来源

上游为公开仓库 `free9999/ipupdate` 的 `backup/img/1/2/ipp` 目录，取其中四个文件夹：

- `clash.meta2`（6 份 config.yaml）
- `hysteria`（4 份 config.json）
- `hysteria2`（4 份 config.json）
- `quick`（4 份 config.yaml）

## 处理流程

1. **抓取**：走 GitLab raw 直链，遇到 429 限流自动重试，并回退到上次缓存。
2. **解析**：分别处理 Clash YAML、Hysteria v1 JSON、Hysteria2 JSON 三种格式。
3. **去重**：以「服务器 + 端口 + 认证口令 + SNI」四要素为唯一键。18 份配置合并为 11 个节点。
4. **归属地**：ip-api 批量查询为主，ipwho.is 兜底，结果缓存在 `geo_cache.json`。
5. **测速**：ICMP 往返延迟与丢包；再用 mihomo 实拨全部节点，测 204 握手延迟与 8 秒限时下载。
6. **输出**：Clash YAML 订阅、CSV 明细、每日测速报告，以及由 `link_export.py` 生成的两份分享链接订阅。

## 节点命名规则

节点名 = **来源文件夹名 + 两位序列号 + 国家/地区**，例如 `clash.meta2-03 🇫🇷法国` 表示来自 `clash.meta2` 文件夹、该文件夹内第 3 个节点，落地在法国。

- 序列号按文件夹各自独立递增，从 `01` 开始。
- 序号基于**去重后**的节点。`clash.meta2` 有 6 份配置、去重后仅 4 个节点，因此只到 `-04`。
- `sub/nodes.csv` 的「合并自」列可反查该节点由哪几份原始配置合并而来。

## 客户端兼容范围

| 协议 | 节点数 | Shadowrocket | v2rayNG |
|---|---|---|---|
| Hysteria v1 | 9 | 支持 | 不支持 |
| Hysteria2 | 1 | 支持（需 build ≥ 1993） | 支持 |
| mieru | 1 | 未证实 | 不支持 |

协议由服务端决定，转换脚本只搬运字段，无法把 v1 节点改写成 v2 协议。详细依据见 `reports/client-compatibility.md`。

## 文件结构

```
.github/workflows/daily.yml   定时任务定义
pipeline.py                   主流程（Windows / Linux 通用）
link_export.py                分享链接订阅生成（Shadowrocket / v2rayNG）
requirements.txt              仅依赖 PyYAML
sub/                          各客户端订阅文件（自动生成，勿手改）
reports/                      每日测速报告与兼容性说明
geo_cache.json                IP 归属地缓存
```

## 已知限制

- **定时延迟**：GitHub Actions 的 cron 采用 UTC，高负载时实际触发可能比设定时间晚数分钟到数十分钟。
- **IPv6 节点**：GitHub 托管运行器通常没有 IPv6 出口，纯 IPv6 节点在云端会被测为不可用；手机端也需要 IPv6 网络才能连接。
- **速度波动**：免费公共节点质量不稳定，同一节点在不同轮次可能从 5 Mbps 掉到 0.01 Mbps，单日结果仅供横向参考。
- **凭据**：工作流使用仓库自带的 `GITHUB_TOKEN`，无需配置额外 Secret。

## 手动触发与本地运行

仓库页面 → Actions → `daily-subscription` → Run workflow。本地运行：

```bash
pip install -r requirements.txt
python pipeline.py            # 输出到 out/ 目录
python pipeline.py --ci       # 输出到 sub/ 与 reports/
python pipeline.py --offline  # 使用上次抓取的缓存，跳过网络抓取
```

## 引用

Hysteria. "URI Scheme." *Hysteria Documentation*, v1.hysteria.network/docs/uri-scheme/, accessed 15 Nov. 2026.

Cedar2025. "Shadowrocket.php." *GitHub*, github.com/cedar2025/Xboard, accessed 15 Nov. 2026.

2dust. "AngConfigManager.kt." *GitHub*, github.com/2dust/v2rayNG, accessed 15 Nov. 2026.

Enfein. "Client Installation & Configuration." *GitHub*, github.com/enfein/mieru, accessed 15 Nov. 2026.
