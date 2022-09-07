'''
Created on 20 mar 2021

@author: andrea
'''
from pyb import Pin, delay
import ssd1306
from DisplayOledUtility import center_text
#from MartinTempUtils import Flex_Optimus
import MartinTempUtils as util

MenuVer ='0.2.4'

def Menu1 (ssd,setTemp1,setTemp2,P1,P2,P3,P4):    
    posInit = 20 #seleziona la posizione iniziale delle scritte
    curPosit = posInit #posizione iniziuale del cursore
    stepPos = 15 #da la distanza tra le varie opzioni
    sT1_old = setTemp1  #memoriza il valore passato x uscire senza modifiche
    sT2_old = setTemp2
    while True:
        center_text(ssd,text='** Config **',y=0) #riga 1 presentazione
        ssd.hline(0,10,128,10) #traccia un aline di separazione
        
        #------ Scritte del menu selezionabili -------
        ssd.text('Set T1: {:0.1f}'.format(setTemp1) ,18,posInit) #voce per  selezionate la temperatura limit 1 ch
        ssd.text('Set T2: {:0.1f}'.format(setTemp2) ,18,posInit+(stepPos*1)) #voce per  selezionate la temperatura limit 2 ch
        ssd.text('Salva ed Esci',18,posInit+(stepPos*2))
        ssd.text('->',0,curPosit) # pone il cursore nella posizione 1
        if P4.value() == 0: #se premupo P4(Y6) muove il cursere
            curPosit=MoveArrow(ssd, cursorPosition=curPosit, step=stepPos,posinit=posInit) #chiama la funziona pe rmuovere
        if P2.value() == 0: #incremente il valore selezionato...
            if curPosit == posInit: #se selezinata settemp 1..
                setTemp1=DeltaTemp1(ssd,val=setTemp1,step=0.5,limit_T=60,posinit=posInit,up_dw=True)#incrementa T1
            elif curPosit == posInit+(stepPos*1): #se selezionatta settem 2....
                setTemp2=DeltaTemp2(ssd,val=setTemp2,step=0.5,limit_T=60,posinit=posInit+(stepPos*1),up_dw=True)#incrementa T2
            elif curPosit == posInit+(stepPos*2):
                Save_Sets(setTemp1=setTemp1,setTemp2=setTemp1)
                return(setTemp1,setTemp2,True)
        if P3.value() == 0: #decrenmenta il valore selezionato...
            if curPosit == posInit: #se selezinata settemp 1..
                setTemp1=DeltaTemp1(ssd,val=setTemp1,step=0.5,limit_T=2,posinit=posInit,up_dw=False)#decrementa T1
            elif curPosit == posInit+(stepPos*1): #se selezionatta settem2....
                setTemp2=DeltaTemp2(ssd,val=setTemp2,step=0.5,limit_T=2,posinit=posInit+(stepPos*1),up_dw=False)#decrementa T2
            elif curPosit == posInit+(stepPos*2):
                Save_Sets(setTemp1=setTemp1,setTemp2=setTemp1)
                return(setTemp1,setTemp2,True)
        if P1.value() == 0:#se premo P1(Y3) esce dal manu config senza salvare
            return(sT1_old,sT2_old,False)
        
        ssd.show()
        delay(50)
        
def MoveArrow(ssd,cursorPosition,step,posinit):#funzione per muovere il cursore
    ssd.text('->',0,cursorPosition,0) #oscura il cursore nella posizione originaria
    curosrPosition= StepUp(cursorPosition, step)
    if curosrPosition > 50: #se maggiore di 45 (pos max)..
        curosrPosition = posinit #torna alla posizion1 0 25
    ssd.text('->',0,curosrPosition,1) #mostra il cursore nella posizione nuova
    return curosrPosition

def DeltaTemp1(ssd,val,step,limit_T,posinit=20,up_dw=True): #varia la il set di T1
    ssd.text('Set T1: {:0.1f}'.format(val) ,18,posinit,0)# oscura la scritta 1 riga
    if up_dw == True: #se il flag è True si incrementa 
        if val <= limit_T - 0.5: #incrementa solo val è minore del limite impostato
            val = StepUp(val, step)#incementa di uno step
    elif up_dw == False:#se il flag è False si decrementa
        if val >= limit_T + 0.5: #decrementa solo se val è maggiore del limite impostao
            val = StepDw(val, step)#decerementa di un  step
    ssd.text('Set T1: {:0.1f}'.format(val) ,18,posinit,1)
    return val

def DeltaTemp2(ssd,val,step,limit_T,posinit=20,up_dw=True): #varia il set di T2
    ssd.text('Set T2: {:0.1f}'.format(val) ,18,posinit,0)
    if up_dw == True:
        if val <= limit_T - 0.5:
            val = StepUp(val, step)
    elif up_dw == False:
        if val >= limit_T + 0.5:
            val = StepDw(val, step)
    ssd.text('Set T2: {:0.1f}'.format(val) ,18,posinit,1)
    return val
    
def StepUp(val, step):#funazion generica di in cremento
    return val+step

def StepDw(val, step): #funziona generica di decremento
    return val-step

def TestDisplay():#piccolo test per il display se funziona
    center_text(ssd=oled, text='Test Menu',y=5)
    center_text(ssd=oled, text='Premi Y6 (P4)',y=15)
    center_text(ssd=oled, text='Ver:{}'.format(MenuVer),y=35)
    
def Save_Sets(setTemp1,setTemp2):
    util.Write_Config(name='TempControl.conf',setTemp1=setTemp1,setTemp2=setTemp2)

if __name__ == '__main__':
    from pyb import Pin
    from machine import I2C
    from DisplayOledUtility import*
    import ssd1306
    
    P1 = Pin('Y3', Pin.IN)
    P2 = Pin('Y4', Pin.IN)
    P3 = Pin('Y5', Pin.IN)
    P4 = Pin('Y6', Pin.IN)
    setTemp1 = 10.0
    setTemp2 = 20.0
    
    i2c = machine.I2C(scl=Pin('Y10'), sda=Pin('Y9'))#i2c1 pyboard
    oled = ssd1306.SSD1306_I2C(128, 64, i2c, 0x3c)
    oled.fill(0)
    TestDisplay()#mosta una schermata iniziale di prova
    oled.show()
    
    while True: #ciclo infito per test menu
        if P4.value() == 0: #se premi il pulsante P4 chiama la funziona menu..
            oled.fill(0)
            oled.show()
            setTemp1,setTemp2=Menu1(ssd=oled, setTemp1=setTemp1,setTemp2=setTemp2,P4=P4,P3=P3,P2=P2,P1=P1)
            oled.fill(0)#resetta lo schermo
            oled.show()
        #if P1.value() == 0:#esci dalla configurazionee mostra i valori
            #oled.fill(0)
            #oled.show()
            oled.text('-- Valori: --',0,1)
            oled.text('Set T1-> {}'.format(setTemp1),0,25)
            oled.text('Set T2-> {}'.format(setTemp2),0,45)
            #TestDisplay()
            oled.show()
    delay(300)
    #oled.show()

