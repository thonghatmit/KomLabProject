#include <stdlib.h>
#include <string.h>
#include "arpa/inet.h"
#include "pppoe_state_migration.h"
#include "ipdb.h"

//#include "pppoe.h"

void frido_test(int temp){
    printf("frido_test()\n");
}



// pppoe write states USERNAME IP PEER_IP SID MAC1 MAC2 MAC3 MAC4 MAC5 MAC6 C(OOKIE)1 C2 .. C24 
struct migration_data_t *parse_cmd_input(char * const *f){
    // f[3] first

    struct migration_data_t *ret = malloc(sizeof(ret)); //where free?
    ret->ip_item = malloc(sizeof(ret->ip_item));
    //ret->mac = _malloc(sizeof(ret->mac)); normal array, no pointer = no malloc

    // iterate through whitespace separated values passed from CLI, start at 3 (=XXX): "pppoe write states XXX ..."
    // at i=3.2 mil the adressspace for f is finished and the if condition would be true from random data
    for(int i=3; i<19; i++){
        if(f[i]){
            switch(i){
                case 3:
                    // for (int x=0; x<strlen(f[i]) && strlen(f[i]) < 49; x++){
                    //     ret->username[x] = f[i][x];
                        
                    // }
                    if (strlen(f[i]) > 49) {
                        printf("ERROR: username to long (49 chars)\n");
                    } else {
                        ret->username = malloc(strlen(f[i])+1); //malloc required for char array as free() is called at channel/session destruction
                        memset(ret->username, '\0', sizeof(ret->username));
                        strcpy(ret->username, f[i]);
                        printf("Set migrated username: %s\n", f[i]);
                    }
                    break;
                case 4:
	                inet_pton(AF_INET, f[i], &(ret->ip_item->addr));
                    printf("Set migrated addr: %s\n", f[i]);
                    break;
                case 5:
                    //TODO: peer_addr gets saved correctly but session show shows 11.11.11.11 (185273099)
                    // => somewhere else stored!
	                inet_pton(AF_INET, f[i], &(ret->ip_item->peer_addr));
                    printf("Set migrated peer_addr: %s\n", f[i]);
                    break;
                case 6:
                    ret->sid = strtol(f[i], NULL, 10); // 10 = base 10
                    printf("Set migrated sid: %i\n", ret->sid);
                    break;
                case 7: // case 7 includes 8,9,10,11,12 for each MAC addr byte, calling_station_id
                    if(f[12]){ //check if last MAC byte is set
                        ret->calling_station_id[0] = strtol(f[7], NULL, 10);
                        ret->calling_station_id[1] = strtol(f[8], NULL, 10);
                        ret->calling_station_id[2] = strtol(f[9], NULL, 10);
                        ret->calling_station_id[3] = strtol(f[10], NULL, 10);
                        ret->calling_station_id[4] = strtol(f[11], NULL, 10);
                        ret->calling_station_id[5] = strtol(f[12], NULL, 10);
                    }
                    break;
                case 13: // case 7 includes 8,9,10,11,12 for each MAC addr byte, calling_station_id
                    if(f[18]){ //check if last MAC byte is set
                        ret->called_station_id[0] = strtol(f[13], NULL, 10);
                        ret->called_station_id[1] = strtol(f[14], NULL, 10);
                        ret->called_station_id[2] = strtol(f[15], NULL, 10);
                        ret->called_station_id[3] = strtol(f[16], NULL, 10);
                        ret->called_station_id[4] = strtol(f[17], NULL, 10);
                        ret->called_station_id[5] = strtol(f[18], NULL, 10);
                    }
                    break;
                // case 19:
                //     if(f[42]){
                //         for(int z=0; z<24; z++){
                //             ret->cookie[z] = strtol(f[13+z], NULL, 10);
                //         }
                //     }
                //     break;
            }
        }
    }

	return ret;
}