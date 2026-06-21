#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <sys/socket.h>
#include <netinet/ip.h>
#include <netinet/tcp.h>

#define BUFFER_SIZE 65536

void print_data(unsigned char *data, int size)
{
    for(int i = 0; i < size; i++)
    {
        if(data[i] >= 32 && data[i] <= 126)
            printf("%c", data[i]);
        else
            printf(".");
    }
    printf("\n");
}

int main()
{
    int sock_raw;
    char buffer[BUFFER_SIZE];

    struct sockaddr saddr;
    socklen_t saddr_size = sizeof(saddr);

    // Create TCP raw socket
    sock_raw = socket(AF_INET, SOCK_RAW, IPPROTO_TCP);

    if(sock_raw < 0)
    {
        perror("Socket creation failed");
        return 1;
    }

    printf("ROLL_NO=CSB24069\n");
    printf("ASSIGNED_PROTOCOL=TCP\n\n");

    int count = 0;

    while(count < 20)
    {
        int packet_size = recvfrom(
            sock_raw,
            buffer,
            BUFFER_SIZE,
            0,
            &saddr,
            &saddr_size
        );

        if(packet_size < 0)
        {
            perror("Packet receive failed");
            close(sock_raw);
            return 1;
        }

        // IP Header
        struct iphdr *ip_header = (struct iphdr *)buffer;

        // TCP Header
        struct tcphdr *tcp_header =
            (struct tcphdr *)
            (buffer + (ip_header->ihl * 4));

        struct sockaddr_in src, dst;

        src.sin_addr.s_addr = ip_header->saddr;
        dst.sin_addr.s_addr = ip_header->daddr;

        // TCP payload
        int ip_header_length = ip_header->ihl * 4;
        int tcp_header_length = tcp_header->doff * 4;

        int header_size =
            ip_header_length + tcp_header_length;

        int payload_size =
            packet_size - header_size;

        unsigned char *payload =
            (unsigned char *)(buffer + header_size);

        count++;

        printf("PACKET_NO=%d\n", count);

        printf("SRC_IP=%s\n",
               inet_ntoa(src.sin_addr));

        printf("DST_IP=%s\n",
               inet_ntoa(dst.sin_addr));

        printf("PROTOCOL=TCP\n");

        printf("PROTOCOL_NO=%d\n",
               ip_header->protocol);

        printf("TTL=%d\n",
               ip_header->ttl);

        printf("PACKET_SIZE=%d\n",
               packet_size);


        // Task 5 additional field
        printf("IP_HEADER_LENGTH=%d bytes\n",
               ip_header_length);


        printf("SRC_PORT=%d\n",
               ntohs(tcp_header->source));

        printf("DST_PORT=%d\n",
               ntohs(tcp_header->dest));


        // TCP Flags
        printf("TCP_FLAGS=");

        if(tcp_header->syn)
            printf("SYN ");

        if(tcp_header->ack)
            printf("ACK ");

        if(tcp_header->fin)
            printf("FIN ");

        if(tcp_header->rst)
            printf("RST ");

        if(tcp_header->psh)
            printf("PSH ");

        if(tcp_header->urg)
            printf("URG ");


        printf("\n");


        // Optional payload display
        printf("PAYLOAD_SIZE=%d bytes\n",
               payload_size);

        if(payload_size > 0)
        {
            printf("PAYLOAD_DATA=");
            print_data(payload, payload_size);
        }

        printf("\n---------------------------------\n\n");
    }

    close(sock_raw);

    return 0;
}
