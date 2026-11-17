# 代理节点池每日整合 · 2026-11-17

- 生成时间：2026-11-17 00:59:48
- 数据源：https://gitlab.com/free9999/ipupdate
- 原始配置 **18** 份 → 去重后 **11** 个唯一节点（合并重复 7 项）
- 测速方式：ICMP 往返延迟 + mihomo 实拨（204 握手延迟 / 8 秒限时下载吞吐）

## 一、测速排行（按下载速率从高到低）

| 排名 | 节点 | 国家/地区 | 协议 | 握手延迟 | 下载速率 | 状态 |
|---|---|---|---|---|---|---|
| 1 | quick-02 | 🇺🇸 美国 | mieru | 552 ms | 157.78 Mbps | 可用 |
| 2 | clash.meta2-01 | 🇫🇷 法国 | hysteria | 1622 ms | 14.41 Mbps | 可用 |
| 3 | quick-01 | 🇺🇸 美国 | hysteria | 1628 ms | 0.01 Mbps | 可用·极慢 |
| 4 | clash.meta2-02 | 🇫🇷 法国 | hysteria | 1337 ms | — | 可用·速率未测出 |
| 5 | hysteria-03 | 🇩🇪 德国 | hysteria | 1434 ms | — | 可用·速率未测出 |
| 6 | clash.meta2-03 | 🇫🇷 法国 | hysteria | — | — | 不可用 |
| 7 | clash.meta2-04 | 🇩🇪 德国 | hysteria | — | — | 不可用 |
| 8 | hysteria-01 | 🇺🇸 美国 | hysteria | — | — | 不可用 |
| 9 | hysteria-02 | 🇺🇸 美国 | hysteria | — | — | 不可用 |
| 10 | hysteria2-01 | 🇫🇷 法国 | hysteria2 | — | — | 不可用 |
| 11 | quick-03 | 🇹🇼 中国台湾 | hysteria | — | — | 不可用 |

## 二、全部节点明细

| # | 国家/地区 | 协议 | 服务器 | 端口 | ICMP延迟 | 丢包 | 握手延迟 | 下载速率 | 来源 |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 🇫🇷 法国 | hysteria | `62.210.28.175` | 24667 | 3053 ms | 100% | 1622 ms | 14.41 Mbps | clash.meta2 |
| 2 | 🇫🇷 法国 | hysteria | `163.172.117.163` | 36699 | 3053 ms | 100% | 1337 ms | — | clash.meta2 |
| 3 | 🇫🇷 法国 | hysteria | `62.210.70.191` | 23556 | 3053 ms | 100% | — | — | clash.meta2 |
| 4 | 🇩🇪 德国 | hysteria | `2a14:7584:d097::a` | 54177 | — | — | — | — | clash.meta2 |
| 5 | 🇺🇸 美国 | hysteria | `137.175.82.44` | 20022 | 3051 ms | 100% | — | — | hysteria |
| 6 | 🇺🇸 美国 | hysteria | `137.175.82.44` | 443 | 3053 ms | 100% | — | — | hysteria |
| 7 | 🇩🇪 德国 | hysteria | `5.83.129.90` | 54177 | 3053 ms | 100% | 1434 ms | — | hysteria |
| 8 | 🇫🇷 法国 | hysteria2 | `2001:bc8:32d7:17b::3` | 22000 | — | — | — | — | hysteria2 |
| 9 | 🇺🇸 美国 | hysteria | `198.200.57.142` | 22335 | 3051 ms | 100% | 1628 ms | 0.01 Mbps | quick |
| 10 | 🇺🇸 美国 | mieru | `198.200.57.152` | 33556 | 3053 ms | 100% | 552 ms | 157.78 Mbps | quick |
| 11 | 🇹🇼 中国台湾 | hysteria | `tw-25.497489.xyz` | 10099 | 3105 ms | 100% | — | — | quick |

## 三、去重记录

- `163.172.117.163:36699` = clash.meta2/2 + quick/1
- `62.210.70.191:23556` = clash.meta2/3 + clash.meta2/4
- `2a14:7584:d097::a:54177` = clash.meta2/5 + clash.meta2/6
- `5.83.129.90:54177` = hysteria/3 + hysteria/4
- `2001:bc8:32d7:17b::3:22000` = hysteria2/1 + hysteria2/2 + hysteria2/3 + hysteria2/4
