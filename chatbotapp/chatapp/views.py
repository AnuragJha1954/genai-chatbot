# chatapp/views.py
import os
import json
from django.shortcuts import render
from django.conf import settings
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST, require_GET
from google import genai
from django.views.decorators.csrf import csrf_exempt

# Optional: convert markdown to HTML on server side
try:
    import markdown as md_lib
    def md_to_html(md_text):
        return md_lib.markdown(md_text)
except Exception:
    # fallback: wrap markdown in <pre> if markdown lib not available
    def md_to_html(md_text):
        import html
        return "<pre>{}</pre>".format(html.escape(md_text))


MODEL_NAME = "gemini-2.5-flash"
SESSION_HISTORY_KEY = "chat_history"    

def _get_genai_client():
    api_key = getattr(settings, "GENAI_API_KEY", None) or os.environ.get("GENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GENAI_API_KEY not found. Set settings.GENAI_API_KEY in settings.py or the environment variable GENAI_API_KEY."
        )
    return genai.Client(api_key=api_key)

def index(request):
    return render(request, "index.html", {"model_name": MODEL_NAME})

@csrf_exempt
@require_POST
def chat_api(request):
    """
    POST JSON: {"message": "..."}
    Response JSON: {"reply": "<markdown>", "html": "<rendered html>", "ok": true}
    History of messages is stored in request.session[SESSION_HISTORY_KEY] as a list of dicts:
      [{"role":"user","text":"..."}, {"role":"model","text":"..."} , ...]
    """
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return HttpResponseBadRequest("Invalid JSON")

    message = payload.get("message", "").strip()
    if not message:
        return HttpResponseBadRequest("No message provided")

    try:
        client = _get_genai_client()
        # create a chat (stateless here). We manage history locally in session.
        chat = client.chats.create(model=MODEL_NAME)
        # send the message
        response = chat.send_message(message)

        # best-effort extract text (SDK versions differ)
        reply_text = getattr(response, "text", None) or getattr(response, "output_text", None)
        if reply_text is None:
            try:
                # fallback to common nested structure
                reply_text = response.output[0].content[0].text
            except Exception:
                reply_text = str(response)

        # convert markdown -> html
        reply_html = md_to_html(reply_text)

        # store into session history
        hist = request.session.get(SESSION_HISTORY_KEY, [])
        hist.append({"role": "user", "text": message})
        hist.append({"role": "model", "text": reply_text})
        request.session[SESSION_HISTORY_KEY] = hist
        request.session.modified = True

        return JsonResponse({"ok": True, "reply": reply_text, "html": reply_html})
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=500)

@csrf_exempt
@require_GET
def history_api(request):
    """
    Returns the session-stored history as JSON: {"history": [{"role":..., "text":...}, ...]}
    """
    hist = request.session.get(SESSION_HISTORY_KEY, [])
    return JsonResponse({"history": hist})

@csrf_exempt
@require_POST
def quit_api(request):
    """
    Clears the session chat history (acts as Quit).
    Optionally returns the history that was just cleared as JSON for printing.
    """
    hist = request.session.get(SESSION_HISTORY_KEY, [])
    # clear
    if SESSION_HISTORY_KEY in request.session:
        del request.session[SESSION_HISTORY_KEY]
        request.session.modified = True
    return JsonResponse({"quit": True, "history": hist})
