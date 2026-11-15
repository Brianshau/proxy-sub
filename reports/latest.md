# 代理节点池每日整合 · 2026-11-15

- 生成时间：2026-11-15 04:44:33
- 数据源：https://gitlab.com/free9999/ipupdate
- 原始配置 **18** 份 → 去重后 **11** 个唯一节点（合并重复 7 项）
- 测速方式：ICMP 往返延迟 + mihomo 实拨（204 握手延迟 / 8 秒限时下载吞吐）

## 一、测速排行（按下载速率从高到低）

| 排名 | 节点 | 国家/地区 | 协议 | 握手延迟 | 下载速率 | 状态 |
|---|---|---|---|---|---|---|
| 1 | quick-02 | 🇺🇸 美国 | mieru | 456 ms | 83.5 Mbps | 可用 |
| 2 | quick-01 | 🇺🇸 美国 | hysteria | 1817 ms | 15.06 Mbps | 可用 |
| 3 | hysteria-01 | 🇺🇸 美国 | hysteria | 1233 ms | 3.5 Mbps | 可用 |
| 4 | clash.meta2-02 | 🇫🇷 法国 | hysteria | 1693 ms | — | 可用·速率未测出 |
| 5 | clash.meta2-01 | 🇫🇷 法国 | hysteria | 1872 ms | — | 可用·速率未测出 |
| 6 | hysteria-03 | 🇩🇪 德国 | hysteria | 1921 ms | — | 可用·速率未测出 |
| 7 | clash.meta2-03 | 🇫🇷 法国 | hysteria | — | — | 不可用 |
| 8 | clash.meta2-04 | 🇩🇪 德国 | hysteria | — | — | 不可用 |
| 9 | hysteria-02 | 🇺🇸 美国 | hysteria | — | — | 不可用 |
| 10 | hysteria2-01 | 🇫🇷 法国 | hysteria2 | — | — | 不可用 |
| 11 | quick-03 | 🇹🇼 中国台湾 | hysteria | — | — | 不可用 |

## 二、全部节点明细

| # | 国家/地区 | 协议 | 服务器 | 端口 | ICMP延迟 | 丢包 | 握手延迟 | 下载速率 | 来源 |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 🇫🇷 法国 | hysteria | `62.210.28.175` | 24667 | 153 ms | 0% | 1872 ms | — | clash.meta2 |
| 2 | 🇫🇷 法国 | hysteria | `163.172.117.163` | 36699 | 151 ms | 0% | 1693 ms | — | clash.meta2 |
| 3 | 🇫🇷 法国 | hysteria | `62.210.70.191` | 23556 | 161 ms | 0% | — | — | clash.meta2 |
| 4 | 🇩🇪 德国 | hysteria | `2a14:7584:d097::a` | 54177 | — | — | — | — | clash.meta2 |
| 5 | 🇺🇸 美国 | hysteria | `137.175.82.44` | 20022 | 20 ms | 0% | 1233 ms | 3.5 Mbps | hysteria |
| 6 | 🇺🇸 美国 | hysteria | `137.175.82.44` | 443 | 20 ms | 0% | — | — | hysteria |
| 7 | 🇩🇪 德国 | hysteria | `5.83.129.90` | 54177 | 160 ms | 0% | 1921 ms | — | hysteria |
| 8 | 🇫🇷 法国 | hysteria2 | `2001:bc8:32d7:17b::3` | 22000 | — | — | — | — | hysteria2 |
| 9 | 🇺🇸 美国 | hysteria | `198.200.57.142` | 22335 | 20 ms | 0% | 1817 ms | 15.06 Mbps | quick |
| 10 | 🇺🇸 美国 | mieru | `198.200.57.152` | 33556 | 20 ms | 0% | 456 ms | 83.5 Mbps | quick |
| 11 | 🇹🇼 中国台湾 | hysteria | `tw-25.497489.xyz` | 10099 | 3072 ms | 100% | — | — | quick |

## 三、去重记录

- `163.172.117.163:36699` = clash.meta2/2 + quick/1
- `62.210.70.191:23556` = clash.meta2/3 + clash.meta2/4
- `2a14:7584:d097::a:54177` = clash.meta2/5 + clash.meta2/6
- `5.83.129.90:54177` = hysteria/3 + hysteria/4
- `2001:bc8:32d7:17b::3:22000` = hysteria2/1 + hysteria2/2 + hysteria2/3 + hysteria2/4
