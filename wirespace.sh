#!/bin/bash

if [[ ! $# -eq 1 ]]; then
	echo "No command found."
	echo "Try 'wirespace --help' for a list of all commands."
	exit
else
	if [[ $1 == "--install" || $1 == "-i" ]]; then
		if [[ $( which python3 ) == "" ]]; then
			echo "Installing Python 3 ..."
			sudo apt-get install python3
		fi
		if [[ $( which pip3 ) == "" ]]; then
			echo "Installing Python Pip 3 ..."
			sudo apt-get install python3-pip
		fi
		echo "Installing dependencies ..."
		sudo pip3 install -r requirements.txt
		sudo apt-get install python3-tk
		echo "Creating database ..."
		python3 manage.py makemigrations
		python3 manage.py migrate
		echo "Setting up administrator ..."
		python3 manage.py createsuperuser
		echo "Wirespace installation complete."

	elif [[ $1 == "--start" || $1 == "-s" ]]; then
		ip=$( python3 actions.py get_ip )
		port=8000
		python3 actions.py configure $ip $port False
		echo -e "Hosting Wirespace admin on http://$ip:$port/host ...\n"
		python3 manage.py runserver "$ip:$port" --insecure

	elif [[ $1 == "--local" || $1 == "-l" ]]; then
		ip="localhost"
		port=8000
		python3 actions.py configure $ip $port True
		echo -e "Hosting Wirespace admin on http://$ip:$port/host ...\n"
		python3 manage.py runserver "$ip:$port" --insecure

	elif [[ $1 == "--custom" || $1 == "-c" ]]; then
		echo -n "Enter IP address : "
		read ip
		echo -n "Enter port number : "
		read port
		python3 actions.py configure $ip $port False
		echo -e "\nHosting Wirespace admin on http://$ip:$port/host ...\n"
		python3 manage.py runserver "$ip:$port" --insecure

	elif [[ $1 == "--editor" || $1 == "-e" ]]; then
		python3 actions.py editor

	elif [[ $1 == "--newuser" || $1 == "-n" ]]; then
		echo "Creating new administrator :"
		python3 manage.py createsuperuser

	elif [[ $1 == "--help" || $1 == "-h" ]]; then
		echo "Wirespace v1.0"
		echo "Developed by Yash, Saurav and Saunack"
		echo -e "Licensed under GNU GPL v3.0\n"
		echo -e "Usage: ./wirespace.sh [OPTION]\n"
		echo -e "****** Installation ******"
		echo -e "-i,--install\tInstalls all dependencies and sets up Wirespace\n"
		echo -e "****** Server-side ******"
		echo -e "-l,--local\tHosts Wirespace locally in debug mode"
		echo -e "-s,--start\tAutodetects IP address and hosts Wirespace over port 8000"
		echo -e "-c,--custom\tHosts Wirespace after manual setup of IP address and port\n"
		echo -e "-n,--newuser\tCreates a new administrator\n"
		echo -e "****** Client-side ******"
		echo -e "-e,--editor\tOpens Wirespace-Editor for local editing and remote saving"
		echo ""
		echo -e "-h,--help\tDisplays this help and exit"
		
	else
		echo "No matching command found."
		echo "Try 'wirespace --help' for a list of all supported commands."
		exit
	fi
fi
