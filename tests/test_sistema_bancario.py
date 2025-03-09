import os
import sys
import unittest
from datetime import datetime
# Adiciona o caminho do módulo 'src' ao sys.path
sys.path.insert(
    0, os.path.abspath(os.path.join(
        os.path.dirname(__file__), ".."))
)
from src.sistemabancario.sistema_bancario import (
    Cliente, PessoaFisica, ContaCorrente, Deposito, Saque, Historico
)


class TestSistemaBancario(unittest.TestCase):

    def setUp(self):
        self.cliente = PessoaFisica(
            nome="João Silva",
            data_nascimento="01-01-1990",
            cpf="12345678901",
            endereco="Rua A, 123 - Bairro B - Cidade C/UF"
        )
        self.conta = ContaCorrente(numero=1, cliente=self.cliente)
        self.cliente.adicionar_conta(self.conta)

    def test_deposito(self):
        deposito = Deposito(valor=100)
        self.cliente.realizar_transacao(self.conta, deposito)
        self.assertEqual(self.conta.saldo, 100)

    def test_saque(self):
        deposito = Deposito(valor=200)
        self.cliente.realizar_transacao(self.conta, deposito)
        saque = Saque(valor=100)
        self.cliente.realizar_transacao(self.conta, saque)
        self.assertEqual(self.conta.saldo, 100)

    def test_saque_sem_saldo(self):
        saque = Saque(valor=100)
        self.cliente.realizar_transacao(self.conta, saque)
        self.assertEqual(self.conta.saldo, 0)

    def test_historico_transacoes(self):
        deposito = Deposito(valor=150)
        self.cliente.realizar_transacao(self.conta, deposito)
        saque = Saque(valor=50)
        self.cliente.realizar_transacao(self.conta, saque)
        transacoes = list(self.conta.historico.gerar_relatorio())
        self.assertEqual(len(transacoes), 2)
        self.assertEqual(transacoes[0]["tipo"], "Deposito")
        self.assertEqual(transacoes[1]["tipo"], "Saque")


if __name__ == "__main__":
    unittest.main()
