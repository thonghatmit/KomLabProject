# taken from http://networkingbodges.blogspot.com/2012/10/using-scapy-to-test-pppoe-ac-cookie.html

import os
from scapy.all import *


class PPPoESession(Automaton):
  randomcookie = False
  retries = 100
  outif="veth-A-Client"
  # Change to mac address to the one from veth-A-Client 'ip link show veth-A-Client'
  mac="a2:9a:13:c6:33:b1" 
  hu="\x7a\x0e\x00\x00"
  ac_cookie=""
  ac_mac="ff:ff:ff:ff:ff:ff"
  our_magic="\x01\x23\x45\x67"
  their_magic="\x00\x00\x00\x00"
  sess_id = 0
# Method to recover an AC-Cookie from the tags
  def getcookie(self, payload):
    loc = 0
    while(loc < len(payload)):
      att_type = payload[loc:loc+2]
      att_len = (256 * ord(payload[loc+2:loc+3])) + ord(payload[loc+3:loc+4])
      print "Got attribute " + str(ord(att_type[:1])).zfill(2) + str(ord(att_type[1:])).zfill(2)  + " of length " + str(att_len) + " value " + payload[loc+4:loc+4+att_len]
      if att_type == "\x01\x04":
        self.ac_cookie = payload[loc+4:loc+4+att_len]
        print "Got AC-Cookie of " + self.ac_cookie
        break
      loc = loc + att_len + 4
# Define possible states
  @ATMT.state(initial=1)
  def START(self):
    pass
  @ATMT.state()
  def WAIT_PADO(self):
    pass
  @ATMT.state()
  def GOT_PADO(self):
    pass
  @ATMT.state()
  def WAIT_PADS(self):
    pass
  @ATMT.state(error=1)
  def ERROR(self):
    pass
  @ATMT.state(final=1)
  def END(self):
    pass
# Define transitions
# Transitions from START
  @ATMT.condition(START)
  def send_padi(self):
    print "Send PADI"
    sendp(Ether(src=self.mac, dst="ff:ff:ff:ff:ff:ff")/PPPoED()/Raw(load='\x01\x01\x00\x00'+'\x01\x03\x00\x04'+self.hu),iface=self.outif)
    raise self.WAIT_PADO()
# Transitions from WAIT_PADO
  @ATMT.timeout(WAIT_PADO, 6)
  def timeout_pado(self):
    print "Timed out waiting for PADO"
    self.retries -= 1
    if(self.retries < 0):
      print "Too many retries, aborting."
      raise self.ERROR()
    raise self.START()
  @ATMT.receive_condition(WAIT_PADO)
  def receive_pado(self,pkt):
    if (PPPoED in pkt) and (pkt[PPPoED].code==7):
      print "Received PADO"
      self.ac_mac=pkt[Ether].src
      self.getcookie(pkt[Raw].load)
      raise self.GOT_PADO()
#
# Transitions from GOT_PADO
  @ATMT.condition(GOT_PADO)
  def send_padr(self):
    print "Send PADR"
    if(self.randomcookie):
      print "Random cookie being used"
      self.ac_cookie=os.urandom(16)
    sendp(Ether(src=self.mac, dst=self.ac_mac)/PPPoED(code=25)/Raw(load='\x01\x01\x00\x00'+'\x01\x03\x00\x04'+self.hu+'\x01\x04\x00'+chr(len(self.ac_cookie))+self.ac_cookie),iface=self.outif)
    raise self.WAIT_PADS()
#
# Transitions from WAIT_PADS
  @ATMT.timeout(WAIT_PADS, 1)
  def timeout_pads(self):
    print "Timed out waiting for PADS"
    self.retries -= 1
    if(self.retries < 0):
      print "Too many retries, aborting."
      raise self.ERROR()
    raise self.GOT_PADO()
  @ATMT.receive_condition(WAIT_PADS)
  def receive_pads(self,pkt):
    if (PPPoED in pkt) and (pkt[PPPoED].code==101):
      print "Received PADS"
      self.sess_id = pkt[PPPoED].sessionid
      raise self.END()
  @ATMT.receive_condition(WAIT_PADS)
  def receive_padt(self,pkt):
    if (PPPoED in pkt) and (pkt[PPPoED].code==167):
      print "Received PADT"
      raise self.ERROR()



p=PPPoESession()
p.run()

