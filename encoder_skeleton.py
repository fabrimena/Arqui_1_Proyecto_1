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


def encode_instruction(instruction: str) -> int:
    """
    Recibe una instrucción como texto, p. ej. "add x5, x6, x7", y debe
    retornar su codificación de 32 bits como entero (0 <= valor < 2**32).

    Debe soportar únicamente las instrucciones en SOPORTADAS. Los valores
    de opcode/funct3/funct7 de cada una NO se proveen aquí: deben
    investigarse en el manual oficial de la ISA RISC-V (ver referencia en
    la especificación) y documentarse en el README.
    """
    # TODO: implementar. Sugerencia: parsear el mnemónico y los operandos,
    # despachar según el formato (R/I/S/B), y ensamblar los campos con
    # operaciones de bits.
    raise NotImplementedError("encode_instruction: pendiente de implementar")


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
    word = encode_instruction(instruction) & 0xFFFFFFFF

    print(explain_instruction(instruction, word))

    # No modificar el formato de la siguiente línea: la especificación la
    # requiere, literal, para permitir la validación automática.
    print(f"HEX: 0x{word:08x}")


if __name__ == "__main__":
    main()
