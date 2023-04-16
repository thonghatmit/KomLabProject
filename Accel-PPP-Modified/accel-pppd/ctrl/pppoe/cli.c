#include <string.h>
#include <stdlib.h>
#include <netinet/in.h>
#include <net/ethernet.h>

#include "triton.h"
#include "cli.h"
#include "ppp.h"
#include "memdebug.h"

#include "pppoe.h"


//FRIDOLIN
#include "ipdb.h"
#include "arpa/inet.h"
#include "events.h"
#include "pppoe_state_migration.h"
extern struct pppoe_serv_t *global_serv;


static void show_interfaces(void *cli)
{
	struct pppoe_serv_t *serv;

	printf("FRIDOLIN: show_imnterfaces");

	cli_send(cli, "interface:   connections:    state:\r\n");
	cli_send(cli, "-----------------------------------\r\n");

	pthread_rwlock_rdlock(&serv_lock);
	list_for_each_entry(serv, &serv_list, entry) {
		cli_sendv(cli, "%9s    %11u    %6s\r\n", serv->ifname, serv->conn_cnt, serv->stopping ? "stop" : "active");
	}
	pthread_rwlock_unlock(&serv_lock);
}

static void intf_help(char * const *fields, int fields_cnt, void *client)
{
	uint8_t show = 7;

	if (fields_cnt >= 3) {
		show &= (strcmp(fields[2], "add")) ? ~1 : ~0;
		show &= (strcmp(fields[2], "del")) ? ~2 : ~0;
		show &= (strcmp(fields[2], "show")) ? ~4 : ~0;
		if (show == 0) {
			cli_sendv(client, "Invalid action \"%s\"\r\n",
				  fields[2]);
			show = 7;
		}
	}
	if (show & 1)
		cli_send(client,
			 "pppoe interface add <name>"
			 " - start pppoe server on specified interface\r\n");
	if (show & 2)
		cli_send(client,
			 "pppoe interface del <name>"
			 " - stop pppoe server on specified interface and"
			 " drop his connections\r\n");
	if (show & 4)
		cli_send(client,
			 "pppoe interface show"
			 " - show interfaces on which pppoe server"
			 " started\r\n");
}

static int intf_exec(const char *cmd, char * const *fields, int fields_cnt, void *client)
{
	if (fields_cnt == 2)
		goto help;

	if (fields_cnt == 3) {
		if (!strcmp(fields[2], "show"))
			show_interfaces(client);
		else
			goto help;

		return CLI_CMD_OK;
	}

	if (fields_cnt != 4)
		goto help;

	if (!strcmp(fields[2], "add"))
		pppoe_server_start(fields[3], client);
	else if (!strcmp(fields[2], "del"))
		pppoe_server_stop(fields[3]);
	else
		goto help;

	return CLI_CMD_OK;
help:
	intf_help(fields, fields_cnt, client);
	return CLI_CMD_OK;
}

//===================================

static int show_stat_exec(const char *cmd, char * const *fields, int fields_cnt, void *client)
{
	cli_send(client, "pppoe:\r\n");
	cli_sendv(client, "  starting: %u\r\n", stat_starting);
	cli_sendv(client, "  active: %u\r\n", stat_active);
	cli_sendv(client, "  delayed PADO: %u\r\n", stat_delayed_pado);
	cli_sendv(client, "  recv PADI: %lu\r\n", stat_PADI_recv);
	cli_sendv(client, "  drop PADI: %lu\r\n", stat_PADI_drop);
	cli_sendv(client, "  sent PADO: %lu\r\n", stat_PADO_sent);
	cli_sendv(client, "  recv PADR(dup): %lu(%lu)\r\n", stat_PADR_recv, stat_PADR_dup_recv);
	cli_sendv(client, "  sent PADS: %lu\r\n", stat_PADS_sent);
	cli_sendv(client, "  filtered: %lu\r\n", stat_filtered);

	return CLI_CMD_OK;
}

//===================================

static void set_verbose_help(char * const *f, int f_cnt, void *cli)
{
	cli_send(cli, "pppoe set verbose <n> - set verbosity of pppoe logging\r\n");
}

static void set_pado_delay_help(char * const *f, int f_cnt, void *cli)
{
	cli_send(cli, "pppoe set PADO-delay <delay[,delay1:count1[,delay2:count2[,...]]]> - set PADO delays (ms)\r\n");
}

static void set_service_name_help(char * const *f, int f_cnt, void *cli)
{
	cli_send(cli, "pppoe set Service-Name <name> - set Service-Name to respond\r\n");
	cli_send(cli, "pppoe set Service-Name * - respond with client's Service-Name\r\n");
}

static void set_ac_name_help(char * const *f, int f_cnt, void *cli)
{
	cli_send(cli, "pppoe set AC-Name <name> - set AC-Name tag value\r\n");
}

static void show_verbose_help(char * const *f, int f_cnt, void *cli)
{
	cli_send(cli, "pppoe show verbose - show current verbose value\r\n");
}

static void show_pado_delay_help(char * const *f, int f_cnt, void *cli)
{
	cli_send(cli, "pppoe show PADO-delay - show current PADO delay value\r\n");
}

static void show_service_name_help(char * const *f, int f_cnt, void *cli)
{
	cli_send(cli, "pppoe show Service-Name - show current Service-Name value\r\n");
}

static void show_ac_name_help(char * const *f, int f_cnt, void *cli)
{
	cli_send(cli, "pppoe show AC-Name - show current AC-Name tag value\r\n");
}

static int show_verbose_exec(const char *cmd, char * const *f, int f_cnt, void *cli)
{
	if (f_cnt != 3)
		return CLI_CMD_SYNTAX;

	cli_sendv(cli, "%i\r\n", conf_verbose);

	return CLI_CMD_OK;
}

static int show_pado_delay_exec(const char *cmd, char * const *f, int f_cnt, void *cli)
{
	if (f_cnt != 3)
		return CLI_CMD_SYNTAX;

	cli_sendv(cli, "%s\r\n", conf_pado_delay);

	return CLI_CMD_OK;
}

static int show_service_name_exec(const char *cmd, char * const *f, int f_cnt, void *cli)
{
	if (f_cnt != 3)
		return CLI_CMD_SYNTAX;

	if (conf_service_name[0]) {
		int i = 0;
		do {
		    cli_sendv(cli, "%s", conf_service_name[i]);
		    i++;
		    if (conf_service_name[i]) { cli_sendv(cli, ","); }
		} while(conf_service_name[i]);
		cli_sendv(cli, "\r\n");
	} else
		cli_sendv(cli, "*\r\n");

	return CLI_CMD_OK;
}

static int show_ac_name_exec(const char *cmd, char * const *f, int f_cnt, void *cli)
{
	if (f_cnt != 3)
		return CLI_CMD_SYNTAX;

	cli_sendv(cli, "%s\r\n", conf_ac_name);

	return CLI_CMD_OK;
}

static int set_verbose_exec(const char *cmd, char * const *f, int f_cnt, void *cli)
{
	if (f_cnt != 4)
		return CLI_CMD_SYNTAX;

	if (!strcmp(f[3], "0"))
		conf_verbose = 0;
	else if (!strcmp(f[3], "1"))
		conf_verbose = 1;
	else
		return CLI_CMD_INVAL;

	return CLI_CMD_OK;
}

static int set_pado_delay_exec(const char *cmd, char * const *f, int f_cnt, void *cli)
{
	if (f_cnt != 4)
		return CLI_CMD_SYNTAX;

	if (dpado_parse(f[3]))
		return CLI_CMD_INVAL;

	return CLI_CMD_OK;
}

static int set_service_name_exec(const char *cmd, char * const *f, int f_cnt, void *cli)
{
	if (f_cnt != 4)
		return CLI_CMD_SYNTAX;

	if (conf_service_name[0]) {
		int i = 0;
		do {
		    _free(conf_service_name[i]);
		    i++;
		} while(conf_service_name[i]);
		conf_service_name[0] = NULL;
	}
	if (!strcmp(f[3], "*"))
		conf_service_name[0] = NULL;
	else {
	    char *conf_service_name_string = _strdup(f[3]);
	    char *p = strtok (conf_service_name_string, ",");
	    int i = 0;
	    while (p != NULL && i<255) {
		conf_service_name[i++] = _strdup(p);
		p = strtok(NULL, ",");
	    }
	    conf_service_name[i] = NULL;
	    _free(conf_service_name_string);
	}

	return CLI_CMD_OK;
}

static int set_ac_name_exec(const char *cmd, char * const *f, int f_cnt, void *cli)
{
	if (f_cnt != 4)
		return CLI_CMD_SYNTAX;

	_free(conf_ac_name);
	conf_ac_name = _strdup(f[3]);

	return CLI_CMD_OK;
}
//===================================


// FRIDOLIN
static int show_states_exec(const char *cmd, char * const *f, int f_cnt, void *cli)
{
	if (f_cnt != 3)
		return CLI_CMD_SYNTAX;

	struct pppoe_serv_t *serv;
	struct pppoe_conn_t *conn;

	pthread_rwlock_rdlock(&serv_lock);
	int sessions_for_json = 0;
	int counter = 0;

	list_for_each_entry(serv, &serv_list, entry) { list_for_each_entry(conn, &serv->conn_list, entry){ sessions_for_json = sessions_for_json + 1; } };

	printf("sessions_for_json: %i\n", sessions_for_json);

	char json_str [10000] = "{\"pppoe_states\":[";

	list_for_each_entry(serv, &serv_list, entry) {
		list_for_each_entry(conn, &serv->conn_list, entry){
			// cli_sendv(cli, "sid: %i \r\n", conn->sid);
			// cli_sendv(cli, "addr: ");
			// for(int i=0; i < ETH_ALEN; i++){
			// 	cli_sendv(cli, "%i, ", conn->addr[i]);
			// }
			// cli_sendv(cli, "\r\nppp_started: %i \r\n", conn->ppp_started);
			// //cli_sendv(cli, "host_uniq: %s \r\n", conn->host_uniq->tag_data);
			// //cli_sendv(cli, "service_name: %s \r\n", conn->service_name->tag_data);
			// cli_sendv(cli, "cookie: ");
			// for(int i=0; i < COOKIE_LENGTH-4; i++){
			// 	cli_sendv(cli, "%i, ", conn->cookie[i]);
			// }
			// cli_sendv(cli, "\r\nsessionid: %s\r\n", conn->ppp.ses.sessionid);
			// if (conn->ppp.ses.username)
			// 	cli_sendv(cli, "username: %s\r\n", conn->ppp.ses.username);

			// if(conn->ppp.ses.ipv4){
			// 	char buf[INET6_ADDRSTRLEN];
			// 	inet_ntop(AF_INET, &conn->ppp.ses.ipv4->addr, buf, INET6_ADDRSTRLEN);
			// 	cli_sendv(cli, "ip: %s\r\n", buf);

			// 	inet_ntop(AF_INET, &conn->ppp.ses.ipv4->peer_addr, buf, INET6_ADDRSTRLEN);
			// 	cli_sendv(cli, "peer_ip: %s\r\n", buf);
			// }

			// if(conn->ppp.ses.ctrl->calling_station_id){
			// 	cli_sendv(cli, "calling_station_id: %s\r\n", conn->ppp.ses.ctrl->calling_station_id);
			// }

			// if(conn->ppp.ses.ctrl->called_station_id){
			// 	cli_sendv(cli, "called_station_id: %s\r\n", conn->ppp.ses.ctrl->called_station_id);
			// }

			// cli_sendv(cli, "--------------\r\n");

			//////////////
			// create json
			char* val_str; //TODO: FREE!
			

			if(0 > asprintf(&val_str, "{\"sid\":%d,", conn->sid)) printf("error formatting sid\n");
			strncat(json_str, val_str, sizeof(json_str) - strlen(json_str) - 1);

			// if(0 > asprintf(&val_str, "{\"addr\":%d\n,", conn->sid)) printf("error formatting\n");

			// cli_sendv(cli, "addr: ");
			// for(int i=0; i < ETH_ALEN; i++){
			// 	cli_sendv(cli, "%i, ", conn->addr[i]);
			// }
			// cli_sendv(cli, "\r\nppp_started: %i \r\n", conn->ppp_started);
			// cli_sendv(cli, "cookie: ");
			// for(int i=0; i < COOKIE_LENGTH-4; i++){
			// 	cli_sendv(cli, "%i, ", conn->cookie[i]);
			// }

			// cli_sendv(cli, "\r\nsessionid: %s\r\n", conn->ppp.ses.sessionid);

		
			if (conn->ppp.ses.username){
				if(0 > asprintf(&val_str, "\"username\":\"%s\",", conn->ppp.ses.username)) printf("error formatting username\n");
				strncat(json_str, val_str, sizeof(json_str) - strlen(json_str) - 1);
			}

			if(conn->ppp.ses.ipv4){
				char buf[INET6_ADDRSTRLEN];
				//ip
				inet_ntop(AF_INET, &conn->ppp.ses.ipv4->addr, buf, INET6_ADDRSTRLEN);

				if(0 > asprintf(&val_str, "\"ip\":\"%s\",", buf)) printf("error formatting ip\n");
				strncat(json_str, val_str, sizeof(json_str) - strlen(json_str) - 1);

				if(0 > asprintf(&val_str, "\"ip_raw\":%i,", conn->ppp.ses.ipv4->addr)) printf("error formatting ip_raw\n");
				strncat(json_str, val_str, sizeof(json_str) - strlen(json_str) - 1);

				//peer_ip
				inet_ntop(AF_INET, &conn->ppp.ses.ipv4->peer_addr, buf, INET6_ADDRSTRLEN);
				if(0 > asprintf(&val_str, "\"peer_ip\":\"%s\",", buf)) printf("error formatting peer_ip\n");
				strncat(json_str, val_str, sizeof(json_str) - strlen(json_str) - 1);

				if(0 > asprintf(&val_str, "\"peer_ip_raw\":%i,", conn->ppp.ses.ipv4->peer_addr)) printf("error formatting peer_ip_raw\n");
				strncat(json_str, val_str, sizeof(json_str) - strlen(json_str) - 1);
			}

			if(conn->ppp.ses.ctrl->calling_station_id){
				if(0 > asprintf(&val_str, "\"calling_station_id\":\"%s\",", conn->ppp.ses.ctrl->calling_station_id)) printf("error formatting calling_station_id\n");
				strncat(json_str, val_str, sizeof(json_str) - strlen(json_str) - 1);
			}

			if(conn->ppp.ses.ctrl->called_station_id){
				if(0 > asprintf(&val_str, "\"called_station_id\":\"%s\"}", conn->ppp.ses.ctrl->called_station_id)) printf("error formatting called_station_id\n");
				strncat(json_str, val_str, sizeof(json_str) - strlen(json_str) - 1);
			}

			counter = counter + 1;

			printf("counter: %i\n", counter);
			if(counter < sessions_for_json){
				strncat(json_str, ",", sizeof(json_str) - strlen(json_str) - 1);
			}
		}
		
	}

	strncat(json_str, "]}", sizeof(json_str) - strlen(json_str) - 1);

	cli_sendv(cli, "%s\r\n", json_str);

	pthread_rwlock_unlock(&serv_lock);

	// pthread_mutex_lock(&serv->lock);
	// struct pppoe_conn_t *conn;
	// list_for_each_entry(conn, &serv->conn_list, entry) {
	// 	cli_sendv(cli, "SID: hallo\r\n");
	// 	//printf("conn-sid: %i\n", conn->sid);
	// 	//cli_sendv(cli, "SID: %i\r\n", conn->sid);
	// }
	// pthread_mutex_unlock(&serv->lock);

	//cli_sendv(cli, "IFNAME: %s\r\n", serv->ifname);

	return CLI_CMD_OK;
}

static void show_states_help(char * const *f, int f_cnt, void *cli)
{
	cli_send(cli, "pppoe show states - print states for migration\r\n");
}

static void write_states_help(char * const *f, int f_cnt, void *cli)
{
	cli_send(cli, "pppoe write states - write states for migration\r\n");
}



static int write_states_exec(const char *cmd, char * const *f, int f_cnt, void *cli){
	struct pppoe_conn_t *conn;
	
	pthread_rwlock_rdlock(&serv_lock);

	struct pppoe_serv_t *serv;
	int counter, counter2;
	counter = 0;
	counter2 = 0;
	list_for_each_entry(serv, &serv_list, entry) {
		counter = counter+1;
		list_for_each_entry(conn, &serv->conn_list, entry){
			counter2 = counter2 + 1;
		}
	} // just take the first serv

	// when selected by list_for_each: serv->conn_list = {next = 0x5555557c44d8, prev = 0x100000001}

	printf("serv in serv_list: %i\n", counter);
	printf("conn in serv_list.serv: %i\n", counter2);

	// when triton serv->conn_list = {next = 0xb350e72929fdf28d, prev = 0x0}
	//struct pppoe_serv_t *serv_triton = container_of(triton_context_self(), typeof(*serv), ctx);
	//struct pppoe_serv_t *serv_triton = container_of(triton_context_self(), typeof(*serv_triton), ctx);
	//serv_triton->conn_list.prev = serv_triton->conn_list.next; //DIRTY hack to set both adresses equal, dont know why container_of returns it this way => prev.next is wrong then

	//static void pppoe_serv_close(struct triton_context_t *ctx)
	//struct pppoe_serv_t *serv = container_of(ctx, typeof(*serv), ctx);

	
	
	struct migration_data_t *parsed_vals = parse_cmd_input(f);
	for(int i=0; i<6; i++){
		global_serv->hwaddr[i] = parsed_vals->called_station_id[i];
	}
	//global_serv->hwaddr = parsed_vals->called_station_id;

	// calling_station_id = &parsed_vals->mac[0]
	conn = allocate_channel_migrated(global_serv, &parsed_vals->calling_station_id[0], &parsed_vals->cookie[0], parsed_vals->sid);
	ap_session_set_username(&conn->ppp.ses, parsed_vals->username);
	connect_ppp_channel(&conn->ppp);  // sets ifname (e.g. ppp0)
	conn->ppp.ses.ipv4 = parsed_vals->ip_item;
	// ap_session_starting(&conn->ppp.ses); ???
	ap_session_activate(&conn->ppp.ses);
 	
	//custom var, important to e.g. prevent lcp rejection when client terminates (unexpected as no session setup is done for migrated state)
	// => maybe later fix migrated state to full migrated incl. authentication (lcp layer), then termination messages will be processed correctly
	conn->ppp.ses.is_migrated = 1;

	// set_owner_migration(&conn->ppp.ses); implemented in ippool.c include not working

	// uint8_t mac[ETHER_ADDR_LEN];
	// mac[0] = 171;
	// mac[1] = 188;
	// mac[2] = 239;
	// mac[3] = 1;
	// mac[4] = 1;
	// mac[5] = 1; // = ab:cd:ef:01:01:01 for testing

	// uint8_t cookie[COOKIE_LENGTH];
	// for (int i=0; i<COOKIE_LENGTH; i++){
	// 	cookie[i] = i; //test data ..
	// }

	// uint16_t sid_migrated;
	// sid_migrated = 42;

	// conn = allocate_channel_migrated(global_serv, &mac[0], &cookie[0], sid_migrated);

 	// //important to use malloc as free is called on username when channel is destroyed
	// char *username = _malloc(100);
	// if (username) {
	// 	username[0] = 'F';
	// 	username[1] = 'r'; 
	// 	username[2] = 'i';
	// 	username[3] = 'd'; 
	// 	username[4] = 'o'; 
	// }


	// printf("username to set: %s\n", username);
	// ap_session_set_username(&conn->ppp.ses, username);

	// connect_ppp_channel(&conn->ppp);  // sets ifname (e.g. ppp0)

	// struct ipv4db_item_t *ip_item = _malloc(sizeof(ip_item));
	// inet_pton(AF_INET, "9.8.7.6", &(ip_item->addr));
	// inet_pton(AF_INET, "1.3.5.7", &(ip_item->peer_addr));

	// conn->ppp.ses.ipv4 = ip_item;//ipdb_get_ipv4(conn->ppp.ses);//->ipv4->peer_addr = NULL;

	// conn->ppp.ses.state = AP_STATE_RESTORE;

	// //triton_event_fire(EV_CTRL_STARTING, &conn->ppp.ses); //KA was hier passiert?
	// //triton_event_fire(EV_CTRL_STARTED, &conn->ppp.ses);
	// //ap_session_starting(&conn->ppp.ses);
	// ap_session_activate(&conn->ppp.ses);
	
	// //u_inet_ntoa(ses->ipv4->peer_addr, buf);
 
	// //triton_context_call(&conn->ctx, (triton_event_func)connect_channel_wrapper, conn); //FRIDOLIN: connect channel creates ppp interfaces

	// printf("AFTER ALLOC CHANNEL MIRATED:\n");
	// struct pppoe_serv_t *serv2;
	// //int counter, counter2;
	// counter = 0;
	// counter2 = 0;
	// list_for_each_entry(serv2, &serv_list, entry) {
	// 	counter = counter+1;
	// 	list_for_each_entry(conn, &serv2->conn_list, entry){
	// 		counter2 = counter2 + 1;
	// 	}
	// } // just take the first serv

	// printf("serv in serv_list: %i\n", counter);
	// printf("conn in serv_list.serv: %i\n\n", counter2);
	
	pthread_rwlock_unlock(&serv_lock);

	return CLI_CMD_OK;
}

// FRIDOLIN END


static void init(void)
{
	cli_register_simple_cmd2(show_stat_exec, NULL, 2, "show", "stat");
	cli_register_simple_cmd2(intf_exec, intf_help, 2, "pppoe", "interface");
	cli_register_simple_cmd2(set_verbose_exec, set_verbose_help, 3, "pppoe", "set", "verbose");
	cli_register_simple_cmd2(set_pado_delay_exec, set_pado_delay_help,
				 3, "pppoe", "set", "PADO-delay");
	cli_register_simple_cmd2(set_service_name_exec, set_service_name_help,
				 3, "pppoe", "set", "Service-Name");
	cli_register_simple_cmd2(set_ac_name_exec, set_ac_name_help,
				 3, "pppoe", "set", "AC-Name");
	cli_register_simple_cmd2(show_verbose_exec, show_verbose_help,
				 3, "pppoe", "show", "verbose");
	cli_register_simple_cmd2(show_pado_delay_exec, show_pado_delay_help,
				 3, "pppoe", "show", "PADO-delay");
	cli_register_simple_cmd2(show_service_name_exec, show_service_name_help,
				 3, "pppoe", "show", "Service-Name");
	cli_register_simple_cmd2(show_ac_name_exec, show_ac_name_help,
				 3, "pppoe", "show", "AC-Name");

	//FRIDOLIN
	cli_register_simple_cmd2(show_states_exec, show_states_help,
				 3, "pppoe", "show", "states");
	cli_register_simple_cmd2(write_states_exec, write_states_help,
				 3, "pppoe", "write", "states");
}

DEFINE_INIT(22, init);
