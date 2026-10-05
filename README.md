
> **Outil multi-tâches en Python** : DDoS · BruteForce · OSINT · Utilitaires réseau

---

## ⚠️ AVERTISSEMENT LÉGAL — À LIRE IMPÉRATIVEMENT

**RED CAT est un outil de cybersécurité éducatif destiné uniquement à :**

- ✅ **Tester vos propres machines et serveurs**
- ✅ **Tester des systèmes pour lesquels vous disposez d'une autorisation écrite explicite**
- ✅ **Apprendre les principes de la cybersécurité dans un cadre légal**

**IL EST STRICTEMENT INTERDIT D'UTILISER CET OUTIL POUR :**

- ❌ Attaquer des systèmes sans autorisation
- ❌ Nuire à des tiers
- ❌ Toute activité illégale

### 🛑 Clause de non-responsabilité

**L'auteur de RED CAT décline toute responsabilité quant à l'utilisation qui pourrait être faite de cet outil. En téléchargeant, installant ou exécutant ce logiciel, vous acceptez l'entière responsabilité de vos actes.**

L'utilisation d'outils d'attaque réseau contre des systèmes non autorisés est **ILLÉGALE** dans la plupart des pays et peut entraîner :
- Des poursuites pénales
- Des amendes
- De la prison
- La confiscation de votre matériel

**Utilisez RED CAT de manière responsable, éthique et légale.**

---

## 📋 Fonctionnalités

### 🔥 DDoS (Tests de charge)
| # | Fonction | Description |
|---|----------|-------------|
| 01 | **Request Flood** | Envoi massif de requêtes HTTP (GET/POST) |
| 02 | **Synflood** | Flood TCP SYN avec spoofing d'IP (nécessite root) |
| 03 | **Pyslow** | Attaque Slowloris (connexions lentes persistantes) |
| 04 | **UDP Flood** | Envoi massif de paquets UDP |

### 🔓 BruteForce
| # | Fonction | Description |
|---|----------|-------------|
| 05 | **Formulaire HTML** | Force brute de formulaires de connexion |
| 06 | **API JSON** | Force brute d'API avec payload JSON |

**Caractéristiques :**
- Bypass automatique des tokens CSRF
- Détection de 2FA
- Détection de lockout
- Détection de rate limiting (429)
- Support proxy
- Retry automatique
- Concurrence asynchrone (aiohttp)

### 🔍 OSINT (Open Source Intelligence)
| # | Fonction | Description |
|---|----------|-------------|
| 07 | **Shodan** | Recherche d'infos sur IP/domaines (clé API requise) |
| 08 | **WiGLE WiFi** | Recherche de réseaux WiFi (clé API requise) |
| 09 | **NumLook** | Infos sur numéros de téléphone internationaux |
| 10 | **VirusTotal** | Analyse de fichiers/URLs/IPs (clé API requise) |
| 11 | **Géolocalisation** | Localisation géographique d'une IP |
| 12 | **MAC Address** | Identification du fabricant d'une carte réseau |
| 13 | **EXIF Data** | Extraction de métadonnées d'images |
| 14 | **YouTube Downloader** | Téléchargement de vidéos/audio YouTube |
| 15 | **Crypto Trace** | Suivi d'adresses Bitcoin |
| 16 | **Sherlock** | Recherche de comptes sur 12+ réseaux sociaux |
| 17 | **SearchFace** | Analyse faciale (âge, genre, ethnie, émotion) |

### 🛠️ Utilitaires réseau
| # | Fonction | Description |
|---|----------|-------------|
| 18 | **Port Scanner** | Scan des ports TCP ouverts |
| 19 | **Subdomain Finder** | Recherche de sous-domaines |
| 20 | **DNS Lookup** | Enregistrements DNS (A, MX, NS, TXT, CNAME) |
| 21 | **Whois Lookup** | Informations WHOIS d'un domaine |
| 22 | **Password Generator** | Génération de mots de passe forts |
| 23 | **Hash Generator** | Calcul MD5, SHA1, SHA256 |
| 24 | **IP Tracker** | Traçage complet d'une IP |
| 25 | **MC IP Finder** | Trouve l'IP d'un serveur Minecraft |
| 26 | **Find Domain IP** | Trouve l'IP et les ports ouverts d'un domaine |

---

## 📦 Installation

### 🐧 Linux / Termux (Android)

```bash
pkg update -y && pkg upgrade -y
pkg install -y python python-pip git openssl libxml2 libxslt whois dnsutils net-tools
python -m pip install --upgrade pip
python -m pip install aiohttp beautifulsoup4 tqdm colorama termcolor requests shodan phonenumbers vt-py exifread yt-dlp ipinfo mac-vendor-lookup dnspython opencv-python pillow
