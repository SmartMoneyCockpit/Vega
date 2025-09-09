import os
base = os.path.join("vault","cache")
os.makedirs(base, exist_ok=True)
flag_path = os.path.join(base, "risk_off.flag")
if os.path.exists(flag_path):
    os.remove(flag_path); print("Risk flag OFF")
else:
    open(flag_path,"w").write("1"); print("Risk flag ON")
