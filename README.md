# Cloud IXL - SCI-LS/PDI sobre RaSTA

> **Trabajo Fin de Máster - Universidad Politécnica de Madrid**
> **Enclavamientos en la nube. Implementación de EULYNX para controlador del módulo de señales**
> Pablo Rubio García - ETSII UPM - 2026

Prototipo de laboratorio de un **Cloud Interlocking (Cloud IXL)** simulado que intercambia órdenes y estados con el **Object Controller (OC)** de una señal luminosa.

El proyecto implementa el lado del enclavamiento de una arquitectura distribuida **Cloud IXL – Object Controller**, utilizando **SCI-LS/PDI** como interfaz de aplicación y una biblioteca **RaSTA** heredada como mecanismo de transporte.

```text
Cloud IXL
   │
   ├── lógica de rutas
   │
   ├── estado solicitado
   │
   ▼
SCI-LS / PDI
   │
   ▼
RaSTA
   │
   ▼
IPv4 / UDP
   │
   ▼
Object Controller
   │
   ▼
Señal luminosa simulada
```

El estado comunicado por el Object Controller vuelve posteriormente al Cloud IXL, donde puede compararse con el estado previamente comandado.

> [!IMPORTANT]
> Este repositorio contiene un **prototipo académico de laboratorio**.
> No constituye una implementación completa ni una demostración de conformidad con **EULYNX, RaSTA, PoS-Signalling o EN 50159**, no permite atribuir un determinado **SIL** y no representa un sistema ferroviario certificado.

## Alcance del prototipo

El Cloud IXL desarrollado incluye:

* lógica reducida de enclavamiento;
* tres secciones de vía simuladas;
* una aguja simulada;
* una señal luminosa;
* dos rutas incompatibles;
* generación de aspectos de señal;
* adaptación de los estados internos a SCI-LS;
* establecimiento de comunicación RaSTA;
* inicialización PDI;
* comandos de aspecto y luminosidad;
* recepción del estado reportado por el Object Controller;
* comparación `commanded / reported`;
* recepción de errores definidos en el ICD;
* ensayos de degradación de red mediante `tc/netem`.

El escenario ferroviario utilizado es:

```text
             ┌── CV_02 ── B
A ── CV_01 ──┤
             └── CV_03 ── C
                  ^
                 P_01
```

Las rutas disponibles son:

| Ruta      | Secciones        | Posición requerida de `P_01` |
| --------- | ---------------- | ---------------------------- |
| `RUTA_AB` | `CV_01`, `CV_02` | `LEFT`                       |
| `RUTA_AC` | `CV_01`, `CV_03` | `RIGHT`                      |

El modelo no reproduce todas las funciones de un enclavamiento ferroviario real. Entre otras limitaciones, no implementa protección de flanco, bloqueo de aproximación, liberación automática por paso de tren, adquisición segura de estados desde campo ni una topología dinámica.

## Arquitectura software

```text
src/
├── cloud_ixl/
│   ├── c/
│   └── headers/
│
├── sci_ls_icd/
│   ├── c/
│   └── headers/
│
├── sci/
│   ├── c/
│   └── headers/
│
└── rasta/
    ├── c/
    └── headers/
```

| Directorio                     | Responsabilidad                                                       |
| ------------------------------ | --------------------------------------------------------------------- |
| `src/cloud_ixl/`               | Estado, rutas, lógica ferroviaria, entrada/salida y adaptación SCI-LS |
| `src/sci_ls_icd/`              | Contrato SCI-LS específico de la integración Cloud IXL – OC           |
| `src/sci/`                     | Funciones SCI y SCI-LS heredadas o adaptadas                          |
| `src/rasta/`                   | Biblioteca RaSTA utilizada como transporte                            |
| `config/`                      | Configuraciones RaSTA `local` y `lab`                                 |
| `scripts/network/`             | Inyección de degradaciones de red                                     |
| `results/network_degradation/` | Campaña experimental y resultados                                     |
| `tests/`                       | Pruebas CUnit heredadas                                               |

## Requisitos

Entorno recomendado:

* Linux o WSL2;
* GCC con soporte C11;
* CMake [3.13 o posterior](https://cmake.org/cmake/help/v3.13/release/3.13.html#command-line) para los comandos de compilación mostrados;
* `make` o Ninja;
* `pthread`;
* `rt`.

Para los ensayos de red:

* Python 3;
* Bash;
* `iproute2`;
* `util-linux`;
* `coreutils`.

La campaña automatizada necesita además un ejecutable externo del Object
Controller compatible y un sistema que permita crear espacios de nombres de
usuario y red y utilizar `tc/netem` dentro de ellos. El OC no está incluido.

En determinadas configuraciones también puede ser necesaria `libcrypto` de OpenSSL.

## Compilación

Desde la raíz del repositorio:

```bash
cmake -S . -B build
cmake --build build --target cloud_ixl -j2
```

La compilación genera el ejecutable `build/bin/exe/examples/cloud_ixl` y las
bibliotecas `build/bin/lib/librasta.so` y `build/bin/lib/libsci_ls_icd.a`.

CMake también copia los dos perfiles versionados a `build/config/`. El perfil
local por defecto se puede encontrar tanto al ejecutar desde la raíz del
repositorio como desde `build/`. No copia las configuraciones privadas.

## Configuración

El contrato utilizado durante la integración define:

| Parámetro     |     Cloud IXL | Object Controller |
| ------------- | ------------: | ----------------: |
| RaSTA ID      |        `0x62` |            `0x61` |
| SCI ID        | `IXL_CENTRAL` |           `LS_OC` |
| PDI version   |        `0x05` |            `0x05` |
| RaSTA network |        `1234` |            `1234` |

Se incluyen un **perfil local operativo** y una **plantilla de laboratorio**:

```text
config/
├── rasta_client1_local.cfg
└── rasta_client1_lab.cfg
```

Ambos ficheros conservan los identificadores y parámetros de protocolo de la
configuración experimental histórica: entre otros, `T_MAX=10000 ms`,
`T_H=2000 ms` y checksum SR `NONE`. Solo difieren las direcciones locales y sus
comentarios.

### Perfil local

```text
Cloud IXL
├── CH1 → 127.0.0.1:9998
└── CH2 → 127.0.0.1:9999

Object Controller
├── CH1 → 127.0.0.1:8888
└── CH2 → 127.0.0.1:8889
```

### Perfil de laboratorio

La plantilla contiene únicamente direcciones de ejemplo:

```text
Cloud IXL
├── CH1 → 192.0.2.10:9998
└── CH2 → 192.0.2.10:9999

Object Controller
├── CH1 → 192.0.2.20:8888
└── CH2 → 192.0.2.20:8889
```

Estas IP pertenecen al bloque de documentación de [RFC 5737](https://www.rfc-editor.org/rfc/rfc5737.html).
No deben utilizarse como interfaces locales ni para ejecutar directamente el
perfil. Hay que sustituirlas por direcciones asignadas al entorno real.

Desde la raíz del repositorio, crear una copia privada:

```bash
cp -n config/rasta_client1_lab.cfg config/rasta_client1_lab.private.cfg
```

Editar `RASTA_REDUNDANCY_CONNECTIONS` en esa copia con las IP **locales del
Cloud IXL** y los puertos de escucha. Las copias `config/*.private.cfg` están
excluidas de Git. El parser no expande variables de entorno en los ficheros.

Las variables de entorno permiten seleccionar el fichero y los destinos del OC:

| Variable | Valor por defecto |
| --- | --- |
| `CLOUD_IXL_RASTA_CONFIG` | `config/rasta_client1_local.cfg` |
| `CLOUD_IXL_OC_CH1_IP` | `127.0.0.1` |
| `CLOUD_IXL_OC_CH1_PORT` | `8888` |
| `CLOUD_IXL_OC_CH2_IP` | `127.0.0.1` |
| `CLOUD_IXL_OC_CH2_PORT` | `8889` |

Las variables `CLOUD_IXL_OC_CH*` solo cambian los destinos **remotos**; no
modifican los sockets locales de `RASTA_REDUNDANCY_CONNECTIONS`. Las rutas
relativas se resuelven desde el directorio de ejecución.

Para el laboratorio, tras adaptar la copia privada y sustituir los textos
`IP_REAL_DEL_OC_CANAL_*` por las IP reales del OC:

```bash
CLOUD_IXL_RASTA_CONFIG=config/rasta_client1_lab.private.cfg \
CLOUD_IXL_OC_CH1_IP="IP_REAL_DEL_OC_CANAL_1" \
CLOUD_IXL_OC_CH2_IP="IP_REAL_DEL_OC_CANAL_2" \
./build/bin/exe/examples/cloud_ixl
```

Los puertos remotos siguen siendo `8888` y `8889` salvo que se indiquen las
variables `CLOUD_IXL_OC_CH1_PORT` y `CLOUD_IXL_OC_CH2_PORT`. La configuración del
OC externo debe acordarse por separado; dos puertos en una misma interfaz no
demuestran diversidad física.

## Ejecución local

Debe iniciarse primero el Object Controller.

Si no se han definido variables que sustituyan los valores por defecto, basta
con ejecutar `./build/bin/exe/examples/cloud_ixl` desde la raíz. La selección
explícita equivalente es:

```bash
CLOUD_IXL_RASTA_CONFIG=config/rasta_client1_local.cfg \
CLOUD_IXL_OC_CH1_IP=127.0.0.1 \
CLOUD_IXL_OC_CH1_PORT=8888 \
CLOUD_IXL_OC_CH2_IP=127.0.0.1 \
CLOUD_IXL_OC_CH2_PORT=8889 \
./build/bin/exe/examples/cloud_ixl
```

La aplicación espera a:

```text
RaSTA connected
       │
       ▼
PDI Version Check
       │
       ▼
Initialisation Request
       │
       ▼
Initial state
       │
       ▼
PDI established
```

Solo después se permite el intercambio normal de órdenes.

## Interfaz de operación

Una vez establecida la PDI:

```text
Command [r=request, l=release, a=aspect, b=brightness, q=quit]:
```

| Comando | Función                        |
| ------- | ------------------------------ |
| `r`     | Solicitar una ruta             |
| `l`     | Liberar una ruta               |
| `a`     | Enviar directamente un aspecto |
| `b`     | Modificar luminosidad          |
| `q`     | Finalizar                      |

El envío directo de aspectos se utiliza únicamente como herramienta de laboratorio para comprobar la comunicación SCI-LS independientemente de la lógica de rutas.

## Aspectos SCI-LS

La implementación utilizada durante los ensayos mantiene habilitados ocho aspectos:

| Entrada | Aspecto               |
| ------: | --------------------- |
|     `0` | `VIA_LIBRE`           |
|     `1` | `PARADA`              |
|     `2` | `ANUNCIO_PARADA`      |
|     `4` | `ANUNCIO_PRECAUCION`  |
|     `5` | `REBASE`              |
|     `6` | `PARADA_SELECTIVA_N2` |
|     `7` | `REBASE_AUTORIZADO`   |
|     `9` | `APAGADA`             |

`VIA_LIBRE_CONDICIONAL` y `PARADA_SELECTIVA_N1` permanecen definidos en el
contrato del proyecto, pero están deshabilitados en la implementación utilizada
para la validación.

## Commanded / Reported

El prototipo distingue el estado solicitado del estado comunicado por el OC:

```text
commanded → estado solicitado por el Cloud IXL
reported  → estado comunicado posteriormente por el OC
```

Para cada comando de aspecto se conserva el payload comandado. Cuando el
Object Controller devuelve `Msg_Indicated_Signal_Aspect`, ambos valores se
comparan byte a byte.

Los resultados previstos son:

```text
CONFIRMED
MISMATCH
REJECTED
TIMEOUT / COMMUNICATION FAILURE
```

El envío correcto de un telegrama no se considera equivalente a la ejecución correcta de la orden.

## Degradación de red

Los ensayos experimentales utilizan `scripts/network/netem.sh`.

El script permite aplicar:

* latencia;
* pérdida;
* duplicación;
* reordenamiento;
* interrupciones temporales;
* pérdida completa del canal 1;
* pérdida completa del canal 2.

Ejemplos:

```bash
sudo ./scripts/network/netem.sh delay 500
sudo ./scripts/network/netem.sh loss 30
sudo ./scripts/network/netem.sh duplicate 10
sudo ./scripts/network/netem.sh reorder 25
sudo ./scripts/network/netem.sh outage 5
sudo ./scripts/network/netem.sh channel1-loss
```

Limpieza:

```bash
sudo ./scripts/network/netem.sh clear
```

La topología y las limitaciones se describen en el
[README de la herramienta de red](scripts/network/README.md).

## Campaña experimental

La campaña automatizada utilizada en el TFM se encuentra en:

```text
results/network_degradation/
├── run_campaign.py
├── datos.csv
└── RESULTS.md
```

Para una nueva campaña, desde la raíz y con el OC externo ya compilado,
indicar su ruta (absoluta, relativa al directorio actual o con `~`):

```bash
export CLOUD_IXL_OC_BIN="/ruta/al/ejecutable/ls_oc_local"
./results/network_degradation/run_campaign.py
```

Sustituir la ruta de ejemplo por la real. El script comprueba que el fichero
existe y tiene permiso de ejecución y utiliza su directorio como `cwd`; los
recursos que necesite el OC deben estar disponibles desde ese directorio.
La campaña inicia ambos procesos en un espacio de red aislado y fija el perfil
local y los destinos de loopback, con independencia del perfil de laboratorio.

Cada ejecución guarda un CSV nuevo en
`results/network_degradation/runs/datos_<fecha_hora>.csv` (directorio ignorado
por Git). Para elegir otro archivo:

```bash
./results/network_degradation/run_campaign.py --output results/network_degradation/runs/mi_campana.csv
```

El archivo no debe existir. El script rechaza `datos.csv`, también si se indica
mediante un enlace simbólico, y nunca sobrescribe una salida existente.

La campaña documentada en el TFM está formada por **54 ejecuciones**.

Entre las condiciones ensayadas se encuentran:

```text
Nominal
Delay:      100 / 500 / 1000 / 3000 ms
Loss:       1 / 5 / 10 / 30 / 100 %
Duplicate:  1 / 5 / 10 %
Reorder:    5 / 10 / 25 %
Outage:     5 / 10 s
Channel 1:  100 % loss
Channel 2:  100 % loss
```

Los 54 registros históricos se conservan en
[`datos.csv`](results/network_degradation/datos.csv), con su descripción en
[`RESULTS.md`](results/network_degradation/RESULTS.md).

## Resultados principales

En el banco utilizado:

* el funcionamiento nominal se completó correctamente;
* los retardos hasta `1000 ms` permitieron completar las operaciones ensayadas;
* con `3000 ms` las tres órdenes principales fueron confirmadas, pero la operación posterior de recuperación falló en las tres repeticiones;
* las pérdidas de `1 %`, `5 %` y `10 %` no provocaron fallos funcionales en las ejecuciones realizadas;
* con `30 %` de pérdida se confirmaron `2/3` órdenes;
* con `100 %` de pérdida no se confirmó ninguna;
* los escenarios ensayados de duplicación y reordenamiento completaron las operaciones;
* la comunicación continuó cuando se bloqueó individualmente uno de los dos canales.

> [!NOTE]
> Los dos canales del banco local son **canales lógicos** diferenciados por socket y puerto.
> Ambos pueden compartir host, interfaz y camino físico, por lo que estos ensayos **no demuestran redundancia física**.

Los valores anteriores caracterizan exclusivamente este prototipo y no deben interpretarse como límites generales de funcionamiento de RaSTA, EULYNX o una red ferroviaria real.

## Limitaciones conocidas

### Canales de comunicación

Los dos canales utilizados no disponen de diversidad física demostrada.

### RaSTA Safety / Retransmission

El checksum SR permanece configurado como `NONE` para mantener la compatibilidad
con el Object Controller utilizado durante la integración.

Por ello, el banco no permite demostrar todas las propiedades que serían exigibles a una comunicación ferroviaria de seguridad.

### Versiones RaSTA

La biblioteca heredada conserva actualmente una limitación en `version_accepted()`.

Aunque existe una lista `RASTA_ACCEPTED_VERSIONS`, la función devuelve aceptación incluso cuando la versión recibida no coincide con una entrada configurada.

### Serialización SCI

La implementación heredada conserva una dependencia del *endianness* del host en la serialización de determinados tipos de mensaje.

El formato objetivo acordado en el ICD es **little-endian**, pero algunas constantes se almacenan internamente previamente intercambiadas para adaptarse al comportamiento de la biblioteca existente.

Esta particularidad pertenece a la implementación del prototipo y **no constituye un requisito EULYNX**.

### Estado de rutas

La lógica reducida puede marcar una ruta como `RESERVED` antes de recibir la confirmación final del Object Controller.

No se implementa una estrategia completa de recuperación del estado de la ruta ante `MISMATCH`, rechazo o determinados fallos de comunicación.

## Documentación

El contrato de interfaz específico de la integración y determinados documentos
de referencia no están publicados en este repositorio. La documentación local bajo
`docs/` permanece excluida de Git; no es un directorio publicado.

El código de `src/sci_ls_icd/` y el adaptador de `src/cloud_ixl/` conservan la
implementación del contrato SCI-LS del prototipo. Con el código publicado se
pueden estudiar la lógica de rutas, la PDI, la creación y el análisis de
payloads y el transporte heredado, y compilar el Cloud IXL y sus bibliotecas
sin esos documentos ni el OC. Este contrato no es una especificación normativa
general de SCI-LS.

Para reproducir la integración completa se necesita un OC compatible externo,
sus recursos y configuración, y confirmar con su responsable los mensajes,
identificadores y restricciones del contrato específico. El código publicado
describe el lado Cloud IXL; no permite verificar por sí solo el comportamiento
del OC. Las nuevas campañas deben identificarse por separado de los resultados
históricos.

Documentación incluida:

* [Parámetros y limitaciones RaSTA](RASTA_EVALUATION.md).
* [Herramienta de degradación de red](scripts/network/README.md).
* [Resultados históricos y trazabilidad](results/network_degradation/RESULTS.md).
* [Estado de las pruebas](tests/README.md).

## Procedencia

La biblioteca RaSTA incluida en este repositorio deriva de implementaciones públicas previas del protocolo, más concretamente la implementada en el [rasta-protocol de Florian Frank](https://github.com/FlorianFrank/rasta-protocol.git)

Se reconoce la colaboración de Pedro en la integración con el Object Controller
externo.

Sobre esa base, el TFM incorpora principalmente:

* el simulador Cloud IXL;
* la lógica reducida de rutas;
* la gestión del lado Cloud IXL de PDI;
* el adaptador SCI-LS;
* el contrato de interfaz del proyecto;
* la comparación `commanded / reported`;
* las herramientas de degradación;
* la campaña experimental.

## Licencia

El código se distribuye bajo la licencia **MIT** incluida en [LICENSE](LICENSE).
