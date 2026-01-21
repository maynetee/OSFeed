from typing import List, Dict, Any
import logging
import re
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.message import Message
from app.models.entity import Entity

logger = logging.getLogger(__name__)

class NERService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def extract_and_save(self, message: Message) -> Dict[str, List[str]]:
        """
        Extract entities from message text (translated preferred).
        Focus on Geopolitics: Persons, Organizations, Locations.
        """
        text = message.translated_text or message.original_text or ""
        if not text:
            return {}

        # 1. Heuristic Extraction (Fast, Zero-cost)
        entities_found = self._heuristic_extraction(text)
        
        # 2. Save to DB
        if entities_found:
            await self._save_entities(message, entities_found)
            
        return entities_found

    def _heuristic_extraction(self, text: str) -> Dict[str, List[str]]:
        """
        Basic regex-based extraction for obvious entities.
        """
        found = {
            "ORG": [],
            "LOC": [],
            "PER": []
        }
        
        pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b'
        matches = re.findall(pattern, text)
        
        for match in matches:
            if any(k in match for k in ["Organization", "Union", "Agency", "Group", "Party", "Army", "Force"]):
                found["ORG"].append(match)
            else:
                found["PER"].append(match)
                
        geopol_keywords = {
            "LOC": ["Ukraine", "Russia", "Gaza", "Israel", "Taiwan", "China", "USA", "Washington", "Kyiv", "Moscow", "Tehran"],
            "ORG": ["NATO", "UN", "EU", "IDF", "Hamas", "Hezbollah"]
        }
        
        for type_, keywords in geopol_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    found[type_].append(keyword)

        return found

    async def _save_entities(self, message: Message, entities: Dict[str, List[str]]):
        for type_, names in entities.items():
            for name in set(names):
                name = name.strip()
                if len(name) < 2: 
                    continue
                    
                stmt = select(Entity).where(
                    Entity.name == name,
                    Entity.type == type_
                )
                result = await self.session.execute(stmt)
                entity = result.scalar_one_or_none()
                
                if not entity:
                    entity = Entity(name=name, type=type_, frequency=1)
                    self.session.add(entity)
                    await self.session.flush()
                else:
                    entity.frequency += 1
                
                if entity not in message.entities_rel:
                    message.entities_rel.append(entity)
                    
        current_json = dict(message.entities or {})
        for k, v in entities.items():
            if k not in current_json:
                current_json[k] = []
            current_json[k] = list(set(current_json[k] + v))
        
        message.entities = current_json 
