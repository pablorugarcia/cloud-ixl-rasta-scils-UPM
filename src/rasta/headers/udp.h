/**
 * This is a module which provides a basic network communication interface for UDP
 */

#ifndef LST_SIMULATOR_UDP_H
#define LST_SIMULATOR_UDP_H

#ifdef __cplusplus
extern "C" {  // only need to export C interface if
              // used by C++ source code
#endif

#include <stdint.h>

#include "sys/types.h"
#ifndef PIKEOS_TOOLCHAIN
#include <netinet/in.h>
#else
#include "lwip/udp.h"
#include "lwip/sockets.h"
#include <types.h>
#endif // PIKEOS_TOOLCHAIN

#define IPV4_STR_LEN 16

/**
 * This function will initialise an udp socket and return its file descriptor, which is used to reference it in later
 * function calls
 * @return the udp socket's file descriptor
 */
#ifdef LWIP
struct udp_pcb* rasta_udp_init();
#else
int udp_init();
#endif


/**
 * Binds a given file descriptor to the given @p port
 * @param file_descriptor the is the file descriptor which will be bound to to the @p port.
 * @param port the port the socket will listen on
 */
#ifdef LWIP
void rasta_udp_bind(struct udp_pcb* file_descriptor, uint16_t port);
#else
void udp_bind(int file_descriptor, uint16_t port);
#endif

/**
 * Binds a given file descriptor to the given @p port at the network interface with IPv4 address @p ip
 * @param file_descriptor the is the file descriptor which will be bound to to the @p port.
 * @param port the port the socket will listen on
 * @param ip the IPv4 address of the network interface the socket will listen on.
 */
#ifdef LWIP
void rasta_udp_bind_device(struct udp_pcb* file_descriptor, uint16_t port, char * ip);
#else
void udp_bind_device(int file_descriptor, uint16_t port, char * ip);
#endif

/**
 * Receive data on the given @p file descriptor and store it in the given buffer.
 * This function will block until data is received!
 * @param file_descriptor the file descriptor which should be used to receive data
 * @param received_message a buffer where the received data will be written too. Has to be at least \p max_buffer_len long
 * @param max_buffer_len the amount of data which will be received in bytes
 * @param sender information about the sender of the data will be stored here
 * @return the amount of received bytes
 */
#ifdef LWIP
size_t rasta_udp_receive(struct udp_pcb*  file_descriptor, unsigned char* received_message,size_t max_buffer_len, struct sockaddr_in *sender);
#else
size_t udp_receive(int file_descriptor, unsigned char* received_message, size_t max_buffer_len, struct sockaddr_in *sender);
#endif

/**
 * Sends a message via the given file descriptor to a @p host and @p port
 * @param file_descriptor the file descriptor which is used to send the message
 * @param message the message which will be send
 * @param message_len the length of the @p message
 * @param host the host where the message will be send to. This has to be an IPv4 address in the format a.b.c.d
 * @param port the target port on the host
 */
#ifdef LWIP
void rasta_udp_send(struct udp_pcb* file_descriptor, unsigned char* message, size_t message_len, char* host, uint16_t port);
#else
void udp_send(int file_descriptor, unsigned char* message, size_t message_len, char* host, uint16_t port);
#endif

/**
 * Sends a message via the given file descriptor to a host, the address information is stored in the
 * @p receiver struct
 * @param file_descriptor the file descriptor which is used to send the message
 * @param message the message which will be send
 * @param message_len the length of the @p message
 * @param receiver address information about the receiver of the message
 */
#ifdef LWIP
void rasta_udp_send_sockaddr(struct udp_pcb* file_descriptor, unsigned char* message, size_t message_len, struct sockaddr_in receiver);
#else
void udp_send_sockaddr(int file_descriptor, unsigned char* message, size_t message_len, struct sockaddr_in receiver);
#endif


/**
 * Closes the udp socket
 * @param file_descriptor the file descriptor which identifies the socket
 */
#ifdef LWIP
void rasta_udp_close(struct udp_pcb* file_descriptor);
#else
void udp_close(int file_descriptor);
#endif

void sockaddr_to_host(struct sockaddr_in sockaddr, char* host);

#ifdef __cplusplus
}
#endif

#endif //LST_SIMULATOR_UDP_H