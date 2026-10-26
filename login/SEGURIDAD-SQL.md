# Tipos de inyección SQL y protección del login

Actualizado: 26 de octubre de 2026.

La tabla resume técnicas comunes, objetivos y formas de activación; pueden combinarse. La peligrosidad es una estimación educativa del impacto potencial, no una puntuación CVSS ni una clasificación oficial. Depende de los permisos de la base, los datos accesibles y los controles de la aplicación. Una técnica ciega también puede tener impacto crítico.

| Tipo o técnica | En qué consiste | Peligrosidad potencial |
| --- | --- | --- |
| Omisión de autenticación mediante condiciones o comentarios | Altera el filtro del login para aceptar una identidad sin validar su contraseña. | Crítica si permite suplantar cuentas privilegiadas. |
| Basada en UNION | Combina resultados de otra consulta con los de la consulta original. | Alta a crítica por exposición de información. |
| Basada en errores | Utiliza mensajes de error para revelar estructura o datos. | Alta; crítica si permite extraer información sensible. |
| Ciega basada en booleanos | Deduce información comparando respuestas a condiciones verdaderas y falsas. | Alta a crítica según la información deducible. |
| Ciega basada en tiempo | Deduce información mediante diferencias de tiempo condicionadas. | Alta a crítica; también puede afectar la disponibilidad. |
| Consultas apiladas | Intenta ejecutar sentencias adicionales si el motor y el controlador lo permiten. | Crítica si permite modificar o eliminar datos. |
| Fuera de banda | Usa un canal distinto para recuperar resultados, si el motor y la red lo permiten. | Alta a crítica por posible extracción de información. |
| De segundo orden | Una entrada almacenada se reutiliza después en una consulta construida de forma insegura. | Alta a crítica según la operación posterior. |

Estas técnicas no se han explotado todas en este laboratorio. La práctica previa confirmó únicamente la omisión de contraseña mediante un comentario en el nombre de usuario. El servidor devuelve una identidad en JSON; no implementa sesiones ni un panel privado.

## Cambio aplicado

En `server-vulnerable.js` se sustituyó la interpolación por una consulta fija:

```js
const query = "SELECT username FROM users WHERE username = ? AND password = ?";
db.get(query, [username, password], (err, row) => {
  // Manejo de respuesta.
});
```

El controlador enlaza los valores por separado. Una comilla o un comentario dentro del usuario o la contraseña se trata como contenido del valor, sin cambiar el SQL. La validación de tipos complementa la parametrización; no la reemplaza. También se parametrizaron las inserciones de los usuarios de demostración.

Se conserva `/login-vulnerable` por compatibilidad con el formulario, aunque la consulta ya está parametrizada. El servidor escucha solo en `127.0.0.1`, evita registrar credenciales y responde con un error genérico si falla la base.

## Verificación reproducible

Desde esta carpeta:

```sh
npm ci
npm test
node server-vulnerable.js
```

Las pruebas inician y cierran un servidor local en un puerto asignado por el sistema. Se verificaron 12 casos HTTP: dos usuarios válidos (200), contraseña incorrecta (401), comentario en usuario (401), tautologías en ambos campos (401), consulta apilada como texto (401), nombre con comilla literal (401), campos ausentes (400), tipo inválido (400), cadena vacía (400) y acceso válido después de los intentos (200). El ejecutor informa 13 pruebas al contar también la prueba contenedora.

El payload de la práctica anterior, `admin' -- ` con contraseña `incorrecta`, ahora devuelve 401. No se implementaron ni probaron aquí extracción por errores, tiempos, UNION, fuera de banda o segundo orden.

El PDF de la práctica previa en `../output/pdf/` conserva evidencia histórica de la versión vulnerable, anterior a esta corrección.

## Limitación del laboratorio

Las contraseñas de demostración siguen almacenadas en texto claro. La parametrización corrige esta vía de inyección, pero no convierte el ejemplo en un sistema de autenticación listo para producción. Un diseño real requiere almacenamiento de contraseñas mediante hash apropiado y gestión de sesiones.

## Fuentes

- [OWASP: pruebas de inyección SQL](https://wstg.owasp.org/stable/4-Web_Application_Security_Testing/07-Input_Validation_Testing/05-Testing_for_SQL_Injection/).
- [OWASP: impacto de la inyección SQL](https://owasp.org/www-community/attacks/SQL_Injection).
- [OWASP: prevención mediante consultas parametrizadas](https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html).
