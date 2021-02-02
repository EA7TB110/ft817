///////////////////////////////////////////////////////
//                                                   //
//     CI-V ICOM CAT TRANSLATOR FOR USE WITH         //
//          70 Mhz to 28 Mhz Transverters            //
//               & Power Amplifiers                  //
//                by ON7EQ 03/2016                   //
//                                                   //
///////////////////////////////////////////////////////

// compiled with IDE v 1.6.8

// see http://www.plicht.de/ekki/civ/index.html  for in depth explanation about CI-V

#include "SoftwareSerial.h"

// On arduino NANO pins 2 and 3 are interrupt capable --> use for RX lines !

// Declare CAT port to transceiver / control PC

#define TRX_RX  (2)
#define TRX_TX  (4)

// Declare CAT port to  PA

#define PA_RX   (3) // but PA is TX only ....
#define PA_TX   (5)


SoftwareSerial DebugSerial (0, 1);

SoftwareSerial CATserialTRX (TRX_RX, TRX_TX);
// Use pins 2 and 4 to talk to the CAT of TRX. 2 is the RX pin, 4 is the TX pin
// Connect the RX pin to the CAT output through a 4k7 resistor.


// Declare CAT port to PC, ATU, Power Amp, ..

SoftwareSerial CATserialPA (PA_RX, PA_TX);
// Use pins 3 and 5 to talk to the CAT of PA. 3 is the RX pin, 5 is the TX pin
// Connect the RX pin to the CAT output through a 4k7 resistor.


#include <LiquidCrystal.h>

// initialize the library with the numbers of the interface pins
// LiquidCrystal connect LCD display (rs, enable, d4, d5, d6, d7)  & connect rw of LCD to ground

LiquidCrystal lcd(12, 11, 10, 9, 8, 7);

////////////////////////////////////////////
////////// DEFINE KEY VARIABLES  ///////////
////////////////////////////////////////////

int cat_TRX_baud = 9600;               // TRX CAT baud set
int cat_PA_baud =  9600;               // PA CAT baud set
int DebugBaud =   38400;               // Debug Baud set

#define TRX_address   (122)            // 122 = HEX $7A = IC-7600
#define PROXY_address (102)            // 102 = HEX $66 = IC-746Pro / IC-7400

#define XVRTER_band    (112)           // 112 = $70 Mhz
#define XVRTER_band_m1 (105)           // 105 = $69 MHz - minus one
#define XVRTER_band_p1 (113)           // 113 = $71 MHz - plus one

#define IF_band  (40)                  // 40 = $28 MHz
#define IF_band_m1  (39)               // 39 = $27 MHz  - minus one
#define IF_band_p1  (41)               // 40 = $29 MHz  - plus one

#define RelayOutPin  (6)               // Relay output pin. H = XVERTER active , relay is energized

#define BeepPin  (A2)                   // Define output pin for BEEPER.  2.4 kHz beeper type SATG1205 for example

#define XVRTERpin (A0)                 //  Low = XVERTER active:  Use as 'hardware' indfication of Xverter active
#define Debugpin  (A1)                 //  Low = DEBUG  select  (--> monitor out on COM port)

// Remark: Pin 13 & on board LED = used to show data on CI-V line. (flashing when data is detected)


// Some standard Icom CI-V CAT addresses, do not alter !

byte all_TRX_address = 0;              // $00 = multicast address to all TRX listening on CAT line, this is 'CI-V transceiver mode'
byte PC_address = 224;                 // $E0 = address of PC controlling


/// SOME OTHER VARIABLES

byte TRVTRmode_HW = 0;                 // Transverter mode initiated by hardware line : 0 = OFF / 1 = Xverter ON
byte TRVTRmode_CAT = 0;                 // Transverter mode initiated by CAT command : 0 = OFF / 1 = Xverter ON

byte Overflow = 0;                     // Overflow flag

byte DEBUG = 0;                        // If no DEBUG mode, no output monitoring on RS-232

// For maximum performance, only run DEBUG mode when required !

byte beep1 = 0;                        // Beep alarm
byte beep2 = 0;                        // Beep alarm

byte Freq_command = 0; 
byte Mode_command = 0; 

int i;
int j;

int incomingTRX;                       //incoming character on TRX side
int incomingPC;                        //incoming character on PC side

int buffget_CATtrx[63] ;               // the receive buffer on TRX end
int buffget_CATpc[63] ;                // the receive buffer on PC end
int mem_freq_byte[15] ;                // the frequency bytes memory
int mem_mode_byte[15] ;                // the frequency bytes memory

int buffget_CATtrx_check[5];           // the receive buffer on TRX end for OK/NG response

long  lastCatTRX = 0;
long  lastCatPC = 0;

byte NoCat = 0;

int unsigned long l00_MHZ = 0;
int unsigned long MHZ = 0;
int unsigned long KHZ = 0;
int unsigned long HZ = 0;
int unsigned long QRG = 0;

int unsigned long catTime = 0;
int unsigned long TRXcatTime = 0;

byte heart [8] = {                    // build special character for 'heartbeat' indication
  B00000,
  B00000,
  B11011,
  B10101,
  B10001,
  B01010,
  B00100,

};

////////////////////////////////////////////////////////////
////////////////////   S E T U P  //////////////////////////
////////////////////////////////////////////////////////////


void setup() {

  // Check if DEBUG mode

  digitalWrite(Debugpin, HIGH);          // activate pull-up

  if (analogRead (Debugpin) > 512) {
    DEBUG = 0;
  }

  else        {
    DEBUG  = 1;
  }


  if (DEBUG == 1) DebugSerial.begin(DebugBaud);   // debug

  CATserialTRX.begin(cat_TRX_baud);
  CATserialPA.begin(cat_PA_baud);

  pinMode (BeepPin, OUTPUT);
  digitalWrite(BeepPin, LOW);
  tone (BeepPin, 2400, 200);

  // set up the LCD's number of columns and rows:
  lcd.begin(16, 2);
  lcd.clear();

  // Print a message to the LCD.

  lcd.print("ON7EQ v4");
  lcd.setCursor(0, 1);
  lcd.print("CATproxy");

  delay (1000);
  lcd.clear();
  lcd.print("lsn $");
  if (PROXY_address < 10) lcd.print("0");
  lcd.print(PROXY_address , HEX);
  lcd.setCursor(0, 1);
  lcd.print("snd $");
  if (TRX_address < 10) lcd.print("0");
  lcd.print(TRX_address , HEX);
  delay (3000);
  lcd.clear();

  if ( DEBUG  == 1)  {
    lcd.print("  DEBUG ");
    lcd.setCursor(0, 1);
    lcd.print("Ser ");
    if (DebugBaud == 9600) lcd.print("9k6");
    if (DebugBaud == 19200) lcd.print("19k2");
    if (DebugBaud == 38400) lcd.print("38k4");
    delay (3000);
  }

  pinMode(13, OUTPUT);

  pinMode(RelayOutPin, OUTPUT);
  digitalWrite(RelayOutPin, LOW);

  digitalWrite(TRX_TX, HIGH);          // activate pull-up
  digitalWrite(PA_TX, HIGH);           // activate pull-up
  
  digitalWrite(XVRTERpin, HIGH);       // activate pull-up


  // LISTEN on TRX port

  CATserialTRX.listen();  // declare the TRX port to listen,  buffer is as well flushed

  if (DEBUG == 1 ) {
    DebugSerial.println ("");
    DebugSerial.println ("********** PROXY CI-V *************");
    DebugSerial.println ("");
    DebugSerial.print ("Listening for PC on $");
    if (PROXY_address < 10) DebugSerial.print ("0");
    DebugSerial.println(PROXY_address , HEX);
    DebugSerial.print ("Sending to TRX on   $");
    if (TRX_address < 10) DebugSerial.print ("0");
    DebugSerial.println(TRX_address , HEX);
    DebugSerial.println ("");
    DebugSerial.println ("********** PROXY CI-V *************");
    DebugSerial.println ("");
    DebugSerial.println ("");
    delay (2000);
    while (CATserialTRX.available()) CATserialTRX.read(); // clean buffer
  }

  // create special character heartbeat

  lcd.createChar(1, heart);
  lcd.setCursor (4, 0);
  lcd.write (1);

  catTime = millis() ;      // reset timer
  TRXcatTime = millis();    // reset timer

  while (CATserialTRX.available()) CATserialTRX.read(); // clean buffer
}

///////////////////////////////////////////
////////////  L   O   O  P  ///////////////
///////////////////////////////////////////


void loop() {

  // Check if DEBUG mode

  if (analogRead (Debugpin) > 512) {
    DEBUG = 0;
  }

  else        {
    DEBUG  = 1;
  }

  // Check if XVERTER enabled by HW line

  if (analogRead (XVRTERpin) < 512)  {    //Yes
    if (TRVTRmode_HW == 0) {
      tone(BeepPin, 2000, 20);
      delay(60);
      tone(BeepPin, 2500, 20);
    }
    TRVTRmode_HW = 1;
  }
  else {                                  // No
    if (TRVTRmode_HW == 1)  {
      tone(BeepPin, 2500, 20);
      delay(60);
      tone(BeepPin, 2000, 20);
    }
    TRVTRmode_HW = 0;
  }

  lcd.setCursor(0, 0);

  if ((TRVTRmode_HW == 1) or (TRVTRmode_CAT == 1)) {
    lcd.print("XVTR");
    digitalWrite(RelayOutPin, HIGH);
  }
  else {
    lcd.print("Norm");
    digitalWrite(RelayOutPin, LOW);
  }

  //-------------------------------------------------------------------
CAT_TRX_next:           // CAT TRX is CAT line for commands to/from TRX
  //-------------------------------------------------------------------

  if ((millis() - catTime) > 5000) {
    NoCat = 1;
    lcd.setCursor(0, 0);
    lcd.print(" NO CAT ");
    lcd.setCursor(0, 1);
    lcd.print("SIGNAL !");
    digitalWrite(RelayOutPin, LOW);
    if (beep1 == 0) {
      beep1 = 1;
      tone (BeepPin, 2400, 10);
    }

  }
  else if ((millis() - TRXcatTime) > 8000) {
    lcd.setCursor(0, 0);
    lcd.print("NO REPLY");
    lcd.setCursor(0, 1);
    lcd.print("FROM TRX");
    digitalWrite(RelayOutPin, LOW);
    if (beep2 == 0) {
      beep2 = 1;
      tone (BeepPin, 2200, 30);
      delay(100);
      tone (BeepPin, 2400, 30);
      delay(100);
      tone (BeepPin, 2600, 30);
    }
  }

  else {NoCat = 0; }
  
  // START OF DATAGRAM CAPTURE

  if (CATserialTRX.available() > 0) {          // There are bytes available in the buffer ?



    if (CATserialTRX.overflow()) {             // indicate overflow in DEBUG mode
      if (DEBUG == 1 )DebugSerial.println(">>>>>>>>>  SoftwareSerial overflow !!!");
      while (CATserialTRX.available()) CATserialTRX.read(); // clean buffer
    }


    incomingTRX = CATserialTRX.read();

    if ((incomingTRX == 254)   ) {            // look for an FE = start of CAT sequence , no overflow (mutilated string ?)
      goto CAT_TRX_start;                     // it is possibly a start !
    }
  }

  delay (1);  // allow buffer to fill


  goto CAT_TRX_next;                         // no specific byte received, so keep monitoring buffer

  //-------------------------------------------------------------------
CAT_TRX_start:                                   // 1st byte was a 254
  //-------------------------------------------------------------------

  delay (20);                                     // delay is required to allow buffer to fill : too low = buffer not filled ! Too high = not smooth response

  for ( i = 0; i < 10; i++) {                     // search for end,  9 bytes is the longest datagram

    if (CATserialTRX.available() > 0) {           // there is dat in buffer !

      buffget_CATtrx[i] = CATserialTRX.read();     // load buffget with next characters

      String byte_string = String(buffget_CATtrx[i], HEX);

      // Sniffer !

      if (DEBUG == 1 )  {
        if (buffget_CATtrx[i] < 10) DebugSerial.print ("0");  // format Serial monitor print
        DebugSerial.print (byte_string);
        DebugSerial.print (" ");
      }
      if (buffget_CATtrx[i] ==  253   ) {
        if (DEBUG == 1) DebugSerial.println ("");
        goto process_string_TRX;
      }                                           // end of string detected

      delay( 1 );                                 //delay 1 ms if true, leave time for buffer to work
    }
  }

  goto CAT_TRX_start;                             // it is possibly a start !


  //-------------------------------------------------------------------
process_string_TRX:                   // Process the string on TRX line
  //-------------------------------------------------------------------

  catTime = millis();                    // Reset timestamp CAT data received
  beep1 = 0;

  if ((buffget_CATtrx[0] == 254)) {      // is the 2nd character again an FE ?

    goto valid_string_TRX;               // yes, now process string !
  }


  goto CAT_TRX_next;                     // no, capture another CAT string !

  //-------------------------------------------------------------------
valid_string_TRX:                    // Process the string on TRX line
  //-------------------------------------------------------------------


  if (DEBUG == 1 ) DebugSerial.println (""); // CR  on serial sniffer

  digitalWrite(13, HIGH);
  lcd.setCursor(4, 0);
  lcd.write(1);

  ////////////////////////////////////////////////////////////////////
  ///////// Case : Command string  from PC to PROXY/TRX
  ////////////////////////////////////////////////////////////////////

  // --> check origin & destination of datagram  !

  if ((buffget_CATtrx[1] == PROXY_address) and  ( buffget_CATtrx[2] ==  PC_address )  )   {   // to proxy address  from PC

    NoCat = 0; // clear CAT alert

    /////////////// check command $03 or $04 = read frequency or mode

    if ((buffget_CATtrx[3] == 3) or (buffget_CATtrx[3] == 4)) {

      // translate on CAT line
      //CATserialTRX.flush();  
      delay (20);
      digitalWrite(13, LOW);
      lcd.setCursor(4, 0);
      lcd.write (1);


      // DEBUG

      if (DEBUG == 1 ) {
        //DebugSerial.println ("  ");
        DebugSerial.print ("read ");
        if (buffget_CATtrx[3] == 3) DebugSerial.print ("freq ");
        if (buffget_CATtrx[3] == 4) DebugSerial.print ("mode ");
        DebugSerial.print ("command (PROXY --> TRX) :  ");
        DebugSerial.print("FE FE ");  // $FE
        DebugSerial.print(TRX_address, DEC);
        DebugSerial.print(" ");
        DebugSerial.print(PC_address, DEC);
        DebugSerial.print(" ");
        DebugSerial.print(buffget_CATtrx[3], DEC);
        DebugSerial.print(" ");
        DebugSerial.print("FD");   // $FD
        DebugSerial.println(" ");
        DebugSerial.println(" ");
      }
      // retransmit  and change destination address to physical address TRX

      CATserialTRX.write(254);  // $FE
      CATserialTRX.write(254);
      CATserialTRX.write(TRX_address);
      CATserialTRX.write(PC_address);
      CATserialTRX.write(buffget_CATtrx[3]);
      CATserialTRX.write(253);   // $FD

    }

    /////////////// check command $00 or $05 as 5th byte in datagram = set frequency

    if (((buffget_CATtrx[3] == 0) or (buffget_CATtrx[3] == 5)) and (buffget_CATtrx[8] == 0)  ) {  // CATtrx[8] == 0 because no QSY possible if QRG > 100 Mhz

     Freq_command = 1;
                        
          mem_freq_byte[5] = buffget_CATtrx[5] ;          // put bytes in memory
          mem_freq_byte[6] = buffget_CATtrx[6] ;
          mem_freq_byte[7] = buffget_CATtrx[7] ;               
            
      //
      // Check if Tranverter must be ON

      // Must be switched on

      if ((buffget_CATtrx[7] ==  XVRTER_band_m1) or  (buffget_CATtrx[7] ==  XVRTER_band)  or (buffget_CATtrx[7] ==  XVRTER_band_p1)) {

        if (TRVTRmode_CAT == 0) {
          tone(BeepPin, 2000, 20);
          delay(40);
          tone(BeepPin, 2500, 20);
          //CATserialTRX.flush();  
          delay(20);
          TRVTRmode_CAT = 1;
          CATserialTRX.write(254);        // $FE
          CATserialTRX.write(254);
          CATserialTRX.write(TRX_address);
          CATserialTRX.write(PC_address);
          CATserialTRX.write(26);         // $1A
          CATserialTRX.write(05);         // $05
          CATserialTRX.write((byte)00);
          CATserialTRX.write(113);        // $71
          CATserialTRX.write(01);         // $01  command to set XVERTER ON
          CATserialTRX.write(253);        // $FD
        }
      }

      // Must be switched off

      else {
        if (TRVTRmode_CAT == 1) {
          tone(BeepPin, 2500, 20);
          delay(40);
          tone(BeepPin, 2000, 20);
          delay(20);
          TRVTRmode_CAT = 0;

          CATserialTRX.write(254);              // $FE
          CATserialTRX.write(254);
          CATserialTRX.write(TRX_address);
          CATserialTRX.write(PC_address);
          CATserialTRX.write(26);               // $1A
          CATserialTRX.write(05);               // $05
          CATserialTRX.write((byte)00);
          CATserialTRX.write(113);              // $71
          CATserialTRX.write((byte)00);         // command to set XVERTER in AUTO mode
          CATserialTRX.write(253);              // $FD
        }
      }

      delay (5);
      digitalWrite(13, LOW);
      lcd.setCursor(4, 0);
      lcd.write (1);

      // DEBUG

      if (DEBUG == 1 ) {
       
        DebugSerial.print ("set frequency command (PROXY --> TRX) :  ");
        DebugSerial.print("FE FE ");  // $FE
        DebugSerial.print(TRX_address, DEC);
        DebugSerial.print(" ");
        DebugSerial.print(PC_address, DEC);
        DebugSerial.print(" ");
        DebugSerial.print(buffget_CATtrx[3], DEC);
        DebugSerial.print(" ");
        DebugSerial.print(buffget_CATtrx[4], DEC);
        DebugSerial.print(" ");
        DebugSerial.print(buffget_CATtrx[5], DEC);
        DebugSerial.print(" ");
        DebugSerial.print(buffget_CATtrx[6], DEC);
        DebugSerial.print(" ");
        DebugSerial.print(buffget_CATtrx[7], HEX);
        DebugSerial.print(" ");
        DebugSerial.print(buffget_CATtrx[8], DEC);
        DebugSerial.print(" ");
        DebugSerial.print("FD");   // $FD
        DebugSerial.println(" ");
        DebugSerial.println(" ");
      }

      // retransmit  and change destination address to physical address TRX
      
      delay(20); 
      CATserialTRX.write(254);  // $FE
      CATserialTRX.write(254);
      CATserialTRX.write(TRX_address);
      CATserialTRX.write(PC_address);

      // 3 possible bytes :
      //CATserialTRX.write((byte)00);           // Set Frequency Command with no reply
      CATserialTRX.write((byte)05);             // Set Frequency Command with reply
      //CATserialTRX.write(buffget_CATtrx[3]);  // Repeat original byte

      CATserialTRX.write((byte)00);             // Assume precision up to 100 Hz, no more required
      //CATserialTRX.write(buffget_CATtrx[4]);

      CATserialTRX.write(buffget_CATtrx[5]);
      CATserialTRX.write(buffget_CATtrx[6]);

      if ((TRVTRmode_HW == 1) or (TRVTRmode_CAT == 1)) {      // 70 MHz Xverter is active !

        if      (buffget_CATtrx[7] ==  XVRTER_band_m1) CATserialTRX.write(IF_band_m1);    // 69 MHz
        else if (buffget_CATtrx[7] ==  XVRTER_band)    CATserialTRX.write(IF_band);       // 70 MHz
        else if (buffget_CATtrx[7] ==  XVRTER_band_p1) CATserialTRX.write(IF_band_p1);    // 71 MHz
        else    (CATserialTRX.write(153));          // If Xverter active, and not 69/70/71 MHz, send 99 Mhz = frequency setting not accepted !
      }

      else  {
        CATserialTRX.write(buffget_CATtrx[7]);       // No Xverter active !
      }

      CATserialTRX.write((byte)00);                  // frequency is always < 100 MHz
      CATserialTRX.write(253);                       // $FD
      } 
      // end set frequency command
    

    //////////////// check command $01 or $06 = set mode & filter

    if ((buffget_CATtrx[3] == 1) or (buffget_CATtrx[3] == 6)) {
            
      // translate on CAT line
      
      delay (20);
      digitalWrite(13, LOW);
      lcd.setCursor(4, 0);
      lcd.write (1);

      // retransmit  and change destination address to physical address TRX

      CATserialTRX.write(254);          // $FE
      CATserialTRX.write(254);
      CATserialTRX.write(TRX_address);
      CATserialTRX.write(PC_address);
      
      // 2 possible bytes :
      CATserialTRX.write(01);           //  $01 for 3rd byte, no response required
      //CATserialTRX.write(buffget_CATtrx[3]);
      
      CATserialTRX.write(buffget_CATtrx[4]);
      CATserialTRX.write(buffget_CATtrx[5]);
      if (buffget_CATtrx[6] != 253) CATserialTRX.write(buffget_CATtrx[6]);  //possibly byte for filter width setting

      CATserialTRX.write(253);         // $FD

    } // end command set mode & filter

  }

  ////////////////////////////////////////////////////////////////////
  ///////// Case : REPLY  from TRX to PC
  ////////////////////////////////////////////////////////////////////

  // --> check origin & destination of datagram  !


  if (((buffget_CATtrx[1] == PC_address) ) and  ( buffget_CATtrx[2] ==  TRX_address )  )   {   // From TRX to PC Controller

    TRXcatTime = millis ();          //reset timer
    beep2 = 0 ;
    delay (20);
    digitalWrite(13, LOW);
    lcd.setCursor(4, 0);
    lcd.write (1);

   //  Check for confirmation of frequency change received & valid 
   //  if success, response from rig will be : $FE $FE to-adr fm-adr $FB $FD 
   
    if (Freq_command == 1){

    if ((buffget_CATtrx[3] == 251) and (buffget_CATtrx[4] == 253))  { 
            tone (BeepPin, 2400, 5);          // emit beep to confirm QSY request performed
            Freq_command = 0;
            goto parse_next_datagram;
           }

       else  {              // NOK, need to re-issue frequency command 1 time
  
       delay (20);
        
      // Check if Tranverter must be ON

      // Must be switched on

      if ((mem_freq_byte[7] ==  XVRTER_band_m1) or  (mem_freq_byte[7] ==  XVRTER_band)  or (mem_freq_byte[7] ==  XVRTER_band_p1)) {

        if (TRVTRmode_CAT == 0) {
          
          TRVTRmode_CAT = 1;
          CATserialTRX.write(254);          // $FE
          CATserialTRX.write(254);
          CATserialTRX.write(TRX_address);
          CATserialTRX.write(PC_address);
          CATserialTRX.write(26);           // $1A
          CATserialTRX.write(05);           // $05
          CATserialTRX.write((byte)00);
          CATserialTRX.write(113);          // $71
          CATserialTRX.write(01);           // $01  command to set XVERTER ON
          CATserialTRX.write(253);          // $FD
        }
      }

      // Must be switched off

      else {
        if (TRVTRmode_CAT == 1) {
          
          TRVTRmode_CAT = 0;
          CATserialTRX.write(254);          // $FE
          CATserialTRX.write(254);
          CATserialTRX.write(TRX_address);
          CATserialTRX.write(PC_address);
          CATserialTRX.write(26);           // $1A
          CATserialTRX.write(05);           // $05
          CATserialTRX.write((byte)00);
          CATserialTRX.write(113);          // $71
          CATserialTRX.write((byte)00);     // command to set XVERTER in AUTO mode
          CATserialTRX.write(253);          // $FD
        }
      }
      
      // retransmit  and change destination address to physical address TRX
      delay (20);
      CATserialTRX.write(254);              // $FE
      CATserialTRX.write(254);
      CATserialTRX.write(TRX_address);
      CATserialTRX.write(PC_address);

      CATserialTRX.write((byte)00);         // Set Frequency Command with no reply
        // CATserialTRX.write((byte)05);    // Set Frequency Command with reply --> could cause loop !
        //CATserialTRX.write(mem_freq_byte[3]);
      
      CATserialTRX.write((byte)00);         // Assume precision up to 100 Hz, no more required
        //CATserialTRX.write(mem_freq_byte[4]);

      CATserialTRX.write(mem_freq_byte[5]);
      CATserialTRX.write(mem_freq_byte[6]);


      if ((TRVTRmode_HW == 1) or (TRVTRmode_CAT == 1)) {      // 70 MHz Xverter is active !

        if      (mem_freq_byte[7] ==  XVRTER_band_m1) CATserialTRX.write(IF_band_m1);
        else if (mem_freq_byte[7] ==  XVRTER_band)    CATserialTRX.write(IF_band);
        else if (mem_freq_byte[7] ==  XVRTER_band_p1) CATserialTRX.write(IF_band_p1);
        else    (CATserialTRX.write(153));          // If Xverter active, and not 69/70/71 MHz, send 99 Mhz = frequency setting not accepted !
      }

      else  {
            CATserialTRX.write(mem_freq_byte[7]);       // No Xverter active !
            }

      CATserialTRX.write((byte)00);                    // frequency is always < 100 MHz
      CATserialTRX.write(253);                         // $FD
      
      } // end re issue frequency command

  
   } // end confirm OK


parse_next_datagram:   

    ///////// reply to request with frequency info: Bbte 4 must be $03

    if ((buffget_CATtrx[3] == 03)) {

      // DEBUG : serial print

      if (DEBUG == 1 ) {
        DebugSerial.println ("  ");
        DebugSerial.print ("reply (PROXY --> PC) : Frequency =  ");
        DebugSerial.print("FE FE ");  // $FE
        DebugSerial.print(PC_address, DEC);
        DebugSerial.print(" ");
        DebugSerial.print(PROXY_address, DEC);
        DebugSerial.print(" ");
        DebugSerial.print(3, DEC);
        DebugSerial.print(" ");
        DebugSerial.print(buffget_CATtrx[4], DEC);
        DebugSerial.print(" ");
        DebugSerial.print(buffget_CATtrx[5], DEC);
        DebugSerial.print(" ");
        DebugSerial.print(buffget_CATtrx[6], DEC);
        DebugSerial.print(" ");
        DebugSerial.print(buffget_CATtrx[7], DEC);

        DebugSerial.print(" ");
        DebugSerial.print(buffget_CATtrx[8], DEC);
        DebugSerial.print(" ");
        DebugSerial.print("FD");   // $FD
        DebugSerial.println(" ");
        DebugSerial.println(" ");
      }

      // Send freqency info on TRX-PC CAT line
  
      delay(20);
      CATserialTRX.write(254);                  // $FE
      CATserialTRX.write(254);
      CATserialTRX.write(PC_address);
      CATserialTRX.write(PROXY_address);
      CATserialTRX.write(03);                  // Frequency !
      CATserialTRX.write(buffget_CATtrx[4]);
      CATserialTRX.write(buffget_CATtrx[5]);
      CATserialTRX.write(buffget_CATtrx[6]);

      if ((TRVTRmode_HW == 1)  or (TRVTRmode_CAT == 1))  {                           // 70 MHz Xverter
        if (buffget_CATtrx[7] < IF_band_m1)  CATserialTRX.write(153);               // Error : send 99 MHz        
        if (buffget_CATtrx[7] == IF_band_m1)  CATserialTRX.write(XVRTER_band_m1);
        if (buffget_CATtrx[7] == IF_band)     CATserialTRX.write(XVRTER_band);
        if (buffget_CATtrx[7] == IF_band_p1)  CATserialTRX.write(XVRTER_band_p1);
        if (buffget_CATtrx[7] > IF_band_p1)  CATserialTRX.write(153);              // Error : send 99 MHz     
      }

      else       {
        CATserialTRX.write(buffget_CATtrx[7]);   // No Xverter
        }

      CATserialTRX.write(((byte)00));
      CATserialTRX.write(253);         // $FD

 
      /////////////// Send freqency info on PA CAT line, in CI-V mode, originating from TRX

      CATserialPA.write(254);          // $FE
      CATserialPA.write(254);
      CATserialPA.write((byte)00);
      CATserialPA.write(TRX_address);
      CATserialPA.write((byte)00);     // Frequency as CI-V multicast 
      CATserialPA.write(buffget_CATtrx[4]);
      CATserialPA.write(buffget_CATtrx[5]);
      CATserialPA.write(buffget_CATtrx[6]);

      if ((TRVTRmode_HW == 1) or (TRVTRmode_CAT == 1)) {       // 70 MHz Xverter is active
        if (buffget_CATtrx[7] < IF_band_m1)  CATserialPA.write(153);  // error ! send 99 MHz = not permitted
        if (buffget_CATtrx[7] == IF_band_m1)  CATserialPA.write(XVRTER_band);  // always send 70 MHz
        if (buffget_CATtrx[7] == IF_band)     CATserialPA.write(XVRTER_band);
        if (buffget_CATtrx[7] == IF_band_p1)  CATserialPA.write(XVRTER_band);  // always send 70 MHz
        if (buffget_CATtrx[7] > IF_band_p1)  CATserialPA.write(153);  // error ! send 99 MHz = not permitted     
      }
      else  {
        CATserialPA.write(buffget_CATtrx[7]);   // No Xverter
      }

      CATserialPA.write((byte)00);          // frequency always < 100 MHz
      CATserialPA.write(253);               // $FD

      //  PRINT operating QRG on LCD Display

      l00_MHZ = (buffget_CATtrx[8]);                // Will always be zero ....
      l00_MHZ = l00_MHZ - (((l00_MHZ / 16) * 6));   // Transform bytes ICOM CAT


      MHZ = (buffget_CATtrx[7]);
      MHZ = MHZ - (((MHZ / 16) * 6));               // Transform bytes ICOM CAT

      KHZ = buffget_CATtrx[6];
      KHZ = KHZ - (((KHZ / 16) * 6));               // Transform bytes ICOM CAT

      HZ = buffget_CATtrx[5];
      HZ = HZ - (((HZ / 16) * 6));                  // Transform bytes ICOM CAT

      QRG = ((MHZ * 10000) + (KHZ * 100) + (HZ * 1)); // QRG variable stores frequency in MMkkkH  format

      if (NoCat == 1) {   // clear 1 st line
          lcd.setCursor(0, 0);
          lcd.print("        ");
          }
      

      lcd.setCursor(0, 1);

      if ((TRVTRmode_HW == 1) or (TRVTRmode_CAT == 1)) {       // 70 MHz Xverter
        if (buffget_CATtrx[7] < IF_band_m1)  lcd.print("ERR");
        if (buffget_CATtrx[7] == IF_band_m1)  lcd.print(" 69");     
        if (buffget_CATtrx[7] == IF_band) lcd.print(" 70");
        if (buffget_CATtrx[7] == IF_band_p1)  lcd.print(" 71");
        if (buffget_CATtrx[7] > IF_band_p1)  lcd.print("ERR");
      }
      else {
        if (MHZ < 100) lcd.print(" ");
        if (MHZ < 10)  lcd.print(" ");
        lcd.print(MHZ, DEC);
      }

      lcd.print(".");

      if (KHZ < 10)  lcd.print("0");
      lcd.print(KHZ, DEC);

      if (HZ < 10)  lcd.print("0");
      lcd.print(HZ, DEC);


    }     // end of frequency info

    // mode info: Byte 4 must be $04

    if ((buffget_CATtrx[3] == 4)) {
      //CATserialTRX.flush();  
      delay(20);
      CATserialTRX.write(254);  // $FE
      CATserialTRX.write(254);
      CATserialTRX.write(PC_address);
      CATserialTRX.write(PROXY_address);
      CATserialTRX.write(4);  // Mode !
      CATserialTRX.write(buffget_CATtrx[4]);
      CATserialTRX.write(253);   // $FD

      lcd.setCursor(5, 0);
      if      (buffget_CATtrx[4] == 00 )  lcd.print("LSB");
      else if (buffget_CATtrx[4] == 01 )  lcd.print("USB");
      else if (buffget_CATtrx[4] == 02 )  lcd.print("AM ");
      else if (buffget_CATtrx[4] == 03 )  lcd.print("CW ");
      else if (buffget_CATtrx[4] == 04 )  lcd.print("FSK");
      else if (buffget_CATtrx[4] == 05 )  lcd.print("FM ");
      else if (buffget_CATtrx[4] == 06 )  lcd.print("CWR");
      else lcd.print(" - ");

      //heartbeat
      lcd.setCursor (4, 0);
      lcd.print(" ");


    } // End mode filter info

  } // end datagram From TRX to PC Controller


  // CI-V 'transceive mode' in multicast

  if ((buffget_CATtrx[1] == 0)  and  (buffget_CATtrx[2] ==  TRX_address ) and  (buffget_CATtrx[3] == 0)) {    // Frequency info to ALL from Transceiver

    TRXcatTime = millis ();  //reset timer

    // translate address to :  To PC from proxy

    delay (20);  // allow PC to receive data
    digitalWrite(13, LOW);
    lcd.setCursor(4, 0);
    lcd.write (1);

    CATserialTRX.write(254);  // $FE
    CATserialTRX.write(254);
    CATserialTRX.write(PC_address);
    // CATserialTRX.write((byte)00);          // Address to all in CI-V multicast : not recommended !
    CATserialTRX.write(PROXY_address);
    CATserialTRX.write(3);  // frequency info
    // CATserialTRX.write((byte)00);          // Frequency in CI-V multicast : not recommended !
    CATserialTRX.write(buffget_CATtrx[4]);
    CATserialTRX.write(buffget_CATtrx[5]);
    CATserialTRX.write(buffget_CATtrx[6]);

    if ((TRVTRmode_HW == 1) or (TRVTRmode_CAT == 1)) {       // 70 MHz Xverter active
        if (buffget_CATtrx[7] < IF_band_m1)  CATserialTRX.write(153); // Error : send 99 MHz        
        if (buffget_CATtrx[7] == IF_band_m1)  CATserialTRX.write(XVRTER_band_m1);
        if (buffget_CATtrx[7] == IF_band)     CATserialTRX.write(XVRTER_band);
        if (buffget_CATtrx[7] == IF_band_p1)  CATserialTRX.write(XVRTER_band_p1);
        if (buffget_CATtrx[7] > IF_band_p1)  CATserialTRX.write(153);  // Error : send 99 MHz 
    }
    else           {
      CATserialTRX.write(buffget_CATtrx[7]); // No Xverter
    }

    CATserialTRX.write((byte)00); // always < 100 MHz
    CATserialTRX.write(253);   // $FD


// Send freqency info on PA CAT line, in CI-V mode, originating from TRX

      CATserialPA.write(254);  // $FE
      CATserialPA.write(254);
      CATserialPA.write((byte)00);
      CATserialPA.write(TRX_address);
      CATserialPA.write((byte)00);  // Frequency as CI-V multicast to all!
      CATserialPA.write(buffget_CATtrx[4]);
      CATserialPA.write(buffget_CATtrx[5]);
      CATserialPA.write(buffget_CATtrx[6]);

      if ((TRVTRmode_HW == 1) or (TRVTRmode_CAT == 1)) {       // 70 MHz Xverter is active
        if (buffget_CATtrx[7] < IF_band_m1)  CATserialPA.write(153);  // error ! send 99 MHz = not permitted
        if (buffget_CATtrx[7] == IF_band_m1)  CATserialPA.write(XVRTER_band);  // always send 70 MHz
        if (buffget_CATtrx[7] == IF_band)     CATserialPA.write(XVRTER_band);
        if (buffget_CATtrx[7] == IF_band_p1)  CATserialPA.write(XVRTER_band);  // always send 70 MHz
        if (buffget_CATtrx[7] > IF_band_p1)  CATserialPA.write(153);  // error ! send 99 MHz = not permitted 
      }
      else  {
        CATserialPA.write(buffget_CATtrx[7]);   // No Xverter
      }

      CATserialPA.write((byte)00);          // frequency always < 100 MHz
      CATserialPA.write(253);               // $FD

   

  //  PRINT operating QRG on LCD display

    l00_MHZ = (buffget_CATtrx[8]);
    l00_MHZ = l00_MHZ - (((l00_MHZ / 16) * 6));   // Transform bytes ICOM CAT

    MHZ = (buffget_CATtrx[7]);
    MHZ = MHZ - (((MHZ / 16) * 6));               // Transform bytes ICOM CAT

    KHZ = buffget_CATtrx[6];
    KHZ = KHZ - (((KHZ / 16) * 6));               // Transform bytes ICOM CAT

    HZ = buffget_CATtrx[5];
    HZ = HZ - (((HZ / 16) * 6));                  // Transform bytes ICOM CAT

    QRG = ((MHZ * 10000) + (KHZ * 100) + (HZ * 1)); // QRG variable stores frequency in MMkkkH  format

    if (NoCat == 1) {   // clear 1 st line
          lcd.setCursor(0, 0);
          lcd.print("        ");
          }
    
    lcd.setCursor(0, 1);

    if ((TRVTRmode_HW == 1) or (TRVTRmode_CAT == 1)) {       // 70 MHz Xverter active
      if (buffget_CATtrx[7] < IF_band_m1)   lcd.print("ERR");
      if (buffget_CATtrx[7] == IF_band_m1)  lcd.print(" 69");     
      if (buffget_CATtrx[7] == IF_band)     lcd.print(" 70");
      if (buffget_CATtrx[7] == IF_band_p1)  lcd.print(" 71");
      if (buffget_CATtrx[7] > IF_band_p1)   lcd.print("ERR");
    }
    else   {
      if (MHZ < 100) lcd.print(" ");
      if (MHZ < 10)  lcd.print(" ");
      lcd.print(MHZ, DEC);
    }

    lcd.print(".");

    if (KHZ < 10)  lcd.print("0");
    lcd.print(KHZ, DEC);

    if (HZ < 10)  lcd.print("0");
    lcd.print(HZ, DEC);

    CATserialTRX.flush();                                 // Wait till TX buffer is flushed
    while (CATserialTRX.available()) CATserialTRX.read(); // clear RX buffer, no process of own transmission !!!

    lcd.setCursor(4, 0);
    lcd.print(" ");

  } //end of CI-V 'transceive mode' in multicast


} // End of loop

