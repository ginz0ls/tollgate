"""Avviso con riassunto: usa l'SDK di Anthropic, che il progetto di prova non installa."""
from anthropic import Anthropic


def costruisci_client():
    return Anthropic()
