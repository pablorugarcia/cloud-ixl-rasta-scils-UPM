# Pruebas de degradación de red

## Procedencia y alcance de los datos

Este directorio reúne los 54 registros históricos de la campaña de degradación
de red del TFM en `datos.csv` y el script experimental `run_campaign.py`. El
script selecciona `config/rasta_client1_local.cfg` y los destinos de loopback.

No se conservan todos los identificadores de los ejecutables utilizados:
faltan los hashes de los binarios Cloud IXL y OC y la revisión exacta del OC
externo. El historial público no permite identificar las revisiones de ambos
ejecutables ni deducir la fecha exacta de ejecución a partir de un commit.

La versión actual del script permite configurar la ruta del OC y la salida del
CSV. Conserva los escenarios, las esperas y la clasificación de la campaña;
una nueva ejecución genera datos nuevos y no garantiza los mismos tiempos o
resultados.

## Método de la campaña experimental

Las pruebas se hicieron en local con el Cloud IXL y el Object Controller
comunicándose por `127.0.0.1`. El script `netem.sh` aplicó la degradación al
tráfico UDP enviado hacia los puertos 8888 y 8889.

Para cada orden se comprobó si el OC la ejecutaba y cuánto tiempo transcurría
hasta recibir su confirmación. Los escenarios normales se repitieron tres
veces. Los cortes y la pérdida de un solo canal se probaron una vez.

El script consultó `tc -s -j qdisc show dev lo` antes de eliminar cada
degradación. En los escenarios normales lo hizo después de terminar la orden
principal. En los cortes de 5 s y 10 s leyó el contador al finalizar el periodo
de pérdida y, en el corte con una orden pendiente, después de los 5 s de
pérdida; en los tres casos la lectura se hizo inmediatamente antes de limpiar
el qdisc. De la salida seleccionó exclusivamente el qdisc de tipo `netem` con
handle `c1d2:` y guardó su contador genérico `drops` en la columna
`netem_dropped` de `datos.csv`.

Un campo vacío indica que ese qdisc no existía en el momento de la lectura; un
cero indica que sí existía, pero no había registrado descartes. Este contador
describe descartes en el qdisc, no pérdidas extremo a extremo ni órdenes
SCI-LS perdidas.

## Resultados de la campaña experimental

| Condición | Resultado | Tiempo observado | Descartes `netem` |
|---|---|---|---:|
| Sin degradación | 3/3 confirmadas | 14.087–16.919 ms | — |
| Retardo de 100 ms | 3/3 confirmadas | 109.379–113.369 ms | 0 |
| Retardo de 500 ms | 3/3 confirmadas | 505.698–515.525 ms | 0 |
| Retardo de 1000 ms | 3/3 confirmadas | 1005.584–1008.985 ms | 0 |
| Retardo de 3000 ms | 3/3 confirmadas; recuperación fallida 3/3 | 3007.924–3011.503 ms | 0 |
| Pérdida del 1 % | 3/3 confirmadas | 10.785–19.529 ms | 0 |
| Pérdida del 5 % | 3/3 confirmadas | 11.602–20.547 ms | 1 |
| Pérdida del 10 % | 3/3 confirmadas | 11.835–16.590 ms | 1 |
| Pérdida del 30 % | 2/3 confirmadas | 17.719–19.241 ms | 7 |
| Pérdida del 100 % | 0/3 confirmadas | — | 36 |
| Duplicación del 1 % | 3/3 confirmadas | 12.889–19.811 ms | 0 |
| Duplicación del 5 % | 3/3 confirmadas | 16.337–18.484 ms | 0 |
| Duplicación del 10 % | 3/3 confirmadas | 12.902–14.404 ms | 0 |
| Reordenamiento del 5 % | 3/3 confirmadas | 105.633–117.185 ms | 0 |
| Reordenamiento del 10 % | 3/3 confirmadas | 13.737–116.369 ms | 0 |
| Reordenamiento del 25 % | 3/3 confirmadas | 104.451–111.626 ms | 0 |
| Corte de 5 s | Orden y recuperación fallidas | — | 4 |
| Corte de 10 s | Resultado `proceso_cerrado` | — | 10 |
| Corte con una orden pendiente | Orden fallida | — | 4 |
| Pérdida total del canal 1 | Orden confirmada | 16.491 ms | 2 |
| Pérdida total del canal 2 | Orden confirmada | 20.652 ms | 2 |
| Nueva sesión sin degradación | Orden confirmada | 10.872 ms | — |

La columna de descartes de esta tabla suma `netem_dropped` para las
repeticiones de cada condición. Los 54 registros individuales permanecen en
`datos.csv`.

Para ejecutar una nueva campaña desde la raíz, se necesita el OC externo
compatible, sus recursos locales y los requisitos de red indicados en el
[README principal](../../README.md#requisitos). Sustituir la ruta de ejemplo:

```bash
export CLOUD_IXL_OC_BIN="/ruta/al/ejecutable/ls_oc_local"
./results/network_degradation/run_campaign.py
```

El script resuelve la ruta del OC, comprueba que existe y es ejecutable y usa
su directorio como `cwd`. La configuración necesaria para ese OC no se incluye
en esta entrega. La salida predeterminada es un archivo nuevo
`results/network_degradation/runs/datos_<fecha_hora>.csv`, excluido de Git.
Puede elegirse otro nombre con `--output`:

```bash
./results/network_degradation/run_campaign.py --output results/network_degradation/runs/mi_campana.csv
```

Se rechazan los archivos ya existentes y el CSV histórico `datos.csv`, incluso
si se accede a este mediante un enlace simbólico.

## Conclusiones de la campaña experimental

- El script simplificado aplica los escenarios de degradación enumerados en la
  tabla anterior y clasifica el resultado de cada orden.
- Los retardos configurados se reflejan aproximadamente en el tiempo de respuesta.
- Con 3000 ms las tres órdenes principales se confirmaron, pero las tres
  órdenes de recuperación fallaron.
- Con pérdida del 100 % no se confirmó ninguna de las tres órdenes.
- Con pérdida del 10 % se confirmaron las tres órdenes; con pérdida del 30 % se
  confirmaron 2 de las 3. Las diferencias entre repeticiones son compatibles
  con el carácter probabilístico de la perturbación.
- La comunicación sigue funcionando cuando se pierde solamente uno de los dos
  canales.
- `netem_dropped` aporta el número de descartes observado en `c1d2:` durante la
  ventana medida de cada escenario, pero no identifica por sí solo qué mensajes
  de aplicación fueron descartados ni demuestra una relación causal individual
  con cada resultado.
- La lectura anterior al `clear` registró 4, 10 y 4 descartes respectivamente
  en los cortes de 5 s, 10 s y con una orden pendiente.

Estas pruebas describen únicamente el comportamiento observado en el prototipo
local. No demuestran conformidad con RaSTA, EULYNX o requisitos de seguridad.
