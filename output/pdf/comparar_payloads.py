"""Compara la revisión vulnerable y la actual solo en servidores de loopback."""
import datetime
import json
from pathlib import Path
import select
import subprocess
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
REVISION = 'fc48115f39d326d76ec9ba991be92494f1111649'
CASES = [
    ('Control negativo', 'admin', 'incorrecta'),
    ('P1: comentario para admin', "admin' -- ", 'incorrecta'),
    ('P2: comentario para juan', "juan' -- ", 'incorrecta'),
    ('P3: tautología en usuario', "' OR 1=1 -- ", 'incorrecta'),
    ('P4: tautología en contraseña', 'admin', "' OR '1'='1"),
    ('Control positivo', 'admin', 'admin'),
]
WRAPPER = r'''
const fs = require('fs');
const http = require('http');
const Module = require('module');
const path = require('path');
const original = http.Server.prototype.listen;
http.Server.prototype.listen = function () {
  const server = this;
  return original.call(server, 0, '127.0.0.1', () => {
    console.log('READY http://127.0.0.1:' + server.address().port);
  });
};
const filename = path.resolve('server-vulnerable.js');
const mod = new Module(filename, module);
mod.filename = filename;
mod.paths = Module._nodeModulePaths(process.cwd());
mod._compile(fs.readFileSync(0, 'utf8'), filename);
'''

def run_version(name, source):
    proc = subprocess.Popen(['node', '-e', WRAPPER], cwd=ROOT/'login',
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, text=True)
    try:
        proc.stdin.write(source)
        proc.stdin.close()
        readable, _, _ = select.select([proc.stdout], [], [], 15)
        if not readable:
            raise RuntimeError('El servidor no anunció su puerto')
        line = proc.stdout.readline().strip()
        if not line.startswith('READY '):
            raise RuntimeError(f'Inicio inesperado: {line}')
        url = line.removeprefix('READY ') + '/login-vulnerable'
        results = []
        for label, user, password in CASES:
            body = {'username': user, 'password': password}
            request = urllib.request.Request(url, data=json.dumps(body).encode(),
                                            headers={'Content-Type': 'application/json'})
            try:
                response = urllib.request.urlopen(request, timeout=5)
            except urllib.error.HTTPError as error:
                response = error
            with response:
                status, data = response.code, json.load(response)
            expected = 200 if label == 'Control positivo' or (name == 'vulnerable' and label.startswith('P')) else 401
            assert status == expected, (name, label, status, data)
            assert data['ok'] == (expected == 200), (name, label, data)
            if label == 'P2: comentario para juan' and name == 'vulnerable':
                assert data['user'] == 'juan'
            results.append({'caso': label, 'solicitud': body, 'http': status, 'respuesta': data})
        return {'version': name, 'casos': results}
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()

legacy = subprocess.check_output(['git', 'show', f'{REVISION}:login/server-vulnerable.js'], cwd=ROOT, text=True)
current = (ROOT/'login/server-vulnerable.js').read_text()
report = {'fecha_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'revision_vulnerable': REVISION,
          'alcance': 'Solo loopback; envoltorio de ejecución asigna puerto dinámico y no modifica las consultas.',
          'resultados': [run_version('vulnerable', legacy), run_version('parametrizada', current)]}
output = ROOT/'output/pdf/evidencias/comparacion-payloads.json'
output.write_text(json.dumps(report, ensure_ascii=False, indent=2))
for version in report['resultados']:
    for case in version['casos']:
        print(version['version'], case['caso'], case['http'], case['respuesta'])
