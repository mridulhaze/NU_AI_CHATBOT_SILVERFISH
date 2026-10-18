"""
Enrichment MCP Server
Provides standardized MCP tools for 24/7 knowledge analysis, enrichment telemetry, and inter-agent knowledge exchange.
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("NU_ENRICHMENT_MCP")

class EnrichmentMCPServer:
    def __init__(self):
        self._worker = None
        self._provenance = None

    @property
    def worker(self):
        if self._worker is None:
            from backend.agents.autonomous_24x7_worker import get_24x7_worker
            self._worker = get_24x7_worker()
        return self._worker

    @property
    def provenance(self):
        if self._provenance is None:
            from backend.agents.knowledge_provenance import get_knowledge_provenance
            self._provenance = get_knowledge_provenance()
        return self._provenance

    def get_enrichment_status(self) -> Dict[str, Any]:
        """
        MCP Tool: get_enrichment_status
        Returns 24/7 autonomous worker telemetry, total pages analyzed, and QA synthesized.
        """
        try:
            status = self.worker.get_status()
            return {"success": True, "data": status, "error": None}
        except Exception as e:
            logger.error(f"MCP get_enrichment_status error: {e}", exc_info=True)
            return {"success": False, "data": None, "error": {"code": "STATUS_FETCH_FAILED", "message": str(e)}}

    def get_recent_knowledge_updates(self, limit: int = 20) -> Dict[str, Any]:
        """
        MCP Tool: get_recent_knowledge_updates
        Allows any peer AI agent to retrieve recent structured knowledge additions.
        """
        try:
            updates = self.provenance.get_recent_updates_stream(limit=limit)
            return {"success": True, "data": updates, "count": len(updates), "error": None}
        except Exception as e:
            logger.error(f"MCP get_recent_knowledge_updates error: {e}", exc_info=True)
            return {"success": False, "data": None, "error": {"code": "UPDATES_FETCH_FAILED", "message": str(e)}}

    def get_knowledge_manifest(self) -> Dict[str, Any]:
        """
        MCP Tool: get_knowledge_manifest
        Returns the standardized machine-readable knowledge manifest.
        """
        try:
            manifest = self.provenance.get_manifest()
            return {"success": True, "data": manifest, "error": None}
        except Exception as e:
            logger.error(f"MCP get_knowledge_manifest error: {e}", exc_info=True)
            return {"success": False, "data": None, "error": {"code": "MANIFEST_FETCH_FAILED", "message": str(e)}}

    def trigger_enrichment_cycle(self, batch_size: int = 10) -> Dict[str, Any]:
        """
        MCP Tool: trigger_enrichment_cycle
        Triggers an immediate batch analysis and knowledge enrichment cycle.
        """
        try:
            result = self.worker.run_enrichment_cycle(batch_size=batch_size)
            return {"success": True, "data": result, "error": None}
        except Exception as e:
            logger.error(f"MCP trigger_enrichment_cycle error: {e}", exc_info=True)
            return {"success": False, "data": None, "error": {"code": "CYCLE_TRIGGER_FAILED", "message": str(e)}}

_enrichment_mcp_instance: Optional[EnrichmentMCPServer] = None

def get_enrichment_mcp_server() -> EnrichmentMCPServer:
    global _enrichment_mcp_instance
    if _enrichment_mcp_instance is None:
        _enrichment_mcp_instance = EnrichmentMCPServer()
    return _enrichment_mcp_instance
