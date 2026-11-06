# Simulador do caminho de dados da Mic-1 - Etapa 2

import sys

MASK = 0xFFFFFFFF
A_INICIAL = 0xFFFFFFFF
B_INICIAL = 0x00000001

REGISTRADORES = ["H", "OPC", "TOS", "CPP", "LV", "SP", "MBR", "PC", "MDR", "MAR"]
REGISTRADORES_32 = ["H", "OPC", "TOS", "CPP", "LV", "SP", "PC", "MDR", "MAR"]

BARRAMENTO_B = {
    0: "MDR",
    1: "PC",
    2: "MBR",
    3: "MBRU",
    4: "SP",
    5: "LV",
    6: "CPP",
    7: "TOS",
    8: "OPC"
}

BARRAMENTO_C = {
    8: "H",
    7: "OPC",
    6: "TOS",
    5: "CPP",
    4: "LV",
    3: "SP",
    2: "PC",
    1: "MDR",
    0: "MAR"
}


def bin32(x):
    #texto de 32 bits
    return format(x & MASK, "032b")


def valor_arquivo(texto):
    texto = texto.strip()
    if texto.lower().startswith("0b"):
        return int(texto, 2)
    if texto.lower().startswith("0x"):
        return int(texto, 16)
    if texto and all(c in "01" for c in texto) and len(texto) in (8, 32):
        return int(texto, 2)
    return int(texto, 10)


def ler_linhas(caminho):
    with open(caminho, "r", encoding="utf-8") as arquivo:
        linhas = []
        for linha in arquivo:
            linha = linha.split("#", 1)[0].strip()
            if linha:
                linhas.append(linha)
    return linhas


def ula(a, b, ir):
    SLL8, SRA1, F0, F1, ENA, ENB, INVA, INC = (int(c) for c in ir)

    if SLL8 == 1 and SRA1 == 1:
        raise ValueError("SLL8 e SRA1 não podem estar ativos ao mesmo tempo.")

    if ENA == 0:
        a = 0
    if ENB == 0:
        b = 0
    if INVA == 1:
        a = ~a & MASK

    #escolhe a operação pelo par (F0, F1)
    co = 0
    if (F0, F1) == (0, 0):
        s = a & b
    elif (F0, F1) == (0, 1):
        s = a | b
    elif (F0, F1) == (1, 0):
        s = ~b & MASK
    else:
        total = a + b + INC
        s = total & MASK
        co = total >> 32

    #desloca o resultado da ULA
    if SLL8 == 1:
        sd = (s << 8) & MASK
    elif SRA1 == 1:
        valor_assinado = s if s < 0x80000000 else s - 0x100000000
        sd = (valor_assinado >> 1) & MASK
    else:
        sd = s

    n = (sd >> 31) & 1
    z = 1 if sd == 0 else 0
    return a & MASK, b & MASK, s, sd, co, n, z


def executar_tarefa1(caminho_programa):
    linhas = ler_linhas(caminho_programa)
    log = []
    log.append("TAREFA 1 - ULA DE 8 BITS DE CONTROLE")
    log.append(f"A inicial = {bin32(A_INICIAL)}")
    log.append(f"B inicial = {bin32(B_INICIAL)}")

    for pc, ir in enumerate(linhas, start=1):
        if len(ir) != 8 or any(c not in "01" for c in ir):
            raise ValueError(f"Instrução inválida na linha {pc}: {ir}")

        a, b, s, sd, co, n, z = ula(A_INICIAL, B_INICIAL, ir)
        log.append("=" * 60)
        log.append(f"Ciclo {pc}")
        log.append(f"PC = {pc}")
        log.append(f"IR = {ir}")
        log.append(f"A = {bin32(a)}")
        log.append(f"B = {bin32(b)}")
        log.append(f"S = {bin32(s)}")
        log.append(f"Sd = {bin32(sd)}")
        log.append(f"Vai-um = {co}")
        log.append(f"N = {n}")
        log.append(f"Z = {z}")

    return "\n".join(log)


def ler_registradores(caminho):
    estado = {}
    valores_sem_nome = []

    for linha in ler_linhas(caminho):
        if "=" in linha:
            nome, valor = linha.split("=", 1)
            estado[nome.strip().upper()] = valor_arquivo(valor)
        elif ":" in linha:
            nome, valor = linha.split(":", 1)
            estado[nome.strip().upper()] = valor_arquivo(valor)
        else:
            partes = linha.replace(",", " ").split()
            if len(partes) == 2 and partes[0].upper() in REGISTRADORES:
                estado[partes[0].upper()] = valor_arquivo(partes[1])
            elif len(partes) == 1:
                valores_sem_nome.append(valor_arquivo(partes[0]))
            else:
                raise ValueError(f"Formato inválido no arquivo de registradores: {linha}")

    if valores_sem_nome:
        if estado:
            raise ValueError("Não misture valores sem nome com registradores identificados.")
        if len(valores_sem_nome) != len(REGISTRADORES):
            raise ValueError("O arquivo deve conter os valores dos dez registradores.")
        estado = dict(zip(REGISTRADORES, valores_sem_nome))

    faltando = [nome for nome in REGISTRADORES if nome not in estado]
    if faltando:
        raise ValueError("Registradores ausentes no arquivo: " + ", ".join(faltando))

    for nome in REGISTRADORES_32:
        estado[nome] &= MASK
    estado["MBR"] &= 0xFF
    return estado


def valor_barramento_b(codigo, registradores):
    if codigo not in BARRAMENTO_B:
        raise ValueError(f"Código do barramento B não utilizado: {codigo:04b}")

    nome = BARRAMENTO_B[codigo]
    valor = registradores[nome] if nome != "MBRU" else registradores["MBR"]

    if nome == "MBR" and valor & 0x80:
        valor = valor | 0xFFFFFF00
    elif nome == "MBRU":
        valor = valor & 0xFF

    return nome, valor & MASK


def registradores_barramento_c(controle):
    selecionados = []
    for bit, nome in BARRAMENTO_C.items():
        if controle & (1 << bit):
            selecionados.append(nome)
    return selecionados


def estado_formatado(registradores):
    linhas = []
    for nome in REGISTRADORES:
        tamanho = 8 if nome == "MBR" else 32
        linhas.append(f"{nome} = {format(registradores[nome], f'0{tamanho}b')}")
    return linhas


def executar_tarefa2(caminho_programa, caminho_registradores):
    linhas = ler_linhas(caminho_programa)
    registradores = ler_registradores(caminho_registradores)
    log = ["TAREFA 2 - CAMINHO DE DADOS", "Estado inicial dos registradores:"]
    log.extend(estado_formatado(registradores))

    for ciclo, ir in enumerate(linhas, start=1):
        if len(ir) != 21 or any(c not in "01" for c in ir):
            raise ValueError(f"Microinstrução inválida na linha {ciclo}: {ir}")

        controle_ula = ir[:8]
        controle_c = int(ir[8:17], 2)
        controle_b = int(ir[17:21], 2)

        estado_inicial = registradores.copy()
        nome_b, b = valor_barramento_b(controle_b, estado_inicial)
        a = estado_inicial["H"]
        destinos = registradores_barramento_c(controle_c)
        a_usado, b_usado, s, sd, co, n, z = ula(a, b, controle_ula)

        #escreve o resultado nos registradores selecionados
        for nome in destinos:
            registradores[nome] = sd & MASK

        log.append("=" * 60)
        log.append(f"Microinstrução {ciclo}")
        log.append(f"IR = {ir}")
        log.append(f"Barramento B = {nome_b}")
        log.append("Barramento C = " + (", ".join(destinos) if destinos else "nenhum registrador"))
        log.append("Registradores no início:")
        log.extend(estado_formatado(estado_inicial))
        log.append(f"A da ULA = {bin32(a_usado)}")
        log.append(f"B da ULA = {bin32(b_usado)}")
        log.append(f"S = {bin32(s)}")
        log.append(f"Sd = {bin32(sd)}")
        log.append(f"Vai-um = {co} | N = {n} | Z = {z}")
        log.append("Registradores no fim:")
        log.extend(estado_formatado(registradores))

    return "\n".join(log)


def main():
    if len(sys.argv) == 1:
        programa_t1 = "programa_etapa2_tarefa1.txt"
        programa_t2 = "programa_etapa2_tarefa2.txt"
        arquivo_registradores = "registradores_etapa2_tarefa2.txt"
        arquivo_saida = "saida_etapa2.txt"
    elif len(sys.argv) == 5:
        programa_t1, programa_t2, arquivo_registradores, arquivo_saida = sys.argv[1:]
    else:
        print("Uso: python3 etapa2.py [programa_t1 programa_t2 registradores_t2 saida]")
        return

    try:
        saida_t1 = executar_tarefa1(programa_t1)
        saida_t2 = executar_tarefa2(programa_t2, arquivo_registradores)
        with open(arquivo_saida, "w", encoding="utf-8") as arquivo:
            arquivo.write(saida_t1 + "\n\n" + saida_t2 + "\n")
        print(f"Execução concluída. Saída salva em {arquivo_saida}.")
    except (OSError, ValueError) as erro:
        print(f"Erro: {erro}")
        sys.exit(1)


if __name__ == "__main__":
    main()
