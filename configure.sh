port=$2
ip=$1
debug=$3

sed -i "s/^ALLOWED_HOSTS.*$/ALLOWED_HOSTS = \['$ip'\]/g" wirespace/settings.py
sed -i "s/^PORT.*$/PORT = $port/g" wirespace/settings.py
sed -i "s/^HOST_IP.*$/HOST_IP = '$ip'/g" wirespace/settings.py
sed -i "s/^DEBUG.*$/DEBUG = $debug/g" wirespace/settings.py
