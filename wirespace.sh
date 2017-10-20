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
		echo "--- WIRESPACE HELP ---"
		echo -e "Command\t\tDescription"
		echo -e "--install,-i\tInstalls all dependencies and sets up Wirespace"
		echo -e "--local,-l\tHosts Wirespace locally in debug mode"
		echo -e "--start,-s\tAutodetects IP address and hosts Wirespace over default port number 8000"
		echo -e "--custom,-c\tHosts wirespace after manual setup of IP address and port number"
		echo -e "--help,-h\tDisplays this help and exit"
	fi
fi