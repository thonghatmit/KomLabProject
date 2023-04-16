// interface into pppoe lib
#include <stdio.h> //FRIDOLIN
#include <stdint.h>

struct migration_data_t {
    uint16_t sid;
    char *username;
    struct ipv4db_item_t *ip_item;
    uint8_t calling_station_id[6];
    uint8_t called_station_id[6];
    uint8_t cookie[24]; //probably not required for state migration, leave empty


};

void frido_test(int temp);
struct migration_data_t *parse_cmd_input(char * const *f);
