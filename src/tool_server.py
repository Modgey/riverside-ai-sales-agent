"""Simulated tool webhook server for Vapi mid-call function calls.

Run this before placing calls: py src/tool_server.py
Then expose via ngrok: ngrok http 3000
Set TOOL_SERVER_URL in .env to the ngrok URL + /tools
"""

from flask import Flask, request, jsonify

app = Flask(__name__)

TOOL_RESPONSES = {
    "book_meeting": "Great, I'll have someone from our team reach out to schedule a time to chat. They should hear from us shortly.",
    "send_signup_link": "Done, I've sent them a link to sign up for a free Riverside trial. They can get started right away.",
}


@app.route("/tools", methods=["POST"])
def handle_tool_call():
    data = request.json
    tool_calls = data.get("message", {}).get("toolCallList", [])

    results = []
    for tc in tool_calls:
        func_name = tc.get("function", {}).get("name", "")
        args = tc.get("function", {}).get("arguments", {})
        response_text = TOOL_RESPONSES.get(func_name, "Action completed.")
        print(f"  Tool call: {func_name}({args}) -> {response_text[:50]}...")
        results.append({
            "toolCallId": tc["id"],
            "result": response_text,
        })

    return jsonify({"results": results})


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "tools": list(TOOL_RESPONSES.keys())})


if __name__ == "__main__":
    print("Tool server running on http://localhost:3000")
    print("Endpoints:")
    print("  POST /tools  - Handle Vapi tool calls (book_meeting, send_signup_link)")
    print("  GET  /health - Health check")
    print()
    print("To expose publicly: ngrok http 3000")
    print("Then set TOOL_SERVER_URL=<ngrok-url>/tools in .env")
    app.run(port=3000, debug=False)
