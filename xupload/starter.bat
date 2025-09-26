@echo off
REM --- Change directory to where TWS is installed ---
cd /d C:\Jts

REM --- Start TWS (javaw) with login args ---
start "" javaw -cp jts.jar;jcommon-1.0.23.jar;jfreechart-1.0.19.jar -Xmx512M jclient.LoginFrame username=DaresB1974 password="mitchell7305!" mode=live api=enabled
