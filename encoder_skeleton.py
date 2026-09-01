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

# Instrucciones de formato I cuya sintaxis de operandos es 'rd, offset(rs1)'
# en lugar de 'rd, rs1, imm'.
LOAD_INSTRS = {"lw", "lb"}



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


def encode_i(info: dict, operands: list, is_load: bool) -> int:
    """
    Ensambla una instrucción de formato I. Dos sintaxis posibles:
        aritmética : 'addi rd, rs1, imm'
        carga      : 'lw rd, offset(rs1)'

    Disposición de campos (manual RISC-V, Figura 2.2):
        imm[11:0] -> [31:20] | rs1[19:15] | funct3[14:12] | rd[11:7] | opcode[6:0]
    """
    if is_load:
        if len(operands) != 2:
            raise ValueError("Una carga espera 2 operandos: rd, offset(rs1)")
        rd = parse_register(operands[0])
        imm, rs1 = parse_mem_operand(operands[1])
    else:
        if len(operands) != 3:
            raise ValueError("El formato I espera 3 operandos: rd, rs1, imm")
        rd = parse_register(operands[0])
        rs1 = parse_register(operands[1])
        imm = parse_immediate(operands[2])

    check_immediate(imm, FORMAT_I)

    return (
        ((imm & 0xFFF) << 20)      # complemento a 2 truncado a los 12 bits del campo
        | (rs1 << 15)
        | (info["funct3"] << 12)
        | (rd << 7)
        | info["opcode"]
    )


def encode_s(info: dict, operands: list) -> int:
    """
    Ensambla una instrucción de formato S: 'sw rs2, offset(rs1)'.

    El inmediato de 12 bits viaja partido en dos trozos (Figura 2.2):
        imm[11:5] -> [31:25] | rs2[24:20] | rs1[19:15] | funct3[14:12]
        imm[4:0]  -> [11:7]  | opcode[6:0]
    """
    if len(operands) != 2:
        raise ValueError("El formato S espera 2 operandos: rs2, offset(rs1)")

    rs2 = parse_register(operands[0])
    imm, rs1 = parse_mem_operand(operands[1])
    check_immediate(imm, FORMAT_S)

    imm12 = imm & 0xFFF          # inmediato en complemento a 2 de 12 bits

    return (
        ((imm12 >> 5) << 25)     # imm[11:5] -> bits 31:25
        | (rs2 << 20)
        | (rs1 << 15)
        | (info["funct3"] << 12)
        | ((imm12 & 0x1F) << 7)  # imm[4:0] -> bits 11:7
        | info["opcode"]
    )


def encode_b(info: dict, operands: list) -> int:
    """
    Ensambla una instrucción de formato B: 'beq rs1, rs2, offset'.

    El desplazamiento se codifica en múltiplos de 2 bytes: el bit 0 es
    implícito (vale 0) y los 12 bits restantes quedan dispersos por la
    palabra (Figuras 2.3 y 2.4 del manual):
        imm[12] -> 31 | imm[10:5] -> 30:25 | rs2 -> 24:20 | rs1 -> 19:15
        funct3  -> 14:12 | imm[4:1] -> 11:8 | imm[11] -> 7 | opcode -> 6:0
    """
    if len(operands) != 3:
        raise ValueError("El formato B espera 3 operandos: rs1, rs2, offset")

    rs1 = parse_register(operands[0])
    rs2 = parse_register(operands[1])
    imm = parse_immediate(operands[2])
    check_immediate(imm, FORMAT_B)

    imm13 = imm & 0x1FFF         # desplazamiento en complemento a 2 de 13 bits

    return (
        (((imm13 >> 12) & 0x1) << 31)    # imm[12]: bit de signo, siempre en inst[31]
        | (((imm13 >> 5) & 0x3F) << 25)  # imm[10:5]
        | (rs2 << 20)
        | (rs1 << 15)
        | (info["funct3"] << 12)
        | (((imm13 >> 1) & 0xF) << 8)    # imm[4:1]
        | (((imm13 >> 11) & 0x1) << 7)   # imm[11], en la posición que S usa para imm[0]
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
    if fmt == FORMAT_I:
        return encode_i(info, operands, is_load=mnemonic in LOAD_INSTRS)
    if fmt == FORMAT_S:
        return encode_s(info, operands)
    if fmt == FORMAT_B:
        return encode_b(info, operands)
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
    # Nombre del grupo de opcodes al que pertenece cada instrucción, según el mapa
# de opcodes base del manual RISC-V (Tabla 24.1, "RISC-V base opcode map").
OPCODE_NAMES = {
    0b0110011: "OP (aritmética/lógica registro-registro)",
    0b0010011: "OP-IMM (aritmética/lógica con inmediato)",
    0b0000011: "LOAD (lectura de memoria)",
    0b0100011: "STORE (escritura en memoria)",
    0b1100011: "BRANCH (salto condicional)",
}


def bits(word: int, high: int, low: int) -> int:
    """Extrae el campo de bits [high:low] de 'word' (ambos extremos incluidos)."""
    return (word >> low) & ((1 << (high - low + 1)) - 1)


def sign_extend(value: int, width: int) -> int:
    """
    Interpreta 'value' (de 'width' bits) como entero con signo en complemento
    a 2: si el bit más significativo está en 1, se le resta 2**width.
    """
    if value & (1 << (width - 1)):
        return value - (1 << width)
    return value


def rebuild_immediate(mnemonic: str, word: int):
    """
    Reconstruye el inmediato con signo a partir de sus trozos dispersos en la
    palabra de 32 bits, tal como lo hace el hardware al decodificar (manual
    RISC-V, Figura 2.4). Retorna None para el formato R, que no lleva
    inmediato.
    """
    fmt = INSTR_TABLE[mnemonic]["format"]
    if fmt == FORMAT_I:
        return sign_extend(bits(word, 31, 20), 12)
    if fmt == FORMAT_S:
        return sign_extend((bits(word, 31, 25) << 5) | bits(word, 11, 7), 12)
    if fmt == FORMAT_B:
        return sign_extend(
            (bits(word, 31, 31) << 12)     # imm[12]
            | (bits(word, 7, 7) << 11)     # imm[11]
            | (bits(word, 30, 25) << 5)    # imm[10:5]
            | (bits(word, 11, 8) << 1),    # imm[4:1]  (imm[0] es siempre 0)
            13,
        )
    return None


def describe_fields(mnemonic: str, word: int) -> list:
    """
    Descompone 'word' en los campos de su formato y retorna una lista de
    tuplas (nombre, bit_alto, bit_bajo, valor_crudo, explicación). Los rangos
    de bits son los de las Figuras 2.2 y 2.3 del manual de la ISA.
    """
    info = INSTR_TABLE[mnemonic]
    fmt = info["format"]
    imm = rebuild_immediate(mnemonic, word)

    rd, rs1, rs2 = bits(word, 11, 7), bits(word, 19, 15), bits(word, 24, 20)
    opcode = bits(word, 6, 0)

    campo_opcode = (
        "opcode", 6, 0, opcode,
        f"Grupo de la instrucción: {OPCODE_NAMES[opcode]}.",
    )
    campo_funct3 = (
        "funct3", 14, 12, bits(word, 14, 12),
        f"Sub-código que, dentro de ese opcode, selecciona '{mnemonic}'.",
    )

    if fmt == FORMAT_R:
        return [
            ("funct7", 31, 25, bits(word, 31, 25),
             "Junto con funct3 distingue la operación concreta "
             "(add y sub comparten funct3 y se separan aquí)."),
            ("rs2", 24, 20, rs2, f"Segundo operando fuente: registro x{rs2}."),
            ("rs1", 19, 15, rs1, f"Primer operando fuente: registro x{rs1}."),
            campo_funct3,
            ("rd", 11, 7, rd, f"Registro destino: x{rd} recibe el resultado."),
            campo_opcode,
        ]

    if fmt == FORMAT_I and mnemonic in LOAD_INSTRS:
        return [
            ("imm[11:0]", 31, 20, bits(word, 31, 20),
             f"Desplazamiento de 12 bits con signo = {imm}; se extiende en signo "
             f"y se suma a x{rs1} para formar la dirección efectiva."),
            ("rs1", 19, 15, rs1, f"Registro base de la dirección: x{rs1}."),
            campo_funct3,
            ("rd", 11, 7, rd,
             f"Registro destino: x{rd} recibe el dato leído de memoria."),
            campo_opcode,
        ]

    if fmt == FORMAT_I:
        return [
            ("imm[11:0]", 31, 20, bits(word, 31, 20),
             f"Operando constante de 12 bits con signo = {imm}; se extiende en "
             f"signo a 32 bits antes de operar."),
            ("rs1", 19, 15, rs1, f"Operando fuente: registro x{rs1}."),
            campo_funct3,
            ("rd", 11, 7, rd, f"Registro destino: x{rd} recibe el resultado."),
            campo_opcode,
        ]

    if fmt == FORMAT_S:
        return [
            ("imm[11:5]", 31, 25, bits(word, 31, 25),
             f"Bits altos del desplazamiento; junto con imm[4:0] forman {imm}."),
            ("rs2", 24, 20, rs2, f"Registro con el dato a escribir: x{rs2}."),
            ("rs1", 19, 15, rs1, f"Registro base de la dirección: x{rs1}."),
            campo_funct3,
            ("imm[4:0]", 11, 7, bits(word, 11, 7),
             f"Bits bajos del desplazamiento; el inmediato completo es {imm}."),
            campo_opcode,
        ]

    # FORMAT_B
    return [
        ("imm[12]", 31, 31, bits(word, 31, 31),
         f"Bit de signo del desplazamiento ({imm}); en RISC-V siempre ocupa "
         f"el bit 31 para acelerar la extensión de signo."),
        ("imm[10:5]", 30, 25, bits(word, 30, 25),
         "Bits 10:5 del desplazamiento del salto."),
        ("rs2", 24, 20, rs2, f"Segundo registro a comparar: x{rs2}."),
        ("rs1", 19, 15, rs1, f"Primer registro a comparar: x{rs1}."),
        campo_funct3,
        ("imm[4:1]", 11, 8, bits(word, 11, 8),
         "Bits 4:1 del desplazamiento (el bit 0 es implícito y vale 0)."),
        ("imm[11]", 7, 7, bits(word, 7, 7),
         "Bit 11 del desplazamiento, reubicado en la casilla que el formato S "
         "usa para imm[0]."),
        campo_opcode,
    ]


def render_bit_table(fields: list) -> str:
    """
    Dibuja una tabla ASCII con una columna por campo. El ancho de cada columna
    se calcula a partir del texto más largo (rango, nombre o valor binario),
    de modo que la tabla queda alineada para cualquiera de los cuatro formatos.
    """
    ranges, names, values = [], [], []
    for name, high, low, raw, _ in fields:
        ranges.append(str(high) if high == low else f"{high}:{low}")
        names.append(name)
        values.append(format(raw, f"0{high - low + 1}b"))

    widths = [max(len(r), len(n), len(v)) + 2
              for r, n, v in zip(ranges, names, values)]
    border = "+" + "+".join("-" * w for w in widths) + "+"

    def row(cells):
        return "|" + "|".join(c.center(w) for c, w in zip(cells, widths)) + "|"

    return "\n".join([border, row(ranges), row(names), border,
                      row(values), border])


def explain_instruction(instruction: str, word: int) -> str:
    """
    Retorna el texto explicativo: formato identificado, codificación binaria y
    hexadecimal, desglose visual de los 32 bits por campo, y el rol de cada
    campo en esta instrucción concreta.
    """
    mnemonic, _ = split_instruction(instruction)
    info = INSTR_TABLE[mnemonic]
    fields = describe_fields(mnemonic, word)

    binario_por_campos = " ".join(
        format(raw, f"0{high - low + 1}b") for _, high, low, raw, _ in fields
    )

    lines = [
        f"Instrucción : {instruction.strip()}",
        f"Mnemónico   : {mnemonic}",
        f"Formato     : {info['format']}",
        f"Binario     : {binario_por_campos}",
        f"              {format(word, '032b')}  (32 bits)",
        f"Hexadecimal : 0x{word:08x}",
        "",
        render_bit_table(fields),
        "",
        "Campos:",
    ]

    for name, high, low, raw, texto in fields:
        rango = str(high) if high == low else f"{high}:{low}"
        ancho = high - low + 1
        lines.append(
            f"  {name:<9} bits {rango:<5} = 0b{format(raw, f'0{ancho}b'):<7}"
            f" = {raw:<4} → {texto}"
        )

    imm = rebuild_immediate(mnemonic, word)
    if imm is not None:
        lines.append("")
        lines.append(
            f"Inmediato reconstruido desde sus trozos: {imm} (decimal con signo)"
        )

    return "\n".join(lines)


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
