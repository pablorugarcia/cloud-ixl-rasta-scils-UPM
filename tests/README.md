# Pruebas heredadas

Este directorio conserva pruebas procedentes de las bibliotecas **RaSTA** y **SCI** incluidas en el repositorio.

```text
tests/
├── README.md
├── rasta/
└── sci/
```

## Contenido

- `tests/rasta/`: pruebas CUnit de la biblioteca RaSTA heredada.
- `tests/sci/`: pruebas CUnit de las funciones SCI/SCI-LS heredadas.

## Estado actual

Las pruebas CUnit heredadas no están integradas en el `CMakeLists.txt` principal
y no disponen de un ejecutor autónomo. Se puede comprobar que CTest no tiene
casos registrados:

```bash
cmake -S . -B build
cmake --build build --target cloud_ixl
ctest --test-dir build -N
```

La última orden muestra:

```text
Total Tests: 0
```

Si la versión de CTest no admite `--test-dir`, ejecutar `ctest -N` desde `build/`.

Algunos casos no compilan con las interfaces actuales. Por ejemplo,
`rastadeferqueueTest.c` y `rastamoduleTest.c` usan llamadas incompatibles con las
bibliotecas incluidas, y `scilsTests.c` incluye `scils_telegram_factory.h`, una
cabecera ausente del repositorio.

Para recuperar estas pruebas hace falta adaptarlas a las interfaces actuales,
disponer de CUnit y añadir un ejecutor. Un resultado de cero casos en CTest no
equivale a haber superado las pruebas.
