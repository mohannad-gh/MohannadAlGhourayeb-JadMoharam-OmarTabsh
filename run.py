"""Start the local Flask setup server."""

import os

from dotenv import load_dotenv

from common.factory import create_app

load_dotenv()
app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.getenv("PORT", "5003")), debug=False)
