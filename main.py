from dotenv import load_dotenv

load_dotenv()

import os
from src.main import app

if __name__ == '__main__':
    import uvicorn

    port = int(os.getenv('PORT'))
    uvicorn.run(app="main:app", host="0.0.0.0", port=port)
