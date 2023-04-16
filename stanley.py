# Stanley - Environment Metrics Device
#    _____ __              __          
#   / ___// /_____ _____  / /__  __  __
#   \__ \/ __/ __ `/ __ \/ / _ \/ / / /
#  ___/ / /_/ /_/ / / / / /  __/ /_/ / 
# /____/\__/\__,_/_/ /_/_/\___/\__, /  
#   .: environment metrics :. /____/   
#
# hardware platform  : Raspberry Pi Zero
# sensors            : BME280 temperature, pressure, humidity sensor
#                    : LTR-559 light and proximity sensor
#                    : MICS6814 analog gas sensor
#                    : ADS1015 analog to digital converter (ADC)
#                    : MEMS microphone
#                    : 0.96" colour LCD (160x80)
#                    : PMS5003 Particle Matter sensor
# Power              : UPS-lite battery backup
#                    : CW2015 Fuel gauge chip
#                    : LiPo 1000mAh
# codebase           : Python
#
# (2023) JinjiroSan
#
# stanley.py : v1-0.2 (alpha) - refactor C0.0


import time
import bme280
import pms5003
import gas
import ltr559
import colorsys
from enviroplus import gas
from enviroplus import led
from enviroplus.noise import Noise
from enviroplus import motion
from ST7735 import TFT
from PIL import Image, ImageDraw, ImageFont

# Define function to estimate NO2 concentration in ppm based on gas sensor readings and temperature/humidity data
def estimate_NO2_concentration(gas_reading, temperature, humidity):
    # Calculate gas resistance ratio using readings from gas sensor module
    gas_ratio = gas_reading / gas_sensor.oxidising_resistance

    # Calculate NO2 concentration in ppm using gas resistance ratio, temperature, and humidity
    NO2_concentration = (gas_ratio / 6.0) / ((temperature / 100.0) ** 1.5 * (humidity / 100.0))

    return NO2_concentration

# Define function to estimate CO concentration in ppm based on gas sensor readings and temperature/humidity data
def estimate_CO_concentration(gas_reading, temperature, humidity):
    # Calculate gas resistance ratio using readings from gas sensor module
    gas_ratio = gas_reading / gas_sensor.reducing_resistance

    # Calculate CO concentration in ppm using gas resistance ratio, temperature, and humidity
    CO_concentration = (gas_ratio / 3.0) / ((temperature / 100.0) ** 1.5 * (humidity / 100.0))

    return CO_concentration

# Define function to estimate NH3 concentration in ppm based on gas sensor readings and temperature/humidity data
def estimate_NH3_concentration(gas_reading, temperature, humidity):
    # Calculate gas resistance ratio using readings from gas sensor module
    gas_ratio = gas_reading / gas_sensor.nh3_resistance

    # Calculate NH3 concentration in ppm using gas resistance ratio, temperature, and humidity
    NH3_concentration = (gas_ratio / 0.15) / ((temperature / 100.0) ** 1.5 * (humidity / 100.0))

    return NH3_concentration

# Initialize gas sensor module on Enviro+ board
gas_sensor = gas.Gas()

# Initialize LED matrix on Enviro+ board
led_matrix = led.LED()

# Initialize noise sensor on Enviro+ board
noise_sensor = Noise()

# Initialize motion sensor on Enviro+ board
motion_sensor = motion.Motion()

# Initialize display on Enviro+ board
display = TFT()

# Initialize font for display text
font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)

# Initialize LTR559 light sensor on Enviro+ board
LTR559 = ltr559.LTR559()

# Initialize UPS Lite for Raspberry Pi Zero
ups_lite = UPSLite()

def draw_gas_pm_data(draw, NO2_concentration, CO_concentration, NH3_concentration, pm_data, thresholds):
    colors = {'normal': (0, 255, 0), 'warning': (255, 255, 0), 'danger': (255, 0, 0)}

    def get_color(value, thresholds):
        if value <= thresholds['warning']:
            return colors['normal']
        elif value <= thresholds['danger']:
            return colors['warning']
        else:
            return colors['danger']

    draw.text((0, 0), f'NO2: {NO2_concentration:.2f} ppb', font=font, fill=get_color(NO2_concentration, thresholds['NO2']))
    draw.text((0, 15), f'CO: {CO_concentration:.2f} ppm', font=font, fill=get_color(CO_concentration, thresholds['CO']))
    draw.text((0, 30), f'NH3: {NH3_concentration:.2f} ppm', font=font, fill=get_color(NH3_concentration, thresholds['NH3']))
    draw.text((0, 45), f'PM1.0: {pm_data["pm10_standard"]} µg/m³', font=font, fill=get_color(pm_data["pm10_standard"], thresholds['PM1.0']))
    draw.text((0, 60), f'PM2.5: {pm_data["pm25_standard"]} µg/m³', font=font, fill=get_color(pm_data["pm25_standard"], thresholds['PM2.5']))
    draw.text((80, 60), f'PM10: {pm_data["pm100_standard"]} µg/m³', font=font, fill=get_color(pm_data["pm100_standard"], thresholds['PM10']))

def draw_temp_humidity_voltage_capacity(draw, temperature, humidity, voltage, battery_capacity, thresholds):
    colors = {'normal': (0, 255, 0), 'warning': (255, 255, 0), 'danger': (255, 0, 0)}

    def get_color(value, thresholds):
        if value <= thresholds['warning']:
            return colors['normal']
        elif value <= thresholds['danger']:
            return colors['warning']
        else:
            return colors['danger']

    draw.text((0, 0), f'Temperature: {temperature:.1f}°C', font=font, fill=get_color(temperature, thresholds['temperature']))
    draw.text((0, 15), f'Humidity: {humidity:.1f}%', font=font, fill=get_color(humidity, thresholds['humidity']))
    draw.text((0, 30), f'Voltage: {voltage:.2f} V', font=font, fill=get_color(voltage, thresholds['voltage']))
    draw.text((0, 45), f'Battery: {battery_capacity:.1f}%', font=font, fill=get_color(battery_capacity, thresholds['battery_capacity']))

def draw_light_noise_motion(draw, light, noise, motion, thresholds):
    colors = {'normal': (0, 255, 0), 'warning': (255, 255, 0), 'danger': (255, 0, 0)}

    def get_color(value, thresholds):
        if value <= thresholds['warning']:
            return colors['normal']
        elif value <= thresholds['danger']:
            return colors['warning']
        else:
            return colors['danger']

    draw.text((0, 0), f'Light: {light:.1f} lux', font=font, fill=get_color(light, thresholds['light']))
    draw.text((0, 15), f'Noise: {noise:.1f} dBA', font=font, fill=get_color(noise, thresholds['noise']))
    draw.text((0, 30), f'Motion: {"Detected" if motion else "No motion"}', font=font, fill=get_color(int(motion), thresholds['motion']))

# Set initial display group
display_group = 0

while True:
    # Take gas sensor readings
    oxidising_reading = gas_sensor.read_oxidising()
    reducing_reading = gas_sensor.read_reducing()
    nh3_reading = gas_sensor.read_nh3()

    # Take temperature and humidity readings
    temperature, pressure, humidity = bme280.read_bme280()

    # Estimate NO2, CO, and NH3 concentrations
    NO2_concentration = estimate_NO2_concentration(oxidising_reading, temperature, humidity)
    CO_concentration = estimate_CO_concentration(reducing_reading, temperature, humidity)
    NH3_concentration = estimate_NH3_concentration(nh3_reading, temperature, humidity)

    # Take PM readings
    pm_data = pms5003.read()

    # Take light sensor readings
    light_data = LTR559.get_lux()

    # Take noise sensor readings
    noise_data = noise_sensor.get_noise_profile()

    # Take motion sensor readings
    motion_data = motion_sensor.get_motion()

    # Update UPS Lite data
    ups_lite.update()
    voltage = ups_lite.get_voltage()
    capacity = ups_lite.get_capacity()

    # Update display with gas and PM data
    img = Image.new('RGB', (160, 80), color=(0, 0, 0))
    draw = ImageDraw.Draw(img)
    if display_group == 0:
        draw_gas_pm_data(draw, gas_resistance, pm25, pm10, thresholds)
    elif display_group == 1:
        draw_temp_humidity_voltage_capacity(draw, temperature, humidity, voltage, battery_capacity, thresholds)
    elif display_group == 2:
        draw_light_noise_motion(draw, light, noise, motion, thresholds)
    display.display(img)
    
    # Sleep for 2 seconds
    time.sleep(2)

    # Increment display group, reset to 0 when reaching the end of the groups
    display_group += 1
    if display_group > 2:
        display_group = 0
