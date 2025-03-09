import functools
import textwrap
from abc import ABC, abstractclassmethod, abstractproperty
from datetime import datetime


class ContaIterador:
    def __init__(self, contas):
        self.__contas = contas
        self.__contador = 0

    def __iter__(self):
        return self

    def __next__(self):
        try:
            conta = self.__contas[self.__contador]
            self.__contador += 1
            return conta
        except IndexError as exc:
            raise StopIteration from exc


class Cliente:
    def __init__(self, endereco):
        self.endereco = endereco
        self.contas = []

    def realizar_transacao(self, conta, transacao):
        if len(conta.historico.transacoes_do_dia()) >= 10:
            print(
                "\n@@@ Operação falhou! Você excedeu numero de operações do dia [10]. @@@"
            )
            return

        transacao.registrar(conta)

    def adicionar_conta(self, conta):
        self.contas.append(conta)


class PessoaFisica(Cliente):
    def __init__(self, nome, data_nascimento, cpf, endereco):
        super().__init__(endereco)
        self.nome = nome
        self.data_nascimento = data_nascimento
        self.cpf = cpf


class Conta:
    def __init__(self, numero, cliente):
        self._saldo = 0
        self._numero = numero
        self._agencia = "0001"
        self._cliente = cliente
        self._historico = Historico()

    @classmethod
    def nova_conta(cls, cliente, numero):
        return cls(numero, cliente)

    @property
    def saldo(self):
        return self._saldo

    @property
    def numero(self):
        return self._numero

    @property
    def agencia(self):
        return self._agencia

    @property
    def cliente(self):
        return self._cliente

    @property
    def historico(self):
        return self._historico

    def sacar(self, valor):
        saldo = self.saldo
        excedeu_saldo = valor > saldo

        if excedeu_saldo:
            print("\n@@@ Operação falhou! Você não tem saldo suficiente. @@@")

        elif valor > 0:
            self._saldo -= valor
            print("\n=== Saque realizado com sucesso! ===")
            return True

        else:
            print("\n@@@ Operação falhou! O valor informado é inválido. @@@")

        return False

    def depositar(self, valor):
        if valor > 0:
            self._saldo += valor
            print("\n=== Depósito realizado com sucesso! ===")
        else:
            print("\n@@@ Operação falhou! O valor informado é inválido. @@@")
            return False

        return True


class ContaCorrente(Conta):
    def __init__(self, numero, cliente, limite=500, limite_saques=3):
        super().__init__(numero, cliente)
        self._limite = limite
        self._limite_saques = limite_saques

    def sacar(self, valor):
        numero_saques = len(
            [
                transacao
                for transacao in self.historico.transacoes
                if transacao["tipo"] == Saque.__name__
            ]
        )

        excedeu_limite = valor > self._limite
        excedeu_saques = numero_saques >= self._limite_saques

        if excedeu_limite:
            print("\n@@@ Operação falhou! O valor do saque excede o limite. @@@")

        elif excedeu_saques:
            print("\n@@@ Operação falhou! Número máximo de saques excedido. @@@")

        else:
            return super().sacar(valor)

        return False

    def __str__(self):
        return f"""\
            Agência:\t{self.agencia}
            C/C:\t\t{self.numero}
            Titular:\t{self.cliente.nome}
        """


class Historico:
    formato = "%d-%m-%Y %H:%M:%S"

    def __init__(self):
        self._transacoes = []

    @property
    def transacoes(self):
        return self._transacoes

    def adicionar_transacao(self, transacao):
        self._transacoes.append(
            {
                "tipo": transacao.__class__.__name__,
                "valor": transacao.valor,
                "data": datetime.now().strftime(Historico.formato),
            }
        )

    def gerar_relatorio(self, tipo_transacao=None):
        tipo = None
        if tipo_transacao and str(tipo_transacao).strip():
            tipo = str(tipo_transacao).strip().lower()[0]
        for transacao in self._transacoes:
            if tipo is None:
                yield transacao
            else:
                if tipo == str(transacao["tipo"]).strip().lower()[0]:
                    yield transacao

    def transacoes_do_dia(self):
        dia = datetime.now().date()
        transacoes = []
        for transacao in self._transacoes:
            if dia == datetime.strptime(transacao["data"], Historico.formato).date():
                transacoes.append(transacao)
        return transacoes


class Transacao(ABC):
    @property
    @abstractproperty
    def valor(self):
        pass

    @abstractclassmethod
    def registrar(self, conta):
        pass


class Saque(Transacao):
    def __init__(self, valor):
        self._valor = valor

    @property
    def valor(self):
        return self._valor

    def registrar(self, conta):
        sucesso_transacao = conta.sacar(self.valor)

        if sucesso_transacao:
            conta.historico.adicionar_transacao(self)


class Deposito(Transacao):
    def __init__(self, valor):
        self._valor = valor

    @property
    def valor(self):
        return self._valor

    def registrar(self, conta):
        sucesso_transacao = conta.depositar(self.valor)

        if sucesso_transacao:
            conta.historico.adicionar_transacao(self)


def log_transacao(func):
    @functools.wraps(func)
    def envelope(*args, **kwargs):
        print(
            f"\n{str(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))}) Inicio da função :: {func.__name__}\n"
        )
        func(*args, **kwargs)
        print(
            f"\n{str(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))}) Fim da função :: {func.__name__}\n"
        )

    return envelope


def menu():
    menu = """\n
    ================ MENU ================
    [d]\tDepositar
    [s]\tSacar
    [e]\tExtrato
    [nc]\tNova conta
    [lc]\tListar contas
    [nu]\tNovo usuário
    [q]\tSair
    => """
    return input(textwrap.dedent(menu))


def filtrar_cliente(cpf, clientes):
    clientes_filtrados = [cliente for cliente in clientes if cliente.cpf == cpf]
    return clientes_filtrados[0] if clientes_filtrados else None


def recuperar_conta_cliente(cliente):
    if not cliente.contas:
        print("\n@@@ Cliente não possui conta! @@@")
        return

    # FIXME: não permite cliente escolher a conta
    return cliente.contas[0]


@log_transacao
def depositar(clientes):
    cpf = None
    while cpf is None:
        try:
            cpf = str(int(input("Informe o CPF (somente número) do cliente: "))).zfill(
                11
            )
        except ValueError:
            cpf = None

    cliente = filtrar_cliente(cpf, clientes)

    if not cliente:
        print("\n@@@ Cliente não encontrado! @@@")
        return

    valor = float(input("Informe o valor do depósito: "))
    transacao = Deposito(valor)

    conta = recuperar_conta_cliente(cliente)
    if not conta:
        return

    cliente.realizar_transacao(conta, transacao)


@log_transacao
def sacar(clientes):
    cpf = None
    while cpf is None:
        try:
            cpf = str(int(input("Informe o CPF (somente número) do cliente: "))).zfill(
                11
            )
        except ValueError:
            cpf = None

    cliente = filtrar_cliente(cpf, clientes)

    if not cliente:
        print("\n@@@ Cliente não encontrado! @@@")
        return

    valor = float(input("Informe o valor do saque: "))
    transacao = Saque(valor)

    conta = recuperar_conta_cliente(cliente)
    if not conta:
        return

    cliente.realizar_transacao(conta, transacao)


@log_transacao
def exibir_extrato(clientes):
    cpf = None
    while cpf is None:
        try:
            cpf = str(int(input("Informe o CPF (somente número) do cliente: "))).zfill(
                11
            )
        except ValueError:
            cpf = None

    cliente = filtrar_cliente(cpf, clientes)

    if not cliente:
        print("\n@@@ Cliente não encontrado! @@@")
        return

    conta = recuperar_conta_cliente(cliente)
    if not conta:
        print("\n@@@ Cliente não possui conta! @@@")
        return

    tipo = str(
        input("Filtrar extrato por tipo (saque [s], depósito [d], ou ambos [enter])?")
    )

    print("\n================ EXTRATO ================")
    # TODO: atualizar a implementação para utilizar o gerador definido em Historico
    transacoes = conta.historico.transacoes

    extrato = ""
    if not transacoes:
        extrato = "Não foram realizadas movimentações."
    else:
        for transacao in conta.historico.gerar_relatorio(tipo):
            extrato += f"\n{transacao['tipo']}:\n\tR$ {transacao['valor']:.2f}"

    print(extrato)
    print(f"\nSaldo:\n\tR$ {conta.saldo:.2f}")
    print("==========================================")


@log_transacao
def criar_cliente(clientes):
    cpf = None
    while cpf is None:
        try:
            cpf = str(int(input("Informe o CPF (somente número): "))).zfill(11)
        except ValueError:
            cpf = None

    cliente = filtrar_cliente(cpf, clientes)

    if cliente:
        print("\n@@@ Já existe cliente com esse CPF! @@@")
        return

    nome = input("Informe o nome completo: ")
    data_nascimento = input("Informe a data de nascimento (dd-mm-aaaa): ")
    if not data_nascimento:
        data_nascimento = str(datetime.now().strftime("%d-%m-%Y"))
    endereco = input(
        "Informe o endereço (logradouro, nro - bairro - cidade/sigla estado): "
    )
    if not endereco:
        endereco = "logradouro, nro - bairro - cidade/sigla"

    cliente = PessoaFisica(
        nome=nome, data_nascimento=data_nascimento, cpf=cpf, endereco=endereco
    )

    clientes.append(cliente)

    print("\n=== Cliente criado com sucesso! ===")


@log_transacao
def criar_conta(numero_conta, clientes, contas):
    cpf = None
    while cpf is None:
        try:
            cpf = str(int(input("Informe o CPF (somente número) do cliente: "))).zfill(
                11
            )
        except ValueError:
            cpf = None

    cliente = filtrar_cliente(cpf, clientes)

    if not cliente:
        print("\n@@@ Cliente não encontrado, fluxo de criação de conta encerrado! @@@")
        return

    conta = ContaCorrente.nova_conta(cliente=cliente, numero=numero_conta)
    contas.append(conta)
    cliente.contas.append(conta)

    print("\n=== Conta criada com sucesso! ===")


def listar_contas(contas):
    # TODO: alterar implementação, para utilizar a classe ContaIterador
    for conta in ContaIterador(contas):
        print("=" * 100)
        print(textwrap.dedent(str(conta)))


def main(lista_clientes=[], lista_contas=[]):
    clientes = []
    contas = []
    if lista_clientes and isinstance(lista_clientes, list):
        clientes.extend(lista_clientes)
    if lista_contas and isinstance(lista_contas, list):
        contas.extend(lista_contas)

    while True:
        opcao = menu()

        if opcao == "d":
            depositar(clientes)

        elif opcao == "s":
            sacar(clientes)

        elif opcao == "e":
            exibir_extrato(clientes)

        elif opcao == "nu":
            criar_cliente(clientes)

        elif opcao == "nc":
            numero_conta = len(contas) + 1
            criar_conta(numero_conta, clientes, contas)

        elif opcao == "lc":
            listar_contas(contas)

        elif opcao == "q":
            break

        else:
            print(
                "\n@@@ Operação inválida, por favor selecione novamente a operação desejada. @@@"
            )


def setar_massa_de_dados():
    cliente = PessoaFisica(
        nome="João Silva",
        data_nascimento="01-01-1990",
        cpf="00000000000",
        endereco="Rua A, 123 - Bairro B - Cidade C/UF",
    )
    conta = ContaCorrente(numero=1, cliente=cliente)
    cliente.adicionar_conta(conta)
    for qt in range(8):
        deposito = Deposito(valor=100 + qt)
        cliente.realizar_transacao(conta, deposito)
    saque = Saque(valor=100)
    cliente.realizar_transacao(conta, saque)
    lista_clientes = [cliente]
    lista_contas = [conta]
    return lista_clientes, lista_contas


if __name__ == "__main__":
    lista_clientes, lista_contas = setar_massa_de_dados()
    main(lista_clientes, lista_contas)
