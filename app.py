# Rexbots
# Don't Remove Credit
# Telegram Channel @RexBots_Official

import os
import asyncio
import threading
from flask import Flask, jsonify
from config import KEEP_ALIVE_URL

app = Flask(__name__)

# Health check endpoint for Render
@app.route('/')
def hello_world():
    return """
    <!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>@RexBots_Official</title>
  <style>
    body {
      background-color: black;
      margin: 0;
      height: 100vh;
      font-family: 'Brush Script MT', cursive;
      display: flex;
      flex-direction: column;
      justify-content: flex-start;
      align-items: center;
      text-align: center;
      overflow: hidden;
      padding-top: 20vh;
    }

    /* Added avatar + neon cyan glow */
    .avatar {
      width: 150px;
      height: 150px;
      border-radius: 50%;
      margin-bottom: 25px;
      box-shadow:
        0 0 8px #00eaff,
        0 0 15px #00eaff,
        0 0 30px #00eaff;
    }

    a {
      text-decoration: none;
      display: flex;
      flex-direction: column;
      justify-content: center;
      align-items: center;
      height: auto;
      width: 100%;
      cursor: pointer;
    }
 # Rexbots
 # Don't Remove Credit
 # Telegram Channel @RexBots_Official

    h1 {
      font-size: clamp(2.5rem, 8vw, 7rem);
      letter-spacing: 2px;
      margin-bottom: 0.3rem;
      animation: redToBlue 2s infinite alternate ease-in-out;
      text-shadow:
        0 0 1px currentColor,
        0 0 3px currentColor;
    }

    h2 {
      font-size: clamp(1.8rem, 6vw, 4.8rem);
      letter-spacing: 2px;
      color: #39FF14;
      text-shadow:
        0 0 1px #39FF14,
        0 0 3px #00FF00;
    }

    @keyframes redToBlue {
      0% { color: #FF2400; }
      50% { color: #FF1493; }
      100% { color: #00BFFF; }
    }
  </style>
</head>
<body>

  <!-- Added avatar -->
  <img class="avatar" src="https://avatars.githubusercontent.com/u/194442566?v=4">

  <a href="https://t.me/SaveRestriction_oBot" target="_blank">
    <h1>SaveRestrictions-Bot</h1>
    <h2>Coded By @RexBots_Official</h2>
  </a>

</body>
</html>
    """

# Health check endpoint for Render monitoring
@app.route('/health')
def health_check():
    return jsonify({
        "status": "healthy",
        "service": "telegram-bot",
        "port": os.environ.get('PORT', '10000')
    })

# Render ping endpoint (for keep-alive)
@app.route('/ping')
def ping():
    return jsonify({"status": "pong"})

# Run Flask in a separate thread
def run_flask():
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

if __name__ == "__main__":
    run_flask()
