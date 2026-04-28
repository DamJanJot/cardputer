<?php
error_reporting(E_ALL);
ini_set('display_errors', 1);

$BASE_DIR = __DIR__;
$PROJECTS_DIR = $BASE_DIR . '/projects';
$EXPORT_DIR = realpath($BASE_DIR . '/../cardputer');
if ($EXPORT_DIR === false) { $EXPORT_DIR = $BASE_DIR . '/../cardputer'; }

if (!is_dir($PROJECTS_DIR)) mkdir($PROJECTS_DIR, 0775, true);
if (!is_dir($EXPORT_DIR)) mkdir($EXPORT_DIR, 0775, true);

function safe_name($name) {
    $name = basename(str_replace('\\', '/', $name));
    $name = preg_replace('/[^a-zA-Z0-9_\-.]/', '', $name);
    if ($name === '') $name = 'new_app.py';
    if (substr($name, -3) !== '.py') $name .= '.py';
    return $name;
}

function default_code($name) {
    return "# " . $name . "\n"
. "from lib import display\n"
. "from lib.hydra.config import Config\n"
. "from lib.userinput import UserInput\n"
. "from font import vga1_8x16 as font\n"
. "import time\n\n"
. "cfg = Config()\n"
. "tft = display.Display(use_tiny_buf=True)\n"
. "kb = UserInput()\n\n"
. "def draw():\n"
. "    tft.fill(cfg.palette[2])\n"
. "    tft.text(\"" . $name . "\", 8, 16, cfg.palette[8], font=font)\n"
. "    tft.text(\"CardpuTest OK\", 8, 40, cfg.palette[8], font=font)\n"
. "    tft.text(\"ESC/Q = exit\", 8, 96, cfg.palette[8], font=font)\n"
. "    tft.show()\n\n"
. "draw()\n\n"
. "while True:\n"
. "    keys = [str(k).upper() for k in kb.get_new_keys()]\n"
. "    if \"ESC\" in keys or \"Q\" in keys:\n"
. "        break\n"
. "    time.sleep_ms(100)\n";
}

$action = $_POST['action'] ?? $_GET['action'] ?? '';
$msg = '';

if ($action === 'new') {
    $file = safe_name($_POST['file'] ?? 'new_app.py');
    $path = $PROJECTS_DIR . '/' . $file;
    if (!file_exists($path)) file_put_contents($path, default_code($file));
    header('Location: ?file=' . urlencode($file));
    exit;
}

if ($action === 'save') {
    $file = safe_name($_POST['file'] ?? 'new_app.py');
    file_put_contents($PROJECTS_DIR . '/' . $file, $_POST['code'] ?? '');
    $msg = "Zapisano: " . $file;
}

if ($action === 'delete') {
    $file = safe_name($_POST['file'] ?? '');
    $path = $PROJECTS_DIR . '/' . $file;
    if (file_exists($path)) unlink($path);
    $msg = "Usunięto: " . $file;
}

if ($action === 'export_one') {
    $file = safe_name($_POST['file'] ?? '');
    $src = $PROJECTS_DIR . '/' . $file;
    if (file_exists($src)) {
        copy($src, $EXPORT_DIR . '/' . $file);
        $msg = "Export do /cardputer/: " . $file;
    }
}

if ($action === 'export_all') {
    $files = glob($PROJECTS_DIR . '/*.py');
    $manifest = [];
    foreach ($files as $src) {
        $name = basename($src);
        copy($src, $EXPORT_DIR . '/' . $name);
        $manifest[] = $name;
    }
    sort($manifest);
    file_put_contents($EXPORT_DIR . '/manifest.txt', implode("\n", $manifest) . "\n");
    $msg = "Export ALL: " . count($manifest) . " plików + manifest.txt";
}

if ($action === 'import_cardputer') {
    $files = glob($EXPORT_DIR . '/*.py');
    $count = 0;
    foreach ($files as $src) {
        copy($src, $PROJECTS_DIR . '/' . basename($src));
        $count++;
    }
    $msg = "Import z /cardputer/: " . $count . " plików";
}

if ($action === 'make_manifest') {
    $files = glob($EXPORT_DIR . '/*.py');
    $manifest = array_map('basename', $files);
    sort($manifest);
    file_put_contents($EXPORT_DIR . '/manifest.txt', implode("\n", $manifest) . "\n");
    $msg = "Odświeżono manifest.txt: " . count($manifest) . " plików";
}

$projects = glob($PROJECTS_DIR . '/*.py');
sort($projects);
$current = safe_name($_GET['file'] ?? ($_POST['file'] ?? (count($projects) ? basename($projects[0]) : 'hello_cardputer.py')));
$current_path = $PROJECTS_DIR . '/' . $current;
if (!file_exists($current_path)) file_put_contents($current_path, default_code($current));
$code = file_get_contents($current_path);
$manifest = file_exists($EXPORT_DIR . '/manifest.txt') ? file_get_contents($EXPORT_DIR . '/manifest.txt') : '';
?>
<!doctype html>
<html lang="pl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>CardpuTest Studio</title>
<style>
:root{--bg:#0b0f14;--panel:#141b24;--panel2:#101720;--line:#2a3544;--text:#e8eef7;--muted:#9fb0c4;--accent:#58a6ff;--good:#76ff9d}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font-family:system-ui,Segoe UI,Arial,sans-serif}
header{padding:16px 20px;border-bottom:1px solid var(--line);background:#0f1620;display:flex;justify-content:space-between;gap:12px}
h1{margin:0;font-size:20px}small{color:var(--muted)}
main{display:grid;grid-template-columns:280px 1fr 320px;gap:12px;padding:12px;height:calc(100vh - 65px)}
.panel{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:12px;overflow:auto}
.list a{display:block;padding:9px 10px;color:var(--text);text-decoration:none;border-radius:9px;margin:4px 0;background:var(--panel2)}
.list a.active{outline:2px solid var(--accent)}
button,input{background:#0c121a;color:var(--text);border:1px solid var(--line);border-radius:10px;padding:9px 10px;font:inherit}
button{cursor:pointer;background:#17345a}.danger{background:#5a1720}
.row{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin:8px 0}.msg{color:var(--good);min-height:22px}
.badge{display:inline-block;color:var(--muted);border:1px solid var(--line);border-radius:999px;padding:4px 8px;margin:2px}
pre{background:#081018;border:1px solid var(--line);padding:10px;border-radius:10px;overflow:auto;color:#c9e2ff}

.editor-wrap{position:relative;height:calc(100vh - 230px);border:1px solid var(--line);border-radius:14px;background:#05080c;overflow:hidden}
#highlight,#code{
  position:absolute;inset:0;margin:0;padding:14px 14px 14px 54px;
  font-family:ui-monospace,Consolas,monospace;font-size:14px;line-height:1.35;
  tab-size:4;white-space:pre;overflow:auto;border:0;border-radius:14px;
  word-wrap:normal;overflow-wrap:normal;
}
#highlight{pointer-events:none;color:#f8f8f2;background:#05080c}
#code{background:transparent;color:rgba(255,255,255,0.02);caret-color:#fff;resize:none;outline:none}
#code::selection{background:rgba(88,166,255,.42);color:rgba(255,255,255,0.02)}
.lineNos{position:absolute;left:0;top:0;bottom:0;width:44px;padding-top:14px;background:#07111d;border-right:1px solid #182333;color:#53657a;text-align:right;font-family:ui-monospace,Consolas,monospace;font-size:14px;line-height:1.35;overflow:hidden;z-index:2}
.lineNos div{padding-right:9px;height:18.9px}
.kw{color:#ff79c6}.str{color:#f1fa8c}.num{color:#bd93f9}.com{color:#6272a4}.fn{color:#50fa7b}.cls{color:#8be9fd}.builtin{color:#8be9fd}.plain{color:#f8f8f2}

.phone{width:240px;height:135px;background:#000;border:8px solid #263241;border-radius:16px;margin:auto;position:relative;overflow:hidden;box-shadow:0 10px 30px #0008}
.screenText{position:absolute;left:8px;top:8px;color:#fff;font-family:monospace;font-size:12px;line-height:16px;white-space:pre-wrap}
.kbd{display:grid;grid-template-columns:repeat(5,1fr);gap:6px;margin-top:12px}.kbd button{padding:7px 4px;font-size:12px;background:#101a27}
.hint{color:var(--muted);font-size:13px;margin-left:auto}
</style>
</head>
<body>
<header><div><h1>📟 CardpuTest Studio</h1><small>MicroHydra dla M5Stack Cardputer</small></div><div><span class="badge">/cardputest</span><span class="badge">export → /cardputer</span></div></header>
<main>
<section class="panel">
<h2>Projekty</h2>
<form method="post" class="row"><input type="hidden" name="action" value="new"><input name="file" placeholder="nazwa.py" style="width:160px"><button>Nowy</button></form>
<div class="list"><?php foreach ($projects as $p): $bn = basename($p); ?><a class="<?= $bn === $current ? 'active' : '' ?>" href="?file=<?= urlencode($bn) ?>"><?= htmlspecialchars($bn) ?></a><?php endforeach; ?></div>
<hr style="border-color:var(--line)">
<form method="post" class="row"><input type="hidden" name="action" value="import_cardputer"><button>Import z /cardputer</button></form>
<form method="post" class="row"><input type="hidden" name="action" value="export_all"><button>Export ALL + manifest</button></form>
<form method="post" class="row"><input type="hidden" name="action" value="make_manifest"><button>Odśwież manifest</button></form>
<h3>manifest.txt</h3><pre><?= htmlspecialchars($manifest ?: 'brak manifestu') ?></pre>
</section>
<section class="panel">
<div class="msg"><?= htmlspecialchars($msg) ?></div>
<form method="post" id="editorForm">
<input type="hidden" name="file" value="<?= htmlspecialchars($current) ?>">
<div class="row"><strong><?= htmlspecialchars($current) ?></strong><button name="action" value="save">💾 Zapisz</button><button name="action" value="export_one">⬆ Export do /cardputer</button><button class="danger" name="action" value="delete" onclick="return confirm('Usunąć projekt?')">Usuń</button><span class="hint">Ctrl+S = zapisz</span></div>
<div class="editor-wrap"><div class="lineNos" id="lineNos"></div><pre id="highlight"></pre><textarea id="code" name="code" spellcheck="false" wrap="off"><?= htmlspecialchars($code) ?></textarea></div>
</form>
</section>
<section class="panel">
<h2>Symulator Cardputera</h2><div class="phone"><div class="screenText" id="screenText">Kliknij „Symuluj”</div></div>
<div class="row"><button onclick="simulate()">▶ Symuluj</button><button onclick="clearScreen()">Wyczyść</button></div>
<div class="kbd"><button onclick="sendKey('UP')">UP</button><button onclick="sendKey('DOWN')">DOWN</button><button onclick="sendKey('LEFT')">LEFT</button><button onclick="sendKey('RIGHT')">RIGHT</button><button onclick="sendKey('ENTER')">ENTER</button><button onclick="sendKey('ESC')">ESC</button><button onclick="sendKey('Q')">Q</button><button onclick="sendKey('A')">A</button><button onclick="sendKey('S')">S</button><button onclick="sendKey('D')">D</button></div>
<h3>Co symuluje?</h3><p style="color:var(--muted)">Preview tekstów z <code>tft.text(...)</code>. Prawdziwy test: Export ALL → Sync Apps.</p>
</section>
</main>
<script>
const codeEl=document.getElementById('code'), highEl=document.getElementById('highlight'), lineEl=document.getElementById('lineNos'), screenEl=document.getElementById('screenText');

const KW = new Set('False None True and as assert async await break class continue def del elif else except finally for from global if import in is lambda nonlocal not or pass raise return try while with yield'.split(' '));
const BUILTIN = new Set('print len str int float range list dict set tuple open super isinstance time display Config UserInput'.split(' '));

function html(s){return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}
function span(cls, s){return '<span class="'+cls+'">'+html(s)+'</span>';}
function isAlpha(c){return /[A-Za-z_]/.test(c);}
function isNum(c){return /[0-9]/.test(c);}
function isAlnum(c){return /[A-Za-z0-9_]/.test(c);}

function highlightLine(line){
  let out='', i=0;
  while(i<line.length){
    const c=line[i];

    if(c === '#'){
      out += span('com', line.slice(i));
      break;
    }

    if(c === '"' || c === "'"){
      const quote=c; let j=i+1, escp=false;
      while(j<line.length){
        const ch=line[j];
        if(escp){escp=false; j++; continue;}
        if(ch==='\\'){escp=true; j++; continue;}
        if(ch===quote){j++; break;}
        j++;
      }
      out += span('str', line.slice(i,j));
      i=j; continue;
    }

    if(isNum(c)){
      let j=i+1;
      while(j<line.length && /[0-9.]/.test(line[j])) j++;
      out += span('num', line.slice(i,j));
      i=j; continue;
    }

    if(isAlpha(c)){
      let j=i+1;
      while(j<line.length && isAlnum(line[j])) j++;
      const word=line.slice(i,j);
      let cls='plain';
      if(KW.has(word)) cls='kw';
      else if(BUILTIN.has(word)) cls='builtin';
      out += span(cls, word);
      i=j; continue;
    }

    out += html(c);
    i++;
  }
  return out;
}

function highlightPython(src){
  return src.split('\n').map(highlightLine).join('\n') + '\n';
}

function updateEditor(){
  const val=codeEl.value;
  highEl.innerHTML=highlightPython(val);
  const lines=val.split('\n').length;
  let nums='';
  for(let i=1;i<=lines;i++) nums += '<div>'+i+'</div>';
  lineEl.innerHTML=nums;
}

function syncScroll(){
  highEl.scrollTop=codeEl.scrollTop;
  highEl.scrollLeft=codeEl.scrollLeft;
  lineEl.scrollTop=codeEl.scrollTop;
}

codeEl.addEventListener('input', updateEditor);
codeEl.addEventListener('scroll', syncScroll);
codeEl.addEventListener('keydown', function(e){
  if((e.ctrlKey||e.metaKey) && e.key.toLowerCase()==='s'){
    e.preventDefault();
    document.getElementById('editorForm').requestSubmit();
  }
  if(e.key==='Tab'){
    e.preventDefault();
    const st=this.selectionStart, en=this.selectionEnd;
    this.value=this.value.substring(0,st)+'    '+this.value.substring(en);
    this.selectionStart=this.selectionEnd=st+4;
    updateEditor();
    syncScroll();
  }
});

function clearScreen(){screenEl.textContent=''}
function currentCode(){return codeEl.value}
function extractTexts(code){
  const out=[]; const re=/(?:tft|display)\.text\(\s*(['"`])([\s\S]*?)\1/g; let m;
  while((m=re.exec(code))!==null) out.push(m[2]);
  if(out.length===0){
    const r2=/["']([^"']{3,40})["']/g;
    while((m=r2.exec(code))!==null){
      const x=m[1];
      if(!x.includes('lib')&&!x.includes('.py')&&!x.includes('__')) out.push(x);
      if(out.length>7) break;
    }
  }
  return out.length?out:['Brak tekstów UI','Zapisz i testuj na urządzeniu'];
}
function simulate(){screenEl.textContent=extractTexts(currentCode()).slice(0,7).join('\n')}
function sendKey(k){screenEl.textContent=screenEl.textContent+'\nKEY: '+k}

updateEditor();
</script>
</body>
</html>
