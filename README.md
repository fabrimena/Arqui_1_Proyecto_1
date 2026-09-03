# Codificador Educativo de Instrucciones RISC-V (RV32I)

Herramienta de línea de comandos que traduce **una** instrucción del subconjunto
RV32I definido en la especificación del proyecto a su codificación binaria de
32 bits, mostrando el desglose de cada campo del formato correspondiente
(R, I, S o B).

Curso: CE-4301 Arquitectura de Computadores I — Proyecto Individual.  
Grupo: 01  
Profesor: Jeferson Gonzalez Gomez.  
Estudiante: Fabricio Mena Mejia.  
Carnet: 2019042722.  

# Preparación previa de la herramienta

La herramienta está escrita en Python 3 y usa **únicamente la biblioteca
estándar**: no hay dependencias que instalar, por lo que el repositorio no
incluye `requirements.txt`.

1. Verificar que Python 3 esté disponible (se requiere 3.8 o superior):

   ```bash
   python3 --version
   ```

   Si no está instalado (Debian / Ubuntu / WSL):

   ```bash
   sudo apt-get update && sudo apt-get install -y python3
   ```

2. Asegurar el permiso de ejecución del punto de entrada. Solo es necesario si
   el repositorio se obtuvo sin permisos (por ejemplo, al descomprimir un
   `.zip`):

   ```bash
   chmod +x run.sh
   ```

Con eso la herramienta queda lista para usarse.

## Uso

```bash
./run.sh "<instruccion>"
```

Ejemplos:

```bash
./run.sh "add x5, x6, x7"
./run.sh "addi x10, x1, -12"
./run.sh "lw x5, 8(x6)"
./run.sh "sw x8, -4(x2)"
./run.sh "beq x1, x2, 8"
```

La salida incluye el formato identificado, la codificación en binario y en
hexadecimal, una tabla con el desglose de los 32 bits campo por campo, la
explicación del rol de cada campo, y —en su propia línea— la codificación en
el formato `HEX: 0xXXXXXXXX`.

# Instalación del toolchain

Solo se requiere ensamblador y `objdump` capaces de manejar RV32; no hace falta
compilador ni biblioteca C.

```bash
sudo apt-get update
sudo apt-get install -y binutils-riscv64-unknown-elf
riscv64-unknown-elf-as --version
riscv64-unknown-elf-objdump --version
```

## Uso

El ensamblador se invoca fijando la ISA de 32 bits explícitamente:

```bash
printf 'add x5, x6, x7\n' > /tmp/t.s <-- Reemplazar por instruccion a codificar
riscv64-unknown-elf-as -march=rv32i -mabi=ilp32 -o /tmp/t.o /tmp/t.s
riscv64-unknown-elf-objdump -d /tmp/t.o
```

## Documentación técnica

Ver [DOCUMENTACION.md](docs/DOCUMENTACION.md).