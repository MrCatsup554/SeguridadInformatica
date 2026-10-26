
// npm init -v
// npm install express sqlite3
// node server-vulnerable.js

const express = require("express");
const sqlite3 = require("sqlite3").verbose();

const app = express();
app.use(express.json());
app.use(express.static(__dirname));

const db = new sqlite3.Database(":memory:");


db.serialize(() => {
  db.run(
    "CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT, password TEXT)",
  );
  db.run("INSERT INTO users (username, password) VALUES (?, ?)", ["admin", "admin"]);
  db.run("INSERT INTO users (username, password) VALUES (?, ?)", ["juan", "1234"]);
});


// Se conserva la ruta original para mantener compatible el formulario.
app.post("/login-vulnerable", (req, res) => {
  const { username, password } = req.body ?? {};

  if (typeof username !== "string" || typeof password !== "string" ||
      username.length === 0 || password.length === 0) {
    return res.status(400).json({ ok: false, message: "Usuario y contraseña requeridos" });
  }

  const query = "SELECT username FROM users WHERE username = ? AND password = ?";

  db.get(query, [username, password], (err, row) => {
    if (err) return res.status(500).json({ ok: false, message: "Error interno del servidor" });
    if (row) return res.json({ ok: true, user: row.username });
    res.status(401).json({ ok: false, message: "Credenciales inválidas" });
  });
});

const server = app.listen(Number(process.env.PORT ?? 3000), "127.0.0.1", () => {
  console.log(`http://127.0.0.1:${server.address().port}`);
});
