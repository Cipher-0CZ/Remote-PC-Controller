"""
Remote PC Controller
---------------------
A single-file Flask application that turns your smartphone into a
touchpad / keyboard / media remote for your PC over local Wi-Fi.

Run:  python remote_pc_controller.py
Then open http://<YOUR_PC_LOCAL_IP>:5000 on your phone's browser
(phone and PC must be on the same Wi-Fi network).
"""

import pyautogui
from flask import Flask, request, jsonify, render_template_string
from pynput.keyboard import Controller as KeyboardController

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
pyautogui.FAILSAFE = False   # prevent exceptions when cursor hits screen corner
pyautogui.PAUSE = 0          # no artificial delay between pyautogui calls

app = Flask(__name__)
kb = KeyboardController()

SCREEN_W, SCREEN_H = pyautogui.size()

# ---------------------------------------------------------------------------
# Frontend (single-file HTML/CSS/JS)
# ---------------------------------------------------------------------------
PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>Remote PC Controller</title>
<style>
  :root{
    --bg:#0e0f13;
    --panel:#181a20;
    --panel-2:#1f222a;
    --accent:#5b8cff;
    --accent-2:#2ecC71;
    --text:#e8e9ec;
    --muted:#8a8f9b;
    --danger:#ff5b6e;
    --radius:14px;
  }
  *{box-sizing:border-box; -webkit-tap-highlight-color:transparent; user-select:none;}
  body{
    margin:0; padding:0;
    background:var(--bg);
    color:var(--text);
    font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif;
    overscroll-behavior:none;
    touch-action:none;
    padding-bottom:24px;
  }
  header{
    padding:16px 18px 8px;
    display:flex; align-items:center; justify-content:space-between;
  }
  header h1{
    font-size:18px; margin:0; font-weight:600; letter-spacing:.3px;
  }
  .status-dot{
    width:9px;height:9px;border-radius:50%;background:var(--accent-2);
    display:inline-block; margin-right:6px; box-shadow:0 0 8px var(--accent-2);
  }
  .status{font-size:12px; color:var(--muted); display:flex; align-items:center;}

  section{ padding: 6px 14px; }
  .section-title{
    font-size:12px; color:var(--muted); text-transform:uppercase;
    letter-spacing:1px; margin:14px 4px 8px;
  }

  #touchpad{
    height:38vh; min-height:220px;
    background:linear-gradient(145deg,var(--panel),var(--panel-2));
    border:1px solid #2a2d36;
    border-radius:var(--radius);
    display:flex; align-items:center; justify-content:center;
    color:var(--muted); font-size:13px;
    position:relative; overflow:hidden;
  }
  #touchpad::after{
    content:"";
    position:absolute; inset:0;
    background:radial-gradient(circle at 50% 0%, rgba(91,140,255,0.08), transparent 60%);
  }

  .grid{ display:grid; gap:10px; }
  .grid-2{ grid-template-columns:1fr 1fr; }
  .grid-3{ grid-template-columns:1fr 1fr 1fr; }
  .grid-4{ grid-template-columns:1fr 1fr 1fr 1fr; }
  .grid-5{ grid-template-columns:repeat(5,1fr); }

  button.btn{
    border:none; outline:none;
    background:var(--panel-2);
    color:var(--text);
    border:1px solid #2a2d36;
    border-radius:12px;
    padding:14px 8px;
    font-size:14px; font-weight:500;
    display:flex; flex-direction:column; align-items:center; gap:4px;
    transition:transform .06s ease, background .15s ease;
  }
  button.btn:active{
    transform:scale(0.94);
    background:var(--accent);
    color:#0e0f13;
  }
  button.btn small{ color:var(--muted); font-size:10px; }
  button.btn:active small{ color:#0e0f13cc; }

  button.btn.accent{ background: rgba(91,140,255,0.12); border-color: rgba(91,140,255,0.35); }
  button.btn.danger{ background: rgba(255,91,110,0.10); border-color: rgba(255,91,110,0.3); }

  .textbar{
    display:flex; gap:8px; padding:6px 14px 4px;
  }
  .textbar input{
    flex:1;
    background:var(--panel-2);
    border:1px solid #2a2d36;
    color:var(--text);
    border-radius:12px;
    padding:12px 14px;
    font-size:14px;
  }
  .textbar button{
    background:var(--accent);
    color:#0b0d12;
    border:none; border-radius:12px;
    padding:0 18px; font-weight:600; font-size:14px;
  }
  .toast{
    position:fixed; left:50%; bottom:18px; transform:translateX(-50%);
    background:#20232b; color:var(--text); padding:8px 16px;
    border-radius:20px; font-size:12px; border:1px solid #2f3340;
    opacity:0; transition:opacity .25s ease; pointer-events:none;
  }
  .toast.show{ opacity:1; }
</style>
</head>
<body>

<header>
  <h1>Remote PC Controller</h1>
  <div class="status"><span class="status-dot"></span>Connected</div>
</header>

<section>
  <div class="section-title">Touchpad — tap to click, hold + drag to select</div>
  <div id="touchpad">Move your finger here</div>
</section>

<section>
  <div class="grid grid-3">
    <button class="btn" onclick="sendClick('left')">🖱️<small>Left Click</small></button>
    <button class="btn" onclick="sendClick('right')">🖱️<small>Right Click</small></button>
    <button class="btn" onclick="sendClick('double')">🖱️<small>Double Click</small></button>
    <button class="btn" onclick="sendScroll(300)">⬆️<small>Scroll Up</small></button>
    <button class="btn" onclick="sendScroll(-300)">⬇️<small>Scroll Down</small></button>
    <button class="btn" onclick="toast('Middle click')" ontouchstart="sendClick('middle')">🖱️<small>Middle Click</small></button>
  </div>
</section>

<section>
  <div class="section-title">VS Code Shortcuts</div>
  <div class="grid grid-5">
    <button class="btn accent" onclick="sendKey('save')">💾<small>Save</small></button>
    <button class="btn accent" onclick="sendKey('run')">▶️<small>Run F5</small></button>
    <button class="btn accent" onclick="sendKey('undo')">↩️<small>Undo</small></button>
    <button class="btn accent" onclick="sendKey('tab')">⇥<small>Tab</small></button>
    <button class="btn accent" onclick="sendKey('palette')">🎛️<small>Cmd Palette</small></button>
  </div>
</section>

<section>
  <div class="section-title">Media Controls</div>
  <div class="grid grid-4">
    <button class="btn" onclick="sendMedia('volup')">🔊<small>Vol +</small></button>
    <button class="btn" onclick="sendMedia('voldown')">🔉<small>Vol -</small></button>
    <button class="btn danger" onclick="sendMedia('mute')">🔇<small>Mute</small></button>
    <button class="btn" onclick="sendMedia('playpause')">⏯️<small>Play/Pause</small></button>
  </div>
</section>

<section>
  <div class="section-title">Send Text to PC</div>
  <div class="textbar">
    <input id="textInput" type="text" placeholder="Type text, then Send…" autocomplete="off" autocapitalize="off" autocorrect="off">
    <button onclick="sendText()">Send</button>
  </div>
</section>

<div class="toast" id="toast"></div>

<script>
const pad = document.getElementById('touchpad');
let lastX = 0, lastY = 0;
let startX = 0, startY = 0;
let moved = 0;
let isDragging = false;
let holdTimer = null;
let touchStartTime = 0;

const DRAG_HOLD_MS = 320;
const MOVE_CANCEL_THRESHOLD = 10; // px of movement that cancels the "hold to drag"
const TAP_MOVE_THRESHOLD = 12;    // px of movement still considered a tap
const TAP_TIME_THRESHOLD = 300;   // ms

function post(url, data){
  fetch(url, {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify(data || {})
  }).catch(()=>{});
}

function toast(msg){
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.classList.add('show');
  clearTimeout(t._timer);
  t._timer = setTimeout(()=> t.classList.remove('show'), 900);
}

pad.addEventListener('touchstart', (e) => {
  const t = e.touches[0];
  lastX = t.clientX; lastY = t.clientY;
  startX = t.clientX; startY = t.clientY;
  moved = 0;
  isDragging = false;
  touchStartTime = Date.now();

  holdTimer = setTimeout(() => {
    if (moved < MOVE_CANCEL_THRESHOLD) {
      isDragging = true;
      post('/mousedown', {});
      toast('Dragging…');
    }
  }, DRAG_HOLD_MS);
}, {passive:true});

pad.addEventListener('touchmove', (e) => {
  const t = e.touches[0];
  const dx = t.clientX - lastX;
  const dy = t.clientY - lastY;
  lastX = t.clientX; lastY = t.clientY;
  moved += Math.abs(dx) + Math.abs(dy);

  if (moved > MOVE_CANCEL_THRESHOLD && holdTimer && !isDragging) {
    clearTimeout(holdTimer);
    holdTimer = null;
  }

  post('/move', {dx: dx, dy: dy});
}, {passive:true});

pad.addEventListener('touchend', () => {
  if (holdTimer) { clearTimeout(holdTimer); holdTimer = null; }

  if (isDragging) {
    post('/mouseup', {});
    isDragging = false;
    return;
  }

  const elapsed = Date.now() - touchStartTime;
  if (moved < TAP_MOVE_THRESHOLD && elapsed < TAP_TIME_THRESHOLD) {
    post('/click', {button: 'left'});
    toast('Click');
  }
}, {passive:true});

function sendClick(button){
  post('/click', {button: button});
  toast(button + ' click');
}
function sendScroll(amount){
  post('/scroll', {amount: amount});
}
function sendKey(action){
  post('/key', {action: action});
  toast(action);
}
function sendMedia(action){
  post('/media', {action: action});
  toast(action);
}
function sendText(){
  const input = document.getElementById('textInput');
  const text = input.value;
  if (!text) return;
  post('/type', {text: text});
  toast('Text sent');
  input.value = '';
  input.blur();
}
document.getElementById('textInput').addEventListener('keydown', (e) => {
  if (e.key === 'Enter') sendText();
});
</script>
</body>
</html>
"""

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route('/')
def index():
    return render_template_string(PAGE)


@app.route('/move', methods=['POST'])
def move():
    data = request.get_json(silent=True) or {}
    dx = float(data.get('dx', 0))
    dy = float(data.get('dy', 0))
    # Sensitivity multiplier — tweak to taste
    sensitivity = 1.6
    pyautogui.moveRel(dx * sensitivity, dy * sensitivity, duration=0)
    return jsonify(ok=True)


@app.route('/click', methods=['POST'])
def click():
    data = request.get_json(silent=True) or {}
    button = data.get('button', 'left')
    if button == 'double':
        pyautogui.doubleClick()
    elif button in ('left', 'right', 'middle'):
        pyautogui.click(button=button)
    return jsonify(ok=True)


@app.route('/mousedown', methods=['POST'])
def mousedown():
    pyautogui.mouseDown(button='left')
    return jsonify(ok=True)


@app.route('/mouseup', methods=['POST'])
def mouseup():
    pyautogui.mouseUp(button='left')
    return jsonify(ok=True)


@app.route('/scroll', methods=['POST'])
def scroll():
    data = request.get_json(silent=True) or {}
    amount = int(data.get('amount', 0))
    pyautogui.scroll(amount)
    return jsonify(ok=True)


@app.route('/key', methods=['POST'])
def key():
    data = request.get_json(silent=True) or {}
    action = data.get('action')

    actions = {
        'save':    lambda: pyautogui.hotkey('ctrl', 's'),
        'run':     lambda: pyautogui.press('f5'),
        'undo':    lambda: pyautogui.hotkey('ctrl', 'z'),
        'tab':     lambda: pyautogui.press('tab'),
        'palette': lambda: pyautogui.hotkey('ctrl', 'shift', 'p'),
    }

    fn = actions.get(action)
    if fn:
        fn()
        return jsonify(ok=True)
    return jsonify(ok=False, error='unknown action'), 400


@app.route('/media', methods=['POST'])
def media():
    data = request.get_json(silent=True) or {}
    action = data.get('action')

    actions = {
        'volup':     lambda: pyautogui.press('volumeup'),
        'voldown':   lambda: pyautogui.press('volumedown'),
        'mute':      lambda: pyautogui.press('volumemute'),
        'playpause': lambda: pyautogui.press('playpause'),
    }

    fn = actions.get(action)
    if fn:
        fn()
        return jsonify(ok=True)
    return jsonify(ok=False, error='unknown action'), 400


@app.route('/type', methods=['POST'])
def type_text():
    data = request.get_json(silent=True) or {}
    text = data.get('text', '')
    if text:
        # pynput handles unicode characters more reliably than pyautogui.write
        kb.type(text)
    return jsonify(ok=True)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    print(f"Screen resolution detected: {SCREEN_W}x{SCREEN_H}")
    print("Starting Remote PC Controller on http://0.0.0.0:5000")
    print("Open this address (with your PC's local IP) from your phone's browser.")
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
