"""
AION OS - Knowledge Base Module
Loads proprietary contract templates and legal reference data.

All data in aionos/knowledge/ is PROPRIETARY.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger("aionos.knowledge")

KNOWLEDGE_DIR = Path(__file__).parent


def load_contract_templates() -> List[Dict]:
    """Load all proprietary contract templates from knowledge/contracts/"""
    contracts_dir = KNOWLEDGE_DIR / "contracts"
    templates = []
    
    if not contracts_dir.exists():
        return templates
    
    for f in contracts_dir.glob("*.json"):
        try:
            data = json.loads(f.read_text(encoding='utf-8'))
            data["_filename"] = f.name
            templates.append(data)
            logger.info(f"Loaded contract template: {f.name}")
        except Exception as e:
            logger.warning(f"Failed to load {f.name}: {e}")
    
    return templates


def get_contract_template(name: str) -> Optional[Dict]:
    """Load a specific contract template by filename (without extension)"""
    path = KNOWLEDGE_DIR / "contracts" / f"{name}.json"
    if path.exists():
        return json.loads(path.read_text(encoding='utf-8'))
    return None


def list_templates() -> List[str]:
    """List all available contract template names"""
    contracts_dir = KNOWLEDGE_DIR / "contracts"
    if not contracts_dir.exists():
        return []
    return [f.stem for f in contracts_dir.glob("*.json")]
