from typing import Any

from app.database.models.memory import KnowledgeNode
from app.memory.graph.builder import graph_builder


class GraphQuery:
    """Retrieves and traverses relationships in the Knowledge Graph."""
    
    @staticmethod
    def get_node(node_id: str) -> KnowledgeNode | None:
        return graph_builder.nodes.get(node_id)
        
    @staticmethod
    def find_nodes_by_label(label: str) -> list[KnowledgeNode]:
        return [n for n in graph_builder.nodes.values() if n.label == label]
        
    @staticmethod
    def get_related_nodes(node_id: str, relation_type: str = None) -> list[dict[str, Any]]:
        """
        Finds all nodes connected to the given node_id, optionally filtered by relation type.
        Returns a list of dicts: {"node": KnowledgeNode, "edge": KnowledgeEdge, "direction": "outbound"|"inbound"}
        """
        results = []
        for e in graph_builder.edges:
            if relation_type and e.relation_type != relation_type:
                continue
                
            if e.source_id == node_id:
                target = graph_builder.nodes.get(e.target_id)
                if target:
                    results.append({"node": target, "edge": e, "direction": "outbound"})
            elif e.target_id == node_id:
                source = graph_builder.nodes.get(e.source_id)
                if source:
                    results.append({"node": source, "edge": e, "direction": "inbound"})
                    
        # Sort by edge weight descending
        results.sort(key=lambda x: x["edge"].weight, reverse=True)
        return results

graph_query = GraphQuery()
