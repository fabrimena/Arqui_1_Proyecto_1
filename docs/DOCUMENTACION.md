# Documentación técnica — Codificador Educativo de Instrucciones RISC-V

CE-4301 Arquitectura de Computadores I — Proyecto Individual.  
Grupo: 01  
Profesor: Jeferson Gonzalez Gomez.  
Estudiante: Fabricio Mena Mejia.  
Carnet: 2019042722.  

## 1. Arquitectura del código y decisiones de diseño

Todo el modelo vive en `encoder_skeleton.py`, organizado en cinco capas de
abajo hacia arriba:

1. **Tabla ISA** — `INSTR_TABLE`, `LOAD_INSTRS`, `IMM_RANGES`, `OPCODE_NAMES`.
   Datos, no lógica: un diccionario por mnemónico con formato, opcode, funct3 y
   funct7.
2. **Parseo** — `split_instruction`, `parse_register`, `parse_immediate`,
   `parse_mem_operand`, `check_immediate`. Convierten texto en enteros y
   validan rangos.
3. **Ensamblado** — `encode_r`, `encode_i`, `encode_s`, `encode_b`. Una función
   por formato; solo operaciones de bits.
4. **Explicación** — `bits`, `sign_extend`, `rebuild_immediate`,
   `describe_fields`, `render_bit_table`, `explain_instruction`. Descomponen la
   palabra ya ensamblada y la presentan.
5. **CLI** — `encode_instruction` (despacho por formato) y `main` (contrato de
   entrada/salida). `run.sh` solo invoca este archivo.

### Decisiones de diseño

- **Tabla hardcodeada en lugar de un parser de la especificación de la ISA.**
  Son 12 instrucciones fijas; una tabla explícita es más legible, se cotejа
  línea por línea contra el manual y no introduce complejidad innecesaria.
- **Despacho por formato, no por mnemónico.** `encode_instruction` consulta el
  campo `format` de la tabla, así que agregar una instrucción del mismo formato
  solo requiere una fila nueva.
- **Parseo separado del ensamblado.** Las mismas rutinas de parseo sirven a los
  cuatro formatos, y las dos sintaxis de operandos (`rd, rs1, rs2` frente a
  `rd, offset(rs1)`) se resuelven en un solo lugar.
- **Validación temprana de inmediatos.** `check_immediate` rechaza valores que
  no caben en el campo (y desplazamientos impares en el formato B) antes de
  ensamblar, en lugar de truncarlos silenciosamente y producir una codificación
  incorrecta.
- **Complemento a 2 explícito con máscaras (`imm & 0xFFF`).** Los enteros de
  Python son de precisión arbitraria y con signo; la máscara los convierte al
  patrón de bits del ancho del campo, que es lo que el hardware espera.
- **Datos separados de presentación en la explicación.** `describe_fields`
  devuelve tuplas `(nombre, bit_alto, bit_bajo, valor, texto)` y
  `render_bit_table` calcula los anchos de columna a partir de ellas. Una sola
  rutina de dibujo sirve para formatos de 5, 6 y 8 campos.
- **El inmediato se reconstruye desde la palabra codificada**
  (`rebuild_immediate`), no se reutiliza el que escribió el usuario. Así el
  ensamblado y el desensamblado se verifican mutuamente en cada ejecución.
- **Errores como `ValueError` con mensaje en español**, traducidos en `main` a
  una línea en `stderr` y código de salida 1, sin *traceback*.

## 2. Instrucciones soportadas y origen de sus campos de codificación

Los valores de `opcode`, `funct3` y `funct7` se obtuvieron del manual oficial
de la ISA:

[Andrew Waterman y Krste Asanović, *The RISC-V Instruction Set Manual, Volume I: Unprivileged ISA*, Document Version 20191213, RISC-V Foundation, diciembre de 2019.](/docs/riscv-spec-20191213.pdf)

Partes concretas consultadas:

| Referencia en el manual | Qué se obtuvo de ahí |
|---|---|
| Figura 2.1 — *RISC-V base unprivileged integer register state* | Existen 32 registros `x0`–`x31` y `x0` está fijo en 0. Define el rango válido en `parse_register`. |
| Figura 2.2 — *RISC-V base instruction formats* | Posición exacta de `funct7`, `rs2`, `rs1`, `funct3`, `rd` e `imm` en los formatos R, I y S. |
| Figura 2.3 — *...showing immediate variants* | Disposición del formato B y su relación con el formato S. |
| Figura 2.4 — *Types of immediate produced by RISC-V instructions* | Qué bit de la instrucción produce cada bit del inmediato en I, S y B, y que la extensión de signo siempre parte de `inst[31]`. |
| §2.3 — *Immediate Encoding Variants* | Que el inmediato B codifica desplazamientos en múltiplos de 2 bytes y que `imm[11]` ocupa la casilla que S usa para `imm[0]`. |
| §2.4 — *Integer Computational Instructions* | `funct3`/`funct7` de `add`, `sub`, `and`, `or`, `addi`, `andi`; opcodes OP y OP-IMM. |
| §2.5 — *Control Transfer Instructions* | `funct3` de `beq`/`bne`; alcance ±4 KiB y offsets pares. |
| §2.6 — *Load and Store Instructions* | `funct3` como selector de ancho (`lb`/`lw`, `sb`/`sw`); dirección efectiva = `rs1 + inmediato extendido en signo`; el store toma el dato de `rs2`. |
| Tabla 24.1 — *RISC-V base opcode map* | Nombres de los grupos de opcode (OP, OP-IMM, LOAD, STORE, BRANCH) usados en la salida explicativa. |
| Tabla 24.2 — *Instruction listing for RISC-V* | Listado autoritativo con los valores binarios exactos por instrucción; se usó para verificar la tabla completa. |

Tabla resultante (constante `INSTR_TABLE` en `encoder_skeleton.py`):

| Instrucción | Formato | opcode | funct3 | funct7 |
|---|---|---|---|---|
| `add`  | R | `0110011` | `000` | `0000000` |
| `sub`  | R | `0110011` | `000` | `0100000` |
| `and`  | R | `0110011` | `111` | `0000000` |
| `or`   | R | `0110011` | `110` | `0000000` |
| `addi` | I | `0010011` | `000` | — |
| `andi` | I | `0010011` | `111` | — |
| `lw`   | I | `0000011` | `010` | — |
| `lb`   | I | `0000011` | `000` | — |
| `sw`   | S | `0100011` | `010` | — |
| `sb`   | S | `0100011` | `000` | — |
| `beq`  | B | `1100011` | `000` | — |
| `bne`  | B | `1100011` | `001` | — |


## 3. Ejemplos de salida explicativa

Uno por formato. Salidas reales de la herramienta:

### 3.1 Formato R

```
$ ./run.sh "add x5, x6, x7"
```
```text
Instrucción : add x5, x6, x7
Mnemónico   : add
Formato     : R
Binario     : 0000000 00111 00110 000 00101 0110011
              00000000011100110000001010110011  (32 bits)
Hexadecimal : 0x007302b3

+---------+-------+-------+--------+-------+---------+
|  31:25  | 24:20 | 19:15 | 14:12  |  11:7 |   6:0   |
|  funct7 |  rs2  |  rs1  | funct3 |   rd  |  opcode |
+---------+-------+-------+--------+-------+---------+
| 0000000 | 00111 | 00110 |  000   | 00101 | 0110011 |
+---------+-------+-------+--------+-------+---------+

Campos:
  funct7    bits 31:25 = 0b0000000 = 0    → Junto con funct3 distingue la operación concreta (add y sub comparten funct3 y se separan aquí).
  rs2       bits 24:20 = 0b00111   = 7    → Segundo operando fuente: registro x7.
  rs1       bits 19:15 = 0b00110   = 6    → Primer operando fuente: registro x6.
  funct3    bits 14:12 = 0b000     = 0    → Sub-código que, dentro de ese opcode, selecciona 'add'.
  rd        bits 11:7  = 0b00101   = 5    → Registro destino: x5 recibe el resultado.
  opcode    bits 6:0   = 0b0110011 = 51   → Grupo de la instrucción: OP (aritmética/lógica registro-registro).
HEX: 0x007302b3
```

### 3.2 Formato I

```
$ ./run.sh "addi x10, x1, -12"
```
```text
Instrucción : addi x10, x1, -12
Mnemónico   : addi
Formato     : I
Binario     : 111111110100 00001 000 01010 0010011
              11111111010000001000010100010011  (32 bits)
Hexadecimal : 0xff408513

+--------------+-------+--------+-------+---------+
|    31:20     | 19:15 | 14:12  |  11:7 |   6:0   |
|  imm[11:0]   |  rs1  | funct3 |   rd  |  opcode |
+--------------+-------+--------+-------+---------+
| 111111110100 | 00001 |  000   | 01010 | 0010011 |
+--------------+-------+--------+-------+---------+

Campos:
  imm[11:0] bits 31:20 = 0b111111110100 = 4084 → Operando constante de 12 bits con signo = -12; se extiende en signo a 32 bits antes de operar.
  rs1       bits 19:15 = 0b00001   = 1    → Operando fuente: registro x1.
  funct3    bits 14:12 = 0b000     = 0    → Sub-código que, dentro de ese opcode, selecciona 'addi'.
  rd        bits 11:7  = 0b01010   = 10   → Registro destino: x10 recibe el resultado.
  opcode    bits 6:0   = 0b0010011 = 19   → Grupo de la instrucción: OP-IMM (aritmética/lógica con inmediato).

Inmediato reconstruido desde sus trozos: -12 (decimal con signo)
HEX: 0xff408513
```

### 3.3 Formato S

```
$ ./run.sh "sw x8, -4(x2)"
```
```text
Instrucción : sw x8, -4(x2)
Mnemónico   : sw
Formato     : S
Binario     : 1111111 01000 00010 010 11100 0100011
              11111110100000010010111000100011  (32 bits)
Hexadecimal : 0xfe812e23

+-----------+-------+-------+--------+----------+---------+
|   31:25   | 24:20 | 19:15 | 14:12  |   11:7   |   6:0   |
| imm[11:5] |  rs2  |  rs1  | funct3 | imm[4:0] |  opcode |
+-----------+-------+-------+--------+----------+---------+
|  1111111  | 01000 | 00010 |  010   |  11100   | 0100011 |
+-----------+-------+-------+--------+----------+---------+

Campos:
  imm[11:5] bits 31:25 = 0b1111111 = 127  → Bits altos del desplazamiento; junto con imm[4:0] forman -4.
  rs2       bits 24:20 = 0b01000   = 8    → Registro con el dato a escribir: x8.
  rs1       bits 19:15 = 0b00010   = 2    → Registro base de la dirección: x2.
  funct3    bits 14:12 = 0b010     = 2    → Sub-código que, dentro de ese opcode, selecciona 'sw'.
  imm[4:0]  bits 11:7  = 0b11100   = 28   → Bits bajos del desplazamiento; el inmediato completo es -4.
  opcode    bits 6:0   = 0b0100011 = 35   → Grupo de la instrucción: STORE (escritura en memoria).

Inmediato reconstruido desde sus trozos: -4 (decimal con signo)
HEX: 0xfe812e23
```

### 3.4 Formato B

```
$ ./run.sh "beq x1, x2, 8"
```
```text
Instrucción : beq x1, x2, 8
Mnemónico   : beq
Formato     : B
Binario     : 0 000000 00010 00001 000 0100 0 1100011
              00000000001000001000010001100011  (32 bits)
Hexadecimal : 0x00208463

+---------+-----------+-------+-------+--------+----------+---------+---------+
|    31   |   30:25   | 24:20 | 19:15 | 14:12  |   11:8   |    7    |   6:0   |
| imm[12] | imm[10:5] |  rs2  |  rs1  | funct3 | imm[4:1] | imm[11] |  opcode |
+---------+-----------+-------+-------+--------+----------+---------+---------+
|    0    |   000000  | 00010 | 00001 |  000   |   0100   |    0    | 1100011 |
+---------+-----------+-------+-------+--------+----------+---------+---------+

Campos:
  imm[12]   bits 31    = 0b0       = 0    → Bit de signo del desplazamiento (8); en RISC-V siempre ocupa el bit 31 para acelerar la extensión de signo.
  imm[10:5] bits 30:25 = 0b000000  = 0    → Bits 10:5 del desplazamiento del salto.
  rs2       bits 24:20 = 0b00010   = 2    → Segundo registro a comparar: x2.
  rs1       bits 19:15 = 0b00001   = 1    → Primer registro a comparar: x1.
  funct3    bits 14:12 = 0b000     = 0    → Sub-código que, dentro de ese opcode, selecciona 'beq'.
  imm[4:1]  bits 11:8  = 0b0100    = 4    → Bits 4:1 del desplazamiento (el bit 0 es implícito y vale 0).
  imm[11]   bits 7     = 0b0       = 0    → Bit 11 del desplazamiento, reubicado en la casilla que el formato S usa para imm[0].
  opcode    bits 6:0   = 0b1100011 = 99   → Grupo de la instrucción: BRANCH (salto condicional).

Inmediato reconstruido desde sus trozos: 8 (decimal con signo)
HEX: 0x00208463
```

## 4. Validación contra el toolchain oficial de 32 bits

# Evidencia de validación contra el toolchain oficial de RISC-V (32 bits)

- Ensamblador: `GNU assembler (2.42-1ubuntu1+6) 2.42`
- Ensamblado : `riscv64-unknown-elf-as -march=rv32i -mabi=ilp32 -mno-relax`
- Referencia : `riscv64-unknown-elf-objdump -d`

> **Nota sobre los saltos condicionales.** GNU `as` interpreta un número
> suelto como destino de salto como *dirección absoluta*, y cuando no puede
> garantizar el alcance genera un trampolín de dos instrucciones
> (`bne` con la condición invertida + `j`). Por eso hay que usar
> la sintaxis `.+N` / `.-N` antes de
> ensamblar, para que se genere una única instrucción de formato B con el
> desplazamiento pedido.  

Comando de ejemplo para llamar un salto en GNU assembler:
```bash  
printf 'beq x1, x2, .+8\n' > /tmp/t.s  
riscv64-unknown-elf-as -march=rv32i -mabi=ilp32 -o /tmp/t.o /tmp/t.s  
riscv64-unknown-elf-objdump -d /tmp/t.o  
```

| # | Instrucción | Escenario | Modelo propio | `objdump -d` | Coincide |
|---|---|---|---|---|---|
| 1 | `add x5, x6, x7` | típico: registros de rango medio | `0x007302b3` | `0x007302b3` | sí |
| 2 | `add x28, x15, x0` | x0 como fuente (sumar cero = copiar) | `0x00078e33` | `0x00078e33` | sí |
| 3 | `add x31, x0, x31` | límite: registros extremos x0 y x31 | `0x01f00fb3` | `0x01f00fb3` | sí |
| 4 | `sub x10, x20, x30` | típico: registros de rango medio | `0x41ea0533` | `0x41ea0533` | sí |
| 5 | `sub x7, x0, x9` | x0 como minuendo (negación de x9) | `0x409003b3` | `0x409003b3` | sí |
| 6 | `sub x31, x31, x0` | límite: registro más alto, restando cero | `0x400f8fb3` | `0x400f8fb3` | sí |
| 7 | `and x12, x13, x14` | típico: registros de rango medio | `0x00e6f633` | `0x00e6f633` | sí |
| 8 | `and x5, x18, x0` | x0 como fuente (resultado siempre 0) | `0x000972b3` | `0x000972b3` | sí |
| 9 | `and x31, x0, x31` | límite: registros extremos x0 y x31 | `0x01f07fb3` | `0x01f07fb3` | sí |
| 10 | `or x9, x10, x11` | típico: registros de rango medio | `0x00b564b3` | `0x00b564b3` | sí |
| 11 | `or x21, x0, x22` | x0 como fuente (equivale a copiar x22) | `0x01606ab3` | `0x01606ab3` | sí |
| 12 | `or x31, x31, x0` | límite: registro más alto, con x0 | `0x000fefb3` | `0x000fefb3` | sí |
| 13 | `addi x10, x1, 100` | inmediato positivo | `0x06408513` | `0x06408513` | sí |
| 14 | `addi x10, x1, -12` | inmediato negativo | `0xff408513` | `0xff408513` | sí |
| 15 | `addi x5, x0, 2047` | límite: máximo inmediato representable (+2047), base x0 | `0x7ff00293` | `0x7ff00293` | sí |
| 16 | `andi x6, x7, 255` | inmediato positivo | `0x0ff3f313` | `0x0ff3f313` | sí |
| 17 | `andi x8, x9, -1` | inmediato negativo (todos los bits en 1) | `0xfff4f413` | `0xfff4f413` | sí |
| 18 | `andi x11, x12, -2048` | límite: mínimo inmediato representable (-2048) | `0x80067593` | `0x80067593` | sí |
| 19 | `lw x5, 8(x6)` | desplazamiento positivo | `0x00832283` | `0x00832283` | sí |
| 20 | `lw x7, -256(x8)` | desplazamiento negativo | `0xf0042383` | `0xf0042383` | sí |
| 21 | `lw x9, 2047(x0)` | límite: máximo desplazamiento (+2047), base x0 | `0x7ff02483` | `0x7ff02483` | sí |
| 22 | `lb x10, 4(x11)` | desplazamiento positivo | `0x00458503` | `0x00458503` | sí |
| 23 | `lb x12, -1(x13)` | desplazamiento negativo | `0xfff68603` | `0xfff68603` | sí |
| 24 | `lb x14, -2048(x15)` | límite: mínimo desplazamiento (-2048) | `0x80078703` | `0x80078703` | sí |
| 25 | `sw x8, 12(x2)` | desplazamiento positivo | `0x00812623` | `0x00812623` | sí |
| 26 | `sw x8, -4(x2)` | desplazamiento negativo | `0xfe812e23` | `0xfe812e23` | sí |
| 27 | `sw x0, 2047(x31)` | límite: máximo desplazamiento (+2047), guardando x0 | `0x7e0fafa3` | `0x7e0fafa3` | sí |
| 28 | `sb x5, 1(x6)` | desplazamiento positivo | `0x005300a3` | `0x005300a3` | sí |
| 29 | `sb x7, -128(x8)` | desplazamiento negativo | `0xf8740023` | `0xf8740023` | sí |
| 30 | `sb x9, -2048(x10)` | límite: mínimo desplazamiento (-2048) | `0x80950023` | `0x80950023` | sí |
| 31 | `beq x1, x2, 8` | salto hacia adelante | `0x00208463` | `0x00208463` | sí |
| 32 | `beq x3, x4, -16` | salto hacia atrás | `0xfe4188e3` | `0xfe4188e3` | sí |
| 33 | `beq x5, x6, 0` | límite: desplazamiento cero (salto a sí misma) | `0x00628063` | `0x00628063` | sí |
| 34 | `bne x7, x8, 20` | salto hacia adelante | `0x00839a63` | `0x00839a63` | sí |
| 35 | `bne x9, x10, -4096` | límite: mínimo desplazamiento representable (-4096) | `0x80a49063` | `0x80a49063` | sí |
| 36 | `bne x11, x12, 4094` | límite: máximo desplazamiento representable (+4094) | `0x7ec59fe3` | `0x7ec59fe3` | sí |

**Resumen:** 36 casos evaluados — 36 coincidencias(en hexadecimal), 0 discrepancias.

### Captura comparativa de herramienta vs toolchain

![Captura de consola](/docs/evidencia/image.png)

## 6. Instalación y preparación de la herramienta

Ver [README.md](/README.md). En resumen: Python 3.8+ de la biblioteca estándar,
sin dependencias externas, y `chmod +x run.sh` si hiciera falta.
