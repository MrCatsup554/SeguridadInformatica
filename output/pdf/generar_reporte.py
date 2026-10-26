from pathlib import Path
import json, hashlib
from xml.sax.saxutils import escape
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.platypus import Paragraph, Table, TableStyle
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader

ROOT = Path(__file__).resolve().parent
E = ROOT / 'evidencias'
W,H = 595.28,841.89
c = canvas.Canvas(str(ROOT/'reporte-laboratorio-sqli.pdf'), pagesize=(W,H))
c.setTitle('Práctica de laboratorio: inyección SQL en login')
c.setAuthor('Laboratorio de Seguridad Informática')
style = ParagraphStyle('body',fontName='Helvetica',fontSize=11,leading=16,textColor=HexColor('#25344A'))
y=0
def page(n,title):
 global y
 c.setFillColor(HexColor('#10263E')); c.rect(0,H-115,W,115,fill=1,stroke=0)
 c.setFillColor(HexColor('#65D6C4')); c.setFont('Helvetica-Bold',10); c.drawString(44,H-35,'SEGURIDAD INFORMÁTICA / LABORATORIO LOCAL')
 c.setFillColor(HexColor('#FFFFFF')); c.setFont('Helvetica-Bold',22); c.drawString(44,H-76,title)
 c.setFillColor(HexColor('#526178')); c.setFont('Helvetica',9)
 c.drawString(44,30,'26 de octubre de 2026 | America/Merida | Evidencia de ejecución')
 c.drawRightString(W-44,30,f'{n} / 8')
 y=H-143
def text(s):
 global y
 p=Paragraph(s,style); _,h=p.wrap(W-88,700); p.drawOn(c,44,y-h); y-=h+12
def heading(s):
 global y
 c.setFillColor(HexColor('#10263E')); c.setFont('Helvetica-Bold',14); c.drawString(44,y-14,s); y-=27
def code(s,padding=20):
 global y
 lines=s.splitlines(); h=len(lines)*13+padding
 c.setFillColor(HexColor('#EEF3F8')); c.roundRect(44,y-h,W-88,h,5,fill=1,stroke=0)
 c.setFillColor(HexColor('#10263E')); c.setFont('Courier',8.5)
 for i,line in enumerate(lines): c.drawString(54,y-17-i*13,line)
 y-=h+14
def image(name,maxw,maxh):
 global y
 im=ImageReader(str(E/name)); iw,ih=im.getSize(); scale=min(maxw/iw,maxh/ih)
 c.drawImage(im,44,y-ih*scale,width=iw*scale,height=ih*scale)
 y-=ih*scale+14

page(1,'Inyección SQL en el login')
heading('Resultado de la práctica inicial')
text('Se confirmó la omisión de la validación de contraseña. El usuario <b>admin</b> con contraseña <b>incorrecta</b> recibió HTTP 401; al enviar <b>admin\' -- </b> con la misma contraseña, el endpoint respondió HTTP 200 y <b>ok: true, user: admin</b>.')
heading('Objetivo y alcance')
text('Demostrar y explicar una inyección SQL en el login educativo recién incorporado. Las pruebas se realizaron exclusivamente contra <b>http://127.0.0.1:3000/login-vulnerable</b>, en la copia local, con los usuarios de demostración y una base SQLite en memoria. No se enviaron pruebas a GitHub ni a servidores externos.')
heading('Entorno y preparación')
text('Aplicación Node.js, Express y sqlite3. Se instalaron las dependencias con <b>npm ci</b>. El servidor se ejecutó con un envoltorio temporal que limita la escucha a 127.0.0.1 y guarda las consultas en servidor.log, sin modificar el código del login.')
text('Código evaluado: <b>login/server-vulnerable.js</b>, líneas 26-38. Revisión local: <font face="Courier" size="8">fc48115f39d326d76ec9ba991be92494f1111649</font>.')
heading('Procedimiento')
text('1. Enviar admin / incorrecta mediante el formulario y capturar el rechazo.<br/>2. Enviar admin\' -- (con espacio final) / incorrecta y capturar la respuesta.<br/>3. Repetir por HTTP y registrar estado y cuerpo JSON.<br/>4. Contrastar la consulta del servidor y formular la corrección.')
text('<b>Actualización:</b> las capturas de las páginas 2 y 3 corresponden a la versión vulnerable. Las páginas 4 a 6 documentan la corrección y las pruebas. Las páginas 7 y 8 detallan cuatro payloads funcionales en la versión anterior, por qué funcionan, su rechazo con parámetros y las conclusiones. El endpoint devuelve JSON, sin sesiones ni panel privado.')
c.showPage()

page(2,'Evidencia 1 / Control de acceso')
heading('Contraseña incorrecta: rechazo esperado')
code('Usuario: admin\nContraseña: incorrecta\nPOST /login-vulnerable\nHTTP 401\n{"ok": false, "message": "Credenciales inválidas"}')
image('01-rechazo.jpg',W-88,310)
text('<b>Figura 1.</b> Captura real del formulario después de enviar credenciales inválidas. La respuesta visible indica ok: false. El estado HTTP 401 se verificó adicionalmente en la repetición registrada en respuestas-http.json.')
heading('Control positivo')
text('La repetición con admin / admin devolvió HTTP 200 y {"ok": true, "user": "admin"}. Este control confirma el comportamiento normal del endpoint con las credenciales precargadas.')
c.showPage()

page(3,'Evidencia 2 / Bypass confirmado')
text('Entrada de usuario: <b>admin\' -- </b> (espacio final). Contraseña: <b>incorrecta</b>. Respuesta HTTP verificada: <b>200</b>.')
image('02-inyeccion.jpg',W-88,365)
text('<b>Figura 2.</b> Captura real del formulario: la misma contraseña incorrecta produce ahora ok: true y user: admin. Se conserva la captura completa tal como la entregó el navegador.')
heading('Consulta observada en el registro')
code("SELECT * FROM users WHERE username = 'admin' -- '\nAND password = 'incorrecta'")
text('La consulta del registro es una sola línea (aquí se divide por espacio). La comilla cierra el literal del usuario y <b>--</b> comenta el resto, incluida la condición de contraseña. La búsqueda efectiva selecciona al usuario admin y db.get devuelve su fila.')
c.showPage()

page(4,'Causa, corrección y evidencias')
heading('Causa e impacto observado')
text('La línea 30 inserta entradas del cliente en el texto SQL mediante interpolación. Los datos alteran la estructura de la consulta. En este laboratorio, el impacto demostrado es la suplantación de admin ante el endpoint sin su contraseña. No se probó extracción masiva ni modificación de datos.')
heading('Corrección aplicada')
text('Se reemplazó la interpolación por parámetros enlazados en login/server-vulnerable.js. La consulta actual recibe el usuario y la contraseña como valores separados:')
code('const query =\n  "SELECT username FROM users" +\n  " WHERE username = ? AND password = ?";\ndb.get(query, [username, password], (err, row) => {\n  // Manejo de error, éxito y rechazo.\n});')
text('Con parámetros, el usuario se trata como un valor. La documentación oficial de SQLite describe estos marcadores y el enlace de valores en tiempo de ejecución:<br/><link href="https://www.sqlite.org/lang_expr.html#parameters" color="#136A84">https://www.sqlite.org/lang_expr.html#parameters</link>')
text('<b>Estado de la corrección:</b> aplicada y verificada. Admin / incorrecta devuelve 401; admin / admin, 200; admin\' -- / incorrecta, 401. También se parametrizaron las inserciones de demostración y se validan campos de tipo cadena no vacíos.')
text('Se eliminó el registro de consultas con contraseñas, se usa una respuesta genérica ante errores de base de datos y el servidor escucha en 127.0.0.1. Se conserva el nombre de la ruta /login-vulnerable para mantener compatible el formulario.')
heading('Archivos de evidencia')
text('En la carpeta <b>evidencias/</b>: 01-rechazo.jpg, 02-inyeccion.jpg, respuestas-http.json y servidor.log. Las capturas documentan las pruebas del formulario; el JSON contiene las repeticiones HTTP con marcas de tiempo UTC. El registro permite verificar el SQL recibido.')
heading('Conclusión')
text('La comparación inicial confirmó la inyección por concatenación. Después del cambio, los intentos probados se tratan como datos y no omiten la validación de contraseña. Las contraseñas de demostración siguen en texto claro; un uso real requiere hash de contraseñas y gestión de sesiones.')
c.showPage()

def table(headers, rows, widths, fontsize=9):
 global y
 cell = ParagraphStyle('cell', parent=style, fontSize=fontsize, leading=fontsize+3)
 head = ParagraphStyle('head', parent=cell, textColor=HexColor('#FFFFFF'), fontName='Helvetica-Bold')
 data = [[Paragraph(escape(v), head) for v in headers]]
 data += [[Paragraph(escape(v), cell) for v in row] for row in rows]
 t=Table(data,colWidths=widths)
 t.setStyle(TableStyle([
  ('BACKGROUND',(0,0),(-1,0),HexColor('#10263E')),
  ('ROWBACKGROUNDS',(0,1),(-1,-1),[HexColor('#EEF3F8'),HexColor('#FFFFFF')]),
  ('VALIGN',(0,0),(-1,-1),'TOP'),
  ('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),
  ('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8),
  ('LINEBELOW',(0,0),(-1,0),1,HexColor('#65D6C4')),
 ]))
 _,h=t.wrap(W-88,700)
 assert y-h > 55, f'Tabla fuera de página: {y-h}'
 t.drawOn(c,44,y-h); y-=h+16

page(5,'Tipos de inyección SQL')
text('La tabla reúne técnicas, objetivos y formas de activación que pueden combinarse. La peligrosidad expresa impacto potencial: es una estimación educativa, no una puntuación CVSS ni una clasificación oficial. Depende de permisos, datos y controles.')
table(['Tipo o técnica','Descripción','Peligrosidad potencial'],[
 ('Omisión de autenticación','Altera condiciones o introduce comentarios para omitir la contraseña.','Crítica al suplantar cuentas privilegiadas.'),
 ('Basada en UNION','Combina resultados de la consulta original con otra consulta.','Alta a crítica por exposición de datos.'),
 ('Basada en errores','Usa errores para revelar estructura o información.','Alta a crítica según los datos revelados.'),
 ('Ciega por booleanos','Deduce información comparando respuestas a condiciones verdaderas y falsas.','Alta a crítica según lo deducible.'),
 ('Ciega por tiempo','Deduce información mediante demoras condicionadas.','Alta a crítica; posible impacto en disponibilidad.'),
 ('Consultas apiladas','Intenta ejecutar sentencias adicionales si motor y controlador lo permiten.','Crítica si permite modificar o borrar datos.'),
 ('Fuera de banda','Recupera resultados por otro canal si motor y red lo permiten.','Alta a crítica por extracción de datos.'),
 ('De segundo orden','Una entrada almacenada se reutiliza después en SQL construido de forma insegura.','Alta a crítica según la operación posterior.'),
],[125,220,W-88-345])
text('No todas estas técnicas aplican a este login. La práctica inicial confirmó la omisión de contraseña mediante comentario. Las pruebas posteriores verifican el rechazo de entradas concretas; no constituyen una explotación de todas las técnicas de la tabla.')
text('Fuentes: OWASP Web Security Testing Guide, sección de SQL Injection; OWASP SQL Injection y SQL Injection Prevention Cheat Sheet. Enlaces en la página 6.')
c.showPage()

page(6,'Verificación posterior al cambio')
text('Las pruebas automatizadas de login/test-login.cjs inician y cierran un servidor en 127.0.0.1 con puerto asignado por el sistema. Ejecución: <b>cd login</b>, después <b>npm test</b>. Resultado: 12 casos HTTP aprobados; el ejecutor cuenta 13 pruebas al incluir la contenedora.')
table(['Caso','HTTP esperado y observado'],[
 ('Admin válido / Juan válido','200 / 200'),
 ('Admin con contraseña incorrecta','401'),
 ("Usuario admin' -- con contraseña incorrecta",'401'),
 ('Tautología en usuario / en contraseña','401 / 401'),
 ('Consulta apilada enviada como texto','401'),
 ('Usuario con comilla literal','401'),
 ('Campos ausentes / tipo inválido / cadena vacía','400 / 400 / 400'),
 ('Admin válido después de los intentos','200'),
],[320,W-88-320])
heading('Interpretación y alcance')
text('El payload que antes devolvía admin ahora es rechazado. Los accesos legítimos siguen funcionando y la tabla de usuarios permanece utilizable tras los intentos. No se ejecutaron pruebas de extracción por UNION, errores, tiempo, fuera de banda o segundo orden.')
text('La salida de la verificación se conserva en <b>evidencias/pruebas-parametrizacion.txt</b>. Las capturas y respuestas-http.json originales documentan el estado anterior; no deben interpretarse como resultados del código corregido.')
heading('Referencias')
text('<link href="https://wstg.owasp.org/stable/4-Web_Application_Security_Testing/07-Input_Validation_Testing/05-Testing_for_SQL_Injection/" color="#136A84">OWASP Web Security Testing Guide: SQL Injection</link><br/><link href="https://owasp.org/www-community/attacks/SQL_Injection" color="#136A84">OWASP: SQL Injection e impacto</link><br/><link href="https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html" color="#136A84">OWASP: SQL Injection Prevention Cheat Sheet</link><br/><link href="https://www.sqlite.org/lang_expr.html#parameters" color="#136A84">SQLite: parámetros en expresiones SQL</link>')
c.showPage()

page(7,'Payloads que funcionan y su causa')
style.fontSize=10
style.leading=13
text('Se ejecutó la misma petición POST /login-vulnerable contra dos servidores locales aislados: la revisión vulnerable fc48115 y el código parametrizado actual. Se conservan las consultas originales; el envoltorio solo asigna puertos dinámicos en 127.0.0.1. Los servidores se cerraron al terminar.')
comparison=json.loads((E/'comparacion-payloads.json').read_text())
old=comparison['resultados'][0]['casos']
new=comparison['resultados'][1]['casos']
rows=[]
for a,b in zip(old[1:5],new[1:5]):
 rows.append((a['caso'].split(':')[0],a['solicitud']['username'],a['solicitud']['password'],f"{a['http']} / {a['respuesta']['user']}",str(b['http'])))
table(['Caso','Usuario exacto','Contraseña exacta','Vulnerable','Corregida'],rows,[42,125,128,68,W-88-363],fontsize=8.5)
text('P1, P2 y P3 llevan un espacio después de <b>--</b>. En todos los casos la respuesta vulnerable fue <b>ok: true</b> y la corregida <b>ok: false</b>. Los valores son datos de laboratorio.')
heading('P1 y P2: comentario tras un usuario conocido')
code("SELECT * FROM users WHERE username = 'admin' -- '\nAND password = 'incorrecta'",padding=10)
text('La comilla cierra el nombre del usuario. El comentario -- anula el resto de la línea, incluida la comparación de contraseña. La consulta efectiva busca solo admin. P2 hace lo mismo con juan y devuelve juan. El salto de línea mostrado es únicamente de presentación; el SQL original es una sola línea.')
heading('P3: condición verdadera en el usuario')
code("SELECT * FROM users WHERE username = '' OR 1=1 -- '\nAND password = 'incorrecta'",padding=10)
text('El predicado OR 1=1 es verdadero y el comentario elimina la condición de contraseña. Se seleccionan filas sin validar credenciales. db.get devuelve una sola fila; en esta ejecución fue admin. Al no existir ORDER BY, ese orden no debe darse por garantizado.')
heading('P4: condición verdadera en la contraseña')
code("SELECT * FROM users WHERE username = 'admin'\nAND password = '' OR '1'='1'",padding=10)
text('La comilla de la entrada cierra el literal de contraseña. La comparación OR \'1\'=\'1\' siempre es verdadera. AND se evalúa antes que OR, por lo que el predicado completo acepta filas aunque la contraseña no coincida. En la prueba, db.get devolvió admin.')
assert y > 55, f'Texto fuera de página: {y}'
c.showPage()

page(8,'Parametrización y conclusiones')
style.fontSize=11
style.leading=16
heading('Corrección de la petición SQL')
text('El servidor mantiene fijo el texto SQL y enlaza ambos campos con sqlite3. La petición HTTP continúa enviando JSON; la protección se aplica al construir y ejecutar la consulta en el servidor. Fragmento aplicado en login/server-vulnerable.js:')
code('const query =\n  "SELECT username FROM users" +\n  " WHERE username = ? AND password = ?";\n\ndb.get(query, [username, password], (err, row) => {\n  if (err) return res.status(500).json({\n    ok: false, message: "Error interno del servidor"\n  });\n  if (row) return res.json({ ok: true, user: row.username });\n  res.status(401).json({\n    ok: false, message: "Credenciales inválidas"\n  });\n});')
text('Los signos ? son marcadores. El arreglo [username, password] proporciona los valores, sin concatenarlos al SQL. Así, admin\' -- se busca como nombre completo y \' OR \'1\'=\'1 como contraseña literal: las comillas, OR y -- contenidos en los valores no se interpretan como estructura de la consulta.')
heading('Resultados y evidencia reproducible')
text('Ejecutar <b>python3 output/pdf/comparar_payloads.py</b> desde la raíz del repositorio. Evidencia: <b>evidencias/comparacion-payloads.json</b>, con fecha UTC, entradas y respuestas. Se aprobaron 12 comparaciones HTTP: seis por versión. Los cuatro payloads pasan de 200 a 401; el control negativo sigue en 401 y el positivo sigue en 200. Esta comparación complementa las pruebas de npm test descritas en la página 6.')
heading('Conclusiones')
text('1. Los cuatro payloads funcionaron porque las entradas del cliente se incorporaban al código SQL y cambiaban sus condiciones.<br/>2. La parametrización aplicada impide esa alteración en los casos comprobados, manteniendo el inicio de sesión con credenciales válidas.<br/>3. Validar tipos y evitar revelar errores o contraseñas complementa la corrección; no sustituye los parámetros.<br/>4. El resultado demuestra aceptación de identidad en JSON, sin acreditar una sesión ni acceso a recursos privados. El laboratorio conserva contraseñas en texto claro y requiere hash de contraseñas y sesiones antes de un uso real.')
c.showPage(); c.save()
manifest={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in E.iterdir() if p.is_file() and p.name!='sha256.json'}
(E/'sha256.json').write_text(json.dumps(manifest,indent=2))
print(ROOT/'reporte-laboratorio-sqli.pdf')
