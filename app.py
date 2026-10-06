
from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

DATABASE = "fila.db"


# Conectar ao banco
def conectar_banco():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# Criar tabela
def criar_banco():
    conn = conectar_banco()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS atendimentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            prioridade TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Aguardando',
            data_hora DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


# Página principal
@app.route("/")
def index():
    conn = conectar_banco()

    fila = conn.execute("""
        SELECT * FROM atendimentos
        WHERE status = 'Aguardando'
        ORDER BY
            CASE WHEN prioridade = 'Preferencial' THEN 0 ELSE 1 END,
            id ASC
    """).fetchall()

    atendimento = conn.execute("""
        SELECT * FROM atendimentos
        WHERE status = 'Em Atendimento'
        ORDER BY id ASC
        LIMIT 1
    """).fetchone()

    conn.close()

    return render_template(
        "index.html",
        fila=fila,
        atendimento=atendimento
    )


# Cadastrar cliente
@app.route("/cadastrar", methods=["POST"])
def cadastrar():
    nome = request.form["nome"]
    prioridade = request.form["prioridade"]

    if nome.strip():
        conn = conectar_banco()

        conn.execute("""
            INSERT INTO atendimentos (nome, prioridade, status)
            VALUES (?, ?, 'Aguardando')
        """, (nome, prioridade))

        conn.commit()
        conn.close()

    return redirect(url_for("index"))


# Chamar próximo cliente
@app.route("/chamar")
def chamar():
    conn = conectar_banco()

    # Verifica se já existe alguém sendo atendido
    atual = conn.execute("""
        SELECT * FROM atendimentos
        WHERE status = 'Em Atendimento'
        LIMIT 1
    """).fetchone()

    if not atual:
        proximo = conn.execute("""
            SELECT * FROM atendimentos
            WHERE status = 'Aguardando'
            ORDER BY
                CASE WHEN prioridade = 'Preferencial' THEN 0 ELSE 1 END,
                id ASC
            LIMIT 1
        """).fetchone()

        if proximo:
            conn.execute("""
                UPDATE atendimentos
                SET status = 'Em Atendimento'
                WHERE id = ?
            """, (proximo["id"],))

            conn.commit()

    conn.close()

    return redirect(url_for("index"))


# Concluir atendimento
@app.route("/concluir/<int:id>")
def concluir(id):
    conn = conectar_banco()

    conn.execute("""
        UPDATE atendimentos
        SET status = 'Concluído'
        WHERE id = ?
    """, (id,))

    conn.commit()
    conn.close()

    return redirect(url_for("index"))


# Cancelar atendimento
@app.route("/cancelar/<int:id>")
def cancelar(id):
    conn = conectar_banco()

    conn.execute("""
        UPDATE atendimentos
        SET status = 'Cancelado'
        WHERE id = ?
    """, (id,))

    conn.commit()
    conn.close()

    return redirect(url_for("index"))


# Histórico
@app.route("/historico")
def historico():
    conn = conectar_banco()

    atendimentos = conn.execute("""
        SELECT * FROM atendimentos
        WHERE status IN ('Concluído', 'Cancelado')
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    return render_template(
        "historico.html",
        atendimentos=atendimentos
    )


if __name__ == "__main__":
    criar_banco()
    app.run(debug=True)