const { test } = require("node:test");
const assert = require("node:assert/strict");
const { spawn } = require("node:child_process");
const { once } = require("node:events");
const { createInterface } = require("node:readline");

test("el login enlaza las entradas como datos y conserva los accesos válidos", { timeout: 15000 }, async (t) => {
  const child = spawn(process.execPath, ["server-vulnerable.js"], {
    cwd: __dirname,
    env: { ...process.env, PORT: "0" },
    stdio: ["ignore", "pipe", "pipe"],
  });
  const lines = createInterface({ input: child.stdout });
  const ready = once(lines, "line");
  const failure = new Promise((_, reject) => {
    child.once("error", reject);
    child.once("exit", (code) => reject(new Error(`Servidor finalizado: ${code}`)));
  });
  t.after(async () => {
    lines.close();
    if (child.exitCode === null && child.signalCode === null) {
      const closed = once(child, "exit");
      child.kill();
      await closed;
    }
  });
  const [url] = await Promise.race([ready, failure]);
  assert.match(url, /^http:\/\/127\.0\.0\.1:\d+$/);

  const cases = [
    ["admin válido", { username: "admin", password: "admin" }, 200, "admin"],
    ["juan válido", { username: "juan", password: "1234" }, 200, "juan"],
    ["contraseña incorrecta", { username: "admin", password: "incorrecta" }, 401],
    ["comentario en usuario", { username: "admin' -- ", password: "incorrecta" }, 401],
    ["tautología en usuario", { username: "' OR 1=1 -- ", password: "incorrecta" }, 401],
    ["tautología en contraseña", { username: "admin", password: "' OR '1'='1" }, 401],
    ["consulta apilada como texto", { username: "admin'; DROP TABLE users; -- ", password: "x" }, 401],
    ["usuario con comilla literal", { username: "O'Reilly", password: "x" }, 401],
    ["campos ausentes", {}, 400],
    ["tipo inválido", { username: { value: "admin" }, password: "admin" }, 400],
    ["cadena vacía", { username: "", password: "admin" }, 400],
    ["tabla intacta tras intentos", { username: "admin", password: "admin" }, 200, "admin"],
  ];
  for (const [name, body, status, user] of cases) {
    await t.test(name, async () => {
      const response = await fetch(`${url}/login-vulnerable`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      assert.equal(response.status, status);
      const data = await response.json();
      assert.equal(data.ok, status === 200);
      if (user) assert.equal(data.user, user);
    });
  }
});
