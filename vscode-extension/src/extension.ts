import * as vscode from 'vscode';
import * as cp from 'child_process';
import * as path from 'path';
import * as fs from 'fs';

let panel: vscode.WebviewPanel | undefined;
let yahllProcess: cp.ChildProcess | undefined;

export function activate(context: vscode.ExtensionContext) {
    // Run setup on first install
    const setupFlag = path.join(process.env.HOME || process.env.USERPROFILE || '', '.yahll', 'setup_complete');
    if (!fs.existsSync(setupFlag)) {
        runSetupWizard(context);
    }

    context.subscriptions.push(
        vscode.commands.registerCommand('yahll.openPanel', () => openChatPanel(context)),
        vscode.commands.registerCommand('yahll.runSetup', () => runSetupWizard(context)),
    );
}

function runSetupWizard(context: vscode.ExtensionContext) {
    const terminal = vscode.window.createTerminal({
        name: 'Yahll Setup',
        env: { FORCE_COLOR: '1' },
    });
    terminal.show();
    terminal.sendText('python -m yahll.setup');

    // After setup, offer to open panel
    const disposable = vscode.window.onDidCloseTerminal(t => {
        if (t.name === 'Yahll Setup') {
            disposable.dispose();
            vscode.window.showInformationMessage(
                'Yahll is ready!',
                'Open Chat'
            ).then(choice => {
                if (choice === 'Open Chat') {
                    openChatPanel(context);
                }
            });
        }
    });
}

function openChatPanel(context: vscode.ExtensionContext) {
    if (panel) {
        panel.reveal(vscode.ViewColumn.Two);
        return;
    }

    panel = vscode.window.createWebviewPanel(
        'yahllChat',
        'Yahll',
        vscode.ViewColumn.Two,
        {
            enableScripts: true,
            retainContextWhenHidden: true,
        }
    );

    panel.webview.html = getChatHtml();
    panel.iconPath = vscode.Uri.joinPath(context.extensionUri, 'icon.png');

    // Spawn yahll --pipe
    startYahllProcess();

    // Extension → webview messages
    panel.webview.onDidReceiveMessage(msg => {
        if (msg.type === 'send' && yahllProcess?.stdin) {
            yahllProcess.stdin.write(msg.text + '\n');
        }
    }, undefined, context.subscriptions);

    panel.onDidDispose(() => {
        panel = undefined;
        yahllProcess?.kill();
        yahllProcess = undefined;
    }, undefined, context.subscriptions);
}

function startYahllProcess() {
    yahllProcess = cp.spawn('yahll', ['--pipe'], {
        shell: true,
        env: { ...process.env, PYTHONUNBUFFERED: '1' },
    });

    let buffer = '';

    yahllProcess.stdout?.on('data', (data: Buffer) => {
        buffer += data.toString();
        const lines = buffer.split('\n');
        buffer = lines.pop() ?? '';
        for (const line of lines) {
            panel?.webview.postMessage({ type: 'chunk', text: line + '\n' });
        }
    });

    yahllProcess.stderr?.on('data', (data: Buffer) => {
        panel?.webview.postMessage({ type: 'error', text: data.toString() });
    });

    yahllProcess.on('exit', () => {
        panel?.webview.postMessage({ type: 'system', text: '\n[YAHLL PROCESS TERMINATED]\n' });
    });
}

function getChatHtml(): string {
    return `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Yahll</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    background: #090d12;
    color: #00ff9f;
    font-family: 'Cascadia Code', 'Fira Code', 'Consolas', monospace;
    font-size: 13px;
    display: flex;
    flex-direction: column;
    height: 100vh;
    overflow: hidden;
  }

  #header {
    background: #0d1117;
    border-bottom: 1px solid #00ff9f22;
    padding: 10px 16px;
    display: flex;
    align-items: center;
    gap: 10px;
    flex-shrink: 0;
  }

  #header .title {
    color: #00ff9f;
    font-weight: bold;
    font-size: 14px;
    letter-spacing: 2px;
    text-transform: uppercase;
  }

  #header .dot {
    color: #00ff9f;
    animation: pulse 2s infinite;
  }

  #header .model {
    color: #00ff9f66;
    font-size: 11px;
    letter-spacing: 1px;
  }

  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.3; }
  }

  #messages {
    flex: 1;
    overflow-y: auto;
    padding: 16px;
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  #messages::-webkit-scrollbar { width: 4px; }
  #messages::-webkit-scrollbar-track { background: transparent; }
  #messages::-webkit-scrollbar-thumb { background: #00ff9f33; border-radius: 2px; }

  .msg {
    max-width: 90%;
    line-height: 1.6;
    white-space: pre-wrap;
    word-break: break-word;
  }

  .msg.user {
    align-self: flex-end;
    color: #7eb8f7;
    border-left: 2px solid #7eb8f744;
    padding-left: 10px;
  }

  .msg.user::before {
    display: block;
    content: 'YOU';
    font-size: 9px;
    letter-spacing: 2px;
    color: #7eb8f766;
    margin-bottom: 4px;
  }

  .msg.yahll {
    align-self: flex-start;
    color: #00ff9f;
    border-left: 2px solid #00ff9f44;
    padding-left: 10px;
  }

  .msg.yahll::before {
    display: block;
    content: 'YAHLL';
    font-size: 9px;
    letter-spacing: 2px;
    color: #00ff9f66;
    margin-bottom: 4px;
  }

  .msg.system {
    align-self: center;
    color: #ff6b6b88;
    font-size: 11px;
    letter-spacing: 1px;
    border: none;
    padding: 0;
  }

  .cursor {
    display: inline-block;
    width: 7px;
    height: 13px;
    background: #00ff9f;
    animation: blink 1s step-end infinite;
    vertical-align: text-bottom;
    margin-left: 1px;
  }

  @keyframes blink {
    0%, 100% { opacity: 1; }
    50% { opacity: 0; }
  }

  #input-bar {
    background: #0d1117;
    border-top: 1px solid #00ff9f22;
    padding: 12px 16px;
    display: flex;
    align-items: center;
    gap: 10px;
    flex-shrink: 0;
  }

  #input-bar .prompt {
    color: #00ff9f;
    font-weight: bold;
    flex-shrink: 0;
  }

  #input {
    flex: 1;
    background: transparent;
    border: none;
    outline: none;
    color: #00ff9f;
    font-family: inherit;
    font-size: 13px;
    caret-color: #00ff9f;
  }

  #input::placeholder { color: #00ff9f33; }

  #send-btn {
    background: #00ff9f18;
    border: 1px solid #00ff9f44;
    color: #00ff9f;
    font-family: inherit;
    font-size: 11px;
    letter-spacing: 1px;
    padding: 4px 12px;
    cursor: pointer;
    transition: background 0.15s;
  }

  #send-btn:hover { background: #00ff9f30; }
  #send-btn:disabled { opacity: 0.3; cursor: not-allowed; }

  .scanline {
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    pointer-events: none;
    background: repeating-linear-gradient(
      0deg,
      transparent,
      transparent 2px,
      rgba(0,255,159,0.015) 2px,
      rgba(0,255,159,0.015) 4px
    );
    z-index: 9999;
  }
</style>
</head>
<body>
<div class="scanline"></div>

<div id="header">
  <span class="title">YAHLL</span>
  <span class="dot">●</span>
  <span class="model">LOCAL INTELLIGENCE ONLINE</span>
</div>

<div id="messages">
  <div class="msg system">[ YAHLL INTELLIGENCE FRAMEWORK CONNECTED ]</div>
  <div class="msg system">[ TYPE A MESSAGE OR USE /help FOR COMMANDS ]</div>
</div>

<div id="input-bar">
  <span class="prompt">&gt;</span>
  <input id="input" type="text" placeholder="Talk to Yahll or type /upgrade..." autocomplete="off" />
  <button id="send-btn">SEND</button>
</div>

<script>
  const vscode = acquireVsCodeApi();
  const messagesEl = document.getElementById('messages');
  const inputEl = document.getElementById('input');
  const sendBtn = document.getElementById('send-btn');

  let currentYahllMsg = null;

  function scrollBottom() {
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  function addUserMsg(text) {
    const div = document.createElement('div');
    div.className = 'msg user';
    div.textContent = text;
    messagesEl.appendChild(div);
    scrollBottom();
  }

  function startYahllMsg() {
    currentYahllMsg = document.createElement('div');
    currentYahllMsg.className = 'msg yahll';
    const cursor = document.createElement('span');
    cursor.className = 'cursor';
    currentYahllMsg.appendChild(cursor);
    messagesEl.appendChild(currentYahllMsg);
    scrollBottom();
    return currentYahllMsg;
  }

  function appendToYahllMsg(text) {
    if (!currentYahllMsg) startYahllMsg();
    const cursor = currentYahllMsg.querySelector('.cursor');
    const textNode = document.createTextNode(text);
    currentYahllMsg.insertBefore(textNode, cursor);
    scrollBottom();
  }

  function finalizeYahllMsg() {
    if (currentYahllMsg) {
      const cursor = currentYahllMsg.querySelector('.cursor');
      if (cursor) cursor.remove();
      currentYahllMsg = null;
    }
  }

  function send() {
    const text = inputEl.value.trim();
    if (!text) return;
    inputEl.value = '';
    addUserMsg(text);
    finalizeYahllMsg();
    startYahllMsg();
    sendBtn.disabled = true;
    vscode.postMessage({ type: 'send', text });
  }

  sendBtn.addEventListener('click', send);
  inputEl.addEventListener('keydown', e => {
    if (e.key === 'Enter') send();
  });

  // Receive messages from extension
  window.addEventListener('message', e => {
    const msg = e.data;
    if (msg.type === 'chunk') {
      appendToYahllMsg(msg.text);
      sendBtn.disabled = false;
    } else if (msg.type === 'error') {
      appendToYahllMsg('[ERROR] ' + msg.text);
      sendBtn.disabled = false;
    } else if (msg.type === 'system') {
      finalizeYahllMsg();
      const div = document.createElement('div');
      div.className = 'msg system';
      div.textContent = msg.text;
      messagesEl.appendChild(div);
      scrollBottom();
    }
  });

  inputEl.focus();
</script>
</body>
</html>`;
}

export function deactivate() {
    yahllProcess?.kill();
}
