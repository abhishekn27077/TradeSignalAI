import asyncio
from app.agents.providers.router import model_router

async def main():
    print("Registered providers:", model_router._providers.keys())
    health = await model_router.health_check_all()
    print("Health:", health)

asyncio.run(main())
