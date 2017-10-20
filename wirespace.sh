#!/bin/bash

if [[ ! $# -eq 1 ]]; then
	echo "No matching command found."
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
		echo "Wirespace installation complete."

	elif [[ $1 == "--start" || $1 == "-s" ]]; then
		ip=$( python3 get_ip.py )
		port=8000
		bash configure.sh $ip $port False
		sudo python3 manage.py runserver "$ip:$port" --insecure

	elif [[ $1 == "--local" || $1 == "-l" ]]; then
		ip="localhost"
		port=8000
		bash configure.sh $ip $port True
		sudo python3 manage.py runserver "$ip:$port" --insecure

	elif [[ $1 == "--custom" || $1 == "-c" ]]; then
		echo -n "Enter IP address : "
		read ip
		echo -n "Enter port number : "
		read port
		bash configure.sh $ip $port False
		echo -e "\nHosting Wirespace on $ip:$port ...\n"
		sudo python3 manage.py runserver "$ip:$port" --insecure

	elif [[ $1 == "--help" || $1 == "-h" ]]; then
		echo "Wirespace v1.0"
		echo "Developed by Saurav, Yash and Saunack"
		echo -e "Licensed under GNU GPL v3.0\n"
		echo -e "Usage: ./wirespace.sh [OPTION]\n"
		echo -e "-i,--install\tInstalls all dependencies and sets up Wirespace"
		echo -e "-l,--local\tHosts Wirespace locally in debug mode"
		echo -e "-s,--start\tAutodetects IP address and hosts Wirespace over port 8000"
		echo -e "-c,--custom\tHosts Wirespace after manual setup of IP address and port"
		echo -e "-h,--help\tDisplays this help and exit"
	fi
fi