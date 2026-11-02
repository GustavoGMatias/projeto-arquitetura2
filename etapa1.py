# Simulador da ULA da Mic-1 - Etapa 1

MASK = 0xFFFFFFFF   #hexadecimal
A_INICIAL = 0xFFFFFFFF   
B_INICIAL = 0x00000001


def bin32(x):
    #texto de 32 bits
    return format(x & MASK, "032b")


def ula(a, b, ir):

    F0, F1, ENA, ENB, INVA, INC = (int(c) for c in ir)

    if ENA == 0:
        a = 0                 
    if ENB == 0:
        b = 0                 
    if INVA == 1:
        a = ~a & MASK  #inverte todos os bits de A

    #escolhe a operacao pelo par (F0, F1)
    co = 0
    if (F0, F1) == (0, 0):
        s = a & b
    elif (F0, F1) == (0, 1):
        s = a | b
    elif (F0, F1) == (1, 0):
        s = ~b & MASK
    else:  #soma
        total = a + b + INC  #vem-um
        s = total & MASK    
        co = total >> 32    #vai-um
    return a, b, s, co


def main(arq_programa, arq_log):
    with open(arq_programa, "r") as f:
        linhas = [linha.strip() for linha in f.readlines()] #lê todas as linhas do arquivo de entrada

    with open(arq_log, "w") as log:  #abre o log de saída para escrever
        log.write(f"b = {bin32(B_INICIAL)}\n")
        log.write(f"a = {bin32(A_INICIAL)}\n\n")
        log.write("Start of Program\n")

        pc = 1    #linha atual
        while True:
            log.write("=" * 60 + "\n")
            log.write(f"Cycle {pc}\n\nPC = {pc}\n")

            ir = linhas[pc - 1] if pc - 1 < len(linhas) else "" #registrador de instrucao
            if ir == "":
                log.write("> Line is empty, EOP.\n\n")
                break

            a, b, s, co = ula(A_INICIAL, B_INICIAL, ir)
            log.write(f"IR = {ir}\n")
            log.write(f"b = {bin32(b)}\n")
            log.write(f"a = {bin32(a)}\n")
            log.write(f"s = {bin32(s)}\n")
            log.write(f"co = {co}\n")
            pc += 1


main("programa_etapa1.txt", "saida_etapa1.txt")
