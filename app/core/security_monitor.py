"""
Security Monitoring and Incident Response for Arbify
===================================================

Comprehensive security monitoring including:
- Real-time threat detection
- Security event aggregation
- Automated incident response
- Security metrics dashboard
"""

import os
import json
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
from enum import Enum

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.responses import JSONResponse

# Security logger
security_logger = logging.getLogger("security.monitor")

class ThreatLevel(Enum):
    """Security threat levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class IncidentStatus(Enum):
    """Security incident status"""
    OPEN = "open"
    INVESTIGATING = "investigating"
    MITIGATED = "mitigated"
    RESOLVED = "resolved"

@dataclass
class SecurityEvent:
    """Security event data structure"""
    id: str
    timestamp: datetime
    event_type: str
    threat_level: ThreatLevel
    source_ip: str
    user_agent: str
    endpoint: str
    description: str
    metadata: Dict[str, Any]
    user_id: Optional[int] = None
    resolved: bool = False

@dataclass
class SecurityIncident:
    """Security incident data structure"""
    id: str
    created_at: datetime
    incident_type: str
    threat_level: ThreatLevel
    status: IncidentStatus
    description: str
    affected_users: List[str]
    source_ips: List[str]
    events: List[str]  # Event IDs
    mitigation_actions: List[str]
    resolved_at: Optional[datetime] = None

class SecurityMonitor:
    """Real-time security monitoring system"""
    
    def __init__(self):
        self.events: deque = deque(maxlen=10000)  # Keep last 10k events
        self.incidents: Dict[str, SecurityIncident] = {}
        self.metrics: Dict[str, Any] = defaultdict(int)
        self.blocked_ips: set = set()
        self.suspicious_ips: Dict[str, int] = defaultdict(int)
        
        # Threat detection rules
        self.setup_threat_rules()
        
        # Start background monitoring
        self.monitoring_active = True
    
    def setup_threat_rules(self):
        """Setup automated threat detection rules"""
        self.threat_rules = {
            # Multiple failed login attempts
            "brute_force": {
                "pattern": "login_failed",
                "threshold": 5,
                "window": 300,  # 5 minutes
                "action": "block_ip",
                "threat_level": ThreatLevel.HIGH
            },
            
            # Rapid API requests
            "rate_limit_abuse": {
                "pattern": "rate_limit_exceeded", 
                "threshold": 10,
                "window": 600,  # 10 minutes
                "action": "temporary_block",
                "threat_level": ThreatLevel.MEDIUM
            },
            
            # SQL injection attempts
            "sql_injection": {
                "pattern": "sql_injection_attempt",
                "threshold": 1,
                "window": 60,
                "action": "immediate_block",
                "threat_level": ThreatLevel.CRITICAL
            },
            
            # XSS attempts
            "xss_attack": {
                "pattern": "xss_attempt",
                "threshold": 1,
                "window": 60,
                "action": "immediate_block", 
                "threat_level": ThreatLevel.HIGH
            },
            
            # Suspicious user agent patterns
            "bot_detection": {
                "pattern": "suspicious_user_agent",
                "threshold": 3,
                "window": 300,
                "action": "investigate",
                "threat_level": ThreatLevel.MEDIUM
            },
            
            # Admin endpoint access
            "admin_access": {
                "pattern": "admin_access_attempt",
                "threshold": 3,
                "window": 600,
                "action": "alert",
                "threat_level": ThreatLevel.HIGH
            }
        }
    
    def log_event(self, event_type: str, source_ip: str, user_agent: str = "", 
                  endpoint: str = "", description: str = "", metadata: Dict = None,
                  user_id: int = None, threat_level: ThreatLevel = ThreatLevel.LOW):
        """Log a security event"""
        
        event = SecurityEvent(
            id=f"evt_{len(self.events)}_{int(datetime.utcnow().timestamp())}",
            timestamp=datetime.utcnow(),
            event_type=event_type,
            threat_level=threat_level,
            source_ip=source_ip,
            user_agent=user_agent[:200],  # Truncate long user agents
            endpoint=endpoint,
            description=description,
            metadata=metadata or {},
            user_id=user_id
        )
        
        self.events.append(event)
        self.metrics[f"event_{event_type}"] += 1
        self.metrics["total_events"] += 1
        
        # Log to file
        security_logger.info(f"SECURITY_EVENT: {json.dumps(asdict(event), default=str)}")
        
        # Check for threats
        self.check_threat_rules(event)
        
        return event.id
    
    def check_threat_rules(self, event: SecurityEvent):
        """Check if event triggers any threat detection rules"""
        for rule_name, rule in self.threat_rules.items():
            if self.matches_pattern(event, rule["pattern"]):
                # Count occurrences in time window
                count = self.count_events_in_window(
                    event.source_ip,
                    rule["pattern"], 
                    rule["window"]
                )
                
                if count >= rule["threshold"]:
                    self.trigger_incident(rule_name, event, rule)
    
    def matches_pattern(self, event: SecurityEvent, pattern: str) -> bool:
        """Check if event matches a threat pattern"""
        return event.event_type == pattern
    
    def count_events_in_window(self, source_ip: str, pattern: str, window_seconds: int) -> int:
        """Count events from an IP matching pattern in time window"""
        cutoff = datetime.utcnow() - timedelta(seconds=window_seconds)
        
        count = 0
        for event in self.events:
            if (event.source_ip == source_ip and 
                event.event_type == pattern and 
                event.timestamp > cutoff):
                count += 1
        
        return count
    
    def trigger_incident(self, rule_name: str, triggering_event: SecurityEvent, rule: Dict):
        """Trigger a security incident"""
        incident_id = f"inc_{rule_name}_{int(datetime.utcnow().timestamp())}"
        
        incident = SecurityIncident(
            id=incident_id,
            created_at=datetime.utcnow(),
            incident_type=rule_name,
            threat_level=rule["threat_level"],
            status=IncidentStatus.OPEN,
            description=f"Threat detected: {rule_name} from {triggering_event.source_ip}",
            affected_users=[str(triggering_event.user_id)] if triggering_event.user_id else [],
            source_ips=[triggering_event.source_ip],
            events=[triggering_event.id],
            mitigation_actions=[]
        )
        
        self.incidents[incident_id] = incident
        
        # Execute automated response
        self.execute_response_action(incident, rule["action"], triggering_event)
        
        # Log incident
        security_logger.warning(f"SECURITY_INCIDENT: {json.dumps(asdict(incident), default=str)}")
        
        return incident_id
    
    def execute_response_action(self, incident: SecurityIncident, action: str, event: SecurityEvent):
        """Execute automated incident response action"""
        if action == "block_ip":
            self.block_ip(event.source_ip, reason=f"Incident: {incident.incident_type}")
            incident.mitigation_actions.append(f"Blocked IP: {event.source_ip}")
        
        elif action == "temporary_block":
            self.temporary_block_ip(event.source_ip, duration=3600)  # 1 hour
            incident.mitigation_actions.append(f"Temporarily blocked IP: {event.source_ip}")
        
        elif action == "immediate_block":
            self.block_ip(event.source_ip, reason=f"Critical threat: {incident.incident_type}")
            incident.mitigation_actions.append(f"Immediately blocked IP: {event.source_ip}")
        
        elif action == "investigate":
            self.suspicious_ips[event.source_ip] += 1
            incident.mitigation_actions.append(f"Marked IP for investigation: {event.source_ip}")
        
        elif action == "alert":
            # In production, send alert to security team
            security_logger.critical(f"SECURITY_ALERT: {incident.description}")
            incident.mitigation_actions.append("Security team alerted")
    
    def block_ip(self, ip: str, reason: str = "Security violation"):
        """Permanently block an IP address"""
        self.blocked_ips.add(ip)
        security_logger.warning(f"IP blocked: {ip} - Reason: {reason}")
    
    def temporary_block_ip(self, ip: str, duration: int):
        """Temporarily block an IP address"""
        # In production, implement with Redis/cache with TTL
        self.blocked_ips.add(ip)
        
        # Schedule unblock (simplified)
        async def unblock_later():
            await asyncio.sleep(duration)
            if ip in self.blocked_ips:
                self.blocked_ips.remove(ip)
                security_logger.info(f"Temporary block expired for IP: {ip}")
        
        asyncio.create_task(unblock_later())
        security_logger.warning(f"IP temporarily blocked: {ip} for {duration}s")
    
    def is_ip_blocked(self, ip: str) -> bool:
        """Check if an IP is blocked"""
        return ip in self.blocked_ips
    
    def get_security_metrics(self) -> Dict[str, Any]:
        """Get comprehensive security metrics"""
        now = datetime.utcnow()
        
        # Recent events (last 24 hours)
        recent_events = [
            e for e in self.events 
            if (now - e.timestamp).total_seconds() < 86400
        ]
        
        # Active incidents
        active_incidents = [
            i for i in self.incidents.values()
            if i.status in [IncidentStatus.OPEN, IncidentStatus.INVESTIGATING]
        ]
        
        # Threat level distribution
        threat_levels = defaultdict(int)
        for event in recent_events:
            threat_levels[event.threat_level.value] += 1
        
        return {
            "total_events": len(self.events),
            "recent_events_24h": len(recent_events),
            "active_incidents": len(active_incidents),
            "blocked_ips": len(self.blocked_ips),
            "suspicious_ips": len(self.suspicious_ips),
            "threat_levels": dict(threat_levels),
            "top_threat_sources": self.get_top_threat_sources(),
            "metrics": dict(self.metrics),
            "last_updated": now.isoformat()
        }
    
    def get_top_threat_sources(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top threat source IPs"""
        ip_counts = defaultdict(int)
        
        for event in self.events:
            if event.threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]:
                ip_counts[event.source_ip] += 1
        
        sorted_ips = sorted(ip_counts.items(), key=lambda x: x[1], reverse=True)
        
        return [
            {"ip": ip, "threat_count": count}
            for ip, count in sorted_ips[:limit]
        ]
    
    def get_recent_incidents(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get recent security incidents"""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        
        recent = [
            asdict(incident) for incident in self.incidents.values()
            if incident.created_at > cutoff
        ]
        
        return sorted(recent, key=lambda x: x["created_at"], reverse=True)
    
    def resolve_incident(self, incident_id: str, resolution_notes: str = ""):
        """Resolve a security incident"""
        if incident_id in self.incidents:
            incident = self.incidents[incident_id]
            incident.status = IncidentStatus.RESOLVED
            incident.resolved_at = datetime.utcnow()
            
            if resolution_notes:
                incident.mitigation_actions.append(f"Resolution: {resolution_notes}")
            
            security_logger.info(f"Incident resolved: {incident_id}")
            return True
        
        return False

# Global security monitor instance
security_monitor = SecurityMonitor()

# API router for security monitoring
router = APIRouter(prefix="/security", tags=["Security Monitoring"])

@router.get("/dashboard")
async def security_dashboard():
    """Get security monitoring dashboard data"""
    return security_monitor.get_security_metrics()

@router.get("/incidents")
async def get_security_incidents(hours: int = 24):
    """Get recent security incidents"""
    return {
        "incidents": security_monitor.get_recent_incidents(hours),
        "total_count": len(security_monitor.incidents)
    }

@router.post("/incidents/{incident_id}/resolve")
async def resolve_incident(incident_id: str, resolution_notes: str = ""):
    """Resolve a security incident"""
    if security_monitor.resolve_incident(incident_id, resolution_notes):
        return {"message": "Incident resolved successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found"
        )

@router.get("/blocked-ips")
async def get_blocked_ips():
    """Get list of blocked IPs"""
    return {
        "blocked_ips": list(security_monitor.blocked_ips),
        "count": len(security_monitor.blocked_ips)
    }

@router.post("/unblock-ip")
async def unblock_ip(ip: str):
    """Manually unblock an IP address"""
    if ip in security_monitor.blocked_ips:
        security_monitor.blocked_ips.remove(ip)
        security_logger.info(f"IP manually unblocked: {ip}")
        return {"message": f"IP {ip} unblocked successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="IP not found in blocked list"
        )

@router.get("/events")
async def get_security_events(limit: int = 100, threat_level: str = None):
    """Get recent security events"""
    events = list(security_monitor.events)
    
    # Filter by threat level if specified
    if threat_level:
        try:
            level = ThreatLevel(threat_level.lower())
            events = [e for e in events if e.threat_level == level]
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid threat level"
            )
    
    # Return most recent events
    events = events[-limit:] if len(events) > limit else events
    events.reverse()  # Most recent first
    
    return {
        "events": [asdict(event) for event in events],
        "total_count": len(security_monitor.events)
    }

# Helper functions for integration
def log_security_event(event_type: str, source_ip: str, **kwargs):
    """Helper function to log security events"""
    return security_monitor.log_event(event_type, source_ip, **kwargs)

def is_ip_blocked(ip: str) -> bool:
    """Helper function to check if IP is blocked"""
    return security_monitor.is_ip_blocked(ip)

# Export classes and functions
__all__ = [
    'SecurityMonitor',
    'security_monitor',
    'ThreatLevel',
    'IncidentStatus',
    'SecurityEvent',
    'SecurityIncident',
    'router',
    'log_security_event',
    'is_ip_blocked'
]
