from fastapi import APIRouter, Body

from app.logs.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/memory", tags=["memory"])


@router.post("/search", summary="Search Memory")
async def search_memory(query: str = Body(default=""), limit: int = Body(default=20)):
    try:
        from app.memory.manager import memory_manager
        results = await memory_manager.search(query, limit=limit) if hasattr(memory_manager, "search") else []
        return {"success": True, "results": results, "count": len(results)}
    except Exception as e:
        logger.warning(f"Memory search error: {e}")
        return {"success": True, "results": [], "count": 0}


@router.get("/statistics", summary="Get Memory Statistics")
async def memory_statistics():
    try:
        from app.memory.manager import memory_manager
        stats = await memory_manager.get_statistics() if hasattr(memory_manager, "get_statistics") else {}
        return {"success": True, "data": stats}
    except Exception as e:
        logger.warning(f"Memory statistics error: {e}")
        return {"success": True, "data": {}}


@router.get("/graph/node/{node_id}", summary="Get Knowledge Graph Node")
async def get_graph_node(node_id: str):
    try:
        from app.memory.graph.query import graph_query
        node = await graph_query.get_node(node_id) if hasattr(graph_query, "get_node") else None
        if node is None:
            return {"success": False, "message": f"Node {node_id} not found"}
        return {"success": True, "node": node}
    except Exception as e:
        logger.warning(f"Graph node error: {e}")
        return {"success": False, "message": str(e)}


@router.get("/graph", summary="Get Knowledge Graph")
async def get_graph():
    try:
        from app.memory.graph.query import graph_query
        graph = await graph_query.get_full_graph() if hasattr(graph_query, "get_full_graph") else {}
        return {"success": True, "data": graph}
    except Exception as e:
        logger.warning(f"Graph error: {e}")
        return {"success": True, "data": {}}