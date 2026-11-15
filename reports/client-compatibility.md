# 客户端链接版订阅 · 兼容性说明

- 生成时间：2026-11-15 05:03:50
- 源订阅：`https://cdn.jsdelivr.net/gh/Brianshau/proxy-sub@main/sub/clash.yaml`
- 节点总数：**11**；Shadowrocket 可用 **10**；v2rayNG 可用 **1**

## 逐节点判定

| 节点名 | 协议 | 服务器 | 端口 | Shadowrocket | v2rayNG | 说明 |
|---|---|---|---|---|---|---|
| clash.meta2-01 🇫🇷法国 | hysteria | `62.210.28.175` | 24667 | 支持 | 仅 v2rayNG 不支持 | hysteria:// 由 Shadowrocket 首创 |
| clash.meta2-02 🇫🇷法国 | hysteria | `163.172.117.163` | 36699 | 支持 | 仅 v2rayNG 不支持 | hysteria:// 由 Shadowrocket 首创 |
| clash.meta2-03 🇫🇷法国 | hysteria | `62.210.70.191` | 23556 | 支持 | 仅 v2rayNG 不支持 | hysteria:// 由 Shadowrocket 首创 |
| clash.meta2-04 🇩🇪德国 | hysteria | `2a14:7584:d097::a` | 54177 | 支持 | 仅 v2rayNG 不支持 | hysteria:// 由 Shadowrocket 首创 |
| hysteria-01 🇺🇸美国 | hysteria | `137.175.82.44` | 20022 | 支持 | 仅 v2rayNG 不支持 | hysteria:// 由 Shadowrocket 首创 |
| hysteria-02 🇺🇸美国 | hysteria | `137.175.82.44` | 443 | 支持 | 仅 v2rayNG 不支持 | hysteria:// 由 Shadowrocket 首创 |
| hysteria-03 🇩🇪德国 | hysteria | `5.83.129.90` | 54177 | 支持 | 仅 v2rayNG 不支持 | hysteria:// 由 Shadowrocket 首创 |
| hysteria2-01 🇫🇷法国 | hysteria2 | `2001:bc8:32d7:17b::3` | 22000 | 支持（需 build≥1993） | 支持 | hysteria2:// 两端格式仅 SNI 参数名不同 |
| quick-01 🇺🇸美国 | hysteria | `198.200.57.142` | 22335 | 支持 | 仅 v2rayNG 不支持 | hysteria:// 由 Shadowrocket 首创 |
| quick-02 🇺🇸美国 | mieru | `198.200.57.152` | 33556 | 未证实 | 不支持 | mieru 官方有 mierus://，但订阅导入未证实 |
| quick-03 🇹🇼中国台湾 | hysteria | `tw-25.497489.xyz` | 10099 | 支持 | 仅 v2rayNG 不支持 | hysteria:// 由 Shadowrocket 首创 |

## 订阅格式与依据

1. 两份订阅均为标准 Base64，解码后每行一条分享链接。
2. Hysteria v1 的 `hysteria://` URI Scheme 由 Hysteria 官方文档说明，
   文档明确该格式最初由 Shadowrocket 引入。
3. 第三方面板的 Shadowrocket 订阅生成器对 v1 输出 `hysteria://`，
   对 v2 输出 `hysteria2://`，并把 v2 的最低版本要求标为 build 1993。
4. v2rayNG 的 `configFmtParsers` 只登记 `hysteria2://` / `hy2://`，
   未登记 `hysteria://`；未登记的 scheme 在订阅导入时被跳过。
5. mieru 官方文档定义 `mieru://` / `mierus://` 分享链接，
   但 Shadowrocket 订阅能否解析未找到可验证依据，因此不写入主订阅。

## 使用限制

- 两个纯 IPv6 节点（`clash.meta2-04`、`hysteria2-01`）需要手机网络具备 IPv6 出口。
- Hysteria2 节点要求 Shadowrocket build 1993 及以上；低版本会跳过该链接。
- 本结论来自公开源码与官方文档核对，未在 iOS / Android 真机上实测导入与连通性。
- 转换只搬运字段，不改变服务端协议；无法把 v1 节点改写成 v2 协议。

## 引用（MLA）

Hysteria. "URI Scheme." *Hysteria Documentation*, v1.hysteria.network/docs/uri-scheme/,
accessed 15 Nov. 2026.

Cedar2025. "Shadowrocket.php." *GitHub*, github.com/cedar2025/Xboard,
accessed 15 Nov. 2026.

2dust. "AppConfig.kt." *GitHub*, github.com/2dust/v2rayNG, accessed 15 Nov. 2026.

2dust. "AngConfigManager.kt." *GitHub*, github.com/2dust/v2rayNG,
accessed 15 Nov. 2026.

2dust. "EConfigType.kt." *GitHub*, github.com/2dust/v2rayNG,
accessed 15 Nov. 2026.

Enfein. "Client Installation & Configuration." *GitHub*, github.com/enfein/mieru,
accessed 15 Nov. 2026.

