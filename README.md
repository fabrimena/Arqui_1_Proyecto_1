# Kit del proyecto

- `encoder_skeleton.py`: esqueleto en Python con el contrato de entrada/salida
  ya implementado. Complete `encode_instruction` y `explain_instruction`.
  Su uso es opcional; puede implementar la herramienta en otro lenguaje o
  desde cero, siempre que respete el mismo contrato (ver especificación).
- `run.sh`: punto de entrada fijo y obligatorio (`./run.sh "<instruccion>"`).
  Tal como se entrega, invoca `encoder_skeleton.py`. Si cambia de lenguaje o
  de estructura, ajuste este archivo para que siga invocando su solución de
  la misma forma.
- `vectores_ejemplo.txt`: instrucciones de ejemplo junto con su codificación
  correcta, para que pueda comprobar su herramienta desde el primer día.

## Cómo usar `vectores_ejemplo.txt`

El archivo tiene el formato `instruccion ; 0xHEX`, una por línea (las líneas
que empiezan con `#` son comentarios). Por ejemplo:

```
add x7, x20, x6 ; 0x006a03b3
```

Esto significa: al ejecutar `./run.sh "add x7, x20, x6"`, la línea `HEX:`
de su salida debe ser exactamente `HEX: 0x006a03b3`.

Puede comparar manualmente, o escribir un script propio corto que lea el
archivo línea por línea, ejecute `./run.sh` con cada instrucción, y compare
el resultado. Estos vectores son un conjunto de ejemplo para su propia
comprobación; **no sustituyen** los al menos 3 casos de prueba por
instrucción (36 en total) que la especificación pide construir y validar
usted mismo contra el toolchain oficial (`objdump -d`).
