import subprocess


def get_cpu_temp():

    temp = subprocess.run(["vcgencmd", "measure_temp"], capture_output=True, text=True).stdout.strip()
    temp = float(temp.split("=")[1].split("'")[0])
    return temp