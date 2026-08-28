#!/usr/bin/env python3
"""
Esqueleto del Codificador Educativo de Instrucciones RISC-V.
CE4301 Arquitectura de Computadores I — Proyecto Individual — 2026-II

Este esqueleto ya implementa el contrato de línea de comandos y de salida
requerido por la especificación. Usted debe completar las dos funciones
marcadas con TODO; puede modificar el resto del archivo si lo necesita,
siempre que se preserve el contrato de invocación y la línea "HEX: 0x...".

No es obligatorio usar este esqueleto ni Python: puede implementar su
propia herramienta desde cero, en el lenguaje que prefiera, siempre que
respete el mismo contrato (ver especificación, sección "Modo de operación").
"""
import re
import sys

# Formatos de instrucción soportados (RV32I).
FORMAT_R = "R"
FORMAT_I = "I"
FORMAT_S = "S"
FORMAT_B = "B"

# Tabla de codificación de las 12 instrucciones soportadas: opcode, funct3
# y funct7 (cuando aplica) según el formato de cada una.
#
# Fuente: Andrew Waterman and Krste Asanović, "The RISC-V Instruction Set
# Manual, Volume I: User-Level ISA", Document Version 20191213, RISC-V
# Foundation, 2019 — Capítulo 2 (RV32I Base Integer Instruction Set),
# específicamente las Figuras: 
# 2.1: RISC-V base unprivileged integer register state. (para numero de registros)
# 2.3: RISC-V base instruction formats showing immediate variants. (para la estructura de los formatos R/I/S/B)
#
INSTR_TABLE = {
    # --- Formato R: aritmética registro-registro (opcode = 0110011) ---
    "add": {"format": FORMAT_R, "opcode": 0b0110011, "funct3": 0b000, "funct7": 0b0000000},
    "sub": {"format": FORMAT_R, "opcode": 0b0110011, "funct3": 0b000, "funct7": 0b0100000},
    "and": {"format": FORMAT_R, "opcode": 0b0110011, "funct3": 0b111, "funct7": 0b0000000},
    "or":  {"format": FORMAT_R, "opcode": 0b0110011, "funct3": 0b110, "funct7": 0b0000000},

    # --- Formato I: aritmética con inmediato (opcode = 0010011) ---
    "addi": {"format": FORMAT_I, "opcode": 0b0010011, "funct3": 0b000},
    "andi": {"format": FORMAT_I, "opcode": 0b0010011, "funct3": 0b111},

    # --- Formato I: carga desde memoria (opcode = 0000011) ---
    "lw": {"format": FORMAT_I, "opcode": 0b0000011, "funct3": 0b010},
    "lb": {"format": FORMAT_I, "opcode": 0b0000011, "funct3": 0b000},

    # --- Formato S: almacenamiento en memoria (opcode = 0100011) ---
    "sw": {"format": FORMAT_S, "opcode": 0b0100011, "funct3": 0b010},
    "sb": {"format": FORMAT_S, "opcode": 0b0100011, "funct3": 0b000},

    # --- Formato B: salto condicional (opcode = 1100011) ---
    "beq": {"format": FORMAT_B, "opcode": 0b1100011, "funct3": 0b000},
    "bne": {"format": FORMAT_B, "opcode": 0b1100011, "funct3": 0b001},
}

SOPORTADAS = list(INSTR_TABLE.keys())


def parse_register(token: str) -> int:
    """
    Parsea un operando de registro en formato 'xN' (p. ej. 'x5') y retorna
    su número de registro como entero (0-31).

    Lanza ValueError si el token no tiene la forma 'xN' con N en [0, 31].
    """
    token = token.strip()
    match = re.fullmatch(r"x(\d{1,2})", token)
    if match is None or not (0 <= int(match.group(1)) <= 31):
        raise ValueError(f"Registro inválido: '{token}' (se esperaba x0-x31)")
    return int(match.group(1))


# Rango del inmediato admitido por cada formato:
#   I y S: campo de 12 bits con signo             -> [-2048, 2047]
#   B:     campo de 13 bits con signo, bit 0 = 0  -> [-4096, 4094], solo pares
IMM_RANGES = {
    FORMAT_I: (-2048, 2047),
    FORMAT_S: (-2048, 2047),
    FORMAT_B: (-4096, 4094),
}


def parse_immediate(token: str) -> int:
    """
    Parsea un inmediato entero. Acepta decimal con o sin signo ('-12', '8')
    y notación con prefijo ('0x1f', '0b1010').
    """
    token = token.strip()
    try:
        # base 0 hace que Python autodetecte el prefijo (0x, 0b, 0o) o decimal.
        return int(token, 0)
    except ValueError:
        pass
    try:
        # Reintento en decimal para casos como '-012', que base 0 rechaza.
        return int(token, 10)
    except ValueError:
        raise ValueError(
            f"Inmediato inválido: '{token}' (se esperaba un entero decimal o 0x...)"
        )


def check_immediate(imm: int, fmt: str) -> None:
    """
    Valida que el inmediato quepa en el campo del formato indicado.

    Para el formato B se exige además que el desplazamiento sea par: el bit 0
    del inmediato no se codifica, porque los saltos son múltiplos de 2 bytes.
    """
    low, high = IMM_RANGES[fmt]
    if not (low <= imm <= high):
        raise ValueError(
            f"Inmediato {imm} fuera del rango [{low}, {high}] del formato {fmt}"
        )
    if fmt == FORMAT_B and imm % 2 != 0:
        raise ValueError(
            f"El desplazamiento de salto {imm} debe ser par (múltiplo de 2 bytes)"
        )


def parse_mem_operand(token: str) -> tuple:
    """
    Parsea la sintaxis 'offset(registro)' de las instrucciones de memoria
    (p. ej. '8(x6)' o '-4(x2)') y retorna la tupla (inmediato, registro).
    """
    match = re.fullmatch(r"(-?\w+)\s*\(\s*(x\d{1,2})\s*\)", token.strip())
    if match is None:
        raise ValueError(
            f"Operando de memoria inválido: '{token}' (se esperaba 'offset(xN)')"
        )
    return parse_immediate(match.group(1)), parse_register(match.group(2))


def split_instruction(instruction: str) -> tuple:
    """
    Separa el texto de la instrucción en (mnemónico, lista de operandos).

    Las comas se tratan como espacios, de modo que 'add x5,x6,x7' y
    'add x5, x6, x7' producen el mismo resultado. No se rompe la sintaxis
    'offset(reg)' porque esta nunca contiene comas.
    """
    text = instruction.strip().lower()
    if not text:
        raise ValueError("Instrucción vacía")
    tokens = text.replace(",", " ").split()
    return tokens[0], tokens[1:]


def encode_r(info: dict, operands: list) -> int:
    """
    Ensambla una instrucción de formato R: 'mnemonico rd, rs1, rs2'.

    Disposición de campos (manual RISC-V, Figura 2.2):
        funct7[31:25] | rs2[24:20] | rs1[19:15] | funct3[14:12] | rd[11:7] | opcode[6:0]
    """
    if len(operands) != 3:
        raise ValueError("El formato R espera 3 operandos: rd, rs1, rs2")

    rd = parse_register(operands[0])
    rs1 = parse_register(operands[1])
    rs2 = parse_register(operands[2])

    return (
        (info["funct7"] << 25)
        | (rs2 << 20)
        | (rs1 << 15)
        | (info["funct3"] << 12)
        | (rd << 7)
        | info["opcode"]
    )


def encode_instruction(instruction: str) -> int:
    """
    Recibe una instrucción como texto, p. ej. "add x5, x6, x7", y retorna su
    codificación de 32 bits como entero (0 <= valor < 2**32).

    El mnemónico se busca en INSTR_TABLE y el ensamblado se delega a la
    función correspondiente al formato de esa instrucción.
    """
    mnemonic, operands = split_instruction(instruction)

    if mnemonic not in INSTR_TABLE:
        raise ValueError(
            f"Instrucción no soportada: '{mnemonic}'. "
            f"Soportadas: {', '.join(SOPORTADAS)}"
        )

    info = INSTR_TABLE[mnemonic]
    fmt = info["format"]

    if fmt == FORMAT_R:
        return encode_r(info, operands)

    raise NotImplementedError(f"Formato {fmt}: pendiente de implementar")


def explain_instruction(instruction: str, word: int) -> str:
    """
    Debe retornar un texto (para imprimirse en pantalla) que muestre, de
    forma visual, los 32 bits de 'word' divididos en los campos del
    formato correspondiente (R, I, S o B) — indicando el rango de bits y
    el valor de cada campo — junto con una breve explicación de cada uno.
    El formato visual (colores, tabla, arte ASCII, etc.) queda a su
    criterio, siempre que sea claro.
    """
    # TODO: implementar.
    raise NotImplementedError("explain_instruction: pendiente de implementar")


def main():
    if len(sys.argv) != 2:
        print(f'Uso: {sys.argv[0]} "<instruccion>"', file=sys.stderr)
        print(f'Ejemplo: {sys.argv[0]} "add x5, x6, x7"', file=sys.stderr)
        sys.exit(2)

    instruction = sys.argv[1]

    # Se calculan codificación y explicación antes de imprimir nada, para que
    # un error de sintaxis no deje una salida a medias.
    try:
        word = encode_instruction(instruction) & 0xFFFFFFFF
        explicacion = explain_instruction(instruction, word)
    except (ValueError, NotImplementedError) as error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)

    print(explicacion)
    # No modificar el formato de la siguiente línea: la especificación la
    # requiere, literal, para permitir la validación automática.
    print(f"HEX: 0x{word:08x}")


if __name__ == "__main__":
    main()
