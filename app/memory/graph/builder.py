import uuid
from typing import Any

from app.database.models.memory import KnowledgeEdge, KnowledgeNode


class GraphBuilder:
    """In-memory Knowledge Graph builder."""
    
    def __init__(self):
        self.nodes: dict[str, KnowledgeNode] = {}
        self.edges: list[KnowledgeEdge] = []
        
    def add_node(self, label: str, properties: dict[str, Any] = None) -> KnowledgeNode:
        """Adds or updates a node. Identifies duplicates by specific properties for MVP."""
        properties = properties or {}
        
        # Simple deduplication by 'name' or 'symbol'
        ident = properties.get('name') or properties.get('symbol')
        if ident:
            for n in self.nodes.values():
                if n.label == label and (n.properties.get('name') == ident or n.properties.get('symbol') == ident):
                    # Update properties
                    n.properties.update(properties)
                    return n
                    
        node_id = str(uuid.uuid4())
        node = KnowledgeNode(id=node_id, label=label, properties=properties)
        self.nodes[node_id] = node
        return node
        
    def add_edge(self, source_id: str, target_id: str, relation: str, properties: dict[str, Any] = None) -> KnowledgeEdge:
        properties = properties or {}
        
        # Deduplicate identical edges
        for e in self.edges:
            if e.source_id == source_id and e.target_id == target_id and e.relation_type == relation:
                e.properties.update(properties)
                e.weight += 1.0 # Strengthen relationship
                return e
                
        edge_id = str(uuid.uuid4())
        edge = KnowledgeEdge(id=edge_id, source_id=source_id, target_id=target_id, relation_type=relation, properties=properties)
        self.edges.append(edge)
        return edge

graph_builder = GraphBuilder()
