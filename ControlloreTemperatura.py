'''
Created on 19 nov 2020

@author: Martin Andrea
'''

from pyb import delay,Pin, Timer
from utime import ticks_ms,ticks_diff
from machine import SoftI2C, WDT
import onewire
import ds18x20
import ssd1306
from DisplayOledUtility import move_center_text, center_text,power_bar
import Menu2
import MartinTempUtils as util

ControllerTemp = '1.0.0'

wdt = WDT(timeout=3000) #abilitato il watchdog a 3 secondi

def Presentazione(ssd,time): #presentazione iniziale
    ssd.fill(0) #cancella tutto lo schemo...
    ssd.show()# .. e poi mastralo!
    move_center_text(ssd, text='Controllore',y=5) #muovi frase 1
    move_center_text(ssd, text='Temperatura',y=20) #movi frase2 
    move_center_text(ssd, text='Ver:{}'.format(ControllerTemp),y=45)# muovi frase 3
    oled.show()# mostra uttto
    delay(time) #aspetta tot tempo poi esci

def DatiInDisplay1(ssd,set_T,read_T,powpr,ch,war_Pow=''):
    ssd.text('Set T{}: {} C'.format(ch,set_T),0,5)
    ssd.text('Temp {}: {:0.1f} C'.format(ch,read_T),0,30)
    if war_Pow == 'ToHi' or war_Pow == 'ToLo':
        ssd.text('Pow{} {} {}%'.format(ch,war_Pow,powpr),0,50)
    else:
        power_bar(ssd=oled,text='Pw{} {}%:'.format(ch,powpr), val=powpr,y=50)#aggiunge barra di potenza
    ssd.show()

def DatiInDisplay2(ssd,set_T1,read_T1,pow1,set_T2,read_T2,pow2):
    ssd.text('Set T1: {} C'.format(set_T1),0,0)
    ssd.text('Temp1 : {:0.1f} C'.format(read_T1),0,10)
    power_bar(ssd=oled,text='Pw1 {}%:'.format(pow1), val=pow1,y=19)#aggiunge barra di potenza
    ssd.text('Set T2: {} C'.format(set_T2),0,36)
    ssd.text('Temp2 : {:0.1f} C'.format(read_T2),0,46)
    power_bar(ssd=oled,text='Pw2 {}%:'.format(pow1), val=pow2,y=55)#aggiunge barra di potenza
    ssd.show()
    
def UnsafePower(powList): #funzione calcolo potenza critica
    if powList[-2] > 90:
        warning = "ToLo"
    elif powList[-2] < 10:
        warning = "ToHi"
    else:
        warning =""
    return warning

def CalcoloTempPercent(set_temp,modalita,perc_val=1.5):#fx calcolo intervallo temperatura percento
    if modalita == 0:# se 0 = modalita inferiore
        percent_temp = set_temp-(set_temp*perc_val)/100
    elif modalita ==1:#se 1 = modalita superiore
        percent_temp = set_temp+(set_temp*perc_val)/100
    return percent_temp

def ConversioneTempoAttesa(minuti):
    return (minuti*60)/5
    
def ControlloSensori(sensInit,ssd):
    ssd.fill(0)# cancella lo schermo
    sensori = sensInit.scan()#creca i sensori
    numeroSensori = len(sensori)#controlla la lista 2sensori" e vedi quanti elementi ci sono
    if numeroSensori == 0:# se non ce nessun sensore collegato..
        center_text(ssd=oled,text='Nessun Sensore',y=25)# scrivi che non ci sono.
        ssd.show()# e mostra il messaggio
        return (False,0,0)# torna False (0,0 son li perche devo essere 3 elementi)
    elif numeroSensori >=1:# se invece ci son 1 o più sensori
        sensInit.convert_temp()# indica di converti in gradi celsious
        Read_Sens = round(sensInit.read_temp(sensori[0]),1)# legge il primo valore della lista
        #print ('Ora ce ne 1',Read_Sens)
        return (True,numeroSensori,Read_Sens)# ritorna True numero dei sensori e la lettura

# ------ Inizializa parametri ----------------------------
setTemp1 = 20.0
setTemp2 = 15.5
configJ = util.Read_Config(name='TempControl.conf',setTemp1=setTemp1,setTemp2=setTemp2)
setTemp1 = configJ['setTemp1']
setTemp2 = configJ['setTemp2']

# ------ Inizializza Pulsanti ----------------------------
pulS1 = Pin('Y3', Pin.IN)
pulS2 = Pin('Y4', Pin.IN)
pulS3 = Pin('Y5', Pin.IN)
pulS4 = Pin('Y6', Pin.IN)

# ------ Inizializza Ingressi ----------------------------
inG1 = Pin('Y8', Pin.IN , Pin.PULL_UP) #bit verifica sonda in Ch1 (0= coolegata)
inG2 = Pin('X9', Pin.IN , Pin.PULL_UP) #bit verifica sonda in Ch2 (0= coolegata)

# ------ Inizializazio Uscite Potenza --------------------
timerSys = pyb.Timer(8, freq=0.2)#attiva il ch8 con freq 0.2hz
exitPot1 = timerSys.channel(1, Timer.PWM, pin=pyb.Pin.board.Y1, pulse_width=0)#attiva ch2 di tim 8
exitPot2 = timerSys.channel(2, Timer.PWM, pin=pyb.Pin.board.Y2, pulse_width=0)#attiva ch2 di tim 8

# ------ Inizializza DXisplay -----------------------------
i2c = machine.SoftI2C(scl=Pin('Y10'), sda=Pin('Y9'),timeout=255)#i2c1 pyboard
oled = ssd1306.SSD1306_I2C(128, 64, i2c, 0x3c)

# ------ Inizializza Sensore Temperatura -----------------
ow = onewire.OneWire(Pin('Y7'))
sensInit = ds18x20.DS18X20(ow)

# ------ presentazione iniziale --------------------------
Presentazione(ssd=oled,time=3000)
print('Ver Controller: {} Ver MartinLib: {}'.format(ControllerTemp,util.MartinTempUtils))

flagSensInit = False #flag per tenere traccia se ci sono o no sensori
while flagSensInit == False:# contollo iniziale dei sensori
    flagSensInit,numSens,tempSens = ControlloSensori(sensInit,ssd=oled)
    #print(flagSensInit,numSens)
    delay(400)

if numSens == 1:
    oled.fill(0)# cancella display
    tempoLetturaSens = ticks_ms()#inizializa tempo ciclo lettrura sensore
    flagTempUp = False #flag per evitare che si decrementi piu volte quando temp sopra tImpos.
    boostActv = 0 #variabile per il controllo del booster
    flagBoostActive = True #falga per attivare il boosster in determinate condizioni
    flagGiroTup = 0 #flag per far almeno 3 letture della dtem
    modalitaModify = 0 #variabile per cambiare la modalita aggiornamento lista potenza
    accediCh1 = True #flag accesso a Ch1 (se True)
    accediCh2 = True #flag accesso aCh2 (se true)
    setPercentSup = 0.25 #setta la percentuale di temperatura sopra il limite consentita
    setPercentInf = 1.5 #setta la percentuale di temperatura sotto il limite consentita
    dTempAntico = 0 #variabile per contenere il delta temp antico inizio =0
    tempControllo = 0 #variabile controllo temperatura x incrementare valori lista
    indiceTempo = 0 #variabile incrementabile per il tempo di attesa incr lista pow
    tempoAttesa1 = ConversioneTempoAttesa(2) #imposto tempo atteesa a n minuti
    varPow = ''
    while True:# crea un ciclo infinito
        if ticks_diff(ticks_ms(),tempoLetturaSens) >= 5000:# tempo di lettura sensore/agg display
            if inG1.value() == 0 and accediCh1 == True: #se la sonda è sul 1 canale...
                canale = '1'
                exitPotX = exitPot1
                setTempX = setTemp1
                tempPercentSup = round(CalcoloTempPercent(set_temp=setTempX,modalita=1,perc_val=setPercentSup),1)
                tempPercentInf = round(CalcoloTempPercent(set_temp=setTempX,modalita=0,perc_val=setPercentInf),1)
                exitPot2.pulse_width(0)
                listaVals,powList = util.Make_Lists(set_temp=tempPercentSup)
                accediCh1 = False #metti a False cosi non rientra in ch1
                accediCh2 = True #poni a treu ch2 soi da garantirne l'eventale accesso
                print("CH1")
            if inG2.value() == 0 and accediCh2 == True: #se la sonda è sul 2 canale..
                canale = '2'
                exitPotX = exitPot2
                setTempX = setTemp2
                tempPercentSup = round(CalcoloTempPercent(set_temp=setTempX,modalita=1,perc_val=setPercentSup),1)
                tempPercentInf = round(CalcoloTempPercent(set_temp=setTempX,modalita=0,perc_val=setPercentInf),1)
                exitPot1.pulse_width(0)
                listaVals,powList = util.Make_Lists(set_temp=tempPercentSup)
                accediCh1 = True #poni a true ch1 soi da garantirne l'eventale accesso
                accediCh2 = False #metti a False cosi non rientra in ch2
                print("CH2")
                
            try:
                flagSensInit,numSens,tempLetta = ControlloSensori(sensInit,ssd=oled)# controlla se i sensori ci sono
            except:#!!! non ci vanno le () !!!!
                print('!!! ERRORE SUL SENSORE!!!!')
                
            if flagSensInit == True:# se ci sono...
                potenzaPerc,indicePotenza = util.Percent_Power_Out(tempLetta,
                            lista_vals=listaVals,pow_list=powList)
                deltaTempX = setTempX-tempLetta #levato ABS!
                if tempLetta > setTempX:#proivare a mettere setTempX
                    if deltaTempX < dTempAntico:
                        dTempAntico = deltaTempX #+ 0.01 #memorizza il valore massimo raggiunto!
                        flagGiroTup += 1
                        #print('tempx ',deltaTempX,'TempAn: ',dTempAntico)
                    if flagTempUp == False and flagGiroTup > 2 and deltaTempX >= dTempAntico:#deltaTempX  >= dTempAntico:#aggiunto =!! (>=
                        print("-- dec lista --")
                        powList = util.Modify_List(powerlist=powList,indexpot=None,
                                                   tempstats=1,delta_t=abs(dTempAntico))
                        flagTempUp = True
                        dTempAntico = 0
                        varPow = UnsafePower(powList)
                        indiceTempo = 0
                        tempoAttesa1 = ConversioneTempoAttesa(4) #ora si passa a n minuti di attesa
                        flagGiroTup = 0
                        flagBoostActive = True #ora si puo ripetere il boost
                if tempLetta < tempPercentInf:
                    if tempLetta <= tempControllo:
                        indiceTempo += 1
                        if indiceTempo > tempoAttesa1:#12 = circa 1 minuto (5*12)
                            powList = util.Modify_List(powerlist=powList, indexpot=indicePotenza,
                                                       tempstats=modalitaModify,delta_t=deltaTempX)#modifica la lista +1% power
                            indiceTempo = 0
                            tempControllo = 0
                            dTempAntico = 0 #da valutare se occoro o no, ma credo di si
                    else:
                        tempControllo = tempLetta
                        indiceTempo = 0

                if tempLetta <= setTempX: #and flagBoostActive == True: #se setTemp1 letta < tem impostata e flag potenza = True
                    flagTempUp = False
                    dTempAntico = 0 #resetta Tempo antico (deve essrci)
                    varPow = UnsafePower(powList) #aggiunto per test bug
                if flagBoostActive == True and tempLetta <= tempPercentInf:
                    if boostActv <= 25:# and flagBoostActive == True:# variabile vera attiva il bustere della potenza
                        if potenzaPerc <= 30:
                            valBoost = util.Liner_Calc(tilt=3.3,param=potenzaPerc,offset=0)#int(round(3.36*potenzaPerc +  15 ,0))#retta per il calcolo dela valore del boost
                        else:
                            valBoost = 100 
                        util.Emited_Power(timer=exitPotX,power_pp=potenzaPerc,boost=valBoost)
                        boostActv = boostActv + 1 
                        indiceTempo = 0 #resetta l'indice tempo
                    else:
                        flagBoostActive = False
                        boostActv = 0
                else:# se falso lavora normalmete con i valori in lista
                    util.Emited_Power(timer=exitPotX,power_pp=potenzaPerc,boost=0)
                    
                DatiInDisplay1(ssd=oled,set_T=setTempX,read_T=tempLetta,powpr=potenzaPerc,
                               ch=canale,war_Pow=varPow)
                tempSens=tempLetta#memroizza la vecchia temperatura
                tempoLetturaSens = ticks_ms() #memorizza il tempo che ce ora!
                
        if pulS4.value() == 0:# se premiamo il pulsante pulS4...
            oled.fill(0)# cancella il display
            (setTemp1,setTemp2,cambio)=Menu2.Menu1(ssd=oled,setTemp1=setTemp1,setTemp2=setTemp2,
                                         P1=pulS1,P2=pulS2,P3=pulS3,P4=pulS4)# chiama la funzione Menu_1 e pasa tutti i valori
            if cambio == True:
                accediCh1 = True
                accediCh2 = True
            else:
                accediCh1 = False
                accediCh2 = False
            dTempAntico = 0
            tempoAttesa1 = ConversioneTempoAttesa(2)
            oled.fill(0)
        wdt.feed() #resetta il watchdog e riparte da zero, se qui non arriva si restetta tutto.
        delay(15)
elif numSens == 2:
    pass
 
