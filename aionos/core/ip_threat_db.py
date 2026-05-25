"""
AION OS — Local IP Threat Intelligence Database
100% OFFLINE. Zero API calls. Zero cloud dependencies.

This is a curated, locally-stored database of:
- Known proxy/VPN/Tor IP ranges
- ISP classification data
- Geolocation by IP range (CIDR)
- Residential proxy indicators
- Threat scoring rules

Updated via secure offline file drops — never phones home.
"""

import ipaddress
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

logger = logging.getLogger("aionos.ip_threat_db")


# =============================================================================
# ENUMS & DATA CLASSES
# =============================================================================

class ProxyType(Enum):
    """Classification of proxy/anonymization type"""
    NONE = "none"
    VPN = "vpn"
    TOR = "tor"
    RESIDENTIAL_PROXY = "residential_proxy"
    DATACENTER_PROXY = "datacenter_proxy"
    PUBLIC_PROXY = "public_proxy"
    WEB_PROXY = "web_proxy"
    UNKNOWN_PROXY = "unknown_proxy"


class ThreatCategory(Enum):
    """IP threat classification categories"""
    CLEAN = "clean"
    LOW_RISK = "low_risk"
    MEDIUM_RISK = "medium_risk"
    HIGH_RISK = "high_risk"
    CRITICAL = "critical"
    KNOWN_MALICIOUS = "known_malicious"


class ISPType(Enum):
    """ISP classification"""
    RESIDENTIAL = "residential"
    BUSINESS = "business"
    DATACENTER = "datacenter"
    MOBILE = "mobile"
    EDUCATION = "education"
    GOVERNMENT = "government"
    UNKNOWN = "unknown"


@dataclass
class IPRecord:
    """Complete intelligence record for an IP address"""
    ip: str
    # Geolocation
    country: str = "Unknown"
    country_code: str = "--"
    region: str = "Unknown"
    city: str = "Unknown"
    zip_code: str = ""
    latitude: float = 0.0
    longitude: float = 0.0
    # Network info
    isp: str = "Unknown"
    isp_type: ISPType = ISPType.UNKNOWN
    asn: str = ""
    domain: str = ""
    net_speed: str = ""
    # Proxy/anonymization
    is_proxy: bool = False
    proxy_type: ProxyType = ProxyType.NONE
    is_anonymous: bool = False
    # Threat intel
    threat_category: ThreatCategory = ThreatCategory.CLEAN
    threat_score: int = 0  # 0-100
    threat_reasons: List[str] = field(default_factory=list)
    # Metadata
    first_seen: str = ""
    last_seen: str = ""
    confidence: float = 0.0  # 0.0-1.0
    raw_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CIDREntry:
    """A CIDR range entry in the local database"""
    network: str  # e.g. "97.96.0.0/14"
    isp: str = ""
    isp_type: ISPType = ISPType.UNKNOWN
    country_code: str = ""
    region: str = ""
    city: str = ""
    asn: str = ""
    domain: str = ""


# =============================================================================
# LOCAL THREAT INTELLIGENCE DATABASE
# =============================================================================

class LocalIPThreatDB:
    """
    Fully offline IP threat intelligence database.
    
    NO NETWORK CALLS. All lookups use local data:
    - Curated CIDR-to-ISP mappings
    - Known proxy/VPN ranges
    - Threat indicator patterns
    - Geolocation by IP range
    
    Data is loaded from local JSON files or built-in defaults.
    """

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or Path(__file__).parent.parent / "data" / "ip_intel"
        
        # Core databases (in-memory)
        self._cidr_entries: List[Tuple[ipaddress.IPv4Network, CIDREntry]] = []
        self._known_proxies: Dict[str, ProxyType] = {}
        self._threat_indicators: Dict[str, Dict] = {}
        self._manual_entries: Dict[str, IPRecord] = {}
        
        # Load built-in intelligence
        self._load_builtin_intel()
        
        # Load external data files if available
        if self.db_path.exists():
            self._load_external_data()

    def _load_builtin_intel(self):
        """Load curated, built-in threat intelligence. Pure Python, no I/O."""
        
        # =================================================================
        # MAJOR US ISP CIDR RANGES
        # These are publicly documented IP allocations
        # =================================================================
        
        isp_ranges = [
            # Charter/Spectrum
            ("97.96.0.0/14", "Charter Communications Inc", ISPType.RESIDENTIAL, "US", "spectrum.com", "AS11427"),
            ("24.0.0.0/12", "Charter Communications Inc", ISPType.RESIDENTIAL, "US", "spectrum.com", "AS11427"),
            ("71.56.0.0/13", "Charter Communications Inc", ISPType.RESIDENTIAL, "US", "spectrum.com", "AS11427"),
            ("66.188.0.0/14", "Charter Communications Inc", ISPType.RESIDENTIAL, "US", "spectrum.com", "AS11427"),
            
            # Comcast/Xfinity
            ("73.0.0.0/8", "Comcast Cable Communications", ISPType.RESIDENTIAL, "US", "comcast.net", "AS7922"),
            ("98.192.0.0/10", "Comcast Cable Communications", ISPType.RESIDENTIAL, "US", "comcast.net", "AS7922"),
            ("50.128.0.0/9", "Comcast Cable Communications", ISPType.RESIDENTIAL, "US", "comcast.net", "AS7922"),
            
            # AT&T
            ("107.128.0.0/10", "AT&T Internet Services", ISPType.RESIDENTIAL, "US", "att.net", "AS7018"),
            ("99.0.0.0/11", "AT&T Internet Services", ISPType.RESIDENTIAL, "US", "att.net", "AS7018"),
            
            # Verizon
            ("100.0.0.0/10", "Verizon Business", ISPType.BUSINESS, "US", "verizon.com", "AS701"),
            ("108.0.0.0/11", "Verizon Business", ISPType.RESIDENTIAL, "US", "verizon.com", "AS701"),
            
            # T-Mobile
            ("172.32.0.0/11", "T-Mobile USA", ISPType.MOBILE, "US", "t-mobile.com", "AS21928"),
            
            # AWS
            ("3.0.0.0/9", "Amazon Web Services", ISPType.DATACENTER, "US", "amazonaws.com", "AS16509"),
            ("54.0.0.0/8", "Amazon Web Services", ISPType.DATACENTER, "US", "amazonaws.com", "AS16509"),
            ("52.0.0.0/8", "Amazon Web Services", ISPType.DATACENTER, "US", "amazonaws.com", "AS16509"),
            
            # Google Cloud
            ("35.192.0.0/12", "Google Cloud", ISPType.DATACENTER, "US", "google.com", "AS15169"),
            ("34.64.0.0/10", "Google Cloud", ISPType.DATACENTER, "US", "google.com", "AS15169"),
            
            # Microsoft Azure
            ("40.64.0.0/10", "Microsoft Azure", ISPType.DATACENTER, "US", "microsoft.com", "AS8075"),
            ("20.0.0.0/8", "Microsoft Azure", ISPType.DATACENTER, "US", "microsoft.com", "AS8075"),
            
            # DigitalOcean
            ("167.71.0.0/16", "DigitalOcean", ISPType.DATACENTER, "US", "digitalocean.com", "AS14061"),
            ("134.209.0.0/16", "DigitalOcean", ISPType.DATACENTER, "US", "digitalocean.com", "AS14061"),
            
            # Known VPN providers
            ("185.159.156.0/22", "NordVPN", ISPType.DATACENTER, "PA", "nordvpn.com", ""),
            ("146.70.0.0/16", "Mullvad VPN", ISPType.DATACENTER, "SE", "mullvad.net", ""),
            ("198.54.128.0/17", "Private Internet Access", ISPType.DATACENTER, "US", "privateinternetaccess.com", ""),
        ]
        
        for cidr, isp, isp_type, cc, domain, asn in isp_ranges:
            try:
                network = ipaddress.IPv4Network(cidr, strict=False)
                entry = CIDREntry(
                    network=cidr, isp=isp, isp_type=isp_type,
                    country_code=cc, domain=domain, asn=asn
                )
                self._cidr_entries.append((network, entry))
            except ValueError:
                continue
        
        # Sort by prefix length (most specific first)
        self._cidr_entries.sort(key=lambda x: x[0].prefixlen, reverse=True)

        # =================================================================
        # KNOWN PROXY / VPN INDICATORS
        # =================================================================
        
        proxy_domains = {
            "nordvpn.com": ProxyType.VPN,
            "expressvpn.com": ProxyType.VPN,
            "mullvad.net": ProxyType.VPN,
            "privateinternetaccess.com": ProxyType.VPN,
            "surfshark.com": ProxyType.VPN,
            "cyberghostvpn.com": ProxyType.VPN,
            "protonvpn.com": ProxyType.VPN,
            "torproject.org": ProxyType.TOR,
            "luminati.io": ProxyType.RESIDENTIAL_PROXY,
            "brightdata.com": ProxyType.RESIDENTIAL_PROXY,
            "smartproxy.com": ProxyType.RESIDENTIAL_PROXY,
            "oxylabs.io": ProxyType.RESIDENTIAL_PROXY,
            "stormproxies.com": ProxyType.RESIDENTIAL_PROXY,
        }
        self._known_proxies = proxy_domains

        # =================================================================
        # TEXAS / HOUSTON REGIONAL DATA (for the active case)
        # =================================================================
        
        # Specific IPs can be added via manual entry or data file
        # This is where case-specific intelligence goes

    def _load_external_data(self):
        """Load additional threat intel from local JSON files."""
        intel_file = self.db_path / "ip_intel.json"
        if intel_file.exists():
            try:
                data = json.loads(intel_file.read_text(encoding="utf-8"))
                for entry in data.get("manual_entries", []):
                    ip = entry.get("ip", "")
                    if ip:
                        self._manual_entries[ip] = IPRecord(
                            ip=ip,
                            country=entry.get("country", "Unknown"),
                            country_code=entry.get("country_code", "--"),
                            region=entry.get("region", "Unknown"),
                            city=entry.get("city", "Unknown"),
                            isp=entry.get("isp", "Unknown"),
                            is_proxy=entry.get("is_proxy", False),
                            threat_score=entry.get("threat_score", 0),
                            raw_data=entry,
                        )
                logger.info(f"Loaded {len(self._manual_entries)} manual IP entries")
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Failed to load external IP data: {e}")

    def add_manual_entry(self, record: IPRecord):
        """Add a manually enriched IP record (e.g., from a screenshot, OSINT)."""
        self._manual_entries[record.ip] = record
        logger.info(f"Added manual IP entry: {record.ip}")

    def lookup(self, ip_str: str) -> IPRecord:
        """
        Look up an IP address against all local databases.
        100% OFFLINE — no network calls.
        """
        # Check manual entries first (highest confidence)
        if ip_str in self._manual_entries:
            record = self._manual_entries[ip_str]
            record.confidence = 1.0
            return record

        # Parse IP
        try:
            ip_obj = ipaddress.IPv4Address(ip_str)
        except (ValueError, ipaddress.AddressValueError):
            return IPRecord(ip=ip_str, threat_category=ThreatCategory.CLEAN)

        # CIDR range lookup
        record = IPRecord(ip=ip_str)
        
        for network, entry in self._cidr_entries:
            if ip_obj in network:
                record.isp = entry.isp
                record.isp_type = entry.isp_type
                record.country_code = entry.country_code
                record.domain = entry.domain
                record.asn = entry.asn
                record.confidence = 0.7
                break

        # Check if ISP domain is known proxy provider
        if record.domain in self._known_proxies:
            record.is_proxy = True
            record.proxy_type = self._known_proxies[record.domain]
            record.is_anonymous = True

        # Run threat scoring
        record = self._score_threat(record)
        
        return record

    def _score_threat(self, record: IPRecord) -> IPRecord:
        """
        Calculate threat score based on local indicators.
        All logic runs locally — no external calls.
        """
        score = 0
        reasons = []

        # Proxy/anonymization indicators
        if record.is_proxy:
            if record.proxy_type == ProxyType.TOR:
                score += 40
                reasons.append("TOR exit node detected")
            elif record.proxy_type == ProxyType.RESIDENTIAL_PROXY:
                score += 35
                reasons.append("Residential proxy — likely compromised device relay")
            elif record.proxy_type == ProxyType.VPN:
                score += 20
                reasons.append("Commercial VPN detected")
            elif record.proxy_type in (ProxyType.DATACENTER_PROXY, ProxyType.PUBLIC_PROXY):
                score += 30
                reasons.append(f"Proxy detected: {record.proxy_type.value}")
            else:
                score += 25
                reasons.append("Anonymous proxy detected")

        if record.is_anonymous:
            score += 15
            reasons.append("Anonymous proxy flag active")

        # ISP type analysis
        if record.isp_type == ISPType.DATACENTER:
            score += 10
            reasons.append("Datacenter IP — not typical for human users")
        elif record.isp_type == ISPType.RESIDENTIAL:
            # Residential IPs used as proxies are MORE suspicious
            if record.is_proxy:
                score += 15
                reasons.append("Residential IP operating as proxy — possible botnet/compromised device")

        # Time-based factors
        if record.last_seen:
            reasons.append(f"Last observed: {record.last_seen}")

        # Cap at 100
        score = min(score, 100)
        record.threat_score = score
        record.threat_reasons = reasons

        # Classify
        if score >= 80:
            record.threat_category = ThreatCategory.CRITICAL
        elif score >= 60:
            record.threat_category = ThreatCategory.HIGH_RISK
        elif score >= 40:
            record.threat_category = ThreatCategory.MEDIUM_RISK
        elif score >= 20:
            record.threat_category = ThreatCategory.LOW_RISK
        else:
            record.threat_category = ThreatCategory.CLEAN

        return record

    def get_stats(self) -> Dict[str, int]:
        """Return database statistics."""
        return {
            "cidr_ranges": len(self._cidr_entries),
            "known_proxy_domains": len(self._known_proxies),
            "manual_entries": len(self._manual_entries),
        }
