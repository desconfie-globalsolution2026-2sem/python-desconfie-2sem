"""Ponto de entrada WSGI alternativo para provedores de hospedagem."""

from app import app


if __name__ == "__main__":
    app.run()
