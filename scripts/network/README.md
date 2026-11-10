# Pruebas de degradación de red

Este directorio contiene la herramienta utilizada para introducir degradaciones controladas sobre la comunicación entre el **Cloud IXL** y el **Object Controller** durante la campaña experimental del TFM.

```text
scripts/network/
├── README.md
└── netem.sh
```

## Topología

El script está diseñado para la topología local utilizada durante los ensayos:

```text
                CANAL 1
Cloud IXL ─────────────────────> Object Controller
127.0.0.1:9998                   127.0.0.1:8888

                CANAL 2
Cloud IXL ─────────────────────> Object Controller
127.0.0.1:9999                   127.0.0.1:8889
```

Ambos procesos se ejecutan en el mismo ordenador y utilizan la interfaz `lo`.

## Sentido de la degradación

Los filtros de `netem.sh` afectan al tráfico UDP enviado al OC en los puertos
8888 y 8889. El tráfico de retorno hacia Cloud IXL no queda sometido directamente
a estas reglas: la degradación ensayada es unidireccional.

## Latencia

```bash
sudo ./scripts/network/netem.sh delay 100
sudo ./scripts/network/netem.sh delay 500
sudo ./scripts/network/netem.sh delay 1000
sudo ./scripts/network/netem.sh delay 3000
```

Los valores se expresan en milisegundos.

## Pérdida de paquetes

```bash
sudo ./scripts/network/netem.sh loss 1
sudo ./scripts/network/netem.sh loss 5
sudo ./scripts/network/netem.sh loss 10
sudo ./scripts/network/netem.sh loss 30
sudo ./scripts/network/netem.sh loss 100
```

Los valores se expresan en porcentaje.

## Duplicación

```bash
sudo ./scripts/network/netem.sh duplicate 1
sudo ./scripts/network/netem.sh duplicate 5
sudo ./scripts/network/netem.sh duplicate 10
```

## Reordenamiento

```bash
sudo ./scripts/network/netem.sh reorder 5
sudo ./scripts/network/netem.sh reorder 10
sudo ./scripts/network/netem.sh reorder 25
```

El escenario de reordenamiento introduce además un retardo fijo que permite a `netem` retener paquetes para que datagramas posteriores puedan adelantarlos.

## Interrupción temporal

```bash
sudo ./scripts/network/netem.sh outage 5
sudo ./scripts/network/netem.sh outage 10
```

`outage` aplica una pérdida del 100 % durante el tiempo indicado, en segundos,
y elimina después la degradación.

## Pérdida de un único canal

Canal 1, tráfico dirigido al puerto UDP 8888:

```bash
sudo ./scripts/network/netem.sh channel1-loss
```

Canal 2, tráfico dirigido al puerto UDP 8889:

```bash
sudo ./scripts/network/netem.sh channel2-loss
```

> [!WARNING]
> Estos canales son lógicamente independientes, pero en el banco local comparten host e interfaz `lo`.
> La prueba no demuestra diversidad física entre caminos de comunicación.

## Estado

Para comprobar las reglas instaladas:

```bash
./scripts/network/netem.sh status
```

La salida muestra los qdisc, los filtros, los contadores y los descartes
registrados.

## Limpieza

Después de cada ensayo:

```bash
sudo ./scripts/network/netem.sh clear
```

Debe eliminarse siempre la configuración de degradación al finalizar.

## Funcionamiento interno

El script utiliza `tc` para instalar un qdisc `prio` con un hijo `netem`. Los
filtros `u32` seleccionan el tráfico dirigido a los puertos del Object Controller.

El resto del tráfico de `lo` no se degrada deliberadamente.

## Limitaciones

La herramienta:

* no descubre automáticamente interfaces;
* no descubre rutas;
* no adapta sus filtros a otras topologías;
* no protege configuraciones `tc` preexistentes;
* está diseñada específicamente para el banco local utilizado durante el TFM.

Por ello debe ejecutarse preferentemente dentro del entorno de red aislado de la campaña experimental o en un sistema local controlado.

## Campaña automatizada

La campaña experimental completa se encuentra en:

```text
results/network_degradation/
├── run_campaign.py
├── datos.csv
└── RESULTS.md
```

Desde la raíz del repositorio, tras compilar Cloud IXL y disponer de un OC
externo compatible, puede ejecutarse mediante (sustituir la ruta de ejemplo):

```bash
export CLOUD_IXL_OC_BIN="/ruta/al/ejecutable/ls_oc_local"
./results/network_degradation/run_campaign.py
```

El OC no se incluye en el repositorio. El script valida su ruta y permiso de
ejecución y utiliza el directorio del ejecutable como `cwd`. La campaña crea
un espacio de nombres de usuario y red aislado; el sistema debe permitirlo y
disponer de `ip`, `tc`, `unshare` y `stdbuf`. No utiliza el perfil de laboratorio.

Los resultados se guardan en un archivo nuevo
`results/network_degradation/runs/datos_<fecha_hora>.csv`.

El directorio `runs/` está excluido de Git. Puede elegirse otra salida con
`--output RUTA_CSV`; el archivo no debe existir. Se impide sobrescribir el CSV
histórico, también mediante un enlace simbólico.

Las 54 ejecuciones históricas del TFM permanecen en
[`datos.csv`](../../results/network_degradation/datos.csv). Su interpretación
está en [`RESULTS.md`](../../results/network_degradation/RESULTS.md).
