# -*- coding: utf-8 -*-
"""
代理节点池每日整合订阅 (跨平台版: Windows 本地 / Linux CI 通用)

数据源: https://gitlab.com/free9999/ipupdate  backup/img/1/2/ipp/{clash.meta2,hysteria,hysteria2,quick}
流程  : 抓取 -> 解析 -> 去重 -> 归属地 -> ICMP + mihomo 实拨测速 -> 输出订阅与清单

本地用法: python pipeline.py
CI  用法: python pipeline.py --ci      # 输出到 sub/ 与 reports/
"""
import json
import os
import re
import socket
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime

import yaml

IS_WIN = os.name == "nt"
ROOT = os.path.dirname(os.path.abspath(__file__))

BASE = "https://gitlab.com/free9999/ipupdate/-/raw/master/backup/img/1/2/ipp"
FOLDERS = {
    "clash.meta2": ("config.yaml", [1, 2, 3, 4, 5, 6]),
    "hysteria":    ("config.json", [1, 2, 3, 4]),
    "hysteria2":   ("config.json", [1, 2, 3, 4]),
    "quick":       ("config.yaml", [1, 2, 3, 4]),
}

CN_NAME = {
    "FR": "法国", "US": "美国", "JP": "日本", "SG": "新加坡", "HK": "中国香港",
    "TW": "中国台湾", "KR": "韩国", "DE": "德国", "NL": "荷兰", "GB": "英国",
    "CA": "加拿大", "AU": "澳大利亚", "RU": "俄罗斯", "IN": "印度", "TR": "土耳其",
    "BR": "巴西", "IT": "意大利", "SE": "瑞典", "CH": "瑞士", "FI": "芬兰",
    "PL": "波兰", "UA": "乌克兰", "VN": "越南", "TH": "泰国", "MY": "马来西亚",
    "ID": "印度尼西亚", "PH": "菲律宾", "AE": "阿联酋", "IL": "以色列", "ES": "西班牙",
}


# ------------------------------------------------------------------ 抓取
def http_get(url, retries=6, wait=18):
    last = ""
    for _ in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=60) as r:
                txt = r.read().decode("utf-8", "ignore")
            if "Rate limit exceeded" in txt:
                last = "rate-limited"
                time.sleep(wait)
                continue
            return txt
        except Exception as e:  # noqa: BLE001
            last = str(e)
            time.sleep(wait)
    print(f"  [warn] fetch failed {url} ({last})", file=sys.stderr)
    return None


def fetch_all(offline=False, cache_dir=None):
    cache_dir = cache_dir or os.path.join(ROOT, "raw")
    os.makedirs(cache_dir, exist_ok=True)
    fetched = {}
    for folder, (fname, idxs) in FOLDERS.items():
        for i in idxs:
            key = f"{folder}/{i}"
            path = os.path.join(cache_dir, f"{folder}_{i}{os.path.splitext(fname)[1]}")
            if offline:
                if os.path.exists(path):
                    fetched[key] = open(path, encoding="utf-8").read()
                continue
            txt = http_get(f"{BASE}/{folder}/{i}/{fname}")
            if txt is None:
                if os.path.exists(path):
                    txt = open(path, encoding="utf-8").read()
                    print(f"  fallback-cache {key}")
                else:
                    continue
            open(path, "w", encoding="utf-8").write(txt)
            fetched[key] = txt
            print(f"  ok {key} ({len(txt)}B)")
            time.sleep(2)
    return fetched


# ------------------------------------------------------------------ 解析
def split_server(s):
    s = (s or "").strip()
    if s.startswith("["):
        host, _, rest = s.partition("]")
        return host.lstrip("["), int((rest.lstrip(":") or "0").split(":")[0] or 0)
    if s.count(":") == 1:
        h, _, p = s.partition(":")
        return h, int(p or 0)
    return s, 0


def parse_clash_proxies(text):
    try:
        doc = yaml.safe_load(text)
    except Exception as e:  # noqa: BLE001
        print(f"  [warn] yaml parse: {e}", file=sys.stderr)
        return []
    if not isinstance(doc, dict):
        return []
    return [dict(p) for p in (doc.get("proxies") or [])
            if isinstance(p, dict) and p.get("server") and p.get("type")]


def parse_hysteria1(doc):
    server, port = split_server(doc.get("server", ""))
    p = {
        "name": "hysteria", "type": "hysteria", "server": server, "port": port,
        "auth-str": doc.get("auth_str") or doc.get("auth", ""),
        "sni": doc.get("server_name", ""),
        "skip-cert-verify": bool(doc.get("insecure", True)),
        "alpn": [doc.get("alpn")] if isinstance(doc.get("alpn"), str) else (doc.get("alpn") or ["h3"]),
        "protocol": doc.get("protocol", "udp"),
        "up": f'{doc.get("up_mbps", 0)} Mbps', "down": f'{doc.get("down_mbps", 0)} Mbps',
    }
    if doc.get("obfs"):
        p["obfs"] = doc["obfs"]
    return p


def parse_hysteria2(doc):
    server, port = split_server(doc.get("server", ""))
    bw = doc.get("bandwidth") or {}
    tls = doc.get("tls") or {}
    p = {
        "name": "hysteria2", "type": "hysteria2", "server": server, "port": port,
        "password": doc.get("auth", ""), "sni": tls.get("sni", ""),
        "skip-cert-verify": bool(tls.get("insecure", True)),
        "up": bw.get("up", ""), "down": bw.get("down", ""),
    }
    obfs = (doc.get("obfs") or {}).get("type")
    if obfs:
        p["obfs"] = obfs
        p["obfs-password"] = (doc.get("obfs") or {}).get("password", "")
    return p


def node_key(p):
    auth = p.get("auth-str") or p.get("password") or p.get("username") or ""
    return (str(p.get("server", "")).lower(), int(p.get("port") or 0),
            str(auth), str(p.get("sni") or "").lower())


# ------------------------------------------------------------------ 归属地
def resolve(host):
    try:
        ips = [i[4][0] for i in socket.getaddrinfo(host, None)]
        v4 = [i for i in dict.fromkeys(ips) if ":" not in i]
        return (v4 or list(dict.fromkeys(ips)) or [host])[0]
    except Exception:  # noqa: BLE001
        return host


GEO_CACHE = os.path.join(ROOT, "geo_cache.json")


def load_geo_cache():
    try:
        return json.load(open(GEO_CACHE, encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}


def geo_one_ipwhois(ip):
    """ip-api 失败时的兜底查询（https，支持 IPv6）"""
    try:
        req = urllib.request.Request(f"https://ipwho.is/{urllib.parse.quote(ip)}",
                                     headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=20) as r:
            d = json.loads(r.read().decode())
        if d.get("success"):
            return {"status": "success", "country": d.get("country", ""),
                    "countryCode": d.get("country_code", ""),
                    "city": d.get("city", ""), "isp": d.get("connection", {}).get("isp", ""),
                    "query": ip}
    except Exception:  # noqa: BLE001
        pass
    return None


def geo_batch(ips):
    cache = load_geo_cache()
    uniq = [i for i in dict.fromkeys(ips) if i]
    need = [i for i in uniq if i not in cache]

    for chunk in [need[i:i + 90] for i in range(0, len(need), 90)]:
        payload = json.dumps([{"query": ip} for ip in chunk]).encode()
        req = urllib.request.Request(
            "http://ip-api.com/batch?fields=status,country,countryCode,city,isp,query",
            data=payload, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=45) as r:
                for item in json.loads(r.read().decode()):
                    if item.get("status") == "success":
                        cache[item["query"]] = item
        except Exception as e:  # noqa: BLE001
            print(f"  [warn] ip-api 批量查询失败: {e}", file=sys.stderr)
        time.sleep(2)

    # 批量失败或漏查的，逐条兜底
    for ip in need:
        if ip in cache:
            continue
        item = geo_one_ipwhois(ip)
        if item:
            cache[ip] = item
            print(f"  [geo] {ip} -> {item.get('countryCode')} (ipwho.is 兜底)")
        time.sleep(0.5)

    try:
        json.dump(cache, open(GEO_CACHE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    except Exception:  # noqa: BLE001
        pass
    return {ip: cache.get(ip, {}) for ip in uniq}


# ------------------------------------------------------------------ 延迟
def ping(host, count=4):
    is_v6 = ":" in host
    if IS_WIN:
        cmd = ["ping", "-n", str(count), "-w", "1500"]
        if is_v6:
            cmd.append("-6")
        cmd.append(host)
        enc = "gbk"
    else:
        cmd = ["ping", "-c", str(count), "-W", "2"]
        if is_v6:
            cmd.append("-6")
        cmd.append(host)
        enc = "utf-8"
    try:
        p = subprocess.run(cmd, capture_output=True, timeout=60)
        out = (p.stdout or b"").decode(enc, "ignore") + (p.stderr or b"").decode(enc, "ignore")
    except Exception:  # noqa: BLE001
        return None, None
    loss = avg = None
    m = re.search(r"(\d+)%", out)
    if m:
        loss = int(m.group(1))
    m = re.search(r"(?:平均|Average)\s*=\s*(\d+)\s*ms", out)
    if m:
        avg = int(m.group(1))
    else:
        m = re.search(r"rtt [^=]*=\s*[\d.]+/([\d.]+)/", out)
        if m:
            avg = round(float(m.group(1)))
        else:
            m = re.search(r"(\d+)\s*ms", out)
            if m:
                avg = int(m.group(1))
    return avg, loss


# ------------------------------------------------------------------ mihomo 实拨
API_PORT = 9099
MIX_PORT = 7899
SECRET = "bench"
TEST_URLS = ["https://speed.cloudflare.com/__down?bytes=25000000",
             "http://cachefly.cachefly.net/20mb.test"]


def api(path, method="GET", body=None):
    req = urllib.request.Request(
        f"http://127.0.0.1:{API_PORT}{path}",
        data=json.dumps(body).encode() if body is not None else None,
        method=method,
        headers={"Authorization": f"Bearer {SECRET}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read().decode() or "{}")


def measure_download(seconds=8):
    best = None
    for url in TEST_URLS:
        cmd = ["curl", "-s", "-o", os.devnull, "--max-time", str(seconds),
               "--proxy", f"http://127.0.0.1:{MIX_PORT}",
               "-w", "%{speed_download}", url]
        try:
            p = subprocess.run(cmd, capture_output=True, timeout=seconds + 15)
            mbps = round(float((p.stdout or b"0").decode().strip() or 0) * 8 / 1e6, 2)
            if mbps > (best or 0):
                best = mbps
            if mbps > 1:
                break
        except Exception:  # noqa: BLE001
            continue
    return best


def mihomo_speedtest(nodes, workdir):
    binary = os.environ.get("MIHOMO_BIN") or os.path.join(
        ROOT, "mihomo.exe" if IS_WIN else "mihomo")
    if not os.path.exists(binary):
        binary = "mihomo"
    os.makedirs(workdir, exist_ok=True)

    proxies, name_of = [], {}
    for idx, n in enumerate(nodes, 1):
        if n["type"] not in ("hysteria", "hysteria2", "mieru"):
            continue
        p = dict(n["proxy"])
        p["name"] = f"T{idx:02d}"
        proxies.append(p)
        name_of[n["key"]] = p["name"]
    if not proxies:
        return {}

    cfg = {
        "mixed-port": MIX_PORT, "allow-lan": False, "log-level": "info", "mode": "rule",
        "external-controller": f"127.0.0.1:{API_PORT}", "secret": SECRET,
        "dns": {"enable": True, "nameserver": ["223.5.5.5", "119.29.29.29"]},
        "proxies": proxies,
        "proxy-groups": [{"name": "TEST", "type": "select", "proxies": [p["name"] for p in proxies]}],
        "rules": ["MATCH,TEST"],
    }
    cfg_path = os.path.join(workdir, "cfg.yaml")
    open(cfg_path, "w", encoding="utf-8").write(
        yaml.safe_dump(cfg, allow_unicode=True, sort_keys=False))

    log = open(os.path.join(workdir, "mihomo.log"), "w", encoding="utf-8", errors="ignore")
    proc = subprocess.Popen([binary, "-d", workdir, "-f", cfg_path],
                            stdout=log, stderr=subprocess.STDOUT)
    ready = False
    for _ in range(25):
        time.sleep(1)
        if proc.poll() is not None:
            break
        try:
            api("/version")
            ready = True
            break
        except Exception:  # noqa: BLE001
            continue
    if not ready:
        print("  [warn] mihomo 未就绪，跳过实拨测速", file=sys.stderr)
        proc.kill()
        log.close()
        return {}

    result = {}
    try:
        for n in nodes:
            nm = name_of.get(n["key"])
            if not nm:
                continue
            try:
                api("/proxies/TEST", method="PUT", body={"name": nm})
            except Exception as e:  # noqa: BLE001
                print(f"    [warn] switch {nm}: {e}")
                continue
            time.sleep(0.5)
            delay = None
            for _try in range(2):
                for probe in ("http://www.gstatic.com/generate_204",
                              "http://cp.cloudflare.com/generate_204"):
                    try:
                        r = api(f"/proxies/{urllib.parse.quote(nm)}"
                                f"/delay?timeout=8000&url={probe}")
                        if r.get("delay"):
                            delay = r["delay"]
                            break
                    except Exception:  # noqa: BLE001
                        continue
                if delay:
                    break
            speed = measure_download() if delay else None
            result[n["key"]] = {"delay": delay, "mbps": speed}
            print(f"    {nm} {n['server'][:24]:24s} delay={delay} speed={speed}")
    finally:
        try:
            proc.terminate()
            proc.wait(timeout=8)
        except Exception:  # noqa: BLE001
            proc.kill()
        log.close()
    return result


# ------------------------------------------------------------------ 渲染
def fmt_flag(cc):
    if not cc or len(cc) != 2:
        return "🏳️"
    return chr(0x1F1E6 + ord(cc[0]) - 65) + chr(0x1F1E6 + ord(cc[1]) - 65)


def status_of(e):
    if e.get("pdelay") is None:
        return "不可用"
    if not e.get("mbps"):
        return "可用·速率未测出"
    if e["mbps"] < 0.5:
        return "可用·极慢"
    return "可用"


def build_subscription(entries):
    proxies = []
    for e in entries:
        p = dict(e["proxy"])
        # 命名规则：文件夹名-两位序列号 + 国家/地区，如 clash.meta2-03 🇫🇷法国
        p["name"] = f'{e["tag"]} {fmt_flag(e.get("countryCode"))}{e.get("country_cn", "")}'
        proxies.append(p)
    names = [p["name"] for p in proxies]
    return {
        "mixed-port": 7890, "allow-lan": False, "mode": "rule", "log-level": "info",
        "proxies": proxies,
        "proxy-groups": [
            {"name": "🚀 节点选择", "type": "select",
             "proxies": ["♻️ 自动选择", "DIRECT"] + names},
            {"name": "♻️ 自动选择", "type": "url-test",
             "url": "http://www.gstatic.com/generate_204", "interval": 300,
             "tolerance": 50, "proxies": names},
        ],
        "rules": ["MATCH,🚀 节点选择"],
    }


def render_md(entries, meta, ranked):
    L = [f"# 代理节点池每日整合 · {meta['date']}", "",
         f"- 生成时间：{meta['generated']}",
         f"- 数据源：{meta['source']}",
         f"- 原始配置 **{meta['raw_count']}** 份 → 去重后 **{len(entries)}** 个唯一节点"
         f"（合并重复 {meta['dup']} 项）",
         "- 测速方式：ICMP 往返延迟 + mihomo 实拨（204 握手延迟 / 8 秒限时下载吞吐）", "",
         "## 一、测速排行（按下载速率从高到低）", "",
         "| 排名 | 节点 | 国家/地区 | 协议 | 握手延迟 | 下载速率 | 状态 |",
         "|---|---|---|---|---|---|---|"]
    for i, e in enumerate(ranked, 1):
        L.append("| {} | {} | {} {} | {} | {} | {} | {} |".format(
            i, e["tag"], fmt_flag(e.get("countryCode")), e.get("country_cn", ""), e["type"],
            f'{e["pdelay"]} ms' if e.get("pdelay") is not None else "—",
            f'{e["mbps"]} Mbps' if e.get("mbps") else "—", status_of(e)))
    L += ["", "## 二、全部节点明细", "",
          "| # | 国家/地区 | 协议 | 服务器 | 端口 | ICMP延迟 | 丢包 | 握手延迟 | 下载速率 | 来源 |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    for i, e in enumerate(entries, 1):
        L.append("| {} | {} {} | {} | `{}` | {} | {} | {} | {} | {} | {} |".format(
            i, fmt_flag(e.get("countryCode")), e.get("country_cn", ""), e["type"],
            e["server"], e["port"],
            f'{e["icmp"]} ms' if e.get("icmp") is not None else "—",
            f'{e["loss"]}%' if e.get("loss") is not None else "—",
            f'{e["pdelay"]} ms' if e.get("pdelay") is not None else "—",
            f'{e["mbps"]} Mbps' if e.get("mbps") else "—", e.get("origin", "")))
    dups = [f"- `{e['server']}:{e['port']}` = " + " + ".join(e["origins"])
            for e in entries if len(e["origins"]) > 1]
    L += ["", "## 三、去重记录", ""] + (dups or ["- 本轮无重复项"])
    return "\n".join(L) + "\n"


def render_csv(entries):
    cols = ["序号", "国家地区", "国家代码", "协议", "服务器", "端口", "SNI", "认证",
            "ICMP延迟ms", "丢包%", "握手延迟ms", "下载Mbps", "状态", "来源", "合并自"]
    lines = [",".join(cols)]
    for i, e in enumerate(entries, 1):
        row = [i, e.get("country_cn", ""), e.get("countryCode", ""), e["type"], e["server"],
               e["port"], e.get("sni", ""), e.get("auth", ""), e.get("icmp", ""),
               e.get("loss", ""), e.get("pdelay", ""), e.get("mbps", ""),
               status_of(e), e.get("origin", ""), "|".join(e.get("origins", []))]
        lines.append(",".join('"%s"' % str(x).replace('"', "'") for x in row))
    return "\n".join(lines) + "\n"


# ------------------------------------------------------------------ 主流程
def main():
    ci = "--ci" in sys.argv
    offline = "--offline" in sys.argv
    date_str = datetime.now().strftime("%Y-%m-%d")

    print("[1/5] 抓取源配置 ...")
    fetched = fetch_all(offline=offline)
    print(f"  取得 {len(fetched)} 份配置")

    print("[2/5] 解析并去重 ...")
    nodes, seen, dup = [], {}, 0
    for key, txt in fetched.items():
        folder = key.split("/")[0]
        if folder == "hysteria":
            try:
                plist = [parse_hysteria1(json.loads(txt))]
            except Exception:  # noqa: BLE001
                plist = []
        elif folder == "hysteria2":
            try:
                plist = [parse_hysteria2(json.loads(txt))]
            except Exception:  # noqa: BLE001
                plist = []
        else:
            plist = parse_clash_proxies(txt)
        for p in plist:
            k = node_key(p)
            if k in seen:
                dup += 1
                seen[k]["origins"].append(key)
                continue
            rec = {"key": k, "type": p["type"], "server": p["server"], "port": p["port"],
                   "sni": p.get("sni", ""),
                   "auth": p.get("auth-str") or p.get("password") or "",
                   "origin": folder, "origins": [key], "proxy": p}
            seen[k] = rec
            nodes.append(rec)
    print(f"  合并 {dup} 个重复项，剩 {len(nodes)} 个唯一节点")

    print("[3/5] 归属地 ...")
    for n in nodes:
        n["ip"] = resolve(n["server"])
    geo = geo_batch([n["ip"] for n in nodes])
    for n in nodes:
        g = geo.get(n["ip"], {})
        n["countryCode"] = g.get("countryCode", "")
        n["country_cn"] = CN_NAME.get(n["countryCode"], g.get("country", "未知"))
        time.sleep(0.2)

    print("[4/5] ICMP 延迟 ...")
    for n in nodes:
        n["icmp"], n["loss"] = ping(n["server"])
        print(f"  {n['server']:34s} icmp={n['icmp']} loss={n['loss']}")

    print("[5/5] mihomo 实拨测速 ...")
    st = mihomo_speedtest(nodes, os.path.join(ROOT, "mihomo_home"))
    for n in nodes:
        r = st.get(n["key"], {})
        n["pdelay"], n["mbps"] = r.get("delay"), r.get("mbps")

    # 命名规则：来源文件夹名 + 该文件夹内两位序列号，如 clash.meta2-03
    counter = {}
    for n in nodes:
        f = n["origin"]
        counter[f] = counter.get(f, 0) + 1
        n["tag"] = f"{f}-{counter[f]:02d}"

    sub = build_subscription(nodes)
    ranked = sorted(nodes, key=lambda x: (-(x.get("mbps") or -1),
                                          x.get("pdelay") if x.get("pdelay") is not None else 99999))
    meta = {"date": date_str, "generated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "source": "https://gitlab.com/free9999/ipupdate",
            "raw_count": len(fetched), "dup": dup}

    head = (f"# 代理节点池每日整合订阅\n# 生成时间: {meta['generated']}\n"
            f"# 来源: {meta['source']}\n"
            f"# {meta['raw_count']} 份配置 -> 去重后 {len(nodes)} 个节点\n")
    sub_yaml = head + yaml.safe_dump(sub, allow_unicode=True, sort_keys=False)
    md = render_md(nodes, meta, ranked)
    csv = render_csv(nodes)

    if ci:
        os.makedirs(os.path.join(ROOT, "sub"), exist_ok=True)
        os.makedirs(os.path.join(ROOT, "reports"), exist_ok=True)
        open(os.path.join(ROOT, "sub", "clash.yaml"), "w", encoding="utf-8").write(sub_yaml)
        open(os.path.join(ROOT, "sub", "nodes.csv"), "w", encoding="utf-8-sig").write(csv)
        open(os.path.join(ROOT, "reports", f"{date_str}.md"), "w", encoding="utf-8").write(md)
        open(os.path.join(ROOT, "reports", "latest.md"), "w", encoding="utf-8").write(md)
        print("  已写入 sub/clash.yaml 与 reports/")
    else:
        day = os.path.join(ROOT, "out", date_str)
        os.makedirs(day, exist_ok=True)
        open(os.path.join(ROOT, "out", "clash_订阅.yaml"), "w", encoding="utf-8").write(sub_yaml)
        open(os.path.join(day, "节点清单.md"), "w", encoding="utf-8").write(md)
        open(os.path.join(day, "节点清单.csv"), "w", encoding="utf-8-sig").write(csv)
        print(f"  已写入 out/")

    # 同步生成分享链接版订阅（Shadowrocket / v2rayNG）
    try:
        import link_export
        export_root = ROOT if ci else os.path.join(ROOT, "out")
        r = link_export.convert(
            sub["proxies"], export_root, meta["generated"],
            "https://cdn.jsdelivr.net/gh/Brianshau/proxy-sub@main/sub/clash.yaml")
        print(f"  链接版: Shadowrocket {r['shadowrocket']}/{r['total']}，"
              f"v2rayNG {r['v2rayng']}/{r['total']}")
    except Exception as e:  # noqa: BLE001
        print(f"  [warn] 链接版生成失败: {e}", file=sys.stderr)

    alive = sum(1 for n in nodes if n.get("pdelay"))
    print(f"\n完成: {len(nodes)} 个节点，可用 {alive} 个")
    if alive == 0:
        print("[warn] 本轮全部节点不可用，可能触发源站故障或网络中断", file=sys.stderr)


if __name__ == "__main__":
    main()
