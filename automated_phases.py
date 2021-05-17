import subprocess
import argparse
from time import sleep

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
                #Running phase 1 blocking to ensure the previous collection files are deleted
                process_1 = subprocess.Popen(["python", "wae_api.py", "-d", "-ph", "1"], close_fds=True)
                process_1.communicate()
            elif counter == 2:
                process_2 = subprocess.Popen(["python", "wae_api.py", "-ph", "2"], close_fds=True)
                sleep(2)
            elif counter == 3:
                process_3 = subprocess.Popen(["python", "wae_api.py", "-ph", "3"], close_fds=True)
                sleep(2)
            elif counter == 4:
                process_4 = subprocess.Popen(["python", "wae_api.py", "-ph", "4"], close_fds=True)
                sleep(2)
            elif counter == 5:
                process_5 = subprocess.Popen(["python", "wae_api.py", "-ph", "5"], close_fds=True)
                sleep(2)
            # elif counter == 6:
            #     process_6 = subprocess.Popen(["python", "wae_api.py", "-ph", "6"])
            # if counter == 6: break
            if counter == 5: break
            counter += 1

        process_2.communicate() and process_3.communicate() and process_4.communicate() and process_5.communicate()
        # process_6.communicate()
        # # process_7 = subprocess.Popen(["python", "wae_api.py", "-b", "-ph", "7"])  
        # process_7.communicate()
        process_6 = subprocess.Popen(["python", "wae_api.py", "-b", "-ph", "6"], close_fds=True)  
        process_6.communicate()

    else:
        while measure:
            if counter == 1:
                # Running phase 1 blocking to ensure the previous collection files are deleted
                process_1 = subprocess.Popen(["python", "wae_api.py", "-d", "-ph", "1"])
                process_1.communicate()
            elif counter == 2:
                process_2 = subprocess.Popen(["python", "wae_api.py", "-ph", "2"])
                sleep(2)
            elif counter == 3:
                process_3 = subprocess.Popen(["python", "wae_api.py", "-ph", "3"])
                sleep(2)
            elif counter == 4:
                # process_4 = subprocess.Popen(["python", "wae_api.py", "-ph", "4"])
                sleep(2)
            elif counter == 5:
                # process_5 = subprocess.Popen(["python", "wae_api.py", "-ph", "5"])
                sleep(2)
            elif counter == 6:
                # process_6 = subprocess.Popen(["python", "wae_api.py", "-ph", "6"])
                sleep(2)
            # if counter == 6: break
            elif counter == 7:
                process_7 = subprocess.Popen(["python", "wae_api.py", "-ph", "7"])
            if counter == 7: break
            counter += 1  
        
        process_2.communicate() and process_3.communicate() and process_7.communicate()

    print("The EPNM script phases were run asynchronously.")

run_phases(build_plan)

