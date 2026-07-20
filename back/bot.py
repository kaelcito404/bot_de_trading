import MetaTrader5 as mt5
import pandas as pd
from ta.trend import EMAIndicator
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange
import time

# ==============================
"1. la conexion con metatrader5 "
# ==============================

if not mt5.initialize(
    login = "",
    password = "",
    server = ""
) : 
    print("hubo un error al iniciar la conexion. error :",mt5.last_error())
    quit()

else : 
    print(mt5.terminal_info())

# ==============================
"2.obtener las velas"
# ==============================

def obtener_velas():
    velas = mt5.copy_rates_from_pos(
        "GOLD", #mercado
        mt5.TIMEFRAME_M15, #temporalidad
        0, #inicio
        30 #cantidad de velas a traer
    )

    if velas is not None and len(velas) > 0 : 
        panel = pd.DataFrame(velas)
        panel["time"] = pd.to_datetime(panel["time"], unit="s")
        panel.set_index("time", inplace=True)
        return panel
    else : 
        print(f"error : {mt5.last_error()}")
        mt5.quit()
        return None

# ==============================
"3.los indicadores"
# ==============================

def cruce(panel) : 
    ema_corta = EMAIndicator(close = panel["close"], window= 7).ema_indicator()
    ema_larga = EMAIndicator(close = panel["close"], window= 21).ema_indicator()
    rsi = RSIIndicator(close=panel["close"], window=14).rsi()
    atr = AverageTrueRange(high = panel["high"], low= panel["low"], close = panel["close"], window=14).average_true_range()

    # los cruces de emas
    alcista = (ema_corta.iloc[-2] > ema_larga.iloc[-2] and ema_corta.iloc[-3] <= ema_larga.iloc[-3])
    bajista = (ema_corta.iloc[-2] < ema_larga.iloc[-2] and ema_corta.iloc[-3] >= ema_larga.iloc[-3])

    #los rsi de los cruces
    rsi_compra = rsi.iloc[-2] < 70
    rsi_venta = rsi.iloc[-2] > 30

    valor_atr = atr.iloc[-2]

    return alcista, bajista, rsi_compra,rsi_venta, valor_atr

# ==============================
"4.las operaciones"
# ==============================

def comprar(atr) : 
    #variables necesarias
    mercado = mt5.symbol_info_tick("GOLD")
    precio = mercado.ask 

    lote = 0.01
    take_profit = precio + 10
    stop_loss = precio - 10

    #la orden a mandar
    request = {
        "action" : mt5.TRADE_ACTION_DEAL,
        "symbol" : "GOLD",
        "volume" : lote,
        "price" : precio,
        "type" : mt5.ORDER_TYPE_BUY,
        "tp" : take_profit,
        "sl" : stop_loss,
        "deviation" : 40,
        "type_filling" : mt5.ORDER_FILLING_IOC
    }

    #mandamos la orden
    mandar_compra = mt5.order_send(request)
    return mandar_compra

def vender(atr) : 
    #variables necesarias
    mercado = mt5.symbol_info_tick("GOLD")
    precio = mercado.bid

    lote = 0.01
    take_profit = precio - 10
    stop_loss = precio + 10

    #la orden
    request = {
        "action" : mt5.TRADE_ACTION_DEAL,
        "symbol" : "GOLD",
        "volume" : lote,
        "type" : mt5.ORDER_TYPE_SELL,
        "price" : precio,
        "tp" : take_profit,
        "sl" : stop_loss,
        "deviation" : 40,
        "type_filling" : mt5.ORDER_FILLING_IOC
    }

    #mandamos la orden
    mandar_venta = mt5.order_send(request)
    return mandar_venta

# ==============================
"5. el bucle"
# ==============================
try : 
    while 1 > 0 : 
        #empezamos el cronometro
        inicio = time.time()
        print("empezando a analizar")

        #llamamos a las funciones
        panel = obtener_velas()
        alcista, bajista, rsi_compra, rsi_venta, valor_atr = cruce(panel)

        #las condiciones
        if alcista and rsi_compra : 
            mandar_compra = comprar(valor_atr)
            #verificamos que no hubo errores
            if mandar_compra.retcode == mt5.TRADE_RETCODE_DONE:
                print("operacion mandada con exito")
            else : 
                print(f"hubo un error. error : {mandar_compra.comment}")
    
        elif bajista and rsi_venta :
            mandar_venta = vender(valor_atr)
            #verificacion
            if mandar_venta.retcode == mt5.TRADE_RETCODE_DONE:
                print("operacion mandada con exito")
            else : 
                print(f"hubo un error. error : {mandar_venta.comment}")
    
        #terminamos el cronometro
        final = time.time()

        #calculamos el enfriamiento
        espera = final - inicio
        enfriamiento = 60 - espera
        if enfriamiento > 0 : 
            time.sleep(enfriamiento)

        print("la cosa ta muy calmaa patron")

#apagamos el bucle con un ctrl + c
except KeyboardInterrupt : 
    print("apagando el bot")
    mt5.shutdown()