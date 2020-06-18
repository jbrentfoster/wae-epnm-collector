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
                #Running phase 1 blocking to ensure the previous collection files are deleted
                process_1 = subprocess.Popen(["python", "wae_api.py", "-d", "-ph", "1"])
                process_1.wait()
            elif counter == 2:
                process_2 = subprocess.Popen(["python", "wae_api.py", "-ph", "2"])
            elif counter == 3:
                process_3 = subprocess.Popen(["python", "wae_api.py", "-ph", "3"])
            elif counter == 4:
                process_4 = subprocess.Popen(["python", "wae_api.py", "-ph", "4"])
            elif counter == 5:
                process_5 = subprocess.Popen(["python", "wae_api.py", "-ph", "5"])
            # elif counter == 6:
            #     process_6 = subprocess.Popen(["python", "wae_api.py", "-ph", "6"])
            # if counter == 6: break
            if counter == 5: break
            counter += 1

        process_2.wait() and process_3.wait() and process_4.wait() and process_5.wait()
        # process_6.wait()
        process_6 = subprocess.Popen(["python", "wae_api.py", "-b", "-ph", "6"])  
        process_6.wait()

    else:
        while measure:
            if counter == 1:
                # Running phase 1 blocking to ensure the previous collection files are deleted
                process_1 = subprocess.Popen(["python", "wae_api.py", "-d", "-ph", "1"])
                process_1.wait()
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
            # elif counter == 7:
            #     subprocess.Popen(["python", "wae_api.py", "-ph", "7"])
            # if counter == 7: break
            if counter == 6: break
            counter += 1  
        
        process_2.wait() and process_3.wait() and process_4.wait() and process_5.wait() and process_6.wait()

    print("The EPNM script phases were run asynchronously.")

run_phases(build_plan)

