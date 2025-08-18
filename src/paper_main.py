import asyncio
import yaml
from module.engine.paper_engine import PaperEngine

async def main():
    with open("config/paper_config.yaml", "r") as f:
        config = yaml.safe_load(f)

    engine = PaperEngine(config)
    await engine.run()

if __name__ == "__main__":
    asyncio.run(main())