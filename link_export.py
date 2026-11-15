# -*- coding: utf-8 -*-
"""
把 Clash Meta 订阅里的节点转换成「分享链接」形式的订阅，同时产出多个客户端版本。

产出：
  sub/shadowrocket.txt          Shadowrocket 订阅（标准 Base64，每行一个链接）
  sub/shadowrocket-links.txt    上者明文
  sub/v2rayng.txt               v2rayNG 订阅（标准 Base64）
  sub/v2rayng-links.txt         上者明文
  sub/generic-links.txt         全协议链接清单（含实验性 mierus://）
  reports/client-compatibility.md  双客户端逐节点兼容性报告

事实依据（见报告末尾 MLA 引用）：
  - 订阅内容为 Base64 编码的 URI 列表，按行分隔。
  - Shadowrocket：Hysteria v1 的 hysteria:// URI Scheme 由 Shadowrocket 首创；
    第三方面板的 Shadowrocket 订阅生成器对 v1 用 hysteria://、对 v2 用 hysteria2://，
    且 v2 需要 Shadowrocket build 1993 及以上。
  - v2rayNG：订阅解析器只登记 hysteria2:// 与 hy2://，未登记 hysteria:// 与 mieru。
  - mieru：官方定义 mieru:// / mierus://，但未证实 Shadowrocket 订阅能解析，故不进主订阅。
"""
import base64
import os
import re
import urllib.parse

V2RAYNG_SCHEMES = {"hysteria2", "hy2"}


def wrap_host(server):
    """IPv6 地址必须加方括号，否则冒号会被当成端口分隔符。"""
    s = str(server).strip()
    if ":" in s and not s.startswith("["):
        return f"[{s}]"
    return s


def q(value):
    return urllib.parse.quote(str(value), safe="")


def mbps(value):
    m = re.search(r"(\d+(?:\.\d+)?)", str(value or ""))
    return m.group(1) if m else None


def insecure_flag(p):
    return "1" if p.get("skip-cert-verify") else "0"


def alpn_value(p):
    a = p.get("alpn")
    if not a:
        return None
    return a[0] if isinstance(a, list) else a


# ---------------------------------------------------------------- Hysteria v1
def hysteria1_link(p, for_shadowrocket=True):
    """Hysteria v1 官方 URI Scheme。

    hysteria://host:port?protocol=&auth=&peer=&insecure=&upmbps=&downmbps=&alpn=#remarks
    Shadowrocket 订阅生成器额外带的 fastopen 属于客户端优化项，源配置里没有，不写入。
    """
    params = [
        ("protocol", p.get("protocol") or "udp"),
        ("auth", p.get("auth-str") or ""),
        ("peer", p.get("sni") or ""),
        ("insecure", insecure_flag(p)),
        ("upmbps", mbps(p.get("up"))),
        ("downmbps", mbps(p.get("down"))),
    ]
    a = alpn_value(p)
    if a:
        params.append(("alpn", a))
    query = "&".join(f"{k}={q(v)}" for k, v in params if v not in (None, ""))
    return f"hysteria://{wrap_host(p['server'])}:{p['port']}?{query}#{q(p.get('name', ''))}"


# ---------------------------------------------------------------- Hysteria v2
def hysteria2_link(p, for_shadowrocket=True):
    """Hysteria2 链接。

    Shadowrocket 口径（Xboard 生成器）：hysteria2://password@host:port?peer=...&insecure=...
    v2rayNG 口径（Hysteria2Fmt）：hysteria2://password@host:port?sni=...&insecure=...
    两者仅 SNI 参数名不同，这里同时写出 peer 与 sni，任一端解析都取得到值；
    其余参数沿用各自实现中已出现的键名。
    """
    pwd = q(p.get("password") or p.get("auth") or "")
    params = [("peer", p.get("sni") or ""), ("sni", p.get("sni") or ""),
              ("insecure", insecure_flag(p))]
    a = alpn_value(p)
    if a:
        params.append(("alpn", a))
    up, down = mbps(p.get("up")), mbps(p.get("down"))
    if up:
        params.append(("upmbps", up))
    if down:
        params.append(("downmbps", down))
    if for_shadowrocket:
        params.append(("obfs", "none"))
    query = "&".join(f"{k}={q(v)}" for k, v in params if v not in (None, ""))
    return f"hysteria2://{pwd}@{wrap_host(p['server'])}:{p['port']}?{query}#{q(p.get('name', ''))}"


# ---------------------------------------------------------------- mieru
def mierus_link(p):
    """mieru 官方 simple sharing link：mierus://username:password@server?port=&protocol=

    该格式来自 mieru 官方客户端文档；未证实 Shadowrocket 订阅能解析，仅作实验性单列。
    """
    user = q(p.get("username") or "")
    pwd = q(p.get("password") or "")
    params = [("profile", "default"),
              ("port", str(p.get("port", ""))),
              ("protocol", q(p.get("transport") or "TCP")),
              ("multiplexing", q(p.get("multiplexing") or "MULTIPLEXING_LOW"))]
    query = "&".join(f"{k}={v}" for k, v in params)
    return f"mierus://{user}:{pwd}@{q(p.get('server', ''))}?{query}#{q(p.get('name', ''))}"


def write_pair(sub_dir, stem, links, header):
    plain = "\n".join(links)
    b64 = base64.b64encode(plain.encode("utf-8")).decode("ascii")
    with open(os.path.join(sub_dir, f"{stem}.txt"), "w", encoding="utf-8") as f:
        f.write(b64 + "\n")
    with open(os.path.join(sub_dir, f"{stem}-links.txt"), "w", encoding="utf-8") as f:
        f.write(header + "\n" + (plain + "\n" if plain else ""))
    return b64


def convert(proxies, out_root, generated, source_url):
    sub_dir = os.path.join(out_root, "sub")
    rep_dir = os.path.join(out_root, "reports")
    os.makedirs(sub_dir, exist_ok=True)
    os.makedirs(rep_dir, exist_ok=True)

    sr_links, v2_links, generic, rows = [], [], [], []
    for p in proxies:
        name, typ = p.get("name", ""), str(p.get("type", "")).lower()
        server, port = p.get("server", ""), p.get("port", "")
        if typ == "hysteria":
            sr_links.append(hysteria1_link(p))
            generic.append(hysteria1_link(p))
            rows.append((name, typ, server, port, "支持", "仅 v2rayNG 不支持",
                         "hysteria:// 由 Shadowrocket 首创"))
        elif typ == "hysteria2":
            sr = hysteria2_link(p, True)
            v2 = hysteria2_link(p, False)
            sr_links.append(sr)
            v2_links.append(v2)
            generic.append(v2)
            rows.append((name, typ, server, port, "支持（需 build≥1993）", "支持",
                         "hysteria2:// 两端格式仅 SNI 参数名不同"))
        else:
            generic.append(mierus_link(p))
            rows.append((name, typ, server, port, "未证实", "不支持",
                         "mieru 官方有 mierus://，但订阅导入未证实"))

    sr_head = (f"# Shadowrocket 分享链接（明文）\n# 生成时间: {generated}\n"
               f"# 源订阅: {source_url}\n# 可用节点: {len(sr_links)} / {len(proxies)}\n")
    v2_head = (f"# v2rayNG 分享链接（明文）\n# 生成时间: {generated}\n"
               f"# 源订阅: {source_url}\n# 可用节点: {len(v2_links)} / {len(proxies)}\n")
    write_pair(sub_dir, "shadowrocket", sr_links, sr_head)
    write_pair(sub_dir, "v2rayng", v2_links, v2_head)

    with open(os.path.join(sub_dir, "generic-links.txt"), "w", encoding="utf-8") as f:
        f.write("# 全协议链接清单（按各协议官方/通行 URI Scheme 生成）\n"
                "# mierus:// 为实验性，未证实客户端订阅导入\n"
                f"# 生成时间: {generated}\n\n" + "\n".join(generic) + "\n")

    lines = [
        "# 客户端链接版订阅 · 兼容性说明", "",
        f"- 生成时间：{generated}",
        f"- 源订阅：`{source_url}`",
        f"- 节点总数：**{len(proxies)}**；Shadowrocket 可用 **{len(sr_links)}**；"
        f"v2rayNG 可用 **{len(v2_links)}**", "",
        "## 逐节点判定", "",
        "| 节点名 | 协议 | 服务器 | 端口 | Shadowrocket | v2rayNG | 说明 |",
        "|---|---|---|---|---|---|---|",
    ]
    for name, typ, server, port, sr, v2, why in rows:
        lines.append(f"| {name} | {typ} | `{server}` | {port} | {sr} | {v2} | {why} |")
    lines += ["", "## 订阅格式与依据", "",
              "1. 两份订阅均为标准 Base64，解码后每行一条分享链接。",
              "2. Hysteria v1 的 `hysteria://` URI Scheme 由 Hysteria 官方文档说明，",
              "   文档明确该格式最初由 Shadowrocket 引入。",
              "3. 第三方面板的 Shadowrocket 订阅生成器对 v1 输出 `hysteria://`，",
              "   对 v2 输出 `hysteria2://`，并把 v2 的最低版本要求标为 build 1993。",
              "4. v2rayNG 的 `configFmtParsers` 只登记 `hysteria2://` / `hy2://`，",
              "   未登记 `hysteria://`；未登记的 scheme 在订阅导入时被跳过。",
              "5. mieru 官方文档定义 `mieru://` / `mierus://` 分享链接，",
              "   但 Shadowrocket 订阅能否解析未找到可验证依据，因此不写入主订阅。", "",
              "## 使用限制", "",
              "- 两个纯 IPv6 节点（`clash.meta2-04`、`hysteria2-01`）需要手机网络具备 IPv6 出口。",
              "- Hysteria2 节点要求 Shadowrocket build 1993 及以上；低版本会跳过该链接。",
              "- 本结论来自公开源码与官方文档核对，未在 iOS / Android 真机上实测导入与连通性。",
              "- 转换只搬运字段，不改变服务端协议；无法把 v1 节点改写成 v2 协议。", "",
              "## 引用（MLA）", "",
              "Hysteria. \"URI Scheme.\" *Hysteria Documentation*, v1.hysteria.network/docs/uri-scheme/,",
              "accessed 15 Nov. 2026.", "",
              "Cedar2025. \"Shadowrocket.php.\" *GitHub*, github.com/cedar2025/Xboard,",
              "accessed 15 Nov. 2026.", "",
              "2dust. \"AppConfig.kt.\" *GitHub*, github.com/2dust/v2rayNG, accessed 15 Nov. 2026.", "",
              "2dust. \"AngConfigManager.kt.\" *GitHub*, github.com/2dust/v2rayNG,",
              "accessed 15 Nov. 2026.", "",
              "2dust. \"EConfigType.kt.\" *GitHub*, github.com/2dust/v2rayNG,",
              "accessed 15 Nov. 2026.", "",
              "Enfein. \"Client Installation & Configuration.\" *GitHub*, github.com/enfein/mieru,",
              "accessed 15 Nov. 2026.", "",
              ]
    with open(os.path.join(rep_dir, "client-compatibility.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    return {"total": len(proxies), "shadowrocket": len(sr_links),
            "v2rayng": len(v2_links)}


if __name__ == "__main__":
    import json
    import sys
    from datetime import datetime
    import yaml
    src = sys.argv[1] if len(sys.argv) > 1 else "sub/clash.yaml"
    out = sys.argv[2] if len(sys.argv) > 2 else "."
    doc = yaml.safe_load(open(src, encoding="utf-8").read())
    r = convert(doc.get("proxies") or [], out,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "本地文件")
    print(json.dumps(r, ensure_ascii=False))
