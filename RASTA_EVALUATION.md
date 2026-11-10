# Canales, parámetros RaSTA y jerarquía de timeouts

## Alcance

Esta nota describe decisiones del prototipo de laboratorio Cloud IXL. No es una
implementación normativa ni evidencia de conformidad EULYNX, RaSTA, EN 50159 o
SIL4.

La comparación original tomó como referencia `Eu.Doc.92 v4.3 (1.A)`, que no se
publica en este repositorio. La documentación local bajo `docs/` está excluida
de Git. Los valores anotados para SCI sobre UDP son `Tmax=1800 ms`, `Th=300 ms`,
`Nsendmax=20`, `MWA=10`, `NmaxPaket=1`, `Tseq=100 ms`,
`NdeferQueueSize=4`, safety code de ocho bytes y dos canales físicos.
Estos valores permiten entender la comparación; para contrastarlos es necesario
consultar el documento de referencia.

## Decisión para el OC de la integración histórica

Las condiciones del OC recogidas durante la integración fueron las siguientes.
Su código y configuración no forman parte de este repositorio:

- el OC utilizaba `Th=2000 ms`; un `Tmax=1800 ms` local podría vencer antes del
  siguiente heartbeat entrante durante una conexión ociosa;
- el OC utilizaba checksum SR `NONE`; cambiar solo Cloud IXL a `HALF` cambia el
  formato que el receptor espera y puede impedir el handshake.

Por ello el perfil local y la plantilla de laboratorio conservan
`Tmax=10000 ms` y checksum `NONE`.
La tabla compara esa configuración con los valores de referencia y recoge una
propuesta para una evaluación futura. La propuesta no constituye un perfil
conforme y no se aportan resultados experimentales que la validen.

| Parámetro | Lab | Eu.Doc.92 UDP | Propuesta unilateral | Decisión |
|---|---:|---:|---:|---|
| `T_MAX` | 10000 ms | 1800 ms | 10000 ms | Mantener por `Th=2000 ms` en el OC. |
| `T_H` | 2000 ms | 300 ms | 300 ms | Local; mayor frecuencia es compatible. |
| `SR_CHECKSUM_LEN` | `NONE` | `HALF` | `NONE` | Requiere coordinación bilateral. |
| `SEND_MAX` | 10 | 20 | 20 | Se anuncia en el handshake; no exige igualdad. |
| `MWA` | 10 | 10 | 10 | Ya coincide. |
| `MAX_PACKET` | 3 | 1 | 1 | Agrupación local; SCI-LS envía un mensaje. |
| `T_SEQ` | 50 ms | 100 ms | 100 ms | Cola de redundancia local. |
| `N_DEFERQUEUE_SIZE` | 2 | 4 | 4 | Cola de redundancia local. |

El parser no soporta herencia entre configuraciones. Para ejecutar esta
propuesta habría que crear un perfil completo y autosuficiente que explicitase
también las dos desviaciones. La compatibilidad debe verificarse con el OC
externo disponible antes de ensayar la propuesta.

## Configuración de los dos canales

Cada entrada de `RASTA_REDUNDANCY_CONNECTIONS` crea un socket UDP y lo liga a
su IP y puerto local. Los destinos se suministran por separado:

| Canal | Local | Remoto |
|---|---|---|
| 1 | primera entrada de `RASTA_REDUNDANCY_CONNECTIONS` | `CLOUD_IXL_OC_CH1_IP`, `CLOUD_IXL_OC_CH1_PORT` |
| 2 | segunda entrada de `RASTA_REDUNDANCY_CONNECTIONS` | `CLOUD_IXL_OC_CH2_IP`, `CLOUD_IXL_OC_CH2_PORT` |

El arranque por defecto selecciona `config/rasta_client1_local.cfg` y destinos
`127.0.0.1:8888` y `127.0.0.1:8889`. La plantilla `rasta_client1_lab.cfg`
solo cambia las IP locales por ejemplos que deben sustituirse en una copia
privada; el [README](README.md#configuración) explica su preparación. Los demás
parámetros de ambos ficheros son iguales y se conservan sin cambios.

La documentación histórica describe un OC que escuchaba en `0.0.0.0:8888` y
`0.0.0.0:8889`; debe comprobarse la configuración del OC externo que se utilice.
Dos puertos o dos alias IP sobre la misma NIC solo aportan redundancia lógica.

Para demostrar dos canales físicos se necesitan, como mínimo:

- dos NIC físicas independientes en Cloud IXL y dos en el OC;
- direccionamiento y rutas que asocien cada par local/remoto a su NIC;
- dos enlaces y caminos de red sin un único enlace físico compartido;
- evidencia de ruta y una prueba de desconexión física de cada camino por
  separado, manteniendo operativo el otro.

El entorno WSL descrito durante el desarrollo exponía únicamente `lo` y una
`eth0`; esa observación histórica no permite demostrar diversidad física.

## Jerarquía temporal del PoC

En el código publicado, el timeout global PDI y el `T_MAX` configurado son:

```text
T_PDI = 11 s > T_RaSTA_failure_detection nominal = 10 s
```

El plazo PDI se calcula conservando los nanosegundos del instante de inicio. El hilo
RaSTA comprueba `T_i` periódicamente, con hasta unos 500 ms entre sondeos en la
implementación actual; el margen no constituye una garantía de tiempo real.

La jerarquía anterior se aplica a una sesión ya establecida. `T_i` se arma después
del `ConnectionResponse`; durante el handshake, el timeout global PDI sigue
limitando el establecimiento.

Los callbacks de timeout y `CLOSED` se ejecutan en hilos separados, por lo que
el orden de sus líneas de log puede variar. El Cloud IXL conserva `PDI_FAILED`
si el timeout RaSTA ya lo estableció, evitando que `CLOSED` lo sobrescriba con
`PDI_DISCONNECTED` durante una orden pendiente.

Toda campaña futura que aplique la propuesta anterior o el timeout PDI de 11
segundos debe registrarse como una campaña nueva. Los resultados históricos de
`results/network_degradation/` mantienen su configuración y significado.
