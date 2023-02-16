#!/usr/bin/env python3

import paramiko
import time
import time
import os
import shutil
from datetime import datetime
import yaml
import logging

# Fortigate information collection tool.
#  This script will run the commands you list in fgtdc_commands.txt (should be in the same directory)
#  This list can ge changed as needed.
#  Configuration is done in the fgtdc_config.yml file for your specfic Fortigate.
#  It will log into the FGT via SSH and run each command logging to file.
#  If logs directory is missing it will be created
""""
 ________         ____     _ __  ___           __              __
/_  __/ /  ___   / __/  __(_) / / _ )___ ____ / /____ ________/ /
 / / / _ \/ -_) / _/| |/ / / / / _  / _ `(_-</ __/ _ `/ __/ _  /
/_/ /_//_/\__/ /___/|___/_/_/ /____/\_,_/___/\__/\_,_/_/  \_,_/
afaulkner@fortinet.com 
"""

now = datetime.now()
current_time = now.strftime("Date-%m-%d-%Y---Time-%H%M%S")

# Opening config file
with open('fgtdc_config.yml', 'r') as file:
	config = yaml.safe_load(file)

# Opening command list file
cmd_file = open('fgtdc_commands.txt', 'r')

# Checking for logs directory
if os.path.isdir(config['script_file_cfg']['log_path']):
	pass
else:
	print("Missing logs directory...creating it now.")
	os.makedirs(config['script_file_cfg']['log_path'])

# Setting up debug
def debug_setup():
	if config['debug_config']['debug_flag'] == "DEBUG":
		debug_flag = logging.DEBUG
	if config['debug_config']['debug_flag'] == "INFO":
		debug_flag = logging.INFO

	logging_file = config['debug_config']['debug_file']
	logging_path = config['debug_config']['debug_path']
	logging_flag = config['debug_config']['debug_log_flag']

	if logging_flag == "N":
		logging.basicConfig(level=debug_flag,format='%(asctime)s:%(levelname)s:%(message)s')
	if logging_flag == "Y":
		logging.basicConfig(filename=logging_path + logging_file,level=debug_flag,format='%(asctime)s:%(levelname)s:%(message)s')
	logging.debug("***** Start of FGTDC Script. *****")

# Checking to see if log file exsist, if not creating.
def check_file():
	logging.debug("Start of check_file function.")
	if os.path.isfile(config['script_file_cfg']['log_path'] + config['script_file_cfg']['log_file']):
		pass
	else:
		fout = open(config['script_file_cfg']['log_path'] + config['script_file_cfg']['log_file'],'wb')
		print("1st time run creating log file.")
		fout.close()

# Checking directory size, this is a safe guard to prevent the script from filling
# the file system.
def dir_size_limit():
	logging.debug("Start of dir_size_limit function")
	for root, dirs, files in os.walk(config['script_file_cfg']['log_path']):
		dir_size = 0
		for fn in files:
			path = os.path.join(root, fn)
			size = os.stat(path).st_size # in bytes
			#print(size)
			dir_size = dir_size + size
	if dir_size > int(config['script_file_cfg']['dir_limit']):
		print("Directory Limit Reached!  Clean out directory and start again.")
		exit()
	else:
		print("Directory size good... moving to next step")
			
# Checking to see if log file has got too large, if yes move it with date stamp.
		# File limit set in yaml file.
def log_file_rotation():
	logging.debug("Start of log_file_rotation function")
	file_size = os.path.getsize(config['script_file_cfg']['log_path'] + config['script_file_cfg']['log_file'])
	
	print("Log file Size is :", file_size, "bytes")
	if file_size > int(config['script_file_cfg']['file_limit']): 
		print("File size exceeds limit....moving..")
		new_log = open(config['script_file_cfg']['log_path'] + current_time + "_log.txt",'wb')
		new_log.close()
		shutil.move(config['script_file_cfg']['log_path'] + config['script_file_cfg']['log_file'], config['script_file_cfg']['log_path'] + current_time + "_log.txt")
	else:
		pass

# Turning off MORE for the console otherwise script hangs.
def console_set():
	logging.debug("Start of console_set function")
	host = config['fgtconfig']['fgt_ip']
	port = config['fgtconfig']['fgt_port']
	username = config['fgtconfig']['fgt_admin']
	password = config['fgtconfig']['fgt_password']
	ssh = paramiko.SSHClient()
	ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	ssh.connect(host, port, username, password)
	cmd = "config system console" "\n" "set output standard" "\n" "end" "\n"
	stdin, stdout, stderr = ssh.exec_command(cmd)
	output = stdout.read().decode('utf-8').strip("\n")
#	print(output)
	ssh.close()

# Running commands against FGT taken from commands file.
def run_command():
	logging.debug("Start of run_command function")
	# Opening log file
	fout = open(config['script_file_cfg']['log_path'] + config['script_file_cfg']['log_file'],'a')
	host = config['fgtconfig']['fgt_ip']
	port = config['fgtconfig']['fgt_port']
	username = config['fgtconfig']['fgt_admin']
	password = config['fgtconfig']['fgt_password']
	ssh = paramiko.SSHClient()
	ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	ssh.connect(host, port, username, password)	
	fout.write(current_time)
	fout.write('\n\r')
	fout.write("***** Start of commands *****")
	fout.write('\n\r')
	
	for cmd in cmd_file:
		if cmd.startswith('#'):
			pass
		else:
			stdin, stdout, stderr = ssh.exec_command(cmd)
			fout.write('\n\r')
			fout.write("Running: " + cmd)
			fout.write('\n\r')
			output = stdout.read().decode('utf-8').strip("\n")
			#print(output)
			time.sleep(.5)
			fout.write('\n\r')
			fout.write(output)
			time.sleep(.5)
	fout.write('\n\r')
	fout.write("***** End of commands *****")
	fout.write('\n\r')
	fout.close()
	cmd_file.close()
	ssh.close()

debug_setup()
dir_size_limit()
check_file()
log_file_rotation()
console_set()
run_command()
logging.debug("***** END of FGTDC Script. *****")