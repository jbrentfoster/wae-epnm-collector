import subprocess
import argparse

parser = argparse.ArgumentParser(description='A tool to automate running the EPNM script')
parser.add_argument('-b', '--build_plan', action='store_true', help="Add this flag to build the plan file.")
arg = parser.parse_args()
build_plan = arg.build_plan

def run_phases(arg):
    measure = True
    counter = 1

    if arg:
        while measure:
            if counter == 1:
                process_1 = subprocess.Popen(["python", "wae_api.py", "-d", "-ph", "1"])
            elif counter == 2:
                process_2 = subprocess.Popen(["python", "wae_api.py", "-ph", "2"])
            elif counter == 3:
                process_3 = subprocess.Popen(["python", "wae_api.py", "-ph", "3"])
            elif counter == 4:
                process_4 = subprocess.Popen(["python", "wae_api.py", "-ph", "4"])
            elif counter == 5:
                process_5 = subprocess.Popen(["python", "wae_api.py", "-ph", "5"])
            elif counter == 6:
                process_6 = subprocess.Popen(["python", "wae_api.py", "-ph", "6"])
            if counter == 6: break
            counter += 1

        process_1.wait()
        process_2.wait()
        process_3.wait()
        process_4.wait()
        process_5.wait()
        process_6.wait()
        subprocess.Popen(["python", "wae_api.py", "-b", "-ph", "7"])  

    else:
        while measure:
            if counter == 1:
                subprocess.Popen(["python", "wae_api.py", "-d", "-ph", "1"])
            elif counter == 2:
                subprocess.Popen(["python", "wae_api.py", "-ph", "2"])
            elif counter == 3:
                subprocess.Popen(["python", "wae_api.py", "-ph", "3"])
            elif counter == 4:
                subprocess.Popen(["python", "wae_api.py", "-ph", "4"])
            elif counter == 5:
                subprocess.Popen(["python", "wae_api.py", "-ph", "5"])
            elif counter == 6:
                subprocess.Popen(["python", "wae_api.py", "-ph", "6"])
            elif counter == 7:
                subprocess.Popen(["python", "wae_api.py", "-ph", "7"])
            if counter == 7: break
            counter += 1  

    print("The EPNM script phases were run asynchronously.")

run_phases(build_plan)

