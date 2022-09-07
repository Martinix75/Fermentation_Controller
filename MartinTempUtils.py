'''
Created on 27 nov 2020

@author: andrea
'''
import ujson
from pyb import Timer
MartinTempUtils='0.5.6'

# ----- Scrittura configurazione Json -------------
def Read_Config(name,**Values): #uso un wkargs, anche se molto lento!
    try:
        with open(name, 'r') as _Filex:
            _valx = ujson.load(_Filex)# legge il file json (è un dizionario!)
        return _valx # ritorna il dizionario
    except(OSError):
        Write_Config(name=name,**Values)# se il file non ce chiema la funzione per crearlo, passando i parametri
        return Read_Config(name=name)
    
def Write_Config(name,**Values):
    with open(name, 'w') as _Filex:
        ujson.dump(Values, _Filex)
        #return Values #sblindare se non funge!
        
# ----- Funzioni Controllo Temperatura --------------
def Flex_Optimus(set_temp):#nuova funziona calcolo punti di flesso
    if set_temp <= 21:
        return Liner_Calc(tilt=0.5,param=set_temp,offset=2, )#round(0.50*set_temp+2)
    elif set_temp > 21 and set_temp <= 45:
        return Liner_Calc(tilt=-0.17,param=set_temp,offset=17.9)#round(-0.17*set_temp+17.9)
    elif set_temp > 45:
        return Liner_Calc(tilt=-0.05,param=set_temp,offset=12.5)#round(-0.36*set_temp+23)
    
def Flex_Points(set_temp,n_flex):
    flex_list = [0]
    for point in range(1,n_flex+1):
        point_temp = set_temp*(point/n_flex)**(1/1.8)#radice di 2.5 (ottimo compromesso tra radice di 2 & 3
        flex_list.append(round(point_temp,1))
    print('Punti flesso: ',flex_list,' len:',len(flex_list))
    return flex_list

def List_Percent_Pwr(n_flex):#correzione BUG1 riscritto funzione (piu bella)
    pot_list = [round((100/(n_flex))*l) for l in range(n_flex,-1,-1)]
    print('ListPwr: ',pot_list,' Len:',len(pot_list))
    return pot_list

def Make_Lists(set_temp):
    n_flex = Flex_Optimus(set_temp)
    lista_vals = Flex_Points(set_temp, n_flex)
    pow_list = List_Percent_Pwr(n_flex)
    return lista_vals,pow_list

def Percent_Power_Out(temp_letta,lista_vals,pow_list):
    if temp_letta >= lista_vals[-1]:# se la temperetura è > del limite imposto
        return (0,len(pow_list)-1)#torna 0 (potenza 0%) ed il suo indeice
    elif temp_letta < lista_vals[-1]: #se la temperatura è minuare del limite valuta..
        for elem in range(len(pow_list)):#calcola lunhgheza lista pote e cicla
            if temp_letta >= lista_vals[elem] and  temp_letta < lista_vals[elem+1]: #contrla se temp_letta è tar i due limiti
                return (pow_list[elem],elem)# ritorna la potenza emessa, e il suo indice corrente

def Emited_Power(timer,power_pp,boost=0):
    if boost >100: #controllo se si supera la percentale consentita
        boost = 100 # valutre se laciare 100 o meno!
    if boost > 0: #se booster > 1 (il numero è la percentale)
        converse = 270*boost
    else:
        converse = 270*power_pp
    timer.pulse_width(converse)

def Modify_List(powerlist,tempstats,indexpot,delta_t=0):
    if tempstats == 0:
        return Modify_Up(powerlist=powerlist,indexpot=indexpot,delta_t=delta_t)
    elif tempstats == 1:
        return Modify_Down(powerlist=powerlist,indexpot=indexpot,delta_t=delta_t)
    elif tempstats == 2:
        return Modify_Work(powerlist=powerlist,indexpot=indexpot,delta_t=delta_t)
    
def Modify_Up(powerlist,indexpot,delta_t=0):#modifica lista prima di arrivare a tem.set (0->tset mediata)
    ParabolicValue = Parabolic_Calc(param=delta_t,coeff=1.6,expon=0.7)#Liner_Calc(tilt=0.78, param=delta_t, offset=0)#3 #incrementa tutta la lista (tranne gli estremi) di 3
    for IndeX in range(len(powerlist)):# ciclo incrementazionle lista
        if powerlist[IndeX] < 100 and powerlist[IndeX] > 0: #tutta la lista  si incrementa a meno degli estremi
            NewValue = powerlist[IndeX] + ParabolicValue
            if NewValue >= 100: #se l'elemento risultante >= 100 (che non puo essere)...
                powerlist[IndeX] = 100 #.. allora poni l'elemento a 100 in ogni caso
            else:
                powerlist[IndeX] = NewValue # se non è >=100 poni l'elemento = newValue
    for IndeX in range(indexpot,len(powerlist)-1):#inizia il ciclo per la media elemento
        powerlist[IndeX] = int((powerlist[IndeX-1]+powerlist[IndeX])/2)
    print("Modifi_Up: ",powerlist)
    return powerlist
'''
def Modify_Down(powerlist,indexpot,delta_t=0):#modifica la lista (penultimo elemento) superato tem impost
    powerlist[indexpot-1] = powerlist[indexpot-1] - Liner_Calc(tilt=2, param=delta_t, offset=1)#1#1 #scala di 1 il penultimo elemento della lista
    print("Modifi_Down: ",powerlist)
    return powerlist
'''
def Modify_Down(powerlist,indexpot,delta_t=0):#nuava funzione di modifica lista down
    LinerValue = Liner_Calc(tilt=4, param=delta_t, offset=1)# calcola quanto scalare con fx lineare
    for Index in range(len(powerlist)-1): #scorri tutta la lista meno l'ultimo elemento
        powerlist[Index] -= LinerValue #decrementa di Liear value tutta la lista
        if powerlist[Index] <= 0: #se ce un elemento a zero (tranne l'ultimo)
            powerlist[Index] = LinerValue # (il penultimo), ponilo = a Linear value
    powerlist = Check_List(powerlist=powerlist)#,step_val=LinerValue)
    #Check_List(powerlist=powerlist) serve????
    print("Modifi_Down2: ",powerlist)
    return powerlist

def Modify_Work(powerlist,indexpot,delta_t=0):# uan volta superato tem impost non mediare ma gioca di fino..
    ParabolicValue = Parabolic_Calc(param=delta_t,coeff=1.6,expon=0.7)
    powerlist[indexpot] = powerlist[indexpot] + ParabolicValue#2 #increneta l'elemnto che non cresce di 2
    for Index in range(len(powerlist)-1):
        powerlist[Index] += ParabolicValue
        if powerlist[Index] > 100:
            powerlist[Index] = 100
    Check_List(powerlist=powerlist)
    print("Modifi_Work: ",powerlist)
    return powerlist
'''
#funziona da ridefinire!!!!!
def Check_List_o(powerlist,step_val=1):#funzione pe ril controllo coerenza lista (valori corretti)
    powerlist.sort(reverse=True)#ordina in modo crescente la lista
    #print(powerlist)
    for Index in range(len(powerlist)-1):
        if powerlist[Index] <= 0:
            powerlist[Index] = powerlist[Index-1]
    return powerlist
'''
def Check_List(powerlist):
    powerlist.sort(reverse=True)#ordina in modo crescente la lista
    print('Lista ordinata: ',powerlist)
    for Index in range(1,len(powerlist)-1):#scorri la lista dal secondo al penutlimo elemento
        if powerlist[Index] >= powerlist[Index-1] and  Index >1:#se lelemento in esame è maggiore = a quello prima...
            powerlist[Index-1] = int((powerlist[Index]+powerlist[Index-2])/2)#modifia elemmento-1 facendo media tra elment-2 ed element
    return powerlist
        

# ---------- funzioni matematiche ------------------------------
def Media( temp_new,temp_old):  # calcolo media temp tra i flessi
    Somma_Parziale = (temp_old + temp_new)
    MediaCont = (Somma_Parziale/2)
    return MediaCont

def Liner_Calc(tilt,param,offset=0):#calcola la retta per le varie voci
    xx = round((tilt*param)+offset)
    print('retta: ',xx)
    return xx#round(tilt*param+offset)

def Parabolic_Calc(param,coeff=1,expon=1):
    kl = round(coeff*(param**expon))
    print('parabola: ',kl)
    return kl#round(coeff*(param**expon))
#valutare in futuro se creare una parabola per esempio 1.4*dT**0.7 da partre qui
# -------- attiva se prog principale -------------------------
if __name__ == '__main__':
    
    #a mai negativo!!
    a = [100,100,80,70,60,1,3,3,3,0]
    print('Lista Orig: ',a)
    print('Lista Modi: ',Check_List(powerlist=a))#,step_val=5))

    #Modify_List(powerlist=a, indexpot=None, tempstats=1,delta_t=3)
    '''
    print (List_Percent_Pwr(n_flex=7))
    Power_Out(temp_letta=23.6, set_temp=24)

    x = 20
    a = Flex_Optimus(x)
    print('Risultao: ',Flex_Points(x, a))
    a,b = Make_Lists(set_temp=29)
    print(a,b)

    print('Testi...')
    a= 1
    b= 23.8
    c= 0.32
    Write_Config(a=a,b=b,c=c)
    j = Read_Config(a=12,b=67,c=45)
    print('ritorna: ',j)
    h=j['a']+10
    k=j['b']+10
    l=j['c']+10
    print(h,k,l,'-',a,b,c)
    '''
 
