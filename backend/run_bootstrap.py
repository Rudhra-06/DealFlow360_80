import os
import asyncio
from scripts.bootstrap_full_demo import bootstrap_demo

if __name__ == "__main__":
    os.environ["DEMO_USER_PASSWORD"] = "DealFlow360Demo123!"
    asyncio.run(bootstrap_demo())
