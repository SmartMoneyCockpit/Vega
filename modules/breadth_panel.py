import pandas as pd
def build_breadth_dataframe():
    data = [
        {"Bucket":"SPY","Advance%":0.54,"Decline%":0.46,"McClellan":"+8","Signal":"Neutral"},
        {"Bucket":"QQQ","Advance%":0.47,"Decline%":0.53,"McClellan":"-6","Signal":"Risk-Off?"},
        {"Bucket":"IWM","Advance%":0.39,"Decline%":0.61,"McClellan":"-22","Signal":"Risk-Off"},
    ]
    return pd.DataFrame(data)
